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

from lib.modules.tools import Settings, Time, Hash, Media, System, File, Tools, Title, Logger, Converter, Regex, Sound, Binge, Math
from lib.modules.interface import Translation, Format, Loader, Dialog, Directory
from lib.modules.database import Database
from lib.modules.concurrency import Pool, Lock
from lib.modules import trakt as Trakt

from lib.meta.pack import MetaPack
from lib.meta.manager import MetaManager

# NB: The "quick" parameter.
# Various functions in this class have a "quick" parameter.
# If "quick=False", extended metadata and pack metadata might be retrieved, since the pack data is used to convert/lookup the Trakt numbers.
# Especially retrieving pack data can take very long, easily 100-200+ ms per pack.
# If a show menu with 50 shows is loaded, this can quickly add up to a few seconds to retrieve the packs of all shows, just to determine if a show is fully watched and should get a checkmark.
# If "quick=True", no extended metadata and pack metadata is retrieved, which is a lot faster.
# With this option, the summarized "packed" counters in show/season metadata is used instead. These might not always be perfect, but are mostly good enough to determine the show's watched status.
# Additionally with quick enabled, the episode numbers in the history data might be incorrect if Trakt uses absolute or non-standard numbers.
# However, this might only create a problem if those numbers are used somewhere else.

class Playback(Database):

	Table				= 'playback'

	# Values used by Trakt scrobble.
	ActionStart			= 'start'
	ActionPause			= 'pause'
	ActionStop			= 'stop'
	ActionFinish		= 'finish' # Pause when the title was already watched at least once, so we can resume later.

	# Progress
	# Percent when video is considered to have started or ended.
	ProgressInitiate	= 0.00001
	ProgressStart		= 0.01
	ProgressConclude	= 0.75
	ProgressEndMovie	= 0.93 # 94% is too low. "LOTR The Return of the King" has credits already rolling at just above 93%.
	ProgressEndShow		= 0.95 # 96% is too low. "American Primeval S01E03" has credits already rolling at 96%.

	# History
	HistoryEndDefault	= 80
	HistoryEndMinimum	= 45

	# Interval
	# Interval in seconds when progress is updated with new values.
	IntervalExternal	= 300	# Trakt - 5 Minutes
	IntervalInternal	= 30	# Local - 30 Seconds.
	IntervalSeek		= 60	# Seeking position during playback. 60 Seconds.
	IntervalReload		= 30	# How often menus can be reloaded. 30 Seconds.

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

	# Tag
	TagHorrible			= 'horrible'
	TagTerrible			= 'terrible'
	TagBad				= 'bad'
	TagPoor				= 'poor'
	TagMediocre			= 'mediocre'
	TagFair				= 'fair'
	TagGood				= 'good'
	TagGreat			= 'great'
	TagExcellent		= 'excellent'
	TagPerfect			= 'perfect'
	Tags				= {
		TagHorrible		: 36802,
		TagTerrible		: 36803,
		TagBad			: 35244,
		TagPoor			: 35243,
		TagMediocre		: 36804,
		TagFair			: 36608,
		TagGood			: 35242,
		TagGreat		: 36607,
		TagExcellent	: 35241,
		TagPerfect		: 36805,
	}

	# Error
	ErrorTrakt			=' trakt'

	# Other
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

		self.mSettingsDialogType = self.settingsDialogType()

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

		self.mManager = None

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
				media TEXT,

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

				PRIMARY KEY(media, idImdb, idTmdb, idTvdb, idTrakt, numberSeason, numberEpisode)
			);
			''' % Playback.Table
		)

		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON %s(media);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON %s(idImdb);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON %s(idTmdb);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON %s(idTvdb);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_5 ON %s(idTrakt);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_6 ON %s(numberSeason);' % (Playback.Table, Playback.Table))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_7 ON %s(numberEpisode);' % (Playback.Table, Playback.Table))

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

	def _query(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, attribute = None, full = False):
		query = []

		if media:
			if Media.isSerie(media): media = Media.Show
			query.append('media = "%s"' % str(media))

		subquery = []
		if imdb: subquery.append('idImdb = "%s"' % str(imdb))
		if tmdb: subquery.append('idTmdb = "%s"' % str(tmdb))
		if tvdb: subquery.append('idTvdb = "%s"' % str(tvdb))
		if trakt: subquery.append('idTrakt = "%s"' % str(trakt))
		if subquery: query.append('(%s)' % ' OR '.join(subquery))

		if attribute: query.append('%s IS NOT NULL' % attribute)

		# Specifically select where values are NULL.
		# Otherwise if selecting a show (with season = None), if will not pass in the season, and then return the season data instead of the show data.
		if not full:
			#if not season is None: query.append('numberSeason = %s' % int(season))
			#if not episode is None: query.append('numberEpisode = %s' % int(episode))
			if season is None: query.append('(numberSeason IS NULL OR numberSeason = "")')
			elif not season is True: query.append('numberSeason = %s' % int(season.get(MetaPack.NumberStandard) if Tools.isDictionary(season) else season))
			if episode is None: query.append('(numberEpisode IS NULL OR numberEpisode = "")')
			elif not episode is True: query.append('numberEpisode = %s' % int(episode.get(MetaPack.NumberStandard) if Tools.isDictionary(episode) else episode))

		if query: return ' WHERE ' + (' AND '.join(query))
		else: return ''

	def _add(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, time = None):
		# NB: "INSERT OR IGNORE" only ignores duplicate entries if the primary key does not contain NULL.
		# SQLite sees two NULLs as different values.
		# This means that "INSERT OR IGNORE" will insert duplicate rows if any of its primary key is NULL, which is always the case since either idTmdb or idTvdb will be NULL.
		# Instead of inserting NULL, insert an empty value to insure that the combined primary key is always unique.
		# https://stackoverflow.com/questions/43827629/why-does-sqlite-insert-duplicate-composite-primary-keys

		if Media.isSerie(media): media = Media.Show

		if imdb is None: imdb = ''
		if tmdb is None: tmdb = ''
		if tvdb is None: tvdb = ''
		if trakt is None: trakt = ''

		if season is None: season = ''
		elif Tools.isDictionary(season): season = season.get(MetaPack.NumberStandard)
		if episode is None: episode = ''
		elif Tools.isDictionary(episode): episode = episode.get(MetaPack.NumberStandard)

		return self._insert('''
			INSERT OR IGNORE INTO %s
				(media, idImdb, idTmdb, idTvdb, idTrakt, numberSeason, numberEpisode, timeStarted)
			VALUES
				(?, ?, ?, ?, ?, ?, ?, ?);
		''' % Playback.Table, [media, imdb, tmdb, tvdb, trakt, season, episode, time])

	def _retrieve(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, attribute = None, single = False, full = False):
		if Media.isSerie(media): media = Media.Show
		if Tools.isDictionary(season): season = season.get(MetaPack.NumberStandard)
		if Tools.isDictionary(episode): episode = episode.get(MetaPack.NumberStandard)

		data = self._select('''
			SELECT
				media,

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
		''' % (Playback.Table, self._query(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, attribute = attribute, full = full)))

		result = None
		if data:
			result = []
			for item in data:
				result.append({
					'media' : item[0],
					'id' : {
						'imdb' : item[1] or None,
						'tmdb' : item[2] or None,
						'tvdb' : item[3] or None,
						'trakt' : item[4] or None,
					},
					'number' : {
						'season' : None if item[5] == '' else item[5],
						'episode' : None if item[6] == '' else item[6],
					},
					'time' : {
						'started' : item[7],
						'updated' : item[8],
						'finished' : item[9],
					},
					'duration' : item[10],
					'progress' : {
						'action' : item[11],
						'percent' : item[12],
						'duration' : item[13],
					},
					'history' : Converter.jsonFrom(item[14]) if item[14] else [],
					'rating' : Converter.jsonFrom(item[15]) if item[15] else [],
				})

		return result[0] if result and single else result

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def percentStart(self, media = None):
		return Playback.ProgressStart

	@classmethod
	def percentConclude(self, media = None):
		return Playback.ProgressConclude

	@classmethod
	def percentEnd(self, media = None):
		return Playback.ProgressEndShow if Media.isSerie(media) else Playback.ProgressEndMovie

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
				choice = Regex.extract(data = choice, expression = r'(\d{1,2})\/(\d{1,2})\/(\d{4})', all = True, group = None)[0]
				result = self.timestamp(date = '%02d-%02d-%02d' % (int(choice[2]), int(choice[1]), int(choice[0])), time = time)
			except:
				result = None
				Logger.error()
		return result

	@classmethod
	def label(self, media):
		label = 33210
		if media == Media.Movie: label = 35496
		elif media == Media.Show: label = 35498
		elif media == Media.Season: label = 32055
		elif media == Media.Episode: label = 33028
		return Translation.string(label)

	@classmethod
	def tag(self, tag = None, rating = None, translate = False):
		if tag is None and not rating is None: tag = list(Playback.Tags.keys())[int(rating) - 1]
		if tag:
			label = Playback.Tags.get(tag)
			if label: return Translation.string(label) if translate else label
		else:
			label = list(Playback.Tags.values())
			if translate: return [Translation.string(i) for i in label]
			else: return label
		return None

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

	@classmethod
	def settingsDialogType(self):
		return Settings.getInteger('interface.dialog.interface')

	@classmethod
	def settingsDialogTypeSpecial(self):
		return self.settingsDialogType() == 0

	##############################################################################
	# METADATA
	##############################################################################

	def _single(self, imdb = None, tmdb = None, tvdb = None, trakt = None):
		if imdb or tmdb or tvdb or trakt: return True
		else: return False

	def _quick(self, quick, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None):
		# Never retrieve/generate pack data if not IDs were passed in, meaning the entire history/progress/ratings are requested, not for a single show.
		# This causes a ton of packs to be generated, which takes too long, and is completely infeasible if the user has 1000s of shows in their history.
		if quick is None and Media.isSerie(media):
			if self._single(imdb = imdb, tmdb = tmdb, tvdb = trakt, trakt = trakt): quick = False
			else: quick = True
		return quick

	def _manager(self):
		# Only create on-demand and not immediatly inside the constructor.
		# Otherwise there is a ciruclar instance creation in the cinstructors of the following classes:
		#	MetaManager -> MetaTools -> Playback -> MetaManager -> etc.
		if self.mManager is None: self.mManager = MetaManager.instance()
		return self.mManager

	# Retrieve the metadata.
	def metadata(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, pack = None, quick = None):
		return self._manager().metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, pack = pack, quick = quick)

	def pack(self, imdb = None, tmdb = None, tvdb = None, trakt = None, metadata = None, pack = None, force = False, quick = False):
		if not pack:
			if metadata: pack = metadata.get('pack')
			if not pack and not quick and (imdb or tmdb or tvdb or trakt): pack = self.metadata(media = Media.Pack, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)
		if pack: pack = MetaPack.instance(pack)
		return pack

	# Retrieve the release date.
	def release(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, timestamp = True, metadata = None):
		time = None
		if metadata is None: metadata = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number)
		if metadata:
			for attribute in ['aired', 'premiered']:
				if not time and attribute in metadata and metadata[attribute]:
					try:
						if timestamp: time = self.timestamp(metadata[attribute])
						else: time = metadata[attribute]
						if time: break
					except: Logger.error()
		return time

	# Calculate the number of times an entire show/season was watched completely.
	# quick=True: does not retrieve any additional metadata or packs. It is therefore a lot faster, but might return inaccurate counts if there are number mismatches between Gaia and Trakt. Should be used for eg show menus.
	def count(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, specials = None, metadata = None, pack = None, history = None, quick = None):
		quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)
		if history is None: history, season, episode, metadata, pack = self.retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, metadata = metadata, pack = pack, quick = quick, adjust = Playback.AdjustSettings, detail = True)
		if history and 'history' in history: history = history['history']
		if not history or not 'count' in history: return None, None

		if media == Media.Movie or media == Media.Episode:
			return history['count']['total'], None
		else:
			plays = None
			countOfficial = None
			countSpecial = None
			if specials is None and season == 0: specials = True

			season, episode, metadata, pack = self.lookupStandard(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick, detail = True)
			pack = self.pack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, pack = pack, quick = quick)

			if pack:
				if episode is None:
					plays = {}
					items = self.lookupNumbers(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, metadata = metadata, pack = pack, specials = specials, quick = quick)
					if items:
						for i in items: plays[i] = 0

				# This is a "dirty" way, but probably the only way, of getting the season count for seasons that only exist on IMDb, but not on Trakt/TMDb/TVDb.
				# Eg: The Office UK S03 (IMDb).
				# Note that this does a full episode metadata retrieval, even if this function is called qith "quick=True".
				# Not sure if this might cause slowness for other weird type of seasons.
				if not plays and not season is None and episode is None:
					if metadata is None and not quick: metadata = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number) # No metadata when called from dialohUnwatch().
					if metadata and not(metadata.get('number') or {}).get(MetaPack.ProviderTrakt):
						packed = metadata.get('packed')
						if packed:
							packed = packed.get('count')
							if packed:
								if 'episode' in packed: packed = packed.get('episode')
								count = packed.get(MetaPack.NumberOfficial)
								if count:
									seasons = {}
									for i in range(count):
										# Cannot retrieve these with "quick=True".
										seasonReal, episodeReal = self.lookupTrakt(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = i + 1, number = MetaPack.NumberStandard, pack = pack, quick = None)
										if not episodeReal is None:
											plays[(seasonReal, episodeReal)] = 0
											seasons[seasonReal] = True
									if len(seasons.keys()) == 1:
										seasonReal = next(iter(seasons))
										if not seasonReal == season:
											history, season, episode, metadata, pack = self.retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonReal, metadata = metadata, pack = pack, quick = quick, adjust = Playback.AdjustSettings, detail = True)
											if history and 'history' in history: history = history['history']

			# Quick summarized data, but sometimes slightly less accurate, although not much.
			# This does not require full pack retrieval from database, which can take very long.
			# Useful for show menus, where we do not want to retrieve 50 pack data (sometimes 100-200+ ms for a single pack retrieval).
			elif metadata:
				packed = metadata.get('packed')
				if packed:
					packed = packed.get('count')
					if packed:
						if 'episode' in packed: packed = packed.get('episode')
						countOfficial = packed.get(MetaPack.NumberOfficial)
						countSpecial = packed.get(MetaPack.NumberSpecial)
					else:
						# For Progress menu where only summarized smart pack data is available for episodes.
						packed = metadata.get('smart')
						if packed:
							packed = packed.get('pack')
							if packed:
								packed = packed.get('count')
								if packed:
									packed = packed.get(MetaPack.NumberOfficial)
									if packed:
										countOfficial = packed.get(MetaPack.ValueEpisode)
										countSpecial = packed.get(MetaPack.ValueSpecial)

			if plays or countOfficial:
				if not plays: plays = {}

				episodes = []
				if 'seasons' in history:
					for i in history['seasons']:
						if 'episodes' in i: episodes.extend(i['episodes'])
				elif 'episodes' in history:
					episodes = history['episodes']

				if media == Media.Show and not specials:
					for i in episodes:
						if not i['season'] == 0:
							plays[(i['season'], i['episode'])] = i['count']['total']
				else:
					for i in episodes:
						plays[(i['season'], i['episode'])] = i['count']['total']

				total = min(plays.values()) if plays else 0
				if countOfficial and len(plays.keys()) < countOfficial + (countSpecial if specials else 0): total = 0

				full = total + 1
				remaining = [{'season' : k[0], 'episode' : k[1], 'plays' : v} for k, v in plays.items() if v < full]
				if len(remaining) == len(plays): remaining = None # All episodes have been watched the same number of times.

				return total, remaining

		return None, None

	def selection(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, seasonStart = None, seasonEnd = None, episodeStart = None, episodeEnd = None, number = None, metadata = None, pack = None):
		if not seasonStart is None: seasonStart, episodeStart, metadata, pack = self.lookupStandard(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStart, episode = episodeStart, number = number, metadata = metadata, pack = pack, detail = True)
		if not seasonEnd is None: seasonEnd, episodeEnd, metadata, pack = self.lookupStandard(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonEnd, episode = episodeEnd, number = number, metadata = metadata, pack = pack, detail = True)

		result = []
		items = self.lookupNumbers(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, pack = pack)

		if items:
			for item in items:
				numberSeason = item[0]
				if (seasonStart is None or numberSeason >= seasonStart) and (seasonEnd is None or numberSeason <= seasonEnd):
					numberEpisode = item[1]
					if (episodeStart is None or numberEpisode >= episodeStart) and (episodeEnd is None or numberEpisode <= episodeEnd):
						result.append({'season' : numberSeason, 'episode' : numberEpisode})

		return result

	def last(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None):
		last = None
		if not season is None:
			season, episode, metadata, pack = self.lookupStandard(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, detail = True)
			if not season is None:
				pack = self.pack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, pack = pack)
				if pack:
					last = False
					numberLast = pack.numberLastStandard(season = season)
					if numberLast and numberLast[MetaPack.PartSeason] == season:
						ended = pack.status(season = numberLast[MetaPack.PartSeason]) == MetaPack.StatusEnded

						# Also check the time. In case the pack data was not updated in a while, the status might be outdated.
						if not ended:
							timeLast = pack.time(season = numberLast[MetaPack.PartSeason], episode = numberLast[MetaPack.PartEpisode])
							if timeLast: ended = timeLast < Time.timestamp()

						if not episode is None: last = ended and numberLast[MetaPack.PartEpisode] == episode # Last episode in season.
						elif not season is None: last = ended # Last season in show.

		return last

	def next(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, pack = None):
		return self._manager().metadataEpisodeNext(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, pack = pack)

	##############################################################################
	# DIALOG
	##############################################################################

	def dialogWatch(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, force = True, internal = None, external = None, refresh = True):
		Loader.show()

		result = False
		alternative = None
		title = 35485
		time = None
		selection = None
		ranged = None

		media, season, episode = self.dialogHierarchy(title = title, message = 33397, media = media, season = season, episode = episode, loader = True)
		if media is False: return result

		specials = Playback.SpecialsNone
		label = self.label(media = media)
		alternative = not external is False and internal is False

		# Recently watched. Ask if the user wants to mark it again.
		# Do not do this if an entire show/season is marked.
		if not Media.isSerie(media) or not episode is None:
			recent, last = self._historyRecent(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external)
			if recent:
				Loader.hide()
				if Dialog.option(title = title, message = Translation.string(35603) % Time.format(last, format = Time.FormatDate, local = True)): Loader.show()
				else: return result

		# Ask user to mark all or only remaining episodes.
		if media == Media.Show or media == Media.Season:
			Loader.hide()
			choice = Dialog.options(title = title, message = 35802, labelConfirm = 33029, labelDeny = 33367, labelCustom = 35233)
			if choice == Dialog.ChoiceCanceled: return result
			elif choice == Dialog.ChoiceYes: selection = None
			elif choice == Dialog.ChoiceNo:
				Loader.show()
				count, selection = self.count(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, specials = True)
			elif choice == Dialog.ChoiceCustom:
				ranged = True
				if media == Media.Show and season is None:
					seasonStart = Dialog.input(title = 33313, type = Dialog.InputNumeric)
					if seasonStart is None: return result
					else: seasonStart = int(seasonStart)
					seasonEnd = Dialog.input(title = 33314, type = Dialog.InputNumeric)
					if seasonEnd is None: return result
					else: seasonEnd = int(seasonEnd)
					selection = self.selection(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, seasonStart = seasonStart, seasonEnd = seasonEnd, number = number)
				elif media == Media.Season or (media == Media.Show and not season is None):
					episodeStart = Dialog.input(title = 33315, type = Dialog.InputNumeric)
					if episodeStart is None: return result
					else: episodeStart = int(episodeStart)
					episodeEnd = Dialog.input(title = 33316, type = Dialog.InputNumeric)
					if episodeEnd is None: return result
					else: episodeEnd = int(episodeEnd)
					selection = self.selection(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, seasonStart = season, seasonEnd = season, episodeStart = episodeStart, episodeEnd = episodeEnd, number = number)
				if not selection:
					Loader.hide()
					Dialog.notification(title = title, message = 33317, icon = Dialog.IconError)
					return result

		# Ask the user if specials should also be marked when marking an entire show.
		if Media.isSerie(media) and season is None and not ranged:
			choice = Dialog.options(title = title, message = 33790, labelConfirm = 33029, labelDeny = 33112, labelCustom = 33111)
			if choice == Dialog.ChoiceCanceled:
				Loader.hide()
				return result
			elif choice == Dialog.ChoiceYes: specials = Playback.SpecialsAll
			elif choice == Dialog.ChoiceNo: specials = Playback.SpecialsNone
			elif choice == Dialog.ChoiceCustom: specials = Playback.SpecialsStory

		# Ask which date to use to mark as watched.
		Loader.hide()
		choice = Dialog.options(title = title, message = 33764, labelConfirm = 33766, labelDeny = 33765, labelCustom = 35233)
		if choice == Dialog.ChoiceCanceled:
			Loader.hide()
			return result
		elif choice == Dialog.ChoiceYes:
			# Use the item's release date.
			# Do not do this for shows/seasons, since every episode's release date has to be retrieved manually.
			if media == Media.Movie or media == Media.Episode:
				Loader.show()
				time = self.release(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number)
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
		result = self.historyUpdate(time = time, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, selection = selection, specials = specials, force = force, internal = internal, external = external, detail = True, wait = True)
		Loader.hide()

		if result == Playback.ErrorTrakt:
			Dialog.notification(title = title, message = Translation.string(33943), icon = Dialog.IconWarning)
			result = False
		elif result:
			Dialog.notification(title = title, message = Translation.string(35502 if alternative else 35510) % label, icon = Dialog.IconSuccess)
			if refresh: Directory.refresh(wait = False)
		else:
			Dialog.notification(title = title, message = Translation.string(35604 if alternative else 35554) % label, icon = Dialog.IconWarning)

		return result

	def dialogUnwatch(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, force = True, internal = None, external = None, refresh = True):
		Loader.show()

		result = False
		alternative = None
		title = 35485
		selection = True

		media, season, episode = self.dialogHierarchy(title = title, message = 33398, media = media, season = season, episode = episode, loader = True)
		if media is False: return result

		hierarchy = (media == Media.Show or media == Media.Season) and episode is None
		label = self.label(media = media)
		alternative = not external is False and internal is False

		history = self.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external)
		if hierarchy or (history and history['count']['total'] and history['count']['total'] > 1):
			count, remaining = self.count(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, history = history)
			if hierarchy and not history['count']['total'] is None: message = Translation.string(35747) % (count, history['count']['total'])
			else: message = Translation.string(35746) % count

			Loader.hide()
			choice = Dialog.options(title = title, message = message, labelConfirm = 33029, labelDeny = 35061, labelCustom = 35233)
			if choice == Dialog.ChoiceCanceled:
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
					history = self.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external, detail = True)
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
		result = self.historyRemove(selection = selection, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, force = force, internal = internal, external = external, detail = True, wait = True)
		Loader.hide()

		if result == Playback.ErrorTrakt:
			# This is technically not true.
			# The history unwatch action can only be executed (and therefore cached fro retry) if the internal Trakt history IDs can be retrieved, which cannot, since Trakt is down.
			#Dialog.notification(title = title, message = Translation.string(33943), icon = Dialog.IconWarning)
			Dialog.notification(title = title, message = Translation.string(35605) % label, icon = Dialog.IconWarning)
			result = False
		elif result:
			Dialog.notification(title = title, message = Translation.string(35503 if alternative else 35511) % label, icon = Dialog.IconSuccess)
			if refresh: Directory.refresh(wait = False)
		else:
			Dialog.notification(title = title, message = Translation.string(35605 if alternative else 35555) % label, icon = Dialog.IconWarning)

		return result

	def dialogRate(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, binge = False, internal = None, external = None, indication = False, refresh = True, timeout = False, loader = None, power = False, qr = True, continues = False, image = None):
		from lib.meta.image import MetaImage

		if loader is None: loader = not binge
		if loader: Loader.show()
		Sound.executeRatingStart()

		result = {}
		title = 35041

		media, season, episode = self.dialogHierarchy(title = title, message = 33399, media = media, season = season, episode = episode, loader = loader)
		if media is False: return None

		label = self.label(media = media)
		alternative = not external is False and internal is False

		rating = self.rating(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external, full = True)
		metadata = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number)

		if metadata and not image and Tools.isDictionary(image): image.update(MetaImage.image(data = metadata, default = None, custom = MetaImage.CustomBase))

		# This allows us to cast ratings if the rating dialog does not auto-close (according to the settings).
		def _dialogRate(rating, current = None, result = None, loader = False, refresh = False):
			if rating:
				sound = not Sound.enabledRatingFinish()
				try: rating = rating['rating']
				except: pass
				if rating:
					rating = max(1, min(10, int(rating)))
					tag = self.tag(rating = rating, translate = True)
					if loader: Loader.show()
					rated = self.ratingUpdate(rating = rating, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external, detail = True, wait = True)
					if loader: Loader.hide()
					if rated == Playback.ErrorTrakt:
						Dialog.notification(title = title, message = Translation.string(33943), icon = Dialog.IconWarning)
						rated = False
					elif rated:
						Dialog.notification(title = title, message = Translation.string(35345 if alternative else 35042) % (label, tag, rating), icon = Dialog.IconSuccess, sound = sound)
						if refresh: Directory.refresh(wait = False)
					elif rated is None:
						Dialog.notification(title = title, message = Translation.string(35577 if alternative else 35576) % (label, tag, rating), icon = Dialog.IconInformation, sound = sound)
					else:
						Dialog.notification(title = title, message = Translation.string(35347 if alternative else 35044) % label, icon = Dialog.IconWarning, sound = sound)
					if not result is None:
						result['result'] = rated
						result['rating'] = rating
					return rated
			return None

		autoclosed = False
		if self.mSettingsDialogType == 1:
			if timeout:
				from lib.modules.convert import ConverterDuration
				duration = ConverterDuration(value = timeout, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordFixed, unit = ConverterDuration.UnitSecond, years = False, months = False, days = False, hours = False, minutes = False, seconds = True)
				Dialog.notification(title = 35579, message = Translation.string(35057) % duration, icon = Dialog.IconInformation)
			rating = Dialog.input(type = Dialog.InputNumeric, title = title, default = rating['rating'] if rating else None, timeout = timeout)
			Sound.executeRatingFinish()
		else:
			from lib.modules.window import WindowRating

			# Execute in a thread during binging.
			# Otherwise submitting the rating to Trakt holds up the process before going to the next-episode binge dialog.
			# delay=True: let the thread wait to force Python to start executing other code before the thread's code.
			if binge: callback = lambda input : Pool.thread(target = _dialogRate, kwargs = {'rating' : input, 'current' : rating, 'result' : result, 'loader' : loader, 'refresh' : not binge}, start = True, delay = True)
			else: callback = lambda input : _dialogRate(rating = input, current = rating, result = result, loader = loader, refresh = not binge)

			try: background = image[MetaImage.TypeFanart]
			except: background = None

			rating = WindowRating.show(metadata = metadata, background = background, rating = rating, indication = indication, binge = binge, continues = continues, timeout = timeout, power = power, qr = qr, callback = callback, wait = True)
			if rating:
				if 'timeout' in rating and rating['timeout'] and 'interacted' in rating and not rating['interacted']: autoclosed = True
				elif 'action' in rating and rating['action'] == WindowRating.ActionPower: return False
				elif 'action' in rating and rating['action'] == WindowRating.ActionCancel: return None # Not False, since we want to show the continue dialog even if the rating dialog was canceled (eg: already rated).
				elif 'rating' in rating: rating = rating['rating']
				else: rating = None
			else: rating = None

		if rating is None: return True if autoclosed else None
		if result: result = result['result']
		if not result and not result is False: result = _dialogRate(rating = rating, loader = loader, refresh = not binge)
		return True if autoclosed else (rating or result or None)

	def dialogUnrate(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, internal = None, external = None, refresh = True):
		Loader.show()

		result = None
		title = 35041

		media, season, episode = self.dialogHierarchy(title = title, message = 33399, media = media, season = season, episode = episode, loader = True)
		if media is False: return result

		label = self.label(media = media)
		alternative = not external is False and internal is False
		Sound.executeRatingStart()

		rating = self.rating(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external, full = True)

		Loader.hide()
		choice = Dialog.option(title = title, message = Translation.string(35344) % (rating['rating'], Time.format(timestamp = rating['time'], format = Time.FormatDate)), labelConfirm = 33633, labelDeny = 35406)
		if choice: return result

		Loader.show()
		Sound.executeRatingFinish()
		sound = not Sound.enabledRatingFinish()
		result = self.ratingRemove(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external, detail = True, wait = True)
		Loader.hide()

		if result == Playback.ErrorTrakt:
			Dialog.notification(title = title, message = Translation.string(33943), icon = Dialog.IconWarning)
			result = False
		elif result:
			Dialog.notification(title = title, message = Translation.string(35346 if alternative else 35043) % label, icon = Dialog.IconSuccess, sound = sound)
			if refresh: Directory.refresh(wait = False)
		else:
			Dialog.notification(title = title, message = Translation.string(35348 if alternative else 35045) % label, icon = Dialog.IconWarning, sound = sound)

		return result

	def dialogAutorate(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, binge = False, automatic = False, internal = None, external = None, refresh = True, power = True, qr = True):
		if self.mSettingsRatingEnabled:
			rate = []
			if media == Media.Movie:
				if self.mSettingsRatingRateMovie == 1:
					if self._ratingRerate(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external):
						rate.append({'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'internal' : internal, 'external' : external, 'refresh' : False})
			elif Media.isSerie(media):
				if binge:
					if self.mSettingsRatingBinge == 0: return False
					elif self.mSettingsRatingBinge == 1 and automatic: return False

				lastEpisode = self.last(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number)
				lastSeason = self.last(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, number = number)
				lastAired = not self.next(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number)

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
				ratedShow = self.rating(media = Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, internal = internal, external = external, full = True)
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

				# Pass in an image dictionary.
				# This ensure that when the rating dialogs are shown after playback, that they all (episode, season, show) use the same images.
				# Otherwise the episode and season rating would use the season fanart, while the show rating would use the show fanart.
				image = {}

				if rateEpisode and not episode is None and self._ratingRerate(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external, force = forceEpisode):
					rate.append({'media' : Media.Episode, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'image' : image, 'internal' : internal, 'external' : external, 'refresh' : False})

				if rateSeason and not season is None and self._ratingRerate(media = Media.Season, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, number = number, internal = internal, external = external, force = forceSeason):
					rate.append({'media' : Media.Season, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'number' : number, 'image' : image, 'internal' : internal, 'external' : external, 'refresh' : False})

				if rateShow and self._ratingRerate(media = Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, internal = internal, external = external, force = forceShow):
					rate.append({'media' : Media.Show, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'image' : image, 'internal' : internal, 'external' : external, 'refresh' : False})

			multiple = len(rate) > 1
			for i in rate:
				i['loader'] = False
				i['power'] = power
				i['qr'] = qr
				if multiple:
					i['continues'] = True
					i['indication'] = True
				if binge:
					i['binge'] = binge
					if self.mSettingsRatingBingeTimeout: i['timeout'] = self.mSettingsRatingBingeTimeout

			results = []
			change = False
			for i in rate:
				# Autoclose on timeout without any interaction, or a power action was executed.
				# If one dialog timed out and auto closed, do not show the remainder of the dialogs.
				# Returns True (autoclosed on timeout without interaction), False (power or some other cancellation action), None (not rated or some other failuire), Integer (rating cast).
				result = self.dialogRate(**i)

				results.append(result)
				if result is False or result is True: break
				elif not result is None: change = True

			# Last episode without a continue dialog.
			if multiple and not binge:
				from lib.modules.window import WindowBackground
				WindowBackground.close()

			if refresh and change: Directory.refresh(wait = False)
			return False if False in results else True
		return None

	def dialogReset(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, internal = None, external = None, refresh = True):
		Loader.show()
		alternative = not external is False and internal is False
		result = self.progressRemove(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external, wait = True)
		Loader.hide()
		if result:
			Dialog.notification(title = 35006, message = 32308 if alternative else 32057, icon = Dialog.IconSuccess)
			if refresh: Directory.refresh(wait = False)
		else:
			Dialog.notification(title = 35006, message = 32309 if alternative else 32058, icon = Dialog.IconWarning)

	def dialogRefresh(self, media = None):
		Loader.show()
		self.refresh(media = media, history = True, progress = True, rating = True, wait = True)
		Loader.hide()
		Dialog.notification(title = 35006, message = 35037, icon = Dialog.IconSuccess)
		Directory.refresh(wait = False)

	def dialogContinue(self, metadata, binge = False, default = None):
		from lib.modules.tools import Observer
		from lib.modules.window import WindowContinue
		from lib.modules.convert import ConverterDuration

		if self.mSettingsDialogType == 0:
			return WindowContinue.show(metadata = metadata, binge = binge, default = default)
		else:
			result = {'action' : WindowContinue.ActionNone, 'timeout' : False, 'interacted' : False}

			action = Binge.continueAction()
			timeout = Binge.continueTimeout()
			if default:
				if Tools.isDictionary(default):
					action = default['action']
					timeout = default['timeout']
				else:
					action = default
			action = WindowContinue._intializeDefault(mode = WindowContinue.ModeContinue, action = action)

			choiceCustom = {'label' : 36419, 'action' : WindowContinue.ActionPower}
			choiceCancel = {'label' : 33743, 'action' : WindowContinue.ActionCancel}
			if action == WindowContinue.ActionContinue:
				choiceDefault = {'label' : 33821, 'action' : WindowContinue.ActionContinue}
				choiceAlternative = {'label' : 36174, 'action' : WindowContinue.ActionStop}
			elif action == WindowContinue.ActionStop:
				choiceDefault = {'label' : 36174, 'action' : WindowContinue.ActionStop}
				choiceAlternative = {'label' : 33821, 'action' : WindowContinue.ActionContinue}
			elif action == WindowContinue.ActionCancel:
				choiceDefault = {'label' : 33743, 'action' : WindowContinue.ActionCancel}
				choiceAlternative = {'label' : 33821, 'action' : WindowContinue.ActionContinue}
			elif action:
				choiceDefault = {'label' : 36419, 'action' : WindowContinue.ActionPower}
				choiceAlternative = {'label' : 33821, 'action' : WindowContinue.ActionContinue}
				choiceCustom = {'label' : 36174, 'action' : WindowContinue.ActionStop}

			message = Translation.string(36522)
			if timeout:
				label = choiceDefault['label']
				actions = Observer.settingsActions()
				for i in actions:
					if action == i['action']:
						label = i['label']
						break

				duration = ConverterDuration(value = timeout, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordShort)
				duration = Regex.replace(data = duration, expression = r'(\d+)', replacement = r'[B]\1[/B]', group = None, all = True)

				message += ' ' + Translation.string(36523) % (Format.fontBold(label), duration)

			choice = Dialog.options(title = 36497, message = message, labelConfirm = choiceAlternative['label'], labelDeny = choiceDefault['label'], labelCustom = choiceCustom['label'], timeout = timeout * 1000)
			if choice == Dialog.ChoiceYes: choice = choiceAlternative
			elif choice == Dialog.ChoiceNo: choice = choiceDefault
			elif choice == Dialog.ChoiceCustom: choice = choiceCustom
			else: choice = choiceCancel

			if choice['action'] == WindowContinue.ActionPower:
				action = action or WindowContinue._intializePower(action = True)
				if not action is False: result['action'] = System.power(action = action, proper = True, notification = True)
			else:
				result['action'] = choice['action']
			return result

	def dialogHierarchy(self, title, message, media, season = None, episode = None, loader = True):
		# If an episode from the Progress menu is marked as watched, the media is "show", but there is also a season/episode number.
		# Ask the user if a single episode, a season, or the full show should be marked as watched.
		if not episode is None and media and not media == Media.Episode:
			message = Translation.string(message) % (Title.numberUniversal(media = Media.Episode, season = season, episode = episode), Title.numberUniversal(media = Media.Season, season = season))
			choice = Dialog.options(title = title, message = message, labelConfirm = 33028, labelDeny = 32055, labelCustom = 35498)
			if choice == Dialog.ChoiceCanceled:
				if loader: Loader.hide()
				return False, False, False
			elif choice == Dialog.ChoiceYes:
				media = Media.Episode
			elif choice == Dialog.ChoiceNo:
				media = Media.Season
				episode = None
			elif choice == Dialog.ChoiceCustom:
				media = Media.Show
				season = None
				episode = None
		return media, season, episode

	##############################################################################
	# COMBINED
	##############################################################################

	def refresh(self, media = None, history = None, progress = None, rating = None, force = False, reload = True, wait = False):
		if self._traktEnabled():
			# If a single one of these is set to True, only refresh that one.
			if history is None and progress is None and rating is None:
				history = True
				progress = True
				rating = True
			Trakt.refresh(media = media, history = history, progress = progress, rating = rating, force = force, reload = reload, wait = wait)
			return True
		return False

	def reload(self, media = None, history = False, progress = False, rating = False, arrival = False, bulk = False, accelerate = False, launch = False, force = False, wait = False):		
		# The menu reloading could take place in a thread, but this could hold up other important code, since some menus can take a long time to refresh.
		# Even if we add a delay/sleep to the reload thread, allowing other code to execute first, eventually the reloading execution will catch up.
		# Smart-reloading will also background retrieve metadata and has to do a lot of processing to smart-assemble the menus, which is all too much for a "quick" reload.
		# Instead, reload in its own process, so that it does not hold up other code, and has its own core for execution.
		if wait:
			self._reload(media = media, history = history, progress = progress, arrival = arrival, bulk = bulk, accelerate = accelerate, launch = launch, force = force)
		else:
			#Pool.thread(target = self._reload, kwargs = {'media' : media, 'history' : history, 'progress' : progress, 'rating' : rating, 'arrival' : arrival, 'bulk' : bulk, 'accelerate' : accelerate, 'launch' : launch, 'force' : force}, start = True)
			System.executePlugin(action = 'playbackReload', parameters = {'media' : media, 'history' : history, 'progress' : progress, 'rating' : rating, 'arrival' : arrival, 'bulk' : bulk, 'accelerate' : accelerate, 'launch' : launch, 'force' : force})

	def _reload(self, media = None, history = False, progress = False, rating = False, arrival = False, bulk = False, accelerate = False, launch = False, force = False):
		from lib.modules.cache import Memory
		from lib.modules.tools import Eminence

		# When we watch an episode and afterwards load the Trakt progress menu, the previously watched show is not listed.
		# This is probably because Gaia thinks there are no new episodes, since the last episode it knows of, has just been watched.
		# If the progress menu is reloaded manually (navigate back and load menu again), the show is listed again.
		# Auto reload here if the history changed, so that the user does not have to manually reload the list.

		# Do not reload if the previous reload was only a few seconds ago.
		# Since this function can be called multiple times after playback has finished. From trakt.py -> historyRefresh() and progressRefresh().
		time = Time.timestamp()
		if Media.isSerie(media): media = Media.Show

		id = 'GaiaPlaybackReload'
		reload = Memory.get(id = id, local = True, kodi = True)

		# NB: Place Shows first, followed by Movies, and then the rest.
		# Since execution for each indexer can take long, do the important ones (Shows and Movies) first, since we might need to refresh the Kodi menu with the new data.
		if not reload:
			reload = {
				Media.Show	: {'history' : 0, 'progress' : 0, 'rating' : 0, 'arrival' : 0, 'bulk' : 0},
				Media.Movie	: {'history' : 0, 'progress' : 0, 'rating' : 0, 'arrival' : 0, 'bulk' : 0},
				Media.Mixed	: {'history' : 0, 'progress' : 0, 'rating' : 0, 'arrival' : 0, 'bulk' : 0},
			}

		allow = {
			Media.Show	: {'history' : False, 'progress' : False, 'rating' : False, 'arrival' : False, 'bulk' : False},
			Media.Movie	: {'history' : False, 'progress' : False, 'rating' : False, 'arrival' : False, 'bulk' : False},
			Media.Mixed	: {'history' : False, 'progress' : False, 'rating' : False, 'arrival' : False, 'bulk' : False},
		}

		update = {}
		if history: update['history'] = True
		if progress: update['progress'] = True
		if rating: update['rating'] = True
		if arrival: update['arrival'] = True

		for key in allow.keys():
			if media is None or media == key:
				for i in update.keys():
					if force: value = True
					else: value = time - reload[key][i] > Playback.IntervalReload
					allow[key][i] = value

					# If movies or shows are updated, also update the mixed menus.
					# This will not refresh any data, only reload the mixed menus using the previously refreshed movie/show metadata.
					if media == Media.Show or media == Media.Movie: allow[Media.Mixed][i] = value

		if bulk: allow[Media.Mixed]['bulk'] = True # Only do this for mixed media.

		# Set the global variable before actually reloading the menus.
		# In case another reload process is started, to prevent double execution.
		for key in allow.keys():
			for i in update.keys():
				if allow[key][i]: reload[key][i] = time
		Memory.set(id = id, value = reload, local = True, kodi = True)

		# Do bulk reloading first, since it will show a dialog and require a reload afterwards.
		for key, value in allow.items():
			if value['bulk']:
				value['bulk'] = False # Do not do again below.
				MetaManager.reload(media = key, accelerate = accelerate, launch = launch, bulk = True) # Only do bulk here.

		for key, value in allow.items():
			if any(value.values()):
				# NB: Do not use the MetaManager singleton instance.
				# During reloading, the MetaManager sets a custom cache delay that should not be set globally for the singleton.
				#manager = self._manager()
				MetaManager.reload(media = key, accelerate = accelerate, launch = launch, **value)

				# Reload the list content in the widget of the Quick view.
				Eminence.widgetReload(media = key)

	def preload(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, number = None, metadata = None, delay = True, wait = False):
		if wait or wait is None: self._preload(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, number = number, metadata = metadata, delay = delay)
		else: Pool.thread(target = self._preload, kwargs = {'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'number' : number, 'metadata' : metadata, 'delay' : delay}, start = True)

	def _preload(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, number = None, metadata = None, delay = None):
		if delay: Pool.wait(delay = 10.0 if delay is True else delay, minimum = True)

		if metadata:
			if not media: media = metadata.get('media')
			if not imdb: imdb = metadata.get('imdb')
			if not tmdb: tmdb = metadata.get('tmdb')
			if not tvdb: tvdb = metadata.get('tvdb')
			if not trakt: trakt = metadata.get('trakt')
			if season is None: season = metadata.get('season') # Allow S0.

		self._manager().metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, number = number)

	# wait=None: only wait for the Trakt refresh, but not the menu reloading.
	def launch(self, refresh = True, reload = True, bulk = False, force = False, delay = None, wait = None):
		if wait or wait is None: self._launch(refresh = refresh, reload = reload, bulk = bulk, force = force, delay = delay, wait = wait)
		else: Pool.thread(target = self._launch, kwargs = {'refresh' : refresh, 'reload' : reload, 'bulk' : bulk, 'force' : force, 'delay' : delay, 'wait' : None}, start = True)

	def _launch(self, refresh = True, reload = True, bulk = False, force = False, delay = None, wait = True):
		if delay: Pool.wait(delay = 3.0 if delay is True else delay, minimum = True)
		if refresh: self.refresh(history = True, progress = True, rating = True, force = force, reload = False, wait = True if wait is None else wait) # Do not reload, since we reload below.
		if bulk: self.reload(history = False, progress = False, arrival = False, bulk = True, launch = True, force = force, wait = False if wait is None else wait) # Only do this when Gaia is launched in the foreground, since it might show a dialog and requires a restart.
		if reload: self.reload(history = True, progress = True, arrival = True, bulk = False, launch = True, force = force, wait = False if wait is None else wait)

	def retrieve(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, adjust = False, internal = None, external = None, quick = None, detail = False):
		result = {}

		# Exact searches do not have metadata.
		if imdb or tmdb or tvdb or trakt:
			# Treat Recaps and Extras as episodes for lookups.
			# They have the first/last episode's metadata.
			if Media.isBonus(media): media = Media.Episode

			quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

			# Do here, so we only need a single lookup for the various functions below.
			if Media.isSerie(media): season, episode, metadata, pack = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick, detail = True, combine = True)

			# Is actually faster without threads.
			# With threads (50 movies): 1.4 - 1.5 secs
			# Without threads (50 movies): 1.1 - 1.2 secs
			'''
			def _retrieve(result, type, function, **kwargs):
				result[type] = function(**kwargs)
			threads = []
			threads.append(Pool.thread(target = _retrieve, kwargs = {'result' : result, 'type' : 'history', 'function' : self.history, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'metadata' : metadata, 'pack' : pack, 'internal' : internal, 'external' : external, 'quick' : quick}, start = True))
			threads.append(Pool.thread(target = _retrieve, kwargs = {'result' : result, 'type' : 'progress', 'function' : self.progress, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'metadata' : metadata, 'pack' : pack, 'internal' : internal, 'external' : external, 'quick' : quick, 'adjust' : adjust}, start = True))
			threads.append(Pool.thread(target = _retrieve, kwargs = {'result' : result, 'type' : 'rating', 'function' : self.rating, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'metadata' : metadata, 'pack' : pack, 'internal' : internal, 'external' : external, 'quick' : quick}, start = True))
			[thread.join() for thread in threads]
			'''

			result['history'] = self.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, internal = internal, external = external, quick = quick)

			progress = self.progress(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, internal = internal, external = external, quick = quick, adjust = adjust, items = True)
			if progress:
				if Tools.isList(progress): progress = progress[0]
				time = progress.get('time')
				if Tools.isDictionary(time): progress = {'value' : progress.get('progress').get('percent'), 'time' : time.get('updated')} # Local
				else: progress = {'value' : progress.get('progress'), 'time' : progress.get('time')} # Trakt
			else:
				progress = None
			result['progress'] = progress

			rating = self.rating(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, internal = internal, external = external, quick = quick, full = True)
			if rating:
				time = rating.get('time')
				if Tools.isDictionary(time): rating = {'value' : rating.get('rating'), 'time' : time.get('updated')} # Local
				else: rating = {'value' : rating.get('rating'), 'time' : rating.get('time')} # Trakt
			else:
				rating = None
			result['rating'] = rating

		if detail: return result, season, episode, metadata, pack
		else: return result

	def update(self, action, duration, current, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, specials = SpecialsNone, metadata = None, pack = None, force = False, internal = None, external = None, wait = False):
		# Exact searches do not have metadata.
		if imdb or tmdb or tvdb or trakt:
			self.progressUpdate(action = action, duration = duration, current = current, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, force = force, internal = internal, external = external, wait = wait)
			self.historyUpdate(duration = duration, current = current, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, specials = specials, metadata = metadata, pack = pack, force = force, internal = internal, external = external, wait = wait)

	##############################################################################
	# LOOKUP
	##############################################################################

	# Get the Trakt season and episode number from the pack using a specific number type.
	# input=False: already looked up, just return the numbers as is.
	# strict=True: return None if the episode cannot be found.
	def lookup(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, input = None, output = None, metadata = None, pack = None, quick = False, strict = False, detail = False):
		lookup = None
		if not input is False and Media.isSerie(media):
			if input is None: input = MetaPack.NumberUniversal # NB: Use NumberUniversal, not NumberStandard, so that we can lookup both standard and sequential numbers.

			# Do not lookup again if a previous function already did the lookup, aka the season/episode parameter is a dict.
			doneSeason = Tools.isDictionary(season)
			doneEpisode = Tools.isDictionary(episode)
			if doneSeason or doneEpisode:
				if doneSeason: season = season.get(output or MetaPack.NumberStandard)
				if doneEpisode: episode = episode.get(output or MetaPack.NumberStandard)
				if doneSeason and doneEpisode: lookup = [season, episode]

			if not lookup and not season is None:
				pack = self.pack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, pack = pack, quick = quick)
				if pack: lookup = pack.lookup(season = season, episode = episode, input = input, output = output)

				# Episodes that are not part of the pack.
				# These are only retrieved in MetaManager.metadataEpisode().
				# Eg: Downton Abbey S02E09 (IMDb).
				if not lookup and not episode is None:
					if not metadata and not quick and (imdb or tmdb or tvdb or trakt):
						quick = False if quick is None else None # If quick=None: retrieve, but only from cache.
						metadata = self.metadata(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, quick = quick, pack = False)
					if metadata:
						lookup = metadata.get('number')
						if lookup:
							lookup = lookup.get(output)
							try: lookup = lookup.get(MetaPack.NumberStandard)
							except: pass # Normal standard lookup, not inside Trakt.

		if not lookup is None:
			if Tools.isList(lookup):
				season = lookup[MetaPack.PartSeason]
				episode = lookup[MetaPack.PartEpisode]
			else: # Season number only.
				season = lookup
		elif strict and not input is False:
			season = None
			episode = None

		if detail: return season, episode, metadata, pack
		else: return season, episode

	# More efficient lookup of both Trakt+Standard numbers, since metadata and pack is only retrieved once.
	def lookupCombined(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, quick = False, strict = None, detail = False, combine = False):
		seasonStandard = None
		episodeStandard = None
		seasonTrakt = None
		episodeTrakt = None

		if Media.isShow(media):
			if not episode is None: media = Media.Episode
			elif not season is None: media = Media.Season

		if Media.isSeason(media) or Media.isEpisode(media):
			seasonTrakt, episodeTrakt, metadata, pack = self.lookupTrakt(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick, strict = True if strict is None else strict, detail = True)

			seasonStandard, episodeStandard, metadata, pack = self.lookupStandard(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick, strict = False if strict is None else strict, detail = True)

		if combine:
			if Media.isShow(media):
				season = None
				episode = None
			else:
				season = {MetaPack.NumberStandard : seasonStandard, MetaPack.ProviderTrakt : seasonTrakt}
				episode = {MetaPack.NumberStandard : episodeStandard, MetaPack.ProviderTrakt : episodeTrakt}
			if detail: return season, episode, metadata, pack
			else: return season, episode
		else:
			if detail: return seasonStandard, episodeStandard, seasonTrakt, episodeTrakt, metadata, pack
			else: return seasonStandard, episodeStandard, seasonTrakt, episodeTrakt

	def lookupStandard(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, quick = False, strict = False, detail = False):
		return self.lookup(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, input = number, output = MetaPack.NumberStandard, metadata = metadata, pack = pack, quick = quick, strict = strict, detail = detail)

	def lookupTrakt(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, quick = False, strict = False, detail = False):
		return self.lookup(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, input = number, output = MetaPack.ProviderTrakt, metadata = metadata, pack = pack, quick = quick, strict = strict, detail = detail)

	def lookupTvdb(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, quick = False, strict = False, detail = False):
		return self.lookup(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, input = number, output = MetaPack.ProviderTvdb, metadata = metadata, pack = pack, quick = quick, strict = strict, detail = detail)

	def lookupNumbers(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, metadata = None, pack = None, specials = True, quick = False):
		items = []
		if Media.isSerie(media) and episode is None:
			if Tools.isDictionary(season): season = season.get(MetaPack.NumberStandard)
			if Tools.isDictionary(episode): episode = episode.get(MetaPack.NumberStandard)
			pack = self.pack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, pack = pack, quick = quick)

			if pack:
				# Mark an entire season or episode.
				for i in pack.season(default = []):
					# NB: Also allow non-official seasons, but then all episode in that season should have the same type.
					# Eg: Dragon Ball Super S02 (only on TVDb, but not on Trakt).
					official = pack.typeOfficial(item = i)
					unofficial = pack.typeUnofficial(item = i)
					standard = False if official else pack.typeStandard(item = i)

					# Eg: Dragon Ball Super (Series and Absolute menu).
					if season is None: universal = pack.typeOfficial(season = 1) and pack.typeUnofficial(season = 2)
					else: universal = season == 1 and pack.typeUnofficial(season = season + 1)

					if official or standard or (specials and pack.typeSpecial(item = i)):
						numberSeason = pack.numberStandard(item = i)
						if (specials or not numberSeason == 0) and (season is None or season == numberSeason):
							for j in pack.episode(season = numberSeason, default = []):
								if not specials and pack.typeSpecial(item = j): add = False
								elif unofficial and season is None: add = False # Update (2025-03). Eg: Dragon Ball Super S02+. Otherwise the Series/Absolute menus do not get a watched checkmark if all episodes were watched. Do not do this for season menus.
								elif universal: add = pack.typeUniversal(item = j) or (standard and pack.typeStandard(item = j))
								elif season is None: add = pack.typeOfficial(item = j)
								elif season == 0: add = pack.typeOfficial(item = j)
								else: add = (official and pack.typeOfficial(item = j)) or (standard and pack.typeStandard(item = j))
								if add:
									numberEpisode = pack.numberStandardEpisode(item = j)
									items.append((numberSeason, numberEpisode))
							if not season is None: break

		elif Media.isMovie(media) or not season is None:
			items.append((season, episode))
		return items

	def lookupItems(self, items, media = None, season = None, episode = None, metadata = None, pack = None, quick = False):
		try:
			if Media.isSerie(media):
				single = not Tools.isArray(items)
				if single:
					id = items.get('id')
					if id: pack = self.pack(imdb = id.get('imdb'), tmdb = id.get('tmdb'), tvdb = id.get('tvdb'), trakt = id.get('trakt'), metadata = metadata, pack = pack, quick = quick)
				items = Tools.copy(items) # Copy because we edit the numbers below and insert alternative seasons.

				for item in [items] if single else items:
					if not single:
						id = item.get('id')
						if id: pack = self.pack(imdb = id.get('imdb'), tmdb = id.get('tmdb'), tvdb = id.get('tvdb'), trakt = id.get('trakt'), quick = quick)
					if pack: # Will only be available if the pack data is passed into this function, or if quick = False.
						alternative = None
						if 'seasons' in item: # For show history.
							seasons = {}
							alternative = {}

							for i in item['seasons']:
								seasonBase, _ = self.lookupStandard(media = Media.Season, season = i.get('season'), number = MetaPack.ProviderTrakt, metadata = metadata, pack = pack)
								if not seasonBase is None: i['season'] = seasonBase
								seasons[seasonBase] = True

								for j in i.get('episodes', []):
									seasonNew, episodeNew = self.lookupStandard(media = Media.Episode, season = j.get('season'), episode = j.get('episode'), number = MetaPack.ProviderTrakt, metadata = metadata, pack = pack)
									if not seasonNew is None and not episodeNew is None:
										j['season'] = seasonNew
										j['episode'] = episodeNew
										if not seasonBase == seasonNew:
											if not seasonNew in alternative: alternative[seasonNew] = []
											alternative[seasonNew].append(j)

							# If Trakt has only one absolute season, while TVDb has multiple seasons.
							# The Trakt data will only have 1 season, but after number conversion it might turn out there are more seasons.
							# Manually add these seasons after lookup.
							# Needed in self.count() to correctly determine season history.
							if alternative:
								for k, v in alternative.items():
									if not k in seasons:
										episodes = Tools.copy(v)
										try: time = max([e['time']['last'] or 0 for e in episodes]) or None
										except: time = None # Sequence/list in max(...) is empty.
										item['seasons'].append({
											'season' : k,
											'count' : {
												'total' : sum([e['count']['total'] for e in episodes]),
												'unique' : sum([e['count']['unique'] for e in episodes]),
											},
											'time' : {
												'last' : time,
												'all' : [time] if time else [],
											},
											'episodes' : episodes,
										})

						elif 'episodes' in item: # For season history.
							unoffical = pack.typeUnofficial(season = season)
							for i in item['episodes']:
								if unoffical and not i.get('season') == season:
									# Dragon Ball super S02+.
									# Otherwise the unoffical TVDb seasons for S02+ are not marked as watched if all S01E01-S01E131 were watched.
									seasonNew, episodeNew = self.lookupTvdb(media = Media.Episode, season = i.get('season'), episode = i.get('episode'), number = MetaPack.ProviderTrakt, metadata = metadata, pack = pack)
								else:
									seasonNew, episodeNew = self.lookupStandard(media = Media.Episode, season = i.get('season'), episode = i.get('episode'), number = MetaPack.ProviderTrakt, metadata = metadata, pack = pack)

								if not seasonNew is None and not episodeNew is None:
									if not season == seasonNew: alternative = True
									i['season'] = seasonNew
									i['episode'] = episodeNew

							if alternative:
								episodes = item['episodes'] = [i for i in item['episodes'] if i.get('season') == season]

								item['count']['total'] = sum([i['count']['total'] for i in episodes])
								item['count']['unique'] = sum([i['count']['unique'] for i in episodes])

								try: time = max([e['time']['last'] or 0 for e in episodes]) or None
								except: time = None # Sequence/list in max(...) is empty.
								item['time']['last'] = time
								item['time']['all'] = [time] if time else []

						else: # For individual episode history.
							seasonNew, episodeNew = self.lookupStandard(media = Media.Episode, season = item.get('season'), episode = item.get('episode'), number = MetaPack.ProviderTrakt, metadata = metadata, pack = pack)
							if not seasonNew is None and not episodeNew is None:
								item['season'] = seasonNew
								item['episode'] = episodeNew

		except: Logger.error()
		return items

	##############################################################################
	# PROGRESS
	##############################################################################

	def progress(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, adjust = False, internal = None, external = None, quick = None, items = False):
		progress = None
		try:
			# Do not return the progress for Season menus, since only episodes can have progress.
			seasonReal = season
			if Tools.isDictionary(seasonReal): seasonReal = seasonReal.get(MetaPack.NumberStandard)
			episodeReal = episode
			if Tools.isDictionary(episodeReal): episodeReal = episodeReal.get(MetaPack.NumberStandard)

			if not(media == Media.Season and not seasonReal is None and episodeReal is None):

				if external is None: external = True
				if internal is None: internal = True

				quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)
				serie = Media.isSerie(media)
				seasonStandard = None
				episodeStandard = None
				seasonTrakt = None
				episodeTrakt = None

				if serie: seasonStandard, episodeStandard, seasonTrakt, episodeTrakt = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick)

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
					end = Playback.ProgressEndShow if Media.isSerie(media) else Playback.ProgressEndMovie
					if adjust == Playback.AdjustSettings: end = min(self.mSettingsHistoryEnd, end)
					limit = (Playback.ProgressInitiate, end) # Use ProgressInitiate instead of ProgressStart.

				if external and self.mSettingsTraktProgress:
					# Some seasons are not on Trakt.
					# Eg: Dragon Ball Super S02+.
					if (not Media.isSeason(media) or not seasonTrakt is None) and (not Media.isEpisode(media) or not episodeTrakt is None):
						progress = Trakt.progressRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonTrakt, episode = episodeTrakt, limit = (limit[0] * 100, limit[1] * 100) if limit else limit, attribute = None) # Set limit here for show/season progress.
						if progress:
							if items:
								# Make shallow copies, since we change the progress percentage.
								# Otherwise we edit the cached data from trakt.py.
								if Tools.isList(progress):
									for i in range(len(progress)):
										item = Tools.copy(progress[i], deep = False)
										item['progress'] = item['progress'] / 100.0
										progress[i] = item
								else:
									progress = Tools.copy(progress, deep = False)
									progress['progress'] = progress['progress'] / 100.0
								return progress
							else:
								progress = progress['progress'] / 100.0

				if internal and progress is None:
					progress = self._retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard, single = not items, full = items if seasonStandard is None else False, attribute = 'progressPercent')
					if progress:
						if items:
							result = progress
							for item in result:
								progress = item['progress']['percent']
								if progress and limit and (progress < limit[0] or progress > limit[1]): item['progress']['percent'] = 0
							return result
						else:
							progress = progress['progress']['percent']

				if progress and limit and (progress < limit[0] or progress > limit[1]): progress = 0
		except: Logger.error()
		return [] if items else progress if progress else 0

	def progressUpdate(self, action, duration, current, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, force = False, internal = None, external = None, detail = False, quick = None, wait = False):
		result = False
		try:
			time = Time.timestamp() # Before the lock to get the time of the action, not the time the lock was released.
			self._lock() # This function can be called from player.py concurrently.

			quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

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
				result = True

				self.mProgressPosition = current
				if internal:
					self.mProgressInternal['action'] = action
					self.mProgressInternal['time'] = time
				if external:
					self.mProgressExternal['action'] = action
					self.mProgressExternal['time'] = time

				if action == Playback.ActionPause or action == Playback.ActionFinish: self.mProgressPause = time

				if wait: result = self._progressUpdate(time = time, action = action, duration = duration, current = current, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, internal = internal, external = external, detail = detail, quick = quick)
				else: Pool.thread(target = self._progressUpdate, kwargs = {'time' : time, 'action' : action, 'duration' : duration, 'current' : current, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'metadata' : metadata, 'pack' : pack, 'internal' : internal, 'external' : external, 'detail' : detail, 'quick' : quick}, start = True)
			else:
				self._unlock()
		except:
			result = False
			Logger.error()
			self._unlock()
		return result

	def _progressUpdate(self, action, duration, current, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = True, external = True, detail = False, quick = None, time = None):
		result = False
		try:
			duration, current, percent = self._time(duration = duration, current = current)

			finished = False
			if action == Playback.ActionFinish:
				finished = True
				action = Playback.ActionPause

			serie = Media.isSerie(media)
			seasonStandard = None
			episodeStandard = None
			seasonTrakt = None
			episodeTrakt = None

			if serie: seasonStandard, episodeStandard, seasonTrakt, episodeTrakt = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick)

			if internal:
				result = True
				if time is None: time = Time.timestamp()
				self._add(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard, time = time)
				self._update('''
					UPDATE %s SET
						timeUpdated = ?,
						duration = ?,
						progressAction = ?,
						progressPercent = ?,
						progressDuration = ?
					%s;''' % (Playback.Table, self._query(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard)), [time, duration, action, percent, current])

			if external and self.mSettingsTraktProgress:
				# Some seasons are not on Trakt.
				# Eg: Dragon Ball Super S02+.
				if (not Media.isSeason(media) or not seasonTrakt is None) and (not Media.isEpisode(media) or not episodeTrakt is None):
					result = Trakt.progressUpdate(action = action, finished = finished, progress = percent * 100, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonTrakt, episode = episodeTrakt, reload = False, wait = True)
					if result or result is None: result = True
					elif detail and result is False: result = Playback.ErrorTrakt # Trakt server might be down.

			# There should not be a reason to wait for the reload here?
			# The Trakt progress is already updated. If after playback the menu is loaded again, the progress should be correct, even if the various smart menus have not reloaded yet.
			# NB: Important to use "accelerate" here, which reduces processing and foreground metadata retrievals, only trying to quickly refresh the various menus.
			# This ensures that the device is as idle as possible during binging when starting the playback of the next episode.
			# Otherwise Gaia is laggy during the rating/binge/playback dialog since tons of episode/season/pack metadata is retrieved and packs generated, after a fresh Gaia install.
			# A proper/full refresh is already done earlier in the playback during historyUpdate(), so here we do not need to do it fully again.
			if finished or action == Playback.ActionStop: self.reload(media = media, progress = True, accelerate = True, wait = False)

		except:
			result = False
			Logger.error()
		self._unlock()
		return result

	def progressRemove(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = None, external = None, detail = False, quick = None, wait = False):
		result = False
		try:
			time = Time.timestamp() # Before the lock to get the time of the action, not the time the lock was released.
			self._lock() # This function can be called from player.py concurrently.

			if internal is None: internal = True
			if external is None: external = True

			quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

			if internal or external:
				result = True
				if wait: result = self._progressRemove(time = time, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, internal = internal, external = external, detail = detail, quick = quick)
				else: Pool.thread(target = self._progressRemove, kwargs = {'time' : time, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'metadata' : metadata, 'pack' : pack, 'internal' : internal, 'external' : external, 'detail' : detail, 'quick' : quick}, start = True)
			else:
				self._unlock()
		except:
			result = False
			Logger.error()
			self._unlock()
		return result

	def _progressRemove(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = True, external = True, detail = False, quick = None, time = None):
		result = False
		try:
			serie = Media.isSerie(media)
			seasonStandard = None
			episodeStandard = None
			seasonTrakt = None
			episodeTrakt = None

			if serie: seasonStandard, episodeStandard, seasonTrakt, episodeTrakt = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick)

			if internal:
				result = True
				if time is None: time = Time.timestamp()
				self._update('''
					UPDATE %s SET
						timeUpdated = ?,
						progressAction = NULL,
						progressPercent = NULL,
						progressDuration = NULL
					%s;''' % (Playback.Table, self._query(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard)), [time])

			if external and self.mSettingsTraktProgress:
				# Some seasons are not on Trakt.
				# Eg: Dragon Ball Super S02+.
				if (not Media.isSeason(media) or not seasonTrakt is None) and (not Media.isEpisode(media) or not episodeTrakt is None):
					result = Trakt.progressRemove(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonTrakt, episode = episodeTrakt, reload = False, wait = True)
					if result or result is None: result = True
					elif detail and result is False: result = Playback.ErrorTrakt # Trakt server might be down.

			# There should not be a reason to wait for the reload here?
			# The Trakt progress is already removed. So even after removing the progress from the context menu, the progress should be correctly removed, even if the various smart menus have not reloaded yet.
			self.reload(media = media, progress = True, wait = False)
		except:
			result = False
			Logger.error()
		self._unlock()
		return result

	##############################################################################
	# HISTORY
	##############################################################################

	# NB: detail=True: retrieve all Trakt play times, instead of just the last one. An additional non-cached API call is being made, so use sparingly and not in batch.
	def history(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = None, external = None, detail = False, quick = None, items = False):
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

			quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)
			serie = Media.isSerie(media)
			seasonStandard = None
			episodeStandard = None
			seasonTrakt = None
			episodeTrakt = None

			if serie:
				seasonStandard, episodeStandard, seasonTrakt, episodeTrakt, metadata, pack = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick, detail = True)

				if external and (Media.isSeason(media) or Media.isEpisode(media)) and seasonTrakt is None:
					# If there is a standard season but not Trakt season, it probably means Trakt has a single absolute season and TVDb the further seasons.
					# Still do a lookup for S01 and then the numbers are converted below and "custom" seasons are added to the history.
					# Eg: Dragon Ball Super
					if seasonStandard > 1: seasonTrakt = 1
					else: external = False

			if external and self.mSettingsTraktStatus:
				# Some seasons are not on Trakt.
				# Eg: Dragon Ball Super S02+.
				if (not Media.isSeason(media) or not seasonTrakt is None) and (not Media.isEpisode(media) or not episodeTrakt is None):
					if serie: pack = self.pack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, pack = pack, quick = quick)
					history = Trakt.historyRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonTrakt, episode = episodeTrakt, detail = detail)
					if history:
						# NB: Only do Trakt number conversion if a single show is requested, such as on season and episode menus.
						# If multiple shows are requested, such as when calling this function with "items=True" to return the ENTIRE history, there might be too many shows.
						# If the user has 100s or 1000s of shows in their history, retrieving all of them to eg create the Progress menu, will cause 1000s of pack generations/retrievals.
						# Generating 1000s in one go is simply not feasible. And even if this is done, the Trakt rate limit is eventually hit, causing pack generations to fail.
						# If the entire history is retrieved, return all of them with Trakt numbers. These have to be converted more efficiently later on when only a subset of items are displayed on the Progress menu.
						if serie and self._single(imdb = imdb, tmdb = tmdb, tvdb = trakt, trakt = trakt): history = self.lookupItems(items = history, media = media, season = seasonStandard, episode = episodeStandard, metadata = metadata, pack = pack, quick = quick)

						if items: return history

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
			# Only use the local history if the user has no Trakt account or changed the setting to only use local history.
			#if internal and not history:
			#if internal and (not history and (not self.mSettingsTraktStatus or external is False)):
			if internal and (history is False or external is False or not self.mSettingsTraktStatus):
				seasonLookup = None
				episodeLookup = None
				if serie:
					values = self.lookupNumbers(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard, metadata = metadata, pack = pack, quick = quick)
					seasons = Tools.listUnique([i[0] for i in values if not i[0] is None])
					episodes = Tools.listUnique([i[1] for i in values if not i[1] is None])

					# Make sure season/episode is True (and not None) if we want to retrieve multiple values, such as all episode from a season to determine if the season was fully watched.
					seasonLookup = seasons[0] if len(seasons) == 1 else True if len(seasons) > 1 else None
					episodeLookup = episodes[0] if len(episodes) == 1 else True if len(episodes) > 1 else None

				values = self._retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonLookup, episode = episodeLookup, full = items, attribute = 'history')

				if values:
					if items: return values
					if media == Media.Show or media == Media.Season:
						seasons = {}
						for item in values:
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
										'all' : [],
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
							try: time = max([j['time']['last'] or 0 for j in i['episodes']]) or None
							except: time = None # Sequence/list in max(...) is empty.
							i['count']['total'] = sum([j['count']['total'] for j in i['episodes']])
							i['count']['unique'] = len(i['episodes'])
							i['time']['last'] = time
							i['time']['all'] = [] if time is None else [time]
							i['episodes'] = Tools.listSort(i['episodes'], key = lambda x : (x['season'], x['episode']))

						if media == Media.Show:
							try: time = max([max([j['time']['last'] or 0 for j in i['episodes']]) for i in seasons]) or None
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
						history = values[0]['history']
						if history:
							result['count']['total'] =  len(history)
							result['count']['unique'] = 1
							result['time']['last'] = history[0]
							result['time']['all'] =  history

		except: Logger.error()
		return [] if items else result

	def historyUpdate(self, time = None, duration = None, current = None, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, selection = None, specials = SpecialsNone, force = False, internal = None, external = None, detail = False, quick = None, wait = False):
		result = False
		try:
			if time is None: time = Time.timestamp()
			self._lock()

			if internal is None: internal = True
			if external is None: external = True

			quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)
			id = self._query(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

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
			if internal or external:
				result = True
				if wait: result = self._historyUpdate(time = time, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, selection = selection, specials = specials, force = force, internal = internal, external = external, detail = detail, quick = quick)
				else: Pool.thread(target = self._historyUpdate, kwargs = {'time' : time, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'metadata' : metadata, 'pack' : pack, 'selection' : selection, 'specials' : specials, 'force' : force, 'internal' : internal, 'external' : external, 'detail' : detail, 'quick' : quick}, start = True)
			else:
				self._unlock()
		except:
			result = False
			Logger.error()
			self._unlock()
		return result

	def _historyUpdate(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, selection = None, specials = SpecialsNone, force = False, internal = True, external = True, detail = False, quick = None, time = None):
		result = False
		try:
			if time is None: time = Time.timestamp()
			timeReleased = time is True
			timeCurrent = Time.timestamp()
			timeInteger = Time.integer()

			serie = Media.isSerie(media)
			seasonStandard = None
			episodeStandard = None
			seasonTrakt = None
			episodeTrakt = None

			if serie:
				metadatas = {}
				base = ('_'.join(str(i) for i in [imdb, tmdb, tvdb, trakt])) + '_%d'

				seasonStandard, episodeStandard, seasonTrakt, episodeTrakt, metadata, pack = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick, detail = True)
				pack = self.pack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, pack = pack, quick = quick) # Used repeatedly in the loop below.

			values = self.lookupNumbers(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard, metadata = metadata, pack = pack, quick = quick)

			items = []
			for s, e in values:
				watch = True
				item = {
					'imdb' : imdb,
					'tmdb' : tmdb,
					'tvdb' : tvdb,
					'trakt' : trakt,
				}

				if serie:
					seasonStandard, episodeStandard, seasonTrakt, episodeTrakt, metadata2, pack2 = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e, number = number, metadata = metadata, pack = pack, quick = quick, detail = True)

					item.update({
						'season' : seasonTrakt,
						'episode' : episodeTrakt,
						'seasonStandard' : seasonStandard,
						'episodeStandard' : episodeStandard,
					})

					if not metadata2:
						# Faster metadata retrieval if an entire show/season is marked as watched.
						id = base % seasonStandard
						if not id in metadatas: metadatas[id] = self.metadata(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, number = MetaPack.NumberStandard, pack = False)
						meta = metadatas.get(id)
						if meta:
							for i in meta:
								if i.get('episode') == episodeStandard:
									metadata2 = i
									break
				else:
					metadata2 = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

				timeRelease = self.release(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard, number = MetaPack.NumberStandard, metadata = metadata2)
				if timeReleased:
					time = timeRelease
					if not time: continue

				# Do not mark unreleased episodes.
				# Only do this if an entire show/season is marked, that is if the episode is None.
				if watch and episode is None and Media.isSerie(media):
					if timeRelease and Time.integer(Time.format(timeRelease, format = Time.FormatDate)) > timeInteger: watch = False

				# Do not mark specials as watched if the entire show is marked.
				if watch and season is None and episode is None and (seasonStandard == 0 or episodeStandard == 0):
					if specials == Playback.SpecialsNone:
						watch = False
					elif specials == Playback.SpecialsStory:
						if not (metadata2.get('special') or {}).get('story'): watch = False

				# Episode not part of the remaining episodes to be marked as watched.
				if selection:
					found = False
					for i in selection:
						if i.get('season') == seasonStandard and i.get('episode') == episodeStandard:
							found = True
							break
					if not found: watch = False

				if watch:
					item['time'] = time
					items.append(item)

			if internal:
				result = True
				for item in items:
					s = item.get('seasonStandard')
					e = item.get('episodeStandard')
					time = item['time']

					history = []
					data = self._retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e, single = True, attribute = 'history')
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

						self._add(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e, time = timeCurrent)
						self._update('''
							UPDATE %s SET
								timeUpdated = ?,
								history = ?
							%s;''' % (Playback.Table, self._query(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e)), [timeCurrent, Converter.jsonTo(history)])

			if external and self.mSettingsTraktStatus:
				updates = []

				for item in items:
					s = item.get('season')
					e = item.get('episode')
					if media == Media.Season and s is None: continue
					elif media == Media.Episode and (s is None or e is None): continue
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
					if self.mSettingsTraktPlaysLast: Trakt.historyRemove(selection = None, media = media, items = updates, refresh = False, reload = False, wait = True)

					result = Trakt.historyUpdate(media = media, items = updates, reload = False, wait = True)
					if result or result is None: result = True
					elif detail and result is False: result = Playback.ErrorTrakt # Trakt server might be down.

			# Preload S0 metadata if S01E01 (or the entire S01) was watched.
			# This ensures that if the show Progress menu is opened for the first time AFTER starting a new show, the episode submenu does not need time to load first, because it has to interleave S0 specials.
			if (media == Media.Season and season == 1) or (media == Media.Episode and season == 1 and episode == 1):
				self.preload(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = 0, delay = True, wait = False)

			# There should not be a reason to wait for the reload here?
			# The Trakt history is already updated. So even after watching and item from the context menu or after playback, the watched status should be correct, even if the various smart menus have not reloaded yet.
			self.reload(media = media, history = True, wait = False)

			from lib.modules.video import Trailer
			Trailer().watch(imdb = imdb)
		except:
			result = False
			Logger.error()
		self._unlock()
		return result

	# selection: None = remove all, False = remove oldest, True = remove most recent, Small Integer = remove specific index, Large Integer = remove specific history ID.
	def historyRemove(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, selection = None, force = False, internal = None, external = None, detail = False, quick = None, wait = False):
		result = False
		try:
			time = Time.timestamp()
			self._lock()

			if internal is None: internal = True
			if external is None: external = True

			quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)
			id = self._query(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
			try: del self.mHistoryMarked[id]
			except: pass

			if internal or external:
				result = True
				if wait: result = self._historyRemove(time = time, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, selection = selection, force = force, internal = internal, external = external, detail = detail, quick = quick)
				else: Pool.thread(target = self._historyRemove, kwargs = {'time' : time, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'selection' : selection, 'force' : force, 'internal' : internal, 'external' : external, 'detail' : detail, 'quick' : quick}, start = True)
			else:
				self._unlock()
		except:
			result = False
			Logger.error()
			self._unlock()
		return result

	def _historyRemove(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, selection = None, force = False, internal = True, external = True, detail = False, quick = None, time = None):
		result = False
		try:
			if time is None: time = Time.timestamp()

			serie = Media.isSerie(media)
			seasonStandard = None
			episodeStandard = None
			seasonTrakt = None
			episodeTrakt = None

			if serie:
				seasonStandard, episodeStandard, seasonTrakt, episodeTrakt, metadata, pack = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick, detail = True)
				pack = self.pack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, pack = pack, quick = quick) # Used repeatedly in the loop below.

			values = self.lookupNumbers(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard, metadata = metadata, pack = pack, quick = quick)

			items = []
			times = []
			for s, e in values:
				item = {
					'imdb' : imdb,
					'tmdb' : tmdb,
					'tvdb' : tvdb,
					'trakt' : trakt,
				}
				if serie:
					seasonStandard, episodeStandard, seasonTrakt, episodeTrakt, metadata2, pack2 = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e, number = number, metadata = metadata, pack = pack, quick = quick, detail = True)
					item.update({
						'season' : seasonTrakt,
						'episode' : episodeTrakt,
						'seasonStandard' : seasonStandard,
						'episodeStandard' : episodeStandard,
					})
				items.append(item)

			if internal:
				result = True
				for item in items:
					s = item.get('seasonStandard')
					e = item.get('episodeStandard')

					data = self._retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e, single = True, attribute = 'history')
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
							%s;''' % (Playback.Table, self._query(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = s, episode = e)), [time, Converter.jsonTo(times if times else None)])

			if external and self.mSettingsTraktStatus:
				updates = []

				for item in items:
					s = item.get('season')
					e = item.get('episode')
					if media == Media.Season and s is None: continue
					elif media == Media.Episode and (s is None or e is None): continue
					updates.append(item)

				if updates:
					result = Trakt.historyRemove(selection = selection, media = media, items = updates, reload = False, wait = True)
					if result or result is None: result = True
					elif detail and result is False: result = Playback.ErrorTrakt # Trakt server might be down.

			# There should not be a reason to wait for the reload here?
			# The Trakt history is already updated. So even after unwatching and item from the context menu , the watched status should be correct, even if the various smart menus have not reloaded yet.
			self.reload(media = media, history = True, wait = False)

			if not times or selection is None:
				from lib.modules.video import Trailer
				Trailer().unwatch(imdb = imdb)
		except:
			result = False
			Logger.error()
		self._unlock()
		return result

	# Last watched episode for binge watching from the context menu.
	def historyLast(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = None, external = None, quick = None):
		quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)
		season, episode, metadata, pack = self.lookupStandard(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick, detail = True)
		history = self.history(media = Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, metadata = metadata, pack = pack, internal = internal, external = external, quick = quick)
		return self._historyLast(history = history, season = season, episode = episode)

	def _historyLast(self, history, season = None, episode = None, specials = True):
		if history and 'seasons' in history:
			result = {'season' : -1, 'episode' : -1, 'time' : 0}
			for i in history['seasons']:
				if specials or not i['season'] == 0:
					if season is None or i['season'] == season:
						if 'episodes' in i:
							for j in i['episodes']:
								if episode is None or j['episode'] >= episode:
									# Either pick the latest time, or if the time is the same, then pick the highest episode number.
									if (j['time']['last'] > result['time']) or (j['time']['last'] == result['time'] and (j['season'] > result['season'] or (j['season'] == result['season'] and j['episode'] > result['episode']))):
										result = {'season' : j['season'], 'episode' : j['episode'], 'time' : j['time']['last'], 'count' : j['count']['total']}
			return result if (result and result['time']) else None
		return None

	def _historyRecent(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, internal = None, external = None, quick = None):
		history = self.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, internal = internal, external = external, quick = quick)
		last = None
		if history and history['count']['total'] and history['time']['last']:
			current = Time.timestamp()
			last = history['time']['last']
			if (current - last) < self.mSettingsHistoryCountRewatch: return True, last
		return False, last

	##############################################################################
	# RATING
	##############################################################################

	def rating(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, full = False, internal = None, external = None, quick = None):
		rating = None
		try:
			if external is None: external = True
			if internal is None: internal = True

			quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)
			serie = Media.isSerie(media)
			seasonStandard = None
			episodeStandard = None
			seasonTrakt = None
			episodeTrakt = None

			if serie: seasonStandard, episodeStandard, seasonTrakt, episodeTrakt = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick)

			if external and self.mSettingsTraktRating:
				# Some seasons are not on Trakt.
				# Eg: Dragon Ball Super S02+.
				if (not Media.isSeason(media) or not seasonTrakt is None) and (not Media.isEpisode(media) or not episodeTrakt is None):
					rating = Trakt.ratingRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonTrakt, episode = episodeTrakt, attribute = None if full else 'rating')

			if internal and rating is None:
				data = self._retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard, single = True, attribute = 'rating')
				if data:
					data = data['rating']
					if data:
						rating = data[0]
						if not full: rating = rating['rating']
		except: Logger.error()
		return rating

	def ratingUpdate(self, rating, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = None, external = None, detail = False, quick = None, wait = False):
		result = False
		try:
			time = Time.timestamp() # Before the lock to get the time of the action, not the time the lock was released.
			self._lock() # This function can be called from player.py concurrently.

			if internal is None: internal = True
			if external is None: external = True

			quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

			if internal or external:
				result = True
				if wait: result = self._ratingUpdate(time = time, rating = rating, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, internal = internal, external = external, detail = detail, quick = quick)
				else: Pool.thread(target = self._ratingUpdate, kwargs = {'time' : time, 'rating' : rating, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'metadata' : metadata, 'pack' : pack, 'internal' : internal, 'external' : external, 'detail' : detail, 'quick' : quick}, start = True)
			else:
				self._unlock()
		except:
			result = False
			Logger.error()
			self._unlock()
		return result

	def _ratingUpdate(self, rating, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = True, external = True, detail = False, quick = None, time = None):
		result = False
		try:
			if time is None: time = Time.timestamp()

			serie = Media.isSerie(media)
			seasonStandard = None
			episodeStandard = None
			seasonTrakt = None
			episodeTrakt = None

			if serie: seasonStandard, episodeStandard, seasonTrakt, episodeTrakt = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick)

			if internal:
				result = True
				ratings = None
				data = self._retrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard, single = True, attribute = 'rating')
				if data: ratings = data['rating']
				if ratings and ratings[0] and ratings[0].get('rating') == rating: result = None # Already rated with unchaged rating.
				if not ratings: ratings = []
				ratings.insert(0, {'time' : time, 'rating' : rating})

				self._add(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard, time = time)
				self._update('''
					UPDATE %s SET
						timeUpdated = ?,
						rating = ?
					%s;''' % (Playback.Table, self._query(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard)), [time, Converter.jsonTo(ratings)])

			if external and self.mSettingsTraktRating:
				# Some seasons are not on Trakt.
				# Eg: Dragon Ball Super S02+.
				if (not Media.isSeason(media) or not seasonTrakt is None) and (not Media.isEpisode(media) or not episodeTrakt is None):
					result = Trakt.ratingUpdate(rating = rating, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonTrakt, episode = episodeTrakt, time = time, wait = True)
					if Tools.isInteger(result): result = None # Already rated with unchaged rating.
					elif result or result is None: result = True
					elif detail and result is False: result = Playback.ErrorTrakt # Trakt server might be down.

		except:
			result = False
			Logger.error()
		self._unlock()
		return result

	def ratingRemove(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = None, external = None, detail = False, quick = None, wait = False):
		result = False
		try:
			time = Time.timestamp() # Before the lock to get the time of the action, not the time the lock was released.
			self._lock() # This function can be called from player.py concurrently.

			if internal is None: internal = True
			if external is None: external = True

			quick = self._quick(quick = quick, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

			if internal or external:
				result = True
				if wait: result = self._ratingRemove(time = time, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, internal = internal, external = external, detail = detail, quick = quick)
				else: Pool.thread(target = self._ratingRemove, kwargs = {'time' : time, 'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'number' : number, 'metadata' : metadata, 'pack' : pack, 'internal' : internal, 'external' : external, 'detail' : detail, 'quick' : quick}, start = True)
			else:
				self._unlock()
		except:
			result = False
			Logger.error()
			self._unlock()
		return result

	def _ratingRemove(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = True, external = True, detail = False, quick = None, time = None):
		result = True
		try:
			serie = Media.isSerie(media)
			seasonStandard = None
			episodeStandard = None
			seasonTrakt = None
			episodeTrakt = None

			if serie: seasonStandard, episodeStandard, seasonTrakt, episodeTrakt = self.lookupCombined(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, quick = quick)

			if internal:
				if time is None: time = Time.timestamp()
				self._update('''
					UPDATE %s SET
						timeUpdated = ?,
						rating = NULL
					%s;''' % (Playback.Table, self._query(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonStandard, episode = episodeStandard)), [time])

			if external and self.mSettingsTraktRating:
				# Some seasons are not on Trakt.
				# Eg: Dragon Ball Super S02+.
				if (not Media.isSeason(media) or not seasonTrakt is None) and (not Media.isEpisode(media) or not episodeTrakt is None):
					result = Trakt.ratingRemove(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonTrakt, episode = episodeTrakt, wait = True)
					if result or result is None: result = True
					elif detail and result is False: result = Playback.ErrorTrakt # Trakt server might be down.
		except:
			result = False
			Logger.error()
		self._unlock()
		return result

	def _ratingRerate(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, metadata = None, pack = None, internal = True, external = True, quick = None, force = False):
		try:
			if force: return True

			allow = False
			current = self.rating(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, metadata = metadata, pack = pack, internal = internal, external = external, quick = quick, full = True)

			if media == Media.Show: rerate = self.mSettingsRatingRerateShow
			elif media == Media.Season: rerate = self.mSettingsRatingRerateSeason
			elif media == Media.Episode: rerate = self.mSettingsRatingRerateEpisode
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

	##############################################################################
	# ITEMS
	##############################################################################

	# Returns a list of historically played items and/or items with scrobble progress.
	# Include both history and progress items, instead of only history items, so that:
	#	Movies without a full play, but with partial progress, are added to the progress menu.
	#	Shows with no episode plays (S01E01 does no have a full play yet), but the first episode has partial progress, are added to the progress menu.
	#	Plus Trakt only stores scrobble progress for 6 months. Hence we can use the local progress items to list movies that the user started to play a year ago, but never finished.
	def items(self, media = None, history = True, progress = True, rating = False, specials = True, internal = None, external = None):
		try:
			# NB: Trakt only stores playback progress for 6 months.
			#	https://trakt.docs.apiary.io/#reference/sync/playback
			# Retrieve the history, instead of progress, for older and fully watched items.

			from lib.meta.tools import MetaTools
			tools = MetaTools.instance()

			mediaFilm = Media.isFilm(media)
			mediaSerie = Media.isSerie(media)

			if internal is None: internal = True
			if external is None: external = True

			#############################
			# PROGRESS
			#############################

			progressExternal = []
			progressInternal = []
			if progress:
				if external:
					items = self.progress(media = media, internal = False, external = True, items = True)
					if items: progressExternal = self._items(media = media, items = items, external = True)
				if internal:
					items = self.progress(media = media, internal = True, external = False, items = True)
					if items: progressInternal = self._items(media = media, items = items, external = False)

			progressItems = progressExternal + progressInternal
			progressItems = tools.filterDuplicate(items = progressItems)

			#############################
			# HISTORY
			#############################

			historyExternal = []
			historyInternal = []
			if history:
				if external:
					items = self.history(media = media, internal = False, external = True, items = True)
					if items: historyExternal = self._items(media = media, items = items, external = True)
				if internal:
					items = self.history(media = media, internal = True, external = False, items = True)
					if items: historyInternal = self._items(media = media, items = items, external = False)

			historyItems = historyExternal + historyInternal
			if mediaSerie:
				items = []
				lookup = {
					'trakt' : {},
					'imdb' : {},
					'tmdb' : {},
					'tvdb' : {},
				}
				for item in historyItems:
					seasonCurrent = item['season']
					episodeCurrent = item['episode']

					if not specials and (seasonCurrent == 0 or episodeCurrent == 0): continue

					other = None
					for i in lookup.keys():
						id = item.get(i)
						if id:
							other = lookup[i].get(id)
							if other: break

					if other:
						playbackCurrent = item['playback']
						timeCurrent = playbackCurrent['time']['update']
						countCurrent = playbackCurrent['count']
						externalCurrent  = playbackCurrent['source']['external']
						specialCurrent = seasonCurrent == 0 or episodeCurrent == 0

						playbackOther = other['playback']
						timeOther = playbackOther['time']['update']
						countOther = playbackOther['count']
						externalOther = playbackOther['source']['external']
						seasonOther = other['season']
						episodeOther = other['episode']

						replace = False

						if not specialCurrent: # Do not replace a normal episode with a special episode. Only the other way around is allowed.

							# Replace specials with normal episodes. In case the user watched a special, we do not want to list the specials season in the Progress menu.
							if seasonOther == 0 or episodeOther == 0: replace = True

							# Items coming from the internal database have a timestamp for ['time']['watched'] even if the item was not fully watched, but just started the playback progress.
							# Only replace a higher-numbered episode with a lower-numbered episode if it has a higher play count, even if its watched time is earlier.
							elif not externalOther or ((countCurrent or 0) > (countOther or 0)):

								# Replace if the watched time is later.
								if timeCurrent > timeOther: replace = True

								# Replace if the watched time is the same, but the season/episode number is greater.
								elif (timeCurrent == timeOther and (seasonCurrent > seasonOther or (seasonCurrent == seasonOther and episodeCurrent > episodeOther))): replace = True

						if replace: Tools.update(other, item, none = False)
					else:
						items.append(item)
						for i in lookup.keys():
							id = item.get(i)
							if id: lookup[i][id] = item
				historyItems = items

			historyItems = tools.filterDuplicate(items = historyItems)

			#############################
			# COMBINATION
			#############################

			def _maximum(value1, value2):
				if value1 and value2: return max(value1, value2)
				elif value1 is None: return value2
				elif value2 is None: return value1

			def _update(item1, item2):
				if Tools.isDictionary(item1):
					if item1 and item2:
						for i in item1.keys():
							value1 = item1[i]
							value2 = item2[i]
							if Tools.isDictionary(value1): _update(value1, value2)
							else: item1[i] = _maximum(value1, value2)

			items = historyItems + progressItems # Prefer history over progress items. If order is ever changed, make sure the progress update below still works.
			items = tools.filterDuplicate(items = items)

			# The same item can be in history and progress. Eg: watched item being rewatched.
			# One of the "playback" dicts has the count, the other the progress.
			# A duplicate progress item will be filtered out above if there is a history item.
			# Update the history item with the progress of the progress item.
			helper = {}
			for item in items:
				# This might not always be accurate, since one item can be from Trakt and one local, and their episode numbering might be different (Trakt vs Standard numbers).
				# Trakt numbers are not converted here, since it is too expensive.
				found = tools.filterContains(items = progressItems, item = item, helper = helper, number = True, result = True)
				if found:
					playback1 = item['playback']
					playback2 = found['playback']

					playback1['count'] = _maximum(playback1['count'], playback2['count'])
					playback1['progress'] = _maximum(playback1['progress'], playback2['progress'])
					_update(playback1['time'], playback2['time'])

					# Aggregate changed values to the outer structure.
					item['playcount'] = playback1['count']
					item['progress'] = playback1['progress']
					item['time'][MetaTools.TimeWatched] = playback1['time']['history']
					item['time'][MetaTools.TimePaused] = playback1['time']['progress']
					item['time'][MetaTools.TimeUpdated] = playback1['time']['update']

			items = Tools.listSort(items, key = lambda x : x['playback']['time']['update'] or 0, reverse = True)

			#############################
			# RATING
			#############################

			# Can take 50-100 ms for smaller histories.
			# Could potentially be made faster by retrieving all ratings at once, similar to history/progress above.
			if (rating or rating is None) and items:
				if rating is None and mediaSerie: mediad = Media.Show
				elif Tools.isString(rating): mediad = rating
				elif mediaSerie: mediad = Media.Episode
				else: mediad = media
				for item in items:
					if Media.isEpisode(mediad): rated = self.rating(media = mediad, imdb = item.get('imdb'), tmdb = item.get('tmdb'), tvdb = item.get('tvdb'), trakt = item.get('trakt'), season = item.get('season'), episode = item.get('episode'), internal = internal, external = external, full = True, quick = True)
					else: rated = self.rating(media = mediad, imdb = item.get('imdb'), tmdb = item.get('tmdb'), tvdb = item.get('tvdb'), trakt = item.get('trakt'), internal = internal, external = external, full = True, quick = True)
					if rated:
						ratedValue = rated.get('rating')
						if not ratedValue is None:
							item['userrating'] = ratedValue
							item['playback']['rating'] = ratedValue

							# Do not adjust the playback dict "update" time, since we want to stick to history/progress time for sorting.
							ratedTime = rated.get('time')
							item['playback']['time']['rating'] = ratedTime
							if not ratedTime is None: item['time'][MetaTools.TimeRated] = ratedTime

			return items
		except: Logger.error()
		return None

	def _items(self, media, items, external = False):
		from lib.meta.tools import MetaTools

		mediaFilm = Media.isFilm(media)
		mediaSerie = Media.isSerie(media)

		# Calculate the total/unique number of episodes watched.
		# In case this data is not available from Trakt.
		counters = None
		if not external and mediaSerie:
			counters = {'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}}
			for item in items:
				history = item.get('history')
				if history:
					count = len(history)
					ids = item['id']
					season = item['number']['season']
					episode = item['number']['episode']
					for i in counters.keys():
						id = ids.get(i)
						if id:
							temp = counters[i]

							if not id in temp: temp[id] = {}
							temp = temp[id]

							if not season in temp: temp[season] = {}
							temp = temp[season]

							if not episode in temp: temp[episode] = 0
							temp[episode] += count

			for i in counters.values():
				for id, x in i.items():
					total = 0
					unique = 0
					mainTotal = 0
					mainUnique = 0
					for season, y in x.items():
						for episode, z in y.items():
							if z > 0:
								total += z
								unique += 1
								if season > 0:
									mainTotal += z
									mainUnique += 1
					i[id] = {
						'total' : total,
						'unique' : unique,
						'main' : {
							'total' : mainTotal,
							'unique' : mainUnique,
						},
					}

		result = []
		for item in items:
			try:
				id = None
				number = None
				progress = None
				counts = None
				count = None
				timeUpdated = None
				timeHistory = None
				timeProgress = None

				if 'history' in item: # Internal (Local)
					id = item['id']
					if mediaSerie: number = item['number']
					progress = item['progress']['percent']
					if not progress is None: timeProgress = item['time']['updated'] # Do not add the time if the progress was cleared.
					try: timeHistory = max(item['history'])
					except: timeHistory = item['time']['finished']
					try: count = len(item['history']) or None
					except: pass

					# Some items only have a rating and not progress or history.
					# Shows/Seasons will always only have a rating.
					# Filter these out.
					if item['progress']['percent'] is None and not item['history']: continue
					elif mediaFilm and not item['number']['season'] is None and not item['number']['season'] == '': continue
					elif mediaSerie and(item['number']['season'] is None or item['number']['season'] == ''): continue

					# Copy over counter summaries for the entire show.
					if counters and id:
						for k, v in id.items():
							if v:
								try:
									counts = counters[k][v]
									break
								except: pass

				else: # External (Trakt)
					if 'movie' in item: id = item['movie']['ids']
					elif 'show' in item: id = item['show']['ids']
					elif 'id' in item: id = item['id']

					if 'progress' in item:
						progress = item['progress']
						timeProgress = item.get('time')
					if 'count' in item:
						counts = item['count']
						if 'main' in item['count'] and 'unique' in item['count']['main']: count = item['count']['main']['unique']
						elif 'unique' in item['count']: count = item['count']['unique']
						if 'time' in item and item['time'] and 'last' in item['time']: timeHistory = item['time']['last']

					if 'seasons' in item:
						# If the last item watched was a special, first see if there is no other S01+ episode available.
						last = self._historyLast(history = item, specials = False)
						if not last: last = self._historyLast(history = item, specials = True)
						if last:
							number = {'season' : last.get('season'), 'episode' : last.get('episode')}
							timeHistory = last.get('time')
							count = last.get('count')
					elif 'episode' in item:
						number = {'season' : item['episode']['season'] if 'season' in item['episode'] else None, 'episode' : item['episode']['number'] if 'number' in item['episode'] else None}

				if id:
					id = {k : (str(v) if v else None) for k, v in id.items()}

					if not progress is None: progress = Math.round(progress, places = 6)
					timeUpdated = max(timeHistory, timeProgress) if (timeHistory and timeProgress) else (timeHistory or timeProgress)

					item = {
						'media' : Media.Episode if mediaSerie else media,
						'id' : id,
					}
					if number: item.update(number)

					# Add as common Kodi attributes, for preliminary filtering and sorting.
					time = {}
					if timeHistory: time[MetaTools.TimeWatched] = timeHistory
					if timeProgress: time[MetaTools.TimePaused] = timeProgress
					if timeUpdated: time[MetaTools.TimeUpdated] = timeUpdated
					item.update(id)
					item.update({
						'playcount' : count,
						'progress' : progress,
						'userrating' : None,
						'time' : time,
					})

					# Add detailed playback data.
					item['playback'] = {
						'source' : {
							'external' : external,
							'internal' : not external,
						},
						'time' : {
							'update' : timeUpdated,
							'history' : timeHistory,
							'progress' : timeProgress,
							'rating' : None,
						},
						'count' : count,
						'progress' : progress,
						'rating' : None,
					}
					if mediaSerie: item['playback']['counts'] = counts

					result.append(item)
			except: Logger.error()
		return result

	##############################################################################
	# CLEAN
	##############################################################################

	def _clean(self, time, commit = True, compact = True):
		if time: return self._delete(query = 'DELETE FROM `%s` WHERE timeUpdated <= ?;' % Playback.Table, parameters = [time], commit = commit, compact = compact)
		return False

	def _cleanTime(self, count):
		if count:
			times = self._selectValues(query = 'SELECT timeUpdated FROM `%s` ORDER BY timeUpdated ASC LIMIT ?;' % Playback.Table, parameters = [count])
			if times: return Tools.listSort(times)[:count][-1]
		return None
