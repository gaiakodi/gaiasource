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

from lib.modules import trakt

from lib.modules.tools import Logger, Media, Kids, Selection, Settings, Tools, System, Time, Regex, Language, Converter, Math
from lib.modules.interface import Dialog, Loader, Translation, Format, Directory
from lib.modules.network import Networker
from lib.modules.convert import ConverterDuration, ConverterTime
from lib.modules.playback import Playback
from lib.modules.account import Trakt, Imdb, Tmdb
from lib.modules.parser import Parser, Raw
from lib.modules.clean import Genre, Title
from lib.modules.cache import Cache, Memory
from lib.modules.concurrency import Pool, Lock, Semaphore

from lib.meta.cache import MetaCache
from lib.meta.image import MetaImage
from lib.meta.tools import MetaTools
from lib.meta.processors.imdb import MetaImdb
from lib.meta.processors.tmdb import MetaTmdb
from lib.meta.processors.fanart import MetaFanart

class Movies(object):

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, media = Media.TypeMovie, kids = Selection.TypeUndefined):
		self.mMetatools = MetaTools.instance()
		self.mCache = Cache.instance()

		self.mDeveloper = System.developerVersion()
		self.mDetail = self.mMetatools.settingsDetail()
		self.mLimit = self.mMetatools.settingsPageMovie()
		self.mLimitSearch = self.mMetatools.settingsPageSearch()

		self.mMedia = media
		if self.mMedia == Media.TypeDocumentary:
			self.mCategory = 'documentary'
			self.mCategoryTheatre = 'documentary'
			self.mVotes = 10000
			self.mAwards = 'oscar_winners'
		elif self.mMedia == Media.TypeShort:
			self.mCategory = 'short,tvshort' # Do not include the "video" category from IMDb here.
			self.mCategoryTheatre = 'short,tvshort'
			self.mVotes = 10000
			self.mAwards = 'oscar_winners'
		else:
			self.mCategory = 'feature,movie,tv_movie'
			self.mCategoryTheatre = 'feature'
			self.mVotes = 100000
			self.mAwards = 'oscar_best_picture_winners'

		self.mKids = kids
		self.mKidsOnly = self.mMetatools.kidsOnly(kids = self.mKids)

		self.mCertificates = None
		self.mRestriction = 0
		if self.mKidsOnly:
			self.mCertificates = []
			self.mRestriction = Settings.getInteger('general.kids.restriction')
			if self.mRestriction >= 0:
				self.mCertificates.append('G')
			if self.mRestriction >= 1:
				self.mCertificates.append('PG')
			if self.mRestriction >= 2:
				self.mCertificates.append('PG-13')
			if self.mRestriction >= 3:
				self.mCertificates.append('R')
			self.mCertificates = '&certificates=' + self.certificatesFormat(self.mCertificates)
		else:
			self.mCertificates = ''

		self.mYear = Time.year()
		self.mLanguage = self.mMetatools.settingsLanguage()

		self.mModeRelease = False
		self.mModeSearch = False
		self.mModeMixed = False

		self.mAccountImdb = Imdb().dataId()
		self.mAccountTmdb = Tmdb().key()
		self.mAccountTrakt = Trakt().dataUsername()

		self.search_link = 'https://api.trakt.tv/search?type=movie&limit=%d&query=' % self.mLimitSearch
		self.people_link = 'https://imdb.com/search/name'
		self.persons_link = 'https://imdb.com/search/name?count=%d&start=1&name=%s' % (self.mLimitSearch, '%s')
		self.personlist_link = 'https://imdb.com/search/name?gender=male,female,non-binary,other&count=%d&start=1' % (self.mLimit)
		self.views_link = 'https://imdb.com/search/title?title_type=%s&languages=en&num_votes=1000,&production_status=released&sort=num_votes,desc&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)
		self.featured_link = 'https://imdb.com/search/title?title_type=%s&languages=en&num_votes=1000,&production_status=released&release_date=date[365],date[60]&sort=moviemeter,asc&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)
		self.person_link = 'https://imdb.com/search/title?title_type=%s&production_status=released&role=%s&sort=year,desc&count=%d&start=1%s' % (self.mCategory, '%s', self.mLimit, '%s')
		self.genre_link = 'https://imdb.com/search/title?title_type=%s&languages=en&num_votes=100,&release_date=,date[0]&genres=%s&sort=moviemeter,asc&count=%d&start=1%s' % (self.mCategory, '%s', self.mLimit, '%s')
		self.language_link = 'https://imdb.com/search/title?title_type=%s&num_votes=100,&production_status=released&languages=%s&sort=moviemeter,asc&count=%d&start=1%s' % (self.mCategory, '%s', self.mLimit, '%s')
		self.certification_link = 'https://imdb.com/search/title?title_type=%s&languages=en&num_votes=100,&production_status=released&certificates=%s&sort=moviemeter,asc&count=%d&start=1' % (self.mCategory, '%s', self.mLimit) # Does not use certificates, since it has it's own.
		self.year_link = 'https://imdb.com/search/title?title_type=%s&languages=en&num_votes=100,&production_status=released&year=%s,%s&sort=moviemeter,asc&count=%d&start=1%s' % (self.mCategory, '%s', '%s', self.mLimit, '%s')
		self.boxoffice_link = 'https://imdb.com/search/title?title_type=%s&languages=en&production_status=released&sort=boxoffice_gross_us,desc&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)
		self.oscars_link = 'https://imdb.com/search/title?title_type=%s&languages=en&production_status=released&groups=%s&sort=year,desc&count=%d&start=1%s' % (self.mCategory, self.mAwards, self.mLimit, self.mCertificates)
		self.theaters_link = 'https://imdb.com/search/title?title_type=%s&languages=en&num_votes=1000,&release_date=date[365],date[0]&sort=release_date_us,desc&count=%d&start=1%s' % (self.mCategoryTheatre, self.mLimit, self.mCertificates)
		self.rating_link = 'https://imdb.com/search/title?title_type=%s&num_votes=%d,&release_date=,date[0]&sort=user_rating,desc&count=%d&start=1%s' % (self.mCategoryTheatre, self.mVotes, self.mLimit, self.mCertificates)
		self.award_link = 'https://imdb.com/search/title?title_type=%s&languages=en&production_status=released&groups=%s&sort=year,desc&count=%d&start=1%s' % (self.mCategory, '%s', self.mLimit, self.mCertificates)

		self.famousfilmmaker_link = 'https://imdb.com/list/ls026411399/'
		self.famousdirector_link = 'https://imdb.com/list/ls000005319/'
		self.famouscinematographer_link = 'https://imdb.com/list/ls000045131/'
		self.famouswriter_link = 'https://imdb.com/list/ls026034645/'
		self.famousproducer_link = 'https://imdb.com/list/ls009401127/'
		self.famouseditor_link = 'https://imdb.com/list/ls020798362/'
		self.famouscomposer_link = 'https://imdb.com/list/ls026034696/'
		self.famousactor_link = 'https://imdb.com/list/ls000005354/'
		self.famousactress_link = 'https://imdb.com/list/ls000005315/'

		self.ratedimdbbest_link = 'https://imdb.com/search/title/?title_type=%s&groups=top_1000&sort=user_rating&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)
		self.ratedimdbworst_link = 'https://imdb.com/search/title/?title_type=%s&groups=bottom_1000&sort=user_rating,asc&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)
		self.ratedtmdbbest_link = '%s?sort=%s&order=%s&votes=1000' % (MetaTmdb.LinkDiscoverMovie, MetaTmdb.SortRating, MetaTmdb.OrderDescending)
		self.ratedtmdbworst_link = '%s?sort=%s&order=%s&votes=100' % (MetaTmdb.LinkDiscoverMovie, MetaTmdb.SortRating, MetaTmdb.OrderAscending)
		self.ratedtraktbest_link = 'https://api.trakt.tv/movies/popular?limit=%d&page=1' % self.mLimit
		self.ratedtraktworst_link = 'https://api.trakt.tv/users/mogodon/lists/worst-movies/items/movie?limit=%d&page=1' % self.mLimit

		# https://mdblist.com/lists/plexmetamanager/
		self.networknetflix_link = 'https://api.trakt.tv/users/plexmetamanager/lists/netflix-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkamazon_link = 'https://api.trakt.tv/users/plexmetamanager/lists/amazon-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkappletv_link = 'https://api.trakt.tv/users/plexmetamanager/lists/appletv-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkhbo_link = 'https://api.trakt.tv/users/plexmetamanager/lists/hbomax-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkdisney_link = 'https://api.trakt.tv/users/plexmetamanager/lists/disney-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkparamount_link = 'https://api.trakt.tv/users/plexmetamanager/lists/paramount-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkpeacock_link = 'https://api.trakt.tv/users/plexmetamanager/lists/peacock-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkhulu_link = 'https://api.trakt.tv/users/plexmetamanager/lists/hulu-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkshowtime_link = 'https://api.trakt.tv/users/plexmetamanager/lists/showtime-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkbritbox_link = 'https://api.trakt.tv/users/plexmetamanager/lists/britbox-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networknow_link = 'https://api.trakt.tv/users/plexmetamanager/lists/now-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkbet_link = 'https://api.trakt.tv/users/plexmetamanager/lists/bet-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkcrunchyroll_link = 'https://api.trakt.tv/users/plexmetamanager/lists/crunchyroll-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkall4_link = 'https://api.trakt.tv/users/plexmetamanager/lists/all4-movies/items/movie?limit=%d&page=1' % self.mLimit
		self.networkyoutube_link = 'https://api.trakt.tv/users/plexmetamanager/lists/youtube-movies/items/movie?limit=%d&page=1' % self.mLimit
		#self.networkdiscovery_link = 'https://api.trakt.tv/users/plexmetamanager/lists/discovery-movies/items/movie?limit=%d&page=1' % self.mLimit  # No movie list.
		#self.networkhayu_link = 'https://api.trakt.tv/users/plexmetamanager/lists/hayu-movies/items/movie?limit=%d&page=1' % self.mLimit  # No movie list.

		self.drugsgeneral_link = 'https://imdb.com/list/ls052149893/'
		self.drugsalcohol_link = 'https://imdb.com/list/ls000527140/'
		self.drugsmarijuana_link = 'https://imdb.com/list/ls036810850/'
		self.drugspsychedelics_link = 'https://imdb.com/list/ls054725090/'

		self.random1_link = 'https://imdb.com/list/ls091294718/'
		self.random2_link = 'https://imdb.com/list/ls080799519/'
		self.random3_link = 'https://imdb.com/list/ls054319665/'

		if self.mMedia == Media.TypeDocumentary or self.mMedia == Media.TypeShort:
			# Documentaries and Shorts do not have a TOP list. Simply use a list sorted by ratings.
			self.popular_link = 'https://imdb.com/search/title?title_type=%s&languages=en&production_status=released&sort=user_rating,desc&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)
			self.new_link = 'https://imdb.com/search/title?title_type=%s&languages=en&num_votes=100,&production_status=released&release_date=date[365],date[1]&sort=moviemeter,asc&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)
			self.home_link = 'https://imdb.com/search/title?online_availability=US/today/Amazon/subs,US/today/Amazon/paid,GB/today/Amazon/subs,GB/today/Amazon/paid,DE/today/Amazon/subs,DE/today/Amazon/paid&title_type=%s&languages=en&num_votes=50,&production_status=released&release_date=date[730],date[30]&sort=moviemeter,asc&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)
			#self.disc_link = None
			self.trending_link = self.featured_link
		else:
			self.popular_link = 'https://imdb.com/search/title?title_type=%s&languages=en&num_votes=1000,&production_status=released&groups=top_1000&sort=moviemeter,asc&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)
			self.new_link = 'https://imdb.com/search/title?title_type=%s&languages=en&num_votes=100,&production_status=released&release_date=date[%d],date[1]&sort=moviemeter,asc&count=%d&start=1%s' % (self.mCategory, 180 if self.mKidsOnly else 90, self.mLimit, self.mCertificates)
			self.home_link = 'https://imdb.com/search/title?online_availability=US/today/Amazon/subs,US/today/Amazon/paid,GB/today/Amazon/subs,GB/today/Amazon/paid,DE/today/Amazon/subs,DE/today/Amazon/paid&title_type=%s&languages=en&num_votes=100,&production_status=released&release_date=date[365],date[30]&sort=moviemeter,asc&count=%d&start=1%s' % (self.mCategory, self.mLimit, self.mCertificates)

			# This redirects to an Amazon shop page.
			# Another alternative might be (not managed by IMDb admins): https://imdb.com/list/ls093173574/
			#self.disc_link = None if self.mLimit <= 20 else ('https://imdb.com/list/ls016522954/?title_type=%s&languages=en&num_votes=50,&production_status=released&release_date=date[365],date[30]&sort=moviemeter,asc' % self.mCategory) # Has some extra movies to home_link. Updated often and maintained by IMDB editors.

			# This page has been removed by IMDb.
			# They now have various IMDb picks at: https://www.imdb.com/imdbpicks/
			# There is also one for streaming: https://www.imdb.com/list/ls566661486/mediaviewer/rm3920182529
			# However, this list is not in a normal view, but uses the IMDb "mediaviewer", which is a slideshow.
			# The mediaviewer pages contain the JSON data for the items.
			# However, it only has the JSON data of a few items before/after the current item in the slideshow.
			# Hence, the mediaviewer page never contains the data of all 30 items in the list, but only a subset.
			# The only way to get all data, is to scroll through the entire slideshow. With each step, the URL will change and the 'rm...' partr updates.
			# Even when this list is loadaed normally: https://www.imdb.com/list/ls566661486
			# It does not show in the normal view, but ust shows images for the 30 titles.
			# It however, does not contain an titles/years or IMDb IDs, but only an image and a link that cannot be used to get the ID, except visiting each link.
			#self.disc_link = None if self.mLimit <= 20 else ('https://imdb.com/imdbpicks/new-to-vod-dvd-blu-ray/ls016522954/?title_type=%s&languages=en&num_votes=50,&production_status=released&release_date=date[365],date[30]&sort=moviemeter,asc' % self.mCategory) # Has some extra movies to home_link. Updated often and maintained by IMDB editors.

			self.trending_link = 'https://api.trakt.tv/movies/trending?limit=%d&page=1' % self.mLimit

		self.traktlists_link = 'https://api.trakt.tv/users/me/lists'
		self.traktlikedlists_link = 'https://api.trakt.tv/users/likes/lists?limit=10000'
		self.traktlist_link = 'https://api.trakt.tv/users/%s/lists/%s/items?limit=%d&page=1' % ('%s', '%s', self.mLimit)
		self.traktcollection_link = 'https://api.trakt.tv/users/me/collection/movies'
		self.traktwatchlist_link = 'https://api.trakt.tv/users/me/watchlist/movies?limit=%d&page=1' % self.mLimit
		self.traktrecommendations_link = 'https://api.trakt.tv/recommendations/movies' # No paging support. Only a limit of up to 100 items.
		self.trakthistory_link = 'https://api.trakt.tv/users/me/history/movies?limit=%d&page=1' % self.mLimit
		self.traktunfinished_link = 'https://api.trakt.tv/sync/playback/movies'

		self.imdblistname_link = 'https://imdb.com/list/%s/?view=detail&sort=alpha,asc&title_type=%s&start=1' % ('%s', self.mCategory)
		self.imdblistdate_link = 'https://imdb.com/list/%s/?view=detail&sort=date_added,desc&title_type=%s&start=1' % ('%s', self.mCategory)
		self.imdblists_link = 'https://imdb.com/user/%s/lists?sort=mdfd&order=desc' % self.mAccountImdb
		self.imdbcollection_link = 'https://imdb.com/user/%s/watchlist?sort=alpha,asc&title_type=%s' % (self.mAccountImdb, self.mCategory)
		self.imdbwatchlist_link = 'https://imdb.com/user/%s/watchlist?sort=date_added,desc&title_type=%s' % (self.mAccountImdb, self.mCategory)
		self.imdbratings_link = 'https://imdb.com/user/%s/ratings?sort=your_rating,desc&mode=detail&title_type=%s' % (self.mAccountImdb, self.mCategory) # Does not use the title_type parameter. Still add it to avoid caching between different types.

	##############################################################################
	# RETRIEVE
	##############################################################################

	def retrieve(self, link = None, items = None, detailed = True, menu = True, full = False, clean = True, quick = None, limit = None, refresh = False, next = True):
		try:
			self.mModeRelease = link in ['new', 'home', 'disc']
			if items is None: items = []

			original = link
			try: link = getattr(self, link + '_link')
			except: pass

			domain = Networker.linkDomain(link, subdomain = False, topdomain = False, ip = False, scheme = False, port = False)

			if original == 'quick':
				self.mModeMixed = True # Hides 0-1% and 99-100% progress labels.
				items = self.quick(limit = limit)
				if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
				items = self.sort(items = items, type = 'quick')

			elif original and original.startswith('home'): # Startswith, since paging parameters are added to the link.
				self.mModeRelease = True
				items = self._home(refresh = refresh)
				items = self.page(link = original, items = items)
				if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

			elif domain == 'trakt':

				if '/users/' in link:
					if self.traktcollection_link in link:
						items = self.cache('cacheRefreshLong', refresh, self.traktList, link = self.traktcollection_link, user = self.mAccountTrakt)
						items = self.page(link = link, items = items)
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

					elif '/me/' in link:
						items = self.cache('cacheRefreshLong', refresh, self.traktList, link = link, user = self.mAccountTrakt)
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
						items = self.sort(items = items)

					else: # Eg: Networks and Rated categories.
						items = self.cache('cacheRefreshExtended', refresh, self.traktList, link = link, user = self.mAccountTrakt)
						if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
						items = self.sort(items = items)

				elif self.search_link in link:
					self.mModeSearch = True
					items = self.cache('cacheMedium', refresh, self.traktList, link = link, user = self.mAccountTrakt)

					# In case Trakt is down.
					if items:
						# Hide extended editions, since otherwise some users might scrape that one instead of the normal edition and then find fewer/no links.
						# Only do this if the user did not specifically search for edition-related keywords.
						# Eg: Search "lord rings":
						#	{"imdb": "tt0120737", "tmdb": "120", "trakt": "88", "title": "The Lord of the Rings: The Fellowship of the Ring", "year": 2001}
						#	{"imdb": "tt21811588", "tmdb": "1032873", "trakt": "830703", "title": "The Lord of the Rings - The Fellowship of the Ring (Extended Edition)", "year": null}
						if not Regex.match(data = link, expression = '(extend|special|edition|version)'):
							items = [i for i in items if not(Regex.match(data = i['title'], expression = '[\(\[].*?edition.*[\)\]]$') and (not 'year' in i or not i['year'] or not 'premiered' in i or not i['premiered'] or not 'duration' in i or not i['duration']))]
					else:
						query = Regex.extract(data = link, expression = 'query=(.*?)(?:$|&)')
						if query:
							query = Networker.linkUnquote(query)
							items = self.cache('cacheMedium', refresh, MetaTmdb.searchMovie, query = query, language = self.mLanguage)
							# Hide extended editions, since otherwise some users might scrape that one instead of the normal edition and then find fewer/no links.
							if not Regex.match(data = link, expression = '(extend|special|edition|version)'):
								items = [i for i in items if not(Regex.match(data = i['title'], expression = '[\(\[].*?edition.*[\)\]]$') and (not 'year' in i or not i['year'] or not 'premiered' in i or not i['premiered']))]

					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

				elif self.traktrecommendations_link in link:
					items = self.cache('cacheRefreshExtended', refresh, self.traktList, link = self.traktrecommendations_link + '?limit=100', user = self.mAccountTrakt, next = False)
					items = self.page(link = link, items = items, maximum = 100)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

				elif self.traktunfinished_link in link:
					items = self.cache('cacheRefreshLong', refresh, self.traktList, link = self.traktunfinished_link, user = self.mAccountTrakt)
					items = self.page(link = link, items = items)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

				else:
					items = self.cache('cacheMedium', refresh, self.traktList, link = link, user = self.mAccountTrakt)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
					if Networker.linkClean(link = self.ratedtraktbest_link, parametersStrip = True) in link: items = self.sort(items = items, type = 'best')

			elif domain == 'imdb':

				if '/list/' in link:
					items = self.cache('cacheExtended', refresh, self.imdbList, link = link, full = full)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
					items = self.sort(items = items)

				elif '/user/' in link:
					items = self.cache('cacheRefreshLong', refresh, self.imdbList, link = link, full = full)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
					items = self.sort(items = items)

				elif 'online_availability' in link:
					self.mModeRelease = True
					items = self.cache('cacheRefreshLong', refresh, self.imdbList, link = link, full = full)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
				else:
					items = self.cache('cacheMedium', refresh, self.imdbList, link = link, full = full)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

			elif domain == 'themoviedb' or domain == 'themdb' or domain == 'tmdb':

				if '/list/' in link:
					items = self.cache('cacheMedium', refresh, MetaTmdb.list, link = link, language = self.mLanguage)
					items = self.page(link = link, items = items)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)
					items = self.sort(items = items, type = 'best' if 'sort=best' in link else 'worst' if 'sort=worst' in link else None)

				elif MetaTmdb.LinkRatedMovie in link:
					items = self.cache('cacheExtended', refresh, MetaTmdb.ratedMovie, link = link, language = self.mLanguage)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

				elif MetaTmdb.LinkDiscoverMovie in link:
					items = self.cache('cacheExtended', refresh, MetaTmdb.discoverMovie, link = link, language = self.mLanguage)
					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

				elif MetaTmdb.LinkSearchMovie in link:
					self.mModeSearch = True
					items = self.cache('cacheMedium', refresh, MetaTmdb.searchMovie, link = link, language = self.mLanguage)

					# Hide extended editions, since otherwise some users might scrape that one instead of the normal edition and then find fewer/no links.
					if not Regex.match(data = link, expression = '(extend|special|edition|version)'):
						items = [i for i in items if not(Regex.match(data = i['title'], expression = '[\(\[].*?edition.*[\)\]]$') and (not 'year' in i or not i['year'] or not 'premiered' in i or not i['premiered']))]

					if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

			elif items:
				if detailed: items = self.metadata(items = items, clean = clean, quick = quick, refresh = refresh)

		except: Logger.error()

		if link:
			genre = (self.search_link in link and not self.people_link in link) or link == 'quick'
			kids = not self.people_link in link
			search = self.search_link in link
		else:
			genre = False
			kids = False
			search = False

		return self.process(items = items, menu = menu, genre = genre, kids = kids, search = search, refresh = refresh, limit = limit, next = next)

	# genre: Filter by genre depending on wether the items are movies, docus, or shorts.
	# kids: Filter by age restriction.
	# search: Wether or not the items are from search results.
	# duplicate: Filter out duplicates.
	# release: Filter out unreleased items. If True, return any items released before today. If date-string,return items before the date. If integer, return items older than the given number of days.
	# limit: Limit the number of items. If True, use the setting's limit. If integer, limit up to the given number.
	def process(self, items, menu = True, genre = True, kids = True, search = False, duplicate = True, release = False, limit = False, refresh = False, next = True):
		if items:
			if duplicate: items = self.mMetatools.filterDuplicate(items = items)

			if genre:
				if self.mMedia == Media.TypeDocumentary: items = [i for i in items if not 'genre' in i or not i['genre'] or ('genre' in i and 'documentary' in [j.lower() for j in i['genre']])]
				elif self.mMedia == Media.TypeShort: items = [i for i in items if not 'genre' in i or not i['genre'] or ('genre' in i and 'short' in [j.lower() for j in i['genre']])]

			if kids: items = self.mMetatools.filterKids(items = items, kids = self.mKids)

			if release:
				date = None
				days = None
				if release is True: days = 1
				elif Tools.isInteger(release) and release < 10000: days = release
				elif release: date = release
				items = self.mMetatools.filterRelease(items = items, date = date, days = days)

			if limit: items = self.mMetatools.filterLimit(items = items, limit = self.mLimit if limit is True else limit)

			if items and menu:
				if refresh: # Check Context commandMetadataList() for more info.
					Loader.hide()
					Directory.refresh()
				else:
					self.menu(items, next = next)

		if not items:
			Loader.hide()
			if menu: Dialog.notification(title = 32010 if search else 32001, message = 33049, icon = Dialog.IconInformation)
		return items

	def cache(self, cache_, refresh_, *args, **kwargs):
		return Tools.executeFunction(self.mCache, 'cacheClear' if refresh_ else cache_, *args, **kwargs)

	##############################################################################
	# PAGE
	##############################################################################

	def page(self, link, items, limit = None, sort = None, maximum = None, next = True):
		# Some Trakt API endpoint do not support pagination.
		# If the user has many watched shows, these list can get very long, making menu loading slow while extended metadata is retrieved.
		# Manually handle paging.

		page = 1
		if limit is None: limit = self.mLimit
		parameters = Networker.linkParameters(link = link)
		if 'limit' in parameters and 'page' in parameters: page = int(parameters['page'])
		parameters['page'] = page + 1
		parameters['limit'] = limit

		items = items[(page - 1) * limit : page * limit]

		# Sort first, since we want to page in accordance to the user's preferred sorting.
		if sort: items = self.sort(items = items, type = sort)

		if len(items) >= limit and (not maximum or (page + 1) * limit <= maximum):
			next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')
			for item in items: item['next'] = next

		for item in items:
			if 'nextFixed' in item: item['next'] = item['nextFixed']

		return items

	##############################################################################
	# SORT
	##############################################################################

	def sort(self, items, type = None, force = False):
		try:
			attribute = None
			reverse = None

			if type == 'best':
				type = None
				force = True
				attribute = 3
				reverse = True
			elif type == 'worst':
				type = None
				force = True
				attribute = 3
				reverse = False
			elif type == 'release':
				type = None
				force = True
				attribute = 5
				reverse = True
			elif type == 'internal':
				type = None
				force = True
				attribute = 999
				reverse = True

			if force or Settings.getBoolean('navigation.sort'):
				dummyString = 'zzzzzzzzzz'

				attribute = Settings.getInteger('navigation.sort.%s.type' % (type if type else self.mMedia)) if attribute is None else attribute
				reverse = Settings.getInteger('navigation.sort.%s.order' % (type if type else self.mMedia)) == 1 if (reverse is None and not attribute == 1) else reverse
				if type == 'quick':
					if attribute == 1:
						attribute = 999
						reverse = True
					elif attribute == 8:
						reverse = True

				if attribute == 0:
					items = Tools.listShuffle(items)
				elif attribute > 1:
					if attribute == 2:
						if Settings.getBoolean('navigation.sort.article'):
							items = sorted(items, key = lambda k : Regex.remove(data = (k.get('title') or '').lower(), expression = '(^the\s|^an?\s)', group = 1) or dummyString, reverse = reverse)
						else:
							items = sorted(items, key = lambda k : (k.get('title') or '').lower() or dummyString, reverse = reverse)
					elif attribute == 3:
						items = sorted(items, key = lambda k : float(k.get('rating') or 0.0), reverse = reverse)
					elif attribute == 4:
						items = sorted(items, key = lambda k : int(k.get('votes') or 0), reverse = reverse)
					elif attribute == 5:
						items = sorted(items, key = lambda k : k.get('premiered') or dummyString, reverse = reverse)
					elif attribute == 6:
						items = sorted(items, key = lambda k : k.get('timeAdded') or 0, reverse = reverse)
					elif attribute == 7:
						items = sorted(items, key = lambda k : k.get('timeWatched') or 0, reverse = reverse)
					elif attribute == 8:
						items = sorted(items, key = lambda k : k.get('sort') or 0, reverse = reverse)
					elif attribute == 999:
						items = sorted(items, key = lambda k : k.get('sort') or 0, reverse = reverse)
				elif reverse:
					items.reverse()

		except: Logger.error()
		return items

	##############################################################################
	# RANDOM
	##############################################################################

	def random(self, menu = True, release = True, limit = True, quick = None, next = True):
		if limit is True: limit = self.mLimit
		elif not limit: limit = 50

		limitSingle = 3
		limitLists = Math.roundUp(limit / float(limitSingle))
		if quick is None: quick = -limitSingle

		links = [
			self.random1_link,
			self.random2_link,
			self.random3_link,

			self.views_link,
			self.featured_link,
			self.boxoffice_link,
			self.oscars_link,
			self.theaters_link,
			self.rating_link,
			self.popular_link,
			self.new_link,
		]

		years = self.years(menu = False)
		if years: links.extend(Tools.listPick([i['link'] for i in years], count = 5))

		genres = self.genres(menu = False)
		if genres: links.extend(Tools.listPick([i['link'] for i in genres], count = 5))

		links = Tools.listShuffle(links)
		links.insert(0, self.home_link) # Always add the home link, to get the latests movies.

		# First try if there are already cached lists.
		if quick is True or quick is False:
			result = []
			for link in links:
				if self.mCache.cacheExists(self.imdbList, link):
					result.append(link)
			if result:
				if len(result) < limitLists:
					for link in links:
						if not link in result:
							result.append(link)
							if len(result) >= limitLists: break
				links = result

		links = links[:limitLists]

		def _random(link, items, quick):
			result = self.mCache.cacheMedium(self.imdbList, link)
			result = self.metadata(items = result, quick = quick)
			if result: items.extend(result)

		items = []
		threads = [Pool.thread(target = _random, kwargs = {'link' : link, 'items' : items, 'quick' : quick}, start = True) for link in links]
		[thread.join() for thread in threads]

		items = self.mMetatools.filterDuplicate(items = items)
		for item in items: item['next'] = System.command(action = 'moviesRandom')
		items = Tools.listShuffle(items)

		return self.process(items = items, menu = menu, release = 30 if release is True else release, limit = limit, next = next)

	##############################################################################
	# QUICK
	##############################################################################

	def quick(self, limit = None):
		# NB: Pass in the media, otherwise Movies/Docus/Shorts will all use the same cached results.
		return self.cache('cacheRefresh', False, self._quick, limit = limit, media = self.mMedia)

	def _quick(self, limit = None, media = None):
		def update(items, category, data):
			result = Movies(media = self.mMedia, kids = self.mKids).retrieve(link = data['link'], quick = True, detailed = False, menu = False)
			if result: items.append({'items' : result, 'category' : category, 'limit' : data['limit'], 'sort' : data['sort']})

		progress = Math.roundUp(Settings.getInteger('menu.quick.progress') / 2.0)
		categories = {
			'unfinished' : {'link' : 'traktunfinished', 'limit' : [progress, progress], 'sort' : [11, 10]}, # Corresponds with shows.py - to interleave movie-show mixed menus.
			'watchlist' : {'link' : 'traktwatchlist', 'limit' : Settings.getInteger('menu.quick.watchlist'), 'sort' : 8},
			'history' : {'link' : 'trakthistory', 'limit' : Settings.getInteger('menu.quick.history'), 'sort' : 7},
			'recommended' : {'link' : 'traktrecommendations', 'limit' : Settings.getInteger('menu.quick.recommended'), 'sort' : 3},
			'arrivals' : {'link' : 'home', 'limit' : Settings.getInteger('menu.quick.arrivals'), 'sort' : 2},
			'popular' : {'link' : 'popular', 'limit' : Settings.getInteger('menu.quick.popular'), 'sort' : 1},
			'trending' : {'link' : 'trending', 'limit' : Settings.getInteger('menu.quick.trending'), 'sort' : 1},
			'featured' : {'link' : 'featured', 'limit' : Settings.getInteger('menu.quick.featured'), 'sort' : 1},
		}

		if limit:
			total = 0
			for value in categories.values():
				limited = value['limit']
				if Tools.isArray(limited): total += sum(limited)
				else: total += limited
			ratio = limit / float(total)
			for key in categories.keys():
				limited = categories[key]['limit']
				if Tools.isArray(limited): categories[key]['limit'] = [Math.roundUp(ratio * i) for i in limited]
				else: categories[key]['limit'] = Math.roundUp(ratio * limited)

		items = []
		threads = []
		for key, value in categories.items():
			if (Tools.isArray(value['limit']) and max(value['limit'])) or value['limit']:
				threads.append(Pool.thread(target = update, kwargs = {'items' : items, 'category' : key, 'data' : value}, start = True))
		[thread.join() for thread in threads]

		# Sort items by the 'sort' rank of the category.
		# Otherwise, since threads can finish at different times, they add items in random order to the results.
		# Otherwise, self.mMetatools.filterContains() below might move down items that appear in multiple lists.
		# Eg: X appear in Unfinished and Arrivals. It should be shown at the top, since Unfinished is ranked higher.
		# However, if Arrivals finishes first, it will be added to the results before we get to the Unfinished list, which will not add the item due to filterContains().
		items = Tools.listSort(data = items, key = lambda i : max(i['sort']) if Tools.isArray(i['sort']) else i['sort'], reverse = True)

		result = []
		for item in items:
			values = self.mMetatools.filterDuplicate(items = item['items'])
			if self.mMedia == Media.TypeDocumentary or self.mMedia == Media.TypeShort: values = self.mMetatools.filterGenre(items = item['items'], genre = self.mMedia)

			category = item['category']
			try: limited = item['limit']
			except: limited = 5
			try: sort = item['sort']
			except: sort = 0

			if category == 'unfinished':
				if limited[0]:
					value = [i for i in values if not self.mMetatools.filterContains(items = result, item = i)]
					value = Tools.listSort(data = value, key = lambda i : i['timeWatched'] if 'timeWatched' in i and i['timeWatched'] else 0, reverse = True)
					value = value[:limited[0]]
					for i in value: i['sort'] = sort[0]
					result.extend(value)

				if limited[1]:
					value = [i for i in values if not self.mMetatools.filterContains(items = result, item = i)]
					value = Tools.listShuffle(value)
					value = value[:limited[1]]
					for i in value: i['sort'] = sort[1]
					result.extend(value)
			elif limited:
				value = [i for i in values if not self.mMetatools.filterContains(items = result, item = i)]
				if category == 'history': value = Tools.listSort(data = value, key = lambda i : i['timeWatched'] if 'timeWatched' in i and i['timeWatched'] else 0, reverse = True)
				else: value = Tools.listShuffle(value)
				value = value[:limited]
				for i in value: i['sort'] = sort
				result.extend(value)

		# Docus/shorts that have too few items.
		if len(result) < (self.mMetatools.settingsPageMixed() / 2.0):
			for item in items:
				values = self.mMetatools.filterDuplicate(items = item['items'])
				if self.mMedia == Media.TypeDocumentary or self.mMedia == Media.TypeShort: values = self.mMetatools.filterGenre(items = item['items'], genre = self.mMedia)
				value = [i for i in values if not self.mMetatools.filterContains(items = result, item = i)]
				value = Tools.listShuffle(value)
				for i in value: i['sort'] = 0
				result.extend(value)

		result = Tools.listUnique(result)
		result = self.sort(items = result, type = 'internal')
		result = result[:limit if limit else self.mMetatools.settingsPageMixed()]

		# Retrieve the detailed metadata here.
		# Otherwise if the quick menu was previously cached and contains an item that does not have detailed metadata in the local database, the menu will take longer to load while this new metadata is retrieved.
		# Already retrieve here when this function cache is refreshed, so that the next time the quick menu is shown, it can be loaded quickly because the detailed metadata is already available.
		self.metadata(items = result)

		for i in result:
			try: del i['next']
			except: pass

		return result

	##############################################################################
	# ARRIVALS
	##############################################################################

	def arrivals(self, menu = True, quick = None, refresh = False, next = True):
		self.mModeRelease = True
		setting = Settings.getInteger('menu.arrival.' + self.mMedia)

		if setting == 0: return self.retrieve(self.new_link, menu = menu, quick = quick, refresh = refresh, next = next)
		elif setting == 1: return self.home(menu = menu, quick = quick, refresh = refresh, next = next)
		elif setting == 2: return self.retrieve(self.popular_link, menu = menu, quick = quick, refresh = refresh, next = next)
		elif setting == 3: return self.retrieve(self.theaters_link, menu = menu, quick = quick, refresh = refresh, next = next)
		elif setting == 4: return self.retrieve(self.trending_link, menu = menu, quick = quick, refresh = refresh, next = next)
		else: return self.home(menu = menu, quick = quick, refresh = refresh, next = next)

	# Called from trakt.py.
	def arrivalsRefresh(self):
		self.retrieve(link = self.traktunfinished_link, menu = False)
		self.retrieve(link = self.trakthistory_link, menu = False)

	##############################################################################
	# HOME
	##############################################################################

	def home(self, menu = True, quick = None, refresh = False, next = True):
		self.mModeRelease = True
		return self.retrieve(link = 'home', menu = menu, quick = quick, refresh = refresh, next = next)

	def _home(self, refresh = False):
		return self.cache('cacheLong', refresh, self._homeRetrieve)

	def _homeRetrieve(self):
		threads = []
		cutoff = int(self.mLimit / 2.0)

		itemsImdb = [[], [], []]
		threads.append(Pool.thread(target = self._homeImdb, kwargs = {'items' : itemsImdb, 'level' : 0}, start = True))
		threads.append(Pool.thread(target = self._homeImdb, kwargs = {'items' : itemsImdb, 'level' : 1}, start = True))
		threads.append(Pool.thread(target = self._homeImdb, kwargs = {'items' : itemsImdb, 'level' : 2}, start = True))

		itemsTmdb = [[], [], []]
		threads.append(Pool.thread(target = self._homeTmdb, kwargs = {'items' : itemsTmdb, 'level' : 0}, start = True))
		threads.append(Pool.thread(target = self._homeTmdb, kwargs = {'items' : itemsTmdb, 'level' : 1}, start = True))
		threads.append(Pool.thread(target = self._homeTmdb, kwargs = {'items' : itemsTmdb, 'level' : 2}, start = True))

		[thread.join() for thread in threads]

		itemsImdb = itemsImdb[1] + itemsImdb[2][:cutoff] + Tools.listInterleave(itemsImdb[2][cutoff:], itemsImdb[0])
		itemsImdb = self.mMetatools.filterDuplicate(items = itemsImdb, id = True, title = False)

		itemsTmdb = itemsTmdb[1] + itemsTmdb[2][:cutoff] + Tools.listInterleave(itemsTmdb[2][cutoff:], itemsTmdb[0])
		itemsTmdb = self.mMetatools.filterDuplicate(items = itemsTmdb, id = True, title = False)

		items = Tools.listInterleave(itemsImdb, itemsTmdb)
		items = self.mMetatools.filterDuplicate(items = items, id = True, title = True) # Also filter by title, since TMDb items only have a TMDb ID.
		#items = self.sort(items = items, type = 'release') # Does not work, IMDb does not have a date, only a year.

		# Sometimes older movies are returned.
		# Remove any that were not released in the past 2 years.
		year = self.mYear - 1
		items = [i for i in items if not 'year' in i or not i['year'] or i['year'] >= year]

		# Move very bad movies to the end.
		good = []
		medium = []
		bad = []
		for i in items:
			try: ratingImdb = i['temp']['imdb']['rating']
			except: ratingImdb = None
			try: ratingTmdb = i['temp']['tmdb']['rating']
			except: ratingTmdb = None

			rating = []
			if ratingImdb: rating.append(ratingImdb)
			if ratingTmdb: rating.append(ratingTmdb)

			if rating:
				rating = sum(rating) / len(rating)
				if rating >= 5.0: good.append(i)
				elif rating < 4.0: bad.append(i)
				else: medium.append(i)
			else:
				medium.append(i)
		items = good + medium + bad

		# Remove 'next', since we manually page.
		if items:
			for i in items:
				try: del i['next']
				except: pass

			# Add a next page to the last item, so that we can page even further.
			items[-1]['nextFixed'] = Regex.replace(data = self.home_link, expression = '[?&](start=\d+)', replacement = 'start=%d' % 201, group = 1)

		return items

	def _homeImdb(self, items, level = None):
		# NB: Any limit above 200 will fail and only return 50 items.

		if level == 0:
			limit = 10
			votes = 1000
			sort = 'release_date,desc'
			release = 'date[60],date[1]'
		elif level == 1:
			limit = 20
			votes = 10000
			sort = 'moviemeter,asc'
			release = 'date[90],date[1]'
		else:
			limit = 200
			votes = 2000
			sort = 'moviemeter,asc'
			release = 'date[365],date[30]'

		link = self.home_link
		link = Regex.replace(data = link, expression = '[?&](count=\d+)', replacement = 'count=%d' % min(200, limit), group = 1)
		link = Regex.replace(data = link, expression = '[?&](sort=.*?)(?:$|&)', replacement = 'sort=%s' % sort, group = 1)
		link = Regex.replace(data = link, expression = '[?&](release_date=.*?)(?:$|&)', replacement = 'release_date=%s' % release, group = 1)
		link = Regex.replace(data = link, expression = '[?&](num_votes=\d+)', replacement = 'num_votes=%d' % votes, group = 1)

		for i in range(1, 50):
			result = self.imdbList(link = Regex.replace(data = link, expression = '[?&](start=\d+)', replacement = 'start=%d' % i, group = 1))
			if result:
				items[level].extend(result)
				if len(items[level]) >= limit: break
			else: break
			if limit <= 200: break

	def _homeTmdb(self, items, level = None):
		# NB: Each page has only 20 items and this limit cannot be changed.
		if not self.mMedia == Media.TypeShort:
			if self.mMedia == Media.TypeDocumentary: genre = MetaTmdb.GenreDocumentary
			else: genre = -MetaTmdb.GenreDocumentary
			type = [MetaTmdb.ReleaseDigital, MetaTmdb.ReleasePhysical]

			language = []
			if self.mLanguage: language.append(self.mLanguage)
			language.extend(Language.settingsCode())
			language = Tools.listUnique(language)

			if level == 0:
				limit = 10
				release = Time.past(days = 30)
				votes = 75 # Do not make too large, otherwise few titles are returned.
				sort = MetaTmdb.SortRelease
				order = MetaTmdb.OrderDescending
			elif level == 1:
				limit = 20
				release = Time.past(days = 60)
				votes = 500
				sort = MetaTmdb.SortPopularity
				order = MetaTmdb.OrderDescending
			else:
				limit = 100
				release = Time.past(days = 365)
				votes = 150
				sort = MetaTmdb.SortPopularity
				order = MetaTmdb.OrderDescending

			for i in range(1, 50):
				result = MetaTmdb.discoverMovie(genre = genre, type = type, release = release, votes = votes, language = language, sort = sort, order = order, page = i)
				if result:
					items[level].extend(result)
					if len(items[level]) >= limit: break
				if not result or len(result) < MetaTmdb.LimitFixed: break # Last page.

	##############################################################################
	# SEARCH
	##############################################################################

	# direct = True: when searching from TmdbHelper.
	def search(self, query = None, direct = False):
		try:
			from lib.modules.search import Search

			queryHas = query
			if not query: query = Dialog.input(title = 32010)
			if not query: return None

			Loader.show()
			if queryHas and not direct:
				if self.mMedia == Media.TypeDocumentary: Search().updateDocumentary(query)
				elif self.mMedia == Media.TypeShort: Search().updateShort(query)
				else: Search().updateMovie(query)
			else:
				if self.mMedia == Media.TypeDocumentary: Search().insertDocumentary(query, self.mKids)
				elif self.mMedia == Media.TypeShort: Search().insertShort(query, self.mKids)
				else: Search().insertMovie(query, self.mKids)

			# Use executeContainer() instead of directly calling retrieve().
			# This is important for shows. Otherwise if you open the season menu of a searched show and go back to the previous menu, the search dialog pops up again.
			link = self.search_link + Networker.linkQuote(query, plus = True)

			if direct: return self.retrieve(link = link)
			else: System.executeContainer(action = 'moviesRetrieve', parameters = {'link' : link, 'media' : self.mMedia, 'kids' : self.mKids})
		except:
			Logger.error()
			return None

	##############################################################################
	# GENRE
	##############################################################################

	def genres(self, menu = True):
		genres = []

		if not self.mKidsOnly or self.mRestriction >= 0:
			genres.extend([
				('Adventure', 'adventure'),
				('Animation', 'animation'),
				('Biography', 'biography'),
				('Comedy', 'comedy'),
				('Drama', 'drama'),
				('Family', 'family'),
				('Fantasy', 'fantasy'),
				('Music ', 'music'),
				('Musical', 'musical'),
				('Sport', 'sport'),
			])
		if not self.mKidsOnly or self.mRestriction >= 1:
			genres.extend([
				('Mystery', 'mystery'),
				('Romance', 'romance'),
				('History', 'history'),
				('Science Fiction', 'sci_fi'),
			])
		if not self.mKidsOnly or self.mRestriction >= 2:
			genres.extend([
				('Action', 'action'),
				('Crime', 'crime'),
				('Thriller', 'thriller'),
				('Western', 'western'),
			])
		if not self.mKidsOnly or self.mRestriction >= 3:
			genres.extend([
				('Horror', 'horror'),
				('War', 'war'),
				('Film Noir', 'film_noir'),
			])

		items = []
		genres = sorted(genres, key = lambda i : i[0])
		for i in genres: items.append({'name': Genre.translate(genre = i[0], language = self.mLanguage), 'link': self.genre_link % (i[1], self.mCertificates), 'image': 'genres.png', 'action': 'moviesRetrieve'})
		if menu: self.directory(items)
		return items

	##############################################################################
	# LANGUAGE
	##############################################################################

	def languages(self):
		items = []
		languages = Language.languages(universal = False)
		for i in languages: items.append({'name': i['name'][Language.NameEnglish], 'link': self.language_link % (i['code'][Language.CodePrimary], self.mCertificates), 'image': 'languages.png', 'action': 'moviesRetrieve'})
		self.directory(items)
		return items

	##############################################################################
	# CERTIFICATION
	##############################################################################

	def certifications(self):
		certificates = []
		if not self.mKidsOnly or self.mRestriction >= 0: certificates.append(('General Audience (G)', 'G'))
		if not self.mKidsOnly or self.mRestriction >= 1: certificates.append(('Parental Guidance (PG)', 'PG'))
		if not self.mKidsOnly or self.mRestriction >= 2: certificates.append(('Parental Caution (PG-13)', 'PG-13'))
		if not self.mKidsOnly or self.mRestriction >= 3: certificates.append(('Parental Restriction (R)', 'R'))
		if not self.mKidsOnly: certificates.append(('Mature Audience (NC-17)', 'NC-17'))

		items = []
		for i in certificates: items.append({'name': str(i[0]), 'link': self.certification_link % self.certificatesFormat(i[1]), 'image': 'certificates.png', 'action': 'moviesRetrieve'})
		self.directory(items)
		return items

	def certificatesFormat(self, certificates):
		base = 'US%3A'
		if not Tools.isArray(certificates): certificates = [certificates]
		return ','.join([base + i.upper() for i in certificates])

	def age(self):
		certificates = []
		if not self.mKidsOnly or self.mRestriction >= 0: certificates.append(('Minor (3+)', 'G'))
		if not self.mKidsOnly or self.mRestriction >= 1: certificates.append(('Young (10+)', 'PG'))
		if not self.mKidsOnly or self.mRestriction >= 2: certificates.append(('Teens (13+)', 'PG-13'))
		if not self.mKidsOnly or self.mRestriction >= 3: certificates.append(('Youth (16+)', 'R'))
		if not self.mKidsOnly: certificates.append(('Mature (18+)', 'NC-17'))

		items = []
		for i in certificates: items.append({'name': str(i[0]), 'link': self.certification_link % self.certificatesFormat(i[1]), 'image': 'age.png', 'action': 'moviesRetrieve'})
		self.directory(items)
		return items

	##############################################################################
	# YEAR
	##############################################################################

	def years(self, menu = True):
		items = []
		for i in range(self.mYear - 0, self.mYear - 100, -1): items.append({'name': str(i), 'link': self.year_link % (str(i), str(i), self.mCertificates), 'image': 'calendar.png', 'action': 'moviesRetrieve'})
		if menu: self.directory(items)
		return items

	def year(self, year, menu = True, refresh = False):
		return self.retrieve(self.year_link % (str(year), str(year), self.mCertificates), menu = menu, refresh = refresh)

	##############################################################################
	# AWARDS
	##############################################################################

	def awards(self, type = None, category = None, subcategory = None, generic = False, menu = True):
		icon = 'awards' if generic else type
		awards = {
			'academyawards' : {
				'global' : {'winner' : 'oscar_winner', 'nominee' : 'oscar_nominee'},
				'picture' : {'winner' : 'best_picture_winner', 'nominee' : 'oscar_best_picture_nominees'},
				'directing' : {'winner' : 'best_director_winner', 'nominee' : 'oscar_best_director_nominees'},
				'people' : {
					'global' : {'winner' : 'oscar_winner', 'nominee' : 'oscar_nominee'},
					'director' : {'winner' : 'best_director_winner', 'nominee' : 'oscar_best_director_nominees'},
					'actor' : {'winner' : 'oscar_best_actor_winners', 'nominee' : 'oscar_best_actor_nominees'},
					'actress' : {'winner' : 'oscar_best_actress_winners', 'nominee' : 'oscar_best_actress_nominees'},
					'actorsupporting' : {'winner' : 'oscar_best_supporting_actor_winners', 'nominee' : 'oscar_best_supporting_actor_nominees'},
					'actresssupporting' : {'winner' : 'oscar_best_supporting_actress_winners', 'nominee' : 'oscar_best_supporting_actress_nominees'},
				},
			},
			'goldenglobes' : {'winner' : 'golden_globe_winner', 'nominee' : 'golden_globe_nominee'},
			'razzieawards' : {'winner' : 'razzie_winner', 'nominee' : 'razzie_nominee'},
			'nationalfilm' : {'winner' : 'national_film_preservation_board_winner'},
		}

		if type is None:
			items = [
				{'name' : Translation.string(33324), 'image' : 'academyawards.png', 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards'}},
				{'name' : Translation.string(33325), 'image' : 'goldenglobes.png', 'action' : 'moviesAwards', 'parameters' : {'type' : 'goldenglobes'}},
				{'name' : Translation.string(33327), 'image' : 'razzieawards.png', 'action' : 'moviesAwards', 'parameters' : {'type' : 'razzieawards'}},
				{'name' : Translation.string(33446), 'image' : 'nationalfilm.png', 'action' : 'moviesRetrieve', 'link' : self.award_link % awards['nationalfilm']['winner']},
			]
		elif type == 'academyawards' and category is None:
			items = [
				{'name' : Translation.string(33700), 'image' : 'academyawardsall.png', 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'global'}},
				{'name' : Translation.string(33698), 'image' : 'academyawardspicture.png', 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'picture'}},
				{'name' : Translation.string(33699), 'image' : 'academyawardsdirector.png', 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'directing'}},
				{'name' : Translation.string(35565), 'image' : 'academyawardspeople.png', 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'people'}},
			]
		elif type == 'academyawards' and category == 'people' and subcategory is None:
			items = [
				{'name' : Translation.string(33700), 'image' : '%speople.png' % icon, 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'people', 'subcategory' : 'global', 'generic' : generic}},
				{'name' : Translation.string(35560), 'image' : '%sdirector.png' % icon, 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'people', 'subcategory' : 'director', 'generic' : generic}},
				{'name' : Translation.string(35561), 'image' : '%smale.png' % icon, 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'people', 'subcategory' : 'actor', 'generic' : generic}},
				{'name' : Translation.string(35562), 'image' : '%sfemale.png' % icon, 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'people', 'subcategory' : 'actress', 'generic' : generic}},
				{'name' : Translation.string(35563), 'image' : '%smale.png' % icon, 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'people', 'subcategory' : 'actorsupporting', 'generic' : generic}},
				{'name' : Translation.string(35564), 'image' : '%sfemale.png' % icon, 'action' : 'moviesAwards', 'parameters' : {'type' : 'academyawards', 'category' : 'people', 'subcategory' : 'actresssupporting', 'generic' : generic}},
			]
		elif type:
			awards = awards[type]
			if category: awards = awards[category]
			if subcategory: awards = awards[subcategory]
			if category == 'people':
				link = self.personlist_link + '&groups=%s'
				items = [
					{'name' : Translation.string(33029), 'image' : '%sall.png' % icon, 'action' : 'moviesPersons', 'link' : link % ','.join([awards['winner'], awards['nominee']])},
					{'name' : Translation.string(33885), 'image' : '%swinner.png' % icon, 'action' : 'moviesPersons', 'link' : link % awards['winner']},
					{'name' : Translation.string(33886), 'image' : '%snominee.png' % icon, 'action' : 'moviesPersons', 'link' : link % awards['nominee']},
				]
			else:
				items = [
					{'name' : Translation.string(33029), 'image' : '%sall.png' % icon, 'action' : 'moviesRetrieve', 'link' : self.award_link % ','.join([awards['winner'], awards['nominee']])},
					{'name' : Translation.string(33885), 'image' : '%swinner.png' % icon, 'action' : 'moviesRetrieve', 'link' : self.award_link % awards['winner']},
					{'name' : Translation.string(33886), 'image' : '%snominee.png' % icon, 'action' : 'moviesRetrieve', 'link' : self.award_link % awards['nominee']},
				]

		if menu: self.directory(items)
		return items

	##############################################################################
	# RATED
	##############################################################################

	def rated(self, type = None, menu = True):
		if type is None:
			items = [
				{'name' : Translation.string(32034), 'image' : 'imdb.png', 'action' : 'moviesRated', 'parameters' : {'type' : 'imdb'}},
				{'name' : Translation.string(33508), 'image' : 'tmdb.png', 'action' : 'moviesRated', 'parameters' : {'type' : 'tmdb'}},
				{'name' : Translation.string(32315), 'image' : 'trakt.png', 'action' : 'moviesRated', 'parameters' : {'type' : 'trakt'}},
			]
		elif type:
			items = [
				{'name' : Translation.string(33733), 'image' : '%sbest.png' % type, 'action' : 'moviesRetrieve', 'link' : 'rated%sbest' % type},
				{'name' : Translation.string(33734), 'image' : '%sworst.png' % type, 'action' : 'moviesRetrieve', 'link' : 'rated%sworst' % type},
			]
		if menu: self.directory(items)
		return items

	##############################################################################
	# NETWORKS
	##############################################################################

	def networks(self, menu = True):
		items = [
			{'name' : Translation.string(35429), 'image' : 'stream.png', 'action' : 'moviesStreamers', 'parameters' : {'media' : self.mMedia, 'kids' : self.mKids}},
		]
		if self.mMedia == Media.TypeMovie: items.append({'name' : Translation.string(35430), 'image' : 'aired.png', 'action' : 'moviesBroadcasters', 'parameters' : {'media' : self.mMedia, 'kids' : self.mKids}})
		if menu: self.directory(items)
		return items

	def networksStreamers(self, service = None, country = None, menu = True):
		items = [
			{'name' : Translation.string(36000), 'image' : 'netflix.png', 'action' : 'moviesRetrieve', 'link' : 'networknetflix'},
			{'name' : Translation.string(36001), 'image' : 'amazon.png', 'action' : 'moviesRetrieve', 'link' : 'networkamazon'},
			{'name' : Translation.string(36002), 'image' : 'appletv.png', 'action' : 'moviesRetrieve', 'link' : 'networkappletv'},
			{'name' : Translation.string(36003), 'image' : 'hbo.png', 'action' : 'moviesRetrieve', 'link' : 'networkhbo'},
			{'name' : Translation.string(36004), 'image' : 'disney.png', 'action' : 'moviesRetrieve', 'link' : 'networkdisney'},
			{'name' : Translation.string(36005), 'image' : 'paramount.png', 'action' : 'moviesRetrieve', 'link' : 'networkparamount'},
			{'name' : Translation.string(36006), 'image' : 'peacock.png', 'action' : 'moviesRetrieve', 'link' : 'networkpeacock'},
			{'name' : Translation.string(36007), 'image' : 'hulu.png', 'action' : 'moviesRetrieve', 'link' : 'networkhulu'},
			{'name' : Translation.string(36008), 'image' : 'showtime.png', 'action' : 'moviesRetrieve', 'link' : 'networkshowtime'},
			{'name' : Translation.string(36009), 'image' : 'britbox.png', 'action' : 'moviesRetrieve', 'link' : 'networkbritbox'},
			{'name' : Translation.string(36010), 'image' : 'now.png', 'action' : 'moviesRetrieve', 'link' : 'networknow'},
			{'name' : Translation.string(36011), 'image' : 'bet.png', 'action' : 'moviesRetrieve', 'link' : 'networkbet'},
			{'name' : Translation.string(36012), 'image' : 'crunchyroll.png', 'action' : 'moviesRetrieve', 'link' : 'networkcrunchyroll'},
			{'name' : Translation.string(36013), 'image' : 'channel4.png', 'action' : 'moviesRetrieve', 'link' : 'networkall4'},
			#{'name' : Translation.string(36014), 'image' : 'discovery.png', 'action' : 'moviesRetrieve', 'link' : 'networkdiscovery'}, # No movie list.
			#{'name' : Translation.string(36015), 'image' : 'hayu.png', 'action' : 'moviesRetrieve', 'link' : 'networkhayu'}, # No movie list.
			{'name' : Translation.string(35296), 'image' : 'youtube.png', 'action' : 'moviesRetrieve', 'link' : 'networkyoutube'},
		]
		items = Tools.listSort(data = items, key = lambda i : i['name'])
		if menu: self.directory(items)
		return items

	def networksBroadcasters(self):
		from lib.indexers.navigator import Navigator
		Navigator(media = self.mMedia, kids = self.mKids).channels()

	##############################################################################
	# PEOPLE
	##############################################################################

	def persons(self, link = None, menu = True):
		if link:
			try: link = getattr(self, link + '_link')
			except: pass
			items = self.mCache.cacheShort(self.imdbListPerson, link)
		else:
			items = self.mCache.cacheMedium(self.imdbListPerson, self.personlist_link)

		if items:
			for i in range(0, len(items)): items[i].update({'action': 'moviesRetrieve', 'media' : self.mMedia})
			if menu: self.directory(items)
		else:
			Loader.hide()
			Dialog.notification(title = 32010, message = 33049, icon = Dialog.IconInformation)

		return items

	def person(self, query = None):
		try:
			from lib.modules.search import Search

			if query:
				if not query: return None
				Search().updatePerson(query)
			else:
				query = Dialog.keyboard(title = 32010)
				if not query: return None
				Search().insertPerson(query, self.mKids)

			# Use executeContainer() instead of directly calling get().
			# This is important for shows. Otherwise if you open the season menu of a searched show and go back to the previous menu, the search dialog pops up again.
			link = self.persons_link % Networker.linkQuote(query, plus = True)
			System.executeContainer(action = 'moviesPersons', parameters = {'link' : link, 'media' : self.mMedia, 'kids' : self.mKids})
			#self.persons(link)
		except: Logger.error()

	def famous(self, menu = True):
		items = [
			{'name' : Translation.string(35339), 'image' : 'famousfilmmaker.png', 'action' : 'moviesPersons', 'link' : 'famousfilmmaker'},
			{'name' : Translation.string(35340), 'image' : 'famousdirector.png', 'action' : 'moviesPersons', 'link' : 'famousdirector'},
			{'name' : Translation.string(35457), 'image' : 'famouscinematographer.png', 'action' : 'moviesPersons', 'link' : 'famouscinematographer'},
			{'name' : Translation.string(35341), 'image' : 'famouswriter.png', 'action' : 'moviesPersons', 'link' : 'famouswriter'},
			{'name' : Translation.string(35458), 'image' : 'famousproducer.png', 'action' : 'moviesPersons', 'link' : 'famousproducer'},
			{'name' : Translation.string(35459), 'image' : 'famouseditor.png', 'action' : 'moviesPersons', 'link' : 'famouseditor'},
			{'name' : Translation.string(35512), 'image' : 'famouscomposer.png', 'action' : 'moviesPersons', 'link' : 'famouscomposer'},
			{'name' : Translation.string(35342), 'image' : 'famousactor.png', 'action' : 'moviesPersons', 'link' : 'famousactor'},
			{'name' : Translation.string(35343), 'image' : 'famousactress.png', 'action' : 'moviesPersons', 'link' : 'famousactress'},
		]
		if menu: self.directory(items)
		return items

	def genders(self, menu = True):
		expression = 'gender=(.*?)(?:$|&)'
		items = [
			{'name' : Translation.string(35270), 'image' : 'gendermale.png', 'action' : 'moviesPersons', 'link' : Regex.replace(data = self.personlist_link, expression = expression, replacement = 'male', group  = 1)},
			{'name' : Translation.string(35271), 'image' : 'genderfemale.png', 'action' : 'moviesPersons', 'link' : Regex.replace(data = self.personlist_link, expression = expression, replacement = 'female', group  = 1)},
			{'name' : Translation.string(35272), 'image' : 'gendernonbinary.png', 'action' : 'moviesPersons', 'link' : Regex.replace(data = self.personlist_link, expression = expression, replacement = 'non-binary', group  = 1)},
			{'name' : Translation.string(35149), 'image' : 'genderother.png', 'action' : 'moviesPersons', 'link' : Regex.replace(data = self.personlist_link, expression = expression, replacement = 'other', group  = 1)},
		]
		if menu: self.directory(items)
		return items

	##############################################################################
	# LIST
	##############################################################################

	def listUser(self, mode = None, watchlist = False):
		items = []
		userlists = []

		if not mode is None: mode = mode.lower().strip()
		enabledTrakt = (mode is None or mode == 'trakt') and self.mAccountTrakt
		enabledImdb = (mode is None or mode == 'imdb') and self.mAccountImdb

		if enabledImdb:
			try:
				lists = self.mCache.cacheRefreshShort(self.imdbListUser, self.imdblists_link)
				for i in range(len(lists)): lists[i]['image'] = 'imdblists.png'
				userlists += lists
			except: pass

		if enabledTrakt:
			try:
				lists = self.mCache.cacheRefreshShort(self.traktListUser, self.traktlists_link, self.mAccountTrakt)
				for i in range(len(lists)): lists[i]['image'] = 'traktlists.png'
				userlists += lists
			except: pass
			try:
				lists = self.mCache.cacheRefreshShort(self.traktListUser, self.traktlikedlists_link, self.mAccountTrakt)
				for i in range(len(lists)): lists[i]['image'] = 'traktlists.png'
				userlists += lists
			except: pass

		# Filter the user's own lists that were
		for i in range(len(userlists)):
			contains = False
			adapted = userlists[i]['link'].replace('/me/', '/%s/' % self.mAccountTrakt)
			for j in range(len(items)):
				if adapted == items[j]['link'].replace('/me/', '/%s/' % self.mAccountTrakt):
					contains = True
					break
			if not contains:
				items.append(userlists[i])

		for i in range(len(items)): items[i]['action'] = 'moviesRetrieve'

		# Watchlist
		if watchlist:
			if enabledImdb: items.insert(0, {'name' : Translation.string(32033), 'link' : self.imdbwatchlist_link, 'image' : 'imdbwatch.png', 'action' : 'moviesRetrieve'})
			if enabledTrakt: items.insert(0, {'name' : Translation.string(32033), 'link' : self.traktwatchlist_link, 'image' : 'traktwatch.png', 'action' : 'moviesRetrieve'})

		self.directory(items)
		return items

	##############################################################################
	# TRAKT
	##############################################################################

	def traktList(self, link, user = None, next = True):
		list = []
		items = []
		dulicates = []

		if self.traktunfinished_link in link:
			unstarted = Playback.percentStart(media = self.mMedia)
			unfinished = Playback.percentEnd(media = self.mMedia)
		else:
			unstarted = None
			unfinished = None

		try:
			parameters = Networker.linkParameters(link = link)
			parameters['extended'] = 'full'
			linkNew = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')
			items = trakt.getTraktAsJson(linkNew)
		except:
			Logger.error()
			return list

		if next:
			next = None
			try:
				parameters = Networker.linkParameters(link = link)
				if 'limit' in parameters and int(parameters['limit']) == len(items):
					parameters['page'] = (int(parameters['page']) + 1) if 'page' in parameters else 2
					next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters).replace('%2C', ',')
			except: Logger.error()
		else:
			next = None

		for item in items:
			try:
				try: progress = max(0, min(1, item['progress'] / 100.0))
				except: progress = None

				# Do not list movies that have a higher progress than the progress considered the end of the video.
				if progress and ((unstarted and progress < unstarted) or (unfinished and progress > unfinished)): continue

				try: item = item['movie']
				except: pass

				title = item['title']
				title = Networker.htmlDecode(title)
				title = Regex.remove(data = title, expression = '\s+[\|\[\(](us|uk|gb|au|\d{4})[\|\]\)]\s*$', all = True)

				try:
					year = item['year']
					if year > self.mYear: continue
				except: year = None

				idImdb = None
				try:
					idImdb = item['ids']['imdb']
					if idImdb:
						idImdb = 'tt' + Regex.remove(data = str(idImdb), expression = '[^0-9]', all = True)
						if idImdb == 'tt': idImdb = None
				except: pass

				idTmdb = item.get('ids', {}).get('tmdb', None)
				if idTmdb: idTmdb = str(idTmdb)
				idTvdb = item.get('ids', {}).get('tvdb', None)
				if idTvdb: idTvdb = str(idTvdb)
				idTrakt = item.get('ids', {}).get('trakt', None)
				if idTrakt: idTrakt = str(idTrakt)

				if not idImdb and not idTmdb: continue
				if idImdb in dulicates or idTmdb in dulicates: continue
				if idImdb: dulicates.append(idImdb)
				if idTmdb: dulicates.append(idTmdb)

				try: plot = Networker.htmlDecode(item['overview'])
				except: plot = None

				try: premiered = Regex.extract(data = item['released'], expression = '(\d{4}-\d{2}-\d{2})', group = 1)
				except: premiered = None

				try: added = Time.timestamp(fixedTime = item['last_updated_at'], iso = True)
				except:
					try: added = Time.timestamp(item['movie']['last_updated_at'], iso = True)
					except: added = None

				try: watched = Time.timestamp(item['last_watched_at'], iso = True)
				except:
					try: watched = Time.timestamp(item['movie']['last_watched_at'], iso = True)
					except: watched = None

				# This seems to be always null.
				try: rewatched = Time.timestamp(item['reset_at'], iso = True)
				except:
					try: rewatched = Time.timestamp(item['movie']['reset_at'], iso = True)
					except: rewatched = None

				try: genre = [i.title() for i in item['genres']]
				except: genre = None

				try: duration = int(item['runtime']) * 60
				except: duration = None

				try: rating = item['rating']
				except: rating = None

				try: votes = item['votes']
				except: votes = None

				try: mpaa = item['certification']
				except: mpaa = None

				item = {
					'imdb' : idImdb,
					'tmdb' : idTmdb,
					'tvdb' : idTvdb,
					'trakt' : idTrakt,

					'title' : title,
					'originaltitle' : title,
					'plot' : plot,
					'year' : year,
					'premiered' : premiered,

					'genre' : genre,
					'duration' : duration,
					'mpaa' : mpaa,

					'timeAdded' : added,
					'timeWatched' : watched,
					'timeRewatched' : rewatched,

					'next' : next,
					'progress' : progress,

					'temp' : {
						'trakt' : {
							'rating' : rating,
							'votes' : votes,
						},
					}
				}
				list.append(item)
			except: Logger.error()

		return list

	def traktListUser(self, link, user):
		list = []

		try: items = trakt.getTraktAsJson(link)
		except: items = None
		if not items: return list

		for item in items:
			try:
				try: name = item['list']['name']
				except: name = item['name']
				name = Networker.htmlDecode(name)

				try: link = (trakt.slug(item['list']['user']['username']), item['list']['ids']['slug'])
				except: link = ('me', item['ids']['slug'])
				link = self.traktlist_link % link

				list.append({'name': name, 'link': link})
			except: Logger.error()

		list = sorted(list, key = lambda k : Regex.remove(data = k['name'], expression = '(^the\s|^an?\s)', group = 1))
		return list

	##############################################################################
	# IMDB
	##############################################################################

	def imdbRequest(self, link):
		return MetaImdb.retrieve(link = link, full = True) # Adds additional headers.

	def imdbPrivacy(self, full, link, rating):
		self.mImdbPublic = False
		if not full:
			self.mCache.cacheDelete(self.imdbListId, link)
			Dialog.confirm(title = 32034, message = 35609 if rating else 35608)
		return Cache.Skip

	def imdbPublic(self):
		return self.mImdbPublic

	def imdbListId(self, link):
		try:
			networker = self.imdbRequest(link = link)
			result = networker.responseDataText()
			try: result = result.decode('iso-8859-1')
			except: pass
			return Raw.parse(data = result, tag = 'meta', extract = 'content', attributes = {'property': 'pageId'})[0]
		except: return None

	def imdbList(self, link, full = False):
		if not link: return None # Some lists for documentaries/shorts might be missing.

		list = []
		items = []
		isRating = '/ratings' in link
		isOwn = '/user/' in link

		documentary = self.mMedia == Media.TypeDocumentary
		short = self.mMedia == Media.TypeShort

		matches = Regex.extract(data = link, expression = 'date\[(\d+)\]', group = None, all = True)
		for i in matches: link = link.replace('date[%s]' % i, Time.past(days = int(i), format = Time.FormatDate))
		linkOriginal = link

		self.mImdbPublic = True
		while True:
			try:
				next = None
				id = None

				if link == self.imdbcollection_link:
					id = self.mCache.cacheExtended(self.imdbListId, link)
					if id: link = self.imdblistname_link % id
				elif link == self.imdbwatchlist_link:
					id = self.mCache.cacheExtended(self.imdbListId, link)
					if id: link = self.imdblistdate_link % id

				if isOwn and not isRating and (not id or id.startswith('ur')):
					if not items: return self.imdbPrivacy(full = full, link = linkOriginal, rating = isRating)
					else: break

				networker = self.imdbRequest(link = link)
				if isOwn and networker.responseErrorCode() == 403:
					if not items: return self.imdbPrivacy(full = full, link = linkOriginal, rating = isRating)
					else: break

				result = networker.responseDataText().replace('\n', '')
				try: result = result.decode('iso-8859-1')
				except: pass

				items += Raw.parse(data = result, tag = 'div', attributes = {'class': '.+? lister-item'}) + Raw.parse(data = result, tag = 'div', attributes = {'class': 'lister-item .+?'})
				items += Raw.parse(data = result, tag = 'div', attributes = {'class': 'list_item.+?'})
			except:
				Logger.error()
				return None

			try:
				# HTML syntax error, " directly followed by attribute name. Insert space in between. Raw.parse can otherwise not handle it.
				result = result.replace('"class="lister-page-next', '" class="lister-page-next')
				next = Raw.parse(data = result, tag = 'a', extract = 'href', attributes = {'class': '.*?lister-page-next.*?'})

				if not next:
					next = Raw.parse(data = result, tag = 'div', attributes = {'class': 'pagination'})[0]
					next = zip(Raw.parse(data = next, tag = 'a', extract = 'href'), Raw.parse(data = next, tag = 'a'))
					next = [i[0] for i in next if 'Next' in i[1]]

				parameters = Networker.linkParameters(link = next[0])
				next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters)
				next = Networker.htmlDecode(next)
			except:
				next = None

			if not full or not next: break
			link = next

		for item in items:
			try:
				# Some lists contain TV shows.
				if 'Episode:' in item: continue

				try:
					# Years that contain extra parts, like "Video Game" or "2019-" or "2011-2018".
					year = Raw.parse(data = item, tag = 'span', attributes = {'class' : '.*lister-item-year.*'})[0]
					if Regex.match(data = year, expression = 'game'): continue # (2018 Video Game)
					if not Regex.match(data = year, expression = '\(\d{4}[a-z\d\s]*\)'): continue # Allow (2014 TV Movie), but disallow (2016 - 2018)
					year = int(Regex.extract(data = year, expression = '(\d{4})', group = 1))
					if year > self.mYear: continue
				except: pass

				imdb = Raw.parse(data = item, tag = 'a', extract = 'href')[0]
				imdb = Regex.extract(data = imdb, expression = '(tt\d+)', group = 1)

				title = Raw.parse(data = item, tag = 'a')[1]
				title = Networker.htmlDecode(title)

				# Raw.parse cannot handle elements without a closing tag.
				#try: poster = Raw.parse(data = item, tag = 'img', extract = 'loadlate')[0]
				#except: poster = None
				try:
					html = Parser(item)
					poster = html.find_all('img')[0]['loadlate']
					if poster:
						if '/nopicture/' in poster: poster = None
						if poster: poster = MetaImdb.image(Networker.htmlDecode(poster))
					else: poster = None
				except: poster = None

				genreIds = []
				try:
					genre = Raw.parse(data = item, tag = 'span', attributes = {'class' : 'genre'})[0]
					genre = [i.strip() for i in genre.split(',')]
					genre = [Networker.htmlDecode(i) for i in genre if i]
					genreIds = [i.lower() for i in genre]
				except: genre = None

				if isRating: # Rating list cannot be filtered according to type using GET parameters.
					if documentary and not 'documentary' in genreIds: continue
					if short and not 'short' in genreIds: continue

				# Some featured lists return documentaries as well (eg home releases).
				# Only exclude if it is ONLY documentary. Allow multiple genres (eg: Jackass Forever 2022 - Documentary, Action, Comedy).
				if not documentary and genreIds and len(genreIds) == 1 and 'documentary' in genreIds: continue

				try:
					mpaa = Raw.parse(data = item, tag = 'span', attributes = {'class' : 'certificate'})[0]
					if not mpaa or mpaa == 'NOT_RATED': mpaa = None
					else: mpaa = Networker.htmlDecode(mpaa.replace('_', '-'))
				except: mpaa = None
				# Do not use this, since TV movies (especially docus and shorts) also have a TV rating.
				#if 'tv' in mpaa.lower(): continue # Some lists contain TV shows.

				try:
					duration = Regex.extract(data = item, expression = '((\d+\shr\s)?\d+\smin)', group = 1)
					duration = ConverterDuration(value = duration).value(ConverterDuration.UnitSecond)
				except: duration = None

				# Some shows are indistinguishable from movies, since they do not contain any info on being a show.
				# Ignore items that have a runtime of more than 5 hours.
				if isRating and duration and duration > 18000: continue

				rating = None
				try: rating = float(Raw.parse(data = item, tag = 'span', attributes = {'class' : 'rating-rating'})[0])
				except:
					try: rating = float(Raw.parse(data = rating, tag = 'span', attributes = {'class' : 'value'})[0])
					except:
						try: rating = float(Raw.parse(data = item, tag = 'div', extract = 'data-value', attributes = {'class' : '.*?imdb-rating'})[0])
						except: pass
				if not rating:
					try:
						rating = Raw.parse(data = item, tag = 'span', attributes = {'class' : 'ipl-rating-star__rating'})[0]
						if not rating or rating == '' or rating == '-': rating = None
						else: rating = float(rating)
					except: rating = None

				ratinguser = None
				if isOwn: # Do not do this for other lists, since the alternative rating might be from a different user (creator of the list) and will incorrectly overwrite the current user's rating.
					try:
						ratinguser = Raw.parse(data = Raw.parse(data = item, tag = 'div', attributes = {'class' : '.*?ipl-rating-star--other-user.*?'})[0], tag = 'span', attributes = {'class' : 'ipl-rating-star__rating'})[0]
						if not ratinguser or ratinguser == '' or ratinguser == '-': ratinguser = None
						else: ratinguser = float(ratinguser)
					except: ratinguser = None

				ratingtime = None
				try: ratingtime = ConverterTime(Regex.extract(data = item, expression = 'rated\son\s(.*?)<', group = 1), format = ConverterTime.FormatDateShort).timestamp()
				except: pass

				ratingmetacritic = None
				try:
					ratingmetacritic = Raw.parse(data = item, tag = 'span', attributes = {'class' : '.*?[^-]metascore.*?'})[0]
					if not ratingmetacritic or ratingmetacritic == '' or ratingmetacritic == '-': ratingmetacritic = None
					else: ratingmetacritic = float(ratingmetacritic) / 10.0 # Out of 100 and not out of 10.
				except: ratingmetacritic = None

				votes = None
				try: votes = int(Raw.parse(data = item, tag = 'span', attributes = {'name' : 'nv'})[0].replace(',', ''))
				except:
					try: votes = int(Raw.parse(data = item, tag = 'div', extract = 'title', attributes = {'class' : '.*?rating-list'})[0].replace(',', ''))
					except:
						try: votes = int(Regex.extract(data = Raw.parse(data = item, tag = 'div', extract = 'title', attributes = {'class' : '.*?rating-list'})[0], expression = '\((.+?)\svotes?\)', group = 1).replace(',', ''))
						except: pass

				try:
					director = Regex.extract(data = item, expression = 'directors?:(.+?)(?:\||<\/div>)', group = 1)
					director = Raw.parse(data = director, tag = 'a')
					director = [Networker.htmlDecode(i) for i in director]
				except: director = None

				try:
					cast = Regex.extract(data = item, expression = 'stars?:(.+?)(?:\||<\/div>)', group = 1)
					cast = Raw.parse(data = cast, tag = 'a')
					cast = [Networker.htmlDecode(i) for i in cast]
				except: cast = None

				plot = None
				try: plot = Raw.parse(data = item, tag = 'p', attributes = {'class' : 'text-muted'})[0]
				except:
					try: plot = Raw.parse(data = item, tag = 'div', attributes = {'class' : 'item_description'})[0]
					except: pass
				if plot:
					plot = plot.rsplit('<span>', 1)[0].strip()
					plot = Regex.remove(data = plot, expression = '(<.+?>|<\/.+?>)', group = 1)
					if not plot:
						try:
							plot = Raw.parse(data = item, tag = 'div', attributes = {'class' : 'lister-item-content'})[0]
							plot = Regex.replace(data = plot, expression = '(<p\s*class="">)', replacement = '<p class="plot_">', group = 1)
							plot = Raw.parse(data = plot, tag = 'p', attributes = {'class' : 'plot_'})[0]
							plot = Regex.remove(data = plot, expression = '(<.+?>|<\/.+?>)', group = 1)
						except: pass
				if plot: plot = Networker.htmlDecode(plot)
				else: plot = None

				item = {
					'imdb' : imdb,
					'title' : title,
					'originaltitle' : title,
					'plot' : plot,
					'year' : year,
					'duration' : duration,
					'mpaa' : mpaa,
					'genre' : genre,
					'director' : director,
					'cast' : cast,
					'temp' : {
						'imdb' : {
							'rating' : rating,
							'ratinguser' : ratinguser,
							'ratingtime' : ratingtime,
							'votes' : votes,
							'poster' : poster,
						},
						'metacritic' : {
							'rating' : ratingmetacritic,
						},
					}
				}

				# Only add next if it actually has a value.
				# The disc releases list does not have a next page.
				# This causes the "Next Page" not to show in the Arrivals menu if the last item is from the disc releases list.
				if next: item['next'] = next

				list.append(item)
			except: Logger.error()

		return list

	def imdbListPerson(self, link):
		list = []

		try:
			networker = self.imdbRequest(link = link)
			result = networker.responseDataText()
			try: result = result.decode('iso-8859-1')
			except: pass
			items = Raw.parse(data = result, tag = 'div', attributes = {'class' : '.+? lister-item'}) + Raw.parse(data = result, tag = 'div', attributes = {'class' : 'lister-item .+?'})
		except: Logger.error()

		try:
			# HTML syntax error, " directly followed by attribute name. Insert space in between. Raw.parse can otherwise not handle it.
			result = result.replace('"class="lister-page-next', '" class="lister-page-next')
			next = Raw.parse(data = result, tag = 'a', extract = 'href', attributes = {'class': '.*?lister-page-next.*?'})

			if not next:
				next = Raw.parse(data = result, tag = 'div', attributes = {'class': 'pagination'})[0]
				next = zip(Raw.parse(data = next, tag = 'a', extract = 'href'), Raw.parse(data = next, tag = 'a'))
				next = [i[0] for i in next if 'Next' in i[1]]

			parameters = Networker.linkParameters(link = next[0])
			next = Networker.linkCreate(link = Networker.linkClean(link, parametersStrip = True, headersStrip = True), parameters = parameters)
			next = Networker.htmlDecode(next)
		except:
			next = None

		for item in items:
			try:
				name = Raw.parse(data = item, tag = 'a')[1]
				name = Networker.htmlDecode(name)

				try:
					# Do not use [-1]  for lists like: https://imdb.com/list/ls000005319/
					bio = Raw.parse(data = item, tag = 'p')[1]
					description = Parser(bio).text
				except:
					description = None

				link = Raw.parse(data = item, tag = 'a', extract = 'href')[1]
				link = Regex.extract(data = link, expression = '(nm\d+)', group = 1)
				link = self.person_link % (link, self.mCertificates)
				link = Networker.htmlDecode(link)

				image = Raw.parse(data = item, tag = 'img', extract = 'src')[0]
				image = MetaImdb.image(Networker.htmlDecode(image), crop = True) # Crop to keep the aspect ratio.

				item = {'name' : name, 'description' : description, 'link' : link, 'image' : image, 'person' : True}
				if next: item['next'] = next
				list.append(item)
			except: Logger.error()

		return list

	def imdbListUser(self, link):
		list = []

		try:
			networker = self.imdbRequest(link = link)
			result = networker.responseDataText()
			try: result = result.decode('iso-8859-1')
			except: pass
			items = []
			items += Raw.parse(data = result, tag = 'div', attributes = {'class' : '(?:.+\s)?list_name(?:\s.+)?'})
			items += Raw.parse(data = result, tag = 'li', attributes = {'class' : '(?:.+\s)?user-list(?:\s.+)?'})
		except: Logger.error()

		for item in items:
			try:
				name = Raw.parse(data = item, tag = 'a')[0]
				name = Networker.htmlDecode(name)

				link = Raw.parse(data = item, tag = 'a', extract = 'href')[0]
				link = link.split('/list/', 1)[-1].replace('/', '')
				link = self.imdblistname_link % link
				link = Networker.htmlDecode(link)

				list.append({'name': name, 'link': link})
			except: Logger.error()

		list = sorted(list, key = lambda k : Regex.remove(data = k['name'], expression = '(^the\s|^an?\s)', group = 1))
		return list

	def imdbUserAccount(self, watched = None, ratings = None):
		data = [[], []]

		threads = []
		if watched is None: threads.append(Pool.thread(target = self.imdbUserWatched, args = (data, 0)))
		else: data[0] = watched
		if ratings is None: threads.append(Pool.thread(target = self.imdbUserRatings, args = (data, 1)))
		else: data[1] = ratings
		[i.start() for i in threads]
		[i.join() for i in threads]

		result = data[0]
		for i in data[1]:
			found = -1
			for j in range(len(result)):
				try:
					if i['imdb'] == result[j]['imdb']:
						found = j
						break
				except: pass
				try:
					if i['tmdb'] == result[j]['tmdb']:
						found = j
						break
				except: pass
			if found >= 0: result[found].update(i)
			else: result.append(i)

		return result

	def imdbUserWatched(self, resultData = None, resultIndex = None):
		data = self.retrieve(link = 'imdbwatchlist', menu = False, detailed = False, full = True, clean = False)
		values = []
		for item in data:
			value = {}
			if 'temp' in item and item['temp'] and 'imdb' in item['temp'] and item['temp']['imdb']:
				if 'watchedtime' in item['temp']['imdb'] and item['temp']['imdb']['watchedtime']: value['time'] = item['temp']['imdb']['watchedtime']
			if 'imdb' in item and item['imdb']: value['imdb'] = item['imdb']
			if 'tmdb' in item and item['tmdb']: value['tmdb'] = item['tmdb']
			if 'imdb' in value or 'tmdb' in value: values.append(value)
		if not resultData is None: resultData[resultIndex] = values
		return values

	def imdbUserRatings(self, resultData = None, resultIndex = None):
		data = self.retrieve(link = 'imdbratings', menu = False, detailed = False, full = True, clean = False)
		values = []
		for item in data:
			if 'temp' in item and item['temp'] and 'imdb' in item['temp'] and item['temp']['imdb']:
				if 'ratinguser' in item['temp']['imdb'] and item['temp']['imdb']['ratinguser']:
					value = {'rating' : item['temp']['imdb']['ratinguser']}
					if 'ratingtime' in item['temp']['imdb'] and item['temp']['imdb']['ratingtime']: value['time'] = item['temp']['imdb']['ratingtime']
					if 'imdb' in item and item['imdb']: value['imdb'] = item['imdb']
					if 'tmdb' in item and item['tmdb']: value['tmdb'] = item['tmdb']
					if 'imdb' in value or 'tmdb' in value: values.append(value)
		if not resultData is None: resultData[resultIndex] = values
		return values

	##############################################################################
	# METADATA
	##############################################################################

	# Either pass in a list of items to retrieve the detailed metadata for all of them.
	# Or pass in an ID or title/year to get the details of a single item.
	# filter: remove uncommon movies, like those without an IMDb ID. If None, will set to True for multiple items, and to False for a single item.
	# By default, do not cache internal requests (eg: Trakt/TMDb/IMDb/Fanart API requests).
	# For a list of 50 items, this will use an additional 5MB of the cache (disc space), plus it takes 100-200 ms longer to write to disc (although this is insignificant, since the entire list takes 20-25 secs).
	# There is no real reason to cache intermediary reque7sts, since the final processed metadata is already cached with MetaCache.
	# The only reason for intermediary caching is if the metadata is imcomplete, and on subsequent menu loading, all of the movie's metadata is requested again, even though some of them might have suceeded previously.
	# quick = Quickly retrieve items from cache without holding up the process of retrieving detailed metadata in the foreground. This is useful if only a few random items are needed from the list and not all of them.
	# quick = positive integer (retrieve the given number of items in the foreground and the rest in the background), negative integer (retrieve the given number of items in the foreground and do not retrieve the rest at all), True (retrieve whatever is in the cache and the rest in the background - could return no items at all), False (retrieve whatever is in the cache and the rest not at all - could return no items at all).
	# threaded = If sub-function calls should use threads or not. None: threaded for single item, non-threaded for multiple items. True: threaded. False: non-threaded.
	def metadata(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, items = None, filter = None, clean = True, quick = None, refresh = False, cache = False, threaded = None):
		try:
			single = False
			if items or (idImdb or idTmdb or idTvdb or idTrakt) or title:
				if items:
					if not Tools.isArray(items):
						single = True
						items = [items]
				else:
					single = True
					items = [{'imdb' : idImdb, 'tmdb' : idTmdb, 'tvdb' : idTvdb, 'trakt' : idTrakt, 'title' : title, 'year' : year}]
				if filter is None: filter = not single

				lock = Lock()
				locks = {}
				semaphore = Semaphore(self.mMetatools.concurrency(media = self.mMedia))
				metacache = MetaCache.instance()
				items = metacache.select(type = MetaCache.TypeMovie, items = items)

				if threaded is None: threaded = len(items) == 1
				threadsSingle = len(items) == 1

				metadataForeground = []
				metadataBackground = []
				threadsForeground = []
				threadsBackground = []

				if quick is None:
					for item in items:
						try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
						except: refreshing = MetaCache.RefreshForeground
						if refreshing == MetaCache.RefreshForeground or refresh:
							self.mMetatools.busyStart(media = self.mMedia, item = item)
							semaphore.acquire()
							if threadsSingle: self.metadataUpdate(item = item, result = metadataForeground, lock = lock, locks = locks, semaphore = semaphore, filter = filter, cache = cache, threaded = threaded, mode = 'foreground')
							else: threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'foreground'}, start = True))
						elif refreshing == MetaCache.RefreshBackground:
							if not self.mMetatools.busyStart(media = self.mMedia, item = item):
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'background'})
				else:
					items = Tools.listShuffle(items)
					lookup = []
					counter = abs(quick) if Tools.isInteger(quick) else None
					foreground = Tools.isInteger(quick)
					background = (Tools.isInteger(quick) and quick > 0) or (quick is True)
					for item in items:
						try: refreshing = item[MetaCache.Attribute][MetaCache.AttributeRefresh]
						except: refreshing = MetaCache.RefreshForeground
						if refreshing == MetaCache.RefreshNone:
							lookup.append(item)
						elif refreshing == MetaCache.RefreshForeground and (counter is None or len(lookup) < counter):
							if foreground:
								self.mMetatools.busyStart(media = self.mMedia, item = item)
								lookup.append(item)
								semaphore.acquire()
								if threadsSingle: self.metadataUpdate(item = item, result = metadataForeground, lock = lock, locks = locks, semaphore = semaphore, filter = filter, cache = cache, threaded = threaded, mode = 'foreground')
								else: threadsForeground.append(Pool.thread(target = self.metadataUpdate, kwargs = {'item' : item, 'result' : metadataForeground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'foreground'}, start = True))
							elif background and not self.mMetatools.busyStart(media = self.mMedia, item = item): # Still add foreground requests to the background threads if the value of "quick" forbids foreground retrieval.
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'background'})
						elif refreshing == MetaCache.RefreshBackground or (counter is None or len(lookup) >= counter):
							if background and not self.mMetatools.busyStart(media = self.mMedia, item = item):
								threadsBackground.append({'item' : item, 'result' : metadataBackground, 'lock' : lock, 'locks' : locks, 'semaphore' : semaphore, 'filter' : filter, 'cache' : cache, 'threaded' : threaded, 'mode' : 'background'})
					items = lookup

				# Wait for metadata that does not exist in the metacache.
				[thread.join() for thread in threadsForeground]
				if metadataForeground: metacache.insert(type = MetaCache.TypeMovie, items = metadataForeground)

				# Let the refresh of old metadata run in the background for the next menu load.
				# Only start the threads here, so that background threads do not interfere or slow down the foreground threads.
				if threadsBackground:
					def _metadataBackground():
						if len(threadsBackground) == 1:
							semaphore.acquire()
							self.metadataUpdate(**threadsBackground[0])
						else:
							for i in range(len(threadsBackground)):
								semaphore.acquire()
								threadsBackground[i] = Pool.thread(target = self.metadataUpdate, kwargs = threadsBackground[i], start = True)
							[thread.join() for thread in threadsBackground]
						if metadataBackground: metacache.insert(type = MetaCache.TypeMovie, items = metadataBackground)

					# Make a deep copy of the items, since the items can be edited below while these threads are still busy, and we do not want to store the extra details in the database.
					for i in threadsBackground: i['item'] = Tools.copy(i['item'])
					Pool.thread(target = _metadataBackground, start = True)

				if filter: items = [i for i in items if 'imdb' in i and i['imdb']]

			# Remove temporary, useless, or already aggregatd data, to keep the size of the data passed arround small.
			if clean and items:
				for item in items:
					try: del item['temp']
					except: pass
					try: del item[MetaCache.Attribute]
					except: pass
		except: Logger.error()

		if single: return items[0] if items else None
		else: return items

	def metadataUpdate(self, item, result = None, lock = None, locks = None, semaphore = None, filter = None, cache = False, threaded = None, mode = None):
		try:
			# If many requests are made at the same time, there can be various network errors:
			#	Network Error [Error Type: Connection | Link: https://webservice.fanart.tv/v3/movies/...]: Failed to establish a new connection: [Errno 111] Connection refused
			#	Network Error [Error Type: Connection | Link: https://api.themoviedb.org/3/movie/...?api_key=...&language=en]: Connection aborted
			#	Network Error [Error Type: Connection | Link: https://api.trakt.tv/movies/.../people?extended=full]: Read timed out.
			#	Network Error [Error Type: Timeout | Link: https://webservice.fanart.tv/v3/movies/...]: Read timed out. (read timeout=45
			#	Network Error [Error Type: Connection | Link: https://api.trakt.tv/movies/.../people?extended=full]: Connection aborted
			# This applies to all providers (Trakt, TMDb, Fanart) and errors are very sporadic.
			# Although some servers might implement rate limits, it is highly unlikely that this is the cause.
			# The API would return a JSON or HTTP error if limits were exceeded. If anything, this might be caused directly by the webservers that drop connections if too many simultaneous connection are established in a short time.
			# However, this is also unlikley, because if only a single provider is used (eg just make Fanart requests and disable the rest), the errors are mostly gone.
			# It is highley likley that this is caused by a slow local internet/VPN connection.
			# Most of the errors are from Fanart, and only a few from Tratk/TMDb. Since Fanart data is larger, this might explain the errors (eg timeout) if the local internet connection is slow.
			# If these network errors occur (excluding any HTTP errors, like 404 meaning the specific movie cannot be found on the API), the following is done:
			#	1. Retrieve as much info as possible from the APIs and populate the ListItem with these values to display to the user.
			#	2. Do NOT write the data to the metadata cache, since it is incomplete. If the menu is reloaded, this function will be called again and another attempt will be made to get the metadata.
			#	3. All subrequests are cached. If eg Fanart fails, but Trakt/TMDb was successful, the menu is reloaded and this function called again, only the failed requests are redone, the other ones use the previously cached data.
			#	4. If a request fails due to network issues (excluding HTTP errors), that request is purged from the cache, so that on the next try the old/invalid cached results are not reused.

			id = None
			complete = True

			idImdb = str(item['imdb']) if item and 'imdb' in item and item['imdb'] else None
			idTmdb = str(item['tmdb']) if item and 'tmdb' in item and item['tmdb'] else None
			idTvdb = str(item['tvdb']) if item and 'tvdb' in item and item['tvdb'] else None
			idTrakt = str(item['trakt']) if item and 'trakt' in item and item['trakt'] else None
			idSlug = str(item['slug']) if item and 'slug' in item and item['slug'] else None

			title = item['title'] if item and 'title' in item and item['title'] else None
			year = item['year'] if item and 'year' in item and item['year'] else None

			# By default we do not cache requests to disc, since it takes longer and requires more storage space.
			# If the same movie appears multiple times in the list (some Trakt lists, eg watched list where a movie was watched twice), sub-requests will also have to be executed multiple times, since they are not disc-cached.
			# Cache in memory and use locks to block subsequent calls with the same ID/title until the first request is done and then use those results without executing all the code again.
			id = Memory.id(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
			if not locks is None:
				if not id in locks:
					lock.acquire()
					if not id in locks: locks[id] = Lock()
					lock.release()
				locks[id].acquire()
				data = Memory.get(id = id, uncached = True, local = True, kodi = False)
				if Memory.cached(data):
					item.update(data)
					return

			if not idImdb:
				title = item['title'] if 'title' in item else None
				year = item['year'] if 'year' in item else None
				ids = self.metadataId(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
				if ids:
					if not ids['complete']: complete = False
					ids = ids['data']
					if ids and 'id' in ids:
						ids = ids['id']
						if ids:
							if not idImdb and 'imdb' in ids: idImdb = ids['imdb']
							if not idTmdb and 'tmdb' in ids: idTmdb = ids['tmdb']
							if not idTvdb and 'tvdb' in ids: idTvdb = ids['tvdb']
							if not idTrakt and 'trakt' in ids: idTrakt = ids['trakt']
							if not idSlug and 'slug' in ids: idSlug = ids['slug']
			if filter and not idImdb: return False

			developer = self.metadataDeveloper(idImdb = idImdb, idTmdb = idTmdb, idTrakt = idTrakt, title = title, year = year, item = item)
			if developer: Logger.log('MOVIE METADATA RETRIEVAL [%s]: %s' % (mode.upper() if mode else 'UNKNOWN', developer))

			if self.mDetail == MetaTools.DetailEssential:
				requests = [
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'imdb', 'function' : self.metadataImdb, 'parameters' : {'idImdb' : idImdb, 'full' : False, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
				]
			elif self.mDetail == MetaTools.DetailStandard:
				requests = [
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'trakt', 'function' : self.metadataTrakt, 'parameters' : {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'imdb', 'function' : self.metadataImdb, 'parameters' : {'idImdb' : idImdb, 'full' : False, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'fanart', 'function' : self.metadataFanart, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
				]
			elif self.mDetail == MetaTools.DetailExtended:
				requests = [
					{'id' : 'tmdb', 'function' : self.metadataTmdb, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'trakt', 'function' : self.metadataTrakt, 'parameters' : {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'imdb', 'function' : self.metadataImdb, 'parameters' : {'idImdb' : idImdb, 'full' : True, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
					{'id' : 'fanart', 'function' : self.metadataFanart, 'parameters' : {'idImdb' : idImdb, 'idTmdb' : idTmdb, 'item' : item, 'language' : self.mLanguage, 'cache' : cache, 'threaded' : threaded}},
				]
			else:
				requests = []

			datas = self.metadataRetrieve(requests = requests, threaded = threaded)

			data = {}
			images = {}
			voting = {
				'rating' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'user' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
				'votes' : {'imdb' : None, 'tmdb' : None, 'tvdb' : None, 'trakt' : None, 'metacritic' : None},
			}

			# Keep a specific order. Later values replace newer values.
			for i in ['imdb', 'fanart', 'trakt', 'tmdb']:
				if i in datas:
					values = datas[i]
					if values:
						if not Tools.isArray(values): values = [values]
						for value in values:
							if not value['complete']:
								complete = False
								if developer: Logger.log('INCOMPLETE MOVIE METADATA [%s]: %s' % (i.upper(), developer))
							provider = value['provider']
							value = value['data']
							if value:
								if MetaImage.Attribute in value:
									images = Tools.update(images, value[MetaImage.Attribute], none = True, lists = True, unique = False)
									del value[MetaImage.Attribute]
								if 'rating' in value: voting['rating'][provider] = value['rating']
								if 'ratinguser' in value: voting['user'][provider] = value['ratinguser']
								if 'votes' in value: voting['votes'][provider] = value['votes']
								data = Tools.update(data, value, none = True, lists = False, unique = False)

			data['voting'] = voting
			data = {k : v for k, v in data.items() if not v is None}

			if 'id' in data and data['id']:
				if not idImdb and 'imdb' in data['id']: idImdb = data['id']['imdb']
				if not idTmdb and 'tmdb' in data['id']: idTmdb = data['id']['tmdb']
				if not idTvdb and 'tvdb' in data['id']: idTvdb = data['id']['tvdb']
				if not idTrakt and 'trakt' in data['id']: idTrakt = data['id']['trakt']
				if not idSlug and 'slug' in data['id']: idSlug = data['id']['slug']

			# This is for legacy purposes, since all over Gaia the IDs are accessed at the top-level of the dictionary.
			# At some later point the entire addon should be updated to have the new ID structure.
			if idImdb: data['imdb'] = idImdb
			if idTmdb: data['tmdb'] = idTmdb
			if idTvdb: data['tvdb'] = idTvdb
			if idTrakt: data['trakt'] = idTrakt
			if idSlug: data['slug'] = idSlug

			if images: MetaImage.update(media = MetaImage.MediaMovie, images = images, data = data)

			# Do this before here already.
			# Otherwise a bunch of regular expressions are called every time the menu is loaded.
			self.mMetatools.cleanPlot(metadata = data)

			# Calculate the rating here already, so that we have a default rating/votes if this metadata dictionary is passed around without being cleaned first.
			# More info under meta -> tools.py -> cleanVoting().
			self.mMetatools.cleanVoting(metadata = data)

			Memory.set(id = id, value = data, local = True, kodi = False)
			item.update(data)

			data[MetaCache.Attribute] = {MetaCache.AttributeComplete : complete}
			result.append(data)
		except:
			Logger.error()
		finally:
			if locks and id: locks[id].release()
			if semaphore: semaphore.release()
			self.mMetatools.busyFinish(media = self.mMedia, item = item)

	def metadataDeveloper(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None, item = None):
		if self.mDeveloper:
			data = []

			if not idImdb and item and 'imdb' in item: idImdb = item['imdb']
			if idImdb: data.append('IMDb: ' + idImdb)

			if not idTmdb and item and 'tmdb' in item: idTmdb = item['tmdb']
			if idTmdb: data.append('TMDb: ' + idTmdb)

			if not idImdb and not idTmdb:
				if not idTrakt and item and 'trakt' in item: idTrakt = item['trakt']
				if idTrakt: data.append('Trakt: ' + idTrakt)

			if data: data = ['[%s]' % (' | '.join(data))]
			else: data = ['']

			if not title and item and 'title' in item: title = item['title']
			if not year and item and 'year' in item: year = item['year']

			if title:
				data.append(title)
				if year: data.append('(%d)' % year)

			return ' '.join(data)
		return None

	# requests = [{'id' : required-string, 'function' : required-function, 'parameters' : optional-dictionary}, ...]
	def metadataRetrieve(self, requests, threaded = None):
		def _metadataRetrieve(request, result):
			try:
				if 'parameters' in request: data = request['function'](**request['parameters'])
				else: data = request['function']()
				result[request['id']] = data
			except:
				Logger.error()
				result[request['id']] = None

		result = {}
		if requests:
			if threaded is None: threaded = len(requests) > 1
			if threaded:
				threads = []
				for request in requests:
					threads.append(Pool.thread(target = _metadataRetrieve, kwargs = {'request' : request, 'result' : result}, start = True))
				[thread.join() for thread in threads]
			else:
				for request in requests:
					_metadataRetrieve(request = request, result = result)
		return result

	def metadataRequest(self, link, data = None, headers = None, method = None, cache = False):
		# HTTP error 429 can be thrown if too many requests were made in a short time.
		# This should only happen with Trakt (which does not call this function), since TMDb/TVDb/Fanart should not have any API limits at the moment.
		# Still check for it, since in special cases 429 might still happen (eg: the TMDb CDN/Cloudflare might block more than 50 concurrent connections).
		# This should not be an issue with normal use, only with batch-generating the preprocessed database that makes 1000s of request every few minutes.

		networker = Networker()
		if cache:
			if cache is True: cache = Cache.TimeoutLong
			result = self.mCache.cache(mode = None, timeout = cache, refresh = None, function = networker.request, link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork or result['error']['code'] == 429:
				# Delete the cache, otherwise the next call will return the previously failed request.
				self.mCache.cacheDelete(networker.request, link = link, data = data, headers = headers, method = method)
				return False
		else:
			result = networker.request(link = link, data = data, headers = headers, method = method)
			if not result or result['error']['type'] in Networker.ErrorNetwork or result['error']['code'] == 429: return False
		return Networker.dataJson(result['data'])

	def metadataId(self, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, title = None, year = None):
		result = self.mMetatools.idMovie(idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, title = title, year = year)
		return {'complete' : True, 'data' : {'id' : result} if result else result}

	def metadataTrakt(self, idImdb = None, idTrakt = None, language = None, item = None, people = False, cache = False, threaded = None):
		complete = True
		result = None
		try:
			id = idTrakt if idTrakt else idImdb
			if id:
				requests = [{'id' : 'movie', 'function' : trakt.getMovieSummary, 'parameters' : {'id' : id, 'full' : True, 'cache' : cache, 'failsafe' : True}}]

				# We already retrieve the cast from TMDb and those values contain thumnail images.
				# Retrieving the cast here as well will not add any new info and just prolong the request/processing time.
				if people: requests.append({'id' : 'people', 'function' : trakt.getPeopleMovie, 'parameters' : {'id' : id, 'full' : True, 'cache' : cache, 'failsafe' : True}})

				translation = language and not language == Language.EnglishCode
				if translation: requests.append({'id' : 'translation', 'function' : trakt.getMovieTranslation, 'parameters' : {'id' : id, 'lang' : language, 'full' : True, 'cache' : cache, 'failsafe' : True}})

				data = self.metadataRetrieve(requests = requests, threaded = threaded)
				if data:
					dataMovie = data['movie']
					dataPeople = data['people'] if people else None
					dataTranslation = data['translation'] if translation else None
					if dataMovie is False or (people and dataPeople is False) or (translation and dataTranslation is False): complete = False

					if dataMovie or dataPeople or dataTranslation:
						result = {}

						if dataMovie and 'title' in dataMovie and 'ids' in dataMovie:
							ids = dataMovie.get('ids')
							if ids:
								ids = {k : str(v) for k, v in ids.items() if v}
								if ids: result['id'] = ids

							title = dataMovie.get('title')
							if title: result['title'] = Networker.htmlDecode(title)

							tagline = dataMovie.get('tagline')
							if tagline: result['tagline'] = Networker.htmlDecode(tagline)

							plot = dataMovie.get('overview')
							if plot: result['plot'] = Networker.htmlDecode(plot)

							year = dataMovie.get('year')
							if year and Tools.isNumber(year): result['year'] = year

							premiered = dataMovie.get('released')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered: result['premiered'] = premiered

							genre = dataMovie.get('genres')
							if genre: result['genre'] = [i.title() for i in genre]

							mpaa = dataMovie.get('certification')
							if mpaa: result['mpaa'] = mpaa

							rating = dataMovie.get('rating')
							if not rating is None: result['rating'] = rating

							votes = dataMovie.get('votes')
							if not votes is None: result['votes'] = votes

							duration = dataMovie.get('runtime')
							if not duration is None: result['duration'] = duration * 60

							status = dataMovie.get('status')
							if status: result['status'] = status.title()

							country = dataMovie.get('country')
							if country: result['country'] = [country]

							languages = dataMovie.get('language')
							if languages: result['language'] = [languages]

							trailer = dataMovie.get('trailer')
							if trailer: result['trailer'] = trailer

							homepage = dataMovie.get('homepage')
							if homepage: result['homepage'] = homepage

						if dataTranslation:
							title = dataTranslation.get('title')
							if title:
								if result['title']: result['originaltitle'] = result['title']
								result['title'] = Networker.htmlDecode(title)

							tagline = dataTranslation.get('tagline')
							if tagline: result['tagline'] = Networker.htmlDecode(tagline)

							plot = dataTranslation.get('overview')
							if plot: result['plot'] = Networker.htmlDecode(plot)

						if dataPeople and ('crew' in dataPeople or 'cast' in dataPeople):
							if 'crew' in dataPeople:
								dataCrew = dataPeople['crew']
								if dataCrew:
									def _metadataTraktPeople(data, job):
										people = []
										if data:
											for i in data:
												if 'jobs' in i:
													jobs = i['jobs']
													if jobs and any(j.lower() in job for j in jobs):
														people.append(i['person']['name'])
										return Tools.listUnique(people)

									if 'directing' in dataCrew:
										director = _metadataTraktPeople(data = dataCrew['directing'], job = ['director'])
										if director: result['director'] = director
									if 'writing' in dataCrew:
										writer = _metadataTraktPeople(data = dataCrew['writing'], job = ['writer', 'screenplay', 'author'])
										if writer: result['writer'] = writer

							if 'cast' in dataPeople:
								dataCast = dataPeople['cast']
								if dataCast:
									cast = []
									order = 0
									for i in dataCast:
										if 'characters' in i and i['characters']: character = ' / '.join(i['characters'])
										else: character = None
										cast.append({'name' : i['person']['name'], 'role' : character, 'order' : order})
										order += 1
									if cast: result['cast'] = cast
		except: Logger.error()
		return {'provider' : 'trakt', 'complete' : complete, 'data' : result}

	def metadataTmdb(self, idImdb = None, idTmdb = None, language = None, item = None, cache = False, threaded = None):
		complete = True
		result = None
		try:
			id = idTmdb if idTmdb else idImdb
			if id:
				def _metadataTmdb(id, mode = None, language = None, cache = True):
					link = 'https://api.themoviedb.org/3/movie/%s%s' % (id, ('/' + mode) if mode else '')
					data = {'api_key' : self.mAccountTmdb}
					if language: data['language'] = language
					return self.metadataRequest(method = Networker.MethodGet, link = link, data = data, cache = cache)

				requests = [
					{'id' : 'movie', 'function' : _metadataTmdb, 'parameters' : {'id' : id, 'language' : language, 'cache' : cache}},
					{'id' : 'people', 'function' : _metadataTmdb, 'parameters' : {'id' : id, 'mode' : 'credits', 'cache' : cache}},
					{'id' : 'image', 'function' : _metadataTmdb, 'parameters' : {'id' : id, 'mode' : 'images', 'cache' : cache}},
				]
				data = self.metadataRetrieve(requests = requests, threaded = threaded)

				if data:
					# https://www.themoviedb.org/talk/53c11d4ec3a3684cf4006400
					imageLink = 'https://image.tmdb.org/t/p/w%d%s'
					imageSize = {MetaImage.TypePoster : 780, MetaImage.TypeFanart : 1280, MetaImage.TypeClearlogo : 500, MetaImage.TypePhoto : 185}

					dataMovie = data['movie']
					dataPeople = data['people']
					dataImage = data['image']

					if dataMovie is False or dataPeople is False or dataImage is False: complete = False

					if dataMovie or dataPeople or dataImage:
						result = {}

						if dataMovie and 'title' in dataMovie and 'id' in dataMovie:
							ids = {}
							idTmdb = dataMovie.get('id')
							if idTmdb: ids['tmdb'] = str(idTmdb)
							idImdb = dataMovie.get('imdb_id')
							if idImdb: ids['imdb'] = str(idImdb)
							if ids: result['id'] = ids

							title = dataMovie.get('title')
							if title: result['title'] = Networker.htmlDecode(title)

							originaltitle = dataMovie.get('original_title')
							if originaltitle: result['originaltitle'] = Networker.htmlDecode(originaltitle)

							tagline = dataMovie.get('tagline')
							if tagline: result['tagline'] = Networker.htmlDecode(tagline)

							plot = dataMovie.get('overview')
							if plot: result['plot'] = Networker.htmlDecode(plot)

							premiered = dataMovie.get('release_date')
							if premiered:
								premiered = Regex.extract(data = premiered, expression = '(\d{4}-\d{2}-\d{2})', group = 1)
								if premiered:
									result['premiered'] = premiered
									year = Regex.extract(data = premiered, expression = '(\d{4})-', group = 1)
									if year: result['year'] = int(year)

							genre = dataMovie.get('genres')
							if genre: result['genre'] = [i['name'].title() for i in genre]

							rating = dataMovie.get('vote_average')
							if not rating is None: result['rating'] = rating

							votes = dataMovie.get('vote_count')
							if not votes is None: result['votes'] = votes

							duration = dataMovie.get('runtime')
							if not duration is None: result['duration'] = duration * 60

							status = dataMovie.get('status')
							if status: result['status'] = status.title()

							studio = dataMovie.get('production_companies')
							if studio: result['studio'] = [i['name'] for i in studio]

							country = dataMovie.get('production_countries')
							if country: result['country'] = [i['iso_3166_1'].lower() for i in country]

							languages = dataMovie.get('spoken_languages')
							if languages: result['language'] = [i['iso_639_1'].lower() for i in languages]
							languages = dataMovie.get('original_language')
							if languages:
								languages = [languages]
								if 'language' in result: Tools.listUnique(languages + result['language'])
								else: result['language'] = languages

							homepage = dataMovie.get('homepage')
							if homepage: result['homepage'] = homepage

							finance = {}
							budget = dataMovie.get('budget')
							if budget: finance['budget'] = budget
							revenue = dataMovie.get('revenue')
							if revenue: finance['revenue'] = revenue
							if finance:
								if 'budget' in finance and 'revenue' in finance: finance['profit'] = finance['revenue'] - finance['budget']
								result['finance'] = finance

							collectionData = dataMovie.get('belongs_to_collection')
							if collectionData:
								collection = {}
								collectionId = collectionData.get('id')
								if collectionId: collection['id'] = collectionId
								collectionTitle = collectionData.get('name')
								if collectionTitle: collection['title'] = Networker.htmlDecode(collectionTitle)

								if collection:
									collectionImage = {}
									collectionPoster = collectionData.get('poster_path')
									if collectionPoster: collectionImage[MetaImage.TypePoster] = [imageLink % (imageSize[MetaImage.TypePoster], collectionPoster)]
									collectionFanart = collectionData.get('backdrop_path')
									if collectionFanart: collectionImage[MetaImage.TypeFanart] = [imageLink % (imageSize[MetaImage.TypeFanart], collectionFanart)]

									collection[MetaImage.Attribute] = collectionImage
									result['collection'] = collection

									# For Kodi.
									#if collection['id']: result['setid'] = collection['id'] # This seems to be the local DB ID for the set (in the Kodi info dialog there is a special button that redirects to the local library set menu).
									if collection['title']: result['set'] = collection['title']

						try:
							if dataPeople:
								if 'crew' in dataPeople:
									dataCrew = dataPeople['crew']
									if dataCrew:
										def _metadataTmdbPeople(data, department, job):
											people = []
											if data:
												for i in data:
													if 'department' in i and department == i['department'].lower():
														if 'name' in i and i['name'] and 'job' in i and i['job'].lower() in job:
															people.append(i['name'])
											return Tools.listUnique(people)

										# https://api.themoviedb.org/3/configuration/jobs?api_key=xxx

										director = _metadataTmdbPeople(data = dataCrew, department = 'directing', job = ['director', 'co-director', 'series director'])
										if director: result['director'] = director

										writer = _metadataTmdbPeople(data = dataCrew, department = 'writing', job = ['writer', 'screenplay', 'author', 'co-writer', 'original film writer', 'original film writer', 'original story', 'story'])
										if writer: result['writer'] = writer

								if 'cast' in dataPeople:
									dataCast = dataPeople['cast']
									if dataCast:
										cast = []
										for i in dataCast:
											if 'character' in i and i['character']: character = i['character']
											else: character = None
											if 'order' in i: order = i['order']
											else: order = None
											if 'profile_path' in i and i['profile_path']: thumbnail = imageLink % (imageSize[MetaImage.TypePhoto], i['profile_path'])
											else: thumbnail = None
											cast.append({'name' : i['name'], 'role' : character, 'order' : order, 'thumbnail' : thumbnail})
										if cast: result['cast'] = cast
						except: Logger.error()

						try:
							if dataImage:
								images = {i : [] for i in MetaImage.Types}
								poster = [[], []]
								keyart = [[], []]
								fanart = [[], []]
								landscape = [[], []]

								entries = (
									('posters', MetaImage.TypePoster),
									('backdrops', MetaImage.TypeFanart),
									('logos', MetaImage.TypeClearlogo),
								)
								for entry in entries:
									try:
										if entry[0] in dataImage:
											indexed = 0
											for i in dataImage[entry[0]]:
												indexed += 1
												index = 99999999 - indexed
												vote = i.get('vote_average')
												vote = float(vote) if vote else 0
												sort = {
													MetaImage.SortIndex : index,
													MetaImage.SortVote : vote,
													MetaImage.SortVoteIndex : [vote, index],
												}
												image = MetaImage.create(link = imageLink % (imageSize[entry[1]], i.get('file_path')), provider = MetaImage.ProviderTmdb, language = i.get('iso_639_1'), sort = sort)
												if entry[1] == MetaImage.TypePoster:
													if image[MetaImage.AttributeLanguage]:
														poster[0].append(image)
														keyart[1].append(image)
													else:
														poster[1].append(image)
														keyart[0].append(image)
												elif entry[1] == MetaImage.TypeFanart:
													if image[MetaImage.AttributeLanguage]:
														landscape[0].append(image)
														fanart[1].append(image)
													else:
														landscape[1].append(image)
														fanart[0].append(image)
												else:
													images[entry[1]].append(image)
									except: Logger.error()

								images[MetaImage.TypePoster] = poster[0] + poster[1]
								images[MetaImage.TypeKeyart] = keyart[0] + keyart[1]
								images[MetaImage.TypeFanart] = fanart[0] + fanart[1]
								images[MetaImage.TypeLandscape] = landscape[0] + landscape[1]

								if images: result[MetaImage.Attribute] = images
						except: Logger.error()
		except: Logger.error()
		return {'provider' : 'tmdb', 'complete' : complete, 'data' : result}

	def metadataFanart(self, idImdb = None, idTmdb = None, language = None, item = None, cache = False, threaded = None):
		complete = True
		result = None
		try:
			if idImdb or idTmdb:
				images = MetaFanart.movie(idImdb = idImdb, idTmdb = idTmdb, cache = cache)
				if images is False: complete = False
				elif images: result = {MetaImage.Attribute : images}
		except: Logger.error()
		return {'provider' : 'fanart', 'complete' : complete, 'data' : result}

	def metadataImdb(self, idImdb = None, language = None, full = False, item = None, cache = False, threaded = None):
		# Only do this if there is no IMDb rating in in the item, that is, the item does not come from a IMDb list.
		# Retrieving the detailed IMDb data does not really add extra metadata above TMDb/Trakt, except for the rating/vote and the revenue (which is also on TMDb).
		# A single IMDb page is more than 200KB, so retrieving 50 movies will take 10MB+.
		if full and idImdb and (not 'temp' in item or not 'imdb' in item['temp'] or not 'rating' in item['temp']['imdb']):
			data = MetaImdb.details(id = idImdb, cache = cache)
			if data: item = data

		results = []

		complete = True
		result = None
		try:
			if item and 'temp' in item and 'imdb' in item['temp']:
				try:
					if 'poster' in item['temp']['imdb']:
						poster = item['temp']['imdb']['poster']
						if poster: result = {MetaImage.Attribute : {MetaImage.TypePoster : [MetaImage.create(link = poster, provider = MetaImage.ProviderImdb)]}}
				except: Logger.error()

				for i in ['rating', 'ratinguser', 'votes']:
					try:
						if i in item['temp']['imdb']:
							if result is None: result = {}
							result[i] = item['temp']['imdb'][i]
					except: Logger.error()
		except: Logger.error()
		results.append({'provider' : 'imdb', 'complete' : complete, 'data' : result})

		complete = True
		result = None
		try:
			if item and 'temp' in item and 'metacritic' in item['temp']:
				for i in ['rating', 'ratinguser', 'votes']:
					try:
						if i in item['temp']['metacritic']:
							if result is None: result = {}
							result[i] = item['temp']['metacritic'][i]
					except: Logger.error()
		except: Logger.error()
		results.append({'provider' : 'metacritic', 'complete' : complete, 'data' : result})

		return results

	##############################################################################
	# NAVIGATION
	##############################################################################

	def check(self, metadatas):
		if Tools.isString(metadatas):
			try: metadatas = Converter.jsonFrom(metadatas)
			except: pass
		if not metadatas:
			Loader.hide()
			Dialog.notification(title = 32001, message = 33049, icon = Dialog.IconInformation)
			return None
		return metadatas

	def menu(self, metadatas, next = True):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			directory = Directory(content = Directory.ContentSettings, media = Media.TypeMovie, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.items(metadatas = metadatas, media = self.mMedia, kids = self.mKids, next = next, mixed = self.mModeMixed, hide = True, hideSearch = self.mModeSearch, hideRelease = self.mModeRelease, contextPlaylist = True, contextShortcutCreate = True))
			directory.finish(loader = self.mModeSearch) # The loader initiated from search() ios not automatically hidden by Kodi once the menu has loaded. Probably because searching starts a new sub-process and does not load the directory like other menus.

	def directory(self, metadatas):
		metadatas = self.check(metadatas = metadatas)
		if metadatas:
			directory = Directory(content = Directory.ContentSettings, cache = True, lock = False)
			directory.addItems(items = self.mMetatools.directories(metadatas = metadatas, media = self.mMedia, kids = self.mKids))
			directory.finish()

	def context(self, idImdb = None, idTmdb = None, title = None, year = None):
		metadata = self.metadata(idImdb = idImdb, idTmdb = idTmdb, title = title, year = year)
		return self.mMetatools.context(metadata = metadata, media = self.mMedia, kids = self.mKids, playlist = True, shortcutCreate = True)
