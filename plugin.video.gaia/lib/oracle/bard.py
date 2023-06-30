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

# https://github.com/dsdanielpark/Bard-API

from lib.oracle import Oracle
from lib.modules.tools import Media, Tools, Logger, Converter, Regex, Time
from lib.modules.interface import Dialog
from lib.modules.external import Importer
from lib.modules.account import Bard as Account

class Bard(Oracle):

	ErrorAccountInvalid		= 'accountinvalid'
	ErrorAccountAccess		= 'accountaccess'

	ErrorServerReponse		= 'serverreponse'
	ErrorServer				= 'server'

	ErrorUnknown			= 'unknown'
	ErrorNone				= None

	Errors = {
		# Throws a Python excecption: raise Exception(\n', 'Exception: SNlM0e value not found in response. Check __Secure-1PSID value.
		# Or: __Secure-1PSID value must end with a single dot. Enter correct __Secure-1PSID value.
		ErrorAccountInvalid	: {'expression' : '(value\s*not\s*found\s*in\s*response|__Secure-1PSID)', 'name' : 'Account Invalid', 'message' : 'The authentication cookie is invalid or has expired.'},

		# Bard is not available in many EU countries.
		# The API returns the following error:
		#	{'content': 'Response Error: b\')]}\\\'\\n\\n38\\n[["wrb.fr",null,null,null,null,[9]]]\\n56\\n[["di",115],["af.httprm",115,"-509415844058109364",7]]\\n25\\n[["e",4,null,null,131]]\\n\'.'}
		# But when going onto the website, the following error is shown: Bard is not available in your country.
		ErrorAccountAccess	: {'expression' : 'response\s*error\s*:', 'name' : 'Account Access', 'message' : 'Bard is not available in your country or inaccessible due to other reasons.'},

		# Throws a Python excecption.
		# Eg: Response code not 200. Response Status is ...
		ErrorServerReponse	: {'expression' : None, 'name' : 'Server Reponse', 'message' : 'The server returned an invalid response.'},

		ErrorServer			: {'expression' : None, 'name' : 'Server', 'message' : 'An unknown server error occurred.'},

		ErrorUnknown		: {'expression' : None, 'name' : 'Unknown', 'message' : 'An unknown error occurred.'},
	}

	Timeout					= 60

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Oracle.__init__(self,
			id				= 'bard',
			name			= 'Bard',
			organization	= 'Google',

			type			= Oracle.TypeChatbot,
			subscription	= Oracle.SubscriptionFree,
			intelligence	= Oracle.IntelligenceHigh,
			rating			= 4, # Although often better than ChatGPT, we only give a rating of 4, since authentication is difficult and Bard is only accessible from a few countries. Plus, sometimes Kodi freezes when using Bard - might be something in the external module.
			color			= 'FF259DE1',

			linkWeb			= 'https://bard.google.com',
			linkAccount		= 'https://accounts.google.com',

			querySupport	= {
				Media.TypeMixed				: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
				Media.TypeMovie				: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
				Media.TypeSet				: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
				Media.TypeDocumentary		: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
				Media.TypeShort				: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
				Media.TypeShow				: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
			},
		)

	##############################################################################
	# HELP
	##############################################################################

	def helpDescription(self, details = False, account = False):
		help = '%s is a generic AI chatbot developed by %s that assists with human-language searches.' % (self.name(), self.organization())
		if details: help += ' It is an intelligent chatbot with advanced capabilities.'
		if account: help += ' Free accounts are available. But access might only be available in certain countries.'
		return help

	def helpAuthentication(self, dialog = True):
		name = self.name()
		organization = self.organization()

		items = [
			{'type' : 'title', 'value' : 'Chatbot'},
			{'type' : 'text', 'value' : self.helpDescription(details = True, account = True)},

			{'type' : 'title', 'value' : 'Characteristics'},
			{'type' : 'text', 'value' : '%s has the following characteristics:' % (name)},
			{'type' : 'subtitle', 'value' : 'Advantages'},
			{'type' : 'list', 'number' : False, 'value' : [
				{'value' : 'State of the art chatbot with good intelligence.'},
				{'value' : 'Access to Google\'s search engine with up-to-date data.'},
				{'value' : 'Quick response time.'},
				{'value' : 'Free accounts.'},
			]},
			{'type' : 'subtitle', 'value' : 'Disadvantages'},
			{'type' : 'list', 'number' : False, 'value' : [
				{'value' : 'No official public API.'},
				{'value' : 'Difficult account authentication using a desktop browser.'},
				{'value' : 'Access only available in some countries.'},
			]},

			{'type' : 'title', 'value' : 'Accounts'},
			{'type' : 'text', 'value' : '%s does not have an official public API yet. The chatbot is therefore utilized through a reversed-engineered library that accesses %s over its website interface. In order to authenticate your %s account, you will need a desktop browser to retrieve a cookie as follows:' % (name, name, organization)},
			{'type' : 'list', 'number' : True, 'value' : [
				{'value' : 'Open %s (%s) in a desktop browser.' % (name, Dialog.link(self.linkWeb(), identation = False))},
				{'value' : 'Sign in with your %s account.' % organization},
				{'value' : 'Hit the [I]F12[/I]  key to open the browser’s developer console.'},
				{'value' : 'Find the cookies stored by the website under [I]Session/Application[/I]  tab, in the [I]Cookies[/I]  section. Copy the value of the [B]__Secure-1PSID[/B] cookie, which is a long random string ending with a dot. Note that there are different cookies with similar names. Make sure to pick the correct one.'},
				{'value' : 'Enter the value of the cookie in the next step to authenticate your account.'},
			]},
			{'type' : 'text', 'value' : 'Note the following important points:'},
			{'type' : 'list', 'number' : False, 'value' : [
				{'value' : 'Do not log out of your %s account in the browser after you authenticated %s in Gaia. If you log out, %s will invalidate the cookie and you will not be able to use %s in Gaia anymore.' % (organization, name, organization, name)},
				{'value' : 'Do not share this cookie with anyone, since it gives access to your %s %s account.' % (organization, name)},
				{'value' : 'The cookie will expire in 6 months. After that you will have to redo the process and reauthenticate %s in Gaia with a new cookie.' % name},
				{'value' : '%s is currently only available in certain countries. Most EU countries are blocked. If you have a VPN, try changing to a US or Canada server, which mostly works.' % name},
			]},
			{'type' : 'text', 'value' : 'More details about the authentication process can be found here'},
			{'type' : 'link', 'value' : self.linkRedirect(help = True)},

			{'type' : 'title', 'value' : 'Usage'},
			{'type' : 'text', 'value' : 'There seems to currently not be any usage limits on %s and you can therefore make as many queries as you like.' % name},
		]

		if dialog: self.helpDialog(items = items)
		return items

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self):
		return Account()

	def accountCookie(self):
		return self.account().dataCookie()

	def accountAuthenticated(self, free = False):
		return self.account().authenticated()

	def accountAuthentication(self, settings = False):
		try:
			return self.account().authenticate(settings = settings)
		except:
			# Eg: externals.requests.exceptions.SSLError: HTTPSConnectionPool(host='bard.google.com', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLZeroReturnError(6, 'TLS/SSL connection has been closed (EOF) (_ssl.c:992)')))
			return False

	def accountVerification(self, cookie = None):
		try:
			result = self._requestChat(message = 'hi', cookie = cookie, notification = True)
			return bool(result and result['success'])
		except:
			# Eg: Exception: __Secure-1PSID value must end with a single dot. Enter correct __Secure-1PSID value.
			return False

	##############################################################################
	# MODULE
	##############################################################################

	@classmethod
	def moduleBard(self):
		return Importer.moduleBard()

	@classmethod
	def moduleConstants(self):
		return Importer.moduleBardConstants()

	@classmethod
	def moduleSession(self):
		return Importer.moduleSession()

	##############################################################################
	# CHAT
	##############################################################################

	def _chat(self, message, context = None, conversation = None, refine = None, media = None):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Bard.ErrorServer)

			if refine: refine = self._chatRefine(conversation)
			else: refine = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			returned = self._requestChat(message = message, session = refine, notification = True)
			time2 = Time.timestamp()

			try: response = returned['data']
			except: response = None
			try: success = bool(returned['success'] and response)
			except: success = False
			try: session = returned['session']
			except: session = None

			Tools.update(result, {
				'success' : success,
				'error' : returned['error'],
				'chat' : {'refine' : session},
			})

			try: result['duration'] = conversation['duration']
			except: pass
			result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

			history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = returned['duration'], message = response, chatbot = result, data = returned['data']))
			result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST
	##############################################################################

	def _requestChat(self, message = None, cookie = None, session = None, notification = True):
		timer = Time(start = True)

		if not cookie: cookie = self.accountCookie()
		bard = self.moduleBard()

		sessionData = session
		session = self.moduleSession()()
		session.headers = Tools.copy(self.moduleConstants().SESSION_HEADERS)
		if sessionData and 'cookies' in sessionData: session.cookies.update(sessionData['cookies'])
		session.cookies.set('__Secure-1PSID', cookie)

		language = self.settingsQueryLanguage()
		bard = bard(token = cookie, session = session, timeout = Bard.Timeout, language = language)
		if sessionData:
			if 'conversation' in sessionData: bard.conversation_id = sessionData['conversation']
			if 'response' in sessionData: bard.response_id = sessionData['response']
			if 'choice' in sessionData: bard.choice_id = sessionData['choice']

		# Specifically retreive the content attribute, since the rest of the data is not a normal dictionary and causes things to fail (eg: save the report to file).
		try: data = bard.get_answer(message)['content']
		except Exception as error: data = str(error)
		error = self._requestError(data = data, notification = notification)

		return {
			'success' : bool(data and not error),
			'error' : error,
			'duration' : timer.elapsed(milliseconds = True),
			'session' : {
				'cookies' : Tools.copy(session.cookies.get_dict()),
				'conversation' : bard.conversation_id,
				'response' : bard.response_id,
				'choice' : bard.choice_id,
			},
			'data' : data,
		}

	def _requestError(self, data = None, type = None, notification = False):
		result = Bard.ErrorNone

		if type:
			error = Bard.Errors[type]
			result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : None}
		elif data:
			message = str(data)

			for type, error in Bard.Errors.items():
				if error['expression'] and Regex.match(data = message, expression = error['expression']):
					result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}
					break
			if result is Bard.ErrorNone and 'error' in data:
				error = Bard.Errors[Bard.ErrorUnknown]
				result = {'type' : Bard.ErrorUnknown, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}

			if notification and result: Dialog.notification(title = self.name(), message = result['message'], icon = Dialog.IconWarning)

		return result
