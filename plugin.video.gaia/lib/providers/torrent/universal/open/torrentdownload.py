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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlSpan, HtmlImage
from lib.modules.tools import Regex, Time

class Provider(ProviderHtml):

	_Link					= ['https://torrentdownload.info', 'https://torrentdownload.ch']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'torrentdownload', ProviderHtml.UnblockFormat3 : 'torrentdownload', ProviderHtml.UnblockFormat4 : 'torrentdownload'}
	_Path					= 'search'

	_ParameterQuery			= 'q'
	_ParameterOffset		= 'p'

	_AttributeContainer		= 'wrapper'
	_AttributeTable			= 'table2'
	_AttributeDetails		= 'smallish'
	_AttributePages			= 'search_stat'
	_AttributeNext			= 'next'

	_ExpressionHash			= '\/?(.*?)\/'
	_ExpressionVerified		= '(verified)'
	_ExpressionMovie		= '(movie)'
	_ExpressionShow			= '(tv)'

	_ExpressionRightNow		= '(right\s*now)'
	_ExpressionYesterday	= '(yesterday)'
	_ExpressionLastMonth	= '(last\s*month)'
	_ExpressionYears		= '(year\s*\+)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'TorrentDownload',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has some inaccurate metadata.',

			rank						= 4,
			performance					= ProviderHtml.PerformanceGood,

			link						= Provider._Link,
			unblock						= Provider._Unblock,

			customVerified				= True,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodeQuote,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterQuery	: ProviderHtml.TermQuery,
												Provider._ParameterOffset	: ProviderHtml.TermOffset,
											},
										},

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			extractList					= [HtmlResults(class_ = Provider._AttributeTable, index = -1, start = 1)],
			extractHash					= [HtmlResult(index = 0), HtmlLink(extract = [Html.AttributeHref, Provider._ExpressionHash])],
			extractFileName				= [HtmlResult(index = 0), HtmlLink()], # File names are cut off (..), but cannot extract it from the link, since spaces and other symbols are replaced in the link.
			extractFileSize				= [HtmlResult(index = 2)],
			extractSourceTimeInexact	= [HtmlResult(index = 1)],
			extractSourceSeeds			= [HtmlResult(index = 3, extract = [Html.ParseText, Html.ParseRemoveComma])],
			extractSourceLeeches		= [HtmlResult(index = 4, extract = [Html.ParseText, Html.ParseRemoveComma])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(id_ = Provider._AttributeNext)])
			if not next: return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		category = self.extractHtml(item, [HtmlResult(index = 0), HtmlSpan(class_ = Provider._AttributeDetails, extract = Html.ParseText)])
		if category is None: return ProviderHtml.Skip # No results found, shows the "direct links" fake table.

		if self.parameterMediaMovie():
			if not Regex.match(data = category, expression = Provider._ExpressionMovie): return ProviderHtml.Skip
		else:
			if not Regex.match(data = category, expression = Provider._ExpressionShow): return ProviderHtml.Skip

		if self.customVerified():
			verified = self.extractHtml(item, [HtmlResult(index = 0), HtmlImage(title_ = Provider._ExpressionVerified)])
			if not verified: return ProviderHtml.Skip

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		# right now
		# 55 minutes ago
		# 19 hours ago
		# Yesterday
		# 3 days ago
		# Last Month
		# 9 months ago
		# 1 Year+
		if Regex.match(data = value, expression = Provider._ExpressionRightNow):
			value = Time.timestamp()
		elif Regex.match(data = value, expression = Provider._ExpressionYesterday):
			value = Time.past(days = 1, format = Time.FormatDate)
		elif Regex.match(data = value, expression = Provider._ExpressionLastMonth):
			value = Time.past(days = 30, format = Time.FormatDate)
		elif Regex.match(data = value, expression = Provider._ExpressionYears):
			value = None

		return value
