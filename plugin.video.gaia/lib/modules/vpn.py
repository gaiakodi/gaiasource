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

from lib.modules import tools
from lib.modules import interface
from lib.modules import network
from lib.modules.concurrency import Pool, Event

class Vpn(object):

	DetectionDisabled		= 0
	DetectionGeneric		= 1
	DetectionManager		= 2

	StatusUnknown			= 'unknown'			# Currently unknown status.
	StatusConnected			= 'connected'		# Currently connected.
	StatusConnecting		= 'connecting'		# Busy connecting for the first time.
	StatusReconnecting		= 'reconnecting'	# Busy reconnecting, that is, the VPN was previously connected, diconnected, and is now connecting again.
	StatusDisconnected		= 'disconnected'	# Currently disconnected.
	StatusDisconnecting		= 'disconnecting'	# Busy disconnecting.

	NotificationsDisabled	= 0
	NotificationsForeground	= 1
	NotificationsBackground	= 2

	LevelEssential			= 0
	LevelExtended			= 1

	AddressVpn				= 0
	AddressIsp				= 1

	MonitorKodi				= 0
	MonitorGaia				= 1

	KillDisabled			= 0
	KillBlock				= 1
	KillReconnect			= 2
	KillPause				= 1
	KillStop				= 2
	KillRestart				= 3

	PropertyStatus			= 'GaiaVpnStatus'

	DataStatus				= []
	DataLocation			= None

	KillThreadReconnect		= None
	KillEventPlayback		= None
	KillEventReconnect		= None
	KillNotification		= {}
	KillStopped				= False
	KillWait				= False
	KillAllow				= False

	Silent					= False

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		pass

	##############################################################################
	# LOG
	##############################################################################

	@classmethod
	def log(self, data):
		if data:
			unknown = interface.Translation.string(33387)
			try: status = data['status'].capitalize()
			except: status = None
			try: service = data['service']
			except: service = None
			try: profile = data['profile']
			except: profile = None
			try: ip = data['address']['ip']
			except: ip = None
			try: provider = data['network']['provider']
			except: provider = None
			try: organization = data['network']['organization']
			except: organization = None
			try: system = data['network']['system']
			except: system = None
			try: continent = data['location']['continent']['name']
			except: continent = None
			try: country = data['location']['country']['name']
			except: country = None
			try: region = data['location']['region']['name']
			except: region = None
			try: city = data['location']['city']['name']
			except: city = None
			tools.Logger.details(title = 'VPN', items = [
				{'section' : 'VPN Details', 'items' : [
					{'label' : 'Status', 'value' : status if status else unknown},
					{'label' : 'Service', 'value' : service if service else unknown},
					{'label' : 'Profile', 'value' : profile if profile else unknown},
				]},
				{'section' : 'Network Details', 'items' : [
					{'label' : 'IP Address', 'value' : ip if ip else unknown},
					{'label' : 'Provider', 'value' : provider if provider else unknown},
					{'label' : 'Organization', 'value' : organization if organization else unknown},
					{'label' : 'System', 'value' : system if system else unknown},
				]},
				{'section' : 'Location Details', 'items' : [
					{'label' : 'Continent', 'value' : continent if continent else unknown},
					{'label' : 'Country', 'value' : country if country else unknown},
					{'label' : 'Region', 'value' : region if region else unknown},
					{'label' : 'City', 'value' : city if city else unknown},
				]},
			], align = True)
		else:
			tools.Logger.log('VPN details cannot be detected.')

	##############################################################################
	# SETTINGS
	##############################################################################

	@classmethod
	def settingsEnabled(self):
		return self.settingsDetection() > Vpn.DetectionDisabled

	@classmethod
	def settingsDetection(self):
		return tools.Settings.getInteger('network.vpn.detection')

	@classmethod
	def settingsDetectionGeneric(self):
		return self.settingsDetection() == Vpn.DetectionGeneric

	@classmethod
	def settingsDetectionManager(self):
		return self.settingsDetection() == Vpn.DetectionManager

	@classmethod
	def settingsNotifications(self):
		return tools.Settings.getInteger('network.vpn.notifications')

	@classmethod
	def settingsNotificationsLevel(self):
		return tools.Settings.getInteger('network.vpn.notifications.level')

	@classmethod
	def settingsMonitor(self):
		return tools.Settings.getBoolean('network.vpn.monitor')

	@classmethod
	def settingsKill(self):
		return self.settingsEnabled() and tools.Settings.getBoolean('network.vpn.kill')

	@classmethod
	def settingsKillRequest(self):
		return tools.Settings.getInteger('network.vpn.kill.request') if self.settingsKill() else Vpn.KillDisabled

	@classmethod
	def settingsKillPlayback(self):
		return tools.Settings.getInteger('network.vpn.kill.playback') if self.settingsKill() else Vpn.KillDisabled

	@classmethod
	def settingsKillTimeout(self):
		return max(int(self.settingsInterval() * 1.5), tools.Settings.getCustom('network.vpn.kill.timeout'))

	@classmethod
	def settingsInterval(self):
		detection = self.settingsDetection()
		result = None
		if detection == Vpn.DetectionGeneric:
			if network.Geolocator.servicesCustomHas(): id = 'network.vpn.monitor.interval.alternative'
			else: id = 'network.vpn.monitor.interval'
			result = tools.Settings.getCustom(id)
		elif detection == Vpn.DetectionManager:
			result = 5 # Can be a very low value. This is only to check the global Kodi property and not an IP lookup. IP lookups only happen if the connection changes.
		return result

	@classmethod
	def settingsLaunch(self, id = None):
		tools.Settings.launch(id = 'network.vpn.detection' if id is None else id)

	##############################################################################
	# STATUS
	##############################################################################

	@classmethod
	def status(self, detect = False, property = None):
		status = None
		if not property:
			try: status = self.data(detect = detect)['status']
			except: pass
		if not status and not property is False:
			try: status = tools.System.windowPropertyGet(Vpn.PropertyStatus)
			except: pass
		return status if status else Vpn.StatusUnknown

	@classmethod
	def statusConnected(self, detect = False, property = None):
		return self.status(detect = detect, property = property) == Vpn.StatusConnected

	@classmethod
	def statusDisconnected(self, detect = False, property = None, lenient = False):
		if lenient: return not self.statusConnected(detect = detect)
		else: return self.status(detect = detect, property = property) == Vpn.StatusDisconnected

	@classmethod
	def statusConnectedGlobal(self):
		# Wait for the global var being set.
		# Important to avoid popups during Gaia launch if the the VPN detection only starts with Gaia and not with Kodi.
		for i in range(10):
			status = self.status(property = True)
			if not status == Vpn.StatusUnknown: break
			tools.Time.sleep(0.5)
		return status == Vpn.StatusConnected

	@classmethod
	def statusPrevious(self):
		try: return Vpn.DataStatus[-1]['status']
		except: return Vpn.StatusUnknown

	@classmethod
	def statusChanged(self, data = None, status = None):
		if data:
			try: statusCurrent = data['status']
			except: statusCurrent = Vpn.StatusUnknown
			try: statusPrevious = Vpn.DataStatus[-1]['status']
			except: statusPrevious = Vpn.StatusUnknown
		else:
			try: statusCurrent = Vpn.DataStatus[-1]['status']
			except: statusCurrent = Vpn.StatusUnknown
			try: statusPrevious = Vpn.DataStatus[-2]['status']
			except: statusPrevious = Vpn.StatusUnknown
		return not statusCurrent == statusPrevious

	@classmethod
	def statusSet(self, data = None):
		tools.System.windowPropertySet(Vpn.PropertyStatus, data['status'] if data else Vpn.StatusUnknown)
		tools.Settings.set('network.vpn.status', interface.Translation.string(33387) if not data else data['label']['setting'])

	@classmethod
	def statusNotification(self, data = None, force = False):
		if data is None: data = self.data(detect = force)
		if data:
			status = data['status']
			level = self.settingsNotificationsLevel()
			if (force or self.statusChanged()) and (level == Vpn.LevelExtended or (level == Vpn.LevelEssential and status in [Vpn.StatusDisconnected, Vpn.StatusConnected])):
				notifications = self.settingsNotifications()
				if notifications == Vpn.NotificationsForeground:
					indent = interface.Format.newline() + '     '
					unknown = interface.Format.fontItalic(33387)

					address = data['address']['ip']
					if not address: address = unknown

					service = [data['service'], data['network']['provider'], data['network']['organization']]
					service = tools.Tools.listUnique([i for i in service if i])
					service = ', '.join(service)
					if not service: service = unknown

					location = data['location']['label']['short']['comma']
					if not location: location = unknown

					if status == Vpn.StatusConnected: message = 33836
					elif status == Vpn.StatusConnecting: message = 33837
					elif status == Vpn.StatusReconnecting: message = 33838
					elif status == Vpn.StatusDisconnected: message = 33835
					elif status == Vpn.StatusDisconnecting: message = 33838
					else: message = 33840
					message = interface.Translation.string(message)

					message += '%s%s: %s' % (indent, interface.Translation.string(33706), interface.Format.fontBold(address))
					message += '%s%s: %s' % (indent, interface.Translation.string(36159), interface.Format.fontBold(service))
					message += '%s%s: %s' % (indent, interface.Translation.string(33874), interface.Format.fontBold(location))

					interface.Dialog.confirm(title = 35284, message = message)
				elif notifications == Vpn.NotificationsBackground:
					icon = None
					if status == Vpn.StatusDisconnected: icon = interface.Dialog.IconError
					elif status == Vpn.StatusDisconnecting: icon = interface.Dialog.IconWarning
					elif status == Vpn.StatusConnected: icon = interface.Dialog.IconSuccess
					else: icon = interface.Dialog.IconInformation

					if status in [Vpn.StatusDisconnected, Vpn.StatusConnected]: time = 10000
					else: time = 7000

					interface.Dialog.notification(title = data['label']['title'], message = data['label']['message'], icon = icon, time = time)

	##############################################################################
	# DATA
	##############################################################################

	@classmethod
	def data(self, refresh = False, detect = False, location = None):
		if refresh or (detect and not Vpn.DataStatus): return self.detect(location = location)
		try: return Vpn.DataStatus[-1]
		except: return None

	@classmethod
	def dataHas(self):
		return bool(Vpn.DataStatus)

	##############################################################################
	# DETECT
	##############################################################################

	@classmethod
	def detect(self, location = None):
		data = None
		detection = self.settingsDetection()
		if detection == Vpn.DetectionGeneric: data = self._detectGeneric()
		elif detection == Vpn.DetectionManager: data = self._detectManager()

		if data:
			time = tools.Time.timestamp()
			data['time'] = time

			if data['status'] == Vpn.StatusConnecting:
				statuses = [i['status'] for i in Vpn.DataStatus if time - i['time'] < 120] # Get statuses of past 2 minutes.
				statuses = [j for i, j in enumerate(statuses) if i == 0 or j != statuses[i - 1]] # Remove sequential duplicates.
				statuses = list(filter(lambda i : not i in (Vpn.StatusConnecting, Vpn.StatusReconnecting, Vpn.StatusDisconnecting), statuses)) # Remove certain statuses.
				if (len(statuses) >= 1 and (statuses[-1] == Vpn.StatusConnected)) or (len(statuses) >= 2 and (statuses[-1] == Vpn.StatusDisconnected and statuses[-2] == Vpn.StatusConnected)):
					data['status'] = Vpn.StatusReconnecting
			elif location or (not Vpn.DataStatus and data['status'] in [Vpn.StatusConnected, Vpn.StatusDisconnected]) or (Vpn.DataStatus and ((data['status'] == Vpn.StatusConnected and not Vpn.DataStatus[-1]['status'] == Vpn.StatusConnected) or (data['status'] == Vpn.StatusDisconnected and not Vpn.DataStatus[-1]['status'] == Vpn.StatusDisconnected))):
				if 'data' in data and data['data']: Vpn.DataLocation = data['data']
				else: Vpn.DataLocation = self._detectLocation()
			if Vpn.DataLocation: data.update(Vpn.DataLocation)

			values = {'service' : None, 'profile' : None, 'provider' : None, 'location1' : None, 'location2' : None}

			try: values['service'] = data['service']
			except: pass
			if not detection == Vpn.DetectionGeneric:
				try: values['profile'] = data['profile']
				except: pass

			try: values['provider'] = Vpn.DataLocation['network']['provider']
			except: pass
			if not values['provider']:
				try: values['provider'] = Vpn.DataLocation['network']['organization']
				except: pass

			try: values['location1'] = Vpn.DataLocation['location']['country']['name']
			except: pass
			if not values['location1']:
				try: values['location1'] = Vpn.DataLocation['location']['region']['name']
				except: pass
				if not values['location1']:
					if not values['location1']:
						try: values['location1'] = Vpn.DataLocation['location']['continent']['name']
						except: pass
			try: values['location2'] = Vpn.DataLocation['location']['city']['name']
			except: pass
			if not values['location2']:
				try: values['location2'] = Vpn.DataLocation['location']['region']['name']
				except: pass

			message = [values['service'], None if detection == Vpn.DetectionGeneric else values['profile'], values['location1'], values['location2']]
			message = [i for i in message if i]
			message = tools.Tools.listUnique(message)
			message = message[:3]

			if len(message) < 3 and values['provider']: message.append(values['provider'])
			message = tools.Tools.listUnique(message)
			if not message: message = [interface.Translation.string(36158)]

			setting = [data['status'].capitalize(), values['location1'], None if detection == Vpn.DetectionGeneric else values['profile'], values['location2']]
			setting = [i for i in setting if i]
			setting = tools.Tools.listUnique(setting)
			setting = setting[:2]
			if not setting: setting = [interface.Translation.string(36158)]

			data['label'] = {
				'title' : 'VPN %s' % data['status'].capitalize(),
				'message' : interface.Format.iconJoin(message),
				'setting' : interface.Format.iconJoin(setting),
			}

			self.statusSet(data)
			if self.statusChanged(data):
				tools.Logger.log('VPN Status Changed: %s -> %s' % (self.statusPrevious().capitalize(), data['status'].capitalize()))
				if data['status'] == Vpn.StatusConnected: self.log(data)

			Vpn.DataStatus.append(data)
			Vpn.DataStatus = Vpn.DataStatus[-100:] # Reduce to the last 100 values.

		return data

	@classmethod
	def _detectLocation(self, process = False, loader = False):
		if loader: interface.Loader.show()
		data = network.Geolocator.detectGlobal()
		if data and process:
			unknown = interface.Translation.string(33387)
			address = data['address']['ip']
			if not address: address = unknown
			provider = data['network']['provider']
			if not provider: provider = unknown
			location = data['location']['label']['short']['comma']
			if not location: location = unknown
			if loader: interface.Loader.hide()
			return address, provider, location
		if loader: interface.Loader.hide()
		return data

	@classmethod
	def _detectGeneric(self):
		data = None
		status = Vpn.StatusUnknown
		mask = tools.Settings.getString('network.vpn.address.mask')
		if mask and not mask == '0.0.0.0':
			status = Vpn.StatusDisconnected
			data = self._detectLocation()
			if data:
				while mask.endswith('.0') or mask.endswith('.*'):
					mask = mask[:-2]
				connected = data['address']['ip'].startswith(mask)
				if tools.Settings.getInteger('network.vpn.address') == Vpn.AddressIsp: connected = not connected
				if connected: status = Vpn.StatusConnected
		return {
			'connected' : status == Vpn.StatusConnected,
			'status' : status,
			'service' : None if not data else data['network']['provider'] or data['network']['organization'],
			'profile' : 'Generic',
			'data' : data,
		}

	@classmethod
	def _detectManager(self, location = False, status = True):
		data = {}
		if location:
			dataLocation = self._detectLocationManager()
			if dataLocation: data.update(dataLocation)
		if status:
			dataStatus = self._detectStatusManager()
			if dataStatus: data.update(dataStatus)
		return data

	@classmethod
	def _detectStatusManager(self):
		state = tools.System.windowPropertyGet('VPN_Manager_VPN_State').lower()
		control = tools.System.windowPropertyGet('VPN_Manager_Service_Control').lower()
		server = tools.System.windowPropertyGet('VPN_Manager_Requested_Server_Name')
		profile = tools.System.windowPropertyGet('VPN_Manager_Requested_Profile_Name')
		connection = tools.System.windowPropertyGet('VPN_Manager_Connected_Profile_Name')

		status = Vpn.StatusUnknown
		if 'start' in state:
			if 'stop' in control: status = Vpn.StatusDisconnecting
			else: status = Vpn.StatusConnected
		elif 'stop' in state:
			if server or profile: status = Vpn.StatusConnecting
			elif 'stop' in control: status = Vpn.StatusDisconnecting
			elif 'start' in control: status = Vpn.StatusConnecting
			else: status = Vpn.StatusDisconnected
		elif state == 'off':
			if 'stop' in control: status = Vpn.StatusDisconnecting
			else: status = Vpn.StatusDisconnected
		elif not state:
			if 'start' == control: status = Vpn.StatusDisconnected # When Kodi is booted, but not VPN was configured.
			elif control == 'started': status = Vpn.StatusConnecting
			elif 'stop' in control: status = Vpn.StatusDisconnecting
			else: status = Vpn.StatusDisconnected

		return {
			'connected' : status == Vpn.StatusConnected,
			'status' : status,
			'service' : tools.Regex.extract(data = connection, expression = '.*\/(.*?)\/.*\.ovpn'),
			'profile' : tools.Regex.extract(data = connection, expression = '.*\/(.*?)\.ovpn'),
		}

	@classmethod
	def _detectLocationManager(self):
		tools.System.windowPropertySet('VPN_Manager_API_State', '')
		tools.System.executeScript('special://home/addons/service.vpn.manager/api.py, GetIP')
		for i in range(300): # Wait up to 30 seconds.
			if tools.System.windowPropertyGet('VPN_Manager_API_State'): break
			tools.Time.sleep(0.1)
		return {
			'status' : Vpn.StatusConnected if tools.Converter.boolean(tools.System.windowPropertyGet('VPN_Manager_API_State')) else Vpn.StatusDisconnected,
			'ip' : tools.System.windowPropertyGet('VPN_Manager_API_IP'),
			'provider' : tools.System.windowPropertyGet('VPN_Manager_API_Provider'),
			'location' : tools.System.windowPropertyGet('VPN_Manager_API_Location'),
		}

	##############################################################################
	# VERIFICATION
	##############################################################################

	@classmethod
	def verification(self, data = None, settings = False):
		interface.Loader.show()
		self.data(refresh = True, location = True)
		interface.Loader.hide()
		self.dialog()
		if settings: self.settingsLaunch(id = 'network.vpn.status')

	##############################################################################
	# CONFIGURATION
	##############################################################################

	@classmethod
	def configuration(self, settings = False):
		result = None
		detection = self.settingsDetection()

		if detection == Vpn.DetectionDisabled:
			if tools.VpnManager.installed(): tools.Settings.set('network.vpn.detection', Vpn.DetectionManager)
			else: tools.Settings.set('network.vpn.detection', Vpn.DetectionGeneric)
			detection = self.settingsDetection()

		configured = False
		if detection == Vpn.DetectionGeneric:
			result = self._configurationGeneric()
			configured = len(tools.Settings.getString('network.vpn.address.mask')) >= 7
		elif detection == Vpn.DetectionManager:
			result = self._configurationManager()
			configured = tools.VpnManager.configured()

		if configured: tools.Settings.set('network.vpn.configuration', interface.Translation.string(35281))
		else: tools.Settings.default('network.vpn.configuration')

		interface.Loader.hide()
		if settings: self.settingsLaunch(id = 'network.vpn.configuration')
		return result

	@classmethod
	def _configurationGeneric(self, introduction = True):
		title = 33834
		success = None
		try:
			unknown = interface.Translation.string(33387)
			counter = 0

			if introduction:
				choice = interface.Dialog.option(title = title, message = 33822, labelConfirm = 33743, labelDeny = 33821)
				if choice:
					success = False
					raise Exception()

				choice = interface.Dialog.option(title = title, message = 33841, labelConfirm = 33743, labelDeny = 33821)
				if choice:
					success = False
					raise Exception()

			choice = interface.Dialog.option(title = title, message = 33823, labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()

			address, provider, location = self._detectLocation(process = True, loader = True)

			choice = interface.Dialog.option(title = title, message = interface.Translation.string(33824) % (address, provider, location), labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()
			elif address == unknown:
				raise Exception('Unknown IP Address')
			elif not '.' in address:
				raise Exception('Invalid IP Address: ' + str(address))

			counter += 1
			index = address.rfind('.')
			part = address[:index]
			mask = part + '.0'
			maskDisplay = part + '.*'

			choice = interface.Dialog.option(title = title, message = interface.Translation.string(33828) % maskDisplay, labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()

			choice = interface.Dialog.option(title = title, message = 33825, labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()

			addressNew, providerNew, locationNew = self._detectLocation(process = True, loader = True)

			while addressNew.startswith(part):
				while address == addressNew:
					choice = interface.Dialog.option(title = title, message = interface.Translation.string(33826) % (address, provider, location), labelConfirm = 33743, labelDeny = 33821)
					if choice:
						success = False
						raise Exception()
					elif address == unknown:
						raise Exception('Unknown IP Address')
					elif not '.' in address:
						raise Exception('Invalid IP Address: ' + str(address))
					addressNew, providerNew, locationNew = self._detectLocation(process = True, loader = True)

				if addressNew.startswith(part):
					address = addressNew
					provider = providerNew
					location = locationNew
					index = part.rfind('.')
					if index <= 0:
						raise Exception('ISP and VPN running on the same network')
					counter += 1
					part = part[:index]
					mask = part + ('.0' * counter)
					maskDisplay = part + ('.*' * counter)

					choice = interface.Dialog.option(title = title, message = interface.Translation.string(33830) % maskDisplay, labelConfirm = 33743, labelDeny = 33821)
					if choice:
						success = False
						raise Exception()

			choice = interface.Dialog.option(title = title, message =  interface.Translation.string(33827) % (addressNew, providerNew, locationNew), labelConfirm = 33743, labelDeny = 33821)
			if choice:
				success = False
				raise Exception()

			tools.Settings.set('network.vpn.detection', Vpn.DetectionGeneric)
			tools.Settings.set('network.vpn.address', Vpn.AddressIsp)
			tools.Settings.set('network.vpn.address.mask', mask)
			interface.Dialog.option(title = title, message = 33830, labelConfirm = 33743, labelDeny = 33832)

			success = True
		except:
			if success is None:
				tools.Logger.error()
				interface.Dialog.confirm(title = title, message = 33829)

		if success is None: success = False
		return success

	@classmethod
	def _configurationManager(self):
		tools.VpnManager.settings(wait = True)
		return tools.VpnManager.configured()

	##############################################################################
	# DIALOG
	##############################################################################

	@classmethod
	def dialog(self, data = None):
		if data is None: data = self.data()
		if data:
			def _value(value1, value2 = None, capitalize = False):
				if value1: value1 = tools.Tools.dictionaryGet(data, value1)
				if value2: value2 = tools.Tools.dictionaryGet(data, value2)

				if value1 is None: return interface.Format.fontItalic(33387)
				elif value2 is None: return value1.capitalize() if capitalize else value1
				else: return '%s (%s)' % (value1, value2.upper())

			items = []

			# VPN
			items.append({
				'title' : 33801,
				'items' : [
					{ 'title' : 33389, 'value' : _value(['status'], capitalize = True) },
					{ 'title' : 36159, 'value' : _value(['service']) },
					{ 'title' : 36160, 'value' : _value(['profile']) },
				]
			})

			# NETWORK
			items.append({
				'title' : 33719,
				'items' : [
					{ 'title' : 33706, 'value' : _value(['address', 'ip']) },
					{ 'title' : 33710, 'value' : _value(['network', 'provider']) },
					{ 'title' : 33711, 'value' : _value(['network', 'organization']) },
					{ 'title' : 33712, 'value' : _value(['network', 'system']) },
				]
			})

			# LOCATION
			items.append({
				'title' : 33874,
				'items' : [
					{ 'title' : 33713, 'value' : _value(['location', 'continent', 'name'], ['location', 'continent', 'code']) },
					{ 'title' : 33714, 'value' : _value(['location', 'country', 'name'], ['location', 'country', 'code']) },
					{ 'title' : 33715, 'value' : _value(['location', 'region', 'name'], ['location', 'region', 'code']) },
					{ 'title' : 33716, 'value' : _value(['location', 'city', 'name'], ['location', 'city', 'code']) },
					{ 'title' : 33717, 'value' : _value(['location', 'coordinate', 'latitude']) },
					{ 'title' : 33718, 'value' : _value(['location', 'coordinate', 'longitude']) },
				]
			})

			interface.Dialog.information(title = 35866, items = items)
		else:
			interface.Dialog.confirm(title = 35866, message = 33833)

	##############################################################################
	# KILL
	##############################################################################

	@classmethod
	def killStop(self):
		if not Vpn.KillWait:
			Vpn.KillStopped = True
			try: Vpn.KillEventPlayback.set()
			except: pass
			try: Vpn.KillEventReconnect.set()
			except: pass

	@classmethod
	def killStopped(self):
		return Vpn.KillStopped or tools.System.aborted()

	@classmethod
	def killRequest(self):
		result = True
		setting = self.settingsKillRequest()
		if not setting == Vpn.KillDisabled and not self.statusConnectedGlobal():
			if setting == Vpn.KillBlock: result = False
			elif setting == Vpn.KillReconnect: result = self._killRequestReconnect()
			if not result: self._killStatus(block = True)
		return result

	@classmethod
	def _killRequestReconnect(self):
		self.killMonitor()
		return self.killProgress()

	@classmethod
	def killPlayback(self, initial = False):
		if not self.settingsKillPlayback() == Vpn.KillDisabled:
			if initial:
				self.killMonitor()
				self.killProgress()
			else:
				Pool.thread(target = self._killPlayback).start()
		return Vpn.KillAllow

	@classmethod
	def _killPlayback(self):
		disconnected = False
		setting = self.settingsKillPlayback()
		if not setting == Vpn.KillDisabled:
			self.killMonitor()
			Vpn.KillEventPlayback.wait()
			disconnected = not Vpn.KillStopped and self.statusDisconnected(property = True)
			if disconnected:
				player = interface.Player()
				if setting == Vpn.KillPause:
					player.pause()
					self._killStatus(pause = True)
				elif setting == Vpn.KillStop:
					player.stop()
					self._killStatus(stop = True)
				elif setting == Vpn.KillRestart:
					Vpn.KillWait = True # To avoid being killed while still waiting for reconnection.
					resume = int(player.getTime())
					interface.Player().stop()
					tools.Time.sleep(0.5) # Wait a bit for onPlaybackStopped() in player.py code to finish.

					# Wait for window to reload, otherwise the stream window will show on top of other dialogs (progress dialog, notifications, etc).
					if tools.Settings.getInteger('interface.stream.interface.reload') >= 2:
						from lib.modules.stream import Settings
						if not Settings.settingsModeAutomatic(): # Window will not show for autoplay
							from lib.modules.window import WindowStreams
							for i in range(20):
								if WindowStreams.visible(): break
								tools.Time.sleep(0.5)

					self._killStatus(restart = True)
					if self.killProgress(): tools.System.queryRedo(parameters = {'resume' : resume})

					Vpn.KillWait = False
					self.killStop()

				return setting
		return None

	@classmethod
	def killMonitor(self):
		if Vpn.KillEventPlayback is None:
			lock = Pool.globalLock()
			lock.acquire()
			if Vpn.KillEventPlayback is None:
				Vpn.KillEventPlayback = Event()
				Vpn.KillEventReconnect = Event()
				Pool.thread(target = self._killMonitor).start()
				self._killMonitor(single = True) # Set the status of Events here immediatly, so we know the VPN status while the thread is busy starting.
			lock.release()

	@classmethod
	def _killMonitor(self, single = False):
		while not self.killStopped():
			if self.statusConnectedGlobal():
				Vpn.KillEventPlayback.clear()
				Vpn.KillEventReconnect.set()
			else:
				Vpn.KillEventPlayback.set()
				Vpn.KillEventReconnect.clear()
			if single: break
			tools.Time.sleep(1)

	@classmethod
	def killProgress(self):
		if Vpn.KillThreadReconnect is None:
			lock = Pool.globalLock()
			lock.acquire()
			if Vpn.KillThreadReconnect is None:
				Vpn.KillThreadReconnect = Pool.thread(target = self._killProgress)
				Vpn.KillThreadReconnect.start()
			lock.release()
		Vpn.KillThreadReconnect.join()
		Vpn.KillThreadReconnect = None # In case this function is called multiple times within the same execution and the thread has to be started again.
		return Vpn.KillAllow

	@classmethod
	def _killProgress(self):
		timeout = self.settingsKillTimeout() * 2 # x2 since we only sleep 0.5 seconds.

		if Vpn.Silent:
			dialog = None
			timeout *= 2 # Wait even longer during service.
		else:
			dialog = interface.Dialog.progress(title = 36166, message = 36178)

		reconnected = False
		for i in range(timeout):
			if Vpn.KillEventReconnect.is_set():
				reconnected = self.statusConnectedGlobal()
				break
			try:
				if dialog.iscanceled(): break
				dialog.update(int((i / timeout) * 100))
			except: pass
			tools.Time.sleep(0.5)
		try: dialog.close()
		except: pass

		if Vpn.Silent or reconnected: Vpn.KillAllow = True # If during the startup service the VPN does not connect before timing out, just allow the connection.
		else: Vpn.KillAllow = interface.Dialog.option(title = 36166, message = 36179, labelConfirm = 33821, labelDeny = 36162)

	@classmethod
	def _killStatus(self, block = False, pause = False, stop = False, restart = False):
		if not Vpn.Silent:
			title = 36166
			message = [36167]
			if block:
				key = 'block'
				message.append(36168)
				level = Vpn.LevelExtended
			elif pause:
				key = 'pause'
				message.append(36175)
				level = Vpn.LevelEssential
			elif stop:
				key = 'stop'
				message.append(36176)
				level = Vpn.LevelEssential
			elif restart:
				key = 'restart'
				message.append(36177)
				level = Vpn.LevelEssential
			else:
				return

			if not key in Vpn.KillNotification and self.settingsNotificationsLevel() >= level:
				Vpn.KillNotification[key] = True

				if not tools.Tools.isArray(message): message = [message]
				message = [interface.Translation.string(i) for i in message]

				notifications = self.settingsNotifications()
				if notifications == Vpn.NotificationsForeground:
					message = '. '.join(message)
					if not message.endswith('.'): message += '.'
					interface.Dialog.confirm(title = title, message = message, wait = False)
				elif notifications == Vpn.NotificationsBackground:
					message = interface.Format.iconJoin(message)
					interface.Dialog.notification(title = title, message = message, icon = interface.Dialog.IconWarning, time = 7000)

	##############################################################################
	# MONITOR
	##############################################################################

	@classmethod
	def monitor(self, delay = True, silent = False):
		Vpn.Silent = silent
		if self.settingsEnabled() and self.settingsMonitor(): Pool.thread(target = self._monitor, kwargs = {'delay' : delay}, start = True)

	@classmethod
	def _monitor(self, delay = True):
		self.statusSet()

		# If the IP is looked up before VPNManager starts, for some reason everything hangs (the IP lookup and also starting VPNManager).
		# Wait and allow VPNManager to start.
		if delay: tools.Time.sleep(5)

		interval = self.settingsInterval()
		while not tools.System.aborted():
			self.data(refresh = True, detect = True)
			self.statusNotification()
			if not interval: break
			if tools.System.abortWait(timeout = interval): break
