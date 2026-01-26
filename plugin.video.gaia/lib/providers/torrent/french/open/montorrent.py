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

from lib.providers.core.html import ProviderHtml, Html, HtmlLink, HtmlDiv
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://montorrent.com']

	_Path					= 'recherche/' # Must end with a slash.

	_LimitApproval			= 100000

	_CategoryMovie			= 's_films'
	_CategoryShow			= 's_series'

	_ParameterQuery			= 'query'
	_ParameterSort			= 'order'
	_ParameterSeeds			= 'seeders'
	_ParameterOrder			= 'orderby'
	_ParameterDescending	= 'desc'
	_ParameterPage			= 'page'
	_ParameterOn			= 'on'

	_AttributeContainer		= 'container-body'
	_AttributeItem			= 't-details'
	_AttributeName			= 't-rls'
	_AttributeSize			= 't-taille'
	_AttributeSeeds			= 't-sources'
	_AttributeLeeches		= 't-clients'
	_AttributeLink			= 'telchargement-torrent'
	_AttributeDetails		= 'statistiques-torrent'
	_AttributeDownloads		= 'telecharges'
	_AttributePages			= 'pagination'

	_ExpressionNext			= r'(suiv|→)'
	_ExpressionNumber		= r'(\d+)'
	_ExpressionTime			= r'(d.?ajout)'
	_ExpressionYear			= r'(\s*an)'
	_ExpressionMonth		= r'(\s*mois)'
	_ExpressionWeek			= r'(\s*semain)'
	_ExpressionDay			= r'(\s*jour)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name						= 'MonTorrent',
			description					= '{name} is less-known open {container} site from France. The site contains results in various languages, but most of them are in French. {name} requests subpages in order to extract the magnet link and other metadata, which substantially increases scraping time.',
			rank						= 4,
			performance					= ProviderHtml.PerformanceBad,
			status						= ProviderHtml.StatusDead, # Website does not exist anymore.

			link						= Provider._Link,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterQuery	: ProviderHtml.TermQuery,
												ProviderHtml.TermCategory	: Provider._ParameterOn,
												Provider._ParameterPage		: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
												Provider._ParameterOrder	: Provider._ParameterDescending,
											},
										},
			searchCategoryMovie			= Provider._CategoryMovie,
			searchCategoryShow			= Provider._CategoryShow,

			extractOptimizeData			= HtmlDiv(class_ = Provider._AttributeContainer), # To detect the last page in processOffset().
			extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeContainer),
			extractList					= [HtmlDiv(class_ = Provider._AttributeItem)],
			extractDetails				= [HtmlDiv(class_ = Provider._AttributeName), HtmlLink(extract = Html.AttributeHref)],
			extractLink					= [ProviderHtml.Details, HtmlDiv(id_ = Provider._AttributeLink), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileName				= [HtmlDiv(class_ = Provider._AttributeName)],
			extractFileSize				= [HtmlDiv(class_ = Provider._AttributeSize)],
			extractSourceTimeInexact	= [ProviderHtml.Details, HtmlDiv(id_ = Provider._AttributeDetails), HtmlDiv(title_ = Provider._ExpressionTime)],
			extractSourceApproval		= [ProviderHtml.Details, HtmlDiv(id_ = Provider._AttributeDetails), HtmlDiv(class_ = Provider._AttributeDownloads, extract = [Html.ParseText, Html.ParseRemoveComma, Provider._ExpressionNumber])],
			extractSourceSeeds			= [HtmlDiv(class_ = Provider._AttributeSeeds)],
			extractSourceLeeches		= [HtmlDiv(class_ = Provider._AttributeLeeches)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			next = False
			pages = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), HtmlLink()])
			if pages:
				for page in pages:
					if Regex.match(data = page.text, expression = Provider._ExpressionNext):
						next = True
						break
			if not next: return ProviderHtml.Skip
		except: self.logError()

	def processSourceTimeInexact(self, value, item, details = None, entry = None):
		try:
			unit = None
			if Regex.match(data = value, expression = Provider._ExpressionYear): unit = 'years'
			elif Regex.match(data = value, expression = Provider._ExpressionMonth): unit = 'months'
			elif Regex.match(data = value, expression = Provider._ExpressionWeek): unit = 'weeks'
			elif Regex.match(data = value, expression = Provider._ExpressionDay): unit = 'days'
			if unit:
				value = Regex.extract(data = value, expression = Provider._ExpressionNumber)
				value = '%s %s ago' % (value, unit)
		except: pass
		return value

	def processSourceApproval(self, value, item, details = None, entry = None):
		if details:
			result = ProviderHtml.ApprovalDefault
			try: result += (1 - result) * (float(value) / Provider._LimitApproval)
			except: pass
			return result
		return value
