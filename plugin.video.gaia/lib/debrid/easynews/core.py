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

from lib.debrid import base
from lib.modules import convert
from lib.modules import cache
from lib.modules import tools
from lib.modules import network
from lib.modules.account import Easynews as Account

class Core(base.Core):

	Id = 'easynews'
	Name = 'EasyNews'
	Abbreviation = 'E'
	Acronym = 'EN'

	Cookie = ('chickenlicker', '%s:%s')

	LinkMain = 'https://easynews.com'
	LinkLogin = 'https://account.easynews.com/index.php'
	LinkAccount = 'https://account.easynews.com/editinfo.php'
	LinkUsage = 'https://account.easynews.com/usageview.php'
	LinkPreferences = 'https://members.easynews.com/2.0/user/prefs?c=general'
	LinkMembers = 'https://members.easynews.com'

	AuthenticateHeader = 'header'
	AuthenticateCookie = 'cookie'
	AuthenticateDefault = AuthenticateHeader

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		base.Core.__init__(self, Core.Id, Core.Name, Core.LinkMain)
		self.mAccount = Account()

	##############################################################################
	# INTERNAL
	##############################################################################

	def _request(self, link, parameters = None, headers = None, cookies = None, timeout = None, username = None, password = None, authenticate = AuthenticateDefault):
		if authenticate == Core.AuthenticateHeader:
			if not headers: headers = {}
			headers.update(self.accountHeader(username = username, password = password))
		elif authenticate == Core.AuthenticateCookie:
			if not cookies: cookies = {}
			cookies.update(self.accountCookie(username = username, password = password))

		# CloudScraper by default uses "prime256v1" if no ECC was specified. This is the most common ECC.
		# This seems to work with almost all website, except EasyNews. Only members.easynews.com, the new members-beta.easynews.com does not have this problem.
		# The following error is returned with members.easynews.com:
		#	Network Error [Error Type: Certificate | Debug: Easynews | Link: https://members.easynews.com/...] (Caused by SSLError(SSLError(1, '[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure (_ssl.c:852)')
		# This is caused by CloudScraper:
		#	self.ssl_context.set_ecdh_curve(self.ecdhCurve)
		# When using some other ECC (eg: secp521r1), or removing the statement altogether, EasyNews works fine.
		# NB: This curve is also used in the EasyNews provider code.
		# More info in cloudflare.py.
		curve = None
		if Core.LinkMembers in link: curve = network.Networker.CurveSecp512r1

		return network.Networker().requestText(link = link, data = parameters, headers = headers, cookies = cookies, curve = curve, timeout = timeout)

	# Old request that uses cookies. Leave here in case EasyNews forces cookies in the future.
	'''def _request(self, link, parameters = None, httpTimeout = None, httpData = None, httpHeaders = None):
		# Place in constructor
		#self.mResult = None
		#self.mSuccess = False
		#self.mError = None
		#self.mCookies = None

		self.mResult = None
		self.mSuccess = True
		self.mError = None

		def login():
			data = {'username': self.accountUsername(), 'password': self.accountPassword(), 'submit': 'submit'}
			self.mCookies = network.Networker().requestCookies(link = Core.LinkLogin, data = data)#gaiaremove can this be done with headers?

		try:
			if not self.mCookies:
				login()
			if not self.mCookies:
				self.mSuccess = False
				self.mError = 'Login Error'
				return self.mResult

			self.mResult = network.Networker().requestText(link = link, data = parameters, cookies = self.mCookies, headers = httpHeaders, timeout = httpTimeout)

			if self.mResult and 'value="Login"' in self.mResult:
				login()
			if not self.mCookies:
				self.mSuccess = False
				self.mError = 'Login Error'
				return self.mResult

			self.mResult = network.Networker().requestText(link = link, data = parameters, cookies = self.mCookies, headers = httpHeaders, timeout = httpTimeout)

			self.mSuccess = self.mCookies and self.mResult and not 'value="Login"' in self.mResult
			if not self.mSuccess: self.mError = 'Login Error'
		except:
			toosl.Logger.error()
			self.mSuccess = False
			self.mError = 'Unknown Error'
		return self.mResult'''

	##############################################################################
	# WEBSITE
	##############################################################################

	@classmethod
	def website(self, open = False):
		link = tools.Settings.getString('internal.link.easynews', raw = True)
		if open: network.Networker.linkShow(link = link)
		return link

	@classmethod
	def vpn(self, open = False):
		link = tools.Settings.getString('internal.link.easynews.vpn', raw = True)
		if open: network.Networker.linkShow(link = link)
		return link

	##############################################################################
	# ACCOUNT
	##############################################################################

	def accountAuthenticationVerify(self, data):
		try:
			account = self.account(username = data['username'], password = data['password'], minimal = True)
			if account:
				label = account['email']
				if not label: label = account['user']
				return {Account.AttributeLabel : label, Account.AttributeVersion : self.accountVersionDetect(cached = False)}
			return None
		except:
			tools.Logger.error()
			return False

	def accountInstance(self):
		return self.mAccount

	def accountLabel(self):
		return self.mAccount.dataLabel()

	def accountUsername(self):
		return self.mAccount.dataUsername()

	def accountPassword(self):
		return self.mAccount.dataPassword()

	def accountSettings(self, enable = True):
		tools.Settings.launch('premium.easynews.enabled')

	def accountEnabled(self):
		return self.mAccount.enabled()

	def accountEnable(self, enable = True):
		self.mAccount.enable(enable = enable)

	def accountDisable(self, disable = True):
		self.mAccount.disable(disable = disable)

	def accountValid(self):
		return self.mAccount.authenticated()

	def accountVerify(self):
		return not self.account(cached = False, minimal = True) is None

	def accountVersion(self, detect = False, cached = True):
		try:
			if self.accountValid():
				return float(self.accountVersionDetect(cached = cached) if detect else self.mAccount.dataVersion())
		except: pass
		return None

	def accountVersionOld(self, detect = False, cached = True):
		version = self.accountVersion(detect = detect, cached = cached)
		return version and version < 3

	def accountVersionNew(self, detect = False, cached = True):
		version = self.accountVersion(detect = detect, cached = cached)
		return not version or version >= 3

	def accountVersionDetect(self, cached = True):
		version = 2.0
		try:
			# Either has changed, or some accounts do not have this anymore.
			'''if cached: html = cache.Cache.instance().cacheRefreshLong(self._request, Core.LinkMembers)
			else: html = cache.Cache.instance().cacheClear(self._request, Core.LinkMembers)

			version = tools.Regex.extract(data = html, expression = 'x-easynews-version.*?content\s*=\s*[\'"](.*?)[\'"]')
			if version: version = float(version)
			else: version = 2.0'''

			if cached: html = cache.Cache.instance().cacheMedium(self._request, link = Core.LinkPreferences)
			else: html = cache.Cache.instance().cacheClear(self._request, link = Core.LinkPreferences)

			version = tools.Regex.extract(data = html, expression = '<select.*?name="members2".*?>(.*?)<\/select>')
			version = tools.Regex.extract(data = version, expression = '<option.*?selected="selected".*?>(.*?)<\/option>')
			version = version.lower()

			if '2.0' in version: version = 2.0
			elif '3.0' in version: version = 3.0
			elif version == 'easynews': version = 3.0
		except: pass
		return version

	# Requests can be made either with cookies, or with Authorization headers.
	def accountCookie(self, username = None, password = None):
		if not username:
			username = self.mAccount.dataUsername()
			password = self.mAccount.dataPassword()
		return {Core.Cookie[0] : Core.Cookie[1] % (username, password)}

	# Requests can be made either with cookies, or with Authorization headers.
	def accountHeader(self, username = None, password = None):
		if not username:
			username = self.mAccount.dataUsername()
			password = self.mAccount.dataPassword()
		return network.Networker.authorizationHeader(type = network.Networker.AuthorizationBasic, username = username, password = password)

	def account(self, cached = True, minimal = False, username = None, password = None):
		account = None
		try:
			if self.accountValid() or (username and password):
				import datetime
				from lib.modules.parser import Parser
				from lib.modules import interface

				if username: accountHtml = self._request(link = Core.LinkAccount, username = username, password = password)
				elif cached: accountHtml = cache.Cache.instance().cacheShort(self._request, Core.LinkAccount)
				else: accountHtml = cache.Cache.instance().cacheClear(self._request, Core.LinkAccount)

				if accountHtml == None or accountHtml == '': raise Exception()

				unlimited = interface.Translation.string(35221)

				accountHtml = Parser(accountHtml)
				accountHtml = accountHtml.find_all('form', id = 'accountForm')[0]
				accountHtml = accountHtml.find_all('table', recursive = False)[0]

				try: accountEmail = accountHtml.find('input', {'name' : 'email'}).get('value')
				except: accountEmail = None

				accountHtml = accountHtml.find_all('tr', recursive = False)
				accountUsername = accountHtml[0].find_all('td', recursive = False)[1].getText()
				accountType = accountHtml[1].find_all('td', recursive = False)[2].getText()
				accountStatus = accountHtml[3].find_all('td', recursive = False)[2].getText()

				accountExpiration = accountHtml[2].find_all('td', recursive = False)[2].getText()
				accountTimestamp = convert.ConverterTime(accountExpiration, format = convert.ConverterTime.FormatDate).timestamp()
				accountExpiration = datetime.datetime.fromtimestamp(accountTimestamp)

				account = {
					'user' : accountUsername,
					'email' : accountEmail,
					'type' : accountType,
					'status' : accountStatus,
					'version' : self.accountVersion(detect = True), # Always redetect, since the user might have changed the version preferences.,
			 		'expiration' : {
						'timestamp' : accountTimestamp,
						'date' : accountExpiration.strftime('%Y-%m-%d'),
						'remaining' : (accountExpiration - datetime.datetime.today()).days,
					}
				}

				if not minimal:
					if cached: usageHtml = cache.Cache.instance().cacheShort(self._request, Core.LinkUsage)
					else: usageHtml = cache.Cache.instance().cacheClear(self._request, Core.LinkUsage)

					if usageHtml == None or usageHtml == '': raise Exception()

					usageHtml = Parser(usageHtml)
					usageHtml = usageHtml.find_all('div', class_ = 'table-responsive')[0]
					usageHtml = usageHtml.find_all('table', recursive = False)[0]
					usageHtml = usageHtml.find_all('tr', recursive = False)

					usageTotal = 0
					usageConsumed = None
					usageRemaining = None
					usageWeb = None
					usageNntp = None
					usageNntpUnlimited = None
					usageLoyaltyTimestamp = 0
					usageLoyaltyTime = None
					usageLoyaltyPoints = 0

					try:
						column = usageHtml[0].find_all('td', recursive = False)[1].getText()
						usageTotal = self._accountSize(column)
					except: pass

					column = usageHtml[1].find_all('td', recursive = False)[2].getText()
					if not 'unlimited' in column.lower():
						try:
							usageConsumed = self._accountSize(column)
						except: pass
						try:
							column = usageHtml[2].find_all('td', recursive = False)[2].getText()
							usageWeb = self._accountSize(column)
						except: pass

					nntp = 0
					for i in range(len(usageHtml)):
						try:
							columns = usageHtml[i].find_all('td', recursive = False)
							if 'nntp' in columns[1].getText().lower():
								try:
									column = columns[2].getText()
									usageNntp = self._accountSize(column)
									nntp += 1
								except: pass
								try:
									columns = usageHtml[i + 1].find_all('td', recursive = False)
									column = columns[2].getText()
									usageNntpUnlimited = self._accountSize(column)
									nntp += 1
								except: pass
								break
						except: pass

					try:
						column = usageHtml[3 + nntp].find_all('td', recursive = False)[2].getText()
						usageRemaining = self._accountSize(column)
					except: pass

					for row in usageHtml:
						columns = row.find_all('td', recursive = False)
						if 'loyalty' in columns[1].getText().lower():
							try:
								usageLoyalty = columns[2].getText()

								usageLoyaltyTime = tools.Regex.extract(data = usageLoyalty, expression = '(\d{4}-\d{1,2}-\d{1,2})')
								usageLoyaltyTimestamp = convert.ConverterTime(usageLoyaltyTime, format = convert.ConverterTime.FormatDate).timestamp()
								usageLoyaltyTime = datetime.datetime.fromtimestamp(usageLoyaltyTimestamp)

								usageLoyaltyPoints = float(tools.Regex.extract(data = usageLoyalty, expression = '(\d+\.\d+)'))
								usageLoyaltyDate = usageLoyaltyTime.strftime('%Y-%m-%d')
							except: pass
							break

					# New accounts have less stats and different order.
					if usageWeb is None and usageNntp is None and usageNntpUnlimited is None:
						usageRemaining = usageConsumed
						usageConsumed = usageTotal if usageTotal else 0
						usageTotal = None if usageRemaining is None else (usageRemaining + usageConsumed)

					usagePrecentageRemaining = (usageRemaining / float(usageTotal)) if usageTotal and usageRemaining else 1
					usagePrecentageConsumed = (usageConsumed / float(usageTotal)) if usageTotal and usageConsumed else 0
					usagePrecentageWeb = (usageWeb / float(usageTotal)) if usageTotal and usageWeb else 0
					usagePrecentageNntp = (usageNntp / float(usageTotal)) if usageTotal and usageNntp else 0
					usagePrecentageNntpUnlimited = (usageNntpUnlimited / float(usageTotal)) if usageTotal and usageNntpUnlimited else 0

					account.update({
						'loyalty' : {
							'time' : {
								'timestamp' : usageLoyaltyTimestamp,
								'date' : usageLoyaltyDate,
							},
							'points' : usageLoyaltyPoints,
						},
						'usage' : {
							'total' : {
								'size' : {
									'bytes' : usageTotal,
									'description' : convert.ConverterSize(float(usageTotal)).stringOptimal() if usageTotal else unlimited,
								},
							},
							'remaining' : {
								'value' : usagePrecentageRemaining,
								'percentage' : round(usagePrecentageRemaining * 100.0, 1),
								'size' : {
									'bytes' : usageRemaining,
									'description' : convert.ConverterSize(float(usageRemaining)).stringOptimal() if usageRemaining else unlimited,
								},
								'description' : '%.0f%%' % round(usagePrecentageRemaining * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
							},
							'consumed' : {
								'value' : usagePrecentageConsumed,
								'percentage' : round(usagePrecentageConsumed * 100.0, 1),
								'size' : {
									'bytes' : usageConsumed,
									'description' : convert.ConverterSize(usageConsumed).stringOptimal(),
								},
								'description' : '%.0f%%' % round(usagePrecentageConsumed * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								'web' : {
									'value' : usagePrecentageWeb,
									'percentage' : round(usagePrecentageWeb * 100.0, 1),
									'size' : {
										'bytes' : usageWeb,
										'description' : convert.ConverterSize(usageWeb).stringOptimal() if usageWeb else unlimited,
									},
									'description' : '%.0f%%' % round(usagePrecentageWeb * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								},
								'nntp' : {
									'value' : usagePrecentageNntp,
									'percentage' : round(usagePrecentageNntp * 100.0, 1),
									'size' : {
										'bytes' : usageNntp,
										'description' : convert.ConverterSize(usageNntp).stringOptimal() if usageNntp else unlimited,
									},
									'description' : '%.0f%%' % round(usagePrecentageNntp * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								},
								'nntpunlimited' : {
									'value' : usagePrecentageNntpUnlimited,
									'percentage' : round(usagePrecentageNntpUnlimited * 100.0, 1),
									'size' : {
										'bytes' : usageNntpUnlimited,
										'description' : convert.ConverterSize(usageNntpUnlimited).stringOptimal() if usageNntpUnlimited else unlimited,
									},
									'description' : '%.0f%%' % round(usagePrecentageNntpUnlimited * 100.0, 0), # Must round, otherwise 2.5% changes to 2% instead of 3%.
								},
							}
						}
					})
		except:
			tools.Logger.error()
		return account

	def _accountSize(self, data):
		value = tools.Regex.extract(data = data, expression = '\((.*?)\)')
		if value: data = value
		value = int(convert.ConverterSize.toBytes(data.replace(',', '').strip()))
		if value < 0: return None
		else: return value
