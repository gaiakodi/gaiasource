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
from lib.providers.core.html import Html, HtmlResults, HtmlResult, HtmlTable, HtmlDiv, HtmlLink

class Provider(ProviderUsenetHtml):

	_Link					= ['https://binzb.com']
	_Path					= 'search'

	_ParameterQuery			= 'q'
	_ParameterPage			= 'p'

	_AttributeContent		= 'content'
	_AttributeList			= 'list'
	_AttributePoster		= 'poster'
	_AttributeNext			= 'paging_next'

	_ExpressionGet			= '\/get\/(.*?)(?:$|&|\/)'
	_ExpressionUploader		= 'posted\s*by:\s*(.*?)(?:$|[\r\n]+)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderUsenetHtml.initialize(self,
			name						= 'BiNZB',
			description					= '{name} is an open usenet indexer. {name} has few results and some inaccurate metadata. Subpages have to be requested to extract the {container} link which substantially increases scraping time.',
			rank						= 2,
			performance					= ProviderUsenetHtml.PerformanceBad,

			# Update (2025-12):
			# The website does not return any results anymore: "No collections found".
			# More info under nzbID.
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

			extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeContent), # To detect the last page in processOffset().
			extractList					= [HtmlResults(class_ = Provider._AttributeList, start = 1)],
			extractDetails				= [HtmlResult(index = 0), HtmlLink(extract = Html.AttributeHref)],
			extractLink					= [ProviderUsenetHtml.Details, HtmlDiv(id_ = Provider._AttributeContent), HtmlTable(), HtmlLink(href_ = Provider._ExpressionGet, extract = Html.AttributeHref)],
			extractIdLocal				= [ProviderUsenetHtml.Details, HtmlDiv(id_ = Provider._AttributeContent), HtmlTable(), HtmlLink(href_ = Provider._ExpressionGet, extract = [Html.AttributeHref, Provider._ExpressionGet])],
			extractFileName				= [HtmlResult(index = 0), HtmlLink()],
			extractFileSize				= [HtmlResult(index = 3)],
			extractReleaseUploader		= [HtmlResult(index = 0), HtmlDiv(class_ = Provider._AttributePoster, extract = [Html.ParseText, Provider._ExpressionUploader, Html.ParseStrip])],
			extractSourceTimeInexact	= [HtmlResult(index = 1)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlLink(class_ = Provider._AttributeNext)])
			if not next: return ProviderUsenetHtml.Skip
		except: pass

	def processLink(self, value, item, details = None, entry = None):
		if details:
			if not value: return ProviderUsenetHtml.Skip
			return self.linkCurrent(path = value)
		return value

	##############################################################################
	# CLEAN
	##############################################################################

	@classmethod
	def cleanFileName(self, value):
		# BiNZB adds a random space in the file name, which causes some metadata to not be detected.
		# Eg: "Titanic.1997.720p.BluRay.DTS.x 264-DJ.par2" yEnc (1/1)
		# Eg: AMS Titanic.1997.1080p.BluRay.DTS-H D.MA.5.1.x264-FuzerHD [01/89] - "Titanic.1997.1080p.BluRay.DTS-H D.MA.5.1.x264-FuzerHD.par2" yEnc (1/1)
		if value and value.count('.') > 3 and value.count(' ') == 1: value = value.replace(' ', '')
		return value
