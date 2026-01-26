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

#gaiaremove
# Update (2025-06-22):
# A new Cloudscraper module (v3.0.0) has been released, which promises considrably better bypassing of newer Cloudflare challenges.
# However, the new version is still very unstable and currently does not work at all.
# Specifically this error:
#	https://github.com/VeNoMouS/cloudscraper/issues/287
#	https://github.com/VeNoMouS/cloudscraper/issues/284
# NB: The current v3 is also sync, only allowing a single CF request at a time. From the Github issues it seems that async calls are not supported. This could create a big problem during scraping?
# Stick to the old version for now.
# In a few weeks from now, once a stable release is available, do the following:
#	1. Change the default module in settings.xml to V3 (network.cloudflare.version). Check #5 below.
#	2. Change the help label of the module setting to reflect the V3 improvements.
#	3. Properley test this to see how many URLs can be bypassed - and if the blocked scrapers now work?
#	4. Change the impact of Provider.StatusCloudflare to have a lesser impact when auto-selecting providers during wizard/optimization. ProviderBase.order() and ProviderBase.optimizationRating().
#	5. Due do the new version only allowing sync (and not asyns) requests, it takes 50-70% longer to do a scrape with the 25 best torrent providers. Test this, and only make the new version thew default version if it does not cause this performance issue.
# Update (2025-12): Still no new update released.

from lib.modules.tools import Settings, Logger, Time, Subprocess, System, File, Regex
from lib.modules.external import Importer
from lib.modules.concurrency import Lock

class CloudflareException(Exception):

	def __init__(self, exception, scraper, message = 'Cloudflare Error'):
		super(CloudflareException, self).__init__(message)
		self.exception = exception
		self.scraper = scraper
		try: self.response = scraper.response
		except: self.response = None
		try: self.cookies = scraper.cookies.get_dict()
		except: self.cookies = None

class Cloudflare(object):

	# Must adhere to settings.xml.
	ModuleCfscrape = 0
	ModuleCloudscraper = 1

	# Must adhere to settings.xml.
	VersionLegacy = 0
	VersionLatest = 1

	# SSL/TLS certificates can make use of RSA or Elliptic Curve Cryptography (ECC).
	# ECC is genrally faster and more secure than RSA (or at least similar security).
	# Most certificates use RSA, but newer ones might employ ECC.
	#	https://www.cryptosys.net/pki/eccrypto.html
	#	https://github.com/tlsfuzzer/python-ecdsa/blob/master/README.md
	# To check the requirements of a SSL certificate:
	#	openssl s_client -connect example.com:443
	# To list all ECC supported on a system:
	#	openssl ecparam -list_curves
	# CloudScraper by default uses "prime256v1" if no ECC was specified. This is the most common ECC.
	# This seems to work with almost all website, except EasyNews. Only members.easynews.com, the new members-beta.easynews.com does not have this problem.
	# The following error is returned with members.easynews.com:
	#	Network Error [Error Type: Certificate | Debug: Easynews | Link: https://members.easynews.com/...] (Caused by SSLError(SSLError(1, '[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure (_ssl.c:852)')
	# This is caused by CloudScraper:
	#	self.ssl_context.set_ecdh_curve(self.ecdhCurve)
	# When using some other ECC (eg: secp521r1), or removing the statement altogether, EasyNews works fine.
	CurvePrime256v1 = 'prime256v1'
	CurveSecp384r1 = 'secp384r1'
	CurveSecp512r1 = 'secp521r1'
	CurveDefault = None

	EngineNative = 'native' # Pure Python - no additional modules required.
	EngineV8 = 'v8' # Not supported. Requires C++ code to be compiled to usue the Python module "v8eval".
	EngineJs2py = 'js2py' # Pure Python - requires "js2py", "pyjsparser", and optionally "tzlocal" and "pytz"
	EngineNodejs = 'nodejs' # External system call.
	EngineChakra = 'chakracore' # Requires external library (.so, .dylib, .dll) which is imported and called from Python.
	Engines = [ # Order according to the priority of picking one.
		{'type' : EngineJs2py,	'name' : 'Js2Py',	'reliable' : True,	'message' : None},
		{'type' : EngineNodejs,	'name' : 'NodeJs',	'reliable' : True,	'message' : 35701},
		{'type' : EngineChakra,	'name' : 'Chakra',	'reliable' : True,	'message' : 35702},
		{'type' : EngineV8,		'name' : 'V8',		'reliable' : True,	'message' : 35703},
		{'type' : EngineNative,	'name' : 'Native',	'reliable' : False,	'message' : None},
	]

	# https://www.wappalyzer.com/technologies/cdn/cloudflare/
	Links = [
		'http://example.com',
		'https://iptorrents.eu',
		'https://arma-models.ru',
		'https://www.spigotmc.org',
		'https://rlsbb.ru',
		'https://chatgpt.com',
		'https://openai.com',
		'https://shopify.com',
		'https://deepseek.com',
		'https://hostinger.com',
		'https://medium.com',
		'https://hubspot.com',
		'https://hd24bit.com',
		'https://marketplace.tonnel.network/',

		'https://yggtorrent.top',
		'https://bt4g.org/search/dummy',
		'https://ext.to/search/?q=dummy',
		'https://idope.se',
		'https://www.torrentfunk.com/all/torrents/dummy.html',
		'https://torrentquest.com/search/?q=dummy',
		'https://extratorrent.st',
		'https://magnetdl.co/search/?q=dummy',

		'https://cloudflare.com',
		'https://gitlab.com',
		'https://w3.org',
		'https://vimeo.com',

		# Domain down.

		#'http://kat.tv',
		#'https://soap2day.is',
		#'https://www.extreme-down.ninja',

		#'https://www.magnetdl.com/d/dummy/',
		#'https://btmulu.com',
		#'https://btmet.com',
		#'https://demonoid.is/files/?query=dummy',
	]

	Headers = [
		'cf-request-id',
		'cf-ray',
	]

	# https://en.wikipedia.org/wiki/List_of_HTTP_status_codes#Cloudflare
	ErrorsDefault = [
		403,
	]
	ErrorsCustom = [
		520,
		521,
		522,
		523,
		524,
		525,
		526,
		527,
		530,
	]

	DelayMinimum = 1
	DelayMaximum = 3

	# Must correspond with settings option.
	RetryMinimum = 1
	RetryMaximum = 10

	# Sometimes Gaia and Kodi stop working, because of:
	#	OSError: [Errno 24] Too many open files
	# This is sporadic and mostly happens during dev/testing where menus are constantly loaded and reloaded.
	# When executing the following command:
	#	lsof -p $(pidof kodi.bin)
	# there are 100s of CLOSE_WAIT requests:
	#	gaia:57464->server-99-86-4-35.fra6.r.cloudfront.net:https (CLOSE_WAIT)
	#	gaia:56584->webservice.fanart.tv:https (CLOSE_WAIT)
	# This post on requests says that instead of using a global Session, create a new session for every client.
	#	https://github.com/psf/requests/issues/4575
	#	https://github.com/psf/requests/issues/239
	#	https://stackoverflow.com/questions/10115126/python-requests-close-http-connection/45684352#45684352
	# The error is probably caused by reusing the sessions too often.
	# If the error is observed again, reduce ReuseLimit or disabble ReuseEnabled.
	ReuseEnabled = True
	ReuseLimit = 10 # 20 too much.
	ReuseLock = Lock()
	ReuseScrapers = {}

	Timeout = 30
	Module = None

	# Must be the same as in network.py.
	# Must have the same values as in settings.xml.
	ValidateStrict				= 3	# Full verification. If anything is wrong with the SSL, the request will fail.
	ValidateModerate			= 2	# Strict verification. Like ValidateStrict, but allows expired and incorrect-domain SSL.
	ValidateLenient				= 1	# Lenient verification. Like ValidateModerate, but uses the old insecure TLSv1 which avoids certain SSL errors (eg: sslv3 alert handshake failure).
	ValidateNone				= 0	# Not implemented yet. Not sure if it can be switched off completley. Currently will fall back to ValidateLenient.

	def __init__(self, engine = None, validate = ValidateStrict, reuse = ReuseEnabled):
		self.mEngine = engine
		self.mValidate = validate
		self.mReuse = reuse

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		Cloudflare.ReuseScrapers = {}
		Cloudflare.Module = None

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def enabled(self):
		return self._settingsEnabled()

	@classmethod
	def settingsModule(self):
		return Settings.getInteger('network.cloudflare.module')

	@classmethod
	def settingsVersion(self):
		return Settings.getInteger('network.cloudflare.version')

	@classmethod
	def settingsEngine(self, settings = True):
		from lib.modules.interface import Loader, Format, Translation, Dialog
		Loader.show()
		labels = []
		cloudflare = Cloudflare()
		engine = self._engine()
		for item in Cloudflare.Engines:
			if engine == item['type']: support = Format.fontColor(32301, Format.colorExcellent())
			elif cloudflare.supported(engine = item['type']): support = Format.fontColor(35696, Format.colorGood())
			else: support = Format.fontColor(35454, Format.colorBad())
			reliable = Translation.string(35698 if item['reliable'] else 35697)
			labels.append('%s [%s]: %s' % (Format.fontBold(item['name']), reliable, support))
		Loader.hide()
		choice = Dialog.select(title = 35690, items = labels)
		if choice >= 0:
			Loader.show()
			supported = cloudflare.supported(engine = Cloudflare.Engines[choice]['type'])
			Loader.hide()
			if supported:
				Loader.hide()
				Settings.set('network.cloudflare.engine', Cloudflare.Engines[choice]['name'])
			else:
				message = Translation.string(35700)
				if Cloudflare.Engines[choice]['message']: message += ' ' + Translation.string(Cloudflare.Engines[choice]['message'])
				Dialog.confirm(title = 35690, message = message)
		if settings: Settings.launch('network.cloudflare.engine')

	@classmethod
	def _settingsEnabled(self):
		return Settings.getBoolean('network.cloudflare.enabled')

	@classmethod
	def _settingsEngine(self):
		return Settings.getString('network.cloudflare.engine')

	@classmethod
	def _settingsRetry(self):
		return Settings.getInteger('network.cloudflare.retry')

	@classmethod
	def _engine(self, engine = None, name = False):
		if engine is None: engine = self._settingsEngine()
		engine = engine.lower()

		result = Cloudflare.EngineNative
		for item in Cloudflare.Engines:
			if item['type'] in engine or engine in item['type']:
				result = item['type']
				break

		if name:
			for item in Cloudflare.Engines:
				if result == item['type']:
					return item['name']
			return None
		else:
			return result

	def _scraper(self, engine = None, certificate = None, link = None, domain = None, curve = None):
		if certificate is None: certificate = self.mValidate
		if certificate <= Cloudflare.ValidateModerate:
			urllib3 = Importer.moduleUrllib3()
			urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
		cloudscraper = self.module()
		interpreter = self._engine(engine)

		counter = 0
		scraper = None
		if self.mReuse:
			domain = self._scraperDomain(link = link, domain = domain)
			Cloudflare.ReuseLock.acquire()
			if not engine in Cloudflare.ReuseScrapers: Cloudflare.ReuseScrapers[engine] = {}
			if not domain in Cloudflare.ReuseScrapers[engine]: Cloudflare.ReuseScrapers[engine][domain] = {}
			if not curve in Cloudflare.ReuseScrapers[engine][domain]: Cloudflare.ReuseScrapers[engine][domain][curve] = []
			if Cloudflare.ReuseScrapers[engine][domain][curve]:
				instance = Cloudflare.ReuseScrapers[engine][domain][curve].pop()
				scraper = instance['scraper']
				counter = instance['counter']
			Cloudflare.ReuseLock.release()

		if not scraper:
			if curve: scraper = cloudscraper.create_scraper(interpreter = interpreter, ssl_verify = certificate, ecdhCurve = curve)
			else: scraper = cloudscraper.create_scraper(interpreter = interpreter, ssl_verify = certificate)

		return {'scraper' : scraper, 'domain' : domain, 'counter' : counter, 'engine' : engine, 'certificate' : certificate, 'curve' : curve}

	def _scraperReuse(self, scraper, engine = None, certificate = None, link = None, domain = None, curve = None, counter = None):
		if self.mReuse:
			counter += 1
			if counter < Cloudflare.ReuseLimit:
				domain = self._scraperDomain(link = link, domain = domain)
				Cloudflare.ReuseScrapers[engine][domain][curve].append({'scraper' : scraper, 'domain' : domain, 'counter' : counter, 'engine' : engine, 'certificate' : certificate, 'curve' : curve})
			else:
				scraper.close()
		else:
			scraper.close()

	def _scraperDomain(self, link = None, domain = None):
		if domain:
			return domain
		elif link:
			from lib.modules.network import Networker
			return Networker.linkDomain(link = link, subdomain = False, topdomain = True, ip = True, scheme = False)
		return None

	@classmethod
	def _verify(self, certificate):
		return certificate >= Cloudflare.ValidateStrict

	@classmethod
	def _timeout(self):
		return Cloudflare.Timeout

	# The time to sleep between retries. Higher number of retries has a shorter delay than less retries.
	@classmethod
	def _delay(self, retry = None):
		if retry is None: retry = self._settingsRetry()
		delay = (((retry - Cloudflare.RetryMinimum) / float(Cloudflare.RetryMaximum - Cloudflare.RetryMinimum) ) * (Cloudflare.DelayMaximum - Cloudflare.DelayMinimum) + Cloudflare.DelayMinimum)
		delay = Cloudflare.DelayMaximum + Cloudflare.DelayMinimum - delay # Inverse range
		return delay

	@classmethod
	def _error(self, description, link):
		Logger.error('Cloudflare ' + description + ' [' + link + ']')

	@classmethod
	def error(self, code, data = None):
		# Some VPNs are straight out blocked by Cloudflare for some domains (eg: ExtraTorrent).
		# No captcha is shown, but Cloudflare shows an error page:
		#
		#	Error 1020
		#	Access denied
		#	What happened?
		#	This website is using a security service to protect itself from online attacks.
		#
		# <h1 class="inline-block md:block mr-2 md:mb-2 font-light text-60 md:text-3xl text-black-dark leading-tight">
		#    <span data-translate="error">Error</span>
		#    <span>1020</span>
		#  </h1>

		try:
			default = False
			custom = False
			if code in Cloudflare.ErrorsDefault: default = True
			elif code in Cloudflare.ErrorsCustom: custom = True

			if data:
				if default or custom:
					if Regex.match(data = data, expression = r'(cloudflare|_cf_chl_opt|cf-error-details)'):
						if default:
							# Do not just check the headers (eg: server: cloudflare), since some sites (eg: ApiBay when not sending GET parameters) return the same headers and 403, but it does not show the Cloudflare.
							# https://support.cloudflare.com/hc/en-us/articles/360029779472-Troubleshooting-Cloudflare-1XXX-errors
							if Regex.match(data = data, expression = r'(error(?:\s*<\/?(?:div|span)>\s*)*1\d{3}|please\s*wait\s*\.{3}|enable\s*javascript\s*and\s*cookies)'): return True
						elif custom:
							return True
			else:
				if custom: return True
		except: Logger.error()

		return False

	@classmethod
	def module(self):
		if Cloudflare.Module is None: Cloudflare.Module = Importer.moduleCloudflare()
		return Cloudflare.Module

	@classmethod
	def prepare(self):
		self.module()

	@classmethod
	def initialize(self):
		cloudflare = Cloudflare()
		if not Settings.getString('network.cloudflare.engine'):
			for item in Cloudflare.Engines:
				if cloudflare.supported(engine = item['type']):
					Settings.set('network.cloudflare.engine', item['name'])
					break

	# Detect whether or not the engine is supported on the current system.
	def supported(self, engine = None):
		if engine is None: engine = self.mEngine
		engine = self._engine(engine)

		if engine == Cloudflare.EngineNative:
			return True
		elif engine == Cloudflare.EngineV8:
			try:
				import v8eval
				v8eval.V8()
				return True
			except:
				return False
		elif engine == Cloudflare.EngineJs2py:
			try:
				js2py = Importer.moduleJs2Py()
				js2py.eval_js('')
				return True
			except:
				return False
		elif engine == Cloudflare.EngineNodejs:
			try:
				return True if Subprocess.output(['node', '-v']) else False
			except:
				return False
		elif engine == Cloudflare.EngineChakra:
			try:
				import os
				import ctypes.util
				for library in ['libChakraCore.so', 'libChakraCore.dylib', 'ChakraCore.dll']:
					if os.path.isfile(os.path.join(os.getcwd(), library)):
						if os.path.join(os.getcwd(), library):
							return True
				if ctypes.util.find_library('ChakraCore'): return True
				return False
			except:
				return False
		return False

	# Verify a single link, or calculate the percentage of bypasses with predefined links.
	def verify(self, link = None, engine = None, retry = None, timeout = None, certificate = None, curve = None, notification = False, settings = False):
		from lib.modules.interface import Loader, Format, Translation, Dialog

		if link:
			response = self.request(link = link, engine = engine, retry = retry, timeout = timeout, certificate = certificate)
			return True if (response and not self.blocked(response = response)) else False
		else:
			if notification:
				Dialog.notification(title = 35689, message = 35699, icon = Dialog.IconInformation)
				Loader.show()

			cloudscraper = self.module()
			ranks = []
			for link in Cloudflare.Links:
				if System.aborted(): break

				scraper = self._scraper(engine = engine, certificate = certificate, curve = curve)['scraper']
				if retry is None: retry = self._settingsRetry()
				if timeout is None: timeout = self._timeout()
				delay = self._delay(retry = retry)

				rank = 0
				for i in range(retry):
					if System.aborted(): break

					try:
						response = scraper.get(link, timeout = timeout)
						if not self.blocked(response = response):
							rank = max(0, 1 - (i * 0.1)) # Give lower rank if it is a retry.
							break
					except cloudscraper.exceptions.CloudflareException:
						self._error('Cloudflare Error - Retry ' + str(i + 1), link)
						if i < retry - 1: Time.sleep(delay)
					except Exception as error:
						self._error('Unknown Error', link)
						break
				ranks.append(rank)
				Time.sleep(delay)

			percent = sum(ranks) / len(ranks)

			if notification:
				colors = Format.colorGradientIncrease(100)
				label = Format.font(str(int(percent * 100)) + '%', bold = True, color = colors[int(round(percent * 99))])
				message = (Translation.string(35693) % label) + ' '
				if percent == 1: message += Translation.string(35694)
				else: message += Translation.string(35695)
				Loader.hide()
				Dialog.confirm(title = 35689, message = message)
			if settings: Settings.launch('network.cloudflare.verification')

			return percent

	# Either set a HTTP code and reponse headers dictionary, or pass in the urllib2/requests response/error object.
	@classmethod
	def blocked(self, code = None, headers = None, response = None):
		data = None
		if not response is None:
			if code is None:
				try: code = response.getcode()
				except: code = response.status_code
			if headers is None:
				try: headers = response.info().dict
				except: headers = response.headers
			data = response.text
		if code in [301, 307, 308, 429, 503]:
			for header in headers:
				if header.lower() in Cloudflare.Headers:
					return True
		if self.error(code = code, data = data): return True
		return False

	# Sometimes the bypass fails, but when retyring again it works.
	# This is due to new Cloudflare V2 challenges, which are currently returned +-80% of the time, whereas the other 20% returns old/solvable challenges.
	def request(self, link, method = None, headers = None, data = None, path = None, check = None, engine = None, retry = None, timeout = None, certificate = None, curve = None, redirect = True, log = True):
		if log: Logger.log('Trying to bypass Cloudflare [' + link + ']')
		cloudscraper = self.module()

		if certificate is None: certificate = self.mValidate

		instance = self._scraper(engine = engine, certificate = certificate, curve = curve, link = link)
		scraper = instance['scraper']

		duration = None
		if retry is None: retry = self._settingsRetry()
		if timeout is None: timeout = self._timeout()

		delay = self._delay(retry = retry)

		for i in range(retry):
			try:
				timer = Time(start = True)

				if path:
					# https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests
					file = File.write(path = path, bytes = True)
					if file:
						with scraper.request(method = 'GET' if method is None else method, url = link, headers = headers, data = data, timeout = timeout, verify = self._verify(certificate), allow_redirects = redirect, stream = True) as stream:
							stream.raise_for_status()
							if check:
								if check is True: check = 0.01
								count = 0
								for chunk in stream.iter_content(chunk_size = 8192):
									file.write(chunk)
									count += 1
									if count > 128: # After every 1MB.
										count = 0
										if System.aborted(): raise Exception('Download Aborted')
										Time.sleep(check)
							else:
								for chunk in stream.iter_content(chunk_size = 8192):
									file.write(chunk)
						file.close()
				else:
					scraper.request(method = 'GET' if method is None else method, url = link, headers = headers, data = data, timeout = timeout, verify = self._verify(certificate), allow_redirects = redirect)

				duration = timer.elapsed(milliseconds = True)
				break
			except cloudscraper.exceptions.CloudflareException as error:
				if log: self._error('Cloudflare Error - Retry ' + str(i + 1), link)
				if i < retry - 1:
					if System.aborted(): break
					Time.sleep(delay)
				else: raise CloudflareException(error, scraper)
			except Exception as error:
				if log: self._error('Unknown Error', link)
				raise CloudflareException(error, scraper)

		if duration is None: duration = timer.elapsed(milliseconds = True)

		# NB: scraper.response.cookies does not return all of the cookies.
		# Not entirley sure why, but maybe only the cookies of the last request are returned, and not all the cookies in the chain or redirection.
		# Use session.cookies to return ALL cookies.
		try: response = scraper.response
		except: response = None
		try: cookies = scraper.cookies.get_dict()
		except: cookies = None

		self._scraperReuse(**instance)

		return {'response' : response, 'cookies' : cookies, 'duration' : duration}
