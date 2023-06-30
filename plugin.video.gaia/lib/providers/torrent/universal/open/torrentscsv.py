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

class Provider(ProviderJson):

	_Link					= ['https://torrents-csv.ml']
	_Path					= 'service/search'

	_LimitOffset			= 100 # 100 seems to be the maximum results the API returns.
	_LimitApproval			= 5000

	_ParameterQuery			= 'q'
	_ParameterPage			= 'page'
	_ParameterLimit			= 'size'

	_AttributeHash			= 'infohash'
	_AttributeName			= 'name'
	_AttributeSize			= 'size_bytes'
	_AttributeTime			= 'created_unix'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeDownloads		= 'completed'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderJson.initialize(self,
			name					= 'TorrentsCSV',
			description				= '{name} is collaborative Git repository collecting {containers} into a large CSV file. The API contains results in various languages, but most of them are in English.',
			rank					= 5,
			performance				= ProviderJson.PerformanceExcellent,

			link					= Provider._Link,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			formatEncode			= ProviderJson.FormatEncodeQuote,

			searchQuery				= {
										ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
										ProviderJson.RequestPath : Provider._Path,
										ProviderJson.RequestData : {
											Provider._ParameterQuery	: ProviderJson.TermQuery,
											Provider._ParameterPage		: ProviderJson.TermOffset,
											Provider._ParameterLimit	: Provider._LimitOffset,
										},
									},

			extractHash				= Provider._AttributeHash,
			extractFileName			= Provider._AttributeName,
			extractFileSize			= Provider._AttributeSize,
			extractSourceTime		= Provider._AttributeTime,
			extractSourceSeeds		= Provider._AttributeSeeds,
			extractSourceLeeches	= Provider._AttributeLeeches,
			extractSourceApproval	= Provider._AttributeDownloads,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processSourceApproval(self, value, item, details = None, entry = None):
		if details:
			result = ProviderJson.ApprovalDefault
			try: result += ((1 - result) * (float(value) / Provider._LimitApproval))
			except: pass
			return result
		return None
