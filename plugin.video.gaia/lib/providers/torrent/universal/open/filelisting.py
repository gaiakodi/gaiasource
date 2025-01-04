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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv, HtmlTable, HtmlTableCell

class Provider(ProviderHtml):

	_Link					= ['https://filelisting.com']
	_Path					= 'result'

	_ParameterQuery			= 'q'
	_ParameterOffset		= 'f'
	_ParameterSearch		= '+in%3Atitle' # Only search in torrent title - faster.

	_AttributeMain			= 'result-main-center'
	_AttributeTitle			= 'dn-title'
	_AttributeStatus		= 'dn-status'
	_AttributeSize			= 'dn-size'
	_AttributePages			= 'btn-group'
	_AttributeButton		= 'btn'
	_AttributeDisabled		= 'disabled'

	_ExpressionLink			= '-%s\.html' % ProviderHtml.ExpressionSha
	_ExpressionSeeds		= '(\d+)\s*\/\s*\d+'
	_ExpressionLeeches		= '\d+\s*\/\s*(\d+)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'FileListing',
			description					= '{name} is a less-known {container} site. The site contains results in various languages, but most of them are in English. {name} has many {containers}, but some trivial metadata is missing.',
			rank						= 4,
			performance					= ProviderHtml.PerformanceGood,
			status						= ProviderHtml.StatusDead, # Domain does not load anymore. Update (2025-01): Domain still down.

			link						= Provider._Link,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 0,
			offsetIncrease				= 20,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterQuery	: ProviderHtml.TermQuery + Provider._ParameterSearch,
												Provider._ParameterOffset	: ProviderHtml.TermOffset,
											},
										},

			extractOptimizeData			= HtmlDiv(id_ = Provider._AttributeMain),
			extractList					= [HtmlDiv(), HtmlDiv(), HtmlTable(skip = 1)], # Skip, since every other row is an empty table.
			extractHash					= [HtmlTableCell(class_ = Provider._AttributeTitle), HtmlLink(href_ = Provider._ExpressionLink, extract = Provider._ExpressionLink)],
			extractFileName				= [HtmlTableCell(class_ = Provider._AttributeTitle), HtmlLink(href_ = Provider._ExpressionLink, extract = Html.ParseTextNested)],
			extractFileSize				= [HtmlTableCell(class_ = Provider._AttributeSize, extract = Html.ParseTextNested)],
			extractSourceSeeds			= [HtmlTableCell(class_ = Provider._AttributeStatus, extract = [Html.ParseTextNested, Provider._ExpressionSeeds])],
			extractSourceLeeches		= [HtmlTableCell(class_ = Provider._AttributeStatus, extract = [Html.ParseTextNested, Provider._ExpressionLeeches])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = self.extractHtml(data, [HtmlDiv(), HtmlDiv(), HtmlDiv(class_ = Provider._AttributePages), HtmlLink(class_ = Provider._AttributeButton, index = -1, extract = Html.AttributeClass)])
			if not next or Provider._AttributeDisabled in next: return ProviderHtml.Skip
		except: self.logError()
