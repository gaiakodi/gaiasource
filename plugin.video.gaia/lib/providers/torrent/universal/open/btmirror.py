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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlParagraph
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://btsao.com', 'https://btmirror.me', 'https://cl.btm103.xyz']
	_Mirror					= ['https://btmirror.neocities.org']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'btmirror', ProviderHtml.UnblockFormat3 : 'btmirror'}

	_Path					= 'en/search/%s/%s'

	_LimitApproval			= 1000

	_Category				= ['video']

	_ParameterCategory		= 'c'
	_ParameterSort			= 's'
	_ParameterTime			= 'create_time'

	_AttributeSearch		= 'search-option'
	_AttributeBox			= 'ssbox'
	_AttributeTorrent		= 'torrent'
	_AttributeBar			= 'sbar'
	_AttributeMagnet		= 'magnet'
	_AttributeDescription	= 'desc'
	_AttributePages			= 'pagination'
	_AttributePage			= 'flag_pg'

	_ExpressionSize			= 'file\s*size\s*:\s*(\d+(?:\.\d+)?\s*[kmgt]?b)(?:$|\s|&nbsp;)'
	_ExpressionDownloads	= 'download\s*times\s*[:：]\s*(\d+)'
	_ExpressionNext			= '(next)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'BtMirror',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has a lot of missing trivial metadata. The search page of {name} does not contain all the metadata. A subpage must therefore be retrieved for each result in order to extract the magnet link, which substantially increases scraping time.',
			rank						= 2,
			performance					= ProviderHtml.PerformanceBad,
			status						= ProviderHtml.StatusDead, # Now redirects to porn site. Update (2024-12): All domains seem to be gone.

			link						= Provider._Link,
			mirror						= Provider._Mirror,
			unblock						= Provider._Unblock,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodeQuote,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path % (ProviderHtml.TermQuery, ProviderHtml.TermOffset),
											ProviderHtml.RequestData : {
												Provider._ParameterCategory	: ProviderHtml.TermCategory,
												Provider._ParameterSort		: Provider._ParameterTime,
											},
										},

			searchCategoryMovie			= Provider._Category,
			searchCategoryShow			= Provider._Category,

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeSearch),
			extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeTorrent),
			extractList					= [HtmlDiv(class_ = Provider._AttributeBox)],
			extractDetails				= [HtmlLink(extract = Html.AttributeHref)],
			extractLink					= [ProviderHtml.Details, HtmlParagraph(class_ = Provider._AttributeMagnet), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlLink(extract = Html.ParseTextNested)],
			extractFileSize				= [HtmlDiv(class_ = Provider._AttributeBar, extract = [Html.ParseTextNested, Provider._ExpressionSize])],
			extractSourceApproval		= [ProviderHtml.Details, HtmlParagraph(class_ = Provider._AttributeDescription, extract = [Html.ParseTextNested, Provider._ExpressionDownloads])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(class_ = Provider._AttributePage, index = -1, extract = Html.ParseTextNested)])
			if last and not Regex.match(data = last, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processSourceApproval(self, value, item, details = None, entry = None):
		if details:
			result = ProviderHtml.ApprovalDefault
			try: result += ((1 - result) * (float(value) / Provider._LimitApproval))
			except: pass
			return result
		return None
