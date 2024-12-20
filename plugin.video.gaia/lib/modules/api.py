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

from lib.modules import tools
from lib.modules import network
from lib.modules import convert
from lib.modules.cache import Cache

class Api(object):

	# Only use 32 characters.
	# Remove 0, O, 1, I, due to looking similar, in case the user has to enter the ID.
	Alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'

	ParameterType = 'type'
	ParameterAction = 'action'
	ParameterKey = 'key'
	ParameterTime = 'time'
	ParameterService = 'service'
	ParameterMode = 'mode'
	ParameterSelection = 'selection'
	ParameterContinent = 'continent'
	ParameterCountry = 'country'
	ParameterRegion = 'region'
	ParameterCity = 'city'
	ParameterCount = 'count'
	ParameterDetails = 'details'
	ParameterLast = 'last'
	ParameterId = 'id'
	ParameterName = 'name'
	ParameterVersion = 'version'
	ParameterSuccess = 'success'
	ParameterError = 'error'
	ParameterData = 'data'
	ParameterCurrency = 'currency'
	ParameterLink = 'link'

	TypeSpeedtest = 'speedtest'
	TypeDonation = 'donation'
	TypeAnnouncement = 'announcement'
	TypePromotion = 'promotion'
	TypeSupport = 'support'

	ActionAdd = 'add'
	ActionRetrieve = 'retrieve'
	ActionUpdate = 'update'
	ActionList = 'list'
	ActionCategories = 'categories'

	SelectionAll = 'all'
	SelectionAverage = 'average'
	SelectionMaximum = 'maximum'
	SelectionMinimum = 'minimum'

	ServiceNone = None
	ServiceGlobal = 'global'
	ServicePremiumize = 'premiumize'
	ServiceOffCloud = 'offcloud'
	ServiceRealDebrid = 'realdebrid'
	ServiceEasyNews = 'easynews'

	@classmethod
	def _idSplit(self, data, size = 2):
		result = []
		for i in range(0, len(data), size):
			result.append(list(data[i : i + size]))
		return result

	@classmethod
	def id(self, data):
		data = tools.Hash.sha256(data)
		data = self._idSplit(data)
		data = [int(i[0], 16) + int(i[1], 16) for i in data]
		data = [Api.Alphabet[i] for i in data]
		return ''.join(data)

	@classmethod
	def idDevice(self):
		return self.id(tools.Platform.identifier())

	@classmethod
	def request(self, type = None, action = None, parameters = {}, raw = False, cache = False):
		# Do not use the caching in Networking, since each API requests gets a timestamp, which will change the lookup ID for the cache.
		if cache is False:
			return self._request(type = type, action = action, parameters = parameters, raw = raw)
		else:
			if tools.Tools.isFunction(cache):
				return cache(function = self._request, type = type, action = action, parameters = parameters, raw = raw)
			else:
				if tools.Tools.isNumber(cache): time = cache
				else: time = Cache.TimeoutMedium
				return Cache.instance().cache(mode = None, timeout = time, refresh = None, function = self._request, type = type, action = action, parameters = parameters, raw = raw)

	@classmethod
	def _request(self, type = None, action = None, parameters = {}, raw = False, cache = False):
		if not type is None: parameters[Api.ParameterType] = type
		if not action is None: parameters[Api.ParameterAction] = action

		time = tools.Time.timestamp()
		parameters[Api.ParameterKey] = tools.Hash.sha256(tools.Converter.unicode(tools.System.obfuscate(tools.Settings.getString(tools.Converter.base64From('aW50ZXJuYWwua2V5LmdhaWE='), raw = True), 15 % 10)) + str(time) + tools.System.name().lower())
		parameters[Api.ParameterTime] = time
		try:
			# Sometimes the SSL cerificate is outdated, causing the API calls to take long and then finally fail. Disable the certificate check.
			# Update: Even with "certificate = False" this can still happen. Refresh the server SSL certificate.
			result = network.Networker().requestText(link = tools.Settings.getString('internal.link.api', raw = True), data = parameters, agent = network.Networker.AgentAddon, cache = cache, certificate = False)
			if raw:
				return result
			else:
				result = tools.Converter.jsonFrom(result)
				if result['success']: return result['data']
				else: return None
		except: return None

	@classmethod
	def lotteryValid(self):
		try: expiry = tools.Settings.getData('internal.lottery')['time']['expiry']
		except: expiry = 0
		return tools.Time.timestamp() < expiry

	@classmethod
	def _lotteryUpdate(self, result):
		if result and 'lottery' in result:
			result = result['lottery']
			if result['won']:
				tools.Settings.setData('internal.lottery', result)
				self.lotteryVoucher()

	@classmethod
	def _lotterVideo(self):
		from lib.modules import interface
		path = tools.File.joinPath(tools.System.pathResources(), 'resources', 'media', 'video', 'lottery', 'Gaia.m3u')
		player = interface.Player()
		if not player.isPlaying():
			player.play(path)

	@classmethod
	def lotteryDialog(self):
		from lib.modules import interface
		data = tools.Settings.getData('internal.lottery')
		indent = '     '
		message = interface.Format.bold(interface.Translation.string(33875)) + interface.Format.newline()
		message += '%s%s: %s' % (indent, interface.Translation.string(33343), interface.Format.bold(data['type'])) + interface.Format.newline()
		message += '%s%s: %s' % (indent, interface.Translation.string(33876), interface.Format.bold(data['voucher'])) + interface.Format.newline()
		if data['description']:
			message += '%s%s: %s' % (indent, interface.Translation.string(33040), interface.Format.bold(data['description'])) + interface.Format.newline()
		if data['instruction']:
			message += data['instruction']
			if not message.endswith('.'): message += '.'
		if data['time']['expiry'] and data['time']['duration']:
			expirationDuration = convert.ConverterDuration(data['time']['duration'], convert.ConverterDuration.UnitSecond).string(format = convert.ConverterDuration.FormatWordLong, unit = convert.ConverterDuration.UnitDay)
			expirationTime = convert.ConverterTime(data['time']['expiry'], convert.ConverterTime.FormatTimestamp).string(format = convert.ConverterTime.FormatDate)
			expiration = '%s (%s)' % (expirationDuration, expirationTime)
			message += ' ' + (interface.Translation.string(33877) % expiration)
		message += ' ' + interface.Translation.string(33878)

		interface.Dialog.confirm(title = 33879, message = message)
		interface.Player().stop()

	@classmethod
	def lotteryVoucher(self):
		data = tools.Settings.getData('internal.lottery')
		try: valid = bool(data['type'] and data['voucher'])
		except: valid = False
		if valid:
			self._lotterVideo()
			tools.Time.sleep(3)
			self.lotteryDialog()

	@classmethod
	def donation(self, currency = None, cache = False):
		if cache is True: cache = Cache.TimeoutLong
		parameters = {}
		if not currency is None: parameters[Api.ParameterCurrency] = currency
		return self.request(type = Api.TypeDonation, action = Api.ActionRetrieve, parameters = parameters, cache = cache)

	@classmethod
	def announcement(self, last = None, version = None, count = 1, cache = False):
		if cache is True: cache = Cache.TimeoutMedium
		parameters = {}
		if not last is None and not last == '': parameters[Api.ParameterLast] = last
		if not version is None and not version == '': parameters[Api.ParameterVersion] = version
		if not count is None and not count == '': parameters[Api.ParameterCount] = count
		return self.request(type = Api.TypeAnnouncement, action = Api.ActionRetrieve, parameters = parameters, cache = cache)

	@classmethod
	def promotion(self, cache = False):
		if cache is True: cache = Cache.TimeoutMedium
		return self.request(type = Api.TypePromotion, action = Api.ActionRetrieve, cache = cache)

	@classmethod
	def supportCategories(self, cache = False):
		if cache is True: cache = Cache.TimeoutLong
		return self.request(type = Api.TypeSupport, action = Api.ActionCategories, cache = cache)

	@classmethod
	def supportList(self, category = None, cache = False):
		if cache is True: cache = Cache.TimeoutLong
		parameters = {}
		if not category is None and not category == '': parameters[Api.ParameterId] = category
		return self.request(type = Api.TypeSupport, action = Api.ActionList, parameters = parameters, cache = cache)

	@classmethod
	def supportQuestion(self, id, cache = False):
		if cache is True: cache = Cache.TimeoutLong
		parameters = {}
		parameters[Api.ParameterId] = id
		return self.request(type = Api.TypeSupport, action = Api.ActionRetrieve, parameters = parameters, cache = cache)

	@classmethod
	def speedtestAdd(self, data):
		data['device'] = self.idDevice()
		parameters = {}
		parameters[Api.ParameterData] = tools.Converter.jsonTo(data)
		result = self.request(type = Api.TypeSpeedtest, action = Api.ActionAdd, parameters = parameters)
		self._lotteryUpdate(result)

	@classmethod
	def speedtestRetrieve(self, service, selection, continent, country, region, city, cache = False):
		if cache is True: cache = Cache.TimeoutLong
		parameters = {}
		if not service == Api.ServiceNone: parameters[Api.ParameterService] = service
		parameters[Api.ParameterSelection] = selection
		parameters[Api.ParameterContinent] = continent
		parameters[Api.ParameterCountry] = country
		parameters[Api.ParameterRegion] = region
		parameters[Api.ParameterCity] = city
		return self.request(type = Api.TypeSpeedtest, action = Api.ActionRetrieve, parameters = parameters, cache = cache)
