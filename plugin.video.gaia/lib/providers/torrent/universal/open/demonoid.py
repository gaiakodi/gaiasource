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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlTable, HtmlTableBody, HtmlTableRow, HtmlTableCell, HtmlLink
from lib.modules.tools import Regex
from lib.modules.network import Networker
from lib.modules.concurrency import Lock, Semaphore

class Provider(ProviderHtml):

	_Link					= ['https://demonoid.is']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'demonoid', ProviderHtml.UnblockFormat3 : 'demonoid', ProviderHtml.UnblockFormat4 : 'demonoid'}
	_Path					= 'files/' # Must end with a slash.

	_LimitApproval			= 250

	_CategoryMovie			= '8'
	_CategoryShow			= '12'

	_ParameterSearch		= 'query'
	_ParameterCategory		= 'category'
	_ParameterPage			= 'page'
	_ParameterSort			= 'sort'
	_ParameterSeeds			= 'S'

	_AttributeContainer		= 'ctable_content_no_pad'
	_AttributeTime			= 'added_today'

	_ExpressionTime			= r'added\s*on.*?,\s*(.*)'
	_ExpressionMagnet		= r'(downloadmagnet)'
	_ExpressionNext			= r'(next)'

	_Lock1					= Semaphore(5)
	_Lock2					= Lock()

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		extractLink = [Html(index = 1), HtmlTableCell(index = 2), HtmlLink(href_ = Provider._ExpressionMagnet, extract = Html.AttributeHref)]

		ProviderHtml.initialize(self,
			name						= 'Demonoid',
			description					= '{name} is one of the oldest {container} sites. The site contains results in various languages, but most of them are in English. {name} requests subpages in order to extract the magnet link, which substantially increases scraping time. {name} has strong Cloudflare protection that might not be bypassable and cause scraping to fail.' ,
			rank						= 3,
			performance					= ProviderHtml.PerformanceGood - ProviderHtml.PerformanceStep,

			# Cloudflare. Update (2025-06): domain is down.
			# From Reddit is seems to be down for 6+ months.
			# From Internet Archives it seems that the last time the domain was working was April 2024.
			# https://web.archive.org/web/20250000000000*/demonoid.is
			#status						= ProviderHtml.StatusCloudflare,
			status						= ProviderHtml.StatusDead,

			link						= Provider._Link,
			unblock						= Provider._Unblock,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= ProviderHtml.FormatEncodePlus,

			searchConcurrency			= True, # To resolve the links in processLink() concurrently.
			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path,
											ProviderHtml.RequestData : {
												Provider._ParameterSearch	: ProviderHtml.TermQuery,
												Provider._ParameterCategory	: ProviderHtml.TermCategory,
												Provider._ParameterPage		: ProviderHtml.TermOffset,
												Provider._ParameterSort		: Provider._ParameterSeeds,
											},
										},
			searchCategoryMovie			= Provider._CategoryMovie,
			searchCategoryShow			= Provider._CategoryShow,


			extractParser				= ProviderHtml.ParserHtml5, # Some HTML errors.
			#extractOptimizeData		= HtmlTableCell(class_ = Provider._AttributeContainer), # Does not work with with ParserHtml5.

			# Do not combine 3 rows, since somtimes multiple torrents can be listed under the same date row.
			# Instead filter out the date rows (align_ = None), combine 2 rows, and extract the date manually.
			#extractList				= [HtmlTableCell(class_ = Provider._AttributeContainer), HtmlResults(index = 1, start = 1, combine = 3)],
			extractList					= [HtmlTableCell(class_ = Provider._AttributeContainer), HtmlTable(index = 1), HtmlTableBody(optional = True, recursive = False), HtmlTableRow(align_ = None, recursive = False, start = 0, combine = 2)],

			extractLink					= extractLink,
			extractFileName				= [Html(index = 0)],
			extractFileSize				= [Html(index = 1), HtmlTableCell(index = 3)],
			extractReleaseUploader		= [Html(index = 1), HtmlTableCell(index = 1)],
			extractSourceTime			= extractLink, # Extract the link in order to manually extract the time later on.
			extractSourceApproval		= [Html(index = 1), HtmlTableCell(index = 5)],
			extractSourceSeeds			= [Html(index = 1), HtmlTableCell(index = 6)],
			extractSourceLeeches		= [Html(index = 1), HtmlTableCell(index = 7)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processData(self, data):
		# Used in processSourceTime().
		self.mRows = self.extractHtml(data, [HtmlTableCell(class_ = Provider._AttributeContainer), HtmlTable(index = 1), HtmlTableBody(optional = True, recursive = False), HtmlTableRow(recursive = False)])
		return data

	def processOffset(self, data, items):
		try:
			next = False
			pages = self.extractHtml(data, [HtmlTableCell(class_ = Provider._AttributeContainer), HtmlTable(index = 0), HtmlLink()])
			if pages:
				for page in pages:
					if Regex.match(data = page.text, expression = Provider._ExpressionNext):
						next = True
						break
			if not next: return ProviderHtml.Skip
		except: self.logError()

	def processLink(self, value, item, details = None, entry = None):
		# Resolving the link returns the magnet.
		# Requesting too many links concurrently causes Demonoid's server to fail and not return the magnet.
		# In such a case, try again, but use a semaphore to limit the number of concurrent connections.
		# Always try to get the magnet without a semaphore, otherwise locking for multiple links can take very long.
		if value:
			value = Networker.linkJoin(self.linkCurrent(), value)

			# First try without locking.
			magnet = Networker().requestLink(link = value, redirect = False) # If redirect is True, the request fails saying that there is no adapter for magnet links.
			if not Networker.linkIsMagnet(magnet):

				# Second try with lenient locking.
				try:
					Provider._Lock1.acquire()
					magnet = Networker().requestLink(link = value, redirect = False)
				finally: Provider._Lock1.release()

				if not Networker.linkIsMagnet(magnet):
					# Third try with strict locking.
					try:
						Provider._Lock2.acquire()
						magnet = Networker().requestLink(link = value, redirect = False)
					finally: Provider._Lock2.release()

					if not Networker.linkIsMagnet(magnet): magnet = None # If it fails again, bad luck, skip the file.

			if Networker.linkIsMagnet(magnet): value = magnet
			else: value = None

		return value

	def processSourceTime(self, value, item, details = None, entry = None):
		# Find the row containing the link.
		# Then iterate backwards over the rows until the first row containing a date.
		if value:
			for i in range(len(self.mRows)):
				if value in str(self.mRows[i]):
					for j in range(i, -1, -1):
						time = self.extractHtml(self.mRows[j], [HtmlTableCell(class_ = Provider._AttributeTime, extract = [Html.ParseText, Provider._ExpressionTime])])
						if time: return time
		return None

	def processSourceApproval(self, value, item, details = None, entry = None):
		result = ProviderHtml.ApprovalDefault
		try: result += ((1 - result) * (float(value) / Provider._LimitApproval))
		except: pass
		return result
