# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from lib.modules.tools import Tools, Logger, Country, Language
from lib.modules.concurrency import Pool, Lock, Semaphore
from lib.modules.cache import Cache
from lib.modules.network import Networker
from lib.meta.data import MetaData

'''
	In future extensions when TMDb/Trakt/IMDb is added:
		1. Make the "season" function callable by season ID/query/year or by show ID/query/year.
		2. Make the "episode" function callable by episode ID/query/year or by season ID/query/year or by show ID/query/year.
		3. Trakt and IMDb seem to require the show ID + season/episode number, instead of using separate season/episode IDs.
		4. That means each function should get additional parameters for the above.
		5. Also put the implementation of this in the subclasses, instead of abstracting everything in the parent class. Would make things easier to code, since every provider is very different on its parameter requirnments.
		6. Update "CacheParameters"
		7. Maybe also do this with the id(...) lookup in _idDefault(), since subclasses might treat id lookups differently.
		8. Maybe also make the "year" parameter (and maybe the "query" parameter as well) to take in a list of values. And/or add a "yearFrom" and "yearTo" that is then converted to a list of years. Some providers, like Trakt support requests with year ranges. Will be more efficient for shows.py -> _details() for looking up the year +- 1.
		9. Maybe change the levels: l1=basic, l2=extended, l3=super-extended, l4=threaded-down, l5=threaded-up (for better consistency between providers).
		10. NB: Improve the speed of providers. Currently it can take 3secs+ just to process a show on level6 (excluding the API request time). A problem does not seem to be the data extraction, but rather _process() in TVDb. Some delays are caused by the dataUpdate() function in metadata.
'''

class MetaProvider(object):

	# Cache

	CacheClear			= Cache.TimeoutClear
	CacheRefresh		= Cache.TimeoutRefresh

	CacheSearch			= Cache.TimeoutDay1
	CacheId				= Cache.TimeoutDay1
	CacheLanguage		= Cache.TimeoutMonth1
	CacheMovie			= Cache.TimeoutWeek1
	CacheCollection		= Cache.TimeoutWeek1
	CacheShow			= Cache.TimeoutDay3
	CacheSeason			= Cache.TimeoutDay1
	CacheEpisode		= Cache.TimeoutDay3
	CachePerson			= Cache.TimeoutMonth1
	CacheCharacter		= Cache.TimeoutMonth1
	CacheCompany		= Cache.TimeoutMonth3
	CacheTranslation	= Cache.TimeoutMonth1

	CacheParameters		= ['id', 'idImdb', 'idTmdb', 'idTvdb', 'idTrakt', 'query', 'year', 'number', 'numberSeason', 'numberEpisode', 'media', 'limit', 'page', 'offset']

	# Level

	Level1				= 1			# Retrieves only basic data. A single request is made.
	Level2				= 2			# Same as Level1, but also retrieves addititonal data, which is typically the "extended" endpoint in APIs. A single request is made which should not take much longer than Level1.
	Level3				= 3			# Same as Level2, but also retrieves additional data, which is typically extra translations in APIs. A single request is made which should not take much longer than Level2.
	Level4				= 4			# Same as Level3, but also retrieves partially detailed data. Show data is detailed, whereas season and episode data is only basic. A single request is made, but it can take a little longer than Level3.
	Level5				= 5			# Same as Level4, but also retrieves partially detailed data. Show and season data is detailed, whereas episode data is only basic. Multiple concurrent requests are made for seasons in separate threads and it can take a lot longer than Level3.
	Level6				= 6			# Same as Level5, but also retrieves fully detailed data. Show, season, and episode data is detailed. Multiple concurrent requests are made in separate threads for seasons and episodes and it can take a lot longer than Level5. Only retrieves detailed data from lower levels (eg: for seasons retrieve detailed episodes, but NOT detailed show data).
	Level7				= 7			# Same as Level6, but also retrieves fully detailed data. Show, season, and episode data is detailed. Multiple concurrent requests are made in separate threads for the show, seasons, and episodes and it can take a lot longer than Level6. Retrieves detailed data from lower AND upper levels (eg: for seasons retrieve detailed episodes and detailed show data).
	LevelDefault		= Level4

	# Translation

	TranslationTitle	= 'title'
	TranslationOverview	= 'overview'

	# Limit

	LimitThread			= 50		# The maximum number of concurrent threads for multi-requests. Limit this for low-end devices, otherwise shows with 100s of episodes might start too many threads simultaneously.
	LimitRequest		= 50		# The maximum number of concurrent requests that each subclass can make to their respective API/website.
	LimitSearch			= 50		# The default maximum number of results returned for searches. Some providers (eg: TVDb) can return a lot of results, but we probably do not need all of them.

	# Lock

	CacheLock			= Lock()
	CacheLocks			= {}
	CacheData			= {}

	RequestLock			= Lock()
	RequestLocks		= {}

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		MetaProvider.CacheData = {}

	###################################################################
	# GENERAL
	##################################################################

	@classmethod
	def provider(self):
		try: return self.Provider
		except: return self.__name__.lower().replace('meta', '')

	###################################################################
	# CACHE
	###################################################################

	@classmethod
	def _cache(self, timeout, function, result = [], threading = True, semaphore = None, *args, **kwargs):
		# Use a lock when retrieving from cache.
		# If the cache is empty (new installation or cache was just cleared), multiple equal requests might be executed in parallel.
		# For instance, the TVDB authentication (token retrieval) might execute multiple times, since it is not in the cache yet.
		# Using a cache makes sure that these kinds of requests are only executed once.

		cache = Cache.instance()
		id = cache.id(function = function, **kwargs)
		data = None

		try:
			# Cache in memory, which is faster then reading/writing from the cache database (disk).
			# Update: The cache now also caches in memory. But this should still be a few seconds faster, since the cache function overheads are skipped.
			data = MetaProvider.CacheData[id]
		except:
			if not id in MetaProvider.CacheLocks:
				MetaProvider.CacheLock.acquire()
				if not id in MetaProvider.CacheLocks: MetaProvider.CacheLocks[id] = Lock()
				MetaProvider.CacheLock.release()

			if not kwargs: kwargs = {}
			kwargs['function_'] = function
			kwargs['threading'] = threading

			MetaProvider.CacheLocks[id].acquire()

			# Only go through the cache if it is an API request and not if it is a local processing function.
			# This drastically increases the speed on slow devices (from +- 120 secs down to 80 secs).
			# NB: The cache has been improved to reduce certain calculations and writing to disk in a separate thread.
			# The cache is not slowing down things anymore, and in some cases is actually faster (at least on a SSD).
			# If this is ever enabled again, note that any calls to Manager.movie(), Manager.show(), etc, will not cache the data. So the processing always has to be redone.
			#	if function == MetaProvider._request or function == MetaProvider._requestJson: data = cache.cacheSeconds(timeout, self._cacheThread, *args, **kwargs)
			#	else: data = self._cacheThread(*args, **kwargs)
			if timeout is False: data = self._cacheThread(*args, **kwargs)
			else: data = cache.cacheSeconds(timeout, self._cacheThread, *args, **kwargs)

			MetaProvider.CacheData[id] = data
			MetaProvider.CacheLocks[id].release()

		if semaphore: semaphore.release()
		result.append(data)
		return data

	@classmethod
	def _cacheThread(self, threading, *args, **kwargs):
		kwargs['result_'] = result_ = []
		if threading: Pool.thread(target = self._cacheExecute, args = args, kwargs = kwargs, start = True, join = True)
		else: self._cacheExecute(*args, **kwargs) # Already running in a parent thread, do not start a new thread (since creating threads takes long). Or threading was disabled.
		return result_[0]

	@classmethod
	def _cacheExecute(self, function_, result_, *args, **kwargs):
		result_.append(function_(*args, **kwargs))

	@classmethod
	def _cacheDefault(self, threaded, cache, timeout, function, *args, **kwargs):
		kwargs = self._idDefault(**kwargs)
		parameter = self._cacheParameter(**kwargs)

		if cache is False: timeout = False
		elif not cache is None and not cache is True: timeout = cache

		# Remove parameters passed to _cacheDefault() that are not a parameter in "function".
		arguments = {}
		parameters = Tools.getParameters(function)
		for k, v in kwargs.items():
			if k in parameters:
				arguments[k] = v
		if 'level' in arguments and arguments['level'] is None: arguments['level'] = MetaProvider.LevelDefault

		# Pass on the "threaded" value to the function, since they internally retrieve further shows/season/episodes.
		if 'threaded' in parameters: arguments['threaded'] = threaded

		# Pass on the "cache" value to the function, since they internally retrieve further shows/season/episodes.
		if function == self.__show or function == self.__season or function == self.__episode: arguments['cache'] = cache

		if parameter:
			# Starting new threads can be slow, especially on low-end devices.
			# Start threads here, since multiple resources can be requested at the same time, and sequentially requesting them is slower.
			# Eg: When opening a show, all the shows seasons/episodes might be requested with a single call to this function.
			# Pass "threading" in, in order not to create another sub-thread within _cache().

			results = []
			threads = []
			parameter = self._cacheParameters(parameter, **arguments)

			limit = 1
			if threaded is True:
				limit = MetaProvider.LimitThread
			elif threaded is None:
				# If a day-time show is retrieved that has 30 seasons, each containing 200 episodes.
				# If the Trakt progress list is retrieved, this can mean a few 100 requests:
				#	1. 200 individual detailed episode requests, plus a possible extra 200 requests if the next episode is in the next season instead of the current season.
				#	2. 30 individual detailed season requests.
				# If threading is completely disabled, 230+ requests have to be done sequentially.
				# This can make a single episode/show in the list hold up the entire menu loading, while all other list entries are already finished and there are technically enough threads available.
				# Allow a few extra threads here, depending on how many threads are currently running, and how many seasons/episodes need to be retrieved.
				# Eg: retrieving S28 for Hollyoaks (tt0112004):
				#	Full threading (max MetaProvider.LimitThread): 13 secs
				#	Dynamic threading (4-8 threads): 32 secs
				#	No threading (0 threads): 150 secs

				threaded = True
				counter = len(parameter)
				maximum = 5 if counter < 50 else 6 if counter < 100 else 7 if counter < 150 else 8
				available = Pool.threadAvailable(percent = True)
				while available > 0.2 and counter > 0:
					limit += 1
					available -= 0.02
					counter -= 10
					if limit >= maximum: break # No more than 5 threads.
			semaphore = Semaphore(limit)

			for i in parameter:
				semaphore.acquire() # Limit the number of concurrent threads, otherwise low-end devices might run out of threads and won't be able to create new ones.
				result = []
				results.append(result)
				i.update({'result' : result, 'timeout' : timeout, 'function' : function, 'threading' : False, 'semaphore' : semaphore})
				if threaded: threads.append(Pool.thread(target = self._cache, args = args, kwargs = i, start = True))
				else: self._cache(*args, **i)
			[i.join() for i in threads]
			return [i[0] for i in results]
		else:
			arguments['threading'] = threaded
			return self._cache(timeout, function, *args, **arguments)

	@classmethod
	def _cacheParameter(self, **kwargs):
		for key, value in kwargs.items():
			if key in MetaProvider.CacheParameters:
				if Tools.isArray(value): return key
		return None

	@classmethod
	def _cacheParameters(self, parameter, **kwargs):
		result = []
		for i in range(len(kwargs[parameter])):
			parameters = {}
			parameters.update(kwargs)
			for key in MetaProvider.CacheParameters:
				try:
					if Tools.isArray(kwargs[key]): parameters[key] = kwargs[key][i]
				except:
					try:
						if not Tools.isArray(kwargs[key]):
							parameters[key] = kwargs[key]
					except: pass
			result.append(parameters)
		return result

	###################################################################
	# REQUEST
	###################################################################

	@classmethod
	def _request(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, cache = None, threaded = None):
		if not cache is None: return self._cache(threaded = threaded, timeout = cache, function = MetaProvider._request, link = link, method = method, data = data, type = type, headers = headers, cookies = cookies)

		result = None
		try:
			self._requestLock()
			result = Networker().request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, agent = Networker.AgentSession)
		finally:
			self._requestUnlock()
		return result

	@classmethod
	def _requestJson(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, cache = None, threaded = None):
		response = MetaProvider._request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, cache = cache, threaded = threaded)
		if response: return Networker.dataJson(response['data'])
		else: return None

	@classmethod
	def _requestLock(self):
		# Limit the number of concurrent requests to the same API/website.
		# Some servers have restrictions on the number of simulations requests from the same IP, but even if they don't have, do not overload.

		id = self.provider()

		if not id in MetaProvider.RequestLocks:
			MetaProvider.RequestLock.acquire()
			if not id in MetaProvider.RequestLocks: MetaProvider.RequestLocks[id] = Semaphore(MetaProvider.LimitRequest)
			MetaProvider.RequestLock.release()

		MetaProvider.RequestLocks[id].acquire()

	@classmethod
	def _requestUnlock(self):
		MetaProvider.RequestLocks[self.provider()].release()

	###################################################################
	# DEFAULT
	###################################################################

	@classmethod
	def _default(self, media, year = None, number = None, numberSeason = None, numberEpisode = None, strict = True):
		numberSeason, numberEpisode = self._defaultNumber(media = media, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode)
		media = self._defaultMedia(media = media, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, strict = strict)
		numberSeason, numberEpisode = self._defaultNumber(media = media, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode)
		return media, numberSeason, numberEpisode

	@classmethod
	def _defaultMedia(self, media = None, year = None, numberSeason = None, numberEpisode = None, strict = True):
		if media is None:
			if not numberEpisode is None: return MetaData.MediaEpisode
			elif not numberSeason is None: return MetaData.MediaSeason

			if not strict:
				if not year is None: return MetaData.MediaMovie
				else: return MetaData.MediaShow
		return media

	@classmethod
	def _defaultNumber(self, media = None, number = None, numberSeason = None, numberEpisode = None):
		if not number is None:
			if numberSeason is None and media == MetaData.MediaSeason: numberSeason = number
			if numberEpisode is None and media == MetaData.MediaEpisode: numberEpisode = number

		if media == MetaData.MediaEpisode:
			if numberSeason is None: numberSeason = 1
			if numberEpisode is None: numberEpisode = 1
		elif not number is None:
			numberSeason = number

		return numberSeason, numberEpisode

	###################################################################
	# LANGUAGE
	###################################################################

	@classmethod
	def language(self, level = None, cache = None, threaded = None):
		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheLanguage, function = self._language, level = level)

	# Virtual
	@classmethod
	def _language(self, level = None):
		return None

	###################################################################
	# SEARCH
	###################################################################

	# year: single year or list of years. Some providers might not support year ranges and will have to make separate queries for each year.
	# page: the page offset, starting at 1.
	# offset: the absolute offset starting at 0.
	# Provide either a page or an offset.
	@classmethod
	def search(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None,  number = None, numberSeason = None, numberEpisode = None, media = None, limit = None, offset = None, page = None, level = None, cache = None, threaded = None):
		if limit is None: limit = MetaProvider.LimitSearch
		if offset is None: offset = ((limit * page) - 1) if page else 0
		if page is None: page = int(offset / float(limit)) if offset else 1

		media, numberSeason, numberEpisode = self._default(media = media, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode)

		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheSearch, function = self._search, idLookup = False, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, limit = limit, offset = offset, page = page, level = level)

	# Virtual
	@classmethod
	def _search(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, numberEpisode = None, media = None, limit = None, offset = None, page = None, level = None):
		return None

	###################################################################
	# ID
	###################################################################

	@classmethod
	def id(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, extract = None, level = None, cache = None, threaded = None):
		media, numberSeason, numberEpisode = self._default(media = media, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode)

		result = self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheId, function = self._id, idLookup = False, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, level = level)
		if extract:
			try: return result[extract]
			except: return None
		return result

	@classmethod
	def idImdb(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, threaded = None):
		return self.id(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, extract = MetaData.ProviderImdb, level = level, cache = cache, threaded = threaded)

	@classmethod
	def idTmdb(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, threaded = None):
		return self.id(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, extract = MetaData.ProviderTmdb, level = level, cache = cache, threaded = threaded)

	@classmethod
	def idTvdb(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, threaded = None):
		return self.id(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, extract = MetaData.ProviderTvdb, level = level, cache = cache, threaded = threaded)

	@classmethod
	def idTrakt(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, threaded = None):
		return self.id(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, extract = MetaData.ProviderTrakt, level = level, cache = cache, threaded = threaded)

	@classmethod
	def _idDefault(self, **kwargs):
		try: idLookup = kwargs['idLookup']
		except: idLookup = True

		try: idAny = kwargs['idAny']
		except: idAny = False

		# Remove invalid IDs.
		for key, value in kwargs.items():
			if key.startswith('id'):
				if not value or value in ['0', 'tt']:
					kwargs[key] = None

		if idAny:
			for key, value in kwargs.items():
				if key.startswith('id') and not value is None:
					kwargs['id'] = value
					break
		else:
			provider = self.provider()
			providerCapital = provider.capitalize()

			idKey = None
			try: id = kwargs['id']
			except: id = None

			for key, value in kwargs.items():
				if key.startswith('id') and providerCapital in key:
					idKey = key
					if not value is None: id = value
					break

			# If Trakt provider is added in the future, change the automatic native ID lookup, since Trakt API calls work with both Trakt IDs and IMDb IDs.
			# Maybe add something to subclasses that indicates for which IDs automatic lookups should be done.
			# And what about directly searching with query/year/number instead of an ID?
			if id is None and idLookup:
				parameters = {'extract' : provider}
				for i in ['query', 'year', 'numberSeason', 'numberEpisode', 'media', 'level']:
					try: parameters[i] = kwargs[i]
					except: pass
				for i in MetaData.Providers:
					i = 'id' + i.capitalize()
					try: parameters[i] = kwargs[i]
					except: pass
				id = self.id(**parameters)

			if id:
				if idKey: kwargs[idKey] = id
				kwargs['id'] = id

		return kwargs

	# Virtual
	@classmethod
	def _id(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, numberEpisode = None, media = None, level = None):
		return None

	###################################################################
	# MOVIE
	###################################################################

	@classmethod
	def movie(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None, cache = None, threaded = None):
		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheMovie, function = self._movie, media = MetaData.MediaMovie, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, level = level)

	# Virtual
	@classmethod
	def _movie(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None):
		return None

	###################################################################
	# COLLECTION
	###################################################################

	@classmethod
	def collection(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None, cache = None, threaded = None):
		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheCollection, function = self._collection, media = MetaData.MediaCollection, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, level = level)

	# Virtual
	@classmethod
	def _collection(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None):
		return None

	###################################################################
	# SHOW
	###################################################################

	@classmethod
	def show(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberAdjust = True, level = None, cache = None, threaded = None):
		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheShow, function = self.__show, media = MetaData.MediaShow, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberAdjust = numberAdjust, level = level)

	@classmethod
	def __show(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberAdjust = True, level = None, cache = None, threaded = None):
		result = self._show(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, level = level)
		if result:
			if level >= MetaProvider.Level5:
				provider = self.provider()
				if not number is None or not numberSeason is None: # Retrieve specific season.
					numberSeason, _ = self._defaultNumber(media = MetaData.MediaSeason, number = number, numberSeason = numberSeason)
					provider = self.provider()
					season = result.season(number = numberSeason)
					if season: season = season.idSeason(provider = provider)
				else: # Retrieve all seasons.
					season = result.idSeason(provider = provider)

				if season:
					season = self.season(id = season, show = result, level = level, cache = cache, threaded = threaded)
					if season: result.seasonSet(value = season, unique = provider)

		# TVDb uses the year as season number for some daytime shows.
		# Eg: Coronation Street - https://thetvdb.com/series/coronation-street
		if numberAdjust and result: result.numberAdjust()

		return result

	# Virtual
	@classmethod
	def _show(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None):
		return None

	###################################################################
	# SEASON
	###################################################################

	@classmethod
	def season(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, show = None, level = None, cache = None, threaded = None):
		numberSeason, _ = self._defaultNumber(media = MetaData.MediaSeason, number = number, numberSeason = numberSeason)
		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheSeason, function = self.__season, media = MetaData.MediaSeason, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, numberSeason = numberSeason, show = show, level = level)

	@classmethod
	def __season(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, show = None, level = None, cache = None, threaded = None):
		result = self._season(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, numberSeason = numberSeason, show = show, level = level)
		if result:
			if level >= MetaProvider.Level6:
				provider = self.provider()

				episode = result.idEpisode(provider = provider)
				if episode:
					episode = self.episode(id = episode, show = show, season = result, level = MetaProvider.Level6, cache = cache, threaded = threaded)
					if episode: result.episodeSet(value = episode, unique = provider)

				if level >= MetaProvider.Level7:
					resultShow = result.idShow(provider = provider)
					if resultShow:
						resultShow = self.show(id = resultShow, level = MetaProvider.Level3, cache = cache, threaded = threaded)
						if resultShow: result.showSet(value = resultShow, unique = provider)
		return result

	# Virtual
	@classmethod
	def _season(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, show = None, level = None):
		pass

	###################################################################
	# EPISODE
	###################################################################

	@classmethod
	def episode(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, show = None, season = None, level = None, cache = None, threaded = None):
		numberSeason, numberEpisode = self._defaultNumber(media = MetaData.MediaEpisode, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode)
		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheEpisode, function = self.__episode, media = MetaData.MediaEpisode, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, show = show, season = season, level = level)

	@classmethod
	def __episode(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, numberEpisode = None, show = None, season = None, level = None, cache = None, threaded = None):
		result = self._episode(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, show = show, season = season, level = level)
		if result:
			if level >= MetaProvider.Level7:
				provider = self.provider()
				resultSeason = result.idSeason(provider = provider)

				if resultSeason:
					resultSeason = self.season(id = resultSeason, show = show, level = MetaProvider.Level4, threaded = threaded)
					if resultSeason:
						resultShow = result.idShow(provider = provider)
						if resultShow:
							resultShow = self.show(id = resultShow, level = MetaProvider.Level4, threaded = threaded)
							if resultShow:
								resultSeason.showSet(value = resultShow, unique = provider)
								result.showSet(value = resultShow, unique = provider) # Set for the episode as well.
						result.seasonSet(value = resultSeason, unique = provider)
		return result

	# Virtual
	@classmethod
	def _episode(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, numberEpisode = None, show = None, season = None, level = None):
		return None

	###################################################################
	# CHARACTER
	###################################################################

	@classmethod
	def character(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None, cache = None, threaded = None):
		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheCharacter, function = self._character, media = MetaData.MediaCharacter, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, level = level)

	# Virtual
	@classmethod
	def _character(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None):
		return None

	###################################################################
	# PERSON
	###################################################################

	@classmethod
	def person(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None, cache = None, threaded = None):
		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CachePerson, function = self._person, media = MetaData.MediaPerson, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, level = level)

	# Virtual
	@classmethod
	def _person(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None):
		return None

	###################################################################
	# COMPANY
	###################################################################

	@classmethod
	def company(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None, cache = None, threaded = None):
		return self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheCompany, function = self._company, media = MetaData.MediaCompany, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, level = level)

	# Virtual
	@classmethod
	def _company(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None):
		return None

	###################################################################
	# TRANSLATION
	###################################################################

	@classmethod
	def translation(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, translation = None, language = None, limit = None, level = None, cache = None, threaded = None):
		if translation is None: translation = MetaProvider.TranslationTitle
		media, numberSeason, numberEpisode = self._default(media = media, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, strict = False)

		result = self._cacheDefault(threaded = threaded, cache = cache, timeout = MetaProvider.CacheTranslation, function = self._translation, id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, translation = translation, level = level)

		if result:
			if not language is None:
				if Tools.isArray(language):
					temp = {}
					for i in language:
						try: temp[i] = result[i]
						except: pass
					result = temp
				elif language is True:
					try: result = result[MetaData.LanguageUniversal]
					except:
						try: result = result[MetaData.LanguageEnglish]
						except: result = None
				else:
					try: result = result[language]
					except: result = None

			if not limit is None:
				if limit is True or limit == 1:
					if Tools.isArray(result):
						try: result = result[0]
						except: result = None
					else:
						temp = {}
						for key, value in result.items():
							try: temp[key] = value[0]
							except: pass
						result = temp
				else:
					if Tools.isArray(result):
						try: result = result[:limit]
						except: result = None
					else:
						temp = {}
						for key, value in result.items():
							try: temp[key] = value[:limit]
							except: pass
						result = temp

		return result

	@classmethod
	def translationTitle(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, language = None, limit = None, level = None, cache = None, threaded = None):
		return self.translation(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, translation = MetaProvider.TranslationTitle, language = language, limit = limit, level = level, cache = cache, threaded = threaded)

	@classmethod
	def translationOverview(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, language = None, limit = None, level = None, cache = None, threaded = None):
		return self.translation(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, translation = MetaProvider.TranslationOverview, language = language, limit = limit, level = level, cache = cache, threaded = threaded)

	# Virtual
	@classmethod
	def _translation(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, numberSeason = None, numberEpisode = None, media = None, translation = None, level = None):
		return None
