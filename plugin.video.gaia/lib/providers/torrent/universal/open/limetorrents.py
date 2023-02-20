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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlImage
from lib.modules.tools import Regex, Time

class Provider(ProviderHtml):

	_Link					= ['https://limetorrents.lol', 'https://limetorrents.pro', 'https://limetorrents.info', 'https://limetorrents.co', 'https://limetor.com', 'https://limetor.pro']
	_Mirror					= ['https://limetorrents.online/mirror-proxy-sites-to-unblock-limetorrents-cc']
	_Unblock				= {ProviderHtml.UnblockFormat1 : 'limetorrents', ProviderHtml.UnblockFormat2 : 'limetorrents', ProviderHtml.UnblockFormat3 : 'limetorrents', ProviderHtml.UnblockFormat4 : 'limetorrents'}
	_Path					= 'search/%s/%s/seeds/%s/'

	_LimitApproval			= 5

	_CategoryMovie			= 'movies'
	_CategoryShow			= 'tv'

	_AttributeContent		= 'content'
	_AttributeTable			= 'table2'
	_AttributeName			= 'tt-name'
	_AttributeOptions		= 'tt-options'
	_AttributeVoteUp		= 'tt-vup'
	_AttributeVoteDown		= 'tt-vdown'
	_AttributePages			= 'search_stat'
	_AttributeNext			= 'next'

	_ExpressionHash			= '\/torrent\/([a-z0-9]{16,})(?:[\/\?]|\.torrent)'
	_ExpressionTime			= '(.*?)(?:\-|\s+in|$)'
	_ExpressionVerified		= '(verified)'

	_ExpressionRightNow		= '(right\s*now)'
	_ExpressionYesterday	= '(yesterday)'
	_ExpressionLastMonth	= '(last\s*month)'
	_ExpressionYears		= '(year\s*\+)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'LimeTorrents',
			description					= '{name} is a well-known {container} site. The site contains results in various languages, but most of them are in English. {name} has many {containers}, but with some inaccurate metadata.',
			rank						= 4,
			performance					= ProviderHtml.PerformanceGood,

			link						= Provider._Link,
			mirror						= Provider._Mirror,
			unblock						= Provider._Unblock,

			customVerified				= True,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodeMinus,

			searchQuery					= Provider._Path % (ProviderHtml.TermCategory, ProviderHtml.TermQuery, ProviderHtml.TermOffset),
			searchCategoryMovie			= Provider._CategoryMovie,
			searchCategoryShow			= Provider._CategoryShow,

			extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeContent), # To detect the last page in processOffset().
			extractList					= [HtmlResults(class_ = Provider._AttributeTable, start = 1)],
			extractHash					= [HtmlResult(index = 0), HtmlLink(href_ = Provider._ExpressionHash, extract = [Html.AttributeHref, Provider._ExpressionHash])],
			extractFileName				= [HtmlResult(index = 0), HtmlDiv(class_ = Provider._AttributeName)], # File names are cut off (..), but cannot extract it from the link, since spaces and other symbols are replaced in the link
			extractFileSize				= [HtmlResult(index = 2)],
			extractSourceTimeInexact	= [HtmlResult(index = 1, extract = [Html.ParseText, Provider._ExpressionTime])],
			extractSourceApproval		= [[HtmlResult(index = 0), HtmlDiv(class_ = Provider._AttributeOptions), HtmlDiv(class_ = Provider._AttributeVoteUp)], [HtmlResult(index = 0), HtmlDiv(class_ = Provider._AttributeOptions), HtmlDiv(class_ = Provider._AttributeVoteDown)]],
			extractSourceSeeds			= [HtmlResult(index = 3)],
			extractSourceLeeches		= [HtmlResult(index = 4)],
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
		if self.customVerified():
			verified = self.extractHtml(item, [HtmlDiv(class_ = Provider._AttributeOptions), HtmlImage(title_ = Provider._ExpressionVerified)])
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

	def processSourceApproval(self, value, item, details = None, entry = None):
		votes = 0
		try: votes += float(value[0])
		except: pass
		try: votes -= float(value[1])
		except: pass
		return ProviderHtml.ApprovalDefault + ((1 - ProviderHtml.ApprovalDefault) * max(-1, min(1, votes / Provider._LimitApproval)))
