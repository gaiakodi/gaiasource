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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlSpan, HtmlListItem
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://ext.to', 'https://search.extto.com']
	_Mirror					= ['https://ext-proxy.github.io']
	_Unblock				= {ProviderHtml.UnblockFormat1 : 'ext'}

	_Path					= {
								ProviderHtml.Version1 : 'browse',
								ProviderHtml.Version2 : 'search/%s/%s/?c=%s&order=seed&sort=desc',
								ProviderHtml.Version3 : 'search/%s/%s/?c=%s&order=seed&sort=desc',
							}

	_LimitOffset			= 100
	_LimitApproval			= 100

	_CategoryMovie			= {
								ProviderHtml.Version1 : '1',
								ProviderHtml.Version2 : 'movies',
								ProviderHtml.Version3 : 'movies',
							}
	_CategoryShow					= {
								ProviderHtml.Version1 : '2',
								ProviderHtml.Version2 : 'tv',
								ProviderHtml.Version3 : 'tv',
							}

	_ParameterQuery			= 'q'
	_ParameterCategory		= 'cat'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'seeds'
	_ParameterOrder			= 'order'
	_ParameterDescending	= 'desc'
	_ParameterLimit			= 'page_size'
	_ParameterOffset		= 'page'
	_ParameterPorn			= 'with_adult'
	_ParameterTrue			= '1'
	_ParameterFalse			= '0'

	_AttributePages1		= 'pages'
	_AttributeActive1		= 'active'
	_AttributeUploader1		= 'simple-user' # Do not use "external-user", since it is not added for verified users.

	_AttributeContainer2	= 'main-block'
	_AttributeDetails2		= 'main-container'
	_AttributeTable2		= 'search-table'
	_AttributeLinks2		= 'pt-2'
	_AttributeInfo2			= 'detail-torrent-poster-info'
	_AttributePages2		= 'pagination-block'

	_ExpressionAge			= '(\s*age\s*)'
	_ExpressionDownloads	= 'downloaded\s*(\d+)\s*time'
	_ExpressionNext			= '(>|&gt;){1,}'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		customAdult					= None
		extractOptimizeDetails		= None
		extractDetails				= None
		extractReleaseUploader		= None
		extractSourceTime			= None
		extractSourceTimeInexact	= None
		extractSourceApproval		= None

		version = self.customVersion()
		if version == ProviderHtml.Version1:
			customAdult					= True
			formatEncode				= ProviderHtml.FormatEncodePlus

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path[version],
											ProviderHtml.RequestData : {
												Provider._ParameterQuery		: ProviderHtml.TermQuery,
												Provider._ParameterCategory		: ProviderHtml.TermCategory,
												Provider._ParameterLimit		: Provider._LimitOffset,
												Provider._ParameterOffset		: ProviderHtml.TermOffset,
												Provider._ParameterSort			: Provider._ParameterSeeds,
												Provider._ParameterOrder		: Provider._ParameterDescending,
												Provider._ParameterPorn			: Provider._ParameterFalse if self.customAdult() else Provider._ParameterTrue,
											},
										}

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContainer2) # To detect the last page in processOffset().
			extractList					= [HtmlResults(class_ = Provider._AttributeTable2)]
			extractLink					= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)]
			extractFileName				= [HtmlResult(index = 0), HtmlLink()]
			extractFileSize				= [HtmlResult(index = 1), HtmlSpan(index = -1)]
			extractReleaseUploader		= [HtmlResult(index = 0), HtmlLink(class_ = Provider._AttributeUploader1, extract = Html.ParseTextNested)]
			extractSourceTime			= [HtmlResult(index = 3), HtmlSpan(index = -1, extract = Html.AttributeTitle)]
			extractSourceSeeds			= [HtmlResult(index = 4), HtmlSpan(index = -1)]
			extractSourceLeeches		= [HtmlResult(index = 5), HtmlSpan(index = -1)]

		elif version == ProviderHtml.Version2:
			formatEncode				= ProviderHtml.FormatEncodeMinus
			searchQuery					= Provider._Path[version] % (ProviderHtml.TermQuery, ProviderHtml.TermOffset, ProviderHtml.TermCategory)

			# The website changed and now has the magnet on the main page.
			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContainer2) # To detect the last page in processOffset().
			extractList					= [HtmlResults(class_ = Provider._AttributeTable2)]
			extractLink					= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)]
			extractFileName				= [HtmlResult(index = 0), HtmlLink()]
			extractFileSize				= [HtmlResult(index = 1)]
			extractSourceTimeInexact	= [HtmlResult(index = 3)]
			extractSourceSeeds			= [HtmlResult(index = 4)]
			extractSourceLeeches		= [HtmlResult(index = 5)]
		elif version == ProviderHtml.Version3:
			formatEncode				= ProviderHtml.FormatEncodeMinus
			searchQuery					= Provider._Path[version] % (ProviderHtml.TermQuery, ProviderHtml.TermOffset, ProviderHtml.TermCategory)

			# The hash could be extracted from the .torrent link on the search page, but there are too many that do not have a download link, only a streaming link that does not contain the hash.
			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContainer2) # To detect the last page in processOffset().
			extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeDetails2)
			extractList					= [HtmlResults(class_ = Provider._AttributeTable2)]
			extractDetails				= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeHref)]
			extractLink					= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeLinks2), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)]
			extractFileName				= [HtmlResult(index = 0), HtmlLink()]
			extractFileSize				= [HtmlResult(index = 1)]
			extractSourceTimeInexact	= [HtmlResult(index = 3)]
			extractSourceApproval		= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeInfo2, extract = [Html.ParseTextNested, Provider._ExpressionDownloads])]
			extractSourceSeeds			= [HtmlResult(index = 4)]
			extractSourceLeeches		= [HtmlResult(index = 5)]

		ProviderHtml.initialize(self,
			name						= 'EXTTorrents',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.',
			rank						= 3,
			performance					= ProviderHtml.PerformanceGood,
			status						= ProviderHtml.StatusCloudflare, # Cloudflare.

			link						= Provider._Link,
			mirror						= Provider._Mirror,
			unblock						= Provider._Unblock,

			customVersion				= 3,
			customAdult					= customAdult,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= formatEncode,

			searchQuery					= searchQuery,
			searchCategoryMovie			= Provider._CategoryMovie[version],
			searchCategoryShow			= Provider._CategoryShow[version],

			extractOptimizeData			= extractOptimizeData,
			extractOptimizeDetails		= extractOptimizeDetails,
			extractList					= extractList,
			extractDetails				= extractDetails,
			extractLink					= extractLink,
			extractFileName				= extractFileName,
			extractFileSize				= extractFileSize,
			extractReleaseUploader		= extractReleaseUploader,
			extractSourceTime			= extractSourceTime,
			extractSourceTimeInexact	= extractSourceTimeInexact,
			extractSourceApproval		= extractSourceApproval,
			extractSourceSeeds			= extractSourceSeeds,
			extractSourceLeeches		= extractSourceLeeches,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			if self.customVersion1():
				last = self.extractHtml(data, [Html(class_ = Provider._AttributePages1), HtmlListItem(index = -1, extract = Html.AttributeClass)])
				if last and Provider._AttributeActive1 in last: return ProviderHtml.Skip
			else:
				last = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages2), HtmlLink(index = -1, extract = Html.ParseText)])
				if not last or not Regex.match(data = last, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		if value: value = Regex.remove(data = value, expression = Provider._ExpressionAge, all = True)
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		if self.customVersion3():
			if value and details:
				result = ProviderHtml.ApprovalDefault
				try: result += (1 - result) * (float(value) / Provider._LimitApproval)
				except: pass
				return result
		return value
