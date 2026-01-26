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
from lib.modules.cache import Cache, Memory
from lib.modules.convert import ConverterTime
from lib.modules.concurrency import Pool
from lib.modules.account import Trakt as Account

TraktId = None
TraktClient = None
TraktAccount = None
TraktCache = None
TraktLimit = None
TraktWait = None

def reset(settings = True):
	global TraktCache
	TraktCache = None

	if settings:
		global TraktAccount
		TraktCache = None

def log(message, size = None, developer = True):
	if not developer or tools.System.developer():
		if size:
			label = 'B'
			try: size = size['compressed'] or 0 # Can be None on failure.
			except: size = 0
			if size >= 1024:
				size /= 1024.0
				label = 'KB'
			if size >= 1024:
				size /= 1024.0
				label = 'MB'
			message += ' [+-%d%s]' % (int(size), label)

		tools.Logger.log(message, name = 'TRAKT', developer = True)

def getTraktAccount():
	global TraktAccount
	if TraktAccount is None: TraktAccount = Account.instance()
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

def getTrakt(url, post = None, headers = None, retry = True, timestamp = None, extended = False, direct = False, method = None, authentication = None, timeout = network.Networker.TimeoutLong, limit = None, full = None):
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

		# Do not do this for GET requests from MetaTrakt.
		if post and not tools.Tools.isString(post) and not method == network.Networker.MethodGet: post = tools.Converter.jsonTo(post)

		# Some features, like searching, can be done without user authentication.
		# Actually, all endpoints not associated with a user (eg mark as watched, sync rating, etc) do NOT require authentication.
		# So getting movie/show/people summary, searching, getting external IDs, etc can be done without authentication.
		if direct or not valid:
			result = network.Networker().request(method = method, link = url, data = post, headers = headers, timeout = timeout)

			try: code = result['error']['code']
			except: code = None
			if code is None:
				try: code = result['status']['code']
				except: code = None
			if not code:
				try: error = result['error']['type']
				except: error = None
				if error == network.Networker.ErrorConnection or error == network.Networker.ErrorTimeout:
					code = -1 # This should hopefully be set if the Trakt server is down.
			code = code if tools.Tools.isNumber(code) else 0

			data = network.Networker.dataText(result['data'])

			if code == 429: # Rate limit reached.
				limit = _limit(url = url, data = result, wait = limit)
				if limit:
					return getTrakt(url = url, post = post, retry = retry, timestamp = timestamp, extended = extended, direct = direct, method = method, authentication = authentication, timeout = timeout, limit = limit)
				else:
					if extended and result['error']: result['error']['trakt'] = 'limit'
			elif (not data and code == -1) or (not data and code >= 300 and not(code == 404 or code == 401 or code == 405)) or (code >= 500 and code <= 599) or (data and tools.Tools.isString(data) and '<html' in data): # Server errors.
				_error(url = url, post = post, timestamp = timestamp, retry = retry, message = 33676)
				if extended and result['error']: result['error']['trakt'] = 'server'

			if extended: return data, result['headers'], result['error']
			else: return data

		headers['Authorization'] = 'Bearer %s' % token
		result = network.Networker().request(method = method, link = url, data = post, headers = headers, timeout = timeout)

		try: code = result['error']['code']
		except: code = None
		if code is None:
			try: code = result['status']['code']
			except: code = None
		if not code:
			try: error = result['error']['type']
			except: error = None
			if error == network.Networker.ErrorConnection or error == network.Networker.ErrorTimeout:
				code = -1 # This should hopefully be set if the Trakt server is down.
		code = code if tools.Tools.isNumber(code) else 0

		data = network.Networker.dataText(result['data'])

		# Sometimes Trakt returns an HTML page containing something like: <title>api.trakt.tv | 502: Bad gateway</title>
		# This is typically a temporay problem, sometimes only lasting a few seconds/minutes.
		# Might be a Cloudflare redirection issue, or maybe a Trakt server restart.
		if code == 429: # Rate limit reached.
			limit = _limit(url = url, data = result, wait = limit)
			if limit:
				return getTrakt(url = url, post = post, retry = retry, timestamp = timestamp, extended = extended, direct = direct, method = method, authentication = authentication, timeout = timeout, limit = limit)
			else:
				if extended:
					if result['error']: result['error']['trakt'] = 'limit'
					return None, result['headers'], result['error']
				else: return None
		elif (not data and code == -1) or (not data and code >= 300 and not(code == 404 or code == 401 or code == 405)) or (code >= 500 and code <= 599) or (data and tools.Tools.isString(data) and '<html' in data): # Server errors.
			_error(url = url, post = post, timestamp = timestamp, retry = retry, message = 33676)
			if extended:
				if result['error']: result['error']['trakt'] = 'server'
				return None, result['headers'], result['error']
			else: return None
		elif data and not(code == 401 or code == 405): # Returned valid data without failing authorization.
			if extended: return data, result['headers'], result['error']
			else: return data
		elif code == 404: # Movie/show cannot be found.
			#_error(url = url, post = post, timestamp = timestamp, retry = False, message = 33786) # Do not show notifications if some movie data cannot be found.
			if extended: return None, result['headers'], result['error']
			else: return None
		elif code >= 200 and code <= 299 and method in [network.Networker.MethodPost, network.Networker.MethodDelete, network.Networker.MethodPut]:
			# For requests that do not return data, such as deleting playback progress from progressRemove(), which returns code 204, but no data.
			if extended: return data, result['headers'], result['error']
			else: return data

		oauth = 'https://api.trakt.tv/oauth/token'
		opost = {'client_id': getTraktId(), 'client_secret': getTraktClient(), 'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob', 'grant_type': 'refresh_token', 'refresh_token': refresh}

		result = network.Networker().request(link = oauth, type = network.Networker.DataJson, data = opost, headers = headers, timeout = timeout)
		try: code = result['error']['code']
		except: code = None
		if code is None:
			try: code = result['status']['code']
			except: code = None
		if not code:
			try: error = result['error']['type']
			except: error = None
			if error == network.Networker.ErrorConnection or error == network.Networker.ErrorTimeout:
				code = -1
		code = code if tools.Tools.isNumber(code) else 0

		data = network.Networker.dataText(result['data'])

		if code == 429: # Rate limit reached.
			limit = _limit(url = url, data = result, wait = limit)
			if limit:
				return getTrakt(url = url, post = post, retry = retry, timestamp = timestamp, extended = extended, direct = direct, method = method, authentication = authentication, timeout = timeout, limit = limit)
			else:
				if extended:
					if result['error']: result['error']['trakt'] = 'limit'
					return None, result['headers'], result['error']
				else: return None
		elif (not data and code == -1) or (not data and code >= 300 and not(code == 404 or code == 401 or code == 405)) or (code >= 500 and code <= 599) or (data and tools.Tools.isString(data) and '<html' in data): # Server errors.
			_error(url = url, post = post, timestamp = timestamp, retry = retry, message = 33676)
			if extended:
				if result['error']: result['error']['trakt'] = 'server'
				return None, result['headers'], result['error']
			else: return None
		elif code == 401 or code == 405 or (code == 400 and data and tools.Tools.isString(data) and 'invalid_grant' in data): # Oauth token failed.
			_error(url = url, post = post, timestamp = timestamp, retry = False, message = 33677)
			if not full is None: # Used from authenticationCheck().
				full['data'] = data
				full['headers'] = result['headers']
				full['error'] = result['error']
				full['code'] = code
			if extended: return None, result['headers'], result['error']
			else: return None
		elif code == 404: # Movie/show cannot be found.
			#_error(url = url, post = post, timestamp = timestamp, retry = False, message = 33786) # Do not show notifications if some movie data cannot be found.
			if extended: return None, result['headers'], result['error']
			else: return None

		data = tools.Converter.jsonFrom(data)

		getTraktAccount().update(token = data['access_token'], refresh = data['refresh_token'])
		valid = authenticated()
		token = getTraktToken()

		headers['Authorization'] = 'Bearer %s' % token
		result = network.Networker().request(method = method, link = url, data = post, headers = headers, timeout = timeout)

		if extended: return network.Networker.dataText(result['data']), result['headers'], result['error']
		else: return network.Networker.dataText(result['data'])
	except: tools.Logger.error()

	if extended: return None, None, None
	else: return None


def _error(url, post, timestamp, message, retry = None):
	try:
		_cacheAdd(url = url, post = post, timestamp = timestamp, retry = retry)

		if tools.Settings.getBoolean('account.trakt.notifications'):
			id = 'GaiaTraktError'
			time = tools.Time.timestamp()
			previous = Memory.get(id = id, message = message, local = True, kodi = True)

			# Only show this notification every max 10 minutes.
			if not previous or (time - previous) > 600:
				Memory.set(value = time, id = id, message = message, local = True, kodi = True)
				interface.Dialog.notification(title = 32315, message = message, icon = interface.Dialog.IconError)
	except: tools.Logger.error()

def _errorIs(error, data = None):
	if not data:
		if tools.Tools.isDictionary(error): return bool(error.get('type') or error.get('code'))
		elif error: return True
	return False

def _cacheAdd(url, post = None, timestamp = None, retry = None):
	# Only cache certain POST requests that will update the users history, ratings, playback, etc.
	# Do not cache general requests, especially GET requests.
	# Otherwise if Trakt goes down and comes back again, a shit ton of requests will be submitted that that user probably does not need anymore.
	# Hence, only cache and retry update requests.
	# Make sure to exclude the GET syn requests. Eg: sync/ratings/<type>
	try:
		if retry: # Only add to the cache if this requests is not a retry itself.
			if tools.Regex.match(data = url, expression = r'\/sync\/(?:(?:history|ratings|watchlist|favorites|collection)(?:$|\/?\?|\/(?:remove|reorder))|playback\/\d)'):
				global TraktCache
				TraktCache = True
				return Cache.instance().traktCache(link = url, data = post, timestamp = timestamp)
	except: tools.Logger.error()

def cacheRetry(force = False, probability = True, wait = False):
	# Only execute this function under certain circumstances:
	#	1. Forced retry done once when Gaia is launched.
	#	2. Retry if a Trakt request failed in the current script execution.
	#	3. Retry every now and then with a small probability (5%).
	# We do not want to retry all the time at the end of every script execution.
	# Otherwise if Trakt is down for a long time, this will make unnecessary requests every time an action is done in Gaia, and the retry will probably fail anyways.
	try:
		global TraktCache
		if force or TraktCache or (probability and tools.Math.randomProbability(probability = 0.05 if probability is True else probability)):
			if wait: _cacheRetry(force = force, probability = probability)
			else: Pool.thread(target = _cacheRetry, kwargs = {'force' : force, 'probability' : probability}, start = True)
	except: tools.Logger.error()

def _cacheRetry(force = False, probability = True):
	try:
		instance = Cache.instance()
		time = tools.Time.timestamp()

		item = None
		error = None
		while True:
			item = instance.traktRetrieve()
			if not item: break

			# Only do this if the request is younger than a month (4 weeks).
			# If Trakt is down for more than a month, something is seriously wrong, and we probably do not want to submit these retries anyways.
			# Or the user has not used Kodi/Gaia for a month after the server downtime. Then we probably also do not want to submit these, since the user probably marked stuff on Trakt manually since then.
			if (time - item['time']) < 2419200:
				# Important to set "retry = False", otherwise the requests might be queued again.
				result, headers, error = getTrakt(url = item['link'], post = tools.Converter.jsonFrom(item['data']) if item['data'] else None, retry = False, timestamp = item['time'], extended = True)
				if _errorIs(error, data = result): break # Trakt still down. Do not containue with other requests.

			instance.traktDelete(item['id'])
			tools.Time.sleep(1.0) # POST requests limit: 1 requests per 1 sec.

		# Refresh if the requests were successful.
		if item and not _errorIs(error): self.refresh()
	except: tools.Logger.error()

def _limit(url = None, data = None, wait = False):
	# https://trakt.docs.apiary.io/#introduction/rate-limiting
	# Trakt does not strictly enforce these limits. Sometimes a few thousand requests can be made before Trakt returns HTTP 429.

	# Update (2025-12):
	# NB: It seems that Trakt does not always include the X-Ratelimit header.
	# Often only Retry-After=xxx and Status=429 headers are returned.
	# Maybe once the limit was reached and continues requests are being made, the header is not added anymore?
	# But even the first request hitting the limit does not seem to have this header anymore.
	# Maybe they permanently removed it?
	try: limit = tools.Converter.jsonFrom(data['headers']['X-Ratelimit'])
	except: limit = None
	try: seconds = int(data['headers']['Retry-After'])
	except: seconds = None

	if wait is None:
		global TraktLimit
		wait = TraktLimit
		if wait is None and not seconds is None:
			if (limit and 'name' in limit and limit['name'] == 'AUTHED_API_POST_LIMIT'):
				wait = 10 # Retry 10 times, since this is important (eg update watched status, progress, etc).
			elif (seconds < 2):
				wait = 1 # Retry only once, and then fail.

	if not seconds is None:
		global TraktWait
		TraktWait = max(TraktWait or 0, tools.Time.timestamp() + seconds + (1 if seconds > 2 else 0))

	if wait and not seconds is None:
		seconds += (0.5 if seconds < 3 else 1 if seconds < 10 else 2)

		if wait is True: retry = 'an infinite number of times'
		elif wait == 1: retry = '1 time'
		else: retry = '%d times' % wait

		tools.Logger.log('Trakt rate limit reached. Retrying %s in %d secs.' % (retry, seconds))
		tools.Logger.log('     Link: %s' % str(url))
		tools.Logger.log('     Wait: %s secs' % str(seconds))
		tools.Logger.log('     Response: %s' % tools.Converter.jsonTo(limit))

		tools.Time.sleep(seconds)
		result = max(0, limit - 1) if tools.Tools.isInteger(limit) else True

		if result:
			tools.Logger.log('Retrying after Trakt rate limit reached.')
			tools.Logger.log('     Link: %s' % str(url))
			tools.Logger.log('     Wait: %s secs' % str(seconds))
		else:
			tools.Logger.log('Not retrying after Trakt rate limit reached.')
			tools.Logger.log('     Link: %s' % str(url))
			tools.Logger.log('     Wait: %s secs' % str(seconds))

		return result
	else:
		tools.Logger.log('Trakt rate limit reached. Aborting request without retrying.')
		tools.Logger.log('     Link: %s' % str(url))
		tools.Logger.log('     Wait: %s secs' % str(seconds))
		tools.Logger.log('     Response: %s' % tools.Converter.jsonTo(limit))
		return False

def _limitEnable(enabled = True):
	global TraktLimit
	TraktLimit = enabled

def limitWait():
	global TraktWait
	return TraktWait

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
				Account.AttributeLinked : network.Networker.linkJoin(result['verification_url'], result['user_code']),
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

# Check if the access token still works and otherwise show the authentication dialog.
def authenticationCheck(loader = False):
	if authenticated():
		full = {}

		if loader: interface.Loader.show()
		data, headers, error = getTrakt(url = '/sync/last_activities', extended = True, full = full)
		if loader: interface.Loader.hide()

		code = full.get('code')
		data = full.get('data')
		if code == 401 or code == 405 or (code == 400 and data and tools.Tools.isString(data) and 'invalid_grant' in data):
			interface.Dialog.confirm(title = 32315, message = 36907)
			getTraktAccount().clear()
			return authentication(settings = False)
		else:
			return True
	return None

def authenticated():
	return getTraktAccount().authenticated()

def manager(media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
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

		if not media:
			if not episode is None: media = tools.Media.Episode
			elif not season is None: media = tools.Media.Season
			elif tvdb: media = tools.Media.Show
			else: media = tools.Media.Movie

		items = [
			{'title' : interface.Dialog.prefixBack(33486), 'close' : True},
			{
				'title' : 32310,
				'items' : [
					{'title' : 33678, 'value' : 33924, 'return' : 'refresh'},
					{'title' : 33979, 'value' : 33923, 'return' : 'reset'} if (media == tools.Media.Movie or not episode is None) else None,
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
	name = re.sub(r'[^a-z0-9_]', '-', name)
	name = re.sub(r'--+', '-', name)
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

		if cache: item = getTraktCache(function = Cache.instance().cacheExtended, url = url, failsafe = failsafe)
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
		if cache: return getTraktCache(function = Cache.instance().cacheExtended, url = url, failsafe = failsafe)
		else: return getTraktAsJson(url = url)
	except: tools.Logger.error()
	return None

def getTVShowSummary(id, full = True, cache = True, failsafe = False):
	try:
		url = '/shows/%s' % id
		if full: url += '?extended=full'
		if cache: return getTraktCache(function = Cache.instance().cacheExtended, url = url, failsafe = failsafe)
		else: return getTraktAsJson(url = url)
	except: tools.Logger.error()
	return None

def getTVSeasonSummary(id, season = None, lang = None, full = True, cache = True, failsafe = False):
	try:
		url = '/shows/%s/seasons' % id
		if not season is None: url += '/%d' % season
		if full: url += '?extended=full'
		if lang: url += '%stranslations=%s' % ('&' if full else '?', lang)
		if cache: return getTraktCache(function = Cache.instance().cacheExtended, url = url, failsafe = failsafe)
		else: return getTraktAsJson(url = url)
	except: tools.Logger.error()
	return None

def sortHas(headers):
	if headers:
		headers = dict((k.lower(), v) for k, v in headers.items())
		sort = headers.get('x-sort-by')
		if sort: return True
	return False

def sortList(data, sort = None, order = None, headers = None):
	try:
		if data and tools.Tools.isArray(data):
			# NB: Trakt seems to switch asc/desc value in the list settings.
			# Eg: Edit the list settings to use asc. Then reload the list website witrhout any GET parameter. Trakt now sets it to desc instead of asc.
			# Just test with the sort functions below and make sure that after changing the settings, the Gaia list has the same order as on Trakt's website.
			if headers:
				headers = dict((k.lower(), v) for k, v in headers.items())
				sort = headers.get('x-sort-by')
				order = headers.get('x-sort-how')

			if sort == 'random':
				data = tools.Tools.listShuffle(data)
			else:
				forward = order == 'desc'
				backward = order is None or order == 'desc'

				function = None
				reverse = None

				if sort == 'rank':
					function = sortRank
					reverse = forward
				elif sort == 'title':
					function = sortTitle
					reverse = forward
				elif sort == 'released':
					function = sortReleased
					reverse = backward
				elif sort == 'runtime':
					function = sortRuntime
					reverse = backward
				elif sort == 'popularity':
					function = sortPopularity
					reverse = backward
				elif sort == 'percentage':
					function = sortPercentage
					reverse = backward
				elif sort == 'votes':
					function = sortVotes
					reverse = backward
				elif sort == 'my_rating':
					function = sortMyrating
					reverse = backward
				elif sort == 'added':
					function = sortAdded
					reverse = backward
				elif sort == 'watched':
					function = sortWatched
					reverse = backward
				elif sort == 'collected':
					function = sortCollected
					reverse = backward
				elif sort == 'updated':
					function = sortUpdated
					reverse = backward
				elif sort == 'time':
					# Some endpoints just return "time" as x-sort-by, without explicitly stating what time to use.
					# Eg: /users/id/watched/type
					if data and data[0]:
						item = data[0]
						for i in [sortCollected, sortWatched, sortRated, sortAdded, sortUpdated]:
							if i(item):
								function = i
								break
					if not function: function = sortUpdated
					reverse = backward

				if function: data = tools.Tools.listSort(data, key = lambda i : function(i), reverse = reverse)
	except: tools.Logger.error()
	return data


def sortRank(data):
	# Trakt's highest/best rank starts at 1.
	try: return data.get('rank', 99999999)
	except: tools.Logger.error()

def sortTitle(data):
	# Trakt's website sorts by title without articles.
	# Trakt sorts by show title + season/episode title.
	try:
		title = [
			data.get('show', {}).get('title'),
			data.get('episode', {}).get('title') or data.get('season', {}).get('title'),
		]
		title = [i for i in title if i]
		if title: title = ' - '.join(title)
		else: title = data.get(data.get('type'), {}).get('title')

		if title is None: title = ''
		else: title = title.lower().strip()

		articles = {
			'en' : r'^((?:the|an?)\s)',
			'de' : r'^((?:de[nmrs]|die|das|ein(?:e[nmrs])?|dies(?:e[nmrs])?)\s)',
			'fr' : r'^((?:l[ae]|les|une?|d[eu](?:\sl[ae])?|des|)\s|(?:l[\'\’\‘]|d[eu](?:\sl[\'\’\‘])))',
			'nl' : r'^((?:de|het|een)\s)',
			'es' : r'^((?:l[ao]s?|el|un[ao]?s?)\s)',
			'pt' : r'^((?:[ao]s?|uma?s?|uns)\s)',
			'it' : r'^((?:il?|gil|l[aeo]|un[ao]?)\s|l[\'\’\‘])',
		}
		for expression in articles.values():
			titleNew = tools.Regex.remove(data = title, expression = expression, group = 1, cache = True)
			if not titleNew == title: return titleNew
	except: tools.Logger.error()
	return title

def sortReleased(data):
	try:
		base = data.get(data.get('type'))
		return base.get('released') or base.get('first_aired') or ''
	except: tools.Logger.error()

def sortRuntime(data):
	try: return data.get(data.get('type')).get('runtime', 0)
	except: tools.Logger.error()

def sortPopularity(data):
	# Not entirely  sure how Trakt calculates the popularity.
	# Under the movies/popular endpoint it states: Popularity is calculated using the rating percentage and the number of ratings.
	# Update: it seems that the popularity is literally just the rating * votes.
	try:
		base = data.get(data.get('type'))
		rating = base.get('rating', 0)
		votes = base.get('votes', 0)
		# https://en.wikipedia.org/wiki/Bayes_estimator#Practical_example_of_Bayes_estimators
		#return ((rating * votes) + (7.0 * 2000)) / float(votes + 2000)
		return rating * votes
	except: tools.Logger.error()

def sortPercentage(data):
	try: return data.get('progress', 0)
	except: tools.Logger.error()

def sortVotes(data):
	try: return data.get(data.get('type')).get('votes', 0)
	except: tools.Logger.error()

def sortMyrating(data):
	try: return data.get('rating', 0)
	except: tools.Logger.error()

def sortAdded(data):
	try: return data.get('listed_at', '') or data.get('created_at', '')
	except: tools.Logger.error()

def sortWatched(data):
	try: return data.get('last_watched_at') or data.get('watched_at') or ''
	except: tools.Logger.error()

def sortCollected(data):
	try: return data.get('last_collected_at') or data.get('collected_at') or ''
	except: tools.Logger.error()

def sortRated(data):
	try: return data.get('last_rated_at') or data.get('rated_at') or ''
	except: tools.Logger.error()

def sortUpdated(data):
	try: return data.get('last_updated_at') or data.get('updated_at') or ''
	except: tools.Logger.error()

def getTraktAsJson(url, post = None, headers = None, direct = False, authentication = None, extended = False, size = False, method = None, timeout = network.Networker.TimeoutLong, sort = True):
	try:
		data, headers, error = getTrakt(url = url, post = post, headers = headers, extended = True, direct = direct, authentication = authentication, method = method, timeout = timeout)

		if size:
			size = {
				'compressed' : network.Networker.size(data = data, headers = headers, compressed = True),
				'decompressed' : network.Networker.size(data = data, headers = headers, compressed = False),
			}

		data = tools.Converter.jsonFrom(data)
		if sort and headers: data = sortList(data = data, headers = headers)

		if size: return data, size
		elif extended: return data, error
		else: return data
	except: tools.Logger.error()
	if size: return None, None
	elif extended: return None, None
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
	try: return processTitles(Cache.instance().cacheExtended(getTraktAsJson, '/movies/%s/aliases' % id))
	except: return []

def getTVShowAliases(id):
	try: return processTitles(Cache.instance().cacheExtended(getTraktAsJson, '/shows/%s/aliases' % id))
	except: return []

def getPeopleMovie(id, full = True, cache = True, failsafe = False):
	try:
		url = '/movies/%s/people' % id
		if full: url += '?extended=full'
		if cache: return getTraktCache(function = Cache.instance().cacheExtended, url = url, failsafe = failsafe)
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
		if cache: return getTraktCache(function = Cache.instance().cacheExtended, url = url, failsafe = failsafe)
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
			if year:
				if tools.Tools.isArray(year):
					if len(year) == 1: year = year[0]
					else: year = '%d-%d' % (year[0], year[1])
				url += '&years=%s' % str(year)
		else: return None
		if full: url += ('&' if '?' in url else '?') + 'extended=full'

		if cache: result = getTraktCache(function = Cache.instance().cacheExtended, url = url, failsafe = failsafe)
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
			if year:
				if tools.Tools.isArray(year):
					if len(year) == 1: year = year[0]
					else: year = '%d-%d' % (year[0], year[1])
				url += '&years=%s' % str(year)
		else: return None
		if full: url += ('&' if '?' in url else '?') + 'extended=full'

		if cache: result = getTraktCache(function = Cache.instance().cacheExtended, url = url, failsafe = failsafe)
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
		r = Cache.instance().cacheExtended(getTraktAsJson, r)
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
# SYNC
##############################################################################

TraktSyncData = None
TraktSyncUpdate = None

def sync(refresh = False):
	if refresh:
		return Cache.instance().cacheClear(_sync)
	else:
		global TraktSyncData
		if TraktSyncData is None: return Cache.instance().cacheQuick(_sync)
		else: return TraktSyncData

def syncAll(refresh = False):
	try: sync(refresh = refresh)['time']['all']
	except: return None

def syncHistory(media, refresh = False):
	try: return sync(refresh = refresh)['time'][media]['history']
	except: return None

def syncProgress(media, refresh = False):
	try: return sync(refresh = refresh)['time'][media]['progress']
	except: return None

def syncRating(media, refresh = False):
	try: return sync(refresh = refresh)['time'][media]['rating']
	except: return None

def syncRefresh(wait = True):
	if wait: sync(refresh = True)
	else: Pool.thread(target = sync, kwargs = {'refresh' : True}, start = True)

def syncClear():
	Cache.instance().cacheDelete(_sync)

def syncUpdate(media = None, type = None, update = False):
	try:
		id = 'account.trakt.sync'
		global TraktSyncUpdate

		if TraktSyncUpdate is None:
			data = tools.Settings.getData(id = id)
			if data: TraktSyncUpdate = data

		if TraktSyncUpdate is None:
			TraktSyncUpdate = {
				'all' : None,
				tools.Media.Movie :
				{
					'all' : None,
					'history' : None,
					'progress' : None,
					'rating' : None,
				},
				tools.Media.Show :
				{
					'all' : None,
					'history' : None,
					'progress' : None,
					'rating' : None,
				},
				tools.Media.Season :
				{
					'all' : None,
					'rating' : None,
				},
				tools.Media.Episode :
				{
					'all' : None,
					'rating' : None,
				},
			}
			tools.Settings.setData(id = id, value = TraktSyncUpdate)

		if update:
			data = sync()
			if media is None: TraktSyncUpdate[type] = data['time'][type]
			else: TraktSyncUpdate[media][type] = data['time'][media][type]
			tools.Settings.setData(id = id, value = TraktSyncUpdate)
		else:
			if media is None:
				result = TraktSyncUpdate[type]
			else:
				result = TraktSyncUpdate[media]
				if type: result = result[type]
			return result
	except:
		tools.Logger.error()
		return None

def syncUpdateHistory(media = None, update = False):
	return syncUpdate(media = media, type = 'history', update = update)

def syncUpdateProgress(media = None, update = False):
	return syncUpdate(media = media, type = 'progress', update = update)

def syncUpdateRating(media = None, update = False):
	return syncUpdate(media = media, type = 'rating', update = update)

def _sync():
	try:
		log(message = 'Refreshing Sync Data ...', developer = True)

		data, size = getTraktAsJson('sync/last_activities', size = True)
		if not data:
			log(message = 'Failed Sync Data', size = size, developer = True)
			return None

		log(message = 'Refreshed Sync Data', size = size, developer = True)

		all = None
		try: all = tools.Time.timestamp(data['all'], iso = True)
		except: tools.Logger.error()

		movieAll = None
		movieHistory = None
		movieProgress = None
		movieRating = None
		try: movieAll = max([tools.Time.timestamp(i, iso = True) for i in data['movies'].values()])
		except: tools.Logger.error()
		try: movieHistory = tools.Time.timestamp(data['movies']['watched_at'], iso = True)
		except: tools.Logger.error()
		try: movieProgress = tools.Time.timestamp(data['movies']['paused_at'], iso = True)
		except: tools.Logger.error()
		try: movieRating = tools.Time.timestamp(data['movies']['rated_at'], iso = True)
		except: tools.Logger.error()

		showAll = None
		showRating = None
		try: showAll = max([tools.Time.timestamp(i, iso = True) for i in data['shows'].values()])
		except: tools.Logger.error()
		try: showRating = tools.Time.timestamp(data['shows']['rated_at'], iso = True)
		except: tools.Logger.error()

		seasonAll = None
		seasonRating = None
		try: seasonAll = max([tools.Time.timestamp(i, iso = True) for i in data['seasons'].values()])
		except: tools.Logger.error()
		try: seasonRating = tools.Time.timestamp(data['seasons']['rated_at'], iso = True)
		except: tools.Logger.error()

		episodeAll = None
		episodeHistory = None
		episodeProgress = None
		episodeRating = None
		try: episodeAll = max([tools.Time.timestamp(i, iso = True) for i in data['episodes'].values()])
		except: tools.Logger.error()
		try: episodeHistory = tools.Time.timestamp(data['episodes']['watched_at'], iso = True)
		except: tools.Logger.error()
		try: episodeProgress = tools.Time.timestamp(data['episodes']['paused_at'], iso = True)
		except: tools.Logger.error()
		try: episodeRating = tools.Time.timestamp(data['episodes']['rated_at'], iso = True)
		except: tools.Logger.error()

		showAll = [showAll, episodeHistory, episodeProgress]
		showAll = max([i for i in showAll if i])

		global TraktSyncData
		TraktSyncData = {
			'time' : {
				'all' : all,
				tools.Media.Movie :
				{
					'all' : movieAll,
					'history' : movieHistory,
					'progress' : movieProgress,
					'rating' : movieRating,
				},
				tools.Media.Show :
				{
					'all' : showAll,
					'history' : episodeHistory,
					'progress' : episodeProgress,
					'rating' : showRating,
				},
				tools.Media.Season :
				{
					'all' : seasonAll,
					'rating' : seasonRating,
				},
				tools.Media.Episode :
				{
					'all' : episodeAll,
					'history' : episodeHistory,
					'progress' : episodeProgress,
					'rating' : episodeRating,
				},
			},
			'data' : data,
		}
		return TraktSyncData
	except:
		tools.Logger.error()
		return None

##############################################################################
# REFRESH
##############################################################################

def refresh(media = None, history = True, progress = True, rating = True, force = False, reload = True, wait = True):
	if wait: _refresh(media = media, history = history, progress = progress, rating = rating, force = force, reload = reload)
	else: Pool.thread(target = _refresh, kwargs = {'media' : media, 'history' : history, 'progress' : progress, 'rating' : rating, 'force' : force, 'reload' : reload, 'delay' : True}, start = True)

def _refresh(media = None, history = True, progress = True, rating = True, force = False, reload = True, delay = False):
	# Sleep if refreshed in the background, to allow other processes to continue and not being held up by this.
	if delay: tools.Time.sleep(0.25)

	# Do this first, since the other refresh function below use the sync data.
	# Important that we use sync=False below, since we already synced the new data here, and we do not want to redo it for each thread.
	syncRefresh(wait = True)

	threads = []

	if not media or tools.Media.isMixed(media) or tools.Media.isFilm(media):
		if history: threads.append(Pool.thread(target = historyRefreshMovie, kwargs = {'force' : force, 'sync' : False, 'reload' : False, 'wait' : True}, start = True))
		if progress: threads.append(Pool.thread(target = progressRefreshMovie, kwargs = {'force' : force, 'sync' : False, 'reload' : False, 'wait' : True}, start = True))
		if rating: threads.append(Pool.thread(target = ratingRefreshMovie, kwargs = {'force' : force, 'sync' : False, 'wait' : True}, start = True))

	if not media or tools.Media.isMixed(media) or tools.Media.isSerie(media):
		if history: threads.append(Pool.thread(target = historyRefreshShow, kwargs = {'force' : force, 'sync' : False, 'reload' : False, 'wait' : True}, start = True))
		if progress: threads.append(Pool.thread(target = progressRefreshShow, kwargs = {'force' : force, 'sync' : False, 'reload' : False, 'wait' : True}, start = True))
		if rating:
			threads.append(Pool.thread(target = ratingRefreshShow, kwargs = {'force' : force, 'sync' : False, 'wait' : True}, start = True))
			threads.append(Pool.thread(target = ratingRefreshSeason, kwargs = {'force' : force, 'sync' : False, 'wait' : True}, start = True))
			threads.append(Pool.thread(target = ratingRefreshEpisode, kwargs = {'force' : force, 'sync' : False, 'wait' : True}, start = True))

	[thread.join() for thread in threads]
	if reload: _reload(history = history, progress = progress, rating = rating, wait = True)

def _reload(media = None, history = False, progress = False, rating = False, force = False, wait = False):
	if history or progress:
		from lib.modules.playback import Playback
		Playback.instance().reload(media = media, history = history, progress = progress, rating = rating, force = force, wait = wait)

##############################################################################
# HISTORY - GENERAL
##############################################################################

TraktHistory = {}

def historyType(media = None, season = None, episode = None, plural = True):
	if media is None: media = tools.Media.Show if (not season is None or not episode is None) else tools.Media.Movie
	if tools.Media.isSerie(media): type = 'show'
	else: type = 'movie'
	if plural and not type.endswith('s'): type += 's'
	return media, type

def historyLink(media = None, type = None, id = None, dateStart = None, dateEnd = None, extended = None):
	if not type: media, type = historyType(media = media)
	if id:
		# This endpoint has paging. Add limit, otherwise only a few episodes are returned.
		link = 'sync/history/%s/%s?limit=9999999999' % (type, id)
		if extended: link += '&extended=full'
		if dateStart: link += '&start_at=' + timeFormat(dateStart)
		if dateEnd: link += '&end_at=' + timeFormat(dateEnd)
	else:
		# NB: There are multiple ways of getting the user's history:
		#	/sync/watched/
		#	/sync/history/
		#	/users/me/watched/
		#	/users/me/history/
		# The /history/ links not only return watched activity, but also checkins and scrobbles, plus they require a date range.
		# So it is better for this purpose to use /watched/.
		# There is a problem with /users/me/watched/, that its extended metadata for shows is sometimes outdated, specifically:
		#	data['show']['aired_episodes']
		# It still contains the metdata of the show BEFORE the new season was released.
		# This causes a few new season releases to not show up at the top of the Progress menu.
		#	episodes.py -> traktListProgress() -> if all(plays == episodeTotal for plays in episodePlays.values()):
		# Note that /sync/watched/ and /users/me/watched/ essentially return the exact same data, except for those few outdated attributes.
		# This happened twice:
		#	Black Mirror S06
		#	The Wheel of Time S02
		# For instance, 2 days after The Wheel of Time S02 was released, /users/me/watched/ returned:
		#	data['show']['aired_episodes'] = 8
		# although 11 episodes where already released (3 for S02). Even when forcefully re-retrieving the list data, it does not update that attribute.
		# Not sure why this is sporadic and only applies to a few shows, but not others.
		# Maybe Trakt caches the metadata for those requests and the metadata cache for some shows was not refreshed yet.
		# Or maybe Trakt only updates the metadata once that show was manually updated from the user's history (aka scrobble or new episode watched)?
		# Not even sure if or when Trakt will refresh the metadata.
		# Even if Trakt does the refresh a few days/weeks later, it is already so old that Gaia might have pushed the show to the 2nd page of the Progress menu and the user might never see it.
		# Also not sure if this only happens in /users/me/watched/ or maybe also sometimes in /sync/watched/ as well.
		# In any case, when using /sync/watched/, The Wheel of Time did return the correctly updated aired_episodes, so stick to this endpoint.

		# Also note that this only happens if the previous season was watched a long time ago.
		# If we mark a season, eg The Wheel of Time, as watched now and the open the Progress menu, /users/me/watched/ pulls in the updated metadata.
		# That might support the point that Trakt only updates the metadata of a show in /users/me/watched/ if we somehow update the watched status or user history of that show.

		# Another point to consider is that the /sync/watched/ extended metadata can be 1MB for an average user's history, and maybe a few MB for users who watch a lot.
		# Every time we launch the addon, start playback, or finish playback, Gaia redownloads this list, putting an unnecessary load on Trakt.
		# Is there maybe a more efficient way of doing this?
		# /sync/watched/ does NOT have a date range, where we could retrieve the entire list every few days, and then add the past days watched items to it, which is smaller in size and can be retrieved more often.
		# The only way seems to use /sync/history/. But this endpoint also contains checkins/scrobbles, although these could be easily filtered out.
		# We still need to somehow merge /sync/history/ with /sync/watched/ data and update all the "plays" attributes correctly.
		# The processing in episodes.py -> traktListProgress() should be able to handle this.

		# Or a better solution: construct the Gaia show Progress manually from playback.py -> items(), similar to movies.py.
		# Technically we only need the last watched season/episode to do this.
		# Then we can skip extended metadata here, and only retrieve the basic/smaller data more regularly.

		link = 'sync/watched/%s' % type

		# We do not need the extended info here for trakt.py.
		# Extended info is about 30% larger then without extended info.
		#if extended is None and type.startswith('show'): extended = True

		if extended: link += '?extended=full'
	return link

##############################################################################
# HISTORY - DATA
##############################################################################

# Also used by episodes.py.
def historyData(media = None, refresh = False, wait = False):
	# Use global var to improve speeds, especially for batch requests where this function is called multiple times for different movies/shows.
	# Caching for 3 days seems very long. However, the data is refreshed at launch and after each playback, so it should be up-to-date most of the time.
	# Plus we also refresh based on sync(), so if the data changes on Trakt, this will also be refreshed.
	# The 3 day cache timeout should only be triggered if the user did not use Gaia for more than 3 days.
	global TraktHistory
	media = tools.Media.Show if tools.Media.isSerie(media) else tools.Media.Movie
	link = historyLink(media = media)
	if refresh:
		if wait: TraktHistory[link] = Cache.instance().cacheClear(historyDataRetrieve, media = media, link = link)
		else: TraktHistory[link] = Cache.instance().cacheRefresh(historyDataRetrieve, media = media, link = link)
	elif not link in TraktHistory:
		TraktHistory[link] = Cache.instance().cacheExtended(historyDataRetrieve, media = media, link = link)
	return TraktHistory[link]

def historyDataRetrieve(media, link):
	log(message = 'Refreshing %s History Data ...' % media.title(), developer = True)
	data, size = getTraktAsJson(link, size = True)
	log(message = 'Refreshed %s History Data' % media.title(), size = size, developer = True)
	syncUpdateHistory(media = media, update = True)
	return historyDataPrepare(data)

def historyDataPrepare(data):
	# In historyRetrieve() we sequentially scan the entire history list to find the items based on IDs.
	# This can slow down menus, since potentially 1000s of history items have to be scanned for each of the eg 50 items in the menu.
	# Not only is the average time O(0.5n) per menu entry, but since menus mostly contain unwatched titles, the actual average will be more like O(0.95n).
	# It seems a better idea to search all IDs once when new data is retrieved, and during consecutive menu access, we only have to do a dictionary lookup of the ID.
	# Constructing a dictionary once should still be faster than sequentially searching the list every time.
	# With some benchmarks, the dictionary option uses only about 60% of the time of a sequential loop for lists with all watched items, and about 75% for list with about half the items watched.
	result = {'id' : {'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}}, 'data' : data}
	providers = result['id'].keys()

	if data:
		for i in range(len(data)):
			item = data[i]
			meta = item.get('show')
			if not meta: meta = item.get('movie')
			if meta:
				ids = meta.get('ids')
				if ids:
					for provider in providers:
						id = ids.get(provider)
						if id: result['id'][provider][str(id)] = i

	return result

def historyDataSync(media = None, refresh = False):
	try:
		# NB: Use syncUpdateHistory() to only refresh the data if the Trakt timestamp changed.
		# Otherwise, if the user's device/system has the wrong time set (eg: date is correct, but year is behind by one), the data will be constantly refreshed, since there is a mistmatch between Trakt and local timestamps.
		media = tools.Media.Show if tools.Media.isSerie(media) else tools.Media.Movie
		timeGlobal = syncHistory(media = media, refresh = refresh)
		if timeGlobal:
			timeLocal = syncUpdateHistory(media = media)
			if not timeLocal or timeGlobal > timeLocal: return True
	except: tools.Logger.error()
	return False

def historyDataRefresh(media = None, force = False, sync = False, wait = False):
	if historyDataSync(media = media, refresh = sync): force = True
	return historyData(media = media, refresh = force, wait = wait)

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
	historyClear(media = tools.Media.Movie, wait = wait)

def historyClearShow(wait = True):
	historyClear(media = tools.Media.Show, wait = wait)

##############################################################################
# HISTORY - REFRESH
##############################################################################

# force: False = no forceful refresh of anything, True = forcefully refresh sync and data. None = forcefully refresh sync, but only data if necessary.
def historyRefresh(media = None, force = False, sync = True, reload = True, wait = True):
	def _historyRefresh(media, force, sync, reload, wait):
		historyDataRefresh(media = media, force = force, sync = sync, wait = wait)
		if reload: _reload(media = media, history = True)
	if wait: _historyRefresh(media = media, force = force, sync = sync, reload = reload, wait = wait)
	else: Pool.thread(target = _historyRefresh, kwargs = {'media' : media, 'force' : force, 'sync' : sync, 'reload' : reload, 'wait' : wait}, start = True)

def historyRefreshMovie(force = False, sync = True, reload = True, wait = True):
	historyRefresh(media = tools.Media.Movie, force = force, sync = sync, reload = reload, wait = wait)

def historyRefreshShow(force = False, sync = True, reload = True, wait = True):
	historyRefresh(media = tools.Media.Show, force = force, sync = sync, reload = reload, wait = wait)

##############################################################################
# HISTORY - RETRIEVE
##############################################################################

# NB: detail=True: retrieve all play times, instead of just the last one. An additional non-cached API call is being made, so use sparingly and not in batch.
# Currently only used when manually marking as unwatched and the user chooses to unwatch a specific play.
def historyRetrieve(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, detail = False):
	try:
		media, type = historyType(media = media, season = season, episode = episode)

		ids = {}
		if not imdb is None: ids['imdb'] = str(imdb)
		if not tmdb is None: ids['tmdb'] = str(tmdb)
		if not tvdb is None: ids['tvdb'] = str(tvdb)
		if not trakt is None: ids['trakt'] = str(trakt)
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)
		single = bool(imdb or tmdb or tvdb or trakt)

		items = historyData(media = media)
		if not items: return False # Either not Trakt history, or Trakt is down.

		if single:
			# Further reduce time by not looking up all IDs.
			# Since Trakt has most external IDs, if it can't find the IMDb ID, it most likley will also not find the other IDs.
			if len(ids.keys()) > 1:
				if tools.Media.isSerie(media): key = 'tmdb'
				else: key = 'tvdb'
				try: del ids[key]
				except: pass

			index = None
			for provider, id in ids.items():
				item = items.get('id').get(provider)
				if item:
					item = item.get(id)
					if not item is None:
						index = item
						break
			if index is None: items = []
			else: items = [items['data'][index]]
		else:
			items = items['data']

		result = []
		if items:
			if tools.Media.isSerie(media):
				for item in items:
					try:
						if 'show' in item:
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
														'all' : historyTimeShow(trakt = item['show']['ids']['trakt'], season = s['number'], episode = e['number']) if detail else [time] if time else [],
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
														'all' : historyTimeShow(trakt = item['show']['ids']['trakt'], season = s['number'], episode = e['number']) if detail else [time] if time else [],
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
					except: tools.Logger.error()
			else:
				for item in items:
					try:
						if 'movie' in item:
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
									'all' : historyTimeMovie(trakt = item['movie']['ids']['trakt']) if detail else [time] if time else [],
								},
							})
					except: tools.Logger.error()

		if single: return result[0] if result else None
		else: return result
	except: tools.Logger.error()
	return None

def historyRetrieveMovie(imdb = None, tmdb = None, trakt = None, detail = False):
	return historyRetrieve(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, trakt = trakt, detail = detail)

def historyRetrieveShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, detail = False):
	return historyRetrieve(media = tools.Media.Show, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, detail = detail)

##############################################################################
# HISTORY - UPDATE
##############################################################################

def historyUpdate(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, time = None, refresh = True, reload = True, wait = False):
	if tools.Media.isSerie(media): return historyUpdateShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, time = time, refresh = refresh, reload = reload, wait = wait)
	else: return historyUpdateMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, items = items, time = time, refresh = refresh, reload = reload, wait = wait)

def historyUpdateTime(items = None, time = None):
	if items and time:
		if tools.Tools.isInteger(time): time = timeFormat(time)
		for i in range(len(items)): items[i]['watched_at'] = time
	return items

def historyUpdateItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, time = None, refresh = True, reload = True, wait = False):
	media, type = historyType(media = media)
	items = request(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items)
	items = historyUpdateTime(items = items, time = time)
	result, error = getTraktAsJson('/sync/history', {type : items}, timeout = timeout(items), extended = True)
	if _errorIs(error = error, data = result): result = False # Trakt server is down. Result should be False, not None.
	if refresh: historyRefresh(media = media, reload = reload, wait = wait)
	return result, items

def historyUpdateMovie(imdb = None, tmdb = None, trakt = None, items = None, time = None, refresh = True, reload = True, wait = False):
	result, items = historyUpdateItems(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, trakt = trakt, items = items, time = time, refresh = refresh, reload = reload, wait = wait)
	return result

def historyUpdateShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, time = None, refresh = True, reload = True, wait = False):
	result, items = historyUpdateItems(media = tools.Media.Show, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, time = time, refresh = refresh, reload = reload, wait = wait)
	return result

##############################################################################
# HISTORY - REMOVE
##############################################################################

# selection: None = remove all, False = remove oldest, True = remove most recent, Small Integer = remove specific index, Large Integer = remove specific history ID, List = start and end timestamp to remove all items between the dates.
def historyRemove(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, selection = None, refresh = True, reload = True, wait = False):
	if tools.Media.isSerie(media): return historyRemoveShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, selection = selection, refresh = refresh, reload = reload, wait = wait)
	else: return historyRemoveMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, items = items, selection = selection, refresh = refresh, reload = reload, wait = wait)

def historyRemoveItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, selection = None, refresh = True, reload = True, wait = False):
	media, type = historyType(media = media)

	ids = None
	if not selection is None:
		error = False
		ids = []
		if items:
			for item in items:
				id = historyId(media = media, imdb = item.get('imdb'), tmdb = item.get('tmdb'), tvdb = item.get('tvdb'), trakt = item.get('trakt'), season = item.get('season'), episode = item.get('episode'), selection = selection)
				if id:
					error = False
					if tools.Tools.isArray(id): ids.extend(id)
					else: ids.append(id)
				elif id is False:
					error = True
		else:
			id = historyId(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, selection = selection)
			if id:
				error = False
				if tools.Tools.isArray(id): ids.extend(id)
				else: ids.append(id)
			elif id is False:
				error = True
		if not ids: return False if error else None, None

	if ids is None:
		items = request(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items)
		result, error = getTraktAsJson('/sync/history/remove', {type : items}, timeout = timeout(items), extended = True)
	else:
		result, error = getTraktAsJson('/sync/history/remove', {'ids' : ids}, timeout = timeout(ids), extended = True)

	if _errorIs(error = error, data = result): result = False # Trakt server is down. Result should be False, not None.
	if refresh: historyRefresh(media = media, reload = reload, wait = wait)
	return result, items

def historyRemoveMovie(imdb = None, tmdb = None, trakt = None, items = None, selection = None, refresh = True, reload = True, wait = False):
	result, items = historyRemoveItems(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, trakt = trakt, items = items, selection = selection, refresh = refresh, reload = reload, wait = wait)
	return result

def historyRemoveShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, selection = None, refresh = True, reload = True, wait = False):
	result, items = historyRemoveItems(media = tools.Media.Show, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, selection = selection, refresh = refresh, reload = reload, wait = wait)
	return result

##############################################################################
# HISTORY - DETAIL
##############################################################################

# action = scrobble, checkin, watch. None == all
# selection: None = retrieve all, False = retrieve oldest, True = retrieve most recent, Small Integer = retrieve specific index, Large Integer = retrieve specific history ID, List = start and end timestamp to retrieve all items between the dates.
def historyDetail(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	if tools.Media.isSerie(media): return historyDetailShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)
	else: return historyDetailMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyDetailItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	media, type = historyType(media = media, season = season, episode = episode, plural = True)

	if not trakt:
		if tools.Media.isSerie(media): data = SearchTVShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, single = True, full = False, cache = True)
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
	if not link in TraktHistory:
		data, error = getTraktAsJson(link, extended = True)
		TraktHistory[link] = data
		if _errorIs(error = error, data = data): return False
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
	return historyDetailItems(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyDetailShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	return historyDetailItems(media = tools.Media.Show, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)

##############################################################################
# HISTORY - ID
##############################################################################

# action = scrobble, checkin, watch. None == all
# selection: None = retrieve all, False = retrieve oldest, True = retrieve most recent, Small Integer = retrieve specific index, Large Integer = retrieve specific history ID, List = start and end timestamp to retrieve all items between the dates.
def historyId(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	if tools.Media.isSerie(media): return historyIdShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)
	else: return historyIdMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyIdItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	result = historyDetailItems(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)
	if result:
		if tools.Tools.isArray(result): result = [i['id'] for i in result if 'id' in i and i['id']]
		elif tools.Tools.isDictionary(result) and 'id' in result and result['id']: result = result['id']
		else: result = None
	return result

def historyIdMovie(imdb = None, tmdb = None, trakt = None, action = None, selection = None):
	return historyIdItems(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyIdShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	return historyIdItems(media = tools.Media.Show, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)

##############################################################################
# HISTORY - TIME
##############################################################################

# action = scrobble, checkin, watch. None == all
# selection: None = retrieve all, False = retrieve oldest, True = retrieve most recent, Small Integer = retrieve specific index, Large Integer = retrieve specific history ID.
def historyTime(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	if tools.Media.isSerie(media): return historyTimeShow(imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)
	else: return historyTimeMovie(imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyTimeItems(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	result = historyDetailItems(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)

	if result:
		if tools.Tools.isArray(result): result = [tools.Time.timestamp(i['watched_at'], iso = True) for i in result if 'watched_at' in i and i['watched_at']]
		elif tools.Tools.isDictionary(result) and 'watched_at' in result and result['watched_at']: result = tools.Time.timestamp(result['watched_at'], iso = True)
		else: result = None
	return result

def historyTimeMovie(imdb = None, tmdb = None, trakt = None, action = None, selection = None):
	return historyTimeItems(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, trakt = trakt, action = action, selection = selection)

def historyTimeShow(imdb = None, tvdb = None, trakt = None, season = None, episode = None, action = None, selection = None):
	return historyTimeItems(media = tools.Media.Show, imdb = imdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, action = action, selection = selection)

##############################################################################
# PROGRESS - GENERAL
##############################################################################

TraktProgress = {}

def progressType(media = None, season = None, episode = None, plural = False):
	if media is None: media = tools.Media.Show if (not season is None or not episode is None) else tools.Media.Movie
	if tools.Media.isSerie(media): type = 'episode'
	else: type = 'movie'
	if plural and not type.endswith('s'): type += 's'
	return media, type

def progressLink(media = None, type = None, season = None, episode = None):
	if not type: media, type = progressType(media = media, season = season, episode = episode, plural = True) # This endpoint uses plural, therefore add "s".
	return '/sync/playback/' + type

##############################################################################
# PROGRESS - DATA
##############################################################################

# Also used by episodes.py.
def progressData(media = None, refresh = False, wait = False):
	# Use global var to improve speeds, especially for batch requests where this function is called multiple times for different movies/shows.
	# Caching for 3 days seems very long. However, the data is refreshed at launch and after each playback, so it should be up-to-date most of the time.
	# Plus we also refresh based on sync(), so if the data changes on Trakt, this will also be refreshed.
	# The 3 day cache timeout should only be triggered if the user did not use Gaia for more than 3 days.
	global TraktProgress
	media = tools.Media.Show if tools.Media.isSerie(media) else tools.Media.Movie # Media can be show or episode, causing the caches to be different for the same data.
	link = progressLink(media = media)
	if refresh:
		if wait: TraktProgress[link] = Cache.instance().cacheClear(progressDataRetrieve, media = media, link = link)
		else: TraktProgress[link] = Cache.instance().cacheRefresh(progressDataRetrieve, media = media, link = link)
	elif not link in TraktProgress:
		TraktProgress[link] = Cache.instance().cacheExtended(progressDataRetrieve, media = media, link = link)
	return TraktProgress[link]

def progressDataRetrieve(media, link):
	log(message = 'Refreshing %s Progress Data ...' % media.title(), developer = True)
	data, size = getTraktAsJson(link, size = True)
	log(message = 'Refreshed %s Progress Data' % media.title(), size = size, developer = True)
	syncUpdateProgress(media = media, update = True)
	return progressDataPrepare(data)

def progressDataPrepare(data):
	# Check historyDataPrepare() for more details.
	# Although the effect is probably a lot lower with progress, since there will be fewer items and they get deleted by Trakt after 6 months.
	result = {'id' : {'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}}, 'data' : data}
	providers = result['id'].keys()

	if data:
		for i in range(len(data)):
			item = data[i]
			meta = item.get('show')
			if not meta: meta = item.get('movie')
			if meta:
				ids = meta.get('ids')
				if ids:
					for provider in providers:
						id = ids.get(provider)
						if id:
							# There can be multiple items with the same show ID, unlike with history.
							if not str(id) in result['id'][provider]: result['id'][provider][str(id)] = []
							result['id'][provider][str(id)].append(i)

			paused = item.get('paused_at')
			if paused: item['time'] = tools.Time.timestamp(paused, iso = True)

	return result

def progressDataSync(media = None, refresh = False):
	try:
		# NB: Use syncUpdateProgress() to only refresh the data if the Trakt timestamp changed.
		# Otherwise, if the user's device/system has the wrong time set (eg: date is correct, but year is behind by one), the data will be constantly refreshed, since there is a mistmatch between Trakt and local timestamps.
		media = tools.Media.Show if tools.Media.isSerie(media) else tools.Media.Movie
		timeGlobal = syncProgress(media = media, refresh = refresh)
		if timeGlobal:
			timeLocal = syncUpdateProgress(media = media)
			if not timeLocal or timeGlobal > timeLocal: return True
	except: tools.Logger.error()
	return False

def progressDataRefresh(media = None, force = False, sync = False, wait = False):
	if progressDataSync(media = media, refresh = sync): force = True
	return progressData(media = media, refresh = force, wait = wait)

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
	progressClear(media = tools.Media.Movie, wait = wait)

def progressClearShow(wait = True):
	progressClear(media = tools.Media.Show, wait = wait)

##############################################################################
# PROGRESS - REFRESH
##############################################################################

# force: False = no forceful refresh of anything, True = forcefully refresh sync and data. None = forcefully refresh sync, but only data if necessary.
def progressRefresh(media = None, force = False, sync = True, reload = True, wait = True):
	def _progressRefresh(media, force, sync, wait):
		progressDataRefresh(media = media, force = force, sync = sync, wait = wait)
		if reload: _reload(media = media, progress = True)
	if wait: _progressRefresh(media = media, force = force, sync = sync, wait = wait)
	else: Pool.thread(target = _progressRefresh, kwargs = {'media' : media, 'force' : force, 'sync' : sync, 'wait' : wait}, start = True)

def progressRefreshMovie(force = False, sync = True, reload = True, wait = True):
	progressRefresh(media = tools.Media.Movie, force = force, sync = sync, reload = reload, wait = wait)

def progressRefreshShow(force = False, sync = True, reload = True, wait = True):
	progressRefresh(media = tools.Media.Show, force = force, sync = sync, reload = reload, wait = wait)

##############################################################################
# PROGRESS - RETRIEVE
##############################################################################

def progressRetrieve(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, limit = None, attribute = 'progress'):
	try:
		media, type = progressType(media = media, season = season, episode = episode)

		ids = {}
		if not imdb is None: ids['imdb'] = str(imdb)
		if not tmdb is None: ids['tmdb'] = str(tmdb)
		if not tvdb is None: ids['tvdb'] = str(tvdb)
		if not trakt is None: ids['trakt'] = str(trakt)
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)
		single = bool(imdb or tmdb or tvdb or trakt)

		items = progressData(media = media)
		if not items: return False # Either not Trakt progress, or Trakt is down.

		if single:
			# Further reduce time by not looking up all IDs.
			# Since Trakt has most external IDs, if it can't find the IMDb ID, it most likley will also not find the other IDs.
			if len(ids.keys()) > 1:
				if tools.Media.isSerie(media): key = 'tmdb'
				else: key = 'tvdb'
				try: del ids[key]
				except: pass

			index = None
			for provider, id in ids.items():
				item = items.get('id').get(provider)
				if item:
					item = item.get(id)
					if not item is None:
						index = item
						break
			if index: items = [items['data'][i] for i in index]
			else: items = []
		else:
			items = items['data']

		if items:
			if single:
				if tools.Media.isSerie(media):
					if season is None and episode is None: # Return any episode that still has progress.
						for item in items:
							try:
								if limit:
									if item['progress'] > limit[0] and item['progress'] < limit[1]: return item[attribute] if attribute else item
									else: return 0 if attribute == 'progress' else None # Avoid lookup in local database.
								else: return item[attribute] if attribute else item
							except: tools.Logger.error()
					elif episode is None: # Return any episode that still has progress.
						for item in items:
							try:
								if item['episode']['season'] == season:
									if limit:
										if item['progress'] > limit[0] and item['progress'] < limit[1]: return item[attribute] if attribute else item
										else: return 0 if attribute == 'progress' else None # Avoid lookup in local database.
									else: return item[attribute] if attribute else item
							except: tools.Logger.error()
					else:
						for item in items:
							try:
								if item['episode']['season'] == season and item['episode']['number'] == episode:
									if limit:
										if attribute and item[attribute] > limit[0] and item['progress'] < limit[1]: return item[attribute] if attribute else item
										else: return 0 if attribute == 'progress' else None # Avoid lookup in local database.
									else: return item[attribute] if attribute else item
							except: tools.Logger.error()
				else:
					for item in items:
						try:
							if limit:
								if item['progress'] > limit[0] and item['progress'] < limit[1]: return item[attribute] if attribute else item
								else: return 0 if attribute == 'progress' else None # Avoid lookup in local database.
							else: return item[attribute] if attribute else item
						except: tools.Logger.error()
			else:
				result = []
				for item in items:
					try:
						if type in item:
							if limit:
								if item['progress'] > limit[0] and item['progress'] < limit[1]: result.append(item)
							else: result.append(item)
					except: tools.Logger.error()
				return result
	except: tools.Logger.error()
	return None

def progressRetrieveMovie(imdb = None, tmdb = None, tvdb = None, trakt = None, limit = None):
	return progressRetrieve(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, limit = limit)

def progressRetrieveShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, limit = None):
	return progressRetrieve(media = tools.Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, limit = limit)

##############################################################################
# PROGRESS - UPDATE
##############################################################################

# action = start, pause, stop
# media = tools.Media.
# progress = float in [0, 100]
def progressUpdate(action, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, finished = False, progress = 0, force = False, refresh = True, reload = True, wait = False):
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

			if tools.Media.isSerie(media): item = SearchTVShow(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, single = True)
			else: item = SearchMovie(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, single = True)

			if item:
				if tools.Media.isSerie(media):
					slug = item['show']['ids']['slug']
					link = '/shows/%s/seasons/%d/episodes/%d' % (slug, season, episode)
					item = Cache.instance().cacheExtended(getTraktAsJson, link)
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
			# Only refresh on finished, not on every play/pause, otherwise there will be too many requests that are not needed until the video is stopped.
			if refresh and (stop or finished): progressRefresh(media = media, reload = reload, wait = wait)
	except: tools.Logger.error()
	return result

def progressUpdateMovie(action, imdb = None, tmdb = None, tvdb = None, trakt = None, finished = False, progress = 0, force = False, refresh = True, reload = True, wait = False):
	return progressUpdate(action = action, media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, finished = finished, progress = progress, force = force, refresh = refresh, reload = reload, wait = wait)

def progressUpdateShow(action, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, finished = False, progress = 0, force = False, refresh = True, reload = True, wait = False):
	return progressUpdate(action = action, media = tools.Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, finished = finished, progress = progress, force = force, refresh = refresh, reload = reload, wait = wait)

##############################################################################
# PROGRESS - REMOVE
##############################################################################

def progressRemove(media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, refresh = True, reload = True, wait = False):
	result = False
	try:
		id = progressRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, attribute = 'id')
		if not id is None:
			link = '/sync/playback/' + str(id)
			_, _, error = getTrakt(link, method = network.Networker.MethodDelete, extended = True)
			if _errorIs(error = error, data = result): result = False # Trakt server is down. Result should be False, not None.
			else: result = True # Since the requests only returns a code, but no body. Unlike all the other history/progress/rating sync requests, which all return a body.

			media, type = progressType(media = media, season = season, episode = episode)
			if refresh: progressRefresh(media = media, reload = reload, wait = wait)
	except: tools.Logger.error()
	return result

def progressRemoveMovie(imdb = None, tmdb = None, tvdb = None, trakt = None, refresh = True, reload = True, wait = False):
	return progressRemove(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, refresh = refresh, reload = reload, wait = wait)

def progressRemoveShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, refresh = True, reload = True, wait = False):
	return progressRemove(media = tools.Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, refresh = refresh, reload = reload, wait = wait)

##############################################################################
# RATING - GENERAL
##############################################################################

TraktRating = {}

def ratingType(media, season = None, episode = None, plural = True, general = False):
	if general and tools.Media.isSerie(media): type = 'show'
	elif media == tools.Media.Show: type = 'show'
	elif media == tools.Media.Season: type = 'season'
	elif media == tools.Media.Episode: type = 'episode'
	else: type = 'movie'
	if plural and not type.endswith('s'): type += 's'
	return media, type

def ratingLink(media = None, type = None, season = None, episode = None):
	if not type: media, type = ratingType(media = media, season = season, episode = episode)
	return '/sync/ratings/' + type

##############################################################################
# RATING - DATA
##############################################################################

# Also used by episodes.py.
def ratingData(media = None, refresh = False, wait = False):
	# Use global var to improve speeds, especially for batch requests where this function is called multiple times for different movies/shows.
	# Caching for 3 days seems very long. However, the data is refreshed at launch and after each playback, so it should be up-to-date most of the time.
	# Plus we also refresh based on sync(), so if the data changes on Trakt, this will also be refreshed.
	# The 3 day cache timeout should only be triggered if the user did not use Gaia for more than 3 days.
	global TraktRating
	link = ratingLink(media = media)
	if refresh:
		if wait: TraktRating[link] = Cache.instance().cacheClear(ratingDataRetrieve, media = media, link = link)
		else: TraktRating[link] = Cache.instance().cacheRefresh(ratingDataRetrieve, media = media, link = link)
	elif not link in TraktRating:
		TraktRating[link] = Cache.instance().cacheExtended(ratingDataRetrieve, media = media, link = link)
	return TraktRating[link]

def ratingDataRetrieve(media, link):
	log(message = 'Refreshing %s Rating Data ...' % media.title(), developer = True)
	data, size = getTraktAsJson(link, size = True)
	log(message = 'Refreshed %s Rating Data' % media.title(), size = size, developer = True)
	syncUpdateRating(media = media, update = True)
	return ratingDataPrepare(data)

def ratingDataPrepare(data):
	# Check historyDataPrepare() for more details.
	# Although the effect is probably a lot lower with rating, since there will be fewer items.
	result = {'id' : {'imdb' : {}, 'tmdb' : {}, 'tvdb' : {}, 'trakt' : {}}, 'data' : data}
	providers = result['id'].keys()

	if data:
		for i in range(len(data)):
			item = data[i]
			meta = item.get('show')
			if not meta: meta = item.get('movie')
			if meta:
				ids = meta.get('ids')
				if ids:
					for provider in providers:
						id = ids.get(provider)
						if id:
							# There can be multiple items with the same show ID, unlike with history.
							if not str(id) in result['id'][provider]: result['id'][provider][str(id)] = []
							result['id'][provider][str(id)].append(i)

			rated = item.get('rated_at')
			if rated: item['time'] = tools.Time.timestamp(rated, iso = True)

	return result

def ratingDataSync(media = None, refresh = False):
	try:
		# NB: Use syncUpdateRating() to only refresh the data if the Trakt timestamp changed.
		# Otherwise, if the user's device/system has the wrong time set (eg: date is correct, but year is behind by one), the data will be constantly refreshed, since there is a mistmatch between Trakt and local timestamps.
		media, type = ratingType(media = media)
		timeGlobal = syncRating(media = media, refresh = refresh)
		if timeGlobal:
			timeLocal = syncUpdateRating(media = media)
			if not timeLocal or timeGlobal > timeLocal: return True
	except: tools.Logger.error()
	return False

def ratingDataRefresh(media = None, force = False, sync = False, wait = False):
	if ratingDataSync(media = media, refresh = sync): force = True
	return ratingData(media = media, refresh = force, wait = wait)

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
	ratingClear(media = tools.Media.Movie, wait = wait)

def ratingClearShow(wait = True):
	ratingClear(media = tools.Media.Show, wait = wait)

def ratingClearSeason(wait = True):
	ratingClear(media = tools.Media.Season, wait = wait)

def ratingClearEpisode(wait = True):
	ratingClear(media = tools.Media.Episode, wait = wait)

##############################################################################
# RATING - REFRESH
##############################################################################

# force: False = no forceful refresh of anything, True = forcefully refresh sync and data. None = forcefully refresh sync, but only data if necessary.
def ratingRefresh(media = None, force = False, sync = True, wait = True):
	def _ratingRefresh(media, force, sync, wait):
		ratingDataRefresh(media = media, force = force, sync = sync, wait = wait)
	if wait: _ratingRefresh(media = media, force = force, sync = sync, wait = wait)
	else: Pool.thread(target = _ratingRefresh, kwargs = {'media' : media, 'force' : force, 'sync' : sync, 'wait' : wait}, start = True)

def ratingRefreshMovie(force = False, sync = True, wait = True):
	ratingRefresh(media = tools.Media.Movie, force = force, sync = sync, wait = wait)

def ratingRefreshShow(force = False, sync = True, wait = True):
	ratingRefresh(media = tools.Media.Show, force = force, sync = sync, wait = wait)

def ratingRefreshSeason(force = False, sync = True, wait = True):
	ratingRefresh(media = tools.Media.Season, force = force, sync = sync, wait = wait)

def ratingRefreshEpisode(force = False, sync = True, wait = True):
	ratingRefresh(media = tools.Media.Episode, force = force, sync = sync, wait = wait)

##############################################################################
# RATING - RETRIEVE
##############################################################################

def ratingRetrieve(media, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, attribute = 'rating'):
	try:
		media, type = ratingType(media = media, season = season, episode = episode)
		if tools.Media.isSerie(media): # Used by ratingData().
			if not episode is None: media = tools.Media.Episode
			elif not season is None: media = tools.Media.Season
			else: media = tools.Media.Show

		ids = {}
		if not imdb is None: ids['imdb'] = str(imdb)
		if not tmdb is None: ids['tmdb'] = str(tmdb)
		if not tvdb is None: ids['tvdb'] = str(tvdb)
		if not trakt is None: ids['trakt'] = str(trakt)
		if not season is None: season = int(season)
		if not episode is None: episode = int(episode)

		items = ratingData(media = media)
		if not items: return False # Either not Trakt ratings, or Trakt is down.

		# Further reduce time by not looking up all IDs.
		# Since Trakt has most external IDs, if it can't find the IMDb ID, it most likley will also not find the other IDs.
		if len(ids.keys()) > 1:
			if tools.Media.isSerie(media): key = 'tmdb'
			else: key = 'tvdb'
			try: del ids[key]
			except: pass

		index = None
		for provider, id in ids.items():
			item = items.get('id').get(provider)
			if item:
				item = item.get(id)
				if not item is None:
					index = item
					break
		if index: items = [items['data'][i] for i in index]
		else: items = []

		if items:
			if tools.Media.isSerie(media):
				if season is None and episode is None: # Return any episode that still has progress.
					for item in items:
						try: return item[attribute] if attribute else item
						except: tools.Logger.error()
				elif episode is None: # Return any episode that still has progress.
					for item in items:
						try:
							if item['season']['number'] == season:
								return item[attribute] if attribute else item
						except: tools.Logger.error()
				else:
					for item in items:
						try:
							if item['episode']['season'] == season and item['episode']['number'] == episode:
								return item[attribute] if attribute else item
						except: tools.Logger.error()
			else:
				for item in items:
					try: return item[attribute] if attribute else item
					except: tools.Logger.error()
	except: tools.Logger.error()
	return None

def ratingRetrieveMovie(imdb = None, tmdb = None, tvdb = None, trakt = None):
	return ratingRetrieve(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt)

def ratingRetrieveShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None):
	return ratingRetrieve(media = tools.Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

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
def ratingUpdate(rating, media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, time = None, items = None, force = False, wait = False):
	result = False
	try:
		# Do not update the rating if it did not change, in order to keep the old/original rating date.
		if not force:
			current = ratingRetrieve(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
			if current == rating: return current

		media, type = ratingType(media = media, season = season, episode = episode, general = True)
		items = request(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, rating = rating, items = items)
		items = ratingUpdateTime(items = items, time = time)
		result, error = getTraktAsJson('/sync/ratings', {type : items}, timeout = timeout(items), extended = True)
		if _errorIs(error = error, data = result): result = False # Trakt server is down. Result should be False, not None.
		if refresh: ratingRefresh(media = media, wait = wait)
	except: tools.Logger.error()
	return result

def ratingUpdateMovie(rating, imdb = None, tmdb = None, tvdb = None, trakt = None, time = None, items = None, force = False, wait = False):
	return ratingUpdate(rating = rating, media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, time = time, items = items, force = force, wait = wait)

def ratingUpdateShow(rating, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, time = None, items = None, force = False, wait = False):
	return ratingUpdate(rating = rating, media = tools.Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, time = time, items = items, force = force, wait = wait)

##############################################################################
# RATING - REMOVE
##############################################################################

def ratingRemove(media = None, imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, wait = False):
	result = False
	try:
		media, type = ratingType(media = media, season = season, episode = episode, general = True)
		items = request(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items)
		result, error = getTraktAsJson('/sync/ratings/remove', {type : items}, timeout = timeout(items), extended = True)
		if _errorIs(error = error, data = result): result = False # Trakt server is down. Result should be False, not None.
		if refresh: ratingRefresh(media = media, wait = wait)
	except: tools.Logger.error()
	return result

def ratingRemoveMovie(imdb = None, tmdb = None, tvdb = None, trakt = None, items = None, wait = False):
	return ratingRemove(media = tools.Media.Movie, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, items = items, wait = wait)

def ratingRemoveShow(imdb = None, tmdb = None, tvdb = None, trakt = None, season = None, episode = None, items = None, wait = False):
	return ratingRemove(media = tools.Media.Show, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, items = items, wait = wait)
