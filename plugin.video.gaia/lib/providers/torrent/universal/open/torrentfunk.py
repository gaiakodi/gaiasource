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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlMain, HtmlLink, HtmlDiv, HtmlImage
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://www.torrentfunk.com', 'https://www.torrentfunk2.com'] # Update (2024-12): Main domain needs www subdomain, otherwise it redirects to an invalid URL.
	_Mirror					= ['https://torrents-proxy.com/torrentfunk/']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'torrentfunk'}
	_Path					= '%s/torrents/%s.html'

	_LimitCount				= 250

	_CategoryMovie			= ['movie', 'anime']
	_CategoryShow			= ['television', 'anime']

	_ParameterCount			= 'i'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'seeds'
	_ParameterOrder			= 'order'
	_ParameterDescending	= 'desc'
	_ParameterPage			= 'page'
	_ParameterVerified		= 'v'
	_ParameterEnabled		= 'on'
	_ParameterDisabled		= 'off'

	_AttributeMain			= 'tmain'
	_AttributeContent		= 'content'
	_AttributePages			= 'pag'

	_ExpressionHash			= r'infohash.*?' + ProviderHtml.ExpressionSha + r'(?:$|\s|<)'
	_ExpressionGood			= r'good'
	_ExpressionBad			= r'bad'
	_ExpressionVerified		= r'verified'
	_ExpressionNext			= r'next'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'TorrentFunk',
			description				= '{name} is one of the older {container} sites. The site contains results in various languages, but most of them are in English. The search page of {name} does not contain all the metadata. A subpage must therefore be retrieved for each result in order to extract the magnet link, which substantially increases scraping time. {name} has basic Cloudflare protection that is mostly bypassable.',
			rank					= 3, # Lower rank, since there are no magnets links, and the dynamiclly created magnets might not contain all trackers.
			performance				= ProviderHtml.PerformanceBad,

			link					= Provider._Link,
			mirror					= Provider._Mirror,
			unblock					= Provider._Unblock,

			customVerified			= True,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			formatEncode			= ProviderHtml.FormatEncodeMinus,
			formatCase				= ProviderHtml.FormatCaseLower, # Must be lower, otherwise TorrentFunk redirects to the lower-case path and drops some GET parameters, including the page number.

			searchQuery				= {
										ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
										ProviderHtml.RequestPath : Provider._Path % (ProviderHtml.TermCategory, ProviderHtml.TermQuery),
										ProviderHtml.RequestData : {
											Provider._ParameterCount	: Provider._LimitCount,
											Provider._ParameterSort		: Provider._ParameterSeeds,
											Provider._ParameterOrder	: Provider._ParameterDescending,
											Provider._ParameterPage		: ProviderHtml.TermOffset,
											Provider._ParameterVerified	: Provider._ParameterEnabled if self.customVerified() else Provider._ParameterDisabled,

										},
									},
			searchCategoryMovie		= Provider._CategoryMovie,
			searchCategoryShow		= Provider._CategoryShow,

			extractParser			= ProviderHtml.ParserHtml5, # Some HTML errors if there is no "verified" DIV.
			extractOptimizeData		= HtmlMain(), # To detect the last page in processOffset().
			extractOptimizeDetails	= HtmlMain(),
			extractList				= [HtmlResults(class_ = Provider._AttributeMain, index = -1, start = 1)],
			extractDetails			= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeHref)],
			extractHash				= [ProviderHtml.Details, Html(extract = [Html.ParseCode, Provider._ExpressionHash])], # ParseCode instead of ParseTextNested, otherwise newlines are gone.
			extractFileName			= [HtmlResult(index = 0), HtmlLink(extract = Html.ParseTextNested)], # Very long titles are cut off (...), but on the main and details page, there is not perfect/reliable way to get the full title. Let Stream extract it from the magnet.
			extractFileSize			= [HtmlResult(index = 2)],
			extractReleaseUploader	= [HtmlResult(index = 5)],
			extractSourceTime		= [HtmlResult(index = 1)],
			extractSourceApproval	= [HtmlResult(index = 0)],
			extractSourceSeeds		= [HtmlResult(index = 3)],
			extractSourceLeeches	= [HtmlResult(index = 4)],
		)

	##############################################################################
	# PROCESS
	#############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlDiv(id_ = Provider._AttributePages), HtmlLink(index = -1, extract = Html.ParseTextNested)])
			if not next or not Regex.match(data = next, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processSourceApproval(self, value, item, details = None, entry = None):
		if not details:
			result = ProviderHtml.ApprovalDefault
			images = self.extractHtml(item, [HtmlResult(index = 0), HtmlImage()])
			if images:
				for image in images:
					if image and image['title']:
						image = image['title']
						if Regex.match(data = image, expression = Provider._ExpressionVerified): result += 0.5
						elif Regex.match(data = image, expression = Provider._ExpressionGood): result += 0.3
						elif Regex.match(data = image, expression = Provider._ExpressionBad): result -= 0.4
			return result
		return None
