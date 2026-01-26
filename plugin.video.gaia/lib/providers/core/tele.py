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

# The open French site all share a similar structure.
# There is no official name for the layout, so we call it Tele(charger).

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlListUnordered, HtmlListItem
from lib.modules.tools import Regex

class ProviderTele(ProviderHtml):

	# Tele matches EACH keyword instead of ALL keywords.
	# For instance, "title year" will return all names that contain either "title" or "year".
	# Therefore do not sort by seeds, instead by default/relevance, which puts names with most keyword matches at top.
	Path1				= 'search_torrent/%s/%s'
	Path2				= 'search_torrent/%s/%s/page-%s'
	Path3				= 'recherche/%s/%s'
	Path4				= 'recherche/%s/%s/page/%s'

	LimitOffset			= 50

	CategoryMovie		= 'films'
	CategoryShow		= 'series'

	AttributeContainer1	= 'listing-torrent'
	AttributeContainer2	= 'content-left-col'
	AttributeContainer3	= 'content-table'
	AttributeContainer4	= 'gauche'
	AttributeTable1		= 'table'
	AttributeTable2		= 'table-corps'
	AttributeDetails1	= 'listing-detail'
	AttributeDetails2	= 'movie-detail'
	AttributeDetails3	= 'content-table'
	AttributeDetails4	= 'infosficher'
	AttributeSize		= 'poid'
	AttributeSeeds		= 'up'
	AttributeLeeches	= 'down'
	AttributePages		= 'pagination'

	ExpressionTime		= r'((?:\d{1,2}[\/\-]){2}\d{4})'
	ExpressionNext		= r'(next|suivant|→|►)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		performance				= ProviderHtml.PerformanceBad,

		offsetStart				= True,
		offsetIncrease			= True,

		formatEncode			= ProviderHtml.FormatEncodeQuote,

		searchQuery				= None,

		extractOptimizeData		= True,
		extractOptimizeDetails	= True,
		extractList				= True,
		extractDetails			= True,
		extractLink				= True,
		extractFileName			= True,
		extractFileSize			= True,
		extractSourceTime		= True,
		extractSourceSeeds		= True,
		extractSourceLeeches	= True,

		**kwargs
	):
		if searchQuery == ProviderTele.Path1: searchQuery = searchQuery % (ProviderHtml.TermCategory, ProviderHtml.TermQuery)
		elif searchQuery == ProviderTele.Path2: searchQuery = searchQuery % (ProviderHtml.TermCategory, ProviderHtml.TermQuery, ProviderHtml.TermOffset)
		elif searchQuery == ProviderTele.Path3: searchQuery = searchQuery % (ProviderHtml.TermQuery, ProviderHtml.TermOffset)
		elif searchQuery == ProviderTele.Path4: searchQuery = searchQuery % (ProviderHtml.TermCategory, ProviderHtml.TermQuery, ProviderHtml.TermOffset)

		ProviderHtml.initialize(self,
			performance				= performance,
			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1 if offsetStart is True else offsetStart,
			offsetIncrease			= ProviderTele.LimitOffset if offsetIncrease is True else offsetIncrease,

			formatEncode			= formatEncode,

			searchQuery				= searchQuery,
			searchCategoryMovie		= ProviderTele.CategoryMovie,
			searchCategoryShow		= ProviderTele.CategoryShow,

			extractOptimizeData		= HtmlDiv(class_ = ProviderTele.AttributeContainer1) if extractOptimizeData is True else extractOptimizeData, # To detect the last page in processOffset().
			extractOptimizeDetails	= HtmlDiv(class_ = ProviderTele.AttributeDetails1) if extractOptimizeDetails is True else extractOptimizeDetails,
			extractList				= [HtmlResults(class_ = ProviderTele.AttributeTable1)] if extractList is True else extractList,
			extractDetails			= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeHref)] if extractDetails is True else extractDetails,
			extractLink				= [ProviderHtml.Details, HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)] if extractLink is True else extractLink,
			extractFileName			= [HtmlResult(index = 0), HtmlLink()] if extractFileName is True else extractFileName,
			extractFileSize			= [HtmlResult(index = 1)] if extractFileSize is True else extractFileSize,
			extractSourceTime		= [ProviderHtml.Details, Html(extract = ProviderTele.ExpressionTime)],
			extractSourceSeeds		= [HtmlResult(index = 2)] if extractSourceSeeds is True else extractSourceSeeds,
			extractSourceLeeches	= [HtmlResult(index = 3)] if extractSourceLeeches is True else extractSourceLeeches,

			**kwargs
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = False
			pages = self.extractHtml(data, [HtmlListUnordered(class_ = ProviderTele.AttributePages), HtmlListItem()])
			if pages:
				for page in pages:
					if Regex.match(data = page.text, expression = ProviderTele.ExpressionNext):
						next = True
						break
			if not next: return ProviderHtml.Skip
		except: self.logError()
