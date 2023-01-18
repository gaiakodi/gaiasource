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

from lib.modules import trakt

from lib.modules.tools import Logger, Media, Kids, Selection, Settings, Tools, System, Time, Regex, Language, Converter, Math
from lib.modules.interface import Dialog, Loader, Translation, Format, Directory
from lib.modules.network import Networker
from lib.modules.convert import ConverterDuration, ConverterTime
from lib.modules.account import Trakt, Imdb, Tmdb
from lib.modules.parser import Parser, Raw
from lib.modules.clean import Genre, Title
from lib.modules.cache import Cache, Memory
from lib.modules.concurrency import Pool, Lock, Semaphore

from lib.meta.cache import MetaCache
from lib.meta.image import MetaImage
from lib.meta.tools import MetaTools
from lib.meta.processors.imdb import MetaImdb
from lib.meta.processors.tmdb import MetaTmdb
from lib.meta.processors.fanart import MetaFanart

class Sets(object):

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, media = Media.TypeSet, kids = Selection.TypeUndefined):
		self.mMetatools = MetaTools.instance()
		self.mCache = Cache.instance()

		self.mDeveloper = System.developerVersion()
		self.mDetail = self.mMetatools.settingsDetail()
		self.mLimit = self.mMetatools.settingsPageMovie()

		self.mMedia = media

		self.mKids = kids
		self.mKidsOnly = self.mMetatools.kidsOnly(kids = self.mKids)

		self.mYear = Time.year()
		self.mLanguage = self.mMetatools.settingsLanguage()

		self.mModeRelease = False
		self.mModeSearch = False

		self.mAccountTmdb = Tmdb().key()

	##############################################################################
	# RETRIEVE
	##############################################################################

	def retrieve(self, link, detailed = True, menu = True, full = False, clean = True, quick = None, refresh = False):
		try:
			self.mModeRelease = link in ['new', 'home', 'disc']
			items = []

			try: link = getattr(self, link + '_link')
			except: pass

			elif link == 'sets':

				items = self.cache('cacheRefreshLong', refresh, MetaTmdb.sets)
				items = self.page(link = link, items = items)
				if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

		except: Logger.error()

		genre = self.search_link in link and not self.persons_link in link and not self.personlist_link in link
		kids = not self.persons_link in link and not self.personlist_link in link
		search = self.search_link in link
		return self.process(items = items, menu = menu, genre = genre, kids = kids, search = search, refresh = refresh)

	# genre: Filter by genre depending on wether the items are movies, docus, or shorts.
	# kids: Filter by age restriction.
	# search: Wether or not the items are from search results.
	# duplicate: Filter out duplicates.
	# release: Filter out unreleased items. If True, return any items released before today. If date-string,return items before the date. If integer, return items older than the given number of days.
	# limit: Limit the number of items. If True, use the setting's limit. If integer, limit up to the given number.
	def process(self, items, menu = True, genre = True, kids = True, search = False, duplicate = False, release = False, limit = False, refresh = False):
		if items:
			if duplicate: items = self.mMetatools.filterDuplicate(items = items)

			if genre:
				if self.mMedia == Media.TypeDocumentary: items = [i for i in items if 'genre' in i and 'documentary' in [j.lower() for j in i['genre']]]
				elif self.mMedia == Media.TypeShort: items = [i for i in items if 'genre' in i and 'short' in [j.lower() for j in i['genre']]]

			if kids: items = self.mMetatools.filterKids(items = items, kids = self.mKids)

			if release:
				date = None
				days = None
				if release is True: days = 1
				elif Tools.isInteger(release) and release < 10000: days = release
				elif release: date = release
				items = self.mMetatools.filterRelease(items = items, date = date, days = days)

			if limit: items = self.mMetatools.filterLimit(items = items, limit = self.mLimit if limit is True else limit)

			if items and menu:
				if refresh: # Check Context commandMetadataList() for more info.
					Loader.hide()
					Directory.refresh()
				else:
					self.menu(items)

		if not items:
			Loader.hide()
			if menu: Dialog.notification(title = 32010 if search else 32001, message = 33049, icon = Dialog.IconInformation)
		return items

	def cache(self, cache, refresh, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cacheClear' if refresh else cache, *args, **kwargs)

	##############################################################################
	# PAGE
	##############################################################################

	def page(self, link, items, limit = None, sort = None, maximum = None):
		# Some Trakt API endpoint do not support pagination.
		# If the user has many watched shows, these list can get very long, making menu loading slow while extended metadata is retrieved.
		# Manually handle paging.

		page = 1
		if limit is None: limit = self.mLimit
		parameters = Networker.linkParameters(link = link)
		if 'limit' in parameters and 'page' in parameters: page = int(parameters['page'])
		parameters['page'] = page + 1
		parameters['limit'] = limit

		items = items[(page - 1) * limit : page * limit]

		# Sort first, since we want to page in accordance to the user's preferred sorting.
		if sort: self.sort(items = items, type = sort)

		if len(items) >= limit and (not maximum or (page + 1) * limit <= maximum):
			next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')
			for item in items: item['next'] = next

		return items

	##############################################################################
	# SORT
	##############################################################################

	def sort(self, items):
		try:
			if Settings.getBoolean('navigation.sort.favourite'):
				attribute = Settings.getInteger('navigation.sort.favourite.%s.type' % self.mMedia)
				reverse = Settings.getInteger('navigation.sort.favourite.%s.order' % self.mMedia) == 1
				if attribute > 0:
					if attribute == 1:
						if Settings.getBoolean('navigation.sort.favourite.article'):
							items = sorted(items, key = lambda k: Regex.remove(data = k['title'], expression = '(^the\s|^an?\s)', group = 1), reverse = reverse)
						else:
							items = sorted(items, key = lambda k: k['title'].lower(), reverse = reverse)
					elif attribute == 2:
						for i in range(len(items)):
							if not 'rating' in items[i]: items[i]['rating'] = None
						items = sorted(items, key = lambda k: float(k['rating']), reverse = reverse)
					elif attribute == 3:
						for i in range(len(items)):
							if not 'votes' in items[i]: items[i]['votes'] = None
						items = sorted(items, key = lambda k: int(k['votes']), reverse = reverse)
					elif attribute == 4:
						for i in range(len(items)):
							if not 'premiered' in items[i]: items[i]['premiered'] = None
						items = sorted(items, key = lambda k: k['premiered'], reverse = reverse)
					elif attribute == 5:
						for i in range(len(items)):
							if not 'added' in items[i]: items[i]['added'] = None
						items = sorted(items, key = lambda k: k['added'], reverse = reverse)
					elif attribute == 6:
						for i in range(len(items)):
							if not 'watched' in items[i]: items[i]['watched'] = None
						items = sorted(items, key = lambda k: k['watched'], reverse = reverse)
				elif reverse:
					items.reverse()
		except: Logger.error()
		return items

	##############################################################################
	# SEARCH
	##############################################################################

	#gaiaremove
	def search(self, terms = None):
		try:
			from lib.modules.search import Searches

			if terms:
				if not terms: return None
				Loader.show()
				if self.mMedia == Media.TypeDocumentary: Searches().updateDocumentaries(terms)
				elif self.mMedia == Media.TypeShort: Searches().updateShorts(terms)
				else: Searches().updateMovies(terms)
			else:
				terms = Dialog.input(title = 32010)
				if not terms: return None
				Loader.show()
				if self.mMedia == Media.TypeDocumentary: Searches().insertDocumentaries(terms, self.mKids)
				elif self.mMedia == Media.TypeShort: Searches().insertShorts(terms, self.mKids)
				else: Searches().insertMovies(terms, self.mKids)

			# Use executeContainer() instead of directly calling retrieve().
			# This is important for shows. Otherwise if you open the season menu of a searched show and go back to the previous menu, the search dialog pops up again.
			link = self.search_link + Networker.linkQuote(terms, plus = True)
			System.executeContainer(action = 'moviesRetrieve', parameters = {'link' : link, 'media' : self.mMedia, 'kids' : self.mKids})
			#return self.retrieve(link)
		except:
			Logger.error()
			return None

	##############################################################################
	# METADATA
	##############################################################################

	def metadata(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = False, cache = False):
		try:
			single = False
			if items or idTmdb or title:
				if items:
					if not Tools.isArray(items):
						single = True
						items = [items]
				else:
					single = True
					items = [{'imdb' : idImdb, 'tmdb' : idTmdb, 'tvdb' : idTvdb, 'trakt' : idTrakt, 'title' : title, 'year' : year}]
				if filter is None: filter = not single

				lock = Lock()
				locks = {}
				semaphore = Semaphore(50)
				metacache = MetaCache.instance()
				items = metacache.select(type = MetaCache.TypeSet, items = items)

				metadataForeground = []
				metadataBackground = []
				threadsForeground = []
				threadsBackground = []

				if quick is None:
					for item in items:
						try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
						except: refreshing = MetaCache.RefreshForeground
						if refreshing == MetaCache.RefreshForeground or refresh:
							self.mMetatools.busyStart(media = self.mMedia, item = item)
							semaphore.acquire()
							threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'foreground'}, start = True))
						elif refreshing == MetaCache.RefreshBackground:
							if not self.mMetatools.busyStart(media = self.mMedia, item = item):
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'background'})
				else:
					items = Tools.listShuffle(items)
					lookup = []
					counter = abs(quick) if Tools.isInteger(quick) else None
					foreground = Tools.isInteger(quick)
					background = (Tools.isInteger(quick) and quick > 0) or (quick is True)
					for item in items:
						try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
						except: refreshing = MetaCache.RefreshForeground
						if refreshing == MetaCache.RefreshNone:
							lookup.append(item)
						elif refreshing == MetaCache.RefreshForeground and (counter is None or len(lookup) < counter):
							if foreground:
								self.mMetatools.busyStart(media = self.mMedia, item = item)
								lookup.append(item)
								semaphore.acquire()
								threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'foreground'}, start = True))
						elif refreshing == MetaCache.RefreshBackground or (counter is None or len(lookup) >= counter):
							if background and not self.mMetatools.busyStart(media = self.mMedia, item = item):
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'mode' : 'background'})
					items = lookup

				# Wait for metadata that does not exist in the metacache.
				[thread.join() for thread in threadsForeground]
				if metadataForeground: metacache.insert(type = MetaCache.TypeSet, items = metadataForeground)

				# Let the refresh of old metadata run in the background for the next menu load.
				# Only start the threads here, so that background threads do not interfere or slow down the foreground threads.
				if threadsBackground:
					def _metadataBackground():
						for i in range(len(threadsBackground)):
							semaphore.acquire()
							threadsBackground[i] = Pool.thread(target = self.metadataUpdate, kwargs = threadsBackground[i], start = True)
						[thread.join() for thread in threadsBackground]
						if metadataBackground: metacache.insert(type = MetaCache.TypeSet, items = metadataBackground)

					# Make a deep copy of the items, since the items can be edited below while these threads are still busy, and we do not want to store the extra details in the database.
					for i in threadsBackground: i['item'] = Tools.copy(i['item'])
					Pool.thread(target = _metadataBackground, start = True)

				if filter: items = [i for i in items if 'tmdb' in i and i['tmdb']]

			# Remove temporary, useless, or already aggregatd data, to keep the size of the data passed arround small.
			if clean and items:
				for item in items:
					try: del item['temp']
					except: pass
					try: del item[MetaCache.Attribute]
					except: pass
		except: Logger.error()

		if single: return items[0] if items else None
		else: return items

	def metadataUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, filter = None, cache = False, mode = None):
		try:
			id = None
			complete = True

			idImdb = str(item['imdb']) if item and 'imdb' in item and item['imdb'] else None
			idTmdb = str(item['tmdb']) if item and 'tmdb' in item and item['tmdb'] else None
			idTvdb = str(item['tvdb']) if item and 'tvdb' in item and item['tvdb'] else None
			idTrakt = str(item['trakt']) if item and 'trakt' in item and item['trakt'] else None
			idSlug = str(item['slug']) if item and 'slug' in item and item['slug'] else None

			title = item['title'] if item and 'title' in item and item['title'] else None
			year = item['year'] if item and 'year' in item and item['year'] else None

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same movie appears multiple times in the list (some Trakt lists, eg watched list where a movie was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					item.update(data)
					return

			if not idTmdb:
				title = item['title'] if 'title' in item else None
				year = item['year'] if 'year' in item else None
				ids = self.metadataId(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
				if ids:
					if not ids['complete']: complete = False
					ids = ids['data']
					if ids and 'id' in ids:
						ids = ids['id']
						if ids:
							if not idImdb and 'imdb' in ids: idImdb = ids['imdb']
							if not idTmdb and 'tmdb' in ids: idTmdb = ids['tmdb']
							if not idTvdb and 'tvdb' in ids: idTvdb = ids['tvdb']
							if not idTrakt and 'trakt' in ids: idTrakt = ids['trakt']
							if not idSlug and 'slug' in ids: idSlug = ids['slug']
			if filter and not idImdb: return False

			developer = self.metadataDeveloper(idImdb = idImdb, idTmdb = idTmdb, idTrakt = idTrakt, title = title, year = year, item = item)
			if developer: Logger.log('SET METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			if self.mDetail == MetaTools.DetailEssential:
				requests = [
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
				]
			elif self.mDetail == MetaTools.DetailStandard:
				requests = [
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
				]
			elif self.mDetail == MetaTools.DetailExtended:
				requests = [
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache}},
				]
			else:
				requests = []

			datas = self.metadataRetrieve(requests = requests)

			data = {}
			images = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'user' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			# Keep a specific order. Later values replace newer values.
			for i in ['tmdb']:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								complete = False
								if developer: Logger.log('INCOMPLETE SET METADATA [%s]: %s' % (i.upper(), developer))
							provider = value['provider']
							value = value['data']
							if value:
								if MetaImage.Attribute in value:
									images = Tools.update(images, value[MetaImage.Attribute], none = True, lists = True, unique = False)
									del value[MetaImage.Attribute]
								if 'rating' in value: voting['rating'][provider] = value['rating']
								if 'ratinguser' in value: voting['user'][provider] = value['ratinguser']
								if 'votes' in value: voting['votes'][provider] = value['votes']
								data = Tools.update(data, value, none = True, lists = False, unique = False)

			data['voting'] = voting
			data = {k : v for k, v in data.items() if not v is None}

			if 'id' in data and data['id']:
				if not idImdb and 'imdb' in data['id']: idImdb = data['id']['imdb']
				if not idTmdb and 'tmdb' in data['id']: idTmdb = data['id']['tmdb']
				if not idTvdb and 'tvdb' in data['id']: idTvdb = data['id']['tvdb']
				if not idTrakt and 'trakt' in data['id']: idTrakt = data['id']['trakt']
				if not idSlug and 'slug' in data['id']: idSlug = data['id']['slug']

			# This is for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
			# At some later point the entire addon should be updated to have the new ID structure.
			if idImdb: data['imdb'] = idImdb
			if idTmdb: data['tmdb'] = idTmdb
			if idTvdb: data['tvdb'] = idTvdb
			if idTrakt: data['trakt'] = idTrakt
			if idSlug: data['slug'] = idSlug

			if images: MetaImage.update(media = MetaImage.MediaMovie, images = images, data = data)

			# Do this before here already.
			# Otherwise a bunch of regular expressions are called every time the menu is loaded.
			self.mMetatools.cleanPlot(metadata = data)

			# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
			# More info under meta -> tools.py -> cleanVoting().
			self.mMetatools.cleanVoting(metadata = data)

			Memory.set(id = id, value = data, local = True, kodi = False)
			item.update(data)

			data[MetaCache.Attribute] = {MetaCache.AttributeComplete : complete}
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self.mMetatools.busyFinish(media = self.mMedia, item = item)

	def metadataDeveloper(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, item = None):
		if self.mDeveloper:
			data = []

			if not idImdb and item and 'imdb' in item: idImdb = item['imdb']
			if idImdb: data.append('IMDb: ' + idImdb)

			if not idTmdb and item and 'tmdb' in item: idTmdb = item['tmdb']
			if idTmdb: data.append('TMDb: ' + idTmdb)

			if not idImdb and not idTmdb:
				if not idTrakt and item and 'trakt' in item: idTrakt = item['trakt']
				if idTrakt: data.append('Trakt: ' + idTrakt)

			if data: data = ['[%s]' % (' | '.join(data))]
			else: data = ['']

			if not title and item and 'title' in item: title = item['title']
			if not year and item and 'year' in item: year = item['year']

			if title:
				data.append(title)
				if year: data.append('(%d)' % year)

			return ' '.join(data)
		return None

	# requests = [{'id' : required-string, 'function' : required-function, 'parameters' : optional-dictionary}, ...]
	def metadataRetrieve(self, requests):
		def _metadataRetrieve(request, result):
			try:
				if 'parameters' in request: data = request['function'](**request['parameters'])
				else: data = request['function']()
				result[request['id']] = data
			except:
				Logger.error()
				result[request['id']] = None
		result = {}
		if requests:
			threads = []
			for request in requests:
				threads.append(Pool.thread(target = _metadataRetrieve, kwargs = {'request' : request, 'result' : result}, start = True))
			[thread.join() for thread in threads]
		return result

	def metadataRequest(self, link, data = None, headers = None, method = None, cache = False):
		networker = Networker()
		if cache:
			if cache is True: cache = Cache.TimeoutLong
			result = self.mCache.cache(mode = None, timeout = cache, refresh = None, function = networker.request, link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork:
				# Delete the cache, otherwise the next call will return the previously failed request.
				self.mCache.cacheDelete(networker.request, link = link, data = data, headers = headers, method = method)
				return False
		else:
			result = networker.request(link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork: return False
		return Networker.dataJson(result['data'])

	def metadataId(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None):
		result = self.mMetatools.idSet(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
		return {'complete' : True, 'data' : {'id' : result} if result else result}

	def metadataTmdb(self, idImdb = None, idTmdb = None, language = None, item = None, cache = False):
		complete = True
		result = None
		try:
			id = idTmdb if idTmdb else idImdb
			if id:
				def _metadataTmdb(id, mode = None, language = None, cache = True):
					link = 'https://api.themoviedb.org/3/movie/%s%s' % (id, ('/' + mode) if mode else '')
					data = {'api_key' : self.mAccountTmdb}
					if language: data['language'] = language
					return self.metadataRequest(method = Networker.MethodGet, link = link, data = data, cache = cache)

				data = self.metadataRetrieve(requests = [
					{'id' : 'movie', 'function' : _metadataTmdb, 'parameters' : {'id' : id, 'language' : language, 'cache' : cache}},
					{'id' : 'people', 'function' : _metadataTmdb, 'parameters' : {'id' : id, 'mode' : 'credits', 'cache' : cache}},
					{'id' : 'image', 'function' : _metadataTmdb, 'parameters' : {'id' : id, 'mode' : 'images', 'cache' : cache}},
				])

				if data:
					# https://www.themoviedb.org/talk/53c11d4ec3a3684cf4006400
					imageLink = 'https://image.tmdb.org/t/p/w%d%s'
					imageSize = {MetaImage.TypePoster : 780, MetaImage.TypeFanart : 1280, MetaImage.TypeClearlogo : 500, MetaImage.TypePhoto : 185}

					dataMovie = data['movie']
					dataPeople = data['people']
					dataImage = data['image']

					if dataMovie is False or dataPeople is False or dataImage is False: complete = False

					if dataMovie or dataPeople or dataImage:
						result = {}

						if dataMovie and 'title' in dataMovie and 'id' in dataMovie:
							ids = {}
							idTmdb = dataMovie.get('id')
							if idTmdb: ids['tmdb'] = str(idTmdb)
							idImdb = dataMovie.get('imdb_id')
							if idImdb: ids['imdb'] = str(idImdb)
							if ids: result['id'] = ids

							title = dataMovie.get('title')
							if title: result['title'] = Networker.htmlDecode(title)

							originaltitle = dataMovie.get('original_title')
							if originaltitle: result['originaltitle'] = Networker.htmlDecode(originaltitle)

							tagline = dataMovie.get('tagline')
							if tagline: result['tagline'] = Networker.htmlDecode(tagline)

							plot = dataMovie.get('overview')
							if plot: result['plot'] = Networker.htmlDecode(plot)

							premiered = dataMovie.get('release_date')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									result['premiered'] = premiered
									year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
									if year: result['year'] = int(year)

							genre = dataMovie.get('genres')
							if genre: result['genre'] = [i['name'].title() for i in genre]

							rating = dataMovie.get('vote_average')
							if not rating is None: result['rating'] = rating

							votes = dataMovie.get('vote_count')
							if not votes is None: result['votes'] = votes

							duration = dataMovie.get('runtime')
							if not duration is None: result['duration'] = duration * 60

							status = dataMovie.get('status')
							if status: result['status'] = status.title()

							studio = dataMovie.get('production_companies')
							if studio: result['studio'] = [i['name'] for i in studio]

							country = dataMovie.get('production_countries')
							if country: result['country'] = [i['iso_3166_1'].lower() for i in country]

							languages = dataMovie.get('spoken_languages')
							if languages: result['language'] = [i['iso_639_1'].lower() for i in languages]
							languages = dataMovie.get('original_language')
							if languages:
								languages = [languages]
								if 'language' in result: Tools.listUnique(languages + result['language'])
								else: result['language'] = result['language'] = languages

							homepage = dataMovie.get('homepage')
							if homepage: result['homepage'] = homepage

							finance = {}
							budget = dataMovie.get('budget')
							if budget: finance['budget'] = budget
							revenue = dataMovie.get('revenue')
							if revenue: finance['revenue'] = revenue
							if finance:
								if 'budget' in finance and 'revenue' in finance: finance['profit'] = finance['revenue'] - finance['budget']
								result['finance'] = finance

							collectionData = dataMovie.get('belongs_to_collection')
							if collectionData:
								collection = {}
								collectionId = collectionData.get('id')
								if collectionId: collection['id'] = collectionId
								collectionTitle = collectionData.get('name')
								if collectionTitle: collection['title'] = Networker.htmlDecode(collectionTitle)

								if collection:
									collectionImage = {}
									collectionPoster = collectionData.get('poster_path')
									if collectionPoster: collectionImage[MetaImage.TypePoster] = [imageLink % (imageSize[MetaImage.TypePoster], collectionPoster)]
									collectionFanart = collectionData.get('backdrop_path')
									if collectionFanart: collectionImage[MetaImage.TypeFanart] = [imageLink % (imageSize[MetaImage.TypeFanart], collectionFanart)]

									collection[MetaImage.Attribute] = collectionImage
									result['collection'] = collection

									# For Kodi.
									#if collection['id']: result['setid'] = collection['id'] # This seems to be the local DB ID for the set (in the Kodi info dialog there is a special button that redirects to the local library set menu).
									if collection['title']: result['set'] = collection['title']

						try:
							if dataPeople:
								if 'crew' in dataPeople:
									dataCrew = dataPeople['crew']
									if dataCrew:
										def _metadataTmdbPeople(data, department, job):
											people = []
											if data:
												for i in data:
													if 'department' in i and department == i['department'].lower():
														if 'job' in i and i['job'].lower() in job:
															people.append(i['name'])
											return Tools.listUnique(people)

										# https://api.themoviedb.org/3/configuration/jobs?api_key=xxx

										director = _metadataTmdbPeople(data = dataCrew, department = 'directing', job = ['director', 'co-director', 'series director'])
										if director: result['director'] = director

										writer = _metadataTmdbPeople(data = dataCrew, department = 'writing', job = ['writer', 'screenplay', 'author', 'co-writer', 'original film writer', 'original film writer', 'original story', 'story'])
										if writer: result['writer'] = writer

								if 'cast' in dataPeople:
									dataCast = dataPeople['cast']
									if dataCast:
										cast = []
										for i in dataCast:
											if 'character' in i and i['character']: character = i['character']
											else: character = None
											if 'order' in i: order = i['order']
											else: order = None
											if 'profile_path' in i and i['profile_path']: thumbnail = imageLink % (imageSize[MetaImage.TypePhoto], i['profile_path'])
											else: thumbnail = None
											cast.append({'name' : i['name'], 'role' : character, 'order' : order, 'thumbnail' : thumbnail})
										if cast: result['cast'] = cast
						except: Logger.error()

						try:
							if dataImage:
								images = {i : [] for i in MetaImage.Types}
								poster = [[], []]
								keyart = [[], []]
								fanart = [[], []]
								landscape = [[], []]

								entries = (
									('posters', MetaImage.TypePoster),
									('backdrops', MetaImage.TypeFanart),
									('logos', MetaImage.TypeClearlogo),
								)
								for entry in entries:
									try:
										if entry[0] in dataImage:
											indexed = 0
											for i in dataImage[entry[0]]:
												indexed += 1
												index = 99999999 - indexed
												vote = i.get('vote_average')
												vote = float(vote) if vote else 0
												sort = {
													MetaImage.SortIndex : index,
													MetaImage.SortVote : vote,
													MetaImage.SortVoteIndex : [vote, index],
												}
												image = MetaImage.create(link = imageLink % (imageSize[entry[1]], i.get('file_path')), provider = MetaImage.ProviderTmdb, language = i.get('iso_639_1'), sort = sort)
												if entry[1] == MetaImage.TypePoster:
													if image[MetaImage.AttributeLanguage]:
														poster[0].append(image)
														keyart[1].append(image)
													else:
														poster[1].append(image)
														keyart[0].append(image)
												elif entry[1] == MetaImage.TypeFanart:
													if image[MetaImage.AttributeLanguage]:
														landscape[0].append(image)
														fanart[1].append(image)
													else:
														landscape[1].append(image)
														fanart[0].append(image)
												else:
													images[entry[1]].append(image)
									except: Logger.error()

								images[MetaImage.TypePoster] = poster[0] + poster[1]
								images[MetaImage.TypeKeyart] = keyart[0] + keyart[1]
								images[MetaImage.TypeFanart] = fanart[0] + fanart[1]
								images[MetaImage.TypeLandscape] = landscape[0] + landscape[1]

								if images: result[MetaImage.Attribute] = images
						except: Logger.error()
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : complete, 'data' : result}

	##############################################################################
	# NAVIGATION
	##############################################################################

	def check(self, metadatas):
		if Tools.isString(metadatas):
			try: metadatas = Converter.jsonFrom(metadatas)
			except: pass
		if not metadatas:
			Loader.hide()
			Dialog.notification(title = 32001, message = 33049, icon = Dialog.IconInformation)
			return None
		return metadatas

	def menu(self, metadatas, next = True):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			directory = Directory(content = Directory.ContentSettings, media = Media.TypeSet, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.items(metadatas = metadatas, media = self.mMedia, kids = self.mKids, next = next, hide = True, hideSearch = self.mModeSearch, hideRelease = self.mModeRelease, contextPlaylist = True, contextShortcutCreate = True))
			directory.finish(loader = self.mModeSearch) # The loader initiated from search() ios not automatically hidden by Kodi once the menu has loaded. Probably because searching starts a new sub-process and does not load the directory like other menus.

	def directory(self, metadatas):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			directory = Directory(content = Directory.ContentSettings, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.directories(metadatas = metadatas, media = self.mMedia, kids = self.mKids))
			directory.finish()

	def context(self, idImdb = None, idTmdb = None, title = None, year = None):
		metadata = self.metadata(idImdb = idImdb, idTmdb = idTmdb, title = title, year = year)
		return self.mMetatools.context(metadata = metadata, media = self.mMedia, kids = self.mKids, playlist = True, shortcutCreate = True)
