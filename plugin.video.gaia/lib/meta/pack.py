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
from lib.modules.concurrency import Pool, Lock

class MetaPack(object):

	# PROVIDER

	ProviderImdb				= 'imdb'
	ProviderTmdb				= 'tmdb'
	ProviderTvdb				= 'tvdb'
	ProviderTrakt				= 'trakt'
	Providers					= [ProviderTrakt, ProviderTvdb, ProviderTmdb, ProviderImdb] # Order matters for quicker processing in this class.

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
	NumberDate					= 'date'			# Episodes are numbered by date YYYYMMDD. Used for daily and late-night shows.
	NumberSpecial				= 'special'			# Special episodes, such as Christmas Specials, that are added as an additional episode to the end of the season. This is mostly done by IMDb (eg: Downton Abbey S05E09), whereas Trakt/TMDb/TVDb typically put these into the specials season S00. Eg: the season runs officially until S02E10, but there is an extra special episode S02E11, which should actually be S00E27.

	NumberOfficial				= 'official'		# Internal. Not used as a number, but used as a type to indicate an episode is part of the official seasons using a official numbering, typically that of Trakt.
	NumberUnofficial			= 'unofficial'		# Internal. Not used as a number, but used as a type to indicate an episode is not part of the official seasons, typically non-Trakt episodes or other specials.
	NumberUniversal				= 'universal'		# Internal. All standard episodes, specials, and sequential episodes in one lookup table. Hence, we can retrieve any standard/special/sequential episode with the same lookup table. Also used as a type to indicate an episode is is shared among all providers, that is all providers (except IMDb) have the episode in the same season and the episode number or ID matches.
	NumberSerie					= 'serie'			# Internal. For constructing Series menus.
	NumberCustom				= 'custom'			# Internal. For Trakt which sometimes uses season-based seasons, but within each season use the absolute episode number (eg: One Piece).
	NumberAutomatic				= 'automatic'		# Internal. Sequential episodes that were added automatically to allow lookups of the real episode number, using the sequential number. However, these episodes do not have metadata on any of the providers and are not considered real sequential episodes, and just point to one of the standard episodes.

	# PART

	PartSeason					= 0					# The index of the season number in the episode's number list.
	PartEpisode					= 1					# The index of the episode number in the episode's number list.

	# INTERVAL
	IntervalWeekly				= Media.Weekly		# One episode released per week. Some weeks might not have a release (eg public holidays) and some weeks might have multiple releases (eg double finales).
	IntervalDaily				= Media.Daily		# One episode released per weekday. Some days might not have a release (eg public holidays) and some weeks might have multiple releases (eg specials during certain events).
	IntervalInstantly			= Media.Instantly	# All episodes of a season are released at once.
	IntervalQuickly				= Media.Quickly		# All episodes of a season are almost released at once, over just a few days.
	IntervalBatchly				= Media.Batchly		# Seasons are divided into smaller subgroups and all episodes within a group are released at once.
	IntervalOtherly				= Media.Otherly		# Other types of releases.

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
	StatusPiloted				= 'piloted'
	StatusUpcoming				= 'upcoming'
	StatusContinuing			= 'continuing'
	StatusReturning				= 'returning'
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
	ValueIncorrect				= 'incorrect'

	CheckInstant				= None				# Process instantly without sleeping at all.
	CheckForeground				= 'foreground'		# Process quickly by having very short sleeps during generation.
	CheckBackground				= 'background'		# Process slowly by having longer sleeps during generation.
	CheckDefault				= CheckForeground

	# Choosing the correct limits and delays is important.
	#	To test these values, start an invoker with two threads, each generating a large pack.
	#	While the pack generation is running, start a second invoker by opening a media menu and check how long it takes to load the menu.
	#	Example: Pokemon + One Piece (this is used as example for the measurnments below).
	# CheckForeground
	#	Example: opening a show menu for the first time, so that the show's pack is generated.
	#	Limit: Do not make the limit too low, otherwise the check function is called too often and even with a small delay, it can drastically slow down generation.
	#	Delay: Use a very short delay in order not to hold up the foreground process. Only delay for long enough so that Python can switch to another thread.
	# CheckBackground
	#
	#	[True, False, True]:	Pack-generation: 36-38 secs		|	Menu-loading: 10-13 secs
	#
	#	[5000, 0.001, True]:	Pack-generation: 37-39 secs		|	Menu-loading: 5.0-6.5 secs
	#	[5000, 0.01, True]:		Pack-generation: 38-43 secs		|	Menu-loading: 2.0-2.5 secs
	#	[5000, 0.02, True]:		Pack-generation: 50-51 secs		|	Menu-loading: 1.3-1.9 secs
	#	[5000, 0.05, True]:		Pack-generation: 66-68 secs		|	Menu-loading: 0.7-0.9 secs
	#	[5000, 0.1, True]:		Pack-generation: 99-100 secs	|	Menu-loading: 0.5-0.7 secs
	#
	#	[10000, 0.001, True]:	Pack-generation: 37-39 secs		|	Menu-loading: 5.0-7.5 secs
	#	[10000, 0.01, True]:	Pack-generation: 36-38 secs		|	Menu-loading: 2.5-4.0 secs
	#	[10000, 0.02, True]:	Pack-generation: 45-46 secs		|	Menu-loading: 1.5-2.1 secs
	#	[10000, 0.05, True]:	Pack-generation: 54-57 secs		|	Menu-loading: 1.0-1.5 secs
	#	[10000, 0.1, True]:		Pack-generation: 76-77 secs		|	Menu-loading: 0.7-0.8 secs
	#
	#	[15000, 0.001, True]:	Pack-generation: 37-39 secs		|	Menu-loading: 7.5-8.5 secs
	#	[15000, 0.01, True]:	Pack-generation: 35-38 secs		|	Menu-loading: 3.0-4.0 secs
	#	[15000, 0.02, True]:	Pack-generation: 43-45 secs		|	Menu-loading: 1.8-2.5 secs
	#	[15000, 0.05, True]:	Pack-generation: 49-51 secs		|	Menu-loading: 1.0-1.5 secs
	#	[15000, 0.1, True]:		Pack-generation: 68-70 secs		|	Menu-loading: 0.7-0.9 secs
	#
	#	[20000, 0.001, True]:	Pack-generation: 37-39 secs		|	Menu-loading: 7.0-8.5 secs
	#	[20000, 0.01, True]:	Pack-generation: 38-39 secs		|	Menu-loading: 3.0-4.5 secs
	#	[20000, 0.02, True]:	Pack-generation: 40-42 secs		|	Menu-loading: 2.3-3.0 secs
	#	[20000, 0.05, True]:	Pack-generation: 45-50 secs		|	Menu-loading: 1.0-1.7 secs
	#	[20000, 0.1, True]:		Pack-generation: 60-63 secs		|	Menu-loading: 1.0-1.2 secs
	#
	#	[25000, 0.001, True]:	Pack-generation: 37-39 secs		|	Menu-loading: 8.0-9.5 secs
	#	[25000, 0.01, True]:	Pack-generation: 38-39 secs		|	Menu-loading: 3.9-4.4 secs
	#	[25000, 0.02, True]:	Pack-generation: 40-41 secs		|	Menu-loading: 2.5-3.5 secs
	#	[25000, 0.05, True]:	Pack-generation: 47-48 secs		|	Menu-loading: 1.5-1.7 secs
	#	[20000, 0.1, True]:		Pack-generation: 58-60 secs		|	Menu-loading: 1.1-1.3 secs
	#
	#	[10000, 0.001, False]:	Pack-generation: 37-39 secs		|	Menu-loading: 7.5-9.0 secs
	#	[10000, 0.01, False]:	Pack-generation: 41-42 secs		|	Menu-loading: 2.5-3.5 secs
	#	[10000, 0.05, False]:	Pack-generation: 59-61 secs		|	Menu-loading: 0.9-1.1 secs
	#	[10000, 0.1, False]:	Pack-generation: 81-82 secs		|	Menu-loading: 0.7-0.9 secs

	CheckConfig					= {CheckInstant : {'limit' : True, 'delay' : False, 'lock' : False}, CheckForeground : {'limit' : 10000, 'delay' : Pool.DelayQuick, 'lock' : False}, CheckBackground : {'limit' : 10000, 'delay' : Pool.DelayMedium, 'lock' : True}}

	ThresholdSequential			= 20		# 30 is too much for "Good times, bad times" S25 + S27.
	ThresholdYear				= 1900

	Identifier					= 'packifier'
	Lock						= Lock()
	Expressions					= None
	Roman						= None
	Instance					= {}

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, pack = None):
		self.mMatchDetail = {}
		self.mMatchExact = {}
		self.mLookup = {}
		self.mEpisode = {}
		self.mLast = {}
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
		try:
			if self.instanceIs(pack = pack, dictionary = False): return pack

			id = self.instanceId(pack = pack)
			if not id: return MetaPack(pack = pack)

			instance = MetaPack.Instance.get(id)
			if not instance:
				# Lock until the item was inserted, in case mutiple calls are made to this function at the same time for the same pack.
				MetaPack.Lock.acquire()

				# Check again after the lock was acquired, in case it was inserted in the meantime.
				instance = MetaPack.Instance.get(id)
				if not instance: instance = MetaPack.Instance[id] = MetaPack(pack = pack)

				MetaPack.Lock.release()

			return instance
		except: Logger.error()
		return None

	@classmethod
	def instanceIs(self, pack, dictionary = True):
		if Tools.isInstance(pack, MetaPack): return True
		if dictionary and Tools.isDictionary(pack) and ('seasons' in pack or 'movies' in pack): return True
		return False

	@classmethod
	def instanceId(self, pack, update = False):
		if pack is None: return None

		# Update (2025-11):
		# Previously we used the memory ID pointing to the dict in memory to identify packs.
		# This ensure the same pack has to only be (costly) initialized once, and subsequent use of the pack can just retrieve the already-initialized object from memory.
		# This solution is robust, but has one major disadvantage:
		# The pack dict cannot be copied (including shallow-copied), since this would create a new dict, which has a different memory ID.
		# Previously the pack metadata was not shallow-copied in MetaCache._memory() like the other metadata for efficiency reasons.
		# This made sure the same dict is returned from MetaCache._memory() on different calls, which would therefore have the same ID here and only have a single pack initialization.
		# However, the nested MetaCache.Attrribute dict is still changed when retrieving from MetaCache memory, which therefore updates the attribute in the same dict which was retrieved previously by another caller.
		# This then causes a variety of issues in MetaManager:
		#	1. MetaManager._metadataCache() would first retrieve the pack metadata from the cache's database and add it to the cache's memory.
		#	2. A later call would retrieve the pack metadata again, but this time from the cache's memory where it was stored from the previous call.
		#	3. At the end of this 2nd (3rd, 4th, etc) call, MetaManager._metadataClean() is called, which removes the MetaCache.Attrribute dict. But since this is the same/global dict, it will remove it for all callers.
		#	4. When the 1st caller's thread continues in MetaManager._metadataCache(), the MetaCache.Attrribute is now deleted, so that it thinks the pack metadata is not in the cache database at all and then makes a foreground refresh of the pack metadata.
		#	5. This is a sporadic error when opening the show Progress menu, depending on how threads are interleaved, and results in pack metadata to be refreshes that is actually in the cache and is up-to-date.
		# To solve this, all metadata, including packs, are now at least shallow-copied in MetaCache._memory() before being returned.
		# This ensure that the first-level of pack dict attributes, including MetaCache.Attrribute, can be edited by different callers, without it changing for other callers.
		# However, this also means that the memory ID cannot be used for pack initialization anymore, since the dict would always be different, causing the same pack to be reinitialized again and again.
		# Instead, we use a "random" ID attribute in the pack dict. Even when shallow-copied, this ID string is also copied, ensuring the same ID is available from every call to MetaCache._memory().
		# The pack metadata is not changed after being generated (except for MetaCache.Attrribute), hence we can be assured that a different dict with the same ID has the same pack data.
		# There are only thress places where the ID changes:
		#	1. MetaCache.select(): The first time the pack metadata is retrieved from the MetaCache database. A new ID is generated before saving it to memory.
		#	2. MetaPack.generateXYZ(): When the pack is updated in MetaPack. A new ID is assigned, so that the next call to MetaPack.instance() will initialize a new pack object with the updated data.
		#	2. MetaPack.reduceXYZ(): Reduced pack data, so that it also can be cached.

		#if Tools.isInstance(pack, MetaPack): return id(pack.mPack)
		#else: return id(pack)

		data = pack.mPack if Tools.isInstance(pack, MetaPack) else pack
		if not update:
			id = data.get(MetaPack.Identifier)
			if id: return id

		# Could also be a random hash, etc.
		# Just has to be unique every time this is called.
		id = str(Time.timestamp(milliseconds = True)) + str(Tools.id(data))

		if update: data[MetaPack.Identifier] = id
		return id

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		MetaPack.Instance = {}
		self._checkReset()

	##############################################################################
	# INITIALIZE
	##############################################################################

	def _initialize(self, pack, id = False):
		try:
			self.mPack = pack

			if pack:
				if id: self.instanceId(pack = pack, update = True) # Generate a new ID for the newly created pack data.

				media = pack.get('content') or pack.get('media') # Legacy, previously the media was stored in "media", but now it is in "content".
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
												message += ' [%s] - Episode: S%sE%s - Index: %sx%s' % (i, str(s), str(e), str(season), str(episode))

												Logger.error(message)
							self.mEpisode[i] = episodes

			return self.mPack
		except:
			message = pack.get('title') if pack else None
			if message: message = message[0]
			Logger.error(message)
			return False

	##############################################################################
	# CHECK
	##############################################################################

	@classmethod
	def _checkId(self):
		return self.__name__

	@classmethod
	def _checkReset(self):
		Pool.checkReset(id = self._checkId())

	@classmethod
	def _checkIncrement(self, count = None):
		if count is None or count > 0: Pool.checkIncrement(id = self._checkId(), count = count)

	@classmethod
	def _checkDelay(self, check, count = None):
		config = MetaPack.CheckConfig[check]
		return Pool.checkIncrement(id = self._checkId(), count = count, limit = config.get('limit'), delay = config.get('delay'), lock = config.get('lock')) # Lock, in case there are multiple packs being generated concurrently.

	##############################################################################
	# EXPRESSION
	##############################################################################

	@classmethod
	def _expression(self, index):
		try:
			return MetaPack.Expressions[index]
		except:
			if MetaPack.Expressions is None:
				generic = '^\s*(?:tba|(?:(?:e|é|e\?)pis(?:o|ó|o\?)(?:des?|d?ios?)|part|folge|teil|aflevering|deel)[\s\-\_\.]*(?:(?:\d{2}[\-\_\.]){2}\d{4}|\d{4}(?:[\-\_\.]\d{2}){2}|(?:\#\s?)?\d+(?:\.\d+)?(?:$|[^\d])|[ivxlcd]+(?:$|[^\da-z]))|(?:(?:\d{2}[\-\_\.]){2}\d{4}|\d{4}(?:[\-\_\.]\d{2}){2}))[\s\:\-]*'
				MetaPack.Expressions = [
					Regex.expression(expression = '(\s{2,})', cache = False),
					Regex.expression(expression = '(' + generic + ')', cache = False),
					Regex.expression(expression = generic, cache = False),
					Regex.expression(expression = '(.{2,})[\(\[\s\-\_\.]*(?:\d+|[ivxlcd]+|one|two|three|four|five)[\)\]\s\-\_\.]*$', cache = False),
					Regex.expression(expression = '(prequel|sequel)', cache = False),
					Regex.expression(expression = '(\d+)', cache = False),
					Regex.expression(expression = '([\(\[]\d+[\)\]]$|(?:part|pt\.?|teil|deel)\d+[\)\]]?$)', cache = False),
					Regex.expression(expression = '(.*?)(?:$|\s*[\(\[])', cache = False),
					Regex.expression(expression = '(?:^|\s)(IX|IV|V?I{0,3})(?:$|[\s\)\]])', cache = False),
				]
			return MetaPack.Expressions[index]

	##############################################################################
	# ROMAN
	##############################################################################

	@classmethod
	def _roman(self, number):
		if MetaPack.Roman is None:
			MetaPack.Roman = {
				'I'		: 1,
				'II'	: 2,
				'III'	: 3,
				'IV'	: 4,
				'V'		: 5,
				'VI'	: 6,
				'VII'	: 7,
				'VIII'	: 8,
				'IX'	: 9,
				'X'		: 10,
			}
		return MetaPack.Roman.get(number)

	##############################################################################
	# CLEAN
	##############################################################################

	@classmethod
	def _titleAdjust(self, title):
		if title:
			main = []
			extra = []

			expression1 = self._expression(0)
			expression2 = self._expression(1)

			for i in title:
				# If the title has double-spaces, also add the cleaned single-space title.
				# Eg: One Piece S22E35: "The World Shakes!  The Straw Hats' Hostage Situation"
				# This only happened to this single episode, and is probably just a mistake on Trakt that will later be fixed.
				# But do this for these special cases, otherwise exact title matching will not work. Currently should only affect the test cases in tester.py.
				if '  ' in i: extra.append(Regex.replace(data = i, expression = expression1, replacement = ' ', all = True, cache = True))

				# Add titles without prefixes.
				# Eg: "Episode 13: Some Title" -> "Some Title"
				# Eg: "2023-03-05: Some Title" -> "Some Title"
				j = Regex.remove(data = i, expression = expression2, group = 1, cache = True).strip()
				if j and not j == i and len(j) > 3: main.append(j)

			if main or extra: return Tools.listUnique(main + title + extra)
		return None

	@classmethod
	def _titleClean(self, title):
		# Remove generic titles for specials that can clash with the titles from the official seasons.
		# Eg: Babylon Berlin S00E06 and S00E15+ have titles like "Episode 6", which is later incorrectly mapped to S01+ that also have an episode named "Episode 6".
		if title:
			expression = self._expression(2)
			return [i for i in title if not Regex.match(data = i, expression = expression, cache = True)]
		return None

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
	def _extractProvider(self, data, key, default = None, unique = None):
		result = None
		if data:
			results = []
			for i in data:
				result = self._extract(data = i, key = key, default = None)
				if not result is None: results.extend(result) if Tools.isList(result) else results.append(result) # Do not use Tools.isArray(), since internal values can be tuples.
			if results:
				if unique: results = Tools.listUnique(results, internal = True) # Allow to sort internal items that are unhashable lists.
				return results
			return default
		return default if result is None else result

	@classmethod
	def _extractMaximum(self, data, key):
		results = []
		for i in data:
			result = self._extract(data = i, key = key)
			if not result is None: results.append(result)
		if results: return max(results)
		else: return None

	# preference (evaluated 1st): pick the value from a specific preferred provider.
	# common (evaluated 2nd): pick the most common value if that value occurs more than other values.
	# minimum/maximum/first(evaluated 3rd): pick the minimum/maximum/first value.
	@classmethod
	def _extractCombined(self, data, key, preference = None, common = None, minimum = None, maximum = None, first = None):
		results = self._extract(data = data, key = key)

		if results:
			result = None
			commoned = None
			if Tools.isTuple(results): results = [results]
			provider = Tools.isArray(results) and Tools.isTuple(results[0])

			if not result and preference and provider:
				for i in results:
					if Tools.isArray(i):
						if i[0] == preference:
							result = i
							if result[1]: break
					else:
						result = i
						if result: break

			if not result and common:
				results = Tools.listUnique(results)
				base = [i[1] if Tools.isArray(i) else i for i in results] if provider else results
				commoned = Tools.listCommon(base)
				if commoned and base.count(commoned) > 1: result = commoned

			if not result:
				if minimum: result = min(results, key = lambda i : i[1] if Tools.isArray(i) else i) if provider else min(results)
				elif maximum: result = max(results, key = lambda i : i[1] if Tools.isArray(i) else i) if provider else max(results)
				elif first: result = results[0]
				elif commoned: result = commoned
				else: result = results[0]

			if result: return result[1] if provider and Tools.isTuple(result) else result
		return None

	@classmethod
	def _extractId(self, data, provider = None, default = None):
		# This function is called a lot during pack generation.
		# When hardcoding the extraction, instead of using self.extract(), about 1-2ms can be saved on average, which is about 1-2% of the total generation time.

		'''if provider: return self._extract(data, ['id', provider], default)
		else: return self._extract(data, 'id', default)'''

		if Tools.isArray(data):
			results = []
			if provider:
				for i in data:
					try: result = i['id']
					except: continue
					try: result = result[provider]
					except: continue
					if not result is None: results.append(result)
			else:
				for i in data:
					try: result = i['id']
					except: continue
					if not result is None: results.append(result)
			return results if results else default
		else:
			try: result = data['id']
			except: return default
			if provider:
				try: result = result[provider]
				except: return default
			return result

	@classmethod
	def _extractType(self, data, type = None, default = None):
		# This function is called a lot during pack generation.
		# When hardcoding the extraction, instead of using self.extract(), about 1-2ms can be saved on average, which is about 1-2% of the total generation time.

		'''if type: return self._extract(data, ['type', type], default)
		else: return self._extract(data, 'type', default)'''

		if Tools.isArray(data):
			results = []
			if type:
				for i in data:
					try: result = i['type']
					except: continue
					try: result = result[type]
					except: continue
					if not result is None: results.append(result)
			else:
				for i in data:
					try: result = i['type']
					except: continue
					if not result is None: results.append(result)
			return results if results else default
		else:
			try: result = data['type']
			except: return default
			if type:
				try: result = result[type]
				except: return default
			return result

	@classmethod
	def _extractTitle(self, data, default = None):
		# This function is called a lot during pack generation.
		# When hardcoding the extraction, instead of using self.extract(), about 1-2ms can be saved on average, which is about 1-2% of the total generation time.

		'''return self._extract(data, 'title', default)'''

		if Tools.isArray(data):
			results = []
			for i in data:
				try: result = i['title']
				except: continue
				if not result is None: results.append(result)
			return results if results else default
		else:
			try: return data['title']
			except: return default

	@classmethod
	def _extractNumber(self, data, number = None, part = None, provider = None, default = None):
		# This function is called a lot during pack generation.
		# When hardcoding the extraction, instead of using self.extract(), about 6-8ms can be saved on average, which is about 6-8% of the total generation time.

		'''key = ['number']
		if not provider is None: key.append(provider)
		if not number is None: key.append(number)
		result = self._extract(data, key, default)
		if not part is None:
			try: return result[part]
			except: return default
		return result'''

		if Tools.isArray(data):
			results = []
			if provider is None and number is None:
				for i in data:
					try: result = i['number']
					except: continue
					if not result is None: results.append(result)
			elif provider is None:
				for i in data:
					try: result = i['number']
					except: continue
					try: result = result[number]
					except: continue
					if not result is None: results.append(result)
			elif number is None:
				for i in data:
					try: result = i['number']
					except: continue
					try: result = result[provider]
					except: continue
					if not result is None: results.append(result)
			else:
				for i in data:
					try: result = i['number']
					except: continue
					try: result = result[provider]
					except: continue
					try: result = result[number]
					except: continue
					if not result is None: results.append(result)
			if results:
				if not part is None:
					try: return results[part]
					except: return default
				return results
			return default
		else:
			try: result = data['number']
			except: return default
			if not provider is None:
				try: result = result[provider]
				except: return default
			if not number is None:
				try: result = result[number]
				except: return default
			if not part is None:
				try: result = result[part]
				except: return default
			return result

	@classmethod
	def _extractDuration(self, data):
		'''result = None
		for i in data:
			result = self._extract(data = i, key = 'duration')
			if result: break # Ignore "0 secs" durations.
		return result'''

		for i in data:
			try:
				result = i['duration']
				if result: return result # Ignore "0 secs" durations.
			except: pass
		return None

	@classmethod
	def _extractStatus(self, data, unique = False):
		status = self._extract(data = data, key = 'status')
		if status and unique:
			status = Tools.listFlatten(status, recursive = True)
			status = Tools.listUnique(status)
		return status

	@classmethod
	def _extractMovies(self, data):
		'''return self._extract(data, 'movies', [])'''

		if Tools.isArray(data):
			results = []
			for i in data:
				try: result = i['movies']
				except: continue
				if not result is None: results.append(result)
			return results if results else []
		else:
			try: return data['movies']
			except: return []

	@classmethod
	def _extractSeasons(self, data):
		'''return self._extract(data, 'seasons', [])'''

		if Tools.isArray(data):
			results = []
			for i in data:
				try: result = i['seasons']
				except: continue
				if not result is None: results.append(result)
			return results if results else []
		else:
			try: return data['seasons']
			except: return []

	@classmethod
	def _extractEpisodes(self, data):
		'''return self._extract(data, 'episodes', [])'''

		if Tools.isArray(data):
			results = []
			for i in data:
				try: result = i['episodes']
				except: continue
				if not result is None: results.append(result)
			return results if results else []
		else:
			try: return data['episodes']
			except: return []

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
	def _createNumber(self, data, provider = None, episode = False):
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
						i = {MetaPack.ValueNumber : Tools.copy(self._extractNumber(i), deep = False)}
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
			MetaPack.NumberDate			: number.get(MetaPack.NumberDate),
		}

		if not provider:
			for i in MetaPack.Providers:
				num = number.get(i) or {}
				result[i] = {
					MetaPack.NumberStandard		: num.get(MetaPack.NumberStandard),
					MetaPack.NumberSequential	: num.get(MetaPack.NumberSequential),
					MetaPack.NumberAbsolute		: num.get(MetaPack.NumberAbsolute),
					MetaPack.NumberDate			: num.get(MetaPack.NumberDate),
				}

		# Always use the sequential/absolute numbers from Trakt if available.
		# Since different providers can have different episodes and numbering, the sequential/absolute numbers might deviated between providers.
		#	Eg: House: one extra episode on Trakt (S06E22).
		#	Eg: One Piece (Anime): difference in numbering in S21-end and S22-start between Trakt and TVDb.
		# Otherwise the sequential/absolute order can be screwed up if providers deviate from each other.
		# Also prefer the date number from Trakt, since the dates can differ between Trakt and TVDb.
		# Eg: One Piece S17 - Trakt (2015) - TVDb (2014)
		# Eg: One Piece S22 - Trakt (2024) - TVDb (2023)
		trakt = number.get(MetaPack.ProviderTrakt)
		if trakt:
			for i in [MetaPack.NumberSequential, MetaPack.NumberAbsolute, MetaPack.NumberDate]:
				value = trakt.get(i)
				if value: result[i] = value

		if episode:
			for k1, v1 in result.items():
				if Tools.isDictionary(v1):
					for k2, v2 in v1.items():
						if v2 is None: v1[k2] = [None, None]
				elif v1 is None: result[k1] = [None, None]

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
	def _createSummary(self, data, summary, specials = None, unspecials = None, value = None, count = False, total = True, mean = True, minimum = True, maximum = True, values = True, sort = False, unique = False, empty = False):
		result = {}

		# Treat differently for show and season summaries.
		# Show summaries should not include any specials for ValueTotal.
		# Season summaries should include non-S01 specials for ValueTotal.

		# NumberSpecial filtering is now done in _createSummaries().
		'''if summary == MetaPack.ValueTotal or not summary:
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
		'''
		if summary == MetaPack.ValueTotal or not summary:
			if len(data) == len([i for i in data if self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason) == 0]):
				data = [i for i in data if self._extractType(i, MetaPack.NumberStandard) or self._extractType(i, MetaPack.NumberSpecial)]
			else:
				data = [i for i in data if self._extractType(i, MetaPack.NumberStandard) or (self._extractType(i, MetaPack.NumberSpecial) and not self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason) == 0)]
		elif summary == MetaPack.NumberOfficial:
			data = [i for i in unspecials if self._extractType(i, MetaPack.NumberOfficial)]
		elif summary == MetaPack.NumberUnofficial:
			data = [i for i in unspecials if self._extractType(i, MetaPack.NumberUnofficial)]
		elif summary == MetaPack.NumberUniversal:
			data = [i for i in unspecials if self._extractType(i, MetaPack.NumberUniversal)]
		elif summary == MetaPack.NumberStandard:
			data = [i for i in unspecials if self._extractType(i, MetaPack.NumberStandard)]
		elif summary == MetaPack.NumberSequential:
			data = [i for i in unspecials if self._extractType(i, MetaPack.NumberSequential)]
		elif summary == MetaPack.NumberAbsolute:
			data = [i for i in unspecials if self._extractType(i, MetaPack.NumberAbsolute)]
		elif summary == MetaPack.NumberSpecial:
			data = [i for i in specials if self._extractType(i, MetaPack.NumberSpecial)]

		data = [i.get(value) for i in data]
		if not empty: data = [i for i in data if i]

		count_ = len(data)
		try: total_ = sum(data)
		except: total_ = 0 # Date strings.

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

		# Filter here, so save some time in _createSummary() which always filters by NumberSpecial.
		specials = []
		unspecials = []
		for i in data:
			if self._extractType(i, MetaPack.NumberSpecial): specials.append(i)
			else: unspecials.append(i)

		for i in [MetaPack.ValueTotal, MetaPack.NumberOfficial, MetaPack.NumberUnofficial, MetaPack.NumberUniversal, MetaPack.NumberStandard, MetaPack.NumberSequential, MetaPack.NumberAbsolute, MetaPack.NumberSpecial]:
			sub = self._createSummary(summary = i, data = data, specials = specials, unspecials = unspecials, value = value, count = count, total = total, mean = mean, minimum = minimum, maximum = maximum, values = values, sort = sort, unique = unique, empty = empty)
			if sub and (sub.get(MetaPack.ValueCount) or sub.get(MetaPack.ValueTotal) or sub.get(MetaPack.NumberSpecial) or sub.get(MetaPack.ValueValues) or sub.get(MetaPack.ValueMinimum) or sub.get(MetaPack.ValueMaximum)):
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

					if self._extractType(i, MetaPack.NumberSpecial) and self._extractNumber(i, MetaPack.NumberStandard, MetaPack.PartSeason):
						# IMDb specials SxxE00.
						# Eg: Doctor Who S02E00.
						# Still allow universal episodes that match to Trakt/TMDb/TVDb S0.
						# Eg: One Piece S15E10 (S00E39 on TVDb).
						# Eg: Pokémon S08E28 (S00E75 on TVDb).
						if not j == MetaPack.NumberSpecial and not self._extractType(i, MetaPack.NumberUniversal) and not self._extractType(i, MetaPack.NumberOfficial): continue

						# Do not count specials with a Trakt absolute number.
						# Eg: One Piece S15E590 (Trakt) which is S15E10 (standard).
						# Do not do for IMDb specials.
						# Eg: Doctor Who S02E00.
						# Update (2025-10): Why were these previously excluded? Should we not could specials, and specifically IMDb specials?
						# Eg: Family Guy S22 and S23 have 2 IMDb specials at the end of the season.
						#if j == MetaPack.NumberSpecial and self._extractType(i, MetaPack.NumberUnofficial) and self._extractNumber(i, MetaPack.NumberStandard, MetaPack.PartEpisode): continue

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

		specials = {MetaPack.ProviderTrakt: {}, MetaPack.ProviderTmdb: {}, MetaPack.ProviderTvdb: {}, MetaPack.ProviderImdb: {}}

		for i in data:
			season = self._extractNumber(i, MetaPack.NumberStandard)
			result[MetaPack.ValueSeason][MetaPack.ValueTotal] += 1

			for k in self._extractType(i).keys():
				try: result[MetaPack.ValueSeason][k] += 1
				except: pass # ValueAutomatic

			for j in self._extractEpisodes(i):
				if not self._extractType(j, MetaPack.NumberAutomatic): result[MetaPack.ValueEpisode][MetaPack.ValueTotal] += 1

				for k in self._extractType(j).keys():
					if k == MetaPack.NumberSequential or k == MetaPack.NumberAbsolute: continue # More accurate calculation below.
					if (k == MetaPack.NumberUniversal or k == MetaPack.NumberStandard) and self._extractType(j, MetaPack.NumberSpecial): continue # Do not count specials for these.

					# Do not count specials twice.
					# Only count if the ID is unqiue.
					# There might be discrepencies bnetween Trakt and TVDb specials, which can make some episode numbers appear twice.
					# Eg: GoT S00E56-57 (TVDb) which are added to the end of the specials, since they are not on Trakt. But Trakt has its own S00E56-57 which are different episodes.
					# The same special might also appear in S0 for some providers, but in a standard season S01+ on other providers.
					# Do not count double.
					if k == MetaPack.NumberSpecial:
						idTrakt = self._extractId(j, MetaPack.ProviderTrakt)
						add = True
						for p in specials.keys():
							id = self._extractId(j, provider = p)
							if id:
								special = specials[p].get(id)
								if not special: specials[p][id] = j

								# Check if the Trakt ID matches.
								# Sometimes Trakt has the incorrect TMDb ID, which causes an incorrect match.
								# Eg: Vikings S00E27 and S00E56 both have the TMDb ID 4111049 on Trakt.
								# Count them as separate sepcials if the Trakt ID does not match.
								elif idTrakt == self._extractId(special, MetaPack.ProviderTrakt): add = False
						if add:
							try: result[MetaPack.ValueEpisode][k] += 1
							except: pass # ValueAutomatic

					elif not(k == MetaPack.NumberOfficial or k == MetaPack.NumberUnofficial) or self._extractNumber(j, MetaPack.NumberStandard, part = MetaPack.PartSeason) > 0:
						try: result[MetaPack.ValueEpisode][k] += 1
						except: pass # ValueAutomatic

				if self._extractType(j, MetaPack.NumberOfficial):
					# Do not add specials to the sequential/absolute count if they form part of the storyline.
					# These episodes will already be counted in the standard S01+ seasons.
					# Eg: One Piece - S00E39 (TVDb) vs S15E590 (Trakt/TMDb)
					allow = True
					if season == 0:
						for k in MetaPack.Providers:
							if self._extractNumber(j, number = MetaPack.NumberStandard, provider = k, part = MetaPack.PartSeason):
								allow = False
								break

					if allow:
						for k in (MetaPack.NumberSequential, MetaPack.NumberAbsolute):
							if self._extractNumber(j, k, part = MetaPack.PartEpisode): result[MetaPack.ValueEpisode][k] += 1

		for i in result[MetaPack.ValueMean].keys():
			try: result[MetaPack.ValueMean][i] = int(Math.round(result[MetaPack.ValueEpisode][i] / float(result[MetaPack.ValueSeason][i] or 1)))
			except: pass # ValueAutomatic

		return result

	@classmethod
	def _createInterval(self, data, status = None, season = False):
		result = MetaPack.IntervalOtherly
		try:
			if data:
				finished = (MetaPack.StatusEnded, MetaPack.StatusCanceled)

				interval = self._extract(data[0], key = 'interval')

				if season is False: # Show release.
					# Pick the interval from the last season.
					# Some shows change their interval type over seasons and we want to use the most recent interval type.
					# Eg: The Witcher S01+S02 are instantly released, while S03 is batchly released.
					previous = None
					for i in reversed(data):
						if self._extractType(i, MetaPack.NumberStandard):
							result = self._extract(i, key = 'interval')
							if result:
								# Either if the season has ended, or if there are enough episodes.
								# Eg: LEGO Masters S05 (batchly) and S06 (weekly). Use weekly for the show.
								# If a new/upcoming season is released, it might already have all episodes, but they do not have dates yet.
								# This makes the latests season have an "otherly" interval. Do not use this for the show interval.
								# Eg: The Lord of the Rings: The Rings of Power S03.
								episodes = self._extract(i, key = 'episodes')
								statusSeason = self._extract(i, key = 'status')
								if statusSeason in finished or (episodes and len(episodes) >= 4 and not(statusSeason == MetaPack.StatusUpcoming and result == MetaPack.IntervalOtherly)):
									# Only do this if the new season has dates for at least the first 3 episodes.
									# Otherwise new seasons with only 1 or 2 episodes, or more episodes but without dates, might be marked as "instantly".
									dated = True
									if episodes:
										limit = 3
										dated = 0
										for j in episodes[:limit]:
											if j and self._extract(j, key = 'time'):
												dated += 1
										dated = dated == limit

									if dated: return result
								if previous is None: previous = result

					return previous or interval
				else: # Season release.
					times = []
					missing = 0
					for i in data:
						if self._extractType(i, MetaPack.NumberOfficial):
							time = self._extract(i, key = 'time')
							if time: times.append(time)
							else: missing += 1

					# For unofficial seasons.
					# Eg: Dragon Ball Super S02+
					if not times:
						missing = 0
						for i in data:
							if self._extractType(i, MetaPack.NumberStandard):
								time = self._extract(i, key = 'time')
								if time: times.append(time)
								else: missing += 1

					if times:
						times = Tools.listSort(times)

						# Some seasons have some episodes with a date and others not.
						# Add dummy times for thesze missing dates.
						# Eg: Good times, bad times (german soap) S08E37+
						if missing:
							time = int((times[0] + times[-1]) / 2.0)
							times.extend([time] * missing)
							times = Tools.listSort(times)

						# Not sure if taking the difference between the first and last episode is the most accurate.
						# Alternatively, calculate the average time span between every two consecutive episodes.
						# Maybe also filter out outliers, such as double episodes, or mid-season finales which create a months-long gap between two episodes.
						difference = abs(times[0] - times[-1]) / 86400.0
						frequency = (len(times) / difference) if difference else 0
						cluster = Tools.listCluster(times, difference = 72000) # Not a full day, otherwise daily shows will form clusters.
						clustered = len(cluster) / float(len(times))

						if frequency > 1.0 and difference <= 7 and status in finished: result = MetaPack.IntervalQuickly # [2.0, 2.0] Eg: The Little Drummer Girl (at least on IMDb).
						elif frequency >= 0.05 and len(cluster) <= 7 and clustered <= 0.5: result = MetaPack.IntervalBatchly # [0.16, 0.28] Eg: The Witcher S03. Eg: Stranger Things S05. Eg: LEGO Masters S05
						elif frequency < 0.01 and difference <= 3 and (status in finished or len(times) >= 3): result = MetaPack.IntervalInstantly # [0.0, 0.0] Eg: The Witcher (do not use this for future season which only have 1 or 2 episodes on Trakt/TVDb).
						elif frequency < 0.35 or (frequency < 0.45 and clustered >= 0.5 and clustered <= 0.75): result = MetaPack.IntervalWeekly # [0.13, 0.18] Eg: Game of Thrones. Also checked "clustered" for future seasons that only have a few episodes and 2 of the episodes have the same release date.
						elif frequency >= 0.35 and frequency <= 1.0: result = MetaPack.IntervalDaily # [0.4, 0.65] Eg: The Late Show with Stephen Colbert

						# Allow certain intervals for S0.
						# Not Weekly or Daily, since the thresholds might not correctly work for S0.
						# Eg: Money Heist S0 is a full season with full episode specials, including a midseason and season finale. Episodes were released in 2 batches.
						if season == 0 and (result == MetaPack.IntervalWeekly or result == MetaPack.IntervalDaily): result = MetaPack.IntervalOtherly
		except: Logger.error()
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

				# Generate a new pack identifier with "id = True".
				return self._initialize(id = True, pack = {
					'media'						: Media.Pack,
					'content'					: Media.Movie,

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
						MetaPack.ValueTotal		: durationTotal,
						MetaPack.ValueMean		: durationMean,
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
	def generateShow(self, trakt = None, tvdb = None, tmdb = None, imdb = None, check = None):
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
					1. Change the "pack" assembly in this function to allow multiple entries in the lookup table per episode. Eg: looking up S02E01 returns a list for "tvdb" that contains 2 entries for TVDb's shorter episodes (S02E01 and S02E02).
					2. Update MetaManager._metadataEpisodeUpdate() to correctly combine the dicts from the different providers, based on the new lookup from this function. Instead of combining the dicts purely based on a fixed episode number (that does not match between Trakt's combined order vs TVDb's uncombined order), do a lookup first to see if it might map to multiple combined episodes. Then only use a subset of the metadata to update the dicts (eg: just add the additional ratings/votings to the updated dict, but not the title, since there are combined/uncombined titles)
					3. Change Playback to mark multiple episodes as watched/rated on Trakt, if the combined order requires it. Or avoid duplicate watched markings for uncombined episodes.
					4. Update the season and episode menus to show the correct ones, preferably the uncombined order.C heck that the menus show the correct watched status checkmark, etc, if the order differs on Trakt vs TVDb.
					5. How does this work for provider scraping that use IDs (eg: Orion)?
					6. NB: TVDb uses different episode IDs for combined order. The standard and absolute seasons use the same episodes and therefore have the same metada and IDs. But TVDb's combined seasons have completely separate episodes, with separate IDs and metadata. I think that Trakt has the episode IDs of the combined TVDb episodes, not the standard/absolute IDs.
					7. Select the correct file from the torrent pack during playback.
					8. Or a hacky solution might be to ignore TVDb's order and use combined orders if available. This would make #3, #4, #6, #7 a lot easier. Not sure what the torrents use? If they also use the combined order, this could be the way.
			'''

			if not tvdb and not trakt and not tmdb and not imdb: return None

			from lib.meta.tools import MetaTools

			timer = Time(start = True, mode = Time.ModeMonotonic) # Only calculate the time if it is actually executing, since there can be sleeps in between from Pool.check().

			if check is True: check = MetaPack.CheckDefault
			elif check is False: check = MetaPack.CheckInstant

			# Do not add IMDb here.
			# Some shows on IMDb have a single absolute season. This can substantially increase pack generation time.
			# Eg: Good times bad times.
			# Eg: One Piece
			# Since IMDb only has the ID and episode number, but no other attributes (eg: title or date), it does not make sense to process it like the other datasets.
			# Instead, only fill in the IMDb ID and number after all episodes were processed, which is a lot faster.
			#base = [(MetaPack.ProviderTvdb, tvdb), (MetaPack.ProviderTrakt, trakt), (MetaPack.ProviderTmdb, tmdb), (MetaPack.ProviderImdb, imdb)] # Order according to which data to prefer.
			base = [(MetaPack.ProviderTvdb, tvdb), (MetaPack.ProviderTrakt, trakt), (MetaPack.ProviderTmdb, tmdb)] # Order according to which data to prefer.

			providersAll = [i[0] for i in base]
			providersExtended = providersAll + [MetaPack.ProviderImdb]
			base = [i for i in base if i[1] and 'seasons' in i[1]] # Check seasons, to exclude IMDb basic data with only an ID.
			data = [i[1] for i in base]
			providers = [i[0] for i in base]
			providerCount = len([i for i in base if i[1]]) # Only count those that have data (aka IMDb should be excluded).
			series = [Media.Premiere, Media.Finale, Media.Inner, Media.Outer, Media.Middle, Media.Alternate, Media.Special, Media.Season]

			language = self._extractList(data, 'language', [])
			tools = MetaTools.instance()
			setting = tools.settingsLanguage()
			current = Time.timestamp()
			developer = System.developerVersion()

			excessive = False
			sequential = None
			discrepancies = {}
			specialDiscrepancy = False # Different providers have a different number of specials, excluding providers without any specials.

			seasonCount = {} # The total number of standard seasons, excluding the special season.
			episodeCount = {} # The total number of sequential episodes in the show, excluding specials.
			showCount = {}

			seasonYear = {}
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

			# Sometimes IMDb temporarily adds a 2nd season to an absolute show.
			# Eg: One Piece - IMDb has a single absolute season.
			# But when S23 was added as a future season (S23 added to TVDb, but not to Trakt/TMDb yet), IMDb now has S02 with a single future episode S02E01.
			# This episode is probably only temporarily in S02 and might be moved to S01 once released.
			# Remove these S02 from IMDb, since they otherwise create confusion, since IMDb now is multi-seasoned instead of single-seasoned.
			if imdb:
				count = {}
				for season in self._extractSeasons(imdb):
					if season:
						numberSeason = self._extractNumber(season, MetaPack.NumberStandard)
						if numberSeason:
							episodes = self._extractEpisodes(season)
							count[numberSeason] = len(episodes)
				if len(count.keys()) == 2 and count.get(1, 0) > 500 and count.get(2, 0) <= 5:
					seasons = self._extractSeasons(imdb)
					for i in range(len(seasons)):
						if self._extractNumber(seasons[i], MetaPack.NumberStandard) == 2:
							del seasons[i]
							break

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

						# For daytime shows where the season number is the year.
						# This seems to mostly happen on TVDb.
						# Eg: Good times, bad times (german soap)
						# IMDb categorizes these shows according to year, but uses S01 for all years, basically creating an absolute order.
						# Eg: Good times, bad times S2000E1889 (TVDb) -> S01E1889 (IMDb)
						numberYear = self._extractNumber(season, 'year')
						if numberYear and numberYear >= MetaPack.ThresholdYear:
							if not provider in seasonYear: seasonYear[provider] = {}
							seasonYear[provider][numberSeason] = numberYear

				seasonCount[provider] = countSeason
				episodeCount[provider] = countEpisode

			# Shows with 1000s of episodes can take very long to generate.
			# Eg: Good times, bad times (german soap) with 8000+ episodes takes 15+ minutes.
			# For these shows, limit various processing in order to reduce pack generation time.
			# This will be less accurate, since for instance title matching is ignored, but it is better to have a less accurate pack that does not take ages to generate.
			# Anime shows (eg: Pokémon or One Piece) will not be subject to this, since they typically only have 1000-2000 episodes.
			if episodeCount and max(episodeCount.values()) > 3000: excessive = True

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

			if not self._checkDelay(check = check): return False

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

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 3 - Combine the metadata from different providers for episodes with the same number matching IDs/titles.
			################################################################################################################

			lookupImdb = {}
			incorrectImdb = {}
			if imdb:
				for season in (imdb.get('seasons') or []):
					for episode in (season.get('episodes') or []):
						id = self._extractId(episode, MetaPack.ProviderImdb)
						if id: lookupImdb[id] = episode['number'][MetaPack.NumberStandard]

			# Trakt sometimes has the wrong TVDb and/or IMDb ID for specials.
			# Eg: Vikings S00E06 (Trakt) - tt11417678 (IMDb) - 6931970 (TVDb)
			# Eg: Vikings S00E07 (Trakt) - tt11417678 (IMDb) - 7473191 (TVDb)
			# Eg: Vikings S00E21 (Trakt) - 7473191 (TVDb)
			# If an ID exists more than once, reset their TVDb/IMDb ID to None, so that title matching is used instead.
			if trakt:
				temp = {MetaPack.ProviderTvdb : {}, MetaPack.ProviderImdb : {}}
				for season in self._extractSeasons(trakt):
					if season and self._extractNumber(season, MetaPack.NumberStandard) == 0:
						episodes = self._extractEpisodes(season)

						for episode in episodes:
							for provider in temp.keys():
								id = self._extractId(episode, provider)
								if id:
									if id in temp[provider]: temp[provider][id] += 1
									else: temp[provider][id] = 1

						for episode in episodes:
							for provider in temp.keys():
								id = self._extractId(episode, provider)
								if id and temp[provider][id] > 1:
									episode['id'][provider] = None

									# For IMDb, only reset the first ID, but not subsequential IDs.
									# Since IMDb data does not have titles, and can therefore not be matched by title later on.
									# Eg: Family Guy S00E23 and S00E24 have the same IMDb ID on Trakt (tt33044453). The ID is actually for S00E24.
									# Not sure if resetting the 1st ID, instead of the 2nd ID, is always the correct way. There might be cases where the 2nd ID needs resetting, and this code has to be re-thought.
									# Update: This cannot be used reliably, since sometimes Trakt has the incorrect IMDb ID which is not correct for any of the episodes it was assigned to.
									# Eg: Vikings S00E06 and S00E07 (Trakt) which have the same IMDb ID tt11417678, but this ID actually belongs to S00E21 (The Saga of Floki).
									# Only reset the first IMDb ID if the episode number is not in S00 or SxxE00.
									#if provider == MetaPack.ProviderImdb: temp[provider][id] = 0
									if provider == MetaPack.ProviderImdb:
										numberImdb = lookupImdb.get(id)
										if numberImdb and numberImdb[MetaPack.PartSeason] > 0 and numberImdb[MetaPack.PartEpisode] > 0:
											temp[provider][id] = 0
						break

			# Sometimes Trakt has the incorrect TVDb/TMDb/IMDb IDs.
			# If the ID from Trakt does not point to any episode from the other provider, reset the ID, so that the correct ID is added based on other attributes (eg: title matching).
			# Currently this is only done for TVDb, but it could also be done for TMDb/IMDb if need be.
			# Eg: QI S22E09 - "Variety" (Trakt) vs "Christmas Special" (TVDb). Trakt has the TVDb ID pointing to the correct episode, but from a different show called "QI XL" which has the extended episodes.
			# Eg: QI S00E15 - Trakt has a TVDb ID that does no longer exist on TVDb.
			# These IDs are added back later on, if there was not any match by number or title.
			correctTvdb = {}
			incorrectTrakt = {}
			if trakt and tvdb:
				for season in self._extractSeasons(tvdb):
					for episode in self._extractEpisodes(season):
						try: idTvdb = episode['id'][MetaPack.ProviderTvdb]
						except: idTvdb = None
						if idTvdb: correctTvdb[idTvdb] = True

				total = 0
				incorrectedTrakt = []
				for season in self._extractSeasons(trakt):
					episodes = self._extractEpisodes(season)
					total += len(episodes)
					for episode in episodes:
						try: idTvdb = episode['id'][MetaPack.ProviderTvdb]
						except: idTvdb = None
						if idTvdb and not idTvdb in correctTvdb:
							incorrectedTrakt.append(episode)
							try: idTrakt = episode['id'][MetaPack.ProviderTrakt]
							except: idTrakt = None
							if idTrakt: incorrectTrakt[idTrakt] = idTvdb

				# Only do this if a small number of episodes have the incorrect ID.
				# Since Trakt might have TVDb IDs that are from another TVDb season order, such as combined/uncombined orders.
				# Eg: Star Wars: Young Jedi Adventures (TVDb)
				if incorrectTrakt and len(incorrectTrakt) < (total * 0.1):
					for episode in incorrectedTrakt:
						episode['id'][MetaPack.ProviderTvdb] = None

			# Sometimes Trakt and TVDb return a different show status.
			# Eg: Pokemon.
			#	On TVDb the show is continuing with S26 and S27.
			#	On Trakt the show has ended with S25. The later seasons are a new/separate show: "Pokémon Horizons: The Series".
			# Prefer the Trakt status, since Trakt is also used for the default numbering and for the season statuses.
			# Trakt/TMDb also have "returning" status for some shows, while TVDb has "continuing". Trakt/TMDb also have the "continuing" status in addition to "returning".
			# Not sure what the difference is. "continuing" is probably if a new season is busy airing, while "returning" is for shows that have a planned future season, but it has not started yet.
			# Eg: One Piece
			statusShow = None
			values = {}
			for provider, item in base:
				value = self._extract(data = item, key = 'status')
				if value: values[provider] = value
			if values:
				statusShow = values.get(MetaPack.ProviderTrakt)
				if not statusShow: statusShow = next(iter(values.values()))
			statusFinished = statusShow in (MetaPack.StatusEnded, MetaPack.StatusCanceled)

			#gaiaabsoluted
			# For some shows Trakt has a single absolute season, while TVDb has multiple seasons.
			# Eg: Dragon Ball Super
			# We could use the TVDb numbering as the official/standard numbers.
			# However, this is probably not a good idea and would cause various issues:
			#	1. Trakt is used for official numbering across other shows, and making exceptions where TVDb numbering is used might create various problems, especially when interacting with Trakt (watched status, ratings, etc).
			#	2. When using MetaManager.metadataEpisode(), there are issues with the numbering, since retrieving a full season of episodes will now have a mismatch between Trakt and TVDb numbers. Eg: retrieving S01E50 will retrieve the TVDb S04 episode, instead of the Trakt S01E50 (which has all IDs, ratings, more images, etc).
			#	3. MetaManager.metadataEpisodeNext() would need specials rules.
			#	4. MetaTools.mergeType() would need updating.
			#	5. Assume that years later, the ended show is restarted and a new season is added. Trakt might add a S02 and TVDb S06. Now we have even more mismatches between the seasons.
			# For now, we stick to Trakt as the official numbering.
			# If we ever want to change this, we can re-enable all code labelled with "gaiaabsoluted" and the Tester will have to be rerun.
			absoluted = {}
			for provider, item in base:
				for season in self._extractSeasons(item):
					if season:
						numberSeason = self._extractNumber(season, MetaPack.NumberStandard)
						if numberSeason and numberSeason > absoluted.get(provider, 0): absoluted[provider] = numberSeason
			# Not sure if this always works correctly. What about a show that has finished S01 and there is already a S02 on TVDb, but not on Trakt.
			absoluted = absoluted.get(MetaPack.ProviderTrakt, -1) == 1 and (absoluted.get(MetaPack.ProviderTvdb, -1) > 2 or (absoluted.get(MetaPack.ProviderTvdb, -1) > 1 and statusFinished))

			# Which provider uses absolute-episode numbering within seasons.
			# Although some leniency, in case the 1st episode is missing, or TVDb does not have all episodes yet.
			absolution = {}
			for provider, item in base:
				seasons = self._extractSeasons(item)
				for season in seasons:
					if season:
						numberSeason = self._extractNumber(season, MetaPack.NumberStandard)
						if numberSeason:
							episodes = self._extractEpisodes(season)
							if episodes:
								numberEpisode = self._extractNumber(episodes[0], MetaPack.NumberStandard, part = MetaPack.PartEpisode)
								if numberEpisode and numberEpisode > 2:
									try: absolution[provider] += 1
									except: absolution[provider] = 1
				if absolution.get(provider): absolution[provider] = absolution[provider] > len(seasons) * 0.7

			tvdbId = {}
			titleSpecial = {}
			for provider, item in base:
				for season in self._extractSeasons(item):
					if season:
						numberSeason = self._extractNumber(season, MetaPack.NumberStandard)
						for episode in self._extractEpisodes(season):
							if episode:
								title = self._extractTitle(episode)

								id = self._extractId(episode, MetaPack.ProviderTvdb)
								if id:
									if not id in tvdbId: tvdbId[id] = []
									tvdbId[id].append((title, episode))

								# Add generic titles for specials to a lookup.
								# Eg: Money Heist S0 - "Episode 1", "Episode 2", etc.
								# These titles get removed to avoid incorrect title matching.
								# They get re-added at the end.
								if numberSeason == 0:
									title = self._createTitle(data = [episode], language = language, setting = setting)
									if title:
										ids = self._extractId(episode)
										if ids:
											for k, v in ids.items():
												if v:
													if not k in titleSpecial: titleSpecial[k] = {}
													try: titleSpecial[k][v].extend(title)
													except: titleSpecial[k][v] = title
			for k1, v1 in titleSpecial.items():
				for k2, v2 in v1.items():
					v1[k2] = Tools.listUnique(v2)

			# Firstly, create an list for each episode, containing the episode metadata from each provider, in the order of the provider preference.
			# Secondly, combine the list of episode metadatas into a single item.
			# NB: Do not just interate over the providers and update the dict in every iteration. Otherwise the last provider (eg IMDb) will overwrite the data of more important providers (eg: TVDb).
			for provider, item in base:
				# Use later on to determine which status comes from which provider.
				value = item.get('status')
				item['status'] = tuple(value) if (Tools.isArray(value) and value[0] == provider) else (provider, value)

				for season in self._extractSeasons(item):
					if season:
						numberSeason = self._extractNumber(season, MetaPack.NumberStandard)
						episodes = self._extractEpisodes(season)

						# Do not add TMDb S00, since there is no extended metadata for them, and S0 can have missing episodes or ordered differently.
						# These values are later interpolated from the Trakt data, since Trakt seems to typically have the TMDb instead of the TVDb episode numbering.
						# Eg: GoT S00.
						# Update: detailed pack metadata is now retrieved from TMDb as weel, so there is no reason for this.
						# Having this enabled, causes TMDb specials to not be included if Trakt does not have the TMDb ID.
						# Eg: Babylon Berlin S00E04+
						#if provider == MetaPack.ProviderTmdb and numberSeason == 0: continue

						if not self._extractNumber(season, MetaPack.NumberSequential): season['number'][MetaPack.NumberSequential] = None
						if not self._extractNumber(season, MetaPack.NumberAbsolute): season['number'][MetaPack.NumberAbsolute] = None
						if not self._extractNumber(season, MetaPack.NumberDate):
							date = None
							try: date = int(self._extract(data = season, key = 'date').split('-')[0])
							except: pass
							if not date:
								try: date = int(self._extract(data = episodes[0], key = 'date').split('-')[0])
								except: pass
							season['number'][MetaPack.NumberDate] = date

						if numberSeason == 0: season['number'][MetaPack.NumberSequential] = 1
						if numberSeason == 0: season['number'][MetaPack.NumberAbsolute] = 1

						season['number'][provider] = self._createNumber(data = season, provider = provider)

						if numberSeason == 0: season['number'][provider][MetaPack.NumberSequential] = 1
						if numberSeason == 0: season['number'][provider][MetaPack.NumberAbsolute] = 1

						# Use later on to determine which seasons status comes from which provider.
						value = season.get('status')
						season['status'] = tuple(value) if (Tools.isArray(value) and value[0] == provider) else (provider, value)

						# Use later on to determine which season types comes from which provider.
						value = season.get('serie')
						season['serie'] = tuple(value) if (Tools.isArray(value) and value[0] == provider) else (provider, value)

						self._createAppend(data = seasonTree, key = numberSeason, values = season)

						numberPrevious = None
						for episode in episodes:
							numberEpisode = self._extractNumber(episode, MetaPack.NumberCustom, part = MetaPack.PartEpisode)
							numberStandard = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
							numberSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
							numberAbsolute = self._extractNumber(episode, MetaPack.NumberAbsolute, part = MetaPack.PartEpisode)
							if numberEpisode is None: numberEpisode = numberStandard

							if numberPrevious is False: # Also do not use any of the subsequent "special" episodes for sequential ordering.
								episode['number'][MetaPack.NumberSequential] = None
								episode['type'] = {MetaPack.NumberSpecial : True}
							else:
								if not numberSequential: episode['number'][MetaPack.NumberSequential] = None
								elif numberPrevious:
									# Sometimes TVDb has weird episodes, probably specials, in their seasons that suddenly have a huge episode number jump.
									# Eg: The Librarians 2014 - S02E10 -> S02E101, S02E102, S02E103.
									# Do not include these in the sequential numbering.
									try:
										numberTemp = numberPrevious.get(MetaPack.NumberSequential)
										if numberTemp and numberTemp[MetaPack.PartEpisode] == numberSequential - 1: # Correct sequential increment from the previous episode.
											numberTemp = numberPrevious.get(MetaPack.NumberStandard)
											if numberTemp and abs(numberTemp[MetaPack.PartEpisode] - numberStandard) > 20:
												# Do not do this for wrongly-numbered episodes.
												# Eg: The Tonight Show Starring Jimmy Fallon S02E223 is incorrectly labelled as S02E263 on Trakt.
												if not Media.Finale in (self._extract(episode, key = 'serie') or []):
													numberPrevious = False
													episode['number'][MetaPack.NumberSequential] = None
													episode['type'] = {MetaPack.NumberSpecial : True}
									except: Logger.error()

							if not numberAbsolute: episode['number'][MetaPack.NumberAbsolute] = None
							episode['number'][provider] = self._createNumber(data = episode, provider = provider)

							if not numberPrevious is False: numberPrevious = self._extractNumber(episode)

							# Do not mark specials with their own internal absolute numbers.
							# An absolute number should indicate the absolute position within the series (S01).
							# And technically specials could be part of the storyline and have their own absolute number to be placed within S01, although this is probably rare or does not happen at all.
							# Also, do not check if the absolute number is None, since Trakt sometimes returns some specials with an absolute number of None and others with a number of 0. Eg: GoT.
							if numberSeason == 0:
								if not numberSequential: episode['number'][MetaPack.NumberSequential] = [1, 0]
								if not self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode, provider = provider): episode['number'][provider][MetaPack.NumberSequential] = [1, 0]

								if not numberAbsolute: episode['number'][MetaPack.NumberAbsolute] = [1, 0]
								if not self._extractNumber(episode, MetaPack.NumberAbsolute, part = MetaPack.PartEpisode, provider = provider): episode['number'][provider][MetaPack.NumberAbsolute] = [1, 0]

								# Remove generic titles for specials that can clash with the titles from the official seasons.
								# Eg: Babylon Berlin S00E06 and S00E15+ have titles like "Episode 6", which is later incorrectly mapped to S01+ that also have an episode named "Episode 6".
								# These titles get added back at the end using "titleSpecial".
								title = episode.get('title')
								if title:
									cleaned = self._titleAdjust(self._titleClean(title = title))
									if not cleaned is None: episode['title'] = cleaned
								alias = episode.get('alias')
								if alias:
									for k, v in alias.items():
										cleaned = self._titleAdjust(self._titleClean(title = v))
										if not cleaned is None: episode['alias'][k] = cleaned
							else:
								title = episode.get('title')
								if title:
									cleaned = self._titleAdjust(title = title)
									if not cleaned is None: episode['title'] = cleaned
								alias = episode.get('alias')
								if alias:
									for k, v in alias.items():
										cleaned = self._titleAdjust(title = v)
										if not cleaned is None: episode['alias'][k] = cleaned

							# Sometimes Trakt has incorrect TVDb IDs.
							# In these cases, the IMDb is also mostly incorrect.
							# TVDb and IMDb typically use the same numbering for these cases, so Trakt probably uses the incorrect number to lookup the episode, and that is why both the TVDb and IMDb IDs are incorrect.
							# Eg: My Name Is Earl S03E06 (Trakt's TVDb ID: 341496, correct TVDb ID: 338859/338860)
							# Eg: My Name Is Earl S03E12 (Trakt's TVDb ID: 361108, correct TVDb ID: 359124/359125)
							# Do not do this for specials, since both their titles and airing date might deviate.
							# Eg: Downton Abbey S00E13.
							# For some late night shows or shows with many episodes, there are often tons of incorrect IDs.
							# Eg: The Tonight Show Starring Jimmy Fallon S01 (but also most other earlier seasons).
							# Although episodes marked as incorrect below are probably all correctly marked, there are so many episodes with incorrect IDs (Jimmy Fallon, Good Times Bad Times, etc), that maybe there are some correct episode IDs that get marked as incorrect.
							# This code might therefore need improvement if some false-positives are found in the future.
							if provider == MetaPack.ProviderTrakt and not numberSeason == 0:
								id = self._extractId(episode, MetaPack.ProviderTvdb)
								if id:
									titleTvdb = tvdbId.get(id)
									if titleTvdb:
										# Also use the aliases for Anime.
										# Eg: Pokémon S01E04 + S01E09.
										#titleTrakt = self._extractTitle(episode)
										titleTrakt = self._createTitle(data = [episode], language = language, setting = setting)

										if titleTrakt:
											titleMatch = []
											titleUnmatch = []
											for i in titleTvdb:
												# Sometimes TVDb does not return an episode title in the API.
												# Eg: One Piece S13E51.
												if i[0] and self.match(data = i[0], title = titleTrakt, combined = True, quick = True, exact = True, detail = True).get('match') < 0.7:
													# Do not do this for specials, since both their titles and airing date might deviate.
													# Eg: Downton Abbey S00E13.
													if not self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason) == 0:
														# Only mark as incorrect, if the airing time deviates a lot.
														# Trakt sometimes has the correct title+date, but the incorrect episode title.
														# Eg: The Tonight Show Starring Jimmy Fallon S07E196
														# The title and alias returned by Trakt is: "Kelly Clarkson, Joy Reid, The Flaming Lips", which is the incorrect title for the episode.
														# The originaltitle returned by Trakt is: "Seth MacFarlane, Evan Rachel Wood, Penn & Teller", which is the correct title. This is also the title shown on Trakt's website.
														# The season is marked as "Locked Season" on Trakt, so the metadata will probably not get updated anymore.
														# The episode was probably incorrect at some point, and then got updated with a new episode title, although the ID and episode number is correct.
														# There are way too many such episodes (eg: just in Jimmy Kimmel), that marking them as incorrect creates more problems.
														time1 = self._extract(data = i[1], key = 'time')
														if Tools.isTuple(time1): time1 = time1[1]
														time2 = self._extract(data = episode, key = 'time')
														if time1 and time2 and abs(time1 - time2) > 172800: titleUnmatch.append((i[1], abs(time1 - time2)))
												elif not self._extractId(i[1], MetaPack.ProviderTrakt):
													# Only add this if there is no Trakt ID. That is, the episode does not come from Trakt.
													# Eg: The Tonight Show Starring Jimmy Fallon S01E159 - Trakt has the ID for mutiple episodes.
													titleMatch.append(i[1])

											if titleUnmatch:
												if titleMatch:
													for i in titleUnmatch:
														i = i[0]
														idImdb = i['id'].get(MetaPack.ProviderImdb)
														if idImdb:
															if not MetaPack.ValueIncorrect in i: i[MetaPack.ValueIncorrect] = []
															i['id'][MetaPack.ProviderTvdb] = None
															i[MetaPack.ValueIncorrect].append(MetaPack.ProviderTvdb)

															if imdb: lookuped = not lookupImdb.get(self._extractId(i, MetaPack.ProviderImdb)) == [numberSeason, numberEpisode]
															else: lookuped = len(titleUnmatch) > 0 # > 0, not > 1. Jimmy Kimmel S01E159 vs S02E31.
															if lookuped:
																incorrectImdb[tuple(self._extractNumber(i, MetaPack.NumberStandard))] = True
																i['id'][MetaPack.ProviderImdb] = None
																i[MetaPack.ValueIncorrect].append(MetaPack.ProviderImdb)
												else:
													idImdb = episode['id'].get(MetaPack.ProviderImdb)

													# Only remove the TVDb ID if there is an IMDb ID.
													# Eg: The Tonight Show Starring Jimmy Fallon S01E165
													if idImdb:
														if not MetaPack.ValueIncorrect in episode: episode[MetaPack.ValueIncorrect] = []
														episode['id'][MetaPack.ProviderTvdb] = None
														episode[MetaPack.ValueIncorrect].append(MetaPack.ProviderTvdb)

														# Sometimes only the TVDb is incorrect, but the IMDb is correct.
														# Eg: The Librarians S01E06 - S01E09.
														if imdb: lookuped = titleUnmatch[0][1] > 31536000 or not lookupImdb.get(self._extractId(episode, MetaPack.ProviderImdb)) == [numberSeason, numberEpisode]
														else: lookuped = len(titleUnmatch) > 1 or titleUnmatch[0][1] > 2592000 # Jimmy Kimmel S02E44.
														if lookuped:
															# Only if there was an incorrect IMDb ID, otherwise do not add.
															# Eg: Good times, bad times S01E04.
															incorrectImdb[(numberSeason, numberEpisode)] = True

															episode['id'][MetaPack.ProviderImdb] = None
															episode[MetaPack.ValueIncorrect].append(MetaPack.ProviderImdb)

							# Use later on to determine which episode types comes from which provider.
							value = episode.get('serie')
							episode['serie'] = tuple(value) if (Tools.isArray(value) and value[0] == provider) else (provider, value)

							# Add the providers, since in certain cases we want to use the Trakt date, since it is more accurate than TMDb/TVDb, because Trakt also has the time, not only the date.
							value = episode.get('year')
							episode['year'] = tuple(value) if (Tools.isArray(value) and value[0] == provider) else (provider, value) if value else None
							value = episode.get('date')
							episode['date'] = tuple(value) if (Tools.isArray(value) and value[0] == provider) else (provider, value) if value else None
							value = episode.get('time')
							episode['time'] = tuple(value) if (Tools.isArray(value) and value[0] == provider) else (provider, value) if value else None

							self._createAppend(data = episodeTree, key = [numberSeason, numberEpisode], values = episode)

			if not self._checkDelay(check = check): return False

			# Do not assemble data from different providers purley on the season/episode number, since the numbering can be different on providers, especially for specials.
			#	Eg: GoT S00E56 (Trakt vs TVDb)
			# Combined/uncombined episodes also have different orders.
			#	Eg: Star Wars: Young Jedi Adventures (Trakt vs TVDb)
			for numberSeason, season in episodeTree.items():
				if not self._checkDelay(check = check): return False
				supported = self._extract(supports, numberSeason)
				for numberEpisode, episode in season.items():
					# Determine the best provider for the episode, depending on the season support and whether or not the specific episode is available from the provider.
					# Prefer the providers with ID+number, then ID only, then number only, then the rest.
					# This is mainly for TMDb which does not have detailed episode metadata, but the episodes numbers are created automatically from the season episode count.
					# This might not always be correct, especially for S00, since the episode number and episode count do not always match.
					# Eg: GoT S00E08 is not available on Trakt/TMDb (at least not the specific number S00E08), but Gaia generates a dummy episode object in MetaTmdb.pack(), containing only the episode number S00E08, but not any IDs/titles (except for S01).
					support, default = self._createSupport(data = episode, support = supported)

					# Only update the metadata of an episode if we are certain the items in the "episode" list are all for the same episode.
					# An episode is considered valid if either the IDs or the title match. If just the season/episode numbers match, it is not considered valid.
					# If not, do not use those incorrect episodes for the metadata update. These number-only-matches will be filled in later.
					# Eg: GoT S00E56 and S00E08 (TVDb vs Trakt/TMDb).
					if default:
						# First collect all the IDs.
						# Eg: TVDb only has the TVDb ID. TMDb only has the TMDb ID. Trakt typically has all IDs.
						# Iterate over all objects once, to make sure we have all the IDs.
						ids = Tools.copy(self._extractId(default, default = {}), deep = False)
						for i in episode:
							if not i is default:
								for j in providers:
									id = self._extractId(i, j)
									if id and id == self._extract(ids, j):
										ids2 = self._extract(i, 'id')
										if ids2: ids = Tools.update(ids, ids2, none = False)
										break

						temp = [default]

						# Add the episode to the unknowns if only one provider has them.
						# Eg: GoT S00E08.
						# Only add them if there is only one ID available. Otherwise this would add too many episodes too the unknowns, which ends up increasing title matching 10 times, slowing down pack creation.
						if len(episode) == 1 and len([i for i in ids.values() if i]) == 1:
							if not numberSeason in episodeUnmatched: episodeUnmatched[numberSeason] = {}
							if not numberEpisode in episodeUnmatched[numberSeason]: episodeUnmatched[numberSeason][numberEpisode] = []
							episodeUnmatched[numberSeason][numberEpisode].append(episode[0])
						else:
							title = self._extractTitle(default)
							time = self._extractCombined(data = default, key = 'time', preference = MetaPack.ProviderTrakt, common = True, minimum = True)

							for i in episode:
								if not i is default:
									matched = None
									match = False
									checker = 0
									title2 = self._extractTitle(i)

									# Match by non-None ID.
									if not match:
										for j in providers:
											id = self._extract(ids, j)
											if id and self._extractId(i, j) == id:
												# Trakt has some incorrect IDs for certain specials.
												# Eg: Downton Abbey S00E12 vs S0013 (Trakt vs TVDb). For S00E12 Trakt has the TVDb ID for the "Downton Abbey" movie which is S00E13 on TVDb.
												# Check if the title matches before considering them a match.
												# Do not only match the title, since some specials are correct, but have different titles.
												# Eg: Downton Abbey S00E08 - "Downton Abbey Text Santa Special" (TVDb) vs "Text Santa 2014" (Trakt).
												# Therefore check the release date first. TVDb and Trakt can have a slight offset in their release date (eg timezone etc). Allow some deviation.
												# Hence, if the release date and the title mismatches, consider them a discrepancy.
												if matched is None:
													matched = True
													if title2 and numberSeason == 0 and time:
														time2 = self._extractCombined(data = i, key = 'time', preference = MetaPack.ProviderTrakt, common = True, minimum = True)
														if time2 and abs(time - time2) > 604800: # 1 week.
															checker += 1
															if self.match(data = title2, title = title, combined = True, quick = True, exact = True, detail = True).get('match') < 0.5:
																self._createUpdate(data = discrepancies, key = [numberSeason, numberEpisode], value = True)
																matched = False

												match = matched
												break

									# Match by non-None title.
									if not match and title and title2:
										checker += 1
										if self.match(data = title2, title = title, combined = True, quick = True):
											match = True

									self._checkIncrement(count = checker)

									# New unaired episode on TMDb that were not scraped by Trakt yet.
									# Eg: One Piece S22E1136+S22E1137 are on TMDb already, but Trakt only goes to S22E1135 at that point.
									try:
										if not match and numberSeason > 0 and self._extractId(i, MetaPack.ProviderTmdb) and not self._extractId(i, MetaPack.ProviderTvdb):
											if not self._extractNumber(i, MetaPack.NumberStandard, provider = MetaPack.ProviderTmdb) == [numberSeason, numberEpisode]:
												# Probably not needed, but only do this for future or recently released episodes.
												date = self._extract(data = i, key = 'time')
												if date and Tools.isArray(date): date = date[1]
												if not date or date > current or abs(date - date) < 1209600: # 14 days.
													temp.append(i)
													if temp and temp[0] == default:
														try: del temp[0]
														except: pass
													continue
									except: Logger.error()

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
						'incorrect'	: self._extractList(data = episode, key = MetaPack.ValueIncorrect, default = []),
						'type'		: {},
						'interval'	: None,

						'serie'		: self._extractProvider(data = episode, key = 'serie'),
						'status'	: self._extractStatus(data = episode, unique = True),
						'title'		: self._createTitle(data = episode, language = language, setting = setting),

						'year'		: self._extractProvider(data = episode, key = 'year', unique = True),
						'date'		: self._extractProvider(data = episode, key = 'date', unique = True),
						'time'		: self._extractProvider(data = episode, key = 'time', unique = True),

						# Do not use _extractMaximum(), since some episodes have a 1 minute runtime difference between Trakt and TVDb.
						# We want to use the duration from the preferred provider.
						# Eg: Westworld S02E03.
						'duration'	: self._extractDuration(data = episode),
					}

					season[numberEpisode] = item
					episodeList.append(item)

			if not self._checkDelay(check = check): return False

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
						'incorrect'	: self._extractList(data = episode, key = MetaPack.ValueIncorrect, default = []),
						'type'		: {},
						'interval'	: None,

						'serie'		: self._extractProvider(data = episode, key = 'serie'),
						'status'	: self._extractStatus(data = episode, unique = True),
						'title'		: self._createTitle(data = episode, language = language, setting = setting),

						'year'		: self._extractProvider(data = episode, key = 'year', unique = True),
						'date'		: self._extractProvider(data = episode, key = 'date', unique = True),
						'time'		: self._extractProvider(data = episode, key = 'time', unique = True),

						'duration'	: self._extractDuration(data = episode),
					}

			# Create a lookup by episode IDs.
			# Make things easier if there is a huge number mismatch between seasons.
			# Eg: One Piece S01E09 (Trakt) vs S02E01 (TVDb).
			# Add lookups for episodes that exist on TVDB, but not on Trakt, and we want to add the Trakt number to it.
			# Eg: One Piece S02E17 (TVDb) vs S01E25 (Trakt)
			# Also improves pack generation speed, since we have to do less title matching, since many of the unfound episodes can be quickly looked up using the lookup tables.
			expression = self._expression(2)
			for structure in [episodeTree, episodeUnmatched, episodeUnknown]: # Place episodeTree before episodeUnmatched/episodeUnknown, since they typically contain more detailed metadata (eg: episodeTree with Trakt data cotnaining multiple IDs vs episodeUnmatched/episodeUnknown with only TVDb ID).
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
									if j and not Regex.match(data = j, expression = expression, cache = True):
										if not j in episodeTitle: episodeTitle[j] = []
										if not i in episodeTitle[j]: episodeTitle[j].append(i)

			if not self._checkDelay(check = check): return False

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

			# There can be many additional episodes added during the previous few steps.
			# Especially if season-absolute-episode numbers (eg: S03E1045) are used, there are 1000s of NumberAutomatic episodes added.
			# Recalculate the "excessive" value here again with all extra added episodes.
			# One Piece: 3555 (1150 actual episodes)
			# Pokémon: 2800 (1300 actual episodes)
			# Good times, bad times (german soap): 24500 (8300 actual episodes)
			if not excessive: excessive = len(episodeList) > 7000

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 6 - Combine the metadata for episodes across different seasons, based on their IDs and titles.
			################################################################################################################

			# Fill in missing IDs and numbers from other episodes belonging in other seasons (eg: Downton Abbey - S02E09 on IMDb - S00E02 on Trakt).
			episodeSpecial = []
			episodeFirst = []
			episodeLater = []
			combined = [0, 0]
			combinedSeason = {}
			expression = self._expression(6)
			for i in episodeList:
				number = self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason, default = -1)
				if number == 0: episodeSpecial.append(i)
				elif number == 1: episodeFirst.append(i)
				elif number > 1: episodeLater.append(i)

				if number >= 0 and not number in combinedSeason: combinedSeason[number] = False
				title = i.get('title')
				if title:
					combined[0] += 1
					for j in title:
						if '/' in j or '|' in j:
							combined[1] += 1
							if number >= 0: combinedSeason[number] = True
							break
						elif number >= 0 and Regex.match(data = j, expression = expression, cache = True):
							combinedSeason[number] = True
			combined = combined[1] > (combined[0] * 0.2)

			# Use a larger threshold for combined/uncombined episodes, since the episode count in the season can be more than 2x between Trakt and TVDb.
			# Eg: Star Wars: Young Jedi Adventures - metadataNext() - S01E48 -> S01E49
			threshold = MetaPack.ThresholdSequential
			if combined: threshold *= 2.5 # A bit more than 2.

			# Create a map for unknown/unmatched episodes and a map with IDs.
			# This saves a little bit of time in the nested loops below.
			mapEpisode = {}
			mapEpisodes = {}
			mapUnmatched = {}
			mapUnknown = {}
			mapIdKnown = {}
			mapIdUnknown = {}
			checker = 0
			for numberSeason in episodeTree.keys():
				if not numberSeason in mapEpisode:
					# Reduce the episodes (and therefore titles) that have to be matched.
					# In the strictest sense, we only have to scan the same season of the current episode, and not all the other seasons.
					# But still include S00 for specials that are placed elsewhere (eg Downton Abbey S05E09 on IMDb).
					if numberSeason == 0:
						episodeSet = episodeSpecial
					else:
						episodeCurrent = list(episodeTree.get(numberSeason).values())
						if excessive:
							episodeSet = episodeCurrent
						else:
							if sequential: # Eg: Dragon Ball Supper S01E16 vs S02E02 (TVDb uses season numbers, Trakt/TMDb use absolute numbers).
								if numberSeason == 1: episodeSet = episodeCurrent + episodeLater + episodeSpecial
								else: episodeSet = episodeCurrent + episodeFirst + episodeSpecial
							else:
								episodeSet = episodeCurrent + episodeSpecial
					unknown = episodeUnknown.get(numberSeason)
					if unknown: episodeSet.extend(unknown.values())

					mapEpisodes[numberSeason] = episodeSet

					ids = {i : {} for i in providersExtended}
					for episode in episodeSet:
						id = self._extractId(episode)
						if id:
							for i in providersExtended:
								id2 = id.get(i)
								if id2: ids[i][id2] = episode
					mapEpisode[numberSeason] = ids

				if not numberSeason in mapIdKnown:
					# This loop takes around 95% of the time to generate packs for very large shows.
					# Even if only IDs are used, without title matching.
					# Only use the episodes which have the same standard season number.
					# This drastically reduces the time for this loop, although some cross-season episodes might not get matched.
					# Eg: Good times, bad times (german soap)
					episodeList3 = episodeTree.get(numberSeason).values()
					if excessive: episodeList2 = episodeList3
					else: episodeList2 = episodeList
					ids = {i : {} for i in providersExtended}
					for episode in episodeList2:
						id = self._extractId(episode)
						if id:
							for i in providersExtended:
								id2 = id.get(i)
								if id2: ids[i][id2] = episode
					mapIdKnown[numberSeason] = ids

				if not numberSeason in mapIdUnknown:
					ids = {i : {} for i in providersExtended}
					for _, season in episodeUnknown.items():
						for _, episode in season.items():
							id = self._extractId(episode)
							if id:
								for i in providersExtended:
									id2 = id.get(i)
									if id2: ids[i][id2] = episode
					mapIdUnknown[numberSeason] = ids

				if not numberSeason in mapUnmatched or not numberSeason in mapUnknown:
					if excessive:
						numberMinimum = numberSeason
						numberMaximum = numberSeason
					else:
						numberMinimum = max(1, numberSeason - 1) # Exclude S00.
						numberMaximum = numberSeason + 1

					if not numberSeason in mapUnmatched:
						values = []
						custom = [episodeUnmatched.get(numberSeason)]
						if not numberSeason == numberMinimum: custom.append(episodeUnmatched.get(numberMinimum))
						for u in custom:
							if u:
								for i in u.values():
									for j in i:
										numberCurrent = self._extractNumber(j, MetaPack.NumberStandard, part = MetaPack.PartSeason)
										if numberCurrent and numberCurrent >= numberMinimum and numberCurrent <= numberMaximum:
											values.append(j)
						mapUnmatched[numberSeason] = values

					if not numberSeason in mapUnknown:
						values = []
						custom = [episodeUnknown.get(numberSeason)]
						if not numberSeason == numberMinimum: custom.append(episodeUnknown.get(numberMinimum))
						for u in custom:
							if u:
								for i in u.values():
									numberCurrent = self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason)
									if numberCurrent and numberCurrent >= numberMinimum and numberCurrent <= numberMaximum:
										values.append(i)
						mapUnknown[numberSeason] = values

				checker += 1
			self._checkIncrement(count = checker)

			for provider, item in base:
				for episode in episodeList:
					if not self._checkDelay(check = check): return False

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
						matched = False
						unided = []

						# In certain cases we can use the detected episode directly for "found".
						# Otherwise a lot of computational power (eg: title matching) is used to first determine the value of "contains", only to then do all the scanning again to get "found".
						contains = False
						contained1 = None
						contained2 = None

						# Do not fill the data if an episode does not even exist on the current provider.
						# Otherwise we have to do a lot of unnecessary title matching for episodes that technically are not on available from the provider.
						if sequential: contains = True # Assume the episode is contained for shows with where some providers use sequential numbering while others use season numbering.
						elif discrepancy: contains = True # Some specials have discrepancies between their IDs and numbers.
						elif title:
							# Do this only for "numberSeason == 0".
							#	Eg: The Office (India) S00E01 vs S01E01
							#	Eg: Star Wars: Young Jedi Adventures S01 (extra uncombined TVDb episodes)
							if numberSeason == 0:
								if not contains:
									unmatched = episodeUnmatched.get(numberSeason) # Eg: GoT S00E08
									if unmatched:
										# Eg: GoT S00E08
										checker = 0
										for i in unmatched.values():
											for j in i:
												checker += 1
												title2 = self._extractTitle(j)
												if title2 and self.match(data = title2, title = title, combined = True, quick = True, exact = True):
													contained2 = j
													contains = True
													break
											if contains: break
										self._checkIncrement(count = checker)
								if not contains:
									unknown = episodeUnknown.get(numberSeason) # Eg: Downton Abbey S00E12 vs S00E13 (TVDb vs Trakt).
									if unknown:
										# Same as the "elif discrepancy:" statement above, but from the other side/episode of the ID/number discrepancy.
										# Eg: Downton Abbey S00E13 - make sure the Trakt data (S00E12) is added to the TVDb data (S00E13).
										# Eg: The Office (India) - TVDb has the pilot as S00E01, while Trakt/TMDb have it as S01E01 and therefore have one more episode in S01.
										checker = 0
										for i in unknown.values():
											checker += 1
											title2 = self._extractTitle(i)
											if title2 and self.match(data = title2, title = title, combined = True, quick = True, exact = True):
												contained2 = i
												contains = True
												break
										self._checkIncrement(count = checker)

							# Or for 1 season above or below the current season.
							#	Eg: LEGO Masters S04E19 (TVDb) vs S05E04 (Trakt/TMDb which does not have the TVDb ID for S05E04, even if it has the TVDb ID for S05E01-03)
							# Also include the previous season's unmatched/unknown values if there is a season discrepancy between Trakt and TVDb.
							# Only include the previous season, since adding too many items to be title-matched can drastically increase computational time.
							# And if there are discrepancies, it typically means TVDb has the episode in the previous season, not the next season.
							# Unsure if this is always the case.
							# Just this code makes the entire pack generation take 20% longer.
							# Hence, use matchExact() which matches raw titles as raw strings without a the use of computationally expensive matching algorithms.
							# This is considerably faster, only adding a few milliseconds to the pack generation time.
							elif numberSeason >= 1:
								for structure in (mapUnmatched, mapUnknown):
									if not contains:
										checker = 0
										structure2 = structure.get(numberSeason)
										if structure2:
											for i in structure2:
												# Sometimes Trakt has the incorrect title.
												# Eg: Good times, bad times S21E218 (Trakt/TMDb "Pia ist zurück") vs S21E4980 (TVDb "Pia ist zurück").
												# Also ignore if there is no sequential number (on TMDb), since titles of episodes in different seasons can match.
												# Eg: Good times, bad times S2003E2742 vs S2025E8299
												if numberSequential:
													numberSequential2 = self._extractNumber(i, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
													if not numberSequential2 or abs(numberSequential - numberSequential2) > threshold: continue

												checker += 1
												title2 = self._extractTitle(i)
												if title2:
													# Match non-exact if it is a combined title.
													# Eg: Star Wars: Young Jedi Adventures S02E21 does not have a TVDb ID on Trakt and is therefore matched by title (combined vs uncombined).
													if self.matchExact(data = title2, title = title):
														contained2 = i
														contains = True
														matched = True
														break
													elif combined and self.match(data = title2, title = title, combined = True, quick = True):
														contained2 = i
														contains = True
														# Not not set this for combined titles.
														# Eg: Star Wars: Young Jedi Adventures S01E35.
														# if not combined: matched = True
														break

											self._checkIncrement(count = checker)

						# For episodes that are in very different seasons, but they have the same ID.
						# Eg: Pokémon (TVDb ID 6436079): S21E01 (Trakt/TMDb) - S18E44 (TVDb)
						# The episode number S21E01 exists on Trakt, but not on TVDb.
						# The episode number S18E44 exists on both and TVDb.
						# The episode therefore ends up in episodeUnknown.
						if not contains:
							ids = mapIdUnknown.get(numberSeason)
							if ids:
								episode2 = None
								if episode2 is None and checkImdb: episode2 = ids.get(MetaPack.ProviderImdb).get(checkImdb)
								if episode2 is None and checkTmdb: episode2 = ids.get(MetaPack.ProviderTmdb).get(checkTmdb)
								if episode2 is None and checkTvdb: episode2 = ids.get(MetaPack.ProviderTvdb).get(checkTvdb)
								if episode2 is None and checkTrakt: episode2 = ids.get(MetaPack.ProviderTrakt).get(checkTrakt)
								if episode2 and not episode is episode2:
									# Sometimes Trakt has the incorrect TMDb ID, which causes an incorrect match.
									# Eg: Vikings S00E27 and S00E56 both have the TMDb ID 4111049 on Trakt.
									# If the TMDb ID matches, but the Trakt ID does not, assume it is not a match.
									# If necessary, this could also be done for other IDs (TVDb/IMDb).
									if not(checkTmdb and checkTrakt and checkTmdb == self._extractId(episode2, MetaPack.ProviderTmdb) and not checkTrakt == self._extractId(episode2, MetaPack.ProviderTrakt)):
										contained1 = episode2
										contains = True
										unided.append(episode2)

						# For episodes that are in very different seasons, but they have the same ID.
						# Eg: Pokémon (TVDb ID 8082533): S24E02 (Trakt/TMDb) - S19E50 (TVDb)
						# The episode number S24E02 exists on Trakt, but not on TVDb.
						# The episode number S19E50 exists on TVDb, but not on Trakt.
						# The episode therefore does not end up in episodeUnknown, but is in episodeList.
						if not contains:
							ids = mapIdKnown.get(numberSeason)
							if ids:
								episode2 = None
								if episode2 is None and checkImdb: episode2 = ids.get(MetaPack.ProviderImdb).get(checkImdb)
								if episode2 is None and checkTmdb: episode2 = ids.get(MetaPack.ProviderTmdb).get(checkTmdb)
								if episode2 is None and checkTvdb: episode2 = ids.get(MetaPack.ProviderTvdb).get(checkTvdb)
								if episode2 is None and checkTrakt: episode2 = ids.get(MetaPack.ProviderTrakt).get(checkTrakt)
								if episode2 and not episode is episode2:
									# Sometimes Trakt has the incorrect TMDb ID, which causes an incorrect match.
									# Eg: Vikings S00E27 and S00E56 both have the TMDb ID 4111049 on Trakt.
									# If the TMDb ID matches, but the Trakt ID does not, assume it is not a match.
									# If necessary, this could also be done for other IDs (TVDb/IMDb).
									if not(checkTmdb and checkTrakt and checkTmdb == self._extractId(episode2, MetaPack.ProviderTmdb) and not checkTrakt == self._extractId(episode2, MetaPack.ProviderTrakt)):
										contained1 = episode2
										contains = True
										unided.append(episode2)

						# Try finding by season-episode numbers.
						if not contains:
							# If the number of a provider is missing, but the the ID of the provider is available, we know the episode has a number mismatch and we should search for the episode elsewhere.
							# Eg: GoT S00E08 (TVDb) vs S00E211 (Trakt/TMDb)
							if id and numberProvider is None:
								contains = True
							else:
								# Do not match by number if it is an new unaired episode on TMDb that was not scraped by Trakt yet.
								# Eg: One Piece S22E1136+S22E1137 are on TMDb already, but Trakt only goes to S22E1135 at that point.
								allow = True
								if self._extractId(episode, MetaPack.ProviderTmdb) and len([j for j in self._extractId(episode).values() if j]) == 1:
									if not self._extractNumber(episode, MetaPack.NumberStandard) == self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTmdb):
										allow = False

								if allow:
									checker = 0
									for i in self._extractSeasons(item):
										if self._extractNumber(i, MetaPack.NumberStandard) == numberSeason:
											time1 = self._extractCombined(data = episode, key = 'time', common = True, minimum = True)
											for j in self._extractEpisodes(i):
												if not episode is j:
													checker += 1
													# The episode number between Trakt and TVDb sometimes matches, but the episodes are not the same.
													# Eg: One Piece S22E47 (Trakt) is not S22E47 (TVDb), but S22E50 (TVDb).
													# Ignore if the titles do not match.
													# Note that some shows will return titles in different languages.
													# Eg: Good times bad times.
													# Hence, only do this for "absolution" shows.
													matchStandard = self._extractNumber(j, MetaPack.NumberStandard, part = MetaPack.PartEpisode) == numberEpisode

													# Try finding by sequential numbers.
													# Eg: Good times, bad times S13E02+ (TVDb uses absolute episode numbers, Trakt does not have the TVDb IDs, and the titles between TVDb and Trakt do not match).
													matchSequential = numberSequential and not numberSeason == 0 and self._extractNumber(j, MetaPack.NumberSequential, part = MetaPack.PartEpisode) == numberSequential

													if matchStandard or matchSequential:
														allow2 = True

														# Do not do this for some episodes:
														# Eg: The Tonight Show Starring Jimmy Fallon S06E58.
														# But do it for other episodes:
														# Eg: The Tonight Show Starring Jimmy Fallon S12E162.
														if self._extractId(j, MetaPack.ProviderTvdb) and not self._extractId(j, MetaPack.ProviderTrakt):
															absolutionTvdb = absolution.get(MetaPack.ProviderTvdb)
															absolutionTrakt = absolution.get(MetaPack.ProviderTrakt)
															yearTvdb = seasonYear.get(MetaPack.ProviderTvdb)
															yearTrakt = seasonYear.get(MetaPack.ProviderTrakt)
															if (absolutionTvdb and not yearTvdb) or (absolutionTrakt and not yearTrakt) or (not absolutionTvdb and not absolutionTrakt and not yearTvdb and not yearTrakt):
																checker += 1
																title2 = self._extractTitle(j)
																# Allow generic title matching, to match "Episode 1" (Trakt) with "1" (TVDb).
																if title2 and not self.match(data = title2, title = title, combined = True, quick = True, exact = True, generic = True):
																	# Sometimes the title does not match, but the episode is the same.
																	# If the title does not match, but the date is the same, assume it is the correct episode.
																	# Eg: QI S22E09 - "Variety" (Trakt) vs "Christmas Special" (TVDb).
																	if checkTrakt and incorrectTrakt.get(checkTrakt):
																		time2 = self._extractCombined(data = j, key = 'time', common = True, minimum = True)
																		if not time1 or not time2 or abs(time1 - time2) > 86400: # 24 hours.
																			allow2 = False
																	else:
																		allow2 = False

														if allow2:
															if matchSequential or (matchStandard and not(numberSeason == 0 or combined)): contained1 = j
															contains = True
															break
											break
									self._checkIncrement(count = checker)

						# If the episode is a normal/standard episode on Trakt, but a special on TVDb, and Trakt does not have the TVDb ID yet.
						# Eg: QI S22E15-16 (Trakt) -> S00E15-16 (TVDb) - Trakt does not have the TVDb ID yet, but might get it in the future, so this code will not apply anymore.
						# Only do this if the date of the two episodes are close, since some shows (eg: QI) use ther same/similar titles for mutiple episodes in different seasons (eg: "VG: Part 1").
						if not contains and numberSeason > 0 and title:
							unknown = episodeUnknown.get(0)
							if unknown:
								time1 = self._extractCombined(data = episode, key = 'time', common = True, minimum = True)
								if time1:
									checker = 0
									for i in unknown.values():
										checker += 1
										time2 = self._extractCombined(data = i, key = 'time', common = True, minimum = True)
										if time1 and time2 and abs(time1 - time2) < 7884000: # 3 months.
											title2 = self._extractTitle(i)

											# parenthese = True: Ignore everything after parenthese. Eg: "VG: Part 1 (Series V)" -> "VG: Part 1".
											# roman = True: Convert roman numbers Eg: "VG: Part II (Series S)" -> "VG: Part 2 (Series S)".
											if title2 and self.match(data = title2, title = title, combined = True, quick = True, exact = True, parenthese = True, roman = True):
												contained1 = i
												contains = True
												break
									self._checkIncrement(count = checker)

						# If Trakt does not have the TVDb ID yet and the title does not match exactly.
						# Only do this if the season/episode numbers are the same and the date is very close, since a very low title matching threshold is used below.
						# Eg: The Late Show with Stephen Colbert S11E10: "Jake Tapper, St. Vincent" (Trakt) vs "Jake Tapper, David Remnick" (TVDb).
						if not contains and numberSeason > 0 and not checkTvdb and title:
							structure = mapUnknown.get(numberSeason)
							if structure:
								checker = 0
								for i in structure:
									if self._extractId(i, provider = MetaPack.ProviderTvdb) and len([j for j in self._extractId(i).values() if j]) == 1:
										if numberSeason == self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason) and numberEpisode == self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartEpisode):
											time1 = self._extractCombined(data = episode, key = 'time', common = True, minimum = True)
											if time1:
												time2 = self._extractCombined(data = i, key = 'time', common = True, minimum = True)
												if time2 and abs(time1 - time2) < 172800: # 2 days.
													checker += 1
													title2 = self._extractTitle(i)
													if title2 and self.match(data = title2, title = title, detail = True).get('match') > 0.35:
														contained1 = i
														contains = True
														matched = True
														break
								self._checkIncrement(count = checker)

						if contains:
							found = []
							if contained1: found.append(contained1)

							# Firstly, try to find a match by ID. This is the most accurate.
							# Trakt can have an episode in absolute order, but still contain the correct TVDb ID to the episode in a different season.
							if not found and not discrepancy:
								if id:
									extra = episodeId[provider].get(id)
									if extra:
										extra = [i for i in extra if not i is episode]
										if extra:
											checker = 0
											for episode2 in extra:
												checker += 1
												id2 = self._extractId(episode2)
												if id2:
													if (checkImdb and checkImdb == id2.get(MetaPack.ProviderImdb)) or (checkTmdb and checkTmdb == id2.get(MetaPack.ProviderTmdb)) or (checkTvdb and checkTvdb == id2.get(MetaPack.ProviderTvdb)) or (checkTrakt and checkTrakt == id2.get(MetaPack.ProviderTrakt)):
														try:
															# Trakt sometimes has the wrong TVDb ID.
															# Eg: Good times, bad times - Trakt S01E04 (TVDb ID 4204280, which is S1995E648/S04E01 on TVDb)
															if numberSeason > 0 and checkTvdb and checkTvdb == id2.get(MetaPack.ProviderTvdb):
																if abs(numberSequential - self._extractNumber(episode2, MetaPack.NumberSequential, part = MetaPack.PartEpisode)) > threshold:
																	# Remove the invalid ID, so it can be matched by other means.
																	if id2.get(MetaPack.ProviderTrakt): episode2['id'][MetaPack.ProviderTvdb] = None
																	elif checkTrakt: episode['id'][MetaPack.ProviderTvdb] = None
																	continue
														except: pass
														found.append(episode2)
														break
											self._checkIncrement(count = checker)
								if not found:
									ids = mapEpisode.get(numberSeason)
									if ids:
										episode2 = None
										if episode2 is None and checkImdb: episode2 = ids.get(MetaPack.ProviderImdb).get(checkImdb)
										if episode2 is None and checkTmdb: episode2 = ids.get(MetaPack.ProviderTmdb).get(checkTmdb)
										if episode2 is None and checkTvdb: episode2 = ids.get(MetaPack.ProviderTvdb).get(checkTvdb)
										if episode2 is None and checkTrakt: episode2 = ids.get(MetaPack.ProviderTrakt).get(checkTrakt)
										if episode2 and not episode is episode2:
											skip = False
											try:
												# Trakt sometimes has the wrong TVDb ID.
												# Eg: Good times, bad times - Trakt S01E04 (TVDb ID 4204280, which is S1995E648/S04E01 on TVDb)
												if numberSeason > 0 and checkTvdb and checkTvdb == id2.get(MetaPack.ProviderTvdb):
													if abs(numberSequential - self._extractNumber(episode2, MetaPack.NumberSequential, part = MetaPack.PartEpisode)) > threshold:
														# Remove the invalid ID, so it can be matched by other means.
														if id2.get(MetaPack.ProviderTrakt): episode2['id'][MetaPack.ProviderTvdb] = None
														elif checkTrakt: episode['id'][MetaPack.ProviderTvdb] = None
														skip = True
											except: pass
											if not skip: found.append(episode2)
								if unided:
									checker = 0
									for episode2 in unided:
										if not episode is episode2:
											checker += 1
											id2 = self._extractId(episode2)
											if id2:
												if (checkImdb and checkImdb == id2.get(MetaPack.ProviderImdb)) or (checkTmdb and checkTmdb == id2.get(MetaPack.ProviderTmdb)) or (checkTvdb and checkTvdb == id2.get(MetaPack.ProviderTvdb)) or (checkTrakt and checkTrakt == id2.get(MetaPack.ProviderTrakt)):
													try:
														# Trakt sometimes has the wrong TVDb ID.
														# Eg: Good times, bad times - Trakt S01E04 (TVDb ID 4204280, which is S1995E648/S04E01 on TVDb)
														if numberSeason > 0 and checkTvdb and checkTvdb == id2.get(MetaPack.ProviderTvdb):
															if abs(numberSequential - self._extractNumber(episode2, MetaPack.NumberSequential, part = MetaPack.PartEpisode)) > threshold:
																# Remove the invalid ID, so it can be matched by other means.
																if id2.get(MetaPack.ProviderTrakt): episode2['id'][MetaPack.ProviderTvdb] = None
																elif checkTrakt: episode['id'][MetaPack.ProviderTvdb] = None
																continue
													except: pass
													found.append(episode2)
													break
									self._checkIncrement(count = checker)

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
										if j:
											for k in j:
												try:
													# Ignore episodes if one is in S0 and the other in S01+.
													episodeSeason = self._extractNumber(k, MetaPack.NumberStandard, part = MetaPack.PartSeason)
													if (numberSeason and not episodeSeason) or (not numberSeason and episodeSeason): continue

													# Ignore if the sequential number difference is too great, even if the titles matches.
													# Since this typically indicates a different episode with the same title.
													# Eg: Good times, bad times (TVDb S2013E5371 vs S2016E6001)
													# Eg: Good times, bad times (TVDb S2014E5480 vs S2016E6138)
													# Also ignore if there is no sequential number (on TMDb), since titles of episodes in different seasons can match.
													# Eg: Good times, bad times S2003E2742 vs S2025E8299
													numberSequential2 = self._extractNumber(k, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
													if numberSeason and (not numberSequential or not numberSequential2): continue
													if abs(numberSequential - numberSequential2) > threshold: continue
												except: pass
												extra.append(k)
									if extra:
										extra = Tools.listUnique([i for i in extra if not i is episode])

										# NB: Limit the number of episodes added here for specials.
										# Some shows have many episodes with the exact same title.
										# This causes many episodes to be added to "found", many of them completely different episodes.
										# When the episode metadata is then merged below with "found", this causes a sudden massive increase in CPU usage and after a few seconds Kodi crashes.
										# Eg: RuPaul's Drag Race (tt1353056)
										#	36 specials with title "Whatcha Packin' With Michelle Visage", probably a mistake on Trakt.
										#	But also many other episodes in S01-S17 where there are 5+ episodes with the same title (eg "Reunited", "Grand Finale").
										# Update: This might have been caused by the recursive increase of duplicate values for year/date/time/serie/status when episode dicts are merged.
										# The duplicate values are now filtered out and should not increase the various lists with every episode merger.
										#found.extend(extra)
										if len(extra) <= 5: found.extend(extra)

									if not found and contained2:
										numberSequential2 = self._extractNumber(contained2, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
										if numberSequential and numberSequential2 and abs(numberSequential - numberSequential2) <= threshold:
											id2 = self._extractId(contained2)
											if id2:
												# Do not use if the IDs mismatch.
												allow = True
												if checkImdb and id2.get(MetaPack.ProviderImdb) and not checkImdb == id2.get(MetaPack.ProviderImdb): allow = False
												elif checkTmdb and id2.get(MetaPack.ProviderTmdb) and not checkTmdb == id2.get(MetaPack.ProviderTmdb): allow = False
												elif checkTvdb and id2.get(MetaPack.ProviderTvdb) and not checkTvdb == id2.get(MetaPack.ProviderTvdb): allow = False
												elif checkTrakt and id2.get(MetaPack.ProviderTrakt) and not checkTrakt == id2.get(MetaPack.ProviderTrakt): allow = False
												if allow: found.append(contained2)

									if not found:
										checker = 0
										for episode2 in ((mapEpisodes.get(numberSeason) or []) + (unided or [])):
											if not episode is episode2:
												checker += 1

												# If mutiple episodes have thew same title, but are different episodes (eg they have a different Trakt ID).
												# Eg: Money Heist S00E01 and S00E14 are both titled "Episode 1" on TMDb, althougfh they are different episodes.
												if checkTrakt:
													idTrakt = self._extractId(episode2, MetaPack.ProviderTrakt)
													if idTrakt and not checkTrakt == idTrakt: continue

												title2 = self._extractTitle(episode2)
												# Do not use "exact = True" for match() here, since it actually increases time.
												if title2 and self.match(data = title2, title = title, combined = True, quick = True):
													try:
														# Ignore if the sequential number difference is too great, even if the titles matches.
														# Since this typically indicates a different episode with the same title.
														# Eg: Good times, bad times (TVDb S2013E5371 vs S2016E6001)
														# Eg: Good times, bad times (TVDb S2014E5480 vs S2016E6138)
														# Also ignore if there is no sequential number (on TMDb), since titles of episodes in different seasons can match.
														# Eg: Good times, bad times S2003E2742 vs S2025E8299
														numberSequential2 = self._extractNumber(episode2, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
														if numberSeason and (not numberSequential or not numberSequential2): continue
														if abs(numberSequential - numberSequential2) > threshold: continue
													except: pass

													found.append(episode2)
													break
										self._checkIncrement(count = checker)

							# Thirdly, try to find by season/episode number.
							# This is the least accurate, since providers can have missing seasons, missing episodes, different episode numbering, combined/uncombined episodes, etc.
							# Only use the "unknown" episodes that were previously not combined into the "episode" object.
							# This should mostly be TMDb (non-S01) objects.
							# Only do this for Specials if there is no discrepancy between the number of special episodes, since the numbering can differ.
							# Eg: Downton Abbey S00E12 vs S00E13 (TVDb vs Trakt).
							# NB: Only do this if not found yet, otherwise there is an issue combining The Office (India) S00E01 (TVDb) vs S01E01 (Trakt).
							# Do not do for combined shows.
							# Eg: Star Wars: Young Jedi Adventures S02E22 (TVDb) is different to S02E22 (Trakt).
							if not found and (not numberSeason == 0 or not specialDiscrepancy) and not combined:
								episode2 = episodeUnknown.get(numberSeason, {}).get(numberEpisode)
								if episode2: found.append(episode2)
								if numberSeason >= 1 and not numberEpisode == numberSequential:
									episode2 = episodeUnknown.get(1, {}).get(numberSequential)
									if episode2: found.append(episode2)

							# Sometimes a new or future/unreleased episode does not have a TVDb ID on Trakt yet.
							# Trakt has a Trakt and TMDb (and often also IMDb) ID for the episode, but probably has not scraped TVDb yet to get the latests IDs from there.
							# Typically a few days later, Trakt has the new ID.
							# Eg: One Piece S22E35 only had a Trakt/TMDb/IMDb ID, even a few days after release.
							# Trakt had the episode listed a few weeks before airing, but TVDb only added it a few days before airing.
							# TVDb only had a TVDb ID for this episode, but no other IDs.
							# Hence, we cannot match by ID and have to match these by title.
							if title and numberSeason > 0:
								providers2 = (MetaPack.ProviderTrakt, MetaPack.ProviderTmdb, MetaPack.ProviderTvdb)

								# We technicaly only have to do this for the missing TVDb ID.
								# But also do this for missing Trakt/TMDb IDs, although this should not happen often.
								# We only do this if the episode only has a single missing ID, so that this is not applied to normal TVDb episodes outside of "unknown".
								ids = []
								for provider2 in providers2:
									for episode2 in [episode] + found:
										if self._extractId(episode2, provider2):
											ids.append(provider2)
											break

								# Only do this if a single ID is missing.
								# If multiple IDs are missing
								missing = None
								if len(ids) == 2:
									try: missing = next(i for i in providers2 if not i in ids)
									except: Logger.error() # This should happen.

								if missing:
									episodeSet = []
									if unided: episodeSet.extend(unided)
									unknown = episodeUnknown.get(numberSeason)
									if unknown: episodeSet.extend(unknown.values())
									episodeSet = [i for i in episodeSet if not i is episode]
									if episodeSet:
										checker = 0
										for episode2 in episodeSet:
											checker += 1
											title2 = self._extractTitle(episode2)
											# Do not use "exact = True" for match() here, since it actually increases time.
											if title2 and self.match(data = title2, title = title, combined = True, quick = True):
												if self._extractId(episode2, missing):
													found.append(episode2)
													break
										self._checkIncrement(count = checker)

							# Remove matches that have different provider IDs, meaning this is probably a different episode, even if the title is the same.
							# Eg: Dragon Ball Super S05E56.
							# Eg: Better Call Saul S00E56 vs S01E01.
							# Still allow some episodes with an ID mismatch, since it can simply be that Trakt has the incorrect/old TVDb ID, while TVDb has a new ID.
							# Eg: Money Heist S02E01, S02E03-E07. Trakt has TVDb IDs that all point to an episode that does not exist anymore. TVDb probably did some cleanup and removed some outlier episodes, and Trakt has not synced since then.
							replaceId = []
							if found and not combined:
								temp = []
								for f in found:
									if self.matchCustom(episode, f):
										temp.append(f)
									else:
										# If the ID mismatches, but the title and other attributes match.
										idValid = [k for k, v in self._extractId(f).items() if v]
										if len(idValid) == 1 and MetaPack.ProviderTvdb in idValid:
											title2 = self._extractTitle(f)
											if title2 and self.matchExact(data = title2, title = title):
												time1 = self._extractCombined(data = episode, key = 'time', preference = MetaPack.ProviderTrakt, common = True, minimum = True)
												time2 = self._extractCombined(data = f, key = 'time', preference = MetaPack.ProviderTvdb, common = True, minimum = True)
												if time1 and time2 and abs(time1 - time2) < 79200: # 22 hours.
													replaceId.append(MetaPack.ProviderTvdb)
													temp.append(f)
								found = temp

							if found:
								group = [episode] + found

								# Also update the "found" item with any values that use _extractProvider().
								# Otherwise values for some providers might go missing if there is an episode number mismatch.
								# Eg: One Piece S22E01 (S22E1089 on TMDb). This results in the final S22E01 episode only having a NumberDate for TVDb and Trakt, but not for TMDb.
								update1 = {
									'year'		: self._extractProvider(data = group, key = 'year', unique = True), # unique: remove duplicate values that happen becuase of the constant merger of dicts.
									'date'		: self._extractProvider(data = group, key = 'date', unique = True),
									'time'		: self._extractProvider(data = group, key = 'time', unique = True),
								}
								update2 = {
									'serie'		: self._extractProvider(data = group, key = 'serie', unique = True),
								}

								episode.update({ # Update to keep the reference to the same object in episodeTree.
									'id'		: {
										'imdb'	: self._extractSelect(data = group, key = ['id', 'imdb']),
										'tmdb'	: self._extractSelect(data = group, key = ['id', 'tmdb']),
										'tvdb'	: self._extractSelect(data = group, key = ['id', 'tvdb']),
										'trakt'	: self._extractSelect(data = group, key = ['id', 'trakt']),
									},
									'number'	: self._createNumber(data = group),
									'support'	: self._extractSelect(data = group, key = 'support'),
									'incorrect'	: self._extractList(data = group, key = MetaPack.ValueIncorrect, default = []),
									'type'		: self._extractDict(data = group, key = 'type'),

									'status'	: self._extractStatus(data = group, unique = True),
									'title'		: self._createTitle(data = group, language = language, setting = setting),

									'duration'	: self._extractDuration(data = group),
								})
								episode.update(update1)
								episode.update(update2)

								# Replace TVDb IDs that are incorrectly captured by Trakt.
								if replaceId:
									for x in replaceId:
										newId = self._extractSelect(found, ['id', x])
										if newId: episode['id'][x] = newId

								for f in found:
									# Do not do this if "episode" is a special, while "f" is not.
									# Otherwise the "special" serie types gets added to the standard S01+ episode.
									# Eg: Better Call Saul S01E01 vs S00E56 - both with a title "Uno".
									# Do not add the "special" type from S00E56 to S01E01.
									if not(self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason) == 0 and self._extractNumber(f, MetaPack.NumberStandard, part = MetaPack.PartSeason) > 0):
										f.update(update1)

										# Only update the series type if there is more than 1 provider ID.
										# Eg: Star Wars: Young Jedi Adventures S01E35 on TVDb should not be marked as a midseason finale, since it matches with S01E19 on Trakt which is a midseason finale.
										if len([x for x in (f.get('id') or{}).values() if x]) > 1: f.update(update2)

										# Add missing IDs and numbers.
										# This happens if Trakt does not have the TVDb ID for an episode.
										# Eg: Lego Masters S05E04 (Trakt/TMDb) is S04E19 (TVDb).
										# Only do this if the title was matched strictly ("matched").
										if matched:
											for k, v in episode['id'].items():
												if v and not f['id'].get(k):
													f['id'][k] = v
													if not self._extractNumber(f, MetaPack.NumberStandard, provider = k, part = MetaPack.PartEpisode):
														f['number'][k] = self._extractNumber(episode, provider = k)

					# Only update here, and not in the for-loop above that does the same thing.
					# Since we want to get the "true" absolute number from another provider if available, instead of using the overwritten value that uses the custom calculated number.
					episode['number'] = self._createNumber(data = episode)

					# Interpolate TMDb S0 numbers that we previously filtered out, because there is no extended metadata, so ID/title matching is not possible.
					# Use the Trakt metadata, since it seems Trakt always has the episode numbering and episode metadata from TMDb and not TVDb.
					# Eg: S00E211 (Trakt/TMDb) vs S00E08 (TVDb).
					# Also do this for other seasons, since the absolute number is not available from TMDb, but it is probably the same as Trakt.
					# This is also important if DetailStandard, where MetaTmdb does not return the episode numbers and IDs for S03+.
					# Only do this if there is a TMDb ID on Trakt, meaning Trakt could find the episode on TMDb.
					# Because TMDb sometimes has missing episodes that are on Trakt.
					# Eg: The Tonight Show Starring Jimmy Fallon S03E13.
					# The NumberDate gets copied later on.
					if self._extractId(episode, MetaPack.ProviderTmdb) and self._extractNumber(episode, provider = MetaPack.ProviderTmdb, part = MetaPack.PartEpisode) is None:
						number = self._extractNumber(episode, provider = MetaPack.ProviderTrakt)
						if number:
							if not episode['number'].get(MetaPack.ProviderTmdb): episode['number'][MetaPack.ProviderTmdb] = {}
							episode['number'][MetaPack.ProviderTmdb].update({k : v for k, v in number.items() if not v is None})

							# Also copy the year/date/time from Trakt.
							# This is important to generate NumberDate later on (although we could just copy Trakt's NumberDate), but more importantly to pick the correct date.
							# If there is only a Trakt and TVDb date, for certain shows/episodes the TVDb instead of the Trakt date might be picked otherwise.
							# Sometimes the date between Trakt and TMDb mismatch, typically because TMDb has the incorrect date.
							# Eg: The Tonight Show Starring Jimmy Fallon S04E11 (TMDb - 2017) vs S04E02 (Trakt - 2016).
							# So using the Trakt date number might not always be accurate, but in most cases it should be fine.
							try:
								for x in ['year', 'date', 'time']:
									values = self._extract(episode, x)
									if values:
										found = False
										for y in values:
											if y[0] == MetaPack.ProviderTmdb:
												found = True
												break
										if not found:
											for y in values:
												if y[0] == MetaPack.ProviderTrakt:
													# Copy the list, because sometimes there are episode number mismatches, causing values from different episodes to be added to the same list reference.
													# Eg: Good times bad times S34E98 is 1 episode off (TVDb S2025E8278), causing both 2025-05-22 (S34E98) and 2025-05-21 (S2025E8278) to be added.
													# By copying, adding to the same list from different episodes is eliminated.
													values = Tools.copy(values, deep = False)
													values.append((MetaPack.ProviderTmdb, y[1]))
													episode[x] = values
													break
							except: Logger.error()

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 7 - Combine the metadata for automatic absolute episodes that are not part of any standard season.
			################################################################################################################

			# Fill in the automatically added absolute episodes.
			# Do this AFTER the complex for-loop above.
			# Since we know there are no IDs and titles for matching, only combine the objects without any computational expensive matching.

			# Sort the episodes of each season based on episode number.
			# Certain episodes can be out of orde, such as missing episodes from TMDb are placed after later episodes.
			# We need the episodes sorted for:
			#	1. The missing Trakt episode loop just below.
			#	2. Calculating the episode types, since they use the previous/next episode's types.
			for numberSeason, season in episodeTree.items():
				episodeTree[numberSeason] = {i[0] : i[1] for i in sorted(season.items(), key = lambda x : x[0])}

			# Sometimes Trakt has a missing episode that is on TMDb.
			# This causes the sequential numbers to be off.
			# Trakt actually seems to have the correct absolute number, even if an episode is missing.
			# Eg: One Piece S01E58 (missing on Trakt, but on TMDb and TVDb).
			# Calculate the missing number "offset" at each episode, which is then used to pick the correct episode by sequential number, in order to populate the automatic episodes below.
			# The sequential numbers are adjusted at the end of this step, after the automatic episodes have been processed.
			offset = 0
			offsets = {}
			try:
				for numberSeason, season in episodeTree.items():
					if numberSeason > 0:
						for numberEpisode, episode in season.items():
							numberTrakt = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTrakt)
							numberTmdb = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTmdb)
							numberSequential = self._extractNumber(episode, MetaPack.NumberSequential)
							if not numberTrakt and numberTmdb: offset += 1
							if numberSequential: offsets[numberSequential[MetaPack.PartEpisode]] = offset
			except: Logger.error()

			# First created a lookup table for all sequential numbers.
			# This is WAY faster than doing this as a nested loop within the other loop below.
			# Do this BEFORE the sequential numbers are adjusted below.
			sequentials = {}
			for episode in episodeLater: # Do not use episodeSet.
				numberSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
				if not numberSequential is None: sequentials[numberSequential] = episode

			for episode in episodeList:
				# This can take long for very large packs.
				# Eg: Days of our Lives (26+ million episode items for which the sequential number is extract in the loop below).
				# Update: the sequential number extraction is now done above outside the loop, and the time to process this loop is considerably faster.
				if not self._checkDelay(check = check): return False

				if self._extractType(episode, MetaPack.NumberAutomatic):
					if self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartSeason) == 1:
						numberEpisode = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
						numberSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
						if not numberEpisode and numberSequential: # Data is missing.
							# Pick the sequential number with an offset if any.
							# This makes sure that the correct sequential episode is picked if there is a missing Trakt episode somewhere in the show.
							#found = sequentials.get(numberSequential)
							found = sequentials.get(numberSequential - offsets.get(numberSequential, 0))

							if found:
								missing = False
								for provider, item in base:
									if not self._extractId(episode, provider): # Data is missing.
										missing = True
										break

								if missing:
									group = [episode, found]
									episode.update({
										'id'		: {
											'imdb'	: self._extractSelect(data = group, key = ['id', 'imdb']),
											'tmdb'	: self._extractSelect(data = group, key = ['id', 'tmdb']),
											'tvdb'	: self._extractSelect(data = group, key = ['id', 'tvdb']),
											'trakt'	: self._extractSelect(data = group, key = ['id', 'trakt']),
										},
										'number'	: self._createNumber(data = group),
										'support'	: self._extractSelect(data = group, key = 'support'),
										'incorrect'	: self._extractList(data = group, key = MetaPack.ValueIncorrect, default = []),
										'type'		: self._extractDict(data = group, key = 'type'),

										'serie'		: self._extractProvider(data = group, key = 'serie', unique = True),
										'status'	: self._extractStatus(data = group, unique = True),
										'title'		: self._createTitle(data = group, language = language, setting = setting),

										'year'		: self._extractProvider(data = group, key = 'year', unique = True),
										'date'		: self._extractProvider(data = group, key = 'date', unique = True),
										'time'		: self._extractProvider(data = group, key = 'time', unique = True),

										'duration'	: self._extractDuration(data = group),
									})

									# Overwrite the numbers, since they can be replaced by a different number from certain providers.
									episode['number'][MetaPack.NumberStandard] = [1, numberSequential]
									episode['number'][MetaPack.NumberSequential] = [1, numberSequential]

			# Sometimes Trakt has a missing episode that is on TMDb.
			# This causes the sequential numbers to be off.
			# Trakt actually seems to have the correct absolute number, even if an episode is missing.
			# Eg: One Piece S01E58 (missing on Trakt, but on TMDb and TVDb).
			# Update (2025-12): One Piece S01E58 is back on Trakt, but has a (bracket-part) missing from its label.
			# Calculate the missing number "offset" and adjust the sequential numbers accordingly.
			offset = 0
			previous = None
			previousIncrement = False
			try:
				for numberSeason, season in episodeTree.items():
					if numberSeason > 0:
						for numberEpisode, episode in season.items():
							# Do not do for automatically added episodes.
							# Otherwise automatic/sequential episodes added to S01 (eg: S01E450) is taking into account, which will incorrectly increase offset.
							if not self._extractType(episode, MetaPack.NumberAutomatic):
								numberTrakt = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTrakt)
								numberTmdb = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTmdb)

								numberSequential = self._extractNumber(episode, MetaPack.NumberSequential)
								numberSequentialTmdb = self._extractNumber(episode, MetaPack.NumberSequential, provider = MetaPack.ProviderTmdb)

								# Only do this if the episode is on TMDb, but not on Trakt (yet).
								# This then uses the Trakt sequential number, which does not exist, instead of using the TVDb sequential number that is picked as the main sequential number, because there is no Trakt number.
								# If the TVDb and Trakt sequential numbers are different, it can cause the wrong (TVDb) sequential number to be used. Revert back to the non-existing Trakt sequential number, so it can be manually calculated/incremented here.
								# Eg: The Tonight Show Starring Jimmy Fallon S13E20+ are not yet on Trakt, but on TMDb/TVDb.
								# If there is only a TVDb number, it means that it is an alternative episode.
								# Eg: Star Wars: Young Jedi Adventures - S01E28 (TVDb).
								if not numberTrakt and numberTmdb: numberSequential = self._extractNumber(episode, MetaPack.NumberSequential, provider = MetaPack.ProviderTrakt)

								# Only increase the offset if not previously incremented.
								# Otherwise if the "previous" sequential number is copied below, it can be incremented by too much (by 2+ instead of 1).
								# This happens because "offset" is incremented with each episode, but then also added "+= offset" to the sequential number.
								# If the "previous" number is used/copied, it was already incremented in the previous iteration, and offset should not be incremented anymore.
								# Otherwise "offset" is increased to a value of 2, which is then added to the already-incremented previous sequential number, causing each sequential number to be incremented by more than 1.
								if not numberTrakt and numberTmdb and not previousIncrement:
									# Do not do if the next episode is also not on Trakt, otherwise it might be a mismatch between Trakt and TMDb, and we should ignore the extra TMDb episodes.
									# Eg: Cops S03E41+ (on TMDb and on Trakt as a special)
									# Eg: Cops S04E46+ (on TMDb and not on Trakt)
									# Cops is so messed up between TMDb and Trakt, no effort is going to be made to fix all the inconsistencies.
									episodeNext = season.get(numberEpisode + 1)
									if episodeNext and self._extractNumber(episodeNext, MetaPack.NumberStandard, provider = MetaPack.ProviderTrakt):
										offset += 1
										previousIncrement = True

								if not numberSequential and previous: numberSequential = Tools.copy(previous, deep = False)
								else: previousIncrement = False

								if numberSequential:
									numberSequential[MetaPack.PartEpisode] += offset
									episode['number'][MetaPack.NumberSequential] = numberSequential

									if numberTmdb:
										if not MetaPack.ProviderTmdb in episode['number']: episode['number'][MetaPack.ProviderTmdb] = {}
										episode['number'][MetaPack.ProviderTmdb][MetaPack.NumberSequential] = numberSequential

								previous = numberSequential
			except: Logger.error()

			if not self._checkDelay(check = check): return False

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
			# A quick hack is to simply check if a season contains multiple episodes with the same standard number, and if so, combined them.
			# NB: Not sure if there are unforeseen implications for other shows when using this.

			episodeLookup = {}
			episodeDelete = []
			for numberSeason, season in episodeTree.items():
				for numberEpisode, episode in season.items():
					number2 = self._extractNumber(episode, MetaPack.NumberStandard)
					if number2:
						numberSeason2 = number2[MetaPack.PartSeason]
						numberEpisode2 = number2[MetaPack.PartEpisode]
						if not numberSeason2 is None and not numberEpisode2 is None:
							key = (numberSeason2, numberEpisode2)
							if not key in episodeLookup: episodeLookup[key] = []
							episodeLookup[key].append(episode)
							if len(episodeLookup[key]) > 1:
								Tools.update(episodeLookup[key][0], episodeLookup[key][-1], none = False, lists = False, unique = False)
								episodeDelete.append((numberSeason, numberEpisode))

			for i in episodeDelete:
				del episodeTree[i[0]][i[1]]

			if not self._checkDelay(check = check): return False

			# Add the previously-removed TVDb ID back, if not other match was found based on number or title.
			# Sometimes the removed ID should not be added back, because the episode was removed from TVDb and therefore the TVDb ID is now invalid.
			# Eg: QI S00E15 - Trakt has a TVDb ID that does no longer exist on TVDb.
			# However, sometimes the TVDb ID is actaully correct, since it can point to another TVDb show, or often points to a full movie on TVDb, instead of a TV special (movie) in TVDb's S0.
			# Hence, it is better to add the ID back in case it points to another movie/show, instead of assuming it is an invalid TVDb ID.
			if incorrectTrakt:
				for numberSeason, season in episodeTree.items():
					for numberEpisode, episode in season.items():
						if not self._extractId(episode, MetaPack.ProviderTvdb):
							idTrakt = self._extractId(episode, MetaPack.ProviderTrakt)
							idTvdb = incorrectTrakt.get(idTrakt)
							if idTvdb: episode['id'][MetaPack.ProviderTvdb] = idTvdb

			################################################################################################################
			# STEP 9 - Determine the episode type and other cleanup.
			################################################################################################################

			episodeCustomized = {}
			numbers = [MetaPack.NumberStandard, MetaPack.NumberSequential, MetaPack.NumberAbsolute, MetaPack.NumberDate]

			# Determine the episode type.
			# Also do this for episodeUnknown, in order to add the correct types.
			# This is important for TVDb-only episodes (eg: Trakt does not have the TVDb ID yet), to add the  Media.Standard type.
			for tree, unknown in [(episodeTree, False), (episodeUnknown, True)]:
				for numberSeason, season in tree.items():
					for numberEpisode, episode in season.items():
						numberProviders = {}
						numberSeasons = {}
						numberEpisodes = {}
						available = 0
						available2 = 0
						for provider in providers:
							# Check either season+episode number, or season number + ID, since numbers do not always match.
							# Eg: One Piece S22E01 vs S22E1089.
							# Season numbers can be vary greatly, if Trakt has an absolute offset within the season.
							# Eg: One Piece S02E01 (Trakt/TMDb S02E62 vs TVDb S05E02)
							matchSeason = False
							matchEpisode = False
							numberProvider = self._extractNumber(episode, MetaPack.NumberStandard, provider = provider)
							if numberProvider:
								matchSeason = numberProvider[MetaPack.PartSeason] == numberSeason
								matchEpisode = numberProvider[MetaPack.PartEpisode] == numberEpisode
								numberProviders[provider] = numberProvider
								numberSeasons[provider] = numberProvider[MetaPack.PartSeason]
								numberEpisodes[provider] = numberProvider[MetaPack.PartEpisode]

							if matchSeason:
								if matchEpisode or self._extractId(episode, provider = provider): available += 1
								if matchEpisode: available2 += 1
							else:
								# Avoid episodes being marked as Universal.
								# Eg: One Piece S02E01, S03E01, S15E10, S21E195, S21E197.
								available2 -= 1

						count = [showCount.get(i, {}).get(numberSeason) for i in providers]
						count = [i for i in count if i]
						minimum = min(count) if count else 0
						maximum = max(count) if count else 0
						difference = maximum - minimum
						automatic = self._extractType(episode, MetaPack.NumberAutomatic)

						number = self._extractNumber(episode, MetaPack.NumberStandard)
						numberEpisode2 = None if number is None else number[MetaPack.PartEpisode]

						# All non-automatic episodes are standard.
						# Or any special that has a season number with at least one provider.
						if not automatic and (numberSeason > 0 or any(numberSeasons.get(i, 0) >= 0 for i in providers)):
							episode['type'][MetaPack.NumberStandard] = True

						# If a standard episode is available on Trakt, mark as "official".
						# If a standard episode is not available on Trakt, mark as "unofficial".
						# Also do this for S0, since we need the official count of specials for the checkmark in season menus.
						if not automatic:
							# If the episode number from S01 is greater than the sequential number, mark as unofficial.
							# Eg: Star Wars: Young Jedi Adventures - S01E49 (TVDb) = S01E25 (Trakt/TMDb)
							numberSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)

							# Only do this if the Trakt/TMDb standard and sequential numbers are far apart.
							# Otherwise the difference might be caused by Trakt/TMDb having a missing episode.
							# Eg: The Tonight Show Starring Jimmy Fallon S01E174 (missing on both Trakt and TMDb).
							# Eg: The Tonight Show Starring Jimmy Fallon S01E183-185.
							numberTraktStandard = numberProviders.get(MetaPack.ProviderTrakt)
							numberTraktStandardEpisode = None if numberTraktStandard is None else numberTraktStandard[MetaPack.PartEpisode]
							numberTraktSequential = self._extractNumber(episode, MetaPack.NumberSequential, provider = MetaPack.ProviderTrakt, part = MetaPack.PartEpisode)
							try: numberDifference = abs(numberTraktStandardEpisode - numberTraktSequential)
							except: numberDifference = None
							if numberSeason == 1 and not numberSequential is None and numberEpisode > numberSequential and (not numberDifference or numberDifference > 3):
								episode['type'][MetaPack.NumberUnofficial] = True
							else:
								numberOfficialSeason = -1 if numberTraktStandard is None else numberTraktStandard[MetaPack.PartSeason]
								if numberOfficialSeason == -1: numberOfficialSeason = numberSeasons.get(MetaPack.ProviderTmdb, -1)
								if numberOfficialSeason >= 0 and (numberOfficialSeason == numberSeason or numberOfficialSeason > 1):
									# Exclude later TVDb episodes that match to earlier Trakt episodes.
									# Eg: My Name Is Earl S03E19+ (TVDb) should be unofficial, even if it points to an official Trakt episode.
									#number = self._extractNumber(episode, MetaPack.NumberStandard)

									# Sometimes Trakt has a missing episode, although it is on TMDb.
									# If no Trakt number is found, use the TMDb number instead.
									# Eg: One Piece S01E58 (not on Trakt).
									numberOfficial = -1 if numberTraktStandard is None else numberTraktStandard
									numberOfficialStandard = -1 if numberTraktStandardEpisode is None else numberTraktStandardEpisode
									if numberOfficial == -1:
										numberOfficial = numberProviders.get(MetaPack.ProviderTmdb)
										numberOfficialStandard = -1 if numberOfficial is None else numberOfficial[MetaPack.PartEpisode]

									numberTvdb = numberProviders.get(MetaPack.ProviderTvdb)
									numberTvdbStandard = -1 if numberTvdb is None else numberTvdb[MetaPack.PartEpisode]
									if numberSeason == 0 or not(not numberOfficial == number and numberTvdb == number and numberOfficialStandard < numberTvdbStandard):
										# If the episode is only on TMDb and not on Trakt.
										# Eg: Cops S04E46+ (on TMDb and not on Trakt). This show is so messed up between TMDb and Trakt, no effort is going to be made to fix all the inconsistencies.
										if available == 1 and self._extractId(episode, MetaPack.ProviderTmdb): episode['type'][MetaPack.NumberUnofficial] = True
										else: episode['type'][MetaPack.NumberOfficial] = True
									elif available > 0: episode['type'][MetaPack.NumberUnofficial] = True
								elif available > 0: episode['type'][MetaPack.NumberUnofficial] = True

						# If an episode is on all providers, mark as "universal".
						# Alternativley, check available2 which is purley based on IDs, in case the season/episode numbers are far off.
						# Eg: One Piece S02E01 (Trakt/TMDb S02E62 vs TVDb S05E02)
						# The second part of the if-statement is used to later mark the correct official/unofficial episode labels with Italics.
						if available == providerCount or (available2 == 0 and available >= (providerCount - 1)):
							episode['type'][MetaPack.NumberUniversal] = True

						# Special season (S0) or special "legacy" special episodes (SxxE00).
						# Or any of the providers has the episode listed under S0, while others have it as a standard episode inside a season.
						if numberSeason == 0 or numberEpisode == 0 or any(numberSeasons.get(i) == 0 for i in providers):
							episode['type'][MetaPack.NumberSpecial] = True

						# A provider has a new unreleased season, while other providers have not added it yet.
						if numberSeason > 0 and available > 0 and numberEpisode2:
							time = self._extractCombined(data = episode, key = 'time', preference = MetaPack.ProviderTrakt, common = True, minimum = True)
							if not time or (time or 0) > current:
								episode['type'][MetaPack.NumberStandard] = True

						# One or more providers have a single sequential-numbered season S01, where not all episodes are part of the standard S01 from the other providers that use multiple seasons.
						# We might not want to show these in the "Season 1" menus if there is an "Absolute" menu as well.
						# Eg: Dragon Ball Super (multiple seasons on TVDb, but single absolute season on Trakt/TMDb).
						if numberSeason == 1 and available > 0:
							episode['type'][MetaPack.NumberSequential] = True

						# Automatically added episodes are currently all sequential episodes.
						if numberSeason == 1 and automatic:
							episode['type'][MetaPack.NumberSequential] = True

						# Episodes who have an absolute number from a provider.
						if numberSeason == 1 and self._extractNumber(episode, MetaPack.NumberAbsolute, part = MetaPack.PartEpisode): # Ignore specials which Trakt assigns a "0" absolute number.
							episode['type'][MetaPack.NumberAbsolute] = True

						# For season-based absolute numbering on Trakt/TMDb.
						# Eg: One Piece S21E892 - S21E1088.
						# This is important to get the correct next episode in MetaManager.metadataEpisodeNext().
						# After the lookup tables have been created, these episode's types will be adjusted.
						if numberSeason > 0 and not automatic:
							# Sometimes TVDb uses the absolute episode numbering, while Trakt uses normal numbering.
							# In this case mark the TVDb episodes as custom, not the Trakt episodes.
							# Eg: Good times, bad times
							if absolution.get(MetaPack.ProviderTvdb):
								providerCustom1 = MetaPack.ProviderTvdb
								providerCustom2 = MetaPack.ProviderTrakt
							else:
								providerCustom1 = MetaPack.ProviderTrakt
								providerCustom2 = MetaPack.ProviderTvdb

							numberCustom = numberSeasons.get(providerCustom1, -1)
							if numberCustom > 1:
								numberCustomStandard = numberEpisodes.get(providerCustom1, -1)
								numberCustomSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode, provider = providerCustom1, default = -2)

								numberCustom2 = numberSeasons.get(providerCustom2, -100)
								numberCustomStandard2 = numberEpisodes.get(providerCustom2, -100)
								numberCustomSequential2 = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode, provider = providerCustom2, default = -100)

								# Do not set the custom type if both Trakt and TVDb have the same episode number.
								# Eg: Good times, bad times S02E161 (161 can be the sequential number 161 or the S02 episode number 161).
								# Allow the sequential number to be off by 1, in case where multiple episodes are aired on the same day, and Trakt vs TVDb switched the episode order.
								# Eg: Good times, bad times S03E23 + S03E24 (Trakt) are swapped around S1994E424 + S1994E425 (TVDb), check the titles on TVDb and the aliases on Trakt.
								if not(numberCustom == numberCustom2 and numberCustomStandard == numberCustomStandard2) and not(numberCustom == numberCustom2 and abs(numberCustomSequential - numberSequential) == 1 and not numberCustomSequential == numberEpisode):
									if numberCustomStandard == numberCustomSequential and numberEpisode == numberCustomStandard:
										episode['type'][MetaPack.NumberCustom] = True
									else:
										# If the Trakt season number does not match with the Gaia season number, it probably means this is an unofficial TVDb episode that maps to a different season.
										# Eg: One Piece S07E33 -> S07E34
										if numberEpisode > 1 and not numberCustom == numberSeason:
											episode['type'][MetaPack.NumberCustom] = True

										# If the Trakt episode was previously processes, it means this one is a TVDb episode that simply maps to an earlier Trakt episode that coincidentally falls within the correct season, so the previous if-statement does not catch it.
										# Eg: One Piece S17E65+
										else:
											if (numberCustom, numberCustomStandard) in episodeCustomized:
												episode['type'][MetaPack.NumberCustom] = True
											else:
												episodeCustomized[(numberCustom, numberCustomStandard)] = True

						#gaiaabsoluted
						'''if absoluted and numberSeason > 0 and not self._extractType(episode, MetaPack.NumberUniversal):
							if self._extractType(episode, MetaPack.NumberOfficial):
								del episode['type'][MetaPack.NumberOfficial]
								episode['type'][MetaPack.NumberUnofficial] = True
							elif self._extractType(episode, MetaPack.NumberUnofficial):
								del episode['type'][MetaPack.NumberUnofficial]
								episode['type'][MetaPack.NumberOfficial] = True
						'''

						# Other cleanup.

						# Add [None, None] to numbers that are not available.
						# Eg: House S06 on Trakt does not have absolute numbers.
						if not unknown:
							number = episode.get('number')
							if number:
								for j in numbers:
									if not number.get(j): number[j] = [None, None]
								for i in MetaPack.Providers:
									for j in numbers:
										if not number.get(i, {}).get(j):
											if not i in number: number[i] = {}
											number[i][j] = [None, None]

						# Remove invalid IDs to reduce the data size.
						episode['id'] = {k : v for k, v in self._extractId(episode, default = {}).items() if v}

						# Remove unsupported providers.
						support = [i for i in providers if self._extractId(episode, i) or not numberEpisodes.get(i) is None]
						episode['support'] = [i for i in self._extract(episode, 'support', []) if i in support]

						# Remove non-existing titles.
						if not self._extract(episode, 'title'):
							try: del episode['title']
							except: pass

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 10 - Fill in missing IDs and numbers for unofficial episodes.
			################################################################################################################

			# Unofficial or uncombined episodes from TVDb often do not have a Trakt/TMDb ID and number.
			# Eg: Star Wars: Young Jedi Adventures S01E26 (TVDb).
			# Fill in the missing ID and number, so we know the corresponding Trakt ID.
			# Only do this after the type was calculated, otherwise it will replace the values of the other (correct) episode.
			# Plus, we only do this for NumberUnofficial to reduce title matching.

			episodeCustom = {i : {} for i in providersExtended}
			for numberSeason, season in episodeTree.items():
				# This can take very long for large shows.
				# Eg: Good times, bad times (german soap)
				if excessive: episodeList2 = episodeTree.get(numberSeason).values()
				else: episodeList2 = episodeList

				episodeList3 = []
				for episode2 in episodeList2:
					if not self._extractType(episode2, MetaPack.NumberUnofficial) and self._extractId(episode2, MetaPack.ProviderTrakt):
						title = self._extractTitle(episode2)
						if title: episodeList3.append((title, episode2))

				for numberEpisode, episode in season.items():
					if self._extractType(episode, MetaPack.NumberUnofficial) and not self._extractId(episode, MetaPack.ProviderTrakt):
						title = self._extractTitle(episode)
						if title:
							checker = 0
							if not self._checkDelay(check = check): return False

							for item in episodeList3:
								title2 = item[0]
								episode2 = item[1]

								if episode is episode2: continue

								# Do not match the title if the provider IDs differ, meaning this is probably a different episode, even if the title is the same.
								# Eg: Better Call Saul S00E56 vs S01E01. Although the title "Uno" is the same as S01E01, this is a different episodes. The plot: 'Table read of "Uno"'.
								if not combined and not self.matchCustom(episode, episode2): continue

								checker += 1
								if title2:
									# Doing full title matching can take very long for large shows.
									if excessive: match = self.matchExact(data = title2, title = title)
									else: match = self.match(data = title2, title = title, combined = True, quick = True)
									if match:
										if not combined: episodeList3.remove(item)
										for j in providersExtended:
											if episode.get('id').get(j) is None: episode['id'][j] = episode2.get('id').get(j)
											numberStandard = episode.get('number').get(j).get(MetaPack.NumberStandard)
											if numberStandard is None or numberStandard[MetaPack.PartEpisode] is None:
												episodeCustom[j][tuple(episode2.get('number').get(j).get(MetaPack.NumberStandard))] = True
												Tools.update(episode.get('number').get(j), episode2.get('number').get(j), none = False, lists = False, unique = False)
										break

							self._checkIncrement(count = checker)

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 11 - Add IMDb episodes based on their IDs and numbers.
			################################################################################################################

			# Extra IMDb episodes that do not match to any of the other episodes.
			# Eg: Lost S01E25
			# Eg: The Tonight Show Starring Jimmy Fallon S08E198+
			episodeImdb = []

			if imdb:
				try:
					# Do not use TVDb IDs for this, since Trakt sometimes has the wrong TVDb ID, causing the incorrect episode to get updated.
					# Eg: One Piece S22E44 vs S22E47.
					#idOther = (MetaPack.ProviderTrakt, MetaPack.ProviderTmdb, MetaPack.ProviderTvdb)
					idOther = (MetaPack.ProviderTrakt, MetaPack.ProviderTmdb)

					lookupId = {i : {} for i in idOther}
					lookupImdbId = {}
					lookupImdbStandard = {}
					lookupImdbSequential = {}
					lookupImdbCount = {}

					for numberSeason, season in episodeTree.items():
						for numberEpisode, episode in season.items():
							if self._extractType(episode, MetaPack.NumberOfficial) and not self._extractType(episode, MetaPack.NumberCustom):
								try: lookupImdbCount[numberSeason] += 1
								except: lookupImdbCount[numberSeason] = 1

							# There can be mutiple episode dicts with the same ID.
							# Eg: Absoluted vs standard numbers.
							try:
								id = episode['id'][MetaPack.ProviderImdb]
								if id:
									try: lookupImdbId[id].append(episode)
									except: lookupImdbId[id] = [episode]
							except: pass
							for i in idOther:
								try:
									id = episode['id'][i]
									if id:
										try: lookupId[i][id].append(episode)
										except: lookupId[i][id] = [episode]
								except: pass
							try:
								number = episode['number'][MetaPack.NumberStandard]
								if number and not number[MetaPack.PartEpisode] is None:
									number = tuple(number)
									try: lookupImdbStandard[number].append(episode)
									except: lookupImdbStandard[number] = [episode]
							except: pass
							try:
								number = episode['number'][MetaPack.NumberSequential]
								if number and not number[MetaPack.PartEpisode] is None:
									number = tuple(number)
									try: lookupImdbSequential[number].append(episode)
									except: lookupImdbSequential[number] = [episode]
							except: pass

					if not self._checkDelay(check = check): return False

					# If the number of episodes per season between Trakt/TMDb/TVDb and IMDb is too large, mark as a discrepancy.
					# For these shows do not assign the IMDb episode purely based on the season/episode number, since the numbers can be quite far off.
					# Eg: LEGO Masters S05.
					# Mark the first season from which the discrepancy occurs. All seasons prior to that should still be allowed to match by number.
					totalImdb = 0
					lastImdb = {}
					lastSeason = max(seasonTree.keys())
					discrepancyImdb = []
					seasonsImdb = imdb.get('seasons') or []
					for season in seasonsImdb:
						numberSeason = season['number'][MetaPack.NumberStandard]
						if numberSeason:
							count = lookupImdbCount.get(numberSeason) or 0
							# Only count until the last official season, since IMDb often has mutiple future seasons, years in advance (eg: Family Guy and South Park).
							if numberSeason <= lastSeason:
								totalImdb += count
								discrepancyImdb.append(abs(len((season.get('episodes') or [])) - count))
						try: lastImdb[numberSeason] = max(i['number'][MetaPack.NumberStandard][MetaPack.PartEpisode] or 0 for i in (season.get('episodes') or []))
						except: lastImdb[numberSeason] = 0
					firstImdb = 1
					try: firstImdb = next((i for i, x in enumerate(discrepancyImdb) if x), 1)
					except: pass
					if discrepancyImdb and (sum(discrepancyImdb) > (totalImdb * 0.1)): discrepancyImdb = firstImdb
					else: discrepancyImdb = False

					# Only a single season (plus optional S0).
					# Eg: One Piece
					absolutedImdb = [i['number'][MetaPack.NumberStandard] for i in seasonsImdb]
					absolutedImdb = (max(absolutedImdb) == 1) if absolutedImdb else False
					if absolutedImdb:
						try: baseImdb = next(i for i in seasonsImdb if i['number'][MetaPack.NumberStandard] == 1)
						except: baseImdb = None
						if baseImdb:
							for numberSeason, season in seasonTree.items():
								if numberSeason > 1:
									for i in season:
										# Do not add "support" here, since these seasons are technically not supported by IMDb.
										if not i['id'].get('imdb'): i['id']['imdb'] = baseImdb['id']['imdb']
										if not MetaPack.ProviderImdb in i['number']: i['number'][MetaPack.ProviderImdb] = {}
										i['number'][MetaPack.ProviderImdb].update(baseImdb['number'])
										i['number'][MetaPack.ProviderImdb][MetaPack.NumberAbsolute] = 1

					for season in seasonsImdb:
						if not self._checkDelay(check = check): return False

						numberSeason = season['number'][MetaPack.NumberStandard]
						lookuped = seasonTree.get(numberSeason)
						if lookuped:
							support = supports.get(numberSeason)
							if support is None: supports[numberSeason] = [MetaPack.ProviderImdb]
							else: support.append(MetaPack.ProviderImdb)

							for i in lookuped:
								if not i['id'].get('imdb'): i['id']['imdb'] = season['id']['imdb']
								if not MetaPack.ProviderImdb in i['number']: i['number'][MetaPack.ProviderImdb] = {}
								i['number'][MetaPack.ProviderImdb].update(season['number'])
								i['number'][MetaPack.ProviderImdb][MetaPack.NumberAbsolute] = 1

						# For seasons only on IMDb.
						# Eg: Money Heist S04 + S05.
						imdbOnly = False
						if not numberSeason in seasonTree:
							imdbOnly = True
							if not numberSeason in episodeTree: episodeTree[numberSeason] = {}

							imdbSerie = [Media.Alternate]
							if numberSeason == 1: imdbSerie.append(Media.Premiere)
							elif statusFinished and numberSeason == max(lastImdb.keys()): imdbSerie.append(Media.Finale)
							else: imdbSerie.append(MetaPack.NumberStandard)

							seasonNumber = self._extract(data = season, key = 'number')
							seasonNumber['imdb'] = Tools.copy(seasonNumber, deep = False)

							seasonTree[numberSeason] = [{
								'id'		: {
									'imdb'	: None,
									'tmdb'	: None,
									'tvdb'	: None,
									'trakt'	: None,
								},
								'number'	: seasonNumber,
								'support'	: [MetaPack.ProviderImdb],
								'incorrect'	: [],
								'type'		: {MetaPack.NumberUnofficial : True},
								'serie'		: (MetaPack.ProviderImdb, imdbSerie),

								'status'	: None,
								'interval'	: None,
								'title'		: None,

								'year'		: None,
								'date'		: None,
								'time'		: None,

								'duration'	: None,
								'count'		: None,
							}]

						for episode in (season.get('episodes') or []):
							try:
								try: id = episode['id'][MetaPack.ProviderImdb]
								except: id = None
								if id:
									number = episode['number'][MetaPack.NumberStandard]
									numberSeason = number[MetaPack.PartSeason]
									numberEpisode = number[MetaPack.PartEpisode]

									# First try by IMDb ID, which is the most accurate.
									lookuped = lookupImdbId.get(id)
									if lookuped:
										for i in lookuped:
											try:
												# Add IMDb specials to the season.
												# Eg: Downton Abbey S03E09.
												# Or episodes for IMDb-only seasons.
												# Eg: Money Heist S04 + S05.
												if (i['number'][MetaPack.NumberStandard][MetaPack.PartSeason] == 0 and not numberEpisode in episodeTree[numberSeason]) or imdbOnly:
													episodeNew = Tools.copy(i)

													episodeNew['id'][MetaPack.ProviderImdb] = id
													for j in ('title', 'year', 'date', 'time', 'status', 'interval'):
														if not episodeNew.get(j): episodeNew[j] = None

													episodeNew['number'].update(episode.get('number'))
													episodeNew['number'][MetaPack.ProviderImdb].update(episode.get('number'))
													if self._extractNumber(episodeNew, MetaPack.NumberAbsolute, part = MetaPack.PartEpisode) is None: episodeNew['number'][MetaPack.NumberAbsolute] = [None, None]

													# Only use the sequential number if it is not a single episode at the end of the seasons, aka an IMDb special.
													# Eg: Downton Abbey S02E09.
													# Check the episode number for both None and 0 (that is [1,0]).
													if all(not self._extractNumber(episodeNew, MetaPack.NumberSequential, part = MetaPack.PartEpisode, provider = j) for j in (MetaPack.ProviderTrakt, MetaPack.ProviderTmdb, MetaPack.ProviderTvdb)):
														episodeNew['number'][MetaPack.NumberSequential] = [1, 0]

													try: del episodeNew['type'][MetaPack.NumberOfficial]
													except: pass
													episodeNew['type'][MetaPack.NumberUnofficial] = True

													support = episodeNew.get('support')
													if not support: support = []
													if not MetaPack.ProviderImdb in support: support.append(MetaPack.ProviderImdb)
													episodeNew['support'] = support

													episodeTree[numberSeason][numberEpisode] = episodeNew
													if not imdbOnly: episodeList.append(episodeNew)

													# Eg: Doctor Who S07E00 is S00E47 (Trakt).
													if numberEpisode == 0:
														i['id'][MetaPack.ProviderImdb] = id
														i['number'][MetaPack.ProviderImdb].update(episode.get('number'))

														support = i.get('support')
														if not support: support = []
														if not MetaPack.ProviderImdb in support: support.append(MetaPack.ProviderImdb)
														i['support'] = support
												else:
													i['number'][MetaPack.ProviderImdb].update(episode.get('number'))

													# Do not do this for combined/uncombined episodes that are only on TVDb, even if they have an IMDb ID.
													# Eg: Star Wars: Young Jedi Adventures S01E28+ (TVDb).
													support = i.get('support')
													if not(self._extractType(i, MetaPack.NumberUnofficial) and support and len(support) == 1 and MetaPack.ProviderTvdb in support):
														if not support: support = []
														if not MetaPack.ProviderImdb in support: support.append(MetaPack.ProviderImdb)
														i['support'] = support

													# Eg: Hereos S01E00.
													if numberSeason > 0 and numberEpisode == 0:
														i['number'].update(episode.get('number'))

											except: Logger.error()

									# Eg: GoT S01E00.
									elif numberSeason > 0 and numberEpisode == 0:
										episodeNew = Tools.copy(episode, deep = False)

										for j in ('title', 'year', 'date', 'time', 'status', 'interval'):
											if not episodeNew.get(j): episodeNew[j] = None

										for i in providersExtended:
											if not i in episodeNew['number']:
												episodeNew['number'][i] = {}
												for j in numbers: episodeNew['number'][i][j] = [None, None]

										# Do not copt the number dict, since it can contain internal provider numbers (Trakt, etc).
										#episodeNew['number'][MetaPack.ProviderImdb] = Tools.copy(episode['number'], deep = False)
										if episode['number']: episodeNew['number'][MetaPack.ProviderImdb].update({k : v for k, v in episode['number'].items() if not k in providersExtended})

										episodeNew['number'].update(episode.get('number'))
										if not episodeNew['number'].get(MetaPack.NumberAbsolute): episodeNew['number'][MetaPack.NumberAbsolute] = [None, None]

										episodeNew['type'] = {MetaPack.NumberUnofficial : True, MetaPack.NumberStandard : True, MetaPack.NumberSpecial : True}
										episodeNew['support'] = [MetaPack.ProviderImdb]

										episodeTree[numberSeason][numberEpisode] = episodeNew
										episodeList.append(episodeNew)
									else:
										extra = False

										# Do not do this for S0, since IMDb's S0 is very different to Trakt/TVDb.
										# Also ingore season specials SxxE00.
										# Eg: Game of Thrones S01E00.
										# Do not add episodes purley based on the episode number if the episode was previously marked as having the incorrect IMDb ID on Trakt.
										# Otherwise the incorrect IMDb ID gets removed, but then a new incorrect IMDb ID gets added here, which is purley done by episode number.
										# Eg: The Tonight Show Starring Jimmy Fallon S02E205 (Trakts incorrect IMDb ID is tt5019824, which gets removed, but then tt4942112 is added here, which is S02E205 on IMDb,which is actually another episode).
										if numberSeason and numberEpisode and (not discrepancyImdb or numberSeason < discrepancyImdb) and not incorrectImdb.get(tuple(number)):
											# Then try by standard number, which is less accurate.
											try: lookuped = lookupImdbStandard[tuple(episode['number'][MetaPack.NumberStandard])]
											except: pass

											# Finally try by sequential number, which can be very far off.
											# Only do this if the total number of official episodes is similar to the total number of episodes from IMDb.
											# If not, there might be a huge discrepancy between IMDb and Trakt/TMDb/TVDb numbers and we do not want to assume the sequential numbers match, especially since we set the IMDb ID.
											# Plus IMDb sometimes has specials in the standard seasons, causing discrepancies in the sequential number.
											# Eg: Downton Abbey S02E09.
											# Only check sequential numbers if no standard number was found.
											# Otherwise an incorrect sequential number might be selected.
											# Eg: One Piece S01E1135 will also return S01E1134 using sequential numbers, since the sequential numbers are missing 1 episode.
											if not lookuped:
												try:
													lookuped = []
													lookups = lookupImdbSequential[tuple(episode['number'][MetaPack.NumberSequential])]
													if lookups:
														for i in lookups:
															type = self._extractType(i)
															if not type or type.get(MetaPack.NumberAutomatic) or empty:
																# The sequential number can be very far off for shows with many episodes streching over many years.
																# Be very strict when sequential numbers are accepted.
																# Eg: The Tonight Show Starring Jimmy Fallon S08E198+ match to S08E112 (Trakt), which is incorrect.
																allow = False
																sequentialMain = self._extractNumber(i, MetaPack.NumberSequential)
																sequentialTrakt = self._extractNumber(i, MetaPack.NumberSequential, provider = MetaPack.ProviderTrakt)
																sequentialTvdb = self._extractNumber(i, MetaPack.NumberSequential, provider = MetaPack.ProviderTvdb)
																if sequentialMain == sequentialTrakt and sequentialMain == sequentialTvdb: allow = True
																elif sequentialMain == sequentialTrakt and sequentialTrakt and sequentialTvdb and sequentialTrakt[MetaPack.PartEpisode] and sequentialTvdb[MetaPack.PartEpisode] and abs(sequentialTrakt[MetaPack.PartEpisode] - sequentialTvdb[MetaPack.PartEpisode]) < 5: allow = True

																if allow: lookuped.append(i)
												except: pass

											# Do not add to automatic absolute episodes in S01.
											# Eg: Lost S01E25 should be its own episode and not match to the automatic-sequential episode S01E25 (or S02E01 on Trakt).
											# Do not do this for single absolute seasons.
											# Eg: One Piece S01E1135 -> S22E47.
											# Eg: Good times bad times.
											if not absolutedImdb:
												temp = []
												for i in lookuped:
													if not self._extractType(i, MetaPack.NumberAutomatic) or numberSeason == self._extractNumber(i, MetaPack.NumberStandard, part = MetaPack.PartSeason, provider = MetaPack.ProviderTrakt):
														temp.append(i)
												lookuped = temp

											# Add all the episodes that have the same ID, but not the same season/episode numbers.
											# Eg: One Piece S01E1135 (IMDb) -> S22E47 (Trakt/TMDb).
											if lookuped:
												temp = []
												sequentialImdb = self._extractNumber(episode, MetaPack.NumberSequential)
												absoluteImdb = self._extractNumber(episode, MetaPack.NumberAbsolute)
												for i in lookuped:
													for j in idOther:
														id2 = i['id'].get(j)
														if id2:
															item = lookupId[j].get(id2)
															if item:
																# Only do this if the sequential number matches the Trakt AND TVDb sequential numbers.
																# If they do not match, it probably indicates a discrpency between the episode numbers.
																# In such a case, do not use the episode, since it probably will be the incorrect one.
																# Eg: Good times bad times S01E403 (correct match against S03E01), S01E8278 (incorrect match against S34E98 from Trakt/TVDb).
																# Also check these special cases:
																# Eg: One Piece S01E1135 (IMDb) vs S22E47 (Trakt).
																for k in item:
																	allow = False

																	absoluteMain = self._extractNumber(k, MetaPack.NumberAbsolute)
																	sequentialMain = self._extractNumber(k, MetaPack.NumberSequential)
																	sequentialTrakt = self._extractNumber(k, MetaPack.NumberSequential, provider = MetaPack.ProviderTrakt)
																	sequentialTvdb = self._extractNumber(k, MetaPack.NumberSequential, provider = MetaPack.ProviderTvdb)

																	if sequentialImdb == sequentialTrakt and sequentialImdb == sequentialTvdb: allow = True
																	elif sequentialImdb == sequentialMain and sequentialImdb == absoluteMain: allow = True

																	if allow: temp.append(k)
																break # Already found. No further ID lookups for other providers for this episode.
												lookuped.extend(temp)
												lookuped = Tools.listUnique(lookuped)

											if lookuped:
												# If the ID mismatches, it is probably not the same episode.
												# But sometimes Trakt/TMDb/TVDb have an incorrect or oudated IMDb ID, which will not be overwritten, but sometimes should be?
												try: id2 = lookuped['id'][MetaPack.ProviderImdb]
												except: id2 = None
												if not id2:
													for i in lookuped:
														# Do not set the ID if there is already an ID.
														# Eg: My Name Is Earl S03E02 - Trakt has the correct ID of S03E03 (IMDb - double episodes).
														# Keep the IMDb ID instead of replacing it.
														if not i['id'].get(MetaPack.ProviderImdb): i['id'][MetaPack.ProviderImdb] = id

														i['number'][MetaPack.ProviderImdb].update(episode.get('number'))

														support = i.get('support')
														if not support: support = []
														if not MetaPack.ProviderImdb in support: support.append(MetaPack.ProviderImdb)
														i['support'] = support

											else: extra = True
										else: extra = True

										# If IMDb has uncombined/part episodes while Trakt/TMDb does not.
										# Although the episode with the given number exists on Trakt/TMDb, it is not the same episode of the given number on IMDb, because IMDb has extra episodes.
										# Hence, the IMDb ID from the IMDb data does not match the IMDb ID from the Trakt data.
										# Still add this episode to "episodeImdb" so that it gets added to the lookup table.
										# Eg: My Name is Earl S03. IMDb/TVDb have a number of episodes split into 2 parts, while Trakt/TMDb has them as combined episodes.
										# Without this, S03E02, S03E04, etc would not be added to the IMDb lookup table.
										mismatched = False
										if not extra and lookuped:
											mismatched = True
											for i in lookuped:
												if i['id'].get(MetaPack.ProviderImdb) == id:
													mismatched = False
													break

										if extra or mismatched:
											number = Tools.copy(episode.get('number'), deep = False)
											number[MetaPack.ProviderImdb] = Tools.copy(episode.get('number'), deep = False)
											item = {
												'id'		: {
													'imdb'	: episode['id'][MetaPack.ProviderImdb],
													'tmdb'	: None,
													'tvdb'	: None,
													'trakt'	: None,
												},
												'number'	: number,
												'support'	: [MetaPack.ProviderImdb],
												'incorrect'	: [],
												'type'		: {MetaPack.NumberUnofficial : True, MetaPack.NumberStandard : True, Media.Alternate : True},
												'interval'	: None,

												'status'	: None,
												'title'		: None,

												'year'		: None,
												'date'		: None,
												'time'		: None,

												'duration'	: None,
											}
											item['number'] = self._createNumber(data = item, episode = True)

											if numberSeason == 0 or numberEpisode == 0:
												item['type'][Media.Special] = True
											elif numberEpisode == 1:
												item['type'][Media.Premiere] = True
												item['type'][Media.Outer if numberSeason == 1 else Media.Inner] = True
											elif numberEpisode and numberEpisode == lastImdb.get(numberSeason):
												item['type'][Media.Finale] = True
												item['type'][Media.Outer if (statusFinished and numberSeason and lastImdb and list(lastImdb.keys())[-1] == numberSeason) else Media.Inner] = True # Only mark as Outer if the show finished.

											if extra:
												# Append to the official tree if an episode with the given number does not exist yet.
												# Do not add it to the tree if it does exist, since the sequential number might be used by another episode.
												# Eg: Lost S01E25 is already S02E01 from the automatic sequential numbering.
												try: found = episodeTree[numberSeason][numberEpisode]
												except: found = None
												if found:
													# Only if the found episode is automatic.
													# Eg: Lost S01E25
													# Not for other episode types.
													# Eg: Vikings S00E06.
													if self._extractType(found, MetaPack.NumberAutomatic):
														episodeImdb.append(item)
												else:
													# Sometimes IMDb has a new season while others do not.
													# Or others do have the season, but with no episodes, so the season number is not in episodeTree.
													if not numberSeason in episodeTree: episodeTree[numberSeason] = {}
													episodeTree[numberSeason][numberEpisode] = item
												episodeList.append(item)
											elif mismatched:
												episodeImdb.append(item)
												episodeList.append(item)

							except: Logger.error()
				except: Logger.error()

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 12 - Add and adjust episode serie types.
			################################################################################################################

			# Do this after Step 9, since it requires the episode types for all episodes in order to calculate the lastEpisode.

			# Do not pick the last season from seasonTree, since seasons are not always ordered by number.
			seasonLastStandard = []
			seasonLastOfficial = []
			for season in seasonTree.values():
				# Not just official, but also other standard seasons.
				# Eg: Dragon Ball Super S02+ on TVDb.
				# Season types are only set in the next step. So do not check th type here.
				#if self._extractType(season, MetaPack.NumberStandard):
				numberStandard = self._extractNumber(season, MetaPack.NumberStandard, part = MetaPack.PartSeason)
				if not numberStandard is None: seasonLastStandard.append(numberStandard)

				numberOfficial = numberStandard
				numberSeason = self._extractDict(data = season, key = 'number')
				typeSeason = self._extractSelect(data = season, key = 'type')
				if typeSeason and MetaPack.NumberUnofficial in typeSeason: numberOfficial = None
				elif numberSeason and self._extractNumber({'number' : numberSeason}, MetaPack.NumberStandard, provider = MetaPack.ProviderTrakt) is None: numberOfficial = None
				if not numberOfficial is None: seasonLastOfficial.append(numberOfficial)
			seasonLastStandard = max(seasonLastStandard) if seasonLastStandard else None
			seasonLastOfficial = max(seasonLastOfficial) if seasonLastOfficial else None

			# Calculate the number of episodes per season, and the average number of episodes over all seasons.
			seasonTotal = 0
			seasonEpisodeTotal = 0
			seasonEpisodeMean = 0 # The average number of episodes per season, calculated over all seasons, except S0.
			seasonEpisodeCount = {} # The number of official episodes in each season.
			for numberSeason, season in episodeTree.items():
				seasonEpisodeCounts = []
				for episode in season.values():
					if not self._extractType(episode, MetaPack.NumberCustom) and self._extractType(episode, MetaPack.NumberOfficial):
						number = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
						if not number is None: seasonEpisodeCounts.append(number)
				seasonEpisodeCount[numberSeason] = max(seasonEpisodeCounts) if seasonEpisodeCounts else 0
			for season, count in seasonEpisodeCount.items():
				if season and count: # Exclude S0.
					seasonTotal += 1
					seasonEpisodeTotal += count
			if seasonEpisodeTotal and seasonTotal: seasonEpisodeMean = seasonEpisodeTotal / seasonTotal

			# Sometimes S00 can contain a full season of sequential episodes.
			# Eg: Money Heist S00 (Trakt).
			# Determine this special case, so that MetaTools.mergeType() is more accurate for S00 premieres/finales.
			specialSeason = False
			specialPremiere = False
			try:
				if 0 in episodeTree:
					specialMiddle = False
					specialFinale = False

					specialCount0 = 0
					specialCount1 = 0
					specialDuration0 = None
					specialDuration1 = None
					specialDurationPremiere = None

					if 1 in episodeTree:
						specialDuration = []
						for episode in episodeTree[1].values():
							specialDuration.append(self._extract(data = episode, key = 'duration'))
							if self._extractType(episode, MetaPack.NumberOfficial): specialCount1 += 1
						specialDuration = [i for i in specialDuration if i]
						if specialDuration: specialDuration1 = sum(specialDuration) / len(specialDuration)

					if specialDuration1:
						specialDuration = []
						for numberEpisode, episode in episodeTree[0].items():
							duration = self._extract(data = episode, key = 'duration')
							if numberEpisode == 1: specialDurationPremiere = duration
							specialDuration.append(duration)
							if self._extractType(episode, MetaPack.NumberOfficial): specialCount0 += 1

							serie = self._extract(data = episode, key = 'serie')
							if serie:
								for i in serie:
									if i[1]:
										if Media.Finale in i[1] and not Media.Middle in i[1]: specialFinale = True
										if Media.Middle in i[1]: specialMiddle = True
						specialDuration = [i for i in specialDuration if i]
						if specialDuration: specialDuration0 = sum(specialDuration) / len(specialDuration)

						# Accept S0 as a full season if all of the below:
						#	1. There is a midseason or season finale.
						#	2. The episode count between S01 and S01 is close.
						#	2. The average duration between S01 and S01 is close.
						if specialFinale or specialMiddle:
							specialCount = specialCount0 / specialCount1
							specialDuration = (specialDuration0 / specialDuration1) if (specialDuration0 and specialDuration1) else None
							if specialCount > 0.6 and specialCount < 1.6:
								if specialCount > 0.7 and specialCount < 1.7:
									specialSeason = True
									if specialDurationPremiere:
										specialDuration = (specialDurationPremiere / specialDuration0) if (specialDurationPremiere and specialDuration0) else None
										if specialDuration and specialDuration > 0.8 and specialDuration < 1.2: specialPremiere = True
			except: Logger.error()

			for numberSeason, season in episodeTree.items():
				seriePrevious = []

				status = None
				seasoned = seasonTree[numberSeason]
				values = self._extract(data = seasoned, key = 'status')
				if values:
					values = {i[0] : i[1] for i in values if i and i[1]}
					if values:
						statusSeason = values.get(MetaPack.ProviderTrakt)
						if not statusSeason: statusSeason = next(iter(values.values()))
						status = [statusSeason] + list(values.values())
				statusSeason = tools.mergeStatus(status, media = Media.Season, season = numberSeason, type = self._extract(seasoned, 'type'), status = statusShow)

				lastEpisode1 = []
				lastEpisode2 = []
				lastEpisode3 = []
				for episode in season.values():
					# Only official non-custom episodes.
					# Eg: One Piece S21 goes up to S21E194, ingore Trakt absolute numbers beyond that.
					if not self._extractType(episode, MetaPack.NumberCustom):
						number = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
						if not number is None:
							if self._extractType(episode, MetaPack.NumberOfficial): lastEpisode1.append(number)

							# Also add the standard number as backup, in case there is no official episode.
							# Eg: Dragon Ball Super S05 is only on TVDb (unofficial), not on Trakt (official).
							if self._extractType(episode, MetaPack.NumberStandard): lastEpisode2.append(number)

				episodeLastStandard = max(lastEpisode2) if lastEpisode2 else max(lastEpisode1) if lastEpisode1 else None
				episodeLastOfficial = max(lastEpisode1) if lastEpisode1 else None

				# Add series year/date/time, types (premieres and finales), and status.
				for numberEpisode, episode in season.items():
					# Determine the episode airing date.
					# Due to timezone differences and other inconsistencies between providers, there might different dates.
					# With local timezones in the EU, the date for such an episode might be a day later.
					# Eg: The Tonight Show Starring Jimmy Fallon (airs at 1 April 23h30 in NY/US, but EU/UTC time might be 2 April 03h30).
					# In most cases the dates should already accommodate the timezone of the origin country (MetaTvdb/MetaTrakt/MetaTmdb.metadataPack()).
					# But in case there are different dates, pick the one that occurs most frequently.
					# And if there is not common date, pick the minimum date, which is mostly the correct one.
					# Eg: The Tonight Show Starring Jimmy Fallon S04E02. Trakt: 16-01-2017, TMDb: does not exist at all, TVDb: 20-09-2016 (but this is actually a different episode S04E11 on Trakt/TMDb).
					# Use "preference = MetaPack.ProviderTrakt", since Trakt is more accurate, since it returns the dates with a time as well, whereas TMDb/TVDb only return the date without the time.
					# Update: Now always pick the Trakt date/timestamp, even if the TMDb and TVDb timestamps are the same (most common).
					# Eg: Game of Thrones S08E06 - Trakt: 1558314000 (Mon May 20 2019 01:00:00 GMT+0000) - TMDb/TVDb: 1558224000 (Sun May 19 2019 00:00:00 GMT+0000)
					# This is a 25h difference (more than a full day). Trakt is correct, since GoT always aired Sundays nights in the US (UTC 2019-05-20.01:00:00 is US/NY 2019-05-19.21:00:00).
					date = self._extract(data = episode, key = 'date')
					if date:
						if Tools.isTuple(date): date = [date]
						for i in date:
							try:
								number = episode['number'][i[0]].get(MetaPack.NumberDate)
								if not number or not number[MetaPack.PartEpisode]: episode['number'][i[0]][MetaPack.NumberDate] = [int(i[1].split('-')[0]), int(i[1].replace('-', ''))]
							except: pass

					episode['year'] = self._extractCombined(data = episode, key = 'year', preference = MetaPack.ProviderTrakt, common = True, minimum = True)
					episode['date'] = self._extractCombined(data = episode, key = 'date', preference = MetaPack.ProviderTrakt, common = True, minimum = True)
					episode['time'] = self._extractCombined(data = episode, key = 'time', preference = MetaPack.ProviderTrakt, common = True, minimum = True)

					standardSeason = None
					standardEpisode = None
					standardNumber = self._extractNumber(episode, MetaPack.NumberStandard)
					if standardNumber:
						standardSeason = standardNumber[MetaPack.PartSeason]
						standardEpisode = standardNumber[MetaPack.PartEpisode]

					try:
						date = self._extract(data = episode, key = 'date')
						episode['number'][MetaPack.NumberDate] = [int(date.split('-')[0]), int(date.replace('-', ''))]
					except: pass

					serieAll = None
					serieProvider = self._extract(data = episode, key = 'serie')

					# If the episode number exists on TVDb, but not on Trakt/TMDb, do not use the Trakt/TMDb serie types.
					# Eg: LEGO Masters S04E14 (TVDb standard) -> S04E13 (Trakt/TMDb finale).
					# Eg: LEGO Masters S04E16 (TVDb standard)
					# Do not do this if the TVDb type is non-standard.
					# Eg: One Piece S21E194 (TVDb finale)
					if self._extractType(episode, MetaPack.NumberOfficial) and self._extractType(episode, MetaPack.NumberStandard):
						tvdbStandard = False
						for i in serieProvider:
							if i[0] == MetaPack.ProviderTvdb:
								tvdbStandard = i[1] and Media.Standard in i[1]
								break
						if tvdbStandard:
							traktSeason = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTrakt, part = MetaPack.PartSeason)
							traktEpisode = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTrakt, part = MetaPack.PartEpisode)
							tvdbSeason = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTvdb, part = MetaPack.PartSeason)
							tvdbEpisode = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTvdb, part = MetaPack.PartEpisode)
							if ((not traktSeason == tvdbSeason) or (traktSeason == tvdbSeason and not traktEpisode == tvdbEpisode)) and (standardSeason == tvdbSeason and standardEpisode == tvdbEpisode):
								serieProvider = {i[0] : i[1] for i in serieProvider if i and i[0] == MetaPack.ProviderTvdb}

					if serieProvider:
						# The value can be a dict if the episode only appears on TVDb.
						# Eg: LEGO Masters S05E06 (TVDb) which is S06E06 (Trakt, but not yet added to Trakt).
						if Tools.isDictionary(serieProvider): serieProvider = {k : v for k, v in serieProvider.items() if v}
						else: serieProvider = {i[0] : i[1] for i in serieProvider if i and i[1]}
						serie = list(serieProvider.values())
						if serie: serieAll = Tools.listUnique(Tools.listFlatten(serie))
					try: serieNext = Tools.listUnique(Tools.listFlatten(list({i[0] : i[1] for i in season[numberEpisode + 1].get('serie') if i and i[1]}.values())))
					except: serieNext = None

					# Determine if an extra episode on IMDb classifies as a special, or is simply because of deviations in numbering.
					# Eg: Family Guy S23E20 (IMDb) is a special (currently unreleased, so it does not map to any Trakt/TVDb episode).
					# Only do this if the average number of episodes per season is low.
					# This excludes daily shows with many episodes, which very often have discrepancies in the number of episodes and episode numbering, although they are not specials.
					# Eg: The Tonight Show Starring Jimmy Fallon S08E198+ (IMDb), while Trakt only goes up to S08E197.
					specialEpisode = False
					if seasonEpisodeMean and seasonEpisodeMean <= 50:
						# Only do this if there are not more than 5 extra episodes on IMDb.
						# If there are more additional episodes on IMDb, they are probably not specials.
						episodeLimit = 5
						# Check if standardEpisode is None, which can be the case if no Trakt data is passed in (due to reaching the Trakt API limit).
						if episodeLastOfficial and not standardEpisode is None and standardEpisode <= (episodeLastOfficial + episodeLimit):
							# Only do this if the current episode number does not exceed the last unofficial/standard by 5.
							# Sometimes Trakt/TMDb/TVDb only have a few episodes listed for a new season, while IMDb has all episodes listed.
							# These are not specials, but rather future/unaired episodes.
							# Eg: Sheriff Country has 5 episodes listed on Trakt/TMDb/TVDb (2025-10-26), while IMDb has 20 episodes listed (although S01E06+ do not have titles/plots/dates yet).
							if standardEpisode >= (episodeLastStandard - episodeLimit):
								specialEpisode = True

					serie = tools.mergeType(values = serieAll, season = standardSeason, episode = standardEpisode, seasonLastStandard = seasonLastStandard, seasonLastOfficial = seasonLastOfficial, episodeLastStandard = episodeLastStandard, episodeLastOfficial = episodeLastOfficial, type = episode.get('type'), typePrevious = seriePrevious, typeNext = serieNext, typeProvider = serieProvider, statusShow = statusShow, statusSeason = statusSeason, specialSeason = specialSeason, specialEpisode = specialEpisode, specialPremiere = specialPremiere)
					if serie:
						for i in series:
							if i in serie: episode['type'][i] = True

					seriePrevious = serie
					try: del episode['serie']
					except: pass

					# Fill in missing status.
					episode['status'] = tools.mergeStatus(self._extract(episode, 'status'), media = Media.Episode, season = standardSeason, episode = standardEpisode, time = self._extract(episode, 'time'), type = self._extract(episode, 'type'), status = statusShow)

					# Recalculate here again, since new IDs might have been added.
					# Eg: Better Call Saul S00E56 (TVDb) S01E01 (Trakt/TMDb).
					# Do not do this for combined shows, since we want to keep the original support values for uncombined episodes.
					# Eg: Star Wars: Young Jedi Adventures S01
					# Although it should not matter if we mark these episodes as supported by all providers.
					if not combined:
						support = [i for i in providers if self._extractId(episode, i) or not self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = i) is None]
						for i in support:
							if not i in episode['support']: episode['support'].append(i)

					# Replace the standard season numbers of TVDb with the year numbers.
					# Do this last, once the standard season number is not needed for any of the calculations above.
					if seasonYear:
						for k, v in seasonYear.items():
							v = v.get(numberSeason)
							if not v is None and not self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason, provider = k) is None: episode['number'][k][MetaPack.NumberStandard][MetaPack.PartSeason] = v

			if not self._checkDelay(check = check): return False

			# Add back titles for specials in S0 that were previously removed since they are generic and cause incorrect title matches.
			# Eg: Money Heist S00.
			try:
				if titleSpecial and 0 in episodeTree:
					for episode in episodeTree[0].values():
						if not self._extractTitle(episode):
							title = None
							for k, v in self._extractId(episode).items():
								if v:
									try:
										title = titleSpecial[k][v]
										if title: break
									except: pass
							if title: episode['title'] = title
			except: Logger.error()

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 13 - Combine season metadata and calculate summaries from the episodes.
			################################################################################################################

			# Exterpolate the season numbers and IDs for absoluted seasons.
			# Eg: Dragon Ball Super - mutiple seasons on TVDb, but only a single season on Trakt/TMDb/IMDb.
			# All seasons S02+ should point to the first Trakt/TMDb/IMDb season.
			absolutedProvider = {}
			for provider, item in base:
				seasons = [i for i in self._extractSeasons(item) if i['number'][MetaPack.NumberStandard]]
				if seasons and len(seasons) == 1 and seasons[0]['number'][MetaPack.NumberStandard] == 1: absolutedProvider[provider] = seasons[0]

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

					'status'	: None,
					'interval'	: None,
					'title'		: self._createTitle(data = season, language = language, setting = setting),

					# Calculated later, since the episode types can change.
					'year'		: None,
					'date'		: None,
					'time'		: None,

					'duration'	: None,
					'count'		: None,

					'episodes'	: episode,
				}

				# Remove invalid IDs to reduce the data size.
				item['id'] = {k : v for k, v in self._extractId(item, default = {}).items() if v}

				# Remove unsupported providers.
				support = [i for i in providersExtended if self._extractId(item, i) or not self._extractNumber(item, MetaPack.NumberStandard, provider = i) is None]
				item['support'] = [i for i in self._extract(item, 'support', []) if i in support]

				# Add missing titles.
				if not item['title']: item['title'] = (['Specials'] if numberSeason == 0 else []) + ['Season %d' % numberSeason]

				# Clean the numbers.
				item['number'] = self._createNumber(data = item)

				# Interpolate TMDb absolute numbers from Trakt, since they are not available from TMDb, but are probably the same as those on Trakt.
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
					if len(support) >= providerCount: item['type'][MetaPack.NumberUniversal] = True
					if numberSeason == 1:
						item['type'][MetaPack.NumberSequential] = True
						item['type'][MetaPack.NumberAbsolute] = True

				standardSeason = self._extractNumber(item, MetaPack.NumberStandard)

				# Sometimes Trakt and TVDb return a different season status.
				# Eg: One Piece S22: continuing (Trakt) and ended (TVDb).
				# This can happen if the metadata is outdated on a provider.
				# Or for One Piece S22, Trakt has a mid-season finale with 2 future episodes listed after it, while TVDb also has a mid-season finale, but it is the last one in the season.
				# Or the TVDb status is assumed to be ended, because there are no more/future episodes, probably because of outdated metadata on TVDb. While Trakt still has a few future episodes listed.
				# Prefer the Trakt status, since Trakt is also used for the default numbering.
				status = None
				statusSeason = None
				values = self._extract(data = season, key = 'status')
				if values:
					values = {i[0] : i[1] for i in values if i and i[1]}
					if values:
						statusSeason = values.get(MetaPack.ProviderTrakt)
						if not statusSeason: statusSeason = next(iter(values.values()))
						status = [statusSeason] + list(values.values())
				time = self._createSummaries(data = episode, value = 'time', count = False, total = False, mean = False, minimum = True, maximum = True, values = True, sort = True, unique = True)
				statusSeason = tools.mergeStatus(status, media = Media.Season, season = standardSeason, time = time.get(MetaPack.ValueMinimum), type = self._extract(item, 'type'), status = statusShow)

				serieAll = None
				serieProvider = self._extract(data = season, key = 'serie')
				if serieProvider:
					serieProvider = {i[0] : i[1] for i in serieProvider if i and i[1]}
					serie = list(serieProvider.values())
					if serie: serieAll = Tools.listUnique(Tools.listFlatten(serie))
				serieLast = self._extract(data = episode[-1], key = 'type') if episode else None

				serie = tools.mergeType(values = serieAll, season = standardSeason, seasonLastStandard = seasonLastStandard, seasonLastOfficial = seasonLastOfficial, type = item.get('type'), typeLast = serieLast, typeProvider = serieProvider, statusShow = statusShow, statusSeason = statusSeason)
				if serie:
					for i in series:
						if i in serie: item['type'][i] = True

				item['status'] = tools.mergeStatus(status, media = Media.Season, season = standardSeason, time = time.get(MetaPack.ValueMinimum), type = self._extract(item, 'type'), status = statusShow)

				# Replace the standard season numbers of TVDb with the year numbers.
				# Do this last, once the standard season number is not needed for any of the calculations above.
				if seasonYear:
					for k, v in seasonYear.items():
						v = v.get(numberSeason)
						if not v is None: item['number'][k][MetaPack.NumberStandard] = v

				# Fill in missing season numbers.
				# Only do this AFTER "support" and "type" were already calculated, since these seasons are technically not supported by the provider.
				if numberSeason > 1:
					try:
						for provider, baseSeason in absolutedProvider.items():
							if not item['id'].get(provider): item['id'][provider] = baseSeason['id'][provider]
							if not provider in item['number']: item['number'][provider] = {}
							item['number'][provider].update(baseSeason['number'][provider])
							item['number'][provider][MetaPack.NumberAbsolute] = 1
					except: Logger.error()

				seasons[numberSeason] = item
			seasons = Tools.listSort(list(seasons.values()), key = lambda i : self._extractNumber(i, MetaPack.NumberStandard))

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 14 - Create a lookup table for quick access and number mapping.
			################################################################################################################

			numbersUniversal = [MetaPack.NumberUniversal] + numbers

			# Episodes that are missing on Trakt, but are on TMDb, might have a missing absolute numbers.
			# This causes None to be inserted as a season in the Absolute lookup table.
			# Eg: One Piece S01E58 (missing on Trakt, but on TMDb and TVDb).
			# Use the sequential number as absolute number, if there is no other episode with that given absolute number.
			try:
				lookupAbsolute = {}
				lookupUnabsolute = []
				for season in seasons:
					for episode in season.get('episodes'):
						numberAbsolute = self._extractNumber(episode, MetaPack.NumberAbsolute, part = MetaPack.PartEpisode)
						if numberAbsolute is None:
							# Only do this if there is no Trakt/TVDb number for the episode.
							if not self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = MetaPack.ProviderTrakt):
								if not self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = MetaPack.ProviderTvdb):
									lookupUnabsolute.append(episode)
						else: lookupAbsolute[numberAbsolute] = True

				# Do not do this if the show does not have absolute numbers for all/most episodes.
				# Aka only some absolute numbers are missing.
				if lookupUnabsolute and (len(lookupUnabsolute) < len(lookupAbsolute) * 0.9):
					for episode in lookupUnabsolute:
						numberSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
						if not numberSequential is None and not numberSequential in lookupAbsolute:
							# Do not add the sequential number as the absolute number, if the episode is only available on IMDb.
							# Otherwise the IMDb absolute number will be used as the episode's global absolute number.
							# Eg: Family Guy S23E20 (IMDb).
							support = self._extract(episode, 'support')
							if support and not(len(support) == 1 and MetaPack.ProviderImdb in support):
								episode['number'][MetaPack.NumberAbsolute][MetaPack.PartSeason] = 1
								episode['number'][MetaPack.NumberAbsolute][MetaPack.PartEpisode] = numberSequential
								lookupAbsolute[numberSequential] = True
			except: Logger.error()

			lookupSeason = {}
			lookupEpisode = {}
			lookupProvider = {}
			for i in numbersUniversal:
				lookupSeason[i] = {}
				lookupEpisode[i] = {}
			for i in MetaPack.Providers:
				lookupSeason[i] = {}
				lookupEpisode[i] = {}
				lookupProvider[i] = {j : {} for j in (MetaPack.NumberSequential, MetaPack.NumberAbsolute, MetaPack.NumberDate)}

			# Some episodes might not have a sequential number, since they are new and only appear on TVDb and not on Trakt yet.
			# Create sequential numbers by incrementing the sequential number from the previous episode.
			lookupExtra = {}
			for season in seasons:
				for episode in season.get('episodes'): # Use the updated episode list.
					for i in (None, MetaPack.ProviderTrakt, MetaPack.ProviderTmdb, MetaPack.ProviderTvdb):
						numberProvider = self._extractNumber(episode, MetaPack.NumberStandard, provider = i)
						if not numberProvider: continue
						numberSeason = numberProvider[MetaPack.PartSeason]
						numberEpisode = numberProvider[MetaPack.PartEpisode]
						if numberSeason is None or numberEpisode is None: continue

						try: lookupList = lookupExtra[numberSeason]
						except: lookupExtra[numberSeason] = lookupList = {}
						try: lookupList2 = lookupList[numberEpisode]
						except: lookupList[numberEpisode] = lookupList2 = []
						lookupList2.append(episode)

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
					numberSeason = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason)
					numberEpisode = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
					if numberSeason is None or numberEpisode is None: continue

					numberSeasonSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartSeason)
					numberEpisodeSequential = self._extractNumber(episode, MetaPack.NumberSequential, part = MetaPack.PartEpisode)

					# Fill in missing sequential numbers from the lookup created above.
					if numberEpisodeSequential is None:
						numberSeasonExtra = numberSeason
						numberEpisodeExtra = numberEpisode - 1
						if numberEpisodeExtra <= 0:
							numberSeasonExtra -= 1
							numberEpisodeExtra = -1
						if numberSeasonExtra:
							if numberEpisodeExtra < 0:
								try: numberEpisodeExtra = lookupExtra[numberSeasonExtra].keys()[-1]
								except: pass
							try: founds = lookupExtra[numberSeasonExtra][numberEpisodeExtra]
							except: founds = None
							if founds:
								# First try to pick a real sequential number that comes from Trakt/TMDb.
								# Otherwise pick the calculated sequential number from the previous iteration.
								found = [None, None, None, None]
								for i in founds:
									numberBase = self._extractNumber(i, MetaPack.NumberSequential, part = MetaPack.PartEpisode)
									numberTrakt = self._extractNumber(i, MetaPack.NumberSequential, part = MetaPack.PartEpisode, provider = MetaPack.ProviderTrakt)
									numberTmdb = self._extractNumber(i, MetaPack.NumberSequential, part = MetaPack.PartEpisode, provider = MetaPack.ProviderTmdb)
									if not numberBase is None:
										if not numberTrakt is None or not numberTmdb is None:
											if not found[0]: found[0] = i
											break
										elif self._extractType(i, MetaPack.NumberOfficial):
											if not found[1]: found[1] = i
										elif self._extractType(i, MetaPack.NumberCustom):
											if not found[3]: found[3] = i
										else:
											if not found[2]: found[2] = i
								found = found[0] or found[1] or found[2] or found[3]
								if found:
									number = Tools.copy(found['number']['sequential'], deep = False)
									number[1] += 1
									episode['number']['sequential'] = number
									numberSeasonSequential = number[0]
									numberEpisodeSequential = number[1]

					if self._extractType(episode, MetaPack.NumberOfficial):
						base = {MetaPack.ValueIndex : [indexSeason, indexEpisode]}
						for i in numbers: base[i] = self._extractNumber(episode, i)
						for i in MetaPack.Providers: base[i] = self._extractNumber(episode, MetaPack.NumberStandard, provider = i)

						try: lookupList = lookupSequential[numberSeasonSequential]
						except: lookupSequential[numberSeasonSequential] = lookupList = {}
						lookupList[numberEpisodeSequential] = base

					indexEpisode += 1
				indexSeason += 1

			lookupNumber = {}
			lookupStandard = {}
			lookupAbsolute = {}
			automatics = []
			counter = 0
			indexSeason = 0
			for season in seasons:
				# Season lookups.
				numberSeason = self._extractNumber(season, MetaPack.NumberStandard)
				base = {MetaPack.ValueIndex : indexSeason}
				for i in numbers: base[i] = self._extractNumber(season, i)
				for i in MetaPack.Providers: base[i] = self._extractNumber(season, MetaPack.NumberStandard, provider = i)

				for number in numbersUniversal:
					numberLookup = MetaPack.NumberStandard if number == MetaPack.NumberUniversal else number
					if not numberSeason == 1 and (numberLookup == MetaPack.NumberSequential or numberLookup == MetaPack.NumberAbsolute): continue # Ignore non-S01 for sequential/absolute.
					item = Tools.copy(base, deep = False)
					for i in MetaPack.Providers:
						numberSeason2 = self._extractNumber(season, numberLookup, provider = i)
						if not numberSeason2 is None:
							item[i] = numberSeason2
							lookupSeason[i][numberSeason2] = Tools.copy(base, deep = False)
					lookupSeason[number][self._extractNumber(season, numberLookup)] = item

				# Episode lookups.
				indexEpisode = 0
				episodes = season.get('episodes') # Use the updated episode list.
				for episode in episodes:
					numberSeason = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartSeason)
					numberEpisode = self._extractNumber(episode, MetaPack.NumberStandard, part = MetaPack.PartEpisode)
					if numberSeason is None or numberEpisode is None: continue

					added = False
					types = (MetaPack.NumberSequential, MetaPack.NumberAbsolute, MetaPack.NumberDate)

					typeAutomatic = self._extractType(episode, MetaPack.NumberAutomatic)
					typeSpecial = self._extractType(episode, MetaPack.NumberSpecial)
					typeOfficial = self._extractType(episode, MetaPack.NumberOfficial)
					typeUnofficial = self._extractType(episode, MetaPack.NumberUnofficial)
					typeCustom = self._extractType(episode, MetaPack.NumberCustom)

					# Add the type for "exists" below. It will later be removed again.
					base = {MetaPack.ValueIndex : [indexSeason, indexEpisode], 'type' : self._extractType(episode)}
					for i in numbers: base[i] = self._extractNumber(episode, i)
					for i in MetaPack.Providers: base[i] = self._extractNumber(episode, MetaPack.NumberStandard, provider = i)

					# Only increment the index counter if it was not created before.
					# Eg: One Piece S02E62 (Trakt) is S02E01 (Gaia Official).
					# Eg: One Piece S03E78 (Trakt) is S03E01 (Gaia Official).
					# We do not want to increment the index for S02E62, since it was already done for S02E01, which is the same episode.
					increment = True
					addition = None
					numberSequential = tuple(self._extractNumber(episode, MetaPack.NumberSequential))

					if numberSeason > 0:
						# Eg: Dragon Ball Super
						# For a few days these "DVD Order" specials were added to TVDb after the season finale:
						#	S00E04 -> S01E15
						#	S00E05 -> S02E14
						#	S00E01 -> S05E56
						# This was probably done by an ignorant user on TVDb, since it was reversed a few days later.
						# But for these specials that only appear on TVDb, do not increment the sequential number and remove the number from the episode.
						# Otherwise this can cause lookup problems.
						# Eg: S01E15 (sequential lookup) should return stadnadrd S02E01, not the TVDB special S01E15.
						# Do not do for IMDb specials.
						# Eg: Downton Abbey S03E09.
						# Eg: LEGO Masters S03E00.
						# Do not do for IMDb specials where the IMDb ID of a special might be removed, since it is a duplicate/incorrect IMDb ID on Trakt.
						# Do not do if the only ID is from IMDb, which indicates an IMDb special.
						# Eg: Family Guy S22E16-17.
						# if typeSpecial and typeUnofficial and not numberEpisode == 0 and self._extractNumber(episode, provider = MetaPack.ProviderTrakt, number = MetaPack.NumberStandard, part = MetaPack.PartSeason) is None:
						if typeSpecial and typeUnofficial and not numberEpisode == 0 and self._extractNumber(episode, provider = MetaPack.ProviderTrakt, number = MetaPack.NumberStandard, part = MetaPack.PartSeason) is None and not [k for k, v in self._extractId(episode).items() if not v is None] == [MetaPack.ProviderImdb]:
							increment = False
							episode['number'][MetaPack.NumberSequential] = [None, None]

						# For episodes that are specials on TVDb, but official episodes on Trakt/TMDb.
						# Eg: Pokémon S19E48 (Trakt/TMDb) - S00E61 (TVDb)
						# Eg: Pokémon S19E49 (Trakt/TMDb) - S00E62 (TVDb)
						# Still increment so it points to the S19 episode data, and not the S00 data.
						elif typeSpecial:
							increment = True

						# For custom episodes that appear at the end of a season on TVDb, but elsewhere on Trakt/TMDb.
						# Eg: Pokémon: S19E50 (TVDb) - S24E02 (Trakt/TMDb) - S19E50 does not exist at all on Trakt/TMDb, it only goes up to S19E49.
						elif typeCustom:
							increment = None # Only increment the episode index, but do not add it to lookupNumber to be reused later.

						# Eg: One Piece S02E62 (Trakt).
						elif typeOfficial:
							addition = lookupNumber.get(numberSequential)

							# Update: Star Wars Young Jedi Adventures S02E01 is now a universal episode.
							# If it is a universal number, do not use "addition".
							# Otherwise, the lookup S02E01 (Trakt and TVDb) returns the absolute episode S01E26, instead of S02E01.
							#if addition and not self._extractType(episode, MetaPack.NumberUniversal): # Star Wars: Young Jedi Adventures S02E01 (Trakt).
							#	base[MetaPack.ValueIndex] = Tools.copy(addition[MetaPack.ValueIndex])
							#	increment = False
							if self._extractType(episode, MetaPack.NumberUniversal): addition = None

						# Eg: Dragon Ball Super S05E55 (TVDB).
						elif not typeUnofficial:
							increment = False

					for number in numbersUniversal:
						# Exclude unofficial episodes from TVDb.
						# Eg: Star Wars: Young Jedi Adventures
						if number in types and not(typeOfficial or typeAutomatic): continue

						# Exclude specials that are a normal episode on Trakt, but a special on TVDb.
						# Eg: One Piece S15E590 (Trakt) vs S00E39 (TVDb): The titles are different, but the release date is the same and Trakt has S00E39's TVDb ID under its episode.
						# Update: Do this now via existsSpecial below.
						# Update 2: Also check this special at the end. Do not add it to the standard lookup table.
						#if number == MetaPack.NumberStandard and numberSeason > 0 and typeSpecial: continue

						if number == MetaPack.NumberUniversal or number in types or self._extractType(episode, number) or (number == MetaPack.NumberStandard and typeSpecial):
							numberLookup = MetaPack.NumberStandard if number == MetaPack.NumberUniversal else number

							nativeSeason = self._extractNumber(episode, numberLookup, part = MetaPack.PartSeason)
							nativeEpisode = self._extractNumber(episode, numberLookup, part = MetaPack.PartEpisode)
							if nativeEpisode == 0 and numberLookup in types: continue # Ignore E00 for sequential/absolute, which all specials use.

							# Ignore IMDb specials.
							# Eg: GoT S01E00 (IMDb) which should not be confused with S00E298 (Trakt/TMDb) which also has the universal number [1, 0] used by all specials.
							item = None
							if number == MetaPack.NumberUniversal and numberSeason == 1 and not numberEpisode == 0 and not typeOfficial:
								try: item = lookupSequential[numberSeason][numberEpisode]
								except: pass
							if not item: item = Tools.copy(base, deep = False)

							if typeAutomatic:
								if not added:
									automatics.append(episode)
									added = True

							# Do not do this for absolute numbers, since they can be very far off.
							# Eg: Star Trek (1966) has 5 absolute episodes before S01E01, which can cause the lookup tables to be incorrect if we continue here.
							# Also do not do this for date numbers. Otherwise in the lookup table, the Trakt/TMDb/TVDb numbers also use the date number, instead of the standard number.
							elif not numberLookup == MetaPack.NumberAbsolute and not numberLookup == MetaPack.NumberDate:

								for i in providersExtended:
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

										# Some episodes exists multiple times.
										# Eg: One Piece: S15E10 (Gaia), S15E590 (Trakt/TMDb), S00E39 (TVDb).
										# This can cause the suboptimal episode to be picked in MetaManager._metadataEpisodeUpdate().
										# Eg: For Trakt/TMDb S15E590, it will pick the special episode (S00E39) instead of season episode (S15E10/S15E590).
										# This will make S01E590 in the Absolute menu show up as S01E00 (since it is seen as a special).
										# If we detect an existing entry in the lookup that is from S0, replace it with a later episode.
										# Only do this for specials, not S1+, since there can be season-overlapping.
										# Eg: One Piece S01E25 (Trakt/TMDb) vs S02E17 (TVDb).
										# UPDATE: Instead of only doing this for S0, also do this for other seasons, if the episode is not of custom type.
										# If TVDb has the episode in an earlier season, while Trakt/TMDb have it in a later season.
										# Replace the TVDb episode object with the one from Trakt.
										# Eg: Pokémon: S24E02 (Trakt/TMDb) - S19E50 (TVDb)
										existsSpecial = False
										#if exists and exists.get(MetaPack.NumberStandard)[MetaPack.PartSeason] == 0:
										if exists:
											existsTypeCustom = self._extractType(exists, MetaPack.NumberCustom)
											existsTypeUniversal = self._extractType(exists, MetaPack.NumberUniversal)
											existsTypeSpecial = self._extractType(exists, MetaPack.NumberSpecial)

											existsFound = False
											existsNumber = [numberSeason, numberEpisode]
											for j in numbers + MetaPack.Providers:
												if exists.get(j) == existsNumber and not existsTypeCustom:
													# Allow universal episodes.
													# Eg: One Piece S15E591
													# Or allow if it is not a special.
													# Eg (exclude): Pokémon S19E48 (Trakt/TMDb) - S00E61 (TVDb)
													if existsTypeUniversal or not existsTypeSpecial:
														existsFound = True
														break
											if not existsFound: existsSpecial = True

										try: existsOriginal = lookupEpisode[i][numberSeason][numberEpisode]
										except: existsOriginal = False

										# If there are some combined episodes on Trakt/TMDb which are uncombined/split on TVDb/IMDb.
										# Hence, the episode matches the official Trakt/TMDb episode with a lower number, as well as the unoffical TVDb/IMDb episode with a higher number.
										# Also allow the higher unoffical number, not just the lower official number.
										# Eg: My Name is Earl S03E19+ are only on IMDb and TVDb.
										# Eg: pack.episode(season = 3,episode= 21, number = 'imdb') should return S03E21 and not S03E18.
										existsMultiple = numberSeason == numberSeason2 and numberEpisode == numberEpisode2 and typeCustom and self._extractType(exists, MetaPack.NumberOfficial) and self._extractType(item, MetaPack.NumberUnofficial)

										# existsOriginal
										#	Do not use the custom sequential numbers if the standard numbers are available.
										#	Eg: Dragon Ball Super S01E28 (sequential lookup) should return TVDb number S03E01, not S01E30 (sequential).
										# self._extractType(item, MetaPack.NumberUniversal)
										#	Replace even if "not existsOriginal", for Trakt/TMDb episode-absolute numbers.
										#	Eg: One Piece S15E10 (TVDb lookup) should return the standard number S14E04, not the Trakt/TMDb number S14E526.
										if (
											existsSpecial
											or existsMultiple
											or (not exists and (not existsOriginal or self._extractType(item, MetaPack.NumberUniversal)))
											or (self._extractType(exists, MetaPack.NumberUnofficial) and self._extractType(item, MetaPack.NumberOfficial))
											or (i == MetaPack.ProviderImdb and numberEpisode2 == 0)
										):
											# Do not replace the season number with the sequential number.
											# Eg: Dragon Ball Super S01E28 (sequential lookup) should return TVDb number S03E01.
											if not numberLookup == MetaPack.NumberSequential:
												# Not for IMDb specials.
												# Eg: GoT S01E00 (IMDb).
												if not(i == MetaPack.ProviderImdb and numberEpisode2 == 0):
													item[i] = [numberSeason2, numberEpisode2]

											if not numberSeason2 in lookupEpisode[i]: lookupEpisode[i][numberSeason2] = {}

											# Use the "real" standard number.
											# Eg: One Piece S02E62 (Trakt) is S02E01 (Gaia Official).
											# Otherwise the lookup in MetaManager._metadataEpisodeUpdate() uses the Trakt standard numbers instead of the Gaia standard numbers.
											base2 = Tools.copy(base, deep = False)
											if addition:
												# Do not do this if "addition" is an unofficial episodes.
												# Eg: Lego Masters S05E02 (Trakt/TMDb) should not be matched to S04E17 (TVDb).
												if not self._extractType(addition, MetaPack.NumberUnofficial):
													# Do not do this if the addition is a special, while base is a standard S01+ episode.
													# Eg: Better Call Saul S01E01 "Uno", also has a TVDb special S00E56 with the same title "Uno". This is the same episode that TVDb has as S01E01 and as a special S00E56 (although their TVDb IDs are different).
													# Without this, the "lookup" -> "episode" -> "trakt" -> would have S01E01 poiting to S00E56, even though Trakt also has this episode as S01E01.
													# UPDATE: Although the titles are the same, these are different episodes. S00E56 is a reading special of S01E01
													if not(base2[MetaPack.NumberStandard][MetaPack.PartSeason] >= 1 and addition[MetaPack.NumberStandard][MetaPack.PartSeason] == 0):
														# Do not replace the index from an official episode with that one of an automatic episode.
														# Eg: One Piece S01E591 (IMDb) with index [1,61] (since the IMDb episodes E61+ are not official and therefore does not increment indexEpisode anymore)
														# Eg: Do not replace the index of One Piece S15E11 (Trakt) with sequential number E591, with the index of the automatic episode S01E591 (IMDb).
														if not(self._extractType(addition, MetaPack.NumberAutomatic) and self._extractType(base2, MetaPack.NumberOfficial)):
															base2[MetaPack.ValueIndex] = Tools.copy(addition[MetaPack.ValueIndex], deep = False)
															base2[MetaPack.NumberStandard] = Tools.copy(addition[MetaPack.NumberStandard], deep = False)

											# If the episode appears twice (once for a lower Trakt number, and once for a higher TVDb number).
											# Only replace the lookup if the episode is official, aka not unofficial and not custom (which is changed to unofficial later on).
											replace = True
											try: lookedup = lookupEpisode[i][numberSeason2][numberEpisode2]
											except: lookedup = None
											try: type1 = self._extractType(lookedup)
											except: type1 = None
											try: type2 = self._extractType(base2)
											except: type2 = None
											if type1 and type2:
												if type1.get(MetaPack.NumberOfficial) and (type2.get(MetaPack.NumberUnofficial) or type2.get(MetaPack.NumberCustom)): replace = False
												elif type1.get(MetaPack.NumberUnofficial) and type2.get(MetaPack.NumberCustom): replace = False

											# IMDb specials SxxE00 that are in S0 on Trakt/TMDb/TVDb.
											# Eg: Doctor Who S03E00
											# pack.episode(season = 3, episode = 0) should return the main standard number as S03E00 and not S00E04.
											if not replace and i == MetaPack.ProviderImdb and numberSeason == numberSeason2: replace = True

											# If there are some combined episodes on Trakt/TMDb which are uncombined/split on TVDb/IMDb.
											# Eg: My Name is Earl S03E19+ are only on IMDb and TVDb.
											# Eg: pack.episode(season = 3,episode= 21, number = 'tvdb') should return S03E21 and not S03E18.
											# This is specifically for TVDb uncombined/split episodes. These episode on IMDb should already be added to the lookup without this.
											# Only do this for combined episodes.
											# Eg: LEGO Masters S04E14 (TVDb) should still match S04E13 (Trakt) and not execute this code.
											elif not replace and existsMultiple and combinedSeason.get(numberSeason): replace = True

											# Do not add if it is a sequential number that does not have an actual corresponing episode.
											# Eg: The Tonight Show Starring Jimmy Fallon S01E174 (TVDb sequential number) vs S02E46 (TVDb standard number).
											# Eg: pack.episode(season = 1,episode = 174, provider = 'tvdb') should not return an episode.
											# Still allow it if it is S01.
											# Eg: One Piece S01E61 TVDb lookup should still return S05E01 (TVDb).
											elif numberLookup == MetaPack.NumberSequential and numberSeason > 1: replace = False

											# If there is already a standard episode with the given number, do not replace it with the sequential number.
											# Otherwise if there is a missing episode on Trakt/TMDb, the standard episode will be replaced with the laster sequential number of the same value, but that points to the next episode.
											# Eg: The Tonight Show Starring Jimmy Fallon S01E174 missing on Trakt/TMDb. Do not replace S01E175 (standard) with S01E174 (sequential).
											if numberLookup == MetaPack.NumberSequential and lookupEpisode[i][numberSeason2].get(numberEpisode2): replace = False

											if replace:
												# Only add unofficial episodes to the lookup table if they were not previously manipulated.
												# Otherwise the manipulated numbers cause havok in the lookup table generation.
												# Eg: Star Wars: Young Jedi Adventures S01E26 on TVDb is added to episodeCustom (since it's Trakt numbers are filled in and it should not be used here, since it is an unofficial episode).
												if typeUnofficial:
													if not episodeCustom.get(i).get((numberSeason2, numberEpisode2)):
														lookupEpisode[i][numberSeason2][numberEpisode2] = base2
												else:
													lookupEpisode[i][numberSeason2][numberEpisode2] = base2

							# Add the various numbers from the providers which are later used to fill in missing numbers in the lookup table.
							for i in providersExtended:
								for j, entry in lookupProvider[i].items():
									numberProvider = self._extractNumber(episode, j, provider = i)
									if numberProvider:
										numberProviderSeason = numberProvider[MetaPack.PartSeason]
										numberProviderEpisode = numberProvider[MetaPack.PartEpisode]
										if numberProviderEpisode:
											try: entryList = entry[numberProviderSeason]
											except: entry[numberProviderSeason] = entryList = {}
											entryList[numberProviderEpisode] = item

							# Avoid adding automatic/special episodes to the standard lookup table.
							# Eg: One Piece S01E590 (Trakt/TMDb: S15E590, TVDb: S00E39, IMDb: S01E590)
							# Otherwise this will throw an error:
							#	pack.episode(season = 1, episode = 590, number = MetaPack.NumberStandard)
							if number == MetaPack.NumberStandard and numberSeason > 0 and typeAutomatic and typeSpecial: continue

							try: lookupList = lookupEpisode[number][nativeSeason]
							except: lookupEpisode[number][nativeSeason] = lookupList = {}
							lookupList[nativeEpisode] = item

							# Used to fix the index for absolute lookups. More info below outside the loop.
							if number == MetaPack.NumberStandard:
								try: lookupList = lookupStandard[nativeSeason]
								except: lookupStandard[nativeSeason] = lookupList = {}
								lookupList[nativeEpisode] = item[MetaPack.ValueIndex]
							elif number == MetaPack.NumberAbsolute and numberSeason > 0:
								support = self._extract(episode, 'support', default = [])
								if len(support) == 1:
									numberCurrent = self._extractNumber(episode, MetaPack.NumberStandard, provider = support[0])
									if numberCurrent:
										seasonCurrent = numberCurrent[MetaPack.PartSeason]
										seasonEpisode = numberCurrent[MetaPack.PartEpisode]
										try: lookupList = lookupAbsolute[seasonCurrent]
										except: lookupAbsolute[seasonCurrent] = lookupList = {}
										lookupList[seasonEpisode] = item

					# Eg: GoT S01E00.
					# Eg: Hereos S01E00.
					if numberSeason > 0 and numberEpisode == 0:
						counter += 1
						indexEpisode += 1
					elif increment:
						counter += 1
						indexEpisode += 1
						lookupNumber[numberSequential] = base
					elif increment is None:
						indexEpisode += 1

				indexSeason += 1

				# Remove automatically added absolute episodes to reduce size.
				# The lookup table now has these episodes, so we can still retrieve them.
				season['episodes'] = [i for i in episodes if not self._extractType(i, MetaPack.NumberAutomatic)]

			# For future episodes that are already on TVDb, but not on Trakt/TMDb/IMDb.
			# The absolute lookups do not have the correct lookup index for these episodes.
			# This causes a lookup error in _initialize().
			# Replace the index in the absolute lookups with the index added to the standard lookup.
			# Eg: One Piece S23E01+ already on TVDb, but not on Trakt/TMDb/IMDb.
			for season, items in lookupAbsolute.items():
				for episode, item in items.items():
					try: lookuped = lookupStandard[season][episode]
					except: lookuped = None
					if lookuped: item[MetaPack.ValueIndex] = lookuped

			# Get the correct numbers for automatically added episodes.
			# The indexes for automatic sequential/absolute episodes are also incorrect (incremented in S01 after the last standard S01 episode).
			for episode in automatics:
				for number in numbersUniversal:
					if number == MetaPack.NumberUniversal or number == MetaPack.NumberDate or self._extractType(episode, number) or (number == MetaPack.NumberStandard and self._extractType(episode, MetaPack.NumberSpecial)):
						numberLookup = MetaPack.NumberStandard if number == MetaPack.NumberUniversal else number
						numberSeason = self._extractNumber(episode, numberLookup, part = MetaPack.PartSeason)
						numberEpisode = self._extractNumber(episode, numberLookup, part = MetaPack.PartEpisode)

						# Eg: The Bachelor S01E00 (sequential).
						if number == MetaPack.NumberSequential and numberSeason == 1 and numberEpisode == 0: continue

						found = None
						for j in self._extract(episode, 'support', default = []):
							try:
								numberProvider = self._extractNumber(episode, MetaPack.NumberStandard, provider = j)
								found = lookupEpisode[j][numberProvider[MetaPack.PartSeason]][numberProvider[MetaPack.PartEpisode]]
							except: pass

							if found and found.get(MetaPack.NumberStandard):
								# Specials that were removed above.
								# Eg: One Piece S15E590 (Trakt) vs S00E39 (TVDb): The titles are different, but the release dateis the same and Trakt has S00E39's TVDb ID under its episode.
								if number == MetaPack.NumberStandard and not found[MetaPack.NumberStandard][MetaPack.PartSeason] == numberSeason: continue

								# Do not replace the sequential lookup if the current sequential number is different to the new sequential number.
								# Sometimes there are discrepancies that causes some sequential numbers to be unavailable on Trakt/TMDb and therefore the (incorrect) TVDb sequential number would be used.
								# This can happen if an unaired/future episode is on TMDb/TVDB/IMDb, but not on Trakt (yet).
								# Also take into account if no IMDb pack data is used (standard metadata detail).
								if number == MetaPack.NumberSequential:
									try:
										if not lookupEpisode[number][numberSeason][numberEpisode][number][MetaPack.PartEpisode] == found[number][MetaPack.PartEpisode]: continue
									except: Logger.error()

									# Sometimes future unaired episodes are on TMDb/TVDb/IMDb, but not on Trakt (yet).
									# This will then use the sequential number from TVDb instead of from Trakt (since it is not available).
									# If the TVDb sequential number is different to the Trakt sequential number, this will insert the wrong TVDb episode in the lookup table's sequential number.
									# Skip it, so that the Trakt/TMDb is inserted instead, where the TMDb sequential number was calculate manually.
									# Eg: The Tonight Show Starring Jimmy Fallon S13E20+ are not yet on Trakt, but on TMDb/TVDb.
									numberTrakt = self._extract(found, MetaPack.ProviderTrakt)
									if not numberTrakt or numberTrakt[MetaPack.PartEpisode] is None: continue

								# Ignore mismatches within standard seasons.
								# Eg: LEGO Masters S01E53 (sequential) should match to S05E02 (Trakt/TMDb) and not S04E15 (TVDb).
								if self._extractType(found, MetaPack.NumberStandard) and self._extractType(found, MetaPack.NumberUnofficial):
									# Do not do if the episode is not yet on Trakt.
									# Eg: One Piece S22E49 (not on Trakt yet), but already on IMDb as S01E1135.
									# Otherwise it causes an error in _initialize().
									numberTrakt = self._extract(found, MetaPack.ProviderTrakt)
									if numberTrakt and not numberTrakt[MetaPack.PartEpisode] is None: continue

								# The same episode might appear as a special (TVDB) and as a standard episode (Trakt/TMDb).
								# Eg: Pokémon: S19E48 (Trakt/TMDb) - S00E61 (TVDb)
								# Since we iterate from the start to the end, the special will always be picked and used to overwrite the standard episode data.
								# In such a case, check if a standard episode is available and rather use that one.
								numberFound = found.get(MetaPack.NumberStandard)
								if numberFound and numberFound[MetaPack.PartSeason] == 0:
									try:
										numberFound2 = found.get(j)
										found2 = lookupEpisode[MetaPack.NumberStandard][numberFound2[MetaPack.PartSeason]][numberFound2[MetaPack.PartEpisode]]
										if found2 and found2.get(j) == numberFound2: found = found2
									except: pass

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

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 16 - Add outlier episodes to the lookup table and clean up.
			################################################################################################################

			# Used to sort the episodes by number, once the unknwon and IMDb episodes were added.
			seasonUpdate = []
			seasonIndex = {} # Do not use seasonTree, since it was already processed.
			index = 0
			for season in seasons:
				seasonIndex[self._extractNumber(season, MetaPack.NumberStandard)] = [index, season]
				index += 1

			# Add any unknown episode that is not part of any of the official episodes.
			# Eg: My Name Is Earl S03E02, S03E08, S03E15, S03E22 (TVDb double episodes)
			# Only add them if no other episode for the given number is found in the provider lookup.
			try:
				for numberSeason, season in episodeUnknown.items():
					for numberEpisode, episode in season.items():
						additions = {}
						for provider in providers:
							number = self._extractNumber(episode, MetaPack.NumberStandard, provider = provider)
							if number:
								numberSeason = number[MetaPack.PartSeason]
								numberEpisode = number[MetaPack.PartEpisode]
								if not numberEpisode is None:
									try: found = lookupEpisode[provider][numberSeason][numberEpisode]
									except: found = None
									if not found: additions[provider] = number

						if additions:
							group = [episode]
							single = [episode]

							# Match double episodes to the other part.
							# Eg: My Name Is Earl S03E02 (TVDb) -> S03E01 (Trakt).
							title = self._extractTitle(episode)
							try: time1 = self._extractCombined(data = episode, key = 'time', common = True, minimum = True)
							except: time1 = self._extract(data = episode, key = 'time')
							for numberEpisode2, episode2 in episodeTree[numberSeason].items():
								title2 = self._extractTitle(episode2)

								if title2:
									# NB: Adjust limitMatch and limitTime based on the match ratio.
									# Also be more strict with S0, otherwise poor title matches are accepted.
									# Eg: Vikings "Vikings, Valhalla and the Legacy of Ragnar Lothbrok" vs "The Saga of Lagertha".
									# Eg: Vikings "The Saga of Bjorn" vs "The Saga of Lagertha".
									match = self.match(data = title2, title = title, combined = True, quick = True, detail = True).get('match')
									limitMatch = 0.7 if numberSeason == 0 else 0.6
									if match > limitMatch:
										limitTime = 31557600 # 1 year.
										if numberSeason == 0:
											if match < 0.7: limitTime = 259200 # 3 days.
											elif match < 0.8: limitTime = 1209600 # 14 days.
											elif match < 0.9: limitTime = 2592000 # 30 days.
										else:
											if match < 0.6: limitTime = 604800 # 7 days.
											elif match < 0.7: limitTime = 2592000 # 30 days.
											elif match < 0.8: limitTime = 15768000 # 6 months.
											elif match < 0.9: limitTime = 23652000 # 9 months.

										# Do not assume the episode is the same, just because the title matches.
										# The special title can be the same as another episode, especially if the same title is used mutiple times in the show.
										# Only accept it if the release date is less than 1 year apart. Note that specials can often have great deviations in their dates.
										# Eg: QI S00E15 (TVDB - 2025-02-10) "VG: Part 1 (Series V)" should not be matched to S00E05 (Trakt - 2020-08-13) "VG: Part 1"
										time2 = self._extract(data = episode2, key = 'time')
										if not time1 or not time2 or abs(time1 - time2) < limitTime:
											group.append(episode2)
											break

							episodeNew = {
								'id'		: {
									'imdb'	: self._extractSelect(data = group, key = ['id', 'imdb']),
									'tmdb'	: self._extractSelect(data = group, key = ['id', 'tmdb']),
									'tvdb'	: self._extractSelect(data = group, key = ['id', 'tvdb']),
									'trakt'	: self._extractSelect(data = group, key = ['id', 'trakt']),
								},
								'number'	: self._createNumber(data = group),
								'support'	: self._extractSelect(data = group, key = 'support'),
								'incorrect'	: self._extractList(data = group, key = MetaPack.ValueIncorrect, default = []),
								'type'		: self._extractDict(data = group, key = 'type'),

								'serie'		: self._extractProvider(data = group, key = 'serie', unique = True),
								'status'	: self._extractStatus(data = group, unique = True),
								'title'		: self._createTitle(data = single, language = language, setting = setting),

								'year'		: self._extractProvider(data = group, key = 'year', unique = True),
								'date'		: self._extractProvider(data = group, key = 'date', unique = True),
								'time'		: self._extractProvider(data = group, key = 'time', unique = True),

								'duration'	: self._extractDuration(data = group),
							}

							# Add missing date number.
							date = self._extract(data = episodeNew, key = 'date')
							if date:
								if Tools.isTuple(date): date = [date]
								for i in date:
									try:
										number = episodeNew['number'][i[0]].get(MetaPack.NumberDate)
										if not number or not number[MetaPack.PartEpisode]: episodeNew['number'][i[0]][MetaPack.NumberDate] = [int(i[1].split('-')[0]), int(i[1].replace('-', ''))]
									except: pass

							episodeNew['year'] = self._extractCombined(data = episodeNew, key = 'year', preference = MetaPack.ProviderTrakt, common = True, minimum = True)
							episodeNew['date'] = self._extractCombined(data = episodeNew, key = 'date', preference = MetaPack.ProviderTrakt, common = True, minimum = True)
							episodeNew['time'] = self._extractCombined(data = episodeNew, key = 'time', preference = MetaPack.ProviderTrakt, common = True, minimum = True)

							for i in numbers:
								if self._extractNumber(episode, i, part = MetaPack.PartEpisode): episodeNew['number'][i] = episode['number'][i]

							date = self._extract(data = episodeNew, key = 'date')
							if date:
								if Tools.isTuple(date): date = [date]
								for i in date:
									try:
										number = episodeNew['number'][i[0]].get(MetaPack.NumberDate)
										if not number or not number[MetaPack.PartEpisode]: episodeNew['number'][i[0]][MetaPack.NumberDate] = [int(i[1].split('-')[0]), int(i[1].replace('-', ''))]
									except: pass

							standardSeason = self._extractNumber(episodeNew, MetaPack.NumberStandard, part = MetaPack.PartSeason)
							standardEpisode = self._extractNumber(episodeNew, MetaPack.NumberStandard, part = MetaPack.PartEpisode)

							try:
								date = self._extract(data = episodeNew, key = 'date')
								episodeNew['number'][MetaPack.NumberDate] = [int(date.split('-')[0]), int(date.replace('-', ''))]
							except: pass

							serieAll = None
							serieProvider = self._extract(data = episode, key = 'serie')

							# If the episode number exists on TVDb, but not on Trakt/TMDb, do not use the Trakt/TMDb serie types.
							# Eg: LEGO Masters S04E14 (TVDb standard) -> S04E13 (Trakt/TMDb finale).
							# Eg: LEGO Masters S04E16 (TVDb standard)
							# Do not do this if the TVDb type is non-standard.
							# Eg: One Piece S21E194 (TVDb finale)
							if self._extractType(episodeNew, MetaPack.NumberOfficial) and self._extractType(episodeNew, MetaPack.NumberStandard):
								tvdbStandard = False
								for i in serieProvider:
									if i[0] == MetaPack.ProviderTvdb:
										tvdbStandard = Media.Standard in i[1]
										break
								if tvdbStandard:
									traktSeason = self._extractNumber(episodeNew, MetaPack.NumberStandard, provider = MetaPack.ProviderTrakt, part = MetaPack.PartSeason)
									traktEpisode = self._extractNumber(episodeNew, MetaPack.NumberStandard, provider = MetaPack.ProviderTrakt, part = MetaPack.PartEpisode)
									tvdbSeason = self._extractNumber(episodeNew, MetaPack.NumberStandard, provider = MetaPack.ProviderTvdb, part = MetaPack.PartSeason)
									tvdbEpisode = self._extractNumber(episodeNew, MetaPack.NumberStandard, provider = MetaPack.ProviderTvdb, part = MetaPack.PartEpisode)
									if ((not traktSeason == tvdbSeason) or (traktSeason == tvdbSeason and not traktEpisode == tvdbEpisode)) and (standardSeason == tvdbSeason and standardEpisode == tvdbEpisode):
										serieProvider = {i[0] : i[1] for i in serieProvider if i and i[0] == MetaPack.ProviderTvdb}

							if serieProvider:
								# The value can be a dict if the episode only appears on TVDb.
								# Eg: LEGO Masters S05E06 (TVDb) which is S06E06 (Trakt, but not yet added to Trakt).
								if Tools.isDictionary(serieProvider): serieProvider = {k : v for k, v in serieProvider.items() if v}
								else: serieProvider = {i[0] : i[1] for i in serieProvider if i and i[1]}
								serie = list(serieProvider.values())
								if serie: serieAll = Tools.listUnique(Tools.listFlatten(serie))

							serie = tools.mergeType(values = serieAll, season = standardSeason, episode = standardEpisode, type = episodeNew.get('type'), typeProvider = serieProvider, statusShow = statusShow)
							if serie:
								for i in series + [MetaPack.NumberStandard]:
									if i in serie: episodeNew['type'][i] = True
							try: del episodeNew['type'][MetaPack.NumberOfficial]
							except: pass
							episodeNew['type'][MetaPack.NumberUnofficial] = True
							episodeNew['type'][Media.Alternate] = True

							try: del episodeNew['serie']
							except: pass

							# Fill in missing status.
							episodeNew['status'] = tools.mergeStatus(self._extract(episodeNew, 'status'), media = Media.Episode, season = standardSeason, episode = standardEpisode, time = self._extract(episodeNew, 'time'), type = self._extract(episodeNew, 'type'), status = statusShow)

							# Recalculate here again, since new IDs might have been added.
							# Eg: Better Call Saul S00E56 (TVDb) S01E01 (Trakt/TMDb).
							# Do not do this for combined shows, since we want to keep the original support values for uncombined episodes.
							# Eg: Star Wars: Young Jedi Adventures S01
							# Although it should not matter if we mark these episodes as supported by all providers.
							episodeNew['support'] = [i for i in providersExtended if self._extractId(episodeNew, i) or not self._extractNumber(episodeNew, MetaPack.NumberStandard, part = MetaPack.PartEpisode, provider = i) is None]

							# Replace the standard season numbers of TVDb with the year numbers.
							# Do this last, once the standard season number is not needed for any of the calculations above.
							if seasonYear:
								for k, v in seasonYear.items():
									v = v.get(numberSeason)
									if not v is None and not self._extractNumber(episodeNew, MetaPack.NumberStandard, part = MetaPack.PartSeason, provider = k) is None: episodeNew['number'][k][MetaPack.NumberStandard][MetaPack.PartSeason] = v

							found = seasonIndex.get(numberSeason)
							if found:
								index = found[0]
								season = found[1]
								seasonUpdate.append(numberSeason)
								season['episodes'].append(episodeNew)

								base = {MetaPack.ValueIndex : [index, len(season['episodes']) - 1]}
								for i in numbers: base[i] = self._extractNumber(episodeNew, i)
								for i in MetaPack.Providers: base[i] = self._extractNumber(episodeNew, MetaPack.NumberStandard, provider = i)
								for k, v in additions.items():
									try: lookupList = lookupEpisode[k][v[MetaPack.PartSeason]]
									except: lookupEpisode[k][v[MetaPack.PartSeason]] = lookupList = {}
									lookupList[v[MetaPack.PartEpisode]] = base
			except: Logger.error()

			# Add IMDb episodes that are not anywhere else.
			try:
				if episodeImdb:
					for episode in episodeImdb:
						number = self._extractNumber(episode, MetaPack.NumberStandard)
						numberSeason = number[MetaPack.PartSeason]
						numberEpisode = number[MetaPack.PartEpisode]
						found = seasonIndex.get(numberSeason)
						if found:
							index = found[0]
							season = found[1]
							seasonUpdate.append(numberSeason)
							season['episodes'].append(episode)

							# Add to the lookup tables.

							base = {MetaPack.ValueIndex : [index, len(season['episodes']) - 1]}
							for i in numbers: base[i] = self._extractNumber(episode, i)
							for i in MetaPack.Providers: base[i] = self._extractNumber(episode, MetaPack.NumberStandard, provider = i)

							try: found = lookupEpisode[MetaPack.ProviderImdb][numberSeason][numberEpisode]
							except: found = None
							if not found:
								try: lookupList = lookupEpisode[MetaPack.ProviderImdb][numberSeason]
								except: lookupEpisode[MetaPack.ProviderImdb][numberSeason] = lookupList = {}
								lookupList[numberEpisode] = base
							for i in numbers:
								number2 = self._extractNumber(episode, i)
								if number2:
									numberSeason2 = number2[MetaPack.PartSeason]
									numberEpisode2 = number2[MetaPack.PartEpisode]
									if not numberSeason2 is None and not numberEpisode2 is None:
										try: found = lookupEpisode[i][numberSeason2][numberEpisode2]
										except: found = None
										if not found:
											try: lookupList = lookupEpisode[i][numberSeason]
											except: lookupEpisode[i][numberSeason] = lookupList = {}
											lookupList[numberEpisode2] = base
			except: Logger.error()

			# NB: Do NOT sort the episodes according to the espisode number.
			# Otherwise the indexes in the lookup table point to the wrong item.
			# The only reason why the episode list needs to be sorted is for last(), used by MetaManager.metadataEpisodeNext().
			# Keep the order of the episodes as is, with the extra IMDb and unknown episodes at the end of the list.
			# Then sort by episodes number on-demand in last() to get the correct last episode.
			#for numberSeason in seasonUpdate:
			#	season = seasonIndex.get(numberSeason)[1]
			#	season['episodes'] = Tools.listSort(season.get('episodes'), key = lambda i : self._extractNumber(i, MetaPack.NumberStandard))

			# Add sequential/absolute/date numbers from providers to the general lookup table if they do not already exist.
			# Eg: Star Wars: Young Jedi Adventures S01E49 (only on TVDb), adding the sequential number.
			# This will probably not work anymore once S03 is released, since S01E49 will then not be the specific TVDb episode, but rather S03E01 (since Trakt has 48 episodes in S01+S02).
			try:
				for provider, item1 in lookupProvider.items():
					for number, item2 in item1.items():
						for numberSeason, item3 in item2.items():
							for numberEpisode, item4 in item3.items():
								try: found = lookupEpisode[number][numberSeason][numberEpisode]
								except: found = None
								if not found:
									try: lookupList = lookupEpisode[number][numberSeason]
									except: lookupEpisode[number][numberSeason] = lookupList = {}
									lookupList[numberEpisode] = item4
			except: Logger.error()

			# Remove entries in the lookup table with None as season/episode number.
			# This should not happen, except if there is some screwup in the show numbering, causing some episodes to not have certain numbers.
			# This is also important for sorting the lookup tables below.
			try:
				invalidSeasons = {}
				invalidSeason = {}
				invalidEpisode = {}

				# Season lookup table.
				for number, lookup in lookupSeason.items():
					for numberSeason, items in lookup.items():
						if numberSeason is None:
							#if developer: Logger.log('PACK GENERATION [%s]: Invalid season number detected' % number.upper())
							invalidSeasons[number] = True
				for number in invalidSeasons.keys():
					try: del lookupSeason[number][None]
					except: pass

				# Episode lookup table.
				for number, lookup in lookupEpisode.items():
					for numberSeason, items in lookup.items():
						if numberSeason is None:
							#if developer: Logger.log('PACK GENERATION [%s]: Invalid season number detected' % number.upper())
							invalidSeason[number] = True
						for numberEpisode, episode in items.items():
							if not numberSeason is None and numberEpisode is None: # Already added to invalidSeason.
								#if developer: Logger.log('PACK GENERATION [%s - S%s]: Invalid episode number detected' % (number.upper(), str(numberSeason)))
								invalidEpisode[number] = numberSeason
				for number in invalidSeason.keys():
					try: del lookupEpisode[number][None]
					except: pass
				for number, numberSeason in invalidEpisode.items():
					try: del lookupEpisode[number][numberSeason][None]
					except: pass
			except: Logger.error()

			# Sort the lookup tables by season/episode numbers.
			# Sometimes episodes with discrepancies can be inserted out of order in the lookup table.
			# This creates all kinds of problems with determining eg the next or last episode in a season.
			for number, lookup in lookupSeason.items():
				lookupSeason[number] = {i[0] : i[1] for i in sorted(lookup.items(), key = lambda x : x[0])}
			for number, lookup in lookupEpisode.items():
				for numberSeason, episodes in lookup.items():
					 lookup[numberSeason] = {i[0] : i[1] for i in sorted(episodes.items(), key = lambda x : x[0])}
				lookupEpisode[number] = {i[0] : i[1] for i in sorted(lookup.items(), key = lambda x : x[0])}

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 17 - Cleanup and calculate summaries for seasons.
			################################################################################################################

			# Clean the types for season-based absolute numbering on Trakt/TMDb.
			# Eg: One Piece S21E892 - S21E1088.
			# Only do this AFTER the lookup tables were created, since they need the NumberOfficial type there.
			for episode in episodeList:
				if self._extractType(episode, MetaPack.NumberCustom):
					episode['type'][MetaPack.NumberUnofficial] = True

					# Allow the standard/universal types for custom TVDb episodes.
					# Eg: My Name Is Earl S03E19+ (TVDb).
					number = self._extractNumber(episode, MetaPack.NumberStandard)
					numberTrakt = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTrakt)
					numberTvdb = self._extractNumber(episode, MetaPack.NumberStandard, provider = MetaPack.ProviderTvdb)
					if not numberTrakt == numberTvdb and number == numberTvdb: removals = [MetaPack.NumberCustom, MetaPack.NumberOfficial]
					else: removals = [MetaPack.NumberCustom, MetaPack.NumberOfficial, MetaPack.NumberStandard, MetaPack.NumberUniversal]

					for i in removals:
						try: del episode['type'][i]
						except: pass

			for season in seasons:
				episodes = season.get('episodes')
				season['year'] = self._createSummaries(data = episodes, value = 'year', count = False, total = False, mean = False, minimum = True, maximum = True, values = True, sort = True, unique = True)
				season['date'] = self._createSummaries(data = episodes, value = 'date', count = False, total = False, mean = False, minimum = True, maximum = True, values = False, sort = True, unique = True) # Do not add the individual dates, since they can take up a lot of space, and we mostly only need the timestamp values. Can be reenabled if we ever need those dates.
				season['time'] = self._createSummaries(data = episodes, value = 'time', count = False, total = False, mean = False, minimum = True, maximum = True, values = True, sort = True, unique = True)
				season['duration'] = self._createSummaries(data = episodes, value = 'duration', count = False, total = True, mean = True, minimum = True, maximum = True, values = False)
				season['count'] = self._createCount(data = episodes)
				season['interval'] = interval = self._createInterval(data = episodes, status = self._extract(season, key = 'status'), season = self._extractNumber(season, MetaPack.NumberStandard))
				for episode in episodes: episode['interval'] = interval

			if not self._checkDelay(check = check): return False

			################################################################################################################
			# STEP 18 - Combine show metadata and calculate summaries from the seasons/episodes.
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

			# Generate a new pack identifier with "id = True".
			result = self._initialize(id = True, pack = {
				'media'		: Media.Pack,
				'content'	: Media.Show,
				'generated'	: Time.timestamp(),

				'id'		: {
					'imdb'	: self._extractSelect(data = data, key = ['id', 'imdb']),
					'tmdb'	: self._extractSelect(data = data, key = ['id', 'tmdb']),
					'tvdb'	: self._extractSelect(data = data, key = ['id', 'tvdb']),
					'trakt'	: self._extractSelect(data = data, key = ['id', 'trakt']),
					'slug'	: self._extractSelect(data = data, key = ['id', 'slug']),
				},
				'support'	: support,

				'status'	: statusShow,
				'interval'	: self._createInterval(data = seasons, status = statusShow),
				'title'		: self._createTitle(data = data, language = language, setting = setting),

				'year'		: self._createSummaries(data = episodeList, value = 'year', count = False, total = False, mean = False, minimum = True, maximum = True, values = True, sort = True, unique = True),
				'date'		: self._createSummaries(data = episodeList, value = 'date', count = False, total = False, mean = False, minimum = True, maximum = True, values = False, sort = True, unique = True), # Do not add the individual dates, since they can take up a lot of space, and we mostly only need the timestamp values. Can be reenabled if we ever need those dates.
				'time'		: self._createSummaries(data = episodeList, value = 'time', count = False, total = False, mean = False, minimum = True, maximum = True, values = True, sort = True, unique = True),

				'duration'	: self._createSummaries(data = episodeList, value = 'duration', count = False, total = True, mean = True, minimum = True, maximum = True, values = False),
				'count'		: self._createCounts(data = seasons),

				'seasons'	: seasons,

				'lookup'	: {MetaPack.ValueSeason : lookupSeason, MetaPack.ValueEpisode : lookupEpisode},
			})

			if developer:
				ids = []
				for i in MetaPack.Providers:
					id = self._extractId(result, i)
					if id: ids.append('%s: %s' % (i.upper(), id))
				ids = ' | '.join(ids)
				Logger.log('PACK GENERATION [%s]: %dms Duration, %d Episodes, %d Detailed Matches, %d Exact Matches' % (ids, timer.elapsed(milliseconds = True), counter, len(self.mMatchDetail.keys()), len(self.mMatchExact.keys())))

			return result
		except: Logger.error()
		return None

	##############################################################################
	# MATCH
	##############################################################################

	# Match a title against a list of titles, to determine if an episode's title is valid.
	# title: a single title or list of titles.
	# combined: match combined titles that can contain two or more episode titles.
	# parenthese: match titles by ignoring the parenthese part. Eg: "VG: Part 1 (Series V)" -> "VG: Part 1".
	# roman: replace roman numbers with arabic numbers. Eg: "VG: Part II" -> "VG: Part 2"
	# quick: if a list of titles is passed, only search until a match was found. If False, continues until the best match is found.
	# generic: wether or not to match generic episode titles. Eg: "Episode 1"
	# exact: first do an exact match first, which is a lot faster. If exact=True, to an full/stricter match. If exact=None, to an partial/lenient match.
	def match(self, data, title, combined = True, parenthese = False, roman = False, quick = True, generic = False, adjust = None, detail = False, exact = False):
		try:
			# Do an exact match first, since it is way faster and avoids expensive calls to the detailed matching below.
			if not exact is False:
				if self.matchExact(data = data, title = title, full = exact):
					return {'match' : 1.0, 'valid' : True} if detail else True

			result = {'match' : 0.0, 'valid' : None}
			if data and title: # Both could be None or empty arrays.
				# Cache results in case we match the same string multiple times.
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

				match = self.mMatchDetail.get(id)
				if match: return match if detail else match.get('valid')

				if Tools.isArray(data) or Tools.isArray(title):
					if not Tools.isArray(data): data = [data]
					for i in data:
						for j in title:
							match = self.match(data = i, title = j, combined = combined, parenthese = parenthese, roman = roman, quick = quick, generic = generic, adjust = adjust, detail = True)
							if quick and match.get('valid'):
								result = match
								break
							elif match.get('match', 0) >= result.get('match', 0):
								result = match
						if quick and result.get('valid'): break
				else:
					threshold = 0.9
					if combined:
						if generic or not Regex.match(data = data, expression = self._expression(2), cache = True):
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
									match = self.match(data = i, title = data2, combined = False, parenthese = parenthese, roman = roman, quick = quick, generic = generic, adjust = adjust, detail = True)
									if quick and match.get('valid'):
										result = match
										break
									elif match.get('match', 0) >= result.get('match', 0):
										result = match

						# "Title (1)" and "Title (2)"
						# "Title Part 1" and "Title Part 2"
						elif Regex.match(data = data, expression = self._expression(3), cache = True):
							threshold = 0.75

					# Eg: Doctor Who - "The Doctor, the Widow and the Wardrobe" vs "The Doctor, the Widow and the Wardrobe Prequel"
					# These are two different episodes with very similar titles. Increase the threshold.
					if Regex.match(data = data, expression = self._expression(4), cache = True):
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
						expression = self._expression(5)
						numbers1 = Regex.extract(data = data, expression = expression, group = None, all = True, cache = True)
						numbers2 = Regex.extract(data = title, expression = expression, group = None, all = True, cache = True)
						if not numbers1 == numbers2: match *= 0.7
						result = {'match' : match, 'valid' : match > threshold}

						# Match generic titles to number titles.
						# Eg: Unburied (tt33038523): "Episode 1" (Trakt) vs "1" (TVDb).
						if not result.get('valid') and generic:
							numeric1 = Tools.isNumeric(data)
							numeric2 = Tools.isNumeric(title)
							if numeric1 or numeric2:
								if numeric1 and numeric2:
									if data == title:
										result['match'] = 1.0
										result['valid'] = True
								elif numbers1 == numbers2:
									result['match'] = 0.8
									result['valid'] = True

						# Match by ignoring the parenthese part.
						# Eg: "VG: Part 1 (Series V)" -> "VG: Part 1".
						if not result.get('valid') and parenthese:
							parenthese1 = '(' in data or '[' in data
							parenthese2 = '(' in title or '[' in title
							if parenthese1 or parenthese2:
								expression = self._expression(7)
								data2 = Regex.extract(data = data, expression = expression, cache = True) if parenthese1 else data
								title2 = Regex.extract(data = title, expression = expression, cache = True) if parenthese2 else title
								if data2 and title2:
									result = self.match(data = data2, title = title2, combined = combined, parenthese = False, roman = roman, quick = quick, generic = generic, adjust = adjust, detail = True)
									valid = result.get('valid')

						# Replace roman numbers with arabic numbers.
						# Eg: "VG: Part II" -> "VG: Part 2"
						if not result.get('valid') and roman:
							roman1 = 'I' in data or 'V' in data or 'X' in data
							roman2 = 'I' in title or 'V' in title or 'X' in title
							if roman1 or roman2:
								expression = self._expression(8)
								data2 = Regex.extract(data = data, expression = expression, cache = True) if roman1 else None
								title2 = Regex.extract(data = title, expression = expression, cache = True) if roman2 else None
								if data2 or title2:
									if data2:
										data2 = self._roman(data2)
										if data2: data2 = Regex.replace(data = data, expression = expression, replacement = str(data2), group = 1, cache = True)
									else:
										data2 = data

									if title2:
										title2 = self._roman(title2)
										if title2: title2 = Regex.replace(data = title, expression = expression, replacement = str(title2), group = 1, cache = True)
									else:
										title2 = title

									if data2 or title2: result = self.match(data = data2, title = title2, combined = combined, parenthese = parenthese, roman = False, quick = quick, generic = generic, adjust = adjust, detail = True)

				self.mMatchDetail[id] = result
		except: Logger.error()
		return result if detail else result.get('valid')

	def matchExact(self, data, title, full = False):
		try:
			if data and title:
				# Caching the values actually increases generation time slightly.
				# Without caching it is 3-5ms (3-5%) faster.
				'''id = []
				if Tools.isArray(data): id.extend(data)
				else: id.append(data)
				if Tools.isArray(title): id.extend(title)
				else: id.append(title)
				id = Tools.listSort(id)
				id.append('1' if full else '0')
				id = '_'.join(id)
				id = id.lower()

				match = self.mMatchExact.get(id)
				if match: return match'''

				result = False
				limit = 10
				values1 = []

				if full:
					if not Tools.isArray(data): data = [data]
					for i in data:
						value = Tools.replaceNotAlphaNumeric(i)
						if value:
							value = value.lower()
							values1.append(value)

					if not Tools.isArray(title): title = [title]
					for i in title:
						value = Tools.replaceNotAlphaNumeric(i)
						if value:
							value = value.lower()
							if value in values1:
								result = True
								break
				else:
					values2 = []
					if not Tools.isArray(data): data = [data]
					for i in data:
						value = Tools.replaceNotAlphaNumeric(i)
						if value:
							value = value.lower()
							values1.append(value)
							if len(value) > limit: values2.append(value)

					if not Tools.isArray(title): title = [title]
					for i in title:
						value = Tools.replaceNotAlphaNumeric(i)
						if value:
							value = value.lower()
							if value in values1:
								result = True
								break

							# Cut-off titles.
							# Eg: "Ein Kuss mit Folge" vs "Ein Kuss mit Folgen" (last letter missing).
							if len(value) > limit:
								for j in values2:
									if value.startswith(j) or j.startswith(value):
										result = True
										break
								if result: break

				#self.mMatchExact[id] = result
				return result
		except: Logger.error()
		return None

	def matchCustom(self, item1, item2, special = True):
		# If both episodes are specials, do not match the IDs.
		# Since Trakt often has incorrect IDs for S0.
		# Eg: Downton Abbey S00E12 (Trakt) has the same title as S00E13 (TVDb), although the TVDb/IMDb/TMDb ID for that episode on Trakt is wrong.
		if special and self._extractNumber(item1, MetaPack.NumberStandard, part = MetaPack.PartSeason) == 0 and self._extractNumber(item2, MetaPack.NumberStandard, part = MetaPack.PartSeason) == 0: return True

		matched = 0
		mismatched = 0
		ids1 = self._extractId(item1)
		ids2 = self._extractId(item2)
		if ids1 and ids2:
			for i in (MetaPack.ProviderTrakt, MetaPack.ProviderTvdb, MetaPack.ProviderTmdb): # Ignore IMDb IDs, since they can be outdated on Trakt/TMDb.
				id1 = ids1.get(i)
				if id1:
					id2 = ids2.get(i)
					if id2:
						if id1 == id2: matched += 1
						else: mismatched += 1

		# Sometimes only a single ID mismatches, although the other ones do match.
		# This can happen for double finales.
		# Eg: House S06E22.
		if not matched and mismatched: return False
		else: return True

	##############################################################################
	# SEARCH
	##############################################################################

	# Search for an episode by ID or title.
	# When searching by ID, the provider of the ID must also be provided.
	# season: pass a list of season numbers to only match some seasons for efficiency. Typically only the same season and S0 are necessary.
	# exclude: any titles or substring that should be removed from the title before matching.
	def search(self, id = None, title = None, provider = None, season = True, lenient = False, exclude = None, excludePrefix = None, excludeSuffix = None):
		if id:
			seasons = self.season(season = season)
			if seasons:
				for season in seasons:
					for episode in self._extractEpisodes(season):
						if self._extractId(episode, provider = provider) == id:
							return episode

		if title:
			if lenient is True:
				for i in [1.0, 0.9, 0.8]:
					episode = self.search(title = title, season = season, lenient = i, exclude = exclude, excludePrefix = excludePrefix, excludeSuffix = excludeSuffix)
					if episode: return episode
			else:
				seasons = self.season(season = season)
				if seasons:
					if exclude or excludePrefix or excludeSuffix:
						title = Tools.stringRemoveAffix(title, remove = exclude, prefix = excludePrefix, suffix = excludeSuffix)
						for season in seasons:
							for episode in self._extractEpisodes(season):
								titleEpisode = self._extractTitle(episode)
								if titleEpisode:
									if Tools.isArray(titleEpisode): titleEpisode = [Tools.stringRemoveAffix(i, remove = exclude, prefix = excludePrefix, suffix = excludeSuffix) for i in titleEpisode]
									else: titleEpisode = Tools.stringRemoveAffix(titleEpisode, remove = exclude, prefix = excludePrefix, suffix = excludeSuffix)
									if self.match(data = title, title = titleEpisode, combined = True, quick = True, generic = True, adjust = lenient, detail = False):
										return episode
					else:
						for season in seasons:
							for episode in self._extractEpisodes(season):
								titleEpisode = self._extractTitle(episode)
								if titleEpisode:
									if self.match(data = title, title = titleEpisode, combined = True, quick = True, generic = True, adjust = lenient, detail = False):
										return episode

		return None

	##############################################################################
	# REDUCE
	##############################################################################

	def reduce(self, season = None, episode = None, fallback = False, alternate = False):
		try:
			if self.mPack:
				base = {'media' : True, 'content' : True, 'interval' : True, 'count' : True}
				values = dict(base, **{'type' : True, 'interval' : True, 'year' : True, 'time' : True, 'date' : True, 'duration' : True})

				if not episode is None:
					data = self.episode(season = season, episode = episode)
					if not data and fallback:
						data = self.episode(season = season, episode = -1)
						values = base
				elif not season is None:
					data = self.season(season = season)
				else:
					data = self.mPack

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

					if alternate:
						type = result.get('type') or {}
						type = Tools.dictionaryRemove(data = type, value = (MetaPack.NumberOfficial, MetaPack.NumberUniversal))
						type[MetaPack.NumberUnofficial] = True
						type[Media.Alternate] = True
						result['type'] = type

					# Add the season counts so that fully watched seasons can be hidden from the Arrivals menu.
					# Used in MetaTools.itemPlayback().
					if season is None and episode is None:
						result['seasons'] = []
						for i in (data.get('seasons') or []):
							result['seasons'].append({
								'number' : self._extractNumber(i, MetaPack.NumberStandard),
								'count' : Tools.copy(i.get('count')),
							})

					# Generate an ID for reduced data as well, so it can be cached.
					self.instanceId(pack = result, update = True)

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
					pack['year'][MetaPack.ValueSeason] = [[]] * totalSeason
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

						pack['year'][MetaPack.ValueSeason][i] = self.yearValues(season = i, default = [])

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

				# Generate an ID for reduced data as well, so it can be cached.
				self.instanceId(pack = pack, update = True)

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

				date = data.get(MetaPack.NumberDate)
				if date and date[-1] is None: date = None

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

				pack = {
					'all' : all,
					'season' : seasoned,

					MetaPack.NumberCustom : custom,
					MetaPack.NumberStandard : standard,
					MetaPack.NumberSequential : sequential,
					MetaPack.NumberAbsolute : absolute,
					MetaPack.NumberDate : date,

					MetaPack.ProviderTrakt : trakt,
					MetaPack.ProviderTmdb : tmdb,
					MetaPack.ProviderTvdb : tvdb,
				}

				# Generate an ID for reduced data as well, so it can be cached.
				self.instanceId(pack = pack, update = True)

				return pack
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
					timeSeason = [None] * totalSeason
					timeEpisode = [None] * totalSeason
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
						timeSeason[i] = [self.timeMinimum(season = i, number = number), self.timeMaximum(season = i, number = number)]
						timeEpisode[i] = self.time(season = i, number = number)

					pack['count'][MetaPack.ValueSeason] = counts
					pack['time'][MetaPack.ValueSeason] = timeSeason

					# Get the latests season's episode release dates.
					# Either the last season, or the season that is that falls in the current time.
					# This is purley used for label formatting, so that we know when a new episode anywhere in the season is released.
					# Do not add the time for all episodes, since they are not really needed and waste storage space.
					time = Time.timestamp()
					for i in timeEpisode:
						if i and time >= i[0] and time <= i[-1]:
							pack['time'][MetaPack.ValueEpisode] = i
							break

					if not MetaPack.ValueEpisode in pack['time'] and timeEpisode and timeEpisode[-1]:
						pack['time'][MetaPack.ValueEpisode] = timeEpisode[-1]

				# Generate an ID for reduced data as well, so it can be cached.
				self.instanceId(pack = pack, update = True)

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

				# Generate an ID for reduced data as well, so it can be cached.
				self.instanceId(pack = data, update = True)

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
					if Tools.isArray(number):
						number1 = number[0]
						number2 = number[1]
					else:
						number1 = number
						number2 = number

					key = self._key(base, provider, number2, type if movie is None else None, value if (episode is None and sequential is None and movie is None and not type) else None)
					data = self._data(item = item, season = season, episode = episode, number = number1, sequential = sequential, movie = movie)
					result = self._extract(data = data, key = key, default = default)

					if not part is None and result:
						if Tools.isArray(result) and Tools.isArray(result[0]): result = [i[part] if i and Tools.isArray(i) else i for i in result]
						elif Tools.isArray(result): result = result[part]

					return result
		except: Logger.error()
		return default

	##############################################################################
	# LOOKUP
	##############################################################################

	# input: NumberUniversal/NumberStandard/NumberSequential/NumberAbsolute/ProviderTrakt/ProviderTmdb/ProviderTvdb/ProviderImdb
	# output: ValueIndex/NumberStandard/NumberSequential/NumberAbsolute/ProviderTrakt/ProviderTmdb/ProviderTvdb/ProviderImdb
	def lookup(self, season = None, episode = None, input = None, output = None):
		try:
			if not input: input = MetaPack.NumberUniversal
			if episode is None:
				result = self.mLookup.get(MetaPack.ValueSeason).get(input)
				if not season is True: result = result.get(self._lookupReverse(item = result, number = season))
			else:
				if (season is False or season is None):
					if input == MetaPack.NumberSpecial: season = 0
					elif input == MetaPack.NumberAbsolute or input == MetaPack.NumberSequential: season = 1
				if input == MetaPack.NumberDate and (not season or season < MetaPack.ThresholdYear) and episode: season = int(str(episode)[:4])
				if input == MetaPack.NumberSpecial: input = MetaPack.NumberStandard

				result = self.mLookup.get(MetaPack.ValueEpisode).get(input)
				if not season is True:
					result = result.get(self._lookupReverse(item = result, number = season))
				if not episode is True:
					result = result.get(self._lookupReverse(item = result, number = episode))

					# Lookup IMDb specials that have the same sequential number as another episode in the sequential lookup.
					# Eg: Lost S01E25 (IMDb only) vs S01E25 (S02E01) in the sequential order.
					# We could update the universal lookup table to return the special instead of the sequential episode.
					# But that might cause too many issues in the lookup table and cannot be simply reversed by changing the code, since the pack metadata in the cache now has the edited lookup.
					# Therefore do a second lookup to see if there is an IMDb special that matches the episode number exactly.
					try:
						if result and season == 1 and (input == MetaPack.NumberUniversal or input == MetaPack.NumberStandard):
							seasonSpecial = result[MetaPack.NumberStandard][MetaPack.PartSeason]
							if seasonSpecial and seasonSpecial > season:
								resultSpecial = self.mLookup.get(MetaPack.ValueEpisode).get(MetaPack.ProviderImdb)
								if resultSpecial:
									# Only do this if IMDb does not have a single absolute season.
									seasonLast = max(resultSpecial.keys())
									try: episodeLast = max(resultSpecial[1].keys())
									except: episodeLast = 0
									if seasonLast > 1 or (seasonLast == season and abs(episodeLast - episode) < 5):
										if not season is True: resultSpecial = resultSpecial.get(self._lookupReverse(item = resultSpecial, number = season))
										if not episode is True: resultSpecial = resultSpecial.get(self._lookupReverse(item = resultSpecial, number = episode))
										if resultSpecial and resultSpecial[MetaPack.NumberStandard][MetaPack.PartSeason] == season and resultSpecial[MetaPack.NumberStandard][MetaPack.PartEpisode] == episode:
											result = resultSpecial
					except: Logger.error()

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
		# Reversed lookup. That is, get the last episode in the season without knowing its exact number.
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

	def seasonStandard(self, season = False, provider = None, default = None):
		return self.season(number = MetaPack.NumberStandard, season = season, provider = provider, default = default)

	def seasonSequential(self, season = False, provider = None, default = None):
		return self.season(number = MetaPack.NumberSequential, season = season, provider = provider, default = default)

	def seasonAbsolute(self, season = False, provider = None, default = None):
		return self.season(number = MetaPack.NumberAbsolute, season = season, provider = provider, default = default)

	def seasonSpecial(self, season = False, provider = None, default = None):
		return self.season(number = MetaPack.NumberSpecial, season = season, provider = provider, default = default)

	def seasonOfficial(self, season = False, provider = None, default = None):
		return self.season(number = MetaPack.NumberOfficial, season = season, provider = provider, default = default)

	def seasonUnofficial(self, season = False, provider = None, default = None):
		return self.season(number = MetaPack.NumberUnofficial, season = season, provider = provider, default = default)

	def _season(self, seasons, season, number = None, provider = None, default = None):
		if number == MetaPack.NumberOfficial or number == MetaPack.NumberUnofficial or number == MetaPack.NumberSpecial: number = MetaPack.NumberStandard
		if self.mLookup:
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
		else: # Reduced pack without a lookup table.
			for i in seasons:
				if self._extractNumber(i) == season:
					return i
		return None

	##############################################################################
	# EPISODE
	##############################################################################

	def episode(self, season = False, episode = False, seasons = None, sequential = None, number = None, provider = None, default = None, filter = False):
		try:
			# Do not use an index to access the episode: pack['seasons'][1]['episodes'][2]
			# Some shows (eg: Days of our Lives) have missing seasons.
			# Iterate and match by actual number.
			if self.mPack:
				if not sequential is None:
					season = 1
					episode = sequential

				if (season is False or season is None) and Tools.isInteger(episode):
					if number == MetaPack.NumberSpecial: season = 0
					elif number == MetaPack.NumberAbsolute or number == MetaPack.NumberSequential or number == MetaPack.NumberDate: season = 1
				if number == MetaPack.NumberSpecial: number = MetaPack.NumberStandard

				if not season is None and not episode is None:
					if seasons: # Already retrieved seasons.
						if not Tools.isArray(seasons): seasons = [seasons] # If a single season was passed in.
					else:
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

	def episodeOfficial(self, season = False, episode = False, sequential = None, provider = None, default = None):
		return self.episode(number = MetaPack.NumberOfficial, season = season, episode = episode, sequential = sequential, provider = provider, default = default)

	def episodeUnofficial(self, season = False, episode = False, sequential = None, provider = None, default = None):
		return self.episode(number = MetaPack.NumberUnofficial, season = season, episode = episode, sequential = sequential, provider = provider, default = default)

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
				except:
					# This should not happen.
					try: message = 'Episode Lookup Error [ID: %s | Season: %s | Episode: %s | Number: %s | Provider: %s | Index: %s]' % (str(self.id()), str(season), str(episode), str(number), str(provider), str(index))
					except: message = None
					Logger.error(message = message)
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
	# LAST
	##############################################################################

	def last(self, season = True, number = None, type = None, release = False, default = None):
		try:
			if number == MetaPack.NumberSpecial:
				if season is None:
					items = self.episode(season = 0, number = number, filter = False)
				else:
					items = self.season(season = 0, number = number)
					items = [items] if items else None
				number = MetaPack.NumberStandard
			else:
				if season is None:
					items = self.season()
				else:
					# This can massively reduce processing time for very large packs (eg: tt0103434).
					# Instead of scanning ALL episodes (retrieving and sorting), only retrieve the episodes of the last season.
					# This assumes the last episode is actually in the last season. Not sure if there are any discrepancies between Trakt/TVDb/IMDb where this is not the case.
					# items = self.episode(season = season, number = number, filter = False)
					seasons = self.lastSeason(number = number, type = type, release = release) if season is True else None
					items = self.episode(season = season, seasons = seasons, number = number, filter = False)

			if items:
				if type or release:
					time = Time.timestamp()
					end = 9999999999

					# Sort the list by season/episode number.
					# The episode list might not always be sorted according to number.
					# Unknown alternate/unofficial episodes might get added to the back of the list.
					# The episode list itself cannot be sorted, otherwise the lookup indexes will point to the incorrect item.
					# Sort here, so that we can correctly determine the last episode, which is used for MetaManager.metadataEpisodeNext().
					# Eg: My Name Is Earl S03E02, S03E08, S03E15
					# Use self.mLast, so we do not have to sort/reverse on every call.
					id = Tools.id(items)
					sorted = self.mLast.get(id)
					if sorted:
						items = sorted
					else:
						items = Tools.listSort(items, key = lambda i : self._extractNumber(i, MetaPack.NumberStandard))
						items = Tools.listReverse(items, inplace = True)
						self.mLast[id] = items

					for item in items:
						# NB: Also check time, not just status. In case the pack was not updated in a while, the status might be outdated compared to the current time.
						if (not type or self._extractType(item, type)) and (not release or item.get('status') == MetaPack.StatusEnded or (item.get('time') or end) < time):
							return item
				else:
					return items[-1]
		except: Logger.error()
		return default

	def lastSeason(self, number = None, type = None, release = False, default = None):
		return self.last(season = None, number = number, type = type, release = release, default = default)

	def lastSeasonOfficial(self, number = None, release = False, default = None):
		return self.lastSeason(type = MetaPack.NumberOfficial, number = number, release = release, default = default)

	def lastSeasonUnofficial(self, number = None, release = False, default = None):
		return self.lastSeason(type = MetaPack.NumberUnofficial, number = number, release = release, default = default)

	def lastSeasonUniversal(self, number = None, release = False, default = None):
		return self.lastSeason(type = MetaPack.NumberUniversal, number = number, release = release, default = default)

	def lastSeasonStandard(self, number = None, release = False, default = None):
		return self.lastSeason(type = MetaPack.NumberStandard, number = number, release = release, default = default)

	def lastSeasonSequential(self, number = None, release = False, default = None):
		return self.lastSeason(type = MetaPack.NumberSequential, number = number, release = release, default = default)

	def lastSeasonAbsolute(self, number = None, release = False, default = None):
		return self.lastSeason(type = MetaPack.NumberAbsolute, number = number, release = release, default = default)

	def lastSeasonSpecial(self, number = None, release = False, default = None):
		return self.lastSeason(type = MetaPack.NumberSpecial, number = number, release = release, default = default)

	def lastEpisode(self, season = True, number = None, type = None, release = False, default = None):
		return self.last(season = season, number = number, type = type, release = release, default = default)

	def lastEpisodeOfficial(self, season = True, number = None, release = False, default = None):
		return self.lastEpisode(type = MetaPack.NumberOfficial, season = season, number = number, release = release, default = default)

	def lastEpisodeUnofficial(self, season = True, number = None, release = False, default = None):
		return self.lastEpisode(type = MetaPack.NumberUnofficial, season = season, number = number, release = release, default = default)

	def lastEpisodeUniversal(self, season = True, number = None, release = False, default = None):
		return self.lastEpisode(type = MetaPack.NumberUniversal, season = season, number = number, release = release, default = default)

	def lastEpisodeStandard(self, season = True, number = None, release = False, default = None):
		return self.lastEpisode(type = MetaPack.NumberStandard, season = season, number = number, release = release, default = default)

	def lastEpisodeSequential(self, season = True, number = None, release = False, default = None):
		return self.lastEpisode(type = MetaPack.NumberSequential, season = season, number = number, release = release, default = default)

	def lastEpisodeAbsolute(self, season = True, number = None, release = False, default = None):
		return self.lastEpisode(type = MetaPack.NumberAbsolute, season = season, number = number, release = release, default = default)

	def lastEpisodeSpecial(self, season = True, number = None, release = False, default = None):
		return self.lastEpisode(type = MetaPack.NumberSpecial, season = season, number = number, release = release, default = default)

	##############################################################################
	# GENERATED
	##############################################################################

	def generated(self, item = None, default = None):
		try: return self._retrieve(base = 'generated', item = item, default = default)
		except: Logger.error()
		return default

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

	def countTotal(self, season = None, item = None, type = None, fallback = False, default = 0, combine = True):
		return self.count(number = MetaPack.ValueTotal, season = season, item = item, type = type, fallback = fallback, default = default, combine = combine)

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

			# Do not pass in the number to extract.
			# Otherwise it will use the "number" parameter as the lookup number, instead of the number to return.
			# This will cause calls like this to fail: pack.numberDate(season = 2, episode = 3)
			#return self._retrieve(base = 'number', season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, part = part, provider = provider, default = default, combine = combine)
			result = self._retrieve(base = 'number', number = [None, number], season = season, episode = episode, sequential = sequential, movie = movie, item = item, part = part, provider = provider, default = default, combine = combine)
			if not result is None: return result
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

	def numberDate(self, season = None, episode = None, sequential = None, item = None, part = None, provider = None, default = None, combine = True):
		return self.number(number = MetaPack.NumberDate, season = season, episode = episode, sequential = sequential, item = item, part = part, provider = provider, default = default, combine = combine)

	def numberDateSeason(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberDate(part = MetaPack.PartSeason, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberDateEpisode(self, season = None, episode = None, sequential = None, item = None, provider = None, default = None, combine = True):
		return self.numberDate(part = MetaPack.PartEpisode, season = season, episode = episode, sequential = sequential, item = item, provider = provider, default = default, combine = combine)

	def numberSeason(self, season = None, episode = None, sequential = None, movie = None, item = None, number = None, provider = None, default = None, combine = True):
		return self.number(part = MetaPack.PartSeason, season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, provider = provider, default = default, combine = combine)

	def numberEpisode(self, season = None, episode = None, sequential = None, movie = None, item = None, number = None, provider = None, default = None, combine = True):
		return self.number(part = MetaPack.PartEpisode, season = season, episode = episode, sequential = sequential, movie = movie, item = item, number = number, provider = provider, default = default, combine = combine)

	def numberLast(self, season = True, number = None, part = None, provider = None, type = None, default = None, release = False, combine = True):
		try:
			item = self.last(season = season, number = number, type = type, release = release, default = None)
			if item: return self.number(item = item, number = number, part = part, provider = provider, default = default, combine = combine)
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

	def numberLastDate(self, season = True, part = None, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLast(number = MetaPack.NumberDate, season = season, part = part, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastDateSeason(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastDate(part = MetaPack.PartSeason, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

	def numberLastDateEpisode(self, season = True, provider = None, type = None, default = None, release = False, combine = True):
		return self.numberLastDate(part = MetaPack.PartEpisode, season = season, provider = provider, type = type, default = default, release = release, combine = combine)

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
		try:
			if Tools.isArray(type):
				types = self._retrieve(base = 'type', season = season, episode = episode, sequential = sequential, item = item, default = default)
				if types and all(types.get(i) for i in type): return True
			else:
				return self._retrieve(base = 'type', season = season, episode = episode, sequential = sequential, item = item, type = type, default = default)
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

	def typeAlternate(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = Media.Alternate, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeOuter(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = Media.Outer, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeInner(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = Media.Inner, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeMiddle(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = Media.Middle, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typePremiere(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = Media.Premiere, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typePremiereOuter(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = (Media.Premiere, Media.Outer), season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typePremiereInner(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = (Media.Premiere, Media.Inner), season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typePremiereMiddle(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = (Media.Premiere, Media.Middle), season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeFinale(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = Media.Finale, season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeFinaleOuter(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = (Media.Finale, Media.Outer), season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeFinaleInner(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = (Media.Finale, Media.Inner), season = season, episode = episode, sequential = sequential, item = item, default = default)

	def typeFinaleMiddle(self, season = None, episode = None, sequential = None, item = None, default = None):
		return self.type(type = (Media.Finale, Media.Middle), season = season, episode = episode, sequential = sequential, item = item, default = default)

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

	@classmethod
	def titleGeneric(self, title):
		return Regex.match(data = title, expression = self._expression(2), cache = True)

	##############################################################################
	# STATUS
	##############################################################################

	def status(self, season = None, episode = None, sequential = None, movie = None, item = None, default = None):
		try: return self._retrieve(base = 'status', season = season, episode = episode, sequential = sequential, movie = movie, item = item, default = default)
		except: Logger.error()
		return default

	##############################################################################
	# INTERVAL
	##############################################################################

	def interval(self, season = None, sequential = None, movie = None, item = None, default = None):
		try: return self._retrieve(base = 'interval', season = season, sequential = sequential, movie = movie, item = item, default = default)
		except: Logger.error()
		return default

	##############################################################################
	# SUPPORT
	##############################################################################

	def support(self, season = None, episode = None, sequential = None, item = None, default = None):
		try: return self._retrieve(base = 'support', season = season, episode = episode, sequential = sequential, item = item, default = default)
		except: Logger.error()
		return default

	##############################################################################
	# INCORRECT
	##############################################################################

	def incorrect(self, season = None, episode = None, sequential = None, item = None, default = None):
		try: return self._retrieve(base = 'incorrect', season = season, episode = episode, sequential = sequential, item = item, default = default)
		except: Logger.error()
		return default
