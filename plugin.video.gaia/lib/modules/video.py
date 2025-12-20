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

import re

from lib.modules.tools import Media, System, Settings, Extension, Tools, Converter, Logger, Time, Math, Regex, Playlist, Matcher
from lib.modules.interface import Dialog, Player, Loader, Format, Translation, Item
from lib.modules.network import Networker
from lib.modules.database import Database
from lib.modules.concurrency import Pool, Lock

class Video(object):

	# Must correspond with the settings.
	ModeDisabled = 0
	ModeDirect = 1
	ModeAutomatic = 2
	ModeManual = 3
	ModeCustom = 4

	# Must correspond with the settings.
	NameTitle = 0
	NameDescription = 1
	NameYoutube = 2

	LinkBase = 'http://www.youtube.com'
	LinkSearch = 'https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=20&order=relevance&key=%s&q=%s'
	LinkDetails = 'https://www.googleapis.com/youtube/v3/videos?part=contentDetails,localizations,statistics,status,snippet&key=%s&id=%s'
	LinkTest = 'https://www.googleapis.com/youtube/v3/videos?part=contentDetails&key=%s&id=5PSNL1qE6VY'
	LinkWatch = 'http://www.youtube.com/watch?v=%s'
	LinkRegister = 'https://console.cloud.google.com'
	LinkHelp = 'internal.link.youtubehelp'

	Domains = ['youtube.com', 'youtu.be', 'yt.be', 'youtube.ae', 'youtube.al', 'youtube.am', 'youtube.at', 'youtube.az', 'youtube.ba', 'youtube.be', 'youtube.bg', 'youtube.bh', 'youtube.bo', 'youtube.by', 'youtube.ca', 'youtube.cat', 'youtube.ch', 'youtube.cl', 'youtube.co', 'youtube.co.ae', 'youtube.co.at', 'youtube.co.cr', 'youtube.co.hu', 'youtube.co.id', 'youtube.co.il', 'youtube.co.in', 'youtube.co.jp', 'youtube.co.ke', 'youtube.co.kr', 'youtube.co.ma', 'youtube.co.nz', 'youtube.co.th', 'youtube.co.tz', 'youtube.co.ug', 'youtube.co.uk', 'youtube.co.ve', 'youtube.co.za', 'youtube.co.zw', 'youtube.com.ar', 'youtube.com.au', 'youtube.com.az', 'youtube.com.bd', 'youtube.com.bh', 'youtube.com.bo', 'youtube.com.br', 'youtube.com.by', 'youtube.com.co', 'youtube.com.do', 'youtube.com.ec', 'youtube.com.ee', 'youtube.com.eg', 'youtube.com.es', 'youtube.com.gh', 'youtube.com.gr', 'youtube.com.gt', 'youtube.com.hk', 'youtube.com.hn', 'youtube.com.hr', 'youtube.com.jm', 'youtube.com.jo', 'youtube.com.kw', 'youtube.com.lb', 'youtube.com.lv', 'youtube.com.ly', 'youtube.com.mk', 'youtube.com.mt', 'youtube.com.mx', 'youtube.com.my', 'youtube.com.ng', 'youtube.com.ni', 'youtube.com.om', 'youtube.com.pa', 'youtube.com.pe', 'youtube.com.ph', 'youtube.com.pk', 'youtube.com.pt', 'youtube.com.py', 'youtube.com.qa', 'youtube.com.ro', 'youtube.com.sa', 'youtube.com.sg', 'youtube.com.sv', 'youtube.com.tn', 'youtube.com.tr', 'youtube.com.tw', 'youtube.com.ua', 'youtube.com.uy', 'youtube.com.ve', 'youtube.cr', 'youtube.cz', 'youtube.de', 'youtube.dk', 'youtube.ee', 'youtube.es', 'youtube.fi', 'youtube.fr', 'youtube.ge', 'youtube.googleapis.com', 'youtube.gr', 'youtube.gt', 'youtube.hk', 'youtube.hr', 'youtube.hu', 'youtube.ie', 'youtube.in', 'youtube.iq', 'youtube.is', 'youtube.it', 'youtube.jo', 'youtube.jp', 'youtube.kr', 'youtube.kz', 'youtube.la', 'youtube.lk', 'youtube.lt', 'youtube.lu', 'youtube.lv', 'youtube.ly', 'youtube.ma', 'youtube.md', 'youtube.me', 'youtube.mk', 'youtube.mn', 'youtube.mx', 'youtube.my', 'youtube.ng', 'youtube.ni', 'youtube.nl', 'youtube.no', 'youtube.pa', 'youtube.pe', 'youtube.ph', 'youtube.pk', 'youtube.pl', 'youtube.pr', 'youtube.pt', 'youtube.qa', 'youtube.ro', 'youtube.rs', 'youtube.ru', 'youtube.sa', 'youtube.se', 'youtube.sg', 'youtube.si', 'youtube.sk', 'youtube.sn', 'youtube.soy', 'youtube.sv', 'youtube.tn', 'youtube.tv', 'youtube.ua', 'youtube.ug', 'youtube.uy', 'youtube.vn']

	TimeFormat = '%Y-%m-%dT%H:%M:%SZ'

	Clean = [
		'season', 'episode',
		'trailer', 'trailers'
		'recap', 'recaps', 'summary',
		'episode', 'promo', 'promos',
		'review', 'reviews',
		'extra', 'extras', 'easter egg', 'easter eggs',
		'deleted', 'delete', 'extended',
		'making of', 'behind the scenes', 'inside', 'backstage',
		'director', 'directors',
		'interview', 'interviews',
		'explained', 'explanation', 'ending',
		'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding',
	]

	def __init__(self, media = Media.Movie, durationMinimum = 1, durationMaximum = None, internal = False):
		self.mMedia = media
		self.mInternal = internal
		self.mDurationMinimum = durationMinimum
		self.mDurationMaximum = durationMaximum
		self.mPlayer = Player()

	@classmethod
	def domains(self):
		return Video.Domains

	@classmethod
	def domainIs(self, link):
		if link:
			link = link.lower()
			for domain in self.domains():
				if domain in link: return True
		return False

	@classmethod
	def command(self, title, year = None, season = None, imdb = None, tmdb = None, tvdb = None, trakt = None, selection = None):
		parameters = {'video' : self.Id, 'title' : title}
		if not year is None: parameters['year'] = year
		if not season is None: parameters['season'] = season
		if not imdb is None: parameters['imdb'] = imdb
		if not tmdb is None: parameters['tmdb'] = tmdb
		if not tvdb is None: parameters['tvdb'] = tvdb
		if not trakt is None: parameters['trakt'] = trakt
		if not selection is None: parameters['selection'] = selection
		return System.command(action = 'streamsVideo', parameters = parameters)

	@classmethod
	def setting(self):
		setting = Settings.getInteger('stream.youtube.retrieval')
		if setting == Video.ModeCustom: setting = Settings.getInteger('stream.youtube.retrieval.' + self.Id)
		return setting

	@classmethod
	def settingContext(self):
		setting = Settings.getInteger('stream.youtube.context')
		if setting == Video.ModeCustom: setting = self.setting()
		return setting

	@classmethod
	def enabled(self, external = False):
		if external: return Extension.installed(id = Extension.IdYouTube)
		else: return self.setting() > 0

	@classmethod
	def install(self):
		from lib.modules.tools import YouTube
		return YouTube.enable(help = True)

	@classmethod
	def authenticated(self, external = False):
		if external: return bool(Video.key(external = True))
		else: return self.account().authenticated()

	@classmethod
	def account(self):
		from lib.modules.account import Youtube
		return Youtube()

	@classmethod
	def accountLabel(self):
		from lib.modules.account import Youtube
		return Youtube().dataLabel()

	@classmethod
	def accountAgent(self):
		from lib.modules.account import Youtube
		return Youtube().agent()

	@classmethod
	def authentication(self, internal = False, settings = False):
		if internal and not Dialog.option(title = 35296, message = 35837, labelConfirm = 32512, labelDeny = 33743): return None

		def _authenticationExternal():
			key = Video.key(external = True)
			return {'key' : key} if key else None

		help = Settings.getString(Video.LinkHelp, raw = True)

		messageNew = {'type' : Dialog.TypeDetails, 'items' : [
			{'type' : 'text', 'value' : 'Google has changed their API authentication and now requires every user to create their own API key. There are two ways to authenticate YouTube:'},
			{'type' : 'list', 'value' : [
				{'title' : 'YouTube Addon', 'value' : 'Use an API key that was already authenticated in the YouTube Kodi addon. The steps below can be skipped.'},
				{'title' : 'Custom Project', 'value' : 'Create a new API key. Open the Google Cloud Console website and follow the steps below.'},
			]},
			{'type' : 'link', 'value' : Video.LinkRegister},
			{'type' : 'list', 'number' : True, 'value' : [
				{'title' : 'Google Login', 'value' : 'Log into Google Cloud Console with your Google account.'},
				{'title' : 'Create Project', 'value' : 'Create a new project. There are various ways to accomplish this, but the easiest way is to use the search feature in the top-center of the Google Cloud menu bar. Search "Create a Project" and select the option under "IAM & Admin". Choose a name and create the project.'},
				{'title' : 'Select Project', 'value' : 'Make sure the newly created project is selected. There are various ways to accomplish this, but the easiest way is to select the project from the top-left dropdown in the menu bar.'},
				{'title' : 'Enable API', 'value' : 'Give your project access to the YouTube API. Use the search feature to find "YouTube Data API v3" and click the "Enable" button.'},
				{'title' : 'Create Credentials', 'value' : 'Navigate to "Credentials" under the YouTube API menu. From the top-left of the menu bar, select "Create Credentials" and choose the "API Key" option. Do not restrict the API key if you do not understand what it does.'},
				{'title' : 'Use Credentials', 'value' : 'Use the generated API key to authenticate YouTube in Gaia in the next step.'},
			]},
			{'type' : 'text', 'value' : 'More information about the authentication can be found here:'},
			{'type' : 'link', 'value' : help},
		]}
		messageVerify = Translation.string(35832) + Dialog.link(link = help, offset = 1)

		loader = Loader.visible()
		result = self.account()._authenticate(
			messageNew = messageNew,
			messageVerify = messageVerify,
			functionExternal = _authenticationExternal,
			functionVerify = self.test,
			settings = settings,
		)

		if internal and loader:
			Dialog.closeAll() # For some reason the loader does not show. Closing all dialogs seems to work.
			Loader.show() # For seaching the API after the authentication.

		try: return result['key']
		except: return None

	@classmethod
	def test(self, key):
		try: key = key['key']
		except: pass
		result = Networker().requestJson(link = Video.LinkTest % key)
		return result and 'items' in result

	@classmethod
	def verify(self):
		return self.test(self.key())

	@classmethod
	def key(self, internal = False, external = False):
		if external:
			try: return System.addon(Extension.IdYouTube).getSetting('youtube.api.key')
			except: return None
		else:
			key = self.account().dataKey()
			if not key and not internal: key = self.authentication(internal = True)
			return key

	def _prefer(self, season = None):
		return None

	def _include(self, season = None):
		return None

	def _exclude(self, season = None):
		return None

	def _cleaned(self, data, title = None): # Do not name "_clean", since the Traler class has its own function named this.
		if title:
			joined = ' '.join(title)
			excludes = []
			for value in Video.Clean:
				if ('+' in value and not value in joined) or (not value in title):
					excludes.append(value)
		else:
			excludes = Video.Clean
		return [i for i in data if not i in excludes]

	def _sort(self, items):
		size = len(items)
		for i in range(size):
			item = items[i]
			sort = 0

			match = item.get('match')
			if match:
				total = 0
				matches = 0
				for j in match.values():
					total += 1
					if j: matches += 1
				if match.get('title'):
					total += 5
					matches += 5
				if match.get('official'):
					total += 1
					matches += 1
				if match.get('prefer'):
					total += 1
					matches += 1
				if not match.get('exclude'):
					matches -= 3
				if match.get('season') is True:
					matches += 2
				elif match.get('season') is False:
					matches -= 2
				sort += (matches / float(total)) * 10

			sort += (item.get('similarity') or 0) * 10
			sort += (item.get('popularity') or 0) # Low weight. Some official trailers that are newly released have very few comments/votes.
			sort += (size - i) / float(size) # Original order returned by queries.

			item['sort'] = sort

		return Tools.listSort(data = items, key = lambda i : i['sort'], reverse = True)

	def _filter(self, items, filters = None, single = True):
		result = []
		for i in range(len(items)):
			filtered = True
			if filters:
				for filter in filters:
					if not items[i]['match'][filter]:
						filtered = False
						break
			if filtered:
				if items[i]['play'] == False:
					link = self._extract(items[i]['id'])
					if link:
						items[i].update(link)
						if single: return items[i]
						else: result.append(items[i])
					else: items[i]['play'] = True
		return result if result else None

	def _search(self, query, title = None, year = None, season = None, selection = None, prefer = None, include = None, exclude = None, single = True):
		try:
			from lib.modules.cache import Cache

			if selection is None:
				selection = self.setting()
				if selection == Video.ModeDisabled: selection = Video.ModeAutomatic # In case it was disabled in the settings, but launched from the Kodi info window or some external addon.

			key = self.key(internal = self.mInternal)
			if not key: return None

			cache = Cache.instance()
			serie = Media.isSerie(self.mMedia)

			# Search videos.
			items = []
			if not Tools.isArray(query): query = [query]

			# Remove "... Collection" keyword for sets, otherwise too few results are found.
			if Media.isSet(self.mMedia):
				expression = '(\scollection)(?:$|[\"\'])'
				title = Regex.remove(data = title, expression = expression, group = 1, cache = True)
				query = [Regex.remove(data = i, expression = expression, group = 1, cache = True) for i in query]

			for q in query:
				link = Video.LinkSearch % (key, Networker.linkQuote(q, plus = True))
				result = cache.cacheMedium(Networker().requestJson, link = link)
				if result and 'items' in result: items.extend(result['items'])

			# Extra details.
			# YouTube returns an error if there are more than 50 IDs: The request specifies an invalid filter parameter.
			link = Video.LinkDetails % (key, ','.join([i['id']['videoId'] for i in items[:50]]))
			result = cache.cacheMedium(Networker().requestJson, link = link)
			result = result.get('items')

			if result:
				for i in result:
					for j in range(len(items)):
						if i['id'] == items[j]['id']['videoId']:
							try:
								if not 'contentDetails' in items[j]: items[j]['contentDetails'] = {}
								items[j]['contentDetails'].update(i['contentDetails'])
							except: pass
							try:
								if not 'localizations' in items[j]: items[j]['localizations'] = {}
								items[j]['localizations'].update(i['localizations'])
							except: pass
							try:
								if not 'status' in items[j]: items[j]['status'] = {}
								items[j]['status'].update(i['status'])
							except: pass
							try:
								if not 'statistics' in items[j]: items[j]['statistics'] = {}
								items[j]['statistics'].update(i['statistics'])
							except: pass
							try:
								if not 'snippet' in items[j]: items[j]['snippet'] = {}
								items[j]['snippet'].update(i['snippet'])
							except: pass

							duration = re.search('^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', items[j]['contentDetails']['duration'])
							try: duration = (int(duration.group(1) if duration.group(1) else 0) * 3600) + (int(duration.group(2) if duration.group(2) else 0) * 60) + (int(duration.group(3) if duration.group(3) else 0))
							except: duration = 0
							items[j]['contentDetails']['duration'] = duration

							try: status = items[j]['status']['privacyStatus']
							except: status = None
							if not status: status = 'public'
							items[j]['status']['privacyStatus'] = status

							break

			# Details not found.
			for i in range(len(items)):
				if not 'contentDetails' in items[i]:
					items[i]['contentDetails'] = {'definition' : 'sd', 'duration' : 0}

			# Filter private videos.
			items = [i for i in items if 'status' in i and i['status']['privacyStatus'] == 'public']

			# Filter duration.
			if self.mDurationMinimum: items = [i for i in items if i['contentDetails']['duration'] >= self.mDurationMinimum]
			if self.mDurationMaximum: items = [i for i in items if i['contentDetails']['duration'] <= self.mDurationMaximum]

			if include:
				for i in range(len(include)):
					if Tools.isArray(include[i]):
						include[i] = [j.lower() for j in include[i]]
					else:
						include[i] = include[i].lower()
			if exclude:
				for i in range(len(exclude)):
					if Tools.isArray(exclude[i]):
						exclude[i] = [j.lower() for j in exclude[i]]
					else:
						exclude[i] = exclude[i].lower()

			title = re.split('[-!$%^&*()_+|~=`{}\[\]:";\'<>?,.\/\s]', title.lower())
			title = [i for i in title if i]
			countTitle = len(title)

			from lib.modules.parser import Parser
			for i in range(len(items)):
				id = items[i]['id']['videoId']
				name = items[i]['snippet']['title']
				try: items[i]['snippet']['title'] = name = Converter.unicode(Parser(name).contents[0]) # Unescape HTML entities.
				except: pass
				split = [j for j in re.split('[-!$%^&*()_+|~=`{}\[\]:";\'<>?,.\/\s]', name.lower()) if j]
				split = [i for i in split if i]
				joined = ' '.join(split)

				hasPrefer = True
				if prefer:
					for j in prefer:
						found = False
						if not Tools.isArray(j): j = [j]
						for k in j:
							if '+' in k:
								sub = re.split('[+]', k)
								try: first = split.index(sub[0])
								except: first = -1
								try: second = split.index(sub[1])
								except: second = -1
								if first >= 0 and second >= 0 and first == (second - 1):
									found = True
									break
							elif k in split:
								found = True
								break
						if not found:
							hasPrefer = False
							break

				hasInclude = True
				if include:
					for j in include:
						found = False
						if not Tools.isArray(j): j = [j]
						for k in j:
							if '+' in k:
								sub = re.split('[+]', k)
								try: first = split.index(sub[0])
								except: first = -1
								try: second = split.index(sub[1])
								except: second = -1
								if first >= 0 and second >= 0 and first == (second - 1):
									found = True
									break
							elif k in split:
								found = True
								break
						if not found:
							hasInclude = False
							break

				hasExclude = True
				if exclude and any((j in joined) if ' ' in j else (j in split ) for j in exclude): hasExclude = False

				# Move videos with a different season number to the end of the list from _sort().
				hasSeason = None
				if serie:
					seasonExtract = Regex.extract(data = name, expression = '(?:season[\s\-\_\+]*|s|part)([0]*\d+)')
					if seasonExtract:
						seasonExtract = int(seasonExtract)
						seasonSearch = 1 if season is None else season
						hasSeason = seasonExtract == seasonSearch

				hasOfficial = 'official' in split

				# Some videos are marked as HD by YouTube, but they are actually not. Check name instead.
				#hasHd = items[i]['contentDetails']['definition'].lower() == 'hd'
				try: hasHd = items[i]['contentDetails']['definition'].lower() == 'hd' and 'hd' in split
				except: hasHd = False

				try: videoQuality = items[i]['contentDetails']['definition'].lower()
				except: videoQuality = 'sd'

				video3d = False
				try: video3d = items[i]['contentDetails']['dimension'].lower() == '3d'
				except: pass

				channel = None
				try:
					value = items[i]['snippet']['channelTitle']
					if value: channel = value
				except: pass

				time = None
				try:
					value = items[i]['snippet']['publishedAt']
					if value: time = value
				except: pass
				if not time:
					try:
						value = items[i]['snippet']['publishTime']
						if value: time = value
					except: pass
				if time: time = Time.timestamp(time, format = Video.TimeFormat)

				language = []
				try:
					value = items[i]['snippet']['defaultAudioLanguage']
					if value: language.append(value)
				except: pass
				try:
					value = items[i]['snippet']['defaultLanguage']
					if value: language.append(value)
				except: pass
				try: language.extend(list(items[i]['localizations'].keys()))
				except: pass

				language = Tools.listUnique(language)
				if not language: language = None

				subtitle = False
				try:
					value = items[i]['contentDetails']['caption']
					if value and not value == 'false': subtitle = True
				except: pass

				countView = 0
				countLike = 0
				countDislike = 0
				countFavorite = 0
				countComment = 0
				try:
					value = int(items[i]['statistics']['viewCount'])
					if value: countView = value
				except: pass
				try:
					value = int(items[i]['statistics']['likeCount'])
					if value: countLike = value
				except: pass
				try:
					value = int(items[i]['statistics']['dislikeCount'])
					if value: countDislike = value
				except: pass
				try:
					value = int(items[i]['statistics']['favoriteCount'])
					if value: countFavorite = value
				except: pass
				try:
					value = int(items[i]['statistics']['commentCount'])
					if value: countComment = value
				except: pass

				popularity = 0
				try: popularity += min(0.25, min(1, (countView / 10000)) * 0.25)
				except: pass
				try: popularity += min(0.05, min(1, (countComment / 100)) * 0.05)
				except: pass
				try: popularity += min(0.7, (countLike / (countDislike + countLike)) * 0.7)
				except: pass
				popularity = Math.round(popularity, places = 2)

				# JaroWinkler provides a better measurement than Levenshtein.
				# Eg: Tom Green Country (2025)
				names = [name]
				if serie: names.append(name + ' Season %d' % (1 if season is None else season))
				if year: names.extend([j.replace(name, name + ' ' + str(year)) for j in names])
				similarity = max([Matcher.jaroWinkler(j, title, ignoreNumeric = False, ignoreCase = True, ignoreSpace = True, ignoreSymbol = True) for j in names])

				cleaned = self._cleaned(data = split, title = title)
				countOverlap = len(set(title) & set(cleaned))
				if countTitle > 2: hasTitle = (countOverlap / float(countTitle)) >= 0.6
				else: hasTitle = countOverlap == countTitle

				if any(j['id'] == id for j in items if j and 'id' in j): # Cheeck if the id is already present
					items[i] = None
				else:
					items[i] = {
						'id' : id,
						'link' : None,
						'play' : False,

						'name' : name,
						'channel' : channel,
						'time' : time,

						'popularity' : popularity,
						'similarity' : similarity,

						'quality' : videoQuality,
						'3d' : video3d,
						'language' : language,
						'subtitle' : subtitle,

						'count' : {
							'view' : countView,
							'like' : countLike,
							'dislike' : countDislike,
							'favorite' : countFavorite,
							'comment' : countComment,
						},

						'match' : {
							'official' : hasOfficial,
							'hd' : hasHd,
							'title' : hasTitle,
							'prefer' : hasPrefer,
							'include' : hasInclude,
							'exclude' : hasExclude,
							'season' : hasSeason,
						},
					}

			items = [i for i in items if i]
			items = self._sort(items)

			if selection == Video.ModeDirect or selection == Video.ModeAutomatic:
				link = self._filter(items, ['title', 'include', 'exclude', 'prefer', 'official', 'hd'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'prefer', 'official'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'prefer', 'hd'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'prefer'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'official', 'hd'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'official'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude', 'hd'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'include', 'exclude'], single = single)
				if link: return link

			if selection == Video.ModeDirect:
				link = self._filter(items, ['title', 'prefer', 'exclude'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'prefer', 'include'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'prefer'], single = single)
				if link: return link
				link = self._filter(items, ['include', 'exclude', 'prefer'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'exclude'], single = single)
				if link: return link
				link = self._filter(items, ['title', 'include'], single = single)
				if link: return link
				link = self._filter(items, ['title'], single = single)
				if link: return link
				link = self._filter(items, ['include', 'exclude'], single = single)
				if link: return link
				link = self._filter(items, ['prefer'], single = single)
				if link: return link
				link = self._filter(items, single = single)
				if link: return link

			# Show a manual selection list.
			if self.mInternal:
				return None
			else:
				if selection == Video.ModeAutomatic or selection == Video.ModeManual:
					if selection == Video.ModeAutomatic:
						Dialog.notification(title = self.Label, message = Translation.string(35645) % Translation.string(self.Label), icon = Dialog.IconError)
					while len(items) > 0:
						names = [i['name'] for i in items]
						choice = Dialog.select(title = self.Label, items = names)
						if choice < 0: return None
						link = self._extract(items[choice]['id'])
						if link:
							return link
						else:
							Dialog.notification(title = self.Label, message = 35361, icon = Dialog.IconError)
							del items[choice]

				if len(items) == 0 and not selection == Video.ModeDirect:
					Dialog.notification(title = self.Label, message = 35361, icon = Dialog.IconError)
		except:
			Logger.error()

	def _extract(self, link):
		try:
			# The setup wizard gets stuck (never opens) if this is imported at the start of the file, which in turn is imported by YouTube in account.py.
			from lib.modules.parser import Parser

			# There are different kind of YouTube URLs with a different way of adding the ID.
			# https://stackoverflow.com/questions/60120026/how-do-i-parse-youtube-urls-to-get-the-video-id-from-a-url-using-dart
			id = Regex.extract(data = link, expression = '.*(?:(?:youtu\.be\/|v\/|vi\/|u\/\w\/|embed\/)|(?:(?:watch)?\/?v(?:i)?=|\&v(?:i)?=))([^#\&\?]*).*')
			if not id:
				id = link.split('?v=')[-1].split('/')[-1].split('?')[0].split('&')[0]
				if not id and not Networker.linkIs(link): id = link

			link = Video.LinkWatch % id
			result = Networker().requestText(link = link, agent = self.accountAgent()) # Add a more recent user-agent, otherwise YouTube throws an error: "Please update your browser ..."

			# Some errors are not in the HTML, but are rendered through JS.
			# "playabilityStatus":{"status":"LOGIN_REQUIRED","reason":"Sign in to confirm your age","errorScreen":{"playerErrorMessageRenderer":{"subreason":{"runs":[{"text":"This video may be inappropriate for some users."}]},"reason":{"runs":[{"text":"Sign in to confirm your age"}]},
			# Update: This could also be done through the old API like the YouTube addon (video_info.py) does it: https://youtubei.googleapis.com/youtubei/v1/player
			if re.search('playerErrorMessageRenderer"\s*:\s*\{', result): return None

			parser = Parser(result, parser = Parser.ParserHtml5)

			alert = parser.findAll('div', {'id': 'watch7-notification-area'})
			if alert and len(alert) > 0: return None

			message = parser.findAll('div', {'id': 'unavailable-submessage'})
			if message:
				message = ''.join([i.text for i in message])
				if re.search('[a-zA-Z]', message): return None

			play = 'plugin://plugin.video.youtube/play/?video_id=%s' % id
			return {'link' : link, 'play' : play}
		except:
			Logger.error()
			return None

	def _resolve(self, query, title = None, year = None, season = None, link = None, selection = None, prefer = None, include = None, exclude = None):
		try:
			if link.startswith(Video.LinkBase):
				link = self._extract(link)
				if link is None: raise Exception()
				return link
			elif not link.startswith('http://'):
				link = Video.LinkWatch % link
				link = self._extract(link)
				if link is None: raise Exception()
				return link
			else:
				raise Exception()
		except:
			# This returns too many fan-created videos. Eg: Game of Thrones Season 2 Recap.
			# If this is ever added back, remember that query can also be a list instead of a string.
			#if exclude: query += ' -' + (' -'.join(exclude))
			return self._search(query, title = title, year = year, season = season, selection = selection, prefer = prefer, include = include, exclude = exclude)

	def _name(self, title, season = None, episode = None):
		if title:
			setting = Settings.getInteger('stream.youtube.name')
			if setting == Video.NameTitle:
				return title
			elif setting == Video.NameDescription:
				title += ' - '
				if not episode is None: title += 'S%02dE%02d' % (int(season), int(episode))
				elif not season is None: title += '%s %s' % (Translation.string(32055), str(season))
				try: title += ' ' + Translation.string(self.Label)
				except: pass
				return Tools.stringRemoveSuffix(title, ' - ').strip()
		return None # The Youtube addon will add the title.

	def _description(self, data, metadata):
		try: plot = metadata['plot']
		except: plot = None

		description = Settings.getInteger('playback.details.description')
		if description > 0:
			details = []
			if 'name' in data and data['name']: details.append((33390, data['name']))
			if 'channel' in data and data['channel']: details.append((32334, data['channel']))

			if details:
				try: plot = plot.strip('\n').strip('\r')
				except: plot = ''

				newline = Format.newline()
				separator = (newline * 2) if plot else ''
				details = '\n'.join([Format.fontBold(Translation.string(i[0]) + ': ') + i[1] for i in details])

				if description == 1: plot = details + separator + plot + newline
				else: plot = plot + separator + details + newline

		return plot

	def _metadata(self, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, title = None, year = None):
		from lib.meta.manager import MetaManager

		if not media: media = self.mMedia
		if Media.isSerie(media):
			if season is None and episode is None: media = Media.Show
			elif episode is None: media = Media.Season
			else: media = Media.Episode

		return MetaManager.instance().metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode)

	def _item(self, data, metadata = None, title = None, year = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
		from lib.meta.tools import MetaTools

		media = self.mMedia
		if metadata is None:
			if Media.isSerie(media):
				if season is None and episode is None: media = Media.Show
				elif episode is None: media = Media.Season
				else: media = Media.Episode
			metadata = self._metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, title = title, year = year)
		else:
			metadata = Tools.copy(metadata)

		item = Item(path = data['play'])
		if metadata:
			metadata['title'] = self._name(title = data['title'] if 'title' in data else metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title'], season = season, episode = episode)
			metadata['plot'] = self._description(data = data, metadata = metadata)

		# NB: Remove the episode number, otherwise the Trakt addon shows the rating dialog when playing videos (eg: trailers during Cinematic Mode).
		# When the episode number is gone, Trakt does not have the full episode info and therefore does not show the rating dialog.
		# For some reason this does not happen with movies. For movies Trakt always detects the movie title as an empty string, preventing the rating dialog from showing.
		try: del metadata['episode']
		except: pass

		MetaTools.instance().itemPlayer(media = media, metadata = metadata, item = item)

		return item

	def play(self, query = None, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, link = None, items = None, resolve = True, loader = True, selection = None, prefer = None, include = None, exclude = None):
		try:
			if loader: Loader.show()

			if not self.key(): # Will show the authnetication message and dialog if not yet authenticated.
				Loader.hide()
				return None
			if not self.enabled(external = True): # If the YouTube addon is not enabled.
				Loader.hide()
				if Dialog.option(title = 35296, message = 36203):
					self.install()
					if not self.enabled(external = True): return None
				else: return None
				Loader.show()

			single = items is None
			if single:
				items = [{'query' : query, 'title' : title, 'link' : None, 'play' : None}]
				if link:
					# A trailer link might be returned by the TMDb/TVDb/Trakt APIs.
					# Although they seem to be YouTube links, just test and ignore if they are not from YouTube.
					if Networker.linkIs(link) and self.domainIs(link): items[0].update(self._extract(link) or {})
					elif link.startswith('plugin:'): items[0]['play'] = play

			if resolve:
				for i in range(len(items)):
					if not Networker.linkIs(items[i]['link']) or not self.domainIs(items[i]['link']):
						linkResolved = self._resolve(query = items[i]['query'], title = items[i]['title'], year = year, season = season, link = items[i]['link'], selection = selection, prefer = prefer, include = include, exclude = exclude)
						if linkResolved: items[i].update(linkResolved)

			items = [item for item in items if not item['play'] is None]
			if len(items) == 0:
				Loader.hide()
				return None

			entries = []
			for item in items:
				entries.append(self._item(data = item, title = title, year = year, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode))

			# Gaia: Must hide loader here and then sleep, otherwise the YouTube addon crashes Kodi.
			# Sleeping for 0.2 is not enough.
			Loader.hide()
			Time.sleep(0.5)

			if single:
				self.mPlayer.play(items[0]['play'], entries[0])
			else:
				playlist = Playlist.playlist()
				for i in range(len(items)):
					playlist.add(items[i]['play'], entries[i])
				self.mPlayer.play(playlist)
		except:
			Logger.error()
			Loader.hide()

class Trailer(Video, Database):

	Name = 'trailers'
	Id = 'trailer'
	Label = 33409
	Description = 35656
	Duration = 300 # 5 minutes.

	TrailerCount = 5
	TrailerDuration = 5

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Trailer.Duration)
		Database.__init__(self, Trailer.Name)
		self.mCinemaPlaylist = Playlist.playlist()
		self.mCinemaStop = False
		self.mCinemaRunning = None
		self.mCinemaInterrupt = False
		self.mCinemaLock = Lock()
		self.mCinemaItems = []

	def _initialize(self):
		self._create('CREATE TABLE IF NOT EXISTS %s (imdb TEXT PRIMARY KEY, time INTEGER);' % Trailer.Name)

	def watched(self, imdb):
		return self._exists('SELECT imdb FROM %s WHERE imdb = "%s";' % (Trailer.Name, imdb))

	def watch(self, imdb):
		self._insert('INSERT OR IGNORE INTO %s (imdb) VALUES ("%s");' % (Trailer.Name, imdb))
		self._update('UPDATE %s SET time = %d;' % (Trailer.Name, Time.timestamp()))

	def unwatch(self, imdb):
		self._delete('DELETE FROM %s WHERE imdb = "%s";' % (Trailer.Name, imdb))

	def _query(self, title = None, year = None, season = None):
		query = []
		if Media.isSerie(self.mMedia):
			# Query first, since it is more accurate.
			if season: query.insert(0, '"%s" "season %s"|s%s trailer' % (title, str(season), str(season)))

			# Also do this for S00/S01.
			# Many miniseries only have trailers without a "season" keyword.
			# And even normal shows often only have trailers without a "season" keyword when S01 is released.
			if season is None or season == 0 or season == 1:
				season = 1
				query.append('"%s" trailer -season %s' % (title, ' '.join(['-s%d' % i for i in range(2, 20)])))

			# The query above, which excludes season numbers, often does not return trailers that are only "Some show title Trailer".
			query.append('"%s" trailer' % title)
		else:
			query.append('"%s" %s trailer' % (title, str(year)))
		return query

	def _prefer(self, season = None):
		result = []
		if Media.isSerie(self.mMedia) and season is None: result.append(['season+1', 's+1', 's1', 'part+1'])
		return result

	def _include(self, season = None):
		result = [['trailer', 'trailers', 'teaser', 'teasers']]
		if Media.isSerie(self.mMedia) and not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season, 'part+%d' % season])
		return result

	def _exclude(self, season = None):
		return ['recap', 'recaps', 'summary', 'episode', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding', 'review', 'reviews', 'music video']

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)

		# Use the "official" trailer from the metadata if available.
		if not link and not items and (imdb or tmdb or tvdb or trakt or title):
			metadata = self._metadata(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, title = title, year = year)
			if metadata:
				link = metadata.get('trailer')
				if not link and (season == 0 or season == 1):
					metadata = self._metadata(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year)
					if metadata: link = metadata.get('trailer')

		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

	@classmethod
	def cinemaEnabled(self):
		return Settings.getInteger('interface.scrape.interface') == 3 and self.authenticated()

	@classmethod
	def cinemaProgress(self):
		return Settings.getBoolean('interface.scrape.interface.progress')

	@classmethod
	def cinemaInterrupt(self):
		return Settings.getBoolean('interface.scrape.interface.interrupt')

	def _cinemaFilter(self, media, items):
		trailer = Trailer()
		items = [item for item in items if 'imdb' in item and not trailer.watched(item['imdb'])]
		try:
			from lib.modules.playback import Playback
			playback = Playback.instance()
			result = []
			for item in items:
				season = item.get('season')
				episode = item.get('episode')
				mediad = media
				if Media.isSerie(media) and (season is None or episode is None): mediad = Media.Show # Otherwise the plyback lookup fails if Media.Episode, but there is no number.
				history = playback.history(media = mediad, imdb = item.get('imdb'), tmdb = item.get('tmdb'), tvdb = item.get('tvdb'), trakt = item.get('trakt'), season = season, episode = episode, quick = True)
				if not history or not history['count']['total']: result.append(item)
			items = result
		except: Logger.error()
		return items

	def _cinemaItems(self, media, minimum = TrailerCount):
		from lib.meta.manager import MetaManager
		from lib.meta.tools import MetaTools

		manager = MetaManager.instance()
		tools = MetaTools.instance()

		items = []

		# First try to retrieve already cached items. This reduces the time before the first trailer starts to play.
		randomized = manager.random(media = media, limit = 2000, detail = False, refresh = False)
		if randomized:
			randomized = randomized.get('items')
			if randomized:
				randomized = self._cinemaFilter(media = media, items = randomized)
				if randomized:
					items.extend(randomized)
					items = tools.filterDuplicate(items)

		# If no cached items are available, retrieve new items.
		if len(items) < minimum:
			randomized = manager.random(media = media, limit = 2000, detail = False, refresh = True)
			if randomized:
				randomized = randomized.get('items')
				if randomized:
					randomized = self._cinemaFilter(media = media, items = randomized)
					if randomized:
						items.extend(randomized)
						items = tools.filterDuplicate(items)

		result = []
		for item in items:
			try:
				if 'imdb' in item and item['imdb'] and item['imdb'].startswith('tt'): # Some do not have an IMDb ID.
					query = self._query(title = item['tvshowtitle']) if Media.isSerie(media) else self._query(title = item['title'], year = item['year'])
					result.append({'metadata' : item, 'query' : query})
			except: pass
		return result

	def _cinemaSearch(self, item):
		try:
			link = None
			metadata = item['metadata']

			# Try using the default trailer if available.
			if 'trailer' in metadata and metadata['trailer'] and self.domainIs(metadata['trailer']): link = self._extract(metadata['trailer'])

			# Otherwise search for a trailer.
			if not link: link = self._resolve(query = item['query'], title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title'], selection = Video.ModeDirect, include = self._include(), exclude = self._exclude())

			if link:
				item['watched'] = False
				item.update(link)
				self.mCinemaLock.acquire()
				self.mCinemaPlaylist.add(item['play'], self._item(data = item, metadata = metadata))
				self.mCinemaItems.append(item)
				self.mCinemaLock.release()
		except:
			Logger.error()

	def _cinemaStart(self, media = Media.Movie, background = None):
		try:
			from lib.modules import window

			loaderNone = Settings.getInteger('interface.scrape.interface.loader') == 0
			if loaderNone: Loader.show()
			else: window.WindowCinema.show(background = background)

			self.mCinemaLock.acquire()
			self.mCinemaRunning = True
			self.mCinemaStop = False
			self.mCinemaInterrupt = False
			self.mCinemaItems = []
			self.mCinemaPlaylist.clear()
			self.mCinemaLock.release()

			items = self._cinemaItems(media = media)
			Tools.listShuffle(items)

			try: items = items[:Trailer.TrailerCount]
			except: pass
			threads = [Pool.thread(target = self._cinemaSearch, args = (item,)) for item in items]
			[thread.start() for thread in threads]
			if loaderNone: Loader.show()

			# Add a maximum number of iterations to each loop, otherwise if something goes wrong, the loops might continue for ever.
			maximum = 600 # 5 minutes.
			while len(self.mCinemaItems) == 0 and not System.aborted() and maximum > 0:
				maximum -= 1
				Time.sleep(0.5)

			if not self.mCinemaStop:
				if loaderNone: Loader.hide()
				self.mPlayer.play(self.mCinemaPlaylist)

				maximum = 1200 # 10 minutes.
				while not System.aborted() and maximum > 0:
					try:
						if self.mPlayer.isPlaying() and self.mPlayer.isPlayingVideo() and self.mPlayer.getTime() >= 0: break
					except: pass

					maximum -= 1
					Time.sleep(0.5)

				if not loaderNone: window.WindowCinema.close()

				# Callbacks don't seem to work with YouTube addon URLs. Check manually.
				maximum = 1200 # 20 minutes.
				while not self.mCinemaStop and not System.aborted() and maximum > 0:
					self.mCinemaRunning = bool(len(self.mPlayer.getAvailableVideoStreams()) > 0 or self.mPlayer.isPlayingVideo()) # Must be wrapped in bool, otherwise returns 0.
					if not self.mCinemaRunning: break

					index = self.mCinemaPlaylist.getposition()
					try: time = self.mPlayer.getTime()
					except: time = 0
					if not self.mCinemaItems[index]['watched'] and time > Trailer.TrailerDuration:
						self.mCinemaItems[index]['watched'] = True
						self.watch(self.mCinemaItems[index]['metadata']['imdb'])

					maximum -= 1
					Time.sleep(1)

		except: Logger.error()

	def cinemaStart(self, media = Media.Movie, background = None, wait = False):
		thread = Pool.thread(target = self._cinemaStart, args = (media, background))
		thread.start()
		if wait: thread.join()

	def cinemaStop(self):
		# This is important.
		# The YouTube plugin needs some time to find and start playing the video.
		# Before the YouTube plugin is ready, Gaia might interrupt the trailer and start the actual episode.
		# A few seconds later, the YouTube plugin finally starts playing and then replaces the episode playback with the trailer playback.
		# In such a case, wait until the trailer starts playing, then stop playback and continue.
		self._cinemaWait1()

		Loader.hide()
		self.mCinemaLock.acquire()
		self.mCinemaStop = True
		self.mCinemaRunning = False
		try: self.mCinemaPlaylist.clear()
		except: pass
		self.mCinemaLock.release()

		if self.cinemaInterrupt(): self.mPlayer.stop()
		self._cinemaWait2()
		if not Settings.getInteger('interface.scrape.interface.loader') == 0:
			from lib.modules import window
			window.WindowCinema.close()

	def _cinemaPlaylist(self):
		try:
			file = self.mPlayer.getPlayingFile()
			return self.mCinemaPlaylist.size() > 0 and ('googlevideo.com' in file or 'youtube.com' in file or 'youtu.be' in file)
		except: return False

	def _cinemaStop(self):
		if self._cinemaPlaylist():
			self.mPlayer.stop()

	def _cinemaWait1(self):
		if self.mCinemaRunning:
			count = 0
			while count < 40:
				try:
					if self.mPlayer.isPlaying() and self.mPlayer.isPlayingVideo() and self.mPlayer.getTime() >= 0: break
				except: pass
				Time.sleep(0.5)
			if self.cinemaInterrupt(): self.mPlayer.stop()

	def _cinemaWait2(self):
		if not self.cinemaInterrupt():
			while self.mPlayer.isPlaying():
				Time.sleep(0.5)
			self.mPlayer.stop()

	def cinemaRunning(self):
		return self.mCinemaRunning is True

	def cinemaCanceled(self):
		return self.mCinemaRunning is False # Can be None.

	##############################################################################
	# CLEAN
	##############################################################################

	def _clean(self, time, commit = True, compact = True):
		if time: return self._delete(query = 'DELETE FROM `%s` WHERE time <= ?;' % Trailer.Name, parameters = [time], commit = commit, compact = compact)
		return False

	def _cleanTime(self, count):
		if count:
			times = self._selectValues(query = 'SELECT time FROM `%s` ORDER BY time ASC LIMIT ?;' % Trailer.Name, parameters = [count])
			if times: return Tools.listSort(times)[:count][-1]
		return None


class Recap(Video):

	Id = 'recap'
	Label = 35535
	Description = 35657
	Duration = 600 # 10 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Recap.Duration)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" recap|summary' % (title)
		else: return '"%s" "season %s"|s%s recap|summary' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['recap', 'recaps', 'summary']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Review(Video):

	Id = 'review'
	Label = 35651
	Description = 35658
	Duration = 1800 # 30 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Review.Duration)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "review"' % (title)
		else: return '"%s" "season %s"|s%s "review"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['review', 'reviews']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Bonus(Video):

	Id = 'bonus'
	Label = 33408
	Description = 35659
	Duration = 1200 # 20 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Bonus.Duration)

	def _query(self, title = None, year = None, season = None):
		# Do not search for "easter eggs", since this returns no results (eg: Game of Thrones).
		if season is None: return '"%s" "extra"|"extras"|"bonus"' % (title)
		else: return '"%s" "season %s"|s%s "extra"|"extras"|"bonus"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['extra', 'extras', 'bonus', 'easter+egg', 'easter+eggs']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'react', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Deleted(Video):

	Id = 'deleted'
	Label = 35654
	Description = 35660
	Duration = 1200 # 20 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Deleted.Duration)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "deleted"|"extended"' % (title)
		else: return '"%s" "season %s"|s%s "deleted"|"extended"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['deleted', 'delete', 'extended']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Production(Video):

	Id = 'production'
	Label = 35650
	Description = 35661
	Duration = 2400 # 40 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Production.Duration)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "making of"|"behind the scenes"|"inside"|"backstage"' % (title)
		else: return '"%s" "season %s"|s%s "making of"|"behind the scenes"|"inside"|"backstage"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['making+of', 'behind+the+scenes', 'inside', 'backstage']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Direction(Video):

	Id = 'direction'
	Label = 33407
	Description = 35662
	Duration = 2400 # 40 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Direction.Duration)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "director"' % (title)
		else: return '"%s" "season %s"|s%s "director"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['director', 'directors']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Interview(Video):

	Id = 'interview'
	Label = 35655
	Description = 35663
	Duration = 2400 # 40 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Interview.Duration)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "interview"' % (title)
		else: return '"%s" "season %s"|s%s "interview"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['interview', 'interviews']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Explanation(Video):

	Id = 'explanation'
	Label = 35652
	Description = 35664
	Duration = 1200 # 20 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Explanation.Duration)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "explained"|"explanation"|"ending"' % (title)
		else: return '"%s" "season %s"|s%s "explained"|"explanation"|"ending"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['explained', 'explanation', 'ending']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Alternation(Video):

	Id = 'alternation'
	Label = 33401
	Description = 33402
	Duration = 1200 # 20 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Alternation.Duration)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "alternate"|"alternative"|"different"|"ending"' % (title)
		else: return '"%s" "season %s"|s%s "alternate"|"alternative"|"different"|"ending"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['alternate', 'alternative', 'different', 'ending']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Reaction(Video):

	Id = 'reaction'
	Label = 33990
	Description = 33991
	Duration = 1800 # 30 minutes.

	def __init__(self, media = Media.Movie):
		Video.__init__(self, media = media, durationMaximum = Reaction.Duration)

	def _query(self, title = None, year = None, season = None):
		if season is None: return '"%s" "react"|"reaction"|"reacting"|"response"|"respond"|"responding"' % (title)
		else: return '"%s" "season %s"|s%s "react"|"reaction"|"reacting"|"response"|"respond"|"responding"' % (title, str(season), str(season))

	def _prefer(self, season = None):
		return []

	def _include(self, season = None):
		result = [['react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']]
		if not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%d' % season])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'episode', 'promo', 'promos', 'recap', 'recaps', 'summary', 'interview']
		if not season is None:
			for episode in range(1, 101):
				result.append('s%02de%02d' % (season, episode))
				result.append('s%de%d' % (season, episode))
				result.append('e%02d' % (episode))
				result.append('e%d' % (episode))
		return result

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		return Video.play(self, query = self._query(title = title, year = year, season = season), imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season), include = self._include(season = season), exclude = self._exclude(season = season))

class Full(Video):

	Id = 'full'

	def __init__(self, media = Media.Movie):
		if media == Media.Movie: duration = 1200 # 20 minutes - Some "shorts" can be searched as movies (eg: 36min - Baelin's Route: An Epic NPC Man Adventure)
		elif media == Media.Docu: duration = 600 # 10 minutes
		elif media == Media.Short: duration = 300 # 5 minutes
		elif Media.isSerie(media): duration = 600 # 10 minutes
		else: duration = 600 # 10 minutes
		Video.__init__(self, media = media, durationMinimum = duration, internal = True)

	def _prefer(self, season = None, episode = None):
		result = []
		if Media.isSerie(self.mMedia):
			if not episode is None: episode = int(episode)
			if not season is None: season = int(season)
			if not episode is None: result.append(['season+%d+episode+%d' % (season, episode), 's+%d+e+%d' % (season, episode), 's%02de%02d' % (season, episode)])
			elif not season is None: result.append(['season+%d' % season, 's+%d' % season, 's%02d' % season, 'part+%d' % season])
		result.append(['full', 'complete'])
		return result

	def _exclude(self, season = None):
		result = ['trailer', 'trailers', 'promo', 'promos', 'recap', 'recaps', 'summary', 'interview', 'interviews', 'explained', 'explanation', 'ending', 'making+of', 'behind+the+scenes', 'inside', 'backstage', 'deleted', 'delete', 'extended', 'extra', 'extras', 'easter+egg', 'easter+eggs', 'review', 'reviews', 'recap', 'recaps', 'summary', 'react', 'reacts', 'reaction', 'reactions', 'reacting', 'response', 'respond', 'responding']
		return result

	def _query(self, title = None, year = None, season = None, episode = None):
		if title:
			if not season is None and not episode is None: return '"%s" "s%02de%02d"' % (title, season, episode)
			elif year: return '"%s" "%s"' % (title, year)
			else: return '"%s"' % title
		return None

	def search(self, title = None, year = None, season = None, episode = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)
		query = self._query(title = title, year = year, season = season, episode = episode)
		if query: return self._search(query = query, title = title, selection = Video.ModeDirect, include = self._include(), exclude = self._exclude(), single = False)
		return None

	def play(self, imdb = None, tmdb = None, tvdb = None, trakt = None, title = None, year = None, season = None, episode = None, link = None, items = None, resolve = True, loader = True, selection = None):
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)
		query = self._query(title = title, year = year, season = season, episode = episode)
		if query: return Video.play(self, query = query, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode, link = link, items = items, resolve = resolve, loader = loader, selection = selection, prefer = self._prefer(season = season, episode = episode), include = self._include(season = season), exclude = self._exclude(season = season))
		return None
