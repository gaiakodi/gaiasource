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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlTable, HtmlImage, HtmlArticle, HtmlListUnordered, HtmlListItem
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	# Update (2024-12): Important to add the www subdomain, otherwise without it, the main domain throws an SSL error. The SSL certificate is probably only valid for the www subdomain.
	_Link					= ['https://www.torlock.com', 'https://www.torlock2.com'] # Main domain is down. torlock2 is still working. Update (2024-12): main domain works again, but not torlock2, due to an expired SSL.
	_Mirror					= ['https://torrents-proxy.com/torlock/']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'torlock', ProviderHtml.UnblockFormat3 : 'torlock'}

	_Path					= '%s/torrents/%s.html'

	_LimitApproval			= 3

	_CategoryMovie			= 'movie'
	_CategoryShow			= 'television'

	_ParameterPage			= 'page'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'seeds' # Sorting by seeds does not seem to work.

	_AttributeContent		= 'table-responsive'
	_AttributeTable			= 'table'
	_AttributePages			= 'pagination'


	_ExpressionHash			= r'(?:info\s*)?hash\s*' + ProviderHtml.ExpressionSha
	_ExpressionVerified		= r'(verified)'
	_ExpressionNext			= r'(next)'
	_ExpressionApproval		= r'(\-?\d+)\s*(?:good|bad)?\s*vote'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'TorLock',
			description				= '{name} is a well-known {container} site. The site contains results in various languages, but most of them are in English. {name} requests subpages in order to extract the magnet link and other metadata, which substantially increases scraping time.',

			# Update (2025-12):
			# Both domains are still working, but they are loading very slowly.
			# And they often result in a "Read timed out (read timeout=30)" or "EOF occurred in violation of protocol (_ssl.c:1006)" errors.
			# But occasionally it still returns a few results, although most queries/pages fail.
			# The rank/performance is already low because of subpages.
			rank					= 3,
			performance				= ProviderHtml.PerformanceBad,

			link					= Provider._Link,
			mirror					= Provider._Mirror,
			unblock					= Provider._Unblock,

			customVerified			= True,

			streamTime				= '%m/%d/%Y', # Has US date format (month first). Pass custom format in and do not use the built-in formats that place the day first.

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			formatEncode			= ProviderHtml.FormatEncodeMinus,

			searchQuery				= {
										ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
										ProviderHtml.RequestPath : Provider._Path % (ProviderHtml.TermCategory, ProviderHtml.TermQuery),
										ProviderHtml.RequestData : {
											Provider._ParameterPage	: ProviderHtml.TermOffset,
											Provider._ParameterSort	: Provider._ParameterSeeds,
										},
									},
			searchCategoryMovie		= Provider._CategoryMovie,
			searchCategoryShow		= Provider._CategoryShow,

			extractOptimizeData		= HtmlDiv(class_ = Provider._AttributeContent, index = -1), # To detect the last page in processOffset().
			extractOptimizeDetails	= HtmlArticle(),
			extractList				= [HtmlResults(class_ = Provider._AttributeTable, index = -1)],
			extractDetails			= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeHref)],

			# Update (2024-12): There do not seem to be magnets links anymore, only links to .torrent files.
			# But the hash is still listed.
			extractLink				= [ProviderHtml.Details, HtmlTable(class_ = Provider._AttributeTable), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractHash				= [ProviderHtml.Details, Html(extract = [Html.ParseTextNested, Provider._ExpressionHash])],

			extractFileName			= [HtmlResult(index = 0), HtmlLink()],
			extractFileSize			= [HtmlResult(index = 2)],
			extractSourceApproval	= [ProviderHtml.Details, Html(extract = [Html.ParseText, Provider._ExpressionApproval])],
			extractSourceTime		= [HtmlResult(index = 1)],
			extractSourceSeeds		= [HtmlResult(index = 3)],
			extractSourceLeeches	= [HtmlResult(index = 4)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlLink(index = -1, extract = Html.AttributeAriaLabel)])
			if not last or not Regex.match(data = last, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		if self.customVerified():
			verified = str(self.extractHtml(item, [HtmlResult(index = 0), HtmlImage(title_ = Provider._ExpressionVerified)]))
			if not verified: return ProviderHtml.Skip

	def processSourceApproval(self, value, item, details = None, entry = None):
		if details:
			result = ProviderHtml.ApprovalDefault
			try:
				value = float(value.replace(',', ''))
				result += ((1 - result) * (value / Provider._LimitApproval))
			except: pass
			return result
		return value
