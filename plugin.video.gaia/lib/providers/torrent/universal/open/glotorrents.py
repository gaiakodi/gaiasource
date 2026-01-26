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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlImage
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://glodls.to', 'https://gtso.cc'] # Offline: https://gtdb.to https://gtdb.cc
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'glotorrents', ProviderHtml.UnblockFormat3 : 'glotorrents', ProviderHtml.UnblockFormat4 : 'glotorrents'}
	_Path					= 'search_results.php'

	_CategoryMovie			= ['1', '72', '28']		# 72 = Packs, 28 = Anime
	_CategoryShow			= ['41', '72', '28']	# 72 = Packs, 28 = Anime

	_ParameterSearch		= 'search'
	_ParameterCategory		= 'cat'
	_ParameterCategory2		= 'c'
	_ParameterPage			= 'page'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'seeders'
	_ParameterOrder			= 'order'
	_ParameterDescending	= 'desc'
	_ParameterDead			= 'incldead'
	_ParameterExternal		= 'inclexternal'

	_AttributeContainer		= 'mCol'
	_AttributeTable			= 'ttable_headinner'
	_AttributePages			= 'pagination'

	_ExpressionNext			= r'(next)'
	_ExpressionVerified		= r'(verified)'
	_ExpressionVip			= r'(vip)'
	_ExpressionAdmin		= r'(admin)'
	_ExpressionUploader		= r'^(uploader)'		# Match start, since it can also be "Verified Uploader".
	_ExpressionAnonymous	= r'^(anonymous)$'	# Match start/end, to exclude usernames with "anonymous" in them.

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'GloTorrents',
			description					= '{name} is a less-known {container} site, but has many and high-quality results with good metadata. The site contains results in various languages, but most of them are in English.',
			rank						= 4,

			# Update (2025-06): Domain is up, but searches return a HTTP 500 error.
			# Using "retryCount" solves the issue for now.
			performance					= ProviderHtml.PerformanceGood - ProviderHtml.PerformanceStep,

			link						= Provider._Link,
			unblock						= Provider._Unblock,

			customVerified				= True,

			# Update (2025-06)
			# GloTorrents returns an empty page with HTTP error 500 (Internal Server Error) with most requests.
			# However, when retrying the same request immediately afterwards (with the same domain, query, etc), it suddenly returns results.
			# Not sure if this is a temporary issue with GloTorrents' server, or if this is a more permanent issue.
			# Retrying the requests seems to solve the issue and returns links.
			retryCount					= 3,
			retryError					= 500,
			retryDelay					= 1,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 0,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,

											# Combine categories.
											#ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestPath : Provider._Path + '?' + ProviderHtml.TermCategory,

											ProviderHtml.RequestData : {
												Provider._ParameterSearch	: ProviderHtml.TermQuery,
												Provider._ParameterPage		: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
												Provider._ParameterOrder	: Provider._ParameterDescending,
												Provider._ParameterDead		: 1, # Included dead results.
												Provider._ParameterExternal	: 0, # Included local and external.

												# Combine categories.
												#Provider._ParameterCategory	: ProviderHtml.TermCategory,
												Provider._ParameterCategory	: 0,
											},
										},

			# Combine categories.
			#searchCategoryMovie		= Provider._CategoryMovie,
			#searchCategoryShow			= Provider._CategoryShow,
			searchCategoryMovie			= '&'.join(['%s%s=1' % (Provider._ParameterCategory2, i) for i in Provider._CategoryMovie]),
			searchCategoryShow			= '&'.join(['%s%s=1' % (Provider._ParameterCategory2, i) for i in Provider._CategoryShow]),

			extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			extractList					= [HtmlResults(class_ = Provider._AttributeTable, skip = 1)], # Every other row is a divider.
			extractLink					= [HtmlResult(index = 3), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlResult(index = 1), HtmlLink(index = -1, extract = Html.AttributeTitle)], # Use the title and not the inner text, since the text is cut off (...).
			extractFileSize				= [HtmlResult(index = 4)],
			extractReleaseUploader		= [HtmlResult(index = 7)],
			extractSourceSeeds			= [HtmlResult(index = 5, extract = [Html.ParseText, Html.ParseRemoveComma])],
			extractSourceLeeches		= [HtmlResult(index = 6, extract = [Html.ParseText, Html.ParseRemoveComma])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(index = -1, extract = Html.ParseText)])
			if not last or not Regex.match(data = last, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processReleaseUploader(self, value, item, details = None, entry = None):
		if value and Regex.match(data = value, expression = Provider._ExpressionAnonymous): value = None
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		item = self.extractHtml(item, [HtmlResult(index = 7)])

		verified = self.extractHtml(item, HtmlImage(title_ = Provider._ExpressionVerified))
		if self.customVerified() and not verified: return ProviderHtml.Skip
		extra = (0.1 if verified else 0.0)

		admin = self.extractHtml(item, HtmlImage(title_ = Provider._ExpressionAdmin))
		if admin: return ProviderHtml.ApprovalExcellent

		vip = self.extractHtml(item, HtmlImage(title_ = Provider._ExpressionVip))
		if vip: return ProviderHtml.ApprovalGood + extra

		uploader = self.extractHtml(item, HtmlImage(title_ = Provider._ExpressionUploader))
		if uploader: return ProviderHtml.ApprovalMedium + extra

		return ProviderHtml.ApprovalDefault + extra
