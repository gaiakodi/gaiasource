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
from lib.providers.core.html import ProviderHtml, Html, HtmlMain, HtmlLink, HtmlDiv, HtmlHeading5, HtmlListItem
from lib.modules.tools import Regex

class Provider(ProviderJson, ProviderHtml):

	# Update (2025-01): .net domain is completely down. .eu domain loads a semi-broken website.
	# https://solidtorrents.net
	_Link					= ['https://solidtorrents.to', 'https://solidtorrents.eu']
	_Path					= {
								ProviderHtml.Version1 : 'search',
								ProviderHtml.Version2 : 'api/v1/search',
							}

	_LimitOffset			= 20
	_LimitApproval			= {
								ProviderHtml.Version1 : 5000,
								ProviderHtml.Version2 : 2000,
							}

	# NB: There are a lot of titles listed under Other/Video.
	_CategoryMovie			= [2, 1] # 2 = Movies, 1 = Other
	_CategoryShow			= [3, 1] # 3 = TV, 1 = Other
	_CategoryVideo			= 'Video'
	_CategoryUnknown		= 'Unknown'

	_ParameterQuery			= 'q'
	_ParameterOffset		= 'skip'
	_ParameterPage			= 'page'
	_ParameterCategory		= 'category'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'seeders'
	_ParameterSafety		= 'safety' # Does not seem to work at the moment.
	_ParameterSpam			= 'fuv'
	_ParameterYes			= 'yes'
	_ParameterNo			= 'no'

	_AttributeContainer		= 'container'
	_AttributeResult		= 'search-result'
	_AttributeInfo			= 'info'
	_AttributeLinks			= 'links'
	_AttributeStats			= 'stats'
	_AttributeTitle			= 'title'
	_AttributePages			= 'pagination'
	_AttributeDisabled		= 'disabled'

	_AttributList			= 'results'
	_AttributId				= '_id'
	_AttributeLink			= 'magnet'
	_AttributeName			= 'title'
	_AttributeSize			= 'size'
	_AttributeTime			= 'imported'
	_AttributeSwarm			= 'swarm'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributeVerified		= 'verified'
	_AttributeDownloads		= 'downloads'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		name					= 'SolidTorrents'
		description				= '{name} is a less-known {container} site and API. The site contains results in various languages, but most of them are in English. {name} is fast and has many {containers} with good metadata.'
		rank					= 5
		performance				= ProviderJson.PerformanceExcellent

		# Update (2024-12): Domain has been down for a few weeks, although it was working a few weeks earlier. Leave enabled, since it will probably come back online and SolidTorrents is one of the better providers.
		# Update (2024-12-20): Domain is up again, but sometimes a search results in a gateway error.
		status					= ProviderJson.StatusOperational

		version = self.customVersion()
		if version == ProviderHtml.Version1:
			ProviderHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,
				status						= status,

				link						= Provider._Link,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 1,
				offsetIncrease				= 1,

				formatEncode				= ProviderHtml.FormatEncodePlus,

				searchQuery					= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path[version],
												ProviderHtml.RequestData : {
													Provider._ParameterQuery	: ProviderHtml.TermQuery,
													Provider._ParameterCategory	: ProviderHtml.TermCategory,
													Provider._ParameterPage		: ProviderHtml.TermOffset,
													Provider._ParameterSort		: Provider._ParameterSeeds,
												},
											},
				searchCategoryMovie			= Provider._CategoryMovie,
				searchCategoryShow			= Provider._CategoryShow,

				extractOptimizeData			= [HtmlMain(), HtmlDiv(class_ = Provider._AttributeContainer, index = -1)], # Get the last container, since a new container was added to the top to download the mobile app.
				extractList					= HtmlListItem(class_ = Provider._AttributeResult),
				extractLink					= [HtmlDiv(class_ = Provider._AttributeLinks), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName				= [HtmlDiv(class_ = Provider._AttributeInfo), HtmlHeading5(class_ = Provider._AttributeTitle), HtmlLink()], # Extract the link, since there can be a checkmark icon next to the file name.
				extractFileSize				= [HtmlDiv(class_ = Provider._AttributeInfo), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 1)],
				extractSourceTime			= [HtmlDiv(class_ = Provider._AttributeInfo), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 4)],
				extractSourceSeeds			= [HtmlDiv(class_ = Provider._AttributeInfo), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 2)],
				extractSourceLeeches		= [HtmlDiv(class_ = Provider._AttributeInfo), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 3)],
				extractSourceApproval		= [HtmlDiv(class_ = Provider._AttributeInfo), HtmlDiv(class_ = Provider._AttributeStats), HtmlDiv(index = 0)],
			)
		elif version == ProviderHtml.Version2:
			category = ','.join([Provider._CategoryVideo, Provider._CategoryUnknown])
			ProviderJson.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= performance,
				status					= status,

				link					= Provider._Link,

				customVersion			= 2,
				customSpam				= True,
				customVerified			= True,

				supportMovie			= True,
				supportShow				= True,
				supportPack				= True,

				offsetStart				= 0,
				offsetIncrease			= Provider._LimitOffset,

				formatEncode			= ProviderJson.FormatEncodePlus,

				searchQuery				= {
											ProviderJson.RequestMethod : ProviderJson.RequestMethodGet,
											ProviderJson.RequestPath : Provider._Path[version],
											ProviderJson.RequestData : {
												Provider._ParameterQuery	: ProviderJson.TermQuery,
												Provider._ParameterCategory	: ProviderJson.TermCategory,
												Provider._ParameterOffset	: ProviderJson.TermOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
												Provider._ParameterSpam		: Provider._ParameterYes if self.customSpam() else Provider._ParameterNo,
											},
										},
				searchCategoryMovie		= category,
				searchCategoryShow		= category,

				extractList				= Provider._AttributList,
				extractLink				= Provider._AttributeLink,
				extractIdLocal			= Provider._AttributId,
				extractFileName			= Provider._AttributeName,
				extractFileSize			= Provider._AttributeSize,
				extractSourceTime		= Provider._AttributeTime,
				extractSourceApproval	= [Provider._AttributeSwarm, Provider._AttributeDownloads],
				extractSourceSeeds		= [Provider._AttributeSwarm, Provider._AttributeSeeds],
				extractSourceLeeches	= [Provider._AttributeSwarm, Provider._AttributeLeeches],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		if self.customVersion2():
			if self.customVerified():
				if not item[Provider._AttributeSwarm][Provider._AttributeVerified]: return ProviderJson.Skip

	def processOffset(self, data, items):
		if self.customVersion1():
			try:
				next = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(index = -1, extract = Html.AttributeClass)])
				if not next or Provider._AttributeDisabled in next: return ProviderHtml.Skip
			except: self.logError()

	def processSourceApproval(self, value, item, details = None, entry = None):
		version = self.customVersion()
		if version == ProviderHtml.Version1:
			result = ProviderHtml.ApprovalDefault
			try:
				if value:
					value = value.lower()
					multiplier = 1
					if 'b' in value: multiplier = 1000000000
					elif 'm' in value: multiplier = 1000000
					elif 'k' in value: multiplier = 1000
					value = Regex.extract(data = value, expression = '(\d+(?:\.\d+)?)')
					value = float(value) * multiplier
					result += (1 - result) * max(0, min(1, (float(value) / Provider._LimitApproval[version])))
			except: self.logError()
			return result
		elif version == ProviderHtml.Version2:
			result = ProviderJson.ApprovalDefault
			try: result += (1 - result) * (float(value) / Provider._LimitApproval[version])
			except: pass
			return result
		return value
