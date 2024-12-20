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

from lib.providers.core.html import ProviderHtml, Html, HtmlBody, HtmlResults, HtmlResult, HtmlDiv, HtmlSpan, HtmlLink, HtmlItalic, HtmlListUnordered, HtmlListItem
from lib.modules.tools import Regex, Converter
from lib.modules.network import Container

# iBit often returns different results with the same request.

class Provider(ProviderHtml):

	_Link					= ['https://ibit.to', 'https://ibit.uno', 'https://ibit.am', 'https://ibit.ws']
	_Mirror					= ['https://torrends.to/proxy/ibit']

	_Path					= 'torrent-search/%s/%s/%s:%s/%s/'

	_LimitApproval			= 10

	_CategoryMovie			= ['Movies', 'Anime']
	_CategoryShow			= ['TV', 'Anime']

	_ParameterSeeds			= 'seeders'
	_ParameterDescending	= 'desc'

	_AttributeContents		= 'contents'
	_AttributeTorrents		= 'torrents'
	_AttributeVerified		= 'verified'
	_AttributeVotes			= 'votes'
	_AttributePages			= 'pagination'
	_AttributeInfo			= 'more-info'
	_AttributeLanguage		= 'inLanguage'

	_ExpressionVotes		= '(\d+)\s*votes?'
	_ExpressionDisabled		= '(disabled)'
	_ExpressionCategory		= '(applicationSubCategory)' # Use an expression, since the attribute can contain multiple values.
	_ExpressionUploader		= '(author)' # Use an expression, since the attribute can contain multiple values.

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'iBit',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} requests subpages in order to extract the magnet link and other metadata, which substantially increases scraping time',
			rank						= 3,
			performance					= ProviderHtml.PerformanceBad,
			status						= ProviderHtml.StatusDead, # Server down for more than 30 days (2023-02-20). Still down (2024-12).

			link						= Provider._Link,
			mirror						= Provider._Mirror,

			customVerified				= True,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodeQuote,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path % (ProviderHtml.TermQuery, ProviderHtml.TermCategory, Provider._ParameterSeeds, Provider._ParameterDescending, ProviderHtml.TermOffset),
										},
			searchCategoryMovie			= Provider._CategoryMovie,
			searchCategoryShow			= Provider._CategoryShow,

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContents),
			extractOptimizeDetails		= HtmlBody(),
			extractList					= [HtmlResults(class_ = Provider._AttributeTorrents)],
			extractDetails				= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeHref)],
			extractLink					= [ProviderHtml.Details, Html(extract = Html.ParseCode)],
			extractFileName				= [HtmlResult(index = 0), HtmlLink(extract = Html.ParseTextNested)],
			extractFileExtra			= [ProviderHtml.Details, HtmlListUnordered(class_ = Provider._AttributeInfo), HtmlSpan(itemprop_ = Provider._ExpressionCategory, extract = Html.ParseTextNested)], # Can contain additional info not in the filename (eg: HDR).
			extractFileSize				= [HtmlResult(index = 3)],

			# Cheked multiple files. None of them have the languages shown on the details page, neither audio nor subtitles.
			# It seems that the language entry is arbitrary, simply incorrect, or indicates the movie release language instead of the languages in the actual file.
			#extractAudioLanguageInexact	= [ProviderHtml.Details, HtmlListUnordered(class_ = Provider._AttributeInfo), HtmlSpan(itemprop_ = Provider._AttributeLanguage, extract = Html.ParseTextNested)],

			extractReleaseUploader		= [ProviderHtml.Details, HtmlListUnordered(class_ = Provider._AttributeInfo), HtmlSpan(itemprop_ = Provider._ExpressionUploader, extract = Html.ParseTextNested)],
			extractSourceApproval		= [HtmlResult(index = 1), HtmlItalic(class_ = Provider._AttributeVotes, extract = [Html.AttributeTitle, Provider._ExpressionVotes])],
			extractSourceTimeInexact	= [HtmlResult(index = 2)],
			extractSourceSeeds			= [HtmlResult(index = 4)],
			extractSourceLeeches		= [HtmlResult(index = 5)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		if self.customVerified():
			verified = str(self.extractHtml(item, [HtmlResult(index = 1), HtmlItalic(class_ = Provider._AttributeVerified)]))
			if not verified: return ProviderHtml.Skip

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlListUnordered(class_ = Provider._AttributePages), HtmlListItem(index = -1)])
			if not last or ('class' in last and Regex.match(data = last['class'], expression = Provider._ExpressionDisabled)):
				return ProviderHtml.Skip
		except: self.logError()

	def processLink(self, value, item, details = None, entry = None):
		if details:
			if value:
				magnet = Regex.extract(data = value, expression = '[\'\"]%s[\'\"]' % ProviderHtml.ExpressionMagnet)
				if magnet:
					# Unescape hex-escaped characters (eg: "\\x26").
					magnet = Converter.unicodeHex(magnet)

					# The hash is split with "X-X".
					# Eg: magnet:?xt=urn:btih:AD5FE1537AX-X4BEBF91B2EX-X4C25A29F56X-XDCCD25A819
					hash = Regex.extract(data = magnet, expression = 'urn:bt[im]h:(.*?)(?:$|&)')
					if hash:
						hashCleaned = hash.replace('X-X', '')
						if hashCleaned:
							magnet = magnet.replace(hash, hashCleaned)
							if Container(magnet).torrentHash(): # Check if the cleaned hash is valid.
								return magnet
			return ProviderHtml.Skip

		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		result = ProviderHtml.ApprovalDefault
		try:
			value = float(value.replace(',', ''))
			result += ((1 - result) * (value / Provider._LimitApproval))
		except: pass
		return result
