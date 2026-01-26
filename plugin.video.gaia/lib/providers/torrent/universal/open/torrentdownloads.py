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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlSpan, HtmlParagraph, HtmlImage
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://torrentdownloads.pro', 'https://torrentdownloads.me']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'torrentdownloads', ProviderHtml.UnblockFormat3 : 'torrentdownloads', ProviderHtml.UnblockFormat4 : 'torrentdownloads'}
	_Path					= 'search/' # Must end with a slash.

	# Do not search by category, since many links are misclassified.
	# Newer stuff also does not show up in the movie/show category, but in some "video" category that is not in TorrentDownloads interface dropdown.
	#_CategoryMovie			= '4'
	#_CategoryShow			= '8'

	_ParameterQuery			= 'search'
	_ParameterCategory		= 's_cat'
	_ParameterOffset		= 'page'
	_ParameterSort			= 'srt'
	_ParameterSeeds			= 'seeds'
	_ParameterOrder			= 'order'
	_ParameterDescending	= 'desc'
	_ParameterVerified		= 'check_box'

	_AttributeContainer		= 'inner_container'
	_AttributeItem			= 'grey_bar3'
	_AttributePages			= 'pagination_box'

	_ExpressionLink			= r'(\/torrent\/.*)'
	_ExpressionNext			= r'(>|&gt;){2,}'
	_ExpressionDetails		= r'(grey_bara?1)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'TorrentDownloads',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} requests subpages in order to extract the magnet link and other metadata, which substantially increases scraping time.',
			rank						= 3,
			performance					= ProviderHtml.PerformanceBad,

			link						= Provider._Link,
			unblock						= Provider._Unblock,

			customVerified				= True,

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
												#Provider._ParameterCategory	: ProviderHtml.TermCategory,
												Provider._ParameterOffset	: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
												Provider._ParameterOrder	: Provider._ParameterDescending,
											},
										},
			#searchCategoryMovie		= Provider._CategoryMovie,
			#searchCategoryShow			= Provider._CategoryShow,

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContainer, index = -1), # To detect the last page in processOffset().
			extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeContainer),
			extractList					= [HtmlDiv(class_ = Provider._AttributeItem, start = 2)], # First row is header, second row points to another site (torrentdownload.info).
			extractDetails				= [HtmlLink(href_ = Provider._ExpressionLink, extract = Html.AttributeHref)],
			extractLink					= [ProviderHtml.Details, HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlLink(href_ = Provider._ExpressionLink)],
			extractFileSize				= [ProviderHtml.Details, HtmlDiv(class_ = Provider._ExpressionDetails, index = 2), HtmlParagraph(extract = Html.ParseTextUnnested)],
			extractSourceTime			= [ProviderHtml.Details, HtmlDiv(class_ = Provider._ExpressionDetails, index = 8), HtmlParagraph(extract = Html.ParseTextUnnested)],
			extractSourceSeeds			= [ProviderHtml.Details, HtmlDiv(class_ = Provider._ExpressionDetails, index = 4), HtmlParagraph(extract = Html.ParseTextUnnested)],
			extractSourceLeeches		= [ProviderHtml.Details, HtmlDiv(class_ = Provider._ExpressionDetails, index = 5), HtmlParagraph(extract = Html.ParseTextUnnested)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			pages = str(self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink()]))
			if not Regex.match(data = pages, expression = Provider._ExpressionNext):
				return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		if self.customVerified():
			verified = self.extractHtml(item, [HtmlSpan(class_ = Provider._ParameterVerified), HtmlImage()])
			if not verified: return ProviderHtml.Skip
