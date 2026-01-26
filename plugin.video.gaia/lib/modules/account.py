# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from lib.modules.tools import Settings, Time, Tools, System, Logger, Extension, File, Regex
from lib.modules.interface import Dialog, Loader, Format, Translation
from lib.modules.network import Networker, Geolocator
from lib.modules.concurrency import Pool

###################################################################
# AUTHENTICATION
###################################################################

class Account(object):

	ModeOauth				= 'oauth'			# OAuth
	ModeUsername			= 'username'		# Username & Password
	ModeEmail				= 'email'			# Email & Passsword
	ModeKey					= 'key'				# API Key
	ModePin					= 'pin'				# API Pin
	ModeCookie				= 'cookie'			# Cookie or session.
	ModeId					= 'id'				# Identifier or Username
	ModeExternal			= 'external'		# External Authentication

	AttributeToken			= 'token'			# OAuth access_token
	AttributeRefresh		= 'refresh'			# OAuth refresh-token
	AttributeCode			= 'code'			# OAuth user_code
	AttributeDevice			= 'device'			# OAuth device_code
	AttributeLink			= 'link'			# OAuth verification_url
	AttributeLinked			= 'linked'			# OAuth verification_url with the code added to the URL for quick QR scanning.
	AttributeExpiration		= 'expiration'		# OAuth expires_in
	AttributeInterval		= 'interval'		# OAuth interval
	AttributeLabel			= 'label'
	AttributeUsername		= 'username'
	AttributeEmail			= 'email'
	AttributePassword		= 'password'
	AttributeKey			= 'key'
	AttributePin			= 'pin'
	AttributeSecret			= 'secret'
	AttributeCookie			= 'cookie'
	AttributeId				= 'id'
	AttributeType			= 'type'
	AttributeVersion		= 'version'

	VerifyUnknown			= None
	VerifyValid				= 'valid'			# Account authenticated and verification succeeded.
	VerifyInvalid			= 'invalid'			# Account authenticated but verification failed.
	VerifyOptional			= 'optional'		# Account not authenticated, but the account is optional.
	VerifyDisabled			= 'disabled'		# Account not authenticated.
	VerifyCloudflare		= 'cloudflare'		# Account verification cannot get past Cloudflare protection.

	VerifyValues			= [VerifyValid, VerifyInvalid, VerifyCloudflare, VerifyOptional, VerifyDisabled, VerifyUnknown]
	VerifyLabels			= {VerifyValid : 33025, VerifyInvalid : 33023, VerifyCloudflare : 33024, VerifyOptional : 35323, VerifyDisabled : 33022, VerifyUnknown : 33387}
	VerifyColors			= {VerifyValid : 'colorExcellent', VerifyInvalid : 'colorBad', VerifyCloudflare : 'colorMedium', VerifyOptional : 'colorPoor', VerifyDisabled : 'colorAlternative', VerifyUnknown : 'colorSpecial'}

	SettingsAccount			= 'account'
	SettingsPremium			= 'premium'
	SettingsNetwork			= 'network'
	SettingsOracle			= 'oracle'
	SettingsEnabled			= 'enabled'
	SettingsAuthentication	= 'authentication'

	DefaultExpiration		= 900				# 15 minutes
	DefaultInterval			= 3					# 3 seconds
	DefaultCancel			= 0.5				# 500 milliseconds

	Data					= {}
	Instance				= {}

	# level: at which Kodi settings level the account should be visible.
	# rank: a value in [1,5] that shows how important the account is to the functionality of Gaia.
	def __init__(self,
		id,
		type = None,
		mode = None,

		name = None,
		description = None,

		free = None,
		optional = False,

		linkDirect = None,
		linkRedirect = None,

		level = None,
		rank = None,
		category = None,

		color = None,
		icon = None,
	):
		self.mId = id
		self.mType = type
		self.mMode = mode

		self.mName = Translation.string(name)
		self.mDescription = Translation.string(description)

		self.mFree = free
		self.mOptional = optional

		if linkDirect and not Networker.linkIs(linkDirect): linkDirect = Settings.getString(linkDirect, raw = True)
		if linkRedirect and not Networker.linkIs(linkRedirect): linkRedirect = Settings.getString(linkRedirect, raw = True)
		self.mLinkDirect = linkDirect if linkDirect else linkRedirect
		self.mLinkRedirect = linkRedirect if linkRedirect else linkDirect

		self.mLevel = level
		self.mRank = rank
		self.mCategory = Account.SettingsAccount if category is None else category

		self.mColor = color
		self.mIcon = icon if icon else {}
		if not 'icon' in self.mIcon: self.mIcon['icon'] = self.id()

		self.mIdentifier = self.mCategory + '_' + self.mId

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			Account.Data = {}
			Account.Instance = {}

	##############################################################################
	# INSTANCE
	##############################################################################

	@classmethod
	def instance(self, **parameters):
		instance = self.__name__
		if parameters: instance += '_' + str('_'.join(parameters.values()))
		if not instance in Account.Instance: Account.Instance[instance] = self(**parameters)
		return Account.Instance[instance]

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def headerBearer(self, token):
		return {'Authorization' : 'Bearer ' + token}

	def settings(self, enabled = True):
		id = Settings.idDataLabel(self.settingsIdAuthentication()) if (self.enabled() or not enabled) else self.settingsIdEnabled()
		Settings.launch(id)

	def settingsId(self, attribute):
		return '%s.%s.%s' % (self.mCategory, self.mId, attribute)

	def settingsIdEnabled(self):
		return self.settingsId(attribute = Account.SettingsEnabled)

	def settingsIdAuthentication(self):
		return self.settingsId(attribute = Account.SettingsAuthentication)

	def settingsVisible(self):
		return self.mLevel is None or self.mLevel <= Settings.level()

	def id(self):
		return self.mId

	def name(self):
		return self.mName

	def description(self):
		return self.mDescription

	def free(self):
		return self.mFree

	def optional(self):
		return self.mOptional

	def linkDirect(self):
		return self.mLinkDirect

	def linkRedirect(self):
		return self.mLinkRedirect

	def level(self):
		return self.mLevel

	def rank(self):
		return self.mRank

	def category(self):
		return self.mCategory

	def color(self):
		return self.mColor

	def icon(self):
		return self.mIcon

	def data(self):
		if not self.mIdentifier in Account.Data:
			if self.authenticated(): Account.Data[self.mIdentifier] = Settings.getData(id = self.settingsIdAuthentication())
			else: Account.Data[self.mIdentifier] = False
		data = Account.Data[self.mIdentifier]
		if data: return data
		else: return False

	def dataToken(self, default = None):
		try: return self.data()[Account.AttributeToken]
		except: return default

	def dataBearer(self, token = None, default = None):
		if not token: token = self.dataToken()
		if token: return self.headerBearer(token = token)
		return default

	def dataRefresh(self, default = None):
		try: return self.data()[Account.AttributeRefresh]
		except: return default

	def dataLabel(self, default = None):
		try: return self.data()[Account.AttributeLabel]
		except: return default

	def dataUsername(self, default = None):
		try: return self.data()[Account.AttributeUsername]
		except: return default

	def dataEmail(self, default = None):
		try: return self.data()[Account.AttributeEmail]
		except: return default

	def dataPassword(self, default = None):
		try: return self.data()[Account.AttributePassword]
		except: return default

	def dataKey(self, default = None):
		try: return self.data()[Account.AttributeKey]
		except: return default

	def dataPin(self, default = None):
		try: return self.data()[Account.AttributePin]
		except: return default

	def dataSecret(self, default = None):
		try: return self.data()[Account.AttributeSecret]
		except: return default

	def dataCookie(self, default = None):
		try: return self.data()[Account.AttributeCookie]
		except: return default

	def dataId(self, default = None):
		try: return self.data()[Account.AttributeId]
		except: return default

	def dataType(self, default = None):
		try: return self.data()[Account.AttributeType]
		except: return default

	def dataVersion(self, default = None):
		try: return self.data()[Account.AttributeVersion]
		except: return default

	def enabled(self):
		return Settings.getBoolean(id = self.settingsIdEnabled())

	def enable(self, enable = True):
		return Settings.set(id = self.settingsIdEnabled(), value = enable)

	def disable(self, disable = True):
		return self.enable(enable = not disable)

	def install(self, id, name = None, required = True, action = None, wait = None):
		return Extension.enable(id = id, name = name, confirm = Extension.ConfirmRequired if required else Extension.ConfirmOptional, notification = True, action = action, wait = wait)

	def installed(self, id, enabled = False):
		return Extension.installed(id = id, enabled = enabled)

	def authenticated(self):
		return self.enabled() and not Settings.defaultIs(id = self.settingsIdAuthentication())

	def clear(self):
		Settings.defaultData(id = self.settingsIdAuthentication())
		Settings.set(self.settingsIdEnabled(), False)
		Account.Data[self.mIdentifier] = None

	def update(self, token = None, refresh = None, label = None, username = None, email = None, password = None, key = None, pin = None, secret = None, cookie = None, id = None, type = None, version = None, data = None):
		if not data: data = self.data()
		if not token is None: data[Account.AttributeToken] = token
		if not refresh is None: data[Account.AttributeRefresh] = refresh
		if not label is None: data[Account.AttributeLabel] = label
		if not username is None: data[Account.AttributeUsername] = username
		if not email is None: data[Account.AttributeEmail] = email
		if not password is None: data[Account.AttributePassword] = password
		if not key is None: data[Account.AttributeKey] = key
		if not pin is None: data[Account.AttributePin] = pin
		if not secret is None: data[Account.AttributeSecret] = secret
		if not cookie is None: data[Account.AttributeCookie] = cookie
		if not id is None: data[Account.AttributeId] = id
		if not type is None: data[Account.AttributeType] = type
		if not version is None: data[Account.AttributeVersion] = version

		if data:
			label = None
			try: label = data[Account.AttributeLabel]
			except: pass
			if not label:
				try: label = data[Account.AttributeUsername]
				except: pass
				if not label:
					try: label = data[Account.AttributeEmail]
					except: pass
					if not label: label = Format.FontPassword
			data[Account.AttributeLabel] = label
			label = Format.fontBold(label)

			Account.Data[self.mIdentifier] = data
			Settings.set(id = self.settingsIdEnabled(), value = True)
			Settings.setData(id = self.settingsIdAuthentication(), value = data, label = label)
		else:
			self.clear()
		return data

	def register(self):
		link = self.linkRedirect()
		if link:
			Networker.linkShow(link = link)
			return None # Ask in settings.py if the account should be authenticated now.
		return False

	def verify(self):
		if self.authenticated():
			result = self._verify()
			if result is False: return Account.VerifyInvalid
			elif result == Account.VerifyCloudflare: return Account.VerifyCloudflare
			elif result: return Account.VerifyValid
			else: return Account.VerifyUnknown
		else:
			if self.optional(): return Account.VerifyOptional
			else: return Account.VerifyDisabled

	def _verify(self):
		return Account.VerifyUnknown

	@classmethod
	def verifyDialog(self):
		Loader.show()

		title = Translation.string(33017)
		message = Translation.string(33018)
		dots = ' '
		dialog = Dialog.progress(title = title, message = Format.fontBold(message + dots))

		indent = '   '
		labelAccount = Translation.string(33339)
		labelAccounts = Translation.string(32346)
		labelBusy = '%s%s%s: %s' % (Format.fontNewline(), indent, Translation.string(33291), '%d')
		separator = Format.iconSeparator(color = True, pad = True)
		labelFinished = '%s%s%s: %s [ %s%s%s%s%s ]' % (Format.fontNewline(), indent, Translation.string(35755), '%d', '%s', separator, '%s', separator, '%s')

		colors = {item : Tools.getFunction(Format, Account.VerifyColors[item])() for item in Account.VerifyValues}
		labels = {key : Translation.string(value) for key, value in Account.VerifyLabels.items()}

		result = []
		threads = []
		self.verifyAll(result = result, threads = threads, wait = False)
		total = float(len(threads))

		while True:
			if System.aborted():
				dialog.close()
				Loader.hide()
				return False
			elif dialog.iscanceled():
				break

			busy = len([thread for thread in threads if thread.is_alive()])
			if busy == 0: break
			progress = int(round(((total - busy) / total) * 100))

			stats = {type : 0 for type in Account.VerifyValues}
			for item in result:
				if item['verify'] in stats: stats[item['verify']] += 1

			valid = Format.font('%d%% %s' % (int(round((stats[Account.VerifyValid] / total) * 100)), labels[Account.VerifyValid]), color = colors[Account.VerifyValid])
			invalid = Format.font('%d%% %s' % (int(round((stats[Account.VerifyInvalid] / total) * 100)), labels[Account.VerifyInvalid]), color = colors[Account.VerifyInvalid])
			cloudflare = Format.font('%d%% %s' % (int(round((stats[Account.VerifyCloudflare] / total) * 100)), labels[Account.VerifyCloudflare]), color = colors[Account.VerifyCloudflare])
			optional = Format.font('%d%% %s' % (int(round((stats[Account.VerifyOptional] / total) * 100)), labels[Account.VerifyOptional]), color = colors[Account.VerifyOptional])
			disabled = Format.font('%d%% %s' % (int(round((stats[Account.VerifyDisabled] / total) * 100)), labels[Account.VerifyDisabled]), color = colors[Account.VerifyDisabled])

			extra = ''
			extra += labelBusy % busy
			extra += labelFinished % ((total - busy), valid, cloudflare, invalid)

			dots += '.'
			if len(dots) >= 5: dots = ' '

			dialog.update(progress, Format.fontBold(message + dots) + extra)
			Time.sleep(0.5)

		items = []
		for i in range(len(result)):
			verify = result[i]['verify']
			rank = (Account.VerifyValues.index(verify) * 100) + i
			items.append((rank, {
				'title' : result[i]['name'],
				'value' : Format.fontColor(labels[verify], color = colors[verify]),
				'color' : False,
			}))
		items.sort(key = lambda i : (i[0], i[1]['title'].lower()))
		items = [i[1] for i in items]

		stats = {type : 0 for type in Account.VerifyValues}
		for item in result:
			if item['verify'] in stats: stats[item['verify']] += 1

		summary = []
		total = float(len(result))
		for type in Account.VerifyValues:
			summary.append({
				'title' : Format.font(labels[type], bold = True, color = colors[type]),
				'value' : '%s (%d %s)' % (Format.font('%d%%' % int(round((stats[type] / total) * 100)) if total else 0, bold = True), stats[type], labelAccount if stats[type] == 1 else labelAccounts),
				'bold' : False,
				'color' : False,
			})

		items = [
			{'title' : Dialog.prefixBack(33486), 'close' : True, 'return' : 0},
			{'title' : 33690, 'items' : summary},
			{'title' : 32346, 'items' : items},
		]

		dialog.close()
		if items: Dialog.information(title = title, items = items, reselect = Dialog.ReselectYes)

		Loader.hide()
		return True

	@classmethod
	def verifyAll(self, result = [], threads = [], wait = True):
		Premium.prepare() # Otherwise there is a deadlock when calling Debrid._import() from different accounts in the threads.
		Opensubtitles.prepare() # Similar issue that there is a deadlock when importing "from xmlrpc.client import ServerProxy".

		accounts = [
			Youtube(),
			Fanart(),
			Trakt(),
			Imdb(),
			Tmdb(),
			Tvdb(),
			Opensubtitles(),
			Orion(),

			Premiumize(),
			Offcloud(),
			Realdebrid(),
			Easynews(),
			Debridlink(),
			Alldebrid(),
			Linksnappy(),
			Megadebrid(),
			Rapidpremium(),
			Simplydebrid(),
			Smoozed(),

			Geolocation(type = Geolocation.TypePrimary),
			Geolocation(type = Geolocation.TypeSecondary),
			Geolocation(type = Geolocation.TypeTertiary),

			Openai(),
			Bard(),
			Betterapi(),
		]

		for i in range(len(accounts)):
			account = accounts[i]
			result.append({'account' : account, 'name' : account.name(), 'verify' : Account.VerifyUnknown})
			threads.append(Pool.thread(target = self._verifyAll, kwargs = {'index' : i, 'result' : result}, start = True))
		if wait: [thread.join() for thread in threads]
		return result

	@classmethod
	def _verifyAll(self, index, result):
		result[index]['verify'] = result[index]['account'].verify()

	def authenticate(self,
		functionHelp = None,		# Function executed before everything else. Shows a help message that is important before the authentication process starts.
		functionNew = None,			# Function executed before the authentication begins if and only if no account was previously authenticated. Must return False if the process should be aborted.
		functionBefore = None,		# Function executed before the authentication begins. Must return False if the process should be aborted.
		functionAfter = None,		# Function executed after the authentication finishes.
		functionRevoke = None,		# Function executed after the authentication the user selected the revoke option.
		functionInitial = None,		# Function executed before the first step in the authentication process to show a help description.
		functionFinal = None,		# Function executed after the whole authentication process for a final message.

		functionUser = None,		# Function executed to before the user input dialog is shown (username/email).
		functionSecret = None,		# Function executed to before the secret input dialog is shown (password/key/pin) was entered.

		# Retrieves the authentication data externally, like from another addon.
		# If external data is returned by this function, the user will be asked if this data should be used, or new data be entered.
		functionExternal = None,

		# Retrieves the authentication data internally, like automatically generating a free API key.
		# If data is returned by this function, it will be used as default authentication data without asking the user for manual input.
		functionInternal = None,

		# Function executed to initiate the authentication proccess. Must return False on failures or a dictionary on success.
		# For OAuth: Return True or {AttributeLink : <required>, AttributeCode : <required>, AttributeDevice : <optional>, AttributeExpiration : <optional>, AttributeInterval : <optional>}.
		# For Basic: Return True/False/None.
		functionInitiate = None,

		# Function executed to check if the authentication was completed. Must return None on not completed yet, False on failures, or a dictionary on success.
		# For OAuth: Return False, None, or dictionary: {AttributeToken : <required>, AttributeRefresh : <optional>, AttributeUsername : <optional>, AttributeEmail : <optional>}.
		# For Basic: Return True, False, None, or dictionary {AttributeUsername : <optional>, AttributeEmail : <optional>}.
		functionVerify = None,

		# Shows a message dialog, similarly to the functions above.
		# Can be a string which will show a confirmation dialog.
		# Or can be a dictionary with optional parameters passed to the dialog: {'type' : Dialog.TypeNotification, 'message' : 'xyz', 'icon' : Dialog.IconError}
		messageNew = None,
		messageBefore = None,
		messageAfter = None,
		messageRevoke = None,
		messageVerify = None,
		messageInitial = None,
		messageFinal = None,
		messageUser = None,
		messageSecret = None,

		# Require an external addon to be installed for this account to work.
		# This only handles basic installation, if more advanced stuff must be done (eg: authenticate in the addon), the functionBefore/functionAfter should be used.
		# dependency: Single or list of {'id' : <addon id>, 'name' : <optional - addon name>, 'required' : <optional - addon required or not>, 'action' : <optional - actions to execute during installation>}
		dependency = None,

		settings = True,
	):
		def _authenticateReturn(result = None):
			self._authenticateMessage(messageAfter)
			if functionAfter: functionAfter(result)
			if settings: self.settings()
			return result

		if dependency:
			if not Tools.isArray(dependency): dependency = [dependency]
			for i in dependency:
				try: dependencyId = i['id']
				except: continue
				if not self.installed(id = dependencyId, enabled = True):
					try: dependencyName = i['name']
					except: dependencyName = None
					try: dependencyRequired = i['required']
					except: dependencyRequired = None
					try: dependencyAction = i['action']
					except: dependencyAction = None
					self.install(id = dependencyId, name = dependencyName, required = dependencyRequired, action = dependencyAction, wait = None)
					if not self.installed(id = dependencyId, enabled = True) and dependencyRequired: return False

		if functionHelp: functionHelp()

		if not self.authenticated():
			self._authenticateMessage(messageNew)
			if functionNew and functionNew() is False: return _authenticateReturn()

		self._authenticateMessage(messageBefore)
		if functionBefore and functionBefore() is False: return _authenticateReturn()

		if self.authenticated():
			choice = Dialog.options(title = self._authenticateTitle(), message = 32511, labelConfirm = 32512, labelDeny = 33743, labelCustom = 32513)
			if choice == Dialog.ChoiceCustom:
				self._authenticateMessage(messageRevoke)
				if functionRevoke and functionRevoke() is False: return _authenticateReturn()
				self.clear()
				Dialog.notification(title = self._authenticateTitle(), message = 32514, icon = Dialog.IconWarning, duplicates = True)
				return _authenticateReturn()
			elif not choice == Dialog.ChoiceYes:
				return _authenticateReturn()

		result = None
		authenticate = True
		if functionExternal:
			result = functionExternal()
			if result:
				choice = Dialog.options(title = self._authenticateTitle(), message = 35829, labelConfirm = 33743, labelDeny = 35675, labelCustom = 35447)
				if choice == Dialog.ChoiceNo:
					authenticate = False
					if functionVerify:
						Loader.show()
						data = functionVerify(result)
						Loader.hide()
						if data:
							if Tools.isDictionary(data): result.update(data)
						else:
							result = False
				elif not choice == Dialog.ChoiceCustom:
					return _authenticateReturn()

		if authenticate:
			self._authenticateMessage(messageInitial)
			if functionInitial and functionInitial() is False: return _authenticateReturn()

			default = None
			if functionInternal:
				internal = functionInternal()
				if internal:
					default = {}
					if Tools.isDictionary(internal):
						default.update(internal)
					else:
						if self.mMode == Account.ModeUsername: default[Account.AttributeUsername] = internal
						elif self.mMode == Account.ModeEmail: default[Account.AttributeEmail] = internal
						elif self.mMode == Account.ModeKey: default[Account.AttributeKey] = internal
						elif self.mMode == Account.ModePin: default[Account.AttributePin] = internal
						elif self.mMode == Account.ModeCookie: default[Account.AttributeCookie] = internal
						elif self.mMode == Account.ModeId: default[Account.AttributeId] = internal
						else: default = None

			if not result:
				if self.mMode == Account.ModeOauth: result = self._authenticateOauth(default = default, functionInitiate = functionInitiate, functionVerify = functionVerify)
				elif self.mMode == Account.ModeUsername: result = self._authenticateUsername(default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionUser = functionUser, functionSecret = functionSecret, messageVerify = messageVerify, messageUser = messageUser, messageSecret = messageSecret)
				elif self.mMode == Account.ModeEmail: result = self._authenticateEmail(default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionUser = functionUser, functionSecret = functionSecret, messageVerify = messageVerify, messageUser = messageUser, messageSecret = messageSecret)
				elif self.mMode == Account.ModeKey: result = self._authenticateKey(default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionSecret = functionSecret, messageUser = messageUser, messageVerify = messageVerify, messageSecret = messageSecret)
				elif self.mMode == Account.ModePin: result = self._authenticatePin(default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionSecret = functionSecret, messageUser = messageUser, messageVerify = messageVerify, messageSecret = messageSecret)
				elif self.mMode == Account.ModeCookie: result = self._authenticateCookie(default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionSecret = functionSecret, messageUser = messageUser, messageVerify = messageVerify, messageSecret = messageSecret)
				elif self.mMode == Account.ModeId: result = self._authenticateId(default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionSecret = functionSecret, messageUser = messageUser, messageVerify = messageVerify, messageSecret = messageSecret)

			self._authenticateMessage(messageFinal)
			if functionFinal and functionFinal() is False: return _authenticateReturn()

		if result:
			self.update(data = result)
			Dialog.notification(title = self._authenticateTitle(), message = 35462, icon = Dialog.IconSuccess, duplicates = True)
		elif result is False:
			Dialog.notification(title = self._authenticateTitle(), message = 33218, icon = Dialog.IconError, duplicates = True)

		return _authenticateReturn(result)

	def _authenticateTitle(self, title = 33101):
		result = ''
		if self.mName: result += self.mName + ' '
		result += Translation.string(title)
		return result

	def _authenticateMessage(self, message):
		if message:
			if Tools.isString(message) or Tools.isInteger(message):
				Dialog.confirm(title = self._authenticateTitle(), message = message)
			else:
				if not 'title' in message: message['title'] = self._authenticateTitle()
				if message['type'] == Dialog.TypeNotification: message['duplicates'] = True
				Dialog.show(**message)

	def _authenticateOauth(self, functionInitiate, functionVerify, parameters = None, default = None):
		try:
			Loader.show()
			dataInitiate = functionInitiate()
			if not dataInitiate:
				Loader.hide()
				return False

			try: expiration = dataInitiate[Account.AttributeExpiration]
			except: expiration = None
			if not expiration: expiration = Account.DefaultExpiration
			try: interval = dataInitiate[Account.AttributeInterval]
			except: interval = None
			if not interval: interval = Account.DefaultInterval
			link = dataInitiate[Account.AttributeLink]
			linked = dataInitiate.get(Account.AttributeLinked)
			code = dataInitiate[Account.AttributeCode]

			from lib.modules.window import WindowQr
			dialog = WindowQr.show(link = link, linked = linked, code = code, icon = self.icon(), color = self.color())

			dataCheck = None
			iterations1 = int(expiration / interval)
			iterations2 = int(interval / Account.DefaultCancel)
			for i in range(iterations1):
				canceled = False
				for j in range(iterations2): # Make cancel more responsive.
					if not dialog.visible():
						canceled = True
						break
					Time.sleep(Account.DefaultCancel)
				if canceled: break

				dataCheck = functionVerify(dataInitiate)
				if dataCheck or dataCheck is False: break # None is returned if still busy.
			try: dialog.close()
			except: pass

			return dataCheck
		except:
			Loader.hide()
			Logger.error()
			return False

	def _authenticateBasic(self, id = None, username = None, email = None, password = None, key = None, pin = None, cookie = None, default = None, functionInitiate = None, functionVerify = None, functionUser = None, functionSecret = None, messageVerify = None, messageUser = None, messageSecret = None):
		if functionInitiate and functionInitiate() is False: return None

		result = {}
		if id: result[Account.AttributeId] = self.dataId()
		if username: result[Account.AttributeUsername] = self.dataUsername()
		if email: result[Account.AttributeEmail] = self.dataEmail()
		if password: result[Account.AttributePassword] = self.dataPassword()
		if key: result[Account.AttributeKey] = self.dataKey()
		if pin: result[Account.AttributePin] = self.dataPin()
		if cookie: result[Account.AttributeCookie] = self.dataCookie()

		while True:
			if username or email or id:
				self._authenticateMessage(messageUser)
				if functionUser and functionUser() is False: return None
				if username:
					if default and Account.AttributeUsername in default: result[Account.AttributeUsername] = default[Account.AttributeUsername]
					else: result[Account.AttributeUsername] = Dialog.input(title = self._authenticateTitle(33267), type = Dialog.InputAlphabetic, default = result[Account.AttributeUsername] if Account.AttributeUsername in result else None)
					if not result[Account.AttributeUsername]: return None # Cancel
				elif email:
					if default and Account.AttributeEmail in default: result[Account.AttributeEmail] = default[Account.AttributeEmail]
					else: result[Account.AttributeEmail] = Dialog.input(title = self._authenticateTitle(32304), type = Dialog.InputAlphabetic, default = result[Account.AttributeEmail] if Account.AttributeEmail in result else None)
					if not result[Account.AttributeEmail]: return None # Cancel
				elif id:
					if default and Account.AttributeId in default: result[Account.AttributeId] = default[Account.AttributeId]
					else: result[Account.AttributeId] = Dialog.input(title = self._authenticateTitle(32305), type = Dialog.InputAlphabetic, default = result[Account.AttributeId] if Account.AttributeId in result else None)
					if not result[Account.AttributeId]: return None # Cancel
			if password or key or pin or cookie:
				self._authenticateMessage(messageSecret)
				if functionSecret and functionSecret() is False: return None
				if password:
					if default and Account.AttributePassword in default: result[Account.AttributePassword] = default[Account.AttributePassword]
					else: result[Account.AttributePassword] = Dialog.input(title = self._authenticateTitle(32307), type = Dialog.InputAlphabetic, default = result[Account.AttributePassword] if Account.AttributePassword in result else None)
					if not result[Account.AttributePassword]: return None # Cancel
				elif key:
					if default and Account.AttributeKey in default: result[Account.AttributeKey] = default[Account.AttributeKey]
					else: result[Account.AttributeKey] = Dialog.input(title = self._authenticateTitle(33100), type = Dialog.InputAlphabetic, default = result[Account.AttributeKey] if Account.AttributeKey in result else None)
					if not result[Account.AttributeKey]: return None # Cancel
				elif pin:
					if default and Account.AttributePin in default: result[Account.AttributePin] = default[Account.AttributePin]
					else: result[Account.AttributePin] = Dialog.input(title = self._authenticateTitle(33103), type = Dialog.InputAlphabetic, default = result[Account.AttributePin] if Account.AttributePin in result else None)
					if not result[Account.AttributePin]: return None # Cancel
				elif cookie:
					if default and Account.AttributeCookie in default: result[Account.AttributeCookie] = default[Account.AttributeCookie]
					else: result[Account.AttributeCookie] = Dialog.input(title = self._authenticateTitle(36354), type = Dialog.InputAlphabetic, default = result[Account.AttributeCookie] if Account.AttributeCookie in result else None)
					if not result[Account.AttributeCookie]: return None # Cancel

			failed = False
			if result:
				if not functionVerify: return result
				Loader.show()
				data = functionVerify(result)
				Loader.hide()
				if data:
					if Tools.isDictionary(data): result.update(data)
					return result
				else:
					failed = True
			Dialog.notification(title = self._authenticateTitle(), message = 33978, icon = Dialog.IconError, duplicates = True)
			if failed: self._authenticateMessage(messageVerify)

		return False

	def _authenticateUsername(self, default = None, functionVerify = None, functionUser = None, functionInitiate = None, functionSecret = None, messageVerify = None, messageUser = None, messageSecret = None):
		return self._authenticateBasic(username = True, default = default, password = True, functionInitiate = functionInitiate, functionVerify = functionVerify, functionUser = functionUser, functionSecret = functionSecret, messageVerify = messageVerify, messageUser = messageUser, messageSecret = messageSecret)

	def _authenticateEmail(self, default = None, functionUser = None, functionInitiate = None, functionVerify = None, functionSecret = None, messageVerify = None, messageUser = None, messageSecret = None):
		return self._authenticateBasic(email = True, default = default, password = True, functionInitiate = functionInitiate, functionVerify = functionVerify, functionUser = functionUser, functionSecret = functionSecret, messageVerify = messageVerify, messageUser = messageUser, messageSecret = messageSecret)

	def _authenticateKey(self, default = None, functionSecret = None, functionInitiate = None, functionVerify = None, messageUser = None, messageVerify = None, messageSecret = None):
		return self._authenticateBasic(key = True, default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionSecret = functionSecret, messageVerify = messageVerify, messageUser = messageUser, messageSecret = messageSecret)

	def _authenticatePin(self, default = None, functionSecret = None, functionInitiate = None, functionVerify = None, messageUser = None, messageVerify = None, messageSecret = None):
		return self._authenticateBasic(pin = True, default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionSecret = functionSecret, messageVerify = messageVerify, messageUser = messageUser, messageSecret = messageSecret)

	def _authenticateCookie(self, default = None, functionSecret = None, functionInitiate = None, functionVerify = None, messageUser = None, messageVerify = None, messageSecret = None):
		return self._authenticateBasic(cookie = True, default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionSecret = functionSecret, messageVerify = messageVerify, messageUser = messageUser, messageSecret = messageSecret)

	def _authenticateId(self, default = None, functionSecret = None, functionInitiate = None, functionVerify = None, messageUser = None, messageVerify = None, messageSecret = None):
		return self._authenticateBasic(id = True, default = default, functionInitiate = functionInitiate, functionVerify = functionVerify, functionSecret = functionSecret, messageVerify = messageVerify, messageUser = messageUser, messageSecret = messageSecret)

class Premium(Account):

	def __init__(self,
		id,
		mode = None,

		name = None,
		description = None,
		free = None,

		linkDirect = None,
		linkRedirect = None,

		level = None,
		rank = None,

		color = None,
		icon = None,
	):
		Account.__init__(self,
			id = id,
			mode = mode,

			name = name,
			description = description,
			free = free,

			linkDirect = linkDirect,
			linkRedirect = linkRedirect,

			level = level,
			rank = rank,
			category = Account.SettingsPremium,

			color = color,
			icon = icon,
		)

	@classmethod
	def help(self):
		from lib.debrid.debrid import Debrid
		Debrid.help()

	@classmethod
	def prepare(self):
		# Otherwise there is a deadlock when calling Debrid._import() from different accounts in the threads (eg: Account.verifyAll()).
		from lib.debrid import debrid

###################################################################
# YOUTUBE
###################################################################

class Youtube(Account):

	def __init__(self):
		from lib.modules.video import Video
		Account.__init__(self,
			id = 'youtube',
			mode = Account.ModeKey,

			name = 35296,
			description = 33988,

			linkDirect = Video.LinkRegister,
			linkRedirect = Video.LinkHelp,

			level = 1,
			rank = 4,
			color = 'FFFF0000',
		)

	@classmethod
	def agent(self):
		# Update (2024-11): Making requests to YouTube pages can now return an error page with: "Please update your browser ..."
		# Add a more recent user-agent to avoid these errors.
		return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'

	def _verify(self, data = None):
		from lib.modules.video import Video
		if data is None: data = self.dataKey()
		return Video().test(key = data)

	def authenticate(self, settings = True):
		from lib.modules.video import Video
		return Video().authentication(settings = settings)

	# This function called from video.py is necessary for the settings wizard.
	def _authenticate(self, messageNew = None, messageVerify = None, functionExternal = None, functionVerify = None, settings = True):
		# No account needs to be authenticated in the YouTube addon if it is only used to stream videos.
		# Hence, if the account is authenticated in Gaia, Gaia will use the API key to search. Then the ID is passed to the YouTube addon, which can play it without an account.
		dependency = {'id' : Extension.IdYouTube, 'required' : True}

		# Click "No" when YouTube addon asks to execute setup wizard.
		if not self.installed(id = dependency['id'], enabled = False):
			def cancelSetup():
				for i in range(500):
					if Dialog.dialogConfirmVisible():
						System.executeClick(control = System.ControlConfirmNo)
						break
					Time.sleep(0.01)
			dependency['action'] = cancelSetup

		return Account.authenticate(self, messageNew = messageNew, messageVerify = messageVerify, functionExternal = functionExternal, functionVerify = functionVerify, dependency = dependency, settings = settings)

###################################################################
# FANART
###################################################################

class Fanart(Account):

	Link = 'https://fanart.tv'
	LinkApi = 'https://fanart.tv/get-an-api-key/'

	def __init__(self):
		Account.__init__(self,
			id = 'fanart',
			mode = Account.ModeKey,

			name = 35260,
			description = 33934,

			optional = True,

			linkDirect = Fanart.Link,
			linkRedirect = 'internal.link.fanart',

			level = 2,
			rank = 2,
			color = 'FF21B6E1',
		)

	def client(self):
		return System.obfuscate(Settings.getString('internal.key.fanart', raw = True))

	def headers(self, key = None):
		# The Fanart API works with only an app key and without a user key.
		# However, the API returns fewer images without a key.
		# https://emby.media/community/index.php?/topic/66178-fanarttv-image-issues/
		# https://medium.com/fanart-tv/what-are-fanart-tv-personal-api-keys-472f60222856
		#	1. Without a user key: Only returns images older than 7 days.
		#	2. With a free user key: Only returns images older than 2 days.
		#	3. With a VIP user key: Returnss images older than 10 minutes.
		# Note that the key parameters are switched. api-key is the app key and client-key is the user key.
		headers = {'api-key' : self.client()}

		if not key: key = self.dataKey()
		if key: headers['client-key'] = key

		return headers

	def _verify(self, data = None):
		# Seems to be no way to verify the personal user key.
		if data is None: key = self.dataKey()
		else: key = data['key']
		networker = Networker()
		result = networker.requestJson(link = 'http://webservice.fanart.tv/v3/movies/tt0499549', headers = self.headers(key = key))
		if networker.responseErrorCloudflare(): return Account.VerifyCloudflare
		try: return 'imdb_id' in result
		except: return False

	def authenticate(self, settings = True):
		return Account.authenticate(self, functionVerify = self._verify, settings = settings, messageNew = {
			'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
				{'type' : 'text', 'value' : 'Authenticate with your Personal API key which can be generated on Fanart\'s website:'},
				{'type' : 'link', 'value' : Fanart.LinkApi},
			]})

###################################################################
# TRAKT
###################################################################

class Trakt(Account):

	Link = 'https://trakt.tv'

	def __init__(self):
		Account.__init__(self,
			id = 'trakt',
			mode = Account.ModeOauth,

			name = 32315,
			description = 33931,

			linkDirect = Trakt.Link,
			linkRedirect = 'internal.link.trakt',

			level = 0,
			rank = 5,
			color = 'FFAA39AE',
		)

	def _verify(self):
		from lib.modules import trakt
		return trakt.authenticationVerify()

	def authenticateExternal(self, result = True):
		# Trakt does the following:
		#	1. If the addon is not installed: After the addon has been newley installed, Trakt automatically shows the authentication dialog without closing other dialogs.
		#	2. If the addon is already installed: Kodi closes other dialogs when the authentication dialog shows.
		#	   2.1 If not authenticated yet: When disabling and re-enabling the addon, Trakt will automatically show the authentication dialog when enabled if no account exists.
		#	   2.2 If already authenticated: Trakt will not show the authentication dialog automatically and it has to be launched manually.
		# Trakt close all dialogs when authenticating.
		# This makes the wizard window close.
		# Disable the close and afterwards revert back to the original code.
		# Trakt handles all action in its service, meaning changing the code does not work, since services load the code at Kodi boot.
		# Disable and re-enable the addon to force the service to restart.
		try:
			if result and not self.authenticatedExternal() and Dialog.option(title = self._authenticateTitle(33848), message = 36238):
				if self.installed(id = 'script.trakt'):
					Pool.thread(target = self._authenticateExternalExecute, start = True, join = True) # Use a thread, otherwise the interface might freeze when enabling/disabling the addon.
				else:
					# Set "wait = None" to only wait for the native Kodi dialog.
					# During Trakt installation, the authentication dialog will popup if the no account was authenticated yet.
					# Ignore those dialogs, since they are already observed in _authenticateExternalStart().
					self.install(id = 'script.trakt', required = False, wait = None)
					if self._authenticateExternalStart(installation = True): self._authenticateExternalFinish()
					else: Pool.thread(target = self._authenticateExternalExecute, start = True, join = True) # Use a thread, otherwise the interface might freeze when enabling/disabling the addon.
		except: Logger.error()
		Loader.hide()

	def _authenticateExternalStart(self):
		from lib.modules.window import Window
		for i in range(100):
			if Window.currentTraktAuthentication():
				return True
				break
			Time.sleep(0.1)
		return False

	def _authenticateExternalFinish(self):
		from lib.modules.window import Window
		while True:
			if not Window.currentTraktAuthentication(): break
			Time.sleep(0.1)
		Loader.show()
		for i in range(20):
			if self.authenticatedExternal(): return True
			Time.sleep(0.1)
		return False

	def _authenticateExternalBusy(self):
		from lib.modules.window import Window
		return Window.currentTraktAuthentication()

	def _authenticateExternalEnable(self, wait = True, loader = True):
		System.executeJson(addon = 'script.trakt', method = 'Addons.SetAddonEnabled', parameters = {'enabled' : True})
		if loader: Loader.show()

		if wait:
			for i in range(50):
				if System.enabled(id = 'script.trakt') is True: break
				Time.sleep(0.1)

			# Wait a little bit for the addon the re-enable and the Trakt service to start.
			if loader: Loader.show()
			Time.sleep(2)

	def _authenticateExternalDisable(self, wait = True, loader = True):
		System.executeJson(addon = 'script.trakt', method = 'Addons.SetAddonEnabled', parameters = {'enabled' : False})
		if loader: Loader.show()

		if wait:
			for i in range(50):
				if System.enabled(id = 'script.trakt') is False: break
				Time.sleep(0.1)

			# When disabling the addon, sometimes the addon cannot stop, because a thread in Trakt's service script is still running.
			# This typically does not happen the first time this code is invoked after starting Kodi, but only on subsequent calls.
			# Eventually Kodi will: CPythonInvoker(23, /home/gaia/.kodi/addons/script.trakt/default.py): script didn't stop in 5 seconds - let's kill it
			# If the thread cannot be killed, sometimes Kodsi just freezes and needs a restart.
			# Waiting here seems to reduce the chances of this happening.
			if loader: Loader.show()
			Time.sleep(6)

	def _authenticateExternalReset(self, authenticated, path, data):
		Time.sleep(2)

		# Disable addon.
		# Only disable/re-enable the addon if the authentication was compelted, otherwise the authenticaation dialog will popup again when re-enabeling.
		if authenticated: self._authenticateExternalDisable(loader = False)

		# Revert code to original.
		if data: File.writeNow(path, data)
		Time.sleep(0.1)

		# Re-enable addon.
		if authenticated: self._authenticateExternalEnable(wait = False, loader = False)

	def _authenticateExternalExecute(self):
		Loader.show()

		# Disable addon.
		self._authenticateExternalDisable()

		# Change the code.
		Loader.show()
		path = File.joinPath(File.translate('special://home'), 'addons', 'script.trakt', 'resources', 'lib', 'service.py')
		fileOriginal = None
		if File.exists(path):
			fileOriginal = file = File.readNow(path)
			file = Regex.replace(data = file, expression = r'xbmc\.executebuiltin\([\'"]Dialog\.Close\(all.*?\)[\'"]\)', replacement = 'pass', all = True)
			File.writeNow(path, file)
		Time.sleep(0.1)

		# Re-enable addon.
		self._authenticateExternalEnable()

		# Authenticate
		if not self._authenticateExternalBusy():
			# Note that if no account was authenticated yet, and the Trakt addon is disabled and enabled, the authentication dialog pops up automatically.
			# Therefore do not execute the script, otherwise the dialog shows twice.
			System.executeScript(script = 'script.trakt', parameters = {'action' : 'auth_info'}, wait = True)
			Time.sleep(2)
		if not self._authenticateExternalStart():
			# When re-enabling the addon, it takes some time for its service to start.
			# The service is responsible for handling the "auth_info" command.
			# Retry twice before giving up.
			for i in range(2):
				System.executeScript(script = 'script.trakt', parameters = {'action' : 'auth_info'}, wait = True)
				Time.sleep(2)
				if self._authenticateExternalStart(): break
		self._authenticateExternalFinish()
		authenticated = self.authenticatedExternal()

		# Revert code to original.
		if fileOriginal: Pool.thread(target = self._authenticateExternalReset, kwargs = {'authenticated' : authenticated, 'path' : path, 'data' : fileOriginal}, start = True)

	def authenticatedExternal(self):
		addon = System.addon(id = 'script.trakt')
		if not addon: return False
		authorization = addon.getSetting('authorization')
		return bool(authorization and len(authorization) > 3)

	def authenticate(self, settings = True):
		from lib.modules import trakt
		return trakt.authentication(settings = settings)

	# This function called from trakt.py is necessary for the settings wizard.
	def _authenticate(self, functionInitiate = None, functionVerify = None, settings = True):
		# Do not authneticate the external addon anymore, since we now handle ratings locally.
		#return Account.authenticate(self, functionInitiate = functionInitiate, functionVerify = functionVerify, functionAfter = self.authenticateExternal, settings = settings)
		return Account.authenticate(self, functionInitiate = functionInitiate, functionVerify = functionVerify, settings = settings)

###################################################################
# IMDB
###################################################################

class Imdb(Account):

	Link		= 'https://imdb.com'
	LinkLogin	= 'https://imdb.com/login'
	LinkUser	= 'https://imdb.com/user'

	def __init__(self):
		Account.__init__(self,
			id = 'imdb',
			mode = Account.ModeId,

			name = 32034,
			description = 33910,

			linkDirect = Imdb.Link,
			linkRedirect = 'internal.link.imdb',

			level = 1,
			rank = 2,
			color = 'FFF6C700',
		)

	def _verify(self, data = None):
		from lib.modules.tools import Regex

		if data is None:
			data = {}
			id = self.dataId()
		else:
			id = data[Account.AttributeId]
		id = id.lower()
		if not id.startswith('ur'): id = 'ur' + id
		data[Account.AttributeId] = id

		networker = Networker()
		result = networker.requestText(link = Networker.linkJoin(Imdb.LinkUser, id))
		if networker.responseErrorCloudflare():
			return Account.VerifyCloudflare
		elif networker.responseSuccess() and result:
			username = Regex.extract(data = result, expression = r'<title>(.*?)\'?s?\s*profile.*?<\/title>')
			if username:
				data[Account.AttributeUsername] = username
				return data
			return True
		return False

	def authenticate(self, settings = True):
		return Account.authenticate(self, functionVerify = self._verify, settings = settings, messageNew = {'type' : Dialog.TypeDetails, 'items' : [
			{'type' : 'text', 'value' : 'Authenticate IMDb with your user ID which can be found on IMDb\'s website.'},
			{'type' : 'link', 'value' : Imdb.LinkLogin},
			{'type' : 'list', 'number' : True, 'value' : [
				{'title' : 'Account Login', 'value' : 'Log into IMDb\'s website with your account.'},
				{'title' : 'Show Lists', 'value' : 'Open the menu under your username in the top right corner and navigate to [I]Your lists[/I].'},
				{'title' : 'Retrieve ID', 'value' : 'Your ID will show in the URL bar of your browser. The ID starts with the letters [I]ur[/I]  followed by digits.'},
			]},
			{'type' : 'text', 'value' : 'IMDb user lists are [I]private[/I]  by default. Lists you want to use in Gaia must be changed to [I]public[/I].'},
			{'type' : 'list', 'number' : True, 'value' : [
				{'title' : 'Show List', 'value' : 'Open the menu under your username in the top right corner and navigate to [I]Your lists[/I].'},
				{'title' : 'Open List', 'value' : 'Open the list of your choice. Besides your custom lists, your checkins and watchlist can also be accessed from the links under the heading.'},
				{'title' : 'Edit List', 'value' : 'Select the [I]Edit[/I]  option from the list\'s top right menu and then click the [I]Settings[/I] link.'},
				{'title' : 'Change Privacy', 'value' : 'Change the [I]Privacy[/I]  option to [I]Public[/I]. Click the [I]Save[/I]  button.'},
			]},
		]})

###################################################################
# TMDB
###################################################################

class Tmdb(Account):

	Link		= 'https://themoviedb.org'
	LinkApi		= 'https://www.themoviedb.org/settings/api'
	LinkVerify	= 'https://api.themoviedb.org/3/configuration?api_key='

	def __init__(self):
		Account.__init__(self,
			id = 'tmdb',
			mode = Account.ModeKey,

			name = 33508,
			description = 33933,

			optional = True,

			linkDirect = Tmdb.Link,
			linkRedirect = 'internal.link.tmdb',

			level = 3,
			rank = 1,
			color = 'FF44C0C5',
		)

	def key(self):
		default = System.obfuscate(Settings.getString('internal.key.tmdb', raw = True))
		return self.dataKey(default)

	def _verify(self, data = None):
		if data is None: key = self.dataKey()
		else: key = data[Account.AttributeKey]
		networker = Networker()
		result = networker.requestJson(link = Tmdb.LinkVerify + key)
		if networker.responseErrorCloudflare(): return Account.VerifyCloudflare
		return bool(result and (not 'success' in result or result['success']))

	def authenticate(self, settings = True):
		messageNew = {'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
			{'type' : 'text', 'value' : 'TMDb does not require user authentication and instead the addon will handle its own internal authentication. You will therefore not lose any addon functionality if you do not authenticate your own account. If you, however, still want to use your own custom API key, you can register a new development project on TMDb\'s website and generate a new API key for it:'},
			{'type' : 'link', 'value' : Tmdb.LinkApi},
		]}
		return Account.authenticate(self, functionVerify = self._verify, settings = settings, messageNew = messageNew)

###################################################################
# TVDB
###################################################################

class Tvdb(Account):

	Link			= 'https://themoviedb.org'
	LinkSubscribe	= 'https://thetvdb.com/subscribe'

	def __init__(self):
		Account.__init__(self,
			id = 'tvdb',
			mode = Account.ModePin,

			name = 35668,
			description = 33946,

			optional = True,

			linkDirect = Tvdb.Link,
			linkRedirect = 'internal.link.tvdb',

			level = 3,
			rank = 1,
			color = 'FF1C7E3E',
		)

	def key(self):
		return System.obfuscate(Settings.getString('internal.key.tvdb', raw = True))

	def pin(self):
		return self.dataPin()

	def _verify(self, data = None):
		from lib.meta.providers.tvdb import MetaTvdb
		if data is None: pin = self.dataPin()
		else: pin = data[Account.AttributePin]
		return MetaTvdb.authenticationVerify(pin = pin)

	def authenticate(self, settings = True):
		messageNew = {'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
			{'type' : 'text', 'value' : 'TVDb does not require user authentication and instead the addon will handle its own internal authentication. You will therefore not lose any addon functionality if you do not authenticate your own account. If you, however, still want to use your own custom API pin, you can subscribe on TVDb\'s website to generate a new pin:'},
			{'type' : 'link', 'value' : Tvdb.LinkSubscribe},
		]}
		return Account.authenticate(self, functionVerify = self._verify, settings = settings, messageNew = messageNew)

###################################################################
# OPENSUBTITLES
###################################################################

class Opensubtitles(Account):

	Link = 'https://opensubtitles.com'

	def __init__(self):
		Account.__init__(self,
			id = 'opensubtitles',
			mode = Account.ModeUsername,

			name = 35683,
			description = 33987,

			linkDirect = Opensubtitles.Link,
			linkRedirect = 'internal.link.opensubtitles',

			level = 1,
			rank = 3,
			color = 'FF231F20',
		)

	@classmethod
	def key(self):
		return System.obfuscate(Settings.getString('internal.key.opensubtitles', raw = True))

	@classmethod
	def prepare(self):
		# When using Opensubtitles in a thread (eg: Account.verifyAll()), the import:
		#	from xmlrpc.client import ServerProxy
		# in Subtitle._connection() can cause a deadlock.
		# When importing outside a thread first, the deadlock is gone.
		# Update: The new OpenSubtitles does not use xmlrpc anymore.
		#from lib.modules.subtitle import Subtitle
		#Subtitle.prepare()
		pass

	def _verify(self, data = None):
		from lib.modules.subtitle import Subtitle
		if data is None:
			username = self.dataUsername()
			password = self.dataPassword()
		else:
			username = data[Account.AttributeUsername]
			password = data[Account.AttributePassword]
		return Subtitle.verify(username = username, password = password)

	def authenticate(self, settings = True):
		# NB: When a password containing a hash "#" was used, authentication failed. When the hash was removed, authentication succeeded.
		return Account.authenticate(self, functionVerify = self._verify, settings = settings, messageNew = {
			'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
				{'type' : 'text', 'value' : 'Authenticate with your OpenSubtitles username and password:'},
				{'type' : 'link', 'value' : Opensubtitles.Link},
			]})

###################################################################
# GEOLOCATION
###################################################################

class Geolocation(Account):

	TypePrimary		= 'primary'
	TypeSecondary	= 'secondary'
	TypeTertiary 	= 'tertiary'

	Services	= {
		1 : {
			'name' : 36148,
			'service' : Geolocator.ServiceIpgeolocationio,
			'link' : 'https://ipgeolocation.io',
			'limit' : {
				'month' : 30000,
				'day' : 1000,
			},
		},
		2 : {
			'name' : 36149,
			'service' : Geolocator.ServiceGeoapifycom,
			'link' : 'https://geoapify.com',
			'limit' : {
				'day' : 3000,
				'second' : 5,
			},
		},
		3 : {
			'name' : 36150,
			'service' : Geolocator.ServiceIpinfodbcom,
			'link' : 'https://ipinfodb.com',
			'limit' : {
				'second' : 2,
			},
		},
		4 : {
			'name' : 36151,
			'service' : Geolocator.ServiceIpdataco,
			'link' : 'https://ipdata.co',
			'limit' : {
				'day' : 1500,
			},
		},
		5 : {
			'name' : 36152,
			'service' : Geolocator.ServiceBigdatacloudnet,
			'link' : 'https://bigdatacloud.net',
			'limit' : {
				'month' : 10000,
			},
		},
		6 : {
			'name' : 36153,
			'service' : Geolocator.ServiceIpapicom,
			'link' : 'http://ipapi.com',
			'limit' : {
				'month' : 1000,
			},
		},
		7 : {
			'name' : 36154,
			'service' : Geolocator.ServiceIpstackcom,
			'link' : 'http://ipstack.com',
			'limit' : {
				'month' : 100,
			},
		},
	}

	def __init__(self, type):
		try:
			self.mService = Geolocation.Services[Settings.getInteger(self.settingsId(category = Account.SettingsNetwork, id = type))]
			name = self.mService['name']
			linkDirect = self.mService['link']
			linkRedirect = 'internal.link.' + self.mService['service']
		except:
			self.mService = None
			name = None
			linkDirect = None
			linkRedirect = None

		self.mNameGeneric = '%s (%s)' % (Translation.string(33936), Translation.string(35486 if type == Geolocation.TypePrimary else 35487 if type == Geolocation.TypeSecondary else 35334))

		Account.__init__(self,
			id = type,
			mode = Account.ModeKey,

			name = name,
			description = 33968,

			optional = True,

			linkDirect = linkDirect,
			linkRedirect = linkRedirect,

			level = 2,
			rank = 1,
			category = Account.SettingsNetwork,
			color = 'FFFF8A00',
		)

	def settingsId(self, category = None, id = None, attribute = None):
		setting = '%s.geolocation.%s' % (category if category else self.mCategory, id if id else self.mId)
		if attribute: setting += '.' + attribute
		return setting

	def settingsIdEnabled(self):
		return self.settingsId()

	def name(self, generic = True):
		if generic: return self.mNameGeneric
		else: return Account.name(self)

	def enabled(self):
		return Settings.getInteger(id = self.settingsIdEnabled()) > 0

	def _verify(self, data = None):
		if data is None:
			data = {}
			key = self.dataKey()
		else:
			key = data['key']
		result = Geolocator.detectGlobal(service = self.mService['service'], key = key)
		if Geolocator.dataValid(result):
			data[Account.AttributeType] = self.mService['service'] # Always include the service type, so that if the users changes the "type" in the spin-list in the settings without reauthenticating, the actual type will still be retrieved from the database.
			return data
		return False

	def authenticate(self, settings = True):
		from lib.modules.tools import Math

		limit = []
		if 'month' in self.mService['limit']: limit.append('%s requests per month' % Math.thousand(self.mService['limit']['month']))
		if 'day' in self.mService['limit']: limit.append('%s requests per day' % Math.thousand(self.mService['limit']['day']))
		if 'minute' in self.mService['limit']: limit.append('%s requests per minute' % Math.thousand(self.mService['limit']['minute']))
		if 'second' in self.mService['limit']: limit.append('%s requests per second' % Math.thousand(self.mService['limit']['second']))

		count = len(limit)
		concatenate = Translation.string(33872).lower()
		if count == 1: limit = limit[0]
		elif count == 2: limit = '%s %s %s' % (limit[0], concatenate, limit[1])
		elif count == 3: limit = ', '.join([limit[0], limit[1], '%s %s' % (concatenate, limit[2])])
		elif count == 4: limit = ', '.join([limit[0], limit[1], limit[2], '%s %s' % (concatenate, limit[3])])

		messageNew = {'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
			{'type' : 'text', 'value' : '%s is a public IP and geolocation lookup service. Free and paid accounts are available. Free accounts have limits of %s. A custom lookup service is only necessary if you use the [I]Generic[/I]  VPN detection feature, which continuously checks the public IP address to determine if the VPN is connected or not. If you do not use the VPN detection, you do not have to authenticate a personal account and instead rely on free internal services.' % (self.name(), limit)},
			{'type' : 'link', 'value' : self.linkDirect()},
		]}

		return Account.authenticate(self, functionVerify = self._verify, settings = settings, messageNew = messageNew)

###################################################################
# ORION
###################################################################

class Orion(Account):

	def __init__(self):
		from lib.modules.orionoid import Orionoid
		try: linkDirect = Orionoid().link()
		except: linkDirect = 'https://orionoid.com' # Addon disabled.

		Account.__init__(self,
			id = 'orion',
			mode = Account.ModeKey,

			name = 35400,
			description = 35408,
			free = True,

			linkDirect = linkDirect,
			linkRedirect = 'internal.link.orion',

			level = 0,
			rank = 5,
			category = Account.SettingsPremium,
			color = 'FF47CAE9',
		)

	def register(self):
		from lib.modules.orionoid import Orionoid
		Orionoid().accountPromotion(background = False) # Do not run in background, otherwise the account status in Gaia's settings wizard is not updated with the new value after Orion's dialogs close.
		return True # New account already authenticated.

	def _verify(self):
		from lib.modules.orionoid import Orionoid
		return Orionoid().accountVerify()

	def authenticate(self, settings = True):
		from lib.modules.orionoid import Orionoid

		if not self.installed(id = Orionoid.Id, enabled = True):
			self.install(id = Orionoid.Id, required = True)
			if not self.installed(id = Orionoid.Id): return False

		try:
			from lib.modules.orionoid import Orionoid
			Orionoid().accountAuthenticate(settings = settings, background = False) # Do not run in background, otherwise the account status in Gaia's settings wizard is not updated with the new value after Orion's dialogs close.
		except AttributeError:
			# The Orion addon can be disabled, even if it is a required dependency.
			# When the addon is enabled, the Orion module can be still not imported, since the Python Invoker still hass the old status.
			# Launch in a separate process and wait for the process to finish.

			Time.sleep(0.1)
			System.executePlugin(action = 'orionAuthenticate')
			Time.sleep(2)
			Orionoid.accountAuthenticateWait()

			# Settings need some time to be updated.
			Loader.show()
			for i in range(50):
				Settings.cacheClear()
				Time.sleep(0.1)
				if self.authenticated(): break
			Loader.hide()

		# Clear the cache, to retrieve the new authentication status that might have been written by another process (including revoking the authentication).
		Settings.cacheClear()
		return self.authenticated()

###################################################################
# PREMIUMIZE
###################################################################

class Premiumize(Premium):

	Link		= 'https://premiumize.me'
	#LinkFree	= 'https://premiumize.me/free' # Does not exist anymore.

	def __init__(self):
		Premium.__init__(self,
			id = 'premiumize',
			mode = Premium.ModeOauth,

			name = 33566,
			description = 33939,

			linkDirect = Premiumize.Link,
			linkRedirect = 'internal.link.premiumize',

			level = 0,
			rank = 4,

			color = 'FFB51E03',
			icon = {'small' : True},
		)

	def _verify(self):
		from lib.debrid.premiumize import Core
		return Core().accountVerify()

	def authenticate(self, help = True, settings = True):
		from lib.debrid.premiumize import Interface
		Interface().accountAuthentication(help = help, settings = settings)

	def _authenticate(self, functionInitiate, functionVerify, help = True, settings = True):
		'''return Premium.authenticate(self, functionInitiate = functionInitiate, functionVerify = functionVerify, functionHelp = self.help if help else None, settings = settings, messageNew = {
			'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
				{'type' : 'text', 'value' : 'Premiumize offers paid and free accounts. Paid accounts are fast and unlimited. Free accounts are restricted and must be activated manually at:'},
				{'type' : 'link', 'value' : Premiumize.LinkFree},
			]})'''
		return Premium.authenticate(self, functionInitiate = functionInitiate, functionVerify = functionVerify, functionHelp = self.help if help else None, settings = settings)

###################################################################
# OFFCLOUD
###################################################################

class Offcloud(Premium):

	Link	= 'https://offcloud.com'
	LinkApi	= 'https://offcloud.com/#/account'

	def __init__(self):
		Premium.__init__(self,
			id = 'offcloud',
			mode = Premium.ModeKey,

			name = 35200,
			description = 35262,

			linkDirect = Offcloud.Link,
			linkRedirect = 'internal.link.offcloud',

			level = 0,
			rank = 4,
			color = 'FF009AFF',
		)

	def _verify(self):
		from lib.debrid.offcloud import Core
		return Core().accountVerify()

	def authenticate(self, help = True, settings = True):
		from lib.debrid.offcloud import Interface
		Interface().accountAuthentication(help = help, settings = settings)

	def _authenticate(self, functionVerify, help = True, settings = True):
		return Premium.authenticate(self, functionVerify = functionVerify, functionHelp = self.help if help else None, settings = settings, messageNew = {
			'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
				{'type' : 'text', 'value' : 'Authenticate with your API key which can be found on OffCloud\'s website under the Account tab:'},
				{'type' : 'link', 'value' : Offcloud.LinkApi},
			]})

###################################################################
# REALDEBRID
###################################################################

class Realdebrid(Premium):

	Link = 'https://real-debrid.com'

	def __init__(self):
		Premium.__init__(self,
			id = 'realdebrid',
			mode = Premium.ModeOauth,

			name = 33567,
			description = 33945,

			linkDirect = Realdebrid.Link,
			linkRedirect = 'internal.link.realdebrid',

			level = 0,
			rank = 3,
			color = 'FFB8D995',
		)

	def _verify(self):
		from lib.debrid.realdebrid import Core
		return Core().accountVerify()

	def authenticate(self, help = True, settings = True):
		from lib.debrid.realdebrid import Interface
		Interface().accountAuthentication(help = help, settings = settings)

	def _authenticate(self, functionInitiate, functionVerify, help = True, settings = True):
		return Premium.authenticate(self, functionInitiate = functionInitiate, functionVerify = functionVerify, functionHelp = self.help if help else None, settings = settings)

###################################################################
# EASYNEWS
###################################################################

class Easynews(Premium):

	Link		= 'https://easynews.com'
	LinkLogin	= 'https://members.easynews.com/login'

	def __init__(self):
		Premium.__init__(self,
			id = 'easynews',
			mode = Premium.ModeUsername,

			name = 33794,
			description = 33948,

			linkDirect = Easynews.Link,
			linkRedirect = 'internal.link.easynews',

			level = 0,
			rank = 3,
			color = 'FF3C6CDE',
		)

	def _verify(self):
		from lib.debrid.easynews import Core
		return Core().accountVerify()

	def authenticate(self, help = True, settings = True):
		from lib.debrid.easynews import Interface
		Interface().accountAuthentication(help = help, settings = settings)

	def _authenticate(self, functionVerify, help = True, settings = True):
		return Premium.authenticate(self, functionVerify = functionVerify, functionHelp = self.help if help else None, settings = settings, messageNew = {
			'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
				{'type' : 'text', 'value' : 'Authenticate with your EasyNews username and password:'},
				{'type' : 'link', 'value' : Easynews.LinkLogin},
			]})

###################################################################
# RESOLVER
###################################################################

class Resolver(Premium):

	def __init__(self, id, name, description = None, rank = 2, color = None):
		Premium.__init__(self,
			id = id,
			mode = Account.ModeExternal,

			name = name,
			description = description,

			level = 0,
			rank = rank,
			color = color,
		)

	def enabled(self):
		return installed

	def _verify(self):
		from lib.modules.tools import Resolver as Resolvery
		return Resolvery().verification(type = self.id())

	def authenticated(self):
		from lib.modules.tools import Resolver as Resolvery
		return Resolvery.authenticated(type = self.id())

	def authenticate(self, help = True, settings = True):
		from lib.modules.tools import Resolver as Resolvery
		Resolvery.authentication(type = self.id(), direct = True, help = help, settings = settings)

###################################################################
# DEBRIDLINK
###################################################################

class Debridlink(Resolver):

	def __init__(self):
		Resolver.__init__(self,
			id = 'debridlink',
			name = 'DebridLink',
			rank = 2,
			color = 'FF264E70',
		)

###################################################################
# ALLDEBRID
###################################################################

class Alldebrid(Resolver):

	def __init__(self):
		Resolver.__init__(self,
			id = 'alldebrid',
			name = 'AllDebrid',
			rank = 2,
			color = 'FFFCC933',
		)

###################################################################
# LINKSNAPPY
###################################################################

class Linksnappy(Resolver):

	def __init__(self):
		Resolver.__init__(self,
			id = 'linksnappy',
			name = 'LinkSnappy',
			rank = 1,
			color = 'FF343434',
		)

###################################################################
# MEGADEBRID
###################################################################

class Megadebrid(Resolver):

	def __init__(self):
		Resolver.__init__(self,
			id = 'megadebrid',
			name = 'MegaDebrid',
			rank = 1,
			color = 'FF232323',
		)

###################################################################
# RAPIDPREMIUM
###################################################################

class Rapidpremium(Resolver):

	def __init__(self):
		Resolver.__init__(self,
			id = 'rapidpremium',
			name = 'RapidPremium',
			rank = 1,
			color = 'FF222C3C',
		)

###################################################################
# SIMPLYDEBRID
###################################################################

class Simplydebrid(Resolver):

	def __init__(self):
		Resolver.__init__(self,
			id = 'simplydebrid',
			name = 'SimplyDebrid',
			rank = 1,
			color = 'FF00ACC1',
		)

###################################################################
# SMOOZED
###################################################################

class Smoozed(Resolver):

	def __init__(self):
		Resolver.__init__(self,
			id = 'smoozed',
			name = 'Smoozed',
			rank = 1,
			color = 'FFDD1F1F',
		)

###################################################################
# TORBOX
###################################################################

class Torbox(Resolver):

	def __init__(self):
		Resolver.__init__(self,
			id = 'torbox',
			name = 'TorBox',
			rank = 3,
			color = 'FF04BF8A',
		)

###################################################################
# DEBRIDER
###################################################################

class Debrider(Premium):

	Link	= 'https://debrider.app'

	def __init__(self):
		Premium.__init__(self,
			id = 'debrider',
			mode = Premium.ModeKey,

			name = 36833,

			linkDirect = Debrider.Link,

			level = 0,
			rank = 3,

			color = 'FFFFDF41',
			icon = {'small' : True},
		)

	def _default(self):
		return Translation.string(33216)

	def _label(self):
		return Settings.idDataLabel(self.settingsIdAuthentication())

	def settings(self, enabled = False):
		return Premium.settings(self, enabled = enabled) # False by default, since the value was not updated yet.

	def enabled(self):
		return Settings.getString(id = self._label()) == self._default()

	def _verify(self, data = None):
		from lib.debrid.external import Debrider
		if Debrider.accountVerify(data = data): return {Account.AttributeLabel : self._default()}
		return False

	def _authenticate(self):
		Dialog.confirm(title = self.name(), message = 'Debrider is currently only supported through Orion. In order to stream, you also have to authenticate your Debrider account on Orion\'s website.')
		if not Orion().authenticated(): return False
		self._authenticateMessage({
			'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
				{'type' : 'text', 'value' : 'Authenticate with your API key which can be found on Debrider\'s website after you subscribed:'},
				{'type' : 'link', 'value' : Debrider.Link},
			]})

	def authenticate(self, help = True, settings = True):
		Premium.authenticate(self, functionNew = self._authenticate, functionVerify = self._verify, functionHelp = self.help if help else None, settings = settings)

	def update(self, token = None, refresh = None, label = None, username = None, email = None, password = None, key = None, pin = None, secret = None, cookie = None, id = None, type = None, version = None, data = None):
		data = Premium.update(self, token = token, refresh = refresh, label = label, username = username, email = email, password = password, key = key, pin = pin, secret = secret, cookie = cookie, id = id, type = type, version = version, data = data)
		if data:
			label = data[Account.AttributeLabel]
			Settings.set(id = self._label(), value = label)
		return data

###################################################################
# EASYDEBRID
###################################################################

class Easydebrid(Premium):

	Link	= 'https://paradise-cloud.com'

	def __init__(self):
		Premium.__init__(self,
			id = 'easydebrid',
			mode = Premium.ModeKey,

			name = 36024,

			linkDirect = Easydebrid.Link,

			level = 0,
			rank = 3,

			color = 'FF3B82F6',
			icon = {'small' : True},
		)

	def _default(self):
		return Translation.string(33216)

	def _label(self):
		return Settings.idDataLabel(self.settingsIdAuthentication())

	def settings(self, enabled = False):
		return Premium.settings(self, enabled = enabled) # False by default, since the value was not updated yet.

	def enabled(self):
		return Settings.getString(id = self._label()) == self._default()

	def _verify(self, data = None):
		from lib.debrid.external import Easydebrid
		if Easydebrid.accountVerify(data = data): return {Account.AttributeLabel : self._default()}
		return False

	def _authenticate(self):
		Dialog.confirm(title = self.name(), message = 'EasyDebrid is currently only supported through Orion. In order to stream, you also have to authenticate your EasyDebrid account on Orion\'s website.')
		if not Orion().authenticated(): return False
		self._authenticateMessage({
			'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
				{'type' : 'text', 'value' : 'Authenticate with your API key which can be found on EasyDebrid\'s website after you subscribed:'},
				{'type' : 'link', 'value' : Easydebrid.Link},
			]})

	def authenticate(self, help = True, settings = True):
		Premium.authenticate(self, functionNew = self._authenticate, functionVerify = self._verify, functionHelp = self.help if help else None, settings = settings)

	def update(self, token = None, refresh = None, label = None, username = None, email = None, password = None, key = None, pin = None, secret = None, cookie = None, id = None, type = None, version = None, data = None):
		data = Premium.update(self, token = token, refresh = refresh, label = label, username = username, email = email, password = password, key = key, pin = pin, secret = secret, cookie = cookie, id = id, type = type, version = version, data = data)
		if data:
			label = data[Account.AttributeLabel]
			Settings.set(id = self._label(), value = label)
		return data

###################################################################
# OPENAI
###################################################################

class Openai(Account):

	def __init__(self):
		from lib.oracle.chatgpt import Chatgpt
		self.mOracle = Chatgpt.instance()

		Account.__init__(self,
			#id = 'openai',
			id = self.mOracle.id(), # To set the correct value in settings.xml.
			mode = Premium.ModeKey,

			name = self.mOracle.organization(),
			description = self.mOracle.helpDescription(),
			free = True,
			optional = True,

			linkDirect = self.mOracle.linkAccount(),
			linkRedirect = self.mOracle.linkRedirect(),

			level = 1,
			rank = 5,
			category = Account.SettingsOracle,
			color = self.mOracle.color(),
		)

	def help(self):
		self.mOracle.helpAuthentication()

	def _verify(self, data = None):
		if data is None: key = self.dataKey()
		else: key = data['key']

		valid = self.mOracle.accountVerification(key = key)

		# NB: Enable the playground if an account was successfully authenticated.
		# Serves as a fallback if the OpenAI account reaches its limits or in some other way does not work (eg: OpenAI servers currently overloaded).
		# Only do this if the setting is disabled (default) and not if the user already changed the setting.
		if key and valid and self.mOracle.settingsPlaygroundDisabled(): self.mOracle.settingsPlaygroundEnable()

		return valid

	def _select(self):
		if self.mOracle.settingsPlaygroundDisabled() or not self.authenticated():
			choice = Dialog.options(title = self._authenticateTitle(), message = 'Do you want to use a [B]free[/B] account with limited capabilities or authenticate a [B]custom[/B] account with advanced capabilities?', labelDeny = 33334, labelConfirm = 33743, labelCustom = 35233)
			if choice == Dialog.ChoiceNo:
				choice = Dialog.options(title = self._authenticateTitle(), message = 'Do you want to use an [B]unofficial[/B] free playground or authenticate an [B]official[/B] %s trial account? The free playground does not require account registration, but is unreliable, constrained, slow, and uncustomizable. The official %s account requires registration, but is reliable, unconstrained, fast, and customizable.' % (self.mOracle.organization(), self.mOracle.organization()), labelDeny = 36338, labelConfirm = 33743, labelCustom = 36337)
				if choice == Dialog.ChoiceNo:
					# Only do this if the setting is disabled (default) and not if the user already changed the setting.
					if self.mOracle.settingsPlaygroundDisabled(): self.mOracle.settingsPlaygroundEnable()
			if not choice == Dialog.ChoiceCustom: return False # Cancel, Close, Free.

		self._authenticateMessage({
			'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
				{'type' : 'text', 'value' : 'Authenticate with your API key which can be found on %s\'s website under the [I]Account[/I]  tab:' % self.mOracle.organization()},
				{'type' : 'link', 'value' : self.mOracle.linkAccount()},
			]
		})

	def authenticate(self, help = True, settings = True):
		return Account.authenticate(self, functionVerify = self._verify, functionHelp = self.help if help else None, functionBefore = self._select, settings = settings)

###################################################################
# BARD
###################################################################

class Bard(Account):

	def __init__(self):
		from lib.oracle.bard import Bard
		self.mOracle = Bard.instance()

		Account.__init__(self,
			#id = 'bard',
			id = self.mOracle.id(), # To set the correct value in settings.xml.
			mode = Premium.ModeCookie,

			name = self.mOracle.organization(),
			description = self.mOracle.helpDescription(),
			free = True,
			optional = True,

			linkDirect = self.mOracle.linkAccount(),
			linkRedirect = self.mOracle.linkRedirect(),

			level = 1,
			rank = 4,
			category = Account.SettingsOracle,
			color = self.mOracle.color(),
		)

	def help(self):
		self.mOracle.helpAuthentication()

	def _verify(self, data = None):
		if data is None: cookie = self.dataCookie()
		else: cookie = data['cookie']
		return self.mOracle.accountVerification(cookie = cookie)

	def authenticate(self, help = True, settings = True):
		return Account.authenticate(self, functionVerify = self._verify, functionHelp = self.help if help else None, settings = settings)

###################################################################
# BETTERAPI
###################################################################

class Betterapi(Account):

	def __init__(self):
		from lib.oracle.youchat import Youchat
		self.mOracle = Youchat.instance()

		Account.__init__(self,
			#id = 'betterapi',
			id = self.mOracle.id(), # To set the correct value in settings.xml.
			mode = Premium.ModeKey,

			name = self.mOracle.name(),
			description = self.mOracle.helpDescription(),
			free = True,
			optional = True,

			linkDirect = self.mOracle.linkAccount(),
			linkRedirect = self.mOracle.linkRedirect(),

			level = 1,
			rank = 2,
			category = Account.SettingsOracle,
			color = self.mOracle.color(),
		)

	def help(self):
		self.mOracle.helpAuthentication()

	def _free(self):
		if self.mFreeKey:
			Loader.show()
			key = self.mOracle.accountKeyGenerate()
			Loader.hide()
			return key
		return None

	def _verify(self, data = None):
		if data is None: key = self.dataKey()
		else: key = data['key']

		result = self.mOracle.accountVerification(key = key)
		if result: self.mOracle.settingsEnable()
		return result

	def _select(self):
		self.mFreeKey = False
		if not self.authenticated():
			choice = Dialog.options(title = self._authenticateTitle(), message = 'Do you want to generate a [B]free[/B] key or authenticate a [B]custom[/B] account?', labelDeny = 33334, labelConfirm = 33743, labelCustom = 35233)
			if choice == Dialog.ChoiceNo:
				self.mFreeKey = True
				return True
			if not choice == Dialog.ChoiceCustom: return False # Cancel, Close.

		self._authenticateMessage({
			'type' : Dialog.TypeDetails, 'text' : False, 'items' : [
				{'type' : 'text', 'value' : 'Authenticate with your API key which can be found on %s\'s website:' % self.name()},
				{'type' : 'link', 'value' : self.mOracle.linkAccount()},
			]
		})

	def authenticate(self, help = True, settings = True):
		return Account.authenticate(self, functionInternal = self._free, functionVerify = self._verify, functionHelp = self.help if help else None, functionBefore = self._select, settings = settings)
