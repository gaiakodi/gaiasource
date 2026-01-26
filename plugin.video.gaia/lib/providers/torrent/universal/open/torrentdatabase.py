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

from lib.providers.core.html import ProviderHtml, Html, HtmlAny, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlSpan
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://developify.ca']
	_Path					= 'newest'

	_CategoryMovie			= 'movies'
	_CategoryShow			= 'TV'

	_ParameterQuery			= 'q'
	_ParameterPage			= 'page'
	_ParameterCategory		= 'category'

	_AttributeContainer		= 'main-container'
	_AttributeTable			= 'torrent-table'
	_AttributePages			= 'pagination'
	_AttributePage			= 'current-page'

	_ExpressionUploader		= r'developify'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'TorrentDatabase',
			description				= '{name} is a new {container} site. The site contains results in various languages, but most of them are in English. Some metadata, such as number of seeds and leeches, might be missing.',
			rank					= 5, # The missing seeds/leeches is only for some links that are older. Newer links seem to have the seeds/leeches.
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
											Provider._ParameterPage		: ProviderHtml.TermOffset,
											Provider._ParameterCategory	: ProviderHtml.TermCategory,
										},
									},
			searchCategoryMovie		= Provider._CategoryMovie,
			searchCategoryShow		= Provider._CategoryShow,

			extractOptimizeData		= HtmlDiv(class_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			extractList				= [HtmlResults(class_ = Provider._AttributeTable, start = 1)],
			extractLink				= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName			= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.ParseTextNested)],
			extractFileSize			= [HtmlResult(index = 2)],
			extractReleaseUploader	= [HtmlResult(index = 5), HtmlSpan(extract = Html.ParseTextUnnested)],
			extractSourceTime		= [HtmlResult(index = 3)],
			extractSourceSeeds		= [HtmlResult(index = 4), HtmlSpan(index = 0, extract = Html.ParseTextUnnested)],
			extractSourceLeeches	= [HtmlResult(index = 4), HtmlSpan(index = -1, extract = Html.ParseTextUnnested)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlAny(index = -1, extract = Html.AttributeClass)])
			if last and Provider._AttributePage in last: return ProviderHtml.Skip
		except: self.logError()

	def processReleaseUploader(self, value, item, details = None, entry = None):
		# Almost all links have the uploader set to "DevelopifyBOT".
		if value and not Regex.match(data = value, expression = Provider._ExpressionUploader): return value
		return None

	def processSourceTime(self, value, item, details = None, entry = None):
		# %:z is only supported in Python 3.12 and later.
		# Eg: 2025-04-19 21:43:11+02:00
		if value: return Regex.extract(data = value, expression = r'(\d{4}\-\d{2}\-\d{2}\s*\d{2}\:\d{2}\:\d{2})', cache = True)
		return value
