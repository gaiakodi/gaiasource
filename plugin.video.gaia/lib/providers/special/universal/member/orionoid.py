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
from lib.modules.orionoid import Orionoid
from lib.modules.stream import Stream
from lib.modules.tools import Media, Hardware, Math, Converter

class Provider(ProviderBase):

	_CustomExtract		= 'extract'
	_CustomFilters		= 'filters'
	_CustomAutomatic	= None
	_CustomEnabled		= True
	_CustomDisabled		= False

	_Anonymous			= 'anonymous'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderBase.initialize(self,
			name				= 'Orion',
			description			= '{name} is a torrent, usenet, and hoster indexer with a huge database of links and metadata. Free and premium accounts are available. The {name} addon must be installed for this provider to work. Account authentication and search filters are available in the {name} addon settings.',
			rank				= 5,
			performance			= ProviderBase.PerformanceExcellent,
			optimization		= True,

			# Allows settings to be opened from manager.py.
			addonModuleScraper	= Orionoid.addonId(),
			addonSettings		= True,

			supportMovie		= True,
			supportShow			= True,
			supportPack			= False,

			accountOther		= ProviderBase.AccountInputCustom,

			custom				= [
									{
										ProviderBase.SettingsId				: Provider._CustomFilters,
										ProviderBase.SettingsLabel			: 'Search Filters',
										ProviderBase.SettingsDefault		: None,
										ProviderBase.SettingsType			: ProviderBase.SettingsTypeCustom,
										ProviderBase.SettingsFormat			: {ProviderBase.SettingsValueDefault : 35233},
										ProviderBase.SettingsDescription	: 'Customize the search filters that are used for scraping Orion.',
									},
									{
										ProviderBase.SettingsId				: Provider._CustomExtract,
										ProviderBase.SettingsLabel			: 'Extract Metadata',
										ProviderBase.SettingsDefault		: Provider._CustomAutomatic,
										ProviderBase.SettingsType			: [{Provider._CustomAutomatic : 33800}, {Provider._CustomEnabled : 32301}, {Provider._CustomDisabled : 32302}],
										ProviderBase.SettingsDescription	: 'Extract additional metadata from the file name, besides the metadata already provided by Orion. The extraction will yield more accurate metadata, but will also increase the scraping time. [I]Automatic[/I]  will optimize the extraction based on your device\'s hardware and the number of streams returned. If the Orion provider is slow, try to disabling extraction.',
									},
								],
		)

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountVerify(self):
		try: return Orionoid().accountValid()
		except: return False

	def accountCustomEnabled(self):
		try: return Orionoid().accountEnabled()
		except: return False

	def accountSettingsLabel(self):
		try: return Orionoid().accountLabel()
		except: return None

	def accountCustomDialog(self):
		#try: Orionoid().accountLogin()
		#except: pass

		# Allows the addon to be installed if currently disabled.
		try:
			from lib.modules.account import Orion as Account
			orion = Orionoid()
			installed = orion.addonInstalled()
			result = Account().authenticate(settings = False)

			# The "Orionoid" class is still the old one before the addon was installed, and can therefore not access the actual Orion addon until the Python Invoker is restarted.
			# The account details/label will therefore not be available and will look to the user as if the authentication was unsuccessful.
			# Show a message asking the user to restart the settings dialog for the authentication to take effect.
			# This is not very user friendly, but should not happen very often, since most users will not disable the Orion addon.
			if not installed and orion.addonInstalled():
				from lib.modules.interface import Dialog
				Dialog.confirm(title = self.name(), message = 36241)
		except: self.logError()

	##############################################################################
	# CUSTOM
	##############################################################################

	def customExecute(self, id = None):
		if id == Provider._CustomFilters:
			try: Orionoid().settingsLaunch(category = Orionoid.SettingsAddonFilters, app = True, wait = True)
			except: pass
			return None

	##############################################################################
	# VEIFY
	##############################################################################

	def verifyScrapeStatus(self):
		# Mark as limited if the daily usage limit was reached.
		result = ProviderBase.VerifyLimited if Orionoid().requestsLimited() else ProviderBase.VerifyFailure
		reason = None
		return result, reason

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, language = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		lock = None
		try:
			type = Orionoid.TypeShow if Media.typeTelevision(media) else Orionoid.TypeMovie
			title = titles['search']['main'][0]
			year = None
			try: year = years['common']
			except: self.logError()
			query = title if exact else None

			if self.queryAllow(type, query, idImdb, idTmdb, idTvdb, title, year, numberSeason, numberEpisode):
				streams = Orionoid(silent = silent).streamRetrieve(type = type, query = query, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, title = title, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, verify = self.verifyBusy())
				self.statisticsUpdateSearch(request = True, page = True)
				if streams:
					data = streams
					streams = streams['streams']
					extract = self.extract(streams = streams)

					chunks = self.priorityChunks(streams)
					for chunk in chunks:
						lock = self.priorityStart(lock = lock)
						for stream in chunk:
							stream = self.stream(data = data, stream = stream, extract = extract, media = media, titles = titles, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, language = language, pack = pack)
							if stream: self.resultAdd(stream)
						self.priorityEnd(lock = lock)
		except: self.logError()
		finally: self.priorityEnd(lock = lock)

	##############################################################################
	# EXTRACT
	##############################################################################

	# gaiaremove - this we should be able to remove (make "extract = False") when Orion has updated its database/metadata in the future.
	def extract(self, streams):
		extract = Provider._CustomEnabled
		try:
			extract = self.custom(Provider._CustomExtract)
			if extract is Provider._CustomAutomatic:
				performance = Hardware.performance()
				limit = Math.scale(value = performance['rating'], fromMinimum = 0, fromMaximum = 1, toMinimum = 500, toMaximum = 3000)
				if not performance['performance'] == Hardware.PerformanceExcellent and len(streams) > limit: extract = Provider._CustomDisabled
				else: extract = Provider._CustomEnabled
		except:	self.logError()
		return extract

	##############################################################################
	# STREAM
	##############################################################################

	def stream(self, data, stream, extract, media, titles, year, numberSeason, numberEpisode, language, pack):
		try:
			television = Media.typeTelevision(media)
			sourceType = self.streamExtract(stream, 'stream', 'type')

			packSeason = None
			if television and pack:
				for season in pack['seasons']:
					if season['number'] == numberSeason:
						packSeason = season
						break

			link = self.streamExtract(stream, 'links')
			hash = self.streamExtract(stream, 'file', 'hash')

			timeUpdated = self.streamExtract(stream, 'time', 'updated')

			fileName = self.streamExtract(stream, 'file', 'name')
			fileSize = self.streamExtract(stream, 'file', 'size')
			fileSizeOriginal = fileSize
			fileSizeInexact = None
			filePack = self.streamExtract(stream, 'file', 'pack')

			videoQuality = self.streamExtract(stream, 'video', 'quality')
			videoCodec = self.streamExtract(stream, 'video', 'codec')
			video3d = self.streamExtract(stream, 'video', '3d')

			audioType = self.streamExtract(stream, 'audio', 'type')
			audioSystem = self.streamExtract(stream, 'audio', 'system')
			audioCodec = self.streamExtract(stream, 'audio', 'codec')

			audioLanguage = self.streamExtract(stream, 'audio', 'languages')
			audioChannels = self.streamExtract(stream, 'audio', 'channels')

			subtitleType = self.streamExtract(stream, 'subtitle', 'type')
			subtitleLanguage = self.streamExtract(stream, 'subtitle', 'languages')

			sourceOrigin = self.streamExtract(stream, 'stream', 'origin')
			sourceHoster = self.streamExtract(stream, 'stream', 'hoster')
			sourceProvider = self.streamExtract(stream, 'stream', 'source')

			sourceSeeds = self.streamExtract(stream, 'stream', 'seeds')
			sourceLeeches = self.streamExtract(stream, 'stream', 'leeches')

			sourceTime = self.streamExtract(stream, 'stream', 'time')
			if not sourceTime: sourceTime = self.streamExtract(stream, 'time', 'updated')

			sourceApproval = self.streamExtract(stream, 'popularity', 'percent')
			if sourceApproval: sourceApproval += ProviderBase.ApprovalDefault

			releaseType = self.streamExtract(stream, 'meta', 'release')
			releaseEdition = self.streamExtract(stream, 'meta', 'edition')
			releaseGroup = self.streamExtract(stream, 'meta', 'uploader')

			accessCache = {}
			access = self.streamExtract(stream, 'access')
			if access:
				try: accessCache[Stream.AccessDebridPremiumize] = access[Stream.AccessDebridPremiumize]
				except: pass
				try: accessCache[Stream.AccessDebridOffcloud] = access[Stream.AccessDebridOffcloud]
				except: pass
				try: accessCache[Stream.AccessDebridRealdebrid] = access[Stream.AccessDebridRealdebrid]
				except: pass
				try: accessCache[Stream.AccessDebridAlldebrid] = access[Stream.AccessDebridAlldebrid]
				except: pass
				try: accessCache[Stream.AccessDebridDebridlink] = access[Stream.AccessDebridDebridlink]
				except: pass
			accessDirect = self.streamExtract(stream, 'access', 'direct')

			idData = Stream.idOrionDataGenerate(
				link				= link[0],
				hash				= hash,

				videoQuality		= videoQuality,
				videoCodec			= videoCodec,
				video3d				= video3d,

				audioType			= audioType,
				audioSystem			= audioSystem,
				audioCodec			= audioCodec,
				audioChannels		= audioChannels,
				audioLanguage		= audioLanguage,

				subtitleType		= subtitleType,
				subtitleLanguage	= subtitleLanguage,

				fileName			= fileName,
				fileSize			= fileSize,
				filePack			= filePack,

				releaseType			= releaseType,
				releaseEdition		= releaseEdition,
				releaseGroup		= releaseGroup,

				sourceType			= sourceType,
				sourceTime			= sourceTime,
				sourceSeeds			= sourceSeeds,

				sourceOrigin		= sourceOrigin,
				sourceProvider		= sourceProvider,
				sourceHoster		= sourceHoster,
			)

			# Do after the ID was generated.

			videoQuality = Orionoid.map(value = videoQuality, category = 'video', attribute = 'quality')
			videoCodec = Orionoid.map(value = videoCodec, category = 'video', attribute = 'codec')
			video3d = Orionoid.map(value = video3d, category = 'video', attribute = '3d')

			audioType = Orionoid.map(value = audioType, category = 'audio', attribute = 'type')
			audioSystem = Orionoid.map(value = audioSystem, category = 'audio', attribute = 'system')
			audioCodec = Orionoid.map(value = audioCodec, category = 'audio', attribute = 'codec')
			if audioChannels == 2 and (fileName or sourceType == Orionoid.StreamHoster): audioChannels = None # Old Orion set 2CH by default if no channels were detected.

			subtitleType = Orionoid.map(value = subtitleType, category = 'subtitle', attribute = 'type')

			sourceType = Orionoid.map(value = sourceType, category = 'source', attribute = 'type')
			if sourceProvider and sourceProvider == Provider._Anonymous: sourceProvider = sourceHoster # Use the hoste if the provider/source is "anonymous".
			if sourceHoster and (sourceHoster == Provider._Anonymous or sourceType == Orionoid.StreamTorrent or sourceType == Orionoid.StreamUsenet): sourceHoster = None # Some torrent providers marked the hoster as "anonymous".

			filePack = Orionoid.map(value = filePack, category = 'file', attribute = 'pack')

			# Orion estimates the file size for packs.
			# Try to get as close as possible to ther original size.
			if filePack:
				if television:
					filePack = Stream.FilePackSeason
					try:
						try: counter = packSeason['count']
						except: counter = pack['count']['mean']['main']
						fileSizeInexact = fileSize
						if counter: fileSize *= counter
					except:
						fileSizeInexact = fileSize
						fileSize = None
				else:
					filePack = Stream.FilePackCollection
					try:
						fileSizeInexact = fileSize
						fileSize *= pack['count']
					except:
						fileSizeInexact = fileSize
						fileSize = None

			if extract:
				videoCodec = None # Does not have all codecs.
				video3d = None # Only has boolean for 3D and not the 3D type.

				audioType = None
				audioSystem = None
				audioCodec = None
				audioChannels = None
				audioLanguage = None

				subtitleType = None
				subtitleLanguage = None

				filePack = None

				releaseType = None
				releaseEdition = None
				releaseGroup = None

			streamy = self.resultStream(
				validateTitle			= False,
				validateYear			= False,
				validateShow			= False,
				extract					= extract,

				idOrionStream			= self.streamExtract(stream, 'id'),
				idOrionMovie			= self.streamExtract(data, 'movie', 'id', 'orion'),
				idOrionCollection		= self.streamExtract(data, 'collection', 'id', 'orion'),
				idOrionShow				= self.streamExtract(data, 'show', 'id', 'orion'),
				idOrionSeason			= self.streamExtract(data, 'season', 'id', 'orion'),
				idOrionEpisode			= self.streamExtract(data, 'episode', 'id', 'orion'),
				idOrionData				= idData,

				link					= link,
				hash					= hash,

				videoQualityInexact		= videoQuality,
				videoCodec				= videoCodec,
				video3d					= video3d,

				audioType				= audioType,
				audioSystem				= audioSystem,
				audioCodec				= audioCodec,
				audioChannels			= audioChannels,
				audioLanguage			= audioLanguage,

				subtitleType			= subtitleType,
				subtitleLanguage		= subtitleLanguage,

				fileName				= fileName,
				fileSize				= fileSize,
				fileSizeInexact			= fileSizeInexact,
				filePack				= filePack,

				releaseType				= releaseType,
				releaseEdition			= releaseEdition,
				releaseGroup			= releaseGroup,

				sourceType				= sourceType,
				sourceTime				= sourceTime,
				sourceApproval			= sourceApproval,
				sourceSeeds				= sourceSeeds,
				sourceLeeches			= sourceLeeches,

				sourceOrigin			= sourceOrigin,
				sourceProvider			= sourceProvider,
				sourceHoster			= sourceHoster,

				accessOrion				= True,
				accessDirect			= accessDirect,
				accessCacheInexact		= accessCache,
			)

			if streamy:
				# Estimate the file size for show and episode packs.
				if streamy.filePack() and television:
					if timeUpdated and timeUpdated > 1646870400: # Ignore for old streams.
						counter = 0
						number = streamy.numberShow()
						if len(number['season']) > 1:
							counter = 0
							for i in number['season']:
								try: counter += packSeason['count']
								except: counter += pack['count']['mean']['main']
						elif len(number['episode']) > 1:
							counter = len(number['episode'])
						if counter:
							try:
								fileSizeInexact = fileSizeOriginal
								fileSize = fileSizeOriginal * counter
								streamy.fileSizeSet(value = fileSizeInexact, exact = Stream.ExactNo)
								streamy.fileSizeSet(value = fileSize, exact = Stream.ExactYes)
							except: pass

				if streamy.audioChannels() is None and not audioChannels is None: streamy.audioChannelsSet(audioChannels)
			else:
				self.log('Invalid stream data: ' + Converter.jsonTo(stream))

			return streamy
		except: self.logError()

	def streamExtract(self, data, *keys):
		try:
			for key in keys: data = data[key]
			return data
		except:
			return None
