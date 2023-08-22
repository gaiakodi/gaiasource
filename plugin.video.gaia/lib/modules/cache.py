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
from ast import literal_eval

from lib.modules.tools import Time, Hash, Logger, System, Converter, Tools
from lib.modules.database import Database
from lib.modules.serializer import Serializer
from lib.modules.concurrency import Pool, Lock

class Cache(Database):

	Name = Database.NameCache # The name of the file. Update version number of the database structure changes.
	NameTrakt = 'trakt'
	NameExpression = 'expression'

	Skip = '[GAIACACHESKIP]' # If a function returns this value, it will not be cached.

	ModeSynchronous = 1		# If expired, wait until the new data has been retrieved, and return the new data.
	ModeAsynchronous = 2	# If expired, retrieve the new data in the background, and immediately return the old data.
	ModeDefault = ModeAsynchronous

	StorageAll = 1		# Cache all data to the database.
	StorageFull = 2		# Only cache non-empty data to the database.
	StorageDefault = StorageAll

	TimeoutMinute1 = 60 # 1 Minute.
	TimeoutMinute5 = 300 # 5 Minutes.
	TimeoutMinute10 = 600 # 10 Minutes.
	TimeoutMinute15 = 900 # 15 Minutes.
	TimeoutMinute20 = 1200 # 20 Minutes.
	TimeoutMinute25 = 1500 # 25 Minutes.
	TimeoutMinute30 = 1800 # 30 Minutes.
	TimeoutMinute45 = 2700 # 45 Minutes.

	TimeoutHour1 = 3600 # 1 Hour.
	TimeoutHour2 = 7200 # 2 Hours.
	TimeoutHour3 = 10800 # 3 Hours.
	TimeoutHour4 = 14400 # 4 Hours.
	TimeoutHour5 = 18000 # 5 Hours.
	TimeoutHour6 = 21600 # 6 Hours.
	TimeoutHour9 = 32400 # 9 Hours.
	TimeoutHour12 = 43200 # 12 Hours.
	TimeoutHour18 = 64800 # 18 Hours.

	TimeoutDay1 = 86400 # 1 Day.
	TimeoutDay2 = 172800 # 2 Days.
	TimeoutDay3 = 259200 # 3 Days.
	TimeoutDay4 = 345600 # 4 Days.
	TimeoutDay5 = 432000 # 5 Days.
	TimeoutDay6 = 518400 # 6 Days.

	TimeoutWeek1 = 604800 # 1 Week.
	TimeoutWeek2 = 1209600 # 2 Weeks.
	TimeoutWeek3 = 1814400 # 3 Weeks.

	TimeoutMonth1 = 2592000 # 1 Month (30 Days).
	TimeoutMonth2 = 5270400 # 2 Months (61 Days).
	TimeoutMonth3 = 7862400 # 3 Months (91 Days).
	TimeoutMonth4 = 10540800 # 4 Months (122 Days).
	TimeoutMonth5 = 13132800 # 5 Months (152 Days).
	TimeoutMonth6 = 15811200 # 6 Months (183 Days).
	TimeoutMonth9 = 23673600 # 9 Months (274 Days).

	TimeoutYear1 = 31536000 # 1 Year (365 Days).
	TimeoutYear2 = 63072000 # 2 Years (730 Days).
	TimeoutYear3 = 94608000 # 3 Years (1095 Days).

	# Keep the timeout as short as possible.
	# The idea is to always update the data in the background on each request.
	# This can cause too many requests if the same cache is access multiple times per second/minute.
	TimeoutClear = -1 # Force refresh the data, but wait until the new data comes in (ModeSynchronous).
	TimeoutRefresh = 0 # Force refresh the data, but still return the current cached data (ModeAsynchronous).
	TimeoutReset = TimeoutMonth1 # 30 Days. Maximum timeout. If values are greater than this, the timeout will be set to TimeoutClear.
	TimeoutMini = TimeoutMinute10  # 10 Minutes.
	TimeoutShort = TimeoutHour1 # 1 Hour.
	TimeoutMedium = TimeoutHour6 # 6 Hours.
	TimeoutLong = TimeoutDay1 # 1 Day.
	TimeoutExtended = TimeoutDay3 # 3 Days.

	Instance = None
	Id = None
	Lock = Lock()
	Updated = False

	def __init__(self, mode = ModeDefault, storage = StorageDefault, timeout = None, internal = False):
		if not internal:
			Logger.log('The Cache class is a singleton and should only be created through the instance() function.', type = Logger.TypeFatal, prefix = True)
			System.exit(log = True)

		Database.__init__(self, Cache.Name)
		self.mMode = mode
		self.mStorage = storage
		self.mTimeout = timeout
		self.mData = {}

	# NB: Always use a single instance of Cache.
	# If creating separate instance using the constructor, each instance will create its own OS file handle to the .db file and establish a seaprate database connection.
	# If too many instances of Cache are created/used (eg: when retrieving metadata, such as retrieving multiple shows and for each show retrieve all the episodes), too many threads will have open database files/connections.
	# This causes SQLite to fail with after too many accesses with the error: "OperationalError: unable to open database file".
	# This problem seems to solved when using a single Cache instance.
	@classmethod
	def instance(self):
		if Cache.Instance is None:
			Cache.Lock.acquire()
			if Cache.Instance is None: Cache.Instance = Cache(internal = True)
			Cache.Lock.release()
		return Cache.Instance

	@classmethod
	def reset(self, settings = True):
		if not Cache.Instance is None:
			Cache.Instance.mData = {}

	##############################################################################
	# DATABASE
	##############################################################################

	def _initialize(self):
		self._create('''
			CREATE TABLE IF NOT EXISTS %s
			(
				id TEXT PRIMARY KEY,
				time INTEGER,
				data TEXT
			);
			'''
		)

		self._create('''
			CREATE TABLE IF NOT EXISTS %s
			(
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				time INTEGER,
				link TEXT,
				data TEXT
			);
			''' % Cache.NameTrakt
		)
		self._create('''
			CREATE TABLE IF NOT EXISTS %s
			(
				id TEXT PRIMARY KEY,
				val TEXT,
				versionKodi TEXT,
				versionAddon TEXT,
				data TEXT
			);
			''' % Cache.NameExpression
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON %s(id, versionKodi, versionAddon);' % (Cache.NameExpression, Cache.NameExpression))

	def _insert(self, query, parameters = None, commit = True):
		Cache.Updated = True
		return Database._insert(self, query = query, parameters = parameters, commit = commit)

	##############################################################################
	# ID
	##############################################################################

	def id(self, function, *args, **kwargs):
		kwargs = self._cacheArguments(function, *args, **kwargs)
		return self._id(function, kwargs)

	def _id(self, function, kwargs):
		if function:
			init = self._idInitialize()
			id = init['expression2'].sub('', init['expression1'].sub('', repr(function))) + '_'
		else:
			id = ''
		id += '_'.join([str(key) + '=' + str(value) for key, value in kwargs.items()])
		return self._idHash(id)

	@classmethod
	def _idGenerate(self, *args, **kwargs):
		data = []
		if args: data.extend(args)
		if kwargs: data.extend([str(key) + '=' + str(value) for key, value in kwargs.items()])
		return self._idHash('_'.join(data))

	@classmethod
	def _idHash(self, data):
		# http://atodorov.org/blog/2013/02/05/performance-test-md5-sha1-sha256-sha512/
		# Hash algorithms have different speeds.
		# These are own tests conducted:
		#	MD5: 2408
		#	SHA1: 2012
		#	SHA256: 3171
		#	SHA512: 2731
		# Use the fastest one, since it is very unlikley that we would have a collison with short hashes.
		return Hash.sha1(data)

	def _idInitialize(self):
		if Cache.Id is None: Cache.Id = {'kodi' : System.versionKodi(full = True), 'addon' : System.version(), 'expression1' : re.compile('.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+'), 'expression2' : re.compile('>')}
		return Cache.Id

	def _idRepresentation(self, function, kwargs):
		if function:
			init = self._idInitialize()
			function = init['expression2'].sub('', init['expression1'].sub('', repr(function)))
		else:
			function = ''
		parameters = ', '.join([str(key) + '=' + str(value) for key, value in kwargs.items()])
		return 'Function : %s | Parameters: %s' % (function, parameters)

	##############################################################################
	# EXECUTE
	##############################################################################

	def execute(self, function, *args, **kwargs):
		kwargs = self._cacheArguments(function, *args, **kwargs)
		return function(**kwargs)

	##############################################################################
	# CACHE
	##############################################################################

	def cacheSelect(self, id): # For direct public access.
		result = self._cacheSelect(id = self._id(function = None, kwargs = {'id' : id}))
		if result: result = result[2]
		return result

	def cacheUpdate(self, id, data): # For direct public access.
		return self._cacheUpdate(id = self._id(function = None, kwargs = {'id' : id}), data = data)

	def _cacheSelect(self, id):
		try: return self.mData[id]
		except: return self._selectSingle('SELECT 0, time, data FROM %s WHERE id = ?;', parameters = (id,)) # Select "0" to indicate the data is not yet unserialized.

	def _cacheUpdate(self, id, data, serialize = False, thread = False):
		# NB: Copy the data before saving it to disk.
		# Since a thread is used for writing, the data (dictionary/list) might have changed its internal structure before it can be written, causing inconsistencies.
		# For instance:
		#	1. Open the Shows -> Lists -> Highest Rated.
		#	2. Delete cache.db.
		#	3. Open "Breaking Bad".
		#	4. Open the "Specials" menu.
		#	5. There will be an error saying nothing could be found.
		# This is because the TVDb season list that is retrieved before caching, is:
		#	[1, 2, 3, 4, 0, 5]
		# While the caching thread runs, the season list in the Metadata object is sorted/adjusted ending in:
		#	[1, 2, 2, 3, 4, 5]
		# Now there is no Season 0, but two Season 2s.
		if serialize: data = Tools.copy(data, deep = True)

		time = Time.timestamp()
		self.mData[id] = (serialize, time, data)

		# The longest part of a cache process is writing to disk.
		# This is even more problematic on slow disks, like HDDs.
		# Run in a separate thread and immediately return that the calling process can continue.
		# Do not start in a thread if we are already inside a thread from a asynchronous call.
		if thread: self.__cacheUpdate(id = id, time = time, data = data, serialize = serialize)
		else: Pool.thread(target = self.__cacheUpdate, kwargs = {'id' : id, 'time' : time, 'data' : data, 'serialize' : serialize}, start = True)

	def __cacheUpdate(self, id, time, data, serialize = False):
		if serialize: data = self._cacheDataTo(data)
		self._insert('INSERT OR IGNORE INTO %s (id) VALUES (?);', (id,))
		return self._update('UPDATE %s SET time = ?, data = ? WHERE id = ?;', parameters = (time, data, id))

	def _cacheDelete(self, id):
		try: del self.mData[id]
		except: pass
		return self._update('DELETE FROM %s WHERE id = ?;', parameters = (id,))

	def _cacheDataTo(self, data):
		try:
			serial = Serializer.dataSerialize(data)
			if serial: data = serial
		except: pass
		return repr(data)

	def _cacheDataFrom(self, data):
		if data is None: return data
		value = data[2]
		if data[0] or value is None: return value
		value = literal_eval(value)
		try:
			serial = Serializer.dataUnserialize(value)
			if serial: value = serial
		except: pass
		return value

	def _cacheDataValid(self, data):
		if data is None or data == [] or data == {} or data == '': return False
		elif data == 'None' or data == '[]' or data == '{}': return False
		else: return True

	def _cacheArguments(self, function, *args, **kwargs):
		# Convert args to kwargs.
		try: parameters = function.__code__.co_varnames # Python 3
		except: parameters = function.func_code.co_varnames # Python 2
		parameters = (parameter for parameter in parameters if not parameter == 'self')
		kwargs.update(dict(zip(parameters, args)))
		return kwargs

	def _cache(self, id, function, kwargs, thread = False):
		try:
			data = function(**kwargs)
			if data == Cache.Skip:
				return None
			else:
				if self.mStorage == Cache.StorageAll or self._cacheDataValid(data): self._cacheUpdate(id = id, data = data, thread = thread, serialize = True)
				return data
		except:
			Logger.error()
			return None

	def cache(self, mode, timeout, refresh, function, *args, **kwargs):
		try:
			kwargs = self._cacheArguments(function, *args, **kwargs)
			id = self._id(function, kwargs)

			if mode is None: mode = self.mMode
			if timeout is None: timeout = self.mTimeout

			if timeout >= Cache.TimeoutRefresh:
				cache = self._cacheSelect(id)
				if cache:
					try:
						difference = Time.timestamp() - cache[1]
						if difference > Cache.TimeoutReset: timeout = Cache.TimeoutClear
						elif (refresh and difference <= refresh) or difference <= timeout:
							data = self._cacheDataFrom(cache)

							# Only force refresh data if the previous try is not too new.
							# Otherwise when opening a channel menu under Movies -> Networks, there are always a bunch of these refreshes.
							old = difference > (timeout * 0.3)

							# Sometimes the cached data is None.
							# This typically indicates that the cached function failed (eg: no internet to retrieve the data).
							# Refresh the request in such a case.
							if old and data is None:
								Logger.log('CACHE: Clearing and reevaluating failed result data (None) - [%s]' % self._idRepresentation(function, kwargs), type = Logger.TypeError, developer = True)
								timeout = Cache.TimeoutClear

							# Sometimes the cached data is an empty list.
							# This typically indicates that the cached function failed (eg Movie Arrivals -> movies.py -> imdbList() -> return an empty list because HTML cannot be interpreted).
							# However, it can also mean that the function succeded, but just returned an empty list (eg: retrieving a list from Trakt/IMDb that is just empty).
							# The user can manually clear the cache to solve this problem, but that is not very user-friendly.
							# If the list is empty, use TimeoutRefresh instead of TimeoutClear, to not hold up processes where the valid results is just an empty list.
							# The user will therefore have to load the menu twice before it will work.
							# UPDATE 1: Do not do this anymore. This can make true empty lists (eg Title Aliases) to always re-retrieve.
							# UPDATE 2: Re-enable this. Even if the request was successful and returns an empty list, it probably indicates a problem on the server-side (eg temporary problem, missing metadata, etc). Re-retrieve and hope new metadata is returned.
							elif old and Tools.isArray(data) and len(data) == 0:
								Logger.log('CACHE: Refreshing failed result data in the background (Empty List) - [%s]' % self._idRepresentation(function, kwargs), type = Logger.TypeError, developer = True)
								timeout = Cache.TimeoutRefresh

							elif not refresh: return data
					except: # If cache[0] is None.
						timeout = Cache.TimeoutClear
			else:
				cache = None

			if timeout == Cache.TimeoutClear or mode == Cache.ModeSynchronous or not cache:
				return self._cache(id, function, kwargs)
			else:
				Pool.thread(target = self._cache, kwargs = {'id' : id, 'function' : function, 'thread' : True, 'kwargs' : kwargs}, start = True)
				return self._cacheDataFrom(cache)
		except:
			Logger.error('Cache Failed: ' + str(function))
		return None

	def cacheRetrieve(self, function, *args, **kwargs):
		try:
			kwargs = self._cacheArguments(function, *args, **kwargs)
			id = self._id(function, kwargs)
			return self._cacheDataFrom(self._cacheSelect(id))
		except:
			return None

	def cacheExists(self, function, *args, **kwargs):
		return bool(self.cacheRetrieve(function, *args, **kwargs))

	# Delete the entire cache entry.
	def cacheDelete(self, function, *args, **kwargs):
		kwargs = self._cacheArguments(function, *args, **kwargs)
		id = self._id(function, kwargs)
		self._cacheDelete(id)

	# Use the timeout set in the constructor.
	def cacheFixed(self, function, *args, **kwargs):
		return self.cache(None, None, function, *args, **kwargs)

	# Force refresh the data, but wait until the new data comes in (ModeSynchronous).
	def cacheClear(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutClear, None, function, *args, **kwargs)

	# Force refresh the data, but still return the current cached data (ModeAsynchronous).
	def cacheRefresh(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutRefresh, None, function, *args, **kwargs)

	# Force refresh the data, but still return the current cached data (ModeAsynchronous).
	def cacheRefreshSeconds(self, timeout, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutRefresh, timeout, function, *args, **kwargs)

	# Force refresh the data, but still return the current cached data (ModeAsynchronous).
	# Will wait to force refresh if the cached data is older than TimeoutMini (ModeSynchronous).
	def cacheRefreshMini(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutRefresh, Cache.TimeoutMini, function, *args, **kwargs)

	# Force refresh the data, but still return the current cached data (ModeAsynchronous).
	# Will wait to force refresh if the cached data is older than TimeoutShort (ModeSynchronous).
	def cacheRefreshShort(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutRefresh, Cache.TimeoutShort, function, *args, **kwargs)

	# Force refresh the data, but still return the current cached data (ModeAsynchronous).
	# Will wait to force refresh if the cached data is older than TimeoutMedium (ModeSynchronous).
	def cacheRefreshMedium(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutRefresh, Cache.TimeoutMedium, function, *args, **kwargs)

	# Force refresh the data, but still return the current cached data (ModeAsynchronous).
	# Will wait to force refresh if the cached data is older than TimeoutLong (ModeSynchronous).
	def cacheRefreshLong(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutRefresh, Cache.TimeoutLong, function, *args, **kwargs)

	# Force refresh the data, but still return the current cached data (ModeAsynchronous).
	# Will wait to force refresh if the cached data is older than TimeoutExtended (ModeSynchronous).
	def cacheRefreshExtended(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutRefresh, Cache.TimeoutExtended, function, *args, **kwargs)

	def cacheSynchronousSeconds(self, timeout, function, *args, **kwargs):
		return self.cache(Cache.ModeSynchronous, timeout, None, function, *args, **kwargs)

	def cacheSynchronousMinutes(self, timeout, function, *args, **kwargs):
		return self.cache(Cache.ModeSynchronous, timeout * 60, None, function, *args, **kwargs)

	def cacheSynchronousHours(self, timeout, function, *args, **kwargs):
		return self.cache(Cache.ModeSynchronous, timeout * 3600, None, function, *args, **kwargs)

	def cacheSynchronousDays(self, timeout, function, *args, **kwargs):
		return self.cache(Cache.ModeSynchronous, timeout * 86400, None, function, *args, **kwargs)

	def cacheSynchronousMini(self, function, *args, **kwargs):
		return self.cache(Cache.ModeSynchronous, Cache.TimeoutMini, None, function, *args, **kwargs)

	def cacheSynchronousShort(self, function, *args, **kwargs):
		return self.cache(Cache.ModeSynchronous, Cache.TimeoutShort, None, function, *args, **kwargs)

	def cacheSynchronousMedium(self, function, *args, **kwargs):
		return self.cache(Cache.ModeSynchronous, Cache.TimeoutMedium, None, function, *args, **kwargs)

	def cacheSynchronousLong(self, function, *args, **kwargs):
		return self.cache(Cache.ModeSynchronous, Cache.TimeoutLong, None, function, *args, **kwargs)

	def cacheSynchronousExtended(self, function, *args, **kwargs):
		return self.cache(Cache.ModeSynchronous, Cache.TimeoutExtended, None, function, *args, **kwargs)

	def cacheSeconds(self, timeout, function, *args, **kwargs):
		return self.cache(None, timeout, None, function, *args, **kwargs)

	def cacheMinutes(self, timeout, function, *args, **kwargs):
		return self.cache(None, timeout * 60, None, function, *args, **kwargs)

	def cacheHours(self, timeout, function, *args, **kwargs):
		return self.cache(None, timeout * 3600, None, function, *args, **kwargs)

	def cacheDays(self, timeout, function, *args, **kwargs):
		return self.cache(None, timeout * 86400, None, function, *args, **kwargs)

	def cacheMini(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutMini, None, function, *args, **kwargs)

	def cacheShort(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutShort, None, function, *args, **kwargs)

	def cacheMedium(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutMedium, None, function, *args, **kwargs)

	def cacheLong(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutLong, None, function, *args, **kwargs)

	def cacheExtended(self, function, *args, **kwargs):
		return self.cache(None, Cache.TimeoutExtended, None, function, *args, **kwargs)

	##############################################################################
	# TRAKT
	##############################################################################

	def traktCache(self, link, data = None, timestamp = None):
		# Only cache the requests that change something on the Trakt account.
		# Trakt uses JSON post data to set things and only uses GET parameters to retrieve things.
		if data is None: return None
		if timestamp is None: timestamp = Time.timestamp()
		self._insert('INSERT INTO %s (time, link, data) VALUES (?, ?, ?);' % Cache.NameTrakt, parameters = (timestamp, link, self._cacheDataTo(data)))

	def traktRetrieve(self):
		self._lock() # Execute the select and delete as atomic operations.
		result = self._selectSingle('SELECT id, time, link, data FROM %s ORDER BY time ASC LIMIT 1;' % Cache.NameTrakt)
		if not result:
			self._unlock()
			return None
		self._delete('DELETE FROM %s WHERE id = ?;' % Cache.NameTrakt, parameters = (result[0],))
		self._unlock()
		return {'time' : result[1], 'link' : result[2], 'data' : self._cacheDataFrom([False, result[1], result[3]])}

	##############################################################################
	# EXPRESSION
	##############################################################################

	def expressionCache(self, id, data):
		init = self._idInitialize()
		return self._insert('INSERT OR IGNORE INTO %s (id, versionKodi, versionAddon, data) VALUES (?, ?, ?, ?);' % Cache.NameExpression, (id, init['kodi'], init['addon'], data))

	def expressionRetrieve(self, id):
		init = self._idInitialize()
		return self._selectValue('SELECT data FROM %s WHERE id = ? AND versionKodi = ? AND versionAddon = ?;' % Cache.NameExpression, parameters = (id, init['kodi'], init['addon']))

	def expressionClean(self):
		init = self._idInitialize()
		return self._delete('DELETE FROM %s WHERE versionKodi <> ? OR versionAddon <> ?;' % Cache.NameExpression, parameters = (init['kodi'], init['addon']), compress = True)

	##############################################################################
	# CLEAN
	##############################################################################

	def _clean(self, time, commit = True, compress = True):
		if time: return self._delete(query = 'DELETE FROM `%s` WHERE time <= ?;' % Cache.Name, parameters = [time], commit = commit, compress = compress)
		return False

	def _cleanTime(self, count):
		if count:
			times = self._selectValues(query = 'SELECT time FROM `%s` ORDER BY time ASC LIMIT ?;' % Cache.Name, parameters = [count])
			if times: return Tools.listSort(times)[:count][-1]
		return None

# The idea behind this local memory cache is as follows:
#	1. Try to load the cached value from a class variable.
#	2. If not available, try to load the value from a global Kodi window property.
#	3. If not available, let the calling class decide what to do.
# This can drastically improve processing time, especially where values are accessed multiple times during an execution, such as various menu loading.
class Memory(object):

	Property	= 'GaiaCache_'
	Uncached	= 'GaiaCacheUncached'

	Timeout		= 86400 # 24 hours.

	Data		= {}

	@classmethod
	def reset(self, settings = True):
		# When using <reuselanguageinvoker>, clear old values every now and then.
		time = Time.timestamp() - Memory.Timeout
		for k, v in Memory.Data.items():
			try:
				if v['time'] < time:
					del Memory.Data[k]
					System.windowPropertyClear(k)
			except: Logger.error()

	@classmethod
	def id(self, *args, **kwargs):
		return Memory.Property + Cache._idGenerate(*args, **kwargs)

	@classmethod
	def idValid(self, id):
		return id and id.startswith(Memory.Property)

	@classmethod
	def get(self, id = None, uncached = False, local = True, kodi = False, **kwargs):
		id = id if self.idValid(id) else self.id(id, **kwargs)

		valid = True
		value = None

		if local:
			try: return Memory.Data[id]['value']
			except: pass

		if kodi:
			value = System.windowPropertyGet(id)
			if value:
				value = Converter.jsonFrom(value)
				Memory.Data[id] = value
				value = value['value']
			else:
				valid = False
		else:
			valid = False

		if not valid: value = Memory.Uncached if uncached else None
		return value

	@classmethod
	def set(self, value, id = None, local = True, kodi = False, **kwargs):
		id = id if self.idValid(id) else self.id(id, **kwargs)
		data = {'value' : value, 'time' : Time.timestamp()}
		if local: Memory.Data[id] = data
		if kodi: System.windowPropertySet(id, Converter.jsonTo(data)) # Always save as a JSON object, so we can preserve the data type and deal with "empty" values.
		return value

	@classmethod
	def clear(self, id = None, local = True, kodi = False, **kwargs):
		id = id if self.idValid(id) else self.id(id, **kwargs)
		if local:
			try: del Memory.Data[id]
			except: pass
		if kodi: System.windowPropertyClear(id)

	@classmethod
	def has(self, id = None, local = True, kodi = False, **kwargs):
		id = id if self.idValid(id) else self.id(id, **kwargs)
		if local and id in Memory.Data: return True
		if kodi and System.windowPropertyGet(id): return True
		return False

	@classmethod
	def cached(self, value):
		return not value == Memory.Uncached

	@classmethod
	def uncached(self, value):
		return value == Memory.Uncached
