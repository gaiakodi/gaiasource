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

from lib.modules.tools import Logger, Converter, System, Tools, Time, Settings, Math, File, Subprocess

class Compression(object):

	TypeLzma		= 'lzma'
	TypeZlib		= 'zlib'
	TypeGzip		= 'gzip'
	TypeBz2			= 'bz2'

	TypeZip			= 'zip'
	TypeSzip		= 'szip' # 7Zip. Since Python variable/function names cannot start with a number.
	TypeXz			= 'xz'

	TypeUnknown		= None

	TypesData		= [TypeLzma, TypeZlib, TypeGzip, TypeBz2]
	TypesFile		= [TypeZip, TypeGzip, TypeSzip, TypeXz]

	# https://en.wikipedia.org/wiki/List_of_file_signatures
	# https://github.com/frizb/FirmwareReverseEngineering/blob/master/IdentifyingCompressionAlgorithms.md
	MagicData		= {
		TypeLzma	: [b'\xfd\x37\x7a\x58\x5a\x00', b'\x5d\x00\x00', b'\x00\x26\x1b\xca\x46\x67'],
		TypeZlib	: [b'\x78\x01', b'\x78\x5e', b'\x78\x9c', b'\x78\xda', b'\x78\x20', b'\x78\x7d', b'\x78\xbb', b'\x78\xf9'],
		TypeGzip	: [b'\x1f\x8b'],
		TypeBz2		: [b'\x42\x5a\x68'],
	}

	MagicFile		= {
		TypeZip		: [b'\x50\x4b\x03\x04', b'\x50\x4b\x05\x06', b'\x50\x4b\x07\x08'],
		TypeGzip	: [b'\x1f\x8b'],
		TypeSzip	: [b'\x37\x7a\xbc\xaf\x27\x1c'],
		TypeXz		: [b'\xfd\x37\x7a\x58\x5a\x00'],
	}

	##############################################################################
	# MAGIC
	##############################################################################

	@classmethod
	def magic(self, data = None, path = None, size = 2):
		try:
			if data:
				return data[:size]
			elif path:
				with open(path, 'rb') as file:
					return file.read(size)
		except: return None

	@classmethod
	def magicSize(self, magic):
		try: return len(Converter.unicode(magic))
		except: return None

	##############################################################################
	# TYPE
	##############################################################################

	@classmethod
	def type(self, data = None, path = None):
		magics = Compression.MagicData if data else Compression.MagicFile
		for type, magic in magics.items():
			if self.magic(data = data, path = path, size = self.magicSize(magic[0])) in magic: return type
		return Compression.TypeUnknown

	@classmethod
	def typeIs(self, type, data = None, path = None):
		try:
			magics = Compression.MagicData if data else Compression.MagicFile
			magic = magics[type]
			return self.magic(data = data, path = path, size = self.magicSize(magic[0])) in magic
		except: return False


class Compressor(Compression):

	'''
		streams.db | 70MB | 1600+ streams from a single scrape | LZMA extreme mode disabled.

							INTEL i7																				ARM Cortex-A73
							Default		Level-0		Level-1		Level-3		Level-5		Level-7		Level-9			Default		Level-0		Level-1		Level-3		Level-5		Level-7		Level-9
		LZMA:
			Size:			0.26%		0.48%		0.39%		0.32%		0.28%		0.23%		0.21%			0.26%		0.48%		0.39%		0.32%		0.28%		0.23%		0.21%
			Compress:		6966 ms		465 ms		524 ms		702 ms		6220 ms		7301 ms		7859 ms			19647 ms	1598 ms		2347 ms		3087 ms		16638 ms	19962 ms	20420 ms
			Decompress:		155 ms		154 ms		157 ms		153 ms		157 ms		159 ms		180 ms			319 ms		295 ms		317 ms		323 ms		319 ms		324 ms		313 ms
		ZLIB:
			Size:			17.70%		100.01%		21.49%		20.56%		17.94%		17.70%		17.67%			17.70%		100.01%		21.49%		20.56%		17.94%		17.70%		17.67%
			Compress:		1281 ms		104 ms		559 ms		677 ms		953 ms		1725 ms		2582 ms			3951 ms		141 ms		1346 ms		1694 ms		2731 ms		5565 ms		8325 ms
			Decompress:		215 ms		102 ms		227 ms		230 ms		224 ms		219 ms		215 ms			390 ms		141 ms		428 ms		421 ms		392 ms		398 ms		391 ms
		GZIP:
			Size:			17.67%		100.01%		21.49%		20.56%		17.94%		17.70%		17.67%			17.67%		100.01%		21.49%		20.56%		17.94%		17.70%		17.67%
			Compress:		2593 ms		172 ms		604 ms		700 ms		993 ms		1736 ms		2614 ms			8396 ms		283 ms		1419 ms		1765 ms		2801 ms		5635 ms		8397 ms
			Decompress:		271 ms		164 ms		294 ms		266 ms		277 ms		254 ms		280 ms			454 ms		239 ms		493 ms		484 ms		455 ms		455 ms		454 ms
		BZ2:
			Size:			2.44%		11.57%		11.57%		5.47%		3.84%		2.94%		2.44%			2.44%		11.57%		11.57%		5.47%		3.84%		2.94%		2.44%
			Compress:		7612 ms		4613 ms		4613 ms		5665 ms		6499 ms		7035 ms		7794 ms			30241 ms	11784 ms	11742 ms	19187 ms	21738 ms	37582 ms	30459 ms
			Decompress:		1572 ms		1173 ms		1173 ms		1155 ms		1233 ms		1289 ms		1550 ms			9915 ms		2653 ms		2649 ms		3955 ms		6348 ms		8720 ms		9925 ms
	'''

	Types			= Compression.TypesData

	SizeLarge		= 'large'	# Large-sized objects to be compressed (JSON in streams.db).
	SizeMedium		= 'medium'	# Medium-size objects to be compressed (JSON in metadata.db).
	SizeSmall		= 'small'	# Small-size objects to be compressed (JSON in cache.db).
	SizeDefault		= SizeMedium
	Sizes			= [SizeLarge, SizeMedium, SizeSmall]

	# Set the limits so that there is no notable increase in execution time to the user.
	# The scraping saving streams should not take more than an extra 10s (worst case, although less on the average case).
	#	Scrape (1600 links): 80MB (for most providers enabled, pack scraping, and extra titles).
	# The menus should not take more than an extra 0.5s.
	#	Movie Menu (50 items): 685KB.
	#	Show Menu (50 items): 1315KB.
	#	Season Menu (10 items): 145KB.
	#	Episode Menu (10 items): 222KB.
	#	Specials Menu (280 items): 1262KB.
	Limit			= {
						SizeLarge	: {'compress' : 10485760,	'decompress' : None},		# 10MB/s
						SizeMedium	: {'compress' : None,		'decompress' : 5242880},	# 5MB/s
						SizeSmall	: {'compress' : None,		'decompress' : 31457280},	# 30MB/s
					}

	Setting			= 'internal.compression'
	Default			= None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def typeDefault(self, size = None, database = False):
		try:
			if Compressor.Default is None:
				setting = Settings.getData(Compressor.Setting)
				if not setting: return None
				Compressor.Default = setting['database' if database else 'default']
			return Compressor.Default[size] if size else Compressor.Default
		except:
			Logger.error()
			return None

	@classmethod
	def details(self):
		result = {
			'global' : None,
			'database' : None,
			'algorithm' : [],
		}

		setting = Settings.getData(Compressor.Setting)
		if setting:
			for i in ['global', 'database']:
				temp = []
				for size in reversed(Compressor.Sizes):
					temp.append('%s (%s)' % (setting['global'][size].upper() if setting['global'][size] else 'None', size.capitalize()))
				result[i] = ' - '.join(temp)

			algorithm = []
			for type, value in setting['algorithm'].items():
				algorithm.append((value['rank'], type, value))
			algorithm = Tools.listSort(data = algorithm, key = lambda i : i[0], reverse = True)

			for i in algorithm:
				description = 'Unsupported'
				if i[2]['support']:
					for size in reversed(Compressor.Sizes):
						ratio = i[2][size]['ratio'] * 100
						compress = i[2][size]['compress'] / 1048576.0
						compress = ('%.1f' if compress > 100 else '%.2f' if compress > 10 else '%.3f') % compress
						decompress = i[2][size]['decompress'] / 1048576.0
						decompress = ('%.1f' if decompress > 100 else '%.2f' if decompress > 10 else '%.3f') % decompress
						description = '%.1f%% Ratio - %sMB/s Compress - %sMB/s Decompress' % (ratio, compress, decompress)
						result['algorithm'].append({'label' : i[1].upper() + '-' + size.capitalize(), 'description' : description})
				else:
					for size in reversed(Compressor.Sizes):
						result['algorithm'].append({'label' : i[1].upper() + '-' + size.capitalize(), 'description' : description})
		else:
			result['global'] = result['database'] = 'Unsupported'

		return result

	##############################################################################
	# BENCHMARK
	##############################################################################

	# Always use level 0, since speed is always more important than compression ratio, since we do not want to slow down the addon.
	# LZMA uses a greedy algorithm for level 0, which is extremely fast and has a great compression ratio, especially compared to higher levels which take considerably longer without substantially increasing the compression ratio.
	# Zlib/Glib (whose lowest level is 1), also have fast compression for lower level, although higher levels have a notably better compression ratio, but not really worth the extra time.
	@classmethod
	def benchmark(self, level = 0, iterations = 3, settings = True, force = False, background = True, wait = False, delay = None):
		if force or Settings.getData(Compressor.Setting) is None:
			if background:
				System.executePlugin(action = 'compressionBenchmark', parameters = {'delay' : delay},wait = wait is True)
				if Tools.isInteger(wait):
					for i in range(wait):
						# Do not use cached settings, retrieve new, since they are updated by another Python invoker.
						if not Settings.getData(Compressor.Setting, cached = False) is None: break
						Time.sleep(1)
			else:
				return self._benchmark(level = level, iterations = iterations, delay = delay, settings = settings)
		return Settings.getData(Compressor.Setting, cached = False)

	@classmethod
	def _benchmark(self, level = 0, iterations = 5, delay = None, settings = True):
		try:
			# NB: Use a few more iterations than 3.
			# Take the lowest, instead of the average, of all measurements.
			# Because this benchmark is run during initial launch, where other processes also use the CPU, and interfere with the measurements.
			if delay:
				if delay is True:
					if System.launchFinished():
						Time.sleep(2)
					else:
						for i in range(240):
							if System.launchFinished(): break
							Time.sleep(0.5)
				else:
					Time.sleep(delay)

			from timeit import default_timer as timer

			result = {}
			for type in Compressor.Types:
				support = self.support(type = type)
				result[type] = {'support' : support}

			# NB: Do not use random data. Some algorithms, especially LZMA, underperform considerably on random data, but are way better for structured JSON data.
			#data = bytes(Tools.stringRandom(length = 1048576, uppercase = True, lowercase = True, digits = True, symbols = True), 'utf-8') # 1MB random data.
			datas = {size : File.readNow(path = File.joinPath(System.pathResources(), 'resources', 'media', 'dummy', size + '.json'), bytes = True) for size in Compressor.Sizes}

			# Do the iterations on the outside loop, not inside a nested loop.
			# This ensures that all algorithms are benchmarked at different times, instead of all benchmarks of the same algorithm be executed after each other.
			# This ensures better measurements when the benchmarking is conducted on first launch, while other processes might be busy, hogging the CPU.
			ratio = {}
			compress = {}
			decompress = {}
			for i in range(iterations):
				for type in Compressor.Types:
					if not type in ratio: ratio[type] = {}
					if not type in compress: compress[type] = {}
					if not type in decompress: decompress[type] = {}

					if result[type]['support']:
						for size, data in datas.items():
							if not size in compress[type]: compress[type][size] = []
							if not size in decompress[type]: decompress[type][size] = []

							compressed = self.compress(data = data, type = type, level = level)
							if compressed:
								start = timer()
								self.compress(data = data, type = type, level = level)
								end = timer()
								compress[type][size].append(end - start)
								Time.sleep(0.1)

								start = timer()
								self.decompress(data = compressed, type = type)
								end = timer()
								decompress[type][size].append(end - start)
								Time.sleep(0.1)

								if not size in ratio[type]: ratio[type][size] = Math.round(len(compressed) / len(data), places = 5)
							else:
								result[type]['support'] = False
								break
			for type in Compressor.Types:
				for size in Compressor.Sizes:
					if size in ratio[type]:
						length = len(datas[size])
						result[type][size] = {
							'ratio' : Math.round(1 - ratio[type][size], places = 5),
							'compress' : Math.round(length / min(compress[type][size]), places = 0),
							'decompress' : Math.round(length / min(decompress[type][size]), places = 0),
						}

			default = {}
			database = {}
			for size in Compressor.Sizes:
				ratio = []
				compress = []
				decompress = []
				for type in Compressor.Types:
					if result[type]['support']:
						ratio.append(result[type][size]['ratio'])
						compress.append(result[type][size]['compress'])
						decompress.append(result[type][size]['decompress'])
				ratio = [min(ratio), max(ratio)] if ratio else [0, 1]
				compress = [min(compress), max(compress)] if compress else [0, 10]
				decompress = [min(decompress), max(decompress)] if decompress else [0, 10]

				ranks = {}
				for type in Compressor.Types:
					if result[type]['support']:
						values = result[type][size]
						valueRatio = Math.scale(value = values['ratio'], fromMinimum = ratio[0], fromMaximum = ratio[1], toMinimum = 0, toMaximum = 1)
						valueCompress = Math.scale(value = values['compress'], fromMinimum = compress[0], fromMaximum = compress[1], toMinimum = 0, toMaximum = 1)
						valueDecompress = Math.scale(value = values['decompress'], fromMinimum = decompress[0], fromMaximum = decompress[1], toMinimum = 0, toMaximum = 1)
						ranks[type] = (0.6 * valueDecompress) + (0.3 * valueCompress) + (0.1 * valueRatio)
						result[type]['rank'] = Math.round(ranks[type], places = 5)
					else:
						result[type]['rank'] = 0

				default[size] = max(ranks, key = ranks.get) if ranks else None

				database[size] = None
				best = result[default[size]][size]
				if size in Compressor.Limit:
					allow = True
					for direction, limit in Compressor.Limit[size].items():
						if limit and best[direction] < limit:
							allow = False
							break
					if allow: database[size] = default[size]

			default = {'default' : default[Compressor.SizeMedium], Compressor.SizeSmall : default[Compressor.SizeSmall], Compressor.SizeMedium : default[Compressor.SizeMedium], Compressor.SizeLarge : default[Compressor.SizeLarge]}
			database = {'default' : database[Compressor.SizeMedium], Compressor.SizeSmall : database[Compressor.SizeSmall], Compressor.SizeMedium : database[Compressor.SizeMedium], Compressor.SizeLarge : database[Compressor.SizeLarge]}
			result = {'global' : default, 'database' : database, 'algorithm' : result}
		except:
			Logger.error()
			result = {}

		if settings: Settings.setData(Compressor.Setting, result)
		return result

	##############################################################################
	# COMPRESSION
	##############################################################################

	@classmethod
	def support(self, data = None, type = None):
		if type is None: type = self.type(data = data)
		if type == Compressor.TypeLzma: return self.lzmaSupport()
		elif type == Compressor.TypeBz2: return self.bz2Support()
		elif type == Compressor.TypeZlib: return self.zlibSupport()
		elif type == Compressor.TypeGzip: return self.gzipSupport()
		else: return False

	# level [0,9]:
	#	0: no compression
	#	1: low compression at high speed
	#	9: high compression at low speed.
	@classmethod
	def compress(self, data, type = None, level = None, extreme = None):
		if type is None: type = self.type(data = data)
		if type == Compressor.TypeLzma: return self.lzmaCompress(data = data, level = level, extreme = extreme)
		elif type == Compressor.TypeBz2: return self.bz2Compress(data = data, level = level)
		elif type == Compressor.TypeZlib: return self.zlibCompress(data = data, level = level)
		elif type == Compressor.TypeGzip: return self.gzipCompress(data = data, level = level)
		else: return None

	@classmethod
	def decompress(self, data, type = None):
		if type is None: type = self.type(data = data)
		if type == Compressor.TypeLzma: return self.lzmaDecompress(data = data)
		elif type == Compressor.TypeBz2: return self.bz2Decompress(data = data)
		elif type == Compressor.TypeZlib: return self.zlibDecompress(data = data)
		elif type == Compressor.TypeGzip: return self.gzipDecompress(data = data)
		else: return None

	##############################################################################
	# LZMA
	##############################################################################

	@classmethod
	def lzmaSupport(self):
		try:
			import lzma
			return True
		except:
			return False

	# level [0,9]:
	#	default: 6
	#	0: no compression
	#	1: low compression at high speed
	#	9: high compression at low speed.
	#	extreme: slightly better compression, but considerably slower speeds, depending on the level. https://man.freebsd.org/cgi/man.cgi?query=lzma
	@classmethod
	def lzmaCompress(self, data, level = None, extreme = None):
		try:
			import lzma
			if level is None and extreme is None:
				return lzma.compress(data)
			else:
				if not level is None: level = max(0, min(9, level))
				if level is None and extreme: level = lzma.PRESET_EXTREME
				elif not level is None and extreme: level = level | lzma.PRESET_EXTREME
				return lzma.compress(data, preset = level)
		except:
			Logger.error()
			return None

	@classmethod
	def lzmaDecompress(self, data):
		try:
			import lzma
			return lzma.decompress(data)
		except:
			Logger.error()
			return None

	##############################################################################
	# ZLIB
	##############################################################################

	@classmethod
	def zlibSupport(self):
		try:
			import zlib
			return True
		except:
			return False

	# level [0,9]:
	#	default: 6
	#	0: no compression
	#	1: low compression at high speed
	#	9: high compression at low speed.
	@classmethod
	def zlibCompress(self, data, level = None):
		try:
			import zlib
			if level is None: return zlib.compress(data)
			else: return zlib.compress(data, level = max(1, min(9, level))) # Never use level 0, since it does not make sense to use it for this algorithm. We still pass in 0 as the best/quickest level, since LZMA has it at 0 and we use it from benchmark().
		except:
			Logger.error()
			return None

	@classmethod
	def zlibDecompress(self, data):
		try:
			import zlib
			return zlib.decompress(data)
		except:
			Logger.error()
			return None

	##############################################################################
	# GZIP
	##############################################################################

	@classmethod
	def gzipSupport(self):
		try:
			import gzip
			return True
		except:
			return False

	# level [0,9]:
	#	default: 9
	#	0: no compression
	#	1: low compression at high speed
	#	9: high compression at low speed.
	@classmethod
	def gzipCompress(self, data, level = None):
		try:
			import gzip
			if level is None: return gzip.compress(data)
			else: return gzip.compress(data, compresslevel = max(1, min(9, level))) # Never use level 0, since it does not make sense to use it for this algorithm. We still pass in 0 as the best/quickest level, since LZMA has it at 0 and we use it from benchmark().
		except:
			Logger.error()
			return None

	@classmethod
	def gzipDecompress(self, data):
		try:
			import gzip
			return gzip.decompress(data)
		except:
			Logger.error()
			return None

	##############################################################################
	# BZ2
	##############################################################################

	@classmethod
	def bz2Support(self):
		try:
			import bz2
			return True
		except:
			return False

	# level [0,9]:
	#	default: 9
	#	0: no compression
	#	1: low compression at high speed
	#	9: high compression at low speed.
	@classmethod
	def bz2Compress(self, data, level = None):
		try:
			import bz2
			if level is None: return bz2.compress(data)
			else: return bz2.compress(data, compresslevel = max(1, min(9, level))) # Never use level 0, since it does not make sense to use it for this algorithm. We still pass in 0 as the best/quickest level, since LZMA has it at 0 and we use it from benchmark().
		except:
			Logger.error()
			return None

	@classmethod
	def bz2Decompress(self, data):
		try:
			import bz2
			return bz2.decompress(data)
		except:
			Logger.error()
			return None

class Archiver(Compression):

	ExtensionZip		= 'zip'
	ExtensionGzip		= 'gz'
	ExtensionSzip		= '7z'
	ExtensionXz			= 'xz'
	ExtensionUnknown	= None

	Extensions			= {
		Compression.TypeZip		: ExtensionZip,
		Compression.TypeGzip	: ExtensionGzip,
		Compression.TypeSzip	: ExtensionSzip,
		Compression.TypeXz		: ExtensionXz,
	}

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def _implemention(self, type):
		Logger.log('%s archive compression not implemented yet.' % type.upper(), type = Logger.TypeFatal)
		return False

	##############################################################################
	# TYPE
	##############################################################################

	@classmethod
	def typeArchive(self, path):
		return not self.type(path = path) == Archiver.TypeUnknown

	##############################################################################
	# EXTENSION
	##############################################################################

	@classmethod
	def extension(self, type, dot = True):
		try:
			extension = Archiver.Extensions[type]
			if extension and dot: extension = '.' + extension
		except: extension = Archiver.ExtensionUnknown
		return extension

	@classmethod
	def extensionType(self, path):
		try:
			for type, extension in Archiver.Extensions.items():
				if path.endswith('.' + extension): return type
		except: return Archiver.TypeUnknown

	##############################################################################
	# COMPRESSION
	##############################################################################

	@classmethod
	def support(self, path = None, type = None):
		if type is None: type = self.type(path = path)
		if type == Archiver.TypeZip: return self.zipSupport()
		elif type == Archiver.TypeGzip: return self.gzipSupport()
		elif type == Archiver.TypeSzip: return self.szipSupport()
		elif type == Archiver.TypeXz: return self.xzSupport()
		else: return False

	@classmethod
	def compress(self, path = None, output = None, type = None, flatten = True):
		if type is None: type = self.type(path = path)
		if type == Archiver.TypeZip: return self.zipCompress(path = path, output = output, flatten = flatten)
		elif type == Archiver.TypeGzip: return self.gzipCompress(path = path, output = output)
		elif type == Archiver.TypeSzip: return self.szipCompress(path = path, output = output)
		elif type == Archiver.TypeXz: return self.xzCompress(path = path, output = output)
		else: return None

	@classmethod
	def decompress(self, path, output, type = None):
		if type is None: type = self.type(path = path)
		if type == Archiver.TypeZip: return self.zipDecompress(path = path, output = output)
		elif type == Archiver.TypeGzip: return self.gzipDecompress(path = path, output = output)
		elif type == Archiver.TypeSzip: return self.szipDecompress(path = path, output = output)
		elif type == Archiver.TypeXz: return self.xzDecompress(path = path, output = output)
		else: return None

	##############################################################################
	# ZIP
	##############################################################################

	@classmethod
	def zipIs(self, path = None):
		return self.typeIs(type = Archiver.TypeZip, path = path)

	@classmethod
	def zipSupport(self):
		try:
			from zipfile import ZipFile
			return True
		except:
			return False

	@classmethod
	def zipCompress(self, path, output, flatten = True):
		try:
			if Tools.isString(path):
				if File.existsDirectory(path = path): _, path = File.listDirectory(path)
				else: path = [path]

			from zipfile import ZipFile, ZIP_DEFLATED
			zip = ZipFile(output, 'w', ZIP_DEFLATED)
			for i in path:
				if flatten: zip.write(i, File.name(path = i, extension = True))
				else: zip.write(i)
			zip.close()

			return True
		except:
			Logger.error()
			return False

	@classmethod
	def zipDecompress(self, path, output):
		try:
			from zipfile import ZipFile
			with ZipFile(path, 'r') as zip:
				zip.extractall(path = output)
			return True
		except:
			Logger.error()
			return False

	##############################################################################
	# GZIP
	##############################################################################

	@classmethod
	def gzipIs(self, path):
		return self.typeIs(type = Archiver.TypeGzip, path = path)

	@classmethod
	def zipSupport(self):
		try:
			import gzip
			return True
		except:
			return False

	@classmethod
	def gzipCompress(self, path, output):
		return self._implemention(type = Archiver.TypeGzip)

	@classmethod
	def gzipDecompress(self, path, output):
		try:
			import gzip
			with gzip.open(path, 'rb') as fileIn:
				with open(File.joinPath(output, File.name(path = path, extension = False)), 'wb') as fileOut:
					for line in fileIn: fileOut.write(line)
			return True
		except:
			Logger.error()
			return False

	##############################################################################
	# SZIP
	##############################################################################

	@classmethod
	def szipIs(self, path):
		return self.typeIs(type = Archiver.TypeSzip, path = path)

	@classmethod
	def szipSupport(self):
		try:
			return '7-Zip' in Subprocess.output(command = '7z --help')
		except:
			return False

	@classmethod
	def szipCompress(self, path, output):
		return self._implemention(type = Archiver.TypeSzip)

	@classmethod
	def szipDecompress(self, path, output):
		try:
			Subprocess.open(command = '7z x "%s" -o"%s"' % (path, output))
			return True
		except:
			Logger.error()
			return False

	##############################################################################
	# XZ
	##############################################################################

	@classmethod
	def xzIs(self, path):
		return self.typeIs(type = Archiver.TypeXz, path = path)

	@classmethod
	def xzSupport(self):
		try:
			return '--version' in Subprocess.output(command = 'xz --help')
		except:
			return False

	@classmethod
	def xzCompress(self, path, output):
		return self._implemention(type = Archiver.TypeXz)

	@classmethod
	def xzDecompress(self, path, output):
		try:
			File.makeDirectory(output)
			Subprocess.open(command = 'xz -dc "%s" > "%s"' % (path, File.joinPath(output, File.name(path = path, extension = False))))
			return True
		except:
			Logger.error()
			return False
