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

import re

from lib.modules.tools import System, Tools, Media, Selection, Settings, File, Converter, Time, Regex, Logger
from lib.modules.interface import Translation, Dialog, Loader
from lib.modules.database import Database
from lib.modules.network import Networker
from lib.modules.concurrency import Pool, Lock

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
	DurationMonitor = 10800 # 3 hours. Number of seconds between library updates by the service.

	##############################################################################
	# CONSTRUCTORS
	##############################################################################

	def __init__(self, media = Media.TypeNone, kids = Selection.TypeUndefined):
		self.mMedia = media
		self.mMediaMovie = Media.typeMovie(self.mMedia)
		self.mMediaTelevision = Media.typeTelevision(self.mMedia)
		self.mInfo = Library.InfoShow if self.mMediaTelevision else Library.InfoMovie
		self.mKids = kids

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
		if not self.mMedia is None: data['media'] = self.mMedia
		if not self.mKids is None: data['kids'] = self.mKids
		data['library'] = 1
		return data

	@classmethod
	def _location(self, media = None, make = True):
		if media is None: return None

		path = None
		if Settings.getInteger('library.location.selection') == 0:
			if media == Media.TypeMovie: label = 32001
			elif media == Media.TypeDocumentary: label = 33470
			elif media == Media.TypeShort: label = 33471
			elif media == Media.TypeShow or media == Media.TypeSeason or media == Media.TypeEpisode: label = 32002
			path = File.joinPath(Settings.path('library.location.combined'), Translation.string(label))
		else:
			if media == Media.TypeSeason or media == Media.TypeEpisode: media = Media.TypeShow
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
				arguments = re.compile('ftp://(.+?):(.+?)@(.+?):?(\d+)?/(.+/?)').findall(path)
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
			path = File.legalPath(path)
			return File.writeNow(path, content)
		except:
			return False

	def _infoLink(self, ids):
		if 'tvdb' in ids and not str(ids['tvdb']) == '' and not str(ids['tvdb']) == '0':
			return Library.LinkTvdb % (str(ids['tvdb']))
		elif 'tmdb' in ids and not str(ids['tmdb']) == '' and not str(ids['tmdb']) == '0':
			return Library.LinkTmdb % (self.mInfo, str(ids['tmdb']))
		elif 'imdb' in ids and not str(ids['imdb']) == '' and not str(ids['imdb']) == '0':
			return Library.LinkImdb % (str(ids['imdb']))
		else:
			return ''

	@classmethod
	def _checkSources(self, title, year, imdb, tvdb = None, season = None, episode = None, tvshowtitle = None, premiered = None):
		try:
			from lib.modules import core
			streams = core.Core().scrape(title = title, year = year, imdb = imdb, tvdb = tvdb, season = season, episode = episode, tvshowtitle = tvshowtitle, premiered = premiered)
			return streams and len(streams) > 1
		except:
			Logger.error()
			return False

	@classmethod
	def _legalPath(self, path):
		try:
			path = path.strip()
			path = re.sub(r'(?!%s)[^\w\-_\.]', '.', path)
			path = re.sub('\.+', '.', path)
			path = re.sub(re.compile('(CON|PRN|AUX|NUL|COM\d|LPT\d)\.', re.I), '\\1_', path)
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
				paths.append(self._location(media = Media.TypeMovie))
				paths.append(self._location(media = Media.TypeShow))
				paths.append(self._location(media = Media.TypeDocumentary))
				paths.append(self._location(media = Media.TypeShort))
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
		type = 'tvshows' if Media.typeTelevision(self.mMedia) else 'movies'
		System.execute('ActivateWindow(10025,library://video/%s/,return)' % type)

	def location(self):
		return self.mLocation

	##############################################################################
	# MOVIES
	##############################################################################

	def _movieAddSingle(self, title, year, imdb, tmdb, metadata, multiple = False, link = None):
		count = 0
		locationKodi = self.mLocation
		locationResolved = File.translate(locationKodi)

		if self._ready() and not multiple:
			Dialog.notification(title = 33244, message = 35177, icon = Dialog.IconInformation, time = self.mDuration)
			self.mDialog = True

		library = []
		try:
			if self.mDuplicates:
				id = [imdb, tmdb] if not tmdb == '0' else [imdb]
				library = System.executeJson(method = 'VideoLibrary.GetMovies', parameters = {'filter' : {'or' : [{'field' : 'year', 'operator' : 'is', 'value' : str(year)}, {'field' : 'year', 'operator' : 'is', 'value' : str(int(year) + 1)}, {'field' : 'year', 'operator' : 'is', 'value' : str(int(year) - 1)}]}, 'properties'  : ['imdbnumber', 'originaltitle', 'year', 'file']})
				library = library['result']['movies']
				library = [i for i in library if ((i['file'].startswith(locationKodi) or i['file'].startswith(locationResolved)) and (i['file'].endswith(Library.ExtensionStrm) or i['file'].endswith(Library.ExtensionMeta))) and (str(i['imdbnumber']) in id or (i['originaltitle'] == title and str(i['year']) == year))]
		except: pass

		if len(library) == 0:
			if not self.mPrecheck or self._checkSources(title, year, imdb, None, None, None, None, None):
				self._movieFiles(title = title, year = year, imdb = imdb, tmdb = tmdb, metadata = metadata, link = link)
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

			from lib.indexers.movies import Movies
			instance = Movies(media = self.mMedia, kids = self.mKids)
			try:
				function = getattr(instance, link)
				if not function or not callable(function): raise Exception()
				items = function()
			except:
				items = instance.retrieve(link = link, menu = False)

			if items is None: items = []
			for i in items:
				try:
					if System.aborted(): return System.exit()
					value = self._movieAddSingle(title = i['title'], year = i['year'], imdb = i['imdb'], tmdb = i['tmdb'], metadata = i, multiple = True)
					if value > 0: count += value
				except:
					pass

		return count

	def _movieResolve(self, title, year):
		try:
			name = re.sub('\s\s+', ' ', re.sub('([^\s\w]|_)+', ' ', title))
			nameLegal = self._legalPath('%s (%s) %s' % (name, year, System.name())) + Library.ExtensionMeta
			path = File.joinPath(self._path(self.mLocation, name, year), nameLegal)
			if not File.exists(path): # To accomodate the old file name format that did not contain the year and Gaia.
				nameLegal = self._legalPath(name) + '.' + System.name().lower()
				path = File.joinPath(self._path(self.mLocation, name, year), nameLegal)
			return self._readFile(path)
		except: return None

	def _movieFiles(self, title, year, imdb, tmdb, metadata = None, link = None):
		try:
			name = re.sub('\s\s+', ' ', re.sub('([^\s\w]|_)+', ' ', title))
			nameLegal = self._legalPath('%s (%s) %s' % (name, year, System.name()))
			generic = link is None
			data = None

			if generic:
				# Do not save the metadata to file. The link becomes too long and Kodi cuts it off.
				#link = '%s?action=scrape&title=%s&year=%s&imdb=%s&tmdb=%s&metadata=%s' % (System.arguments(0), Converter.quoteTo(title), year, imdb, tmdb, metadata)
				link = System.command(action = 'scrape', parameters = self._parameterize({'title' : title, 'year' : year, 'imdb' : imdb, 'tmdb' : tmdb}))
			else:
				data = link
				link = System.command(action = 'libraryResolve', parameters = self._parameterize({'title' : title, 'year' : year}))

			path = self._path(self.mLocation, name, year)
			self._createDirectory(path)

			pathSrtm = File.joinPath(path, nameLegal + Library.ExtensionStrm)
			self._writeFile(pathSrtm, link)

			pathNfo = File.joinPath(path, 'movie.nfo')
			self._writeFile(pathNfo, self._infoLink({'imdb': imdb, 'tmdb': tmdb}))

			if not generic:
				pathGaia = File.joinPath(path, nameLegal + Library.ExtensionMeta)
				self._writeFile(pathGaia, data)
		except:
			Logger.error()

	##############################################################################
	# SHOW
	##############################################################################

	def _televisionAddSingle(self, title, year, season, episode, imdb, tvdb, metadata, multiple = False, link = None):
		count = 0
		locationKodi = self.mLocation
		locationResolved = File.translate(locationKodi)

		if self._ready() and not multiple:
			Dialog.notification(title = 33244, message = 35177, icon = Dialog.IconInformation, time = self.mDuration)
			self.mDialog = True

		if metadata and 'tvdb' in metadata and 'season' in metadata and 'episode' in metadata:
			items = [metadata]
		else:
			from lib.indexers.episodes import Episodes
			items = Episodes(kids = self.mKids).metadata(idImdb = imdb, idTvdb = tvdb, title = title, year = year, season = season, episode = episode)
			if items: items = [items]

		try: items = [{'title': i['title'], 'year': i['year'], 'imdb': i['imdb'], 'tvdb': i['tvdb'], 'season': i['season'], 'episode': i['episode'], 'tvshowtitle': i['tvshowtitle'], 'premiered': i['premiered'], 'count': i['count'] if 'count' in i else None} for i in items]
		except: items = []

		try:
			if self.mDuplicates and len(items) > 0:
				id = [items[0]['imdb'], items[0]['tvdb']]

				library = System.executeJson(method = 'VideoLibrary.GetTVShows', parameters = {'properties' : ['imdbnumber', 'title', 'year']})
				library = library['result']['tvshows']
				library = [i['title'] for i in library if str(i['imdbnumber']) in id or (i['title'] == items[0]['tvshowtitle'] and str(i['year']) == items[0]['year'])][0]

				library = System.executeJson(method = 'VideoLibrary.GetEpisodes', parameters = {'filter' : {'and' : [{'field' : 'tvshow', 'operator' : 'is', 'value' : library}]}, 'properties' : ['season', 'episode', 'file']})
				library = library['result']['episodes']
				library = [i for i in library if (i['file'].startswith(locationKodi) or i['file'].startswith(locationResolved)) and (i['file'].endswith(Library.ExtensionStrm) or i['file'].endswith(Library.ExtensionMeta))]
				library = ['S%02dE%02d' % (int(i['season']), int(i['episode'])) for i in library]

				items = [i for i in items if not 'S%02dE%02d' % (int(i['season']), int(i['episode'])) in library]
		except: pass

		today = Time.integer(Time.past(hours = 6, format = Time.FormatDate))

		if len(items) == 0:
			count = -1
		else:
			for i in items:
				try:
					if System.aborted(): return System.exit()

					if self.mPrecheck:
						if i['episode'] == 1:
							self.mBlock = True
							streams = self._checkSources(i['title'], i['year'], i['imdb'], i['tvdb'], i['season'], i['episode'], i['tvshowtitle'], i['premiered'])
							if streams: self.mBlock = False
						if self.mBlock: continue

					premiered = None
					if not premiered and 'premiered' in i:
						premiered = i['premiered']
						if not premiered or premiered == '' or premiered == '0': premiered = None
					if not premiered and 'aired' in i:
						premiered = i['aired']
						if not premiered or premiered == '' or premiered == '0': premiered = None

					if (premiered and Time.integer(premiered) > today) or (not premiered and not self.mUnaired): continue

					self._televisionFiles(item = i, metadata = metadata, link = link)
					count += 1
				except: Logger.error()

		return count

	def _televisionAddMultiple(self, link = None, title = None, year = None, imdb = None, tvdb = None, season = None):
		from lib.indexers.shows import Shows
		from lib.indexers.seasons import Seasons
		from lib.indexers.episodes import Episodes

		Loader.hide()
		count = -1

		if Dialog.option(title = 33244, message = 35179):
			count = 0
			if self._ready():
				Dialog.notification(title = 33244, message = 35177, icon = Dialog.IconInformation, time = self.mDuration)
				self.mDialog = True

			items = None

			if link:
				try:
					instance = Shows(kids = self.mKids)
					try:
						function = getattr(instance, link)
						if not function or not callable(function): raise Exception()
						items = function()
					except:
						items = instance.retrieve(link = link, menu = False)
				except:
					pass

				if not items or len(items) == 0:
					instance = Episodes(kids = self.mKids)
					try:
						function = getattr(instance, link)
						if not function or not callable(function): raise Exception()
						items = function()
					except:
						items = instance.retrieve(link = link, menu = False)
			else:
				if season is None: items = Shows(kids = self.mKids).metadata(idImdb = imdb, idTvdb = tvdb, title = title, year = year)
				else: items = Seasons(kids = self.mKids).metadata(idImdb = imdb, idTvdb = tvdb, title = title, year = year, season = season)
				if items: items = [items]

			if items is None: items = []

			itemsEpisodes = []
			threads = []
			lock = Lock()

			def resolveSeasons(title, year, imdb, tvdb):
				seasons = Seasons(kids = self.mKids).metadata(idImdb = imdb, idTvdb = tvdb, title = title, year = year)
				if seasons:
					for season in seasons:
						resolveEpisodes(imdb = imdb, tvdb = tvdb, title = title, year = year, season = season['season'])

			def resolveEpisodes(title, year, imdb, tvdb, season):
				episodes = Episodes(kids = self.mKids).metadata(idImdb = imdb, idTvdb = tvdb, title = title, year = year, season = season)
				if episodes:
					lock.acquire()
					itemsEpisodes.extend(episodes)
					lock.release()

			for i in items:
				if 'episode' in i: itemsEpisodes.append(i)
				elif 'season' in i: threads.append(Pool.thread(target = resolveEpisodes, args = (i['tvshowtitle'] if 'tvshowtitle' in i else i['title'], i['year'], i['imdb'], i['tvdb'], i['season']), start = True))
				else: threads.append(Pool.thread(target = resolveSeasons, args = (i['tvshowtitle'] if 'tvshowtitle' in i else i['title'], i['year'], i['imdb'], i['tvdb']), start = True))
			[i.join() for i in threads]

			for i in itemsEpisodes:
				try:
					if System.aborted(): return System.exit()
					value = self._televisionAddSingle(title = i['tvshowtitle'] if 'tvshowtitle' in i else i['title'], year = i['year'] if 'year' in i else None, season = i['season'], episode = i['episode'], imdb = i['imdb'], tvdb = i['tvdb'], metadata = i, multiple = True)
					if value > 0: count += value
				except: Logger.error()

		return count

	def _televisionResolve(self, title, year, season, episode):
		try:
			name = re.sub('\s\s+', ' ', re.sub('([^\s\w]|_)+', ' ', title))
			nameLegal = self._legalPath('%s S%02dE%02d %s' % (name, int(season), int(episode), System.name())) + Library.ExtensionMeta
			path = File.joinPath(self._path(self.mLocation, name, year, season), nameLegal)
			if not File.exists(path): # To accomodate the old file name format that did not contain Gaia.
				nameLegal = self._legalPath('%s S%02dE%02d' % (name, int(season), int(episode))) + '.' + System.name().lower()
				path = File.joinPath(self._path(self.mLocation, name, year, season), nameLegal)
			return self._readFile(path)
		except: return None

	def _televisionFiles(self, item, metadata = None, link = None):
		try:
			try: year = metadata['year']
			except: year = item['year']
			title, imdb, tvdb, season, episode, showtitle, count = item['title'], item['imdb'], item['tvdb'], item['season'], item['episode'], item['tvshowtitle'], item['count']

			season = int(season)
			episode = int(episode)

			generic = link is None
			name = re.sub('\s\s+', ' ', re.sub('([^\s\w]|_)+', ' ', showtitle))
			nameLegal = self._legalPath('%s S%02dE%02d %s' % (name, season, episode, System.name()))

			if generic:
				# Do not save the metadata to file. The link becomes too long and Kodi cuts it off.
				#metadata = Converter.quoteTo(Converter.jsonTo(metadata))
				#link = '%s?action=scrape&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&metadata=%s' % (System.arguments(0), title, year, imdb, tvdb, season, episode, showtitle, premiered, metadata)
				parameters = {'title' : title, 'tvshowtitle' : showtitle, 'year' : year, 'imdb' : imdb, 'tvdb' : tvdb, 'season' : season, 'episode' : episode}
				if count: parameters['count'] = count
				link = System.command(action = 'scrape', parameters = self._parameterize(parameters))
			else:
				data = link
				link = System.command(action = 'libraryResolve', parameters = self._parameterize({'title' : showtitle, 'year' : year, 'season' : season, 'episode' : episode}))

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
		library = Library(media = Media.TypeShow)
		if continues:
			while not System.aborted():
				library.update(media = Media.TypeShow, wait = True)
				if System.abortWait(timeout = Library.DurationMonitor): break
		else:
			library.update(media = Media.TypeShow)

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
			self._createDirectory(self._location(media = Media.TypeMovie))
			self._createDirectory(self._location(media = Media.TypeShow))
			self._createDirectory(self._location(media = Media.TypeDocumentary))
			self._createDirectory(self._location(media = Media.TypeShort))
		except: Logger.error()

		if Media.typeMovie(media): self._updateMovies(notifications = notifications, force = force)
		elif Media.typeTelevision(media): self._updateShows(notifications = notifications, force = force)
		elif media is None: Library(media = Media.TypeShow)._updateShows(notifications = notifications, force = force, all = True) # Make sure mLocation is initialized.

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

					try: tvshowtitle = params['tvshowtitle']
					except: tvshowtitle = None
					try: tvshowtitle = params['show']
					except: pass
					if tvshowtitle is None or tvshowtitle == '': continue

					year, imdb, tvdb = params['year'], params['imdb'], params['tvdb']

					imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))

					try: tmdb = params['tmdb']
					except: tmdb = '0'

					items.append({'tvshowtitle': tvshowtitle, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb})
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
			base._create('CREATE TABLE IF NOT EXISTS shows (id TEXT PRIMARY KEY, items TEXT);')
		except:
			Logger.error()
			return

		try:
			from lib.indexers.episodes import Episodes
		except:
			Logger.error()
			return

		count = 0

		for item in items:
			if System.aborted(): return System.exit()
			it = None

			try:
				fetch = base._selectSingle('SELECT * FROM shows WHERE id = "%s";' % item['tvdb'])
				if fetch: it = Converter.jsonFrom(fetch[1])
			except: Logger.error()

			try:
				if it is None:
					it = Episodes(kids = self.mKids).retrieve(idImdb = item['imdb'], idTvdb = item['tvdb'], title = item['tvshowtitle'], year = item['year'], menu = False)
					if it:
						status = it[0]['status'].lower()
						it = [{'title': i['title'], 'year': item['year'] if item['year'] else i['year'], 'imdb': i['imdb'], 'tvdb': i['tvdb'], 'season': i['season'], 'episode': i['episode'], 'tvshowtitle': i['tvshowtitle'], 'premiered': i['premiered'], 'count': i['count'] if 'count' in i else None} for i in it]
						if not status == 'continuing' and not status == 'continue':
							json = Converter.jsonTo(it)
							base._insert('INSERT INTO shows VALUES (?, ?);', parameters = (item['tvdb'], json))
			except: Logger.error()

			try:
				id = [item['imdb'], item['tvdb']]
				if not item['tmdb'] == '0': id += [item['tmdb']]

				episode = [x['title'] for x in library if str(x['imdbnumber']) in id or (x['title'] == item['tvshowtitle'] and str(x['year']) == item['year'])][0]
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

					premiered = None
					if not premiered and 'premiered' in i:
						premiered = i['premiered']
						if not premiered or premiered == '' or premiered == '0': premiered = None
					if not premiered and 'aired' in i:
						premiered = i['aired']
						if not premiered or premiered == '' or premiered == '0': premiered = None

					#if (premiered and Time.integer(premiered) > today) or (not premiered and not self.mUnaired):
					#	continue

					self._televisionFiles(i)
					count += 1
				except:
					Logger.error()

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
			self._location(media = Media.TypeMovie, make = False),
			self._location(media = Media.TypeDocumentary, make = False),
			self._location(media = Media.TypeShort, make = False),
			self._location(media = Media.TypeShow, make = False),
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
			self._location(media = Media.TypeMovie, make = False),
			self._location(media = Media.TypeDocumentary, make = False),
			self._location(media = Media.TypeShort, make = False),
			self._location(media = Media.TypeShow, make = False),
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
		if self.mMedia == Media.TypeShow or self.mMedia == Media.TypeSeason or self.mMedia == Media.TypeEpisode:
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
		if self.pathMeta(path): path = path.rstrip(Library.ExtensionMeta) + Library.ExtensionStrm
		if self.pathStrm(path): return self._readFile(path)
		else: return None

	def resolveMeta(self, path):
		if self.pathStrm(path): path = path.rstrip(Library.ExtensionStrm) + Library.ExtensionMeta
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

	def add(self, link = None, title = None, year = None, season = None, episode = None, imdb = None, tmdb = None, tvdb = None, metadata = None, precheck = None):
		from lib.modules import network

		count = -1

		try: metadata = Converter.jsonFrom(metadata)
		except: pass

		isAddon = link and link.startswith(System.PluginPrefix)
		isLink = link and Networker.linkIs(link)
		isStream = isLink and (not imdb is None or not tmdb is None or not tvdb is None)
		isSingle = (link is None or isAddon or isStream)
		if isSingle and self.mMediaTelevision and episode is None: isSingle = False

		if precheck is None:
			if isAddon or isStream: self.mPrecheck = False
		else:
			self.mPrecheck = precheck

		if self.mMediaMovie:
			if isSingle: count = self._movieAddSingle(link = link, title = title, year = year, imdb = imdb, tmdb = tmdb, metadata = metadata)
			else: count = self._movieAddMultiple(link = link)
		elif self.mMediaTelevision:
			if isSingle: count = self._televisionAddSingle(link = link, title = title, year = year, season = season, episode = episode, imdb = imdb, tvdb = tvdb, metadata = metadata)
			else: count = self._televisionAddMultiple(link = link, title = title, year = year, season = season, imdb = imdb, tvdb = tvdb)

		if count >= 0:
			if self.mDialog:
				if count > 0: Dialog.notification(title = 33244, message = 35178, icon = Dialog.IconSuccess, wait = False)
				else: Dialog.notification(title = 33244, message = 35196, icon = Dialog.IconError, wait = False)
			if self.mUpdate and not self._libraryBusy() and count > 0:
				self._libraryUpdate()
		else:
			if self.mDialog:
				Dialog.notification(title = 33244, message = 35673, icon = Dialog.IconError, wait = False)
