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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlSpan, HtmlTable

class Provider(ProviderHtml):

	_Link					= ['https://torrentkitty.net', 'https://torrentkitty.se', 'https://torrentkitty.app', 'https://torrentkitty.me', 'https://torrentkitty.tv', 'https://torrentkitty.re', 'https://torrentkitty.lol']
	_Mirror					= ['https://sosomagnet.com', 'https://about.me/torrentkitty']

	_Path					= 'search/%s/%s'

	_AttributeMain			= 'main'
	_AttributeResults		= 'archiveResult'
	_AttributeName			= 'name'
	_AttributeTime			= 'date'
	_AttributeAction		= 'action'
	_AttributeInformation	= 'information'
	_AttributeWrapper		= 'wrapper'
	_AttributeDetails		= 'detailSummary'
	_AttributePages			= 'pagination'
	_AttributeDisabled		= 'disabled'

	_ExpressionSize			= r'(?:content\s*)?size\s*:\s*(\d+(?:\.\d+)?\s*[kmgt]?b)(?:$|\s|&nbsp;)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'TorrentKitty',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has a lot of missing trivial metadata. The search page of {name} does not contain all the metadata. A subpage must therefore be retrieved for each result in order to extract the magnet link, which substantially increases scraping time.',
			rank						= 2,
			performance					= ProviderHtml.PerformanceBad,

			link						= Provider._Link,
			mirror						= Provider._Mirror,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodeQuote,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path % (ProviderHtml.TermQuery, ProviderHtml.TermOffset),
										},

			extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeMain),
			extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeWrapper),
			extractList					= [HtmlResults(id_ = Provider._AttributeResults, start = 1)],
			extractDetails				= [HtmlResult(class_ = Provider._AttributeAction), HtmlLink(rel_ = Provider._AttributeInformation, extract = Html.AttributeHref)],
			extractLink					= [HtmlResult(class_ = Provider._AttributeAction), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlResult(class_ = Provider._AttributeName)],
			extractFileSize				= [ProviderHtml.Details, HtmlTable(class_ = Provider._AttributeDetails, extract = [Html.ParseTextNested, Provider._ExpressionSize])], # The size on the main search page is the .torrent file size, not the size of the content.
			extractSourceTime			= [HtmlResult(class_ = Provider._AttributeTime)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlSpan(index = -1, extract = Html.AttributeClass)])
			if last and Provider._AttributeDisabled in last:
				return ProviderHtml.Skip
		except: self.logError()
