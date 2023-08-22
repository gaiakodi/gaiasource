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

from lib.indexers.movies import Movies

from lib.modules.tools import Logger, Media, Kids, Selection, Settings, Tools, System, Time, Regex, Converter
from lib.modules.interface import Dialog, Loader, Translation, Directory
from lib.modules.network import Networker
from lib.modules.cache import Cache, Memory
from lib.modules.concurrency import Pool, Lock, Semaphore

from lib.meta.cache import MetaCache
from lib.meta.image import MetaImage
from lib.meta.tools import MetaTools
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

		self.mCertificates = None
		self.mRestriction = 0
		if self.mKidsOnly:
			self.mCertificates = []
			self.mRestriction = Settings.getInteger('general.kids.restriction')
			if self.mRestriction >= 0:
				self.mCertificates.append('G')
			if self.mRestriction >= 1:
				self.mCertificates.append('PG')
			if self.mRestriction >= 2:
				self.mCertificates.append('PG-13')
			if self.mRestriction >= 3:
				self.mCertificates.append('R')
			self.mCertificates = '&certificates=' + self.certificatesFormat(self.mCertificates)
		else:
			self.mCertificates = ''

		self.mYear = Time.year()
		self.mLanguage = self.mMetatools.settingsLanguage()

		self.mModeSearch = False

	##############################################################################
	# RETRIEVE
	##############################################################################

	def retrieve(self, link = None, idTmdb = None, title = None, year = None, character = None, detailed = True, menu = True, clean = True, quick = None, refresh = False, next = True):
		try:
			if idTmdb:
				items = self.cache('cacheExtended', refresh, self.tmdbList, id = idTmdb)
				return Movies(kids = self.mKids).retrieve(items = items, detailed = detailed, menu = menu, clean = clean, quick = quick, refresh = refresh)
			else:
				if link:
					if MetaTmdb.LinkSearchSet in link:
						type = 'search'
						parameters = {'link' : link}
					else:
						type = Networker.linkClean(link, parametersStrip = True, headersStrip = True)
						parameters = Networker.linkParameters(link = link)
				else:
					type = 'browse'
					parameters = {}
				if character and not 'character' in parameters: parameters['character'] = character
				if not 'page' in parameters: parameters['page'] = 1
				if not 'limit' in parameters: parameters['limit'] = self.mLimit
				link = Networker.linkCreate(link = type, parameters = parameters)

				if type == 'search':
					self.mModeSearch = True
					items = self.cache('cacheMedium', refresh, self.tmdbSearch, query = parameters.get('query'), link = parameters.get('link'))
				else:
					items = self.cache('cacheExtended', refresh, self.tmdbList)

				sort = None
				reverse = False
				character = None
				strict = False
				if type == 'arrivals':
					sort = 'tmdb'
					reverse = True
					strict = True
				elif type == 'alphabetic':
					#sort = 'title' # Do not sort, keep original order.
					if character is None: character = parameters['character'] if 'character' in parameters else False
				elif type == 'random':
					sort = False
					strict = True

				items = self.tmdbFilter(items = items, sort = sort, reverse = reverse, character = character)

				items = self.page(link = link, items = items, strict = strict)
				if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
				return self.process(items = items, menu = menu, refresh = refresh, next = next)
		except: Logger.error()

	# kids: Filter by age restriction.
	# search: Wether or not the items are from search results.
	# duplicate: Filter out duplicates.
	# release: Filter out unreleased items. If True, return any items released before today. If date-string,return items before the date. If integer, return items older than the given number of days.
	# limit: Limit the number of items. If True, use the setting's limit. If integer, limit up to the given number.
	def process(self, items, menu = True, kids = True, search = False, duplicate = True, release = False, limit = False, refresh = False, next = True):
		if items:
			if duplicate: items = self.mMetatools.filterDuplicate(items = items)

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
					self.menu(items, next = next)

		if not items:
			Loader.hide()
			if menu: Dialog.notification(title = 32010 if search else 32001, message = 33049, icon = Dialog.IconInformation)
		return items

	def cache(self, cache_, refresh_, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cacheClear' if refresh_ else cache_, *args, **kwargs)

	##############################################################################
	# PAGE
	##############################################################################

	# strict: filter out sets that have missing metadata.
	def page(self, link, items, limit = None, sort = None, strict = False, maximum = None):
		# Some Trakt API endpoint do not support pagination.
		# If the user has many watched shows, these list can get very long, making menu loading slow while extended metadata is retrieved.
		# Manually handle paging.

		offset = None
		page = 1
		if limit is None: limit = self.mLimit
		parameters = Networker.linkParameters(link = link)
		if 'limit' in parameters and 'page' in parameters: page = int(parameters['page'])
		if 'offset' in parameters: offset = int(parameters['offset'])

		start = ((page - 1) * limit) if offset is None else offset
		end = start + limit

		# There are many porn collections, especially newer ones.
		itemsDone = []
		stopped = False
		for i in range(10): # 5 is too little for Arrivals menu.
			step = (i * limit)
			offset = end + step
			try: itemsChunk = items[start + step : end + step]
			except: itemsChunk = None
			if not itemsChunk:
				stopped = True
				break

			itemsChunk = self.metadata(items = itemsChunk, clean = False)
			if itemsChunk:
				if strict:
					for item in itemsChunk:
						if 'plot' in item and item['plot'] and 'rating' in item and item['rating']:
							if MetaImage.Attribute in item and item[MetaImage.Attribute]:
								image = False
								for value in item[MetaImage.Attribute].values():
									if len(value) > 0:
										image = True
										break
								if image: itemsDone.append(item)
				else:
					itemsDone.extend(itemsChunk)

				if len(itemsDone) >= limit:
					stopped = True
					break
		items = itemsDone

		if len(items) > limit: offset -= len(items) - limit
		items = items[:limit]

		# Sort first, since we want to page in accordance to the user's preferred sorting.
		if sort: items = self.sort(items = items, type = sort)

		parameters['page'] = page + 1
		parameters['limit'] = limit
		parameters['offset'] = offset

		if (len(items) >= limit or not stopped) and (not maximum or (page + 1) * limit <= maximum):
			next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')
			for item in items: item['next'] = next

		for item in items:
			if 'nextFixed' in item: item['next'] = item['nextFixed']

		return items

	##############################################################################
	# SORT
	##############################################################################

	def sort(self, items, type = None, force = False):
		try:
			attribute = None
			reverse = None

			if type == 'best':
				type = None
				force = True
				attribute = 3
				reverse = True
			elif type == 'worst':
				type = None
				force = True
				attribute = 3
				reverse = False
			elif type == 'release':
				type = None
				force = True
				attribute = 5
				reverse = True
			elif type == 'internal':
				type = None
				force = True
				attribute = 999
				reverse = True

			if force or Settings.getBoolean('navigation.sort'):
				dummyString = 'zzzzzzzzzz'

				attribute = Settings.getInteger('navigation.sort.%s.type' % (type if type else Media.TypeSet)) if attribute is None else attribute
				reverse = Settings.getInteger('navigation.sort.%s.order' % (type if type else Media.TypeSet)) == 1 if (reverse is None and not attribute == 1) else reverse
				if type == 'quick':
					if attribute == 1:
						attribute = 999
						reverse = True
					elif attribute == 8:
						reverse = True

				if attribute == 0:
					items = Tools.listShuffle(items)
				elif attribute > 1:
					if attribute == 2:
						if Settings.getBoolean('navigation.sort.article'):
							items = sorted(items, key = lambda k : Regex.remove(data = (k.get('title') or '').lower(), expression = '(^the\s|^an?\s)', group = 1) or dummyString, reverse = reverse)
						else:
							items = sorted(items, key = lambda k : (k.get('title') or '').lower() or dummyString, reverse = reverse)
					elif attribute == 3:
						items = sorted(items, key = lambda k : float(k.get('rating') or 0.0), reverse = reverse)
					elif attribute == 4:
						items = sorted(items, key = lambda k : int(k.get('votes') or 0), reverse = reverse)
					elif attribute == 5:
						items = sorted(items, key = lambda k : k.get('premiered') or dummyString, reverse = reverse)
					elif attribute == 6:
						items = sorted(items, key = lambda k : k.get('timeAdded') or 0, reverse = reverse)
					elif attribute == 7:
						items = sorted(items, key = lambda k : k.get('timeWatched') or 0, reverse = reverse)
					elif attribute == 8:
						items = sorted(items, key = lambda k : k.get('sort') or 0, reverse = reverse)
					elif attribute == 999:
						items = sorted(items, key = lambda k : k.get('sort') or 0, reverse = reverse)
				elif reverse:
					items.reverse()

		except: Logger.error()
		return items

	##############################################################################
	# ALPHABETIC
	##############################################################################

	def alphabetic(self, menu = True):
		items = []
		characters = list(map(chr, range(ord('a'), ord('z') + 1)))
		for character in characters:
			items.append({'name': character.upper(), 'action': 'setsRetrieve', 'link': 'alphabetic?character=' + character, 'image': 'alphabet.png'})
		items.append({'name': Translation.string(35149), 'action': 'setsRetrieve', 'link': 'alphabetic', 'image': 'alphabet.png'})
		if menu: self.directory(items)
		return items

	##############################################################################
	# SEARCH
	##############################################################################

	# direct = True: when searching from TmdbHelper (although TmdbHelper cannot search sets atm).
	def search(self, query = None, direct = False):
		try:
			from lib.modules.search import Search

			queryHas = query
			if not query: query = Dialog.input(title = 32010)
			if not query: return None

			Loader.show()
			if queryHas and not direct: Search().updateSet(query)
			else: Search().insertSet(query, self.mKids)

			# Use executeContainer() instead of directly calling retrieve().
			# This is important for shows. Otherwise if you open the season menu of a searched show and go back to the previous menu, the search dialog pops up again.
			link = 'search?' + Networker.linkEncode({'query' : query, 'limit' : self.mMetatools.settingsPageSearch()}, plus = True)

			if direct: return self.retrieve(link = link)
			else:  System.executeContainer(action = 'setsRetrieve', parameters = {'link' : link, 'media' : self.mMedia, 'kids' : self.mKids})
		except:
			Logger.error()
			return None

	##############################################################################
	# TMDB
	##############################################################################

	def tmdbList(self, id = None):
		result = []

		if id is None:
			items = MetaTmdb.sets()
			if items: result = [{'tmdb' : item['id'], 'title' : item['name'], 'sort' : Converter.unicodeNormalize(item['name']).lower()} for item in items]
		else:
			items = MetaTmdb.set(id = id, language = self.mLanguage)
			if items and 'parts' in items:
				for part in items['parts']:
					item = {'tmdb' : part['id'], 'title' : part['title']}

					premiered = part.get('release_date')
					if premiered:
						premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
						if premiered:
							item['premiered'] = premiered
							year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
							if year: item['year'] = int(year)

					result.append(item)

				# In most cases the movies in a set are correctly sorted by release date.
				# However, there are a few sets (eg: Start Wars) were a movie might not have been corretly inserted by date.
				result = Tools.listSort(data = result, key = lambda i : i['premiered'] or 'zzzzzzzzzz')
		return result

	def tmdbSearch(self, query = None, link = None):
		return MetaTmdb.searchSet(query = query, link = link, language = self.mLanguage)

	def tmdbFilter(self, items, sort = None, reverse = False, character = None):
		if items:
			if sort: items = Tools.listSort(data = items, key = lambda i : i['sort' if sort == 'title' else sort], reverse = reverse)
			elif sort is False: items = Tools.listShuffle(items)
			elif reverse: items.reverse()

			if not character is None:
				if Tools.isString(character): items = [i for i in items if i['title'].lower().startswith(character)]
				else: items = [i for i in items if not i['title'][0].isalpha()]

		return items

	##############################################################################
	# METADATA
	##############################################################################

	# Either pass in a list of items to retrieve the detailed metadata for all of them.
	# Or pass in an ID or title/year to get the details of a single item.
	# filter: remove uncommon movies, like those without an IMDb ID. If None, will set to True for multiple items, and to False for a single item.
	# By default, do not cache internal requests (eg: Trakt/TMDb/IMDb/Fanart API requests).
	# For a list of 50 items, this will use an additional 5MB of the cache (disc space), plus it takes 100-200 ms longer to write to disc (although this is insignificant, since the entire list takes 20-25 secs).
	# There is no real reason to cache intermediary reque7sts, since the final processed metadata is already cached with MetaCache.
	# The only reason for intermediary caching is if the metadata is imcomplete, and on subsequent menu loading, all of the movie's metadata is requested again, even though some of them might have suceeded previously.
	# quick = Quickly retrieve items from cache without holding up the process of retrieving detailed metadata in the foreground. This is useful if only a few random items are needed from the list and not all of them.
	# quick = positive integer (retrieve the given number of items in the foreground and the rest in the background), negative integer (retrieve the given number of items in the foreground and do not retrieve the rest at all), True (retrieve whatever is in the cache and the rest in the background - could return no items at all), False (retrieve whatever is in the cache and the rest not at all - could return no items at all).
	# threaded = If sub-function calls should use threads or not. None: threaded for single item, non-threaded for multiple items. True: threaded. False: non-threaded.
	def metadata(self, idTmdb = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None):
		try:
			single = False
			if items or idTmdb or (title and year):
				if items:
					if not Tools.isArray(items):
						single = True
						items = [items]
				else:
					single = True
					items = [{'tmdb' : idTmdb, 'title' : title, 'year' : year}]
				if filter is None: filter = not single

				lock = Lock()
				locks = {}
				semaphore = Semaphore(self.mMetatools.concurrency(media = self.mMedia))
				metacache = MetaCache.instance()
				items = metacache.select(type = MetaCache.TypeSet, items = items)

				if threaded is None: threaded = len(items) == 1
				threadsSingle = len(items) == 1

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
							if threadsSingle: self.metadataUpdate(item = item, result = metadataForeground, lock = lock, locks = locks, semaphore = semaphore, filter = filter, cache = cache, threaded = threaded, mode = 'foreground')
							else: threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'foreground'}, start = True))
						elif refreshing == MetaCache.RefreshBackground:
							if not self.mMetatools.busyStart(media = self.mMedia, item = item):
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'background'})
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
								if threadsSingle: self.metadataUpdate(item = item, result = metadataForeground, lock = lock, locks = locks, semaphore = semaphore, filter = filter, cache = cache, threaded = threaded, mode = 'foreground')
								else: threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'foreground'}, start = True))
							elif background and not self.mMetatools.busyStart(media = self.mMedia, item = item): # Still add foreground requests to the background threads if the value of "quick" forbids foreground retrieval.
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'background'})
						elif refreshing == MetaCache.RefreshBackground or (counter is None or len(lookup) >= counter):
							if background and not self.mMetatools.busyStart(media = self.mMedia, item = item):
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'background'})
					items = lookup

				# Wait for metadata that does not exist in the metacache.
				[thread.join() for thread in threadsForeground]
				if metadataForeground: metacache.insert(type = MetaCache.TypeSet, items = metadataForeground)

				# Let the refresh of old metadata run in the background for the next menu load.
				# Only start the threads here, so that background threads do not interfere or slow down the foreground threads.
				if threadsBackground:
					def _metadataBackground():
						if len(threadsBackground) == 1:
							semaphore.acquire()
							self.metadataUpdate(**threadsBackground[0])
						else:
							for i in range(len(threadsBackground)):
								semaphore.acquire()
								threadsBackground[i] = Pool.thread(target = self.metadataUpdate, kwargs = threadsBackground[i], start = True)
							[thread.join() for thread in threadsBackground]
						if metadataBackground: metacache.insert(type = MetaCache.TypeSet, items = metadataBackground)

					# Make a deep copy of the items, since the items can be edited below while these threads are still busy, and we do not want to store the extra details in the database.
					for i in threadsBackground: i['item'] = Tools.copy(i['item'])
					Pool.thread(target = _metadataBackground, start = True)

				if filter: items = [i for i in items if ('tmdb' in i and i['tmdb']) and (not 'adult' in i or not i['adult'])]

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

	def metadataUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, filter = None, cache = False, threaded = None, mode = None):
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
			if filter and not idTmdb: return False

			developer = self.metadataDeveloper(idImdb = idImdb, idTmdb = idTmdb, idTrakt = idTrakt, title = title, year = year, item = item)
			if developer: Logger.log('SET METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			if self.mDetail == MetaTools.DetailEssential:
				requests = [
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
				]
			elif self.mDetail == MetaTools.DetailStandard:
				requests = [
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'fanart', 'function' : self.metadataFanart, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
				]
			elif self.mDetail == MetaTools.DetailExtended:
				requests = [
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'fanart', 'function' : self.metadataFanart, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
				]
			else:
				requests = []

			datas = self.metadataRetrieve(requests = requests, threaded = threaded)

			data = {}
			images = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'user' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			# Keep a specific order. Later values replace newer values.
			for i in ['fanart', 'tmdb']:
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

			if images: MetaImage.update(media = MetaImage.MediaSet, images = images, data = data)

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
	def metadataRetrieve(self, requests, threaded = None):
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
			if threaded is None: threaded = len(requests) > 1
			if threaded:
				threads = []
				for request in requests:
					threads.append(Pool.thread(target = _metadataRetrieve, kwargs = {'request' : request, 'result' : result}, start = True))
				[thread.join() for thread in threads]
			else:
				for request in requests:
					_metadataRetrieve(request = request, result = result)
		return result

	def metadataRequest(self, function = None, cache = False, *args, **kwargs):
		if cache:
			if cache is True: cache = Cache.TimeoutLong
			result = self.mCache.cache(mode = None, timeout = cache, refresh = None, function = function, *args, **kwargs)
			if not result:
				# Delete the cache, otherwise the next call will return the previously failed request.
				self.mCache.cacheDelete(function)
				return False
		else:
			result = function(*args, **kwargs)
			if not result: return False
		return result

	def metadataId(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None):
		result = self.mMetatools.idSet(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
		return {'complete' : True, 'data' : {'id' : result} if result else result}

	def metadataTmdb(self, idImdb = None, idTmdb = None, language = None, item = None, cache = False, threaded = None):
		complete = True
		result = None
		try:
			if idTmdb:
				requests = [
					{'id' : 'set', 'function' :  self.metadataRequest, 'parameters' : {'function' : MetaTmdb.set, 'id' : idTmdb, 'language' : language, 'cache' : cache}},
					{'id' : 'image', 'function' :  self.metadataRequest, 'parameters' : {'function' : MetaTmdb.setImages, 'id' : idTmdb, 'cache' : cache}},
					{'id' : 'genre', 'function' :  self.metadataRequest, 'parameters' : {'function' : MetaTmdb.generesMovie, 'language' : language, 'cache' : cache}},
				]
				data = self.metadataRetrieve(requests = requests, threaded = threaded)

				if data:
					# https://www.themoviedb.org/talk/53c11d4ec3a3684cf4006400
					imageLink = 'https://image.tmdb.org/t/p/w%d%s'
					imageSize = {MetaImage.TypePoster : 780, MetaImage.TypeFanart : 1280, MetaImage.TypeClearlogo : 500, MetaImage.TypePhoto : 185}

					dataSet = data['set']
					dataImage = data['image']
					dataGenre = data['genre']
					dataParts = dataSet['parts'] if dataSet and 'parts' in dataSet else None

					if dataSet is False or dataImage is False or dataGenre is False or not dataParts: complete = False

					result = {}
					if 'name' in dataSet and 'id' in dataSet:
						ids = {}
						idTmdb = dataSet.get('id')
						if idTmdb: ids['tmdb'] = str(idTmdb)
						if ids: result['id'] = ids

						title = dataSet.get('name')
						if title: result['title'] = result['set'] = Regex.remove(data = Networker.htmlDecode(title), expression = '(?:\s*-\s*)?(?:\s*movie\s*)?(?:\s*[\[\(\{])?\s*((?:d(?:i|uo|ou)|tr[iy]|(?:quadr[iao]|tetr[ao])|penta|hex[ao]|hept[ao]|oct[ao]|enn?e[ao]|dec[ao]|antho)log(?:(?:i|í)[ae]?|y)s?|coll?ecti(?:on|e)s?|sagas?|set|colecci(?:o|ó)n|cole(?:c|ç)(?:a|ã)o|collezione|kollektion(?:en)?|seri|sammlung|(?:film)?reihe|komplett|verzameling|samling|kolekcja|kolekce|koleksiyonu|трилогия|коллекция|полный)(?:\s*[\]\)\}])?$', all = True)

						plot = dataSet.get('overview')
						if plot: result['plot'] = result['setoverview'] = Networker.htmlDecode(plot)

						values = []
						for part in dataParts:
							premiered = part.get('release_date')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered: values.append(premiered)
						if values:
							premiered = min(values, key = lambda i : Time.integer(i))
							if premiered:
								result['premiered'] = premiered
								year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
								if year: result['year'] = int(year)

						if dataGenre:
							values = []
							for part in dataParts:
								value = part.get('genre_ids')
								if not value is None: values.extend(value)
							if values: result['genre'] = [dataGenre[i].title() for i in Tools.listUnique(values) if i in dataGenre]

						rating = None
						values = []
						for part in dataParts:
							value = part.get('vote_average')
							if not value is None: values.append(value)
						if values: rating = values

						votes = None
						values = []
						for part in dataParts:
							value = part.get('vote_count')
							if not value is None: values.append(value)
						if values: votes = values

						voting = self.mMetatools.voting(metadata = {'voting' : {'rating' : {'tmdb' : rating}, 'votes' : {'tmdb' : votes}}})
						if voting:
							result['rating'] = voting['rating']
							result['votes'] = max(votes)  if votes else 0

						values = []
						for part in dataParts:
							value = part.get('original_language')
							if value: values.append(value)
						if values: result['language'] = values

						adult = False
						for part in dataParts:
							if part.get('adult'):
								adult = True
								break
						result['adult'] = adult

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

	def metadataFanart(self, idImdb = None, idTmdb = None, language = None, item = None, cache = False, threaded = None):
		complete = True
		result = None
		try:
			if idImdb or idTmdb:
				images = MetaFanart.movie(idImdb = idImdb, idTmdb = idTmdb, cache = cache)
				if images is False: complete = False
				elif images: result = {MetaImage.Attribute : images}
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result}

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
			directory.addItems(items = self.mMetatools.items(metadatas = metadatas, media = self.mMedia, kids = self.mKids, next = next, hide = True, hideSearch = self.mModeSearch, contextPlaylist = True, contextShortcutCreate = True))
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
