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

from lib.modules import tools
from lib.modules import network
from lib.modules import interface
from lib.modules import database
from lib.modules import clipboard
from lib.modules.cache import Cache
from lib.modules.convert import ConverterTime
from lib.modules.concurrency import Pool
from lib.modules.account import Trakt as Account

TraktId = None
TraktClient = None
TraktAccount = None
TraktLimit = None

def reset(settings = True):
	if settings:
		global TraktAccount
		TraktAccount = None

def getTraktAccount():
	global TraktAccount
	if TraktAccount is None: TraktAccount = Account()
	return TraktAccount

def getTraktId():
	global TraktId
	if TraktId is None: TraktId = tools.System.obfuscate(tools.Settings.getString('internal.key.trakt.id', raw = True))
	return TraktId

def getTraktClient():
	global TraktClient
	if TraktClient is None: TraktClient = tools.System.obfuscate(tools.Settings.getString('internal.key.trakt.client', raw = True))
	return TraktClient

def getTraktToken():
	return getTraktAccount().dataToken()

def getTraktRefresh():
	return getTraktAccount().dataRefresh()

def getTrakt(url, post = None, headers = None, cache = True, check = True, timestamp = None, extended = False, direct = False, method = None, authentication = None, timeout = network.Networker.TimeoutLong, limit = None):
	try:
		if not url.startswith('https://api.trakt.tv'):
			url = network.Networker.linkJoin('https://api.trakt.tv', url)

		token = None
		refresh = None
		if authentication:
			valid = True
			token = authentication['token']
			refresh = authentication['refresh']
		else:
			valid = authenticated()
			if valid:
				token = getTraktToken()
				refresh = getTraktRefresh()

		if headers  is None: headers = {}
		headers['Content-Type'] = 'application/json'
		headers['trakt-api-key'] = getTraktId()
		headers['trakt-api-version'] = '2'

		if not post is None: post = tools.Converter.jsonTo(post)

		if direct or not valid:
			# Some features, like searching, can be done without user authentication.
			# Actually, all endpoints not associated with a user (eg mark as watched, sync rating, etc) do NOT require authentication.
			# So getting movie/show/people summary, searching, getting external IDs, etc can be done without authentication.
			result = network.Networker().request(method = method, link = url, data = post, headers = headers, timeout = timeout)
			data = network.Networker.dataText(result['data'])
			if extended: return data, result['headers'], result['error']
			else: return data

		headers['Authorization'] = 'Bearer %s' % token
		result = network.Networker().request(method = method, link = url, data = post, headers = headers, timeout = timeout)
		try: code = result['error']['code']
		except: code = None
		if code is None:
			try: code = result['status']['code']
			except: code = None
		data = network.Networker.dataText(result['data'])

		# Sometimes Trakt returns an HTML page containing something like: <title>api.trakt.tv | 502: Bad gateway</title>
		# This is typically a temporay problem, sometimes only lasting a few seconds/minutes.
		# Might be a Cloudflare redirection issue, or maybe a Trakt server restart.
		if code == 429:
			limit = _limit(url = url, data = result, wait = limit)
			if limit:
				return getTrakt(url = url, post = post, cache = cache, check = check, timestamp = timestamp, extended = extended, direct = direct, method = method, authentication = authentication, timeout = timeout, limit = limit)
			else:
				if extended: return None, result['headers'], result['error']
				else: return None
		elif (not data and not code == 404 and code >= 300) or (tools.Tools.isNumber(code) and code >= 500 and code <= 599) or (data and tools.Tools.isString(data) and '<html' in data):
			_error(url = url, post = post, timestamp = timestamp, message = 33676)
			if extended: return None, result['headers'], result['error']
			else: return None
		elif data and not (code == 401 or code == 405):
			#if check: cacheUpdate() # Now checked at the end of the script execution.
			if extended: return data, result['headers'], result['error']
			else: return data
		elif code == 404:
			#_error(url = url, post = post, timestamp = timestamp, message = 33786) # Do not show notifications if some movie data cannot be found.
			if extended: return None, result['headers'], result['error']
			else: return None

		oauth = 'https://api.trakt.tv/oauth/token'
		opost = {'client_id': getTraktId(), 'client_secret': getTraktClient(), 'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob', 'grant_type': 'refresh_token', 'refresh_token': refresh}

		result = network.Networker().request(link = oauth, type = network.Networker.DataJson, data = opost, headers = headers, timeout = timeout)
		try: code = result['error']['code']
		except: code = None
		if code is None:
			try: code = result['status']['code']
			except: code = None
		data = network.Networker.dataText(result['data'])

		if code == 429:
			limit = _limit(url = url, data = result, wait = limit)
			if limit:
				return getTrakt(url = url, post = post, cache = cache, check = check, timestamp = timestamp, extended = extended, direct = direct, method = method, authentication = authentication, timeout = timeout, limit = limit)
			else:
				if extended: return None, result['headers'], result['error']
				else: return None
		elif (not data and not code == 404 and code >= 300) or (tools.Tools.isNumber(code) and code >= 500 and code <= 599) or (data and tools.Tools.isString(data) and '<html' in data):
			_error(url = url, post = post, timestamp = timestamp, message = 33676)
			if extended: return None, result['headers'], result['error']
			else: return None
		elif data and (code == 401 or code == 405):
			_error(url = url, post = post, timestamp = timestamp, message = 33677)
			if extended: return None, result['headers'], result['error']
			else: return None
		elif code == 404:
			#_error(url = url, post = post, timestamp = timestamp, message = 33786) # Do not show notifications if some movie data cannot be found.
			if extended: return None, result['headers'], result['error']
			else: return None

		data = tools.Converter.jsonFrom(data)

		getTraktAccount().update(token = data['access_token'], refresh = data['refresh_token'])
		valid = authenticated()
		token = getTraktToken()

		headers['Authorization'] = 'Bearer %s' % token
		result = network.Networker().request(method = method, link = url, data = post, headers = headers, timeout = timeout)
		#if check: cacheUpdate() # Now checked at the end of the script execution.
		if extended: return network.Networker.dataText(result['data']), result['headers'], result['error']
		else: return network.Networker.dataText(result['data'])
	except: tools.Logger.error()

	if extended: return None, None, None
	else: return None


def _error(url, post, timestamp, message):
	_cache(url = url, post = post, timestamp = timestamp)
	if tools.Settings.getBoolean('account.trakt.notifications'):
		interface.Dialog.notification(title = 32315, message = message, icon = interface.Dialog.IconError)

	# Might want to keep the Loader shown when Trakt fails.
	# Eg: Search Trakt, and if it fails, fall back to TMDb search, but keep the Loader visible.
	#interface.Loader.hide()

def cacheUpdate(wait = False):
	if wait: _cacheProcess()
	else: Pool.thread(target = _cacheProcess, start = True)

def _cache(url, post = None, timestamp = None):
	return Cache.instance().traktCache(link = url, data = post, timestamp = timestamp)

def _cacheProcess():
	while True:
		item = Cache.instance().traktRetrieve()
		if not item: break
		getTrakt(url = item['link'], post = tools.Converter.jsonFrom(item['data']) if item['data'] else None, cache = True, check = False, timestamp = item['time'])

def _limit(url = None, data = None, wait = False):
	# https://trakt.docs.apiary.io/#introduction/rate-limiting
	# Trakt does not strictly enforce these limits. Sometimes a few thousand requests can be made before Trakt returns HTTP 429.

	try: limit = tools.Converter.jsonFrom(data['headers']['X-Ratelimit'])
	except: limit = None
	try: seconds = int(data['headers']['Retry-After'])
	except: seconds = None

	if wait is None:
		global TraktLimit
		wait = TraktLimit
		if wait is None and not seconds is None:
			if (limit and 'name' in limit and limit['name'] == 'AUTHED_API_POST_LIMIT'):
				wait = 10 # Retry 10 times, sincer this is important (eg update watched status, progress, etc).
			elif (seconds < 2):
				wait = 1 # Retry only once, and then fail.

	if wait and not seconds is None:
		seconds += (0.5 if seconds < 3 else 1 if seconds < 10 else 2)
		if wait is True: retry = 'an infinite number of times'
		elif wait == 1: retry = '1 time'
		else: retry = '%d times' % wait

		tools.Logger.log('Trakt rate limit reached. Retrying %s in %d secs.' % (retry, seconds))
		tools.Logger.log('     Link: %s' % str(url))
		tools.Logger.log('     Response: %s' % tools.Converter.jsonTo(limit))

		tools.Time.sleep(seconds)
		result = max(0, limit - 1) if tools.Tools.isInteger(limit) else True

		if result:
			tools.Logger.log('Retrying after Trakt rate limit reached.')
			tools.Logger.log('     Link: %s' % str(url))
		else:
			tools.Logger.log('Not retrying after Trakt rate limit reached.')
			tools.Logger.log('     Link: %s' % str(url))

		return result
	else:
		tools.Logger.log('Trakt rate limit reached. Aborting request without retrying.')
		tools.Logger.log('     Link: %s' % str(url))
		tools.Logger.log('     Response: %s' % tools.Converter.jsonTo(limit))
		return False

def _limitEnable(enabled = True):
	global TraktLimit
	TraktLimit = enabled

def authentication(settings = True):
	def _authenticationInitiate():
		try:
			result = getTraktAsJson('/oauth/device/code', {'client_id': getTraktId()}, direct = True)
			return {
				Account.AttributeExpiration : int(result['expires_in']),
				Account.AttributeInterval : int(result['interval']),
				Account.AttributeCode : result['user_code'],
				Account.AttributeDevice : result['device_code'],
				Account.AttributeLink : result['verification_url'],
			}
		except:
			tools.Logger.error()
			return False

	def _authenticationVerify(data):
		try:
			result = getTraktAsJson('/oauth/device/token', {'client_id': getTraktId(), 'client_secret': getTraktClient(), 'code': data['device']}, direct = True)
			if result and 'access_token' in result:
				result = {
					Account.AttributeToken : result['access_token'],
					Account.AttributeRefresh : result['refresh_token'],
				}
				profile = getTraktAsJson('/users/me', authentication = result)
				result[Account.AttributeUsername] = profile['username']
				return result
			return None
		except:
			tools.Logger.error()
			return False

	return getTraktAccount()._authenticate(functionInitiate = _authenticationInitiate, functionVerify = _authenticationVerify, settings = settings)

def authenticationVerify():
	profile = getTraktAsJson('/users/me')
	return profile and 'username' in profile and bool(profile['username'])

def authenticated():
	return getTraktAccount().authenticated()

def manager(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
	try:
		interface.Loader.show()
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)

		label = interface.Translation.string(33297) + ' - %s'
		lists = []
		try:
			result = Cache.instance().cacheRefreshShort(getTraktAsJson, '/users/me/lists')
			result = [(i['name'], i['ids']['slug']) for i in result]
			for i in result:
				lists.append({
					'title' : label % interface.Translation.string(i[0]),
					'items' : [
						{'title' : interface.Translation.string(32521) % i[0], 'value' : interface.Translation.string(33580) % i[0], 'return' : '/users/me/lists/%s/items' % i[1]},
						{'title' : interface.Translation.string(32522) % i[0], 'value' : interface.Translation.string(33581) % i[0], 'return' : '/users/me/lists/%s/items/remove' % i[1]},
					],
				})
		except: tools.Logger.error()

		if not episode is None: media = tools.Media.TypeEpisode
		elif not season is None: media = tools.Media.TypeSeason
		elif tvdb: media = tools.Media.TypeShow
		else: media = tools.Media.TypeMovie

		items = [
			{'title' : interface.Dialog.prefixBack(33486), 'close' : True},
			{
				'title' : 32310,
				'items' : [
					{'title' : 33678, 'value' : 33924, 'return' : 'refresh'},
					{'title' : 33979, 'value' : 33923, 'return' : 'reset'} if (media == tools.Media.TypeMovie or not episode is None) else None,
				],
			},
			{
				'title' : 35500,
				'items' : [
					{'title' : 33651, 'value' : 33655, 'return' : 'watch'},
					{'title' : 33652, 'value' : 33656, 'return' : 'unwatch'},
				],
			},
			{
				'title' : 35501,
				'items' : [
					{'title' : 33653, 'value' : 33657, 'return' : 'rate'},
					{'title' : 33654, 'value' : 33658, 'return' : 'unrate'},
				],
			},
			{
				'title' : 33002,
				'items' : [
					{'title' : 32520, 'value' : 33579, 'return' : '/users/me/lists/%s/items'},
				],
			},
			{
				'title' : label % interface.Translation.string(32032),
				'items' : [
					{'title' : 32516, 'value' : 33575, 'return' : '/sync/collection'},
					{'title' : 32517, 'value' : 33576, 'return' : '/sync/collection/remove'},
				],
			},
			{
				'title' : label % interface.Translation.string(32033),
				'items' : [
					{'title' : 32518, 'value' : 33577, 'return' : '/sync/watchlist'},
					{'title' : 32519, 'value' : 33578, 'return' : '/sync/watchlist/remove'},
				],
			},
		]
		items += lists

		interface.Loader.hide()
		select = interface.Dialog.information(title = 32070, items = items)

		if select:
			if select in ['refresh', 'reset', 'watch', 'unwatch', 'rate', 'unrate']:
				from lib.modules.playback import Playback
				playback = Playback.instance()
				if select == 'refresh': playback.dialogRefresh(media = media)
				elif select == 'reset': playback.dialogReset(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = False, external = True)
				elif select == 'watch': playback.dialogWatch(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, force = True, internal = False, external = True)
				elif select == 'unwatch': playback.dialogUnwatch(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, force = True, internal = False, external = True)
				elif select == 'rate': playback.dialogRate(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = False, external = True)
				elif select == 'unrate': playback.dialogUnrate(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, internal = False, external = True)
			else:
				interface.Loader.show()
				if tvdb == None:
					post = {"movies": [{"ids": {"imdb": imdb}}]}
				else:
					if not episode == None:
						post = {"shows": [{"ids": {"imdb": imdb, "tvdb": tvdb}, "seasons": [{"number": season, "episodes": [{"number": episode}]}]}]}
					elif not season == None:
						post = {"shows": [{"ids": {"imdb": imdb, "tvdb": tvdb}, "seasons": [{"number": season}]}]}
					else:
						post = {"shows": [{"ids": {"imdb": imdb, "tvdb": tvdb}}]}

				if select == '/users/me/lists/%s/items':
					slug = listAdd(successNotification = False)
					if not slug == None: getTrakt(select % slug, post = post)
				else:
					getTrakt(select, post = post)

				interface.Loader.hide()
				interface.Dialog.notification(title = 32315, message = 33583 if '/remove' in select else 33582, icon = interface.Dialog.IconSuccess)
	except:
		tools.Logger.error()
		interface.Loader.hide()


def listAdd(successNotification = True):
	new = interface.Dialog.keyboard(title = 32520)
	if (new == None or new == ''): return
	result = getTrakt('/users/me/lists', post = {"name" : new, "privacy" : "private"})

	try:
		slug = tools.Converter.jsonFrom(result)['ids']['slug']
		if successNotification:
			interface.Dialog.notification(title = 32070, message = 33661, icon = interface.Dialog.IconSuccess)
		return slug
	except:
		interface.Dialog.notification(title = 32070, message = 33584, icon = interface.Dialog.IconError)
		return None


def lists(id = None):
	return Cache.instance().cacheMedium(getTraktAsJson, 'https://api.trakt.tv/users/me/lists' + ('' if id == None else ('/' + str(id))))


def list(id):
	return lists(id = id)


def slug(name):
	name = name.strip()
	name = name.lower()
	name = re.sub('[^a-z0-9_]', '-', name)
	name = re.sub('--+', '-', name)
	return name

def verify(authentication = None):
	try:
		if getTraktAsJson('/sync/last_activities', authentication = authentication):
			return True
	except: pass
	return False

def request(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, rating = None, items = None):
	result = []
	if not items: items = [{'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode, 'rating' : rating}]
	for item in items:
		value = {'ids' : {}}
		if 'imdb' in item and item['imdb']: value['ids']['imdb'] = 'tt' + item['imdb'].replace('tt', '')
		if 'tmdb' in item and item['tmdb']: value['ids']['tmdb'] = int(item['tmdb'])
		if 'tvdb' in item and item['tvdb']: value['ids']['tvdb'] = int(item['tvdb'])
		if 'trakt' in item and item['trakt']: value['ids']['trakt'] = int(item['trakt'])

		time = None
		if 'time' in item and not item['time'] is None:
			try:
				time = item['time']
				if tools.Tools.isInteger(time): time = timeFormat(time)
				if time:
					time = {
						'watched_at' : time, # Watched history sync.
						'rated_at' : time, # Rating sync.
					}
					value.update(time)
				else:
					time = None
			except: tools.Logger.error()

		if 'season' in item and not item['season'] is None:
			entry = {'number' : int(item['season'])}
			if time: entry.update(time)
			value['seasons'] = [entry]

			if 'episode' in item and not item['episode'] is None:
				entry = {'number' : int(item['episode'])}
				if time: entry.update(time)
				if 'rating' in item and not item['rating'] is None: entry['rating'] = int(item['rating'])
				value['seasons'][0]['episodes'] = [entry]
			elif 'rating' in item and not item['rating'] is None:
				value['seasons'][0]['rating'] = int(item['rating'])
		else:
			if 'rating' in item and not item['rating'] is None:
				value['rating'] = int(item['rating'])

		result.append(value)
	return result

def timeout(items):
	return max(network.Networker.TimeoutLong, len(items) * 2)

def link(media, slug, season = None, episode = None):
	if not slug: return None
	link = 'https://trakt.tv/%s/%s'
	if tools.Media.typeTelevision(media):
		type = 'shows'
		if not season is None:
			link += '/seasons/%d' % int(season)
			if not episode is None:
				link += '/episodes/%d' % int(episode)
	else:
		type = 'movies'
	return link % (type, slug)

def settingsPlays():
	return tools.Settings.getInteger('account.trakt.plays')

# This is the old code for rating using the script.trakt dialog.
# Not needed anymore, since we do ratings locally now.
# Leave here for a while, in case we need the legacy code later on.
'''
def rate(imdb = None, tvdb = None, season = None, episode = None, wait = None):
	return _rate(action = 'rate', imdb = imdb, tvdb = tvdb, season = season, episode = episode, wait = wait)

def unrate(imdb = None, tvdb = None, season = None, episode = None, wait = None):
	return _rate(action = 'unrate', imdb = imdb, tvdb = tvdb, season = season, episode = episode, wait = wait)

def rateManual(imdb = None, tvdb = None, season = None, episode = None, wait = None):
	return rate(imdb = imdb, tvdb = tvdb, season = season, episode = episode, wait = wait)

def rateAutomatic(imdb = None, tvdb = None, season = None, episode = None, wait = None):
	if tools.Trakt.installed():
		interface.Loader.show()
		if tools.Settings.getInteger('account.trakt.rating') == 1:
			return rateManual(imdb = imdb, tvdb = tvdb, season = season, episode = episode, wait = wait)
		else:
			addon = tools.System.addon(id = tools.Extension.IdTrakt)
			automatic = False
			if tvdb or season or episode: automatic = addon.getSettingBool('rate_episode')
			else: automatic = addon.getSettingBool('rate_movie')
			if automatic: rateWait(wait = wait)
		interface.Loader.hide()

def rateWait(wait = None):
	if wait is None: wait = tools.Settings.getBoolean('account.trakt.rating.wait')
	if wait: Pool.thread(target = _rateWait, start = True).join()

def _rateWait():
	try:
		if tools.Trakt.installed():
			import xbmcgui
			from lib.modules.window import Window

			# Use these in case the rating dialog does not show, but instead a notification that says the item was already rated.
			# Either check if not notification is shown and then one pops up, or if a notification already shows (eg: from Gaia) and then the object changes when a new notification is shown.
			notification = interface.Dialog.dialogNotificationVisible()
			notificationDialog = xbmcgui.Window(Window.IdWindowNotification)

			# Wait for the dialog to show.
			# 8 seconds. Do not make this too long, in case of the Kodi bug where no notifications are shown anymore until Kodi is restarted.
			visible = False
			for i in range(80):
				if Window.currentTraktRating():
					visible = True
					break
				elif interface.Dialog.dialogNotificationVisible() and ((not notification) or (notification and not notificationDialog == xbmcgui.Window(Window.IdWindowNotification))):
					break
				tools.Time.sleep(0.1)
			interface.Loader.hide()

			# Wait for the dialog to close.
			if visible:
				while Window.currentTraktRating():
					tools.Time.sleep(0.1)

	except: tools.Logger.error()

def _rate(action, imdb = None, tvdb = None, season = None, episode = None, wait = None):
	try:
		if tools.Trakt.installed():
			interface.Loader.show()
			data = {}
			data['action'] = action
			if not tvdb is None:
				data['remoteid'] = tvdb
				if not episode is None:
					data['media_type'] = 'episode'
					data['season'] = int(season)
					data['episode'] = int(episode)
				elif not season is None:
					data['media_type'] = 'season'
					data['season'] = int(season)
				else:
					data['media_type'] = 'show'
			else:
				data['remoteid'] = imdb
				data['media_type'] = 'movie'

			tools.System.executeScript(script = tools.Extension.IdTrakt, parameters = data, wait = True)
			rateWait(wait = wait)
		else:
			interface.Dialog.notification(title = 32315, message = 33659)
	except:
		interface.Loader.hide()
		tools.Logger.error()
'''

def getMovieTranslation(id, lang = None, full = False, cache = True, failsafe = False):
	url = '/movies/%s/translations' % id
	return getTranslation(url = url, lang = lang, full = full, cache = cache, failsafe = failsafe)

def getTVShowTranslation(id, lang = None, season = None, episode = None, full = False, cache = True, failsafe = False):
	if season is None and episode is None: url = '/shows/%s/translations' % id
	elif episode is None: url = '/shows/%s/seasons/%s/translations' % (id, str(season))
	else: url = '/shows/%s/seasons/%s/episodes/%s/translations' % (id, str(season), str(episode))
	return getTranslation(url = url, lang = lang, full = full, cache = cache, failsafe = failsafe)

def getTranslation(url, lang = None, full = False, cache = True, failsafe = False):
	try:
		all = False
		single = False
		multi = False
		if not lang: all = True
		elif tools.Tools.isString(lang): single = True
		elif tools.Tools.isArray(lang): multi = True

		if single: url += '/%s' % lang

		if cache: item = getTraktCache(function = Cache.instance().cacheLong, url = url, failsafe = failsafe)
		else: item = getTraktAsJson(url = url)

		item = processTitles(item)

		# Sometimes the "title" is null for some languages.
		# Eg: /shows/tt13991232/translations
		if item:
			if multi: item = [i for i in item if i['language'] in lang]
			if not full: item = [i['title'] for i in item if 'title' in i and i['title']]
			if single: item = item[0]
			return item
	except: tools.Logger.error()
	return None

def getMovieSummary(id, full = True, cache = True, failsafe = False):
	try:
		url = '/movies/%s' % id
		if full: url += '?extended=full'
		if cache: return getTraktCache(function = Cache.instance().cacheLong, url = url, failsafe = failsafe)
		else: return getTraktAsJson(url = url)
	except: tools.Logger.error()
	return None

def getTVShowSummary(id, full = True, cache = True, failsafe = False):
	try:
		url = '/shows/%s' % id
		if full: url += '?extended=full'
		if cache: return getTraktCache(function = Cache.instance().cacheLong, url = url, failsafe = failsafe)
		else: return getTraktAsJson(url = url)
	except: tools.Logger.error()
	return None

def getTVSeasonSummary(id, season = None, lang = None, full = True, cache = True, failsafe = False):
	try:
		url = '/shows/%s/seasons' % id
		if not season is None: url += '/%d' % season
		if full: url += '?extended=full'
		if lang: url += '%stranslations=%s' % ('&' if full else '?', lang)
		if cache: return getTraktCache(function = Cache.instance().cacheLong, url = url, failsafe = failsafe)
		else: return getTraktAsJson(url = url)
	except: tools.Logger.error()
	return None

def sort_list(sort_key, sort_direction, list_data):
	reverse = False if sort_direction == 'asc' else True
	if sort_key == 'rank':
		return sorted(list_data, key=lambda x: x['rank'], reverse=reverse)
	elif sort_key == 'added':
		return sorted(list_data, key=lambda x: x['listed_at'], reverse=reverse)
	elif sort_key == 'title':
		return sorted(list_data, key=lambda x: title_key(x[x['type']].get('title')), reverse=reverse)
	elif sort_key == 'released':
		return sorted(list_data, key=lambda x: x[x['type']].get('first_aired', ''), reverse=reverse)
	elif sort_key == 'runtime':
		return sorted(list_data, key=lambda x: x[x['type']].get('runtime', 0), reverse=reverse)
	elif sort_key == 'popularity':
		return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
	elif sort_key == 'percentage':
		return sorted(list_data, key=lambda x: x[x['type']].get('rating', 0), reverse=reverse)
	elif sort_key == 'votes':
		return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
	else:
		return list_data


def title_key(title):
	try:
		if title is None: title = ''
		articles_en = ['the', 'a', 'an']
		articles_de = ['der', 'die', 'das']
		articles = articles_en + articles_de

		match = re.match('^(\w+\s+)', title.lower())
		if match and match.group(1) in articles: offset = len(match.group(1))
		else: offset = 0

		return title[offset:]
	except:
		return title

def getTraktAsJson(url, post = None, headers = None, direct = False, authentication = None, extended = False, method = None, timeout = network.Networker.TimeoutLong):
	try:
		data, headers, error = getTrakt(url = url, post = post, headers = headers, extended = True, direct = direct, authentication = authentication, method = method, timeout = timeout)
		data = tools.Converter.jsonFrom(data)
		if headers:
			headers = dict((k.lower(), v) for k, v in headers.items())
			if 'x-sort-by' in headers and 'x-sort-how' in headers:
				data = sort_list(headers['x-sort-by'], headers['x-sort-how'], data)
		if extended: return data, error
		else: return data
	except: tools.Logger.error()
	if extended: return None, None
	else: return None

def getTraktCache(function, url, post = None, direct = False, authentication = None, failsafe = False):
	data, error = function(getTraktAsJson, url = url, post = post, direct = direct, authentication = authentication, extended = True)
	if failsafe and error and error['type'] in network.Networker.ErrorNetwork:
		Cache.instance().cacheDelete(getTraktAsJson, url = url, post = post, direct = direct, authentication = authentication, extended = True)
		return False
	return data

def processTitles(data):
	if data:
		try:
			result = []
			for item in data:
				# Filter out titles that are URLs.
				# Trakt sometimes returns a URL as an alias.
				# Eg: Cruella (2001): https://world.snagfilms.cc/en/movie/337404/cruella
				if network.Networker.linkIs(item['title']): continue

				result.append(item)
			return result
		except: tools.Logger.error()
	return data

def getMovieAliases(id):
	try: return processTitles(Cache.instance().cacheLong(getTraktAsJson, '/movies/%s/aliases' % id))
	except: return []

def getTVShowAliases(id):
	try: return processTitles(Cache.instance().cacheLong(getTraktAsJson, '/shows/%s/aliases' % id))
	except: return []

def getPeopleMovie(id, full = True, cache = True, failsafe = False):
	try:
		url = '/movies/%s/people' % id
		if full: url += '?extended=full'
		if cache: return getTraktCache(function = Cache.instance().cacheLong, url = url, failsafe = failsafe)
		else: return getTraktAsJson(url = url)
	except:
		tools.Logger.error()
		return None

def getPeopleShow(id, season = None, episode = None, full = True, cache = True, failsafe = False):
	try:
		if season is None and episode is None: url = '/shows/%s/people' % id
		elif episode is None: url = '/shows/%s/seasons/%s/people' % (id, str(season))
		else: url = '/shows/%s/seasons/%s/episodes/%s/people' % (id, str(season), str(episode))
		if full: url += '?extended=full'
		if cache: return getTraktCache(function = Cache.instance().cacheLong, url = url, failsafe = failsafe)
		else: return getTraktAsJson(url = url)
	except:
		tools.Logger.error()
		return None

def SearchAll(title = None, year = None, imdb = None, tmdb = None, tvdb = None, trakt = None, full = True, single = False, cache = True, failsafe = False):
	try:
		result = []
		movies = SearchMovie(title = title, year = year, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, full = full, single = single, cache = cache, failsafe = failsafe)
		if movies: result.extend(movies)
		shows = SearchTVShow(title = title, year = year, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, full = full, single = single, cache = cache, failsafe = failsafe)
		if shows: result.extend(shows)
		return result if result else None
	except:
		tools.Logger.error()
		return None

def SearchMovie(title = None, year = None, imdb = None, tmdb = None, tvdb = None, trakt = None, full = True, single = False, cache = True, failsafe = False):
	try:
		if trakt: url = '/search/trakt/%s?type=movie' % str(trakt)
		elif imdb: url = '/search/imdb/%s?type=movie' % str(imdb)
		elif tmdb: url = '/search/tmdb/%s?type=movie' % str(tmdb)
		elif tvdb: url = '/search/tvdb/%s?type=movie' % str(tvdb)
		elif title:
			url = '/search/movie?query=%s' % network.Networker.linkQuote(title, plus = True)
			if year: url += '&years=%s' % str(year)
		else: return None
		if full: url += ('&' if '?' in url else '?') + 'extended=full'

		if cache: result = getTraktCache(function = Cache.instance().cacheLong, url = url, failsafe = failsafe)
		else: result = getTraktAsJson(url = url)

		if result is False: return result
		if single: return result[0] if result else None
		else: return result
	except:
		tools.Logger.error()
		return None

def SearchTVShow(title = None, year = None, imdb = None, tmdb = None, tvdb = None, trakt = None, full = True, single = False, cache = True, failsafe = False):
	try:
		if trakt: url = '/search/trakt/%s?type=show' % str(trakt)
		elif tvdb: url = '/search/tvdb/%s?type=show' % str(tvdb)
		elif imdb: url = '/search/imdb/%s?type=show' % str(imdb)
		elif tmdb: url = '/search/tmdb/%s?type=show' % str(tmdb)
		elif title:
			url = '/search/show?query=%s' % network.Networker.linkQuote(title, plus = True)
			if year: url += '&years=%s' % str(year)
		else: return None
		if full: url += ('&' if '?' in url else '?') + 'extended=full'

		if cache: result = getTraktCache(function = Cache.instance().cacheLong, url = url, failsafe = failsafe)
		else: result = getTraktAsJson(url = url)

		if result is False: return result
		if result: result = [i for i in result if i['type'] == 'show'] # Filter out movie results that might be returned by IMDb lookups which do not support a type parameter.
		if single: return result[0] if result else None
		else: return result
	except:
		tools.Logger.error()
		return None


def getGenre(content, type, type_id):
	try:
		r = '/search/%s/%s?type=%s&extended=full' % (type, type_id, content)
		r = Cache.instance().cacheLong(getTraktAsJson, r)
		r = r[0].get(content, {}).get('genres', [])
		return r
	except:
		return []

##############################################################################
# TIME
##############################################################################

def timeFormat(timestamp):
	# Python by default formats the timezone microseconds to 6 decimal places.
	# Trakt cannot interpret that, so use FormatDateTimeJsonShort instead which only uses 3 decimal places.
	# Use OffsetUtc, otherwise the time marked on Trakt might be off if the user's timezone is UTC.
	return ConverterTime(value = timestamp, format = ConverterTime.FormatTimestamp).string(format = ConverterTime.FormatDateTimeJsonShort, offset = ConverterTime.OffsetUtc)

##############################################################################
# REFRESH
##############################################################################

def refresh(media = None, wait = True, reload = False):
	threads = []
	if not media or tools.Media.typeMovie(media):
		threads.append(Pool.thread(target = historyRefreshMovie, kwargs = {'wait' : True}, start = True))
		threads.append(Pool.thread(target = progressRefreshMovie, kwargs = {'wait' : True}, start = True))
		threads.append(Pool.thread(target = ratingRefreshMovie, kwargs = {'wait' : True}, start = True))
	if not media or tools.Media.typeTelevision(media):
		threads.append(Pool.thread(target = historyRefreshShow, kwargs = {'wait' : True, 'reload' : reload}, start = True))
		threads.append(Pool.thread(target = progressRefreshShow, kwargs = {'wait' : True}, start = True))
		threads.append(Pool.thread(target = ratingRefreshShow, kwargs = {'wait' : True}, start = True))
	if wait: [thread.join() for thread in threads]

##############################################################################
# HISTORY - GENERAL
##############################################################################

TraktHistory = {}

def historyType(media = None, season = None, episode = None, plural = True):
	if media is None: media = tools.Media.TypeShow if (not season is None or not episode is None) else tools.Media.TypeMovie
	if tools.Media.typeTelevision(media): type = 'show'
	else: type = 'movie'
	if plural and not type.endswith('s'): type += 's'
	return media, type

def historyLink(media = None, type = None, id = None, dateStart = None, dateEnd = None, extended = False):
	if not type: media, type = historyType(media = media)
	if id:
		# This endpoint has paging. Add limit, otherwise only a few episodes are returned.
		link = 'sync/history/%s/%s?limit=9999999999' % (type, id)
		if extended: link += '&extended=full'
		if dateStart: link += '&start_at=' + timeFormat(dateStart)
		if dateEnd: link += '&end_at=' + timeFormat(dateEnd)
	else:
		link = 'sync/watched/%s' % type
		if extended: link += '?extended=full'
	return link

##############################################################################
# HISTORY - CLEAR
##############################################################################

def historyClear(media, wait = True):
	def _historyClear(media):
		global TraktHistory
		TraktHistory = {}
		Cache.instance().cacheDelete(getTraktAsJson, historyLink(media = media))
	if wait: _historyClear(media = media)
	else: Pool.thread(target = _historyClear, kwargs = {'media' : media}, start = True)

def historyClearMovie(wait = True):
	historyClear(media = tools.Media.TypeMovie, wait = wait)

def historyClearShow(wait = True):
	historyClear(media = tools.Media.TypeShow, wait = wait)

##############################################################################
# HISTORY - REFRESH
##############################################################################

def historyRefresh(media = None, wait = True, reload = True):
	def _historyRefresh(media, reload):
		historyClear(media = media, wait = True)
		historyRetrieve(media = media)

		# When we watch an episode and afterwards load the Trakt progress menu, the previously watched show is not listed.
		# This is probably because Gaia thinks there are no new episodes, since the last episode it knows of, has just been watched.
		# If the progress menu is reloaded manually (navigate back and load menu again), the show is listed again.
		# Auto reload here if the history changed, so that the user does not have to manually reload the list.
		if reload and tools.Media.typeTelevision(media):
			from lib.indexers.episodes import Episodes
			Episodes().arrivalsRefresh()

	if wait: _historyRefresh(media = media, reload = reload)
	else: Pool.thread(target = _historyRefresh, kwargs = {'media' : media, 'reload' : reload}, start = True)

def historyRefreshMovie(wait = True):
	historyRefresh(media = tools.Media.TypeMovie, wait = wait)

def historyRefreshShow(wait = True, reload = True):
	historyRefresh(media = tools.Media.TypeShow, wait = wait, reload = reload)

##############################################################################
# HISTORY - RETRIEVE
##############################################################################

# NB: detailed == True: retrieve all play times, instead of just the last one. An additional non-cached API call is being made, so use sparingly and not in batch.
# Currently only used when manually marking as unwatched and the user chooses to unwatch a specific play.
def historyRetrieve(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, detailed = False):
	if tools.Media.typeTelevision(media): return historyRetrieveShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, detailed = detailed)
	else: return historyRetrieveMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, detailed = detailed)

def historyRetrieveItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, detailed = False):
	try:
		media, type = historyType(media = media, season = season, episode = episode)

		ids = {}
		if not imdb is None: ids['imdb'] = str(imdb)
		if not tmdb is None: ids['tmdb'] = int(tmdb)
		if not tvdb is None: ids['tvdb'] = int(tvdb)
		if not trakt is None: ids['trakt'] = int(trakt)
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)

		link = historyLink(type = type)

		# Use global var to improve speeds, especially for batch requests where this function is called multiple times for different movies/shows.
		global TraktHistory
		if not link in TraktHistory: TraktHistory[link] = Cache.instance().cacheMini(getTraktAsJson, link)
		items = TraktHistory[link]

		single = bool(imdb or tmdb or tvdb or trakt)
		result = []
		if items:
			if tools.Media.typeTelevision(media):
				for item in items:
					try:
						if 'show' in item:
							allow = False
							if single:
								for id in ids.keys():
									if id in item['show']['ids'] and item['show']['ids'][id] == ids[id]:
										allow = True
										break
							else: allow = True

							if allow:
								id = {k : str(v) if v else None for k, v in item['show']['ids'].items()}
								time = tools.Time.timestamp(item['last_watched_at'], iso = True)
								show = {
									'id' : id,
									'title' : item['show']['title'],
									'year' : item['show']['year'],
									'count' : {
										'total' : item['plays'],
										'unique' : sum([len(i['episodes']) for i in item['seasons']]),
										'main' : {
											'total' : sum([sum([j['plays'] for j in i['episodes']]) for i in item['seasons'] if not i['number'] == 0]),
											'unique' : sum([len(i['episodes']) for i in item['seasons'] if not i['number'] == 0]),
										},
									},
									'time' : {
										'last' : time,
										'all' : [time],
									},
								}

								found = False
								seasons = []
								for s in item['seasons']:
									try:
										episodes = []
										for e in s['episodes']:
											try:
												if episode is None:
													time = tools.Time.timestamp(e['last_watched_at'], iso = True)
													episodes.append({
														'season' : s['number'],
														'episode' : e['number'],
														'count' : {
															'total' : e['plays'],
															'unique' : 1,
														},
														'time' : {
															'last' : time,
															'all' : historyTimeShow(trakt = item['show']['ids']['trakt'], season = s['number'], episode = e['number']) if detailed else [time] if time else [],
														},
													})
												elif season == s['number'] and episode == e['number']:
													time = tools.Time.timestamp(e['last_watched_at'], iso = True)
													result.append({
														'id' : id,
														'title' : item['show']['title'],
														'year' : item['show']['year'],
														'season' : s['number'],
														'episode' : e['number'],
														'count' : {
															'total' : e['plays'],
															'unique' : 1,
														},
														'time' : {
															'last' : time,
															'all' : historyTimeShow(trakt = item['show']['ids']['trakt'], season = s['number'], episode = e['number']) if detailed else [time] if time else [],
														},
													})
													found = True
													break
											except: tools.Logger.error()

										if not season is None and episode is None:
											if season == s['number']:
												time = max([e['time']['last'] for e in episodes])
												result.append({
													'id' : id,
													'title' : item['show']['title'],
													'year' : item['show']['year'],
													'season' : s['number'],
													'count' : {
														'total' : sum([e['count']['total'] for e in episodes]),
														'unique' : sum([e['count']['unique'] for e in episodes]),
													},
													'time' : {
														'last' : time,
														'all' : [time] if time else [],
													},
													'episodes' : episodes,
												})
												found = True
												break
										elif season is None and episode is None:
											time = max([e['time']['last'] for e in episodes])
											seasons.append({
												'season' : s['number'],
												'count' : {
													'total' : sum([e['count']['total'] for e in episodes]),
													'unique' : sum([e['count']['unique'] for e in episodes]),
												},
												'time' : {
													'last' : time,
													'all' : [time] if time else [],
												},
												'episodes' : episodes,
											})
										if found: break
									except: tools.Logger.error()
								if found: break

								if season is None and episode is None:
									show['seasons'] = seasons
									result.append(show)
								if single: break
					except: tools.Logger.error()
			else:
				for item in items:
					try:
						if 'movie' in item:
							allow = False
							if single:
								for id in ids.keys():
									if id in item['movie']['ids'] and item['movie']['ids'][id] == ids[id]:
										allow = True
										break
							else: allow = True

							if allow:
								time = tools.Time.timestamp(item['last_watched_at'], iso = True)
								result.append({
									'id' : {k : str(v) if v else None for k, v in item['movie']['ids'].items()},
									'title' : item['movie']['title'],
									'year' : item['movie']['year'],
									'count' : {
										'total' : item['plays'],
										'unique' : item['plays'],
									},
									'time' : {
										'last' : time,
										'all' : historyTimeMovie(trakt = item['movie']['ids']['trakt']) if detailed else [time] if time else [],
									},
								})
								if single: break
					except: tools.Logger.error()

		if single: return result[0] if result else None
		else: return result
	except: tools.Logger.error()
	return None

def historyRetrieveMovie(imdb = None, tmdb = None, trakt = None, detailed = False):
	return historyRetrieveItems(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, trakt = trakt, detailed = detailed)

def historyRetrieveShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, detailed = False):
	return historyRetrieveItems(media = tools.Media.TypeShow, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, detailed = detailed)

##############################################################################
# HISTORY - UPDATE
##############################################################################

def historyUpdate(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, time = None, refresh = True, wait = False):
	if tools.Media.typeTelevision(media): return historyUpdateShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, time = time, refresh = refresh, wait = wait)
	else: return historyUpdateMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, items = items, time = time, refresh = refresh, wait = wait)

def historyUpdateTime(items = None, time = None):
	if items and time:
		if tools.Tools.isInteger(time): time = timeFormat(time)
		for i in range(len(items)): items[i]['watched_at'] = time
	return items

def historyUpdateItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, time = None, refresh = True, wait = False):
	media, type = historyType(media = media)
	items = request(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items)
	items = historyUpdateTime(items = items, time = time)
	result = getTraktAsJson('/sync/history', {type : items}, timeout = timeout(items))
	if refresh: historyRefresh(media = media, wait = wait)
	return result, items

def historyUpdateMovie(imdb = None, tmdb = None, trakt = None, items = None, time = None, refresh = True, wait = False):
	result, items = historyUpdateItems(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, trakt = trakt, items = items, time = time, refresh = refresh, wait = wait)
	return result

def historyUpdateShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, time = None, refresh = True, wait = False):
	result, items = historyUpdateItems(media = tools.Media.TypeShow, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, time = time, refresh = refresh, wait = wait)
	return result

##############################################################################
# HISTORY - REMOVE
##############################################################################

# selection: None = remove all, False = remove oldest, True = remove most recent, Small Integer = remove specific index, Large Integer = remove specific history ID, List = start and end timestamp to remove all items between the dates.
def historyRemove(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, selection = None, refresh = True, wait = False):
	if tools.Media.typeTelevision(media): return historyRemoveShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, selection = selection, refresh = refresh, wait = wait)
	else: return historyRemoveMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, items = items, selection = selection, refresh = refresh, wait = wait)

def historyRemoveItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, selection = None, refresh = True, wait = False):
	media, type = historyType(media = media)

	ids = None
	if not selection is None:
		ids = []
		if items:
			for item in items:
				id = historyId(media = media, imdb = item.get('imdb'), tmdb = item.get('tmdb'), tvdb = item.get('tvdb'), trakt = item.get('trakt'), season = item.get('season'), episode = item.get('episode'), selection = selection)
				if id:
					if tools.Tools.isArray(id): ids.extend(id)
					else: ids.append(id)
		else:
			id = historyId(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, selection = selection)
			if id:
				if tools.Tools.isArray(id): ids.extend(id)
				else: ids.append(id)
		if not ids: return None, None

	if ids is None:
		items = request(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items)
		result = getTraktAsJson('/sync/history/remove', {type : items}, timeout = timeout(items))
	else:
		result = getTraktAsJson('/sync/history/remove', {'ids' : ids}, timeout = timeout(ids))

	if refresh: historyRefresh(media = media, wait = wait)
	return result, items

def historyRemoveMovie(imdb = None, tmdb = None, trakt = None, items = None, selection = None, refresh = True, wait = False):
	result, items = historyRemoveItems(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, trakt = trakt, items = items, selection = selection, refresh = refresh, wait = wait)
	return result

def historyRemoveShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, selection = None, refresh = True, wait = False):
	result, items = historyRemoveItems(media = tools.Media.TypeShow, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, selection = selection, refresh = refresh, wait = wait)
	return result

##############################################################################
# HISTORY - DETAIL
##############################################################################

# action = scrobble, checkin, watch. None == all
# selection: None = retrieve all, False = retrieve oldest, True = retrieve most recent, Small Integer = retrieve specific index, Large Integer = retrieve specific history ID, List = start and end timestamp to retrieve all items between the dates.
def historyDetail(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	if tools.Media.typeTelevision(media): return historyDetailShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)
	else: return historyDetailMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyDetailItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	media, type = historyType(media = media, season = season, episode = episode, plural = True)

	if not trakt:
		if tools.Media.typeTelevision(media): data = SearchTVShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, single = True, full = False, cache = True)
		else: data = SearchMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, single = True, full = False, cache = True)
		if data and 'type' in data and data['type'] in data:
			data = data[data['type']]
			if 'ids' in data and 'trakt' in data['ids']: trakt = data['ids']['trakt']
	if not trakt: return None

	dateStart = None
	dateEnd = None
	if tools.Tools.isArray(selection) and selection:
		dateStart = selection[0]
		dateEnd = selection[1]

	result = None
	link = historyLink(type = type, id = trakt, dateStart = dateStart, dateEnd = dateEnd)

	# Use global var to improve speeds, especially for batch requests where this function is called multiple times for different movies/shows.
	global TraktHistory
	if not link in TraktHistory: TraktHistory[link] = getTraktAsJson(link)
	data = TraktHistory[link]
	if data:
		if not season is None: data = [i for i in data if i['episode']['season'] == season]
		if not episode is None: data = [i for i in data if i['episode']['number'] == episode]

		if action: result = [i for i in data if i['action'] == action]
		else: result = data

		if not selection is None:
			if result:
				if selection is True: result = result[0]
				elif selection is False: result = result[-1]
				elif tools.Tools.isInteger(selection):
					if selection < len(result): result = result[selection]
					else: result = next(i for i in result if 'id' in i and i['id'] == selection)
			else:
				result = None

	return result

def historyDetailMovie(imdb = None, tmdb = None, trakt = None, action = None, selection = None):
	return historyDetailItems(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyDetailShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	return historyDetailItems(media = tools.Media.TypeShow, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)

##############################################################################
# HISTORY - ID
##############################################################################

# action = scrobble, checkin, watch. None == all
# selection: None = retrieve all, False = retrieve oldest, True = retrieve most recent, Small Integer = retrieve specific index, Large Integer = retrieve specific history ID, List = start and end timestamp to retrieve all items between the dates.
def historyId(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	if tools.Media.typeTelevision(media): return historyIdShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)
	else: return historyIdMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyIdItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	result = historyDetailItems(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)
	if result:
		if tools.Tools.isArray(result): result = [i['id'] for i in result if 'id' in i and i['id']]
		elif tools.Tools.isDictionary(result) and 'id' in result and result['id']: result = result['id']
		else: result = None
	return result

def historyIdMovie(imdb = None, tmdb = None, trakt = None, action = None, selection = None):
	return historyIdItems(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyIdShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	return historyIdItems(media = tools.Media.TypeShow, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)

##############################################################################
# HISTORY - TIME
##############################################################################

# action = scrobble, checkin, watch. None == all
# selection: None = retrieve all, False = retrieve oldest, True = retrieve most recent, Small Integer = retrieve specific index, Large Integer = retrieve specific history ID.
def historyTime(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	if tools.Media.typeTelevision(media): return historyTimeShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)
	else: return historyTimeMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyTimeItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	result = historyDetailItems(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)

	if result:
		if tools.Tools.isArray(result): result = [tools.Time.timestamp(i['watched_at'], iso = True) for i in result if 'watched_at' in i and i['watched_at']]
		elif tools.Tools.isDictionary(result) and 'watched_at' in result and result['watched_at']: result = tools.Time.timestamp(result['watched_at'], iso = True)
		else: result = None
	return result

def historyTimeMovie(imdb = None, tmdb = None, trakt = None, action = None, selection = None):
	return historyTimeItems(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyTimeShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	return historyTimeItems(media = tools.Media.TypeShow, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)

##############################################################################
# PROGRESS - GENERAL
##############################################################################

TraktProgress = {}

def progressType(media = None, season = None, episode = None, plural = False):
	if media is None: media = tools.Media.TypeShow if (not season is None or not episode is None) else tools.Media.TypeMovie
	if tools.Media.typeTelevision(media): type = 'episode'
	else: type = 'movie'
	if plural and not type.endswith('s'): type += 's'
	return media, type

##############################################################################
# PROGRESS - CLEAR
##############################################################################

def progressClear(media, wait = True):
	def _progressClear(media):
		global TraktProgress
		TraktProgress = {}
		media, type = progressType(media = media, plural = True) # This endpoint uses plural, therefore add "s".
		Cache.instance().cacheDelete(getTraktAsJson, '/sync/playback/' + type)
	if wait: _progressClear(media = media)
	else: Pool.thread(target = _progressClear, kwargs = {'media' : media}, start = True)

def progressClearMovie(wait = True):
	progressClear(media = tools.Media.TypeMovie, wait = wait)

def progressClearShow(wait = True):
	progressClear(media = tools.Media.TypeShow, wait = wait)

##############################################################################
# PROGRESS - REFRESH
##############################################################################

def progressRefresh(media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, wait = True):
	def _progressRefresh(media, imdb, tmdb, tvdb, trakt, season, episode):
		progressClear(media = media, wait = True)
		progressRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
	if wait: _progressRefresh(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
	else: Pool.thread(target = _progressRefresh, kwargs = {'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode}, start = True)

def progressRefreshMovie(imdb = None, tmdb = None, tvdb = None, trakt = None, wait = True):
	progressRefresh(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, wait = wait)

def progressRefreshShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, wait = True):
	progressRefresh(media = tools.Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, wait = wait)

##############################################################################
# PROGRESS - RETRIEVE
##############################################################################

def progressRetrieve(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, limit = None, attribute = 'progress'):
	try:
		media, type = progressType(media = media, season = season, episode = episode)

		ids = {}
		if not imdb is None: ids['imdb'] = str(imdb)
		if not tmdb is None: ids['tmdb'] = int(tmdb)
		if not tvdb is None: ids['tvdb'] = int(tvdb)
		if not trakt is None: ids['trakt'] = int(trakt)
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)

		link = '/sync/playback/' + type + 's' # This endpoint uses plural, therefore add "s".

		# Use global var to improve speeds, especially for batch requests where this function is called multiple times for different movies/episodes.
		global TraktProgress
		if not link in TraktProgress: TraktProgress[link] = Cache.instance().cacheMini(getTraktAsJson, link)
		items = TraktProgress[link]

		if items:
			if tools.Media.typeTelevision(media):
				if season is None and episode is None: # Return any episode that still has progress.
					for id in ids.keys():
						for item in items:
							try:
								if 'show' in item and id in item['show']['ids'] and item['show']['ids'][id] == ids[id]:
									if limit:
										if item['progress'] > limit[0] and item['progress'] < limit[1]: return item[attribute]
										else: return 0 if attribute == 'progress' else None # Avoid lookup in local database.
									else: return item[attribute]
							except: tools.Logger.error()
				elif episode is None: # Return any episode that still has progress.
					for id in ids.keys():
						for item in items:
							try:
								if 'show' in item and 'episode' in item and id in item['show']['ids'] and item['show']['ids'][id] == ids[id]:
									if item['episode']['season'] == season:
										if limit:
											if item['progress'] > limit[0] and item['progress'] < limit[1]: return item[attribute]
											else: return 0 if attribute == 'progress' else None # Avoid lookup in local database.
										else: return item[attribute]
							except: tools.Logger.error()
				else:
					for id in ids.keys():
						for item in items:
							try:
								if 'show' in item and 'episode' in item and id in item['show']['ids'] and item['show']['ids'][id] == ids[id]:
									if item['episode']['season'] == season and item['episode']['number'] == episode:
										if limit:
											if item[attribute] > limit[0] and item['progress'] < limit[1]: return item[attribute]
											else: return 0 if attribute == 'progress' else None # Avoid lookup in local database.
										else: return item[attribute]
							except: tools.Logger.error()
			else:
				for id in ids.keys():
					for item in items:
						try:
							if 'movie' in item and id in item['movie']['ids'] and item['movie']['ids'][id] == ids[id]:
								if limit:
									if item['progress'] > limit[0] and item['progress'] < limit[1]: return item[attribute]
									else: return 0 if attribute == 'progress' else None # Avoid lookup in local database.
								else: return item[attribute]
						except: tools.Logger.error()
	except: tools.Logger.error()
	return None

def progressRetrieveMovie(imdb = None, tmdb = None, tvdb = None, trakt = None, limit = None):
	return progressRetrieve(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, limit = limit)

def progressRetrieveShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, limit = None):
	return progressRetrieve(media = tools.Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, limit = limit)

##############################################################################
# PROGRESS - UPDATE
##############################################################################

# action = start, pause, stop
# media = tools.Media.Type
# progress = float in [0, 100]
def progressUpdate(action, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, progress = 0, force = False, wait = False):
	result = False
	try:
		if action:
			media, type = progressType(media = media, season = season, episode = episode)

			# Trakt automatically marks items as watched if the action is "stop" and the progress is above 80%.
			# The API documentation states to use the "pause" action if the the threshold should be greater than 80%.
			stop = action == 'stop'
			if not force and stop: action = 'pause'

			if not season is None: season = int(season)
			if not episode is None: episode = int(episode)

			if tools.Media.typeTelevision(media): item = SearchTVShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, single = True)
			else: item = SearchMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, single = True)

			if item:
				if tools.Media.typeTelevision(media):
					slug = item['show']['ids']['slug']
					link = '/shows/%s/seasons/%d/episodes/%d' % (slug, season, episode)
					item = Cache.instance().cacheLong(getTraktAsJson, link)
				else:
					item = item['movie']

				if item:
					link = '/scrobble/' + action
					data = {
						type : item,
						'progress' : progress,
						'app_version' : tools.System.version(),
					}
					result = getTraktAsJson(url = link, post = data)
					result = bool(result and 'progress' in result)

			# Make sure that NEW values are retrieved in progressRetrieve() and not the old cached values.
			# Refresh if stopped, so that next retrieval is faster.
			# Only clear, instead of a full refresh, on play/pause, otherwise there will be too many requests that are not needed until the video is stopped.
			if stop: progressRefresh(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, wait = wait)
			else: progressClear(media = media)
	except: tools.Logger.error()
	return result

def progressUpdateMovie(action, imdb = None, tmdb = None, tvdb = None, trakt = None, progress = 0, force = False, wait = False):
	return progressUpdate(action = action, media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, progress = progress, force = force, wait = wait)

def progressUpdateShow(action, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, progress = 0, force = False, wait = False):
	return progressUpdate(action = action, media = tools.Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, progress = progress, force = force, wait = wait)

##############################################################################
# PROGRESS - REMOVE
##############################################################################

def progressRemove(media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, wait = False):
	result = False
	try:
		id = progressRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, attribute = 'id')
		if not id is None:
			link = '/sync/playback/' + str(id)
			getTrakt(link, method = network.Networker.MethodDelete)

			progressRefresh(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, wait = wait)
	except: tools.Logger.error()
	return result

def progressRemoveMovie(imdb = None, tmdb = None, tvdb = None, trakt = None, wait = False):
	return progressRemove(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, wait = wait)

def progressRemoveShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, wait = False):
	return progressRemove(media = tools.Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, wait = wait)

##############################################################################
# RATING - GENERAL
##############################################################################

TraktRating = {}

def ratingType(media, season = None, episode = None, plural = True, general = False):
	if general and tools.Media.typeTelevision(media): type = 'show'
	elif media == tools.Media.TypeShow: type = 'show'
	elif media == tools.Media.TypeSeason: type = 'season'
	elif media == tools.Media.TypeEpisode: type = 'episode'
	else: type = 'movie'

	if plural and not type.endswith('s'): type += 's'
	return media, type

##############################################################################
# RATING - CLEAR
##############################################################################

def ratingClear(media, wait = True):
	def _ratingClear(media):
		global TraktRating
		TraktRating = {}
		media, type = ratingType(media = media)
		Cache.instance().cacheDelete(getTraktAsJson, '/sync/ratings/' + type)
	if wait: _ratingClear(media = media)
	else: Pool.thread(target = _ratingClear, kwargs = {'media' : media}, start = True)

def ratingClearMovie(wait = True):
	ratingClear(media = tools.Media.TypeMovie, wait = wait)

def ratingClearShow(wait = True):
	ratingClear(media = tools.Media.TypeShow, wait = wait)

##############################################################################
# RATING - REFRESH
##############################################################################

def ratingRefresh(media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, wait = True):
	def _ratingRefresh(media, imdb, tmdb, tvdb, trakt, season, episode):
		ratingClear(media = media, wait = True)
		ratingRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
	if wait: _ratingRefresh(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
	else: Pool.thread(target = _ratingRefresh, kwargs = {'media' : media, 'imdb' : imdb, 'tmdb' : tmdb, 'tvdb' : tvdb, 'trakt' : trakt, 'season' : season, 'episode' : episode}, start = True)

def ratingRefreshMovie(imdb = None, tmdb = None, tvdb = None, trakt = None, wait = True):
	ratingRefresh(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, wait = wait)

def ratingRefreshShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, wait = True):
	ratingRefresh(media = tools.Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, wait = wait)

##############################################################################
# RATING - RETRIEVE
##############################################################################

def ratingRetrieve(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, attribute = 'rating'):
	try:
		media, type = ratingType(media = media, season = season, episode = episode)

		ids = {}
		if not imdb is None: ids['imdb'] = str(imdb)
		if not tmdb is None: ids['tmdb'] = int(tmdb)
		if not tvdb is None: ids['tvdb'] = int(tvdb)
		if not trakt is None: ids['trakt'] = int(trakt)
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)

		link = '/sync/ratings/' + type

		# Use global var to improve speeds, especially for batch requests where this function is called multiple times for different movies/episodes.
		global TraktRating
		if not link in TraktRating: TraktRating[link] = Cache.instance().cacheMini(getTraktAsJson, link)
		items = TraktRating[link]

		if items:
			if tools.Media.typeTelevision(media):
				if season is None and episode is None: # Return any episode that still has progress.
					for id in ids.keys():
						for item in items:
							try:
								if 'show' in item and id in item['show']['ids'] and item['show']['ids'][id] == ids[id]:
									return item[attribute] if attribute else {'rating' : item['rating'], 'time' : tools.Time.timestamp(item['rated_at'], iso = True)}
							except: tools.Logger.error()
				elif episode is None: # Return any episode that still has progress.
					for id in ids.keys():
						for item in items:
							try:
								if 'show' in item and 'episode' in item and id in item['show']['ids'] and item['show']['ids'][id] == ids[id]:
									if item['episode']['season'] == season:
										return item[attribute] if attribute else {'rating' : item['rating'], 'time' : tools.Time.timestamp(item['rated_at'], iso = True)}
							except: tools.Logger.error()
				else:
					for id in ids.keys():
						for item in items:
							try:
								if 'show' in item and 'episode' in item and id in item['show']['ids'] and item['show']['ids'][id] == ids[id]:
									if item['episode']['season'] == season and item['episode']['number'] == episode:
										return item[attribute] if attribute else {'rating' : item['rating'], 'time' : tools.Time.timestamp(item['rated_at'], iso = True)}
							except: tools.Logger.error()
			else:
				for id in ids.keys():
					for item in items:
						try:
							if 'movie' in item and id in item['movie']['ids'] and item['movie']['ids'][id] == ids[id]:
								return item[attribute] if attribute else {'rating' : item['rating'], 'time' : tools.Time.timestamp(item['rated_at'], iso = True)}
						except: tools.Logger.error()
	except: tools.Logger.error()
	return None

def ratingRetrieveMovie(imdb = None, tmdb = None, tvdb = None, trakt = None):
	return ratingRetrieve(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

def ratingRetrieveShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
	return ratingRetrieve(media = tools.Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

##############################################################################
# RATING - UPDATE
##############################################################################

def ratingUpdateTime(items = None, time = None):
	if items and time:
		if tools.Tools.isInteger(time): time = timeFormat(time)
		for i in items:
			i['rated_at'] = time
			if 'seasons' in i:
				for j in i['seasons']:
					j['rated_at'] = time
					if 'episodes' in j:
						for k in j['episodes']:
							k['rated_at'] = time
	return items

# rating = integer in [1, 10]
def ratingUpdate(rating, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, time = None, items = None, wait = False):
	result = False
	try:
		media, type = ratingType(media = media, season = season, episode = episode, general = True)
		items = request(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, rating = rating, items = items)
		items = ratingUpdateTime(items = items, time = time)
		result = getTraktAsJson('/sync/ratings', {type : items}, timeout = timeout(items))
		if refresh: ratingRefresh(media = media, wait = wait)
	except: tools.Logger.error()
	return result

def ratingUpdateMovie(rating, imdb = None, tmdb = None, tvdb = None, trakt = None, time = None, items = None, wait = False):
	return ratingUpdate(rating = rating, media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, time = time, items = items, wait = wait)

def ratingUpdateShow(rating, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, time = None, items = None, wait = False):
	return ratingUpdate(rating = rating, media = tools.Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, time = time, items = items, wait = wait)

##############################################################################
# RATING - REMOVE
##############################################################################

def ratingRemove(media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, wait = False):
	result = False
	try:
		media, type = ratingType(media = media, season = season, episode = episode, general = True)
		items = request(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items)
		result = getTraktAsJson('/sync/ratings/remove', {type : items}, timeout = timeout(items))
		if refresh: ratingRefresh(media = media, wait = wait)
	except: tools.Logger.error()
	return result

def ratingRemoveMovie(imdb = None, tmdb = None, tvdb = None, trakt = None, items = None, wait = False):
	return ratingRemove(media = tools.Media.TypeMovie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, items = items, wait = wait)

def ratingRemoveShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, wait = False):
	return ratingRemove(media = tools.Media.TypeShow, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, wait = wait)

##############################################################################
# IMDB IMPORT
##############################################################################

def imdbImportCheck(importWatched, importRatings):
	from lib.indexers.movies import Movies

	def check(method, result, index):
		indexer = Movies(type = tools.Media.TypeMovie)
		getattr(indexer, method)()
		result[index] = indexer.imdbPublic()

	threads = []
	values = [None, None]
	if any(importWatched):
		values[0] = False
		threads.append(Pool.thread(target = check, args = ('imdbUserWatched', values, 0)))
	if any(importRatings):
		values[1] = False
		threads.append(Pool.thread(target = check, args = ('imdbUserRatings', values, 1)))

	[i.start() for i in threads]
	[i.join() for i in threads]
	return values[0], values[1]

def imdbImportRetrieve(importWatched, importRatings, ratings):
	from lib.indexers.movies import Movies
	from lib.indexers.shows import Shows

	def retrieve(type, method, result, index):
		if tools.Media.typeTelevision(type): result[index] = getattr(Shows(), method)()
		else: result[index] = getattr(Movies(type = type), method)()

	threads = []
	valuesWatched = [None, None, None, None]
	valuesRatings = [None, None, None, None]

	if importWatched[0]: threads.append(Pool.thread(target = retrieve, args = (tools.Media.TypeMovie, 'imdbUserWatched', valuesWatched, 0)))
	if importWatched[1]: threads.append(Pool.thread(target = retrieve, args = (tools.Media.TypeDocumentary, 'imdbUserWatched', valuesWatched, 1)))
	if importWatched[2]: threads.append(Pool.thread(target = retrieve, args = (tools.Media.TypeShort, 'imdbUserWatched', valuesWatched, 2)))
	if importWatched[3]: threads.append(Pool.thread(target = retrieve, args = (tools.Media.TypeShow, 'imdbUserWatched', valuesWatched, 3)))

	if importRatings[0]: threads.append(Pool.thread(target = retrieve, args = (tools.Media.TypeMovie, 'imdbUserRatings', valuesRatings, 0)))
	if importRatings[1]: threads.append(Pool.thread(target = retrieve, args = (tools.Media.TypeDocumentary, 'imdbUserRatings', valuesRatings, 1)))
	if importRatings[2]: threads.append(Pool.thread(target = retrieve, args = (tools.Media.TypeShort, 'imdbUserRatings', valuesRatings, 2)))
	if importRatings[3]: threads.append(Pool.thread(target = retrieve, args = (tools.Media.TypeShow, 'imdbUserRatings', valuesRatings, 3)))

	[i.start() for i in threads]
	[i.join() for i in threads]

	if ratings:
		if importWatched[0] and importRatings[0]: valuesWatched[0] = Movies(type = tools.Media.TypeMovie).imdbUserAccount(ratings = valuesRatings[0], watched = valuesWatched[0])
		if importWatched[1] and importRatings[1]: valuesWatched[1] = Movies(type = tools.Media.TypeDocumentary).imdbUserAccount(ratings = valuesRatings[1], watched = valuesWatched[1])
		if importWatched[2] and importRatings[2]: valuesWatched[2] = Movies(type = tools.Media.TypeShort).imdbUserAccount(ratings = valuesRatings[2], watched = valuesWatched[2])
		if importWatched[3] and importRatings[3]: valuesWatched[3] = Shows().imdbUserAccount(ratings = valuesRatings[3], watched = valuesWatched[3])

	return valuesWatched, valuesRatings

def imdbImportSync(itemsWatched, itemsRatings):
	def syncWatched(type, items):
		if tools.Media.typeTelevision(type): historyUpdateShow(items = items)
		else: historyUpdateMovie(items = items)

	def syncRatings(type, items):
		if tools.Media.typeTelevision(type): ratingUpdateShow(items = items)
		else: ratingUpdateMovie(items = items)

	threads = []

	if itemsWatched[0]: threads.append(Pool.thread(target = syncWatched, args = (tools.Media.TypeMovie, itemsWatched[0])))
	if itemsWatched[1]: threads.append(Pool.thread(target = syncWatched, args = (tools.Media.TypeDocumentary, itemsWatched[1])))
	if itemsWatched[2]: threads.append(Pool.thread(target = syncWatched, args = (tools.Media.TypeShort, itemsWatched[2])))
	if itemsWatched[3]: threads.append(Pool.thread(target = syncWatched, args = (tools.Media.TypeShow, itemsWatched[3])))

	if itemsRatings[0]: threads.append(Pool.thread(target = syncRatings, args = (tools.Media.TypeMovie, itemsRatings[0])))
	if itemsRatings[1]: threads.append(Pool.thread(target = syncRatings, args = (tools.Media.TypeDocumentary, itemsRatings[1])))
	if itemsRatings[2]: threads.append(Pool.thread(target = syncRatings, args = (tools.Media.TypeShort, itemsRatings[2])))
	if itemsRatings[3]: threads.append(Pool.thread(target = syncRatings, args = (tools.Media.TypeShow, itemsRatings[3])))

	[i.start() for i in threads]
	[i.join() for i in threads]

def imdbImport():
	if interface.Dialog.option(title = 32034, message = 35610):
		yes = interface.Format.fontBold(interface.Format.fontColor(interface.Translation.string(33341), interface.Format.colorExcellent()))
		no = interface.Format.fontBold(interface.Format.fontColor(interface.Translation.string(33342), interface.Format.colorBad()))

		importWatched = [True, True, True, True]
		importRatings = [True, True, True, True]

		initial = True
		while initial:
			choice = 1
			while choice > 0:
				items = [
					interface.Format.fontBold(interface.Translation.string(33821)),

					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(32001), interface.Translation.string(32033))) + (yes if importWatched[0] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(33470), interface.Translation.string(32033))) + (yes if importWatched[1] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(33471), interface.Translation.string(32033))) + (yes if importWatched[2] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(32002), interface.Translation.string(32033))) + (yes if importWatched[3] else no),

					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(32001), interface.Translation.string(35602))) + (yes if importRatings[0] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(33470), interface.Translation.string(35602))) + (yes if importRatings[1] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(33471), interface.Translation.string(35602))) + (yes if importRatings[2] else no),
					interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(35212), interface.Translation.string(32002), interface.Translation.string(35602))) + (yes if importRatings[3] else no),
				]
				choice = interface.Dialog.select(title = 32034, items = items)
				if choice < 0: return False
				elif choice == 0: break
				elif choice < 5: importWatched[choice - 1] = not importWatched[choice - 1]
				else: importRatings[choice - 5] = not importRatings[choice - 5]

			while True:
				publicWatched, publicRatings = imdbImportCheck(importWatched, importRatings)
				if publicWatched is False:
					if interface.Dialog.option(title = 32034, message = 35608, labelConfirm = 35606, labelDeny = 35374): continue
				elif publicRatings is False:
					if interface.Dialog.option(title = 32034, message = 35609, labelConfirm = 35606, labelDeny = 35374): continue
				else:
					initial = False
				break

		ratings = interface.Dialog.option(title = 32034, message = 35611) if any(importRatings) else False
		itemsWatched, itemsRatings = imdbImportRetrieve(importWatched, importRatings, ratings)

		items = [interface.Format.fontBold(interface.Translation.string(33821))]
		if not itemsWatched[0] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(32001), interface.Translation.string(32033), interface.Translation.string(35607))) + str(len(itemsWatched[0])))
		if not itemsWatched[1] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(33470), interface.Translation.string(32033), interface.Translation.string(35607))) + str(len(itemsWatched[1])))
		if not itemsWatched[2] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(33471), interface.Translation.string(32033), interface.Translation.string(35607))) + str(len(itemsWatched[2])))
		if not itemsWatched[3] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(32002), interface.Translation.string(32033), interface.Translation.string(35607))) + str(len(itemsWatched[3])))
		if not itemsRatings[0] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(32001), interface.Translation.string(35602), interface.Translation.string(35607))) + str(len(itemsRatings[0])))
		if not itemsRatings[1] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(33470), interface.Translation.string(35602), interface.Translation.string(35607))) + str(len(itemsRatings[1])))
		if not itemsRatings[2] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(33471), interface.Translation.string(35602), interface.Translation.string(35607))) + str(len(itemsRatings[2])))
		if not itemsRatings[3] is None: items.append(interface.Format.fontBold('%s %s %s: ' % (interface.Translation.string(32002), interface.Translation.string(35602), interface.Translation.string(35607))) + str(len(itemsRatings[3])))
		choice = interface.Dialog.select(title = 32034, items = items)
		if choice < 0: return False

		if interface.Dialog.option(title = 32034, message = 35612):
			interface.Loader.show()
			imdbImportSync(itemsWatched, itemsRatings)
			interface.Loader.hide()
			interface.Dialog.confirm(title = 32034, message = 35613)
			return True

	interface.Loader.hide()
	return False
