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

from lib.providers.core.offline import ProviderOffline

class Provider(ProviderOffline):

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderOffline.initialize(self,
			name				= 'OfflineRar',
			link				= [
									'https://github.com/offlineindexer/data/raw/main/rarbg/meta.json',
									'https://gitlab.com/offlineindexer/data/raw/main/rarbg/meta.json',
								],

			dumpProviderName	= 'RarBG',
			dumpReleaseTime		= 1685577600, # 2023-06-01
			dumpSizeDownload	= 100948659,
			dumpSizeStorage		= 268955648,
			dumpSizeCount		= 1591037,
			dumpLinkWeb			= 'https://rarbg.to',
			dumpLinkSource		= 'https://github.com/2004content/rarbg',
			dumpLinkOrignal		= [
									'https://github.com/2004content/rarbg/raw/main/everything/everything.7z.001',
									'https://github.com/2004content/rarbg/raw/main/everything/everything.7z.002',
									'https://github.com/2004content/rarbg/raw/main/everything/everything.7z.003',
									'https://github.com/2004content/rarbg/raw/main/everything/everything.7z.004',
									'https://github.com/2004content/rarbg/raw/main/everything/everything.7z.005',
								],
			dumpProcessFilter	= ProviderOffline.FilterMagnet,
		)
