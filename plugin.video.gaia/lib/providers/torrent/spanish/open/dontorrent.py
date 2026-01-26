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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlSpan, HtmlParagraph, HtmlListUnordered
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://dontorrent.rip', 'https://dontorrents.com', 'https://dontorrent.com', 'https://dontorrent.org', 'https://dontorrent.io', 'https://dontorrent.la', 'https://dontorrent.to']
	_Mirror					= ['https://torrends.to/proxy/dontorrent']

	_Path					= 'buscar/%s/page/%s'

	_AttributeContainer		= 'buscador'
	_AttributeContent		= 'card-body'
	_AttributeCategory		= 'badge'
	_AttributeHeader		= 'lead'
	_AttributeTable			= 'table'
	_AttributePages			= 'pagination'
	_AttributePage			= 'page-link'

	_ExpressionName			= r'.*\/(.*?)\.torrent'
	_ExpressionSize			= r'tamaño\s*:\s*(.*)'
	_ExpressionMovie		= r'(pel[ií]cula|documental(?:es)?|variado)'
	_ExpressionShow			= r'(series?|episodios?|documental(?:es)?|variado)'
	_ExpressionBrackets		= r'^\(?(.*?)\)?$'
	_ExpressionStrip		= r'^[\s\.\-]*(.*?)[\s\.\-]*$'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name							= 'DonTorrent',
			description						= '{name} is less-known open {container} site from Spain. The site contains results in various languages, but most of them are in Spanish. {name} has torrent files instead of magnet links, and has missing metadata, such as file size, hashes, and peer counts. {name} requests subpages in order to extract the magnet link, which substantially increases scraping time.',
			rank							= 2,
			performance						= ProviderHtml.PerformanceBad,

			link							= Provider._Link,
			mirror							= Provider._Mirror,

			supportSpecial					= False, # Has episodes, but they are not directly searchable.
			supportPack						= False, # Has season packs, but they are not directly searchable.

			offsetStart						= 1,
			offsetIncrease					= 1,

			formatEncode					= ProviderHtml.FormatEncodeQuote,

			queryYear						= False, # Does not support searching by year.
			queryEpisode					= ProviderHtml.TermTitleShow, # Does not support individual episode searches.

			searchQuery						= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path % (ProviderHtml.TermQuery, ProviderHtml.TermOffset),
												ProviderHtml.RequestHeaders : {
													Provider.RequestHeaderReferer : ProviderHtml.TermLinkHost, # Must add a referer, otherwise it shows an error: "Necesitas utilizar el buscador".
												},
											},

			extractOptimizeData				= HtmlDiv(id_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			extractOptimizeDetails			= HtmlDiv(class_ = Provider._AttributeContent),
			extractList						= [HtmlDiv(class_ = Provider._AttributeContent), HtmlParagraph(recursive = False)],
			extractDetails					= [HtmlLink(extract = Html.AttributeHref)],
			extractEntries					= [HtmlResults(class_ = Provider._AttributeTable)],
			extractFileSize					= [ProviderHtml.Details, Html(extract = [Html.ParseTextNested, Provider._ExpressionSize])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlLink(class_ = Provider._AttributePage, index = -1, extract = Html.AttributeHref)])
			if not last or last == '#': return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		try:
			category = self.extractHtml(item, [HtmlSpan(class_ = Provider._AttributeCategory, extract = Html.ParseText)])
			expression = Provider._ExpressionShow if self.parameterMediaShow() else Provider._ExpressionMovie
			if category and not Regex.match(data = category, expression = expression): return ProviderHtml.Skip

			# Validate to only retrieve sub-pages that are valid.
			name = self.extractHtml(item, [HtmlLink(extract = Html.ParseText)])
			if not self.searchValid(data = name): return ProviderHtml.Skip

			classes = self.extractHtml(item, [Html(extract = Html.AttributeClass)])
			if classes and Provider._AttributeHeader in classes: return ProviderHtml.Skip # Header rows.
		except: self.logError()

	def processLink(self, value, item, details = None, entry = None):
		if details or entry:
			if self.parameterMediaMovie(): entry = details
			value = self.extractHtml(entry, [HtmlLink(href_ = ProviderHtml.ExpressionTorrent, extract = Html.AttributeHref)])
		return value

	def processFileName(self, value, item, details = None, entry = None):
		if details or entry:
			link = self.processLink(value = value, item = item, details = details, entry = entry)
			if link: return Regex.extract(data = link, expression = Provider._ExpressionName)
		return value

	def processFileExtra(self, value, item, details = None, entry = None):
		result = []
		if entry and self.parameterMediaShow():
			result.append(self.extractHtml(entry, [HtmlResult(index = 0, extract = [Html.ParseText, Provider._ExpressionStrip])]))
		if item and (self.parameterMediaMovie() or (self.parameterMediaShow() and entry)):
			result.append(self.extractHtml(item, [HtmlLink(extract = [Html.ParseText, Provider._ExpressionStrip])]))
			extras = self.extractHtml(item, [HtmlSpan(recursive = False), HtmlSpan(recursive = False)])
			if extras:
				for extra in extras:
					try: classes = extra[Html.AttributeClass]
					except: classes = None
					if not classes: result.append(Regex.extract(data = extra.text, expression = Provider._ExpressionBrackets))
				value = [i for i in result if i]
		return value
