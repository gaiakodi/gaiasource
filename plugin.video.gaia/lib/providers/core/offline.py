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

from lib.providers.core.base import ProviderBase
from lib.modules.tools import Tools, File, Media, Hash, System, Math, Converter, Regex, Archive, Time, Hardware
from lib.modules.interface import Dialog, Format, Translation
from lib.modules.network import Networker, Container
from lib.modules.database import Database
from lib.modules.stream import Stream
from lib.modules.convert import ConverterTime, ConverterSize

class ProviderOffline(ProviderBase):

	AttributeName		= 'name'
	AttributeHash		= 'hash'
	AttributeTime		= 'time'
	AttributeSize		= 'size'
	AttributeSeeds		= 'seeds'
	AttributeLeeches	= 'leeches'
	AttributeDownloads	= 'downloads'
	AttributeUploader	= 'uploader'

	FilterMagnet		= '&dn=(.*?)(?:&[a-z\d]+=|$)'	# Extracts file name from magnet link.
	FilterQuote			= '"(.*)"'						# Extracts file name from between quotes.

	_CustomLocation		= 'location'

	UpdateProbability	= 0.1 # The probability that the dataset is checked for updates during each scrape.

	def __init__(self, **kwargs):
		ProviderBase.__init__(self, **kwargs)

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		name				= None,
		description			= None,
		link				= None,
		rank				= 2,
		performance			= ProviderBase.PerformanceGood,
		optimization		= False, # Do not enable offline providers during optimization. Users have to manually enable them. This is because of oudated data and large downloads.
		enabled				= False,

		supportMovie		= True,
		supportShow			= True,
		supportPack			= True,

		# These values will be overwritten by more exact/up-to-date values from the online meta.json.
		dumpProviderId		= None,	# Optional. Will be determined from the provider name.
		dumpProviderName	= None,	# The website/provider that the dump originated from.
		dumpReleaseTime		= None,	# The estimated date (timestamp) the dump was created.
		dumpSizeDownload	= None,	# The estimated file size (in bytes) of the compressed archive that has to be downloaded.
		dumpSizeStorage		= None,	# The estimated file size (in bytes) of the decompressed database that is stored locally.
		dumpSizeCount		= None,	# The estimated number of rows in the database.

		dumpLinkWeb			= None,	# The original website of the provider.
		dumpLinkSource		= None,	# The website or Github that hosts the dump.

		# Link can be:
		#	String: A single link.
		#	List: A list of multiple links.
		#	Dictionary: The key is the media (TypeMixed/TypeMovie/TypeShow) and the value is a single link or list of links.
		# If a list contains links ending with .00x it is assumed to be a multi-part archive.
		dumpLinkOrignal		= None,

		# A regular expression string.
		# Extracts the file name from a line, in order to filter porn keywords in an external process.
		# If not provided, the entire line will be matched, which can cause some problems:
		#	Other data, like the hash, might contain a random string of characters that match keywords (eg: "porn").
		#	The line might contain a date, which will be interpreted as a porn release (since many porn video contain a date in their file name).
		dumpProcessFilter	= None,

		**kwargs
	):
		try:
			path = self.pathMeta(name = name)
			if File.exists(path):
				meta = Converter.jsonFrom(File.readNow(path))
				dumpProviderId = meta['provider']['id']
				dumpProviderName = meta['provider']['name']
				dumpReleaseTime = meta['release']['time']
				dumpSizeDownload = meta['size']['download']
				dumpSizeStorage = meta['size']['storage']
				dumpSizeCount = meta['size']['count']
		except: self.logError()

		if not description: description = 'The {name} provider downloads a static offline database from [B]{dumpprovidername}[/B] with [B]{dumpsizecount}[/B] enries up to [B]{dumpreleasetime}[/B]. Scraping is done locally by querying the downloaded database. Although scraping might be fast with a local database, it only contains links from older titles. Newer releases will therefore not be available through this provider. During the first scrape, the provider will download a [B]{dumpsizedownload}[/B] archive which will be extracted locally and require [B]{dumpsizestorage}[/B] disk space. Hence, the first scrape might be slow due to the database download, but subsequent scrapes will be a lot faster, since no additional internet requests will have to be made. A fast internal drive, like a SSD or eMMC, is recommended, since millions of file names are scanned during scraping. External or other slower drives, like a HDD or USB drive, also work, but are considerably slower for larger databases. The database might also lack additional metadata, such as file sizes, dates, peers, and uploaders.'
		description = description.format(**{
			'name' : '{name}',
			'dumpprovidername' : dumpProviderName,
			'dumpreleasetime' : ConverterTime(dumpReleaseTime, ConverterTime.FormatTimestamp).string(ConverterTime.FormatMonth),
			'dumpsizedownload' : ConverterSize(dumpSizeDownload).stringOptimal(places = ConverterSize.PlacesNone),
			'dumpsizestorage' : ConverterSize(dumpSizeStorage).stringOptimal(places = ConverterSize.PlacesNone),
			'dumpsizecount' : Math.thousand(dumpSizeCount or 0),
		})

		ProviderBase.initialize(self,
			name				= name,
			description			= description,
			link				= link,
			rank				= rank,
			performance			= performance,
			optimization		= optimization,
			enabled				= enabled,

			supportMovie		= supportMovie,
			supportShow			= supportShow,
			supportPack			= supportPack,

			custom				= [
									{
										ProviderBase.SettingsId				: ProviderOffline._CustomLocation,
										ProviderBase.SettingsLabel			: 'Storage Location',
										ProviderBase.SettingsDefault		: self.path(default = True, name = name),
										ProviderBase.SettingsType			: ProviderBase.SettingsTypePath,
										ProviderBase.SettingsMode			: ProviderBase.SettingsPathRead,
										ProviderBase.SettingsDescription	: 'The location of the directory containing the database and meta files. This directory requires write permissions if you want to automatically download future database updates. Make sure that enough disk space is available and use a fast local drive if possible for better performance. Samba and network drives might not always work for this.',
									},
								],

			**kwargs
		)

		self.dataUpdate({
			'dump' : {
				'provider' : {
					'id' : dumpProviderId or dumpProviderName.lower(),
					'name' : dumpProviderName,
				},
				'release' : {
					'time' : dumpReleaseTime,
					'date' : ConverterTime(dumpReleaseTime, ConverterTime.FormatTimestamp).string(ConverterTime.FormatDate),
				},
				'size' : {
					'download' : dumpSizeDownload,
					'storage' : dumpSizeStorage,
					'count' : dumpSizeCount,
				},
				'link' : {
					'web' : dumpLinkWeb,
					'source' : dumpLinkSource,
					'orignal' : dumpLinkOrignal if Tools.isArray(dumpLinkOrignal) else [dumpLinkOrignal],
				},
				'data' : [],
				'process' : {
					'filter' : dumpProcessFilter,
				},
			}
		})

	##############################################################################
	# DUMP
	##############################################################################

	def dump(self):
		return self.mData['dump']

	def dumpProviderId(self):
		return self.mData['dump']['provider']['id']

	def dumpProviderName(self):
		return self.mData['dump']['provider']['name']

	def dumpReleaseTime(self):
		return self.mData['dump']['release']['time']

	def dumpReleaseDate(self):
		return self.mData['dump']['release']['date']

	def dumpSizeDownload(self):
		return self.mData['dump']['size']['download']

	def dumpSizeStorage(self):
		return self.mData['dump']['size']['storage']

	def dumpSizeCount(self):
		return self.mData['dump']['size']['count']

	def dumpLinkWeb(self):
		return self.mData['dump']['link']['web']

	def dumpLinkSource(self):
		return self.mData['dump']['link']['source']

	def dumpLinkOrignal(self):
		return self.mData['dump']['link']['orignal']

	def dumpProcessFilter(self):
		return self.mData['dump']['process']['filter']

	##############################################################################
	# PATH
	##############################################################################

	def path(self, default = False, name = None, translate = None):
		if not default:
			custom = self.custom(id = ProviderOffline._CustomLocation)
			if custom: return File.translatePath(custom)
		if translate is None: translate = not default
		return File.translatePath(File.joinPath(System.pathProviders(translate = translate), name or self.name()))

	def pathData(self, id = None, name = None):
		if id:
			return File.joinPath(self.path(name = name), 'data%s%s' % (id, Database.Extension))
		else:
			_, files = File.listDirectory(path = self.path(name = name), absolute = True)
			return [i for i in files if i.endswith(Database.Extension)]

	def pathMeta(self, name = None):
		return File.joinPath(self.path(name = name), 'meta.json')

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, language = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		try:
			# Download the dataset.
			# Only do this here and not during initialize(), otherwise downloading will occur just when loading the providers.
			self.update()

			# This can take quite long for larger databaes.
			# OfflineParadise (875 MB over 6 databases) takes about 35 seconds on a SSD.
			# OfflineCSV (67 MB over 1 database) takes about 10 seconds on a SSD.
			if not self.stopped():
				paths = self.pathData()
				for path in paths:
					if not self.stopped():
						self.searchFind(path = path, media = media, titles = titles)
						self.statisticsUpdateSearch(request = True, page = True)
		except: self.logError()

	def searchFind(self, path, media, titles):
		try:
			if File.exists(path):
				titles = titles['search']['main']
				queries = Tools.listUnique(['%' + Tools.replaceNotAlphaNumeric(i, replace = '%') + '%' for i in titles])
				matcher = '(?:^|[^a-z\d]+)(%s)(?:$|[^a-z\d]+)' % ('|'.join(Tools.listUnique([Tools.replaceNotAlphaNumeric(i, replace = '[^a-z\d]+') for i in titles])))
				if queries:
					database = Database(path = path, label = True)
					if database:
						query = ' OR '.join(['name LIKE ?'] * len(queries))
						tables = database._tables()
						if tables:
							mixed = '(?:data|mixed|generic|all|full|torrents?|magnets?|links?|urls?|streams?)'
							if Media.typeMovie(media): expression = '(movie|film|set|collection|%s)' % mixed
							elif Media.typeTelevision(media): expression = '(tv|television|serie|show|episode|%s)' % mixed
							if expression: tables = [i for i in tables if Regex.match(data = i, expression = expression)]
							if not tables: tables = database._tables()
						for i in tables:
							values = database._select('SELECT * FROM %s WHERE %s;' % (i, query), (queries))
							if values:
								parameters = {
									Stream.ParameterLink : '(?:link|url|urn|magnet|torrent)',
									Stream.ParameterHash : '(?:(?:info.*)?hash|md5|sha1|sha256|sha512)',

									Stream.ParameterVideoQuality : '(?:video.*)?quality',
									Stream.ParameterVideoCodec : '(?:video.*)?codec',
									Stream.ParameterVideoDepth : '(?:video.*)?(?:depth|bit)',
									Stream.ParameterVideoRange : '(?:video.*)?(?:range|sdr|hdr)',
									Stream.ParameterVideo3d : '(?:video.*)?(?:3d|sbs)',

									Stream.ParameterAudioType : '(?:audio.*)type',
									Stream.ParameterAudioChannels : '(?:audio.*)?(?:channel|surround)',
									Stream.ParameterAudioSystem : '(?:audio.*)system',
									Stream.ParameterAudioCodec : '(?:audio.*)codec',
									Stream.ParameterAudioLanguage : '(?:audio.*)?language',

									Stream.ParameterSubtitleType : '(?:subtitle.*)type',
									Stream.ParameterSubtitleLanguage : '(?:subtitle.*)language',

									Stream.ParameterReleaseType : '(?:release.*)type',
									Stream.ParameterReleaseFormat : '(?:release.*)?format',
									Stream.ParameterReleaseEdition : '(?:release.*)?edition',
									Stream.ParameterReleaseNetwork : '(?:release.*)?network',
									Stream.ParameterReleaseGroup : '(?:release.*)?group',
									Stream.ParameterReleaseUploader : '(?:release.*)?(?:uploader|user)',

									Stream.ParameterFileName : '(?:file.*)?name',
									Stream.ParameterFileExtra : '(?:file.*)?extra',
									Stream.ParameterFileSize : '(?:file.*)?(?:size|byte)',
									Stream.ParameterFileContainer : '(?:file.*)?container',
									Stream.ParameterFilePack : '(?:(?:file|show|season|episode|set|collection).*)?(?:pack|set|collection)',

									Stream.ParameterSourceType : '(?:source.*)?type',
									Stream.ParameterSourceSeeds : '(?:source.*)?seed',
									Stream.ParameterSourceLeeches : '(?:source.*)?leech',
									Stream.ParameterSourcePeers : '(?:source.*)?peers',
									Stream.ParameterSourceTime : '(?:source.*)?(?:time(?:.*stamp)?|date)',
									Stream.ParameterSourcePopularity : '(?:source.*)?(?:popularity|rating|rank(?:ing)?)',
									Stream.ParameterSourcePublisher : '(?:source.*)?publisher',
									Stream.ParameterSourceHoster : '(?:source.*)?host',
								}

								attributes = {}
								value = values[0]
								for k, v in parameters.items():
									for i in value.keys():
										if k == i or Regex.match(data = i, expression = v):
											attributes[k] = i
											break

								if attributes:
									for i in values:
										if i:
											parameters = Tools.copy(attributes)
											for k, v in parameters.items():
												try: parameters[k] = i[v]
												except: parameters[k] = None
											if (Stream.ParameterHash in parameters and parameters[Stream.ParameterHash]) or (Stream.ParameterLink in parameters and parameters[Stream.ParameterLink]):
												if Stream.ParameterFileName in parameters and parameters[Stream.ParameterFileName]:
													# The database can return a lot of incorrect links, which increases scraping time due to all the processing in stream.py.
													# Eg: For "Game of Thrones" we also search "GoT", which with the SQL like "%" will match any name with a "got" substring.
													if Regex.match(data = parameters[Stream.ParameterFileName], expression = matcher):
														if not Stream.ParameterSourceType in parameters or not parameters[Stream.ParameterSourceType]: parameters[Stream.ParameterSourceType] = self.type()

														# Used among others by Orion.
														parameters[Stream.ParameterAccessOffline] = True
														parameters[Stream.ParameterSourceHoster] = self.dumpProviderName()

														stream = self.resultStream(**parameters)
														if stream: self.resultAdd(stream)
						database._close()
		except: self.logError()

	##############################################################################
	# GENERATE
	##############################################################################

	def generate(self):
		id = self.id()
		directory = File.joinPath(self.access(), id)

		sql = [
			{'name' : ProviderOffline.AttributeTime,		'index' : False,	'type' : 'INTEGER'},
			{'name' : ProviderOffline.AttributeSize,		'index' : False,	'type' : 'INTEGER'},
			{'name' : ProviderOffline.AttributeSeeds,		'index' : False,	'type' : 'INTEGER'},
			{'name' : ProviderOffline.AttributeLeeches,		'index' : False,	'type' : 'INTEGER'},
			{'name' : ProviderOffline.AttributeDownloads,	'index' : False,	'type' : 'INTEGER'},
			{'name' : ProviderOffline.AttributeUploader,	'index' : False,	'type' : 'TEXT'},
			{'name' : ProviderOffline.AttributeHash,		'index' : False,	'type' : 'TEXT'},
			{'name' : ProviderOffline.AttributeName,		'index' : True,		'type' : 'TEXT COLLATE NOCASE'},
		]

		data = {
			Media.TypeMixed : [],
			Media.TypeMovie : [],
			Media.TypeShow : [],
		}

		link = Tools.copy(self.dumpLinkOrignal())
		if not Tools.isDictionary(link): link = {Media.TypeMixed : link}
		for k, v in link.items():
			if Tools.isArray(v) and Regex.match(data = v[0], expression = '\.[a-z]?0*(?:0|1)$'): # Multi-part archive.
				data[k] = [{'id' : Hash.sha1(v[0]), 'name' : v[0], 'link' : v, 'path' : None}]
			else:
				if not Tools.isArray(v): v = [v]
				data[k] = [{'id' : Hash.sha1(i), 'name' : i, 'link' : i, 'path' : None} for i in v]

		self.log('Downloading datasets ...')
		for k, v in data.items():
			for i in v:
				path = System.temporary(directory = File.joinPath(directory, '1-input'), gaia = True, make = True, clear = False)
				i['path'] = File.joinPath(path, i['id'])
				if File.exists(i['path']):
					self.log('   Already downloaded: %s' % i['path'])
				else:
					if Tools.isArray(i['link']):
						for j in i['link']:
							pathSplit = i['path'] + Regex.extract(data = j, expression = '.*(\.\d+)$')
							if File.exists(pathSplit):
								self.log('   Already downloaded: %s' % pathSplit)
							else:
								self.log('   Downloading: %s' % j)
								success = Networker().download(link = j, path = pathSplit)
								if not success:
									self.log('Failed to download %s datasets: %s' % (k, j))
									return False
						i['path'] += Regex.extract(data = i['link'][0], expression = '.*(\.\d+)$')
					else:
						self.log('   Downloading: %s' % i['link'])
						success = Networker().download(link = i['link'], path = i['path'])
						if not success:
							self.log('Failed to download %s datasets: %s' % (k, i['link']))
							return False

		self.log('Decompressing datasets ...')
		for k, v in data.items():
			if any(i['path'] for i in v):
				self.log('   Decompressing %s database ...' % k)
				for i in v:
					path = System.temporary(directory = File.joinPath(directory, '2-extract'), file = i['id'], gaia = True, make = True, clear = False)
					if not File.exists(File.joinPath(path, i['id'])):
						if Archive.isArchive(i['path']):
							File.makeDirectory(path)
							Archive.decompress(path = i['path'], output = path)
							_, files = File.listDirectory(path = path, absolute = True)
							if files:
								i['path'] = files[0]
							else:
								self.log('Failed to decompress %s datasets: %s' % (k, i['name']))
								return False
						else: # Raw CSV.
							File.copy(pathFrom = i['path'], pathTo = path)
					else:
						_, files = File.listDirectory(path = path, absolute = True)
						i['path'] = files[0]

		pathExclude = self._generateExcludeExpression()
		if not pathExclude: return False

		self.log('Excluding database ...')
		from lib.modules.tools import Subprocess
		for k, v in data.items():
			if any(i['path'] for i in v):
				self.log('   Excluding %s database ...' % k)
				for i in v:
					if i['path'] and File.exists(i['path']):
						path = System.temporary(directory = File.joinPath(directory, '3-exclude'), gaia = True, make = True, clear = False)
						File.makeDirectory(path)
						path = File.joinPath(path, i['id'] + '.dat')
						if not File.exists(path):
							# multiprocessing has a problem in the new Python version.
							# So we cannot make the Stream functionos executed in parallel.
							# The best option is to start a subprocess to filter out porn in parallel, and then filter the Stream stuff sequentially in Kodi.
							arguments = Converter.base64To(Converter.jsonTo({'input' : i['path'], 'output' : path, 'exclude' : pathExclude, 'filter' : self.dumpProcessFilter()}))
							Subprocess.live(command = ['python3', File.joinPath(File.directoryCurrent(), 'exclude.py'), arguments])
						i['path'] = path

		self.log('Generating database ...')
		directoryData = System.temporary(directory = File.joinPath(directory, '4-process'), gaia = True, make = True, clear = False)
		pathData = File.joinPath(directoryData, 'data1' + Database.Extension)
		countData = 0
		if not File.exists(pathData):
			pathData = []
			pathData.append(System.temporary(directory = directoryData, file = 'data' + str(len(pathData) + 1) + Database.Extension, gaia = True, make = True, clear = False))
			database = Database(path = pathData[-1])
			for k, v in data.items():
				if any(i['path'] for i in v):
					self.log('   Generating %s database ...' % k)

					table = 'data' if k == Media.TypeMixed else k
					query = 'INSERT INTO %s (%s) VALUES (%s);' % (table, ', '.join([j['name'] for j in sql]), ', '.join(['?'] * len(sql)))
					queries = ['CREATE TABLE IF NOT EXISTS %s (%s);' % (table, ', '.join(['%s %s' % (j['name'], j['type']) for j in sql]))]
					for j in sql:
						if 'index' in j and j['index']:
							queries.append('CREATE INDEX IF NOT EXISTS index_%s_%s ON %s(%s %s);' % (table, j['name'], table, j['name'], 'COLLATE NOCASE' if 'nocase' in j['type'].lower() else ''))
					for i in queries: database._create(i)

					for i in v:
						if i['path'] and File.exists(i['path']):
							count = float(sum(1 for _ in open(i['path'])) / 100)
							counter = 0
							counterValid = 0
							counterInvalid = 0
							progress = -1
							time = Time.timestamp()
							with open(i['path']) as file:
								for line in file:
									extracted = self._generateExtract(line)
									valid = self._generateExcludeStream(extracted)

									counter += 1
									if extracted and valid: counterValid += 1
									else: counterInvalid += 1
									currentProgress = Math.round(counter / count, places = 1)
									if currentProgress > progress and countData % 5000 == 0:
										currentTime = Time.timestamp() - time
										progress = currentProgress
										self.log('      Progress: %.1f%% [Total: %s | Valid: %s | Invalid: %s] -- [Time: %d min | Remaining: %d min]' % (progress, Math.thousand(counter), Math.thousand(counterValid), Math.thousand(counterInvalid), currentTime / 60.0, (((currentTime * (100.0 / (progress or 0.0001))) - currentTime) / 60.0)))
										if System.aborted(): return False

									if extracted and valid:
										# Superhits Of The 80\'s greatest hits 1986
										# Brian Tracy - \"21 Ways To\" series
										# &#30495;&#37326;&#36229;&#26144;&#20687; Animal Camera
										# [post-rock, psychedelic rock] (2016) Black Bombaim &amp; Pete
										# [HUNT-764] &nbsp; At that moment, I Na moody never you connect
										# 35 ans et pr&ecirc;tes &agrave; encaisse [ WEB-DL, 720p]
										# [MEKO-123] &quot;What are you going to get drunk with your aunt
										# A M&uacute;mia BDRip 1080p Dublado JohnL
										# A Voz de Uma Gera&ccedil;&atilde;o (2014) BluRay 720p Dual &Aac
										if 'name' in extracted:
											extracted['name'] = extracted['name'].replace('\\\'', '\'').replace('\\"', '"')
											extracted['name'] = Networker.htmlDecode(extracted['name'])

										parameters = []
										for j in sql: parameters.append(extracted[j['name']] if j['name'] in extracted else None)
										database._insert(query, parameters, commit = False)
										countData += 1
										if countData % 10000 == 0: database._commit() # Reduce disk I/O.

										# If the database becomes too large, split over multiple files.
										# For some providers (eg RarBG), 1,000,000 rows are 60-70MB.
										# For other providers (eg TorrentParadise), 1,000,000 rows are around 90-95MB, probably due to longer file names.
										if countData % 1000000 == 0:
											database._commit()
											database._compress()
											database._close()

											pathData.append(System.temporary(directory = directoryData, file = 'data' + str(len(pathData) + 1) + Database.Extension, gaia = True, make = True, clear = False))
											database = Database(path = pathData[-1])
											for i in queries: database._create(i)
						else:
							self.log('Failed to process %s database: %s' % (k, i['name']))
							return False

			database._commit()
			database._compress()
			database._close()

		self.log('Generating release ...')

		countData = 0
		_, pathData = File.listDirectory(path = directoryData, absolute = True)
		pathData = Tools.listSort(pathData)
		for i in pathData:
			database = Database(path = i)
			tables = database._selectValues('SELECT name FROM sqlite_schema WHERE type = "table";')
			for j in tables: countData += int(database._selectValue('SELECT COUNT(*) FROM %s;' % j))

		directory = System.temporary(directory = File.joinPath(directory, '5-release'), gaia = True, make = True, clear = False)
		File.deleteDirectory(directory)
		nameMeta = 'meta.json'
		pathMeta = System.temporary(directory = directory, file = nameMeta, gaia = True, make = True, clear = False)
		sizeDownload = 0
		sizeStorage = 0
		datas = []

		for i in range(len(pathData)):
			nameZip = 'data' + str(i + 1) + Archive.extension(type = Archive.TypeZip, dot = True)
			pathZip = System.temporary(directory = File.joinPath(directory, 'data'), file = nameZip, gaia = True, make = True, clear = False)

			if Archive.zipCompress(path = pathData[i], output = pathZip):
				sizeDownload += File.size(pathZip)
				sizeStorage += File.size(pathData[i])
				datas.append(Networker.linkJoin(self.link().replace(nameMeta, ''), 'data', nameZip))
			else:
				self.log('Failed to create archive: %s' % pathZip)
				return False

		meta = Tools.copy(self.dump())
		del meta['process']
		meta['size']['download'] = sizeDownload
		meta['size']['storage'] = sizeStorage
		meta['size']['count'] = countData
		meta['data'] = datas
		meta = Converter.jsonPrettify(data = meta)
		File.writeNow(pathMeta, meta)

		return True

	# Can be overwritten by subclasses.
	# A function that extracts values from a dataset line.
	# Receives as input a single line as a string.
	# Returns a dictionary with extracted attributes, or None if it failed (eg: comment or incorrectly formatted line).
	# If not overwritten by subclasses, this default function will be used that assumes each line is one magnet link.
	def _generateExtract(self, data):
		# Do not save the magnet to the database.
		# From the dumps it seems that magnets only contain the hash and the name, but not any other parameters like the size or the trackers.
		# Storing the entire magnet link therefore just increases the database file size, since the hash/name is stored twice, together with the magnet prefix for each row.
		'''try:
			if data:
				if Networker.linkIs(link = data, magnet = True):
					if Networker.linkIsMagnet(link = data):
						name = Container(link = data).torrentName()
						if name: return {ProviderOffline.AttributeName : name, ProviderOffline.AttributeLink : data}
		except: self.logError()
		return None'''
		try:
			if data and Networker.linkIsMagnet(link = data):
				container = Container(link = data)
				hash = container.torrentHash()
				name = container.torrentName()
				if hash and name: return {ProviderOffline.AttributeHash : hash, ProviderOffline.AttributeName : name}
		except: self.logError()
		return None

	def _generateExcludeStream(self, data):
		if not data: return False

		# 20 MB too little for a lot of porn.
		# There are a few valid ones between 70-100MB, but most of them are porn/software.
		if 'size' in data and data['size'] and data['size'] < 104857600: return False

		if not 'name' in data: return False
		name = data['name']
		if not name: return False

		expressionSeparator = u'[\s\-\–\_\+\.\,\\\/\|\:\&]'
		expressionSeparatorExtra = u'[\s\-\–\_\+\.\,\\\/\|\:\&\(\[\{\)\]\}]'

		# Prohibited
		if Stream.titleProhibited(data = name, special = True, exception = True): return False

		# Porn studios as a prefix with camel case.
		prefix = name.split(' ')
		if prefix:
			prefix = prefix[0]
			index = [i for i, e in enumerate(prefix + 'A') if e.isupper()]
			if index:
				parts = [prefix[index[j] : index[j + 1]] for j in range(len(index) - 1)]
				if len(parts) > 1 and Stream.titleProhibited(data = ' '.join(parts), special = True, exception = True): return False

		# Music/Albums
		if Regex.match(data = name, expression = 'kbps', cache = True):
			# Some DD/DTS also have a kbps label.
			system = Stream.audioSystemExtract(data = name)
			if not system or not system in [Stream.AudioSystemDolby, Stream.AudioSystemDts]: return False
		codec = Stream.audioCodecExtract(data = name)
		album = codec and codec in [Stream.AudioCodecFlac, Stream.AudioCodecMp3]
		if not album:
			if codec: return True
			if Stream.audioSystemExtract(data = name): return True

		# Generic
		if Regex.match(data = name, expression = '((?:^|%s)(?:movies?|films?|tv|series?|episodes?)(?:$|%s))' % (expressionSeparatorExtra, expressionSeparatorExtra), cache = True): return True

		# Number
		number = Stream.numberShowExtract(data = name)
		if number and (number['season'] or number['episode']): return True

		# Other (mixed order for faster processing).
		if Stream.videoQualityExtract(data = name, default = False): return True
		if Stream.videoCodecExtract(data = name): return True
		if Stream.audioChannelsExtract(data = name): return True
		if Stream.releaseTypeExtract(data = name): return True
		if Stream.filePackExtract(data = name): return True
		if Stream.videoRangeExtract(data = name): return True
		if Stream.videoDepthExtract(data = name): return True
		if Stream.releaseFormatExtract(data = name): return True
		if Stream.releaseEditionExtract(data = name): return True
		if Stream.releaseNetworkExtract(data = name): return True
		if Stream.subtitleTypeExtract(data = name): return True
		if Stream.video3dExtract(data = name): return True

		audio = Stream.audioTypeExtract(data = name)
		if audio and not audio == Stream.AudioTypeOriginal: return True

		music = Regex.match(data = name, expression = '(?:^|%s)(\d+%s*cds?|va|top%s\d+|music%s(?:compilation|collection|set)s?|vol(?:umes?)?%s*\d+|megamix|remixland|discography|@?\d+%s*kbps?|best%sof)(?:$|%s)' % (expressionSeparatorExtra, expressionSeparator, expressionSeparator, expressionSeparator, expressionSeparator, expressionSeparator, expressionSeparator, expressionSeparatorExtra), cache = True)

		# Year
		if not album and not music and Stream.yearExtract(data = name): return True

		# Do this last.
		# This can be valid names, but if not video/stream metadata was detected, these are probably books, music, or software.
		if music: return False

		return False

	def _generateExcludeExpression(self):
		self.log('Generating exclude expressions ...')
		result = []
		path = System.temporary(directory = self.access(), file = 'exclude.dat', gaia = True, make = True, clear = False)

		if File.exists(path):
			data = File.readNow(path)
			result = data.split('\n')
		else:
			expressionSymbol			= u'[\s\-\–\!\?\$\%%\^\&\*\(\)\_\+\|\~\=\#\`\{\}\\\[\]\:\"\;\'\<\>\,\.\\\/]'
			expressionSymbolAlternative	= u'[\s\-\–\$\%%\^\&\*\(\)\_\+\|\~\=\`\{\}\\\[\]\:\"\;\'\<\>\,\.\\\/]'
			expressionSymbolStart		= u'(?:^|' + expressionSymbol + '+)'
			expressionSymbolEnd			= u'(?:$|' + expressionSymbol + '+)'
			expressionSeparator			= u'[\s\-\–\_\+\.\,\\\/\|\:\&]'
			expressionSeparatorExtra	= u'[\s\-\–\_\+\.\,\\\/\|\:\&\(\[\{\)\]\}]'

			# Porn
			result.append('(?:horny|penetration|facials?|shemale|nude.+photos?|fc2.?ppv|MyDaughtersHotFriend|SisLoveMe)')

			# JAV Porn
			#	 [HD] FCH-037
			#	[HD] SIRO-3911
			#	[HD] 200GANA-2119
			#	[HD] 300MIUM-472
			result.append('(?:\s*\[hd\]\s*[a-z\d]+\-\d+\s*$)')

			# Some daytime shows have a date, but most dates are porn.
			result.append('(?:[0123]\d[\.\-\s]?[0123]\d[\.\-\s]?(?:19|2[01])?\d{2}|(?:19|2[01])?\d{2}[\.\-\s]?[0123]\d[\.\-\s]?[0123]\d)')

			# Music
			result.append('(?:^%s?VA%s+|(?:mp3|aac|flac)%s+@)' % (expressionSeparatorExtra, expressionSeparatorExtra, expressionSeparator))
			result.append('(?:^|%s)(ost)(?:$|%s)' % (expressionSeparatorExtra, expressionSeparator))

			# Books
			result.append('(?:(?:^|%s)(epubs?|ebooks?)(?:$|%s))' % (expressionSeparatorExtra, expressionSeparatorExtra))
			result.append('(?:^ttc[\.\-\s]|books?.?(?:collections?|packs?))')
			result.append('(?:\d+[\s\-\–\_\+\.]?(?:ed(?:ition)?|(?:st|nd|rd|th)[\s\-\–\_\+\.]?ed(?:ition)?))')

			# Software
			result.append('(?:v(?:ersion)?[\.\-\s]*\d+\.\d+|v(?:ersion)?[\.\-\s]*\d+[\.\-\s]\d+[\.\-\s]\d+|(?:with|including|includes)[\.\-\s]*crack(?:s|ed)?|crackingpatching|keygen|build[\.\-\s]*\d+|free4pc|babupc|x86|x64|[^a-z\d]oem[^a-z\d]|mac.*os)')

			# Games
			result.append('(?:skidrow|fitgirl|codex)')

			# Other
			result.append('(?:Tour[\.\-\s]de[\.\-\s]France)')

			# Dictionary

			link = 'https://github.com/dolph/dictionary/raw/master/popular.txt'
			self.log('   Downloading: %s' % link)
			words = Networker().requestText(link = link)
			if words: words = [i.lower().strip() for i in words.split('\n')]
			if not words:
				self.log('Could not download dictionary %s' % link)
				return None

			# Names

			names = []

			link = 'https://github.com/dominictarr/random-name/raw/master/first-names.txt' # Does not include names like "richard".
			self.log('   Downloading: %s' % link)
			name = Networker().requestText(link = link)
			if name:
				names.extend([i.lower().strip() for i in name.split('\n')])
			else:
				self.log('Could not download names: %s' % link)
				return None

			link = 'https://github.com/aruljohn/popular-baby-names/raw/master/2021/girl_boy_names_2021.json'
			self.log('   Downloading: %s' % link)
			name = Networker().requestJson(link = link)
			if name:
				names.extend([i.lower().strip() for i in name['girls']])
				names.extend([i.lower().strip() for i in name['boys']])
			else:
				self.log('Could not download names: %s' % link)
				return None

			names = Tools.listUnique(names)
			if not names:
				self.log('Could not download names')
				return None

			# Porn
			links = [
				#'https://github.com/mhhakim/pihole-blocklist/raw/master/porn.txt', # Too many incorrect domains, like booking.com.

				'https://github.com/mhhakim/pihole-blocklist/raw/master/custom-porn-blocklist.txt',
				'https://github.com/Bon-Appetit/porn-domains/raw/master/block.txt',
				'https://github.com/v2ray/domain-list-community/raw/master/data/category-porn',
				'https://github.com/4skinSkywalker/Anti-Porn-HOSTS-File/raw/master/HOSTS.txt',

				'https://gist.github.com/ryanlewis/a37739d710ccdb4b406d/raw/0fbd315eb2900bb736609ea894b9bde8217b991a/google_twunter_lol',
				'https://gist.github.com/jonathonbyrdziak/8cdd4c01aa941c1854b9/raw/31236f5b161e682a9726f4525b2fe4fbbe8855c7/negative-keywords-porn.js',
			]

			exclude = ['1bet', '2160p', '2160', '1080p', '1080', '720p', '720', 'web', 'cam', 'webcam', 'multi', 'noads', 'noad', 'hdtv', 'kiki', 'foryou', 'france', 'asian', '', 'mania', 'worldof', 'forme',  'incharge', 'bewild', 'mywife', 'keygen', 'thepalace', 'top100', 'tera', 'hardcore', 'starz', 'pluto', 'sex', 'butt', 'ass', 'arse', 'adult', 'dick', 'fuck', 'fucks', 'fucked', 'hump', 'mature', 'naked', 'naughty', 'sexy', 'balls', 'bastard', 'bitch', 'crap', 'damn', 'god', 'hell', 'knob', 'lust', 'nazi', 'retard', 'sadist', 'screwing', 'shit', 'shits', 'shitty', 'slut', 'sluts', 'snatch', 'turd', 'taboo', 'suck', 'sucks', 'watersport', 'watersports', 'free']

			for link in links:
				self.log('   Downloading: %s' % link)
				data = Networker().requestText(link = link)
				if data: data = data.split('\n')
				if not data:
					self.log('Could not download keywords: %s' % link)
					return None

				self.log('      Progress: 0%')
				progressed = 0
				total = float(len(data))
				for i in range(int(total)):
					progress = Math.round(value = (i / total) * 100, places = 0)
					if progress > progressed:
						progressed = progress
						self.log('      Progress: %d%%' % progress)

					value = data[i].lower().strip()
					if value:
						value = value.replace('0.0.0.0', '').replace('www.', '').strip(' ').strip('\t').strip(' ')
						if value and not value.startswith('#') and not value.startswith('//') and not value.startswith('include:') and not value.startswith('regexp:') and '.' in value:
							domain = Networker.linkDomain(link = value, subdomain = False, topdomain = False, ip = False, scheme = False, port = False)
							if domain and len(domain) >= 5 and not Tools.isNumeric(domain):
								if not domain in exclude:
									# Exclude words that appear in the English dictionary.
									domainStripped = Tools.replaceNotAlphaNumeric(data = domain, replace = '')
									if not domainStripped in exclude:
										if domain == domainStripped: domainStripped = None
										if not any(j == domain for j in words) and (not domainStripped or not any(j == domainStripped for j in words)):
											if not any(j == domain for j in names) and (not domainStripped or not any(j == domainStripped for j in names)):
												result.append(Tools.replaceNotAlphaNumeric(data = domain, replace = '[\s\.\-\_]?'))

				self.log('      Progress: 100%')

			result = Tools.listUnique(result)
			File.writeNow(path, '\n'.join(result))

		self.log('Exclude expressions: %s' % Math.thousand(len(result)))
		return path

	##############################################################################
	# UPDATE
	##############################################################################

	def update(self, force = False):
		titleError = '%s %s' % (self.name(), Translation.string(35311))
		titleDownload = '%s %s' % (self.name(), Translation.string(32403))
		try:
			directory = File.joinPath(self.access(), self.id())
			path = self.path()
			pathMeta = self.pathMeta()

			current = None
			if File.exists(pathMeta): current = Converter.jsonFrom(File.readNow(pathMeta))

			if force or not current or Math.randomProbability(ProviderOffline.UpdateProbability):
				links = self.links()

				# Retrieve the meta file.
				meta = None
				for link in links:
					try:
						data = Networker().requestJson(link = link)
						if data and Tools.isDictionary(data) and 'release' in data:
							meta = data
							break
					except: self.logError()
				if not meta:
					Dialog.notification(title = titleError, message = 36367, icon = Dialog.IconError)
					return False

				# Download the dataset.
				if not current or not current['release']['time'] == meta['release']['time']:
					# The minimum space required: download ZIP stored temporarily + extracted database size + at least 100MB free for other OS/Kodi functionality.
					storageRequired = meta['size']['download'] + meta['size']['storage'] + 104857600
					storageFree = Hardware.storageUsageFreeBytes()
					if storageFree and storageFree < storageRequired:
						message = [
							Translation.string(36365),
							'%s: %s' % (Translation.string(36366), ConverterSize(storageRequired).stringOptimal(places = ConverterSize.PlacesNone)),
							'%s: %s' % (Translation.string(33721), ConverterSize(storageFree).stringOptimal(places = ConverterSize.PlacesNone)),
						]
						Dialog.notification(title = titleError, message = Format.iconJoin(message), icon = Dialog.IconError)
						return False

					message = [
						Translation.string(36374 if current else 36373),
						'%s: %s' % (Translation.string(32403), ConverterSize(meta['size']['download']).stringOptimal(places = ConverterSize.PlacesNone)),
						'%s: %s' % (Translation.string(33350), ConverterSize(meta['size']['storage']).stringOptimal(places = ConverterSize.PlacesNone)),
						'%s: %s' % (Translation.string(35222), Math.thousand(meta['size']['count'])),
					]
					Dialog.notification(title = titleDownload, message = Format.iconJoin(message), icon = Dialog.IconInformation)

					File.deleteDirectory(path)
					File.makeDirectory(path)

					id = 1
					for i in range(len(meta['data'])):
						pathTemp1 = System.temporaryRandom(directory = directory, gaia = True, make = True, clear = False)
						pathTemp2 = System.temporary(directory = directory, file = Hash.random(), gaia = True, make = True, clear = False)
						if Networker().download(link = meta['data'][i], path = pathTemp1):
							if Archive.zipDecompress(path = pathTemp1, output = pathTemp2):
								_, files = File.listDirectory(path = pathTemp2, absolute = True)
								for file in files:
									File.move(pathFrom = file, pathTo = self.pathData(id = id), replace = True)
									id += 1
							else:
								Dialog.notification(title = titleError, message = 36369, icon = Dialog.IconError)
								return False
						else:
							Dialog.notification(title = titleError, message = 36368, icon = Dialog.IconError)
							return False

						File.deleteDirectory(System.temporary(directory = directory, gaia = True, make = True, clear = False))
						_, files = File.listDirectory(path = self.path(), absolute = True)
						count = sum([1 if i.endswith(Database.Extension) else 0 for i in files])
						if count == len(meta['data']):
							File.writeNow(pathMeta, Converter.jsonTo(meta))
							if File.exists(pathMeta):
								Dialog.notification(title = titleDownload, message = 36372, icon = Dialog.IconSuccess)
								return True

						Dialog.notification(title = titleError, message = 36370, icon = Dialog.IconError)
						return False
				else:
					return None
			else:
				return None
		except: self.logError()
		Dialog.notification(title = titleError, message = 36371, icon = Dialog.IconError)
		return False
