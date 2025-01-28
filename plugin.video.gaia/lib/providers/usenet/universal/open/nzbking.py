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

from lib.providers.core.usenet import ProviderUsenetHtml
from lib.providers.core.html import Html, HtmlResults, HtmlResult, HtmlBody, HtmlDiv, HtmlLink
from lib.modules.tools import Regex

class Provider(ProviderUsenetHtml):

	_Link				= ['https://nzbking.com']

	_LimitOffset		= 50

	_ParameterQuery		= 'q'
	_ParameterOffset	= 'o'
	_ParameterFormat	= 'ft'
	_ParameterVideo		= 'vi'

	_AttributeResult	= 'search-result'
	_AttributeSubject	= 'search-subject'
	_AttributeAge		= 'search-age'
	_AttributePoster	= 'search-poster'
	_AttributePages		= 'pagination'

	_ExpressionId		= 'nzb:(.*?)(?:$|\/)'
	_ExpressionName		= '(.+?)(?:<br\/?>|<a\s+|[\r\n]+)'
	_ExpressionSize		= 'size:\s*(.*?)(?:$|[\r\n]+)'
	_ExpressionPassword	= 'password\s*protected'
	_ExpressionParts	= 'parts:\s*(\d+)\s*\/\s*(\d+)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderUsenetHtml.initialize(self,
			name						= 'NZBKing',
			description					= '{name} is a popular open usenet indexer. The site contains many English titles, but is also a great source for other European languages. {name} has a lot more results than most other open usenet indexers.',
			rank						= 5,

			# Update (2025-01): main page loads, but search page returns an error "Page unavailable".
			#performance				= ProviderUsenetHtml.PerformanceGood,
			performance					= ProviderUsenetHtml.PerformanceMedium,

			# Website is down since the start of Nov 2022, but admins said they have to take down the server "for a while", so might come back up.
			# Mark only as Impaired. If offline for a few months, change the status to Dead.
			# https://www.reddit.com/r/usenet/comments/yk8bpj/nzbkingcom_shutting_down_for_uncertain_time/
			status						= ProviderUsenetHtml.StatusImpaired,

			link						= Provider._Link,

			customPassword				= True,
			customIncomplete			= True,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 0,
			offsetIncrease				= Provider._LimitOffset,

			formatEncode				= ProviderUsenetHtml.FormatEncodeQuote,

			searchQuery					= {
											ProviderUsenetHtml.RequestMethod : ProviderUsenetHtml.RequestMethodGet,
											ProviderUsenetHtml.RequestData : {
												Provider._ParameterQuery	: ProviderUsenetHtml.TermQuery,
												Provider._ParameterOffset	: ProviderUsenetHtml.TermOffset,
												Provider._ParameterFormat	: Provider._ParameterVideo,
											},
										},

			extractOptimizeData			= HtmlBody(), # To detect the last page in processOffset().
			extractList					= [HtmlDiv(class_ = Provider._AttributeResult, start = 1)],
			extractLink					= [HtmlDiv(class_ = Provider._AttributeSubject), HtmlLink(href_ = Provider._ExpressionId, extract = Html.AttributeHref)],
			extractIdLocal				= [HtmlDiv(class_ = Provider._AttributeSubject), HtmlLink(href_ = Provider._ExpressionId, extract = [Html.AttributeHref, Provider._ExpressionId])],
			extractFileName				= [HtmlDiv(class_ = Provider._AttributeSubject, extract = [Html.ParseText, Provider._ExpressionName])],
			extractFileSize				= [HtmlDiv(class_ = Provider._AttributeSubject, extract = [Html.ParseText, Provider._ExpressionSize])],
			extractReleaseUploader		= [HtmlDiv(class_ = Provider._AttributePoster)],
			extractSourceTime			= [HtmlDiv(class_ = Provider._AttributeAge)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink()])
			if not next: return ProviderUsenetHtml.Skip
		except: pass

	def processBefore(self, item):
		subject = self.extractHtml(item, [HtmlDiv(class_ = Provider._AttributeSubject, extract = Html.ParseText)])
		if self.customPassword():
			try:
				if Regex.match(data = subject, expression = Provider._ExpressionPassword): return ProviderUsenetHtml.Skip
			except: pass
		if self.customIncomplete():
			try:
				parts = Regex.extract(data = subject, expression = Provider._ExpressionParts, group = None, all = True)[0]
				if int(parts[0]) < int(parts[1]): return ProviderUsenetHtml.Skip
			except: pass

	def processLink(self, value, item, details = None, entry = None):
		if not value: return ProviderUsenetHtml.Skip
		return self.linkCurrent(path = value)
