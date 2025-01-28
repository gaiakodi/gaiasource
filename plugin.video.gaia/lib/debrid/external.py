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

from lib.modules.concurrency import Pool, Lock
from lib.modules.network import Networker
from lib.modules.cache import Cache
from lib.modules.tools import Logger, System, Tools, Settings, Resolver, Hash
from lib.debrid.core import Core

class External(object):

	LimitGet = 40
	LimitPost = 100

	Lock = Lock()
	Authentication = {}
	Resolver = {}

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			External.Authentication = {}

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _lock(self):
		External.Lock.acquire()

	@classmethod
	def _unlock(self):
		try: External.Lock.release()
		except: pass

	@classmethod
	def _chunks(self, id, limit = None):
		if limit is None: limit = External.LimitPost
		return [id[i:i + limit] for i in range(0, len(id), limit)]

	@classmethod
	def _process(self, id, sources, callback, function, result, limit = None, timeout = None):
		chunks = self._chunks(id = id, limit = limit)
		threads = []
		for chunk in chunks:
			threads.append(Pool.thread(target = function, kwargs = {'id' : chunk, 'sources' : sources, 'callback' : callback, 'result' : result, 'timeout' : timeout}, start = True))
		[thread.join() for thread in threads]

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def instances(self, authenticated = True):
		instances = [Torbox, Easydebrid, Debridlink, Alldebrid]
		if authenticated: instances = [i for i in instances if i.authenticated()]
		return instances

	@classmethod
	def id(self):
		return self.Id

	@classmethod
	def name(self):
		return self.Name

	@classmethod
	def abbreviation(self):
		return self.Abbreviation

	@classmethod
	def acronym(self):
		return self.Acronym

	##############################################################################
	# AUTHENTICATION
	##############################################################################

	@classmethod
	def authentication(self, id = None):
		if id is None: id = self.id()

		if not id in External.Authentication:
			self._lock()
			if not id in External.Authentication:
				data = self.authenticationData()
				if data is None: data = Resolver.authenticationData(type = id)
				External.Authentication[id] = data
			self._unlock()

		return External.Authentication[id]

	@classmethod
	def authenticated(self, id = None):
		data = self.authentication(id = id)
		try: return data['enabled'] and data['valid']
		except: return False

	@classmethod
	def authenticationData(self):
		return None

	##############################################################################
	# RESOLVER
	##############################################################################

	@classmethod
	def resolver(self, id):
		if not id in External.Resolver:
			self._lock()
			if not id in External.Resolver:
				try:
					import importlib
					External.Resolver[id] = importlib.import_module(id)
				except:
					Logger.error()
					External.Resolver[id] = None
			self._unlock()

		return External.Resolver[id]

	@classmethod
	def resolverInstance(self, id, service):
		resolver = self.resolver(id = id)
		if service and resolver:
			service = service.lower()
			instances = resolver.relevant_resolvers(order_matters = True)
			for instance in instances:
				if instance.isUniversal() and service in Tools.replaceNotAlphaNumeric(instance.name.lower()):
					return instance
		return None

	##############################################################################
	# SERVICES
	##############################################################################

	@classmethod
	def services(self):
		return Cache.instance().cacheExtended(self._services)

	@classmethod
	def _services(self):
		return None

	##############################################################################
	# CACHE
	##############################################################################

	@classmethod
	def cached(self, id, sources = None, timeout = None, callback = None):
		result = []
		self._process(id = id, sources = sources, callback = callback, function = self._cached, result = result, limit = self.cachedLimit(), timeout = timeout)
		return result

	@classmethod
	def cachedLimit(self):
		return External.LimitPost

	@classmethod
	def cachedModes(self):
		return {}

	@classmethod
	def _cached(self, id, sources, callback, result, timeout):
		pass


class Orion(External):

	Id = 'orion'
	Name = 'Orion'
	Abbreviation = 'O'
	Acronym = 'OR'

	Ids = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def id(self):
		if Orion.Ids is None:
			from lib.modules.orionoid import Orionoid
			ids = []
			if Settings.getInteger('scrape.cache.inspection.premiumize') == 2: ids.append(Orionoid.DebridPremiumize)
			if Settings.getInteger('scrape.cache.inspection.offcloud') == 2: ids.append(Orionoid.DebridOffcloud)
			if Settings.getInteger('scrape.cache.inspection.torbox') == 2: ids.append(Orionoid.DebridTorbox)
			if Settings.getInteger('scrape.cache.inspection.easydebrid') == 2: ids.append(Orionoid.DebridEasydebrid)
			if Settings.getInteger('scrape.cache.inspection.realdebrid') == 2: ids.append(Orionoid.DebridRealdebrid)
			if Settings.getInteger('scrape.cache.inspection.debridlink') == 2: ids.append(Orionoid.DebridDebridlink)
			if Settings.getInteger('scrape.cache.inspection.alldebrid') == 2: ids.append(Orionoid.DebridAlldebrid)
			Orion.Ids = ids
		return Orion.Ids

	##############################################################################
	# CACHE
	##############################################################################

	@classmethod
	def cachedLimit(self):
		return External.LimitPost

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent, Core.ModeUsenet, Core.ModeHoster}

	@classmethod
	def _cached(self, id, sources, callback, result, timeout):
		from lib.modules.orionoid import Orionoid
		data = None
		try:
			data = Orionoid().debridLookup(item = id, type = self.id())
			if data:
				for hash, debrids in data.items():
					for debrid, value in debrids.items():
						if callback: callback(debrid, hash, value)
						result.append({'debrid' : debrid, 'id' : hash.lower(), 'hash' : hash.lower(), 'cached' : value})
		except:
			Logger.error()



class Debridlink(External):

	Id = 'debridlink'
	Name = 'DebridLink'
	Abbreviation = 'D'
	Acronym = 'DL'

	##############################################################################
	# REQUEST
	##############################################################################

	@classmethod
	def _request(self, mode, action, data = None, timeout = None, refresh = True):
		authentication = self.authentication()
		networker = Networker()
		networker.request(
			link = 'https://debrid-link.com/api/v2/%s/%s' % (mode, action),
			method = Networker.MethodGet,
			type = Networker.DataForm,
			timeout = timeout,
			headers = {'Authorization' : 'Bearer %s' % authentication['token']},
			data = data,
		)

		# OAuth expired. Refresh the token.
		if refresh and networker.responseErrorCode() == 401:
			instance = self.resolverInstance(id = authentication['resolver'], service = self.id())
			if instance:
				try:
					instance().refresh_token()
					return self._request(mode = mode, action = action, data = data, timeout = timeout, refresh = False)
				except: Logger.error()

		return networker.responseDataJson()

	##############################################################################
	# SERVICES
	##############################################################################

	@classmethod
	def _services(self):
		try:
			data = self._request('downloader', 'domains')
			result = [Core.ModeTorrent]
			if data and 'value' in data and data['value']: result.extend(data['value'])
			return result
		except:
			Logger.error()
			return []

	##############################################################################
	# CACHE
	##############################################################################

	@classmethod
	def cachedLimit(self):
		return External.LimitGet

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent}

	@classmethod
	def _cached(self, id, sources, callback, result, timeout):
		data = None
		try:
			data = self._request(mode = 'seedbox', action = 'cached', data = {'url' : ','.join(id)}, timeout = timeout)
			if data and 'value' in data:
				data = data['value']
				for i in id:
					if callback: callback(self.id(), i, i in data)
					result.append({'id' : i.lower(), 'hash' : i.lower(), 'cached' : i in data})
		except:
			if data and 'error' in data: Logger.log('DebridLink Cache Lookup Failure: ' + str(data['error']), type = Logger.TypeError)
			else: Logger.error()


class Alldebrid(External):

	Id = 'alldebrid'
	Name = 'AllDebrid'
	Abbreviation = 'A'
	Acronym = 'AD'

	##############################################################################
	# REQUEST
	##############################################################################

	@classmethod
	def _request(self, mode, action, data = None, timeout = None):
		return Networker().requestJson(
			link = 'https://api.alldebrid.com/v4/%s/%s?agent=%s' % (mode, action, System.name()),
			method = Networker.MethodPost,
			type = Networker.DataForm,
			timeout = timeout,
			headers = {'Authorization' : 'Bearer %s' % self.authentication()['token']},
			data = data,
		)

	##############################################################################
	# SERVICES
	##############################################################################

	@classmethod
	def _services(self):
		try:
			data = self._request('hosts', 'domains')
			data = data['data']
			result = [Core.ModeTorrent]
			if data['hosts']: result.extend(data['hosts'])
			if data['streams']: result.extend(data['streams'])
			if data['redirectors']: result.extend(data['redirectors'])
			return result
		except:
			Logger.error()
			return []

	##############################################################################
	# CACHE
	##############################################################################

	@classmethod
	def cachedLimit(self):
		return External.LimitPost

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent}

	@classmethod
	def _cached(self, id, sources, callback, result, timeout):
		data = None
		try:
			data = self._request(mode = 'magnet', action = 'instant', data = {'magnets[]' : id}, timeout = timeout)
			if data and 'data' in data:
				data = data['data']['magnets']
				for i in data:
					if callback: callback(self.id(), i['hash'], i['instant'])
					result.append({'id' : i['magnet'].lower(), 'hash' : i['hash'].lower(), 'cached' : i['instant']})
		except:
			if data and 'error' in data and 'message' in data['error']: Logger.log('AllDebrid Cache Lookup Failure: ' + str(data['error']['message']), type = Logger.TypeError)
			else: Logger.error()

class Torbox(External):

	Id = 'torbox'
	Name = 'TorBox'
	Abbreviation = 'T'
	Acronym = 'TB'

	##############################################################################
	# REQUEST
	##############################################################################

	@classmethod
	def _request(self, mode, action, data = None, method = None, timeout = None):
		return Networker().requestJson(
			link = 'https://api.torbox.app/v1/api/%s/%s' % (mode, action),
			method = method or Networker.MethodGet,
			type = Networker.DataForm,
			timeout = timeout,
			headers = {'Authorization' : 'Bearer %s' % self.authentication()['apikey']},
			data = data,
		)

	##############################################################################
	# SERVICES
	##############################################################################

	@classmethod
	def _services(self):
		try:
			data = self._request('webdl', 'hosters')
			data = data['data']
			result = [Core.ModeTorrent, Core.ModeUsenet]
			if data:
				for i in data:
					if i.get('status'): result.extend(i['domains'])
			return result
		except:
			Logger.error()
			return []

	##############################################################################
	# CACHE
	##############################################################################

	@classmethod
	def cachedLimit(self):
		return External.LimitGet

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent, Core.ModeUsenet, Core.ModeHoster}

	@classmethod
	def _cached(self, id, sources, callback, result, timeout):
		data = None
		try:
			found = {}
			lookup = {}

			torrent = []
			usenet = []
			hoster = []
			for i in range(len(id)):
				source = sources[i]['stream']

				if source.sourceTypeTorrent(): value = id[i].lower()
				else: value = Hash.md5(id[i]).lower()

				if source.sourceTypeTorrent(): torrent.append(value)
				elif source.sourceTypeUsenet(): usenet.append(value)
				elif source.sourceTypeHoster(): hoster.append(value)

				lookup[value] = id[i]

			values = {}
			if torrent: values['torrents'] = torrent
			if usenet: values['usenet'] = usenet
			if hoster: values['webdl'] = hoster

			for k, v in values.items():
				try:
					data = self._request(mode = k, action = 'checkcached', data = {'hash' : ','.join(v), 'format' : 'list'}, timeout = timeout)
					if data and 'data' in data:
						data = data['data']
						for i in data:
							hash = i['hash'].lower()
							if callback: callback(self.id(), lookup[hash], True)
							result.append({'id' : lookup[hash], 'hash' : hash, 'cached' : True})
							found[hash] = True
					for i in v:
						if not i in found:
							if callback: callback(self.id(), lookup[i], False)
							result.append({'id' : lookup[i], 'hash' : i, 'cached' : False})
							found[i] = True
				except:
					if data and ('error' in data or 'detail' in data): Logger.log('TorBox Cache Lookup Failure: ' + str(data.get('detail') or data.get('error')), type = Logger.TypeError)
					else: Logger.error()
		except:
			if data and ('error' in data or 'detail' in data): Logger.log('TorBox Cache Lookup Failure: ' + str(data.get('detail') or data.get('error')), type = Logger.TypeError)
			else: Logger.error()

class Easydebrid(External):

	Id = 'easydebrid'
	Name = 'EasyDebrid'
	Abbreviation = 'E'
	Acronym = 'ED'

	##############################################################################
	# REQUEST
	##############################################################################

	@classmethod
	def _request(self, mode, action, data = None, method = None, timeout = None, key = None):
		return Networker().requestJson(
			link = 'https://easydebrid.com/api/v1/%s/%s' % (mode, action),
			method = method or Networker.MethodGet,
			type = Networker.DataJson if method == Networker.MethodPost else Networker.DataForm,
			timeout = timeout,
			headers = {'Authorization' : 'Bearer %s' % (key or self.authentication()['key'])},
			data = data,
		)

	##############################################################################
	# AUTHENTICATION
	##############################################################################

	@classmethod
	def authenticationData(self):
		from lib.modules.account import Easydebrid as Account
		key = Account().dataKey()
		return {
			'enabled' : bool(key),
			'valid' : bool(key),
			'key' : key,
		}

	##############################################################################
	# ACCOUNT
	##############################################################################

	@classmethod
	def accountEnabled(self):
		return self.authenticationData().get('enabled')

	@classmethod
	def accountVerify(self, data = None):
		data = self._request(mode = 'user', action = 'details', key = data.get('key') if data else None)
		return bool(data and data.get('id'))

	##############################################################################
	# SERVICES
	##############################################################################

	@classmethod
	def _services(self):
		try:
			return [Core.ModeTorrent]
		except:
			Logger.error()
			return []

	##############################################################################
	# CACHE
	##############################################################################

	@classmethod
	def cachedLimit(self):
		return External.LimitPost

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent}

	@classmethod
	def _cached(self, id, sources, callback, result, timeout):
		try:
			data = self._request(mode = 'link', action = 'lookup', data = {'urls' : id}, method = Networker.MethodPost, timeout = timeout)
			if data and 'cached' in data:
				data = data['cached']
				for i in range(len(data)):
					if callback: callback(self.id(), id[i], data[i])
					result.append({'id' : id[i], 'hash' : id[i], 'cached' : data[i]})
		except: Logger.error()
