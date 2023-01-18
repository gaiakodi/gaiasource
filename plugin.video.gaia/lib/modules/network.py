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
from lib.modules.external import Importer
from lib.modules.concurrency import Lock, Semaphore

try:
	from urllib.parse import urlparse, urlsplit, urlencode, parse_qs, quote, quote_plus, unquote, unquote_plus
except:
	from urlparse import urlparse, urlsplit, parse_qs
	from urllib import urlencode, quote, quote_plus, unquote, unquote_plus

class Networker(object):

	MethodGet					= 'GET'
	MethodPost					= 'POST'
	MethodPut					= 'PUT'
	MethodDelete				= 'DELETE'
	MethodHead					= 'HEAD'

	DataNone					= None
	DataPost					= 'post'
	DataJson					= 'json'
	DataForm					= 'form'
	DataMulti					= 'multi'

	AgentNone					= None
	AgentAddon					= 'addon'
	AgentDesktopRandom			= 'desktoprandom'
	AgentDesktopFixed			= 'desktopfixed'
	AgentMobileRandom			= 'mobilerandom'
	AgentMobileFixed			= 'mobilefixed'
	AgentSession				= 'session'
	AgentData					= {}

	MimeJson					= 'application/json'
	MimeMulti					= 'multipart/form-data'
	MimeForm					= 'application/x-www-form-urlencoded'

	# https://webcheatsheet.com/html/character_sets_list.php
	CharsetUtf8					= 'utf-8'
	CharsetWin1251				= 'windows-1251'

	HeaderAuthorization			= 'Authorization'
	HeaderUserAgent				= 'User-Agent'
	HeaderContentType			= 'Content-Type'
	HeaderContentLength			= 'Content-Length'
	HeaderContentDisposition	= 'Content-Disposition'
	HeaderReferer				= 'Referer'
	HeaderCookie				= 'Cookie'
	HeaderLocation				= 'Location'
	HeaderRange					= 'Range'
	HeaderRequestToken			= 'X-Request-Token'
	HeaderAcceptLanguage		= 'Accept-Language'
	HeaderAcceptEncoding		= 'Accept-Encoding'

	CookiePhp					= 'PHPSESSID'

	# More info in cloudflare.py.
	CurvePrime256v1				= 'prime256v1'
	CurveSecp384r1				= 'secp384r1'
	CurveSecp512r1				= 'secp521r1'
	CurveDefault				= None

	StatusNone					= None
	StatusUnknown				= 'unknown'
	StatusOnline				= 'online'
	StatusOffline				= 'offline'
	StatusCloudflare			= 'cloudflare'

	ErrorUnknown				= 'unknown'		# Unknown error.
	ErrorRequest				= 'request'		# The request failed (eg: HTTP errors).
	ErrorConnection				= 'connection'	# The connection could not be establish (eg: invalid URL, cannot reolve host, domain down).
	ErrorTimeout				= 'timeout'		# Request timed out. The connection to the server did not receive a reply within a certain amount of time.
	ErrorCloudflare				= 'cloudflare'	# The request could not bypass Cloudflare (eg: unsolvable challenges, captcha).
	ErrorCertificate			= 'certificate'	# SSL retrieval or validation errors.
	ErrorVpn					= 'vpn'			# VPN not connected, request blocked.
	ErrorNetwork				= [ErrorConnection, ErrorTimeout, ErrorCloudflare, ErrorCertificate, ErrorVpn]

	CloudflareUnknown			= 'unknown'		# Unknown Cloudflare error.
	CloudflareChallenge			= 'challenge'	# Cloudflare new kind of challenge.
	CloudflareSolve				= 'solve'		# Cloudflare challenge cannot be solved.
	CloudflareLoop				= 'loop'		# Cloudflare recursive depth loop.
	Cloudflare1020				= '1020'		# Cloudflare code 1020 block.
	CloudflareIuam				= 'iuam'		# Cloudflare problem extracting IUAM paramters.
	CloudflareCaptcha			= 'captcha'		# Cloudflare various captcha errors.

	# Must be the same as in cloudflare.py.
	# Must have the same values as in settings.xml.
	ValidateStrict				= 3	# Full verification. If anything is wrong with the SSL, the request will fail.
	ValidateModerate			= 2	# Strict verification. Like ValidateStrict, but allows expired and incorrect-domain SSL.
	ValidateLenient				= 1	# Lenient verification. Like ValidateModerate, but uses the old insecure TLSv1 which avoids certain SSL errors (eg: sslv3 alert handshake failure).
	ValidateNone				= 0	# Not implemented yet. Not sure if it can be switched off completley. Currently will fall back to ValidateLenient.

	AuthorizationBasic			= 'Basic'
	AuthorizationBearer			= 'Bearer'

	TimeoutLong					= 45
	TimeoutMedium				= 30
	TimeoutShort				= 15
	TimeoutMinimum				= 15
	TimeoutMaximum				= 60

	ReuseLock					= Lock()
	ReuseSessions				= {}

	ConcurrencyLock				= Lock()
	ConcurrencySemaphore		= {}

	###################################################################
	# CONSTRUCTOR
	###################################################################

	def __init__(self):
		self.mRequest = None
		self.mResponse = None

	###################################################################
	# INTERNAL
	###################################################################

	def _clean(self):
		self.mRequest = {
			'method' : None, # The request HTTP method.
			'link' : None, # The request URL.
			'data' : None, # The request POST data.
			'headers' : None, # The request headers.
		}
		self.mResponse = {
			'request' : None, # The original request.
			'success' : None, # Whether or not the request was successful.
			'link' : None, # The final redirect URL
			'status' : {
				'code' : None, # The HTTP status code.
				'message' : None, # The HTTP status description.
			},
			'error' : {
				'type' : None, # The type of the error occured.
				'code' : None, # The code of the error occured. Is the HTTP status code if it is a request error, otherwise it is another error code string.
				'message' : None, # The short message of the error occured. Is the HTTP status message if it is a request error, otherwise it is an exception message.
				'description' : None, # The description of the error occured.
			},
			'duration' : {
				'connection' : None, # How long in milliseconds the request took to complete. This only measures the time it takes to receive a reply and not the time it takes to download the data.
				'request' : None, # How long in milliseconds the request took to complete. This includes the entire request, including downloading the data.
			},
			'meta' : {
				'type' : None, # The MIME type extracted from the headers.
				'name' : None, # The file name extracted from the headers.
				'size' : None, # The file size extracted from the headers.
			},
			'data' : None, # The response raw byte data.
			'headers' : None, # The response headers.
			'cookies' : None, # The response cookies.
		}

	###################################################################
	# MODULE
	###################################################################

	@classmethod
	def modulePrepare(self):
		# Importing modules in threads or sub-threads sometimes causes Python/Kodi to hang.
		# These are sporadic errors, and there is no clear reason on why this happens - maybe a Kodi bug.
		# The code just hangs at importing a module and never continues, possibly a deadlock.
		# This happens often with moduleTldExtract(), but sometimes also with moduleCaseInsensitiveDict()
		# Might be module specific, or maybe not and it just deadlocks at importing any module.
		# This sometimes causes some providers to not finish during scraping, or when retrieving detailed metadata in threads from one of the indexers.
		# Importing the modules in the root/main thread before starting the sub-threads seems to solve the problem.
		# Maybe it is a better idea to always call this from addon.py before any code is executed, instead of only calling this for certain features of Gaia (providers, metadata, etc).

		#self.moduleTldExtract()
		self.moduleCaseInsensitiveDict()
		self.moduleOrderedDict()
		self.moduleSession()
		self.moduleHttpAdapter()
		self.moduleUrllib3()

	@classmethod
	def moduleTldExtract(self):
		# Check providers/core/base.py -> concurrencyPrepare() for a full description of why we do this.
		return Importer.moduleTldExtract()

	@classmethod
	def moduleCaseInsensitiveDict(self):
		return Importer.moduleCaseInsensitiveDict()

	@classmethod
	def moduleOrderedDict(self):
		return Importer.moduleOrderedDict()

	@classmethod
	def moduleRequests(self):
		return Importer.moduleRequests()

	@classmethod
	def moduleSession(self):
		return Importer.moduleSession()

	@classmethod
	def moduleHttpAdapter(self):
		return Importer.moduleHttpAdapter()

	@classmethod
	def moduleUrllib3(self):
		return Importer.moduleUrllib3()

	###################################################################
	# LINK
	###################################################################

	# Replaces special characters with %XX.
	# If plus parameter is True, spaces are replaced with + instead of %20.
	# Safe specifies a string of characters that should not be encoded.
	# If check, will check if the data is already encoded to avoid multiple encoding.
	@classmethod
	def linkQuote(self, data, plus = False, safe = None, check = False):
		if check and not self.linkUnquote(data = data, plus = plus) == data: return data
		if safe: return quote_plus(data, safe = safe) if plus else quote(data, safe = safe)
		else: return quote_plus(data) if plus else quote(data)

	# Replaces %XX with special characters.
	# If plus parameter is True, + are also replaced with spaces instead of only %20.
	@classmethod
	def linkUnquote(self, data, plus = False):
		return unquote_plus(data) if plus else unquote(data)

	# Encodes a dictionary into a GET parameter string.
	@classmethod
	def linkEncode(self, data, plus = True, duplicates = True):
		return urlencode(data, doseq = duplicates, quote_via = quote_plus if plus else quote)

	# Decodes a GET parameter string into a dictionary.
	# If case parameter is True, a case-insenstive request dictionary is returned instead of a native dictionary.
	# If multi parameter is True and multiple parameters with the same name exists, the parameters in the result dictionary are returned as a list.
	@classmethod
	def linkDecode(self, data, case = False, multi = False):
		result = {}
		parameters = parse_qs(data.lstrip('?'), keep_blank_values = True)
		for key, values in parameters.items():
			if key.endswith('[]'): key = key.replace('[]', '')
			for value in values:
				if multi:
					if key in result: result[key].append(value)
					else: result[key] = [value]
				else:
					result[key] = value
		if case: result = self.moduleCaseInsensitiveDict()(result)
		return result

	@classmethod
	def _linkClean(self, link, parametersExtract = False, parametersStrip = False, headersExtract = False, headersStrip = False):
		parameters = {} if parametersExtract else None
		headers = {} if headersExtract else None

		if link:
			index = link.find('|')
			if index >= 0:
				headers = link[index + 1:]
				if headersStrip: link = link[:index]
				if headersExtract: headers = self.linkDecode(headers, case = True)

			index = link.find('?')
			if index >= 0:
				parameters = link[index + 1:]
				if parametersStrip: link = link[:index]
				if parametersExtract: parameters = self.linkDecode(parameters, case = True)

			link = link.replace(' ', '%20')

		return link, parameters, headers

	# Cleans a link.
	# If strip is True, any headers in the link will be removed.
	@classmethod
	def linkClean(self, link, parametersStrip = False, headersStrip = True):
		return self._linkClean(link = link, parametersExtract = False, parametersStrip = parametersStrip, headersExtract = False, headersStrip = headersStrip)[0]

	# Extract the headers from a URL with the format: http://whatever.com/whatever|key1=value1&&key2=value2
	# If the headers parameter is provided, it will build a new link and append the headers to the URL.
	# If the decode parameter is True, the ;-joined headers will be split and returned as a dictionary instead of a string. Is useful for cookies, but also splits headers like User-Agent.
	@classmethod
	def linkHeaders(self, link, headers = None, cookies = None, decode = False):
		if headers is None and cookies is None:
			link, _, headers = self._linkClean(link = link, parametersExtract = False, parametersStrip = False, headersExtract = True, headersStrip = True)
			if decode: headers = {key : self._headersSplit(headers = value) for key, value in headers.items()} if headers else headers
			return headers
		else:
			if headers is None: headers = {}
			if cookies: headers['Cookie'] = cookies
			headers = {key.title() : (self._headersJoin(headers = value) if tools.Tools.isInstance(value, (dict, self.moduleCaseInsensitiveDict())) else value) for key, value in headers.items()}
			if headers: link += '|' + self.linkEncode(headers)
			return link

	# Extract the cookies from a URL with the format: http://whatever.com/whatever|Cookie=whatever
	# If the cookies parameter is provided, it will build a new link and append the cookies to the URL.
	# If the decode parameter is False, the cookies will be returned as an encoded string instead of a dictionary.
	@classmethod
	def linkCookies(self, link, cookies = None, headers = None, decode = True):
		if cookies is None:
			headers = self.linkHeaders(link = link, decode = decode)
			return headers['Cookie'] if 'Cookie' in headers else {}
		else:
			return self.linkHeaders(link = link, cookies = cookies)

	# Create a GET link with a dictionary of parameters.
	@classmethod
	def linkCreate(self, link = None, parameters = None, duplicates = True, encode = True):
		if tools.Tools.isArray(link): link = self.linkJoin(*link)
		if parameters:
			if not tools.Tools.isString(parameters):

				# For links that require a fixed parameter order (eg: NewzNab).
				if tools.Tools.isArray(parameters):
					parameters = self.moduleOrderedDict()(parameters)

				if encode:
					parameters = self.linkEncode(data = parameters, duplicates = duplicates)
				else:
					# urllib.urlencode only has the "quote_via" parameter since Python 3.5.
					# So we have to create it manually to accomodate older Kodi versions.
					url = []
					for key, value in parameters.items():
						keyNew = str(key) + '[]'
						found = False
						if not duplicates:
							for i in url:
								if i[0] == key or i[0] == keyNew:
									found = True
									break
						if not found:
							if tools.Tools.isArray(value):
								for i in value: url.append((keyNew, i))
							else:
								url.append((key,value))
					parameters = '&'.join([str(i[0]) + '=' + str(i[1]) for i in url])
			if link is None:
				link = parameters
			else:
				if not self.linkPath(link = link) and not link.endswith('/'): link += '/'
				link += ('&' if '?' in link else '?') + parameters
		return link

	# Join parts into a link.
	@classmethod
	def linkJoin(self, *parts):
		if len(parts) == 0: return None
		result = parts[0].rstrip('/')
		for i in range(1, len(parts)):
			if parts[i]:
				if tools.Tools.isArray(parts[i]):
					for j in range(len(parts[i])):
						if parts[i][j]: result = result.rstrip('/') + '/' + str(parts[i][j]).lstrip('/')
				else: result = result.rstrip('/') + '/' + str(parts[i]).lstrip('/')
		return result

	# Get the file extension of a link if available.
	@classmethod
	def linkExtension(self, link):
		path = self.linkPath(link = link)
		path = path.split('?')[0].split('&')[0].split('|')[0].rsplit('.')
		if len(path) <= 1: return None
		return path[-1].replace('/', '').lower()

	@classmethod
	def linkIs(self, link, magnet = False):
		return tools.Tools.isString(link) and (tools.Regex.match(data = link, expression = '^\s*(http|ftp)s?:\/{2}') or (magnet and self.linkIsMagnet(link)))

	@classmethod
	def linkIsMagnet(self, link):
		return tools.Tools.isString(link) and tools.Regex.match(data = link, expression = '^\s*magnet:')

	@classmethod
	def linkIsIp(self, link):
		return tools.Tools.isString(link) and tools.Regex.match(data = link, expression = '^\s*((http|ftp)s?:\/{2})?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')

	# Checks if a link is a local domain or IP address.
	@classmethod
	def linkIsLocal(self, link):
		try:
			import ipaddress
			if ipaddress.ip_address(link.lower()).is_private: return True
		except: pass
		return tools.Tools.isString(link) and tools.Regex.match(data = link, expression = '^\s*((http|ftp)s?:\/{2})?(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.16\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|::1|0:0:0:0:0:0:0:1|fc[0-9a-f]{0,22}::|fd[0-9a-f]{0,22}::)')

	# Extracts the domain from the link.
	@classmethod
	def linkDomain(self, link, subdomain = False, topdomain = True, ip = True, scheme = False, port = False):
		# Manual string manipulation is not perfect. Cannot handle certain things like msulti-TLD (eg: co.uk).
		'''
		try:
			if self.linkIsMagnet(link): return None
			try: result = link.split('://')[1].split('/')[0].split(':')[0].strip()
			except: result = link.strip()
			isIp = self.linkIsIp(result)
			if not ip and isIp: return None
			if not subdomain and not isIp: result = '.'.join(result.split('.')[-2:])
			if not topdomain and not isIp: result = '.'.join(result.split('.')[:-1])
			return result.lower()
		except: return None
		'''

		if not link: return None
		if self.linkIsMagnet(link): return None

		try:
			parts = self.moduleTldExtract().extract(link)
		except:
			tools.Logger.error()
			return None

		result = parts[1]
		if not ip and self.linkIsIp(result): return None

		try:
			if topdomain is True and parts[2]: result = result + '.' + parts[2]
			elif topdomain: result = result + '.' + topdomain
		except: pass

		try:
			if subdomain is True and parts[0]: result = parts[0] + '.' + result
			elif subdomain: result = subdomain + '.' + result
		except: pass

		if port:
			parse = urlparse(link)
			if parse.port: result += ':' + str(parse.port)

		if scheme: result = self.linkScheme(link = link, syntax = True) + result

		return result.lower()

	# Add/replace the subdomain in the link.
	@classmethod
	def linkSubdomain(self, link, subdomain):
		domain = self.linkDomain(link = link, subdomain = subdomain, topdomain = True, ip = True, scheme = True)
		path = self.linkPath(link = link)
		return self.linkJoin(domain, path)

	# Extracts the path from the link (excluding the protocol, domain, and parameters).
	@classmethod
	def linkPath(self, link, parameters = False, strip = True):
		parse = urlparse(link)
		path = parse.path
		if parameters:
			query = tools.Converter.unicode(parse.query)
			if query: path += '?' + query
		if strip: path = path.lstrip('/')
		return path

	# Extracts the path from the link (excluding the protocol, domain, and parameters), split by / into a list.
	@classmethod
	def linkParts(self, link, parameters = False, strip = True):
		path = self.linkPath(link = link, parameters = parameters, strip = strip)
		if path: return path.split('/')
		else: return None

	# Extracts the file name.
	@classmethod
	def linkName(self, link, extension = True, decode = True):
		path = self.linkPath(link = link)
		if path:
			name = tools.File.name(path = path, extension = extension)
			if name:
				if decode: return self.linkUnquote(data = name, plus = not '%20' in name)
				return name
		return None

	# Extracts the GET parameters from a link.
	# If decode parameter is False, the parameters are returned as a string instead of a dictionary.
	# If case parameter is True, a case-insenstive request dictionary is returned instead of a native dictionary.
	@classmethod
	def linkParameters(self, link, decode = True, case = False, multi = False, split = False):
		result = urlsplit(link) if split else urlparse(link)
		result = tools.Converter.unicode(result.query)
		if decode: result = self.linkDecode(data = result, case = case, multi = multi)
		return result

	# Extracts URL fragments.
	# Eg: https://mega.nz/#!Gbh1!HyalkK3VsHE
	@classmethod
	def linkFragments(self, link, decode = True, case = False, multi = False, state = True):
		result = urlparse(link).fragment
		result = tools.Converter.unicode(result)
		if decode: result = self.linkDecode(data = result, case = case, multi = multi)
		if not state and result: result = {key.lstrip('!') : value for key, value in result.items()}
		return result

	# Extracts the link protocol/scheme.
	# syntax: add ://
	@classmethod
	def linkScheme(self, link, syntax = False):
		result = urlparse(link).scheme
		if syntax: result = result + '://'
		return result

	@classmethod
	def linkPort(self, link):
		try: return urlparse(link).port
		except: return None

	@classmethod
	def linkParse(self, link):
		return urlparse(link)

	@classmethod
	def linkOpen(self, link, copy = None, notification = True, front = True, loader = True, label = None):
		from lib.modules.interface import Loader, Translation, Dialog
		if loader: Loader.show() # Needs some time to load. Show busy.

		success = False
		label = Translation.string(label if label else 33381)

		try:
			if tools.Platform.systemTypeMacintosh():
				try:
					tools.Subprocess.open(['open', link], communicate = False)
					success = True
				except: pass
			if not success:
				# This opens http/https links in the browser and magnets in a torrent client.
				# Other URIs, like crypto wallets, do not open, without raising an exception.
				import webbrowser
				webbrowser.open(link, new = 2, autoraise = front) # new = 2 opens new tab.
				success = True
		except: tools.Logger.error()

		if notification:
			if success: Dialog.notification(title = 36265, message = Translation.string(36267) % label, icon = Dialog.IconSuccess, duplicates = True)
			else: Dialog.notification(title = 36266, message = Translation.string(36268) % label, icon = Dialog.IconWarning, duplicates = True)

		if copy or (copy is None and not success):
			from lib.modules.clipboard import Clipboard
			Clipboard.copy(value = link, notify = True, type = label)

		if loader: Loader.hide()

	@classmethod
	def linkCopy(self, link):
		from lib.modules.clipboard import Clipboard
		Clipboard.copyLink(value = link, notify = True)

	@classmethod
	def linkShow(self, link):
		from lib.modules.window import WindowQr
		WindowQr.show(link = link)

	###################################################################
	# AUTHORIZATION
	###################################################################

	# Creates an authorization header string.
	# Either provide the value, or the username and password.
	@classmethod
	def authorization(self, type, value = None, username = None, password = None):
		if value is None:
			if not username is None and not password is None:
				value = tools.Converter.base64To('%s:%s' % (username, password))
		if value is None: return None
		else: return '%s %s' % (type, value)

	# Creates an authorization header dictionary.
	@classmethod
	def authorizationHeader(self, type, value = None, username = None, password = None):
		authorization = self.authorization(type = type, value = value, username = username, password = password)
		if authorization: return {Networker.HeaderAuthorization : authorization}
		else: return None

	###################################################################
	# HTML
	###################################################################

	# Decodes HTML entities (eg: "&eacute;" -> "é").
	@classmethod
	def htmlDecode(self, data):
		try:
			try: from HTMLParser import HTMLParser
			except: from html.parser import HTMLParser
			data = HTMLParser().unescape(data)
		except: pass
		return data

	# Remove HTML tags.
	@classmethod
	def htmlRemove(self, data):
		try:
			from lib.modules.parser import Parser
			data = Parser(data = data, parser = Parser.ParserHtml).text
		except: pass
		return data

	###################################################################
	# HEADERS
	###################################################################

	@classmethod
	def _headersClean(self, headers):
		return {key.title() : value for key, value in headers.items()}

	@classmethod
	def _headersMerge(self, headers1, headers2):
		return tools.Tools.dictionaryMerge(headers1, headers2)

	@classmethod
	def _headersJoin(self, headers):
		if tools.Tools.isArray(headers): headers = '; '.join([str(value) for value in headers])
		elif tools.Tools.isInstance(headers, (dict, self.moduleCaseInsensitiveDict())): headers = '; '.join([str(key) + '=' + str(value) for key, value in headers.items()])
		return headers

	@classmethod
	def _headersSplit(self, headers):
		if tools.Tools.isString(headers):
			if '=' in headers:
				headers = headers.split(';')
				headers = [value.strip().split('=') for value in headers]
				headers = {value[0].strip() : (value[1].strip() if len(value) > 1 else None) for value in headers}
			elif ';' in headers:
				headers = headers.split(';')
				headers = [value.strip() for value in headers]
		return headers

	@classmethod
	def _headersCookie(self, cookies, headers = None):
		if not cookies is None and not tools.Tools.isString(cookies):
			cookies = dict(cookies)
			cookies = self._headersJoin(headers = cookies)
		if not headers is None and 'Cookie' in headers and headers['Cookie']:
			if cookies: cookies = headers['Cookie'] + '; ' + cookies
			else: cookies = headers['Cookie']
		return cookies

	@classmethod
	def _headersAgent(self, agent = None, link = None):
		# https://www.whatismybrowser.com/guides/the-latest-user-agent/
		if agent == Networker.AgentAddon:
			return tools.Platform.agent()
		elif agent == Networker.AgentMobileFixed:
			return 'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.71 Mobile Safari/537.36'
		elif agent == Networker.AgentMobileRandom:
			agents = [
				'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.71 Mobile Safari/537.36',
				'Mozilla/5.0 (Linux; Android 12; SM-A205U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.71 Mobile Safari/537.36',
				'Mozilla/5.0 (Android 12; Mobile; LG-M255; rv:102.0) Gecko/102.0 Firefox/102.0',
				'Mozilla/5.0 (Linux; Android 12; LM-Q710(FGN)) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.71 Mobile Safari/537.36',
				'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Mobile/15E148 Safari/604.1',
				'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/103.0.5060.63 Mobile/15E148 Safari/604.1',
			]
			return tools.Tools.listPick(agents)
		elif agent == Networker.AgentDesktopFixed:
			return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
		elif agent == Networker.AgentDesktopRandom:
			browser = [['%s.0' % i for i in range(18, 43)], ['37.0.2062.103', '37.0.2062.120', '37.0.2062.124', '38.0.2125.101', '38.0.2125.104', '38.0.2125.111', '39.0.2171.71', '39.0.2171.95', '39.0.2171.99', '40.0.2214.93', '40.0.2214.111', '40.0.2214.115', '42.0.2311.90', '42.0.2311.135', '42.0.2311.152', '43.0.2357.81', '43.0.2357.124', '44.0.2403.155', '44.0.2403.157', '45.0.2454.101', '45.0.2454.85', '46.0.2490.71', '46.0.2490.80', '46.0.2490.86', '47.0.2526.73', '47.0.2526.80'], ['11.0']]
			windows = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2', 'Windows NT 6.1', 'Windows NT 6.0', 'Windows NT 5.1', 'Windows NT 5.0']
			features = ['; WOW64', '; Win64; IA64', '; Win64; x64', '']
			agents = ['Mozilla/5.0 ({windows}{feature}; rv:{browser}) Gecko/20100101 Firefox/{browser}', 'Mozilla/5.0 ({windows}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{browser} Safari/537.36', 'Mozilla/5.0 ({windows}{feature}; Trident/7.0; rv:{browser}) like Gecko']
			index = tools.Math.random(0, len(agents) - 1)
			return agents[index].format(windows = tools.Tools.listPick(windows), feature = tools.Tools.listPick(features), browser = tools.Tools.listPick(browser[index]))
		else:
			if link:
				link = self.linkDomain(link = link, subdomain = False, topdomain = True, ip = True, scheme = False)
				if link: link = link.lower()

			# NB: Do not use mobile agents, since some websites (like IMDb) return a desktop/mobile version of the website based on the User-Agent.
			# If the mobile version of the website is returned, the parsing and regular expressions might fail, since they were created for the desktop version.
			#if not link in Networker.AgentData: Networker.AgentData[link] = self._headersAgent(agent = tools.Tools.listPick([Networker.AgentMobileRandom, Networker.AgentDesktopRandom]))
			if not link in Networker.AgentData: Networker.AgentData[link] = self._headersAgent(agent = Networker.AgentDesktopRandom)

			return Networker.AgentData[link]
		return agent

	@classmethod
	def _headersRange(self, range = None):
		if range:
			start = range[0] if range[0] else 0
			size = range[1] if range[1] else 0
			if start > 0 or size > 0:
				if size == 0: range = 'bytes=%d-' % start
				else: range = 'bytes=%d-%d' % (start, start + size - 1)
			else:
				range = None
		return range

	# Extracts the file name from the reponse headers.
	@classmethod
	def _headersName(self, headers):
		try:
			if tools.Tools.isDictionary(headers): headers = self.moduleCaseInsensitiveDict()(headers)
			return tools.Regex.extract(data = headers['Content-Disposition'], expression = 'filename\s*=\s*[\'"](.*)[\'"]')
		except: pass
		return None

	# Extracts the file size from the reponse headers.
	@classmethod
	def _headersSize(self, headers):
		try:
			if tools.Tools.isDictionary(headers): headers = self.moduleCaseInsensitiveDict()(headers)

			if 'Content-Range' in headers:
				value = tools.Regex.extract(data = headers['Content-Range'], expression = 'bytes.*\/(.*)')
				if value and value.isdigit(): return int(value)

			if 'Content-Length' in headers:
				value = headers['Content-Length']
				if value.isdigit(): return int(value)

		except: pass
		return None

	# Extracts the file mime type from the reponse headers.
	@classmethod
	def _headersType(self, headers):
		try:
			if tools.Tools.isDictionary(headers): headers = self.moduleCaseInsensitiveDict()(headers)
			return tools.Regex.extract(data = headers[Networker.HeaderContentType], expression = '(.*?)(?:;|$)')
		except: pass
		return None

	@classmethod
	def headersAcceptLanguage(self, language = None, country = None, weighted = False, wildcard = True, structured = True):
		if language:
			if not tools.Tools.isArray(language): language = [language]

			if country:
				if not tools.Tools.isArray(country): country = [country]
				country = [tools.Country.country(i) for i in country]
				country = [i for i in country if i]

			result = []
			for i in language:
				i = i.lower()
				if country:
					for j in country:
						if i in j[tools.Country.Language]:
							result.append(i + '-' + j[tools.Country.Code][tools.Country.CodePrimary].upper())
				result.append(i)

		if wildcard: result.append('*')

		if result and weighted:
			# https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept-Language
			# https://developer.mozilla.org/en-US/docs/Glossary/Quality_values
			weight = 1.0
			step = 0.01 # Up to three decimal digits.
			for i in range(len(result)):
				weight -= step
				result[i] = '%s;q=%.2f' % (result[i], max(step, weight))

		result = ','.join(result)
		if structured: result = {Networker.HeaderAcceptLanguage : result}
		return result

	###################################################################
	# DATA
	###################################################################

	@classmethod
	def _dataForm(self, data):
		if data and not tools.Tools.isString(data): data = self.linkEncode(data)
		return Networker.MimeForm, data

	@classmethod
	def _dataJson(self, data):
		if data and not tools.Tools.isString(data):
			data = tools.Converter.jsonTo(data)
		return Networker.MimeJson, data

	@classmethod
	def _dataMulti(self, data):
		boundry = 'X-X-X-' + str(tools.Time.timestamp()) + '-X-X-X'
		content = Networker.MimeMulti + '; boundary=%s' % boundry

		if not tools.Tools.isArray(data): data = [data]
		form = bytearray('', 'utf8')
		for entry in data:
			disposition = '%s: form-data' % Networker.HeaderContentDisposition
			if 'name' in entry: disposition += '; name="%s"' % entry['name']
			if 'filename' in entry: disposition += '; filename="%s"' % entry['filename']
			disposition += '\n'

			form += bytearray('--%s\n' % boundry, 'utf8')
			form += bytearray(disposition, 'utf8')
			if 'type' in entry: form += bytearray('%s: %s\n' % (Networker.HeaderContentType, entry['type']), 'utf8')
			form += bytearray('\n', 'utf8')
			try: form += bytearray(entry['data'], 'utf8')
			except: form += entry['data']
			form += bytearray('\n', 'utf8')
			form += bytearray('--%s--\n' % boundry, 'utf8')

		return content, form

	@classmethod
	def dataText(self, data):
		return tools.Converter.unicode(data)

	@classmethod
	def dataJson(self, data):
		return tools.Converter.jsonFrom(data)

	###################################################################
	# SETTINGS
	###################################################################

	@classmethod
	def _settingsCertificates(self):
		return tools.Settings.getInteger('network.general.certificates')

	@classmethod
	def _settingsReuse(self):
		return tools.Settings.getBoolean('network.general.reuse')

	###################################################################
	# SESSION
	###################################################################

	@classmethod
	def _session(self, reuse = None, validate = ValidateNone, curve = None, link = None, domain = None):
		if reuse is None: reuse = self._settingsReuse()
		session = None

		if reuse:
			domain = self._sessionDomain(link = link, domain = domain)
			Networker.ReuseLock.acquire()
			if not domain in Networker.ReuseSessions: Networker.ReuseSessions[domain] = []
			if Networker.ReuseSessions[domain]: session = Networker.ReuseSessions[domain].pop()
			Networker.ReuseLock.release()

		if session is None:
			session = self.moduleSession()() # Must create an instance of Session.
			if validate <= Networker.ValidateModerate:
				urllib3 = self.moduleUrllib3()
				urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

				import ssl
				class Certificate(self.moduleHttpAdapter()):
					def __init__(self, *args, **kwargs):
						self.context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
						if curve: self.context.set_ecdh_curve(curve)
						self.context.check_hostname = False # Must be set BEFORE verify_mode, otherwise this statement is ignored and an error is thrown: " Cannot set verify_mode to CERT_NONE when check_hostname is enabled."
						self.context.verify_mode = ssl.CERT_NONE
						if validate <= Networker.ValidateLenient:
							self.context.options &= ~ssl.OP_NO_TLSv1_3 & ~ssl.OP_NO_TLSv1_2 & ~ssl.OP_NO_TLSv1_1
							try: self.context.minimum_version = ssl.TLSVersion.TLSv1
							except: # TLSVersion not known.
								try: self.context.minimum_version = ssl.PROTOCOL_TLSv1
								except: pass # Old versions do not have a minimum_version.
						super(Certificate, self).__init__(**kwargs)
					def init_poolmanager(self, *args, **kwargs):
						kwargs['ssl_context'] = self.context
						return super(Certificate, self).init_poolmanager(*args, **kwargs)
					def proxy_manager_for(self, *args, **kwargs):
						kwargs['ssl_context'] = self.context
						return super(Certificate, self).proxy_manager_for(*args, **kwargs)
				session.mount('https://', Certificate())

		return session, domain

	@classmethod
	def _sessionReuse(self, session, link = None, domain = None):
		Networker.ReuseSessions[self._sessionDomain(link = link, domain = domain)].append(session)

	@classmethod
	def _sessionDomain(self, link = None, domain = None):
		if domain: return domain
		elif link: return self.linkDomain(link = link, subdomain = False, topdomain = True, ip = True, scheme = False)
		return None

	###################################################################
	# TIMEOUT
	###################################################################

	@classmethod
	def timeoutAdjust(self, timeout):
		if not tools.Tools.isNumber(timeout): timeout = Networker.TimeoutMedium
		return min(Networker.TimeoutMaximum, max(Networker.TimeoutMinimum, timeout))

	###################################################################
	# REQUEST
	###################################################################

	'''
		NOTE
			If the link prarameter is provided: Make a new request and return the RESPONSE dictionary.
			If the link prarameter is not provided: Do not make a new request and just return the REQUEST dictionary from the previous request.
		PARAMETERS
			link (required): Request URL.
			method (optional): HTTP method. If no method is set and data is passed in, the method will be POST. If no method is set and no data is passed in, the method will be GET.
			data (optional): The POST, JSON, or form data. If the method is GET, the data will be appended as GET parameters to the URL.
			type (optional): The type of the data. If not set, normal POST data is assumed. Alternativley the data can be JSON, HTTP multi-part, or HTTP form data.
			headers (optional): The HTTP headers as a dictionary.
			cookies (optional): The HTTP cookies as a dictionary or string. Cookies can also be set directly in the headers.
			range (optional): The HTTP byte range as a tuple or list with two values, the start byte and the size.
			agent (optional): The HTTP user agent. If not set, a default agent is used. Can be a fixed agent string, or an agent type (AgentAddon, AgentMobileFixed, etc).
			timeout (optional): The request timeout. If not set, the default timeout is used.
			concurrency (optional): The maximum number of concurrent connections/requests. If not set, an unlimited number of connections can be established.
			certificate (optional): Whether or not to validate SSL certificates. If not set, the user specified setting is used.
			curve (optional): The Elliptic Curve Cryptography (ECC) to use for the SSL/TLS certificates. More info in cloudflare.py.
			redirect (optional): Allow HTTP redirects.
			encode (optional): Whether or not to URL encode the GET parameters.
			charset (optional): Which character set to use for encoding.
			vpn (optional): Whether or not to check if the VPN is connected (and possibly wait for reconnection) before makiong the request.
			process (optional): Wether or not to process the data and save it to the response. If the output data/JSON/HTML is very large, saving it to the response can take long, and is unnecessary if the data is not used in the end (eg: speedtest).
			debug (optional): An additional debug string to print if something goes wrong with the request.
		RETURNS
			Response dictionary.
			{
				'request' : <Dictionary - The original request.>,
				'success' : <Boolean - Whether or not the request was successful.>,
				'link' : <None/String - The final redirect URL.>,
				'status' : {
					'code' : <None/Integer - The HTTP status code.>,
					'message' : <None/String - The HTTP status description.>,
				},
				'error' : {
					'type' : <None/String - The type of the error occured.>,
					'code' : <None/Integer/String - The code of the error occured. Is the HTTP status code if it is a request error, otherwise it is another error code string.>,
					'message' : <None/String - The message of the error occured. Is the HTTP status message if it is a request error, otherwise it is an exception message.>,
					'description' : <None/String - The description of the error occured.>,
				},
				'duration' : {
					'connection' : <None/Integer - How long in milliseconds the request took to complete. This only measures the time it takes to receive a reply and not the time it takes to download the data.>,
					'request' : <None/Integer - How long in milliseconds the request took to complete. This includes the entire request, including downloading the data.>,
				},
				'meta' : {
					'type' : <None/String - The MIME type extracted from the headers.>,
					'name' : <None/String - The file name extracted from the headers.>,
					'size' : <None/Integer - The file size extracted from the headers.>,
				},
				'data' : <None/Bytes - The response raw byte data.>,
				'headers' : <None/Dictionary - The response headers (case insenstive keys - can be accessed with any case, since it uses CaseInsensitiveDict).>,
				'cookies' : <None/Dictionary - The response cookies (case sensitive keys - can be accessed with any case, since it uses CaseInsensitiveDict).>,
			}
	'''
	def request(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, encode = True, charset = None, vpn = True, process = True, debug = None, cache = False):
		if cache is False:
			return self._request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout_ = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, encode = encode, charset = charset, vpn = vpn, process = process, debug = debug)
		else:
			from lib.modules.cache import Cache
			if tools.Tools.isFunction(cache):
				return cache(function = self._request, link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout_ = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, encode = encode, charset = charset, vpn = vpn, process = process, debug = debug)
			else:
				if tools.Tools.isNumber(cache): time = cache
				else: time = Cache.TimeoutMedium
				return Cache.instance().cache(mode = None, timeout = time, refresh = None, function = self._request, link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout_ = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, encode = encode, charset = charset, vpn = vpn, process = process, debug = debug)

	def _request(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout_ = None, concurrency = None, certificate = None, curve = None, redirect = True, encode = True, charset = None, vpn = True, process = True, debug = None):
		try:
			if link is None: return self.mRequest

			from lib.modules.cloudflare import Cloudflare
			from lib.modules.vpn import Vpn
			CaseInsensitiveDict = self.moduleCaseInsensitiveDict()

			self._clean()
			if not timeout_: timeout_ = Networker.TimeoutLong

			link, _, headersExtra = self._linkClean(link = link, parametersExtract = False, parametersStrip = False, headersExtract = True, headersStrip = True)

			method = method if method else Networker.MethodPost if data else Networker.MethodGet
			if method == Networker.MethodGet:
				link = self.linkCreate(link = link, parameters = data, encode = encode)
				data = None
			else: # POST and others.
				if encode is False or charset:
					# Create a POST query manually, since otherwise Requests will re-encode already encoded values in the dictionary.
					# This seems to only apply to encoding that is different to UTF-8. Eg the encoded data coming in as Windows-1251 encoded.
					# There seems to be no parameter in Requests to tell it not to encode the dict values.
					# Therefore create a charset/url-encoded data string, which Requests will not encode again, since it considers it as raw POST data.
					# Will also have to add the the "charset" in the HTTP headers, see below.
					data = self.linkCreate(parameters = data, encode = False)

			if not headers: headers = {}
			headers = self._headersMerge(headers1 = headers, headers2 = headersExtra)
			headers = self._headersClean(headers = headers)

			cookies = self._headersCookie(cookies = cookies, headers = headers)
			if cookies: headers[Networker.HeaderCookie] = cookies

			if not Networker.HeaderUserAgent in headers or not headers[Networker.HeaderUserAgent]:
				agent = self._headersAgent(agent = agent, link = link)
				if agent: headers[Networker.HeaderUserAgent] = agent

			if not Networker.HeaderRange in headers or not headers[Networker.HeaderRange]:
				range = self._headersRange(range = range)
				if range: headers[Networker.HeaderRange] = range

			if data:
				content = None
				if type == Networker.DataJson: content, data = self._dataJson(data = data)
				elif type == Networker.DataMulti: content, data = self._dataMulti(data = data)
				elif type == Networker.DataForm: content, data = self._dataForm(data = data)
				elif charset: content, data = self._dataForm(data = data)

				# Encode, otherwise for some special body data, requests throws an error about encoding.
				# For instance, scraping "Dune 2021" with BitLord:
				#	'latin-1' codec can't encode character '\u2013' in position 11: Body ('–') is not valid Latin-1. Use body.encode('utf-8') if you want to send it encoded in UTF-8.
				if tools.Tools.isString(data) and charset:
					try: data = data.encode(charset)
					except: pass

				if content and (not Networker.HeaderContentType in headers or not headers[Networker.HeaderContentType]):
					# Important for some providers (like NoNameClub) that use a different encoding charset than UTF-8.
					# If the charset is Windows-1251 and the charset is not added to the headers, the server interprets it as probably UTF-8, and then returns different results.
					# The Provider structure passes and already encoded query to the Networker.
					if charset: content += '; charset=' + charset

					headers[Networker.HeaderContentType] = content

			self.mRequest['method'] = method
			self.mRequest['link'] = link
			self.mRequest['data'] = data
			self.mRequest['headers'] = CaseInsensitiveDict(headers)

			session = None
			domain = None
			validate = self._settingsCertificates()
			reuse = self._settingsReuse()
			released = False
			duration = None

			try:
				headers = dict(self._headersClean(headers = headers)) # Headers are case insensitive. But just make them titlecase in case the Cloudflare scraper does something weird.
				vpnError = False
				if not vpn or Vpn.killRequest(): # Check if VPN is connected.
					if concurrency:
						if not concurrency in Networker.ConcurrencySemaphore:
							Networker.ConcurrencyLock.acquire()
							if not concurrency in Networker.ConcurrencySemaphore: Networker.ConcurrencySemaphore[concurrency] = Semaphore(concurrency)
							Networker.ConcurrencyLock.release()
						Networker.ConcurrencySemaphore[concurrency].acquire()

					if Cloudflare.enabled():
						result = Cloudflare(validate = validate, reuse = reuse).request(method = method, link = link, headers = headers, data = data, timeout = timeout_, certificate = certificate, curve = curve, redirect = redirect, log = False)
						response = result['response']
						responseCookies = result['cookies']
						duration = result['duration']
					else:
						if certificate is None: certificate = validate
						verify = certificate >= Cloudflare.ValidateStrict

						session, domain = self._session(reuse = reuse, validate = certificate, curve = curve, link = link)
						timer = tools.Time(start = True)
						response = session.request(method = 'GET' if method is None else method, url = link, headers = headers, data = data, timeout = timeout_, verify = verify, allow_redirects = redirect)
						duration = timer.elapsed(milliseconds = True)

						# NB: session.response.cookies does not return all of the cookies.
						# Not entirley sure why, but maybe only the cookies of the last request are returned, and not all the cookies in the chain or redirection.
						# Use session.cookies to return ALL cookies.
						try: responseCookies = session.cookies.get_dict()
						except: responseCookies = None

					if concurrency:
						released = True
						Networker.ConcurrencySemaphore[concurrency].release()
				else:
					vpnError = True

				try: self.mRequest['headers'] = CaseInsensitiveDict(response.request.headers)
				except: pass

				try: success = response.status_code < 300
				except: success = False
				self.mResponse['success'] = success
				try: self.mResponse['status']['code'] = response.status_code
				except: pass
				try: self.mResponse['status']['message'] = response.reason
				except: pass

				if not success:
					if vpnError:
						self.mResponse['error']['type'] = Networker.ErrorVpn
						self.mResponse['error']['message'] = 'VPN not connected and the request blocked.'
					else:
						self.mResponse['error']['type'] = Networker.ErrorRequest
						self.mResponse['error']['code'] = response.status_code
						self.mResponse['error']['message'] = response.reason

				try: self.mResponse['duration']['connection'] = int(response.elapsed.total_seconds() * 1000)
				except: pass
				try: self.mResponse['duration']['request'] = duration
				except: pass

				try: self.mResponse['link'] = response.url
				except: pass

				if process:
					# Do not add different formats to the response.
					# Firstly, this is wastes time if some format is not used.
					# Secondly, large data will be stored as duplicate in cache.py, wasting disk space.
					'''try: self.mResponse['data']['bytes'] = response.content
					except: pass
					try: self.mResponse['data']['unicode'] = tools.Converter.unicode(response.content)
					except: pass
					try: self.mResponse['data']['text'] = response.text
					except: pass
					try: self.mResponse['data']['json'] = response.json()
					except: pass'''
					try: self.mResponse['data'] = response.content
					except: pass
					try: responseText = response.text
					except: responseText = None
				else:
					self.mResponse['data'] = None
					responseText = None

				try: self.mResponse['headers'] = CaseInsensitiveDict(response.headers)
				except: pass
				try: self.mResponse['headers']['Status'] = response.status_code
				except: pass
				try:
					# 'Location' headers seems not to be added to the response headers.
					# Add manually.
					# Used by extratorrent.py.
					if not Networker.HeaderLocation in self.mResponse['headers'] and self.mResponse['link']:
						self.mResponse['headers'][Networker.HeaderLocation] = self.mResponse['link']
				except: pass
				try: self.mResponse['cookies'] = CaseInsensitiveDict(responseCookies)
				except: pass

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
				#
				# Do not just check the headers (eg: server: cloudflare), since some sites (eg: ApiBay when not sending GET parameters) return the same headers and 403, but it does not show the Cloudflare.
				# https://support.cloudflare.com/hc/en-us/articles/360029779472-Troubleshooting-Cloudflare-1XXX-errors
				if self.mResponse['error']['code'] == 403:
					try:
						if tools.Regex.match(data = responseText, expression = 'cloudflare'):
							if tools.Regex.match(data = responseText, expression = '(error(?:\s*<\/?(?:div|span)>\s*)*1\d{3}|please\s*wait\s*\.{3})'):
								self.mResponse['error']['type'] = Networker.ErrorCloudflare
					except: pass

			except Exception as error:
				if concurrency and not released: Networker.ConcurrencySemaphore[concurrency].release()

				# Custom CloudflareException.
				try: self.mResponse['status']['code'] = error.response.status_code
				except: pass
				try: self.mResponse['status']['message'] = error.response.reason
				except: pass

				try: self.mResponse['duration']['connection'] = int(error.response.elapsed.total_seconds() * 1000)
				except: pass
				try: self.mResponse['duration']['request'] = duration
				except: pass

				try:
					self.mResponse['headers'] = CaseInsensitiveDict(error.response.headers)
					self.mResponse['headers']['Status'] = error.response.status_code
				except: pass
				try: self.mResponse['cookies'] = CaseInsensitiveDict(error.cookies)
				except:
					try: self.mResponse['cookies'] = CaseInsensitiveDict(error.response.cookies.get_dict())
					except: pass
				try: error = error.exception
				except: pass

				errorType = Networker.ErrorUnknown
				errorCode = None
				errorName = error.__class__.__name__.lower()

				if 'connectionerror' in errorName:
					errorType = Networker.ErrorConnection
				elif 'cloudflare' in errorName:
					errorType = Networker.ErrorCloudflare
					errorCode = Networker.CloudflareUnknown
					if 'challenge' in errorName: errorCode = Networker.CloudflareChallenge
					elif 'solve' in errorName: errorCode = Networker.CloudflareSolve
					elif 'loop' in errorName: errorCode = Networker.CloudflareLoop
					elif '1020' in errorName: errorCode = Networker.Cloudflare1020
					elif 'iuam' in errorName: errorCode = Networker.CloudflareIuam
					elif 'loop' in errorName: errorCode = Networker.CloudflareLoop
					elif 'captcha' in errorName: errorCode = Networker.CloudflareCaptcha
				elif 'timed out' in errorName or 'timeout' in errorName:
					errorType = Networker.ErrorTimeout
				elif 'ssl' in errorName:
					errorType = Networker.ErrorCertificate

				try: errorDescription = error.message
				except: errorDescription = str(error)

				try:
					errorMessage = tools.Regex.extract(data = errorDescription, expression = '>:\s*(.*)')
					if not errorMessage:
						errorMessage = tools.Regex.extract(data = errorDescription, expression = '\]\s*(.*)')
						if not errorMessage:
							errorMessage = tools.Regex.extract(data = errorDescription, expression = 'port\s*=\s*\d{1,5}\):\s*(.*)')
							if not errorMessage: errorMessage = tools.Regex.extract(data = errorDescription, expression = '\s*(connection\s*aborted).*?\'')
					if errorMessage: errorMessage = errorMessage.strip().strip('(').strip(')').strip(',').strip('\'').strip()
					else: errorMessage = errorDescription
				except: errorMessage = errorDescription

				# Add full description for Android "_bootlocale" errors.
				try:
					if 'bootlocale' in errorDescription:
						tools.Logger.error()
						errorMessage = errorDescription
				except: pass

				self.mResponse['success'] = False
				self.mResponse['error']['type'] = errorType
				self.mResponse['error']['code'] = errorCode
				self.mResponse['error']['message'] = errorMessage
				self.mResponse['error']['description'] = errorDescription

				tools.Logger.log('Network Error', '[' + (('Error Type: ' + errorType.title()) if errorType else '') + ((' | Error Code: ' + str(errorCode).title()) if errorCode else '') + ((' | Debug: ' + str(debug)) if debug else '') + ' | Link: ' + link + ']:', errorMessage)

			self.mResponse['meta']['type'] = self._headersType(headers = self.mResponse['headers'])
			self.mResponse['meta']['name'] = self._headersName(headers = self.mResponse['headers'])
			self.mResponse['meta']['size'] = self._headersSize(headers = self.mResponse['headers'])

			self.mResponse['request'] = tools.Tools.copy(self.mRequest)

			if reuse and session: self._sessionReuse(session = session, domain = domain)


			return self.mResponse
		except:
			tools.Logger.error()
			return None

	'''
		NOTE
			If the link prarameter is provided: Make a new request and return the RESPONSE data.
			If the link prarameter is not provided: Do not make a new request and just return the REQUEST data from the previous request.
		RETURNS
			The response data object on request success, otherwise None.
	'''
	def requestData(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, vpn = True, cache = False):
		if link is None: return self.mRequest['data']
		response = self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, vpn = vpn, cache = cache)
		return self.responseDataBytes()

	'''
		NOTE
			If the link prarameter is provided: Make a new request and return the RESPONSE data.
			If the link prarameter is not provided: Do not make a new request and just return the REQUEST data from the previous request.
		RETURNS
			The response binary data on request success, otherwise None.
	'''
	def requestBytes(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, vpn = True, cache = False):
		if link is None: return self.mRequest['data']
		self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, vpn = vpn, cache = cache)
		return self.responseDataBytes()

	'''
		NOTE
			If the link prarameter is provided: Make a new request and return the RESPONSE data.
			If the link prarameter is not provided: Do not make a new request and just return the REQUEST data from the previous request.
		RETURNS
			The response unicode text data on request success, otherwise None.
	'''
	def requestText(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, vpn = True, cache = False):
		if link is None: return self.dataText(self.mRequest['data'])
		self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, vpn = vpn, cache = cache)
		return self.responseDataText()

	'''
		NOTE
			If the link prarameter is provided: Make a new request and return the RESPONSE JSON data.
			If the link prarameter is not provided: Do not make a new request and just return the REQUEST JSON data from the previous request.
		RETURNS
			The response JSON dictionary on request success and if the returned data is JSON, otherwise None.
	'''
	def requestJson(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, vpn = True, cache = False):
		if link is None: return self.dataJson(self.mRequest['data'])
		self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, vpn = vpn, cache = cache)
		return self.responseDataJson()

	'''
		NOTE
			If the link prarameter is provided: Make a new request and return the RESPONSE headers.
			If the link prarameter is not provided: Do not make a new request and just return the REQUEST headers from the previous request.
		RETURNS
			The response headers as a dictionary (lower case keys) on request success, otherwise None.
	'''
	def requestHeaders(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, vpn = True, cache = False):
		if link is None: return self.mRequest['headers']
		response = self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, vpn = vpn, cache = cache)
		return response['headers']

	'''
		NOTE
			If the link prarameter is provided: Make a new request and return the RESPONSE cookies.
			If the link prarameter is not provided: Do not make a new request and just return the REQUEST cookies from the previous request.
		RETURNS
			The response cookies as a dictionary (case sensitive keys) on request success, otherwise None.
	'''
	def requestCookies(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, vpn = True, cache = False):
		if link is None: return self.mRequest['cookies']
		response = self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, vpn = vpn, cache = cache)
		return response['cookies']

	'''
		NOTE
			If the link prarameter is provided: Make a new request and return the RESPONSE final redirected URL.
			If the link prarameter is not provided: Do not make a new request and just return the REQUEST URL from the previous request.
		RETURNS
			The response final redirected URL on request success, otherwise None.
	'''
	def requestLink(self, link = None, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, vpn = True, cache = False):
		if link is None: return self.mRequest['link']
		response = self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, vpn = vpn, cache = cache)
		result = response['link']
		if result == link:
			try:
				other = response['headers']['location']
				if other: result = other
			except: pass
		return result

	'''
		NOTE
			Check if the link is valid/accessible. By default makes a HEAD request.
			If the link prarameter is provided: Make a new request and return the RESPONSE success.
			If the link prarameter is not provided: Do not make a new request and just return the RESPONSE success from the previous request.
		RETURNS
			The response success status.
	'''
	def requestSuccess(self, link = None, method = MethodHead, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, vpn = True, cache = False):
		if link is None: return self.mResponse['success']
		response = self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, vpn = vpn, cache = cache)
		return response['success']

	'''
		NOTE
			Get the status of a link. Similar to requestSuccess(), but it also checks the data content.
			First only the headers are retrieved. If the request was successful and the content is TEXT/HTML/JSON, it will download the content and search for certain keywords (eg: "not found").
		RETURNS
			The response status.
	'''
	def requestStatus(self, link, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None, concurrency = None, certificate = None, curve = None, redirect = True, vpn = True, cache = False):
		response = self.request(link = link, method = Networker.MethodHead, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, vpn = vpn, cache = cache)

		if not response['success']:
			if response['error']['type'] == Networker.ErrorCloudflare:
				return Networker.StatusCloudflare
			else:
				return Networker.StatusOffline

		if response['meta']['type']:
			if any(i in response['meta']['type'] for i in ['text', 'json']):
				response = self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout, concurrency = concurrency, certificate = certificate, curve = curve, redirect = redirect, cache = cache)
				text = self.responseDataText()
				if text:
					text = text.lower()
					# Do not be too general, like "copyright", beacause other links/texts on the page might also those phrases.
					failures = ['not found', 'permission denied', 'access denied', 'forbidden access', 'file unavailable', 'bad file', 'unauthorized', 'file remove', 'payment required', 'method not allowed', 'not acceptable', 'authentication required', 'request timeout', 'unavailable for legal reasons', 'too many request', 'file removed', 'file has been removed', 'removed file', 'file expired']
					if any(failure in text for failure in failures):
						return Networker.StatusOffline
					else:
						return Networker.StatusUnknown
				else:
					return Networker.StatusOffline

		return Networker.StatusOnline

	###################################################################
	# RESPONSE
	###################################################################

	def response(self):
		return self.mResponse

	def responseData(self):
		return self.mResponse['data']

	def responseDataBytes(self):
		return self.responseData()

	def responseDataText(self):
		return self.dataText(self.responseData())

	def responseDataJson(self):
		return self.dataJson(self.responseData())

	def responseHeaders(self):
		return self.mResponse['headers']

	def responseCookies(self):
		return self.mResponse['cookies']

	def responseLink(self):
		return self.mResponse['link']

	def responseSuccess(self):
		return self.mResponse['success']

	def responseStatus(self):
		return self.mResponse['status']

	def responseStatusCode(self):
		return self.mResponse['status']['code']

	def responseStatusMessage(self):
		return self.mResponse['status']['message']

	def responseError(self):
		return self.mResponse['error']

	def responseErrorType(self):
		return self.mResponse['error']['type']

	def responseErrorCode(self):
		return self.mResponse['error']['code']

	def responseErrorMessage(self):
		return self.mResponse['error']['message']

	def responseErrorDescription(self):
		return self.mResponse['error']['description']

	def responseErrorCloudflare(self):
		return self.responseErrorType() == Networker.ErrorCloudflare

	def responseErrorTimeout(self):
		return self.responseErrorType() == Networker.ErrorTimeout

	# Server rejected the connection, because too many parallel connections were made to the server at the same time.
	def responseErrorConnections(self, full = True):
		# Some server return error 429 as they should.
		if self.responseErrorXxx(rangeFrom = 429, rangeTo = 429): return True

		# Other servers simply drop the connection, without returning any HTTP errors.
		# Eg: Failed to establish a new connection: [Errno 111] Connection refused
		# Note that "Connection refused" can also mean something else went wrong, like the domain is down or parked, etc.
		# Check for "Connection refused", since "Failed to establish a new connection" can also be caused by something else.
		# Eg: Failed to establish a new connection: [Errno 101] Network is unreachable
		# Eg: Failed to establish a new connection: [Errno -2] Name or service not known
		if full:
			data = self.responseErrorMessage()
			if data and tools.Regex.match(data = data, expression = 'failed\s*to\s*establish\s*a\s*new\s*connection.*?connection\s*refused'): return True

		return False

	def responseErrorXxx(self, rangeFrom, rangeTo):
		code = self.mResponse['error']['code']
		return code and tools.Tools.isInteger(code) and code >= rangeFrom and code <= rangeTo

	def responseError2xx(self):
		return self.responseErrorXxx(rangeFrom = 200, rangeTo = 299)

	def responseError3xx(self):
		return self.responseErrorXxx(rangeFrom = 300, rangeTo = 399)

	def responseError4xx(self):
		return self.responseErrorXxx(rangeFrom = 400, rangeTo = 499)

	def responseError5xx(self):
		return self.responseErrorXxx(rangeFrom = 500, rangeTo = 599)

	def responseDuration(self):
		return self.mResponse['duration']

	def responseDurationConnection(self):
		return self.mResponse['duration']['connection']

	def responseDurationRequest(self):
		return self.mResponse['duration']['request']

	###################################################################
	# DOWNLOAD
	###################################################################

	# Downloads a file to disk.
	# NB: Be careful with big files, since the entire file is downloaded into memory before saving it to disk.
	def download(self, link, path, method = None, data = None, type = None, headers = None, cookies = None, range = None, agent = None, timeout = None):
		response = self.request(link = link, method = method, data = data, type = type, headers = headers, cookies = cookies, range = range, agent = agent, timeout = timeout)
		if not response['success']: return False
		tools.File.writeNow(path, self.responseDataBytes())
		return True


class Geolocator(object):

	ServiceIpwhoisapp		= 'ipwhoisapp'			# Public Access
	ServiceIpinfoio			= 'ipinfoio'			# Public Access
	ServiceGeopluginnet		= 'geopluginnet'		# Public Access
	ServiceIpapiio			= 'ipapiio'				# Public Access
	ServiceIpapico			= 'ipapico'				# Public Access
	ServiceGeolocationdbcom	= 'geolocationdbcom'	# Public Access
	ServiceDbipcom			= 'dbipcom'				# Public Access
	ServiceGeojsio			= 'geojsio'				# Public Access
	ServicePublic			= [ServiceIpwhoisapp, ServiceIpinfoio, ServiceGeopluginnet, ServiceIpapiio, ServiceIpapico, ServiceGeolocationdbcom, ServiceDbipcom, ServiceGeojsio]

	ServiceIpgeolocationio	= 'ipgeolocationio'		# Private Access - 1,000 req per day / 30,000 req per month
	ServiceGeoapifycom		= 'geoapifycom'			# Private Access - 5 req per second / 3,000 req per day
	ServiceIpinfodbcom		= 'ipinfodbcom'			# Private Access - 2 req per second
	ServiceIpdataco			= 'ipdataco'			# Private Access - 1,500 req per day
	ServiceBigdatacloudnet	= 'bigdatacloudnet'		# Private Access - 10,000 req per month
	ServiceIpapicom			= 'ipapicom'			# Private Access - 1,000 req per month
	ServiceIpstackcom		= 'ipstackcom'			# Private Access - 100 req per month
	ServicePrivate			= [ServiceIpgeolocationio, ServiceGeoapifycom, ServiceIpinfodbcom, ServiceIpdataco, ServiceBigdatacloudnet, ServiceIpapicom, ServiceIpstackcom]

	AnonymizeNone			= None
	AnonymizeObfuscate		= 'obfuscate' # Anonymize by obfuscating the IP address and other info.
	AnonymizeStrip			= 'strip' # Anonymize by completely removing IP address and other info.

	PropertyLast			= 'GaiaGeolocatorLast'

	LocationCache			= None

	###################################################################
	# LOCATION
	###################################################################

	@classmethod
	def location(self,
		continentCode = None,
		continentName = None,

		countryCode = None,
		countryName = None,

		regionCode = None,
		regionName = None,

		cityCode = None,
		cityName = None,

		coordinateLatitude = None,
		coordinateLongitude = None,

		timezone = None,
	):
		if Geolocator.LocationCache is None: Geolocator.LocationCache = Importer.moduleGeoNamesCache()()

		def _query(data):
			try: return data.lower().replace(' ', '')
			except: return data

		if not continentCode: continentCode = None
		if not continentName: continentName = None
		if not countryCode: countryCode = None
		if not countryName: countryName = None
		if not regionCode: regionCode = None
		if not regionName: regionName = None
		if not cityCode: cityCode = None
		if not cityName: cityName = None
		if not coordinateLatitude: coordinateLatitude = None
		if not coordinateLongitude: coordinateLongitude = None
		if not timezone: timezone = None

		queryStateCode = None
		try: queryContinentCode = _query(continentCode)
		except: queryContinentCode = None
		try: queryContinentName = _query(continentName)
		except: queryContinentName = None
		try: queryCountryCode = _query(countryCode)
		except: queryCountryCode = None
		try: queryCountryName = _query(countryName)
		except: queryCountryName = None
		try: queryRegionCode = _query(regionCode)
		except: queryRegionCode = None
		try: queryRegionName = _query(regionName)
		except: queryRegionName = None
		try: queryCityCode = _query(cityCode)
		except: queryCityCode = None
		try: queryCityName = _query(cityName)
		except: queryCityName = None

		if not continentCode or not continentName or not countryCode or not countryName or not regionCode or not regionName or not cityCode or not cityName or not coordinateLatitude or not coordinateLongitude or not timezone:
			if cityName:
				data = Geolocator.LocationCache.search_cities(query = cityName, case_sensitive = False)
				found = False
				if data:
					if len(data) > 1:
						if not found and cityName and countryCode:
							for i in data:
								try:
									if _query(i['name']) == queryCityName and _query(i['countrycode']) == queryCountryCode:
										found = True
										data = i
										break
								except: pass
						if not found and cityName:
							for i in data:
								try:
									if _query(i['name']) == queryCityName:
										found = True
										data = i
										break
								except: pass
						if not found and countryCode:
							for i in data:
								try:
									if _query(i['countrycode']) == queryCountryCode:
										found = True
										data = i
										break
								except: pass
						if tools.Tools.isList(data):
							data = data[0]
					else:
						found = True
						data = data[0]
			elif coordinateLatitude and coordinateLongitude:
				data = Geolocator.LocationCache.get_cities()
				if data:
					closestDistance = 9999999999
					closestCity = None
					largestPopulation = 0
					largestCity = None
					for i in data.values():
						if i['latitude'] and i['longitude']:
							distance = abs(coordinateLatitude - i['latitude']) + abs(coordinateLongitude - i['longitude'])
							if distance <= closestDistance:
								if not countryCode or queryCountryCode == _query(i['countrycode']):
									closestDistance = distance
									closestCity = i
							if distance <= 0.1 and i['population'] and i['population'] > largestPopulation: # Otherwise suburbs are detected as cities.
								largestPopulation = i['population']
								largestCity = i
					if largestCity:
						found = True
						data = largestCity
					elif closestCity:
						found = True
						data = closestCity

				if found and data:
					if not timezone or not '/' in timezone: timezone = data['timezone']
					if not cityName:
						cityName = data['name']
						try: queryCityName = _query(cityName)
						except: queryCityName = None
					if not countryCode:
						countryCode = data['countrycode']
						try: queryCountryName = _query(countryCode)
						except: queryCountryName = None
					if not coordinateLatitude: coordinateLatitude = data['latitude']
					elif data['latitude'] and len(str(data['latitude'])) > len(str(coordinateLatitude)): coordinateLatitude = data['latitude']
					if not coordinateLongitude: coordinateLongitude = data['longitude']
					elif data['longitude'] and len(str(data['longitude'])) > len(str(coordinateLongitude)): coordinateLongitude = data['longitude']
					queryStateCode = _query(data['admin1code'])

			if not continentCode or not continentName or not countryCode or not countryName:
				data = Geolocator.LocationCache.get_countries()
				if data:
					found = False
					if not found and countryCode and len(countryCode) == 2:
						for i in data.values():
							try:
								if queryCountryCode == _query(i['iso']):
									found = True
									data = i
									break
							except: pass
					if not found and countryCode and len(countryCode) == 3:
						for i in data.values():
							try:
								if queryCountryCode == _query(i['iso3']):
									found = True
									data = i
									break
							except: pass
					if not found and countryName:
						for i in data.values():
							try:
								if queryCountryName == _query(i['name']):
									found = True
									data = i
									break
							except: pass
					# Lookup FIPS last, since they can clash with with ISO codes. Eg: Australia has ISO "AU", but Austria has FIPS "AU" as well.
					if not found and countryCode and len(countryCode) == 2:
						for i in data.values():
							try:
								if queryCountryCode == _query(i['fips']):
									found = True
									data = i
									break
							except: pass
					if found and data:
						if not continentCode:
							continentCode = data['continentcode']
							try: queryContinentCode = _query(continentCode)
							except: queryContinentCode = None
						if not countryCode:
							countryCode = data['iso']
							try: queryCountryCode = _query(countryCode)
							except: queryCountryCode = None
						if not countryName:
							countryName = data['name']
							try: queryCountryName = _query(countryName)
							except: queryCountryName = None

			if not continentCode or not continentName:
				data = Geolocator.LocationCache.get_continents()
				if data:
					found = False
					if not found and continentCode:
						for i in data.values():
							try:
								if queryContinentCode == _query(i['continentCode']):
									found = True
									data = i
									break
							except: pass
					if not found and continentName:
						for i in data.values():
							try:
								if queryContinentName == _query(i['asciiName']):
									found = True
									data = i
									break
							except: pass
					if not found and countryCode:
						for i in data.values():
							try:
								if queryCountryCode in _query(i['cc2']).split(','):
									found = True
									data = i
									break
							except: pass
					if found and data:
						if not continentCode:
							continentCode = data['continentCode']
							try: queryContinentCode = _query(continentCode)
							except: queryContinentCode = None
						if not continentName:
							continentName = data['asciiName']
							try: queryContinentName = _query(continentName)
							except: queryContinentName = None

			if _query(countryCode) == 'us' and ((not regionName and regionCode) or (not regionCode and regionName) or (not regionCode and not regionName and queryStateCode)):
				data = Geolocator.LocationCache.get_us_states()
				if data:
					found = False
					if not found and regionCode:
						for i in data.values():
							try:
								if queryRegionCode == _query(i['code']):
									found = True
									data = i
									break
							except: pass
					if not found and regionName:
						for i in data.values():
							try:
								if queryRegionName == _query(i['name']):
									found = True
									data = i
									break
							except: pass
					if not found and queryStateCode:
						for i in data.values():
							try:
								if queryStateCode == _query(i['code']):
									found = True
									data = i
									break
							except: pass
					if found and data:
						if not regionCode:
							regionCode = data['code']
							try: queryRegionCode = _query(regionCode)
							except: queryRegionCode = None
						if not regionName:
							regionName = data['name']
							try: queryRegionName = _query(regionName)
							except: queryRegionName = None

		return {
			'timezone' : timezone if timezone else None,
			'continent' : {
				'code' : continentCode.lower() if continentCode else None,
				'name' : continentName if continentName else None,
			},
			'country' : {
				'code' : countryCode.lower() if countryCode else countryCode,
				'name' : countryName if countryName else None,
			},
			'region' : {
				'code' : regionCode.lower() if regionCode else regionCode,
				'name' : regionName if regionName else None,
			},
			'city' : {
				'code' : cityCode.lower() if cityCode else cityCode,
				'name' : cityName if cityName else None,
			},
			'coordinate' : {
				'latitude' : coordinateLatitude if coordinateLatitude else None,
				'longitude' : coordinateLongitude if coordinateLongitude else None,
			},
		}

	###################################################################
	# SERVICE
	###################################################################

	@classmethod
	def services(self, public = True, private = True, custom = True, limit = 7):
		if public: public = self.servicesPublic()
		if private: private = self.servicesPrivate()
		if custom: custom = self.servicesCustom()

		result = []

		# Always use the the primary custom first.
		# If no custom was set, use a random public (or private) one, which allows more randomized first picks.
		if custom: result.append(custom[0])
		elif public: result.append(tools.Tools.listPick(public))
		elif private: result.append(tools.Tools.listPick(private))

		# Add the previously working service as second.
		# This ensures we do not waste too much time going down the list if the first pick failed.
		functional = self.serviceLast(full = False)
		if functional: result.append(functional)

		# Add the remaining custom ones.
		if custom: result.extend(custom)
		if public: result.extend(tools.Tools.listShuffle(public))
		if private: result.extend(tools.Tools.listShuffle(private))

		# Remove duplicates. This should keep the order an remove subsequent duplicates (instead of the first ones).
		result = tools.Tools.listUnique(result)

		if limit: result = result[:limit]
		return result

	@classmethod
	def servicesPublic(self, shuffle = False):
		result = [{'service' : service} for service in Geolocator.ServicePublic]
		if result and shuffle: result = tools.Tools.listShuffle(result)
		return result

	@classmethod
	def servicesPrivate(self, shuffle = False, full = True):
		result = []
		for service in Geolocator.ServicePrivate:
			keys = tools.Converter.jsonFrom(tools.System.obfuscate(tools.Settings.getString('internal.key.' + service, raw = True)))
			if full: result.extend([{'service' : service, 'key' : key} for key in keys])
			else: result.append({'service' : service, 'key' : tools.Tools.listPick(keys)})
		if result and shuffle: result = tools.Tools.listShuffle(result)
		return result

	@classmethod
	def servicesCustom(self, shuffle = False):
		from lib.modules.account import Geolocation
		result = [Geolocation(Geolocation.TypePrimary), Geolocation(Geolocation.TypeSecondary), Geolocation(Geolocation.TypeTertiary)]
		result = [{'service' : i.dataType(), 'key' : i.dataKey()} for i in result if i.authenticated()]
		if result and shuffle: result = tools.Tools.listShuffle(result)
		return result

	@classmethod
	def servicesCustomHas(self):
		return bool(self.servicesCustom())

	@classmethod
	def serviceLast(self, full = True):
		try:
			service = tools.Converter.jsonFrom(tools.System.windowPropertyGet(Geolocator.PropertyLast))
			if full: return service
			else: return {'service' : service['service'], 'key' : service['key']}
		except: return None

	@classmethod
	def serviceLastSet(self, service, key, data = None):
		if service: tools.System.windowPropertySet(Geolocator.PropertyLast, tools.Converter.jsonTo({'service' : service, 'key' : key, 'time' : tools.Time.timestamp(), 'data' : data}))

	@classmethod
	def serviceLastClear(self):
		tools.System.windowPropertyClear(Geolocator.PropertyLast)

	###################################################################
	# DATA
	###################################################################

	@classmethod
	def dataValid(self, data):
		return bool(data and (data['address']['ipv4'] or data['address']['ipv6']))

	@classmethod
	def _dataExtract(self, data, keys, process = None):
		try:
			result = tools.Tools.dictionaryGet(dictionary = data, keys = keys)
			if process: result = process(result)
			return result
		except: return None

	@classmethod
	def _dataName(self, name):
		return tools.Regex.remove(data = name, expression = '.*(\s[\[\(\{].*$)', group = 1) or name

	@classmethod
	def _dataIp(self, ip = None, ipv4 = None, ipv6 = None):
		if not ipv4 and tools.Regex.match(data = ip, expression = '^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'): ipv4 = ip
		elif not ipv6 and tools.Regex.match(data = ip, expression = '(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'): ipv6 = ip
		return ipv4, ipv6

	@classmethod
	def _dataAnonymize(self, data, anonymize):
		if not anonymize == Geolocator.AnonymizeNone:
			if tools.Tools.isDictionary(data):
				data['address']['ip'] = self._dataAnonymize(data = data['address']['ip'], anonymize = anonymize)
				data['address']['ipv4'] = self._dataAnonymize(data = data['address']['ipv4'], anonymize = anonymize)
				data['address']['ipv6'] = self._dataAnonymize(data = data['address']['ipv6'], anonymize = anonymize)

				data['address']['name'] = None

				if anonymize == Geolocator.AnonymizeObfuscate:
					latitude = data['location']['coordinate']['latitude']
					if latitude: data['location']['coordinate']['latitude'] = tools.Math.round(latitude, places = 2)
					longitude = data['location']['coordinate']['longitude']
					if longitude: data['location']['coordinate']['longitude'] = tools.Math.round(longitude, places = 2)
				elif anonymize == Geolocator.AnonymizeStrip:
					data['location']['coordinate']['latitude'] = None
					data['location']['coordinate']['longitude'] = None
			elif data:
				if anonymize == Geolocator.AnonymizeObfuscate:
					if '.' in data: # IPv4
						mask = '255.255.255.0'
						parts = 4
					elif ':' in data: # IPv6
						mask = 'ffff:ffff:ffff:ffff:0000:0000:0000:0000'
						parts = 16

					from ipaddress import ip_address
					address = ip_address(data).packed
					mask = ip_address(mask).packed
					packed = bytearray()
					for i in range(0, parts):
						packed.append(mask[i] & address[i])
					data = str(ip_address(bytes(packed)))
				elif anonymize == Geolocator.AnonymizeStrip:
					data = None

		return data

	@classmethod
	def _data(self,
		addressIp = None,
		addressIpv4 = None,
		addressIpv6 = None,
		addressName = None,

		networkProvider = None,
		networkOrganization = None,
		networkSystem = None,

		continentCode = None,
		continentName = None,

		countryCode = None,
		countryName = None,

		regionCode = None,
		regionName = None,

		cityCode = None,
		cityName = None,

		coordinateLatitude = None,
		coordinateLongitude = None,

		timezone = None,

		fill = True,
	):
		from lib.modules.interface import Format

		try: coordinateLongitude = float(coordinateLongitude)
		except: coordinateLongitude = None

		if not addressIpv4: addressIpv4 = None
		if not addressIpv6: addressIpv6 = None
		if not addressName: addressName = None
		addressIpv4, addressIpv6 = self._dataIp(ip = addressIp, ipv4 = addressIpv4, ipv6 = addressIpv6)

		expression = '(asn?\d+)' # ASN number (eg: AS62240)
		if networkProvider:
			asn = tools.Regex.extract(data = networkProvider, expression = expression)
			if asn:
				if not networkSystem: networkSystem = asn.strip()
				networkProvider = tools.Regex.remove(data = networkProvider, expression = expression).strip()
		if networkOrganization:
			asn = tools.Regex.extract(data = networkOrganization, expression = expression)
			if asn:
				if not networkSystem: networkSystem = asn.strip()
				networkOrganization = tools.Regex.remove(data = networkOrganization, expression = expression).strip()

		if not networkProvider: networkProvider = networkOrganization if networkOrganization else None
		if not networkOrganization: networkOrganization = networkProvider if networkProvider else None
		if not networkSystem: networkSystem = None

		if continentCode:
			try: continentCode = continentCode.lower()
			except: continentCode = None
		else: continentCode = None
		if not continentName: continentName = None
		if continentName: continentName = self._dataName(continentName)

		if countryCode:
			try: countryCode = countryCode.lower()
			except: countryCode = None
		else: countryCode = None
		if not countryName: countryName = None
		if countryCode and not countryName: countryName = tools.Country.name(countryCode)
		elif countryName and not countryCode: countryCode = tools.Country.name(countryName)
		if countryName: countryName = self._dataName(countryName)

		if regionCode:
			try: regionCode = regionCode.lower()
			except: regionCode = None
		else: regionCode = None
		if not regionName: regionName = None
		if regionName: regionName = self._dataName(regionName)

		if cityCode:
			try: cityCode = cityCode.lower()
			except: cityCode = None
		else: cityCode = None
		if not cityName: cityName = None
		if cityName: cityName = self._dataName(cityName)

		if coordinateLatitude:
			try: coordinateLatitude = float(coordinateLatitude)
			except: coordinateLatitude = None
		else: coordinateLatitude = None
		if coordinateLongitude:
			try: coordinateLongitude = float(coordinateLongitude)
			except: coordinateLongitude = None
		else: coordinateLongitude = None

		if not timezone: timezone = None

		if fill and (addressIpv4 or addressIpv6):
			data = self.location(
				continentCode = continentCode,
				continentName = continentName,

				countryCode = countryCode,
				countryName = countryName,

				regionCode = regionCode,
				regionName = regionName,

				cityCode = cityCode,
				cityName = cityName,

				coordinateLatitude = coordinateLatitude,
				coordinateLongitude = coordinateLongitude,

				timezone = timezone,
			)
			continentCode = data['continent']['code']
			continentName = data['continent']['name']

			countryCode = data['country']['code']
			countryName = data['country']['name']

			regionCode = data['region']['code']
			regionName = data['region']['name']

			cityCode = data['city']['code']
			cityName = data['city']['name']

			coordinateLatitude = data['coordinate']['latitude']
			coordinateLongitude = data['coordinate']['longitude']

			timezone =  data['timezone']

		if not regionName and cityName: regionName = cityName

		labelFull = [continentName, countryName, regionName, cityName]
		labelFull = tools.Tools.listUnique([i for i in labelFull if i])

		labelShort = []
		if countryName: labelShort.append(countryName)
		elif continentName: labelShort.append(continentName)
		if cityName: labelShort.append(cityName)
		elif regionName: labelShort.append(regionName)
		labelShort = tools.Tools.listUnique(labelShort)

		labelLong = tools.Tools.copy(labelShort)
		if continentName: labelLong.insert(0, continentName)
		labelLong = tools.Tools.listUnique(labelLong)

		return {
			'address' : {
				'ip' : addressIpv4 or addressIpv6,
				'ipv4' : addressIpv4,
				'ipv6' : addressIpv6,
				'name' : addressName,
			},
			'network' : {
				'provider' : networkProvider,
				'organization' : networkOrganization,
				'system' : networkSystem,
			},
			'location' : {
				'label' : {
					'full' : {
						'icon' : Format.iconJoin(labelFull),
						'comma' : ', '.join(labelFull),
					},
					'long' : {
						'icon' : Format.iconJoin(labelLong),
						'comma' : ', '.join(labelLong),
					},
					'short' : {
						'icon' : Format.iconJoin(labelShort),
						'comma' : ', '.join(labelShort),
					},
				},
				'timezone' : timezone,
				'continent' : {
					'code' : continentCode,
					'name' : continentName,
				},
				'country' : {
					'code' : countryCode,
					'name' : countryName,
				},
				'region' : {
					'code' : regionCode,
					'name' : regionName,
				},
				'city' : {
					'code' : cityCode,
					'name' : cityName,
				},
				'coordinate' : {
					'latitude' : coordinateLatitude,
					'longitude' : coordinateLongitude,
				},
			},
		}

	###################################################################
	# DETECT
	###################################################################

	@classmethod
	def detect(self, anonymize = AnonymizeNone):
		return {'global' : self.detectGlobal(anonymize = anonymize), 'local' : self.detectLocal()}

	@classmethod
	def detectGlobal(self, service = None, key = None, anonymize = AnonymizeNone):
		result = None

		if service is None:
			services = self.services()
			for service in services:
				result = self.detectGlobal(**service)
				if result: break
		else:
			function = tools.Tools.getFunction(self, '_detect' + service.capitalize())
			try: result = function(key = key)
			except: result = function()
			if self.dataValid(result): self.serviceLastSet(service = service, key = key, data = result)
			else: result = None

			log = []
			log.append('Service: %s' % service.capitalize())
			if key: log.append('Key: %s...' % key[:5])
			if result:
				log.append('IP: %s' % result['address']['ip'])
				for i in ['country', 'city', 'region', 'continent']:
					if result['location'][i]['name']:
						log.append('Location: %s' % result['location'][i]['name'])
						break
			else: log.append('Lookup Failure')
			tools.Logger.log('Geolocation Lookup: ' + ' | '.join(log), developer = True)

		return self._dataAnonymize(data = result, anonymize = anonymize)

	@classmethod
	def detectLocal(self):
		import xbmc
		name = None
		if not name:
			try:
				import platform
				name = platform.node()
			except: pass
			if not name:
				try:
					import platform
					name = platform.uname()[1]
				except: pass
				if not name:
					try:
						import os
						name = os.uname()[1]
					except: pass
					if not name:
						try:
							import socket
							name = socket.gethostname()
						except: pass

		ipv4, ipv6 = self._dataIp(ip = xbmc.getIPAddress())
		return {
			'address' : {
				'ip' : ipv4 or ipv6,
				'ipv4' : ipv4,
				'ipv6' : ipv6,
				'name' : name,
			}
		}

	@classmethod
	def detectExternal(self, ip = None, domain = None, service = None, key = None, anonymize = AnonymizeNone):
		result = None

		if ip is None and domain:
			import socket
			domain = Networker.linkDomain(link = domain, subdomain = True, topdomain = True, ip = True, scheme = False)
			try: ip = socket.gethostbyname(domain)
			except: tools.Logger.log('Domain IP Lookup Failure: ' + domain)

		if ip:
			if service is None:
				services = self.services()
				for service in services:
					result = self.detectExternal(ip = ip, **service)
					if result: break
			else:
				function = tools.Tools.getFunction(self, '_detect' + service.capitalize())
				try: result = function(ip = ip, key = key)
				except:
					try: result = function(ip = ip)
					except: return None # Does not support lookup by custom IP.
				if self.dataValid(result): self.serviceLastSet(service = service, key = key, data = result)
				else: result = None

		if result: result['address']['domain'] = domain
		return self._dataAnonymize(data = result, anonymize = anonymize)

	@classmethod
	def _detectRequest(self, link, data = None):
		# Reduce timeout.
		# If this quick/simple request takes longer that 15 secs, it probably means that the service is down (or some other connection issue, non-connected VPN with kill switrch, no internet connection, etc).
		# Use GET to add data as GET and not POST parameters.
		# Do not use the VPN kill switch here, since this function might be called from the VPN code.
		return Networker().requestJson(link = link, data = data, method = Networker.MethodGet, timeout = 15, vpn = False)

	@classmethod
	def _detectIpwhoisapp(self, ip = None):
		try:
			data = self._detectRequest(link = 'https://ipwhois.app/json/%s' % (ip if ip else ''))
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					networkProvider = self._dataExtract(data = data, keys = 'isp'),
					networkOrganization = self._dataExtract(data = data, keys = 'org'),
					networkSystem = self._dataExtract(data = data, keys = 'asn'),
					continentCode = self._dataExtract(data = data, keys = 'continent_code'),
					continentName = self._dataExtract(data = data, keys = 'continent'),
					countryCode = self._dataExtract(data = data, keys = 'country_code'),
					countryName = self._dataExtract(data = data, keys = 'country'),
					regionName = self._dataExtract(data = data, keys = 'region'),
					cityName = self._dataExtract(data = data, keys = 'city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
					timezone = self._dataExtract(data = data, keys = 'timezone'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectIpinfoio(self, ip = None):
		try:
			data = self._detectRequest(link = 'https://ipinfo.io/%sjson' % ((ip + '/') if ip else ''))
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					addressName = self._dataExtract(data = data, keys = 'hostname'),
					networkOrganization = self._dataExtract(data = data, keys = 'org'),
					countryCode = self._dataExtract(data = data, keys = 'country'),
					regionName = self._dataExtract(data = data, keys = 'region'),
					cityName = self._dataExtract(data = data, keys = 'city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'loc', process = lambda x : x.split(',')[0]),
					coordinateLongitude = self._dataExtract(data = data, keys = 'loc', process = lambda x : x.split(',')[1]),
					timezone = self._dataExtract(data = data, keys = 'timezone'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectGeopluginnet(self, ip = None):
		try:
			data = self._detectRequest(link = 'http://geoplugin.net/json.gp%s' % (('?ip=' + ip) if ip else ''))
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'geoplugin_request') or ip,
					continentCode = self._dataExtract(data = data, keys = 'geoplugin_continentCode'),
					continentName = self._dataExtract(data = data, keys = 'geoplugin_continentName'),
					countryCode = self._dataExtract(data = data, keys = 'geoplugin_countryCode'),
					countryName = self._dataExtract(data = data, keys = 'geoplugin_countryName'),
					regionCode = self._dataExtract(data = data, keys = 'geoplugin_regionCode'),
					regionName = self._dataExtract(data = data, keys = 'geoplugin_regionName'),
					cityName = self._dataExtract(data = data, keys = 'geoplugin_city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'geoplugin_latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'geoplugin_longitude'),
					timezone = self._dataExtract(data = data, keys = 'geoplugin_timezone'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectIpapiio(self, ip = None):
		try:
			data = self._detectRequest(link = 'https://ip-api.io/json/%s' % (ip if ip else ''))
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					networkOrganization = self._dataExtract(data = data, keys = 'organisation'),
					countryCode = self._dataExtract(data = data, keys = 'country_code'),
					countryName = self._dataExtract(data = data, keys = 'country_name'),
					regionCode = self._dataExtract(data = data, keys = 'region_code'),
					regionName = self._dataExtract(data = data, keys = 'region_name'),
					cityName = self._dataExtract(data = data, keys = 'city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
					timezone = self._dataExtract(data = data, keys = 'time_zone'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectIpapico(self, ip = None):
		try:
			data = self._detectRequest(link = 'https://ipapi.co/%sjson' % ((ip + '/') if ip else ''))
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					networkOrganization = self._dataExtract(data = data, keys = 'org'),
					networkSystem = self._dataExtract(data = data, keys = 'asn'),
					continentCode = self._dataExtract(data = data, keys = 'continent_code'),
					continentName = self._dataExtract(data = data, keys = 'continent_name'),
					countryCode = self._dataExtract(data = data, keys = 'country_code'),
					countryName = self._dataExtract(data = data, keys = 'country_name'),
					regionCode = self._dataExtract(data = data, keys = 'region_code'),
					regionName = self._dataExtract(data = data, keys = 'region'),
					cityName = self._dataExtract(data = data, keys = 'city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
					timezone = self._dataExtract(data = data, keys = 'timezone'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectDbipcom(self, ip = None):
		try:
			data = self._detectRequest(link = 'https://api.db-ip.com/v2/free/%s' % (ip if ip else 'self'))
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ipAddress') or ip,
					continentCode = self._dataExtract(data = data, keys = 'continentCode'),
					continentName = self._dataExtract(data = data, keys = 'continentName'),
					countryCode = self._dataExtract(data = data, keys = 'countryCode'),
					countryName = self._dataExtract(data = data, keys = 'countryName'),
					regionName = self._dataExtract(data = data, keys = 'stateProv'),
					cityName = self._dataExtract(data = data, keys = 'city'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectGeojsio(self, ip = None):
		try:
			data = self._detectRequest(link = 'https://get.geojs.io/v1/ip/geo.json%s' % (('?ip=' + ip) if ip else ''))
			if data:
				if tools.Tools.isArray(data): data = data[0] # If custom IP is used.
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					networkProvider = self._dataExtract(data = data, keys = 'organization'),
					networkOrganization = self._dataExtract(data = data, keys = 'organization_name'),
					continentCode = self._dataExtract(data = data, keys = 'continent_code'),
					continentName = self._dataExtract(data = data, keys = 'continent'),
					countryCode = self._dataExtract(data = data, keys = 'country_code'),
					countryName = self._dataExtract(data = data, keys = 'country'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
					timezone = self._dataExtract(data = data, keys = 'timezone'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectGeolocationdbcom(self, ip = None):
		try:
			data = self._detectRequest(link = 'https://geolocation-db.com/json/%s' % (ip if ip else ''))
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'IPv4') or ip,
					countryCode = self._dataExtract(data = data, keys = 'country_code'),
					countryName = self._dataExtract(data = data, keys = 'country_name'),
					regionName = self._dataExtract(data = data, keys = 'state'),
					cityName = self._dataExtract(data = data, keys = 'city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectIpgeolocationio(self, ip = None, key = None):
		try:
			data = {'apiKey' : key}
			if ip: data['ip'] = ip
			data = self._detectRequest(link = 'https://api.ipgeolocation.io/ipgeo', data = data)
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					networkProvider = self._dataExtract(data = data, keys = 'isp'),
					networkOrganization = self._dataExtract(data = data, keys = 'organization'),
					continentCode = self._dataExtract(data = data, keys = 'continent_code'),
					continentName = self._dataExtract(data = data, keys = 'continent_name'),
					countryCode = self._dataExtract(data = data, keys = 'country_code2'),
					countryName = self._dataExtract(data = data, keys = 'country_name'),
					regionName = self._dataExtract(data = data, keys = 'district'),
					cityName = self._dataExtract(data = data, keys = 'city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
					timezone = self._dataExtract(data = data, keys = ['time_zone', 'name']),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectGeoapifycom(self, ip = None, key = None):
		try:
			data = {'apiKey' : key}
			if ip: data['ip'] = ip
			data = self._detectRequest(link = 'https://api.geoapify.com/v1/ipinfo', data = data)
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					continentCode = self._dataExtract(data = data, keys = ['continent', 'code']),
					continentName = self._dataExtract(data = data, keys = ['continent', 'name']),
					countryCode = self._dataExtract(data = data, keys = ['country', 'iso_code']),
					countryName = self._dataExtract(data = data, keys = ['country', 'name']),
					regionCode = self._dataExtract(data = data, keys = ['state', 'code']),
					regionName = self._dataExtract(data = data, keys = ['state', 'name']),
					cityName = self._dataExtract(data = data, keys = ['city', 'name']),
					coordinateLatitude = self._dataExtract(data = data, keys = ['location', 'latitude']),
					coordinateLongitude = self._dataExtract(data = data, keys = ['location', 'longitude']),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectIpinfodbcom(self, ip = None, key = None):
		try:
			data = {'key' : key, 'format' : 'json'}
			if ip: data['ip'] = ip
			data = self._detectRequest(link = 'https://api.ipinfodb.com/v3/ip-city/', data = data)
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ipAddress') or ip,
					countryCode = self._dataExtract(data = data, keys = 'countryCode'),
					countryName = self._dataExtract(data = data, keys = 'countryName'),
					regionName = self._dataExtract(data = data, keys = 'regionName'),
					cityName = self._dataExtract(data = data, keys = 'cityName'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
					timezone = self._dataExtract(data = data, keys = 'timeZone'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectIpdataco(self, ip = None, key = None):
		try:
			data = self._detectRequest(link = 'https://api.ipdata.co%s' % (('/' + ip) if ip else ''), data = {'api-key' : key})
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					networkOrganization = self._dataExtract(data = data, keys = ['asn', 'name']),
					networkSystem = self._dataExtract(data = data, keys = ['asn', 'asn']),
					continentCode = self._dataExtract(data = data, keys = 'continent_code'),
					continentName = self._dataExtract(data = data, keys = 'continent_name'),
					countryCode = self._dataExtract(data = data, keys = 'country_code'),
					countryName = self._dataExtract(data = data, keys = 'country_name'),
					regionCode = self._dataExtract(data = data, keys = 'region_code'),
					regionName = self._dataExtract(data = data, keys = 'region'),
					cityName = self._dataExtract(data = data, keys = 'city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
					timezone = self._dataExtract(data = data, keys = ['time_zone', 'name']),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectBigdatacloudnet(self, ip = None, key = None):
		try:
			data = {'key' : key, 'localityLanguage' : 'en'}
			if ip: data['ip'] = ip
			data = self._detectRequest(link = 'https://api.bigdatacloud.net/data/ip-geolocation-full', data = data)
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					networkOrganization = self._dataExtract(data = data, keys = ['network', 'organisation']),
					networkSystem = self._dataExtract(data = data, keys = ['network', 'carriers', 0, 'asn']),
					continentCode = self._dataExtract(data = data, keys = ['location', 'continentCode']),
					continentName = self._dataExtract(data = data, keys = ['location', 'continent']),
					countryCode = self._dataExtract(data = data, keys = ['country', 'isoAlpha2']),
					countryName = self._dataExtract(data = data, keys = ['country', 'name']),
					regionName = self._dataExtract(data = data, keys =  ['location', 'localityName']),
					cityName = self._dataExtract(data = data, keys = ['location', 'city']),
					coordinateLatitude = self._dataExtract(data = data, keys = ['location', 'latitude']),
					coordinateLongitude = self._dataExtract(data = data, keys = ['location', 'longitude']),
					timezone = self._dataExtract(data = data, keys = ['location', 'timeZone', 'ianaTimeId']),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectIpapicom(self, ip = None, key = None):
		try:
			data = self._detectRequest(link = 'http://api.ipapi.com/api/%s' % (ip if ip else 'check'), data = {'access_key' : key}) # HTTPS only for paid accounts.
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					continentCode = self._dataExtract(data = data, keys = 'continent_code'),
					continentName = self._dataExtract(data = data, keys = 'continent_name'),
					countryCode = self._dataExtract(data = data, keys = 'country_code'),
					countryName = self._dataExtract(data = data, keys = 'country_name'),
					regionCode = self._dataExtract(data = data, keys =  'region_code'),
					regionName = self._dataExtract(data = data, keys =  'region_name'),
					cityName = self._dataExtract(data = data, keys = 'city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
				)
		except: tools.Logger.error()
		return None

	@classmethod
	def _detectIpstackcom(self, ip = None, key = None):
		try:
			data = self._detectRequest(link = 'http://api.ipstack.com/%s' % (ip if ip else 'check'), data = {'access_key' : key}) # HTTPS only for paid accounts.
			if data:
				return self._data(
					addressIp = self._dataExtract(data = data, keys = 'ip') or ip,
					continentCode = self._dataExtract(data = data, keys = 'continent_code'),
					continentName = self._dataExtract(data = data, keys = 'continent_name'),
					countryCode = self._dataExtract(data = data, keys = 'country_code'),
					countryName = self._dataExtract(data = data, keys = 'country_name'),
					regionCode = self._dataExtract(data = data, keys =  'region_code'),
					regionName = self._dataExtract(data = data, keys =  'region_name'),
					cityName = self._dataExtract(data = data, keys = 'city'),
					coordinateLatitude = self._dataExtract(data = data, keys = 'latitude'),
					coordinateLongitude = self._dataExtract(data = data, keys = 'longitude'),
				)
		except: tools.Logger.error()
		return None

	###################################################################
	# DIALOG
	###################################################################

	@classmethod
	def dialog(self):
		from lib.modules import interface

		def _value(value1, value2 = None):
			if value1 is None: return interface.Format.fontItalic(33387)
			elif value2 is None: return value1
			else: return '%s (%s)' % (value1, value2.upper())

		interface.Loader.show()
		items = []
		information = self.detect()

		# Local
		data = information['local']
		items.append({
			'title' : 33704,
			'items' : [
				{ 'title' : 33706, 'value' : _value(data['address']['ip']) },
				{ 'title' : 33707, 'value' : _value(data['address']['name']) },
			]
		})

		# Global
		data = information['global']
		items.append({
			'title' : 33705,
			'items' : [
				{ 'title' : 33706, 'value' : _value(data['address']['ip']) },
				{ 'title' : 33710, 'value' : _value(data['network']['provider']) },
				{ 'title' : 33711, 'value' : _value(data['network']['organization']) },
				{ 'title' : 33712, 'value' : _value(data['network']['system']) },
				{ 'title' : 33713, 'value' : _value(data['location']['continent']['name'], data['location']['continent']['code']) },
				{ 'title' : 33714, 'value' : _value(data['location']['country']['name'], data['location']['country']['code']) },
				{ 'title' : 33715, 'value' : _value(data['location']['region']['name'], data['location']['region']['code']) },
				{ 'title' : 33716, 'value' : _value(data['location']['city']['name'], data['location']['city']['code']) },
				{ 'title' : 33717, 'value' : _value(data['location']['coordinate']['latitude']) },
				{ 'title' : 33718, 'value' : _value(data['location']['coordinate']['longitude']) },
			]
		})

		interface.Loader.hide()
		interface.Dialog.information(title = 33703, items = items)


class Resolver(object):

	ModeNone = 'none' # Do not resolve. Must be string.
	ModeProvider = 'provider' # Resolve through the provider only
	ModeService = 'service' # Resolve through provider and service (such as debrid or URLResolver).
	ModeDefault = ModeService

	@classmethod
	def resolve(self, source, clean = True, timeout = None, info = False, internal = True, cloud = False, mode = ModeDefault): # Use timeout with caution.
		from lib.modules.concurrency import Pool

		resolver = Resolver()
		resolver.mLink = None
		if not mode: mode = Resolver.ModeNone
		thread = Pool.thread(target = resolver._resolve, args = (source, clean, info, internal, cloud, mode))
		thread.start()
		if timeout:
			timestep = 0.1
			for i in range(int(timeout / timestep)):
				tools.Time.sleep(timestep)
			if thread.is_alive():
				return None
		else:
			thread.join()
		return resolver.mLink

	def _resolve(self, source, clean = True, info = False, internal = True, cloud = False, mode = ModeDefault):
		# Resolves the link using the providers and urlresolver.
		from lib.modules import core # Must be imported here due to circular imports.
		self.mLink = core.Core().sourceResolve(source, info = info, internal = internal, cloud = cloud, resolve = mode)['link']
		if clean and self.mLink: self.mLink = Networker.linkClean(self.mLink, headersStrip = False)
		return self.mLink


class Container(object):

	Separator = '_'

	# Types

	# Must be the same as stream.py.
	TypeUnknown = None
	TypeTorrent = 'torrent'
	TypeUsenet = 'usenet'
	TypeHoster = 'hoster'

	# Extensions
	ExtensionData = '.dat'
	ExtensionTorrent = '.torrent'
	ExtensionUsenet = '.nzb'
	ExtensionHoster = '.container'

	# Mimes
	MimeData = 'application/octet-stream'
	MimeTorrent = 'application/x-bittorrent'
	MimeUsenet = 'application/x-nzb'
	MimeHoster = 'application/octet-stream'

	# Paths
	PathTemporary = tools.System.temporary()
	PathTemporaryContainer = tools.File.joinPath(PathTemporary, 'containers')
	PathTemporaryContainerData = tools.File.joinPath(PathTemporaryContainer, 'data')
	PathTemporaryContainerTorrent = tools.File.joinPath(PathTemporaryContainer, TypeTorrent)
	PathTemporaryContainerUsenet = tools.File.joinPath(PathTemporaryContainer, TypeUsenet)
	PathTemporaryContainerHoster = tools.File.joinPath(PathTemporaryContainer, TypeHoster)

	# Version
	Version1			= 1 # BitTorrent v1.
	Version2			= 2 # BitTorrent v2.
	VersionAny			= True
	VersionAll			= None
	VersionFallback1	= 'fallback1' # Use v1 and if not available fall back to v2.
	VersionFallback2	= 'fallback2' # Use v2 and if not available fall back to v1.
	VersionFallback		= VersionFallback1
	VersionDefault		= VersionAny

	# Base
	Base16		= 'base16'	# Base16/Hex
	Base32		= 'base32'	# Base32
	Base64		= 'base64'	# Base64
	BaseNone	= None 		# Keep current base encoding
	BaseDefault	= Base16

	# Length

	LengthSha1Base16			= 40	# SHA1 hex encoded.
	LengthSha1Base32Padded		= 32	# SHA1 base32 encoded (with = padding).
	LengthSha1Base32Unpadded	= 32	# SHA1 base32 encoded (without = padding).
	LengthSha1Base64Padded		= 28	# SHA1 base64 encoded (with = padding).
	LengthSha1Base64Unpadded	= 27	# SHA1 base64 encoded (without = padding).

	LengthSha256Base16			= 64	# SHA1 hex encoded.
	LengthSha256Base32Padded	= 56	# SHA1 base32 encoded (with = padding).
	LengthSha256Base32Unpadded	= 52	# SHA1 base32 encoded (without = padding).
	LengthSha256Base64Padded	= 44	# SHA1 base64 encoded (with = padding).
	LengthSha256Base64Unpadded	= 43	# SHA1 base64 encoded (without = padding).

	LengthSha1		= {LengthSha1Base16 : True, LengthSha1Base32Padded : True, LengthSha1Base32Unpadded : True, LengthSha1Base64Padded : True, LengthSha1Base64Unpadded : True}
	LengthSha256	= {LengthSha256Base16 : True, LengthSha256Base32Padded : True, LengthSha256Base32Unpadded : True, LengthSha256Base64Padded : True, LengthSha256Base64Unpadded : True}
	LengthBase16	= {LengthSha1Base16 : True, LengthSha256Base16 : True}
	LengthBase32	= {LengthSha1Base32Padded : True, LengthSha1Base32Unpadded : True, LengthSha256Base32Padded : True, LengthSha256Base32Unpadded : True}
	LengthBase64	= {LengthSha1Base64Padded : True, LengthSha1Base64Unpadded : True, LengthSha256Base64Padded : True, LengthSha256Base64Unpadded : True}
	LengthUnpadded	= {LengthSha1Base32Unpadded : True, LengthSha1Base64Unpadded : True, LengthSha256Base32Unpadded : True, LengthSha256Base64Unpadded : True}
	LengthUpper		= {LengthSha1Base16 : True, LengthSha1Base32Padded : True, LengthSha1Base32Unpadded : True, LengthSha256Base16 : True, LengthSha256Base32Padded : True, LengthSha256Base32Unpadded : True}

	# Prefix
	PrefixMagnet		= 'magnet:'
	PrefixUrn			= 'urn:'
	PrefixSha1			= 'urn:btih:'
	PrefixSha256		= 'urn:btmh:'

	# Expression
	ExpressionPrefix	= 'urn:bt[im]h:'
	ExpressionHash		= 'xt=urn:bt[im]h:([a-z\d\/\+=]+)(?:$|&)'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	# link: link, magnet, hash, or local path.
	# download: automatically download the torrent or NZB file.
	def __init__(self, link, download = False):
		self.linkSet(link)
		self.downloadSet(download)

	##############################################################################
	# INTERNAL
	##############################################################################

	# GENERAL

	def _type(self, link):
		# Check Magnet
		if self._torrentIsMagnet(link = link):
			return Container.TypeTorrent

		# Check Extensions
		if self._torrentIsExtension(link = link):
			return Container.TypeTorrent
		elif self._usenetIsExtension(link = link):
			return Container.TypeUsenet

		# Check Local Files
		if self._torrentIsFile(link = link, local = True):
			return Container.TypeTorrent
		elif self._usenetIsFile(link = link, local = True):
			return Container.TypeUsenet

		# Check Providers
		if self._torrentIsProvider(link = link):
			return Container.TypeTorrent
		elif self._usenetIsProvider(link = link):
			return Container.TypeUsenet

		# Check Online Files
		if self._torrentIsFile(link = link, local = False):
			return Container.TypeTorrent
		elif self._usenetIsFile(link = link, local = False):
			return Container.TypeUsenet

		# No Type Found
		return Container.TypeUnknown

	def _hash(self, link, type = None):
		if type is None: type = self._type(link)

		if type == Container.TypeTorrent: return self._torrentHash(link)
		elif type == Container.TypeUsenet: return self._usenetHash(link)
		else: return None

	def _extension(self, link, type = None):
		if type is None: type = self._type(link)

		if type == Container.TypeTorrent: return Container.ExtensionTorrent
		elif type == Container.TypeUsenet: return Container.ExtensionUsenet
		elif type == Container.TypeHoster: return Container.ExtensionHoster
		else: return None

	def _mime(self, link, type = None):
		if type is None: type = self._type(link)

		if type == Container.TypeTorrent: return Container.MimeTorrent
		elif type == Container.TypeUsenet: return Container.MimeUsenet
		elif type == Container.TypeHoster: return Container.MimeHoster
		else: return None

	# CACHE

	def _cache(self, link, type = None, lite = False):
		import os

		mime = None
		extension = None
		size = None
		data = None
		path = None
		name = None
		hash = None
		magnet = None

		if not link is None and not link == '':
			magnet = self._torrentIsMagnet(link)
			if magnet:
				type = Container.TypeTorrent
				hash = self._hash(link = link, type = type)
			else:
				if os.path.exists(link):
					path = link
				else:
					id = self._cacheId(link = link)
					path = self._cacheFind(id = id, type = type)

				if path:
					type = self._type(path)
					name = self._cacheName(path = path)
					data = self._cacheData(path = path)

				if self.mDownload and data is None and not self.mDownloadFailed:
					counter = 0
					while counter < 3:
						counter += 1
						response = Networker().request(link = link)
						data = response['data']
						name = response['meta']['name']
						if data is None or data == '':
							# Certain servers (eg: UsenetCrawler) block consecutive or batch calls and mark them as 503 (temporarily unavailable). Simply wait a bit and try again.
							if response['error']['code'] == 503 and not response['error']['type'] == Networker.ErrorCloudflare:
								tools.Time.sleep(1)
							else:
								self.mDownloadFailed = True
								break
						else:
							self._cacheInitialize()
							if self._usenetIsData(data):
								data = data.replace(b'\r', b'') # Very important, otherwise the usenet hashes on Premiumize's server and the local hashes won't match, because the local file got some extra \r.

							path = self._cachePath(type = type, id = id, name = name)
							tools.File.writeNow(path, data, bytes = True, native = True)

							type = self._type(path)
							if not type == Container.TypeUnknown:
								pathNew = self._cachePath(type = type, id = id, name = name)
								tools.File.move(path, pathNew)
								path = pathNew

							break

				base = path if link is None else link
				if not name and not base is None:
					name = tools.File.name(base)

			if not lite and path:
				size = tools.File.size(path)
				mime = self._mime(link = path, type = type)
				extension = self._extension(link = path, type = type)
				hash = self._hash(link = path, type = type)

		return {'type' : type, 'hash' : hash, 'name' : name, 'mime' : mime, 'magnet' : magnet, 'link' : link, 'path' : path, 'extension' : extension, 'size' : size, 'data' : data}

	def _cacheInitialize(self):
		try:
			tools.File.makeDirectory(Container.PathTemporaryContainerData)
			tools.File.makeDirectory(Container.PathTemporaryContainerTorrent)
			tools.File.makeDirectory(Container.PathTemporaryContainerUsenet)
			tools.File.makeDirectory(Container.PathTemporaryContainerHoster)
		except:
			pass

	def _cacheClear(self):
		try:
			tools.File.delete(Container.PathTemporaryContainer, force = True)
		except:
			pass

	def _cacheId(self, link):
		return tools.Hash.sha1(link)

	def _cachePath(self, type, id, name = None):
		path = None
		try:
			if type == Container.TypeTorrent:
				path = Container.PathTemporaryContainerTorrent
				extension = Container.ExtensionTorrent
			elif type == Container.TypeUsenet:
				path = Container.PathTemporaryContainerUsenet
				extension = Container.ExtensionUsenet
			elif type == Container.TypeHoster:
				path = Container.PathTemporaryContainerHoster
				extension = Container.ExtensionHoster
			else:
				path = Container.PathTemporaryContainerData
				extension = Container.ExtensionData

			if name is None:
				name = id
			else:
				name = id + Container.Separator + name

			if not name.endswith(extension):
				name += extension
			path = tools.File.joinPath(path, name)
		except:
			pass
		return path

	def _cacheName(self, path):
		name = tools.File.name(path)
		if name:
			index = name.find(Container.Separator)
			if index >= 0:
				name = name[index + 1:]
		return name

	def _cacheData(self, path):
		if not path or Networker.linkIs(link = path, magnet = True): return None
		return tools.File.readNow(path, bytes = True, native = True)

	def _cacheFind(self, id, type = None):
		try:
			id = id.lower()

			if type == Container.TypeTorrent: containers = [Container.PathTemporaryContainerTorrent]
			elif type == Container.TypeUsenet: containers = [Container.PathTemporaryContainerUsenet]
			elif type == Container.TypeHoster: containers = [Container.PathTemporaryContainerHoster]
			else: containers = [Container.PathTemporaryContainerTorrent, Container.PathTemporaryContainerUsenet, Container.PathTemporaryContainerHoster]
			containers.append(Container.PathTemporaryContainerData)

			for container in containers:
				if tools.File.existsDirectory(container):
					directories, files = tools.File.listDirectory(container)
					for file in files:
						if file.lower().startswith(id):
							return tools.File.joinPath(container, file)
		except:
			pass
		return None

	# TORRENT

	def _torrentData(self, path, info = True, attribute = None):
		if not path or Networker.linkIs(link = path, magnet = True): return None

		# NB: Do not add a try-catch here, since other function rely on this to fail.
		data = tools.File.readNow(path, bytes = True, native = True) # Native, otherwise bencode cannot decode the data.
		data = Importer.moduleBencode().bdecode(data)
		if info:
			try: data = data[b'info']
			except:
				try: data = data['info']
				except: pass
		if attribute:
			try: data = data[bytes(attribute, 'utf-8')]
			except:
				try: data = data[attribute]
				except: data = None
		return data

	# Link can be a torrent hash, list of torrent hashes (SHA1 and SHA256), or existing magnet link.
	def _torrentMagnet(self, link, title = None, encode = True, tracker = True, parameters = None, version = VersionFallback):
		try:
			if self._torrentIsMagnet(link):
				params = self._torrentMagnetParameters(link = link)
				try:
					hash = [tools.Regex.remove(data = i, expression = Container.ExpressionPrefix) for i in params['xt']]
					del params['xt']
				except: pass
				try:
					if title is None and params['dn']: title = params['dn']
					del params['dn']
				except: pass
				try:
					if (tracker is None or tracker is True) and params['tr']: tracker = params['tr']
					del params['tr']
				except: pass
				if parameters is False: params = []
				elif not parameters is None: params.update(parameters)
				parameters = params
			else:
				if Networker.linkIs(link = link, magnet = False):
					if not title: title = self._torrentName(link = link)
					hash = self._torrentHashFile(link = link, version = None)
				elif tools.Tools.isArray(link):
					hash = link
				else:
					hash = [link]

			return self._torrentMagnetCreate(hash = hash, title = title, tracker = tracker, parameters = parameters, encode = encode, version = version)
		except: tools.Logger.error()

	@classmethod
	def _torrentMagnetCreate(self, hash, title = None, tracker = True, parameters = None, encode = True, version = VersionFallback):
		try:
			values = []

			# Add hashes.
			if not hash: return None
			if not tools.Tools.isArray(hash): hash = [hash]
			for i in hash:
				length = len(i)
				if length in Container.LengthSha1: prefix = Container.PrefixSha1
				elif length in Container.LengthSha256: prefix = Container.PrefixSha256
				else: prefix = Container.PrefixSha256
				values.append(('xt', prefix + i.upper() if length in Container.LengthUpper else i))

			# Use a specific hash/version.
			if version in [Container.Version1, Container.Version2, Container.VersionFallback1, Container.VersionFallback2]:
				prefix = Container.PrefixSha256 if version in [Container.Version2, Container.VersionFallback2] else Container.PrefixSha1
				value = None
				for i in values:
					if i[1].startswith(prefix):
						value = i
						break
				if not value and version in [Container.VersionFallback1, Container.VersionFallback2]: value = values[0]
				if value: values = [value]
				else: values = []

			if not values: return None

			# Add titles.
			if title:
				if not tools.Tools.isArray(title): title = [title]
				values.extend([('dn', i) for i in title])

			# Add other parameters.
			if parameters:
				if tools.Tools.isDictionary(parameters): parameters = [(key, val) for key, val in parameters.items()]
				values.extend(parameters)

			# Add trackers.
			if tracker:
				if tracker is True: tracker = Tracker.trackers()
				elif not tools.Tools.isArray(tracker): tracker = [tracker]
				values.extend([('tr', i) for i in tracker])

			# If multiple values were specified for a single key.
			temp = []
			for i in values:
				if tools.Tools.isArray(i[1]): temp.extend([(i[0], j) for j in i[1]])
				else: temp.append(i)
			values = temp

			# URL-encode parameter values, except URNs.
			if encode: values = [(i[0], self._torrentParameterEncode(i[1])) for i in values]

			# Create the magnet.
			link = Container.PrefixMagnet + '?' + ('&'.join([i[0] + '=' + i[1] for i in values]))
			link = link.replace('/', '%2F') # Some magnet links still have the slash / (urlencode does not encode slashes). This seems to be a problem with RealDebrid. Manually escape these slashes.

			return link
		except: tools.Logger.error()

	def _torrentMagnetBase(self, link):
		return self._torrentMagnet(link = link, title = False, tracker = False, parameters = False)

	@classmethod
	def _torrentMagnetParameters(self, link):
		return Networker.linkParameters(link = link, decode = True, multi = True)

	@classmethod
	def _torrentMagnetTrackers(self, link):
		parameters = self._torrentMagnetParameters(link = link)
		try: return parameters['tr']
		except: return None

	@classmethod
	def _torrentMagnetClean(self, link, tracker = True, decode = True, encode = True, base = BaseDefault, version = VersionAll):
		if self._torrentIsMagnet(link):

			# Replace &amps; with &.
			if decode: link = tools.Regex.replace(data = link, expression = '(&amp;)([a-z]{2}=)', replacement = '&\g<2>')

			hash = None
			title = None
			parameters = self._torrentMagnetParameters(link = link)
			try:
				hash = [self._torrentHashBase(hash = tools.Regex.remove(data = i, expression = Container.ExpressionPrefix), base = base) for i in parameters['xt']]
				del parameters['xt']
			except: tools.Logger.error()
			try:
				title = parameters['dn']
				del parameters['dn']
			except: pass
			try:
				tracker = parameters['tr']
				del parameters['tr']
			except: pass

			return self._torrentMagnetCreate(hash = hash, title = title, tracker = tracker, parameters = parameters, encode = encode, version = version)

		return link

	def _torrentMagnetRename(self, link, title = None, encode = True, replace = True, version = VersionAll):
		try:
			hash = None
			names = None
			parameters = self._torrentMagnetParameters(link = link)
			try:
				hash = parameters['xt']
				del parameters['xt']
			except: tools.Logger.error()
			try:
				names = parameters['dn']
				del parameters['dn']
			except: pass
			try:
				tracker = parameters['tr']
				del parameters['tr']
			except: pass

			if names:
				for i in range(len(names)):
					name = names[i]
					replacement = replace
					if replacement is None:
						expression = tools.Regex.expression(expression = '\.{2,}\s*$')
						if title and (not name or expression.search(name)) and (title and not expression.search(title)):
							if name:
								current = Networker.linkUnquote(name)
								current = current.strip(' ').rstrip('.').rstrip(' ')
								if title.startswith(current): replacement = True
							else:
								replacement = True
					if replacement is True or (replacement is False and not name) or (not name or (replacement and tools.Regex.match(data = name, expression = replacement))):
						names[i] = title
			else:
				names = [title]

			seen = set()
			names = [i for i in names if not (i in seen or seen.add(i))]

			return self._torrentMagnetCreate(hash = hash, title = names, tracker = tracker, parameters = parameters, encode = encode, version = version)

		except: pass
		return link

	def _torrentName(self, link):
		try:
			if self._torrentIsMagnet(link):
				result = parse_qs(urlparse(link).query)['dn']
				if tools.Tools.isArray(result): result = result[0]
				return result
			else:
				path = self._cache(link, lite = True)['path']
				name = self._torrentData(path, info = True, attribute = 'name')
				try: name = str(name, 'utf-8')
				except: name = str(name)
				return name
		except:
			return None

	# local: If true, does not retrieve any data from the internet, only local extensions, names, and files.
	def _torrentIs(self, link, local = False):
		result = self._torrentIsMagnet(link = link) or self._torrentIsExtension(link = link) or self._torrentIsFile(link = link, local = True) or self._torrentIsProvider(link = link)
		if not result and local == False:
			result = self._torrentIsFile(link = link, local = local)
		return result

	@classmethod
	def _torrentIsMagnet(self, link):
		return Networker.linkIsMagnet(link)

	@classmethod
	def _torrentIsExtension(self, link, local = False):
		return link.endswith(Container.ExtensionTorrent)

	def _torrentIsFile(self, link, local = False):
		path = None
		if not local and Networker.linkIs(link):
			path = self._cache(link, lite = True)
			if path and 'path' in path: path = path['path']
			else: return False
		else:
			path = link
		try:
			return bool(self._torrentData(path)) # Will throw an exception if not torrent, or return None if it is a URL.
		except:
			return False

	def _torrentIsProvider(self, link):
		from lib.providers.core.manager import Manager
		link = link.lower()
		providers = Manager.providers(type = Container.TypeTorrent, enabled = True)
		for provider in providers:
			if any(domain in link for domain in provider.linkDomains(subdomain = False)):
				return True
		return False

	def _torrentHash(self, link, version = VersionDefault):
		if self._torrentIsMagnet(link): return self._torrentHashMagnet(link = link, version = version)
		else: return self._torrentHashFile(link = link, version = version)

	@classmethod
	def _torrentHashMagnet(self, link, version = VersionDefault, base = BaseDefault):
		if self._torrentIsMagnet(link):
			hashes = tools.Regex.extract(data = link, expression = Container.ExpressionHash, group = None, all = True)
			if not hashes: return None # If the magnet is malformed and does not contain a hash.

			if version is Container.VersionAny:
				return self._torrentHashBase(hash = hashes[0], base = base)
			elif version == Container.Version1:
				for hash in hashes:
					length = len(hash)
					if length in Container.LengthSha1:
						return self._torrentHashBase(hash = hash, base = base)
			elif version == Container.Version2:
				for hash in hashes:
					length = len(hash)
					if length in Container.LengthSha256:
						return self._torrentHashBase(hash = hash, base = base)
			else:
				return [self._torrentHashBase(hash = hash, base = base) for hash in hashes]

		return None

	def _torrentHashFile(self, link, version = VersionDefault):
		try:
			path = self._cache(link, lite = True)
			if path and 'path' in path: path = path['path']
			else: return None
			try:
				info = self._torrentData(path)
				info = Importer.moduleBencode().bencode(info)
				if version is Container.VersionAny: return tools.Hash.sha1(info)
				elif version == Container.Version1: return tools.Hash.sha1(info)
				elif version == Container.Version2: return tools.Hash.sha256(info)
				else: return [tools.Hash.sha256(info), tools.Hash.sha1(info)]
			except:
				return None
		except:
			return None

	@classmethod
	def _torrentHashBase(self, hash, base = BaseDefault):
		if not hash: return hash
		length = len(hash)

		# Detect current base encoding.
		if length in Container.LengthBase32: current = Container.Base32
		elif length in Container.LengthBase64: current = Container.Base64
		else: current = Container.Base16

		# Pad with '=' if not enough padding is present, otherwise base decoding will fail.
		if length in Container.LengthUnpadded and (current == Container.Base32 or current == Container.Base64): hash += '=' * (-length % 4)

		# Convert to upper, otherwise base decoding will fail.
		if current == Container.Base16 or current == Container.Base32: hash = hash.upper()

		if current == base or base == Container.BaseNone: return hash

		# Decode.
		if current == Container.Base16: hash = tools.Converter.base16From(hash)
		elif current == Container.Base32: hash = tools.Converter.base32From(hash)
		elif current == Container.Base64: hash = tools.Converter.base64From(hash)

		# Encode.
		if base == Container.Base16: hash = tools.Converter.base16To(hash)
		elif base == Container.Base32: hash = tools.Converter.base32To(hash)
		elif base == Container.Base64: hash = tools.Converter.base64To(hash)

		return hash

	@classmethod
	def _torrentParameterEncode(self, value):
		if value and not value.startswith(Container.PrefixUrn): # Do not encode URNs (hash prefixes).
			try: value = Networker.linkUnquote(value, plus = not ' ' in value and not '%20' in value) # If already encoded. Only decode '+' if there are no spaces in the name (assuming the + is a space).
			except: pass
			try: value = Networker.linkQuote(value, plus = False) # Do not use quote_plus for title, otherwise adds + to title in some software.
			except: tools.Logger.error()
		return value

	# USENET

	def _usenetData(self, path):
		if not path or Networker.linkIs(link = path, magnet = True): return None
		return tools.File.readNow(path, native = True) # Native, otherwise zome NZBs fail to read.

	# local: If true, does not retrieve any data from the internet, only local extensions, names, and files.
	def _usenetIs(self, link, local = False):
		result = self._usenetIsExtension(link = link) or self._usenetIsFile(link = link, local = True) or self._usenetIsProvider(link = link)
		if not result and local == False:
			result = self._usenetIsFile(link = link, local = local)
		return result

	def _usenetIsExtension(self, link):
		return link.endswith(Container.ExtensionUsenet)

	def _usenetIsFile(self, link, local = False):
		path = None
		if not local and Networker.linkIs(link):
			path = self._cache(link, lite = True)
			if path and 'path' in path: path = path['path']
			else: return False
		else:
			path = link
		try:
			data = self._usenetData(path)
			return self._usenetIsData(data)
		except: tools.Logger.error()
		return False

	def _usenetIsData(self, data):
		try:
			if not data is None:
				try: data = tools.Converter.unicode(data)
				except: pass
				try: data = data.lower()
				except: pass
				try:
					if b'<!doctype nzb' in data or b'</nzb>' in data:
						return True
				except:
					if '<!doctype nzb' in data or '</nzb>' in data:
						return True
		except: tools.Logger.error()
		return False

	def _usenetIsProvider(self, link):
		from lib.providers.core.manager import Manager
		link = link.lower()
		providers = Manager.providers(type = Container.TypeUsenet, enabled = True)
		for provider in providers:
			if any(domain in link for domain in provider.linkDomains(subdomain = False)):
				return True
		return False

	def _usenetHash(self, link):
		try:
			path = self._cache(link, lite = True)
			if path and 'path' in path: path = path['path']
			else: return None
			try:
				data = self._usenetData(path)
				return tools.Hash.sha1(data)
			except:
				return None
		except:
			return None

	##############################################################################
	# BASICS
	##############################################################################

	def linkSet(self, link):
		if self._torrentIsMagnet(link): self.mLink = link.strip()
		else: self.mLink = Networker.linkClean(link = link, headersStrip = False) # Returns the cleaned link.

	def link(self):
		return self.mLink

	def downloadSet(self, download):
		self.mDownload = download
		self.mDownloadFailed = False

	def download(self):
		return self.mDownload

	def type(self):
		return self._type(self.mLink)

	def extension(self):
		return self._extension(self.mLink)

	def mime(self):
		return self._mime(self.mLink)

	##############################################################################
	# ADVANCED
	##############################################################################

	# Clear local containers.
	def clear(self):
		self._cacheClear()

	# Get the hash of the container.
	def hash(self, type = None):
		return self._hash(link = self.mLink, type = type)

	# Cache the container.
	def cache(self):
		result = self._cache(link = self.mLink)
		return not result['data'] is None

	# Returns a dictionary with the container details.
	def information(self):
		return self._cache(link = self.mLink)

	def isFile(self):
		return self.torrentIsFile() or self.usenetIs()

	##############################################################################
	# TORRENT
	##############################################################################

	# Create a magnet from a hash or existing magnet.
	def torrentMagnet(self, title = None, encode = True, tracker = True, version = VersionFallback):
		return self._torrentMagnet(self.mLink, title = title, encode = encode, tracker = tracker, version = version)

	# Clean magnet link from name and trackers.
	def torrentMagnetBase(self):
		return self._torrentMagnetBase(self.mLink)

	# hash can be a single hash or a list of hashes (eg: a SHA1 and SHA256 hash).
	# title can be a single name or a list of names.
	# parameters can be a list of tuples or dictionary, where the first-entry/dict-key is the parameter name, and the second-entry/dict-value the parameter value or list of values.
	def torrentMagnetCreate(self, title = None, parameters = [], encode = True, tracker = True, version = VersionFallback):
		return self._torrentMagnetCreate(hash = self.mLink, title = title, parameters = parameters, encode = encode, tracker = tracker, version = version)

	# Clean the magnet link:
	#	1. Replace &amps; with &.
	#	2. Replace base32/64-encoded hash with hexadecimal hash.
	#	3. URL-encode all parameters correctly.
	def torrentMagnetClean(self, tracker = True, decode = True, encode = True, base = BaseDefault, version = VersionAll):
		return self._torrentMagnetClean(self.mLink, tracker = tracker, decode = decode, encode = encode, base = base, version = version)

	def torrentTrackers(self):
		return self._torrentMagnetTrackers(self.mLink)

	# Add a name parameter to the magnet.
	# replace = False: Do not add if the magnet already has a name.
	# replace = True: Overwrite if the magnet already has a name.
	# replace = None: Overwrite if the magnet already has a name and the name starts with the new name (excluding trailing dots).
	# replace = string: Overwrite if the magnet already has a name and the name matches a regular expression.
	def torrentMagnetRename(self, title = None, encode = True, replace = True, version = VersionAll):
		return self._torrentMagnetRename(self.mLink, title = title, encode = encode, replace = replace, version = version)

	def torrentName(self):
		return self._torrentName(self.mLink)

	def torrentIs(self):
		return self._torrentIs(self.mLink)

	def torrentIsMagnet(self):
		return self._torrentIsMagnet(self.mLink)

	def torrentIsFile(self):
		return self._torrentIsFile(self.mLink)

	def torrentHash(self):
		return self._torrentHash(self.mLink)

	def torrentHashMagnet(self):
		return self._torrentHashMagnet(self.mLink)

	def torrentHashFile(self):
		return self._torrentHashFile(self.mLink)

	##############################################################################
	# USENET
	##############################################################################

	def usenetIs(self):
		return self._usenetIs(self.mLink)

	def usenetHash(self):
		return self._usenetHash(self.mLink)


class Tracker(object):

	Limit = 25
	Timeout = 10
	Outlier = 1000000000

	# gaiaremove - update these
	# Common Trackers
	# Last update: 2021-09-28
	# Do not add too many trackers. Anything above 150 trackers in a magnet link will cause a failure on Premiumize, most likeley due to GET/POST size limits. Also makes the magnet unnecessarily large for Orion.
	# Trackers are automatically retrieved from newtrackon.com, but keep this list as backup in case newtrackon.com is not accessible.
	# https://newtrackon.com
	# https://github.com/ngosang/trackerslist
	Trackers = {}
	TrackersNew = {}
	TrackersCommon = [
		'udp://open.stealth.si:80/announce',					# 100% uptime (Norway)
		'udp://tracker.torrent.eu.org:451/announce',			# 100% uptime (France)
		'udp://tracker.birkenwald.de:6969/announce',			# 100% uptime (Germany)
		'http://tracker.files.fm:6969/announce',				# 100% uptime (Germany)
		'udp://tracker.beeimg.com:6969/announce',				# 100% uptime (Switzerland)
		'udp://tracker.zerobytes.xyz:1337/announce',			# 100% uptime (Netherlands)
		'udp://tracker.moeking.eu.org:6969/announce',			# 100% uptime (Netherlands)
		'http://tracker.bt4g.com:2095/announce',				# 100% uptime (United States)
		'https://tracker.nanoha.org:443/announce',				# 100% uptime (United States)
		'udp://tracker.cyberia.is:6969/announce',				# 99.9% uptime (Switzerland)
		'udp://exodus.desync.com:6969/announce',				# 99.9% uptime (United States)
		'https://tracker.lilithraws.cf:443/announce',			# 99.9% uptime (United States)
		'udp://tracker.army:6969/announce',						# 99.8% uptime (United States)
		'udp://tracker.bitsearch.to:1337/announce',				# 99.8% uptime (Netherlands)
		'udp://tracker.opentrackr.org:1337/announce',			# 99.6% uptime (Netherlands)
		'udp://explodie.org:6969/announce',						# 99.5% uptime (United States)
		'http://t.nyaatracker.com:80/announce',					# 98.6% uptime (Canada/France/Singapore)
		'udp://bt1.archive.org:6969/announce',					# 98.3% uptime (United States)
		'udp://9.rarbg.com:2890/announce',						# 97.9% uptime (France)
		'udp://tracker.leech.ie:1337/announce',					# 97.7% uptime (Luxembourg)
		'udp://tracker.openbittorrent.com:80/announce',			# 85.3% uptime (Sweden)
		'https://1337.abcvg.info:443/announce',					# 75.6% uptime (United States/Canada)
		'udp://retracker.netbynet.ru:2710/announce',			# 67.0% uptime (Russia)
		'https://tracker.foreverpirates.co:443/announce',		# 54.4% uptime (United States)
	]

	##############################################################################
	# TRACKERS
	##############################################################################

	@classmethod
	def trackers(self, common = True, new = True, http = True, udp = True, limit = Limit):
		id = '_'.join([str(common), str(new), str(http), str(udp), str(limit)])
		if id in Tracker.Trackers: return Tracker.Trackers[id]

		idNew = '_'.join([str(http), str(udp)])
		if new and not idNew in Tracker.TrackersNew:
			type = 'stable'
			if http and udp: type = 'stable'
			elif http: type = 'http'
			elif udp: type = 'udp'

			from lib.modules.cache import Cache
			result = Cache.instance().cacheLong(Networker().requestText, link = 'https://newtrackon.com/api/' + type)
			if result and not result == 'None':
				result = result.split('\n')
				result = [i.strip() for i in result]
				Tracker.TrackersNew[idNew] = [i for i in result if i]

		trackers = []
		if new and idNew in Tracker.TrackersNew: trackers.extend(Tracker.TrackersNew[idNew])
		if common and Tracker.TrackersCommon: trackers.extend(Tracker.TrackersCommon)
		trackers = tools.Tools.listUnique(trackers)

		if not http: [i for i in trackers if not i.startswith('http')]
		if not udp: [i for i in trackers if not i.startswith('udp')]

		if limit: trackers = trackers[:limit]

		Tracker.Trackers[id] = trackers
		return trackers

	##############################################################################
	# CHECK
	##############################################################################

	# Check the latest seed/leech count on trackers.
	# items: Single or list of magnets or hashes.
	# limit: Maximum number of trackers to check. More trackers take longer.
	# timeout: Connection timeout for trackers.
	# excludeOutlier: Some trackers have very large values which are probably incorrect. Exclude these values when calculating minimum/maximum/mean values.
	# excludeFailure: Some trackers fail or have 0 as values with 0 completed downloads. Exclude these values when calculating minimum/maximum/mean values.
	@classmethod
	def check(self, items, limit = Limit, timeout = Timeout, excludeOutlier = True, excludeFailure = True):
		if not items: return None
		scraper = Importer.moduleTorrentTrackerScraper()

		result = {}
		single = False
		if not tools.Tools.isArray(items):
			single = True
			items = [items]

		for item in items:
			magnet = None
			hash = None
			trackers = None

			if Networker.linkIsMagnet(item):
				container = Container(item)
				magnet = item
				hash = container.torrentHash()
				trackers = container.torrentTrackers()
			else:
				hash = item
			hash = hash.lower()

			fails = {}
			value = {
				'magnet' : magnet,
				'hash' : hash,
				'seeds' : {'minimum' : None, 'maximum' : None, 'mean' : None},
				'leeches' : {'minimum' : None, 'maximum' : None, 'mean' : None},
				'completed' : {'minimum' : None, 'maximum' : None, 'mean' : None},
				'tracker' : {},
			}

			if not trackers: trackers = self.trackers()
			if trackers:
				if limit: trackers = trackers[:limit]
				data = scraper.Scraper(trackers = trackers, infohashes = [hash], timeout = timeout).scrape()
				if data:
					for i in data:
						tracker = i['tracker']
						if not i['error']:
							value['tracker'][tracker] = {'seeds' : None, 'leeches' : None, 'completed' : None}
							value['tracker'][tracker]['seeds'] = i['results'][0]['seeders']
							value['tracker'][tracker]['leeches'] = i['results'][0]['leechers']
							value['tracker'][tracker]['completed'] = i['results'][0]['completed']
						if i['error'] or not i['results'][0]['completed']: fails[tracker] = True

			for i in ['seeds', 'leeches', 'completed']:
				if excludeFailure: values = [v for k, v in value['tracker'].items() if not k in fails]
				else: values = list(value['tracker'].values())

				values = [j[i] for j in values]

				# Some trackers, like xxtor.com, have very high values, which are probably incorrect.
				if excludeOutlier: values = [j for j in values if j < Tracker.Outlier]

				value[i]['minimum'] = min(values)
				value[i]['maximum'] = max(values)
				value[i]['mean'] = 0 if len(values) == 0 else int(sum(values) / float(len(values)))

			result[value['hash']] = value

		if single:
			try: return list(result.values())[0]
			except: return None
		else:
			return result
