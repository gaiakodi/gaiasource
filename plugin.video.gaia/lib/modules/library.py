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

# https://kodi.wiki/view/Naming_video_files/TV_shows

import re

from lib.modules.tools import System, Tools, Media, Settings, File, Converter, Time, Regex, Logger
from lib.modules.interface import Translation, Dialog, Loader
from lib.modules.database import Database
from lib.modules.network import Networker
from lib.modules.concurrency import Pool, Lock, Semaphore

class Library(object):

	DatabaseName = 'library'

	InfoMovie = 'movie'
	InfoShow = 'tv'

	LinkTvdb = 'https://thetvdb.com/dereferrer/series/%s' # Or: https://thetvdb.com/?tab=series&id=%s
	LinkTmdb = 'https://themoviedb.org/%s/%s'
	LinkImdb = 'https://imdb.com/title/%s/'

	ExtensionStrm = '.strm'
	ExtensionMeta = '.meta'

	DurationUpdate = 60000
	DurationNoUpdate = 4000
	DurationMonitor = 7200 # 2 hours. Number of seconds between library updates by the service.

	##############################################################################
	# CONSTRUCTORS
	##############################################################################

	def __init__(self, media = Media.Unknown):
		self.mMedia = media
		self.mMediaFilm = Media.isFilm(self.mMedia)
		self.mMediaSerie = Media.isSerie(self.mMedia)
		self.mInfo = Library.InfoShow if self.mMediaSerie else Library.InfoMovie

		self.mDuplicates = Settings.getBoolean('library.general.duplicates')
		self.mPrecheck = Settings.getBoolean('library.general.precheck')
		self.mUnaired = Settings.getBoolean('library.general.unaired')
		self.mUpdate = Settings.getBoolean('library.update.automatic')

		self.mDuration = Library.DurationUpdate if self.mUpdate else Library.DurationNoUpdate
		self.mLocation = self._location(media = self.mMedia)
		self.mDialog = False

	##############################################################################
	# INTERNAL
	##############################################################################

	def _parameterize(self, data):
		data = {k : v for k, v in data.items() if not v is None}
		if not self.mMedia is None: data['media'] = self.mMedia
		data = System.originSet(origin = System.OriginLibrary, parameters = data)
		return data

	@classmethod
	def _location(self, media = None, make = True):
		if media is None: return None

		path = None
		if Settings.getInteger('library.location.selection') == 0:
			if media == Media.Movie: label = 32001
			elif media == Media.Show or media == Media.Season or media == Media.Episode: label = 32002
			path = File.joinPath(Settings.path('library.location.combined'), Translation.string(label))
		else:
			if media == Media.Season or media == Media.Episode: media = Media.Show
			path = Settings.path('library.location.%s' % media)
		path = path.strip()
		if not path.endswith('\\') and not path.endswith('/'): path += '/'
		if make: File.makeDirectory(path)
		return path

	@classmethod
	def _createDirectory(self, path):
		try:
			if path.startswith('ftp://') or path.startswith('ftps://'):
				from ftplib import FTP
				arguments = re.compile(r'ftp://(.+?):(.+?)@(.+?):?(\d+)?/(.+/?)').findall(path)
				ftp = FTP(arguments[0][2], arguments[0][0], arguments[0][1])
				try: ftp.cwd(arguments[0][4])
				except: ftp.mkd(arguments[0][4])
				ftp.quit()
			else:
				path = File.legalPath(path)
				if not File.existsDirectory(path):
					return File.makeDirectory(path)
			return True
		except:
			Logger.error()
			return False

	@classmethod
	def _readFile(self, path):
		try:
			path = File.legalPath(path)
			return File.readNow(path)
		except:
			return None

	@classmethod
	def _writeFile(self, path, content):
		try:
			if Tools.isArray(content): content = '\n'.join(content)
			if not content: content = ''
			path = File.legalPath(path)
			return File.writeNow(path, content)
		except:
			return False

	def _infoLink(self, ids):
		# It is possible to add multiple links to the file for the various info scrapers.
		# Plus TVDb scraper is not installed by default in Kodi anymore, so many users will probably use the TMDb scraper for shows.
		# Place TMDb BEFORE TVDb, even for shows.
		# Otherwise TMDb scraper adds the correct show, plus another random show. Not sure why, but maybe there is a bug in TMDb that extracts the ID from the TVDb URL?
		# This is not a problem if the TVDb scraper is selected. It can handle the TMDb URL appearing first.
		links = [self._infoLinkImdb, self._infoLinkTmdb, self._infoLinkTvdb]

		result = []
		for link in links:
			link = link(ids = ids)
			if link: result.append(link)
		return result or None

	def _infoLinkImdb(self, ids):
		imdb = ids.get('imdb')
		if imdb: return Library.LinkImdb % str(imdb)
		else: return None

	def _infoLinkTmdb(self, ids):
		tmdb = ids.get('tmdb')
		if tmdb: return Library.LinkTmdb % (self.mInfo, str(tmdb))
		else: return None

	def _infoLinkTvdb(self, ids):
		tvdb = ids.get('tvdb')
		if tvdb: return Library.LinkTvdb % str(tvdb)
		else: return None

	@classmethod
	def _checkSources(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, tvshowtitle = None, title = None, year = None, premiered = None, metadata = None):
		try:
			from lib.modules.core import Core
			streams = Core().scrape(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, tvshowtitle = tvshowtitle, title = title, year = year, premiered = premiered, metadata = metadata)
			return streams and len(streams) > 1
		except:
			Logger.error()
			return False

	@classmethod
	def _legalPath(self, path):
		try:
			path = path.strip()
			path = re.sub(r'(?!%s)[^\w\-_\.]', '.', path)
			path = re.sub(r'\.+', '.', path)
			path = re.sub(re.compile(r'(CON|PRN|AUX|NUL|COM\d|LPT\d)\.', re.I), '\\1_', path)
			path = path.strip('.')
		except:
			pass
		return path

	@classmethod
	def _path(self, path, title, year = None, season = None):
		parts = self._pathParts(title = title, year = year, season = season)
		for part in parts: path = File.joinPath(path, part)
		return path

	@classmethod
	def _pathParts(self, title, year = None, season = None):
		parts = []
		part = re.sub(r'[^\w\-_\. ]', '_', title)
		part = '%s (%s)' % (part, str(year)) if year else part
		parts.append(part)
		if not season is None:
			if season == 0: parts.append(Translation.string(35637))
			else: parts.append(Translation.string(32055) + ' ' + str(season))
		return parts

	@classmethod
	def _ready(self):
		return not System.visible('Window.IsVisible(infodialog)') and not System.visible('Player.HasVideo')

	@classmethod
	def _libraryBusy(self):
		return System.visible('Library.IsScanningVideo')

	def _libraryUpdate(self, all = False):
		self._libraryRefresh(paths = None if all else [self._location(media = self.mMedia)])

	@classmethod
	def _libraryRefresh(self, paths = None):
		# Check if the path was added to the Kodi sources.
		# If not, inform the user to manually add the path.
		contains = False
		try:
			if paths is None:
				paths = []
				paths.append(self._location(media = Media.Movie))
				paths.append(self._location(media = Media.Show))
			paths.extend([File.translate(i) for i in paths])
			paths = [i.rstrip('/').rstrip('\\') for i in paths]
			result = System.executeJson(method = 'Files.GetSources', parameters = {'media' : 'video'})
			result = result['result']['sources']
			for i in result:
				if i['file'].rstrip('/').rstrip('\\') in paths:
					contains = True
					break
		except: Logger.error()
		if not contains: Dialog.confirm(title = 35170, message = 33942)

		# Updating specific paths creates problems, since the user might have a special:// path in Gaia settings and a C:/ path in the Kodi library.
		# Kodi does not see these two paths as the same, and will therefore not update the library.
		# Scan the entire library instead.
		#System.execute('UpdateLibrary(video,%s)' % self.mLocation)
		System.execute('UpdateLibrary(video)')

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def enabled(self):
		return Settings.getBoolean('library.general.enabled')

	@classmethod
	def settings(self):
		Settings.launch(Settings.CategoryLibrary)

	def local(self):
		type = 'tvshows' if self.mMediaSerie else 'movies'
		System.execute('ActivateWindow(10025,library://video/%s/,return)' % type)

	def location(self):
		return self.mLocation

	def notificationLocation(self):
		Dialog.confirm(title = 35170, message = Translation.string(33068) % self.mMedia)

	##############################################################################
	# MOVIES
	##############################################################################

	def _movieAddSingle(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, metadata = None, multiple = False, link = None):
		count = 0
		locationKodi = self.mLocation
		locationResolved = File.translate(locationKodi)

		if self._ready() and not multiple:
			Dialog.notification(title = 33244, message = 35177, icon = Dialog.IconInformation, time = self.mDuration)
			self.mDialog = True

		library = []
		try:
			if self.mDuplicates:
				id = [i for i in [imdb, tmdb] if i]
				library = System.executeJson(method = 'VideoLibrary.GetMovies', parameters = {'filter' : {'or' : [{'field' : 'year', 'operator' : 'is', 'value' : str(year)}, {'field' : 'year', 'operator' : 'is', 'value' : str(int(year) + 1)}, {'field' : 'year', 'operator' : 'is', 'value' : str(int(year) - 1)}]}, 'properties'  : ['imdbnumber', 'originaltitle', 'year', 'file']})
				library = library['result']['movies']
				library = [i for i in library if ((i['file'].startswith(locationKodi) or i['file'].startswith(locationResolved)) and (i['file'].endswith(Library.ExtensionStrm) or i['file'].endswith(Library.ExtensionMeta))) and (str(i['imdbnumber']) in id or (i['originaltitle'] == title and str(i['year']) == str(year)))]
		except: Logger.error()

		if len(library) == 0:
			if not self.mPrecheck or self._checkSources(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, metadata = metadata):
				self._movieFiles(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, metadata = metadata, link = link)
				count += 1
		else:
			count = -1

		return count

	def _movieAddMultiple(self, link):

		Loader.hide()
		count = -1

		if Dialog.option(title = 33244, message = 35179):
			count = 0
			if self._ready():
				Dialog.notification(title = 33244, message = 35177, icon = Dialog.IconInformation, time = self.mDuration)
				self.mDialog = True

			from lib.meta.menu import MetaMenu
			items = MetaMenu.instance(media = self.mMedia).content(command = link)
			items = items.get('items') if items else None
			if items:
				for i in items:
					try:
						if System.aborted(): return System.exit()
						value = self._movieAddSingle(imdb = i.get('imdb'), tmdb = i.get('tmdb'), tvdb = i.get('tvdb'), trakt = i.get('trakt'), title = i.get('title'), year = i.get('year'), metadata = i, multiple = True)
						if value > 0: count += value
					except: Logger.error()

		return count

	def _movieResolve(self, title, year):
		try:
			name = re.sub(r'\s\s+', ' ', re.sub(r'([^\s\w]|_)+', ' ', title))
			nameLegal = self._legalPath('%s (%s) %s' % (name, year, System.name())) + Library.ExtensionMeta
			path = File.joinPath(self._path(self.mLocation, name, year), nameLegal)
			if not File.exists(path): # To accomodate the old file name format that did not contain the year and Gaia.
				nameLegal = self._legalPath(name) + '.' + System.name().lower()
				path = File.joinPath(self._path(self.mLocation, name, year), nameLegal)
			return self._readFile(path)
		except: return None

	def _movieFiles(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, metadata = None, link = None):
		try:
			name = re.sub(r'\s\s+', ' ', re.sub(r'([^\s\w]|_)+', ' ', title))
			nameLegal = self._legalPath('%s (%s) %s' % (name, year, System.name()))
			generic = link is None
			data = None

			if generic:
				# Do not save the metadata to file. The link becomes too long and Kodi cuts it off.
				#link = '%s?action=scrape&title=%s&year=%s&imdb=%s&tmdb=%s&metadata=%s' % (System.arguments(0), Converter.quoteTo(title), year, imdb, tmdb, metadata)
				link = System.command(action = 'scrape', parameters = self._parameterize({'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year}), optimize = False, origin = False)
			else:
				data = link
				link = System.command(action = 'libraryResolve', parameters = self._parameterize({'title' : title, 'year' : year}), optimize = False, origin = False)

			path = self._path(self.mLocation, name, year)
			self._createDirectory(path)

			pathSrtm = File.joinPath(path, nameLegal + Library.ExtensionStrm)
			self._writeFile(pathSrtm, link)

			pathNfo = File.joinPath(path, 'movie.nfo')
			self._writeFile(pathNfo, self._infoLink({'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}))

			if not generic:
				pathGaia = File.joinPath(path, nameLegal + Library.ExtensionMeta)
				self._writeFile(pathGaia, data)
		except:
			Logger.error()

	##############################################################################
	# SHOW
	##############################################################################

	def _televisionAddSingle(self, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, title = None, year = None, metadata = None, multiple = False, link = None):
		count = 0
		locationKodi = self.mLocation
		locationResolved = File.translate(locationKodi)

		if self._ready() and not multiple:
			Dialog.notification(title = 33244, message = 35177, icon = Dialog.IconInformation, time = self.mDuration)
			self.mDialog = True

		if metadata and 'tvdb' in metadata and 'season' in metadata and 'episode' in metadata:
			items = [metadata]
		else:
			from lib.meta.manager import MetaManager
			items = MetaManager.instance().metadataEpisode(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode)
			if items: items = [items]

		try:
			if self.mDuplicates and items:
				id = [i for i in [items[0].get('imdb'), items[0].get('tvdb')] if i]

				library = System.executeJson(method = 'VideoLibrary.GetTVShows', parameters = {'properties' : ['imdbnumber', 'title', 'year']})
				library = library['result']['tvshows']
				library = [i['title'] for i in library if str(i['imdbnumber']) in id or (i['title'] == items[0].get('tvshowtitle') and str(i['year']) == str(items[0].get('tvshowyear') or items[0].get('year')))]

				if library:
					library = library[0]
					library = System.executeJson(method = 'VideoLibrary.GetEpisodes', parameters = {'filter' : {'and' : [{'field' : 'tvshow', 'operator' : 'is', 'value' : library}]}, 'properties' : ['season', 'episode', 'file']})
					library = library['result']['episodes']
					library = [i for i in library if (i['file'].startswith(locationKodi) or i['file'].startswith(locationResolved)) and (i['file'].endswith(Library.ExtensionStrm) or i['file'].endswith(Library.ExtensionMeta))]
					library = ['S%02dE%02d' % (int(i['season']), int(i['episode'])) for i in library]

					items = [i for i in items if not 'S%02dE%02d' % (int(i.get('season')), int(i.get('episode'))) in library]
		except: Logger.error()

		today = Time.integer(Time.past(hours = 6, format = Time.FormatDate))

		if not items:
			count = -1
		else:
			for i in items:
				try:
					if System.aborted(): return System.exit()

					if self.mPrecheck:
						if i.get('episode') == 1:
							self.mBlock = True
							streams = self._checkSources(imdb = i.get('imdb'), tmdb = i.get('tmdb'), tvdb = i.get('tvdb'), trakt = i.get('trakt'), season = i.get('season'), episode = i.get('episode'), tvshowtitle = i.get('tvshowtitle'), title = i.get('title'), year = i.get('tvshowyear') or i.get('year'), premiered = i.get('premiered'), metadata = i)
							if streams: self.mBlock = False
						if self.mBlock: continue

					premiered = None
					if not premiered:
						premiered = i.get('premiered') or None
						if not premiered: premiered = i.get('aired') or None
					if (premiered and Time.integer(premiered) > today) or (not premiered and not self.mUnaired): continue

					self._televisionFiles(item = i, metadata = metadata, link = link)
					count += 1
				except: Logger.error()

		return count

	#gaiaremove
	#gaiafuture - Adding an entire page of shows to the library is extremely expensive.
	#gaiafuture - Each episode for each of the shows is added. This requires the full metadata (show + pack + season + episode metadata).
	#gaiafuture - If the metadata is cached, it should not be a huge issue.
	#gaiafuture - If the metadata is not cached, it has to be retrieved. This can take VERY long and possibly hit the Trakt/IMDb limits.
	#gaiafuture - This has to be somehow improved. Either only allow a single show to be added at a time. Or use something like MetaManager.preload() to first slowly load all metadata (taking the API rate limits into account), and only then adding all of them to the library.
	def _televisionAddMultiple(self, link = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, title = None, year = None):
		from lib.meta.manager import MetaManager

		Loader.hide()
		count = -1
		original = season

		if Dialog.option(title = 33244, message = 35179):
			count = 0
			if self._ready():
				Dialog.notification(title = 33244, message = 35177, icon = Dialog.IconInformation, time = self.mDuration)
				self.mDialog = True

			items = None

			if link:
				from lib.meta.menu import MetaMenu
				items = MetaMenu.instance(media = Media.Show).content(command = link)
				items = items.get('items') if items else None
				if not items:
					items = MetaMenu.instance(media = Media.Episode).content(command = link)
					items = items.get('items') if items else None
			else:
				if season is None: items = MetaManager.instance().metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, pack = False)
				else: items = MetaManager.instance().metadataSeason(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, title = title, year = year, pack = False)
				if items: items = [items]

			if items is None: items = []

			itemsEpisodes = []
			threads = []
			lock = Lock()

			# Retrieving uncached episode metadata can take very long.
			# Each request could potentially make multiple nested requests to seasons, shows, and packs.
			# Limit the number of threads that run concurrently.
			# Not only to reduce threading, but also reduce simultaneous requests to Trakt/TVDb/TMDb/etc.
			semaphore1 = Semaphore(5)
			semaphore2 = Semaphore(5)

			def resolveSeasons(imdb, tmdb, tvdb, trakt, title, year):
				try:
					semaphore1.acquire()
					seasons = MetaManager.instance().metadataSeason(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, pack = False)
					if seasons:
						for season in seasons:
							resolveEpisodes(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season.get('season'))
				except: Logger.error()
				finally: semaphore1.release()

			def resolveEpisodes(imdb, tmdb, tvdb, trakt, season, title, year):
				try:
					semaphore2.acquire()
					episodes = MetaManager.instance().metadataEpisode(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, title = title, year = year, pack = False)
					if episodes:
						lock.acquire()
						itemsEpisodes.extend(episodes)
						lock.release()
				except: Logger.error()
				finally: semaphore2.release()

			for i in items:
				if 'episode' in i:
					itemsEpisodes.append(i)
				else:
					kwargs = {'imdb' : i.get('imdb'), 'tmdb' : i.get('tmdb'), 'tvdb' : i.get('tvdb'), 'trakt' : i.get('trakt'), 'title' : i.get('tvshowtitle') or i.get('title'), 'year' : i.get('tvshowyear') or i.get('year')}
					if 'season' in i:
						kwargs['season'] = i.get('season')
						threads.append(Pool.thread(target = resolveEpisodes, kwargs = kwargs, start = True))
					else:
						threads.append(Pool.thread(target = resolveSeasons, kwargs = kwargs, start = True))
			[i.join() for i in threads]

			for i in itemsEpisodes:
				try:
					if System.aborted(): return System.exit()
					value = self._televisionAddSingle(imdb = i.get('imdb'), tmdb = i.get('tmdb'), tvdb = i.get('tvdb'), trakt = i.get('trakt'), title = i.get('tvshowtitle') or i.get('title'), year = i.get('tvshowyear') or i.get('year'), season = i.get('season'), episode = i.get('episode'), metadata = i, multiple = True)
					if value > 0: count += value
				except: Logger.error()

		return count

	def _televisionResolve(self, title, year, season, episode):
		try:
			name = re.sub(r'\s\s+', ' ', re.sub(r'([^\s\w]|_)+', ' ', title))
			nameLegal = self._legalPath('%s S%02dE%02d %s' % (name, int(season), int(episode), System.name())) + Library.ExtensionMeta
			path = File.joinPath(self._path(self.mLocation, name, year, season), nameLegal)
			if not File.exists(path): # To accomodate the old file name format that did not contain Gaia.
				nameLegal = self._legalPath('%s S%02dE%02d' % (name, int(season), int(episode))) + '.' + System.name().lower()
				path = File.joinPath(self._path(self.mLocation, name, year, season), nameLegal)
			return self._readFile(path)
		except: return None

	def _televisionFiles(self, item, metadata = None, link = None):
		try:
			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			season = item.get('season')
			episode = item.get('episode')
			tvshowtitle = item.get('tvshowtitle')
			title = item.get('title') or item.get('tvshowtitle')

			# Get the show year, not the season or episode year.
			year = None
			if not year:
				for i in [metadata, item]:
					try:
						year = i.get('show').get('tvshowyear') or i.get('show').get('year')
						if year: break
					except: pass
			if not year:
				for i in [metadata, item]:
					try:
						year = i.get('pack').get('year').get('minimum')
						if year: break
					except: pass
			if not year:
				for i in [metadata, item]:
					try:
						year = i.get('tvshowyear') or i.get('year')
						if year: break
					except: pass

			season = int(season)
			episode = int(episode)

			generic = link is None
			name = re.sub(r'\s\s+', ' ', re.sub(r'([^\s\w]|_)+', ' ', tvshowtitle))
			nameLegal = self._legalPath('%s S%02dE%02d %s' % (name, season, episode, System.name()))

			if generic:
				# Do not save the metadata to file. The link becomes too long and Kodi cuts it off.
				#metadata = Converter.quoteTo(Converter.jsonTo(metadata))
				#link = '%s?action=scrape&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&metadata=%s' % (System.arguments(0), title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, metadata)
				parameters = {'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'title' : title, 'tvshowtitle' : tvshowtitle, 'year' : year}
				link = System.command(action = 'scrape', parameters = self._parameterize(parameters), optimize = False, origin = False)
			else:
				data = link
				link = System.command(action = 'libraryResolve', parameters = self._parameterize({'title' : tvshowtitle, 'year' : year, 'season' : season, 'episode' : episode}), optimize = False, origin = False)

			path = self._path(self.mLocation, name, year)

			pathNfo = File.joinPath(path, 'tvshow.nfo')
			self._createDirectory(path)
			self._writeFile(pathNfo, self._infoLink(item))

			path = self._path(self.mLocation, name, year, season)
			pathSrtm = File.joinPath(path, nameLegal + Library.ExtensionStrm)
			self._createDirectory(path)
			self._writeFile(pathSrtm, link)

			if not generic:
				pathGaia = File.joinPath(path, nameLegal + Library.ExtensionMeta)
				self._writeFile(pathGaia, data)
		except: Logger.error()

	##############################################################################
	# MONITOR
	##############################################################################

	@classmethod
	def monitor(self, continues = True):
		if self.enabled() and Settings.getBoolean('library.update.monitor'):
			Pool.thread(target = self._monitor, kwargs = {'continues' : continues}, start = True)

	@classmethod
	def _monitor(self, continues = True):
		library = Library(media = Media.Show)
		if continues:
			while not System.aborted():
				library.update(media = Media.Show, wait = True)
				if System.abortWait(timeout = Library.DurationMonitor): break
		else:
			library.update(media = Media.Show)

	##############################################################################
	# UPDATE
	##############################################################################

	@classmethod
	def refresh(self, notifications = None, wait = True):
		Pool.thread(target = self._libraryRefresh, start = True, join = wait)

	@classmethod
	def update(self, notifications = None, force = None, media = None, wait = True): # Must wait, otherwise the script finishes before the thread.
		Pool.thread(target = Library(media = media)._update, args = (media, notifications, force), start = True, join = wait)

	def _update(self, media = None, notifications = None, force = None):
		try:
			self._createDirectory(self._location(media = Media.Movie))
			self._createDirectory(self._location(media = Media.Show))
		except: Logger.error()

		if Media.isFilm(media): self._updateMovies(notifications = notifications, force = force)
		elif Media.isSerie(media): self._updateShows(notifications = notifications, force = force)
		elif media is None: Library(media = Media.Show)._updateShows(notifications = notifications, force = force, all = True) # Make sure mLocation is initialized.

	def _updateMovies(self, notifications = None, force = None):
		Loader.hide()
		self._libraryUpdate()

	def _updateShows(self, notifications = None, force = None, all = False):
		if notifications is None:
			notifications = Settings.getInteger('library.update.notifications')
			notificationDuration = self.mDuration if notifications == 2 else Library.DurationNoUpdate
			notifications = notifications > 0
		Loader.hide()

		try:
			items = []
			season, episode = [], []
			show = [File.joinPath(self.mLocation, i) for i in File.listDirectory(self.mLocation)[0]]
			for s in show:
				try: season += [File.joinPath(s, i) for i in File.listDirectory(s)[0]]
				except: pass
			for s in season:
				try: episode.append([File.joinPath(s, i) for i in File.listDirectory(s)[1] if i.endswith(Library.ExtensionStrm)][-1])
				except: pass

			for file in episode:
				try:
					data = File.readNow(file)
					if not data.startswith(System.plugin()): continue

					params = Networker.linkDecode(data)

					tvshowtitle = params.get('tvshowtitle')
					if not tvshowtitle: tvshowtitle = params.get('show')
					if not tvshowtitle: continue

					imdb = params.get('imdb')
					tmdb = params.get('tmdb')
					tvdb = params.get('tvdb')
					trakt = params.get('trakt')
					try: year = int(params.get('tvshowyear') or params.get('year'))
					except: year = None

					imdb = 'tt' + re.sub(r'[^0-9]', '', str(imdb))

					items.append({'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'tvshowtitle' : tvshowtitle, 'year' : year})
				except: Logger.error()

			items = [i for x, i in enumerate(items) if i not in items[x + 1:]]
			if len(items) == 0:
				if force: self._libraryUpdate(all = all)
				return
		except:
			Logger.error()
			return

		try:
			library = System.executeJson(method = 'VideoLibrary.GetTVShows', parameters = {'properties' : ['imdbnumber', 'title', 'year']})
			library = library['result']['tvshows']
		except:
			Logger.error()
			return

		if notifications and self._ready():
			Dialog.notification(title = 33244, message = 35181, icon = Dialog.IconInformation, time = notificationDuration)
			self.mDialog = True

		try:
			base = Database(name = Library.DatabaseName)
			base._create('CREATE TABLE IF NOT EXISTS shows (idImdb TEXT, idTmdb TEXT, idTvdb TEXT, idTrakt TEXT, data TEXT);')
		except:
			Logger.error()
			return

		from lib.meta.tools import MetaTools
		from lib.meta.manager import MetaManager
		manager = MetaManager.instance()

		count = 0
		for item in items:
			if System.aborted(): return System.exit()
			it = None

			try:
				query = []
				parameters = []
				for i in ['imdb', 'tmdb', 'tvdb', 'trakt']:
					id = item.get(i)
					if id:
						query.append('id%s = ?' % i.capitalize())
						parameters.append(id)
				if query:
					fetch = base._selectSingle('SELECT data FROM shows WHERE %s;' % ' OR '.join(query), parameters)
					if fetch: it = Converter.jsonFrom(fetch[0])
			except: Logger.error()

			try:
				if it is None:
					it = manager.metadataEpisode(imdb = item.get('imdb'), tmdb = item.get('tmdb'), tvdb = item.get('tvdb'), trakt = item.get('trakt'), title = item.get('tvshowtitle'), year = item.get('year') or item.get('tvshowyear'), season = True) # Retrieve all episodes.
					if it:
						status = (it[0].get('pack', {}).get('status') or it[-1].get('status')).lower()
						it = [{'imdb' : i.get('imdb'), 'tmdb' : i.get('tmdb'), 'tvdb' : i.get('tvdb'), 'trakt' : i.get('trakt'), 'season' : i.get('season'), 'episode' : i.get('episode'), 'tvshowtitle' : i.get('tvshowtitle'), 'title' : i.get('title'), 'year' : item.get('tvshowyear') or item.get('year'), 'premiered' : item.get('premiered')} for i in it]
						if not status == MetaTools.StatusContinuing: base._insert('INSERT INTO shows (idImdb, idTmdb, idTvdb, idTrakt, data) VALUES (?, ?, ?, ?, ?);', parameters = (item.get('imdb'), item.get('tmdb'), item.get('tvdb'), item.get('trakt'), Converter.jsonTo(it)))
			except: Logger.error()

			try:
				id = [i for i in [item.get('imdb'), item.get('tvdb'), item.get('tmdb')] if i]

				episode = [x['title'] for x in library if str(x['imdbnumber']) in id or (x['title'] == item.get('tvshowtitle') and str(x['year']) == str(item.get('tvshowyear') or item.get('year')))][0]
				episode = System.executeJson(method = 'VideoLibrary.GetEpisodes', parameters = {'filter' : {'and' : [{'field' : 'tvshow', 'operator' : 'is', 'value' : episode}]}, 'properties' : ['season', 'episode']})
				episode = episode.get('result', {}).get('episodes', {})
				episode = [{'season': int(i['season']), 'episode': int(i['episode'])} for i in episode]
				episode = sorted(episode, key = lambda x : (x['season'], x['episode']))[-1]

				num = [x for x, y in enumerate(it) if str(y['season']) == str(episode['season']) and str(y['episode']) == str(episode['episode'])][-1]
				it = [y for x, y in enumerate(it) if x > num]
				if len(it) == 0: continue
			except:
				continue

			today = Time.integer(Time.past(hours = 6, format = Time.FormatDate))

			for i in it:
				try:
					if System.aborted(): return System.exit()
					self._televisionFiles(i)
					count += 1
				except: Logger.error()

		if notifications and self.mDialog:
			Dialog.notification(title = 33244, message = 35182, icon = Dialog.IconSuccess, wait = False)
		if force or (self.mUpdate and not self._libraryBusy() and count > 0):
			self._libraryUpdate(all = all)

	##############################################################################
	# CLEAR
	##############################################################################

	@classmethod
	def clear(self, clean = False):
		self.clearDatabase()
		self.clearFile()
		if clean: self.clean()

	@classmethod
	def clearDatabase(self, confirm = False):
		Database(name = Library.DatabaseName).clear(confirm = confirm)

	@classmethod
	def clearFile(self, clean = None):
		paths = [
			self._location(media = Media.Movie, make = False),
			self._location(media = Media.Show, make = False),
		]
		for path in paths:
			File.deleteDirectory(path)

		if clean is None: clean = Dialog.option(title = 35170, message = 33469)
		if clean: self.clean(wait = False)

	##############################################################################
	# SIZE
	##############################################################################

	@classmethod
	def size(self):
		files = self.sizeFile()
		return self.sizeDatabase() + (files if files > 0 else 0)

	@classmethod
	def sizeDatabase(self):
		return Database(name = Library.DatabaseName, connect = False)._size()

	@classmethod
	def sizeFile(self, limit = True):
		total = 0
		checked = []
		paths = [
			self._location(media = Media.Movie, make = False),
			self._location(media = Media.Show, make = False),
		]

		# NB: Limit the total size at 5GB after which size calculations terminate.
		# Otherwise if the user makes the library path point to a HDD with 100s of movies, this function can take a very long time, sinze it will scan the entire HDD.
		if limit is True: limit = 5368709120
		elif not limit: limit = None

		for path in paths:
			if not path in checked:
				size = File.sizeDirectory(path, limit = limit)
				if size < 0: return None
				total += size
				checked.append(path)

		return total

	##############################################################################
	# CLEAN
	##############################################################################

	@classmethod
	def clean(self, update = True, wait = False):
		if wait: self._clean(update = update)
		else: Pool.thread(target = self._clean, kwargs = {'update' : update}, start = True)

	@classmethod
	def _clean(self, update = True):
		System.execute('CleanLibrary(video)', wait = True)
		if update: System.execute('UpdateLibrary(video)', wait = True)

	##############################################################################
	# RESOLVE
	##############################################################################

	def resolve(self, title = None, year = None, season = None, episode = None):
		if self.mMedia == Media.Show or self.mMedia == Media.Season or self.mMedia == Media.Episode:
			command = self._televisionResolve(title = title, year = year, season = season, episode = episode)
		else:
			command = self._movieResolve(title = title, year = year)

		# Avoid playback error dialog:
		#	Playback failed - One or more items failed to play. Check the log for more information abouth this message.
		# Calling this function with "success = True" will automatically execute the command.
		if command:
			#System.executePlugin(command = command)
			System.pluginResolvedSet(success = True, link = command)
		else:
			System.pluginResolvedSet(success = False)
			Dialog.confirm(title = 35170, message = 35494)

	def resolveStrm(self, path):
		if self.pathMeta(path): path = Tools.stringRemoveSuffix(path, Library.ExtensionMeta) + Library.ExtensionStrm
		if self.pathStrm(path): return self._readFile(path)
		else: return None

	def resolveMeta(self, path):
		if self.pathStrm(path): path = Tools.stringRemoveSuffix(path, Library.ExtensionStrm) + Library.ExtensionMeta
		if self.pathMeta(path): return self._readFile(path)
		else: return None

	##############################################################################
	# PATH
	##############################################################################

	@classmethod
	def pathStrm(self, path):
		return path.lower().endswith(Library.ExtensionStrm)

	@classmethod
	def pathMeta(self, path):
		return path.lower().endswith(Library.ExtensionMeta)

	##############################################################################
	# ADD
	##############################################################################

	def add(self, link = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, title = None, year = None, metadata = None, precheck = None):
		count = -1

		if not metadata:
			from lib.meta.manager import MetaManager
			metadata = MetaManager.instance().metadata(media = self.mMedia, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, pack = False)
		elif Tools.isString(metadata):
			metadata = Converter.jsonFrom(metadata)
		if metadata:
			title = metadata.get('tvshowtitle') or metadata.get('title') or metadata.get('originaltitle')
			year = metadata.get('tvshowyear') or metadata.get('year')

		isAddon = link and link.startswith(System.PluginPrefix)
		isLink = link and Networker.linkIs(link)
		isStream = isLink and (not imdb is None or not tmdb is None or not tvdb is None)
		isSingle = (link is None or isAddon or isStream)
		if isSingle and self.mMediaSerie and episode is None: isSingle = False

		if precheck is None:
			if isAddon or isStream: self.mPrecheck = False
		else:
			self.mPrecheck = precheck

		if self.mMediaFilm:
			if isSingle: count = self._movieAddSingle(link = link, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, metadata = metadata)
			else: count = self._movieAddMultiple(link = link)
		elif self.mMediaSerie:
			if isSingle: count = self._televisionAddSingle(link = link, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, title = title, year = year, metadata = metadata)
			else: count = self._televisionAddMultiple(link = link, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, title = title, year = year)

		if count >= 0:
			if self.mDialog:
				if count > 0: Dialog.notification(title = 33244, message = 35178, icon = Dialog.IconSuccess, wait = False)
				else: Dialog.notification(title = 33244, message = 35196, icon = Dialog.IconError, wait = False)
			if self.mUpdate and not self._libraryBusy() and count > 0:
				self._libraryUpdate()
		else:
			if self.mDialog:
				Dialog.notification(title = 33244, message = 35673, icon = Dialog.IconError, wait = False)
