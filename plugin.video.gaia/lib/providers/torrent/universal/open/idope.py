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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResultsUnordered, HtmlBody, HtmlLink, HtmlDiv, HtmlSpan, HtmlListUnordered, HtmlListItem, HtmlInput, HtmlBold, HtmlButton, HtmlForm
from lib.modules.tools import Regex

class Provider(ProviderHtml):

	_Link					= {
								ProviderHtml.Version1 : ['https://idope.se'], # Down: https://idope.cc
								ProviderHtml.Version2 : ['https://idope.pw', 'https://idope.xyz'],
							}
	_Details				= {
								ProviderHtml.Version2 : 'torrent-details/', # Important to have a slash at the end, otherwise a 404 error is returned.
							}
	_Mirror					= {
								ProviderHtml.Version1 : ['https://www.alltorrentsites.com/idope-proxy-list/', 'https://unblocksource.com/idope-proxy/'],
								ProviderHtml.Version2 : None,
							}
	_Unblock				= {
								ProviderHtml.Version1 : {ProviderHtml.UnblockFormat4 : 'idope'},
								ProviderHtml.Version2 : None,
							}
	_Path					= {
								ProviderHtml.Version1 : 'torrent-list/%s/?c=%s&p=%s',
								ProviderHtml.Version2 : 'query/%s/page/%s', # Do not use /search-site/, since it cannot handle pages. Even though it is a GET URL, POST parameters are still needed.
							}

	_CategoryMovie			= {
								ProviderHtml.Version1 : ['1', '2'], # 1 = Movies, 2 = Videos
								ProviderHtml.Version2 : ['movies', 'anime'],
							}
	_CategoryShow			= {
								ProviderHtml.Version1 : ['2', '3'], # 3 = TV, 2 = Videos
								ProviderHtml.Version2 : ['tv', 'anime'],
							}

	_AttributeMain			= 'showdivchild'
	_AttributeTree			= 'options-wthree'
	_AttributeResults		= 'div2'
	_AttributeResultsChild	= 'div2child'
	_AttributeResult		= 'resultdiv'
	_AttributeTop			= 'resultdivtop'
	_AttributeBottom		= 'resultdivbotton' # Incorrect spelling.
	_AttributeName			= 'resultdivtopname'
	_AttributeSize			= 'resultdivbottonlength'
	_AttributeTime			= 'resultdivbottontime'
	_AttributeSeeds			= 'resultdivbottonseed'
	_AttributeFile			= 'resultfile'
	_AttributeHash			= 'hideinfohash'
	_AttributePages			= 'div3'
	_AttributeNext			= 'next'

	_AttributeId			= 'id'
	_AttributeQuery			= 'q'
	_AttributeTree			= 'options-wthree'
	_AttributeBar			= 'seedbar'
	_AttributeColumn		= 'column'

	_ExpressionHash			= '(%s*)' % _AttributeHash
	_ExpressionPage			= '(/page/\d)'
	_ExpressionNext			= '(next)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()
		if version == ProviderHtml.Version1:
			formatEncode				= ProviderHtml.FormatEncodeQuote
			searchQuery					= Provider._Path[version] % (ProviderHtml.TermQuery, ProviderHtml.TermCategory, ProviderHtml.TermOffset)
			searchCategoryMovie			= ','.join(Provider._CategoryMovie[version])
			searchCategoryShow			= ','.join(Provider._CategoryShow[version])

			# iDope returns different HTML on an arbitrary basis, even between requesting sequential pages.
			# This is probably to block scrapers.
			# Sometimes: <div id="div2"> / <div id="div2child"> / <div  class="resultdiv">
			# Othertimes: <div id="div2"> / <a href="/torrent/.../"> / <div  class="resultdiv">
			# Do not extractOptimizeData, since the class is not always added to the div.
			extractList					= [HtmlDiv(id_ = Provider._AttributeResults), HtmlLink(), HtmlDiv(class_ = Provider._AttributeResult)]
			extractDetails				= None
			extractLink					= None
			extractFileName				= [HtmlDiv(class_ = Provider._AttributeTop), HtmlDiv(class_ = Provider._AttributeName)]
			extractHash					= [HtmlDiv(class_ = Provider._AttributeBottom), HtmlDiv(id_ = Provider._ExpressionHash)] # Two divs with class hideinfohash, so check the ID instead.
			extractFileSize				= [HtmlDiv(class_ = Provider._AttributeBottom), HtmlDiv(class_ = Provider._AttributeSize)]
			extractReleaseUploader		= None
			extractSourceTimeInexact	= [HtmlDiv(class_ = Provider._AttributeBottom), HtmlDiv(class_ = Provider._AttributeTime)]
			extractSourceSeeds			= [HtmlDiv(class_ = Provider._AttributeBottom), HtmlDiv(class_ = Provider._AttributeSeeds)]
			extractSourceLeeches		= None
		elif version == ProviderHtml.Version2:
			formatEncode				= ProviderHtml.FormatEncodeNone
			searchQuery					= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodPost,
											ProviderHtml.RequestPath : Provider._Path[version] % (ProviderHtml.TermQuery, ProviderHtml.TermOffset),
											ProviderHtml.RequestData : {
												Provider._AttributeQuery : ProviderHtml.TermQuery,
											},
										}
			searchCategoryMovie			= None
			searchCategoryShow			= None

			extractList					= [HtmlDiv(class_ = Provider._AttributeTree), HtmlResultsUnordered()]
			extractDetails				= [HtmlInput(name_ = Provider._AttributeId, extract = Html.AttributeValue)]
			extractLink					= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeBar), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)]
			extractFileName				= [HtmlButton(extract = Html.AttributeTitle)]
			extractHash					= None
			extractFileSize				= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeBar), HtmlDiv(class_ = Provider._AttributeColumn, index = 2), HtmlBold()]
			extractReleaseUploader		= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeBar), HtmlDiv(class_ = Provider._AttributeColumn, index = 5), HtmlBold()]
			extractSourceTimeInexact	= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeBar), HtmlDiv(class_ = Provider._AttributeColumn, index = 3), HtmlBold()]
			extractSourceSeeds			= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeBar), HtmlDiv(class_ = Provider._AttributeColumn, index = 0), HtmlBold()]
			extractSourceLeeches		= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeBar), HtmlDiv(class_ = Provider._AttributeColumn, index = 1), HtmlBold()]

		ProviderHtml.initialize(self,
			name						= 'iDope',
			description					= '{name} is a less know {container} site. {name} has multiple structural problems, outdated metadata, and strong Cloudflare protection that might not be bypassable and cause scraping to fail. Version %s must request subpages to extract additional information, which substantially increases scraping time.' % ProviderHtml.Version2,
			rank						= 3,
			performance					= ProviderHtml.PerformanceBad,
			status						= ProviderHtml.StatusCloudflare, # Cloudflare.

			link						= Provider._Link[version],
			mirror						= Provider._Mirror[version],
			unblock						= Provider._Unblock[version],

			customVersion				= 2,

			supportMovie				= True,
			supportShow					= True,
			supportPack					= True,

			offsetStart					= 1,
			offsetIncrease				= 1,

			formatEncode				= formatEncode,

			searchQuery					= searchQuery,
			searchCategoryMovie			= searchCategoryMovie,
			searchCategoryShow			= searchCategoryShow,

			extractOptimizeData			= HtmlBody(),
			extractOptimizeDetails		= HtmlDiv(class_ = Provider._AttributeTree),
			extractList					= extractList,
			extractDetails				= extractDetails,
			extractLink					= extractLink,
			extractHash					= extractHash,
			extractFileName				= extractFileName,
			extractFileSize				= extractFileSize,
			extractReleaseUploader		= extractReleaseUploader,
			extractSourceTimeInexact	= extractSourceTimeInexact,
			extractSourceSeeds			= extractSourceSeeds,
			extractSourceLeeches		= extractSourceLeeches,
		)

		if version == ProviderHtml.Version1: self.extractList = (lambda data: self.extractListSpecial(data = data))

	##############################################################################
	# EXTRACT
	##############################################################################

	def extractListSpecial(self, data):
		try:
			if self.extractHtml(item = data, keys = [HtmlDiv(id_ = Provider._AttributeResultsChild)]):
				return self.extractHtml(item = data, keys = [HtmlDiv(id_ = Provider._AttributeResults), HtmlDiv(id_ = Provider._AttributeResultsChild), HtmlDiv(class_ = Provider._AttributeResult)])
			else:
				items = self.extractHtml(item = data, keys = [HtmlDiv(id_ = Provider._AttributeResults), HtmlLink()])

				# Extract the hash and insert it as a new HTML element.
				if items:
					for i in range(len(items)):
						item = items[i]
						hash = Regex.extract(data = item[Html.AttributeHref], expression = '.+\/(.+)\/')
						file = self.extractHtml(item = item, keys = [HtmlDiv(class_ = Provider._AttributeFile)])[0]
						element = data.new_tag(Html.TagDiv, id = Provider._AttributeHash + str(i))
						element.string = hash
						file.append(element)

				return items
		except: self.logError()

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			if self.customVersion1():
				next = self.extractHtml(data, [HtmlDiv(id_ = Provider._AttributePages), HtmlDiv(id_ = Provider._AttributeNext)])
				if not next: return ProviderHtml.Skip
			else:
				next = self.extractHtml(data, [HtmlForm(action_ = Provider._ExpressionPage, index = -1), HtmlButton(index = -1, extract = Html.ParseText)])
				if not next or not Regex.match(data = next, expression = Provider._ExpressionNext): return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		version = self.customVersion()
		if version == ProviderHtml.Version2:
			if self.parameterMediaShow(): categories = Provider._CategoryShow[version]
			else: categories = Provider._CategoryMovie[version]

			category = self.extractHtml(item, [HtmlDiv(class_ = Provider._AttributeBar), HtmlSpan(index = -1, extract = Html.ParseText)]).lower()
			found = False
			for i in categories:
				if i in category:
					found = True
					break

			if not found: return ProviderHtml.Skip
		return None

	def processDetails(self, value, item):
		version = self.customVersion()
		if version == ProviderHtml.Version1:
			return ProviderHtml.processDetails(self, value = value, item = item)
		else:
			return {
						ProviderHtml.RequestMethod : ProviderHtml.RequestMethodPost,
						ProviderHtml.RequestPath : Provider._Details[version],
						ProviderHtml.RequestData : {Provider._AttributeId : value},
					}
