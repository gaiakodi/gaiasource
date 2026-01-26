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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= ['https://tntfork.it']
	_Path					= 'index.php'

	_ParameterQuery			= 'titolo'

	_ExpressionLink			= r'bt[im]h:([a-z0-9]{32,})(?:$|&)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name				= 'TNTFork',
			description			= '{name} is a minor open {container} site from Italy. The site contains results in various languages, but most of them are in Italian. {name} has an outdated archive of TNTVillage, limited results, and missing metadata such as the peer counter.',
			rank				= 1,
			performance			= ProviderHtml.PerformanceGood - ProviderHtml.PerformanceStep,
			status				= ProviderHtml.StatusDead, # Website does not exist anymore.

			link				= Provider._Link,

			formatEncode		= ProviderHtml.FormatEncodePlus,

			queryYear			= False, # Adding the year only finds results when encapsulated in brackets.

			searchQuery			= {
									ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
									ProviderHtml.RequestPath : Provider._Path,
									ProviderHtml.RequestData : {
										Provider._ParameterQuery : ProviderHtml.TermQuery,
									},
								},

			extractList			= [HtmlResults(start = 1)],
			extractLink			= [HtmlResult(index = 1), HtmlLink(extract = Html.AttributeHref)],
			extractFileName		= [[HtmlResult(index = 2)], [HtmlResult(index = 3)]],
			extractFileSize		= [HtmlResult(index = 5)],
			extractSourceTime	= [HtmlResult(index = 0)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processLink(self, value, item, details = None, entry = None):
		# Some links are censored: magnet:?xt=urn:btih:Censurato&dn=...
		try:
			if not Regex.match(data = value, expression = Provider._ExpressionLink): return ProviderHtml.Skip
			return value
		except: return None

	def processFileName(self, value, item, details = None, entry = None):
		try: return ' '.join(value)
		except: return None

	def processFileSize(self, value, item, details = None, entry = None):
		try: return value + ' GB'
		except: return None
