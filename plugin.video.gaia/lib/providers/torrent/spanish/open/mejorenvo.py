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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlTable, HtmlTableRow, HtmlLink
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://mejorenvo1.com', 'https://mejorenvo.com', 'https://mejorenvo.me', 'https://mejorenvo.net', 'https://mejorenvo.tv', 'https://mejorenvo.info']

	_Path					= 'secciones.php'

	_ParameterQuery			= 'q'
	_ParameterSection		= 'sec'
	_ParameterSearch		= 'buscador'

	_ExpressionMovie		= r'(pel[ií]cula)'
	_ExpressionShow			= r'(series?)'
	_ExpressionTime			= r'fecha\s*:*\s*(.*)'
	_ExpressionFormat		= r'formato\s*:*\s*(.*)'
	_ExpressionEntry		= r'(a\d+)'
	_ExpressionTorrent		= r'(torrent=1)'
	_ExpressionSeason		= r'(temporada)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name							= 'MejorenVO',
			description						= '{name} is less-known open {container} site from Spain. The site contains results in various languages, but most of them are in Spanish. {name} has torrent files instead of magnet links, and has missing metadata, such as file size, hashes, and peer counts. {name} requests subpages and sub-subpages in order to extract the magnet link, which substantially increases scraping time.',
			rank							= 2,
			performance						= ProviderHtml.PerformanceBad,
			status							= ProviderHtml.StatusDead, # Website does not exist anymore.

			link							= Provider._Link,

			supportSpecial					= False, # Has episodes, but they are not directly searchable.
			supportPack						= False, # Has season packs, but they are not directly searchable.

			formatEncode					= ProviderHtml.FormatEncodePlus,

			queryYear						= False, # Does not support searching by year.
			queryEpisode					= ProviderHtml.TermTitleShow, # Does not support the default SxxEyy format.

			searchQuery						= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path,
												ProviderHtml.RequestData : {
													Provider._ParameterQuery : ProviderHtml.TermQuery,
													Provider._ParameterSection : Provider._ParameterSearch,
												},
											},
			searchConcurrency				= True,

			extractOptimizeData				= HtmlTable(),
			extractOptimizeDetails			= HtmlTable(index = 6),
			extractOptimizeEntries			= HtmlTable(index = 6),
			extractList						= [HtmlResults(index = 7)],
			extractDetails					= [HtmlLink(extract = Html.AttributeHref)],
			extractEntries					= [HtmlTableRow(id_ = Provider._ExpressionEntry)],
		)

	##############################################################################
	# EXTRACT
	##############################################################################

	def extractLink(self, item, details = None, entry = None):
		value = details if self.parameterMediaMovie() else entry
		if value: return self.extractHtml(value, [HtmlLink(href_ = ProviderHtml.ExpressionTorrent, extract = Html.AttributeHref)])
		else: return None

	def extractFileExtra(self, item, details = None, entry = None):
		value = details if self.parameterMediaMovie() else entry
		if value: return self.extractHtml(value, [Html(extract = Html.ParseTextNested)])
		else: return None

	def extractSourceTime(self, item, details = None, entry = None):
		value = details if self.parameterMediaMovie() else entry
		if value: return self.extractHtml(value, [Html(extract = [Html.ParseTextNested, Provider._ExpressionTime])])
		else: return None

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		try:
			category = self.extractHtml(item, [HtmlResult(index = 1, extract = Html.ParseText)])
			expression = Provider._ExpressionShow if self.parameterMediaShow() else Provider._ExpressionMovie
			if category and not Regex.match(data = category, expression = expression): return ProviderHtml.Skip

			# Validate to only retrieve sub-pages that are valid.
			name = self.extractHtml(item, [HtmlLink(extract = Html.ParseTextNested)])
			if not name: return ProviderHtml.Skip
			season = Regex.match(data = name, expression = Provider._ExpressionSeason) # Some miniseries or series with only one seasaon do not have a season.
			if not self.searchValid(data = name, validateShow = season): return ProviderHtml.Skip
		except: self.logError()

	def processEntry(self, item):
		try:
			# Some do not have torrent links, only eMule links.
			torrent = self.extractHtml(item, [HtmlLink(href_ = Provider._ExpressionTorrent)])
			if not torrent: return ProviderHtml.Skip

			link = self.extractHtml(item, [HtmlLink(index = 0)])

			# Validate to only retrieve sub-pages that are valid.
			name = link.text
			if not name or not self.searchValid(data = name, validateTitle = False): return ProviderHtml.Skip

			data = self.searchRequest(path = link[Html.AttributeHref])
			if data: item = self.extractData(data = data)
			else: item = None
		except: self.logError()
		return item

	def processFileExtra(self, value, item, details = None, entry = None):
		if self.parameterMediaMovie() or (self.parameterMediaShow() and entry):
			if value:
				result = []
				result.append(self.extractHtmlDecode(Regex.extract(data = value, expression = Provider._ExpressionFormat)))
				value = [i for i in result if i]
		return value
