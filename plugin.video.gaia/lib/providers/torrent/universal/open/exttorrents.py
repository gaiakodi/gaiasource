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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://ext.to', 'https://extto.com']
	_Mirror					= ['https://ext-proxy.github.io']
	_Unblock				= {ProviderHtml.UnblockFormat1 : 'ext'}

	_Path					= 'search/%s/%s/?c=%s&order=seed&sort=desc'

	_LimitApproval			= 100

	_CategoryMovie			= 'movies'
	_CategoryShow			= 'tv'

	_AttributeContainer		= 'main-block'
	_AttributeDetails		= 'main-container'
	_AttributeTable			= 'search-table'
	_AttributeLinks			= 'pt-2'
	_AttributeInfo			= 'detail-torrent-poster-info'
	_AttributePages			= 'pagination-block'

	_ExpressionAge			= '(\s*age\s*)'
	_ExpressionDownloads	= 'downloaded\s*(\d+)\s*time'
	_ExpressionNext			= '(>|&gt;){1,}'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'EXTTorrents',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.',
			rank						= 3,
			performance					= ProviderHtml.PerformanceGood,
			status						= ProviderHtml.StatusImpaired, # Cloudflare.

			link						= Provider._Link,
			mirror						= Provider._Mirror,
			unblock						= Provider._Unblock,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodeMinus,

			searchQuery					= Provider._Path % (ProviderHtml.TermQuery, ProviderHtml.TermOffset, ProviderHtml.TermCategory),
			searchCategoryMovie			= Provider._CategoryMovie,
			searchCategoryShow			= Provider._CategoryShow,

			# The hash could be extracted from the .torrent link on the search page, but there are too many that do not have a download link, only a streaming link that does not contain the hash.
			#extractOptimizeData		= HtmlDiv(class_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			#extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeDetails),
			#extractList				= [HtmlResults(class_ = Provider._AttributeTable)],
			#extractDetails				= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeHref)],
			#extractLink				= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeLinks), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			#extractFileName			= [HtmlResult(index = 0), HtmlLink()],
			#extractFileSize			= [HtmlResult(index = 1)],
			#extractSourceTimeInexact	= [HtmlResult(index = 3)],
			#extractSourceApproval		= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeInfo, extract = [Html.ParseTextNested, Provider._ExpressionDownloads])],
			#extractSourceSeeds			= [HtmlResult(index = 4)],
			#extractSourceLeeches		= [HtmlResult(index = 5)],

			# The website changed and now has the magnet on the main page.
			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			extractList					= [HtmlResults(class_ = Provider._AttributeTable)],
			extractLink					= [HtmlResult(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlResult(index = 0), HtmlLink()],
			extractFileSize				= [HtmlResult(index = 1)],
			extractSourceTimeInexact	= [HtmlResult(index = 3)],
			extractSourceApproval		= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeInfo, extract = [Html.ParseTextNested, Provider._ExpressionDownloads])],
			extractSourceSeeds			= [HtmlResult(index = 4)],
			extractSourceLeeches		= [HtmlResult(index = 5)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(index = -1, extract = Html.ParseText)])
			if not last or not Regex.match(data = last, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		if value: value = Regex.remove(data = value, expression = Provider._ExpressionAge, all = True)
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		if value and details:
			result = ProviderHtml.ApprovalDefault
			try: result += (1 - result) * (float(value) / Provider._LimitApproval)
			except: pass
			return result
		return value
