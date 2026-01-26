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

# Has paging, but the paging uses a unqiue code in the GET URL. No easy way to do it.

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlTable, HtmlLink, HtmlDiv, HtmlSpan, HtmlUnderlined

class Provider(ProviderHtml):

	_Link					= ['https://pb.wtf', 'https://piratbit.org', 'https://piratbit.top', 'https://piratbit.pw']
	_Mirror					= ['https://piratbit.blogspot.com']

	_Path					= 'tracker/' # Must end with a slash, otherwise returns random results.

	_LimitApproval			= 500

	_ParameterQuery			= 'ss'
	_ParameterSort			= 'o'
	_ParameterSeeds			= '10'
	_ParameterOrder			= 's'
	_ParameterDescending	= '2'
	_ParameterCategory		= 'dc'
	_ParameterSection		= 'df'
	_ParameterUploader		= 'da'
	_ParameterSpeed			= 'ds'
	_ParameterSource		= 'sns'
	_ParameterTime			= 'tm'
	_ParameterIgnore		= '-1'
	_ParameterYes			= '1'
	_ParameterNo			= '0'

	_AttributeTable			= 'tor-tbl'
	_AttributeContent		= 'page_contents'
	_AttributeMain			= 'topocs_maine'
	_AttributeDetails		= 'table-condensed'

	_ExpressionFailure		= r'tor_info.*?(noopener)'
	_ExpressionVerified		= r'(проверено)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name					= 'PiratBit',
			description				= '{name} is less-known open {container} site from Russia. The site contains results in various languages, but most of them are in Russian. {name} does not support paging, requests subpages in order to extract the magnet link, and has other problems with subpages, which substantially increases scraping time.',
			rank					= 2,
			performance				= ProviderHtml.PerformanceBad,

			link					= Provider._Link,
			mirror					= Provider._Mirror,

			customVerified			= True,

			# About 30% of the time the details page does not contain a magnet link, but instead outgoing links asking for donations.
			# In such a case, try again, which in most cases returns the magnet link page.
			# Sometimes also returns a HTTP 503 error, which causes web.py to switch to the next domain.
			retryCount				= 3,
			retryExpression			= Provider._ExpressionFailure,

			formatEncode			= ProviderHtml.FormatEncodePlus,

			searchQuery				= {
										ProviderHtml.RequestMethod : ProviderHtml.RequestMethodPost,
										ProviderHtml.RequestPath : Provider._Path,
										ProviderHtml.RequestData : {
											Provider._ParameterQuery	: ProviderHtml.TermQuery,
											Provider._ParameterSort		: Provider._ParameterSeeds,
											Provider._ParameterOrder	: Provider._ParameterDescending,
											Provider._ParameterUploader	: Provider._ParameterYes,
											Provider._ParameterCategory	: Provider._ParameterNo,
											Provider._ParameterSection	: Provider._ParameterNo,
											Provider._ParameterSpeed	: Provider._ParameterNo,
											Provider._ParameterSource	: Provider._ParameterIgnore,
											Provider._ParameterTime		: Provider._ParameterIgnore,
										},
									},

			extractParser			= ProviderHtml.ParserHtml5, # Some bugs on the details page.
			extractList				= [HtmlResults(id_ = Provider._AttributeTable)],
			extractDetails			= [HtmlResult(index = 1), HtmlLink(extract = Html.AttributeHref)],
			extractLink				= [ProviderHtml.Details, HtmlDiv(id_ = Provider._AttributeContent), HtmlTable(id_ = Provider._AttributeMain), HtmlTable(class_ = Provider._AttributeDetails), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName			= [HtmlResult(index = 1), HtmlLink()],
			extractFileSize			= [HtmlResult(index = 2), HtmlUnderlined()],
			extractSourceTime		= [HtmlResult(index = 6), HtmlUnderlined()],
			extractSourceApproval	= [HtmlResult(index = 5)],
			extractSourceSeeds		= [HtmlResult(index = 3)],
			extractSourceLeeches	= [HtmlResult(index = 4)],
			extractReleaseUploader	= [HtmlResult(index = 6), HtmlLink()],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		if self.customVerified():
			verified = self.extractHtml(item, [HtmlResult(index = 0), HtmlSpan(title_ = Provider._ExpressionVerified)])
			if not verified: return ProviderHtml.Skip

	def processSourceApproval(self, value, item, details = None, entry = None):
		result = ProviderHtml.ApprovalDefault
		try: result += ((1 - result) * (float(value) / Provider._LimitApproval))
		except: pass
		return result
