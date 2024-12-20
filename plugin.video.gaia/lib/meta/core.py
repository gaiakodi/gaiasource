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

from lib.meta.service import MetaService
from lib.meta.data import MetaData, MetaWrap

from lib.modules.tools import File, Tools, Logger
from lib.modules.concurrency import Pool, Lock

class MetaCore(object):

	# Level
	Level1				= MetaService.Level1
	Level2				= MetaService.Level2
	Level3				= MetaService.Level3
	Level4				= MetaService.Level4
	Level5				= MetaService.Level5
	Level6				= MetaService.Level6
	Level7				= MetaService.Level7
	LevelDefault		= MetaService.LevelDefault

	# Threaded
	# Only use a threaded manager if a single item is retrieved (single lookup like eg next episode during binge watching).
	# Do NOT use a threaded manager from the indexer classes.
	# If eg the Trakt progress list is retrieved for the first time (uncached):
	#	1. Each episode in the list will be retrieved.
	#	2. For each episode, the metadata for all episodes in that season and the next season is retrieved.
	#	3. For each episode, the metadata for all the seasons is retrieved.
	#	4. For each episode, the metadata for the show is retrieved.
	# If threads are used on the lowest level (like here in MetaCore), this can spawn 100s of threads.
	# On Intel/AMD devices with a lot of memory this might be fine.
	# But on ARM devices with limited memory, the maximum number of threads is 250-290, and the OS might run out of threads and won't be able to create new ones.
	# More info in concurrency.py -> Pool.instance().

	ThreadedDynamic		= None				# Retrieve metadata with as many sub-threads as possible without using too many threads that might lead to running out of threads.
	ThreadedEnable		= True				# Retrieve metadata with as many sub-threads as needed.
	ThreadedDisable		= False				# Retrieve metadata with as few sub-threads as possible, preferably just 1.
	ThreadedDefault		= ThreadedDynamic

	# Provider

	ProviderImdb		= MetaData.ProviderImdb
	ProviderTmdb		= MetaData.ProviderTmdb
	ProviderTvdb		= MetaData.ProviderTvdb
	ProviderTrakt		= MetaData.ProviderTrakt
	ProviderDefault		= MetaData.ProviderDefault

	ProviderLock		= Lock()
	Providers			= None

	###################################################################
	# CONSTRUCTOR
	###################################################################

	def __init__(self, provider = None, threaded = ThreadedDefault):
		if provider: self.mProvider = self.provider(provider = provider, internal = True)
		else: self.mProvider = None
		self.mThreaded = threaded

		self.language = self._language
		self.search = self._search
		self.id = self._id
		self.idImdb = self._idImdb
		self.idTmdb = self._idTmdb
		self.idTvdb = self._idTvdb
		self.idTrakt = self._idTrakt
		self.movie = self._movie
		self.collection = self._collection
		self.show = self._show
		self.season = self._season
		self.episode = self._episode
		self.character = self._character
		self.person = self._person
		self.company = self._company
		self.translation = self._translation
		self.translationTitle = self._translationTitle
		self.translationOverview = self._translationOverview

	###################################################################
	# PROVIDER
	###################################################################

	@classmethod
	def provider(self, provider = None, internal = False):
		if MetaCore.Providers is None:
			MetaCore.ProviderLock.acquire()
			if MetaCore.Providers is None:
				import importlib
				providers = {}
				directories, files = File.listDirectory(File.joinPath(File.directory(__file__), 'services'), absolute = False)
				path = 'lib.meta.services.'
				for file in files:
					if not file.startswith('_') and file.endswith('.py'):
						file = file.replace('.py', '')
						module = importlib.import_module(path + file)
						try:
							module = Tools.getClass(module, 'Meta' + file.capitalize())
							if module: providers[file] = module
						except: Logger.error()
				MetaCore.Providers = providers # Only set at the end, otherwise an empty dict might be used while the loop above is still running.
			MetaCore.ProviderLock.release()

		if provider is None or provider is True: return list(MetaCore.Providers.values())
		elif Tools.isString(provider): return [MetaCore.Providers[provider]] if internal else MetaCore.Providers[provider]
		elif Tools.isArray(provider): return [v for k, v in MetaCore.Providers.items() if k in provider]

	def providerExecute(self, provider, function, *args, **kwargs):
		if provider is None: provider = self.mProvider
		else: provider = self.provider(provider = provider, internal = True)
		if not provider: return None

		single = len(provider) == 1
		results = {}
		threads = []
		for i in provider:
			result = []
			results[i.provider()] = result

			kwargs['result'] = result
			kwargs['provider'] = i
			kwargs['function'] = function
			kwargs['threaded'] = self.mThreaded

			# Reduce the number of threads created if only a single provider is used.
			# The thread is joined below, so using threads with a single provider does not add any benefits.
			if (single and self.mThreaded is None) or self.mThreaded is False:
				self._providerExecute(*args, **kwargs)
			else:
				threads.append(Pool.thread(target = self._providerExecute, args = args, kwargs = kwargs, start = True))
		[i.join() for i in threads]

		mode = None
		for value in results.values():
			try: value = value[0]
			except: continue # Empty list
			if Tools.isInstance(value, MetaData): # MetaData object.
				mode = 'metadata'
				break
			elif Tools.isList(value):
				if len(value) > 0 and Tools.isInstance(value[0], MetaData): # List of search metadata objects.
					mode = 'listmeta'
					break
				else: # List of strings or dictionaries for translations.
					mode = 'list'
					break
			elif Tools.isDictionary(value): # Dictionary of IDs.
				mode = 'dictionary'
				break
			elif Tools.isString(value): # Single IDs.
				mode = 'single'
				break

		data = None
		if mode == 'metadata':
			data = MetaWrap()
			for key, value in results.items():
				try: data.metadataSet(provider = key, value = value[0])
				except: pass
		elif mode == 'listmeta':
			data = []
			for key, value in results.items():
				try:
					for v in value[0]:
						wrap = MetaWrap()
						wrap.metadataSet(provider = key, value = v)
						data.append(wrap)
				except: pass
		elif mode == 'list':
			data = []
			for value in results.values():
				try: data.extend(value[0])
				except: pass
		elif mode == 'dictionary':
			data = {}
			for value in results.values():
				try: data.update(value[0])
				except: pass
		elif mode == 'single':
			try:
				data = list(results.values())[0]
				if Tools.isArray(data): data = data[0]
			except: data = None

		return data

	@classmethod
	def _providerExecute(self, result, provider, function, *args, **kwargs):
		data = Tools.getFunction(instance = provider, name = function)(*args, **kwargs)
		result.append(data)
		return data

	###################################################################
	# LANGUAGE
	###################################################################

	@classmethod
	def language(self, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).language(level = level, cache = cache)

	def _language(self, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'language', level = level, cache = cache)

	###################################################################
	# SEARCH
	###################################################################

	@classmethod
	def search(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, limit = None, offset = None, page = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).search(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, limit = limit, offset = offset, page = page, level = level, cache = cache)

	def _search(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, limit = None, offset = None, page = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'search', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, limit = limit, offset = offset, page = page, level = level, cache = cache)

	###################################################################
	# ID
	###################################################################

	@classmethod
	def id(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, extract = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).id(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, extract = extract, level = level, cache = cache)

	@classmethod
	def idImdb(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).idImdb(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, level = level, cache = cache)

	@classmethod
	def idTmdb(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).idTmdb(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, level = level, cache = cache)

	@classmethod
	def idTvdb(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).idTvdb(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, level = level, cache = cache)

	@classmethod
	def idTrakt(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).idTrakt(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, level = level, cache = cache)

	def _id(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, extract = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'id', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, extract = extract, level = level, cache = cache)

	def _idImdb(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'idImdb', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, level = level, cache = cache)

	def _idTmdb(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'idTmdb', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, level = level, cache = cache)

	def _idTvdb(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'idTvdb', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, level = level, cache = cache)

	def _idTrakt(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'idTrakt', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, level = level, cache = cache)

	###################################################################
	# MOVIE
	###################################################################

	@classmethod
	def movie(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).movie(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, level = level, cache = cache)

	def _movie(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'movie', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, level = level, cache = cache)

	###################################################################
	# COLLECTION
	###################################################################

	@classmethod
	def collection(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).collection(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, level = level, cache = cache)

	def _collection(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'collection', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, level = level, cache = cache)

	###################################################################
	# SHOW
	###################################################################

	@classmethod
	def show(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberAdjust = True, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).show(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberAdjust = numberAdjust, level = level, cache = cache)

	def _show(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberAdjust = True, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'show', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberAdjust = numberAdjust, level = level, cache = cache)

	###################################################################
	# SEASON
	###################################################################

	@classmethod
	def season(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, show = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).season(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, show = show, level = level, cache = cache)

	def _season(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, show = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'season', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, show = show, level = level, cache = cache)

	###################################################################
	# EPISODE
	###################################################################

	@classmethod
	def episode(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, show = None, season = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).episode(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, show = show, season = season, level = level, cache = cache)

	def _episode(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, show = None, season = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'episode', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, show = show, season = season, level = level, cache = cache)

	###################################################################
	# CHARACTER
	###################################################################

	@classmethod
	def character(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).character(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, level = level, cache = cache)

	def _character(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'character', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, level = level, cache = cache)

	###################################################################
	# PERSON
	###################################################################

	@classmethod
	def person(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).person(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, level = level, cache = cache)

	def _person(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'person', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, level = level, cache = cache)

	###################################################################
	# COMPANY
	###################################################################

	@classmethod
	def company(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).company(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, level = level, cache = cache)

	def _company(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'company', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, level = level, cache = cache)

	###################################################################
	# TRANSLATION
	###################################################################

	@classmethod
	def translation(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, translation = None, language = None, limit = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).translation(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, translation = translation, language = language, limit = limit, level = level, cache = cache)

	def _translation(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, translation = None, language = None, limit = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'translation', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, translation = translation, language = language, limit = limit, level = level, cache = cache)

	@classmethod
	def translationTitle(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, language = None, limit = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).translationTitle(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, language = language, limit = limit, level = level, cache = cache)

	def _translationTitle(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, language = None, limit = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'translationTitle', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, language = language, limit = limit, level = level, cache = cache)

	@classmethod
	def translationOverview(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, language = None, limit = None, level = None, cache = None, provider = ProviderDefault, threaded = ThreadedDefault):
		return MetaCore(provider = provider, threaded = threaded).translationOverview(id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, language = language, limit = limit, level = level, cache = cache)

	def _translationOverview(self, id = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, query = None, year = None, number = None, numberSeason = None, numberEpisode = None, media = None, language = None, limit = None, level = None, cache = None, provider = ProviderDefault):
		return self.providerExecute(provider = provider, function = 'translationOverview', id = id, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, query = query, year = year, number = number, numberSeason = numberSeason, numberEpisode = numberEpisode, media = media, language = language, limit = limit, level = level, cache = cache)
