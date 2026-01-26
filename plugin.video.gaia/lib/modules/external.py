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

from importlib import import_module, util as import_util
from lib.modules.concurrency import Lock

class Importer(object):

	InternalDirectory = 'Internals'
	InternalRefresh = 0.01 # 1%

	Lock = Lock()
	Modules = {}

	# Exceptions to not print to log.
	Exceptions = [
		# On AppleTV: py-cpuinfo currently only works on X86 and some ARM/PPC/S390X/MIPS CPUs.
		'cpuinfo currently only works on',
	]

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		Importer.Modules = {}

	##############################################################################
	# UPDATE
	##############################################################################

	@classmethod
	def update(self, force = False):
		from lib.modules.tools import Math, Logger, System, File
		try:
			if force is True or Math.randomProbability(force if force else Importer.InternalRefresh): # 1% of the time.
				# Occasionally refresh the local TLD cache with new/changed TLDs.
				#self.moduleTldExtract().update(True)

				# Occasionally remove the JS2PY temp directory, to accomodate code updates.
				# Remove: xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile')), 'Internals', 'js2py')

				# Instead of updating/deleting for each external library, just delete the entire directory, which will force all externals to refresh in any case.
				# Plus this might also solve some other issues, like subdirs/subfiles not being able to be deleted, due to some permission issues on the parent dir.
				path = File.joinPath(System.profile(), Importer.InternalDirectory)
				File.deleteDirectory(path)
				return True
			else:
				return None
		except: Logger.error()
		return False

	###################################################################
	# INTERNAL
	###################################################################

	@classmethod
	def module(self, module, submodule = None, backupModule = None, backupSubmodule = None, error = True):
		id = [module, submodule, backupModule, backupModule]
		id = '_'.join([i for i in id if i])

		try:
			if not id in Importer.Modules:
				Importer.Lock.acquire()
				if not id in Importer.Modules:
					try:
						package = import_module(module)
						if submodule: package = getattr(package, submodule)
					except Exception as exception:
						if backupModule:
							package = import_module(backupModule)
							if backupSubmodule: package = getattr(package, backupSubmodule)
						else:
							raise exception
					if package: Importer.Modules[id] = package
				try: Importer.Lock.release()
				except: pass
		except Exception as exception:
			if error is True:
				from lib.modules.tools import Logger

				exclude = False
				message = str(exception)
				for i in Importer.Exceptions:
					if i in message:
						exclude = True
						break

				if not exclude: Logger.error()
			elif not error is False and not not error is None:
				try: error(error = exception)
				except: error()
		finally:
			try: Importer.Lock.release()
			except: pass

		if id in Importer.Modules: return Importer.Modules[id]
		else: return None

	@classmethod
	def moduleVersion(self, module):
		result = None
		try:
			from lib.modules.tools import File, Tools, Regex

			if Tools.isString(module): module = self.module(module = module)
			name = module.__name__
			if name.startswith('externals.'): name = name.split('.')[1]
			pkg = True

			if not result:
				try:
					result = module.__version__
				except: pass

			if not result:
				try:
					from importlib_metadata import distribution
					result = distribution(name).version
				except: pass

			# Python >= 3.8
			if not result:
				try:
					from importlib.metadata import version
					result = version(name)
				except Exception as e:
					# pkg_resources is deprecated since Python 3.12, logging this:
					#	UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81. from pkg_resources import get_distribution
					# If importlib.metadata.version throws a PackageNotFoundError exception, we know the module works, there is just no version info available in the module.
					# Eg: uJson has no version info, since it only has the compiled library, but no version info in any of the Python file.
					# In such a case, do not try pkg_resources as well, since it will also not work just only show the warning.
					try:
						if type(e).__name__ == 'PackageNotFoundError': pkg = False
					except: pass

			# Python < 3.8
			if not result and pkg:
				try:
					from pkg_resources import get_distribution
					result = get_distribution(name).version
				except: pass

			if not result:
				try:
					path = module.__path__
					if Tools.isArray(path): path = path[0]
					path = str(path)
					library = Loader.moduleLibraries(path = path)
					if library:
						path = File.joinPath(path, library)
						with open(path, 'rb') as file:
							data = file.read()
							value = Regex.extract(data = data, expression = b'(.{0,20}__version__.{0,20})', flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines)
							if value:
								value = str(value)
								value = Regex.remove(data = value, expression = r'\\\\x[0-9a-f]{2}', all = True)
								value = Regex.remove(data = value, expression = r'\\x[0-9a-f]{2}', all = True)
								value = Regex.extract(data = value, expression = r'(\d+\.\d+\.\d+)')
								if value: result = value
				except: pass

		except: pass
		return result

	@classmethod
	def moduleLabel(self, module, binary = False, extra = None):
		try:
			from lib.modules.tools import Tools

			moduleLibrary = None
			moduleName = None
			if Tools.isString(module):
				moduleLibrary = self.module(module = module)
				moduleName = module
			elif module:
				moduleLibrary = module
				moduleName = module.__name__

			type = None
			details = []

			if '.' in moduleName:
				type = 'External'
				if binary:
					module = moduleName.split('.')

					system = module[-1]
					try: system = Loader.Labels[system]
					except: system = [system.upper()]

					python = module[-2].replace('_', '.')

					details = system + ['Python ' + python]
			else:
				type = Loader.ModuleNative.capitalize() if moduleName else Loader.ModuleUnknown.capitalize()

			if not details and moduleName:
				from lib.modules.tools import Platform, Regex
				platform = Platform.detect(full = False)

				details = []
				try: details.append(platform['system']['name'])
				except: pass
				try: details.append('64bit' if platform['architecture']['bits'] == Platform.Bits64 else '32bit')
				except: pass
				try: details.append(platform['architecture']['type'].replace('arm', 'ARM'))
				except: pass
				try: details.append('Python ' + Regex.extract(data = platform['python']['version'], expression = r'(\d+\.\d+)'))
				except: pass

			version = Importer.moduleVersion(moduleLibrary)
			if version: details.insert(0, version)

			if extra:
				if Tools.isArray(extra): details.extend(extra)
				else: details.append(extra)

			if details: return '%s (%s)' % (type, ' - '.join(details))
			else: return str(type)
		except: # Module not detected.
			return Loader.ModuleUnknown.capitalize()

	@classmethod
	def moduleFile(self, id, path):
		try:
			import sys
			file = import_util.spec_from_file_location(id, path)
			module = import_util.module_from_spec(file)
			sys.modules[id] = module
			file.loader.exec_module(module)
			return module
		except:
			from lib.modules.tools import Logger
			Logger.error()
		return None

	###################################################################
	# BINARIES
	###################################################################

	@classmethod
	def modulePsutil(self):
		return Psutil().module()

	@classmethod
	def moduleUjson(self):
		return Ujson().module()

	###################################################################
	# TEXT
	###################################################################

	@classmethod
	def moduleChardet(self, error = True):
		return self.module(module = 'externals.chardet', error = error)

	@classmethod
	def moduleUnidecode(self, error = True):
		return self.module(module = 'externals.unidecode', submodule = 'unidecode', error = error)

	###################################################################
	# DICTIONARY
	###################################################################

	@classmethod
	def moduleCaseInsensitiveDict(self, error = True):
		return self.module(module = 'externals.requests.structures', submodule = 'CaseInsensitiveDict', error = error)

	@classmethod
	def moduleOrderedDict(self, error = True):
		return self.module(module = 'collections', submodule = 'OrderedDict', backupModule = 'externals.ordereddict.ordereddict', backupSubmodule = 'OrderedDict', error = error)

	###################################################################
	# TIME
	###################################################################

	@classmethod
	def moduleTimeParse(self, error = True):
		return self.module(module = 'externals.pytimeparse.timeparse', error = error)

	@classmethod
	def modulePytz(self, error = True):
		return self.module(module = 'externals.pytz', error = error)

	###################################################################
	# NETWORK
	###################################################################

	@classmethod
	def moduleTldExtract(self, error = True):
		# Check providers/core/base.py -> concurrencyPrepare() for a full description of why we do this.
		return self.module(module = 'externals.tldextract', error = error)

	@classmethod
	def moduleRequests(self, error = True):
		return self.module(module = 'externals.requests', error = error)

	@classmethod
	def moduleSession(self, error = True):
		return self.module(module = 'externals.requests', submodule = 'Session', error = error)

	@classmethod
	def moduleHttpAdapter(self, error = True):
		return self.module(module = 'externals.requests.adapters', submodule = 'HTTPAdapter', error = error)

	@classmethod
	def moduleUrllib3(self, error = True):
		return self.module(module = 'externals.urllib3', error = error)

	@classmethod
	def moduleGeoNamesCache(self, error = True):
		return self.module(module = 'externals.geonamescache', submodule = 'GeonamesCache', error = error)

	###################################################################
	# CLOUDFLARE
	###################################################################

	@classmethod
	def moduleCloudflare(self, error = True, label = False):
		from lib.modules.cloudflare import Cloudflare
		module = Cloudflare.settingsModule()
		if module == Cloudflare.ModuleCfscrape:
			return self.moduleCfScrape(error = error, label = label)
		elif module == Cloudflare.ModuleCloudscraper:
			version = Cloudflare.settingsVersion()
			return self.moduleCloudScraper(error = error, label = label, new = version == Cloudflare.VersionLatest)
		else:
			return None

	@classmethod
	def moduleCloudScraper(self, error = True, label = False, new = False):
		module = self.module(module = 'externals.cloudscraper.' + ('new' if new else 'old'), error = error)
		if label:
			from lib.modules.cloudflare import Cloudflare
			return self.moduleLabel(module = module, extra = Cloudflare._engine(name = True))
		else:
			return module

	@classmethod
	def moduleCfScrape(self, error = True, label = False):
		module = self.module(module = 'externals.cfscrape', error = error)
		if label: return self.moduleLabel(module = module, extra = 'CfScrape')
		else: return module

	###################################################################
	# TORRENT
	###################################################################

	@classmethod
	def moduleTorrentTrackerScraper(self, error = True):
		return self.module(module = 'externals.torrenttrackerscraper.scraper', error = error)

	@classmethod
	def moduleBencode(self, error = True):
		return self.module(module = 'externals.bencode', error = error)

	###################################################################
	# BEAUTIFULSOUP
	###################################################################

	@classmethod
	def moduleBeautifulSoup(self, error = True):
		return self.module(module = 'externals.beautifulsoup', submodule = 'BeautifulSoup', error = error)

	@classmethod
	def moduleBeautifulStrainer(self, error = True):
		return self.module(module = 'externals.beautifulsoup', submodule = 'SoupStrainer', error = error)

	@classmethod
	def moduleBeautifulTag(self, error = True):
		return self.module(module = 'externals.beautifulsoup.element', submodule = 'Tag', error = error)

	@classmethod
	def moduleBeautifulNavigable(self, error = True):
		return self.module(module = 'externals.beautifulsoup.element', submodule = 'NavigableString', error = error)

	###################################################################
	# JAVASCRIPT
	###################################################################

	# Update (2025-06):
	# When trying to import the old JS2PY v0.71 module into Python 3.11, the following error is thrown:
	#	script.gaia.externals/lib/externals/js2py/utils/injector.py", line 220, in check\n    raise RuntimeError(\n', 'RuntimeError: Your python version made changes to the bytecode\n']
	# This is discussed here:
	#	https://github.com/PiotrDabkowski/Js2Py/issues/282
	# Pretty sure the old JS2PY worked fine before, even in Python 3.11. Not sure why this error suddenly starts showing.
	# The error is gone when using the "new" JS2PY v 0.74.
	# If it is indeed a bytecode compatibility issue between Python 3.8 and 3.11, try importing the new module first, and if it fails, import the old module.

	@classmethod
	def moduleJs2Py(self, error = True):
		return self.module(module = 'externals.js2py.new', backupModule = 'externals.js2py.old', error = error)

	@classmethod
	def moduleJs2PyEval1(self, error = True):
		return self.module(module = 'externals.js2py.new', submodule = 'eval_js', backupModule = 'externals.js2py.old', backupSubmodule = 'eval_js', error = error)

	@classmethod
	def moduleJs2PyEval2(self, error = True):
		return self.module(module = 'externals.js2py.new', submodule = 'EvalJs', backupModule = 'externals.js2py.old', backupSubmodule = 'EvalJs', error = error)

	###################################################################
	# TEXTDISTANCE
	###################################################################

	@classmethod
	def moduleTextDistLcs(self, error = True):
		return self.module(module = 'externals.pytextdist.edit_distance', submodule = 'lcs_similarity', error = error)

	@classmethod
	def moduleTextDistLevenshtein(self, error = True):
		return self.module(module = 'externals.pytextdist.edit_distance', submodule = 'levenshtein_similarity', error = error)

	@classmethod
	def moduleTextDistDamerauLevenshtein(self, error = True):
		return self.module(module = 'externals.pytextdist.edit_distance', submodule = 'damerau_levenshtein_similarity', error = error)

	@classmethod
	def moduleTextDistHamming(self, error = True):
		return self.module(module = 'externals.pytextdist.edit_distance', submodule = 'hamming_similarity', error = error)

	@classmethod
	def moduleTextDistJaro(self, error = True):
		return self.module(module = 'externals.pytextdist.edit_distance', submodule = 'jaro_similarity', error = error)

	@classmethod
	def moduleTextDistJaroWinkler(self, error = True):
		return self.module(module = 'externals.pytextdist.edit_distance', submodule = 'jaro_winkler_similarity', error = error)

	@classmethod
	def moduleTextDistCosine(self, error = True):
		return self.module(module = 'externals.pytextdist.vector_similarity', submodule = 'cosine_similarity', error = error)

	@classmethod
	def moduleTextDistJaccard(self, error = True):
		return self.module(module = 'externals.pytextdist.vector_similarity', submodule = 'jaccard_similarity', error = error)

	@classmethod
	def moduleTextDistSorensen(self, error = True):
		return self.module(module = 'externals.pytextdist.vector_similarity', submodule = 'sorensen_dice_similarity', error = error)

	@classmethod
	def moduleTextDistQgram(self, error = True):
		return self.module(module = 'externals.pytextdist.vector_similarity', submodule = 'qgram_similarity', error = error)

	###################################################################
	# HACHOIR
	###################################################################

	@classmethod
	def moduleHachoirParser(self, error = True):
		return self.module(module = 'externals.hachoir.parser', submodule = 'createParser', error = error)

	@classmethod
	def moduleHachoirMetadata(self, error = True):
		return self.module(module = 'externals.hachoir.metadata', submodule = 'extractMetadata', error = error)

	###################################################################
	# QRCODE
	###################################################################

	@classmethod
	def moduleQrCode(self, error = True):
		return self.module(module = 'externals.qrcode', error = error)

	@classmethod
	def moduleQrPymaging(self, error = True):
		return self.module(module = 'externals.qrcode.image.pure', submodule = 'PymagingImage', error = error)

	@classmethod
	def moduleQrStyledPil(self, error = True):
		return self.module(module = 'externals.qrcode.image.styledpil', submodule = 'StyledPilImage', error = error)

	@classmethod
	def moduleQrDrawers(self, error = True):
		return self.module(module = 'externals.qrcode.image.styles.moduledrawers', error = error)

	@classmethod
	def moduleQrGradiant(self, error = True):
		return self.module(module = 'externals.qrcode.image.styles.colormasks', submodule = 'RadialGradiantColorMask', error = error)

	@classmethod
	def moduleQrFill(self, error = True):
		return self.module(module = 'externals.qrcode.image.styles.colormasks', submodule = 'SolidFillColorMask', error = error)

	@classmethod
	def moduleQrImage(self, error = True, label = False):
		module = self.module(module = 'PIL', error = error)
		extra = 'Pillow'
		if not module:
			module = self.module(module = 'Image', error = error)
			extra = 'Image'
		if label: return self.moduleLabel(module = module, extra = extra)
		else: return module

	###################################################################
	# CLIPBOARD
	###################################################################

	@classmethod
	def modulePyperClip(self, error = True):
		return self.module(module = 'externals.pyperclip', error = error)

	###################################################################
	# SPEEDTEST
	###################################################################

	@classmethod
	def moduleSpeedTest(self, error = True):
		return self.module(module = 'externals.speedtest.speedtest', submodule = 'Speedtest', error = error)

	###################################################################
	# HARDWARE
	###################################################################

	@classmethod
	def moduleCpuInfo(self, error = True):
		return self.module(module = 'externals.cpuinfo.cpuinfo', error = error)

	###################################################################
	# BARD
	###################################################################

	@classmethod
	def moduleBard(self, error = True):
		return self.module(module = 'externals.bardapi', submodule = 'Bard', error = error)

	@classmethod
	def moduleBardConstants(self, error = True):
		return self.module(module = 'externals.bardapi.constants', error = error)


class Loader(object):

	ModuleNone		= 'none'	# Neither the native not the modules from "externals" could be imported.
	ModuleNative	= 'native'	# The native module.
	ModuleUnknown	= 'unknown'	# The import process somehow failed.

	SystemWindows	= 'win'
	SystemLinux		= 'lin'
	SystemMac		= 'mac'
	SystemArm		= 'arm'

	Adapted			= '__gaia__'
	Python			= ('.py',)
	Library			= ('.pyd', '.so', '.dll')
	Property		= 'GaiaExternal'
	Modules			= {}
	Lock			= Lock()

	Labels			= {
		'win64'		: ['Windows', '64bit', 'x86'],
		'win32'		: ['Windows', '32bit', 'x86'],
		'winarm'	: ['Windows', '64bit', 'ARM'],

		'mac64'		: ['Mac', '64bit', 'x86'],
		'mac32'		: ['Mac', '32bit', 'x86'],
		'macarm'	: ['Mac', '64bit', 'ARM'],

		'lin64'		: ['Linux', '64bit', 'x86'],
		'lin32'		: ['Linux', '32bit', 'x86'],

		'arm64'		: ['Linux', '64bit', 'ARM'],
		'armv6'		: ['Linux', '64bit', 'ARMv6'],
		'armv7'		: ['Linux', '32bit', 'ARMv7'],
		'armv8'		: ['Linux', '64bit', 'ARMv8'],
		'armv9'		: ['Linux', '64bit', 'ARMv9'],
		'armhf'		: ['Linux', '32bit', 'ARMhf'],
		'armel'		: ['Linux', '32bit', 'ARMel'],
	}

	###################################################################
	# CONSTRUCTOR
	###################################################################

	def __init__(self, id = None):
	 	self.mId = id

	@classmethod
	def instance(self, module):
		if module:
			module = module.lower()
			if module == Psutil.Id: return Psutil()
			elif module == Ujson.Id: return Ujson()
		return None

	@classmethod
	def clear(self):
		Psutil().modulePropertyClear()
		Ujson().modulePropertyClear()

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		self.clear()
		Loader.Modules = {}

	###################################################################
	# MODULE
	###################################################################

	def module(self):
		if not self.moduleId() in Loader.Modules:
			Loader.Lock.acquire()
			if not self.moduleId() in Loader.Modules:
				instance = None
				try:
					module = self.moduleProperty()
					if module:
						if module == Loader.ModuleNative:
							instance = Importer.module(module = self.moduleId())
						elif '.' in module:
							instance = Importer.module(module = module)
					else:
						instance = self.moduleLoad()
				except:
					from lib.modules.tools import Logger
					Logger.error()
				Loader.Modules[self.moduleId()] = instance
			Loader.Lock.release()
		try: return Loader.Modules[self.moduleId()]
		except: return None

	def moduleId(self):
		return self.mId

	def moduleProperty(self):
		from lib.modules.tools import System
		return System.windowPropertyGet(self.modulePropertyId())

	def modulePropertySet(self, value):
		from lib.modules.tools import System
		return System.windowPropertySet(self.modulePropertyId(), value)

	def modulePropertyClear(self):
		from lib.modules.tools import System
		return System.windowPropertyClear(self.modulePropertyId())

	def modulePropertyId(self):
		return Loader.Property + self.moduleId().capitalize()

	def moduleLabel(self):
		return Importer.moduleLabel(module = self.module(), binary = True)

	def moduleTest(self, module):
		return True

	@classmethod
	def modulePython(self, path, absolute = False):
		from lib.modules.tools import File
		_, files = File.listDirectory(path = path, absolute = absolute)
		try: return [i for i in files if i.endswith(Loader.Python)]
		except: return []

	@classmethod
	def moduleLibraries(self, path, absolute = False):
		from lib.modules.tools import File
		_, files = File.listDirectory(path = path, absolute = absolute)
		try: return [i for i in files if i.endswith(Loader.Library)]
		except: return []

	def moduleAdapt(self, path, system, versionCurrent, versionOriginal):
		from lib.modules.tools import File

		result = []

		pathAdapted = File.joinPath(path, Loader.Adapted, versionOriginal)
		File.makeDirectory(pathAdapted)

		adapted = self.moduleAdaptVersion(system = system, versionCurrent = versionCurrent, versionOriginal = versionOriginal, pathOriginal = path, pathAdapted = pathAdapted)
		if adapted: result.append(adapted)

		adapted = self.moduleAdaptWindows(system = system, versionCurrent = versionCurrent, versionOriginal = versionOriginal, pathOriginal = path, pathAdapted = pathAdapted)
		if adapted: result.append(adapted)

		return result

	def moduleAdaptVersion(self, system, versionCurrent, versionOriginal, pathOriginal, pathAdapted):
		'''
			In many cases, and older a newer Python version can be used.
			Python will not loaded the .pyd if the file name has a wrong version.
			So copy them over and rename the .pyd.
		'''
		try:
			if not versionCurrent == versionOriginal:
				from lib.modules.tools import File, Regex

				replacement = versionCurrent.replace('_', '')

				pathFrom = File.joinPath(pathOriginal, versionOriginal, system)
				pathTo = File.joinPath(pathAdapted, system)
				if not File.existsDirectory(pathTo):
					File.copyDirectory(pathFrom = pathFrom, pathTo = pathTo, overwrite = False)

					libraries = self.moduleLibraries(path = pathTo)
					for library in libraries:
						libraryFrom = File.joinPath(pathTo, library)
						libraryTo = File.joinPath(pathTo, Regex.replace(data = library, expression = r'\.(?:cpython|cp)\-?(\d+[a-z]?)\-', replacement = replacement, group = 1))
						File.move(pathFrom = libraryFrom, pathTo = libraryTo, replace = False)

				if File.existsDirectory(pathTo) and self.moduleLibraries(path = pathTo):
					self.moduleAdaptImport(path = pathTo)
					return system
		except:
			from lib.modules.tools import Logger
			Logger.error()
		return None

	def moduleAdaptWindows(self, system, versionCurrent, versionOriginal, pathOriginal, pathAdapted):
		'''
			Kodi under Windows has a problem with the Python version.
			Kodi ships with the Python library as "python3.8.dll".
			However, the standard Python naming convention ignores the dot between the version and will rather use "python38.dll".
			Precompiled .pyd libraries are all linked to "python38.dll", but Kodi only has a "python3.8.dll".
			This results in the following error when trying to import the .pyd file:
				from ._psutil_windows import ABOVE_NORMAL_PRIORITY_CLASS, ImportError: DLL load failed while importing _psutil_windows: The specified module could not be found.
			Replacing the dependecy in the .pyd file solves the problem. Note that .pyd files are just normal Windows DLLs and can be edited as such.
			One cannot just binary read/write the .pyd file and replace "python38.dll" with "python3.8.dll", since this will corrupt the file.
			There is a nifty Python library (machomachomangler) that can do exactly this.
		'''
		try:
			if system.startswith(Loader.SystemWindows):
				from lib.modules.tools import File

				pathBase = File.joinPath(pathOriginal, versionOriginal, system)

				systemNew = system + 'kodi'
				pathNew = File.joinPath(pathAdapted, systemNew)
				versionNew = versionOriginal.replace('_', '')

				if not File.existsDirectory(pathNew):
					if File.copyDirectory(pathBase, pathNew):
						libraries = self.moduleLibraries(path = pathNew)
						if libraries:
							for library in libraries:
								pathLibrary = File.joinPath(pathNew, library)
								with open(pathLibrary, 'rb') as file: data = file.read()
								if data:
									from externals.machomachomangler.pe import redll
									data = redll(data, {bytes('python%s.dll' % versionNew, 'ascii') : bytes('python%s.dll' % (versionNew[0] + '.' + versionNew[1:]), 'ascii')})
									with open(pathLibrary, 'wb') as file: file.write(data)

				if self.moduleLibraries(path = pathNew):
					self.moduleAdaptImport(path = pathNew)
					return systemNew
		except:
			from lib.modules.tools import Logger
			Logger.error()
		return None

	def moduleAdaptImport(self, path):
		'''
			Change the psutil sys.modules['xxx'] in _common.py.
		'''

		from lib.modules.tools import File, Regex
		separator = File.separator()
		files = self.modulePython(path = path, absolute = True)
		for file in files:
			try:
				data = File.readNow(file)
				if data and Regex.match(data = data, expression = r'sys\.modules\[[\'"]externals.'):
					parts = Regex.extract(data = file, expression = r'lib\%s(externals\%s.*)\%s' % (separator, separator, separator))
					parts = parts.split(separator)
					parts = '.'.join(parts)
					if parts:
						data = Regex.replace(data = data, expression = r'sys\.modules\[(.*?)]', replacement = '\'%s\'' % parts, group = 1)
						File.writeNow(file, data)
			except:
				from lib.modules.tools import Logger
				Logger.error()

	def moduleDetect(self, wait = True):
		# Execute in a separate process/execution, since the repeated imports of different psutil library architectures gives the following error:
		# 	from . import _psutil_linux as cext "ImportError: cannot import name '_psutil_linux' from partially initialized module 'externals.psutil.39.lin64' (most likely due to a circular import)
		from lib.modules.tools import System
		System.executePlugin(action = 'externalImport', parameters = {'module' : self.moduleId()}, wait = wait)

	def moduleLoad(self, initialize = False):
		try:
			# Do not use tools.Settings, since the class itself uses JSON.
			from lib.modules.tools import System
			if System.addon().getSettingBool('general.performance.library'):
				id = self.moduleId()
				load = False
				try:
					instance = import_module(id)
					if instance and self.moduleTest(instance):
						self.modulePropertySet(Loader.ModuleNative)
						return instance
					else:
						load = True
				except ImportError:
					load = True

				if load:
					from lib.modules.tools import Platform, Tools, System, File

					# NB: Do not use Platform here, otherwise there are possible recursive psutil() calls when the plaform identifier is generated.
					#bits64 = Platform.architectureBits64()
					#system = Platform.systemType()
					platform = Platform.detect(full = False)
					bits64 = platform['architecture']['bits'] == Platform.Bits64
					arm = platform['architecture']['type'] == Platform.ArchitectureArm
					system = platform['system']['type']
					python = platform['python']['version']

					architecture = platform['architecture']['name']
					if architecture:
						architecture = architecture.lower().strip()
						try:
							architecture = {
								'armv6l' : 'armv6',
								'armv7l' : 'armv7',
								'armv8l' : 'armv8',
								'armv9l' : 'armv9',
								'aarch64' : 'arm64',
							}[architecture]
						except: pass

					prefix = None
					if system == Platform.SystemWindows: prefix = Loader.SystemWindows
					elif system == Platform.SystemMacintosh: prefix = Loader.SystemMac
					elif arm: prefix = Loader.SystemArm
					else: prefix = Loader.SystemLinux

					path = File.joinPath(System.pathExternals(), 'lib', 'externals', id)

					# In many cases a different Python version (both lower and higher) can be used.
					# First try to use the current Python version, then higher version, and finally lower versions.
					versionCurrent = '_'.join(python.split('.')[:2])
					versions, _ = File.listDirectory(path = path, absolute = False)
					versions = [i for i in versions if i and Tools.isNumeric(i[0])]

					versions = [(i, int(i.replace('_', ''))) for i in versions]
					versions = Tools.listSort(versions, key = lambda i : i[1])
					versions = [i[0] for i in versions]

					try:
						index = versions.index(versionCurrent)
						versions = [versionCurrent] + versions[index + 1:] + list(reversed(versions[:index]))
					except:
						versions = list(reversed(versions))

					for version in versions:
						try:
							systems, _ = File.listDirectory(path = File.joinPath(path, version), absolute = False)
							systems = [i for i in systems if i and Tools.isAlphabetic(i[0])]
							if prefix: systems = [i for i in systems if i.startswith(prefix)]
							if bits64: systems = [i for i in systems if '64' in i] + [i for i in systems if not '64' in i]
							else: systems = [i for i in systems if '32' in i] + [i for i in systems if not '32' in i]
							if architecture and architecture in systems: systems.insert(0, systems.pop(systems.index(architecture)))

							modules = []
							for i in systems:
								modules.append({'adapted' : '', 'version' : version, 'system' : i})
								adapted = self.moduleAdapt(path = path, system = i, versionCurrent = versionCurrent, versionOriginal = version)
								if adapted: modules.extend([{'adapted' : '.' + Loader.Adapted, 'version' : version, 'system' : j} for j in adapted])

							for i in modules:
								try:
									module = 'externals.%s%s.%s.%s' % (id, i['adapted'], i['version'], i['system'])
									instance = import_module(module)
									if instance and self.moduleTest(instance):
										self.modulePropertySet(module)
										return instance
								except: pass
						except:
							from lib.modules.tools import Logger
							Logger.error()

					self.modulePropertySet(Loader.ModuleNone)
					return None
			else:
				self.modulePropertySet(Loader.ModuleNone)
				return None
		except:
			from lib.modules.tools import Logger
			Logger.error()

		self.modulePropertySet(Loader.ModuleUnknown)
		return None

class Psutil(Loader):

	Id = 'psutil'

	def __init__(self):
	 	Loader.__init__(self, id = Psutil.Id)

class Ujson(Loader):

	Id = 'ujson'

	def __init__(self):
	 	Loader.__init__(self, id = Ujson.Id)

	def moduleTest(self, module):
		# Check that encoding/decoding actually works.
		# Specifically check if the 'default' parameter is available, since some older versions of the module does not have that parameter yet.
		try: return module.dumps({'a':[0,1]}, default = self.moduleSerialize).replace(' ', '') == '{"a":[0,1]}' and module.loads('{"a":[0,1]}')['a'][1] == 1
		except: return False

	@classmethod
	def moduleSerialize(self, object):
		try: return object.dataJson()
		except:
			try: return object.__json__()
			except: return object.__dict__
