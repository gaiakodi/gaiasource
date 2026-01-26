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

from lib.providers.core.html import ProviderHtml, Html, HtmlTableRow, HtmlTableCell, HtmlInput, HtmlLink

class Provider(ProviderHtml):

	_Link					= ['https://ilcorsaronero.in', 'https://ilcorsaronero.link', 'https://ilcorsaronero.pro', 'https://ilcorsaronero.fun', 'https://ilcorsaronero.xyz', 'https://ilcorsaronero.pw', 'https://ilcorsaronero.info', 'https://ilcorsaronero.cc']
	_Mirror					= ['https://lagazzettadelcorsaro.com']
	_Path					= 'argh.php'

	_ParameterQuery			= 'search'

	_ExpressionItem			= r'(odd\d?)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'ilCorSaRoNeRo',
			description				= '{name} is well-known open {container} site from Italy. The site contains results in various languages, but most of them are in Italian. {name} does not support paging and results might therefore be limited.',
			rank					= 3,
			performance				= ProviderHtml.PerformanceGood,

			link					= Provider._Link,
			mirror					= Provider._Mirror,

			formatEncode			= ProviderHtml.FormatEncodePlus,

			searchQuery				= {
										ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
										ProviderHtml.RequestPath : Provider._Path,
										ProviderHtml.RequestData : {
											Provider._ParameterQuery : ProviderHtml.TermQuery,
										},
									},

			extractParser			= ProviderHtml.ParserHtml5, # Has some HTML bugs.
			extractList				= [HtmlTableRow(class_ = Provider._ExpressionItem)],
			extractHash				= [HtmlTableCell(index = 3), HtmlInput(extract = Html.AttributeValue)],
			extractFileName			= [HtmlTableCell(index = 1)],
			extractFileSize			= [HtmlTableCell(index = 2)],
			extractSourceTime		= [HtmlTableCell(index = 4)],
			extractSourceSeeds		= [HtmlTableCell(index = 5)],
			extractSourceLeeches	= [HtmlTableCell(index = 6)],
		)
