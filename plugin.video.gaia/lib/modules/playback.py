# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from lib.modules.tools import Settings, Time, Hash, Media, System, File, Tools, Logger, Converter, Regex
from lib.modules.interface import Translation, Loader, Dialog, Directory
from lib.modules.database import Database
from lib.modules.concurrency import Pool, Lock
from lib.modules import trakt as Trakt
from lib.meta.data import MetaData

class Playback(Database):

	Table				= 'playback'

	# Values used by Trakt scrobble.
	ActionStart			= 'start'
	ActionPause			= 'pause'
	ActionStop			= 'stop'
	ActionFinish		= 'finish' # Pause when the title was already watched at least once, so we can resume later.

	# Progress
	# Percent when video is considered to have started or ended.
	ProgressStart		= 0.01
	ProgressEndMovie	= 0.94
	ProgressEndShow		= 0.96

	# History
	HistoryEndDefault	= 80
	HistoryEndMinimum	= 45

	# Interval
	# Interval in seconds when progress is updated with new values.
	IntervalExternal	= 300	# Trakt - 5 Minutes
	IntervalInternal	= 30	# Local - 30 Seconds.
	IntervalSeek		= 60	# Seeking position during playback. 60 Seconds.

	# Specials
	SpecialsNone		= False
	SpecialsAll			= True
	SpecialsStory		= 'story'

	# Time
	TimeStart			= '00:00:00'
	TimeMiddle			= '12:00:00'
	TimeEnd				= '23:59:59'

	# Adjust
	AdjustNone			= False
	AdjustInternal		= True
	AdjustSettings		= 'settings'

	# Other
	Autoclosed			= 'autoclosed'
	Instance			= None
	Lock				= Lock()

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Database.__init__(self, Database.NamePlayback)
		self.mLock = Lock()

		self.mSettingsHistoryEnabled = self.settingsHistoryEnabled()
		self.mSettingsHistoryEnd = (self.settingsHistoryEnd() if self.mSettingsHistoryEnabled else Playback.HistoryEndDefault) / 100.0
		self.mSettingsHistoryCount = self.settingsHistoryCount()
		self.mSettingsHistoryCountRewatch = self.settingsHistoryCountRewatch()
		self.mSettingsHistoryProgress = self.settingsHistoryProgress()
		self.mSettingsHistoryProgressResume = self.settingsHistoryProgressResume()

		self.mSettingsRatingEnabled = self.settingsRatingEnabled()
		self.mSettingsRatingMode = self.settingsRatingMode()
		self.mSettingsRatingDialog = self.settingsRatingDialog()
		self.mSettingsRatingBinge = self.settingsRatingBinge()
		self.mSettingsRatingBingeTimeout = self.settingsRatingBingeTimeout()
		self.mSettingsRatingRate = self.settingsRatingRate()
		self.mSettingsRatingRateMovie = self.settingsRatingRateMovie() if self.mSettingsRatingRate else 0
		self.mSettingsRatingRateShow = self.settingsRatingRateShow() if self.mSettingsRatingRate else 0
		self.mSettingsRatingRateSeason = self.settingsRatingRateSeason() if self.mSettingsRatingRate else 0
		self.mSettingsRatingRateEpisode = self.settingsRatingRateEpisode() if self.mSettingsRatingRate else 0

		self.mSettingsRatingRerate = self.settingsRatingRerate()
		self.mSettingsRatingRerateMovie = self.settingsRatingRerateMovie() if self.mSettingsRatingRerate else False
		self.mSettingsRatingRerateShow = self.settingsRatingRerateShow() if self.mSettingsRatingRerate else False
		self.mSettingsRatingRerateSeason = self.settingsRatingRerateSeason() if self.mSettingsRatingRerate else False
		self.mSettingsRatingRerateEpisode = self.settingsRatingRerateEpisode() if self.mSettingsRatingRerate else False

		self.mSettingsTrakt = self._traktEnabled() and self.mSettingsHistoryEnabled
		self.mSettingsTraktStatus = self.mSettingsTrakt and self.mSettingsHistoryCount == 1
		self.mSettingsTraktProgress = self.mSettingsTrakt and self.mSettingsHistoryProgress == 1
		self.mSettingsTraktRating = self._traktEnabled() and self.mSettingsRatingEnabled and self.mSettingsRatingMode == 1

		self.mSettingsTraktPlays = Trakt.settingsPlays()
		self.mSettingsTraktPlaysLast = self.mSettingsTraktPlays == 0
		self.mSettingsTraktPlaysAll = self.mSettingsTraktPlays == 1

		self.mProgressPosition = None
		self.mProgressPause = 0
		self.mProgressInternal = {'action' : None, 'time' : 0}
		self.mProgressExternal = {'action' : None, 'time' : 0}

		self.mHistoryMarked = {}

	@classmethod
	def instance(self):
		if Playback.Instance is None:
			Playback.Lock.acquire()
			if Playback.Instance is None: Playback.Instance = Playback()
			Playback.Lock.release()
		return Playback.Instance

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			Playback.Instance = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _initialize(self):
		self._create('''
			CREATE TABLE IF NOT EXISTS %s
			(
				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,

				numberSeason INTEGER,
				numberEpisode INTEGER,

				timeStarted INTEGER,
				timeUpdated INTEGER,
				timeFinished INTEGER,

				duration INTEGER,

				progressAction TEXT,
				progressPercent REAL,
				progressDuration INTEGER,

				history TEXT,

				rating TEXT,

				PRIMARY KEY(idImdb, idTmdb, idTvdb, idTrakt, numberSeason, numberEpisode)
			);
			''' % Playback.Table
		)

		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON %s(idImdb);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON %s(idTmdb);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON %s(idTvdb);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON %s(idTrakt);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_5 ON %s(numberSeason);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_6 ON %s(numberEpisode);' % (Playback.Table, Playback.Table))

	def _lock(self):
		try: self.mLock.acquire()
		except: pass

	def _unlock(self):
		try: self.mLock.release()
		except: pass

	@classmethod
	def _traktEnabled(self):
		return Trakt.authenticated()

	def _time(self, duration = None, current = None):
		if duration is None or current is None: return None, None, None
		duration = int(duration)
		current = int(current)
		if current <= 0 or duration <= 0: percent = 0
		else: percent = current / float(duration)
		return duration, current, percent

	def _query(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
		query = []

		if imdb: query.append('idImdb = "%s"' % str(imdb))
		if tmdb: query.append('idTmdb = "%s"' % str(tmdb))
		if tvdb: query.append('idTvdb = "%s"' % str(tvdb))
		if trakt: query.append('idTrakt = "%s"' % str(trakt))
		query = ['(%s)' % ' OR '.join(query)]

		# Specifically select where values are NULL.
		# Otherwise if selecting a show (with season = None), if will not pass in the season, and then return the season data instead of the show data.
		#if not season is None: query.append('numberSeason = %s' % int(season))
		#if not episode is None: query.append('numberEpisode = %s' % int(episode))
		if season is None: query.append('(numberSeason IS NULL OR numberSeason = "")')
		elif not season is True: query.append('numberSeason = %s' % int(season))
		if episode is None: query.append('(numberEpisode IS NULL OR numberEpisode = "")')
		elif not episode is True: query.append('numberEpisode = %s' % int(episode))

		return ' WHERE ' + (' AND '.join(query))

	def _add(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, time = None):
		# NB: "INSERT OR IGNORE" only ignores duplicate entries if the primary key does not contain NULL.
		# SQLite sees two NULLs as different values.
		# This means that "INSERT OR IGNORE" will insert duplicate rows if any of its primary key is NULL, which is always the case since either idTmdb or idTvdb will be NULL.
		# Instead of inserting NULL, insert an empty value to insure that the combined primary key is always unique.
		# https://stackoverflow.com/questions/43827629/why-does-sqlite-insert-duplicate-composite-primary-keys

		if imdb is None: imdb = ''
		if tmdb is None: tmdb = ''
		if tvdb is None: tvdb = ''
		if trakt is None: trakt = ''
		if season is None: season = ''
		if episode is None: episode = ''
		return self._insert('''
			INSERT OR IGNORE INTO %s
				(idImdb, idTmdb, idTvdb, idTrakt, numberSeason, numberEpisode, timeStarted)
			VALUES
				(?, ?, ?, ?, ?, ?, ?);
		''' % Playback.Table, [imdb, tmdb, tvdb, trakt, season, episode, time])

	def _retrieve(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, single = False):
		data = self._select('''
			SELECT
				idImdb,
				idTmdb,
				idTvdb,
				idTrakt,

				numberSeason,
				numberEpisode,

				timeStarted,
				timeUpdated,
				timeFinished,

				duration,

				progressAction,
				progressPercent,
				progressDuration,

				history,

				rating
			FROM %s %s;
		''' % (Playback.Table, self._query(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)))

		result = None
		if data:
			result = []
			for item in data:
				result.append({
					'id' : {
						'imdb' : item[0],
						'tmdb' : item[1],
						'tvdb' : item[2],
						'trakt' : item[3],
					},
					'number' : {
						'season' : item[4],
						'episode' : item[5],
					},
					'time' : {
						'started' : item[6],
						'updated' : item[7],
						'finished' : item[8],
					},
					'duration' : item[9],
					'progress' : {
						'action' : item[10],
						'percent' : item[11],
						'duration' : item[12],
					},
					'history' : Converter.jsonFrom(item[13]) if item[13] else [],
					'rating' : Converter.jsonFrom(item[14]) if item[14] else [],
				})

		return result[0] if result and single else result

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def percentStart(self, media = None):
		return Playback.ProgressStart

	@classmethod
	def percentEnd(self, media = None):
		return Playback.ProgressEndShow if Media.typeTelevision(media) else Playback.ProgressEndMovie

	##############################################################################
	# SETTINGS
	##############################################################################

	@classmethod
	def settingsHistoryEnabled(self):
		return Settings.getBoolean('activity.history.enabled')

	@classmethod
	def settingsHistoryEnd(self, percent = False):
		return Settings.getInteger('activity.history.end')

	@classmethod
	def settingsHistoryCount(self):
		return Settings.getInteger('activity.history.count' + ('.alternative' if self._traktEnabled() else ''))

	@classmethod
	def settingsHistoryCountRewatch(self):
		return Settings.getCustom('activity.history.count.rewatch')

	@classmethod
	def settingsHistoryProgress(self):
		return Settings.getInteger('activity.history.progress' + ('.alternative' if self._traktEnabled() else ''))

	@classmethod
	def settingsHistoryProgressResume(self):
		return Settings.getInteger('activity.history.progress.resume')

	@classmethod
	def settingsRatingEnabled(self):
		return Settings.getBoolean('activity.rating.enabled')

	@classmethod
	def settingsRatingMode(self):
		return Settings.getInteger('activity.rating.mode' + ('.alternative' if self._traktEnabled() else ''))

	@classmethod
	def settingsRatingDefault(self):
		return Settings.getInteger('activity.rating.default')

	@classmethod
	def settingsRatingDialog(self):
		return Settings.getBoolean('interface.rating.interface')

	@classmethod
	def settingsRatingBinge(self):
		return Settings.getInteger('activity.rating.binge')

	@classmethod
	def settingsRatingBingeTimeout(self):
		return Settings.getCustom('activity.rating.binge.timeout')

	@classmethod
	def settingsRatingRate(self):
		return Settings.getBoolean('activity.rating.rate')

	@classmethod
	def settingsRatingRateMovie(self):
		return Settings.getInteger('activity.rating.rate.movie')

	@classmethod
	def settingsRatingRateShow(self):
		return Settings.getInteger('activity.rating.rate.show')

	@classmethod
	def settingsRatingRateSeason(self):
		return Settings.getInteger('activity.rating.rate.season')

	@classmethod
	def settingsRatingRateEpisode(self):
		return Settings.getInteger('activity.rating.rate.episode')

	@classmethod
	def settingsRatingRerate(self):
		return Settings.getBoolean('activity.rating.rerate')

	@classmethod
	def settingsRatingRerateMovie(self):
		return Settings.getCustom('activity.rating.rerate.movie')

	@classmethod
	def settingsRatingRerateShow(self):
		return Settings.getCustom('activity.rating.rerate.show')

	@classmethod
	def settingsRatingRerateSeason(self):
		return Settings.getCustom('activity.rating.rerate.season')

	@classmethod
	def settingsRatingRerateEpisode(self):
		return Settings.getCustom('activity.rating.rerate.episode')

	##############################################################################
	# METADATA
	##############################################################################

	# Retrieve the metadata.
	@classmethod
	def metadata(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
		metadata = None
		if Media.typeTelevision(media):
			if not episode is None:
				from lib.indexers.episodes import Episodes
				metadata = Episodes().metadata(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt, season = season, episode = episode)
			elif not season is None:
				from lib.indexers.seasons import Seasons
				metadata = Seasons().metadata(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt, season = season)
			else:
				from lib.indexers.shows import Shows
				metadata = Shows().metadata(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt)
		else:
			from lib.indexers.movies import Movies
			metadata = Movies().metadata(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt)
		return metadata

	# Retrieve the release date.
	@classmethod
	def release(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, timestamp = True, metadata = None):
		time = None
		if metadata is None: metadata = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
		if metadata:
			for attribute in ['aired', 'premiered']:
				if not time and attribute in metadata and metadata[attribute]:
					try:
						if timestamp: time = self.timestamp(metadata[attribute])
						else: time = metadata[attribute]
						if time: break
					except: Logger.error()
		return time

	@classmethod
	def timestamp(self, date, time = TimeMiddle):
		# Make sure the UTC time is taken. If only a date is provided, the local time zone is used.
		# Use 12h00, so that the correct date is used, irrespective of the user's time zone. And it is more likely the user watched it at 12h00 than at 00h00.
		return Time.timestamp(fixedTime = '%sT%s.000Z' % (date, time), iso = True)

	@classmethod
	def timestampInput(self, title, time = TimeMiddle):
		result = False
		choice = Dialog.input(title = title, type = Dialog.InputDate)
		if choice:
			try:
				choice = Regex.extract(data = choice, expression = '(\d{1,2})\/(\d{1,2})\/(\d{4})', all = True, group = None)[0]
				result = self.timestamp(date = '%02d-%02d-%02d' % (int(choice[2]), int(choice[1]), int(choice[0])), time = time)
			except:
				result = None
				Logger.error()
		return result

	# Calculate the number of times an entire show/season was watched completely.
	def count(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, specials = False, metadata = None, history = None):
		if history is None: history = self.retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, adjust = Playback.AdjustSettings)
		if history and 'history' in history: history = history['history']
		if not history or not 'count' in history: return None, None

		if Media.typeMovie(media) or media == Media.TypeEpisode:
			return history['count']['total'], None
		else:
			if metadata is None: metadata = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

			plays = None
			if 'pack' in metadata and metadata['pack']:
				pack = metadata['pack']

				if season is None and episode is None:
					if 'seasons' in pack:
						plays = {}
						for i in pack['seasons']:
							if specials or not i['number'][MetaData.NumberOfficial] == 0:
								if 'episodes' in i:
									for j in i['episodes']:
										if specials or not j['number'][MetaData.NumberOfficial] == 0:
											plays[(i['number'][MetaData.NumberOfficial], j['number'][MetaData.NumberOfficial])] = 0
				elif episode is None:
					if 'seasons' in pack:
						plays = {}
						for i in pack['seasons']:
							if i['number'][MetaData.NumberOfficial] == season:
								if 'episodes' in i:
									for j in i['episodes']:
										if specials or not j['number'][MetaData.NumberOfficial] == 0:
											plays[(i['number'][MetaData.NumberOfficial], j['number'][MetaData.NumberOfficial])] = 0
								break

			if plays:
				episodes = []
				if 'seasons' in history:
					for i in history['seasons']:
						if 'episodes' in i: episodes.extend(i['episodes'])
				elif 'episodes' in history:
					episodes = history['episodes']

				if media == Media.TypeShow and not specials:
					for i in episodes:
						if not i['season'] == 0:
							plays[(i['season'], i['episode'])] = i['count']['total']
				else:
					for i in episodes:
						plays[(i['season'], i['episode'])] = i['count']['total']

				count = min(plays.values())
				full = count + 1
				remaining = [{'season' : k[0], 'episode' : k[1], 'plays' : v} for k, v in plays.items() if v < full]
				if len(remaining) == len(plays): remaining = None # All episodes have been watched the same number of times.
				return count, remaining

		return None, None

	def selection(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, seasonStart = None, seasonEnd = None, episodeStart = None, episodeEnd = None, metadata = None):
		result = []
		if metadata is None: metadata = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

		if 'pack' in metadata and metadata['pack']:
			pack = metadata['pack']
			if 'seasons' in pack:
				for i in pack['seasons']:
					if (seasonStart is None or i['number'][MetaData.NumberOfficial] >= seasonStart) and (seasonEnd is None or i['number'][MetaData.NumberOfficial] <= seasonEnd):
						if 'episodes' in i:
							for j in i['episodes']:
								if (episodeStart is None or j['number'][MetaData.NumberOfficial] >= episodeStart) and (episodeEnd is None or j['number'][MetaData.NumberOfficial] <= episodeEnd):
									result.append({'season' : i['number'][MetaData.NumberOfficial], 'episode' : j['number'][MetaData.NumberOfficial]})

		return result

	def label(self, media):
		label = 33210
		if media == Media.TypeMovie: label = 35496
		elif media == Media.TypeDocumentary: label = 35497
		elif media == Media.TypeShort: label = 35110
		elif media == Media.TypeShow: label = 35498
		elif media == Media.TypeSeason: label = 32055
		elif media == Media.TypeEpisode: label = 33028
		return Translation.string(label)

	def last(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
		from lib.meta.data import MetaData
		last = None
		metadata = self.metadata(media = Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
		if 'pack' in metadata:
			pack = metadata['pack']
			if pack:

				# Last episode in season.
				if not episode is None:
					if 'seasons' in pack and pack['seasons']:
						for i in pack['seasons']:
							if i['number'][MetaData.NumberOfficial] == season:
								last = (episode == i['count']) and i['status'] == MetaData.StatusEnded
								break

				# Last season in show.
				elif not season is None:
					last = (season == pack['count']['season']['main']) and pack['status'] == MetaData.StatusEnded

		return last

	def next(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
		from lib.indexers.episodes import Episodes
		return Episodes().metadataNext(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt, season = season, episode = episode)

	##############################################################################
	# DIALOG
	##############################################################################

	def dialogWatch(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, force = True, internal = None, external = None, refresh = True):
		Loader.show()

		result = False
		alternative = None
		title = 35485
		time = None
		selection = None
		ranged = None
		specials = Playback.SpecialsNone
		label = self.label(media = media)
		alternative = not external is False and internal is False

		# Recently watched. Ask if the user wants to mark it again.
		# Do not do this if an entire show/season is marked.
		if not Media.typeTelevision(media) or not episode is None:
			recent, last = self._historyRecent(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external)
			if recent:
				Loader.hide()
				if Dialog.option(title = title, message = Translation.string(35603) % Time.format(last, format = Time.FormatDate, local = True)): Loader.show()
				else: return result

		# Ask user to mark all or only remaining episodes.
		if media == Media.TypeShow or media == Media.TypeSeason:
			Loader.hide()
			choice = Dialog.options(title = title, message = 35802, labelConfirm = 33029, labelDeny = 33367, labelCustom = 35233)
			if choice == Dialog.ChoiceCancelled: return result
			elif choice == Dialog.ChoiceYes: selection = None
			elif choice == Dialog.ChoiceNo:
				Loader.show()
				count, selection = self.count(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, specials = True)
			elif choice == Dialog.ChoiceCustom:
				ranged = True
				if media == Media.TypeShow and season is None:
					seasonStart = Dialog.input(title = 33313, type = Dialog.InputNumeric)
					if seasonStart is None: return result
					else: seasonStart = int(seasonStart)
					seasonEnd = Dialog.input(title = 33314, type = Dialog.InputNumeric)
					if seasonEnd is None: return result
					else: seasonEnd = int(seasonEnd)
					selection = self.selection(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, seasonStart = seasonStart, seasonEnd = seasonEnd)
				elif media == Media.TypeSeason or (media == Media.TypeShow and not season is None):
					episodeStart = Dialog.input(title = 33315, type = Dialog.InputNumeric)
					if episodeStart is None: return result
					else: episodeStart = int(episodeStart)
					episodeEnd = Dialog.input(title = 33316, type = Dialog.InputNumeric)
					if episodeEnd is None: return result
					else: episodeEnd = int(episodeEnd)
					selection = self.selection(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, seasonStart = season, seasonEnd = season, episodeStart = episodeStart, episodeEnd = episodeEnd)
				if not selection:
					Loader.hide()
					Dialog.notification(title = title, message = 33317, icon = Dialog.IconError)
					return result

		# Ask the user if specials should also be marked when marking an entire show.
		if Media.typeTelevision(media) and season is None and not ranged:
			choice = Dialog.options(title = title, message = 33790, labelConfirm = 33029, labelDeny = 33112, labelCustom = 33111)
			if choice == Dialog.ChoiceCancelled:
				Loader.hide()
				return result
			elif choice == Dialog.ChoiceYes: specials = Playback.SpecialsAll
			elif choice == Dialog.ChoiceNo: specials = Playback.SpecialsNone
			elif choice == Dialog.ChoiceCustom: specials = Playback.SpecialsStory

		# Ask which date to use to mark as watched.
		Loader.hide()
		choice = Dialog.options(title = title, message = 33764, labelConfirm = 33766, labelDeny = 33765, labelCustom = 35233)
		if choice == Dialog.ChoiceCancelled:
			Loader.hide()
			return result
		elif choice == Dialog.ChoiceYes:
			# Use the item's release date.
			# Do not do this for shows/seasons, since every episode's release date has to be retrieved manually.
			if Media.typeMovie(media) or media == Media.TypeEpisode:
				Loader.show()
				time = self.release(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
				if not time:
					Loader.hide()
					Dialog.notification(title = title, message = 33789, icon = Dialog.IconError)
					return result
			else:
				time = True
		elif choice == Dialog.ChoiceCustom:
			# Use a custom date.
			time = self.timestampInput(title = 33767, time = Playback.TimeMiddle)
			if not time:
				if time is None: Dialog.notification(title = title, message = 33788, icon = Dialog.IconError)
				Loader.hide()
				return result

		# Wait for threads to finish, otherwise the threads might not have updated the watched status before refreshing the directory below.
		Loader.show()
		result = self.historyUpdate(time = time, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, selection = selection, specials = specials, force = force, internal = internal, external = external, wait = True)
		Loader.hide()

		if result:
			Dialog.notification(title = title, message = Translation.string(35502 if alternative else 35510) % label, icon = Dialog.IconSuccess)
			if refresh: Directory.refresh(wait = False)
		else:
			Dialog.notification(title = title, message = Translation.string(35604 if alternative else 35554) % label, icon = Dialog.IconWarning)

		return result

	def dialogUnwatch(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, force = True, internal = None, external = None, refresh = True):
		Loader.show()

		result = False
		alternative = None
		title = 35485
		selection = True
		hierarchy = (media == Media.TypeShow or media == Media.TypeSeason) and episode is None
		label = self.label(media = media)
		alternative = not external is False and internal is False

		history = self.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external)
		if hierarchy or (history and history['count']['total'] and history['count']['total'] > 1):
			count, remaining = self.count(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, history = history)
			if hierarchy: message = Translation.string(35747) % (count, history['count']['total'])
			else: message = Translation.string(35746) % count

			Loader.hide()
			choice = Dialog.options(title = title, message = message, labelConfirm = 33029, labelDeny = 35061, labelCustom = 35233)
			if choice == Dialog.ChoiceCancelled:
				return result
			elif choice == Dialog.ChoiceCustom:
				if hierarchy:
					# Date range.
					dateStart = self.timestampInput(title = 33240, time = Playback.TimeStart)
					if not dateStart:
						if dateStart is None: Dialog.notification(title = title, message = 33788, icon = Dialog.IconError)
						return result
					dateEnd = self.timestampInput(title = 33241, time = Playback.TimeEnd)
					if not dateEnd:
						if dateEnd is None: Dialog.notification(title = title, message = 33788, icon = Dialog.IconError)
						return result
					selection = [dateStart, dateEnd]
				else:
					# Specific play.
					Loader.show()
					history = self.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external, detailed = True)
					items = [Time.format(i, format = Time.FormatDateTime, local = True) for i in history['time']['all']]
					Loader.hide()
					choice = Dialog.select(title = title, items = items)
					if choice < 0: return result
					elif choice >= 0: selection = choice
			else:
				if choice == Dialog.ChoiceYes: selection = None
				elif choice == Dialog.ChoiceNo: selection = True

		# Wait for threads to finish, otherwise the threads might not have updated the watched status before refreshing the directory below.
		Loader.show()
		result = self.historyRemove(selection = selection, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, force = force, internal = internal, external = external, wait = True)
		Loader.hide()

		if result:
			Dialog.notification(title = title, message = Translation.string(35503 if alternative else 35511) % label, icon = Dialog.IconSuccess)
			if refresh: Directory.refresh(wait = False)
		else:
			Dialog.notification(title = title, message = Translation.string(35605 if alternative else 35555) % label, icon = Dialog.IconWarning)

		return result

	def dialogRate(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = None, external = None, animation = False, refresh = True, timeout = None):
		Loader.show()

		result = None
		title = 35041
		label = self.label(media = media)
		alternative = not external is False and internal is False

		rating = self.rating(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external, full = True)
		metadata = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

		if timeout:
			from lib.modules.convert import ConverterDuration
			duration = ConverterDuration(value = timeout, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordFixed, unit = ConverterDuration.UnitSecond, years = False, months = False, days = False, hours = False, minutes = False, seconds = True)
			Dialog.notification(title = 35579, message = Translation.string(35057) % duration, icon = Dialog.IconInformation)

		autoclosed = False
		if self.mSettingsRatingDialog == 1:
			rating = Dialog.input(type = Dialog.InputNumeric, title = title, default = rating['rating'] if rating else None, timeout = timeout)
		else:
			from lib.modules.window import WindowRating
			rating = WindowRating.show(metadata = metadata, rating = rating, animation = animation, timeout = timeout, wait = True)
			autoclosed = WindowRating.closedTimeout()

		if rating is None: return Playback.Autoclosed if autoclosed else result
		else: rating = max(1, min(10, int(rating)))

		Loader.show()
		result = self.ratingUpdate(rating = rating, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external, wait = True)
		Loader.hide()

		if result:
			Dialog.notification(title = title, message = Translation.string(35345 if alternative else 35042) % (label, rating), icon = Dialog.IconSuccess)
			if refresh: Directory.refresh(wait = False)
		elif result is None:
			Dialog.notification(title = title, message = Translation.string(35577 if alternative else 35576) % (label, rating), icon = Dialog.IconInformation)
		else:
			Dialog.notification(title = title, message = Translation.string(35347 if alternative else 35044) % label, icon = Dialog.IconWarning)

		return Playback.Autoclosed if autoclosed else result

	def dialogUnrate(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = None, external = None, refresh = True):
		Loader.show()
		result = None
		title = 35041
		label = self.label(media = media)
		alternative = not external is False and internal is False

		rating = self.rating(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external, full = True)

		Loader.hide()
		choice = Dialog.option(title = title, message = Translation.string(35344) % (rating['rating'], Time.format(timestamp = rating['time'], format = Time.FormatDate)), labelConfirm = 33633, labelDeny = 35406)
		if choice: return result

		Loader.show()
		result = self.ratingRemove(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external, wait = True)
		Loader.hide()

		if result:
			Dialog.notification(title = title, message = Translation.string(35346 if alternative else 35043) % label, icon = Dialog.IconSuccess)
			if refresh: Directory.refresh(wait = False)
		else:
			Dialog.notification(title = title, message = Translation.string(35348 if alternative else 35045) % label, icon = Dialog.IconWarning)

		return result

	def dialogAutorate(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, binge = False, automatic = False, internal = None, external = None, refresh = True):
		if self.mSettingsRatingEnabled:
			rate = []
			if Media.typeMovie(media):
				if self.mSettingsRatingRateMovie == 1:
					if self._ratingRerate(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external):
						rate.append({'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'internal' : internal, 'external' : external, 'refresh' : False})
			elif Media.typeTelevision(media):
				if binge:
					if self.mSettingsRatingBinge == 0: return False
					elif self.mSettingsRatingBinge == 1 and automatic: return False

				lastEpisode = self.last(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
				lastSeason = self.last(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season)
				lastAired = not self.next(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

				forceEpisode = False
				rateEpisode = self.mSettingsRatingRateEpisode
				if rateEpisode == 1: rateEpisode = True
				else: rateEpisode = False

				forceSeason = False
				rateSeason = self.mSettingsRatingRateSeason
				if rateSeason == 1: rateSeason = lastEpisode
				elif rateSeason == 2: rateSeason = True
				else: rateSeason = False

				forceShow = False
				rateShow = self.mSettingsRatingRateShow
				ratedShow = self.rating(media = Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, internal = internal, external = external, full = True)
				if rateShow == 1: rateShow = lastEpisode and lastSeason
				elif rateShow == 2: rateShow = lastEpisode
				elif rateShow == 3: rateShow = True
				elif rateShow == 4: rateShow = lastEpisode and (lastSeason or lastAired)
				elif rateShow == 5: rateShow = lastEpisode and (not binge or lastSeason or lastAired)
				elif rateShow == 6:
					forceShow = True
					rateShow = lastEpisode and (not ratedShow or lastSeason)
				elif rateShow == 7:
					forceShow = True
					rateShow = lastEpisode and (not ratedShow or lastSeason or lastAired)
				else: rateShow = False

				if rateEpisode and not episode is None and self._ratingRerate(media = Media.TypeEpisode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external, force = forceEpisode):
					rate.append({'media' : Media.TypeEpisode, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'internal' : internal, 'external' : external, 'refresh' : False})

				if rateSeason and not season is None and self._ratingRerate(media = Media.TypeSeason, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, internal = internal, external = external, force = forceSeason):
					rate.append({'media' : Media.TypeSeason, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'internal' : internal, 'external' : external, 'refresh' : False})

				if rateShow and self._ratingRerate(media = Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, internal = internal, external = external, force = forceShow):
					rate.append({'media' : Media.TypeShow, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'internal' : internal, 'external' : external, 'refresh' : False})

			multiple = len(rate) > 1
			for i in rate:
				if multiple: i['animation'] = True
				if binge and self.mSettingsRatingBingeTimeout: i['timeout'] = self.mSettingsRatingBingeTimeout

			for i in rate:
				# If one dialog timed out and auto closed, do not show the remainder of the dialogs.
				if self.dialogRate(**i) == Playback.Autoclosed: break

			if refresh: Directory.refresh(wait = False)
			return True

	def dialogReset(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = None, external = None, refresh = True):
		Loader.show()
		alternative = not external is False and internal is False
		result = self.progressRemove(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external, wait = True)
		Loader.hide()
		if result:
			Dialog.notification(title = 35006, message = 32308 if alternative else 32057, icon = Dialog.IconSuccess)
			if refresh: Directory.refresh(wait = False)
		else:
			Dialog.notification(title = 35006, message = 32309 if alternative else 32058, icon = Dialog.IconWarning)

	def dialogRefresh(self, media = None):
		Loader.show()
		self.refresh(media = media, wait = True)
		Loader.hide()
		Dialog.notification(title = 35006, message = 35037, icon = Dialog.IconSuccess)
		Directory.refresh(wait = False)

	##############################################################################
	# COMBINED
	##############################################################################

	def refresh(self, media = None, wait = False):
		if self._traktEnabled():
			Trakt.refresh(media = media, wait = wait)
			return True
		return False

	def retrieve(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, adjust = False, internal = None, external = None):
		result = {}

		# Exact searches do not have metadata.
		if not imdb is None or not tmdb is None or not tvdb is None or not trakt is None:
			# Is actually faster without threads.
			# With threads (50 movies): 1.4 - 1.5 secs
			# Without threads (50 movies): 1.1 - 1.2 secs
			'''
			def _retrieve(result, type, function, **kwargs):
				result[type] = function(**kwargs)
			threads = []
			threads.append(Pool.thread(target = _retrieve, kwargs = {'result' : result, 'type' : 'history', 'function' : self.history, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'internal' : internal, 'external' : external}, start = True))
			threads.append(Pool.thread(target = _retrieve, kwargs = {'result' : result, 'type' : 'progress', 'function' : self.progress, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'internal' : internal, 'external' : external, 'adjust' : adjust}, start = True))
			threads.append(Pool.thread(target = _retrieve, kwargs = {'result' : result, 'type' : 'rating', 'function' : self.rating, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'internal' : internal, 'external' : external}, start = True))
			[thread.join() for thread in threads]
			'''

			result['history'] = self.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external)
			result['progress'] = self.progress(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external, adjust = adjust)
			result['rating'] = self.rating(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external)

		return result

	def update(self, action, duration, current, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, specials = SpecialsNone, force = False, internal = None, external = None, wait = False):
		# Exact searches do not have metadata.
		if not imdb is None or not tmdb is None or not tvdb is None or not trakt is None:
			self.progressUpdate(action = action, duration = duration, current = current, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, force = force, internal = internal, external = external, wait = wait)
			self.historyUpdate(duration = duration, current = current, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, specials = specials, force = force, internal = internal, external = external, wait = wait)

	##############################################################################
	# PROGRESS
	##############################################################################

	def progress(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, adjust = False, internal = None, external = None):
		progress = None
		try:
			if external is None: external = True
			if internal is None: internal = True

			limit = None
			if adjust:
				# The limit can be adjusted with either the value from the user's settings, or the hardcoded internal values.
				# When creating list items for the menus, use the setting's value (Playback.AdjustSettings).
				# If the user has watched eg 90% and stops playback, the item is marked as watched (and the user might also rate it).
				# The menu is refreshed and a checkmark icon is now shown, indicating the item was watched, even if it has not exceeded Playback.ProgressEndMovie yet.
				# If menus would use Playback.AdjustInternal instead, items would be marked as watched, but the progress/resume icon would be shown instead of the checkmark.
				# We still want to use Playback.AdjustInternal when resuming playback from player.py.
				# This allows the user to resume playback if they did not watch till the end, although the item was already marked as watched.
				# Eg: 5 mins left before the credits, but then the user falls asleep. Next day the user wants to finish the last few minutes. Also important for binge watching, the user might want to watch the last few minutes of the previous episode to catch up before the next episode.
				end = Playback.ProgressEndShow if Media.typeTelevision(media) else Playback.ProgressEndMovie
				if adjust == Playback.AdjustSettings: end = min(self.mSettingsHistoryEnd, end)
				limit = (Playback.ProgressStart, end)

			if external and self.mSettingsTraktProgress:
				progress = Trakt.progressRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, limit = (limit[0] * 100, limit[1] * 100) if limit else limit) # Set limit here for show/season progress.
				if progress: progress /= 100.0

			if internal and progress is None:
				progress = self._retrieve(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, single = True)
				if progress: progress = progress['progress']['percent']

			if progress and limit:
				if progress < limit[0] or progress > limit[1]: progress = 0
		except: Logger.error()
		return progress if progress else 0

	def progressUpdate(self, action, duration, current, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, force = False, internal = None, external = None, wait = False):
		try:
			time = Time.timestamp() # Before the lock to get the time of the action, not the time the lock was released.
			self._lock() # This function can be called from player.py concurrently.

			if not force:
				# Update if there is a big jump in current playback position, such as seeking or changing chapters.
				if not action == Playback.ActionStart or (not self.mProgressPosition is None and not current is None and (abs(current - self.mProgressPosition) < Playback.IntervalSeek)):
					# The video is paused when the player buffers.
					# Only update every few minutes, otherwise there are too many Trakt calls.
					difference = None
					if internal is None:
						if action == self.mProgressInternal['action']: difference = time - self.mProgressInternal['time']
						elif action == Playback.ActionPause: difference = time - self.mProgressPause
						if difference: internal = difference > Playback.IntervalInternal
					if external is None:
						if action == self.mProgressExternal['action']: difference = time - self.mProgressExternal['time']
						elif action == Playback.ActionPause: difference = time - self.mProgressPause
						if difference: external = difference > Playback.IntervalExternal

			if internal is None: internal = True
			if external is None: external = True

			if force or internal or external:
				self.mProgressPosition = current
				if internal:
					self.mProgressInternal['action'] = action
					self.mProgressInternal['time'] = time
				if external:
					self.mProgressExternal['action'] = action
					self.mProgressExternal['time'] = time

				if action == Playback.ActionPause or action == Playback.ActionFinish: self.mProgressPause = time

				if wait: self._progressUpdate(time = time, action = action, duration = duration, current = current, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external)
				else: Pool.thread(target = self._progressUpdate, kwargs = {'time' : time, 'action' : action, 'duration' : duration, 'current' : current, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'internal' : internal, 'external' : external}, start = True)
			else:
				self._unlock()
		except:
			Logger.error()
			self._unlock()

	def _progressUpdate(self, action, duration, current, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = True, external = True, time = None):
		try:
			duration, current, percent = self._time(duration = duration, current = current)
			if action == Playback.ActionFinish: action = Playback.ActionPause

			if internal:
				if time is None: time = Time.timestamp()
				self._add(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, time = time)
				self._update('''
					UPDATE %s SET
						timeUpdated = ?,
						duration = ?,
						progressAction = ?,
						progressPercent = ?,
						progressDuration = ?
					%s;''' % (Playback.Table, self._query(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)), [time, duration, action, percent, current])

			if external and self.mSettingsTraktProgress:
				Trakt.progressUpdate(action = action, progress = percent * 100, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

		except: Logger.error()
		self._unlock()

	def progressRemove(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = None, external = None, wait = False):
		try:
			time = Time.timestamp() # Before the lock to get the time of the action, not the time the lock was released.
			self._lock() # This function can be called from player.py concurrently.

			if internal is None: internal = True
			if external is None: external = True

			if internal or external:
				if wait: self._progressRemove(time = time, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external)
				else: Pool.thread(target = self._progressRemove, kwargs = {'time' : time, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'internal' : internal, 'external' : external}, start = True)
				return True
			else:
				self._unlock()
		except:
			Logger.error()
			self._unlock()
		return False

	def _progressRemove(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = True, external = True, time = None):
		try:
			if internal:
				if time is None: time = Time.timestamp()
				self._update('''
					UPDATE %s SET
						timeUpdated = ?,
						progressAction = NULL,
						progressPercent = NULL,
						progressDuration = NULL
					%s;''' % (Playback.Table, self._query(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)), [time])

			if external and self.mSettingsTraktProgress:
				Trakt.progressRemove(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

		except: Logger.error()
		self._unlock()

	##############################################################################
	# HISTORY
	##############################################################################

	# NB: detailed == True: retrieve all Trakt play times, instead of just the last one. An additional non-cached API call is being made, so use sparingly and not in batch.
	def history(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = None, external = None, detailed = False):
		history = None
		result = {
			'count' : {
				'total' : None,
				'unique' : None,
			},
			'time' : {
				'last' : None,
				'all' : None,
			},
		}

		try:
			if external is None: external = True
			if internal is None: internal = True

			if external and self.mSettingsTraktStatus:
				history = Trakt.historyRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, detailed = detailed)
				if history:
					result['count']['total'] = history['count']['total']
					result['count']['unique'] = history['count']['unique']
					if 'main' in history['count']: result['count']['main'] = history['count']['main']
					result['time']['last'] = history['time']['last']
					result['time']['all'] = history['time']['all']
					if 'seasons' in history: result['seasons'] = history['seasons']
					if 'episodes' in history: result['episodes'] = history['episodes']

			# NB: If all episodes of a season are marked as watched, except one which is marked locally, but not on Trakt.
			# In such a case, the episode will have a checkmark icon under the episode menu (since the local history is also used).
			# However, the season will have a progress icon.
			# Only use the local history if the user hass no Trakt account or changed the setting to only use local history.
			#if internal and not history:
			if internal and not history and not self.mSettingsTraktStatus:
				items = self._historyItems(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
				seasons = Tools.listUnique([i[0] for i in items if not i[0] is None])
				episodes = Tools.listUnique([i[1] for i in items if not i[1] is None])

				# Make sure season/episode is True (and not None) if we want to retrieve multiple values, such as all episode from a season to determine if the season was fully watched.
				items = self._retrieve(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasons[0] if len(seasons) == 1 else True if len(seasons) > 1 else None, episode = episodes[0] if len(episodes) == 1 else True if len(episodes) > 1 else None)

				if items:
					if media == Media.TypeShow or media == Media.TypeSeason:
						seasons = {}
						for item in items:
							s = item['number']['season']
							if not s in seasons:
								seasons[s] = {
									'season' : s,
									'count' : {
										'total' : None,
										'unique' : None,
									},
									'time' : {
										'last' : None,
										'all' :[],
									},
									'episodes' : [],
								}

							history = item['history']
							if history:
								seasons[s]['episodes'].append({
									'season' : item['number']['season'],
									'episode' : item['number']['episode'],
									'count' : {
										'total' : len(history),
										'unique' : 1,
									},
									'time' : {
										'last' : history[0],
										'all' : history,
									},
								})

						seasons = list(seasons.values())
						seasons = Tools.listSort(seasons, key = lambda x : x['season'])
						for i in seasons:
							try: time = max([j['time']['last'] for j in i['episodes']])
							except: time = None # Sequence/list in max(...) is empty.
							i['count']['total'] = sum([j['count']['total'] for j in i['episodes']])
							i['count']['unique'] = len(i['episodes'])
							i['time']['last'] = time
							i['time']['all'] = [time]
							i['episodes'] = Tools.listSort(i['episodes'], key = lambda x : (x['season'], x['episode']))

						if media == Media.TypeShow:
							try: time = max([max([j['time']['last'] for j in i['episodes']]) for i in seasons])
							except: time = None # Sequence/list in max(...) is empty.
							result.update({
								'count' : {
									'total' : sum([sum([j['count']['total'] for j in i['episodes']]) for i in seasons]),
									'unique' : sum([len(i['episodes']) for i in seasons]),
									'main' : {
										'total' : sum([sum([j['count']['total'] for j in i['episodes']]) for i in seasons if not i['season'] == 0]),
										'unique' : sum([len(i['episodes']) for i in seasons if not i['season'] == 0]),
									},
								},
								'time' : {
									'last' : time,
									'all' : [time],
								},
								'seasons' : seasons,
							})
						else:
							result.update(seasons[0])
					else:
						history = items[0]['history']
						if history:
							result['count']['total'] =  len(history)
							result['count']['unique'] = 1
							result['time']['last'] = history[0]
							result['time']['all'] =  history

		except: Logger.error()
		return result

	def historyUpdate(self, time = None, duration = None, current = None, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, selection = None, specials = SpecialsNone, force = False, internal = None, external = None, wait = False):
		try:
			if time is None: time = Time.timestamp()
			self._lock()

			if internal is None: internal = True
			if external is None: external = True

			id = self._query(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

			# Already marked as watched.
			if not force:
				duration, current, percent = self._time(duration = duration, current = current)

				if id in self.mHistoryMarked:
					self._unlock()
					return False

				# On some hosters (eg: VidLox), if videos are taken down, they replace it with a short 404 video clip.
				# If the video clip is below 30 seconds, assume it is not a valid one, and do not mark progress, binge watch, etc.
				if not duration is None and duration <= Playback.HistoryEndMinimum:
					self._unlock()
					return False

				# Not finished yet.
				if not percent is None and percent < self.mSettingsHistoryEnd:
					self._unlock()
					return False

			self.mHistoryMarked[id] = True
			if wait: self._historyUpdate(time = time, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, selection = selection, specials = specials, force = force, internal = internal, external = external)
			else: Pool.thread(target = self._historyUpdate, kwargs = {'time' : time, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'selection' : selection, 'specials' : specials, 'force' : force, 'internal' : internal, 'external' : external}, start = True)
			return True
		except:
			Logger.error()
			self._unlock()
			return False

	def _historyUpdate(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, selection = None, specials = SpecialsNone, force = False, internal = True, external = True, time = None):
		try:
			if time is None: time = Time.timestamp()
			timeReleased = time is True
			timeCurrent = Time.timestamp()
			timeInteger = Time.integer()

			items = []
			history = self._historyItems(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
			for s, e in history:
				watch = True
				metadata = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e)
				timeRelease = self.release(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e, metadata = metadata)

				if timeReleased:
					time = timeRelease
					if not time: continue

				# Do not mark unreleased episodes.
				# Only do this if an entire show/season is marked, that is if the episode is None.
				if watch and episode is None and Media.typeTelevision(media):
					if timeRelease and Time.integer(Time.format(timeRelease, format = Time.FormatDate)) > timeInteger: watch = False

				# Do not mark specials as watched if the entire show is marked.
				if watch and season is None and episode is None and (s == 0 or e == 0):
					if specials == Playback.SpecialsNone:
						watch = False
					elif specials == Playback.SpecialsStory:
						# Legacy: 'story' was its own attribute before. Now it is part of a dictionary.
						if (not 'story' in metadata or not metadata['story']) and (not 'special' in metadata or not metadata['special'] or not Tools.isDictionary(metadata['special']) or not 'story' in metadata['special'] or not metadata['special']['story']):
							watch = False

				# Episode not part of the remaining episodes to be marked as watched.
				if selection:
					found = False
					for i in selection:
						if i['season'] == s and i['episode'] == e:
							found = True
							break
					if not found: watch = False

				if watch:
					items.append({
						'imdb' : imdb,
						'tmdb' : tmdb,
						'tvdb' : tvdb,
						'trakt' : trakt,
						'season' : s,
						'episode' : e,
						'time' : time,
					})

			if internal:
				for item in items:
					s = item['season']
					e = item['episode']
					time = item['time']

					history = []
					data = self._retrieve(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e, single = True)
					if data:
						data = data['history']
						if data: history = data

					# Rewatched within a short period of time.
					# 0: Always mark rewatch playbacks as watched.
					watch = True
					if not force and self.mSettingsHistoryCountRewatch > 0:
						last = max(history) if history else None
						if last and (time - last) < self.mSettingsHistoryCountRewatch: watch = False

					if watch:
						history.append(time)
						history = Tools.listSort(history, reverse = True) # Put the most recent play at the start, in order keep the same order as in Trakt.

						self._add(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e, time = timeCurrent)
						self._update('''
							UPDATE %s SET
								timeUpdated = ?,
								history = ?
							%s;''' % (Playback.Table, self._query(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e)), [timeCurrent, Converter.jsonTo(history)])

			if external and self.mSettingsTraktStatus:
				updates = []
				for item in items:
					s = item['season']
					e = item['episode']
					time = item['time']

					# Rewatched within a short period of time.
					# 0: Always mark rewatch playbacks as watched.
					watch = True
					if not force and not self.mSettingsTraktPlaysLast and self.mSettingsHistoryCountRewatch > 0:
						data = Trakt.historyRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e)
						if data and 'time' in data:
							last = data['time']
							if last:
								last = last['last']
								if last and (time - last) < self.mSettingsHistoryCountRewatch: watch = False

					if watch: updates.append(item)

				if updates:
					# Remove all watches if user changed the Trakt settings to only keep the last watched playback instead of all.
					if self.mSettingsTraktPlaysLast: Trakt.historyRemove(selection = None, media = media, items = updates)

					Trakt.historyUpdate(media = media, items = updates)

			from lib.modules.video import Trailer
			Trailer().watch(imdb = imdb)
		except: Logger.error()
		self._unlock()

	# selection: None = remove all, False = remove oldest, True = remove most recent, Small Integer = remove specific index, Large Integer = remove specific history ID.
	def historyRemove(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, selection = None, force = False, internal = None, external = None, wait = False):
		try:
			time = Time.timestamp()
			self._lock()

			if internal is None: internal = True
			if external is None: external = True

			id = self._query(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
			try: del self.mHistoryMarked[id]
			except: pass

			if wait: self._historyRemove(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, selection = selection, force = force, internal = internal, external = external, time = time)
			else: Pool.thread(target = self._historyRemove, kwargs = {'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'selection' : selection, 'force' : force, 'internal' : internal, 'external' : external, 'time' : time}, start = True)
			return True
		except:
			Logger.error()
			self._unlock()
			return False

	def _historyRemove(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, selection = None, force = False, internal = True, external = True, time = None):
		try:
			if time is None: time = Time.timestamp()

			items = []
			times = []
			history = self._historyItems(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
			for s, e in history:
				items.append({
					'imdb' : imdb,
					'tmdb' : tmdb,
					'tvdb' : tvdb,
					'trakt' : trakt,
					'season' : s,
					'episode' : e,
				})

			if internal:
				for item in items:
					s = item['season']
					e = item['episode']

					data = self._retrieve(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e, single = True)
					if data:
						data = data['history']
						if data: times = data

						if selection is None: times = None
						elif times:
							if selection is False: times.pop()
							elif selection is True: times.pop(0)
							elif Tools.isInteger(selection):
								# Could potentially fail if the selection integer is from Trakt and the Trakt and local history do not match.
								try: times.pop(selection)
								except: pass
							elif Tools.isArray(selection):
								times = [i for i in times if i < selection[0] or i > selection[1]]

						self._update('''
							UPDATE %s SET
								timeUpdated = ?,
								history = ?
							%s;''' % (Playback.Table, self._query(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e)), [time, Converter.jsonTo(times if times else None)])

			if external and self.mSettingsTraktStatus:

				Trakt.historyRemove(selection = selection, media = media, items = items, wait = True)

			if not times or selection is None:
				from lib.modules.video import Trailer
				Trailer().unwatch(imdb = imdb)
		except: Logger.error()
		self._unlock()

	# Last watched episode for binge watching.
	def historyLast(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = None, external = None):
		history = self.history(media = Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, internal = internal, external = external)
		if history and 'seasons' in history:
			result = {'season' : -1, 'episode' : -1, 'time' : 0}
			for i in history['seasons']:
				if season is None or i['season'] == season:
					if 'episodes' in i:
						for j in i['episodes']:
							if episode is None or j['episode'] >= episode:
								# Either pick the latest time, or if the time is the same, then pick the highest episode number.
								if (j['time']['last'] > result['time']) or (j['time']['last'] == result['time'] and (j['season'] > result['season'] or (j['season'] == result['season'] and j['episode'] > result['episode']))):
									result = {'season' : j['season'], 'episode' : j['episode'], 'time' : j['time']['last']}
			return result if (result and result['time']) else None
		return None

	def _historyItems(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
		items = []
		if Media.typeTelevision(media) and episode is None:
			# Mark an entire season or episode.
			from lib.indexers.shows import Shows
			metadata = Shows().metadata(idImdb = imdb, idTmdb = tmdb, idTvdb = tvdb, idTrakt = trakt)
			if metadata and 'pack' in metadata:
				for i in metadata['pack']['seasons']:
					if season is None or season == i['number'][MetaData.NumberOfficial]:
						for j in i['episodes']:
							items.append((i['number'][MetaData.NumberOfficial], j['number'][MetaData.NumberOfficial]))
						if not season is None: break
		else:
			items.append((season, episode))
		return items

	def _historyRecent(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = None, external = None):
		history = self.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external)
		last = None
		if history and history['count']['total'] and history['time']['last']:
			current = Time.timestamp()
			last = history['time']['last']
			if (current - last) < self.mSettingsHistoryCountRewatch: return True, last
		return False, last

	##############################################################################
	# RATING
	##############################################################################

	def rating(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, full = False, internal = None, external = None):
		rating = None
		try:
			if external is None: external = True
			if internal is None: internal = True

			if external and self.mSettingsTraktRating:
				rating = Trakt.ratingRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, attribute = None if full else 'rating')

			if internal and rating is None:
				data = self._retrieve(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, single = True)
				if data:
					data = data['rating']
					if data:
						rating = data[0]
						if not full: rating = rating['rating']
		except: Logger.error()
		return rating

	def ratingUpdate(self, rating, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = None, external = None, wait = False):
		result = False
		try:
			time = Time.timestamp() # Before the lock to get the time of the action, not the time the lock was released.
			self._lock() # This function can be called from player.py concurrently.

			if internal is None: internal = True
			if external is None: external = True

			if internal or external:
				result = True
				if wait: result = self._ratingUpdate(time = time, rating = rating, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external)
				else: Pool.thread(target = self._ratingUpdate, kwargs = {'time' : time, 'rating' : rating, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'internal' : internal, 'external' : external}, start = True)
			else:
				self._unlock()
		except:
			Logger.error()
			self._unlock()
		return result

	def _ratingUpdate(self, rating, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = True, external = True, time = None):
		result = False
		try:
			if time is None: time = Time.timestamp()

			if internal:
				result = True
				ratings = None
				data = self._retrieve(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, single = True)
				if data: ratings = data['rating']
				if not ratings: ratings = []
				ratings.insert(0, {'time' : time, 'rating' : rating})

				self._add(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, time = time)
				self._update('''
					UPDATE %s SET
						timeUpdated = ?,
						rating = ?
					%s;''' % (Playback.Table, self._query(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)), [time, Converter.jsonTo(ratings)])

			if external and self.mSettingsTraktRating:
				result = Trakt.ratingUpdate(rating = rating, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, time = time)

		except: Logger.error()
		self._unlock()
		return result

	def ratingRemove(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = None, external = None, wait = False):
		try:
			time = Time.timestamp() # Before the lock to get the time of the action, not the time the lock was released.
			self._lock() # This function can be called from player.py concurrently.

			if internal is None: internal = True
			if external is None: external = True

			if internal or external:
				if wait: self._ratingRemove(time = time, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external)
				else: Pool.thread(target = self._ratingRemove, kwargs = {'time' : time, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'internal' : internal, 'external' : external}, start = True)
				return True
			else:
				self._unlock()
		except:
			Logger.error()
			self._unlock()
		return False

	def _ratingRemove(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = True, external = True, time = None):
		try:
			if internal:
				if time is None: time = Time.timestamp()
				self._update('''
					UPDATE %s SET
						timeUpdated = ?,
						rating = NULL
					%s;''' % (Playback.Table, self._query(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)), [time])

			if external and self.mSettingsTraktRating:
				Trakt.ratingRemove(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

		except: Logger.error()
		self._unlock()

	def _ratingRerate(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, internal = True, external = True, force = False):
		try:
			if force: return True

			allow = False
			current = self.rating(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = internal, external = external, full = True)

			if media == Media.TypeShow: rerate = self.mSettingsRatingRerateShow
			elif media == Media.TypeSeason: rerate = self.mSettingsRatingRerateSeason
			elif media == Media.TypeEpisode: rerate = self.mSettingsRatingRerateEpisode
			else: rerate = self.mSettingsRatingRerateMovie

			if current: # Already rated.
				if Tools.isInteger(rerate):
					if rerate == 0: allow = True # Always rerate.
					elif rerate > 0 and (Time.timestamp() - current['time'] > rerate): allow = True # Rerate old.
			else: allow = True # Not rated yet.

			return allow
		except:
			Logger.error()
			return True
