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

from lib.providers.core.web import ProviderWeb
from lib.modules.tools import Tools, Regex, Converter
from lib.modules.network import Networker
from lib.modules.parser import Parser, Strainer, Navigable

class Html(object):

	ResultTable				= 'table'			# Extract table/tr.
	ResultList				= 'list'			# Extract ul/li.
	ResultListOrdered		= 'listordered'		# Extract ol/li.
	ResultListUnordered		= 'listunordered'	# Extract ul/li.
	ResultDiv				= 'div'				# Extract div/div.

	ParseTag				= 'tag'				# Find element by tag name (BeautifulSoup).
	ParseAttribute			= 'attribute'		# Find element by attribute (BeautifulSoup).
	ParseRecursive			= 'recursive'		# Find elements recursively (BeautifulSoup).
	ParseString				= 'string'			# Find element by string or regular expression object (BeautifulSoup).
	ParseCode				= 'code'			# Extract the HTML code (elements and text).
	ParseText				= 'text'			# Extract inner text including nested elements (BeautifulSoup).
	ParseTextNested			= 'textnested'		# Extract inner text including nested elements. Same as ParseText.
	ParseTextUnnested		= 'textunnested'	# Extract inner text excluding nested elements.
	ParseExpression			= 'expression'		# Find element or extract data by regular expression string. Will be converted to ParseString.
	ParseExtract			= 'extract'			# Extract specific data from element.
	ParseOptional			= 'optional'		# If extraction fails, ignore it and continue with parent/ancestor (eg: tbody that might not always be there).
	ParseIndex				= 'index'			# Extract element at index from list. Can be a negative integer to retrieve from the back of the list.
	ParseStart				= 'start'			# Start index of sub-list to extract from list.
	ParseEnd				= 'end'				# End index of sub-list to extract from list.
	ParseSkip				= 'skip'			# Skip every nth element. Useful if eg every other row in the table is a row border and should not be processed.
	ParseCombine			= 'combine'			# Combine n number of elements into one. Useful if a result's data is split across multiple table rows.
	ParseDecode				= 'decode'			# URL decode the data.
	ParseEncode				= 'encode'			# URL encode the data.
	ParseStrip				= 'strip'			# Strip whitespaces from the sides.
	ParseSplitSpace			= 'splitspace'		# Split string by spaces.
	ParseSplitComma			= 'splitcomma'		# Split string by comma.
	ParseSplitBar			= 'splitbar'		# Split string by vertical bar/slash.
	ParseRemoveSpace		= 'removespace'		# Remove all spaces.
	ParseRemoveComma		= 'removecomma'		# Remove all commas.
	ParseInteger			= 'interger'		# Convert to integer.
	ParseFloat				= 'float'			# Convert to float.

	TagHead					= 'head'
	TagBody					= 'body'
	TagScript				= 'script'
	TagTitle				= 'title'
	TagInput				= 'input'
	TagButton				= 'button'
	TagForm					= 'form'
	TagLink					= 'a'
	TagDiv					= 'div'
	TagSpan					= 'span'
	TagNav					= 'nav'
	TagParagraph			= 'p'
	TagImage				= 'img'
	TagFont					= 'font'
	TagBold					= 'b'
	TagItalic				= 'i'
	TagUnderlined			= 'u'
	TagStrong				= 'strong'
	TagSmall				= 'small'
	TagLabel				= 'label'
	TagHeading1				= 'h1'
	TagHeading2				= 'h2'
	TagHeading3				= 'h3'
	TagHeading4				= 'h4'
	TagHeading5				= 'h5'
	TagMain					= 'main'
	TagArticle				= 'article'
	TagFieldSet				= 'fieldset'
	TagTable				= 'table'
	TagTableHead			= 'thead'
	TagTableBody			= 'tbody'
	TagTableHeader			= 'th'
	TagTableRow				= 'tr'
	TagTableCell			= 'td'
	TagListOrdered			= 'ol'
	TagListUnordered		= 'ul'
	TagListItem				= 'li'
	TagDescriptionList		= 'dl'
	TagDescriptionName		= 'dt'
	TagDescriptionValue		= 'dd'
	TagKeyboardInput		= 'kbd'

	AttributeId				= 'id'
	AttributeClass			= 'class'
	AttributeTitle			= 'title'
	AttributeName			= 'name'
	AttributeValue			= 'value'
	AttributeHref			= 'href'
	AttributeRel			= 'rel'
	AttributeSrc			= 'src'
	AttributeAction			= 'action'
	AttributeAlt			= 'alt'

	AttributeData			= 'data-%s'
	AttributeDataTimestamp	= AttributeData % 'timestamp'

	AttributeAria			= 'aria-%s'
	AttributeAriaLabel		= AttributeAria % 'label'

	# Parameters starting/ending with an _ are always considered to be HTML attributes.
	def __init__(self, **kwargs):
		self.mData = {}
		attribute = {}
		for key, value in dict(**kwargs).items():
			if key.startswith('_') or key.endswith('_'): attribute[key.strip('_')] = value
			else: self.mData[key] = value
		if attribute: self.mData[Html.ParseAttribute] = attribute

	def __getitem__(self, key):
		return self.mData[key]

	def __json__(self):
		return Converter.jsonTo(self.mData)

	def data(self):
		return self.mData


# Any tag type.
class HtmlAny(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = True
		Html.__init__(self, **kwargs)


class HtmlHead(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagHead
		Html.__init__(self, **kwargs)


class HtmlBody(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagBody
		Html.__init__(self, **kwargs)


class HtmlScript(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagScript
		Html.__init__(self, **kwargs)


class HtmlTitle(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagTitle
		Html.__init__(self, **kwargs)


class HtmlInput(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagInput
		Html.__init__(self, **kwargs)


class HtmlButton(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagButton
		Html.__init__(self, **kwargs)


class HtmlForm(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagForm
		Html.__init__(self, **kwargs)


class HtmlTable(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagTable
		Html.__init__(self, **kwargs)


class HtmlTableBody(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagTableBody
		Html.__init__(self, **kwargs)


class HtmlTableRow(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagTableRow
		Html.__init__(self, **kwargs)


class HtmlTableCell(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagTableCell
		Html.__init__(self, **kwargs)


class HtmlListOrdered(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagListOrdered
		Html.__init__(self, **kwargs)


class HtmlListUnordered(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagListUnordered
		Html.__init__(self, **kwargs)


class HtmlListItem(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagListItem
		Html.__init__(self, **kwargs)


class HtmlDescriptionList(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagDescriptionList
		Html.__init__(self, **kwargs)


class HtmlDescriptionName(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagDescriptionName
		Html.__init__(self, **kwargs)


class HtmlDescriptionValue(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagDescriptionValue
		Html.__init__(self, **kwargs)


class HtmlLink(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagLink
		Html.__init__(self, **kwargs)


class HtmlDiv(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagDiv
		Html.__init__(self, **kwargs)


class HtmlSpan(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagSpan
		Html.__init__(self, **kwargs)


class HtmlNav(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagNav
		Html.__init__(self, **kwargs)


class HtmlParagraph(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagParagraph
		Html.__init__(self, **kwargs)


class HtmlImage(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagImage
		Html.__init__(self, **kwargs)


class HtmlFont(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagFont
		Html.__init__(self, **kwargs)


class HtmlBold(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagBold
		Html.__init__(self, **kwargs)


class HtmlItalic(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagItalic
		Html.__init__(self, **kwargs)


class HtmlUnderlined(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagUnderlined
		Html.__init__(self, **kwargs)


class HtmlStrong(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagStrong
		Html.__init__(self, **kwargs)


class HtmlSmall(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagSmall
		Html.__init__(self, **kwargs)


class HtmlLabel(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagLabel
		Html.__init__(self, **kwargs)


class HtmlHeading1(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagHeading1
		Html.__init__(self, **kwargs)


class HtmlHeading2(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagHeading2
		Html.__init__(self, **kwargs)


class HtmlHeading3(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagHeading3
		Html.__init__(self, **kwargs)


class HtmlHeading4(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagHeading4
		Html.__init__(self, **kwargs)


class HtmlHeading5(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagHeading5
		Html.__init__(self, **kwargs)


class HtmlMain(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagMain
		Html.__init__(self, **kwargs)


class HtmlArticle(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagArticle
		Html.__init__(self, **kwargs)


class HtmlFieldSet(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagFieldSet
		Html.__init__(self, **kwargs)


class HtmlKeyboardInput(Html):
	def __init__(self, **kwargs):
		kwargs[Html.ParseTag] = Html.TagKeyboardInput
		Html.__init__(self, **kwargs)


# Shorthand class to extract from the HTML body: table -> optional table body -> table rows.
class HtmlResults(Html):
	def __init__(self, type = Html.ResultTable, start = None, end = None, skip = None, combine = None, **kwargs):
		if type == Html.ResultTable: self.mData = [HtmlTable(**kwargs), HtmlTableBody(optional = True, recursive = False), HtmlTableRow(recursive = False, start = start, end = end, skip = skip, combine = combine)]
		elif type == Html.ResultList or type == Html.ResultListUnordered: self.mData = [HtmlListUnordered(**kwargs), HtmlListItem(recursive = False, start = start, end = end, skip = skip, combine = combine)]
		elif type == Html.ResultListOrdered: self.mData = [HtmlListOrdered(**kwargs), HtmlListItem(recursive = False, start = start, end = end, skip = skip, combine = combine)]
		elif type == Html.ResultDiv: self.mData = [HtmlDiv(**kwargs), HtmlDiv(recursive = False, start = start, end = end, skip = skip, combine = combine)]

class HtmlResultsTable(HtmlResults):
	def __init__(self, **kwargs):
		HtmlResults.__init__(self, type = Html.ResultTable, **kwargs)

class HtmlResultsList(HtmlResults):
	def __init__(self, **kwargs):
		HtmlResults.__init__(self, type = Html.ResultList, **kwargs)

class HtmlResultsOrdered(HtmlResults):
	def __init__(self, **kwargs):
		HtmlResults.__init__(self, type = Html.ResultListOrdered, **kwargs)

class HtmlResultsUnordered(HtmlResults):
	def __init__(self, **kwargs):
		HtmlResults.__init__(self, type = Html.ResultListUnordered, **kwargs)

class HtmlResultsDiv(HtmlResults):
	def __init__(self, **kwargs):
		HtmlResults.__init__(self, type = Html.ResultDiv, **kwargs)

# Shorthand class to extract from the results table: table cell.
class HtmlResult(Html):
	def __init__(self, type = Html.ResultTable, **kwargs):
		if not Html.ParseIndex in kwargs: kwargs[Html.ParseIndex] = 0
		if type == Html.ResultTable: self.mData = [HtmlTableCell(recursive = False, **kwargs)]
		elif type == Html.ResultList or type == Html.ResultListOrdered or type == Html.ResultListUnordered: self.mData = [HtmlListItem(recursive = False, **kwargs)]
		elif type == Html.ResultDiv: self.mData = [HtmlDiv(recursive = False, **kwargs)]

class HtmlResultTable(HtmlResult):
	def __init__(self, **kwargs):
		HtmlResult.__init__(self, type = Html.ResultTable, **kwargs)

class HtmlResultDiv(HtmlResult):
	def __init__(self, **kwargs):
		HtmlResult.__init__(self, type = Html.ResultDiv, **kwargs)


class ProviderHtml(ProviderWeb):

	# https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser
	#	ParserXml: Very fast (implemented in C). Cannot handle HTML mistakes (eg: unclosed tags). Does not work (maybe because the library is updated for Python 3), throwing an "RuntimeError: restricted attribute" error.
	#	ParserHtml: Fast (implemented in C). Can handle many HTML mistakes (eg: unclosed tags).
	#	ParserHtml5: Slow (implemented in Python). Can handle most HTML mistakes (eg: unclosed tags). Cannot use optimized extraction, making it even slower. Should only be used if none of the other parsers work.
	# HTML/HTML5 can handle unopened, unclosed, and incorrectly nested tags, which the default XML parser cannot. Eg: KickAssTorrents has unopened and unclosed tags.
	ParserXml		= Parser.ParserXml
	ParserHtml		= Parser.ParserHtml
	ParserHtml5		= Parser.ParserHtml5
	ParserDefault	= Parser.ParserHtml

	def __init__(self, **kwargs):
		ProviderWeb.__init__(self, **kwargs)

	def initialize(self,
		# Attributes can be:
		#	1. None:			Do not extract.
		#	2. String:			Extract a regular expression if the string contains round brackets. Otherwise the HTML tag name.
		#	3. Integer:			Extract a specific index from a list of elements.
		#	4. Dictionary:		Extract by various values.
		#						{'tag' : <tag name>, 'recursive' : <search decendents recursively - True by default>, 'string' : <search by string instead of tags>, 'expression' : <search by regular expression instead of tags>, 'extract' : <see below>, ... <any HTML attribute (eg: 'id' : 'table')> ...}
		#						If HTML attributes have the same name as the keys in the dictionary above (eg: tag="xyz"), the attributes can be passed as an additional dictionary.
		#						{'tag' : ..., 'recursive' : ..., 'attribute' : {...}}
		#	5. List:			Extract recursively where each value in the list is one of the types above.
		#
		# Extract:
		#	1. None or not provided:		Extract the inner HTML text.
		#	2. String:						Extract a regular expression if the string contains round brackets. If ParseText, extract the inner HTML text. Otherwise extract an HTML attribute.
		#	3. Integer:						Extract a specific index from a list of elements.
		#	4. Dictionary:					Extract a specific type (eg: {ParseAttribute : 'id'}).
		#	5. List of strings/integers:	Extract recursively by index and expression/attribute/text (eg: [2]['id'] extract the id attribute from the 3rd element, [1][None]/[1][ParseText] extract the inner text of the 2nd element).
		#	6. List of dictionaries:		Extract recursively by index/expression/attribute/text (eg: [{ParseIndex : 2}, {ParseAttribute : 'id'}] extract the id attribute from the 3rd element, [{ParseIndex : 1}, None]/{ParseIndex : 1}, ParseText] extract the inner text of the 2nd element).
		#	7. List of lists:				Just like linear lists, but extract multiple values.
		#
		# Notes:
		#	1. If ParseOptional is passed, it will try to extract it, but if not found, continue using the parent/ancestor. Is useful to extract <tbody> from a table that might not always be there.
		#	2. If ParseStart/ParseEnd is passed, a subset of the results are used. This is useful if a table has its first row as header and this row should be skipped.

		extractParser					= None, # Which HTML parser to use. Check the parse description for more details.

		# Specify a specific element to parse, instead of parsing the entire HTML document.
		# Only parsing a subset of elements is faster, especially if many subpages are requested.
		#	True: Use the extractList as reference point for the main page, and scan through the other extract parameters to find the reference point for subpages.
		#	False: Do not apply optimization, and therefore parse the entire document.
		#	Dictionary/Html: Specify a custom element as reference point.
		extractOptimizeData				= True,	# Optimize the extraction of the main page.
		extractOptimizeDetails			= True,	# Optimize the extraction of the details subpage.
		extractOptimizeEntries			= True,	# Optimize the extraction of the entries on the subpage.

		extractData						= None, # A regular expression which can be used to extract the HTML string if it is not returned as HTML data, but as part of some text.

		extractList						= None,	# The outer list/table containing the individual items.

		# Extract an full link or path from HTML that points to a subpage. The subpage is requested and passed into the extract functions.
		# Can be used to extract additional metadata from a sub-page for each item in extractList.
		# searchConcurrency will be set to True if it was not already set.
		# Will only be executed if the file name is valid.
		extractDetails					= None,

		# The details page sometimes contains multiple links/streams.
		# This parameter extracts a list of sub-entries from the details page (similar to the extractList parameter).
		extractEntries					= None,

		extractLink						= None,

		extractIdLocal					= None,
		extractIdUniversal				= None,
		extractIdCollection				= None,
		extractIdItem					= None,

		extractHash						= None,
		extractHashContainer			= None,
		extractHashContainerMd5			= None,
		extractHashContainerSha1		= None,
		extractHashContainerSha256		= None,
		extractHashContainerSha512		= None,
		extractHashFile					= None,
		extractHashFileMd5				= None,
		extractHashFileSha1				= None,
		extractHashFileSha256			= None,
		extractHashFileSha512			= None,
		extractHashOther				= None,
		extractHashOtherMd5				= None,
		extractHashOtherSha1			= None,
		extractHashOtherSha256			= None,
		extractHashOtherSha512			= None,

		extractVideoQuality				= None,
		extractVideoQualityInexact		= None,
		extractVideoResolution			= None,
		extractVideoResolutionInexact	= None,
		extractVideoWidth				= None,
		extractVideoWidthInexact		= None,
		extractVideoHeight				= None,
		extractVideoHeightInexact		= None,
		extractVideoAspect				= None,
		extractVideoAspectInexact		= None,
		extractVideoCodec				= None,
		extractVideoDepth				= None,
		extractVideoRange				= None,
		extractVideo3d					= None,

		extractAudioType				= None,
		extractAudioChannels			= None,
		extractAudioSystem				= None,
		extractAudioCodec				= None,
		extractAudioLanguage			= None,
		extractAudioLanguageInexact		= None,

		extractSubtitleType				= None,
		extractSubtitleLanguage			= None,
		extractSubtitleLanguageInexact	= None,

		extractReleaseType				= None,
		extractReleaseFormat			= None,
		extractReleaseEdition			= None,
		extractReleaseNetwork			= None,
		extractReleaseGroup				= None,
		extractReleaseUploader			= None,

		extractFileName					= None,
		extractFileNameInexact			= None,
		extractFileExtra				= None,
		extractFileSizeInexact			= None,
		extractFileSize					= None,
		extractFileContainer			= None,
		extractFilePack					= None,

		extractSourceType				= None,
		extractSourceSeeds				= None,
		extractSourceSeedsInexact		= None,
		extractSourceLeeches			= None,
		extractSourceLeechesInexact		= None,
		extractSourceTime				= None,
		extractSourceTimeInexact		= None,
		extractSourcePopularity			= None,
		extractSourceApproval			= None,
		extractSourcePublisher			= None,
		extractSourceHoster				= None,

		performance						= None,
		propagate						= True,
		**kwargs
	):
		# Reduce the performance for providers that use ParserHtml5.
		# ParserHtml5 is 3-5 times slower to parse HTML compared to ParserHtml.
		# Reduce their chances of being enabled during optimization.
		if extractParser == ProviderHtml.ParserHtml5:
			if performance: performance = max(ProviderWeb.PerformanceBad, performance - ProviderWeb.PerformanceStep)
			else: performance = ProviderWeb.PerformanceBad

		if propagate: ProviderWeb.initialize(self, performance = performance, **kwargs)

		self.mParser = ProviderHtml.ParserDefault if extractParser is None else extractParser
		self.mHtml = None
		self.mOptimizeData = None
		self.mOptimizeDetails = None
		self.mOptimizeEntries = None

		if extractOptimizeData:
			if extractOptimizeData is True:
				if extractList:
					if Tools.isArray(extractList): self.mOptimizeData = extractList[0]
					else: self.mOptimizeData = extractList
			else:
				self.mOptimizeData = extractOptimizeData
			try:
				self.mOptimizeData = self.mOptimizeData.data()
				if Tools.isArray(self.mOptimizeData):
					self.mOptimizeData = self.mOptimizeData[0]
					try: self.mOptimizeData = self.mOptimizeData.data()
					except: pass
			except: pass

		if extractOptimizeDetails:
			if extractOptimizeDetails is True:
				elements = []
				for key, value in locals().items():
					if key.startswith('extract') and Tools.isArray(value) and value[0] == ProviderWeb.Details:
						value = value[1]
						try: value = value.data()
						except: pass
						if Tools.isArray(value): value = value[0]
						elements.append(value)
				if len(elements) > 0:
					allow = True
					element = elements[0]
					try: element = element.data()
					except: pass
					for el in elements:
						try: el = el.data()
						except: pass
						if not el == element:
							self.log(self.id() + ': The details subpage contains different root elements for different extraction attributes and could therefore not be optimized. The "extractOptimizeDetails" parameter should be specified.')
							allow = False
							break
					if allow: self.mOptimizeDetails = element
			else:
				self.mOptimizeDetails = extractOptimizeDetails
			try:
				self.mOptimizeDetails = self.mOptimizeDetails.data()
				if Tools.isArray(self.mOptimizeDetails):
					self.mOptimizeDetails = self.mOptimizeDetails[0]
					try: self.mOptimizeDetails = self.mOptimizeDetails.data()
					except: pass
			except: pass

		if extractOptimizeEntries:
			if extractOptimizeEntries is True:
				elements = []
				for key, value in locals().items():
					if key.startswith('extract') and Tools.isArray(value) and value[0] == ProviderWeb.Entries:
						value = value[1]
						try: value = value.data()
						except: pass
						if Tools.isArray(value): value = value[0]
						elements.append(value)
				if len(elements) > 0:
					allow = True
					element = elements[0]
					try: element = element.data()
					except: pass
					for el in elements:
						try: el = el.data()
						except: pass
						if not el == element:
							self.log(self.id() + ': The entries subpage contains different root elements for different extraction attributes and could therefore not be optimized. The "extractOptimizeEntries" parameter should be specified.')
							allow = False
							break
					if allow: self.mOptimizeEntries = element
			else:
				self.mOptimizeEntries = extractOptimizeEntries
			try:
				self.mOptimizeEntries = self.mOptimizeEntries.data()
				if Tools.isArray(self.mOptimizeEntries):
					self.mOptimizeEntries = self.mOptimizeEntries[0]
					try: self.mOptimizeEntries = self.mOptimizeEntries.data()
					except: pass
			except: pass

		if extractData is None: self.extractData = (lambda data, details = False: self.extractHtmlData(data = data, details = details))
		else: self.extractData = (lambda data, details = False: self.extractHtmlData(data = Regex.extract(data = data, expression = extractData), details = details))

		if not extractList is None: self.extractList = (lambda data: self.extractHtml(item = data, keys = extractList))

		if not extractDetails is None:
			if self.searchConcurrency() is None: self.searchConcurrencySet(True)
			self.extractDetails = (lambda item: self.extractHtml(item = item, keys = extractDetails))

		if not extractEntries is None:
			if not extractEntries[0] == ProviderWeb.Details: extractEntries.insert(0, ProviderWeb.Details)
			self.extractEntries = (lambda item, details = None: self.extractHtml(item = item, details = details, keys = extractEntries))

		if not extractLink is None: self.extractLink = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractLink, extract = True))

		if not extractIdLocal is None: self.extractIdLocal = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractIdLocal, extract = True))
		if not extractIdUniversal is None: self.extractIdUniversal = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractIdUniversal, extract = True))
		if not extractIdCollection is None: self.extractIdCollection = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractIdCollection, extract = True))
		if not extractIdItem is None: self.extractIdItem = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractIdItem, extract = True))

		if not extractHash is None: self.extractHash = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHash, extract = True))
		else:
			if not extractHashContainer is None: self.extractHashContainer = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashContainer, extract = True))
			else:
				if not extractHashContainerMd5 is None: self.extractHashContainerMd5 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashContainerMd5, extract = True))
				if not extractHashContainerSha1 is None: self.extractHashContainerSha1 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashContainerSha1, extract = True))
				if not extractHashContainerSha256 is None: self.extractHashContainerSha256 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashContainerSha256, extract = True))
				if not extractHashContainerSha512 is None: self.extractHashContainerSha512 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashContainerSha512, extract = True))
			if not extractHashFile is None: self.extractHashFile = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashFile, extract = True))
			else:
				if not extractHashFileMd5 is None: self.extractHashFileMd5 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashFileMd5, extract = True))
				if not extractHashFileSha1 is None: self.extractHashFileSha1 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashFileSha1, extract = True))
				if not extractHashFileSha256 is None: self.extractHashFileSha256 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashFileSha256, extract = True))
				if not extractHashFileSha512 is None: self.extractHashFileSha512 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashFileSha512, extract = True))
			if not extractHashOther is None: self.extractHashOther = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashOther, extract = True))
			else:
				if not extractHashOtherMd5 is None: self.extractHashOtherMd5 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashOtherMd5, extract = True))
				if not extractHashOtherSha1 is None: self.extractHashOtherSha1 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashOtherSha1, extract = True))
				if not extractHashOtherSha256 is None: self.extractHashOtherSha256 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashOtherSha256, extract = True))
				if not extractHashOtherSha512 is None: self.extractHashOtherSha512 = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractHashOtherSha512, extract = True))

		if not extractVideoQuality is None: self.extractVideoQuality = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoQuality, extract = True))
		if not extractVideoQualityInexact is None: self.extractVideoQualityInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoQualityInexact, extract = True))
		if not extractVideoResolution is None: self.extractVideoResolution = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoResolution, extract = True))
		if not extractVideoResolutionInexact is None: self.extractVideoResolutionInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoResolutionInexact, extract = True))
		if not extractVideoWidth is None: self.extractVideoWidth = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoWidth, extract = True))
		if not extractVideoWidthInexact is None: self.extractVideoWidthInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoWidthInexact, extract = True))
		if not extractVideoHeight is None: self.extractVideoHeight = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoHeight, extract = True))
		if not extractVideoHeightInexact is None: self.extractVideoHeightInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoHeightInexact, extract = True))
		if not extractVideoAspect is None: self.extractVideoAspect = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoAspect, extract = True))
		if not extractVideoAspectInexact is None: self.extractVideoAspectInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoAspectInexact, extract = True))
		if not extractVideoCodec is None: self.extractVideoCodec = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoCodec, extract = True))
		if not extractVideoDepth is None: self.extractVideoDepth = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoDepth, extract = True))
		if not extractVideoRange is None: self.extractVideoRange = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideoRange, extract = True))
		if not extractVideo3d is None: self.extractVideo3d = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractVideo3d, extract = True))

		if not extractAudioType is None: self.extractAudioType = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractAudioType, extract = True))
		if not extractAudioChannels is None: self.extractAudioChannels = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractAudioChannels, extract = True))
		if not extractAudioSystem is None: self.extractAudioSystem = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractAudioSystem, extract = True))
		if not extractAudioCodec is None: self.extractAudioCodec = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractAudioCodec, extract = True))
		if not extractAudioLanguage is None: self.extractAudioLanguage = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractAudioLanguage, extract = True))
		if not extractAudioLanguageInexact is None: self.extractAudioLanguageInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractAudioLanguageInexact, extract = True))

		if not extractSubtitleType is None: self.extractSubtitleType = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSubtitleType, extract = True))
		if not extractSubtitleLanguage is None: self.extractSubtitleLanguage = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSubtitleLanguage, extract = True))
		if not extractSubtitleLanguageInexact is None: self.extractSubtitleLanguageInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSubtitleLanguageInexact, extract = True))

		if not extractReleaseType is None: self.extractReleaseType = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractReleaseType, extract = True))
		if not extractReleaseFormat is None: self.extractReleaseFormat = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractReleaseFormat, extract = True))
		if not extractReleaseEdition is None: self.extractReleaseEdition = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractReleaseEdition, extract = True))
		if not extractReleaseNetwork is None: self.extractReleaseNetwork = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractReleaseNetwork, extract = True))
		if not extractReleaseGroup is None: self.extractReleaseGroup = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractReleaseGroup, extract = True))
		if not extractReleaseUploader is None: self.extractReleaseUploader = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractReleaseUploader, extract = True))

		if extractFileName is True: self.extractFileName = (lambda item, details = None, entry = None: True)
		elif not extractFileName is None: self.extractFileName = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractFileName, extract = True))
		if extractFileNameInexact is True: self.extractFileNameInexact = (lambda item, details = None, entry = None: True)
		elif not extractFileNameInexact is None: self.extractFileNameInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractFileNameInexact, extract = True))
		if not extractFileExtra is None: self.extractFileExtra = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractFileExtra, extract = True))
		if not extractFileSize is None: self.extractFileSize = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractFileSize, extract = True))
		if not extractFileSizeInexact is None: self.extractFileSizeInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractFileSizeInexact, extract = True))
		if not extractFileContainer is None: self.extractFileContainer = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractFileContainer, extract = True))
		if not extractFilePack is None: self.extractFilePack = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractFilePack, extract = True))

		if not extractSourceType is None: self.extractSourceType = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourceType, extract = True))
		if not extractSourceSeeds is None: self.extractSourceSeeds = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourceSeeds, extract = True))
		if not extractSourceSeedsInexact is None: self.extractSourceSeedsInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourceSeedsInexact, extract = True))
		if not extractSourceLeeches is None: self.extractSourceLeeches = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourceLeeches, extract = True))
		if not extractSourceLeechesInexact is None: self.extractSourceLeechesInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourceLeechesInexact, extract = True))
		if not extractSourceTime is None: self.extractSourceTime = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourceTime, extract = True))
		if not extractSourceTimeInexact is None: self.extractSourceTimeInexact = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourceTimeInexact, extract = True))
		if not extractSourcePopularity is None: self.extractSourcePopularity = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourcePopularity, extract = True))
		if not extractSourceApproval is None: self.extractSourceApproval = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourceApproval, extract = True))
		if not extractSourcePublisher is None: self.extractSourcePublisher = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourcePublisher, extract = True))
		if not extractSourceHoster is None: self.extractSourceHoster = (lambda item, details = None, entry = None: self.extractHtml(item = item, details = details, entry = entry, keys = extractSourceHoster, extract = True))

	##############################################################################
	# GENERAL
	##############################################################################

	# Create a new empty element.
	def create(self, tag):
		return self.mHtml.new_tag(tag)

	##############################################################################
	# PARSE
	##############################################################################

	def parseHtml(self, data, strainer = None):
		try: return Parser(data = data, parser = self.mParser, only = strainer)
		except: self.logError()
		return None

	##############################################################################
	# EXTRACT
	##############################################################################

	def extractHtmlData(self, data, details = False):
		try:
			# ParserHtml5 cannot handle optimization.
			# Error: You provided a value for parse_only, but the html5lib tree builder doesn't support parse_only. The entire document will be parsed.
			optimize = None
			if not self.mParser == ProviderHtml.ParserHtml5:
				if not details and self.mOptimizeData: optimize = self.mOptimizeData
				elif details and self.mOptimizeDetails: optimize = self.mOptimizeDetails
			if optimize:
				tag, attributes, string, _, _, _, _, _, _, _, _ = self.extractHtmlParameters(keys = optimize)
				strainer = Strainer(tag = tag, string = string, attributes = attributes)
				self.mHtml = self.parseHtml(data = data, strainer = strainer)
			else:
				self.mHtml = self.parseHtml(data = data)
			return self.mHtml
		except: self.logError()

	def extractHtmlDecode(self, data):
		if Tools.isArray(data):
			if data and Tools.isArray(data[0]): data = [Parser.convert(data = i[0], full = True) for i in data]
			else: data = [Parser.convert(data = i, full = True) for i in data]
			data = [i.strip() for i in data if i]
		else:
			data = Parser.convert(data = data, full = True)
			if data: data = data.strip()
		return data

	def extractHtmlItem(self, item):
		if Tools.isArray(item):
			try: return item[0]
			except: return None
		return item

	def extractHtmlExpression(self, data, multi = False):
		if multi: return Regex.match(data = data, expression = '(\([^\?].*?\).*?){2,}')
		else: return data and '(' in data and ')' in data

	def extractHtmlParameters(self, keys, extract = None):
		tag = None
		recursive = True
		string = None
		attributes = None
		optional = False
		index = None
		start = None
		end = None
		skip = None
		combine = None

		# Make a copy, the dictionary is reused by each extraction and keys are deleted below.
		keys = Tools.copy(keys)
		if Tools.isDictionary(keys):
			try:
				tag = keys[Html.ParseTag]
				del keys[Html.ParseTag]
			except: pass
			try:
				recursive = keys[Html.ParseRecursive]
				del keys[Html.ParseRecursive]
			except: pass
			try:
				string = keys[Html.ParseString]
				del keys[Html.ParseString]
			except: pass
			try:
				string = Regex.expression(keys[Html.ParseExpression])
				del keys[Html.ParseExpression]
			except: pass
			try:
				extract = keys[Html.ParseExtract]
				del keys[Html.ParseExtract]
			except: pass
			try:
				optional = keys[Html.ParseOptional]
				del keys[Html.ParseOptional]
			except: pass
			try:
				index = keys[Html.ParseIndex]
				del keys[Html.ParseIndex]
			except: pass
			try:
				start = keys[Html.ParseStart]
				del keys[Html.ParseStart]
			except: pass
			try:
				end = keys[Html.ParseEnd]
				del keys[Html.ParseEnd]
			except: pass
			try:
				skip = keys[Html.ParseSkip]
				del keys[Html.ParseSkip]
			except: pass
			try:
				combine = keys[Html.ParseCombine]
				del keys[Html.ParseCombine]
			except: pass
			try:
				attributes = keys[Html.ParseAttribute]
				del keys[Html.ParseAttribute]
			except: attributes = keys
		elif Tools.isString(keys):
			if self.extractHtmlExpression(keys): string = Regex.expression(keys)
			else: tag = keys
		elif Tools.isInteger(keys):
			index = keys

		if attributes:
			for key, value in attributes.items():
				if self.extractHtmlExpression(value):
					attributes[key] = Regex.expression(value)

		return tag, attributes, string, recursive, extract, optional, index, start, end, skip, combine

	def extractHtmlValue(self, item, extract):
		try:
			if extract is True:
				return self.extractHtmlDecode(self.extractHtmlItem(item).text)
			elif Tools.isInteger(extract):
				return self.extractHtmlDecode(item[extract])
			elif Tools.isString(extract):
				if extract == Html.ParseText or extract == Html.ParseTextNested: return self.extractHtmlDecode(self.extractHtmlItem(item).text)
				elif extract == Html.ParseTextUnnested: return self.extractHtmlDecode(''.join([i for i in self.extractHtmlItem(item).contents if type(i) == Navigable]))
				elif extract == Html.ParseCode: return self.extractHtmlDecode(Converter.unicode(self.extractHtmlItem(item)))
				elif extract == Html.ParseEncode: return self.extractHtmlDecode(Networker.linkQuote(item))
				elif extract == Html.ParseDecode: return self.extractHtmlDecode(Networker.linkUnquote(item))
				elif extract == Html.ParseStrip: return self.extractHtmlDecode(item).strip()
				elif extract == Html.ParseSplitSpace:
					try: return [i.strip() for i in self.extractHtmlDecode(item).split(' ')]
					except: return None
				elif extract == Html.ParseSplitComma:
					try: return [i.strip() for i in self.extractHtmlDecode(item).split(',')]
					except: return None
				elif extract == Html.ParseSplitBar:
					try: return [i.strip() for i in self.extractHtmlDecode(item).split('|')]
					except: return None
				elif extract == Html.ParseRemoveSpace: return self.extractHtmlDecode(item).replace(' ', '')
				elif extract == Html.ParseRemoveComma: return self.extractHtmlDecode(item).replace(',', '')
				elif extract == Html.ParseInteger:
					try: return int(item)
					except: return None
				elif extract == Html.ParseFloat:
					try: return float(item)
					except: return None
				elif self.extractHtmlExpression(extract):
					# Use unicode() instead of str(), otherwise there are UnicodeEncodeError for YggTorrent.
					if self.extractHtmlExpression(extract, multi = True): return self.extractHtmlDecode(Regex.extract(data = Converter.unicode(item), expression = extract, group = None, all = True))
					else: return self.extractHtmlDecode(Regex.extract(data = Converter.unicode(item), expression = extract))
				elif extract == Html.ParseTag: return item.name
				else:
					try: return self.extractHtmlDecode(self.extractHtmlItem(item)[extract])
					except: return None # If attribute is not present.
			elif Tools.isDictionary(extract):
				key = list(extract.keys())[0]
				if key == Html.ParseText or key == Html.ParseTextNested or key == Html.ParseTextUnnested:
					return self.extractHtmlValue(item = item, extract = key)
				else:
					value = list(extract.values())[0]
					return self.extractHtmlValue(item = item, extract = value)
			elif Tools.isArray(extract):
				if Tools.isArray(extract[0]):
					return [self.extractHtmlValue(item = item, extract = i) for i in extract]
				else:
					for i in extract:
						item = self.extractHtmlValue(item = item, extract = i)
					return item
			return item
		except:
			self.logError(developer = True)

	def extractHtml(self, item, keys, details = None, entry = None, extract = None):
		try:
			# HTML object.
			try: keys = keys.data()
			except: pass

			if Tools.isArray(keys):
				if keys[0] == ProviderWeb.Details:
					if details is None: return None # On first iteration (item) when details page has not been requested yet.
					keys = keys[1:]
					item = details
				elif keys[0] == ProviderWeb.Entries:
					if details is None: return None # On first iteration (item) when details page has not been requested yet.
					keys = keys[1:]
					item = entry

				if Tools.isArray(keys[0]):
					items = []
					for key in keys:
						it = item
						total = len(key)
						for i in range(total):
							it = self.extractHtml(item = it, keys = key[i], extract = None if (extract is True and i < (total - 1)) else extract) # Only extract for the last element in the list
							if it is None: break
						items.append(it)
					item = items
				else:
					total = len(keys)
					for i in range(total):
						item = self.extractHtml(item = item, keys = keys[i], extract = None if (extract is True and i < (total - 1)) else extract) # Only extract for the last element in the list
						if item is None: break
				return item
			else:
				tag, attributes, string, recursive, extract, optional, index, start, end, skip, combine = self.extractHtmlParameters(keys = keys, extract = extract)
				if tag or string or attributes:
					result = None
					element = self.extractHtmlItem(item)

					if element: result = element.find_all(name = True if tag is None else tag, recursive = recursive, string = string, attrs = attributes)

					if result:
						if skip is None: skip = 1
						else: skip += 1

						if not start is None and not end is None: result = result[start : end : skip]
						elif not start is None: result = result[start : : skip]
						elif not end is None: result = result[ : end : skip]
						elif skip > 1: result = result[ : : skip]

						if not combine is None and combine > 1: result = [result[i:i + combine] for i in range(0, len(result), combine)]
					elif optional: result = item
				else:
					result = item
				if not index is None:
					try: result = result[index]
					except: result = None

				if result:
					if not extract is None: result = self.extractHtmlValue(item = result, extract = extract)
				else:
					result = None
				return result
		except:
			self.logError(developer = True)
			return None
