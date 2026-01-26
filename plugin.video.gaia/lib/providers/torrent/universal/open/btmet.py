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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlScript, HtmlBold
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	# https://github.com/btmet/home
	_Link					= ['https://btmet.com']
	_Path					= 'search.php'

	_Category				= [1] # 1 = Video

	_ParameterQuery			= 'q'
	_ParameterCategory		= 'c'
	_ParameterPage			= 'p'
	_ParameterSort			= 'o'
	_ParameterRelevance		= '0'

	_CookieCover			= 'sp'
	_CookieFile				= 'sf'
	_CookieName				= 'br'
	_CookiePreview			= 'di'
	_CookieCovered			= 'pic'
	_CookieAdult			= 'r18'
	_CookieSize				= 's'
	_CookieTime				= 't'
	_CookieSort				= 'sort'
	_CookieFalse			= 'false'
	_CookieOne				= '1'
	_CookieZero				= '0'

	_AttributeWall			= 'wall'
	_AttributeItem			= 'search-item'
	_AttributeTitle			= 'item-title'
	_AttributeBar			= 'item-bar'
	_AttributeTime			= 'fromnow'
	_AttributePages			= 'bottom-pager'

	_ExpressionSize			= r'file\s*size\s*:\s*(\d+(?:\.\d+)?\s*[kmgt]?b)(?:$|\s|&nbsp;)'
	_ExpressionNext			= r'(next)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		cookies = {
			Provider._CookieCover : Provider._CookieFalse,
			Provider._CookieFile : Provider._CookieFalse,
			Provider._CookieName : Provider._CookieFalse,
			Provider._CookiePreview : Provider._CookieZero,
			Provider._CookieCovered : Provider._CookieZero,
			Provider._CookieSize : Provider._CookieZero,
			Provider._CookieTime : Provider._CookieZero,
			Provider._CookieSort : Provider._CookieZero,
		}
		if not self.customAdult(): cookies[Provider._CookieAdult] = Provider._CookieOne

		ProviderHtml.initialize(self,
			name						= 'BtMet',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has a lot of missing trivial metadata and contains a number of fake uploads. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.',
			rank						= 2,
			performance					= ProviderHtml.PerformanceMedium - ProviderHtml.PerformanceStep,
			status						= ProviderHtml.StatusDead, # Cloudflare. Update (2025-06): Domain is down.

			link						= Provider._Link,

			customAdult					= True,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			# Starts at page 50 and decreases from there.
			offsetStart					= 50,
			offsetIncrease				= -1,

			formatEncode				= ProviderHtml.FormatEncodeQuote,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestCookies : cookies,
											ProviderHtml.RequestData : {
												Provider._ParameterQuery	: ProviderHtml.TermQuery,
												Provider._ParameterCategory	: ProviderHtml.TermCategory,
												Provider._ParameterPage		: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterRelevance,
											},
										},

			searchCategoryMovie			= Provider._Category,
			searchCategoryShow			= Provider._Category,

			extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeWall),
			extractList					= HtmlDiv(class_ = Provider._AttributeItem),
			extractLink					= [HtmlLink(href_ = r'^' + ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)], # ^: must start with magnet:....
			extractFileName				= [HtmlDiv(class_ = Provider._AttributeTitle), HtmlScript(extract = [Html.ParseCode, r'decodeURIComponent\([\'"](.*?)[\'"]\)', Html.ParseDecode])],
			extractFileSize				= [HtmlDiv(class_ = Provider._AttributeBar, extract = [Html.ParseTextNested, Provider._ExpressionSize])],
			extractSourceTimeInexact	= [HtmlDiv(class_ = Provider._AttributeBar), HtmlBold(class_ = Provider._AttributeTime, extract = 't')],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			current = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(index = -2, extract = Html.ParseTextNested)])
			if current and not Regex.match(data = current, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processLink(self, value, item, details = None, entry = None):
		return value if value else ProviderHtml.Skip

	def processFileName(self, value, item, details = None, entry = None):
		if value:
			try: return self.parseHtml(value).text
			except: self.logError()
		return None
