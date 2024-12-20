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

from lib.modules.tools import Logger, Converter, Tools, Time, Language, Country, Media, Audience, Matcher, Regex
from lib.modules.concurrency import Pool, Lock, Semaphore
from lib.modules.cache import Cache, Memory
from lib.meta.tools import MetaTools

class MetaProvider(object):

	# RELEASE

	ReleaseNew						= 'new'						# Movies, Shows, Seasons, Episodes.
	ReleaseHome						= 'home'					# Movies.
	ReleaseFinale					= 'finale'					# Episodes.
	ReleaseFuture					= 'future'					# Movies, Shows, Seasons, Episodes.

	# COMPANY

	CompanyStudio					= 'studio'					# Studios only.
	CompanyNetwork					= 'network'					# Networks only.
	CompanyVendor					= 'vendor'					# Vendors only.
	CompanyProducer					= 'producer'				# Studios only at the moment.
	CompanyBroadcaster				= 'broadcaster'				# Studios and networks.
	CompanyDistributor				= 'distributor'				# Studios, networks, and vendors.
	CompanyOriginal					= 'original'				# Studios and networks, excluding other major companies.

	# VOTING

	VotingNone						= 'none'					# Allow all without any filtering. Do not use None, since we test the value.
	VotingMinimal					= 'minimal'					# Remove those with very few votes.
	VotingLenient					= 'lenient'					# Only remove those with a very low rating or vote count.
	VotingNormal					= 'normal'					# Remove those generally considered to crappy to watch.
	VotingModerate					= 'moderate'				# Keep decent ones.
	VotingStrict					= 'strict'					# Only keep the best.
	VotingExtreme					= 'extreme'					# Extreme cases.

	# FILTER

	FilterNone						= 0							# Do not apply any filtering and return results as is.
	FilterLenient					= 1							# Apply filtering to remove obviously wrong media, such as removing short films from feature movies.
	FilterStrict					= 2							# Apply filtering to remove wrong media according to Gaia's menus, such as removing documentaries and anime from the standard feature movie menus.

	# CONVERT
	ConvertDirect					= True
	ConvertInverse					= False
	Convert							= {}

	# REGION
	Language						= Language.CodeEnglish		# Default language.
	Country							= Country.CodeUnitedStates	# Default country.

	# TEMP
	Temp							= 'temp'

	# CONCURRENCY
	Concurrency						= 30						# Default maximum concurrent requests. Can be overwritten by subclasses.

	# CACHE
	Cache							= Cache.TimeoutExtended		# Default cache timeout.

	# USAGE
	UsageProperty					= 'GaiaRequests'
	UsageAuthenticatedRequest		= 1000						# Can be overwritten by subclasses.
	UsageAuthenticatedDuration		= 300						# Can be overwritten by subclasses.
	UsageUnauthenticatedRequest		= 1000						# Can be overwritten by subclasses.
	UsageUnauthenticatedDuration	= 300						# Can be overwritten by subclasses.

	# OTHER
	Id								= None
	Name							= None
	Lock							= Lock()
	Instance						= {}

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, account = None):
		self.mAccount = account
		self.mLock = {}
		self.mCache = Cache.instance()
		self.mMetatools = MetaTools.instance()
		self.mLanguage = self.mMetatools.settingsLanguage()
		self.mCountry = self.mMetatools.settingsCountry()

	@classmethod
	def instance(self):
		id = self.id()
		if not id in MetaProvider.Instance:
			MetaProvider.Lock.acquire()
			if not id in MetaProvider.Instance: MetaProvider.Instance[id] = self()
			MetaProvider.Lock.release()
		return self.Instance[id]

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		MetaProvider.Instance = {} # Clear instances, accounts, and class member variables in subclasses.

	##############################################################################
	# ID
	##############################################################################

	@classmethod
	def id(self):
		return self.Id or self._idGenerate()

	@classmethod
	def _idGenerate(self):
		if self.Id is None: self.Id = self.__name__.lower().replace('meta', '')
		return self.Id

	##############################################################################
	# NAME
	##############################################################################

	# Can be overwritten by subclasses.
	@classmethod
	def name(self, id = None):
		if self.Name is None:
			if id is None: id = self.id()
			if len(id) == 4: self.Name = id[:3].upper() + id[3].lower() # IMDb, TMDb, TVDb.
			else: self.Name = id.title() # Trakt, others.
		return self.Name

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self):
		return self.mAccount

	def accountId(self):
		try: return self.mAccount.dataId()
		except: return None

	def accountUser(self):
		try: return self.mAccount.dataUsername()
		except: return None

	def accountKey(self, internal = True):
		try:
			key = self.mAccount.dataKey()
			if not key and internal: key = self.mAccount.key() # TMDb, TVDb
			return key
		except: return None

	def accountValid(self):
		try: return self.mAccount.authenticated()
		except: return False

	def accountAuthenticate(self):
		try: return self.mAccount.authenticate(settings = False)
		except: return False

	##############################################################################
	# EXECUTE
	##############################################################################

	def _execute(self, requests, threaded = None, lock = None):
		result = {}
		if requests:
			if lock is None: lock = True
			if threaded is None: threaded = len(requests) > 1
			if threaded:
				threads = [Pool.thread(target = self._executeFunction, kwargs = {'request' : request, 'result' : result, 'lock' : lock}, start = True) for request in requests]
				[thread.join() for thread in threads]
			else:
				for request in requests: self._executeFunction(request = request, result = result, lock = lock)
		return result

	def _executeFunction(self, request, result, lock):
		try:
			if lock: self._lock(limit = lock)
			result[request['id']] = None
			function = request.get('function') or self._executeRequest
			result[request['id']] = function(**(request.get('parameters') or {}))
		except:
			Logger.error()
		finally:
			if lock: self._unlock(limit = lock)

	# Can be overwritten by subclasses to call their native _request() function if it is not named "_request()".
	def _executeRequest(self, **parameters):
		try: return self._request(**parameters)
		except: Logger.error()

	##############################################################################
	# USAGE
	##############################################################################

	@classmethod
	def usageGlobal(self, authenticated = False, full = False):
		from lib.meta.providers.trakt import MetaTrakt
		from lib.meta.providers.imdb import MetaImdb
		from lib.meta.providers.tmdb import MetaTmdb
		providers = [MetaTrakt, MetaImdb, MetaTmdb]
		usage = {i.id() : i.instance().usage(authenticated = authenticated) for i in providers}
		maximum = max(usage.values())
		if full:
			usage['global'] = maximum
			return usage
		return maximum

	def usage(self, authenticated = False, count = False):
		requests = []
		total = 0.0

		if authenticated is True or authenticated is None:
			requests.extend(self._usageClean(Memory.get(id = self._usageId(authenticated = True), local = True, kodi = True)))
			total += self.UsageAuthenticatedRequest

		if authenticated is False or authenticated is None:
			requests.extend(self._usageClean(Memory.get(id = self._usageId(authenticated = False), local = True, kodi = True)))
			total += self.UsageUnauthenticatedRequest

		if count: return len(requests)
		elif total: return len(requests) / total
		else: return 0.0

	def _usageId(self, authenticated = False):
		return '%s_%s_%s' % (self.UsageProperty, self.id(), str(authenticated))

	def _usageUpdate(self, authenticated = False):
		id = self._usageId(authenticated = authenticated)
		requests = self._usageClean(Memory.get(id = id, local = True, kodi = True))
		requests.append(Time.timestamp())
		Memory.set(id = id, value = requests, local = True, kodi = True)

	def _usageClean(self, requests, authenticated = False):
		if requests:
			threshold = Time.timestamp() - (self.UsageAuthenticatedDuration if authenticated else self.UsageUnauthenticatedDuration) - 1
			return [i for i in requests if i > threshold]
		return []

	##############################################################################
	# CONVERT
	##############################################################################

	@classmethod
	def _convert(self, values, value, inverse = False, default = None):
		id = Tools.id(values)
		if not id in MetaProvider.Convert:
			inversed = {}

			# List and dict values cannot be reversed looked up (eg: MetaTrakt Studios or MetaImdb Companies).
			for k, v in values.items():
				if not Tools.isStructure(v):
					inversed[v] = k
					if Tools.isString(v): inversed[v.lower()] = k # Also add the lower case, for providers like MetaImdb (HTML vs JSON vs CSV genres).

			MetaProvider.Convert[id] = {
				MetaProvider.ConvertDirect : values,
				MetaProvider.ConvertInverse : inversed,
			}

		# Check prefix, so that eg "!anime" can also be looked up.
		data = MetaProvider.Convert[id][MetaProvider.ConvertInverse if inverse else MetaProvider.ConvertDirect]
		if Tools.isArray(value):
			temp = []
			for i in value:
				if Tools.isString(i):
					prefix = i[0]
					if Tools.isAlphabeticNumeric(prefix):
						key = i
						prefix = None
					else:
						key = Tools.stringRemovePrefix(i, prefix)
				else:
					key = i
					prefix = None
				result = data.get(key, key if default is True else default)
				temp.append((prefix + result) if (prefix and result) else result)
			temp = Tools.listFlatten(temp) # TMDb genres.
			return [i for i in temp if not i is None]
		else:
			if Tools.isString(value):
				prefix = value[0]
				if Tools.isAlphabeticNumeric(prefix):
					key = value
					prefix = None
				else:
					key = Tools.stringRemovePrefix(value, prefix)
			else:
				key = value
				prefix = None
			result = data.get(key, key if default is True else default)
			return (prefix + result) if (prefix and result) else result

	@classmethod
	def _convertGenre(self, genre, inverse = False, default = None):
		return self._convert(values = self.Genres, value = genre, inverse = inverse, default = default)

	@classmethod
	def _convertStatus(self, status, inverse = False, default = None):
		return self._convert(values = self.Status, value = status, inverse = inverse, default = default)

	@classmethod
	def _convertCertificate(self, certificate, inverse = False, default = None):
		if not certificate: return certificate
		elif Tools.isArray(certificate): return [self._convertCertificate(certificate = i, inverse = inverse, default = default) for i in certificate]
		else: return Audience.clean(certificate) if inverse else Audience.format(certificate)

	@classmethod
	def _convertAward(self, award, inverse = False, default = None):
		return self._convert(values = self.Awards, value = award, inverse = inverse, default = default)

	@classmethod
	def _convertGender(self, gender, inverse = False, default = None):
		return self._convert(values = self.Genders, value = gender, inverse = inverse, default = default)

	@classmethod
	def _convertPleasure(self, pleasure, inverse = False, default = None):
		pleasures = self._convert(values = MetaTools.pleasure(), value = pleasure, inverse = inverse, default = default)
		if pleasures:
			id = self.id()
			pleasures = [i['provider'][id] for i in pleasures]
		return pleasures

	@classmethod
	def _convertCompany(self, company, inverse = False, default = None):
		type = None
		if Tools.isList(company):
			type = company[1]
			company = company[0]
		elif Tools.isDictionary(company):
			type = next(iter(company.values()))
			company = next(iter(company.keys()))
		result = self._convert(values = self._companies(), value = company, inverse = inverse, default = default)
		if result and type: result = result.get(type)
		return result

	##############################################################################
	# COMPANY
	##############################################################################

	# Virtual
	@classmethod
	def _companies(self):
		return None

	@classmethod
	def company(self, niche = None, company = None, studio = None, network = None, parameters = None, delete = True):
		companies = {}

		def _add(name, type = None):
			name = str(name)
			if not name in companies: companies[name] = []
			if not type or type == 'company': type = MetaProvider.CompanyBroadcaster
			companies[name].append(type)

		if niche:
			niche = Media.stringFrom(niche)
			if Media.isEnterprise(niche):
				for i in MetaTools.company().keys():
					if Media.isMedia(media = niche, type = i):
						_add(name = i, type = Media.type(media = niche, type = Media.Enterprise))

		if company:
			if Tools.isDictionary(company):
				for k, v in company.items(): _add(name = k, type = v)
			else:
				if not Tools.isArray(company): company = [company]
				for i in company: _add(name = i)

		if studio:
			for i in studio if Tools.isArray(studio) else [studio]: _add(name = i, type = MetaProvider.CompanyStudio)

		if network:
			for i in network if Tools.isArray(network) else [network]: _add(name = i, type = MetaProvider.CompanyNetwork)

		if parameters:
			for i in ['company', MetaProvider.CompanyStudio, MetaProvider.CompanyNetwork, MetaProvider.CompanyVendor, MetaProvider.CompanyProducer, MetaProvider.CompanyBroadcaster, MetaProvider.CompanyDistributor, MetaProvider.CompanyOriginal]:
				parameter = parameters.get(i)
				if delete:
					try: del parameters[i]
					except: pass
				if parameter:
					for j in parameter if Tools.isArray(parameter) else [parameter]: _add(name = j, type = i)

		if companies:
			company = {}
			for k, v in companies.items():
				v = Tools.listUnique(v)
				if v: company[k] = v
			if company: return company

		return None

	##############################################################################
	# CACHE
	##############################################################################

	def _cache(self, function, timeout = None, **parameters):
		return self.mCache.cacheSeconds(timeout = self._cacheTimeout() if timeout is None or timeout is True else timeout, function = function, **parameters)

	def _cacheTimeout(self):
		return self.Cache # Use "self" instead of "MetaProvider" so that each subclasses has its own variable.

	def _cacheDelete(self, function, **parameters):
		return self.mCache.cacheDelete(function = function, **parameters)

	###################################################################
	# LOG
	###################################################################

	@classmethod
	def _log(self, message, data1 = None, data2 = None, data3 = None, type = Logger.TypeError):
		data = self.id().upper()
		if message: data += ' ' + message
		data += ': '

		if data1 and Tools.isStructure(data1): data1 = Converter.jsonTo(data1)
		if data2 and Tools.isStructure(data2): data2 = Converter.jsonTo(data2)
		if data3 and Tools.isStructure(data3): data3 = Converter.jsonTo(data3)

		Logger.log(data, data1, data2, data3, type = type)

	@classmethod
	def _error(self):
		Logger.error(self.id().upper())

	##############################################################################
	# CONCURRENCY
	##############################################################################

	def _concurrency(self, limit = None):
		id = self.id()

		if limit is None or limit is True: limit = self._concurrencyLimit()
		elif limit is False: limit = 1

		if not id in self.mLock:
			MetaProvider.Lock.acquire()
			if not id in self.mLock: self.mLock[id] = {}
			MetaProvider.Lock.release()

		if not limit in self.mLock[id]:
			MetaProvider.Lock.acquire()
			if not limit in self.mLock[id]: self.mLock[id][limit] = Lock() if limit <= 0 else Semaphore(limit)
			MetaProvider.Lock.release()

		return self.mLock[id][limit]

	def _concurrencyLimit(self):
		return self.Concurrency # Use "self" instead of "MetaProvider" so that each subclasses has its own variable.

	def _lock(self, limit = None):
		self._concurrency(limit = limit).acquire()

	def _unlock(self, limit = None):
		try: self._concurrency(limit = limit).release()
		except: pass

	##############################################################################
	# DATA
	##############################################################################

	@classmethod
	def _data(self, item, key = None, default = None):
		for i in self._dataKeys(key = key):
			try: item = item[i]
			except: return default
		return item

	@classmethod
	def _dataSet(self, item = None, key = None, value = None, copy = False):
		result = item
		if copy: value = Tools.copy(value)

		key = self._dataKeys(key = key)
		if key:
			for i in key[:-1]:
				if not i in item: item[i] = {}
				item = item[i]
			key = key[-1]

			if key in item:
				entry = item[key]
				if Tools.isDictionary(entry): Tools.update(entry, value)
				elif Tools.isArray(entry): item[key] = Tools.listUnique(entry + (value if Tools.isArray(value) else [value]))
				else: item[key] = value
			else:
				item[key] = value
		else:
			Tools.update(item, value)

		return result

	@classmethod
	def _dataRemove(self, item = None, key = None, clean = False):
		if Tools.isList(item):
			return [self._dataRemove(item = i, key = key, clean = clean) for i in item]
		else:
			result = item
			key = self._dataKeys(key = key)
			if key:
				# Clean if nested objects are empty.
				if clean:
					key = Tools.copy(key)# Copy the key, since since values are deleted from it, and the key is reused if this function is called with mutiple items.
					while key:
						value = item
						for i in key[:-1]:
							try:
								value = value[i]
							except:
								value = None
								break
						if value:
							val = value.get(key[-1])
							if not val and not val is False:
								try: del value[key[-1]]
								except: pass
							del key[-1]
						else:
							break
				else: # Remove last key.
					value = item
					for i in key[:-1]:
						try:
							value = value[i]
						except:
							value = None
							break
					if value:
						try: del value[key[-1]]
						except: pass
			return result

	@classmethod
	def _dataKeys(self, key = None):
		if key and not Tools.isArray(key): key = [key]
		return key

	##############################################################################
	# TEMP
	##############################################################################

	@classmethod
	def _temp(self, item, key = None, default = None):
		return self._data(item = item, key = self._tempKeys(key = key), default = default)

	@classmethod
	def _tempSet(self, item = None, key = None, value = None, copy = False, clean = False):
		if clean and not value is None: value = self._tempRemove(item = value, key = None if clean is True else clean, clean = True)
		return self._dataSet(item = item, key = self._tempKeys(key = key), value = value, copy = copy)

	@classmethod
	def _tempRemove(self, item = None, key = None, clean = False):
		return self._dataRemove(item = item, key = self._tempKeys(key = key), clean = clean)

	# Delete entire "temp" dictionary.
	@classmethod
	def _tempClean(self, item = None):
		return self._dataRemove(item = item, key = self._tempKey())

	@classmethod
	def _tempKeys(self, key = None):
		keys = [self._tempKey(), self.id()]
		if not key is None:
			if Tools.isArray(key): keys.extend(key)
			else: keys.append(key)
		return keys

	@classmethod
	def _tempKey(self):
		return MetaProvider.Temp

	##############################################################################
	# VOTING
	##############################################################################

	@classmethod
	def _voting(self, media, niche, release = None, year = None, date = None, genre = None, language = None, country = None, certificate = None, company = None, status = None, rating = None, votes = None, sort = None, active = None):
		exceptionAll = None
		exceptionDate = None
		exceptionVote = None
		exceptionBest = None
		exceptionPrestige = None

		isBase = False
		isLenient = False
		isAnime = Media.isAnime(niche) or (genre and MetaTools.GenreAnime in genre)
		isDonghua = Media.isDonghua(niche) or (genre and MetaTools.GenreDonghua in genre)

		isNew = release == MetaProvider.ReleaseNew or Media.isNew(niche)
		isHome = release == MetaProvider.ReleaseHome or Media.isHome(niche)
		isFuture = release == MetaProvider.ReleaseFuture or Media.isFuture(niche)

		try: dateStart = date[0]
		except: dateStart = None if Tools.isArray(date) else date
		try: dateEnd = date[1]
		except: dateEnd = None if Tools.isArray(date) else date
		try: dateDifference = abs(Time.timestamp() - (dateEnd or dateStart))
		except: dateDifference = None

		if date and not isFuture:
			future = Time.timestamp(fixedTime = Time.future(days = 1, format = Time.FormatDate), format = Time.FormatDate)
			isFuture = any(not i is None and i > future for i in (date if Tools.isArray(date) else [date]))

		if not dateStart is None and dateStart == dateEnd: # For single day menus. Otherwise too few/no titles might be returned.
			exceptionAll = MetaProvider.VotingMinimal
			exceptionDate = MetaProvider.VotingMinimal
		elif not dateDifference is None and dateDifference <= 1209600 and not isHome: # Titles released within the past 2 weeks. Probably has less votes.
			if active: # IMDb
				pass # Typically has a lot of votes, even for new releases.
			else: # Trakt
				exceptionAll = MetaProvider.VotingMinimal
				exceptionDate = MetaProvider.VotingMinimal
				exceptionVote = MetaProvider.VotingLenient
				exceptionBest = MetaProvider.VotingLenient
				exceptionPrestige = MetaProvider.VotingLenient
		elif not dateDifference is None and dateDifference <= 2678400 and not isHome: # Titles released within the past month. Probably has less votes.
			if active: # IMDb
				pass # Typically has a lot of votes, even for new releases.
			elif not active: # Trakt
				exceptionAll = MetaProvider.VotingLenient
				exceptionDate = MetaProvider.VotingLenient
				exceptionVote = MetaProvider.VotingLenient
				exceptionBest = MetaProvider.VotingLenient
				exceptionPrestige = MetaProvider.VotingLenient
		elif isNew or isHome: # New/home releases have way less votes on Trakt.
			if active: # IMDb
				exceptionVote = MetaProvider.VotingNormal
				exceptionBest = MetaProvider.VotingNormal
				exceptionPrestige = MetaProvider.VotingNormal
			else: # Trakt
				if isHome: # Trakt has very little titles in the DVD calendar.
					exceptionAll = MetaProvider.VotingMinimal
					exceptionDate = MetaProvider.VotingMinimal
					exceptionVote = MetaProvider.VotingMinimal
					exceptionBest = MetaProvider.VotingMinimal
					exceptionPrestige = MetaProvider.VotingMinimal
				else:
					exceptionVote = MetaProvider.VotingMinimal
					exceptionBest = MetaProvider.VotingLenient # Otherwise only 1 or 2 titles are sometimes return.
					exceptionPrestige = MetaProvider.VotingLenient
		elif any(bool(i) for i in [year, date, genre, language, country, certificate, status]): # Be more lenient for submenus, since otherwise often very few items are returned because they have few votes (eg: the normal genre menu Anime).
			exceptionVote = MetaProvider.VotingNormal
			if isAnime or isDonghua:
				exceptionBest = MetaProvider.VotingNormal
				exceptionPrestige = MetaProvider.VotingNormal
			elif language:
				if any(i for i in language if not i in ['en', 'de', 'fr']):
					exceptionBest = MetaProvider.VotingNormal
					exceptionPrestige = MetaProvider.VotingNormal
				else:
					exceptionBest = MetaProvider.VotingModerate
					exceptionPrestige = MetaProvider.VotingModerate
			elif country:
				if any(i for i in country if not i in ['us', 'gb', 'uk', 'ca', 'au', 'de', 'fr', 'jp', 'in']):
					exceptionBest = MetaProvider.VotingNormal
					exceptionPrestige = MetaProvider.VotingNormal
				else:
					exceptionBest = MetaProvider.VotingModerate
					exceptionPrestige = MetaProvider.VotingModerate
			elif certificate and any(i in [Audience.CertificateNr, Audience.CertificateNc17, Audience.CertificateTvma] for i in certificate): # IMDb has very few eg NC-17 rated titles.
				exceptionBest = MetaProvider.VotingNormal
				exceptionPrestige = MetaProvider.VotingNormal
			else:
				exceptionBest = MetaProvider.VotingStrict # For "Best Rated", require more votes, otherwise too many old/foreign films are listed which are over-rated (eg: Comedy genre menu).
				exceptionPrestige = MetaProvider.VotingModerate
		else:
			isBase = not niche or len(niche) <= 1

		if company: # Do not apply on any studios/networks, since those lists are already small.
			exceptionAll = MetaProvider.VotingNone
			exceptionDate = MetaProvider.VotingNone

		if Media.isPleasure(niche): isLenient = True # Too few titles and most have very few votes.
		if genre and MetaTools.GenreNone in genre: isLenient = True # Titles under the "None" genre on Trakt have very few votes.
		if isLenient:
			exceptionAll = MetaProvider.VotingLenient
			exceptionDate = MetaProvider.VotingLenient
			exceptionVote = MetaProvider.VotingLenient
			exceptionBest = MetaProvider.VotingLenient
			exceptionPrestige = MetaProvider.VotingLenient

		if Media.isExplore(niche):
			if Media.isAll(niche):
				if rating is None: rating = exceptionAll or MetaProvider.VotingLenient
				if votes is None: votes = exceptionAll or MetaProvider.VotingLenient
			elif Media.isNew(niche):
				if rating is None: rating = exceptionDate or MetaProvider.VotingLenient
				if votes is None: votes = exceptionDate or MetaProvider.VotingNormal
			elif Media.isHome(niche):
				if votes is None: votes = exceptionDate or MetaProvider.VotingNormal # Otherwise too many unknown titles are returned.
			elif Media.isBest(niche):
				# Do not add this if sorting is supported (eg IMDb), otherwise few results might be returned, especially for niches.
				# Still add for providers that do not support sorting (eg Trakt).
				if rating is None and not sort: rating = MetaProvider.VotingStrict

				# Sometimes less than 250 items are retruned (eg: Action genre Best Rated) with VotingStrict.
				# Make an exception for the main/normal Best menu that does not have any other niches or parameters.
				if votes is None: votes = exceptionBest or (MetaProvider.VotingExtreme if isBase else MetaProvider.VotingModerate)
			elif Media.isWorst(niche):
				if votes is None: votes = MetaProvider.VotingNormal
			elif Media.isPrestige(niche):
				if rating is None: rating = MetaProvider.VotingStrict
				if votes is None: votes = exceptionPrestige or MetaProvider.VotingModerate
			elif Media.isPopular(niche):
				if votes is None: votes = exceptionVote or MetaProvider.VotingModerate
			elif Media.isUnpopular(niche):
				pass
			elif Media.isViewed(niche):
				if votes is None: votes = exceptionVote or MetaProvider.VotingStrict
			elif Media.isGross(niche):
				pass
			elif Media.isAward(niche):
				pass
			elif Media.isTrend(niche):
				pass

		# Do not use voting for future releases, since there are not many votes.
		if isFuture:
			rating = None
			votes = None
		elif not Media.isBest(niche) and not Media.isWorst(niche) and not Media.isPrestige(niche) and not Media.isPopular(niche) and not Media.isUnpopular(niche) and not Media.isViewed(niche):
			if Media.isPoor(niche):
				if votes and not votes == MetaProvider.VotingNone: votes = MetaProvider.VotingMinimal
			elif Media.isBad(niche):
				votes = None

		if rating == MetaProvider.VotingNone: rating = None
		if votes == MetaProvider.VotingNone: votes = None

		return rating, votes

	##############################################################################
	# LOCATION
	##############################################################################

	def language(self, language = None, exclude = False, default = True):
		if default is True: default = MetaProvider.Language
		if language is None or language is True:
			language = self.mLanguage
			if not language and default: language = default
		if exclude:
			if exclude is True: exclude = MetaProvider.Language
			if Tools.isArray(exclude) and language in exclude: return None
			elif language == exclude: return None
		return language

	def country(self, country = None, exclude = False, default = True):
		if default is True: default = MetaProvider.Country
		if country is None or country is True:
			country = self.mCountry
			if not country and default: country = default
		if exclude:
			if exclude is True: exclude = MetaProvider.Country
			if Tools.isArray(exclude) and country in exclude: return None
			elif country == exclude: return None
		return country
