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

try:
	from urllib.request import urlopen, Request
	from urllib.error import HTTPError, URLError
except:
	from urllib2 import urlopen, Request, HTTPError, URLError

from lib.debrid import base
from lib.modules import convert
from lib.modules import cache
from lib.modules import tools
from lib.modules import interface
from lib.modules import network
from lib.modules.vpn import Vpn
from lib.modules.stream import Stream
from lib.modules.concurrency import Pool, Lock
from lib.modules.account import Realdebrid as Account

class Core(base.Core):

	Id = 'realdebrid'
	Name = 'RealDebrid'
	Abbreviation = 'R'
	Acronym = 'RD'
	Priority = 3

	# Service Statuses
	ServiceStatusUp = 'up'
	ServiceStatusDown = 'down'
	ServiceStatusUnsupported = 'unsupported'

	ServicesUpdate = None
	ServicesList = None
	ServicesTorrent = [
		{	'name' : 'Torrent',		'id' : 'torrent',	'domain' : '',	'status' : ServiceStatusUp,	'supported' : True,	'hoster' : False,	},
	]

	#Links
	LinkMain = 'https://real-debrid.com'
	LinkApi = 'https://api.real-debrid.com/rest/1.0'
	LinkAuthentication = 'https://api.real-debrid.com/oauth/v2'

	# Methods
	MethodGet = network.Networker.MethodGet
	MethodPost = network.Networker.MethodPost
	MethodPut = network.Networker.MethodPut
	MethodDelete = network.Networker.MethodDelete

	# Types
	TypeTorrent = 'torrent'

	# Statuses
	StatusUnknown = 'unknown'
	StatusError = 'error'
	StatusMagnetError = 'magnet_error'
	StatusMagnetConversion = 'magnet_conversion'
	StatusFileSelection = 'waiting_files_selection'
	StatusQueued = 'queued'
	StatusBusy = 'downloading'
	StatusFinished = 'downloaded'
	StatusVirus = 'virus'
	StatusCompressing = 'compressing'
	StatusUploading = 'uploading'
	StatusDead = 'dead'

	# Categories
	CategoryUser = 'user'
	CategoryHosts = 'hosts'
	CategoryToken = 'token'
	CategoryDevice = 'device'
	CategoryUnrestrict = 'unrestrict'
	CategoryTorrents = 'torrents'
	CategoryTime = 'time'

	# Actions
	ActionStatus = 'status'
	ActionCode = 'code'
	ActionCredentials = 'credentials'
	ActionLink = 'link'
	ActionAddTorrent = 'addTorrent'
	ActionAddMagnet = 'addMagnet'
	ActionActive = 'activeCount'
	ActionInfo = 'info'
	ActionAvailableHosts = 'availableHosts'
	ActionSelectFiles = 'selectFiles'
	ActionDelete = 'delete'
	ActionInstantAvailability = 'instantAvailability'
	ActionDomains = 'domains'

	# Parameters
	ParameterClientId = 'client_id'
	ParameterClientSecret = 'client_secret'
	ParameterCode = 'code'
	ParameterGrantType = 'grant_type'
	ParameterNewCredentials = 'new_credentials'
	ParameterLink = 'link'
	ParameterMagnet = 'magnet'
	ParameterFiles = 'files'

	# Errors
	ErrorUnknown = 'unknown'
	ErrorInaccessible = 'inaccessible' # Eg: 404 error.
	ErrorUnavailable = 'unavailable' # When season pack does not contain a certain episode. Or if there is not usable file in the download.
	ErrorRealDebrid = 'realdebrid' # Error from RealDebrid server.
	ErrorBlocked = 'blocked' # User IP address blocked.
	ErrorDone = 'action_already_done' # Action already done.

	# Selection
	SelectionAll = 'all'
	SelectionName = 'name'
	SelectionFile = 'file'
	SelectionLargest = 'largest'

	# Limits
	LimitLink = 2000 # Maximum length of a URL.
	LimitHashesGet = 40 # Maximum number of 40-character hashes to use in GET parameter so that the URL length limit is not exceeded.

	# Time
	TimeOffset = None

	# User Agent
	Agent = None

	# Client
	ClientId = None
	ClientGrant = 'http://oauth.net/grant_type/device/1.0'

	# Authentication
	AuthenticationDone = None
	AuthenticationLock = Lock()

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, debug = True):
		base.Core.__init__(self, Core.Id, Core.Name, Core.LinkMain)

		self.mAccount = Account()

		self.mDebug = debug
		self.mLinkBasic = None
		self.mLinkFull = None
		self.mParameters = None
		self.mSuccess = None
		self.mError = None
		self.mErrorCode = None
		self.mErrorDescription = None
		self.mResult = None
		self.mLock = None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			Core.AuthenticationDone = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _agent(self):
		if Core.Agent is None: Core.Agent = tools.System.name() + ' ' + tools.System.version()
		return Core.Agent

	def _client(self):
		if Core.ClientId is None: Core.ClientId = tools.System.obfuscate(tools.Settings.getString('internal.key.realdebrid', raw = True))
		return Core.ClientId

	def _request(self, method, link, parameters = None, data = None, headers = None, timeout = None, authenticate = True):
		self.mResult = None

		linkOriginal = link
		parametersOriginal = parameters
		dataOriginal = data

		def redo(method, link, parameters, data, headers, timeout, authenticate):
			if authenticate:
				if self.accountAuthenticationRefresh():
					bearer = self.accountInstance().dataBearer()
					if bearer:
						headers.update(bearer)
						return self._request(method = method, link = link, parameters = parameters, data = data, headers = headers, timeout = timeout, authenticate = False)
			return None

		try:
			if not timeout:
				if data: timeout = 60
				else: timeout = 30

			self.mLinkBasic = link
			self.mParameters = parameters
			self.mSuccess = None
			self.mError = None
			self.mErrorCode = None
			self.mErrorDescription = None

			if method == Core.MethodGet or method == Core.MethodPut or method == Core.MethodDelete:
				if parameters:
					if not link.endswith('?'):
						link += '?'
					parameters = network.Networker.linkEncode(parameters)
					link += parameters
			elif method == Core.MethodPost:
				if parameters:
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

			self.mResult = tools.Converter.jsonFrom(self.mResult, default = self.mResult)
			self.mSuccess = self._success(self.mResult)
			self.mError = self._error(self.mResult)

			if not self.mSuccess:
				if self.mError == 'bad_token' and authenticate:
					return redo(method = method, link = linkOriginal, parameters = parametersOriginal, data = dataOriginal, headers = headers, timeout = timeout, authenticate = authenticate)
				else:
					self._requestErrors('The call to the RealDebrid API failed', link, data, self.mErrorCode, self.mResult)

		except (HTTPError, URLError) as error:
			self.mSuccess = False
			if hasattr(error, 'code'):
				errorCode = error.code
				errorString = ' ' + str(errorCode)
			else:
				errorCode = 0
				errorString = ''
			try:
				errorApi = tools.Converter.jsonFrom(error.read())
				self.mErrorCode = errorApi['error_code']
				self.mErrorDescription = errorApi['error']
			except: pass
			if self.mErrorDescription == 'bad_token' or errorCode == 401:
				return redo(method = method, link = linkOriginal, parameters = parametersOriginal, data = dataOriginal, headers = headers, timeout = timeout, authenticate = authenticate)
			else:
				self.mError = 'RealDebrid Unavailable [HTTP/URL Error%s]' % errorString
				self._requestErrors(self.mError, link, data, self.mErrorCode, self.mResult)
				if not self.mErrorDescription == None:
					if 'ip_not_allowed' in self.mErrorDescription:
						interface.Dialog.closeAllProgress() # The stream connection progress dialog is still showing.
						interface.Dialog.confirm(title = 33567, message = 35060)
						self.mErrorCode = Core.ErrorBlocked
		except Exception as error:
			self.mSuccess = False
			self.mError = 'Unknown Error'
			try:
				self.mErrorCode = 0
				self.mErrorDescription = str(error)
			except: pass
			self._requestErrors(self.mError, link, data, self.mErrorCode, self.mResult)

		return self.mResult

	def _requestErrors(self, message, link, payload, error = None, result = None):
		if self.mDebug:
			try: link = str(link)
			except: link = ''
			try: payload = str(payload) if len(str(payload)) < 300 else 'Payload too large to display'
			except: payload = ''
			try: error = str(error)
			except: error = ''
			try: result = str(result)
			except: result = ''
			tools.Logger.error(str(message) + (': Link [%s] Payload [%s] Error [%s] Result [%s]' % (link, payload, error, result)), exception = False)

	def _requestAuthentication(self, method, link, parameters = None, data = None, headers = None, timeout = None, token = None):
		if not parameters: parameters = {}
		if not headers: headers = {}

		bearer = self.accountInstance().dataBearer(token = token)
		if bearer: headers.update(bearer)

		return self._request(method = method, link = link, parameters = parameters, data = data, headers = headers, timeout = timeout)

	def _retrieve(self, method, category, action = None, id = None, link = None, magnet = None, files = None, hashes = None, data = None, headers = None, timeout = None, token = None):
		linkApi = network.Networker.linkJoin(Core.LinkApi, category, action)
		if not id == None: linkApi = network.Networker.linkJoin(linkApi, id)

		if not hashes == None:
			for hash in hashes:
				linkApi = network.Networker.linkJoin(linkApi, hash)

		parameters = {}
		if not link == None: parameters[Core.ParameterLink] = link
		if not magnet == None: parameters[Core.ParameterMagnet] = magnet
		if not files == None: parameters[Core.ParameterFiles] = files

		return self._requestAuthentication(method = method, link = linkApi, parameters = parameters, data = data, headers = headers, timeout = timeout, token = token)

	##############################################################################
	# SUCCESS
	##############################################################################

	def _success(self, result):
		if tools.Tools.isDictionary(result): return result and not 'error' in result
		else: return not result is None and not result == ''

	def _error(self, result):
		if tools.Tools.isDictionary(result): return result['error'] if result and 'error' in result else None
		else: return None

	def success(self):
		return self.mSuccess

	def error(self):
		return self.mError

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('internal.link.realdebrid', raw = True)
		if open: network.Networker.linkShow(link = link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountAuthenticationRefresh(self):
		try:
			# Only refresh once, in case multiple requests are submitted with an expired token.
			# Otherwise every parallel request will try to refresh the token itself.
			Core.AuthenticationLock.acquire()

			if Core.AuthenticationDone is None:
				Core.AuthenticationDone = False
				try:
					account = self.accountInstance()
					dataRefresh = account.dataRefresh()
					if dataRefresh: # Can be none if the settings DB corrupted.
						tools.Logger.log('The RealDebrid token expired. The token is being refreshed.')
						link = network.Networker.linkJoin(Core.LinkAuthentication, Core.CategoryToken)
						parameters = {
							Core.ParameterClientId : account.dataId(),
							Core.ParameterClientSecret : account.dataSecret(),
							Core.ParameterCode : dataRefresh,
							Core.ParameterGrantType : Core.ClientGrant,
						}
						result = self._request(method = Core.MethodPost, link = link, parameters = parameters, timeout = 20, authenticate = False)
						if result and not 'error' in result and 'access_token' in result and 'refresh_token' in result:
							account.update(token = result['access_token'], refresh = result['refresh_token'])
							Core.AuthenticationDone = True
					else:
						tools.Logger.log('The RealDebrid token expired, but the account data is unavailable. Please reauthenticate your RealDebrid account.')
				except:
					tools.Logger.error()
		except:
			tools.Logger.error()
		finally:
			Core.AuthenticationLock.release()
		return bool(Core.AuthenticationDone)

	def accountAuthenticationInitiate(self):
		try:
			link = network.Networker.linkJoin(Core.LinkAuthentication, Core.CategoryDevice, Core.ActionCode)
			parameters = {
				Core.ParameterClientId : self._client(),
				Core.ParameterNewCredentials : 'yes'
			}
			result = self._request(method = Core.MethodGet, link = link, parameters = parameters, timeout = 30, authenticate = False)
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

	def accountAuthenticationVerify(self, data):
		try:
			link = network.Networker.linkJoin(Core.LinkAuthentication, Core.CategoryDevice, Core.ActionCredentials)
			parameters = {
				Core.ParameterClientId : self._client(),
				Core.ParameterCode : data['device'],
			}
			result = self._request(method = Core.MethodGet, link = link, parameters = parameters, timeout = 30, authenticate = False)
			if result and 'client_secret' in result:
				id = result['client_id']
				secret = result['client_secret']

				link = network.Networker.linkJoin(Core.LinkAuthentication, Core.CategoryToken)
				parameters = {
					Core.ParameterClientId : id,
					Core.ParameterClientSecret : secret,
					Core.ParameterCode : data['device'],
					Core.ParameterGrantType : Core.ClientGrant,
				}
				result = self._request(method = Core.MethodPost, link = link, parameters = parameters, timeout = 30, authenticate = False)
				if 'access_token' in result and 'refresh_token' in result:
					token = result['access_token']
					refresh = result['refresh_token']

					account = self.account(token = token)
					label = account['user']
					if not label: label = account['email']
					if not label: label = account['id']

					return {
						Account.AttributeId : id,
						Account.AttributeSecret : secret,
						Account.AttributeToken : token,
						Account.AttributeRefresh : refresh,
						Account.AttributeLabel : label,
					}
				else:
					return False
			else:
				return None
		except:
			tools.Logger.error()
			return False

	def accountInstance(self):
		return self.mAccount

	def accountLabel(self):
		return self.mAccount.dataLabel()

	def accountSettings(self):
		return tools.Settings.launch('premium.realdebrid.enabled')

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

	def account(self, cached = True, token = None):
		try:
			if self.accountValid() or token:
				import datetime

				if token: result = self._retrieve(method = Core.MethodGet, category = Core.CategoryUser, token = token)
				elif cached: result = cache.Cache.instance().cacheShort(self._retrieve, method = Core.MethodGet, category = Core.CategoryUser)
				else: result = cache.Cache.instance().cacheClear(self._retrieve, method = Core.MethodGet, category = Core.CategoryUser)

				#if not self.success(): # Do not use this, since it will be false for cache calls.
				if result and tools.Tools.isDictionary(result) and 'id' in result and result['id']:
					expiration = result['expiration']
					index = expiration.find('.')
					if index >= 0: expiration = expiration[:index]
					expiration = expiration.strip().lower().replace('t', ' ')
					expiration = tools.Time.datetime(expiration, '%Y-%m-%d %H:%M:%S')

					return {
						'user' : result['username'],
						'id' : result['id'],
						'email' : result['email'],
						'type' : result['type'],
						'locale' : result['locale'],
						'points' : result['points'],
						'expiration' : {
							'timestamp' : tools.Time.timestamp(expiration),
							'date' : expiration.strftime('%Y-%m-%d %H:%M:%S'),
							'remaining' : (expiration - datetime.datetime.today()).days
						}
					}
				else:
					return None
			else:
				return None
		except:
			tools.Logger.error()
			return None

	##############################################################################
	# SERVICES
	##############################################################################

	# If available is False, will return all services, including those that are currently down.
	def services(self, available = True, cached = True, onlyEnabled = False):
		# Even thow ServicesUpdate is a class variable, it will be destrcucted if there are no more Premiumize instances.
		if Core.ServicesUpdate is None:
			Core.ServicesUpdate = []

			if self.accountValid():
				streamingTorrent = self.streamingTorrent()
				streamingHoster = self.streamingHoster()

				try:
					# NB: The /hosts/status always throws errors, sometimes 401 errors, sometimes unknow errors. Just use /hosts.
					# Update: This might be an old/temporary bug, /hosts/status seems to work fine now.
					# NB: Also do not use /hosts/status and then check the status, because there are often hosts which are indicated to be down, but actually succefully resolve links (eg: NitroFlare, RuTube, etc).

					'''
					if cached: result = cache.Cache.instance().cacheShort(self._retrieve, method = Core.MethodGet, category = Core.CategoryHosts, action = Core.ActionStatus)
					else: result = cache.Cache.instance().cacheClear(self._retrieve, method = Core.MethodGet, category = Core.CategoryHosts, action = Core.ActionStatus)

					for service in Core.ServicesTorrent:
						service['enabled'] = streamingTorrent
						Core.ServicesUpdate.append(service)

					if not result == None:
						for key, value in result.items():
							if not available or value['status'] == Core.ServiceStatusUp:
								Core.ServicesUpdate.append({
									'name' : value['name'],
									'id' : key.lower(),
									'identifier' : value['id'],
									'enabled' : streamingHoster,
									'domain' : key,
									'status' : value['status'],
									'supported' : value['supported'] == 1,
								})
					'''

					if cached: result = cache.Cache.instance().cacheShort(self._retrieve, method = Core.MethodGet, category = Core.CategoryHosts)
					else: result = cache.Cache.instance().cacheClear(self._retrieve, method = Core.MethodGet, category = Core.CategoryHosts)
					
					if not result is None:
						for key, value in result.items():
							if key: # Exclude "Remote".
								Core.ServicesUpdate.append({
									'name' : value['name'],
									'id' : key.lower(),
									'identifier' : value['id'],
									'enabled' : streamingHoster,
									'domain' : key,
									'status' : 'up',
									'supported' : True,
									'hoster' : True,
								})
						Core.ServicesUpdate = sorted(Core.ServicesUpdate, key = lambda i : len(i['id']))

					for service in Core.ServicesTorrent:
						service['enabled'] = streamingTorrent
						Core.ServicesUpdate.insert(0, service)

				except:
					tools.Logger.error()

		if onlyEnabled:
			return [i for i in Core.ServicesUpdate if i['enabled']]
		else:
			return Core.ServicesUpdate

	def servicesDomains(self, cached = True):
		if cached: return cache.Cache.instance().cacheShort(self._retrieve, method = Core.MethodGet, category = Core.CategoryHosts, action = Core.ActionDomains)
		else: return cache.Cache.instance().cacheClear(self._retrieve, method = Core.MethodGet, category = Core.CategoryHosts, action = Core.ActionDomains)

	def servicesList(self, onlyEnabled = False, domains = True):
		if Core.ServicesList is None:
			services = self.services(onlyEnabled = onlyEnabled)
			special = [service['id'] for service in services if not service['hoster']]
			result = [service['id'] for service in services if service['hoster']]
			if domains:
				try: result.extend(self.servicesDomains())
				except: tools.Logger.error()
			result = sorted(list(set(result)))
			Core.ServicesList = special + result
		return Core.ServicesList

	def service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		for service in self.services():
			if service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain:
				return service
		return None

	##############################################################################
	# ADD
	##############################################################################

	def _addLink(self, result):
		try: id = result['id']
		except: id = None
		try: link = result['download']
		except: link = None
		return self.addResult(id = id, link = link)

	def add(self, link, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False, type = None):
		container = network.Container(link)
		if not type: type = container.type()
		if type == network.Container.TypeTorrent:
			try:
				hash = container.hash()
				if not hash: raise Exception()
				existing = self._itemHash(hash, title = title, year = year, season = season, episode = episode)
				if not existing: raise Exception()
				return self._addLink(existing)
			except:
				return self.addTorrent(link = link, name = name)
		else:
			return self.addHoster(link)

	def addContainer(self, link, name = None):
		try:
			source = network.Container(link, download = True).information()
			if source['path'] == None and source['data'] == None:
				return Core.ErrorInaccessible

			data = source['data']
			result = self._retrieve(method = Core.MethodPut, category = Core.CategoryTorrents, action = Core.ActionAddTorrent, data = data)

			if self.success() and 'id' in result: return self._addLink(result)
			elif self.mErrorCode == Core.ErrorBlocked: return self.addResult(error = Core.ErrorBlocked, notification = True)
			else: return self.addResult(error = Core.ErrorRealDebrid)
		except:
			tools.Logger.error()
			return self.addResult(error = Core.ErrorRealDebrid)

	def addHoster(self, link):
		result = self._retrieve(method = Core.MethodPost, category = Core.CategoryUnrestrict, action = Core.ActionLink, link = link)
		if self.success() and 'download' in result: return self._addLink(result)
		elif self.mErrorCode == Core.ErrorBlocked: return self.addResult(error = Core.ErrorBlocked, notification = True)
		else: return self.addResult(error = Core.ErrorRealDebrid)

	def addTorrent(self, link, name = None):
		container = network.Container(link)
		source = container.information()
		if source['magnet']:
			magnet = container.torrentMagnet(title = name, encode = False)
			result = self._retrieve(method = Core.MethodPost, category = Core.CategoryTorrents, action = Core.ActionAddMagnet, magnet = magnet)
			if self.success() and 'id' in result: return self._addLink(result)
			elif self.mErrorCode == Core.ErrorBlocked: return self.addResult(error = Core.ErrorBlocked, notification = True)
			else: return self.addResult(error = Core.ErrorRealDebrid)
		else:
			return self.addContainer(link = link, name = name)

	##############################################################################
	# SELECT
	##############################################################################

	# Selects the files in the torrent to download.
	# files can be an id, a list of ids, or a Selection type.
	def selectList(self, id, files = None, item = None, selection = None, title = None, year = None, season = None, episode = None, manual = False, pack = False, strict = False):
		if manual:
			if item == None: item = self.item(id)
			items = {}
			items['items'] = item
			items['link'] = None
			items['selection'] = None
			return items
		else:
			result = None
			largest = None
			try:
				# NB: Be careful with SelectionAll.
				# If SelectionAll, RealDebrid will create a RAR archive from the downloaded files and only the entire archive can be downloaded. Individual files cannot be accessed anymore.
				# Rather select all files with SelectionName. Then individual files (eg episodes in season pack) can still be accessed.
				# Also note that RealDebrid might delete individual files at a later point in time, so the RealDebrid cloud provider might not work with very old files.
				if files == Core.SelectionAll:
					result = Core.SelectionAll
				elif files == Core.SelectionName:
					if item == None: item = self.item(id)
					if item and 'files' in item:
						validTitles1 = []
						validTitles2 = []
						validEpisodes1 = []
						validEpisodes2 = []

						# Movie collections.
						if largest is None and not season and not episode and pack and title:
							# Match titles with an increased "adjust" ratio.
							# Movies in collection packs have very similar names (eg: "The Lord of the Rings - The Two Towers" vs "The Lord of the Rings - The Return of the King").
							# The incorrect movie might be picked, hence start with a very strict matching ratio, and reduce it bit-by-bit until we find the first and highest/best match.
							offset = 0
							lookupFiles = []
							lookupValues1 = []
							lookupValues2 = []
							for i in range(len(item['files'])):
								file = item['files'][i]
								lookupValues1.append([file['name']])
								lookupValues2.append([file['name'], file['path']])
								lookupFiles.append(file)

							# First try the individual file names, and only if nothing was found, try with the full folder path and name.
							# Otherwise this file will match for "The Terminator 1984":
							#	The Terminator Collection (1984-2019) 2009.Terminator.Salvation.1920x800.BDRip.x264.DTS-HD.MA.mkv
							index = Stream.titlesValid(media = tools.Media.TypeMovie, data = lookupValues1, title = title, year = year, exclude = True, valid = validTitles1)
							if index is None: index = Stream.titlesValid(media = tools.Media.TypeMovie, data = lookupValues2, title = title, year = year, exclude = True, valid = validTitles1)
							if not index is None: largest = lookupFiles[index]
							validTitles1 = [lookupFiles[i] for i in validTitles1]

						# Individual movies and season-episodes.
						if largest is None:
							for file in item['files']:
								if not(season and episode) or Stream.numberShowValid(data = file['path'], season = season, episode = episode, single = True):
									validTitles1.append(file)
									if not title or not Stream.titleProhibited(data = file['path'], title = title, exception = not season is None and season == 0):
										validTitles2.append(file)
								for file in validTitles2:
									if largest is None or file['size']['bytes'] > largest['size']['bytes']:
										largest = file

						# Only episodes.
						if largest is None and episode:
							for file in item['files']:
								if Stream.numberShowValid(data = file['path'], episode = episode, single = True):
									validEpisodes1.append(file)
									if not title or not Stream.titleProhibited(data = file['path'], title = title, exception = not season is None and season == 0):
										validEpisodes2.append(file)
							if not strict:
								for file in validEpisodes2:
									if largest is None or file['size']['bytes'] > largest['size']['bytes']:
										largest = file

						if largest is None and not strict:
							for file in validTitles1:
								if largest is None or file['size']['bytes'] > largest['size']['bytes']:
									largest = file
							if largest is None:
								for file in validEpisodes1:
									if largest is None or file['size']['bytes'] > largest['size']['bytes']:
										largest = file

					if largest is None:
						return result
					else:
						# Always download all files in season packs.
						# Otherwise RealDebrid will only download a single episode, but still show the torrent as being cached.
						# Subsequent episodes from the pack might therefore have to be downloaded first even though they show up as being cached.
						# NB: Do not use "all" or simply select all files in the torrent.
						# If there is any non-media file selected, Realdebrid will compress the downloaded files into a RAR and they become inaccessible.
						# If only media files are selected, no RAR is created and each file can be accessed individually.
						if pack: result = ','.join([str(file['id']) for file in item['files'] if file['video']])
						else: result = str(largest['id'])
				elif files == Core.SelectionLargest:
					if item is None:
						item = self.item(id)
					if item and 'files' in item and not strict:
						largestId = None
						largestSize = 0
						for file in item['files']:
							size = file['size']['bytes']
							if size > largestSize:
								largestSize = size
								largestId = file['id']
								largest = file
						if largestId is None:
							return result
						else:
							result = str(largestId)
					else:
						return Core.ErrorUnavailable
				elif files == Core.SelectionFile:
					if item is None:
						item = self.item(id)

					# Always download all files in season packs.
					# Otherwise RealDebrid will only download a single episode, but still show the torrent as being cached.
					# Subsequent episodes from the pack might therefore have to be downloaded first even though they show up as being cached.
					# NB: Do not use "all" or simply select all files in the torrent.
					# If there is any non-media file selected, Realdebrid will compress the downloaded files into a RAR and they become inaccessible.
					# If only media files are selected, no RAR is created and each file can be accessed individually.
					if pack: result = ','.join([str(file['id']) for file in item['files'] if file['video']])
					elif tools.Tools.isArray(selection): result = ','.join(selection)
					else: result = str(selection)
				elif not tools.Tools.isString(files):
					if tools.Tools.isArray(files): result = ','.join(files)
					else: result = str(files)
			except: tools.Logger.error()

			items = {}
			items['items'] = item
			items['link'] = largest['link'] if largest and 'link' in largest else None
			items['selection'] = result
			return items

	# Selects the files in the torrent to download.
	# files can be an id, a list of ids, or a Selection type.
	def select(self, id, files, item = None, selection = None, title = None, year = None, season = None, episode = None, pack = False, strict = False):
		try:
			items = self.selectList(id = id, files = files, item = item, selection = selection, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
			if items is None or items['selection'] is None: return Core.ErrorUnavailable
			result = self._retrieve(method = Core.MethodPost, category = Core.CategoryTorrents, action = Core.ActionSelectFiles, id = id, files = items['selection'])
			if self.success() or self.mError == Core.ErrorDone: return True
			else: return Core.ErrorRealDebrid
		except:
			# If there are no seeders and RealDebrid cannot retrieve a list of files.
			return Core.ErrorRealDebrid

	def selectAll(self, id, pack = False, strict = False):
		return self.select(id = id, files = Core.SelectionAll, pack = pack, strict = strict)

	def selectName(self, id, item = None, title = None, year = None, season = None, episode = None, pack = False, strict = False):
		return self.select(id = id, files = Core.SelectionName, item = item, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)

	def selectFile(self, id, selection, item = None, pack = False, strict = False):
		return self.select(id = id, files = Core.SelectionFile, selection = selection, item = item, pack = pack, strict = strict)

	def selectLargest(self, id, item = None, pack = False, strict = False):
		return self.select(id = id, files = Core.SelectionLargest, item = item, pack = pack, strict = strict)

	def selectManualInitial(self, id, item = None, pack = False, strict = False):
		try:
			items = self.selectList(id = id, item = item, manual = True, pack = pack, strict = strict)
			if items == None or items['items'] == None: return Core.ErrorUnavailable
			else: return items
		except:
			# If there are no seeders and RealDebrid cannot retrieve a list of files.
			return Core.ErrorRealDebrid

	def selectManualFinal(self, id, selection):
		try:
			if not tools.Tools.isString(selection):
				if tools.Tools.isArray(selection): selection = ','.join(selection)
				else: selection = str(selection)
			self._retrieve(method = Core.MethodPost, category = Core.CategoryTorrents, action = Core.ActionSelectFiles, id = id, files = selection)
			if self.success() or self.mError == Core.ErrorDone: return True
			else: return Core.ErrorRealDebrid
		except:
			# If there are no seeders and RealDebrid cannot retrieve a list of files.
			return Core.ErrorRealDebrid

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent}

	# id: single hash or list of hashes.
	def cachedIs(self, id, timeout = None):
		result = self.cached(id = id, timeout = timeout)
		if tools.Tools.isDictionary(result): return result['cached']
		elif tools.Tools.isArray(result): return[i['cached'] for i in result]
		else: return False

	# id: single hash or list of hashes.
	def cached(self, id, timeout = None, callback = None, sources = None):
		single = tools.Tools.isString(id)
		if single: id = [id] # Must be passed in as a list.
		id = [id.lower() for id in id]

		# A URL has a maximum length, so the hashes have to be split into parts and processes independently, in order not to exceed the URL limit.
		chunks = [id[i:i + Core.LimitHashesGet] for i in range(0, len(id), Core.LimitHashesGet)]
		if sources: chunksSources = [sources[i:i + Core.LimitHashesGet] for i in range(0, len(sources), Core.LimitHashesGet)]
		else: chunksSources = None

		self.tCacheLock = Lock()
		self.tCacheResult = {}
		def cachedChunk(callback, hashes, sources, timeout):
			try:
				realdebrid = Core()
				result = realdebrid._retrieve(method = Core.MethodGet, category = Core.CategoryTorrents, action = Core.ActionInstantAvailability, hashes = hashes, timeout = timeout)
				if realdebrid.success():
					for key, value in result.items():
						key = key.lower()
						result = False
						try:
							if value:
								files = []
								value = value['rd']
								for group in value:
									# NG says that season packs can be properley detected in the new RD API.
									# For now, include torrents with multiple files.
									#if len(group.keys()) == 1: # More than 1 file means the unrestricted link will be a RAR file.
										for fileKey, fileValue in group.items():
											if tools.Video.extensionValid(path = fileValue['filename']):
												files.append(fileValue['filename'])
								if len(files) > 0:
									if sources:
										source = sources[hashes.index(key)]
										if source['stream'].filePack(boolean = True) or (source['stream'].metaMediaShow() and len(files) > 1):
											for file in files:
												if source['stream'].validName(data = file):
													result = True
										else:
											result = True
									else:
										result = True
						except:
							tools.Logger.error()

						self.tCacheLock.acquire()
						self.tCacheResult[key] = result
						self.tCacheLock.release()
						if callback:
							try: callback(self.id(), key, result)
							except: pass
			except:
				tools.Logger.error()

		threads = []
		for i in range(len(chunks)):
			try: thread = Pool.thread(target = cachedChunk, args = (callback, chunks[i], chunksSources[i], timeout))
			except: thread = Pool.thread(target = cachedChunk, args = (callback, chunks[i], None, timeout))
			threads.append(thread)
			thread.start()

		[i.join() for i in threads]
		if not callback:
			caches = []
			for key, value in self.tCacheResult.items():
				caches.append({'id' : key, 'hash' : key, 'cached' : value})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches

	##############################################################################
	# DELETE
	##############################################################################

	# Check if the file can be deleted.
	@classmethod
	def deletePossible(self, type):
		return type == Core.ModeTorrent or type == Core.Id

	def delete(self, id):
		result = self._retrieve(method = Core.MethodDelete, category = Core.CategoryTorrents, action = Core.ActionDelete, id = id)
		if self.success() or self.mErrorCode is None or self.mErrorCode == 0: # The delete request does not return any data, only HTTP 204.
			return True
		else:
			return Core.ErrorRealDebrid

	def deleteAll(self, wait = True):
		items = self.items(default = [])
		if tools.Tools.isArray(items):
			if len(items) > 0:
				def _deleteAll(id):
					Core().delete(id)
				threads = []
				for item in items:
					threads.append(Pool.thread(target = _deleteAll, args = (item['id'],)))

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
			return Core.ErrorRealDebrid

	def _deleteSingle(self, hashOrLink):
		id = None
		items = self.items(default = [])
		if network.Networker.linkIs(hashOrLink):
			for item in items:
				if item['link'] == hashOrLink:
					id = item['id']
		else:
			hashOrLink = hashOrLink.lower()
			for item in items:
				if item['hash'].lower() == hashOrLink:
					id = item['id']
			if id is None: # If RealDebrid ID was passed instead of hash.
				id = hashOrLink

		if id is None: return False
		self.delete(id)
		return True

	# Delete an item and its corresponding transfer based on the link or hash.
	def deleteSingle(self, hashOrLink, wait = True):
		thread = Pool.thread(target = self._deleteSingle, args = (hashOrLink,))
		thread.start()
		if wait: thread.join()
		return True

	# Delete on launch
	def deleteLaunch(self):
		try:
			if tools.Settings.getBoolean('premium.realdebrid.removal'):
				option = tools.Settings.getInteger('premium.realdebrid.removal.launch')
				if option == 1: self.deleteAll(wait = False)
		except: tools.Logger.error()

	# Delete on playback ended
	def deletePlayback(self, id, pack = None, category = None):
		try:
			if tools.Settings.getBoolean('premium.realdebrid.removal'):
				option = tools.Settings.getInteger('premium.realdebrid.removal.playback')
				if option == 1: self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack): self.deleteSingle(id, wait = False)
		except: tools.Logger.error()

	# Delete on failure
	# id = hash or link
	def deleteFailure(self, id, pack = None):
		try:
			if tools.Settings.getBoolean('premium.realdebrid.removal'):
				option = tools.Settings.getInteger('premium.realdebrid.removal.failure')
				if option == 1: self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack): self.deleteSingle(id, wait = False)
		except: tools.Logger.error()

	##############################################################################
	# TIME
	##############################################################################

	def _timeOffset(self):
		try:
			timeServer = self._retrieve(method = Core.MethodGet, category = Core.CategoryTime)
			timeServer = convert.ConverterTime(timeServer, format = convert.ConverterTime.FormatDateTime).timestamp()
			timeUtc = tools.Time.timestamp()
			timeOffset =  timeServer - timeUtc
			return int(3600 * round(timeOffset / float(3600))) # Round to the nearest hour
		except:
			return 0

	def timeOffset(self):
		# Only initialize TimeOffset if it was not already intialized before.
		# There is an issue with RealDebrid servers being flooded with /time API requests.
		# Not sure why this happens, but might be because the cache is not working (eg: write permission on Android).
		# Always check if TimeOffset is already in memory from a previous request, so that issues with caching the value to disk do not cause continues API calls.
		if Core.TimeOffset is None:
			Core.TimeOffset = cache.Cache.instance().cacheMedium(self._timeOffset)
		return Core.TimeOffset

	##############################################################################
	# ITEMS
	##############################################################################

	def _itemHash(self, hash, title = None, year = None, season = None, episode = None):
		try:
			hash = hash.lower()
			items = self.items()

			# Movies and season-episodes.
			validTitles = []
			for item in items:
				if item['hash'].lower() == hash:
					# Also check for the season/episode for season packs.
					# Otherwise RealDebrid will always return the first ever episode downloaded in the pack, since the hash for the torrent is the same.
					# Force to download again, if the episode does not match, that is a different episode is selected from the season pack.
					if not(season and episode) or Stream.numberShowValid(data = item['name'], season = season, episode = episode, single = True):
						validTitles.append(item)
						if not title or not Stream.titleProhibited(data = item['name'], title = title, exception = not season is None and season == 0):
							return item

			# Only episodes.
			validEpisodes = []
			if episode:
				for item in items:
					if item['hash'].lower() == hash:
						# Also check for the season/episode for season packs.
						# Otherwise RealDebrid will always return the first ever episode downloaded in the pack, since the hash for the torrent is the same.
						# Force to download again, if the episode does not match, that is a different episode is selected from the season pack.
						if Stream.numberShowValid(data = item['name'], episode = episode, single = True):
							validEpisodes.append(item)
							if not title or not Stream.titleProhibited(data = item['name'], title = title, exception = not season is None and season == 0):
								return item

			if title:
				if len(validTitles) > 0:
					return validTitles[0]
				elif len(validEpisodes) > 0: return validEpisodes[0]
		except:
			pass
		return None

	def _item(self, dictionary, title = None, year = None, season = None, episode = None, pack = False, strict = False, selection = None):
		result = {}
		try:
			status = dictionary['status']
			sizeBytes = dictionary['bytes']
			if sizeBytes == 0: # Seems to be a bug in RealDebrid that sometimes the size shows up as 0. Use the largest file instead.
				if 'files' in dictionary:
					for file in dictionary['files']:
						size = file['bytes']
						if size > sizeBytes: sizeBytes = size
				if sizeBytes == 0 and 'original_bytes' in dictionary:
					sizeBytes = dictionary['original_bytes']
			size = convert.ConverterSize(value = sizeBytes, unit = convert.ConverterSpeed.Byte)

			split = convert.ConverterSize(value = dictionary['split'], unit = convert.ConverterSpeed.ByteGiga)
			speed = convert.ConverterSpeed(value = dictionary['speed'] if 'speed' in dictionary else 0, unit = convert.ConverterSpeed.Byte)

			offset = self.timeOffset()
			started = convert.ConverterTime(value = dictionary['added'], format = convert.ConverterTime.FormatDateTimeJson, offset = offset)
			if 'ended' in dictionary:
				finished = convert.ConverterTime(value = dictionary['ended'], format = convert.ConverterTime.FormatDateTimeJson, offset = offset)
				# RealDebrid seems to do caching in the background. In such a case, the finished time might be before the started time, since it was previously downloaded by another user.
				if finished.timestamp() < started.timestamp(): finished = started
			else:
				finished = None

			seeders = dictionary['seeders'] if 'seeders' in dictionary else 0

			completedProgress = dictionary['progress'] / 100.0
			completedBytes = int(sizeBytes * completedProgress)
			completedSize = convert.ConverterSize(value = completedBytes, unit = convert.ConverterSpeed.Byte)
			if finished is None: difference = tools.Time.timestamp() - started.timestamp()
			else: difference = finished.timestamp() - started.timestamp()
			completedDuration = convert.ConverterDuration(value = difference, unit = convert.ConverterDuration.UnitSecond)
			completedSeconds = completedDuration.value(convert.ConverterDuration.UnitSecond)

			remainingProgress = 1 - completedProgress
			remainingBytes = sizeBytes - completedBytes
			remainingSize = convert.ConverterSize(value = remainingBytes, unit = convert.ConverterSpeed.Byte)
			remainingSeconds = int(remainingBytes * (completedSeconds / float(completedBytes))) if completedBytes > 0 else 0
			remainingDuration = convert.ConverterDuration(value = remainingSeconds, unit = convert.ConverterDuration.UnitSecond)

			result = {
				'id' : dictionary['id'],
				'hash' : dictionary['hash'],
				'name' : dictionary['filename'],
				'type' : Core.TypeTorrent,
				'status' : status,
				'host' : dictionary['host'],
				'time' : {
					'started' : started.timestamp(),
					'finished' : finished.timestamp() if finished else None
				},
				'size' : {
					'bytes' : size.value(),
					'description' : size.stringOptimal()
				},
				'split' : {
					'bytes' : split.value(),
					'description' : split.stringOptimal()
				},
				'transfer' : {
					'speed' : {
						'bytes' : speed.value(convert.ConverterSpeed.Byte),
						'bits' : speed.value(convert.ConverterSpeed.Bit),
						'description' : speed.stringOptimal()
					},
					'torrent' : {
						'seeding' : status == Core.StatusUploading,
						'seeders' : seeders,
					},
					'progress' : {
						'completed' : {
							'value' : completedProgress,
							'percentage' : int(completedProgress * 100),
							'size' : {
								'bytes' : completedSize.value(),
								'description' : completedSize.stringOptimal()
							},
							'time' : {
								'seconds' : completedDuration.value(convert.ConverterDuration.UnitSecond),
								'description' : completedDuration.string(convert.ConverterDuration.FormatDefault)
							}
						},
						'remaining' : {
							'value' : remainingProgress,
							'percentage' : int(remainingProgress * 100),
							'size' : {
								'bytes' : remainingSize.value(),
								'description' : remainingSize.stringOptimal()
							},
							'time' : {
								'seconds' : remainingDuration.value(convert.ConverterDuration.UnitSecond),
								'description' : remainingDuration.string(convert.ConverterDuration.FormatDefault)
							}
						}
					}
				}
			}

			# Link
			index = None
			if 'links' in dictionary and len(dictionary['links']) > 0:
				# NB: The file list returned from RealDebrid contains all files, those that were selected and those that were not.
				# However, the returned links list only contains links to the selected files.
				# Keep an offset to pick the correct link by index from the list.
				largest = None
				offset = 0

				try:
					validTitles = []
					validEpisodes = []
					files = dictionary['files']

					# Select specific file IDs.
					if largest is None and not selection is None:
						if tools.Tools.isString(selection): selection = selection.split(',')
						if not tools.Tools.isArray(selection): selection = [selection]
						selection = [int(i) for i in selection]

						offset = 0
						lookupFiles = []
						lookupValues = []
						for i in range(len(files)):
							file = files[i]
							if file['selected']:
								if file['id'] in selection:
									lookupValues.append(file['id'])
									lookupFiles.append({'file' : file, 'index' : i, 'offset' : offset})
							else:
								offset += 1

						index = None
						for file in lookupFiles:
							if file['file']['id'] in selection:
								largest = file
								break

					# Movie collections.
					if largest is None and not season and not episode and pack:
						# Match titles with an increased "adjust" ratio.
						# Movies in collection packs have very similar names (eg: "The Lord of the Rings - The Two Towers" vs "The Lord of the Rings - The Return of the King").
						# The incorrect movie might be picked, hence start with a very strict matching ratio, and reduce it bit-by-bit until we find the first and highest/best match.
						offset = 0
						lookupFiles = []
						lookupValues1 = []
						lookupValues2 = []
						for i in range(len(files)):
							file = files[i]
							if file['selected']:
								lookup = []
								try:
									fileName = file['path'].split('/')[-1]
									lookupValues1.append(fileName)
									lookup.append(fileName)
								except: pass
								lookup.append(file['path'])
								lookupValues2.append(lookup)
								lookupFiles.append({'file' : file, 'index' : i, 'offset' : offset})
							else:
								offset += 1

						# First try the individual file names, and only if nothing was found, try with the full folder path and name.
						# Otherwise this file will match for "The Terminator 1984":
						#	The Terminator Collection (1984-2019) 2009.Terminator.Salvation.1920x800.BDRip.x264.DTS-HD.MA.mkv
						index = Stream.titlesValid(media = tools.Media.TypeMovie, data = lookupValues1, title = title, year = year, exclude = True, valid = validTitles)
						if index is None: index = Stream.titlesValid(media = tools.Media.TypeMovie, data = lookupValues2, title = title, year = year, exclude = True, valid = validTitles)
						if not index is None: largest = lookupFiles[index]
						validTitles = [lookupFiles[i] for i in validTitles]

					# Individual movies and season-episodes.
					if largest is None:
						offset = 0
						for i in range(len(files)):
							file = files[i]
							if file['selected']:
								if not(season and episode) or Stream.numberShowValid(data = file['path'], season = season, episode = episode, single = True):
									validTitles.append({'file' : file, 'index' : index, 'offset' : offset})
									if not title or not Stream.titleProhibited(data = file['path'], title = title, exception = not season is None and season == 0):
										if largest is None or file['bytes'] > largest['file']['bytes']:
											largest = {'file' : file, 'index' : i, 'offset' : offset}
							else:
								offset += 1

					# Only episodes.
					if largest is None and episode:
						offset = 0
						for i in range(len(files)):
							file = files[i]
							if file['selected']:
								if Stream.numberShowValid(data = file['path'], episode = episode, single = True):
									validEpisodes.append({'file' : file, 'index' : index, 'offset' : offset})
									if not title or not Stream.titleProhibited(data = file['path'], title = title, exception = not season is None and season == 0):
										if largest is None or file['bytes'] > largest['file']['bytes']:
											largest = {'file' : file, 'index' : i, 'offset' : offset}
							else:
								offset += 1

					if not strict:
						if largest is None:
							if len(validTitles) > 0: largest = validTitles[0]
							elif len(validEpisodes) > 0: largest = validEpisodes[0]

						if largest is None:
							offset = 0
							for i in range(len(files)):
								file = files[i]
								if file['selected']:
									if largest is None or file['bytes'] > largest['file']['bytes']:
										largest = {'file' : file, 'index' : i, 'offset' : offset}
								else:
									offset += 1

				except: pass # If there is not 'files' attribute in the results.

				index = 0
				offset = 0
				if not largest is None:
					index = largest['index']
					offset = largest['offset']

				try:
					result['link'] = dictionary['links'][index - offset]
				except:
					index = 0
					result['link'] = dictionary['links'][index] # Sometimes RD only has 1 link for all the files.
			else:
				result['link'] = None

			# Files
			if 'files' in dictionary and len(dictionary['files']) > 0:
				offset = 0
				files = []
				for i in range(len(dictionary['files'])):
					file = dictionary['files'][i]
					size = convert.ConverterSize(value = file['bytes'], unit = convert.ConverterSpeed.Byte)

					name = dictionary['filename']
					parts = []

					path = file['path']
					if not path.startswith('/'): path = '/' + path
					path = name + path

					start = path.rfind('/')
					if start >= 0:
						name = path[start + 1:]
						parts = path[:start].split('/')
						parts = [p for p in parts if p]

					if not file['selected']: offset += 1

					item = {
						'id' : file['id'],
						'path' : path,
						'parts' : parts,
						'name' : name,
						'link' : None,
						'selected' : tools.Converter.boolean(file['selected']),
						'video' : tools.Video.extensionValid(path = path),
						'size' : {
							'bytes' : size.value(),
							'description' : size.stringOptimal()
						}
					}
					try: item['link'] = dictionary['links'][i - offset] if file['selected'] else None
					except:
						try: item['link'] = dictionary['links'][0] if file['selected'] else None # RAR files have only a single link.
						except: pass
					files.append(item)

					if index == i: result['video'] = item
				result['files'] = files
			else:
				result['files'] = None
		except:
			tools.Logger.error()

		return result

	def items(self, title = None, year = None, season = None, episode = None, pack = False, strict = False, full = False, default = ErrorRealDebrid):
		data = self._retrieve(method = Core.MethodGet, category = Core.CategoryTorrents)
		if self.success():
			items = []
			if full:
				lock = Lock()
				threads = [Pool.thread(target = Core().item, kwargs = {'id' : i['id'], 'title' : None, 'year' : None, 'pack' : False, 'selection' : items, 'lock' : lock}) for i in data]
				[thread.start() for thread in threads]
				[thread.join() for thread in threads]
			else:
				items = [self._item(i, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict) for i in data]
			return items
		else:
			return default

	def item(self, id, title = None, year = None, season = None, episode = None, pack = False, strict = False, selection = None, result = None, lock = None, default = ErrorRealDebrid):
		data = self._retrieve(method = Core.MethodGet, category = Core.CategoryTorrents, action = Core.ActionInfo, id = id)
		if self.success():
			item = self._item(data, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, selection = selection)
			if not result is None:
				try: lock.acquire()
				except: pass
				result.append(item)
				try: lock.release()
				except: pass
			return item
		else:
			return default

	##############################################################################
	# DOWNLOAD
	##############################################################################

	# Number of torrent download slots available.
	def downloadSlots(self):
		results = self._retrieve(method = Core.MethodGet, category = Core.CategoryTorrents, action = Core.ActionActive)
		if self.success():
			try: return results['limit'] - results['nb']
			except: return 0
		else:
			return Core.ErrorRealDebrid

	def downloadHosts(self):
		results = self._retrieve(method = Core.MethodGet, category = Core.CategoryTorrents, action = Core.ActionAvailableHosts)
		if self.success():
			items = []
			for result in results:
				size = convert.ConverterSize(value = result['max_file_size'], unit = convert.ConverterSpeed.ByteGiga)
				items.append({
					'domain' : result['host'],
					'size' : {
						'bytes' : size.value(),
						'description' : size.stringOptimal()
					}
				})
			return items
		else:
			return Core.ErrorRealDebrid

	def downloadInformation(self):
		items = self.items()
		if tools.Tools.isArray(items):
			count = len(items)
			countBusy = 0
			countFinished = 0
			countFailed = 0
			size = 0
			for item in items:
				size += item['size']['bytes']
				status = item['status']
				if status in [Core.StatusUnknown, Core.StatusError, Core.StatusMagnetConversion, Core.StatusVirus, Core.StatusDead]:
					countFailed += 1
				elif status in [Core.StatusFinished, Core.StatusUploading]:
					countFinished += 1
				else:
					countBusy += 1
			size = convert.ConverterSize(value = size, unit = convert.ConverterSize.Byte)

			result = {
				'count' : {
					'total' : count,
					'busy' : countBusy,
					'finished' : countFinished,
					'failed' : countFailed,
				},
				'size' : {
					'bytes' : size.value(),
					'description' : size.stringOptimal()
				}
			}

			hosts = self.downloadHosts()
			if tools.Tools.isArray(hosts) and len(hosts) > 0:
				result['host'] = hosts[0]

			return result
		else:
			return Core.ErrorRealDebrid
