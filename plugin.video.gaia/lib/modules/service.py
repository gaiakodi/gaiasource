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

from lib.modules.tools import Tools, Logger, System, Settings, Time
from lib.modules.interface import Context, Translation
from lib.modules.library import Library
from lib.modules.vpn import Vpn
from lib.modules.bluetooth import Bluetooth
from lib.modules.cache import Cache
from lib.modules.external import Importer, Loader
from lib.modules.concurrency import Pool
from lib.modules.database import Database
from lib.modules import trakt as Trakt
from lib.providers.core.manager import Manager

class Service(object):

	ModeKodi			= 'kodi'
	ModeGaia			= 'gaia'

	SettingService		= 'general.launch.service'
	SettingAcceleration	= 'general.launch.acceleration'
	SettingAutomatic	= 'general.launch.automatic'

	##############################################################################
	# SETTINGS
	##############################################################################

	@classmethod
	def settingService(self, mode = None):
		result = Settings.getInteger(Service.SettingService)
		if mode:
			if mode == Service.ModeKodi: result = result == 0
			elif mode == Service.ModeGaia: result = result == 1
			else: result = False
		return result

	@classmethod
	def settingAcceleration(self):
		return Settings.getBoolean(Service.SettingAcceleration)

	@classmethod
	def settingAutomatic(self):
		return Settings.getBoolean(Service.SettingAutomatic)

	##############################################################################
	# LAUNCH
	##############################################################################

	@classmethod
	def launchKodi(self, thread = False, process = False):
		return self.launch(mode = Service.ModeKodi, thread = thread, process = process)

	@classmethod
	def launchGaia(self, thread = False, process = False):
		return self.launch(mode = Service.ModeGaia, thread = thread, process = process)

	@classmethod
	def launch(self, mode, thread = False, process = False):
		if self.settingService(mode = mode):
			if process:
				System.executePlugin(action = 'service' + mode.capitalize())
			else:
				if thread: Pool.thread(target = self._launch, kwargs = {'mode' : mode}, start = True)
				else: self._launch(mode = mode)
			return True
		return False

	@classmethod
	def _launch(self, mode):
		label = Translation.string(33805 if mode == Service.ModeKodi else 33806)
		Logger.log('SERVICE STARTED: %s' % label)

		kodi = mode == Service.ModeKodi

		# Reset possible old modules after the addon was updated.
		# Otherwise after upgrade, Gaia throws errors about copied modules under the __gaia__ directory.
		Importer.reset()
		Loader.reset()

		# Reset launch data to force Gaia to fully launch after the addon was upgraded.
		if kodi: System.launchDataClear(full = True)

		# Reload here if the invoker settings changed after upgrading Gaia.
		# This will cause Kodi to freeze for a bit.
		# Once reloaded, Kodi will restart all services, so this script will be called again.
		if not Settings.interpreterSelect(notification = True, silent = True):
			# Remove old settings no longer in settings.xml.
			# Do here instead of during the addon launch, since this function can fail and also takes very long.
			# The function is also more likley to work correctly here, since there are less threads writing to settings.
			Settings.clean()

			# Initialize Gaia during Kodi boot.
			if kodi:
				if self.settingAcceleration(): System.launch(hidden = True)
				if self.settingAutomatic(): System.launchAutomatic()

			# VPN Monitor
			# NB: Utilizes an infinite busy-wait thread.
			Vpn.monitor(delay = kodi, silent = True)

			# Bluetooth Monitor
			# NB: Utilizes an infinite busy-wait thread.
			Bluetooth.monitor()

			# Local Library Update Monitor
			# NB: Utilizes an infinite busy-wait thread.
			Library.monitor()

			# Context Menu
			Context.initialize(force = True, wait = False)

			# Trakt Cache
			# Retry previously failed Trakt POST requests.
			Trakt.cacheRetry(force = True, wait = False)

			# Database Cleanup
			# This can take very long for large databases.
			# Do here instead of during launch. Nothing important requires this to finish first.
			Manager.streamsDatabaseClearOld(notification = True, wait = True)
			Database.cleanAutomatic(notification = True, wait = True)

			# Wait for threads.
			# Do not timeout, since there might be various threads that should run continuously (eg: Bluetooth and Library service).
			Pool.join(timeout = False)

		Logger.log('SERVICE FINISHED: %s' % label)
