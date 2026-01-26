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

from lib.providers.core.tele import ProviderTele
from lib.providers.core.html import Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlSpan

class Provider(ProviderTele):

	_Link			= {
						ProviderTele.Version1 : ['https://cpasbien.to'],
						ProviderTele.Version2 : ['https://cpasbien.sh'],
					}

	_ExpressionHash	= r'window\.location\.href.*?[\'"\/]([a-f0-9]{40})[\'"]'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()
		if version == ProviderTele.Version1:
			offsetStart				= None # Has paging element in HTML, but it does not work.
			offsetIncrease			= None
			query					= ProviderTele.Path1
			extractOptimizeDetails	= HtmlDiv(id_ = ProviderTele.AttributeContainer4),
			extractLink				= [ProviderTele.Details, HtmlLink(href_ = ProviderTele.ExpressionMagnet, extract = Html.AttributeHref)]
			extractHash				= None
			extractFileSize			= [ProviderTele.Details, HtmlDiv(id_ = ProviderTele.AttributeDetails4), HtmlSpan(index = 0, recursive = False)]
		elif version == ProviderTele.Version2:
			query					= ProviderTele.Path3
			offsetStart				= True
			offsetIncrease			= True
			extractOptimizeDetails	= Html()
			extractLink				= None
			extractHash				= [ProviderTele.Details, Html(extract = Provider._ExpressionHash)]
			extractFileSize			= [HtmlResult(index = 0), HtmlDiv(class_ = ProviderTele.AttributeSize)]

		ProviderTele.initialize(self,
			name					= 'Cpasbien',
			description				= '{name} is well-known open {container} site from France. The site contains results in various languages, but most of them are in French. {name} has few {containers}, paging issues, and missing or inaccurate metadata. {name} requests subpages in order to extract the magnet link and other metadata, which substantially increases scraping time.',
			rank					= 2,
			performance				= ProviderTele.PerformanceBad,

			link					= Provider._Link[version],

			customVersion			= 2,

			offsetStart				= offsetStart,
			offsetIncrease			= offsetIncrease,

			searchQuery				= query,

			extractOptimizeData		= HtmlDiv(id_ = ProviderTele.AttributeContainer4), # To detect the last page in processOffset().
			extractOptimizeDetails	= extractOptimizeDetails,
			extractList				= [HtmlResults(class_ = ProviderTele.AttributeTable2)],
			extractDetails			= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeHref)],
			extractLink				= extractLink,
			extractHash				= extractHash,
			extractFileName			= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeTitle)],
			extractFileSize			= extractFileSize,
			extractSourceSeeds		= [HtmlResult(index = 0), HtmlDiv(class_ = ProviderTele.AttributeSeeds)],
			extractSourceLeeches	= [HtmlResult(index = 0), HtmlDiv(class_ = ProviderTele.AttributeLeeches)],
		)
