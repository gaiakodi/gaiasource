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
from lib.modules.tools import Logger, System, Tools, Settings, Resolver
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
	def _process(self, id, callback, function, result, limit = None, timeout = None):
		chunks = self._chunks(id = id, limit = limit)
		threads = []
		for chunk in chunks:
			threads.append(Pool.thread(target = function, kwargs = {'id' : chunk, 'callback' : callback, 'result' : result, 'timeout' : timeout}, start = True))
		[thread.join() for thread in threads]

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def instances(self, authenticated = True):
		instances = [Debridlink, Alldebrid]
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
			if not id in External.Authentication: External.Authentication[id] = Resolver.authenticationData(type = id)
			self._unlock()

		return External.Authentication[id]

	@classmethod
	def authenticated(self, id = None):
		data = self.authentication(id = id)
		try: return data['enabled'] and data['valid']
		except: return False

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
	def cached(self, id, timeout = None, callback = None, sources = None):
		result = []
		self._process(id = id, callback = callback, function = self._cached, result = result, limit = self.cachedLimit(), timeout = timeout)
		return result

	@classmethod
	def cachedLimit(self):
		return External.LimitPost

	@classmethod
	def cachedModes(self):
		return {}

	@classmethod
	def _cached(self, id, callback, result, timeout):
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
	def _cached(self, id, callback, result, timeout):
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
	def _cached(self, id, callback, result, timeout):
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
	def _cached(self, id, callback, result, timeout):
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
