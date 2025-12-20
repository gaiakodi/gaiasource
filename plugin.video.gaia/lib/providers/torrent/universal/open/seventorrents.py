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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlSmall, HtmlStrong, HtmlListUnordered, HtmlListItem

class Provider(ProviderHtml):

	_Link					= ['https://7torrents.cc']

	_Path					= 'search'

	_ParameterQuery			= 'query'
	_ParameterPage			= 'page'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'seeders'

	_AttributeContainer		= 'card'
	_AttributeItems			= 'results'
	_AttributeItem			= 'media'
	_AttributeBody			= 'media-body'
	_AttributePages			= 'pagination'
	_AttributeNext			= 'next'
	_AttributeDisabled		= 'disabled'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'SevenTorrents',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has many {containers}, but also has Cloudflare protection that might not be bypassable and cause scraping to fail.',
			rank						= 4,
			performance					= ProviderHtml.PerformanceGood,
			status						= ProviderHtml.StatusDead, # Domains are down, but still accessible through: https://seventorrents.unblockit.cam. Update (2025-06): Still down.

			link						= Provider._Link,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterQuery	: ProviderHtml.TermQuery,
												Provider._ParameterPage		: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
											},
										},

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			extractList					= [HtmlDiv(id_ = Provider._AttributeItems), HtmlDiv(class_ = Provider._AttributeItem)],
			extractLink					= [HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlDiv(class_ = Provider._AttributeBody), HtmlLink()],
			extractFileSize				= [HtmlDiv(class_ = Provider._AttributeBody), HtmlSmall(index = 0), HtmlStrong()],
			extractSourceTimeInexact	= [HtmlDiv(class_ = Provider._AttributeBody), HtmlSmall(index = 4), HtmlStrong()],
			extractSourceSeeds			= [HtmlDiv(class_ = Provider._AttributeBody), HtmlSmall(index = 2), HtmlStrong()],
			extractSourceLeeches		= [HtmlDiv(class_ = Provider._AttributeBody), HtmlSmall(index = 3), HtmlStrong()],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlListItem(class_ = Provider._AttributeNext, extract = Html.AttributeClass)])
			if not next or Provider._AttributeDisabled in next: return ProviderHtml.Skip
		except: self.logError()
