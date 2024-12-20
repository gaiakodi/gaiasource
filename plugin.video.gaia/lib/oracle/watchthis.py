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

# https://www.watchthis.dev

from lib.oracle import Oracle
from lib.modules.tools import Media, Tools, Logger, Settings, Time, Regex, Converter
from lib.modules.interface import Dialog
from lib.modules.network import Networker

class Watchthis(Oracle):

	ErrorServer				= 'server'
	ErrorUnknown			= 'unknown'
	ErrorNone				= None

	Errors = {
		ErrorServer			: {'expression' : None, 'name' : 'Server', 'message' : 'An unknown server error occurred.'},
		ErrorUnknown		: {'expression' : None, 'name' : 'Unknown', 'message' : 'An unknown error occurred.'},
	}

	# It seems that this API just forwards the query to ChatGPT.
	# So technically we could use the custom Gaia queries (eg: JSON or ID).
	# However, this might raise suspicion with the site admin if suddenly other formatted queries comes into his OpenAI account.
	# So stick with the queries used on the website.
	QueryFixed				= {
		Media.Movie		: 'Give me a list of 5 movie recommendations that fit all of the following categories: . Make sure it fits the following description as well: %s. If you do not have 5 recommendations that fit these criteria perfectly, do your best to suggest other movie\'s that I might like. Please return this response as a numbered list with the movie\'s title, followed by a colon, and then a brief description of the movie. There should be a line of whitespace between each item in the list.',
		Media.Show		: 'Give me a list of 5 tv show recommendations that fit all of the following categories: . Make sure it fits the following description as well: %s. If you do not have 5 recommendations that fit these criteria perfectly, do your best to suggest other tv show\'s that I might like. Please return this response as a numbered list with the tv show\'s title, followed by a colon, and then a brief description of the tv show. There should be a line of whitespace between each item in the list.',
		Media.Mixed		: 'Give me a list of 5 tv show or movie recommendations that fit all of the following categories: . Make sure it fits the following description as well: %s. If you do not have 5 recommendations that fit these criteria perfectly, do your best to suggest other tv show or movie\'s that I might like. Please return this response as a numbered list with the tv show or movie\'s title, followed by a colon, and then a brief description of the tv show or movie. There should be a line of whitespace between each item in the list.',
	}

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Oracle.__init__(self,
			id				= 'watchthis',
			name			= 'WatchThis',
			organization	= 'WatchThis',

			type			= Oracle.TypeRecommender,
			subscription	= Oracle.SubscriptionFree,
			intelligence	= Oracle.IntelligenceMedium,
			rating			= 3,
			color			= 'FFDB2777',

			linkWeb			= 'https://watchthis.dev',
			linkApi			= 'https://watchthis.dev/api/getRecommendation',

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
		if details: help += ' It is an intelligent recommender with some advanced capabilities.'
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
				{'value' : 'Simple responses with restricted output formats.'},
			]},

			{'type' : 'title', 'value' : 'Accounts'},
			{'type' : 'text', 'value' : '%s does not require an account and can be used for free.' % name},
			{'type' : 'link', 'value' : self.linkAccount()},

			{'type' : 'title', 'value' : 'Usage'},
			{'type' : 'text', 'value' : '%s seems to be built on top of ChatGPT. It works similar to the native ChatGPT in Gaia, in that queries are adjusted with additional keywords to guide the chatbot in order to provide structured responses.' % name},
		]

		if dialog: self.helpDialog(items = items)
		return items

	##############################################################################
	# CHAT
	##############################################################################

	def _chat(self, message, context = None, conversation = None, refine = None, media = None):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()
			duration = 0

			result = self._result()
			result['error'] = self._requestError(type = Watchthis.ErrorServer)

			if refine: refine = self._chatRefine(conversation)
			else: refine = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			query = Media.Show if Media.isSerie(media) else Media.Movie if Media.isFilm(media) else Media.Mixed
			query = Watchthis.QueryFixed[query] % message

			returned = self._request(data = {'searched' : query})
			time2 = Time.timestamp()

			try: response = returned['data']
			except: response = None
			try: success = bool(returned['success'] and response)
			except: success = False
			try: error = returned['error']
			except: error = True

			Tools.update(result, {
				'success' : success,
				'error' : error,
			})

			try: result['duration'] = conversation['duration']
			except: pass
			result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

			history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), replace = True, time = time2, duration = duration, message = response, chatbot = result, data = returned['data'] )) # Replace, since during refine a new list is generated.
			result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST
	##############################################################################

	def _request(self, data = None, cache = False):
		link = self.linkApi()
		networker = Networker()
		response = networker.request(method = Networker.MethodPost, type = Networker.DataJson, link = link, data = data, cache = cache)

		data = networker.responseDataText()
		error = self._requestError(data = data, notification = True)

		return {
			'success' : bool(data and not error),
			'error' : error,
			'duration' : networker.responseDurationRequest(),
			'data' : data,
		}

	def _requestError(self, data = None, type = None, notification = False):
		result = Watchthis.ErrorNone

		if type:
			error = Watchthis.Errors[type]
			result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : None}
		elif data:
			try: message = data['error']
			except:  message = ''

			for type, error in Watchthis.Errors.items():
				if error['expression'] and Regex.match(data = message, expression = error['expression']):
					result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}
					break
			if result is Watchthis.ErrorNone and 'error' in data:
				error = Watchthis.Errors[Watchthis.ErrorUnknown]
				result = {'type' : Watchthis.ErrorUnknown, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}

			if notification and result: Dialog.notification(title = self.name(), message = result['message'], icon = Dialog.IconWarning)

		return result
