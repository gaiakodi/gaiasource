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

from lib.providers.core.json import ProviderJson

# https://yts.mx/api

class Provider(ProviderJson):

	_Link					= ['https://yts.lt', 'https://yts.gg', 'https://yts.am', 'https://yts.ag']
	_Mirror					= ['https://yifystatus.com', 'https://ytsproxies.com', 'https://yts.mx/blog/yts-mx-is-the-only-new-official-domain-for-yify-movies']
	_Unblock				= {ProviderJson.UnblockFormat1 : 'yts', ProviderJson.UnblockFormat2 : 'yts', ProviderJson.UnblockFormat3 : 'ytss2', ProviderJson.UnblockFormat4 : 'yts'}
	_Path					= 'api/v2/list_movies.json'

	_LimitOffset			= 50 # The maximum number of results returned by a query.

	_ParameterQuery			= 'query_term'
	_ParameterPage			= 'page'
	_ParameterLimit			= 'limit'
	_ParameterSort			= 'sort_by'
	_ParameterSeeds			= 'seeds'
	_ParameterOrder			= 'order_by'
	_ParameterDescending	= 'desc'
	_ParameterRating		= 'with_rt_ratings'
	_ParameterFalse			= 'false'

	_AttributeData			= 'data'
	_AttributeMovies		= 'movies'
	_AttributeTorrents		= 'torrents'
	_AttributeHash			= 'hash'
	_AttributeSize			= 'size_bytes'
	_AttributeTime			= 'date_uploaded_unix'
	_AttributeSeeds			= 'seeds'
	_AttributeLeeches		= 'peers'
	_AttributeType			= 'type'
	_AttributeQuality		= 'quality'

	_AttributeCount			= 'movie_count'
	_AttributeLimit			= 'limit'
	_AttributePage			= 'page_number'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderJson.initialize(self,
			name					= 'YTS',
			description				= '{name} is one of the oldest and most well-known {container} sites. The API contains results in various languages, but most of them are in English. {name} only indexes movies and does not provide file names for advanced metadata detection. There are only a few results per movie, but scraping is fast and links are usually of good quality. {name} has recently been in the news for handing over user information, based on IP addresses from public torrent trackers, to unauthorized third parties. Inform yourself about this topic and disable the provider if you have concerns. You are safe if you use a debrid service or VPN.',
			rank					= 5,
			performance				= ProviderJson.PerformanceExcellent,

			link					= Provider._Link,
			mirror					= Provider._Mirror,
			unblock					= Provider._Unblock,

			supportMovie			= True,
			supportShow				= False,
			supportPack				= False,

			offsetStart				= 1,
			offsetIncrease			= 1,

			formatEncode			= ProviderJson.FormatEncodeQuote,

			searchQuery				= [
										{
											ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
											ProviderJson.RequestPath : Provider._Path,
											ProviderJson.RequestData : {
												Provider._ParameterQuery	: ProviderJson.TermIdImdb,
												Provider._ParameterPage		: ProviderJson.TermOffset,
												Provider._ParameterLimit	: Provider._LimitOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
												Provider._ParameterOrder	: Provider._ParameterDescending,
												Provider._ParameterRating	: Provider._ParameterFalse,
											},
										},
										{
											ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
											ProviderJson.RequestPath : Provider._Path,
											ProviderJson.RequestData : {
												Provider._ParameterQuery	: ProviderJson.TermQuery,
												Provider._ParameterPage		: ProviderJson.TermOffset,
												Provider._ParameterLimit	: Provider._LimitOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
												Provider._ParameterOrder	: Provider._ParameterDescending,
												Provider._ParameterRating	: Provider._ParameterFalse,
											},
										},
									],

			extractList				= [Provider._AttributeData, Provider._AttributeMovies, Provider._AttributeTorrents],
			extractHash				= Provider._AttributeHash,
			extractFileName			= True,
			extractFileSize			= Provider._AttributeSize,
			extractFileExtra		= [[Provider._AttributeQuality], [Provider._AttributeType]],
			extractSourceTime		= Provider._AttributeTime,
			extractSourceSeeds		= Provider._AttributeSeeds,
			extractSourceLeeches	= Provider._AttributeLeeches,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		data = data[Provider._AttributeData]
		count = data[Provider._AttributeCount]
		limit = data[Provider._AttributeLimit]
		page = data[Provider._AttributePage]
		if count <= (limit * page): return ProviderJson.Skip

	def processReleaseGroup(self, value, item, details = None, entry = None):
		return 'yts'
