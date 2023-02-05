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
from lib.modules.tools import Regex

class Provider(ProviderJson):

	_Link					= ['https://torrentproject.cc', 'https://torrentproject2.com', 'https://torrentproject2.se', 'http://torrentproject2.org', 'https://torrentproject.info']

	_LimitApproval			= 2

	_CategoryMovie			= 'Movies'
	_CategoryShow			= 'TV'

	_ParameterQuery			= 's'
	_ParameterOffset		= 'p'
	_ParameterSort			= 'orderby'
	_ParameterSeeds			= 'seeders'
	_ParameterFilter		= 'filter'
	_ParameterSafe			= 'safe'
	_ParameterOn			= 'on'

	_AttributeLink			= 'magnet'
	_AttributeName			= 'title'
	_AttributeSize			= 'size'
	_AttributeTime			= 'date'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeUploader		= 'uploader'
	_AttributeVerified		= 'verified'
	_AttributeApproval		= 'reliable'
	_AttributeCategory		= 'category'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderJson.initialize(self,
			name					= 'TorrentProject',
			description				= '{name} is a less-known {container} indexer that scrapes other sites. The site contains results in various languages, but most of them are in English. {name} indexes other torrent sites.',
			rank					= 4,
			performance				= ProviderJson.PerformanceGood,

			link					= Provider._Link,

			customVerified			= True,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 0,
			offsetIncrease			= 1,

			formatEncode			= ProviderJson.FormatEncodeQuote,

			searchQuery				= {
										ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
										ProviderJson.RequestData : {
											Provider._ParameterQuery	: ProviderJson.TermQuery,
											Provider._ParameterOffset	: ProviderJson.TermOffset,
											Provider._ParameterSort		: Provider._ParameterSeeds,
											Provider._ParameterSafe		: Provider._ParameterOn,
											Provider._ParameterFilter	: 0, # Not sure what this parameter does, but must be present for the query to work.
										},
									},

			extractLink				= Provider._AttributeLink,
			extractFileName			= Provider._AttributeName,
			extractFileSize			= Provider._AttributeSize,
			extractSourceTime		= Provider._AttributeTime,
			extractSourceSeeds		= Provider._AttributeSeeds,
			extractSourceLeeches	= Provider._AttributeLeeches,
			extractSourceApproval	= Provider._AttributeApproval,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processRequest(self, data):
		# Remove HTML tags if present
		data = data.replace('<pre>', '').replace('</pre>', '')
		data = data[:-1] + '}'

		# Replace PHP syntax.
		data = data.replace('array (', '{').replace('),', '},')
		data = data.replace('NULL,', 'null,')
		data = data.replace('\' => ', '\' : ')

		# Replace quotes.
		data = data.replace('\\\'', '[GAIA_APOSTROPHE]') # In string.
		data = data.replace('"', '\\"')
		data = data.replace('\'', '"')
		data = data.replace('[GAIA_APOSTROPHE]', '\'')

		# Remove trailing commas.
		data = Regex.replace(data = data, expression = ',\s+}', replacement = '}')
		data = Regex.replace(data = data, expression = ',\s+\]', replacement = ']')

		return data

	def processData(self, data):
		try: return list(data.values())
		except: return None

	def processBefore(self, item):
		category = item[Provider._AttributeCategory]
		if category:
			if self.parameterMediaMovie(): target = Provider._CategoryMovie
			elif self.parameterMediaShow(): target = Provider._CategoryShow
			if not category == target: return ProviderJson.Skip

		if self.customVerified():
			if not item[Provider._AttributeVerified]: return ProviderJson.Skip

	def processSourceApproval(self, value, item, details = None, entry = None):
		result = ProviderJson.ApprovalDefault
		if value: result += (1 - result) * (float(value) / Provider._LimitApproval)
		return result
