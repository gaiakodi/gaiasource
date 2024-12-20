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

# Domain is down and will probably not come back up.
# 	https://github.com/urbanguacamole/torrent-paradise
# 	https://github.com/urbanguacamole/torrent-paradise/issues/45
# The new website is located at:
#	IPFS HASH:
#		QmQjsKamNFZRvCMXDvZXQmRYjsmSkmZG5pBCTY4LtMj8hs
#		Qme21itRkXCq5Comc48FMKURNwRaJguYNeNj6vmxh3fqzd
#	https://cloudflare-ipfs.com/ipfs/<IPFS HASH>/
#	https://ipfs.io/ipfs/<IPFS HASH>/
#	https://dweb.link/ipfs/<IPFS HASH>/
# However, it runs the "ifps"" version where searching is done locally via JS, instead of using the "static" version of the website that does pre-searching and has a JSON API.
# A HTTP API exists, but there sre not useful links returned:
#	https://app.swaggerhub.com/apis-docs/ipfs-search/ipfs-search/1.0.2

#gaiafuture - Does a new domain exist yet?
#gaiafuture - Can we somehow convert the JS on the website to Python?
#gaiafuture - Or maybe even execute the JS in a Python-JS interpreter?
#gaiafuture - Maybe rename this to "TorrentParadised" (ending with a D), and add this as a new one to the "open" category: https://torrentparadise.org / https://torrentparadise.net / https://torrent-paradise.com

from lib.providers.core.json import ProviderJson

class Provider(ProviderJson):

	_Link				= ['https://torrent-paradise.ml']
	_Path				= 'api/search'

	_ParamaterQuery		= 'q'

	_AttributeId		= 'id'
	_AttributeText		= 'text'
	_AttributeLength	= 'len'
	_AttributeSeeds		= 's'
	_AttributeLeeches	= 'l'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderJson.initialize(self,
			name					= 'TorrentParadise',
			description				= '{name} is search engine for the InterPlanetary File System (IPFS) which is a protocol and peer-to-peer network for storing and sharing data in a distributed file system. IPFS is more resilient to censorship and take downs due to its distributed nature.',
			link					= Provider._Link,
			rank					= 5,
			performance				= ProviderJson.PerformanceExcellent,
			status					= ProviderJson.StatusDead,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			searchQuery				= {
										ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
										ProviderJson.RequestPath : Provider._Path,
										ProviderJson.RequestData : {
											Provider._ParamaterQuery : ProviderJson.TermQuery,
										},
									},

			extractHash				= Provider._AttributeId,
			extractFileName			= Provider._AttributeText,
			extractFileSize			= Provider._AttributeLength,
			extractSourceSeeds		= Provider._AttributeSeeds,
			extractSourceLeeches	= Provider._AttributeLeeches,
		)
