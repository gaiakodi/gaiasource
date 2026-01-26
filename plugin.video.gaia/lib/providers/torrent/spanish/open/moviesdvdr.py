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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link						= ['https://moviesdvdr.co', 'https://moviesdvdr.com']

	_Path						= 'page/%s/'

	_ParameterQuery				= 's'

	_AttributeContainer			= 'container'
	_AttributeContent			= 'content'
	_AttributeList				= 'listagem'
	_AttributeItem				= 'item'
	_AttributeName				= 'titulo'
	_AttributePages				= 'wp-pagenavi'
	_AttributeNext				= 'nextpostslink'

	_ExpressionSize				= r'tamaño\s*:*\s*(.*)'
	_ExpressionTime				= r'fecha\s*:*\s*(.*)'
	_ExpressionFormat			= r'formato\s*:*\s*(.*)'
	_ExpressionAudioLanguage	= r'idiomas\s*:*\s*(.*)'
	_ExpressionSubtitleLanguage	= r'subtitulos\s*:*\s*(.*)'
	_ExpressionSubtitle			= r'(subtitulos)'
	_ExpressionLanguage			= r'(idioma\s*)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name							= 'MoviesDVDR',
			description						= '{name} is less-known open {container} site from Spain. The site contains results in various languages, but most of them are in Spanish. {name} has torrent files instead of magnet links, and has missing metadata, such as hashes and peer counts. {name} requests subpages in order to extract the magnet link, which substantially increases scraping time.',
			rank							= 2,
			performance						= ProviderHtml.PerformanceBad,

			link							= Provider._Link,

			supportShow						= False,
			supportSpecial					= False,
			supportPack						= False,
			supportPackMovie				= False,
			supportPackShow					= False,
			supportPackSeason				= False,

			streamTime						= '%m/%d/%Y', # Month first.

			offsetStart						= 1,
			offsetIncrease					= 1,

			formatEncode					= ProviderHtml.FormatEncodePlus,

			queryYear						= False, # Does not support searching by year.

			searchQuery						= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path % ProviderHtml.TermOffset,
												ProviderHtml.RequestData : {
													Provider._ParameterQuery : ProviderHtml.TermQuery,
												},
											},

			extractOptimizeData				= HtmlDiv(class_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			extractOptimizeDetails			= HtmlDiv(class_ = Provider._AttributeContent),
			extractList						= [HtmlDiv(class_ = Provider._AttributeList), HtmlDiv(class_ = Provider._AttributeItem)],
			extractDetails					= [HtmlLink(extract = Html.AttributeHref)],
			extractLink						= [ProviderHtml.Details, HtmlLink(href_ = ProviderHtml.ExpressionTorrent, extract = Html.AttributeHref)],
			extractFileName					= [HtmlLink(), HtmlDiv(class_ = Provider._AttributeName)],
			extractFileExtra				= [ProviderHtml.Details, Html(extract = Html.ParseTextNested)],
			extractFileSize					= [ProviderHtml.Details, Html(extract = [Html.ParseTextNested, Provider._ExpressionSize])],
			extractSourceTime				= [ProviderHtml.Details, Html(extract = [Html.ParseTextNested, Provider._ExpressionTime])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(class_ = Provider._AttributeNext)])
			if not next: return ProviderHtml.Skip
		except: self.logError()

	def processFileExtra(self, value, item, details = None, entry = None):
		if value:
			result = []

			result.append(self.extractHtmlDecode(Regex.extract(data = value, expression = Provider._ExpressionFormat)))

			language = Regex.extract(data = value, expression = Provider._ExpressionAudioLanguage, group = None, all = True)
			if language:
				language = self.extractHtmlDecode(language)
				language = [Regex.remove(data = i, expression = Provider._ExpressionLanguage, all = True) for i in language]
				language.insert(0, 'Audio')
				result.append(language)

			language = Regex.extract(data = value, expression = Provider._ExpressionSubtitleLanguage, group = None, all = True)
			if language:
				language = self.extractHtmlDecode(language)
				language = [Regex.remove(data = i, expression = Provider._ExpressionLanguage, all = True) for i in language]
				language.insert(0, 'Subtitulos')
				result.append(language)

			value = [i for i in result if i]

		return value
