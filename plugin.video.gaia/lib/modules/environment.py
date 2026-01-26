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

# Do not import any Gaia modules here, since this is called from script.module.external.

# Kodi can now run as a Flatpak container.
# At least for Linux, it seems that Kodi has now officially moved over to Flatpak completely, and PPA repositories are not maintained/updated anymore.
#	https://kodi.tv/article/ubuntu-team-kodi-ppa-officially-retired/
# Flatpak runs with isolated app-island sandboxing environments, which has the following implications:
#	1. Files
#		Files outside the app-island (the Kodi data dir, eg: ~/.var/app/tv.kodi.Kodi/...) cannot be accessed anymore.
#		This should not be an issue, since Gaia does not access any files outside this directory.
#		For dev purposes, if other directories have to be accessed (eg: /tmp), simply do one of the following:
#			a. Permanently add the path to the Kodi permissions using Flatseal: flatpak run com.github.tchx84.Flatseal
#			b. Launch Kodi with additional parameters: flatpak --filesystem=/tmp run tv.kodi.Kodi
#	2. Commands
#		System commands cannot be executed anymore.
#		This should not break anything in Gaia, but some optional features will not work (eg: copy to clipboard, or measuring the network speed during buffering).
#		In order to still allow these calls, do one of the following:
#			a. Permanently enable the "D-Bus session bus" permission using Flatseal: flatpak run com.github.tchx84.Flatseal
#			b. Launch Kodi with additional parameters: flatpak --talk-name=org.freedesktop.Flatpak run tv.kodi.Kodi
#			c. Launch Kodi with additional parameters: flatpak --socket=session-bus run tv.kodi.Kodi
#		Then Python subprocess calls can be made with:
#			flatpak-spawn --host <command>
#		Note that this essentially removes the sandboxing security features and allows Kodi to make any system call.
#		Users should only do this if they know what they are doing, or if the sandboxing security does not matter.

class Environment(object):

	TypeNone		= None
	TypeFlatpak		= 'flatpak'

	Types			= {
						TypeNone : {
							'type'		: TypeNone,
							'name'		: 'Default',
							'label'		: 'Default',
							'command'	: None,
						},
						TypeFlatpak : {
							'type'		: TypeFlatpak,
							'name'		: 'Flatpak',
							'label'		: 'Container (Flatpak)',
							'command'	: ['flatpak-spawn', '--host'],
						},
					}

	SettingMode		= 'general.enviroment.command'
	SettingCustom	= 'general.enviroment.command.custom'
	SettingTest		= 'general.enviroment.command.test'

	Data			= None
	Enabled			= None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		Environment.Data = None
		if settings: Environment.Enabled = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def data(self):
		return self._detect()

	@classmethod
	def _detect(self):
		# https://stackoverflow.com/questions/75274925/is-there-a-way-to-find-out-if-i-am-running-inside-a-flatpak-appimage-or-another
		if Environment.Data is None:
			from os import environ
			environment = (environ.get('container') or '').lower()
			if environment == 'flatpak': data = Environment.Types[Environment.TypeFlatpak]
			else: data = Environment.Types[Environment.TypeNone]
			Environment.Data = data
		return Environment.Data

	##############################################################################
	# TYPE
	##############################################################################

	@classmethod
	def type(self):
		try: return self.data().get('type')
		except: return Environment.TypeNone

	@classmethod
	def typeNone(self):
		return self.type() == Environment.TypeNone

	@classmethod
	def typeFlatpak(self):
		return self.type() == Environment.TypeFlatpak

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def name(self):
		try: return self.data().get('name')
		except: return Environment.Types[Environment.TypeNone]['name']

	@classmethod
	def label(self):
		try: return self.data().get('label')
		except: return Environment.Types[Environment.TypeNone]['label']

	##############################################################################
	# ENABLED
	##############################################################################

	@classmethod
	def enabled(self):
		if Environment.Enabled is None:
			# Do not use Gaia's Setting class here, since it is called from script.modules.externals.
			from lib.modules.tools import System
			addon = System.addon()

			mode = addon.getSettingInt(Environment.SettingMode)
			if mode == 1: Environment.Enabled = True
			elif mode == 2: Environment.Enabled = addon.getSettingString(Environment.SettingCustom)
			elif mode == 3: Environment.Enabled = Environment.Types.get(Environment.TypeFlatpak).get('command')
			else: Environment.Enabled = False

		return Environment.Enabled

	##############################################################################
	# TEST
	##############################################################################

	@classmethod
	def test(self, interface = True, settings = False):
		from lib.modules.tools import Subprocess, Settings
		from lib.modules.interface import Dialog, Translation

		# Do not use a basic command, like "echo" or "ls", since they also work without the special permissions.
		# Also try to use a command that is available on multiple platforms (Linux, Mac, Windows, etc).
		result = Subprocess.output('ping -h')
		if result:
			result = result.lower()
			result = any(i in result for i in ['ipv4', 'ipv6', 'ttl', 'dns', 'timeout', 'resolve', 'source address'])
		else:
			result = False

		Settings.set(id = Environment.SettingTest, value = Translation.string(33025 if result else 33023))
		if interface: Dialog.confirm(title = 36626, message = 36628 if result else 36629)
		if settings: Settings.launch(id = Environment.SettingTest)

		return result

	##############################################################################
	# COMMAND
	##############################################################################

	@classmethod
	def command(self, command):
		if command:
			try:
				enabled = self.enabled()
				if enabled:
					wrapper = None
					if Environment.Enabled is True:
						data = self.data()
						if data: wrapper = data.get('command')
					else:
						wrapper = enabled
					if wrapper:
						if isinstance(wrapper, (list, tuple)):
							if isinstance(command, (list, tuple)): command = wrapper + command
							else: command = ' '.join(wrapper) + ' ' + command
						else:
							try: command = wrapper % command
							except: command = wrapper + ' ' + command
			except: pass
		return command
