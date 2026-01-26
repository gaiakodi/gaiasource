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

from lib.providers.core.html import ProviderHtml, Html, HtmlDiv, HtmlLink
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://pirateiro.com', 'https://pirateiro.io']
	_Mirror					= ['https://torrends.to/site/pirateiro']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'pirateiro', ProviderHtml.UnblockFormat3 : 'pirateiro'}
	_Path					= 'search'

	_ParameterSearch		= 'query'
	_ParameterPage			= 'page'

	_AttributeContainer		= 'card-container'
	_AttributeDetails		= 'card-body'
	_AttributeBox			= 'list-group-item'		# Previous: card-link
	_AttributeCategory		= 'cat-span'
	_AttributeTitle			= 'pt-title'			# Previous: card-title
	_AttributeTime			= 'time-torrent'		# Previous: text-muted (main page)
	_AttributeSize			= 'single-size'			# Previous: size-badge (main page)
	_AttributeSeeds			= 'btn-seed-home'		# Previous: prog-green
	_AttributeLeeches		= 'btn-leech-home'		# Previous: prog-red
	_AttributePages			= 'pagi-container'
	_AttributePage			= 'pagi-link'
	_AttributeDisabled		= 'disabled'

	_ExpressionMovie		= r'(movie|anime)'
	_ExpressionShow			= r'(tv|anime)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'Pirateiro',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. The search page of {name} does not contain all the metadata. A subpage must therefore be retrieved for each result in order to extract the magnet link, which substantially increases scraping time. Subpages also load very slowly, further increasing scraping time.',
			rank						= 2, # Because of very very slow subpages.
			performance					= ProviderHtml.PerformanceBad,

			link						= Provider._Link,
			mirror						= Provider._Mirror,
			unblock						= Provider._Unblock,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			# Subpages take very long to load, sometimes 10+ seconds.
			# Maybe a temp problem, or Pirateiro does this to prevent scraping.
			# Set a fixed number of threads to use, in order to retrieve multiple subpages concurrently.
			searchConcurrency			= 6,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterSearch	: ProviderHtml.TermQuery,
												Provider._ParameterPage		: ProviderHtml.TermOffset,
											},
										},

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContainer),
			extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeDetails),
			extractList					= [HtmlLink(class_ = Provider._AttributeBox)],
			extractDetails				= [Html(extract = Html.AttributeHref)],
			extractLink					= [ProviderHtml.Details, HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [Html(class_ = Provider._AttributeTitle)],
			extractFileSize				= [ProviderHtml.Details, Html(class_ = Provider._AttributeSize)],
			extractSourceTimeInexact	= [ProviderHtml.Details, Html(class_ = Provider._AttributeTime)],
			extractSourceSeeds			= [Html(class_ = Provider._AttributeSeeds)],
			extractSourceLeeches		= [Html(class_ = Provider._AttributeLeeches)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(class_ = Provider._AttributePage, index = -1, extract = Html.AttributeClass)])
			if next and Provider._AttributeDisabled in next: return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		expression = Provider._ExpressionShow if self.parameterMediaShow() else Provider._ExpressionMovie
		category = self.extractHtml(item, [Html(class_ = Provider._AttributeCategory, extract = Html.ParseTextNested)])
		if not category or not Regex.match(data = category, expression = expression): return ProviderHtml.Skip
