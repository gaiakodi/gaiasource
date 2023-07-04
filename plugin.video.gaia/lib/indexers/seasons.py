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

from lib.indexers.shows import Shows

from lib.modules.tools import Logger, Regex, Tools, System, Time, Media, Selection, Language, Converter
from lib.modules.interface import Directory, Dialog, Loader, Translation
from lib.modules.cache import Cache, Memory
from lib.modules.network import Networker
from lib.modules.clean import Title
from lib.modules.account import Trakt, Tmdb
from lib.modules.concurrency import Pool, Lock, Semaphore

from lib.meta.data import MetaData
from lib.meta.cache import MetaCache
from lib.meta.image import MetaImage
from lib.meta.tools import MetaTools
from lib.meta.manager import MetaManager
from lib.meta.processors.fanart import MetaFanart

class Seasons(object):

	def __init__(self, media = Media.TypeSeason, kids = Selection.TypeUndefined):
		self.mMetatools = MetaTools.instance()
		self.mCache = Cache.instance()

		self.mDeveloper = System.developerVersion()
		self.mDetail = self.mMetatools.settingsDetail()
		self.mLimit = self.mMetatools.settingsPageShow()

		self.mMedia = media
		self.mKids = kids
		self.mKidsOnly = self.mMetatools.kidsOnly(kids = self.mKids)

		self.mYear = Time.year()
		self.mLanguage = self.mMetatools.settingsLanguage()

		self.mAccountTrakt = Trakt().dataUsername()
		self.mAccountTmdb = Tmdb().key()

		self.traktwatchlist_link = 'https://api.trakt.tv/users/me/watchlist/seasons?limit=%d&page=1' % self.mLimit
		self.traktlist_link = 'https://api.trakt.tv/users/%s/lists/%s/items?limit=%d&page=1' % ('%s', '%s', self.mLimit)
		self.traktlists_link = 'https://api.trakt.tv/users/me/lists'
		self.traktlikedlists_link = 'https://api.trakt.tv/users/likes/lists?limit=10000'

	##############################################################################
	# RETRIEVE
	##############################################################################

	def retrieve(self, link = None, idImdb = None, idTvdb = None, title = None, year = None, menu = True, clean = True, quick = None, refresh = False, next = True):
		try:
			items = []
			if link:
				items = Shows(kids = self.mKids).retrieve(link = link, menu = False, quick = quick, refresh = refresh)
			else:
				items = self.metadata(idImdb = idImdb, idTvdb = idTvdb, title = title, year = year, quick = quick, refresh = refresh)

				if self.mMetatools.settingsShowSeries():
					show = Shows(kids = self.mKids).metadata(idImdb = idImdb, idTvdb = idTvdb, title = title, year = year, quick = quick, refresh = refresh)
					if show: items.insert(0, show)
		except: Logger.error()

		return self.process(items = items, menu = menu, refresh = refresh, next = next)

	# kids: Filter by age restriction.
	# search: Wether or not the items are from search results.
	# duplicate: Filter out duplicates.
	# release: Filter out unreleased items. If True, return any items released before 3 hours. If date-string,return items before the date. If integer, return items older than the given number of hours.
	# limit: Limit the number of items. If True, use the setting's limit. If integer, limit up to the given number.
	def process(self, items, menu = True, kids = True, search = False, duplicate = False, release = False, limit = False, refresh = False, next = True):
		if items:
			if duplicate: items = self.mMetatools.filterDuplicate(items = items)

			if kids: items = self.mMetatools.filterKids(items = items, kids = self.mKids)

			if release:
				date = None
				hours = None
				if release is True: hours = 3
				elif Tools.isInteger(release) and release < 10000: hours = release
				elif release: date = release
				items = self.mMetatools.filterRelease(items = items, date = date, hours = hours)

			if limit: items = self.mMetatools.filterLimit(items = items, limit = self.mLimit if limit is True else limit)

			if items and menu:
				if refresh: # Check Context commandMetadataList() for more info.
					Loader.hide()
					Directory.refresh()
				else:
					self.menu(items, next = next)

		if not items:
			Loader.hide()
			if menu: Dialog.notification(title = 32010 if search else 32054, message = 33049, icon = Dialog.IconInformation)
		return items

	def cache(self, cache_, refresh_, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cacheClear' if refresh_ else cache_, *args, **kwargs)

	##############################################################################
	# LIST
	##############################################################################

	def listUser(self, mode = None, watchlist = False):
		shows = Shows(kids = self.mKids)

		items = []
		userlists = []

		if not mode is None: mode = mode.lower().strip()
		enabledTrakt = (mode is None or mode == 'trakt') and self.mAccountTrakt

		if enabledTrakt:
			try:
				lists = Cache.instance().cacheRefreshShort(shows.traktListUser, self.traktlists_link, self.mAccountTrakt)
				for i in range(len(lists)): lists[i]['image'] = 'traktlists.png'
				userlists += lists
			except: pass
			try:
				lists = Cache.instance().cacheRefreshShort(shows.traktListUser, self.traktlikedlists_link, self.mAccountTrakt)
				for i in range(len(lists)): lists[i]['image'] = 'traktlists.png'
				userlists += lists
			except: pass

		# Filter the user's own lists that were
		for i in range(len(userlists)):
			contains = False
			adapted = userlists[i]['link'].replace('/me/', '/%s/' % self.mAccountTrakt)
			for j in range(len(items)):
				if adapted == items[j]['link'].replace('/me/', '/%s/' % self.mAccountTrakt):
					contains = True
					break
			if not contains:
				items.append(userlists[i])

		for i in range(len(items)):items[i]['action'] = 'seasonsRetrieve'

		# Watchlist
		if watchlist:
			if enabledTrakt: items.insert(0, {'name' : Translation.string(32033), 'link' : self.traktwatchlist_link, 'image' : 'traktwatch.png', 'action' : 'seasonsRetrieve'})

		shows.directory(items)
		return items

	##############################################################################
	# METADATA
	##############################################################################

	# By default, do not cache internal requests (eg: Trakt/TVDb/IMDb/Fanart API requests).
	# For a list of 50 items, this will use an additional 8-9MB of the cache (disc space), plus it takes 4 secs longer to write to disc (the entire list takes 17-25 secs).
	# There is no real reason to cache intermediary requests, since the final processed metadata is already cached with MetaCache.
	# The only reason for intermediary caching is if the metadata is imcomplete, and on subsequent menu loading, all of the show's metadata is requested again, even though some of them might have suceeded previously.
	# quick = Quickly retrieve items from cache without holding up the process of retrieving detailed metadata in the foreground. This is useful if only a few random items are needed from the list and not all of them.
	# quick = positive integer (retrieve the given number of items in the foreground and the rest in the background), negative integer (retrieve the given number of items in the foreground and do not retrieve the rest at all), True (retrieve whatever is in the cache and the rest in the background - could return no items at all), False (retrieve whatever is in the cache and the rest not at all - could return no items at all).
	# threaded = If sub-function calls should use threads or not. None: threaded for single item, non-threaded for multiple items. True: threaded. False: non-threaded.
	def metadata(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, season = None, items = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None):
		try:
			single = False

			if items or (idImdb or idTvdb) or (title and year):
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
				semaphore = Semaphore(self.mMetatools.concurrency(media = self.mMedia))
				metacache = MetaCache.instance()
				items = metacache.select(type = MetaCache.TypeSeason, items = items)

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
				if metadataForeground: metacache.insert(type = MetaCache.TypeSeason, items = metadataForeground)

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
						if metadataBackground: metacache.insert(type = MetaCache.TypeSeason, items = metadataBackground)

					# Make a deep copy of the items, since the items can be edited below (added pack and seasonNext/seasonPrevious/seasonCurrent) while these threads are still busy, and we do not want to store the extra details in the database.
					for i in threadsBackground: i['item'] = Tools.copy(i['item'])
					Pool.thread(target = _metadataBackground, start = True)

				if filter: items = [i for i in items if 'tvdb' in i and i['tvdb']]

			# Remove temporary, useless, or already aggregatd data, to keep the size of the data passed arround small.
			if clean:
				for item in items:
					try: del item['temp']
					except: pass
					try: del item[MetaCache.Attribute]
					except: pass

			# Add detailed show metadata.
			self.metadataAggregate(items = items, threaded = threaded)

			if single:
				if items:
					result = items[0]['seasons']
					if season is None: return result
					for i in result:
						if i['season'] == season: return i
				return None
			elif items and 'season' in items[0] and not items[0]['season'] is None:
				# Use to select a single season for different shows from navigator -> History -> Seasons.
				result = []
				for item in items:
					for i in item['seasons']:
						if i['season'] == item['season']:
							result.append(i)
							break
				return result
			else:
				return [item['seasons'] for item in items]
		except: Logger.error()
		return None

	def metadataUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, filter = None, cache = False, threaded = None, mode = None):
		try:
			id = None
			complete = True

			idImdb = str(item['imdb']) if item and 'imdb' in item and item['imdb'] else None
			idTmdb = str(item['tmdb']) if item and 'tmdb' in item and item['tmdb'] else None
			idTvdb = str(item['tvdb']) if item and 'tvdb' in item and item['tvdb'] else None
			idTvmaze = str(item['tvmaze']) if item and 'tvmaze' in item and item['tvmaze'] else None
			idTvrage = str(item['tvrage']) if item and 'tvrage' in item and item['tvrage'] else None
			idTrakt = str(item['trakt']) if item and 'trakt' in item and item['trakt'] else None
			idSlug = str(item['slug']) if item and 'slug' in item and item['slug'] else None

			title = item['tvshowtitle'] if item and 'tvshowtitle' in item and item['tvshowtitle'] else item['title'] if item and 'title' in item and item['title'] else None
			year = item['year'] if item and 'year' in item and item['year'] else None

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, idTvmaze = idTvmaze, idTvrage = idTvrage, title = title, year = year)
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

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not idTvdb or (not idImdb and not idTrakt) or (not idTmdb and self.mDetail == MetaTools.DetailExtended):
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
							if not idTvmaze and 'tvmaze' in ids: idTvmaze = ids['tvmaze']
							if not idTvrage and 'tvrage' in ids: idTvrage = ids['tvrage']
							if not idTrakt and 'trakt' in ids: idTrakt = ids['trakt']
							if not idSlug and 'slug' in ids: idSlug = ids['slug']
			if filter and not idTvdb: return False

			developer = self.metadataDeveloper(idImdb = idImdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year, item = item)
			if developer: Logger.log('SEASON METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			show = Shows().metadata(idImdb = idImdb, idTvdb = idTvdb, threaded = threaded)
			if not show:
				Memory.set(id = id, value = {}, local = True, kodi = False)
				return False

			try: pack = show['pack']
			except: pack = None

			if not title and show and 'tvshowtitle' in show: title = show['tvshowtitle']

			if self.mDetail == MetaTools.DetailEssential:
				requests = [
					{'id' : 'tvdb', 'function' : self.metadataTvdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
				]
			elif self.mDetail == MetaTools.DetailStandard:
				requests = [
					{'id' : 'tvdb', 'function' : self.metadataTvdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'trakt', 'function' : self.metadataTrakt, 'parameters' : {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'fanart', 'function' : self.metadataFanart, 'parameters' : {'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
				]
			elif self.mDetail == MetaTools.DetailExtended:
				requests = [
					{'id' : 'tvdb', 'function' : self.metadataTvdb, 'parameters' : {'idImdb' : idImdb, 'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'trakt', 'function' : self.metadataTrakt, 'parameters' : {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'fanart', 'function' : self.metadataFanart, 'parameters' : {'idTvdb' : idTvdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
				]
			else:
				requests = []

			datas = self.metadataRetrieve(requests = requests, threaded = threaded)

			data = {'seasons' : []}
			images = {}
			votings = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'user' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}
			for i in ['tvmaze', 'metacritic', 'imdb', 'tmdb', 'fanart', 'trakt', 'tvdb']: # Keep a specific order. Later values replace newer values.
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								complete = False
								if developer: Logger.log('INCOMPLETE SEASON METADATA [%s]: %s' % (i.upper(), developer))
							provider = value['provider']
							value = Tools.copy(value['data']) # Copy, since we do title/plot/studio replacement below in another loop.
							if value:
								for season in value['seasons']:
									number = season['season']

									if MetaImage.Attribute in season:
										if not number in images: images[number] = {}
										images[number] = Tools.update(images[number], season[MetaImage.Attribute], none = True, lists = True, unique = False)
										del season[MetaImage.Attribute]

									if not number in votings: votings[number] = Tools.copy(voting)
									if 'rating' in season: votings[number]['rating'][provider] = season['rating']
									if 'ratinguser' in season: votings[number]['user'][provider] = season['ratinguser']
									if 'votes' in season: votings[number]['votes'][provider] = season['votes']

									found = False
									for j in data['seasons']:
										if j['season'] == number:
											found = True
											Tools.update(j, season, none = True, lists = False, unique = False)
											break
									if not found: data['seasons'].append(season)

			if pack:
				# Copy the additional numbers (eg: season number given as the year) from the pack.
				numbers = {i['number'][MetaData.NumberOfficial] : i['number'] for i in pack['seasons']}
				for i in data['seasons']:
					try: i['number'] = numbers[i['season']]
					except: i['number'] = {MetaData.NumberOfficial : i['season']}

				# Fanart sometimes has images for non-existing seasons.
				# Eg: "How I Met Your Mother" has Fanart posters for Season 89.
				# Remove these seasons.
				numbers = list(numbers.keys())
				numberMaximum = max(numbers) + 10
				data['seasons'] = [i for i in data['seasons'] if i['season'] in numbers or i['season'] <= numberMaximum]

			# Some values are often missing or incorrect on TVDb, and should be replaced with the Trakt/TMDb metadata.
			# TVDb has often incorrect studios/networks for seasons (eg: Game of Thrones and Breaking Bad).
			# TVDb typically does not have a title and plot for seasons. Even if there are plots, it is only available in other languages, except English.
			# TVDb also does not have the cast for seasons. But we do not retrieve the cast from Trakt, since it requires an additional API call per season, and does not have actor thumbnails. Use the show cast from TVDb which has thumbnails.
			for i in ['trakt', 'tmdb']: # Place TMDb last, since it has more transalated season titles than Trakt.
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							value = value['data']
							if value:
								for season in value['seasons']:
									for j in data['seasons']:
										if j['season'] == season['season']:
											for attribute in ['title', 'originaltitle', 'plot', 'studio']:
												if attribute in season and season[attribute]: j[attribute] = season[attribute]
											break

			for i in range(len(data['seasons'])):
				season = data['seasons'][i]
				number = season['season']
				if number in votings: season['voting'] = votings[number]

				data['seasons'][i] = {k : v for k, v in season.items() if not v is None}
				season = data['seasons'][i]

				if 'id' in season and season['id']:
					if not idImdb and 'imdb' in season['id']: idImdb = season['id']['imdb']
					if not idTmdb and 'tmdb' in season['id']: idTmdb = season['id']['tmdb']
					if not idTvdb and 'tvdb' in season['id']: idTvdb = season['id']['tvdb']
					if not idTvmaze and 'tvmaze' in season['id']: idTvmaze = season['id']['tvmaze']
					if not idTvrage and 'tvrage' in season['id']: idTvrage = season['id']['tvrage']
					if not idTrakt and 'trakt' in season['id']: idTrakt = season['id']['trakt']
					if not idSlug and 'slug' in season['id']: idSlug = season['id']['slug']
				if 'id' in show and show['id']:
					if not idImdb and 'imdb' in show['id']: idImdb = show['id']['imdb']
					if not idTmdb and 'tmdb' in show['id']: idTmdb = show['id']['tmdb']
					if not idTvdb and 'tvdb' in show['id']: idTvdb = show['id']['tvdb']
					if not idTvmaze and 'tvmaze' in show['id']: idTvmaze = show['id']['tvmaze']
					if not idTvrage and 'tvrage' in show['id']: idTvrage = show['id']['tvrage']
					if not idTrakt and 'trakt' in show['id']: idTrakt = show['id']['trakt']
					if not idSlug and 'slug' in show['id']: idSlug = show['id']['slug']

				# This is for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
				# At some later point the entire addon should be updated to have the new ID structure.
				if not 'id' in season: season['id'] = {}
				if idImdb: season['id']['imdb'] = season['imdb'] = idImdb
				if idTmdb: season['id']['tmdb'] = season['tmdb'] = idTmdb
				if idTvdb: season['id']['tvdb'] = season['tvdb'] = idTvdb
				if idTvmaze: season['id']['tvmaze'] = season['tvmaze'] = idTvmaze
				if idTvrage: season['id']['tvrage'] = season['tvrage'] = idTvrage
				if idTrakt: season['id']['trakt'] = season['trakt'] = idTrakt
				if idSlug: season['id']['slug'] = season['slug'] = idSlug

				# Trakt sometimes returns new/unaired seasons that are not on TVDb.
				# This unique Trakt season does not have a show title, which will cause the season menu to be classified as "mixed" as the show title is added to the season label.
				if not 'tvshowtitle' in season and title: season['tvshowtitle'] = title

				if number in images and images[number]: MetaImage.update(media = MetaImage.MediaSeason, images = images[number], data = season)

				# Do this before here already.
				# Otherwise a bunch of regular expressions are called every time the menu is loaded.
				self.mMetatools.cleanPlot(metadata = season)

				# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
				# More info under meta -> tools.py -> cleanVoting().
				self.mMetatools.cleanVoting(metadata = season)

			# Sort so that the list is in the order of the season numbers.
			data['seasons'].sort(key = lambda i : i['season'])

			# Set the show details.
			try: season = data['seasons'][1] # Season 1
			except:
				try: season = data['seasons'][0] # Specials
				except: season = None
			if idImdb: data['imdb'] = idImdb
			if idTmdb: data['tmdb'] = idTmdb
			if idTvdb: data['tvdb'] = idTvdb
			if idTvmaze: data['tvmaze'] = idTvmaze
			if idTvrage: data['tvrage'] = idTvrage
			if idTrakt: data['trakt'] = idTrakt
			if idSlug: data['slug'] = idSlug
			title = season['tvshowtitle'] if season and 'tvshowtitle' in season else None
			if title: data['tvshowtitle'] = data['title'] = title
			year = season['year'] if season and 'year' in season else None
			if year: data['year'] = year

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

	def metadataAggregate(self, items, threaded = None):
		# Do not store duplicate or non-season data in the MetaCache database, otherwise too much unnecessary storage space will be used.
		# Check episodes.py -> metadataAggregate() for more info.

		try:
			shows = []
			for item in items:
				try:
					try: idImdb = item['imdb']
					except: idImdb = None
					try: idTvdb = item['tvdb']
					except: idTvdb = None
					shows.append({'imdb' : idImdb, 'tvdb' : idTvdb})
				except: Logger.error()
			shows = Tools.listUnique(shows)
			shows = Shows().metadata(items = shows, threaded = threaded) if shows else None

			for item in items:
				try:
					try: idImdb = item['imdb']
					except: idImdb = None
					try: idTvdb = item['tvdb']
					except: idTvdb = None

					for show in shows:
						if show and MetaImage.Attribute in show:
							if ('imdb' in show and show['imdb'] and show['imdb'] == idImdb) or ('tvdb' in show and show['tvdb'] and show['tvdb'] == show):
								try: pack = show['pack']
								except: pack = None
								if pack:
									for season in item['seasons']:
										season['pack'] = pack

								for season in item['seasons']:
									if (not 'plot' in season or not season['plot']) and ('plot' in show and show['plot']): season['plot'] = show['plot'] # Unaired seasons.
									MetaImage.update(media = MetaImage.MediaShow, images = Tools.copy(show[MetaImage.Attribute]), data = season, category = MetaImage.MediaShow) # Add show images.

								break

				except: Logger.error()
		except: Logger.error()

	def metadataDeveloper(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, item = None):
		if self.mDeveloper:
			data = []

			if not idImdb and item and 'imdb' in item: idImdb = item['imdb']
			if idImdb: data.append('IMDb: ' + idImdb)

			if not idTvdb and item and 'tvdb' in item: idTvdb = item['tvdb']
			if idTvdb: data.append('TVDb: ' + idTvdb)

			if not idImdb and not idTvdb:
				if not idTrakt and item and 'trakt' in item: idTrakt = item['trakt']
				if idTrakt: data.append('Trakt: ' + idTrakt)

			if data: data = ['[%s]' % (' | '.join(data))]
			else: data = ['']

			if not title and item:
				if 'tvshowtitle' in item: title = item['tvshowtitle']
				elif 'title' in item: title = item['title']
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

	def metadataRequest(self, link, data = None, headers = None, method = None, cache = True):
		# HTTP error 429 can be thrown if too many requests were made in a short time.
		# This should only happen with Trakt (which does not call this function), since TMDb/TVDb/Fanart should not have any API limits at the moment.
		# Still check for it, since in special cases 429 might still happen (eg: the TMDb CDN/Cloudflare might block more than 50 concurrent connections).
		# This should not be an issue with normal use, only with batch-generating the preprocessed database that makes 1000s of request every few minutes.

		networker = Networker()
		if cache:
			if cache is True: cache = Cache.TimeoutLong
			result = self.mCache.cache(mode = None, timeout = cache, refresh = None, function = networker.request, link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork or result['error']['code'] == 429:
				# Delete the cache, otherwise the next call will return the previously failed request.
				self.mCache.cacheDelete(networker.request, link = link, data = data, headers = headers, method = method)
				return False
		else:
			result = networker.request(link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork or result['error']['code'] == 429: return False
		return Networker.dataJson(result['data'])

	def metadataId(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None):
		result = self.mMetatools.idShow(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
		return {'complete' : True, 'data' : {'id' : result} if result else result}

	def metadataTrakt(self, idImdb = None, idTrakt = None, language = None, item = None, people = False, cache = False, threaded = None):
		complete = True
		result = None
		try:
			id = idTrakt if idTrakt else idImdb
			if id:
				requests = [{'id' : 'seasons', 'function' : trakt.getTVSeasonSummary, 'parameters' : {'id' : id, 'full' : True, 'cache' : cache, 'failsafe' : True}}]
				data = self.metadataRetrieve(requests = requests, threaded = threaded)
				if data:
					dataSeasons = data['seasons']
					if dataSeasons is False: complete = False

					if dataSeasons:
						numbers = []
						result = {'seasons' : []}

						for dataSeason in dataSeasons:
							if dataSeason and 'title' in dataSeason and 'ids' in dataSeason:
								resultSeason = {}

								number = dataSeason['number']
								resultSeason['season'] = number
								numbers.append(number)

								ids = dataSeason.get('ids')
								if ids:
									ids = {k : str(v) for k, v in ids.items() if v}
									if ids: resultSeason['id'] = {'season' : ids}

								title = dataSeason.get('title')
								if title: resultSeason['title'] = Networker.htmlDecode(title)

								plot = dataSeason.get('overview')
								if plot: resultSeason['plot'] = Networker.htmlDecode(plot)

								premiered = dataSeason.get('first_aired')
								if premiered:
									premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
									if premiered:
										resultSeason['premiered'] = premiered
										resultSeason['aired'] = premiered

								airs = dataSeason.get('aired_episodes')
								if airs:
									if not 'airs' in resultSeason: resultSeason['airs'] = {}
									resultSeason['airs']['episodes'] = airs

								rating = dataSeason.get('rating')
								if not rating is None: resultSeason['rating'] = rating

								votes = dataSeason.get('votes')
								if not votes is None: resultSeason['votes'] = votes

								studio = dataSeason.get('network')
								if studio: resultSeason['studio'] = studio if Tools.isArray(studio) else [studio]

								result['seasons'].append(resultSeason)

						# Retrieving the people and translations requires a separate API call per season.
						requests = []
						translation = language and not language == Language.EnglishCode
						for number in numbers:
							if people: requests.append({'id' : 'people%d' % number, 'function' : trakt.getPeopleShow, 'parameters' : {'id' : id, 'season' : number, 'full' : True, 'cache' : cache, 'failsafe' : True}})
							if translation: requests.append({'id' : 'translation%d' % number, 'function' : trakt.getTVShowTranslation, 'parameters' : {'id' : id, 'season' : number, 'lang' : language, 'full' : True, 'cache' : cache, 'failsafe' : True}})

						if requests:
							data = self.metadataRetrieve(requests = requests, threaded = threaded)
							for number in numbers:
								resultSeason = None
								for i in result['seasons']:
									if i['season'] == number:
										resultSeason = i
										break

								if resultSeason:
									dataPeople = data['people%d' % number] if people else None
									dataTranslation = data['translation%d' % number] if translation else None
									if (people and dataPeople is False) or (translation and dataTranslation is False): complete = False

									if dataTranslation:
										title = dataTranslation.get('title')
										if title:
											if resultSeason['title']: resultSeason['originaltitle'] = resultSeason['title']
											resultSeason['title'] = Networker.htmlDecode(title)

										plot = dataTranslation.get('overview')
										if plot: resultSeason['plot'] = Networker.htmlDecode(plot)

									if dataPeople and ('crew' in dataPeople or 'cast' in dataPeople):
										if 'crew' in dataPeople:
											dataCrew = dataPeople['crew']
											if dataCrew:
												def _metadataTraktPeople(data, job):
													people = []
													if data:
														for i in data:
															if 'jobs' in i:
																jobs = i['jobs']
																if jobs and any(j.lower() in job for j in jobs):
																	people.append(i['person']['name'])
													return Tools.listUnique(people)

												if 'directing' in dataCrew:
													director = _metadataTraktPeople(data = dataCrew['directing'], job = ['director'])
													if director: resultSeason['director'] = director
												if 'writing' in dataCrew:
													writer = _metadataTraktPeople(data = dataCrew['writing'], job = ['writer', 'screenplay', 'author'])
													if writer: resultSeason['writer'] = writer

										if 'cast' in dataPeople:
											dataCast = dataPeople['cast']
											if dataCast:
												cast = []
												order = 0
												for i in dataCast:
													if 'characters' in i and i['characters']: character = ' / '.join(i['characters'])
													else: character = None
													cast.append({'name' : i['person']['name'], 'role' : character, 'order' : order})
													order += 1
												if cast: resultSeason['cast'] = cast
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def metadataTvdb(self, idImdb = None, idTvdb = None, language = None, item = None, cache = False, threaded = None):
		complete = True
		result = None
		try:
			if idTvdb or idImdb:
				manager = MetaManager(provider = MetaManager.ProviderTvdb, threaded = MetaManager.ThreadedDynamic if threaded is False else threaded)
				show = manager.show(idTvdb = idTvdb, idImdb = idImdb, level = MetaManager.Level5, cache = cache)
				if show and show.idTvdb():
					result = {'seasons' : []}

					showId = show.id()
					showIdImdb = show.idImdb()
					showIdTmdb = show.idTmdb()
					showIdTvdb = show.idTvdb()
					showIdTrakt = show.idTrakt()
					showTitle = show.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					showPlot = show.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
					showYear = show.year()
					showPremiered = show.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
					showAirTime = show.releaseTime(zone = MetaData.ZoneOriginal)
					showAirDay = show.releaseDay()
					showAirZone = show.releaseZoneName()
					showGenre = show.genreName()
					showMpaa = show.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
					showDuration = show.durationSeconds()
					showStatus = show.statusLabel()
					showCountry = show.releaseCountry()
					showLanguage = show.languageOriginal()
					showStudio = show.companyNameNetwork()
					showCast = show.personKodiCast()
					showDirector = show.personKodiDirector()
					showWriter = show.personKodiWriter()
					showImage = {
						MetaImage.TypePoster : show.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeThumb : show.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeFanart : show.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeLandscape : show.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeBanner : show.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeClearlogo : show.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeClearart : show.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeDiscart : show.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
						MetaImage.TypeKeyart : show.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
					}

					seasons = show.season(sort = True)
					episodes = show.episode(sort = True)

					for season in seasons:
						try:
							episodesSeason = season.episode()
							try: episodesFirst = episodesSeason[0]
							except: episodesFirst = None
							try: episodesLast = episodesSeason[-1]
							except: episodesLast = None

							resultSeason = {}
							resultSeason['id'] = Tools.copy(showId) # Copy, since we edit it for each season by adding the season IDs.

							resultSeason['season'] = season.numberSeason()

							if showTitle: resultSeason['tvshowtitle'] = showTitle

							title = season.titleSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
							if title: resultSeason['title'] = title

							title = season.titleOriginal(selection = MetaData.SelectionSingle)
							if title:
								resultSeason['originaltitle'] = title
								if not 'title' in resultSeason: resultSeason['title'] = title

							plot = season.overviewSettings(selection = MetaData.SelectionSingle, fallback = MetaData.FallbackSecondary)
							if not plot: plot = showPlot
							if plot: resultSeason['plot'] = plot

							# Always use the show's year, used for search by title-and-year and for adding multiple seasons under the same tvshowtitle-and-year folder in the local library.
							if showYear: resultSeason['year'] = showYear

							premiered = season.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
							if not premiered:
								if episodesFirst: premiered = episodesFirst.releaseDateFirst(zone = MetaData.ZoneOriginal, format = MetaData.FormatDate)
								if not premiered and resultSeason['season'] <= 1: premiered = showPremiered # Do not do this for later seasons, since they might be new/unaired seasons and we do not want to use the years-earlier show premier date.
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									resultSeason['premiered'] = premiered
									resultSeason['aired'] = premiered

							airs = {}
							airTime = season.releaseTime(zone = MetaData.ZoneOriginal)
							if not airTime:
								if episodesFirst: airTime = episodesFirst.releaseTime(zone = MetaData.ZoneOriginal)
								if not airTime: airTime = showAirTime
							if airTime: airs['time'] = airTime
							airDay = season.releaseDay()
							if not airDay:
								if episodesFirst: airDay = episodesFirst.releaseDay()
								if not airDay: airDay = showAirDay
							if airDay: airs['day'] = [i.title() for i in airDay]
							airZone = season.releaseZoneName()
							if not airZone:
								if episodesFirst: airZone = episodesFirst.releaseZoneName()
								if not airZone: airZone = showAirZone
							if airZone: airs['zone'] = airZone
							if airs: resultSeason['airs'] = airs

							genre = season.genreName()
							if not genre:
								genre = showGenre
								if not genre and episodesFirst: genre = episodesFirst.genreName()
							if genre: resultSeason['genre'] = [i.title() for i in genre]

							mpaa = season.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
							if not mpaa:
								mpaa = showMpaa
								if not mpaa and episodesFirst: mpaa = episodesFirst.certificateCode(country = MetaData.CountryOriginal, selection = MetaData.SelectionSingle)
							if mpaa: resultSeason['mpaa'] = mpaa

							duration = season.durationSeconds()
							if duration is None:
								if episodesFirst: duration = episodesFirst.durationSeconds()
								if duration is None: duration = showDuration
							if not duration is None: resultSeason['duration'] = duration

							status = season.statusLabel()
							if not status:
								if episodesLast: status = episodesLast.statusLabel()
								# It does not make sense to have a status for episodes.
								# It only clutters the info dialog with an extra label.
								# And Kodi docs say it is for shows only.
								#if not status: status = showStatus
							if status: resultSeason['status'] = status.title()

							country = season.releaseCountry()
							if not country:
								country = showCountry
								if not country and episodesFirst: country = episodesFirst.releaseCountry()
							if country: resultSeason['country'] = [country]

							language = season.languageOriginal()
							if not language:
								language = showLanguage
								if not language and episodesFirst: language = episodesFirst.languageOriginal()
							if language: resultSeason['language'] = language if Tools.isArray(language) else [language]

							studio = season.companyNameNetwork()
							if not studio:
								studio = showStudio
								if not studio and episodesFirst: studio = episodesFirst.companyNameNetwork()
							if studio: resultSeason['studio'] = studio

							cast = season.personKodiCast()
							if not cast:
								cast = showCast
								if not cast and episodesFirst: cast = episodesFirst.personKodiCast()
							if cast: resultSeason['cast'] = cast

							director = season.personKodiDirector()
							if not director:
								director = showDirector
								if not director and episodesFirst: director = episodesFirst.personKodiDirector()
							if director: resultSeason['director'] = director

							writer = season.personKodiWriter()
							if not writer:
								writer = showWriter
								if not writer and episodesFirst: writer = episodesFirst.personKodiWriter()
							if writer: resultSeason['writer'] = writer

							image = {
								MetaImage.TypePoster : season.imageKodiPoster(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeThumb : season.imageKodiThumb(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeFanart : season.imageKodiFanart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeLandscape : season.imageKodiLandscape(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeBanner : season.imageKodiBanner(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeClearlogo : season.imageKodiClearlogo(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeClearart : season.imageKodiClearart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeDiscart : season.imageKodiDiscart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
								MetaImage.TypeKeyart : season.imageKodiKeyart(language = MetaData.LanguageSpecific, selection = MetaData.SelectionList, fallback = MetaData.FallbackPrimary, sort = MetaData.SortSettings),
							}
							for k, v in image.items(): image[k] = [MetaImage.create(link = i, provider = MetaImage.ProviderTvdb) for i in v] if v else []
							if image: resultSeason[MetaImage.Attribute] = image

							result['seasons'].append(resultSeason)
						except: Logger.error()
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : complete, 'data' : result}

	def metadataTmdb(self, idTmdb = None, language = None, item = None, cache = False, threaded = None):
		complete = True
		result = None
		try:
			if idTmdb:
				def _metadataTmdb(id, mode = None, season = None, language = None, cache = True):
					if not season is None:
						if mode is None: mode = 'season'
						mode += '/%d' % season
					link = 'https://api.themoviedb.org/3/tv/%s%s' % (id, ('/' + mode) if mode else '')
					data = {'api_key' : self.mAccountTmdb}
					if language: data['language'] = language
					return self.metadataRequest(method = Networker.MethodGet, link = link, data = data, cache = cache)

				requests = [
					{'id' : 'show', 'function' : _metadataTmdb, 'parameters' : {'id' : idTmdb, 'language' : language, 'cache' : cache}},
				]
				data = self.metadataRetrieve(requests = requests, threaded = threaded)

				if data:
					dataShow = data['show']
					if dataShow is False: complete = False

					if dataShow and 'name' in dataShow and 'id' in dataShow:
						result = {'seasons' : []}

						numbers = []
						requests = []
						for i in dataShow.get('seasons'):
							if i and 'season_number' in i:
								number = i.get('season_number')
								numbers.append(number)
								requests.append({'id' : 'season%d' % number, 'function' : _metadataTmdb, 'parameters' : {'id' : idTmdb, 'season' : number, 'language' : language, 'cache' : cache}})

						if requests:
							data = self.metadataRetrieve(requests = requests, threaded = threaded)

							for number in numbers:
								dataSeason = data['season%d' % number]
								if dataSeason is False or dataSeason is None: complete = False
								if dataSeason:
									resultSeason = {}
									resultSeason['season'] = dataSeason.get('season_number')

									ids = {}
									idTmdb = dataSeason.get('id')
									if idTmdb: ids['tmdb'] = str(idTmdb)
									if ids: resultSeason['id'] = {'season' : ids}

									title = dataSeason.get('name')
									if title: resultSeason['title'] = Networker.htmlDecode(title)

									plot = dataSeason.get('overview')
									if plot: resultSeason['plot'] = Networker.htmlDecode(plot)

									premiered = dataSeason.get('air_date')
									if premiered:
										premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
										if premiered:
											resultSeason['premiered'] = premiered
											resultSeason['aired'] = premiered

									# TMDb does not have ratings for seasons, only for shows and episodes.
									# Calculate the average vote over al episodes in the season.
									# Limit the vote count to the maximum of the episodes, assuming that the same people vote for different episodes.
									rating = []
									votes = []
									episodes = dataSeason.get('episodes')
									if episodes:
										for episode in episodes:
											if episode:
												ratingEpisode = episode.get('vote_average')
												if not ratingEpisode is None: rating.append(ratingEpisode)

												votesEpisode = episode.get('vote_count')
												if not votesEpisode is None: votes.append(votesEpisode)
									if rating: resultSeason['rating'] = sum(rating) / float(len(rating))
									if votes: resultSeason['votes'] = max(votes)

									if resultSeason: result['seasons'].append(resultSeason)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : complete, 'data' : result}

	def metadataFanart(self, idTvdb = None, language = None, item = None, cache = False, threaded = None):
		complete = True
		result = None
		try:
			if idTvdb:
				images = MetaFanart.show(idTvdb = idTvdb, season = True, cache = cache)
				if images is False: complete = False
				elif images:
					result = {'seasons' : []}
					for season, data in images.items():
						result['seasons'].append({'season' : season, MetaImage.Attribute : data})
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
			Dialog.notification(title = 32054, message = 33049, icon = Dialog.IconInformation)
			return None
		return metadatas

	def menu(self, metadatas, next = True):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			directory = Directory(content = Directory.ContentSettings, media = Media.TypeSeason, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.items(metadatas = metadatas, media = self.mMedia, kids = self.mKids, contextPlaylist = False, contextShortcutCreate = True))
			directory.finish()

	def context(self, idImdb = None, idTvdb = None, title = None, year = None, season = None):
		metadata = self.metadata(idImdb = idImdb, idTvdb = idTvdb, title = title, year = year, season = season)
		return self.mMetatools.context(metadata = metadata, media = self.mMedia, kids = self.mKids, playlist = False, shortcutCreate = True)

	def extras(self, metadata):
		directory = Directory(content = Directory.ContentSettings, media = Media.TypeEpisode, cache = True, lock = False)
		directory.addItems(items = self.mMetatools.itemsExtra(metadata = metadata, kids = self.mKids))
		directory.finish()
