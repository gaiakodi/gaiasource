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

try:
	from urllib.request import urlopen, Request
	from urllib.error import HTTPError, URLError
except:
	from urllib2 import urlopen, Request, HTTPError, URLError

from lib.debrid import base
from lib.modules import convert
from lib.modules import cache
from lib.modules import tools
from lib.modules import network
from lib.modules.vpn import Vpn
from lib.modules.stream import Stream
from lib.modules.concurrency import Pool, Lock
from lib.modules.account import Offcloud as Account

class Core(base.Core):

	Id = 'offcloud'
	Name = 'OffCloud'
	Abbreviation = 'O'
	Acronym = 'OC'
	Priority = 2

	LinkMain = 'https://offcloud.com'
	LinkApi = 'https://offcloud.com/api/'

	ServicesUpdate = None
	ServicesList = None
	ServiceTorrent = {'id' : 'torrent', 'name' : 'Torrent', 'domain' : 'torrent'}
	ServiceUsenet = {'id' : 'usenet', 'name' : 'Usenet', 'domain' : 'usenet'}

	ServiceStatusUnknown = 'unknown'
	ServiceStatusOnline = 'online' # working flawlessly
	ServiceStatusOffline = 'offline' # broken for the time being
	ServiceStatusCloud = 'cloud' # restricted to cloud
	ServiceStatusLimited = 'limited' # quota reached, 24 hours ETA
	ServiceStatusAwaiting = 'awaiting' # coming soon, waiting for demand
	ServiceStatusSoon = 'soon' # to be implemented within next few days

	# Methods
	MethodGet = network.Networker.MethodGet
	MethodPost = network.Networker.MethodPost
	MethodPut = network.Networker.MethodPut
	MethodDelete = network.Networker.MethodDelete

	# User Agent
	Agent = None

	# Categories
	CategoryInstant = 'instant'
	CategoryCloud = 'cloud'
	CategoryCache = 'cache'
	CategoryRemote = 'remote'
	CategoryRemoteAccount = 'remote-account'
	CategoryProxy = 'proxy'
	CategoryLogin = 'login'
	CategoryAccount = 'account'
	CategoryTorrent = 'torrent'
	CategorySites = 'sites'

	# Actions
	ActionDownload = 'download'
	ActionUpload = 'upload'
	ActionList = 'list'
	ActionStatus = 'status'
	ActionExplore = 'explore'
	ActionCheck = 'check'
	ActionGet = 'get'
	ActionStats = 'stats'
	ActionHistory = 'history'
	ActionRemove = 'remove'

	# Parameters
	ParameterApiKey = 'apiKey' # apikey does not work for POST.
	ParameterRequestId = 'requestId'
	ParameterUrl = 'url'
	ParameterProxyId = 'proxyId'
	ParameterRemoteOptionId = 'remoteOptionId'
	ParameterFolderId = 'folderId'
	ParameterHashes = 'hashes[]'
	ParameterMessages = 'messageIds[]'

	# Statuses
	StatusUnknown = 'unknown'
	StatusError = 'error'
	StatusCanceled = 'canceled'
	StatusQueued = 'queued'
	StatusBusy = 'busy'
	StatusProcessing = 'processing' # unzipping a cached archive.
	StatusInitialize = 'initialize'
	StatusFinalize = 'finalize'
	StatusFinished = 'finished'
	StatusQueued = 'queued'

	# Server
	ServerUnknown = 'unknown'
	ServerMain = 'main'
	ServerProxy = 'proxy'

	# Errors
	ErrorUnknown = 'unknown'
	ErrorOffCloud = 'offcloud'
	ErrorLimitCloud = 'limitcloud'
	ErrorLimitPremium = 'limitpremium'
	ErrorLimitLink = 'limitlink'
	ErrorLimitProxy = 'limitproxy'
	ErrorLimitVideo = 'limitvideo'
	ErrorPremium = 'premium'
	ErrorSelection = 'selection' # No file selected from list of items.
	ErrorInaccessible = 'inaccessible' # Eg: 404 error.
	ErrorCopyright = 'copyright'

	# Limits
	LimitLink = 2000 # Maximum length of a URL.
	LimitHashesGet = 40 # Maximum number of 40-character hashes to use in GET parameter so that the URL length limit is not exceeded.
	LimitHashesPost = 100 # Even when the hashes are send via POST, Premiumize seems to ignore the last ones (+- 1000 hashes). When too many hashes are sent at once (eg 500-900), if often causes a request timeout. Keep the limit small enough. Rather start multiple requests which should create multipel threads on the server.

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		base.Core.__init__(self, Core.Id, Core.Name, Core.LinkMain)

		self.mAccount = Account.instance()

		self.mDebug = True
		self.mLinkBasic = None
		self.mLinkFull = None
		self.mParameters = None
		self.mSuccess = None
		self.mError = None
		self.mResult = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _agent(self):
		if Core.Agent is None: Core.Agent = tools.System.name() + ' ' + tools.System.version()
		return Core.Agent

	def _request(self, method, link, parameters = None, data = None, headers = None, timeout = None):
		self.mResult = None
		try:
			if not timeout:
				if data: timeout = 60
				else: timeout = 30

			self.mLinkBasic = link
			self.mParameters = parameters
			self.mSuccess = None
			self.mError = None

			# If data is set, send the apikey via GET.
			if method == Core.MethodGet or method == Core.MethodPut or method == Core.MethodDelete or data:
				if parameters:
					if not link.endswith('?'):
						link += '?'
					parameters = network.Networker.linkEncode(parameters)
					link += parameters
			else:
				# urllib only sends a POST request if there is HTTP data.
				# Hence, if there are no parameters, add dummy ones.
				if not parameters: parameters = {'x' : ''}
				data = network.Networker.linkEncode(parameters)

			self.mLinkFull = link

			if data:
				try: data = data.encode('utf-8')
				except: pass
				request = Request(link, data = data)
			else: request = Request(link)

			if method == Core.MethodPut or method == Core.MethodDelete:
				request.get_method = lambda: method.upper()

			request.add_header('User-Agent', self._agent())
			if headers:
				for key in headers:
					request.add_header(key, headers[key])

			# gaiaremove - In the future rewrite this using Networker.
			if Vpn.killRequest():
				response = urlopen(request, timeout = timeout)
				self.mResult = response.read()
				response.close()
			else:
				self.mResult = None

			try:
				self.mResult = tools.Converter.jsonFrom(self.mResult)
				if self.mResult and 'error' in self.mResult:
					self.mSuccess = False
					self.mError = 'API Error'
					try:
						if self.mResult and 'downloaded yet' in self.mResult['error'].lower():
							return None # Avoid errors being printed.
					except: pass
				else:
					self.mSuccess = True
			except:
				self.mSuccess = False
				self.mError = 'JSON Error'

			if not self.mSuccess: self._requestErrors('The call to the OffCloud API failed', link, data, self.mResult)
		except (HTTPError, URLError) as error:
			self.mSuccess = False
			if hasattr(error, 'code'):
				errorCode = error.code
				errorString = ' ' + str(errorCode)
			else:
				errorCode = 0
				errorString = ''
			self.mError = 'OffCloud Unavailable [HTTP/URL Error%s]' % errorString
			self._requestErrors(self.mError, link, data, self.mResult)
		except Exception as error:
			if tools.Tools.isString(self.mResult):
				html = '<html>' in self.mResult
			else:
				html = False
			self.mSuccess = False
			if html: self.mError = 'HTML Error'
			else: self.mError = 'Unknown Error'
			self._requestErrors(self.mError, link, data, self.mResult)
		return self.mResult

	def _requestErrors(self, message, link, payload, result = None):
		if self.mDebug:
			link = str(link)
			payload = str(payload) if len(str(payload)) < 300 else 'Payload too large to display'
			result = str(result) if len(str(result)) < 300 else 'Result too large to display'
			tools.Logger.error(str(message) + (': Link [%s] Payload [%s] Result [%s]' % (link, payload, result)))

	def _retrieve(self, method, category, action = None, url = None, proxy = None, request = None, hash = None, segment = None, timeout = None, data = None, headers = None, key = None):
		if category == Core.CategoryTorrent and action == Core.ActionUpload:
			# For some reason, this function is not under the API.
			link = network.Networker.linkJoin(Core.LinkMain, category, action)
		elif category == Core.CategoryCloud and action == Core.ActionExplore:
			link = network.Networker.linkJoin(Core.LinkApi, category, action, request)
			request = None # Do not add as parameter
		elif action == Core.ActionRemove:
			link = network.Networker.linkJoin(Core.LinkMain, category, action, request)
			request = None # Do not add as parameter
		elif action:
			link = network.Networker.linkJoin(Core.LinkApi, category, action)
		else:
			link = network.Networker.linkJoin(Core.LinkApi, category)

		parameters = {}
		parameters[Core.ParameterApiKey] = key if key else self.accountInstance().dataKey()

		if not url is None: parameters[Core.ParameterUrl] = url
		if not proxy is None: parameters[Core.ParameterProxyId] = proxy
		if not request is None: parameters[Core.ParameterRequestId] = request
		if not hash is None:
			if tools.Tools.isString(hash):
				parameters[Core.ParameterHashes] = hash.lower()
			else:
				for i in range(len(hash)):
					hash[i] = hash[i].lower()
				parameters[Core.ParameterHashes] = hash
		if not segment is None:
			parameters[Core.ParameterMessages] = segment

		return self._request(method = method, link = link, parameters = parameters, data = data, headers = headers, timeout = timeout)

	##############################################################################
	# SUCCESS
	##############################################################################

	def success(self):
		return self.mSuccess

	def error(self):
		return self.mError

	def _error(self, result, default = ErrorUnknown):
		try:
			if 'not_available' in result:
				# If the premium subscription expiered (now on free subscription), OffCloud returns this error when adding a new file:
				# 	{"not_available":"torrent"}
				# Assume this is because of the expiration.
				# OffCloud was asked to add a different error for this, so maybe this can be changed in the future.
				if result['not_available'] == 'torrent' or result['not_available'] == 'usenet': result = 'unavailable'
				else: result = result['not_available']
			elif 'error' in result:
				result = result['error']
			result = result.lower()

			if result == 'unavailable': return Core.ErrorPremium
			elif 'reserved' in result and 'premium' in result: return Core.ErrorPremium
			elif 'dmca' in result or 'eucd' in result: return Core.ErrorCopyright
			elif 'cloud' in result: return Core.ErrorLimitCloud
			elif 'premium' in result: return Core.ErrorLimitPremium
			elif 'link' in result: return Core.ErrorLimitLink
			elif 'video' in result: return Core.ErrorLimitVideo
			elif 'proxy' in result: return Core.ErrorLimitProxy
		except: pass
		return default

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('internal.link.offcloud', raw = True)
		if open: network.Networker.linkShow(link = link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountAuthenticationVerify(self, data):
		try:
			account = self.account(key = data['key'])
			if account:
				label = account['email']
				if not label: label = account['user']
				return {Account.AttributeLabel : label}
			return None
		except:
			tools.Logger.error()
			return False

	def accountInstance(self):
		return self.mAccount

	def accountLabel(self):
		return self.mAccount.dataLabel()

	def accountSettings(self):
		return tools.Settings.launch('premium.offcloud.enabled')

	def accountEnabled(self):
		return self.mAccount.enabled()

	def accountEnable(self, enable = True):
		self.mAccount.enable(enable = enable)

	def accountDisable(self, disable = True):
		self.mAccount.disable(disable = disable)

	def accountValid(self):
		return self.mAccount.authenticated()

	def accountVerify(self):
		return not self.account(cached = False) is None

	def account(self, cached = True, key = None):
		try:
			if self.accountValid() or key:
				import datetime

				if key: result = self._retrieve(method = Core.MethodGet, category = Core.CategoryAccount, action = Core.ActionStats, key = key)
				elif cached: result = cache.Cache.instance().cacheShort(self._retrieve, method = Core.MethodGet, category = Core.CategoryAccount, action = Core.ActionStats)
				else: result = cache.Cache.instance().cacheClear(self._retrieve, method = Core.MethodGet, category = Core.CategoryAccount, action = Core.ActionStats)

				if result and 'userId' in result and result['userId']:
					limits = result['limits']
					expiration = tools.Time.datetime(result['expirationDate'], '%d-%m-%Y') if result['expirationDate'] else None

					return {
						'user' : result['userId'],
						'email' : result['email'],
						'premium' : result['isPremium'],
						'expiration' : {
							'timestamp' : tools.Time.timestamp(expiration) if expiration else None,
							'date' : expiration.strftime('%Y-%m-%d') if expiration else None,
							'remaining' : (expiration - datetime.datetime.today()).days if expiration else None,
						},
						'limits' : {
							'links' : limits['links'],
							'premium' : limits['premium'],
							'torrents' : limits['torrent'],
							'streaming' : limits['streaming'],
							'cloud' : {
								'bytes' : limits['cloud'],
								'description' : convert.ConverterSize(float(limits['cloud'])).stringOptimal(),
							},
							'proxy' : {
								'bytes' : limits['proxy'],
								'description' : convert.ConverterSize(float(limits['proxy'])).stringOptimal(),
							},
						},
					}
		except:
			tools.Logger.error()
		return None

	##############################################################################
	# INSTANT
	##############################################################################

	def instant(self):
		return tools.Settings.getBoolean('premium.offcloud.instant')

	def instantUpdate(self, data, settings = False):
		if data: tools.Settings.setData(id = 'premium.offcloud.instant.location', value = data, label = data['name'])
		if settings: tools.Settings.launchData('premium.offcloud.instant.location')

	##############################################################################
	# SERVICES
	##############################################################################

	def services(self, cached = True, onlyEnabled = False):
		# Even thow ServicesUpdate is a class variable, it will be destrcucted if there are no more OffCloud instances.
		if Core.ServicesUpdate is None:
			Core.ServicesUpdate = []

			streamingTorrent = self.streamingTorrent()
			streamingUsenet = self.streamingUsenet()
			streamingHoster = self.streamingHoster()

			try:
				if cached: result = cache.Cache.instance().cacheShort(self._retrieve, method = Core.MethodGet, category = Core.CategorySites)
				else: result = cache.Cache.instance().cacheClear(self._retrieve, method = Core.MethodGet, category = Core.CategorySites)

				# Sometimes error HTML page is returned.
				if not tools.Tools.isArray(result):
					Core.ServicesUpdate = None
					return None

				usenet = None
				for i in result:
					id = i['name']
					if id == Core.ServiceUsenet['id']:
						enabled = streamingUsenet
						name = Core.ServiceUsenet['name']
						domain = Core.ServiceUsenet['domain']
						domains = []
					else:
						enabled = streamingHoster

						name = i['displayName']
						index = name.find('.')
						if index >= 0: name = name[:index]
						name = name.title()

						domain = i['displayName'].lower()
						if not '.' in domain: domain = i['hosts'][0].lower()

						# Often has www or other sudomains.
						domain = network.Networker.linkDomain(domain, subdomain = False, topdomain = True, ip = True)

						domains = [j for j in i['hosts'] if '.' in j] # Some domains are not real domains, but just IDs (eg "tf1").
						domains = list(set([network.Networker.linkDomain(d, subdomain = False, topdomain = True, ip = True) for d in domains]))
						domains = [j for j in domains if '.' in j] # Some TLDs are not detected by tldextract in linkDomain (eg ft TLD in "tf1.ft").

					try: instant = not bool(i['noInstantDownload'])
					except: instant = True

					try: stream = bool(i['isVideoStreaming'])
					except: stream = False

					try:
						status = i['isActive'].lower()
						if 'healthy' in status: status = Core.ServiceStatusOnline
						elif 'dead' in status: status = Core.ServiceStatusOffline
						elif 'cloud' in status: status = Core.ServiceStatusCloud
						elif 'limited' in status: status = Core.ServiceStatusLimited
						elif 'awaiting' in status: status = Core.ServiceStatusAwaiting
						elif 'r&d' in status: status = Core.ServiceStatusSoon
						else: status = Core.ServiceStatusUnknown
					except:
						status = Core.ServiceStatusUnknown

					try:
						limitSize = i['maxAmountPerUser']
						if tools.Tools.isString(limitSize) and 'unlimited' in limitSize.lower(): limitSize = 0
						else: limitSize = long(limitSize)
					except:
						limitSize = 0

					try:
						limitChunks = i['maxChunks']
						if tools.Tools.isString(limitChunks) and 'unlimited' in limitChunks.lower(): limitChunks = 0
						else: limitChunks = long(limitChunks)
					except:
						limitChunks = 0

					try:
						limitGlobal = i['maxChunksGlobal']
						if tools.Tools.isString(limitGlobal) and 'unlimited' in limitGlobal.lower(): limitGlobal = 0
						else: limitGlobal = long(limitGlobal)
					except:
						limitGlobal = 0

					item = {
						'id' : id,
						'enabled' : enabled and status == Core.ServiceStatusOnline,
						'hoster' : True,
						'status' : status,
						'instant' : instant,
						'stream' : stream,
						'name' : name,
						'domain' : domain,
						'domains' : domains,
						'limits' :
						{
							'size' : limitSize,
							'chunks' : limitChunks,
							'global' : limitGlobal,
						},
					}
					if id == Core.ServiceUsenet['id']:
						item['hoster'] = False
						usenet = item
					else:
						Core.ServicesUpdate.append(item)

				Core.ServicesUpdate = sorted(Core.ServicesUpdate, key = lambda i : len(i['id']))
				Core.ServicesUpdate.insert(0, usenet)
				Core.ServicesUpdate.insert(0, {
					'id' : Core.ServiceTorrent['id'],
					'enabled' : streamingTorrent,
					'hoster' : False,
					'status' : Core.ServiceStatusOnline,
					'instant' : True,
					'stream' : False,
					'name' : Core.ServiceTorrent['name'],
					'domain' : Core.ServiceTorrent['domain'],
					'domains' : [],
					'limits' :
					{
						'size' : 0,
						'chunks' : 0,
						'global' : 0,
					},
				})

			except:
				tools.Logger.error()

		if onlyEnabled:
			return [i for i in Core.ServicesUpdate if i['enabled']]
		else:
			return Core.ServicesUpdate

	def servicesList(self, onlyEnabled = False):
		if Core.ServicesList is None:
			services = self.services(onlyEnabled = onlyEnabled)
			if services:
				special = [service['id'] for service in services if not service['hoster']]
				result = []
				for service in services:
					if service['hoster']:
						if 'domain' in service: result.append(service['domain'])
						if 'domains' in service: result.extend(service['domains'])
				result = sorted(list(set(result)))
				Core.ServicesList = special + result
		return Core.ServicesList

	def service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		for service in self.services():
			if service['id'].lower() == nameOrDomain or service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain or ('domains' in service and nameOrDomain in [i.lower() for i in service['domains']]):
				return service
		return None

	##############################################################################
	# PROXY
	##############################################################################

	def proxyList(self):
		try:
			result = self._retrieve(method = Core.MethodPost, category = Core.CategoryProxy, action = Core.ActionList)
			if self.success():
				proxies = []
				result = result['list']
				for proxy in result:
					try:
						location = re.search('\\(([^(0-9)]*)', proxy['name']).group(1).strip()
						location = location.replace('US', 'United States')
						location = location.replace(',', ' -')
					except:
						tools.Logger.error()
						location = None

					try:
						type = re.search('(.*)\\(', proxy['name']).group(1).strip().lower()
						if Core.ServerMain in type: type = Core.ServerMain
						elif Core.ServerProxy in type: type = Core.ServerProxy
						else: type = Core.ServerUnknown
					except:
						type = Core.ServerUnknown

					try:
						if not location == None and not type == Core.ServerUnknown:
							description = '[' + type.capitalize() + '] ' + location
						elif not location == None:
							description = location
						else:
							description = proxy['name']
					except:
						description = proxy['name']

					if not location == None: name = location
					else: name = proxy['name']

					proxies.append({
						'id' : proxy['id'],
						'type' : type,
						'location' : location,
						'region' : proxy['region'].lower(),
						'name' : name,
						'description' : description,
					})
				return proxies
		except:
			tools.Logger.error()
		return None

	##############################################################################
	# ADD
	##############################################################################

	def _addLink(self, category = CategoryCloud, result = None, title = None, year = None, season = None, episode = None, pack = False, strict = False):
		id = None
		link = None
		items = None
		error = None

		try:
			if 'not_available' in result or 'error' in result:
				error = self._error(result)
			elif 'requestId' in result:
				id = result['requestId']
				try:
					items = self.item(category = category, id = id, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, transfer = True, files = True)
					link = items['video']['link']
				except: pass
		except:
			pass
		return self.addResult(error = error, id = id, link = link, items = items, category = category, strict = strict)

	def _addType(self, link, type = None):
		if not type:
			type = network.Container(link).type()
			if type == network.Container.TypeUnknown:
				type = network.Container.TypeHoster
		return type

	def _addCategory(self, link = None, type = None):
		type = self._addType(link = link, type = type)
		if type == network.Container.TypeTorrent or type == network.Container.TypeUsenet:
			return Core.CategoryCloud
		else:
			if tools.Settings.getBoolean('premium.offcloud.instant'): return Core.CategoryInstant
			else: return Core.CategoryCloud

	def _addProxy(self):
		try: result = tools.Settings.getData('premium.offcloud.instant.location')['id']
		except: result = None
		return result

	def add(self, link, category = None, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False, type = None, proxy = None):
		type = self._addType(link = link, type = type)
		if category == None: category = self._addCategory(type = type)
		if category == Core.CategoryInstant and proxy == None: proxy = self._addProxy()
		if type == network.Container.TypeTorrent:
			return self.addTorrent(link = link, name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
		elif type == network.Container.TypeUsenet:
			return self.addUsenet(link = link, name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
		else:
			return self.addHoster(link = link, category = category, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, proxy = proxy)

	def addInstant(self, link, title = None, year = None, season = None, episode = None, pack = False, strict = False, proxy = None):
		result = self._retrieve(method = Core.MethodPost, category = Core.CategoryInstant, action = Core.ActionDownload, url = link, proxy = proxy)
		if self.success(): return self._addLink(category = Core.CategoryInstant, result = result, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
		else: return self.addResult(error = self._error(result, default = Core.ErrorOffCloud))

	def addCloud(self, link, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False, type = None):
		result = self._retrieve(method = Core.MethodPost, category = Core.CategoryCloud, action = Core.ActionDownload, url = link)
		if self.success(): return self._addLink(category = Core.CategoryCloud, result = result, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
		else: return self.addResult(error = self._error(result, default = Core.ErrorOffCloud))

	# Downloads the torrent, nzb, or any other container supported by Core.
	# If mode is not specified, tries to detect the file type automatically.
	def addContainer(self, link, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False):
		try:
			source = network.Container(link, download = True).information()
			if source['path'] == None and source['data'] == None: # Sometimes the NZB cannot be download, such as 404 errors.
				return self.addResult(error = Core.ErrorInaccessible)

			if not name:
				try: name = source['stream'].fileName(generate = True)
				except: pass
				if not name:
					try: name = source['stream'].hash()
					except: pass
					if not name: name = 'Download'

			# Only needed for Premiumize, but also use here, in case they have the same problems.
			# Name must end in an extension, otherwise Premiumize throws an "unknown type" error for NZBs.
			if source['extension'] and not name.endswith(source['extension']): name += source['extension']

			boundry = 'X-X-X'
			headers = {'Content-Type' : 'multipart/form-data; boundary=%s' % boundry}

			# Important: OffCloud requires new lines with \r\n, otherwise there are "unexpected errors".
			data = bytearray('--%s\r\n' % boundry, 'utf8')
			data += bytearray('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % name, 'utf8')
			data += bytearray('Content-Type: %s\r\n\r\n' % source['mime'], 'utf8')
			data += source['data']
			data += bytearray('\r\n--%s--\r\n' % boundry, 'utf8')

			result = self._retrieve(method = Core.MethodPost, category = Core.CategoryTorrent, action = Core.ActionUpload, data = data, headers = headers)
			if self.success(): return self.addCloud(link = result['url'], name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
			else: return self.addResult(error = self._error(result, default = Core.ErrorOffCloud))
		except:
			tools.Logger.error()
			return self.addResult(error = Core.ErrorOffCloud)

	def addHoster(self, link, category = CategoryInstant, title = None, year = None, season = None, episode = None, pack = False, strict = False, proxy = None):
		if category == Core.CategoryInstant:
			return self.addInstant(link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, proxy = proxy)
		else:
			return self.addCloud(link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)

	def addTorrent(self, link, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False):
		container = network.Container(link)
		source = container.information()
		if source['magnet']:
			return self.addCloud(link = container.torrentMagnet(title = name, encode = False), name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
		else:
			return self.addContainer(link = link, name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)

	def addUsenet(self, link, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False):
		return self.addContainer(link = link, name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)

	##############################################################################
	# DOWNLOADS
	##############################################################################

	def downloadInformation(self, category = None):
		items = self.items(category = category)
		if tools.Tools.isArray(items):
			from lib.modules import interface
			unknown = interface.Translation.string(33387)

			count = [0, 0]
			countBusy = [0, 0]
			countFinished = [0, 0]
			countFailed = [0, 0]
			countCanceled = [0, 0]
			size = [0, 0]
			sizeValue = [0, 0]
			sizeDescription = [unknown, unknown]

			for item in items:
				index = 0 if item['category'] == Core.CategoryInstant else 1
				status = item['status']
				try: size[index] += item['size']['bytes']
				except: pass
				count[index] += 1
				if status in [Core.StatusUnknown, Core.StatusError]:
					countFailed[index] += 1
				elif status in [Core.StatusCanceled]:
					countCanceled[index] += 1
				elif status in [Core.StatusFinished]:
					countFinished[index] += 1
				else:
					countBusy[index] += 1

			if not size[0] == 0:
				size[0] = convert.ConverterSize(value = size[0], unit = convert.ConverterSize.Byte)
				sizeValue[0] = size[0].value()
				sizeDescription[0] = size[0].stringOptimal()
			if not size[1] == 0:
				size[1] = convert.ConverterSize(value = size[1], unit = convert.ConverterSize.Byte)
				sizeValue[1] = size[1].value()
				sizeDescription[1] = size[1].stringOptimal()

			result = {
				'limits' : self.account()['limits']
			}
			if category == None or category == Core.CategoryInstant:
				result.update({
					'instant' : {
						'count' : {
							'total' : count[0],
							'busy' : countBusy[0],
							'finished' : countFinished[0],
							'canceled' : countCanceled[0],
							'failed' : countFailed[0],
						},
						'size' : {
							'bytes' : sizeValue[0],
							'description' : sizeDescription[0],
						},
					},
				})
			if category == None or category == Core.CategoryCloud:
				result.update({
					'cloud' : {
						'count' : {
							'total' : count[1],
							'busy' : countBusy[1],
							'finished' : countFinished[1],
							'canceled' : countCanceled[1],
							'failed' : countFailed[1],
						},
						'size' : {
							'bytes' : sizeValue[1],
							'description' : sizeDescription[1],
						},
					},
				})
			return result
		else:
			return Core.ErrorOffCloud

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent, Core.ModeUsenet}

	# id: single hash or list of hashes.
	def cachedIs(self, id, timeout = None):
		result = self.cached(id = id, timeout = timeout)
		if tools.Tools.isDictionary(result): return result['cached']
		elif tools.Tools.isArray(result): return [i['cached'] for i in result]
		else: return False

	# id: single hash or list of hashes.
	# NB: a URL has a maximum length. Hence, a list of hashes cannot be too long, otherwise the request will fail.
	def cached(self, id, timeout = None, callback = None, sources = None):
		try:
			single = tools.Tools.isString(id)
			if single: id = [id] # Must be passed in as a list.

			method = Core.MethodPost # Post can send more at a time.
			if method == Core.MethodPost:
				chunks = [sources[i:i + Core.LimitHashesPost] for i in range(0, len(sources), Core.LimitHashesPost)]
			else:
				chunks = [sources[i:i + Core.LimitHashesGet] for i in range(0, len(sources), Core.LimitHashesGet)]
			for chunk in chunks:
				for c in range(len(chunk)):
					chunk[c] = [chunk[c]['stream'].hashContainer(), chunk[c]['stream'].segment(best = True)]

			self.tCacheLock = Lock()
			self.tCacheResult = []

			def cachedChunk(callback, method, chunk, timeout):
				try:
					hashes = [c[0] for c in chunk if not c[0] is None]
					segments = [c[1] for c in chunk if not c[1] is None]
					offcloud = Core()
					result = offcloud._retrieve(method = method, category = Core.CategoryCache, hash = hashes, segment = segments, timeout = timeout)
					if offcloud.success():
						cached = [i.lower() for i in result['cachedItems']]
						claimed = result['claimedItems'] if 'claimedItems' in result else None
						self.tCacheLock.acquire()
						self.tCacheResult.extend(result)
						self.tCacheLock.release()
						if callback:
							for c in chunk:
								try: callback(self.id(), c[0], c[0] in cached and (c[1] is None or claimed is None or not c[1] in claimed))
								except: pass
				except:
					tools.Logger.error()

			threads = []
			for chunk in chunks:
				thread = Pool.thread(target = cachedChunk, args = (callback, method, chunk, timeout))
				threads.append(thread)
				thread.start()

			[i.join() for i in threads]
			if not callback:
				caches = []
				for source in sources:
					hash = source['stream'].hashContainer()
					segment = source['stream'].segment(best = True)
					caches.append({'id' : hash, 'hash' : hash, 'cached' : hash in self.tCacheResult['cachedItems'] and (segment is None or self.tCacheResult['claimedItems'] is None or not segment in self.tCacheResult['claimedItems'])})
				if single: return caches[0] if len(caches) > 0 else False
				else: return caches
		except:
			tools.Logger.error()

	##############################################################################
	# ITEM
	##############################################################################

	def _itemStatus(self, status):
		status = status.lower()
		if status == 'downloading': return Core.StatusBusy
		elif status == 'downloaded': return Core.StatusFinished
		elif status == 'created': return Core.StatusInitialize
		elif status == 'processing': return Core.StatusFinalize
		elif status == 'error': return Core.StatusError
		elif status == 'queued': return Core.StatusQueued
		elif status == 'canceled': return Core.StatusCanceled
		elif status == 'fragile': return Core.StatusError
		else: return Core.StatusUnknown

	def _itemFile(self, link):
		name = link.split('/')[-1]
		try: extension = name.split('.')[-1]
		except: extension = None
		stream = tools.Video.extensionValid(extension)
		return {
			'link' : link,
			'name' : name,
			'extension' : extension,
			'stream' : stream,
		}

	# season, episode, transfer and files only for cloud.
	def item(self, category, id, title = None, year = None, season = None, episode = None, pack = False, strict = False, transfer = True, files = True):
		if category == Core.CategoryInstant:
			return self.itemInstant(id = id)
		elif category == Core.CategoryCloud:
			return self.itemCloud(id = id, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, transfer = transfer, files = files)
		else:
			return None

	def itemInstant(self, id):
		# Not supported by API.
		# Retrieve entier instant download list and pick the correct one from it.
		items = self.items(category = Core.CategoryInstant)
		for i in items:
			if i['id'] == id:
				return i
		return None

	# transfer requires an one API call.
	# files requires an one API call.
	def itemCloud(self, id, title = None, year = None, season = None, episode = None, pack = False, strict = False, transfer = True, files = True):
		try:
			self.tResulTransfer = None;
			self.tResulContent = None;

			def _itemTransfer(id):
				try: self.tResulTransfer = Core()._retrieve(method = Core.MethodPost, category = Core.CategoryCloud, action = Core.ActionStatus, request = id)['status']
				except: pass

			def _itemContent(id):
				try:
					self.tResulContent = Core()._retrieve(method = Core.MethodGet, category = Core.CategoryCloud, action = Core.ActionExplore, request = id)
					if 'error' in self.tResulContent: self.tResulContent = None # Some cloud downloads do not support exploring. They only contain a single file (eg YouTube downloads).
				except: pass

			threads = []
			if transfer: threads.append(Pool.thread(target = _itemTransfer, args = (id,)))
			if files: threads.append(Pool.thread(target = _itemContent, args = (id,)))
			[i.start() for i in threads]
			[i.join() for i in threads]

			result = {
				'id' : id,
				'category' : Core.CategoryCloud,
			}

			if self.tResulTransfer:
				status = self._itemStatus(self.tResulTransfer['status'])

				error = None
				try: error = self.tResulTransfer['errorMessage']
				except: pass

				directory = False
				try: directory = self.tResulTransfer['isDirectory']
				except: pass

				name = None
				try: name = self.tResulTransfer['fileName']
				except: pass

				server = None
				try: server = self.tResulTransfer['server']
				except: pass

				size = 0
				try: size = long(self.tResulTransfer['fileSize'])
				except: pass
				sizeObject = convert.ConverterSize(size)

				speed = 0
				try:
					speed = float(re.sub('[^0123456789\.]', '', self.tResulTransfer['downloadingSpeed']))
					speedObject = convert.ConverterSpeed(speed, unit = convert.ConverterSpeed.Byte)
				except:
					# Hoster links downloaded through the cloud.
					try:
						speed = self.tResulTransfer['info'].replace('-', '').strip()
						speedObject = convert.ConverterSpeed(speed)
						speed = speedObject.value(unit = convert.ConverterSpeed.Byte)
					except:
						speedObject = convert.ConverterSpeed(speed, unit = convert.ConverterSpeed.Byte)

				progressValueCompleted = 0
				progressValueRemaining = 0
				progressPercentageCompleted = 0
				progressPercentageRemaining = 0
				progressSizeCompleted = 0
				progressSizeRemaining = 0
				progressTimeCompleted = 0
				progressTimeRemaining = 0
				if status == Core.StatusFinished:
					progressValueCompleted = 1
					progressPercentageCompleted = 1
					progressSizeCompleted = size
				else:
					try:
						progressSizeCompleted = long(self.tResulTransfer['amount'])
						progressSizeRemaining = size - progressSizeCompleted

						progressValueCompleted = progressSizeCompleted / float(size)
						progressValueRemaining = 1 - progressValueCompleted

						progressPercentageCompleted = round(progressValueCompleted * 100, 1)
						progressPercentageRemaining = round(progressValueRemaining * 100, 1)

						progressTimeCompleted = long(self.tResulTransfer['downloadingTime']) / 1000
						progressTimeRemaining = long(progressSizeRemaining / float(speed))
					except:
						pass
				progressSizeCompletedObject = convert.ConverterSize(progressSizeCompleted)
				progressSizeRemainingObject = convert.ConverterSize(progressSizeRemaining)
				progressTimeCompletedObject = convert.ConverterDuration(progressTimeCompleted, convert.ConverterDuration.UnitSecond)
				progressTimeRemainingObject = convert.ConverterDuration(progressTimeRemaining, convert.ConverterDuration.UnitSecond)

				result.update({
					'name' : name,
					'server' : server,
					'status' : status,
					'error' : error,
					'directory' : directory,
					'size' : {
						'bytes' : sizeObject.value(),
						'description' : sizeObject.stringOptimal(),
					},
					'transfer' : {
						'speed' : {
							'bytes' : speedObject.value(convert.ConverterSpeed.Byte),
							'bits' : speedObject.value(convert.ConverterSpeed.Bit),
							'description' : speedObject.stringOptimal(),
						},
						'progress' : {
							'completed' : {
								'value' : progressValueCompleted,
								'percentage' : progressPercentageCompleted,
								'size' : {
									'bytes' : progressSizeCompletedObject.value(),
									'description' : progressSizeCompletedObject.stringOptimal(),
								},
								'time' : {
									'seconds' : progressTimeCompletedObject.value(convert.ConverterDuration.UnitSecond),
									'description' : progressTimeCompletedObject.string(convert.ConverterDuration.FormatDefault),
								},
							},
							'remaining' : {
								'value' : progressValueRemaining,
								'percentage' : progressPercentageRemaining,
								'size' : {
									'bytes' : progressSizeRemainingObject.value(),
									'description' : progressSizeRemainingObject.stringOptimal(),
								},
								'time' : {
									'seconds' : progressTimeRemainingObject.value(convert.ConverterDuration.UnitSecond),
									'description' : progressTimeRemainingObject.string(convert.ConverterDuration.FormatDefault),
								},

							},
						}
					},
				})

				# Cloud downloads with a single file have no way of returning the link.
				# cloud/history and cloud/status do not return the link, and cloud/explore returns "bad archive" for single files.
				# Construct the link manually.
				# This should be removed once OffCloud updates their API to fix this.
				if not self.tResulContent and not directory and status == Core.StatusFinished and not server == None and not server == '':
					self.tResulContent = ['https://%s.offcloud.com/cloud/download/%s/%s' % (server, id, network.Networker.linkQuote(name, plus = True))]

			if self.tResulContent:
				video = None
				files = []
				filesVideo = []
				filesSelection = []

				for i in self.tResulContent:
					file = self._itemFile(i)
					files.append(file)
					if file['stream']: filesVideo.append(file)

				if len(filesVideo) > 0: filesSelection = filesVideo
				elif len(files) > 0: filesSelection = files

				validTitles = []
				validEpisodes = []
				items = []
				for i in filesSelection:
					# Somtimes the parent folder name contains part of the name and the actual file the other part.
					# Eg: Folder = "Better Call Saul Season 1", File "Part 1 - Episode Name"
					try: items.append({'name' : i['name'], 'path' : name + ' ' + i['name'], 'file' : i})
					except: items.append({'name' : i['name'], 'file' : i})

				# Movie collections.
				if video is None and not season and not episode and pack:
					# Match titles with an increased "adjust" ratio.
					# Movies in collection packs have very similar names (eg: "The Lord of the Rings - The Two Towers" vs "The Lord of the Rings - The Return of the King").
					# The incorrect movie might be picked, hence start with a very strict matching ratio, and reduce it bit-by-bit until we find the first and highest/best match.
					lookupFiles = []
					lookupValues1 = []
					lookupValues2 = []
					for item in items:
						lookupValues1.append(item['name'])
						lookup = []
						try: lookup.append(item['path'])
						except: pass
						lookup.append(item['name'])
						lookupValues2.append(lookup)
						lookupFiles.append(item['file'])

					# First try the individual file names, and only if nothing was found, try with the full folder path and name.
					# Otherwise this file will match for "The Terminator 1984":
					#	The Terminator Collection (1984-2019) 2009.Terminator.Salvation.1920x800.BDRip.x264.DTS-HD.MA.mkv
					index = Stream.titlesValid(media = tools.Media.Movie, data = lookupValues1, title = title, year = year, filter = True, quick = True, exclude = True, valid = validTitles)
					if index is None: index = Stream.titlesValid(media = tools.Media.Movie, data = lookupValues2, title = title, year = year, filter = True, quick = True, exclude = True, valid = validTitles)
					if not index is None: video = lookupFiles[index]
					validTitles = [lookupFiles[i] for i in validTitles]

				# Individual movies and season-episodes.
				if video is None:
					for item in items:
						path = item['path'] if 'path' in item else item['name']
						if not(season and episode) or Stream.numberShowValid(data = path, season = season, episode = episode, single = True):
							validTitles.append(item['file'])
							if not Stream.titleProhibited(data = path, title = title, exception = not season is None and season == 0):
								video = item['file']
								break

				# Only episodes.
				if video is None and episode:
					for item in items:
						path = item['path'] if 'path' in item else item['name']
						if Stream.numberShowValid(data = path, episode = episode, single = True):
							validEpisodes.append(item['file'])
							if not Stream.titleProhibited(data = path, title = title, exception = not season is None and season == 0):
								video = item['file']
								break

				if video is None:
					if len(validTitles) > 0:
						if season is None and episode is None: video = max(validTitles, key = len) # Choose the longest file name from the list.
						else: video = validTitles[0]
					elif len(validEpisodes) > 0:
						video = validEpisodes[0]

				if video is None and not strict:
					if len(filesVideo) > 0: video = filesVideo[0]
					elif len(files) > 0: video = files[0]

				result.update({
					'files' : files,
					'video' : video,
				})

			self.tResulTransfer = None
			self.tResulContent = None

			return result
		except:
			tools.Logger.error()
		return None

	def itemsInstant(self):
		return self.items(category = Core.CategoryInstant)

	def itemsCloud(self):
		return self.items(category = Core.CategoryCloud)

	def items(self, category = None):
		try:
			if category is None:
				threads = []
				self.tResultItemsInstant = None
				self.tResultItemsCloud = None
				def _itemsInstant():
					self.tResultItemsInstant = Core().items(category = Core.CategoryInstant)
				def _itemsCloud():
					self.tResultItemsCloud = Core().items(category = Core.CategoryCloud)
				threads.append(Pool.thread(target = _itemsInstant))
				threads.append(Pool.thread(target = _itemsCloud))
				[i.start() for i in threads]
				[i.join() for i in threads]

				result = []
				if self.tResultItemsInstant: result += self.tResultItemsInstant
				if self.tResultItemsCloud: result += self.tResultItemsCloud
				self.tResultItemsInstant = None
				self.tResultItemsCloud = None
				return result
			else:
				items = []
				result = self._retrieve(method = Core.MethodGet, category = category, action = Core.ActionHistory)
				for i in result:
					status = self._itemStatus(i['status'])
					files = []

					# Instant links always stay at created.
					if category == Core.CategoryInstant:
						if status == Core.StatusInitialize: status = Core.StatusFinished
						try: files = [self._itemFile(i['downloadLink'])]
						except: pass

					try: id = i['requestId']
					except: id = None
					try: name = i['fileName']
					except: name = None
					try: directory = i['isDirectory']
					except: directory = False
					try: server = i['server']
					except: server = None
					try: time = convert.ConverterTime(i['createdOn'], format = convert.ConverterTime.FormatDateTimeJson).timestamp()
					except: time = None
					try: metadata = i['metaData']
					except: metadata = None

					# Do not include hidden items with an error status. These are internal control items from Core.
					if not(status == Core.StatusError and metadata == 'hide'):
						items.append({
							'id' : id,
							'category' : category,
							'status' : status,
							'name' : name,
							'directory' : directory,
							'server' : server,
							'time' : time,
							'files' : files,
							'video' : None if len(files) == 0 else files[0],
						})
				return items
		except:
			tools.Logger.error()
		return None

	##############################################################################
	# ID
	##############################################################################

	@classmethod
	def idItem(self, idOrLink):
		if network.Networker.linkIs(idOrLink):
			# Matches LAST occurance of a hash.
			# Instant links have both the user account hash and file hash in the link.
			id = re.search('[a-zA-Z0-9]{24}(?!.*[a-zA-Z0-9]{24})', idOrLink, re.IGNORECASE).group(0)
		else:
			return idOrLink

	##############################################################################
	# DELETE
	##############################################################################

	@classmethod
	def deletePossible(self, type):
		return True

	# id can be an ID or link.
	def delete(self, id, category = CategoryCloud, wait = True):
		def _delete(id, category):
			result = self._retrieve(method = Core.MethodGet, category = category, action = Core.ActionRemove, request = id)
			if self.success(): return True
			else: return Core.ErrorOffCloud

		if category == None: category = Core.CategoryCloud
		id = self.idItem(id)
		if wait:
			return _delete(id, category)
		else:
			thread = Pool.thread(target = _delete, args = (id, category))
			thread.start()

	def deleteInstant(self, id):
		return self.delete(id = id, category = Core.CategoryInstant)

	def deleteCloud(self, id):
		return self.delete(id = id, category = Core.CategoryCloud)

	def deleteAll(self, category = None, wait = True):
		items = self.items(category = category)
		if tools.Tools.isArray(items):
			if len(items) > 0:
				def _deleteAll(category, id):
					Core().delete(category = category, id = id)
				threads = []
				for item in items:
					threads.append(Pool.thread(target = _deleteAll, args = (item['category'], item['id'])))

				# Complete the first thread in case the token has to be refreshed.
				threads[0].start()
				threads[0].join()

				for i in range(1, len(threads)):
					threads[i].start()
				if wait:
					for i in range(1, len(threads)):
						threads[i].join()
			return True
		else:
			return Core.ErrorOffCloud

	def deleteAllInstant(self, wait = True):
		return self.deleteAll(category = Core.CategoryInstant, wait = wait)

	def deleteAllCloud(self, wait = True):
		return self.deleteAll(category = Core.CategoryCloud, wait = wait)

	# Delete on launch
	def deleteLaunch(self):
		try:
			if tools.Settings.getBoolean('premium.offcloud.removal'):
				option = tools.Settings.getInteger('premium.offcloud.removal.launch')
				if option == 1: self.deleteAll(wait = False)
		except: tools.Logger.error()

	# Delete on playback ended
	# id can be an ID or link.
	def deletePlayback(self, id, pack = None, category = None):
		try:
			if tools.Settings.getBoolean('premium.offcloud.removal'):
				option = tools.Settings.getInteger('premium.offcloud.removal.playback')
				if option == 1: self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack): self.delete(id = id, category = category, wait = False)
		except: tools.Logger.error()

	# Delete on failure
	# id can be an ID or link.
	def deleteFailure(self, id, pack = None, category = None):
		try:
			if tools.Settings.getBoolean('premium.offcloud.removal'):
				option = tools.Settings.getInteger('premium.offcloud.removal.failure')
				if option == 1: self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack): self.delete(id = id, category = category, wait = False)
		except: tools.Logger.error()
