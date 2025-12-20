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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlSpan, HtmlMain, HtmlBold, HtmlListUnordered, HtmlListItem, HtmlResultsDiv, HtmlParagraph, HtmlBold

class Provider(ProviderHtml):

	# The .org domain is old version 2, while .com is the new version 1.
	_Link					= {
								ProviderHtml.Version1 : 'https://bt4gprx.com',
								ProviderHtml.Version2 : 'https://bt4g.org',
							}
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'bt4g', ProviderHtml.UnblockFormat3 : 'bt4g'}
	_Path					= {
								ProviderHtml.Version1 : 'search',
								ProviderHtml.Version2 : 'movie/search/%s/%s/%s' # The "movie" category is actually the "video" category containing both movies and shows.
							}

	_CategoryMovie			= ['movie']
	_CategoryShow			= ['movie'] # Also uses the "movie" category.

	_ParameterSort			= 'byseeders'

	_ParameterQuery			= 'q'
	_ParameterCategory		= 'category'
	_ParameterPage			= 'p'
	_ParameterOrder			= 'orderby'
	_ParameterSeeds			= 'seeders'

	_AttributeTable			= 'list-group'
	_AttributeItem			= 'result-item'
	_AttributeCard			= 'card'
	_AttributeButton		= 'btn-primary'
	_AttributeDetails		= 'mb-1'
	_AttributeDetail		= 'me-2'

	_AttributeContainer		= 'container'
	_AttributeRow			= 'row'
	_AttributeColumn		= 'col'
	_AttributeSize			= 'red-pill'
	_AttributeSeeds			= 'seeders'
	_AttributeLeeches		= 'leechers'
	_AttributePages			= 'pagination'
	_AttributeActive		= 'active'

	_ExpressionTime			= '(?:\:\s*(.*))'
	_ExpressionLink			= 'magnet/' + ProviderHtml.ExpressionSha

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		name			= 'BT4G'
		description		= '{name} is a well-known {container} site. The site contains results in various languages, but most of them are in English. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.'
		rank			= 3
		status			= ProviderHtml.StatusCloudflare # Cloudflare. For v1, Cloudflare only seems to block requests when accessing page 4+.

		version = self.customVersion()
		if version == ProviderHtml.Version1:
			ProviderHtml.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= ProviderHtml.PerformanceBad,
				status					= status,

				link					= Provider._Link[version],
				unblock					= Provider._Unblock,

				supportMovie			= True,
				supportShow				= True,
				supportPack				= True,

				offsetStart				= 1,
				offsetIncrease			= 1,

				formatEncode			= ProviderHtml.FormatEncodeQuote,

				searchQuery				= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path[version],
											ProviderHtml.RequestData : {
												Provider._ParameterQuery	: ProviderHtml.TermQuery,
												Provider._ParameterCategory	: ProviderHtml.TermCategory,
												Provider._ParameterPage		: ProviderHtml.TermOffset,
												Provider._ParameterOrder	: Provider._ParameterSeeds,
											},
										},
				searchCategoryMovie		= Provider._CategoryMovie,
				searchCategoryShow		= Provider._CategoryShow,

				extractParser			= ProviderHtml.ParserHtml5, # Contains HTML errors.
				extractOptimizeData		= HtmlMain(id_ = Provider._AttributeContainer),
				extractOptimizeDetails	= HtmlDiv(class_ = Provider._AttributeCard),
				extractList				= [HtmlResultsDiv(class_ = Provider._AttributeTable, index = -1)],
				extractDetails			= [HtmlLink(extract = Html.AttributeHref)],
				extractHash				= [ProviderHtml.Details, HtmlLink(class_ = Provider._AttributeButton, extract = [Html.AttributeHref, ProviderHtml.ExpressionSha])],
				extractFileName			= [HtmlLink(extract = Html.AttributeTitle)],
				extractFileSize			= [HtmlParagraph(class_ = Provider._AttributeDetails), HtmlSpan(class_ = Provider._AttributeDetail, index = 3), HtmlBold()],
				extractSourceTime		= [HtmlParagraph(class_ = Provider._AttributeDetails), HtmlSpan(class_ = Provider._AttributeDetail, index = 1, extract = [Html.ParseText, Provider._ExpressionTime])],
				extractSourceSeeds		= [HtmlParagraph(class_ = Provider._AttributeDetails), HtmlBold(id_ = Provider._AttributeSeeds)],
				extractSourceLeeches	= [HtmlParagraph(class_ = Provider._AttributeDetails), HtmlBold(id_ = Provider._AttributeLeeches)],
			)
		elif version == ProviderHtml.Version2:
			ProviderHtml.initialize(self,
				name					= name,
				description				= description,
				rank					= rank,
				performance				= ProviderHtml.PerformanceGood - ProviderHtml.PerformanceStep,
				status					= status,

				link					= Provider._Link[version],
				unblock					= Provider._Unblock,

				supportMovie			= True,
				supportShow				= True,
				supportPack				= True,

				offsetStart				= 1,
				offsetIncrease			= 1,

				formatEncode			= ProviderHtml.FormatEncodeQuote,

				searchQuery				= Provider._Path[version] % (ProviderHtml.TermQuery, Provider._ParameterSort, ProviderHtml.TermOffset),

				extractOptimizeData		= HtmlMain(),
				extractList				= [HtmlDiv(class_ = Provider._AttributeContainer), HtmlDiv(class_ = Provider._AttributeRow, start = 2, recursive = False), HtmlDiv(class_ = Provider._AttributeColumn), HtmlDiv(start = 1)],
				extractHash				= [HtmlLink(href_ = Provider._ExpressionLink, extract = Provider._ExpressionLink)],
				extractFileName			= [HtmlLink(href_ = Provider._ExpressionLink, extract = Html.AttributeTitle)],
				extractFileSize			= [HtmlBold(class_ = Provider._AttributeSize)],
				extractSourceTime		= [HtmlSpan(index = 1, recursive = False), HtmlBold()],
				extractSourceSeeds		= [HtmlBold(id_ = Provider._AttributeSeeds)],
				extractSourceLeeches	= [HtmlBold(id_ = Provider._AttributeLeeches)],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		# For both versions the same.
		try:
			next = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlListItem(index = -1, extract = Html.AttributeClass)])
			if not next or Provider._AttributeActive in next: return ProviderHtml.Skip
		except: self.logError()
