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
from lib.providers.core.html import Html, HtmlResults, HtmlResult, HtmlForm, HtmlInput, HtmlLink, HtmlDiv, HtmlSpan, HtmlListItem
from lib.modules.tools import Regex

class Provider(ProviderUsenetHtml):

	_Link					= ['https://binsearch.info']

	_PathSearch				= {
								ProviderUsenetHtml.Version1 : 'search',
								ProviderUsenetHtml.Version2 : None,
							}
	_PathDownload			= {
								ProviderUsenetHtml.Version1 : '/nzb?%s=on',
								ProviderUsenetHtml.Version2 : '/?action=nzb&%s=on',
							}

	_LimitOffset			= {
								ProviderUsenetHtml.Version1 : 100,
								ProviderUsenetHtml.Version2 : 250,
							}

	_ParameterQuery			= 'q'
	_ParameterOffset		= 'min'
	_ParameterLimit			= 'max'
	_ParameterLimitAge		= 'adv_age'
	_ParameterLimitSize		= 'xminsize'
	_ParameterDate			= 'date'
	_ParameterFormat		= 'postdate'
	_ParameterSort			= 'adv_sort'

	_AttributeContainer		= 'items-stretch'
	_AttributeResults1		= 'result-table'
	_AttributeResults2		= 'r2'
	_AttributeSubject		= 's'
	_AttributeDescription	= 'd'
	_AttributeMenu			= 'xMenuT'
	_AttributeIncomplete	= 'incomplete'
	_AttributePages			= 'navigation'
	_AttributeDisabled		= 'disabled'

	_ExpressionNext			= '(>|&gt;)'
	_ExpressionSize			= 'size\s*:\s*(.+?)(?:$|,)'
	_ExpressionParts		= 'parts\s*available:\s*(\d+)\s*\/\s*(\d+)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()

		name			= 'Binsearch'
		description		= '{name} is one of the oldest open usenet indexers. {name} has mostly incomplete {containers}, duplicate results, missing metadata, and incorrect file sizes, and should therefore be avoided if possible.'
		rank			= 1
		performance		= ProviderUsenetHtml.PerformanceMedium - ProviderUsenetHtml.PerformanceStep
		customVersion	= 2

		query = {
			Provider._ParameterQuery	: ProviderUsenetHtml.TermQuery,
			Provider._ParameterOffset	: ProviderUsenetHtml.TermOffset,
			Provider._ParameterLimit	: Provider._LimitOffset[version],
			Provider._ParameterSort		: Provider._ParameterDate,
			Provider._ParameterFormat	: Provider._ParameterDate,
		}

		age = self.customTime(days = True)
		if age: query[Provider._ParameterLimitAge] = age
		size = self.customSize()
		if size: query[Provider._ParameterLimitSize] = size

		# New API (post 2025-12).
		if version == ProviderUsenetHtml.Version1:
			ProviderUsenetHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,

				link						= Provider._Link,

				customVersion				= customVersion,
				customIncomplete			= True,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 0,
				offsetIncrease				= 1,

				formatEncode				= ProviderUsenetHtml.FormatEncodePlus,

				searchQuery					= {
												ProviderUsenetHtml.RequestMethod : ProviderUsenetHtml.RequestMethodGet,
												ProviderUsenetHtml.RequestPath : Provider._PathSearch[version],
												ProviderUsenetHtml.RequestData : query,
											},

				extractParser				= ProviderUsenetHtml.ParserHtml5, # Contains many unclosed tags. Use lenient parsing.
				extractOptimizeData			= HtmlForm(class_ = Provider._AttributeContainer), # To detect the last page in processOffset().
				extractList					= [HtmlResults(class_ = Provider._AttributeResults1, start = 1)],
				extractLink					= [HtmlResult(index = 1), HtmlInput(extract = Html.AttributeName)],
				extractIdLocal				= [HtmlResult(index = 1), HtmlInput(extract = Html.AttributeName)],
				extractFileName				= [HtmlResult(index = 2), HtmlLink()],
				extractFileSize				= [HtmlResult(index = 2), HtmlDiv(), HtmlDiv(), HtmlSpan(index = 0)],
				extractReleaseUploader		= [HtmlResult(index = 2), HtmlDiv(), HtmlDiv(), HtmlSpan(index = 2), HtmlLink()],
				extractSourceTime			= [HtmlResult(index = 3)],
			)

		elif version == ProviderUsenetHtml.Version2:
			ProviderUsenetHtml.initialize(self,
				name						= name,
				description					= description,
				rank						= rank,
				performance					= performance,

				link						= Provider._Link,

				customVersion				= customVersion,
				customIncomplete			= True,

				supportMovie				= True,
				supportShow					= True,
				supportPack					= True,

				offsetStart					= 0,
				offsetIncrease				= Provider._LimitOffset[version],

				formatEncode				= ProviderUsenetHtml.FormatEncodePlus,

				searchQuery					= {
												ProviderUsenetHtml.RequestMethod : ProviderUsenetHtml.RequestMethodGet,
												ProviderUsenetHtml.RequestData : query,
											},

				extractParser				= ProviderUsenetHtml.ParserHtml5, # Contains many unclosed tags. Use lenient parsing.
				extractOptimizeData			= HtmlForm(), # To detect the last page in processOffset().
				extractList					= [HtmlResults(id_ = Provider._AttributeResults2, start = 1)],
				extractLink					= [HtmlResult(index = 1), HtmlInput(extract = Html.AttributeName)],
				extractIdLocal				= [HtmlResult(index = 1), HtmlInput(extract = Html.AttributeName)],
				extractFileName				= [HtmlResult(index = 2), Html(class_ = Provider._AttributeSubject)],
				extractFileSize				= [HtmlResult(index = 2), Html(class_ = Provider._AttributeDescription, extract = Provider._ExpressionSize)],
				extractReleaseUploader		= [HtmlResult(index = 3)],
				extractSourceTime			= [HtmlResult(index = 5)],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			version = self.customVersion()
			if version == ProviderUsenetHtml.Version1:
				last = self.extractHtml(data, [Html(role_ = Provider._AttributePages, index = -1), HtmlListItem(index = -1, extract = Html.AttributeClass)])
				if last and Provider._AttributeDisable in last: return ProviderUsenetHtml.Skip
			elif version == ProviderUsenetHtml.Version2:
				pages = self.extractHtml(data, [Html(class_ = Provider._AttributeMenu, index = -1), HtmlLink(index = -1, extract = Html.ParseText)])
				if pages:
					next = False
					for page in pages:
						if page == Provider._ExpressionNext:
							next = True
							break
					if not next: return ProviderUsenetHtml.Skip
		except: pass

	def processBefore(self, item):
		if self.customIncomplete():
			version = self.customVersion()
			if version == ProviderUsenetHtml.Version1:
				parts = self.extractHtml(item, [HtmlResult(index = 2), HtmlDiv(), HtmlDiv(), HtmlSpan(index = 1, extract = Html.AttributeClass)])
				if parts and Provider._AttributeIncomplete in parts: return ProviderUsenetHtml.Skip
			elif version == ProviderUsenetHtml.Version2:
				try:
					parts = self.extractHtml(item, [HtmlResult(index = 2), Html(class_ = Provider._AttributeDescription, extract = Html.ParseText)])
					parts = Regex.extract(data = parts, expression = Provider._ExpressionParts, group = None, all = True)[0]
					if int(parts[0]) < int(parts[1]): return ProviderUsenetHtml.Skip
				except: pass

	def processLink(self, value, item, details = None, entry = None):
		if not value: return ProviderUsenetHtml.Skip
		return self.linkCurrent(path = Provider._PathDownload[self.customVersion()] % value)
