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

# https://deepsearch.mycelebs.com

from lib.oracle import Oracle
from lib.modules.tools import Media, Tools, Logger, Settings, Time, Regex, Converter
from lib.modules.interface import Dialog
from lib.modules.network import Networker

class Keytalk(Oracle):

	ActionFinder			= 'finder'
	ActionVoice				= 'voice'
	ActionBert				= 'bert'
	ActionModels			= 'models'
	ActionMovie				= 'maimovie'
	ActionShow				= 'maimovie_tv'

	ErrorServer				= 'server'
	ErrorUnknown			= 'unknown'
	ErrorNone				= None

	Errors = {
		ErrorServer			: {'expression' : None, 'name' : 'Server', 'message' : 'An unknown server error occurred.'},
		ErrorUnknown		: {'expression' : None, 'name' : 'Unknown', 'message' : 'An unknown error occurred.'},
	}

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Oracle.__init__(self,
			id				= 'keytalk',
			name			= 'KeyTalk',
			organization	= 'MyCelebs',

			type			= Oracle.TypeRecommender,
			subscription	= Oracle.SubscriptionFree,
			intelligence	= Oracle.IntelligenceLow,
			rating			= 3,
			color			= 'FF7950F2',

			linkWeb			= 'https://deepsearch.mycelebs.com',
			linkApi			= 'https://deepsearch.mycelebs.com/api',

			querySupport	= {
				Media.Mixed					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: False,
					Oracle.ModeSingle		: False,

					Oracle.QueryContext		: False,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: False,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: False,
					Oracle.QueryJsonId		: False,
				},
				Media.Movie					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: False,
					Oracle.ModeSingle		: False,

					Oracle.QueryContext		: False,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: False,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: False,
				},
				Media.Set					: {
					Oracle.ModePlain		: False,
					Oracle.ModeList			: False,
					Oracle.ModeSingle		: False,

					Oracle.QueryContext		: False,
					Oracle.QueryRaw			: False,
					Oracle.QueryTextTitle	: False,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: False,
				},
				Media.Show					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: False,
					Oracle.ModeSingle		: False,

					Oracle.QueryContext		: False,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: False,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: False,
				},
			},
		)

	##############################################################################
	# HELP
	##############################################################################

	def helpDescription(self, details = False, account = False):
		help = '%s is an AI media recommender developed by %s that makes movie and show suggestions.' % (self.name(), self.organization())
		if details: help += ' It is a primitive recommender with limited capabilities.'
		if account: help += ' No account is required.'
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
				{'value' : 'No account needed to use the service.'},
				{'value' : 'Quick response time.'},
			]},
			{'type' : 'subtitle', 'value' : 'Disadvantages'},
			{'type' : 'list', 'number' : False, 'value' : [
				{'value' : 'Primitive recommender with limited intelligence.'},
				{'value' : 'Simple responses with restricted output formats.'},
			]},

			{'type' : 'title', 'value' : 'Accounts'},
			{'type' : 'text', 'value' : '%s does not require an account and can be used for free.' % name},
			{'type' : 'link', 'value' : self.linkAccount()},

			{'type' : 'title', 'value' : 'Usage'},
			{'type' : 'text', 'value' : '%s is very primitive and only makes basic recommendations for related titles. %s cannot understand complex queries and will just extract known keywords from the request on which the suggestion will be based.' % (name, name)},
		]

		if dialog: self.helpDialog(items = items)
		return items

	##############################################################################
	# CHAT
	##############################################################################

	def _chat(self, message, context = None, conversation = None, refine = None, media = None):
		# KeyTalk does the following on their website:
		#	1. The user query is submitted and the API returns a list of "keytalks", which are keywords/terms/substrings extracted from the query.
		#	2. These "keytalks" are then used in another API call to retrieve the actual titles.
		#	3. If the 1st query did not return any "keytalks", the raw query is submitted as another API call to "bert" (assuming this is Google BERT), which directly returns titles.
		# Technically we could just query "bert" with the 1st call. However, this might cost KeyTalk more BERT tokens. Therefore, do the same as the website and only use it as fallback.

		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()
			duration = 0

			action = Keytalk.ActionShow if Media.isSerie(media) else Keytalk.ActionMovie

			result = self._result()
			result['error'] = self._requestError(type = Keytalk.ErrorServer)

			if refine: refine = self._chatRefine(conversation)
			else: refine = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			type = self.settingsQueryType()
			limit = self.settingsQueryLimit()
			language = self.settingsQueryLanguage()

			keytalks = None
			response = None
			success = False

			if type == 0 or type == 1:
				returned = self._request(action = [Keytalk.ActionFinder, Keytalk.ActionVoice, action], data = {
					'voice_content' : message,
					'voice_os' : 'web-deepsearch',
					'voice_service' : 'maimovie',
					'voice_lang' : language,
				})
				try: duration += returned['duration']
				except: pass

				if returned and returned['success'] and 'keytalks' in returned['data'] and returned['data']['keytalks']:
					keytalks = returned['data']['keytalks']
					if refine and 'keytalks' in refine and refine['keytalks']: keytalks = refine['keytalks'] + keytalks

					returned = self._request(action = [Keytalk.ActionFinder, action], data = {
						'start' : 0,
						'rows' : limit,
						'keytalk' : keytalks,
					})
					try: duration += returned['duration']
					except: pass

					try: response = Converter.jsonTo(returned['data']['data']['data'])
					except: response = None
					try: success = bool(returned['success'] and response)
					except: success = False
				else:
					returned = None

			if (type == 0 and not success) or type == 2:
				returned = self._request(action = [Keytalk.ActionBert, Keytalk.ActionModels, action], data = {
					'start' : 0,
					'rows' : limit,
					'sentence' : message,
				})
				try: duration += returned['duration']
				except: pass

			time2 = Time.timestamp()

			try:
				data = returned['data']
				response = data['data']['data']

				# Delete internal lists, since they cause problems when interpreting the reponse by the Oracle.
				# Update: Only add the necccessary attributes, since otherwise the description added to the plot is to long.
				'''if Tools.isArray(response):
					for i in response:
						if Tools.isDictionary(i):
							for k, v in i.items():
								try:
									if Tools.isArray(v):
										# Do not delete, since the iteration will fail with a changing dictionary size.
										#del i[k]
										i[k] = None
								except: pass'''
				temp = []
				for i in response:
					item = {}
					for j in ['imdb', 'imdb_id', 'title', 'original_title', 'year', 'release_date']:
						try: item[j] = i[j]
						except: pass
					if item: temp.append(item)

				response = Converter.jsonTo(temp)
			except:
				data = None
				response = None
			try: success = bool(returned['success'] and response)
			except: success = False
			try: error = returned['error']
			except: error = True

			Tools.update(result, {
				'success' : success,
				'error' : error,
				'chat' : {'refine' : {'keytalks' : keytalks}},
			})

			try: result['duration'] = conversation['duration']
			except: pass
			result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), duration or 0) # Get the max in case a cached result was returned.

			history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), replace = True, time = time2, duration = duration, message = response, chatbot = result, data = data)) # Replace, since during refine a new list is generated.
			result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST
	##############################################################################

	def _request(self, action, data = None, cache = False):
		if not Tools.isArray(action): action = [action]
		link = Networker.linkJoin(*([self.linkApi()] + action))

		cookies = {'first_user' : 'true', 'first_result_user' : 'true'}

		networker = Networker()
		response = networker.request(method = Networker.MethodPost, type = Networker.DataJson, link = link, data = data, cookies = cookies, cache = cache)
		data = networker.responseDataJson()

		error = self._requestError(data = data, notification = True)

		return {
			'success' : bool(data and not error),
			'error' : error,
			'duration' : networker.responseDurationRequest(),
			'data' : data,
		}

	def _requestError(self, data = None, type = None, notification = False):
		result = Keytalk.ErrorNone

		if type:
			error = Keytalk.Errors[type]
			result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : None}
		elif data:
			try: message = data['error']
			except:  message = ''

			for type, error in Keytalk.Errors.items():
				if error['expression'] and Regex.match(data = message, expression = error['expression']):
					result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}
					break
			if result is Keytalk.ErrorNone and 'error' in data:
				error = Keytalk.Errors[Keytalk.ErrorUnknown]
				result = {'type' : Keytalk.ErrorUnknown, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}

			if notification and result: Dialog.notification(title = self.name(), message = result['message'], icon = Dialog.IconWarning)

		return result
