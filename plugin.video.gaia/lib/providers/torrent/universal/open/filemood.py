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

from lib.providers.core.html import ProviderHtml, Html, HtmlTable, HtmlTableRow, HtmlTableCell, HtmlLink, HtmlDiv
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://filemood.com']
	_Path					= 'result'

	_LimitOffset			= 20 # Fixed

	_ParameterQuery			= 'q'
	_ParameterSearch		= 'in:title'
	_ParameterPage			= 'f'

	_AttributeContainer		= 'result-main-center'
	_AttributePages			= 'btn-group'
	_AttributePage			= 'btn'
	_AttributeDisabled		= 'disabled'

	_ExpressionSeeds		= '(\d+)\s*\/\s*\d+'
	_ExpressionLeeches		= '\d+\s*\/\s*(\d+)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'FileMood',
			description				= '{name} is a new {container} site. The site contains results in various languages, but most of them are in English. Some metadata, such as dates, are missing.',
			rank					= 4, # Missing dates.
			performance				= ProviderHtml.PerformanceGood,

			link					= Provider._Link,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 0,
			offsetIncrease			= Provider._LimitOffset,

			formatEncode			= ProviderHtml.FormatEncodePlus,

			searchQuery				= {
										ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
										ProviderHtml.RequestPath : Provider._Path,
										ProviderHtml.RequestData : {
											Provider._ParameterQuery	: ProviderHtml.TermQuery + '+' + Provider._ParameterSearch, # Only search in the title. Space should be encoded as "formatEncode".
											Provider._ParameterPage		: ProviderHtml.TermOffset,
										},
									},

			extractOptimizeData		= HtmlDiv(id_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			extractList				= [HtmlDiv(), HtmlDiv(), HtmlTable()], # Each result is in its own table.
			extractHash				= [HtmlTableRow(index = 0), HtmlTableCell(index = 0), HtmlLink(extract = [Html.AttributeHref, ProviderHtml.ExpressionSha])],
			extractFileName			= [HtmlTableRow(index = 0), HtmlTableCell(index = 0), HtmlLink(extract = Html.ParseTextNested)],
			extractFileSize			= [HtmlTableRow(index = 0), HtmlTableCell(index = 2, extract = Html.ParseTextNested)],
			extractSourceSeeds		= [HtmlTableRow(index = 0), HtmlTableCell(index = 1, extract = [Html.ParseTextNested, Provider._ExpressionSeeds])],
			extractSourceLeeches	= [HtmlTableRow(index = 0), HtmlTableCell(index = 1, extract = [Html.ParseTextNested, Provider._ExpressionLeeches])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(class_ = Provider._AttributePage, index = -1, extract = Html.AttributeClass)])
			if last and Provider._AttributeDisabled in last: return ProviderHtml.Skip
		except: self.logError()
