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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlLink, HtmlDiv
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link						= ['https://subtorrents.in', 'https://subtorrents.nl', 'https://subtorrents.com', 'https://subtorrents.la', 'https://subtorrents.net', 'https://subtorrents.one', 'https://subtorrents.tv', 'https://subtorrents.club']

	_Path						= 'page/%s/'

	_ParameterQuery				= 's'

	_AttributeContent			= 'secciones'
	_AttributeTable				= 'searchResult'
	_AttributeDetails			= 'fichdatos'
	_AttributePages				= 'pagination'

	_ExpressionSize				= r'tamaño.*?>(.*?)(?:<\/li>)'
	_ExpressionTime				= r'fecha(?:\s*de\s*estreno)?.*?>(.*?)(?:<\/li>)'
	_ExpressionVideoQuality		= r'calidad.*?>(.*?)(?:<\/li>)'
	_ExpressionVideo3d			= r'3d.*?>(.*?)(?:<\/li>)'
	_ExpressionAudioCodec		= r'audio.*?>(.*?)\s*(?:<\/li>)'
	_ExpressionAudioLanguage	= r'>[\s,]*(idioma.*?)\s*<.*?(?:>[\s,]*(idioma.*?)\s*<)*'
	_ExpressionSubtitleType		= r'>([^<]*subtitulos.*?)\s*<'
	_ExpressionSubtitleLanguage	= r'subtitulos.*title\s*=\s*[\'"](?!trailer)(.*?)[\'"]'
	_ExpressionSubtitle			= r'(subtitulos)'
	_ExpressionLanguage			= r'(idioma\s*)'
	_ExpressionNext				= r'(»|&raquo;)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name							= 'SubTorrents',
			description						= '{name} is less-known open {container} site from Spain. The site contains results in various languages, but most of them are in Spanish. {name} has torrent files instead of magnet links, and has missing metadata, such as file size, hashes, and peer counts. {name} requests subpages in order to extract the magnet link, which substantially increases scraping time.',
			rank							= 2,
			performance						= ProviderHtml.PerformanceBad,

			link							= Provider._Link,

			offsetStart						= 1,
			offsetIncrease					= 1,

			formatEncode					= ProviderHtml.FormatEncodePlus,

			queryYear						= False, # Does not support searching by year.
			queryEpisode					= ProviderHtml.TermTitleShow, # Cannot search by number.

			searchQuery						= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path % ProviderHtml.TermOffset,
												ProviderHtml.RequestData : {
													Provider._ParameterQuery : ProviderHtml.TermQuery,
												},
											},

			extractOptimizeData				= HtmlDiv(class_ = Provider._AttributeContent), # To detect the last page in processOffset().
			extractOptimizeDetails			= HtmlDiv(class_ = Provider._AttributeContent),
			extractList						= [HtmlResults(class_ = Provider._AttributeTable)],
			extractDetails					= [HtmlLink(extract = Html.AttributeHref)],
			extractFileExtra				= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, extract = Html.ParseCode)],
			extractFileSize					= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, extract = [Html.ParseCode, Provider._ExpressionSize])],
			extractSourceTime				= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, extract = [Html.ParseCode, Provider._ExpressionTime])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(index = -1, extract = Html.ParseText)])
			if not last or not Regex.match(data = last, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		try:
			# Validate to only retrieve sub-pages that are valid.
			name = self.extractHtml(item, [HtmlLink(extract = Html.ParseText)])
			if not self.searchValid(data = name, validateShow = False): return ProviderHtml.Skip
		except: self.logError()

	def processLink(self, value, item, details = None, entry = None):
		if details:
			links = self.extractHtml(details, [HtmlLink(href_ = ProviderHtml.ExpressionTorrent)])
			if links:
				if self.parameterMediaMovie():
					value = links[0][Html.AttributeHref]
				else:
					result = []
					try:
						number = '%dx%02d' % (self.parameterNumberSeason(), self.parameterNumberEpisode())
						for link in links:
							name = link[Html.AttributeTitle]
							if number in name: result.append((name, link[Html.AttributeHref])) # Do quick efficient number check.
					except: pass
					if not result: result = [(link[Html.AttributeTitle], link[Html.AttributeHref]) for link in links] # If nothing was found, try all.

					for link in result:
						if self.searchValid(data = link[0], validateTitle = False): # Do not validate the title, if abbreviation is used (eg: GOT).
							value = link[1]
							self.mExtra = link[0]
							break

		return value

	def processFileExtra(self, value, item, details = None, entry = None):
		if value:
			result = []

			try: result.append(self.extractHtmlDecode(self.mExtra))
			except: pass

			result.append(self.extractHtmlDecode(Regex.extract(data = value, expression = Provider._ExpressionVideoQuality)))
			result.append(self.extractHtmlDecode(Regex.extract(data = value, expression = Provider._ExpressionVideo3d)))

			result.append(self.extractHtmlDecode(Regex.extract(data = value, expression = Provider._ExpressionAudioCodec)))
			language = Regex.extract(data = value, expression = Provider._ExpressionAudioLanguage, group = None, all = True)
			if language:
				language = self.extractHtmlDecode(language)
				language = [Regex.remove(data = i, expression = Provider._ExpressionLanguage, all = True) for i in language]
				language.insert(0, 'Audio')
				result.append(language)

			subtitles = Regex.extract(data = value, expression = Provider._ExpressionSubtitleType)
			if subtitles:
				subtitles = self.extractHtmlDecode(subtitles)
				subtitles = Regex.remove(data = subtitles, expression = Provider._ExpressionSubtitle, all = True)
			language = Regex.extract(data = value, expression = Provider._ExpressionSubtitleLanguage, group = None, all = True)
			if language:
				language = self.extractHtmlDecode(language)
				language = [Regex.remove(data = i, expression = Provider._ExpressionLanguage, all = True) for i in language]
				if subtitles: language.insert(0, subtitles)
				language.insert(0, 'Subtitulos')
				result.append(language)
			elif subtitles:
				result.append('Subtitulos ' + subtitles)

			value = [i for i in result if i]

		return value
