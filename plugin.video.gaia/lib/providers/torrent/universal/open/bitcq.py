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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlResultsTable, HtmlResult, HtmlListUnordered, HtmlListItem

class Provider(ProviderHtml):

	_Link					= ['https://bitcq.com']
	_Path					= 'search'

	_Category				= [1] # 1 = Video

	_ParameterQuery			= 'q'
	_ParameterCategory		= 'category[]'
	_ParameterPage			= 'page'

	_AttributeContainer		= 'container'
	_AttributeTable			= 'table'
	_AttributePages			= 'pagination'
	_AttributeActive		= 'active'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'BitCQ',
			description				= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has some missing trivial metadata.',
			rank					= 3,
			performance				= ProviderHtml.PerformanceGood,

			link					= Provider._Link,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			formatEncode			= ProviderHtml.FormatEncodePlus,

			searchQuery				= {
										ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
										ProviderHtml.RequestPath : Provider._Path,
										ProviderHtml.RequestData : {
											Provider._ParameterQuery	: ProviderHtml.TermQuery,
											Provider._ParameterCategory	: ProviderHtml.TermCategory,
											Provider._ParameterPage		: ProviderHtml.TermOffset,
										},
									},

			searchCategoryMovie		= Provider._Category,
			searchCategoryShow		= Provider._Category,

			extractOptimizeData		= HtmlDiv(id_ = Provider._AttributeContainer),
			extractList				= HtmlResultsTable(class_ = Provider._AttributeTable),
			extractLink				= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName			= [HtmlResult(index = 1), HtmlLink(extract = Html.ParseTextNested)],
			extractFileSize			= [HtmlResult(index = 3, extract = Html.ParseTextNested)],
			extractSourceLeeches	= [HtmlResult(index = 4, extract = Html.ParseTextNested)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlListItem(index = -1, extract = Html.AttributeClass)])
			if last and Provider._AttributeActive in last: return ProviderHtml.Skip
		except: self.logError()

	def processFileName(self, value, item, details = None, entry = None):
		# Contains spaces at start and end of string.
		return value.strip() if value else None
