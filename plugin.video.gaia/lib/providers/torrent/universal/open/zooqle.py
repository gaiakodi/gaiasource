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

# Update (2024-12):
#	There are 2 new domains:
#		https://zooqle.io
#		https://zooqle.pro
# But they do not have a table layout anymore.
# Plus it contains very few links.
# Plus it only has movies, no shows.
# So probably not worth implementing these new domains.

class Provider(ProviderHtml):

	_Link				= ['https://zooqle.com']
	_Mirror				= ['https://torrends.to/proxy/zooqle']
	_Unblock			= {ProviderHtml.UnblockFormat1 : 'zooqle', ProviderHtml.UnblockFormat2 : 'zooqle', ProviderHtml.UnblockFormat3 : 'zooqle2', ProviderHtml.UnblockFormat4 : 'zooqle'}
	_Path				= 'search?q=%s+category%%3A%s&pg=%s&v=t&s=ns&sd=d' # s=ns: sort by seeds, sd=d: sort descending.

	_CategoryMovie		= 'Movies'
	_CategoryShow		= 'TV'
	_CategoryAnime		= 'Anime'

	_AttributeMain		= 'zq-small'
	_AttributeTable		= 'table-torrents'
	_AttributeLong		= 'long'
	_AttributePages		= 'pagination'

	_ExpressionSeeds	= 'seed.*?([\d,]+)'
	_ExpressionLeeches	= 'leech.*?([\d,]+)'
	_ExpressionStandard	= '(std)'
	_ExpressionAudio	= '(audio)'
	_ExpressionLanguage	= '(language)'
	_ExpressionNext		= '(next)'
	_ExpressionMute		= '(mute)'
	_ExpressionExclude	= '(med|low)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'Zooqle',
			description					= '{name} has a very large database of {containers} and metadata. The site contains results in various languages, but most of them are in Russian or English.',
			rank						= 5,
			performance					= ProviderHtml.PerformanceGood,
			status						= ProviderHtml.StatusDead, # 2022-06-20: website hass been down. From Reddit is seems to be down from April 2022. Update (2024-12): Still down.

			link						= Provider._Link,
			mirror						= Provider._Mirror,
			unblock						= Provider._Unblock,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchQuery					= Provider._Path % (ProviderHtml.TermQuery, ProviderHtml.TermCategory, ProviderHtml.TermOffset),
			searchCategoryMovie			= ','.join([Provider._CategoryMovie, Provider._CategoryAnime]),
			searchCategoryShow			= ','.join([Provider._CategoryShow, Provider._CategoryAnime]),

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeMain), # To detect the last page in processOffset().
			extractList					= [HtmlResults(class_ = Provider._AttributeTable)],
			extractLink					= [HtmlResult(index = 2), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlResult(index = 1), HtmlLink()],
			extractFileSize				= [HtmlResult(index = 3)],
			extractFileExtra			= [HtmlResult(index = 1), HtmlDiv()], # Extract this as fileNameExtra, instead of individual values, since the filename might contain more specific details (eg: the div contains "3D", but the filename contains "3D SBS").
			extractSourceTimeInexact	= [HtmlResult(index = 4)],
			extractSourceSeeds			= [HtmlResult(index = 5), HtmlDiv(extract = [Html.AttributeTitle, Provider._ExpressionSeeds])],
			extractSourceLeeches		= [HtmlResult(index = 5), HtmlDiv(extract = [Html.AttributeTitle, Provider._ExpressionLeeches])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [Html(class_ = Provider._AttributePages), HtmlLink(attribute = {Html.AttributeAriaLabel : Provider._ExpressionNext, Html.AttributeClass : Provider._ExpressionMute})])
			if last: return ProviderHtml.Skip
		except: self.logError()

	def processFileExtra(self, value, item, details = None, entry = None):
		try: value = Regex.remove(data = value, expression = Provider._ExpressionExclude, all = True).strip()
		except: pass
		return value

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		if value and Provider._AttributeLong in value: return None
		return value
