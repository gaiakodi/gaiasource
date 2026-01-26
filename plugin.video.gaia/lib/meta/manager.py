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

from lib.modules.tools import Media, Logger, Tools, System, Time, Regex, Math, Title, Language, Audience, Hardware, Settings
from lib.modules.concurrency import Pool, Lock, Semaphore
from lib.modules.cache import Cache, Memory
from lib.modules.network import Networker

from lib.meta.core import MetaCore
from lib.meta.data import MetaData
from lib.meta.pack import MetaPack
from lib.meta.cache import MetaCache
from lib.meta.tools import MetaTools
from lib.meta.image import MetaImage

from lib.meta.provider import MetaProvider
from lib.meta.providers.imdb import MetaImdb
from lib.meta.providers.tmdb import MetaTmdb
from lib.meta.providers.tvdb import MetaTvdb
from lib.meta.providers.trakt import MetaTrakt
from lib.meta.providers.fanart import MetaFanart

class MetaManager(object):

	Smart				= 'smart'

	ContentDiscover		= 'discover'
	ContentSearch		= 'search'
	ContentQuick		= 'quick'
	ContentProgress		= 'progress'
	ContentHistory		= 'history'
	ContentArrival		= 'arrival'
	ContentRandom		= 'random'
	ContentList			= 'list'
	ContentPerson		= 'person'
	ContentSeason		= 'season'
	ContentEpisode		= 'episode'
	ContentSet			= 'set'

	SpecialSettings		= None
	SpecialInclude		= True
	SpecialExclude		= False
	SpecialReduce		= 'reduce'

	ModeSynchronous		= 'synchronous'		# Make various background threads run in the foreground, waiting for them to finish before continuing.
	ModeUndelayed		= 'undelayed'		# Make Cache write updates immediately, instead of scheduling in a background thread to execute at the end of execution.
	ModeGenerative		= 'generative'		# Put MetaCache into generative mode to create the external metadata addon.
	ModeAccelerate		= 'accelerate'		# Try to accelerate smart menu refreshes by doing the minimal amount of work. Eg: useful during binging when we do not want to hold up the playback of the next episode if smart-refreshing is going on in the background.

	OriginTrakt			= 'trakt'			# The release info comes from Trakt's calendars.
	OriginOfficial		= 'official'		# The release info comes from a disk/streaming release date website.
	OriginScene			= 'scene'			# The release info comes from a scene-release website.
	OriginArrival		= 'arrival'			# The release info comes from the internal Arrival menu content.
	OriginProgress		= 'progress'		# The release info comes from the internal Progress menu content.

	PropertyRelease		= 'GaiaMetaRelease'
	PropertyBusy		= 'GaiaMetaBusy'

	Instance			= None
	Batch				= None

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, mode = None, tester = None):
		self.mTools = MetaTools.instance()
		self.mLanguage = self.mTools.settingsLanguage()

		self.mDetail = self.mTools.settingsDetail()
		self.mLevel = self.mTools.settingsDetail(level = True)
		self.mTester = tester

		self.mDeveloper = System.developerVersion()
		self.mDeveloperExtra = False

		self.mModeSynchronous = None
		self.mModeGenerative = None
		self.mModeUndelayed = None
		self.mModeAccelerate = None
		if mode:
			if MetaManager.ModeSynchronous in mode: self.mModeSynchronous = True
			if MetaManager.ModeGenerative in mode: self.mModeGenerative = True
			if MetaManager.ModeUndelayed in mode: self.mModeUndelayed = True
			if MetaManager.ModeAccelerate in mode: self.mModeAccelerate = True

		self.mPerformance = Hardware.performanceRating()
		self.mPerformanceFast = False
		self.mPerformanceMedium = False
		self.mPerformanceSlow = False
		if self.mPerformance >= 0.75: self.mPerformanceFast = True
		elif self.mPerformance >= 0.6: self.mPerformanceMedium = True
		else: self.mPerformanceSlow = True

		self.mReleaseMedia = None

		self.mReloadMedia = None
		self.mReloadBusy = False
		self.mReloadQuick = False

		self.mLock = Lock()
		self.mLocks = {}

		self.mProviders = None
		self.mLimits = {}
		self.mThreads = {}
		self.mRenew = None

		# More info in _busyBenchmark()
		self.mBusyThread = None
		self.mBusyLock = Lock()
		self.mBusyGlobal = True		# Use global instead of local memory.
		self.mBusyMultiple = True	# Store all IDs in a single memory value, instead of storing each ID in a separate memory value.
		self.mBusyThreaded = False	# Use threads to remove the values from memory.
		self.mBusyWait = True		# When using threads for removal, delay the removal until other processing is done.
		self.mBusyRemove = []
		self.mBusyProvider = [MetaTools.ProviderTrakt, MetaTools.ProviderImdb, MetaTools.ProviderTmdb, MetaTools.ProviderTvdb, MetaTools.ProviderImdx] # Order from most likely to least likley to find the ID, to save some time.

		self.mJob = None
		self.jobReset()

		# Using a long delay makes loading menus, like Quick, faster.
		# If cache data is refreshed in the background, the refresh call to the cache function is delayed, allowing other code to continue.
		# Hence, the detailed metadata retrieval, paging, and sorting can execute before the cache data refresh thread is executed.
		# Eg: This reduces Quick menu loading from 1.5 secs to 1.0 secs.
		self.mCache = None
		self._cacheInitialize(mode = Cache.ModeSynchronous if self.mModeSynchronous else Cache.ModeDefault, delay = Cache.DelayDisable if self.mModeUndelayed else Cache.DelayLong)

	@classmethod
	def instance(self):
		if MetaManager.Instance is None: MetaManager.Instance = self()
		return MetaManager.Instance

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		MetaManager.Instance = None
		MetaManager.Batch = None

	##############################################################################
	# THREAD
	##############################################################################

	# These only contain the threads from the _metadataCache() and the update functions called within.
	# This does not contain any of the other threads *smart-reloading, etc).
	# These functions allow us to join the threads and wait for the manager to finish the metadata updates it is busy with.
	# Used by Tester to wait for one batch of metadata updates to finish before continuing to the next batch.

	def _threadAdd(self, thread):
		# Do not store the thread objects in the self.mThreads.
		# Otherwise if threadJoin() is never called (currently only called from tester.py), the thread remains in memory and does not get garbage-collected.
		#self.mThreads[thread.id()] = thread
		self.mThreads[thread.id()] = True

	def _threadClear(self):
		self.mThreads = {}

	def threadJoin(self, timeout = None):
		try:
			if timeout: timer = Time(start = True)
			for id in list(self.mThreads.keys()): # Use a list, since we edit/delete from the dict in the loop.
				if Pool.busy(id = id): Pool.join(instance = Pool.retrieve(id = id), timeout = timeout)
				del self.mThreads[id]
				if timeout and timer.elapsed() > timeout: return False
			return True
		except: Logger.error()
		return False

	##############################################################################
	# CHECK
	##############################################################################

	@classmethod
	def _check(self):
		return Pool.check()

	@classmethod
	def _checkDelay(self):
		return Pool.checkDelay(lock = True)

	def _checkInterval(self, mode = None):
		reloading = bool(self.reloadingMedia())
		background = mode == MetaCache.RefreshBackground

		if reloading: delay = Pool.DelayMedium
		elif background: delay = Pool.DelayShort
		else: delay = False

		return Pool.check(delay = delay, lock = background or reloading)

	##############################################################################
	# CACHE
	##############################################################################

	def _cache(self, cache_, refresh_, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cacheClear' if refresh_ else cache_, *args, **kwargs)

	def _cacheTimeout(self, timeout_, refresh_, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cache', None, timeout_, refresh_, *args, **kwargs)

	def _cacheRetrieve(self, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cacheRetrieve', *args, **kwargs)

	def _cacheDelete(self, *args, **kwargs):
		self.mCache.cacheDelete(*args, **kwargs)

	def _cacheTime(self, *args, **kwargs):
		return self.mCache.cacheTime(*args, **kwargs)

	def _cacheInitialize(self, mode = Cache.ModeDefault, delay = Cache.DelayLong):
		self.mCache = Cache.instance(mode = mode, delay = delay)
		return self.mCache

	##############################################################################
	# JOB
	##############################################################################

	def job(self):
		return self.mJob

	def jobBusy(self, media = None, count = 0, foreground = True, background = False, none = False):
		type = []
		if foreground: type.append(MetaCache.RefreshForeground)
		if background: type.append(MetaCache.RefreshBackground)
		if none: type.append(None)
		for i in type:
			if (not media or media in self.mJob[i]['media']) and self.mJob[i]['count'] > count: return True
		return False

	def jobCount(self, media = None, foreground = True, background = False, none = False):
		count = 0
		type = []
		if foreground: type.append(MetaCache.RefreshForeground)
		if background: type.append(MetaCache.RefreshBackground)
		if none: type.append(None)
		for i in type:
			if not media or media in self.mJob[i]['media']: count += self.mJob[i]['count']
		return count

	def jobReset(self):
		self.mJob = {
			None						: {'count' : 0, 'media' : [], 'content' : None},
			MetaCache.RefreshForeground	: {'count' : 0, 'media' : [], 'content' : None},
			MetaCache.RefreshBackground	: {'count' : 0, 'media' : [], 'content' : None},
		}

	def _jobUpdate(self, media, foreground = None, background = None, none = None, content = None, hint = None):
		multiplier = 1
		foreign = not self.mLanguage == Language.CodeEnglish

		pack = None
		if hint and hint.get('pack'): pack = MetaPack.instance(pack = hint.get('pack'))

		# Estimate the number of subrequests per media type.
		# The detailed request count can be found in each _metadataXXXUpdate() function.
		if media == Media.Movie:
			if self.mDetail == MetaTools.DetailEssential: multiplier = 3 if foreign else 2
			elif self.mDetail == MetaTools.DetailStandard: multiplier = 7 if foreign else 6
			elif self.mDetail == MetaTools.DetailExtended: multiplier = 9 if foreign else 8
		elif media == Media.Show:
			if self.mDetail == MetaTools.DetailEssential: multiplier = 3 if foreign else 2
			elif self.mDetail == MetaTools.DetailStandard: multiplier = 5 if foreign else 4
			elif self.mDetail == MetaTools.DetailExtended: multiplier = 9 if foreign else 8
		elif media == Media.Season:
			# The exact number of seasons are not known beforehand.
			count = 0
			if pack: count = pack.countSeasonTotal()
			if not count: count = 10
			if self.mDetail == MetaTools.DetailEssential: multiplier = count + 2
			elif self.mDetail == MetaTools.DetailStandard: multiplier = ((2 * count) if foreign else count) + 3
			elif self.mDetail == MetaTools.DetailExtended: multiplier = ((4 * count) if foreign else (3 * count)) + 7
		elif media == Media.Episode:
			# The exact number of episodes are not known beforehand.
			count = 0
			if pack: count = pack.countEpisodeOfficial(season = hint.get('season'))
			if not count: count = 15
			if self.mDetail == MetaTools.DetailEssential: multiplier = count + 3
			elif self.mDetail == MetaTools.DetailStandard: multiplier = count + 3
			elif self.mDetail == MetaTools.DetailExtended: multiplier = (2 * count) + 5
		elif media == Media.Pack:
			if self.mDetail == MetaTools.DetailEssential: multiplier = 3
			elif self.mDetail == MetaTools.DetailStandard: multiplier = 4
			elif self.mDetail == MetaTools.DetailExtended: multiplier = 5
		elif media == Media.Set:
			if self.mDetail == MetaTools.DetailEssential: multiplier = 2
			elif self.mDetail == MetaTools.DetailStandard: multiplier = 3
			elif self.mDetail == MetaTools.DetailExtended: multiplier = 3

		# Episodes from multiple shows.
		# Eg: Progress menu.
		# No accurate counts available. Just mutiply the number of shows in the menu with the default count.
		if hint and hint.get('count'): multiplier *= hint.get('count')

		if not foreground is None:
			self.mJob[MetaCache.RefreshForeground]['count'] += foreground * multiplier
			self.mJob[MetaCache.RefreshForeground]['media'].append(media)
			if not content is None: self.mJob[MetaCache.RefreshForeground]['content'] = content

		if not background is None:
			self.mJob[MetaCache.RefreshBackground]['count'] += background * multiplier
			self.mJob[MetaCache.RefreshBackground]['media'].append(media)
			if not content is None: self.mJob[MetaCache.RefreshBackground]['content'] = content

		if not none is None:
			self.mJob[None]['count'] += none
			self.mJob[None]['media'].append(media)
			if not content is None: self.mJob[None]['content'] = content

	@classmethod
	def _jobTimer(self, start = True):
		# Only calculate the time if the code is actually executing, since there can be sleeps in between from _check().
		return Time(start = start, mode = Time.ModeMonotonic)

	##############################################################################
	# BUSY
	##############################################################################

	'''
		Scenario 1:

			a. Clear the local metadata.db and load a show menu (eg: Highest Rated).
			b. Since no local metadata is available, the metadata is now retrieved from script.gaia.metadata, returned immediately, and the new metadata is retrieved/refreshed in the background.
			c. When the menu is loaded/decorated, in playback.py -> _historyItems() -> each show in the list is retrieved again individually with Shows().metadata(...).
			d. This causes eg 50 separate calls to Shows().metadata(), each of them retrieving the metadata from script.gaia.metadata and refreshing the metadata in the background for a second time.
			e. The metadata is refreshed in the background again, since the original background threads for retrieving the metadata have not yet finished and have not written to MetaCache.
			f. In metadataUpdate() the Memory class is used to check if there are multiple concurrent requests to the same show, and let any subsequent request wait and then just use the cached data without making all the provider requests again.
			g. However, just starting background threads in metadata(), just for them to exit shortly after being started, requires a lot of time, making the "cached" menu still load slowly.

			To solve this, we check if metadata is already retrieved by another thread, BEFORE starting the new background threads.
			This is done with a local Memory variable, and will therefore only work for calls from within the same process/interpreter.
			If eg loading the menu twice (either double clicking by accident, or opening a menu, immediately going back and then reopening the menu before the previous call fully finished), multiple interpreters are started and this detection will not work, since the class variable is not shared.
			In that case, bad luck, make the background threads start twice. New metadata retrieval should still be skipped inside the thread in metadataUpdate() where Memory is used.
			We could use Memory(kodi = True) to make this work across interpreters, but the time it takes for looking up and setting the global Kodi variable might not be worth the effort, and would only be used very few times.

		Scenario 2:

			Previously "local = True, kodi = False" was used.
			This can make metadata being retrieved/generated duplicate times across multiple Python processes/invokers, wasting resources and time.

			a. A large pack is outdated (eg One Piece or Pokémon).
			b. Open the show Progress menu. Since the pack is outdated, it will be retrieved/generated in the background when the menu is opened.
			c. Open any episode submenu in the Progress menu. Then navigate back to the main Progress menu.
			d. Since the pack is very large, it takes 30-60 secs to generate. But since we go back to the main Progress menu, the pack is needed again for the menu, retrieved from cache, and since it is still outdated, it will be retrieved/generated again.
			e. Now the large pack is generated twice (or even more), since it takes a long time to create the pack, and multiple Python processes/invokers have initiated a refresh of the pack before the previous generation was completed.

			It is therefore insufficient to only use local memory, since Python processes/invokers do not share that memory.
			Hence, use "local = False, kodi = True" to allow checking across multiple Python processes.
			Do not use "local = True, kodi = True", otherwise a process will first retrieve the local values, although the global values might have been recently updated by another process.

			The performance implication is negligible.
			The busy functions are only called when metadata is actually being refreshed. But when up-to-date metadata is retrieved from the cache, these functions are not called.
			Using local memory takes about 0.5ms per item, while global memory takes 0.8ms per item.
			More info under _busyBenchmark().
	'''

	def _busyStart(self, media, item):
		try:
			# Use a timestamp instead of just setting a boolean.
			# In case something goes wrong with the global memory, we do not want to never update again until Kodi is restarted and the memory is cleared.
			# If the value is older than a few minutes, assume it is an outdated value and do not use it.
			time = Time.timestamp()
			limit = (time - 300) # 5 minutes.
			busy = False

			# Atomic operation to read and possibly write the memory value.
			# Otherwise we read the memory in one process, then another process updates the values, only for the first process to overwrite the memory containing the new value with the later _busySet().
			self._busyLock()

			# All IDs stored as a single JSON object.
			if self.mBusyMultiple:
				data = self._busyGet(initialize = True)
				if data:
					for provider in self.mBusyProvider:
						try:
							id = self._busyId(item = item, provider = provider)
							if id:
								value = data[media][provider].get(id)
								if value:
									if value > limit: busy = True
									break
						except: pass
				if not busy:
					changed = False
					for provider in self.mBusyProvider:
						try:
							id = self._busyId(item = item, provider = provider)
							if id:
								if not media in data: data[media] = {}
								if not provider in data[media]: data[media][provider] = {}
								data[media][provider][id] = time
								changed = True
						except: pass
					if changed: self._busySet(data = data)

			# IDs stored as individual values.
			else:
				ids = self._busyIds(media = media, item = item)
				for id in ids:
					data = self._busyGet(id = id, initialize = True)
					if data:
						if data > limit: busy = True
						break
				if not busy:
					for id in ids:
						self._busySet(id = id, data = time)

			self._busyUnlock()

			if busy:
				developer = self._metadataDeveloper(item = item)
				if developer: Logger.log('METADATA BUSY [%s]: %s' % (media.upper(), developer))

			return busy
		except: Logger.error()
		return None

	def _busyFinish(self, media, item):
		try:
			if self.mBusyMultiple:
				for provider in self.mBusyProvider:
					try:
						id = self._busyId(item = item, provider = provider)
						if id: self.mBusyRemove.append({'media' : media, 'provider' : provider, 'id' : id})
					except: pass
			else:
				ids = self._busyIds(media = media, item = item)
				if ids: self.mBusyRemove.extend(ids)

			if self.mBusyRemove:
				if self.mBusyThreaded:
					self._busyLock()
					if not self.mBusyThread or self.mBusyThread.finished():
						self.mBusyThread = Pool.thread(target = self._busyRemove, kwargs = {'wait' : self.mBusyWait})
						self._busyUnlock()
						self.mBusyThread.start()
					else:
						self._busyUnlock()
				else:
					self._busyRemove(wait = False)

			try: del item[MetaCache.Attribute][MetaCache.AttributeBusy]
			except: pass
		except: Logger.error()

	def _busyRemove(self, wait = False):
		try:
			if self.mBusyRemove:
				if wait: Pool.wait(delay = 30.0)

				self._busyLock()
				remove = self.mBusyRemove
				self.mBusyRemove = []

				if self.mBusyMultiple:
					changed = False
					data = self._busyGet()
					for i in remove:
						try:
							del data[i['media']][i['provider']][i['id']]
							changed = True
						except: pass
					if changed: self._busySet(data = data)
				else:
					for id in remove:
						self._busyClear(id = id)

				self._busyUnlock()
		except: Logger.error()

	def _busyId(self, item, provider):
		id = item.get(provider)
		if not id:
			try: id = item['id'][provider]
			except: pass
		if id and Media.isEpisode(item.get('media')): id += '_' + str(item.get('season'))
		return id

	def _busyIds(self, media, item):
		ids = []
		try:
			for provider in self.mBusyProvider:
				id = self._busyId(item = item, provider = provider)
				if id: ids.append(MetaManager.PropertyBusy + '_' + str(media) + '_' + provider + '_' + str(id))
		except: Logger.error()
		return ids

	def _busyGet(self, id = None, initialize = False):
		id = id or MetaManager.PropertyBusy
		if not self.mBusyMultiple and self.mBusyGlobal:
			# Slightly faster than using Memory, since there is no JSON-encoding.
			data = System.windowPropertyGet(id)
			if data: data = int(data)
		else:
			data = Memory.get(fixed = id, local = not self.mBusyGlobal, kodi = self.mBusyGlobal)

		if initialize and data is None:
			data = {}
			self._busySet(id = id, data = data)
		return data

	def _busySet(self, data, id = None):
		id = id or MetaManager.PropertyBusy
		if not self.mBusyMultiple and self.mBusyGlobal:
			# Slightly faster than using Memory, since there is no JSON-encoding.
			System.windowPropertySet(id, str(data))
		else:
			Memory.set(fixed = id, value = data, local = not self.mBusyGlobal, kodi = self.mBusyGlobal)

	def _busyClear(self, id = None):
		id = id or MetaManager.PropertyBusy
		if not self.mBusyMultiple and self.mBusyGlobal:
			System.windowPropertyClear(id)
		else:
			Memory.clear(fixed = id, local = not self.mBusyGlobal, kodi = self.mBusyGlobal)

	def _busyLock(self):
		self.mBusyLock.acquire()

	def _busyUnlock(self):
		self.mBusyLock.release()

	def _busyBenchmark(self):
		# When measuring the execution time in _busyFinish() in a live situation, the duration can be very long, from 10-90 secs.
		# Even when using different types of timers, the execution time seems way too long, sometimes even longer than the entire Python process time (which is obviously incorrect).
		# However, the total execution time to load a menu does not seem to be greatly affected by using the _busyXxx() functions, even with global memory.
		# The inaccurate time measurements might be due to other reasons, like the threading and locking in _metadataCache() and _metadataXxxUpdate(), Python interleaving threads, etc.
		# Rather run this function to benchmark the actual time it takes to read/write value to global memory.
		#
		# Results:
		#	Multiple: Batch IDs are faster for 50 items or less, but single IDs are faster if there are more items. Most of the time there will be considerably less than 50 items being loaded at the same time.
		#	Threaded: Non-threaded is slightly faster than threaded, depending on how many items are loaded at the same time.
		#
		# Using batch IDs can also slow down slightly over time.
		# Sometimes a few IDs remain in the dict. This can happen if the ID of the base item changes if detailed metadata is retrieved. Or if a process is canceled before _busyRemove() is called.
		# This is not a huge issue, since this will only be few IDs. But if the user does not restart Kodi for a while, this dict can grow in size.
		# On the other hand, if single IDs are used, then there will be a lot more global Kodi properties, which can slow down lookup a bit.

		limit = 50
		media = Media.Show
		items = self.discover(media = media, niche = Media.Prestige, limit = limit)['items']
		Logger.log('BUSY MEMORY BENCHMARK: %i Items' % limit)

		benches = [
			{'label' : 'Default (Default Configuration)',											'multiple' : None, 'global' : None, 'threaded' : None},

			# Only works between threads within the same Python process/invoker.
			{'label' : 'Local (Local Memory | Threads | Batch IDs | Non-Threaded)',					'multiple' : True, 'global' : False, 'threaded' : False},
			{'label' : 'Local (Local Memory | Threads | Batch IDs | Threaded)',						'multiple' : True, 'global' : False, 'threaded' : True},
			{'label' : 'Local (Local Memory | Threads | Single IDs | Non-Threaded)',				'multiple' : False, 'global' : False, 'threaded' : False},
			{'label' : 'Local (Local Memory | Threads | Single IDs | Threaded)',					'multiple' : False, 'global' : False, 'threaded' : True},

			# Works between threads within the same Python process/invoker and between different Python processes/invokers.
			{'label' : 'Global (Global Memory | Processes+Threads | Batch IDs | Non-Threaded)',		'multiple' : True, 'global' : True, 'threaded' : False},
			{'label' : 'Global (Global Memory | Processes+Threads | Batch IDs | Threaded)',			'multiple' : True, 'global' : True, 'threaded' : True},
			{'label' : 'Global (Global Memory | Processes+Threads | Single IDs | Non-Threaded)',	'multiple' : False, 'global' : True, 'threaded' : False},
			{'label' : 'Global (Global Memory | Processes+Threads | Single IDs | Threaded)',		'multiple' : False, 'global' : True, 'threaded' : True},
		]

		# Initialize
		threads = [Pool.thread(target = self._busyStart, kwargs = {'media' : media, 'item' : item}) for item in items]
		[thread.start() for thread in threads]
		[thread.join() for thread in threads]
		threads = [Pool.thread(target = self._busyFinish, kwargs = {'media' : media, 'item' : item}) for item in items]
		[thread.start() for thread in threads]
		[thread.join() for thread in threads]
		if self.mBusyThread and not self.mBusyThread.finished(): self.mBusyThread.join()
		self.mBusyThread = None
		self._busyClear()
		for item in items:
			for id in self._busyIds(media = media, item = item):
				self._busyClear(id = id)

		for bench in benches:
			if not bench['global'] is None:
				self.mBusyMultiple = bench['multiple']
				self.mBusyGlobal = bench['global']
				self.mBusyThreaded = bench['threaded']
				self.mBusyWait = False

			total = 0
			interations = 20
			for i in range(interations):
				timer = self._jobTimer()

				threads = [Pool.thread(target = self._busyStart, kwargs = {'media' : media, 'item' : item}) for item in items]
				[thread.start() for thread in threads]
				[thread.join() for thread in threads]

				threads = [Pool.thread(target = self._busyFinish, kwargs = {'media' : media, 'item' : item}) for item in items]
				[thread.start() for thread in threads]
				[thread.join() for thread in threads]

				if self.mBusyThread and not self.mBusyThread.finished(): self.mBusyThread.join()
				self.mBusyThread = None

				total += timer.elapsed(True)

				self._busyClear()
				for item in items:
					for id in self._busyIds(media = media, item = item):
						self._busyClear(id = id)
				Time.sleep(0.3)

			duration = int(total / interations)
			tab = '\t'
			if len(bench['label']) <= 64: tab += '\t'
			if len(bench['label']) <= 56: tab += '\t'
			if len(bench['label']) <= 45: tab += '\t\t\t'
			space = ''
			if duration < 100: space += ' '
			if duration < 10: space += ' '
			Logger.log(bench['label'] + ':%sTotal: %s%d ms | Item: %.2f ms ' % (tab, space, duration, duration / limit))
			Time.sleep(1)

	##############################################################################
	# PROVIDER
	##############################################################################

	def providers(self, id = None):
		if self.mProviders is None:
			self.mProviders = {
				MetaTrakt.id() : MetaTrakt,
				MetaImdb.id() : MetaImdb,
				MetaTmdb.id() : MetaTmdb,
			}
		return self.mProviders.get(id) if id else self.mProviders

	def providerName(self, id):
		provider = self.providers(id = id)
		return provider.name() if provider else None

	def provider(self, content = None, media = None, niche = None, keyword = None, release = None, genre = None, certificate = None, company = None, studio = None, network = None, award = None, gender = None, ranking = None, **parameters):
		providers = self.providers()

		trakt = MetaTrakt.id()
		imdb = MetaImdb.id()
		tmdb = MetaTmdb.id()
		weight = {i : 0 for i in providers.keys()}

		extra = 10
		full = 3
		good = 2
		poor = 1
		none = -1000

		# Basic support for TMDb.
		if Media.isSet(media): return [tmdb]
		elif content == MetaManager.ContentSearch: weight[tmdb] = poor
		else: weight[tmdb] = none

		# EXPLORE
		# If sorting is involved, prefer IMDb over Trakt, since Trakt cannot sort by most attributes.
		# If no sorting is involved, prefer Trakt over IMDb, since IMDb has a page limit.
		if Media.isAll(niche):
			# Prefer Trakt, since it has no page limit.
			weight[trakt]	+= full
			weight[imdb]	+= poor
		elif Media.isNew(niche):
			# Prefer IMDb, since Trakt returns few links and has no proper paging.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isHome(niche):
			# Prefer Trakt, since it has better home release dates.
			weight[trakt]	+= full
			weight[imdb]	+= poor
		elif Media.isBest(niche):
			# Prefer IMDb, since it has better ratings.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isWorst(niche):
			# Prefer IMDb, since it can sort by rating.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isPrestige(niche):
			# Prefer Trakt, since it has no page limit.
			weight[trakt]	+= full
			weight[imdb]	+= poor
		elif Media.isPopular(niche):
			# Prefer IMDb, since it has more votes.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isUnpopular(niche):
			# Prefer IMDb, since it can sort by votes.
			weight[trakt]	+= poor
			weight[imdb]	+= full
		elif Media.isViewed(niche):
			# Prefer Trakt, since it uses the actual watches, not the vote count.
			weight[trakt]	+= full
			weight[imdb]	+= poor
		elif Media.isGross(niche):
			# Trakt does not have any finacial details.
			weight[trakt]	+= none
			weight[imdb]	+= poor
		elif Media.isAward(niche):
			# Trakt does not have any award details.
			weight[trakt]	+= none
			weight[imdb]	+= poor
		elif Media.isTrend(niche):
			# Trakt's Trending enpoint is more current/temporary, since it shows the titles currently watched by users.
			# IMDb's Moviemeter also incorporates trends, but a lot seems to be based on the rating/votes.
			# Prefer IMDb, because the other explore menus already use Trakt a lot.
			weight[trakt]	+= poor
			weight[imdb]	+= good

		if release:
			if release == MetaProvider.ReleaseFuture:
				weight[trakt]	+= good
				weight[imdb]	+= poor		# Mostly only has year, but no full premiere date.

		if genre:
			genres = self.mTools.genre()
			if not Tools.isList(genre): genre = [genre]
			for i in genre:
				i = genres.get(i)
				if i and i['support'].get(media):
					m = i['provider']
					for p in weight.keys():
						v = m.get(p, {}).get(media, False)
						if v is True: weight[p] += good
						elif v is None: weight[p] += poor
						elif v is False: weight[p] += none
				else: # Unsupport genre by media or all providers.
					for p in weight.keys():
						weight[p] += none

			# Only IMDb supports AND genres.
			# Trakt ORs genres.
			if Media.isTopic(niche) or Media.isMood(niche): weight[trakt] += none

		# Trakt can only filter by year, which is the cur rent year and might already be released titles.
		if Media.isFuture(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra

		# Trakt has few titles listed for Sports/Sporting-Event.
		if Media.isSport(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to use IMDb for Explore, eg All Releases.

		# IMDb can search by primary language/country, whereas Trakt searches any language/country.
		# Hence, many unrelated titles show up when using Trakt (eg: Germanic cinema lists almost no German movies).
		if Media.isRegion(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb has a separate keyword parameter, whereas Trakt adds it to the search query.
		if keyword or Media.isPleasure(niche):
			# Do not do this atm. IMDb might have separate keywords, but the results return too many un or less related titles.
			# Eg: for "Cannabis", IMDb returns few stoners movies and a ton of titles where weed might have only be mentioned once, whereas Trakt returns mostly stoner movies.
			# Plus we can search multiple keywords on Trakt (ORed).
			#weight[trakt]	+= poor
			#weight[imdb]	+= extra
			weight[trakt]	+= extra
			weight[imdb]	+= full

		# IMDb has its own media type for miniseries.
		# Trakt hasw a mini-series genre, but there are 0 titles listed under it.
		if Media.isMini(niche):
			weight[trakt]	+= poor # Still allow it, in case the genre ever starts to work on Trakt.
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb (1m titles): has more titles listed under its "Shorts" and "TV Shorts" media types.
		# Trakt (330k titles): has way less titles listed under its "Short" genre. Hence, shorts are retrieved from Trakt using the duration parameter.
		if Media.isShort(niche):
			# IMDb has 6k+ shows listed under the "Short" genre.
			# Trakt only has 3 shows listed under the "Short" genre.
			if Media.isSerie(media):
				weight[trakt]	+= poor # Still allow it, in case the genre ever starts to work on Trakt.
				weight[imdb]	+= extra # Add double to force using IMDb.
			else:
				weight[trakt]	+= good
				weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb (50k titles): has more titles listed under its "TV Specials" media type.
		# Trakt (1k titles): has way less titles listed under, since it uses the "Holiday" genre and extra keywords in the query.
		if Media.isSpecial(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb (150k titles): has more titles listed under its "TV Movies" media type.
		# Trakt (1k titles): has way less titles listed under, since it uses extra keywords in the query.
		if Media.isTelevision(niche):
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb has more titles listed for studios than Trakt.
		# Trakt has a "network" parameter, but very few titles are listed under it and it only works for shows.
		# IMDb has a hacky way of searching by a network and excluding other rival companies, that works well enough.
		# Trakt is also more accurate, since IMDb can list the same company as studio, network, or other producer or distributor.
		company = MetaProvider.company(niche = niche, company = company, studio = studio, network = network)
		if company:
			if content == MetaManager.ContentSearch:
				weight[trakt]	+= good
				weight[imdb]	+= full
			else:
				networked = False
				advanced = False
				types = [MetaProvider.CompanyVendor, MetaProvider.CompanyProducer, MetaProvider.CompanyBroadcaster, MetaProvider.CompanyDistributor, MetaProvider.CompanyOriginal]
				for k, v in company.items():
					if MetaProvider.CompanyNetwork in v: networked = True
					elif any(i in types for i in v): advanced = True
				if networked and Media.isFilm(media):
					weight[trakt]	+= poor
					weight[imdb]	+= extra
				elif advanced:
					weight[trakt]	+= good
					weight[imdb]	+= extra

		if award:
			weight[trakt]	+= poor if award in [MetaTools.AwardTop100, MetaTools.AwardTop250, MetaTools.AwardTop1000, MetaTools.AwardBottom100, MetaTools.AwardBottom250, MetaTools.AwardBottom1000] else none
			weight[imdb]	+= extra # Add double to force using IMDb.

		if ranking:
			weight[trakt]	+= poor
			weight[imdb]	+= extra # Add double to force using IMDb.

		# IMDb often has titles not on Trakt/TMDb/TVDb yet. Eg: the unreleased Avatar movies ("Avatar 5").
		# When searching with IMDb (eg: query=avatar), titles are returned that do not have detailed metadata (eg: duration), since they are not on Trakt/etc yet, making the menu look ugly.
		# It is therefore better to use Trakt, where the search results look cleaner, having all the durations.
		# Plus IMDb's results deviate quickly from the search query, whereas Trakt has more accurate results at the top.
		if content == MetaManager.ContentSearch:
			if media == Media.List:
				weight[trakt]	+= full
				weight[imdb]	+= none
			elif not company:
				weight[trakt]	+= full
				weight[imdb]	+= good

		# Trakt does not have images for people. IMDb does.
		# Update: Trakt now has images in their API, including for people.
		# However, Trakt does not sort the people (eg by popularity). Hence, mostly unknown and Indian actors are returned. So stick with IMDb, which sorts people by popularity.
		# Only IMDb can lookup by gender.
		if media == Media.Person or content == MetaManager.ContentPerson:
			weight[imdb]	+= full
			weight[trakt]	+= none if (gender or award) else poor

		# IMDb does not support seasons at all
		if Media.isSeason(media): weight[imdb] = none

		# IMDb does support episodes, but the discover/search does not return the episode number, only the show and episode titles and IDs.
		# Additionally, IMDb episode searches often contain multiple (different) episodes from the same show, instead of episodes from all different shows.
		elif Media.isEpisode(media): weight[imdb] = poor

		return [i[0] for i in Tools.listSort(weight.items(), key = lambda i : i[1], reverse = True) if i[1] >= 0]

	##############################################################################
	# PROVIDER - USAGE
	##############################################################################

	@classmethod
	def providerUsage(self, authenticated = False, full = False, provider = None, cache = False):
		return MetaProvider.usageGlobal(authenticated = authenticated, full = full, provider = provider, cache = cache)

	# NB: "authenticated = None" by default to get the total of both authenticated and unauthenticated requests.
	# Update (2025-12): Trakt now does not allow a combined total of 2000 for authenticated/unauthenticated anymore. Only use the unauthenticated total now.
	@classmethod
	def providerUsageTotal(self, authenticated = False, full = False, provider = None, cache = False):
		return self.providerUsage(authenticated = authenticated, full = full, provider = provider, cache = cache)

	@classmethod
	def providerUsageTrakt(self, authenticated = False, cache = False):
		return self.providerUsage(provider = MetaTrakt, authenticated = authenticated, cache = cache)

	@classmethod
	def providerUsageTmdb(self, authenticated = False, cache = False):
		return self.providerUsage(provider = MetaTmdb, authenticated = authenticated, cache = cache)

	@classmethod
	def providerUsageTvdb(self, authenticated = False, cache = False):
		return self.providerUsage(provider = MetaTvdb, authenticated = authenticated, cache = cache)

	@classmethod
	def providerUsageImdb(self, authenticated = False, cache = False):
		return self.providerUsage(provider = MetaImdb, authenticated = authenticated, cache = cache)

	@classmethod
	def providerUsageFanart(self, authenticated = False, cache = False):
		return self.providerUsage(provider = MetaFanart, authenticated = authenticated, cache = cache)

	##############################################################################
	# PROVIDER - ERROR
	##############################################################################

	@classmethod
	def providerError(self, full = False, provider = None, cache = False):
		return MetaProvider.errorGlobal(full = full, provider = provider, cache = cache)

	@classmethod
	def providerErrorTrakt(self, cache = False):
		return self.providerError(provider = MetaTrakt, cache = cache)

	@classmethod
	def providerErrorTmdb(self, cache = False):
		return self.providerError(provider = MetaTmdb, cache = cache)

	@classmethod
	def providerErrorTvdb(self, cache = False):
		return self.providerError(provider = MetaTvdb, cache = cache)

	@classmethod
	def providerErrorImdb(self, cache = False):
		return self.providerError(provider = MetaImdb, cache = cache)

	@classmethod
	def providerErrorFanart(self, cache = False):
		return self.providerError(provider = MetaFanart, cache = cache)

	##############################################################################
	# PROVIDER - WAIT
	##############################################################################

	@classmethod
	def providerWait(self, full = False, provider = None, cache = False):
		return MetaProvider.waitGlobal(full = full, provider = provider, cache = cache)

	@classmethod
	def providerWaitTrakt(self, cache = False):
		return self.providerWait(provider = MetaTrakt, cache = cache)

	@classmethod
	def providerWaitTmdb(self, cache = False):
		return self.providerWait(provider = MetaTmdb, cache = cache)

	@classmethod
	def providerWaitTvdb(self, cache = False):
		return self.providerWait(provider = MetaTvdb, cache = cache)

	@classmethod
	def providerWaitImdb(self, cache = False):
		return self.providerWait(provider = MetaImdb, cache = cache)

	@classmethod
	def providerWaitFanart(self, cache = False):
		return self.providerWait(provider = MetaFanart, cache = cache)

	##############################################################################
	# PROCESS
	##############################################################################

	def _process(self, media, items, parameters = None, filter = False, sort = False, order = False, page = False, limit = False, more = None, unknown = None):
		try:
			if items:
				# Filter
				if filter:
					full = Tools.isInteger(more) and len(items) == more
					if filter.get(MetaTools.FilterDuplicate) is True and (Media.isSeason(media) or Media.isEpisode(media)): filter[MetaTools.FilterDuplicate] = {'number' : True}
					items = self.mTools.filter(items = items, filter = filter, unknown = unknown)
					if full: more = len(items) # Update smart paging, eg: Anime filtered Progress menu.

				# Sort
				if sort or order: items = self.mTools.sort(items = items, sort = sort, order = order, inplace = True)

				# Limit
				if not page is False: items = self._limitPage(media = media, items = items, page = page, limit = limit, more = more, parameters = parameters)
				elif limit: items = self._limitItems(media = media, items = items, limit = limit, parameters = parameters)
		except: Logger.error()
		return items

	def _processAggregate(self, media, items):
		# Certain menus contain seasons or episodes, instead of shows.
		# Eg: New Releases -> New Seasons/Episodes
		# Loading these menus as season/episode menus is very inefficient, since each entry is from a different show and would have to retrieve/generate pack metadata and full episode/season/show metadata.
		# Just create these menus as show menus with some additional metadata/labels from the season/episode.
		# This then only requires the show metadata retrieval, and only if the user clicks on a shopw, is the full pack/season metadata loaded.
		# Note that Trakt and IMDb return different structures in this case.

		if Media.isSeason(media) or Media.isEpisode(media):
			result = []

			for item in items:
				try: show = item['temp'][MetaTrakt.id()]['detail']['show']
				except: show = None

				try: premiere = item['time'][MetaTools.TimePremiere]
				except: premiere = None
				if not premiere:
					premiere = item.get('aired') or item.get('premiered')
					if premiere: premiere = Time.timestamp(premiere, format = Time.FormatDate, utc = True)

				# Trakt metadata.
				if show:
					season = item.get('season')
					if not season is None: show['season'] = season

					episode = item.get('episode')
					if not episode is None: show['episode'] = episode

					if premiere:
						if not show.get('time'): show['time'] = {}
						show['time'][MetaTools.TimeCustom] = premiere

					result.append(show)

				# IMDb metadata.
				# Does not have season/episode numbers.
				elif not Media.isShow(item.get('metadata')):
					item['media'] = Media.Show
					if premiere:
						if not item.get('time'): item['time'] = {}
						item['time'][MetaTools.TimeCustom] = premiere
					result.append(item)

			items = result
		else:
			for item in items:
				if not item.get('media'): item['media'] = media
				try: premiere = item['time'][MetaTools.TimePremiere]
				except: premiere = None
				if not premiere:
					premiere = item.get('premiered')
					if premiere:
						if not item.get('time'): item['time'] = {}
						item['time'][MetaTools.TimePremiere] = Time.timestamp(premiere, format = Time.FormatDate, utc = True)

		return items

	def _processor(self, media = None, niche = None, release = None, year = None, date = None, genre = None, language = None, country = None, certificate = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, strict = None):
		if filter is None: filter = {}

		niche = Tools.copy(niche)
		if not niche: niche = []
		nicheFilter = []
		if ranking: niche.append(ranking)

		if page is None: page = 1
		if limit is None: limit = self.limit(media = media)

		if Media.isAll(niche):
			sort = MetaTools.SortNone
		elif Media.isNew(niche):
			sort = MetaTools.SortNewest
			filter[MetaTools.FilterTime] = MetaTools.TimeLaunch
		elif Media.isHome(niche):
			sort = MetaTools.SortLatest
			filter[MetaTools.FilterTime] = MetaTools.TimeHome
		elif Media.isBest(niche):
			sort = MetaTools.SortBest
		elif Media.isWorst(niche):
			sort = MetaTools.SortWorst
		elif Media.isPrestige(niche):
			sort = MetaTools.SortNone
		elif Media.isPopular(niche):
			sort = MetaTools.SortPopular
		elif Media.isUnpopular(niche):
			sort = MetaTools.SortUnpopular
		elif Media.isViewed(niche):
			sort = MetaTools.SortNone
		elif Media.isGross(niche):
			sort = MetaTools.SortNone
		elif Media.isAward(niche):
			sort = MetaTools.SortNone
		elif Media.isTrend(niche):
			sort = MetaTools.SortNone

		if Media.isTopic(niche): filter[MetaTools.FilterGenre] = self.mTools.nicheTopic(niche = niche, strict = strict)
		elif Media.isMood(niche): filter[MetaTools.FilterGenre] = self.mTools.nicheMood(niche = niche)

		if Media.isKid(niche): filter[MetaTools.FilterKid] = True
		elif Media.isTeen(niche): filter[MetaTools.FilterTeen] = True

		if Media.isRegion(niche):
			region = self.mTools.nicheRegion(niche = niche)
			if region.get('language'): filter[MetaTools.FilterLanguage] = region.get('language')
			elif region.get('country'): filter[MetaTools.FilterCountry] = region.get('country')

		if Media.isQuality(niche): filter[MetaTools.FilterRating] = {'include' : self.mTools.nicheQuality(niche = niche, media = media), 'deviation' : True}

		if Media.isAge(niche): filter[MetaTools.FilterTime] = {'include' : self.mTools.nicheAge(niche = niche, format = True), 'time' : MetaTools.TimeLaunch, 'deviation' : True}

		if release:
			if MetaProvider.ReleaseNew in release:
				if sort is None: sort = MetaTools.SortNewest
				filter[MetaTools.FilterTime] = {'include' : [None, Time.format(format = Time.FormatDate)], 'time' : MetaTools.TimeLaunch, 'deviation' : True}
			elif MetaProvider.ReleaseHome in release:
				if sort is None: sort = MetaTools.SortLatest
				filter[MetaTools.FilterTime] = {'include' : [None, Time.format(format = Time.FormatDate)], 'time' : MetaTools.TimeHome, 'deviation' : True}
			elif MetaProvider.ReleaseFuture in release:
				if sort is None: sort = MetaTools.SortOldest
				filter[MetaTools.FilterTime] = {'include' : [Time.future(days = 1, format = Time.FormatDate), None], 'time' : MetaTools.TimeLaunch, 'deviation' : False}

		# Trakt sometimes returns titles that do not fall within the date range.
		# This is because dates can vary greatly between providers, such as which date (premiere/limited/theatrical/digital) is used as the release, or there being big gaps between these different dates.
		# Set "deviation = True" to allow some margin during filtering. Titles who's dates are a little bit off will be acepted, only only dates that are far off will be filtered out.
		if date:
			# Do not filter if we only retrieve a single day.
			# Otherwise in most cases ALL titles get filtered out, since more accurate release dates are retrieved from TMDb, which are mostly not the exact requested date.
			if not(Tools.isArray(date) and len(date) == 2 and date[0] == date[1]):
				filter[MetaTools.FilterTime] = {'include' : date, 'time' : MetaTools.TimeHome if Media.isHome(niche) else MetaTools.TimeLaunch, 'deviation' : True}

		if genre:
			if not Tools.isArray(genre): genre = [genre]
			genre = [i for i in genre if not i == MetaTools.GenreNone] # Do not filter by "None" genre.
			if genre:
				if filter.get(MetaTools.FilterGenre): filter[MetaTools.FilterGenre].extend(genre)
				else: filter[MetaTools.FilterGenre] = genre

		if language:
			if filter.get(MetaTools.FilterLanguage): filter[MetaTools.FilterCountry].extend(language if Tools.isArray(language) else [language])
			else: filter[MetaTools.FilterLanguage] = language if Tools.isArray(language) else [language]

		if country:
			if filter.get(MetaTools.FilterCountry): filter[MetaTools.FilterCountry].extend(country if Tools.isArray(country) else [country])
			else: filter[MetaTools.FilterCountry] = country if Tools.isArray(country) else [country]

		if certificate:
			if filter.get(MetaTools.FilterCertificate): filter[MetaTools.FilterCertificate].extend(certificate if Tools.isArray(certificate) else [certificate])
			else: filter[MetaTools.FilterCertificate] = certificate if Tools.isArray(certificate) else [certificate]

		if award:
			if sort is None:
				if award in [MetaTools.AwardTop100, MetaTools.AwardTop250, MetaTools.AwardTop1000]: sort = MetaTools.SortBest
				elif award in [MetaTools.AwardBottom100, MetaTools.AwardBottom250, MetaTools.AwardBottom1000]: sort = MetaTools.SortWorst

		return {
			'niche' : niche,
			'filter' : filter or None,
			'sort' : sort,
			'order' : order,
			'page' : page,
			'limit' : limit,
		}

	# Should not be used if the list comes from a niche-filtered provider request (normal menus), since that should be enough to be included in the menu, even if their detailed metadata has some values missing, like a secondary company or genre, or discrepancies in other values (eg: network "CBS" vs "CBS All Access" are both "cbs" in the niche).
	# Only use for smart Progress menus, where we want to exclude non-niche history items.
	def _processorNiche(self, niche = None, filter = None, generic = False):
		if filter is None: filter = {}

		# Only add this for niches if specifically requested.
		# Since studios/networks might be missing from the metadata, or the name has discrepancies (eg: "CBS" vs "CBS All Access").
		# Used for Progress menus.
		if niche:
			niche = Media.stringFrom(niche)

			if generic:
				exclude = []

				# Only use the company ID, not the company type, otherwise too few might be returned.
				exclude.extend([Media.Original, Media.Producer, Media.Broadcaster, Media.Distributor])

				niche = Tools.copy(niche) # Copy in order not to edit the original.
				for i in exclude: niche = Media.remove(media = niche, type = i)

			value = filter.get(MetaTools.FilterNiche)
			filter[MetaTools.FilterNiche] = [] # Do not edit the original niche list.

			if value:
				value = Media.stringFrom(value)
				if Tools.isArray(value): filter[MetaTools.FilterNiche].extend(value)
				else: filter[MetaTools.FilterNiche].append(value)

			if Tools.isArray(niche): filter[MetaTools.FilterNiche].extend(niche)
			else: filter[MetaTools.FilterNiche].append(niche)

		return filter

	def _processorFilter(self, media = None, niche = None, niched = None, year = None, date = None, genre = None, language = None, country = None, certificate = None, award = None, ranking = None, rating = None, votes = None, page = None, limit = None, strict = None):
		return self._processor(media = media, niche = niche, niched = niched, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, page = page, limit = limit, strict = strict).get('filter')

	def _processorSort(self, media = None, niche = None, year = None, date = None, genre = None, language = None, country = None, certificate = None, award = None, ranking = None, rating = None, votes = None, page = None, limit = None, strict = None):
		return self._processor(media = media, niche = niche, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, page = page, limit = limit, strict = strict).get('sort')

	def _processorOrder(self, media = None, niche = None, year = None, date = None, genre = None, language = None, country = None, certificate = None, award = None, ranking = None, rating = None, votes = None, page = None, limit = None, strict = None):
		return self._processor(media = media, niche = niche, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, page = page, limit = limit, strict = strict).get('order')

	##############################################################################
	# LIMIT
	##############################################################################

	def limit(self, media = None, content = None, submenu = None):
		if not media in self.mLimits: self.mLimits[media] = {}
		if not content in self.mLimits[media]:
			limit = 50
			if content == MetaManager.ContentSearch:
				limit = self.mTools.settingsPageSearch()
			elif content == MetaManager.ContentProgress:
				limit = self.mTools.settingsPageProgress()
			elif submenu:
				if self.mTools.submenuIsEpisode(submenu = submenu): limit = self.mTools.settingsPageSubmenu()
				elif self.mTools.submenuIsSequential(submenu = submenu): limit = self.mTools.settingsPageAbsolute()
				elif self.mTools.submenuIsAbsolute(submenu = submenu): limit = self.mTools.settingsPageAbsolute()
				else: limit = self.mTools.settingsPageSerie()
			else:
				if media is None or Media.isMixed(media): limit = self.mTools.settingsPageMixed()
				elif Media.isEpisode(media): limit = self.mTools.settingsPageEpisode()
				elif Media.isSeason(media): limit = self.mTools.settingsPageEpisode()
				elif Media.isSerie(media): limit = self.mTools.settingsPageShow()
				else: limit = self.mTools.settingsPageMovie()
			self.mLimits[media][content] = limit
		return self.mLimits[media][content]

	def _limitItems(self, items, limit = None, media = None, parameters = None):
		try:
			if limit is True or limit is None: limit = self.limit(media = media, content = parameters.get('content'))
			if limit: return items[:limit]
		except: Logger.error()
		return items

	# more: True = force add a More menu, False = never add a More menu, None = add a More menu if there are enough items, Integer = add a More menu if there are enough items, the value is the total/maximum titles in a fixed list that is not paged through an API.
	def _limitPage(self, items, page = None, limit = None, more = None, media = None, parameters = None):
		try:
			parent = False
			content = None
			submenu  = False
			season = None
			episode = None
			offset = None

			if parameters:
				parent = True
				if page is None and 'page' in parameters:
					try: page = int(parameters['page'])
					except: pass
				if limit is None and 'limit' in parameters:
					try: limit = int(parameters['limit'])
					except: pass
				content = parameters.get('content')
				submenu = parameters.get('submenu')
				season = parameters.get('season')
				episode = parameters.get('episode')
				offset = parameters.get('offset')
			else:
				parameters = {}

			if page is None or page is True: page = 1
			if limit is None or limit is True: limit = self.limit(media = media, content = content, submenu = submenu)

			total = None
			if more and Tools.isInteger(more):
				total = more
				more = None
			elif not more is True:
				total = len(items)
				if total == limit: total = None

			# Filter out any specials that were already shown on the previous page.
			# Only allow specials after the last special of the previous page.
			if submenu and offset:
				for i in range(len(items)):
					item = items[i]
					if item.get('season') == 0 and item.get('episode') == offset:
						items = [item for j, item in enumerate(items) if not item.get('season') == 0 or j > i]
						break

			if self.mTools.submenuIsEpisode(submenu = submenu):
				history = self.mTools.submenuHistory()

				# Use the actual episode we want to watch, not the values passed in by parameters, which are offsetted by submenuHistory().
				# Only do this for the 1st page where we add the history.
				if page <= 1:
					count = 0
					for item in items:
						if item.get('season') > 0:
							count += 1
							if count > history:
								season = item.get('season')
								episode = item.get('episode')
								break

				# Sometimes there are too many specials at the end of a season, which prevents a submenu from opening at the correct last watched episode.
				# Eg: It's Always Sunny in Philadelphia - watch all episodes until and including S07E01.
				# If one opens the submenu, one expects S07E02 to be listed.
				# However, it still lists S06E11+ with all the specials at the end of S06, requiring to go to the next page before finding S07.
				# Not sure if this impacts any other operations, like flatten series menus, etc.
				# Another example: Bunch of specials at the end of GoT S07.
				try:
					# Still keep the actual history episodes one might want to rewatch.
					include = []
					for i in range(0, min(history, len(items))):
						if items[i].get('season') > 0:
							include.append(items[i])

					actual = -1
					for i in range(history, len(items)):
						if items[i].get('season') > 0:
							actual = i + 1
							break

					if actual > 0 and actual > limit: items = Tools.listUnique(include + items[actual - history - 1:]) # The same item can be in both "include" and the sub-array. Remove duplicate references.
				except: Logger.error()

				# Limit the maximum number of specials before the 1st official episode to 3.
				# Otherwise the submenu under Progress might only show 10 specials, and the user has to page to the next page to get the actual episode to watch.
				try:
					if (not page or page == 1) and not season is None and not episode is None:
						exclude = []
						for i in range(len(items)):
							item = items[i]
							if item.get('season') == 0: exclude.append(i)
							elif item.get('season') == season and item.get('episode') == episode: break

						# Keep the last (probably the most relevant) specials, preceeding the 1st episode.
						# Remove the older specials that exceed "history" count, namely all specials before the ones we exclude in the previous statement.
						exclude = exclude[:len(exclude) - history]
						if exclude: items = [i for j, i in enumerate(items) if j not in exclude]
				except: Logger.error()

				# If the menu limit is so small that it is lower than the "irrelevant" previously-watched episodes and specials, start removing the earlier ones.
				# Eg: menu limit is 6, but there are 3 specials + 3 previously-watched episodes, filling the menu, so that the actual episode of interest is cut off at position 7+.
				# This will cut away both episodes and specials, until the episode of interest is in the menu.
				try:
					if limit:
						index = -1
						for i in range(len(items)):
							item = items[i]
							if item.get('season') == season and item.get('episode') == episode:
								index = i
								break
						if index >= 0 and index >= limit: items = items[index - limit + 1:]
				except: Logger.error()

			if total and limit and len(items) > limit:
				if submenu: items = items[0 : limit] # Do not apply the page for episode submenus, since they have their own internal paging system.
				else: items = items[(page - 1) * limit : page * limit]

			page += 1
			parameters['page'] = page
			parameters['limit'] = limit

			# Arbitrary paging for episode submenus.
			if submenu and parameters:
				item = None
				for i in reversed(items):
					# Ignore Recaps, Extras, and Specials for series menu.
					# Ignore "sequential" marked specials in the Absolute menu. Eg: Downtown Abbey S06E09.
					if Media.isEpisode(i.get('media')) and (i.get('season') or i.get('season') == season) and not i.get('sequential'):
						item = i
						break
				if item:
					ranged = self._metadataEpisodeRange(pack = item.get('pack'), season = season, episode = episode, limit = limit, number = submenu)
					if ranged:
						if self.mTools.submenuIsSequential(submenu = submenu) or self.mTools.submenuIsAbsolute(submenu = submenu):
							seasonLast = 1
							episodeLast = ranged[submenu]['last']
						else:
							seasonLast = ranged['season']['last']
							episodeLast = ranged['episode']['last']
						if (not seasonLast is None and item['season'] >= seasonLast) and (not episodeLast is None and item['episode'] >= episodeLast): more = False

				# Some shows are only available on IMDb, and have only one episode listed there (eg: tt31566242, tt30346074).
				# Do not add More if there is only one episode in the Series menu.
				if more is None and len(items) > 1: more = True

			if more is None and limit:
				count = len(items)
				offset = page * limit
				if count >= limit and not total and not content == MetaManager.ContentEpisode:
					more = True
				elif total:
					last = Math.roundUpClosest(total, base = limit)
					if count >= limit and offset <= last: more = True
					elif count and offset >= last: more = False

			parameters['more'] = bool(more is True and parent)
		except: Logger.error()
		return items

	##############################################################################
	# RELOAD
	##############################################################################

	# Prevent multiple reloads running at the same time, or shortly after each other.
	@classmethod
	def _lock(self, mode, media, content, update = True, delay = None, force = False):
		id = 'GaiaManagerReload'

		# Reload from global var, in case another Python process updated the values.
		data = Memory.get(id = id, local = False, kodi = True)
		if not data:
			data = {
				'refresh' : {
					Media.Show	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Movie	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Mixed	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
				},
				'reload' : {
					Media.Show	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Movie	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Mixed	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
				},
				MetaManager.Smart : {
					Media.Show	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Movie	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
					Media.Mixed	: {MetaManager.ContentQuick : 0, MetaManager.ContentProgress : 0, MetaManager.ContentArrival : 0},
				},
			}

		time = Time.timestamp()
		timeout = 180 # 3 minutes.

		if force or (time - data[mode][media][content]) > timeout:
			data[mode][media][content] = time
			if update: Memory.set(id = id, value = data, local = True, kodi = True)

			if delay is None: delay = False if mode == MetaManager.Smart else True
			if delay: Time.sleep(0.03) # Add short sleeps in between, to allow some breating space so that other threads/code can execute.

			return True
		return False

	@classmethod
	def _lockRefresh(self, media, content, update = True, delay = None, force = False):
		return self._lock(mode = 'refresh', media = media, content = content, update = update, delay = delay, force = force)

	@classmethod
	def _lockReload(self, media, content, update = True, delay = None, force = False):
		return self._lock(mode = 'reload', media = media, content = content, update = update, delay = delay, force = force)

	@classmethod
	def _lockSmart(self, media, content, update = True, delay = None, force = False):
		return self._lock(mode = MetaManager.Smart, media = media, content = content, update = update, delay = delay, force = force)

	##############################################################################
	# RELOAD
	##############################################################################

	# Called from playback.py, which in turn is called from trakt.py.
	# history = only update lists/items that are affected by changes in the history (a title was watched/unwatched).
	# progress = only update lists/items that are affected by changes in the progress (a title's unfinished playback progress).
	# arrival = only update lists/items that are affected by changes in the arrivals.
	# bulk = only update the IMDb bulk data. This takes very long and should only be done during launch.
	# launch = if True the call to this function was made during Kodi launch. If False, it was called from somewhere else, such as during binging. This can be used to only execute certain computationally expensive code during boot.
	# delay = whether or not to delay the cache refreshes for the lists by a few seconds in order not to hold up other processes. If False, immediately refresh the cache without waiting.
	@classmethod
	def reload(self, media = None, history = False, progress = False, rating = False, arrival = False, release = None, bulk = False, accelerate = False, launch = False, delay = False, force = False):
		if not self._checkDelay(): return False

		# This function should never be called from the singleton, since its changes the cache delay, and sets self.mReloadBusy.
		# Read the comment below for self.mReloadBusy.
		if self == MetaManager.instance():
			Logger.log('Reloading the menus should never be done with MetaManager.instance().', type = Logger.TypeFatal)
			return False

		if not media:
			for i in [Media.Show, Media.Movie, Media.Mixed]:
				self.reload(media = i, history = history, progress = progress, rating = rating, arrival = arrival, launch = launch, delay = delay, force = force)
			return True

		# Do not use the singleton.
		# Create a custom instance that expires at the end of the call.
		# Since we change the cache and set various member variables that do not change back.
		# By default, do not delay.
		# Since this function is called directly after playback ended, and the cache data should immediately be refreshed.
		# The Kodi menu currently shown might be the one that needs reloading, and the newly refreshed cache data should immediately be available if the Kodi container/menu is reloaded.
		# Do not use DelayNone, but DelayDisable, since we do not want to use threads at all in the cache.
		# Otherwise if we make the refresh calls below, internally they might threaded cache functions still executing, while we already continue to the reload call, which assumes the refresh calls are done and it can directly retrieve from cache.
		# Eg: The progress data might be outdated, which will immediately return the data and then refresh in a background cache thread. The code continues to the reload call, and the reload call will ALSO refresh the data, since the previous refresh call has not finished and updated the cache entry.
		mode = []
		if accelerate: mode.append(MetaManager.ModeAccelerate)
		if not delay: mode.append(MetaManager.ModeUndelayed)
		manager = MetaManager(mode = mode)
		developer = manager.mDeveloper

		# During mixed menu reloads, just retrieve the smart data from cache without causing the cached function to possibly refresh and execute again.
		# Otherwise, if we eg reload during binge watching after an episode is watched, then the show menus are reloaded, and in the end the mixed menus as well.
		# This might then cause the movie menu code to be refreshed/executed, especially if the cache timeout for that menu is very low (eg Quick).
		# Hence, if we refresh movies, only movie menu functions should execute, but not any show functions, and vice versa.
		# If we reload mixed menus, then the internally used data should already be refreshed from a previous call. We should not trigger and possible internal refreshes by calling the cached function with a timeout.
		# Eg: Reload shows after an episode playback finished, this happens:
		#	1. The show Progress/Quick data is refreshed.
		#	2. The show Progress/Quick outer menus from content() are reloaded.
		#	3. The outer mixed menus from content() are reloaded. This will use the refreshed show data from #1, and the "old" movie data from cache from whenever it was last refreshed.
		#	4. At no point during this process should any movie cache-function execute or any movie smart-reloads happen.
		# Sometimes titles from the other media can still be re-retrieved in the background. Namely if a mixed menu is reloaded from content(), it loads the detailed metadata of all titles from page 1 to add them to the cache for quicker access.
		# If the metadata of these titles is outdated, they will be refreshed in the background. Although this should not happen too often.
		manager.mReloadMedia = media

		# Refresh the IMDb bulk metadata.
		# This can take 3-5+ minutes on a high-end device, and 10-15+ minutes on a low-end device.
		# Only do this during launch and not during other calls in between, such as after playback ended or when a menu is opened.
		# Otherwise the device might slow down during binging in case the bulk cache timeout is triggered at that point.
		# Only refresh during Kodi launch to reduce the impact of the downlaoding/processing.
		# No need to check the "launch" parameter, since "bulk" is only set to True during launch.
		# Do this first, since it takes long, might need a restart once done, and its updated data might be needed for the metadata refreshes below.
		if bulk and Media.isMixed(media):
			if not self._checkDelay(): return False
			if developer: Logger.log('RELOAD: Refreshing Bulk Data ...')
			manager.bulkImdbRefresh(reload = True, wait = True) # Do not set "refresh = True" to force a refresh. Only refresh if the cache timeout was reached in MetaImdb.

		if not Media.isMixed(media):
			if (history or progress) and self._lockRefresh(media = media, content = MetaManager.ContentProgress, force = force):
				if not self._checkDelay(): return False
				if developer: Logger.log('RELOAD: Refreshing %s Progress ...' % media.capitalize())
				manager.progress(media = media, refresh = True)

			if arrival and self._lockRefresh(media = media, content = MetaManager.ContentArrival, force = force):
				if not self._checkDelay(): return False
				if developer: Logger.log('RELOAD: Refreshing %s Arrivals ...' % media.capitalize())
				manager.arrival(media = media, refresh = True)

			if (history or progress) and self._lockRefresh(media = media, content = MetaManager.ContentQuick, force = force):
				if not self._checkDelay(): return False
				if developer: Logger.log('RELOAD: Refreshing %s Quick ...' % media.capitalize())
				manager.quick(media = media, refresh = True) # Do this last, since it uses the data of the other functions.

			if release or (release is None and (progress or arrival)):
				if not self._checkDelay(): return False
				if developer: Logger.log('RELOAD: Refreshing %s Releases ...' % media.capitalize())
				manager.release(media = media, refresh = True)

		# Reload the cached first page. This is quick, since no full refresh is done.
		# Also do if ratings were updated, to display the user rating in the progress menu after the rating dialog at the end of playback.
		# Do this AFTER all the refresh calls, otherwise it would prevent them from smart-reloading.
		manager.mReloadBusy = True # Prevent smart-reloads if we only reloading the cached menu.

		if (history or progress or rating) and self._lockReload(media = media, content = MetaManager.ContentProgress, force = force):
			if not self._checkDelay(): return False
			if developer: Logger.log('RELOAD: Reloading %s Progress ...' % media.capitalize())
			manager.progress(media = media, reload = True)

		if arrival and self._lockReload(media = media, content = MetaManager.ContentArrival, force = force):
			if not self._checkDelay(): return False
			if developer: Logger.log('RELOAD: Reloading %s Arrivals ...' % media.capitalize())
			manager.arrival(media = media, reload = True)

		if (history or progress or rating) and self._lockReload(media = media, content = MetaManager.ContentQuick, force = force):
			if not self._checkDelay(): return False
			if developer: Logger.log('RELOAD: Reloading %s Quick ...' % media.capitalize())
			manager.quick(media = media, reload = True) # Do this last, since it uses the data of the other functions.

		# Do not disable here again.
		# The reloading in content() will execute the cache function in a background thread that might be delayed (egv GIL switching between threads).
		# Hence, we can already reach this statement before those threads are executed and get to the smart-reload part that checks this variable.
		# This might then cause smart-reloads we do not want if the thread timing is just right.
		# Therefore, the reload() function should NEVER be called by the singleton MetaManager.instance().
		# Create a csutom MetaManager object which is ONLY use for calling the reload() function, and should be discarded afterwards, since it will never smart-reload again.
		#manager.mReloadBusy = False

		return True

	def reloading(self, busy = True, quick = True, mixed = True):
		if busy and self.mReloadBusy: return True
		if quick and self.mReloadQuick: return True
		if mixed and Media.isMixed(self.mReloadMedia): return True
		return False

	def reloadingMixed(self):
		return self.reloading(busy = False, quick = False, mixed = True)

	def reloadingMedia(self):
		return self.mReloadMedia

	##############################################################################
	# PRELOAD
	##############################################################################

	# clean: remove old/unused metadata records from MetaCache that have a different settings ID.
	@classmethod
	def preload(self, callback = None, clean = None):
		try:
			progress = 0.0
			def _progress(percent = None, tasks = None, part = None, status = None, detail = None):
				if part:
					if not percent: percent = 0
					if Tools.isArray(tasks): tasks = len(tasks)
					elif not tasks: tasks = 1
					percent = progress + ((percent + 1) / float(tasks) * part)
				self._batchProgress(percent = percent, status = status, detail = detail)

			def _update():
				while True:
					if self._batch('status', 'cool'): _progress(status = 'Cooling Down Requests', detail = 'Pausing retrievals to give APIs some breathing space.')
					if self._batchCanceled(skip = False):
						self._batchStop()
						return
					Time.sleep(1)

			def _base(data, media = False, season = False):
				result = {'imdb' : data.get('imdb'), 'tmdb' : data.get('tmdb'), 'tvdb' : data.get('tvdb'), 'trakt' : data.get('trakt'), 'title' : data.get('tvshowtitle') or data.get('title'), 'year' : data.get('tvshowyear') or data.get('year')}
				if media:
					mediad = data.get('media')
					if media is True and Media.isSerie(mediad): mediad = Media.Show
					result['media'] = mediad
				if season: result['season'] = data.get('season')
				return result

			# limit=False: return all items.
			# internal=True: in order not to use the outer cache data from content().
			parameters = {'refresh' : True, 'pack' : False, 'detail' : False, 'limit' : False, 'internal' : True}

			batch = self._batchStart(strict = True, callback = callback, status = 'Initializing Smart Menus', detail = 'Preparing smart menus for metadata retrieval.')
			Pool.thread(target = _update, start = True)

			# MetaManager:
			#	Use ModeSynchronous to wait for threads.
			# 	Make all MetaCache retrievals execute in the foreground.
			# 	Make smart-reloads execute in the foreground.
			# 	This makes sure any internal threads are completed before moving to the next task.
			# MetaCache:
			# 	Use ModeUndelayed to wait for the cache functions to finish, instead of executing them in a background thread.
			# 	This makes sure any cache threads are completed before moving to the next task.
			manager = MetaManager(mode = [MetaManager.ModeSynchronous, MetaManager.ModeUndelayed]) # Do not use MetaManager.instance(), since we change the cache mode and delay.

			# On low-end devices there are major performance issues during preloading.
			performance = manager.mPerformance
			performanceGood = performance > 0.65
			performanceMedium = performance >= 0.3 and performance < 0.65
			performanceBad = performance < 0.3

			# Low-end devices are considerably slower. Use less iterations.
			iterated = {
				'initial' : 1,
				'extended' : 4 if performanceGood else 3 if performanceMedium else 2,
				'final' : {
					# These later reloads on low-end devices only take 2-15secs.
					# And note that a lot of items which were already preloaded in "extended" are reset again with _metadataSmartRenew(). A few more iterations might therefore not hurt.
					'skip' : 7 if performanceGood else 5 if performanceMedium else 3,
					'unskip' : 10 if performanceGood else 7 if performanceMedium else 5,
					'quick' : 1,
				},
				'reload' : {
					'skip' : 3 if performanceGood else 2 if performanceMedium else 1,
					'unskip' : 4 if performanceGood else 3 if performanceMedium else 2,
				},
			}

			# Reduce the chunk size for low-end devices. This reduces the number of threads being used.
			chunked = {
				'lookup' : 50 if performanceGood else 40 if performanceMedium else 30,
				Media.Movie : 25 if performanceGood else 20 if performanceMedium else 15, # Movies + Shows.
				Media.Set : 30 if performanceGood else 25 if performanceMedium else 20,
				Media.Season : 5 if performanceGood else 4 if performanceMedium else 3, # Seasons + Packs. Do not make the chunk too large, since packs and detailed metadata for all seasons are retrieved.
				Media.Episode : 4 if performanceGood else 3 if performanceMedium else 2, # Do not make the chunk too large, since some seasons can contain many episodes.
			}

			from lib.modules.playback import Playback
			from lib.modules.interface import Format
			from lib.meta.menu import MetaMenu

			# Try reducing the number of threads where possible.
			# This is important for low-end devices, which can sometimes run out of threads during the the detailed metadata retrieval phase.
			threaded = False

			current = Time.timestamp()
			cache = MetaCache.instance()
			playback = Playback.instance()
			items = []
			movies = []
			shows = []
			sets = {'trakt' : {}, 'tmdb' : {}, 'imdb' : {}}

			stepProgress = 0
			stepArrival = 0
			stepQuick = 0

			detailProgress = '%s custom %s %s menu based on your Trakt history.'
			detailArrival = '%s custom %s %s menu from multiple sources.'
			detailReleaseMovie = '%s internal release calendar for new movies.'
			detailReleaseShow = '%s internal release calendar for your Trakt shows.'

			status = 'Initializing Metadata Cache'
			detail = 'Preparing the metadata cache for preloading.'
			_progress(0, status = status, detail = detail)
			if clean: Time.sleep(10) # Wait for cache clearing to finish with the database.

			# SYNC TRAKT DATA
			if not self._batchCanceled():
				part = 0.03
				if playback._traktEnabled():
					self._batchStep(trakt = 0.0)
					tasks = [
						{'media' : Media.Movie},
						{'media' : Media.Show},
					]
					for i, task in enumerate(tasks):
						media = task.get('media')
						status = 'Synchronizing Trakt %ss' % media.title()
						detail = 'Retrieving your Trakt %s history, progress, and ratings.' % media
						_progress(i, tasks = tasks, part = part, status = status, detail = detail)

						playback.refresh(media = task.get('media'), history = True, progress = True, rating = True, force = True, reload = False, wait = True)
						self._batchStep(trakt = (i + 1) / len(tasks))
						if not self._batchCool(): break
					self._batchStep(trakt = 1.0)
					self._batchCool()
				progress += part

			# IMDB BULK DATA
			# NB: Do not load the bulkdata here, especially not before preloading.
			# On low-end devices, once the bulkdata update is done, the preloading runs super slow.
			# This is not ideal, since the perloaded metadata will not be using the bulkdata (only if they are later refreshed), but this is just a limitations to accept.
			# Do the bulkdata at the end, just before the restart.
			# If enabled again, make sure to the progress parts add up to 100 (with the additional 5% here).
			'''if not self._batchCanceled():
				part = 0.05
				if self._bulkImdbEnabledSettings():
					self._batchStep(imdb = 0.0)

					status = 'Collecting IMDb Data'
					detail = 'Creating IMDb bulk dataset with IDs, numbers, and ratings.'
					_progress(part = part, status = status, detail = detail)

					manager.bulkImdbRefresh(refresh = None, silent = None, wait = True) # refresh=None to semi-force a refresh, without refreshing it every time this function is called, in case the user continues preloading the next day.
					self._batchStep(imdb = 1.0)
					self._batchCool()
				progress += part
			'''

			# METACACHE CLEAN
			# Removes old/unused metadata records from the cache that have a different settings ID in the database.
			# This is only done if "clean" is enabled, which is currently only done on major versions upgrades.
			# This would then clear old data during version upgrades and reduce the database size.
			part = 0.02
			if not self._batchCanceled():
				if clean:
					status = 'Clearing Old Metadata'
					detail = 'Removing old metadata records from the cache.'
					cache.clearOld()
			progress += part

			# ARRIVALS AND PROGRESS
			# Basic/quick creation of the Arrivals and Progress smart-data, which is used for the release calendar.
			if not self._batchCanceled():
				part = 0.05
				iterations = iterated['initial']
				tasks = [
					{'media' : Media.Movie,	'content' : MetaManager.ContentProgress,	'iterations' : iterations},
					{'media' : Media.Show,	'content' : MetaManager.ContentProgress,	'iterations' : iterations},
					{'media' : Media.Movie,	'content' : MetaManager.ContentArrival,		'iterations' : iterations},
					{'media' : Media.Show,	'content' : MetaManager.ContentArrival,		'iterations' : iterations},
				]
				manager.mModeAccelerate = True # To reduce the detailed metadata retrieved during smart loading. Proper loading is done later on.
				for i, task in enumerate(tasks):
					if self._batchCanceled(): break
					iterations = task.get('iterations')
					for j in range(iterations):
						if not self._batchCool(): break

						media = task.get('media')
						content = task.get('content')
						status = 'Initializing %s %ss' % (content.title(), media.title())
						if content == MetaManager.ContentProgress: detail = detailProgress
						elif content == MetaManager.ContentArrival: detail = detailArrival
						_progress(i, tasks = tasks, part = part, status = status, detail = detail % ('Constructing', media, content))

						values = manager.content(**task, **parameters)
						if values:
							values = values.get('items')
							items.append(values)
							if content == MetaManager.ContentProgress:
								if media == Media.Movie: movies.extend(values)
								elif media == Media.Show: shows.extend(values)

						step = 0.1
						if content == MetaManager.ContentProgress:
							stepProgress += step
							self._batchStep(progress = stepProgress)
						elif content == MetaManager.ContentArrival:
							stepArrival += step
							self._batchStep(arrival = stepArrival)

						if not self._batchCool(): break
				manager.mModeAccelerate = False # Reset to the original value for the remainder of the code.

				# Set the initial totals here already, so they are displayed in the window.
				# Detailed totals are calculated later.
				if not self._batchCanceled() and items:
					items = Tools.listFlatten(items, recursive = False)
					items = manager.mTools.filterDuplicate(items = items, id = True)

					itemsMovie = []
					itemsShow = []
					itemsSeason = []
					itemsEpisode = []
					itemsPack = []
					itemsSet = []

					# Count movies and shows for both Progress and Arrivals.
					totalMovie = 0
					totalShow = 0
					for item in items:
						media = item.get('media')
						if Media.isSerie(media):
							totalShow += 1
							itemsShow.append(_base(media = Media.Show, data = item, season = False))
						elif Media.isMovie(media):
							totalMovie += 1
							itemsMovie.append(_base(media = Media.Movie, data = item))
					self._batchMeta(media = Media.Movie, total = totalMovie)
					self._batchMeta(media = Media.Show, total = totalShow)

					# Count seasons, episodes, packs, and sets only for Progress, since detailed metadata below movies/shows is not loaded in Arrivals.
					for item in movies:
						try: id = item['id']['collection']['tmdb']
						except: id = None
						if id: itemsSet.append(_base(media = Media.Set, data = {'tmdb' : id}))
					for item in shows:
						itemsPack.append(_base(media = Media.Pack, data = item, season = False))
						itemsSeason.append(_base(media = Media.Season, data = item, season = False))
						itemsEpisode.append(_base(media = Media.Episode, data = item, season = False))

					# Sets these only for Progress.
					# Assume at least one season/episode per show. The exact count is increased below.
					self._batchMeta(media = Media.Set, total = len(itemsSet))
					self._batchMeta(media = Media.Pack, total = len(itemsPack))
					self._batchMeta(media = Media.Season, total = len(itemsSeason))
					self._batchMeta(media = Media.Episode, total = len(itemsEpisode))

					# Determine which metadata is already in the cache.
					# Otherwise the metadata counters stay low or even at 0 if the sequential loading is skipped and the user does not know how much is really preloaded.
					self._batchCool()
					for i in ((Media.Movie, itemsMovie), (Media.Show, itemsShow), (Media.Season, itemsSeason), (Media.Episode, itemsEpisode), (Media.Pack, itemsPack), (Media.Set, itemsSet)):
						count = 0
						tasks = Tools.listChunk(i[1], chunk = chunked['lookup'])
						for task in tasks:
							cache.lookup(type = i[0], items = task)
							if i[0] == Media.Episode: count += sum([len(MetaCache.attribute(j, MetaCache.AttributeSeason)) for j in task if MetaCache.valid(item = j)])
							else: count += sum([int(MetaCache.valid(item = j)) for j in task])
							if not self._batchCool(): break
						if not self._batchCool(): break
						self._batchMeta(media = i[0], count = count)

				self._batchCool()
				progress += part

			# RELEASE CALENDAR
			if not self._batchCanceled():
				part = 0.05
				tasks = [
					{'media' : Media.Movie},
					{'media' : Media.Show},
				]
				for i, task in enumerate(tasks):
					media = task.get('media')
					status = 'Initializing %s Calendar' % media.title()
					if media == Media.Movie: detail = detailReleaseMovie
					elif media == Media.Show: detail = detailReleaseShow
					_progress(i, tasks = tasks, part = part, status = status, detail = detail % 'Constructing')

					manager.release(media = media, refresh = True)

					self._batchStep(release = 0.5 * ((i + 1) / len(tasks)))
					if not self._batchCool(): break

				self._batchStep(release = 0.5)
				self._batchCool()
				progress += part

			# LOAD SMART MENUS
			# Do a few iterations of the smart menus before retrieving the metadata sequentially.
			# This ensures that if the user clicks the Skip button, the smart menus are at least intialized enough for basic use.
			if not self._batchCanceled():
				iterations = iterated['extended'] # Do this multiple time to retrieve more detailed metadata.
				part = 0.10
				tasks = [
					{'media' : Media.Movie,	'content' : MetaManager.ContentProgress,	'iterations' : iterations},
					{'media' : Media.Show,	'content' : MetaManager.ContentProgress,	'iterations' : iterations},
					{'media' : Media.Movie,	'content' : MetaManager.ContentArrival,		'iterations' : iterations},
					{'media' : Media.Show,	'content' : MetaManager.ContentArrival,		'iterations' : iterations},
				]

				# Reinitialize these to get more detailed-loaded metadata for from the smart menus.
				# Eg: greater chance of having Set IDs for Progress movies.
				items = []
				moviesArrival = []
				showsArrival = []
				moviesProgress = []
				showsProgress = []

				for i, task in enumerate(tasks):
					if self._batchCanceled(): break
					iterations = task.get('iterations')
					for j in range(iterations):
						if not self._batchCool(): break

						media = task.get('media')
						content = task.get('content')
						status = 'Creating %s %s' % (media.title(), content.title() + ('s' if content == MetaManager.ContentArrival else ''))
						if content == MetaManager.ContentProgress: detail = detailProgress % ('Assembling', media, content)
						elif content == MetaManager.ContentArrival: detail = detailArrival % ('Assembling', media, content)
						_progress(i, tasks = tasks, part = part, status = status, detail = detail)

						values = manager.content(**task, **parameters)

						# Add these again with hopefully more detailed metadata.
						# Only do this on the last iteration, since those will have the most metadata.
						if values and j == (iterations - 1):
							values = values.get('items')
							items.append(values)
							if content == MetaManager.ContentArrival:
								if media == Media.Movie: moviesArrival.extend(values)
								elif media == Media.Show: showsArrival.extend(values)
							elif content == MetaManager.ContentProgress:
								if media == Media.Movie: moviesProgress.extend(values)
								elif media == Media.Show: showsProgress.extend(values)

						step = 0.1
						if content == MetaManager.ContentProgress:
							stepProgress += step
							self._batchStep(progress = stepProgress)
						elif content == MetaManager.ContentArrival:
							stepArrival += step
							self._batchStep(arrival = stepArrival)

						self._batchWait(5)
				self._batchCool()
				progress += part

			# REFRESH OUTDATED ITEMS
			# Refresh outdated metadata of very new releases.
			# In case the metadata was refreshed a long time ago and has very outdated dates and ratings/votes, causing them to be added far back in the smart lists.
			# Refresh these items, but not forcefully. Then remove these with _metadataSmartRenew() from the smart-list so they get smart-reloaded with hopefully updated metadata.
			# Hopefully any missing home release dates were added at this point by _smartRelease().
			if not self._batchCanceled():
				part = 0.05
				try:
					limit = 150 # Maximum items to refresh.
					reload = current - 1209600 # Last refreshed more than 2 weeks ago.
					past = current - 3628800 # 6 weeks into the past.
					future = current + 604800 # 1 week into the future.

					for entry in ((Media.Movie, moviesArrival), (Media.Show, showsArrival)):
						status = 'Refreshing Outdated Metadata'
						detail = 'Updating old metadata for newly released %ss.' % entry[0]
						_progress(progress, status = status, detail = detail)

						itemsNew = [(manager.mTools.time(metadata = i, type = MetaTools.TimeHome, estimate = False, fallback = False) or manager.mTools.time(metadata = i, type = MetaTools.TimeDebut, estimate = True, fallback = True) or 0, i) for i in entry[1]]
						itemsPast = [i for i in itemsNew if i[0] > past and i[0] <= current]
						itemsFuture = [i for i in itemsNew if i[0] > current and i[0] < future]
						itemsNew = [i[1] for i in itemsPast] + [i[1] for i in itemsFuture]
						manager._metadataSmartRenew(media = entry[0], items = itemsNew)
						cache.lookup(type = entry[0], items = itemsNew)
						itemsNew = [i for i in itemsNew if ((i.get(MetaCache.Attribute) or {}).get(MetaCache.AttributeTime) or 999999999999) < reload] # Do not refresh items not currently cached.

						before = MetaManager.Batch['count']['load'][entry[0]]
						tasks = Tools.listChunk(itemsNew, chunk = chunked[Media.Movie])
						for i, task in enumerate(tasks):
							task = [_base(data = t, media = True, season = False) for t in task]
							_progress(i, tasks = tasks, part = part * 0.5)
							manager.metadata(items = task, pack = False, clean = False, aggregate = False, threaded = threaded)
							if not self._batchCool(): break
							if (MetaManager.Batch['count']['load'][entry[0]] - before) > limit: break # If a certain number of items were loaded, cancel the process.
				except: Logger.error()
				self._batchCool()
				progress += part

			# Only allow skipping from this point on.
			# Sleep to allow some time for the sound to play, otherwise too much CPU is used by the preloading that the sound is choppy.
			# Sleep before and after settings kip.
			self._batchWait(3)
			self._batchProgress(skip = True)
			self._batchWait(3)

			# SEQUENTIAL LOAD METADATA
			if not self._batchCanceled() and items:
				part = 0.10
				status = 'Retrieving Detailed Metadata'
				detail = 'Fetching detailed movie and show metadata.'
				_progress(progress, status = status, detail = detail)

				# Interleave Progress/Arrivals and movies/shows.
				# So that if the user skips the rest of the sequentially retrieved list, an equal number of items were retrieved over movies/shows and Progress/Arrivals.

				items = Tools.listInterleave(*items)
				items = manager.mTools.filterDuplicate(items = items, id = True)

				# For both Progress and Arrivals.
				totalMovie = 0
				totalShow = 0
				for item in items:
					media = item.get('media')
					if Media.isSerie(media): totalShow += 1
					elif Media.isMovie(media): totalMovie += 1
				self._batchMeta(media = Media.Movie, total = totalMovie)
				self._batchMeta(media = Media.Show, total = totalShow)

				# Only for Progress.
				totalSet = 0
				for item in moviesProgress:
					try:
						if item['id']['collection']['tmdb']: totalSet += 1
					except: pass
				self._batchMeta(media = Media.Set, total = totalSet)

				# Only for Progress shows.
				# Assume at least one season/episode per show. The exact count is increased below.
				totalShow = len(showsProgress)
				self._batchMeta(media = Media.Pack, total = totalShow)
				self._batchMeta(media = Media.Season, total = totalShow)
				self._batchMeta(media = Media.Episode, total = totalShow)

				# Sequentially load all metadata in chunks.
				countMovie = 0
				countShow = 0
				tasks = Tools.listChunk(items, chunk = chunked[Media.Movie])
				for i, task in enumerate(tasks):
					for t in task:
						if Media.isSerie(t.get('media')): countShow += 1
						else: countMovie += 1
					task = [_base(data = t, media = True, season = False) for t in task]

					_progress(i, tasks = tasks, part = part)
					manager.metadata(items = task, pack = False, clean = False, aggregate = False, threaded = threaded)

					# Get more set IDs, since many Progress movies have no set ID yet, because they were not smart-detailed-loaded yet.
					for j in task:
						if Media.isMovie(j.get('media')):
							try: idSet = j['id']['collection']['tmdb']
							except: idSet = None
							if idSet:
								for k, v in sets.items():
									id = j['id'].get(k)
									if id: v[id] = idSet

					self._batchMeta(media = Media.Movie, increase = countMovie)
					self._batchMeta(media = Media.Show, increase = countShow)
					if not self._batchCool(): break

				self._batchCool()
				progress += part

			# LOAD PROGRESS SETS
			if not self._batchCanceled():
				part = 0.05
				status = 'Populating Progress Sets'
				detail = 'Fetching sets for your favorite movies.'
				_progress(progress, status = status, detail = detail)

				if moviesProgress:
					tasks = []
					for i in moviesProgress:
						try: idSet = i['id']['collection']['tmdb']
						except: idSet = None
						if not idSet:
							for k, v in sets.items():
								id = i['id'].get(k)
								if id:
									idSet = v.get(id)
									if idSet: break
						if idSet: tasks.append(idSet)
					tasks = Tools.listUnique(tasks)

					if tasks:
						self._batchMeta(media = Media.Set, total = len(tasks))
						tasks = [_base(data = {'tmdb' : i}, media = Media.Set) for i in tasks]
						tasks = Tools.listChunk(tasks, chunk = chunked[Media.Set])

						if self._batchCool():
							countSet = 0
							for i, set in enumerate(tasks):
								_progress(i, tasks = tasks, part = part)
								set = manager.metadataSet(items = set, threaded = threaded)

								countSet += len(set)
								self._batchMeta(media = Media.Set, increase = countSet)
								if not self._batchCool(): break

					self._batchCool()
				progress += part

			# LOAD PROGRESS SEASONS + PACKS
			if not self._batchCanceled():
				part = 0.15
				status = 'Populating Progress Seasons'
				detail = 'Fetching seasons for your favorite shows.'
				_progress(progress, status = status, detail = detail)

				episodes = []
				totalEpisode = 0
				if showsProgress:
					# Remove season number from the progress, otherwise metadataSeason() will only retrieve that season, instead of all seasons.
					showsProgress = [_base(data = i, season = False) for i in showsProgress]

					# Do not make the chunk too large, since packs and detailed metadata for all seasons are retrieved.
					showsProgress = Tools.listChunk(showsProgress, chunk = chunked[Media.Season])

					if self._batchCool():
						countSeason = 0
						for i, show in enumerate(showsProgress):
							_progress(i, tasks = showsProgress, part = part)
							seasons = manager.metadataSeason(items = show, pack = False, threaded = threaded) # Still retrieves the pack, just does not aggregate it.
							if seasons and not self._batchCanceled():
								countSeason += len(seasons)
								self._batchMeta(media = Media.Season, increase = countSeason)

								for season in seasons:
									if season:
										values = []
										season = Tools.listSort(season, key = lambda i : 9999 if i.get('season') is None else i.get('season'))

										# Always add the specials, since they take long to load and are interleaved in Progress submenus.
										if season[0].get('season') == 0: values.append(_base(data = season.pop(0), season = True))

										# Add the first and last 5 seasons.
										limit = 5
										values.extend([_base(data = i, season = True) for i in season[:limit]])
										values.extend([_base(data = i, season = True) for i in season[-limit:]])

										if values:
											values = manager.mTools.filterDuplicate(items = values, id = True, number = True)
											if values:
												episodes.extend(values)
												try:
													totalEpisode += season['packed']['count'][MetaPack.NumberOfficial]
													self._batchMeta(media = Media.Episode, total = totalEpisode)
												except: pass

							if not self._batchCool(): break

					self._batchCool()
				progress += part

			# LOAD PROGRESS EPISODES
			if not self._batchCanceled():
				part = 0.15
				status = 'Populating Progress Episodes'
				detail = 'Fetching episodes for your favorite shows.'
				_progress(progress, status = status, detail = detail)

				if episodes and self._batchCool():
					# Do not make the chunk too large, since some seasons can contain many episodes.
					episodes = Tools.listChunk(episodes, chunk = chunked[Media.Episode])
					countEpisode = 0
					for i, episode in enumerate(episodes):
						_progress(i, tasks = episodes, part = part)
						values = manager.metadataEpisode(items = episode, pack = False, threaded = threaded)

						if values:
							countEpisode += len(values)
							self._batchMeta(media = Media.Episode, increase = countEpisode)
						if not self._batchCool(): break

				self._batchCool()
				progress += part

			# Do not allow skipping from this point on.
			self._batchProgress(skip = False)
			skip = False # Ignore skipping for certain parts.

			# In case the user skipped, add the progress up until this point.
			progress = 0.75
			_progress(progress)

			# RELEASE CALENDAR
			# Refresh the release calendar with the new fully loaded data from Arrivals and Progress used in _releaseAssemble().
			if not self._batchCanceled(skip = skip):
				part = 0.05
				tasks = [
					{'media' : Media.Movie},
					{'media' : Media.Show},
				]
				for i, task in enumerate(tasks):
					media = task.get('media')
					status = 'Finalizing %s Calendar' % media.title()
					if media == Media.Movie: detail = detailReleaseMovie
					elif media == Media.Show: detail = detailReleaseShow
					_progress(i, tasks = tasks, part = part, status = status, detail = detail % 'Refreshing')

					manager.release(media = media, refresh = True)

					self._batchStep(release = 0.5 + (0.5 * ((i + 1) / len(tasks))))
					if not self._batchCool(skip = skip): break

				self._batchStep(release = 1.0)
				self._batchCool(skip = skip)
				progress += part

			# LOAD SMART MENUS
			# Refresh the smart menus with the new fully loaded metadata.
			if not self._batchCanceled(skip = skip):
				iterations = iterated['final']['skip' if self._batchSkipped() else 'unskip']
				iterationsQuick = iterated['final']['quick']
				step = (1.0 - stepProgress) / iterations
				part = 0.10
				tasks = [
					{'media' : Media.Movie,	'content' : MetaManager.ContentProgress,	'iterations' : iterations},
					{'media' : Media.Show,	'content' : MetaManager.ContentProgress,	'iterations' : iterations},
					{'media' : Media.Movie,	'content' : MetaManager.ContentArrival,		'iterations' : iterations},
					{'media' : Media.Show,	'content' : MetaManager.ContentArrival,		'iterations' : iterations},
					{'media' : Media.Movie,	'content' : MetaManager.ContentQuick,		'iterations' : iterationsQuick},
					{'media' : Media.Show,	'content' : MetaManager.ContentQuick,		'iterations' : iterationsQuick},
				]

				for i, task in enumerate(tasks):
					if self._batchCanceled(skip = skip): break
					iterations = task.get('iterations')
					for j in range(iterations):
						if not self._batchCool(skip = skip): break

						media = task.get('media')
						content = task.get('content')
						if content == MetaManager.ContentQuick:
							status = 'Creating %s %ss' % (content.title(), media.title())
							detail = 'Assembling custom %s %s menu for swift navigation.' % (media, content)
						else:
							status = 'Finalizing %s %s' % (media.title(), content.title() + ('s' if content == MetaManager.ContentArrival else ''))
							if content == MetaManager.ContentProgress: detail = detailProgress % ('Refreshing', media, content)
							elif content == MetaManager.ContentArrival: detail = detailArrival % ('Refreshing', media, content)
						_progress(i, tasks = tasks, part = part, status = status, detail = detail)

						values = manager.content(**task, **parameters)

						if content == MetaManager.ContentQuick:
							stepQuick += 0.5
							self._batchStep(quick = stepQuick)
						else:
							if content == MetaManager.ContentProgress:
								stepProgress += step
								self._batchStep(progress = stepProgress)
							elif content == MetaManager.ContentArrival:
								stepArrival += step
								self._batchStep(arrival = stepArrival)

						self._batchWait(5, skip = skip)

				self._batchStep(progress = 1.0)
				self._batchStep(arrival = 1.0)
				self._batchStep(quick = 1.0)
				self._batchCool(skip = skip)
				progress += part

			# RELOAD CACHED MENUS
			if not self._batchCanceled(skip = skip):
				iterations = iterated['reload']['skip' if self._batchSkipped() else 'unskip']
				part = 0.05
				for i in range(iterations):
					if not self._batchCool(skip = skip): break

					status = 'Generating Smart Menus'
					detail = 'Caching custom smart menus for faster loading.'
					_progress(i, tasks = iterations, part = part, status = status, detail = detail)

					playback.reload(history = True, progress = True, rating = True, arrival = True, force = True, wait = True)

					self._batchStep(cache = (i + 1) / iterations)
					self._batchWait(5, skip = skip)
				self._batchCool(skip = skip)
				progress += part

			_progress(0.95, status = 'Finalizing Smart Menus', detail = 'Preparing the smart menus and cleaning up.')

			# Make sure everything is commited and written to disk before restarting.
			cache._commit()
			cache._compact()
			manager.mCache._commit()
			manager.mCache._compact()
			self._batchWait(30) # Wait for any thread or disk writes that might still be busy.

			MetaMenu.instance().notificationCached(delay = False, force = True)
			_progress(1.0, status = 'Smart Menus Preloaded', detail = 'The smart menus were preloaded and are now ready for use.')

			self._batchStop()
			return True
		except:
			Logger.error()
			_progress(1.0, status = 'Smart Preload Failure', detail = 'The smart menus could not be fully preloaded, but should still work.')
			self._batchStop()
			return False

	@classmethod
	def preloadCancel(self):
		self._batchStop()
		MetaImdb.bulkRefreshCancel()

	@classmethod
	def preloadSkip(self):
		self._batchSkip()

	##############################################################################
	# GENERATE
	##############################################################################

	# Generate a large metadata.db for the external metadata addon.
	@classmethod
	def generate(self, refresh = False):
		# Size (LZMA is almost the same as ZLIB (default compression) for smaller objects, but can be better for larger objects, such as packs and seasons):
		# The cleaned and ZIP-compressed addon reduces the size by a few 10MBs.
		#	Movie:		+-5KB
		#	Set:		+-2KB
		#	Show:		+-7KB
		#	Pack:		+-10KB
		#	Season:		+-20KB
		#	Episode:	+-210KB
		#	IMDb Bulk:	+-17MB (total)

		from lib.modules.tools import Settings
		from lib.modules.interface import Dialog, Format
		from lib.modules.convert import ConverterSize, ConverterDuration

		def _update():
			dialog = Dialog.progress(title = 'Metadata Generation', message = 'Initializing ...')
			cache = MetaCache.instance(generate = True)

			speed = None
			speeds = []

			while True:
				current = Time.timestamp()
				progress = self._batch('progress', 'percent')

				detail = self._batch('progress', 'detail')
				if not detail or (current - detail['time']) > 20:
					detail = cache.details()
					self._batchProgress(detail = detail)

					interval = 75 # 25+ minutes (once every 20 secs).
					total = sum([detail['count'][i] for i in [Media.Movie, Media.Set, Media.Show, Media.Season, Media.Episode, Media.Pack]])
					speeds.append((current, total))
					total = len(speeds)
					if total > interval: speeds = speeds[total - interval:]
					speed = speeds[-1][0] - speeds[0][0]
					speed = int(Math.roundUp(60 * ((speeds[-1][1] - speeds[0][1]) / float(speed)))) if speed else 0

				message = []
				message.append(Format.bold('Status: ') + '%s - %s - %d%% - %s - %d/m' % (
					Format.bold(ConverterSize(detail.get('size')).stringOptimal()),
					'Cooling Down' if self._batch('status', 'cool') else self._batch('progress', 'status'),
					int(progress * 100),
					ConverterDuration(self._batch('progress', 'time'), unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatClockShort),
					speed,
				))
				message.append(Format.bold('Usage: ') + '[B]%s%%[/B] (%d%% Trakt, %d%% IMDb, %d%% TMDb)' % (
					int(self._batch('usage', 'global') * 100),
					int(self._batch('usage', 'trakt') * 100),
					int(self._batch('usage', 'imdb') * 100),
					int(self._batch('usage', 'tmdb') * 100),
				))
				message.append(Format.bold('Films: ') + ', '.join(['%s %ss' % (Format.bold(Math.thousand(detail['count'][i])), i.title()) for i in [Media.Movie, Media.Set]]))
				message.append(Format.bold('Series: ') + ', '.join(['%s %ss' % (Format.bold(Math.thousand(detail['count'][i])), i.title()) for i in [Media.Show, Media.Season, Media.Episode, Media.Pack]]))
				message = Format.newline().join(message)

				if progress >= 1:
					dialog.update(101, message)
					self._batchStop()
					while not dialog.iscanceled(): Time.sleep(1)
					return
				else:
					dialog.update(int(progress * 100), message)

				if dialog.iscanceled():
					self._batchStop()
					return
				Time.sleep(1)

		self._batchStart(status = 'Initializing')
		thread = Pool.thread(target = _update, start = True)
		manager = MetaManager(mode = [MetaManager.ModeGenerative, MetaManager.ModeSynchronous, MetaManager.ModeUndelayed])

		# Change all the settings for the best possible metadata.
		settings = [
			'general.language.primary',
			'general.language.secondary',
			'general.language.tertiary',

			'metadata.region.language',
			'metadata.region.country'

			'metadata.rating.movie',
			'metadata.rating.movie.fallback',
			'metadata.rating.show',
			'metadata.rating.show.fallback',

			'image.location',
			'image.style.movie',
			'image.style.set',
			'image.style.show',
			'image.style.season',
			'image.style.episode',
			'image.selection.movie',
			'image.selection.set',
			'image.selection.show',
			'image.selection.season',
			'image.selection.episode',
			'image.selection.episode.show',
			'image.selection.episode.season',
			'image.selection.multiple',
			'image.selection.multiple.show',
			'image.selection.multiple.season',
			'image.special.season',
			'image.special.season.show',
			'image.special.episode',
			'image.special.episode.show',
			'image.special.episode.season',
		]
		for i in settings: Settings.default(i)
		MetaTools.settingsDetailSet(MetaTools.DetailExtended)
		MetaImdb.bulkSettingsModeSet(MetaImdb.BulkModeExtended)

		# Not all IMDb ratings are included, due to the 100MB file size limit on Github.
		# Check MetaCache.externalGenerate() for more details on how items are removed.
		self._batchProgress(status = 'Refreshing IMDb Bulk Data')
		refreshBulk = refresh
		if not refreshBulk:
			bulk = MetaCache.externalBulk()
			refreshBulk = None if (bulk and bulk > 1000) else True # refresh=None to semi-force a refresh, without refreshing it every time this function is called.
		manager.bulkImdbRefresh(refresh = refreshBulk, force = True, wait = True)

		self._batchProgress(status = 'Generating ID List')
		self._batchCool()
		items = manager._cache('cacheExtended', refresh, self._generateAssemble)
		self._batchCool()

		limit = {
			Media.Movie : 6500,
			Media.Show : 6500,
			Media.Pack : 1000,
			Media.Season : 1000, # Should be the same as the items for Media.Pack, since seasons will also retrieve/generate the pack.
			Media.Set : [2500, 1000], # [number to retrieve, number to keep after sorting by votes]
		}
		chunk = {
			# Do not make these to high (eg: 50).
			# The chunks are too , increasing the chances of hitting the Trakt API limit.
			# Smaller chunks allow more frequent cool downs in between and can therefore detect Trakt limits more quickly.
			# This number x 5, should not exceed the cool down stop limit of the total Trakt limit.
			# Eg: chunk (30) x requests-per-title (5) < cool-down-stop (1.0 - 0.8) x Trakt limit (1000)
			#		= 30x5 < (1.0-0.8)x1000
			#		= 150 < 200
			#		= allowed chunk size. max 35.
			Media.Movie : 30,
			Media.Show : 30,

			Media.Set : 50,

			Media.Pack : 15,
			Media.Season : 15,
		}

		sets = {}
		data = {}
		for i in limit.keys():
			data[i] = []
			values = items.get(Media.Show if i in [Media.Season, Media.Pack] else i)
			if values:
				limited = limit[i]
				if Tools.isArray(limited): limited = limited[0]
				values = values[:limited]
				values = Tools.copy(values) # Copy, since we change the media.
				for j in values: j['media'] = i # Change the media for seasons and packs.
				data[i] = Tools.listChunk(values, chunk = chunk[i])

		step = 0
		total = sum([len(i) for i in data.values()])
		for k, v in data.items():
			if self._batchCanceled(): break
			self._batchProgress(status = 'Generating %ss' % k.title())
			for i in v:
				step += 1
				self._batchProgress(percent = (step / total) * 0.95)
				items = manager.metadata(items = i, pack = False)
				if k == Media.Set:
					for item in items: sets[item.get('id', {}).get('tmdb')] = item.get('votes') or 0
				if not self._batchCool(): break

		# Sort sets by votes and keep the most popular ones.
		sets = dict(Tools.listSort(sets.items(), key = lambda i : i[1], reverse = True))
		sets = {i : sets[i] for i in list(sets)[:limit[Media.Set][1]]}
		sets = list(sets)

		self._batchProgress(percent = 0.95, status = 'Processing Database')
		self._batchWait(30) # Wait for any writes to the database to finish.
		MetaCache.externalGenerate(sets = sets)

		self._batchProgress(percent = 1, status = 'Finished')
		thread.join()
		self._batchStop()

		return True

	@classmethod
	def _generateAssemble(self):
		trakt = MetaTrakt.instance()

		tasks = {
			Media.Movie : {'result' : [], 'limit' : [1350, 1.4, 0.8]},
			Media.Show : {'result' : [], 'limit' : [1200, 1.6, 0.8]},
		}

		year = Time.year()
		for media, task in tasks.items():
			requests = []
			limit = task.get('limit')[0]
			offset = year

			requests.append({'year' : [offset - 3, offset], 'limit' : limit})
			offset -= 4

			limit = int(limit *  task.get('limit')[1])
			for i in range(6):
				requests.append({'year' : [offset - 9, offset], 'limit' : limit})
				offset -= 10
				limit = int(limit *  task.get('limit')[2])

			result = task.get('result')
			for i in requests:
				if i.get('limit') > 0:
					items = trakt.discover(media = media, extended = True, sort = MetaTrakt.SortPopular, **i)
					if items:
						boost = 1.5 # Increase to give recent releases a higher popularity boost.
						for item in items:
							popularity = item.get('votes') or 10
							y = item.get('year')
							if y:
								difference = abs(year - y)
								if difference <= 3: popularity *= boost * (4 - difference) # More recent releases had less time to accumulate votes.
							result.append({'popularity' : int(popularity), 'media' : media, 'imdb' : item.get('imdb'), 'tmdb' : item.get('tmdb'), 'tvdb' : item.get('tvdb'), 'trakt' : item.get('trakt'), 'title' : item.get('title')})

			task['result'] = Tools.listSort(result, key = lambda i : i['popularity'], reverse = True)

		tasks[Media.Set] = {'result' : []}
		items = MetaTmdb.instance().discoverSet()
		if items: tasks[Media.Set]['result'] = [{'media' : item.get('media'), 'tmdb' : item.get('tmdb'), 'title' : item.get('title')} for item in items]

		return {
			Media.Movie : tasks[Media.Movie]['result'],
			Media.Show : tasks[Media.Show]['result'],
			Media.Set : tasks[Media.Set]['result'],
		}

	##############################################################################
	# BATCH
	##############################################################################

	@classmethod
	def _batch(self, *key):
		result = MetaManager.Batch
		for i in key: result = result[i]
		return result

	@classmethod
	def _batchSet(self, type1, type2, value):
		MetaManager.Batch[type1][type2] = value

	@classmethod
	def _batchCanceled(self, skip = True):
		canceled = self._batch('status', 'cancel')
		if canceled: return canceled
		if skip: return self._batchSkipped()
		return False

	@classmethod
	def _batchSkipped(self):
		return self._batch('status', 'skip')

	@classmethod
	def _batchProgress(self, percent = None, status = None, detail = None, skip = None, callback = None):
		if not percent is None: self._batchSet('progress', 'percent', percent)
		if not status is None: self._batchSet('progress', 'status', status)
		if not detail is None: self._batchSet('progress', 'detail', detail)
		if not skip is None: self._batchSet('progress', 'skip', skip)
		if callback: callback(MetaManager.Batch)

	@classmethod
	def _batchStep(self, trakt = None, imdb = None, release = None, cache = None, progress = None, arrival = None, quick = None, callback = None):
		if not trakt is None: self._batchSet('step', 'trakt', trakt)
		if not imdb is None: self._batchSet('step', 'imdb', imdb)
		if not release is None: self._batchSet('step', 'release', release)
		if not cache is None: self._batchSet('step', 'cache', cache)
		if not progress is None: self._batchSet('step', MetaManager.ContentProgress, progress)
		if not arrival is None: self._batchSet('step', MetaManager.ContentArrival, arrival)
		if not quick is None: self._batchSet('step', MetaManager.ContentQuick, quick)
		if callback: callback(MetaManager.Batch)

	@classmethod
	def _batchStart(self, strict = False, status = None, detail = None, callback = None):
		# Keep start/stop close together, to more evenly spread out the requests and reduce the chances of IMDb blocking the IP.
		# When it drops below start, then a bunch of new requests are made, but we quickly cool down again if stop is hit shortly after.
		# Hence, we have smaller batches of requests with shorter cool downs. Instead of having one huge batch and then waiting very long.
		strict = 0.1 if strict else 0.0
		MetaManager.Batch = {
			'limit' : {
				# Update (2025-12):
				# Trakt now only allows 1000 req/5min for unauthenticated requests, not the additional 1000 for authenticated requests.
				# The usage measurement has been changed to now only include unauthenticated requests, so the hard limit is 1000 req/5min.
				# The start/stop limits were increased from their old values, otherwise the loading is too slow.
				# Higher limits are appropriate, since we are not working with the previous 50%-50% of auth/unauth requests, trying to keep under 50%, but the entire 100% is now the 1000 requests.
				# NB: Do not make the stop limit too high. Since a batch of 50 items can be started after this limit was reached, pushing up the Trakt limit easily 10% higher. With 85% it has been overserved that the Trakt usage can go up to 95%.
				#	'start' : [0.5 - strict, 0.75 - strict],
				#	'stop' : 0.6,
				# This works almost perfectly. Trakt limits are only hit occasionally.
				#	'start' : [0.5 - strict, 0.6 - strict], 'stop' : 0.85,
				#	'start' : [0.5 - strict, 0.7 - strict], 'stop' : 0.83,
				#	'start' : [0.5 - strict, 0.7 - strict], 'stop' : 0.80,
				#	'start' : [0.4 - strict, 0.5 - strict], 'stop' : 0.80,
				#	'start' : [0.4 - strict, 0.5 - strict], 'stop' : 0.70,
				#	'start' : [0.5 - strict, 0.6 - strict], 'stop' : 0.65, (still very occasionally reaches the limit)
				#	'start' : [0.5 - strict, 0.6 - strict], 'stop' : 0.6, (still very occasionally reaches the limit)
				# This rarley hits the limit and if so mostly with movies.
				# 30 movies/min - 35-40 shows/min - 40 packs/min - 20-25 seasons/min
				'start' : [0.5 - strict, 0.6 - strict],
				'stop' : 0.6,

				'trakt' : 3,
			},
			'usage' : {
				'global' : 0,
				'trakt' : 0,
				'imdb' : 0,
				'tmdb' : 0,
			},
			'status' : {
				'strict' : strict,
				'cool' : None,
				'cancel' : None,
				'skip' : None,
			},
			'progress' : {
				'skip' : None,
				'time' : 0,
				'percent' : 0,
				'status' : status,
				'detail' : detail,
			},
			'step' : {
				'trakt' : None, # None indicates no Trakt account is used.
				'imdb' : None, # None indicates no IMDb data is retrieved based on the metadata detail level.
				'release' : 0.0,
				'cache' : 0.0,
				MetaManager.ContentProgress : 0.0,
				MetaManager.ContentArrival : 0.0,
				MetaManager.ContentQuick : 0.0,
			},
			'count' : {
				# Items which metadata was newly retrieved or refreshed.
				'load' : {
					'all' : 0,
					Media.Movie : 0,
					Media.Show : 0,
					Media.Season : 0,
					Media.Episode : 0,
					Media.Pack : 0,
					Media.Set : 0,
					'data' : {
						Media.Movie : {},
						Media.Show : {},
						Media.Season : {},
						Media.Episode : {},
						Media.Pack : {},
						Media.Set : {},
					},
				},

				# Items which metadata was retireved and processed, with or without a refresh.
				# Values: [count, total].
				'meta' : {
					'all' : [0, 0],
					Media.Movie : [0, 0],
					Media.Show : [0, 0],
					Media.Season : [0, 0],
					Media.Episode : [0, 0],
					Media.Pack : [0, 0],
					Media.Set : [0, 0],
				},

				# Items that were processed in the smart-lists.
				# Values: [count, total].
				MetaManager.Smart : {
					'all' : {
						'all' : [0, 0],
						Media.Movie : [0, 0],
						Media.Show : [0, 0],
					},
					MetaManager.ContentProgress : {
						'all' : [0, 0],
						Media.Movie : [0, 0],
						Media.Show : [0, 0],
					},
					MetaManager.ContentArrival : {
						'all' : [0, 0],
						Media.Movie : [0, 0],
						Media.Show : [0, 0],
					},
				},
			},
		}
		Pool.thread(target = self._batchUpdate, kwargs = {'callback' : callback}, start = True)
		return MetaManager.Batch

	@classmethod
	def _batchStop(self):
		if MetaManager.Batch: self._batchSet('status', 'cancel', True)

	@classmethod
	def _batchSkip(self):
		if MetaManager.Batch: self._batchSet('status', 'skip', True)

	@classmethod
	def _batchWait(self, seconds, skip = True):
		for i in range(seconds):
			if self._batchCanceled(skip = skip): break
			Time.sleep(1)

	@classmethod
	def _batchUpdate(self, callback = None):
		timer = self._jobTimer()
		while not self._batchCanceled(skip = False): # Continue the update thread when skipped.
			MetaManager.Batch['usage'].update(self.providerUsageTotal(full = True))
			self._batchSet('progress', 'time', timer.elapsed())
			if callback: callback(MetaManager.Batch)

			if System.aborted(): self._batchStop() # If Kodi is exited.
			else: Time.sleep(1)

		countAll = self._batch('count', 'load', 'all')
		countMovie = self._batch('count', 'load', Media.Movie)
		countShow = self._batch('count', 'load', Media.Show)
		countSeason = self._batch('count', 'load', Media.Season)
		countEpisode = self._batch('count', 'load', Media.Episode)
		countPack = self._batch('count', 'load', Media.Pack)
		countSet = self._batch('count', 'load', Media.Set)
		Logger.log('BATCH LOADED (Total: %d | %ds): %d Movies | %d Shows | %d Seasons | %d Episodes | %d Packs | %d Sets' % (countAll, timer.elapsed(), countMovie, countShow, countSeason, countEpisode, countPack, countSet))

		# Clear some memory.
		for i in MetaManager.Batch['count'].keys():
			if 'data' in MetaManager.Batch['count'][i]:
				for k in MetaManager.Batch['count'][i]['data'].keys():
					MetaManager.Batch['count'][i]['data'][k] = {}

		# One last window update.
		if callback: callback(MetaManager.Batch)

	@classmethod
	def _batchLoad(self, media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None):
		try:
			if MetaManager.Batch:
				id = None
				if imdb: id = 'imdb' + str(imdb)
				elif trakt: id = 'trakt' + str(trakt)
				elif tmdb: id = 'tmdb' + str(tmdb)
				elif tvdb: id = 'tvdb' + str(tvdb)
				if id:
					id = '%s_%s_%s' % (media, id, str(season))
					count = MetaManager.Batch['count']['load']
					if not id in count['data'][media]:
						count['data'][media][id] = True
						count[media] += 1
						count['all'] += 1
		except: Logger.error()

	@classmethod
	def _batchSmart(self, content, media, total = None, count = None):
		try:
			if MetaManager.Batch:
				if Media.isSerie(media): media = Media.Show
				batch = MetaManager.Batch['count'][MetaManager.Smart]

				if not count is None and not total is None and count > total: total = count
				if not count is None: batch[content][media][0] = count
				if not total is None: batch[content][media][1] = total

				count = 0
				total = 0
				for k, v in batch[content].items():
					if not k == 'all':
						count += v[0]
						total += v[1]
				batch[content]['all'][0] = count
				batch[content]['all'][1] = total

				countMovie = 0
				countShow = 0
				totalMovie = 0
				totalShow = 0
				for k, v in batch.items():
					if not k == 'all':
						countMovie += v[Media.Movie][0]
						totalMovie += v[Media.Movie][1]
						countShow += v[Media.Show][0]
						totalShow += v[Media.Show][1]
				batch['all'][Media.Movie][0] = countMovie
				batch['all'][Media.Movie][1] = totalMovie
				batch['all'][Media.Show][0] = countShow
				batch['all'][Media.Show][1] = totalShow
				batch['all']['all'][0] = countMovie + countShow
				batch['all']['all'][1] = totalMovie + totalShow
		except: Logger.error()

	@classmethod
	def _batchMeta(self, media, total = None, count = None, increase = None):
		try:
			if MetaManager.Batch:
				batch = MetaManager.Batch['count']['meta']

				# Allows increasing the total if the new count is greater than the existing total.
				if count is None: count = batch[media][0]
				if total is None: total = batch[media][1]

				if not increase is None: count = max(count, increase)
				if not count is None and not total is None and count > total: total = count
				if not count is None: batch[media][0] = count
				if not total is None: batch[media][1] = total

				count = 0
				total = 0
				for k, v in batch.items():
					if not k == 'all':
						count += v[0]
						total += v[1]
				batch['all'][0] = count
				batch['all'][1] = total
		except: Logger.error()

	@classmethod
	def _batchCool(self, skip = True):
		if not self._batchCanceled(skip = skip):
			Time.sleep(0.02) # Allow other threads to execute, like the one updating the preload Window progress.

			usage = self._batch('usage', 'global') > self._batch('limit', 'stop')

			# Sometimes the Trakt API rate limit is reached, even with a low usage.
			# This is because the user might have loaded a lot of metadata, restarted Kodi, and the global properties are reset.
			# When the preload is started again, Trakt might return 429 errors, since the limit was reached in the previous Kodi session.
			# Also use this as an indicator to cool down.
			# Update: not really needed anymore, since we now also check providerWait(), which will have the Trakt wait duration if error 429 was hit.
			trakt = self.providerErrorTrakt() > self._batch('limit', 'trakt')

			# Update (2025-12):
			# Trakt does not return the X-Ratelimit header anymore, at least not for all requests. The Retry-After header is still returned.
			# Hence, waiting for the number of requests to dial down is not enough anymore.
			# Wait for the indicated number of seconds returned by Trakt as well.
			wait = self.providerWait()

			if usage or trakt or wait:
				self._batchSet('status', 'cool', Time.timestamp())

				for i in range(10):
					if self._batchCanceled(skip = skip): break
					Time.sleep(1)

				if not self._batchCanceled(skip = skip):
					time = Time(start = True)
					limit1 = self._batch('limit', 'start', 0)
					limit2 = self._batch('limit', 'start', 1)
					limit3 = self._batch('limit', 'trakt')
					while True:
						if self._batchCanceled(skip = skip): break

						# Only check the request counters if there is no specific wait duration by any provider (eg Trakt).
						waiting = wait and wait > Time.timestamp()
						if not waiting: # Not busy waiting.
							if usage:
								if self._batch('usage', 'global') < limit1: break
								elif self._batch('usage', 'trakt') < limit2 and self._batch('usage', 'imdb') < limit2 and self._batch('usage', 'tmdb') < limit2: break
							elif trakt:
								if self.providerErrorTrakt() < limit3: break
								if time.elapsed() > (MetaTrakt._usageDuration() + 10): break # Should not happen, but just in case the provider errors are not reset.
							else: # Done waiting and no usage/trakt errors.
								break

						for i in range(5):
							if self._batchCanceled(skip = skip): break
							Time.sleep(1)

					for i in range(5):
						if self._batchCanceled(skip = skip): break
						Time.sleep(1)

		self._batchSet('status', 'cool', False)
		return not self._batchCanceled(skip = skip)

	##############################################################################
	# BULK
	##############################################################################

	# These two parameters allow us to use the bulk data, even if the user has disabled the setting, as long as the data is available in either the internal or external database.
	# external: Use the data from the preprocessed external addon. These values might be outdated.
	# internal: Use any existing data from the metadata cache, even if the bulkdata setting was disabled later on.
	@classmethod
	def _bulkImdbEnabled(self, internal = True, external = True):
		if self._bulkImdbEnabledSettings(): return True
		if internal and self._bulkImdbInternal(): return True
		if external and self._bulkImdbExternal(): return True
		return False

	@classmethod
	def _bulkImdbEnabledSettings(self):
		return MetaImdb.instance().bulkEnabled()

	@classmethod
	def _bulkImdbInternal(self):
		return MetaCache.bulkAvailable()

	@classmethod
	def _bulkImdbExternal(self):
		return MetaCache.externalAvailable()

	# These two parameters allow us to use the bulk data, even if the user has disabled the setting, as long as the data is available in either the internal or external database.
	# external: Use the data from the preprocessed external addon. These values might be outdated.
	# internal: Use any existing data from the metadata cache, even if the bulkdata setting was disabled later on.
	def _bulkImdbLookup(self, imdb, imdbEpisode = None, season = None, episode = None, data = False, internal = True, external = True):
		if internal: internal = self._bulkImdbInternal()
		if external: external = self._bulkImdbExternal()
		force = internal or external
		return MetaImdb.instance().bulk(id = imdb, idEpisode = imdbEpisode, season = season, episode = episode, data = data, force = force, generate = self.mModeGenerative)

	#silent: If True, no dialogs/progress/notifications are shown. If False, everything is shown. If None, only error notifications are shown.
	def bulkImdbRefresh(self, force = False, refresh = False, reload = None, selection = None, generate = None, silent = False, restart = None, wait = True):
		timer = Time(start = True)
		Logger.log('BULK GENERATION: Updating IMDb bulk metadata ...')
		result = MetaImdb.instance().bulkRefresh(generate = self.mModeGenerative if generate is None else generate, force = force, refresh = refresh, reload = reload, selection = selection, silent = silent, restart = restart, wait = wait)
		if wait:
			if result is None:
				status = 'SUCCESS'
				message = 'IMDb bulk metadata still up-to-date'
			elif result:
				status = 'SUCCESS'
				message = 'IMDb bulk metadata updated'
			else:
				status = 'FAILURE'
				message = 'IMDb bulk metadata could not be updated'
			Logger.log('BULK %s (%ds): %s' % (status, timer.elapsed(), message))
		return result

	##############################################################################
	# METADATA
	##############################################################################

	# Either pass in a list of items to retrieve the detailed metadata for all of them.
	# Or pass in an ID or title/year to get the details of a single item.

	# By default, do not cache internal requests (eg: Trakt/TVDb/IMDb/Fanart API requests).
	# For a list of 50 items, this will use an additional 8-9MB of the cache (disc space), plus it takes 4 secs longer to write to disc (the entire list takes 17-25 secs).
	# There is no real reason to cache intermediary requests, since the final processed metadata is already cached with MetaCache.
	# The only reason for intermediary caching is if the metadata is imcomplete, and on subsequent menu loading, all of the show's metadata is requested again, even though some of them might have suceeded previously.

	# filter: remove uncommon movies, like those without an IMDb ID. If None, will set to True for multiple items, and to False for a single item.
	# By default, do not cache internal requests (eg: Trakt/TMDb/IMDb/Fanart API requests).
	# For a list of 50 items, this will use an additional 5MB of the cache (disc space), plus it takes 100-200 ms longer to write to disc (although this is insignificant, since the entire list takes 20-25 secs).
	# There is no real reason to cache intermediary reque7sts, since the final processed metadata is already cached with MetaCache.
	# The only reason for intermediary caching is if the metadata is imcomplete, and on subsequent menu loading, all of the movie's metadata is requested again, even though some of them might have suceeded previously.
	# quick = Quickly retrieve items from cache without holding up the process of retrieving detailed metadata in the foreground. This is useful if only a few random items are needed from the list and not all of them.
	# quick = positive integer (retrieve the given number of items in the foreground and the rest in the background), negative integer (retrieve the given number of items in the foreground and do not retrieve the rest at all), True (retrieve whatever is in the cache and the rest in the background - could return no items at all), False (retrieve whatever is in the cache and the rest not at all - could return no items at all), Dictionary {'foreground' : X, 'background' : Y} (retrieve a maximum foreground/background items).
	# threaded = If sub-function calls should use threads or not. None: threaded for single item, non-threaded for multiple items. True: threaded. False: non-threaded.

	# NB NB NB: pack
	#	Take note of the following when calling this function for shows/seasons/episode.
	#	If the pack data is not needed by the caller, pass in "pack=False".
	#	Not only will this save local resources, by not having to read from disk, decompress and JSON-decode large pack data, but also avoids unnecessary pack generation for shows where we do not really need it.
	#	Some pack generations can take 5+ seconds, due to title matching, if there are many episodes with different titles. Eg: Rick and Morty S0 (TVDb vs Trakt/TMDb).
	#	Although the data needed from provider APIs for pack creation only requires a few API calls, those calls can be very large and take a long time (eg: Trakt), since a lot of episode data is retrieved.
	#	For instance, when loading a menu with shows, do not retrieve the pack data, since otherwise it will generate pack data for every show in the menu, although the user might only be interested in a single show.
	#	If "pack=None" (default) or "pack=True" is passed in, the pack will be generated and added to the show/season/episode metadata.
	#	In the future we should make this "pack=False" by default, and require the caller to explicitly pass in "pack=True" in order to get the pack.
	#	But for now, since so many callers assume the pack data will be available, return the pack by default, and let callers explicitly state "pack=False" if they do not need the pack.

	def metadata(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, number = None, items = None, pack = None, filter = None, clean = True, quick = None, refresh = None, cache = False, threaded = None, limit = None, next = None, discrepancy = None, special = None, aggregate = True, hierarchical = False):
		# If no media is passed in, assume the items have different media.
		# Eg: Single search across movies and shows.
		if (not media or Media.isMixed(media)) and Tools.isArray(items):
			result = []
			data = {
				Media.Movie : [],
				Media.Show : [],
				Media.Season : [],
				Media.Episode : [],
				Media.Pack : [],
				Media.Set : [],
			}

			for item in items:
				try: data[item.get('media')].append(item)
				except: Logger.error()
			for media, values in data.items():
				if media and values:
					values = self.metadata(media = media, items = values, number = number, pack = pack, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded, limit = limit, next = next, discrepancy = discrepancy, special = special, aggregate = aggregate, hierarchical = hierarchical)
					if values: result.extend([(self.mTools.index(items = items, item = i, default = -1), i) for i in values])

			return [i[1] for i in Tools.listSort(result, key = lambda i : i[0])]
		else:
			if media is None and Tools.isDictionary(items): media = items.get('media')

			if Media.isShow(media):
				if not episode is None: media = Media.Episode
				elif not season is None: media = Media.Season

			if Media.isFilm(media): return self.metadataMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, items = items, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
			elif Media.isShow(media): return self.metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, items = items, pack = pack, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
			elif Media.isSeason(media): return self.metadataSeason(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, items = items, pack = pack, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded, aggregate = aggregate)
			elif Media.isEpisode(media): return self.metadataEpisode(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, number = number, items = items, pack = pack, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded, limit = limit, next = next, discrepancy = discrepancy, special = special, aggregate = aggregate, hierarchical = hierarchical)
			elif Media.isPack(media): return self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, items = items, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
			elif Media.isSet(media): return self.metadataSet(tmdb = tmdb, title = title, year = year, items = items, filter = filter, clean = clean, quick = quick, refresh = refresh, cache = cache, threaded = threaded)

		return None

	# level=0: Only refresh outer metadata.
	# level=1: Only refresh inner metadata.
	# level=2: Refresh inner and outer metadata.
	def metadataRefresh(self, level = None, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, number = None, notification = None):
		from lib.modules.interface import Dialog, Translation
		from lib.meta.menu import MetaMenu

		if MetaMenu.instance().notification(content = 'refresh', type = [media, level], background = False):
			def _notification(message, warning = False):
				if notification: Dialog.notification(title = 36770, message = message, icon = Dialog.IconWarning if warning else Dialog.IconInformation, time = 7000)

			if Media.isMovie(media):
				if level == 2:
					message = 36775
					refresh = None
				elif level == 1:
					message = 36776
					refresh = None
				else:
					message = 36777
					refresh = True
				_notification(message = message)
				item = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, refresh = refresh)
				if item and (level == 1 or level == 2):
					try:
						items = {'media' : Media.Set}
						items.update(item['collection'])
					except: items = None
					if items:
						item = self.metadata(items = items, refresh = True)
						if item and level == 2:
							items = item.get('part')
							if items: self.metadata(items = items, refresh = True)

			elif Media.isSet(media):
				if level == 2:
					message = 36775
					refresh = True
				elif level == 1:
					message = 36777
					refresh = None
				else:
					message = 36776
					refresh = True
				_notification(message = message)
				item = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, refresh = refresh)
				if item and (level == 1 or level == 2):
					items = item.get('part')
					if items: self.metadata(items = items, refresh = True)

			elif Media.isSerie(media) or Media.isPack(media):
				if Media.isShow(media):
					if level == 2: message = 36782
					elif level == 1: message = 36783
					else: message = 36778
				elif Media.isSeason(media):
					message = 36779
				elif Media.isEpisode(media):
					message = Translation.string(36780) % Title.numberUniversal(media = Media.Season, season = season)
				elif Media.isPack(media):
					message = 36781
				_notification(message = message)
				item = self.metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season if Media.isEpisode(media) else None, pack = False, refresh = True)
				if item:
					if level == 1 or level == 2:
						self.metadata(media = Media.Pack, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, pack = False, refresh = True)
						item = self.metadata(media = Media.Season, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, pack = False, refresh = True)
						if item:
							items = []
							totalSeason = 0
							totalEpisode = 0
							limitSeason = 4 # Minimum number of seasons to refresh.
							limitEpisode = 300 # Maximum number of episodes to refresh.

							item = Tools.listSort(item, key = lambda i : i.get('season'))
							if level == 1: item = Tools.listReverse(item)
							elif level == 2: item = Tools.listUnique(Tools.listInterleave([i for i in item if not i.get('season') == 0], [i for i in item if i.get('season') == 0], Tools.listReverse(item)))

							for i in item:
								add = False
								if level == 1:
									status = i.get('status')
									add = not status or status in MetaTools.StatusesPresent or status in MetaTools.StatusesFuture
								elif level == 2:
									add = True
								if add:
									items.append(i.get('season'))
									count = None
									try: count = i['packed']['count']['total']
									except: pass
									if not count:
										try: count = i['count']['episode']['total']
										except: pass
										if not count: count = 35
									totalSeason += 1
									totalEpisode += count
									if totalSeason >= limitSeason and totalEpisode > limitEpisode: break

							items = Tools.listUnique([i for i in items if not i is None])
							if items:
								items = items[:10]
								items = [{'media' : Media.Episode, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : i} for i in items]
								self.metadata(items = items, pack = False, refresh = True)

			if notification: Dialog.closeNotification()
			return True
		return False

	def _metadataRefresh(self, refresh):
		# If "refresh=False", also do not refresh the sub-metadata which is retrieve in the various update functions.
		# For instance, if we retrieve the episode metadata, it will also internally retrieve the show/season/pack metadata.
		# That is, if "refresh=False" for any metadata, any other metadata that is needed should also NOT be refreshed.
		# Only do this if "refresh=False" and not if "refresh=True" (or another value), otherwise if we refresh the episode metadata, it will also refresh the internal show/season/pack metadata.
		# Used by tester.py to force the refresh not to happen.
		return False if refresh is False else None

	def _metadataDeveloper(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, item = None, extra = None):
		if self.mDeveloper and (not extra or self.mDeveloperExtra):
			data = []

			if not imdb and item and 'imdb' in item: imdb = item['imdb']
			if imdb: data.append('IMDb: ' + str(imdb))

			if not trakt and item and 'trakt' in item: trakt = item['trakt']
			if trakt: data.append('Trakt: ' + str(trakt))

			if not media or Media.isFilm(media) or Media.isSet(media):
				if not tmdb and item and 'tmdb' in item: tmdb = item['tmdb']
				if tmdb: data.append('TMDb: ' + str(tmdb))

			if not media or Media.isSerie(media):
				if not tvdb and item and 'tvdb' in item: tvdb = item['tvdb']
				if tvdb: data.append('TVDb: ' + str(tvdb))

			if data: data = ['[%s]' % (' | '.join(data))]
			else: data = ['']

			if item:
				if not title: title = item.get('tvshowtitle') or item.get('title')
				if not year: year = item.get('tvshowyear') or item.get('year')

			# Packs return a list/dict for titles and years.
			if title and Tools.isArray(title): title = title[0]
			if year and not Tools.isInteger(year): year = year[0] if Tools.isArray(year) else year.get('minimum') if Tools.isDictionary(year) else None

			if title:
				data.append(title)
				if year: data.append('(%d)' % year)
			if not season is None:
				if episode is None: data.append('S%02d' % season)
				else: data.append('S%02dE%02d' % (season, episode))

			return ' '.join(data)
		return None

	def _metadataTemporize(self, item, result, provider):
		if item:
			temp = item.get('temp', {})
			if temp:
				temp = temp.get(provider)
				if temp:
					# Images
					try:
						data = temp.get(MetaImage.Attribute)
						if data:
							if not result.get(MetaImage.Attribute): result[MetaImage.Attribute] = {}
							image = result.get(MetaImage.Attribute)
							for key, value in data.items():
								if value:
									if Tools.isArray(value): value = [MetaImage.create(link = v, provider = provider) for v in value]
									else: value = [MetaImage.create(link = value, provider = provider)]
									if not image.get(key): image[key] = value
									else: image[key] = Tools.listUnique(image[key] + value)
					except: Logger.error()

					# Voting
					try:
						data = temp.get('voting')
						if data:
							value = data.get('rating')
							if value: result['rating'] = value

							value = data.get('votes')
							if value: result['votes'] = value

							value = data.get('user')
							if value: result['userrating'] = value
					except: Logger.error()

					# Progress
					value = temp.get('progress')
					if value: result['progress'] = value

					# Time
					value = temp.get('time')
					if value:
						if not 'time' in result: result['time'] = {}
						result['time'].update(value)

		return result

	# requests = [{'id' : required-string, 'function' : required-function, 'parameters' : optional-dictionary}, ...]
	def _metadataRetrieve(self, requests, threaded = None):
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
				threads = [Pool.thread(target = _metadataRetrieve, kwargs = {'request' : request, 'result' : result}, start = True) for request in requests]
				[thread.join() for thread in threads]
			else:
				for request in requests:
					_metadataRetrieve(request = request, result = result)
		return result

	def _metadataRequest(self, link = None, data = None, headers = None, method = None, function = None, cache = False, *args, **kwargs):
		if function:
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
		else:
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

	def _metadataCache(self, media, items, function, quick = None, refresh = None, cache = None, threaded = None, hierarchical = None, hint = None):
		threading = len(items) == 1 if threaded is None else threaded

		# Use memeber variables instead of local variables.
		# In case this function is called multiple times from different places to retrieve the same metadata.
		# Eg: Smart menu background refresh while the foreground menu construction from content() also requests the same metadata.
		#lock = Lock()
		#locks = {}
		lock = self.mLock
		locks = self.mLocks

		semaphore = Semaphore(self.mTools.concurrency(media = media, hierarchical = hierarchical))
		metacache = MetaCache.instance(generate = self.mModeGenerative)
		refreshInternal = self._metadataRefresh(refresh = refresh)

		metadataForeground = []
		metadataBackground = []
		jobsForeground = []
		jobsBackground = []

		items = metacache.select(type = media, items = items)

		if quick is None:
			for item in items:
				parameters = {'item' : item, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'cache' : cache, 'threaded' : threading}

				try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
				except: refreshing = MetaCache.RefreshForeground

				if refresh is True:
					refreshing = MetaCache.RefreshForeground

				elif refresh is False:
					refreshing = MetaCache.RefreshDisabled

				# During external metadata addon generation, reretrieve incomplete items.
				elif self.mModeGenerative and item[MetaCache.Attribute].get('part'):
					refreshing = MetaCache.RefreshForeground

				elif refreshing == MetaCache.RefreshBackground and self.mModeSynchronous:
					refreshing = MetaCache.RefreshForeground

				# Force a certain refresh.
				# Do not change the refreshing value if it is not RefreshForeground/RefreshBackground.
				# Used by _metadataSmartRefresh() to refresh all metadata in the background.
				elif (not self.mModeGenerative and not self.mModeSynchronous) and ((refreshing == MetaCache.RefreshBackground and refresh == MetaCache.RefreshForeground) or (refreshing == MetaCache.RefreshForeground and refresh == MetaCache.RefreshBackground)):
					refreshing = refresh

				if refreshing == MetaCache.RefreshForeground:
					self._busyStart(media = media, item = item)
					parameters.update({'result' : metadataForeground, 'mode' : MetaCache.RefreshForeground, 'refresh' : refreshInternal})
					jobsForeground.append(parameters)

				elif refreshing == MetaCache.RefreshBackground:
					if not self._busyStart(media = media, item = item):
						parameters.update({'result' : metadataBackground, 'mode' : MetaCache.RefreshBackground, 'refresh' : refreshInternal})
						jobsBackground.append(parameters)

		else:
			items = Tools.listShuffle(items, copy = True) # Create a shallow copy of the list, so that the order of the items does not change for the list that is passed into metadata().
			valid = []
			lookup = []

			foreground = None
			background = None
			if quick is True:
				foreground = False
				background = True
			elif quick is False:
				foreground = False
				background = False
			elif Tools.isDictionary(quick):
				foreground = quick.get(MetaCache.RefreshForeground, False)
				background = quick.get(MetaCache.RefreshBackground, False)
			elif Tools.isInteger(quick):
				if quick >= 0:
					foreground = quick
					background = True
				else:
					foreground = abs(quick)
					background = False

			for item in items:
				useable = False
				parameters = {'item' : item, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'cache' : cache, 'threaded' : threading}

				try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
				except: refreshing = MetaCache.RefreshForeground

				if refreshing == MetaCache.RefreshNone:
					valid.append(item)

				# Make sure that this does not execute if called from _metadataSmartLoad() with "quick=False" and we are in synchronous mode (called from reload()).
				elif refreshing == MetaCache.RefreshForeground or (refreshing == MetaCache.RefreshBackground and background is True and self.mModeSynchronous):
					if foreground is True or (foreground and len(lookup) < foreground) or (background is True and self.mModeSynchronous):
						self._busyStart(media = media, item = item)
						valid.append(item)
						lookup.append(item)
						parameters.update({'result' : metadataForeground, 'mode' : MetaCache.RefreshForeground, 'refresh' : refreshInternal})
						jobsForeground.append(parameters)
					elif background is True or (background and len(jobsBackground) < background):
						useable = True
						if not self._busyStart(media = media, item = item): # Still add foreground requests to the background threads if the value of "quick" forbids foreground retrieval.
							parameters.update({'result' : metadataBackground, 'mode' : MetaCache.RefreshBackground, 'refresh' : refreshInternal})
							jobsBackground.append(parameters)

				elif refreshing == MetaCache.RefreshBackground:
					useable = True
					if background is True or (background and len(jobsBackground) < background):
						if not self._busyStart(media = media, item = item):
							parameters.update({'result' : metadataBackground, 'mode' : MetaCache.RefreshBackground, 'refresh' : refreshInternal})
							jobsBackground.append(parameters)

				# Still add incomplete metadata to the returned items, since it has metadata, even if something is missing.
				# Important for metadata that is always labeled as incomplete, because it does not exist on some providers.
				# Eg: The Office UK S03 (on IMDb, but not on Trakt/TVDb/TMDb).
				# Also do this for external metadata, other-settings metadata, etc. Everything that is not invalid.
				if useable and not MetaCache.status(item) == MetaCache.StatusInvalid: valid.append(item)

			items = valid

		# Do this before starting to execute any threads.
		self._jobUpdate(media = media, foreground = len(jobsForeground), background = len(jobsBackground), hint = hint)

		if jobsForeground:
			if len(jobsForeground) == 1:
				if self._checkInterval(mode = MetaCache.RefreshForeground):
					if threaded is None: jobsForeground[0]['threaded'] = True # Faster parallel sub-requests if only one item needs to be retrieved.
					semaphore.acquire()
					if self._check():
						MetaCache.log(jobsForeground[0]['item'])
						function(**jobsForeground[0])
					else:
						semaphore.release()
			else:
				if threaded is None and len(jobsForeground) == 2: # Faster parallel sub-requests if only two items needs to be retrieved. 3 or more items use sequential requests.
					jobsForeground[0]['threaded'] = True
					jobsForeground[1]['threaded'] = True
				threads = []
				for i in jobsForeground:
					semaphore.acquire()
					if self._checkInterval(mode = MetaCache.RefreshForeground):
						MetaCache.log(i['item'])
						thread = Pool.thread(target = function, kwargs = i, start = True)
						threads.append(thread)
						self._threadAdd(thread = thread)
					else:
						semaphore.release()
						break
				if self._check(): [thread.join() for thread in threads] # Wait for metadata that does not exist in the metacache.

			# Do not insert if Kodi was aborted, since the loop above might not have finished retrieving all metadata and we do not want to insert unfinished/undetailed metadata.
			# 1 item: wait (do not start a background thread). Multiple items: do not wait (start a background thread).
			# Update (2025-11): Copy the metadata, since the metadata is returned and can change before the MetaCache insert thread gets executed.
			if self._check() and metadataForeground: metacache.insert(type = media, items = metadataForeground, wait = None, copy = True)

		# Let the refresh of old metadata run in the background for the next menu load.
		# Only start the threads here, so that background threads do not interfere or slow down the foreground threads.
		if jobsBackground:
			def _metadataBackground():
				if len(jobsBackground) == 1:
					if self._checkInterval(mode = MetaCache.RefreshBackground): # Delay slightly to allow more important code to execute first.
						if threaded is None: jobsBackground[0]['threaded'] = True # Faster parallel sub-requests if only one item needs to be retrieved. Even do for background, in case a single item in eg Progress menu is refreshed that needs to be loaded shortly afterwards.
						semaphore.acquire()
						if self._check():
							MetaCache.log(jobsBackground[0]['item'])
							function(**jobsBackground[0])
						else:
							semaphore.release()
				else:
					# For 2 or more background items, do not use threads, to allow foreground processes to use more.
					for i in range(len(jobsBackground)):
						semaphore.acquire()
						if self._checkInterval(mode = MetaCache.RefreshBackground): # Delay slightly to allow more important code to execute first.
							MetaCache.log(jobsBackground[i]['item'])
							thread = Pool.thread(target = function, kwargs = jobsBackground[i], start = True)
							jobsBackground[i] = thread
							self._threadAdd(thread = thread)
						else:
							semaphore.release()
							break
					if self._check(): [thread.join() for thread in jobsBackground]

				# Do not insert if Kodi was aborted, since the loop above might not have finished retrieving all metadata and we do not want to insert unfinished/undetailed metadata.
				# Wait (do not start a background thread), since we are already inside a thread.
				# Update (2025-11): Do not copy here, since it can take very long for packs, and it was already deep-copied below.
				if self._check() and metadataBackground: metacache.insert(type = media, items = metadataBackground, wait = True, copy = False)

			# Make a deep copy of the items, since the items can be edited/aggregated in the calling functions, and we do not want to store the unnecessary/large data in the database.
			# Eg: Adding large pack data, next/previous seasons, show/season images, etc.
			# The data is also deep copied in MetaCache, but because the background update runs in its own thread below, the dict might get edited before MetaCache has a chance to copy it.
			# This is also important for partial data (MetaCache.AttributePart):
			# MetaCache.Attribute gets removed in MetaManager._metadataClean(), and with a copy here, it is ensured that MetaCache.AttributePart is still available in the MetaManager._metadataUpdateXYZ(), even if another thread that retrieved the metadata has removed the attribute in _metadataClean().
			#for i in jobsBackground: i['item'] = Tools.copy(i['item'], deep = True)
			for i in jobsBackground: i['item'] = MetaCache.copy(type = media, data = i['item'], deep = None, cache = True) # "deep=None": deep copy all, but only shallow copy packs, because they take long to copy and are not internally edited anyways.

			# Delay to let other more important code execute first, before the less-important background retrieval happens.
			thread = Pool.thread(target = _metadataBackground, start = True, delay = Pool.DelayExtended)
			self._threadAdd(thread = thread)

		return items

	def _metadataAggregate(self, media, items):
		try:
			# The outer list metadata might be refreshed, without the inner title metadata being refreshed, just retrieving the old data from cache.
			# This means there can be new/updated values in temp from the outer list, like the progress, watched time, user rating, or even an updated global rating/votes, while the cached metadata still holds the old/outdated values.
			# Use the temp values and replace the main metadata values.

			if items:
				def _metadataAggregate(item, temp):
					voted = False

					for provider in ['metacritic', 'imdb', 'tvdb', 'tmdb', 'trakt']:
						values = temp.get(provider)
						if values:
							# Voting
							try:
								voting = values.get('voting')
								if voting:
									if not 'voting' in item: item['voting'] = {}
									votingCurrent = item.get('voting')
									for i in ['rating', 'votes', 'user']:
										value = voting.get(i)
										if value:
											if i == 'user': item['userrating'] = value
											if not value == votingCurrent.get(i, {}).get(provider):
												voted = True
												if not i in item['voting']: item['voting'][i] = {}
												item['voting'][i][provider] = value
							except: Logger.error()

							# Progress
							try:
								value = values.get('progress')
								if not value is None: item['progress'] = value
							except: Logger.error()

							# Time
							try:
								value = values.get('time')
								if value:
									if not 'time' in item: item['time'] = {}
									for k, v in value.items():
										if v: item['time'][k] = v
							except: Logger.error()

					# Recalculate the global rating/votes.
					# Only do this if the rating/votes actually changed, to save time.
					if voted: self.mTools.cleanVoting(metadata = item, round = True) # Round to reduce storage space of average ratings with many decimal places.

					aggregate = item.get('aggregate')
					if aggregate:
						del item['aggregate']
						for k, v in aggregate.items():
							item[k] = v

				values = items if Tools.isArray(items) else [items]

				if Media.isSeason(media):
					for item in values:
						temp = item.get('temp')
						if temp:
							numberSeason = item.get('season')
							if not numberSeason is None:
								for i in (item.get('seasons') or []):
									if i.get('season') == numberSeason:
										_metadataAggregate(item = i, temp = temp)
										break
				elif Media.isEpisode(media):
					for item in values:
						temp = item.get('temp')
						if temp:
							numberSeason = item.get('season')
							numberEpisode = item.get('episode')
							if not numberSeason is None and not numberSeason is None:
								for i in (item.get('episodes') or []):
									if i.get('season') == numberSeason and i.get('episode') == numberEpisode:
										_metadataAggregate(item = i, temp = temp)
										break
				else:
					for item in values:
						temp = item.get('temp')
						if temp: _metadataAggregate(item = item, temp = temp)

		except: Logger.error()
		return items

	def _metadataClean(self, media, items, clean = True, deep = True):
		try:
			if clean and items:
				if deep:
					if Media.isSeason(media): deep = 'seasons'
					elif Media.isEpisode(media): deep = 'episodes'
					else: deep = False

				values = items if Tools.isArray(items) else [items]
				if values and Tools.isArray(values[0]): values = Tools.listFlatten(values) # A list for multiple shows, each containing a list of seasons or episodes.

				for item in values:
					# Remove contradicting niches.
					# For instance, the niche contains both mini-series and multi-series types.
					# Eg: tt20234568 (mini-series type, but has 2 seasons).
					# This should already be fixed in MetaTools.niche().
					# However, if the menu list returns "Mini", but the detailed metadata has the correct "Multi", then both will be merged into the niche in MetaCache -> Tools.update().
					# IMDb will still lists "Mini" in the Advanced Search (eg: Arrivals), but this cannot be fixed from MetaImdb._extractNiche(), since the number of seasons is only in the detailed title IMDb page.
					item['niche'] = self.mTools.nicheClean(niche = item.get('niche'), genre = item.get('genre'))

					try: del item['temp']
					except: pass

					# Keep the cache for smart menu refreshes.
					if not clean == 'cache':
						try: del item[MetaCache.Attribute]
						except: pass

					if deep:
						values = item.get(deep)
						if values:
							for i in values:
								try: del i['temp']
								except: pass
		except: Logger.error()
		return items

	def _metadataFilter(self, media, items, filter = None, deep = True):
		try:
			if items:
				if filter is None: filter = len(items) > 1
				if filter:
					if deep:
						if Media.isSeason(media): deep = 'seasons'
						elif Media.isEpisode(media): deep = 'episodes'
						else: deep = False
					items = [i for i in items if (not deep or i.get(deep)) and (i.get('imdb') or i.get('trakt') or i.get('tvdb') or i.get('tmdb'))]
		except: Logger.error()
		return items

	##############################################################################
	# METADATA - ID
	##############################################################################

	# Sometimes platforms have the wrong ID for one or more providers.
	# This happens a lot for new releases. Mostly shows, but occasionally movies as well.
	# This happens with TMDb/Trakt:
	#	1. A new title gets added on TMDb.
	#	2. Trakt later scrapes this from TMDb and adds it to its library.
	#	3. A few days later it turns out the info on TMDb is wrong. Either a user entered incorrect info, or more frequently, the title was added multiple times by different users.
	#	4. Trakt later scrapes TMDb again. Now it adds the second/duplicate title to its library as well. So there are now 2+ entries on Trakt.
	#	5. TMDb removes one of the duplicates. The TMDb ID for the deleted title still exists. When opening the TMDb page, the ID+slug still shows in the URL, but it redirects to a 404 page.
	#	6. The one entry on Trakt now points to a TMDb (and possibly a IMDb) ID that does not exist, so retrieving TMDb images/ratings/etc does not work for this title.
	#	7. Trakt sometimes removes the duplicate entry, but this can take very long. And sometimes it does not do this at all and duplicates remain on the platform.
	#	8. This could also mean there are now 2 entries on Trakt with the same IMDb ID. So retrieving metadata from Trakt using the IMDb ID might return the outdated duplicate entry.
	# This can also happen to IMDb, although less frequent:
	#	1. A new title gets added to IMDb.
	#	2. TMDb/TVDb/Trakt scrape these.
	#	3. Later IMDb removes the title and creates a new one with a new ID. This could be duplicates or some other reason IMDb does this.
	#	4. The old IMDb ID now goes to a 404 page, or in some cases actually HTTP redirects to the new ID.
	#	5. TMDb/TVDb/Trakt might still have the old ID and/or a duplicate entry, and it might take a long time until they get cleaned.
	# These incorrect/oudated/non-existing IDs cause various problems:
	#	1. MetaCache might have issues, because there might be multiple entries with partially the same IDs. Retrieving by eg IMDb ID from cache might therefore return the old entry.
	#	2. Retrieving certain metadata, like images and rating, might not work for these titles, since they point to old non-existing IDs.
	# This also causes issues with the Arrivals smart-list:
	#	1. A new release is retrieved from the IMDb Advanced Search or TMDb Discover, only having an IMDb/TMDb ID.
	#	2. Other IDs are looked up using the IMDb/TMDb ID.
	#	3. The looked-up IDs might be different to the original IDs. Either IMDb has the new ID, and the lookup on TVDb/Trakt has the old IDs, or vice versa.
	#	4. Now in the Arrivals smart-list, these are seen as two different titles, since their IDs are different and will not be removed during duplicate filtering.
	# This also causes issues with already cached metadata that is being refreshed.
	#	1. The metadata was retrieved the first time with the old IDs and written to MetaCache.
	#	2. Later this metadata gets fixed on IMDb/TMDb/Trakt.
	#	3. Weeks later the metadata is automatically refreshed.
	#	4. But now the IDs from the old cached metadata is used to make the new requests, possibly retrieving the wrong IMDb or TMDb metadata, or no data at all.
	#	5. Hence, with every metadata refresh, the existing IDs should be REPLACED with the new ones coming in.
	# However, there might still be some IDs that are wrong.
	# Hence, we accumulate all IDs coming in from different providers, and pick the one that occurs most frequently.
	# This will probably not solve all issues, but at least some of them.
	# Example:
	#	The Arrivals menu retrieved this show from TMDb Discover: https://www.themoviedb.org/tv/256212-cris-miro-ella
	#	On Trakt there are multiple entries for this title:
	#		a. Show: https://trakt.tv/shows/cris-miro-she-her-hers (IMDb: tt32495809 | TMDb: 256212)
	#		b. Show: https://trakt.tv/shows/cris-miro-ella (IMDb: tt32495809 | TMDb: 256723 - already deleted)
	#		c. Movie: https://trakt.tv/movies/cris-miro-she-her-hers-2024 (IMDb: None | TMDb: 1308642 - movie, not tv - already deleted)
	#	Now the detailed metadata is retrieved. First an ID lookup is done via TVDb, returning:
	#		{'tvdb': '451157', 'imdb': 'tt32495809', 'tmdb': '256212'}
	#	During detailed metadata retrieval, providers return the following:
	#		IMDb: {'imdb': 'tt32495809'}
	#		TMDb: {'tmdb': '256212', 'imdb': 'tt32495809', 'tvdb': '451157'}
	#		TVDb: {'imdb': 'tt32495809', 'tmdb': '256212', 'tvdb': '451157'}
	#		Trakt: {'imdb': 'tt32495809', 'tmdb': '256723', 'trakt': '244111', 'slug': 'cris-miro-ella'}
	#	Since Trakt is considered most important, its IMDb would be carried over into the final metadata.
	#	By now using the most frequent IDs, we can use TMDb 256212. But Trakt still points to the "wrong" entry, since we technically want https://trakt.tv/shows/cris-miro-she-her-her.

	def _metadataId(self, metadata, ids, type):
		value1 = (metadata.get('id') or {}).get(type)
		value2 = Tools.listCommon(ids[type])
		if not value1: return value2
		elif not value2: return value1
		elif Tools.listCount(ids[type], value2) > Tools.listCount(ids[type], value1): return value2
		else: return value1

	def _metadataIdAdd(self, metadata, ids, type = None):
		values = metadata.get('id')
		if values:
			if type:
				value = values.get(type)
				if value:
					ids[type].append(value)
					return value
			else:
				for k, v in values.items():
					ids[k].append(v)
		return None

	def _metadataIdUpdate(self, metadata, ids):
		# Always replace the IDs with new values.
		# Otherwise if there is an incorrect IMDb ID on Trakt/TMDb, it gets written to MetaCache.
		# At a later point the ID is corrected on Trakt/TMDb.
		# If the data is now refreshed, the old ID from MetaCache is used instead of the newly retrieved IDs.
		# Hence, always replace these.
		types = ['imdb', 'tmdb', 'tvdb', 'trakt', 'slug']
		if Media.isSerie(metadata.get('media')): types.extend(['tvmaze', 'tvrage'])
		for type in types:
			value = self._metadataId(metadata = metadata, ids = ids, type = type)
			if value:
				# Also add the top-level ID, for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
				# At some later point the entire addon should be updated to have the new ID structure.
				if not 'id' in metadata: metadata['id'] = {}
				metadata[type] = metadata['id'][type] = value

	def _metadataIdLookup(self, media, title, year = None, list = False, quick = None):
		if title:
			id = self.mTools.id(media = media, title = title, year = year, quick = quick)
			if id and any(i for i in id.values()):
				# Add the title/year for a possible lookup if Trakt does not have the IMDb ID yet.
				result = {'imdb' : id.get('imdb'), 'tmdb' : id.get('tmdb'), 'tvdb' : id.get('tvdb'), 'trakt' : id.get('trakt'), 'title' : title, 'year' : year}
				return [result] if list else result
		return None

	##############################################################################
	# METADATA - SMART
	##############################################################################

	# remove:
	#	remove=True: Remove items that are not in "new".
	# detail: Wether or not to return detailed metadata.
	def _metadataSmart(self, media = None, items = None, new = None, filter = None, sort = None, order = None, limit = None, remove = None, content = None, timer = None, detail = False):
		try:
			if not self._check(): return Cache.Skip # Return Skip to not save the unfinished data to the cache.
			if timer is None: timer = self._jobTimer()
			current = Time.timestamp()

			movie = Media.isMovie(media)
			serie = Media.isSerie(media)

			stats = None
			helper = {}
			arrival = content == MetaManager.ContentArrival
			if not items: items = []

			# NB: use "number='extended'", not just "number=True", to also include standard/sequential/Trakt numbers that might be different between "new" (coming from Trakt) and "items" which are already smart-loaded.
			# Eg: One Piece - "new" items from Trakt (S02E63) vs already smart-loaded "items" (S02E02).
			number = 'extended' if serie else False

			# Add new items to the existing list.
			if new:
				# Remove any items not in new.
				# For Progress, since old watched episodes should be removed and replaced with the newly/next watched episode.

				if remove is True: # Progress
					helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
					items = [i for i in items if self.mTools.filterContains(items = new, item = i, number = number, key = MetaManager.Smart, helper = helper)]

				# Copy over values that can be changed by the user to already smart-loaded items.
				# For instance, we have all movies in ProgressRewatch smart-loaded. Now we watch the top movie on the list.
				# After the update, the new watched time from the new item should be added to the current smart-loaded item.
				helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
				for i in new:
					item = self.mTools.filterContains(items = items, item = i, number = number, key = MetaManager.Smart, helper = helper, result = True)
					if item:
						# Also accept None values from the new items.
						# A value could be available on the previous smart-load, but with the new smart-load, these values might be None.
						# Eg: progress cleared, item unwatched, rating removed, etc.

						item['playback'] = i.get('playback')

						for j in ['playcount', 'progress', 'userrating']: item[j] = i.get(j)

						times = i.get('time')
						if times:
							if not item.get('time'): item['time'] = {}

							for j in MetaTools.TimesTrakt:
								time = times.get(j)
								if time:
									item['time'][j] = time
								else: # Also overwrite with None. Eg: there was a paused time, but then the progress was cleared, and the new paused time is now None. Or if an item was unwatched.
									try: del item['time'][j]
									except: pass

						# For not-yet smart-loaded items, update the dates and ratings/votes, which might be higher for newer metadata.
						# Important for preliminary sorting of shows that are to be released today.
						# Otherwise new releases might end up on page 2+, because they have oudated metadata from an older cached request, with lower votes and slightly incorrect dates.
						# Once new arrival metadata comes in, use the newer dates/votes/rating.
						if arrival and not (item.get(MetaManager.Smart) or {}).get('time'):
							if times:
								for j in MetaTools.TimesRelease:
									time = times.get(j)
									if time and time > (item['time'].get(j) or 0): item['time'][j] = time

							votes = i.get('votes')
							if votes and votes > (item.get('votes') or 0):
								item['votes'] = votes
								item['rating'] = i.get('rating')

				# Only add new items that are not in the current list.
				# This makes sure that existing items with detailed metadata are not replaced with the same item without detailed metadata.
				new = [i for i in new if not self.mTools.filterContains(items = items, item = i, number = number, key = MetaManager.Smart, helper = helper)] # Reuse the helper.\
				if new:
					# Do initial sorting.
					# Important for Rewatch menus, were we actually want the oldest (watched longest time ago) items first, although the history items coming in are sorted by most recently watched.
					if sort or order: new = self._process(media = media, items = new, sort = sort, order = order, filter = False, page = False, limit = False)

					# Add the new items that are not in the current list to the front of the list.
					# This makes sure that a newly watched episode is immediately moved to the front for detailed metadata retrieval on the next request.
					items = new + items

			if items:
				# Load existing metadata from the cache.
				# Over time more and more detailed metadata will be available for improved sorting.
				items, stats = self._metadataSmartLoad(media = media, items = items, content = content, stats = True)
				if not self._check(): return Cache.Skip # Return Skip to not save the unfinished data to the cache.

				# Filter and sort using the more detailed metadata retrieved prior.
				if filter or sort or order: items = self._process(media = media, items = items, filter = filter, sort = sort, order = order, page = False, limit = False)

				# Filter out Wrestling titles, typically coming from IMDb.
				# Various Arrivals menu contain these, but more so niche menus (eg: TV Specials).
				# These cannot be filtered out any other way (eg: genre, etc).77
				if arrival: # Allow for the Progress menu.
					for item in items:
						title = item.get('title')
						if title and Regex.match(data = title, expression = r'(?:^|[\s\-\:])(WWE|AEW|UFC|NXT|TNA|[eE]lite\s*[wW]restling|[wW]restle\s*[mM]ania)(?:$|[\s\-\:])', flags = Regex.FlagNone, cache = True):
							item[MetaManager.Smart]['removed'] = current

				if Tools.isInteger(remove):
					if remove <= 20000:
						items = items[:remove]
					else:
						# There are quite a lot of titles returned within the requested time period, that when detailed metadata is retrieved, their dates are older than the requested time.
						# Often this is just a few days, but sometimes the digital/physical release date can be 6+ months older than the date requested from the eg Trakt calendar.
						# If we simply remove titles older than 1 year, these titles will constantly be in the "new" list.
						# They then get smart-loaded, only to discover that their actual date from the detailed metadata is older than a year, so that they then get removed here again.
						# This makes the same items stuck in "new" for a very long time, always getting smart-loaded and then removed, instead of spending the time on smart-loading other titles.
						# Instead of removing the titles older than 1 year, leave them in the list for another 9 months (1.75 years total) so that they can be used to filter out old items from the "new" list.
						# These "removed" items only have IDs and time, but all other metadata gets removed to save disk space.
						delete = current - int(0.75 * remove) # Delete 9 months after it was first marked for removal.
						remove1 = current - int(1.0 * remove)
						remove2 = current - int(2.0 * remove)
						remove3 = current - int(2.5 * remove)
						for item in items:
							smart = item[MetaManager.Smart] or {}

							removed = smart.get('removed')
							if removed:
								# Completely delete items that were marked as removed a long time ago.
								if removed < delete: smart['removed'] = True
							else:
								# Mark more recent items as "removed" and leave in the list for later deletion.
								# NB: Items not smart-loaded yet will not have the calculated home/launch/debut/etc dates. Use a fallback for the raw dates.
								time = item.get('time') or {}
								time1 = None
								time2 = None
								time3 = None
								time4 = None

								# Remove items more quickly if they are unpopular.
								# That is, they have relatively few votes a long time after release.
								# Only if the item was smart-loaded/refreshed after its home/premiere release, so that hopefully up-to-date vote counts are available.
								# This clears up the smart data more quickly to reduce the overall size. And the user is probably not interested in these titles anyways.
								adjust = 1.0
								smartTime = smart.get('time')
								if smartTime:
									votes = item.get('votes') or 0
									if votes < 1000:
										premiere = time.get(MetaTools.TimePremiere)
										if not premiere: premiere = current - 94672800 # Dummy premiere 3 years ago.
										if smartTime > premiere:
											home = None
											homed = True
											if movie:
												home = time.get(MetaTools.TimeDigital) or time.get(MetaTools.TimePhysical) or time.get(MetaTools.TimeTelevision) or time.get(MetaTools.TimeCustom)
												homed = not home or smartTime > home
											if homed:
												age = current - (home or premiere)
												if age > 47336400: # 1.5+ year.
													if votes < 100: adjust = 0.4
													elif votes < 250: adjust = 0.5
													elif votes < 500: adjust = 0.6
													elif votes < 1000: adjust = 0.7
												elif age > 31557600: # 1+ year.
													if votes < 100: adjust = 0.5
													elif votes < 250: adjust = 0.6
													elif votes < 500: adjust = 0.7
													elif votes < 1000: adjust = 0.8
												elif age > 23652000: # 9+ months.
													if votes < 100: adjust = 0.6
													elif votes < 250: adjust = 0.7
													elif votes < 500: adjust = 0.8
													elif votes < 1000: adjust = 0.9

								# Remove digital/physical releases or season premieres older than 1 year.
								# Movies: home release
								# Shows: latests season premiere
								if not removed:
									# Prefer the custom time for shows, which is the more recent season premiere, instead of the older show premiere.
									for i in (MetaTools.TimeCustom, MetaTools.TimePremiere) if serie else (MetaTools.TimeHome, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision, MetaTools.TimeCustom):
										time1 = time.get(i)
										if time1:
											if time1 < (remove1 * adjust): removed = True
											break

								# Remove very old premiered releases who only recently got a digital/physical release, older than 2 years.
								# Only do this for movies. Otherwise shows with a very old show premiere are removed, even if they have a recent season premiere.
								# Only do this if there is no home release. If there is a home release, wait for the previous statement to remove by home release date.
								# Movies: premiere release
								# Shows: none
								if not removed and movie and not time1:
									for i in (MetaTools.TimeDebut, MetaTools.TimePremiere, MetaTools.TimeLimited, MetaTools.TimeTheatrical, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision, MetaTools.TimeCustom):
										time2 = time.get(i)
										if time2:
											if time2 < (remove2 * adjust): removed = True
											break

								# Remove very old releases who do not have a known date, but only a very inaccurate TimeUnknown from the Arrivals request parameter, older than 2 years.
								if not removed:
									time3 = time.get(MetaTools.TimeUnknown)
									if time3 and time3 < (remove2 * adjust): removed = True

								# This will probably never trigger.
								# Remove titles with very old premieres, but only if there is no time1/time2 (eg: movie home release or show premiere).
								if not removed and not time1 and not time2:
									time4 = time.get(MetaTools.TimePremiere)
									if time4 and time4 < (remove3 * adjust): removed = True

								if removed: smart['removed'] = current

						# Delete items that were marked as "removed" a long time ago to reduce the list size and remove older items over time.
						items = [item for item in items if not item[MetaManager.Smart].get('removed') is True]

				# In very rare occasions, there are too many items returned by _arrivalRetrieve().
				# In one case, it has been observed that this function returns 2000-2500 items, a few hours later 5000-6000, and a few hours later 2000-2500 again.
				# This might be a temporary bug in eg Trakt. Maybe they worked on the API and the temporary changes ignored the "limit" parameter, therefore returning more items then it should.
				# This is difficult to detect, very sporadic, and only happens in very rare cases.
				# The items have to be limited in some way, otherwise the list grows too large, slowing down smart-loading, especially on low-end devices, and requiring way to much detailed metadata to be loaded.
				# The current best solution is to remove the oldest items by release date to a maximum limit.
				# Even if we remove too many items, or items that are actually important, hopefully they will be re-added during the next iteration when hopefully the temporary bug is gone.
				# But if the overhead items that were incorrectly added to the list do not fall within the removal date range (eg: too many NEWER items were added with a very low rating), they might be stuck in the list for way longer.
				# Not sure what should be done about this case.
				try:
					if arrival:
						maximum = 4000
						if len(items) > maximum:
							Logger.log('SMART LIMIT (%s - %s Titles): Detected too many titles in Arrivals. This might be a temporary issue and should be investigated further.' % (media.capitalize(), len(items)))
							if movie:
								items = Tools.listSort(items, key = lambda i : self.mTools.time(metadata = i, type = MetaTools.TimeHome, estimate = False, fallback = False) or self.mTools.time(metadata = i, type = MetaTools.TimeDebut, estimate = True, fallback = True) or 0, reverse = True)
							else:
								items = Tools.listSort(items, key = lambda i : self.mTools.time(metadata = i, type = MetaTools.TimeDebut, estimate = True, fallback = True) or 0, reverse = True)
							items = items[:maximum]
							if sort: items = self._process(media = media, items = items, sort = sort, order = order, page = False, limit = False)
				except: Logger.error()

				# NB: Do not store the detailed metadata in cache.db, otherwise it will become too large.
				# We still need to retrieve the detailed metadata, since we filter by genre above, and the base metadata might not contain the genre.
				if not detail: items = self._metadataSmartReduce(media = media, items = items)

			if stats:
				message = 'Total: %d [%d Active, %d Removed] | Processed: %d [%d New, %d Queued, %d Done] | Retrieved: %d [%d Cache, %d Foreground, %d Background]' % (
					stats['total']['all'],
					stats['total']['active'],
					stats['total']['remove'],
					stats['total']['new'] + stats['total']['queue'] + stats['total']['done'], # Should be the same as "active", except if something is wrong.
					stats['total']['new'],
					stats['total']['queue'],
					stats['total']['done'],
					stats['count']['all'],
					stats['count']['cache'],
					stats['count']['foreground'],
					stats['count']['background']
				)
			else: message = 'Smart generation failed without any items'
			Logger.log('SMART REFRESH (%s %s | %dms): %s' % (media.capitalize(), (content or 'unknown').capitalize(), timer.elapsed(milliseconds = True), message))
		except: Logger.error()

		# Return this as a dictionary, not a list.
		# Otherwise if the user does not have any progress for a niche, it returns an empty list, and then the cache complaints:
		#	CACHE: Refreshing failed result data in the background (Empty List) - [Function : Movies._progressAssemble | Parameters: ...]
		# Add the time for _metadataSmartReload().
		if not self._check(): return Cache.Skip # Return Skip to not save the unfinished data to the cache.
		return {
			'time' : Time.timestamp(),
			'items' : items,
		}

	def _metadataSmartLoad(self, media, items, content = None, stats = False):
		try:
			if items:
				current = Time.timestamp()

				movie = Media.isMovie(media)
				serie = Media.isSerie(media)
				episode = Media.isEpisode(media) or (serie and content == MetaManager.ContentProgress)
				pack = content == MetaManager.ContentProgress
				arrival = content == MetaManager.ContentArrival

				itemsNew = [] # Newly added items never seen before. Most important.
				itemsRelease = [[], []] # Items recently premiered. More important.
				itemsQueue = [] # Items already in the list, but not smart-loaded before. Medium important.
				itemsDone = [] # Items already in the list, and smart-loaded before. Least important.
				itemsRenew = [[], [], []] # Items already smart-loaded, but that are recently released and should be reloaded to get more up-to-date ratings/votes.
				itemsRemove = [] # Items removed because they are too old or other reasons.
				itemsLoad = []

				# This is set during preloading.
				# There might be new releases which detailed metadata has not been updated in a while.
				# Hence, the dates and ratings are outdated, making the item be listed at a far later page in Arrivals.
				# These items' metadata is hopefully refreshed in preload().
				# Reset them below in the smart list, so they get reloaded and their (updated) metadata reretrieved from cache, so that they are hopefully sorted to the front of the list.
				renew = None
				try:
					if arrival and self.mRenew: # Only for Arrival, since we reset the dict below, so it can only be used once.
						renew = self.mRenew.get(media)
						if renew:
							self.mRenew[media] = {} # Reset to not do this again on the next iteration.
							renewProviders = [MetaTools.ProviderTrakt, MetaTools.ProviderImdb, MetaTools.ProviderTmdb, MetaTools.ProviderTvdb]
				except: Logger.error()

				for item in items:
					# Can be used for debugging to force a specific item to be reloaded.
					'''if 'tt0000000' in str(item):
						item[MetaManager.Smart] = {}
						itemsNew.append(item)
					'''

					# Check above for more comments.
					try:
						if renew:
							renewal = False
							for provider in renewProviders:
								id = item.get(provider) or (item.get('id') or {}).get(provider)
								if id and renew[provider].get(id):
									renewal = True
									break
							if renewal:
								item[MetaManager.Smart] = {}
								itemsNew.append(item)
					except: Logger.error()

					self._metadataSmartUpdate(item = item)
					if content == MetaManager.ContentProgress and not 'external' in item[MetaManager.Smart]:
						self._metadataSmartUpdate(item = item, key = 'external', value = Tools.get(item, 'playback', 'source', 'external'))

					smart = item[MetaManager.Smart]
					if smart.get('removed'):
						itemsRemove.append(item)
					else:
						age = self._metadataSmartRelease(media = media, item = item, current = current)
						if age:
							ageRelease = age.get('release')
							ageHome = age.get('home')
						else:
							ageRelease = None
							ageHome = None

						smart = smart.get('time')

						if not smart:
							# The IMDb ID can change for a title, especially for new releases.
							# This can happen because of two reasons:
							#	1. A NEW request is made to an IMDb page for Arrivals, which contains the new IMDb ID. When detailed metadata is retrieved, a different IMDb ID is returned from Trakt/TMDb/TVDb which still point to the old IMDb ID, since they have not refreshed their own metadata and pulled in the new ID yet.
							#	2. A CACHED request for an IMDb page from Arrivals (days or weeks old) still returns the old IMDb, while everyone (IMDb/Trakt/TMDb/TVDb) have already updated to the new ID.
							# This makes an item coming into this function have an old IMDb ID and once the detailed metadata is retrieved, it now has a different IMDb ID and is therefore seen as a different title.
							# This makes an item get stuck in itemsNew/itemsRelease until the providers have updated their IDs.
							# In can get stuck even longer (weeks or months) if the providers do not update the IDs, or if some update it, but not others, causing an inconsistency between the IDs from Trakt/TMDb/TVDb.
							# In this case the item might only get out of the queue if it is outdated after a long time and then gets smart-removed.
							# Generally this should not be a huge issue, especially if detailed metadata is available from MetaCache and therefore only requires a local lookup.
							# However, if a number of these items get stuck, slots for foreground/background metadata retrieval during smart-loading are wasted, since every smart-refresh will load these items again, instead of using the slots for other queued/uncached items, slowing down how fast the smart Arrivals items are populated.
							# To avoid this slight "inefficiency", we add the original IMDb ID coming from one of the Arrivals lists, as a separate "imdx" ID.
							# Then during duplicate filtering, we use both those IDs and ensure the "new" item gets filtered out using the old and new IMDb IDs.
							#	Eg: And IMDb advanced search returns tt31186041. When looking up the Trakt/TMDb/TVDb IDs using this IMDb ID, and then retrieving the detailed metadata from all of them, the item ends up with tt33356012.
							#	This is the old IMDb ID, which has already changed on IMDb (and IMDb redirects tt33356012 to tt31186041), but the ID was not yet updated on Trakt/TMDb/TVDb. It might take a few days/weeks until the new ID might appear on providers.
							# This "imdx" IDs is used in MetaTools.filterDuplicate() and MetaTools.filterContains().
							imdb = item.get('imdb')
							if imdb and not item.get('imdx'):
								if not 'id' in item: item['id'] = {}
								item['id']['imdx'] = item['imdx'] = imdb

							if smart is None: item[MetaManager.Smart]['time'] = 0

							# Use more frequent intervals for home releases, to more quickly retrieve new digital/pysical releases.
							# This is only if not smart-loaded yet. Already smart-loaded items use other code at the end of the loop.
							if not ageRelease is None and ageRelease > -259200: # Not more than 3 days into the future.
								# Home release in the past 1 week, or premiere release in the past 3 days.
								# More likley these are wanted in the Arrivals menu.
								if ageRelease < 259200 or (not ageHome is None and ageHome < 604800):
									itemsRelease[0].append(item)
									continue

								# Home release in the past 3 weeks, or premiere release in the past 2 weeks.
								# More likley these are wanted in the Arrivals menu.
								elif ageRelease < 1209600 or (not ageHome is None and ageHome < 1814400):
									itemsRelease[1].append(item)
									continue

						if smart is None:
							item[MetaManager.Smart]['time'] = 0
							itemsNew.append(item)
						elif smart == 0:
							itemsQueue.append(item)
						else:
							if not ageRelease is None and ageRelease > -172800: # Not more than 2 days into the future.
								if ageRelease < 604800: itemsRenew[0].append(item) # Released in the past week.
								elif ageRelease < 1209600: itemsRenew[1].append(item) # Released in the past 2 weeks.
								elif ageRelease < 1814400: itemsRenew[2].append(item) # Released in the past 3 weeks.
							itemsDone.append(item)

				# Add to the other items.
				itemsNew += itemsRelease[0]
				itemsQueue = itemsRelease[1] + itemsQueue

				countAll = 0
				countCache = 0
				countForeground = 0
				countBackground = 0
				totalAll = len(items)
				totalNew = len(itemsNew)
				totalQueue = len(itemsQueue)
				totalDone = len(itemsDone)
				totalRemove = len(itemsRemove)
				totalActive = totalAll - totalRemove

				# First try to retrieve whatever is in the cache from any other request that might have retrieved the detailed metadata.
				# This call should never cause any new metadata to be retrieved. Only existing metadata should be returned.
				# This should also not be a lot of metadata, since we only retrieve new items that we are not yet aware of have detailed metadata.
				# Those we do know have detailed metadata are not loaded, since they are in "itemsDone".
				itemsCache = itemsNew + itemsQueue
				if itemsCache or (arrival and itemsRenew):
					# Limit the number of items to retrieve from the cache. Retrieve the rest during the next execution.
					# Otherwise, if the user has loaded many menu pages since the last time this function was called, there might be too much new metadata to retrieve from disk, which might take too long.
					# Especially for the episode Progress menu, which will also retrieve large pack data from disk.
					# Add some randomness, otherwise we might always try to retrieve the first items only, while there are cached items later in the list.
					itemsCache = self._metadataSmartChunk(items = itemsCache, limit = 20 if episode else 50 if serie else 75)

					# Add some more randomized items for the Arrivals menu.
					# Otherwise the Arrivals with 5000+ titles takes way to long to smart-load, since most items retrieved above are not cached and will return very few items.
					# Plus the Arrivals menu is not refreshed that often. So the extra retrievals should not matter.
					if arrival:
						helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
						itemsCache2 = []

						# Also reload titles that were released recently.
						# When a new show comes out, it is mostly smart-loaded on the first day from itemsNew.
						# However, on the first day there are very few votes. Even for popular shows, on the first 2 days there are often less than 20 votes.
						# Eg: American Primeval only had 14 votes and a low rating 2-3 days after release. Even after a week there were only 400 votes on Trakt.
						# Now that the title is smart-loaded, it might end up on page 2 or later, therefore not loading the detailed metadata, and MetaTools._sortGlobal() will only use the early votes (less than 20).
						# Now the title is stuck on page 2+ and might take very very long to get reloaded, since there are so many other titles in the queue. Even if it is finally reloaded, it is so old by then, that it ends up on a later page anyways.
						# Therefore, reload recent releases more frequently.
						itemsCache2 += Tools.listShuffle(itemsRenew[0][:20])
						itemsCache2 += Tools.listShuffle(itemsRenew[1][:15 + (20 - len(itemsCache2))])
						itemsCache2 += Tools.listShuffle(itemsRenew[2][:10 + (35 - len(itemsCache2))])

						itemsCache2 = Tools.listShuffle(itemsNew[:15]) + itemsCache2 + Tools.listShuffle(itemsNew[15:] + itemsQueue)
						itemsCache2 = [i for i in itemsCache2 if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsCache += self._metadataSmartChunk(items = itemsCache2, limit = 100) # If the limit is changed, also change itemsRenew above.

					itemsCache = self._metadataSmartRetrieve(items = itemsCache, pack = pack, quick = False) # Retrieve from cache and the rest not at all.
					if not self._checkInterval(): return (False, False) if stats else False
					if itemsCache:
						countCache += len(itemsCache)
						itemsLoad.extend(itemsCache)

						# Remove any items that now have detailed metadata.
						# NB: Do not filter by number here, since the Trakt number has been converted to a Standard number, and might mismatch here.
						# There should in any case not be multiple episodes from the same show in the list.
						# Otherwise the converted episode number is always seen as a "new" episode and end up retrieving metadata for it again and again.
						# Eg: One Piece S02E63.
						helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
						itemsNew = [i for i in itemsNew if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsQueue = [i for i in itemsQueue if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsRelease[0] = [i for i in itemsRelease[0] if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsRelease[1] = [i for i in itemsRelease[1] if not self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]

				# Now retrieve detailed metadata for not yet smart-loaded items.
				# Only do this for as few items as possible, since more detailed metadata is retrieved outside and will be incorporated during the next smart loading.
				# Also retrieving a new episode in the Progress menu, will retrieve metadata for all episodes in the season, season metadata, show metadata, and pack metadata/generation, so even a few items can take long.
				# This should not hold up the smart list creation a long time.
				# Still retrieve at least the most recent new item, since that might be the just-watched episode and we want to correctly have the next episode from that show in the new progress list.
				count = 3 if episode else 5 if serie else 7 # Update (2025-11): Previously 3 for all media. But increased this, since 3 is very little. There are 10 more added for Arrivals below.
				itemsCache = None

				if self.mModeAccelerate:
					# If in accelerate mode, retrieve as little as possible.
					# This is during binge watching when starting the playback of the next episode.
					# Gaia can be laggy during the rating/binge/playback dialog, since heavy refreshing is gonig on in the background.
					# Do this only at the end of playback (action finished or stop).
					# A full refresh happens earlier during playback, when the history is updated.
					itemsCache = itemsNew[:1]
				else:
					if Math.randomProbability(0.3):
						# Sometimes an item gets "stuck" in the "new" list over and over again.
						# This can be because of some incorrect ID that makes the item get removed from the smart list, only to be added again when the smart list is refreshed.
						# These issues should all have been fixed now and this should not happen anymore.
						# But still do this, just in case some other yet-unknown problem also causes this.
						# Instead of always picking the first 3 items, every now-and-then pick random items from the first 10.
						try:
							itemsCache = Tools.listShuffle(itemsNew[:10])[:count]
							if len(itemsCache) < count: itemsCache += Tools.listShuffle(itemsQueue[:10])[:(count + 1) - len(itemsCache)] # Add more if there are no new items.
						except: Logger.error()
					if not itemsCache:
						itemsCache = itemsNew[:count]
						if len(itemsCache) < count: itemsCache += itemsQueue[:(count + 1) - len(itemsCache)] # Add more if there are no new items.

					# Items releases in the past few days should be urgently retrieved.
					# Otherwise shows released today might take too long until it shows up on the Arrivals menu, if there are too many items in the queue that are waiting for smart-loading.
					if arrival:
						# Not if it comes from MetaCache, that is, loaded with a one of the calls above.
						helper = {}
						itemsImportant = [i for i in itemsRelease[0] if not MetaCache.Attribute in i and self.mTools.filterContains(items = itemsCache, item = i, helper = helper)]
						itemsCache += itemsImportant[:10]

				if itemsCache:
					itemsCache = self._metadataSmartRetrieve(items = itemsCache, pack = pack, quick = None) # Retrieve from cache, foreground or background.
					if not self._checkInterval(): return (False, False) if stats else False
					if itemsCache:
						countForeground += len(itemsCache)
						itemsLoad.extend(itemsCache)

				# If there are few items retrieved from cache, also reload some already smart-loaded items in order to refresh their metadata if they are outdated.
				# Refresh those items that were smart-loaded the longest time ago.
				if len(itemsLoad) < (30 if arrival else 20) and itemsDone:
					itemsCache = Tools.listSort(itemsDone, key = lambda i : i.get(MetaManager.Smart).get('time'))

					# These will later on also be refreshed by _metadataSmartReload(), so no need to retrieve these in the background/foreground.
					#itemsCache = self._metadataSmartChunk(items = itemsCache, limit = 7 if episode else 15 if serie else 20)
					#itemsCache = self._metadataSmartRetrieve(items = itemsCache, pack = pack, quick = True) # Retrieve from cache and the rest in the background.
					#if not self._checkInterval(): return (False, False) if stats else False
					#if itemsCache is False:
					#	if stats: return False, False
					#	else: return False
					#if itemsCache:
					#	countBackground += len(itemsCache)
					#	itemsLoad.extend(itemsCache)

					# Be more aggresive with Arrivals. Since new releases (1-2 weeks) have very few votes, although the detailed metadata might be updated with the new higher vote count.
					# The old lower vote count can make new releases have a lower order in sortGlobal().
					itemsCache = self._metadataSmartChunk(items = itemsCache, limit = (10 if episode else 40) if arrival else (7 if episode else 15 if serie else 20))
					itemsCache = self._metadataSmartRetrieve(items = itemsCache, pack = pack, quick = False) # Retrieve from cache and the rest not at all.
					if not self._checkInterval(): return (False, False) if stats else False
					if itemsCache:
						countCache += len(itemsCache)
						itemsLoad.extend(itemsCache)

				countAll = len(itemsLoad)

				# NB: The items in "itemsLoad" might not be the original dictionary from "items" that was passed into self.metadata().
				# self.metadataEpisode() returns a new dictionary, since all episodes of a season are retrieved in one go from MetaCache.
				# So do not just update the values in "itemsLoad", since it will not update the original "items" that is returned by this function.
				# Copy over the values from "itemsLoad" into the original "items".
				helper = {} # Use a helper, since it is considerably faster if filterContains() is called multiple times in a loop.
				for item in itemsLoad:
					# Do not use the number, since it might have changed.
					# Plus smart lists should not contain multiple episodes from the same show.
					found = self.mTools.filterContains(items = items, item = item, helper = helper, result = True)
					if found:
						# Add the timestamp to indicate this item was smart-loaded.
						# If the detailed metadata comes from the external metadata addon, do not update the time, since it might be outdated metadata.
						# Generally this should not be an issue, but if the user installs Gaia for the first time a few weeks/months after the external addon was updated, it will start pulling in outdated metadata for the Arrivals smart menu from the addon,
						# This can contain incorrect release dates, and low votes/ratings, which affects global sorting.
						# Still allow the external metadata as "fallback", improving filtering/sorting when the smart list is initially created.
						# This can also greatly help with importing a large Trakt history in the Progress menu, which will have a lot of older titles and this allows for detailed metadata right from the start, and improve filtering/sorting.
						# However, since we leave the smart time at 0, on the next smart-refresh it will see this as a new/queued item and retrieve it again. This time it would have the new metadata from the local cache.
						external = MetaCache.status(item) == MetaCache.StatusExternal
						self._metadataSmartUpdate(item = item, key = 'time', value = 0 if external else current)

						if content == MetaManager.ContentProgress:
							if Media.isEpisode(item.get('media')):
								# Episodes coming from the Trakt history still have the Trakt numbers.
								# It is too expensive to convert all these numbers in Playback.
								# Do here, so that we do not have to do it later in metadataEpisode() for already smart-loaded items, every time the Progress menu is loaded.
								if found[MetaManager.Smart].get('external'): # This is set on "found", not the "item".
									try: number = item['number'][MetaPack.NumberStandard]
									except: number = None
									if number:
										# Used to determine newly added episode of if the episode is already in the list.
										# Since the Trakt number gets replaced below.
										item[MetaManager.Smart]['season'] = item['season']
										item[MetaManager.Smart]['episode'] = item['episode']

										item['season'] = number[MetaPack.PartSeason]
										item['episode'] = number[MetaPack.PartEpisode]
										found[MetaManager.Smart]['external'] = None # Do not lookup again in metadataEpisode().

								# Determine the next episode.
								# Any show that does not have a next episode (eg: all episodes watched), should be moved further back to the list.
								# Otherwise in content() there might be less items on the page than the limit, because these are only filtered out later.
								# Only do this if the pack is available.
								# Used by MetaTools._sortLocal()
								pack = item.get('pack')
								if pack:
									pack = MetaPack.instance(pack = pack)
									item[MetaManager.Smart]['pack'] = pack.reduceSmart()

									nextItem = {'imdb' : item.get('imdb'), 'tmdb' : item.get('tmdb'), 'tvdb' : item.get('tvdb'), 'trakt' : item.get('trakt'), 'season' : item.get('season'), 'episode' : item.get('episode')}
									nextNumber = self._metadataEpisodeIncrement(item = nextItem, number = MetaPack.ProviderTrakt if found[MetaManager.Smart].get('external') else MetaPack.NumberStandard, threaded = False)

									if nextItem.get('invalid') or nextItem.get('episode') is None:
										# Set to False, to specifically indicate that there is no new episode.
										item[MetaManager.Smart]['next'] = False
									else:
										nextSeason = nextItem.get('season')
										nextEpisode = nextItem.get('episode')

										# Add the next episode's time to the smart data.
										# This is used for preliminary sorting PRIOR to the paging.
										# Otherwise future episodes cannot be filtered out BEFORE the paging is done. Meaning future episode can only be sorted to the bottom of the 1st page, instead of moving it to later pages.
										item[MetaManager.Smart]['next'] = {
											'season' : nextSeason,
											'episode' : nextEpisode,
											'number' : nextNumber,
											'time' : pack.time(season = nextSeason, episode = nextEpisode, number = nextNumber),
										}

									# Used by release() to determine earlier refresh rates.
									# Add this here, since we already loaded the pack, which is not done again in release() for efficiency reasons.
									releaseItem = pack.lastEpisodeOfficial()
									if releaseItem:
										releaseSeason = pack.numberStandardSeason(item = releaseItem)
										releaseEpisode = pack.numberStandardEpisode(item = releaseItem)
										releaseTime = [pack.timeMinimum(season = i) for i in range(releaseSeason + 1)]
										releaseTime = [i for i in releaseTime if i]
										item[MetaManager.Smart]['release'] = {
											Media.Season : releaseSeason,
											Media.Episode : releaseEpisode,
											'count' : {
												Media.Pack : pack.countEpisodeOfficial(), # Total number of episodes in the entire show, excluding S0.
												Media.Season : releaseSeason, # Total number of seasons, excluding S0.
												Media.Episode : releaseEpisode, # Total number of episodes in latests seasons.
												Media.Special : pack.countEpisode(season = 0), # Total number of specials in S0.
											},
											'time' : [
												pack.timeStandard(season = 1, episode = 1),
												releaseTime,
												pack.timeValues(season = releaseSeason), # Add all episode dates. The closest one will be picked in release().
											],
										}
									else:
										item[MetaManager.Smart]['release'] = None

						elif arrival:
							# NB: Add the season number to the smart dict.
							# Otherwise for Show Arrivals, the show object + season number is part of the "new" list that comes in.
							# Once the show object gets smart-loaded, the season number in the root dict gets removed.
							# This then causes the smart list to grow very large over time, since every show object is added multiple times to the smart list, once with a season number and once without.
							# Then when we call MetaTools.filterContains(), these objects are seen as different ones, since they have different season numbers.
							if Media.isSerie(item.get('media')): item[MetaManager.Smart]['season'] = item.get('season')

							# Some titles have no plot and/or poster.
							# Sort these titles to the back of the Arrivals list, since they look ugly and are typically low-budget movies.
							# _arrivalProcess() adds after-filters to remove these items from the menu.
							# But do this here so we can sort them to the back instead of filtering them at the end, so that menus still have the full 50 items per page.

							complete = bool(item.get('plot')) and bool((item.get(MetaImage.Attribute) or {}).get('poster'))
							if not complete:
								# If the title is released in the future, then missing metadata is very common.
								# Do not set to False, otherwise if they are sorted in MetaTools._sortGlobal(), they get added to the back if the smart-loaded metadata is outdated, even if it is a major blockbuster that will get these missing attributes once released.
								time = self.mTools.time(type = MetaTools.TimePremiere, metadata = item, estimate = False, fallback = True)
								if time and time > current: complete = None
							item[MetaManager.Smart]['complete'] = complete

						found.update(item)
					else:
						# This should never happen. If it does, something is wrong.
						Logger.log('SMART REFRESH FAILURE: %s [%s]' % (str(item.get('tvshowtitle') or item.get('title')), str(item.get('imdb') or item.get('trakt'))))

			# Recalculate values that can change.
			# Do this even if the item was not loaded above, since these values can change in the history without it being smart-loaded again.
			# Similar to the new-loop in _metadataSmart(), but these values migth require additional attributes calculated in this function.
			if content == MetaManager.ContentProgress:
				# The "play" attribute indicates the total number of plays plus the progress.
				# Eg: 2.5 means played fully twice, and currently rewatching with a progress of 50%.
				# For shows, it means the percetange of the show fully watched.
				# Eg: 2.5 means all episodes were played twice, and currently rewatching with half the episodes watched.
				# This might not be a perfect indicator, since the user might have watched a few episodes multiple times, and others fewer or no times.
				# But for normal watches, this should be a pretty good indicator.
				for item in items:
					play = 0
					if serie:
						pack = item[MetaManager.Smart].get('pack')
						if pack:
							countTotal = Tools.get(pack, 'count', MetaPack.NumberOfficial, MetaPack.ValueEpisode)
							if countTotal:
								countWatched = Tools.get(item, 'playback', 'counts', 'main', 'total')
								progressWatched = Tools.get(item, 'playback', 'progress') # Not really needed, since this will make almost no difference.
								play = ((countWatched or 0) + (progressWatched or 0)) / float(countTotal)
					else:
						play = (Tools.get(item, 'playback', 'count') or 0) + (Tools.get(item, 'playback', 'progress') or 0)
					item[MetaManager.Smart]['play'] = Math.round(play, places = 6) if play else play

			# Important to filter duplicates for Arrivals.
			# There can be duplicate items, some with one of the IMDb/TMDb/Trakt IDs only, and others with multiple IDs. Eg: some items come from IMDb sources, otherwise from Trakt or TMDb.
			# Only after detailed metadata retrieval are all the IDs available and can we filter out these duplicates.
			# This means the Arrivals list can get slightly smaller over time.
			# Also check the number, since the same show can have 2 seasons released within the same year. Keep both, otherwise the one is always in "new".
			# The duplicate seasons get filtered out in _arrivalProcess().
			items = self.mTools.filterDuplicate(items = items, id = True, title = False, number = True)

			statistics = {
				'total' : {'all' : totalAll, 'active' : totalActive, 'new' : totalNew, 'queue' : totalQueue, 'done' : totalDone, 'remove' : totalRemove},
				'count' : {'all' : countAll, 'cache' : countCache, 'foreground' : countForeground, 'background' : countBackground},
			}
			self._metadataSmartStats(media = media, content = content, stats = statistics.get('total'))

			if stats: return items, statistics
			else: return items
		except:
			Logger.error()
			if stats: return items, None
			else: return items

	def _metadataSmartRenew(self, media, items):
		try:
			providers = [MetaTools.ProviderTrakt, MetaTools.ProviderImdb, MetaTools.ProviderTmdb, MetaTools.ProviderTvdb]
			if self.mRenew is None: self.mRenew = {}
			if not media in self.mRenew:
				self.mRenew[media] = {}
				for i in providers: self.mRenew[media][i] = {}

			renew = self.mRenew[media]
			for item in items:
				ids = item.get('id')
				for i in providers:
					id = ids.get(i)
					if id: renew[i][id] = True
		except: Logger.error()

	def _metadataSmartRelease(self, media, item, current = None, update = True):
		try:
			# Add the less-inaccurate dates from external sources as TimeCustom as a fallback:
			#	1. This allows for better sorting of movie Arrivals from MetaTools._sortGlobal() if the digital/physical release dates are not available yet.
			#	2. This allows for more frequent refreshes of the item in the smart-list below if its digital/physical dates get closer. Movies get added to Arrivals on their digital date and having updated metadata around this time is beneficial.
			# Most dates returned by _arrivalRetrieve() are premiere dates. Only the Trakt DVD calendar returns a few physical dates.
			# But digital dates are not available at all in _arrivalRetrieve(), except if detailed metadata is loaded or when using the dates from external sources in release().
			# The digital/physical release dates can be missing if:
			#	1. The item was not smart-loaded yet and therefore has missing dates.
			#	2. The item was smart-loaded a while back and therefore has outdated metadata. Sometimes digital/physical dates are only added to Trakt/TMDb a few days prior to those dates.
			#	3. The item has no digital/physical dates in the detailed metadata. Either the title does not have those dates at all, or they were simply not entered on Trakt/TMDb.
			# Hence, if the digital/physical dates are not available for smart items, use the external dates instead for better sorting and quicker refreshing.

			if current is None: current = Time.timestamp()
			time = item.get('time') or {}
			movie = Media.isMovie(media)

			# Do not use dates more than 3 days into the future, since they probably still have outdated metadata and we do not want to unnecessarily refresh.
			# The places that call this function assume this value to be no more than 3 days.
			future = 259200

			all = []
			home = []
			custom = None
			origin = None

			# Add the external custom date if available from release().
			# Do this every time the smart list is refreshed, since release() gets updated daily with new dates.
			# The total lookup for all items is 25-35ms, where most of the time is spend on initializing the release() cache the first time the function is called.
			try:
				lookup = self.release(media = media, metadata = item)
				if lookup:
					# Add the origin to the smart attributes, which is used in MetaTools._sortGlobal().
					# Titles that are on the Trakt calendar are weighted higher in the Arrivals menu.
					# More info under MetaTools._sortGlobal().
					origin = {
						'release' : lookup.get('origin'),	# The item's origin in the release() calendar.
						'arrival' : item.get('origin'),		# The item's origin from the arrival() smart menu.
					}
					if update: item[MetaManager.Smart]['origin'] = origin

					lookuped = lookup.get('time')
					if lookuped:
						custom = lookuped
						if movie and update: # Only add this for movies, since shows have a different TimeCustom.
							# Most recent date in the past. No future dates.
							homed = lookup.get('home')
							if homed:
								home.extend(homed)
								homed = [i for i in homed if i <= current]
								if homed: homed = max(homed)

							# NB: Prefer the digitial/physical release date from Trakt.
							# Since time[2] can be a physical date in the future, while there is a digital date in the past.
							# Prefer the earlier date for TimeCustom.
							lookuped = homed or lookuped[2] or lookuped[1] or lookuped[0] # homed=digital/physical(Trakt), 2=digital/physical, 1=limited/theatrical, 0=premiere
							if lookuped:
								if not time: item['time'] = time = {} # Sometimes the time attribute is None.
								time[MetaTools.TimeCustom] = lookuped
			except: Logger.error()

			# Get the closest time for more frequent refreshes around the release dates.
			if movie:
				# Add all 3 custom dates for movies.
				if custom:
					all.extend(custom)
					home.append(custom[2])

				# The digital/pysical release dates might be closer to the current date than the premiere.
				for t in (MetaTools.TimeHome, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision):
					value = time.get(t)
					if value: home.append(value)
				if not home: # Estimate the time if no other dates are available.
					value = self.mTools.timeEstimate(type = MetaTools.TimeHome, times = time, metadata = item)
					if value: home.append(value)

				all.extend(home)
			else:
				# Do not include the episode release dates, otherwise refreshing will happen too often when a new episode is released every week.
				# Only include the show and season premiere.
				if custom: all.extend(custom[:2])

			# NB: Items not smart-loaded yet, do not have home/debut/etc calculated times, only the raw premiere time.
			for t in (MetaTools.TimeDebut, MetaTools.TimePremiere, MetaTools.TimeLimited, MetaTools.TimeTheatrical) if movie else (MetaTools.TimeDebut, MetaTools.TimePremiere):
				value = time.get(t)
				if value: all.append(value)
			if not all: # Estimate the time if no other dates are available.
				value = self.mTools.timeEstimate(type = MetaTools.TimeDebut, times = time, metadata = item)
				if value: all.append(value)

			age = self.mTools.timeClosest(times = all, time = current, future = future, fallback = True) if all else None
			if age: age = current - age

			home = self.mTools.timeClosest(times = home, time = current, future = future, fallback = True) if home else None
			if home: home = current - home

			return {'release' : age, 'home' : home, 'origin' : origin}
		except: Logger.error()
		return None

	# Always retrieve the pack data, since it is needed to create various smart attributes.
	# Do not aggregate the show/season data, since it is not needed here, and only slows down things and requires additional disk I/O.
	def _metadataSmartRetrieve(self, items, quick = None, refresh = None, pack = True, aggregate = False):
		# Clean: keep the MetaCache data to determine if it comes from the external cache.
		return self.metadata(items = items, quick = quick, refresh = refresh, pack = pack, aggregate = aggregate, clean = 'cache')

	def _metadataSmartUpdate(self, item, key = None, value = None):
		if not MetaManager.Smart in item: item[MetaManager.Smart] = {}
		if not key is None: item[MetaManager.Smart][key] = value
		return item

	def _metadataSmartStats(self, media = None, content = None, stats = None, notification = None):
		try:
			id = 'internal.smart'
			data = Settings.getData(id)

			if Media.isSerie(media): media = Media.Show
			if not data: data = {'time' : {'update' : 0, 'notification' : 0}}

			if stats: self._batchSmart(content = content, media = media, total = stats.get('active'), count = stats.get('done')) # Use "active", not "all", to ignore removed items.

			if stats or notification:
				if stats:
					data['time']['update'] = Time.timestamp()
					if not content in data: data[content] = {}
					data[content][media] = stats
				if notification:
					data['time']['notification'] = Time.timestamp()
				Settings.setData(id, data)

			try:
				if data:
					total = 0
					done = 0
					for i in [MetaManager.ContentProgress, MetaManager.ContentArrival]:
						for j in [Media.Movie, Media.Show]:
							try:
								value = data[i][j]
								total += value.get('active') or 0 # Use "active", not "all", to ignore removed items.
								done += value.get('done') or 0
							except: continue
					progress = int(min(100, (done / float(total)) * 100))

					from lib.modules.interface import Translation
					Settings.set(id = 'metadata.general.preload', value = '%d%% %s' % (progress, Translation.string(36839)))
			except: Logger.error()

			if content:
				data = data.get(content)
				if media: data = data.get(media)
			return data
		except: Logger.error()
		return None

	def _metadataSmartChunk(self, items, limit, performance = True, accelerate = True):
		# Only low-end devices, background refreshes/reloads can take very long, making menus very slow.
		if performance:
			if self.mPerformanceMedium: limit *= 0.9
			elif self.mPerformanceSlow: limit *= 0.8

		if accelerate and self.mModeAccelerate: limit *= 0.9

		limit = max(1, int(limit))
		limit1 = int(limit * 0.6)
		limit2 = limit - limit1
		return items[:limit1] + Tools.listShuffle(items[limit1:])[:limit2]

	def _metadataSmartReduce(self, media, items, full = True):
		# NB: Keep the time dict, since this is needed for semi-removed smart items to be fully removed at a later point based on the dates.
		# The times are also used for release().
		# NB: Also keep item['id']['collection'] for sets.
		removed = ['media', 'id', 'imdb', 'imdx', 'tmdb', 'tvdb', 'trakt', 'time']

		# Include any attributes that might be used for sorting or filtering, BEFORE the detailed metadata is retrieved.
		values = [
			'media', 'niche', 'origin',
			'id', 'imdb', 'imdx', 'tmdb', 'tvdb', 'trakt',
			'tvshowtitle', 'title', 'originaltitle',
			'tvshowyear', 'year', 'premiered', 'time',
			'rating', 'votes', # Do not add "voting", since it increases the size, and only the aggregated rating/votes are needed.
			'country', 'language', 'genre', 'mpaa',
		]

		if full:
			removed.append(MetaManager.Smart)
			values.extend([
				MetaManager.Smart,
				'progress', 'playcount', 'userrating',
				#'playback', # Do not add "playback", since it increases the size, but is not needed, since all necessary values are necessary into MetaManager.Smart.
			])

		if Media.isSerie(media):
			values.extend(['tvshowtitle', 'season', 'episode', 'number', 'aired'])
			removed.extend(['season', 'episode'])

		return [{i : item.get(i) for i in (removed if (item.get(MetaManager.Smart) or {}).get('removed') else values)} for item in items]

	def _metadataSmartAggregate(self, media, items, base):
		try:
			if base:
				if not Tools.isArray(base): base = [base]
				if any(MetaManager.Smart in i for i in base):
					smarts = {'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}}
					for item in base:
						smart = item.get(MetaManager.Smart)
						if smart:
							for i in smarts.keys():
								id = item.get(i)
								if id: smarts[i][id] = smart

					for item in items:
						for i in smarts.keys():
							id = item.get(i)
							if id:
								smart = smarts[i].get(id)
								if smart:
									item[MetaManager.Smart] = smart
									break

		except: Logger.error()
		return items

	def _metadataSmartReload(self, media, items, time, content = None, cache = None, delay = True, force = False):
		try:
			if not self._check(): return False

			if items:
				# Reload in one of these cases:
				#	1. If forced.
				#	2. If coming from cache and the cache call was more than a minute ago.
				#	3. If coming from cache and the overall usage is relativley low.
				# Do not reload if _metadataSmartLoad() was called immediately beforehand (either cache is None, or time is a few seconds ago).
				if force or (cache and ((Time.timestamp() - time) > 60 or self.providerUsage() < 0.3)):
					parameters = {'media' : media, 'items' : items, 'content' : content, 'delay' : delay}

					# NB: Do not execute in a thread if we are refreshing from reload().
					# Wait until the smart-reload is done before moving on to refreshing the next media/menu.
					if self.mModeSynchronous or self.reloadingMedia():
						if parameters['delay'] is True: parameters['delay'] = 0.05
						self._metadataSmartRefresh(**parameters)
					else:
						Pool.thread(target = self._metadataSmartRefresh, kwargs = parameters, start = True)

					return True
		except: Logger.error()
		return None

	def _metadataSmartRefresh(self, media, items, content = None, delay = True):
		try:
			if delay: Time.sleep(0.01) # Allow other code to execute.

			# Do this check only here, so that it is done in the thread and does not hold up the process.
			if self._lockSmart(media = media, content = content):
				# Allow the main code in content() to execute before we do this.
				# Prevents this code and possibly foreground metadata retrieval from delaying the menu.
				# Wait a long time, since content() can retrieve a lot of metadata when few items are cached, which can take long.
				# The wait will be less if the script execution finishes more quickly. So this is only the "maximum wait".
				# Wait at the start, so we can later get more accurate MetaTrakt/MetaImdb usage.
				Pool.wait(delay = 30.0 if delay is True else delay, minimum = True)
				timer = self._jobTimer()

				serie = Media.isSerie(media)
				episode = Media.isEpisode(media) or (serie and content == MetaManager.ContentProgress)
				pack = content == MetaManager.ContentProgress
				arrival = content == MetaManager.ContentArrival

				# Only retrieve a few items, since this function is called quite often:
				#	1. When Gaia is launched.
				#	2. When the smart menu is opened by the user.
				#	3. When a title was watched or the Trakt history changes in some way.
				# For a normal daily use, this can easily be 5+ reloads per day.
				# Especially for episode progress menus, if a new episode is requested, metadata for all episodes in that the season, all season metadata, show metadata, and pack metadata/generation is needed, which can take very long.
				# So retrieve as minimal metadata as possible in one go. Not too little, otherwise it will take forever to fully load a large Trakt history of a few thousand items.
				# Add some randomness to avoid issues when the first items can never be retrieved.
				# If all items were smart-loaded, it will start refreshing older items in case their metadata changes in the future.
				#
				# Update (2025-05): The Progress smart-list takes a few weeks to fully load, but the Arrivals smart-list takes 6 months of continuous use until fully loaded.
				# Since there are now busy-sleeps during metadata refreshing and pack generation, the background smart-reloading should not hold up Python processes that open menus for too long.
				# Increase the limit and check if it doesn't affect loading times. This can be further increased (or decreased) in the future.
				#limit = 5 if episode else 8 if serie else 10 # Just 5 items for episodes can take 60+ secs.
				limit = 6 if episode else 12 if serie else 15 # Just 5 items for episodes can take 60+ secs, mostly because of the pack generation.

				# After some time most of these items are cached and will not retrieve/refresh the metadata.
				# Increase the limit if a certain percentage of items are already smart-loaded.
				countDone = 0
				countQueue = 0
				for item in items:
					if item.get(MetaManager.Smart).get('time'): countDone += 1
					else: countQueue += 1
				done = (countDone / countQueue) if (countDone and countQueue) else 2.0 if countDone else 0.0
				more = arrival and not episode and self.mPerformanceFast
				if done >= 2.0: limit *= 2.5 if more else 2.0
				elif done >= 1.5: limit *= 2.0 if more else 1.5
				elif done >= 1.0: limit *= 1.5 if more else 1.3
				elif done >= 0.75: limit *= 1.7 if more else 1.2
				elif done >= 0.5: limit *= 1.2 if more else 1.1

				# Reduce a bit for slower devices.
				# More reduction is done in _metadataSmartChunk().
				if done >= 0.5 and not self.mPerformanceFast: limit *= 0.85

				usage = self.providerUsage()
				if usage > 0.75: limit = 0
				elif usage > 0.25: limit = max(1, int(limit * (1.0 - usage)))

				limit = int(max(1, min(50, limit)))
				limit1 = max(1, int(limit / 2.0))
				limit2 = max(1, int(limit / 5.0))
				limit3 = max(1, int(limit / 10.0))

				# Move the new and queued items to the front.
				lookup = [[], [[], [], []], []]
				current = Time.timestamp()
				items = Tools.listShuffle(items)

				for item in items:
					smarted = item.get(MetaManager.Smart).get('time')

					# Firstly, add new releases that were not smart-loaded yet.
					if not smarted: # None or 0.
						lookup[0].append(item)
						continue

					# Secondly, add recent releases that were already smart-loaded.
					# Check _metadataSmartLoad() with the "American Primeval" comment.
					# More recent releases should be reloaded more frequently, since the rating/votes are very low the first few days after release.
					# This causes important recent releases to be only listed on page 2+.
					age = self._metadataSmartRelease(media = media, item = item, current = current)
					if age:
						age = age.get('release')
						if not age is None and age > -259200: # Not more than 3 days into the future.
							if age < 604800: # 1 week.
								lookup[1][0].append(item)
								continue
							elif age < 1209600: # 2 weeks.
								lookup[1][1].append(item)
								continue
							elif age < 1814400: # 3 weeks.
								lookup[1][2].append(item)
								continue

					# Thirdly, add older releases that were already smart-loaded.
					lookup[2].append(item)

				# Titles not smart-loaded yet.
				# Prefer those that were recently released.
				lookup[0] = Tools.listSort(lookup[0], key = lambda i : max(-259200, (self._metadataSmartRelease(media = media, item = i, current = current) or {}).get('release') or 0))
				items1 = lookup[0][:limit1]
				items2 = lookup[0][limit1:]

				# Only use 10 items released in the past week, 10 items released in the past 2 weeks, and 5 items released in the past 3 weeks.
				# Only 50 items are retrieved, and we do not always want to use recent releases only. So cap them at 25.
				# Add the rest to lookup[2].
				items3 = []
				items3 += lookup[1][0][:limit2]
				lookup[2] += lookup[1][0][limit2:]
				extra = limit2 + (limit2 - len(items3))
				items3 += lookup[1][1][:extra]
				lookup[2] += lookup[1][1][extra:]
				extra = limit3 + ((2 * limit2) - len(items3))
				items3 += lookup[1][2][:extra]
				lookup[2] += lookup[1][2][extra:]

				items = []
				items += items1 # Retrieve up to 25 titles that were not smart-loaded yet.
				items += items3 # Re-retrieve up to 25 titles released in the past 3 weeks.
				items += items2 # Retrieve the remainder of the titles that were not smart-loaded yet.
				items += Tools.listSort(lookup[2], key = lambda i : i.get(MetaManager.Smart).get('time')) # Fill the remainder with already smart-loaded titles, starting with those smart-loaded the longest time ago.

				count = 0
				total = len(items)
				if limit:
					items = self._metadataSmartChunk(items = items, limit = limit)

					# Retrieve from cache, foreground or background. Aggregate to also refresh the show metadata if it is outdated.
					# Make all refreshes run in the background to add delays in between.
					items = self._metadataSmartRetrieve(items = items, quick = None, refresh = MetaCache.RefreshBackground, pack = pack, aggregate = True)

					if items: count = len(items) # Some might be retrieved from the cache. So the actual number of foreground/background retrievals might be lower.

				Logger.log('SMART RELOAD (%s %s | %dms): Total: %d | Retrieved: %d' % (media.capitalize(), (content or 'unknown').capitalize(), timer.elapsed(milliseconds = True), total, count))
		except: Logger.error()

	##############################################################################
	# METADATA - MOVIE
	##############################################################################

	def metadataMovie(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = None, cache = False, threaded = None):
		try:
			media = Media.Movie

			pickSingle = False
			pickMultiple = False

			if items:
				if Tools.isArray(items):
					pickMultiple = True
				else:
					pickSingle = True
					items = [items]
			elif trakt or imdb or tmdb or tvdb:
				pickSingle = True
				items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year}] # Add the title/year for a possible lookup if Trakt does not have the IMDb ID yet.
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				items = self._metadataCache(media = media, items = items, function = self._metadataMovieUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)
					items = self._metadataAggregate(media = media, items = items)

					if pickSingle: items = items[0] if items else None

					items = self._metadataClean(media = media, items = items, clean = clean)
					return items
		except: Logger.error()
		return None

	def _metadataMovieUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, refresh = None, part = True):
		try:
			# If many requests are made at the same time, there can be various network errors:
			#	Network Error [Error Type: Connection | Link: https://webservice.fanart.tv/v3/movies/...]: Failed to establish a new connection: [Errno 111] Connection refused
			#	Network Error [Error Type: Connection | Link: https://api.themoviedb.org/3/movie/...?api_key=...&language=en]: Connection aborted
			#	Network Error [Error Type: Connection | Link: https://api.trakt.tv/movies/.../people?extended=full]: Read timed out.
			#	Network Error [Error Type: Timeout | Link: https://webservice.fanart.tv/v3/movies/...]: Read timed out. (read timeout=45
			#	Network Error [Error Type: Connection | Link: https://api.trakt.tv/movies/.../people?extended=full]: Connection aborted
			# This applies to all providers (Trakt, TMDb, Fanart) and errors are very sporadic.
			# Although some servers might implement rate limits, it is highly unlikely that this is the cause.
			# The API would return a JSON or HTTP error if limits were exceeded. If anything, this might be caused directly by the webservers that drop connections if too many simultaneous connection are established in a short time.
			# However, this is also unlikley, because if only a single provider is used (eg just make Fanart requests and disable the rest), the errors are mostly gone.
			# It is highley likley that this is caused by a slow local internet/VPN connection.
			# Most of the errors are from Fanart, and only a few from Tratk/TMDb. Since Fanart data is larger, this might explain the errors (eg timeout) if the local internet connection is slow.
			# If these network errors occur (excluding any HTTP errors, like 404 meaning the specific movie cannot be found on the API), the following is done:
			#	1. Retrieve as much info as possible from the APIs and populate the ListItem with these values to display to the user.
			#	2. Do NOT write the data to the metadata cache, since it is incomplete. If the menu is reloaded, this function will be called again and another attempt will be made to get the metadata.
			#	3. All subrequests are cached. If eg Fanart fails, but Trakt/TMDb was successful, the menu is reloaded and this function called again, only the failed requests are redone, the other ones use the previously cached data.
			#	4. If a request fails due to network issues (excluding HTTP errors), that request is purged from the cache, so that on the next try the old/invalid cached results are not reused.

			if not self._checkInterval(mode = mode): return None

			media = Media.Movie

			ids = {'imdb' : [], 'tmdb' : [], 'tvdb' : [], 'trakt' : [], 'slug' : [], 'tvmaze' : [], 'tvrage' : []}

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')

			title = item.get('title')
			year = item.get('year')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same movie appears multiple times in the list (some Trakt lists, eg watched list where a movie was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used multiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partStatus = None
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			try:
				partCache = item.get(MetaCache.Attribute)
				if partCache:
					partStatus = partCache.get(MetaCache.AttributeStatus)
					# Only do this for StatusPartial.
					# Other non-partial statuses that cause a refresh might also have the "part" dictionary.
					# However, in these cases the old "part" data should not be used, since as full refresh is needed and all requests should be redone.
					if part and partStatus == MetaCache.StatusPartial:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
			except: Logger.error()

			if not imdb or not tmdb:
				values = partOld.get('id')
				if not values or not values.get('complete'): values = self._metadataMovieId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = values
				if values:
					if not values.get('complete'): partDone = False
					values = values.get('data')
					if values:
						value = self._metadataIdAdd(type = 'imdb', metadata = values, ids = ids)
						if not imdb: imdb = value
						value = self._metadataIdAdd(type = 'tmdb', metadata = values, ids = ids)
						if not tmdb: tmdb = value
						value = self._metadataIdAdd(type = 'tvdb', metadata = values, ids = ids)
						if not tvdb: tvdb = value
						value = self._metadataIdAdd(type = 'trakt', metadata = values, ids = ids)
						if not trakt: trakt = value
						value = self._metadataIdAdd(type = 'slug', metadata = values, ids = ids)
						if not slug: slug = value
			if not imdb and not tmdb and not tvdb and not trakt: return False

			cache = cache if cache else None
			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('MOVIE METADATA RETRIEVAL [%s - %s]: %s' % (mode.upper() if mode else 'UNKNOWN', partStatus.upper() if partStatus else 'NEW', developer))

			# DetailEssential: 2-3 requests [Trakt: 1-2 (summary, optional translations), TMDb: 1 (summary), IMDb: 0, Fanart: 0]
			# DetailStandard: 6-7 requests [Trakt: 3-4 (summary, studios, releases, optional translations), TMDb: 2 (summary, images), IMDb: 0, Fanart: 1 (summary)]
			# DetailExtended: 8-9 requests [Trakt: 4-5 (summary, people, studios, releases, optional translations), TMDb: 2 (summary, images), IMDb: 1 (summary), Fanart: 1 (summary)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'trakt', 'function' : self._metadataMovieTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'title' : title, 'year' : year, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'tmdb', 'function' : self._metadataMovieTmdb, 'parameters' : {'tmdb' : tmdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'imdb', 'function' : self._metadataMovieImdb, 'parameters' : {'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'fanart', 'function' : self._metadataMovieFanart, 'parameters' : {'imdb' : imdb, 'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				# Do not use the old parts if retrieving in the foreground.
				# Otherwise if the metadata is refreshed forcefully (eg: from the context menu), and the current MetaCache entry is incomplete, it will use the existing old parts and only refresh the previously failed/incomplete parts.
				# Instead, refresh all parts if the refresh is in the foreground.
				# MetaCache.StatusPartial refreshes happen by default in the background, which will still only re-retrieve the incomplete parts.
				if not mode == MetaCache.RefreshForeground:
					partRequests = []
					for i in requests:
						partData = partOld.get(i['id'])
						if partData and partData.get('complete'): partDatas[i['id']] = partData
						else: partRequests.append(i)
					requests = partRequests
					partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			if not self._checkInterval(mode = mode): return None
			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			if not self._checkInterval(mode = mode): return None
			datas.update(partDatas)

			data = {}
			niches = []
			genres = []
			studios = []
			networks = []
			languages = []
			countries = []
			status = []
			times = []
			durations = []
			mpaas = []
			casts = []
			directors = []
			writers = []
			creators = []
			images = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			providers = ['metacritic', 'imdb', 'fanart', 'tmdb', 'trakt'] # Keep a specific order. Later values replace newer values.
			providersImage = ['tmdb', 'fanart', 'trakt', 'imdb'] # Preferred providers must be placed first. Otherwise it might pick unwanted images first (eg IMDb).

			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('MOVIE METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							value = value['data']
							if value:
								if MetaImage.Attribute in value:
									images = Tools.update(images, value[MetaImage.Attribute], none = False, lists = True, unique = False)
									del value[MetaImage.Attribute]

								self._metadataIdAdd(metadata = value, ids = ids)

								if 'niche' in value: niches.append(value['niche'])
								if 'genre' in value: genres.append(value['genre'])
								if 'studio' in value: studios.append(value['studio'])
								if 'network' in value: networks.append(value['network'])
								if 'language' in value: languages.append(value['language'])
								if 'country' in value: countries.append(value['country'])
								if 'status' in value: status.append(value['status'])
								if 'time' in value: times.append(value['time'])
								if 'duration' in value: durations.append(value['duration'])
								if 'mpaa' in value: mpaas.append(value['mpaa'])

								if 'cast' in value: casts.append(value['cast'])
								if 'director' in value: directors.append(value['director'])
								if 'writer' in value: writers.append(value['writer'])
								if 'creator' in value: creators.append(value['creator'])

								if 'rating' in value: voting['rating'][provider] = value['rating']
								if 'votes' in value: voting['votes'][provider] = value['votes']
								if 'userrating' in value: voting['user'][provider] = value['userrating']

								data = Tools.update(data, value, none = False, lists = False, unique = False)

			genres = self.mTools.mergeGenre(genres)
			if genres: data['genre'] = genres

			languages = self.mTools.mergeLanguage(languages)
			if languages: data['language'] = languages

			countries = self.mTools.mergeCountry(countries)
			if countries: data['country'] = countries

			networks = self.mTools.mergeNetwork(networks, country = countries)
			if networks: data['network'] = networks

			# order: prefer the studios most providers list early.
			# Check that movies in sets have the same studio icons:
			#	Harry Potter (Warner Bros)
			#	The Lord of the Rings (New Line Cinema)
			#	The Hobbit (New Line Cinema)
			studios = self.mTools.mergeStudio(studios, other = networks, country = countries, order = False)
			if studios: data['studio'] = studios

			status = self.mTools.mergeStatus(status, media = media)
			if status: data['status'] = status

			times = self.mTools.mergeTime(times, metadata = data)
			if times:
				data['time'] = times

				# The "premiered" date returned by Trakt/TMDb/IMDb can vary greatly.
				# In most cases it is not actually the premiere date, but rather the limited/theatrical date or the digital date if the previous two are unavailable.
				# It also makes more sense to use the launch date here, since normal people cannot attend premieres, and the premiere can be weeks/months before the theatrical date.
				# Check MetaTools.timeGenerate() for more details.
				# https://trakt.tv/movies/bank-of-dave-2023
				launch = times.get(MetaTools.TimeLaunch)
				if launch: data['premiered'] = Time.format(launch, format = Time.FormatDate)

			durations = self.mTools.mergeDuration(durations)
			if durations: data['duration'] = durations

			mpaas = self.mTools.mergeCertificate(mpaas, media = media)
			if mpaas: data['mpaa'] = mpaas

			cast = self.mTools.mergeCast(casts)
			if cast: data['cast'] = cast

			director = self.mTools.mergeCrew(directors)
			if director: data['director'] = director

			writer = self.mTools.mergeCrew(writers)
			if writer: data['writer'] = writer

			creator = self.mTools.mergeCrew(creators)
			if creator: data['creator'] = creator

			data['media'] = media

			niche = self.mTools.mergeNiche(niches)
			niche = self.mTools.niche(niche = niche, metadata = data)
			if niche: data['niche'] = niche

			# Add the IMDb rating/votes from the bulk datasets.
			# This should never happen, since the latests rating/votes are already retrieve from HTML if MetaTools.DetailExtended.
			try:
				if self._bulkImdbEnabled():
					try: votingImdb = voting['rating']['imdb']
					except: votingImdb = None
					if votingImdb is None:
						votingImdb = self._bulkImdbLookup(imdb = data.get('imdb'))
						if votingImdb:
							voting['rating']['imdb'] = votingImdb.get('rating')
							voting['votes']['imdb'] = votingImdb.get('votes')
			except: Logger.error()

			data['voting'] = voting

			# Add the collection ID to the "id" dictionary.
			# This is added to the smart-loaded data and is later used in release().
			# Also used by preload() to load a movie set from the smart-reduced-progress-data.
			collection = Tools.get(data, 'collection', 'id')
			if collection: data['id']['collection'] = Tools.copy(collection)

			data = {k : v for k, v in data.items() if not v is None}

			# Always replace the IDs of refreshed metadata and do not use the IDs saved to MetaCache previously.
			# Since the old metadata can contain old/outdated/wrong IDs which were fixed in the newly retrieved/refreshed metadata.
			# Check for a detailed explanation under _metadataId().
			self._metadataIdUpdate(metadata = data, ids = ids)

			if images:
				MetaImage.update(media = MetaImage.MediaMovie, images = images, data = data, sort = providersImage)
			else:
				# Sometimes the images are not available, especially for new/future releases.
				# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
				partDone = False
				try: partNew['tmdb']['complete'] = False
				except: pass
				try: partNew['fanart']['complete'] = False
				except: pass
				if developer: Logger.log('MOVIE IMAGES INCOMPLETE: %s' % developer)

			# Do this before here already.
			# Otherwise a bunch of regular expressions are called every time the menu is loaded.
			self.mTools.cleanDescription(metadata = data)

			# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
			# More info under meta -> tools.py -> cleanVoting().
			self.mTools.cleanVoting(metadata = data, round = True) # Round to reduce storage space of average ratings with many decimal places.

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self._busyFinish(media = media, item = item)

	def _metadataMovieId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, quick = None):
		result = self.mTools.idMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataMovieTrakt(self, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# Do not use the cached summarized data. Only if it comes from IMDb.
			try: origin = bool(item['temp']['trakt'])
			except: origin = False

			if detail == MetaTools.DetailEssential and item and origin: # Comes from a Trakt list with basic metadata.
				if MetaCache.Attribute in item:
					result = {}
				else:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				result = self._metadataTemporize(item = item, result = result, provider = 'trakt')
			else: # Comes from another list, or forcefully retrieve detailed metadata.
				if trakt or imdb or tmdb or tvdb or title:
					# Trakt has an API limit of 1000 requests per 5 minutes.
					# Retrieving all the additional metadata will very quickly consume the limit if a few pages are loaded.
					# Only retrieve the extended metadata if enough requests are still avilable for the past 5 minutes.
					person = False
					studio = False
					release = False
					if self.mModeGenerative:
						person = True
						studio = True
						release = True
					else:
						usage = self.providerUsageTrakt(authenticated = False)
						if detail == MetaTools.DetailStandard:
							if usage < 0.7: release = True
							if usage < 0.5: studio = True
						elif detail == MetaTools.DetailExtended:
							if usage < 0.9: release = True
							if usage < 0.8: studio = True
							if usage < 0.5: person = True

					# We already retrieve the cast (with thumbnails), translations, studios, and release dates, from TMDb.
					# Retrieving all of them here again will add little new metadata and only prolong the retrieval.
					# translation = None: only retrieve for non-English.
					return MetaTrakt.instance().metadataMovie(trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, summary = True, translation = None, person = person, studio = studio, release = release, language = language, extended = True, detail = True, cache = cache, concurrency = bool(threaded))
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def _metadataMovieTmdb(self, tmdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataMovie(imdb = imdb, tmdb = tmdb, language = language, cache = cache, threaded = threaded, quick = detail == MetaTools.DetailEssential, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataMovieImdb(self, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		results = []

		# Do not use the cached summarized data. Only if it comes from IMDb.
		try: origin = not item['temp']['imdb']['voting']['rating'] is None
		except: origin = False

		# Only do this if there is no IMDb rating in in the item, that is, the item does not come from a IMDb list.
		# Retrieving the detailed IMDb data does not really add extra metadata above TMDb/Trakt, except for the rating/vote and the revenue (which is also on TMDb).
		# A single IMDb page is more than 200KB, so retrieving 50 movies will take 10MB+.
		if detail == MetaTools.DetailExtended and imdb and not origin:
			data = MetaImdb.instance().metadataMovie(id = imdb, language = language, cache = cache)
			if data:
				item = data
				origin = True

		complete = True
		result = None
		try:
			if origin and item:
				# Some titles, especially less-known docus/shorts, have metadata from IMDb, but not on TMDb or Trakt.
				# Copy the entire IMDb strucuture, so we have at least a title/plot/etc from IMDb if nothing is available from TMDb or Trakt.
				# NB: Only do this if the item did not come from the MetaCache, since it then contains metadata from other providers.
				# This can cause an exception if metadata(..., refresh = True) is called, which causes a problem with MetaImage.Attribute, since the values from the local cache are URL strings, whereas the newley retrieved images are still unprocessed dictionaries (eg from TMDb), and these arrays cannot be mixed by MetaImage.
				# Update: Also do this if it comes from the cache, but the status is "invalid", meaning the data does not come from MetaCache, but the original dict comes from one of the lists/menus.
				# Eg: basic item comes from random(). It is looked up in MetaCache but cannot be found.
				if (not MetaCache.Attribute in item or MetaCache.status(item) == MetaCache.StatusInvalid) and 'temp' in item and 'imdb' in item['temp']:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				else:
					result = {}
				result = self._metadataTemporize(item = item, result = result, provider = 'imdb')

				# Check MetaImdb._extractItems() for more details.
				for attribute in ['genre', 'language', 'country']:
					value = item.get(attribute)
					if value:
						value = Tools.listUnique(value + (result.get(attribute) or []))
						if value: result[attribute] = value
				for attribute in ['mpaa']:
					value = item.get(attribute)
					if value: result[attribute] = value

				if complete: complete = bool(result and 'rating' in result and result['rating'])
		except: Logger.error()
		results.append({'provider' : 'imdb', 'complete' : complete, 'data' : result})

		complete = True
		result = None
		try:
			if origin and item:
				result = self._metadataTemporize(item = item, result = {}, provider = 'metacritic')
		except: Logger.error()
		results.append({'provider' : 'metacritic', 'complete' : complete, 'data' : result})

		return results

	def _metadataMovieFanart(self, imdb = None, tmdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if imdb or tmdb:
				images = MetaFanart.instance().metadataMovie(imdb = imdb, tmdb = tmdb, cache = cache)
				if images is False: complete = False
				elif images: result = {MetaImage.Attribute : images}
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result}

	##############################################################################
	# METADATA - SET
	##############################################################################

	def metadataSet(self, tmdb = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = None, cache = False, threaded = None):
		try:
			media = Media.Set

			pickSingle = False
			pickMultiple = False

			if items:
				if Tools.isArray(items):
					pickMultiple = True
				else:
					pickSingle = True
					items = [items]
			elif tmdb:
				pickSingle = True
				items = [{'tmdb' : tmdb, 'title' : title, 'year' : year}]
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				items = self._metadataCache(media = media, items = items, function = self._metadataSetUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)
					items = self._metadataAggregate(media = media, items = items)

					if pickSingle: items = items[0] if items else None

					items = self._metadataClean(media = media, items = items, clean = clean)
					return items
		except: Logger.error()
		return None

	def _metadataSetUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, refresh = None, part = True):
		try:
			if not self._checkInterval(mode = mode): return None

			media = Media.Set

			ids = {'imdb' : [], 'tmdb' : [], 'tvdb' : [], 'trakt' : [], 'slug' : [], 'tvmaze' : [], 'tvrage' : []}

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')

			title = item.get('title')
			year = item.get('year')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same movie appears multiple times in the list (some Trakt lists, eg watched list where a movie was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used multiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partStatus = None
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			try:
				partCache = item.get(MetaCache.Attribute)
				if partCache:
					partStatus = partCache.get(MetaCache.AttributeStatus)
					# Only do this for StatusPartial.
					# Other non-partial statuses that cause a refresh might also have the "part" dictionary.
					# However, in these cases the old "part" data should not be used, since as full refresh is needed and all requests should be redone.
					if part and partStatus == MetaCache.StatusPartial:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
			except: Logger.error()

			if not tmdb:
				values = partOld.get('id')
				if not values or not values.get('complete'): values = self._metadataSetId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = values
				if values:
					if not values.get('complete'): partDone = False
					values = values.get('data')
					if values:
						value = self._metadataIdAdd(type = 'imdb', metadata = values, ids = ids)
						if not imdb: imdb = value
						value = self._metadataIdAdd(type = 'tmdb', metadata = values, ids = ids)
						if not tmdb: tmdb = value
						value = self._metadataIdAdd(type = 'tvdb', metadata = values, ids = ids)
						if not tvdb: tvdb = value
						value = self._metadataIdAdd(type = 'trakt', metadata = values, ids = ids)
						if not trakt: trakt = value
						value = self._metadataIdAdd(type = 'slug', metadata = values, ids = ids)
						if not slug: slug = value
			if not tmdb: return False

			cache = cache if cache else None
			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('SET METADATA RETRIEVAL [%s - %s]: %s' % (mode.upper() if mode else 'UNKNOWN', partStatus.upper() if partStatus else 'NEW', developer))

			# DetailEssential: 1 request [TMDb: 1 (summary), Fanart: 0]
			# DetailStandard: 3 requests [TMDb: 2 (summary, images), Fanart: 1 (summary)]
			# DetailExtended: 3+parts requests [TMDb: 2 (summary, images, part ID), Fanart: 1 (summary)] (1 request per part to get the IDs below for the IMDb bulk ratings)
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'tmdb', 'function' : self._metadataSetTmdb, 'parameters' : {'tmdb' : tmdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'fanart', 'function' : self._metadataSetFanart, 'parameters' : {'imdb' : imdb, 'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				# Do not use the old parts if retrieving in the foreground.
				# Otherwise if the metadata is refreshed forcefully (eg: from the context menu), and the current MetaCache entry is incomplete, it will use the existing old parts and only refresh the previously failed/incomplete parts.
				# Instead, refresh all parts if the refresh is in the foreground.
				# MetaCache.StatusPartial refreshes happen by default in the background, which will still only re-retrieve the incomplete parts.
				if not mode == MetaCache.RefreshForeground:
					partRequests = []
					for i in requests:
						partData = partOld.get(i['id'])
						if partData and partData.get('complete'): partDatas[i['id']] = partData
						else: partRequests.append(i)
					requests = partRequests
					partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			if not self._checkInterval(mode = mode): return None
			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			if not self._checkInterval(mode = mode): return None
			datas.update(partDatas)

			data = {}
			niches = []
			genres = []
			studios = []
			networks = []
			languages = []
			countries = []
			status = []
			times = []
			durations = []
			mpaas = []
			images = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			providers = ['fanart', 'tmdb'] # Keep a specific order. Later values replace newer values.
			providersImage = ['tmdb', 'fanart'] # Preferred providers must be placed first. Otherwise it might pick unwanted images first (eg IMDb).

			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('SET METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							value = value['data']
							if value:
								if MetaImage.Attribute in value:
									images = Tools.update(images, value[MetaImage.Attribute], none = False, lists = True, unique = False)
									del value[MetaImage.Attribute]

								self._metadataIdAdd(metadata = value, ids = ids)

								if 'niche' in value: niches.append(value['niche'])
								if 'genre' in value: genres.append(value['genre'])
								if 'studio' in value: studios.append(value['studio'])
								if 'network' in value: networks.append(value['network'])
								if 'language' in value: languages.append(value['language'])
								if 'country' in value: countries.append(value['country'])
								if 'status' in value: status.append(value['status'])
								if 'time' in value: times.append(value['time'])
								if 'duration' in value: durations.append(value['duration'])
								if 'mpaa' in value: mpaas.append(value['mpaa'])

								if 'rating' in value: voting['rating'][provider] = value['rating']
								if 'votes' in value: voting['votes'][provider] = value['votes']
								if 'userrating' in value: voting['user'][provider] = value['userrating']

								data = Tools.update(data, value, none = False, lists = False, unique = False)

			# If TMDb fails for some reason and has incomplete metadata.
			if data.get('part') is None: data['part'] = []

			genres = self.mTools.mergeGenre(genres)
			if genres: data['genre'] = genres

			languages = self.mTools.mergeLanguage(languages)
			if languages: data['language'] = languages

			countries = self.mTools.mergeCountry(countries)
			if countries: data['country'] = countries

			networks = self.mTools.mergeNetwork(networks, country = countries)
			if networks: data['network'] = networks

			studios = self.mTools.mergeStudio(studios, other = networks, country = countries, order = False) # order: prefer the studios most providers list early.
			if studios: data['studio'] = studios

			status = self.mTools.mergeStatus(status, media = media)
			if status: data['status'] = status

			times = self.mTools.mergeTime(times, metadata = data)
			if times:
				data['time'] = times
				launch = times.get(MetaTools.TimeLaunch)
				if launch: data['premiered'] = Time.format(launch, format = Time.FormatDate)

			durations = self.mTools.mergeDuration(durations)
			if durations: data['duration'] = durations

			mpaas = self.mTools.mergeCertificate(mpaas, media = media)
			if mpaas: data['mpaa'] = mpaas

			data['media'] = media

			niche = self.mTools.mergeNiche(niches)
			niche = self.mTools.niche(niche = niche, metadata = data)
			if niche: data['niche'] = niche

			for i in data.get('part'):
				i['voting'] = {
					'rating' : {'tmdb' : i.get('rating')},
					'votes' : {'tmdb' : i.get('votes')},
				}

			# Add the IMDb rating/votes from the bulk datasets.
			# This requires an ID lookup for each part and should therefore only be done if MetaTools.DetailExtended.
			# Loading a mneu with 50 sets with no metadata cached:
			#	Without this code: 5-7 secs
			#	With this code with ID lookups cached: 7-8 secs
			#	With this code with ID lookups not cached (Trakt lookup): 30-35 secs
			#	With this code with ID lookups not cached (TMDb lookup): 10-15 secs
			try:
				if self._bulkImdbEnabled():
					try: votingImdb = voting['rating']['imdb']
					except: votingImdb = None
					if votingImdb is None:
						def _id(tmdb, parts):
							if tmdb:
								# Do a "quick" lookup only on TMDb.
								# TMDb ID lookups are twice as fast as Trakt lookups.
								id = self._metadataMovieId(tmdb = tmdb, quick = 'tmdb')
								if id: parts[tmdb] = id
						parts = {}
						t=Time(start=True)
						threads = [Pool.thread(target = _id, kwargs = {'tmdb' : i['tmdb'], 'parts' : parts}, start = True) for i in data.get('part')]
						Pool.join(instance = threads)

						values = []
						for idTmdb, i in parts.items():
							try: idImdb = i['data']['id']['imdb']
							except: idImdb = None
							if idImdb:
								votingImdb = self._bulkImdbLookup(imdb = idImdb)
								if votingImdb:
									values.append(votingImdb)
									for j in data.get('part'):
										if j.get('tmdb') == idTmdb:
											j['voting']['rating']['imdb'] = votingImdb.get('rating')
											j['voting']['votes']['imdb'] = votingImdb.get('votes')
											self.mTools.cleanVoting(metadata = j, round = True)
											break

						votingImdb = self.mTools.votingAverageWeighted(metadata = values, maximum = True)
						if votingImdb:
							voting['rating']['imdb'] = Math.round(votingImdb.get('rating'), places = 3)
							voting['votes']['imdb'] = votingImdb.get('votes')
			except: Logger.error()

			data['voting'] = voting

			data = {k : v for k, v in data.items() if not v is None}

			# Always replace the IDs of refreshed metadata and do not use the IDs saved to MetaCache previously.
			# Since the old metadata can contain old/outdated/wrong IDs which were fixed in the newly retrieved/refreshed metadata.
			# Check for a detailed explanation under _metadataId().
			self._metadataIdUpdate(metadata = data, ids = ids)

			if images:
				MetaImage.update(media = MetaImage.MediaSet, images = images, data = data, sort = providersImage)
			else:
				# Sometimes the images are not available, especially for new/future releases.
				# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
				partDone = False
				try: partNew['tmdb']['complete'] = False
				except: pass
				try: partNew['fanart']['complete'] = False
				except: pass
				if developer: Logger.log('SET IMAGES INCOMPLETE: %s' % developer)

			data['title'] = self.mTools.cleanTitle(title = data.get('title'), media = media, parts = data.get('part'))

			# Do this before here already.
			# Otherwise a bunch of regular expressions are called every time the menu is loaded.
			self.mTools.cleanDescription(metadata = data)

			# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
			# More info under meta -> tools.py -> cleanVoting().
			self.mTools.cleanVoting(metadata = data, round = True) # Round to reduce storage space of average ratings with many decimal places.

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, tmdb = data.get('tmdb'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self._busyFinish(media = media, item = item)

	def _metadataSetId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None):
		result = self.mTools.idSet(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataSetTmdb(self, tmdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataSet(imdb = imdb, tmdb = tmdb, language = language, cache = cache, threaded = threaded, quick = detail == MetaTools.DetailEssential, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataSetFanart(self, imdb = None, tmdb = None, language = None, item = None, cache = False, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if imdb or tmdb:
				images = MetaFanart.instance().metadataSet(imdb = imdb, tmdb = tmdb, cache = cache)
				if images is False: complete = False
				elif images: result = {MetaImage.Attribute : images}
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result}

	##############################################################################
	# METADATA - SHOW
	##############################################################################

	# NB: For efficiency, call this function with "pack=False" if the pack data is not needed. More info at metadata().
	def metadataShow(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, items = None, pack = None, filter = None, clean = True, quick = None, refresh = None, cache = False, threaded = None, aggregate = True):
		try:
			media = Media.Show

			pickSingle = False
			pickMultiple = False

			refreshInternal = self._metadataRefresh(refresh = refresh)

			if items:
				if Tools.isArray(items):
					pickMultiple = True
				else:
					pickSingle = True
					items = [items]
			elif trakt or imdb or tmdb or tvdb:
				pickSingle = True
				items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year}] # Add the title/year for a possible lookup if Trakt does not have the IMDb ID yet.
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				items = self._metadataCache(media = media, items = items, function = self._metadataShowUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)
					items = self._metadataAggregate(media = media, items = items)

					if pickSingle: items = items[0] if items else None

					# Do not add "refresh" here, otherwise the pack will be refreshed every time a season is refreshed.
					# Only add "refreshInternal" which is either False or None.
					items = self._metadataPackAggregate(items = items, pack = pack, refresh = refreshInternal, quick = quick, cache = cache, threaded = threaded)

					# Aggregate the season images for Arrivals menus.
					# This is a lightweight aggregation, which only retrieves from the local cache.
					# Hence, if the season metadata is in the cache, season images are displayed.
					# If the season metadata is not in the cache, use show images instead.
					# If there is no cached metadata for any of the titles, this adds 5-10ms.
					# If the metadata is cached for most titles, this adds about 50-100ms.
					# The first page of Arrivals is cached, so the extra time will only apply to pages 2+.
					if aggregate: items = self._metadataShowAggregate(items = items, refresh = refreshInternal, threaded = threaded)

					items = self._metadataClean(media = media, items = items, clean = clean)

					return items
		except: Logger.error()
		return None

	def _metadataShowUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, refresh = None, part = True):
		try:
			if not self._checkInterval(mode = mode): return None

			media = Media.Show

			ids = {'imdb' : [], 'tmdb' : [], 'tvdb' : [], 'trakt' : [], 'slug' : [], 'tvmaze' : [], 'tvrage' : []}

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')
			tvmaze = item.get('tvmaze')
			tvrage = item.get('tvrage')

			title = item.get('tvshowtitle') or item.get('title')
			year = item.get('tvshowyear') or item.get('year')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used multiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partStatus = None
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			try:
				partCache = item.get(MetaCache.Attribute)
				if partCache:
					partStatus = partCache.get(MetaCache.AttributeStatus)
					# Only do this for StatusPartial.
					# Other non-partial statuses that cause a refresh might also have the "part" dictionary.
					# However, in these cases the old "part" data should not be used, since as full refresh is needed and all requests should be redone.
					if part and partStatus == MetaCache.StatusPartial:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
			except: Logger.error()

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not tvdb or (not imdb and not trakt) or (self.mLevel >= 2 and not tmdb):
				values = partOld.get('id')
				if not values or not values.get('complete'): values = self._metadataShowId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = values
				if values:
					if not values.get('complete'): partDone = False
					values = values.get('data')
					if values:
						value = self._metadataIdAdd(type = 'imdb', metadata = values, ids = ids)
						if not imdb: imdb = value
						value = self._metadataIdAdd(type = 'tmdb', metadata = values, ids = ids)
						if not tmdb: tmdb = value
						value = self._metadataIdAdd(type = 'tvdb', metadata = values, ids = ids)
						if not tvdb: tvdb = value
						value = self._metadataIdAdd(type = 'trakt', metadata = values, ids = ids)
						if not trakt: trakt = value
						value = self._metadataIdAdd(type = 'slug', metadata = values, ids = ids)
						if not slug: slug = value
						value = self._metadataIdAdd(type = 'tvmaze', metadata = values, ids = ids)
						if not tvmaze: tvmaze = value
						value = self._metadataIdAdd(type = 'tvrage', metadata = values, ids = ids)
						if not tvrage: tvrage = value
			if not imdb and not tmdb and not tvdb and not trakt: return False

			cache = cache if cache else None
			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('SHOW METADATA RETRIEVAL [%s - %s]: %s' % (mode.upper() if mode else 'UNKNOWN', partStatus.upper() if partStatus else 'NEW', developer))

			# DetailEssential: 2-3 requests [Trakt: 1-2 (summary, optional translations), TVDb: 1 (summary), TMDb: 0, IMDb: 0, Fanart: 0]
			# DetailStandard: 4-5 requests [Trakt: 2-3 (summary, studios, optional translations), TVDb: 1 (summary), TMDb: 0, IMDb: 0, Fanart: 1 (summary)]
			# DetailExtended: 8-9 requests [Trakt: 3-4 (summary, people, studios, optional translations), TVDb: 1 (summary), TMDb: 2 (summary), IMDb: 1 (summary), Fanart: 1 (summary)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'trakt', 'function' : self._metadataShowTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'title' : title, 'year' : year, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'tvdb', 'function' : self._metadataShowTvdb, 'parameters' : {'tvdb' : tvdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'imdb', 'function' : self._metadataShowImdb, 'parameters' : {'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'fanart', 'function' : self._metadataShowFanart, 'parameters' : {'tvdb' : tvdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
					if self.mLevel >= 2:
						requests.append({'id' : 'tmdb', 'function' : self._metadataShowTmdb, 'parameters' : {'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				# Do not use the old parts if retrieving in the foreground.
				# Otherwise if the metadata is refreshed forcefully (eg: from the context menu), and the current MetaCache entry is incomplete, it will use the existing old parts and only refresh the previously failed/incomplete parts.
				# Instead, refresh all parts if the refresh is in the foreground.
				# MetaCache.StatusPartial refreshes happen by default in the background, which will still only re-retrieve the incomplete parts.
				if not mode == MetaCache.RefreshForeground:
					partRequests = []
					for i in requests:
						partData = partOld.get(i['id'])
						if partData and partData.get('complete'): partDatas[i['id']] = partData
						else: partRequests.append(i)
					requests = partRequests
					partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			if not self._checkInterval(mode = mode): return None
			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			if not self._checkInterval(mode = mode): return None
			datas.update(partDatas)

			data = {}
			niches = []
			genres = []
			studios = []
			networks = [[], []]
			languages = []
			countries = []
			status = []
			times = []
			timed = {}
			durations = []
			mpaas = []
			casts = []
			directors = []
			writers = []
			creators = []
			images = {}
			packs = {}
			counts = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			providers = ['metacritic', 'imdb', 'tmdb', 'fanart', 'tvdb', 'trakt'] # Keep a specific order. Later values replace newer values.
			providersImage = ['tvdb', 'fanart', 'tmdb', 'trakt', 'imdb'] # Preferred providers must be placed first. Otherwise some shows might pick the IMDb image. Eg: tt19401686 (Trakt: the-vikings-2015 vs the-vikings-2015-248534).

			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('SHOW METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							value = value['data']
							if value:
								if MetaImage.Attribute in value:
									images = Tools.update(images, value[MetaImage.Attribute], none = False, lists = True, unique = False)
									del value[MetaImage.Attribute]

								self._metadataIdAdd(metadata = value, ids = ids)

								if 'niche' in value: niches.append(value['niche'])
								if 'genre' in value: genres.append(value['genre'])
								if 'studio' in value: studios.append(value['studio'])
								if 'network' in value: networks[1 if i == 'tvdb' else 0].append(value['network'])
								if 'language' in value: languages.append(value['language'])
								if 'country' in value: countries.append(value['country'])
								if 'status' in value: status.append(value['status'])
								if 'time' in value:
									times.append(value['time'])
									timed[i] = value['time']
								if 'duration' in value: durations.append(value['duration'])
								if 'mpaa' in value: mpaas.append(value['mpaa'])

								if 'cast' in value: casts.append(value['cast'])
								if 'director' in value: directors.append(value['director'])
								if 'writer' in value: writers.append(value['writer'])
								if 'creator' in value: creators.append(value['creator'])

								if 'rating' in value: voting['rating'][provider] = value['rating']
								if 'votes' in value: voting['votes'][provider] = value['votes']
								if 'userrating' in value: voting['user'][provider] = value['userrating']

								if 'packed' in value: packs[i] = value['packed']
								if 'count' in value: counts[i] = value['count']

								data = Tools.update(data, value, none = False, lists = False, unique = False)

			genres = self.mTools.mergeGenre(genres)
			if genres: data['genre'] = genres

			languages = self.mTools.mergeLanguage(languages)
			if languages: data['language'] = languages

			countries = self.mTools.mergeCountry(countries)
			if countries: data['country'] = countries

			# Trakt and TMDb often list multiple networks if shows are later taken over by a new network.
			#	Community:
			#		TMDb: ['NBC', 'Yahoo! Screen']
			#		TVDB: ['NBC', 'Yahoo! Screen', 'YouTube']
			#		Trakt: ['Yahoo! Screen']
			#	Vikings:
			#		TMDb: ['Prime Video', 'History']
			#		TVDB: ['History Canada']
			#		Trakt: ['Amazon']
			#	The Boys
			#		TMDb: ['Prime Video']
			#		TVDB: ['Prime Video', 'YouTube']
			#		Trakt: ['Amazon']
			# Although Trakt lists multiple networks on their website (from earliest to newest network), it only returns the newest network via the API.
			# TMDb sometimes lists the earlier networks first, sometimes the newer networks.
			# TVDb has an original network attribute, which will be added first to the list. So prefer TVDb.
			networks = self.mTools.mergeNetwork(networks[0] + networks[1], order = True, country = countries) # They get reversed in merge(), so place TVDb last.
			if networks: data['network'] = networks

			studios = self.mTools.mergeStudio(studios, other = networks, country = countries)
			if studios: data['studio'] = studios

			status = self.mTools.mergeStatus(status, media = media)
			if status: data['status'] = status

			times = self.mTools.mergeTime(times, providers = timed, metadata = data)
			if times:
				data['time'] = times

				zone = (data.get('airs') or {}).get('zone')
				premiere = times.get(MetaTools.TimePremiere)
				accurate = True

				# Recalculate the date to accomodate timezones.
				# Late night shows from the US that air late at night have a GMT time early in the morning of the next day on Trakt.
				# This mostly matters for episodes, not that much for shows and seasons.
				# Eg: The Tonight Show Starring Jimmy Fallon S02E44 (Trakt: 2015-03-21T03:30:00Z, actual date in the timezone of release: 2015-03-20 23:30)
				if Tools.isInteger(premiere):
					# If Trakt does not have a premiere date yet (eg: future unreleased season), do not replace the date that was calculated with the show's timezone.
					# TVDb only has the date, but does not have the time.
					# Hence, converting the TVDb timestamp to a date using the show's timezone (which comes from Trakt) can result in an incorrect date (off by 1 day).
					# Eg: 2025-01-02 00:00:00 (GMT's timezone) might be converted to 2025-01-01 22:00:00 (show's timezone).
					if not zone or not (timed.get(MetaTools.ProviderTrakt) or {}).get(MetaTools.TimePremiere): accurate = False

					# Update (2025-11):
					# The Late Show with Stephen Colbert had the following date on Trakt for a very long time: 2015-09-08 (1441769400)
					# This date included the timezone offset based on the airing time in NY.
					# However, Trakt seems to now have removed the offset from the show's premiere date and no has: 2015-09-08T00:00:00Z (1441670400).
					# This is only for this show, not other shows, including other late-night shows.
					# This probably happened, because the airing time of Colbert changed.
					# Earlier seasons/episodes have an airing date with a time of 03:30, while the last episode S11E34 now has 04:30.
					# So maybe Trakt removed the offset because of the airing time discrepancy between different episodes.
					# Colbert S01 still has the offset on Trakt. It was only removed for the show metadata.
					# We could just ignore this and use the new offset-less timezone date.
					# However, this would make the show's premiere date 2015-09-07, while the actual premiere date is still 2015-09-08.
					# We now detect if the date returned by Trakt ends with "...T00:00:00.000Z", indicating a possible offset removal.
					# However, this cannot be done on face-value, since some shows will actually have a date ending in "...T00:00:00.000Z", which does still include the offset (eg: Heroes).
					# Hence, in trakt.py we check if the date ends with "...T00:00:00.000Z" AND the airing time does not end in "...:00" (eg: 04:30).
					# If the airing time has a minute value (not :00), but the premiere date does not, assume the offset was removed, and therefore do not use the timezone in the date-string creation below.
					try: offset = data['temp']['trakt']['offset']
					except: offset = True

					premiere = Time.format(premiere, format = Time.FormatDate, zone = zone if offset else None)

				# Only update if there is no date, or there is a date and a timezone.
				if premiere and (accurate or not data.get('premiered')): data['premiered'] = data['aired'] = premiere

			durations = self.mTools.mergeDuration(durations, short = self.mTools.niche(niche = self.mTools.mergeNiche(niches), media = media, metadata = data))
			if durations: data['duration'] = durations

			mpaas = self.mTools.mergeCertificate(mpaas, media = media)
			if mpaas: data['mpaa'] = mpaas

			cast = self.mTools.mergeCast(casts)
			if cast: data['cast'] = cast

			director = self.mTools.mergeCrew(directors)
			if director: data['director'] = director

			writer = self.mTools.mergeCrew(writers)
			if writer: data['writer'] = writer

			creator = self.mTools.mergeCrew(creators)
			if creator: data['creator'] = creator

			seasons = None
			episodes = None
			count = self.mTools.mergeCount(counts)
			if count:
				data['count'] = count
				try: seasons = count['season']['total'] or count['season']['released']
				except: pass
				try: episodes = count['episode']['total'] or count['episode']['released']
				except: pass

			data['media'] = media

			niche = self.mTools.mergeNiche(niches)

			# Add the episode release interval to the niche.
			# This can only be calculated from MetaPack.
			# Do not retrieve or generate the pack if the show metadata is refreshed, due to performance implications.
			# The release niche is added to the show in _metadataPackUpdate().
			# Extract it here from the cached metadata and add it to the new data.
			# This niche will only be available if the show has ever generated a pack.
			# But since this the release type is only used during scraping (from the episode metadata), not having it for the show metadata should be fine.
			niched = item.get('niche')
			if niched:
				niched = Media.type(niched, Media.Interval)
				if niched:
					if niche is None: niche = []
					niche.append(niched)

			niche = self.mTools.niche(niche = niche, metadata = data, seasons = seasons, episodes = episodes)
			if niche: data['niche'] = niche

			# Add the IMDb rating/votes from the bulk datasets.
			# This should never happen, since the latests rating/votes are already retrieve from HTML if MetaTools.DetailExtended.
			try:
				if self._bulkImdbEnabled():
					try: votingImdb = voting['rating']['imdb']
					except: votingImdb = None
					if votingImdb is None:
						votingImdb = self._bulkImdbLookup(imdb = data.get('imdb'))
						if votingImdb:
							voting['rating']['imdb'] = votingImdb.get('rating')
							voting['votes']['imdb'] = votingImdb.get('votes')
			except: Logger.error()

			data['voting'] = voting

			data = {k : v for k, v in data.items() if not v is None}

			# Always replace the IDs of refreshed metadata and do not use the IDs saved to MetaCache previously.
			# Since the old metadata can contain old/outdated/wrong IDs which were fixed in the newly retrieved/refreshed metadata.
			# Check for a detailed explanation under _metadataId().
			self._metadataIdUpdate(metadata = data, ids = ids)

			if not data.get('tvshowtitle') and data.get('title'): data['tvshowtitle'] = data['title']

			# Just for consistency with season/episode metadata.
			year = data.get('year')
			if not year and times:
				premiere = times.get(MetaTools.TimePremiere)
				if premiere: year = Time.year(premiere)
			data['tvshowyear'] = data['year'] = year

			if images:
				MetaImage.update(media = MetaImage.MediaShow, images = images, data = data, sort = providersImage)
			else:
				# Sometimes the images are not available, especially for new/future releases.
				# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
				partDone = False
				try: partNew['tvdb']['complete'] = False
				except: pass
				try: partNew['fanart']['complete'] = False
				except: pass
				if developer: Logger.log('SHOW IMAGES INCOMPLETE: %s' % developer)

			# Do this before here already.
			# Otherwise a bunch of regular expressions are called every time the menu is loaded.
			self.mTools.cleanDescription(metadata = data)

			# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
			# More info under meta -> tools.py -> cleanVoting().
			self.mTools.cleanVoting(metadata = data, round = True) # Round to reduce storage space of average ratings with many decimal places.

			# Use the base pack counts/durations from TMDb and Trakt.
			# TMDb has more detailed counts than Trakt.
			# Prefer the old reduced pack data added by _metadataPackUpdate().
			# Otherwise if we refresh the show metadata, the reduced pack data is gone until the pack is updated again.
			# These "inaccurate" counters are used to display episode counts in some skins (eg Aeon Nox) in show menus.
			pack = {}
			try: pack.update(packs.get('trakt')) # Least accurate.
			except: pass
			try: pack.update(packs.get('tmdb')) # More accurate.
			except: pass
			try: pack.update(item.get('packed')) # Most accurate, since it was calculated from the full pack.
			except: pass
			if pack: data['packed'] = pack

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self._busyFinish(media = media, item = item)

	def _metadataShowId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, quick = None):
		result = self.mTools.idShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataShowTrakt(self, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# Do not use the cached summarized data. Only if it comes from IMDb.
			try: origin = bool(item['temp']['trakt'])
			except: origin = False

			if detail == MetaTools.DetailEssential and item and origin: # Comes from a Trakt list with basic metadata.
				if MetaCache.Attribute in item:
					result = {}
				else:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				result = self._metadataTemporize(item = item, result = result, provider = 'trakt')
			else: # Comes from another list, or forcefully retrieve detailed metadata.
				if trakt or imdb or tmdb or tvdb or title:
					# Trakt has an API limit of 1000 requests per 5 minutes.
					# Retrieving all the additional metadata will very quickly consume the limit if a few pages are loaded.
					# Only retrieve the extended metadata if enough requests are still avilable for the past 5 minutes.
					person = False
					studio = False
					if self.mModeGenerative:
						person = True
						studio = True
					else:
						usage = self.providerUsageTrakt(authenticated = False)
						if detail == MetaTools.DetailStandard:
							if usage < 0.5: studio = True
						elif detail == MetaTools.DetailExtended:
							if usage < 0.8: studio = True
							if usage < 0.5: person = True

					# We already retrieve the cast (with thumbnails), translations and studios, from TMDb.
					# Retrieving all of them here again will add little new metadata and only prolong the retrieval.
					# translation = None: only retrieve for non-English.
					result = MetaTrakt.instance().metadataShow(trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, summary = True, translation = None, person = person, studio = studio, language = language, extended = True, detail = True, cache = cache, concurrency = bool(threaded))

					if result.get('complete'):
						# Create basic pack data in case the full pack metadata has not been retrieved yet.
						# Is used by some skins (eg Aeon Nox) to display episode counts for show menus.
						try:
							data = result.get('data')
							if data:
								pack = MetaPack.reduceBase(episodeOfficial = (data.get('count') or {}).get('released'), duration = data.get('duration'))
								if pack: result['data']['packed'] = pack
						except: Logger.error()

					return result # Already contains the outer structure.
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def _metadataShowTvdb(self, tvdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTvdb.instance().metadataShow(tvdb = tvdb, imdb = imdb, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : True, 'data' : None}

	def _metadataShowTmdb(self, tmdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataShow(tmdb = tmdb, language = language, cache = cache, threaded = threaded, quick = detail == MetaTools.DetailEssential, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataShowImdb(self, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		results = []

		# Do not use the cached summarized data. Only if it comes from IMDb.
		try: origin = not item['temp']['imdb']['voting']['rating'] is None
		except: origin = False

		# Only do this if there is no IMDb rating in in the item, that is, the item does not come from a IMDb list.
		# Retrieving the detailed IMDb data does not really add extra metadata above TMDb/Trakt, except for the rating/vote and the revenue (which is also on TMDb).
		# A single IMDb page is more than 200KB, so retrieving 50 shows will take 10MB+.
		if detail == MetaTools.DetailExtended and imdb and not origin:
			data = MetaImdb.instance().metadataShow(id = imdb, language = language, cache = cache)
			if data:
				item = data
				origin = True

		complete = True
		result = None
		try:
			if origin and item:
				# Some titles, especially less-known docus/shorts, have metadata from IMDb, but not on TMDb or Trakt.
				# Copy the entire IMDb strucuture, so we have at least a title/plot/etc from IMDb if nothing is available from TMDb or Trakt.
				# NB: Only do this if the item did not come from the MetaCache, since it then contains metadata from other providers.
				# This can cause an exception if metadata(..., refresh = True) is called, which causes a problem with MetaImage.Attribute, since the values from the local cache are URL strings, whereas the newley retrieved images are still unprocessed dictionaries (eg from TMDb), and these arrays cannot be mixed by MetaImage.
				# Update: Also do this if it comes from the cache, but the status is "invalid", meaning the data does not come from MetaCache, but the original dict comes from one of the lists/menus.
				# Eg: basic item comes from random(). It is looked up in MetaCache but cannot be found.
				if (not MetaCache.Attribute in item or MetaCache.status(item) == MetaCache.StatusInvalid) and 'temp' in item and 'imdb' in item['temp']:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				else:
					result = {}
				result = self._metadataTemporize(item = item, result = result, provider = 'imdb')

				# Check MetaImdb._extractItems() for more details.
				for attribute in ['genre', 'language', 'country']:
					value = item.get(attribute)
					if value:
						value = Tools.listUnique(value + (result.get(attribute) or []))
						if value: result[attribute] = value
				for attribute in ['mpaa']:
					value = item.get(attribute)
					if value: result[attribute] = value

				if complete: complete = bool(result and 'rating' in result and result['rating'])
		except: Logger.error()
		results.append({'provider' : 'imdb', 'complete' : complete, 'data' : result})

		complete = True
		result = None
		try:
			if origin and item:
				result = self._metadataTemporize(item = item, result = {}, provider = 'metacritic')
		except: Logger.error()
		results.append({'provider' : 'metacritic', 'complete' : complete, 'data' : result})

		return results

	def _metadataShowFanart(self, tvdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if tvdb:
				images = MetaFanart.instance().metadataShow(tvdb = tvdb, cache = cache)
				if images is False: complete = False
				elif images: result = {MetaImage.Attribute : images}
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result}

	def _metadataShowAggregate(self, items, refresh = None, threaded = None):
		try:
			if items:
				# Only aggregate if it contains a season number.
				# Eg: Arrivals menu.
				item = items[0] if Tools.isList(items) else items
				if not item.get('season') is None:
					# quick = False: Do not retrieve/refresh season or pack metadata. Only retrieve what is in the cache.
					# Otherwise for the Arrivals menu, this would retrieve too much lower-level metadata for each show listed in the menu.
					# aggregate = False: Do not aggregate the show, since this is already the show object.
					items = self._metadataEpisodeAggregate(items = items, threaded = threaded, refresh = refresh, quick = False, aggregate = False)
		except: Logger.error()
		return items

	##############################################################################
	# METADATA - SEASON
	##############################################################################

	# NB: For efficiency, call this function with "pack=False" if the pack data is not needed. More info at metadata().
	def metadataSeason(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, items = None, pack = None, filter = None, clean = True, quick = None, refresh = None, cache = False, threaded = None, aggregate = True, hint = None):
		try:
			media = Media.Season

			pickSingle = False
			pickMultiple = False

			refreshInternal = self._metadataRefresh(refresh = refresh)

			if items:
				if Tools.isArray(items):
					pickMultiple = True
				else:
					pickSingle = True
					if season is None: season = items.get('season')
					items = [items]
			elif trakt or imdb or tmdb or tvdb:
				pickSingle = True
				items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year}] # Add the title/year for a possible lookup if Trakt does not have the IMDb ID yet.
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				items = self._metadataCache(media = media, items = items, function = self._metadataSeasonUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded, hint = hint)

				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)
					items = self._metadataAggregate(media = media, items = items) # Must be before picking, since it uses temp and the internal "seasons" list.

					if items:
						picks = None
						if pickSingle:
							picks = items[0].get('seasons')
							if picks and not season is None:
								temp = None
								for i in picks:
									if i['season'] == season:
										temp = i
										break
								picks = temp
						elif not items[0].get('season') is None:
							# Use to select a single season for different shows from navigator -> History -> Seasons.
							picks = []
							for item in items:
								for i in (item.get('seasons') or []):
									if i['season'] == item['season']:
										picks.append(i)
										break
						else:
							picks = [item['seasons'] for item in items]
						items = picks

						if items:
							# Do not add "refresh" here, otherwise the pack will be refreshed every time a season is refreshed.
							# Only add "refreshInternal" which is either False or None.
							items = self._metadataPackAggregate(items = items, pack = pack, refresh = refreshInternal, quick = quick, cache = cache, threaded = threaded)
							if aggregate: items = self._metadataSeasonAggregate(items = items, refresh = refreshInternal, threaded = threaded)
							items = self._metadataClean(media = media, items = items, clean = clean)
							return items
		except: Logger.error()
		return None

	def _metadataSeasonUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, refresh = None, part = True):
		try:
			if not self._checkInterval(mode = mode): return None

			media = Media.Season

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')
			tvmaze = item.get('tvmaze')
			tvrage = item.get('tvrage')

			title = item.get('tvshowtitle') or item.get('title')
			year = item.get('tvshowyear') or item.get('year')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used multiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partStatus = None
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			try:
				partCache = item.get(MetaCache.Attribute)
				if partCache:
					partStatus = partCache.get(MetaCache.AttributeStatus)
					# Only do this for StatusPartial.
					# Other non-partial statuses that cause a refresh might also have the "part" dictionary.
					# However, in these cases the old "part" data should not be used, since as full refresh is needed and all requests should be redone.
					if part and partStatus == MetaCache.StatusPartial:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
			except: Logger.error()

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not tvdb or (not imdb and not trakt) or (self.mLevel >= 2 and (not tmdb or not not imdb)):
				ids = partOld.get('id')
				if not ids or not ids.get('complete'): ids = self._metadataSeasonId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = ids
				if ids:
					if not ids.get('complete'): partDone = False
					ids = ids.get('data')
					if ids:
						ids = ids.get('id')
						if ids:
							if not imdb: imdb = ids.get('imdb')
							if not tmdb: tmdb = ids.get('tmdb')
							if not tvdb: tvdb = ids.get('tvdb')
							if not trakt: trakt = ids.get('trakt')
							if not slug: slug = ids.get('slug')
							if not tvmaze: tvmaze = ids.get('tvmaze')
							if not tvrage: tvrage = ids.get('tvrage')
			if not imdb and not tmdb and not tvdb and not trakt: return False

			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('SEASON METADATA RETRIEVAL [%s - %s]: %s' % (mode.upper() if mode else 'UNKNOWN', partStatus.upper() if partStatus else 'NEW', developer))

			show = self.metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, pack = False, refresh = refresh, threaded = threaded)
			if not show:
				Memory.set(id = id, value = {}, local = True, kodi = False)
				return False

			# Use the IDs of the show metadata.
			# This is useful if Trakt does not have the IMDb/TVDb ID yet.
			# The show metadata would have already done a MetaTrakt.lookup(), so it does not have to be done here again.
			# Always replace the values, in case the season metadata still contains old IDs or title.
			idsShow = show.get('id')
			if idsShow:
				trakt = idsShow.get('trakt') or trakt
				imdb = idsShow.get('imdb') or imdb
				tmdb = idsShow.get('tmdb') or tmdb
				tvdb = idsShow.get('tvdb') or tvdb
				slug = idsShow.get('slug') or slug
			parentTitle = title = show.get('tvshowtitle') or show.get('title') or title
			parentYear = year = show.get('tvshowyear') or show.get('year') or year

			pack = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, refresh = refresh, threaded = threaded)
			if not self._checkInterval(mode = mode): return None
			pack = MetaPack.instance(pack = pack)

			cache = cache if cache else None

			# count = number of seasons.
			# DetailEssential: (count + 2) requests (eg: 10 seasons = 11 requests) [Trakt: 1 (summary), TVDb: 2-count (summary, each season), TMDb: 0, IMDb: 0, Fanart: 0 (summary)]
			# DetailStandard: ((1-2)*count + 3) requests (eg: 10 seasons = 12 requests or 21 requests with translations) [Trakt: 1 or (1-count) (summary, optional translations), TVDb: 2-count (summary, each season), TMDb: 0, IMDb: 0, Fanart: 1 (summary)]
			# DetailExtended: ((3-4)*count + 5-7) requests (eg: 10 seasons = 32 requests or 42 requests with translations) [Trakt: (2-count) or (2*count) (summary, each season, optional translations), TVDb: 2-count (summary, each season), TMDb: 2-(count/20) (summary, each season), IMDb: 1-count (each season), Fanart: 1 (summary)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'trakt', 'function' : self._metadataSeasonTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'title' : title, 'year' : year, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'tvdb', 'function' : self._metadataSeasonTvdb, 'parameters' : {'tvdb' : tvdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'fanart', 'function' : self._metadataSeasonFanart, 'parameters' : {'tvdb' : tvdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
					if self.mLevel >= 2:
						requests.append({'id' : 'tmdb', 'function' : self._metadataSeasonTmdb, 'parameters' : {'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
						requests.append({'id' : 'imdb', 'function' : self._metadataSeasonImdb, 'parameters' : {'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				# Do not use the old parts if retrieving in the foreground.
				# Otherwise if the metadata is refreshed forcefully (eg: from the context menu), and the current MetaCache entry is incomplete, it will use the existing old parts and only refresh the previously failed/incomplete parts.
				# Instead, refresh all parts if the refresh is in the foreground.
				# MetaCache.StatusPartial refreshes happen by default in the background, which will still only re-retrieve the incomplete parts.
				if not mode == MetaCache.RefreshForeground:
					partRequests = []
					for i in requests:
						partData = partOld.get(i['id'])
						if partData and partData.get('complete'): partDatas[i['id']] = partData
						else: partRequests.append(i)
					requests = partRequests
					partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			if not self._checkInterval(mode = mode): return None
			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			if not self._checkInterval(mode = mode): return None
			datas.update(partDatas)

			data = {'seasons' : []}
			niches = {}
			genres = {}
			studios = {}
			networks = {}
			languages = {}
			countries = {}
			statuses = {}
			types = {}
			times = {}
			timed = {}
			durations = {}
			mpaas = {}
			casts = {}
			directors = {}
			writers = {}
			creators = {}
			images = {}
			votings = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			providers = ['metacritic', 'imdb', 'tmdb', 'fanart', 'tvdb', 'trakt'] # Keep a specific order. Later values replace newer values.
			providersImage = ['tvdb', 'fanart', 'tmdb', 'trakt', 'imdb'] # Preferred providers must be placed first. Otherwise it might pick unwanted images first (eg IMDb).

			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('SEASON METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							seasons = value['data']
							if seasons:
								seasons = Tools.copy(seasons) # Copy, since we do title/plot/studio replacement below in another loop.
								for season in seasons:
									number = season['season']

									if MetaImage.Attribute in season:
										if not number in images: images[number] = {}
										images[number] = Tools.update(images[number], season[MetaImage.Attribute], none = False, lists = True, unique = False)
										del season[MetaImage.Attribute]

									if 'niche' in season:
										if not number in niches: niches[number] = []
										niches[number].append(season['niche'])
									if 'genre' in season:
										if not number in genres: genres[number] = []
										genres[number].append(season['genre'])
									if 'studio' in season:
										if not number in studios: studios[number] = []
										studios[number].append(season['studio'])
									if 'network' in season:
										if not number in networks: networks[number] = [[], []]
										networks[number][1 if i == 'tvdb' else 0].append(season['network'])
									if 'language' in season:
										if not number in languages: languages[number] = []
										languages[number].append(season['language'])
									if 'country' in season:
										if not number in countries: countries[number] = []
										countries[number].append(season['country'])
									if 'status' in season:
										if not number in statuses: statuses[number] = []
										statuses[number].append(season['status'])
									if 'type' in season:
										if not number in types: types[number] = []
										types[number].append(season['type'])
									if 'time' in season:
										if not number in times: times[number] = []
										times[number].append(season['time'])
										if not number in timed: timed[number] = {}
										timed[number][i] = season['time']
									if 'duration' in season:
										if not number in durations: durations[number] = []
										durations[number].append(season['duration'])
									if 'mpaa' in season:
										if not number in mpaas: mpaas[number] = []
										mpaas[number].append(season['mpaa'])

									if 'cast' in season:
										if not number in casts: casts[number] = []
										casts[number].append(season['cast'])
									if 'director' in season:
										if not number in directors: directors[number] = []
										directors[number].append(season['director'])
									if 'writer' in season:
										if not number in writers: writers[number] = []
										writers[number].append(season['writer'])
									if 'creator' in season:
										if not number in creators: creators[number] = []
										creators[number].append(season['creator'])

									if not number in votings: votings[number] = Tools.copy(voting)
									if 'rating' in season: votings[number]['rating'][provider] = season['rating']
									if 'votes' in season: votings[number]['votes'][provider] = season['votes']
									if 'userrating' in season: votings[number]['user'][provider] = season['userrating']

									found = False
									for j in data['seasons']:
										if j['season'] == number:
											found = True
											Tools.update(j, season, none = False, lists = False, unique = False)
											break
									if not found: data['seasons'].append(season)

			# Fanart can sometimes return images for a season that does not exist.
			# Eg: Dexter S09.
			# Remove any season that does not have an ID or title.
			# IMDb sometimes returns a season that does not exist, such as for specials. Do not filter these out.
			# Eg: The Office UK S03 (IMDb).
			data['seasons'] = [i for i in data['seasons'] if i.get('title') or any((i.get('id') or {}).get(j) or (i.get('temp') or {}).get('imdb') for j in providers)]

			if pack:
				# Copy the additional numbers(eg: season number given as the year) from the pack.
				numbers = {pack.numberStandard(item = i) : pack.number(item = i, number = False) for i in pack.season(default = [])}
				for i in data['seasons']:
					try: i['number'] = numbers[i['season']]
					except: i['number'] = {MetaPack.NumberStandard : i['season']}
					i['packed'] = pack.reduce(season = i['season'])

				# Fanart sometimes has images for non-existing seasons.
				# Eg: "How I Met Your Mother" has Fanart posters for Season 89.
				# Remove these seasons.
				numbers = list(numbers.keys())
				numberMaximum = (max(numbers) if numbers else 0) + 10
				data['seasons'] = [i for i in data['seasons'] if i['season'] in numbers or i['season'] <= numberMaximum]

			# Add summarized pack data to seasons only existing on IMDb.
			# Eg: The Office UK S03 (IMDb).
			for i in data['seasons']:
				if not i.get('packed'):
					count = ((i.get('temp') or {}).get('imdb') or {}).get('count')
					if count: i['packed'] = MetaPack.reduceBase(episodeOfficial = count)

			# Some values are often missing or incorrect on TVDb, and should be replaced with the Trakt/TMDb metadata.
			# TVDb has often incorrect studios/networks for seasons (eg: Game of Thrones and Breaking Bad).
			# TVDb typically does not have a title and plot for seasons. Even if there are plots, it is only available in other languages, except English.
			# TVDb also does not have the cast for seasons. But we do not retrieve the cast from Trakt, since it requires an additional API call per season, and does not have actor thumbnails. Use the show cast from TVDb which has thumbnails.
			for i in ['trakt', 'tmdb']: # Place TMDb last, since it has more translated season titles than Trakt.
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							seasons = value['data']
							if seasons:
								for season in seasons:
									for j in data['seasons']:
										if j['season'] == season['season']:
											for attribute in ['title', 'originaltitle', 'plot', 'studio']:
												if attribute in season and season[attribute]: j[attribute] = season[attribute]
											break

			# Some attributes might be missing. Use the show/season attributes.
			# Eg: Most episodes, if not all, do not have a studio.
			parentPlot = show.get('plot')
			parentNetwork = show.get('network')
			parentStudio = show.get('studio')
			parentLanguage = show.get('language')
			parentCountry = show.get('country')
			parentGenre = show.get('genre')
			parentMpaa = show.get('mpaa')
			parentStatus = show.get('status')
			parentDuration = show.get('duration')
			parentCast = show.get('cast')
			parentDirector = show.get('director')
			parentWriter = show.get('writer')
			parentCreator = show.get('creator')
			parentPremiere = show.get('premiered') or show.get('aired')
			parentTime = show.get('time')
			parentZone = (show.get('airs') or {}).get('zone')

			# Sometimes TVDb list "probably" incorrect networks for seasons.
			# Eg: One Piece. TVDb lists BBC, NBC, CBS, Adult Swim as networks, but Fuji TV only for three of the seasons. Trakt has Fuji TV for all seasons.
			# If Trakt/TMDb list a single network for all seasons, but TVDb has multiple networks, prefer Trakt. Otherwise prefer TVDb.
			# Also switch if TVDb returns Syndication (licensed to multiple networks).
			# Eg: Star Trek (1966).
			# Update: About 1/3 of all popular shows have at least one season that TVDb has the completely wrong network listed for seasons.
			# Eg: Black Mirror S06: Teletoon
			# Eg: Better Call Saul S05: Das Erste
			# Since TVDb does not list the network under seasons on their website, it is assumed that these values are probably not maintained anymore and can have a lot of incorrect values.
			# For seasons, always list TVDb last if it only contains a single network, which is cacluated per-season.
			networksSwitch = False
			networksTvdb = {}
			networksOther = {}
			for i in data['seasons']:
				network = networks.get(i.get('season'))
				if network:
					for j in network[1]:
						for k in j:
							try: networksTvdb[k] += 1
							except: networksTvdb[k] = 1
					for j in network[0]:
						for k in j:
							try: networksOther[k] += 1
							except: networksOther[k] = 1
			countTvdb = len(networksTvdb.keys())
			countOther = len(networksOther.keys())
			countAverage = len(data['seasons']) / 2
			if countOther == 1 and countTvdb > 2:
				networksSwitch = True
			elif countOther == 1 and countTvdb >= 1:
				from lib.meta.company import MetaCompany
				if any(i in MetaCompany.helperSyndication() for i in networksTvdb.keys()): networksSwitch = True

			imagesMissing = None
			lastSeason = None
			for i in data['seasons']:
				number = i['season']
				if lastSeason is None or number > lastSeason: lastSeason = number

			lastImdb = None
			dateImdb = {}
			try:
				dataImdb = datas.get('imdb')
				if dataImdb:
					for i in dataImdb if Tools.isArray(dataImdb) else [dataImdb]:
						if i.get('provider') == 'imdb':
							values = i.get('data')
							if values:
								lastImdb = max(j.get('season') or 0 for j in values)
								try:
									for j in values:
										date = j.get('tvshowyear') or j.get('year')
										if not date:
											date = j.get('premiered') or j.get('aired')
											if date: date = int(date.split('-')[0])
										if date: dateImdb[j.get('season')] = date
								except: Logger.error()
							break
			except: Logger.error()
			if not lastImdb: lastImdb = -1

			# Do a first run over the images in order to get the theme of the first image selected after sorting.
			# "imagesThemes" is then used below to pick the actual images.
			imagesThemes = MetaImage.themes(media = MetaImage.MediaSeason, images = images, sort = providersImage)

			for i in range(len(data['seasons'])):
				season = data['seasons'][i]
				numberSeason = season['season']

				# Use the numbers from the pack, since the mapping between providers might have changed them.
				# Create default numbering, in case something is not available in the pack.
				if not 'number' in season: season['number'] = {}
				number = season['number']

				if not MetaPack.NumberStandard in number: number[MetaPack.NumberStandard] = numberSeason
				if not MetaPack.NumberSequential in number: number[MetaPack.NumberSequential] = 1
				if not MetaPack.NumberAbsolute in number: number[MetaPack.NumberAbsolute] = 1

				# Add missing IMDb numbers which are not available from the pack.
				if (numberSeason in dateImdb or numberSeason > 0 and lastImdb == 1) and lastImdb > 0:
					if not MetaPack.ProviderImdb in number: number[MetaPack.ProviderImdb] = {}

					# Special season, marked as "Unknown" season for some shows.
					# Eg: One Piece
					if numberSeason == 0: number[MetaPack.ProviderImdb][MetaPack.NumberStandard] = 0

					# Only has a single absolute season, typically devided by year.
					# Eg: One Piece
					elif lastImdb == 1: number[MetaPack.ProviderImdb][MetaPack.NumberStandard] = 1

					# Allow some leeway in case a new/future season is only on one provider.
					elif abs(lastSeason - lastImdb) <= 1: number[MetaPack.ProviderImdb][MetaPack.NumberStandard] = number.get(MetaPack.NumberStandard)

					number[MetaPack.ProviderImdb][MetaPack.NumberAbsolute] = number.get(MetaPack.NumberAbsolute)
					number[MetaPack.ProviderImdb][MetaPack.NumberSequential] = number.get(MetaPack.NumberSequential)
					number[MetaPack.ProviderImdb][MetaPack.NumberDate] = dateImdb.get(number[MetaPack.ProviderImdb][MetaPack.NumberStandard])

				value = self.mTools.mergeGenre(genres.get(numberSeason), parent = parentGenre)
				if not value and parentGenre: value = Tools.copy(parentGenre)
				if value: season['genre'] = value

				value = self.mTools.mergeLanguage(languages.get(numberSeason))
				if not value and parentLanguage: value = Tools.copy(parentLanguage)
				if value: season['language'] = value

				value = self.mTools.mergeCountry(countries.get(numberSeason))
				if not value and parentCountry: value = Tools.copy(parentCountry)
				if value: season['country'] = value

				# More info at _metadataShowUpdate().
				value = None
				network = networks.get(numberSeason)
				switch = networksSwitch
				if not switch:
					try:
						# Eg: Better Call Saul S05.
						# Eg: Black Mirror S06.
						# Only do this if the network does not appear frequently.
						# Eg: Vikings
						# Eg: Friends
						# Eg: Brooklyn Nine-Nine
						# Eg: Avatar Last Airbender
						if len(network[1][0]) == 1:
							countTvdb = networksTvdb.get(network[1][0][0], 0)
							countOther = networksOther.get(network[0][0][0], 0)
							if countTvdb <= countAverage: switch = True
							elif countOther >= countAverage and countTvdb < countOther: switch = True
					except: pass
				if network: value = self.mTools.mergeNetwork((network[1] + network[0]) if switch else (network[0] + network[1]), order = True, country = season.get('country')) # Different order in certain situations.
				if not value and parentNetwork: value = Tools.copy(parentNetwork)
				if value: season['network'] = value

				other = value # Must be right after networks.
				value = self.mTools.mergeStudio(studios.get(numberSeason), other = other, country = season.get('country'))
				if not value and parentStudio: value = Tools.copy(parentStudio)
				if value: season['studio'] = value

				# If there is no time for S00 and S01, use the show's time.
				missing = False
				if numberSeason <= 1 and parentTime and not times.get(numberSeason):
					missing = True
					if not numberSeason in times: times[numberSeason] = []
					times[numberSeason].append(parentTime)
				value = self.mTools.mergeTime(times.get(numberSeason), providers = timed.get(numberSeason), metadata = season)
				if value:
					season['time'] = value

					premiere = None
					accurate = True
					# Some shows are only available on IMDb, but not other providers (eg: tt31566242, tt30346074).
					# These seasons often do not have a release date.
					# Add the date from the interpolated show date.
					if not season.get('premiered'): premiere = parentPremiere if missing else None

					# Recalculate the date to accomodate timezones.
					# Late night shows from the US that air late at night have a GMT time early in the morning of the next day on Trakt.
					# This mostly matters for episodes, not that much for shows and seasons.
					# Eg: The Tonight Show Starring Jimmy Fallon S02E44 (Trakt: 2015-03-21T03:30:00Z, actual date in the timezone of release: 2015-03-20 23:30)
					if not premiere: premiere = value.get(MetaTools.TimePremiere)
					if Tools.isInteger(premiere):
						# If Trakt does not have a premiere date yet (eg: future unreleased season), do not replace the date that was calculated with the show's timezone.
						# TVDb only has the date, but does not have the time.
						# Hence, converting the TVDb timestamp to a date using the show's timezone (which comes from Trakt) can result in an incorrect date (off by 1 day).
						# Eg: 2025-01-02 00:00:00 (GMT's timezone) might be converted to 2025-01-01 22:00:00 (show's timezone).
						if not parentZone or not ((timed.get(numberSeason) or {}).get(MetaTools.ProviderTrakt) or {}).get(MetaTools.TimePremiere): accurate = False
						premiere = Time.format(premiere, format = Time.FormatDate, zone = parentZone)

					# Only update if there is no date, or there is a date and a timezone.
					if premiere and (accurate or not season.get('premiered')): season['premiered'] = season['aired'] = premiere

				value = self.mTools.mergeDuration(durations.get(numberSeason), short = self.mTools.niche(niche = self.mTools.mergeNiche(niches.get(numberSeason)), media = media, metadata = season, show = show, pack = pack))
				if value: season['duration'] = value

				value = self.mTools.mergeCertificate(mpaas.get(numberSeason), media = media)
				if not value and parentMpaa: value = Tools.copy(parentMpaa)
				if value: season['mpaa'] = value

				value = self.mTools.mergeCast(casts.get(numberSeason), show = parentCast)
				if value: season['cast'] = value

				value = self.mTools.mergeCrew(directors.get(numberSeason))
				if not value and parentDirector: value = Tools.copy(parentDirector)
				if value: season['director'] = value

				value = self.mTools.mergeCrew(writers.get(numberSeason))
				if not value and parentWriter: value = Tools.copy(parentWriter)
				if value: season['writer'] = value

				value = self.mTools.mergeCrew(creators.get(numberSeason))
				if not value and parentCreator: value = Tools.copy(parentCreator)
				if value: season['creator'] = value

				season['media'] = media

				niche = self.mTools.mergeNiche(niches.get(numberSeason))
				niche = self.mTools.niche(niche = niche, metadata = season, show = show, pack = pack)
				if niche: season['niche'] = niche

				if numberSeason in votings:
					voting = votings[numberSeason]

					# Add the IMDb rating/votes from the bulk datasets.
					# This should never happen, since the latests rating/votes are already retrieve from HTML if MetaTools.DetailExtended.
					try:
						if self._bulkImdbEnabled():
							try: votingImdb = voting['rating']['imdb']
							except: votingImdb = None
							if votingImdb is None and imdb:
								try: seasonImdb = number[MetaPack.ProviderImdb][MetaPack.NumberStandard]
								except: seasonImdb = None
								if seasonImdb is None: seasonImdb = numberSeason

								# Do not using the IMDb rating if IMDb has a single abolsute season, while Trakt/TMDb/TVDb have multiple seasons.
								# Otherwise, because of the very high vote count on IMDb, all seasons will end up with the same rating, from IMDb's S01.
								# Eg: One Piece.
								if not(seasonImdb == 1 and numberSeason > 1):
									votingImdb = self._bulkImdbLookup(imdb = imdb, season = seasonImdb)
									if votingImdb:
										voting['rating']['imdb'] = votingImdb.get('rating')
										voting['votes']['imdb'] = votingImdb.get('votes')
					except: Logger.error()

					season['voting'] = voting

				# The season duration returned by providers is typically the duration of the first episode.
				# This can be off quite a lot from the average episode duration.
				# This then displays a large deviation for shows with a double-first-episode, or shows like eg Downton Abbey with a slightly longer first episode in each season.
				duration = pack.durationMean(season = numberSeason)
				if not duration: duration = season.get('duration')
				if not duration: duration = parentDuration # Eg: The Office UK S03 (IMDb)
				if duration: season['duration'] = Math.roundClosest(duration, base = 60) # Round to closest minute.

				# Update: Always use the tvshowtitle from the show metadata and replace it in the episode metadata.
				# The episode metadata might be outdated and contains an old/alias title for tvshowtitle.
				# Plus the episode metadata only gets a title from TVDb/IMDb, but not from Trakt/TMDb.
				# The tvshowtitle in the show metadata is therefore more likley to be correct/up-to-date.
				# Eg: The tvshowtitle for the show is (correctly) "Pluribus", while the tvshowtitle for the episode (on TVDb) is "PLUR1BUS", which is an alias.
				# This attribute is important, since it is used as the title during scarping.
				#if not season.get('tvshowtitle') and parentTitle: season['tvshowtitle'] = parentTitle
				if parentTitle: season['tvshowtitle'] = parentTitle

				# Only some providers return a year for seasons/episodes, like TVDb and IMDb.
				# TVDb seems to typically have the show year, but IMDb can have the actual season/episode year and not the show year.
				# If we use the season/episode metadata object to do a title+year lookup or do a scrape, the year might not be the show's year and cause incorrect results.
				# Always explicitly store the show year.
				season['tvshowyear'] = parentYear or season.get('year')
				try: premiere = season['time'][MetaTools.TimePremiere]
				except: premiere = None
				if premiere: season['year'] = Time.year(premiere) # Add the actual season year.

				# Unaired seasons often do not have a plot.
				if not season.get('plot') and parentPlot: season['plot'] = parentPlot

				data['seasons'][i] = {k : v for k, v in season.items() if not v is None}
				season = data['seasons'][i]

				# Always replace the IDs with new values.
				# Otherwise if there is an incorrect IMDb ID on Trakt/TMDb, it gets written to MetaCache.
				# At a later point the ID is corrected on Trakt/TMDb.
				# If the data is now refreshed, the old ID from MetaCache is used instead of the newly retrieved IDs.
				# Hence, always replace these.
				# Prefer the ID from the show over the one from the season/episode. Since sometimes IDs (eg IMDb ID) is incorrect and later gets fixed. Show metadata is more likely to get the fixed IDs, while episode metadata might still have the old ID.
				ids1 = show.get('id') or {}
				ids2 = season.get('id') or {}
				value = ids1.get('imdb') or ids2.get('imdb')
				if value: imdb = value
				value = ids1.get('tmdb') or ids2.get('tmdb')
				if value: tmdb = value
				value = ids1.get('tvdb') or ids2.get('tvdb')
				if value: tvdb = value
				value = ids1.get('trakt') or ids2.get('trakt')
				if value: trakt = value
				value = ids1.get('slug') or ids2.get('slug')
				if value: slug = value
				value = ids1.get('tvmaze') or ids2.get('tvmaze')
				if value: tvmaze = value
				value = ids1.get('tvrage') or ids2.get('tvrage')
				if value: tvrage = value

				# This is for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
				# At some later point the entire addon should be updated to have the new ID structure.
				if not 'id' in season: season['id'] = {}
				if imdb: season['id']['imdb'] = season['imdb'] = imdb
				if tmdb: season['id']['tmdb'] = season['tmdb'] = tmdb
				if tvdb: season['id']['tvdb'] = season['tvdb'] = tvdb
				if trakt: season['id']['trakt'] = season['trakt'] = trakt
				if slug: season['id']['slug'] = season['slug'] = slug
				if tvmaze: season['id']['tvmaze'] = season['tvmaze'] = tvmaze
				if tvrage: season['id']['tvrage'] = season['tvrage'] = tvrage

				# Trakt sometimes returns new/unaired seasons that are not on TVDb.
				# This unique Trakt season does not have a show title, which will cause the season menu to be classified as "mixed" as the show title is added to the season label.
				if not 'tvshowtitle' in season and title: season['tvshowtitle'] = title

				if numberSeason in images and images[numberSeason]: MetaImage.update(media = MetaImage.MediaSeason, images = images[numberSeason], data = season, sort = providersImage, themes = imagesThemes)
				else: imagesMissing = numberSeason

				# Do this before here already.
				# Otherwise a bunch of regular expressions are called every time the menu is loaded.
				self.mTools.cleanDescription(metadata = season)

				# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
				# More info under meta -> tools.py -> cleanVoting().
				self.mTools.cleanVoting(metadata = season, round = True) # Round to reduce storage space of average ratings with many decimal places.

			# Sort so that the list is in the order of the season numbers.
			data['seasons'].sort(key = lambda i : i['season'])

			# Determine the season type.
			# Do this after the seasons were sorted, since we need the previous/next/last season.
			try:
				seasonLastStandard = None
				seasonLastOfficial = None
				try: seasonLastStandard = data['seasons'][-1].get('season')
				except: pass
				if pack:
					seasonLastStandard = pack.numberLastStandardSeason()
					seasonLastOfficial = pack.numberLastOfficialSeason()
				for i in range(len(data['seasons'])):
					try:
						season = data['seasons'][i]
						number = season.get('season')
						statusSeason = season.get('status')

						type = None
						status = None
						if pack:
							entry = pack.season(season = number, number = MetaPack.NumberStandard)
							if entry:
								type = pack.type(item = entry)
								status = pack.status(item = entry)
								status = [status] if status else [] # Add the pack status, since it is sometimes more accurate (eg Vikings S0).

						try: typePrevious = (data['seasons'][i - 1].get('type') if number > 1 else None) or self.mTools.mergeType(types[number - 1], season = number)
						except: typePrevious = None
						try: typeNext = self.mTools.mergeType(types[number + 1], season = number)
						except: typeNext = None
						try: typeLast = self.mTools.mergeType(types[number][-1], season = number)
						except: typeLast = None
						value = self.mTools.mergeType(types.get(number), season = number, seasonLastStandard = seasonLastStandard, seasonLastOfficial = seasonLastOfficial, type = type, typePrevious = typePrevious, typeNext = typeNext, typeLast = typeLast, statusShow = parentStatus, statusSeason = statusSeason)
						if value: season['type'] = value

						try: premiered = season['time'][MetaTools.TimePremiere]
						except: premiered = None
						value = self.mTools.mergeStatus((statuses.get(number) or []) + (status or []), media = media, time = premiered, season = number, type = season.get('type'), status = parentStatus)
						if value: season['status'] = value
					except: Logger.error()
			except: Logger.error()

			# Set the show details.
			try: season = data['seasons'][1] # Season 1
			except:
				try: season = data['seasons'][0] # Specials
				except: season = None
			data['media'] = media # Add this so that MetaCache knows the media without having to access the inner "seasons" list.
			data['id'] = {}
			if imdb: data['id']['imdb'] = data['imdb'] = imdb
			if tmdb: data['id']['tmdb'] = data['tmdb'] = tmdb
			if tvdb: data['id']['tvdb'] = data['tvdb'] = tvdb
			if trakt: data['id']['trakt'] = data['trakt'] = trakt
			if slug: data['id']['slug'] = data['slug'] = slug
			if tvmaze: data['id']['tvmaze'] = data['tvmaze'] = tvmaze
			if tvrage: data['id']['tvrage'] = data['tvrage'] = tvrage

			title = parentTitle
			if not title and season: title = season.get('tvshowtitle')
			if title: data['tvshowtitle'] = data['title'] = title

			year = parentYear
			if not year and season: year = season.get('tvshowyear') or season.get('year')
			if year: data['tvshowyear'] = data['year'] = year

			# Add the show status for MetaCache.
			# Use the status of the pack, in case it is newer than the status from the show metadata.
			status = parentStatus
			if not status in (MetaTools.StatusEnded, MetaTools.StatusCanceled):
				statusPack = pack.status()
				if statusPack in (MetaTools.StatusEnded, MetaTools.StatusCanceled): status = statusPack
			data['status'] = status

			# Add show niche.
			# Currently not used, but could be used to help identify niches, such as mini-series.
			niched = show.get('niche')
			if not niched:
				# Not that accurate, since it contains niches from individual seasons that might not always apply to the entire show (eg: "finale" season).
				try: niched.extend(self.mTools.mergeNiche(niches.values()))
				except: pass
			niche = self.mTools.niche(niche = niched, metadata = show, show = show, pack = pack)
			data['niche'] = niche

			# Sometimes the images are not available, especially for new/future releases.
			# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
			if not imagesMissing is None:
				partDone = False
				try: partNew['tvdb']['complete'] = False
				except: pass
				try: partNew['fanart']['complete'] = False
				except: pass
				if developer: Logger.log('SEASON IMAGES INCOMPLETE: %s' % self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item, season = imagesMissing))

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self._busyFinish(media = media, item = item)

	def _metadataSeasonId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, quick = None):
		result = self.mTools.idShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataSeasonTrakt(self, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# Do not use the cached summarized data. Only if it comes from IMDb.
			try: origin = bool(item['temp']['trakt'])
			except: origin = False

			if detail == MetaTools.DetailEssential and item and origin: # Comes from a Trakt list with basic metadata.
				if MetaCache.Attribute in item:
					result = {}
				else:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				result = self._metadataTemporize(item = item, result = result, provider = 'trakt')
			else: # Comes from another list, or forcefully retrieve detailed metadata.
				if trakt or imdb or tmdb or tvdb or title:
					# Trakt has an API limit of 1000 requests per 5 minutes.
					# Retrieving all the additional metadata will very quickly consume the limit if a few pages are loaded.
					# Only retrieve the extended metadata if enough requests are still avilable for the past 5 minutes.
					usage = self.providerUsageTrakt(authenticated = False)

					person = False
					if self.mModeGenerative: person = True
					elif detail == MetaTools.DetailExtended and usage < 0.5: person = True

					translation = None
					if detail == MetaTools.DetailEssential: translation = False # Use the translations from TVDb.

					# We already retrieve the cast (with thumbnails), translations and studios, from TMDb.
					# Retrieving all of them here again will add little new metadata and only prolong the retrieval.
					# translation = None: only retrieve for non-English.
					return MetaTrakt.instance().metadataSeason(trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, summary = True, translation = translation, person = person, language = language, extended = True, detail = True, cache = cache, concurrency = bool(threaded))
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def _metadataSeasonTvdb(self, tvdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTvdb.instance().metadataSeason(imdb = imdb, tvdb = tvdb, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : True, 'data' : None}

	def _metadataSeasonTmdb(self, tmdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataSeason(tmdb = tmdb, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataSeasonImdb(self, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# A single IMDb season page is +- 190-250KB compressed.
			# There is no way to efficiently retrieve all/many seasons/episodes from IMDb, only one season at a time with up to 50 episodes per season.
			# Use this function conservatively, since it can make multiple requests, at retrieving too many IMDb pages in a short time can result in IMDb blocking requests.
			# Only retrieve few seasons if the item does not come from MetaCache, meaning it is newley loaded, and might be part of batch requests for Trakt Progress sync.
			usage = self.providerUsageImdb()

			new = True
			if item and MetaCache.valid(item): new = False

			season = []

			# Add the season numbers from the bulk data if available.
			# This typically contains all the seasons and is more accurate and than using the season numbers from other providers below.
			# This also avoids the incremental retrieval of seasons below (max(season) + 1), and also avoids trying to retrieve seasons that do not exist on IMDb.
			bulk = self._bulkImdbLookup(imdb = imdb, data = True)
			try:
				if bulk:
					bulk = bulk.get('seasons')
					if bulk:
						season.extend(bulk.keys())
						if season: new = False # Retrieve more seasons the first time.
			except: Logger.error()

			# Bulk data not available, or S01 is not in the bulk data yet.
			if not season or not 1 in season:
				if item and item.get('seasons'):
					for i in item.get('seasons'):
						number = i.get('season')
						if not number is None: season.append(number)

					# Add one additional season number to the end.
					# This is a useful tool if there are inconsistencies with season numbers on IMDb.
					# Eg: Money Heist: 3 seasons (Trakt/TMDB/TVDb) vs 5 seasons (IMDb - the midseasons were split into separate seasons).
					# On the 1st non-new refresh, only 3 seasons will be retrieved from IMDb.
					# On the 2nd non-new refresh, 4 seasons are retrieved.
					# On the 3rd non-new refresh, 5 seasons are retrieved.
					# On the 4th non-new refresh, 6 seasons are retrieved, but only 5 are returned. It will stay at this level.
					# Hence, for these inconsistent shows, systematically retrieve more seasons on every refresh.
					# Eg: Family Guy and South Park - IMDb has mutiple future seasons for years in advance.
					if season: season.append(max(season) + 1)
				else:
					season = [i for i in range(10)]

			# Remove duplicates and sort, in case bulk season numbers were used.
			season = Tools.listUnique(season)
			season = Tools.listSort(season)

			# Move the special season to the back, since it typically does not exist on IMDb, and we want to retrieve it last.
			try:
				season.remove(0)
				season.append(0)
			except: pass

			if self.mModeGenerative:
				season = season[:50]
			elif new:
				if usage < 0.25: season = season[:4]
				elif usage < 0.50: season = season[:3]
				elif usage < 0.75: season = season[:2]
				elif usage < 0.90: season = season[:1]
				else: season = []
			else:
				if usage < 0.25: pass
				elif usage < 0.50: season = season[:20]
				elif usage < 0.75: season = season[:10]
				elif usage < 0.90: season = season[:5]
				else: season = []

			if season: result = MetaImdb.instance().metadataSeason(id = imdb, season = season, language = language, cache = cache, threaded = threaded)
		except: Logger.error()
		return {'provider' : 'imdb', 'complete' : complete, 'data' : result}

	def _metadataSeasonFanart(self, tvdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			if tvdb:
				images = MetaFanart.instance().metadataShow(tvdb = tvdb, season = True, cache = cache)
				if images is False: complete = False
				elif images:
					result = []
					for season, data in images.items():
						result.append({'season' : season, MetaImage.Attribute : data})
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result or None}

	def _metadataSeasonAggregate(self, items, refresh = None, threaded = None):
		# Do not store duplicate or non-season data in the MetaCache database, otherwise too much unnecessary storage space will be used.
		# Check _metadataEpisodeAggregate() for more info.
		try:
			if items:
				values = items if Tools.isArray(items) else [items]
				if values and Tools.isArray(values[0]): values = Tools.listFlatten(values) # A list for multiple shows, each containing a list of seasons.

				shows = []
				for item in values:
					try: shows.append({'imdb' : item.get('imdb'), 'tmdb' : item.get('tmdb'), 'tvdb' : item.get('tvdb'), 'trakt' : item.get('trakt')})
					except: Logger.error()
				shows = Tools.listUnique(shows)
				shows = self.metadataShow(items = shows, pack = False, refresh = refresh, threaded = threaded) if shows else None

				if shows:
					for item in values:
						try:
							imdb = item.get('imdb')
							tmdb = item.get('tmdb')
							tvdb = item.get('tvdb')
							trakt = item.get('trakt')
							for show in shows:
								if (imdb and show.get('imdb') == imdb) or (tmdb and show.get('tmdb') == tmdb) or (tvdb and show.get('tvdb') == tvdb) or (trakt and show.get('trakt') == trakt):
									# Add show images.
									if MetaImage.Attribute in show: MetaImage.update(media = MetaImage.MediaShow, images = Tools.copy(show[MetaImage.Attribute]), data = item, category = MetaImage.MediaShow)

									# Add show status used for label details in smart menus.
									# Add the tagline for Progress menus.
									item['serie'] = {
										'show' : {
											'status' : show.get('status'),
											'tagline' : show.get('tagline'),
										}
									}

									break
						except: Logger.error()
		except: Logger.error()
		return items

	##############################################################################
	# METADATA - EPISODE
	##############################################################################

	# NB: For efficiency, call this function with "pack=False" if the pack data is not needed. More info at metadata().
	# This function can be called in different ways, by either providing the individual parameters or using "items":
	#	1. Pass in a season: retrieve all episodes of that season.
	#		a. season = True: retrieve all episodes of all seasons of the show, including specials.
	#		b. season = False: retrieve all episodes of all seasons of the show, excluding specials.
	#	2. Pass in a season and episode: retrieve a specific episode based on the number.
	#	3. Pass in a season, episode, and limit: retrieve multiple consecutive episodes, starting from the given number. A negative limit means retrieve up to the end of the season.
	#	4. Pass in a season, episode, and next: retrieve the next "unwatched" episode in the series, based on the parameters passed in and the Trakt playback history. Used for the Progress menu.
	def metadataEpisode(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, number = None, items = None, pack = None, filter = None, clean = True, quick = None, refresh = None, cache = False, threaded = None, limit = None, next = None, discrepancy = None, special = SpecialExclude, aggregate = True, hierarchical = False, hint = None):
		try:
			media = Media.Episode

			packData = None
			packInstance = None
			packLookup = None

			pickSingle = False
			pickSingles = False
			pickMultiple = False
			pickSequential = number == MetaPack.NumberSequential or number == MetaPack.NumberAbsolute

			base = items
			numbering = None

			refreshInternal = self._metadataRefresh(refresh = refresh)

			smart = False
			if next == MetaManager.Smart:
				next = True
				smart = True

			if items or (trakt or imdb or tmdb or tvdb) or title:
				if pickSequential and not items:
					numbering = episode
					if episode is True:
						season = False # All seasons, excluding specials.
						episode = None
					else:
						season = 1

				# Do a lookup in the pack data to get the real season/episode numbers.
				# Eg: looking up a sequential number to get the season/episode number for a later season.
				# Do not do for "next", since we do the lookup later after the number was incremented.
				if (pickSequential and not next) or (not items and not episode is None):
					lookup = items
					if not lookup and Tools.isInteger(season):
						lookup = {'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year, 'season' : season, 'episode' : episode} # Add the title/year for a possible lookup if Trakt does not have the IMDb ID yet.
					if lookup:
						packLookup = self._metadataPackLookup(items = lookup, number = number, refresh = refreshInternal, threaded = threaded, quick = quick)
						if not items and (not numbering or Tools.isInteger(season)):
							season = lookup['season']
							episode = lookup['episode']
				elif items and Tools.isArray(items):
					# Progress menu's final metadata retrieval.
					# The progress/history might still have Trakt numbers, since they are too costly to convert in Playback if the user has a huge history.
					# Only lookup the numbers once a small subset of the items are loaded in the Progress menu page.
					# Eg: One Piece S02E63 (Trakt number).
					lookup = [i for i in items if Tools.get(i, MetaManager.Smart, 'external')] # 'external' if it comes from Trakt without numbers converted yet. Is set to None in metadataSmart() if already looked-up, so it does not have to be done here again.

					# Important to pass on "quick" here, when called from metadataSmart().
					# We do not want to generate a new pack if we are in quick mode.
					if lookup: packLookup = self._metadataPackLookup(items = lookup, number = MetaPack.ProviderTrakt, refresh = refreshInternal, threaded = threaded, quick = quick)

				if items:
					if Tools.isArray(items):
						if 'episode' in items[0]: pickSingles = True
					else:
						pickSingle = True
						season = items.get('season')
						episode = items.get('episode')
						items = [items]

				elif not season is None and not episode is None and limit:
					items = []
					pickMultiple = True
					if not numbering and special is MetaManager.SpecialSettings: special = self.mTools.settingsShowInterleave()

					# Reduce the number of seasons to retrieve if they do not exist in the first place or if they are not included in the menu.
					packData = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, refresh = refreshInternal, threaded = threaded)
					if packData: packInstance = MetaPack.instance(pack = packData)

					ranged = self._metadataEpisodeRange(pack = packInstance, season = season, episode = episode, limit = limit, number = number)
					if ranged:
						 # Add the title/year for a possible lookup if Trakt does not have the IMDb ID yet.
						if special and not ranged.get('season').get('start') == 0: items.append({'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year, 'season' : 0})
						items.extend([{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year, 'season' : i} for i in range(ranged.get('season').get('start'), ranged.get('season').get('end') + 1)])

				elif season is True or season is False:
					# Retrieve all episodes of all seasons for the show.
					# Used by library.py.
					items = []
					pickMultiple = True

					packData = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, refresh = refreshInternal, threaded = threaded)
					if packData:
						packInstance = MetaPack.instance(pack = packData)
						total = packInstance.countSeasonTotal()
						if total:
							for i in range(total):
								if i == 0 and season is False: continue
								items.append({'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year, 'season' : i}) # Add the title/year for a possible lookup if Trakt does not have the IMDb ID yet.

				else:
					pickSingle = True
					if filter is None: filter = True

					if trakt or imdb or tmdb or tvdb: items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year}] # Add the title/year for a possible lookup if Trakt does not have the IMDb ID yet.
					elif title: items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

					if items:
						items[0]['season'] = season
						if not episode is None: items[0]['episode'] = episode

						# This is used at the end of the function to remove sequential/absolute episodes from S01.
						# Update: Do not do this only for S01. We can also use this for the hint passed to _jobUpdate().
						# This takes about 150ms.
						# Update: The only reason why this takes so long is the call to MetaCache.settingsId() and Pool.settingMetadata() that is calculated here for the first time.
						# But this will be calculated eventually by some other call anyways, so this should not drastically increase time.
						if season == 1 or hint is True:
							packData = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, refresh = refreshInternal, threaded = threaded)
							if packData: packInstance = MetaPack.instance(pack = packData)

				# UPDATE 1
				#	When there is a mistake calling this function with seasonLast or episodeLast being None, it screws up the metadata saved to the database.
				#	Eg: When calling _metadataEpisodeNext(..., season = None, episode = None), eg from binge(), typically the last season of the show this function was called on, contains all episodes of the show (similar to the Series/flattened menus).
				#	If seasonLast/episodeLast was set but is None, filter out those items.
				#	Not sure if there is any place where this function is called that actually wants None for seasonLast/episodeLast?
				# UPDATE 2
				#	Season can be None if called from MetaManager._episode().
				#	This is caused by a bug when the Series menu is opened, but loaded as an Episodes submenu instead of a Series submenu.
				#	Eg: change MetaTools._command() and replace "if not Tools.isString(submenu): submenu = MetaTools.SubmenuSerie" with "if not Tools.isString(submenu): submenu = MetaTools.SubmenuEpisode"
				#	Then open the Series menu on GoT. A bunch of metadata requests are made, which are all incorrect. And finally the incorrectly retrieved metadata of S08 is then written to metadata.db -> episodes.
				#	This should not happen under normal circumstances. But leave here in case this happens for other reasons.
				items = [item for item in items if not(item.get('season') is None and item.get('episode') is None)]

				# NB: Only execute this if-statement if we are not in quick mode.
				# Not sure if this is correct, or if there are some calls that actually require this part during quick?
				# Without checking quick here, if the Trakt progress list contains 100+ items, the Arrivals menu loads very slowly, since all items' metadata is retrieved here.
				# This also causes Kodi to crash often, once the threads run out and no new ones can be created.
				# UPDATE: Only do this if quick is not False, not if quick is True/integer. Otherwise, below where we retrieve the full metadata, the foreground/background threads fail in _metadataEpisodeUpdate(), since there is no incremented season number in the items yet.
				if next and not quick is False and items:
					itemsIncrement = None

					# This uses already incremented numbers from metadataSmart()
					# This allows faster Progress menu loading, by not having to do expensive increments every time the menu is laoded.
					# Only do the increment here, for items that do not have the next number set.
					# This can easily save 500-700ms for a Progress menu with 20 items.
					if smart:
						itemsIncrement = []
						itemsSingle = len(items) == 1
						current = Time.timestamp()
						for item in items:
							smarted = item.get(MetaManager.Smart)
							# Only use this if the smart increment is not older than 3 months.
							# Otherwise if the smart increment was calculated with an old pack, newly released seasons/episodes might still have the old no-next-episode.
							# Do not make this too short, otherwise an item than was not updated in metadataSmart() for a while will hold up the process and make the menu slower.
							if smarted and (current - (smarted.get('time') or 0)) < 7776000:
								smarted = smarted.get('next')
								if smarted:
									item['season'] = smarted.get('season')
									item['episode'] = smarted.get('episode')
									if itemsSingle:
										number = smarted.get('number')
										if number: pickSequential = number == MetaPack.NumberSequential or number == MetaPack.NumberAbsolute
								elif not smarted is False:
									itemsIncrement.append(item)
					else: # metadataEpisodeNext()
						itemsIncrement = items

					if itemsIncrement:
						lock = Lock()
						locks = {}
						semaphore = Semaphore(self.mTools.concurrency(media = media, hierarchical = hierarchical))

						if len(itemsIncrement) == 1:
							semaphore.acquire()
							item = itemsIncrement[0]
							numberNew = self._metadataEpisodeIncrement(item = item, number = number, lock = lock, locks = locks, semaphore = semaphore, cache = cache, refresh = refreshInternal, threaded = threaded, discrepancy = discrepancy)
							if not number and numberNew:
								number = numberNew
								pickSequential = number == MetaPack.NumberSequential or number == MetaPack.NumberAbsolute
						else:
							threadsNext = []
							for item in itemsIncrement:
								semaphore.acquire()
								threadsNext.append(Pool.thread(target = self._metadataEpisodeIncrement, kwargs = {'item' : item, 'number' : number, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'cache' : cache, 'refresh' : refreshInternal, 'threaded' : threaded, 'discrepancy' : discrepancy}, start = True))
							[thread.join() for thread in threadsNext]

						# Check invalid: No more episodes available.
						# Check episode: _metadataEpisodeIncrement() can return without adding the 'invalid' attribute. Filter out all items without a valid episode number.
						# Update: Do not remove shows without a next episode (aka finished shows).
						# Otherwise some niche Progress menus are relativley empty. We simply move them to the end of the list during sorting.
						if smart:
							temp = []
							for item in items:
								invalid = False
								if item.get('invalid'): invalid = True
								if item.get('episode') is None: invalid = True
								else: temp.append(item)
								if invalid: self._metadataSmartUpdate(item = item, key = 'next', value = False)
							items = temp
						else: # metadataEpisodeNext()
							items = [i for i in items if not i.get('invalid') and not i.get('episode') is None]

						# Do the lookup here, after the numbers were incremented.
						packLookup = self._metadataPackLookup(items = items, refresh = refreshInternal, threaded = threaded, quick = quick)
						if pickSingle and items:
							season = items[0].get('season')
							episode = items[0].get('episode')

				if items:
					if packInstance or (hint and not hint is True): hint = {'season' : items[0].get('season'), 'pack' : packInstance or hint} # Episodes fom a single show.
					elif len(items) > 1: hint = {'count' : len(items)} # Episodes fom multiple shows.
					else: hint = None

					items = self._metadataCache(media = media, items = items, function = self._metadataEpisodeUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded, hierarchical = hierarchical, hint = hint)

					if items:
						items = self._metadataFilter(media = media, items = items, filter = filter)
						items = self._metadataAggregate(media = media, items = items) # Must be before picking, since it uses temp and the internal "episodes" list.

						if items:
							picks = None
							if pickSingles:
								picks = []
								for item in items:
									if 'episodes' in item:
										for episode in item['episodes']:
											if episode['season'] == item['season'] and episode['episode'] == item['episode']:
												if not 'time' in episode: episode['time'] = {}
												for attribute in MetaTools.TimesTrakt: # Use the times for the last watched episode to add to the incremented episode for sorting of progress menus.
													try: episode['time'][attribute] = item['time'][attribute]
													except: pass
												picks.append(episode)
												break
							elif pickSingle:
								picks = []
								for item in items: picks.extend(item['episodes'])
								if not episode is None:
									temp = None
									for i in picks:
										if i['episode'] == episode:
											temp = i
											break
									picks = temp
								elif season:
									# For unofficial episodes caused by Trakt season-absolute-episode-numbering.
									# Eg: One Piece S02 episode menu should end at S02E22 and not continue with Trakt absolute numbers S22E62+.
									# Eg: One Piece S18 episode menu should end at S18E55 and not continue with Trakt absolute numbers S18E749+.
									# Not sure if this could remove episodes from other shows that might need to stay in the episode menu. If so, change the types that are checked below.
									# Also check this with combined episodes.
									# Eg: Star Wars: Young Jedi Adventures S01E26-E49, check that all E4x episodes are there.
									if packInstance:
										temp = []
										previous = None
										for i in picks:
											try:
												# Only if the gap between two consecutive episodes is greater than 2.
												if (previous and (i.get('episode') - previous) > 2):
													type = packInstance.type(season = i.get('season'), episode = i.get('episode')) or {}
													if type.get(MetaPack.NumberUnofficial) and not MetaPack.NumberStandard in type and not MetaPack.NumberSpecial in type: break
												previous = i.get('episode')
											except: Logger.error()
											temp.append(i)
										picks = temp

							elif pickMultiple:
								picks = []

								# Remove sequential/absolute episodes from the Series menu.
								# Some providers might have the episodes in an absolute season, while others have the episodes listed under multiple seasons.
								# Otherwise the same episode is listed twice, once as absolute number and once as season number.
								#	Eg: Dragon Ball Super.
								# Also do for Absolute menu, since seasons can have different episode counts between Trakt and TVDb.
								#	Eg: One Piece (3rd page - eg TVDb 3x16)
								if number == MetaPack.NumberSerie or number == MetaPack.NumberSequential:
									numberAll = {}
									for item in items:
										for i in item['episodes']:
											numberAll[(i.get('season'), i.get('episode'))] = True

									types = [MetaPack.NumberOfficial, MetaPack.NumberSpecial]
									if number == MetaPack.NumberSequential: types.append(MetaPack.NumberSequential)
									for item in items:
										for i in item['episodes']:
											type = packInstance.type(season = i.get('season'), episode = i.get('episode')) or {}

											# If type is None, it is an IMDb special (eg: Downton Abbey S02E09).
											# Allow unofficial specials (eg: One Piece S00E02 on TVDb, but not on Trakt).
											if (not type or any(type.get(j) for j in types)) and (not type.get(MetaPack.NumberUnofficial) or type.get(MetaPack.NumberSpecial)):
												# Sometimes TVDb has more episodes in a season than Trakt, which causes the TVDb number to clash with the sequential number.
												# Filter out these "unofficial" episodes, which might sometimes be labeled as "official", since they are the Trakt absolute numbers pointing to an episode in S02+.
												# Eg: Star Wars: Young Jedi Adventures
												if type.get(MetaPack.NumberOfficial) and i.get('season') == 1:
													numberStandard = tuple(packInstance.numberStandard(season = i.get('season'), episode = i.get('episode')))
													numberSequential = tuple(packInstance.numberSequential(season = i.get('season'), episode = i.get('episode')))
													if not numberStandard == numberSequential and numberSequential in numberAll: continue
												picks.append(i)
								else:
									for item in items: picks.extend(item['episodes'])
							else:
								picks = [item['episodes'] for item in items]

							items = picks

							# Must be called before filterNumber() below.
							# Do not do this for Series menus. If not doing this for Series menus causes some other issues, this can be removed again.
							# We do not do this for Series menus, since there might be clashes between sequential numbers and extra TVDb numbers.
							#	Eg: Star Wars: Young Jedi Adventures
							# 		The 2nd page of Series has an episode offset of S01E26.
							#		S01E26 can be a sequential number or the TVDb standard number for uncombined episodes.
							#		This makes the 2nd page have episodes: S01E26, S02E02, S02E03, ...
							#		Do not convert the numbers, so it stays at: S02E01, S02E02, S02E03, ...
							if not number == MetaPack.NumberSerie: self._metadataPackNumber(items = items, lookup = packLookup, season = season, episode = episode, numbering = numbering, number = number)

							if pickMultiple:
								# Filter here already, since the previous season might still be included in items.
								# This makes the detecting the first episode from the season in _metadataEpisodeSpecial() impossible.
								# Remove season-based episodes from the absolute menu (eg: check the last sequential menu page of Dragon Ball Super).
								if pickSequential:
									items = self.mTools.filterNumber(items = items, season = 1, episode = numbering, single = Media.Season)

									# For shows that have both sequential/absolute episodes and seasoned episodes (from different providers), the same absolute number might appear twice.
									# Once for the actual absolute episode, and once for the seasoned episode which number has been converted to absolute during _metadataPackNumber().
									# This makes the absolute episodes from S02+ appear after the last episode in the Absolute menu, creating an infinite cycle.
									# Eg: Dragon Ball Super (the last page of the Absolute menu).
									previous = 0
									for i in range(len(items)):
										numberEpisode = items[i].get('episode')
										if not numberEpisode == 0: # Allow IMDb specials.
											if numberEpisode < previous:
												items = items[:i] # Ignore everything after the largest absolute number.
												break
											else:
												previous = numberEpisode
								else:
									# This is important for Progress submenus where Trakt and TVDb have a very different season odering.
									# Eg: One Piece.
									try:
										numberSequential = None
										if packInstance:
											# Do not just lookup the sequential number of the last episode on the previous page.
											# The last episode on the previous page might be an unofficial episode from TVDb (unofficial) that maps to a later season on Trakt (official).
											# Eg: LEGO Masters S06E01+ (Trakt) which are S05 (TVDb).
											# This causes S06E01-S06E04 to get removed from the Series submenu on page 6, since those episodes are S05 on TVDb, with the same sequential numbers as S06E01+.
											# We can also not just use: packInstance.lastEpisodeOfficial(season = season), since that will only work for Series submenus starting at SxxE01, and not the Progress submenus that can have an offset at an arbitrary episode.
											# Hence, use the last number from the previous page, iterating in reverse until we find the first official episode.

											#numberSequential = packInstance.lookupSequential(season = season, episode = episode)
											numberEpisode = episode
											while numberEpisode >= 1:
												item = packInstance.episode(season = season, episode = numberEpisode)
												if item:
													if packInstance.typeUnofficial(item = item):
														numberEpisode -= 1
													else:
														numberSequential = packInstance.numberSequential(item = item)
														break
												else: numberEpisode -= 1
											if not numberSequential: numberSequential = packInstance.lookupSequential(season = season, episode = episode)

										if numberSequential: numberSequential = numberSequential[MetaPack.PartEpisode]
										else: numberSequential = 0

										sequentialFound = {}
										def _sequentialValid(item):
											# Always allow specials. They get filtered out later on in _metadataEpisodeSpecial().
											if item.get('season') == 0 or item.get('episode') == 0: return True

											# The if-statement has 2 parts:
											# 1. (sequentialNumber >= numberSequential)
											#		Eg: One Piece: start the Progress submenu at S01E20, go to the next pages until we hit S02E01 as last item.
											#			Go to the next page and S02E17-S02E22 from TVDb are there.
											#			After S02E22, the episodes continue from S03E15 because of the aired date sorting in _metadataEpisodeSpecial() removed S03E01-S03E14.
											# 2. (not sequentialNumber in sequentialFound)
											#	Important to filter by duplicate sequential numbers here.
											#		Eg: One Piece S01E20.
											#	Progress menu starting at S01E20, going to the next page of the progress submenu will list both S01 and S02 episodes.
											#		Eg: One Piece S01E26 and S02E18 are both the same episode (S01E26 from Trakt and S02E18 from TVDb).
											#	Remove these "duplicate" episodes based on their sequential number.

											try: sequentialNumber = item['number'][MetaPack.NumberSequential][MetaPack.PartEpisode]
											except: sequentialNumber = 0
											try: traktNumber = item['number'][MetaPack.ProviderTrakt][MetaPack.NumberStandard][MetaPack.PartSeason]
											except: traktNumber = None
											try: tvdbNumber = item['number'][MetaPack.ProviderTvdb][MetaPack.NumberStandard][MetaPack.PartSeason]
											except: tvdbNumber = None
											try: imdbNumber = item['number'][MetaPack.ProviderImdb][MetaPack.NumberStandard][MetaPack.PartSeason]
											except: imdbNumber = None

											allow = (sequentialNumber >= numberSequential) and (not sequentialNumber in sequentialFound)
											if allow:
												# Ignore unofficial TVDb episodes.
												# Eg: My Name Is Earl S03E19+.
												# Also do not allow unofficial episodes, except specials (eg IMDb specials).
												# Eg: LEGO Masters S05E05+ (unofficial on TVDb).
												type = item.get('type')
												if type and MetaPack.NumberUnofficial in type and not MetaPack.NumberSpecial in type: allow = False

											if allow:
												sequentialFound[sequentialNumber] = True
												return True
											else:
												# Allow IMDb specials.
												# Eg: Downton Abbey S02E09.
												if imdbNumber and not traktNumber and not tvdbNumber: return True
											return False

										items = [i for i in items if _sequentialValid(i)]
									except: Logger.error()

									items = self.mTools.filterNumber(items = items, season = season, episode = episode)

								if special: items = self._metadataEpisodeSpecial(items = items, special = special, season = season, episode = episode, number = number, pack = packInstance)

							# Still add IMDb specials to the sequential menu, which do not have an actual sequential number (S01E00).
							# Eg: Downton Abbey S02E09.
							# Eg: Star Trek (1966) S01E00.
							# Change the numbers AFTER filterNumber() above.
							if pickSequential and items:
								for item in items if Tools.isArray(items) else [items]:
									if not item.get('episode') and not packInstance.numberEpisode(item = item, number = number):
										numberSeason = packInstance.numberStandardSeason(item = item)
										numberEpisode = packInstance.numberStandardEpisode(item = item)
										if not numberSeason is None and not numberEpisode is None:
											item['sequential'] = True # Use by MetaTools.label().
											item['season'] = numberSeason
											item['episode'] = numberEpisode

							# Do not add "refresh" here, otherwise the pack will be refreshed every time a season is refreshed.
							# Only add "refreshInternal" which is either False or None.
							items = self._metadataPackAggregate(items = items, data = packData, pack = pack, refresh = refreshInternal, quick = quick, cache = cache, threaded = threaded)

							# For Progress menus, the episode aggregation can take very long (1.0-1.5 secs).
							# This data is not really needed for any of the menu's functionality. Or is it?
							# Still do season aggregation, since we want the show poster for the menu.
							if aggregate:
								# Update (2025-04): Although the images are not absolutely necessary.
								# However, we might still want to use the season images when changing the settings for Images -> Combined Images, for anthology series (eg: White Lotus).
								# Calling _metadataEpisodeAggregate() takes anywhere from 40-250ms, but on average around 100-150ms.
								# This should not be a huge problem, since the first page of the Progress menu is cached and this will be done in the background.
								# And when the user occasionally goes to the next page, waiting an additional 150ms is not the end.
								# NB: If this is ever changed back, make sure to update the default values for the Combined Images setting.

								#if next: items = self._metadataSeasonAggregate(items = items, refresh = refreshInternal, threaded = threaded)
								#else: items = self._metadataEpisodeAggregate(items = items, refresh = refreshInternal, threaded = threaded)
								items = self._metadataEpisodeAggregate(items = items, refresh = refreshInternal, threaded = threaded)

							# Add the smart data back, needed for sorting later on.
							# This is also important for _metadataSmartLoad() for episode Progress menus.
							# Since all episodes of a season are retrieved from the database in one go, the dictionaries returned by this function are not the same dictionaries passed into the function.
							# Hence, the items returned by this function will not have the original attributes from the p[assed in items.]
							if smart: items = self._metadataSmartAggregate(media = media, items = items, base = base)

							items = self._metadataClean(media = media, items = items, clean = clean)

							return items
		except: Logger.error()
		return None

	#gaiafuture - make this function work with storyline specials. Ask the user during binge if they want to play the special or continue with the next official episode (eg: Downton Abbey S02E09/S00E02).
	def metadataEpisodeNext(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, number = None, pack = None, refresh = None, released = True):
		try:
			item = {'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year, 'season' : season, 'episode' : episode}

			# NB: discrepancy = False
			# If an entire season was previously watched. Then the 1st three episodes are watched a second time.
			# The next day, the user wants to watch E02 (and E03) again, since they fell asleep after E01.
			# Otherwise when checking discrepancies, Gaia will throw an error during playback, saying no more episodes available for binge watching.
			item = self.metadataEpisode(items = item, number = number, pack = pack, refresh = refresh, next = True, discrepancy = False)

			if item:
				premiered = None
				if not premiered and 'premiered' in item: premiered = item['premiered']
				if not premiered and 'aired' in item: premiered = item['aired']
				if not released or not premiered or Time.integer(premiered) <= Time.integer(Time.past(hours = 3, format = Time.FormatDate)): return item
		except: Logger.error()
		return None

	def _metadataEpisodeUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, refresh = None, part = True):
		try:
			if not self._checkInterval(mode = mode): return None

			media = Media.Episode

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')
			tvmaze = item.get('tvmaze')
			tvrage = item.get('tvrage')

			title = item.get('tvshowtitle') or item.get('title')
			year = item.get('tvshowyear') or item.get('year')
			numberSeason = originalSeason = item.get('season')

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = numberSeason)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data: item.update(Tools.copy(data)) # Copy in case the memory is used multiple times. Can be None if not found.
					return None

			# Previous incomplete metadata.
			partDone = True
			partStatus = None
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			try:
				partCache = item.get(MetaCache.Attribute)
				if partCache:
					partStatus = partCache.get(MetaCache.AttributeStatus)
					# Only do this for StatusPartial.
					# Other non-partial statuses that cause a refresh might also have the "part" dictionary.
					# However, in these cases the old "part" data should not be used, since as full refresh is needed and all requests should be redone.
					if part and partStatus == MetaCache.StatusPartial:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
			except: Logger.error()

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not tvdb or (not imdb and not trakt) or (self.mLevel >= 2 and not tmdb):
				ids = partOld.get('id')
				if not ids or not ids.get('complete'): ids = self._metadataEpisodeId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = ids
				if ids:
					if not ids.get('complete'): partDone = False
					ids = ids.get('data')
					if ids:
						ids = ids.get('id')
						if ids:
							if not imdb: imdb = ids.get('imdb')
							if not tmdb: tmdb = ids.get('tmdb')
							if not tvdb: tvdb = ids.get('tvdb')
							if not trakt: trakt = ids.get('trakt')
							if not slug: slug = ids.get('slug')
							if not tvmaze: tvmaze = ids.get('tvmaze')
							if not tvrage: tvrage = ids.get('tvrage')
			if not imdb and not tmdb and not tvdb and not trakt: return False

			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item, season = numberSeason)
			if developer: Logger.log('EPISODE METADATA RETRIEVAL [%s - %s]: %s' % (mode.upper() if mode else 'UNKNOWN', partStatus.upper() if partStatus else 'NEW', developer))

			show = self.metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, pack = False, refresh = refresh, threaded = threaded)
			if not show:
				Memory.set(id = id, value = {}, local = True, kodi = False)
				return False

			# Use the IDs of the show metadata.
			# This is useful if Trakt does not have the IMDb/TVDb ID yet.
			# The show metadata would have already done a MetaTrakt.lookup(), so it does not have to be done here again.
			# Always replace the values, in case the season metadata still contains old IDs or title.
			idsShow = show.get('id')
			if idsShow:
				trakt = idsShow.get('trakt') or trakt
				imdb = idsShow.get('imdb') or imdb
				tmdb = idsShow.get('tmdb') or tmdb
				tvdb = idsShow.get('tvdb') or tvdb
				slug = idsShow.get('slug') or slug
			parentTitle = title = show.get('tvshowtitle') or show.get('title') or title
			parentYear = year = show.get('tvshowyear') or show.get('year') or year

			season = self.metadataSeason(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = numberSeason, pack = False, refresh = refresh, threaded = threaded, hint = {'pack' : show.get('packed')})
			if not season:
				Memory.set(id = id, value = {}, local = True, kodi = False)
				return False

			if not parentTitle: parentTitle = title = season.get('tvshowtitle')
			if not parentYear: parentYear = year = season.get('tvshowyear')

			pack = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, refresh = refresh, threaded = threaded)
			if not self._checkInterval(mode = mode): return None
			pack = MetaPack.instance(pack = pack)

			cache = cache if cache else None

			# count = number of episodes.
			# DetailEssential: (count + 3) requests (eg: 10 episodes = 13 requests) [Trakt: 1 (summary), TVDb: 3-count (show summary, season summary, each episode), TMDb: 0, IMDb: 0]
			# DetailStandard: (count + 3) requests (eg: 10 episodes = 13 requests) [Trakt: 1 (summary), TVDb: 3-count (show summary, season summary, each episode), TMDb: 0, IMDb: 0]
			# DetailExtended: (2*count + 5) requests (eg: 10 episodes = 25 requests) [Trakt: 2-count (summary, people for each episode), TVDb: 3-count (show summary, season summary, each episode), TMDb: 1 (summary), IMDb: 1 (summary)]
			requests = []
			if self.mLevel >= 0:
				# Sometimes the season numbers are different to the standard season number.
				# Eg: Good times, bad times (TVDb uses the year as saeason number).
				numberSeasonTrakt = numberSeason
				numberSeasonTvdb = numberSeason
				numberSeasonTmdb = numberSeason
				numberSeasonImdb = numberSeason
				if pack:
					temp = pack.lookup(season = numberSeason, output = MetaPack.ProviderTrakt)
					if not temp is None: numberSeasonTrakt = temp
					temp = pack.lookup(season = numberSeason, output = MetaPack.ProviderTvdb)
					if not temp is None: numberSeasonTvdb = temp
					temp = pack.lookup(season = numberSeason, output = MetaPack.ProviderTmdb)
					if not temp is None: numberSeasonTmdb = temp
					temp = pack.lookup(season = numberSeason, output = MetaPack.ProviderImdb)
					if not temp is None: numberSeasonImdb = temp

				requests.append({'id' : 'trakt', 'function' : self._metadataEpisodeTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'title' : title, 'year' : year, 'season' : numberSeasonTrakt, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'tvdb', 'function' : self._metadataEpisodeTvdb, 'parameters' : {'tvdb' : tvdb, 'imdb' : imdb, 'season' : numberSeasonTvdb, 'item' : item, 'pack' : pack, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'imdb', 'function' : self._metadataEpisodeImdb, 'parameters' : {'imdb' : imdb, 'season' : numberSeasonImdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 2:
					requests.append({'id' : 'tmdb', 'function' : self._metadataEpisodeTmdb, 'parameters' : {'tmdb' : tmdb, 'season' : numberSeasonTmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				# Do not use the old parts if retrieving in the foreground.
				# Otherwise if the metadata is refreshed forcefully (eg: from the context menu), and the current MetaCache entry is incomplete, it will use the existing old parts and only refresh the previously failed/incomplete parts.
				# Instead, refresh all parts if the refresh is in the foreground.
				# MetaCache.StatusPartial refreshes happen by default in the background, which will still only re-retrieve the incomplete parts.
				if not mode == MetaCache.RefreshForeground:
					partRequests = []
					for i in requests:
						partData = partOld.get(i['id'])
						if partData and partData.get('complete'): partDatas[i['id']] = partData
						else: partRequests.append(i)
					requests = partRequests
					partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			if not self._checkInterval(mode = mode): return None
			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			if not self._checkInterval(mode = mode): return None
			datas.update(partDatas)

			data = {'episodes' : []}
			maps = {}
			unmaps = {}
			remaps = {}
			niches = {}
			genres = {}
			studios = {}
			networks = {}
			languages = {}
			countries = {}
			statuses = {}
			types = {}
			typesOriginal = {}
			typesProvider = {}
			times = {}
			timed = {}
			durations = {}
			mpaas = {}
			images = {}
			votings = {}
			casts = {}
			directors = {}
			writers = {}
			creators = {}
			titles = {'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}, 'metacritic' : {}}
			dates = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			# Create a specific order for the providers to update the metadata with.
			# MetaPack will determine the "best" order, typically based on which provider has more episodes.
			# Eg: GoT (TVDb vs Trakt) S00E56 and S00E57.
			# Eg: "Star Wars: Young Jedi Adventures" with combined/uncombined episodes. But in this case TVDb has more (uncombined) episdodes than Trakt in any case.
			providers = ['metacritic']
			support = pack.support(season = numberSeason)
			if support:
				# Always use TVDb above TMDb, even if TMDb has more episodes in the season.
				try: indexTmdb = support.index('tmdb')
				except: indexTmdb = -1
				try: indexTvdb = support.index('tvdb')
				except: indexTvdb = -1
				if indexTmdb >= 0 and indexTvdb >= 0 and indexTmdb < indexTvdb: support.insert(indexTvdb, support.pop(indexTmdb))
				providers.extend(reversed(support))
			if not 'imdb' in providers: providers.insert(providers.index('metacritic') + 1, 'imdb')
			if not 'tmdb' in providers: providers.insert(providers.index('imdb') + 1, 'tmdb')
			if not 'fanart' in providers: providers.insert(providers.index('tmdb') + 1, 'fanart')
			if not 'trakt' in providers: providers.append('trakt')
			if not 'tvdb' in providers: providers.append('tvdb')
			providersImage = ['tvdb', 'fanart', 'tmdb', 'trakt', 'imdb'] # Preferred providers must be placed first.

			# Add Fanart and map to TVDb, since it uses TVDb IDs and numbering.
			# Allow additional episodes from IMDb that are not on TVDb/TMDb/Trakt (eg: IMDb Downton Abbey S02E09, which is a special elsewhere).
			def _lookupImdb(numberSeason, numberEpisode, episode, episodes, pack):
				try:
					titleEpisode = episode.get('title')

					if not 'number' in episode: episode['number'] = {}
					episode['number']['imdb'] = {MetaPack.NumberStandard : [numberSeason, numberEpisode]}

					# Only do search() with expensive title matching if the episode count differs.
					# Otherwise assume the IMDb numbering is correct.
					# Also always do it for SxxE00, even if the counts match.
					# Eg: LEGO Master S03 - IMDb has S03E00, but not S03E13, so that there are 16 episodes for S03, just like on Trakt (used in the pack).
					if titleEpisode and pack:
						if numberEpisode == 0 or not pack.countEpisode(season = numberSeason) == len(episodes):
							# Only match current season and specials.
							# Allow for "lenient" matching if the strict matching did not return a result.
							# This allows for titles that do not have a perfect match. Eg: Downton Abbey S06E09 ("Christmas Special") vs S00E11 ("Christmas Day").
							# NB: Exclude the show title from matching, otherwise the titles might be too similar.
							# Eg: GoT S01E00 (IMDb): "Game of Thrones: Unaired Original Pilot" matches S00E207 (Trakt): "Game of Thrones: The Inner Circle".
							# These 2 match, because the prefix in the title is the same.
							# Only exclude the prefix, since the suffix might be required.
							# Eg: "Inside Game of Thrones" or "Making Game of Thrones".
							match = pack.search(title = titleEpisode, season = [numberSeason, 0], lenient = True, excludePrefix = title)
							if match:
								mapped = False
								actualSeason = pack.numberStandardSeason(item = match)
								actualEpisode = pack.numberStandardEpisode(item = match)

								if not(actualSeason == numberSeason and actualEpisode == actualEpisode):
									id = pack.id(season = actualSeason, episode = actualEpisode)
									if id:
										if not episode.get('id'): episode['id'] = {}
										if not episode['id'].get('episode'): episode['id']['episode'] = {}
										ids = episode['id']['episode']
										for k, v in id.items():
											if not ids.get(k): ids[k] = v

									if actualSeason == numberSeason:
										numberEpisode = actualEpisode
										mapped = True
									else:
										# Special elsewhere (eg: Downton Abbey S02E09).
										# Add the other numbers to the episode, so a notification can be shown during scraping that the episode might also be available under a different number.
										number = pack.number(season = actualSeason, episode = actualEpisode, number = False)
										if number:
											mapped = True
											episode['number'].update(number)
											episode['number'][MetaPack.NumberStandard] = [numberSeason, numberEpisode]

									if mapped:
										if not numberSeason in maps: maps[numberSeason] = {}
										if not numberEpisode in maps[numberSeason]: maps[numberSeason][numberEpisode] = []
										maps[numberSeason][numberEpisode].append('imdb')
				except: Logger.error()
				return numberSeason, numberEpisode
			providersLookup = {'trakt' : 'trakt', 'tvdb' : 'tvdb', 'tmdb' : 'tmdb', 'fanart' : 'tvdb', 'imdb' : ['imdb', _lookupImdb] if self._bulkImdbEnabled() else _lookupImdb}

			# A season that only exists on IMDb, but none of the other providers.
			# Episode number mappings should not be done in this case, otherwise the season is always empty.
			# Eg: Money Heist S04 + S05.
			imdbOnly = []
			for i in providers:
				if not i == 'fanart':
					values = datas.get(i)
					if values:
						episodes = values[0].get('data') if Tools.isArray(values) else values.get('data')
						if episodes: imdbOnly.append(i)
			imdbOnly = len(imdbOnly) == 1 and 'imdb' in imdbOnly

			imdbPrevious = None
			for i in providers:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								partDone = False
								if developer: Logger.log('EPISODE METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

							provider = value['provider']

							# Use "provider", not "i", since IMDb also has Metacritic data.
							# NB: Important to copy, since the dict is edited below.
							# Otherwise we edit the dict before it gets (possibly) written as partial data to MetaCache.
							# Eg: TVDb fails or has no data yet (new release). The TMDb images get deleted below, and the TMDb is later added as partial data to MetaCache. The next time the partial metadata is refreshed, the TMDb data is used, but now does not have images anymore, causing the poster to be missing in the menus.
							# This mostly happens with new releases. Either TMDb/TVDb/Trakt has not listed it yet, or Trakt has the wrong TMDb/TVDb ID.
							partNew[provider] = Tools.copy(value)

							episodes = value['data']
							if episodes:
								episodes = Tools.copy(episodes) # Copy, since we do title/plot/studio replacement below in another loop.
								for episode in episodes:
									numberSeason = numberSeason2 = episode['season']
									numberEpisode = numberEpisode2 = episode['episode']

									# Used for filling in missing episodes later on.
									titles[i][(numberSeason, numberEpisode)] = episode.get('title')

									# Add IMDb dates to use as the date number later on.
									if i == 'imdb':
										try: idImdb = episode['id']['episode'][i]
										except: idImdb = None
										if idImdb: dates[idImdb] = episode.get('premiered')

									# Lookup the real Gaia season/episode number using the provider's native number.
									# This ensures that the correct dicts are updated with each other if the numbers differ on some.
									# If there is no lookup for the current provider (eg: IMDb), continue by assuming their numbering is correct.
									lookup = providersLookup.get(i)
									mapped = False
									unmapped = False
									invalid = False

									if lookup and not imdbOnly:
										if Tools.isFunction(lookup):
											numberSeason, numberEpisode = lookup(numberSeason = numberSeason, numberEpisode = numberEpisode, episode = episode, episodes = episodes, pack = pack)
										else:
											lookupInput = lookup[0] if Tools.isArray(lookup) else lookup

											# Unknown alternate/unoffical episodes are now added to the provider lookup table in MetaPack.
											# Eg: Star Wars: Young Jedi Adventures S02E22 (TVDb).
											# This now causes the TVDb-specific episode to be returned, instead of the standard universal episode it was matched against.
											# If such a lookup is detected, keep "lookuped" as None in order not to include the episode in the results.
											# Old code:
											#	# For instance, if Trakt uses absolute episode numbering within standard seasons.
											#	# Eg: One Piece (Anime) - S22E1089 instead of S22E01.
											#	lookuped = pack.lookupStandard(season = numberSeason, episode = numberEpisode, input = lookupInput)
											lookuped = None
											lookupEpisode = pack.episode(season = numberSeason, episode = numberEpisode, number = lookupInput)
											if pack.typeUnofficial(item = lookupEpisode) and pack.type(item = lookupEpisode, type = Media.Alternate):
												support = len(pack.support(item = lookupEpisode, default = []))

												# Exclude unofficial episodes that were already added to IMDb, but not the other providers.
												# Eg: The Tonight Show Starring Jimmy Fallon S12E141+ on IMDb, but not on Trakt/TMDb/TVDb.
												if support == 1 and not pack.support(item = lookupEpisode) == [MetaPack.ProviderImdb]: lookupEpisode = None

												# Exclude unofficial episodes where the TVDb season does not match any of the other provider's season.
												# This can happen if the entire TVDb season maps to a different official season.
												# Eg: One Piece S11E15 (TVDb). S11 on TVDb maps to S08 on Trakt/TMDb.
												elif support > 1 and i == MetaPack.ProviderTvdb:
													numberAllow = False
													for p in [MetaPack.ProviderTrakt, MetaPack.ProviderTmdb, MetaPack.ProviderImdb]:
														try: numberProvider = lookupEpisode[MetaPack.ProviderTrakt][MetaPack.NumberStandard][MetaPack.PartSeason]
														except: numberProvider = None
														if not numberProvider is None and numberProvider == numberSeason:
															numberAllow = True
															break
													if not numberAllow: lookupEpisode = None
											if lookupEpisode:
												lookuped = pack.number(item = lookupEpisode)

												# Sometime Trakt has the incorrect TVDb and/or IMDb episode ID.
												# Remove the incorrect ID.
												# Eg: My Name is Earl S03E06 + S03E12.
												incorrect = pack.incorrect(item = lookupEpisode)
												if incorrect:
													for j in incorrect:
														try:
															idProvider = episode['id']['episode'][j]
															episode['id']['episode'][j] = None
														except: idProvider = None
														if developer and i == 'trakt': Logger.log('EPISODE %s ID INVALID [%s]: S%02dE%02d (%s) - ID: %s | Title: %s' % (j.upper(), i.upper(), numberSeason, numberEpisode, developer, idProvider, episode.get('title')))

											# Still lookup IMDb specials.
											# This sets the IDs and numbers of other providers to the episode.
											# The IDs/numbers might not be available from MetaPack, since IMDb's bulk dataset does not have titles that can be matched against Trakt/TMDb/TVDb S0.
											# Eg: Lego Masters S03E00 (make sure it shows all the numbers in the dialog before scraping).
											if Tools.isArray(lookup):
												numberSeason2, numberEpisode2 = lookup[1](numberSeason = numberSeason, numberEpisode = numberEpisode, episode = episode, episodes = episodes, pack = pack)

												if lookuped:
													# If a new absolute episode is on IMDb, which maps to a later season on Trakt.
													# Eg: One Piece S01E1145 (IMDb) -> S22E57 (Trakt).
													# Do not do if the season and episode number matches in "lookuped".
													# Eg: One Piece S02.
													if i == 'imdb' and not numberSeason2 is None and lookuped[0] > numberSeason2 and not lookuped[0] == originalSeason:
														invalid = True
														lookuped = None
												else:
													# Do not add the IMDb episode, if it does not fall within the numbers of the pack.
													# The pack might be a bit outdated, and there is a new episode on IMDb.
													# Eg: One Piece S01E1135 (IMDb)
													# Since this number cannot be mapped (since it is not yet in the pack), _lookupImdb will return it as S01E1135, which is then added incorrectly as an IMDb special to S01.
													# If the number is larger than the known IMDb number of the last episode in the season, ignore it and do not add as an episode.
													# Allow some deviation, if an episode is not in the pack.
													# Eg: Lost S01E25 (maybe the pack code is later updated to accomodate this episode).
													# Update: Allow more than 3 extra episodes.
													# Sometimes IMDb has many more future/unaired episodes than Trakt/TMDb/TVDb.
													# Eg: The Tonight Show Starring Jimmy Fallon S12E136-S12E163 on IMDb, but Trakt/TVDb only goes up until S12E135.
													# Check the previous IMDb and only reject if the gap between the current and the previous episode is too great.
													#numberLast = pack.numberLastStandardEpisode(season = numberSeason, provider = i)
													#if numberLast and numberEpisode2 > (numberLast + 2): invalid = True
													#else: lookuped = [numberSeason2, numberEpisode2]
													if imdbPrevious and abs(imdbPrevious - numberEpisode2) > 3: invalid = True
													else: lookuped = [numberSeason2, numberEpisode2]

											# If the episode maps to a special S00, keep the old standard season number.
											# Eg: Downton Abbey S02E09 (IMDb) -> S00E02.
											if lookuped and lookuped[0] == 0 and numberSeason > 0: lookuped = None

											# If a single Trakt absolute numbering maps to a TVDb multi-season numbering, stick to the Trakt absolute numbers.
											# Eg: Dragon Ball Super - should have 131 episodes in S01 (absolute).
											# UPDATE (2025-03-05): Is this still needed? Even without this code, Dragon Ball Super still seems to be correct.
											# Maybe something was fixed in MetaPack which makes this obsolete.
											# With this code, One Piece S22E01 (TVDb) maps to S22E04 (incorrect). Without the code it maps to S21E195 (correct) and will be ignore for S22.
											# We also do not want this for One Piece S19, where TVDb would map S19E01 -> S19E25 with this code.
											# UPDATE (2025-03-20): This is indeed still needed Dragon Ball Super S02+.
											# Otherwise S02+ has no episodes at all, because ALL TVDb unofficial episodes match to Trakt S01 and will therefore be ignored and not added to the results.
											# This causes numerous fails in Tester.metadataNext().
											# Doing this only for typeUnofficial() seems to solve the problem.
											# To verify this is working, the following mapping has to be used:
											#	One Piece S22E01 (TVDb) -> S21E195
											#	Dragon Ball Super S02E01 (TVDb) -> no mapping, should stay at S02E01.
											#if lookuped and not lookuped[0] is None and not lookuped[0] == numberSeason:
											#	lookuped = pack.lookup(season = numberSeason, episode = numberEpisode, input = MetaPack.NumberStandard, output = lookup)
											#	if lookuped and not lookuped[0] is None and not lookuped[0] == numberSeason: lookuped = None
											if lookuped and not lookuped[0] is None and not lookuped[0] == numberSeason:
												if pack.typeUnofficial(item = pack.episode(season = numberSeason, episode = numberEpisode, provider = MetaPack.NumberStandard)):
													lookuped = pack.lookup(season = numberSeason, episode = numberEpisode, input = MetaPack.NumberStandard, output = lookup[0] if Tools.isArray(lookup) else lookup)
													if lookuped and not lookuped[0] is None and not lookuped[0] == numberSeason: lookuped = None

											if lookuped and not lookuped[0] is None:
												mapped = not(numberSeason == lookuped[0] and numberEpisode == lookuped[1])
												if mapped:
													if not numberSeason in maps: maps[numberSeason] = {}
													if not numberEpisode in maps[numberSeason]: maps[numberSeason][numberEpisode] = []
													maps[numberSeason][numberEpisode].append(i)

												if lookuped[0] and numberSeason and not lookuped[0] == numberSeason:
													if not numberSeason in remaps: remaps[numberSeason] = {}
													if not numberEpisode in remaps[numberSeason]: remaps[numberSeason][numberEpisode] = []
													if not i in remaps[numberSeason][numberEpisode]: remaps[numberSeason][numberEpisode].append(i)

												if developer and mapped: Logger.log('EPISODE NUMBER MAPPING [%s]: S%02dE%02d -> S%02dE%02d (%s)' % (i.upper(), numberSeason, numberEpisode, lookuped[0], lookuped[1], developer))

												numberSeason = lookuped[0]
												numberEpisode = lookuped[1]

												# Change these numbers, otherwise they are added twice to the season menu, once for the standard number and once for the alternative/absolute number.
												# Eg One Piece (Anime) - S22E01 vs S22E1089.
												episode['season'] = lookuped[0]
												episode['episode'] = lookuped[1]
											else:
												if pack.episodeUnofficial(season = numberSeason, episode = numberEpisode, provider = lookup):
													if not numberSeason in unmaps: unmaps[numberSeason] = {}
													if not numberEpisode in unmaps[numberSeason]: unmaps[numberSeason][numberEpisode] = []
													unmaps[numberSeason][numberEpisode].append(i)
													unmapped = True

												# The pack might be outdated and not have newley aired episodes yet.
												# Do not reject these new episodes if they cannot be found in the pack.
												# Only reject them if they are specials, or if the number of episodes in the pack is greater than the number in the current provider season.
												# Eg: Vikings: A number of the TVDb specials.
												if invalid or numberSeason == 0 or pack.countEpisodeOfficial(season = numberSeason) > len(episodes):
													if developer: Logger.log('EPISODE NUMBER INVALID [%s]: S%02dE%02d (%s)' % (i.upper(), numberSeason, numberEpisode, developer))
													continue # Eg: GoT S00E56/S00E57 on TVDb that do not exist on Trakt/TMDb. Trakt/TMDb have different specials under that number, and do not have them under any other number.

									if i == 'imdb': imdbPrevious = numberEpisode

									if numberEpisode is None:
										if developer: Logger.log('EPISODE NUMBER UNKNOWN [%s]: S%02d (%s)' % (i.upper(), numberSeason, developer))
										continue # IMDb S0 ("Unknown") does not have episode numbers.

									# Check "unmapped" here, since we do not want to add the values if the episode number between Trakt and TVDb is far off.
									# Eg: Star Wars: Young Jedi Adventures S02E22.
									# This is only really important for not adding the "type" if unmapped.
									# Otherwise the type value of the Trakt episode is used for the TVDb episode (which is a totally different episode, but has the same number S02E22).
									if not unmapped:
										if MetaImage.Attribute in episode:
											if not numberSeason in images: images[numberSeason] = {}
											if not numberEpisode in images[numberSeason]: images[numberSeason][numberEpisode] = {}
											images[numberSeason][numberEpisode] = Tools.update(images[numberSeason][numberEpisode], episode[MetaImage.Attribute], none = False, lists = True, unique = False)
											del episode[MetaImage.Attribute]

										if 'title' in episode:
											if not numberSeason in titles: titles[numberSeason] = {}
											if not numberEpisode in titles[numberSeason]: titles[numberSeason][numberEpisode] = []
											titles[numberSeason][numberEpisode].append((i, episode['title'])) # Add the provider here, since we sort according to provider later on.
										if 'niche' in episode:
											if not numberSeason in niches: niches[numberSeason] = {}
											if not numberEpisode in niches[numberSeason]: niches[numberSeason][numberEpisode] = []
											niches[numberSeason][numberEpisode].append(episode['niche'])
										if 'genre' in episode:
											if not numberSeason in genres: genres[numberSeason] = {}
											if not numberEpisode in genres[numberSeason]: genres[numberSeason][numberEpisode] = []
											genres[numberSeason][numberEpisode].append(episode['genre'])
										if 'studio' in episode:
											if not numberSeason in studios: studios[numberSeason] = {}
											if not numberEpisode in studios[numberSeason]: studios[numberSeason][numberEpisode] = []
											studios[numberSeason][numberEpisode].append(episode['studio'])
										if 'network' in episode:
											if not numberSeason in networks: networks[numberSeason] = {}
											if not numberEpisode in networks[numberSeason]: networks[numberSeason][numberEpisode] = [[], []]
											networks[numberSeason][numberEpisode][1 if i == 'tvdb' else 0].append(episode['network'])
										if 'language' in episode:
											if not numberSeason in languages: languages[numberSeason] = {}
											if not numberEpisode in languages[numberSeason]: languages[numberSeason][numberEpisode] = []
											languages[numberSeason][numberEpisode].append(episode['language'])
										if 'country' in episode:
											if not numberSeason in countries: countries[numberSeason] = {}
											if not numberEpisode in countries[numberSeason]: countries[numberSeason][numberEpisode] = []
											countries[numberSeason][numberEpisode].append(episode['country'])
										if 'status' in episode:
											if not numberSeason in statuses: statuses[numberSeason] = {}
											if not numberEpisode in statuses[numberSeason]: statuses[numberSeason][numberEpisode] = []
											statuses[numberSeason][numberEpisode].append(episode['status'])
										if 'time' in episode:
											if not numberSeason in times: times[numberSeason] = {}
											if not numberEpisode in times[numberSeason]: times[numberSeason][numberEpisode] = []
											times[numberSeason][numberEpisode].append(episode['time'])
											if not numberSeason in timed: timed[numberSeason] = {}
											if not numberEpisode in timed[numberSeason]: timed[numberSeason][numberEpisode] = {}
											timed[numberSeason][numberEpisode][i] = episode['time']
										if 'duration' in episode:
											if not numberSeason in durations: durations[numberSeason] = {}
											if not numberEpisode in durations[numberSeason]: durations[numberSeason][numberEpisode] = []
											durations[numberSeason][numberEpisode].append(episode['duration'])
										if 'mpaa' in episode:
											if not numberSeason in mpaas: mpaas[numberSeason] = {}
											if not numberEpisode in mpaas[numberSeason]: mpaas[numberSeason][numberEpisode] = []
											mpaas[numberSeason][numberEpisode].append(episode['mpaa'])

										if 'type' in episode:
											if not numberSeason in types: types[numberSeason] = {}
											if not numberEpisode in types[numberSeason]: types[numberSeason][numberEpisode] = []
											types[numberSeason][numberEpisode].append(episode['type'])

											if not numberSeason2 in typesOriginal: typesOriginal[numberSeason2] = {}
											if not numberEpisode2 in typesOriginal[numberSeason2]: typesOriginal[numberSeason2][numberEpisode2] = []
											typesOriginal[numberSeason2][numberEpisode2].append(episode['type'])

											if not numberSeason in typesProvider: typesProvider[numberSeason] = {}
											if not numberEpisode in typesProvider[numberSeason]: typesProvider[numberSeason][numberEpisode] = {}
											typesProvider[numberSeason][numberEpisode][i] = episode['type']

										if episode.get('cast'):
											if not numberSeason in casts: casts[numberSeason] = {}
											if not numberEpisode in casts[numberSeason]: casts[numberSeason][numberEpisode] = []
											casts[numberSeason][numberEpisode].append(episode['cast'])
										if episode.get('director'):
											if not numberSeason in directors: directors[numberSeason] = {}
											if not numberEpisode in directors[numberSeason]: directors[numberSeason][numberEpisode] = []
											directors[numberSeason][numberEpisode].append(episode['director'])
										if episode.get('writer'):
											if not numberSeason in writers: writers[numberSeason] = {}
											if not numberEpisode in writers[numberSeason]: writers[numberSeason][numberEpisode] = []
											writers[numberSeason][numberEpisode].append(episode['writer'])
										if episode.get('creator'):
											if not numberSeason in creators: creators[numberSeason] = {}
											if not numberEpisode in creators[numberSeason]: creators[numberSeason][numberEpisode] = []
											creators[numberSeason][numberEpisode].append(episode['creator'])

										if not numberSeason in votings: votings[numberSeason] = {}
										if not numberEpisode in votings[numberSeason]: votings[numberSeason][numberEpisode] = Tools.copy(voting)
										if 'rating' in episode: votings[numberSeason][numberEpisode]['rating'][provider] = episode['rating']
										if 'votes' in episode: votings[numberSeason][numberEpisode]['votes'][provider] = episode['votes']
										if 'userrating' in episode: votings[numberSeason][numberEpisode]['user'][provider] = episode['userrating']

									# NB: Use the "update" dict below to replace the updated episode numbers, and only add the episode if "numberSeason == originalSeason".
									# Otherwise an episode that is originally from a different season (eg S0), will be used to update the dict (and numbers) and add it to the episode list.
									# Eg: The Office (India) - TVDb has the pilot as S00E01 while Trakt/TMDb has it as S01E01 and therefore also one more episode in the season.
									# Without the "update" replacement, the TVDb S00E01 will replace the numbering of the episode of S01E01 to now have S00E01 numbers, which we do not want. It will then also add an extra episode, so that the season has 14 instead of the correct 13.
									found = False
									for j in data['episodes']:
										if j['season'] == numberSeason and j['episode'] == numberEpisode:
											found = True
											update = None
											if not episode['season'] == numberSeason or not episode['episode'] == numberEpisode:
												update = {
													'season' : j['season'],
													'episode' : j['episode'],
													'number' : j['number'],
												}
											Tools.update(j, episode, none = False, lists = False, unique = False)
											if update: j.update(update)
											break
									if not found and numberSeason == originalSeason: data['episodes'].append(episode)

			# Special episodes that are on Trakt, but not on TVDb, might not have certain attributes.
			attributes = ['studio', 'genre', 'country', 'cast']
			values = {i : {} for i in attributes}
			for episode in data['episodes']:
				for attribute in attributes:
					if attribute in episode and episode[attribute]:
						if episode['season'] in values[attribute]:
							if len(str(values[attribute][episode['season']])) > len(str(episode[attribute])): continue
						values[attribute][episode['season']] = episode[attribute]

			# Use the average duration of episodes in the season if an episode does not have a duration.
			# Eg: Downton Abbey S06E09 - special which is only on IMDb. TMDb/TVDb/Trakt list it under the specials season.
			parentDuration = season.get('duration')
			if not parentDuration:
				parentDuration = [i.get('duration') for i in data['episodes']]
				parentDuration = [i for i in parentDuration if i]
				if parentDuration: parentDuration = int(sum(parentDuration) / float(len(parentDuration)))
				else: parentDuration = None

			# Some attributes might be missing. Use the show/season attributes.
			# Eg: Most episodes, if not all, do not have a studio.
			parentZone = (show.get('airs') or {}).get('zone')
			parentNetwork = season.get('network') or show.get('network')
			parentStudio = season.get('studio') or show.get('studio')
			parentLanguage = season.get('language') or show.get('language')
			parentCountry = season.get('country') or show.get('country')
			parentGenre = season.get('genre') or show.get('genre')
			parentMpaa = season.get('mpaa') or show.get('mpaa')
			parentCastShow = show.get('cast')
			parentCastSeason = season.get('cast')
			parentDirector = season.get('director') or show.get('director')
			parentWriter = season.get('writer') or show.get('writer')
			parentCreator = season.get('creator') or show.get('creator')
			parentPremiere = season.get('premiered') or season.get('aired')
			parentTime = season.get('time')
			parentStatus = season.get('status')
			parentType = season.get('type')

			imagesMissing = None
			lastImdb = None
			dateImdb = {}
			try:
				dataImdb = datas.get('imdb')
				if dataImdb:
					for i in dataImdb if Tools.isArray(dataImdb) else [dataImdb]:
						if i.get('provider') == 'imdb':
							values = i.get('data')
							if values:
								lastImdb = max(j.get('episode') or 0 for j in values)
								try:
									for j in values:
										date = j.get('premiered') or j.get('aired')
										if date:
											numberSeason = j.get('season')
											if not numberSeason in dateImdb: dateImdb[numberSeason] = {}
											dateImdb[numberSeason][j.get('episode')] =[int(date.split('-')[0]), int(date.replace('-', ''))]
								except: Logger.error()
							break
			except: Logger.error()
			if not lastImdb: lastImdb = -1

			# Prefer IMDb titles last, since they are often in a non-English language. Eg: Money Heist: titles are in Spanish on IMDb.
			titleOrder = pack.support(season = originalSeason)
			if not titleOrder: titleOrder = providers # If the season is only on IMDb and not in the pack. Eg: Money Heist S04 + S05.
			for k1, v1 in titles.items():
				if Tools.isInteger(k1):
					for k2, v2 in v1.items():
						if v2:
							try: v2 = Tools.listSort(v2, key = lambda x : titleOrder.index(x[0]) if x[0] in titleOrder else 999)
							except: Logger.error()
							v1[k2] = [i[1] for i in v2]

			for i in range(len(data['episodes'])):
				episode = data['episodes'][i]
				numberSeason = episode.get('season')
				numberEpisode = episode.get('episode')

				# Use the numbers from the pack, since the mapping between providers might have changed them.
				# Create default numbering, in case something is not available in the pack.
				if not 'number' in episode: episode['number'] = {}
				number = episode['number']

				# Use the IDs from the pack, since the mapping between providers might have changed them.
				type = None
				incorrect = None
				if pack:
					# Do not retrieve using pack.number(), since it will use NumberUniversal for lookups, which might not always match with NumberStandard.
					# Eg: Star Wars: Young Jedi Adventures S01E26 (NumberUniversal sees this as absolute, mapping to S02E01, while NumberStandard will retrieve the TVDb uncombined episode S01E26).
					#numbers = pack.number(season = numberSeason, episode = numberEpisode, number = False)
					entryAlternate = None
					entry = pack.episode(season = numberSeason, episode = numberEpisode, number = MetaPack.NumberStandard)
					if not entry and imdbOnly:
						# For IMDb seasons that are not in the pack, because the season does not exist on Trakt/TMDb/TVDb.
						# Eg: Money Heist S04 + S05.
						try: idEpisode = episode['id']['episode'][MetaPack.ProviderImdb]
						except: idEpisode = None
						if idEpisode:
							entry = entryAlternate = pack.search(id = idEpisode, provider = MetaPack.ProviderImdb)
							entry = Tools.copy(entry)
							entry['number'][MetaPack.NumberStandard] = [numberSeason, numberEpisode]

					if entry:
						type = pack.type(item = entry)
						incorrect = pack.incorrect(item = entry)

					numbers = entry.get(MetaPack.ValueNumber) if entry else None
					if numbers:
						numberStandard = numbers.get(MetaPack.NumberStandard)

						# Only replace if the season matches the requested season.
						# Otherwise episodes that map top another season might be added.
						# Eg: Star Wars: Young Jedi Adventures S01E26-S01E50 - uncombined S01 from TVDb clash with the absolute numbers from Trakt that uses combined episodes.
						if not numberStandard is None and numberStandard[0] == originalSeason:
							episode['season'] = numberSeason = numberStandard[0]
							episode['episode'] = numberEpisode = numberStandard[1]
						try: del episode['absolute'] # Delete the absolute number, to force extracting it from the "number" dictionary.
						except: pass

						# Add the IMDb date number which is not available from MetaPack.
						try: numberImdb = numbers[MetaPack.ProviderImdb][MetaPack.NumberDate]
						except: numberImdb = None
						if not numberImdb or numberImdb[MetaPack.PartEpisode] is None:
							try: idImdb = episode['id']['episode'][MetaPack.ProviderImdb]
							except: idImdb = None
							if idImdb:
								date = dates.get(idImdb)
								if date: numbers[MetaPack.ProviderImdb][MetaPack.NumberDate] = [int(date.split('-')[0]), int(date.replace('-', ''))]

						# Important: lists = None
						# This only replaces the season-episode-number lists if they are None.
						# If they are not None, they are not replaced.
						# This is important for the numbers set by IMDb through _lookupImdb(), otherwise they are replaced here with None, since those numbers are not in the pack.
						# Eg: LEGO Masters S03E00 (make sure all numbers show in the dialog during scraping).
						Tools.update(episode['number'], numbers, none = False, lists = None, unique = False)

					idsEpisode = pack.id(season = numberSeason, episode = numberEpisode)
					if not 'id' in episode: episode['id'] = {}
					ids = pack.id(season = numberSeason)
					if ids:
						if not 'season' in episode['id']: episode['id']['season'] = {}
						Tools.update(episode['id']['season'], ids, none = False, lists = False, unique = False)
					ids = pack.id(season = numberSeason, episode = numberEpisode)
					if ids:
						if not 'episode' in episode['id']: i['id']['episode'] = {}
						Tools.update(episode['id']['episode'], ids, none = False, lists = False, unique = False)

					# Add reduced pack data for things like the episode type.
					# Use fallback for specials that are only on IMDb (eg: Downton abbey S02E09), to use some base values from the last known episode in the season.
					packed = pack.reduce(season = numberSeason, episode = numberEpisode, fallback = True)
					if not packed and imdbOnly and entryAlternate: packed = pack.reduce(season = entryAlternate['number'][MetaPack.NumberStandard][MetaPack.PartSeason], episode = entryAlternate['number'][MetaPack.NumberStandard][MetaPack.PartEpisode], fallback = True, alternate = True)
					episode['packed'] = packed

				# Only do this AFTER the pack numbers were added.
				if not MetaPack.NumberStandard in number: number[MetaPack.NumberStandard] = [numberSeason, numberEpisode]
				if not MetaPack.NumberSequential in number: number[MetaPack.NumberSequential] = [1, episode.get('sequential') or 0] # "or 0" for IMDb specials.
				if not MetaPack.NumberAbsolute in number: number[MetaPack.NumberAbsolute] = [1, episode.get('absolute') or 0]

				# Add missing IMDb numbers which are not available from the pack.
				# Only do this if IMDb was found, since IMDb might use absolute numbers and would not find anything on a season level.
				# Eg: One Piece S02.
				# Ignore episode numbers that do not match.
				# Eg: Star Wars: Young Jedi Adventures S01E26.
				# Do not assume the IMDb numbers are the same as the official numbers if Trakt has the incorrect TVDB/IMDb episode ID.
				# Rather remove the numbers that are likley wrong, instead of keeping possible wrong numbers that might point to the incorrect episode.
				# Eg: My Name is Earl S03E06 + S03E12.
				if (not incorrect or not MetaPack.ProviderImdb in incorrect) and numberSeason > 0 and numberEpisode <= lastImdb:
					try: numberImdb = number[MetaPack.ProviderImdb][MetaPack.NumberSequential][MetaPack.PartEpisode]
					except: numberImdb = None
					if numberImdb is None:
						if not MetaPack.ProviderImdb in number: number[MetaPack.ProviderImdb] = {}
						for j in [MetaPack.NumberStandard, MetaPack.NumberSequential, MetaPack.NumberAbsolute]: number[MetaPack.ProviderImdb][j] = Tools.copy(number.get(j))
						number[MetaPack.ProviderImdb][MetaPack.NumberDate] = (dateImdb.get(numberSeason) or {}).get(numberEpisode)

				# Special episodes that are on Trakt, but not on TVDb, might not have certain attributes.
				for attribute in attributes:
					if not attribute in episode or not episode[attribute]:
						try: episode[attribute] = values[attribute][numberSeason]
						except: pass

				# For future/unaired episodes.
				# Eg: a future season is already on TVDb and the episodes have proper titles. On Trakt/TMDb the new episodes are still incomplete with titles like "Episode 1", "Episode 2", etc.
				# Do not use the proxy title from Trakt, but the real title from TVDb.
				# IMDb also has titles like: "Episode dated 14 December 2020" (tt23626090).
				titlePick = None
				if not episode.get('title') or MetaPack.titleGeneric(title = episode.get('title')):
					tba = (episode.get('title') or '').lower() == 'tba' # Rather replace "TBA" (typically from TVDb) with "Episode N" (Trakt/TMDb/IMDb).
					value = titles.get(numberSeason, {}).get(numberEpisode)
					if value:
						for j in value:
							if j and (not MetaPack.titleGeneric(title = j) or (tba and not j.lower() == 'tba')):
								titlePick = j
								episode['title'] = j
								break
				# TMDb sometimes has future/unaired episodes with titles from IMDb, probably because they scrape IMDb.
				# Eg: Episode #12.132
				if episode.get('title'):
					episode['title'] = MetaImdb.cleanTitle(episode['title'])

					# Remove prefixes from pilots.
					# Eg: GoT S01E00 (IMDb): "Game of Thrones: Unaired Original Pilot"
					if numberSeason > 0 and numberEpisode == 0:
						titleLower = episode['title'].lower()
						if ('pilot' in titleLower or 'premiere' in titleLower or 'unaired' in titleLower) and title and titleLower.startswith(title.lower()):
							titleCleaned = Regex.remove(data = episode['title'], expression = r'^(%s\s*(?:[\:\-]\s*)?)' % title)
							if titleCleaned: episode['title'] = MetaImdb.cleanTitle(titleCleaned)

				# If the original title is a generic title (eg: Episode 3), replace it with an alias titles that is not the main title.
				# Eg: Money Heist S01 - there are generic titles, English titles, and some Spanish titles from IMDb. Use the English titles as "title" and the Spanish title as "originaltitle".
				if not episode.get('originaltitle') or MetaPack.titleGeneric(title = episode.get('originaltitle')):
					value = titles.get(numberSeason, {}).get(numberEpisode)
					if value:
						for j in value:
							if j and not j == titlePick and not MetaPack.titleGeneric(title = j):
								episode['originaltitle'] = j
								break

				value = self.mTools.mergeGenre(genres.get(numberSeason, {}).get(numberEpisode), parent = show.get('genre'))
				if not value and parentGenre: value = Tools.copy(parentGenre)
				if value: episode['genre'] = value

				value = self.mTools.mergeLanguage(languages.get(numberSeason, {}).get(numberEpisode))
				if not value and parentLanguage: value = Tools.copy(parentLanguage)
				if value: episode['language'] = value

				value = self.mTools.mergeCountry(countries.get(numberSeason, {}).get(numberEpisode))
				if not value and parentCountry: value = Tools.copy(parentCountry)
				if value: episode['country'] = value

				# More info at _metadataShowUpdate().
				value = None
				network = networks.get(numberSeason, {}).get(numberEpisode)

				# For specials, TVDb often has the wrong network.
				# Eg: One Piece has half the episodes marked as BBC One.
				# If only TVDb has a network, rather default to the season network.
				# Otherwise in Series/Progress menus, interleaved specials cause a different studio icon to pop up, which is noticeable when scrolling.
				if numberSeason == 0 and network and len(network[0]) == 0 and len(network[1]) == 1: network = None

				if network: value = self.mTools.mergeNetwork(network[0] + network[1], order = True, country = episode.get('country'))
				if not value and parentNetwork: value = Tools.copy(parentNetwork)
				if value: episode['network'] = value

				other = value # Must be right after networks.
				value = self.mTools.mergeStudio(studios.get(numberSeason, {}).get(numberEpisode), country = episode.get('country'), other = other)
				if not value and parentStudio: value = Tools.copy(parentStudio)
				if value: episode['studio'] = value

				# If there is no time for E00 and E01, use the season's time.
				missing = False
				if numberEpisode <= 1 and parentTime and not times.get(numberSeason, {}).get(numberEpisode):
					missing = True
					if not numberSeason in times: times[numberSeason] = {}
					if not numberEpisode in times[numberSeason]: times[numberSeason][numberEpisode] = []
					times[numberSeason][numberEpisode].append(parentTime)
				value = self.mTools.mergeTime(times.get(numberSeason, {}).get(numberEpisode), providers = timed.get(numberSeason, {}).get(numberEpisode), metadata = episode)
				if value:
					episode['time'] = value

					premiere = None
					accurate = True

					# Some shows are only available on IMDb, but not other providers (eg: tt31566242, tt30346074).
					# These seasons often do not have a release date.
					# Add the date from the interpolated show date.
					if not episode.get('premiered'): premiere = parentPremiere if missing else None

					# Recalculate the date to accomodate timezones.
					# Late night shows from the US that air late at night have a GMT time early in the morning of the next day on Trakt.
					# Eg: The Tonight Show Starring Jimmy Fallon S02E44 (Trakt: 2015-03-21T03:30:00Z, actual date in the timezone of release: 2015-03-20 23:30)
					if not premiere: premiere = value.get(MetaTools.TimePremiere)
					if Tools.isInteger(premiere):
						# If Trakt does not have a premiere date yet (eg: future unreleased season), do not replace the date that was calculated with the show's timezone.
						# TVDb only has the date, but does not have the time.
						# Hence, converting the TVDb timestamp to a date using the show's timezone (which comes from Trakt) can result in an incorrect date (off by 1 day).
						# Eg: 2025-01-02 00:00:00 (GMT's timezone) might be converted to 2025-01-01 22:00:00 (show's timezone).
						if not parentZone or not ((timed.get(numberSeason, {}).get(numberEpisode) or {}).get(MetaTools.ProviderTrakt) or {}).get(MetaTools.TimePremiere): accurate = False
						premiere = Time.format(premiere, format = Time.FormatDate, zone = parentZone)

					# Only update if there is no date, or there is a date and a timezone.
					if premiere and (accurate or not episode.get('premiered')): episode['premiered'] = episode['aired'] = premiere

				value = self.mTools.mergeDuration(durations.get(numberSeason, {}).get(numberEpisode))
				if value: episode['duration'] = value

				value = self.mTools.mergeCertificate(mpaas.get(numberSeason, {}).get(numberEpisode), media = media)
				if not value and parentMpaa: value = Tools.copy(parentMpaa)
				if value: episode['mpaa'] = value

				value = self.mTools.mergeCast(casts.get(numberSeason, {}).get(numberEpisode), season = parentCastSeason, show = parentCastShow)
				if value: episode['cast'] = value

				value = self.mTools.mergeCrew(directors.get(numberSeason, {}).get(numberEpisode))
				if not value and parentDirector: value = Tools.copy(parentDirector)
				if value: episode['director'] = value

				value = self.mTools.mergeCrew(writers.get(numberSeason, {}).get(numberEpisode))
				if not value and parentWriter: value = Tools.copy(parentWriter)
				if value: episode['writer'] = value

				value = self.mTools.mergeCrew(creators.get(numberSeason, {}).get(numberEpisode))
				if not value and parentCreator: value = Tools.copy(parentCreator)
				if value: episode['creator'] = value

				episode['media'] = media

				niche = self.mTools.mergeNiche(niches.get(numberSeason, {}).get(numberEpisode))
				niche = self.mTools.niche(niche = niche, metadata = episode, show = show, pack = pack)
				if niche: episode['niche'] = niche

				if numberSeason in votings and numberEpisode in votings[numberSeason]:
					voting = votings[numberSeason][numberEpisode]

					# Add the IMDb rating/votes from the bulk datasets.
					# This should only be necessary for episodes SxxE51+, since the HTML page shows up to first 50 episodes.
					try:
						if self._bulkImdbEnabled():
							try: votingImdb = voting['rating']['imdb']
							except: votingImdb = None
							if votingImdb is None and imdb:
								try: idImdb = episode['id']['episode']['imdb']
								except: idImdb = None
								if idImdb:
									votingImdb = self._bulkImdbLookup(imdb = imdb, imdbEpisode = idImdb)
								else:
									try: numberImdb = episode['number']['imdb'][MetaPack.NumberStandard]
									except: numberImdb = None
									if numberImdb and not numberImdb[-1] is None:
										votingImdb = self._bulkImdbLookup(imdb = imdb, season = numberImdb[MetaPack.PartSeason], episode = numberImdb[MetaPack.PartEpisode])
								if votingImdb:
									voting['rating']['imdb'] = votingImdb.get('rating')
									voting['votes']['imdb'] = votingImdb.get('votes')
					except: Logger.error()

					episode['voting'] = voting

				# Use the show/season average episode duration in there is no extact duration.
				if not episode.get('duration') and parentDuration: episode['duration'] = parentDuration

				# Newer unaired episodes from shows like "Coronation Street" do not always have a tvshowtitle, which causes sorting to fail.
				# Update: Always use the tvshowtitle from the show metadata and replace it in the episode metadata.
				# The episode metadata might be outdated and contains an old/alias title for tvshowtitle.
				# Plus the episode metadata only gets a title from TVDb/IMDb, but not from Trakt/TMDb.
				# The tvshowtitle in the show metadata is therefore more likley to be correct/up-to-date.
				# Eg: The tvshowtitle for the show is (correctly) "Pluribus", while the tvshowtitle for the episode (on TVDb) is "PLUR1BUS", which is an alias.
				# This attribute is important, since it is used as the title during scarping.
				#if not episode.get('tvshowtitle') and parentTitle: episode['tvshowtitle'] = parentTitle
				if parentTitle: episode['tvshowtitle'] = parentTitle

				# Only some providers return a year for seasons/episodes, like TVDb and IMDb.
				# TVDb seems to typically have the show year, but IMDb can have the actual season/episode year and not the show year.
				# If we use the season/episode metadata object to do a title+year lookup or do a scrape, the year might not be the show's year and cause incorrect results.
				# Always explicitly store the show year.
				episode['tvshowyear'] = parentYear or episode.get('year')
				try: premiere = episode['time'][MetaTools.TimePremiere]
				except: premiere = None
				if premiere: episode['year'] = Time.year(premiere) # Add the actual season year.

				data['episodes'][i] = {k : v for k, v in episode.items() if not v is None}
				episode = data['episodes'][i]

				# Always replace the IDs with new values.
				# Otherwise if there is an incorrect IMDb ID on Trakt/TMDb, it gets written to MetaCache.
				# At a later point the ID is corrected on Trakt/TMDb.
				# If the data is now refreshed, the old ID from MetaCache is used instead of the newly retrieved IDs.
				# Hence, always replace these.
				# Prefer the ID from the show over the one from the season/episode. Since sometimes IDs (eg IMDb ID) is incorrect and later gets fixed. Show metadata is more likely to get the fixed IDs, while episode metadata might still have the old ID.
				ids1 = show.get('id') or {}
				ids2 = season.get('id') or {}
				ids3 = episode.get('id') or {}
				value = ids1.get('imdb') or ids2.get('imdb') or ids3.get('imdb')
				if value: imdb = value
				value = ids1.get('tmdb') or ids2.get('tmdb') or ids3.get('tmdb')
				if value: tmdb = value
				value = ids1.get('tvdb') or ids2.get('tvdb') or ids3.get('tvdb')
				if value: tvdb = value
				value = ids1.get('trakt') or ids2.get('trakt') or ids3.get('trakt')
				if value: trakt = value
				value = ids1.get('slug') or ids2.get('slug') or ids3.get('slug')
				if value: slug = value
				value = ids1.get('tvmaze') or ids2.get('tvmaze') or ids3.get('tvmaze')
				if value: tvmaze = value
				value = ids1.get('tvrage') or ids2.get('tvrage') or ids3.get('tvrage')
				if value: tvrage = value

				# This is for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
				# At some later point the entire addon should be updated to have the new ID structure
				if not 'id' in episode: episode['id'] = {}
				if imdb: episode['id']['imdb'] = episode['imdb'] = imdb
				if tmdb: episode['id']['tmdb'] = episode['tmdb'] = tmdb
				if tvdb: episode['id']['tvdb'] = episode['tvdb'] = tvdb
				if trakt: episode['id']['trakt'] = episode['trakt'] = trakt
				if slug: episode['id']['slug'] = episode['slug'] = slug
				if tvmaze: episode['id']['tvmaze'] = episode['tvmaze'] = tvmaze
				if tvrage: episode['id']['tvrage'] = episode['tvrage'] = tvrage

				# Delete all remaining images which might have a dict instead of a URL for some images.
				# This can happen if all TVDb episodes match to a different season.
				# Hence the "episode" dict coming from TVDb might still have an image dict, but the if-statement for MetaImage.update() will not execute (and replace the image dict), since the episode number cannot be found.
				# The images are already deleted in the main for-loop above. But due to all the episode merging/updates, there might still be some image dicts left, which get delete here.
				# Eg: One Piece S11 which maps to TVDB S08.
				try: del episode[MetaImage.Attribute]
				except: pass

				if numberSeason in images and images[numberSeason] and numberEpisode in images[numberSeason] and images[numberSeason][numberEpisode]:
					MetaImage.update(media = MetaImage.MediaEpisode, images = images[numberSeason][numberEpisode], data = episode, sort = providersImage)
				elif not type or type.get(MetaPack.NumberOfficial): # Ignore unofficial episodes with missing images, although this would probably not happen that often.
					imagesMissing = (numberSeason, numberEpisode)

				# Do this before here already.
				# Otherwise a bunch of regular expressions are called every time the menu is loaded.
				self.mTools.cleanDescription(metadata = episode)

				# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
				# More info under meta -> tools.py -> cleanVoting().
				self.mTools.cleanVoting(metadata = episode, round = True) # Round to reduce storage space of average ratings with many decimal places.

			# Add all unofficial episodes that were mapped to an official number.
			# Otherwise when opening the season menu, only official episodes are shown.
			# Eg: Star Wars: Young Jedi Adventures: S01E25+
			# Otherwise only every 2nd unofficial episode for Young Jedi will show in the S01 menu, since Trakt has combined episodes and TVDB uncombined episodes.
			# Do this at the end, once all the metadata has been filled and aggregated.
			try:
				extra = []
				lookup = {(i.get('season'), i.get('episode')) : True for i in data['episodes']}
				exclude = {'trakt' : True, 'tmdb' : True}
				for episode in data['episodes']:
					numbers = episode.get('number')
					if numbers:
						for i in providers:
							number = numbers.get(i)
							if number:
								number = number.get(MetaPack.NumberStandard)
								numberId = tuple(number)
								if number and not number[MetaPack.PartSeason] is None and not number[MetaPack.PartEpisode] is None and number[MetaPack.PartSeason] == originalSeason and not numberId in lookup:
									numberSeason = number[MetaPack.PartSeason]
									numberEpisode = number[MetaPack.PartEpisode]

									# Only add if the episode has a "standard" type.
									# Eg: Exclude One Piece S02E62+ (Trakt/TMDb).
									# Still allow unofficial episodes from TVDb.
									# Eg: Include One Piece S17E65+ (TVDb).
									# Eg: Include Young Jedi Adventures: S01E25+ (TVDb).
									found = pack.episode(season = numberSeason, episode = numberEpisode, provider = i, number = MetaPack.NumberStandard)
									if found and (pack.typeStandard(item = found) or not i in exclude):
										entry = Tools.copy(episode)
										entry['season'] = numberSeason
										entry['episode'] = numberEpisode
										lookup[numberId] = True
										titleEpisode = titles.get(i).get(numberId)
										if titleEpisode: entry['title'] = MetaImdb.cleanTitle(titleEpisode) # Use the uncombined title if available.
										extra.append(entry)
				data['episodes'].extend(Tools.listUnique(extra)) # The same unofficial episode can be added multiple times in the inner loop above.
			except: Logger.error()

			# Sort so that the list is in the order of the episode numbers.
			data['episodes'].sort(key = lambda i : i['episode'])

			# Remove unofficial episodes with episode numbers way greater than they should.
			# Eg: Jimmy Fallon S12 has 162 episodes on Trakt/TMDb/IMDb.
			# However, on TVDb the season finale is correct at S12E162, but it is immediatly followed by S12E1301 - S12E1305.
			# These episodes are actually part of S13, but S13 has not been added to TVDb yet. So they seem to add the episode with their absolute numbers to S12.
			episodes = []
			episodePrevious = None
			for i in data['episodes']:
				numberEpisode = i.get('episode')
				if episodePrevious:
					try: unoffical = i['packed']['type'][MetaPack.NumberUnofficial]
					except: unoffical = False
					if unoffical and numberEpisode > (episodePrevious + 201):
						continue
				episodePrevious = numberEpisode
				episodes.append(i)
			data['episodes'] = episodes

			# Determine the episode type.
			# Do this at the end, since it requires the previous/next episode, and unofficial episodes might have been added later on with the code above.
			try:
				statusShow = show.get('status')
				statusSeason = season.get('status')
				timePack = None
				episodePrevious = None
				episodeLastStandard = None
				episodeLastOfficial = None
				seasonLastStandard = None
				seasonLastOfficial = None
				try: episodeLastStandard = data['episodes'][-1].get('episode')
				except: pass
				if pack:
					timePack = pack.generated()

					# Get a more accurate last episode.,
					# Eg: Star Wars: Young Jedi Adventures S01E25 should be the last episode in S01, not the uncombined E26+ from TVDb.
					episode = pack.numberLastOfficialEpisode(season = originalSeason)
					if episode: episodeLastOfficial = episode
					episode = pack.numberLastStandardEpisode(season = originalSeason)
					if episode:
						episodeLastStandard = episode
						if not episodeLastOfficial: episodeLastOfficial = episode

						# Sometimes the pack is outdated for continuing seasons where new episodes are added on a weekly basis.
						# During pack generation, TVDb might already have the next/future episodes, while Trakt does not.
						# This can make the last official episode in the season to be the last episode listed on Trakt, although there are more TVDb episodes.
						# Eg: S.W.A.T. S08. The pack was created when Trakt had up to S08E18. When the episode metadata was refreshed, both Trakt and TVDb had the actual last episode S08E22. At this point S08E19+ were still unaired.
						# However, because the pack was a bit outdated, it only had Trakt episodes until S08E18, and because S08E19-S08E22 only had a TVDb number/ID, those last episodes were marked as unofficial.
						# This cause both S08E18 and S08E22 to be marked as series finale, at least until the pack data is refreshed.
						# If the last standard episode number is greater than last official number, and there is a TVDb number and no Trakt number, use the last standard number as the official number.
						if episodeLastStandard > episodeLastOfficial and not(statusShow == MetaTools.StatusEnded or statusShow == MetaTools.StatusCanceled):
							episode = pack.lastEpisodeStandard(season = originalSeason)
							if episode and pack.typeUnofficial(item = episode):
								numberSeason = pack.numberStandardSeason(item = episode)
								numberEpisode = pack.numberStandardEpisode(item = episode)
								numberTrakt = pack.numberStandardEpisode(season = numberSeason, episode = numberEpisode, provider = MetaPack.ProviderTrakt)
								numberTvdb = pack.numberStandardEpisode(season = numberSeason, episode = numberEpisode, provider = MetaPack.ProviderTvdb)
								if not numberTrakt and numberTvdb:
									# Do not do this if the last official episode is a finale.
									# Eg: LEGO Masters S04E13 (Trakt season finale) and S04E14 (unofficial TVDb episodes).
									lastType = pack.type(season = originalSeason, episode = episodeLastOfficial)
									if not lastType or not(Media.Finale in lastType and (Media.Inner in lastType or Media.Outer in lastType)):
										episodeLastOfficial = episodeLastStandard

					seasonLastStandard = pack.numberLastStandardSeason()
					seasonLastOfficial = pack.numberLastOfficialSeason()

				for i in range(len(data['episodes'])):
					try:
						episode = data['episodes'][i]
						numberSeason = episode.get('season')
						numberEpisode = episode.get('episode')

						# Use the IDs from the pack, since the mapping between providers might have changed them.
						type = None
						if pack:
							# Do not retrieve using pack.number(), since it will use NumberUniversal for lookups, which might not always match with NumberStandard.
							# Eg: Star Wars: Young Jedi Adventures S01E26 (NumberUniversal sees this as absolute, mapping to S02E01, while NumberStandard will retrieve the TVDb uncombined episode S01E26).
							#numbers = pack.number(season = numberSeason, episode = numberEpisode, number = False)
							entry = pack.episode(season = numberSeason, episode = numberEpisode, number = MetaPack.NumberStandard)
							if entry: type = pack.type(item = entry)

						# Use the proper alread-processed type from the previous episode.
						# Eg: Vikings S06E10 and S06E11.
						try: typePrevious = (data['episodes'][i - 1].get('type') if numberEpisode > 1 else None) or self.mTools.mergeType(types[numberSeason][numberEpisode - 1], season = numberSeason)
						except: typePrevious = None
						try: typeNext = self.mTools.mergeType(types[numberSeason][numberEpisode + 1], season = numberSeason)
						except: typeNext = None
						try: typeLast = self.mTools.mergeType(types[numberSeason][-1], season = numberSeason)
						except: typeLast = None
						try: typeProvider = typesProvider[numberSeason][numberEpisode]
						except: typeProvider = None
						try: typeProviderNext = typesProvider[numberSeason][numberEpisode + 1]
						except: typeProviderNext = None
						try: map = maps[numberSeason][numberEpisode]
						except: map = None
						try: mapNext = maps[numberSeason][numberEpisode + 1]
						except: mapNext = None
						try: unmap = unmaps[numberSeason][numberEpisode]
						except: unmap = None
						try: remap = remaps[numberSeason][numberEpisode]
						except: remap = None
						timeEpisode = self.mTools.time(type = MetaTools.TimePremiere, metadata = episode, estimate = False, fallback = False)

						value = types.get(numberSeason, {}).get(numberEpisode) or typesOriginal.get(numberSeason, {}).get(numberEpisode)

						# If the season is only on IMDb and not in the pack.
						# Eg: Money Heist S04 + S05.
						if imdbOnly:
							if not value: value = []
							value = value + [MetaPack.NumberUnofficial, Media.Alternate]
							if numberEpisode < MetaImdb.LimitDefault and numberEpisode == lastImdb and statusSeason in MetaTools.StatusesPast: value.append(Media.Finale)

						value = self.mTools.mergeType(value, season = numberSeason, seasonLastStandard = seasonLastStandard, seasonLastOfficial = seasonLastOfficial, episode = numberEpisode, episodeLastStandard = episodeLastStandard, episodeLastOfficial = episodeLastOfficial, episodePrevious = episodePrevious, type = type, typePrevious = typePrevious, typeNext = typeNext, typeLast = typeLast, typeProvider = typeProvider, typeProviderNext = typeProviderNext, map = map, mapNext = mapNext, remap = remap, unmap = unmap, timeEpisode = timeEpisode, timePack = timePack, statusShow = statusShow, statusSeason = statusSeason)
						if value: episode['type'] = value

						try: premiered = episode['time'][MetaTools.TimePremiere]
						except: premiered = None
						value = self.mTools.mergeStatus(statuses.get(numberSeason, {}).get(numberEpisode), media = media, season = numberSeason, episode = numberEpisode, time = premiered)
						if value: episode['status'] = value

						# Mark IMDb-exclusive episodes as storyline specials.
						# Eg: Downton Abbey S02E09.
						value = episode.get('special')
						if not value or not value.get('type'):
							beforeSeason = None
							beforeEpisode = None
							afterSeason = None
							afterEpisode = None
							type = episode.get('type') or []
							try: idsEpisode = [k for k, v in episode['id']['episode'].items() if v]
							except: pass
							idsCount = len(idsEpisode)
							if numberSeason > 0 and idsEpisode and 'imdb' in idsEpisode and (idsCount == 1 or (idsCount > 1 and Media.Special in type and Media.Alternate in type)):
								# Specials from IMDb.
								# Eg: Downton Abbey S02E09.
								# There are often Trakt/TMDb/TVDb IDs for these IMDb specials. Hence, also check the special/alternate types.
								value = [MetaData.SpecialEpisode, MetaData.SpecialImportant]
								if numberEpisode == 0:
									# Heroes S01E00 should be listed after S00E01 in the Series menu.
									beforeSeason = numberSeason
									beforeEpisode = 1
								else:
									# Make sure Downton Abbey S06E09 is interleaved before the movie specials in the Series menu.
									afterSeason = numberSeason
							elif Media.Special in type and idsEpisode and 'tvdb' in idsEpisode and ((idsCount == 1) or (idsCount == 2 and 'imdb' in idsEpisode)):
								# Specials on TVDb.
								# Eg: Dragon Ball Super S02E14 and S05E56.
								# For some reason S02E14 is marked as a movie on TVDb's website. But when retrieving it through the TVDb API, the "isMovie" attribute is 0. Not sure if this is a temporary caching issue on TVDb.
								value = [MetaData.SpecialEpisode, MetaData.SpecialImportant]
							else:
								# Specials from Trakt and TMDb.
								value = MetaData.specialExtract(data = episode.get('title'), exclude = [parentTitle])
								if not value: value = [MetaData.SpecialUnimportant]
							if value:
								if not episode.get('special'): episode['special'] = {}
								if not episode['special'].get('type'): episode['special']['type'] = value
								if episode['special'].get('story') is None: episode['special']['story'] = MetaData().specialStory(special = value)
								if episode['special'].get('extra') is None: episode['special']['extra'] = MetaData().specialExtra(special = value)

								if not beforeSeason is None or not beforeEpisode is None:
									if not episode['special'].get('before'): episode['special']['before'] = {}
									if not beforeSeason is None and episode['special']['before'].get('season') is None: episode['special']['before']['season'] = beforeSeason
									if not beforeEpisode is None and episode['special']['before'].get('episode') is None: episode['special']['before']['episode'] = beforeEpisode
								if not afterSeason is None or not afterEpisode is None:
									if not episode['special'].get('after'): episode['special']['after'] = {}
									if not afterSeason is None and episode['special']['after'].get('season') is None: episode['special']['after']['season'] = afterSeason
									if not afterEpisode is None and episode['special']['after'].get('episode') is None: episode['special']['after']['episode'] = afterEpisode
					except: Logger.error()
			except: Logger.error()

			# Set the show details.
			try: episode = data['episodes'][1] # SxxE02.
			except:
				try: episode = data['episodes'][0] # Possibly an unaired Pilot SxxE00, otherwise SxxE01.
				except: episode = None
			data['media'] = media # Add this so that MetaCache knows the media without having to access the inner "episodes" list.
			data['id'] = {}
			if imdb: data['id']['imdb'] = data['imdb'] = imdb
			if tmdb: data['id']['tmdb'] = data['tmdb'] = tmdb
			if tvdb: data['id']['tvdb'] = data['tvdb'] = tvdb
			if trakt: data['id']['trakt'] = data['trakt'] = trakt
			if slug: data['id']['slug'] = data['slug'] = slug
			if tvmaze: data['id']['tvmaze'] = data['tvmaze'] = tvmaze
			if tvrage: data['id']['tvrage'] = data['tvrage'] = tvrage

			title = parentTitle
			if not title and episode: title = episode.get('tvshowtitle')
			if title: data['tvshowtitle'] = data['title'] = title

			# Show year.
			year = parentYear
			if not year and episode: year = episode.get('tvshowyear') or episode.get('year')
			if year: data['tvshowyear'] = year

			# Season year.
			year = season.get('year')
			if not year and episode: year = episode.get('year')
			if year: data['year'] = year

			if not originalSeason is None: data['season'] = originalSeason

			# Add the season status for MetaCache.
			# Use the status of the pack, in case it is newer than the status from the season metadata.
			status = parentStatus
			if not status in (MetaTools.StatusEnded, MetaTools.StatusCanceled):
				statusPack = pack.status()
				if statusPack in (MetaTools.StatusEnded, MetaTools.StatusCanceled): status = statusPack
			data['status'] = status

			# Add the season type for MetaCache.
			data['type'] = parentType

			# Add season niche.
			# Currently not used, but could be used to help identify niches, such as mini-series.
			# Combine the show and season niches, since the show nich can have additional genere-based niches that are not in the season.
			niched = []
			nicheSeason = season.get('niche')
			if nicheSeason: niched.extend(nicheSeason)
			nicheShow = show.get('niche')
			if nicheShow: niched.extend(nicheShow)
			if not niched:
				# Not that accurate, since it contains niches from individual episodes that might not always apply to the season (eg: "standard" episode).
				try: niched.extend(self.mTools.mergeNiche(niches.get(originalSeason).values()))
				except: pass
			niche = self.mTools.niche(niche = niched, metadata = season or show, show = show, pack = pack)
			data['niche'] = niche

			# Sometimes the images are not available, especially for new/future releases.
			# This looks ugly in the menus. Mark as incomplete to re-retrieve sooner.
			if not imagesMissing is None:
				partDone = False
				try: partNew['tvdb']['complete'] = False
				except: pass
				if developer: Logger.log('EPISODE IMAGES INCOMPLETE: %s' % self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item, season = imagesMissing[0], episode = imagesMissing[1]))

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data: item.update(Tools.copy(data)) # Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'), season = originalSeason)
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self._busyFinish(media = media, item = item)

	def _metadataEpisodeId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, quick = None):
		result = self.mTools.idShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataEpisodeTrakt(self, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, season = None, language = None, item = None, cache = None, threaded = None, detail = None):
		complete = True
		result = None
		try:
			# Do not use the cached summarized data. Only if it comes from IMDb.
			try: origin = bool(item['temp']['trakt'])
			except: origin = False

			if detail == MetaTools.DetailEssential and item and origin: # Comes from a Trakt list with basic metadata.
				if MetaCache.Attribute in item:
					result = {}
				else:
					result = Tools.copy(item)
					try: del result['temp']
					except: pass
				result = self._metadataTemporize(item = item, result = result, provider = 'trakt')
			else: # Comes from another list, or forcefully retrieve detailed metadata.
				if trakt or imdb or tmdb or tvdb or title:
					# Trakt has an API limit of 1000 requests per 5 minutes.
					# Retrieving all the additional metadata will very quickly consume the limit if a few pages are loaded.
					# Only retrieve the extended metadata if enough requests are still avilable for the past 5 minutes.
					usage = self.providerUsageTrakt(authenticated = False)

					person = False
					if self.mModeGenerative: person = True
					elif detail == MetaTools.DetailExtended and usage < 0.5: person = True

					translation = None
					if detail == MetaTools.DetailEssential: translation = False # Use the translations from TVDb.

					# We already retrieve the cast (with thumbnails) and translations from TVDb.
					# Retrieving all of them here again will add little new metadata and only prolong the retrieval.
					# translation = None: only retrieve for non-English.
					return MetaTrakt.instance().metadataEpisode(trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, season = season, summary = True, translation = translation, person = person, language = language, extended = True, detail = True, cache = None if cache is False else cache, concurrency = bool(threaded))
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def _metadataEpisodeTvdb(self, tvdb = None, imdb = None, season = None, language = None, item = None, pack = None, cache = None, threaded = None, detail = None):
		try: return MetaTvdb.instance().metadataEpisode(tvdb = tvdb, imdb = imdb, season = season, pack = pack, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : True, 'data' : None}

	def _metadataEpisodeTmdb(self, tmdb = None, season = None, language = None, item = None, cache = None, threaded = None, detail = None):
		try: return MetaTmdb.instance().metadataEpisode(tmdb = tmdb, season = season, language = language, cache = cache, threaded = threaded, detail = True)
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataEpisodeImdb(self, imdb = None, season = None, language = None, item = None, cache = None, threaded = None, detail = None):
		results = []

		# Do not use the cached summarized data. Only if it comes from IMDb.
		try: origin = not item['episodes'][0]['temp']['imdb']['voting']['rating'] is None
		except:
			try: origin = not item[0]['temp']['imdb']['voting']['rating'] is None
			except: origin = False

		# Only do this if there is no IMDb rating in in the item, that is, the item does not come from a IMDb list.
		# Retrieving the detailed IMDb data does not really add extra metadata above TMDb/Trakt, except for the rating/vote and the revenue (which is also on TMDb).
		if detail == MetaTools.DetailExtended and imdb and not origin:
			data = MetaImdb.instance().metadataEpisode(id = imdb, season = season, language = language, cache = cache)
			if data:
				item = data
				origin = True

		complete = True
		result = []
		try:
			if origin and item and 'episodes' in item:
				current = Time.timestamp()
				for episode in item['episodes']:
					if episode and 'season' in episode and 'episode' in episode:
						resultEpisode = Tools.copy(episode)
						try: del resultEpisode['temp']
						except: pass
						resultEpisode = self._metadataTemporize(item = episode, result = resultEpisode, provider = 'imdb')
						if resultEpisode:
							# Check MetaImdb._extractItems() for more details.
							for attribute in ['genre', 'language', 'country']:
								value = episode.get(attribute)
								if value:
									value = Tools.listUnique(value + (resultEpisode.get(attribute) or []))
									if value: resultEpisode[attribute] = value
							for attribute in ['mpaa']:
								value = episode.get(attribute)
								if value: resultEpisode[attribute] = value

							result.append(resultEpisode)

						# Newley released seasons might not have ratings for all episodes yet.
						# Mark as incomplete in order to re-retrieve at a later stage when there are hopefully new ratings.
						if complete:
							if resultEpisode:
								# Only mark as incomplete if the episode has a premiere date and it is in the recent past.
								# If the episode does not have a premiere date, it is likley a future episode or an episode with a number above 50, meaning it is not retrieved from HTML, but from the bulk IMDb data.
								# 1. If it comes from the IMDb bulk data, the bulk data is only updated once in a while, and redoing this function mostly does not help, since the bulk data will probably not have been updated yet and the rating will still be None.
								# 2. If it is future episode, it also does not help redoing this function, since there will typically be no votes for unaired episodes yet.
								# 3. If the episode is in the far past and still has no rating yet, it also does not help redoing this function, since it is probably an unpopular show and that will not get any votes soon.
								try:
									premiere = resultEpisode.get('premiere')
									if premiere:
										age = current - Time.timestamp(fixedTime = premiere, format = Time.FormatDate)
										if age > 0 and age < 5256000: # In the past and less than 2 months ago.
											complete = bool(resultEpisode.get('rating'))
								except: Logger.error()
							else:
								complete = False
		except: Logger.error()
		results.append({'provider' : 'imdb', 'complete' : complete, 'data' : result or None})

		complete = True
		result = []
		try:
			if origin and item and 'episodes' in item:
				for episode in item['episodes']:
					if episode and 'temp' in episode and 'metacritic' in episode['temp']:
						if 'season' in episode and 'episode' in episode:
							resultEpisode = {'season' : episode['season'], 'episode' : episode['episode']}
							resultEpisode = self._metadataTemporize(item = episode, result = resultEpisode, provider = 'metacritic')
							if resultEpisode: result.append(resultEpisode)
		except: Logger.error()
		results.append({'provider' : 'metacritic', 'complete' : complete, 'data' : result or None})

		return results

	def _metadataEpisodeAggregate(self, items, refresh = None, quick = None, threaded = None, aggregate = True):
		# Adding the previous/current/next season metadata to individual episodes in _metadataEpisodeUpdate() is a bad idea, since the metadata is saved to the MetaCache database.
		# This increases the database size to quickly grow beyond 1GB+.
		# Especially for shows with many seasons, and seasons with a lot of episodes (eg S00 - Specials), this can easily increase the database size by more than 50%.
		# Instead, retrieve the season metadata from the season table on demand and add it to the dictionary.
		# This increases processing time slightly, although only by a few ms, but saves 100s of MBs of storage space.

		# The same applies to the 'pack'.
		# For shows with many episodes (eg S00 - Specials - can sometimes have 100s of episodes), this dictionary can be very large, since the title, duration, and numbers for each episode is stored.
		# The pack can further increase the database size by more than 50%.

		# Also add season images here.
		# The image URLs do not require that much extra storage space, so its not as bad as the seasons and pack attributes.
		# However, an advantage of doing this here, is that if the season updates with new images, the episodes will always have the latest ones.

		try:
			if items:
				values = items if Tools.isArray(items) else [items]
				if values and Tools.isArray(values[0]): values = Tools.listFlatten(values) # A list for multiple shows, each containing a list of episodes.

				seasons = []
				for item in values:
					try: seasons.append({'imdb' : item.get('imdb'), 'tmdb' : item.get('tmdb'), 'tvdb' : item.get('tvdb'), 'trakt' : item.get('trakt')})
					except: Logger.error()
				seasons = Tools.listUnique(seasons)
				seasons = self.metadataSeason(items = seasons, pack = False, refresh = refresh, quick = quick, threaded = threaded, aggregate = aggregate) if seasons else None

				if seasons:
					fixed = None
					for item in values:
						try: number = item['number'][MetaPack.NumberStandard][MetaPack.PartSeason]
						except: number = item.get('season')
						if not number == 0:
							fixed = number
							break

					for item in values:
						try:
							imdb = item.get('imdb')
							tmdb = item.get('tmdb')
							tvdb = item.get('tvdb')
							trakt = item.get('trakt')

							# For the Sequential/Absolute menu, use the stanadrd number, since the "season" attribute is 1 for all episodes.
							try: number = item['number'][MetaPack.NumberStandard][MetaPack.PartSeason]
							except: number = item.get('season')

							# For interleaved specials in the Series and Progress submenus, use the images of the current season and not S0.
							# Otherwise when flipping through the menu, the fanart changes, causing a visual disruption.
							if number == 0 and fixed: number = fixed

							for season in seasons:
								first = season[0] if season else None
								if first:
									if (imdb and first.get('imdb') == imdb) or (tmdb and first.get('tmdb') == tmdb) or (tvdb and first.get('tvdb') == tvdb) or (trakt and first.get('trakt') == trakt):
										if number is None:
											seasonCurrent = None
											seasonPrevious = None
											seasonNext = None
										else:
											seasonCurrent = next((i for i in season if i['season'] == number), None)
											seasonPrevious = next((i for i in season if i['season'] == number - 1), None)
											seasonNext = next((i for i in season if i['season'] == number + 1), None)

										if seasonCurrent:
											# Add show status used for label details in smart menus.
											# This status from the show to the season was already aggregated in _metadataEpisodeAggregate().
											serie = seasonCurrent.get('serie') or {}
											serie['season'] = {
												'status' : seasonCurrent.get('status'),
												'tagline' : seasonCurrent.get('tagline'),
											}
											item['serie'] = serie

										if seasonCurrent: seasonCurrent = self.mTools.reduce(metadata = seasonCurrent, pack = True, seasons = True)
										if seasonPrevious: seasonPrevious = self.mTools.reduce(metadata = seasonPrevious, pack = True, seasons = True)
										if seasonNext: seasonNext = self.mTools.reduce(metadata = seasonNext, pack = True, seasons = True)

										item['seasons'] = {
											'previous' : seasonPrevious,
											'current' : seasonCurrent,
											'next' : seasonNext,
										}

										if seasonCurrent and MetaImage.Attribute in seasonCurrent:
											MetaImage.update(media = MetaImage.MediaSeason, images = Tools.copy(seasonCurrent[MetaImage.Attribute]), data = item, category = MetaImage.MediaSeason) # Add season images.
											if MetaImage.MediaShow in seasonCurrent[MetaImage.Attribute]: MetaImage.update(media = MetaImage.MediaShow, images = Tools.copy(seasonCurrent[MetaImage.Attribute][MetaImage.MediaShow]), data = item, category = MetaImage.MediaShow) # Add show images.
										break

						except: Logger.error()
		except: Logger.error()
		return items

	def _metadataEpisodeIncrement(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, item = None, number = None, provider = None, lock = None, locks = None, semaphore = None, cache = False, refresh = None, threaded = None, discrepancy = None):
		try:
			media = Media.Episode

			if item:
				if imdb is None:
					imdb = item.get('imdb')
					if imdb: imdb = str(imdb)
				if tmdb is None:
					tmdb = item.get('tmdb')
					if tmdb: tmdb = str(tmdb)
				if tvdb is None:
					tvdb = item.get('tvdb')
					if tvdb: tvdb = str(tvdb)
				if trakt is None:
					trakt = item.get('trakt')
					if trakt: trakt = str(trakt)

				if title is None: title = item.get('tvshowtitle') or item.get('title')
				if year is None: year = item.get('tvshowyear') or item.get('year')

				if season is None: season = item.get('season')
				if episode is None: episode = item.get('episode')

			if not tvdb:
				ids = self._metadataEpisodeId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				if ids:
					ids = (ids.get('data') or {}).get('id') # "data" can be None if the ID was not found.
					if ids:
						if not imdb: imdb = ids.get('imdb')
						if not tmdb: tmdb = ids.get('tmdb')
						if not tvdb: tvdb = ids.get('tvdb')
						if not trakt: trakt = ids.get('trakt')
			if not imdb and not tvdb and not trakt and not tmdb: return False

			# Important to add "number" here, since there might be multiple lookups with different numbers (eg: standard vs sequential).
			id = Memory.id(media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, number = number, increment = True)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if item and data: item.update(Tools.copy(data)) # Copy in case the memory is used multiple times.
					return data

			developer = self._metadataDeveloper(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)

			pack = self.metadataPack(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, refresh = refresh, threaded = threaded)
			if not pack:
				if developer: Logger.log('CANNOT DETERMINE NEXT EPISODE: ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
				return False
			pack = MetaPack.instance(pack = pack)

			# If a sequential/absolute episode was passed in, continue with that numbering. Else default to the standard numbering.
			# When a specific number was requested (by passing in a "number" parameter), continue with that numbering (eg: Downton Abbey S01E07 -> S02E01 ("standard") and S01E07 -> S01E08 ("sequential")).
			# Otherwise, shows where some providers have a sequential/absolute season as standard season, will continue with the sequential numbering (eg: Dragon Ball Supper S01E14 -> S01E15).
			# Otherwise, when the requestsed number is not found as an standard number, continue with the sequential numbering (eg: Downton Abbey S01E07 -> S02E01 and S01E08 -> S01E09).
			# Otherwise, when no sequential/absolute number was requestsed, continue with the default/standard numbering (eg: Downton Abbey S01E07 -> S02E01).
			if number is None:
				for i in [MetaPack.NumberStandard, MetaPack.NumberSequential, MetaPack.NumberAbsolute]:
					if pack.episode(season = season, episode = episode, number = i):
						number = i
						break
				if not number: number = MetaPack.NumberStandard

			# Retrieve the next available episode after the last watched episode.
			# If the next episode is in the same season as the last watched episode, continue like normal and retrieve all episodes for the current season.
			# If the next episode is in the next season (aka last watched episode was the last episode from the previous season), retrieve the all episodes for next season.
			seasonNext = season + 1
			seasonSelect = None
			episodeNext = episode + 1
			episodeFirst = 1
			episodeSelect = None
			found = 0

			# Important to use "type = MetaPack.NumberOfficial" in all number lookups, otherwise unofficial episodes at the end of the season might be used, therefore not going to the next season.
			# Eg: One Piece S21E892 - S21E1088.
			# If the passed-in episode is not an official episode, use the standard number instead.
			# Eg: Dragon Ball Super S02E01.
			type = MetaPack.NumberOfficial
			if not pack.typeOfficial(season = season, episode = episode):
				type = MetaPack.NumberStandard
			else:
				# If the standard number does not match the one requested, check if it is an unofficial episode.
				# Eg: Star Wars: Young Jedi Adventures S01E48 -> S01E49.
				# This will probably not be the case anymore once S03 is released, since Trakt has 48 episodes for S01+S02.
				# Do not do this if the standard episode is the first episode in the next season.
				# Eg: Downton Abbey S01E08 -> S01E09.
				numberStandard = pack.numberStandard(season = season, episode = episode)
				numberStandardSeason = numberStandard[MetaPack.PartSeason]
				numberStandardEpisode = numberStandard[MetaPack.PartEpisode]
				if numberStandard and not(numberStandardSeason == season and numberStandardEpisode == episode) and not(numberStandardSeason == seasonNext and numberStandardEpisode == episodeFirst):
					if not pack.typeOfficial(item = pack.episode(season = season, episode = episode, number = MetaPack.NumberUnofficial)):
						type = MetaPack.NumberStandard
			if number == MetaPack.NumberOfficial or number == MetaPack.NumberUnofficial:
				type = number
				number = MetaPack.NumberStandard
			elif number in MetaPack.Providers:
				if not provider: provider = number
				type = MetaPack.NumberStandard
				number = MetaPack.NumberStandard

			# Next episode in the same season.
			if episodeNext <= pack.numberLastEpisode(season = season, number = number, provider = provider, type = type, default = -1):
				seasonSelect = season
				episodeSelect = episodeNext
				found = 1

			# First episode in the next season.
			elif episodeFirst <= pack.numberLastEpisode(season = seasonNext, number = number, provider = provider, type = type, default = -1):
				seasonSelect = seasonNext
				episodeSelect = episodeFirst
				found = 2

			# First episode in the next season.
			# If requested by NumberUnofficial, the next season's first episode is most likely an official episode.
			# Eg: My Name Is Earl S03E22 (TVDb unofficial) -> S04E01 (official).
			elif type == MetaPack.NumberUnofficial and episode == pack.numberLastEpisode(season = season, number = number, provider = provider, type = type, default = -1) and episodeFirst <= pack.numberLastEpisode(season = seasonNext, number = number, provider = provider, type = MetaPack.NumberOfficial, default = -1):
				seasonSelect = seasonNext
				episodeSelect = episodeFirst
				found = 2

			# Sequential numbering when there are unofficial episodes.
			# Eg: Star Wars: Young Jedi Adventures: S01E25 -> S01E26
			elif number == MetaPack.NumberSequential or number == MetaPack.NumberAbsolute:
				type = number
				if episodeNext <= pack.numberLastEpisode(season = season, number = number, provider = provider, type = number, default = -1):
					seasonSelect = season
					episodeSelect = episodeNext
					found = 1

			# If all episodes in a show are watched 1 time, the show is hidden from the Progress menu.
			# If a single episode in the show was watched 2 times while the rest were only watched 1 time (maybe by accident or rewatched after a long time), it shows up again in the Progress menu.
			# Hide these shows where the previous N episodes have a lower playcount than the current/last-watched episode.
			if discrepancy is None: discrepancy = self.mTools.settingsShowDiscrepancy()
			if discrepancy and found and seasonSelect and episodeSelect:
				from lib.modules.playback import Playback
				playback = Playback.instance()

				# NB: Use quick, to reduce time needed by Playback to lookup Trakt episode numbers, which are not needed here.
				countCurrent = playback.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, pack = pack, quick = True)

				if countCurrent:
					# The episode has progress, but is not fully watched yet.
					# Do not go to the next episode, but stick to the current episode.
					if not countCurrent['count']['total']:
						if developer: Logger.log('EPISODE UNFINISHED (NEXT): ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
						found = 3
					else:
						countNext = playback.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = seasonSelect, episode = episodeSelect, pack = pack, quick = True) # NB: Use quick, to reduce time.

						if countNext and countNext['count']['total']: # Only do this if the next episode was already watched (aka rewatch).
							countNext = countNext['count']['total']
							countCurrent = countCurrent['count']['total']

							# Previous episodes have a lower count.
							if countCurrent and countCurrent > 1:
								lookups = []
								seasonCounter = season
								episodeCounter = episode
								for i in range(5):
									episodeCounter -= 1
									if episodeCounter <= 0:
										if seasonCounter == 1: break
										seasonCounter -= 1
										episodeCounter = pack.numberLastEpisode(season = seasonCounter, number = number, provider = provider, type = type, default = 0)
									lookups.append({'season' : seasonCounter, 'episode' : episodeCounter})

								counter = 0
								for i in lookups:
									value = playback.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = i['season'], episode = i['episode'], pack = pack)
									if value and value['count']['total'] and value['count']['total'] >= countCurrent: counter += 1

								# 0.4: less than 2 out of 5.
								if (discrepancy == MetaTools.DiscrepancyLenient and counter == 0 and lookups) or (discrepancy == MetaTools.DiscrepancyStrict and counter < len(lookups) * 0.4):
									if developer: Logger.log('EPISODE HIDDEN (PREVIOUS): ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
									found = 0

							# Next episodes have the same playcount.
							# A previous season/episode might have been marked as watched at a later date than the next season/episode.
							# Hide these as well.
							if countCurrent == countNext:
								lookups = []
								seasonCounter = season
								episodeCounter = episode

								for i in range(10):
									add = True
									end = False
									episodeCounter += 1
									if episodeCounter > pack.numberLastEpisode(season = seasonCounter, number = number, provider = provider, type = type, default = 0):
										seasonCounter += 1
										if seasonCounter > pack.numberLastSeason(number = number, provider = provider, type = type, default = 0):
											add = False
											end = True
										else:
											episodeCounter = 1
									if add: lookups.append({'season' : seasonCounter, 'episode' : episodeCounter})
									if end: break

								counter = 0
								for i in lookups:
									countContinue = playback.history(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = i['season'], episode = i['episode'], pack = pack)
									if countContinue:
										countContinue = countContinue['count']['total']
										if not countContinue is None and not countContinue == countCurrent:
											counter += countContinue
											break
									else:
										counter += 1

								if (discrepancy == MetaTools.DiscrepancyLenient and counter == 0) or (discrepancy == MetaTools.DiscrepancyStrict and counter > 0):
									if developer: Logger.log('EPISODE HIDDEN (NEXT): ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
									found = 0

			if found == 0:
				data = {'invalid' : True}

				Memory.set(id = id, value = data, local = True, kodi = False)
				if item: item.update(data)

				if developer and self.mDeveloperExtra: Logger.log('NO NEXT EPISODE: ' + developer + (' [%s]' % Title.numberUniversal(season = season, episode = episode)))
				return None
			else:
				if found == 1: data = {'season' : season, 'episode' : episodeNext}
				elif found == 2: data = {'season' : seasonNext, 'episode' : episodeFirst}
				elif found == 3: data = {'season' : season, 'episode' : episode}

				Memory.set(id = id, value = data, local = True, kodi = False)
				if item: item.update(data)

				if developer and self.mDeveloperExtra: Logger.log('NEXT EPISODE FOUND: ' + developer + (' [%s -> %s]' % (Title.numberUniversal(season = season, episode = episode), Title.numberUniversal(season = data['season'], episode = data['episode']))))
				return number
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
		return None # Do not put inside "finally:".

	# This function takes in a list of episodes, containing both standard and special episodes.
	# It determines which specials to keep and which to remove, based on the episode type (eg: storyline special) and the user's specials settings.
	# The specials are then interleaved between the standard episodes, based on their release date and the fixed position that TVDb sometimes assigns to specials.
	def _metadataEpisodeSpecial(self, items, special = None, season = None, episode = None, number = None, pack = None):
		timeStart = None
		timeEnd = None
		timePrevious = None
		timeNext = None
		timeLimit = None
		timeBefore = None
		seasonLast = None
		seasonCurrent = season

		offset = not episode is None
		if season is None or episode is None or (season == 1 and episode == 1):
			season = None
			episode = None

		result = []
		for item in items:
			time = None
			try: time = item['aired']
			except: pass
			if not time:
				try: time = item['premiered']
				except: pass
			if not 'aired' in item: item['aired'] = time
			if not 'premiered' in item: item['premiered'] = time

			if not item['season'] == 0:
				if seasonLast is None or item['season'] > seasonLast: seasonLast = item['season']

				if time:
					timeValue = Time.integer(time)
					if timeStart is None or timeValue < timeStart: timeStart = timeValue # Include all specials prior to S01E01.
					if timeEnd is None or timeValue > timeEnd: timeEnd = timeValue

			if time and not season is None and item['season'] == season and item['episode'] == episode:
				timeLimit = Time.integer(time)

			result.append(item)
		items = result

		if number == MetaPack.NumberSerie and seasonCurrent: seasonLast = min(seasonLast, seasonCurrent)

		if pack and seasonLast:
			seasonCurrent = None
			seasonPrevious = None
			seasonNext = None
			for i in pack.season(default = []):
				if pack.typeOfficial(item = i): # Skip unofficial seasons (eg: Dragon Ball Super S02+).
					numberSeason = pack.numberStandard(item = i)
					if numberSeason == seasonLast: seasonCurrent = i
					elif numberSeason > 0 and numberSeason == seasonLast - 1: seasonPrevious = i
					elif numberSeason == seasonLast + 1: seasonNext = i

			if seasonCurrent:
				if seasonPrevious:
					time = pack.timeMaximumOfficial(item = seasonPrevious)
					if time: timePrevious = Time.integer(Time.format(timestamp = time, format = Time.FormatDate))
				else:
					timeStart = None # Is the first season. Inluce all previous specials.

				if seasonNext:
					time = pack.timeMinimumOfficial(item = seasonNext)
					if time: timeNext = Time.integer(Time.format(timestamp = time, format = Time.FormatDate))
				else:
					timeEnd = None # Is the last season. Include all remaining specials

		if timeLimit:
			if timeStart: timeStart = max(timeStart, timeLimit)
			else: timeStart = timeLimit

		# Get the last episode of the previous submenu.
		# This is used to filter out specials that belong to the previous submenu (aka they are actually placed before the last normal episode in the previous submenu).
		try:
			if pack:
				lastSeason = 0
				lastEpisode = 0
				for item in items:
					if item['season'] > 0:
						lastSeason = item['season']
						lastEpisode = item['episode']
						break
				if lastSeason > 1:
					if lastEpisode == 1:
						lastSeason -= 1
						lastEpisode = pack.countEpisode(season = lastSeason)
					else:
						lastEpisode -= 1
					timeBefore = pack.time(season = lastSeason, episode = lastEpisode)
					if timeBefore: timeBefore = Time.integer(Time.format(timestamp = timeBefore, format = Time.FormatDate))
		except: Logger.error()

		if timeStart or timeEnd or offset:
			reduce = special == MetaManager.SpecialReduce # Make sure it is boolean and not None.
			unofficial = self.mTools.settingsShowInterleaveUnofficial(reduce = reduce)
			extra = self.mTools.settingsShowInterleaveExtra(reduce = reduce)
			duration = self.mTools.settingsShowInterleaveDuration(reduce = reduce)

			average = None
			if pack:
				average = pack.durationMeanOfficial()
				if average: average *= duration

			result = []
			for item in items:
				# In case multiple specials have the same release date.
				if timeLimit:
					if not item['season'] == 0 and item['season'] < season: continue
					elif item['season'] == season and item['episode'] < episode: continue

				if item['season'] == 0:
					special = item.get('special')
					specialStory = None
					specialExtra = None
					if special:
						specialStory = special.get('story')
						specialExtra = special.get('extra')
					if not extra and specialStory: # For both None and False.
						# Only add storyline specials if they have a before/after number so that they can be placed at a predefined position.
						# This is useful for specials which have a premier date that is far off from its actual position, and will be correctly placed at the end of this function.
						# Eg: House S00E01.
						# If there is no before/after number, do not add here, but use the premier date to determine if it should be added.
						if special.get('before') or special.get('after'):
							result.append(item)
							continue
					elif extra is True and not specialStory:
						continue
					elif extra is False and not specialStory and specialExtra:
						continue

					# Update (2025-07): Why are only specials with a TVDb ID allowed?
					# Eg: Money Heist S0 has full episodes specials in S0 on Trakt which are not on TVDb.
					#if unofficial and (not 'episode' in item['id'] or not 'tvdb' in item['id']['episode'] or not item['id']['episode']['tvdb']):
					if unofficial and (not item['id'].get('episode') or len([i for i in item['id']['episode'].values() if i]) == 0): continue
					if duration and average and (not 'duration' in item or not item['duration'] or item['duration'] < average): continue

					time = None
					try: time = item['aired']
					except: pass
					if not time:
						try: time = item['premiered']
						except: pass

					if time:
						time = Time.integer(time)
						if (timeStart is None or time >= timeStart) and (timeEnd is None or time <= timeEnd):
							result.append(item)

						# For specials between seasons, determine if the special is closer to the current or the previous/next season.
						# Check for "time >= timePrevious"  and "time <= timeNext" for Trakt multiple submenus that are not devided strictly according to seasons.
						elif (timeStart is None or time < timeStart) and timePrevious and time >= timePrevious:
							differenceCurrent = abs(timeStart - time)
							differencePrevious = abs(timePrevious - time)
							if differenceCurrent < differencePrevious:
								if not item['season'] == 0 or (timeBefore and time >= timeBefore):
									result.append(item)
						elif (timeEnd is None or time > timeEnd) and timeNext and time <= timeNext:
							differenceCurrent = abs(timeEnd - time)
							differenceNext = abs(timeNext - time)
							if differenceCurrent < differenceNext:
								result.append(item)
				else:
					result.append(item)
		else:
			result = items

		# Make sure that specials are interleaved by airing date.
		# But also accomodate episodes that were not aired yet.
		# Eg: If S03E01 was not released yet, it should not be moved to the front of the list because it has no airing date.
		lastSeason = 0
		lastEpisode = 0
		lastAired = 0
		for i in reversed(result):
			if 'aired' in i and i['aired']:
				lastSeason = i['season']
				lastEpisode = i['episode']
				lastAired = Time.integer(i['aired'])
				break

		# (0.1 if i['season'] == 0 else 0.0): Move specials that were released on the same day as a normal episode, to AFTER the normal episode.
		# Eg: GoT 7x04 -> 0x29 Inside Episode 4 -> 7x05 -> 0x30 Inside Episode 5
		def _sort(item):
			currentSeason = item.get('season')
			currentEpisode = item.get('episode')
			currentAired = item.get('aired')
			if currentAired: order = Time.integer(currentAired) + (0.1 if currentSeason == 0 else 0.0)
			elif (currentSeason > lastSeason or (currentSeason == lastSeason and currentEpisode > lastEpisode)): order = lastAired
			else: order = 0
			return (order, currentSeason or 0, currentEpisode or 0)
		result = sorted(result, key = _sort)

		# Filter out unofficial TVDb episodes from a previous season that maps to a later official season.
		# Eg: LEGO Masters S05 (unofficial TVDb) vs S06 (official Trakt).
		# Otherwise in the Progress submenus S05E07+ (unofficial) are placed after S06E06 (official).
		temp = []
		previousSeason = None
		for item in result:
			currentSeason = item.get('season')
			if currentSeason == 0:
				temp.append(item)
			elif previousSeason is None or currentSeason >= previousSeason:
				temp.append(item)
				previousSeason = currentSeason
		result = temp

		# Specials appearing on the same day as the FIRST episode can sometimes be the same as described above.
		# Eg: GoT 8x01 -> 0x46 Inside Episode 1
		# But in most cases those specials should be placed BEFORE the first episode, since they are typically recaps, interviews, or other specials that are aired right before the new season premier.
		i = 0
		temp = []
		while i < len(result): # The index (i) in a for-loop cannot be adjusted within the loop iteself (eg: "i = j"). Use a while loop instead.
			item = result[i]
			if not item.get('season') == 0 and item.get('episode') == 1:
				aired = item.get('aired')
				if aired:
					for j in range(i + 1, len(result)):
						item2 = result[j]
						if item2.get('season') == 0 and item2.get('aired') == aired:
							i += 1
							temp.append(item2)
						else: break
			temp.append(item)
			i += 1
		result = temp

		# Move episode to a specific position, if the exact position is known.
		# That is, TVDb has set the before/after numbers.
		# Do not just go by date, since sometimes a special can be added a lot later with a later premier date, although it belongs earlier.
		# Eg: House S00E01 is an unaired pilot and should be placed before S01E01, but its premier date is only after S07.
		default = []
		fixed = []
		firstSeason = None
		firstEpisode = None
		lastSeason = None
		lastEpisode = None
		for item in result:
			currentSeason = item.get('season')
			if not currentSeason == 0:
				currentEpisode = item.get('episode')
				if firstSeason is None or currentSeason <= firstSeason:
					firstSeason = currentSeason
					if firstEpisode is None or currentEpisode < firstEpisode: firstEpisode = currentEpisode
				if lastSeason is None or currentSeason >= lastSeason:
					lastSeason = currentSeason
					if lastEpisode is None or currentEpisode > lastEpisode: lastEpisode = currentEpisode

			special = item.get('special')
			if special:
				if special.get('before') or special.get('after'):
					fixed.append(item)
					continue
			default.append(item)

		previousSeason = None
		previousEpisode = None
		if pack and default:
			first = default[0]
			if first.get('season') > 1 and first.get('episode') in (0, 1):
				previous = pack.lookupStandard(season= first.get('season') - 1, episode = -1)
				if previous:
					previousSeason = previous[MetaPack.PartSeason]
					previousEpisode = previous[MetaPack.PartEpisode]

		if fixed:
			try:
				for item in fixed:
					before = item.get('special').get('before')
					if before:
						beforeSeason = before.get('season')
						beforeEpisode = before.get('episode') or 1

						# The before/after numbers always come from TVDb. Convert to standard numbers, so they can be placed correctly, if Trakt has different numbers.
						# Eg: One Piece, the first few specials should be interleaved in S01 (Trakt), while the before/after numbers from TVDb indicate S02+.
						if pack:
							lookup = pack.lookupStandard(season = beforeSeason, episode = beforeEpisode, input = MetaPack.ProviderTvdb)
							if lookup and lookup[MetaPack.PartEpisode]:
								beforeSeason = lookup[MetaPack.PartSeason]
								beforeEpisode = lookup[MetaPack.PartEpisode]

						if beforeSeason >= firstSeason and beforeSeason <= lastSeason: # Exclude specials that do not belong within the current seasons.
							if (beforeSeason > firstSeason or beforeEpisode >= firstEpisode) and (beforeSeason < lastSeason or beforeEpisode <= lastEpisode):
								for i, item2 in enumerate(default):
									if item2.get('season') >= beforeSeason and item2.get('episode') >= beforeEpisode:
										default.insert(i, item)
										break
			except: Logger.error()

			# Reversed, because the inner loop is also reversed.
			# Otherwise sequential specials are out of order.
			# Eg: The Office UK S00E01 and S00E02 at the end of the Series menu.
			try:
				for item in reversed(fixed):
					after = item.get('special').get('after')
					if after:
						afterSeason = after.get('season')
						afterEpisode = after.get('episode')
						afterException = not afterEpisode
						if afterException: afterEpisode = 999999

						# The before/after numbers always come from TVDb. Convert to standard numbers, so they can be placed correctly, if Trakt has different numbers.
						# Eg: One Piece, the first few specials should be interleaved in S01 (Trakt), while the before/after numbers from TVDb indicate S02+.
						if pack:
							lookup = pack.lookupStandard(season = afterSeason, episode = -1 if afterException else afterEpisode, input = MetaPack.ProviderTvdb) # Lookup function works with negative numbers.
							if lookup and lookup[MetaPack.PartEpisode]:
								afterSeason = lookup[MetaPack.PartSeason]
								afterEpisode = lookup[MetaPack.PartEpisode]

						acceptedSeason = previousSeason or firstSeason
						if afterSeason >= acceptedSeason and afterSeason <= lastSeason: # Exclude specials that do not belong within the current seasons.
							if (afterSeason > acceptedSeason or afterEpisode >= firstEpisode) and (afterSeason < lastSeason or afterEpisode <= lastEpisode or afterException):
								inserted = False

								for i, item2 in reversed(list(enumerate(default))):
									currentSeason = item2.get('season')
									currentEpisode = item2.get('episode')
									if ((currentSeason == 0 and currentSeason == afterSeason) or (currentSeason > 0 and currentSeason <= afterSeason)) and currentEpisode <= afterEpisode:
										default.insert(i + 1, item) # +1 to insert AFTER the given episode. Eg: The Office UK S00E01 and S00E02 at the end of the Series menu.
										inserted = True
										break

								# Important if there are a bunch of specials between two seasons.
								# Eg: Create an episode submenu for Doctor Who that starts at S01E01 and has 10 episodes per page.
								# Go to the page between S04E13 and S05E01, which should contain S00E09, S00E13, S00E14, S00E15, S00E16, S00E17.
								# The page starts at S05E01 (firstSeason/firstEpisode), while the placement is after S04E13 (afterSeason/afterEpisode).
								# Hence, also include the last episode of the previous season if specials cannot be placed with the for-loop above.
								if not inserted:
									if previousSeason == afterSeason and previousEpisode == afterEpisode:
										default.insert(0, item)
			except: Logger.error()

		result = default

		return result

	# This function determines the episodes (number range) that need to be retrieved to create a single menu page, based on the season/episode number offset, page limit, and the numbering type.
	# Menu performance is improved, since only the minimum number of episodes have to be retrieved from the database (all episodes of a season grouped together).
	def _metadataEpisodeRange(self, pack, season, episode = None, limit = None, number = None):
		try:
			if limit is None: limit = self.limit(submenu = True)

			count = 0
			seasonStart = 1 if season == 0 else season
			seasonLast = None
			episodeStart = None if episode is None else episode
			episodeEnd = None
			episodeLast = None

			# Retrieve an additional season, since the More page simply increments the episode, and not the season, in the parameters passed to the next page.
			# If this is the last episode of the season, the increment will obviously be incorrect (eg: last S01 episode is S01E10, but the More page increments it to S01E11).
			# Hence, we might also ahve to retrieve the next season, since the increment is for the first episode of the next season (eg: S02E01).
			seasonEnd = seasonStart + 1

			# Add another season for Episode submenus (Progress menu).
			# Do not do this for Series submenus, since the menu always stops at the last episode of the season, and the next page loads the next seaason.
			# However, Episode submenus can page across multiple seasons (aka contain episodes from two season, plus the specials), so we might also have to include a few episodes from the next season in the menu.
			if not number == MetaPack.NumberSerie: seasonEnd += 1

			specialSeason = self.mTools.settingsShowSpecialSeason()
			specialEpisode = self.mTools.settingsShowSpecialEpisode()

			if pack:
				pack = MetaPack.instance(pack = pack)
				seasons = pack.season()

				if seasons:
					seasonLast = pack.numberLastOfficialSeason()
					episodeLast = pack.numberLastOfficialEpisode()

					# If the requested season is larger then the official last season, assume the unofficial seasons are used.
					# Eg: Dragon Ball Super. Last official season is S01 (Trakt). But the requested season might be S05, which is unofficial (TVDb).
					if not seasonLast is None and seasonLast < season:
						seasonLast = pack.numberLastUnofficialSeason()
						episodeLast = pack.numberLastUnofficialEpisode()

					for i in seasons:
						numberSeason = pack.numberStandard(item = i)
						if numberSeason >= seasonStart and (specialSeason or not numberSeason == 0):
							episodes = pack.episode(season = numberSeason) or [] # Can be None if there is a future season that does not contain any episodes yet.

							if episodeStart is None or not numberSeason == seasonStart: count += len(episodes)
							else: count += len([j for j in episodes if pack.numberStandardEpisode(item = j) >= episodeStart and (specialEpisode or not pack.numberStandardEpisode(item = j) == 0)]) # Only do this for seasonStart and not subsequent seasons.

							episodeEnd = episodeLast
							seasonEnd = numberSeason + 1
							if count >= limit: break

			if count == 0 and limit == 0:
				seasonStart += 1
				seasonEnd = seasonStart + 1
			if number == MetaPack.NumberSerie: seasonEnd = min(seasonEnd, seasonStart + 1) # Retrieve less seasons for series menus, since we know it will be cut off at the last episode of the season before paging to the next season.

			if seasonLast is None: seasonLast = seasonStart # Missing metadata for uncommon shows.
			seasonEnd = min(seasonEnd, seasonLast)

			result = {
				'limit' : limit,
				'season' : {'start' : seasonStart, 'end' : seasonEnd, 'last' : seasonLast},
				'episode' : {'start' : episodeStart, 'end' : episodeEnd, 'last' : episodeLast},
			}

			if pack and number in [MetaPack.NumberSequential, MetaPack.NumberAbsolute]:
				# Check the Absolute menu for GoT.
				# If the episode is not extracted first, the numberEnd/numberLast values are None, causing the Absolute menu for GoT to go to the next page after S01E73, starting back at S01E01.
				#numberStart = pack.numberEpisode(number = number, season = seasonStart, episode = episodeStart)
				#numberEnd = pack.numberEpisode(number = number, season = seasonEnd, episode = episodeEnd)
				#numberLast = pack.numberEpisode(number = number, season = seasonLast, episode = episodeLast)
				numberStart = pack.numberEpisode(number = number, item = pack.episode(season = seasonStart, episode = episodeStart))
				numberEnd = pack.numberEpisode(number = number, item = pack.episode(season = seasonEnd, episode = episodeEnd))
				numberLast = pack.numberEpisode(number = number, item = pack.episode(season = seasonLast, episode = episodeLast))

				result[number] = {'start' : numberStart, 'end' : numberEnd, 'last' : numberLast}

			return result
		except: Logger.error()
		return None

	##############################################################################
	# METADATA - PACK
	##############################################################################

	def metadataPack(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = None, cache = False, threaded = None):
		try:
			media = Media.Pack

			pickSingle = False
			pickMultiple = False

			if items:
				if Tools.isArray(items):
					pickMultiple = True
				else:
					pickSingle = True
					items = [items]
			elif trakt or imdb or tmdb or tvdb:
				pickSingle = True
				items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'title' : title, 'year' : year}] # Add the title/year for a possible lookup if Trakt does not have the IMDb ID yet.
			elif title:
				pickSingle = True
				items = self._metadataIdLookup(media = media, title = title, year = year, list = True)

			if items:
				# Get into the correct format for MetaCache to update the dictionaries.
				for item in items:
					value = item.get('tvshowtitle') or item.get('title')
					if not value is None and not Tools.isArray(value): item['title'] = [value]
					value = item.get('tvshowyear') or item.get('year')
					if not value is None and not Tools.isDictionary(value): item['year'] = {MetaPack.ValueMinimum : value}

				items = self._metadataCache(media = media, items = items, function = self._metadataPackUpdate, quick = quick, refresh = refresh, cache = cache, threaded = threaded)

				if items:
					items = self._metadataFilter(media = media, items = items, filter = filter)

					if pickSingle: items = items[0] if items else None

					items = self._metadataClean(media = media, items = items, clean = clean)

					return items
		except: Logger.error()
		return None

	def _metadataPackUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, cache = False, threaded = None, mode = None, refresh = None, part = True):
		try:
			if not self._checkInterval(mode = mode): return None

			media = Media.Pack

			imdb = item.get('imdb')
			tmdb = item.get('tmdb')
			tvdb = item.get('tvdb')
			trakt = item.get('trakt')
			slug = item.get('slug')
			tvmaze = item.get('tvmaze')
			tvrage = item.get('tvrage')

			title = item.get('tvshowtitle') or item.get('title')
			year = item.get('tvshowyear') or item.get('year')

			if title and Tools.isArray(title): title = title[0]
			if year and Tools.isDictionary(year): year = year.get(MetaPack.ValueMinimum)

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same show appears multiple times in the list (some Trakt lists, eg watched list where a show was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					if data:
						# Copy in case the memory is used multiple times. Can be None if not found.
						# Update (2025-11): Deep-copying pack data can take very long, especially for shows with a lot of episodes (eg tt0112004).
						# Only do a very-efficient shallow-copy. This should be enough, since the internal pack dict data should not be edited afterwards and all access to the data is ready-only get.
						# Not sure if this would create some issues, like updating and existing pack dict.
						#item.update(Tools.copy(data))
						item.update(Tools.copy(data, deep = False))
					return None

			# Previous incomplete metadata.
			partDone = True
			partStatus = None
			partOld = {}
			partNew = {MetaCache.AttributeFail : 0}
			try:
				partCache = item.get(MetaCache.Attribute)
				if partCache:
					partStatus = partCache.get(MetaCache.AttributeStatus)
					# Only do this for StatusPartial.
					# Other non-partial statuses that cause a refresh might also have the "part" dictionary.
					# However, in these cases the old "part" data should not be used, since as full refresh is needed and all requests should be redone.
					if part and partStatus == MetaCache.StatusPartial:
						partOld = partCache.get(MetaCache.AttributePart) or {}
						partNew[MetaCache.AttributeFail] = partOld.get(MetaCache.AttributeFail, 0)
			except: Logger.error()

			# Trakt requires either a Trakt or IMDb ID.
			# TMDb requires a TMDb ID.
			if not tvdb or (not imdb and not trakt) or (self.mLevel >= 1 and not tmdb) or (self.mLevel >= 2 and not imdb):
				ids = partOld.get('id')
				if not ids or not ids.get('complete'): ids = self._metadataPackId(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
				partNew['id'] = ids
				if ids:
					if not ids.get('complete'): partDone = False
					ids = ids.get('data')
					if ids:
						ids = ids.get('id')
						if ids:
							if not imdb: imdb = ids.get('imdb')
							if not tmdb: tmdb = ids.get('tmdb')
							if not tvdb: tvdb = ids.get('tvdb')
							if not trakt: trakt = ids.get('trakt')
							if not slug: slug = ids.get('slug')
							if not tvmaze: tvmaze = ids.get('tvmaze')
							if not tvrage: tvrage = ids.get('tvrage')
			if not imdb and not tmdb and not tvdb and not trakt: return False

			# Use the IDs of the show metadata.
			# This is useful if Trakt does not have the IMDb/TVDb ID yet.
			# The show metadata would have already done a MetaTrakt.lookup(), so it does not have to be done here again.
			# Always replace the values, in case the season metadata still contains old IDs or title.
			show = self.metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, pack = False, refresh = refresh, threaded = threaded)
			idsShow = show.get('id')
			if idsShow:
				trakt = idsShow.get('trakt') or trakt
				imdb = idsShow.get('imdb') or imdb
				tmdb = idsShow.get('tmdb') or tmdb
				tvdb = idsShow.get('tvdb') or tvdb
				slug = idsShow.get('slug') or slug
			title = show.get('tvshowtitle') or show.get('title') or title
			year = show.get('tvshowyear') or show.get('year') or year

			cache = cache if cache else None
			developer = self._metadataDeveloper(media = Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, item = item)
			if developer: Logger.log('PACK METADATA RETRIEVAL [%s - %s]: %s' % (mode.upper() if mode else 'UNKNOWN', partStatus.upper() if partStatus else 'NEW', developer))

			# DetailEssential: 3 requests [Trakt: 2 (episodes, translations), TVDb: 1 (episodes), TMDb: 0, IMDb: 0 (local bulk data is used)]
			# DetailStandard: 4 requests [Trakt: 2 (episodes, translations), TVDb: 1 (episodes), TMDb: 1 (summary), IMDb: 0 (local bulk data is used)]
			# DetailExtended: 5-7 requests [Trakt: 2 (episodes, translations), TVDb: 1 (episodes), TMDb: 2-4 (summary, episodes), IMDb: 0 (local bulk data is used)]
			requests = []
			if self.mLevel >= 0:
				requests.append({'id' : 'tvdb', 'function' : self._metadataPackTvdb, 'parameters' : {'tvdb' : tvdb, 'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				requests.append({'id' : 'trakt', 'function' : self._metadataPackTrakt, 'parameters' : {'trakt' : trakt, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'title' : title, 'year' : year, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
				if self.mLevel >= 1:
					requests.append({'id' : 'tmdb', 'function' : self._metadataPackTmdb, 'parameters' : {'tmdb' : tmdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})
					if self.mLevel >= 2:
						requests.append({'id' : 'imdb', 'function' : self._metadataPackImdb, 'parameters' : {'imdb' : imdb, 'item' : item, 'cache' : cache, 'threaded' : threaded, 'language' : self.mLanguage, 'detail' : self.mDetail}})

			partDatas = {}
			if partOld:
				# Do not use the old parts if retrieving in the foreground.
				# Otherwise if the metadata is refreshed forcefully (eg: from the context menu), and the current MetaCache entry is incomplete, it will use the existing old parts and only refresh the previously failed/incomplete parts.
				# Instead, refresh all parts if the refresh is in the foreground.
				# MetaCache.StatusPartial refreshes happen by default in the background, which will still only re-retrieve the incomplete parts.
				if not mode == MetaCache.RefreshForeground:
					partRequests = []
					for i in requests:
						partData = partOld.get(i['id'])
						if partData and partData.get('complete'): partDatas[i['id']] = MetaPack.fix(provider = i['id'], data = partData)
						else: partRequests.append(i)
					requests = partRequests
					partDatas = Tools.copy(partDatas) # Copy inner dicts that can be carried over with the update() below.

			if not self._checkInterval(mode = mode): return None
			datas = self._metadataRetrieve(requests = requests, threaded = threaded)
			if not self._checkInterval(mode = mode): return None
			datas.update(partDatas)

			data = {}
			for i in ['imdb', 'tmdb', 'trakt', 'tvdb']:
				if i in datas:
					value = datas[i]
					if value:
						partNew[i] = value
						if value['complete']:
							data[i] = value.get('data')

						# Do not mark packs as partial if the IMDb data is missing
						# This can happen if the bulkdata setting was disabled.
						# Also do not do this in case the datasets are removed from IMDb in the future.
						# Otherwise all packs will constantly be partial-refreshed, because all of them have the IMDb data missing.
						elif not i == 'imdb':
							partDone = False
							if developer: Logger.log('PACK METADATA INCOMPLETE [%s]: %s' % (i.upper(), developer))

			pack = MetaPack()
			if data:
				data['check'] = MetaPack.CheckBackground if (mode == MetaCache.RefreshBackground or self.reloadingMedia()) else MetaPack.CheckForeground
				data = pack.generateShow(**data)
				if data is False or not self._checkInterval(mode = mode): return None # Kodi was aborted.

				# Store the reduced pack metadata (counts, durations, etc) in the show metadata.
				# This does not require a lot of extra storage space.
				# This allows for eg: season/episode counters in show menus (for certain skins that support it, like Aeon Nox).
				# Only shows that the user has shown interest in, by eg opening the season menu of the show, will retrieve these detailed counters.
				try:
					if show:
						reduce = pack.reduce()
						if reduce:
							metacache = MetaCache.instance()
							shows = metacache.select(type = MetaCache.TypeShow, items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt}], memory = False)
							if shows and MetaCache.valid(shows[0]): # Only if the data is already in the cache and not eg invalid or from external addon.
								# Do not update the time, rather use the old time.
								# Otherwise the show data has the time when the pack was last updated, and not the time the show was last updated.
								time = shows[0][MetaCache.Attribute].get(MetaCache.AttributeTime)
								try: del shows[0][MetaCache.Attribute]
								except: pass
								shows[0]['packed'] = reduce
								shows[0]['niche'] = self.mTools.niche(niche = shows[0].get('niche'), metadata = shows[0]) # Add the release types (eg daily episode release).
								metacache.insert(type = MetaCache.TypeShow, items = shows, time = time, wait = True, copy = False) # Update (2025-11): Copy is probably unnecessary here.
				except: Logger.error()

				if data:
					ids = data.get('id') or {}
					if not data.get('imdb'):
						if ids.get('imdb'): data['imdb'] = ids.get('imdb')
						elif imdb: data['imdb'] = imdb
					if not data.get('tmdb'):
						if ids.get('tmdb'): data['tmdb'] = ids.get('tmdb')
						elif tmdb: data['tmdb'] = tmdb
					if not data.get('tvdb'):
						if ids.get('tvdb'): data['tvdb'] = ids.get('tvdb')
						elif tvdb: data['tvdb'] = tvdb
					if not data.get('trakt'):
						if ids.get('trakt'): data['trakt'] = ids.get('trakt')
						elif trakt: data['trakt'] = trakt
					if not data.get('slug'):
						if ids.get('slug'): data['slug'] = ids.get('slug')
						elif slug: data['slug'] = slug
					if not data.get('tvmaze'):
						if ids.get('tvmaze'): data['tvmaze'] = ids.get('tvmaze')
						elif tvmaze: data['tvmaze'] = tvmaze
					if not data.get('tvrage'):
						if ids.get('tvrage'): data['tvrage'] = ids.get('tvrage')
						elif tvrage: data['tvrage'] = tvrage

			Memory.set(id = id, value = data, local = True, kodi = False)
			if item and data:
				# Can be None if the ID was not found. Copy in case the outer item is edited before we write the data to MetaCache.
				# Update (2025-11): Deep-copying pack data can take very long, especially for shows with a lot of episodes (eg tt0112004).
				# Only do a very-efficient shallow-copy. This should be enough, since the internal pack dict data should not be edited afterwards and all access to the data is ready-only getters.
				# Not sure if this would create some issues, like updating and existing pack dict.
				#item.update(Tools.copy(data))
				item.update(Tools.copy(data, deep = False))
			elif not data: data = {}

			if partDone:
				try: item[MetaCache.Attribute][MetaCache.AttributePart] = None
				except: pass
			else:
				partNew[MetaCache.AttributeFail] += 1
				data[MetaCache.Attribute] = {MetaCache.AttributePart : partNew}

			self._batchLoad(media = media, imdb = data.get('imdb'), tmdb = data.get('tmdb'), tvdb = data.get('tvdb'), trakt = data.get('trakt'))
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self._busyFinish(media = media, item = item)

	def _metadataPackId(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, quick = None):
		result = self.mTools.idShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick)
		if result: return {'complete' : True, 'data' : {'id' : result}}
		else: return {'complete' : False, 'data' : result}

	def _metadataPackTrakt(self, trakt = None, imdb = None, tmdb = None, tvdb = None, title = None, year = None, language = None, item = None, cache = None, threaded = None, detail = None):
		if trakt or imdb or tmdb or tvdb or title:
			try: return MetaTrakt.instance().metadataPack(trakt = trakt, imdb = imdb, tmdb = tmdb, tvdb = tvdb, title = title, year = year, cache = cache, threaded = threaded, detail = True)
			except: Logger.error()
		return {'provider' : 'trakt', 'complete' : True, 'data' : None}

	def _metadataPackTvdb(self, tvdb = None, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		if tvdb or imdb:
			try: return MetaTvdb.instance().metadataPack(tvdb = tvdb, imdb = imdb, cache = cache, threaded = threaded, detail = True)
			except: Logger.error()
		return {'provider' : 'tvdb', 'complete' : True, 'data' : None}

	def _metadataPackTmdb(self, tmdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		if tmdb:
			try: return MetaTmdb.instance().metadataPack(tmdb = tmdb, cache = cache, threaded = threaded, detail = True, quick = not(detail == MetaTools.DetailExtended))
			except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : True, 'data' : None}

	def _metadataPackImdb(self, imdb = None, language = None, item = None, cache = None, threaded = None, detail = None):
		if imdb:
			try: return MetaImdb.instance().metadataPack(imdb = imdb, detail = True)
			except: Logger.error()
		return {'provider' : 'imdb', 'complete' : True, 'data' : None}

	def _metadataPackPrepare(self, items):
		if Tools.isArray(items):
			if items and Tools.isArray(items[0]): items = Tools.listFlatten(items, recursive = False)
		else:
			items = [items]
		return items

	def _metadataPackRetrieve(self, items = None, instance = False, quick = None, refresh = None, cache = False, threaded = None):
		try:
			if items:
				# If multiple seasons/episodes of the same show is passed in, only retrieve the pack once for all of them.
				ids = ['trakt', 'tvdb', 'tmdb', 'imdb']
				items = self._metadataPackPrepare(items = items)
				lookup = Tools.listUnique([{i : item.get(i) for i in ids} for item in items])
				if lookup:
					data = self.metadataPack(items = lookup, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
					if data:
						# Create a dictionary for faster lookups.
						packs = {i : {} for i in ids}
						for i in data:
							for j in ids:
								try: id = i.get('id').get(j)
								except: id = None
								if id: packs[j][id] = MetaPack.instance(pack = i) if instance else i
						return packs
		except: Logger.error()
		return None

	# Add pack data to the show/season/episode items.
	def _metadataPackAggregate(self, items = None, pack = None, data = None, quick = None, refresh = None, cache = False, threaded = None):
		try:
			if items:
				if pack is None: pack = True # Add pack data by default, except if explicitly stated not to (eg: from show menus).
				if pack:
					if data: # Faster if pack was already retrieved previously and all items belong to the same show.
						for item in (items if Tools.isArray(items) else [items]):
							item['pack'] = data
					else:
						values = self._metadataPackPrepare(items = items) # Do not change "items", since they are returened byt the function.
						packs = self._metadataPackRetrieve(items = values, instance = False, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
						if packs:
							for item in values:
								for i in packs.keys():
									try: id = item.get('id').get(i)
									except: id = item.get(i)
									if id:
										try: data = packs.get(i).get(id)
										except: data = None
										if data:
											# Do not create a deep copy of each pack, but only add the reference to the same dictionary.
											# Pack data can get very large, and since it is static/unchangeable, there does not seem be a reason for copying the pack for each item.
											item['pack'] = data
											break
		except: Logger.error()
		return items

	# Lookup the real native season-episode numbers from other numbers, like absolute episodes.
	def _metadataPackLookup(self, items = None, number = None, provider = None, quick = None, refresh = None, cache = False, threaded = None):
		lookup = None
		try:
			if items:
				packs = self._metadataPackRetrieve(items = items, instance = True, quick = quick, refresh = refresh, cache = cache, threaded = threaded)
				if packs:
					input = number or provider
					lookup = {i : {} for i in packs.keys()}
					for item in (items if Tools.isArray(items) else [items]):
						for i in packs.keys():
							try: id = item.get('id').get(i)
							except: id = item.get(i)
							if id:
								try: pack = packs.get(i).get(id)
								except: pack = None
								if pack:
									if not id in lookup[i]: lookup[i][id] = {}
									season = item.get('season')
									episode = item.get('episode')
									original = (season, episode)
									value = pack.lookupStandard(season = season, episode = episode, input = input)
									if value:
										if Tools.isArray(value):
											item['season'] = value[0]
											item['episode'] = value[1]
											lookup[i][id][tuple(value)] = original
										else:
											item['season'] = value
									else:
										lookup[i][id][original] = original
									break
		except: Logger.error()
		return lookup

	# Revert the season/episode numbers back to the original numbers, as requested.
	def _metadataPackNumber(self, items = None, lookup = None, season = None, episode = None, numbering = None, number = None):
		try:
			if items:
				if not numbering is None:
					if not number: number = MetaPack.NumberSequential
					for item in (items if Tools.isArray(items) else [items]):
						try: value = item['number'][number][1]
						except:
							try: value = item[number][1]
							except: value = None
						item['season'] = 1
						item['episode'] = value or 0
				elif lookup:
					for item in (items if Tools.isArray(items) else [items]):
						value = (item.get('season'),) if episode is None else (item.get('season'), item.get('episode'))
						for i in lookup.keys():
							try: found = lookup.get(i).get(item.get(i)).get(value)
							except: found = None

							# NB: Only change the original number if it is not negative.
							# Since the episode Progress menu retrieves 3 "history" items, so the episode number can be negative.
							# In such a case, keep the real looked-up number.
							if found and found[1] >= 0:
								item['season'] = found[0]
								item['episode'] = found[1]
								break
		except: Logger.error()
		return items

	##############################################################################
	# CONTENT
	##############################################################################

	'''
		detail: Retrieve detailed metadata.
			True/None: Retrieve detailed metadata, which takes longer.
			False: Retrieve only basic metadata, like IDs, which is faster.
		quick: How to retrieve the detailed metadata.
			True: Retrieve whatever is in the cache and the rest in the background. Could return no items at all.
			False: Retrieve whatever is in the cache and the rest not at all. Could return no items at all.
			Positive Integer: Retrieve the given number of items in the foreground and the rest in the background.
			Negative Integer: Retrieve the given number of items in the foreground and do not retrieve the rest at all.
		refresh: Refresh the list.
			True: Forcefully refresh the list source data.
			False/None: Do not refresh the list source data, but retrieve it from the cache.
		menu: Load the menu.
			True/None: Load the Kodi directory/menu.
			False: Do not load the Kodi directory/menu, just retrun the items as a list.
		more: Add a next page.
			True/None: Add a 'More' item to the end of the list if available.
			False: Do not add a 'More' item to the end of the list.
	'''
	def content(self, media = None, niche = None, content = None, progress = None, page = None, limit = None, refresh = None, reload = None, internal = None, **parameters):
		if not niche: niche = None # Can be [].

		# Do not retrieve full pack data when loading show menus.
		# This requires more and longer API calls to providers, and more local processing to generate the packs.
		# For most of the shows in the menu, the user is not interested in them and it would be a waste to retrieve packs for them.
		# Only if a season/episode is opened underneath a show, or other calls such as scraping or the context menu, will the full pack data be retrieved.
		# That is: only retrieve/generate packs if they will actually be used.
		# More info at MetaManager.metadata().
		# Update: This was moved from MetaMenu._menuMedia() to here.
		# Otherwise when the mixed Quick menu is opened, it has parameters = {'pack' : False}
		# But when we call MetaManager.reload() after an episode was watched, this function is called with parameters = {}
		# Hence, the _cache() call below is different, since the parameters are different.
		# This makes the main Quick menu not refresh with the latests watched episode.
		if (not media or Media.isMixed(media) or Media.isShow(media)) and not content == MetaManager.ContentProgress:
			pack = parameters.get('pack')
			if pack is None: parameters['pack'] = False

		# Cache the Quick, Progress, and Arrivals menu to make them faster.
		# This reduces menu loading time by +-50%, since the cached data already contains the detailed metadata, filtered and sorted.
		# Only do this for certain menus, only for the first page, and not for niche menus, since each of these calls has to be manually refreshed from reload().
		# Also do not do this for too many types of menus, or beyond page 1, otherwise it requires too much cache disk space.
		# Every time the cache data is retrieved, it will immediately refresh the data in the background ("cacheRefresh").
		if not niche and not page and not limit and not refresh and not internal:
			if (content == MetaManager.ContentProgress and progress == MetaTools.ProgressDefault) or content == MetaManager.ContentArrival or content == MetaManager.ContentQuick:
				# Make sure the parameters are the same for the cache.
				if parameters: parameters = {k : v for k, v in parameters.items() if not v is None} # Can be a dict with all values None if called from progress().

				# Update (2025-11):
				# Even though the refresh is done in the background, it still has some impact on performance, since the reloading can be done too often.
				# Since the episode submenus are executed in a separate invoker, every time the user navigates back from an episode submenu to the main Progress menu, the progress menu gets reloaded, since it is not cached by Kodi.
				# Hence, if the user navigates in and out of shows from the Progress menu, the content gets reloaded every time, although the data has probably not changed and therefore does not require an immediate refresh.
				# Therefore cache the menu for a minute to avoid these unnecessary repeated refreshes.
				# Still force a refresh when the menu is reloaded from MetaManager.reload().
				# Also add a delay for background refreshes, to allow any other process to execute first, such as when opening an episode submenu.
				#return self._cache('cacheRefresh', reload, self._content, media = media, niche = niche, content = content, progress = progress, **parameters)
				if reload:
					return self._cache('cacheRefresh', reload, self._content, media = media, niche = niche, content = content, progress = progress, **parameters)
				else:
					# Make sure this has the same perameters as the cacheRefresh call above, otherwise it will be a different cache entry.
					# Hence, __exclude__ the delay parameter from the cache ID calculation.
					return self._cacheTimeout(Cache.TimeoutMinute1, None, self._content, media = media, niche = niche, content = content, progress = progress, delay = (Pool.DelayLong, Pool.DelayMedium), __exclude__ = 'delay', **parameters)

		return self._content(media = media, niche = niche, content = content, progress = progress, page = page, limit = limit, refreshing = refresh, **parameters)

	def _content(self,
		# Use default None values, so that we can pass None in from the script parameters in addon.py.

		media = None,
		niche = None,

		content = None,
		items = None,

		type = None, # Can be used as an alias for the parameters below.
		search = None,
		progress = None,
		arrival = None,
		history = None,
		set = None,
		list = None,
		person = None,

		imdb = None,
		tmdb = None,
		tvdb = None,
		trakt = None,

		title = None,
		season = None,
		episode = None,
		pack = None,

		query = None,
		keyword = None,
		release = None,
		status = None,
		year = None,
		date = None,
		duration = None,
		genre = None,
		language = None,
		country = None,
		certificate = None,
		company = None,
		studio = None,
		network = None,
		award = None,
		gender = None,
		ranking = None,
		rating = None,
		votes = None,

		filter = None,
		sort = None,
		order = None,
		page = None,
		limit = None,
		offset = None,

		provider = None,
		more = None,

		detail = None,
		quick = None,
		delay = None,
		refreshing = None, # "refresh" is a parameter for the Cache.

		submenu = None,		# The episode submenu opened from an episode in the Progress menu or from the Series menu.
		special = None,		# Interleave specials between episodes in the Progress menu or from the Series menu, based on their date. SpecialSettings (None): use settings, SpecialInclude (True): include specials, SpecialExclude (False): exclude specials, SpecialReduce ("reduce"): include specials, but reduce the number of specials.

		# Only for internal use.
		filters = None, # Use the "filter" parameter instead if custom filters should be passed in. Read the comments in the function below for more info on this.

		# Allow other parameters to be passed in, which will be ignored.
		# This is useful if some parameters from and old Gaia version are still passed in.
		# Eg: The user has setup a skin widget, which sets the parameters XYZ. In a later Gaia version, parameter XYZ gets renamed/removed. This should not break the widget.
		**parameters
	):
		try:
			# Delay this function, allowing other more important processes to execute first, such as menu loading.
			# Add a minimum delay ("minimum=True"), otherwise it might get executed too quickly if the current process does not have any more work, and we should wait for any other/external invokers currently busy.
			if delay:
				minimum = True
				if delay is True: delay = Pool.DelayShort
				elif Tools.isArray(delay):
					minimum = delay[1]
					delay = delay[0]
				Pool.wait(delay = delay, minimum = minimum)

			data = None
			parameters = {}
			refresh = refreshing
			if filters: filter = filters

			if not content is None: parameters['content'] = content
			if not media is None: parameters['media'] = media
			if not niche is None: parameters['niche'] = niche

			if type:
				if content == MetaManager.ContentSearch: search = type
				elif content == MetaManager.ContentProgress: progress = type
				elif content == MetaManager.ContentArrival: arrival = type
				elif content == MetaManager.ContentHistory: history = type
				elif content == MetaManager.ContentSet: set = type
				elif content == MetaManager.ContentList: list = type
				elif content == MetaManager.ContentPerson: person = type
			if not search is None: parameters['search'] = search
			if not progress is None: parameters['progress'] = progress
			if not arrival is None: parameters['arrival'] = arrival
			if not history is None: parameters['history'] = history
			if not set is None: parameters['set'] = set
			if not list is None: parameters['list'] = list
			if not person is None: parameters['person'] = person

			# IDs can be integers when decoded in MetaMenu.
			# Trakt can have 2 values for the ID for lists (username + list ID).
			if not imdb is None: parameters['imdb'] = imdb if Tools.isArray(imdb) else str(imdb)
			if not tmdb is None: parameters['tmdb'] = tmdb if Tools.isArray(tmdb) else str(tmdb)
			if not tvdb is None: parameters['tvdb'] = tvdb if Tools.isArray(tvdb) else str(tvdb)
			if not trakt is None: parameters['trakt'] = trakt if Tools.isArray(trakt) else str(trakt)

			if not title is None: parameters['title'] = title
			if not season is None: parameters['season'] = int(season)
			if not episode is None: parameters['episode'] = int(episode)
			if not pack is None: parameters['pack'] = pack

			if not query is None: parameters['query'] = query
			if not keyword is None: parameters['keyword'] = keyword
			if not release is None: parameters['release'] = release
			if not status is None: parameters['status'] = status
			if not year is None: parameters['year'] = year
			if not date is None: parameters['date'] = date
			if not duration is None: parameters['duration'] = duration
			if not genre is None: parameters['genre'] = genre
			if not language is None: parameters['language'] = language
			if not country is None: parameters['country'] = country
			if not certificate is None: parameters['certificate'] = certificate
			if not company is None: parameters['company'] = company
			if not studio is None: parameters['studio'] = studio
			if not network is None: parameters['network'] = network
			if not award is None: parameters['award'] = award
			if not gender is None: parameters['gender'] = gender
			if not ranking is None: parameters['ranking'] = ranking
			if not rating is None: parameters['rating'] = rating
			if not votes is None: parameters['votes'] = votes

			if not filter is None: parameters['filter'] = filter
			if not sort is None: parameters['sort'] = sort
			if not order is None: parameters['order'] = order
			if not page is None: parameters['page'] = page
			if not limit is None: parameters['limit'] = limit
			if not offset is None: parameters['offset'] = offset

			if not provider is None: parameters['provider'] = provider
			if not more is None: parameters['more'] = more

			if not search is None: parameters['search'] = search
			if not progress is None: parameters['progress'] = progress

			if not detail is None: parameters['detail'] = detail
			if not quick is None: parameters['quick'] = quick
			if not refresh is None: parameters['refresh'] = refresh

			if not submenu is None: parameters['submenu'] = submenu
			if not special is None: parameters['special'] = special

			# For next pages (more), so that the search/progress type is maintained during paging.
			if not search is None: parameters['search'] = search
			if not progress is None: parameters['progress'] = progress

			if items is None: items = []
			parametersBase = Tools.copy(parameters)

			custom = {
				'filter' : bool(filter),
				'sort' : bool(sort),
				'order' : bool(order),
				'page' : bool(page),
				'limit' : bool(limit),
			}

			hierarchical = Media.isEpisode(media) and not content == MetaManager.ContentEpisode
			if filter is None: filter = {}
			if detail is None: detail = True
			if more is True: more = None # Do not force a More item if there are no more titles available.
			next = None
			error = None

			if content == MetaManager.ContentQuick: data = self._quick(**parameters)
			elif content == MetaManager.ContentProgress: data = self._progress(**parameters)
			elif content == MetaManager.ContentHistory: data = self._history(**parameters)
			elif content == MetaManager.ContentArrival: data = self._arrival(**parameters)
			elif content == MetaManager.ContentDiscover: data = self._discover(**parameters)
			elif content == MetaManager.ContentSearch: data = self._search(**parameters)
			elif content == MetaManager.ContentRandom: data = self._random(**parameters)
			elif content == MetaManager.ContentList: data = self._list(**parameters)
			elif content == MetaManager.ContentPerson: data = self._person(**parameters)
			elif content == MetaManager.ContentSeason: data = self._season(**parameters)
			elif content == MetaManager.ContentEpisode: data = self._episode(**parameters)
			elif content == MetaManager.ContentSet: data = self._set(**parameters)

		except: Logger.error()

		if data and Tools.isDictionary(data):
			items = data.get('items')

			# Only use the internal/automatic values, if the user did not manually pass in the parameter.
			if not data.get('media') is None: media = data.get('media')
			if not data.get('sort') is None: sort = data.get('sort')
			if not data.get('order') is None: order = data.get('order')
			if not limit is False and not data.get('limit') is None: limit = data.get('limit') # Do not use the user's custom value here, since it is already passed in to the API calls, and the provider/results determine which value to use here.
			if not data.get('submenu') is None: submenu = data.get('submenu')
			if not data.get('special') is None: special = data.get('special')
			if not more is False and not data.get('more') is None: more = data.get('more')
			if not data.get('pack') is None: pack = data.get('pack')
			if not data.get('next') is None: next = data.get('next')
			if not data.get('error') is None: error = data.get('error')

			# Pass the parameters on to the next page (More), for various reasons.
			#	1. Pass on "query", otherwise the next page will open up the input dialog again.
			#	2. Pass on "provider", otherwise if a non-default provider was selected fromt he context menu to discover/search, the next page will use the default provider again.
			#	3. Any custom parameters passed in by the user (eg: custom limit for an external widget), otherwise the next page will ignore those custom parameters.
			#	4. Any adjusted page/limit/more/etc, since those might be changed by the discover/search functions, like IMDb not having more than 5 pages (maximum 250 items).
			for i in ['query', 'provider']:
				if i in data: parameters[i] = data.get(i)
			for k, v in custom.items():
				if v and k in data: parameters[k] = data.get(k)

			filters = data.get('filter')
			if filters:
				filters = Tools.copy(filters)
				if Tools.isArray(filters): filter = [Tools.update(i, filter, none = False) for i in filters]
				else: filter = Tools.update(filters, filter, none = False)
			if Tools.isArray(filter):
				for f in filter:
					if not MetaTools.FilterDuplicate in f:
						f[MetaTools.FilterDuplicate] = True
			else:
				if not MetaTools.FilterDuplicate in filter:
					filter[MetaTools.FilterDuplicate] = True

			# For some weird reason, if we have a "filter" parameter in the plugin://... URL added to xbmcplugin.addDirectoryItems(...), the "filter" parameter gets removed from the URL.
			# That means if we allow the user to pass in custom filters and create a next page item (more), we cannot add the parameter to the URL to also apply those filters for the next page(s).
			# It seems that Kodi removes this parameter. Not sure why. Maybe Kodi uses its own internal "filter" parameter, probably in the left-hand Kodi menu that allows the user to add custom filters for any Kodi menu.
			# However, if we change the name of the parameter (eg: plural "filters"), the parameter is kept.
			# This only seems to be occuring in xbmcplugin.addDirectoryItems(...). If the "filter" parameter is hardcoded in the plugin URL and executed, it is still allowed.
			# Although using "filter" works when calling the plugin URL directly, once the menu loaded, the back button does not work anymore, and only reloads the content of the plugin URL.
			# If we either "optimize" the plugin URL (parameters are base64-encoded), or we use a different parameter name (eg "filters"), then the back navigation works again.
			filters = parameters.get('filter')
			if filters:
				parameters['filters'] = filters
				try: del parameters['filter']
				except: pass

		# Create a copy, since the parameters are adjusted in _process() for More.
		parametersLoad = Tools.copy(parameters)

		# Allow different filters for before and after the manual paging.
		if Tools.isArray(filter):
			filterBefore = filter[0] or {}
			filterAfter = filter[1] or {}
		else:
			filterBefore = filter or {}
			filterAfter = filter or {}

		if Tools.isArray(sort):
			sortBefore = sort[0] or None
			sortAfter = sort[1] or None
		else:
			sortBefore = sort or None
			sortAfter = sort or None

		if Tools.isArray(order):
			orderBefore = order[0] or None
			orderAfter = order[1] or None
		else:
			orderBefore = order or None
			orderAfter = order or None

		if items:
			if not media == Media.List and not media == Media.Person:
				# Do not do for seasons and episodes, since detailed metadata was already retrieved in _season() and _episode().
				if not content == MetaManager.ContentSeason and not content == MetaManager.ContentEpisode:
					# Sort and page before the detail metadata is retrieved.
					if (more is True or (Tools.isInteger(more) and more > 0)) and detail:
						# Do not allow unknown values during filtering for Progress/Arrivals items.
						# Otherwise filtering by eg Anime niche/genre will include all items without a genre, which will only be removed during the 2nd _process() call.
						# All attributes for filtering/sorting should already be set by _metadataSmart(), and those without these attributes are not-yet-cached items down the list.
						unknown = None
						if content == MetaManager.ContentProgress or content == MetaManager.ContentArrival: unknown = False

						full = len(items) == more

						# The MPAA certificate is mostly only available from the detailed metadata.
						if Media.isKid(niche) or Media.isTeen(niche): self.metadata(items = items, pack = pack, quick = -self.limit(media = media, content = content), special = special, hierarchical = hierarchical)

						items = self._process(media = media, items = items, parameters = parameters, filter = filterBefore, sort = sortBefore, order = orderBefore, page = page, limit = limit, more = more, unknown = unknown)

						if filterBefore.get(MetaTools.FilterDuplicate): filterAfter[MetaTools.FilterDuplicate] = False # No need to do again, unlike the other filters which might get new values from the detailed metadata.
						page = False # Already paged, do not do it again.
						if full: more = len(items) # Update smart paging, eg: Anime filtered Progress menu.

					# Do not pass the 'refresh' parameter here, since it should only be used for the list data.
					if detail: items = self.metadata(items = items, pack = pack, quick = quick, next = next, special = special, hierarchical = hierarchical)

			# Also do for lists menu paging.
			items = self._process(media = media, items = items, parameters = parameters, filter = filterAfter, sort = sortAfter, order = orderAfter, page = page, limit = limit, more = more)

		parametersMore = parameters if parameters.get('more') else None
		try: del parametersMore['more']
		except: pass

		return {
			'items'	: items,
			'base'	: parametersBase,
			'load'	: parametersLoad,
			'more'	: parametersMore,
			'error'	: error,
		}

	##############################################################################
	# DISCOVER
	##############################################################################

	def discover(self, media = None, niche = None, keyword = None, release = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentDiscover, media = media, niche = niche, keyword = keyword, release = release, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _discover(self, media = None, niche = None, keyword = None, release = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, refresh = None, **parameters):
		try:
			mediad = media
			if Media.isMixed(media): media = None

			processor = self._processor(media = media, niche = niche, release = release, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentDiscover))
			niche = processor.get('niche')
			if filter is None: filter = processor.get('filter')
			if sort is None: sort = processor.get('sort')
			if order is None: order = processor.get('order')
			if page is None: page = processor.get('page')
			if limit is None: limit = processor.get('limit')

			if provider is True or not provider: providers = self.provider(content = MetaManager.ContentDiscover, media = media, niche = niche, release = release, genre = genre, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking)
			else: providers = provider if Tools.isArray(provider) else [provider]

			for provider in providers:
				if provider == MetaTools.ProviderTrakt:
					# Otherwise paging continues to the next month/year.
					if date:
						traktPage = None
						traktLimit = None
					else:
						traktPage = page
						traktLimit = limit

					data = self._cache('cacheLong', refresh, MetaTrakt.instance().discover, media = media, niche = niche, keyword = keyword, release = release, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, rating = rating, votes = votes, page = traktPage, limit = traktLimit, internal = True)
					items = data.get('items')

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					if items:
						# Sometimes Trakt returns less items than the requested limit, or some items are locally filtered out. Return the initial count to add a next page to the menu (eg: if 49 items are returned, but 50 were requested).
						more = data.get('more')
						if more is False and date: more = len(items) # Since page/limit is set to None above.

						page = traktPage
						limit = traktLimit

						if release: limit = False # Do not limit the items in content(), since releases uses the Trakt calendar and does not return a fixed page size/limit. Eg: the page (aka one month of releases) can have 100+ titles.

				elif provider == MetaTools.ProviderImdb:
					items = self._cache('cacheLong', refresh, MetaImdb.instance().discover, media = media, niche = niche, keyword = keyword, release = release, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = award, rating = rating, votes = votes)

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					if items:
						more = MetaImdb.LimitDiscover

						# Future releases mostly only have a year, but not a premiered date.
						# Even when retrieving detailed metadata, most of the future titles on IMDb are not even listed on Trakt/TMDb yet.
						if release == MetaProvider.ReleaseFuture:
							try: del filter[MetaTools.FilterTime]
							except: pass

				if items:
					items = self._processAggregate(media = media, items = items)
					if Media.isSeason(mediad) or Media.isEpisode(mediad): mediad = Media.Show

					return {
						'items'		: items,

						'filter'	: filter,
						'sort'		: sort,
						'order'		: order,
						'page'		: page,
						'limit'		: limit,

						'provider'	: provider,
						'more'		: more,

						# Never retrieve pack data for discover menus.
						# All menus are either show menus, or season/episode menus emulated as show menus, but any both cases we do not want to retrieve pack data.
						'pack'		: False,
					}
		except: Logger.error()
		return None

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media = None, niche = None, search = None, query = None, keyword = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentSearch, media = media, niche = niche, search = search, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking, rating = rating, votes = votes, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _search(self, media = None, niche = None, search = None, query = None, keyword = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, refresh = None, **parameters):
		try:
			if media == Media.Set or search == Media.Set: return self._set(set = MetaManager.ContentSearch, media = media, niche = niche, query = query, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, refresh = refresh, **parameters)
			elif media == Media.List or search == Media.List: return self._list(list = MetaManager.ContentSearch, media = media, niche = niche, query = query, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, refresh = refresh, **parameters)
			elif media == Media.Person or search == Media.Person: return self._person(person = MetaManager.ContentSearch, media = media, niche = niche, query = query, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, refresh = refresh, **parameters)

			mediad = media
			if Media.isMixed(media): media = None

			processor = self._processor(media = media, niche = niche, year = year, date = date, genre = genre, language = language, country = country, certificate = certificate, award = award, ranking = ranking, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentSearch))
			niche = processor.get('niche')
			if filter is None: filter = processor.get('filter')
			if sort is None: sort = processor.get('sort')
			if order is None: order = processor.get('order')
			if page is None: page = processor.get('page')
			if limit is None: limit = processor.get('limit')
			more = None

			if provider is True or not provider: providers = self.provider(content = MetaManager.ContentSearch, media = media, niche = niche, genre = genre, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking)
			else: providers = provider if Tools.isArray(provider) else [provider]

			for provider in providers:
				if provider == MetaTools.ProviderTrakt:
					#gaiaremove
					# UPDATE (2025-12):
					# Trakt does not seem to support paging for the search endpoint anymore, and caps the limit at 50.
					# If this is fixed in the future, revert back to the old code.
					# More info under MetaTrakt.search().
					'''
					data = self._cache('cacheLong', refresh, MetaTrakt.instance().search, media = media, niche = niche, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, rating = rating, votes = votes, page = page, limit = limit, internal = True)
					items = data.get('items')

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					# Sometimes Trakt returns less items than the requested limit, or some items are locally filtered out. Return the initial count to add a next page to the menu (eg: if 49 items are returned, but 50 were requested).
					if items: more = data.get('more')
					'''
					data = self._cache('cacheLong', refresh, MetaTrakt.instance().search, media = media, niche = niche, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, rating = rating, votes = votes, page = 1, limit = MetaTrakt.LimitSearch, internal = True)
					items = data.get('items')
					if items: more = MetaTrakt.LimitSearch

				elif provider == MetaTools.ProviderImdb:
					items = self._cache('cacheLong', refresh, MetaImdb.instance().search, media = media, niche = niche, query = query, keyword = keyword, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, group = award, rating = rating, votes = votes)

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					if items: more = MetaImdb.LimitDiscover

				elif provider == MetaTools.ProviderTmdb:
					items = self._cache('cacheLong', refresh, MetaTmdb.instance().search, media = media, query = query, page = page)

					# Only set these values if the call was successful. Otherwise these adjusted parameters might be used by the fallback provider.
					if items:
						more = True
						limit = MetaTmdb.LimitFixed # Also set limit.

				if items:
					items = self._processAggregate(media = media, items = items)
					if Media.isSeason(mediad) or Media.isEpisode(mediad): mediad = Media.Show

					return {
						'items'		: items,

						'filter'	: filter,
						'sort'		: sort,
						'order'		: order,
						'page'		: page,
						'limit'		: limit,

						'search'	: search,
						'query' 	: query, # Add this for next pages.

						'provider'	: provider,
						'more'		: more,

						# Never retrieve pack data for discover menus.
						# All menus are either show menus, or season/episode menus emulated as show menus, but any both cases we do not want to retrieve pack data.
						# This should not happen, since we do not search seasons or episodes, but still add it, just like in discover().
						'pack'		: False,
					}
		except: Logger.error()
		return None

	##############################################################################
	# PROGRESS
	##############################################################################

	def quick(self, media = None, niche = None, detail = None, quick = None, reload = None, refresh = None, **parameters):
		return self.content(content = MetaManager.ContentQuick, media = media, niche = niche, detail = detail, quick = quick, reload = reload, refresh = refresh, **parameters)

	def _quick(self, media = None, niche = None, refresh = None, **parameters):
		try:
			if media is None or Media.isMixed(media):
				data1 = self._quick(media = Media.Show, niche = niche, refresh = refresh, **parameters)
				data2 = self._quick(media = Media.Movie, niche = niche, refresh = refresh, **parameters)
				if not data1: data1 = {}
				if not data2: data2 = {}
				result = data1 or data2
				if result:
					items1 = data1.get('items') or []
					items2 = data2.get('items') or []

					# Progress: 2
					# History: 1
					# Arrival: 1
					# Recommend: 1
					# Random: 0
					result1 = []
					result2 = []
					for i in [0, 1, 3, 5, 7]:
						try: result1.append(items1[i])
						except: pass
						try: result1.append(items2[i])
						except: pass
					for i in [2, 4, 6, 8, 9]:
						try: result2.append(items1[i])
						except: pass
						try: result2.append(items2[i])
						except: pass
					items = result1 + result2
					items = items[:10]

					result.update({
						'limit'		: (data1.get('limit') or 0) + (data2.get('limit') or 0),
						'more'		: (data1.get('more') or 0) + (data2.get('more') or 0),
						'items'		: items,
					})
					return result
				return None

			items = None

			# Try to avoid the cache function execution (refreshing in the background) if we are reloading mixed menus.
			# More info in reload().
			if self.reloadingMixed(): items = self._cacheRetrieve(self._quickAssemble, media = media, niche = niche)

			# Do not use "cacheRefresh", since this will make the quick menu reload if we open an item within the Quick menu and then navigate back.
			if not items: items = self._cache('cacheQuick', refresh, self._quickAssemble, media = media, niche = niche)

			if items:
				return {
					'items'		: items,
					'next'		: MetaManager.Smart,
					'more'		: False,
					'pack'		: False,
				}
		except: Logger.error()
		return None

	def _quickAssemble(self, media = None, niche = None):
		try:
			timer = self._jobTimer()
			result = []
			helper = {}

			def _add(count, items, items2 = None):
				counter = 0

				# Add high rated titles.
				for item in items:
					if not item in result:
						rating = item.get('rating')
						if rating and rating >= 7.0:
							result.append(item)
							counter += 1
							if counter >= count: break

				# Fill up if there are still too few.
				if counter < count:
					for item in items or items2:
						if not item in result:
							result.append(item)
							counter += 1
							if counter >= count: break

			# The same show can appear multiple times with different episode numbers.
			# Eg: the show is added from "itemsProgress" and from "itemsArrival" or in rare cases "itemsRandom".
			# Filter out titles that are already in "result".
			def _duplicate(items):
				# serie=True: some items are shows, while others are episodes, and both should be treated as the same media.
				return [i for i in items if not self.mTools.filterContains(items = result, item = i, serie = True, helper = helper)]

			from lib.modules.playback import Playback
			playback = Playback.instance()

			countProgress = 3
			countHistory = 2
			countArrival = 2
			countRecommend = 2
			countRandom = 1
			countTotal = countProgress + countHistory + countArrival + countRecommend + countRandom

			current = Time.timestamp()
			month = 2628000 # 1 month.
			start = Playback.percentStart()
			end = Playback.percentEnd()
			total = 0
			sleepy = self.mTools.settingsSleepyDuration() # Do not show fully watched itemsa if the user disabled the sleepy duration.

			# Prevent smart-reloads, since they already happen if the individual progress/arrivals menus are refreshed.
			# Refreshing the quick menu, either from reload() or when the user opens the menu, should never make smart-reloads.
			# Do not use self.mReloadBusy, since at the end of this function we change the value back to True, and do not want to do that to self.mReloadBusy. More info under reload().
			self.mReloadQuick = True

			itemsProgress = self.progress(media = media, niche = niche, pack = False, detail = False, limit = 150, internal = True) # Internal, in order not to use the outer cache data from content().
			if itemsProgress:
				itemsProgress = itemsProgress.get('items')
				if itemsProgress: total += len(itemsProgress)

			itemsArrival = self.arrival(media = media, niche = niche, pack = False, detail = False, limit = 150, internal = True) # Internal, in order not to use the outer cache data from content().
			if itemsArrival:
				itemsArrival = itemsArrival.get('items')
				if itemsArrival: total += len(itemsArrival)

			itemsRecommend = self.list(media = media, niche = niche, list = MetaTools.ListRecommendation, provider = MetaTools.ProviderTrakt, detail = False, limit = 100, internal = True)
			if itemsRecommend:
				itemsRecommend = itemsRecommend.get('items')
				if itemsRecommend: total += len(itemsRecommend)

			itemsRandom = self.random(media = media, niche = niche, detail = False, limit = 100, internal = True)
			if itemsRandom:
				itemsRandom = itemsRandom.get('items')
				if itemsRandom: total += len(itemsRandom)

			if itemsProgress:
				if Media.isSerie(media):
					# Busy shows recently watched.
					count = 0
					for item in itemsProgress:
						time = self.mTools.time(metadata = item, type = MetaTools.TimeWatched, estimate = False, fallback = False)

						# Do not add fully watched shows after some time.
						add = True
						if time:
							smart = item.get(MetaManager.Smart)
							if smart and not smart.get('next'):
								play = smart.get('play')
								if play and int(play) == play: # Fully watched without rewatching.
									if (current - time) > sleepy: add = False

						if not time: time = self.mTools.time(metadata = item, type = MetaTools.TimePaused, estimate = False, fallback = False) # Also allow when an episode is still in rpogress without an episode being fully watched.
						if add and time and (current - time) <= month:
							result.append(item)
							count += 1
							if count >= countProgress: break

					# Fill up if there are not recently watched shows.
					count = len(result)
					if count < countProgress:
						for item in itemsProgress:
							if not item in result:
								result.append(item)
								count += 1
								if count >= countProgress: break

					# Newley released episode for a show not watched in a while.
					count = 0
					for item in itemsProgress:
						if not item in result:
							smart = item.get(MetaManager.Smart)
							if smart:
								released = []

								release = Tools.get(smart, 'pack', 'time', 'season')
								if release:
									for i in release:
										if i and i[0]:
											seconds = current - i[0]
											if seconds >= 0: released.append(seconds)

								# Also add the next episodes time, but only if SxxE01.
								# Should be the same as the one from the pack, but this one can be newer if the pack metadata is outdated.
								next = Tools.get(smart, 'next', 'time')
								if next and item.get('episode') == 1:
									seconds = current - next
									if seconds >= 0: released.append(seconds)

								if released:
									released = min(released)
									if released < month:
										result.append(item)
										count += 1
										if count >= countHistory: break

				else:
					# Unfinished movies.
					count = 0
					for item in itemsProgress:
						progress = item.get('progress')
						if progress and progress >= start and progress <= end:
							result.append(item)
							count += 1
							if count >= countProgress: break

					# Finished movies.
					count = 0
					for item in itemsProgress:
						if not item in result:
							playcount = item.get('playcount')
							if playcount:
								time = self.mTools.time(metadata = item, type = MetaTools.TimeWatched, estimate = False, fallback = False)
								if time and (current - time) <= sleepy:
									result.append(item)
									count += 1
									if count >= countHistory: break

				# Fill up if there are still too few movies or shows.
				count = len(result)
				if count < (countProgress + countHistory):
					for item in itemsProgress:
						if not item in result:
							result.append(item)
							count += 1
							if count >= (countProgress + countHistory): break

			# New arrivals.
			if itemsArrival:
				itemsArrival = _duplicate(itemsArrival)
				items = Tools.listShuffle(itemsArrival[:20]) + itemsArrival[20:]
				_add(countArrival, items, itemsArrival)

			# Trakt recommendations.
			if itemsRecommend:
				# Trakt returns watched/rated items. Trakt can only filter out by watchlist/collection.
				# Remove already watched items.
				itemsRecommend = [i for i in itemsRecommend if not Tools.get(playback.history(media = media, imdb = i.get('imdb'), tmdb = i.get('tmdb'), tvdb = i.get('tvdb'), trakt = i.get('trakt'), quick = True), 'count', 'total')]
				if itemsRecommend:
					itemsRecommend = _duplicate(itemsRecommend)
					itemsRecommend = Tools.listShuffle(itemsRecommend)
					_add(countRecommend, itemsRecommend)

			# Random titles.
			if itemsRandom:
				itemsRandom = _duplicate(itemsRandom)
				itemsRandom = Tools.listShuffle(itemsRandom)
				_add(countRandom, itemsRandom)

			# Fill up if there are still too few.
			items = []
			if itemsArrival: items += itemsArrival
			if itemsRecommend: items += itemsRecommend
			if itemsRandom: items += itemsRandom
			if items:
				items = _duplicate(items)
				count = countTotal - len(result)
				if count > 0: _add(count, items)

			result = result[:countTotal]

			if Media.isSerie(media):
				for item in result:
					if item.get('season') is None: item['season'] = 1
					if item.get('episode') is None: item['episode'] = 1

			Logger.log('SMART REFRESH (%s Quick | %dms): Total: %d | Retrieved: %d' % (media.capitalize(), timer.elapsed(milliseconds = True), len(result), total))
			return result
		except: Logger.error()
		finally: self.mReloadQuick = False
		return None

	##############################################################################
	# RELEASE
	##############################################################################

	@classmethod
	def release(self, media = None, metadata = None, extract = None, refresh = None):
		# There is a small problem with refreshing metadata from MetaCache.
		# If a new season is released, but the locally cached season and pack metadata is outdated (does not contain the new season yet), the new season will not show up in the menus until the metadata is refreshed.
		# Since metadata is now only refreshed every 2 months, it can take a long time until the metadata is updated and contains the new season.
		# Eg: Last Week Tonight with John Oliver S12E01 was just released.
		# Eg: The show is listed under the Progress menu and marked in bold, since the smart menu knows about the new S12E01 release.
		# Eg: When opening the episode submenu or the season menu, S12 is not listed at all, since the cached season metadata only goes up to S11 and was not recently refreshed.
		# To recude this happening, we generate a large list of more accurate release dates:
		#	1. When smart-loading Progress, the dates from the last season in the pack is used. This will only work if the pack metadata is up-to-date and the smart item was recently processed to include the pack dates.
		#	2. When smart-loading Arrivals, the dates for all recent season releases are used. This only works for shows that are in Arrivals and smaller less-known shows might not be included.
		# In MetaCache._timeExtract(), when retrieving metadata from the local cache, this list of dates is used to determine which titles should be refreshed more often, instead of relying on the possibly outdated dates inside the cached metadata.
		# This should allow more frequent metadata refreshes for most popular shows and shows in the user's progress.
		# For any other titles that are not refreshed with this date list:
		#	1. Either stick to the outdated metadata and wait until it is refreshed naturally, which can take a long time, since the new refresh period is 2 months.
		#	2. Or the user manually refreshes the metadata from the context menu -> Refresh -> Refresh Menu/Season metadata.

		# Title metadata is only refreshed in MetaCache every 2 months by default.
		# The metadata might therefore be outdated, especially for new-ish releases, and has to be refreshed more frequently to get the latest metadata.
		# Once titles are older than 1-2 years, their metadata will change little (except their rating/votes), and only refreshing on the 2-month-interval is sufficient.
		#
		# Incomplete metadata causes the following problems:
		#	1.	Some metadata attributes might be missing or incomplete, such as aliases, cast, images, etc.
		#		This metadata is non-critical and should not cause any problems if outdated.
		#		Incomplete metadata is rare and mostly prevalent around the release dates.
		#		So refreshing often around the release dates should solve this.
		#	2.	Some metadata attributes might be available, but their values are outdated.
		#		The rating/votes might be low, especially close to the premiere date, since most people have not cast their vote yet.
		#		This metadata is only semi-critical and should not cause too many problems.
		#		The ratings/votes are used for global and local sorting in MetaTools.sort(), and if outdated might make them move lower down the Arrivals menu.
		#		However, the global sorting takes new releases with less votes into account, so even if outdated, the implications should be limited.
		#	3.	Some metadata dates might be unavailable, causing critical problems.
		#		MetaCache and MetaManager.metadataSmart() use the release dates to determine if metadata should be refreshed more frequently.
		#		If some of these dates are missing, the metadata will not be refreshed early enough and titles might not be listed on the first page of Progress/Arrivals shortly after such a date.
		#
		# These missing dates cause problems in 2 menus:
		#	1.	Movie Arrivals:
		#		This menu is created based on the digital/physical release dates of movies, since we want proper 4K releases and not CAM/SCR releases.
		#			Outdated metadata might not have digital/physical dates yet, and will therefore not refresh early, and only refresh around the known earlier premiere/theatrical dates.
		#			Example: A Complete Unknown (2024)
		#				 The movie premiered on 2024-11-20/2024-12-10 and theatrically on 2024-12-25 in the US, with many countries only getting their theatrical release in late January/February 2025.
		#				 The digital release was on 2025-02-25 in the US, but these dates were only added to Trakt/TMDb a few days before the actual digital release. And at this point there was still no physical date yet.
		#				 So even if the metadata was refreshed a few days prior, it would still not contain the newly added digital date.
		#				 The movie was therefore not listed under Arrivals a few days after its digital release. It might have only shown up weeks later, or when the physical release comes out.
		#		The digital/physical dates are not available from Trakt/TMDb/IMDb when assembling the Arrivals smart list, and all of them only return the premiere dates.
		#			Even if we filter by date and online/watch availability on TMDb/IMDb, or on Trakt (using the "watchnow" parameter), the date filtering is applied to the premiere date, not the digital/physical date.
		#			So even if we use the end-range of the date request parameter as an estimate of the digital/physical dates, the range/estimate is actually done on the earlier premiere date.
		#			Example: A Complete Unknown (2024)
		#				 On IMDb with the online-availability parameter, this movie is only listed in the date range [2025-11-01,2025-11-31], since that is when the premiere took place.
		#				 So even if we use the "2025-11-31" date parameter as an digital date estimate, it will still be far off the actual digital release on 2025-02-25.
		#		The only exception to this is the Trakt DVD Calendar, which returns an outer attribute which is the physical release date.
		#			But Trakt does not have a Digital Calendar. We can filter the All Movies Calendar using the "watchnow" parameter, but this will still return the premiere dates.
		#			Physical dates are also typically way later than the digital dates, and many do not have a physical release at all (eg Netflix Originals).
		#			All other providers, and other Trakt calendars, only return the premiere date.
		#			So the only way to get the updated metadata is to wait for the standard 2-month refresh interval, hope the physical date is soon and listed on Trakt to trigger a refresh, or let the user manually refresh the metadata from the context menu.
		#			If the metadata is only refreshed weeks after the digital/physical release, this should not be a huge problem for popular movies getting listed on the first page of Arrivals.
		#			Popular movies will remain in Arrivals for way longer, since they have a high rating and many votes. So even if they only get added to Arrivals days/weeks later, the user will still see it at some later point.
		#			However, less popular titles with outdated dates, might never make it to the first few pages of Arrivals, since they have a low rating/votes.
		#			They should be shown at least for a few days at the top of Arrivals, purely based on their release date. But because the metadata is outdated, their digital/physical date will have passed and the votes will not be enough to move it to the Arrival top.
		#		Movie Progress does not have this problem. Once a movie is in this menu, because it was or is being watched, there is no urgency in refreshing the metadata.
		#	2.	Show Progress:
		#		Shows only have one date, the premiere date, so once we have that date, we can refresh accordingly.
		#			Unlike movies, Show Arrivals do not have the outdated date issue.
		#			All shows listed under Arrivals have their show premiere dates and the latest season premiere dates, which is enough for refreshing.
		#			Items listed under the Show Arrivals are show menu entries, which do not require frequent refreshes if a new season/episode is released.
		#		On the other hand, the problem with shows is in the Progress menu.
		#			Season/episode/pack metadata can have missing seasons/episodes because they were not added yet before the last refresh.
		#			This can make a new season/episode from the user's progress not show up in the Progress submenu.
		#			Example: Last Week Tonight with John Oliver
		#				S12 premiered on 2025-02-17. At this point, the season, episode, and pack metadata were still outdated and not containing the latest season/episode.
		#				When opening the episode-submenu under Progress, the show only listed episodes up to S11. And when opening the show's season menu, S12 was also not listed there until the metadata was refreshed.
		#				However, S12E01 was listed in the show Arrivals menu. This date can be used to refresh the season/episode/pack metadata earlier.
		#
		# Shows also make things more complex due to the different ways in which episode can be released:
		#	1.	All episodes of a season have the same release date.
		#		The metadata for all episodes will be available on the season premiere.
		#		The metadata does not have to be refreshed that often, because all episode metadata is available from day one.
		#		Only refresh occasionally to get the updated ratings/votes.
		#	2.	Episodes are released on different days, typically one episode per week, with all metadata available from day one.
		#		In most cases, but not always, the metadata of all episodes is available on the season premiere, even if episodes only air at a later stage.
		#		The metadata does not have to be refreshed that often, because most metadata is complete.
		#		Only refresh occasionally to get the updated ratings/votes.
		#	3.	Episodes are released on different days, typically one episode per week, but not all metadata is available from day one.
		#		The metadata of only a few future episodes, typically 2-4 episodes, is released ahead of time.
		#		For instance, if S02E03 airs today, the metadata for S02E04-S02E06 might already be available, but not anything for S02E07 or later.
		#		But often the future episode has missing metadata. Beside the ratings/votes, they often do not have titles and thumbnails, and are listed as eg "Episode #4".
		#		This metadata has to be refreshed more often than the previous season types, since we need to get the updated metadata for future episodes.
		#		However, it probably does not require a weekly refresh, since at least the episode numbers for the next few weeks are already available.
		#	4.	Episodes are released on different days, typically one episode per week, but every episode's metadata is only added once aired.
		#		This is typically for anime, eg One Piece, where a new episode is released every 1-2 weeks, but the metadata is sometimes only added to Trakt/TMDb/TVDb a few days before it airs.
		#		This metadata has to be refreshed frequently, preferably once a week, so that the episode is available under Progress every week the user wants to watch the next episode.
		#		But anime shows often have 100s of episodes per season. So refreshing the entire season's episode metadata every week requires a lot of API requests.
		#		The pack data might require fewer API requests, but anime shows might have 1000s of episodes for the show. So refreshing packs every week might require a lot of local processing to match thousands of titles in MetaPack.
		#		In the worst case, if we do not refresh the metadata every week, most of the time the next episode metadata will be available more than a week beforehand.
		#		Or the user just has to wait a week or two until the metadata is refreshed naturally and the new episode becomes available.
		#	5.	Episodes are released on different days, typically one episode per week, but there are mid-season finales.
		#		These seasons can release all episode at once, even those after the mid-season finale.
		#		But more typically all episodes until the mid-season finale are released, all at once or once a week, and the rest of the metadata for the 2nd half is only released months later.
		#		This creates a problem, since the gap between consecutive episodes might not be 1-2 weeks, but rather 6-12+ months.
		#		Hence, the metadata might not be refreshed very quickly, so when the mid-season premiere airs, it might not immediately be listed at the top of Progress.
		#		We could just refresh the metadata on a weekly basis, but this would mean a lot of requests and processing for months where the metadata does not change.
		#		A lot of anime does this. Most anime has a single/absolute season which is divided into arcs/stories/adventures/voyage which are then divided into mid-season finales.
		#		Trakt/TMDb then groups these arcs into actual seasons, but there can be huge discrepancies where the premieres/finales are placed between Trakt/TMDb and TVDb.
		#		These anime shows also often add a mid-season finale, but when the next episode is released months later, it is not added to the previous season (as a new mid-season premiere), but rather a completely new season is created.
		#		Example: One Piece S21 finale and S22 mid-season finale.
		#		In the worst case, episodes are not released weekly, but in arbitrary intervals, and the last episode is not marked as a finale. Then we do not know when a season has actually ended and how often we should refresh.
		# Different metadata of shows therefore have to be refreshed as follows:
		#	1.	Shows: Only refresh frequently around the show premiere. Refresh occasionally around the season premieres as well to get more updated ratings/votes.
		#	2.	Seasons: Refresh frequently around every season premiere. Refreshing around new episode releases is not necessary, since the season metadata will not change a lot.
		#	3.	Episodes: Refresh frequently around every season premiere. Depending on the show type from above, also refresh this occasionally or even weekly if a new episode is released.
		#	4.	Packs: Refresh frequently around every season premiere. Depending on the show type from above, also refresh this occasionally or even weekly if a new episode is released. Weekly released episode numbers are needed for binging and other features.
		#
		# To solve the outdated metadata issue, because of the missing/outdated dates:
		# https://www.reddit.com/r/torrents/comments/27ceeq/rss_scene_release_feed/
		# https://www.digitalworldz.co.uk/threads/good-site-for-sceen-releases.199667/
		# https://en.wikipedia.org/wiki/Nuke_(warez)
		#	1.	Movies:
		#		Retrieve the digital/physical release dates from another external source.
		#			None of Trakt/TMDb/IMDb return these dates without requesting the detailed metadata for each individual movie. The only exception is the Trakt DVD Calendar which does return the physical, but not the digital, release date.
		#			Hence, retrieve these dates from other sites that have those dates.
		#			We can also use various scence release logs to check if some title has a 4K release already. But these scene logs do not have an API and their RSS feed typically only shows the releases of the past day.
		#			This is not a perfect solution, since many unpopular movies will not be listed on any of these sites. But at least the more popular ones should be listed and therefore refreshed frequently.
		#			Update(2025-11): Trakt has now added a streaming/digitial calendar that returns the digitial release date without having to request detailed metadata.
		#	2.	Shows:
		#		Technically we do not need additional dates for the Progress menu.
		#			All show/season premieres from the Arrivals smart list should be enough to refresh the various show metadata.
		#			However, if the user has a less popular show in his progress, that show might never get listed under Arrivals, because it has too few votes. The latest dates for refreshing will therefore not be available through Arrivals.
		#		Additionally, many shows have mid-season finales where the next mid-season premiere might only be released months later.
		#			Especially anime does this often, where they have a mid-season finale that only continues 6-12 months later.
		#			Example: One Piece
		#				S21 ended with a mid-season finale. But when the new episode came out, a new season S22 was started.
		#				Currently S22 has a mid-season finale at S22E1122 (2024-10-13) and the next unaired episode S22E1123 (2025-04-06) will probably be added as S23 once released.
		#			If only the show/season premieres are known, the season/episode/pack metadata will probably not be refreshed early, and the mid-season premiere might not immediately be moved to the top of Progress once aired.
		#			Plus the shows that air weekly with episodes only added on a weekly basis, might have outdated metadata and therefore not always have the latest episodes.
		#		Hence, also use the newest aired episode dates to more frequently refresh at least the episode and pack metadata.
		#			The Arrivals menu only has show and season premieres, not individual episodes.
		#			To get individual episodes, use the Trakt My Shows Calendar, which returns the latest episode number and airing date.
		#			This should not be too heavy, since that Trakt Calendar only returns the new episodes for the user's shows, so it should not be that many.

		if self == MetaManager.instance():
			Logger.log('Releases should never be done with MetaManager.instance().', type = Logger.TypeFatal)
			return False

		items = None

		if not media and metadata: media = metadata.get('media')

		mediad = media
		if Media.isSerie(media) or Media.isPack(media): mediad = Media.Show
		elif Media.isSet(media): mediad = Media.Movie

		if mediad == Media.Movie or mediad == Media.Show:
			# Storing the items in a MetaManager class variable has no performance improvement over just using Memory.
			# Cache for a maximum of 48h in memory. In case the user does not restart the device for a long time, so that a refresh is forced at least every other day.
			timeout = Cache.TimeoutDay1
			id = self._releaseId(media = mediad)
			if not refresh: items = Memory.get(id = id, local = True, kodi = True, timeout = timeout * 2)

			if not items:
				manager = MetaManager(mode = [MetaManager.ModeAccelerate, MetaManager.ModeUndelayed])
				manager.mReleaseMedia = mediad
				if refresh:
					items = manager._cacheTimeout(timeout, refresh, manager._releaseAssemble, media = mediad)
				else:
					# Never assemble if refreshing was not explicitly requested.
					# Otherwise when the Progress/Arrival menus are created, retrieving metadata from MetaCache will call this function, which in turn will call progress()/arrival() causing a deadlock.
					items = manager._cacheRetrieve(manager._releaseAssemble, media = mediad)
				Memory.set(id = id, value = items, local = True, kodi = True)

			#manager.mReleaseMedia = None # Do not reset, since the above cache call might still be busy.

			if metadata:
				id, item = self._releaseLookup(media = media, metadata = metadata, items = items)
				if extract: item = self._releaseExtract(media = media, metadata = metadata, item = item, id = id) # Do this, even if the item cannot be found in _releaseLookup().
				return item

		return items

	@classmethod
	def _releaseLookup(self, media, metadata, items):
		try:
			ids = None
			result = None
			if items:
				collection = Media.isSet(metadata.get('media'))
				if 0:
					id = Tools.get(metadata, 'id', MetaTools.ProviderTmdb)
					if id:
						lookup = items['collection'].get(id)
						if lookup: result = lookup

				if not result:
					if collection: parts = metadata.get('part')
					else: parts = [metadata]
					if parts:
						for part in parts:
							id = part.get('id')
							if id:
								for provider in (MetaTools.ProviderTrakt, MetaTools.ProviderImdb, MetaTools.ProviderTmdb, MetaTools.ProviderTvdb):
									idProvider = id.get(provider)
									if idProvider:
										lookup = items[provider].get(idProvider)
										if lookup:
											ids = id
											result = lookup
											break # Only break once found, since the lookup sub-tables of Trakt/IMDb/TMDb do not always contain the same titles.
							if result: break
				if result:
					result = items['data'].get(str(result)) # The lookup ID is an integer, but the data keys are strings, so cast to string.
					if result:
						result = self._releaseReduce(item = result)
						if collection:
							# Replace the IDs if it is in the release dictionary, which has more IDs.
							# Otherwise keep to the set metadata part IDs, which only has the TMDb ID.
							ids2 = result.get('id')
							if ids2: ids = ids2

			return ids, result
		except: Logger.error()
		return None, None

	@classmethod
	def _releaseExtract(self, media, metadata, item, id):
		try:
			def _extract(metadata, pack = None, lookup = None, all = False, minimum = None, maximum = None):
				if metadata:
					values = []
					if minimum is None and all: minimum = True
					if maximum is None and all: maximum = True

					if pack:
						value = pack.time(item = metadata)
						if value: values.extend(value) if Tools.isArray(value) else values.append(value)

						if minimum:
							value = pack.timeMinimumStandard()
							if value: values.append(value)
						if maximum:
							value = pack.timeMaximumStandard()
							if value: values.append(value)
					else:
						if Tools.isArray(metadata): parts = metadata
						else: parts = metadata.get('seasons') or metadata.get('episodes') or metadata.get('part') # Seasons, episodes, and sets metadata.

						if parts:
							for i in parts:
								if i:
									value = _extract(metadata = i, lookup = lookup, all = all, minimum = minimum, maximum = maximum)
									if value: values.extend(value)
						else:
							time = metadata.get('time')
							if time and Tools.isDictionary(time):
								for i in lookup:
									value = time.get(i)
									if value:
										values.append(value)
										if not all: break

							if not values and lookup and MetaTools.TimePremiere in lookup:
								value = metadata.get('premiered') or metadata.get('aired')
								if value: values.append(Time.timestamp(fixedTime = value, format = Time.FormatDate))

							if minimum or maximum:
								packed = metadata.get('packed')
								if packed:
									packed = packed.get('time')
									if packed:
										if minimum:
											value = packed if Tools.isInteger(packed) else packed.get(MetaPack.ValueMinimum)
											if value: values.append(value)
										if maximum:
											value = packed if Tools.isInteger(packed) else packed.get(MetaPack.ValueMaximum)
											if value: values.append(value)

					if values: return values
				return None

			current = Time.timestamp()
			lookup = (MetaTools.TimePremiere, MetaTools.TimeTelevision, MetaTools.TimeDigital, MetaTools.TimePhysical)
			counts = [0, 0, 0, 0]
			times = [[], [], [], []]
			origin = None
			count = None
			period = None
			pack = None
			previous = None
			closest = None
			last = None
			special = None
			typeSeason = None
			typeEpisode = None
			number = None
			numberSeason = None
			numberEpisode = None

			# For season/episode/pack metadata, this is the status of the show.
			status = metadata.get('status')

			# Show release interval.
			try: interval = metadata['packed']['interval']
			except: interval = None

			# Legacy, before the media for packs was "show", which is now added as the "content" attribute and the "media" attribute is now "pack".
			# Use the media passed in from MetaCache.
			if not media:
				media = metadata.get('media')
				if not media: # Legacy, before the media was added to the outer season and metadata dicts.
					if metadata.get('seasons'): media = Media.Season
					elif metadata.get('episodes'): media = Media.Episode

			if item:
				# Important to copy here, since the dictionary is edited below.
				# Otherwise when retrieving different metadata (show/season/episode/pack) for the same show, the same global count dictionary is used and updated by all of them.
				count = Tools.copy(item.get('count'))

				origin = item.get('origin')
				previous = item.get('previous')
				closest = item.get('closest')
				last = item.get('last')
				special = item.get('special')

				number = item.get('number') or {}
				numberSeason = number.get('season')
				numberEpisode = number.get('episode')

				# Add the dates from external sources.
				# Only do this for episode metadata if the season matches.
				if not media == Media.Episode or numberSeason == metadata.get('season'):
					values = item.get('time')
					if values:
						for i in range(len(values)):
							value = values[i]
							if value:
								if Tools.isArray(value): times[i].extend(value)
								else: times[i].append(value)

					# If a special is the most recently released episode, its time is used for the closest episode time[2].
					# In such a case, check if time[2] is the same as the special time, and if so, replace it with one of the other times.
					# For other media (shows/seasons/packs), having the special in time[2] is acceptable, since we only care amount the most recent episode, irrespective if it is a special or not.
					if media == Media.Episode and not numberSeason == 0 and special:
						specialTime = special.get('time')
						if specialTime:
							episodeTime = times[2]
							if specialTime in episodeTime:
								if closest: episodeTime.append(closest.get('time'))
								if previous: episodeTime.append(previous.get('time'))
								if last: episodeTime.append(last.get('time'))
								episodeTime = [i for i in episodeTime if i and not i == specialTime]
								if not episodeTime: episodeTime = [specialTime] # If a standard episode has the same date as the special.
								times[2] = episodeTime

			if not count: count = {}

			# MOVIES + SETS
			#	1. Debut dates (premiere)
			#	2. Launch dates (limited/theatrical)
			#	3. Home dates (digital/physical/television)
			#	4. Other (scene/unknown)
			if media == Media.Movie or media == Media.Set:
				# Use a fallback for sets, which only have the premiere date in the individual movies/parts.
				value = _extract(metadata = metadata, lookup = (MetaTools.TimeDebut, MetaTools.TimePremiere, MetaTools.TimeLimited, MetaTools.TimeTheatrical, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision))
				if value: times[0].extend(value)

				value = _extract(metadata = metadata, lookup = (MetaTools.TimeLaunch, MetaTools.TimeLimited, MetaTools.TimeTheatrical, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision))
				if value: times[1].extend(value)

				value = _extract(metadata = metadata, lookup = (MetaTools.TimeHome, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision))
				if value: times[2].extend(value)

				if media == Media.Set: count = len(metadata.get('part') or [])

			# SHOWS
			#	1. Show premiere (S01)
			#	2. Show premiere (S01)
			#	3. Show premiere and finale (or last available episode) (Sxx)
			#	4. None
			elif media == Media.Show:
				value = _extract(metadata = metadata, lookup = lookup, minimum = True)
				if value: [times[i].extend(value) for i in (0, 1)]

				value = _extract(metadata = metadata, lookup = lookup, minimum = True, maximum = True)
				if value: times[2].extend(value)

			# SEASONS
			#	1. Show premiere (S01)
			#	2. All season premieres (Sxx)
			#	3. Standard season premieres and finales (or last available episode) (Sxx)
			#	4. Special season (S00)
			elif media == Media.Season:
				seasons = metadata.get('seasons')
				if seasons:
					# Use the last season's release interval, since it can change from season to season, and refreshing matters for the last season.
					for i in reversed(seasons):
						try:
							interval = i['packed']['interval']
							if interval: break
						except: pass

					for i in seasons:
						season = i.get('season')
						if not season is None:
							index = []
							if season == 1: index.append({'index' : 0, 'minimum' : True})
							if season >= 0: index.append({'index' : 1, 'minimum' : True})
							if season >= 1: index.append({'index' : 2, 'minimum' : True, 'maximum' : True}) # Not for specials.
							if season == 0: index.append({'index' : 3, 'minimum' : True})
							if index:
								for j in index:
									counts[j['index']] += 1 # Count even if there is no time.
									value = _extract(metadata = i, lookup = lookup, minimum = j.get('minimum'), maximum = j.get('maximum'))
									if value: times[j['index']].extend(value)
					typeSeason = seasons[-1].get('type') or []

				try: count[Media.Season] = max(count.get(Media.Season) or 0, counts[2]) # Use counts[2] and not counts[1], since it should exclude S0.
				except: pass
				try: count[Media.Special] = max(count.get(Media.Special) or 0, 1 if counts[3] else 0)
				except: pass

			# EPISODES
			#	1. Season premieres (SxxE01)
			#	2. Season, midseason, and alternative premieres (SxxEyy)
			#	3. All standard episodes (SxxEyy)
			#	4. Special episodes (SxxE00 and S00Eyy)
			elif media == Media.Episode:
				episodes = metadata.get('episodes')
				if episodes:
					try: interval = episodes[0]['packed']['interval']
					except: pass

					for i in episodes:
						season = i.get('season')
						episode = i.get('episode')
						if not episode is None:
							index = []
							typed = i.get('type') or []
							if episode == 1: index.append(0)
							if episode == 1 or Media.Premiere in typed: index.append(1)
							if episode >= 1: index.append(2)
							if episode == 0 or Media.Special in typed: index.append(3)
							if index:
								for j in index: counts[j] += 1 # Count even if there is no time.
								value = _extract(metadata = i, lookup = lookup)
								if value:
									for j in index: times[j].extend(value)
					typeEpisode = episodes[-1].get('type') or []

					# Trakt season absolute-episode numbers.
					# Eg: One Piece S22 starts at E1089.
					# The episode count from release calendars are based on the last aired episode number.
					# Eg: One Piece S22E1155. S22 is seen as having 1155 episodes.
					# Subtract the first episode number to get the actual count.
					# Eg: One Piece S22E1155 - S22E1089 + 1 = 67 episodes.
					# Currently episode releases only come from the Trakt calendar and from the Arrivals.
					try:
						if origin and MetaManager.OriginTrakt in origin:
							first = None
							try: first = episodes[0]['number'][MetaPack.ProviderTrakt][MetaPack.NumberStandard][MetaPack.PartEpisode]
							except: pass
							if first is None:
								try: first = episodes[0].get('episode')
								except: pass
							if first and first > 1:
								total = count.get(Media.Episode) - first + 1
								if total > 0: count[Media.Episode] = total
					except: Logger.error()

				try: count[Media.Episode] = max(count.get(Media.Episode) or 0, counts[2])
				except: pass
				try: count[Media.Special] = max(count.get(Media.Special) or 0, counts[3])
				except: pass

				# Only if requesting the latests season.
				if not numberSeason is None and numberSeason == metadata.get('season'): typeSeason = metadata.get('type')

			# PACKS
			#	1. Show premieres (S01E01)
			#	2. Season, midseason, and alternative premieres (SxxEyy)
			#	3. All standard episodes (SxxEyy)
			#	4. Special episodes (SxxE00 and S00Eyy)
			elif media == Media.Pack:
				pack = MetaPack.instance(metadata)

				if pack:
					status = pack.status()
					interval = pack.interval()

					lastSeason = pack.lastSeasonOfficial() or pack.lastSeasonStandard()
					numberLast = pack.numberSeason(item = lastSeason) if lastSeason else None

					# The for-loop can take a few 100ms for packs with a few 1000 episodes.
					# Technically not all episodes are needed, only the recent ones.
					# This reduces the show Progress menu loading time for 15 shows (with at least one large show) for this function from 300-500ms down to 80-100ms.
					#episodes = pack.episode()
					episodes = []
					numbers = [0] # Always include S0, since there might be new specials.
					numberMaximum = []

					if numberSeason: # Add the season of the current release.
						numbers.append(numberSeason)
						numberMaximum.append(numberSeason)
					if numberLast: # Add the last available season.
						numbers.append(numberLast)
						numberMaximum.append(numberLast)
					if not numberSeason and not numberLast: # Add S01 if there are no other numbers.
						numbers.append(1)
						numberMaximum.append(1)

					# Add other seasons that are currently running or are in the future.
					numberMaximum = [i for i in numberMaximum if i]
					if numberMaximum:
						numberMaximum = max(numberMaximum)
						if numberMaximum and not numberMaximum in numbers:
							for i in range(numberMaximum, 0, -1):
								timeSeason = pack.timeMaximum(season = i)
								if not timeSeason: timeSeason = pack.timeMinimum(season = i)
								numbers.append(i)
								if timeSeason and timeSeason < current: break

					for i in Tools.listUnique(numbers):
						episodes2 = pack.episode(season = i)
						if episodes2: episodes.extend(episodes2)

					# Always include the first episode for the show premiere.
					if not 1 in numbers:
						episode2 = pack.episode(season = 1, episode = 1)
						if episode2: episodes.append(episode2)

					if episodes:
						for i in episodes:
							numberStandard = pack.numberStandard(item = i)
							if numberStandard:
								try: season = numberStandard[MetaPack.PartSeason]
								except: season = None
								try: episode = numberStandard[MetaPack.PartEpisode]
								except: episode = None
								if not season is None and not episode is None:
									index = []
									type = pack.type(item = i)
									if season == 1 and episode == 1: index.append(0)
									if season >= 1 and (episode == 1 or (type and type.get(Media.Premiere))): index.append(1)
									if season >= 1 and episode >= 1: index.append(2)
									if season == 0 or episode == 0 or (type and type.get(Media.Special)): index.append(3)
									if index:
										value = _extract(metadata = i, pack = pack)
										if value:
											for j in index: times[j].extend(value)

					typeSeason = pack.type(item = lastSeason)
					typeEpisode = pack.type(item = pack.lastEpisodeOfficial() or pack.lastEpisodeStandard())

					# Sometimes Trakt does not have the TVDb IDs of newly released episodes.
					# This makes all TVDb episodes extra unofficial episodes.
					# The total/standard episode count can therefore be substantially higher, up to twice as many episodes, since the unofficial episodes are counted as well.
					# Certain unofficial episodes should still be counted, such as a few extra IMDb specials at the end of the season.
					# Hence, if the standard count is substantially higher than the official count, rather use the official count.
					def _count(media, count, countAll, countOfficial):
						try: count[media] = max(count.get(media) or 0, countOfficial if (countAll > countOfficial * 1.5) else countAll)
						except: pass
					_count(media = Media.Pack, count = count, countAll = pack.countEpisode(), countOfficial = pack.countEpisodeOfficial())
					_count(media = Media.Season, count = count, countAll = pack.countSeasonStandard(), countOfficial = pack.countSeasonOfficial())
					_count(media = Media.Episode, count = count, countAll = pack.countEpisodeStandard(), countOfficial = pack.countEpisodeOfficial())
					_count(media = Media.Special, count = count, countAll = pack.countSpecial(), countOfficial = pack.countSpecial())

			# Get the IDs if this title is old and therefore not in the releases anymore.
			if not id and metadata: id = metadata.get('id')

			# Calculate the season and episode types.
			types = (Media.Premiere, Media.Finale, Media.Special, Media.Standard, Media.Outer, Media.Inner, Media.Middle)
			if typeSeason: typeSeason = [i for i in typeSeason if i in types]
			if not typeSeason: typeSeason = None
			if typeEpisode: typeEpisode = [i for i in typeEpisode if i in types]
			if not typeEpisode: typeEpisode = None

			# Calculate the release period.
			value = _extract(metadata = metadata, pack = pack, lookup = (MetaTools.TimePremiere, MetaTools.TimeLimited, MetaTools.TimeTheatrical, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision, MetaTools.TimeEnded), all = True) # TimeEnded for the season's last episode.
			if not value: value = []
			for i in (0, 1, 2): value.extend(times[i])
			minimum = min(value) if value else None
			maximum = max(value) if value else None

			if status in MetaTools.StatusesFuture: period = MetaCache.PeriodFuture
			elif status in MetaTools.StatusesPresent: period = MetaCache.PeriodPresent
			elif status in MetaTools.StatusesPast: period = MetaCache.PeriodPast

			# If the movie does not have a home release date yet and its premiere date is within the past few years, mark it as PeriodPresent.
			# Since movies are StatusReleased (aka PeriodPast) right after having premiered, even if it was not released for home yet.
			# Also mark home release dates within the past few weeks as PeriodPresent, so that MetaCache._releaseLevel() picks a higher level while the movie is new (for home).
			if media == Media.Movie and period == MetaCache.PeriodPast:
				value = _extract(metadata = metadata, lookup = (MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision))
				if not value and (not maximum or maximum > (current - 63115200)): period = MetaCache.PeriodPresent # 2 years. No home release date and the premiere date is within the past few years.
				elif value and maximum and maximum > (current - 4838400): period = MetaCache.PeriodPresent # 8 weeks. Home release date is within the past few weeks.

			# Do not set the period to PeriodPast based solely on the time when the status is PeriodPresent.
			# Otherwise if season metadata is outdated and does not have the latest unreleased season, it will be set to PeriodPast instead of PeriodPresent.
			finished = not period == MetaCache.PeriodPresent
			if not finished and typeEpisode and Media.Finale in typeEpisode:
				if media == Media.Episode:
					if Media.Inner in typeEpisode or Media.Outer in typeEpisode: finished = True
				if media == Media.Season or media == Media.Pack:
					if Media.Outer in typeEpisode: finished = True
			if maximum and maximum < current and finished:
				period = MetaCache.PeriodPast
				status = MetaTools.StatusEnded
			elif minimum and minimum <= current and maximum and maximum >= current:
				period = MetaCache.PeriodPresent
				status = MetaTools.StatusContinuing
			elif minimum and minimum >= current:
				period = MetaCache.PeriodFuture
			# The current seasons has ended, but the show is returning for a new season at some point in the future.
			# Sometimes StatusReturning is used for currently running seasons (present). Therefore, also check the time to see if the season ended.
			# StatusReturning can also be an outdated status before the new season was released. Now that the new season started, the updated status would be StatusContinuing.
			# Not sure if this can create problems, when the currently running season is StatusReturning, but the maximum time is in the past, but unaired/future episodes in the season do not have metadata yet.
			elif status == MetaTools.StatusReturning and maximum and maximum < current:
				# For daily shows, the last episode (maximum) has to aired at least 2 weeks ago to be considered PeriodPast.
				# Sometimes Trakt does not have the most recent episodes for daily shows, while IMDb (and sometimes TVDb) has more future/unaired episodes.
				# Eg: The Tonight Show Starring Jimmy Fallon - Trakt only goes up to S13E19 (aired 5 days ago) while IMDb goes until S13E53 (future episodes without a date).
				if not interval == MetaPack.IntervalDaily or abs(maximum - current) > 1209600: # 2 weeks.
					period = MetaCache.PeriodPast

			# Calculate the closest dates.
			tools = MetaTools.instance()
			past, future = self._releaseClosest(media = media)
			times = [tools.timeClosest(times = i, time = current, past = past, future = future, fallback = True) for i in times]

			if times:
				result = {'id' : id, 'status' : status, 'period' : period}
				if Media.isSerie(media): result['interval'] = interval
				result['time'] = times
				result['count'] = count or None

				if Media.isSerie(media):
					if number: result['number'] = number
					if previous: result['previous'] = previous
					if closest: result['closest'] = closest
					if last:
						result['last'] = Tools.copy(last) # Edited below.
					elif not numberSeason is None:
						result['last'] = {'season' : numberSeason}
						if not numberEpisode is None: result['last']['episode'] = numberEpisode
					else:
						result['last'] = {}
					result['last']['type'] = {'season' : typeSeason, 'episode' : typeEpisode}
					if special: result['special'] = special

				return result
		except: Logger.error()
		return None

	@classmethod
	def _releaseClear(self, media = None):
		if media:
			Memory.clear(id = self._releaseId(media = media), local = True, kodi = True)
		else:
			Memory.clear(id = self._releaseId(media = Media.Movie), local = True, kodi = True)
			Memory.clear(id = self._releaseId(media = Media.Show), local = True, kodi = True)

	@classmethod
	def _releaseId(self, media):
		return MetaManager.PropertyRelease + media

	@classmethod
	def _releaseClosest(self, media):
		# future: The maximum allowed time into the future. Titles further into the future will be ingored if there are past dates.
		# past: The maximum allowed time into the past. Titles older than this will allow dates further into the future than specified with the "future" parameter.
		# Do not go too far into the future, otherwise a future physical date might be preferred above a recently past digital date.
		if Media.isSerie(media):
			# Less than half a week in case the previous aired episode was released a week before, still refresh according to the past episode's date.
			# Eg: The past episode aired 2 days ago, while the new episode is 5 days into the future. In this case, use the past date's refresh rate.
			future = 259200 # 3 days
			# If the previous aired episode is more than a week ago, allow dates further than the "future" parameter into the future.
			# Eg: The past episode aired a year ago, while the new episode is 2 weeks into the future. In this case, use the future date's refresh rate.
			past = 691200 # 8 days
		else:
			# In case 2 dates (eg digital and physical) are close to each other.
			future = 604800 # 1 week.
			# Assume that the past date has been refreshed within this period, after which we allow further future dates as well.
			past = 1209600 # 2 weeks.

		return past, future

	def _releaseAssemble(self, media):
		try:
			timer = self._jobTimer()

			itemsExternal = []
			itemsProgress = []
			itemsArrival = []
			movie = Media.isFilm(media)
			serie = Media.isSerie(media)
			current = Time.timestamp()
			collections = None
			order = [MetaTools.ProviderTrakt, MetaTools.ProviderImdb, MetaTools.ProviderTmdb, MetaManager.OriginOfficial, MetaManager.OriginScene, MetaManager.OriginArrival, MetaManager.OriginProgress]

			results = []
			result = {MetaTools.ProviderTrakt : {}, MetaTools.ProviderImdb : {}, MetaTools.ProviderTmdb : {}, MetaTools.ProviderTvdb : {}, 'slug' : {}}
			if movie: result['collection'] = {}

			# Make sure that any parameters passed into this function does not cause a different cache call, since the cache parameters are different.
			# Meaning these calls should always retrieve the same data as the normal menu and reload calls.
			# limit=False: return all items.
			# internal=True: in order not to use the outer cache data from content().
			progress = self.progress(media = media, pack = False, detail = False, limit = False, internal = True)
			if progress: itemsProgress = progress.get('items')
			arrival = self.arrival(media = media, pack = False, detail = False, limit = False, internal = True)
			if arrival: itemsArrival = arrival.get('items')

			external = self._releaseExternal(media = media)
			if external: itemsExternal = external

			# The calculated times (debut, launch, etc) are not available if the item was not smart-loaded yet.
			if movie:
				types = (
					(MetaTools.TimeDebut, MetaTools.TimePremiere, MetaTools.TimeLimited, MetaTools.TimeTheatrical, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision),
					(MetaTools.TimeLaunch, MetaTools.TimeTheatrical, MetaTools.TimeLimited, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision),
					(MetaTools.TimeHome, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision),
				)
				typesAll = (MetaTools.TimePremiere, MetaTools.TimeLimited, MetaTools.TimeTheatrical, MetaTools.TimeDigital, MetaTools.TimePhysical, MetaTools.TimeTelevision, MetaTools.TimeCustom)

				# Extract the collection ID from items that have it (Arrivals) so that it can be used for those that do not have the collection ID (scene/official/etc).
				collections = {MetaTools.ProviderTrakt : {}, MetaTools.ProviderImdb : {}, MetaTools.ProviderTmdb : {}}
				for item in (itemsExternal + itemsProgress + itemsArrival):
					collection = Tools.get(item, 'id', 'collection', MetaTools.ProviderTmdb)
					if collection:
						for i in collections.keys():
							id = item.get(i)
							if id: collections[i][id] = collection

			# NB: Sometimes the official releases return a DVD/Bluray release for a season that is far into the past.
			# Eg: One Piece S14 (physical release) while the current airing season is S22.
			# These are skipped inside the for-loop based on the season/episode numbers.
			# However, this requires "entry" to have a number from a previous loop-iteration, before we get to OriginOfficial.
			# Hence, first process OriginTrakt/OriginProgress/OriginArrivals to make sure the later number is added to "entry", before processing OriginOfficial/OriginScene with these earlier/incorrect numbers.
			# This is needed for the skipping code inside the for-loop, underneath "if originExternal:".
			itemsTrakt = []
			itemsOfficial = []
			itemsScene = []
			itemsOther = []
			for item in itemsExternal:
				origin = item.get('origin')
				if origin == MetaManager.OriginTrakt: itemsTrakt.append(item)
				elif origin == MetaManager.OriginOfficial: itemsOfficial.append(item)
				elif origin == MetaManager.OriginScene: itemsScene.append(item)
				else: itemsOther.append(item) # This should never happen, except if there is a bug.

			for origin, items in ((None, itemsTrakt), (MetaManager.OriginProgress, itemsProgress), (MetaManager.OriginArrival, itemsArrival), (None, itemsOfficial), (None, itemsScene), (None, itemsOther)):
				for item in items:
					trakt = item.get(MetaTools.ProviderTrakt)
					imdb = item.get(MetaTools.ProviderImdb)
					tmdb = item.get(MetaTools.ProviderTmdb)
					tvdb = item.get(MetaTools.ProviderTvdb)

					collection = None
					if movie:
						collection = Tools.get(item, 'id', 'collection', MetaTools.ProviderTmdb)
						if not collection:
							for i in collections.keys():
								id = item.get(i)
								if id:
									collection = collections[i].get(id)
									if collection: break

					# Also add the slug, for quicker lookups for the official/scene releases.
					# Recalculate the slug, in case the Trakt slug was passed in from the smart lists (should not be the case).
					title = item.get('tvshowtitle') or item.get('title')
					slug = Tools.replaceNotAlphaNumeric(title).lower() if title else None
					if not slug: slug = item.get('slug')

					lookup = [('slug', slug), (MetaTools.ProviderTrakt, trakt), (MetaTools.ProviderImdb, imdb), (MetaTools.ProviderTmdb, tmdb), (MetaTools.ProviderTvdb, tvdb), ('collection', collection)]
					lookup = [i for i in lookup if not i[1] is None]

					# Item can appear in both Progress and Arrivals.
					# Or they appear in both the smart lists and the external sources.
					entry = None
					for i in lookup:
						entry = result[i[0]].get(i[1])
						if entry: break
					if not entry:
						# 4 sets of time:
						#	Movies: [premiere (earliest release) | limited/theatrical | digital/physical/tv | last release (eg 4k or anniversary release) ]
						#	Shows: [show premiere S01E01 | latests season premiere SxxE01 | latests episode aired SxxEyy | latests special aired S00Eyy]
						# 4 subsets of time, ordered from most important/exact to least important/exact:
						#	[known/exact/Trakt dates | official non-Trakt dates | estimated/scene/unknwon-number dates | unknown/very-inexact dates from request parameters]
						entry = {'origin' : [], 'time' : [[[], [], [], []], [[], [], [], []], [[], [], [], []], [[], [], [], []]]}

						# If the movie belongs to a collection, add the movie IDs.
						# These are needed in _releaseLookup() and later in MetaCache._releasePartial() to determine which movie is the latest one in the collection.
						# Do not add the IDs for all titles, since they are not needed and just increase storage space.
						if collection: entry['id'] = {MetaTools.ProviderTrakt : trakt, MetaTools.ProviderImdb : imdb, MetaTools.ProviderTmdb : tmdb, 'collection' : collection}

						results.append(entry)
						for i in lookup: result[i[0]][i[1]] = entry

					smart = Tools.get(item, MetaManager.Smart, 'release') or {}
					type = item.get('type')

					time = item.get('time')
					timeSingle = time
					if Tools.isArray(timeSingle): timeSingle = self.mTools.timeClosest(times = timeSingle, time = current, future = True)
					elif Tools.isDictionary(timeSingle): timeSingle = timeSingle.get(MetaTools.TimePremiere)

					# Always replace the origin if one of the items comes from Trakt, since Trakt has the most accurate data.
					# This is also used in other places, like in _metadataSmartRelease() to sort titles that on the Trakt calendar to the top.
					if origin is None: origin = item.get('origin') # Only for external sources.
					originInternal = origin == MetaManager.OriginArrival or origin == MetaManager.OriginProgress
					originExternal = origin == MetaManager.OriginOfficial or origin == MetaManager.OriginScene

					origins = entry.get('origin')
					origins.append(origin)
					origins = Tools.listSort(Tools.listUnique([i for i in origins if i]), order = order)
					entry['origin'] = origins

					index = None
					season = None
					episode = None
					unknown = None

					if movie:
						if type == MetaTools.TimePremiere: index = [0]
						elif type in MetaTools.TimesCinema: index = [1]
						elif type in MetaTools.TimesHome: index = [2]
						else: index = [2] # Digital/physical date.

						# Add the accurate digitial/physical release dates.
						# Used by the smart menus in _metadataSmartRelease().
						# Since time[2] can be a physical date in the future, while there is a digital date in the past.
						# And sometimes we specifically want the past date, instead of the closest past/future date.
						home = item.get('home')
						if home: entry['home'] = Tools.listSort(Tools.listUnique(home))
					elif serie:
						season = item.get('season')
						episode = item.get('episode')

						entryNumber = entry.get('number')
						if entryNumber is None: entry['number'] = entryNumber = {}

						# Sometimes the official releases return a DVD/Bluray release for a season that is far into the past.
						# Skip these and do not replace the higher numbers.
						# Eg: One Piece S14 (physical release) while the current airing season is S22.
						if originExternal:
							existingSeason = entryNumber.get('season')
							existingEpisode = entryNumber.get('episode')
							if not existingSeason is None and not season is None:
								if season < existingSeason: continue
								if not existingEpisode is None and not episode is None:
									if season == existingSeason and episode < existingEpisode: continue

						# Add the previously aired and last known episodes.
						# Do not use specials for previous/closest/last.
						special = []
						existingSpecial = entry.get('special')
						if existingSpecial: special.append(existingSpecial)
						if season == 0: special.append({'season' : season, 'episode' : episode, 'time' : timeSingle})

						# Last aired episode.
						# Is always in the past and closest to the current time.
						previous = item.get('previous')
						if previous:
							if previous.get('season') == 0:
								special.append(previous)
								previous = None
							else:
								# NB: Only change the previous entry, if the new item was aired AFTER the time of the existing entry.
								# Otherwise if the Trakt official calendar has the previous episode as S22E10, but the user has only watched until S04E03 (from OriginProgress), then S22E10 is incorrectly replaced by the years-earlier S04E03.
								try: existing = entry['previous']['time']
								except: existing = None
								if not existing or (previous.get('time') or 0) > existing: entry['previous'] = previous
								else: previous = None

						# Episode closest to the current time.
						# Can be the previously aired episode, or the next unaired/future episode.
						closest = item.get('closest')
						if closest:
							if closest.get('season') == 0:
								special.append(closest)
								closest = None
							else:
								# NB: Only change the closest entry, if the time of the new item is closer to the time of the existing entry.
								# Otherwise if the Trakt official calendar has the closest episode as S22E10, but the user has only watched until S04E03 (from OriginProgress), then S22E10 is incorrectly replaced by the years-earlier S04E03.
								try: existing = entry['closest']['time']
								except: existing = None
								if not existing or closest.get('time') == self.mTools.timeClosest(times = [existing, closest.get('time') or 0], time = current, future = True): entry['closest'] = closest
								else: closest = None

						# The last known episode in the season, typically in the future.
						# Is often the season finale, but does not have to be if episode's metadata is released eg weekly, shortly before they air.
						last = item.get('last')
						if last:
							if last.get('season') == 0:
								special.append(last)
								last = None
							else:
								try: existing = entry['last']['time']
								except: existing = None
								if not existing or (last.get('time') or 0) > existing: entry['last'] = last
								else: last = None

						# The last known special episode, past or future.
						if special:
							try:
								if len(special) == 1:
									special = special[0]
								else:
									timeSpecial = self.mTools.timeClosest(times = [i.get('time') for i in special if i.get('time')], time = current, future = True)
									if timeSpecial: special = next(i for i in special if i.get('time') == timeSpecial)
									else: special = max(special, key = lambda i : (i.get('episode') or -1))
							except: Logger.error()
							if special:
								if Tools.isArray(special): special = special[-1]
								entry['special'] = special

						# If the show is not in the user's Trakt progress, but only comes from Arrivals.
						# Interpolate missing details as far as possible.
						try:
							if not previous:
								episodes = [closest, {'season' : season, 'episode' : episode or 1, 'time' : timeSingle}, last]
								episodes = [i for i in episodes if i and not i.get('season') == 0 and i.get('time') and i.get('time') < current]

								# NB: Only change the previous entry, if the new item was aired AFTER the time of the existing entry.
								# Otherwise if the Trakt official calendar has the previous episode as S22E10, but the user has only watched until S04E03 (from OriginProgress), then S22E10 is incorrectly replaced by the years-earlier S04E03.
								if episodes:
									itemPrevious = max(episodes, key = lambda i : (i.get('episode') or -1))
									try: existing = entry['previous']['time']
									except: existing = None
									if not existing or (itemPrevious.get('time') or 0) > existing:
										previous = itemPrevious
										if previous: entry['previous'] = previous
						except: Logger.error()
						try:
							if not closest:
								episodes = [previous, {'season' : season, 'episode' : episode or 1, 'time' : timeSingle}, last]
								episodes = [i for i in episodes if i and not i.get('season') == 0 and i.get('time')]
								if episodes:
									# NB: Only change the closest entry, if the time of the new item is closer to the time of the existing entry.
									# Otherwise if the Trakt official calendar has the closest episode as S22E10, but the user has only watched until S04E03 (from OriginProgress), then S22E10 is incorrectly replaced by the years-earlier S04E03.
									timeClosest = self.mTools.timeClosest(times = [i.get('time') for i in episodes], time = current, future = True)
									try: existing = entry['closest']['time']
									except: existing = None
									if not existing or timeClosest == self.mTools.timeClosest(times = [existing, timeClosest or 0], time = current, future = True):
										if timeClosest: closest = next(i for i in episodes if i.get('time') == timeClosest)
										else: closest = episodes[0]
										if closest: entry['closest'] = closest
						except: Logger.error()

						# Do not use the maximum number to determine the index.
						# Otherwise if a show is released on DVD (from official), it will be added as an episode date.
						unknown = season is None and episode is None
						specialIs = not season is None and season == 0
						if specialIs: index = [3]
						elif season is None or episode is None: index = [1]
						elif season == 1 and episode == 1: index = [0, 1, 2]
						elif season > 1 and episode == 1: index = [1, 2]
						else: index = [2]

						# Pick the highest season/episode number if there are multiple seasons/episodes for the same show.
						numbers = [
							(item.get('season'), item.get('episode')),					# Arrivals/Progress: last watched episode. Official/Scene: last released or unreleased season/episode (past or future).
							(smart.get('season'), smart.get('episode')),				# Arrivals/Progress: last known episode of the show (past or future). Official/Scene: None.
							(entryNumber.get('season'), entryNumber.get('episode')),	# Previous entry.
						]
						numbersSpecial = Tools.copy(numbers)

						# Arrivals/Progress can contain future/unaired episodes.
						# Hence, the number might not be the closest episode, but a future episode or even the last episode of the season.
						# Use the maximum number that is lower than the previously aired episode.
						if previous:
							previousSeason = previous.get('season')
							previousEpisode = previous.get('episode')
							if not previousSeason is None:
								numbers.append((previousSeason, previousEpisode))
								numbersSpecial.append((previousSeason, previousEpisode))
								numbers = [i for i in numbers if (i[0] or 0) <= previousSeason]
								if not previousEpisode is None:
									maximumEpisode = None
									if closest and not closest.get('season') == 0: maximumEpisode = closest.get('episode') # Exclude specials returned by Trakt sometimes.
									if maximumEpisode is None: maximumEpisode = (previousEpisode + 1) # The closest (possible future) episode after the previously aired episode.
									numbers = [i for i in numbers if (i[1] or 0) <= maximumEpisode]
						number = max(numbers, key = lambda i : (i[0] or -1, i[1] or -1))
						season = 1 if number[0] is None else number[0]
						episode = 1 if number[1] is None else number[1]

						if origin == MetaTools.ProviderTrakt:
							season2 = item.get('season')
							episode2 = item.get('episode')
							if not season2 is None and not episode2 is None:
								if not season2 == 0: # Exclude specials returned by Trakt sometimes.
									season = season2
									episode = episode2

						entryNumber['season'] = season
						entryNumber['episode'] = episode

						# Specials are often added after a season ends, or even weeks/months/years after the show has ended.
						# Eg: tt0165581 ended in 2007, but a new special (S00E10) was added in 2021.
						# Add the special number, so that S0 can be refreshed if a new special comes out, even if the season/episode number points to the last standard episode in the show.
						# Specials are only be available from the Trakt episode calendar.
						if specialIs:
							number = max(numbersSpecial, key = lambda i : (0 if i[0] == 0 else -1, i[1] or -1))
							if number and number[0] == 0 and number[1]: entryNumber['special'] = number[1]

						# Pick the maximum counts.
						countSeason = [season, item.get('season'), smart.get('season'), entryNumber.get('season')]
						countEpisode = [episode, item.get('episode'), smart.get('episode'), entry.get('episode')]
						if previous:
							countSeason.append(previous.get('season'))
							countEpisode.append(previous.get('episode'))
						if closest:
							countSeason.append(closest.get('season'))
							countEpisode.append(closest.get('episode'))
						if last:
							countSeason.append(last.get('season'))
							countEpisode.append(last.get('episode'))
						countSeason = max(countSeason, key = lambda i : i or 0)
						countEpisode = max(countEpisode, key = lambda i : i or 0)

						count = {
							Media.Pack : 1, # Total number of episodes in the entire show. Actual count is unknown, only the first episode is known.
							Media.Season : countSeason, # Total number of seasons, excluding S0.
							Media.Episode : countEpisode or 1, # Total number of episodes in the latests season. Actual count is unknown, only the first episode is known.
							Media.Special : entryNumber.get('special') or (1 if specialIs else None), # Total number of specials in S0. Do not assume S0 exists, otherwise there might be constant season refreshes if the metadata only contains S1 and only S1 (but not S0) exists on Trakt/TVDb.
						}

						counted = entry.get('count') or {}
						smarted  = smart.get('count') or {}
						if counted or smarted:
							for i in count.keys():
								count[i] = max(counted.get(i) or 0, smarted.get(i) or 0, count.get(i) or 0)
						entry['count'] = count

					if time:
						if Tools.isDictionary(time): # Arrivals/Progress.
							if movie:
								for i in range(len(types)):
									# Add the exact/known dates first.
									value = None
									for j in types[i]:
										value = time.get(j)
										if value:
											entry['time'][i][0].append(value)
											break

									# Add the estimated dates.
									if not value:
										value = self.mTools.timeEstimate(type = types[i][0], times = time, metadata = item)
										if value: entry['time'][i][2].append(value)

								# Add last/closest (re-)release date for movies.
								all = []
								for i in typesAll:
									# Do not include the custom movie date from Arrivals/Progress, since it already comes from release() iteself.
									# Ignore it, in case the old date is still in the smart Arrivals/Progress list, because of old code, even though it is not in release() anymore.
									if i == MetaTools.TimeCustom and originInternal: continue

									value = time.get(i)
									if value: all.append(value)
								entry['time'][3][0].extend(all)
							elif serie:
								# Show, season, or episode premieres.
								value = time.get(MetaTools.TimePremiere)
								if value:
									if Tools.isArray(value):
										for i in index: entry['time'][i][0].extend(value)
									elif Tools.isInteger(value):
										for i in index: entry['time'][i][0].append(value)

								# Season premieres.
								value = time.get(MetaTools.TimeCustom)
								if value:
									if Tools.isArray(value):
										entry['time'][1][0].extend(value)
									elif Tools.isInteger(value):
										entry['time'][1][0].append(value)
									# If there is a custom time, the premiere time should be the show's premiere.
									value = time.get(MetaTools.TimePremiere)
									if value:
										if Tools.isArray(value):
											entry['time'][0][0].extend(value)
										elif Tools.isInteger(value):
											entry['time'][0][0].append(value)

								# Additional dates from the pack added by the show progress smart-list.
								if smart:
									value = smart.get('time')
									if value:
										for i in range(len(value)):
											if Tools.isArray(value[i]): entry['time'][i][0].extend(value[i])
											else: entry['time'][i][0].append(value[i])

							# Add the unknown dates last.
							# For shows add this as a season premiere, since Arrivals calendars are only new shows/seasons, not new episodes.
							value = time.get(MetaTools.TimeUnknown)
							if value: entry['time'][2 if movie else 1][3].append(value)

						else: # External sources.
							# Add scene releases to the back, because they sometimes are not close to the actual release date (although many are released within a few days of the date).
							# Also add official releases without a season/episode number to the back. These are later DVD releases from Official2/Official3 which can be released years after the show has ended.
							# Eg: dvdsreleasedates.com had a new BluRay release for tt0165581 in Dec 2024. Do not add this as primary date.
							# Do not add official non-Trakt dates to front, since sometimes there are DVD/BluRay releases months or years after the actual physical release date (eg: new 4KL remastered or deluxe editions).
							# Eg: dvdsreleasedates.com had a new SteelBook 4K release for tt15239678 on 19 Nov 2024 (more than half a year after the official home release date).
							if origin == MetaManager.OriginScene or unknown: section = 2 # Scene and unknown releases.
							elif item.get('trakt'): section = 0 # Official Trakt releases.
							else: section = 1 # Official non-Trakt releases.
							if Tools.isArray(time):
								for i in index: entry['time'][i][section].extend(time)
							elif Tools.isInteger(time):
								for i in index: entry['time'][i][section].append(time)

							# Add last/closest (re-)release date for movies.
							if movie:
								if Tools.isArray(time): entry['time'][3][0].extend(time)
								elif Tools.isInteger(time): entry['time'][3][0].append(time)

			# There can be dates in the same category that are very far apart, especially the 3rd time entries.
			#	Movies: The Trakt calendar only returns premiere/physical dates, but no digital dates. The scene releases might also not come out on the exact digital/physical release dates.
			#	Episodes: There can be airing dates of multiple/all episodes in a season.
			# Instead of having a complex process to determine which of those dates to use (eg: digital vs physical vs scene dates), keep the selection simple.
			# Simply pick the date that is closest to today. This list gets refreshed every day, so the time difference between the release date and today are recalculated regularly and should be accurate enough.
			# Also limit how far into the future dates can be used. If today is between the digital date (in the past) and the physical date (in the future), only pick the future date (if it is closer to today) if it is not too far into the future.
			# This might cause some movies to be refreshed a few extra times. Eg: a refresh triggered on the digital release date, and a few days later again when the scene release comes out.
			# But this will not happen too often, only happen for newish releases, and even if it happens, refreshing a movie 2-3 times more is not too expensive.
			past, future = self._releaseClosest(media = media)
			for item in results:
				remove = False

				time = item.get('time')
				if time:
					for i in range(len(time)):
						for j in range(len(time[i])):
							value = [k for k in time[i][j] if k]

							# Add the more accurate Trakt digital/physical release dates to time[2][0].
							if movie and i == 2 and j == 0:
								home = item.get('home')
								if home: value.extend(home)

							time[i][j] = self.mTools.timeClosest(times = value, time = current, future = future, past = past, fallback = True) if value else None

						# Pick the date that is most accurate.
						# Only pick ones from the back of the list if there are no dates in the front.
						#	1. Exact/known dates. These should be accurate dates.
						#	2. Official non-Trakt releases that sometimes can have a DVD release a lot later than the actual physical release date.
						#	3. Scene releases, official releases without a season/episode number, and estimated dates, which are mostly slightly inaccurate.
						#	4. Unknown dates added as request parameters, which are mostly very inaccurate.
						time[i] = time[i][0] or time[i][1] or time[i][2] or time[i][3] # Replace the date list with a single date.

					if serie:
						# If no episode time is available yet, because it was not smart loaded yet (the air date is not available in the Trakt Progress), assume the season/show premiere as episode premiere.
						if not time[2]: time[2] = time[1] or time[0]

					# Remove if all dates are None.
					if not remove:
						value = any(time)
						if not value: remove = True

					# Remove if the digital/physical, or the last episode, was released more than a year ago.
					if not remove:
						value = time[2]
						if value and (current - value) > 31557600: remove = True

					# Remove if the closest available date is more than 1.5 years ago.
					if not remove:
						value = self.mTools.timeClosest(times = time, time = current, future = True)
						if value and (current - value) > 47336400: remove = True

					# For movies, remove if the premiere date was years ago. They are only listed here, since they have a recent physical release.
					if not remove:
						if movie:
							value = time[0]
							if value and (current - value) > 78894000: remove = True # Premiered more than 2.5 years ago.
				else:
					remove = True

				if remove: item['remove'] = True

			# Do not store the slug lookup, to save space.
			# Lookups should also be done on IDs only to keep things efficient.
			# If an item has only a slug, but no ID, it will not be used.
			del result['slug']

			# Remove old entries to save space and make lookups more efficient.
			# Items are removed if they have not date or the date is far into the past.
			for k, v in result.items():
				for x in list(v.keys()): # Since we delete while iterating.
					if v[x].get('remove'): del v[x]

			# Limit the maximum number of items in the lookup table, to reduce storage space and lookup time.
			# Older values already get removed if they have an old date.
			# But in case there is a bug, or simply many releases within a year, that makes the lookup table grow continuously.
			# The titles removed here are the oldest ones (months ago), which we probably do not need in any case.
			limit = 5000
			for k, v in result.items():
				values = Tools.listSort(v.values(), key = lambda x : min([(i or 0) for i in (x['time'] or [0])]), reverse = True)
				for item in values[:limit]:
					if not 'remove' in item: item['remove'] = False
				for item in values[limit:]:
					if not 'remove' in item: item['remove'] = True
			for k, v in result.items():
				for x in list(v.keys()): # Since we delete while iterating.
					if v[x].get('remove'):
						del v[x]
					else:
						try: del v[x]['remove']
						except: pass

			# The release dictionary can grow very large, easily a few MB per media.
			# This dictionary can then take long to load from Memory and JSON-decode when metadata is retrieved from cache, even if it is only done once per invoker.
			# Reduce the size of the dictionary as follows:
			#	1. Instead of storing each item seperatley under trakt/imdb/tmdb/tvdb, store it once in the "data" lookup and then assign an ID to it, which is added to the trakt/imdb/tmdb/tvdb lookup.
			#	2. Change all keys to a single letter, to reduce storage space.
			# Both these changes have to be inversed in _releaseLookup().
			# This reduces the dictionary size to a third.
			id0 = 0
			ids = {}
			data = {}
			for provider, values in result.items():
				for id, value in values.items():
					id1 = Tools.id(value)
					id2 = ids.get(id1)
					if not id2:
						id0 += 1
						id2 = id0
						ids[str(id1)] = id2
						data[str(id2)] = self._releaseReduce(item = value, inverse = True)
					values[id] = id2
			result['data'] = data

			Logger.log('SMART RELEASES (%s | %dms): Total: %d' % (media.capitalize(), timer.elapsed(milliseconds = True), max([len(i.keys()) for i in result.values()])))
			return result
		except: Logger.error()
		return None

	@classmethod
	def _releaseReduce(self, item, inverse = False):
		# Make the dict reduced-key : full-key.
		# So that the inverse mapping below does not have to be done from _releaseLookup() which is called often, but only in _releaseAssemble(), which is not called that often.
		keys = {
			'o'	: 'origin',
			't'	: 'time',

			# Movies (if it is part of a colelction)
			'i'	: 'id',
			'f'	: 'trakt',
			'g'	: 'imdb',
			'h'	: 'tmdb',
			'j'	: 'tvdb',
			'k'	: 'collection',

			# Shows
			'n'	: 'number',
			's'	: 'season',
			'e'	: 'episode',
			'x'	: 'special',
			'p'	: 'pack',
			'c'	: 'count',
			'r'	: 'previous',
			'l'	: 'closest',
			'a'	: 'last',

			'z'	: 'home',
		}
		if inverse: keys = {v : k for k, v in keys.items()}

		result = {}
		for k1, v1 in item.items():
			if Tools.isDictionary(v1):
				value = {}
				for k2, v2 in v1.items():
					key = keys.get(k2)
					if not key:
						key = k2
						Logger.log('RELEASE REDUCE: Unknown key "%s"' % key)
					value[key] = v2
			else:
				value = v1

			key = keys.get(k1)
			if not key:
				key = k1
				Logger.log('RELEASE REDUCE: Unknown key "%s"' % key)
			result[key] = value

		return result

	def _releaseExternal(self, media, items = None, refresh = None):
		# Takes about 15-20 secs for the initial retrieval, and about 5 secs for daily retrievals.

		def _release(result, function, rank, refresh):
			result[rank] = function(refresh = refresh)

		threads = []
		official = [None, None, None]
		scene = [None, None, None]

		#gaiafuture - Add another official release calendar.
		#	https://www.releases.com/calendar/movies?f=v%3A4K%20Blu-ray
		# But this is probably not needed, since there are already so many calendars.
		# Plus Trakt now has a streaming calendar and this would not add much.

		functions = [
			# https://trakt.tv
			# Refreshed daily [Initial: 39 requests | Daily: 6 requests | Not refreshed for a few days: 6-18 requests]
			# Disk/streaming movie releases and new episode releases.
			# Returns around 400 movies + whatever shows the user has for the intial 2x13 pages.
			self._releaseExternalOfficial1,

			# https://dvdsreleasedates.com
			# Refreshed every 3 days [Initial: 26 requests | Every 3 days: 4 requests | Not refreshed for a few days: 4-12 requests]
			# Digital and disk releases with IMDb ID, but not that many titles listed.
			# Returns around 700 titles for the intial 2x13 pages.
			self._releaseExternalOfficial2,

			# https://blu-ray.com
			# Refreshed every 3 days [Initial: 39 requests | Every 3 days: 6 requests | Not refreshed for a few days: 6-18 requests]
			# Digital and disk releases without IMDb ID and only a title, but has more titles listed.
			# Returns around 4500 titles for the intial 3x13 pages.
			self._releaseExternalOfficial3,
		]
		threads.extend([Pool.thread(target = _release, kwargs = {'result' : official, 'function' : functions[i], 'rank' : i, 'refresh' : refresh}, start = True) for i in range(len(functions))])

		functions = [
			# https://rlsbb.cc
			# Refreshed daily [Initial: 20 requests | Daily: 2 requests | Not refreshed for a few days: 2-15 requests]
			# Has multiple subdomains and can therefore attempt extra requests if a subdomain is down.
			# Returns around 150 titles for the intial 20 pages.
			self._releaseExternalScene1,

			# https://predb.me
			# Refreshed daily [Initial: 20 requests | Daily: 2 requests | Not refreshed for a few days: 2-15 requests]
			# Sometimes has sporadic Cloudflare protection and might not return results.
			# Returns around 100 titles for the intial 20 pages.
			self._releaseExternalScene2,

			# https://pre.corrupt-net.org
			# Refreshed daily [Initial: 6 requests | Daily: 4 requests | Not refreshed for a few days: 4-6 requests]
			# Does not return many titles, since most listed on the pages are old, shows, or foreign titles.
			# Returns around 20 titles for the intial 2x3 pages.
			self._releaseExternalScene3,
		]
		threads.extend([Pool.thread(target = _release, kwargs = {'result' : scene, 'function' : functions[i], 'rank' : i, 'refresh' : refresh}, start = True) for i in range(len(functions))])

		Pool.join(instance = threads)

		result = []
		for i in (official + scene):
			i = i.get(media)
			if i: result.extend(i)
		return result

	def _releaseExternalAssemble(self, function, links, domains = None, pages = None, cache = None, refresh = None):
		def _release(dummy, scene):
			try:
				current = Time.timestamp()

				# Get the previous cached data.
				result = self._cacheRetrieve(_release, dummy, scene)

				# First call will not have any results yet.
				new = False
				last = None
				if result:
					times = []
					for v1 in result.values():
						for v2 in v1:
							t = v2.get('time')
							if t: times.append(t)
					if times: last = max(times)
				else:
					new = True
					result = {Media.Movie : [], Media.Show : []}

				# Start each link in a separate thread to speed up the process.
				# Individual months are retrieved sequentially inside _releaseRetrieve().
				target = self._releaseExternalScene if scene else self._releaseExternalOfficial
				threads = [Pool.thread(target = target, kwargs = {'result' : result, 'function' : function, 'link' : link, 'domains' : domains, 'pages' : pages, 'new' : new, 'last' : last}, start = True) for link in links]
				Pool.join(instance = threads)

				# Remove duplicate entries.
				# The old cached data and the new retrievals often contain the same titles.
				lookup = (MetaTools.ProviderImdb, MetaTools.ProviderTrakt, MetaTools.ProviderTmdb, MetaTools.ProviderTvdb, 'slug')
				items1 = {Media.Movie : {}, Media.Show : {}}
				items2 = {Media.Movie : [], Media.Show : []}
				for k, v in result.items():
					for x in v:
						existing = None
						for i in lookup:
							value = x.get(i)
							if value:
								existing = items1[k].get(i + '_' + value)
								if existing: break
						if existing:
							# Add both the digital and physical dates from Trakt.
							if k == Media.Movie and x.get('origin') == MetaManager.OriginTrakt:
								existing['home'].append(x.get('time'))

							time = [existing.get('time'), x.get('time')]
							if scene: time = min(time) # Pick the first scene release, which will be closest to the actual digital/physical release date.
							else: time = self.mTools.timeClosest(times = [existing.get('time'), x.get('time')], time = current) # Use the closest time for official releases, to use either the digital or physical date.
							existing['time'] = time

							# There can mutiple episodes for the same show in the calendar.
							# Keep track of the previous aired episode, since it is needed in MetaCache._releaseOutdated().
							# Since the "time" attribute above is the closest time and can therefore be a future episodes.
							if k == Media.Show:
								time1 = x.get('time')
								season1 = x.get('season')
								episode1 = x.get('episode')

								# Set the numbers of the closest episode (past or future).
								if time == x.get('time'):
									existing['season'] = season1
									existing['episode'] = episode1
									if not season1 == 0: existing['closest'] = {'season' : season1, 'episode' : episode1, 'time' : time1}

								# Previously aired episode.
								previous = existing.get('previous')
								time2 = previous.get('time')
								season2 = previous.get('season')
								episode2 = previous.get('episode')
								if time1 <= current:
									if not season2 is None and not season1 is None:
										replace = False
										if not episode2 is None and not episode1 is None:
											if (season1 > season2) or (season1 == season2 and episode1 > episode2) or (season1 == season2 and episode1 < episode2 and time2 > current): replace = True
										else:
											if (season1 > season2) or (season1 <= season2 and time2 > current): replace = True
										if replace: existing['previous'] = {'season' : season1, 'episode' : episode1, 'time' : time1}

								# Last known episode. Might not have aired yet.
								last = existing.get('last')
								season2 = last.get('season')
								episode2 = last.get('episode')
								if not season2 is None and not season1 is None:
									replace = False
									if not episode2 is None and not episode1 is None:
										if (season1 > season2) or (season1 == season2 and episode1 > episode2): replace = True
									else:
										if (season1 > season2): replace = True
									if replace: existing['last'] = {'season' : season1, 'episode' : episode1, 'time' : time1}
						else:
							# Add both the digital and physical dates from Trakt.
							if k == Media.Movie and x.get('origin') == MetaManager.OriginTrakt:
								x['home'] = [x.get('time')]

						 	# More info in the comments above.
							elif k == Media.Show:
								base = {'season' : x.get('season'), 'episode' : x.get('episode'), 'time' : x.get('time')}
								x['previous'] = Tools.copy(base)
								x['closest'] = Tools.copy(base)
								x['last'] = Tools.copy(base)

							items2[k].append(x)
							for i in lookup:
								items1[k][i + '_' + value] = x
				result = items2

				# Remove old entries to save storage space.
				limitMovie = current - 63115200 # 2 years. Higher, since movies can have longer periods between the cinema and home release dates.
				limitShow = current - 39447000 # 1.25 year. Lower, since a new season can already arrive within a year.
				for k, v in result.items(): result[k] = [i for i in v if (i.get('time') or 0) > (limitMovie if k == Media.Movie else limitShow)]

				# Limit the maximum number of items in the lookup table, to reduce storage space and processing time.
				# Older values already get removed if they have an old date.
				# But in case there is a bug, or simply many releases within a year, that makes the lookup table grow continuously.
				# Keep the limit high, since further reductions are done when the lookup table is created.
				limit = 7500
				for k, v in result.items():
					values = Tools.listSort(v, key = lambda x : x['time'], reverse = True)
					result[k] = values[:limit]

				return result
			except: Logger.error()
			return None

		# Official: release dates are added ahead of time, often even a month into the future. Hence, do not refresh every day.
		# Scene: release are added on a daily basis. Hence, refresh every day.
		# Add the function ID, so that the cache is unique for each child function that calls this.
		scene = MetaManager.OriginScene in repr(function).lower()
		if cache is None: cache = cache.TimeoutDay1 if scene else Cache.TimeoutDay3

		return self._cacheTimeout(cache, refresh, _release, self.mCache.id(function), scene)

	def _releaseExternalOfficial(self, result, function, link, domains, pages, new, last):
		try:
			# A page has a month of releases.
			maximum = pages
			pages = 2
			if new:
				# If never retrieved before, get a full year of releases (plus next month).
				pages = 13
			elif last:
				# If not refreshed in a long time, get more months.
				last = abs(Time.timestamp() - last)
				last = int(last / 2628000)
				pages = max(2, min(6, last))
			if maximum: pages = min(pages, maximum)

			year = Time.year()
			month = Time.month() + 1 # Start at next/future month.
			if month > 12:
				year += 1
				month = 1

			type = None
			if Tools.isDictionary(link):
				type = link.get('type')
				link = link.get('link')

			for i in range(pages):
				success = function(result = result, link = link, year = year, month = month, type = type)
				if not success: break # If a request fails, do not continue to the next month.
				month -= 1
				if month < 1:
					year -= 1
					month = 12
		except: Logger.error()

	def _releaseExternalScene(self, result, function, link, domains, pages, new, last):
		try:
			page = 1
			domain = None

			# A page has 1 - 1.5 days of releases.
			maximum = pages
			pages = 2
			if new:
				# If never retrieved before, get more pages.
				pages = 20
			elif last:
				# If not refreshed in a long time, get more pages.
				last = abs(Time.timestamp() - last)
				last = int(last / 86400)
				pages = max(2, min(15, last))
			if maximum: pages = min(pages, maximum)

			type = None
			if Tools.isDictionary(link):
				type = link.get('type')
				link = link.get('link')

			for i in range(pages):
				success = False

				# Try different subdomains in case one is down.
				# If a previous call worked with a specific domain, stick to that domain.
				if not domains:
					success = function(result = result, link = link, page = page, type = type)
				elif domain:
					success = function(result = result, link = link % domain, page = page, type = type)
				else:
					for j in domains:
						success = function(result = result, link = link % j, page = page, type = type)
						if success:
							domain = j
							break

				if not success: break # If a request fails with all subdomains, do not continue to the next month.
				page += 1
		except: Logger.error()

	def _releaseExternalProcess(self, result, media, name, time, type = None):
		if name and time:
			if (
				Regex.match(data = name, expression = r'[\s\.\-\_\[\(]((?:1080|2160|3160|4096|4320)[ip]?|[468]k|uhd|blu.?ray|(?:bd|dvd)(?:r|.?rip)|web(?:.?(?:rip|dl))?)(?:$|[\s\.\-\_\]\)])', cache = True) # Must be HD releases.
				and not Regex.match(data = name, expression = r'[\s\.\-\_\[\(]((?:(?:hd|dvd|bd).?)?(?:cam|scr|tc|tele.?cine|ts|tele.?sync)(?:.?rip)?)(?:$|[\s\.\-\_\]\)])', cache = True) # Must not be CAM/SCR/TS/TC releases.
				and not Regex.match(data = name, expression = r'[\s\.\-\_\[\(](hc|dub(?:bed|bing)?|pcm|theater|theatre|record(?:ing|ed)?)(?:$|[\s\.\-\_\]\)])', cache = True) # Must not be HC/dubbed/PCM/theater releases. Eg: Nuremberg 2025 1080p Theater HEVC PCM 5.1-NaNi
				and not Regex.match(data = name, expression = r'[\s\.\-\_\[\(](s\d+(?:e\d+))(?:$|[\s\.\-\_\]\)])', cache = True) # Must not be shows (present in the x264 category of corrupt-net.org). Most of then are in any case old or German/Dutch releases.
			):
				# Update: Now do very strict matching of movie scene releases.
				# If there is an improper scene release that is detected as a proper HD release, but contains some keyword that is not in the regex above, the scene date is added as a digital release date and can mess things up.
				# Eg: Nuremberg 2025 1080p Theater HEVC PCM 5.1-NaNi
				# Eg: Previously the "Theater" keyword was not detected. Hence, this date was added as a digital date 2 months before the actual digital release. Now the movie shows up in Arrivals way too early.
				# Hence, do a stricter match and only allow filenames that overwhelmingly point to a proper HD release.
				# This will reduce the total detected scene titles, but this is more accurate and should not be a problem, since Trakt now has a proper streaming calendar with more accurate dates.
				# If this still allows improper titles to slip through, add this to _releaseAssemble() where the movie index list is determined:
				#	if origin == MetaManager.OriginScene: index = [3] # Add this line.
				#	elif type == MetaTools.TimePremiere: index = [0]
				#	elif type in MetaTools.TimesCinema: index = [1]
				#	elif type in MetaTools.TimesHome: index = [2]
				#	else: index = [2]
				# This will therefore not add scene dates as digital/physical dates anymore, but rather as an unknown date. This would essentially remove the scene dates from being used in release() and only rely on Trakt and Official calendars.
				allow = True
				if media == Media.Movie:
					allow = False
					count = 0
					expressions = [
						r'[\s\.\-\_\[\(](?:hdr(?:[\s\.\-\_]?\d+(?:\+|plus)?)?|dv|dolby.?vision)(?:$|[\s\.\-\_\]\)])', # HDR/DV.
						r'[\s\.\-\_\[\(](?:(?:2160|3160|4096|4320)[ip]?|[468]k)(?:$|[\s\.\-\_\]\)])', # 4K+ and not 1080p.
						r'[\s\.\-\_\[\(](?:uhd|blu.?ray|(?:bd|dvd)(?:r|.?rip)|web(?:.?(?:rip|dl))?)(?:$|[\s\.\-\_\]\)])', # Disk/web rip.
						r'[\s\.\-\_\[\(](?:atmos|7\.1)(?:$|[\s\.\-\_\]\)])', # HQ audio.
					]
					for expression in expressions:
						if Regex.match(data = name, expression = expression, cache = True):
							count += 1
							if count >= 2: # Must match at least 2 of the expressions.
								allow = True
								break

				if allow:
					match = Regex.extract(data = name, expression = r'\s*(.*?)[\s\.\-\_\[\(]*((?:19|2[01])\d{2})(?:$|[\s\.\-\_\]\)])', group = None, all = True, cache = True) # Year.
					if match:
						match = match[0]
						title = match[0].replace('.', ' ')

						# Bleach Thousand Year Blood War Vol 01 D01
						# Im Quitting Heroing Vol 02
						# The Dreaming Boy Is a Realist D01
						new = Regex.extract(data = title, expression = r'(.*?)\s*((?:vol(?:ume|\.)?)\s*\d+|d(?:is[ck])?\s*\d+)', cache = True)
						if new: title = new

						year = int(match[1])
						self._releaseExternalAdd(result = result, media = media, title = title, year = year, time = time, type = type, origin = MetaManager.OriginScene)

	def _releaseExternalAdd(self, result, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, time = None, type = None, extra = None, origin = None):
		if (imdb or tmdb or tvdb or trakt or title) and time:

			# Official2 and Official3.
			if not media and title:
				# Shangri-La Frontier: Season 1, Part 1
				# Shameless: The Complete Series
				# Frasier - Season Two
				# The Unwanted Undead Adventurer: The Complete Season
				# The Penguin: The Complete First Season
				# The Last of Us: The Complete First Season 4K (SteelBook)
				# Jujutsu Kaisen: Season 2 - Shibuya Incident
				# Star Trek: Lower Decks: The Final Season
				# One Piece: Season 14 Voyage 3
				# All Creatures Great and Small Season 5
				# The Rising of the Shield Hero: Season Three
				# Welcome to Demon School Iruma-kun: Season 2
				# he Unwanted Undead Adventurer: The Complete Season
				# All Creatures Great and Small: Season 5
				# Spy x Family: Season Two
				# A Sign of Affection: The Complete Season
				# The Apothecary Diaries: Season 1, Part 2
				# The 100 Girlfriends Who Really, Really, Really, Really, Really Love You: Season 1
				# Jujutsu Kaisen: Season 2 - Hidden Inventory/Premature Death
				# Chained Soldier: Season 1 Complete Collection
				# My Teen Romantic Comedy SNAFU: Complete Three Season Collection
				# Bucchigiri?!: The Complete Season
				# Doctor Who: Sylvester McCoy: Complete Season Two
				# Tales of Wedding Rings: Season 1
				# Many more formats.
				if Regex.match(data = title, expression = r'(seasons?|series?)', cache = True):
					media = Media.Show

					# Sometimes the season is only given in the extended/extra attributes.
					for i in [title, extra]:
						if i:
							if not season:
								extract = Regex.extract(data = title, expression = r'(?:seasons?|series?)\s*(\d+)(?![a-z])', cache = True)
								if extract: season = int(extract)
							if not season:
								extract = Regex.extract(data = title, expression = r'(?:(?:seasons?|series?)\s*(one|two|three|four|five|six|seven|eight|nine|ten)|(one|two|three|four|five|six|seven|eight|nine|ten|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|[1-9]+(?:st|nd|rd|th))\s*(?:seasons?|series?))', cache = True)
								if extract:
									if extract == 'one' or extract == 'first' or extract == '1st': season = 1
									elif extract == 'two' or extract == 'second' or extract == '2nd': season = 2
									elif extract == 'three' or extract == 'third' or extract == '3rd': season = 3
									elif extract == 'four' or extract == 'fourth' or extract == '4th': season = 4
									elif extract == 'five' or extract == 'fifth' or extract == '5th': season = 5
									elif extract == 'six' or extract == 'sixth' or extract == '6th': season = 6
									elif extract == 'seven' or extract == 'seventh' or extract == '7th': season = 7
									elif extract == 'eight' or extract == 'eighth' or extract == '8th': season = 8
									elif extract == 'nine' or extract == 'ninth' or extract == '9th': season = 9
									elif extract == 'ten' or extract == 'tenth' or extract == '10th': season = 10
							if season: break

					# Remove trailing descriptions.
					# Star Trek: Section 31 [DVD]
					title = Regex.remove(data = title, expression = r'(\s*(?:[\:\-]\s*(?:(?:the)?\s*(?:final|last|full|complete|one|two|three|four|five|six|seven|eight|nine|ten|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|[1-9]+(?:st|nd|rd|th))\s*)*(?:seasons?|series?)|\s+(?:seasons?|series?)\s*\d+).*)$', cache = True)
				else:
					media = Media.Movie

				# Remove trailing descriptions.
				# The Wages of Fear 4K
				# Den of Thieves: 2-Film Collection 4K (SteelBook)
				# Djabe & Steve Hackett: Freya - Arctic Jam (DigiPack)
				# Star Trek: Lower Decks - The Complete Series (SteelBook)
				# Last of the Red Hot Lovers (Mediabook)
				# Jethro Tull: Curious Ruminant (Hardback Book)
				# Cheyenne: The Complete Series
				# The Divergent Series: 3-Film Collection
				# Den of Thieves: 2-Film Collection 4K (SteelBook)
				# The World Is Still Beautiful: Complete Collection
				# Morning Show Mysteries: Complete Movie Collection
				# Hallmark Dayspring 2-Movie Collection
				# Star Trek: Section 31 [DVD]
				title = Regex.remove(data = title, expression = r'([\s\-\_\:]+(?:\s*(?:[\:\-]|\d+\-)\s*(?:4k|\([a-z\d\s\-]+\)|(?:the\s*)?(?:(?:\d+|one|two|three|four|five)[\-\s])?(?:(?:final|last|first|second|third|fourth|fifth|complete|movie|film|collection|series?|seasons?)\s)+)|4k|\([a-z\d\s\-]+\)|(?:series?|seasons?)\s\d|[\[\(]?(?:dvd|blur.?ray)[\]\)]?).*)$', cache = True)

			if Media.isSerie(media) or not year or year >= (Time.year() - 3): # Do not add old titles for movies.
				item = {'origin' : origin or MetaManager.OriginOfficial, 'time' : time, 'type' : type}

				ids = []
				if imdb: ids.append((MetaTools.ProviderImdb, imdb))
				if trakt: ids.append((MetaTools.ProviderTrakt, trakt))
				if tmdb: ids.append((MetaTools.ProviderTmdb, tmdb))
				if tvdb: ids.append((MetaTools.ProviderTvdb, tvdb))
				for i in ids: item[i[0]] = i[1]

				if title:
					item['slug'] = Tools.replaceNotAlphaNumeric(title).lower()
					item['title'] = title

				if year: item['year'] = year
				if not season is None: item['season'] = season
				if not episode is None: item['episode'] = episode

				result[media].append(item)

	# Trakt DVD/Streaming Calendar.
	# Is already part of the Arrivals, but add here again as a backup to create a full lookup table. Plus this includes future months not in Arrivals.
	def _releaseExternalOfficial1(self, refresh = None):
		def _release(result, link, year, month, type = None):
			media = link
			serie = Media.isSerie(media)

			valid = True
			error = None

			start = '%d-%02d-01' % (year, month)
			month += 1
			if month > 12:
				year += 1
				month = 1
			end = '%d-%02d-01' % (year, month)

			if serie:
				releases = [
					# Only shows that the user is watching, otherwise there will be too many episodes added.
					{'media' : Media.Episode, 'release' : MetaTrakt.ReleaseNew, 'date' : MetaTools.TimePremiere, 'user' : True},
				]
			else:
				releases = [
					{'media' : media, 'release' : MetaTrakt.ReleaseDigital, 'date' : MetaTools.TimeDigital, 'user' : False},
					{'media' : media, 'release' : MetaTrakt.ReleasePhysical, 'date' : MetaTools.TimePhysical, 'user' : False},
				]

			# future: allow future dates.
			# duplicate: allow multiple episodes from the same show released in the same period.
			for release in releases:
				data = MetaTrakt.instance().release(media = release['media'], release = release['release'], user = release['user'], date = [start, end], future = True, duplicate = True)
				try:
					for i in data:
						try:
							time = i['time'][release['date']]
							if time: self._releaseExternalAdd(origin = MetaManager.OriginTrakt, result = result, media = media, imdb = i.get('imdb'), tmdb = i.get('tmdb'), tvdb = i.get('tvdb'), trakt = i.get('trakt'), title = i.get('tvshowtitle') or i.get('title'), year = i.get('tvshowyear') or i.get('year'), season = i.get('season'), episode = i.get('episode'), time = time, type = release['date'])
						except: error = 'ITEM'
				except: error = 'ITEMS'

			if error and self.mDeveloper: Logger.log('RELEASE INVALID OFFICIAL1 [%s]: %s' % (error, media))
			return valid

		links = [Media.Movie, Media.Show]
		return self._releaseExternalAssemble(function = _release, links = links, refresh = refresh, cache = Cache.TimeoutDay1)

	# https://dvdsreleasedates.com
	# Digital and disk releases with IMDb ID, but not that many titles listed.
	def _releaseExternalOfficial2(self, refresh = None):
		def _release(result, link, year, month, type):
			from lib.modules.parser import Parser
			from lib.modules.convert import ConverterTime

			valid = False
			error = None

			networker = Networker()
			link = networker.linkJoin(link, year, month) + '/' # Must end with a /.
			data = networker.requestText(link = link)

			# Should not have Cloudflare protection. But still check in case it is added later on.
			if networker.responseErrorType() == Networker.ErrorCloudflare:
				error = 'CLOUDFLARE'
			elif data:
				data = Parser(data = data, parser = Parser.ParserHtml5) # Use HTML5, since there are some bugs in the markup.
				if data:
					data = original = data.find(class_ = 'fieldtable')
					if data:
						valid = True
						data = data.find_all(class_ = 'fieldtable-inner')
				if data:
					for values in data:
						try:
							time = values.find(class_ = 'reldate').find(text = True) # Not nested text.
							time = Regex.extract(data = time, expression = r'(\w+\s+\d.*?\d{4})', cache = True) # Remove weekday.
							time = time = ConverterTime(time, format = ConverterTime.FormatDateAmerican, utc = True).timestamp()
							for value in values.find_all(class_ = 'dvdcell'):
								try:
									imdb = value.find(class_ = 'imdblink').find('a')['href']
									imdb = Regex.extract(data = imdb, expression = r'\/(tt\d+)')
									try: title = value.find_all('a')[1].text
									except: title = None
									self._releaseExternalAdd(result = result, imdb = imdb, title = title, time = time, type = type)
								except:
									Logger.error()
									error = 'ITEM'
						except:
							Logger.error()
							error = 'ITEMS'
				else:
					# Future months sometimes do not have any data, showing this error:
					#	 Sorry, nothing currently available. Check back often for updates.
					# Do not mark this as a struct error.
					try: text = original.text
					except: text = None
					if not original or not text or not 'nothing currently available' in text.lower(): error = 'STRUCT'
			else: error = 'DATA'

			if error and self.mDeveloper: Logger.log('RELEASE INVALID OFFICIAL2 [%s]: %s' % (error, link))
			return valid

		# Must have www subdomain, otherwise always redirects to the current month.
		links = [
			{'type' : MetaTools.TimeDigital, 'link' : 'https://www.dvdsreleasedates.com/digital-releases/'}, # Digital release dates.
			{'type' : MetaTools.TimePhysical, 'link' : 'https://www.dvdsreleasedates.com/releases/'}, # BluRay and 4K release dates.
		]
		return self._releaseExternalAssemble(function = _release, links = links, refresh = refresh, cache = Cache.TimeoutDay3)

	# https://blu-ray.com
	# Digital and disk releases without IMDb ID and only a title, but has more titles listed.
	def _releaseExternalOfficial3(self, refresh = None):
		def _release(result, link, year, month, type):
			from lib.modules.tools import Converter
			from lib.modules.convert import ConverterTime

			valid = False
			error = None

			networker = Networker()
			link = networker.linkCreate(link = link, parameters = {'year' : year, 'month' : month})
			data = networker.requestText(link = link)

			# Should not have Cloudflare protection. But still check in case it is added later on.
			if networker.responseErrorType() == Networker.ErrorCloudflare:
				error = 'CLOUDFLARE'
			elif data:
				try:
					data = str(data)

					# Even if there is no titles listes (eg next month's future releases), still check if the page is correct.
					valid = Regex.match(data = data, expression = r'<a\s.*?title\s*=\s*[\'\"]blu\-ray\.com', cache = True)

					values = Regex.extract(data = data, expression = r'movies\[\d.*?(\{.*?\})\s*;', group = None, all = True, cache = True)
					if values:
						for value in values:
							try:
								if value:
									# Double quotes inside a string.
									# Eg: 'Limited Box Set, 2 180g LP Gatefold, 3 exclusive 10" Vinyl records, XL T-Shirt, Exclusive Plectrums, Lanyard, Art Print'
									value = Regex.replace(data = value, expression = r'"', replacement = '\\\\\\"', all = True, cache = True)

									# Strings are in escaped single quotes.
									value = Regex.replace(data = value, expression = r'(:\s*)\\\\\'(.*?)\\\\\'([\,\]\}])', replacement = r'\1"\2"\3', all = True, cache = True)

									# Replace escaped quotes internal to string.
									for i in range(3): value = Regex.replace(data = value, expression = r'(\\\\\')', replacement = '\'', all = True, cache = True)

									# The keys do not have quotes.
									# Do multiple times, otherwise not all keys are quoted.
									for i in range(3): value = Regex.replace(data = value, expression = r'([\[\{]\s*|(?:\"|:\s*\d+)\s*,\s*)((?=\D)\w+):', replacement = r'\1"\2":', all = True, cache = True)

									# Unescape hex-escaped characters in the string.
									# Eg: Arz\xe9 -> Arzé
									value = Converter.unicodeUnescape(value)

									original = value
									value = Converter.jsonFrom(value)
									if value:
										title = value.get('title')
										year = value.get('year')
										year = int(year) if year else None
										time = ConverterTime(value.get('releasedate'), format = ConverterTime.FormatDateAmerican, utc = True).timestamp()
										extra = value.get('extended')
										self._releaseExternalAdd(result = result, title = title, year = year, time = time, type = type, extra = extra)
									else: error = 'ITEM'
							except:
								Logger.error()
								error = 'ITEM'
					else: error = 'ITEMS'
				except:
					Logger.error()
					error = 'STRUCT'
			else: error = 'DATA'

			if error and self.mDeveloper: Logger.log('RELEASE INVALID OFFICIAL3 [%s]: %s' % (error, link))
			return valid

		links = [
			{'type' : MetaTools.TimeDigital, 'link' : 'https://www.blu-ray.com/digital/releasedates.php'}, # Digital release dates (medium).
			{'type' : MetaTools.TimePhysical, 'link' : 'https://www.blu-ray.com/movies/releasedates.php'}, # BluRay and 4K release dates (many).
			{'type' : MetaTools.TimePhysical, 'link' : 'https://www.blu-ray.com/dvd/releasedates.php'}, # DVD release dates (few).
		]
		return self._releaseExternalAssemble(function = _release, links = links, refresh = refresh, cache = Cache.TimeoutDay3)

	# https://rlsbb.cc
	def _releaseExternalScene1(self, refresh = None):
		def _release(result, link, page, type):
			from lib.modules.parser import Parser
			from lib.modules.convert import ConverterTime

			valid = False
			error = None

			networker = Networker()
			link = link if page == 1 else networker.linkJoin(link, 'page', page) # First page cannot have a page number.
			data = networker.requestText(link = link, cookies = {'serach_mode' : 'light'}) # Add light-search cookie, otherwise the blog HTML is returned.

			# Should not have Cloudflare protection. But still check in case it is added later on.
			if networker.responseErrorType() == Networker.ErrorCloudflare:
				error = 'CLOUDFLARE'
			elif data:
				data = Parser(data = data, parser = Parser.ParserHtml5)
				if data:
					data = data.find(id = 'resultdiv')
					if data:
						valid = True
						try:
							for value in data.find_all('tr'):
								try:
									cells = value.find_all('td')
									name = cells[-1].find('a').text
									time = ConverterTime(cells[0].text, format = ConverterTime.FormatDate, utc = True).timestamp()
									self._releaseExternalProcess(result = result, media = Media.Movie, name = name, time = time, type = type)
								except:
									Logger.error()
									error = 'ITEM'
						except:
							Logger.error()
							error = 'ITEMS'
					else: error = 'STRUCT'
				else: error = 'PARSE'
			else: error = 'DATA'

			if error and self.mDeveloper: Logger.log('RELEASE INVALID SCENE1 [%s]: %s' % (error, link))
			return valid

		domains = ['cc', 'to', 'com', 'ru']
		links = [{'type' : MetaTools.TimeDigital, 'link' : 'https://search.rlsbb.%s/category/movies/'}]
		return self._releaseExternalAssemble(function = _release, links = links, domains = domains, refresh = refresh, cache = Cache.TimeoutDay1)

	# https://predb.me
	def _releaseExternalScene2(self, refresh = None):
		def _release(result, link, page, type):
			from lib.modules.parser import Parser

			valid = False
			error = None

			networker = Networker()
			link = networker.linkCreate(link, parameters = {'page' : page})
			data = networker.requestText(link = link)

			# Sometimes Cloudflare blocks the request.
			if networker.responseErrorType() == Networker.ErrorCloudflare:
				error = 'CLOUDFLARE'
			elif data:
				data = Parser(data = data, parser = Parser.ParserHtml5)
				if data:
					data = data.find(class_ = 'pl-body')
					if data:
						valid = True
						try:
							for value in data.find_all(class_ = 'post'):
								try:
									name = value.find(class_ = 'p-title').find(text = True)
									time = int(value.find(class_ = 'p-time')['data'])
									self._releaseExternalProcess(result = result, media = Media.Movie, name = name, time = time, type = type)
								except:
									Logger.error()
									error = 'ITEM'
						except:
							Logger.error()
							error = 'ITEMS'
					else: error = 'STRUCT'
				else: error = 'PARSE'
			else: error = 'DATA'

			if error and self.mDeveloper: Logger.log('RELEASE INVALID SCENE2 [%s]: %s' % (error, link))
			return valid

		links = [{'type' : MetaTools.TimeDigital, 'link' : 'https://predb.me/?cats=movies'}]
		return self._releaseExternalAssemble(function = _release, links = links, refresh = refresh, cache = Cache.TimeoutDay1)

	# https://pre.corrupt-net.org
	# Does not return many titles, since most are very old or episodes.
	def _releaseExternalScene3(self, refresh = None):
		def _release(result, link, page, type):
			from lib.modules.parser import Parser
			from lib.modules.convert import ConverterTime

			valid = False
			error = None

			networker = Networker()
			link = networker.linkCreate(link = link, parameters = {'page' : page}) # When adding a page number, the data is returned as semi-strcutured corrupt HTML.
			data = networker.requestText(link = link)

			# Should not have Cloudflare protection. But still check in case it is added later on.
			if networker.responseErrorType() == Networker.ErrorCloudflare:
				error = 'CLOUDFLARE'
			elif data:
				valid = data.startswith('<tr')
				if valid:
					data = Parser(data = data, parser = Parser.ParserHtml) # Do not use HTML5, otherwise the corrupt HTML is rearrnaged.
					if data:
						try:
							for value in data.find_all('tr'):
								try:
									cells = value.find_all('td')
									name = cells[1].find(text = True) # Not nested text.
									time = ConverterTime(cells[-1].find(text = True), format = ConverterTime.FormatDateTime, utc = True).timestamp()
									self._releaseExternalProcess(result = result, media = Media.Movie, name = name, time = time, type = type)
								except:
									Logger.error()
									error = 'ITEM'
						except:
							Logger.error()
							error = 'ITEMS'
					else: error = 'PARSE'
				else: error = 'STRUCT'
			else: error = 'DATA'

			if error and self.mDeveloper: Logger.log('RELEASE INVALID SCENE3 [%s]: %s' % (error, link))
			return valid

		# Other types available under the "Filters" toggle on https://pre.corrupt-net.org/live.php
		# Limit the maximum number of pages, since most results are useless in any case and only waste time.
		links = [
			{'type' : MetaTools.TimePhysical, 'link' : 'https://pre.corrupt-net.org/search.php?search=type:bluray'},
			{'type' : MetaTools.TimeDigital, 'link' : 'https://pre.corrupt-net.org/search.php?search=type:x264'},
			#{'type' : MetaTools.TimePhysical, 'link' : 'https://pre.corrupt-net.org/search.php?search=type:dvdr'}, # Mostly series, old releases, or German/Dutch/etc releases.
		]
		return self._releaseExternalAssemble(function = _release, links = links, pages = 3, refresh = refresh, cache = Cache.TimeoutDay1)

	def releasing(self):
		if self.mReleaseMedia: return True
		return False

	def releasingMedia(self):
		return self.mReleaseMedia

	##############################################################################
	# PROGRESS
	##############################################################################

	def progress(self, media = None, niche = None, progress = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None, detail = None, quick = None, reload = None, refresh = None, more = None, **parameters):
		if not progress: progress = MetaTools.ProgressDefault # Important for the cache call in content().
		return self.content(content = MetaManager.ContentProgress, media = media, niche = niche, progress = progress, unknown = unknown, filter = filter, sort = sort, order = order, page = page, limit = limit, detail = detail, quick = quick, reload = reload, refresh = refresh, more = more, **parameters)

	def _progress(self, media = None, niche = None, progress = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None, refresh = None, **parameters):
		try:
			if media is None or Media.isMixed(media):
				data1 = self._progress(media = Media.Show, limit = 0.5, niche = niche, progress = progress, unknown = unknown, filter = filter, sort = sort, order = order, page = page, refresh = refresh, **parameters)
				data2 = self._progress(media = Media.Movie, limit = 0.5, niche = niche, progress = progress, unknown = unknown, filter = filter, sort = sort, order = order, page = page, refresh = refresh, **parameters)
				if not data1: data1 = {}
				if not data2: data2 = {}
				result = data1 or data2
				if result:
					result.update({
						'limit'		: (data1.get('limit') or 0) + (data2.get('limit') or 0),
						'more'		: (data1.get('more') or 0) + (data2.get('more') or 0),
						'items'		: Tools.listInterleave(data1.get('items') or [], data2.get('items') or []),
					})
					return result
				return None

			data = None
			time = self._cacheTime(self._progressAssemble, media = media)

			# Try to avoid the cache function execution (refreshing in the background) if we are reloading mixed menus.
			# More info in reload().
			if self.reloadingMixed() or self.releasing(): data = self._cacheRetrieve(self._progressAssemble, media = media)

			# NB: Do not pass in any parameters to the cache call that might cause a separate cache entry to be saved.
			# Eg: niche, progress, filter, sort, order.
			# It might seem intuitive to pass in the niche, or at least the progress type or sorting, such as for ProgressRewatch which is sorted in the reverse order compared to the other progress menus.
			# However, this would establish a separate smart list which has to be updated over time. This should not be a huge issue, since these could quickly retrieve already cached metadata that other progress menus have loaded.
			# But this would mean that every type of progress menu, plus every niche, would create a larger list in the cache, and would each have to update their smart-list individually.
			# A better way is to create a SINGLE progress smart-list (technically two, one for movies, one for shows), containing all progress types, niches etc.
			# Then we only have to maintain a single list, which saves cache disk space, and if the list is updated from eg reload(), it does it for all progress menus.
			# We then filter and sort them outside below, the cache call, which should not take that long, even for larger Trakt histories.
			# This might not be perfect all the time. For instance, ProgressRewatch will only be accurate once a lot of items were smart-loaded, and would initially not have good sorting, since it is sorted in reverse and the first items in this list might not have been smart-loaded for dates yet.
			# However, overall this should improve performance, save disk space, and make things easier.
			# NB: Do not call this when executing release(), otherwise it might deadlock. Eg: MetaManager.progress() -> MetaCache._releaseInitialize() -> MetaManager.release() -> MetaManager.progress() -> ...
			if not data and not self.releasing(): data = self._cache('cacheShort', refresh, self._progressAssemble, media = media)

			if data:
				items = data.get('items')
				if items:
					result = self._progressProcess(items = items, media = media, niche = niche, progress = progress, unknown = unknown, filter = filter, sort = sort, order = order, page = page, limit = limit)

					# Retrieve more detailed metadata, even if the above list is loaded from cache.
					# Do not execute if we only reload the cached menu from reload(), otherwise there are too many requests.
					if not self.reloading() and not self.releasing() and not self.mModeAccelerate: self._metadataSmartReload(media = media, content = MetaManager.ContentProgress, cache = time, **data)

					result.update({
						'provider'	: MetaTrakt.id(),
						'progress'	: progress,
						'next'		: MetaManager.Smart,
						'more'		: len(result.get('items')),

						# Saves a lot of time and is not needed for the menu, is it?
						# Previously MetaTools.submenuNumber() needed the pack to calculate the negative history number offset, but this is now only done once the episode is actually opened in the menu.
						# Maybe there is some other function in MetaTools or elsewhere that requires the pack - keep your eyes open for things that do not work.
						# Update (2025-01): We actually need the season/episode counts for MetaTools.itemPlayback() to show the correct watched/progress icons for Progress menus where episodes are listed as shows.
						# But instead we use the summarized pack data added to the "smart" dictionary.
						'pack'		: False,
					})
					return result
		except: Logger.error()
		return None

	def _progressAssemble(self, media):
		timer = self._jobTimer()
		from lib.modules.playback import Playback

		# Ratings are only needed for ProgressRewatch sorting, but retrieve them, since all progress types are created from the same data.
		# Use "rating=None" to retrieve the show rating instead of the episode rating.
		itemsNew = Playback.instance().items(media = media, history = True, progress = True, rating = None)

		# Retrieve the current smart-list from cache. To be updated.
		itemsCurrent = self._cacheRetrieve(self._progressAssemble, media = media)
		itemsCurrent = itemsCurrent.get('items') if itemsCurrent else None

		# SortLocal works for all progress menus, except ProgressRewatch, which sorts in reverse order. But this will be done later on.
		return self._metadataSmart(media = media, items = itemsCurrent, new = itemsNew, sort = MetaTools.SortLocal, remove = True, detail = False, timer = timer, content = MetaManager.ContentProgress)

	def _progressProcess(self, items, media = None, niche = None, progress = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None):
		# All the filtering and sorting here should only take a few milliseconds.
		# It takes about 20ms for Playback.instance(), but this has to be created in any case later on when the menu is loaded.

		# Do not use ProgressPartial for the main Progress menu.
		# For movies it might be fine to exclude those that were watched <1%.
		# But for shows, the user might start a new show, watch 50% of S01E01 and pause/stop. It should then appear on the Progress menu the next load if the user wants to continue the episode the next day.
		if not progress: progress = MetaTools.ProgressDefault

		if unknown is None: unknown = True
		if limit is None: limit = self.limit(media = media, content = MetaManager.ContentProgress)
		elif Tools.isFloat(limit): limit = int(limit * self.limit(media = media, content = MetaManager.ContentProgress))

		# The main progress menu is not filtered at all, but strictly sorted using advanced attributes.
		# The sub progress menus (under Favorites), are strictly filtered, but are then lightly sorted simply based on Trakt user dates (most recent watched/rated/scrobbled/collected dates).
		if sort is None:
			if progress == MetaTools.ProgressDefault: sort = MetaTools.SortLocal
			elif progress == MetaTools.ProgressRewatch: sort = MetaTools.SortRewatch
			else: sort = MetaTools.SortUsed

		# Filter niche Progress menus, like Anime, Originals, and Minis.
		# Filter by the niche list itself, not the derived filters, since this is faster are more reliable than possible incomplete detailed metadata attributes, like secondary companies or genres.
		filter = self._processorNiche(niche = niche, filter = filter, generic = True)

		if items:
			# Filter by progress type.
			# The main progress menu is not filtered, only sorted.
			if not progress ==  MetaTools.ProgressDefault: items = self.mTools.filterProgress(items = items, include = progress)

			# Filter directly by niche, and not the filters create from the niche.
			# Because the cache porgress list has reduced metadata, and not all prarameters might be available here, although most should.
			# Not all items can be filtered out here, if they have not detailed metadata yet.
			# Leave the final sorting to content() after the detailed metadata was retrieved.
			# This should only take a few ms, even for large lists.
			niched = filter.get(MetaTools.FilterNiche) # Only use the company ID, not the company type, otherwise too few titles might be returned.
			if niched:
				# Do not allow unknowns when a niche is specified.
				# Otherwise all shows which were not smart-loaded yet, are added to it.
				# Eg: multi-season shows are listed under Minis Progress menu, just because they do not smart-loaded yet.
				# Even if some are filtered out, after a little while the smart-list will be full enough to list more under the niche menus.
				items = self.mTools.filterNiche(items = items, include = niched, unknown = unknown)

			# Sort here, since this could not be done by metadataSmart(), since it does not know the sort/order parameters.
			if sort or order: items = self._process(media = media, items = items, sort = sort, order = order, page = False, limit = False)

			# The series Rewatch progress menu should be displayed as a show menu and not an episode menu.
			if progress == MetaTools.ProgressRewatch and Media.isSerie(media): items = self.mTools.base(media = Media.Show, items = items)

		return {
			'items'		: items,
			'filter'	: filter,
			'sort'		: [None, sort], # Already sorted here. Only do the secondary sort in content().
			'order'		: [None, order],
			'page'		: page,
			'limit'		: limit,
		}

	##############################################################################
	# HISTORY
	##############################################################################

	def history(self, media = None, niche = None, history = None, filter = None, sort = None, order = None, page = None, limit = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		if not history: history = media
		return self.content(content = MetaManager.ContentHistory, media = media, niche = niche, history = history, filter = filter, sort = sort, order = order, page = page, limit = limit, detail = detail, quick = quick, refresh = refresh, more = more, **parameters)

	def _history(self, media = None, niche = None, history = None, filter = None, sort = None, order = None, page = None, limit = None, **parameters):
		try:
			if media:
				if limit is None:
					# Use the progress menu limit for seasons/episodes, which should be on the lower-end.
					# Since each item in the menu will load large pack data, and all seasons/episodes are from different shows and will therefore have to load its own pack.
					if media == Media.Season or media == Media.Episode: limit = self.limit(content = MetaManager.ContentProgress)
					else: limit = self.limit(media = media)

				from lib.modules.history import History
				items = History().retrieve(media = media, niche = niche, limit = limit, page = page, unique = True, load = media)

				if items:
					return {
						'items'		: items,

						'filter'	: filter,
						'sort'		: sort,
						'order'		: order,
						'page'		: page,
						'limit'		: limit,

						'history'	: history,
						'more'		: len(items) == limit,
					}
		except: Logger.error()
		return None

	##############################################################################
	# ARRIVAL
	##############################################################################

	def arrival(self, media = None, niche = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None, detail = None, quick = None, reload = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentArrival, media = media, niche = niche, unknown = unknown, filter = filter, sort = sort, order = order, page = page, limit = limit, detail = detail, quick = quick, reload = reload, refresh = refresh, more = more, **parameters)

	def _arrival(self, media = None, niche = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None, refresh = None, detail = None, **parameters):
		try:
			if media is None or Media.isMixed(media):
				data1 = self._arrival(media = Media.Show, limit = 0.5, niche = niche, unknown = unknown, filter = filter, sort = sort, order = order, page = page, refresh = refresh, **parameters)
				data2 = self._arrival(media = Media.Movie, limit = 0.5, niche = niche, unknown = unknown, filter = filter, sort = sort, order = order, page = page, refresh = refresh, **parameters)
				if not data1: data1 = {}
				if not data2: data2 = {}
				result = data1 or data2
				if result:
					items = Tools.listInterleave(data1.get('items') or [], data2.get('items') or [])
					items = items[:2000] # Otherwise sorting takes too long.
					result.update({
						'limit'		: (data1.get('limit') or 0) + (data2.get('limit') or 0),
						'more'		: len(items),
						'items'		: items,
					})
					return result
				return None

			data = None
			time = self._cacheTime(self._arrivalAssemble, media = media, niche = niche)

			# Show a notification if an Arrivals menu, or a niche Arrivals menu is created for the first time, since it can make 100+ requests which can take a while.
			if not time: self._jobUpdate(media = media, none = 100, content = MetaManager.ContentArrival)

			# Try to avoid the cache function execution (refreshing in the background) if we are reloading mixed menus.
			# More info in reload().
			if self.reloadingMixed() or self.releasing(): data = self._cacheRetrieve(self._arrivalAssemble, media = media, niche = niche)

			# NB: Do not call this when executing release(), otherwise it might deadlock. Eg: MetaManager.arrival() -> MetaCache._releaseInitialize() -> MetaManager.release() -> MetaManager.arrival() -> ...
			if not data and not self.releasing(): data = self._cache('cacheBasic', refresh, self._arrivalAssemble, media = media, niche = niche)

			if data:
				items = data.get('items')
				if items:
					result = self._arrivalProcess(items = items, media = media, niche = niche, unknown = unknown, filter = filter, sort = sort, order = order, page = page, limit = limit, detail = detail)

					# Retrieve more detailed metadata, even if the above list is loaded from cache.
					# Do not execute if we only reload the cached menu from reload(), otherwise there are too many requests.
					if not self.reloading() and not self.releasing() and not self.mModeAccelerate: self._metadataSmartReload(media = media, content = MetaManager.ContentArrival, cache = time, **data)

					result.update({
						'next'		: MetaManager.Smart,
						'more'		: len(result.get('items')),

						# Saves a lot of time and is not needed for the menu, is it?
						# Previously MetaTools.submenuNumber() needed the pack to calculate the negative history number offset, but this is now only done once the episode is actually opened in the menu.
						# Maybe there is some other function in MetaTools or elsewhere that requires the pack - keep your eyes open for things that do not work.
						'pack'		: False,
					})
					return result
		except: Logger.error()
		return None

	def _arrivalAssemble(self, media, niche = None):
		timer = self._jobTimer()

		itemsNew = self._arrivalRetrieve(media = media, niche = niche)

		# Retrieve the current smart-list from cache. To be updated.
		itemsCurrent = self._cacheRetrieve(self._arrivalAssemble, media = media, niche = niche)
		itemsCurrent = itemsCurrent.get('items') if itemsCurrent else None

		# NB: Do not remove based on the smart list length. Eg: 1000.
		# Otherwise, every time _metadataSmart() is called, a bunch of "new" items are added.
		# At the end of _metadataSmart(), most of these items get removed again, because they are sorted to the bottom of the list (eg: olderish release or low rating/votes) and then get removed by the eg 1000 limit.
		# When _metadataSmart() is called again, these previously-removed items are not in the smart list and are therefore seen as truely "new" items.
		# Then when we smart-load titles from MetaCache, it will always load these previously-removed items, because they are seen as new.
		# This means the smart list is populated very slowley, since it always quick-cache-loads the same items on every refresh, which are then removed again at the end.
		# Instead, keep the entire year's arrivals and only remove them if they are too old.
		# Even with a few thousand titles, this should be less than 2MB storage space.
		remove = 31536000 # 1 year.

		return self._metadataSmart(media = media, items = itemsCurrent, new = itemsNew, sort = MetaTools.SortGlobal, remove = remove, detail = False, timer = timer, content = MetaManager.ContentArrival)

	def _arrivalRetrieve(self, media, niche):
		functions = None # Used in _add().

		def _votes(votes):
			return int(votes * 0.1) if niche else votes

		def _add(values, base, **parameters):
			base = Tools.copy(base)
			if parameters: base.update(parameters)
			base['origin'] = functions.get(base.get('function'))
			values.append(base)

		def _forward(year, month):
			return [year - 1, month]

		def _backward(year, month):
			date = [year - 1, month - 1]
			if date[1] < 1:
				date[0] -= 1
				date[1] = 12
			return date

		def _date(date):
			start = [date[0], date[1], 1]
			if date[1] >= 12: end = [date[0] + 1, 1, 1]
			else: end = [date[0], date[1] + 1, 1]
			start = Time.timestamp('%d-%02d-%02d' % tuple(start), format = Time.FormatDate, utc = True)
			end = Time.timestamp('%d-%02d-%02d' % tuple(end), format = Time.FormatDate, utc = True)
			return [start, end]

		def _increase(values, base, date, **parameters):
			_add(values = values, base = base, date = _date(date), **parameters)
			date[1] += 1
			if date[1] > 12:
				date[0] += 1
				date[1] = 1

		def _decrease(values, base, date, **parameters):
			_add(values = values, base = base, date = _date(date), **parameters)
			date[1] -= 1
			if date[1] < 1:
				date[0] -= 1
				date[1] = 12

		############################################
		# INITIALIZATION
		############################################

		# MOVIES
		#	Items: +-3000 (+-5000 with duplicates)
		#	Requests: 136 + niche requests
		# SHOWS
		#	Items: +-2000 (+-4500 with duplicates)
		#	Requests: 77 + niche requests

		# When using Gaia regularly for 6+ months, only 50-60% of the Arrivals have been cached.
		#	Movies: 2772 (accumulated over time) - 2429 (total at the end of the function)
		#	Shows: 3316 (accumulated over time) - 1954 (total at the end of the function)
		# Reduce the total items being retrieved to allow caching to complete earlier.
		# Reduction from the previous values is this function are marked as "reduced".

		movie = Media.isFilm(media)
		show = Media.isSerie(media)
		mini = Media.isMini(niche)

		trakt = MetaTrakt.instance().discover
		imdb = MetaImdb.instance().discover
		tmdb = MetaTmdb.instance().discover

		providers = self.provider(content = MetaManager.ContentDiscover, media = media, niche = niche)
		if not niche or mini: providers.append(MetaTools.ProviderTmdb) # At some point MetaTmdb has to be rewritten to allow proper niches.
		if mini:
			try: providers.remove(MetaTools.ProviderTrakt)
			except: pass

		functions = {
			trakt : MetaTools.ProviderTrakt,
			imdb : MetaTools.ProviderImdb,
			tmdb : MetaTools.ProviderTmdb,
		}

		items = []
		primary = []
		secondary = []
		delete = []

		durationHour12 = 43200
		durationDay3 = 259200
		durationWeek2 = 1209600
		durationWeek3 = 1814400
		durationWeek4 = 2419200
		durationMonth1 = 2628000
		durationMonth3 = 7884000
		durationMonth6 = 15768000
		durationYear1 = 31557600

		year = Time.year()
		month = Time.month()

		# Trakt and TMDb can return movies that are decades old.
		# This is because those old movies get a new 4k/BluRay release, which gives them a new release date.
		# The date parameter then applies to the new digital/physical release date and not the premiere date which can be very long ago.
		# Do not do this for shows, since there can be new episodes released for very old shows that started years ago.
		years = [year - 3, year] if movie else None

		# Only retrieve decent titles, since most users will not be interested in bad titles.
		# At the end we retrieve a few of the worst titles.
		if niche:
			best = [3.5, 10.0]
			worst = [0.0, 3.49999]
		else:
			best = [5.0, 10.0]
			worst = [0.0, 4.99999]

		############################################
		# SUMMARY RELEASES
		############################################

		# Most popular releases over the past year.

		timeout = durationMonth1
		time = durationYear1

		# TRAKT
		#	Movies:	250 items (1 request - 250 per request)
		#	Shows:	250 items (1 request - 250 per request)
		base = {
			'function'	: trakt,
			'timeout'	: timeout,
			'year'		: years,
			'rating'	: best,
			'sort'		: MetaTrakt.SortPopular,
			'limit'		: 250,
		}
		_add(values = secondary, base = base, year = year) # Can return future releases.
		_add(values = delete, base = base, year = year - 1)

		# TMDB
		#	Movies:	200 items (10 requests - 20 per request)
		#	Shows:	200 items (10 requests - 20 per request)
		base = {
			'function'	: tmdb,
			'timeout'	: timeout,
			'time'		: time,
			'year'		: years,
			'serie'		: MetaTmdb.SerieMini if mini else True,
			'rating'	: best,
			'votes'		: _votes(10 if show else 100),
			'sort'		: MetaTmdb.SortPopularity,
			'limit'		: MetaTmdb.limit(10),
		}
		_add(values = secondary, base = base)

		# IMDB
		#	Movies:	500 items (2 requests - 250 per request)
		#	Shows:	500 items (2 requests - 250 per request)
		base = {
			'function'	: imdb,
			'timeout'	: timeout,
			'time'		: time,
			'language'	: True, # Otherwise too many Indian titles are returned.
			'rating'	: best,
			'votes'		: _votes(100 if show else 1000),
			'sort'		: MetaImdb.SortPopularity,
		}
		_add(values = primary, base = base, release = MetaImdb.ReleaseHome)
		_add(values = secondary, base = base, release = MetaImdb.ReleaseNew)

		############################################
		# HOME RELEASES
		############################################

		# Most popular digital and physical releases per month over the past year.

		timeout = durationWeek3

		if movie:
			# TRAKT (Physical Releases)
			# The Trakt DVD Calendar only contains physical releases, no digital releases.
			# Hence, if a title already has a digital date, but no physical date, it will not show up here.
			#	Movies:	300-700 items (12 requests - 30-70 per request)
			date1 = _forward(year = year, month = month)
			date2 = _backward(year = year, month = month)
			base = {
				'function'	: trakt,
				'timeout'	: timeout,
				'release'	: MetaTrakt.ReleasePhysical,
				'year'		: years,
				#'rating'	: best, # No rating, since already few titles are returned.
			}
			for i in range(12):
				_increase(values = primary, base = base, date = date1)
				_decrease(values = delete, base = base, date = date2)

			# TRAKT (Digital Releases)
			# Trakt only has a Premiere Calendar and a DVD Calendar, but no Digital Calendar.
			# Hence, if a title already has a digital date, but no physical date, it will not show up in the DVD Calendar.
			# Digital releases can be filtered in the Calendars using the "watchnow" parameter, which is not in the API docs, but is used on Trakt's website for movie calendars.
			# This is not that useful, since doing this returns digital releases, but they only have premiere dates, not the digital dates (unlike the DVD Calendar also has the physical release dates).
			# The digital date is used to refresh the MetaCache metadata for new digital/physical release dates.
			# Since the digital date is not available here, these values add little to Arrivals.
			# But the query date range is used to "estimate" the digital date, which is better than nothing.
			# Update (2025-09): Trakt has added a new movie streaming calendar API endpoint, which also returns the digital release date.
			#	Movies:	300-700 items (12 requests - 40-70 per request)
			date1 = _forward(year = year, month = month)
			date2 = _backward(year = year, month = month)
			base = {
				'function'	: trakt,
				'timeout'	: timeout,
				'release'	: MetaTrakt.ReleaseDigital,
				'year'		: years,
				'rating'	: best,
				'votes'		: _votes(250), # (reduced: 200 -> 250) Reduce the number of titles returned.
			}
			for i in range(12):
				_increase(values = primary, base = base, date = date1)
				_decrease(values = delete, base = base, date = date2)

			# TMDB
			#	Movies:	720 items (36 requests - 20 per request)
			date1 = _forward(year = year, month = month)
			date2 = _backward(year = year, month = month)
			base = {
				'function'	: tmdb,
				'timeout'	: timeout,
				'release'	: MetaTmdb.ReleaseHome,
				'year'		: years,
				'serie'		: MetaTmdb.SerieMini if mini else True,
				'rating'	: best,
				'votes'		: _votes(150), # (reduced: 100 -> 150)
				'sort'		: MetaTmdb.SortPopularity,
				'limit'		: MetaTmdb.limit(3),
			}
			for i in range(12):
				_increase(values = primary, base = base, date = date1)
				_decrease(values = delete, base = base, date = date2)

			# IMDB
			#	Movies:	2500 items (12 requests - 250 per request - more recent months return less than 250)
			date1 = _forward(year = year, month = month)
			date2 = _backward(year = year, month = month)
			base = {
				'function'	: imdb,
				'timeout'	: timeout,
				'release'	: MetaImdb.ReleaseHome,
				'language'	: True, # Otherwise too many Indian titles are returned.
				'rating'	: best,
				'votes'		: _votes(200), # (reduced: 100 -> 200)
				'sort'		: MetaImdb.SortPopularity,
			}
			for i in range(12):
				_increase(values = primary, base = base, date = date1)
				_decrease(values = delete, base = base, date = date2)

		############################################
		# NEW RELEASES
		############################################

		# Most popular theatrical releases per month over the past year.

		timeout = durationWeek4

		# TRAKT
		#	Movies:	800-2000 items (12 requests - 50-200 per request)
		#	Shows:	450-650 items (12 requests - 20-80 per request)
		date1 = _forward(year = year, month = month)
		date2 = _backward(year = year, month = month)
		base = {
			'function'	: trakt,
			'timeout'	: timeout,
			'release'	: MetaTrakt.ReleaseNew,
			'year'		: years,
			'rating'	: best,
			'votes'		: _votes(50 if show else 70), # (reduced: 30 -> 50 if show else 50 -> 70)
		}
		for i in range(12):
			_increase(values = secondary, base = base, date = date1)
			_decrease(values = delete, base = base, date = date2)

		# TMDB
		#	Movies:	480 items (24 requests - 20 per request)
		#	Shows:	480 items (24 requests - 20 per request)
		date1 = _forward(year = year, month = month)
		date2 = _backward(year = year, month = month)
		base = {
			'function'	: tmdb,
			'timeout'	: timeout,
			'release'	: MetaTmdb.ReleaseNew,
			'year'		: years,
			'serie'		: MetaTmdb.SerieMini if mini else True,
			'rating'	: best,
			'votes'		: _votes(30 if show else 150), # (reduced: 10 -> 30 if show else 100 -> 150)
			'sort'		: MetaTmdb.SortPopularity,
			'limit'		: MetaTmdb.limit(2),
		}
		for i in range(12):
			_increase(values = secondary, base = base, date = date1)
			_decrease(values = delete, base = base, date = date2)

		############################################
		# SEASON RELEASES
		############################################

		# Most popular new seasons per month over the past year.
		# Unlike the other requests, this retrieves and newly premiered season, not just a new S01.

		timeout = durationWeek3

		if show:
			# TRAKT
			#	Shows:	650-750 items (12 requests - 50-180 per request - with 50 votes)
			#	Shows:	900-1100 items (12 requests - 50-180 per request - with 30 votes)
			#	Shows:	1000-1200 items (12 requests - 50-180 per request - with 25 votes)
			#	Shows:	1000-1400 items (12 requests - 50-180 per request - with 20 votes)
			date1 = _forward(year = year, month = month)
			date2 = _backward(year = year, month = month)
			base = {
				'function'	: trakt,
				'timeout'	: timeout,
				'media'		: Media.Season,
				'rating'	: best,
				'votes'		: _votes(40), # (reduced: 25 -> 40)
			}
			for i in range(12):
				_increase(values = primary, base = base, date = date1)
				_decrease(values = delete, base = base, date = date2)

		############################################
		# MINISERIES RELEASES
		############################################

		# Most popular new miniseries per month over the past year.

		timeout = durationMonth1
		time = durationYear1

		if show:
			# TMDB
			#	Shows:	100 items (5 requests - 20 per request)
			base = {
				'function'	: tmdb,
				'timeout'	: timeout,
				'time'		: time,
				'serie'		: MetaTmdb.SerieMini,
				'rating'	: best,
				'votes'		: _votes(20),
				'sort'		: MetaTmdb.SortPopularity,
				'limit'		: MetaTmdb.limit(5),
			}
			_add(values = secondary, base = base)

			# IMDB
			#	Shows:	250 items (1 request - 250 per request)
			base = {
				'function'	: imdb,
				'timeout'	: timeout,
				'niche'		: Media.Mini,
				'time'		: time,
				'language'	: True, # Otherwise too many Indian titles are returned.
				'rating'	: best,
				'votes'		: _votes(50),
				'sort'		: MetaImdb.SortPopularity,
			}
			_add(values = secondary, base = base)

		############################################
		# RECENT RELEASES
		############################################

		# Most popular releases over the past month.

		timeout = durationHour12
		time = durationMonth1

		# TRAKT
		#	Movies:	100-350 items (3 requests - 10-300 per request)
		#	Shows:	100-200 items (2 requests - 100-200 per request)
		base = {
			'function'	: trakt,
			'timeout'	: timeout,
			'time'		: time,
			'year'		: years,
			'rating'	: best,
			'votes'		: _votes(10), # (reduced: 5 -> 10)
		}
		_add(values = secondary, base = base, release = MetaTrakt.ReleaseNew)
		if movie:
			_add(values = primary, base = base, release = MetaTrakt.ReleaseDigital)
			_add(values = primary, base = base, release = MetaTrakt.ReleasePhysical)
		elif show:
			_add(values = primary, base = base, release = MetaTrakt.ReleaseNew, media = Media.Season)

		# TMDB
		#	Movies:	120 items (6 requests - 20 per request)
		#	Shows:	60 items (3 requests - 20 per request)
		base = {
			'function'	: tmdb,
			'timeout'	: timeout,
			'time'		: time,
			'year'		: years,
			'serie'		: MetaTmdb.SerieMini if mini else True,
			'rating'	: best,
			'votes'		: _votes(5),
			'sort'		: MetaTmdb.SortPopularity,
			'limit'		: MetaTmdb.limit(3),
		}
		if movie: _add(values = primary, base = base, release = MetaTmdb.ReleaseHome)
		_add(values = secondary, base = base, release = MetaTmdb.ReleaseNew)

		# IMDB
		#	Movies:	250-350 items (2 requests - 30-250 per request)
		#	Shows:	200-300 items (2 requests - 20-250 per request)
		base = {
			'function'	: imdb,
			'timeout'	: timeout,
			'time'		: time,
			'language'	: True, # Otherwise too many Indian titles are returned.
			'rating'	: best,
			'votes'		: _votes(15), # (reduced: 5 -> 15)
			'sort'		: MetaImdb.SortPopularity,
		}
		_add(values = primary, base = base, release = MetaImdb.ReleaseHome)
		_add(values = secondary, base = base, release = MetaImdb.ReleaseNew)

		############################################
		# WORST RELEASES
		############################################

		# Most popular amongst the worst releases. Other requests above retrieve only better ratings.

		timeout = durationMonth1
		time = durationYear1

		# TRAKT
		#	Movies:	100 items (1 request - 100 per request)
		#	Shows:	100 items (1 request - 100 per request)
		base = {
			'function'	: trakt,
			'timeout'	: timeout,
			'year'		: years,
			'rating'	: worst,
			'votes'		: _votes(150 if show else 200), # (reduced: 100 -> 150/200)
			'sort'		: MetaTrakt.SortPopular,
			'limit'		: 50, # (reduced: 100 -> 50)
		}
		_add(values = secondary, base = base, year = year) # Can return future releases.
		_add(values = delete, base = base, year = year - 1)

		# TMDB
		#	Movies:	20 items (1 request - 20 per request)
		#	Shows:	20 items (1 request - 20 per request)
		base = {
			'function'	: tmdb,
			'timeout'	: timeout,
			'time'		: time,
			'year'		: years,
			'serie'		: MetaTmdb.SerieMini if mini else True,
			'rating'	: worst,
			'sort'		: MetaTmdb.SortVotes,
			'limit'		: MetaTmdb.limit(1),
		}
		_add(values = secondary, base = base)

		# IMDB
		#	Movies:	100 items (1 request - 100 per request)
		#	Shows:	100 items (1 request - 100 per request)
		base = {
			'function'	: imdb,
			'timeout'	: timeout,
			'time'		: time,
			'language'	: True, # Otherwise too many Indian titles are returned.
			'rating'	: worst,
			'sort'		: MetaImdb.SortVotes,
			'limit'		: 50, # (reduced: 100 -> 50)
		}
		_add(values = secondary, base = base)

		############################################
		# NICHE RELEASES
		############################################

		# Add additional niche content if the user is a regular/frequent viewer.
		# There are already a number of anime titles in the other requests (especially for shows), but add a few extra.

		if not niche:
			nicheRegular = []
			nicheFrequent = []
			niches = {
				Media.Docu		: self.mTools.settingsContentDocu(),
				Media.Short		: self.mTools.settingsContentShort(),
				Media.Family	: self.mTools.settingsContentFamily(),
				Media.Anima		: self.mTools.settingsContentAnima(),
				Media.Anime		: self.mTools.settingsContentAnime(),
				Media.Donghua	: self.mTools.settingsContentDonghua(),
			}
			for k, v in niches.items():
				if v >= MetaTools.ContentFrequent: nicheFrequent.append(k)
				elif v >= MetaTools.ContentRegular: nicheRegular.append(k)

			timeout = durationWeek2
			time = durationMonth3
			for i in nicheFrequent + nicheRegular:
				base = {
					'function'	: imdb,
					'timeout'	: timeout,
					'time'		: time,
					'rating'	: best,
					'votes'		: _votes(10),
					'sort'		: MetaImdb.SortPopularity,
					'niche'		: i,
				}
				_add(values = secondary, base = base, release = MetaImdb.ReleaseNew)

			timeout = durationDay3
			time = durationMonth1
			for i in nicheFrequent:
				base = {
					'function'	: trakt,
					'timeout'	: timeout,
					'time'		: time,
					'year'		: years,
					'votes'		: _votes(3),
					'niche'		: i,
				}
				_add(values = secondary, base = base, release = MetaTrakt.ReleaseNew)
				if movie:
					_add(values = secondary, base = base, release = MetaTrakt.ReleaseDigital)
					_add(values = secondary, base = base, release = MetaTrakt.ReleasePhysical)
				elif show:
					_add(values = secondary, base = base, release = MetaTrakt.ReleaseNew, media = Media.Season)

		############################################
		# RETRIEVE
		############################################

		threads = []
		synchronizer = Semaphore(6)

		# There are two main ways of retrieving the data:
		#	1. Fixed Date Ranges:
		#		Cache entire months or weeks that are only refreshed once in a while.
		#		These calls are for data in the "far" past and will probably not change a lot anymore, and therefore do not have to be refreshed that often.
		#		These use fixed date ranges as parameters to the cached function, so that the cache entry stays the same as time progresses.
		#		For instance, the cache entry for [2024-01-01, 2024-02-01] is the same today as it is next week or next month.
		#	2. Time Spans:
		#		Reretrieve/refresh requests for recent dates more frequently.
		#		This data will probably change more frequently and should be refreshed more often.
		#		These do not use fixed date ranges, but a time span or duration instead.
		#		This means every time the cache is refreshed, the same cache entry gets replaced with the new data, even if the dates are different, saving disk space.
		#		If the date range would be passed in, the parameters to the cache are different each time, meaning a new cache entry would be created every time.
		#		Now the dynamic date range is only calculated INSIDE the cache function execution.
		#		For instance, the cache entry for [7 days] will be different today than tomorrow or the next week, because the internal date range is calculated from the current date.
		for item in primary + secondary: # Add the home releases before the new releases to the results, since they are more likley to have a digital/physical release date and show up in the menu.
			# Skip unsupported providers for certain niches.
			provider = functions.get(item.get('function'))
			if provider and not provider in providers: continue

			item['items'] = items
			if not item.get('media'): item['media'] = media
			if 'niche' in item: item['niche'] = Media.add(item['niche'], niche)
			else: item['niche'] = niche

			threads.append(Pool.thread(target = self._arrivalCache, kwargs = item, synchronizer = synchronizer, start = True))
		[thread.join() for thread in threads]

		# Add the origin of the title.
		# This helps to better sort Arrivals by increasing the sorting weight if the title appears on Trakt.
		try:
			origins = {i : {} for i in functions.values()}
			order = list(origins.keys())

			for item in items:
				existing = None
				origin = item.get('origin')
				ider = '%s_' + str(item.get('season'))
				for provider in origins.keys():
					id = item['id'].get(provider)
					if id:
						existing = origins[provider].get(ider % id)
						if existing: break
				if existing:
					if Tools.isArray(origin): existing.extend(origin)
					else: existing.append(origin)
					item['origin'] = existing
				else:
					if not Tools.isArray(origin): origin = [origin]
					item['origin'] = origin
					for provider in origins.keys():
						id = item['id'].get(provider)
						if id: origins[provider][ider % id] = origin

			for item in items:
				origin = item.get('origin')
				if origin:
					origin = Tools.listFlatten(origin)
					origin = Tools.listUnique([i for i in origin if i])
					origin = Tools.listSort(origin, order = order)
				item['origin'] = origin
		except: Logger.error()

		# Many shows can have more than one season premiered within the past year.
		# Eg: tt11612120 S02 and S03.
		# Merge duplicate items by number, to prefer the one with the highest season number.
		# NB: Also merge based on the number of votes.
		# The same title can come from an older cached page with outdated metadata (fewer votes), while the "recent" releases request can return the same title, but with more recent metadata (more votes).
		items = self.mTools.filterDuplicate(items = items, id = True, title = False, number = False, merge = ['number', 'votes'])

		# Trakt summary can return future items.
		items = self.mTools.filterTime(items = items, include = 1, time = MetaTools.TimeLaunch)

		# Start a background thread to delete old unused cached entries.
		# These will eventually be cleared by the cache itself, but if we know they will not be used anymore, we can just as well delete them here.
		for i in delete:
			try: del i['timeout']
			except: pass
		Pool.thread(target = self._arrivalClear, kwargs = {'media' : media, 'niche' : niche, 'items' : delete}, start = True)

		return items

	def _arrivalCache(self, items, function, timeout, media, **parameters):
		def _arrivalCache(result, date = None, origin = None):
			try:
				if result:
					# Smart reduce here already, otherwise the cache for thousands of titles has tons of unnecessary data, filling up disk space.
					result = self._metadataSmartReduce(media = media, items = result, full = False)

					# Titles from IMDb do not have a date.
					# This causes the items to always be "new" in _metadataSmart(), since they are filtered out at the end.
					# Add an estimated date based on the date parameter to ensure they are kept in the smart list.
					# Trakt only returns physical release dates, but not digital release dates.
					# TMDb does not return physical or digital release dates, only premiere dates.
					# Add the end of the date-range, so we at least have an approximation.
					# This extra date can be used to refresh titles more frequently if they are close to their physical/digital release.
					# Update: This date can be still far from the actual physical/digital dates.
					# The Trakt/IMDb digital retrieval will apply the date range parameter to the premiere date and only filter by digital-watch options, but it will not apply the date parameter to the digital date.
					# Update (2025-03): IMDb was updated and now returns the premiere date. There might be 1 or 2 titles from IMDb that only haver a year, but no date. But 99.9% should now have a date.
					if date:
						date1 = date[-1] if (date[1] - date[0]) <= 3024000 else None # Only if the parameter range is lower than 35 days.
						date2 = date[-1]
					else:
						date1 = None
						date2 = None

					movie = Media.isMovie(media)
					for item in result:
						times = item.get('time')
						if not times: times = item['time'] = {}

						premiere = None
						if not times.get(MetaTools.TimePremiere):
							premiere = item.get('aired') or item.get('premiered')
							if premiere:
								premiere = Time.timestamp(premiere, format = Time.FormatDate, utc = True)
								times[MetaTools.TimePremiere] = premiere

						if not times.get(MetaTools.TimePremiere) or (movie and (not times.get(MetaTools.TimeDigital) or not times.get(MetaTools.TimePhysical))):
							time = date1 or premiere or date2
							if time: times[MetaTools.TimeUnknown] = time

						item['origin'] = origin

				return result
			except: Logger.error()

		if parameters.get('time'):
			def _arrivalCache1(time, **parameters):
				origin = parameters.get('origin')
				try: del parameters['origin']
				except: pass
				try: offset = parameters.pop('offset')
				except: offset = 0
				end = Time.timestamp() - offset
				parameters['date'] = [Time.past(timestamp = end, seconds = time), end]
				result = function(**parameters)
				return _arrivalCache(result = result, date = parameters.get('date'), origin = origin)
			execute = _arrivalCache1
		else:
			# Randomize the cache timeout with +-8 hours.
			# So that over time, these cache calls are out-of-sync and do not all refresh at the same time.
			# This reduces batch requests to a provider in a short time span.
			# Do not add too much, since with every cache refresh, this value is added.
			if timeout > 172800: timeout += Math.random(start = -28800, end = 28800)

			def _arrivalCache2(**parameters):
				origin = parameters.get('origin')
				try: del parameters['origin']
				except: pass
				result = function(**parameters)
				return _arrivalCache(result = result, date = parameters.get('date'), origin = origin)
			execute = _arrivalCache2

		data = self._cache('cacheSeconds', None, function = execute, timeout = timeout, media = media, **parameters)

		if data:
			data = self._processAggregate(media = media, items = data)
			if Media.isSerie(media):
				for item in data:
					item['media'] = Media.Show # Replace season releases.
					if item.get('season') is None: item['season'] = 1
			items.extend(data)

	def _arrivalClear(self, media, niche, items):
		# Delete old cache entries to save some disk space.
		Time.sleep(5) # Wait for other processes to finish.
		for item in items:
			if not 'media' in item: item['media'] = media
			if 'niche' in item and niche: item['niche'] = Media.add(item['niche'], niche)
			else: item['niche'] = niche
			self._cacheDelete(**item)

	def _arrivalProcess(self, items, media = None, niche = None, unknown = None, filter = None, sort = None, order = None, page = None, limit = None, detail = None):
		if unknown is None: unknown = True
		if limit is None: limit = self.limit(media = media, content = MetaManager.ContentArrival)
		elif Tools.isFloat(limit): limit = int(limit * self.limit(media = media, content = MetaManager.ContentArrival))
		if sort is None: sort = MetaTools.SortGlobal

		# Filter niche menus, like Anime, Originals, and Minis.
		# Filter by the niche list itself, not the derived filters, since this is faster are more reliable than possible incomplete detailed metadata attributes, like secondary companies or genres.
		filterBefore = self._processorNiche(niche = niche, filter = filter, generic = True)

		# Filter out items without a plot or poster.
		# Items without a plot are useless if we do not know what the movie is about.
		# Items without a poster look ugly in the menus, and are typically not high-calibre titles.
		# Some movies have no plot, some have no poster, and some have no plot and poster.
		# Only do this for the after-filters, since before retrieving the detailed metadata, the plot/images might not be available yet.
		# Do not partial-filter if "limit=False", since it specifically means to retrieve all titles. Also not for "detail=False", since non-detailed metadata typically do not have a plot/poster. Used by preload() and release().
		filterAfter = {}
		if not limit is False and not detail is False: filterAfter.update({MetaTools.FilterPartial : {'plot' : True, 'poster' : True}})
		filterAfter.update(filterBefore)

		filter = [filterBefore, filterAfter]

		if items:
			# Filter out items marked as "removed".
			items = [item for item in items if not (item.get(MetaManager.Smart) or {}).get('removed')]

			# Some items have an episode number, which causes them to be displayed as an episode in the Arrivals menu, instead of a season.
			# This happens spordically with only a few items in the menu, and only the first time the shows Arrivals menu is opened after Kodi launch. If the menu is opened a second time, all are displayed as seasons.
			# Not sure what causes this, maybe some items are getting cached in MetaCache's memory from smart-loading during boot, which are then reused the first time the shows Arrivals menu is opened.
			# Setting the episode number to None seems to solve the problem.
			if Media.isSerie(media):
				for item in items: item['episode'] = None

			# Filter directly by niche, and not the filters create from the niche.
			# Because the cache porgress list has reduced metadata, and not all prarameters might be available here, although most should.
			# Not all items can be filtered out here, if they have not detailed metadata yet.
			# Leave the final sorting to content() after the detailed metadata was retrieved.
			# This should only take a few ms, even for large lists.
			niched = filterBefore.get(MetaTools.FilterNiche) # Only use the company ID, not the company type, otherwise too few titles might be returned.
			if niched:
				# Do not allow unknowns when a niche is specified.
				# Otherwise all shows which were not smart-loaded yet, are added to it.
				# Eg: multi-season shows are listed under Minis Progress menu, just because they do not smart-loaded yet.
				# Even if some are filtered out, after a little while the smart-list will be full enough to list more under the niche menus.
				items = self.mTools.filterNiche(items = items, include = niched, unknown = unknown)

			# There can be shows with 2+ seasons released within a year, and might therefore show up multiple times in the list.
			# Filter them out and keep the one with the highest season/episode number.
			# This should not be done during smart-loading. Otherwise one of the seasons is always removed, and therefore it ends up in the "new" list again, every time the list is refreshed.
			# Hence, keep both seasons in the smart-list and only filter them out here.
			items = self.mTools.filterDuplicate(items = items, id = True, title = False, number = False, merge = 'number')

			# Sometimes a title can appear mutiple times in Arrivals.
			# Once from Trakt/TMDb which still holds the old/outdated IMDb ID, but does not have the "imdx" ID set (yet).
			# And once from IMDb with the new/updated IMDb ID.
			# Filter out these duplicates and merge by "idimdb" to use the Trakt/TMDb item, but update its IMDb ID from the item coming from IMDb (which probably has the new/updated ID).
			# Eg: Home Sweet Home: Rebirth 2025
			#	Trakt: {'imdb': 'tt29425837', 'tmdb': '1353117', 'trakt': '1104128', 'slug': 'home-sweet-home-rebirth-2025'}
			#	IMDb: {'imdb': 'tt29425792', 'imdx': 'tt29425792'}
			#	Merged: {'imdb': 'tt29425792', 'imdx': 'tt29425837', 'tmdb': '1353117', 'trakt': '1104128', 'slug': 'home-sweet-home-rebirth-2025'}
			# Takes about 10-20ms.
			items = self.mTools.filterDuplicate(items = items, id = False, title = True, number = True, merge = 'idimdb')

			# Reduce the number of items returned.
			# This reduces later filtering/sorting time, and we probably do not need more than this.
			# The items are already sorted, so the first N items should be the best ones.
			# This ensures linear processing time, to counter the smart list growing very large over time.
			if not limit is False and not self.releasing(): items = items[:2000]

		return {
			'items'		: items,
			'filter'	: filter,
			'sort'		: sort,
			'order'		: order,
			'page'		: page,
			'limit'		: limit,
		}

	##############################################################################
	# RANDOM
	##############################################################################

	def random(self, media = None, niche = None, arrival = None, keyword = None, release = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentRandom, media = media, niche = niche, arrival = arrival, keyword = keyword, release = release, status = status, year = year, date = date, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, award = award, ranking = ranking, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit, detail = detail, quick = quick, refresh = refresh, more = more)

	def _random(self, media = None, niche = None, arrival = None, filter = None, sort = None, order = None, page = None, limit = None, refresh = None, **parameters):
		try:
			if media:
				if Media.isSerie(media): media = Media.Show # If episodes are scraped the media is Media.Episode.
				items = self._cache('cacheExtended', refresh, self._randomAssemble, media = media, niche = niche, arrival = arrival, **parameters)
				if items:
					return {
						'items'		: items,
						'filter'	: filter,
						'sort'		: sort,
						'order'		: order,
						'page'		: page,
						'limit'		: limit,
						'more'		: len(items),
						'pack'		: False,
					}
		except: Logger.error()
		return None

	def _randomAssemble(self, media = None, niche = None, arrival = None, keyword = None, release = None, status = None, year = None, date = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, award = None, ranking = None, rating = None, votes = None, **parameters):
		try:
			count = 15 if niche else 10 # Niches, like Anime, return way less items.
			multi = count * 2 # Certain providers might not be supported for certain parameter combinations. Add a few more.
			random = {}

			time = release or year or date or Media.isNew(niche) or Media.isHome(niche) or Media.isAge(niche)

			# Loading a full Arrivals menu takes a lot of requests.
			# Only do this if explicitly requested (arrivals=True) or if it is not a niche.
			if arrival is None and not niche and not time: arrival = True

			# Random year.
			if not time:
				random['year'] = []
				current = Time.year()
				for i in range(multi):
					start = Math.random(start = 1970, end = current)
					random['year'].append([start, min(current, start + Math.random(start = 3, end = 10))])

			# Random genre.
			exclude = [MetaTools.GenreNone, MetaTools.GenreShort, MetaTools.GenreNews, MetaTools.GenreMusic, MetaTools.GenreMusical, MetaTools.GenreSport, MetaTools.GenreSporting, MetaTools.GenreTravel, MetaTools.GenreHoliday, MetaTools.GenreHome, MetaTools.GenreFood, MetaTools.GenreTalk, MetaTools.GenreGame, MetaTools.GenreAward, MetaTools.GenreReality, MetaTools.GenreSoap, MetaTools.GenrePodcast, MetaTools.GenreIndie, MetaTools.GenreSpecial]
			if not genre and not Media.isTopic(niche) and not Media.isMood(niche):
				genres = []
				for k, v in self.mTools.genre().items():
					if v['support'][media] and (v['provider'][MetaTools.ProviderImdb][media] or v['provider'][MetaTools.ProviderTrakt][media]):
						genres.append(k)
				for i in exclude:
					try: genres.remove(i)
					except: pass
				random['genre'] = Tools.listPick(genres, count = multi, remove = True)

			# Random certificate.
			if not certificate and not Media.isAudience(niche):
				certificates = [Audience.CertificateNr]
				if Media.isSerie(media):
					certificates.extend([
						Audience.CertificateTvg,
						Audience.CertificateTvy,
						Audience.CertificateTvy7,
						Audience.CertificateTvpg,
						Audience.CertificateTv13,
						Audience.CertificateTv14,
						Audience.CertificateTvma,
					])
				else:
					certificates.extend([
						Audience.CertificateNr,
						Audience.CertificateG,
						Audience.CertificatePg,
						Audience.CertificatePg13,
						Audience.CertificateR,
						Audience.CertificateNc17,
					])
				random['certificate'] = Tools.listPick(certificates, count = multi)

			if not ranking and not rating and not Media.isQuality(niche):
				random['rating'] = []
				for i in range(multi):
					start = Math.random(start = 4.0, end = 8.0)
					random['rating'].append([Math.round(start, places = 1), Math.round(min(10.0, start + Math.random(start = 1, end = 5)), places = 1)])

			items = []
			threads = []
			for i in range(multi):
				even = i % 2

				kwargs = Tools.copy(parameters)
				kwargs.update({
					'items' : items,
					'media' : media,
					'niche' : niche,
					'keyword' : keyword,
					'release' : release,
					'status' : status,
					'year' : year,
					'date' : date,
					'duration' : duration,
					'genre' : genre,
					'language' : language,
					'country' : country,
					'certificate' : certificate,
					'company' : company,
					'studio' : studio,
					'network' : network,
					'award' : award,
					'ranking' : ranking,
					'rating' : rating,
					'votes' : votes,
				})

				counter = 0
				values = ['year', 'genre', 'certificate', 'rating'] if even else ['year', 'genre', 'rating', 'certificate'] # Eg: Anime, do not always just pick year+certificate.
				for j in values:
					value = random.get(j)
					if value:
						counter += 1
						kwargs[j] = value[i]
						if counter >= 2: break

				# Sometimes use Trakt and sometimes IMDb.
				# Switch provider if a genre is not supported, otherwise IMDb will make a requests without a genre.
				provider = [MetaTools.ProviderTrakt, MetaTools.ProviderImdb] if even else [MetaTools.ProviderImdb, MetaTools.ProviderTrakt]
				if kwargs.get('genre') and not self.mTools.genre(genre = kwargs.get('genre'))['provider'][provider[0]][media]: provider = [provider[1], provider[0]]

				# Remove unsupported providers for certain combinations.
				# Eg: Only use IMDb, but not Trakt, for random Award Winners.
				providers = self.provider(**kwargs)
				provider = [i for i in provider if i in providers]
				if not provider: continue

				kwargs['provider'] = provider

				if not votes and not Media.isPrestige(niche) and not Media.isPopular(niche) and not Media.isUnpopular(niche) and not Media.isViewed(niche):
					kwargs['votes'] = 250 if provider[0] == MetaTools.ProviderImdb else 50

				# Although we do not specifically search by these genres, these genres can still be returned if they fall within any of the other parameters.
				# This can cause a lot of game/talk shows, etc to appear in the list.
				# Specifically exclude these genres in the query.
				value = kwargs.get('genre')
				value = [value] if value else []
				kwargs['genre'] = value + ['-' + i for i in exclude]

				threads.append(Pool.thread(target = self._randomDiscover, kwargs = kwargs, start = True))
				if len(threads) >= count: break

			if arrival:
				kwargs = Tools.copy(kwargs)
				for i in ['release', 'year', 'date', 'provider']:
					try: del kwargs[i]
					except: pass
				threads.append(Pool.thread(target = self._randomArrival, kwargs = kwargs, start = True))

			[thread.join() for thread in threads]

			if items:
				items = Tools.listShuffle(items)
				return items
		except: Logger.error()
		return None

	def _randomDiscover(self, items, **parameters):
		result = self._discover(**parameters)
		if result:
			result = result.get('items')
			if result: items.extend(result)

	def _randomArrival(self, items, **parameters):
		result = self._arrival(**parameters)
		if result:
			result = result.get('items')
			if result: items.extend(result[:500])

	##############################################################################
	# SET
	##############################################################################

	def set(self, set = None, tmdb = None, title = None, year = None, query = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentSet, media = Media.Set, set = set, tmdb = tmdb, title = title, year = year, query = query, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _set(self, set = None, tmdb = None, title = None, year = None, query = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		try:
			media = Media.Set
			processor = self._processor(media = media, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentSet))
			if filter is None: filter = processor.get('filter')
			if sort is None: sort = processor.get('sort')
			if order is None: order = processor.get('order')
			if page is None: page = processor.get('page')
			if limit is None: limit = processor.get('limit')

			mediad = media
			items = None
			parameters = {}
			function = None
			timeout = 'cacheExtended'

			alphabetic = 0
			discover = set == MetaTools.SetDiscover or set == MetaTools.SetArrival or set == MetaTools.SetPopular or set == MetaTools.SetRandom
			if set == MetaTools.SetAlphabetic:
				alphabetic = 1
				discover = True
			if not discover and set:
				set = str(set) # Alphabetic integers are converted to int.
				if len(set) == 1:
					set = set.lower()
					alphabetic = 2
					discover = True

			if not provider: provider = MetaTools.ProviderTmdb

			if provider == MetaTools.ProviderTmdb:
				instance = MetaTmdb.instance()

				# Items of a set.
				if tmdb:
					item = self.metadataSet(tmdb = tmdb, refresh = refresh)
					if item:
						mediad = Media.Movie
						items = Tools.copy(item.get('part')) # Since they will get edited.
						more = True
				elif discover:
					function = instance.discoverSet
					more = True
				elif set == MetaManager.ContentSearch:
					function = instance.searchSet
					parameters['query'] = query
					limit = MetaTmdb.LimitFixed
					more = True

			if function: items = self._cache(timeout, refresh, function, **parameters)

			if items:
				if alphabetic:
					for i in items: i['sort'] = Tools.replaceNotAlphaNumeric(i.get('title'), '').strip().lower()
					if alphabetic == 2:
						if set == '_': items = [i for i in items if not i['sort'] or not(i['sort'][0].isascii() or i['sort'][0].isdigit())]
						else: items = [i for i in items if i['sort'].startswith(set)]
					items = Tools.listSort(items, key = lambda i : i['sort'] or 'ZZZZZZZZZZZZZZZZZZ')

				elif set == MetaTools.SetArrival:
					# Assume the most recently added sets are new ones.
					# Many are not that new, many are porn, and most have no images or other metadata.
					items = Tools.listReverse(items)

				elif set == MetaTools.SetSearch:
					# The order returned by TMDb set searches is not great.
					# When searching "Avatar" it shows two other sets before the one we actually want.
					# Manually sort by total votes instead.
					if sort is None: sort = MetaTools.SortVotes

				elif set == MetaTools.SetRandom:
					items = Tools.listShuffle(items)

				if more is True: more = len(items)

				return {
					'items'		: items,
					'media'		: mediad,
					'set'		: set,

					'filter'	: filter,
					'sort'		: sort,
					'order'		: order,
					'page'		: page,
					'limit'		: limit,
					'more'		: more,
				}
		except: Logger.error()
		return None

	##############################################################################
	# LIST
	##############################################################################

	def list(self, media = None, niche = None, list = None, imdb = None, tmdb = None, tvdb = None, trakt = None, query = None, status = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentList, media = media, niche = niche, list = list, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, query = query, status = status, year = year, duration = duration, genre = genre, language = language, country = country, certificate = certificate, company = company, studio = studio, network = network, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _list(self, media = None, niche = None, list = None, imdb = None, tmdb = None, tvdb = None, trakt = None, query = None, status = None, year = None, duration = None, genre = None, language = None, country = None, certificate = None, company = None, studio = None, network = None, rating = None, votes = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, refresh = None, more = None, **parameters):
		try:
			if media:
				processor = self._processor(media = media, niche = niche, year = year, genre = genre, language = language, country = country, certificate = certificate, rating = rating, votes = votes, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentList))
				niche = processor.get('niche')
				if filter is None: filter = processor.get('filter')
				if sort is None: sort = processor.get('sort')
				if order is None: order = processor.get('order')
				if page is None: page = processor.get('page')
				if limit is None: limit = processor.get('limit')

				parameters = {}
				function = None
				timeout = 'cacheMedium'
				mediad = media
				error = None
				discover = list in [MetaManager.ContentSearch, MetaTools.ListArrival, MetaTools.ListQuality, MetaTools.ListAward, MetaTools.ListReal, MetaTools.ListBucket, MetaTools.ListMind]

				if not provider:
					if trakt: provider = MetaTools.ProviderTrakt
					elif imdb: provider = MetaTools.ProviderImdb
					elif discover: provider = MetaTools.ProviderTrakt
					elif list in [MetaTools.ListDiscover, MetaTools.ListPopular, MetaTools.ListTrending, MetaTools.ListOfficial]: provider = MetaTools.ProviderTrakt

				if provider == MetaTools.ProviderTrakt:
					instance = MetaTrakt.instance()

					# Items of a list.
					if trakt:
						function = instance.list
						timeout = 'cacheShort'
						parameters['media'] = media
						parameters['niche'] = niche
						if Tools.isArray(trakt):
							parameters['user'] = trakt[0]
							parameters['id'] = trakt[1]

							# Only use "cacheRefresh" if we use paging for Trakt lists.
							# Currently all list items are retrieved at once without paging, to allow for proper local sorting.
							# Since these requests are larger and take longer, cache them for longer.
							#timeout = 'cacheRefresh'
							timeout = 'cacheShort' if trakt[0] == instance.accountUser() else 'cacheLong'
						else:
							parameters['id'] = trakt

						# We do not page for Trakt lists anymore.
						# Retrieve all (or at least up to 2000) items from the lsit in one go.
						# This allows for proper sorting across the entire list, instead of sub-par sorting over a single page.
						# Check MetaTrakt.LimitList for more info.
						#parameters['page'] = page
						#parameters['limit'] = limit
						parameters['page'] = None
						parameters['limit'] = MetaTrakt.LimitList
						more = True

					# Search for lists.
					elif list == MetaManager.ContentSearch:
						niche = media
						media = Media.List
						function = instance.search
						timeout = 'cacheExtended'
						parameters['media'] = media
						parameters['query'] = query
						parameters['page'] = page
						parameters['limit'] = limit

					# Predefined list search.
					elif discover:
						include = []
						if list == MetaTools.ListArrival:
							include = ['new', 'recent', 'latest', 'arrival']
						elif list == MetaTools.ListQuality:
							include = ['best', 'top', 'good', 'great', 'greatest', 'perfect']
						elif list == MetaTools.ListAward:
							include = ['award', 'winner']
							if Media.isMovie(media): include.extend(['oscar'])
							elif Media.isSerie(media): include.extend(['emmy', 'emmies'])
							include.extend(['golden globe', 'best picture', 'best script', 'best screenplay', 'best director'])
						elif list == MetaTools.ListReal:
							include = ['true story', 'truestory', 'true event', 'trueevent', 'real story', 'realstory', 'real event', 'realevent']
						elif list == MetaTools.ListBucket:
							include = ['bucket', 'bucketlist', 'mustwatch', 'must watch']
						elif list == MetaTools.ListMind:
							include = ['mindfuck', 'mind fuck', 'brainfuck', 'brain fuck', 'mindbending', 'mind bending', 'mindblowing', 'mind blowing', 'plot twist', 'weird']

						exclude = ['people']
						if Media.isMovie(media): exclude.extend(['tv', 'television', 'tvshow', 'show', 'serie', 'season', 'episode'])
						elif Media.isSerie(media): exclude.extend(['movie', 'film', 'cinema', 'theater'])

						include = ['"%s"' % i for i in include]
						exclude = ['!*%s*' % i for i in exclude]
						query = '(%s) && %s' % (' || '.join(include), ' && '.join(exclude))

						niche = media
						media = Media.List
						function = instance.search
						timeout = 'cacheExtended'
						parameters['media'] = media
						parameters['query'] = query
						parameters['page'] = page
						parameters['limit'] = limit

					# Lists of lists.
					elif list in [MetaTools.ListPersonal, MetaTools.ListLike, MetaTools.ListComment, MetaTools.ListCollaboration, MetaTools.ListDiscover, MetaTools.ListPopular, MetaTools.ListTrending]:
						niche = media
						media = Media.List
						function = instance.lists
						timeout = 'cacheExtended' if list in [MetaTools.ListDiscover, MetaTools.ListPopular, MetaTools.ListTrending] else 'cacheRefresh'
						parameters['list'] = MetaTools.ListPopular if list == MetaTools.ListDiscover else list
						if list in [MetaTools.ListPersonal, MetaTools.ListCollaboration]:
							more = True
						else:
							parameters['page'] = page
							parameters['limit'] = limit

					# Official Trakt lists. Currently seems to only be movie collections.
					elif list == MetaTools.ListOfficial:
						niche = media
						media = Media.List
						function = instance.search
						timeout = 'cacheExtended'
						parameters['media'] = media
						parameters['list'] = list
						parameters['page'] = page
						parameters['limit'] = limit

					# Trakt user lists.
					else:
						parameters['media'] = media
						if list in [MetaTools.ListCalendar, MetaTools.ListProgress] and Media.isSerie(media): parameters['media'] = mediad = Media.Episode
						parameters['niche'] = niche

						if list in [MetaTools.ListRecommendation, MetaTools.ListCalendar, MetaTools.ListCollection, MetaTools.ListHistory]:
							more = True
						else:
							parameters['page'] = page
							parameters['limit'] = limit

						parameters.update({
							'status' : status,
							'year' : year,
							'duration' : duration,
							'genre' : genre,
							'language' : language,
							'country' : country,
							'certificate' : certificate,
							'company' : company,
							'studio' : studio,
							'network' : network,
							'rating' : rating,
							'votes' : votes,
							'sort' : sort,
							'order' : order,
						})

						if list == MetaTools.ListRecommendation:
							function = instance.recommendation
							timeout = 'cacheExtended'
							parameters['collection'] = False # Titles collected are probably ones that were already watched.
							parameters['watchlist'] = True # Titles on the watchlist are probably ones that were not watched yet.
							more = MetaTrakt.LimitRecommendation
						elif list == MetaTools.ListCalendar:
							function = instance.release
							timeout = 'cacheMedium'
							if Media.isSerie(media):
								parameters['user'] = True
								parameters['release'] = False
							else:
								parameters['user'] = True
								parameters['release'] = MetaTrakt.ReleaseNew

							# Do not do this, since it will cause the request not to be cached, since the timestamps are different every time we make the call.
							#parameters['date'] = [Time.past(years = 1, utc = True), Time.timestamp(utc = True)]
							date = Time.format(format = Time.FormatDate) + ' 23:59:59'
							timestamp = Time.timestamp(date, format = Time.FormatDateTime, utc = True)
							parameters['date'] = [Time.past(timestamp = timestamp, years = 1, utc = True), timestamp]
						elif list == MetaTools.ListWatchlist:
							# This allows the retrieval of shows, seasons, and individual episodes from the watchlist, instead of just shows.
							if Media.isSerie(media): parameters['media'] = mediad = [Media.Show, Media.Season, Media.Episode]
							function = instance.listWatch
							timeout = 'cacheShort'
						elif list == MetaTools.ListFavorite:
							function = instance.listFavorite
							timeout = 'cacheShort'
						elif list == MetaTools.ListCollection:
							function = instance.listCollection
							timeout = 'cacheShort'
						elif list == MetaTools.ListRating:
							function = instance.listRating
							timeout = 'cacheQuick'
						elif list == MetaTools.ListHistory:
							function = instance.listWatched # Not "listHistory", which also contains scrobbles and checkins.
							timeout = 'cacheQuick'
						elif list == MetaTools.ListProgress:
							function = instance.listProgress
							timeout = 'cacheQuick'
						elif list == MetaTools.ListHidden:
							function = instance.listHidden
							timeout = 'cacheExtended'

				elif provider == MetaTools.ProviderImdb:
					instance = MetaImdb.instance()

					# Items of a list.
					if imdb:
						function = instance.list
						timeout = 'cacheQuick'
						if Tools.isArray(imdb):
							if len(imdb) > 1: timeout = 'cacheRefresh'
							imdb = imdb[-1] # User ID + list ID can be passed in.
						parameters.update({
							'media' : media,
							'id' : imdb,
							'year' : year,
							'genre' : genre,
							'rating' : rating,
							'votes' : votes,
						})

					# Lists of lists.
					elif list == MetaTools.ListPersonal:
						niche = media
						media = Media.List
						function = instance.lists
						timeout = 'cacheQuick'

					# IMDb user lists.
					else:
						if list == MetaTools.ListWatchlist: function = instance.listWatch
						elif list == MetaTools.ListRating: function = instance.listRating
						elif list == MetaTools.ListCheckin: function = instance.listCheckin
						timeout = 'cacheShort'
						parameters.update({
							'media' : media,
							'year' : year,
							'genre' : genre,
							'rating' : rating,
							'votes' : votes,
						})

				items = self._cache(timeout, refresh, function, **parameters) if function else None

				if items == MetaImdb.Privacy:
					self._cacheDelete(function, **parameters)
					error = MetaImdb.Privacy
					items = None
					more = None

				if items:
					if more is True: more = len(items)

					for item in items:
						if mediad == Media.Episode and not media == Media.List:
							item['media'] = Media.Show

							# Aggregate these attributes, otherwise the menu (eg Trakt Calendar) shows the details for the show, instead of the episode.
							aggregate = {}
							for i in ['tvshowtitle', 'title', 'originaltitle', 'tagline', 'plot', 'tvshowyear', 'year', 'premiered', 'aired', 'time', 'rating', 'votes', 'voting', 'duration', 'status']:
								value = item.get(i)
								if value: aggregate[i] = value
							item['aggregate'] = aggregate

						item['niche'] = niche # Used in MetaTools.command() to determine which media items to retrieve from the list.

					# There are a bunch of users that spam the Trakt lists, probably to show up in addon menus.
					# These occasionally pop up in the various Trakt list discoveries (eg: New Arrivals).
					#	https://trakt.tv/search/lists?query=call%20girls
					#	Eg: Dubailand Call Girls +971505700000 Indian Call Girls ...
					if discover:
						items = [item for item in items if not Regex.match(data = item.get('title'), expression = r'call.?girl.*\d', cache = True)]
						more = True # Else the next page does not show if we filter out some itmes.

				# Also return if there are no items. To return the MetaImdb.Privacy error.
				return {
					'items'		: items,
					'media'		: media,
					'error'		: error,
					'list'		: list,

					'filter'	: filter,
					'sort'		: sort,
					'order'		: order,
					'page'		: page,
					'limit'		: limit,
					'more'		: more,

					'pack'		: False,
				}
		except: Logger.error()
		return None

	##############################################################################
	# PERSON
	##############################################################################

	def person(self, media = None, niche = None, person = None, imdb = None, tmdb = None, tvdb = None, trakt = None, query = None, gender = None, award = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, detail = None, quick = None, refresh = None, more = None, **parameters):
		return self.content(content = MetaManager.ContentPerson, media = media, niche = niche, person = person, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, query = query, gender = gender, award = award, filter = filter, sort = sort, order = order, page = page, limit = limit, provider = provider, detail = detail, quick = quick, refresh = refresh, more = more)

	def _person(self, media = None, niche = None, person = None, imdb = None, tmdb = None, tvdb = None, trakt = None, query = None, gender = None, award = None, filter = None, sort = None, order = None, page = None, limit = None, provider = None, refresh = None, more = None, **parameters):
		try:
			if media:
				processor = self._processor(media = media, niche = niche, filter = filter, sort = sort, order = order, page = page, limit = limit or self.limit(media = media, content = MetaManager.ContentPerson))
				niche = processor.get('niche')
				if filter is None: filter = processor.get('filter')
				if sort is None: sort = processor.get('sort')
				if order is None: order = processor.get('order')
				if page is None: page = processor.get('page')
				if limit is None: limit = processor.get('limit')

				parameters = {}
				function = None
				timeout = 'cacheExtended'

				if person in [MetaTools.PersonFilmmaker, MetaTools.PersonCreator, MetaTools.PersonDirector, MetaTools.PersonCinematographer, MetaTools.PersonWriter, MetaTools.PersonProducer, MetaTools.PersonEditor, MetaTools.PersonComposer, MetaTools.PersonActor, MetaTools.PersonActress]:
					imdb = {
						Media.Movie : {
							MetaTools.PersonFilmmaker		: 'ls026411399',
							MetaTools.PersonDirector		: 'ls000005319',
							MetaTools.PersonCinematographer	: 'ls000045131',
							MetaTools.PersonWriter			: 'ls026034645',
							MetaTools.PersonProducer		: 'ls009401127',
							MetaTools.PersonEditor			: 'ls020798362',
							MetaTools.PersonComposer		: 'ls026034696',
							MetaTools.PersonActor			: 'ls000005354',
							MetaTools.PersonActress			: 'ls000005315',
						},
						Media.Show : {
							MetaTools.PersonCreator			: 'ls062274560',
							MetaTools.PersonDirector		: 'ls059167873',
							MetaTools.PersonCinematographer	: 'ls075157401',
							MetaTools.PersonWriter			: 'ls059167873',
							MetaTools.PersonProducer		: 'ls098127847',
							MetaTools.PersonComposer		: 'ls068448237',
							MetaTools.PersonActor			: 'ls046978814',
							MetaTools.PersonActress			: 'ls082848195',
						},
					}[media][person]

				if not provider:
					if trakt: provider = MetaTools.ProviderTrakt
					elif imdb: provider = [MetaTools.ProviderImdb, MetaTools.ProviderTrakt] # Trakt can also search by IMDb ID.
				if provider is True or not provider: providers = self.provider(content = MetaManager.ContentPerson, gender = gender, award = award)
				else: providers = provider if Tools.isArray(provider) else [provider]

				for provider in providers:
					if provider == MetaTools.ProviderTrakt:
						instance = MetaTrakt.instance()

						# Get titles for a person.
						if trakt or imdb:
							function = instance.person
							parameters['media'] = media
							parameters['id'] = trakt or imdb
							more = True

						# Search for people.
						elif person == MetaManager.ContentSearch:
							niche = media
							media = Media.Person
							function = instance.search
							parameters['media'] = media
							parameters['query'] = query
							parameters['page'] = page
							parameters['limit'] = limit

						# Discover people. Does not have images.
						elif person == MetaTools.PersonDiscover:
							niche = media
							media = Media.Person
							function = instance.person
							parameters['media'] = media
							parameters['page'] = page
							parameters['limit'] = limit

					elif provider == MetaTools.ProviderImdb:
						instance = MetaImdb.instance()

						# Get titles for a person.
						if imdb:
							if instance.idType(imdb) == MetaImdb.IdList:
								niche = media
								media = Media.Person
								function = instance.list
								parameters['media'] = media
								parameters['id'] = imdb
								more = True
							else:
								function = instance.discover
								parameters['media'] = media
								parameters['id'] = imdb
								more = True

						# Search for people.
						elif person == MetaManager.ContentSearch:
							niche = media
							media = Media.Person
							function = instance.searchPerson
							more = True
							parameters['query'] = query

						# Discover people.
						elif person == MetaTools.PersonDiscover:
							niche = media
							media = Media.Person
							function = instance.discoverPerson
							more = True
							if gender: parameters['gender'] = gender
							if award: parameters['group'] = award

					items = self._cache(timeout, refresh, function, **parameters) if function else None

					if items:
						if more is True: more = len(items)

						for item in items:
							item['niche'] = niche # Used in MetaTools.command() to determine which media items to retrieve from the list.

						return {
							'items'		: items,
							'media'		: media,
							'person'	: person,

							'filter'	: filter,
							'sort'		: sort,
							'order'		: order,
							'page'		: page,
							'limit'		: limit,
							'more'		: more,

							'pack'		: False,
						}
		except: Logger.error()
		return None

	##############################################################################
	# SEASON
	##############################################################################

	def season(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, quick = None, refresh = None, **parameters):
		return self.content(content = MetaManager.ContentSeason, media = Media.Season, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick, refresh = refresh)

	def _season(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, quick = None, refresh = None, **parameters):
		try:
			show = self.metadataShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick, refresh = refresh)
			if show:
				items = self.metadataSeason(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, quick = quick, refresh = refresh, hint = {'pack' : show.get('pack') or show.get('packed')})
				if items:
					pack = MetaPack.instance(pack = show.get('pack'))
					countSeason = pack.countSeasonOfficial()
					countSpecial = pack.countEpisodeSpecial()
					countOfficial = pack.countEpisodeOfficial()
					countSeasonUniversal = pack.countSeasonUniversal()

					niche = show.get('niche')
					specialStory = pack.durationMaximumSpecial(default = 0) > (pack.durationMeanOfficial(default = 0) * 0.8) # At least one longer special.
					absoluteDefault = countSeason > 1 and pack.numberLastStandardEpisode(season = 1) == pack.numberLastSequentialEpisode(season = 1) # Eg: Dragon Ball Super (Trakt vs TVDb).
					absoluteNiche = Media.isAnime(niche) or Media.isDonghua(niche)

					index = -1
					for i in range(len(items)):
						if items[i]['season'] == 0:
							index = i
							break

					setting = self.mTools.settingsShowSpecial()
					if not(setting == 3 or (setting == 2 and countSpecial) or (setting == 1 and specialStory)):
						if index >= 0:
							items.pop(index)
							index = -1

					# Use the natively calculated Sequential instead of the Absolute order.
					# In most cases they are exactly the same.
					# But in some cases the Absolute numbering is completely screwed up. Eg: House.
					# Place the Absolute menu 2nd, since it shares details with the Series menu (eg: watched status, user rating, etc).
					if countSeason: # Not for titles only available on IMDb.
						setting = self.mTools.settingsShowAbsolute()
						if setting == 3 or (setting == 2 and (absoluteDefault or absoluteNiche)) or (setting == 1 and absoluteDefault):
							sequential = Tools.copy(show)
							sequential['sequential'] = True
							#items.insert(0 if index < 0 else (index + 1), sequential) # Placed between Specials and S01.
							items.insert(0, sequential) # Placed between Series and Specials.

					# Some shows only available on IMDb, but not other providers, will have no pack data, and therefore not countSpecial or countOfficial (eg: tt31566242, tt30346074).
					# Still show the Series menu if there is at least a season.
					setting = self.mTools.settingsShowSerie()
					if setting == 3 or (setting == 2 and (countSeason or countSeasonUniversal or countSpecial or countOfficial)) or (setting == 1 and (countSpecial and countOfficial)):
						items.insert(0, show)
				return {'items' : items}
		except: Logger.error()
		return None

	##############################################################################
	# EPISODE
	##############################################################################

	def episode(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, page = None, limit = None, quick = None, refresh = None, submenu = None, special = None, **parameters):
		return self.content(content = MetaManager.ContentEpisode, media = Media.Episode, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, page = page, limit = limit, quick = quick, refresh = refresh, submenu = submenu, special = special)

	def _episode(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, page = None, limit = None, quick = None, refresh = None, submenu = None, special = None, **parameters):
		try:
			if not season is None:
				more = None

				number = None
				if self.mTools.submenuIsSequential(submenu = submenu): number = MetaPack.NumberSequential
				elif self.mTools.submenuIsAbsolute(submenu = submenu): number = MetaPack.NumberSequential
				elif self.mTools.submenuIsSerie(submenu = submenu): number = MetaPack.NumberSerie

				# This is important if the last episode in an Episode submenu is the last episode of S01 of that show.
				# MetaTools.submenuNumber() will then increment the episode number by one for the next page.
				# Then in metadataEpisode() it will be interpreted as a sequential number, causing problems with paging.
				# Eg: GoT S01E10 will be incremented to S01E11. Make sure the 1st page of the Episode submenu has S01E10 listed as the last episode of the page for this to happen.
				elif self.mTools.submenuIsEpisode(submenu = submenu): number = MetaPack.NumberStandard

				# Reduce means to reduce the number of (unimportant) specials interleaved in submenus.
				# Reduce the number of specials in Progress submenus (episodes-submenu), but leave the extra specials for the Series menu (series-submenu).
				reduce = True if special == MetaManager.SpecialReduce else None
				interleave = self.mTools.settingsShowInterleave() if special is MetaManager.SpecialSettings else bool(special)
				if season and episode and interleave and self.mTools.submenuIsEpisode(submenu = submenu): reduce = True
				if reduce: special = MetaManager.SpecialReduce

				# Limit the number of episodes shown for indirect or flattened episode menus (eg Trakt Progress list).
				# Otherwise menus with many episodes per season take too long to load and the user probably does not access the last episodes in the list anyway.
				if not limit:
					if submenu: limit = self.limit(submenu = submenu)
					elif not episode is None: limit = self.limit(submenu = MetaTools.SubmenuSerie if (not reduce and interleave) else MetaTools.SubmenuEpisode)

				items = self.metadataEpisode(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, number = number, limit = limit, quick = quick, refresh = refresh, special = special, hint = True)

				if items:
					# Preferablly show an entire season per page in the Series menu.
					# If there are too many episodes (eg 100s) in a season, page that season like normal episode submenu.
					# The easiest way to do this is to simply retrieve episodes, like with episodes submenus, and remove the last ones that are in the next season.
					if self.mTools.submenuIsSerie(submenu = submenu):
						first = None
						for i in range(len(items)):
							if first is None: # The season parameter passed into this function might be wrong (eg the last episode of the previous season).
								value = items[i].get('season')
								if value: first = value
							elif items[i].get('season') > first:
								# Do not do this if there are less than 3 items.
								# Eg: Star Wars: Young Jedi Adventures
								#	A clash between Trakt's sequential numbers and TVDb's uncombined numbers make the next page always have the 1st episode as sequential number and the rest of the episodes standard numbers.
								#	This makes the series menu page 2+ always show only 1 episode per page.
								# This should not happen anymore, since in metadataEpisode() we do not convert the numbers for Series menu anymore:
								#	if not number == MetaPack.NumberSerie: self._metadataPackNumber(...)
								if i >= 3: items = items[:i]
								break

					return {
						'items' 	: items,

						'submenu'	: submenu,
						'special'	: special,

						'limit'		: limit,
						'more'		: more,
					}
		except: Logger.error()
		return None
