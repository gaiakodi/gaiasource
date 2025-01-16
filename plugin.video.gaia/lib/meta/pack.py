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

from lib.modules.tools import Logger, Tools, Time, Language, Media, Matcher, Regex, Math, System

class MetaPack(object):

	# PROVIDER

	ProviderImdb				= 'imdb'
	ProviderTmdb				= 'tmdb'
	ProviderTvdb				= 'tvdb'
	ProviderTrakt				= 'trakt'

	# NUMBER

	# NB: Only use NumberStandard and NumberSequential in Gaia, since the other number orders can result in incorrect episodes being scraped and played.
	#	Standard:
	#		These are the standard multi-season numbers used by Gaia. Gaia will establish its own native standard numbering by combining the data from all providers.
	#		Individual providers have their own standard numbering, which might differ between providers.
	#		Eg: Dragon Ball Super
	#			TVDb uses multi-season numbering for its standard season.
	#			Trakt/TMDb use a single absolute season.
	#	Absolute:
	#		The absolute numbering as determined by the providers.
	#		Sometimes the absolute order can also contain specials.
	#		In most cases the providers' absolute numbering is the same as the Sequential numbering, that is, all multi-seasons are combined into one and the episodes are numbered sequentially.
	#		NB: However, this is not always the case. Sometimes providers have an absolute order that is very different to the sequential order.
	#		Eg: House
	#			TVDb starts the absolute season at S01E02 with the first standard episode, while S01E01 is a 4min unaired pilot special.
	#			TVDb has a huge gap between S01E111 and S01E133, with the standard S06 added to the end of the absolute season, although their air dates are earlier than those of episodes places before them.
	#			Not sure if this is simply a mistake on TVDb, or if there is a reason for this. Maybe S06 was so bad that people decided to place it last to not create a bad taste for the viewer.
	#			But the absolute season on TVDb has so many issues that it can simply not be used as a reliable order.
	#			For instance, if we scrape S01E02 or play a video from a season pack, it will definitely return the standard E02, and not the standard E01 (which is preceded by the 4min unaired pilot).
	#			Therefore, always use the Sequential order everywhere in Gaia, since this is calculated locally, irrespective of what the provider has listed as absolute number.
	#			Trakt/TMDb use multi-seasons, and do not even have alternative seasons listed on their website.
	#			However, Trakt also lists the "absolute" number of the standard S01E01 as "2", not "1".
	#			Not sure why, since they do not have alternative seasons (unlike for other shows like Dragon Ball Super). Maybe this is a number extracted from old TVDb data.
	#			Although Trakt has the first episode with an "absolute" number of "2", the unaired pilot in S0 does not have an "absolute" number of "1", but instead "0" like for all other specials.
	#			So the "true" absolute order cannot even be established, since absolute "1" does not technically exist on Trakt/TMDb.
	#			TVDb also does not have the unaired pilot listed under the absolute season "Season 1", but instead under the absolute season "Unassigned Episodes".
	#			So overall, it does not seem to be a good idea to use any of the TVDb, Trakt, or TMDb absolute season in Gaia, since it will in cases like this scrape/play the wrong episode, use the wrong metadata, etc.
	#	Sequential:
	#		The "absolute" number as calculated natively by Gaia.
	#		This is the numbering that should be used in Gaia for Absolute menus, scraping, etc.
	#		Sequential numbering does not contain specials, unlike absolute season which sometimes can.
	#		In most cases the sequential and absolute orders will be the same.
	#		Eg: Dragon Ball Super
	#		But in other cases they might slightly or substantially differ.
	#		Eg: House
	#		Eg: Dragon Ball (the original series)
	#	Combined:
	#		Sometimes some providers have multiple episodes combined into one.
	#		This is sometimes done if the episodes are very short (5-15 mins), typically for kids shows.
	#		Eg: Star Wars: Young Jedi Adventures
	#			TVDb has its standard season use the individual/uncombined episodes. Although they do have a "Combined" alternative season as well.
	#			Trakt/TMDb use combined episodes.
	#		This is currently not supported, due to the extra complexity.
	#		But generally, this should not be an issue to implement for a future update. The lookup table should just return multiple numbers for combined episodes.
	#		But custom rules will have to be added to scraping, playback, and Trakt syncing.
	#		Plus we have a similar issue to absolute numbers, that the same number between combined and uncombined episodes can be a completely different episode.
	#		Eg: Star Wars: Young Jedi Adventures S01E05 (TVDb vs Trakt).
	#	Alternative:
	#		We could add additional number orders in the future, without having to change a lot in MetaPack.
	#		We would just have to add this ne number to each episode object, annd then add an additional category in the lookup table.
	#		Eg: Aired episode order (without specials)
	#		Eg: Aired episode order (with specials)
	#		Eg: Story/saga order (although not sure how to get specials that are part of the story from the pack data, eg: Downton Abbey S00E02. Check TVDb's "finaleType" and "isMovie").
	#		Again, these should probably NOT BE USED, since their absolute episode numbering will interfere with the real standard and sequential numbering.

	NumberStandard				= 'standard'		# A show with multiple season, each season containing multiple episodes. Eg: S01E01 or S02E03.
	NumberSequential			= 'sequential'		# A show with a single season, constructed from the standard seasons, where all episodes are numbered sequential, excluding specials. Eg: S01E01 or S01E123.
	NumberAbsolute				= 'absolute'		# A show with a single season, containing all or most of the standard episodes, and sometimes specials. Absolute numbers are determined by the provider and are mostly, but not always, the same as sequential. Eg: S01E01 or S01E123. Eg: House has a special as S01E01 and the standard first episode as S01E02.
	NumberSpecial				= 'special'			# Special episodes, such as Christmas Specials, that are added as an additional episode to the end of the season. This is mostly done by IMDb (eg: Downton Abbey S05E09), whereas Trakt/TMDb/TVDb typically put these into the specials season S00. Eg: the season runs officially until S02E10, but there is an extra special episode S02E11, which should actually be S00E27.

	NumberOfficial				= 'official'		# Internal. Not used as a number, but used as a type to indicate an episode is part of the official seasons using a official numbering, typically that of Trakt.
	NumberUnofficial			= 'unofficial'		# Internal. Not used as a number, but used as a type to indicate an episode is not part of the official seasons, typically non-Trakt episodes or other specials.
	NumberUniversal				= 'universal'		# Internal. All standard episodes, specials, and sequential episodes in one lookup table. Hence, we can retrieve any standard/special/sequential episode with the same lookup table. Also used as a type to indicate an episode is is shared among all providers.
	NumberSerie					= 'serie'			# Internal. For constructing Series menus.
	NumberCustom				= 'custom'			# Internal. For Trakt which sometimes uses season-based seasons, but within each season use the absolute episode number (eg: One Piece).
	NumberAutomatic				= 'automatic'		# Internal. Sequential episodes that were added automatically to allow lookups of the real episode number, using the sequential number. However, these episodes do not have metadata on any of the providers and are not considered real sequential episodes, and just point to one of the standard episodes.

	# PART

	PartSeason					= 0					# The index of the season number in the episode's number list.
	PartEpisode					= 1					# The index of the episode number in the episode's number list.

	# STATUS
	# Make sure these correspond with MetaData.Status and MetaTools.Status.

	StatusRumored				= 'rumored'
	StatusPlanned				= 'planned'
	StatusScripted				= 'scripted'
	StatusPreproduction			= 'preproduction'
	StatusProduction			= 'production'
	StatusPostproduction		= 'postproduction'
	StatusCompleted				= 'completed'
	StatusReleased				= 'released'
	StatusPilot					= 'pilot'
	StatusUpcoming				= 'upcoming'
	StatusContinuing			= 'continuing'
	StatusEnded					= 'ended'
	StatusCanceled				= 'canceled'

	# VALUE
	ValueCount					= 'count'
	ValueTotal					= 'total'
	ValueMean					= 'mean'
	ValueMinimum				= 'minimum'
	ValueMaximum				= 'maximum'
	ValueValues					= 'values'
	ValueRange					= 'range'
	ValueIndex					= 'index'
	ValueNumber					= 'number'
	ValueSeason					= 'season'
	ValueEpisode				= 'episode'
	ValueSpecial				= 'special'

	ExpressionGeneric			= '^\s*(?:episode|part)[\s\-\_\.]*(?:\d|[ivxlcd])+'
	Instance					= {}

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, pack = None):
		self.mMatch = {}
		self.mLookup = {}
		self.mEpisode = {}
		self.mMedia = None
		self.mMovie = None
		self.mShow = None
		self.mPack = None
		self.mReduce = None
		self._initialize(pack = pack)

	# Use a singleton if the pack data is the same.
	# We can then reuse the populated lookup table variables from the same instance.
	@classmethod
	def instance(self, pack):
		if self.instanceIs(pack = pack, dictionary = False): return pack
		id = self.instanceId(pack = pack)
		instance = MetaPack.Instance.get(id)
		if not instance: instance = MetaPack.Instance[id] = MetaPack(pack = pack)
		return instance

	@classmethod
	def instanceIs(self, pack, dictionary = True):
		if Tools.isInstance(pack, MetaPack): return True
		if dictionary and Tools.isDictionary(pack) and ('seasons' in pack or 'movies' in pack): return True
		return False

	@classmethod
	def instanceId(self, pack):
		if pack is None: return None
		if Tools.isInstance(pack, MetaPack): return id(pack.mPack)
		else: return id(pack)

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		MetaPack.Instance = {}

	##############################################################################
	# INITIALIZE
	##############################################################################

	def _initialize(self, pack):
		try:
			self.mPack = pack

			if pack:
				media = pack.get('media')
				if media: self.mMedia = media
				elif 'seasons' in pack: self.mMedia = Media.Show
				elif 'movies' in pack: self.mMedia = Media.Movie
				if self.mMedia == Media.Show: self.mShow = True
				elif self.mMedia == Media.Movie: self.mMovie = True

				if self.mShow:
					# JSON-encoding changes integer keys to strings.
					# Change them back to integers after JSON-decoding.
					# This is very fast, taking +-0ms (zero).
					try: string = Tools.isString(next(iter(pack.get('lookup').get(MetaPack.ValueSeason).get(MetaPack.NumberStandard))))
					except: string = False
					if string:
						def _cast(value):
							# Sometimes the episode number can be None (eg: House), which then gets converted to the string "null" during JSON-encoding.
							# This then fails to cast to int.
							try: return int(value)
							except: return None

						lookup = {}
						for k1, v1 in pack.get('lookup').items():
							lookup[k1] = {}
							for k2, v2 in v1.items():
								lookup[k1][k2] = {}
								for k3, v3 in v2.items():
									lookup[k1][k2][_cast(k3)] = v3 if k1 == MetaPack.ValueSeason else {_cast(k4) : v4 for k4, v4 in v3.items()}
						pack['lookup'] = lookup
					self.mLookup = pack.get('lookup')

					# Create episode lists for each season type/numbering, to improve efficieny when these lists are needed repeatedly. Eg: numberLast().
					# Since only the standard season order is stored in the JSON.
					if self.mLookup: # Can be a summarized pack without a lookup table and season/episode lists.
						for i in [MetaPack.NumberSequential, MetaPack.NumberAbsolute]: # Not for MetaPack.NumberUniversal.
							lookup = self.lookup(season = True, episode = True, input = i)
							episodes = []
							for s, v1 in lookup.items():
								for e, v2 in v1.items():
									index = v2[MetaPack.ValueIndex]
									if index:
										season = index[MetaPack.PartSeason]
										episode = index[MetaPack.PartEpisode]
										if not season is None and not episode is None:
											try:
												episodes.append(pack['seasons'][season]['episodes'][episode])
											except:
												# This should not happen, except if there is a bug in generateShow() that causes an episode mismatch, or there is a missing episode number.
												# Update: This seems to sometimes happen if a lot of packs are generated one after the other, eventually causing Trakt not to return any metadata (probably hit the rate limit).
												# Then no episodes have the Trakt numbers and the lookup table generation fails.
												# Update: These errors always seem to be caused by missing Trakt data.
												# But it should not be a huge issue. Since the pack will be marked as "partial" in MetaCache, and refreshed in the near future, which should fix the pack.
												# Not sure if this is always caused by the Trakt rate limit, or if sometimes Trakt just does not return these huge data structures (eg: connection aborted or an exception thrown in Gaia somewhere that causes the Trakt data to be incomplete or not passed on).

												message = pack.get('title') if pack else None
												if message: message = message[0]
												if not message: message = ''
												imdb = pack.get('imdb')
												if imdb: message += ' (%s)' % imdb
												message += ' S%sE%s' % (str(season), str(episode))

												Logger.error(message)
							self.mEpisode[i] = episodes

			return self.mPack
		except:
			message = pack.get('title') if pack else None
			if message: message = message[0]
			Logger.error(message)
			return False

	##############################################################################
	# EXTRACT
	##############################################################################

	@classmethod
	def _extract(self, data, key, default = None):
		result = None
		if data:
			if Tools.isArray(data):
				results = []
				for i in data:
					result = self._extract(data = i, key = key, default = None)
					if not result is None: results.append(result)
				return results if results else default
			else:
				if Tools.isArray(key):
					temp = data
					for i in key:
						try: temp = temp.get(i)
						except: break # Reached a non-dict value.
						if temp is None: return default
					result = temp
				else:
					result = data.get(key)
		return default if result is None else result

	@classmethod
	def _extractSelect(self, data, key):
		result = None
		for i in data:
			result = self._extract(data = i, key = key)
			if result or result is False or result == 0: break
		return result

	@classmethod
	def _extractList(self, data, key, default = None):
		results = []
		for i in data:
			result = self._extract(data = i, key = key)
			if result: results.extend(result)
		if results: return Tools.listUnique(results)
		else: return default

	@classmethod
	def _extractDict(self, data, key):
		results = {}
		for i in reversed(data): # Reverse, since we want to replace the values from least to most important provider.
			result = self._extract(data = i, key = key)
			if result:
				if not results: results = Tools.copy(result) # Important to copy here, otherwise internal dicts/lists (eg: "number") can get mixed up if updated below.
				else: results = Tools.update(results, result, none = False, lists = False, unique = False)
		return results

	@classmethod
	def _extractMaximum(self, data, key):
		results = []
		for i in data:
			result = self._extract(data = i, key = key)
			if not result is None: results.append(result)
		if results: return max(results)
		else: return None

	@classmethod
	def _extractId(self, data, provider = None, default = None):
		if provider: return self._extract(data, ['id', provider], default)
		else: return self._extract(data, 'id', default)

	@classmethod
	def _extractType(self, data, type = None, default = None):
		if type: return self._extract(data, ['type', type], default)
		else: return self._extract(data, 'type', default)

	@classmethod
	def _extractTitle(self, data, default = None):
		return self._extract(data, 'title', default)

	@classmethod
	def _extractNumber(self, data, number = None, part = None, provider = None, default = None):
		key = ['number']
		if not provider is None: key.append(provider)
		if not number is None: key.append(number)
		result = self._extract(data, key, default)
		if not part is None:
			try: return result[part]
			except: return default
		return result

	@classmethod
	def _extractDuration(self, data, key):
		result = None
		for i in data:
			result = self._extract(data = i, key = key)
			if result: break # Ignore "0 secs" durations.
		return result

	@classmethod
	def _extractMovies(self, data):
		return self._extract(data, 'movies', [])

	@classmethod
	def _extractSeasons(self, data):
		return self._extract(data, 'seasons', [])

	@classmethod
	def _extractEpisodes(self, data):
		return self._extract(data, 'episodes', [])

	##############################################################################
	# CREATE
	##############################################################################

	@classmethod
	def _createTitle(self, data, language, setting):
		# Only keep the default title, original title, English title, and the titles according to the user's metadata language setting.
		# Otherwise the pack data becomes too large, and we do not need all those other titles in any case.
		result = []

		for i in data:
			title = i.get('title')
			if title: result.append((5, title))

			alias = i.get('alias')
			if alias:
				for k, v in alias.items():
					if k in language: result.append((3, v))
					elif k == setting: result.append((2, v))
					elif k == Language.CodeEnglish: result.append((1, v))

		result = Tools.listSort(result, key = lambda i : i[0], reverse = True)
		result = [i[1] for i in result]
		return Tools.listUnique(Tools.listFlatten(result))

	@classmethod
	def _createNumber(self, data, provider = None):
		if Tools.isArray(data):
			# Trakt sometimes uses season-based numbering for the season, but inside the season, the episode number is absolute.
			# Eg: One Piece - the 1st episode of S02 on Trakt is S02E62, not S02E01, where 62 is the absolute number.
			# TVDb uses proper season-episode numbering for One Piece, but has different seasons and different episode counts in each season, and has a bunch of specials that are part of the normal Trakt season (eg: TVDb S00E56 vs Trakt S01E1121).
			# In MetaTrakt.pack() we add the custom calculated season number which we then use
			temp = []
			for i in data:
				season = self._extractNumber(i, MetaPack.NumberCustom)
				if season:
					standard = self._extractNumber(i, MetaPack.NumberStandard)
					if standard and not standard == season:
						i = {MetaPack.ValueNumber : Tools.copy(self._extractNumber(i))}
						i[MetaPack.ValueNumber][MetaPack.NumberStandard] = season
				temp.append(i)
			data = temp
			number = self._extractDict(data = data, key = 'number')
		else:
			number = self._extract(data = data, key = 'number')

		# Copy (create new structure), since we use it for sub-dicts.
		# Copy manually, so we can get the number type in a specific order.
		result = {
			MetaPack.NumberStandard		: number.get(MetaPack.NumberStandard),
			MetaPack.NumberSequential	: number.get(MetaPack.NumberSequential),
			MetaPack.NumberAbsolute		: number.get(MetaPack.NumberAbsolute),
		}

		if not provider:
			for i in [MetaPack.ProviderTrakt, MetaPack.ProviderTvdb, MetaPack.ProviderTmdb, MetaPack.ProviderImdb]:
				num = number.get(i) or {}
				result[i] = {
					MetaPack.NumberStandard		: num.get(MetaPack.NumberStandard),
					MetaPack.NumberSequential	: num.get(MetaPack.NumberSequential),
					MetaPack.NumberAbsolute		: num.get(MetaPack.NumberAbsolute),
				}

		# Always use the sequential/absolute numbers from Trakt if available.
		# Since different providers can have different episodes and numbering, the sequential/absolute numbers might deviated between providers.
		#	Eg: House: one extra episode on Trakt (S06E22).
		#	Eg: One Piece (Anime): difference in numbering in S21-end and S22-start between Trakt and TVDb.
		# Otherwise the sequential/absolute order can be screwed up if providers deviate from each other.
		trakt = number.get(MetaPack.ProviderTrakt)
		if trakt:
			for i in [MetaPack.NumberSequential, MetaPack.NumberAbsolute]:
				value = trakt.get(i)
				if value: result[i] = value

		return result

	@classmethod
	def _createSupport(self, data, support):
		# Determine the best provider for the episode, depending on the season support and whether or not the specific episode is available from the provider.
		# Prefer the providers with ID+number, then ID only, then number only, then the rest.
		# This is mainly for TMDb which does not have detailed episode metadata, but the episodes numbers are created automatically from the season episode count.
		# This might not always be correct, especially for S00, since the episode number and episode count do not always match.
		# Eg: GoT S00E08 is not available on Trakt/TMDb (at least not the specific number S00E08), but Gaia generates a dummy episode object in MetaTmdb.pack(), containing only the episode number S00E08, but not any IDs/titles (except for S01).
		if support:
			temp = [[], [], [], []]
			for i in support:
				for j in data:
					id = not self._extractId(j, i) is None
					number = not self._extractNumber(j, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = i) is None
					temp[0 if (id and number) else 1 if id else 2 if number else 3].append((i, j))
			temp = Tools.listFlatten(temp, recursive = False)
			default = temp[0][1]
			supports = Tools.listUnique([i[0] for i in temp])
			return supports, default
		else:
			return [], None

	@classmethod
	def _createAppend(self, data, key, values):
		if Tools.isArray(key):
			for i in key[:-1]:
				if not i in data: data[i] = {}
				data = data[i]
			key = key[-1]
		if not key in data: data[key] = []
		data[key].append(values)

	@classmethod
	def _createUpdate(self, data, key, value):
		if Tools.isArray(key):
			for i in key[:-1]:
				if not i in data: data[i] = {}
				data = data[i]
			key = key[-1]
		data[key] = value

	@classmethod
	def _createSummary(self, data, summary, value = None, count = False, total = True, mean = True, minimum = True, maximum = True, values = True, sort = False, unique = False, empty = False):
		result = {}

		# Treat differently for show and season summaries.
		# Show summaries should not include any specials for ValueTotal.
		# Season summaries should include non-S01 specials for ValueTotal.
		if summary == MetaPack.ValueTotal or not summary:
			if len(data) == len([i for i in data if self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason) == 0]):
				data = [i for i in data if self._extractType(i, MetaPack.NumberStandard) or self._extractType(i, MetaPack.NumberSpecial)]
			else:
				data = [i for i in data if self._extractType(i, MetaPack.NumberStandard) or (self._extractType(i, MetaPack.NumberSpecial) and not self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason) == 0)]
		elif summary == MetaPack.NumberOfficial:
			data = [i for i in data if self._extractType(i, MetaPack.NumberOfficial) and not self._extractType(i, MetaPack.NumberSpecial)]
		elif summary == MetaPack.NumberUnofficial:
			data = [i for i in data if self._extractType(i, MetaPack.NumberUnofficial) and not self._extractType(i, MetaPack.NumberSpecial)]
		elif summary == MetaPack.NumberUniversal:
			data = [i for i in data if self._extractType(i, MetaPack.NumberUniversal) and not self._extractType(i, MetaPack.NumberSpecial)]
		elif summary == MetaPack.NumberStandard:
			data = [i for i in data if self._extractType(i, MetaPack.NumberStandard) and not self._extractType(i, MetaPack.NumberSpecial)]
		elif summary == MetaPack.NumberSequential:
			data = [i for i in data if self._extractType(i, MetaPack.NumberSequential) and not self._extractType(i, MetaPack.NumberSpecial)]
		elif summary == MetaPack.NumberAbsolute:
			data = [i for i in data if self._extractType(i, MetaPack.NumberAbsolute) and not self._extractType(i, MetaPack.NumberSpecial)]
		elif summary == MetaPack.NumberSpecial:
			data = [i for i in data if self._extractType(i, MetaPack.NumberSpecial)]

		data = [i.get(value) for i in data]
		if not empty: data = [i for i in data if i]

		count_ = len(data)
		total_ = sum(data)

		if count: result[MetaPack.ValueCount] = count_
		if total: result[MetaPack.ValueTotal] = total_
		if mean: result[MetaPack.ValueMean] = int(total_ / float(count_)) if count_ else None
		if minimum: result[MetaPack.ValueMinimum] = min(data) if data else None
		if maximum: result[MetaPack.ValueMaximum] = max(data) if data else None
		if values:
			if sort: data = Tools.listSort(data)
			if unique: data = Tools.listUnique(data)
			result[MetaPack.ValueValues] = data

		return result

	@classmethod
	def _createSummaries(self, data, value, count = False, total = True, mean = True, minimum = True, maximum = True, values = True, sort = False, unique = False, empty = False):
		result = {}

		for i in [MetaPack.ValueTotal, MetaPack.NumberOfficial, MetaPack.NumberUnofficial, MetaPack.NumberUniversal, MetaPack.NumberStandard, MetaPack.NumberSequential, MetaPack.NumberAbsolute, MetaPack.NumberSpecial]:
			sub = self._createSummary(summary = i, data = data, value = value, count = count, total = total, mean = mean, minimum = minimum, maximum = maximum, values = values, sort = sort, unique = unique, empty = empty)
			if sub and (sub.get(MetaPack.ValueCount) or sub.get(MetaPack.ValueTotal) or sub.get(MetaPack.NumberSpecial) or sub.get(MetaPack.ValueValues)):
				if i == MetaPack.ValueTotal: result.update(sub)
				else: result[i] = sub

		return result

	@classmethod
	def _createCount(self, data):
		result = {
			MetaPack.ValueTotal : 0,
			MetaPack.NumberOfficial : 0,
			MetaPack.NumberUnofficial : 0,
			MetaPack.NumberUniversal : 0,
			MetaPack.NumberStandard : 0,
			MetaPack.NumberSequential : 0,
			MetaPack.NumberAbsolute : 0,
			MetaPack.NumberSpecial : 0,
		}

		if data:
			for i in data:
				result[MetaPack.ValueTotal] += 1
				for j in self._extractType(i).keys():
					# Do not count unofficial episodes.
					if j == MetaPack.NumberSequential and not(self._extractType(i, MetaPack.NumberOfficial) or self._extractType(i, MetaPack.NumberAutomatic)): continue

					try: result[j] += 1
					except: pass # ValueAutomatic

		return result

	@classmethod
	def _createCounts(self, data):
		result = {
			MetaPack.ValueSeason : {
				MetaPack.ValueTotal : 0,
				MetaPack.NumberOfficial : 0,
				MetaPack.NumberUnofficial : 0,
				MetaPack.NumberUniversal : 0,
				MetaPack.NumberStandard : 0,
				MetaPack.NumberSequential : 0,
				MetaPack.NumberAbsolute : 0,
				MetaPack.NumberSpecial : 0,
			},
			MetaPack.ValueEpisode : {
				MetaPack.ValueTotal : 0,
				MetaPack.NumberOfficial : 0,
				MetaPack.NumberUnofficial : 0,
				MetaPack.NumberUniversal : 0,
				MetaPack.NumberStandard : 0,
				MetaPack.NumberSequential : 0,
				MetaPack.NumberAbsolute : 0,
				MetaPack.NumberSpecial : 0,
			},
			MetaPack.ValueMean : {
				MetaPack.ValueTotal : 0,
				MetaPack.NumberOfficial : 0,
				MetaPack.NumberUnofficial : 0,
				MetaPack.NumberUniversal : 0,
				MetaPack.NumberStandard : 0,
				MetaPack.NumberSequential : 0,
				MetaPack.NumberAbsolute : 0,
				MetaPack.NumberSpecial : 0,
			},
		}

		for i in data:
			result[MetaPack.ValueSeason][MetaPack.ValueTotal] += 1

			for k in self._extractType(i).keys():
				try: result[MetaPack.ValueSeason][k] += 1
				except: pass # ValueAutomatic

			for j in self._extractEpisodes(i):
				if not self._extractType(j, MetaPack.NumberAutomatic): result[MetaPack.ValueEpisode][MetaPack.ValueTotal] += 1

				for k in self._extractType(j).keys():
					if k == MetaPack.NumberSequential or k == MetaPack.NumberAbsolute: continue # More accurate calculation below.
					if (k == MetaPack.NumberUniversal or k == MetaPack.NumberStandard) and self._extractType(j, MetaPack.NumberSpecial): continue # Do not count specials for these.

					if not(k == MetaPack.NumberOfficial or k == MetaPack.NumberUnofficial) or self._extractNumber(j, MetaPack.NumberStandard, part = MetaPack.PartSeason) > 0:
						try: result[MetaPack.ValueEpisode][k] += 1
						except: pass # ValueAutomatic

				if self._extractType(j, MetaPack.NumberOfficial):
					for k in [MetaPack.NumberSequential, MetaPack.NumberAbsolute]:
						if self._extractNumber(j, k, part = MetaPack.PartEpisode): result[MetaPack.ValueEpisode][k] += 1

		for i in result[MetaPack.ValueMean].keys():
			try: result[MetaPack.ValueMean][i] = int(Math.round(result[MetaPack.ValueEpisode][i] / float(result[MetaPack.ValueSeason][i] or 1)))
			except: pass # ValueAutomatic

		return result

	##############################################################################
	# GENERATE
	##############################################################################

	def generateMovie(self, title = None, movies = None):
		try:
			if movies:
				from lib.meta.tools import MetaTools

				# First sort by year and then by time, in case the exact release date is not known.
				movies = Tools.listSort(movies, key = lambda i : (i.get('year', 0), i.get('time', 0)))

				number = 0
				current = Time.timestamp()
				for movie in movies:
					if not movie.get('duration'): movie['duration'] = None # Remove '0' durations.

					status = movie.get('status')
					if status: status = movie['status'] = MetaTools.statusExtract(status)

					if status == MetaTools.StatusReleased: movie['released'] = True
					else:
						time = movie.get('time')
						if time: movie['released'] = time <= current
						else: movie['released'] = False

					number += 1
					movie['number'] = number

				# Exclude future movies, since the pack is used in Stream for various functions, and future movies cannot be in a file collection/pack.
				futures = [i for i in movies if not i.get('released')]
				movies = [i for i in movies if i.get('released')]
				count = len(movies)

				years = []
				times = []
				durations = []

				for movie in movies:
					year = movie.get('year')
					if year: years.append(year)
					time = movie.get('time')
					if time: times.append(time)
					duration = movie.get('duration')
					if duration: durations.append(duration)

				status = MetaTools.StatusReleased
				if len(futures) > 0:
					status = MetaTools.StatusPlanned
					for i in reversed(futures):
						i = i.get('status')
						if i:
							if i == MetaTools.StatusRumored: continue
							status = i
							break

				yearMinimum = None
				yearMaximum = None
				if years:
					years = Tools.listSort(Tools.listUnique(years))
					yearMinimum = min(years)
					yearMaximum = max(years)

				timeMinimum = None
				timeMaximum = None
				if times:
					times = Tools.listSort(Tools.listUnique(times))
					timeMinimum = min(times)
					timeMaximum = max(times)

				durationCount = None
				durationTotal = None
				durationMean = None
				durationMinimum = None
				durationMaximum = None
				if durations:
					durationCount = len(durations)
					durationTotal = sum(durations)
					durationMean = int(durationTotal / float(durationCount))
					durationMinimum = min(durations)
					durationMaximum = max(durations)
					if durationCount < count: durationTotal += durationMean * (count - durationCount) # Missing duration, use mean duration of other movies.

				if not title: title = []
				elif not Tools.isArray(title): title = [title]

				return self._initialize(pack = {
					'media'						: Media.Movie,
					'title'						: title,
					'count'						: count,
					'status'					: status,
					'year'						: {
						MetaPack.ValueMinimum	: yearMinimum,
						MetaPack.ValueMaximum	: yearMaximum,
						MetaPack.ValueValues	: years,
					},
					'time'						: {
						MetaPack.ValueMinimum	: timeMinimum,
						MetaPack.ValueMaximum	: timeMaximum,
						MetaPack.ValueValues	: times,
					},
					'duration'					: {
						MetaPack.ValueTotal	: durationTotal,
						MetaPack.ValueMean	: durationMean,
						MetaPack.ValueMinimum	: durationMinimum,
						MetaPack.ValueMaximum	: durationMaximum,
					},
					'movies'					: movies + futures,
				})
		except: Logger.error()
		return None

	'''

		SEASON SUMMARY:
			The summary for year/time/duration/count has the following structure.
			Summaries without any values are removed to reduce the data size.
				{
					// All standard episodes and specials (that are placed within a standard season, excluding S0 specials).
					// Or for S0 itself, all specials within S0.
					"total": <summed-value>,
					"mean": <averaged-value>,
					"minimum": <min-value>,
					"maximum": <max-value>,
					"values": [<all-values>],

					// All standard episodes in the season, excluding any specials.
					"standard": {
						"total": <summed-value>,
						"mean": <averaged-value>,
						"minimum": <min-value>,
						"maximum": <max-value>,
						"values": [<all-values>],
					},

					// All absolute, and therefore also standard, episodes in the season, excluding any specials.
					"absolute": {
						"total": <summed-value>,
						"mean": <averaged-value>,
						"minimum": <min-value>,
						"maximum": <max-value>,
						"values": [<all-values>],
					},

					// All special episodes in the season.
					"special": {
						"total": <summed-value>,
						"mean": <averaged-value>,
						"minimum": <min-value>,
						"maximum": <max-value>,
						"values": [<all-values>],
					},
        		}
	'''
	def generateShow(self, trakt = None, tvdb = None, tmdb = None, imdb = None):
		try:
			# Some examples to test with:
			#
			#	Dragon Ball Super
			#		IMDb/TMDb/Trakt use absolute numbering, TVDb use season numbering.
			#			IMDb: 1 season, 131 episodes, 0 specials, 0 unassigned. Default absolute numbering. Year numbering available.
			#				https://imdb.com/title/tt4644488/episodes/?season=1
			#			TMDb: 1 season, 131 episodes, 0 specials, 0 unassigned. Default absolute numbering. Various alternative numberings available.
			#				https://themoviedb.org/tv/62715-dragon-ball-chou/episode_groups?language=en-US
			#			TVDb: 5 seasons, 131 episodes, 2 specials, 3 unassigned. Default season numbering. Alternative absolute numbering available.
			#				https://thetvdb.com/series/dragon-ball-super#seasons
			#			Trakt: 1 season, 131 episodes, 0 specials, 0 unassigned. Default absolute numbering.
			#				https://trakt.tv/shows/dragon-ball-super/seasons/1
			#
			#	Downton Abbey
			#		IMDb has the Christmas specials, that are part of the story-line, listed at the end of each season. TMDb/TVDb/Trakt have them as specials.
			#			IMDb: 6 seasons, 52 episodes, 0 specials, 0 unassigned. Default season numbering. Year numbering available.
			#				https://imdb.com/title/tt1606375/episodes/
			#			TMDb: 6 seasons, 47 episodes, 12 specials, 0 unassigned. Default season numbering. Various alternative numberings available.
			#				https://themoviedb.org/tv/33907-downton-abbey/seasons?language=en-US
			#			TVDb: 6 seasons, 47 episodes, 19 specials, 0 unassigned. Default season numbering. Alternative absolute numbering available.
			#				https://thetvdb.com/series/downton-abbey#seasons
			#			Trakt: 6 seasons, 47 episodes, 12 specials, 0 unassigned. Default season numbering.
			#				https://trakt.tv/shows/downton-abbey
			#
			#	Game of Thrones
			#		TVDb has fewer specials than Trakt/TMDb. S00E56 and S00E57 differs between TVDb and Trakt/TMDb. Trakt has 4 more specials than TMDb, although they end in the same number S00E294.
			#		Trakt/TMDb has some special numbers missing (S00E07 and S00E08). TVDb has these numbers, but it contains specials that are elwshere in Trakt/TMDb (S00E210 and S00E211).
			#			IMDb: 8 seasons, 73 episodes, 0 specials, 0 unassigned. Default season numbering. Year numbering available.
			#				https://imdb.com/title/tt0944947/episodes/
			#			TMDb: 8 seasons, 73 episodes, 282 specials, 0 unassigned. Default season numbering. Various alternative numberings available.
			#				https://themoviedb.org/tv/1399-game-of-thrones/seasons?language=en-US
			#			TVDb: 8 seasons, 73 episodes, 55 specials, 0 unassigned. Default season numbering. Alternative absolute numbering available.
			#				https://thetvdb.com/series/game-of-thrones#seasons
			#			Trakt: 8 seasons, 73 episodes, 286 specials, 0 unassigned. Default season numbering.
			#				https://trakt.tv/shows/game-of-thrones
			#
			#	One Piece (Anime)
			#		Trakt/TMDb devides the show into seasons, but within seasons, episodes have absolute numbering.
			#		The seasons between TVDb and Trakt/TMDb are very different, split at different places. Eg: The last 3 episodes in S21 and the first 3 episodes in S22.
			#			https://thetvdb.com/series/one-piece#seasons
			#			https://trakt.tv/shows/one-piece
			#			https://themoviedb.org/tv/37854?language=en-US
			#
			#	House
			#		The absolute order on TVDb is a complete mess. The standard first episode is listed as S01E02, since a 4 min unaired pilot in the specials (S00E01) is considered the absolute S01E01.
			#		However, TVDb does not list that unaired pilot as part of the absolute season, since it is listed under "Unassigned Episodes".
			#		Trakt/TMDb do not have alternative seasons for this show. However, Trakt does have the "absolute" attribute in episodes, which also starts from "2", not from "1".
			#		While the unaired pilot in the specials season has an "absolute" number of "0", like all specials on Trakt. So we cannot even manually add episode "1" to the absolute season, since there is nothing that indicates its position.
			#		TVDb also has a huge gap between S01E111 and S01E133, with the standard S06 added to the end of the absolute season, although their air dates are earlier than those of episodes places before them.
			#		Not sure if this is simply a mistake on TVDb, or if there is a reason for this. Maybe S06 was so bad that people decided to place it last to not create a bad taste for the viewer.
			#		But the absolute season on TVDb has so many issues that it can simply not be used as a reliable order.
			#		For instance, if we scrape S01E02 or play a video from a season pack, it will definitely return the standard E02, and not the standard E01 (which is preceded by the 4min unaired pilot).
			#		Trakt/TMDb also has 2 episodes for S06E21, although both have the same metadata and duration. TVDb's duration is also 45 mins, so this does not seem like a double-episode?
			#		TVDb has split S06E01 into 2 episodes, while Trakt/TMDb have a single episode.
			#		Trakt also does not have absolute numbers for S06 (all are "0").
			#		Trakt has and absolute number of "197" for S06E21, while TVDb has "192" for that episode. But Trakt's second "Help Me" episode S06E22 has absolute number "192."
			#			https://imdb.com/title/tt0412142
			#			https://thetvdb.com/series/house#seasons
			#			https://themoviedb.org/tv/1408-house/seasons?language=en-US
			#			https://trakt.tv/shows/house
			#
			#	Days of our Lives
			#		Test this to see how long it takes to generate packs for very large shows.
			#		This show also has a bunch of seasons missing.
			#			https://imdb.com/title/tt0058796/
			#			https://themoviedb.org/tv/881-days-of-our-lives/seasons?language=en-US
			#			https://trakt.tv/shows/days-of-our-lives
			#			https://thetvdb.com/series/days-of-our-lives#seasons
			#
			#	Rick and Morty
			#		Very different specials and special ordering between TVDb and Trakt/TMDb.
			#			https://imdb.com/title/tt2861424/
			#			https://themoviedb.org/tv/60625-rick-and-morty?language=en-US
			#			https://trakt.tv/shows/rick-and-morty/
			#			https://thetvdb.com/series/rick-and-morty#seasons
			#
			######################################################################################################################################################################
			#
			#	#gaiafuture
			#		These have weird seasons and ordering, and currently do not work perfectly.
			#		Properly supporting them might be too much effort and/or add too much extra complexity.
			#		Leave for now. Implement in the future, especially the Anime stuff.
			#
			#	Star Wars: Young Jedi Adventures
			#		IMDb/TMDb/Trakt have 2 episodes combined into one, TVDb has the short episodes individually/uncombined.
			#		IMDB has extra episodes in season 1, which are specials on TMDb/TVDb/Trakt
			#			IMDb: 2 seasons, 42 episodes, 0 specials, 6 unassigned. Default season numbering. Year numbering available.
			#				https://imdb.com/title/tt4644488/episodes/?season=1
			#			TMDb: 2 seasons, 36 episodes, 12 specials, 0 unassigned. Default season numbering. Various alternative numberings available.
			#				https://themoviedb.org/tv/202998-star-wars-young-jedi-adventures/seasons?language=en-US
			#			TVDb: 2 seasons, 72 episodes, 12 specials, 54 unassigned. Default season numbering. Alternative absolute and combined numbering available.
			#				https://thetvdb.com/series/star-wars-young-jedi-adventures#seasons
			#			Trakt: 2 seasons, 36 episodes, 12 specials, 0 unassigned. Default season numbering.
			#				https://trakt.tv/shows/star-wars-young-jedi-adventures
			#
			#	One Piece
			#		Although TVDb and Trakt/TMDb have the same number of seasons, almost every season has a different episode count between the various providers.
			#		To make things even worse, although Trakt has seasons, each season does not start at episode 1. Eg: the first S02 episode is S02E62, basically continuing the episode numbering after S01.
			#		This show is a complete mess.
			#			https://thetvdb.com/series/one-piece#seasons
			#			https://trakt.tv/shows/one-piece
			#
			#	Hunter x Hunter
			#		Also check this show (the 2011 version, not 1999). Same number of seasons on Trakt/TVdb, but slight differences.
			#			https://trakt.tv/shows/hunter-x-hunter-2011
			#			https://thetvdb.com/series/hunter-x-hunter-2011#seasons
			#		Some torrents use the Trakt numbering, while others use the TVDb numbering:
			#			https://solidtorrents.to/torrents/hunter-x-hunter-s03-1080p-blu-ray-10-bit-dual-audi-c4444/602f92bb08d17ad804a7ebd0/
			#			https://solidtorrents.to/torrents/hunter-x-hunter-s03-1080p-blu-ray-10-bit-dual-audi-2b06c/66004c207a868426ce37e86e/
			#			https://solidtorrents.to/torrents/hunter-x-hunter-2011-s03-1080p-nf-web-dl-aac2-0-h--6c8eb/651a8a9f3eaa2eefeb809a45/
			#		We have to accomodate the weird Trakt numbers (eg: Trakt S03E137 vs TVDb S03E01). We still have to mark stuff on Trakt with this numbering, but we should somehow make it use S03E01 for Gaia+menus.
			#		Also update Core._scrapeNumber() to possibly list more than 2 numberings to choose from. Eg S01E137, S03E137, S03E01.
			#

			'''
				#gaiafuture

				This function currently does not support combined vs uncombined episode numbering (two or more episodes combined into one).
					Eg: "Star Wars: Young Jedi Adventures" on TVDb has a default uncombined order, whereas on Trakt/TMDb it uses the combined order.
				Supporting this would require too much time and additional complexity that does not seem to justify adding it.
				Plus this is probably limited to mostly children's shows which often have very short episodes.
				If this is ever supported, do the following:
					1. Change the "pack" assembly in this function to allow mutiple entries in the lookup table per episode. Eg: looking up S02E01 returns a list for "tvdb" that contains 2 entries for TVDb's shorter episodes (S02E01 and S02E02).
					2. Update MetaManager._metadataEpisodeUpdate() to correctly combine the dicts from the different providers, based on the new lookup from this function. Instead of combining the dicts purely based on a fixed episode number (that does not match between Trakt's combined order vs TVDb's uncombined order), do a lookup first to see if it might map to mutiple combined episodes. Then only use a subset of the metadata to update the dicts (eg: just add the additional ratings/votings to the updated dict, but not the title, since there are combined/uncombined titles)
					3. Change Playback to mark mutiple episodes as watched/rated on Trakt, if the combined order requires it. Or avoid duplicate watched markings for uncombined episodes.
					4. Update the season and episode menus to show the correct ones, preferably the uncombined order.C heck that the menus show the correct watched status checkmark, etc, if the order differs on Trakt vs TVDb.
					5. How does this work for provider scraping that use IDs (eg: Orion)?
					6. NB: TVDb uses different episode IDs for combined order. The standard and absolute seasons use the same episodes and therefore have the same metada and IDs. But TVDb's combined seasons have completely separate episodes, with separate IDs and metadata. I think that Trakt has the episode IDs of the combined TVDb episodes, not the standard/absolute IDs.
					7. Select the correct file from the torrent pack during playback.
					8. Or a hacky solution might be to ignore TVDb's order and use combined orders if available. This would make #3, #4, #6, #7 a lot easier. Not sure what the torrents use? If they also use the combined order, this could be the way.
			'''

			if not tvdb and not trakt and not tmdb and not imdb: return None

			from lib.meta.tools import MetaTools

			timer = Time(start = True)

			base = [(MetaPack.ProviderTvdb, tvdb), (MetaPack.ProviderTrakt, trakt), (MetaPack.ProviderTmdb, tmdb), (MetaPack.ProviderImdb, imdb)] # Order according to which data to prefer.
			providersAll = [i[0] for i in base]
			base = [i for i in base if i[1] and 'seasons' in i[1]] # Check seasons, to exclude IMDb basic data with only an ID.
			data = [i[1] for i in base]
			providers = [i[0] for i in base]
			providerCount = len([i for i in base if i[1]]) # Only count those that have data (aka IMDb should be excluded).

			language = self._extractList(data, 'language', [])
			setting = MetaTools.instance().settingsLanguage()
			current = Time.timestamp()

			sequential = None
			discrepancies = {}
			specialDiscrepancy = False # Different providers have a different number of specials, excluding providers without any specials.

			seasonCount = {} # The total number of standard seasons, excluding the special season.
			episodeCount = {} # The total number of sequential episodes in the show, excluding specials.
			showCount = {}

			seasonTree = {}
			episodeTree = {}
			episodeList = [] # Linear list of references for quicker iterations. Holds references to episodeTree.
			episodeUnknown = {}
			episodeUnmatched = {}
			episodeId = {i : {} for i in providersAll}
			episodeTitle = {}

			################################################################################################################
			# STEP 1 - Calculate the show, season, and episode counts.
			################################################################################################################

			# Calculate the show/season/episode counts.
			# Note that sometimes seasons are missing, so do not just count upwards.
			for provider, item in base:
				countSeason = 0
				countEpisode = 0
				showCount[provider] = {}

				for season in self._extractSeasons(item):
					if season:
						numberSeason = self._extractNumber(season, MetaPack.NumberStandard)

						episodes = self._extractEpisodes(season)
						episodes = len(episodes) if episodes else 0

						if not numberSeason == 0:
							if numberSeason > countSeason: countSeason = numberSeason
							countEpisode += episodes
						showCount[provider][numberSeason] = episodes

				seasonCount[provider] = countSeason
				episodeCount[provider] = countEpisode

			# Determine if there is a discrepancy between the number of specials between providers.
			specials = [showCount.get(i).get(0) for i in providers]
			specialDiscrepancy = len(set([i for i in specials if i])) > 1

			# Fill in seasons that are not available on a provider.
			# Eg: Days of our Lives.
			for provider in providers:
				for i in range(1, seasonCount[provider] + 1):
					if not i in showCount[provider]: showCount[provider][i] = 0

			# Determine if the show is sequential numbered on some providers and not on others.
			seasonSingle = []
			seasonMulti = []
			for provider, count in seasonCount.items():
				if count == 1: seasonSingle.append(provider)
				elif count > 1: seasonMulti.append(provider)
			if seasonSingle and seasonMulti:
				for i in seasonSingle:
					count1 = self._extract(showCount, [i, 1])
					for j in seasonMulti:
						count2 = self._extract(showCount, [j, 1])
						if count1 > (count2 + 3):
							sequential = True
							break
					if sequential: break

			################################################################################################################
			# STEP 2 - Determine the best provider to use per season.
			################################################################################################################

			# Determine the preferred provider to use for specific seasons.
			# Prefer the provider with most episodes in the show.
			#	Eg: GoT S00 - Trakt/TMDb has a lot more episodes than TVDb - And S00E56/S00E57 are mistmatched.
			#	Eg: Star Wars: Young Jedi Adventures - TVDb has twice as many uncombined episodes than Trakt/TMDb which uses combined episodes.
			# Always prefer Trakt order to ensure consistency and make it easier to sync playback/ratings.
			# Some shows are very different between Trakt/TMDb and TVDb, so sticking to a single provider is best.
			#	Eg: One Piece (Anime)
			supports = {}
			supportsOrder1 = {MetaPack.ProviderTrakt : 40000, MetaPack.ProviderTvdb : 30000, MetaPack.ProviderTmdb : 20000, MetaPack.ProviderImdb : 10000} # Prefer Trakt over TVDB over TMDb over IMDb if the counts are the same.
			supportsOrder2 = {MetaPack.ProviderTrakt : 0.4, MetaPack.ProviderTvdb : 0.3, MetaPack.ProviderTmdb : 0.2, MetaPack.ProviderImdb : 0.1} # Prefer Trakt over TVDB over TMDb over IMDb if the counts are the same.
			for numberSeason in range(max(seasonCount.values()) + 1):
				# Prefer Trakt for normal seasons, but use the provider with most episodes for S0.
				# Eg: Downton Abbey: TVDb has more specials than Trakt.
				supportsOrder = supportsOrder2 if numberSeason == 0 else supportsOrder1

				values = Tools.listSort([[i, self._extract(showCount, [i, numberSeason], 0) + self._extract(supportsOrder, i)] for i in providers], key = lambda i : i[1], reverse = True)

				# If only a few extra episodes are available on one provider, ignore them and stick to the original preference (TVDb, Trakt, TMDb).
				# This could be just a special at the end of the season, or a provider has added a few unaired episodes that the others have not added yet.
				# Do not do this for S00, even if there are only 1 or 2 episodes extra, since just a single episode out of place can change the episode numbering in S00. Always prefer the one with more specials.
				if numberSeason > 0:
					value = Tools.listSort([i[1] for i in values if i[1]])
					if value:
						threshold = 4 # Allow for up to 3 episodes extra. Accomodate the decimal fraction.
						maximum = int(value[-1])
						for i in values:
							if i[1] and abs(maximum - i[1]) < threshold: i[1] = maximum + self._extract(supportsOrder, i[0])

				values = [i[0] for i in values]

				# For specials, always move TMDb after Trakt.
				# Important for specials where Trakt does not have the TMDb IDs and the titles of the specials between Trakt and TVDb do not match.
				# Eg: Babylon Berlin S00E06 - "The first trailer for the new season" (Trakt) vs "Episode 6" (TMDb) - "Episode 6" gets removed in the next step because it is too generic, but even with it, it would not match the title on Trakt.
				if numberSeason == 0:
					try: indexTrakt = values.index(MetaPack.ProviderTrakt)
					except: indexTrakt = -1
					try: indexTmdb = values.index(MetaPack.ProviderTmdb)
					except: indexTmdb = -1
					if indexTrakt >= 0 and indexTmdb >= 0 and indexTmdb < indexTrakt:
						values.pop(indexTmdb)
						values.insert(values.index(MetaPack.ProviderTrakt) + 1, MetaPack.ProviderTmdb)

				supports[numberSeason] = values

			################################################################################################################
			# STEP 3 - Combine the metadata from different providers for episodes with the same number matching IDs/titles.
			################################################################################################################

			# Firstly, create an list for each episode, containing the episode metadata from each provider, in the order of the provider preference.
			# Secondly, combine the list of episode metadatas into a single item.
			# NB: Do not just interate over the providers and update the dict in every iteration. Otherwise the last provider (eg IMDb) will overwrite the data of more important providers (eg: TVDb).
			for provider, item in base:
				for season in self._extractSeasons(item):
					if season:
						numberSeason = self._extractNumber(season, MetaPack.NumberStandard)

						# Do not add TMDb S00, since there is no extended metadata for them, and S0 can have missing episodes or ordered differently.
						# These values are later interpolated from the Trakt data, since Trakt seems to typically have the TMDb instead of the TVDb episode numbering.
						# Eg: GoT S00.
						# Update: detailed pack metadata is now retrieved from TMDb as weel, so there is no reason for this.
						# Having this enabled, causes TMDb specials to not be included if Trakt does not have the TMDb ID.
						# Eg: Babylon Berlin S00E04+
						#if provider == MetaPack.ProviderTmdb and numberSeason == 0: continue

						if not self._extractNumber(season, MetaPack.NumberSequential): season['number'][MetaPack.NumberSequential] = None
						if not self._extractNumber(season, MetaPack.NumberAbsolute): season['number'][MetaPack.NumberAbsolute] = None

						if numberSeason == 0: season['number'][MetaPack.NumberSequential] = 1
						season['number'][provider] = self._createNumber(data = season, provider = provider)
						if numberSeason == 0: season['number'][provider][MetaPack.NumberSequential] = 1

						if numberSeason == 0: season['number'][MetaPack.NumberAbsolute] = 1
						season['number'][provider] = self._createNumber(data = season, provider = provider)
						if numberSeason == 0: season['number'][provider][MetaPack.NumberAbsolute] = 1

						self._createAppend(data = seasonTree, key = numberSeason, values = season)

						numberPrevious = None
						for episode in self._extractEpisodes(season):
							numberEpisode = self._extractNumber(episode, MetaPack.NumberCustom, part = MetaPack.PartEpisode)
							if numberEpisode is None: numberEpisode = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)

							if numberPrevious is False: # Also do not use any of the subsequent "special" episodes for sequential ordering.
								episode['number'][MetaPack.NumberSequential] = None
								episode['type'] = {MetaPack.NumberSpecial : True}
							else:
								numberSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
								if not numberSequential: episode['number'][MetaPack.NumberSequential] = None
								elif numberPrevious:
									# Sometimes TVDb has weird episodes, probably specials, in their seasons that suddenly have a huge episode number jump.
									# Eg: The Librarians 2014 - S02E10 -> S02E101, S02E102, S02E103.
									# Do not include these in the sequential numbering.
									try:
										numberTemp = numberPrevious.get(MetaPack.NumberSequential)
										if numberTemp and numberTemp[MetaPack.PartEpisode] == numberSequential - 1: # Correct sequential increment from the previous episode.
											numberTemp = numberPrevious.get(MetaPack.NumberStandard)
											if numberTemp and abs(numberTemp[MetaPack.PartEpisode] - self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)) > 20:
												numberPrevious = False
												episode['number'][MetaPack.NumberSequential] = None
												episode['type'] = {MetaPack.NumberSpecial : True}
									except: Logger.error()

							if not self._extractNumber(episode, MetaPack.NumberAbsolute, part = MetaPack.PartEpisode): episode['number'][MetaPack.NumberAbsolute] = None
							episode['number'][provider] = self._createNumber(data = episode, provider = provider)

							if not numberPrevious is False: numberPrevious = self._extractNumber(episode)

							# Do not mark specials with their own internal absolute numbers.
							# An absolute number should indicate the absolute position within the series (S01).
							# And technically specials could be part of the storyline and have their own absolute number to be placed within S01, although this is probably rare or does not happen at all.
							# Also, do not check if the absolute number is None, since Trakt sometimes returns some specials with an absolute number of None and others with a number of 0. Eg: GoT.
							if numberSeason == 0:
								if not self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode): episode['number'][MetaPack.NumberSequential] = [1, 0]
								if not self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode, provider = provider): episode['number'][provider][MetaPack.NumberSequential] = [1, 0]

								if not self._extractNumber(episode, MetaPack.NumberAbsolute, part = MetaPack.PartEpisode): episode['number'][MetaPack.NumberAbsolute] = [1, 0]
								if not self._extractNumber(episode, MetaPack.NumberAbsolute, part = MetaPack.PartEpisode, provider = provider): episode['number'][provider][MetaPack.NumberAbsolute] = [1, 0]

								# Remove generic titles for specials that can clash with the titles from the official seasons.
								# Eg: Babylon Berlin S00E06 and S00E15+ have titles like "Episode 6", which is later incorrectly mapped to S01+ that also have an episode named "Episode 6".
								title = episode.get('title')
								if title: episode['title'] = [i for i in title if not Regex.match(data = i, expression = MetaPack.ExpressionGeneric, cache = True)]

							self._createAppend(data = episodeTree, key = [numberSeason, numberEpisode], values = episode)

			# Do not assemble data from different providers purley on the season/episode number, since the numbering can be different on providers, especially for specials.
			#	Eg: GoT S00E56 (Trakt vs TVDb)
			# Combined/uncombined episodes also have different orders.
			#	Eg: Star Wars: Young Jedi Adventures (Trakt vs TVDb)
			for numberSeason, season in episodeTree.items():
				for numberEpisode, episode in season.items():
					# Determine the best provider for the episode, depending on the season support and whether or not the specific episode is available from the provider.
					# Prefer the providers with ID+number, then ID only, then number only, then the rest.
					# This is mainly for TMDb which does not have detailed episode metadata, but the episodes numbers are created automatically from the season episode count.
					# This might not always be correct, especially for S00, since the episode number and episode count do not always match.
					# Eg: GoT S00E08 is not available on Trakt/TMDb (at least not the specific number S00E08), but Gaia generates a dummy episode object in MetaTmdb.pack(), containing only the episode number S00E08, but not any IDs/titles (except for S01).
					support, default = self._createSupport(data = episode, support = self._extract(supports, numberSeason))

					# Only update the metadata of an episode if we are certain the items in the "episode" list are all for the same episode.
					# An episode is considered valid if either the IDs or the title match. If just the season/episode numbers match, it is not considered valid.
					# If not, do not use those incorrect episodes for the metadata update. These number-only-matches will be filled in later.
					# Eg: GoT S00E56 and S00E08 (TVDb vs Trakt/TMDb).
					if default:
						# First collect all the IDs.
						# Eg: TVDb only has the TVDb ID. TMDb only has the TMDb ID. Trakt typically has all IDs.
						# Iterate over all objects once, to make sure we have all the IDs.
						ids = Tools.copy(self._extractId(default, default = {}))
						for i in episode:
							if not i is default:
								for j in providers:
									id = self._extractId(i, j)
									if id and id == self._extract(ids, j):
										ids = Tools.update(ids, self._extract(i, 'id', {}), none = False)
										break

						temp = [default]
						title = self._extractTitle(default)
						time = self._extract(default, 'time')

						# Add the episode to the unknowns if only one provider has them.
						# Eg: GoT S00E08.
						# Only add them if there is only one ID available. Otherwise this would add too many episodes too the unknowns, which ends up increasing title matching 10 times, slowing down pack creation.
						if len(episode) == 1 and len([i for i in ids.values() if i]) == 1:
							if not numberSeason in episodeUnmatched: episodeUnmatched[numberSeason] = {}
							if not numberEpisode in episodeUnmatched[numberSeason]: episodeUnmatched[numberSeason][numberEpisode] = []
							episodeUnmatched[numberSeason][numberEpisode].append(episode[0])
						else:
							for i in episode:
								if not i is default:
									match = False

									# Match by non-None ID.
									if not match:
										for j in providers:
											id = self._extract(ids, j)
											if id and self._extractId(i, j) == id:
												matched = True

												# Trakt has some incorrect IDs for certain specials.
												# Eg: Downton Abbey S00E12 vs S0013 (Trakt vs TVDb). For S00E12 Trakt has the TVDb ID for the "Downton Abbey" movie which is S00E13 on TVDb.
												# Check if the title matches before considering them a match.
												# Do not only match the title, since some specials are correct, but have different titles.
												# Eg: Downton Abbey S00E08 - "Downton Abbey Text Santa Special" (TVDb) vs "Text Santa 2014" (Trakt).
												# Therefore check the release date first. TVDb and Trakt can have a slight offset in their release date (eg timezone etc). Allow some deviation.
												# Hence, if the release date and the title mismatches, consider them a discrepancy.
												if numberSeason == 0 and time:
													time2 = self._extract(i, 'time')
													if time2 and abs(time - time2) > 604800: # 1 week.
														title2 = self._extractTitle(i)
														if title2 and self.match(data = title2, title = title, combined = True, quick = True, detail = True).get('match') < 0.5:
															self._createUpdate(data = discrepancies, key = [numberSeason, numberEpisode], value = True)
															matched = False
												match = matched
												break

									# Match by non-None title.
									if not match and title:
										title2 = self._extractTitle(i)
										if title2 and self.match(data = title2, title = title, combined = True, quick = True):
											match = True

									# Add if either ID or title matched.
									if match:
										temp.append(i)
									else:
										if not numberSeason in episodeUnknown: episodeUnknown[numberSeason] = {}
										if not numberEpisode in episodeUnknown[numberSeason]: episodeUnknown[numberSeason][numberEpisode] = []
										episodeUnknown[numberSeason][numberEpisode].append(i)
						episode = temp

					item = {
						'id'		: {
							'imdb'	: self._extractSelect(data = episode, key = ['id', 'imdb']),
							'tmdb'	: self._extractSelect(data = episode, key = ['id', 'tmdb']),
							'tvdb'	: self._extractSelect(data = episode, key = ['id', 'tvdb']),
							'trakt'	: self._extractSelect(data = episode, key = ['id', 'trakt']),
						},
						'number'	: self._createNumber(data = episode),
						'support'	: support,
						'type'		: {},

						'status'	: self._extractSelect(data = episode, key = 'status'),
						'title'		: self._createTitle(data = episode, language = language, setting = setting),

						'year'		: self._extractSelect(data = episode, key = 'year'),
						'time'		: self._extractSelect(data = episode, key = 'time'),

						# Do not use _extractMaximum(), since some episodes have a 1 minute runtime difference between Trakt and TVDb.
						# We want to use the duration from the preferred provider.
						# Eg: Westworld S02E03.
						'duration'	: self._extractDuration(data = episode, key = 'duration'),
					}

					season[numberEpisode] = item
					episodeList.append(item)

			################################################################################################################
			# STEP 4 - Combine the metadata for "unknown" episodes that do not have a matching number, ID, or title.
			################################################################################################################

			# Combine all the "unknown" episodes by season/episode number.
			# These are episodes without an ID or title.
			# These are later used as last resort.
			# Eg: TMDb S0 and S2+ does not have extended metadata.
			for numberSeason, season in episodeUnknown.items():
				for numberEpisode, episode in season.items():
					support, default = self._createSupport(data = episode, support = self._extract(supports, numberSeason))
					episodeUnknown[numberSeason][numberEpisode] = {
						'id'		: {
							'imdb'	: self._extractSelect(data = episode, key = ['id', 'imdb']),
							'tmdb'	: self._extractSelect(data = episode, key = ['id', 'tmdb']),
							'tvdb'	: self._extractSelect(data = episode, key = ['id', 'tvdb']),
							'trakt'	: self._extractSelect(data = episode, key = ['id', 'trakt']),
						},
						'number'	: self._createNumber(data = episode),
						'support'	: support,
						'type'		: {},

						'status'	: self._extractSelect(data = episode, key = 'status'),
						'title'		: self._createTitle(data = episode, language = language, setting = setting),

						'year'		: self._extractSelect(data = episode, key = 'year'),
						'time'		: self._extractSelect(data = episode, key = 'time'),
						'duration'	: self._extractDuration(data = episode, key = 'duration'),
					}

			# Create a lookup by episode IDs.
			# Make things easier if there is a huge number mismatch between seasons.
			# Eg: One Piece S01E09 (Trakt) vs S02E01 (TVDb).
			# Add lookups for episodes that exist on TVDB, but not on Trakt, and we want to add the Trakt number to it.
			# Eg: One Piece S02E17 (TVDb) vs S01E25 (Trakt)
			# Also improves pack generation speed, since we have to do less title matching, since many of the unfound episodes can be quickly looked up using the lookup tables.
			for structure in [episodeTree, episodeUnmatched, episodeUnknown]: # Place episodeTree before episodeUnmatched/episodeUnknown, since they typically contain more detailed metadata (eg: episodeTree with Trakt data cotnaining mutiple IDs vs episodeUnmatched/episodeUnknown with only TVDb ID).
				for numberSeason, season in structure.items():
					for numberEpisode, episode in season.items():
						for i in episode if Tools.isArray(episode) else [episode]:
							for j in providers:
								id = self._extractId(i, j)
								if id:
									if not id in episodeId[j]: episodeId[j][id] = []
									if not i in episodeId[j][id]: episodeId[j][id].append(i)
							title = self._extractTitle(i)
							if title:
								for j in title:
									# Do not add common titles like "Episode 1".
									if j and not Regex.match(data = j, expression = MetaPack.ExpressionGeneric, cache = True):
										if not j in episodeTitle: episodeTitle[j] = []
										if not i in episodeTitle[j]: episodeTitle[j].append(i)

			################################################################################################################
			# STEP 5 - Add automatic absolute episodes if they do not already exist.
			################################################################################################################

			# Add automatic dummy absolute episodes if they do not already exist.
			# These technically non-existing episodes will not have their metadata added to the pack, since it it just a reference to another episode.
			# The lookup table is created from this to allow for quicker conversion from one episode number to another one.
			seasonFirst = self._extract(episodeTree, 1)
			if seasonFirst:
				# Do not use the max count, instead use the Trakt count.
				# Since TVDb can have more episodes, such as with combined episodes, which then screw up the sequential number generation later on.
				# Eg: Star Wars: Young Jedi Adventures
				#for i in range(1, max(episodeCount.values()) + 1):
				count = episodeCount.get(MetaPack.ProviderTrakt) or episodeCount.get(MetaPack.ProviderTvdb) or max(episodeCount.values())
				for i in range(1, count + 1):
					if not i in seasonFirst:
						item = {
							'type'		: {MetaPack.NumberAutomatic : True},
							'number'	: {MetaPack.NumberSequential : [1, i]},
						}
						seasonFirst[i] = item
						episodeList.append(item)

			################################################################################################################
			# STEP 6 - Combine the metadata for episodes across different seasons, based on their IDs and titles.
			################################################################################################################

			# Fill in missing IDs and numbers from other episodes belonging in other seasons (eg: Downton Abbey - S02E09 on IMDb - S00E02 on Trakt).
			episodeSpecial = []
			episodeFirst = []
			episodeLater = []
			for i in episodeList:
				number = self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason, default = -1)
				if number == 0: episodeSpecial.append(i)
				elif number == 1: episodeFirst.append(i)
				elif number > 1: episodeLater.append(i)

			for provider, item in base:
				for episode in episodeList:
					# Only pick other episodes that are in the same season or S00.
					numberSeason = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason)
					numberEpisode = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
					if numberSeason is None or numberEpisode is None: continue # Eg: One Piece where there is a huge inconsistency in seasons and numbering between Trakt and TVDb.

					numberSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
					numberProvider = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = provider)
					discrepancy = self._extract(discrepancies, [numberSeason, numberEpisode])
					title = self._extractTitle(episode)

					id = self._extractId(episode)
					if id:
						checkImdb = self._extract(id, MetaPack.ProviderImdb)
						checkTmdb = self._extract(id, MetaPack.ProviderTmdb)
						checkTvdb = self._extract(id, MetaPack.ProviderTvdb)
						checkTrakt = self._extract(id, MetaPack.ProviderTrakt)
						id = self._extract(id, provider)
					else: # Automatic sequential episodes.
						checkImdb = None
						checkTmdb = None
						checkTvdb = None
						checkTrakt = None

					# Data is missing.
					# Also check if there is no Trakt ID. Eg: One Piece S02E17 (TVDb).
					if not id or numberProvider is None or not checkTrakt:
						unknown = episodeUnknown.get(numberSeason) # Eg: Downton Abbey S00E12 vs S00E13 (TVDb vs Trakt).
						unmatched = episodeUnmatched.get(numberSeason) # Eg: GoT S00E08

						# Do not fill the data if an episode does not even exist on the current provider.
						# Otherwise we have to do a lot of unnecessary title matching for episodes that technically are not on available from the provider.
						contains = False
						if sequential: contains = True # Assume the episode is contained for shows with where some providers use sequential numbering while others use season numbering.
						elif discrepancy: contains = True # Some specials have discrepancies between their IDs and numbers.
						elif title and numberSeason == 0: # Do not do this only for "numberSeason == 0", due to The Office (India) S00E01 vs S01E01. And Star Wars: Young Jedi Adventures S01 (extra uncombined TVDb episodes).
							if not contains and unmatched:
									# Eg: GoT S00E08
									for i in unmatched.values():
										for j in i:
											title2 = self._extractTitle(j)
											if title2 and self.match(data = title2, title = title, combined = True, quick = True):
												contains = True
												break
							if not contains and unknown:
								# Same as the "elif discrepancy:" statement above, but from the other side/episode of the ID/number discrepancy.
								# Eg: Downton Abbey S00E13 - make sure the Trakt data (S00E12) is added to the TVDb data (S00E13).
								# Eg: The Office (India) - TVDb has the pilot as S00E01, while Trakt/TMDb have it as S01E01 and therefore have one more episode in S01.
								for i in unknown.values():
									title2 = self._extractTitle(i)
									if title2 and self.match(data = title2, title = title, combined = True, quick = True):
										contains = True
										break

						if not contains:
							for i in self._extractSeasons(item):
								if self._extractNumber(i, MetaPack.NumberStandard) == numberSeason:
									# If the number of a provider is missing, but the the ID of the provider is available, we know the episode has a number mismatch and we should search for the episode elsewhere.
									# Eg: GoT S00E08 (TVDb) vs S00E211 (Trakt/TMDb)
									if id and numberProvider is None:
										contains = True
										break
									else:
										for j in self._extractEpisodes(i):
											if self._extractNumber(j, MetaPack.NumberStandard, part = MetaPack.PartEpisode) == numberEpisode:
												contains = True
												break
									break

						if contains:
							found = []

							# Reduce the episodes (and therefore titles) that have to be matched.
							# In the strictest sense, we only have to scan the same season of the current episode, and not all the other seasons.
							# But still include S00 for specials that are placed elsewhere (eg Downton Abbey S05E09 on IMDb).
							if numberSeason == 0:
								episodeSet = episodeSpecial
							else:
								episodeCurrent = [i for i in episodeList if self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason) == numberSeason]
								if sequential: # Eg: Dragon Ball Supper S01E16 vs S02E02 (TVDb uses season numbers, Trakt/TMDb use absolute numbers).
									if numberSeason == 1: episodeSet = episodeCurrent + episodeLater + episodeSpecial
									else: episodeSet = episodeCurrent + episodeFirst + episodeSpecial
								else:
									episodeSet = episodeCurrent + episodeSpecial
							if unknown: episodeSet.extend(unknown.values())
							episodeSet = [i for i in episodeSet if not i is episode]

							# Firstly, try to find a match by ID. This is the most accurate.
							# Trakt can have an episode in absolute order, but still contain the correct TVDb ID to the episode in a different season.
							if not found and not discrepancy:
								extra = []
								if id:
									extra = episodeId[provider].get(id)
									if extra: extra = [i for i in extra if not i is episode]
								for episode2 in (extra or []) + episodeSet:
									id2 = self._extractId(episode2)
									if id2:
										if (checkImdb and checkImdb == id2.get(MetaPack.ProviderImdb)) or (checkTmdb and checkTmdb == id2.get(MetaPack.ProviderTmdb)) or (checkTvdb and checkTvdb == id2.get(MetaPack.ProviderTvdb)) or (checkTrakt and checkTrakt == id2.get(MetaPack.ProviderTrakt)):
											found.append(episode2)
											break

							# Secondly, try to find by title. This is the next-best option.
							# TVDb can have non-English titles, especially for anime (eg Dragon Ball Supper), and does not have any aliases/transalations.
							# Do not match titles across all seasons, since this takes very long (20+ secs for GoT).
							# 99% of the time, the matched episode is within the same season. That is, same season, only different episode order within that season.
							# 1% of the time it is an extra episode that is actually a special.
							# Not sure if there are any episodes that eg appear in S02, but actually belong to S03.
							# Sometimes there is a special that has the same title as an episode. Eg: TMDb S00E06 vs S01E07
							if not found:
								if title:
									extra = []
									for i in title if Tools.isArray(title) else [title]:
										j = episodeTitle.get(i)
										if j: extra.extend(j)
									if extra:
										extra = Tools.listUnique([i for i in extra if not i is episode])
										found.extend(extra)
									if not found:
										for episode2 in episodeSet:
											title2 = self._extractTitle(episode2)
											if title2 and self.match(data = title2, title = title, combined = True, quick = True):
												found.append(episode2)
												break

							# Thirdly, try to find by season/episode number.
							# This is the least accurate, since providers can have missing seasons, missing episodes, different episode numbering, combined/uncombined episodes, etc.
							# Only use the "unknown" episodes that were previously not combined into the "episode" object.
							# This should mostly be TMDb (non-S01) objects.
							# Only do this for Specials if there is no discrepancy between the number of special episodes, since the numbering can differ.
							# Eg: Downton Abbey S00E12 vs S00E13 (TVDb vs Trakt).
							# NB: Only do this if not found yet, otherwise there is an issue combining The Office (India) S00E01 (TVDb) vs S01E01 (Trakt).
							if not found and (not numberSeason == 0 or not specialDiscrepancy):
								episode2 = episodeUnknown.get(numberSeason, {}).get(numberEpisode)
								if episode2: found.append(episode2)
								if numberSeason >= 1 and not numberEpisode == numberSequential:
									episode2 = episodeUnknown.get(1, {}).get(numberSequential)
									if episode2: found.append(episode2)

							if found:
								group = [episode] + found
								episode.update({ # Update to keep the reference to the same object in episodeTree.
									'id'		: {
										'imdb'	: self._extractSelect(data = group, key = ['id', 'imdb']),
										'tmdb'	: self._extractSelect(data = group, key = ['id', 'tmdb']),
										'tvdb'	: self._extractSelect(data = group, key = ['id', 'tvdb']),
										'trakt'	: self._extractSelect(data = group, key = ['id', 'trakt']),
									},
									'number'	: self._createNumber(data = group),
									'support'	: self._extractSelect(data = group, key = 'support'),
									'type'		: self._extractDict(data = group, key = 'type'),

									'status'	: self._extractSelect(data = group, key = 'status'),
									'title'		: self._createTitle(data = group, language = language, setting = setting),

									'year'		: self._extractSelect(data = group, key = 'year'),
									'time'		: self._extractSelect(data = group, key = 'time'),
									'duration'	: self._extractDuration(data = group, key = 'duration'),
								})



					# Only update here, and not in the for-loop above that does the same thing.
					# Since we want to get the "true" absolute number from another provider if available, instead of using the overwritten value that uses the custom calculated number.
					episode['number'] = self._createNumber(data = episode)

					# Fill in missing status.
					if not self._extract(episode, 'status'):
						time = self._extract(episode, 'time')
						if time: episode['status'] = MetaPack.StatusUpcoming if time > current else MetaPack.StatusEnded

					# Interpolate TMDb S0 numbers that we previously filtered out, because there is no extended metadata, so ID/title matching is not possible.
					# Use the Trakt metadata, since it seems Trakt always has the episode numbering and episode metadata from TMDb and not TVDb.
					# Eg: S00E211 (Trakt/TMDb) vs S00E08 (TVDb).
					# Also do this for other seasons, since the absolute number is not available from TMDb, but it is probably the same as Trakt.
					if self._extractId(episode, MetaPack.ProviderTmdb):
						number = self._extractNumber(episode, provider = MetaPack.ProviderTrakt)
						if number:
							if not episode['number'].get(MetaPack.ProviderTmdb): episode['number'][MetaPack.ProviderTmdb] = {}
							episode['number'][MetaPack.ProviderTmdb].update({k : v for k, v in number.items() if not v is None})

			################################################################################################################
			# STEP 7 - Combine the metadata for automatic absolute episodes that are not part of any standard season.
			################################################################################################################

			# Fill in the automatically added absolute episodes.
			# Do this AFTER the complex for-loop above.
			# Since we know there are no IDs and titles for matching, only combine the objects without any computational expensive matching.
			for provider, item in base:
				for episode in episodeList:
					if self._extractType(episode, MetaPack.NumberAutomatic):
						if self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartSeason) == 1:
							numberEpisode = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
							numberSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
							id = self._extractId(episode, provider)
							if not id and not numberEpisode and numberSequential: # Data is missing.
								found = None
								for episode2 in episodeLater: # Do not use episodeSet.
									if not episode2 is episode:
										if self._extractNumber(episode2, MetaPack.NumberSequential, part = MetaPack.PartEpisode) == numberSequential:
											found = episode2
											break
								if found:
									combined = [episode, found]
									episode.update({
										'id'		: {
											'imdb'	: self._extractSelect(data = combined, key = ['id', 'imdb']),
											'tmdb'	: self._extractSelect(data = combined, key = ['id', 'tmdb']),
											'tvdb'	: self._extractSelect(data = combined, key = ['id', 'tvdb']),
											'trakt'	: self._extractSelect(data = combined, key = ['id', 'trakt']),
										},
										'number'	: self._createNumber(data = combined),
										'support'	: self._extractSelect(data = combined, key = 'support'),
										'type'		: self._extractDict(data = combined, key = 'type'),

										'status'	: self._extractSelect(data = combined, key = 'status'),
										'title'		: self._createTitle(data = combined, language = language, setting = setting),

										'year'		: self._extractSelect(data = combined, key = 'year'),
										'time'		: self._extractSelect(data = combined, key = 'time'),
										'duration'	: self._extractDuration(data = combined, key = 'duration'),
									})

									# Overwrite the numbers, since they can be replaced by a different number from certain providers.
									episode['number'][MetaPack.NumberStandard] = [1, numberSequential]
									episode['number'][MetaPack.NumberSequential] = [1, numberSequential]

			################################################################################################################
			# STEP 8 - Combine duplicate episodes from messed up shows.
			################################################################################################################

			# This is probably the shitties code in this function, but it seems to work pretty decently.
			# There are some shows that are very different from various providers.
			# Eg: One Piece (Anime).
			#	1. Trakt uses season-numbering for the seasons, but within the seasons, the episodes are numbered absolutely.
			#	2. Trakt and TVDb have the same number of seasons, but internally they are completely different. Differnt episode count, different offset, and some episodes are in a completely different season between Trakt and TVDb.
			#	3. Trakt has some storyline episodes as standard episodes, while others are in S0. TVDb also does this, but seems to have more of these episodes in S0. And sometimes a TVDb standard episode is a Trakt special, and for another Trakt standard episode, it is a TVDb special.
			#	4. Some of the episode titles vary slightly between Trakt and TVDb.
			#	5. Trakt seems to often use the TVDb absolute episode IDs, which are different to the TVDb standard IDs.
			#	6. And so much more that is messed up in the numbering.
			# With these issues, some seasons (eg: S22) end up with more episodes than the max(Trakt, TVDb), since the episode will be contained once for the standard TVDb number, and once for the Trakt absolute number.
			# A quick hack is to simply check if a season contains mutiple episodes with the same standard number, and if so, combined them.
			# NB: Not sure if there are unforeseen implications for other shows when using this.

			episodeLookup = {}
			episodeDelete = []
			for numberSeason, season in episodeTree.items():
				for numberEpisode, episode in season.items():
					numberSeason2 = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason)
					numberEpisode2 = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
					if not numberSeason2 is None and not numberEpisode2 is None:
						key = (numberSeason2, numberEpisode2)
						if not key in episodeLookup: episodeLookup[key] = []
						episodeLookup[key].append(episode)
						if len(episodeLookup[key]) > 1:
							Tools.update(episodeLookup[key][0], episodeLookup[key][-1], none = False, lists = False, unique = False)
							episodeDelete.append((numberSeason, numberEpisode))

			for i in episodeDelete:
				del episodeTree[i[0]][i[1]]

			################################################################################################################
			# STEP 9 - Determine the episode type and other cleanup.
			################################################################################################################

			episodeTrakt = {}
			numbers = [MetaPack.NumberStandard, MetaPack.NumberSequential, MetaPack.NumberAbsolute]
			ids = [MetaPack.ProviderTrakt, MetaPack.ProviderTvdb, MetaPack.ProviderTmdb, MetaPack.ProviderImdb]

			# Determine the episode type.
			for numberSeason, season in episodeTree.items():
				for numberEpisode, episode in season.items():
					available = 0
					available2 = 0
					for provider in providers:
						# Check either season+episode number, or season number + ID, since numbers do not always match.
						# Eg: One Piece S22E01 vs S22E1089.
						# Season numbers can be vary greatly, if Trakt has an absolute offset within the season.
						# Eg: One Piece S02E01 (Trakt/TMDb S02E62 vs TVDb S05E02)
						matchId = self._extractId(episode, provider = provider)
						matchSeason = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason, provider = provider) == numberSeason
						matchEpisode = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = provider) == numberEpisode
						if matchSeason:
							if matchEpisode or matchId: available += 1
							if matchEpisode: available2 += 1

					count = [showCount.get(i, {}).get(numberSeason) for i in providers]
					count = [i for i in count if i]
					minimum = min(count) if count else 0
					maximum = max(count) if count else 0
					difference = maximum - minimum

					# All non-automatic episodes are standard.
					# Or any special that has a season number with at least one provider.
					if not self._extractType(episode, MetaPack.NumberAutomatic) and (numberSeason > 0 or any(self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason, provider = i, default = 0) >= 0 for i in providers)):
						episode['type'][MetaPack.NumberStandard] = True

					# If a standard episode is available on Trakt, mark as "official".
					# If a standard episode is not available on Trakt, mark as "unofficial".
					# Also do this for S0, since we need the official count of specials for the checkmark in season menus.
					if not self._extractType(episode, MetaPack.NumberAutomatic):
						numberTrakt = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason, provider = MetaPack.ProviderTrakt, default = -1)
						if numberTrakt >= 0 and (numberTrakt == numberSeason or numberTrakt > 1): episode['type'][MetaPack.NumberOfficial] = True
						elif available > 0: episode['type'][MetaPack.NumberUnofficial] = True

					# If an episode is on all providers, mark as "universal".
					# Alternativley, check available2 which is purley based on IDs, in case the season/episode numbers are far off.
					# Eg: One Piece S02E01 (Trakt/TMDb S02E62 vs TVDb S05E02)
					# The seond part of the if-statement is used to later mark the correct official/unofficial episode labels with Italics.
					if available == providerCount or (available2 == 0 and available >= (providerCount - 1)):
						episode['type'][MetaPack.NumberUniversal] = True

					# Special season (S0) or special "legacy" special episodes (SxxE00).
					# Or any of the providers has the episode listed under S0, while others have it as a standard episode inside a season.
					if numberSeason == 0 or numberEpisode == 0 or any(self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason, provider = i) == 0 for i in providers):
						episode['type'][MetaPack.NumberSpecial] = True

					# A provider has a new unreleased season, while other providers have not added it yet.
					if numberSeason > 0 and available > 0 and self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode) and (not episode.get('time') or (episode.get('time') or 0) > current):
						episode['type'][MetaPack.NumberStandard] = True

					# One or more providers have a single sequential-numbered season S01, where not all episodes are part of the standard S01 from the other providers that use mutiple seasons.
					# We might not want to show these in the "Season 1" menus if there is an "Absolute" menu as well.
					# Eg: Dragon Ball Super (mutiple seasons on TVDb, but single absolute season on Trakt/TMDb).
					if numberSeason == 1 and available > 0:
						episode['type'][MetaPack.NumberSequential] = True

					# Automatically added episodes are currently all sequential episodes.
					if numberSeason == 1 and self._extractType(episode, MetaPack.NumberAutomatic):
						episode['type'][MetaPack.NumberSequential] = True

					# Episodes who have an absolute number from a provider.
					if numberSeason == 1 and self._extractNumber(episode, MetaPack.NumberAbsolute, part = MetaPack.PartEpisode): # Ignore specials which Trakt assigns a "0" absolute number.
						episode['type'][MetaPack.NumberAbsolute] = True

					# For season-based absolute numbering on Trakt/TMDb.
					# Eg: One Piece S21E892 - S21E1088.
					# This is important to get the correct next episode in MetaManager.metadataEpisodeNext().
					# After the lookup tables have been created, these episode's types will be adjusted.
					if numberSeason > 0 and not self._extractType(episode, MetaPack.NumberAutomatic):
						numberTrakt = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason, provider = MetaPack.ProviderTrakt, default = -1)
						if numberTrakt > 0:
							numberTraktStandard = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = MetaPack.ProviderTrakt, default = -1)
							numberTraktSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode, provider = MetaPack.ProviderTrakt, default = -2)
							if numberTrakt > 1:
								if numberTraktStandard == numberTraktSequential and numberEpisode == numberTraktStandard:
									episode['type'][MetaPack.NumberCustom] = True
								else:
									# If the Trakt season number does not match with the Gaia season number, it probably means this is an unofficial TVDb episode that maps to a different season.
									# Eg: One Piece S07E33 -> S07E34
									if numberEpisode > 1 and not numberTrakt == numberSeason:
										episode['type'][MetaPack.NumberCustom] = True

									# If the Trakt episode was previously processes, it means this one is a TVDb episode that simply maps to an earlier Trakt episode that coincidentally falls within the correct season, so the previous if-statement does not catch it.
									# Eg: One Piece S17E65+
									else:
										if (numberTrakt, numberTraktStandard) in episodeTrakt:
											episode['type'][MetaPack.NumberCustom] = True
										else:
											episodeTrakt[(numberTrakt, numberTraktStandard)] = True

					# Other cleanup.

					# Add [None, None] to numbers that are not available.
					# Eg: House S06 on Trakt does not have absolute numbers.
					number = episode.get('number')
					if number:
						for j in numbers:
							if not number.get(j): number[j] = [None, None]
						for i in ids:
							for j in numbers:
								if not number.get(i, {}).get(j):
									if not i in number: number[i] = {}
									number[i][j] = [None, None]

					# Remove invalid IDs to reduce the data size.
					episode['id'] = {k : v for k, v in self._extractId(episode, default = {}).items() if v}

					# Remove unsupported providers.
					support = [i for i in providers if self._extractId(episode, i) or not self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = i) is None]
					episode['support'] = [i for i in self._extract(episode, 'support', []) if i in support]

					# Remove non-existing titles.
					if not self._extract(episode, 'title'):
						try: del episode['title']
						except: pass

			################################################################################################################
			# STEP 10 - Fill in missing IDs and numbers for unofficial episodes.
			################################################################################################################

			# Unofficial or uncombined episodes from TVDb often do not have a Trakt/TMDb ID and number.
			# Eg: Star Wars: Young Jedi Adventures S01E26 (TVDb).
			# Fill in the missing ID and number, so we know the corresponding Trakt ID.
			# Only do this after the type was calculated, otherwise it will replace the values of the other (correct) episode.
			# Plus, we only do this for NumberUnofficial to reduce title matching.

			episodeCustom = {i : {} for i in providersAll}
			for numberSeason, season in episodeTree.items():
				for numberEpisode, episode in season.items():
					if self._extractType(episode, MetaPack.NumberUnofficial) and not self._extractId(episode, MetaPack.ProviderTrakt):
						title = self._extractTitle(episode)
						if title:
							for episode2 in episodeList:
								if episode is episode2: continue
								title2 = self._extractTitle(episode2)
								if title2 and self.match(data = title2, title = title, combined = True, quick = True):
									for j in providersAll:
										if episode.get('id').get(j) is None: episode['id'][j] = episode2.get('id').get(j)
										numberStandard = episode.get('number').get(j).get(MetaPack.NumberStandard)
										if numberStandard is None or numberStandard[MetaPack.PartEpisode] is None:
											episodeCustom[j][tuple(episode2.get('number').get(j).get(MetaPack.NumberStandard))] = True
											Tools.update(episode.get('number').get(j), episode2.get('number').get(j), none = False, lists = False, unique = False)
									break

			################################################################################################################
			# STEP 11 - Combine season metadata and calculate summaries from the episodes.
			################################################################################################################

			seasons = {}
			for numberSeason, season in seasonTree.items():
				# Sort the episodes according to number.
				# Some specials are not always sorted.
				episode = [(k, v) for k, v in episodeTree.get(numberSeason, {}).items()]
				episode = Tools.listSort(episode, key = lambda i : i[0])
				episode = [i[1] for i in episode]

				item = {
					'id'		: {
						'imdb'	: self._extractSelect(data = season, key = ['id', 'imdb']),
						'tmdb'	: self._extractSelect(data = season, key = ['id', 'tmdb']),
						'tvdb'	: self._extractSelect(data = season, key = ['id', 'tvdb']),
						'trakt'	: self._extractSelect(data = season, key = ['id', 'trakt']),
					},
					'number'	: self._extractDict(data = season, key = 'number'),
					'support'	: supports.get(numberSeason),
					'type'		: {},

					'status'	: self._extractSelect(data = season, key = 'status'),
					'title'		: self._createTitle(data = season, language = language, setting = setting),

					# Calculated later, since the episode types can change.
					'year'		: None,
					'time'		: None,
					'duration'	: None,
					'count'		: None,

					'episodes'	: episode,
				}

				# Remove invalid IDs to reduce the data size.
				item['id'] = {k : v for k, v in self._extractId(item, default = {}).items() if v}

				# Remove unsupported providers.
				support = [i for i in providers if self._extractId(item, i) or not self._extractNumber(item, MetaPack.NumberStandard, provider = i) is None]
				item['support'] = [i for i in self._extract(item, 'support', []) if i in support]

				# Add missing titles.
				if not item['title']: item['title'] = (['Specials'] if numberSeason == 0 else []) + ['Season %d' % numberSeason]

				# Clean the numbers.
				item['number'] = self._createNumber(data = item)

				# Interpolate TMDb absolute numbers from Trakt, since they are not avilable from TMDb, but are probably the same as those on Trakt.
				if self._extractId(item, MetaPack.ProviderTmdb):
					number = self._extractNumber(item, provider = MetaPack.ProviderTrakt)
					if number:
						if not item['number'].get(MetaPack.ProviderTmdb): item['number'][MetaPack.ProviderTmdb] = {}
						item['number'][MetaPack.ProviderTmdb].update({k : v for k, v in number.items() if not v is None})

				if numberSeason == 0:
					item['type'][MetaPack.NumberSpecial] = True
				else:
					item['type'][MetaPack.NumberStandard] = True
					if MetaPack.ProviderTrakt in support: item['type'][MetaPack.NumberOfficial] = True
					else: item['type'][MetaPack.NumberUnofficial] = True
					if len(support) == providerCount: item['type'][MetaPack.NumberUniversal] = True
					if numberSeason == 1:
						item['type'][MetaPack.NumberSequential] = True
						item['type'][MetaPack.NumberAbsolute] = True

				seasons[numberSeason] = item
			seasons = Tools.listSort(list(seasons.values()), key = lambda i : self._extractNumber(i, MetaPack.NumberStandard))

			################################################################################################################
			# STEP 12 - Create a lookup table for quick access and number mapping.
			################################################################################################################

			numbersUniversal = [MetaPack.NumberUniversal] + numbers

			lookupSeason = {}
			lookupEpisode = {}
			for i in numbersUniversal:
				lookupSeason[i] = {}
				lookupEpisode[i] = {}
			for i in ids:
				lookupSeason[i] = {}
				lookupEpisode[i] = {}

			# This is for shows where TVDb has more episodes in a season than Trakt.
			#	Eg: Star Wars: Young Jedi Adventures S01
			# This causes inconsistency between standard S01 numbering and sequential/absolute numbering.
			#	Eg: Star Wars: Young Jedi Adventures S01E26 is a standard episode on TVDb, but not on Trakt. But S01E26 should also be the sequential number for S02E01.
			# We do not want to remove the extra TVDb episodes from the start, since we still want to display them in the Seasons menu.
			# But at the same time, we do not want to include these in the lookup tables and sequential/absolute number calculations.
			# Create a pre-lookup table here, and when we create the universal lookup table, ignore these redundant episodes and use the sequential episode from a later season instead.
			lookupSequential = {}
			indexSeason = 0
			for season in seasons:
				indexEpisode = 0
				episodes = season.get('episodes') # Use the updated episode list.
				for episode in episodes:
					if self._extractType(episode, MetaPack.NumberOfficial):
						numberSeason = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason)
						numberEpisode = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
						if numberSeason is None or numberEpisode is None: continue

						base = {MetaPack.ValueIndex : [indexSeason, indexEpisode]}
						for i in numbers: base[i] = self._extractNumber(episode, i)
						for i in ids: base[i] = self._extractNumber(episode, MetaPack.NumberStandard, provider = i)

						numberSeason = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartSeason)
						numberEpisode = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
						if not numberSeason in lookupSequential: lookupSequential[numberSeason] = {}
						lookupSequential[numberSeason][numberEpisode] = base

					indexEpisode += 1
				indexSeason += 1

			lookupNumber = {}
			automatics = []
			counter = 0
			indexSeason = 0
			for season in seasons:
				# Season lookups.
				numberSeason = self._extractNumber(season, MetaPack.NumberStandard)
				base = {MetaPack.ValueIndex : indexSeason}
				for i in numbers: base[i] = self._extractNumber(season, i)
				for i in ids: base[i] = self._extractNumber(season, MetaPack.NumberStandard, provider = i)

				for number in numbersUniversal:
					numberLookup = MetaPack.NumberStandard if number == MetaPack.NumberUniversal else number
					if not numberSeason == 1 and (numberLookup == MetaPack.NumberSequential or numberLookup == MetaPack.NumberAbsolute): continue # Ignore non-S01 for sequential/absolute.
					item = Tools.copy(base)
					for i in ids:
						numberSeason2 = self._extractNumber(season, numberLookup, provider = i)
						if not numberSeason2 is None:
							item[i] = numberSeason2
							lookupSeason[i][numberSeason2] = Tools.copy(base)
					lookupSeason[number][self._extractNumber(season, numberLookup)] = item

				# Episode lookups.
				indexEpisode = 0
				episodes = season.get('episodes') # Use the updated episode list.
				for episode in episodes:
					numberSeason = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason)
					numberEpisode = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
					if numberSeason is None or numberEpisode is None: continue

					types = (MetaPack.NumberSequential, MetaPack.NumberAbsolute)
					automatic = self._extractType(episode, MetaPack.NumberAutomatic)
					added = False

					# Add the type for "exists" below. It will later be removed again.
					base = {MetaPack.ValueIndex : [indexSeason, indexEpisode], 'type' : self._extractType(episode)}
					for i in numbers: base[i] = self._extractNumber(episode, i)
					for i in ids: base[i] = self._extractNumber(episode, MetaPack.NumberStandard, provider = i)

					# Only increment the index counter if it was not created before.
					# Eg: One Piece S02E62 (Trakt) is S02E01 (Gaia Official).
					# Eg: One Piece S03E78 (Trakt) is S03E01 (Gaia Official).
					# We do not want to increment the index for S02E62, since it was already done for S02E01, which is the same episode.
					increment = True
					addition = None
					numberSequential = tuple(self._extractNumber(episode, MetaPack.NumberSequential))
					if numberSeason > 0:
						if self._extractType(episode, MetaPack.NumberOfficial): # One Piece S02E62 (Trakt).
							addition = lookupNumber.get(numberSequential)
							if addition and not self._extractType(episode, MetaPack.NumberUniversal): # Star Wars: Young Jedi Adventures S02E01 (Trakt).
								base[MetaPack.ValueIndex] = Tools.copy(addition[MetaPack.ValueIndex])
								increment = False
						elif not self._extractType(episode, MetaPack.NumberUnofficial): # Dragon Ball Super S05E55 (TVDB).
							increment = False

					for number in numbersUniversal:
						# Exclude unofficial episodes from TVDb.
						# Eg: Star Wars: Young Jedi Adventures
						if number in types and not(self._extractType(episode, MetaPack.NumberOfficial) or self._extractType(episode, MetaPack.NumberAutomatic)): continue

						# Exclude specials that are a normal episode on Trakt, but a special on TVDb.
						# Eg: One Piece S15E590 (Trakt) vs S00E39 (TVDb): The titles are different, but the release date is the same and Trakt has S00E39's TVDb ID under its episode.
						# Update: Do this now via existsSpecial below.
						#if number == MetaPack.NumberStandard and numberSeason > 0 and self._extractType(episode, MetaPack.NumberSpecial): continue

						if number == MetaPack.NumberUniversal or number in types or self._extractType(episode, number) or (number == MetaPack.NumberStandard and self._extractType(episode, MetaPack.NumberSpecial)):
							numberLookup = MetaPack.NumberStandard if number == MetaPack.NumberUniversal else number

							nativeSeason = self._extractNumber(episode, numberLookup, part = MetaPack.PartSeason)
							nativeEpisode = self._extractNumber(episode, numberLookup, part = MetaPack.PartEpisode)
							if nativeEpisode == 0 and numberLookup in types: continue # Ignore E00 for sequential/absolute, which all specials use.

							item = None
							if number == MetaPack.NumberUniversal and numberSeason == 1 and not self._extractType(episode, MetaPack.NumberOfficial):
								try: item = lookupSequential[numberSeason][numberEpisode]
								except: pass
							if not item: item = Tools.copy(base)

							if automatic:
								if not added:
									automatics.append(episode)
									added = True

							# Do not do this for absolute numbers, since they can be very far off.
							# Eg: Star Trek (1966) has 5 absolute episodes before S01E01, which can cause the lookup tables to be incorrect if we continue here.
							elif not numberLookup == MetaPack.NumberAbsolute:
								for i in ids:
									numberSeason2 = self._extractNumber(episode, numberLookup, part = MetaPack.PartSeason, provider = i)
									numberEpisode2 = self._extractNumber(episode, numberLookup, part = MetaPack.PartEpisode, provider = i)
									if numberEpisode2 == 0 and numberLookup in types: continue # Ignore E00 for providers, which all specials use.
									if not numberSeason2 is None and not numberEpisode2 is None:
										# NB: Only add the episode to the lookup if it was not added previously.
										# If there is an inconsistency with the season division between Trakt and TVDb, the same episode can appear in multiple seasons.
										# Eg: One Piece S01E25 (Trakt) is in the official Gaia S01, but is also S02E17 (TVDb) and also appears in official Gaia S02 (since Trakt's S02 only has 16 episodes).
										# Without checking the existence first, we first add S01E25 to the Trakt lookup, which correctly points to Gaia's index [1,24] episode.
										# Then later when S02E17 comes up, the existing Trakt lookup gets replaced with this "unofficial" version.
										# Either add to the lookup if it does not exist yet, or if the later episode is official, while the previous one is unofficial.
										try: exists = lookupEpisode[i][numberSeason2][numberEpisode2]
										except: exists = False

										# Some episodes exists multipl;e times.
										# Eg: One Piece: S15E10 (Gaia), S15E590 (Trakt/TMDb), S00E39 (TVDb).
										# This can cause the suboptimal episode to be picked in MetaManager._metadataEpisodeUpdate().
										# Eg: For Trakt/TMDb S15E590, it will pick the special episode (S00E39) instead of season episode (S15E10/S15E590).
										# This will make S01E590 in the Absolute menu show up as S01E00 (since it is seen as a special).
										# If we detect an existing entry in the lookup that is from S0, replace it with a later episode.
										# Only do this for specials, not S1+, since there can be season-overlapping.
										# Eg: One Piece S01E25 (Trakt/TMDb) vs S02E17 (TVDb).
										existsSpecial = False
										if exists and exists.get(MetaPack.NumberStandard)[MetaPack.PartSeason] == 0:
											existsFound = False
											existsNumber = [numberSeason, numberEpisode]
											for j in numbers + ids:
												if exists.get(j) == existsNumber:
													existsFound = True
													break
											if not existsFound: existsSpecial = True

										if not exists or existsSpecial or (self._extractType(exists, MetaPack.NumberUnofficial) and self._extractType(item, MetaPack.NumberOfficial)):
											item[i] = [numberSeason2, numberEpisode2]
											if not numberSeason2 in lookupEpisode[i]: lookupEpisode[i][numberSeason2] = {}

											# Use the "real" standard number.
											# Eg: One Piece S02E62 (Trakt) is S02E01 (Gaia Official).
											# Otherwise the lookup in MetaManager._metadataEpisodeUpdate() uses the Trakt standard numbers instead of the Gaia standard numbers.
											base2 = Tools.copy(base)
											if addition:
												# Do not do this if the addition is a special, while base is a standard S01+ episode.
												# Eg: Better Call Saul S01E01 "Uno", also has a TVDb special S00E56 with the same title "Uno". This is the same episode that TVDb has as S01E01 and as a special S00E56 (although their TVDb IDs are different).
												# Without this, the "lookup" -> "episode" -> "trakt" -> would have S01E01 poiting to S00E56, even though Trakt also has this episode as S01E01.
												if not(base2[MetaPack.NumberStandard][MetaPack.PartSeason] >= 1 and addition[MetaPack.NumberStandard][MetaPack.PartSeason] == 0):
													base2[MetaPack.ValueIndex] = Tools.copy(addition[MetaPack.ValueIndex])
													base2[MetaPack.NumberStandard] = Tools.copy(addition[MetaPack.NumberStandard])

											# Only add unofficial episodes to the lookup table if they were not previously manipulated.
											# Otherwise the manipulated numbers cause havok in the lookup table generation.
											# Eg: Star Wars: Young Jedi Adventures S01E26 on TVDb is added to episodeCustom (since it's Trakt numbers are filled in and it should not be used here, since it is an unofficial episode).
											if self._extractType(episode, MetaPack.NumberUnofficial):
												if not episodeCustom.get(i).get((numberSeason2, numberEpisode2)):
													lookupEpisode[i][numberSeason2][numberEpisode2] = base2
											else:
												lookupEpisode[i][numberSeason2][numberEpisode2] = base2

							if not nativeSeason in lookupEpisode[number]: lookupEpisode[number][nativeSeason] = {}
							lookupEpisode[number][nativeSeason][nativeEpisode] = item

					if increment:
						counter += 1
						indexEpisode += 1
						lookupNumber[numberSequential] = base
				indexSeason += 1

				# Remove automatically added absolute episodes to reduce size.
				# The lookup table now has these episodes, so we can still retrieve them.
				season['episodes'] = [i for i in episodes if not self._extractType(i, MetaPack.NumberAutomatic)]

			# Get the correct numbers for automatically added episodes.
			# The indexes for automatic sequential/absolute episodes are also incorrect (incremented in S01 after the last standard S01 episode).
			for episode in automatics:
				for number in numbersUniversal:
					if number == MetaPack.NumberUniversal or self._extractType(episode, number) or (number == MetaPack.NumberStandard and self._extractType(episode, MetaPack.NumberSpecial)):
						numberLookup = MetaPack.NumberStandard if number == MetaPack.NumberUniversal else number
						numberSeason = self._extractNumber(episode, numberLookup, part = MetaPack.PartSeason)
						numberEpisode = self._extractNumber(episode, numberLookup, part = MetaPack.PartEpisode)
						found = None
						for j in self._extract(episode, 'support', default = []):
							try: found = lookupEpisode[j][self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason, provider = j)][self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = j)]
							except: pass
							if found and found.get(MetaPack.NumberStandard):
								# Specials that were removed above.
								# Eg: One Piece S15E590 (Trakt) vs S00E39 (TVDb): The titles are different, but the release dateis the same and Trakt has S00E39's TVDb ID under its episode.
								if number == MetaPack.NumberStandard and not found[MetaPack.NumberStandard][MetaPack.PartSeason] == numberSeason: continue

								try:
									lookupEpisode[number][numberSeason][numberEpisode].update(lookupEpisode[MetaPack.NumberStandard][found[MetaPack.NumberStandard][MetaPack.PartSeason]][found[MetaPack.NumberStandard][MetaPack.PartEpisode]])
									break
								except:
									# This will be triggered if a new season is available on a provider with a single unaired episode.
									# That is, a new unreleased season that has not been added to all providers yet.
									try:
										lookupEpisode[number][numberSeason][numberEpisode].update(lookupEpisode[MetaPack.NumberUniversal][found[MetaPack.NumberStandard][MetaPack.PartSeason]][found[MetaPack.NumberStandard][MetaPack.PartEpisode]])
										break
									except: Logger.error()

			# Delete the type we added to check "exists".
			for v1 in lookupEpisode.values():
				for v2 in v1.values():
					for v3 in v2.values():
						try: del v3['type']
						except: pass

			################################################################################################################
			# STEP 14 - Cleanup and calculate summaries for seasons.
			################################################################################################################

			# Clean the types for season-based absolute numbering on Trakt/TMDb.
			# Eg: One Piece S21E892 - S21E1088.
			# Only do this AFTER the lookup tables were created, since they need the NumberOfficial type there.
			for episode in episodeList:
				if self._extractType(episode, MetaPack.NumberCustom):
					episode['type'][MetaPack.NumberUnofficial] = True
					for i in [MetaPack.NumberCustom, MetaPack.NumberOfficial, MetaPack.NumberStandard, MetaPack.NumberUniversal]:
						try: del episode['type'][i]
						except: pass

			for season in seasons:
				episodes = season.get('episodes')
				season['year'] = self._createSummaries(data = episodes, value = 'year', count = False, total = False, mean = False, minimum = True, maximum = True, values = True, sort = True, unique = True)
				season['time'] = self._createSummaries(data = episodes, value = 'time', count = False, total = False, mean = False, minimum = True, maximum = True, values = True, sort = True, unique = True)
				season['duration'] = self._createSummaries(data = episodes, value = 'duration', count = False, total = True, mean = True, minimum = True, maximum = True, values = False)
				season['count'] = self._createCount(data = episodes)

			################################################################################################################
			# STEP 14 - Combine show metadata and calculate summaries from the seasons/episodes.
			################################################################################################################

			# Determine the show preference, based on the preferences of all seasons combined, excluding specials.
			available = Tools.listFlatten([self._extract(i, 'support', []) for i in seasons])
			support = {MetaPack.ProviderImdb : 0, MetaPack.ProviderTmdb : 0, MetaPack.ProviderTvdb : 0, MetaPack.ProviderTrakt : 0}
			for numberSeason in range(1, max(seasonCount.values()) + 1):
				value = supports.get(numberSeason)
				for i in support.keys():
					try: support[i] += value.index(i)
					except: support[i] += 5
			support = [(k, v) for k, v in support.items()]
			support = Tools.listSort(support, key = lambda i : i[1])
			support = [i[0] for i in support if i[0] in available]

			result = self._initialize(pack = {
				'media'		: Media.Show,

				'id'		: {
					'imdb'	: self._extractSelect(data = data, key = ['id', 'imdb']),
					'tmdb'	: self._extractSelect(data = data, key = ['id', 'tmdb']),
					'tvdb'	: self._extractSelect(data = data, key = ['id', 'tvdb']),
					'trakt'	: self._extractSelect(data = data, key = ['id', 'trakt']),
					'slug'	: self._extractSelect(data = data, key = ['id', 'slug']),
				},
				'support'	: support,

				'status'	: self._extractSelect(data = data, key = 'status'),
				'title'		: self._createTitle(data = data, language = language, setting = setting),

				'year'		: self._createSummaries(data = episodeList, value = 'year', count = False, total = False, mean = False, minimum = True, maximum = True, values = True, sort = True, unique = True),
				'time'		: self._createSummaries(data = episodeList, value = 'time', count = False, total = False, mean = False, minimum = True, maximum = True, values = True, sort = True, unique = True),
				'duration'	: self._createSummaries(data = episodeList, value = 'duration', count = False, total = True, mean = True, minimum = True, maximum = True, values = False),
				'count'		: self._createCounts(data = seasons),

				'seasons'	: seasons,

				'lookup'	: {MetaPack.ValueSeason : lookupSeason, MetaPack.ValueEpisode : lookupEpisode},
			})

			if System.developerVersion():
				ids = []
				for i in [MetaPack.ProviderTrakt, MetaPack.ProviderTvdb, MetaPack.ProviderTmdb, MetaPack.ProviderImdb]:
					id = self._extractId(result, i)
					if id: ids.append('%s: %s' % (i.upper(), id))
				ids = ' | '.join(ids)
				Logger.log('PACK GENERATION [%s]: %dms Duration, %d Episodes, %d Matches' % (ids, timer.elapsed(milliseconds = True), counter, len(self.mMatch.keys())))

			return result
		except: Logger.error()
		return None

	##############################################################################
	# MATCH
	##############################################################################

	# Match a title against a list of titles, to determine if an episode's title is valid.
	# title: a single title or list of titles.
	# combined: match combined titles that can contain two or more episode titles.
	# quick: if a list of titles is passed, only search until a match was found. If False, continues until the best match is found.
	# generic: wether or not to match generic episode titles. Eg: "Episode 1"
	def match(self, data, title, combined = True, quick = True, generic = False, adjust = None, detail = False):
		try:
			result = {'match' : 0.0, 'valid' : None}
			if data and title: # Both could be None or empty arrays.
				# Cache results in case we match the same string mutiple times.
				id = []

				if Tools.isArray(data): id.extend(data)
				else: id.append(data)
				if Tools.isArray(title): id.extend(title)
				else: id.append(title)
				id = Tools.listSort(id)

				id.append(str(combined))
				id.append(str(quick))
				id.append(str(generic))
				id.append(str(adjust))
				id = '_'.join(id)

				match = self.mMatch.get(id)
				if match: return match if detail else match.get('valid')

				if Tools.isArray(data) or Tools.isArray(title):
					if not Tools.isArray(data): data = [data]
					for i in data:
						for j in title:
							match = self.match(data = i, title = j, combined = combined, quick = quick, generic = generic, adjust = adjust, detail = True)
							if quick and match.get('valid'):
								result = match
								break
							elif match.get('match', 0) >= result.get('match', 0):
								result = match
						if quick and result.get('valid'): break
				else:
					threshold = 0.9
					if combined:
						if generic or not Regex.match(data = data, expression = MetaPack.ExpressionGeneric, cache = True):
							# "Title 1 / Title 2"
							# Eg: "The Young Jedi / Yoda's Mission" vs "The Young Jedi".
							data2 = title
							split = []

							# Either "data" or "title" can be split.
							for i in ['/', '|']:
								split = data.split(i)
								if len(split) > 1: break
							if len(split) <= 1:
								for i in ['/', '|']:
									split = title.split(i)
									if len(split) > 1: break
								data2 = data

							if len(split) > 1:
								for i in split:
									match = self.match(data = i, title = data2, combined = False, quick = quick, generic = generic, adjust = adjust, detail = True)
									if quick and match.get('valid'):
										result = match
										break
									elif match.get('match', 0) >= result.get('match', 0):
										result = match

						# "Title (1)" and "Title (2)"
						# "Title Part 1" and "Title Part 2"
						elif Regex.match(data = data, expression = '(.{2,})[\(\[\s\-\_\.]*(?:\d+|[ivxlcd]+|one|two|three|four|five)[\)\]\s\-\_\.]*$', cache = True):
							threshold = 0.75

					# Eg: Doctor Who - "The Doctor, the Widow and the Wardrobe" vs "The Doctor, the Widow and the Wardrobe Prequel"
					# These are two different episodes with very similar titles. Increase the threshold.
					if Regex.match(data = data, expression = '(prequel|sequel)', cache = True):
						threshold = 0.95

					# Make a little bit more lenient for shorter titles.
					# Eg: "The Young Jedi" vs "The Young Jedis" has 0.92 match (Levenstein).
					if len(data) < 20: threshold *= 0.95

					if adjust: threshold *= adjust

					if result.get('valid') is None: # Not already done by combined above.
						# Large shows can take a long time to generate, due to many title matches.
						# Eg: One Piece (TRAKT: 37696 | TVDB: 81797 | TMDB: 37854 | IMDB: tt0388629)
						# These are the generation times for One Piece:
						#	levenstein:			42436ms Duration, 3516 Episodes, 240349 Matches
						#	damerauLevenshtein:	50278ms Duration, 3516 Episodes, 240349 Matches
						#	jaro:				20843ms Duration, 3516 Episodes, 240262 Matches
						#	jaroWinkler:		21172ms Duration, 3516 Episodes, 240074 Matches
						#	longestSequence:	38887ms Duration, 3516 Episodes, 240310 Matches
						#	differenceSequence:	19580ms Duration, 3516 Episodes, 240394 Matches
						match = Matcher.jaro(data, title, ignoreCase = True, ignoreSpace = True, ignoreNumeric = False, ignoreSymbol = True)

						# If a close string match, but there are numbers in the title that do not match.
						# Eg: "Title Part (1)" vs "Title Part (2)"
						numbers1 = Regex.extract(data = data, expression = '(\d+)', group = None, all = True, cache = True)
						numbers2 = Regex.extract(data = title, expression = '(\d+)', group = None, all = True, cache = True)
						if not numbers1 == numbers2: match *= 0.7

						result = {'match' : match, 'valid' : match > threshold}

				self.mMatch[id] = result
		except: Logger.error()
		return result if detail else result.get('valid')

	##############################################################################
	# SEARCH
	##############################################################################

	# Search for an episode using the title.
	# season: pass a list of season numbers to only match some seasons for efficiency. Typically only the same season and S0 are neccessary.
	def search(self, title, season = True, lenient = False):
		if lenient is True:
			for i in [1.0, 0.9, 0.8]:
				episode = self.search(title = title, season = season, lenient = i)
				if episode: return episode
		else:
			seasons = self.season(season = season)
			if seasons:
				for season in seasons:
					for episode in self._extractEpisodes(season):
						if self.match(data = title, title = self._extractTitle(episode), combined = True, quick = True, generic = True, adjust = lenient, detail = False):
							return episode
		return None

	##############################################################################
	# REDUCE
	##############################################################################

	def reduce(self, season = None, episode = None):
		try:
			if self.mPack:
				values = {'media' : True, 'type' : True, 'year' : True, 'time' : True, 'duration' : True, 'count' : True}

				if not episode is None: data = self.episode(season = season, episode = episode)
				elif not season is None: data = self.season(season = season)
				else: data = self.mPack

				# Data can be None if the episode cannot be found in the pack, such as IMDb specials.
				# Eg: Downton Abbey S02E09.
				if data:
					result = Tools.copy({k : v for k, v in data.items() if k in values}) # Copy, because we delete entries below.
					for k1, v1 in result.items():
						try: del v1[MetaPack.ValueValues]
						except: pass
						if Tools.isDictionary(v1):
							for k2, v2 in v1.items():
								try: del v2[MetaPack.ValueValues]
								except: pass
					return result
		except: Logger.error()
		return None

	#gaiafuture
	#
	# This should only be used for the metaPack attribute in stream.py.
	# Internal lists from reduced packs start from index 1 (index 0 is None), since episode and movie numbers also start from 1.
	# Do not use a dictionary for season/episode/movie number structures, since the dictionary keys are converted to strings during serialization and we do not want to change them back to integers after unserialization.
	#
	# Do not add the entire original pack to the Stream object, for the following reasons:
	#	1. Some packs can be 1-2MB in uncompressed size. Even for an average show (eg GoT), the pack can still be a few 100KBs.
	#	2. Large packs increase computational time and size when the internal Stream dictionary is serialized/unserialized.
	#	3. Large packs increase the time and storage space when the Streams are saved to streams.db after scrape, although they all contain the same meta attributes, including the same pack data.
	#	4. Large packs increase the time for encoding/decoding of commands in core.py, that are created for each menu item in WindowStream, especially if there are 1000+ streams. Eg: using a reduced pack for 500 GoT streams decreases command encoding time from 20 secs down to 10 secs.
	#
	# This reduction is a quick solution to reduce time and size, but it is still not perfect.
	#	1. Larger packs (eg: Days of our Lives) with 10k+ episodes can still have a large reduced pack, since a lot of durations/counts are stored.
	#	2. This only addresses the metaPack attribute in Stream. But metaTitle can also be large (although not nearly as large as metaPack) and is the same across all streams from a scrape.
	#	3. We cannot just remove the metaTitle/metaPack attributes after the Stream was created/validated, since we later need that data again to do further title/number validation when an actual file is selected by filename from the pack during playback (Play -> Handler -> Debrid -> select file from torrent pack).
	#
	# In the future we should improve the way that streams are saved/processed in core.py.
	#	1. Make streams.db contain a summary table, and then one table per scrape, where each stream is its own row.
	#	2. Remove all "meta" attributes from the streams and store them once in the summary table.
	#	3. Give each scrape and each stream a unique ID (eg: Stream.idGaia()).
	#	4. Instead of adding the entire stream data to commands, context menus, etc, only add the scrape+stream IDs.
	#	5. Then similar to metadata.db, we can efficiently pass around the stream ID, and then when we actually need the full stream data (eg playback or context menu), we load the stream as a single DB row, add the "meta" attributes from the summary table to it, and return it.
	#
	# But irrespective of what we do with streams.db, reducing the pack for Stream has its own advantages.
	#	1. The reduction and lookup lists only have to be created once at the start of a scrape and can then be reused by all scraped streams with minimal/fast lookups, instead of 100s of streams using all using the slower functions in this class.
	#	2. If the internal Stream "mData" dictionary, or the scraper's "parameters" dictionary are passed around and possibly deep-copied, a smaller pack dictionary will be faster to copy.
	#	3. Calculating the internal cache ID in Stream for cached function calls that pass in the pack dictionary is faster with a smaller pack.
	#	4. Any intermediary serialization/unserialization of Stream, before it gets saved/processed in core.py, is faster with smaller packs.
	#	5. 90% of the pack info is not actuially needed in Stream. Only pass in the essentials.
	#
	def reduceStream(self):
		try:
			if self.mReduce: return self.mReduce

			if self.mPack:
				pack = {'media' : self.media(), 'year' : {}, 'count' : {}, 'duration' : {}}

				# Do not just add the year range, since some specials can be released years later.
				# Eg: The Office (US) has specials released in 2021.
				# This then causes other The Offices (eg: India 2019) to validate the streams as correct, since the year falls within the range.
				#pack['year'][MetaPack.ValueValues] = self.yearValues(default = [])
				#pack['year'][MetaPack.ValueRange] = self.yearRange()

				yearsNormal = []
				yearsSpecial = []
				for season in self.season(default = []):
					years = self.yearValues(item = season)
					if years:
						if self.typeSpecial(item = season): yearsSpecial.extend(years)
						else: yearsNormal.extend(years)

				yearsNormal = Tools.listSort(Tools.listUnique(yearsNormal))
				yearsSpecial = Tools.listSort(Tools.listUnique(yearsSpecial))

				if yearsNormal and yearsSpecial and abs(yearsNormal[-1] - yearsSpecial[-1]) > 5:
					pack['year'][MetaPack.ValueValues] = yearsNormal
					pack['year'][MetaPack.ValueRange] = [yearsNormal[0], yearsNormal[-1]]
				else:
					pack['year'][MetaPack.ValueValues] = self.yearValues(default = [])
					pack['year'][MetaPack.ValueRange] = self.yearRange()

				pack['duration'][MetaPack.ValueMean] = self.durationMeanOfficial()

				# Take into account specials that are part of S01+.
				# Eg: One Piece S15E590 (Trakt) vs S00E39 (TVDb).
				specialsTotal = self.countEpisodeSpecial()
				specialsReal = self.countEpisodeSpecial(season = 0)

				if self.mShow:
					pack['count'][MetaPack.ValueTotal] = {
						MetaPack.ValueSeason : self.countSeasonTotal(),
						MetaPack.ValueEpisode : self.count(),
						MetaPack.ValueSpecial : specialsTotal,
					}
					pack['count'][MetaPack.NumberOfficial] = {
						MetaPack.ValueMean : self.countMeanOfficial(fallback = True),
						MetaPack.ValueSeason : self.countSeasonOfficial(),
						MetaPack.ValueEpisode : self.countEpisodeOfficial(fallback = True),
						MetaPack.ValueSpecial : specialsReal,
					}
					pack['count'][MetaPack.NumberStandard] = {
						MetaPack.ValueMean : self.countMeanStandard(fallback = True),
						MetaPack.ValueSeason : self.countSeasonStandard(),
						MetaPack.ValueEpisode : self.countEpisodeStandard(fallback = True),
					}
					pack['duration'][MetaPack.ValueTotal] = self.durationTotalOfficial(default = 0)

					# There can be missing seasons. Eg: Days of our Lives.
					numberSeason = self.number(season = True, default = [])
					totalSeason = (max(numberSeason) + 1) if numberSeason else 0
					pack['count'][MetaPack.ValueSeason] = [0] * totalSeason
					pack['duration'][MetaPack.ValueSeason] = [None] * totalSeason
					pack['duration'][MetaPack.ValueEpisode] = [None] * totalSeason

					for i in numberSeason:
						# Lookup by standard number and then filter to only get official episodes.
						# Otherwise other non-official episodes might be added.
						# Eg: One Piece S21 would add the absolute numbers (eg S21E1008).

						# First try the official count (eg: One Piece S02).
						# Then try the standard count (eg: Dragon Ball Super S02).
						if i == 0: number = MetaPack.NumberSpecial
						else: number = MetaPack.NumberOfficial
						episodes = self.episode(season = i, episode = True, number = number)
						if not episodes:
							number = MetaPack.NumberStandard
							episodes = self.episode(season = i, episode = True, number = number)

						pack['count'][MetaPack.ValueSeason][i] = self.countEpisode(season = i, number = number)
						pack['duration'][MetaPack.ValueSeason][i] = self.durationTotal(season = i, number = number)

						numberEpisode = self.numberStandardEpisode(item = episodes, default = []) # Ignore absolute episodes in S01.
						totalEpisode = (max(numberEpisode) + 1) if numberEpisode else 0
						pack['duration'][MetaPack.ValueEpisode][i] = [None] * totalEpisode
						for j in numberEpisode: pack['duration'][MetaPack.ValueEpisode][i][j] = self.duration(season = i, episode = j)

				elif self.mMovie:
					total = self.count()
					pack['count'][MetaPack.ValueTotal] = total

					# Movie numbers start at 1.
					# This is important for Stream.__releaseValidCollection().
					total += 1
					pack['duration'][MetaPack.ValueValues] = [None] * total
					pack['title'] = [[]] * total
					for i in range(1, total):
						pack['duration'][MetaPack.ValueValues][i] = self.duration(movie = i, combine = False)
						pack['title'][i] = self.title(movie = i, default = [])

				self.mReduce = pack
				return self.mReduce
		except: Logger.error()
		return None

	@classmethod
	def reduceNumber(self, data = None, pack = None, season = None, episode = None):
		try:
			if not data and pack: data = self.instance(pack).episode(season = season, episode = episode, number = MetaPack.NumberStandard).get(MetaPack.ValueNumber)
			if data:
				custom = None
				if not episode is None: custom = [season, episode]

				standard = data.get(MetaPack.NumberStandard)
				if standard and standard[-1] is None: standard = None

				sequential = data.get(MetaPack.NumberSequential)
				if sequential and sequential[-1] is None: sequential = None

				absolute = data.get(MetaPack.NumberAbsolute)
				if absolute and absolute[-1] is None: absolute = None

				trakt = (data.get(MetaPack.ProviderTrakt) or {}).get(MetaPack.NumberStandard)
				if trakt and trakt[-1] is None: trakt = None

				tmdb = (data.get(MetaPack.ProviderTmdb) or {}).get(MetaPack.NumberStandard)
				if tmdb and tmdb[-1] is None: tmdb = None

				tvdb = (data.get(MetaPack.ProviderTvdb) or {}).get(MetaPack.NumberStandard)
				if tvdb and tvdb[-1] is None: tvdb = None

				all = [custom, standard, sequential, absolute, trakt, tmdb, tvdb]
				all = Tools.listUnique([i for i in all if i])

				# Numbers that are within the same season.
				# Eg: One Piece S03E01
				# Include Trakt, since it has season-absolute numbers for some anime, and many filenames use that number.
				# Eg: One Piece S03E78
				# Do not include TVDb, since it often has very different numbering to standard/Trakt/TMDb.
				# Sometimes there are some filenames that use TVDb numbers, but they are very rare and would result in too many false-positives during scraping.
				# Eg: One Piece S06E09
				# Even if TVDb's number falls into the same season (eg: S03), the numbers are probably too far off, resulting in too many false-positives.
				seasoned = [standard]
				if trakt and trakt[MetaPack.PartSeason] == season: seasoned.append(trakt) # Some shows are not on Trakt.
				seasoned = Tools.listUnique([i for i in seasoned if i])

				return {
					'all' : all,
					'season' : seasoned,

					MetaPack.NumberCustom : custom,
					MetaPack.NumberStandard : standard,
					MetaPack.NumberSequential : sequential,
					MetaPack.NumberAbsolute : absolute,

					MetaPack.ProviderTrakt : trakt,
					MetaPack.ProviderTmdb : tmdb,
					MetaPack.ProviderTvdb : tvdb,
				}
		except: Logger.error()
		return None

	def reduceSmart(self):
		try:
			if self.mPack:
				pack = {'count' : {}, 'time' : {}}

				if self.mShow:
					# Take into account specials that are part of S01+.
					# Eg: One Piece S15E590 (Trakt) vs S00E39 (TVDb).
					pack['count'][MetaPack.ValueTotal] = {
						MetaPack.ValueSeason : self.countSeasonTotal(),
						MetaPack.ValueEpisode : self.count(),
						MetaPack.ValueSpecial : self.countEpisodeSpecial(),
					}
					pack['count'][MetaPack.NumberOfficial] = {
						MetaPack.ValueSeason : self.countSeasonOfficial(),
						MetaPack.ValueEpisode : self.countEpisodeOfficial(fallback = True),
						MetaPack.ValueSpecial : self.countEpisodeSpecial(season = 0),
					}

					numberSeason = self.number(season = True, default = [])
					totalSeason = (max(numberSeason) + 1) if numberSeason else 0
					counts = [0] * totalSeason
					times = [None] * totalSeason
					for i in numberSeason:
						# First try the official count (eg: One Piece S02).
						# Then try the standard count (eg: Dragon Ball Super S02).

						if i == 0: number = MetaPack.NumberSpecial
						else: number = MetaPack.NumberOfficial
						count = self.countEpisode(season = i, number = number)
						if not count:
							number = MetaPack.NumberStandard
							count = self.countEpisode(season = i, number = number)

						counts[i] = count
						times[i] = [self.timeMinimum(season = i, number = number), self.timeMaximum(season = i, number = number)]

					pack['count'][MetaPack.ValueSeason] = counts
					pack['time'][MetaPack.ValueSeason] = times

				return pack
		except: Logger.error()
		return None

	@classmethod
	def reduceBase(self, seasonOfficial = None, seasonSpecial = None, episodeOfficial = None, episodeSpecial = None, duration = None):
		try:
			dataSeason = {}
			dataEpisode = {}
			dataMean = {}
			dataDuration = {}

			total = 0
			if seasonOfficial:
				total += seasonOfficial
				dataSeason[MetaPack.NumberOfficial] = seasonOfficial
				dataSeason[MetaPack.NumberAbsolute] = 1
			if seasonSpecial:
				total += 1
				dataSeason[MetaPack.NumberSpecial] = 1
			if total:
				dataSeason[MetaPack.ValueTotal] = total

			total = 0
			if episodeOfficial:
				total += episodeOfficial
				dataEpisode[MetaPack.NumberOfficial] = episodeOfficial
				dataEpisode[MetaPack.NumberAbsolute] = episodeOfficial
			if episodeSpecial:
				total += episodeSpecial
				dataEpisode[MetaPack.NumberSpecial] = episodeSpecial
			if total:
				dataEpisode[MetaPack.ValueTotal] = total

			if dataSeason and dataEpisode:
				for i in dataSeason.keys():
					try: dataMean[i] = int(dataEpisode.get(i) / dataSeason.get(i))
					except: pass

			if duration:
				durations = {
					MetaPack.ValueMean : duration,
					MetaPack.ValueMinimum : duration,
					MetaPack.ValueMaximum : duration,
				}
				if episodeOfficial: durations[MetaPack.ValueTotal] = duration * episodeOfficial

				dataDuration.update(durations)
				dataDuration[MetaPack.NumberOfficial] = Tools.copy(durations)
				dataDuration[MetaPack.NumberAbsolute] = Tools.copy(durations)

			data = {}
			if dataSeason or dataEpisode or dataMean:
				data['count'] = {}
				if dataSeason: data['count'][MetaPack.ValueSeason] = dataSeason
				if dataEpisode: data['count'][MetaPack.ValueEpisode] = dataEpisode
				if dataMean: data['count'][MetaPack.ValueMean] = dataMean
			if dataDuration:
				data['duration'] = dataDuration

			if data:
				data['media'] = Media.Show
				return data
		except: Logger.error()
		return None

	##############################################################################
	# RETRIEVE
	##############################################################################

	def _key(self, *types):
		return [i for i in types if not i is None]

	def _data(self, item = None, season = None, episode = None, number = None, sequential = None, movie = None):
		if not item is None: return item
		elif not movie is None: return self.movie(movie = movie)
		elif not episode is None or not sequential is None: return self.episode(season = season, episode = episode, number = number, sequential = sequential)
		elif not season is None: return self.season(season = season, number = number)
		else: return self.mPack

	def _mean(self, value, default = None, combine = True):
		if value:
			if Tools.isArray(value) and combine: return int(sum(value) / float(len(value)))
			return value
		return default

	def _minimum(self, value, default = None, combine = True):
		if value:
			if Tools.isArray(value) and combine: return min(value)
			return value
		return default

	def _maximum(self, value, default = None, combine = True):
		if value:
			if Tools.isArray(value) and combine: return max(value)
			return value
		return default

	def _range(self, minimum, maximum, default = None, combine = True):
		if Tools.isList(minimum) or Tools.isList(maximum):
			if combine:
				minimum = min(minimum) if minimum else None
				maximum = max(maximum) if maximum else None
				return self._range(minimum = minimum, maximum = maximum, default = default)
			else:
				result = []
				for i in range(len(minimum)):
					result.append([minimum[i], maximum[i]])
				return result
		else:
			if minimum is None and maximum is None: return default
			elif minimum is None: return [maximum, maximum]
			elif maximum is None: return [minimum, minimum]
			else: return [minimum, maximum]

	def _retrieve(self, item = None, base = None, value = None, season = None, episode = None, sequential = None, movie = None, number = None, part = None, type = None, provider = None, default = None, combine = True):
		try:
			if item or self.mPack:
				multiSeason = Tools.isList(season)
				multiEpisode = Tools.isList(episode)
				multiMovie = Tools.isList(movie)
				if multiSeason or multiEpisode or multiMovie:
					results = []

					if multiSeason:
						for i in season:
							result = self._retrieve(base = base, value = value, season = i, episode = episode, sequential = sequential, number = number, part = part, type = type, default = default, combine = combine)
							if result: results.append(result)
					elif multiEpisode:
						for i in episode:
							result = self._retrieve(base = base, value = value, season = season, episode = i, sequential = sequential, number = number, part = part, type = type, default = default, combine = combine)
							if result: results.append(result)
					elif multiMovie:
						for i in movie:
							result = self._retrieve(base = base, value = value, movie = i, number = number, part = part, type = type, default = default, combine = combine)
							if result: results.append(result)

					if results:
						if combine:
							if Tools.isList(results[0]) or Tools.isString(results[0]): return Tools.listFlatten(results)
							else: return sum(results)
						else: return results
					return default
				else:
					key = self._key(base, provider, number, type if movie is None else None, value if (episode is None and sequential is None and movie is None and not type) else None)
					data = self._data(item = item, season = season, episode = episode, number = number, sequential = sequential, movie = movie)
					result = self._extract(data = data, key = key, default = default)

					if not part is None and result:
						if Tools.isArray(result) and Tools.isArray(result[0]): result = [i[part] if i else i for i in result]
						else: result = result[part]

					return result
		except: Logger.error()
		return default

	##############################################################################
	# LOOKUP
	##############################################################################

	# input: NumberUniversal/NumberStandard/NumberSequential/NumberAbsolute/ProviderTrakt/ProviderTmdb/ProviderTvdb/ProviderImdb
	# output: ValueIndex/NumberStandard/NumberSequential/NumberAbsolute/ProviderTrakt/ProviderTmdb/ProviderTvdb/ProviderImdb
	def lookup(self, season, episode = None, input = None, output = None):
		try:
			if not input: input = MetaPack.NumberUniversal
			if episode is None:
				result = self.mLookup.get(MetaPack.ValueSeason).get(input)
				if not season is True: result = result.get(self._lookupReverse(item = result, number = season))
			else:
				result = self.mLookup.get(MetaPack.ValueEpisode).get(input)
				if not season is True: result = result.get(self._lookupReverse(item = result, number = season))
				if not episode is True: result = result.get(self._lookupReverse(item = result, number = episode))
			if output: result = result.get(output)
			return result
		except: return None

	def lookupIndex(self, season, episode = None, input = None):
		return self.lookup(season = season, episode = episode, input = input, output = MetaPack.ValueIndex)

	def lookupStandard(self, season, episode = None, input = None):
		return self.lookup(season = season, episode = episode, input = input, output = MetaPack.NumberStandard)

	def lookupSequential(self, season, episode = None, input = None):
		return self.lookup(season = season, episode = episode, input = input, output = MetaPack.NumberSequential)

	def lookupAbsolute(self, season, episode = None, input = None):
		return self.lookup(season = season, episode = episode, input = input, output = MetaPack.NumberAbsolute)

	def lookupTrakt(self, season, episode = None, input = None):
		return self.lookup(season = season, episode = episode, input = input, output = MetaPack.ProviderTrakt)

	def lookupTmdb(self, season, episode = None, input = None):
		return self.lookup(season = season, episode = episode, input = input, output = MetaPack.ProviderTmdb)

	def lookupTvdb(self, season, episode = None, input = None):
		return self.lookup(season = season, episode = episode, input = input, output = MetaPack.ProviderTvdb)

	def lookupImdb(self, season, episode = None, input = None):
		return self.lookup(season = season, episode = episode, input = input, output = MetaPack.ProviderImdb)

	def _lookupReverse(self, item, number):
		# Reversed lookup. That is, get the last episode in the seaosn without knowing its exact number.
		# Used by MetaManager._metadataEpisodeSpecial()
		# Only works correctly for Python 3.7+, since it keeps the order of insertion into the dictionary.
		# https://stackoverflow.com/questions/71740593/retrieving-last-value-of-a-python-dictionary
		if number < 0:
			if number == -1:
				try: number = next(reversed(item)) # More efficient.
				except:
					number = 1
					Logger.error()
			else:
				try: # Less efficient.
					keys = list(item)
					try: number = keys[number]
					except: number = 1
				except: Logger.error()
		return number

	##############################################################################
	# MEDIA
	##############################################################################

	def media(self, default = None):
		return self.mMedia

	##############################################################################
	# MOVIE
	##############################################################################

	# Movie numbers start at 1, not 0.
	def movie(self, movie = False, future = False, default = None):
		try:
			if self.mPack and not movie is None:
				movies = self._extractMovies(self.mPack)
				if movies:
					if movie is False or movie is True:
						if future: return movies
						else: return [i for i in movies if i.get('released')]
					elif Tools.isArray(movie):
						result = []
						for i in movie:
							for j in movies:
								if self._extractNumber(j) == i:
									if future or j.get('released'): result.append(j)
									break
						if result: return result
					else:
						for i in movies:
							if self._extractNumber(i) == movie:
								if future or i.get('released'): return i
								break
		except: Logger.error()
		return default

	##############################################################################
	# SEASON
	##############################################################################

	def season(self, season = False, number = None, provider = None, default = None):
		try:
			if self.mPack and not season is None:
				seasons = self._extractSeasons(self.mPack)
				if seasons:
					if season is False or season is True:
						return seasons
					elif Tools.isArray(season):
						result = []
						for i in season:
							item = self._season(seasons = seasons, season = i, number = number, provider = provider)
							if item: result.append(item)
						if result: return result
					else:
						item = self._season(seasons = seasons, season = season, number = number, provider = provider)
						if item: return item
		except: Logger.error()
		return default

	def _season(self, seasons, season, number = None, provider = None, default = None):
		if number == MetaPack.NumberOfficial or number == MetaPack.NumberUnofficial or number == MetaPack.NumberSpecial: number = MetaPack.NumberStandard
		index = self.lookupIndex(season = season, input = number or provider)
		if not index is None:
			try:
				result = seasons[index]

				# Use the episode list for a specifc numbering type, since the stored JSON uses the standard order.
				# Otherwise returning a sequential/absolute season would only contain the episodes of the standard S01, instead of all episodes.
				episodes = self.mEpisode.get(number)
				if episodes:
					result = Tools.copy(result, deep = False) # Only the outer structure, since we change the 'episodes' attribute below.
					result['episodes'] = episodes

				return result
			except: Logger.error() # Should not happen.
		return None

	##############################################################################
	# EPISODE
	##############################################################################

	def episode(self, season = False, episode = False, sequential = None, number = None, provider = None, default = None, filter = False):
		try:
			# Do not use an index to access the episode: pack['seasons'][1]['episodes'][2]
			# Some shows (eg: Days of our Lives) have missing seasons.
			# Iterate and match by actual number.
			if self.mPack:
				if not sequential is None:
					season = 1
					episode = sequential

				if not season is None and not episode is None:
					seasons = self._extractSeasons(self.mPack)
					if seasons:
						if (season is False or season is True) and (episode is False or episode is True):
							result = Tools.listFlatten([self._extractEpisodes(i) for i in seasons])
							if filter: result = self._episodeFilter(episodes = result, type = number)
							return result
						elif Tools.isArray(season) or Tools.isArray(episode):
							if not Tools.isArray(episode): episode = [episode]
							result = []
							for i in season if Tools.isArray(season) else [season]:
								for j in episode:
									item = self._episode(seasons = seasons, season = i, episode = j, number = number, provider = provider)
									if item: result.extend(item) if Tools.isArray(item) else result.append(item)
							if result: return self._episodeFilter(episodes = result, type = number)
						else:
							item = self._episode(seasons = seasons, season = season, episode = episode, number = number, provider = provider)
							if item:
								if filter: item = self._episodeFilter(episodes = item, type = number)
								return item
		except: Logger.error()
		return default

	def episodeStandard(self, season = False, episode = False, sequential = None, provider = None, default = None):
		return self.episode(number = MetaPack.NumberStandard, season = season, episode = episode, sequential = sequential, provider = provider, default = default)

	def episodeSequential(self, season = False, episode = False, sequential = None, provider = None, default = None):
		return self.episode(number = MetaPack.NumberSequential, season = season, episode = episode, sequential = sequential, provider = provider, default = default)

	def episodeAbsolute(self, season = False, episode = False, sequential = None, provider = None, default = None):
		return self.episode(number = MetaPack.NumberAbsolute, season = season, episode = episode, sequential = sequential, provider = provider, default = default)

	def episodeSpecial(self, season = False, episode = False, sequential = None, provider = None, default = None):
		return self.episode(number = MetaPack.NumberSpecial, season = season, episode = episode, sequential = sequential, provider = provider, default = default)

	def _episode(self, seasons, season, episode, number = None, provider = None, default = None):
		if episode is False or episode is True:
			if number == MetaPack.NumberOfficial or number == MetaPack.NumberUnofficial or number == MetaPack.NumberSpecial:
				item = self._season(seasons = seasons, season = season)
				if item: return self._episodeFilter(episodes = self._extractEpisodes(item), type = number)
			else:
				item = self._season(seasons = seasons, season = season, number = number)
				if item: return self._extractEpisodes(item)
		else:
			if number == MetaPack.NumberOfficial or number == MetaPack.NumberUnofficial or number == MetaPack.NumberSpecial: number = MetaPack.NumberStandard
			index = self.lookupIndex(season = season, episode = episode, input = number or provider)
			if not index is None:
				try: return self._extractEpisodes(seasons[index[0]])[index[1]]
				except: Logger.error() # Should not happen.
		return default

	def _episodeFilter(self, episodes, type):
		if episodes and type:
			single = not Tools.isList(episodes)
			if single: episodes = [episodes]
			if Tools.isString(type): type = {type : True}
			result = []
			for i in episodes:
				match = True
				types = i.get('type', {})
				for k, v in type.items():
					if not v == types.get(k):
						match = False
						break
				if match: result.append(i)
			if single: episodes = result[0] if result else None
			else: episodes = result
		return episodes

	##############################################################################
	# COUNT
	##############################################################################

	def count(self, season = None, item = None, number = None, type = None, fallback = False, default = 0, combine = True):
		try:
			if self.mShow:
				if type is None and season is None and item is None: type = MetaPack.ValueEpisode
				if number is None: number = MetaPack.NumberStandard
			count = self._retrieve(base = 'count', season = season, item = item, number = type, type = number, combine = combine) # Switch number and type.
			if count: return count

			if fallback and self.mShow: return self.count(item = item, number = number, type = MetaPack.ValueMean, default = default, fallback = False, combine = combine)
		except: Logger.error()
		return default

	def countOfficial(self, season = None, item = None, type = None, fallback = False, default = 0, combine = True):
		return self.count(number = MetaPack.NumberOfficial, season = season, item = item, type = type, fallback = fallback, default = default, combine = combine)

	def countUnofficial(self, season = None, item = None, type = None, fallback = False, default = 0, combine = True):
		return self.count(number = MetaPack.NumberUnofficial, season = season, item = item, type = type, fallback = fallback, default = default, combine = combine)

	def countUniversal(self, season = None, item = None, type = None, fallback = False, default = 0, combine = True):
		return self.count(number = MetaPack.NumberUniversal, season = season, item = item, type = type, fallback = fallback, default = default, combine = combine)

	def countStandard(self, season = None, item = None, type = None, fallback = False, default = 0, combine = True):
		return self.count(number = MetaPack.NumberStandard, season = season, item = item, type = type, fallback = fallback, default = default, combine = combine)

	def countSequential(self, season = None, item = None, type = None, fallback = False, default = 0, combine = True):
		return self.count(number = MetaPack.NumberSequential, season = season, item = item, type = type, fallback = fallback, default = default, combine = combine)

	def countAbsolute(self, season = None, item = None, type = None, fallback = False, default = 0, combine = True):
		return self.count(number = MetaPack.NumberAbsolute, season = season, item = item, type = type, fallback = fallback, default = default, combine = combine)

	def countSpecial(self, season = None, item = None, type = None, fallback = False, default = 0, combine = True):
		return self.count(number = MetaPack.NumberSpecial, season = season, item = item, type = type, fallback = fallback, default = default, combine = combine)

	def countSeason(self, item = None, number = None, default = 0, fallback = False, combine = True):
		return self.count(type = MetaPack.ValueSeason, item = item, number = number, default = default, fallback = fallback, combine = combine)

	def countSeasonOfficial(self, item = None, default = 0, fallback = False, combine = True):
		return self.countSeason(number = MetaPack.NumberOfficial, item = item, default = default, fallback = fallback, combine = combine)

	def countSeasonUnofficial(self, item = None, default = 0, fallback = False, combine = True):
		return self.countSeason(number = MetaPack.NumberUnofficial, item = item, default = default, fallback = fallback, combine = combine)

	def countSeasonUniversal(self, item = None, default = 0, fallback = False, combine = True):
		return self.countSeason(number = MetaPack.NumberUniversal, item = item, default = default, fallback = fallback, combine = combine)

	def countSeasonStandard(self, item = None, default = 0, fallback = False, combine = True):
		return self.countSeason(number = MetaPack.NumberStandard, item = item, default = default, fallback = fallback, combine = combine)

	def countSeasonSequential(self, item = None, default = 0, fallback = False, combine = True):
		return self.countSeason(number = MetaPack.NumberSequential, item = item, default = default, fallback = fallback, combine = combine)

	def countSeasonAbsolute(self, item = None, default = 0, fallback = False, combine = True):
		return self.countSeason(number = MetaPack.NumberAbsolute, item = item, default = default, fallback = fallback, combine = combine)

	def countSeasonSpecial(self, item = None, default = 0, fallback = False, combine = True):
		return self.countSeason(number = MetaPack.NumberSpecial, item = item, default = default, fallback = fallback, combine = combine)

	def countSeasonTotal(self, item = None, default = 0, fallback = False, combine = True):
		return self.countSeason(number = MetaPack.ValueTotal, item = item, default = default, fallback = fallback, combine = combine)

	def countEpisode(self, season = None, item = None, number = None, default = 0, fallback = False, combine = True):
		return self.count(season = season, item = item, number = number, default = default, fallback = fallback, combine = combine)

	def countEpisodeOfficial(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countEpisode(number = MetaPack.NumberOfficial, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countEpisodeUnofficial(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countEpisode(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countEpisodeUniversal(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countEpisode(number = MetaPack.NumberUniversal, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countEpisodeStandard(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countEpisode(number = MetaPack.NumberStandard, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countEpisodeSequential(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countEpisode(number = MetaPack.NumberSequential, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countEpisodeAbsolute(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countEpisode(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countEpisodeSpecial(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countEpisode(number = MetaPack.NumberSpecial, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countEpisodeTotal(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countEpisode(number = MetaPack.ValueTotal, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countMean(self, season = None, item = None, number = None, default = 0, fallback = False, combine = True):
		return self.count(type = MetaPack.ValueMean, season = season, item = item, number = number, default = default, fallback = fallback, combine = combine)

	def countMeanOfficial(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countMean(number = MetaPack.NumberOfficial, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countMeanUnofficial(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countMean(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countMeanUniversal(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countMean(number = MetaPack.NumberUniversal, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countMeanStandard(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countMean(number = MetaPack.NumberStandard, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countMeanSequential(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countMean(number = MetaPack.NumberSequential, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countMeanAbsolute(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countMean(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countMeanSpecial(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countMean(number = MetaPack.NumberSpecial, season = season, item = item, default = default, fallback = fallback, combine = combine)

	def countMeanTotal(self, season = None, item = None, default = 0, fallback = False, combine = True):
		return self.countMean(number = MetaPack.ValueTotal, season = season, item = item, default = default, fallback = fallback, combine = combine)

	##############################################################################
	# NUMBER
	##############################################################################

	def number(self, season = None, episode = None, sequential = None, movie = None, item = None, number = None, part = None, provider = None, default = None, combine = True):
		try:
			if number is None and not self.mMovie: number = MetaPack.NumberStandard
			elif number is False: number = None # Retrieve entire number dictionary.
			return self._retrieve(base = 'number', season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, part = part, provider = provider, default = default, combine = combine)
		except: Logger.error()
		return default

	def numberStandard(self, season = None, episode = None, sequential = None, item = None, part = None, provider = None, default = None, combine = True):
		return self.number(number = MetaPack.NumberStandard, season = season, episode = episode, sequential = sequential, item = item, part = part, provider = provider, default = default, combine = combine)

	def numberStandardSeason(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberStandard(part = MetaPack.PartSeason, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberStandardEpisode(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberStandard(part = MetaPack.PartEpisode, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberSequential(self, season = None, episode = None, sequential = None, item = None, part = None, provider = None, default = None, combine = True):
		return self.number(number = MetaPack.NumberSequential, season = season, episode = episode, sequential = sequential, item = item, part = part, provider = provider, default = default, combine = combine)

	def numberSequentialSeason(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberSequential(part = MetaPack.PartSeason, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberSequentialEpisode(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberSequential(part = MetaPack.PartEpisode, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberAbsolute(self, season = None, episode = None, sequential = None, item = None, part = None, provider = None, default = None, combine = True):
		return self.number(number = MetaPack.NumberAbsolute, season = season, episode = episode, sequential = sequential, item = item, part = part, provider = provider, default = default, combine = combine)

	def numberAbsoluteSeason(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberAbsolute(part = MetaPack.PartSeason, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberAbsoluteEpisode(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberAbsolute(part = MetaPack.PartEpisode, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberSpecial(self, season = None, episode = None, sequential = None, item = None, part = None, provider = None, default = None, combine = True):
		return self.number(number = MetaPack.NumberSpecial, season = season, episode = episode, sequential = sequential, item = item, part = part, provider = provider, default = default, combine = combine)

	def numberSpecialSeason(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberSpecial(part = MetaPack.PartSeason, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberSpecialEpisode(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberSpecial(part = MetaPack.PartEpisode, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberSeason(self, season = None, episode = None, sequential = None, movie = None, item = None, number = None, provider = None, default = None, combine = True):
		return self.number(part = MetaPack.PartSeason, season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, provider = provider, default = default, combine = combine)

	def numberEpisode(self, season = None, episode = None, sequential = None, movie = None, item = None, number = None, provider = None, default = None, combine = True):
		return self.number(part = MetaPack.PartEpisode, season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, provider = provider, default = default, combine = combine)

	def numberLast(self, season = True, number = None, part = None, provider = None, type = None, default = None, release = False, combine = True):
		try:
			if number == MetaPack.NumberSpecial:
				if season is None:
					items = self.episode(season = 0, number = number, filter = False)
				else:
					items = self.season(season = 0, number = number)
					items = [items] if items else None
				number = MetaPack.NumberStandard
			else:
				if season is None: items = self.season()
				else: items = self.episode(season = season, number = number, filter = False)
			if items:
				if type or release:
					time = Time.timestamp()
					end = 9999999999
					for item in reversed(items):
						# NB: Also check time, not just status. In case the pack was not updated in a while, the status might be outdated compared to the current time.
						if (not type or self._extractType(item, type)) and (not release or item.get('status') == MetaPack.StatusEnded or (item.get('time') or end) < time):
							return self.number(item = item, number = number, part = part, provider = provider, default = default, combine = combine)
				else:
					return self.number(item = items[-1], number = number, part = part, provider = provider, default = default, combine = combine)
		except: Logger.error()
		return default

	def numberLastSeason(self, season = True, number = None, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLast(part = MetaPack.PartSeason, season = True if season is None else season, number = number, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastEpisode(self, season = True, number = None, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLast(part = MetaPack.PartEpisode, season = season, number = number, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastOfficial(self, season = True, part = None, provider = None, default = None, release = False, combine = True):
		return self.numberLast(number = MetaPack.NumberStandard, type = MetaPack.NumberOfficial, season = season, part = part, provider = provider,  default = default, release = release, combine = combine)

	def numberLastOfficialSeason(self, season = True, provider = None, default = None, release = False, combine = True):
		return self.numberLastOfficial(part = MetaPack.PartSeason, season = season, provider = provider, default = default, release = release, combine = combine)

	def numberLastOfficialEpisode(self, season = True, provider = None, default = None, release = False, combine = True):
		return self.numberLastOfficial(part = MetaPack.PartEpisode, season = season, provider = provider, default = default, release = release, combine = combine)

	def numberLastUnofficial(self, season = True, part = None, provider = None, default = None, release = False, combine = True):
		return self.numberLast(number = MetaPack.NumberStandard, type = MetaPack.NumberUnofficial, season = season, part = part, provider = provider,  default = default, release = release, combine = combine)

	def numberLastUnofficialSeason(self, season = True, provider = None, default = None, release = False, combine = True):
		return self.numberLastUnofficial(part = MetaPack.PartSeason, season = season, provider = provider, default = default, release = release, combine = combine)

	def numberLastUnofficialEpisode(self, season = True, provider = None, default = None, release = False, combine = True):
		return self.numberLastUnofficial(part = MetaPack.PartEpisode, season = season, provider = provider, default = default, release = release, combine = combine)

	def numberLastUniversal(self, season = True, part = None, provider = None, default = None, release = False, combine = True):
		return self.numberLast(number = MetaPack.NumberStandard, type = MetaPack.NumberUniversal, season = season, part = part, provider = provider,  default = default, release = release, combine = combine)

	def numberLastUniversalSeason(self, season = True, provider = None, default = None, release = False, combine = True):
		return self.numberLastUniversal(part = MetaPack.PartSeason, season = season, provider = provider, default = default, release = release, combine = combine)

	def numberLastUniversalEpisode(self, season = True, provider = None, default = None, release = False, combine = True):
		return self.numberLastUniversal(part = MetaPack.PartEpisode, season = season, provider = provider, default = default, release = release, combine = combine)

	def numberLastStandard(self, season = True, part = None, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLast(number = MetaPack.NumberStandard, season = season, part = part, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastStandardSeason(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastStandard(part = MetaPack.PartSeason, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastStandardEpisode(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastStandard(part = MetaPack.PartEpisode, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastSequential(self, season = True, part = None, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLast(number = MetaPack.NumberSequential, season = season, part = part, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastSequentialSeason(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastSequential(part = MetaPack.PartSeason, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastSequentialEpisode(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastSequential(part = MetaPack.PartEpisode, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastAbsolute(self, season = True, part = None, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLast(number = MetaPack.NumberAbsolute, season = season, part = part, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastAbsoluteSeason(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastAbsolute(part = MetaPack.PartSeason, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastAbsoluteEpisode(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastAbsolute(part = MetaPack.PartEpisode, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastSpecial(self, season = True, part = None, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLast(number = MetaPack.NumberSpecial, season = season, part = part, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastSpecialSeason(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastSpecial(part = MetaPack.PartSeason, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastSpecialEpisode(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastSpecial(part = MetaPack.PartEpisode, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

	##############################################################################
	# YEAR
	##############################################################################

	def year(self, season = None, episode = None, sequential = None, movie = None, item = None, number = None, type = None, default = None, combine = True):
		try: return self._retrieve(base = 'year', value = MetaPack.ValueValues, season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, type = type, default = default, combine = combine)
		except: Logger.error()
		return default

	def yearOfficial(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.year(number = MetaPack.NumberOfficial, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def yearUnofficial(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.year(number = MetaPack.NumberUnofficial, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def yearUniversal(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.year(number = MetaPack.NumberUniversal, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def yearStandard(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.year(number = MetaPack.NumberStandard, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def yearSequential(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.year(number = MetaPack.NumberSequential, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def yearAbsolute(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.year(number = MetaPack.NumberAbsolute, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def yearSpecial(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.year(number = MetaPack.NumberSpecial, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def yearMinimum(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._minimum(value = self.year(type = MetaPack.ValueMinimum, season = season, movie = movie, item = item, number = number, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def yearMinimumOfficial(self, season = None, item = None, default = None, combine = True):
		return self.yearMinimum(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def yearMinimumUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.yearMinimum(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def yearMinimumUniversal(self, season = None, item = None, default = None, combine = True):
		return self.yearMinimum(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def yearMinimumStandard(self, season = None, item = None, default = None, combine = True):
		return self.yearMinimum(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def yearMinimumSequential(self, season = None, item = None, default = None, combine = True):
		return self.yearMinimum(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def yearMinimumAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.yearMinimum(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def yearMinimumSpecial(self, season = None, item = None, default = None, combine = True):
		return self.yearMinimum(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def yearMaximum(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._maximum(value = self.year(type = MetaPack.ValueMaximum, season = season, movie = movie, item = item, number = number, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def yearMaximumOfficial(self, season = None, item = None, default = None, combine = True):
		return self.yearMaximum(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def yearMaximumUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.yearMaximum(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def yearMaximumUniversal(self, season = None, item = None, default = None, combine = True):
		return self.yearMaximum(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def yearMaximumStandard(self, season = None, item = None, default = None, combine = True):
		return self.yearMaximum(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def yearMaximumSequential(self, season = None, item = None, default = None, combine = True):
		return self.yearMaximum(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def yearMaximumAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.yearMaximum(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def yearMaximumSpecial(self, season = None, item = None, default = None, combine = True):
		return self.yearMaximum(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def yearRange(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._range(minimum = self.yearMinimum(season = season, movie = movie, item = item, number = number, combine = False), maximum = self.yearMaximum(season = season, movie = movie, item = item, number = number, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def yearRangeOfficial(self, season = None, item = None, default = None, combine = True):
		return self.yearRange(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def yearRangeUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.yearRange(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def yearRangeUniversal(self, season = None, item = None, default = None, combine = True):
		return self.yearRange(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def yearRangeStandard(self, season = None, item = None, default = None, combine = True):
		return self.yearRange(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def yearRangeSequential(self, season = None, item = None, default = None, combine = True):
		return self.yearRange(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def yearRangeAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.yearRange(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def yearRangeSpecial(self, season = None, item = None, default = None, combine = True):
		return self.yearRange(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def yearValues(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self.year(type = MetaPack.ValueValues, season = season, movie = movie, item = item, number = number, default = default, combine = combine)
		except: Logger.error()
		return default

	def yearValuesOfficial(self, season = None, item = None, default = None, combine = True):
		return self.yearValues(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def yearValuesUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.yearValues(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def yearValuesUniversal(self, season = None, item = None, default = None, combine = True):
		return self.yearValues(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def yearValuesStandard(self, season = None, item = None, default = None, combine = True):
		return self.yearValues(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def yearValuesSequential(self, season = None, item = None, default = None, combine = True):
		return self.yearValues(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def yearValuesAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.yearValues(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def yearValuesSpecial(self, season = None, item = None, default = None, combine = True):
		return self.yearValues(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	##############################################################################
	# TIME
	##############################################################################

	def time(self, season = None, episode = None, sequential = None, movie = None, item = None, number = None, type = None, default = None, combine = True):
		try: return self._retrieve(base = 'time', value = MetaPack.ValueValues, season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, type = type, default = default, combine = combine)
		except: Logger.error()
		return default

	def timeOfficial(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.time(number = MetaPack.NumberOfficial, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def timeUnofficial(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.time(number = MetaPack.NumberUnofficial, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def timeUniversal(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.time(number = MetaPack.NumberUniversal, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def timeStandard(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.time(number = MetaPack.NumberStandard, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def timeSequential(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.time(number = MetaPack.NumberSequential, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def timeAbsolute(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.time(number = MetaPack.NumberAbsolute, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def timeSpecial(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.time(number = MetaPack.NumberSpecial, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def timeMinimum(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._minimum(value = self.time(season = season, movie = movie, item = item, number = number, type = MetaPack.ValueMinimum, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def timeMinimumOfficial(self, season = None, item = None, default = None, combine = True):
		return self.timeMinimum(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def timeMinimumUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.timeMinimum(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def timeMinimumUniversal(self, season = None, item = None, default = None, combine = True):
		return self.timeMinimum(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def timeMinimumStandard(self, season = None, item = None, default = None, combine = True):
		return self.timeMinimum(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def timeMinimumSequential(self, season = None, item = None, default = None, combine = True):
		return self.timeMinimum(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def timeMinimumAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.timeMinimum(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def timeMinimumSpecial(self, season = None, item = None, default = None, combine = True):
		return self.timeMinimum(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def timeMaximum(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._maximum(value = self.time(season = season, movie = movie, item = item, number = number, type = MetaPack.ValueMaximum, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def timeMaximumOfficial(self, season = None, item = None, default = None, combine = True):
		return self.timeMaximum(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def timeMaximumUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.timeMaximum(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def timeMaximumUniversal(self, season = None, item = None, default = None, combine = True):
		return self.timeMaximum(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def timeMaximumStandard(self, season = None, item = None, default = None, combine = True):
		return self.timeMaximum(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def timeMaximumSequential(self, season = None, item = None, default = None, combine = True):
		return self.timeMaximum(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def timeMaximumAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.timeMaximum(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def timeMaximumSpecial(self, season = None, item = None, default = None, combine = True):
		return self.timeMaximum(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def timeRange(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._range(minimum = self.timeMinimum(season = season, movie = movie, item = item, number = number, combine = False), maximum = self.timeMaximum(season = season, movie = movie, item = item, number = number, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def timeRangeOfficial(self, season = None, item = None, default = None, combine = True):
		return self.timeRange(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def timeRangeUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.timeRange(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def timeRangeUniversal(self, season = None, item = None, default = None, combine = True):
		return self.timeRange(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def timeRangeStandard(self, season = None, item = None, default = None, combine = True):
		return self.timeRange(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def timeRangeSequential(self, season = None, item = None, default = None, combine = True):
		return self.timeRange(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def timeRangeAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.timeRange(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def timeRangeSpecial(self, season = None, item = None, default = None, combine = True):
		return self.timeRange(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def timeValues(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self.time(season = season, movie = movie, item = item, number = number, type = MetaPack.ValueValues, default = default, combine = combine)
		except: Logger.error()
		return default

	def timeValuesOfficial(self, season = None, item = None, default = None, combine = True):
		return self.timeValues(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def timeValuesUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.timeValues(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def timeValuesUniversal(self, season = None, item = None, default = None, combine = True):
		return self.timeValues(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def timeValuesStandard(self, season = None, item = None, default = None, combine = True):
		return self.timeValues(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def timeValuesSequential(self, season = None, item = None, default = None, combine = True):
		return self.timeValues(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def timeValuesAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.timeValues(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def timeValuesSpecial(self, season = None, item = None, default = None, combine = True):
		return self.timeValues(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	##############################################################################
	# DURATION
	##############################################################################

	def duration(self, season = None, episode = None, sequential = None, movie = None, item = None, number = None, type = None, default = None, combine = True):
		try: return self._retrieve(base = 'duration', value = MetaPack.ValueMean, season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, type = type, default = default, combine = combine)
		except: Logger.error()
		return default

	def durationOfficial(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.duration(number = MetaPack.NumberOfficial, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def durationUnofficial(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.duration(number = MetaPack.NumberUnofficial, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def durationUniversal(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.duration(number = MetaPack.NumberUniversal, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def durationStandard(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.duration(number = MetaPack.NumberStandard, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def durationSequential(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.duration(number = MetaPack.NumberSequential, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def durationAbsolute(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.duration(number = MetaPack.NumberAbsolute, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def durationSpecial(self, season = None, episode = None, sequential = None, item = None, type = None, default = None, combine = True):
		return self.duration(number = MetaPack.NumberSpecial, season = season, episode = episode, sequential = sequential, item = item, type = type, default = default, combine = combine)

	def durationTotal(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self.duration(season = season, movie = movie, item = item, number = number, type = MetaPack.ValueTotal, default = default, combine = combine)
		except: Logger.error()
		return default

	def durationTotalOfficial(self, season = None, item = None, default = None, combine = True):
		return self.durationTotal(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def durationTotalUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.durationTotal(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def durationTotalUniversal(self, season = None, item = None, default = None, combine = True):
		return self.durationTotal(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def durationTotalStandard(self, season = None, item = None, default = None, combine = True):
		return self.durationTotal(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def durationTotalSequential(self, season = None, item = None, default = None, combine = True):
		return self.durationTotal(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def durationTotalAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.durationTotal(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def durationTotalSpecial(self, season = None, item = None, default = None, combine = True):
		return self.durationTotal(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def durationMean(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._mean(self.duration(season = season, movie = movie, item = item, number = number, type = MetaPack.ValueMean, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def durationMeanOfficial(self, season = None, item = None, default = None, combine = True):
		return self.durationMean(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def durationMeanUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.durationMean(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def durationMeanUniversal(self, season = None, item = None, default = None, combine = True):
		return self.durationMean(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def durationMeanStandard(self, season = None, item = None, default = None, combine = True):
		return self.durationMean(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def durationMeanSequential(self, season = None, item = None, default = None, combine = True):
		return self.durationMean(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def durationMeanAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.durationMean(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def durationMeanSpecial(self, season = None, item = None, default = None, combine = True):
		return self.durationMean(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def durationMinimum(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._minimum(value = self.duration(season = season, movie = movie, item = item, number = number, type = MetaPack.ValueMinimum, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def durationMinimumOfficial(self, season = None, item = None, default = None, combine = True):
		return self.durationMinimum(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def durationMinimumUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.durationMinimum(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def durationMinimumUniversal(self, season = None, item = None, default = None, combine = True):
		return self.durationMinimum(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def durationMinimumStandard(self, season = None, item = None, default = None, combine = True):
		return self.durationMinimum(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def durationMinimumSequential(self, season = None, item = None, default = None, combine = True):
		return self.durationMinimum(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def durationMinimumAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.durationMinimum(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def durationMinimumSpecial(self, season = None, item = None, default = None, combine = True):
		return self.durationMinimum(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def durationMaximum(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._maximum(value = self.duration(season = season, movie = movie, item = item, number = number, type = MetaPack.ValueMaximum, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def durationMaximumOfficial(self, season = None, item = None, default = None, combine = True):
		return self.durationMaximum(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def durationMaximumUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.durationMaximum(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def durationMaximumUniversal(self, season = None, item = None, default = None, combine = True):
		return self.durationMaximum(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def durationMaximumStandard(self, season = None, item = None, default = None, combine = True):
		return self.durationMaximum(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def durationMaximumSequential(self, season = None, item = None, default = None, combine = True):
		return self.durationMaximum(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def durationMaximumAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.durationMaximum(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def durationMaximumSpecial(self, season = None, item = None, default = None, combine = True):
		return self.durationMaximum(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	def durationRange(self, season = None, movie = None, item = None, number = None, default = None, combine = True):
		try: return self._range(minimum = self.durationMinimum(season = season, movie = movie, item = item, number = number, combine = False), maximum = self.durationMaximum(season = season, movie = movie, item = item, number = number, combine = False), default = default, combine = combine)
		except: Logger.error()
		return default

	def durationRangeOfficial(self, season = None, item = None, default = None, combine = True):
		return self.durationRange(number = MetaPack.NumberOfficial, season = season, item = item, default = default, combine = combine)

	def durationRangeUnofficial(self, season = None, item = None, default = None, combine = True):
		return self.durationRange(number = MetaPack.NumberUnofficial, season = season, item = item, default = default, combine = combine)

	def durationRangeUniversal(self, season = None, item = None, default = None, combine = True):
		return self.durationRange(number = MetaPack.NumberUniversal, season = season, item = item, default = default, combine = combine)

	def durationRangeStandard(self, season = None, item = None, default = None, combine = True):
		return self.durationRange(number = MetaPack.NumberStandard, season = season, item = item, default = default, combine = combine)

	def durationRangeSequential(self, season = None, item = None, default = None, combine = True):
		return self.durationRange(number = MetaPack.NumberSequential, season = season, item = item, default = default, combine = combine)

	def durationRangeAbsolute(self, season = None, item = None, default = None, combine = True):
		return self.durationRange(number = MetaPack.NumberAbsolute, season = season, item = item, default = default, combine = combine)

	def durationRangeSpecial(self, season = None, item = None, default = None, combine = True):
		return self.durationRange(number = MetaPack.NumberSpecial, season = season, item = item, default = default, combine = combine)

	##############################################################################
	# TYPE
	##############################################################################

	def type(self, season = None, episode = None, sequential = None, item = None, type = None, default = None):
		try: return self._retrieve(base = 'type', season = season, episode = episode, sequential = sequential, item = item, type = type, default = default)
		except: Logger.error()
		return default

	def typeOfficial(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = MetaPack.NumberOfficial, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeUnofficial(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = MetaPack.NumberUnofficial, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeUniversal(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = MetaPack.NumberUniversal, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeStandard(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = MetaPack.NumberStandard, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeSequential(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = MetaPack.NumberSequential, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeAbsolute(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = MetaPack.NumberAbsolute, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeSpecial(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = MetaPack.NumberSpecial, season = season, episode = episode, sequential = sequential, item = item, default = default)

	##############################################################################
	# ID
	##############################################################################

	def id(self, season = None, episode = None, sequential = None, movie = None, item = None, provider = None, default = None, combine = True):
		try:
			return self._retrieve(base = 'id', season = season, episode = episode, sequential = sequential, movie = movie, item = item, provider = provider, default = default, combine = combine)
		except: Logger.error()
		return default

	##############################################################################
	# TITLE
	##############################################################################

	def title(self, season = None, episode = None, sequential = None, movie = None, item = None, number = None, type = None, default = None, combine = True, flatten = False):
		try:
			result = self._retrieve(base = 'title', season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, type = type, default = default, combine = combine)
			if flatten and result: result = Tools.listFlatten(result)
			return result
		except: Logger.error()
		return default

	##############################################################################
	# STATUS
	##############################################################################

	def status(self, season = None, episode = None, sequential = None, movie = None, item = None, default = None):
		try: return self._retrieve(base = 'status', season = season, episode = episode, sequential = sequential, movie = movie, item = item, default = default)
		except: Logger.error()
		return default

	##############################################################################
	# SUPPORT
	##############################################################################

	def support(self, season = None, episode = None, sequential = None, item = None, default = None):
		try: return self._retrieve(base = 'support', season = season, episode = episode, sequential = sequential, item = item, default = default)
		except: Logger.error()
		return default
