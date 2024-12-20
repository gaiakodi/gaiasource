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

# When googeling YouChat's API, this link pops up:
#	https://you.com/search?q=how+do+i+access+the+youchat+api+from+python%3F&tbm=youchat&cfr=chatb&cid=c2_3185ff03-f4ab-4ef4-a84e-31d31ef59487
# This is the chatbot explaining how to use its own API, by using the link:
#	https://api.you.com/chatbot/v1/search?q={query}&apikey={api_key}
# And saying: "To access the YouChat API from Python , you first need to complete the user registration process on the You.com website to obtain your API key".
# However, there is no API key in the account settings and none was email after registration.
#
# Via a Reddit post, the apparent devs of YouChat said to use the BetterAPI:
#	https://www.reddit.com/r/YouSearch/comments/10gk4a8/when_will_an_api_for_youchat_be_available/
#	https://github.com/You-OpenSource/You-Python
#	https://api.betterapi.net/about/
#	https://api.betterapi.net/redoc
# When using the BetterAPI code, YouChat is hidden behind Cloudflare (https://you.com/api/streamingSearch).
# BetterAPI also has Google Bard (returns server error) and BetterChat (provides cut-off replies).

from lib.oracle import Oracle
from lib.modules.tools import Media, Tools, Logger, Converter, Settings, Regex, Time
from lib.modules.interface import Dialog
from lib.modules.network import Networker
from lib.modules.account import Betterapi as Account

class Youchat(Oracle):

	ErrorAccountKey			= 'accountkey'	# {"error":"We apologize, but it appears that we were unable to locate a valid API key associated with this request. This issue may occur if you generated your key prior to February 26th, 2023. Please be advised that any API keys that have not been used within two hours of creation will automatically be deleted to ensure the security of our system. To resolve this issue, we recommend generating a new API key and ensuring that it is used within the designated time frame. Thank you for your understanding and cooperation."}
	ErrorServerLoad			= 'serverload'	# {"message": "Im sorry, but we have reached the maximum number of users at the moment. Please wait a bit and try again later. Thank you for your patience!", "time": "01", "status_code": 200}
	ErrorServer				= 'server'

	ErrorUnknown			= 'unknown'
	ErrorNone				= None

	Errors = {
		ErrorAccountKey		: {'expression' : 'valid[\s\-\_]*api[\s\-\_]*key', 'name' : 'Account Key', 'message' : 'The account API key is invalid.'},
		ErrorServerLoad		: {'expression' : 'reached\sthe\smaximum\snumber\sof\susers ', 'name' : 'Server Load', 'message' : 'The server is currently overloaded. Try again later.'},
		ErrorServer			: {'expression' : None, 'name' : 'Server', 'message' : 'An unknown server error occurred.'},

		ErrorUnknown		: {'expression' : None, 'name' : 'Unknown', 'message' : 'An unknown error occurred.'},
	}

	RetryCount				= 1
	RetryDelay				= 3

	Timeout					= 90

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Oracle.__init__(self,
			id				= 'youchat',
			name			= 'YouChat',
			organization	= 'You',

			type			= Oracle.TypeChatbot,
			subscription	= Oracle.SubscriptionFree,
			intelligence	= Oracle.IntelligenceLow,
			rating			= 2,
			color			= 'FF00DCFF',

			linkWeb			= 'https://you.com/chat',
			linkApi			= 'https://api.betterapi.net/youchat',
			linkAccount		= 'https://api.betterapi.net/about',
			linkKey			= 'https://api.betterapi.net/gen',

			# When requesting JSON, the chatbot basically gives JS code and explains how to generate the JSON yourself.
			# Generally when requesting very specific data (like IDs), the chatbot just tells you to go onto IMDb/TMDb website and find the stuff yourself.
			querySupport	= {
				Media.Mixed					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: False,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: False,
					Oracle.QueryJsonId		: False,
				},
				Media.Movie					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: False,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: False,
					Oracle.QueryJsonId		: False,
				},
				Media.Set					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: False,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: False,
					Oracle.QueryJsonId		: False,
				},
				Media.Show					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: False,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: False,
					Oracle.QueryJsonId		: False,
				},
			},
		)

	##############################################################################
	# HELP
	##############################################################################

	def helpDescription(self, details = False, account = False):
		help = '%s is a generic AI chatbot developed by %s that assists with human-language searches.' % (self.name(), self.organization())
		if details: help += ' It is a primitive chatbot with limited capabilities.'
		if account: help += ' Free accounts are available.'
		return help

	def helpAuthentication(self, dialog = True):
		name = self.name()
		organization = self.organization()

		items = [
			{'type' : 'title', 'value' : 'Chatbot'},
			{'type' : 'text', 'value' : self.helpDescription(details = True, account = True)},
			{'type' : 'link', 'value' : self.linkWeb()},

			{'type' : 'title', 'value' : 'Characteristics'},
			{'type' : 'text', 'value' : '%s has the following characteristics:' % name},
			{'type' : 'subtitle', 'value' : 'Advantages'},
			{'type' : 'list', 'number' : False, 'value' : [
				{'value' : 'Free accounts without expiration.'},
			]},
			{'type' : 'subtitle', 'value' : 'Disadvantages'},
			{'type' : 'list', 'number' : False, 'value' : [
				{'value' : 'Primitive chatbot with limited intelligence.'},
				{'value' : 'Simple responses with restricted output formats.'},
				{'value' : 'Query limit based on server load.'},
			]},

			{'type' : 'title', 'value' : 'Accounts'},
			{'type' : 'text', 'value' : '%s can currently not be accessed through %s\'s own API. Instead, you can utilize %s through the BetterAPI, which offers free API keys without requiring account registration.' % (name, organization, name)},
			{'type' : 'link', 'value' : self.linkAccount()},

			{'type' : 'title', 'value' : 'Usage'},
			{'type' : 'text', 'value' : '%s is very primitive, struggling to provide responses in the desired formats. In many cases the chatbot will also not reply adequately and tell you to search for titles yourself.' % name},
		]

		if dialog: self.helpDialog(items = items)
		return items

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self):
		return Account.instance()

	def accountKey(self):
		return self.account().dataKey()

	def accountKeyGenerate(self):
		data = self._request(link = self.linkKey())
		try: return data['key']
		except: return None

	def accountAuthenticated(self, free = False):
		return self.account().authenticated()

	def accountAuthentication(self, settings = False):
		return self.account().authenticate(settings = settings)

	def accountVerification(self, key = None):
		result = self._requestChat(message = 'hi', key = key, notification = False)
		return bool(result and result['success'])

	##############################################################################
	# CHAT
	##############################################################################

	def _chat(self, message, context = None, conversation = None, refine = None, media = None):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Youchat.ErrorServer)

			if refine: refine = self._chatRefine(conversation)
			else: refine = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			# The chatbot system context is not yet implemented in BetterAPI.
			if refine: idContext = refine['contextid']
			else: idContext = Tools.stringRandom(length = 32, uppercase = True, lowercase = True, digits = True, symbols = False)

			# Only way to deal with refinments with the current API.
			messages = []
			if refine: messages = refine['messages']
			messages.append(message)

			data = {
				'inputs' : '. '.join([i.strip(' ').strip('.').strip(' ') for i in messages]),
				'contextid' : idContext,
				'stream' : False,
			}
			returned = self._requestChat(data = data)
			time2 = Time.timestamp()

			try: response = returned['data']['generated_text']
			except: response = None
			try: success = bool(returned['success'] and response)
			except: success = False

			Tools.update(result, {
				'success' : success,
				'error' : returned['error'],
				'chat' : {'refine' : {'contextid' : idContext, 'messages' : messages}},
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

	def _request(self, link, data = None, headers = None, cookies = None, cache = False):
		return Networker().requestJson(method = Networker.MethodGet, link = link, data = data, headers = headers, cookies = cookies, cache = cache)

	def _requestChat(self, message = None, data = None, key = None, cache = False, retry = True, notification = True):
		# Manually measure time, since networker.responseDurationRequest() can return None if the request was aborted by the server.
		timer = Time(start = True)

		if not data: data = {'inputs' : message}
		if not 'key' in data: data['key'] = key if key else self.accountKey()

		link = self.linkApi()
		timeout = int(min(Youchat.Timeout * 3, max(Youchat.Timeout, Youchat.Timeout * (len(Converter.jsonTo(data)) / 500.0)))) if data else None

		networker = Networker()
		response = networker.request(method = Networker.MethodGet, link = link, data = data, cache = cache, timeout = timeout)
		error = self._requestError(data = networker.responseDataJson(), notification = not retry)

		if error == Youchat.ErrorServerLoad and retry:
			if retry is True: retry = Youchat.RetryCount
			while retry > 0 and response:
				Logger.log('YouChat is currently overloaded. Retrying query: %s' % Converter.jsonTo(data), type = Logger.TypeError)
				Time.sleep(Youchat.RetryDelay)
				retry -= 1
				response = networker.request(method = Networker.MethodGet, link = link, data = data, cache = cache, timeout = timeout)
				error = self._requestError(data = networker.responseDataJson(), notification = retry == 0) # Only show the error notification after the last retry.

		return {
			'success' : bool(data and not error),
			'error' : error,
			'duration' : timer.elapsed(milliseconds = True),
			'data' : networker.responseDataJson(),
		}

	def _requestError(self, data = None, type = None, notification = False):
		result = Youchat.ErrorNone

		if type:
			error = Youchat.Errors[type]
			result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : None}
		elif data:
			try: message = data['error']
			except:
				try: message = data['message']
				except: message = ''

			for type, error in Youchat.Errors.items():
				if error['expression'] and Regex.match(data = message, expression = error['expression']):
					result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}
					break
			if result is Youchat.ErrorNone and 'error' in data:
				error = Youchat.Errors[Youchat.ErrorUnknown]
				result = {'type' : Youchat.ErrorUnknown, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}

			if notification and result: Dialog.notification(title = self.name(), message = result['message'], icon = Dialog.IconWarning)

		return result
