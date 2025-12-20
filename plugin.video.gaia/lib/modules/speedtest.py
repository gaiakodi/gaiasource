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

import re
import json
import time
import urllib
import random
from lib import debrid
from lib.modules import interface
from lib.modules import tools
from lib.modules import convert
from lib.modules import network
from lib.modules import api
from lib.modules.concurrency import Pool

class SpeedTester(object):

	Unknown = 'unknown'
	UnknownCapitalize = Unknown.capitalize()

	UpdateNone = None
	UpdateAsk = 'ask'
	UpdateBoth = 'both'
	UpdateManual = 'manual'
	UpdateAutomatic = 'automatic'
	UpdateDefault = UpdateNone

	PhaseLatency = 'latency'
	PhaseDownload = 'download'
	PhaseUpload = 'upload'

	def __init__(self, name, phases):
		self.mId = name.lower()
		self.mName = name
		self.mMode = None

		self.mPhases = phases
		self.mPhase = None

		self.mLatency = None
		self.mDownload = None
		self.mUpload = None

		self.mCurrent = 0
		self.mError = False

		self.mInformation = None
		self.mInformationNetwork = None

	@classmethod
	def result(self):
		return tools.Settings.getInteger('internal.speedtest')

	def latency(self):
		return self.mLatency

	def download(self, unit = None):
		if unit: return convert.ConverterSpeed(self.mDownload, unit = convert.ConverterSpeed.Bit).value(unit = unit)
		else: return self.mDownload

	def upload(self, unit = None):
		if unit: return convert.ConverterSpeed(self.mUpload, unit = convert.ConverterSpeed.Bit).value(unit = unit)
		else: return self.mUpload

	def latencySet(self, value):
		self.mLatency = value

	def downloadSet(self, value):
		self.mDownload = value

	def uploadSet(self, value):
		self.mUpload = value

	def formatLatency(self, unknown = UnknownCapitalize):
		if self.mLatency: return self._formatLatency(self.mLatency)
		else: return unknown

	def formatDownload(self, unknown = UnknownCapitalize):
		if self.mDownload: return self._formatSpeed(self.mDownload)
		else: return unknown

	def formatUpload(self, unknown = UnknownCapitalize):
		if self.mUpload: return self._formatSpeed(self.mUpload)
		else: return unknown

	def _validate(self):
		return True

	@classmethod
	def _formatLatency(self, latency):
		if not latency: # Use not to check for both None and 0.
			return SpeedTester.UnknownCapitalize
		else:
			return '%.0f ms' % latency

	@classmethod
	def _formatSpeed(self, speed):
		if not speed: # Use not to check for both None and 0.
			return SpeedTester.UnknownCapitalize
		else:
			return convert.ConverterSpeed(value = speed, unit = convert.ConverterSpeed.Bit).stringOptimal(unit = convert.ConverterSpeed.Bit, notation = convert.ConverterSpeed.SpeedLetter)

	@classmethod
	def _formatSpeedLatency(self, speed = None, latency = None, ignore = False):
		if not speed and not latency: # Use not to check for both None and 0.
			return interface.Translation.string(33387)
		else:
			if ignore:
				if not speed: return self._formatLatency(latency)
				elif not latency: return self._formatLatency(speed)
			return '%s (%s)' % (self._formatSpeed(speed), self._formatLatency(latency))

	def _formatDifference(self, local, community, formatter, colorPositive, colorNegative, colorNeutral):
		differenceLabel = ''
		if not community:
			return SpeedTester.UnknownCapitalize
		if local:
			difference = local - community
			differenceAbsolute = abs(difference)
			differenceAbsolute = formatter(differenceAbsolute)
			if difference > 0: differenceLabel = interface.Format.color('+ %s' % differenceAbsolute, colorPositive)
			elif difference < 0: differenceLabel = interface.Format.color('- %s' % differenceAbsolute, colorNegative)
			else: differenceLabel = interface.Format.color(differenceAbsolute, colorNeutral)
			differenceLabel = ' (%s)' % differenceLabel
		return '%s%s' % (formatter(community), differenceLabel)

	def _formatDifferenceLatency(self, local, community):
		return self._formatDifference(local = local, community = community, formatter = self._formatLatency, colorPositive = interface.Format.colorBad(), colorNegative = interface.Format.colorExcellent(), colorNeutral = interface.Format.colorMedium())

	def _formatDifferenceSpeed(self, local, community):
		return self._formatDifference(local = local, community = community, formatter = self._formatSpeed, colorPositive = interface.Format.colorExcellent(), colorNegative = interface.Format.colorBad(), colorNeutral = interface.Format.colorMedium())

	def _informationInternal(self, service = api.Api.ServiceNone, selection = api.Api.SelectionAverage):
		self.mInformation = self._information(service = service, selection = selection, networkInformation = True)
		if self.mInformation:
			self.mInformationNetwork = self.mInformation[1]
			self.mInformation = self.mInformation[0]
		return self.mInformation

	@classmethod
	def _information(self, service = api.Api.ServiceNone, selection = api.Api.SelectionAverage, networkInformation = False):
		try:
			geolocation = network.Geolocator.detectGlobal(anonymize = network.Geolocator.AnonymizeObfuscate)
			continent = geolocation['location']['continent']['name']
			country = geolocation['location']['country']['name']
			region = geolocation['location']['region']['name']
			city = geolocation['location']['city']['name']

			result = api.Api.speedtestRetrieve(service = service, selection = selection, continent = continent, country = country, region = region, city = city)
			if result:
				result = result[selection]
				if networkInformation: return (result, geolocation)
				else: return result
		except:
			tools.Logger.error()
		return None

	'''
		items = [
			{
				'name' : string, // Made bold
				'description' : string, // Made non-bold
				'result' : anything,
			}
		]
	'''
	@classmethod
	def _testDialog(self, options):
		if options == None or len(options) == 0:
			return None

		items = []
		for option in options:
			name = option['name'] if 'name' in option else None
			description = option['description'] if 'description' in option else None
			item = ''
			if name: item += interface.Format.bold(interface.Translation.string(name))
			if name and description: item += interface.Format.bold(': ')
			if description: item += interface.Translation.string(description)
			items.append(item)

		choice = interface.Dialog.select(title = 33030, items = items)
		if choice < 0: return None
		else: return choice

	def _testSelection(self):
		return True

	def _testLatency(self):
		return None

	def _testDownload(self):
		return None

	def _testUpload(self):
		return None

	def testLatency(self, format = False):
		try:
			self.mPhase = SpeedTester.PhaseLatency
			latency = self._testLatency()
			if latency == 0 or latency == 10000: self.mLatency = None # Global speed test failures lasts a maximum of 10 secs.
			else: self.mLatency = latency
			if format: latency = self._formatLatency(latency)
			return latency
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def testDownload(self, format = False):
		try:
			self.mPhase = SpeedTester.PhaseDownload
			download = self._testDownload()
			if download == 0:
				self.mDownload = None
			elif not download is None:
				tools.Settings.set('internal.speedtest', int(download))
				self.mDownload = download
			if format: download = self._formatSpeed(download)
			return download
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def testUpload(self, format = False):
		try:
			self.mPhase = SpeedTester.PhaseUpload
			upload = self._testUpload()
			if upload == 0: self.mUpload = None
			else: self.mUpload = upload
			if format: upload = self._formatSpeed(upload)
			return upload
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def test(self, format = True, full = True):
		self.mPhase = None
		self.mError = False
		self.mCurrent = 0
		result = {}

		if full and SpeedTester.PhaseLatency in self.mPhases:
			self.mCurrent += 1
			result[SpeedTester.PhaseLatency] = self.testLatency(format)
		if SpeedTester.PhaseDownload in self.mPhases:
			self.mCurrent += 1
			result[SpeedTester.PhaseDownload] = self.testDownload(format)
		if full and SpeedTester.PhaseUpload in self.mPhases:
			self.mCurrent += 1
			result[SpeedTester.PhaseUpload] = self.testUpload(format)

		return result

	@classmethod
	def select(self, update = UpdateNone, full = True):
		options = [
			{
				'name' : interface.Translation.string(33509) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterGlobal(),
			},
			{
				'name' : interface.Translation.string(33566) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterPremiumize(),
			},
			{
				'name' : interface.Translation.string(35200) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterOffCloud(),
			},
			{
				'name' : interface.Translation.string(33567) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterRealDebrid(),
			},
			{
				'name' : interface.Translation.string(33794) + ' ' + interface.Translation.string(33030),
				'result' : SpeedTesterEasyNews(),
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False
		options[choice]['result'].show(update = update, full = full)
		return options[choice]['result']

	def show(self, update = UpdateDefault, full = True):
		self.mMode = self._testSelection()
		if self.mMode == False: return
		try: self.mMode = self.mMode.lower()
		except: self.mMode = None

		if not self._validate(): return

		self.mPhase = None
		self.mError = False

		title = 'Speed Test'
		message = 'Testing the internet connection %s:'
		info = message % 'capabilities'
		progressDialog = interface.Dialog.progress(title = title, message = info)

		dots = ''
		stringLatency = '%s     %s: ' % (interface.Format.fontNewline(), interface.Translation.string(33858))
		stringSpeedDownload = '%s     %s: ' % (interface.Format.fontNewline(), interface.Translation.string(33074))
		stringSpeedUpload = '%s     %s: ' % (interface.Format.fontNewline(), interface.Translation.string(33859))

		threadInformation = Pool.thread(target = self._informationInternal, args = (self.mId,))
		threadInformation.start()

		thread = Pool.thread(target = self.test, args = (True, full))
		thread.start()

		while True:
			try:
				if self.mError: break
				try:
					# NB: Do not check for abort here. This will cause the speedtest to close automatically in the configuration wizard.
					if progressDialog.iscanceled(): return None
				except: pass

				if self.mPhase == SpeedTester.PhaseLatency:
					info = message % 'latency'
				elif self.mPhase == SpeedTester.PhaseDownload:
					info = message % 'download speed'
				elif self.mPhase == SpeedTester.PhaseUpload:
					info = message % 'upload speed'
				else:
					info = message % 'capabilities'

				dots += '.'
				if len(dots) > 3: dots = ''

				if self.mPhase == SpeedTester.PhaseLatency:
					if full and SpeedTester.PhaseLatency in self.mPhases:
						info += stringLatency + dots
				elif self.mPhase == SpeedTester.PhaseDownload:
					if full and SpeedTester.PhaseLatency in self.mPhases:
						info += stringLatency + self._formatLatency(self.mLatency)
					if SpeedTester.PhaseDownload in self.mPhases:
						info += stringSpeedDownload + dots
				elif self.mPhase == SpeedTester.PhaseUpload:
					if full and SpeedTester.PhaseLatency in self.mPhases:
						info += stringLatency + self._formatLatency(self.mLatency)
					if SpeedTester.PhaseDownload in self.mPhases:
						info += stringSpeedDownload + self._formatSpeed(self.mDownload)
					if full and SpeedTester.PhaseUpload in self.mPhases:
						info += stringSpeedUpload + dots

				lines = 4 - info.count(interface.Format.fontNewline())
				for i in range(max(0, lines)):
					info += interface.Format.fontNewline()

				try: progressDialog.update(int((max(0, self.mCurrent - 1) / len(self.mPhases)) * 100), info)
				except: pass

				if not thread.is_alive(): break
				if self.mError: break
				time.sleep(0.5)
			except:
				tools.Logger.error()

		interface.Loader.show()
		threadInformation.join()
		interface.Loader.hide()

		try: progressDialog.close()
		except: pass

		if self.mError:
			interface.Dialog.confirm(title = title, message = 'The internet connection can currently not be tested. Please try again later.')
		elif full:
			items = []

			itemsCategory = []
			if SpeedTester.PhaseLatency in self.mPhases:
				itemsCategory.append({ 'title' : 33858, 'value' : self._formatLatency(self.mLatency) })
			if SpeedTester.PhaseDownload in self.mPhases:
				itemsCategory.append({ 'title' : 33074, 'value' : self._formatSpeed(self.mDownload) })
			if SpeedTester.PhaseUpload in self.mPhases:
				itemsCategory.append({ 'title' : 33859, 'value' : self._formatSpeed(self.mUpload) })
			items.append({'title' : 33860, 'items' : itemsCategory})

			if self.mInformation:
				areas = ['international', 'continent', 'country', 'region', 'city']
				titles = [33861, 33862, 33863, 33864, 33865]
				networkInformation = self.mInformationNetwork['location']

				for i in range(len(titles)):
					itemsCategory = []

					if areas[i] in networkInformation:
						location = networkInformation[areas[i]]['name']
						if not location: location = SpeedTester.UnknownCapitalize
						itemsCategory.append({ 'title' : 33874, 'value' : location })

					area = self.mInformation[areas[i]]

					if SpeedTester.PhaseLatency in self.mPhases:
						itemsCategory.append({ 'title' : 33858, 'value' : self._formatDifferenceLatency(local = self.mLatency, community = area[self.mId]['latency']) })
					if SpeedTester.PhaseDownload in self.mPhases:
						itemsCategory.append({ 'title' : 33074, 'value' : self._formatDifferenceSpeed(local = self.mDownload, community = area[self.mId]['download']) })
					if SpeedTester.PhaseUpload in self.mPhases:
						itemsCategory.append({ 'title' : 33859, 'value' : self._formatDifferenceSpeed(local = self.mUpload, community = area[self.mId]['upload']) })
					items.append({'title' : titles[i], 'items' : itemsCategory})

			# Dialog
			interface.Loader.hide()
			interface.Dialog.information(title = 33030, items = items)

			# Sharing
			if not interface.Dialog.option(title = 33845, message = 33847, labelConfirm = 33743, labelDeny = 33880): self._share()

	@classmethod
	def comparison(self, force = False):
		try:
			interface.Loader.show()
			result = self._information(networkInformation = True)
			networkInformation = result[1]['location']
			result = result[0]
			items = []

			international = result['international']
			items.append({
				'title' : interface.Translation.string(33853),
				'items' : [
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = international['global']['download'], latency = international['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = international['premiumize']['download'], latency = international['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = international['offcloud']['download'], latency = international['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = international['realdebrid']['download'], latency = international['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = international['easynews']['download'], latency = international['easynews']['latency']) },
				]
			})

			continent = result['continent']
			items.append({
				'title' : interface.Translation.string(33713),
				'items' : [
					{ 'title' : 33874, 'value' : networkInformation['continent']['name'] },
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = continent['global']['download'], latency = continent['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = continent['premiumize']['download'], latency = continent['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = continent['offcloud']['download'], latency = continent['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = continent['realdebrid']['download'], latency = continent['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = continent['easynews']['download'], latency = continent['easynews']['latency']) },
				]
			})

			country = result['country']
			items.append({
				'title' : interface.Translation.string(33714),
				'items' : [
					{ 'title' : 33874, 'value' : networkInformation['country']['name'] },
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = country['global']['download'], latency = country['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = country['premiumize']['download'], latency = country['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = country['offcloud']['download'], latency = country['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = country['realdebrid']['download'], latency = country['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = country['easynews']['download'], latency = country['easynews']['latency']) },
				]
			})

			region = result['region']
			items.append({
				'title' : interface.Translation.string(33715),
				'items' : [
					{ 'title' : 33874, 'value' : networkInformation['region']['name'] },
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = region['global']['download'], latency = region['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = region['premiumize']['download'], latency = region['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = region['offcloud']['download'], latency = region['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = region['realdebrid']['download'], latency = region['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = region['easynews']['download'], latency = region['easynews']['latency']) },
				]
			})

			city = result['city']
			items.append({
				'title' : interface.Translation.string(33716),
				'items' : [
					{ 'title' : 33874, 'value' : networkInformation['city']['name'] },
					{ 'title' : 33509, 'value' : self._formatSpeedLatency(speed = city['global']['download'], latency = city['global']['latency']) },
					{ 'title' : 33566, 'value' : self._formatSpeedLatency(speed = city['premiumize']['download'], latency = city['premiumize']['latency']) },
					{ 'title' : 35200, 'value' : self._formatSpeedLatency(speed = city['offcloud']['download'], latency = city['offcloud']['latency']) },
					{ 'title' : 33567, 'value' : self._formatSpeedLatency(speed = city['realdebrid']['download'], latency = city['realdebrid']['latency']) },
					{ 'title' : 33794, 'value' : self._formatSpeedLatency(speed = city['easynews']['download'], latency = city['easynews']['latency']) },
				]
			})

			# Dialog
			interface.Loader.hide()
			interface.Dialog.information(title = 33030, items = items)
		except:
			tools.Logger.error()
			interface.Loader.hide()
			interface.Dialog.notification(title = 33030, message = 33852, icon = interface.Dialog.IconError)

	def _share(self):
		thread = Pool.thread(target = self._shareBackground)
		thread.start()

	def _shareBackground(self):
		try:
			data = self.mInformationNetwork if self.mInformationNetwork else network.Geolocator.detectGlobal(anonymize = network.Geolocator.AnonymizeObfuscate)

			data['type'] = {
				'service' : self.mId,
				'mode' : self.mMode,
			}
			data['measurement'] = {
				'latency' : {
					'value' : self.mLatency,
					'description' : self._formatLatency(self.mLatency),
				},
				'download' : {
					'value' : self.mDownload,
					'description' : None if self.mDownload == None else self._formatSpeed(self.mDownload),
				},
				'upload' : {
					'value' : self.mUpload,
					'description' : None if self.mUpload == None else self._formatSpeed(self.mUpload),
				},
			}

			api.Api.speedtestAdd(data = data)
		except:
			tools.Logger.error()
			#interface.Dialog.notification(title = 33030, message = 33843, icon = interface.Dialog.IconError)

class SpeedTesterGlobal(SpeedTester):

	Name = 'Global'

	def __init__(self):
		SpeedTester.__init__(self, name = SpeedTesterGlobal.Name, phases = [self.PhaseLatency, self.PhaseDownload, self.PhaseUpload])
		self.mTester = None
		self.mServer = None
		self.mCity = None

	def _testSelection(self):
		# Since 2020, SpeedTest does not return all servers anymore.
		# Instead the 100 closest servers are returned.
		# https://sparanoid.com/lab/speedtest-list/
		return 'automatic'

		'''options = [
			{
				'name' : 33800,
				'result' : 'automatic',
			},
			{
				'name' : 'Argentina',
				'result' : 'buenos aires',
			},
			{
				'name' : 'Austria',
				'result' : 'vienna',
			},
			{
				'name' : 'Australia',
				'result' : 'sydney',
			},
			{
				'name' : 'Belgium',
				'result' : 'brussels',
			},
			{
				'name' : 'Brazil',
				'result' : 'rio de janeiro',
			},
			{
				'name' : 'Canada',
				'result' : 'toronto',
			},
			{
				'name' : 'China',
				'result' : 'beijing',
			},
			{
				'name' : 'Colombia',
				'result' : 'bogota',
			},
			{
				'name' : 'Czech Republic',
				'result' : 'prague',
			},
			{
				'name' : 'Denmark',
				'result' : 'copenhagen',
			},
			{
				'name' : 'Egypt',
				'result' : 'cairo',
			},
			{
				'name' : 'Finland',
				'result' : 'helsinki',
			},
			{
				'name' : 'France',
				'result' : 'paris',
			},
			{
				'name' : 'Germany',
				'result' : 'berlin',
			},
			{
				'name' : 'Greece',
				'result' : 'athens',
			},
			{
				'name' : 'Greenland',
				'result' : 'nuuk',
			},
			{
				'name' : 'Hong Kong',
				'result' : 'hong kong',
			},
			{
				'name' : 'Hungary',
				'result' : 'budapest',
			},
			{
				'name' : 'Iceland',
				'result' : 'reykjavik',
			},
			{
				'name' : 'India',
				'result' : 'new delhi',
			},
			{
				'name' : 'Indonesia',
				'result' : 'jakarta',
			},
			{
				'name' : 'Israel',
				'result' : 'jerusalem',
			},
			{
				'name' : 'Italy',
				'result' : 'rome',
			},
			{
				'name' : 'Japan',
				'result' : 'tokyo',
			},
			{
				'name' : 'Mexico',
				'result' : 'mexico city',
			},
			{
				'name' : 'Netherlands',
				'result' : 'amsterdam',
			},
			{
				'name' : 'New Zealand',
				'result' : 'auckland',
			},
			{
				'name' : 'Nigeria',
				'result' : 'abuja',
			},
			{
				'name' : 'Norway',
				'result' : 'oslo',
			},
			{
				'name' : 'Pakistan',
				'result' : 'islamabad',
			},
			{
				'name' : 'Philippines',
				'result' : 'manila',
			},
			{
				'name' : 'Poland',
				'result' : 'warsaw',
			},
			{
				'name' : 'Portugal',
				'result' : 'lisbon',
			},
			{
				'name' : 'Russia',
				'result' : 'moscow',
			},
			{
				'name' : 'Singapore',
				'result' : 'singapore',
			},
			{
				'name' : 'South Africa',
				'result' : 'johannesburg',
			},
			{
				'name' : 'South Korea',
				'result' : 'seoul',
			},
			{
				'name' : 'Spain',
				'result' : 'barcelona',
			},
			{
				'name' : 'Sweden',
				'result' : 'stockholm',
			},
			{
				'name' : 'Switzerland',
				'result' : 'zurich',
			},
			{
				'name' : 'Taiwan',
				'result' : 'taipei',
			},
			{
				'name' : 'Turkey',
				'result' : 'istanbul',
			},
			{
				'name' : 'Ukraine',
				'result' : 'kiev',
			},
			{
				'name' : 'United Kingdom',
				'result' : 'london',
			},
			{
				'name' : 'United States Central',
				'result' : 'denver',
			},
			{
				'name' : 'United States East',
				'result' : 'new york',
			},
			{
				'name' : 'United States West',
				'result' : 'san francisco',
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False
		self.mCity = None if options[choice]['result'] == 'automatic' else options[choice]['result']
		return options[choice]['result'].replace(' ', '').lower()'''

	def _filter(self, items):
		result = []
		if tools.Tools.isArray(items):
			for item in items:
				result.extend(self._filter(item))
		elif tools.Tools.isDictionary(items):
			if 'url' in items and 'name' in items:
				result.append(items)
			else:
				for item in items.values():
					result.extend(self._filter(item))
		return result

	def _serverName(self, city):
		city = city.lower()
		index = city.find(',')
		if index >= 0: city = city[:index]
		return city.strip()

	def _server(self):
		try:
			if not self.mTester:
				from lib.modules.external import Importer
				Speedtest = Importer.moduleSpeedTest()
				error = False
				for i in range(5):
					# Sometimes error 503 is returned. Try a few times.
					# If used too many times, can also return a 403 error.
					try:
						self.mTester = Speedtest()
						break
					except:
						if not error: tools.Logger.error()
						error = True
						time.sleep(1)

				if not self.mTester:
					self.mError = True
					return None

			if self.mServer:
				return self.mServer
			else:
				result = []
				servers = self.mTester.get_servers()
				servers = self._filter(servers)
				names = [self._serverName(server['name']) for server in servers]

				if self.mCity:
					selections = [self._serverName(self.mCity)]
				else:
					selections = ['new york', 'london', 'berlin', 'moscow', 'johannesburg', 'tokyo', 'sydney', 'rio de janeiro']

				serverSelections = []
				self.mMode = None
				for selection in selections:
					for i in range(len(names)):
						if selection == names[i]:
							if self.mMode == None: self.mMode = selection.replace(' ', '').lower()
							serverSelections.append(servers[i])

				if len(serverSelections) == 0:
					# Since 2020, SpeedTest does not return all servers anymore.
					# Instead the 100 closest servers are returned.
					# https://sparanoid.com/lab/speedtest-list/
					if self.mCity: interface.Dialog.notification(title = 33030, message = 'No server found in this location. Using the closest server instead.', icon = interface.Dialog.IconWarning)
					result = self._filter(self.mTester.get_closest_servers())
				else:
					# Select a random server. In case one fails, it will pick a different one during the next test.
					result.append(random.choice(serverSelections))
				try:
					self.mServer = self.mTester.get_best_server(result)
					return self.mServer
				except:
					tools.Logger.error()
				return None
		except:
			tools.Logger.error()
			self.mError = True

	def _testLatency(self):
		try:
			server = self._server()
			if server and 'latency' in server:
				return server['latency']
			else:
				self.mError = True
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def _testDownload(self):
		try:
			server = self._server()
			if server:
				return self.mTester.download()
			else:
				self.mError = True
		except:
			tools.Logger.error()
			self.mError = True
		return None

	def _testUpload(self):
		try:
			server = self._server()
			if server:
				return self.mTester.upload()
			else:
				self.mError = True
		except:
			tools.Logger.error()
			self.mError = True
		return None

class SpeedTesterDebrid(SpeedTester):

	# Not all hosters have the same download speed on debrid services (or at least on Premiumize). Or maybe this is just random?
	Links = [
		'https://rapidgator.net/file/7c181bd538274a439395197f05253fd6/gaia.dat.html',
		'https://uptobox.com/hwgg3sy1cxmy',
		'https://1fichier.com/?0fd0zhn3avcqqk6xojkx',
		'https://www.mediafire.com/file/kj6yt2jj3tsr2jt/gaia.dat/file',
		'https://drop.download/5o15rwss1im0',
		'https://clicknupload.club/npwnxrq3i461',
		'https://www.youtube.com/watch?v=1jiP1iJf2Ac',
	]

	LatencyTotal = 10 # How many time to do the latency test. Must be a lot, otherwise the average is not good.
	LatencyCount = 5 # The number of last tests to calculate the mean latency from.

	def __init__(self, name, link = None):
		SpeedTester.__init__(self, name = name, phases = [self.PhaseLatency, self.PhaseDownload])
		self.mLink = link
		self.mLinks = None

	def _testLatency(self):
		latencies = []
		for i in range(SpeedTesterDebrid.LatencyTotal):
			response = network.Networker().request(method = network.Networker.MethodHead, link = self.mLink, process = False)
			latencies.append(response['duration']['connection'])

		latencies.sort()
		last = latencies[:SpeedTesterDebrid.LatencyCount]
		self.mLatency = int(sum(last) / float(len(last)))

		return self.mLatency

	def _testLink(self, link):
		return None

	def _testDownload(self):
		try:
			links = SpeedTesterDebrid.Links if self.mLinks == None else self.mLinks
			link = None
			for i in links:
				result = self._testLink(i)
				try:
					if network.Networker.linkIs(result): # Direct/main link.
						link = result
					elif result['success']:
						link = result['link']
						break
					elif result['error'] == debrid.realdebrid.Core.ErrorBlocked: # Blocked RealDebrid IP address.
						return None
				except: pass
			if not network.Networker.linkIs(link): # Errors returned by debrid, eg: ErrorRealDebrid
				return None

			response = network.Networker().request(link = link, process = False)

			#size = len(response['data']) if response['data'] else 0 # Does not work anymore, since we use "process = False" above.
			try: size = int(response['headers'][network.Networker.HeaderContentLength])
			except: size = 0

			try: duration = int(response['duration']['request'])
			except: duration = 0

			return int((size * 8) / (duration / 1000.0)) if duration else 0
		except:
			tools.Logger.error()
			return None

class SpeedTesterPremiumize(SpeedTesterDebrid):

	Name = 'Premiumize'

	Link = 'https://premiumize.me'
	LinkServer = 'http://mirror.nforce.com/pub/speedtests/25mb.bin'

	def __init__(self):
		SpeedTesterDebrid.__init__(self, name = SpeedTesterPremiumize.Name, link = SpeedTesterPremiumize.Link)

	def _testSelection(self):
		options = [
			{
				'identifier' : 'main',
				'name' : 33668,
			},
			{
				'identifier' : 'streaming',
				'name' : 33667,
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False
		if choice == 0: self.mLinks = [SpeedTesterPremiumize.LinkServer]
		return options[choice]['identifier']

	def _testLink(self, link):
		if link == SpeedTesterPremiumize.LinkServer:
			return link
		else:
			return debrid.premiumize.Core().add(link)

	def _validate(self):
		if not self.mLinks == None and not len(self.mLinks) == 0 and self.mLinks[0] == SpeedTesterPremiumize.LinkServer or debrid.premiumize.Core().accountValid():
			return True
		else:
			name = interface.Translation.string(33566)
			message = interface.Translation.string(33640) % name
			interface.Dialog.confirm(title = name, message = message)
			return False

class SpeedTesterOffCloud(SpeedTesterDebrid):

	Name = 'OffCloud'

	# https://offcloud.com/api/speedtest
	Link = 'https://fr-4.offcloud.com'
	LinkServer = 'https://fr-4.offcloud.com/test10MB.zip'

	def __init__(self):
		SpeedTesterDebrid.__init__(self, name = SpeedTesterOffCloud.Name, link = SpeedTesterOffCloud.Link)

	def _testSelection(self):
		options = [
			{
				'identifier' : 'main',
				'name' : 33668,
			},
			{
				'identifier' : 'streaming',
				'name' : 33667,
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False
		if choice == 0: self.mLinks = [SpeedTesterOffCloud.LinkServer]
		return options[choice]['identifier']

	def _testLink(self, link):
		if link == self.LinkServer:
			return link
		else:
			return debrid.offcloud.Core().add(link)

	def _validate(self):
		if not self.mLinks == None and not len(self.mLinks) == 0 and self.mLinks[0] == SpeedTesterOffCloud.LinkServer or debrid.offcloud.Core().accountValid():
			return True
		else:
			name = interface.Translation.string(35200)
			message = interface.Translation.string(33640) % name
			interface.Dialog.confirm(title = name, message = message)
			return False

class SpeedTesterRealDebrid(SpeedTesterDebrid):

	Name = 'RealDebrid'

	Link = 'https://real-debrid.com'

	def __init__(self):
		SpeedTesterDebrid.__init__(self, name = SpeedTesterRealDebrid.Name, link = SpeedTesterRealDebrid.Link)

	def _testLink(self, link):
		return debrid.realdebrid.Core().add(link)

	def _validate(self):
		if debrid.realdebrid.Core().accountValid():
			return True
		else:
			name = interface.Translation.string(33567)
			message = interface.Translation.string(33640) % name
			interface.Dialog.confirm(title = name, message = message)
			return False

class SpeedTesterEasyNews(SpeedTester):

	Name = 'EasyNews'

	Download = '/test/20M?_=' # Use more than 10MB for more accurate measurement.

	LinkUsWest = 'https://iad-dl-01.easynews.com'
	LinkUsEast = 'https://lax-dl-01.easynews.com'
	LinkEurope = 'https://fra-dl-01.easynews.com'

	LatencyTotal = 10 # How many time to do the latency test. Must be a lot, otherwise the average is not good.
	LatencyCount = 5 # The number of last tests to calculate the mean latency from.

	def __init__(self):
		SpeedTester.__init__(self, name = SpeedTesterEasyNews.Name, phases = [self.PhaseLatency, self.PhaseDownload])
		self.mLinkLatency = None
		self.mLinkDownload = None

	def _testLatency(self):
		latencies = []
		for i in range(SpeedTesterEasyNews.LatencyTotal):
			response = network.Networker().request(method = network.Networker.MethodHead, link = self.mLinkLatency, process = False)
			latencies.append(response['duration']['connection'])

		latencies.sort()
		last = latencies[:SpeedTesterEasyNews.LatencyCount]
		self.mLatency = int(sum(last) / float(len(last)))

		return self.mLatency

	def _testDownload(self):
		response = network.Networker().request(link = self.mLinkDownload, process = False)

		#size = len(response['data']) if response['data'] else 0 # Does not work anymore, since we use "process = False" above.
		try: size = int(response['headers'][network.Networker.HeaderContentLength])
		except: size = 0

		try: duration = int(response['duration']['request'])
		except: duration = 0

		return int((size * 8) / (duration / 1000.0)) if duration else 0

	def _testSelection(self):
		options = [
			{
				'identifier' : 'europe',
				'name' : 33799,
				'result' : SpeedTesterEasyNews.LinkEurope,
			},
			{
				'identifier' : 'unitedstateseast',
				'name' : 33797,
				'result' : SpeedTesterEasyNews.LinkUsEast,
			},
			{
				'identifier' : 'unitedstateswest',
				'name' : 33798,
				'result' : SpeedTesterEasyNews.LinkUsWest,
			},
		]
		choice = self._testDialog(options)
		if choice == None: return False

		timestamp = str(tools.Time.timestamp() * 1000) # Uses millisecond timestamp
		self.mLinkLatency = options[choice]['result']
		self.mLinkDownload = options[choice]['result'] + SpeedTesterEasyNews.Download + timestamp

		return options[choice]['identifier']
