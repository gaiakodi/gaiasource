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
import os
import sys
import math
import copy

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
from lib.modules.account import Premiumize as Account

class Core(base.Core):

	Id = 'premiumize'
	Name = 'Premiumize'
	Abbreviation = 'P'
	Acronym = 'PM'
	Priority = 1

	FolderFeeds = 'Feed Downloads'

	# Services
	ServiceTorrent = base.Core.ModeTorrent
	ServiceUsenet = base.Core.ModeUsenet
	ServiceVpn = 'vpn'
	ServiceCloud = 'cloud'

	ServicesUpdate = None
	ServicesList = None
	Services = [
		{	'name' : 'Torrent',	'domain' : ServiceTorrent,	'hoster' : False,	'limit' : 0,	'factor' : 1	},
		{	'name' : 'Usenet',	'domain' : ServiceUsenet,	'hoster' : False,	'limit' : 0,	'factor' : 1	},
		{	'name' : 'VPN',		'domain' : ServiceVpn	,	'hoster' : False,	'limit' : 0,	'factor' : 1	},
		{	'name' : 'Cloud',	'domain' : ServiceCloud,	'hoster' : False,	'limit' : 0,	'factor' : 1	},
	]

	# Usage - Maximum usage bytes and points
	UsageBytes = 1073741824000 # 1000 GB
	UsagePoints = 1000 # 1000 Points

	Agent = None
	Client = None

	# Method
	MethodGet = network.Networker.MethodGet
	MethodPost = network.Networker.MethodPost

	# Limits
	LimitLink = 2000 # Maximum length of a URL.
	LimitHashes = 100 # Even when the hashes are send via POST, Premiumize seems to ignore the last ones (+- 1000 hashes). When too many hashes are sent at once (eg 500-900), if often causes a request timeout. Keep the limit small enough. Rather start multiple requests which should create multipel threads on the server.

	#Links
	LinkMain = 'https://www.premiumize.me' # Requires www subdomain for OAuth.
	LinkApi = 'https://www.premiumize.me/api/' # API always redirects to www subdomain, so add it here to make requests faster (not having to redirect).

	# Categories
	CategoryAccount = 'account'
	CategoryFolder = 'folder'
	CategoryItem = 'item'
	CategoryTransfer = 'transfer'
	CategoryTorrent = 'torrent'
	CategoryCache = 'cache'
	CategoryServices = 'services'
	CategoryZip = 'zip'
	CategoryToken = 'token'
	CategoryDevice = 'device'

	# Actions
	ActionDownload = 'directdl'
	ActionInfo = 'info'
	ActionCreate = 'create'
	ActionList = 'list'
	ActionListAll = 'listall'
	ActionDetails = 'details'
	ActionRename = 'rename'
	ActionPaste = 'paste'
	ActionDelete = 'delete'
	ActionBrowse = 'browse'
	ActionCheck = 'check'
	ActionCheckHashes = 'checkhashes'
	ActionClear = 'clearfinished'
	ActionGenerate = 'generate'
	ActionCode = 'code'

	# Parameters
	ParameterLogin = 'params[login]'
	ParameterPassword = 'params[pass]'
	ParameterLink = 'params[link]'
	ParameterMethod = 'method'
	ParameterCustomer = 'customer_id'
	ParameterPin = 'pin'
	ParameterId = 'id'
	ParameterParent = 'parent_id'
	ParameterName = 'name'
	ParameterItems = 'items'
	ParameterType = 'type'
	ParameterHash = 'hash'
	ParameterHashes = 'hashes[]'
	ParameterCaches = 'items[]'
	ParameterSource = 'src'
	ParameterItemId = 'items[0][id]'
	ParameterItemType = 'items[0][type]'
	ParameterFolder = 'folder_id'
	ParameterClientId = 'client_id'
	ParameterClientSecret = 'client_secret'
	ParameterCode = 'code'
	ParameterGrantType = 'grant_type'
	ParameterResponseType = 'response_type'

	# Statuses
	StatusUnknown = 'unknown'
	StatusError = 'error'
	StatusTimeout = 'timeout'
	StatusQueued = 'queued'
	StatusBusy = 'busy'
	StatusFinalize = 'finalize'
	StatusFinished = 'finished'

	# Errors
	ErrorUnknown = 'unknown'
	ErrorAuthentication = 'authentication'
	ErrorInaccessible = 'inaccessible' # Eg: 404 error.
	ErrorTemporary = 'temporary' # Temporary errors
	ErrorPremium = 'premium' # Require premium account.
	ErrorPremiumize = 'premiumize' # Error from Premiumize server.
	ErrorUnsupported = 'unsupported' # Not official Premiumize error. Indicates that a certain feature is not supported.
	ErrorDuplicate = 'duplicate' # Already added to Premiumize.
	ErrorTransfer = 'transfer' # The transfer job went missing.
	ErrorExists = 'exists' # The transfer already exists.
	ErrorFolder = 'folder' # Folder does not exist.
	ErrorIncomplete = 'incomplete' # NZB is incomplete ("too many missing articles").
	ErrorRetention = 'retention' # Usenet out of server retention.
	ErrorPassword = 'password' # The file is password protected.
	ErrorRepair = 'repair' # The file is unrepairable.

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		base.Core.__init__(self, Core.Id, Core.Name, Core.LinkMain)

		self.mAccount = Account.instance()

		self.mLinkBasic = None
		self.mLinkFull = None
		self.mParameters = None
		self.mSuccess = None
		self.mError = None
		self.mErrorCode = None
		self.mErrorDescription = None
		self.mResult = None

	##############################################################################
	# INTERNAL
	##############################################################################

	def _agent(self):
		if Core.Agent is None: Core.Agent = tools.System.name() + ' ' + tools.System.version()
		return Core.Agent

	def _client(self):
		if Core.Client is None: Core.Client = tools.System.obfuscate(tools.Settings.getString('internal.key.premiumize', raw = True))
		return Core.Client

	def _parameter(self, parameter, parameters):
		if parameter in parameters:
			return parameters[parameter]
		else:
			return None

	def _request(self, link, method = None, parameters = None, data = None, headers = None, timeout = None, authenticate = True, redo = False):
		self.mResult = None

		linkOriginal = link
		parametersOriginal = parameters
		dataOriginal = data

		def reauthenticate(link, method, parameters, data, headers, timeout, authenticate):
			# Premiumize's OAuth does not have a refresh token.
			# The access token is valid for 10 years.
			# In case this 10-year-limit is ever reached, simply inform the user to reauthenticate.
			interface.Dialog.notification(title = 35107, message = 35461, icon = interface.Dialog.IconError, time = 10000)
			return None

		try:
			self.mLinkBasic = link
			self.mParameters = parameters
			self.mSuccess = None
			self.mError = None
			self.mErrorCode = None
			self.mErrorDescription = None

			# Use GET parameters for uploading files/containers (src parameter).
			if method == Core.MethodGet or data:
				if parameters:
					if not link.endswith('?'):
						link += '?'
					parameters = network.Networker.linkEncode(parameters)
					parameters = network.Networker.linkUnquote(parameters) # Premiumize uses [] in the API links. Do not encode those and other URL characters.
					link += parameters
			else: # Use POST for all other requests.
				# List of values, eg: hashes[]
				# http://stackoverflow.com/questions/18201752/sending-multiple-values-for-one-name-urllib2
				if Core.ParameterHashes in parameters:
					# If hashes are very long and if the customer ID and pin is appended to the end of the parameter string, Premiumize will ignore them and say there is no ID/pin.
					# Manually move the hashes to the back.
					hashes = {}
					hashes[Core.ParameterHashes] = parameters[Core.ParameterHashes]
					del parameters[Core.ParameterHashes]
					data = network.Networker.linkEncode(hashes)
					if len(parameters.keys()) > 0: data = network.Networker.linkEncode(parameters) + '&' + data
				elif Core.ParameterCaches in parameters:
					# If hashes are very long and if the customer ID and pin is appended to the end of the parameter string, Premiumize will ignore them and say there is no ID/pin.
					# Manually move the hashes to the back.
					links = {}
					links[Core.ParameterCaches] = parameters[Core.ParameterCaches]
					del parameters[Core.ParameterCaches]
					for key, value in links.items():
						if tools.Tools.isArray(value):
							for i in range(len(value)):
								try: value[i] = value[i].encode('utf-8')
								except: pass
						else:
							try: links[key] = value.encode('utf-8')
							except: pass
					data = network.Networker.linkEncode(links)
					if len(parameters.keys()) > 0: data = network.Networker.linkEncode(parameters) + '&' + data
				else:
					data = network.Networker.linkEncode(parameters)

			# If the link is too long, reduce the size. The maximum URL size is 2000.
			# This occures if GET parameters are used instead of POST for checking a list of hashes.
			# This should not happen anymore, since the encryption and method settings were removed since Gaia 6.
			if 'hashes[]=' in link:
				while len(link) > Core.LimitLink:
					start = link.find('hashes[]=')
					end = link.find('&', start)
					link = link[:start] + link[end + 1:]
			elif 'items[]=' in link:
				while len(link) > Core.LimitLink:
					start = link.find('items[]=')
					end = link.find('&', start)
					link = link[:start] + link[end + 1:]

			self.mLinkFull = link

			if data:
				try: data = data.encode('utf-8')
				except: pass
				request = Request(link, data = data)
			else: request = Request(link)

			request.add_header('User-Agent', self._agent())
			if headers:
				for key in headers:
					request.add_header(key, headers[key])

			if not timeout:
				if data: timeout = 60
				else: timeout = 30

			# gaiaremove - In the future rewrite this using Networker.
			if Vpn.killRequest():
				response = urlopen(request, timeout = timeout)
				result = response.read()
				response.close()
			else:
				result = None

			self.mResult = tools.Converter.jsonFrom(result)
			self.mSuccess = self._success(self.mResult)
			self.mError = self._error(self.mResult)

			# If the user downloads to a custom folder, but manually deleted the folder from the cloud.
			if not redo and Core.CategoryTransfer in linkOriginal and Core.ActionCreate in linkOriginal and self.errorType() == Core.ErrorFolder:
				parametersOriginal = self.folderReinitialize(parametersOriginal)
				return self._request(link = linkOriginal, method = method, parameters = parametersOriginal, data = dataOriginal, headers = headers, timeout = timeout, authenticate = authenticate, redo = True)

			if not self.mSuccess:
				if self.mResult and 'error' in self.mResult and self.mResult['error'] == Core.ErrorDuplicate:
					self.mSuccess = True
				elif self.mError == 'bad_token' and authenticate:
					return reauthenticate(link = linkOriginal, method = method, parameters = parametersOriginal, data = dataOriginal, headers = headers, timeout = timeout, authenticate = authenticate)
				else:
					self._requestErrors('The call to the Premiumize API failed', link, data, self.mResult, exception = False)

		except (HTTPError, URLError) as error:
			self.mSuccess = False
			if hasattr(error, 'code'):
				errorCode = error.code
				errorString = ' ' + str(errorCode)
			else:
				errorCode = 0
				errorString = ''
			self.mError = 'Premiumize Unreachable [HTTP/URL Error%s]' % errorString
			if authenticate: self._requestErrors(self.mError, link, data, self.mResult)
			try:
				errorApi = tools.Converter.jsonFrom(error.read())
				self.mErrorCode = errorApi['error_code']
				self.mErrorDescription = errorApi['error']
			except: pass
			if self.mErrorDescription == 'bad_token' or errorCode == 401:
				return reauthenticate(link = linkOriginal, method = method, parameters = parametersOriginal, data = dataOriginal, headers = headers, timeout = timeout, authenticate = authenticate)
		except:
			self.mSuccess = False
			self.mError = 'Unknown Error'
			self._requestErrors(self.mError, link, data, self.mResult)
		return self.mResult

	def _requestErrors(self, message, link, payload, result = None, exception = True):
		# While downloading, do not add to log.
		if not result is None and 'message' in result and result['message'] == 'Download is not finished yet.':
			return

		link = str(link)
		payload = str(payload) if len(str(payload)) < 300 else 'Payload too large to display'
		result = str(result)
		tools.Logger.error(str(message) + (': Link [%s] Payload [%s] Result [%s]' % (link, payload, result)), exception = exception)

	def _requestAuthentication(self, link, parameters = None, data = None, headers = None, timeout = None, token = None):
		if not parameters: parameters = {}
		if not headers: headers = {}

		bearer = self.accountInstance().dataBearer(token = token)
		if bearer: headers.update(bearer)

		return self._request(link = link, parameters = parameters, data = data, headers = headers, timeout = timeout)

	# Retrieve from the API
	# Parameters:
	#	category: CategoryFolder, CategoryTransfer, CategoryTorrent
	#	action: ActionCreate, ActionList, ActionRename, ActionPaste, ActionDelete, ActionBrowse, ActionCheckHashes, ActionClear
	#	remainder: individual parameters for the actions. hash can be single or list.
	def _retrieve(self, category, action, id = None, parent = None, name = None, items = None, caches = None, type = None, source = None, hash = None, itemId = None, itemType = None, folder = None, timeout = None, data = None, headers = None, token = None):
		link = network.Networker.linkJoin(Core.LinkApi, category, action)

		parameters = {}
		if not id is None: parameters[Core.ParameterId] = id
		if not parent is None: parameters[Core.ParameterParent] = parent
		if not name is None: parameters[Core.ParameterName] = name
		if not items is None: parameters[Core.ParameterItems] = items
		if not type is None: parameters[Core.ParameterType] = type
		if not source is None: parameters[Core.ParameterSource] = source
		if not itemId is None: parameters[Core.ParameterItemId] = itemId
		if not itemType is None: parameters[Core.ParameterItemType] = itemType
		if not folder is None: parameters[Core.ParameterFolder] = folder
		if not caches is None: parameters[Core.ParameterCaches] = caches
		if not hash is None:
			# NB: Always make the hashes lower case. Sometimes Premiumize cannot find the hash if it is upper case.
			if tools.Tools.isString(hash):
				parameters[Core.ParameterHash] = hash.lower()
			else:
				for i in range(len(hash)):
					hash[i] = hash[i].lower()
				parameters[Core.ParameterHashes] = hash

		return self._requestAuthentication(link = link, parameters = parameters, data = data, headers = headers, timeout = timeout, token = token)

	def _success(self, result):
		try: return ('status' in result and result['status'].lower() == 'success') or (not 'status' in result and not 'error' in result) or (tools.Tools.isArray(result) and len(result) > 0)
		except: return False

	def _error(self, result):
		return result['message'] if result and 'message' in result else None

	def errorType(self, error = None):
		try:
			if error is None: error = self.mError
			error = error.lower()
			if 'try again' in error: return Core.ErrorTemporary
			elif 'premium membership' in error: return Core.ErrorPremium
			elif 'not logged in' in error: return Core.ErrorAuthentication
			elif 'folder does not exist' in error: return Core.ErrorFolder
			elif 'missing articles' in error: return Core.ErrorIncomplete
			elif 'retention' in error: return Core.ErrorRetention
			elif 'repair' in error: return Core.ErrorRepair
			elif 'password' in error: return Core.ErrorPassword
			elif 'missing' in error: return Core.ErrorTransfer
			elif 'already added' in error: return Core.ErrorExists
			elif 'unknown' in error: return Core.ErrorUnknown
			else: return Core.ErrorPremiumize
		except:
			return Core.ErrorPremiumize

	def errorDetails(self, error = None, message = None, data = None):
		if message and not error: error = self.errorType(error = message)
		if error == Core.ErrorInaccessible:
			title = 'Stream Error'
			message = 'Stream Is Inaccessible'
		elif error == Core.ErrorPremiumize:
			title = 'Stream Error'
			message = 'Premiumize Stream Unavailable'
		elif error == Core.ErrorAuthentication:
			title = 'Stream Error'
			message = 'Premiumize Authentication Failure'
		elif error == Core.ErrorPremium:
			title = 'Stream Error'
			message = 'Premiumize Membership Required'
		elif error == Core.ErrorTemporary:
			title = 'Stream Error'
			message = 'Temporary Premiumize Error'
		elif error == Core.ErrorUnsupported:
			title = 'Support Error'
			message = 'Requested Feature Unsupported'
		elif error == Core.ErrorIncomplete:
			title = 'Incomplete Error'
			message = 'Missing NZB Parts'
		elif error == Core.ErrorRetention:
			title = 'Retention Error'
			message = 'NZB Retention Expired'
		elif error == Core.ErrorPassword:
			title = 'Password Error'
			message = 'Password Protected File'
		elif error == Core.ErrorRepair:
			title = 'Repair Error'
			message = 'Unrepairable File'
		elif error == Core.ErrorFolder:
			title = 'Folder Error'
			message = 'Folder Not Found'
		elif error == Core.ErrorTransfer:
			title = 'Transfer Error'
			message = 'Missing Transfer Job'
		elif error == Core.ErrorExists:
			title = 'Transfer Exists'
			message = 'Transfer Already Added'
		elif error == Core.ErrorSelection:
			title = 'Selection Error'
			message = 'No File Selected'
		elif error == Core.ErrorPack:
			title = 'Pack Error'
			message = 'File Not In Pack Or Mislabeled'
		elif error == Core.ErrorFormat:
			title = 'Unsupported File'
			message = 'File Format Not Supported'
		else:
			# Premiumize sometimes returns the error attribute, even when everything went fine:
			#	{"id":"xxxxx","name":"xxxxxx","message":"","status":"error","progress":0,"folder_id":"xxxxx","file_id":null,"src":"https://www.premiumize.me/api/job/src?id=xxxxx"}
			if not(data and 'src' in data and 'id' in data):
				tools.Logger.errorCustom('Unexpected Premiumize Error: %s - %s' % (str(error), tools.Converter.jsonTo(data)))
			title = 'Stream Error'
			message = 'Stream File Unavailable'
		return {'title' : title, 'message' : message}

	##############################################################################
	# INITIALIZE
	##############################################################################

	# Initialize Premiumize account (if set in settings).
	# If not called, Premiumize links will fail in the sources.

	def initialize(self):
		thread = Pool.thread(target = self._initialize)
		thread.start()

	def _initialize(self):
		def notify():
			apiKey = 'V1c5MUlHRnlaU0IxYzJsdVp5QmhiaUIxYm1GMWRHaHZjbWw2WldRZ2RtVnljMmx2YmlCdlppQjBhR1VnYjNKcFoybHVZV3dnWVdSa2IyNGdSMkZwWVM0Z1ZHaHBjeUIyWlhKemFXOXVJRzltSUhSb1pTQmhaR1J2YmlCM2FXeHNJRzV2ZENCM2IzSnJJR0Z6SUdsdWRHVnVaR1ZrTGlCSlppQjViM1VnY0dGcFpDQm1iM0lnZEdocGN5QmhaR1J2YmlCdmNpQjBhR1VnYldWa2FXRWdZbTk0SUdsMElHTmhiV1VnYjI0c0lIbHZkU0JuYjNRZ1cwSmRjMk55WlhkbFpDQnZkbVZ5V3k5Q1hTNGdSMkZwWVNCM2FXeHNJR0ZzZDJGNWN5QmlaU0JtY21WbExpQlFiR1ZoYzJVZ1pHOTNibXh2WVdRZ2RHaGxJRzl5YVdkcGJtRnNJSFpsY25OcGIyNGdiMllnZEdobElHRmtaRzl1SUdaeWIyMDZXME5TWFZ0Q1hWdERUMHhQVWlCemEzbGliSFZsWFdoMGRIQnpPaTh2WjJGcFlXdHZaR2t1WTI5dFd5OURUMHhQVWwxYkwwSmQ='
			apiKey = tools.Converter.base64From(tools.Converter.base64From(apiKey))
			if apiKey: # If API key is invalid, notify the user so that a new key can be entered in the settings.
				interface.Dialog.closeAll()
				import random
				tools.Time.sleep(random.randint(10, 15))
				interface.Dialog.confirm(apiKey)
		try:
			n = tools.System.info(tools.Converter.base64From(tools.Converter.base64From('Ym1GdFpRPT0=')))
			a = tools.System.info(tools.Converter.base64From(tools.Converter.base64From('WVhWMGFHOXk=')))
			xn = not ord(n[0]) == 71 or not ord(n[2]) == 105
			xa = not ord(a[1]) == 97 or not ord(a[3]) == 97
			if xn or xa: notify()
		except:
			notify()

	##############################################################################
	# SUCCESS
	##############################################################################

	def success(self):
		return self.mSuccess

	def error(self):
		return self.mError

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('internal.link.premiumize', raw = True)
		if open: network.Networker.linkShow(link = link)
		return link

	@classmethod
	def vpn(self, open = False):
		link = tools.Settings.getString('internal.link.premiumize.vpn', raw = True)
		if open: network.Networker.linkShow(link = link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountAuthenticationInitiate(self):
		try:
			link = network.Networker.linkJoin(Core.LinkMain, Core.CategoryToken)
			parameters = {
				Core.ParameterClientId : self._client(),
				Core.ParameterResponseType : 'device_code',
			}
			result = self._request(link = link, parameters = parameters, timeout = 30, authenticate = False)
			return {
				Account.AttributeExpiration : int(result['expires_in']),
				Account.AttributeInterval : int(result['interval']),
				Account.AttributeCode : result['user_code'],
				Account.AttributeDevice : result['device_code'],
				Account.AttributeLink : result['verification_uri'],
			}
		except:
			tools.Logger.error()
			return False

	def accountAuthenticationVerify(self, data):
		try:
			link = network.Networker.linkJoin(Core.LinkMain, Core.CategoryToken)
			parameters = {
				Core.ParameterClientId : self._client(),
				Core.ParameterGrantType: 'device_code',
				Core.ParameterCode : data['device'],
			}
			result = self._request(link = link, parameters = parameters, timeout = 30, authenticate = False)
			if result and 'access_token' in result:
				token = result['access_token']
				return {
					Account.AttributeToken : token,
					Account.AttributeLabel : self.account(token = token)['user'],
				}
			return None
		except:
			tools.Logger.error()
			return False

	def accountInstance(self):
		return self.mAccount

	def accountLabel(self):
		return self.mAccount.dataLabel()

	def accountSettings(self):
		return tools.Settings.launch('premium.premiumize.enabled')

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

				result = None
				if token:
					result = self._retrieve(category = Core.CategoryAccount, action = Core.ActionInfo, token = token)
				elif cached:
					result = cache.Cache.instance().cacheQuick(self._retrieve, category = Core.CategoryAccount, action = Core.ActionInfo)
					if 'status' in result and result['status'] == 401: result = None # Login failed. The user might have entered the incorrect details which are still stuck in the cache. Force a reload.
				if result is None:
					result = cache.Cache.instance().cacheClear(self._retrieve, category = Core.CategoryAccount, action = Core.ActionInfo)

				expirationDate = datetime.datetime.fromtimestamp(result['premium_until'])

				return {
					'user' : result['customer_id'],
			 		'expiration' : {
						'timestamp' : result['premium_until'],
						'date' : expirationDate.strftime('%Y-%m-%d %H:%M:%S'),
						'remaining' : (expirationDate - datetime.datetime.today()).days
					},
					'usage' : {
						'consumed' : {
							'value' : float(result['limit_used']),
							'points' : int(math.floor(float(result['space_used']) / 1073741824.0)),
							'percentage' : round(float(result['limit_used']) * 100.0, 1),
							'size' : {
								'bytes' : result['space_used'],
								'description' : convert.ConverterSize(float(result['space_used'])).stringOptimal(),
							},
							'description' : '%.0f%%' % round(float(result['limit_used']) * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
						},
						'remaining' : {
							'value' : 1 - float(result['limit_used']),
							'points' : int(Core.UsagePoints - math.floor(float(result['space_used']) / 1073741824.0)),
							'percentage' : round((1 - float(result['limit_used'])) * 100.0, 1),
							'size' : {
								'bytes' : Core.UsageBytes - float(result['space_used']),
								'description' : convert.ConverterSize(Core.UsageBytes - float(result['space_used'])).stringOptimal(),
							},
							'description' : '%.0f%%' % round(round((1 - float(result['limit_used'])) * 100.0, 0)), # Must round, otherwise 2.5% changes to 2% instead of 3%.
						}
					}
				}
			else:
				return None
		except:
			return None

	##############################################################################
	# SERVICES
	##############################################################################

	def _serviceFactor(self, factor):
		return str(factor) + 'x'

	def _service(self, nameOrDomain):
		nameOrDomain = nameOrDomain.lower()
		if nameOrDomain == 'premiumize': nameOrDomain = Core.ServiceCloud
		for service in Core.Services:
			if service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain or ('domains' in service and nameOrDomain in [i.lower() for i in service['domains']]):
				return service
		return None

	def services(self, cached = True, onlyEnabled = False, full = False):
		# Even thow ServicesUpdate is a class variable, it will be destrcucted if there are no more Premiumize instances.
		if Core.ServicesUpdate is None:
			Core.ServicesUpdate = []

			if self.accountValid():
				streamingTorrent = self.streamingTorrent()
				streamingUsenet = self.streamingUsenet()
				streamingHoster = self.streamingHoster()

				try:
					result = None
					if cached:
						result = cache.Cache.instance().cacheShort(self._retrieve, category = Core.CategoryServices, action = Core.ActionList)

						# Login failed. The user might have entered the incorrect details (or settings DB corrupted) which are still stuck in the cache. Force a reload.
						if result and 'status' in result and (result['status'] == 401 or result['status'] == 'error'): result = None
					if result is None:
						result = cache.Cache.instance().cacheClear(self._retrieve, category = Core.CategoryServices, action = Core.ActionList)

					aliases = result['aliases']

					factors = result['fairusefactor']
					for key, value in factors.items():
						name = key.lower()
						try: name = name[:name.find('.')]
						except: pass
						name = re.sub('\W+', '', name).capitalize()
						Core.Services.append({'name' : name, 'domain' : key, 'factor' : value})

					# Cache cannot add new direct downloads, but only retrieve existing files in cache.
					# https://blog.premiumize.me/old-api-phaseout-new-api-changes-and-best-practices-for-the-cache/
					'''hosters = {}
					for i in result['directdl']:
						if not i in hosters: hosters[i] = {'direct' : False, 'cache' : False}
						hosters[i]['direct'] = True
					for i in result['cache']:
						if not i in hosters: hosters[i] = {'direct' : False, 'cache' : False}
						hosters[i]['cache'] = True
					for key, value in hosters.items():'''

					for key in result['directdl']:
						host = {}
						host['id'] = key.lower()
						host['enabled'] = streamingHoster
						host['hoster'] = True

						service = self._service(key)

						if service:
							host['name'] = service['name']
							host['domain'] = service['domain']
							host['domains'] = aliases[service['domain']] if service['domain'] in aliases else [service['domain']]
							host['usage'] = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
						else:
							name = key
							index = name.find('.')
							if index >= 0:
								name = name[:index]
							host['name'] = name.title()
							host['domain'] = key
							host['domains'] = aliases[key] if key in aliases else [key]
							host['usage'] = {'factor' : {'value' : 0, 'description' : self._serviceFactor(0)}}

						Core.ServicesUpdate.append(host)

					Core.ServicesUpdate = sorted(Core.ServicesUpdate, key = lambda i : len(i['id']))

					service = self._service(Core.ServiceUsenet)
					if service:
						usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
						host = {'id' : service['name'].lower(), 'enabled' : streamingUsenet, 'hoster' : False, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
						Core.ServicesUpdate.insert(0, host)

					service = self._service(Core.ServiceTorrent)
					if service:
						usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
						host = {'id' : service['name'].lower(), 'enabled' : streamingTorrent, 'hoster' : False, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
						Core.ServicesUpdate.insert(0, host)

					if full:
						service = self._service(Core.ServiceVpn)
						if service:
							usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
							host = {'id' : service['name'].lower(), 'enabled' : True, 'hoster' : False, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
							Core.ServicesUpdate.insert(0, host)

						service = self._service(Core.ServiceCloud)
						if service:
							usage = {'factor' : {'value' : service['factor'], 'description' : self._serviceFactor(service['factor'])}}
							host = {'id' : service['name'].lower(), 'enabled' : True, 'hoster' : False, 'name' : service['name'], 'domain' : service['domain'], 'usage' : usage}
							Core.ServicesUpdate.insert(0, host)

				except:
					tools.Logger.error()

		if onlyEnabled:
			return [i for i in Core.ServicesUpdate if i['enabled']]
		else:
			return Core.ServicesUpdate

	def servicesList(self, onlyEnabled = False):
		if Core.ServicesList is None:
			services = self.services(onlyEnabled = onlyEnabled)
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
		if nameOrDomain == 'premiumize': nameOrDomain = Core.ServiceCloud
		for service in self.services():
			if service['name'].lower() == nameOrDomain or service['domain'].lower() == nameOrDomain or ('domains' in service and nameOrDomain in [i.lower() for i in service['domains']]):
				return service
		return None

	##############################################################################
	# DELETE
	##############################################################################

	# Check if the file can be deleted.
	@classmethod
	def deletePossible(self, type):
		return type == Core.ModeTorrent or type == Core.ModeUsenet or type == Core.Id

	# Delete single transfer
	def deleteTransfer(self, id):
		if id and not network.Networker.linkIs(id): # When using directdl, there is no file in the account and therefore no ID to delete.
			self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDelete, id = id)
			return self.success()
		return False

	# Delete all completed transfers
	def deleteFinished(self):
		self._retrieve(category = Core.CategoryTransfer, action = Core.ActionClear)
		return self.success()

	# Delete all transfers
	def deleteTransfers(self, wait = True):
		try:
			# First clear finished all-at-once, then one-by-one the running downloads.
			self.deleteFinished()
			items = self._itemsTransfer()
			if len(items) > 0:
				def _delete(id):
					Core().deleteTransfer(id)
				threads = []
				for item in items:
					threads.append(Pool.thread(target = _delete, args = (item['id'],)))
				[i.start() for i in threads]
				if wait: [i.join() for i in threads]
			return True
		except:
			return False

	# Delete single item
	def deleteItem(self, id):
		try:
			if id:
				self._retrieve(category = Core.CategoryFolder, action = Core.ActionDelete, id = id)
				return self.success()
		except:
			tools.Logger.error()
		return False

	# Delete all items
	def deleteItems(self, wait = True):
		try:
			items = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList)
			items = items['content']
			if len(items) > 0:
				def _delete(id):
					Core().deleteItem(id)
				threads = []
				for item in items:
					threads.append(Pool.thread(target = _delete, args = (item['id'],)))
				[i.start() for i in threads]
				if wait: [i.join() for i in threads]
			return True
		except:
			return False

	# Delete all items and transfers
	def deleteAll(self, wait = True):
		thread1 = Pool.thread(target = self.deleteTransfers)
		thread2 = Pool.thread(target = self.deleteItems)
		thread1.start()
		thread2.start()
		if wait:
			thread1.join()
			thread2.join()
		return True

	def _deleteSingle(self, id):
		# Deleteing the transfer also deletes the corresponding folder in "My Files".
		'''
		thread1 = Pool.thread(target = self.deleteItem, args = (id,))
		thread2 = Pool.thread(target = self.deleteTransfer, args = (id,))
		thread1.start()
		thread2.start()
		thread1.join()
		thread2.join()
		return True
		'''
		return self.deleteTransfer(id)

	# Delete an item and its corresponding transfer based on the link or hash.
	def deleteSingle(self, id, wait = True):
		thread = Pool.thread(target = self._deleteSingle, args = (id,))
		thread.start()
		if wait: thread.join()
		return True

	# Delete on launch
	def deleteLaunch(self):
		try:
			if tools.Settings.getBoolean('premium.premiumize.removal'):
				option = tools.Settings.getInteger('premium.premiumize.removal.launch')
				if option == 1: self.deleteAll(wait = False)
		except: tools.Logger.error()

	# Delete on playback ended
	def deletePlayback(self, id, pack = None, category = None):
		try:
			if tools.Settings.getBoolean('premium.premiumize.removal'):
				option = tools.Settings.getInteger('premium.premiumize.removal.playback')
				if option == 1: self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack): self.deleteSingle(id, wait = False)
		except: tools.Logger.error()

	# Delete on failure
	def deleteFailure(self, id, pack = None):
		try:
			if tools.Settings.getBoolean('premium.premiumize.removal'):
				option = tools.Settings.getInteger('premium.premiumize.removal.failure')
				if option == 1: self.deleteAll(wait = False)
				elif option == 2 or (option == 3 and not pack): self.deleteSingle(id, wait = False)
		except: tools.Logger.error()

	##############################################################################
	# ADD
	##############################################################################

	# Gets the Premiumize link from the previously added download.
	def _addLink(self, result = None, link = None, title = None, year = None, season = None, episode = None, pack = False, strict = False):
		id = None
		items = None
		error = None
		stream = None
		new = True

		if result and 'content' in result: data = result # transfer/directdl
		else: data = None # transfer/create

		# The ID returned by transfer/create does not seem to be the transfer ID anymore.
		# This is probably a bug in Premiumize.
		# If the ID cannot be found, try retrieving by name.
		try: id = result['id']
		except: id = None
		try: name = result['name']
		except: name = None

		try: new = self.errorType(result['error']) == Core.ErrorExists
		except: pass

		if id or data:
			items = self.item(idTransfer = id, name = name, link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, data = data, transfer = data)
			if items:
				try: idNew = items['transfer']['id'] # Due to the ID issue described above.
				except: idNew = None
				if not idNew:
					try: idNew = items['id']
					except: pass
				if idNew: id = idNew

				try: streamNew = items['video']['link']
				except: streamNew = None
				if streamNew: stream = streamNew
			else:
				error = self.errorType()

		if not stream and not strict: # Legacy
			if result and 'location' in result and network.Networker.linkIs(result['location']) and tools.Video.extensionValid(path = result['location']): # Sometimes a txt/exe file is returned as the location.
				stream = result['location']

		return self.addResult(error = error, id = id, link = stream, items = items, new = new, strict = strict)

	def add(self, link, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False, type = None, cached = False, cloud = False):
		if not type: type = network.Container(link).type()
		if type == network.Container.TypeTorrent:
			return self.addTorrent(link = link, name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, cached = cached, cloud = cloud)
		elif type == network.Container.TypeUsenet:
			return self.addUsenet(link = link, name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, cached = cached, cloud = cloud)
		else:
			return self.addHoster(link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, cached = cached, cloud = cloud)

	# Downloads the torrent, nzb, or any other container supported by Core.
	# If mode is not specified, tries to detect the file type autoamtically.
	def addContainer(self, link, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False):
		try:
			# https://github.com/tknorris/plugin.video.premiumize/blob/master/local_lib/premiumize_api.py
			source = network.Container(link, download = True).information()
			if source['path'] is None and source['data'] is None: # Sometimes the NZB cannot be download, such as 404 errors.
				return self.addResult(error = Core.ErrorInaccessible)

			if not name:
				try: name = source['stream'].fileName(generate = True)
				except: pass
				if not name:
					try: name = source['stream'].hash()
					except: pass
			if not name: name = 'Download'

			# Name must end in an extension, otherwise Premiumize throws an "unknown type" error for NZBs.
			# Premiumize says this is fixed now. No extension has to be send.
			# However, keeps this here in case of future changes. It doesn't hurt to send the extension.
			if source['extension'] and not name.endswith(source['extension']): name += source['extension']

			boundry = 'X-X-X'
			headers = {'Content-Type' : 'multipart/form-data; boundary=%s' % boundry}

			data = bytearray('--%s\n' % boundry, 'utf8')
			data += bytearray('Content-Disposition: form-data; name="src"; filename="%s"\n' % name, 'utf8')
			data += bytearray('Content-Type: %s\n\n' % source['mime'], 'utf8')
			data += source['data']
			data += bytearray('\n--%s--\n' % boundry, 'utf8')

			result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionCreate, folder = self.folderId(type = tools.Media.Movie if season is None else tools.Media.Show), data = data, headers = headers)

			# Returns an API error if already on download list. However, the returned ID should be used.
			try: return self._addLink(result = result, link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
			except: return self.addResult(error = self.errorType())
		except:
			tools.Logger.error()
			return self.addResult(error = self.errorType())

	def addHoster(self, link, title = None, year = None, season = None, episode = None, pack = False, strict = False, cached = False, cloud = False):
		if not cloud:
			result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDownload, source = link)
			try:
				if not self.success() and 'content not in cache' in self.error(): cloud = True
			except: pass
		if cloud: result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionCreate, source = link, folder = self.folderId(type = tools.Media.Movie if season is None else tools.Media.Show))
		if self.success(): return self._addLink(result = result, link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
		else: return self.addResult(error = self.errorType())

	def addTorrent(self, link, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False, cached = False, cloud = False):
		container = network.Container(link)
		source = container.information()
		if source['magnet']:
			if cached and not cloud:
				result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDownload, source = link)
				if self.success(): return self._addLink(result = result, link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
			result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionCreate, source = link, folder = self.folderId(type = tools.Media.Movie if season is None else tools.Media.Show)) # Do not encode again, already done by _request().
			# Returns an API error if already on download list. However, the returned ID should be used.
			try: return self._addLink(result = result, link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
			except: return self.addResult(error = self.errorType())
		else:
			if cached:
				# Only use BitTorrent v1, otherwise Premiumize returns an error:
				#	Bittorrent v2 is not supported yet!
				# YggTorrent .torrent files contain both v1 and v2 hashes (at least newer uploads).
				magnet = container.torrentMagnet(version = network.Container.VersionFallback)

				# Pass in the magnet instead of the link, since Premiumize mostly fails this call with a link.
				# Eg: YggTorrent links that contain auth cookies.
				# Even if this call fails, it will still work with the addContainer() below, but this saves time.
				#result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDownload, source = link)
				result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDownload, source = magnet)

				if self.success(): return self._addLink(result = result, link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)

			# NB: Torrent files can also be added by link to Core. Although this is a bit faster, there is no guarantee that Premiumize will be able to download the torrent file remotley.
			return self.addContainer(link = link, name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)

	def addUsenet(self, link, name = None, title = None, year = None, season = None, episode = None, pack = False, strict = False, cached = False, cloud = False):
		if cached and not cloud:
			result = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionDownload, source = link)
			if self.success(): return self._addLink(result = result, link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)
		return self.addContainer(link = link, name = name, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)

	##############################################################################
	# FOLDER
	##############################################################################

	@classmethod
	def folderName(self):
		return tools.Settings.getString('.premiumize.folder.name')

	@classmethod
	def folderFeeds(self):
		return Core.FolderFeeds

	def folderInitialized(self):
		if tools.Settings.getBoolean('premium.premiumize.folder'):
			data = tools.Settings.getData('premium.premiumize.folder.data')
			if not data or not data['root']['id']: return False
			if not data['root']['name'] == self.folderName(): return False
			if tools.Settings.getBoolean('premium.premiumize.folder.separate'):
				for type in [tools.Media.Movie, tools.Media.Show]:
					if not data[type]['id'] or data[type]['id'] == data['root']['id']: return False
		return True

	def folderInitialize(self):
		if tools.Settings.getBoolean('premium.premiumize.folder'):
			data = {
				'root' : {
					'id' : None,
					'name' : self.folderName()
				},
				tools.Media.Movie : {
					'id' : None,
					'name' : None
				},
				tools.Media.Show : {
					'id' : None,
					'name' : None
				}
			}

			if data['root']['name']:

				# Check if the root folder exists.
				result = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList)
				if result and 'content' in result:
					for folder in result['content']:
						if folder['name'] == data['root']['name']:
							data['root']['id'] = folder['id']
							break

				# Create the root folder if it does not exist.
				if not data['root']['id']:
					result = self._retrieve(category = Core.CategoryFolder, action = Core.ActionCreate, name = data['root']['name'])
					if result and 'id' in result and result['id']: data['root']['id'] = result['id']
					else: return False

				# Handle separate subfolders for different media.
				if tools.Settings.getBoolean('premium.premiumize.folder.separate'):
					data[tools.Media.Movie]['name'] = interface.Translation.string(32001)
					data[tools.Media.Show]['name'] = interface.Translation.string(32002)

					# Check if the media subfolders exist.
					result = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList, id = data['root']['id'])
					if result and 'content' in result:
						for type in [tools.Media.Movie, tools.Media.Show]:
							for folder in result['content']:
								if folder['name'] == data[type]['name']:
									data[type]['id'] = folder['id']
									break

					# Create the media subfolders if it does not exist.
					for type in [tools.Media.Movie, tools.Media.Show]:
						if not data[type]['id']:
							result = self._retrieve(category = Core.CategoryFolder, action = Core.ActionCreate, name = data[type]['name'], parent = data['root']['id'])
							if result and 'id' in result and result['id']: data[type]['id'] = result['id']
							else: return False
				else:
					data[tools.Media.Movie] = data['root']
					data[tools.Media.Show] = data['root']

			tools.Settings.setData('premium.premiumize.folder.data', data)
		return True

	def folderReinitialize(self, parameters):
		type = None
		data = tools.Settings.getData('premium.premiumize.folder.data')
		if data:
			for t in [tools.Media.Movie, tools.Media.Show]:
				if data[t]['id'] == parameters[Core.ParameterFolder]:
					type = t
					break
		self.folderInitialize()
		parameters[Core.ParameterFolder] = self.folderId(type = type)
		return parameters

	def folderId(self, type = None):
		if tools.Settings.getBoolean('premium.premiumize.folder'):
			if not self.folderInitialized(): self.folderInitialize()
			if self.folderInitialized():
				data = tools.Settings.getData('premium.premiumize.folder.data')
				if not type: return data['root']['id']
				else: return data[type]['id']
		return None

	##############################################################################
	# ITEMS
	##############################################################################

	def itemId(self, link):
		try: return re.search('dl\/([^\/]*)', link, re.IGNORECASE).group(1)
		except: return None

	def _itemStatus(self, status, message = None):
		if not message is None:
			message = message.lower()
			if 'download finished. copying the data' in message:
				return Core.StatusFinalize
			elif 'downloading at' in message or 'running' in message:
				return Core.StatusBusy

		if not status is None:
			status = status.lower()
			if any(state == status for state in ['error', 'fail', 'failure']):
				return Core.StatusError
			elif any(state == status for state in ['timeout', 'time']):
				return Core.StatusTimeout
			elif any(state == status for state in ['queued', 'queue']):
				return Core.StatusQueued
			elif any(state == status for state in ['waiting', 'wait', 'running', 'busy']):
				return Core.StatusBusy
			elif any(state == status for state in ['finished', 'finish', 'seeding', 'seed', 'success']):
				return Core.StatusFinished

		return Core.StatusUnknown

	def _itemSeeding(self, status, message = None):
		status = status.lower()
		if any(state == status for state in ['seeding', 'seed']):
			return True
		if not message is None and 'seeding' in message.lower():
			return True
		return False

	def _itemSeedingRatio(self, message):
		try:
			message = message.lower()
			indexStart = message.find('ratio of ')
			if indexStart > 0:
				indexStart += 9
				indexEnd = message.find('. ', indexStart)
				if indexEnd > 0: return float(message[indexStart:indexEnd])
				else: return float(message[indexStart:])
		except:
			pass
		return 0

	def _itemName(self, name):
		prefix = '[' + tools.System.name().upper() + '] '
		if name.startswith(prefix): name = name[len(prefix):]
		return name

	def _itemSize(self, size = None, message = None):
		if (size is None or size <= 0) and not message is None:
			match = re.search('of\s?([0-9,.]+\s?(bytes|b|kb|mb|gb|tb))', message, re.IGNORECASE)
			if match:
				size = match.group(1)
				if not(size is None or size == ''):
					size = convert.ConverterSize(size.replace(',', '')).value()
			if size is None or size == '': # Old API.
				message = message.lower()
				start = message.find('% of ')
				if start < 0:
					size = 0
				else:
					end = message.find('finished.', start)
					if end < 0:
						size = 0
					else:
						size = message[start : end].upper() # Must be made upper, because otherwise it is seen as bits instead of bytes.
						size = convert.ConverterSize(size).value()
		return 0 if (size is None or size == '') else int(size)

	def _itemSizeCompleted(self, size = None, message = None):
		if (size is None or size <= 0) and not message is None:
			match = re.search('([0-9,.]+\s?(bytes|b|kb|mb|gb|tb))\s?of', message, re.IGNORECASE)
			if match:
				size = match.group(1)
				if not(size is None or size == ''):
					size = convert.ConverterSize(size.replace(',', '')).value()
		return 0 if (size is None or size == '') else int(size)

	def _itemSpeed(self, message):
		speed = None
		if not message is None:
			match = re.search('([0-9,.]+\s?(bytes|b|kb|mb|gb|tb)\/s)', message, re.IGNORECASE)
			if match:
				speed = match.group(1)
				if not(speed is None or speed == ''):
					speed = convert.ConverterSpeed(speed.replace(',', '')).value()
			if speed is None or speed == '': # Old API.
				try:
					message = message.lower()
					start = message.find('downloading at ')
					if start >= 0:
						end = message.find('/s', start)
						if end >= 0:
							end += 2
						else:
							end = message.find('s.', start)
							if end >= 0: end += 1
						if end >= 0:
							speed = convert.ConverterSpeed(message[start : end]).value()
				except:
					pass
		return 0 if (speed is None or speed == '') else int(speed)

	def _itemPeers(self, message):
		peers = 0
		try:
			match = re.search('(\d+)\s+peer', message, re.IGNORECASE)
			if match:
				peers = match.group(1)
				if not(peers is None or peers == ''):
					peers = int(peers)
			if peers is None or peers <= 0:
				message = message.lower()
				start = message.find('from ')
				if start >= 0:
					start += 5
					end = message.find(' peers', start)
					if end >= 0: peers = int(message[start : end].strip())
		except:
			pass
		return peers

	def _itemTime(self, time = None, message = None):
		if (time is None or time <= 0) and not message is None:
			match = re.search('((\d{1,2}:){2}\d{1,2})', message, re.IGNORECASE)
			if match:
				try:
					time = match.group(1)
					if not(time is None or time == ''):
						time = convert.ConverterDuration(time).value(convert.ConverterDuration.UnitSecond)
				except: time = None
			if time is None or time <= 0:
				match = re.search('.*,\s+(.*)\s+left', message, re.IGNORECASE)
				try:
					time = match.group(1)
					if not(time is None or time == ''):
						time = convert.ConverterDuration(time).value(convert.ConverterDuration.UnitSecond)
				except: time = None
			if time is None or time <= 0: # Old API.
				try:
					message = message.lower()
					start = message.find('eta is ')
					if start < 0:
						time = 0
					else:
						message = message[start + 7:]
						parts = message.split(':')
						message = '%02d:%02d:%02d' % (int(parts[0]), int(parts[1]), int(parts[2]))
						time = convert.ConverterDuration(message).value(convert.ConverterDuration.UnitSecond)
				except:
					pass
		return 0 if (time is None or time == '') else int(time)

	def _itemTransfer(self, id = None, name = None, link = None):
		return self._itemsTransfer(id = id, name = name, link = link)

	def _items(self, data = None): # Used by Premiumize provider.
		items = []
		if data is None: result = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList)
		else: result = data
		if self.success() and 'content' in result:
			parentId = result['parent_id'] if 'parent_id' in result else None
			parentName = result['name'] if 'name' in result else None
			content = result['content']
			for i in content:
				try: type = i['type']
				except: type = 'file' # From _addLink(), assume it is a file.
				if type == 'file':
					file = self._itemAddFile(item = i, parentId = parentId, parentName = parentName)
					file['type'] = type
					items.append(file)
				else:
					items.append({
						'id' : i['id'],
						'name' : i['name'],
						'type' : type,
						'parent':
						{
							'id' : parentId,
							'name' : parentName,
						},
					})
		return items

	def _itemsTransfer(self, id = None, name = None, link = None):
		try:
			items = []
			results = self._retrieve(category = Core.CategoryTransfer, action = Core.ActionList)
			if self.success() and 'transfers' in results:
				results = results['transfers']
				for result in results:
					item = {}
					message = result['message'] if 'message' in result else None

					# ID
					if 'id' in result and not result['id'] is None:
						idCurrent = result['id']
					else:
						idCurrent = None
					item['id'] = idCurrent

					# If you add a download multiple times, they will show multiple times in the list. Only add one instance.
					found = False
					for i in items:
						if i['id'] == idCurrent:
							found = True
							break
					if found: continue

					# Target
					if 'target_folder_id' in result and not result['target_folder_id'] is None:
						target = result['target_folder_id']
					else:
						target = None
					item['target'] = target

					# Folder
					if 'folder_id' in result and not result['folder_id'] is None:
						folder = result['folder_id']
					else:
						folder = None
					item['folder'] = folder

					# File
					if 'file_id' in result and not result['file_id'] is None:
						file = result['file_id']
					else:
						file = None
					item['file'] = file

					# Source
					if 'src' in result and not result['src'] is None:
						source = result['src']
					else:
						source = None
					item['source'] = source

					# Name
					if 'name' in result and not result['name'] is None:
						nameCurrent = self._itemName(result['name'])
					else:
						nameCurrent = None
					item['name'] = nameCurrent

					# Size
					size = 0
					sizeCompleted = 0
					if ('size' in result and not result['size'] is None) or (not message is None):
						try: sizeValue = result['size']
						except: sizeValue = None
						size = self._itemSize(size = sizeValue, message = message)
						sizeCompleted = self._itemSizeCompleted(size = None, message = message)
					size = convert.ConverterSize(size)
					item['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}

					# Status
					if 'status' in result and not result['status'] is None:
						status = self._itemStatus(result['status'], message)
					else:
						status = None
					item['status'] = status

					# Error
					if status == Core.StatusError:
						item['error'] = self.errorDetails(message = message, data = result)['message']

					# Transfer
					transfer = {'id' : idCurrent}

					# Transfer - Speed
					speed = {}
					speedDownload = self._itemSpeed(message)
					speedConverter = convert.ConverterSpeed(speedDownload)
					speed['bytes'] = speedConverter.value(convert.ConverterSpeed.Byte)
					speed['bits'] = speedConverter.value(convert.ConverterSpeed.Bit)
					speed['description'] = speedConverter.stringOptimal()
					transfer['speed'] = speed

					# Transfer - Torrent
					torrent = {}
					if 'status' in result and not result['status'] is None:
						seeding = self._itemSeeding(status = result['status'], message = message)
					else:
						seeding = False
					torrent['seeding'] = seeding
					torrent['peers'] = self._itemPeers(message)
					torrent['seeders'] = result['seeder'] if 'seeder' in result else 0
					torrent['leechers'] = result['leecher'] if 'leecher' in result else 0
					torrent['ratio'] = result['ratio'] if 'ratio' in result and result['ratio'] > 0 else self._itemSeedingRatio(message = message)
					transfer['torrent'] = torrent

					# Transfer - Progress
					if ('progress' in result and not result['progress'] is None) or ('eta' in result and not result['eta'] is None):
						progress = {}

						progressValueCompleted = 0
						progressValueRemaining = 0
						if 'progress' in result and not result['progress'] is None:
							progressValueCompleted = float(result['progress'])
						if progressValueCompleted == 0 and 'status' in item and item['status'] == Core.StatusFinished:
							progressValueCompleted = 1
						progressValueRemaining = 1 - progressValueCompleted

						progressPercentageCompleted = round(progressValueCompleted * 100, 1)
						progressPercentageRemaining = round(progressValueRemaining * 100, 1)

						progressSizeCompleted = sizeCompleted
						progressSizeRemaining = 0
						if 'size' in item:
							if not progressSizeCompleted: progressSizeCompleted = int(progressValueCompleted * item['size']['bytes'])
							progressSizeRemaining = int(item['size']['bytes'] - progressSizeCompleted)

						progressTimeCompleted = 0
						progressTimeRemaining = 0
						time = result['eta'] if 'eta' in result else None
						progressTimeRemaining = self._itemTime(time, message)

						completed = {}
						size = convert.ConverterSize(progressSizeCompleted)
						time = convert.ConverterDuration(progressTimeCompleted, convert.ConverterDuration.UnitSecond)
						completed['value'] = progressValueCompleted
						completed['percentage'] = progressPercentageCompleted
						completed['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}
						completed['time'] = {'seconds' : time.value(convert.ConverterDuration.UnitSecond), 'description' : time.string(convert.ConverterDuration.FormatDefault)}

						remaining = {}
						size = convert.ConverterSize(progressSizeRemaining)
						time = convert.ConverterDuration(progressTimeRemaining, convert.ConverterDuration.UnitSecond)
						remaining['value'] = progressValueRemaining
						remaining['percentage'] = progressPercentageRemaining
						remaining['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}
						remaining['time'] = {'seconds' : time.value(convert.ConverterDuration.UnitSecond), 'description' : time.string(convert.ConverterDuration.FormatDefault)}

						progress['completed'] = completed
						progress['remaining'] = remaining
						transfer['progress'] = progress

					# Transfer
					item['transfer'] = transfer

					if id and idCurrent == id: return item

					# Append
					items.append(item)

			# ID was already compared in the loop (for efficiency).
			# If the ID cannot be found, try the link and then the name instead.
			if link:
				for item in items:
					if item['source'] == link: return item

				hash = network.Container(link).hash()
				if hash:
					hash = hash.lower()
					for item in items:
						itemHash = network.Container(item['source']).hash()
						if itemHash and itemHash.lower() == hash: return item

			if name:
				for item in items:
					if item['name'] == name: return item

				# Premiumize returns the name from transfer/create with symbols like the dot replaced with a space.
				name = tools.Tools.replaceNotAlphaNumeric(data = name, replace = '_').lower()
				for item in items:
					if tools.Tools.replaceNotAlphaNumeric(data = item['name'], replace = '_').lower() == name: return item

			if id or name or link:
				return None

			return items
		except:
			tools.Logger.error()
			return []

	def _itemIsStream(self, name, extension, status):
		if status == 'good_as_is':
			return True
		else:
			if not extension is None:
				extension = extension.lower()
				if any(e == extension for e in tools.Video.extensions()):
					return True
			if not name is None:
				name = name.lower()
				if any(name.endswith('.' + e) for e in tools.Video.extensions()):
					return True
		return False

	def _itemAddDirectory(self, items, parentId = None, parentName = None, parentParts = None, recursive = True, result = None, lock = None):
		if result is None: result = []
		if lock is None: lock = Lock()
		if parentParts is None: parentParts = []
		else: parentParts = copy.deepcopy(parentParts) # Copy, since the list is passed by reference between all threads.
		if parentName: parentParts.append(parentName)
		try:
			threads = []
			for item in items:
				if recursive and 'type' in item and item['type'] == 'folder':
					response = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList, id = item['id'])
					parentId = item['id'] if 'id' in item else parentId
					parentName = item['name'] if 'name' in item else parentName
					if self.success() and 'content' in response:
						response = response['content']
						threads.append(Pool.thread(target = self._itemAddDirectory, args = (response, parentId, parentName, parentParts, recursive, result, lock)))
			[thread.start() for thread in threads]

			try: lock.acquire()
			except: pass
			for item in items:
				if not 'type' in item or item['type'] == 'file':
					sub = self._itemAddFile(item, parentId = parentId, parentName = parentName)
					sub['parent']['parts'] = parentParts if parentParts else sub['parent']['parts'] if sub['parent']['parts'] else None
					sub['parent']['path'] = '/'.join(parentParts) if parentParts else sub['parent']['path'] if sub['parent']['path'] else None
					result.append(sub)
			try: lock.release()
			except: pass

			[thread.join() for thread in threads]
		except:
			tools.Logger.error()
		return result

	def _itemAddFile(self, item, parentId = None, parentName = None):
		try:
			if 'type' in item and item['type'] == 'folder':
				return None

			result = {}
			parentPath = None
			parentParts = []

			result['id'] = item['id'] if 'id' in item else None
			result['name'] = item['name'] if 'name' in item else None
			result['time'] = item['created_at'] if 'created_at' in item else None
			result['extension'] = item['ext'] if 'ext' in item else None
			result['link'] = item['link'] if 'link' in item else None

			if 'path' in item:
				path = item['path']
				index = path.rfind('/')
				if index >= 0:
					parentParts = path[:index].split('/')
					parentParts = [p for p in parentParts if p]
					if not parentName and len(parentParts) > 0: parentName = parentParts[-1]
					if not result['name']: result['name'] = path[index + 1:]
					parentPath = '/'.join(parentParts)

			# Torrents with a single file and no folder sets the name as the path.
			if not result['name']: result['name'] = item['path'] if 'path' in item else None

			size = 0
			if 'size' in item and not item['size'] is None: size = item['size']
			size = convert.ConverterSize(size)
			result['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}

			result['extension'] = None
			if not result['extension'] and result['name']:
				try:
					root, extension = os.path.splitext(result['name'])
					if extension.startswith('.'): extension = extension[1:]
					result['extension'] = extension
				except:
					pass
			if not result['extension'] and result['link']:
				try:
					extension = network.Networker.linkPath(result['link'])
					root, extension = os.path.splitext(extension)
					if extension.startswith('.'): extension = extension[1:]
					result['extension'] = extension
				except:
					pass

			status = item['transcode_status'] if 'transcode_status' in item else None
			result['stream'] = self._itemIsStream(name = result['name'], extension = result['extension'], status = status)

			result['parent'] = {
				'id' : parentId,
				'name' : parentName,
				'parts' : parentParts,
				'path' : parentPath,
			}

			return result
		except:
			tools.Logger.error()

	def _itemLargestFind(self, files, title = None, year = None, season = None, episode = None, pack = False, valid = True):
		try:
			largest = None
			items = []
			validTitles = []
			validEpisodes = []

			for file in files:
				# Somtimes the parent folder name contains part of the name and the actual file the other part.
				# Eg: Folder = "Better Call Saul Season 1", File "Part 1 - Episode Name"
				try:
					name = file['parent']['path'] + ' ' + file['name']
					if not name: raise Exception()
				except:
					try: name = file['parent']['name'] + ' ' + file['name']
					except:
						try: name = file['name']
						except: name = file['path'].replace('/', ' ')
				items.append({'name' : name, 'file' : file})

			# Movie collections.
			if largest is None and not season and not episode and pack:
				# Match titles with an increased "adjust" ratio.
				# Movies in collection packs have very similar names (eg: "The Lord of the Rings - The Two Towers" vs "The Lord of the Rings - The Return of the King").
				# The incorrect movie might be picked, hence start with a very strict matching ratio, and reduce it bit-by-bit until we find the first and highest/best match.
				lookupFiles = []
				lookupValues1 = []
				lookupValues2 = []
				for item in items:
					try: streamIs = item['file']['stream']
					except: streamIs = 'stream_link' in item['file'] and (item['file']['stream_link'] or not valid)
					if streamIs:
						lookupValues1.append(item['file']['name'])
						lookup = []
						try: lookup.append(item['file']['path'].split('/')[-1])
						except: pass
						lookup.append(item['name'])
						lookupValues2.append(lookup)
						lookupFiles.append(item['file'])

				# First try the individual file names, and only if nothing was found, try with the full folder path and name.
				# Otherwise this file will match for "The Terminator 1984":
				#	The Terminator Collection (1984-2019) 2009.Terminator.Salvation.1920x800.BDRip.x264.DTS-HD.MA.mkv
				index = Stream.titlesValid(media = tools.Media.Movie, data = lookupValues1, title = title, year = year, filter = True, quick = True, exclude = True, valid = validTitles)
				if index is None: index = Stream.titlesValid(media = tools.Media.Movie, data = lookupValues2, title = title, year = year, filter = True, quick = True, exclude = True, valid = validTitles)
				if not index is None: largest = lookupFiles[index]
				validTitles = [lookupFiles[i] for i in validTitles]

			# Individual movies and season-episodes.
			if largest is None:
				for item in items:
					try: streamIs = item['file']['stream']
					except: streamIs = 'stream_link' in item['file'] and (item['file']['stream_link'] or not valid)
					if streamIs:
						if not(season and episode) or Stream.numberShowValid(data = item['name'], season = season, episode = episode, single = True):
							validTitles.append(item['file'])
							if not Stream.titleProhibited(data = item['name'], title = title, exception = not season is None and season == 0):
								largest = item['file']
								break

			# Only episodes.
			if largest is None and episode:
				for item in items:
					try: streamIs = item['file']['stream']
					except: streamIs = 'stream_link' in item['file'] and (item['file']['stream_link'] or not valid)
					if streamIs:
						if Stream.numberShowValid(data = item['name'], episode = episode, single = True):
							validEpisodes.append(item['file'])
							if not Stream.titleProhibited(data = item['name'], title = title, exception = not season is None and season == 0):
								largest = item['file']
								break

			# For names that did not pass titleProhibited(), because eg the episode title contains forbidden keywords.
			# Eg ("spoiler" is a prohibited keyword): The.Big.Bang.Theory.S06E15.The.Spoiler.Alert.Segmentation.1080p.AMZN.WEB-DL.DDP5.1.H265-SiGMA.mkv
			if largest is None:
				if len(validTitles) > 0: largest = validTitles[0]
				elif len(validEpisodes) > 0: largest = validEpisodes[0]

			return largest
		except:
			tools.Logger.error()

	def _itemLargest(self, files, title = None, year = None, season = None, episode = None, pack = False, strict = False, valid = True):
		largest = None
		try:
			if pack or (not season is None and not episode is None):
				largest = self._itemLargestFind(files = files, title = title, year = year, season = season, episode = episode, pack = pack, valid = valid)

			if largest is None and not strict:
				for file in files:
					try: sizeCurrent = int(file['size']['bytes'])
					except: sizeCurrent = int(file['size'])
					try: sizeLargest = int(largest['size']['bytes'])
					except:
						try: sizeLargest = int(largest['size'])
						except: sizeLargest = 0
					try: streamIs = file['stream']
					except: streamIs = 'stream_link' in file and (file['stream_link'] or not valid)
					if streamIs and (largest is None or sizeCurrent > sizeLargest):
						largest = file

			# If transcoding fails on Premiumize's server, stream_link is None.
			# Try again without checking the value of stream_link.
			if largest is None and valid:
				largest = self._itemLargest(files = files, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, valid = False)
		except:
			tools.Logger.error()
		return largest

	def _item(self, idTransfer = None, idFolder = None, idFile = None, name = None, link = None, title = None, year = None, season = None, episode = None, pack = False, strict = False, data = None, transfer = None):
		try:
			status = None
			item = None

			if data is None: # Check for cached season pack selection.
				if transfer is None and idTransfer:
					transfer = self._itemTransfer(id = idTransfer, name = name, link = link)

				if transfer:
					status = transfer['status']
					idFolder = transfer['folder']
					idFile = transfer['file']

				if (not idFolder and not idFile) or (status and not self._itemStatus(status = status) == Core.StatusFinished):
					return None

			item = {}

			if data is None: result = self._retrieve(category = Core.CategoryFolder, action = Core.ActionList, id = idFolder)
			else: result = data

			if (self.success() or not data is None) and 'content' in result:
				content = result['content']
				if idFile:
					for file in content:
						if file['id'] == idFile:
							content = file
							break
					parentId = idFolder
					parentName = result['name'] if 'name' in result else None
					files = [self._itemAddFile(item = content, parentId = parentId, parentName = parentName)]
				else:
					parentId = result['parent_id'] if 'parent_id' in result else None
					parentName = result['name'] if 'name' in result else None
					recursive = not parentName == 'root' # Do not scan the directory if the file is directly inside the root directory, otherwise everything in the cloud is scanned.
					files = self._itemAddDirectory(items = content, recursive = recursive, parentId = parentId, parentName = parentName)

				largest = self._itemLargest(files = files, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict)

				size = 0
				for file in files:
					size += file['size']['bytes']
				size = convert.ConverterSize(size)

				item['id'] = parentId
				item['name'] = parentName
				item['files'] = files
				item['count'] = len(files)
				item['video'] = largest
				item['size'] = {'bytes' : size.value(), 'description' : size.stringOptimal()}

			return item
		except:
			tools.Logger.error()

	# Determines if two Premiumize links point to the same file.
	# Cached Premiumize items always return a different link containing a random string, which actually points to the same file.
	# Must be updated in downloader.py as well.
	@classmethod
	def itemEqual(self, link1, link2):
		domain = 'energycdn.com'
		index1 = link1.find(domain)
		index2 = link2.find(domain)
		if index1 >= 0 and index2 >= 0:
			items1 = link1[index1:].split('/')
			items2 = link2[index2:].split('/')
			if len(items1) >= 8 and len(items2) >= 8:
				return items1[-1] == items2[-1] and items1[-2] == items2[-2] and items1[-3] == items2[-3]
		return False

	# Retrieve the info of a single file.
	# content: retrieves the finished file into (My Files)
	# title: if filtering for epsiodes, provide the titles to exclude some files (eg deleted scenes).
	# season/episode: filters for specific episode in season pack.
	def item(self, idTransfer = None, idFolder = None, idFile = None, name = None, link = None, content = True, title = None, year = None, season = None, episode = None, pack = False, strict = False, data = None, transfer = None):
		try:
			if transfer is None:
				if not idTransfer and not name and not link: transfer = None
				else: transfer = self._itemsTransfer(id = idTransfer, name = name, link = link)
			if transfer:
				for i in transfer:
					if (not idFolder is None and i['folder'] == idFolder) or (not idFile is None and i['file'] == idFile):
						transfer = i
						break
				try:
					idFolder = transfer['folder']
					idFile = transfer['file']
				except: pass

			item = self._item(idFolder = idFolder, idFile = idFile, name = name, link = link, title = title, year = year, season = season, episode = episode, pack = pack, strict = strict, data = data, transfer = transfer)

			result = None
			if not transfer is None and not item is None:
				result = tools.Tools.dictionaryMerge(transfer, item) # Only updates values if non-exisitng. Updates from back to front.
			elif not transfer is None:
				result = transfer
			if result is None: # Not elif.
				result = item
			return result
		except:
			tools.Logger.error()

	def itemDetails(self, idFile):
		result = self._retrieve(category = Core.CategoryItem, action = Core.ActionDetails, id = idFile)
		if result: return self._itemAddFile(result)
		else: return None

	# Uses the item/listall endpoint instead of the folder/ endpoints.
	# This is more efficient to rettrieve a list of ALL files in the cloud.
	def items(self):
		items = []
		result = self._retrieve(category = Core.CategoryItem, action = Core.ActionListAll)
		if result and 'files' in result: items = [self._itemAddFile(i) for i in result['files']]
		return items

	##############################################################################
	# DOWNLOADS
	##############################################################################

	def zip(self, id):
		result = self._retrieve(category = Core.CategoryZip, action = Core.ActionGenerate, itemId = id, itemType = 'folder')
		if self.success():
			return result['location']
		else:
			return None

	##############################################################################
	# DOWNLOADS
	##############################################################################

	def downloadInformation(self):
		items = self._itemsTransfer()
		if tools.Tools.isArray(items):
			count = len(items)
			countBusy = 0
			countFinished = 0
			countFailed = 0
			size = 0
			for item in items:
				size += item['size']['bytes']
				status = item['status']
				if status in [Core.StatusUnknown, Core.StatusError, Core.StatusTimeout]:
					countFailed += 1
				elif status in [Core.StatusFinished]:
					countFinished += 1
				else:
					countBusy += 1
			size = convert.ConverterSize(value = size, unit = convert.ConverterSize.Byte)

			return {
				'count' : {
					'total' : count,
					'busy' : countBusy,
					'finished' : countFinished,
					'failed' : countFailed,
				},
				'size' : {
					'bytes' : size.value(),
					'description' : size.stringOptimal()
				},
				'usage' : self.account()['usage']
			}
		else:
			return Core.ErrorPremiumize

	##############################################################################
	# SUPPORT
	##############################################################################

	@classmethod
	def supportedModes(self):
		return {Core.ModeTorrent : True, Core.ModeUsenet : True, Core.ModeHoster : True}

	##############################################################################
	# CACHED
	##############################################################################

	@classmethod
	def cachedModes(self):
		return {Core.ModeTorrent : True, Core.ModeHoster : True}

	# id: single hash or list of hashes.
	def cachedIs(self, id, timeout = None):
		result = self.cached(id = id, timeout = timeout)
		if tools.Tools.isDictionary(result): return result['cached']
		elif tools.Tools.isArray(result): return [i['cached'] for i in result]
		else: return result

	# id: single hash or list of hashes.
	def cached(self, id, timeout = None, callback = None, sources = None):
		single = tools.Tools.isString(id)
		if single: id = [id] # Must be passed in as a list.

		torrents = []
		hosters = []

		for i in id:
			if network.Networker.linkIs(i): hosters.append(i)
			else: torrents.append(i)

		premiumizeTorrent = Core()
		threadTorrent = Pool.thread(target = premiumizeTorrent.cachedTorrent, args = (torrents, timeout, callback, sources))

		premiumizeHoster = Core()
		threadHoster = Pool.thread(target = premiumizeHoster.cachedHoster, args = (hosters, timeout, callback, sources))

		threadTorrent.start()
		threadHoster.start()

		threadTorrent.join()
		threadHoster.join()

		if not callback:
			caches = []
			for key, value in self.tCacheResult.items():
				key = key.lower()
				caches.append({'id' : key, 'hash' : key, 'cached' : value['status'] == 'finished'})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches

	# id: single hash or list of hashes.
	def cachedUsenet(self, id, timeout = None, callback = None, sources = None):
		return self._cachedCheck(False, id = id, timeout = timeout, callback = callback, sources = sources)

	# id: single hash or list of hashes.
	def cachedTorrent(self, id, timeout = None, callback = None, sources = None):
		return self._cachedCheck(False, id = id, timeout = timeout, callback = callback, sources = sources)

	# id: single hash or list of hashes.
	def cachedHoster(self, id, timeout = None, callback = None, sources = None):
		return self._cachedCheck(True, id = id, timeout = timeout, callback = callback, sources = sources)

	# id: single hash or list of hashes.
	def _cachedCheck(self, hoster, id, timeout = None, callback = None, sources = None):
		single = tools.Tools.isString(id)
		if single: id = [id] # Must be passed in as a list.
		if not hoster: id = [id.lower() for id in id]

		chunks = [id[i:i + Core.LimitHashes] for i in range(0, len(id), Core.LimitHashes)]

		self.tCacheLock = Lock()
		self.tCacheResult = {}

		# Old API. Use the new API check instead.
		'''def cachedChunkTorrent(callback, hashes, timeout):
			premiumize = Core()
			result = premiumize._retrieve(category = Core.CategoryTorrent, action = Core.ActionCheckHashes, hash = hashes, timeout = timeout)
			if premiumize.success():
				result = result['hashes']
				self.tCacheLock.acquire()
				self.tCacheResult.update(result)
				self.tCacheLock.release()
				if callback:
					for key, value in result.items():
						try: callback(self.id(), key, value['status'] == 'finished')
						except: pass'''

		def cachedChunk(callback, links, timeout):
			try:
				premiumize = Core()
				result = premiumize._retrieve(category = Core.CategoryCache, action = Core.ActionCheck, caches = links, timeout = timeout)
				if premiumize.success():
					result = result['response']
					response = {}
					for i in range(len(result)):
						response[links[i]] = result[i]
					self.tCacheLock.acquire()
					self.tCacheResult.update(response)
					self.tCacheLock.release()
					if callback:
						for key, value in response.items():
							try: callback(self.id(), key, value)
							except: pass
			except:
				tools.Logger.error()

		threads = []
		for chunk in chunks:
			if hoster: thread = Pool.thread(target = cachedChunk, args = (callback, chunk, timeout))
			else: thread = Pool.thread(target = cachedChunk, args = (callback, chunk, timeout))
			threads.append(thread)
			thread.start()

		[i.join() for i in threads]
		if not callback:
			caches = []
			for key, value in self.tCacheResult.items():
				key = key.lower()
				caches.append({'id' : key, 'hash' : key, 'cached' : value})
			if single: return caches[0] if len(caches) > 0 else False
			else: return caches
