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
from lib.modules.tools import System, Media, File, Matcher, Converter, Tools
from lib.modules.network import Networker
from lib.modules.stream import Stream
from lib.modules.library import Library

class Provider(ProviderBase):

	_Match				= 0.7 # Minimum title match ratio.

	_CustomStrmStream	= 'strmstream'
	_CustomStrmScrape	= 'strmscrape'
	_CustomStrmAddon	= 'strmaddon'
	_CustomStrmLocal	= 'strmlocal'
	_CustomStrmNetwork	= 'strmnetwork'
	_CustomStrmOnline	= 'strmonline'
	_CustomFileLocal	= 'filelocal'
	_CustomFileNetwork	= 'filelnetwork'
	_CustomFileOnline	= 'filelonline'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderBase.initialize(self,
			name			= 'LocalLibrary',
			description		= 'Search the local Kodi library for content that was previously added to it.',
			rank			= 5,
			performance		= ProviderBase.PerformanceGood,
			optimization	= True,

			supportMovie	= True,
			supportShow		= True,
			supportPack		= False,

			custom			= [
								{
									ProviderBase.SettingsId				: Provider._CustomStrmStream,
									ProviderBase.SettingsLabel			: 'Gaia Stream STRM',
									ProviderBase.SettingsDefault		: True,
									ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
									ProviderBase.SettingsDescription	: 'Include STRM files that point to a Gaia streamable file. These STRM files are created if you add a stream link to your local library through Gaia.',
								},
								{
									ProviderBase.SettingsId				: Provider._CustomStrmScrape,
									ProviderBase.SettingsLabel			: 'Gaia Scrape STRM',
									ProviderBase.SettingsDefault		: False,
									ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
									ProviderBase.SettingsDescription	: 'Include STRM files that point to a Gaia scrape processs. These STRM files are created if you add a movie, show, season, or episode to your local library through Gaia.',
								},
								{
									ProviderBase.SettingsId				: Provider._CustomStrmAddon,
									ProviderBase.SettingsLabel			: 'Addon STRM',
									ProviderBase.SettingsDefault		: True,
									ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
									ProviderBase.SettingsDescription	: 'Include STRM files that point to an external addon other than Gaia. These STRM files are created by other Kodi addons.',
								},
								{
									ProviderBase.SettingsId				: Provider._CustomStrmLocal,
									ProviderBase.SettingsLabel			: 'Local STRM',
									ProviderBase.SettingsDefault		: True,
									ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
									ProviderBase.SettingsDescription	: 'Include STRM files that point to file on the local drive.',
								},
								{
									ProviderBase.SettingsId				: Provider._CustomStrmNetwork,
									ProviderBase.SettingsLabel			: 'Network STRM',
									ProviderBase.SettingsDefault		: True,
									ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
									ProviderBase.SettingsDescription	: 'Include STRM files that point to a file on the local network.',
								},
								{
									ProviderBase.SettingsId				: Provider._CustomStrmOnline,
									ProviderBase.SettingsLabel			: 'Online STRM',
									ProviderBase.SettingsDefault		: True,
									ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
									ProviderBase.SettingsDescription	: 'Include STRM files that point to an online link. This includes HTTP, FTP, and magnet links.',
								},
								{
									ProviderBase.SettingsId				: Provider._CustomFileLocal,
									ProviderBase.SettingsLabel			: 'Local File',
									ProviderBase.SettingsDefault		: True,
									ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
									ProviderBase.SettingsDescription	: 'Include files from the local drive. This includes all local files that are not stored as an STRM.',
								},
								{
									ProviderBase.SettingsId				: Provider._CustomFileNetwork,
									ProviderBase.SettingsLabel			: 'Network File',
									ProviderBase.SettingsDefault		: True,
									ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
									ProviderBase.SettingsDescription	: 'Include files from the local network. This includes all network files that are not stored as an STRM.',
								},
								{
									ProviderBase.SettingsId				: Provider._CustomFileOnline,
									ProviderBase.SettingsLabel			: 'Online File',
									ProviderBase.SettingsDefault		: True,
									ProviderBase.SettingsType			: ProviderBase.SettingsTypeBoolean,
									ProviderBase.SettingsDescription	: 'Include files that point to an online link. This includes HTTP, FTP, and magnet links that are not stored as an STRM.',
								},
							],
		)

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media = None, niche = None, titles = None, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		lock = None
		try:
			# Cannot search the library by IMDb ID for some reason.
			# The RPC always returns an error: Received value does not match any of the union type definitions.

			yearsNew = []
			if years and 'all' in years and years['all']:
				for year in years['all']:
					yearsNew.extend([year, year - 1, year + 1])
				yearsNew = Tools.listUnique(yearsNew)
			years = yearsNew

			# The IMDb ID of items in the library can be the IMDb, TMDb, or TVDb ID, depending on the scraper the user selected.
			# That means that the TMDb ID of shows passed into this function can be None, and we can therefore not rely on the ID only.
			# If the ID matches, we accept the results without validating the file name in Streams.
			# If no ID is matches, we filter by file name and let Streams validate it.
			ids = {}
			if idImdb: ids['imdb'] = idImdb
			if idTmdb: ids['tmdb'] = idTmdb
			if idTvdb: ids['tvdb'] = idTvdb

			filter = []
			if years:
				filter.extend([{'field' : 'year', 'operator' : 'is', 'value' : '%d' % i} for i in years])
			else:
				for title in titles['search'].values():
					if not Tools.isArray(title): title = [title]
					filter.extend([{'field' : 'title', 'operator' : 'contains', 'value' : '%s' % i} for i in title])
					filter.extend([{'field' : 'originaltitle', 'operator' : 'contains', 'value' : '%s' % i} for i in title])
			filter = {'or': filter}

			self.statisticsUpdateSearch(page = True)
			if Media.isSerie(media):
				results = self.searchJson(method = 'VideoLibrary.GetTVShows', parameters = {'filter' : filter, 'properties': ['uniqueid', 'imdbnumber', 'title', 'originaltitle']})
				if 'result' in results and 'tvshows' in results['result']:
					results = results['result']['tvshows']
					for result in results:
						matchId, matchTitle = self.searchMatch(result = result, titles = titles, ids = ids)
						if not matchId and not matchTitle: continue
						if numberSeason and numberEpisode:
							filter = {'and' : [
								{'field' : 'season', 'operator' : 'is', 'value' : '%d' % numberSeason},
								{'field' : 'episode', 'operator' : 'is', 'value' : '%d' % numberEpisode},
							]}
						result = self.searchJson(method = 'VideoLibrary.GetEpisodes', parameters = {'filter' : filter, 'tvshowid' : result['tvshowid'], 'properties': ['file']})
						if 'result' in result and 'episodes' in result['result']:
							result = self.searchFilter(result['result']['episodes'])

							chunks = self.priorityChunks(result)
							for chunk in chunks:
								lock = self.priorityStart(lock = lock)
								for res in chunk:
									res = self.searchJson(method = 'VideoLibrary.GetEpisodeDetails', parameters = {'episodeid' : res['episodeid'], 'properties': ['streamdetails', 'file']})
									if 'result' in res and 'episodedetails' in res['result']:
										res = res['result']['episodedetails']
										self.searchProcess(match = matchId, result = res, media = media, titles = titles, years = years, numberSeason = numberSeason, numberEpisode = numberEpisode, numberPack = numberPack, language = language, country = country, network = network, studio = studio, pack = pack)
								self.priorityEnd(lock = lock)
			else:
				results = self.searchJson(method = 'VideoLibrary.GetMovies', parameters = {'filter' : filter, 'properties': ['uniqueid', 'imdbnumber', 'title', 'originaltitle', 'file']})
				if 'result' in results and 'movies' in results['result']:
					results = self.searchFilter(results['result']['movies'])

					chunks = self.priorityChunks(results)
					for chunk in chunks:
						lock = self.priorityStart(lock = lock)
						for result in chunk:
							matchId, matchTitle = self.searchMatch(result = result, titles = titles, ids = ids)
							if not matchId and not matchTitle: continue
							result = self.searchJson(method = 'VideoLibrary.GetMovieDetails', parameters = {'movieid' : result['movieid'], 'properties': ['streamdetails', 'file']})
							if 'result' in result and 'moviedetails' in result['result']:
								result = result['result']['moviedetails']
								self.searchProcess(match = matchId, result = result, media = media, titles = titles, years = years, numberSeason = numberSeason, numberEpisode = numberEpisode, numberPack = numberPack, language = language, country = country, network = network, studio = studio, pack = pack)
						self.priorityEnd(lock = lock)

		except: self.logError()
		finally: self.priorityEnd(lock = lock)

	def searchJson(self, method, parameters):
		result = System.executeJson(method = method, parameters = parameters)
		self.statisticsUpdateSearch(request = True)
		return result

	def searchMatch(self, result, titles, ids):
		matchId = False
		matchTitle = False

		if 'uniqueid' in result and result['uniqueid']:
			for key, value in ids.items():
				if key in result['uniqueid'] and result['uniqueid'][key] == value:
					matchId = True
					break

		if not matchId: matchId = 'imdbnumber' in result and result['imdbnumber'] in ids.values()

		if not matchId:
			for title in titles['processed']['all']:
				for value in ['title', 'originaltitle']:
					if value in result and result[value] and Matcher.levenshtein(title, result[value]) > Provider._Match:
						matchTitle = True
						break
			if not matchTitle:
				for title in titles['processed']['all']:
					if 'label' in result and result['label'] and Matcher.levenshtein(title, result['label']) > Provider._Match:
						matchTitle = True
						break
			if not matchTitle:
				for title in titles['processed']['all']:
					if 'file' in result and result['file'] and Matcher.levenshtein(title, File.name(result['file'])) > Provider._Match:
						matchTitle = True
						break

		return matchId, matchTitle

	def searchFilter(self, files):
		strmStream = self.custom(id = Provider._CustomStrmStream)
		strmScrape = self.custom(id = Provider._CustomStrmScrape)
		strmAddon = self.custom(id = Provider._CustomStrmAddon)
		strmLocal = self.custom(id = Provider._CustomStrmLocal)
		strmNetwork = self.custom(id = Provider._CustomStrmNetwork)
		strmOnline = self.custom(id = Provider._CustomStrmOnline)
		fileLocal = self.custom(id = Provider._CustomFileLocal)
		fileNetwork = self.custom(id = Provider._CustomFileNetwork)
		fileOnline = self.custom(id = Provider._CustomFileOnline)

		pluginGaia = System.plugin()
		pluginAddon = System.plugin(id = '')

		result = []
		for file in files:
			try:
				path = file['file']
				if Library.pathStrm(path):
					data = File.readNow(path)
					if data:
						command = System.commandResolve(command = data, initialize = False)
						data = data.lower()
						if data.startswith(pluginGaia):
							if command and 'action' in command and command['action'] == 'scrape':
								if strmScrape: result.append(file)
							else:
								if strmStream: result.append(file)
						elif data.startswith(pluginAddon):
							if strmAddon: result.append(file)
						elif Networker.linkIs(data, magnet = True):
							if strmOnline: result.append(file)
						elif File.samba(data):
							if strmNetwork: result.append(file)
						else:
							if strmLocal: result.append(file)
				else:
					if Networker.linkIs(path, magnet = True):
						if fileOnline: result.append(file)
					elif File.samba(path):
						if fileNetwork: result.append(file)
					else:
						if fileLocal: result.append(file)
			except: self.logError()

		return result

	def searchExtract(self, path):
		# Load the stream data from a Gaia .strm file added to the library previously.
		try:
			if Library.pathStrm(path):
				data = Library().resolveMeta(path)
				if data:
					parameters = System.commandResolve(command = data, initialize = False)
					if 'source' in parameters:
						source = parameters['source']
						if 'stream' in source: return source['stream']
		except: self.logError()
		return None

	def searchValid(self, value):
		return value and not value == 'und'

	def searchValue(self, values, key):
		result = None
		if key in values:
			value = values[key]
			if self.searchValid(value): result = value
		return result

	def searchProcess(self, match, result, media, titles, years = None, numberSeason = None, numberEpisode = None, numberPack = None, language = None, country = None, network = None, studio = None, pack = None):
		videoWidth = None
		videoHeight = None
		videoAspect = None
		videoCodec = None
		video3d = None
		total = len(result['streamdetails']['video'])
		for i in range(total):
			video = result['streamdetails']['video'][i]
			width = self.searchValue(video, 'width')
			height = self.searchValue(video, 'height')
			if (width and height) or i == (total - 1):
				videoWidth = width
				videoHeight = height
				videoAspect = self.searchValue(video, 'aspect')
				videoCodec = self.searchValue(video, 'codec')
				video3d = self.searchValue(video, 'stereomode')
				if not video3d: video3d = self.searchValue(video, 'stereoscopicmode')
				break

		audioChannels = None
		audioCodec = None
		audioLanguage = []
		for audio in result['streamdetails']['audio']:
			channels = self.searchValue(audio, 'channels')
			if channels and (not audioChannels or channels > audioChannels):
				audioChannels = channels
				codec = self.searchValue(audio, 'codec')
				if codec: audioCodec = codec
			if not audioCodec: audioCodec = self.searchValue(audio, 'codec')
			language = self.searchValue(audio, 'language')
			if language: audioLanguage.append(language)

		subtitleLanguage = []
		for subtitle in result['streamdetails']['subtitle']:
			language = self.searchValue(subtitle, 'language')
			if language: subtitleLanguage.append(language)

		link = result['file']
		data = self.searchExtract(link)

		strm = link.lower().endswith(Library.ExtensionStrm)
		fileName = None
		fileSize = None
		sourceTime = None
		try: fileName = File.name(path = link, extension = True)
		except: pass
		try:
			if not strm: fileSize = File.size(path = link)
		except: pass
		try: sourceTime = File.timeCreated(path = link)
		except: pass

		if data:
			stream = self.resultStream(
				validate = not match,
				validateSize = False,
				data = data,
			)
		else:
			stream = self.resultStream(
				validate = not match,
				validateSize = False,
				extractor = not Networker.linkIs(link) and not strm,

				link = link,

				videoWidth = videoWidth,
				videoHeight = videoHeight,
				videoAspect = videoAspect,
				videoCodec = videoCodec,
				video3d = video3d,

				audioChannels = audioChannels,
				audioSystem = audioCodec,
				audioCodec = audioCodec,
				audioLanguage = audioLanguage,

				subtitleLanguage = subtitleLanguage,

				fileName = fileName,
				fileSize = fileSize,

				sourceType = Stream.SourceTypeLocal,
				sourceTime = sourceTime,
				sourcePopularity = 1,
			)
		if stream: self.resultAdd(stream)
