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

# https://popcorntime.api-docs.io/api/welcome/introduction
# https://github.com/popcorn-official/popcorn-api
# https://github.com/popcorn-official/popcorn-desktop/wiki/FAQ (listed new domain).

from lib.providers.core.json import ProviderJson
from lib.modules.stream import Stream
from lib.modules.network import Container

class Provider(ProviderJson):

	# https://upaste.me/803c51640d33c812b
	# Only .tk domain works, but keep the other ones in case they come up again.
	# Although movies/shows/anime have different subdomains, it seems all of them can be used to search anything.
	_Link				= [
							'https://shows.cf',
							'https://popcorn-time.ga',
							#'https://popcorn-ru.tk', # Not reachable by some VPNs. Seems to be down.
							#'https://tv-v2.api-fetch.sh',
							#'https://tv-v2.api-fetch.am',
							#'https://tv-v2.api-fetch.website',
						]
	_Path				= '%s/%s'

	_CategoryMovie		= 'movie'
	_CategoryShow		= 'show'

	_AttributeTorrents	= 'torrents'
	_AttributeEpisodes	= 'episodes'
	_AttributeEpisode	= 'episode'
	_AttributeSeason	= 'season'
	_AttributeLink		= 'url'
	_AttributeSize		= 'size'
	_AttributeProvider	= 'provider'
	_AttributeSeeds		= 'seeds'
	_AttributeSeed		= 'seed'
	_AttributeLeeches	= 'peers'
	_AttributeLeech		= 'peer'

	_AttributeQuality	= 'quality'
	_AttributeLanguage	= 'language'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderJson.initialize(self,
			name					= 'PopcornTime',
			description				= '{name} is one of the oldest and most well-known {container} APIs. The API contains results in various languages, but most of them are in English. {name} has few results, but they are of good quality. The API does not have file names and sizes for movies and episodes respectively. {name} might not accessible from some countries or VPNs.',
			rank					= 4,
			performance				= ProviderJson.PerformanceExcellent - ProviderJson.PerformanceStep,

			link					= Provider._Link,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			searchQuery				= Provider._Path % (ProviderJson.TermCategory, ProviderJson.TermIdImdb),
			searchCategoryMovie		= Provider._CategoryMovie,
			searchCategoryShow		= Provider._CategoryShow,

			extractLink				= Provider._AttributeLink,
			extractVideoQuality		= Provider._AttributeQuality,
			extractFileName			= True,
			extractFileExtra		= Provider._AttributeProvider,
			extractFileSize			= Provider._AttributeSize,
			extractSourceSeeds		= Provider._AttributeSeeds,
			extractSourceLeeches	= Provider._AttributeLeeches,
		)

	##############################################################################
	# EXTRACT
	##############################################################################

	def extractList(self, data):
		# Movies and shows have different structures and attribute names.

		items = []
		if self.parameterMediaMovie():
			if data and Provider._AttributeTorrents in data and data[Provider._AttributeTorrents]:
				for language, item in data[Provider._AttributeTorrents].items():
					for quality, item in item.items():
						item[Provider._AttributeLanguage] = language
						item[Provider._AttributeQuality] = quality
						items.append(self._extractQuality(item))
		else:
			season = self.parameterNumberSeason()
			episode = self.parameterNumberEpisode()
			for item in data[Provider._AttributeEpisodes]:
				if item and Provider._AttributeSeason in item and Provider._AttributeEpisode in item and Provider._AttributeTorrents in item:
					if item[Provider._AttributeSeason] == season and item[Provider._AttributeEpisode] == episode:
						if item[Provider._AttributeTorrents]:
							for quality, item in item[Provider._AttributeTorrents].items():
								item[Provider._AttributeQuality] = quality
								items.append(self._extractQuality(item))
						break

		for i in range(len(items)):
			try: items[i][Provider._AttributeSeeds] = items[i][Provider._AttributeSeed]
			except: pass
			try: items[i][Provider._AttributeLeeches] = items[i][Provider._AttributeLeech]
			except: pass

		return items

	def _extractQuality(self, item):
		# Some links have a given quality of 480p, but the file name in the magnet link contains a different quality, and the file size also seems too large for 480p.
		# Eg: Dune (2021)
		#	"480p":	dn=No.Time.To.Die.2021.1080p.AMZN.WEBRip.DDP5.1.Atmos.x264-NOGRP
		if Provider._AttributeLink in item:
			name = Container(item[Provider._AttributeLink]).torrentName()
			if name:
				quality = Stream.videoQualityExtract(name)
				if quality: item[Provider._AttributeQuality] = quality
		return item
