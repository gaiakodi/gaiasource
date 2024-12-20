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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlSpan, HtmlItalic
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link				= {
							ProviderHtml.Version1 : ['https://kickasst.net', 'https://thekat.app', 'https://kickasstorrents.bz', 'https://kkickass.com', 'https://kkat.net', 'https://thekat.cc'],
							ProviderHtml.Version2 : ['https://kickasstorrents.to', 'https://katcr.to', 'http://kickass.to', 'https://kickass.sx', 'https://kat.am'],
						}
	_Mirror				= {
							ProviderHtml.Version1 : ['https://kickass.how'],
							ProviderHtml.Version2 : ['https://thekickasstorrents.to'],
						}
	_Unblock			= {
							ProviderHtml.Version1 : None,
							ProviderHtml.Version2 : {ProviderHtml.UnblockFormat1 : 'kickasstorrents', ProviderHtml.UnblockFormat2 : 'kat', ProviderHtml.UnblockFormat3 : 'kickass2', ProviderHtml.UnblockFormat4 : 'kickass'},
						}
	_Path				= {
							ProviderHtml.Version1 : 'usearch/%s%%20category:%s/%s/?field=seeders&sorder=desc',
							ProviderHtml.Version2 : 'search/%s/category/%s/%s/?sortby=seeders&sort=desc',
						}

	_CategoryMovie		= 'movies'
	_CategoryShow		= 'tv'

	_AttributeMain		= 'mainpart'
	_AttributeData		= 'data'
	_AttributeName		= 'cellMainLink'
	_AttributeInfo		= 'markeredBlock'
	_AttributeVerified	= 'ka-verify'
	_AttributeButtons	= 'buttonsline'
	_AttributePages		= 'pages'
	_AttributePage		= 'siteButton'
	_AttributeActive	= 'active'

	_ExpressionMagnet	= '(.*magnet.*)'
	_ExpressionUploader	= 'posted\s*by\s*(.*?)\s*in\s*'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()
		if version == ProviderHtml.Version1:
			extractDetails				= None
			extractLink					= [HtmlResult(index = 0), HtmlLink(title_ = Provider._ExpressionMagnet, extract = [Html.AttributeHref, ProviderHtml.ExpressionMagnet, Html.ParseDecode])]
			extractReleaseUploader		= [HtmlResult(index = 0), HtmlDiv(class_ = Provider._AttributeInfo, extract = [Html.ParseTextUnnested, Provider._ExpressionUploader])]
			extractSourceTimeInexact	= [HtmlResult(index = 2)]
			# At the bottom of the list there are typically torrents with N/A seeds/leeches.
			# When opening the details page of those torrents, the correct seeds/leeches is shown. For some reason that are not displayed correctly in the main table.
			# Exclude those results in processSourceSeeds().
			extractSourceSeeds			= [HtmlResult(index = 3)]
			extractSourceLeeches		= [HtmlResult(index = 4)]
		elif version == ProviderHtml.Version2:
			extractDetails				= [HtmlResult(index = 0), HtmlLink(class_ = Provider._AttributeName, extract = Html.AttributeHref)]
			extractLink					= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeMain), HtmlDiv(class_ = Provider._AttributeButtons), HtmlLink(href = ProviderHtml.ExpressionMagnet, extract = [Html.AttributeHref])]
			extractReleaseUploader		= [HtmlResult(index = 0), HtmlDiv(class_ = Provider._AttributeInfo), HtmlSpan(extract = [Html.ParseTextUnnested, Provider._ExpressionUploader])]
			extractSourceTimeInexact	= [HtmlResult(index = 3)]
			extractSourceSeeds			= [HtmlResult(index = 4)]
			extractSourceLeeches		= [HtmlResult(index = 5)]

		ProviderHtml.initialize(self,
			name						= 'KickassTorrents',
			description					= '{name} is one of the oldest and most well-known {container} sites. The site contains results in various languages, but most of them are in English. There are different versions of {name} on different mirror sites which are incompatible with each other. Version %s contains magnet links on the main page and is therefore faster to scrape, but has numerous bugs that can return incomplete metadata or restrict paging, sorting, and categorization. Version %s requires requests to subpages to extract the magnet link and is therefore substantially slower to scrape.' % (ProviderHtml.Version1, ProviderHtml.Version2),
			rank						= 4,
			performance					= ProviderHtml.PerformanceBad,

			link						= Provider._Link[version],
			mirror						= Provider._Mirror[version],
			unblock						= Provider._Unblock[version],

			customVersion				= 2,
			customVerified				= True,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodeQuote,

			# Some results, especially older stuff, are miscategorized as "other" instead of "movies" or "tv".
			# However, when removing the category from the search (or searching both movies/tv and other) returns fewer results for some reason.
			# For now, ignore all the miscategorized results.
			searchQuery					= Provider._Path[version] % (ProviderHtml.TermQuery, ProviderHtml.TermCategory, ProviderHtml.TermOffset),
			searchCategoryMovie			= Provider._CategoryMovie,
			searchCategoryShow			= Provider._CategoryShow,

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeMain), # To detect the last page in processOffset().
			extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeMain),
			extractDetails				= extractDetails,
			extractList					= [HtmlResults(class_ = Provider._AttributeData)],
			extractLink					= extractLink,
			extractFileName				= [HtmlResult(index = 0), HtmlLink(class_ = Provider._AttributeName)],
			extractFileSize				= [HtmlResult(index = 1)],
			extractReleaseUploader		= extractReleaseUploader,
			extractSourceApproval		= [HtmlResult(index = 0), HtmlItalic(class_ = Provider._AttributeVerified, extract = Html.AttributeClass)],
			extractSourceTimeInexact	= extractSourceTimeInexact,
			extractSourceSeeds			= extractSourceSeeds,
			extractSourceLeeches		= extractSourceLeeches,
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			pages = self.extractHtml(data, [Html(class_ = Provider._AttributePages), Html(class_ = Provider._AttributePage)])
			next = False
			current = 0
			for page in pages:
				if Provider._AttributeActive in page[Html.AttributeClass]:
					current = int(page.text)
				elif current and int(page.text) > current:
					next = True
					break
			if not next: return ProviderHtml.Skip
		except: self.logError()

	def processSourceSeeds(self, value, item, details = None, entry = None):
		try: return int(value)
		except: return ProviderHtml.Skip

	def processSourceApproval(self, value, item, details = None, entry = None):
		if self.customVerified() and not value: return ProviderHtml.Skip
		if value: return ProviderHtml.ApprovalExcellent
		else: return ProviderHtml.ApprovalDefault
