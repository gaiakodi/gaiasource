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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlTable, HtmlTableRow, HtmlTableCell, HtmlLink, HtmlMain, HtmlDiv
from lib.modules.network import Networker

class Provider(ProviderHtml):

	_Link					= ['https://www5.yggtorrent.re', 'https://www5.yggtorrent.fi', 'https://www5.yggtorrent.la', 'https://www5.yggtorrent.nz', 'https://www5.yggtorrent.si', 'https://www5.yggtorrent.se', 'https://www5.yggtorrent.to', 'https://www5.yggtorrent.gg', 'https://www5.yggtorrent.is']
	_Mirror					= ['https://www5.yggtorrent.fi/engine/domains']

	_PathSearch				= 'engine/search?do=search&name=%s&category=2145&sub_category=%s&page=%s' # 2145 = Video
	_PathDownload			= 'engine/download_torrent?id=%s'
	_PathLogin				= 'user/login'

	_LimitApproval			= 500

	_CategoryAll			= 'all'
	_CategoryMovie			= ['2183', '2181', '2178'] # 2183 = Movie, 2181 = Documentary, 2178 = Animation
	_CategoryShow			= ['2185', '2184', '2182', '2179'] # 2185 = Show, 2184 = TV Show, 2182 = TV Program, 2179 = Animation Series

	_ParameterUsername		= 'id'
	_ParameterPassword		= 'pass'

	_AttributeContent		= 'ct'
	_AttributeTable			= 'table'
	_AttributeName			= 'torrent_name'
	_AttributeHidden		= 'hidden'
	_AttributeTorrent		= 'infos-torrent'
	_AttributeInformation	= 'informations'
	_AttributePages			= 'pagination'
	_AttributeNext			= 'next'

	_ExpressionId			= '.+\/(.*?)-'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'YggTorrent',
			description				= '{name} is the most widely used torrent site from France. The site contains results in various languages, but most of them are in French. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail. Most VPN servers are subject to these Cloudflare restrictions, but most VPN services have a few servers that are except from Cloudflare and are able to scrape the site. The search page of {name} does not contain all the metadata. A subpage must therefore be retrieved for each result in order to extract hashes, which substantially increases scraping time.',
			rank					= 4,
			performance				= ProviderHtml.PerformanceBad,
			#status					= ProviderHtml.StatusImpaired, # It seems that YGG has removed/reduced Cloudflare protection.

			link					= Provider._Link,
			mirror					= Provider._Mirror,

			accountUsername			= True,
			accountPassword			= True,
			accountAuthentication	= {
										ProviderHtml.ProcessMode : ProviderHtml.AccountModeResolve,

										# The first request creates the cookies, the second request assigns authentication to the cookie.
										# It seems that the new YGG does not require this anymore.
										#ProviderHtml.ProcessIterations : 2,

										ProviderHtml.ProcessRequest : {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodPost,
											ProviderHtml.RequestPath : Provider._PathLogin,
											ProviderHtml.RequestData : {
												Provider._ParameterUsername : ProviderHtml.TermAuthenticationUsername,
												Provider._ParameterPassword : ProviderHtml.TermAuthenticationPassword,
											},
										},
										ProviderHtml.ProcessExtract : {
											ProviderHtml.RequestCookies : True,
										},

										# The second login request returns error 403 (at least through Cloudflare), although the request was succesful.
										# Scraping works, but provider validation fails at the account step.
										# Manually validate the request, instead of relying on the HTTP return code.
										#ProviderHtml.ProcessValidate : {
										#	ProviderHtml.RequestCookies : {'_ygg' : '.+'},
										#},
									},

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 0,
			offsetIncrease			= 50,

			# Searching these also finds others:
			#	saison: saisons
			#	integrale: intégrale
			#	integral: intégral
			#	trilogy: trilogie
			#	complete: complet
			queryYear				= False, # Many movies do not contain the year.

			formatEncode			= ProviderHtml.FormatEncodePlus,

			searchQuery				= Provider._PathSearch % (ProviderHtml.TermQuery, ProviderHtml.TermCategory, ProviderHtml.TermOffset),

			# Search all video subcategories together, instead of separately.
			# Searching indivdual subcategories, especially for shows with multiple pack labels, can result in 20+ requests to main pages that are mostly empty.
			# Speed up the process by only searching one subcategory and then filter out those few incorrect results in processItem().
			searchCategory			= Provider._CategoryAll,
			#searchCategoryMovie	= Provider._CategoryMovie,
			#searchCategoryShow		= Provider._CategoryShow,

			extractOptimizeData		= HtmlMain(class_ = Provider._AttributeContent),
			extractList				= [HtmlResults(class_ = Provider._AttributeTable)],
			extractHash				= [ProviderHtml.Details, HtmlTable(class_ = Provider._AttributeInformation), HtmlTableRow(index = 4), HtmlTableCell(index = 1)],
			extractDetails			= [HtmlResult(index = 1), HtmlLink(id_ = Provider._AttributeName, extract = Html.AttributeHref)],
			extractLink				= [HtmlResult(index = 1), HtmlLink(id_ = Provider._AttributeName, extract = [Html.AttributeHref, Provider._ExpressionId])],
			extractFileName			= [HtmlResult(index = 1), HtmlLink(id_ = Provider._AttributeName)],
			extractFileSize			= [HtmlResult(index = 5)],
			extractReleaseUploader	= [ProviderHtml.Details, HtmlTable(class_ = Provider._AttributeInformation), HtmlTableRow(index = 5), HtmlTableCell(index = 1)],
			extractSourceTime		= [HtmlResult(index = 4), Html(class_ = Provider._AttributeHidden)],
			extractSourceApproval	= [HtmlResult(index = 6)],
			extractSourceSeeds		= [HtmlResult(index = 7)],
			extractSourceLeeches	= [HtmlResult(index = 8)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [Html(class_ = Provider._AttributePages), HtmlLink(rel_ = Provider._AttributeNext)])
			if not next: return ProviderHtml.Skip
		except: self.logError()

	def processItem(self, item):
		type = self.extractHtml(item, [HtmlResult(index = 0), HtmlDiv(extract = Html.ParseText)])
		categories = Provider._CategoryShow if self.parameterMediaShow() else Provider._CategoryMovie
		if not type or not type in categories: return ProviderHtml.Skip
		return item

	def processLink(self, value, item, details = None, entry = None):
		return Networker.linkJoin(self.linkCurrent(), Provider._PathDownload % value)

	def processSourceApproval(self, value, item, details = None, entry = None):
		try:
			value = float(value) / Provider._LimitApproval
			return min(ProviderHtml.ApprovalExcellent, value)
		except:
			return ProviderHtml.ApprovalDefault
