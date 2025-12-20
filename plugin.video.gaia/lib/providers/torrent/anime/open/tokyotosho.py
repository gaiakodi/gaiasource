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

# https://www.tokyotosho.info/rss_customize.php
# The RSS feed does not have certain info, like the number of seeds, leeches, and downloads.
# Use the HTML search instead.
# The HTML cannot use the "filter" parameter to filter by multiple categories, only the "type" parameter which filters by a single category.
# The search filters can be customized, which are added as a cookie. But the "filter" parameter in the cookie seems to be ingored. Other cookies (like the theme) do seem to work.
# https://www.tokyotosho.info/settings.php

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlTableRow, HtmlLink, HtmlDiv, HtmlSpan, HtmlParagraph
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['http://tokyotosho.info', 'http://tokyotosho.se', 'http://tokyo-tosho.net']
	_Path					= 'search.php'

	_CategoryAll			= '0'
	_CategoryAnime			= ['1', '10', '8', '7', '12', '11', '5'] # 1 = Anime, 10 = Non-English, 8 = Drama, 7 = Raws (Undubbed), 12 = Hentai (Anime), 11 = Batch (Packs), 5 = Other

	_LimitOffset			= 750
	_LimitApproval			= 200

	_ParameterQuery			= 'terms'
	_ParameterFilter		= 'filter'
	_ParameterCategory		= 'type'
	_ParameterName			= 'searchName'
	_ParameterComment		= 'searchComment'
	_ParameterLimit			= 'entries'
	_ParameterOffset		= 'page'
	_ParameterTrue			= 'true'

	_AttributeMain			= 'main'
	_AttributeList			= 'listing'
	_AttributeTop			= 'desc-top'
	_AttributeBottom		= 'desc-bot'
	_AttributeTitle			= 'nofollow'
	_AttributeStats			= 'stats'
	_AttributeAuthorized	= 'auth_ok'
	_AttributeUnauthorized	= 'auth_bad'

	_ExpressionCategory		= 'cat=(\d+)'
	_ExpressionSize			= 'size\s*:\s*([a-z\d\.]+)\s*(?:$|\|)'
	_ExpressionDate			= 'date\s*:\s*([\d\-\:\s]+)\s*[a-z]*\s*(?:$|\|)'
	_ExpressionUploader		= 'submitter\s*:\s*(.*?)\s*(?:$|\|)'
	_ExpressionSeeds		= 's\s*:\s*(\d+)(?:$|\s)'
	_ExpressionLeeches		= 'l\s*:\s*(\d+)(?:$|\s)'
	_ExpressionDownloads	= 'c\s*:\s*(\d+)(?:$|\s)'
	_ExpressionOffset		= 'showing\s*results.*?(\d+)\s*of\s*.*?(\d+)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name							= 'TokyoTosho',
			description						= '{name} is one of the oldest anime {container} sites. The site contains results in various languages, but most of them are in Japanese. {name} occasionally has unconventional file names which might cause some links to be rejects.',
			rank							= 3,
			performance						= ProviderHtml.PerformanceExcellent,

			#gaiaremove - hide the provider for now. Enable once anime is fully supported. Still needs proper testing.
			status							= ProviderHtml.StatusHidden,

			link							= Provider._Link,

			customVerified					= True,

			supportMovie					= True,
			supportShow						= True,
			supportPack						= True,

			offsetStart						= 1,
			offsetIncrease					= 1,

			formatEncode					= ProviderHtml.FormatEncodePlus,

			searchQuery						= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path,
												ProviderHtml.RequestData : {
													Provider._ParameterQuery	: ProviderHtml.TermQuery,
													Provider._ParameterCategory	: ProviderHtml.TermCategory,
													Provider._ParameterOffset	: ProviderHtml.TermOffset,
													Provider._ParameterName		: Provider._ParameterTrue,
												},
											},

			# Do not use the All category (type=0).
			# Otherwise no results are returned for some queries (eg: "dragon ball").
			# An HTTP 500 error is returned. Maybe there are too many results causing the server to fail?
			searchCategoryMovie				= Provider._CategoryAnime,
			searchCategoryShow				= Provider._CategoryAnime,

			extractOptimizeData				= HtmlDiv(id_ = Provider._AttributeMain),
			extractList						= [HtmlResults(class_ = Provider._AttributeList, start = 1)], # First row is a border. Rows are combined in processItems().
			extractLink						= [HtmlResult(class_ = Provider._AttributeTop), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName					= [HtmlResult(class_ = Provider._AttributeTop), HtmlLink(rel_ = Provider._AttributeTitle, extract = Html.ParseTextUnnested)], # Nested spans are for spaces.
			extractFileSize					= [HtmlResult(class_ = Provider._AttributeBottom, extract = [Html.ParseTextUnnested, Provider._ExpressionSize])],
			extractSourceTime				= [HtmlResult(class_ = Provider._AttributeBottom, extract = [Html.ParseTextUnnested, Provider._ExpressionDate])],
			extractSourceApproval			= [HtmlResult(class_ = Provider._AttributeStats, extract = [Html.ParseTextNested, Provider._ExpressionDownloads])],
			extractSourceSeeds				= [HtmlResult(class_ = Provider._AttributeStats, extract = [Html.ParseTextNested, Provider._ExpressionSeeds])],
			extractSourceLeeches			= [HtmlResult(class_ = Provider._AttributeStats, extract = [Html.ParseTextNested, Provider._ExpressionLeeches])],
			extractReleaseUploader			= [HtmlResult(class_ = Provider._AttributeBottom, extract = [Html.ParseTextNested, Provider._ExpressionUploader])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processItems(self, items):
		# Details are split over two rows. Combine every second row.
		if items:
			from lib.modules.tools import Tools
			values = []
			for i in range(0, len(items), 2):
				value = str(items[i]) + str(items[i + 1])
				value = Regex.remove(data = value, expression = '<\/tr>\s*<tr.*?>')
				value = self.parseHtml(value)
				if value:
					value = self.extractHtml(value, HtmlTableRow())
					if value: values.append(value[0])
			return values
		return items

	def processBefore(self, item):
		# This is unnecessary if we request individual categories.
		# But keep this here, in case we retrieve All (type=0) and have to manually check the category.
		if item:
			category = self.extractHtml(item, [HtmlResult(index = 0), HtmlLink(extract = [Html.AttributeHref, Provider._ExpressionCategory])])
			if category and not category in Provider._CategoryAnime: return ProviderHtml.Skip

	def processOffset(self, data, items):
		try:
			offset = self.extractHtml(data, HtmlParagraph())
			if offset:
				for i in offset:
					extract = Regex.extract(data = str(i), expression = Provider._ExpressionOffset, group = None, all = True)
					if extract:
						extract = extract[0]
						if extract and extract[0] == extract[1]:
							return ProviderHtml.Skip
						break
		except: self.logError()

	def processSourceApproval(self, value, item, details = None, entry = None):
		detail = self.extractHtml(item, HtmlResult(class_ = Provider._AttributeBottom))
		if detail:
			authorized = self.extractHtml(detail, HtmlSpan(class_ = Provider._AttributeAuthorized))
			unauthorized = self.extractHtml(detail, HtmlSpan(class_ = Provider._AttributeUnauthorized))
			if self.customVerified() and not authorized: return ProviderJson.Skip

		result = ProviderHtml.ApprovalDefault
		try: result += (1 - result) * (float(value) / Provider._LimitApproval)
		except: pass

		if authorized: result += 0.25
		elif unauthorized: result -= 0.25

		return max(0, min(1, result))
