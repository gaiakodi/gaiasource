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

from lib.providers.core.html import ProviderHtml, Html, HtmlDiv, HtmlLink, HtmlImage, HtmlHeading1, HtmlHeading2
from lib.modules.tools import Regex, Tools
from lib.modules.network import Container

class Provider(ProviderHtml):

	_Link					= ['https://lapumia.org']

	_Path					= 'page'

	_ParameterSearch		= 's'

	_AttributePosts			= 'posts'
	_AttributePost			= 'post'
	_AttributeTitle			= 'title'
	_AttributeContent		= 'content'

	_ExpressionFormat		= r'formato\s*:*\s*(.*)'
	_ExpressionDescription	= r'((?:download|baixar)\s*)'
	_ExpressionSizes		= r'tamanho\s*:*\s*(.*)'
	_ExpressionSize			= r'(\d+(?:\.\d+)?\s*[mg]b)'
	_ExpressionLanguage		= r'idioma\s*:*\s*(.*)'
	_ExpressionQuality		= r'\/*(.*?(?:sd|720|1080|2160|4k).*?)(?:\.(?:png|jpg|jpeg|bmp|gif|svg))?$'
	_ExpressionQuality2160	= r'(2160|4k)'
	_ExpressionQuality1080	= r'(1080)'
	_ExpressionQuality720	= r'(720)'
	_ExpressionSubtitle1	= r'legenda\s*:*\s*(.*)'
	_ExpressionSubtitle2	= r'legendas?(?:\.(?:png|jpg|jpeg|bmp|gif|svg))$'
	_ExpressionSubtitle3	= r'(legenda(?:do)?)'
	_ExpressionSubtitle4	= r'((?:download|baixar)\s*legenda(?:do)?s?)'
	_ExpressionDual			= r'(?:^|[\s\-\_])+(dual\s?)(?:$|[\s\-\_])+'
	_ExpressionSeason		= r'(\d+.?\stemporada)'
	_ExpressionEpisode		= r'(.*?):'
	_ExpressionNumber		= r'(\d+.?\s)'

	_CustomLink				= 'customlink'
	_CustomName				= 'customname'
	_CustomSize				= 'customsize'
	_CustomInfo				= 'custominfo'
	_CustomAudio			= 'customaudio'
	_CustomSubtitle			= 'customsubtitle'

	##############################################################################
	# INITIALIZE
	##############################################################################

	def initialize(self):
		ProviderHtml.initialize(self,
			name							= 'Lapumia',
			description						= '{name} is less-known open {container} site from Brazil. The site contains results in various languages, but most of them are in Portuguese. {name} has multiple links for each release. Some metadata, such as audio languages and subtitles, might therefore be inaccurate or not apply to each link for the given release.',
			rank							= 2,
			performance						= ProviderHtml.PerformanceBad,

			link							= Provider._Link,

			supportSpecial					= False, # Has episodes, but they are not directly searchable.

			offsetStart						= 1,
			offsetIncrease					= 1,

			formatEncode					= ProviderHtml.FormatEncodePlus,

			searchQuery						= {
												ProviderHtml.RequestMethod : ProviderHtml.RequestMethodGet,
												ProviderHtml.RequestPath : [Provider._Path, ProviderHtml.TermOffset],
												ProviderHtml.RequestData : {
													Provider._ParameterSearch : ProviderHtml.TermQuery,
												},
											},

			extractOptimizeData				= HtmlDiv(class_ = Provider._AttributePosts),
			extractOptimizeDetails			= HtmlDiv(class_ = Provider._AttributePost),
			extractOptimizeEntries			= False,
			extractList						= [HtmlDiv(class_ = Provider._AttributePost)],
			extractDetails					= [HtmlDiv(class_ = Provider._AttributeTitle), HtmlLink(extract = Html.AttributeHref)],
			extractEntries					= [ProviderHtml.Details, HtmlDiv(class_ = Provider._AttributeContent)],
			extractLink						= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._CustomLink)],
			extractFileNameInexact			= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._CustomName)],
			extractFileExtra				= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._CustomInfo)],
			extractFileSize					= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._CustomSize)],
			extractAudioLanguageInexact		= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._CustomAudio)],
			extractSubtitleType				= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._CustomSubtitle)],
			extractSubtitleLanguageInexact	= [ProviderHtml.Entries, HtmlDiv(class_ = Provider._CustomSubtitle)],
		)

	##############################################################################
	# PROCESS
	##############################################################################

	def processBefore(self, item):
		try:
			# Validate to only retrieve sub-pages that are valid.
			name = self.extractHtml(item, [HtmlDiv(class_ = Provider._AttributeTitle), HtmlLink(extract = Html.ParseText)])
			if not self.searchValid(data = name): return ProviderHtml.Skip
		except: self.logError()

	def processEntries(self, value, item, details = None):
		entries = []

		# Often there are multiple file sizes listed if there are multiple links.
		#	Tamanho: 1.04 GB | 1.38 GB | 2.21 GB | 7.94 GB | 16.3 GB
		#	Tamanho: 30 GB./Part.
		sizes = self.extractHtml(value, [Html(extract = [Html.ParseTextNested, Provider._ExpressionSizes])])
		sizes = Regex.extract(data = sizes, expression = Provider._ExpressionSize, group = None, all = True)

		audios = self.extractHtml(value, [Html(extract = [Html.ParseTextNested, Provider._ExpressionLanguage])])
		if audios: audios = [i.strip() for i in audios.split('|' if '|' in audios else ',')]
		else: audios = None

		# Sometimes the videos do not come with integrated subtitles.
		# Instead there is an additional link to manually download the subtitles from.
		# In such a case, remove the subtitle keywords.
		subtitlesBlock = bool(self.extractHtml(value, [HtmlImage(src_ = Provider._ExpressionSubtitle2)]))
		if not subtitlesBlock: subtitlesBlock = bool(self.extractHtml(value, [HtmlLink(expression = Provider._ExpressionSubtitle4)]))
		subtitles = self.extractHtml(value, [Html(extract = [Html.ParseTextNested, Provider._ExpressionSubtitle1])])

		# The actual filename will be extracted from the magnet. But add to fileExtra in case it contains additional metadata.
		# Do not use this, since the title can contain conflicitng info, like multiple video qualities:
		#	Duna Torrent (2021) Dual Áudio 5.1 WEB-DL 720p, 1080p e 4K 2160p Download
		title = self.extractHtml(details, [HtmlDiv(class_ = Provider._AttributeTitle), HtmlHeading1(extract = Html.ParseText)])
		if title: title = Regex.remove(data = title, expression = Provider._ExpressionDescription, group = 1, all = True)

		season = None
		if title and self.parameterMediaShow():
			season = Regex.extract(data = title, expression = Provider._ExpressionSeason)
			# Make sure the number is placed AFTER the keyword, otherwise the number detection will not detect the episode and label it as a pack.
			# Eg: season-number season-keyword episode-keyword episode-number
			if season:
				number = Regex.extract(data = season, expression = Provider._ExpressionNumber)
				if number: season = season.replace(number, '') + ' ' + number.strip()

		links = self.extractHtml(value, [HtmlLink(href_ = ProviderHtml.ExpressionMagnet)])

		# In very few cases therre are less file sizes than links and there is no clear connection between the sizes and the given links.
		# Sort the sizes and assign based on quality.
		# Eg: Dune 2021: https://lapumia.org/?p=26671
		sizesQuality = None
		if len(sizes) > 1 and not len(sizes) == len(links):
			qualities = []
			for i in range(len(links)):
				qualities.append(Regex.extract(data = self.extractHtml(links[i], [HtmlImage(extract = Html.AttributeSrc)]).strip(), expression = Provider._ExpressionQuality))
			qualities = Tools.listUnique(qualities)

			from lib.modules.convert import ConverterSize
			sizes = [ConverterSize(i).value() for i in sizes]
			sizesSorted = Tools.listSort(sizes)

			sizesQuality = {}
			for expression in [Provider._ExpressionQuality2160, Provider._ExpressionQuality1080, Provider._ExpressionQuality720]:
				for quality in qualities:
					if Regex.match(data = quality, expression = expression):
						try: sizesQuality[quality] = sizesSorted.pop()
						except: pass
						break

		for i in range(len(links)):
			link = self.extractHtml(self.parseHtml('<div>%s</div>' % str(links[i])), [HtmlLink(href_ = ProviderHtml.ExpressionMagnet, extract = Html.AttributeHref)])
			if link:
				parent = links[i].parent
				values = {Provider._CustomLink : link}

				# Description
				label = None
				description = []
				if not description: # Some episodes.
					try: description.append(links[i].find_previous_sibling(Html.TagSpan).text)
					except: pass
				if not description: # Movies and most episodes.
					try: description.append(parent.find_previous_sibling(Html.TagHeading2).text)
					except: pass
				if not description: # Some episodes are wrapped in a separate div.
					try: description.append(parent.parent.find_previous_sibling(Html.TagHeading2).text)
					except: pass
				try:
					episode = Regex.extract(data = parent.text, expression = Provider._ExpressionEpisode) # Individual episodes.
					episode = Regex.remove(data = episode, expression = Provider._ExpressionDescription, group = 1, all = True)
					description.append(episode)
				except: pass
				try: description.append(links[i].text)
				except: pass
				if description:
					description = ' '.join([j for j in description if j])
					description = Regex.remove(data = description, expression = Provider._ExpressionDescription, group = 1, all = True)

				# Info
				info = []
				quality = None
				if description: info.append(description)
				try:
					quality = Regex.extract(data = self.extractHtml(links[i], [HtmlImage(extract = Html.AttributeSrc)]).strip(), expression = Provider._ExpressionQuality)
					info.append(quality)
				except: pass
				values[Provider._CustomInfo] = ' '.join([j for j in info if j])

				# Name
				# A few magnet links do not have a file name.
				# Do not use the page title, since it can contain conflicting info, such as "Completa" being detected as a pack, instead of the individual episode number added below.
				name = None
				if not Container(link).torrentName():
					if self.parameterMediaMovie():
						name = self.parameterTitles()['main']
						year = None
						try: year = years['common']
						except: self.logError()
						if year: name += ' (%d)' % year
					else:
						name = self.parameterTitles()['main']
						if season: name += ' ' + season
						if episode: name += ' ' + episode
				values[Provider._CustomName] = name

				# Size
				try: size = sizesQuality[quality]
				except:
					try: size = sizes[i]
					except: size = sizes[0] if sizes else ''
				values[Provider._CustomSize] = size

				# Audio
				audio = None
				if audios:
					if len(audios) >= 2 and description and Regex.match(data = description, expression = Provider._ExpressionDual): audio = ' '.join(audios)
					else:
						try: audio = audios[i]
						except:
							try: audio = ' '.join(audios)
							except: pass
				values[Provider._CustomAudio] = audio if audio else ''

				# Subtitle
				values[Provider._CustomSubtitle] = subtitles if subtitles and not subtitlesBlock else ''
				if subtitlesBlock: values[Provider._CustomInfo] = Regex.remove(data = values[Provider._CustomInfo], expression = Provider._ExpressionSubtitle3, all = True)

				entry = ''
				for key, value in values.items():
					entry += '<div class="%s">%s</div>' % (key, value)
				entries.append(self.parseHtml(entry))

		return entries
