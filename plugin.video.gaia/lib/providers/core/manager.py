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

import os
import imp
import pkgutil

from lib.providers.core.base import ProviderBase
from lib.modules.database import Database
from lib.modules.tools import Logger, Tools, Hash, Time, File, System, Converter, Settings, Language, Math, Regex, Hardware, Platform
from lib.modules.concurrency import Pool, Lock

ProviderAddon = None

class Manager(object):

	# Database
	Database					= None
	DatabaseLock				= Lock()
	DatabaseName				= 'providers'
	DatabaseProviders			= 'providers'
	DatabaseLinks				= 'links'
	DatabaseStreams				= 'streams'
	DatabaseFailures			= 'failures'

	# Settings
	SettingsOptimization		= 'internal.initial.optimization'
	SettingsConfigurationData	= 'provider.configuration.data'
	SettingsPresetsData			= 'provider.presets.data'
	SettingsPresetsEnabled		= 'provider.presets.enabled'
	SettingsScrapeOptimize		= 'scrape.optimization.optimize'
	SettingsProviderOptimize	= 'provider.optimization.optimize'

	SettingsLock				= Lock()
	SettingsThread				= None

	# Tradeoff
	TradeoffSpeed				= 'speed' # Prefer faster scraping over more links.
	TradeoffResult				= 'result' # Prefer more links over faster scraping.
	TradeoffMix					= 'mix' # Prefer a good combination of speed and links.
	TradeoffFactor				= 0.3 # How much to increase/decrease the rating by if a tradeoff is used. Should be large enough to move from one group to another, and groups are 0.2 apart from each other.

	# Providers
	ProvidersData				= None
	ProvidersCache				= None

	# Other
	Thread						= None
	Create						= {}

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		from lib.providers.core.web import ProviderWeb
		from lib.providers.core.external import ProviderExternal
		from lib.providers.core.debrid import ProviderDebrid

		Manager.Create = {}
		Manager.ProvidersData = None
		Manager.ProvidersCache = None

		ProviderBase.reset(settings = settings)
		ProviderWeb.reset(settings = settings)
		ProviderExternal.reset(settings = settings)
		ProviderDebrid.reset(settings = settings)

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def check(self, progress = True, wait = False):
		def _check(progress = True):
			self.providersInitialize(full = False, progress = progress)
			self.settingsLabel()
			self.presetsLabel()

		Manager.Thread = Pool.thread(target = _check, args = (progress,))
		Manager.Thread.start()
		if wait: Manager.Thread.join()

	@classmethod
	def checkWait(self):
		if Manager.Thread: Manager.Thread.join()

	##############################################################################
	# DATA
	##############################################################################

	@classmethod
	def dataPath(self):
		return System.pathProviders()

	@classmethod
	def dataSize(self):
		return File.sizeDirectory(self.dataPath())

	@classmethod
	def dataClear(self):
		return File.deleteDirectory(self.dataPath())

	##############################################################################
	# DATABASE
	##############################################################################

	@classmethod
	def databaseInitialize(self, wait = False):
		self._databaseInitialize()
		self.databaseClearOld(wait)

	@classmethod
	def databaseSize(self):
		return self._database()._size()

	@classmethod
	def databaseClear(self, providers = True, links = True, streams = True, failures = True, compress = True):
		base = self._database()
		if providers:
			base._drop(table = Manager.DatabaseProviders, compress = compress)
			try: del Manager.Create[Manager.DatabaseProviders]
			except: pass
		if links:
			base._drop(table = Manager.DatabaseLinks, compress = compress)
			try: del Manager.Create[Manager.DatabaseLinks]
			except: pass
		if streams:
			base._drop(table = Manager.DatabaseStreams, compress = compress)
			try: del Manager.Create[Manager.DatabaseStreams]
			except: pass
		if failures:
			base._drop(table = Manager.DatabaseFailures, compress = compress)
			try: del Manager.Create[Manager.DatabaseFailures]
			except: pass

	@classmethod
	def databaseClearOld(self, wait = False):
		def _databaseClearOld():
			self.streamsDatabaseClearOld()
			self.linksDatabaseClearOld()
		if wait: _databaseClearOld()
		else: Pool.thread(target = _databaseClearOld, start = True)

	@classmethod
	def _database(self):
		if Manager.Database is None:
			Manager.DatabaseLock.acquire()
			if Manager.Database is None: Manager.Database = Database(name = Manager.DatabaseName)
			Manager.DatabaseLock.release()
		return Manager.Database

	@classmethod
	def _databaseInitialize(self, providers = True, links = True, streams = True, failures = True, force = False):
		base = self._database()
		if providers:
			if not Manager.DatabaseProviders in Manager.Create or force:
				Manager.Create[Manager.DatabaseProviders] = True
				base._create('CREATE TABLE IF NOT EXISTS %s (version TEXT PRIMARY KEY, data TEXT);' % Manager.DatabaseProviders)
		if links:
			if not Manager.DatabaseLinks in Manager.Create or force:
				Manager.Create[Manager.DatabaseLinks] = True
				base._create('CREATE TABLE IF NOT EXISTS %s (id TEXT PRIMARY KEY, provider TEXT, time INTEGER, data TEXT);' % Manager.DatabaseLinks)
		if streams:
			if not Manager.DatabaseStreams in Manager.Create or force:
				Manager.Create[Manager.DatabaseStreams] = True
				base._create('CREATE TABLE IF NOT EXISTS %s (id TEXT PRIMARY KEY, provider TEXT, time INTEGER, data TEXT);' % Manager.DatabaseStreams)
		if failures:
			if not Manager.DatabaseFailures in Manager.Create or force:
				Manager.Create[Manager.DatabaseFailures] = True
				base._create('CREATE TABLE IF NOT EXISTS %s (id TEXT PRIMARY KEY, count INTEGER, time INTEGER);' % Manager.DatabaseFailures)
		return base

	@classmethod
	def _databaseId(self, provider = None, query = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None):
		values = []
		if provider: values.append(provider.id())
		if query: values.append(query)
		if idImdb: values.append('imdb' + str(idImdb))
		elif idTmdb: values.append('tmdb' + str(idTmdb))
		elif idTvdb: values.append('tvdb' + str(idTvdb))
		if not numberSeason is None: values.append(str(numberSeason))
		if not numberEpisode is None: values.append(str(numberEpisode))
		id = [value if value else '' for value in values]
		return Hash.sha256('_'.join(id))

	##############################################################################
	# PROVIDERS
	##############################################################################

	@classmethod
	def _providersDatabaseInitialize(self):
		return self._databaseInitialize(providers = True, links = False, streams = False, failures = False)

	@classmethod
	def _providersDatabaseRetrieve(self, full = True, id = None, addon = None, enabled = None, media = None, type = None, mode = None, access = None, preset = None, settings = True):
		try:
			base = self._providersDatabaseInitialize()
			result = base._selectSingle('SELECT version, data FROM %s;' % (Manager.DatabaseProviders))
			if result and result[0] == System.version():
				if full:
					from lib.modules import handler
					supportTorrent = handler.Handler(type = handler.Handler.TypeTorrent).supported()
					supportUsenet = handler.Handler(type = handler.Handler.TypeUsenet).supported()
					supportHoster = handler.Handler(type = handler.Handler.TypeHoster).supported()

					developer = System.developer()
					failures = self.failureList()

				data = Converter.jsonFrom(result[1])
				if data:
					providers = []

					# Reinitialize providers if an external addon was updated.
					versions = {}
					for i in range(len(data)):
						try:
							module = data[i]['addon']['module']['scraper']
							if module:
								versionOld = data[i]['addon']['version']
								if versionOld:
									if not module in versions:
										try: versionCurrent = System.version(module)
										except: versionCurrent = None
										versions[module] = versionCurrent
									if versionCurrent and not versionOld == versionCurrent:
										return None
						except:
							Logger.error()

					settings = self.settingsLoad()
					try: preset = preset['data']
					except: pass

					for i in range(len(data)):
						try:
							# Creating instances of providers that won't be used in any case results in an unnecessary increase of execution time.
							# Instead, providers that are not needed are skipped and never instantiated.
							# Only if subsequent loading of providers have different attributes to the ones below, do we reset and reload them from the database (resetting is done in the providersInitialize() function).
							if data[i]['status'] == ProviderBase.StatusHidden: continue
							if not enabled is None:
								# Check specifically against False (is), since it can return None if no specific value was set by the user (default == None).
								if self.settingsEnabled(type = data[i]['category']['type'], mode = data[i]['category']['mode'], access = data[i]['category']['access'], addon = data[i]['addon']['id'], id = data[i]['id'], data = settings) is False:
									continue
							if not id is None:
								if not data[i]['id'] == id: continue
							if not addon is None:
								if not data[i]['addon']['id'] == addon: continue
							if not media is None:
								if not data[i]['support'][media]: continue
							if not type is None:
								if not data[i]['category']['type'] == type: continue
							if not mode is None:
								if not data[i]['category']['mode'] == mode: continue
							if not access is None:
								if not data[i]['category']['access'] == access: continue

							source = imp.load_source(data[i]['file']['id'], data[i]['file']['path'])
							object = source.Provider(data = data[i])

							if full:
								enabledSupport = True
								if type == handler.Handler.TypeTorrent:
									if not supportTorrent: enabledSupport = False
								elif type == handler.Handler.TypeUsenet:
									if not supportUsenet: enabledSupport = False
								elif type == handler.Handler.TypeHoster:
									if not supportHoster: enabledSupport = False
								object.enableSupport(enabledSupport)

								enabledDeveloper = True
								if object.developer(): enabledDeveloper = developer
								object.enableDeveloper(enabledDeveloper)

								object.enableFailure(not object.id() in failures)

							providers.append(object)
						except: Logger.error()

					if settings: self.settingsRetrieve(providers = providers, preset = preset)
					return providers
		except: Logger.error()
		return None

	@classmethod
	def _providersDatabaseUpdate(self, providers = None, provider = None):
		try:
			if not providers and provider:
				id = provider.id()
				providers = Converter.jsonFrom(self._providersDatabaseInitialize()._selectValue('SELECT data FROM %s;' % (Manager.DatabaseProviders)))
				for i in range(len(providers)):
					if providers[i]['id'] == id:
						providers[i] = provider
						break

			self.databaseClear()
			data = '"%s"' % Converter.jsonTo(providers).replace('"', '""').replace("'", "''")
			self._providersDatabaseInitialize()._insert('INSERT INTO %s (version, data) VALUES ("%s", %s);' % (Manager.DatabaseProviders, System.version(), data))
		except: Logger.error()

	@classmethod
	def _providersCache(self, id = None, addon = None, enabled = None, media = None, type = None, mode = None, access = None, preset = None, module = None):
		cache = [id, addon, enabled, media, type, mode, access, module]
		if preset: cache.append(preset['id'])
		if not any(cache): return False
		cache = [' ' if i is None else str(i) for i in cache]
		return '_'.join(cache)

	@classmethod
	def _providersClear(self):
		Manager.ProvidersData = None
		Manager.ProvidersCache = None

	@classmethod
	def providersInitialize(self, full = True, progress = False, id = None, exclude = None, description = None, addon = None, enabled = None, media = None, type = None, mode = None, access = None, local = None, external = None, preset = None, settings = True, module = False, reload = False):
		typeNew = type
		if local: typeNew = ProviderBase.TypeLocal
		elif external: typeNew = ProviderBase.TypeExternal
		cache = self._providersCache(id = id, addon = addon, enabled = enabled, media = media, type = typeNew, mode = mode, access = access, preset = preset, module = module)
		if not Manager.ProvidersCache is False and not Manager.ProvidersCache == cache:
			Manager.ProvidersData = None
			Manager.ProvidersCache = cache

		if Manager.ProvidersData is None: self._providersInitialize(full = full, progress = progress, id = id, addon = addon, enabled = enabled, media = media, type = typeNew, mode = mode, access = access, preset = preset, settings = settings, module = module)
		elif reload and settings: self.settingsRetrieve(providers = Manager.ProvidersData, preset = preset)

		return Manager.ProvidersData

	@classmethod
	def _providersInitialize(self, full = True, progress = False, id = None, addon = None, enabled = None, media = None, type = None, mode = None, access = None, preset = None, settings = True, module = False):
		from lib.modules import interface
		try:
			progressDialog = None
			Manager.ProvidersData = []

			if module: data = None # Make sure to load the "dummy" or not-installed addons. Should only happen from the settings dialog.
			else: data = self._providersDatabaseRetrieve(full = full, id = id, addon = addon, enabled = enabled, media = media, type = type, mode = mode, access = access, preset = preset, settings = settings)

			if data is None:
				if progress:
					progressDialog = interface.Dialog.progress(title = 35147, message = 35148, background = True)
					total = 200 # +- the total number of providers

				providers = []
				data = []
				files = []

				path1 = os.path.join(System.path(), 'lib', 'providers')
				for _, name1, _ in pkgutil.walk_packages([path1]):
					path2 = os.path.join(path1, name1)
					for _, name2, _ in pkgutil.walk_packages([path2]):
						path3 = os.path.join(path2, name2)
						for _, name3, _ in pkgutil.walk_packages([path3]):
							path4 = os.path.join(path3, name3)
							for _, name4, package in pkgutil.walk_packages([path4]):
								if not package:
									files.append([path4, name4])
									if progress: progressDialog.update(int(40 * (len(files) / total)))

				if progress:
					total = len(files)
					providersExtras = 0

				for file in files:
					try:
						id = file[1]
						name = id + '.py'
						directory = file[0]
						path = os.path.join(directory, name)

						object = imp.load_source(id, path).Provider(initialize = True)

						instances = []
						try:
							instances = object.instances()
							if module and not instances: instances.append(object) # Show "supported" external addons in the settings dialog.
						except: instances.append(object)

						instancesMulti = len(instances) > 1
						if progress and instancesMulti: providersExtras += len(instances) - 1

						for instance in instances:
							providers.append(instance)
							if progress:
								total = len(files)
								progressDialog.update(int(30 + (50 * ((len(providers) - providersExtras) / float(total)))))

					except ImportError:
						if ProviderBase.logDeveloper(): Logger.error() # Do not log errors for non-installed external scraping addons.
					except Exception as error:
						Logger.log('A provider could not be loaded (%s): %s.' % (str(id), str(error)))
						Logger.error()

				if module:
					if progress: progressDialog.update(80)
					self.settingsRetrieve(providers = providers)
					data = providers
					if progress: progressDialog.update(100)
				else:
					if progress: progressDialog.update(80)
					self._providersDatabaseUpdate(providers = providers)
					if progress: progressDialog.update(85)
					data = self._providersDatabaseRetrieve(preset = preset, settings = settings)
					if progress: progressDialog.update(95)
					if settings: self._providersUpdate(providers = data)
					if progress: progressDialog.update(100)

			Manager.ProvidersData = data
		except Exception as error:
			Logger.log('The providers could not be loaded (%s).' % str(error))
			Logger.error()

		if progressDialog:
			try: progressDialog.close()
			except: pass

		return Manager.ProvidersData

	@classmethod
	def _providersUpdate(self, providers):
		# Update the settings with links in case the provider code was updated with new domains.
		# Maintain the old custom domains the user added before the update.
		# Also maintain the order if the user moved domains up/down.
		try:
			for provider in providers: provider.linksClean()
			self.settingsUpdate(providers)
		except: Logger.error()

	'''
		FUNCTION:
			Retrieve a list of providers according to specified attributes.
		PARAMETERS:
			id (None/string/list): The provider ID.
			exclude (None/string/list): The provider ID to exclude.
			description (None/string): A fuzzy description to match against the provider ID, name, and file name.
			addon (None/string): The addon ID the provider comes from.
			enabled (None/boolean): The enabled status of the provider.
			media (None/string): The media type of the provider.
			type (None/string): The category type of the provider.
			mode (None/string): The category mode of the provider.
			access (None/string): The category access of the provider.
			local (None/boolean): If local providers should be included.
			external (None/boolean): If external providers should be included.
			preset (None/string/dictionary): The preset data or ID.
			module (boolean): Also load "dummy" external addon modules that are not installed.
			reload (None/boolean): Reload the provider settings if they are already in cache.
			sort (boolean): Sort the providers according to various attributes, from best to worst providers.
	'''
	@classmethod
	def providers(self, id = None, exclude = None, description = None, addon = None, enabled = None, media = None, type = None, mode = None, access = None, local = None, external = None, preset = None, settings = True, module = False, reload = False, sort = False):
		typeMulti = Tools.isArray(type)
		modeMulti = Tools.isArray(mode)
		accessMulti = Tools.isArray(access)

		preset = self.presetsRetrieve(preset)
		providers = self.providersInitialize(id = id, exclude = exclude, description = description, addon = addon, enabled = enabled, media = media, type = None if typeMulti else type, mode = None if modeMulti else mode, access = None if accessMulti else access, local = local, external = external, preset = preset, settings = settings, module = module, reload = reload)

		if not id is None:
			if not Tools.isArray(id): id = [id]
			providers = [i for i in providers if i.id() in id]

		if not exclude is None:
			if not Tools.isArray(exclude): exclude = [exclude]
			providers = [i for i in providers if not i.id() in exclude]

		if not description is None:
			providers = [i for i in providers if i.match(description = description, exact = False)]

		if not addon is None:
			if not Tools.isArray(addon): addon = [addon]
			providers = [i for i in providers if i.addonId() in addon]

		if not enabled is None: providers = [i for i in providers if i.enabled() == enabled]
		if not media is None: providers = [i for i in providers if media in i.supportMedia()]
		if not type is None:
			if typeMulti: providers = [i for i in providers if i.type() in type]
			else: providers = [i for i in providers if i.type() == type]
		if not mode is None:
			if modeMulti: providers = [i for i in providers if i.mode() in mode]
			else: providers = [i for i in providers if i.mode() == mode]
		if not access is None:
			if accessMulti: providers = [i for i in providers if i.access() in access]
			else: providers = [i for i in providers if i.access() == access]
		if not local is None: providers = [i for i in providers if i.typeLocal() == local]
		if not external is None: providers = [i for i in providers if i.typeExternal() == external]

		if sort:
			# Randomize the provider order.
			# In case a concurrency limit is used (not all providers are started at the same time), some providers that take longer than others might always start last and then just unnecessarily increase the scraping time.
			# If shuffeled, these slow providers will not always be last, but sometimes are executed first.
			# Below we sort tyhe providers, but providers with the same rank will be shuffeled internally.
			providers = Tools.listShuffle(providers)

			# Sort by order (rank + performance + type + status).
			providers = sorted(providers, key = lambda i : i.order(), reverse = True)

		return providers

	@classmethod
	def provider(self, id = None, exclude = None, description = None, addon = None, enabled = None, media = None, type = None, mode = None, access = None, local = None, external = None):
		try: return self.providers(id = id, exclude = exclude, description = description, addon = addon, enabled = enabled, media = media, type = type, mode = mode, access = access, local = local, external = external)[0]
		except: return None

	@classmethod
	def providersCount(self, id = None, exclude = None, description = None, addon = None, enabled = None, media = None, type = None, mode = None, access = None, local = None, external = None):
		return len(self.providers(id = id, exclude = exclude, description = description, addon = addon, enabled = enabled, media = media, type = type, mode = mode, access = access, local = local, external = external))

	@classmethod
	def providersLanguages(self, id = None, exclude = None, description = None, addon = None, enabled = None, media = None, type = None, mode = None, access = None, local = None, external = None, universal = True, english = True):
		providers = self.providers(id = id, exclude = exclude, description = description, addon = addon, enabled = enabled, media = media, type = type, mode = mode, access = access, local = local, external = external)

		languages = []
		for provider in providers:
			languages.extend(provider.languages())
		languages = Tools.listUnique(languages)

		if not universal:
			try: del languages[Language.UniversalCode]
			except: pass
		if not english:
			try: del languages[Language.EnglishCode]
			except: pass

		return languages

	##############################################################################
	# HELP
	##############################################################################

	@classmethod
	def _help(self, label, description = None, items = None):
		from lib.modules.interface import Format, Translation

		newline = Format.fontNewline()
		colorPrimary = Format.colorPrimary()
		colorSecondary = Format.colorSecondary()

		message = Format.font(label, bold = True, uppercase = True, color = colorPrimary) + newline + newline
		if description:
			message += Translation.string(description) + newline + newline
		if items:
			separator = Format.iconSeparator(color = colorPrimary, padRight = True, bold = True)
			for item in items:
				try: message += separator + Format.font(Translation.string(item['label']) + ': ', bold = True, color = colorSecondary) + Translation.string(item['description']) + newline
				except: message += separator + item + newline
			message += newline
		return message

	@classmethod
	def help(self, description = None, mirrors = None, settings = None, settingsGeneral = None, settingsScrape = None, settingsCustom = None, settingsProvider = None):
		message = ''
		if description: message += self._help(label = 33040, description = description)
		if mirrors: message += self._help(label = 33422, description = 35788, items = mirrors)
		if settings: message += self._help(label = 33011, items = settings)
		if settingsGeneral: message += self._help(label = 35751, items = settingsGeneral)
		if settingsScrape: message += self._help(label = 35752, items = settingsScrape)
		if settingsCustom: message += self._help(label = 35754, items = settingsCustom)
		if settingsProvider: message += self._help(label = 35753, items = settingsProvider)
		return message

	##############################################################################
	# VERIFY
	##############################################################################

	@classmethod
	def verify(self, providers = None, type = None, mode = None, access = None, addon = None, enabled = None, internal = False):
		try:
			from lib.modules.interface import Dialog, Format, Translation, Loader

			title = Translation.string(33017)

			single = providers and not Tools.isArray(providers)
			if single:
				providers = [providers]
			else:
				if enabled is None:
					items = [
						{'title' : Dialog.prefixBack(35374 if internal else 33486), 'close' : True, 'return' : 0},
						{'title' : Dialog.prefixNext(33239), 'action' : self._verifyHelp},
						'',
						{'title' : Dialog.prefixNext(35763), 'close' : True, 'return' : 1},
						{'title' : Dialog.prefixNext(35764), 'close' : True, 'return' : 2},
						{'title' : Dialog.prefixNext(35765), 'close' : True, 'return' : 3},
					]
					choice = Dialog.information(title = title, items = items, reselect = Dialog.ReselectYes)
					if choice is None: return False
					elif choice == 0: return True
					elif choice == 2: enabled = True
					elif choice == 3: enabled = False

				if providers is None:
					Loader.show()
					providers = self.providers(type = type, mode = mode, access = access, addon = addon)
					if enabled is True: providers = [provider for provider in providers if provider.enabledSettings()]
					elif enabled is False: providers = [provider for provider in providers if not provider.enabledSettings()]
					Loader.hide()
				else:
					if enabled is True: providers = [provider for provider in providers if provider.enabledSettingsProvider()]
					elif enabled is False: providers = [provider for provider in providers if not provider.enabledSettingsProvider()]

			message = Translation.string(35762 if single else 33019)
			dialog = Dialog.progress(title = title, message = Format.fontBold(message))

			colors = {item : Tools.getFunction(Format, ProviderBase.VerifyColors[item])() for item in ProviderBase.VerifyValues}
			values = {item : Format.font(ProviderBase.VerifyLabels[item], color = Tools.getFunction(Format, ProviderBase.VerifyColors[item])()) for item in ProviderBase.VerifyValues}
			labels = {key : Translation.string(value) for key, value in ProviderBase.VerifyLabels.items()}

			results = []
			Manager.VerifyCanceled = False
			Manager.VerifyResults = []

			threads = [Pool.thread(target = self._verify, args = (provider,)) for provider in providers]
			[thread.start() for thread in threads]

			items = None
			dots = ' '
			total = float(len(threads))

			if single:
				progress = 1
				while True:
					if dialog.iscanceled():
						dialog.close()
						Loader.show()
						[provider.stop() for provider in providers]
						Loader.hide()
						Manager.VerifyCanceled = True
						break

					busy = len([thread for thread in threads if thread.is_alive()])
					if busy == 0: break
					progress += 2
					progress = min(progress, 99)

					dots += '.'
					if len(dots) >= 5: dots = ' '

					dialog.update(progress, Format.fontBold(message + dots))
					Time.sleep(0.5)

				if Manager.VerifyResults:
					verification = Manager.VerifyResults[0][1]
					for item in ProviderBase.VerifyOrder:
						type = verification[item][ProviderBase.VerifyType]
						reason = verification[item][ProviderBase.VerifyReason]
						if not type is None:
							value = ProviderBase.VerifyLabels[type]
							if reason:
								try: value = '%s (%s %s)' % (Translation.string(value), Translation.string(ProviderBase.VerifyLabels[reason]), Translation.string(ProviderBase.VerifyLabels[ProviderBase.VerifyError]))
								except: pass # Unknown errors (does not have a label in VerifyLabels)
							results.append({
								'title' : ProviderBase.VerifyLabels[item],
								'value' : Format.font(value, color = Tools.getFunction(Format, ProviderBase.VerifyColors[type])()),
								'color' : False,
							})

					items = [
						{'title' : Dialog.prefixBack(35374), 'close' : True},
						{'title' : 33690, 'items' : results},
					]
			else:
				indent = '   '
				labelProvider = Translation.string(33681)
				labelProviders = Translation.string(32345)
				labelBusy = '%s%s%s: %s' % (Format.fontNewline(), indent, Translation.string(33291), '%d')
				separator = Format.iconSeparator(color = True, pad = True)
				labelFinished = '%s%s%s: %s [ %s%s%s%s%s ]' % (Format.fontNewline(), indent, Translation.string(35755), '%d', '%s', separator, '%s', separator, '%s')

				while True:
					if dialog.iscanceled():
						dialog.close()
						Loader.show()
						[provider.stop() for provider in providers]
						Loader.hide()
						Manager.VerifyCanceled = True
						break

					busy = len([thread for thread in threads if thread.is_alive()])
					if busy == 0: break
					progress = int(round(((total - busy) / total) * 100))

					stats = {type : 0 for type in ProviderBase.VerifyValues}
					for result in Manager.VerifyResults:
						result = [i[ProviderBase.VerifyType] for i in result[1].values()]
						for type in reversed(ProviderBase.VerifyValues):
							if type in result:
								stats[type] += 1
								break

					success = Format.font('%d%% %s' % (int(round((stats[ProviderBase.VerifySuccess] / total) * 100)), labels[ProviderBase.VerifySuccess]), color = colors[ProviderBase.VerifySuccess])
					limited = Format.font('%d%% %s' % (int(round((stats[ProviderBase.VerifyLimited] / total) * 100)), labels[ProviderBase.VerifyLimited]), color = colors[ProviderBase.VerifyLimited])
					failed = Format.font('%d%% %s' % (int(round((stats[ProviderBase.VerifyFailure] / total) * 100)), labels[ProviderBase.VerifyFailure]), color = colors[ProviderBase.VerifyFailure])

					dots += '.'
					if len(dots) >= 5: dots = ' '

					extra = ''
					extra += labelBusy % busy
					extra += labelFinished % ((total - busy), success, limited, failed)

					dialog.update(progress, Format.fontBold(message + dots) + extra)
					Time.sleep(0.5)

				verifications = Manager.VerifyResults
				for verification in verifications:
					rank = 0
					items = []
					for item in ProviderBase.VerifyOrder:
						type = verification[1][item][ProviderBase.VerifyType]
						if not type is None:
							if type == ProviderBase.VerifyFailure: rank -= 100
							elif type == ProviderBase.VerifyLimited: rank -= 10
							items.append(Format.fontColor(labels[item], color = colors[type]))
					items = Format.iconJoin(items)
					results.append((rank, {
						'title' : verification[0].label(),
						'value' : items,
						'color' : False,
					}))
				results.sort(key = lambda i : (i[0], i[1]['title'].lower()))
				results = [i[1] for i in results]

				stats = {type : 0 for type in ProviderBase.VerifyValues}
				for result in Manager.VerifyResults:
					result = [i[ProviderBase.VerifyType] for i in result[1].values()]
					for type in reversed(ProviderBase.VerifyValues):
						if type in result:
							stats[type] += 1
							break

				summary = []
				total = float(len(Manager.VerifyResults))
				for type in ProviderBase.VerifyValues:
					summary.append({
						'title' : Format.font(labels[type], bold = True, color = colors[type]),
						'value' : '%s (%d %s)' % (Format.font('%d%%' % int(round((stats[type] / total) * 100)) if total else 0, bold = True), stats[type], labelProvider if stats[type] == 1 else labelProviders),
						'bold' : False,
						'color' : False,
					})

				items = [
					{'title' : Dialog.prefixBack(35374 if internal else 33486), 'close' : True, 'return' : 0},
					{'title' : Dialog.prefixNext(33239), 'action' : self._verifyHelp},
					{'title' : Dialog.prefixNext(33183), 'action' : self._verifyToggle, 'parameters' : {'results' : Manager.VerifyResults}},

					{'title' : 33690, 'items' : summary},
					{'title' : 32345, 'items' : results},
				]

			dialog.close()
			if items:
				choice = Dialog.information(title = title, items = items, reselect = Dialog.ReselectYes)
				return not choice is None and not choice == -1 and not Manager.VerifyCanceled
			return True
		except: Logger.error()

	@classmethod
	def _verify(self, provider):
		verify = provider.verify()
		if not Manager.VerifyCanceled: Manager.VerifyResults.append((provider, verify))

	@classmethod
	def _verifyToggle(self, results, enable = None, verify = None):
		if enable is None:
			from lib.modules.interface import Dialog
			items = [
				{'title' : Dialog.prefixBack(35374), 'close' : True},
				{'title' : Dialog.prefixNext(35766), 'close' : True, 'action' : self._verifyToggle, 'parameters' : {'results' : results, 'enable' : True, 'verify' : None}},
				{'title' : Dialog.prefixNext(35756), 'close' : True, 'action' : self._verifyToggle, 'parameters' : {'results' : results, 'enable' : True, 'verify' : ProviderBase.VerifySuccess}},
				{'title' : Dialog.prefixNext(35757), 'close' : True, 'action' : self._verifyToggle, 'parameters' : {'results' : results, 'enable' : True, 'verify' : ProviderBase.VerifyLimited}},
				{'title' : Dialog.prefixNext(35758), 'close' : True, 'action' : self._verifyToggle, 'parameters' : {'results' : results, 'enable' : True, 'verify' : ProviderBase.VerifyFailure}},
				{'title' : Dialog.prefixNext(35759), 'close' : True, 'action' : self._verifyToggle, 'parameters' : {'results' : results, 'enable' : False, 'verify' : ProviderBase.VerifySuccess}},
				{'title' : Dialog.prefixNext(35760), 'close' : True, 'action' : self._verifyToggle, 'parameters' : {'results' : results, 'enable' : False, 'verify' : ProviderBase.VerifyLimited}},
				{'title' : Dialog.prefixNext(35761), 'close' : True, 'action' : self._verifyToggle, 'parameters' : {'results' : results, 'enable' : False, 'verify' : ProviderBase.VerifyFailure}},
			]
			Dialog.information(title = 33017, items = items, reselect = Dialog.ReselectYes)
		else:
			providers = []
			for result in results:
				values = [i['type'] for i in result[1].values()]
				for type in reversed(ProviderBase.VerifyValues):
					if type in values:
						if verify is None:
							result[0].enableSettingsProvider(enable = (type == ProviderBase.VerifySuccess or type == ProviderBase.VerifyLimited))
							providers.append(result[0])
						elif verify == type:
							result[0].enableSettingsProvider(enable = enable)
							providers.append(result[0])
						break
			self.settingsUpdate(providers)

	@classmethod
	def _verifyHelp(self):
		from lib.modules.interface import Dialog, Format
		items = [
			{'type' : 'title', 'value' : 'Verification Steps', 'break' : 2},
			{'type' : 'text', 'value' : 'Providers are verified in two steps. During the first step, the domain of the provider is tested to see if it is valid and reachable. During the second step, the provider is scraped with a few predefined titles to see if any valid results are returned.', 'break' : 2},
			{'type' : 'title', 'value' : 'Verification Statuses', 'break' : 2},
			{'type' : 'text', 'value' : 'Providers have the following verification statuses for both the domain and the scraping:', 'break' : 2},
			{'type' : 'list', 'color' : False, 'value' : [
				{'title' : Format.fontColor('Success (Green)', color = Tools.getFunction(Format, ProviderBase.VerifyColors[ProviderBase.VerifySuccess])()), 'value' : 'Everything worked as intended and is fully operational. A domain with success status means the domain is up and reachable. Note that many providers have multiple mirror domains. The success status indicates that one of the mirror domains was reachable, not necessarily the first main domain. Scraping with success status means that valid links were returned from the provider. This means that the current website or API structure of the provider is still up to date in Gaia.'},
				{'title' : Format.fontColor('Limited (Yellow)', color = Tools.getFunction(Format, ProviderBase.VerifyColors[ProviderBase.VerifyLimited])()), 'value' : 'There are certain limitations that might in some cases, but not necessarily always, prevent the provider from working as intended. This can be caused by a variety of reasons, such as temporary server outages or bugs in the website code. However, in most cases this is caused by strict Cloudflare protection of a website. Cloudflare often prevents automated scripts from accessing websites. Some of these restrictions can be bypassed, but with recent changes to Cloudflare, most of the blocking remains impassable. Note that the Cloudflare protection is increased if you are using a VPN. Disabling your VPN often helps removing these Cloudflare protection mechanisms. A domain with limited status almost always means Cloudflare blocking, but in few cases can also indicate temporary unrelated issues with the domain. If the domain is successful, but the scraping is limited, it often means that the website does not have Cloudflare protection on the main site, but does have Cloudflare protection on the search page.'},
				{'title' : Format.fontColor('Failure (Red)', color = Tools.getFunction(Format, ProviderBase.VerifyColors[ProviderBase.VerifyFailure])()), 'value' : 'There are major issues that prevent the provider from working. A domain with failed status means that the domain is down or returns some unrecoverable error. If scraping fails, it means the server is down and often indicates the provider and its website are dead, in many cases permanently. If the domain is still active and you can view the working website in a browser, but scraping fails in Gaia, it is most likely that the website changed its structure making it incompatible with the code in Gaia. In such a case, please open a support ticket on Gaia\'s website to get the code updated with the new provider structure.'},
			]},
		]
		Dialog.details(title = 33017, items = items)

	##############################################################################
	# SETTINGS
	##############################################################################

	@classmethod
	def settingsEnabled(self, data = None, type = None, mode = None, access = None, addon = None, id = None):
		if data is None: data = self.settingsLoad()
		if not data: return None
		if type:
			if not data[type]['enabled']: return False
			elif mode:
				if not data[type]['data'][mode]['enabled']: return False
				elif access:
					if not data[type]['data'][mode]['data'][access]['enabled']: return False
					else:
						if not addon: addon = ProviderBase.addonGaiaId()
						if not data[type]['data'][mode]['data'][access]['data'][addon]['enabled']: return False
						else:
							try:
								if id and not data[type]['data'][mode]['data'][access]['data'][addon]['data'][id]['enabled']: return False
							except:
								return None # If "enabled" was not set, it is None (default).
		return True

	@classmethod
	def settingsCount(self, providers = None, type = None, mode = None, access = None, addon = None, label = False, total = False):
		try:
			def labelProviders(count):
				from lib.modules.interface import Translation
				return '%d %s' % (count, Translation.string(33681 if count == 1 else 32345))
			def labelDisabled(count = None):
				from lib.modules.interface import Format
				return Format.fontColor(32302 if count is None else labelProviders(count), color = Format.colorBad())
			def labelEnabled(count):
				from lib.modules.interface import Format
				return Format.fontColor(labelProviders(count), color = Format.colorPoor() if count == 0 else Format.colorExcellent())

			if providers is None: providers = self.providers(type = type, mode = mode, access = access, addon = addon, reload = True)
			if not providers: return None

			enabled = [i for i in providers if i.enabledSettings(type = not type, mode = not mode, access = not access, addon = not addon) and i.enabledInternal()]
			account = [i for i in enabled if i.enabledAccount()]

			countAll = len(providers)
			countEnabled = len(enabled)
			countAccount = len(account)

			if label:
				if total: return labelProviders(countAccount)

				if addon:
					if not providers[0].enabledSettingsAddon(): return labelDisabled()
				elif access:
					if not providers[0].enabledSettingsAccess(): return labelDisabled()
				elif mode:
					if not providers[0].enabledSettingsMode(): return labelDisabled()
				elif type:
					if not providers[0].enabledSettingsType(): return labelDisabled()

				# For flattened menus.
				type2, mode2, access2 = self.settingsFlatten(type = type, mode = mode, access = access)
				if not type == type2 or not mode == mode2 or not access == access2:
					if not providers[0].enabledSettings(type = False if type2 is None else True, mode = False if mode2 is None else True, access = False if access2 is None else True, addon = False, provider = False):
						return labelDisabled()

				if countAccount == 0:
					# Color the subcategories red if one of the main categories was disabled.
					# Only color orange if the parent categories are all enabled
					if countEnabled:
						if addon:
							if not enabled[0].enabledSettingsAccess(): return labelDisabled(countAccount)
						elif access:
							if not enabled[0].enabledSettingsMode(): return labelDisabled(countAccount)
						elif mode:
							if not enabled[0].enabledSettingsType(): return labelDisabled(countAccount)
						return labelEnabled(countAccount)
					elif countAll: return labelDisabled(countAccount)
					else: return labelDisabled()

				if account[0].enabledSettings(provider = False): return labelEnabled(countAccount)
				else: return labelDisabled(countAccount)
			else: return countAccount
		except: Logger.error()
		return '' if label else 0

	@classmethod
	def settingsToggle(self, data = None, providers = None, language = None, native = None, type = None, mode = None, access = None, addon = None, enable = None):
		if data is None: data = self.settingsLoad()
		if not data is None:
			if providers:
				if not Tools.isArray(providers): providers = [providers]
				if native:
					[provider.instanceToggle() for provider in providers]
				else:
					if language: providers = [provider for provider in providers if provider.language() == language]
					if enable is None:
						count = len(providers)
						enable = sum([1 if i.enabledSettingsProvider() else -1 for i in providers])
						if enable == count: enable = False
						elif enable == -count: enable = True
						elif enable < (count / 2): enable = True
						else: enable = False
					[provider.enableSettingsProvider(enable) for provider in providers]
				self.settingsUpdate(providers = providers, data = data)
			elif type:
				# Enable all parent categories backward.
				# Important for external providers which are disabled by default.
				enabled = not data[type]['enabled']
				if mode:
					enabled = enabled or not data[type]['data'][mode]['enabled']
					if access:
						enabled = enabled or not data[type]['data'][mode]['data'][access]['enabled']
						if addon:
							enabled = enabled or not data[type]['data'][mode]['data'][access]['data'][addon]['enabled']
							data[type]['data'][mode]['data'][access]['data'][addon]['enabled'] = enabled
						if enabled or not addon: data[type]['data'][mode]['data'][access]['enabled'] = enabled
					if enabled or not access: data[type]['data'][mode]['enabled'] = enabled
				if enabled or not mode: data[type]['enabled'] = enabled

				self.settingsSave(data = data)

	@classmethod
	def settingsToggleDefault(self, data = None, save = True):
		if data is None: data = self.settingsLoad()

		for type in data.keys():
			data[type]['enabled'] = ProviderBase.TypesData[type]['enabled']
			for mode in data[type]['data'].keys():
				data[type]['data'][mode]['enabled'] = ProviderBase.ModesData[mode]['enabled']
				for access in data[type]['data'][mode]['data'].keys():
					data[type]['data'][mode]['data'][access]['enabled'] = ProviderBase.AccessesData[access]['enabled']
					for addon in data[type]['data'][mode]['data'][access]['data'].keys():
						data[type]['data'][mode]['data'][access]['data'][addon]['enabled'] = True

		if save: self.settingsSave(data = data)

	@classmethod
	def settingsDefault(self, data = None, providers = None, attributes = None, type = None, mode = None, access = None, addon = None):
		if data is None: data = self.settingsLoad()
		if providers is None:
			if type:
				if addon: del data[type]['data'][mode]['data'][access]['data'][addon]
				elif access: del data[type]['data'][mode]['data'][access]
				elif mode: del data[type]['data'][mode]
				elif type: del data[type]
			else:
				data = {}
		else:
			if not Tools.isArray(providers): providers = [providers]
			if attributes and not Tools.isArray(attributes): attributes = [attributes]

			for provider in providers:
				id = provider.id()
				values = data[provider.type()]['data'][provider.mode()]['data'][provider.access()]['data'][provider.addonId()]['data']
				if attributes:
					value = values[id]
					for attribute in attributes:
						try:
							if Tools.isArray(attribute): del value[attribute[0]][attribute[1]]
							else: del value[attribute]
						except: pass
					values[id] = value
				else:
					values[id] = {}

		self.settingsSave(data = data)
		if providers is None:
			self._providersClear() # Important to reload providers correctly (eg: toggle a specific external provider, go to the main menu withoutu closing the dialog, and click Default = the provider toggle is not reset).
			providers = self.providers(type = type, mode = mode, access = access, addon = addon, reload = True)
		else: self.settingsRetrieve(providers = providers, data = data)
		self.settingsUpdate(providers = providers, data = data)

	@classmethod
	def settingsFlatten(self, data = None, type = None, mode = None, access = None):
		def contains(data, key = None):
			if key:
				if not key in data: return False
				data = data[key]
			for key, value in data['data'].items():
				if 'data' in value:
					if contains(value): return True
				elif value: return True
			return False

		if data is None: data = self.settingsLoad()
		if not data: return None, None, None

		types = []
		for i in ProviderBase.Types:
			if contains(data, i):
				types.append(i)
				if len(types) > 1: break
		if len(types) == 1: type = types[0]

		if type and type in data:
			data = data[type]['data']

			modes = []
			for i in ProviderBase.Modes:
				if contains(data, i):
					modes.append(i)
					if len(modes) > 1: break
			if len(modes) == 1: mode = modes[0]

			if mode and mode in data:
				data = data[mode]['data']

				accesses = []
				for i in ProviderBase.Accesses:
					if contains(data, i):
						accesses.append(i)
						if len(accesses) > 1: break
				if len(accesses) == 1: access = accesses[0]

		return type, mode, access

	@classmethod
	def settingsRetrieve(self, providers, data = None, preset = None):
		try:
			if data is None: data = self.settingsLoad()
			if preset: data.update(preset)

			if not Tools.isArray(providers): providers = [providers]
			for provider in providers:
				try:
					id = provider.id()
					type = provider.type()
					mode = provider.mode()
					access = provider.access()
					addon = provider.addonId()

					try: enabledType = data[type]['enabled']
					except: enabledType = ProviderBase.TypesData[type]['enabled']
					try: enabledMode = data[type]['data'][mode]['enabled']
					except: enabledMode = ProviderBase.ModesData[mode]['enabled']
					try: enabledAccesss = data[type]['data'][mode]['data'][access]['enabled']
					except: enabledAccesss = ProviderBase.AccessesData[access]['enabled']
					try: enabledAddon = data[type]['data'][mode]['data'][access]['data'][addon]['enabled']
					except: enabledAddon = None

					try: settings = data[type]['data'][mode]['data'][access]['data'][addon]['data'][id]
					except: settings = None

					try: enabledProvider = settings['enabled']
					except: enabledProvider = provider.enabledDefault()
					try: account = settings['account']
					except: account = None
					try: link = settings['link']
					except: link = provider.links(settings = False, deleted = True, flat = False)
					try: scrape = settings['scrape']
					except: scrape = provider.scrape(settings = False)
					try: custom = settings['custom']
					except: custom = provider.custom(settings = False)

					provider.enableSettingsType(enabledType)
					provider.enableSettingsMode(enabledMode)
					provider.enableSettingsAccess(enabledAccesss)
					provider.enableSettingsAddon(enabledAddon)
					provider.enableSettingsProvider(enabledProvider)
					provider.accountSet(account)
					provider.linkSet(link, settings = True)
					provider.scrapeSet(scrape, settings = True)
					provider.customSet(custom, settings = True)

					provider.initialize()
				except: Logger.error()
		except: Logger.error()

	@classmethod
	def settingsUpdate(self, providers, data = None, internal = False):
		try:
			if data is None and not internal: data = self.settingsLoad()
			if not data: data = {}

			if not Tools.isArray(providers): providers = [providers]
			for provider in providers:
				id = provider.id()
				type = provider.type()
				mode = provider.mode()
				access = provider.access()
				addon = provider.addonId()

				settings = {
					'enabled'		: provider.enabledSettingsProvider(),
					'account'		: provider.account(),
					'link'			: provider.links(settings = True, deleted = True, flat = False),
					'scrape'		: provider.scrape(settings = True),
					'custom'		: provider.custom(settings = True)
				}
				settings = {key : value for key, value in settings.items() if not value is None} # Remove None values to reduce size.

				if not type in data: data[type] = {'enabled' : ProviderBase.TypesData[type]['enabled'], 'data' : {}}
				if not mode in data[type]['data']: data[type]['data'][mode] = {'enabled' : ProviderBase.ModesData[mode]['enabled'], 'data' : {}}
				if not access in data[type]['data'][mode]['data']: data[type]['data'][mode]['data'][access] = {'enabled' : ProviderBase.AccessesData[access]['enabled'], 'data' : {}}
				if not addon in data[type]['data'][mode]['data'][access]['data']: data[type]['data'][mode]['data'][access]['data'][addon] = {'enabled' : True, 'data' : {}}
				data[type]['data'][mode]['data'][access]['data'][addon]['data'][id] = settings

			self.settingsSave(data = data)
		except:
			Logger.error()
		return data

	@classmethod
	def settingsLoad(self, basic = False):
		data = Settings.getData(Manager.SettingsConfigurationData)

		if data is None:
			# In case the settings entry was deleted, but providers.db was not deleted, causing the providers/settings not to reinitialize.
			# Initialize settings manually here.
			data = self.settingsUpdate(providers = self.providers(settings = False), data = data, internal = True)

		if basic: # Used by presets.
			providers = self.providers()
			providers = {i.id() : i.enabledDefault() for i in providers}
			data = Tools.copy(data) # Important, since we edit the dictionary.
			for key1, value1 in data.items():
				for key2, value2 in value1['data'].items():
					for key3, value3 in value2['data'].items():
						for key4, value4 in value3['data'].items():
							for key5, value5 in value4['data'].items():
								delete = []
								for key6, value6 in value5.items():
									if key6 == 'enabled':
										if value6 is None: value5['enabled'] = providers[key5] # Set the default value if not in the settings.
									else: delete.append(key6) # Cannot delete during iteration.
								for key6 in delete:
									del value5[key6]
								if not 'enabled' in value5: value5['enabled'] = providers[key5] # Set the default value if not in the settings.

		return data

	@classmethod
	def settingsSave(self, data, count = False, wait = False):
		Settings.setData(Manager.SettingsConfigurationData, data)
		if count: self.settingsLabel(wait = wait)

	@classmethod
	def settingsLabel(self, count = None, wait = False):
		if count is None:
			def countUpdate():
				count = self.settingsCount(label = True, total = True)
				Settings.setLabel(Manager.SettingsConfigurationData, count)
				Manager.SettingsLock.release()

			Manager.SettingsLock.acquire()
			Manager.SettingsThread = Pool.thread(target = countUpdate)
			Manager.SettingsThread.start()
			if wait: Manager.SettingsThread.join()
		else:
			Settings.setLabel(Manager.SettingsConfigurationData, count, background = not wait)

	@classmethod
	def settingsLabelWait(self):
		if Manager.SettingsThread: Manager.SettingsThread.join()

	@classmethod
	def settings(self, id = None, type = None, mode = None, access = None, addon = None, settings = False):
		from lib.modules.tools import Extension, Language
		from lib.modules.interface import Dialog, Format, Loader, Translation

		Loader.show()
		bullet = Format.iconBullet(color = Format.colorSecondary())
		bulletGood = Format.iconBullet(color = Format.colorExcellent())
		bulletMedium = Format.iconBullet(color = Format.colorMedium())
		bulletPoor = Format.iconBullet(color = Format.colorPoor())
		bulletBad = Format.iconBullet(color = Format.colorBad())

		def _settingsProviders(type = None, mode = None, access = None, addon = None, module = False, reload = False):
			self.globalProviders = self.providers(type = type, mode = mode, access = access, addon = addon, module = module, reload = reload)
			return self.globalProviders

		def _settingsMenu(menu, provider = None, index = None):
			self.globalMenu = menu
			if not provider is None:
				if Tools.isString(provider): self.globalProvider = self.provider(id = provider)
				else: self.globalProvider = provider
			if not index is None:
				self.globalIndex = index

		def _settingsMenuId():
			return self.globalMenuId

		def _settingsMenuOffset():
			value = self.globalMenuOffset
			self.globalMenuOffset = 0 # Reset on menu refresh.
			return value

		def _settingsBack(type = None, mode = None, access = None, addon = None, provider = False, force = False):
			if (type and self.globalBackType) or (mode and self.globalBackMode) or (access and self.globalBackAccess) or (addon and self.globalBackAddon) or (provider and self.globalBackProvider) or force:
				if type: parameters = {'type' : True}
				elif mode: parameters = {'mode' : True}
				elif access: parameters = {'access' : True}
				elif addon: parameters = {'addon' : True}
				elif provider or force: parameters = {}
				return {'title' : Dialog.prefixBack(35374), 'remember' : False, 'action' : _settingsNavigateBack, 'parameters' : parameters}
			else:
				return {'title' : Dialog.prefixBack(33486), 'close' : True}

		def _settingsNavigate(type = None, mode = None, access = None, addon = None):
			if not type is None: self.globalType = type
			if not mode is None: self.globalMode = mode
			if not access is None: self.globalAccess = access
			if not addon is None: self.globalAddon = addon

		def _settingsNavigateBack(provider = None, type = None, mode = None, access = None, addon = None):
			if provider:
				if Tools.isArray(provider): provider = provider[0]
				type = provider.type()
				mode = provider.mode()
				access = provider.access()
				addon = provider.addonId()

			if addon and self.globalBackAddon: _settingsNavigate(addon = False)
			elif access and self.globalBackAccess: _settingsNavigate(access = False)
			elif mode and self.globalBackMode: _settingsNavigate(mode = False)
			elif type and self.globalBackType: _settingsNavigate(type = False)

			if self.globalMenu == 'domain': self.globalMenu = 'settings'
			else: self.globalMenu = None

		def _settingsHelp(provider = None):
			description = Translation.string(34347) % (ProviderBase.rankIcon(), bulletBad.strip(), bulletMedium.strip(), bulletGood.strip())
			mirrors = None

			settingsGeneral = [{'label' : 33564, 'description' : 34340}, {'label' : 33183, 'description' : 34341}, {'label' : 33219, 'description' : 34346}, {'label' : 35269, 'description' : 34469}]
			settingsScrape = []
			settingsCustom = []
			settingsProvider = []

			if provider:
				description = provider.description()
				mirrors = provider.mirrors()
				settingsScrape = provider.scrapeAttributes()
				settingsCustom = provider.customAttributes()
				if provider.accountHas(): settingsProvider.append({'label' : 33339, 'description' : 34342})
				if provider.linkHas(): settingsProvider.append({'label' : 33159, 'description' : 34343})
			else:
				settingsScrape = ProviderBase.scrapeAttributesAll()

			message = self.help(description = description, mirrors = mirrors, settingsGeneral = settingsGeneral, settingsScrape = settingsScrape, settingsProvider = settingsProvider, settingsCustom = settingsCustom)
			Dialog.text(title = 33681, message = message)

		def _settingsDefault(providers = None, attributes = None, type = None, mode = None, access = None, addon = None, navigate = False):
			message = 33222
			if providers:
				if attributes: message = 33220
				else: message = 33221
			if Dialog.option(title = 32345, message = message):
				self.settingsDefault(providers = providers, attributes = attributes, type = type, mode = mode, access = access, addon = addon)
			if navigate: _settingsNavigateBack(provider = providers, type = type, mode = mode, access = access, addon = addon)

		def _settingsToggle(providers = None, language = None, native = None, type = None, mode = None, access = None, addon = None, navigate = True):
			if providers: self.settingsToggle(providers = providers, language = language, native = native)
			else: self.settingsToggle(type = type, mode = mode, access = access, addon = addon)
			_settingsToggleBack(providers = providers, type = type, mode = mode, access = access, addon = addon, navigate = navigate)

		def _settingsToggleBack(providers = None, type = None, mode = None, access = None, addon = None, navigate = True):
			if navigate and not self.globalId:
				if providers: _settingsNavigateBack()
				else: _settingsNavigateBack(provider = providers, type = type, mode = mode, access = access, addon = addon)

		def _settingsToggleStatus(providers = None, navigate = True):
			choice = Dialog.options(title = 33196, message = 33377, labelConfirm = 33430, labelDeny = 33456, labelCustom = 33431)
			if choice == Dialog.ChoiceYes: choice = [ProviderBase.StatusOperational]
			elif choice == Dialog.ChoiceNo: choice = [ProviderBase.StatusOperational, ProviderBase.StatusImpaired]
			elif choice == Dialog.ChoiceCustom: choice = [ProviderBase.StatusImpaired]
			else: choice = None
			if choice:
				enabled = []
				disabled = []
				for i in providers:
					if i.status() in choice: enabled.append(i)
					else: disabled.append(i)
				self.settingsToggle(providers = enabled, enable = True)
				self.settingsToggle(providers = disabled, enable = False)
			_settingsToggleBack(providers = providers, navigate = navigate)

		def _settingsToggleBest(providers = None, navigate = True):
			Dialog.confirm(title = 33193, message = 33420)
			count = Dialog.input(title = 33193, type = Dialog.InputNumeric, default = min(10, len(providers)))
			if count:
				count = int(count)
				providers = sorted(providers, key = lambda i : i.order(), reverse = True)
				self.settingsToggle(providers = providers[:count], enable = True)
				self.settingsToggle(providers = providers[count:], enable = False)
			_settingsToggleBack(providers = providers, navigate = navigate)

		def _settingsVerify(providers = None, type = None, mode = None, access = None, addon = None):
			verify = self.verify(providers = providers, type = type, mode = mode, access = access, addon = addon, internal = True)
			if not verify: self.globaClose = True

		def _settingsOptimize():
			self.optimizeProvider(wait = True)
			_settingsProviders(reload = True)

		def _settingsExternal(module):
			Extension.settings(id = module, wait = True)

		def _settingsInstall(scraper = None, parent = None, name = None):
			if scraper: Extension.enable(id = scraper, name = name, confirm = True, notification = True, wait = True)

			# For now, do not install the parent addon.
			# Some providers might fail if the parent addon is not installed/enabled (since they might need settings from the parent).
			#if parent: Extension.enable(id = parent, name = name, confirm = True)

			# Make sure the code is copied over, prepared, etc, and everything from the database reloaded.
			if scraper and Extension.installed(scraper):
				Loader.show()
				self.databaseClear(providers = True, links = False, streams = False, failures = False)
				_settingsProviders(module = True)
				Loader.hide()

		def _settingsScrapeAction(provider, id):
			Loader.show()
			provider.scrapeDialog(id = id)
			self.settingsUpdate(provider)

		def _settingsCustomAction(provider, id):
			Loader.show()
			provider.customDialog(id = id)
			self.settingsUpdate(provider)

		def _settingsAccountAction(provider, type):
			Loader.show()
			provider.accountDialog(type = type)
			self.settingsUpdate(provider)

		def _settingsDomainAction(provider, index, action):
			links = provider.links(settings = True, deleted = True, flat = False)

			change = False
			if action == 'up' and index > 0:
				change = True
				links.insert(index - 1, links.pop(index))
				self.globalMenuOffset = -1
			elif action == 'down' and index < len(links):
				change = True
				links.insert(index + 1, links.pop(index))
				self.globalMenuOffset = 1
			elif action == 'remove':
				change = True
				if links[index]['custom']: links.pop(index)
				else: links[index]['deleted'] = True
				self.globalMenuOffset = -1

			if change:
				provider.linkSet(links, settings = True)
				self.settingsUpdate(provider)
			_settingsNavigateBack()

		def _settingsDomainAdd(provider):
			Loader.show()
			links = provider.links(settings = True, deleted = True, flat = False)
			link = Dialog.input(title = 33160, type = Dialog.InputAlphabetic)
			if link:
				Loader.show()
				from lib.modules.network import Networker
				if not Networker.linkScheme(link): link = 'https://' + link
				links.append({'link' : link, 'custom' : True})
				provider.linkSet(links, settings = True)
				self.settingsUpdate(provider)

		def _settingsDomainUnblock(provider):
			links = provider.links(settings = True, deleted = True, flat = False)
			if not provider.linksUnblock(links): Dialog.notification(title = 35286, message = 35287, icon = Dialog.IconInformation)
			provider.linkSet(links, settings = True)
			self.settingsUpdate(provider)

		def _settingsItems():
			if self.globaClose: return None

			# Direct settings dialog for a specific provider ID.
			if self.globalId and not self.globalMenu: _settingsMenu(menu = 'settings', provider = self.globalId)

			# On back action.
			back = self.globalType is False or self.globalMode is False or self.globalAccess is False or self.globalAddon is False
			backType = self.globalType is False
			backMode = self.globalMode is False
			backAccess = self.globalAccess is False
			backAddon = self.globalAddon is False

			type, mode, access = self.settingsFlatten(type = self.globalType, mode = self.globalMode, access = self.globalAccess)
			backHop = 0
			if type and not self.globalType == type: backHop += 1
			if mode and not self.globalMode == mode: backHop += 1
			if access and not self.globalAccess == access: backHop += 1

			if self.globalType is False:
				self.globalType = None
			elif self.globalMode is False:
				self.globalMode = None
				if backHop >= 1: self.globalType = None
			elif self.globalAccess is False:
				self.globalAccess = None
				if backHop >= 1:
					self.globalMode = None
					if backHop >= 2: self.globalType = None
			elif self.globalAddon is False:
				self.globalAddon = None
				if backHop >= 1:
					self.globalAccess = None
					if backHop >= 2:
						self.globalMode = None
						if backHop >= 3: self.globalType = None

			type = self.globalType
			mode = self.globalMode
			access = self.globalAccess
			addon = self.globalAddon
			type, mode, access = self.settingsFlatten(type = type, mode = mode, access = access) # Skip subcategories if there is only one.
			menu = self.globalMenu
			if not menu == 'settings' and not menu == 'domain': self.globalProvider = None

			# Generate menu ID for automatic reselection on navigation.
			id = []
			if self.globalProvider: id.append(self.globalProvider.id())
			else: id.extend(['menu', type, mode, access, addon]) # Add menu to always have a string (main menu).
			if menu: id.append(menu)
			if id: self.globalMenuId = '_'.join([i for i in id if i])
			else: self.globalMenuId = None

			if menu == 'toggle': items = _settingsItemsToggle(type = type, mode = mode, access = access, addon = addon)
			elif menu == 'settings': items = _settingsItemsSettings(provider = self.globalProvider)
			elif menu == 'domain': items = _settingsItemsDomain(provider = self.globalProvider, index = self.globalIndex)
			elif not type: items = _settingsItemsType(type = type)
			elif not type == ProviderBase.TypeExternal and not mode: items = _settingsItemsMode(type = type, mode = mode)
			elif not type == ProviderBase.TypeExternal and not access: items = _settingsItemsAccess(type = type, mode = mode, access = access)
			elif type == ProviderBase.TypeExternal and not addon: items = _settingsItemsAddon(type = type, mode = mode, access = access)
			else: items = _settingsItemsProviders(type = type, mode = mode, access = access, addon = addon)

			return items

		# Items for the main type menu.
		def _settingsItemsType(type):
			items = [
				_settingsBack(),
				{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp},
				{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault},
				{'title' : Dialog.prefixNext(33219), 'action' : _settingsVerify},
				{'title' : Dialog.prefixNext(35269), 'action' : _settingsOptimize},
				Dialog.EmptyLine,
			]
			for type in ProviderBase.Types:
				count = self.settingsCount(label = True, type = type)
				if not count and type == ProviderBase.TypeExternal: count = Format.fontColor(35859, Format.colorPoor())
				if not count is None: items.append({'title' : ProviderBase.TypesData[type]['label'], 'prefix' : bullet, 'color' : False, 'value' : count, 'action' : _settingsNavigate, 'parameters' : {'type' : type}})
			return items

		# Items for the main mode menu.
		def _settingsItemsMode(type, mode):
			items = [
				_settingsBack(type = True),
				{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp},
				{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'type' : type}},
				{'title' : Dialog.prefixNext(33183), 'action' : _settingsToggle, 'parameters' : {'type' : type}},
				{'title' : Dialog.prefixNext(33219), 'action' : _settingsVerify, 'parameters' : {'type' : type}},
				Dialog.EmptyLine,
			]
			for mode in ProviderBase.Modes:
				count = self.settingsCount(label = True, type = type, mode = mode)
				if not count is None: items.append({'title' : ProviderBase.ModesData[mode]['label'], 'prefix' : bullet, 'color' : False, 'value' : count, 'action' : _settingsNavigate, 'parameters' : {'mode' : mode}})
			return items

		# Items for the main access menu.
		def _settingsItemsAccess(type, mode, access):
			items = [
				_settingsBack(mode = True),
				{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp},
				{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'type' : type, 'mode' : mode}},
				{'title' : Dialog.prefixNext(33183), 'action' : _settingsToggle, 'parameters' : {'type' : type, 'mode' : mode}},
				{'title' : Dialog.prefixNext(33219), 'action' : _settingsVerify, 'parameters' : {'type' : type, 'mode' : mode}},
				Dialog.EmptyLine,
			]
			for access in ProviderBase.Accesses:
				count = self.settingsCount(label = True, type = type, mode = mode, access = access)
				if not count is None: items.append({'title' : ProviderBase.AccessesData[access]['label'], 'prefix' : bullet, 'color' : False, 'value' : count, 'action' : _settingsNavigate, 'parameters' : {'access' : access}})
			return items

		# Items for the main addon menu.
		def _settingsItemsAddon(type, mode, access):
			installedless = Format.fontColor(35859, Format.colorPoor())
			enabledless = Format.fontColor(33746, Format.colorMedium())
			codeless = Format.fontColor(33850, Format.colorBad())
			providers = _settingsProviders(type = type, module = True)
			addons = [{'id' : i.addonId(), 'object' : i} for i in providers]
			addons = Tools.listUnique(data = addons, attribute = 'id')

			items = [
				_settingsBack(access = True),
				{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp},
				{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'type' : type, 'mode' : mode, 'access' : access}},
				{'title' : Dialog.prefixNext(33183), 'action' : _settingsToggle, 'parameters' : {'type' : type, 'mode' : mode, 'access' : access}},
				{'title' : Dialog.prefixNext(33219), 'action' : _settingsVerify, 'parameters' : {'type' : type, 'mode' : mode, 'access' : access}},
				Dialog.EmptyLine,
			]
			for addon in addons:
				enabled = addon['object'].addonEnabled(scraper = True, parent = False)
				installed = addon['object'].addonInstalled(scraper = True, parent = False)
				prefix = bulletGood if enabled else bulletMedium if installed else bulletPoor
				count = self.settingsCount(label = True, type = type, mode = mode, access = access, addon = addon['id'])
				if not installed: value = installedless
				elif not enabled: value = enabledless
				elif not count: # Some errors in executing the external addon code (eg: import errors).
					instances = addon['object'].instances(full = True)
					if all([not i['valid'] for i in instances]): value = codeless # All providers failed, assuming there is some major problem in the external addon code (eg: unresolved import).
					else: value = count
				else: value = count
				items.append({'title' : '%s (%s)' % (addon['object'].addonName(), addon['object'].addonRank(label = True)), 'prefix' : prefix, 'color' : False, 'value' : value, 'action' : _settingsNavigate, 'parameters' : {'addon' : addon['id']}})
			return items

		# Items for the provider list menu.
		def _settingsItemsProviders(type, mode, access, addon):
			providers = _settingsProviders(type = type, mode = mode, access = access, addon = addon, reload = True, module = True)

			external = type == ProviderBase.TypeExternal
			enabled = Format.fontColor(32301, Format.colorExcellent())
			enabledParent = Format.fontColor(32301, Format.colorBad())
			accountless = Format.fontColor(33215, Format.colorPoor())
			accountlessParent = Format.fontColor(33215, Format.colorBad())
			internal = Format.fontColor(35411, Format.colorPoor())
			internalParent = Format.fontColor(35411, Format.colorBad())
			disabled = Format.fontColor(32302, Format.colorBad())
			uninstalled = Format.fontColor(35859, Format.colorPoor())

			addonExternal = False
			addonProvider = None
			addonInstalled = None
			addonEnabled = None
			addonName = None
			addonModuleScraper = None
			addonModuleParent = None
			addonModuleSettings = None
			addonSettings = None
			try:
				if providers[0].typeExternal():
					addonExternal = True
					addonProvider = providers[0]
					addonInstalled = providers[0].addonInstalled(scraper = True, parent = False, settings = False)
					addonEnabled = providers[0].addonEnabled(scraper = True, parent = False, settings = False)
					addonName = providers[0].addonName()
					addonModuleScraper = providers[0].addonModuleScraper()
					addonModuleParent = providers[0].addonModuleParent()
					addonModuleSettings = providers[0].addonModuleSettings()
					addonSettings = addonModuleSettings and providers[0].addonSettings() and providers[0].addonEnabled(scraper = False, parent = False, settings = True)
			except: pass
			menu = not addonExternal or (addonInstalled and addonEnabled)

			actions = [
				_settingsBack(addon = True) if external else _settingsBack(access = True),
				{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp, 'parameters' : {'provider' : addonProvider}},
				{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'type' : type, 'mode' : mode, 'access' : access, 'addon' : addon}} if menu else None,
				{'title' : Dialog.prefixNext(33183), 'action' : _settingsMenu, 'parameters' : {'menu' : 'toggle'}} if menu else None,
				{'title' : Dialog.prefixNext(33219), 'action' : _settingsVerify, 'parameters' : {'type' : type, 'mode' : mode, 'access' : access, 'addon' : addon}} if menu else None,
				{'title' : Dialog.prefixNext(33736), 'action' : _settingsInstall, 'parameters' :{'scraper' : addonModuleScraper, 'parent' : addonModuleParent, 'name' : addonName}} if addonExternal and (not addonInstalled or not addonEnabled) else None,
				{'title' : Dialog.prefixNext(33011), 'action' : _settingsExternal, 'parameters' :{'module' : addonModuleSettings}} if addonSettings else None,
				Dialog.EmptyLine,
			]

			sub = []
			if not addonInstalled is False and not addonEnabled is False: # Can be None.
				for provider in providers:
					# If there are import errors in the external addon code (eg: some module imports that fail), the provider name is not detectable.
					# In that case, do not show the provider.
					# The root "External" menu will show "Code Errors".
					if not provider.name(): continue

					if provider.enabledSettingsProvider():
						if provider.typeSpecial() and provider.addonModuleScraper() and (not provider.addonInstalled(scraper = True, parent = False, settings = False) or not provider.addonEnabled(scraper = True, parent = False, settings = False)): settings = uninstalled
						elif not provider.enabledInternal(): settings = internal if provider.enabledSettings() else internalParent
						elif provider.enabledAccount(): settings = enabled if provider.enabledSettings() else enabledParent
						else: settings = accountless if provider.enabledSettings() else accountlessParent
					else: settings = disabled

					sort = ''
					label = '%s (%s)' % (provider.name(), provider.rank(label = True))
					if provider.typeExternal():
						label = '[%s] %s' % (Format.fontUppercase(provider.languageSecondary()), label)
						sort += provider.languageSecondary() + ' '

					sort += provider.name()
					sort = sort.lower()
					if provider.typeSpecial() and 'orion' in sort: sort = '' # Always place Orion first.

					providerBullet = bulletGood
					if provider.statusImpaired(): providerBullet = bulletMedium
					elif provider.statusDead(): providerBullet = bulletBad
					elif provider.typeExternal(): providerBullet = bulletGood if provider.addonEnabled(scraper = True, parent = False) else bulletBad

					sub.append({'title' : label, 'prefix' : providerBullet, 'sort' : sort, 'color' : False, 'value' : settings, 'action' : _settingsMenu, 'parameters' : {'menu' : 'settings', 'provider' : provider}})
				sub = Tools.listSort(sub, key = lambda i : i['sort'])

			return actions + sub

		# Items for the main and provider toggle menu.
		def _settingsItemsToggle(type, mode, access, addon):
			providers = _settingsProviders(type = type, mode = mode, access = access, addon = addon)

			items = [
				_settingsBack(provider = True),
				{'title' : Dialog.prefixNext(35790), 'action' : _settingsToggle, 'parameters' : {'type' : type, 'mode' : mode, 'access' : access, 'addon' : addon}},
				{'title' : Dialog.prefixNext(33184), 'action' : _settingsToggle, 'parameters' : {'providers' : providers}},
			]
			if len(providers) > 1:
				items.append({'title' : Dialog.prefixNext(33193), 'action' : _settingsToggleBest, 'parameters' : {'providers' : providers}})
				items.append({'title' : Dialog.prefixNext(33196), 'action' : _settingsToggleStatus, 'parameters' : {'providers' : providers}})

			if providers and providers[0].typeExternal(): items.append({'title' : Dialog.prefixNext(35767), 'action' : _settingsToggle, 'parameters' : {'native' : True, 'providers' : providers}})
			codes = [provider.language() for provider in providers]
			codes = list(set(codes))
			if len(codes) > 1:
				codes = sorted(codes)
				toggle = Translation.string(33183) + ' '
				items.extend([{'title' : Dialog.prefixNext(toggle + Language.name(language)), 'action' : _settingsToggle, 'parameters' : {'language' : language, 'providers' : providers}} for language in codes])
			return items

		# Items for the provider settings menu.
		def _settingsItemsSettings(provider):
			try:
				addonModuleSettings = provider.addonModuleSettings()
				addonModuleScraper = provider.addonModuleScraper()
				addonEnabled = provider.addonEnabled(scraper = True)
				addonSettings = addonModuleSettings and provider.addonSettings() and provider.addonEnabled(scraper = False, parent = False, settings = True)
			except:
				addonModuleSettings = None
				addonModuleScraper = None
				addonInstalled = None
				addonSettings = None

			items = [
				_settingsBack(provider = True),
				{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp, 'parameters' : {'provider' : provider}},
				{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'providers' : provider}},
				{'title' : Dialog.prefixNext(33183), 'action' : _settingsToggle, 'parameters' : {'providers' : provider}},
				{'title' : Dialog.prefixNext(33219), 'action' : _settingsVerify, 'parameters' : {'providers' : provider}},
				{'title' : Dialog.prefixNext(33736), 'action' : _settingsInstall, 'parameters' : {'scraper' : addonModuleScraper}} if not addonEnabled else None,
				{'title' : Dialog.prefixNext(33011), 'action' : _settingsExternal, 'parameters' :{'module' : addonModuleSettings}} if addonSettings else None,
			]

			# Scrape
			attributes = provider.scrapeAttributes()
			if attributes:
				category = [{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'providers' : provider, 'attributes' : ['scrape']}}]
				if attributes:
					for attribute in attributes:
						category.append({'title' : attribute['label'], 'value' : attribute['format'], 'action' :  _settingsScrapeAction, 'parameters' : {'provider' : provider, 'id' : attribute['id']}})
				items.append({'title' : 35514, 'items' : category})

			# Custom
			attributes = provider.customAttributes()
			if attributes:
				category = [{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'providers' : provider, 'attributes' : ['custom']}}]
				if attributes:
					for attribute in attributes:
						category.append({'title' : attribute['label'], 'value' : attribute['format'], 'action' :  _settingsCustomAction, 'parameters' : {'provider' : provider, 'id' : attribute['id']}})
				items.append({'title' : 33681, 'items' : category})

			# Account
			if provider.accountHas():
				category = [{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'providers' : provider, 'attributes' : 'account'}}]
				attributes = provider.accountAttributes()
				for attribute in attributes:
					category.append({'title' : attribute['label'], 'value' : attribute['format'], 'action' : _settingsAccountAction, 'parameters' : {'provider' : provider, 'type' : attribute['type']}})
				items.append({'title' : 33339, 'items' : category})

			# Domains
			links = provider.links(settings = True, deleted = True, flat = False)
			if links and not [link for link in links if not 'deleted' in link or not link['deleted']]: # In case the user deleted all the domains, restore the default ones.
				links = provider.copy(default = True).links(settings = True, deleted = True, flat = False)
				if links and len(links) > 0:
					provider.linkSet(links, settings = True)
					self.settingsUpdate(provider)
			if links:
				category = [
					{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'providers' : provider, 'attributes' : 'link'}},
					{'title' : Dialog.prefixNext(35069), 'action' : _settingsDomainAdd, 'parameters' : {'provider' : provider}},
				]
				if provider.unblockHas() and provider.unblockEnabled():
					category.append({'title' : Dialog.prefixNext(35286), 'action' : _settingsDomainUnblock, 'parameters' : {'provider' : provider}})

				number = 0
				for i in range(len(links)):
					if not 'deleted' in links[i] or not links[i]['deleted']:
						number += 1
						title = '%d. %s' % (number, Translation.string(35233 if links[i]['custom'] else 35286 if ('unblock' in links[i] and links[i]['unblock']) else 35022))
						category.append({'title' : title, 'value' : links[i]['link'], 'action' : _settingsMenu, 'parameters' : {'menu' : 'domain', 'provider' : provider, 'index' : i}})
				items.append({'title' : 33159, 'items' : category})

			return items

		# Items for the provider domain settings menu.
		def _settingsItemsDomain(provider, index):
			return [
				_settingsBack(force = True),
				{'title' : Dialog.prefixNext(35403), 'action' : _settingsDomainAction, 'parameters' : {'provider' : provider, 'index' : index, 'action' : 'up'}},
				{'title' : Dialog.prefixNext(35404), 'action' : _settingsDomainAction, 'parameters' : {'provider' : provider, 'index' : index, 'action' : 'down'}},
				{'title' : Dialog.prefixNext(35406), 'action' : _settingsDomainAction, 'parameters' : {'provider' : provider, 'index' : index, 'action' : 'remove'}},
			]

		def _settingsDialog(type = None):
			Dialog.information(title = 32345, items = _settingsItems(), refresh = _settingsItems, reselect = Dialog.ReselectMenu, offset = _settingsMenuOffset, id = _settingsMenuId)

		# Execute

		self.globaClose = False
		self.globalMenu = None
		self.globalMenuId = None
		self.globalMenuOffset = 0
		self.globalIndex = None
		self.globalProviders = None
		self.globalProvider = None
		self.globalModule = False
		self.globalType = type
		self.globalMode = mode
		self.globalAccess = access
		self.globalAddon = addon
		self.globalId = id

		self.globalBackType = True
		self.globalBackMode = True
		self.globalBackAccess = True
		self.globalBackAddon = True
		self.globalBackProvider = True

		type, mode, access = self.settingsFlatten(type = type, mode = mode, access = access)
		if type or mode or access or addon or id:
			self.globalBackType = False
			if mode or access or addon or id:
				self.globalBackMode = False
				if access or addon or id:
					self.globalBackAccess = False
					if addon or id:
						self.globalBackAddon = False
						if id:
							self.globalBackProvider = False

		_settingsDialog()

		Loader.show()
		# Wait for label to update before launching the setttings. Otherwise the old label probably still shows.
		# Always wait, since the Kodi GUI becomes unresponsive if threads are still running.
		self.settingsLabel(wait = True)
		Loader.hide()
		if settings: Settings.launchData(Manager.SettingsConfigurationData)

	##############################################################################
	# PRESETS
	##############################################################################

	@classmethod
	def presets(self, settings = False):
		from lib.modules.interface import Format, Dialog, Loader, Translation
		Loader.show()

		presets = Settings.getDataList(Manager.SettingsPresetsData)
		self.globalClose = False
		self.globalEdit = False

		help = self.help(description = 34048, settings = [
			{'label' : 35069, 'description' : 34049},
			{'label' : 33686, 'description' : 34050},
			{'label' : 33685, 'description' : 34051},
			{'label' : 33171, 'description' : 34052},
			{'label' : 35406, 'description' : 34053},
		])

		def _presetsHelp():
			Dialog.text(title = 33682, message = help)

		def _presetsEdit(index):
			items = [
				{'title' : Dialog.prefixBack(35374), 'close' : True, 'return' : True},
				{'title' : Dialog.prefixNext(33239), 'close' : True, 'return' : True, 'action' : _presetsHelp},
				{'title' : Dialog.prefixNext(33686), 'close' : True, 'return' : True, 'action' : _presetsSave, 'parameters' : {'index' : index}},
				{'title' : Dialog.prefixNext(33685), 'close' : True, 'return' : True, 'action' : _presetsLoad, 'parameters' : {'index' : index}},
				{'title' : Dialog.prefixNext(33171), 'close' : True, 'return' : True, 'action' : _presetsRename, 'parameters' : {'index' : index}},
				{'title' : Dialog.prefixNext(35406), 'close' : True, 'return' : True, 'action' : _presetsRemove, 'parameters' : {'index' : index}},
			]

			choice = Dialog.information(title = 33682, items = items)
			if not choice: self.globalClose = True

		def _presetsCount(count):
			return '%d %s' % (count, Translation.string(33710 if count == 1 else 32345))

		def _presetsName(default = None):
			if default is None: default = '%s %d' % (Translation.string(33683), len(presets) + 1)
			return Dialog.input(title = 33687, type = Dialog.InputAlphabetic, default = default)

		def _presetsId():
			id = None
			while True:
				id = Hash.random()
				found = False
				for preset in presets:
					if preset['id'] == id:
						found = True
						break
				if not found: break
			return id

		def _presetsCreate(id = None, name = None, data = None, count = None):
			Loader.show()
			if id is None: id = _presetsId()
			if name is None: name = _presetsName()
			if data is None: data = self.presetsData()
			if count is None: count = _presetsCount(self.settingsCount())
			preset = {
				'id' : id,
				'name' : name,
				'count' : count,
				'data' : data,
			}
			Loader.hide()
			return preset

		def _presetsAdd():
			presets.append(_presetsCreate())
			_presetsUpdate()

		def _presetsRemove(index):
			del presets[index]
			_presetsUpdate(notification = False)

		def _presetsRename(index):
			name = _presetsName(presets[index]['name'])
			presets[index] = _presetsCreate(name = name, id = presets[index]['id'], data = presets[index]['data'], count = presets[index]['count'])
			_presetsUpdate()

		def _presetsSave(index):
			presets[index] = _presetsCreate(id = presets[index]['id'], name = presets[index]['name'])
			_presetsUpdate()

		def _presetsLoad(index):
			if Dialog.option(title = 33682, message = 33684):
				Loader.show()
				self.settingsSave(data = presets[index]['data'], count = True, wait = True)
				Loader.hide()
				Dialog.notification(title = 33682, message = 33689, icon = Dialog.IconSuccess)
				self.globalClose = True

		def _presetsUpdate(notification = True):
			self.globalEdit = True
			Settings.setData(Manager.SettingsPresetsData, presets, background = True)
			if notification: Dialog.notification(title = 33682, message = 33688, icon = Dialog.IconSuccess)

		def _presetsItems():
			if self.globalClose: return None
			bullet = Format.iconBullet(color = Format.colorSecondary())

			actions = [
				{'title' : Dialog.prefixBack(33486), 'close' : True},
				{'title' : Dialog.prefixNext(33239), 'action' : _presetsHelp},
				{'title' : Dialog.prefixNext(35069), 'action' : _presetsAdd},
				Dialog.EmptyLine,
			]
			sub = [{'title' : bullet + presets[i]['name'], 'value' : presets[i]['count'], 'color' : False, 'action' : _presetsEdit, 'parameters' : {'index' : i}} for i in range(len(presets))]

			return actions + sub

		Dialog.information(title = 33682, items = _presetsItems(), refresh = _presetsItems, reselect = True)

		if self.globalEdit:
			Loader.show()
			self.presetsLabel(presets)
			Settings.wait() # Wait until labels were update before launching the settings dialog again.
			Loader.hide()

		if settings: Settings.launchData(Manager.SettingsPresetsData)

	@classmethod
	def presetsLabel(self, presets = None):
		from lib.modules.interface import Translation

		if not presets: presets = Settings.getDataList(Manager.SettingsPresetsData)
		count = len(presets)

		label = '%d %s' % (count, Translation.string(33683 if count == 1 else 33682))
		Settings.setLabel(Manager.SettingsPresetsData, label, background = True)

	@classmethod
	def presetsData(self):
		# Currently we only take the "enabled" values from the settings, excluding accounts, domains, custom settings, etc.
		# Otherwise if the user currently has set an account set for a provider and then uses a preset, the preset data (with no/different account) will be used instead of the one in the settings at the moment.
		# If in the future we want to also save all the other settings to the preset, we should add an option to the preset dialog's Add/Save options to aask the user to only save "enabled" or "all settings".
		return self.settingsLoad(basic = True)

	@classmethod
	def presetsEnabled(self):
		return Settings.getBoolean(Manager.SettingsPresetsEnabled)

	@classmethod
	def presetsRetrieve(self, preset, data = False):
		if Tools.isString(preset):
			presets = Settings.getDataList(Manager.SettingsPresetsData)
			for item in presets:
				if item['id'] == preset: return item['data'] if data else item
			for item in presets:
				if item['name'] == preset: return item['data'] if data else item
		elif Tools.isDictionary(preset):
			return preset['data'] if preset else item
		return None

	@classmethod
	def presetsSelection(self, id = True):
		from lib.modules.interface import Dialog, Format
		items = Settings.getDataList(Manager.SettingsPresetsData)
		if items:
			choice = Dialog.select(title = 33682, items = ['%s: %s' % (Format.fontBold(item['name']), item['count']) for item in items])
			if choice >= 0:
				result = items[choice]
				if id: result = result['id']
				return result
		else:
			Dialog.notification(title = 35058, message = 35059, icon = interface.Dialog.IconError)
		return None

	##############################################################################
	# FAILURE
	##############################################################################

	@classmethod
	def _failureInitialize(self):
		return self._databaseInitialize(providers = False, links = False, streams = False, failures = True)

	@classmethod
	def failureClear(self):
		self.databaseClear(providers = False, links = False, streams = False, failures = True)

	@classmethod
	def failureEnabled(self):
		return Settings.getBoolean('provider.failure.detection')

	@classmethod
	def failureLimit(self):
		return Settings.getInteger('provider.failure.detection.limit')

	@classmethod
	def failureTime(self):
		return Settings.getCustom('provider.failure.detection.time')

	@classmethod
	def failureTimeLabel(self):
		return Settings.customLabel(id = 'provider.failure.detection.time', value = self.failureTime())

	@classmethod
	def failureList(self):
		result = []
		if self.failureEnabled():
			thresholdLimit = self.failureLimit()
			thresholdTime = self.failureTime()
			if thresholdTime > 0: thresholdTime = Time.timestamp() - thresholdTime

			data = self._failureInitialize()
			result = data._selectValues('SELECT id FROM %s WHERE NOT (count < %d OR time < %d);' % (Manager.DatabaseFailures, thresholdLimit, thresholdTime))
		return result

	@classmethod
	def failureUpdate(self, finished, unfinished):
		if self.failureEnabled():
			from lib.modules import orionoid

			data = self._failureInitialize()
			current = data._selectValues('SELECT id FROM %s;' % Manager.DatabaseFailures)
			timestamp = Time.timestamp()

			for id in finished:
				if not orionoid.Orionoid.Scraper in id:
					if id in current: data._update('UPDATE %s SET count = 0, time = %d WHERE id = "%s";' % (Manager.DatabaseFailures, timestamp, id), commit = False)
					else: data._insert('INSERT INTO %s (id, count, time) VALUES ("%s", 0, %d);' % (Manager.DatabaseFailures, id, timestamp), commit = False)

			for id in unfinished:
				if not orionoid.Orionoid.Scraper in id:
					if id in current: data._update('UPDATE %s SET count = count + 1, time = %d WHERE id = "%s";' % (Manager.DatabaseFailures, timestamp, id), commit = False)
					else: data._insert('INSERT INTO %s (id, count, time) VALUES ("%s", 1, %d);' % (Manager.DatabaseFailures, id, timestamp), commit = False)

			data._commit()

	##############################################################################
	# OPTIMIZATION
	##############################################################################

	@classmethod
	def _optimizeDevice(self, processor = True, memory = True, storage = True, connection = True, iterations = 3, progress = [], analyze = True):
		progress.append((0, 35007))

		from lib.modules.tools import Hardware

		data = None
		performance = Hardware.PerformanceMedium
		default = base = 0.5
		label = 33387

		if analyze:
			try:
				processorTotal = False
				processorSingle = False
				connectionSpeed = False
				connectionLatency = False
				storageRead = False
				storageWrite = False

				try:
					processorTotal = Manager.OptimizeDevice['processor']['total']
					processorSingle = Manager.OptimizeDevice['processor']['single']
					memory = Manager.OptimizeDevice['memory']
					storageRead = Manager.OptimizeDevice['storage']['read']
					storageWrite = Manager.OptimizeDevice['storage']['write']
				except:
					def callback(category):
						if category == Hardware.CategoryProcessor: progress.append((5, 36047))
						elif category == Hardware.CategoryMemory: progress.append((10, 36048))
						elif category == Hardware.CategoryStorage: progress.append((20, 36139))
						elif category == Hardware.CategoryConnection: progress.append((50, 35008))

					data = Hardware.performance(processor = processor, memory = memory, storage = storage, connection = connection, callback = callback)

					if processor:
						processorTotal = data['processor']['value']['total']
						processorSingle = data['processor']['value']['single']
					if memory:
						memory = data['memory']['value']
					if storage:
						storageRead = data['storage']['value']['read']
						storageWrite = data['storage']['value']['write']
					if connection:
						connectionSpeed = data['connection']['value']['speed']
						connectionLatency = data['connection']['value']['latency']

				#gaiaremove
				data0 = Tools.copy(data)

				data = Hardware.performance(processorTotal = processorTotal, processorSingle = processorSingle, memory = memory, storageRead = storageRead, storageWrite = storageWrite, connectionSpeed = connectionSpeed, connectionLatency = connectionLatency)
				performance = data['performance']
				base = data['rating']

				#gaiaremove
				try:
					if not data['processor']['label']['rating'] or data['processor']['label']['rating'] == '0%':
						Logger.log('Hardware Data 0: ' + str(processor) + ' * ' + str(processorTotal) + ' * ' + str(processorSingle))
						Logger.log('Hardware Data 1: ' + Converter.jsonTo(data0))
						Logger.log('Hardware Data 2: ' + Converter.jsonTo(data))
						Logger.log('Hardware Data 3: ' + Converter.jsonTo(Hardware.data()))

						from lib.modules.tools import Platform
						p1 = Platform.data(refresh = True)
						p2 = Hardware.data(full = True, refresh = True)
						Logger.log('Hardware Data 4: ' + Converter.jsonTo(p1))
						Logger.log('Hardware Data 5: ' + Converter.jsonTo(p2))
				except: Logger.error()

				label = [[36049, data['label']['description']]]
				if processor: label.append([36046, data['processor']['label']['description']])
				if memory: label.append([35004, data['memory']['label']['description']])
				if storage: label.append([33350, data['storage']['label']['description']])
				if connection: label.append([33404, data['connection']['label']['description']])
			except:
				Logger.error()

		progress.append(100)
		return {'performance' : performance, 'base' : base, 'default' : default, 'label' : label, 'data' : data}

	@classmethod
	def _optimizeProvider(self, progress = [], analyze = True):
		progress.append((0, 35009))

		count = default = 20
		label = 33387

		def multiply(count):
			return max(1, count) / float(default)

		if analyze:
			try:
				from lib.modules.tools import Media
				from lib.modules.interface import Translation

				try:
					countReal = count = Manager.OptimizeProvider
				except:
					self.providers()
					countReal = len(self.providers(enabled = True))
					countMovie = len(self.providers(media = Media.TypeMovie, enabled = True, local = False))
					countShow = len(self.providers(media = Media.TypeShow, enabled = True, local = False))
					count = max(countMovie, countShow)

				if count == 0: label = 33112
				elif count <= 20: label = 35000
				elif count <= 40: label = 35001
				else: label = 35002
				label = '%s (%d %s)' % (Translation.string(label), countReal, Translation.string(32301))
			except:
				Logger.error()

		progress.append(100)
		return {'count' : count, 'multiplier' : multiply(count), 'default' : multiply(default), 'label' : [32345, label]}

	@classmethod
	def _optimizePack(self, progress = [], analyze = True):
		progress.append((0, 35275))

		count = default = 3
		label = 33387

		def multiply(count):
			return count * 0.2

		if analyze:
			try:
				from lib.modules.interface import Translation

				if ProviderBase.settingsGlobalPackEnabled():
					countMovie = int(ProviderBase.settingsGlobalPackMovie())
					countShow = int(ProviderBase.settingsGlobalPackShow()) + int(ProviderBase.settingsGlobalPackSeason())
					count = countMovie + countShow
				else:
					count = 0

				if count == 0: label = 33112
				elif count <= 1: label = 35000
				elif count <= 2: label = 35001
				else: label = 35002
				label = '%s (%d %s)' % (Translation.string(label), count, Translation.string(35274))
			except:
				Logger.error()

		progress.append(100)
		return {'count' : count, 'multiplier' : multiply(count), 'default' : multiply(default), 'label' : [33167, label]}

	@classmethod
	def _optimizeTitle(self, progress = [], analyze = True):
		progress.append((0, 35010))

		count = default = 2
		label = 33387

		def multiply(count):
			return count * 0.2

		if analyze:
			try:
				from lib.modules.tools import Language
				from lib.modules.interface import Translation, Font

				count = 1

				if ProviderBase.settingsGlobalTitleEnabled():
					if ProviderBase.settingsGlobalTitleOriginal(): count += 1
					if ProviderBase.settingsGlobalTitleNative(): count += 1
					if ProviderBase.settingsGlobalTitleLocal(): count += 1
					if ProviderBase.settingsGlobalTitleAlias(): count += 4
					if ProviderBase.settingsGlobalTitleCharacter(): count += 2

					language = ProviderBase.settingsGlobalTitleLanguage()
					if not language == Language.EnglishCode: count += 1

					if count >= 10: label = 35002
					elif count >= 5: label = 35001
					elif count >= 0: label = 35000
				else:
					label = 33564

				label = '%s (%s %d %s)' % (Translation.string(label), Font.icon(icon = Font.IconEstimator), count, Translation.string(35274))
			except:
				Logger.error()

		progress.append(100)
		return {'count' : count, 'multiplier' : multiply(count), 'default' : multiply(default), 'label' : [33881, label]}

	@classmethod
	def _optimizeKeyword(self, progress = [], analyze = True):
		progress.append((0, 35813))

		count = default = 7
		label = 33387

		def multiply(count):
			return count * 0.2

		if analyze:
			try:
				from lib.modules.interface import Translation, Font

				count = 1

				if ProviderBase.settingsGlobalKeywordEnabled():
					values = [ProviderBase.settingsGlobalKeywordEnglish(), ProviderBase.settingsGlobalKeywordNative(), ProviderBase.settingsGlobalKeywordCustom()]
					for value in values:
						if value == ProviderBase.KeywordQuick: count += 2
						elif value == ProviderBase.KeywordFull: count += 4

					if count >= 10: label = 35002
					elif count >= 5: label = 35001
					elif count >= 0: label = 35000
				else:
					label = 33564

				label = '%s (%s %d %s)' % (Translation.string(label), Font.icon(icon = Font.IconEstimator), count, Translation.string(35274))
			except:
				Logger.error()

		progress.append(100)
		return {'count' : count, 'multiplier' : multiply(count), 'default' : multiply(default), 'label' : [35484, label]}

	@classmethod
	def _optimizeMirror(self, progress = [], analyze = True):
		progress.append((0, 35273))

		count = default = 0
		label = 33387

		def multiply(count):
			return count * 0.02

		if analyze:
			try:
				from lib.modules.interface import Translation

				if ProviderBase.settingsGlobalMirrorEnabled():
					count = ProviderBase.settingsGlobalMirrorLimit()

				if count >= 6: label = 35002
				elif count >= 3: label = 35001
				elif count >= 1: label = 35000
				else: label = 33112

				label = '%s (%d %s)' % (Translation.string(label), count, Translation.string(35268))
			except:
				Logger.error()

		progress.append(100)
		multiplier = multiply(count)
		return {'count' : count, 'multiplier' : multiply(count), 'default' : multiply(default), 'label' : [35830, label]}

	@classmethod
	def _optimizeEvaluate(self, data, tradeoff):
		from lib.modules.interface import Translation

		def scale(rating, minimum, maximum, base = None):
			result = int(Math.round(Math.scale(value = rating, fromMinimum = 0, fromMaximum = 1, toMinimum = minimum, toMaximum = maximum), places = 0))
			if not base is None: result = Math.roundClosest(value = result, base = base)
			return result

		rating = data['rating']
		performance = data['performance']
		multiplier = data['multiplier']
		default = data['default']

		# Label
		labelFew = Translation.string(35000)
		labelSeveral = Translation.string(35001)
		labelMany = Translation.string(35002)
		labelDisabled = Translation.string(33022)

		# Language

		languages = Language.settingsCode()
		languageCount = len(languages)
		languageEnglish = languageCount >= 1 and Language.EnglishCode in languages
		languageEnglishOnly = languageCount == 1 and languages[0] == Language.EnglishCode
		languageEnglishPrimary = languageCount >= 1 and languages[0] == Language.EnglishCode
		languageForeign = len([i for i in languages if not i == Language.EnglishCode]) > 0
		languageForeignOnly = languageCount >= 1 and not Language.EnglishCode in languages
		languageForeignPrimary = languageCount >= 1 and not languages[0] == Language.EnglishCode

		# Rating

		# Use the hyperbolic tangent function (instead of a linear function) to reduce the impact of large ratings.
		# Otherwise, smaller ratings are adjusted a little, while larger ratings change a lot more.
		adjust = 0.7 # Reduce the impact of the multiplier, otherwise the rating is changed too much.
		multiplier = Math.scale(value = multiplier, fromMinimum = 0, fromMaximum = default, toMinimum = 0, toMaximum = 1)
		if multiplier > 1: rating -= (multiplier - 1) * Math.tanh(rating) * adjust
		elif multiplier < 1: rating += (1 - multiplier) * Math.tanh(rating) * adjust
		ratingOriginal = rating = (Math.tanh(rating) * 0.4) + (rating * 0.6)

		tradeoffMultiplier = 0
		if tradeoff == Manager.TradeoffSpeed: tradeoffMultiplier = -Manager.TradeoffFactor
		elif tradeoff == Manager.TradeoffResult: tradeoffMultiplier = +Manager.TradeoffFactor
		rating = rating * (1 + tradeoffMultiplier)
		rating = Math.round(min(1, max(0, rating)), places = 2)

		# Limit
		# The timeout should acutally be decreased if there is a speed tradeoff, since all the other parameters are decreased (aka smaller timeout needed).
		limitTime = scale(rating = 1 - ratingOriginal, minimum = 120, maximum = 400) # Use 90 instead of 60 as the minimum, since scrapes, even on a good device, mostly take more than 60 secs. Use 120 instead of 90, since show scraping can take longer than 90 (with packs etc).
		limitTime = Math.roundClosest(value = limitTime * (1 + (tradeoffMultiplier * 1.5)), base = 5)
		limitTime = min(max(limitTime, 90), 420)
		limitTimeLabel = ProviderBase.settingsGlobalLimitTimeLabel(value = limitTime)

		limitQuery = scale(rating = rating, minimum = 3, maximum = 10)
		limitQueryLabel = str(limitQuery)

		limitPage = scale(rating = rating, minimum = 1, maximum = 8)
		if tradeoff == Manager.TradeoffSpeed: limitPage -= 2
		elif tradeoff == Manager.TradeoffResult: limitPage += 2
		limitPage = min(max(limitPage, 2), 10)
		limitPageLabel = str(limitPage)

		limitRequest = scale(rating = rating, minimum = 250, maximum = 10000, base = 250)

		# Concurrency
		# On an Intel iX there is not significant difference in scraping time with different limits.
		# Anything below 1x core-count slows down scraping.
		# Test runs:
		# 	20 providers with slowest ones disabled.
		# 	Default scrape settings (packs, titles, keywords), except the page limit set to 5.
		#	Scraping episode and returning 1000+ links.
		threads = Hardware.processorCountThread()
		if Platform.pythonConcurrencyProcess() and threads >= 4 and performance['processor']['rating'] >= ProviderBase.Performance7:
			# 0.5x core-count (3): 100 seconds | 51% CPU load
			# 1x core-count + 1 (7): 68 seconds | 72% CPU load
			# 2x core-count + 1 (13): 58 seconds | 83% CPU load
			# Unlimited: 60 seconds | 81% CPU load
			concurrencyMode = ProviderBase.ConcurrencyProcess
			concurrencyLimit = scale(rating = rating, minimum = max(2, threads + 1), maximum = max(2, (threads * 2) + 1))
		else:
			# 0.5x core-count (3): 96 seconds | 38% CPU load
			# 1x core-count + 1 (7): 88 seconds | 42% CPU load
			# 2x core-count + 1 (13): 87 seconds | 42% CPU load
			# Unlimited: 84 seconds | 42% CPU load
			concurrencyMode = ProviderBase.ConcurrencyThread
			concurrencyLimit = 0
		concurrencyConnection = 0
		concurrencyLabel = Translation.string(36039 if concurrencyMode == ProviderBase.ConcurrencyThread else 36040)

		# Pack

		packMovie = rating >= ProviderBase.Performance4
		packShow = rating >= ProviderBase.Performance3
		packSeason = rating >= ProviderBase.Performance0 # Always enabled season packs. Raspberry Pi is at 8%.
		packCount = int(packMovie) + int(packShow) + int(packSeason)
		packEnabled = packCount > 0
		packLabel = labelFew if packCount == 1 else labelSeveral if packCount == 2 else labelMany if packCount == 3 else labelDisabled

		# Title

		titleCharacters = (languageForeignOnly and rating >= ProviderBase.Performance6) or (languageForeignPrimary and rating >= ProviderBase.Performance7) or (languageForeign and rating >= ProviderBase.Performance8)
		titleOriginal = (languageForeignOnly and rating >= ProviderBase.Performance0) or (languageForeignPrimary and rating >= (ProviderBase.Performance1 - ProviderBase.PerformanceHalf)) or (languageForeign and rating >= ProviderBase.Performance1) or (rating >= ProviderBase.Performance4)
		titleNative = (languageForeignOnly and rating >= ProviderBase.Performance0) or (languageForeignPrimary and rating >= (ProviderBase.Performance1 - ProviderBase.PerformanceHalf)) or (languageForeign and rating >= ProviderBase.Performance1) or (rating >= ProviderBase.Performance4)
		titleLocal = (languageForeignOnly and rating >= ProviderBase.Performance4) or (languageForeignPrimary and rating >= ProviderBase.Performance5) or (languageForeign and rating >= ProviderBase.Performance8)
		titleAlias = (languageForeignOnly and rating >= ProviderBase.Performance5) or (languageForeignPrimary and rating >= ProviderBase.Performance6) or (languageForeign and rating >= ProviderBase.Performance8)
		titleCount = int(2 if titleCharacters else 0) + int(titleOriginal) + int(titleNative) + int(titleLocal) + (3 if titleAlias else 0)
		titleEnabled = titleCount > 0
		titleLabel = labelMany if titleCount >= 5 else labelSeveral if titleCount >= 3 else labelFew if titleCount >= 1 else labelDisabled

		# Keyword

		keywordEnabled = rating >= ProviderBase.Performance2
		keywordEnglish = ProviderBase.KeywordNone
		if rating >= ProviderBase.Performance5 or (languageEnglish and rating >= ProviderBase.Performance4): keywordEnglish = ProviderBase.KeywordFull
		elif rating >= ProviderBase.Performance2 or (languageEnglish and rating >= ProviderBase.Performance1): keywordEnglish = ProviderBase.KeywordQuick
		keywordNative = ProviderBase.KeywordNone
		if rating >= ProviderBase.Performance8 or (languageForeign and rating >= ProviderBase.Performance7): keywordNative = ProviderBase.KeywordFull
		elif rating >= ProviderBase.Performance2 or (languageForeign and rating >= ProviderBase.Performance1): keywordNative = ProviderBase.KeywordQuick
		keywordCustom = ProviderBase.KeywordNone
		if languageForeign and rating >= ProviderBase.Performance9: keywordCustom = ProviderBase.KeywordFull
		elif languageForeign and rating >= ProviderBase.Performance8: keywordCustom = ProviderBase.KeywordQuick
		keywordCount = (2 if keywordEnglish == ProviderBase.KeywordFull else 1 if keywordEnglish == ProviderBase.KeywordQuick else 0) + (2 if keywordNative == ProviderBase.KeywordFull else 1 if keywordNative == ProviderBase.KeywordQuick else 0) + (2 if keywordCustom == ProviderBase.KeywordFull else 1 if keywordCustom == ProviderBase.KeywordQuick else 0)
		keywordEnabled = keywordCount > 0
		keywordLabel = labelMany if keywordCount >= 5 else labelSeveral if keywordCount >= 3 else labelFew if keywordCount >= 1 else labelDisabled

		# Year

		# Having multiple years should not happen that often. Always enable it.
		yearEnabled = True

		# Mirror

		mirrorEnabled = rating >= ProviderBase.Performance8
		mirrorLimit = scale(rating = rating, minimum = 1, maximum = 4)
		mirrorLabel = labelDisabled if not mirrorEnabled else labelMany if mirrorLimit >= 3 else labelSeveral if mirrorLimit >= 2 else labelFew if mirrorLimit >= 1 else labelDisabled

		# Providers

		self.settingsToggleDefault(save = False)
		providers = self.providers(reload = True)
		self.settingsRetrieve(providers = providers)

		providersAll = []
		for i in range(len(providers)):
			providersAll.append((providers[i].optimize(language = languages), providers[i]))

		providersEnabled = [i[1] for i in providersAll if i[0] is True]
		providersDisabled = [i[1] for i in providersAll if i[0] is False]
		providersAll = [i for i in providersAll if not i[0] is True and not i[0] is False]
		providersAll = Tools.listSort(data = providersAll, key = lambda i : i[0], reverse = True)
		providersAll = [i[1] for i in providersAll]

		providerMinimum = 5
		providerMaximum = 40 # 50 upper limit is too much for show scraping, even for high-end devices.
		providerRating = Math.power(1.5, rating) - 1
		providerLimit = providerMinimum + scale(rating = providerRating, minimum = 0, maximum = providerMaximum)
		providerLimit = max(providerMinimum, int(providerLimit))
		if tradeoff == Manager.TradeoffSpeed: providerLimit = providerLimit - max(5, int(providerLimit * 0.1))
		elif tradeoff == Manager.TradeoffResult: providerLimit = providerLimit + max(5, int(providerLimit * 0.1))
		providerLimit = max(providerMinimum, providerLimit)

		providersEnabled.extend(providersAll[:providerLimit])
		providersDisabled.extend(providersAll[providerLimit:])

		for i in providersEnabled: i.enableSettingsProvider()
		for i in providersDisabled: i.disableSettingsProvider()
		providers = providersEnabled + providersDisabled

		# Result

		return {
			'rating' : rating,
			'performance' : performance,

			'settings' : {
				'providers' : providers,
				'limit' : {
					'time' : limitTime,
					'query' : limitQuery,
					'page' : limitPage,
					'request' : limitRequest,
				},
				'concurrency' : {
					'mode' : concurrencyMode,
					'limit' : concurrencyLimit,
					'connection' : concurrencyConnection,
				},
				'pack' : {
					'enabled' : packEnabled,
					'movie' : packMovie,
					'show' : packShow,
					'season' : packSeason,
				},
				'title' : {
					'enabled' : titleEnabled,
					'characters' : titleCharacters,
					'original' : titleOriginal,
					'native' : titleNative,
					'local' : titleLocal,
					'alias' : titleAlias,
				},
				'keyword' : {
					'enabled' : keywordEnabled,
					'english' : keywordEnglish,
					'native' : keywordNative,
					'custom' : keywordCustom,
				},
				'year' : {
					'enabled' : yearEnabled,
				},
				'mirror' : {
					'enabled' : mirrorEnabled,
					'limit' : mirrorLimit,
				},
			},

			'label' : {
				'providers' : str(self.settingsCount(providers = providers)),
				'time' : limitTimeLabel,
				'query' : limitQueryLabel,
				'page' : limitPageLabel,
				'concurrency' : concurrencyLabel,
				'pack' : packLabel,
				'title' : titleLabel,
				'keyword' : keywordLabel,
				'mirror' : mirrorLabel,
			},
		}

	@classmethod
	def _optimizeHelp(self):
		from lib.modules.interface import Dialog, Format

		newline = Format.fontNewline()
		newline2 = newline + newline

		message = ''

		message += self._help(
			label = 'Settings Optimization',
			description = newline2.join([
				'Certain devices might take very long to scrape, because they have limited processing power or slow internet. This feature optimizes the scraping settings and toggles individual providers according to your device\'s hardware performance and internet connection speed.',
				'There is a general tradeoff between the number of links found and the time it takes to scrape. Some settings increase the number of links found, but also increase scraping time. Other settings might reduce scraping time, but also reduce the number of links found.',
				'The optimization process is only a rough approximation of good parameters. Manually adjusting individual settings might further improve the scraping performance for your device.',
			]),
		)

		message += self._help(
			label = 'Device Performance',
			description = 'The performance of devices is broadly categorized as follows:',
			items = [
				{'label' : 'High-end Devices', 'description' : 'Most laptops and desktop computers with a decent processor. These devices can handle a lot of providers and queries without notably affecting the scraping duration.'},
				{'label' : 'Low-end Devices', 'description' : 'Devices with slow processors, such as Amazon Firesticks, Nvidia Shields, Apple TVs, Rokus, Raspberry Pis, Odroids, and most other media boxes and SBCs. These devices scrape very slowly due to limited processing power. Reducing the number of providers and queries can improve scraping time.'},
			]
		)

		message += self._help(
			label = 'Device Rating',
			description = 'The rating of devices is calculated as follows:',
			items = [
				{'label' : 'Processor', 'description' : 'The CPU is the most important component affecting performance. Executing providers in parallel, performing multiple queries, and processing metadata requires a lot of processing power. Most Intel or AMD processors found in laptops and desktops are able to handle the processing. ARM or other processors found in phones, tablets, media boxes, and SBCs are slow and might take considerably longer to process links.'},
				{'label' : 'Memory', 'description' : 'RAM has a lesser effect on the performance, as long as you have a few hundred MB free memory. Laptops, desktops, and most phones, tablets, and media boxes have enough memory. Very old media boxes or SBCs with 1GB memory or less might have performance issues.'},
				{'label' : 'Storage', 'description' : 'Secondary storage only has a minor impact on performance. Storage is only used to load cached data or save streams to the cache at the end of the scraping process. SSDs, eMMCs, and HDDs are fast enough. SD cards, used by devices such as Raspberry Pis, are slow and might reduce performance. First generation Class 10 SD cards and lower are really slow. Newer generations of Class 10 cards are slightly better.'},
				{'label' : 'Internet', 'description' : 'The internet connection speed only has a noticeable impact if it is slower than the processing of links and metadata. If you have a fast processor and slow internet, the internet, instead of the processor, might be the bottleneck holding up scraping. Speeds of 10 mbps or faster should be able to handle any query load. 4 mbps or slower might sometimes increase scraping time.'},
			]
		)

		message += self._help(
			label = 'Scraping Factors',
			description = 'Scraping time is influenced by the following factors:',
			items = [
				{'label' : 'Providers', 'description' : 'Scraping takes longer the more providers are enabled. Decreasing the number of providers is the first step that should be taken in order to reduce scraping time. Many providers share the same links. Enabling too many providers will result in many duplicate links and only prolong scraping unnecessarily.'},
				{'label' : 'Queries', 'description' : 'Each provider can submit multiple different search queries to servers in order to find more links with name variations, such as pack scraping, alternative titles and keywords. The more queries that are made, the longer scraping will take.'},
				{'label' : 'Metadata', 'description' : 'Extracting metadata from file names is a computational expensive task and can substantially increase scraping time on devices with a slow processor. Since this feature is integral to the addon, there is not much that can be done, except using a better device. However, reducing the number of providers and queries will reduce the number of links found. Fewer links means less metadata extraction, which in turn reduces processor load and scraping time.'},
			]
		)

		message += self._help(
			label = 'Settings Labels',
			description = 'Options that are marked with a green arrow in the settings dialog have an affect on the scraping duration:',
			items = [
				{'label' : 'Up Arrow (%s)' % Format.font('↑', color = Format.ColorPrimary), 'description' : 'Enabling or increasing these settings will prolong scraping. These settings typically add additional queries which increase the likelihood of finding more links, but also take longer since more requests have to be made to servers.'},
				{'label' : 'Down Arrow (%s)' % Format.font('↓', color = Format.ColorPrimary), 'description' : 'These settings can be used to restrict time or resources in order to reduce the scraping duration. These settings do not decrease scraping time directly, but rather cut off the scraping process once certain conditions have been met.'},
				{'label' : 'Up-Down Arrow (%s)' % Format.font('↕', color = Format.ColorPrimary), 'description' : 'These settings are highly depended on your device\'s hardware and can go either way. Changing these settings can sometimes decrease, and in other cases, increase scraping time. Either test them to find the optimal settings for your device, or leave them at their default values.'},
			]
		)

		message += self._help(
			label = 'Settings Options',
			description = 'The scraping settings do the following:',
			items = [
				{'label' : 'Limits', 'description' : 'Limit the scraping time, number of pages and requests that each provider can make. These settings reduce scraping time and server load.'},
				{'label' : 'Concurrency', 'description' : 'Change the manner in which providers are executed in parallel. These settings are dependent on your device\'s processor capabilities and can either increase or decrease scraping time slightly.'},
				{'label' : 'Packs', 'description' : 'Search file packs in addition to individual movies or episodes. Additional queries are made which increases scraping time.'},
				{'label' : 'Titles', 'description' : 'Search alternative titles besides the regular English title. These settings improve the chances of finding non-English titles. Additional queries are made which increases scraping time.'},
				{'label' : 'Keywords', 'description' : 'Search alternative keywords, mostly used for pack scraping. Keywords, such as "pack", "complete", or "trilogy" improve the probability of finding file packs. Additional queries are made which increases scraping time.'},
				{'label' : 'Years', 'description' : 'Search alternative release years, mostly used for movies. In rare cases metadata providers might have different years for the same title, especially if it was released at the start or end of the year. Additional queries are made in special cases which increases scraping time.'},
				{'label' : 'Mirrors', 'description' : 'Search mirror or unblocked domains if the main domain of a provider is unreachable. Scraping time can increase slightly if some main domains are down.'},
				{'label' : 'Termination', 'description' : 'Stop providers early under certain conditions. These setting can reduce scraping time.'},
			]
		)

		message += self._help(
			label = 'Tradeoff',
			description = 'The optimization process aims to find the optimal tradeoff between the number of links found and the scraping time. The tradeoff can be adjusted as follows:',
			items = [
				{'label' : 'Mixed Tradeoff', 'description' : 'The best configuration estimated by the addon.'},
				{'label' : 'Speed Tradeoff', 'description' : 'Adjust the estimated configuration by putting a greater emphasis on reducing scraping time than on finding more links.'},
				{'label' : 'Result Tradeoff', 'description' : 'Adjust the estimated configuration by putting a greater emphasis on finding more links than on reducing scraping time.'},
			]
		)

		Dialog.text(title = 35016, message = message)

	@classmethod
	def _optimizeApply(self, data = None, updateScrape = True, updateProvider = True, callbackNext = None, internal = False, settings = False):
		from lib.modules.interface import Translation, Dialog, Loader

		if not internal: Loader.show()

		if data is None:
			from lib.modules.window import WindowOptimization
			data = WindowOptimization.data()

		update = False
		if data and 'settings' in data:
			update = True
			data = data['settings']
			if updateScrape:
				ProviderBase.settingsGlobalLimitTimeSet(data['limit']['time'])
				ProviderBase.settingsGlobalLimitQuerySet(data['limit']['query'])
				ProviderBase.settingsGlobalLimitPageSet(data['limit']['page'])
				ProviderBase.settingsGlobalLimitRequestSet(data['limit']['request'])

				ProviderBase.settingsGlobalConcurrencyModeSet(data['concurrency']['mode'])
				ProviderBase.settingsGlobalConcurrencyLimitSet(data['concurrency']['limit'])
				ProviderBase.settingsGlobalConcurrencyConnectionSet(data['concurrency']['connection'])

				ProviderBase.settingsGlobalPackEnabledSet(data['pack']['enabled'])
				ProviderBase.settingsGlobalPackMovieSet(data['pack']['movie'])
				ProviderBase.settingsGlobalPackShowSet(data['pack']['show'])
				ProviderBase.settingsGlobalPackSeasonSet(data['pack']['season'])

				ProviderBase.settingsGlobalTitleEnabledSet(data['title']['enabled'])
				ProviderBase.settingsGlobalTitleCharacterSet(data['title']['characters'])
				ProviderBase.settingsGlobalTitleOriginalSet(data['title']['original'])
				ProviderBase.settingsGlobalTitleNativeSet(data['title']['native'])
				ProviderBase.settingsGlobalTitleLocalSet(data['title']['local'])
				ProviderBase.settingsGlobalTitleAliasSet(data['title']['alias'])

				ProviderBase.settingsGlobalKeywordEnabledSet(data['keyword']['enabled'])
				ProviderBase.settingsGlobalKeywordEnglishSet(data['keyword']['english'])
				ProviderBase.settingsGlobalKeywordNativeSet(data['keyword']['native'])
				ProviderBase.settingsGlobalKeywordCustomSet(data['keyword']['custom'])

				ProviderBase.settingsGlobalYearEnabledSet(data['year']['enabled'])

				ProviderBase.settingsGlobalMirrorEnabledSet(data['mirror']['enabled'])
				ProviderBase.settingsGlobalMirrorLimitSet(data['mirror']['limit'])

				Settings.set(id = Manager.SettingsScrapeOptimize, value = Translation.string(35750))

			if updateProvider:
				self.settingsToggleDefault()
				self.settingsUpdate(providers = data['providers'])
				self.settingsLabel(wait = not internal and settings)
				Settings.set(id = Manager.SettingsProviderOptimize, value = Translation.string(35750))

		if not internal:
			Loader.hide()
			if data and update and (updateScrape or updateProvider):
				Dialog.notification(title = 35016, message = 36134, icon = Dialog.IconSuccess, duplicates = True)

			if settings:
				if updateScrape and updateProvider: settings = None
				elif updateScrape: settings = Manager.SettingsScrapeOptimize
				elif updateProvider: settings = Manager.SettingsProviderOptimize
				else: settings = None
				Settings.launch(id = settings)

		if callbackNext: callbackNext()
		return data

	@classmethod
	def optimize(self,
		# Anaylze specific components which will be used to calculate the performance.
		analyzeProcessor = True, # Device processor.
		analyzeMemory = True, # Device memory.
		analyzeStorage = True, # Device storage.
		analyzeConnection = True, # Internet connection speed.
		analyzeProvider = False, # Number of enabled providers.
		analyzePack = False, # Pack scraping.
		analyzeTitle = False, # Number of titles to scrape.
		analyzeKeyword = False, # Number of keywords to scrape.
		analyzeMirror = False, # Mirror sites.

		# Update specific settings.
		updateScrape = True, # Update the scarping settings.
		updateProvider = True, # Update the provider settings.

		settings = False, # Launch settings dialog afterwards.
		internal = False, # Internal or hidden optimization without any interface component.
		stepper = False, # Show the window as part of a step-by-step wizard.
		tradeoff = TradeoffMix, # Default tradeoff.
	):
		from lib.modules.interface import Translation
		from lib.modules.window import WindowOptimization

		try:
			index = 0
			thread = None
			label = None
			functions = []
			progress = []
			self.tResult = []

			#Manager.OptimizeDevice = {'name' : 'Odroid N2+', 'hardware' : '4 cores @ 2.2GHz + 2 cores @ 1.9GHz | 4GB', 'common' : True, 'processor' : {'total' : 12600000000, 'single' : 2200000000}, 'memory' : 4294967296, 'storage' : {'read' : 10485760, 'write' : 10485760}}
			#Manager.OptimizeDevice = {'name' : 'Raspberry Pi 4', 'hardware' : '4 cores @ 1.5GHz | 4GB', 'common' : True, 'processor' : {'total' : 6000000000, 'single' : 1500000000}, 'memory' : 4294967296, 'storage' : {'read' : 10485760, 'write' : 10485760}}
			#Manager.OptimizeDevice = {'name' : 'Amazon Fire TV Stick 4K Max', 'hardware' : '4 cores @ 1.8GHz | 2GB', 'common' : False, 'processor' : {'total' : 7200000000, 'single' : 1800000000}, 'memory' : 2147483648, 'storage' : {'read' : 52428800, 'write' : 31457280}}

			def _optimizeExecute(function, **kwargs):
				result = function(**kwargs)
				try: result['analyze'] = kwargs['analyze']
				except: result['analyze'] = False
				self.tResult.append(result)

			functions.append((0.65, {'function' : self._optimizeDevice, 'processor' : analyzeProcessor, 'memory' : analyzeMemory, 'storage' : analyzeStorage, 'connection' : analyzeConnection, 'progress' : progress, 'analyze' : analyzeProcessor or analyzeMemory or analyzeStorage or analyzeConnection}))
			functions.append((0.07, {'function' : self._optimizeProvider, 'progress' : progress, 'analyze' : analyzeProvider}))
			functions.append((0.07, {'function' : self._optimizePack, 'progress' : progress, 'analyze' : analyzePack}))
			functions.append((0.07, {'function' : self._optimizeTitle, 'progress' : progress, 'analyze' : analyzeTitle}))
			functions.append((0.07, {'function' : self._optimizeKeyword, 'progress' : progress, 'analyze' : analyzeKeyword}))
			functions.append((0.07, {'function' : self._optimizeMirror, 'progress' : progress, 'analyze' : analyzeMirror}))

			label = Translation.string(35007)
			if not internal: WindowOptimization.update(diagnoseProgress = 0, diagnoseStatus = label)

			function = None
			progressCurrent = 0
			while True:
				if not internal:
					while len(progress) > 0:
						try:
							progression = progress.pop(0)
							if Tools.isArray(progression):
								subProgress = progression[0]
								label = Translation.string(progression[1])
							elif Tools.isNumber(progression):
								subProgress = progression
						except: pass
						if subProgress >= 100:
							progressCurrent += weight * subProgress
							progressNew = progressCurrent
						else:
							progressNew = progressCurrent + (weight * subProgress)
						WindowOptimization.update(diagnoseProgress = int(progressNew * 0.99), diagnoseStatus = label)

				if thread is None or not thread.is_alive():
					if index >= len(functions): break
					weight, function = functions[index]
					thread = Pool.thread(target = _optimizeExecute, kwargs = function)
					thread.start()
					index += 1

				if internal: Time.sleep(0.03)
				else: Time.sleep(0.2)
			if not internal: WindowOptimization.update(diagnoseProgress = 100, diagnoseStatus = label)

			rating = 0
			multiplier = 0
			default = 0
			performance = None
			for result in self.tResult:
				if 'base' in result: rating += result['base']
				if 'multiplier' in result: multiplier += result['multiplier']
				if 'default' in result and 'multiplier' in result: default += result['default']
				if 'data' in result: performance = result['data']
			if not performance: performance = Hardware.performance()

			data = {
				'rating' : rating,
				'performance' : performance,
				'multiplier' : multiplier,
				'default' : default,
			}
			if not internal:
				WindowOptimization.update(diagnoseData = data, diagnoseScrape = updateScrape, diagnoseProvider = updateProvider)
			else:
				data = self._optimizeEvaluate(data = data, tradeoff = tradeoff)
				self._optimizeApply(data = data, updateScrape = updateScrape, updateProvider = updateProvider, internal = internal, settings = settings)
		except:
			Logger.error()
			self._optimizeApply(updateScrape = updateScrape, updateProvider = updateProvider, internal = internal, settings = settings)

	@classmethod
	def optimizeShow(self,
		analyzeProcessor = True,
		analyzeMemory = True,
		analyzeStorage = True,
		analyzeConnection = True,
		analyzeProvider = False,
		analyzePack = False,
		analyzeTitle = False,
		analyzeKeyword = False,
		analyzeMirror = False,

		updateScrape = True,
		updateProvider = True,

		navigationNext = True,
		callbackClose = None,
		callbackCancel = None,
		callbackBack = None,
		callbackNext = None,

		category = True, # Show the provider/scrape category buttons in the window.
		settings = False,
		internal = False,
		stepper = False,
		wait = False,
	):
		Settings.set(Manager.SettingsOptimization, True)

		def cancel():
			self._optimizeApply(
				updateScrape = updateScrape,
				updateProvider = updateProvider,
				internal = internal,
				settings = settings,
			)
			if callbackCancel: callbackCancel()
			return True

		from lib.modules.window import WindowOptimization
		return WindowOptimization.show(
			wait = wait,
			stepper = True if stepper else False,
			progress = stepper if Tools.isNumber(stepper) else None,
			navigationNext = navigationNext,
			navigationCategory = category,
			callbackHelp = 	self._optimizeHelp,
			callbackTradeoff = self._optimizeEvaluate,
			callbackClose = callbackClose,
			callbackCancel = cancel,
			callbackDiagnose = lambda : Pool.thread(target = self.optimize, kwargs = {
				'analyzeProcessor' : analyzeProcessor,
				'analyzeMemory' : analyzeMemory,
				'analyzeStorage' : analyzeStorage,
				'analyzeConnection' : analyzeConnection,
				'analyzeProvider' : analyzeProvider,
				'analyzePack' : analyzePack,
				'analyzeTitle' : analyzeTitle,
				'analyzeKeyword' : analyzeKeyword,
				'analyzeMirror' : analyzeMirror,

				'updateScrape' : updateScrape,
				'updateProvider' : updateProvider,

				'settings' : settings,
				'internal' : internal,
				'stepper' : stepper,
			}).start(),
			callbackBack = callbackBack,
			callbackNext = lambda data, updateScrape, updateProvider: self._optimizeApply(
				data = data,
				updateScrape = updateScrape,
				updateProvider = updateProvider,
				callbackNext = callbackNext,
				internal = internal,
				settings = settings,
			),
		)

	@classmethod
	def optimizeScrape(self, wait = False, **kwargs):
		return self.optimizeShow(wait = wait, analyzePack = False, analyzeTitle = False, analyzeKeyword = False, analyzeMirror = False, updateProvider = False, **kwargs)

	@classmethod
	def optimizeProvider(self, wait = False, **kwargs):
		return self.optimizeShow(wait = wait, analyzeProvider = False, updateScrape = False, **kwargs)

	@classmethod
	def optimizeInternal(self, **kwargs):
		return self.optimize(analyzeConnection = False, internal = True, **kwargs)

	@classmethod
	def optimized(self):
		return Settings.getBoolean(Manager.SettingsOptimization)

	##############################################################################
	# LINKS
	##############################################################################

	@classmethod
	def linksTime(self, time = False):
		result = ProviderBase.TimeCache
		if time: result = Time.timestamp() - result
		return result

	@classmethod
	def linksDatabaseClear(self, all = True, compress = True):
		if all: self.databaseClear(providers = False, links = True, streams = False, failures = False)
		else: self._databaseInitialize()._delete('DELETE FROM %s WHERE time < ?' % Manager.DatabaseLinks, parameters = [self.linksTime(time = True)], compress = compress)

	@classmethod
	def linksDatabaseClearOld(self):
		self.linksDatabaseClear(all = False)

	@classmethod
	def _linksDatabaseInitialize(self):
		return self._databaseInitialize(providers = False, links = True, streams = False, failures = False)

	@classmethod
	def _linksDatabaseQuery(self, query, parameters = None):
		return self._linksDatabaseInitialize()._select(query = query % Manager.DatabaseLinks, parameters = parameters)

	@classmethod
	def linksRetrieve(self, provider = None, query = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, time = None):
		if provider.typeLocal(): return None # always rescrape local providers.

		id = self._databaseId(provider = provider, query = query, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, numberSeason = numberSeason, numberEpisode = numberEpisode)
		if time is None: time = self.linksTime(time = True)

		links = self._linksDatabaseInitialize()._selectSingle(query = 'SELECT data FROM %s WHERE id = ? AND time >= ?;' % Manager.DatabaseLinks, parameters = [id, time])
		try: return Converter.jsonFrom(links[0])['data']
		except: return None

	@classmethod
	def linksInsert(self, data, provider = None, query = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None):
		id = self._databaseId(provider = provider, query = query, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, numberSeason = numberSeason, numberEpisode = numberEpisode)
		base = self._linksDatabaseInitialize()
		data = Converter.jsonTo({'data' : data}) # Some external providers return a dictionary.

		base._delete(query = 'DELETE FROM %s WHERE id = ?;' % Manager.DatabaseLinks, parameters = [id])
		base._insert(query = 'INSERT INTO %s VALUES (?, ?, ?, ?);' % Manager.DatabaseLinks, parameters = [id, provider.id(), Time.timestamp(), data])

	##############################################################################
	# STREAMS
	##############################################################################

	@classmethod
	def streamsTime(self, time = False):
		result = ProviderBase.TimeCache
		if time: result = Time.timestamp() - result
		return result

	@classmethod
	def streamsDatabaseClear(self, all = True, compress = True):
		if all: self.databaseClear(providers = False, links = False, streams = True, failures = False)
		else: self._databaseInitialize()._delete('DELETE FROM %s WHERE time < ?' % Manager.DatabaseStreams, parameters = [self.streamsTime(time = True)], compress = compress)

	@classmethod
	def streamsDatabaseClearOld(self):
		self.streamsDatabaseClear(all = False)

	@classmethod
	def _streamsDatabaseInitialize(self):
		return self._databaseInitialize(providers = False, links = False, streams = True, failures = False)

	@classmethod
	def _streamsDatabaseQuery(self, query, parameters = None):
		return self._streamsDatabaseInitialize()._select(query = query % Manager.DatabaseStreams, parameters = parameters)

	@classmethod
	def streamsRetrieve(self, provider = None, query = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, time = None):
		from lib.modules.stream import Stream

		if provider.typeLocal(): return None # always rescrape local providers.

		id = self._databaseId(provider = provider, query = query, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, numberSeason = numberSeason, numberEpisode = numberEpisode)

		if time is None: time = self.streamsTime(time = True)
		else: time = Time.timestamp() - time

		streams = self._streamsDatabaseInitialize()._selectSingle(query = 'SELECT data FROM %s WHERE id = ? AND time >= ?;' % Manager.DatabaseStreams, parameters = [id, time])
		try:
			streams = Converter.jsonFrom(streams[0])
			streams = [Stream.load(data = stream) for stream in streams]
			[stream.infoCacheSet(True) for stream in streams]
			return streams
		except: return None

	@classmethod
	def streamsInsert(self, data, provider = None, query = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None):
		id = self._databaseId(provider = provider, query = query, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, numberSeason = numberSeason, numberEpisode = numberEpisode)
		base = self._streamsDatabaseInitialize()

		base._delete(query = 'DELETE FROM %s WHERE id = ?;' % Manager.DatabaseStreams, parameters = [id])
		base._insert(query = 'INSERT INTO %s VALUES (?, ?, ?, ?);' % Manager.DatabaseStreams, parameters = [id, provider.id(), Time.timestamp(), Converter.jsonTo(data)])
