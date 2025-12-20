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

from lib.modules.tools import System, File, Hash, Language, Tools, Time, Media, Settings, Converter, Regex, Extension, Math
from lib.modules.network import Networker
from lib.providers.core.base import ProviderBase
from lib.modules.stream import Stream
from lib.modules.external import Importer

class ProviderExternal(ProviderBase):

	Settings = {}

	def __init__(self,
		supportMovie	= True,
		supportShow		= True,
		supportPack		= False,

		**kwargs
	):
		self.dataClear()
		self.mData['instance'] = {'id' : None}
		self.mInstance = None

		try: moduleParent = self.IdParent
		except: moduleParent = None

		try: moduleSettings = self.IdSettings
		except: moduleSettings = None

		try: prepare = self.Prepare
		except: prepare = ProviderBase.PrepareDefault

		# First initialize here.
		ProviderBase.initialize(self,
			description			= 'This provider utilizes scrapers from the external addon [I]{addon}[/I]. [I]{addon}[/I] must be installed and enabled in order to be searched. Only hoster scrapers are used. Some scrapers might be ignored if they contain bugs, cannot resolve import statements, or cannot be executed for other reasons.',

			addonId				= self.IdGaia,
			addonName			= self.Name,
			addonRank			= self.Rank,
			addonSettings		= self.Settings,
			addonPrepare		= prepare,
			addonModuleScraper	= self.IdAddon,
			addonModuleParent	= moduleParent,
			addonModuleSettings	= moduleSettings,

			supportMovie		= supportMovie,
			supportShow			= supportShow,
			supportPack			= supportPack,
		)

		# Then replace the values with the JSON data from the database.
		# Do not call the constructor before initialize(), since kwargs contains the JSON data that should overwrite any existing values.
		ProviderBase.__init__(self, dataClear = False, **kwargs)

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self, **kwargs):
		# Do not intialize like native Gaia providers.
		# External providers are always loaded from the JSON data in the database.
		# If we call the parent intialize() here, it will overwrite many attributes (eg: name).
		pass

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			ProviderExternal.Settings = {}

	##############################################################################
	# ENABLED
	##############################################################################

	def enabledExternal(self):
		# If an external addon is NOT installed, but its category is enabled in the settings, it will be returned by Manager.providers(enabled = True).
		# In such a case, check if the instance has an ID. If it has an ID, it is installed. If it does not have an ID, it is not installed.
		return bool(self.mData['instance'].get('id'))

	##############################################################################
	# INSTANCES
	##############################################################################

	@classmethod
	def instancesPath(self):
		return System.pathProviders(self.Name)

	@classmethod
	def instancesInclude(self, id = None, path = None):
		# NB: Translate paths for Windows, since joinPath() uses '\' and the special protocol uses '/'.
		# Without translating, the sys path is invalid.
		# On Linux, it seems all addons are added to the system path by default, and the code below (except for the scraping addon) is not required.
		# However, on Windows, the dependecy addons are not included by default (if they do not appear in Gaia's addon.xml) and they have to be imported manually.

		if path is None:
			if id is None: path = self.instancesPath()
			else: path = File.joinPath(File.pathHome(), 'addons', id)
		path = File.translate(path)
		if not File.existsDirectory(path): return False

		# Always include sub-dependecies before dependecies.
		data = File.readNow(File.translate(File.joinPath(path, 'addon.xml')))
		dependencies = Regex.extract(data = data, expression = '<import.*?addon\s*=\s*"(.*?)"', group = None, all = True)
		if dependencies:
			for dependency in dependencies:
				if not dependency.startswith('xbmc.'):
					self.instancesInclude(id = dependency)

		# Some modules, like kodi-six, use a different directory name than "lib".
		library = Regex.extract(data = data, expression = '<extension.*?library\s*=\s*"(.*?)".*?point\s*=\s*"xbmc.python.module".*?>')
		if not library: library = Regex.extract(data = data, expression = '<extension.*?point\s*=\s*"xbmc.python.module".*?library\s*=\s*"(.*?)".*?>')
		if not library: library = 'lib'
		library = File.translate(File.joinPath(path, library))
		if File.existsDirectory(library):
			import sys
			if not library in sys.path: sys.path.append(library)

		return True

	@classmethod
	def instancesRename(self, path, extra = []):
		# Some scrapers, like Crew, have the Furk username/password in a different addon's settings.
		# The scraper module addon can be installed without the main video addon.
		# If so, xbmcaddon.Addon(idSettings) will throw a runtime exception.
		# Best would be to have a try-catch statement, but that cannot be placed in a single line.
		# The best option is therefore to use the JSON RPC to check if the main addon is enabled before passing the ID to xbmcaddon.Addon.
		# This assumes that the file being processes has the "xbmc" module already imported.
		# If this is not the case in the future, we might need to do a full multi-line replacement or add a wrapper function that has a try-catch inside.
		try:
			idSettings = self.IdSettings
			idSettings = '"%s" if \'"enabled":true\' in xbmc.executeJSONRPC(\'{"jsonrpc":"2.0","id":"1","method":"Addons.GetAddonDetails","params":{"addonid":"%s","properties":["enabled"]}}\') else "%s"' % (self.IdSettings, self.IdSettings, self.IdAddon)
		except:
			idSettings = '"%s"' % self.IdAddon

		replacementsMain = [
			['from resources.lib.', 'from %s.' % self.IdLibrary],
		]

		replacements = []
		replacements.extend(replacementsMain)

		# CloudFlare import can clash with an import from another addon.
		replacements.extend([
			['from %s.modules import cfscrape' % self.IdLibrary, 'from %s.modules import cfscrape' % self.IdLibrary],
			['import pyaes', 'from %s.modules import pyaes' % self.IdLibrary],
			['from %s.modules from %s.modules import pyaes' % (self.IdLibrary, self.IdLibrary), 'from %s.modules import pyaes' % self.IdLibrary], # Fix duplicate replacements (some pyaes are imported from resources.lib, others are just import pyaes)
			['from %s.modules from %s.modules import pyaes' % (self.IdLibrary, self.IdLibrary), 'from %s.modules import pyaes' % self.IdLibrary], # Fix duplicate replacements (some pyaes are imported from resources.lib, others are just import pyaes)
			['xbmcaddon.Addon().getSetting', 'xbmcaddon.Addon(' + idSettings + ').getSetting'],
			['xbmcaddon.Addon().setSetting', 'xbmcaddon.Addon(' + idSettings + ').setSetting'],
			['xbmcaddon.Addon()', 'xbmcaddon.Addon("' + self.IdAddon + '")'],
			['if debrid.status() is False:', 'if False:'],
			['if debrid.status() == False:', 'if False:'],
			['filename = filename.split(addon)[1]', 'filename = filename.split("%s")[1]' % self.Name],
		])

		for ext in extra:
			replacements.append(['from %s.%s.%s.lib' % (self.IdLibrary, self.Path[-1], ext), 'from %s.%s.%s.libxyz' % (self.IdLibrary, self.Path[-1], ext)])

		try: replacements.extend(self.Replacements)
		except: pass

		directories, files = File.listDirectory(path, absolute = True)
		flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines
		flags2 = Regex.FlagCaseInsensitive | Regex.FlagMultiLines
		for file in files:
			if file.endswith('.py'):
				data = original = File.readNow(file)

				for replace in replacements:
					data = data.replace(replace[0], replace[1])

				# TheCrew -> client.py: has base64 encoded code that also contain imports.
				if not 'cfscrape' in file and 'eval(' in data:
					replacement = ')'
					for replace in replacementsMain:
						replacement += '.replace(b\'%s\', b\'%s\')' % (replace[0], replace[1])
					data = Regex.replace(data = data, expression = 'b64decode\(eval\(.*?\)(\))', replacement = replacement, group = 1, all = True, flags = flags)

				# There is a sporadic error when importing modules if multiple external addons are used.
				# These are random (about 50% of the time) and depend on the order in which external providers are executed.
				# For example:
				#		FenomScrapers-Myvideolink -> AttributeError -> ['Traceback (most recent call last):\n',
				#		'File ".kodi/userdata/addon_data/plugin.video.gaia/Providers/FenomScrapers/lib/fenomscrapers/sources_fenomscrapers/hosters/myvideolink.py", line 51, in sources\n
				#		name = source_utils.strip_non_ascii_and_unprintable(post[1])\n', "AttributeError: module 'oathscrapers.modules.source_utils' has no attribute 'strip_non_ascii_and_unprintable'\n",
				#		'\nDuring handling of the above exception, #	another exception occurred:\n\n', 'Traceback (most recent call last):\n', '  File "plugin.video.gaia/lib/providers/core/external.py", line 551, in search\n
				#		 elif count == 2: items = instance.sources(url, hostersAll)\n', '  File ".kodi/userdata/addon_data/plugin.video.gaia/Providers/FenomScrapers/lib/fenomscrapers/sources_fenomscrapers/hosters/myvideolink.py", line 120, in sources\n
				#		source_utils.scraper_error(\'MYVIDEOLINK\')\n', "AttributeError: module 'oathscrapers.modules.source_utils' has no attribute 'scraper_error'\n"]
				# The problem is that the imports of modules from different addons with the same name can overwrite each other.
				# For instance, in Fenom -> maxrls.py:
				#		from fenomscrapers.modules import source_utils
				# This will correctly import source_utils from the fenomscrapers directory.
				# However, when an Oath scraper executes afterwards and has:
				#		from oathscrapers.modules import source_utils
				# The Oath import will overwrite the Fenom import of source_utils. Hence, when Fenom's maxrls.py actually uses functions from source_utils, it might end up using source_utils from Oath.
				# This does not make sense, since scrapers import specifically from their own code (eg: "from fenomscrapers." or "from oathscrapers").
				# But for some reason Python or Kodi get these mixed up, probably because it relies only on the file name and not its full import path.
				# For many files/functions this is not a problem, since they are the same across addons.
				# However, in some cases if the file/functions are different, it can throw exceptions.
				# The problem is mitigated by replacing all import statements with addon-specific aliases (eg: from fenomscrapers.modules import source_utils as fenomscrapers_source_utils).
				modules = Regex.extract(data = data, expression = 'from\s+%s.*?\s+import\s+(.*?)\n' % self.IdLibrary, group = None, all = True, flags = flags)
				if modules:
					modules = [module.split(',') for module in modules]
					modules = Tools.listFlatten(modules)
					modules = [module.strip() for module in modules]
					modules = Tools.listUnique(modules)
					for module in modules:
						if ' as ' in module:
							module = Regex.extract(data = module, expression = 'as\s+(.*)', group = 1)
							alias = '%s_%s' % (self.IdLibrary, module)
							data = Regex.replace(data = data, expression = 'from\s+%s.*?\s+import\s+.*?\s+as\s+(%s)' % (self.IdLibrary, module), replacement = alias, group = 1, all = True, flags = Regex.FlagNone)
						else:
							alias = '%s_%s' % (self.IdLibrary, module)
							data = Regex.replace(data = data, expression = 'from\s+%s.*?\s+import.*?[\s,]+(?<!%s_)(%s)' % (self.IdLibrary, self.IdLibrary, module), replacement = '%s as %s' % (module, alias), group = 1, all = True, flags = Regex.FlagNone)

						if module.isupper(): data = Regex.replace(data = data, expression = '(%s)' % module, replacement = alias, group = 1, all = True, flags = Regex.FlagNone) # Assume a variable is imported (eg: control.py -> UNDESIRABLES).
						else: data = Regex.replace(data = data, expression = '(%s)[\.\(\[]' % module, replacement = alias, group = 1, all = True, flags = Regex.FlagNone)

				# Calls to the parent's addon settings or info.
				# These calls fail if the parent addon is not installed or disabled.
				# Eg: OathScrapers -> cache.py -> data_path = oathscrapers_control.transPath(oathscrapers_control.addon('plugin.video.theoath').getAddonInfo('profile'))
				if '.addon(' in data:
					calls = Regex.extract(data = data, expression = '=\s*(.*?\.addon\(.*?\)\..*?\(.*?\)+)', all = True, group = None)
					if calls:
						for call in calls:
							call2 = Regex.extract(data = call, expression = '([^\(]*?\.addon\(.*?\))')
							if call2:
								call2 = call2.replace('"', '\\"')
								variable = Hash.random()
								data = data.replace(call, '%s if exec("try:\\n GAIA_%s = %s\\nexcept: GAIA_%s = None", globals(), locals()) or locals()["GAIA_%s"] else None' % (call, variable, call2, variable, variable))

				# Make sure the addon does not filter out unsupported links. Let Gaia do that.
				if file.endswith('source_utils.py'):
					# Make sure the last return statement in the try-except part is still left as is.
					data = Regex.replace(data = data, expression = 'def\s*is_host_valid.*?(?:except.*?)(return\s*False).*(?:$|def\s)', replacement = 'pass;return False', group = 1, all = True, flags = flags)

					# Replace remaining ones.
					data = Regex.replace(data = data, expression = 'def\s*is_host_valid.*?(?<!pass[;#])(return\s*False).*(?:$|def\s)', replacement = 'pass#', group = 1, all = True, flags = flags)

					# Replace the one that checks if the host is valid.
					data = Regex.replace(data = data, expression = 'def\s*is_host_valid.*?(return\s*any\(hosts\)).*(?:$|def\s)', replacement = 'return True', group = 1, all = True, flags = flags)

				# TheCrew - Ororo
				# \'Authorization\': \'Basic %s\' % base64.b64encode(\'%s:%s\' % (self.user, self.password).encode(\'utf-8\')),\n', "AttributeError: 'tuple' object has no attribute 'encode'\n"]
				if file.endswith('ororo.py'):
					data = data.replace('base64.b64encode(\'%s:%s\' % (self.user, self.password).encode(\'utf-8\'))', 'base64.b64encode((\'%s:%s\' % (self.user, self.password)).encode(\'utf-8\'))')

				# Fenom - cfscrape
				# SSLContext is read-only and cannot change its attributes/methods.
				# self.ssl_context.orig_wrap_socket = self.ssl_context.wrap_socket\n', "AttributeError: 'SSLContext' object has no attribute 'orig_wrap_socket'\n"]
				if 'cfscrape' in file and file.endswith('__init__.py'):
					data = data.replace('self.ssl_context.orig_wrap_socket = self.ssl_context.wrap_socket', '')
					data = data.replace('self.ssl_context.wrap_socket = self.wrap_socket', 'self.ssl_context.check_hostname = False')

				if not len(original) == len(data) or not original == data:
					File.writeNow(file, data)

		for directory in directories:
			self.instancesRename(path = directory, extra = extra)

	@classmethod
	def instancesInstalled(self):
		return Extension.installed(self.IdAddon)

	@classmethod
	def instancesPrepare(self, force = False):
		pathSource = System.path(self.IdAddon)
		if not pathSource: return None # Not installed.

		pathDestination = self.instancesPath()
		file = 'addon.xml'
		fileSource = File.joinPath(pathSource, file)
		fileDestination = File.joinPath(pathDestination, file)
		path = File.joinPath(pathDestination, self.Path)

		if force or not File.exists(fileDestination) or not Hash.fileSha1(fileSource) == Hash.fileSha1(fileDestination):
			File.copyDirectory(pathSource, pathDestination)

			# For some reason pkgutil.walk_packages fails with "SyntaxError" for directories named "lib".
			# Maybe this is because the main directory is also called "lib" and there is some name conflict.
			# Rename the directory and replace import statements.
			# Eg: OpenScrapers -> lib/openscrapers/sources_openscrapers/ru/lib/
			extra = []
			directories, _ = File.listDirectory(path = path, absolute = False)
			for directory in directories:
				pathDirectory = File.joinPath(path, directory)
				subs, _ = File.listDirectory(path = pathDirectory, absolute = False)
				for sub in subs:
					if sub == 'lib':
						extra.append(directory)
						File.renameDirectory(File.joinPath(pathDirectory, sub), File.joinPath(pathDirectory, 'libxyz'))
			extra = list(set(extra))

			# Some addons, like TheCrew, to not have a subdirectory in their "lib" directory that has its own name.
			# Eg: lib/resources/lib/...
			# Because the subdirectory is not unique, it can cause import clashes with other external provider addons.
			# Rename the directory to ensure it is unique.
			try:
				try: restructure = self.Restructure
				except: restructure = False
				if restructure:
					# Cannot move a directory into itself. So first move to a temp directory.
					pathFrom = File.joinPath(pathDestination, restructure[0])
					pathTo = File.joinPath(pathDestination, '_gaia_')
					File.move(pathFrom = pathFrom, pathTo = pathTo)
					pathFrom = pathTo
					pathTo = File.joinPath(pathDestination, restructure[1])
					File.move(pathFrom = pathFrom, pathTo = pathTo)
			except: self.logError()

			self.instancesRename(path = pathDestination, extra = extra)

		self.instancesInclude()

		return path

	@classmethod
	def instancesVersion(self):
		try: return System.version(self.IdAddon)
		except: return None

	@classmethod
	def instancesRank(self, providers):
		# Some addons have priorities starting at 1, but then there is a huge gap and the other priorities are 20 or higher.
		# Make it a simple order.
		ranks = set()
		for provider in providers:
			ranks.add(provider.rank())
		ranks = Tools.listSort(list(ranks))
		ranksBinary = len(ranks) <= 2
		for provider in providers:
			provider.rankSet(ranks.index(provider.rank()) + 1)

		rankMinimum = None
		rankMaximum = None
		for provider in providers:
			rank = provider.rank()
			if rankMinimum is None or (not rank is None and rank < rankMinimum): rankMinimum = rank
			if rankMaximum is None or (not rank is None and rank > rankMaximum): rankMaximum = rank
		if rankMinimum is None: rankMinimum = 0
		if rankMaximum is None: rankMaximum = 1

		for provider in providers:
			rank = provider.rank()

			if rank is None:
				rank = ProviderBase.RankDefault
			else:
				if rankMinimum == rankMaximum: rank = (ProviderBase.RankMaximum - ProviderBase.RankMinimum) / 2.0
				else: rank = Math.scale(value = rank, fromMinimum = rankMaximum, fromMaximum = rankMinimum, toMinimum = ProviderBase.RankMinimum, toMaximum = ProviderBase.RankMaximum) # Reverse min and max, since highest priority starts at 1.
				rank = int(Math.round(rank))
				if ranksBinary and rank == ProviderBase.RankMinimum: rank += 1 # If priorities is only 0 or 1.
			provider.rankSet(rank)

			performance = (rank / float(ProviderBase.RankLimit)) / 2.0
			performance = Math.round(ProviderBase.Performance2 + performance, places = 2)
			provider.performanceSet(performance = performance)

	@classmethod
	def instances(self, full = False):
		pass

	##############################################################################
	# INSTANCE
	##############################################################################

	@classmethod
	def instanceIgnore(self, id = None, scraper = None):
		try:
			if id and ('torrent' in id or 'orion' in id or id == 'library' or 'easynews' in id): return True

			# The only way to figure out if it is torrent, is to inspect the source code.
			if scraper:
				import inspect
				code = inspect.getsource(scraper.__class__)
				if Regex.match(data = code, expression = '(magnet:|[\'"](?:torrent|magnet)[\'"])'): return True
		except: self.logError()
		return False

	@classmethod
	def instanceDomain(self, link):
		return Tools.stringRemovePrefix(Networker.linkDomain(link = link, subdomain = True, topdomain = True, ip = True), 'www.')

	@classmethod
	def instanceInitialize(self, scraper, supportMovie, supportShow, id, name, version, rank, path = None, directory = None):
		try:
			provider = self(supportMovie = supportMovie, supportShow = supportShow)
			provider.instanceSet(scraper)
			provider.nameSet(name)
			provider.idGenerate(id)
			provider.labelGenerate(name.replace(' ', '').replace('-', '').replace('_', '').replace('.', ''))
			provider.addonVersionSet(version)
			provider.rankSet(rank)
			provider.instanceIdSet(id)
			try: provider.instanceFileSet(path)
			except: pass
			provider.instanceToggle() # Must be after the instance ID was set.

			# Check if it has a custom resolve() function.
			if path:
				data = File.readNow(path)
				resolver = Regex.match(data = data, expression = 'def\s+resolve\(')
				if resolver and Regex.match(data = data, expression = 'def\s+resolve\(.*?\n\s*return\s(?:u(?:rl)?|link|None|True|False)'): resolver = False
				provider.resolverSet(resolver)

			# Extract the languages.
			language = []
			try: language = scraper.language
			except:
				try: language = Regex.extract(data = directory, expression = '^(\w{2})(?:_.*$|$)')
				except: pass
			if not language: language = []
			if not Tools.isArray(language): language = [language]
			language = [Language.code(i) for i in language]
			language = [i for i in language if i]
			if not language: language = [Language.UniversalCode]
			provider.languageSet(language)

			# Extract the domains.
			# _base_link: Do not use base_link that is defined as a property (eg: KinoX), since this can make additional HTTP requests, slowing down the process.
			links = []
			processed = []

			link = scraper.base_link if Tools.hasVariable(scraper, 'base_link') else None
			if not link: link = scraper.base_new if Tools.hasVariable(scraper, 'base_new') else None
			domains = scraper.domains if Tools.hasVariable(scraper, 'domains') else None
			if not link and domains: link = 'http://' + domains[0]
			if link:
				link = link.strip(' ') # Do not strip /, beause scrapers often need then to work.
				links.append(link)
				processed.append(self.instanceDomain(link))
				if domains:
					scheme = Networker.linkScheme(link)
					if scheme: scheme += '://'
					else: scheme = 'http://'
					for domain in domains:
						new = domain.strip(' ')
						if not Networker.linkScheme(new): new = scheme + new
						if not new in links:
							newSub = self.instanceDomain(new)
							if not newSub in processed:
								links.append(new)
								processed.append(newSub)

			provider.linkSet(links, settings = False)

			return provider
		except:
			self.logError()
			return None

	def instanceParameterize(self):
		try:
			if self.mInstance:
				# Some providers (eg: KinoX) do not have a "base_link" attribute, but rather a "base_link" function and a "_base_link" attribute.
				# The "base_link" is dynamically generated from the "domains" list.
				link = self.link(settings = True)
				if Tools.hasVariable(self.mInstance, 'base_link'):
					if (not self.mInstance.base_link or self.mInstance.base_link.endswith('/')) and not link.endswith('/'): link += '/' # Some links require a slash at the end, since they are string-concatenated instead of properly URL-joined.
					self.mInstance.base_link = link
				elif Tools.hasVariable(self.mInstance, 'base_new'): # Eg: Fen-Rlsbb
					if (not self.mInstance.base_new or self.mInstance.base_new.endswith('/')) and not link.endswith('/'): link += '/' # Some links require a slash at the end, since they are string-concatenated instead of properly URL-joined.
					self.mInstance.base_new = link

				domains = self.linkDomains(subdomain = True, settings = True)
				if Tools.hasVariable(self.mInstance, 'domains'): self.mInstance.domains = domains
		except: self.logError()

	def instanceSet(self, instance):
		self.mInstance = instance

	def instanceObject(self, parameterize = True):
		pass

	def instanceEnabled(self):
		pass

	def instanceId(self):
		return self.mData['instance']['id']

	def instanceIdSet(self, id):
		self.mData['instance']['id'] = id

	def instanceToggle(self):
		enabled = self.instanceEnabled()
		self.enableDefault(enabled)
		self.enableSettingsProvider(enabled)

	##############################################################################
	# SEARCH
	##############################################################################

	def searchProcess(self, items):
		lock = None
		try:
			if items:
				chunks = self.priorityChunks(items)
				for chunk in chunks:
					lock = self.priorityStart(lock = lock)
					for item in chunk:
						if self.stopped(): break

						try:
							try: link = item['url'].replace('http:http:', 'http:').replace('https:https:', 'https:').replace('http:https:', 'https:').replace('https:http:', 'http:') # Some of the links start with a double http.
							except: continue

							# External providers (eg: "Get Out"), sometimes has weird characters in the URL.
							# Ignore the links that have non-printable ASCII or UTF8 characters.
							#try: link = link.decode('utf-8')
							#except: continue
							try:
								try: link = bytes(link, 'utf-8') # If link is already a str, then calling str(link, 'utf-8') throws an exception. Convert too bytes first.
								except: pass
								link = str(link, 'utf-8')
							except:
								try: self.log('Link has encoding errors: ' + link)
								except: self.log('Link has encoding errors.')
								continue

							# Some links do not have a protocol.
							if link.startswith('//'): link = 'http:' + link

							# Some external addons return an addon URL instead of the actual URL.
							if not Networker.linkIs(link, magnet = True):
								try: link = Networker.linkParameters(link)['url']
								except: continue

							# NB: Do not check for gcloud, gdrive, etc, since these are separate website not owned by Google.
							source = Converter.unicode(item['source']).lower().replace(' ', '')
							if 'torrent' in source: continue
							if Networker.linkIsIp(source): source = 'Anonymous'
							elif Regex.match(data = source, expression = '(google.*?(vid|link))'): source = 'GoogleVideo'
							elif Regex.match(data = source, expression = '(google.*?(cloud|user|content))'): source = 'GoogleCloud'
							elif Regex.match(data = source, expression = '(google.*?doc)'): source = 'GoogleDocs'
							elif Regex.match(data = source, expression = '(google.*?drive)'): source = 'GoogleDrive'
							elif '.' in source: source = Networker.linkDomain(link = source, subdomain = False, topdomain = True, ip = True)

							try: videoQuality = item['quality']
							except: videoQuality = None

							try: audioLanguage = item['language']
							except: audioLanguage = None

							try: fileExtra = item['info']
							except: fileExtra = None

							try: fileSize = item['size'] * 1073741824
							except: fileSize = None

							try: accessDirect = item['direct']
							except: accessDirect = None

							try: accessMember = item['memberonly']
							except: accessMember = None

							# Do not just set the source as sourceHoster, since eg GVideo has files pointing to other hosters like YouTube.
							sourcePublisher = None
							sourceHoster = None
							if not source == 'direct':
								domain = Stream.sourceHosterExtract(link)
								if not self.linkDomain() == domain: sourceHoster = source
								elif not domain == source: sourcePublisher = source

							stream = self.resultStream(
								validate = Stream.ValidateLenient,
								validateSize = False,
								validatePeers = False,

								link = link,

								videoQuality = videoQuality,

								fileExtra = fileExtra,
								fileSize = fileSize,

								sourceType = Stream.SourceTypeHoster,
								sourcePublisher = sourcePublisher,
								sourceHoster = sourceHoster,

								accessDirect = accessDirect,
								accessMember = accessMember,

								thresholdSize = self.customSize(),
								thresholdTime = self.customTime(),
								thresholdPeers = self.customPeers(),
								thresholdSeeds = self.customSeeds(),
								thresholdLeeches = self.customLeeches(),
							)
							if stream:
								if not stream.audioLanguage(): stream.audioLanguageSet(audioLanguage)
								self.resultAdd(stream)
						except: self.logError(self.addonName() + '-' + self.name())
				self.priorityEnd(lock = lock)
		except: self.logError(self.addonName() + '-' + self.name())
		finally: self.priorityEnd(lock = lock)

	##############################################################################
	# RESOLVE
	##############################################################################

	def resolve(self, link, renew = False):
		self.clear()
		try: return self.instanceObject().resolve(link)
		except: return link


class ProviderExternalUnstructured(ProviderExternal):

	def __init__(self, **kwargs):
		ProviderExternal.__init__(self, **kwargs)
		if not 'file' in self.mData['instance']: self.mData['instance']['file'] = None

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media = None, niche = None, titles = None, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		from lib.providers.core.manager import Manager
		try:
			url = None
			instance = self.instanceObject()
			if instance:
				titles = Tools.copy(titles) # Make a copy, because the list is sometimes edited in the scraper.
				if cacheLoad: url = Manager.linksRetrieve(provider = self, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode, time = self.cacheTime())
				if not url:
					titleMain = titles['main']
					titleLocal = titles['local'] if 'local' in titles else titleMain
					titleEpisode = titles['episode'] if 'episode' in titles else titleMain
					titleAliases = []
					if 'alias' in titles:
						for c, title in titles['alias'].items():
							titleAliases.extend([{'country' : c, 'title' : t} for t in title])

					date = None
					if time: date = Time.format(timestamp = time, format = Time.FormatDate)

					year = None
					try: year = years['common']
					except: self.logError()

					functionShow = Tools.hasFunction(instance, 'tvshow')
					functionEpisode = Tools.hasFunction(instance, 'episode')
					functionMovie = Tools.hasFunction(instance, 'movie')

					if functionShow or functionMovie:
						if Media.isSerie(media):
							if functionShow and functionEpisode:
								url = instance.tvshow(idImdb, idTvdb, titleMain, titleLocal, titleAliases, str(year))
								self.statisticsUpdateSearch(request = True)
								url = instance.episode(url, idImdb, idTvdb, titleEpisode, date, str(numberSeason), str(numberEpisode))
								self.statisticsUpdateSearch(request = True)
						else:
							if functionMovie:
								try:
									url = instance.movie(idImdb, titleMain, titleLocal, titleAliases, str(year))
								except Exception as error:
									if Regex.match(data = str(error).lower(), expression = 'takes.*\s5\s.*argument'):
										url = instance.movie(idImdb, titleMain, titleAliases, str(year))
								self.statisticsUpdateSearch(request = True)
					else: # New FenomScrapers pass the dictionary directly to sources().
						if Media.isSerie(media):
							url = {'imdb': idImdb, 'tvdb': idTvdb, 'tvshowtitle': titleMain, 'aliases': titleAliases, 'year': str(year), 'title': titleEpisode, 'premiered': date, 'season': str(numberSeason), 'episode': str(numberEpisode)}
						else:
							url = {'imdb': idImdb, 'title': titleMain, 'aliases': titleAliases, 'year': str(year)}

					if cacheSave and url: Manager.linksInsert(data = url, provider = self, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, numberSeason = numberSeason, numberEpisode = numberEpisode)

				if url:
					count = len(Tools.getParameters(instance.sources))

					# Don't use named parameters due to CMovies.
					# Fenom does not have the hostersPremium parameter anymore.
					if count == 1: items = instance.sources(url)
					elif count == 2: items = instance.sources(url, hostersAll)
					elif count >= 3: items = instance.sources(url, hostersAll, hostersPremium)

					self.statisticsUpdateSearch(request = True, page = True)
					self.searchProcess(items = items)
		except:
			self.logError(message = self.addonName() + '-' + self.name(), developer = True)

	##############################################################################
	# INSTANCE
	##############################################################################

	def instanceFile(self):
		return self.mData['instance']['file']

	def instanceFileSet(self, path):
		self.mData['instance']['file'] = path

	def instanceObject(self, parameterize = True):
		try:
			if self.mInstance is None:
				# NB: Do not use "imp" anymore, since it deprecated in Python 3.13+.
				#import imp

				self.instancesInclude()

				#self.mInstance = imp.load_source(self.instanceId(), self.instanceFile()).source()
				self.mInstance = Importer.moduleFile(id = self.instanceId(), path = self.instanceFile()).source()

				if parameterize: self.instanceParameterize()
		except: self.logError()
		return self.mInstance

	def instanceEnabled(self):
		if not self.IdAddon in ProviderExternal.Settings:
			System.addon(self.IdAddon).setSetting('_%s_' % System.name().lower(), '') # Forces Kodi to generate the settings profile file if it does not already exist.
			ProviderExternal.Settings[self.IdAddon] = File.readNow(File.joinPath(System.profile(self.IdAddon), 'settings.xml'))
		data = ProviderExternal.Settings[self.IdAddon]
		if not data: return True # Some addons (eg GlobalScrapers) do not have a settings file. Enable by default.
		return Converter.boolean(Settings.raw('provider.' + self.instanceId(), parameter = Settings.ParameterValue, data = data))

	##############################################################################
	# INSTANCES
	##############################################################################

	@classmethod
	def instances(self, full = False):
		import pkgutil

		# NB: Do not use "imp" anymore, since it deprecated in Python 3.13+.
		#import imp

		items = []
		providers = []
		if self.instancesInstalled():
			try:
				version = self.instancesVersion()
				sources = self.instancesPrepare()

				if sources:

					# Sometimes there is a __init__.py file missing in the directories.
					# This file is required for a valid Python module and will cause walk_packages to fail if absence.
					directories, files = File.listDirectory(sources, absolute = True)
					for directory in directories:
						path = File.joinPath(directory, '__init__.py')
						if not File.exists(path): File.create(path)

					try:
						path1 = sources
						for _, name1, package1 in pkgutil.walk_packages([path1]):
							if not 'torrent' in name1.lower() and not name1.lower().endswith('_tor'): # _tor: TheCrew.
								ids = []
								path2 = File.joinPath(sources, name1)
								directory = name1 if package1 else None

								# If the scraper does not have a second level of directories, like GlobalScrapers.
								for _, name2, package2 in pkgutil.walk_packages([path2]):
									if not package2: ids.append(name2)
								if not package1 and len(ids) == 0:
									path2 = path1
									ids = [name1]

								for id in ids:
									item = {'id' : id}
									try:
										if self.instanceIgnore(id = id):
											item['ignore'] = True
											continue

										item['name'] = name = id.replace(' ', '').replace('-', '').replace('_', '').replace('.', '').capitalize()
										item['path'] = path = File.joinPath(path2, id + '.py')

										#scraper = imp.load_source(id, path).source()
										scraper = Importer.moduleFile(id = id, path = path).source()

										if self.instanceIgnore(scraper = scraper):
											item['ignore'] = True
											continue

										supportMovie = Tools.hasFunction(scraper, 'movie')
										supportShow = Tools.hasFunction(scraper, 'episode')

										try: rank = scraper.priority
										except: rank = None

										provider = self.instanceInitialize(scraper = scraper, supportMovie = supportMovie, supportShow = supportShow, id = id, name = name, version = version, rank = rank, path = path, directory = directory)
										item['instance'] = provider
										if provider: providers.append(provider)
										else: item['error'] = 'initialize'
									except Exception as error:
										item['error'] = str(error)
										self.logError(message = self.Name + '-' + id, developer = True)
									item['valid'] = bool('instance' in item and ['instance'])
									items.append(item)
					except: self.logError()

					self.instancesRank(providers = providers)

			except: self.logError()

		if full: return items
		else: return providers


class ProviderExternalStructured(ProviderExternal):

	def __init__(self, **kwargs):
		ProviderExternal.__init__(self, **kwargs)

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media = None, niche = None, titles = None, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		try:
			from lib import debrid
			debridHas = debrid.Debrid.enabled()
			titleMain = titles['main']

			scraper = self.instanceObject()
			if scraper:
				year = None
				try: year = years['common']
				except: self.logError()

				if Media.isSerie(media): items = scraper.scrape_episode(title = titleMain, year = year, show_year = year, season = numberSeason, episode = numberEpisode, imdb = idImdb, tvdb = idTvdb, debrid = debridHas)
				else: items = scraper.scrape_movie(title = titleMain, year = str(year), imdb = idImdb, debrid = debridHas)
				self.statisticsUpdateSearch(request = True, page = True)

				self.searchProcess(items = items)
		except:
			self.logError(message = self.addonName() + '-' + self.name(), developer = True)

	##############################################################################
	# INSTANCE
	##############################################################################

	def instanceEnabled(self):
		return self.instanceObject()._is_enabled()

	def instanceObject(self, parameterize = True):
		try:
			if self.mInstance is None:
				result = self.instancesScrapers(name = self.name())
				if result:
					self.mInstance = result[0]()
					if parameterize: self.instanceParameterize()
		except: self.logError()
		return self.mInstance

	##############################################################################
	# INSTANCES
	##############################################################################

	@classmethod
	def instancesScrapers(self, name = None):
		try:
			import importlib
			return importlib.import_module(self.Module).relevant_scrapers(names_list = name, include_disabled = True, exclude = None)
		except:
			self.logError()
			return []

	@classmethod
	def instances(self, full = False):
		items = []
		providers = []

		if self.instancesInstalled():
			try:
				version = self.instancesVersion()
				scrapers = self.instancesScrapers()

				for scraper in scrapers:
					item = {}
					try:
						item['name'] = name = scraper.name
						item['id'] = id = scraper.name.replace(' ', '').lower()
						if self.instanceIgnore(id = id):
							item['ignore'] = True
							continue

						scraper = scraper()
						if self.instanceIgnore(scraper = scraper):
							item['ignore'] = True
							continue

						supportMovie = Tools.hasFunction(scraper, 'scrape_movie')
						supportShow = Tools.hasFunction(scraper, 'scrape_episode')

						try: rank = scraper.priority
						except: rank = None

						provider = self.instanceInitialize(scraper = scraper, supportMovie = supportMovie, supportShow = supportShow, id = id, name = name, version = version, rank = rank)
						item['instance'] = provider
						if provider: providers.append(provider)
						else: item['error'] = 'initialize'
					except Exception as error:
						item['error'] = str(error)
						self.logError(message = self.Name + '-' + id, developer = True)
					item['valid'] = bool('instance' in item and ['instance'])
					items.append(item)

				self.instancesRank(providers = providers)

			except: self.logError()

		if full: return items
		else: return providers
