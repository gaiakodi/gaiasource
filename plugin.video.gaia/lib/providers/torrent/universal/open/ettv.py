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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlParagraph, HtmlFieldSet
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://ettvcentral.com', 'https://ettv.be', 'https://ettvdl.com']
	_Mirror					= ['https://ettvproxies.com']
	_Unblock				= {ProviderHtml.UnblockFormat1 : 'ettv', ProviderHtml.UnblockFormat2 : 'ettv', ProviderHtml.UnblockFormat3 : 'ettv', ProviderHtml.UnblockFormat4 : 'ettv'}
	_Path					= 'torrents-search.php'

	_ParameterQuery			= 'search'
	_ParameterPage			= 'page'

	_AttributeContent		= 'myFrame-content'
	_AttributeContainer		= 'container-fluid'
	_AttributeTable			= 'table'
	_AttributeDownload		= 'downloadbox'
	_AttributeDetails		= 'download'

	_ExpressionName			= '(.*?)\s*torrent$'
	_ExpressionTime			= 'date\s*added\s*:\s*(.*)'
	_ExpressionLanguage		= 'lang\s*:\s*(.*)'
	_ExpressionCategory		= 'category\s*:\s*(.*)'
	_ExpressionMovie		= '(movie)'
	_ExpressionShow			= '(tv)'
	_ExpressionNext			= '(next)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'ETTV',
			description					= '{name} is a well-known {container} site. The site contains results in various languages, but most of them are in English. {name} requests subpages in order to extract the magnet link and other metadata, which substantially increases scraping time.',
			rank						= 3,
			performance					= ProviderHtml.PerformanceBad,
			status						= ProviderHtml.StatusDead, # Domain does not load for a week now. Update (2024-12): Still down. Update (2025-06): Still down..

			link						= Provider._Link,
			mirror						= Provider._Mirror,
			unblock						= Provider._Unblock,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 0,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterQuery	: ProviderHtml.TermQuery,
												Provider._ParameterPage		: ProviderHtml.TermOffset,
											},
										},

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContent), # To detect the last page in processOffset().
			extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeContainer, index = -1),
			extractList					= [HtmlResults(class_ = Provider._AttributeTable)],
			extractDetails				= [HtmlResult(index = 1), HtmlLink(extract = Html.AttributeHref)],
			extractLink					= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeDownload), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlResult(index = 1), HtmlLink(extract = [Html.AttributeTitle, Provider._ExpressionName])],
			extractFileSize				= [HtmlResult(index = 3)],
			extractAudioLanguageInexact	= [ProviderHtml.Details, HtmlDiv(recursive = False), HtmlFieldSet(class_ = Provider._AttributeDetails, index = 1, extract = [Html.ParseTextNested, Provider._ExpressionLanguage])],
			extractReleaseUploader		= [HtmlResult(index = 7)],
			extractSourceTime			= [ProviderHtml.Details, HtmlDiv(recursive = False), HtmlFieldSet(class_ = Provider._AttributeDetails, index = 1, extract = [Html.ParseTextNested, Provider._ExpressionTime])],
			extractSourceSeeds			= [HtmlResult(index = 5)],
			extractSourceLeeches		= [HtmlResult(index = 6)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlParagraph(index = -1), HtmlLink(index = -1, extract = Html.ParseText)])
			if not last or not Regex.match(data = last, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processDetailsBefore(self, item):
		category = self.extractHtml(item, [HtmlDiv(recursive = False), HtmlFieldSet(class_ = Provider._AttributeDetails, index = 1, extract = [Html.ParseTextNested, Provider._ExpressionCategory])])
		if category:
			if self.parameterMediaMovie():
				if not Regex.match(data = category, expression = Provider._ExpressionMovie): return ProviderHtml.Skip
			else:
				if not Regex.match(data = category, expression = Provider._ExpressionShow): return ProviderHtml.Skip
