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
from lib.modules.tools import Media
from lib.modules.video import Full

class Provider(ProviderBase):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderBase.initialize(self,
			name			= 'YouTube',
			description		= '{name} is a well-known public streaming website. {name} often returns incorrect streams that are incomplete or contain fan-created content. Only use this provider if other providers find nothing or for content that is released exclusively on {name}.',
			rank			= 2,
			performance		= ProviderBase.PerformanceGood,
			optimization	= False,

			supportMovie	= True,
			supportShow		= True,
			supportPack		= False,

			accountOther	= ProviderBase.AccountInputCustom,
		)

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountVerify(self):
		return Full.verify()

	def accountCustomEnabled(self):
		return Full.enabled()

	def accountSettingsLabel(self):
		return Full.accountLabel()

	def accountCustomDialog(self):
		Full.authentication()

	##############################################################################
	# SEARCH
	##############################################################################

	def search(self, media, titles, years = None, time = None, idImdb = None, idTmdb = None, idTvdb = None, numberSeason = None, numberEpisode = None, language = None, pack = None, exact = None, silent = False, cacheLoad = True, cacheSave = True, hostersAll = None, hostersPremium = None):
		try:
			type = Media.TypeShow if Media.typeTelevision(media) else Media.TypeMovie
			title = titles['search']['main'][0]
			year = years['common']
			if self.queryAllow(type, title, year, numberSeason, numberEpisode):
				streams = Full(type = type).search(title = title, year = year, season = numberSeason, episode = numberEpisode)
				self.statisticsUpdateSearch(page = True, request = True)
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
			sourceApproval = self.streamExtract(stream, 'popularity')
			if sourceApproval: sourceApproval += ProviderBase.ApprovalDefault

			return self.resultStream(
				idProviderUniversal		= self.streamExtract(stream, 'id'),

				link					= self.streamExtract(stream, 'link'),

				videoQualityInexact		= self.streamExtract(stream, 'quality'),
				video3d					= self.streamExtract(stream, '3d'),

				audioLanguage			= self.streamExtract(stream, 'language'),

				subtitleType			= Stream.SubtitleTypeSoft if self.streamExtract(stream, 'subtitle') else Stream.SubtitleTypeNone,

				fileName				= self.streamExtract(stream, 'name'),

				releaseUploader			= self.streamExtract(stream, 'channel'),

				sourceType				= Stream.SourceTypeHoster,
				sourceTime				= self.streamExtract(stream, 'time'),
				sourceApproval			= sourceApproval,
			)
		except: self.logError()

	def streamExtract(self, data, *keys):
		try:
			for key in keys: data = data[key]
			return data
		except: return None
