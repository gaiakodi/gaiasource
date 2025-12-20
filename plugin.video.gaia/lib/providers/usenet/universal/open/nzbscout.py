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
from lib.providers.core.html import Html, HtmlMain, HtmlDiv, HtmlLink
from lib.modules.tools import Regex

class Provider(ProviderUsenetHtml):

	_Link					= ['https://nzbscout.com']
	_Path					= 'search'

	_LimitApproval			= 1000

	_ParameterQuery			= 'q'
	_ParameterPage			= 'page'

	_AttributeContent		= 'content'
	_AttributeProduct		= 'product'
	_AttributeTitle			= 'product-title'
	_AttributeDownload		= 'btn-dwn'
	_AttributeDetails		= 'pb-lg-1'
	_AttributePages			= 'pagination'
	_AttributeNext			= 'paging_next'

	_ExpressionId			= '.*\/([a-z0-9\-]+)(?:$|\/)'
	_ExpressionSize			= 'size\s*:?\s*(\d+(?:\.\d+)?\s*[kmgt]?b)\s*(?:$|\n)'
	_ExpressionTime			= 'posted\s*:?\s*([\d\-\:\s]+)\s*(?:$|\n)'
	_ExpressionUploader		= 'poster\s*:?\s*(.*?)\s*(?:$|\n)'
	_ExpressionDownloads	= 'downloaded\s*:?\s*([\d\,]+)\s*times?\s*(?:$|\n)'
	_ExpressionVideo		= 'video\s*format\s*:?\s*(.*?)\s*(?:$|\n)'
	_ExpressionCodec		= 'codec\s*:?\s*(.*?)\s*(?:$|\n)'
	_ExpressionResolution	= 'width\s*x\s*height\s*:?\s*(.*?)\s*(?:$|\n)'
	_ExpressionAspect		= 'aspect\s*:?\s*(.*?)\s*(?:$|\n)'
	_ExpressionAudio		= 'audio\s*format\s*:?\s*(.*?)\s*(?:$|\n)'
	_ExpressionChannels		= 'channels\s*:?\s*(.*?)\s*(?:$|\n)'
	_ExpressionLanguage		= 'media\s*info.*language\s*:?\s*(.*?)\s*(?:$|\n)'
	_ExpressionAnonymous	= '^anonymous$'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderUsenetHtml.initialize(self,
			name						= 'NZBScout',
			description					= '{name} is a new open usenet indexer. The site contains many English titles, but is also a great source for other European languages. {name} has fewer results than most other open usenet indexers.',
			rank						= 4,
			performance					= ProviderUsenetHtml.PerformanceBad,

			#gaiaremove
			# Update (2025-12): Domain just shows "Redirecting" with an empty page. If still inaccesible in a few months, change to StatusDead.
			status						= ProviderUsenetHtml.StatusImpaired,

			link						= Provider._Link,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderUsenetHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderUsenetHtml.RequestMethod : ProviderUsenetHtml.RequestMethodGet,
											ProviderUsenetHtml.RequestPath : Provider._Path,
											ProviderUsenetHtml.RequestData : {
												Provider._ParameterQuery	: ProviderUsenetHtml.TermQuery,
												Provider._ParameterPage		: ProviderUsenetHtml.TermOffset,
											},
										},

			extractOptimizeData			= HtmlMain(id_ = Provider._AttributeContent), # To detect the last page in processOffset().
			extractOptimizeDetails		= HtmlMain(id_ = Provider._AttributeContent),
			extractList					= [HtmlDiv(class_ = Provider._AttributeProduct)],
			extractDetails				= [HtmlDiv(class_ = Provider._AttributeTitle), HtmlLink(extract = Html.AttributeHref)],
			extractLink					= [ProviderUsenetHtml.Details, HtmlLink(class_ = Provider._AttributeDownload, extract = Html.AttributeHref)],
			extractIdLocal				= [ProviderUsenetHtml.Details, HtmlLink(class_ = Provider._AttributeDownload, extract = [Html.AttributeHref, Provider._ExpressionId])],
			extractVideoCodec			= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 0, extract = [Html.ParseTextNested])],
			extractVideoResolution		= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 0, extract = [Html.ParseTextNested, Provider._ExpressionResolution])],
			extractVideoAspect			= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 0, extract = [Html.ParseTextNested, Provider._ExpressionAspect, Html.ParseFloat])],
			extractAudioCodec			= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 0, extract = [Html.ParseTextNested, Provider._ExpressionAudio])],
			extractAudioChannels		= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 0, extract = [Html.ParseTextNested, Provider._ExpressionChannels])],
			extractAudioLanguageInexact	= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 0, extract = [Html.ParseTextNested])],
			extractFileName				= [HtmlDiv(class_ = Provider._AttributeTitle), HtmlLink()],
			extractFileSize				= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 1, extract = [Html.ParseTextNested, Provider._ExpressionSize])],
			extractReleaseUploader		= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 1, extract = [Html.ParseTextNested, Provider._ExpressionUploader])],
			extractSourceTime			= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 1, extract = [Html.ParseTextNested, Provider._ExpressionTime])],
			extractSourceApproval		= [ProviderUsenetHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails, index = 1, extract = [Html.ParseTextNested, Provider._ExpressionDownloads])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink(class_ = Provider._AttributeNext)])
			if not next: return ProviderUsenetHtml.Skip
		except: pass

	def processBefore(self, item):
		try:
			# Validate to only retrieve sub-pages that are valid.
			name = self.extractHtml(item, [HtmlDiv(class_ = Provider._AttributeTitle), HtmlLink(extract = Html.ParseTextNested)])
			if not self.searchValid(data = name): return ProviderUsenetHtml.Skip
		except: self.logError()

	def processReleaseUploader(self, value, item, details = None, entry = None):
		if value and Regex.match(data = value, expression = Provider._ExpressionAnonymous): value = None
		return value if value else None

	def processVideoCodec(self, value, item, details = None, entry = None):
		if value:
			values = []
			values.append(Regex.extract(data = value, expression = Provider._ExpressionVideo))
			values.append(Regex.extract(data = value, expression = Provider._ExpressionCodec))
			value = ' '.join([i for i in values if i])
		return value if value else None

	def processAudioLanguageInexact(self, value, item, details = None, entry = None):
		# There can be 2 language entries. One for the original movie release, and one for the uploaded file.
		if value: value = Regex.extract(data = value, expression = Provider._ExpressionLanguage, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines)
		return value if value else None

	def processSourceApproval(self, value, item, details = None, entry = None):
		if details:
			result = ProviderUsenetHtml.ApprovalDefault
			try:
				value = float(value.replace(',', ''))
				result += ((1 - result) * (value / Provider._LimitApproval))
			except: pass
			return result
		return None
