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

from lib.providers.core.html import ProviderHtml, Html, HtmlBody, HtmlResultsTable, HtmlResult, HtmlLink, HtmlDiv, HtmlSpan

class Provider(ProviderHtml):

	_Link					= ['https://isohunt.app', 'https://isohunt.ch', 'https://isohunt.nz']
	_Mirror					= ['https://techraver.com/isohunt-proxy-mirror-sites', 'https://isohunt.page']
	_Path					= 'torrents'

	_CategoryMovie			= [5, 1] # 5 = Movies, 1 = Anime
	_CategoryShow			= [8, 1] # 8 = TV, 1 = Anime

	_ParameterQuery			= 'ihq'
	_ParameterCategory		= 'iht'
	_ParameterOffset		= 'Torrent_page'
	_ParameterSort			= 'Torrent_sort'
	_ParameterSeeds			= 'seeders'

	_AttributeSearch		= 'search-list'
	_AttributeTorrents		= 'table-torrents'
	_AttributeTitle			= 'title-row'
	_AttributeSize			= 'size-row'
	_AttributeTime			= 'date-row'
	_AttributeSeeds			= 'seeds'
	_AttributeLeeches		= 'leechs'
	_AttributeMagnet		= 'btn-magnet'

	_ExpressionDetails		= '(torrent_details)'
	_ExpressionMagnet		= '(?:url|link|magnet)=(magnet.*?)(?:$|&)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'IsoHunt',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. The search page of {name} does not contain all the metadata. A subpage must therefore be retrieved for each result in order to extract the magnet link, which substantially increases scraping time.',
			rank						= 3,
			performance					= ProviderHtml.PerformanceBad,

			link						= Provider._Link,
			mirror						= Provider._Mirror,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 0,
			offsetIncrease				= 40,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterQuery	: ProviderHtml.TermQuery,
												Provider._ParameterCategory	: ProviderHtml.TermCategory,
												Provider._ParameterOffset	: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
											},
										},

			searchCategoryMovie			= Provider._CategoryMovie,
			searchCategoryShow			= Provider._CategoryShow,

			extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeSearch),
			extractOptimizeDetails		= HtmlBody(),
			extractList					= [HtmlResultsTable(class_ = Provider._AttributeTorrents)],
			extractDetails				= [HtmlResult(class_ = Provider._AttributeTitle), HtmlLink(href_ = Provider._ExpressionDetails, extract = Html.AttributeHref)],
			extractLink					= [ProviderHtml.Details, HtmlLink(class_ = Provider._AttributeMagnet, extract = [Html.AttributeHref, Provider._ExpressionMagnet, Html.ParseDecode])],
			extractFileName				= [HtmlResult(class_ = Provider._AttributeTitle), HtmlLink(href_ = Provider._ExpressionDetails, extract = Html.ParseTextNested)],
			extractFileSize				= [HtmlResult(class_ = Provider._AttributeSize, extract = Html.ParseTextNested)],
			extractSourceTimeInexact	= [HtmlResult(class_ = Provider._AttributeTime, extract = Html.ParseTextNested)],
			extractSourceSeeds			= [ProviderHtml.Details, HtmlSpan(class_ = Provider._AttributeSeeds)],
			extractSourceLeeches		= [ProviderHtml.Details, HtmlSpan(class_ = Provider._AttributeLeeches)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	# There is no proper way to detect the last page.
	# Paging continues infinitely until the result table is empty.
	'''def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlLink(class_ = Provider._AttributePage, index = -1, extract = Html.ParseTextNested)])
			if last and not Regex.match(data = last, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()'''
