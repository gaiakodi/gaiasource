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

from lib.providers.core.html import ProviderHtml, Html, HtmlBody, HtmlScript, HtmlResultsList, HtmlLink, HtmlDiv, HtmlSpan
from lib.modules.tools import Regex, JavaScript
from lib.modules.network import Networker

class Provider(ProviderHtml):

	# All domains, except the .in domain, have their magnet links obfuscated by JavaScript.
	# Not only does this require additional files to be requested, but it can easily take 5 seconds for eaach JS snippet to be parsed and evaluated.
	# Hence, place the .in domain first, which has no obfuscation and is therefore faster.
	_Link					= ['https://elitetorrent.nz', 'https://elitetorrent.in', 'https://elitetorrent.com', 'https://elitetorrent.to', 'https://elitetorrent.tv', 'https://elitetorrent.io', 'https://elitetorrent.nl', 'https://elitetorrent.xyz', 'https://elitetorrent.one']
	_Unblock				= {ProviderHtml.UnblockFormat2 : 'elitetorrent', ProviderHtml.UnblockFormat3 : 'elitetorrent'}

	_Path					= 'page/%s/'

	_ParameterQuery			= 's'

	_AttributeContent		= 'principal'
	_AttributeList			= 'miniboxs'
	_AttributeLinks			= 'ficha_descarga_opciones'
	_AttributeDetails		= 'capa-fichadescarga'
	_AttributeDescription	= 'secc-ppal'
	_AttributePeers			= 'infotorrent'
	_AttributePages			= 'paginacion'
	_AttributePage			= 'pagina'

	_ExpressionName			= r'(.*?)(?:\(.*|$)'
	_ExpressionSize			= r'tamaño\s*:*\s*(.*)'
	_ExpressionTime			= r'fecha\s*:*\s*(.*)'
	_ExpressionFormat		= r'formato\s*:*\s*(.*)'
	_ExpressionRelease		= r'calidad\s*:*\s*(.*)'
	_ExpressionAudio		= r'idioma\s*:*\s*(.*)'
	_ExpressionSubtitle		= r'subtitulo\s*:*\s*(.*)'
	_ExpressionSeeds		= r'semillas\s*:*\s*(.*?)[\s|]'
	_ExpressionLeeches		= r'clientes\s*:*\s*(.*?)[\s|]'
	_ExpressionExtra		= r'^([\d\s\-]+)$'
	_ExpressionOriginal		= r'^(\s*vos[a-z]?)$'
	_ExpressionScript		= r'(lazy\/js\/.*?\.js)'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name							= 'EliteTorrent',
			description						= '{name} is less-known open {container} site from Spain. The site contains results in various languages, but most of them are in Spanish. {name} requests subpages in order to extract the magnet link, which substantially increases scraping time. In addition, most {name} domains obfuscate magnet links with JavaScript code, which has to be downloaded separately and executed in order to extract the link. This process can take very long, especially on slower devices, and {name} should therefore only be used if absolutely necessary.',
			rank							= 2,
			performance						= ProviderHtml.PerformanceBad,
			status							= ProviderHtml.StatusImpaired,

			link							= Provider._Link,
			unblock							= Provider._Unblock,

			offsetStart						= 1,
			offsetIncrease					= 1,

			formatEncode					= ProviderHtml.FormatEncodePlus,

			queryYear						= False, # Does not support searching by year.
			queryEpisode					= [
												'%s %sx%s' % (ProviderHtml.TermTitleShow, ProviderHtml.TermSeason, ProviderHtml.TermEpisode), # Does not support the default SxxEyy format.
												'%s %sx%s' % (ProviderHtml.TermTitleShow, ProviderHtml.TermSeason, ProviderHtml.TermEpisodeZero), # Some episode numbers have a leading 0.
											],

			searchQuery						= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : Provider._Path % ProviderHtml.TermOffset,
												ProviderHtml.RequestData : {
													Provider._ParameterQuery : ProviderHtml.TermQuery,
												},
											},
			searchConcurrency				= True, # Since the scripts might be requested in processLink().

			extractOptimizeData				= HtmlDiv(id_ = Provider._AttributeContent), # To detect the last page in processOffset().
			extractOptimizeDetails			= HtmlBody(), # Extract the entire body, since the JS script link might need to be extracted in processLink().
			extractList						= [HtmlResultsList(class_ = Provider._AttributeList)],
			extractDetails					= [HtmlLink(extract = Html.AttributeHref)],
			extractLink						= [ProviderHtml.Details, HtmlDiv(id_ = Provider._AttributeContent), HtmlDiv(class_ = Provider._AttributeLinks), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
			extractFileSize					= [ProviderHtml.Details, HtmlDiv(id_ = Provider._AttributeContent), HtmlDiv(id_ = Provider._AttributeDetails), HtmlDiv(class_ = Provider._AttributeDescription, extract = [Html.ParseTextNested, Provider._ExpressionSize])],
			extractSourceTime				= [ProviderHtml.Details, HtmlDiv(id_ = Provider._AttributeContent), HtmlDiv(id_ = Provider._AttributeDetails), HtmlDiv(class_ = Provider._AttributeDescription, extract = [Html.ParseTextNested, Provider._ExpressionTime])],
			extractSourceSeeds				= [ProviderHtml.Details, HtmlDiv(id_ = Provider._AttributeContent), HtmlDiv(id_ = Provider._AttributeDetails), HtmlDiv(class_ = Provider._AttributePeers, extract = [Html.ParseTextNested, Provider._ExpressionSeeds])],
			extractSourceLeeches			= [ProviderHtml.Details, HtmlDiv(id_ = Provider._AttributeContent), HtmlDiv(id_ = Provider._AttributeDetails), HtmlDiv(class_ = Provider._AttributePeers, extract = [Html.ParseTextNested, Provider._ExpressionLeeches])],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processOffset(self, data, items):
		try:
			last = self.extractHtml(data, [HtmlDiv(class_ = Provider._AttributePages), Html(class_ = Provider._AttributePage, index = -1, extract = Html.ParseTag)])
			if last and not last == Html.TagLink: return ProviderHtml.Skip
		except: self.logError()

	def processBefore(self, item):
		try:
			# Validate to only retrieve sub-pages that are valid.
			name = self.extractHtml(item, [HtmlLink(extract = Html.AttributeTitle)])
			if name:
				name = Regex.extract(data = name, expression = Provider._ExpressionName)
				if not self.searchValid(data = name, validateShow = False): return ProviderHtml.Skip
		except: self.logError()

	def processLink(self, value, item, details = None, entry = None):
		if details and not value:
			script = self.extractHtml(details, [HtmlScript(src_ = Provider._ExpressionScript, extract = Html.AttributeSrc)])
			if script:
				if not Networker.linkIs(script): script = self.linkCurrent(path = script)
				script = self.requestText(link = script)
				if script:
					code = '\
						var GAIA_RESULT = "";\
						\
						function GAIA_JQUERY()\
						{\
							this.length = 1;\
							this.click = function(code){ code(new GAIA_EVENT()); };\
						};\
						\
						function GAIA_EVENT()\
						{\
							this.preventDefault = function(){};\
						};\
						\
						function GAIA_WINDOW()\
						{\
							this.open = function(result){ GAIA_RESULT = result; };\
						};\
						var window = new GAIA_WINDOW();\
						\
						function setInterval(){};\
						function setTimeout(){};\
						function $(){ return new GAIA_JQUERY(); };\
						\
						try{%s}catch(e){};\
					' % script
					link = JavaScript.execute(code = code, variable = 'GAIA_RESULT')
					if Networker.linkIsMagnet(link): value = link
		return value

	def processFileExtra(self, value, item, details = None, entry = None):
		if details:
			result = []

			result.append(self.extractHtml(item, [HtmlLink(extract = Html.AttributeTitle)]))

			# On some pages the formatting is different.
			# Do not directly extract Html.ParseTextNested, since this will not replace <br> with a \n, making the regex extraction go to the end instead of the end of the line.
			# Manually replace <br>.
			# https://www.elitetorrent.nz/peliculas/dune/
			value = self.extractHtml(details, [HtmlDiv(id_ = Provider._AttributeContent), HtmlDiv(id_ = Provider._AttributeDetails), HtmlDiv(class_ = Provider._AttributeDescription)])
			value = self.parseHtml(str(value).replace('<br>', '\n').replace('<br/>', '\n'))
			value = self.extractHtml(value, [Html(extract = Html.ParseTextNested)])

			release = self.extractHtmlDecode(Regex.extract(data = value, expression = Provider._ExpressionRelease))
			if release and not Regex.match(data = release, expression = Provider._ExpressionExtra): result.append(release)

			result.append(self.extractHtmlDecode(Regex.extract(data = value, expression = Provider._ExpressionFormat)))

			language = Regex.extract(data = value, expression = Provider._ExpressionAudio, group = None, all = True)
			if language:
				language = self.extractHtmlDecode(language)
				language.insert(0, 'Audio')
				result.append(language)

			language = Regex.extract(data = value, expression = Provider._ExpressionSubtitle, group = None, all = True)
			if language:
				language = self.extractHtmlDecode(language)
				language.insert(0, 'Subtitulos')
				result.append(language)

			value = [i for i in result if i]

		return value
