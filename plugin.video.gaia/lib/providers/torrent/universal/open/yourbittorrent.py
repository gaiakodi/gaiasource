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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlDiv, HtmlLink, HtmlKeyboardInput, HtmlItalic

class Provider(ProviderHtml):

	_Link				= ['https://yourbittorrent.com']
	_Mirror				= ['https://torrends.to/proxy/yourbittorrent']

	_CategoryMovie		= ['movie', 'anime']
	_CategoryShow		= ['television', 'anime']

	_ParameterQuery		= 'q'
	_ParameterCategory	= 'c'

	_AttributeContainer	= 'container'
	_AttributeTable		= 'table'
	_AttributeCard		= 'card'
	_AttributeCheck		= 'fa-check'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'YourBittorrent',
			description				= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} requests subpages in order to extract the magnet link and other metadata, which substantially increases scraping time. {name} does not support paging and will therefore return few results. Recently {name} has been very slow and is often inaccessible.',

			# Update (2025-11):
			# Back in the day YourBittorrent worked great.
			# But over the past 1+ year, YourBittorrent is often completely inaccessible.
			# It loads very very slowly and then does not return any results, or returns YourBittorrent HTML (with search bar, etc), but shows a 404 error.
			# Every now and then it does work and is even searchable and returns results, but this is very rare and still takes very long for a single page.
			# Reduce the rank and performance to not select this provider automatically anymore.
			rank					= 3,
			performance				= ProviderHtml.PerformanceBad,

			link					= Provider._Link,
			mirror					= Provider._Mirror,

			customVerified			= True,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			formatEncode			= ProviderHtml.FormatEncodeMinus,

			searchQuery				= {
										ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
										ProviderHtml.RequestData : {
											Provider._ParameterQuery	: ProviderHtml.TermQuery,
											Provider._ParameterCategory	: ProviderHtml.TermCategory,
										},
									},
			searchCategoryMovie		= Provider._CategoryMovie,
			searchCategoryShow		= Provider._CategoryShow,

			extractParser			= ProviderHtml.ParserHtml5, # Contains HTML errors.
			extractOptimizeData		= HtmlDiv(id_ = Provider._AttributeContainer),
			extractOptimizeDetails	= HtmlDiv(class_ = Provider._AttributeCard),
			extractList				= [HtmlResults(class_ = Provider._AttributeTable, index = -1)],
			extractDetails			= [HtmlResult(index = 1), HtmlLink(extract = Html.AttributeHref)],
			extractHash				= [ProviderHtml.Details, HtmlKeyboardInput(extract = [Html.ParseText, ProviderHtml.ExpressionSha])],
			extractFileName			= [HtmlResult(index = 1), HtmlLink(extract = Html.ParseTextNested)],
			extractFileSize			= [HtmlResult(index = 2)],
			extractSourceTime		= [HtmlResult(index = 3)],
			extractSourceSeeds		= [HtmlResult(index = 4)],
			extractSourceLeeches	= [HtmlResult(index = 5)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		if self.customVerified():
			verified = str(self.extractHtml(item, [HtmlResult(index = 1), HtmlItalic(class_ = Provider._AttributeCheck)]))
			if not verified: return ProviderHtml.Skip
