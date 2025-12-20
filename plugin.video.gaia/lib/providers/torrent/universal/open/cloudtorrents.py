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
from lib.modules.tools import Time

# NB: CloudTorrents can contain duplicates in the results, same torrent from different source sites.

class Provider(ProviderJson):

	_Link					= ['https://api.cloudtorrents.com']
	_Path					= 'search'

	_LimitOffset			= 50 # 50 is the maximum.
	_LimitApproval			= 5000

	_CategoryMovie			= ['5', '1'] # 5 = Movies, 1 = Anime
	_CategoryShow			= ['8', '1'] # 8 = TV, 1 = Anime

	_ParameterQuery			= 'query'
	_ParameterCategory		= 'torrent_type'
	_ParameterLimit			= 'limit'
	_ParameterOffset		= 'offset'
	_ParameterSort			= 'ordering'
	_ParameterSeeds			= '-se'

	_AttributeList			= 'results'
	_AttributeItem			= 'torrent'
	_AttributeMeta			= 'torrentMetadata'
	_AttributeLink			= 'torrentMagnet'
	_AttributeHash			= 'torrentHash'
	_AttributeName			= 'name'
	_AttributeSize			= 'size'
	_AttributeTime			= 'uploadedAt'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeDownloads		= 'trackerDownloads'
	_AttributeUploader		= 'originalUploader'
	_AttributeNext			= 'next'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderJson.initialize(self,
			name					= 'CloudTorrents',
			description				= '{name} is a new and efficient {containers} API. The API contains results in various languages, but most of them are in English.',
			rank					= 5,
			performance				= ProviderJson.PerformanceExcellent,

			link					= Provider._Link,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 0,
			offsetIncrease			= Provider._LimitOffset,

			formatEncode			= ProviderJson.FormatEncodePlus,

			searchQuery				= {
										ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
										ProviderJson.RequestPath : Provider._Path,
										ProviderJson.RequestData : {
											Provider._ParameterQuery	: ProviderJson.TermQuery,
											Provider._ParameterCategory	: ProviderJson.TermCategory,
											Provider._ParameterLimit	: Provider._LimitOffset,
											Provider._ParameterOffset	: ProviderJson.TermOffset,
											Provider._ParameterSort		: Provider._ParameterSeeds,
										},
									},
			searchCategoryMovie		= Provider._CategoryMovie,
			searchCategoryShow		= Provider._CategoryShow,

			extractList				= Provider._AttributeList,
			extractLink				= [Provider._AttributeItem, Provider._AttributeMeta, Provider._AttributeLink],
			extractHash				= [Provider._AttributeItem, Provider._AttributeMeta, Provider._AttributeHash],
			extractFileName			= [Provider._AttributeItem, Provider._AttributeMeta, Provider._AttributeName],
			extractFileSize			= [Provider._AttributeItem, Provider._AttributeMeta, Provider._AttributeSize],
			extractSourceTime		= [Provider._AttributeItem, Provider._AttributeTime],
			extractSourceSeeds		= [Provider._AttributeItem, Provider._AttributeSeeds],
			extractSourceLeeches	= [Provider._AttributeItem, Provider._AttributeLeeches],
			extractSourceApproval	= [Provider._AttributeItem, Provider._AttributeDownloads],
			extractReleaseUploader	= [Provider._AttributeItem, Provider._AttributeMeta, Provider._AttributeUploader],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		if not data.get(Provider._AttributeNext): return ProviderJson.Skip

	def processSourceTime(self, value, item, details = None, entry = None):
		# Not working when doing this from ConverterTime().
		if value: value = Time.timestamp(value, format = '%Y-%m-%dT%H:%M:%S.%f%z')
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		result = ProviderJson.ApprovalDefault
		try: result += ((1 - result) * (float(value) / Provider._LimitApproval))
		except: pass
		return result
