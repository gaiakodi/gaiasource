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

from lib.providers.core.html import ProviderHtml, Html, HtmlBody, HtmlTable, HtmlTableRow, HtmlTableCell, HtmlLink
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://magnet4you.me']
	_Unblock				= {ProviderHtml.UnblockFormat4 : 'magnet4you'}
	_Path					= 'search.php' # Must end with a slash.

	_LimitOffset			= 80
	_LimitApproval			= 10 # Some values in the thousands, but most are low or 0.

	_ParameterSearch		= 's'
	_ParameterOffset		= 'start'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'seed'

	_AttributeItem			= 'tb4'
	_AttributePage			= 'botton444'

	_ExpressionNext			= '(next)'
	_ExpressionThousand		= '(k)'
	_ExpressionMillion		= '(m)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'Magnet4You',
			description					= '{name} is a well-known {container} site. The site contains many English results, but also results in various other languages. {name} has many high-quality results with mostly good metadata.',
			rank						= 5,
			performance					= ProviderHtml.PerformanceGood,
			status						= ProviderHtml.StatusDead, # Cloudflare says host is unreachable. Rechecked after a few weeks, still the same problem. Update (2025-06): domain has been down completely for a long time.

			link						= Provider._Link,
			unblock						= Provider._Unblock,


			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 0,
			offsetIncrease				= Provider._LimitOffset,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterSearch	: ProviderHtml.TermQuery,
												Provider._ParameterOffset	: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
											},
										},

			# The HTML returned is changed by JS, so check the original source.
			extractOptimizeData			= HtmlBody(), # To detect the last page in processOffset().
			extractList					= [HtmlTable(class_ = Provider._AttributeItem)],
			extractLink					= [HtmlTableCell(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlTableCell(index = 0)],
			extractFileSize				= [HtmlTableCell(index = 2)],
			extractSourceTimeInexact	= [HtmlTableCell(index = 1)],
			extractSourceApproval		= [HtmlTableCell(index = 6)],
			extractSourceSeeds			= [HtmlTableCell(index = 4)],
			extractSourceLeeches		= [HtmlTableCell(index = 5)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlLink(class_ = Provider._AttributePage, index = -1, extract = Html.ParseText)])
			if not last or not Regex.match(data = last, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processItem(self, item):
		item = self.extractHtml(item, [HtmlTableRow(index = 0)])
		link = self.extractHtml(item, [HtmlTableCell(index = 0), HtmlLink(href_ = ProviderHtml.ExpressionMagnet)])
		if not link: return ProviderHtml.Skip # Items are added twice. One has a magnet link, the other one not.
		return item

	def processSourceApproval(self, value, item, details = None, entry = None):
		result = ProviderHtml.ApprovalDefault
		if value:
			try:
				value = Regex.replace(data = value, expression = Provider._ExpressionThousand, replacement = '000')
				value = Regex.replace(data = value, expression = Provider._ExpressionMillion, replacement = '000000')
				result += (1 - result) * min(1, (float(value) / Provider._LimitApproval))
			except: pass
		return result
