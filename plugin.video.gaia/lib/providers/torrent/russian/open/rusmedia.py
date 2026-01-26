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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlTable, HtmlLink, HtmlDiv, HtmlParagraph, HtmlFont

class Provider(ProviderHtml):

	_Link					= ['http://rus-media.org']
	_Path					= 'search.php'

	_LimitOffset			= 50

	_ParameterQuery			= 'keywords'
	_ParameterPage			= 'start'
	_ParameterSearch		= 'tracker_search'
	_ParameterTorrent		= 'torrent'
	_ParameterShow			= 'sr'
	_ParameterTopics		= 'topics'
	_ParameterMatch			= 'sf'
	_ParameterTitle			= 'titleonly'
	_ParameterSort			= 'sk'
	_ParameterSeeds			= 'ts'
	_ParameterOrder			= 'sd'
	_ParameterDescending	= 'd'
	_ParameterTime			= 'st'
	_ParameterMagnet		= 'magnet'
	_ParameterYes			= '1'
	_ParameterNo			= '0'

	_AttributeContainer		= 'wrapcentre'
	_AttributeTable			= 'tablebg'
	_AttributeSeeds			= 'seed'
	_AttributeLeeches		= 'leech'
	_AttributePages			= 'nav'

	_ExpressionVerified		= r'(√)'
	_ExpressionNext			= r'(След)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'RusMedia',
			description				= '{name} is less-known open {container} site from Russia. The site contains results in various languages, but most of them are in Russian. {name} requests subpages in order to extract the magnet link, which substantially increases scraping time.',
			rank					= 3,
			performance				= ProviderHtml.PerformanceBad,

			link					= Provider._Link,

			customVerified			= True,

			offsetStart				= 0,
			offsetIncrease			= Provider._LimitOffset,

			formatEncode			= ProviderHtml.FormatEncodePlus,

			searchQuery				= {
										ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
										ProviderHtml.RequestPath : Provider._Path,
										ProviderHtml.RequestData : {
											Provider._ParameterQuery	: ProviderHtml.TermQuery,
											Provider._ParameterPage		: ProviderHtml.TermOffset,
											Provider._ParameterSearch	: Provider._ParameterTorrent,
											Provider._ParameterShow		: Provider._ParameterTopics,
											Provider._ParameterMatch	: Provider._ParameterTitle,
											Provider._ParameterSort		: Provider._ParameterSeeds,
											Provider._ParameterOrder	: Provider._ParameterDescending,
											Provider._ParameterTime		: Provider._ParameterNo,
										},
									},

			extractOptimizeData		= HtmlDiv(id_ = Provider._AttributeContainer),
			extractList				= [HtmlResults(class_ = Provider._AttributeTable, start = 2)],
			extractDetails			= [HtmlResult(index = 1), HtmlLink(extract = Html.AttributeHref)],
			extractLink				= [ProviderHtml.Details, HtmlTable(class_ = Provider._AttributeTable), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName			= [HtmlResult(index = 1), HtmlLink()],
			extractFileSize			= [HtmlResult(index = 4)],
			extractSourceTime		= [HtmlResult(index = 5), HtmlParagraph(index = 0)],
			extractSourceSeeds		= [HtmlResult(index = 3), HtmlDiv(class_ = Provider._AttributeSeeds)],
			extractSourceLeeches	= [HtmlResult(index = 3), HtmlDiv(class_ = Provider._AttributeLeeches)],
			extractReleaseUploader	= [HtmlResult(index = 2), HtmlLink()],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(index = -1, extract = [Html.ParseText, Provider._ExpressionNext])])
			if not next: return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		if self.customVerified():
			verified = self.extractHtml(item, [HtmlResult(index = 1), HtmlFont(extract = [Html.ParseText, Provider._ExpressionVerified])])
			if not verified: return ProviderHtml.Skip

	def processDetails(self, value, item):
		return ('%s&%s=%s' % (value.lstrip('.').lstrip('/'), Provider._ParameterMagnet, Provider._ParameterYes)) if value else value
