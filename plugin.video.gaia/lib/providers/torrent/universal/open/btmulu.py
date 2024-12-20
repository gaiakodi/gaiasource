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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlArticle, HtmlHeading4, HtmlParagraph, HtmlListUnordered, HtmlListItem

class Provider(ProviderHtml):

	#_Link				= ['https://btmulu.com', 'https://btmulu9.club']
	_Link				= ['https://btmulu.work', 'https://btmulu.live', 'https://btmulu.click', 'https://btmulu.com']
	_Path				= 'search/%s/page-%s.html'

	_AttributeList		= 'list-view'
	_AttributeItem		= 'item'
	_AttributePages		= 'pagination'
	_AttributeDisabled	= 'disabled'

	_ExpressionLink		= 'hash/(%s).html' % ProviderHtml.ExpressionSha
	_ExpressionSize		= 'size\s*[:：]\s*(\d+(?:\.\d+)?\s*[kmgt]?b)(?:$|\s|&nbsp;)'
	_ExpressionTime		= 'created\s*[:：]\s*(\d+-\d+-\d+(?:\s\d+:\d+:\d+)?)(?:$|\s|&nbsp;)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'BtMulu',
			description				= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has a lot of missing trivial metadata and contains a number of fake uploads. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.',
			rank					= 2,
			performance				= ProviderHtml.PerformanceMedium - ProviderHtml.PerformanceStep,
			status					= ProviderHtml.StatusImpaired, # Cloudflare. Update (2024-12): Probably not using Cloudflare anymore. But leave this, since the results are not that good and domains change often.

			link					= Provider._Link,

			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			offsetStart				= 1,
			offsetIncrease			= 1,

			formatEncode			= ProviderHtml.FormatEncodePlus,

			searchQuery				= {
										ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
										ProviderHtml.RequestPath : Provider._Path % (ProviderHtml.TermQuery, ProviderHtml.TermOffset),
									},

			extractOptimizeData		= HtmlDiv(class_ = Provider._AttributeList),
			extractList				= HtmlArticle(class_ = Provider._AttributeItem),
			extractHash				= [HtmlLink(href_ = Provider._ExpressionLink, extract = Provider._ExpressionLink)],
			extractFileName			= [HtmlLink(href_ = Provider._ExpressionLink), HtmlHeading4(extract = Html.ParseTextUnnested)],
			extractFileSize			= [HtmlParagraph(extract = [Html.ParseTextUnnested, Provider._ExpressionSize])],
			extractSourceTime		= [HtmlParagraph(extract = [Html.ParseTextUnnested, Provider._ExpressionTime])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlListItem(index = -1, extract = Html.AttributeClass)])
			if last and Provider._AttributeDisabled in last: return ProviderHtml.Skip
		except: self.logError()

	def processHash(self, value, item, details = None, entry = None):
		# Top entries are "fake" redirects.
		return value if value else ProviderHtml.Skip

	def processFileName(self, value, item, details = None, entry = None):
		# Contains spaces at start of string.
		return value.strip() if value else None
