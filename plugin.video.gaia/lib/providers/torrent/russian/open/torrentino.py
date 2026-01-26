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

from lib.providers.core.html import ProviderHtml, Html, HtmlResults, HtmlResult, HtmlLink, HtmlDiv, HtmlSpan
from lib.modules.tools import Regex

# There is another version with a different HTML structure at: https://torrentino.org
# In their search bar, they show the "torrentino.ru" logo, so not sure if they have the same content as the .ru domain.
# The .org domain does not have magnets, only .torrent files.
# Also, the .org domain somtimes as .rar files (.torrent file compressed). So if ever used, make sure the link has a .torrent extension.

class Provider(ProviderHtml):

	_Link					= {
								ProviderHtml.Version1 : 'https://torrentino.ru',
								ProviderHtml.Version2 : 'https://torrentino.download',
							}
	_Path					= {
								ProviderHtml.Version1 : 'search',
								ProviderHtml.Version2 : 'search.php',
							}

	_ParameterQuery1		= 'query'
	_ParameterQuery2		= 'q'
	_ParameterSort			= 'orderby'
	_ParameterSeeds			= 'seeders'
	_ParameterOrder			= 'ft'
	_ParameterDescending	= 'desc'

	_AttributeTable			= 'table_list'
	_AttributeDetails		= 'torrent_content'

	_AttributeList			= 'film-list'
	_AttributeItem			= 'film-item'
	_AttributeName			= 'film-item-name'
	_AttributeYear			= 'basis-2'
	_AttributeTorrents		= 'film-torrents-list'
	_AttributeTorrent		= 'list-item'
	_AttributeInfoVideo		= 'basis-2'
	_AttributeInfoAudio		= 'basis-3'
	_AttributeSize			= 'basis-6'
	_AttributeTime			= 'basis-8'
	_AttributeAudio			= 'basis-4'
	_AttributeSubtitle		= 'basis-5'
	_AttributeSeeds			= 'torrent-seeds'
	_AttributeLeeches		= 'torrent-peers'

	_Expression3d			= r'(?:^|[\s,])(3d|bd3d|side\s*by\s*side|over\s*under)(?:$|[\s,])'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		version = self.customVersion()

		name = 'Torrentino'
		description = '{name} is less-known open {container} site from Russia. The site contains results in various languages, but most of them are in Russian. {name} requests subpages in order to extract links, which substantially increases scraping time. {name} has multiple versions which are incompatible with each other.'
		customVersion = 2

		if version == ProviderHtml.Version1:
			ProviderHtml.initialize(self,
				name							= name,
				description						= description,
				rank							= 3,
				performance						= ProviderHtml.PerformanceMedium, # Has subpage - but there will only be 1 subpage (containing all the magnets) for most searches.

				link							= Provider._Link[version],

				customVersion					= customVersion,

				supportPack						= False, # Do not search for separate packs - they are extracted from the entries page.

				formatEncode					= ProviderHtml.FormatEncodeQuote,

				searchQuery						= {
													ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
													ProviderHtml.RequestPath : Provider._Path[version],
													ProviderHtml.RequestData : {
														Provider._ParameterQuery1	: ProviderHtml.TermTitle, # Does not support year searches.
													},
												},

				extractOptimizeData				= HtmlDiv(class_ = Provider._AttributeList),
				extractOptimizeDetails			= HtmlDiv(class_ = Provider._AttributeTorrents),
				extractOptimizeEntries			= False,
				extractList						= [HtmlLink(class_ = Provider._AttributeItem)],
				extractDetails					= [Html(extract = Html.AttributeHref, recursive = False)],
				extractEntries					= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeTorrent)],
				extractLink						= [ProviderHtml.Entries, HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileSize					= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._AttributeSize)],
				extractAudioLanguageInexact		= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._AttributeAudio, extract = [Html.ParseTextNested, Html.ParseSplitSpace])],
				extractSubtitleLanguageInexact	= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._AttributeSubtitle, extract = [Html.ParseTextNested, Html.ParseSplitSpace])],
				#extractSourceTime				= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._AttributeTime)], # Probably the time the torrent was added to the website, not the time the torrent was published.
				extractSourceSeeds				= [ProviderHtml.Entries, HtmlSpan(class_ = Provider._AttributeSeeds)],
				extractSourceLeeches			= [ProviderHtml.Entries, HtmlSpan(class_ = Provider._AttributeLeeches)],
			)
		elif version == ProviderHtml.Version2:
			ProviderHtml.initialize(self,
				name					= name,
				description				= description,
				rank					= 2,
				performance				= ProviderHtml.PerformanceBad,
				status					= ProviderHtml.StatusDead, # Website redirects to a different website.

				link					= Provider._Link[version],

				customVersion			= customVersion,

				formatEncode			= ProviderHtml.FormatEncodePlus,

				searchQuery				= {
											ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
											ProviderHtml.RequestPath : Provider._Path[version],
											ProviderHtml.RequestData : {
												Provider._ParameterQuery2	: ProviderHtml.TermQuery,
												Provider._ParameterSort		: Provider._ParameterSeeds,
												Provider._ParameterOrder	: Provider._ParameterDescending,
											},
										},

				extractList				= [HtmlResults(class_ = Provider._AttributeTable, start = 1)],
				extractDetails			= [HtmlResult(index = 1), HtmlLink(extract = Html.AttributeHref)],
				extractLink				= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeDetails), HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)],
				extractFileName			= [HtmlResult(index = 1), HtmlLink()],
				extractFileSize			= [HtmlResult(index = 4)],
				extractSourceTime		= [HtmlResult(index = 0)],
				extractSourceSeeds		= [HtmlResult(index = 2)],
				extractSourceLeeches	= [HtmlResult(index = 3)],
			)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		if self.customVersion1():
			names = self.extractHtml(item, [Html(class_ = Provider._AttributeName)])
			for name in names:
				name = self.extractHtmlValue(item = name, extract = Html.ParseTextNested)

				if name:
					year = self.extractHtml(item, Html(class_ = Provider._AttributeYear, extract = Html.ParseTextNested))
					if year: name += ' ' + year

				# Russian providers have a default 0.7 streamAdjust (web.py -> StreamAdjustRussian).
				# Overwrite here, since these are not file names, but clean titles.
				if self.searchValid(data = name, validateSeason = False, validateEpisode = False, adjust = 1): return item
			return ProviderHtml.Skip
		return item

	def processFileExtra(self, value, item, details = None, entry = None):
		if self.customVersion1():
			if entry:
				video = self.extractHtml(entry, [HtmlDiv(class_ = Provider._AttributeInfoVideo, extract = Html.ParseTextNested)])
				audio = self.extractHtml(entry, [HtmlDiv(class_ = Provider._AttributeInfoAudio, extract = Html.ParseTextNested)])
				value = ', '.join([i for i in [video, audio] if i])

				# Many torrents are marked as 3D, although they are not.
				# Remove 3D keywords and let the 3D format be detected from the file name.
				if value: value = Regex.remove(data = value, expression = Provider._Expression3d, all = True).strip()
			else:
				return None
		return value if value else None
