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
from lib.modules.stream import Stream

class ProviderCenter(ProviderBase):

	def __init__(self, **kwargs):
		ProviderBase.__init__(self, **kwargs)

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		name			= None,
		description		= None,
		rank			= 5,
		performance		= ProviderBase.PerformanceGood,

		supportMovie	= True,
		supportShow		= True,
		supportPack		= False,

		core			= None,
		**kwargs
	):
		self.mCore = core
		self.mCore.serverInitialize(servers = self.account())

		if not name: name = self.mCore.name()

		description = '{name} is a locally or remotely hosted media server designed to organize, play, and stream audio and video to a variety of devices. The media server can be used in a browser or through an app, but can also be accessed through an API. {name} typically requires a premium membership, since files are hosted on private servers.' + ((' ' + description) if description else '')

		ProviderBase.initialize(self,
			name			= name,
			description		= description,
			rank			= rank,
			performance		= performance,

			supportMovie	= supportMovie,
			supportShow		= supportShow,
			supportPack		= supportPack,

			accountOther	= ProviderBase.AccountInputCustom,

			**kwargs
		)

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountVerify(self):
		result = self.mCore.serverVerify()
		if result is None: return ProviderBase.VerifyLimited
		elif result: return ProviderBase.VerifySuccess
		else: return ProviderBase.VerifyFailure

	def accountCustomEnabled(self):
		return self.mCore.serverValid()

	def accountSettingsLabel(self):
		from lib.modules.interface import Translation, Format
		if not self.mCore.serverHas(): return None
		elif self.mCore.serverValid(): return Translation.string(33216)
		else: return Format.fontItalic(33642) # Server added, but the user authentication failed.

	def accountCustomDialog(self):
		return self.mCore.serverSettings()

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, language = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		try:
			title = titles['search']['main']
			year = years
			try: year = years['all']
			except: self.logError()

			if self.queryAllow(media, title, year, numberSeason, numberEpisode, exact):
				streams = self.mCore.search(media = media, title = title, year = year, numberSeason = numberSeason, numberEpisode = numberEpisode, exact = exact)
				self.statisticsUpdateSearch(request = len(title), page = len(title))
				if streams:
					for stream in streams:
						stream = self.stream(stream = stream)
						if stream: self.resultAdd(stream)
		except: self.logError()

	##############################################################################
	# STREAM
	##############################################################################

	def stream(self, stream):
		try:
			releaseFormat = Stream.ReleaseFormatNone
			fileContainer = Stream.FileContainerNone
			fileSize = None
			fileSizeInexact = None
			if stream['stream']['type'] == self.mCore.TypeOriginal:
				fileSize = stream['file']['size']
				releaseFormat = Stream.ReleaseFormatOriginal
			elif stream['stream']['type'] == self.mCore.TypeTranscoded:
				fileContainer = stream['file']['container']
				fileSizeInexact = stream['file']['size']
				releaseFormat = Stream.ReleaseFormatTranscoded

			result = self.resultStream(
				# Do not validate here, since it was already validated while making API calls.
				# Although most Emby servers seem to have the title/year in the file name, it might not always be the case, causing validation to fail here.
				# For instance, the server admin might create a directory with the title/year and have separate quality videos in there that do not contain the titl/year in the file name.
				validate				= False,

				# NOT the item ID, since there can be multiple streams under the same item.
				# This would then make the streams all generate the same ID with Stream.idGaiaGenerate().
				idProviderLocal			= stream['id']['source'],
				idProviderItem			= stream['id']['source'] + '_' + str(stream['stream']['type']),

				link					= stream['stream']['link'],

				subtitleType			= stream['subtitle']['type'],
				subtitleLanguage		= stream['subtitle']['language'],

				fileName				= stream['file']['name'],
				fileSize				= fileSize,
				fileSizeInexact			= fileSizeInexact,

				sourceType				= Stream.SourceTypePremium,
				sourceOrigin			= self.mCore.name(),
				sourceProvider			= stream['stream']['source'],
				sourceApproval			= 1.0,

				accessDirect			= True,
				accessMember			= True,
			)

			if result:
				# Sometimes the metadata extracted from the file name are different to the valuess below.
				# Eg: the file name might  contain the number of audio channels from the default/first audio stream, but a different sstream might be used.

				if stream['video']['width']: result.videoWidthSet(stream['video']['width'])
				if stream['video']['height']: result.videoHeightSet(stream['video']['height'])
				if stream['video']['quality']: result.videoQualitySet(stream['video']['quality'])
				if stream['video']['codec']: result.videoCodecSet(stream['video']['codec'])
				if stream['video']['range']: result.videoRangeSet(stream['video']['range'])
				if stream['video']['depth']: result.videoDepthSet(stream['video']['depth'])
				if stream['video']['3d']: result.video3dSet(stream['video']['3d'])

				if stream['audio']['codec']:
					result.audioSystemSet(stream['audio']['codec'])
					result.audioCodecSet(stream['audio']['codec'])
				if stream['audio']['channels']: result.audioChannelsSet(stream['audio']['channels'])
				if stream['audio']['language']: result.audioLanguageSet(stream['audio']['language'])

				if stream['subtitle']['type']: result.subtitleTypeSet(stream['subtitle']['type'])
				if stream['subtitle']['language']: result.subtitleLanguageSet(stream['subtitle']['language'])

				if fileContainer: result.fileContainerSet(fileContainer, extract = False) # "TS" is not extracted as fileContainer, since it also means TeleSync.
				if releaseFormat: result.releaseFormatSet(releaseFormat, extract = False)

			return result
		except: self.logError()
