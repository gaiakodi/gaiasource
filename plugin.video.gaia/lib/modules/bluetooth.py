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

from lib.modules.tools import Subprocess, Regex, Tools, Logger, Time, System, Settings
from lib.modules.concurrency import Pool

class Bluetooth(object):

	PropertySupport 	= 'GaiaBluetoothSupport'
	PropertyBusy 		= 'GaiaBluetoothBusy'

	SettingEnabled		= 'bluetooth.general.enabled'
	SettingDevices		= 'bluetooth.device.list'
	SettingReconnect	= 'bluetooth.monitor.enabled'
	SettingInterval		= 'bluetooth.monitor.interval'

	Count				= None

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _execute(self, action = None, exit = True, timeout = None):
		if action:
			if Tools.isArray(action): action = '\n'.join(action)
			action = '%s\n' % action
			if exit: action += 'exit'
		else:
			action = True
		return Subprocess.open(command = 'bluetoothctl', communicate = action, timeout = timeout)

	@classmethod
	def _wait(self, device, loader = True, duration = 45):
		from lib.modules.interface import Loader
		if loader: Loader.show()

		if not Tools.isArray(device): device = [device]
		changed = []
		for i in range(duration):
			if System.aborted(): return
			devices = self.devices()
			for j in device:
				address = j['address']
				for k in devices:
					if address == k['address']:
						if not address in changed and not j == k: changed.append(address)
						break
			if len(changed) >= len(device): break
			Time.sleep(1)

		if loader: Loader.hide()

	@classmethod
	def _extractDevice(self, data):
		return Regex.extract(data = data, expression = '^\s*device\s+((?:[a-f\d]{2}[:-]){5}[a-f\d]{2})\s+(.*?)$', all = True, group = None, flags = Regex.FlagCaseInsensitive | Regex.FlagMultiLines)

	@classmethod
	def _extractInfo(self, data, attribute):
		data = Regex.extract(data = data, expression = '^\s*%s\s*:?\s*(.*?)$' % attribute, flags = Regex.FlagCaseInsensitive | Regex.FlagMultiLines)
		return bool(data and data.lower().strip() == 'yes')

	@classmethod
	def _settingsLabel(self, count):
		from lib.modules.interface import Translation
		Settings.set(Bluetooth.SettingDevices, '%d %s' % (count, Translation.string(35012 if count == 1 else 33536)))

	@classmethod
	def _busy(self):
		return bool(System.windowPropertyGet(Bluetooth.PropertyBusy))

	@classmethod
	def _busySet(self):
		System.windowPropertySet(Bluetooth.PropertyBusy, '1')

	@classmethod
	def _busyClear(self):
		System.windowPropertyClear(Bluetooth.PropertyBusy)

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def initialize(self):
		supported = self.supported(enabled = False)
		System.windowPropertySet(Bluetooth.PropertySupport, str(int(supported)))
		if supported: self.devices() # To update the device count in ther settings.

	@classmethod
	def enabled(self):
		return Settings.getBoolean(Bluetooth.SettingEnabled)

	@classmethod
	def supported(self, enabled = True):
		if not enabled or self.enabled():
			#data = self._execute(action = 'version') # This calls hangs if there is no Bluetooth dongle: Waiting to connect to bluetoothd...
			data = Subprocess.output(command = 'bluetoothctl --version')
			return bool(data and Regex.extract(data = data, expression = '^\s*bluetoothctl.*?(\d+\.)', flags = Regex.FlagCaseInsensitive | Regex.FlagMultiLines))
		return False

	@classmethod
	def devices(self, paired = None, trusted = None, blocked = None, connected = None):
		devices = []

		# NB: If there is no Bluetooth dongle, the command hangs with: Waiting to connect to bluetoothd...
		# Add a timeout to it.
		dataAll = self._execute(action = 'devices', timeout = 10)
		if dataAll:
			dataAll = self._extractDevice(data = dataAll)
			if dataAll:
				for device in dataAll:
					deviceAddress = device[0]
					deviceName = device[1]
					devicePaired = False
					deviceTrusted = False
					deviceBlocked = False
					deviceConnected = False

					dataInfo = self._execute(action = 'info ' + deviceAddress)
					if dataInfo:
						devicePaired = self._extractInfo(data = dataInfo, attribute = 'paired')
						deviceTrusted = self._extractInfo(data = dataInfo, attribute = 'trusted')
						deviceBlocked = self._extractInfo(data = dataInfo, attribute = 'blocked')
						deviceConnected = self._extractInfo(data = dataInfo, attribute = 'connected')

					devices.append({'name' : deviceName, 'address' : deviceAddress, 'paired' : devicePaired, 'trusted' : deviceTrusted, 'blocked' : deviceBlocked, 'connected' : deviceConnected})

				if not Bluetooth.Count == len(devices):
					Bluetooth.Count = len(devices)
					self._settingsLabel(count = Bluetooth.Count)

				if not paired is None: devices = [device for device in devices if device['paired'] == paired]
				if not trusted is None: devices = [device for device in devices if device['trusted'] == trusted]
				if not blocked is None: devices = [device for device in devices if device['blocked'] == blocked]
				if not connected is None: devices = [device for device in devices if device['connected'] == connected]

		return devices

	@classmethod
	def connect(self, device = None, paired = True, trusted = None, blocked = None, connected = False, wait = True, loader = True, busy = True):
		try:
			if busy: self._busySet()

			from lib.modules.interface import Loader
			if loader: Loader.show()

			if not device: device = self.devices(paired = paired, trusted = trusted, blocked = blocked, connected = connected)
			elif not Tools.isArray(device): device = [device]

			for i in device:
				address = i['address']

				# Pairing can take some time, and we can therefore not execute all these commands right after each other.
				# Do not exit, but let the subprocess timeout, bbasically creating a sleep(15) between the commands.
				for action in ['pair', 'trust', 'connect']:
					if loader: Loader.show()
					self._execute(action = action + ' ' + address, exit = False, timeout = 15)
					self._wait(device = i, loader = False, duration = 15)

			if wait: self._wait(device = device, loader = loader)
		except:
			Logger.error()
		finally:
			if busy: self._busyClear()

	@classmethod
	def disconnect(self, device = None, paired = True, trusted = None, blocked = None, connected = True, wait = True, loader = True, busy = True):
		try:
			if busy: self._busySet()

			from lib.modules.interface import Loader
			if loader: Loader.show()

			if not device: device = self.devices(paired = paired, trusted = trusted, blocked = blocked, connected = connected)
			elif not Tools.isArray(device): device = [device]

			for i in device:
				self._execute(action = 'disconnect ' + i['address'])

			if wait: self._wait(device = device, loader = loader)
		except:
			Logger.error()
		finally:
			if busy: self._busyClear()

	##############################################################################
	# DIALOG
	##############################################################################

	@classmethod
	def dialog(self, wait = True, loader = True, settings = False):
		try:
			from lib.modules.interface import Dialog, Loader
			if loader: Loader.show()

			self._busySet()
			self.tWait = wait
			self.tLoader = loader
			Dialog.information(title = 33529, items = self._dialogItems(), refresh = self._dialogItems, reselect = Dialog.ReselectYes)

			if settings: Settings.launch(id = Bluetooth.SettingDevices)
			if loader: Loader.hide()
		except:
			Logger.error()
		finally:
			self._busyClear()

	@classmethod
	def _dialogAction(self, device, wait = True, loader = True):
		if device['connected']: self.disconnect(device = device, wait = wait, loader = loader)
		else: self.connect(device = device, wait = wait, loader = loader)

	@classmethod
	def _dialogItems(self):
		from lib.modules.interface import Dialog, Format

		paired = Format.fontColor(33533, color = Format.colorSpecial())
		unpaired = Format.fontColor(33535, color = Format.colorPoor())
		trusted = Format.fontColor(35531, color = Format.colorGood())
		blocked = Format.fontColor(33534, color = Format.colorBad())
		connected = Format.fontColor(35857, color = Format.colorExcellent())
		disconnected = Format.fontColor(35858, color = Format.colorPoor())

		items = [
			{'title' : Dialog.prefixBack(33486), 'close' : True},
			{'title' : Dialog.prefixNext(32072), 'action' : lambda: None},
			{'title' : Dialog.prefixNext(33530), 'action' : self.connect, 'parameters' : {'busy' : False}},
			{'title' : Dialog.prefixNext(33531), 'action' : self.disconnect, 'parameters' : {'busy' : False}},
			'',
		]

		devices = self.devices()
		for device in devices:
			value = []
			if device['connected']: value.append(connected)
			elif device['paired']: value.append(disconnected)
			if device['blocked']: value.append(blocked)
			if device['trusted']: value.append(trusted)
			if device['paired']: value.append(paired)
			elif not device['connected']: value.append(unpaired)

			items.append({'title' : device['name'], 'value' : Format.iconJoin(value), 'color' : False, 'action' : self._dialogAction, 'parameters' : {'device' : device, 'wait' : self.tWait, 'loader' : self.tLoader}})

		return items

	##############################################################################
	# SERVICE
	##############################################################################

	@classmethod
	def service(self):
		Pool.thread(target = self._serviceInitialize, start = True)

	@classmethod
	def _serviceInitialize(self):
		# Intialize in the service, and not when Gaia is launched, since the initialization can take some time if not Bluetooth dongle is connected.
		self.initialize()
		if Settings.getBoolean(Bluetooth.SettingReconnect) and self.supported():
			Pool.thread(target = self._serviceMonitor, start = True)

	@classmethod
	def _serviceMonitor(self):
		try:
			interval = Settings.getCustom(Bluetooth.SettingInterval)
			step = 5
			steps = int(interval / step)
			while not System.aborted():
				# Do not autoconnect while the user is manually connecting, disconnecting, or pairing.
				# Otherwise this might cause conflict.
				if not self._busy():
					self.connect(paired = True, connected = False, loader = False)

				# Make the service abort more quickly when the interval is very long.
				for i in range(steps):
					if System.aborted(): return
					Time.sleep(step)
		except: Logger.error()
