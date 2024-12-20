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

from lib.modules.tools import Tools, System, Time, Logger, Settings, Language, File, Converter
from lib.modules.interface import Dialog, Format, Translation
from lib.modules.network import Networker
from lib.modules.cache import Cache
from lib.modules.convert import ConverterTime, ConverterDuration
from lib.modules.account import Opensubtitles as Account

class Subtitle(object):

	Link			= 'https://api.opensubtitles.com'
	Path			= 'api/v1'

	ActionLogin		= 'login'
	ActionSearch	= 'subtitles'
	ActionDownload	= 'download'

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def _log(self, message):
		Logger.log('[OPENSUBTITLES] %s' % message)

	@classmethod
	def _agent(self):
		version = '0.0.1' if System.developerVersion() else System.version()
		return '%s v%s' % (System.name(), version)

	@classmethod
	def _key(self):
		return Account.key()

	##############################################################################
	# ACCOUNT
	##############################################################################

	@classmethod
	def account(self):
		return Account()

	@classmethod
	def verify(self, username = None, password = None):
		if self._login(username = username, password = password, refresh = True): return True
		else: return False

	##############################################################################
	# CONNECTION
	##############################################################################

	@classmethod
	def _request(self, method = None, action = None, data = None, internal = None, authorization = True):
		link = Subtitle.Link
		headers = {'Api-Key' : self._key()}

		if authorization:
			login = self._login()
			if login:
				value = login.get('token')
				if value: headers['Authorization'] = 'Bearer ' + value
				value = login.get('link')
				if value: link = ('' if value.startswith('http') else 'https://') + value

		link = Networker.linkJoin(link, Subtitle.Path, action)

		# Do not use the Cloudflare bypasser.
		# The login/subtitle endpoints work through Cloudflare, but for some reason the download endpoint does not.
		# Probably because the user-agent has to be fixed, while the Cloudflare bypasser might change the user-agent on the go.
		# Could also have been a temp issue. OpenSubtitles was down/slow while testing this. Maybe they changed something on the servers.
		result = Networker().requestJson(link = link, method = method, type = type, data = data, agent = self._agent(), headers = headers, cloudflare = False)
		error = self._response(data = result, notification = authorization)

		# Token expires after 24 hours. Refresh it.
		if authorization and result and not internal and error == 'token':
			login = self._login(refresh = True)
			if login: return self._request(method = method, action = action, data = data, internal = True)

		return result

	@classmethod
	def _requestGet(self, action = None, data = None, authorization = True):
		return self._request(method = Networker.MethodGet, action = action, data = data, authorization = authorization)

	@classmethod
	def _requestPost(self, action = None, data = None, authorization = True):
		return self._request(method = Networker.MethodPost, action = action, data = data, authorization = authorization)

	@classmethod
	def _login(self, username = None, password = None, refresh = False):
		if username is None and password is None:
			account = self.account()
			if username is None: username = account.dataUsername()
			if password is None: password = account.dataPassword()

		if username and password:
			from lib.modules.vpn import Vpn
			if Vpn.killRequest():

				def _login(username, password):
					self._log('Refreshing Token')
					data = self._requestPost(action = Subtitle.ActionLogin, data = {'username' : username, 'password' : password}, authorization = False)
					if data and data.get('token'):
						self._log('Token Refresh Success')
						return {
							'token' : data.get('token'),
							'link' : data.get('base_url'),
						}
					self._log('Token Refresh Failure')
					return False

				# Tokens are valid for 24 hours.
				return Cache.instance().cacheSeconds(timeout = Cache.TimeoutClear if refresh else Cache.TimeoutDay1, function = _login, username = username, password = password)

		return None

	@classmethod
	def _response(self, data, notification = True):
		try:
			if not data:
				self._log('Unknown Server Error')
				self._notification(message = 35862, error = True, notification = notification)
				return False

			result = None
			error = None
			status = int(data.get('status') or 0)
			message = (data.get('message') or '').lower()
			errors = data.get('errors') # Form search(). Eg: {"errors":["Not enough parameters"],"status":400}
			if errors:
				errors = ' - '.join(errors)
				if message: message += ' - '
				message += errors

			# Do not show notification is token is being refreshed.
			# A success message can be returned as well from download().
			#	"message":"Your quota will be renewed in 12 hours and 04 minutes (2024-12-10 23:59:59 UTC) ts=1733831755 "
			if 'token' in message: result = 'token'
			elif message and (status >= 300 or not 'remaining' in data): error = message

			if status or error: self._log('Error %s - %s' % (str(status), message))

			if error:
				self._notification(message = error, error = True, notification = notification)
				return result if result else False
			else:
				if 'remaining' in data:
					message = []

					requests = data.get('requests')
					remaining = data.get('remaining')
					total = requests + remaining
					if remaining < 0: remaining = 0

					# Only show if few are left.
					if (remaining / float(total)) < 0.5:
						 # If limit is used up, returns -1 remaining, and requests is one higher. Eg: {"requests": 21, "remaining": -1}
						message.append('%s: %d %s %d' % (Translation.string(33367), remaining, Translation.string(33073), total))

						time = data.get('reset_time_utc')
						if time:
							time = ConverterTime(time, format = ConverterTime.FormatDateTimeJson).timestamp()
							time = ConverterDuration(max(0, time - Time.timestamp()), unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatWordMinimal)
							if time: message.append('%s: %s' % (Translation.string(35479), time.title()))

						self._notification(message = Format.iconJoin(message), error = remaining <= 0, notification = notification)

				return result if result else True
		except: Logger.error()
		return None

	@classmethod
	def _notification(self, message, error = False, notification = True):
		if notification and Settings.getInteger('playback.subtitle.notifications') > 0:
			Dialog.notification(title = 35145 if error else 35393, message = message, duplicates = True, icon = Dialog.IconError if error else Dialog.IconInformation)

	##############################################################################
	# SEARCH
	##############################################################################

	@classmethod
	def search(self, imdb = None, tmdb = None, title = None, year = None, season = None, episode = None, language = None, page = None, refresh = False):
		try:
			serie = not season is None
			data = {}

			data['type'] = 'episode' if serie else 'movie'

			if imdb:
				imdb = int(str(imdb).replace('tt', ''))
				if serie: data['parent_imdb_id'] = imdb
				else: data['imdb_id'] = imdb
			if tmdb:
				tmdb = int(tmdb)
				if serie: data['parent_tmdb_id'] = tmdb
				else: data['tmdb_id'] = tmdb

			if not imdb and not tmdb:
				data['query'] = title
				if year: data['year'] = year

			if not season is None: data['season_number'] = season
			if not episode is None: data['episode_number'] = episode

			# 3-letter code passed in from player.py.
			if language:
				if not Tools.isArray(language): language = [language]
				language = [Language.code(language = i, code = Language.CodePrimary) for i in language]
			else:
				language = Language.settingsCode()
			if language:
				language = [i for i in language if i]
				language = Tools.listUnique(language)
				language = Tools.listSort(language)
				data['languages'] = ','.join(language)

			data['ai_translated'] = 'include'
			data['foreign_parts_only'] = 'include'
			data['hearing_impaired'] = 'include'
			data['machine_translated'] = 'include'
			data['trusted_sources'] = 'include'

			data['order_by'] = 'new_download_count'
			data['order_direction'] = 'desc'
			if page: data['page'] = page

			result = Cache.instance().cacheSeconds(timeout = Cache.TimeoutClear if refresh else Cache.TimeoutDay1, function = self._requestGet, action = Subtitle.ActionSearch, data = data)
			if result:
				result = result.get('data')
				if result: return self.process(data = result)
		except: Logger.error()
		return None

	##############################################################################
	# DOWNLOAD
	##############################################################################

	@classmethod
	def download(self, subtitle, refresh = False):
		try:
			if not subtitle: return None
			id = subtitle.get('id')
			if not id: return None

			data = {
				'file_id'		: id,
				'sub_format'	: 'srt',
			}

			# Download links are valid for 3 hours.
			result = Cache.instance().cacheSeconds(timeout = Cache.TimeoutClear if refresh else (Cache.TimeoutHour3 - 180), function = self._requestPost, action = Subtitle.ActionDownload, data = data)

			if result:
				link = result.get('link')
				if link:
					# Add the language code to the filename (with a dot), because Kodi uses this format to detect the language from SRT files.
					# Kodi will remove the code and symbols before displaying it in the Kodi player interface.
					# NB: Do not append the language to the end (eg: filename.eng.srt).
					# In most cases it works, but if the filename contains certain keywords, they will be used as language instead of the last keyword.
					# Eg: "No Time To Die ...srt" will be detected as Norwegian (first word "No").
					# Use the fallback code if available. Kodi cannot detect some variation codes (eg: ZHT). Use the main language code instead.
					# It seems that Kodi can also not detect any other language/country variatios (eg: zh-TW, zh-Hant, zh_TW, zhtw)
					# https://github.com/xbmc/xbmc/issues/15308
					try: language = subtitle['language'][Language.Fallback]
					except: language = subtitle['language'][Language.Code][Language.CodeStream]
					path = '%s.%s.srt' % (language.upper(), subtitle['name'])

					path = System.temporary(directory = 'subtitles', file = path)
					if not File.exists(path): Networker().request(link = link, path = path, cloudflare = False)
					if File.exists(path):
						subtitle['path'] = path

						# Decoding should not be neccessary anymore in the new OpenSubtitles, according to their docs:
						#	Subtitle file in temporary URL will be always in UTF-8 encoding.
						subtitle['decoded'] = None
						# Certain languages (eg: Chinese, Hebrew, etc) have to be decoded so that they can be correctly encoded with UTF-8.
						# The encoding is not known, and the data returned by OpenSubtitles does not seem to indicate the encoding.
						# Detect the encoding automatically (best guess).
						'''encoding = Converter.encodingDetect(<file data>)
						subtitle['decoded'] = None
						if encoding:
							try:
								data = data.decode(encoding)
								subtitle['decoded'] = True
							except:
								Logger.error()
								subtitle['decoded'] = False'''

						return subtitle
		except: Logger.error()
		return None

	##############################################################################
	# PROCESS
	##############################################################################

	@classmethod
	def process(self, data, integrated = False, universal = True):
		if Tools.isArray(data):
			if not data: return []
			result = [self.process(data = i, integrated = integrated, universal = universal) for i in data]
			return [i for i in result if i]

		if not data: return None
		if not integrated:
			data = data.get('attributes')
			if not data: return None

		result = {}

		file = data.get('files')
		file = file[0] if file else {}
		if not integrated and not file: return None

		result['id'] = data.get('id') if integrated else file.get('file_id') # Use the "file_id" for downloads.
		result['name'] = data.get('name' if integrated else 'release')

		result['language'] = data.get('language' if integrated else 'language')
		if not Tools.isDictionary(result['language']): result['language'] = Language.language(result['language'], variation = True)
		if universal and not result['language']: result['language'] = Language.universal()
		result['language'] = {k : v for k, v in Tools.copy(result['language']).items() if k in [Language.Code, Language.Name, Language.Country]}

		result['rating'] = 1.0 if integrated else (float(data.get('ratings') or 0.0) / 10.0)
		result['votes'] = None if integrated else (data.get('votes') or 0)

		result['download'] = None if integrated else ((data.get('download_count') or 0) + (data.get('new_download_count') or 0))
		result['comment'] = None if integrated else (data.get('comments') or None)

		result['time'] = None if integrated else data.get('upload_date')
		if result['time']: result['time'] = ConverterTime(result['time'], format = ConverterTime.FormatDateTimeJsonBasic).timestamp()

		result['link'] = None if integrated else data.get('url')

		result['type'] = {
			'integrated'	: integrated,
			'default'		: data.get('default' if integrated else False) or False,
			'impaired'		: data.get('impaired' if integrated else 'hearing_impaired') or False,
			'trusted'		: True if integrated else data.get('from_trusted') or False,
			'foreign'		: data.get('forced' if integrated else 'foreign_parts_only') or False,
			'ai'			: data.get('ai' if integrated else 'ai_translated') or False,
			'machine'		: data.get('machine' if integrated else 'machine_translated' or False),
		}

		result['file'] = {
			'hd'	: data.get('hd'),
			'fps'	: data.get('fps'),
			'disc'	: data.get('disc' if integrated else 'nb_cd'),
			'name'	: file.get('file_name'),
		}

		uploader = data.get('uploader') or {}
		result['uploader'] = {
			'name'	: uploader.get('name'),
			'rank'	: uploader.get('rank'),
		}

		return result
