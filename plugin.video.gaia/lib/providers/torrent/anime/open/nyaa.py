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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlListUnordered, HtmlListItem, HtmlDiv, HtmlImage
from lib.modules.tools import Media, Regex, Language

class Provider(ProviderHtml):

	_Link					= ['https://nyaa.si', 'https://nyaa.iss.one', 'https://nyaa.land', 'https://nyaa.digital', 'https://nyaa.iss.ink', 'https://nyaa.ink', 'https://ny.iss.one']
	_Mirror					= ['https://nyaatorrents.info']
	_Unblock				= {ProviderHtml.UnblockFormat1 : 'nyaa', ProviderHtml.UnblockFormat2 : 'nyaa', ProviderHtml.UnblockFormat3 : 'nyaa', ProviderHtml.UnblockFormat4 : 'nyaa'}

	_CategoryAnime			= '0_0'

	_LimitRequests			= 5 # 7 already too much.
	_LimitApproval			= 200

	_ParameterQuery			= 'q'
	_ParameterCategory		= 'c'
	_ParameterOffset		= 'p'
	_ParameterSort			= 's'
	_ParameterSeeds			= 'seeders'
	_ParameterOrder			= 'o'
	_ParameterDescending	= 'desc'
	_ParameterFilter		= 'f'
	_ParameterAll			= '0'
	_ParameterTrusted		= '2'

	_AttributeContainer		= 'container'
	_AttributeList			= 'torrent-list'
	_AttributePages			= 'pagination'
	_AttributeNext			= 'next'
	_AttributeDisabled		= 'disabled'
	_AttributeSuccess		= 'success'
	_AttributeDanger		= 'danger'

	_ExpressionEnglish		= r'(?<!non.)english' # Exclude "Non-English"

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name							= 'Nyaa',
			description						= '{name} is one of the oldest anime {container} sites. The site contains results in various languages, but most of them are in Japanese. {name} occasionally has unconventional file names which might cause some links to be rejects.',
			rank							= 3,
			performance						= ProviderHtml.PerformanceGood - ProviderHtml.PerformanceStep,

			link							= Provider._Link,
			mirror							= Provider._Mirror,
			unblock							= Provider._Unblock,

			queryExtraShow					= ['%s batch' % ProviderHtml.TermTitleShow], # Packs are marked as "[Batch]".

			customVerified					= True,

			supportMovie					= True,
			supportShow						= True,
			supportPack						= True,

			requestCount					= Provider._LimitRequests, # Returns HTTP 429 if there are too many connections.

			offsetStart						= 1,
			offsetIncrease					= 1,

			formatEncode					= ProviderHtml.FormatEncodePlus,

			searchQuery						= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestData : {
													Provider._ParameterQuery	: ProviderHtml.TermQuery,
													Provider._ParameterCategory	: ProviderHtml.TermCategory,
													Provider._ParameterOffset	: ProviderHtml.TermOffset,
													Provider._ParameterSort		: Provider._ParameterSeeds,
													Provider._ParameterOrder	: Provider._ParameterDescending,
												},
											},
			searchCategoryMovie				= Provider._CategoryAnime,
			searchCategoryShow				= Provider._CategoryAnime,

			extractOptimizeData				= HtmlDiv(class_ = Provider._AttributeContainer),
			extractList						= [HtmlResults(class_ = Provider._AttributeList)],
			extractLink						= [HtmlResult(index = 2), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName					= [HtmlResult(index = 1), HtmlLink(index = -1)],
			extractFileSize					= [HtmlResult(index = 3)],
			extractSubtitleLanguageInexact	= [HtmlResult(index = 0), HtmlImage(extract = Html.AttributeAlt)], # In most cases the "English Translated" category does NOT refer to the audio, but to subtitles.
			extractSourceTime				= [HtmlResult(index = 4, extract = Html.AttributeDataTimestamp)],
			extractSourceApproval			= [HtmlResult(index = 7)],
			extractSourceSeeds				= [HtmlResult(index = 5)],
			extractSourceLeeches			= [HtmlResult(index = 6)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlListItem(class_ = Provider._AttributeNext, extract = Html.AttributeClass)])
			if not next or Provider._AttributeDisabled in next: return ProviderHtml.Skip
		except: self.logError()

	def processSubtitleLanguageInexact(self, value, item, details = None, entry = None):
		if value and Regex.match(data = value, expression = Provider._ExpressionEnglish): return Language.EnglishCode
		else: return None

	def processSourceApproval(self, value, item, details = None, entry = None):
		type = self.extractHtmlValue(item, extract = [Html.AttributeClass, 0])
		if self.customVerified() and not type == Provider._AttributeSuccess: return ProviderJson.Skip

		result = ProviderHtml.ApprovalDefault
		try: result += (1 - result) * (float(value) / Provider._LimitApproval)
		except: pass

		if type == Provider._AttributeSuccess: result += 0.25
		elif type == Provider._AttributeDanger: result -= 0.25

		return max(0, min(1, result))
