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

# Update (2025-06)
# The API parameters have changed.
#	https://torrents-csv.com/service/search?q=[QUERY]&size=[NUMBER_OF_RESULTS]&after=[AFTER]
# The size parameter does not seem to work anymore, even though it is still documented. It seems that a fixed limit of 25 is now used.
# The "page" parameter was removed.
# A new "after" parameter was added. This seems to not be the page or offset.
# Instead, a new "next" attribute was added to the JSON results, which is the next "rowid" to retrieve from, that is after the last item of the previous page.

from lib.providers.core.json import ProviderJson

class Provider(ProviderJson):

	_Link					= ['https://torrents-csv.com'] # https://torrents-csv.ml is down.
	_Path					= 'service/search'

	_LimitOffset			= 100 # 100 seems to be the maximum results the API returns.
	_LimitApproval			= 5000

	_ParameterQuery			= 'q'
	_ParameterPage			= 'page'
	_ParameterLimit			= 'size'
	_ParameterAfter			= 'after'

	_AttributeList			= 'torrents'
	_AttributeHash			= 'infohash'
	_AttributeName			= 'name'
	_AttributeSize			= 'size_bytes'
	_AttributeTime			= 'created_unix'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeDownloads		= 'completed'
	_AttributeNext			= 'next'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderJson.initialize(self,
			name					= 'TorrentsCSV',
			description				= '{name} is collaborative Git repository collecting {containers} into a large CSV file. The API contains results in various languages, but most of them are in English.',
			rank					= 5,
			performance				= ProviderJson.PerformanceExcellent,
			#status					= ProviderJson.StatusDead, # Domain and Git repo is down. Update (2024-12): New .com domain works.

			link					= Provider._Link,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			# Update (2025-06)
			# TorrentsCsv does not use page numbers like before.
			# Instead it now has an "after" parameter, which is the "rowid" of the previous torrent serving as an ID offset to retrieve torrents after this ID.
			# The results now contain a "next" attribute which can be passed in as the next request's "after" parameter. The "next" attribute is essentially the "rowid" parameter from the last torrent in the current results returned.
			# The "next" attribute is now returned using processOffset().
			#offsetStart			= 1,
			#offsetIncrease			= 1,
			offsetStart				= 0, # If not specified, it will add an empty string as the parameter (after=''), which does not return any results.

			formatEncode			= ProviderJson.FormatEncodeQuote,

			searchQuery				= {
										ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
										ProviderJson.RequestPath : Provider._Path,
										ProviderJson.RequestData : {
											Provider._ParameterQuery	: ProviderJson.TermQuery,
											Provider._ParameterLimit	: Provider._LimitOffset, # Update (2025-06): The limit/size parameter does not work anymore. The limit is not fixed at 25.
											#Provider._ParameterPage	: ProviderJson.TermOffset, # Paging does not work anymore with the .com and is also not documented. Can still return only 100 results.
											Provider._ParameterAfter	: ProviderJson.TermOffset,
										},
									},

			extractList				= Provider._AttributeList,
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

	def processOffset(self, data, items):
		try:
			if data and data.get(Provider._AttributeNext): return data.get(Provider._AttributeNext)
			else: return ProviderHtml.Skip
		except: self.logError()

	def processSourceApproval(self, value, item, details = None, entry = None):
		if details:
			result = ProviderJson.ApprovalDefault
			try: result += ((1 - result) * (float(value) / Provider._LimitApproval))
			except: pass
			return result
		return None
