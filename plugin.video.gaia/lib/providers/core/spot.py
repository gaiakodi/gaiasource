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

'''

	Spotweb is a community fork of Spotnet.
		https://en.wikipedia.org/wiki/Spotnet
		https://github.com/spotweb/spotweb
		https://github.com/spotnet/spotnet
		https://www.spot-net.nl/

	Spotnet/Spotweb has added support for the Newznab API:
		https://github.com/spotweb/spotweb/wiki/Spotweb-als-Newznab-Provider

	However, there are many problems with the Spotnet API:
		1. The GET query format is the same, but the returned JSON is different.
		2. Many parameters (eg: extended=1) does not work.
		3. Searching by IMDb/TVDb ID does not work.
		4. Some type searches only work on some sites. For instance "t=movie&q=xxx" works on some sites, but other sites only work with "t=search&q=xxx".
		5. Some sites (eg: NZBStars) have major problems with the API. NZBStars throws JS error popups when querying the API in the browser, but works with CURL. Even with CURL, queries do not work, just returning random results.

'''

from lib.providers.core.newz import ProviderSpot
from lib.providers.core.usenet import ProviderUsenetHtml
from lib.providers.core.html import Html, HtmlResults, HtmlResult, HtmlLink
from lib.modules.tools import Tools

class ProviderSpotJson(ProviderSpot):

	_LimitCompletion		= 100

	_AttributeId			= 'ID'
	_AttributeName			= 'name'
	_AttributeSize			= 'size'
	_AttributeTime			= 'adddate'
	_AttributeUploader		= 'fromname'
	_AttributeCompletion	= 'completion'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self, **kwargs):
		ProviderSpot.initialize(self,
			performance				= ProviderSpot.PerformanceExcellent,

			customIncomplete		= True,

			supportZero				= False, # No links are returned with "q=Title&season=1&ep=0", but episodes are returned with "q=Title&season=1".
			supportOffset			= False,
			supportAttributes		= False,

			extractFileName			= ProviderSpotJson._AttributeName,
			extractFileSize			= ProviderSpotJson._AttributeSize,
			extractReleaseUploader	= ProviderSpotJson._AttributeUploader,
			extractSourceTime		= ProviderSpotJson._AttributeTime,

			**kwargs
		)

	##############################################################################
	# EXTRACT
	##############################################################################

	def extractLink(self, item, details = None, entry = None):
		id = self.extractIdUniversal(item = item, details = details)
		if id: return self._linkCreate(type = ProviderSpot._TypeDownload, id = id)
		return None

	def extractIdUniversal(self, item, details = None, entry = None):
		try: return item[ProviderSpotJson._AttributeGuid]
		except:
			try: return item[ProviderSpotJson._AttributeId]
			except: pass
		return None

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		if self.customIncomplete():
			try:
				completion = item[ProviderSpotJson._AttributeCompletion]
				if Tools.isInteger(completion) and completion < ProviderSpotJson._LimitCompletion: return ProviderJson.Skip
			except: pass


# Some Spotweb APIs do not work (properly). Search the HTML instead.
class ProviderSpotHtml(ProviderUsenetHtml):

	_ParameterDirection	= 'direction'
	_ParameterNext		= 'next'
	_ParameterPage		= 'pagenr'
	_ParameterValue		= 'search[value]'
	_ParameterTree		= 'search[tree]'
	_ParameterTitle		= 'Title:%%3D:%s'
	_ParameterAge		= 'date:%%3E:-%d+day'
	_ParameterSize		= 'filesize:%%3E:%d'
	_ParameterSpam		= 'reportcount:%3C%3D:1'

	_CategoryMovie		= 'cat0_z0'
	_CategoryShow		= 'cat0_z1'

	_AttributeTable		= 'spots'
	_AttributeTitle		= 'title'
	_AttributeTime		= 'date'
	_AttributeSize		= 'filesize'
	_AttributeUploader	= 'poster'
	_AttributeLink		= 'nzb'

	_ExpressionId		= r'messageid=(.*?)(?:$|&)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self,
		performance	= ProviderUsenetHtml.PerformanceGood,

		**kwargs
	):
		query = [ProviderSpotHtml._ParameterTitle % ProviderUsenetHtml.TermQuery]
		age = self.customTime(days = True)
		if age: query.append(ProviderSpotHtml._ParameterAge % age)
		size = self.customSize(bytes = True)
		if size: query.append(ProviderSpotHtml._ParameterSize % size)
		if self.customSpam(): query.append(ProviderSpotHtml._ParameterSpam)

		ProviderUsenetHtml.initialize(self,
			supportMovie			= True,
			supportShow				= True,
			supportPack				= True,

			customSpam				= True,

			offsetStart				= 0,
			offsetIncrease			= 1,

			formatEncode			= ProviderUsenetHtml.FormatEncodePlus,

			searchQuery				= {
										ProviderUsenetHtml.RequestMethod : ProviderUsenetHtml.RequestMethodGet,
										ProviderUsenetHtml.RequestData : {
											ProviderSpotHtml._ParameterDirection	: ProviderSpotHtml._ParameterNext,
											ProviderSpotHtml._ParameterPage			: ProviderUsenetHtml.TermOffset,
											ProviderSpotHtml._ParameterTree			: ProviderUsenetHtml.TermCategory,
											ProviderSpotHtml._ParameterValue		: query,
										},
									},
			searchCategoryMovie		= ProviderSpotHtml._CategoryMovie,
			searchCategoryShow		= ProviderSpotHtml._CategoryShow,

			extractList				= [HtmlResults(class_ = ProviderSpotHtml._AttributeTable)],
			extractLink				= [HtmlResult(class_ = ProviderSpotHtml._AttributeLink), HtmlLink(extract = Html.AttributeHref)],
			extractIdUniversal		= [HtmlResult(class_ = ProviderSpotHtml._AttributeLink), HtmlLink(extract = [Html.AttributeHref, ProviderSpotHtml._ExpressionId, Html.ParseDecode])],
			extractFileName			= [HtmlResult(class_ = ProviderSpotHtml._AttributeTitle), HtmlLink()],
			extractFileSize			= [HtmlResult(class_ = ProviderSpotHtml._AttributeSize)],
			extractSourceTime		= [HtmlResult(class_ = ProviderSpotHtml._AttributeTime, extract = Html.AttributeTitle)],
			extractReleaseUploader	= [HtmlResult(class_ = ProviderSpotHtml._AttributeUploader)],

			**kwargs
		)
