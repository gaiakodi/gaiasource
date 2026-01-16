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

'''
	###################################################################################################################
	# FOR THIRD-PARTY DEVELOPERS
	###################################################################################################################

		If you want to call Gaia from your addon or widget, use one of the following endpoints:
			1. menu:	Load a variety of different menus.
			2. search:	Search for a title using a query.
			3. scrape:	Scrape a specific title for links.
			4. play:	Play a link from a scraped title.

		COMMAND URI:

			plugin://plugin.video.gaia/?action=...&param1=...&param2=...&param3=...

		PYTHON:

			import xbmc
			xbmc.executebuiltin("RunPlugin(plugin://plugin.video.gaia/?action=...&param1=...&param2=...&param3=...)")

	###################################################################################################################
	# MENU
	###################################################################################################################

		Open any of the menus or submenus in Gaia.
		This can also be used to load menus and lists inside Kodi skin widgets.

		PARAMETERS:

			- action:		Specify the action, in this case loading a menu.
				Required:	Yes
				Type:		String
				Example:	action=menu
				Values:		menu
			- menu:			Specify the menu type.
				Required:	Yes
				Type:		String
				Example:	menu=media
				Values:		media (movie and show menus)
							folder (directory menus)
							person (people menus)
							extra (season extra menus)
							tool (tools menus)
			- content:		Specify the content loaded into the menu.
				Required:	Yes (media menus), No (other menus)
				Type:		String
				Example:	content=discover
				Values:		discover (discover content based on parameters)
							search (search for content using a query)
							quick (the Quick menu)
							progress (the Progress menu)
							history (the History menu)
							arrival (the Arrivals menu)
							set (the Sets menu)
							list (the Lists menu)
							person (the People menu)
							season (the season menus under shows)
							episode (the episode menus under seasons)
			- media:		Specify the media type if "menu=media". If no media is provided, "mixed" is assumed.
				Required:	Yes (media menus), No (other menus)
				Type:		String
				Example:	media=movie
				Values:		movie (movie menus)
							show (show menus)
							season (season menus)
							episode (episode menus)
							mixed (mixed movie and show menus, where supported)
			- niche:		Specify the niche to narrow down the content.
				Required:	No
				Type:		String, List
				Example:	niche=mini | niche=anime-best
				Values:		feature (full-length feature movies)
							short (short films or shows)
							special (TV specials)
							multi (muti-season shows)
							mini (single-season mini-series)
							anima (animation of all types)
							anime (Japanese animation)
							donghua (Chinese animation)
							docu (documentaries)
							family (family and children)
							all (all releases)
							new (new releases, typically sorted descending by release date)
							home (home releases, typically sorted descending by release date)
							best (best rated titles, typically sorted descending by rating)
							worst (worst rated titles, typically sorted ascending by rating)
							prestige (high quality releases, typically filtered by a minimum rating and minimum number of votes)
							popular (most popular titles, typically sorted descending by number of watches or votes)
							unpopular (least popular titles, typically sorted ascending by number of watches or votes)
							viewed (widely viewed titles, typically filtered by a minimum number of votes)
							gross (highest grossing box office hits, typically sorted descending by gross income)
							award (award winners)
							trend (currently trending titles, typically filtered/sorted by current temporary trendiness or popularity)
							- A full list of values is available under lib/modules/tools.py/class Media
			- page:			Specify the page number.
				Required:	No
				Type:		Integer
				Example:	page=2
				Values:		[1,infinity]
			- limit:		Specify the number of titles to list per page. This should generally not be used, as the value is determined by the addon settings and the capability of the provider. Stick to a limit of 100 or lower.
				Required:	No
				Type:		Integer
				Example:	limit=20
				Values:		[1,250]
			- provider:		Specify the metadata provider to use for the menu. This should generally not be used, as the best possible provider is determined based on the other parameters.
				Required:	No
				Type:		String
				Example:	provider=trakt
				Values:		trakt (load the menu using Trakt)
							imdb (load the menu using IMDb)
							tmdb (load the menu using TMDb)
			- id:			Specify a provider ID to load season and episode menus. One or more IDs can be passed.
				Required:	Yes (season and episode menus), No (other menus)
				Type:		String
				Example:	trakt=123456 | imdb=tt123456 | trakt=123456&imdb=tt123456
				Values:		trakt=<id> (using a Trakt ID)
							imdb=<id> (using an IMDb ID)
							tmdb=<id> (using a TMDb ID)
							tvdb=<id> (using a TVDb ID)
			- title:		Specify the title. It is highly recommended to use one of the Trakt/IMDb/TMDb/TVDb IDs, since they are faster and more accurate. If the ID is not known, a title, and preferably a year, can be used instead.
				Required:	No
				Type:		String
				Example:	title=Some%20Title
				Values:		Any title.
			- year:			Specify the year. This narrows down a search or discovery to a specific year.
				Required:	No
				Type:		Integer, Range
				Example:	year=2010 | year=2015,2018
				Values:		Any year.
			- season:		Specify the season number for episode menus.
				Required:	Yes (episode menus), No (other menus)
				Type:		Integer
				Example:	season=2
				Values:		[0,infinity]
			- query:		Specify the search query when "content=search". If no query is provided, an input dialog will be shown.
				Required:	No
				Type:		String
				Example:	query=some%20title
				Values:		Any search string
			- keyword:		Specify additional keywords to narrow down the discovery or search. Only supported by some providers.
				Required:	No
				Type:		String, List
				Example:	keyword=happy
				Values:		Any keywords
			- keyword:		Specify additional keywords to narrow down the discovery or search. Only supported by some providers.
				Required:	No
				Type:		String, List
				Example:	keyword=happy
				Values:		Any keywords
			- release:		Specify the release type.
				Required:	No
				Type:		String
				Example:	release=home
				Values:		new (new releases for movies and shows)
							home (home, digital, and physical releases for movies)
							future (future releases for movies and shows)
			- date:			Specify a date to narrow down the results.
				Required:	No
				Type:		Integer (timestamp), String (YYYY-MM-DD), Range
				Example:	date=1732540312 | date=2010-05-20 | date=1732040312,1732540312 | date=2010-05-20,2010-06-10
				Values:		Any timestamp or date string.
			- duration:		Specify the runtime to narrow down the results.
				Required:	No
				Type:		Integer (minimum seconds), Range (minimum to maximum)
				Example:	duration=1800 | duration=1500,3000
				Values:		Any duration in seconds
			- genre:		Specify the genre to narrow down the results.
				Required:	No
				Type:		String, List
				Example:	genre=action | genre=action,thriller
				Values:		Any support genre. Values are ANDed or ORed together, depending on the provider.
							- A full list of values is available under lib/meta/tools.py/class MetaTools
			- language:		Specify the language to narrow down the results.
				Required:	No
				Type:		String, List
				Example:	genre=en | genre=en,fr
				Values:		Any support language in as ISO-639-1 codes. Values are ANDed or ORed together, depending on the provider.
							- A full list of values is available under lib/modules/tools.py/class Language
			- country:		Specify the country to narrow down the results.
				Required:	No
				Type:		String, List
				Example:	genre=us | genre=us,fr
				Values:		Any support language in as ISO Alpha-2 codes. Values are ANDed or ORed together, depending on the provider.
							- A full list of values is available under lib/modules/tools.py/class Country
			- certificate:	Specify the audience certificate to narrow down the results.
				Required:	No
				Type:		String
				Example:	certificate=pg13 | certificate=tvpg
				Values:		Any support certificate. Currently only MPAA certificates are fully supported
							nr, g, pg, pg13, r, nc17 (movies)
							nr, tvg, tvy, tvy7, tvpg, tv13, tv14, tvma (shows)
							- A full list of values is available under lib/modules/tools.py/class Audience
			- company:		Specify the company (studio or network) to narrow down the results. This uses one of the main supported company identifiers.
				Required:	No
				Type:		String
				Example:	company=netflix
				Values:		Any support company.
							- A full list of values is available under lib/meta/tools.py/class MetaTools
			- studio:		Specify the studio to narrow down the results. This is similar to "company", but instead uses a Trakt or IMDb studio ID.
				Required:	No
				Type:		String
				Example:	studio=co123456 (IMDb) | studio=123 (Trakt)
				Values:		Any support studio.
							- A full list of values is available under lib/meta/providers/imdb.py|trakt.py
			- network:		Specify the network to narrow down the results. This is similar to "company", but instead uses a Trakt or IMDb network ID.
				Required:	No
				Type:		String
				Example:	network=co123456 (IMDb) | network=123 (Trakt)
				Values:		Any support network.
							- A full list of values is available under lib/meta/providers/imdb.py|trakt.py
			- award:		Specify the won awards to narrow down the results. This only works for IMDb.
				Required:	No
				Type:		String
				Example:	award=academywinner | award=top250
				Values:		Any support award.
							- A full list of values is available under lib/meta/tools.py/class MetaTools
			- gender:		Specify the person's gender for people menus. This only works for IMDb.
				Required:	No
				Type:		String
				Example:	gender=male
				Values:		male, female, nonbinary, other
			- rating:		Specify the rating to narrow down the results. Note that the ratings are different between Trakt and IMDb.
				Required:	No
				Type:		Decimal, Range
				Example:	rating=6.5 (minimum) | rating=7.0,8.5 (minimum to maximum)
				Values:		[0.0, 10.0]
			- votes:		Specify the number of votes to narrow down the results. Note that the votes are different between Trakt and IMDb.
				Required:	No
				Type:		Integer, Range
				Example:	votes=1000 (minimum) | rating=2000,5000 (minimum to maximum)
				Values:		[0, infinity]

		EXAMPLES:

			- Main movie menu:
				plugin://plugin.video.gaia/?action=menu&menu=folder&media=movie
			- Niche anime show menu:
				plugin://plugin.video.gaia/?action=menu&menu=folder&media=show&niche=anime
			- Movie explore menu for best rated:
				plugin://plugin.video.gaia/?action=menu&menu=media&content=discover&media=movie&niche=best
			- Show genre menu for action:
				plugin://plugin.video.gaia/?action=menu&menu=media&content=discover&media=show&genre=action
			- Movie arrivals menu:
				plugin://plugin.video.gaia/?action=menu&menu=media&content=arrival&media=movie
			- Show progress menu:
				plugin://plugin.video.gaia/?action=menu&menu=media&content=progress&media=show
			- Mixed quick menu:
				plugin://plugin.video.gaia/?action=menu&menu=media&content=quick
			- Mixed search menu:
				plugin://plugin.video.gaia/?action=menu&menu=media&content=search
			- Season menu using a title (rather use an ID):
				plugin://plugin.video.gaia/?action=menu&menu=media&content=season&media=season&title=Silo
			- Episode menu using IDs:
				plugin://plugin.video.gaia/?action=menu&menu=media&content=episode&trakt=180770&season=2

	###################################################################################################################
	# SEARCH
	###################################################################################################################

		Search for titles using a search query.
		This is a shorthand version of the menu endpoint "action=menu&menu=media&content=search".

		PARAMETERS:

			- action:		Specify the action, in this case searching.
				Required:	Yes
				Type:		String
				Example:	action=search
				Values:		search
			- media:		Specify the media type to search. If no media is provided, "mixed" is assumed.
				Required:	No
				Type:		String
				Example:	media=movie
				Values:		movie (movie searches)
							show (show searches)
							set (set searches)
							list (list searches)
							person (people searches)
							mixed (mixed movie and show searches)
			- niche:		Specify the niche to narrow down the search. This will return fewer results.
				Required:	No
				Type:		String, List
				Example:	niche=anime
				Values:		feature (full-length feature movies)
							short (short films or shows)
							special (TV specials)
							multi (muti-season shows)
							mini (single-season mini-series)
							anima (animation of all types)
							anime (Japanese animation)
							donghua (Chinese animation)
							docu (documentaries)
							family (family and children)
							- A full list of values is available under lib/modules/tools.py/class Media
			- query:		Specify the search query. If no query is provided, an input dialog will be shown.
				Required:	No
				Type:		String
				Example:	query=some%20title
				Values:		Any search string
			- page:			Specify the page number.
				Required:	No
				Type:		Integer
				Example:	page=2
				Values:		[1,infinity]
			- limit:		Specify the number of titles to list per page. This should generally not be used, as the value is determined by the addon settings and the capability of the provider. Stick to a limit of 50 or lower.
				Required:	No
				Type:		Integer
				Example:	limit=10
				Values:		[1,250]
			- provider:		Specify the metadata provider to use for the search. This should generally not be used, as the best possible provider is automatically determined.
				Required:	No
				Type:		String
				Example:	provider=trakt
				Values:		trakt (search with Trakt)
							imdb (search with IMDb)
							tmdb (search with TMDb)
			- other:		Any of the other parameters listed under the "menu" endpoint can be used (genre, year, language, etc). This will reduce the search results and should generally not be used.

		EXAMPLES:

			- Search movies:
				plugin://plugin.video.gaia/?action=search&media=movie
			- Search anime movies and shows:
				plugin://plugin.video.gaia/?action=search&niche=anime
			- Search sets:
				plugin://plugin.video.gaia/?action=search&media=set
			- Search people using a fixed query:
				plugin://plugin.video.gaia/?action=search&media=person&query=james

	###################################################################################################################
	# SCRAPE
	###################################################################################################################

		Scrape a specific title for links.

		PARAMETERS:

			- action:		Specify the action, in this case scraping.
				Required:	Yes
				Type:		String
				Example:	action=scrape
				Values:		scrape
			- media:		Specify the media type to search.
				Required:	Yes
				Type:		String
				Example:	media=movie
				Values:		movie (movie scrapes), show (episode scrapes)
			- trakt:		Specify the Trakt ID.
				Required:	No
				Type:		String
				Example:	trakt=123456
				Values:		Any valid Trakt ID
			- imdb:			Specify the IMDb ID.
				Required:	No
				Type:		String
				Example:	imdb=tt123456
				Values:		Any valid IMDb ID
			- tmdb:			Specify the TMDb ID.
				Required:	No
				Type:		String
				Example:	tmdb=123456
				Values:		Any valid TMDb ID
			- tvdb:			Specify the TVDb ID.
				Required:	No
				Type:		String
				Example:	tvdb=123456
				Values:		Any valid TVDb ID
			- title:		Specify a title instead of an ID.
				Required:	No
				Type:		String
				Example:	title=Some%20Title
				Values:		Any valid title
			- year:			Specify a year together with the title.
				Required:	No
				Type:		Integer
				Example:	year=2010
				Values:		Any valid year
			- season:		Specify the season number.
				Required:	Yes (shows), No (movies)
				Type:		Integer
				Example:	season=1
				Values:		Any valid season number
			- episode:		Specify the episode number.
				Required:	Yes (shows), No (movies)
				Type:		Integer
				Example:	episode=1
				Values:		Any valid episode number

		LOOKUP:

			- You can scrape by using a single or multiple IDs, by providing a title and year, or both.
			- Scraping by ID is always better, faster, and more reliable than scraping by title and year.
			- If IDs are provided, no title or year is required.
			- If a title is provided, a year is not required. However, a year will substantially improve the chances of picking
			  the correct title, especially if there are multiple movies/shows with the same title, but released in different years.

		IDS:

			The best way to scrape is by using an ID. You can pass in IDs from multiple providers and let Gaia figure out which
			one to use. The reliability and accuracy of IDs is as follows (from most reliable to least reliable):

			- Movies: Trakt, IMDb, TMDb, (TVDb)
			- Shows: Trakt, IMDb, TVDb, (TMDb)

			You should avoid searching movies by TVDb ID and shows by TMDb ID. Although it might work in some cases, most of the time
			nothing will be found. If you have IDs from multiple providers, just pass all of them in.

		EXAMPLES:

			- Movies:
				- Search by single ID:
					plugin://plugin.video.gaia/?action=scrape&media=movie&imdb=tt1392190
					plugin://plugin.video.gaia/?action=scrape&media=movie&tmdb=76341
					plugin://plugin.video.gaia/?action=scrape&media=movie&trakt=56360
				- Search by multiple IDs:
					plugin://plugin.video.gaia/?action=scrape&media=movie&imdb=tt1392190&tmdb=76341&trakt=56360
				- Search by title and year:
					plugin://plugin.video.gaia/?action=scrape&media=movie&title=Mad%20Max%3A%20Fury%20Road&year=2015
				- Search by title:
					plugin://plugin.video.gaia/?action=scrape&media=movie&title=Mad%20Max%3A%20Fury%20Road
				- Search by anything:
					plugin://plugin.video.gaia/?action=scrape&media=movie&imdb=tt1392190&tmdb=76341&trakt=56360&title=Mad%20Max%3A%20Fury%20Road&year=2015

			- Shows:
				- Search by single ID:
					plugin://plugin.video.gaia/?action=scrape&media=show&imdb=tt0944947&season=8&episode=2
					plugin://plugin.video.gaia/?action=scrape&media=show&tvdb=121361&season=8&episode=2
					plugin://plugin.video.gaia/?action=scrape&media=show&trakt=1390&season=8&episode=2
				- Search by multiple IDs:
					plugin://plugin.video.gaia/?action=scrape&media=show&imdb=tt0944947&tvdb=121361&trakt=1390&season=8&episode=2
				- Search by title and year:
					plugin://plugin.video.gaia/?action=scrape&media=show&title=Game%20of%20Thrones&year=2011&season=8&episode=2
				- Search by title:
					plugin://plugin.video.gaia/?action=scrape&media=show&title=Game%20of%20Thrones&season=8&episode=2
				- Search by anything:
					plugin://plugin.video.gaia/?action=scrape&media=show&imdb=tt0944947&tvdb=121361&trakt=1390&title=Game%20of%20Thrones&year=2011&season=8&episode=2

	###################################################################################################################
	# PLAY
	###################################################################################################################

		Play a specific link from a previous scrape.

		PARAMETERS:

			- action:		Specify the action, in this case playing.
				Required:	Yes
				Type:		String
				Example:	action=play
				Values:		play
			- media:		Specify the media type to play.
				Required:	Yes
				Type:		String
				Example:	media=movie
				Values:		movie (movie plays), show (episode plays)
			- source:		One of the source JSON objects returned by a previous scrape. This is not very user-friendly at the moment and will be updated int he future to take in a source ID, instead of a full object.
				Required:	Yes
				Type:		Dictionary
				Example:	source={...}
				Values:		Any valid source dictionary
			- trakt:		Specify the Trakt ID.
				Required:	No
				Type:		String
				Example:	trakt=123456
				Values:		Any valid Trakt ID
			- imdb:			Specify the IMDb ID.
				Required:	No
				Type:		String
				Example:	imdb=tt123456
				Values:		Any valid IMDb ID
			- tmdb:			Specify the TMDb ID.
				Required:	No
				Type:		String
				Example:	tmdb=123456
				Values:		Any valid TMDb ID
			- tvdb:			Specify the TVDb ID.
				Required:	No
				Type:		String
				Example:	tvdb=123456
				Values:		Any valid TVDb ID
			- title:		Specify a title instead of an ID.
				Required:	No
				Type:		String
				Example:	title=Some%20Title
				Values:		Any valid title
			- year:			Specify a year together with the title.
				Required:	No
				Type:		Integer
				Example:	year=2010
				Values:		Any valid year
			- season:		Specify the season number.
				Required:	Yes (shows), No (movies)
				Type:		Integer
				Example:	season=1
				Values:		Any valid season number
			- episode:		Specify the episode number.
				Required:	Yes (shows), No (movies)
				Type:		Integer
				Example:	episode=1
				Values:		Any valid episode number

		LOOKUP:

			- You can scrape by using a single or multiple IDs, by providing a title and year, or both.
			- Scraping by ID is always better, faster, and more reliable than scraping by title and year.
			- If IDs are provided, no title or year is required.
			- If a title is provided, a year is not required. However, a year will substantially improve the chances of picking
			  the correct title, especially if there are multiple movies/shows with the same title, but released in different years.

		IDS:

			The best way to scrape is by using an ID. You can pass in IDs from multiple providers and let Gaia figure out which
			one to use. The reliability and accuracy of IDs is as follows (from most reliable to least reliable):

			- Movies: Trakt, IMDb, TMDb, (TVDb)
			- Shows: Trakt, IMDb, TVDb, (TMDb)

			You should avoid searching movies by TVDb ID and shows by TMDb ID. Although it might work in some cases, most of the time
			nothing will be found. If you have IDs from multiple providers, just pass all of them in.

		EXAMPLES:

			- Play a movie link:
				plugin://plugin.video.gaia/?action=play&media=movie&imdb=tt1392190&tmdb=76341&trakt=56360&source=<JSON-encoded-source-dictionary>

	###################################################################################################################
'''

import xbmcaddon
developer = xbmcaddon.Addon().getAddonInfo('version') == '999.999.999'
if developer:
	import time as timer
	timeStart = timer.time()

from lib.modules import tools

parameters = tools.System.commandResolve(initialize = True)

action = parameters.get('action')

# For Gaia Eminence.
action = tools.System.redirect(parameters = parameters) or action

if developer: tools.Logger.log('EXECUTION STARTED [Action: %s]' % str(action))

# Prepare important things for every new Python process/invoker.
quick = tools.System.prepare(action = action, parameters = parameters)

if not quick:
	#gaiaremove - too much data passed via command-line. Maybe use a Stream ID as parameter. Then lookup the stream from streams.db or global var. Similar to how the metadata is handled now.
	source = parameters.get('source')
	if not source is None:
		source = tools.Converter.dictionary(source)
		if tools.Tools.isArray(source): source = source[0]

####################################################
# HOME
####################################################

if action is None or action == 'home':
	from lib.modules.menu import Menu
	Menu.instance().menu()

	# Reset the restart flag here, since an addon restart will end up in this function.
	tools.System.restartFinish()

	# Launch the donations dialog.
	# Only show if System.launchStatus(), since the donations dialog is also shown after the intial launch process and we do not want to show it twice.
	# Also call it here, for users who do not shut down their devices and keep it running for a long time.
	if tools.System.launchStatus() == 3: tools.Donations.popup(wait = True)

####################################################
# MENU
####################################################

elif action == 'menu':
	from lib.modules.menu import Menu
	Menu.instance().menu(**parameters)

elif action == 'search':
	from lib.modules.menu import Menu
	Menu.instance().menu(menu = Menu.MenuSearch, **parameters)

####################################################
# SCRAPE
####################################################

elif action.startswith('scrape'):

	if action == 'scrape':
		# Sometimes when using the Kore remote app and clicking on a movie/episode to start a scrape, the user might accidentally click twice, which starts the scraping process twice.
		# This is not a huge issue for other endpoints, but the scrape endpoint starts many threads and uses many resources, and should be avoided.
		# This is not a perfect solution, since both processes might call windowPropertyGet() before the other process is able to call windowPropertySet().
		# If the double scrape still happens in the future, we need a more advanced solution.
		# One way would be to rename this endpoint to “scrapeNow” and create another endpoint “scrape”.
		# “scrape” checks and sets the global property, and if not set, initiates the actual endpoint “scrapeNow” which clears the global property after scraping is done.
		# “scrapeNow” also checks the global property again, just as a second safety.
		# This would create a greater time gap between processes and would reduce the chance of both processes executing at the same time. However, it also requires two Python invokers, which slows down the starting of the scrape process.
		# Update: Hitting the ENTER key twice shortly after each other calls this endpoint twice, but in all cases only one scrape was done. So it seems to work.

		property = 'GaiaScrapeBusy'
		id = tools.System.windowPropertyGet(property)
		time = tools.Time.timestamp()

		# In case a previous scrape did not clear the property, allow a new scrape after 10 seconds.
		if not id or (time - int(id) > 10):
			try:
				tools.System.windowPropertySet(property, str(time))

				try: silent = bool(parameters.get('silent'))
				except: silent = False
				try: binge = int(parameters.get('binge'))
				except: binge = None

				from lib.modules import interface
				if not silent and not binge: interface.Loader.show()

				from lib.modules import core
				from lib.modules import video

				# Already show here, since getConstants can take long when retrieving debrid service list.
				if (not video.Trailer.cinemaEnabled() or tools.Settings.getBoolean('playback.autoplay.enabled')) and (not binge == tools.Binge.ModeBackground or binge == tools.Binge.ModeContinue): interface.Loader.show()

				media = parameters.get('media')

				imdb = parameters.get('imdb')
				tmdb = parameters.get('tmdb')
				tvdb = parameters.get('tvdb')
				trakt = parameters.get('trakt')

				title = parameters.get('title')
				tvshowtitle = parameters.get('tvshowtitle')

				year = parameters.get('year')
				tvshowyear = parameters.get('tvshowyear')
				premiered = parameters.get('premiered')

				season = parameters.get('season')
				episode = parameters.get('episode')
				number = parameters.get('number')

				autoplay = tools.Converter.boolean(parameters.get('autoplay'), none = True)
				autopack = parameters.get('autopack')
				preset = parameters.get('preset')
				cache = tools.Converter.boolean(parameters.get('cache'), none = True)
				items = parameters.get('items')

				# When called by TmdbHelper.
				if imdb == 'None': imdb = None
				if tmdb == 'None': tmdb = None
				if tvdb == 'None': tvdb = None
				if trakt == 'None': trakt = None
				if title == 'None': title = None
				if tvshowtitle == 'None': tvshowtitle = None
				if year == 'None': year = None
				if tvshowyear == 'None': tvshowyear = None
				if premiered == 'None': premiered = None
				if season == 'None': season = None
				if episode == 'None': episode = None

				if year: year = int(year)
				if tvshowyear: tvshowyear = int(tvshowyear)
				if not season is None: season = int(season)
				if not episode is None: episode = int(episode)

				core.Core(media = media, silent = silent).scrape(title = title, tvshowtitle = tvshowtitle, year = year, tvshowyear = tvshowyear, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number, premiered = premiered, autopack = autopack, autoplay = autoplay, preset = preset, binge = binge, cache = cache, items = items)
			except: tools.Logger.error()
			tools.System.windowPropertyClear(property)

	elif action == 'scrapeAgain':
		from lib.modules import core
		media = parameters.get('media')
		link = parameters.get('link')
		core.Core(media = media).scrapeAgain(link = link)

	elif action == 'scrapeManual':
		from lib.modules import core
		media = parameters.get('media')
		link = parameters.get('link')
		core.Core(media = media).scrapeManual(link = link)

	elif action == 'scrapeAutomatic':
		from lib.modules import core
		media = parameters.get('media')
		link = parameters.get('link')
		core.Core(media = media).scrapeAutomatic(link = link)

	elif action == 'scrapePresetManual':
		from lib.modules import core
		link = parameters.get('link')
		core.Core(media = media).scrapePresetManual(link = link)

	elif action == 'scrapePresetAutomatic':
		from lib.modules import core
		media = parameters.get('media')
		link = parameters.get('link')
		core.Core(media = media).scrapePresetAutomatic(link = link)

	elif action == 'scrapeSingle':
		from lib.modules import core
		media = parameters.get('media')
		link = parameters.get('link')
		core.Core(media = media).scrapeSingle(link = link)

	elif action == 'scrapeBinge':
		from lib.modules import core
		media = parameters.get('media')
		link = parameters.get('link')
		core.Core(media = media).scrapeBinge(link = link)

	elif action == 'scrapeExact':
		from lib.modules import core
		media = parameters.get('media')
		query = parameters.get('query')
		core.Core(media = media).scrapeExact(query)

	elif action == 'scrapeOptimize':
		from lib.providers.core.manager import Manager
		settings = tools.Converter.boolean(parameters.get('settings'))
		Manager.optimizeScrape(settings = settings)

####################################################
# STREAMS
####################################################

elif action.startswith('streams'):

	if action == 'streamsShow':
		from lib.modules import core
		from lib.modules import interface
		media = parameters.get('media')
		autoplay = tools.Converter.boolean(parameters.get('autoplay'))
		if autoplay: interface.Loader.show() # Only for autoplay, since showing the directory has its own loader.
		direct = tools.Converter.boolean(parameters.get('direct'))
		filter = tools.Converter.boolean(parameters.get('filterx'))
		library = tools.Converter.boolean(parameters.get('library'))
		initial = tools.Converter.boolean(parameters.get('initial'))
		new = tools.Converter.boolean(parameters.get('new'))
		add = tools.Converter.boolean(parameters.get('add'))
		process = tools.Converter.boolean(parameters.get('process'))
		try: binge = int(parameters.get('binge'))
		except: binge = None
		core.Core(media = media).showStreams(direct = direct, filter = filter, autoplay = autoplay, library = library, initial = initial, new = new, add = add, process = process, binge = binge)

	elif action == 'streamsFilters':
		from lib.modules.core import Core
		media = parameters.get('media')
		Core(media = media).filterStreams()

	elif action == 'streamsInformation':
		from lib.modules.stream import Stream
		Stream(data = source['stream']).dialog()

	elif action == 'streamsVideo':
		from lib.modules import video

		media = parameters.get('media')

		link = parameters.get('link')

		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')

		title = parameters.get('title')
		year = parameters.get('year')
		if year: year = int(year)
		season = parameters.get('season')
		if not season is None: season = int(season)

		mode = parameters.get('video')
		selection = parameters.get('selection')
		if not selection is None: selection = int(selection)

		getattr(video, mode.capitalize())(media = media).play(imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, link = link, selection = selection)


####################################################
# PLAY
####################################################

elif action.startswith('play') and not action.startswith('playback') and not action.startswith('playlist'):

	if action == 'play':
		if not tools.System.globalLocked(id = 'play'): # Check playcount.py for more details.
			from lib.modules.interface import Loader
			from lib.modules.core import Core
			Loader.show() # Immediately show the loader, since slow system will take long to show it in play().

			media = parameters.get('media')
			imdb = parameters.get('imdb')
			tmdb = parameters.get('tmdb')
			tvdb = parameters.get('tvdb')
			trakt = parameters.get('trakt')
			title = parameters.get('title')
			year = parameters.get('year')
			if year: year = int(year)
			season = parameters.get('season')
			if not season is None: season = int(season)
			episode = parameters.get('episode')
			if not episode is None: episode = int(episode)

			try: binge = int(parameters['binge'])
			except: binge = None
			try: resume = int(parameters['resume'])
			except: resume = None
			try: autoplay = tools.Converter.boolean(parameters['autoplay'])
			except: autoplay = False
			try: library = tools.Converter.boolean(parameters['library'])
			except: library = False
			try: new = tools.Converter.boolean(parameters['new'])
			except: new = False
			try: add = tools.Converter.boolean(parameters['add'])
			except: add = False
			try: reload = tools.Converter.boolean(parameters['reload'])
			except: reload = True
			downloadType = parameters.get('downloadType')
			downloadId = parameters.get('downloadId')
			handleMode = parameters.get('handleMode')

			Core(media = media).play(source = source, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, downloadType = downloadType, downloadId = downloadId, handleMode = handleMode, autoplay = autoplay, library = library, new = new, add = add, binge = binge, reload = reload, resume = resume)

	if action == 'playCache':
		from lib.modules.core import Core
		media = parameters.get('media')
		try: binge = int(parameters.get('binge'))
		except: binge = None
		try: reload = tools.Converter.boolean(parameters.get('reload'))
		except: reload = True
		handleMode = parameters.get('handleMode')
		Core(media = media).playCache(source = source, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, handleMode = handleMode, binge = binge, reload = reload)

	elif action == 'playLocal':
		from lib.modules.core import Core
		media = parameters.get('media')
		try: binge = int(parameters.get('binge'))
		except: binge = None
		path = parameters.get('path')
		downloadType = parameters.get('downloadType')
		downloadId = parameters.get('downloadId')
		Core(media = media).playLocal(path = path, source = source, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, downloadType = downloadType, downloadId = downloadId, binge = binge)

####################################################
# REFRESH
####################################################

elif action.startswith('refresh'):

	if action == 'refreshMenu':
		from lib.modules import interface
		interface.Loader.show()

		if tools.Converter.boolean(parameters.get('playback')):
			from lib.modules.playback import Playback
			media = parameters.get('media')
			Playback.instance().refresh(media = media, history = True, progress = True, rating = True, reload = False, wait = True)

		interface.Loader.hide() # Hide before, since Kodi will show its own laoder when refreshing the directory.

		container = parameters.get('container') # Refresh a specific container by ID. This does currently not work. Check Directory.refresh() for more info.
		interface.Directory.refresh(id = container)

	elif action == 'refreshMetadata':
		from lib.modules import interface
		interface.Loader.show()

		media = parameters.get('media')
		level = parameters.get('level')
		level = int(level) if level else 0
		notification = parameters.get('notification')

		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')

		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)

		from lib.meta.manager import MetaManager
		MetaManager.instance().metadataRefresh(level = level, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, notification = notification)

		interface.Loader.hide() # Hide before, since Kodi will show its own laoder when refreshing the directory.

		container = parameters.get('container') # Refresh a specific container by ID. This does currently not work. Check Directory.refresh() for more info.
		interface.Directory.refresh(id = container)

####################################################
# BINGE
####################################################

elif action.startswith('binge'):

	if action == 'binge':
		from lib.modules.core import Core
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		number = parameters.get('number')
		scrape = parameters.get('scrape')
		if scrape is None: scrape = True
		else: scrape = tools.Converter.boolean(scrape)
		Core(media = media).bingeStart(scrape = scrape, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, number = number)

####################################################
# SYSTEM
####################################################

elif action.startswith('system'):

	if action == 'systemInformation':
		tools.System.information()

	elif action == 'systemManager':
		tools.System.manager()

	elif action == 'systemPower':
		tools.System.power(action = None, level = 2)

	if action == 'systemBenchmark':
		from lib.modules.tester import Tester
		Tester.benchmarkDialog()

####################################################
# EXTERNAL
####################################################

elif action.startswith('external'):

	if action == 'externalImport':
		from lib.modules.external import Loader
		module = parameters.get('module')
		Loader.instance(module = module).moduleLoad()

####################################################
# COMPRESSION
####################################################

elif action.startswith('compression'):

	if action == 'compressionBenchmark':
		from lib.modules.compression import Compressor
		delay = parameters.get('delay')
		if delay: delay = int(delay) if tools.Tools.isNumeric(delay) else tools.Converter.boolean(delay)
		Compressor.benchmark(delay = delay, settings = True, background = False)

####################################################
# LOG
####################################################

elif action.startswith('log'):

	if action == 'log' or action == 'logKodi':
		tools.Logger.dialog()

	elif action == 'logScrape':
		tools.Logger.dialogScrape()

####################################################
# NFORMATION
####################################################

elif action.startswith('information'):

	if action == 'informationChangelog':
		tools.Changelog.show()

	elif action == 'informationDisclaimer':
		tools.Disclaimer.show(exit = True)

	elif action == 'informationAnnouncement':
		tools.Announcements.show(force = True)

	elif action == 'informationAttribution':
		from lib.modules.window import WindowAttribution
		WindowAttribution.show(progress = False)

	elif action == 'informationAbout':
		from lib.modules import interface
		interface.Splash.popupAbout()

####################################################
# PROMOTIONS
####################################################

elif action.startswith('promotions'):

	if action == 'promotions' or action == 'promotionsMenu':
		tools.Promotions.menu(force = tools.Converter.boolean(parameters.get('force')))

	elif action == 'promotionsSelect':
		tools.Promotions.select(provider = parameters.get('provider'))

####################################################
# PLAYLIST
####################################################

elif action.startswith('playlist'):

	if action == 'playlistShow':
		tools.Playlist.show()

	elif action == 'playlistClear':
		tools.Playlist.clear()

	elif action == 'playlistAdd':
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)

		label = parameters.get('label')
		link = parameters.get('link')
		context = parameters.get('context')

		tools.Playlist.add(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, link = link, label = label, context = context)

	elif action == 'playlistRemove':
		label = parameters.get('label')
		tools.Playlist.remove(label = label)

####################################################
# PLAYBACK
####################################################

elif action.startswith('playback'):

	if action == 'playbackWatch':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogWatch(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'playbackUnwatch':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogUnwatch(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'playbackRate':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogRate(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'playbackUnrate':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogUnrate(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'playbackRefresh':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		Playback.instance().dialogRefresh(media = media)

	elif action == 'playbackReset':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Playback.instance().dialogReset(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'playbackReload':
		from lib.modules.playback import Playback
		media = parameters.get('media')
		history = tools.Converter.boolean(parameters.get('history'))
		progress = tools.Converter.boolean(parameters.get('progress'))
		rating = tools.Converter.boolean(parameters.get('rating'))
		arrival = tools.Converter.boolean(parameters.get('arrival'))
		bulk = tools.Converter.boolean(parameters.get('bulk'))
		accelerate = tools.Converter.boolean(parameters.get('accelerate'))
		launch = tools.Converter.boolean(parameters.get('launch'))
		force = tools.Converter.boolean(parameters.get('force'))
		Playback.instance().reload(media = media, history = history, progress = progress, rating = rating, arrival = arrival, bulk = bulk, accelerate = accelerate, launch = launch, force = force, wait = True)

####################################################
# CLEANUP
####################################################

elif action.startswith('cleanup'):

	if action == 'cleanup':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Cleanup.clean(settings = settings)

####################################################
# ACCOUNTS
####################################################

elif action.startswith('accounts'):

	if action == 'accountsVerify':
		from lib.modules.account import Account
		Account.verifyDialog()

####################################################
# PROVIDERS
####################################################

elif action.startswith('providers'):

	if action == 'providersPresets':
		from lib.providers.core.manager import Manager
		settings = tools.Converter.boolean(parameters.get('settings'))
		Manager.presets(settings = settings)

	elif action == 'providersConfigure':
		from lib.modules.interface import Loader
		Loader.show() # Show here already for slow devices.
		from lib.providers.core.manager import Manager
		id = parameters.get('id')
		type = parameters.get('type')
		mode = parameters.get('mode')
		access = parameters.get('access')
		addon = parameters.get('addon')
		settings = tools.Converter.boolean(parameters.get('settings'))
		Manager.settings(id = id, type = type, mode = mode, access = access, addon = addon, settings = settings)

	elif action == 'providersVerify':
		from lib.providers.core.manager import Manager
		Manager.verify()

	elif action == 'providersOptimize':
		from lib.providers.core.manager import Manager
		settings = tools.Converter.boolean(parameters.get('settings'))
		Manager.optimizeProvider(settings = settings)

####################################################
# DOWNLOADS
####################################################

elif action.startswith('download'):

	if action == 'download':
		from lib.modules import interface
		try:
			interface.Loader.show()

			from lib.modules.core import Core
			from lib.modules.downloader import Downloader

			media = parameters.get('media')
			downloadType = parameters.get('downloadType')
			downloadId = parameters.get('downloadId')
			refresh = tools.Converter.boolean(parameters.get('refresh'))
			downer = Downloader(downloadType)
			if downloadId is None:
				handleMode = parameters.get('handleMode')
				link = Core(media = media).sourceResolve(source, info = True, internal = False, download = True, handleMode = handleMode)['link']
				if link is None:
					interface.Loader.hide()
				else:
					from lib.meta.manager import MetaManager
					from lib.meta.image import MetaImage

					imdb = parameters.get('imdb')
					tmdb = parameters.get('tmdb')
					tvdb = parameters.get('tvdb')
					trakt = parameters.get('trakt')
					season = parameters.get('season')
					if not season is None: season = int(season)
					episode = parameters.get('episode')
					if not episode is None: episode = int(episode)

					metadata = MetaManager.instance().metadata(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)
					if metadata:
						image = MetaImage.imagePoster(data = metadata)
						title = tools.Title.title(media = media, metadata = metadata)
						downer.download(media = Downloader.MediaShow if tools.Media.isSerie(media) else Downloader.MediaMovie if tools.Media.isFilm(media) else Downloader.MediaOther, title = title, link = link, image = image, metadata = metadata, source = tools.Converter.jsonTo(source), refresh = refresh)
			else:
				downer.download(id = downloadId, forceAction = True, refresh = refresh)
		except:
			interface.Loader.hide()
			tools.Logger.error()

	if action == 'downloadExecute':
		import sys
		from lib.modules.downloader import Downloader
		Downloader.execute(action = tools.System.arguments(3), type = tools.System.arguments(4), id = tools.System.arguments(5), observation = tools.System.arguments(6))

	elif action == 'downloadDetails':
		from lib.modules.downloader import Downloader
		downloadType = parameters.get('downloadType')
		downloadId = parameters.get('downloadId')
		Downloader(type = downloadType, id = downloadId).details()

	elif action == 'downloadsManager':
		from lib.modules.downloader import Downloader
		downloadType = parameters.get('downloadType')
		if downloadType is None: downloadType = Downloader.TypeManual
		downer = Downloader(type = downloadType)
		downer.items(status = Downloader.StatusAll, refresh = False)

	elif action == 'downloadsList':
		media = parameters.get('media')
		downloadType = parameters.get('downloadType')
		downloadStatus = parameters.get('downloadStatus')

		from lib.modules.downloader import Downloader
		downer = Downloader(downloadType)
		# Do not refresh the list using a thread. Seems like the thread is not always stopped and then it ends with multiple threads updating the list.
		# During the update duration multiple refreshes sometimes happen due to this. Hence, you will see the loader flash multiple times during the 10 secs.
		# Also, with a fresh the front progress dialog also flashes and reset it's focus.
		#downer.items(status = status, refresh = True)
		downer.items(status = downloadStatus, refresh = False)

	elif action == 'downloadsClear':
		media = parameters.get('media')
		downloadType = parameters.get('downloadType')
		downloadStatus = parameters.get('downloadStatus')

		from lib.modules.downloader import Downloader
		downer = Downloader(downloadType)
		downer.clear(status = downloadStatus)

	elif action == 'downloadsRefresh':
		from lib.modules.downloader import Downloader
		downloadType = parameters.get('downloadType')
		downer = Downloader(downloadType)
		downer.itemsRefresh()

	elif action == 'downloadsSettings':
		tools.Settings.launch(tools.Settings.CategoryDownload)

	elif action == 'downloadCloud':
		from lib.modules import core
		media = parameters.get('media')
		core.Core(media = media).sourceCloud(source)

####################################################
# SERVICE
####################################################

elif action.startswith('service'):

	if action == 'serviceKodi':
		from lib.modules.service import Service
		Service.launchKodi()

	elif action == 'serviceGaia':
		from lib.modules.service import Service
		Service.launchGaia()

####################################################
# ORACLE
####################################################

elif action.startswith('oracle'):

	if action == 'oracle':
		from lib.oracle import Oracle
		media = parameters.get('media')
		full = tools.Converter.boolean(parameters.get('full'))
		history = parameters.get('history')
		Oracle.execute(media = media, full = full, history = history)

	elif action == 'oracleMenu':
		from lib.oracle import Oracle
		service = parameters.get('service')
		data = parameters.get('data')
		loader = tools.Converter.boolean(parameters.get('loader'))
		Oracle.instance(service = service).menu(data = data, loader = loader)

	elif action == 'oracleAuthentication':
		from lib.oracle import Oracle
		service = parameters.get('service')
		settings = tools.Converter.boolean(parameters.get('settings'))
		Oracle.instance(service = service).settingsAuthenticationDialog(settings = settings)

	elif action == 'oraclePlayground':
		from lib.oracle import Oracle
		service = parameters.get('service')
		settings = tools.Converter.boolean(parameters.get('settings'))
		Oracle.instance(service = service).settingsPlaygroundDialog(settings = settings)

	elif action == 'oracleModel':
		from lib.oracle import Oracle
		service = parameters.get('service')
		settings = tools.Converter.boolean(parameters.get('settings'))
		Oracle.instance(service = service).settingsModelDialog(settings = settings)

	elif action == 'oracleQuery':
		from lib.oracle import Oracle
		service = parameters.get('service')
		settings = tools.Converter.boolean(parameters.get('settings'))
		Oracle.instance(service = service).settingsQueryDialog(settings = settings)

####################################################
# PREMIUMIZE
####################################################

elif action.startswith('premiumize'):

	if action == 'premiumizeAuthentication':
		from lib.debrid import premiumize
		settings = tools.Converter.boolean(parameters.get('settings'))
		premiumize.Interface().accountAuthentication(settings = settings)

	elif action == 'premiumizeList':
		from lib.debrid import premiumize
		premiumize.Interface().directoryList()

	elif action == 'premiumizeListAction':
		from lib.debrid import premiumize
		item = parameters.get('item')
		context = parameters.get('context')
		premiumize.Interface().directoryListAction(item, context)

	elif action == 'premiumizeItem':
		from lib.debrid import premiumize
		item = parameters.get('item')
		premiumize.Interface().directoryItem(item)

	elif action == 'premiumizeItemAction':
		from lib.debrid import premiumize
		item = parameters.get('item')
		premiumize.Interface().directoryItemAction(item)

	elif action == 'premiumizeAdd':
		from lib.debrid import premiumize
		premiumize.Interface().addManual()

	elif action == 'premiumizeInformation':
		from lib.debrid import premiumize
		premiumize.Interface().downloadInformation()

	elif action == 'premiumizeAccount':
		from lib.debrid import premiumize
		premiumize.Interface().account()

	elif action == 'premiumizeWebsite':
		from lib.debrid import premiumize
		premiumize.Core().website(open = True)

	elif action == 'premiumizeVpn':
		from lib.debrid import premiumize
		premiumize.Core().vpn(open = True)

	elif action == 'premiumizeClear':
		from lib.debrid import premiumize
		premiumize.Interface().clear()

	elif action == 'premiumizeSettings':
		tools.Settings.launch(id = 'premium.premiumize.enabled')

####################################################
# PREMIUMIZE
####################################################

elif action.startswith('offcloud'):

	if action == 'offcloudAuthentication':
		from lib.debrid import offcloud
		settings = tools.Converter.boolean(parameters.get('settings'))
		offcloud.Interface().accountAuthentication(settings = settings)

	elif action == 'offcloudList':
		from lib.debrid import offcloud
		category = parameters.get('category')
		offcloud.Interface().directoryList(category = category)

	elif action == 'offcloudListAction':
		from lib.debrid import offcloud
		item = parameters.get('item')
		context = parameters.get('context')
		offcloud.Interface().directoryListAction(item = item, context = context)

	elif action == 'poffcloudItem':
		from lib.debrid import offcloud
		item = parameters.get('item')
		offcloud.Interface().directoryItem(item)

	elif action == 'offcloudItemAction':
		from lib.debrid import offcloud
		item = parameters.get('item')
		offcloud.Interface().directoryItemAction(item)

	elif action == 'offcloudAdd':
		from lib.debrid import offcloud
		category = parameters.get('category')
		offcloud.Interface().addManual(category = category)

	elif action == 'offcloudInformation':
		from lib.debrid import offcloud
		category = parameters.get('category')
		offcloud.Interface().downloadInformation(category = category)

	elif action == 'offcloudAdd':
		from lib.debrid import offcloud
		offcloud.Interface().addManual()

	elif action == 'offcloudAccount':
		from lib.debrid import offcloud
		offcloud.Interface().account()

	elif action == 'offcloudWebsite':
		from lib.debrid import offcloud
		offcloud.Core().website(open = True)

	elif action == 'offcloudClear':
		from lib.debrid import offcloud
		category = parameters.get('category')
		offcloud.Interface().clear(category = category)

	elif action == 'offcloudSettings':
		tools.Settings.launch(id = 'premium.offcloud.enabled')

	elif action == 'offcloudSettingsLocation':
		from lib.debrid import offcloud
		offcloud.Interface().settingsLocation()

####################################################
# REALDEBRID
####################################################

elif action.startswith('realdebrid'):

	if action == 'realdebridAuthentication':
		from lib.debrid import realdebrid
		settings = tools.Converter.boolean(parameters.get('settings'))
		realdebrid.Interface().accountAuthentication(settings = settings)

	elif action == 'realdebridList':
		from lib.debrid import realdebrid
		realdebrid.Interface().directoryList()

	elif action == 'realdebridListAction':
		from lib.debrid import realdebrid
		item = parameters.get('item')
		realdebrid.Interface().directoryListAction(item)

	elif action == 'realdebridAdd':
		from lib.debrid import realdebrid
		realdebrid.Interface().addManual()

	elif action == 'realdebridInformation':
		from lib.debrid import realdebrid
		realdebrid.Interface().downloadInformation()

	elif action == 'realdebridAccount':
		from lib.debrid import realdebrid
		realdebrid.Interface().account()

	elif action == 'realdebridWebsite':
		from lib.debrid import realdebrid
		realdebrid.Core().website(open = True)

	elif action == 'realdebridClear':
		from lib.debrid import realdebrid
		realdebrid.Interface().clear()

	elif action == 'realdebridSettings':
		tools.Settings.launch(id = 'premium.realdebrid.enabled')

####################################################
# DEBRIDER
####################################################

elif action.startswith('debrider'):

	if action == 'debriderAuthentication':
		from lib.modules.account import Debrider
		help = tools.Converter.boolean(parameters.get('help'))
		settings = tools.Converter.boolean(parameters.get('settings'))
		Debrider().authenticate(help = help, settings = settings)

####################################################
# EASYDEBRID
####################################################

elif action.startswith('easydebrid'):

	if action == 'easydebridAuthentication':
		from lib.modules.account import Easydebrid
		help = tools.Converter.boolean(parameters.get('help'))
		settings = tools.Converter.boolean(parameters.get('settings'))
		Easydebrid().authenticate(help = help, settings = settings)

####################################################
# EASYNEWS
####################################################

elif action.startswith('easynews'):

	if action == 'easynewsAuthentication':
		from lib.debrid import easynews
		settings = tools.Converter.boolean(parameters.get('settings'))
		easynews.Interface().accountAuthentication(settings = settings)

	elif action == 'easynewsAccount':
		from lib.debrid import easynews
		easynews.Interface().account()

	elif action == 'easynewsWebsite':
		from lib.debrid import easynews
		easynews.Core().website(open = True)

	elif action == 'easynewsVpn':
		from lib.debrid import easynews
		easynews.Core().vpn(open = True)

	elif action == 'easynewsSettings':
		tools.Settings.launch(id = 'premium.easynews.enabled')

####################################################
# EMBY
####################################################

elif action.startswith('emby'):

	if action == 'embySettings':
		from lib.modules.center import Emby
		Emby().settings()

	elif action == 'embyWebsite':
		from lib.modules.center import Emby
		Emby().website(open = True)

####################################################
# JELLYFIN
####################################################

elif action.startswith('jellyfin'):

	if action == 'jellyfinSettings':
		from lib.modules.center import Jellyfin
		Jellyfin().settings()

	elif action == 'jellyfinWebsite':
		from lib.modules.center import Jellyfin
		Jellyfin().website(open = True)

####################################################
# ELEMENTUM
####################################################

elif action.startswith('elementum'):

	if action == 'elementumConnect':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Elementum.connect(install = False, settings = settings)

	elif action == 'elementumInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Elementum.connect(install = True, settings = settings)

	elif action == 'elementumLaunch':
		tools.Elementum.launch()

	elif action == 'elementumInterface':
		tools.Elementum.interface()

	elif action == 'elementumSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Elementum.settings(settings = settings)

####################################################
# QUASAR
####################################################

elif action.startswith('quasar'):

	if action == 'quasarConnect':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Quasar.connect(install = False, settings = settings)

	elif action == 'quasarInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Quasar.connect(install = True, settings = settings)

	elif action == 'quasarLaunch':
		tools.Quasar.launch()

	elif action == 'quasarInterface':
		tools.Quasar.interface()

	elif action == 'quasarSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Quasar.settings(settings = settings)

####################################################
# RESOLVER
####################################################

elif action.startswith('resolver'):

	if action == 'resolverAuthentication':
		type = parameters.get('type')
		help = tools.Converter.boolean(parameters.get('help'))
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Resolver.authentication(type = type, help = help, settings = settings)

	elif action == 'resolverInstall':
		help = tools.Converter.boolean(parameters.get('help'))
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Resolver.install(help = help, settings = settings)

	elif action == 'resolverSettings':
		universal = tools.Converter.boolean(parameters.get('universal'))
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Resolver.settings(universal = universal, settings = settings)

####################################################
# RESOLVEURL
####################################################

elif action.startswith('resolveurl'):

	if action == 'resolveurlSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.ResolveUrl.settings(settings = settings)

	elif action == 'resolveurlInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.ResolveUrl.enable(refresh = True, confirm = True, settings = settings)

	elif action == 'resolveurlAuthentication':
		type = parameters.get('type')
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.ResolveUrl.authentication(type = type, settings = settings)

####################################################
# URLRESOLVER
####################################################

elif action.startswith('urlresolver'):

	if action == 'urlresolverSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.UrlResolver.settings(settings = settings)

	elif action == 'urlresolverInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.UrlResolver.enable(refresh = True, confirm = True, settings = settings)

	elif action == 'urlresolverAuthentication':
		type = parameters.get('type')
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.UrlResolver.authentication(type = type, settings = settings)

####################################################
# OPESCRAPERS
####################################################

elif action.startswith('opescrapers'):

	if action == 'opescrapersSettings':
		tools.OpeScrapers.settings()

	elif action == 'opescrapersProviders':
		tools.OpeScrapers.providers()

	elif action == 'opescrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.OpeScrapers.enable(refresh = True, settings = settings)

####################################################
# FENSCRAPERS
####################################################

elif action.startswith('fenscrapers'):

	if action == 'fenscrapersSettings':
		tools.FenScrapers.settings()

	elif action == 'fenscrapersProviders':
		tools.FenScrapers.providers()

	elif action == 'fenscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.FenScrapers.enable(refresh = True, settings = settings)

####################################################
# OATSCRAPERS
####################################################

elif action.startswith('oatscrapers'):

	if action == 'oatscrapersSettings':
		tools.OatScrapers.settings()

	elif action == 'oatscrapersProviders':
		tools.OatScrapers.providers()

	elif action == 'oatscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.OatScrapers.enable(refresh = True, settings = settings)


####################################################
# CRESCRAPERS
####################################################

elif action.startswith('crescrapers'):

	if action == 'crescrapersSettings':
		tools.CreScrapers.settings()

	elif action == 'crescrapersProviders':
		tools.CreScrapers.providers()

	elif action == 'crescrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.CreScrapers.enable(refresh = True, settings = settings)

####################################################
# LAMSCRAPERS
####################################################

elif action.startswith('lamscrapers'):

	if action == 'lamscrapersSettings':
		tools.LamScrapers.settings()

	elif action == 'lamscrapersProviders':
		tools.LamScrapers.providers()

	elif action == 'lamscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.LamScrapers.enable(refresh = True, settings = settings)

####################################################
# CIVCRAPERS
####################################################

elif action.startswith('civscrapers'):

	if action == 'civscrapersSettings':
		tools.CivScrapers.settings()

	elif action == 'civscrapersProviders':
		tools.CivScrapers.providers()

	elif action == 'civscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.CivScrapers.enable(refresh = True, settings = settings)

####################################################
# GLOSCRAPERS
####################################################

elif action.startswith('gloscrapers'):

	if action == 'gloscrapersSettings':
		tools.GloScrapers.settings()

	elif action == 'gloscrapersProviders':
		tools.GloScrapers.providers()

	elif action == 'gloscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.GloScrapers.enable(refresh = True, settings = settings)

####################################################
# UNISCRAPERS
####################################################

elif action.startswith('uniscrapers'):

	if action == 'uniscrapersSettings':
		tools.UniScrapers.settings()

	elif action == 'uniscrapersProviders':
		tools.UniScrapers.providers()

	elif action == 'uniscrapersInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.UniScrapers.enable(refresh = True, settings = settings)

####################################################
# NANSCRAPERS
####################################################

elif action.startswith('nanscrapers'):

	if action == 'nanscrapersSettings':
		tools.NanScrapers.settings()

	elif action == 'nanscrapersProviders':
		tools.NanScrapers.providers()

	elif action == 'nanscrapersInstall':
		tools.NanScrapers.enable(refresh = True)

####################################################
# YOUTUBE
####################################################

elif action.startswith('youtube'):

	if action == 'youtubeAuthentication':
		from lib.modules import video
		settings = tools.Converter.boolean(parameters.get('settings'))
		video.Video.authentication(settings = settings)

	elif action == 'youtubeSettings':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.YouTube.settings(settings = settings)

	elif action == 'youtubeInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.YouTube.enable(settings = settings)

	elif action == 'youtubeQuality':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.YouTube.qualitySelect(settings = settings)

	elif action == 'youtubeLaunch':
		tools.YouTube.launch()

	elif action == 'youtubeWebsite':
		tools.YouTube.website(open = True)

####################################################
# UPNEXT
####################################################

elif action.startswith('upnext'):

	if action == 'upnextSettings':
		tools.UpNext.settings()

	elif action == 'upnextInstall':
		tools.UpNext.enable(refresh = True)

####################################################
# TMDBHELPER
####################################################

elif action.startswith('tmdbhelper'):

	if action == 'tmdbhelperLaunch':
		tools.TmdbHelper.launch()

	elif action == 'tmdbhelperSettings':
		tools.TmdbHelper.settings()

	elif action == 'tmdbhelperInstall':
		tools.TmdbHelper.enable(refresh = True, confirm = True)

	elif action == 'tmdbhelperIntegrate':
		tools.TmdbHelper.integrate()

####################################################
# VPNMANAGER
####################################################

elif action.startswith('vpnmanager'): # Make sure this is placed BEFORE the 'vpn' category.

	if action == 'vpnmanagerLaunch':
		tools.VpnManager.launch()

	elif action == 'vpnmanagerSettings':
		tools.VpnManager.settings()

	elif action == 'vpnmanagerInstall':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.VpnManager.enable(refresh = True, confirm = True, settings = settings)

####################################################
# BLUETOOTH
####################################################

elif action.startswith('bluetooth'):

	if action == 'bluetoothConnect':
		from lib.modules.bluetooth import Bluetooth
		Bluetooth.connect()

	elif action == 'bluetoothDisconnect':
		from lib.modules.bluetooth import Bluetooth
		Bluetooth.disconnect()

	elif action == 'bluetoothDialog':
		from lib.modules.bluetooth import Bluetooth
		settings = tools.Converter.boolean(parameters.get('settings'))
		Bluetooth.dialog(settings = settings)

####################################################
# SPEEDTEST
####################################################

elif action.startswith('speedtest'):

	if action == 'speedtest':
		from lib.modules import speedtest
		speedtest.SpeedTester.select(parameters.get('update'))

	elif action == 'speedtestGlobal':
		from lib.modules import speedtest
		speedtest.SpeedTesterGlobal().show(parameters.get('update'))

	elif action == 'speedtestPremiumize':
		from lib.modules import speedtest
		speedtest.SpeedTesterPremiumize().show(parameters.get('update'))

	elif action == 'speedtestOffCloud':
		from lib.modules import speedtest
		speedtest.SpeedTesterOffCloud().show(parameters.get('update'))

	elif action == 'speedtestRealDebrid':
		from lib.modules import speedtest
		speedtest.SpeedTesterRealDebrid().show(parameters.get('update'))

	elif action == 'speedtestEasyNews':
		from lib.modules import speedtest
		speedtest.SpeedTesterEasyNews().show(parameters.get('update'))

	elif action == 'speedtestComparison':
		from lib.modules import speedtest
		speedtest.SpeedTester.comparison()

####################################################
# LOTTERY
####################################################

elif action.startswith('lottery'):

	if action == 'lottery' or action == 'lotteryVoucher':
		from lib.modules import api
		api.Api.lotteryVoucher()

####################################################
# INFORMER
####################################################

elif action.startswith('informer'):

	if action == 'informerDialog':
		from lib.informers import Informer
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		title = parameters.get('title')
		year = parameters.get('year')
		if year: year = int(year)
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Informer.show(type = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, title = title, year = year, season = season, episode = episode)

	elif action == 'informerSettings':
		from lib.informers import Informer
		id = parameters.get('id')
		Informer.instance(id).settings()

	elif action == 'informerInstall':
		from lib.informers import Informer
		id = parameters.get('id')
		refresh = tools.Converter.boolean(parameters.get('refresh'))
		Informer.instance(id).enable(refresh = refresh)

	elif action == 'informerLaunch':
		from lib.informers import Informer
		id = parameters.get('id')
		Informer.instance(id).launch()

####################################################
# FANART
####################################################

elif action.startswith('fanart'):

	if action == 'fanartAuthentication':
		from lib.modules.account import Fanart
		settings = tools.Converter.boolean(parameters.get('settings'))
		Fanart().authenticate(settings = settings)

####################################################
# IMDB
####################################################

elif action.startswith('imdb'):

	if action == 'imdbAuthentication':
		from lib.modules.account import Imdb
		settings = tools.Converter.boolean(parameters.get('settings'))
		Imdb().authenticate(settings = settings)

####################################################
# TVDB
####################################################

elif action.startswith('tvdb'):

	if action == 'tvdbAuthentication':
		from lib.modules.account import Tvdb
		settings = tools.Converter.boolean(parameters.get('settings'))
		Tvdb().authenticate(settings = settings)

####################################################
# TMDB
####################################################

elif action.startswith('tmdb'):

	if action == 'tmdbAuthentication':
		from lib.modules.account import Tmdb
		settings = tools.Converter.boolean(parameters.get('settings'))
		Tmdb().authenticate(settings = settings)

####################################################
# TRAKT
####################################################

elif action.startswith('trakt'):

	if action == 'traktManager':
		from lib.modules import trakt as Trakt
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Trakt.manager(media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode)

	elif action == 'traktAuthentication':
		from lib.modules import trakt as Trakt
		settings = tools.Converter.boolean(parameters.get('settings'))
		Trakt.authentication(settings = settings)

	elif action == 'traktListAdd':
		from lib.modules import trakt as Trakt
		Trakt.listAdd()

####################################################
# OPENSUBTITLES
####################################################

elif action.startswith('opensubtitles'):

	if action == 'opensubtitlesAuthentication':
		from lib.modules.account import Opensubtitles
		settings = tools.Converter.boolean(parameters.get('settings'))
		Opensubtitles().authenticate(settings = settings)

####################################################
# NETWORK
####################################################

elif action.startswith('network'):

	if action == 'networkInformation':
		from lib.modules.network import Geolocator
		Geolocator.dialog()

	elif action == 'networkAuthentication':
		from lib.modules.account import Geolocation
		type = parameters.get('type')
		settings = tools.Converter.boolean(parameters.get('settings'))
		Geolocation(type = type).authenticate(settings = settings)

####################################################
# VPN
####################################################

elif action.startswith('vpn'):

	if action == 'vpnVerify':
		from lib.modules import vpn
		settings = tools.Converter.boolean(parameters.get('settings'))
		vpn.Vpn.verification(settings = settings)

	elif action == 'vpnConfigure':
		from lib.modules.vpn import Vpn
		settings = tools.Converter.boolean(parameters.get('settings'))
		Vpn.configuration(settings = settings)

	elif action == 'vpnSettings':
		external = tools.Converter.boolean(parameters.get('external'))
		if external:
			tools.VpnManager.settings()
		else:
			from lib.modules.vpn import Vpn
			Vpn.settingsLaunch()

	elif action == 'vpnChange':
		profile = parameters.get('profile')
		dialog = tools.Converter.boolean(parameters.get('dialog'))
		tools.VpnManager.change(profile = profile, dialog = dialog)

	elif action == 'vpnDisconnect':
		tools.VpnManager.disconnect()

	elif action == 'vpnStatus':
		tools.VpnManager.status()

####################################################
# EXTENSIONS
####################################################

elif action.startswith('extensions'):

	if action == 'extensions':
		id = parameters.get('id')
		tools.Extension.dialog(id = id)

	elif action == 'extensionsHelp':
		tools.Extension.help(full = True)

####################################################
# THEME
####################################################

elif action.startswith('theme'):

	if action == 'themeSkinSelect':
		from lib.modules.theme import Theme
		Theme.skinSettings()

	elif action == 'themeIconSelect':
		from lib.modules import interface
		interface.Icon.settings()

####################################################
# BACKUP
####################################################

elif action.startswith('backup'):

	if action == 'backup' or action == 'backupAutomatic':
		tools.Backup.automatic()

	elif action == 'backupImport':
		tools.Backup.manualImport()

	elif action == 'backupExport':
		tools.Backup.manualExport()

####################################################
# SETTINGS
####################################################

elif action.startswith('settings'):

	if action == 'settings' or action == 'settingsAdvanced':
		id = parameters.get('id')
		tools.Settings.launch(id = id)

	elif action == 'settingsWizard':
		from lib.modules.window import WindowWizard
		type = parameters.get('type')
		WindowWizard.launch(type = type)

	elif action == 'settingsOptimization':
		from lib.providers.core.manager import Manager
		Manager.optimizeShow()

	elif action == 'settingsBackground':
		id = parameters.get('id')
		addon = parameters.get('addon')
		category = parameters.get('category')
		tools.Settings.launch(id = id, addon = addon, category = category, background = False)

	elif action == 'settingsExternal':
		tools.Settings.externalSave(parameters)

	elif action == 'settingsLanguage':
		id = parameters.get('id')
		title = parameters.get('title')
		if title:
			try: title = int(title)
			except: pass
		none = tools.Converter.boolean(parameters.get('none'))
		automatic = tools.Converter.boolean(parameters.get('automatic'))
		set = parameters.get('set')
		tools.Language.settingsSelect(id = id, title = title, none = none, automatic = automatic, set = set)

	elif action == 'settingsCountry':
		id = parameters.get('id')
		title = parameters.get('title')
		if title:
			try: title = int(title)
			except: pass
		none = tools.Converter.boolean(parameters.get('none'))
		automatic = tools.Converter.boolean(parameters.get('automatic'))
		frequency = tools.Converter.boolean(parameters.get('frequency'))
		tools.Country.settingsSelect(id = id, title = title, none = none, automatic = automatic, frequency = frequency)

	elif action == 'settingsLayout':
		from lib.modules.interface import Loader
		Loader.show() # Show here already for slow devices.
		from lib.modules.stream import Layout
		Layout().show(settings = True)

	elif action == 'settingsFilters':
		from lib.modules.interface import Loader
		Loader.show() # Show here already for slow devices.
		from lib.modules.stream import Settings
		mode = parameters.get('mode')
		Settings(mode = mode).show()

	elif action == 'settingsTermination':
		from lib.modules.interface import Loader
		Loader.show() # Show here already for slow devices.
		from lib.modules.stream import Termination
		settings = tools.Converter.boolean(parameters.get('settings'))
		Termination().show(settings = settings)

	elif action == 'settingsCustom':
		id = parameters.get('id')
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Settings.custom(id = id, settings = settings)

	elif action == 'settingsBuffer':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Buffer.settings(settings = settings)

	elif action == 'settingsTimeout':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Timeout.settings(settings = settings)

	elif action == 'settingsPlaylist':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Playlist.settings(settings = settings)

	elif action == 'settingsView':
		from lib.modules.view import View
		media = parameters.get('media')
		content = parameters.get('content')
		previous = parameters.get('previous')
		settings = tools.Converter.boolean(parameters.get('settings'))
		View.settings(media = media, content = content, previous = previous, settings = settings)

	elif action == 'settingsImage':
		from lib.meta.image import MetaImage
		mode = parameters.get('mode')
		media = parameters.get('media')
		settings = tools.Converter.boolean(parameters.get('settings'))
		MetaImage.settingsSelect(mode = mode, media = media, settings = settings)

	elif action == 'settingsIcon':
		from lib.modules.interface import Font
		settings = tools.Converter.boolean(parameters.get('settings'))
		Font.iconSettings(settings = settings)

	elif action == 'settingsCompany':
		from lib.meta.company import MetaCompany
		settings = tools.Converter.boolean(parameters.get('settings'))
		MetaCompany.settingsSelect(settings = settings)

	elif action == 'settingsInterpreter':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Settings.interpreterSelect(settings = settings)

	elif action == 'settingsDatabase':
		from lib.modules.database import Database
		settings = tools.Converter.boolean(parameters.get('settings'))
		Database.cleanSettings(settings = settings)

	elif action == 'settingsObserver':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Observer.settingsUpdate(settings = settings)

	elif action == 'settingsSound':
		settings = tools.Converter.boolean(parameters.get('settings'))
		tools.Sound.settingsUpdate(settings = settings)

	elif action == 'settingsEnvironment':
		from lib.modules.environment import Environment
		settings = tools.Converter.boolean(parameters.get('settings'))
		Environment.test(settings = settings)

	elif action == 'settingsDetailMediaMenu':
		from lib.modules.interface import Detail
		settings = tools.Converter.boolean(parameters.get('settings'))
		Detail.settingsMediaMenuUpdate(settings = settings)

	elif action == 'settingsDetailMediaFormat':
		from lib.modules.interface import Detail
		settings = tools.Converter.boolean(parameters.get('settings'))
		Detail.settingsMediaFormatUpdate(settings = settings)

	elif action == 'settingsDetailActivityMenu':
		from lib.modules.interface import Detail
		settings = tools.Converter.boolean(parameters.get('settings'))
		Detail.settingsActivityMenuUpdate(settings = settings)

	elif action == 'settingsDetailActivityFormat':
		from lib.modules.interface import Detail
		settings = tools.Converter.boolean(parameters.get('settings'))
		Detail.settingsActivityFormatUpdate(settings = settings)

	elif action == 'settingsDetailActivityPlay':
		from lib.modules.interface import Detail
		settings = tools.Converter.boolean(parameters.get('settings'))
		Detail.settingsActivityPlayUpdate(settings = settings)

	elif action == 'settingsDetailActivityProgress':
		from lib.modules.interface import Detail
		settings = tools.Converter.boolean(parameters.get('settings'))
		Detail.settingsActivityProgressUpdate(settings = settings)

	elif action == 'settingsDetailActivityRating':
		from lib.modules.interface import Detail
		settings = tools.Converter.boolean(parameters.get('settings'))
		Detail.settingsActivityRatingUpdate(settings = settings)

	elif action == 'settingsDetailActivityAir':
		from lib.modules.interface import Detail
		settings = tools.Converter.boolean(parameters.get('settings'))
		Detail.settingsActivityAirUpdate(settings = settings)

####################################################
# DONATIONS
####################################################

elif action.startswith('donations'):

	if action == 'donations':
		from lib.modules import tools
		type = parameters.get('type')
		tools.Donations.show(type = type)

####################################################
# SHORTCUT
####################################################

elif action.startswith('shortcut'):

	if action == 'shortcutShow':
		id = parameters.get('id')
		label = parameters.get('label')
		command = parameters.get('command')
		folder = tools.Converter.boolean(parameters.get('folder'))
		create = tools.Converter.boolean(parameters.get('create'))
		delete = tools.Converter.boolean(parameters.get('delete'))
		Shortcut.instance().show(id = id, label = label, command = command, folder = folder, create = create, delete = delete)

	elif action == 'shortcutOpen':
		id = parameters.get('id')
		Shortcut.instance().open(id = id)

####################################################
# LIBRARY
####################################################

elif action.startswith('library'):

	if action == 'libraryAdd':
		from lib.modules.library import Library
		precheck = tools.Converter.boolean(parameters.get('precheck'))
		link = parameters.get('link')
		media = parameters.get('media')
		imdb = parameters.get('imdb')
		tmdb = parameters.get('tmdb')
		tvdb = parameters.get('tvdb')
		trakt = parameters.get('trakt')
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Library(media = media).add(link = link, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, precheck = precheck)

	elif action == 'libraryResolve':
		from lib.modules.library import Library
		media = parameters.get('media')
		title = parameters.get('title')
		if title: title = tools.Converter.quoteFrom(title)
		year = parameters.get('year')
		if year: year = int(year)
		season = parameters.get('season')
		if not season is None: season = int(season)
		episode = parameters.get('episode')
		if not episode is None: episode = int(episode)
		Library(media = media).resolve(title = title, year = year, season = season, episode = episode)

	elif action == 'libraryRefresh':
		from lib.modules.library import Library
		media = parameters.get('media')
		Library(media = media).refresh()

	elif action == 'libraryUpdate':
		from lib.modules.library import Library
		media = parameters.get('media')
		force = tools.Converter.boolean(parameters.get('force'))
		Library.update(force = force, media = media)

	elif action == 'libraryClean':
		from lib.modules.library import Library
		media = parameters.get('media')
		Library(media = media).clean()

	elif action == 'libraryLocal':
		from lib.modules.library import Library
		media = parameters.get('media')
		Library(media = media).local()

	elif action == 'librarySettings':
		from lib.modules.library import Library
		Library.settings()

####################################################
# SUPPORT
####################################################

elif action.startswith('support'):

	if action == 'supportMenu':
		from lib.modules import support
		support.Support.menu()

	elif action == 'supportBugs':
		from lib.modules import support
		support.Support.bugs()

	elif action == 'supportCategories':
		from lib.modules import support
		support.Support.categories()

	elif action == 'supportReport':
		from lib.modules import support
		support.Support.report()

	elif action == 'supportQuestions':
		from lib.modules import support
		support.Support.questions(int(parameters.get('id')))

	elif action == 'supportQuestion':
		from lib.modules import support
		support.Support.question(int(parameters.get('id')))

####################################################
# ORION
####################################################

elif action.startswith('orion'):

	if action == 'orionInitialize':
		try:
			from lib.modules import orionoid
			settings = parameters.get('settings')
			if settings and not '.' in settings: settings = tools.Converter.boolean(settings)
			debrid = tools.Converter.boolean(parameters.get('debrid'))
			orionoid.Orionoid().initialize(settings = settings, debrid = debrid)
		except: pass

	elif action == 'orionSettings':
		try:
			from lib.modules import orionoid
			id = parameters.get('id')
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid.addonSettings(id = id, settings = settings)
		except: pass

	elif action == 'orionFilters':
		try:
			from lib.modules import orionoid
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid().settingsFilters(settings = settings)
		except: pass

	elif action == 'orionLaunch':
		try:
			from lib.modules import orionoid
			orionoid.Orionoid().addonLaunch()
		except: pass

	elif action == 'orionInstall':
		try:
			from lib.modules import orionoid
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid.addonEnable(refresh = True, settings = settings)
		except: pass

	elif action == 'orionUninstall':
		try:
			from lib.modules import orionoid
			orionoid.Orionoid.uninstall()
		except: pass

	elif action == 'orionWebsite':
		try:
			from lib.modules import orionoid
			orionoid.Orionoid().addonWebsite(open = True)
		except: pass

	elif action == 'orionAuthenticate':
		try:
			from lib.modules import orionoid
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid().accountAuthenticate(settings = settings)
		except: pass

	elif action == 'orionDebrid':
		try:
			from lib.modules import orionoid
			type = parameters.get('type')
			help = tools.Converter.boolean(parameters.get('help'))
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid().debridAuthenticate(type = type, help = help, settings = settings)
		except: pass

	elif action == 'orionAccount':
		try:
			from lib.modules import orionoid
			orionoid.Orionoid().accountDialog()
		except: pass

	elif action == 'orionPromotion':
		try:
			from lib.modules import orionoid
			settings = tools.Converter.boolean(parameters.get('settings'))
			orionoid.Orionoid().accountPromotion(settings = settings)
		except: pass

	elif action == 'orionVoteUp':
		try:
			from lib.modules import orionoid
			notification = tools.Converter.boolean(parameters.get('notification'), none = True)
			orionoid.Orionoid().streamVote(idItem = parameters.get('idItem'), idStream = parameters.get('idStream'), vote = orionoid.Orionoid.VoteUp, automatic = False, notification = True if notification is None else notification)
		except: pass

	elif action == 'orionVoteDown':
		try:
			from lib.modules import orionoid
			notification = tools.Converter.boolean(parameters.get('notification'), none = True)
			orionoid.Orionoid().streamVote(idItem = parameters.get('idItem'), idStream = parameters.get('idStream'), vote = orionoid.Orionoid.VoteDown, automatic = False, notification = True if notification is None else notification)
		except: pass

	elif action == 'orionRemove':
		try:
			from lib.modules import orionoid
			notification = tools.Converter.boolean(parameters.get('notification'), none = True)
			orionoid.Orionoid().streamRemove(idItem = parameters.get('idItem'), idStream = parameters.get('idStream'), automatic = False, notification = True if notification is None else notification)
		except: pass

####################################################
# CONTEXT
####################################################

elif action.startswith('context'):

	if action == 'contextShow':
		from lib.modules.interface import Loader
		Loader.show() # It can take some time to open the context menu on the first use after starting Gaia.
		from lib.modules.interface import Context
		menu = Context()
		menu.dataFrom(parameters.get('context'))
		menu.show()

####################################################
# QR
####################################################

elif action.startswith('qr'):

	if action == 'qr':
		try:
			from lib.modules.interface import Loader
			Loader.show() # Needs some time to load. Show busy.

			media = parameters.get('media')
			if media:
				imdb = parameters.get('imdb')
				tmdb = parameters.get('tmdb')
				tvdb = parameters.get('tvdb')
				trakt = parameters.get('trakt')
				season = parameters.get('season')
				if not season is None: season = int(season)
				episode = parameters.get('episode')
				if not episode is None: episode = int(episode)
				type = parameters.get('type')
				search = parameters.get('search', True)
				test = parameters.get('test', True)
				fallback = parameters.get('fallback', True)
				tools.Link.qr(type = type, media = media, imdb = imdb, tmdb = tmdb, tvdb = tvdb, trakt = trakt, season = season, episode = episode, search = search, test = test, fallback = fallback, loader = True)
			else:
				link = parameters.get('link')
				name = parameters.get('name')
				hash = parameters.get('hash')
				code = parameters.get('code')
				wallet = parameters.get('wallet')
				payment = parameters.get('payment')
				symbol = parameters.get('symbol')

				from lib.modules.window import WindowQr
				WindowQr.show(link = link, name = name, hash = hash, code = code, wallet = wallet, payment = payment, symbol = symbol)
		except: tools.Logger.error()

####################################################
# FILE
####################################################

elif action.startswith('file'):

	if action == 'fileLink':
		from lib.modules.interface import Loader
		try:
			Loader.show() # Needs some time to load. Show busy.
			from lib.modules.network import Networker, Resolver
			from lib.modules.window import WindowQr

			mode = parameters.get('mode')
			if not mode: mode = 'original'

			if 'link' in parameters:
				link = parameters.get('link')
			elif source:
				from lib.modules.stream import Stream
				stream = Stream.load(data = source['stream'])
				if mode == 'original':
					link = stream.linkPrimary()
				elif mode == 'resolved':
					link = stream.linkProvider()
					if not link: link = Resolver.resolve(source = source, clean = True, internal = False, cloud = False, mode = Resolver.ModeProvider)
				elif mode == 'stream':
					link = stream.linkStream()
					if not link:
						link = Resolver.resolve(source = source, clean = True, internal = False, cloud = False, mode = Resolver.ModeService)
						if not link: link = Stream.load(data = source['stream']).linkResolved() # Provider-resolved link added by Resolver.resolve() and therefore reload.
				if not link: link = stream.linkPrimary() # Sometimes resolving does not work. Eg: 404 errors.

			link = Networker.linkClean(link)
			WindowQr.show(link = link)
		except: tools.Logger.error()

	elif action == 'fileName':
		from lib.modules.interface import Loader
		try:
			Loader.show() # Needs some time to load. Show busy.
			from lib.modules.stream import Stream
			from lib.modules.window import WindowQr
			if 'name' in parameters: name = parameters.get('name')
			elif source: name = Stream.load(data = source['stream']).stream.fileName()
			WindowQr.show(name = name)
		except: tools.Logger.error()

	elif action == 'fileHash':
		from lib.modules.interface import Loader
		try:
			Loader.show() # Needs some time to load. Show busy.
			from lib.modules.stream import Stream
			from lib.modules.window import WindowQr
			if 'hash' in parameters: hash = parameters.get('hash')
			elif source: hash = Stream.load(data = source['stream']).stream.hash()
			WindowQr.show(hash = hash)
		except: tools.Logger.error()

	elif action == 'fileAdd':
		from lib.modules.interface import Loader
		Loader.show()
		from lib.modules.core import Core
		media = parameters.get('media')
		link = parameters.get('link')
		metadata = parameters.get('metadata')
		if metadata: metadata = tools.Converter.dictionary(metadata)
		Core(media = media).addLink(link = link, metadata = metadata)

####################################################
# CLOUDFLARE
####################################################

elif action.startswith('cloudflare'):

	if action == 'cloudflareEngine':
		from lib.modules.cloudflare import Cloudflare
		settings = tools.Converter.boolean(parameters.get('settings'))
		Cloudflare.settingsEngine(settings = settings)

	elif action == 'cloudflareVerify':
		from lib.modules.cloudflare import Cloudflare
		settings = tools.Converter.boolean(parameters.get('settings'))
		Cloudflare().verify(settings = settings, notification = True)

####################################################
# METADATA
####################################################

elif action.startswith('metadata'):

	if action == 'metadataSettings':
		tools.Settings.launch(tools.Settings.CategoryMetadata)

	elif action == 'metadataDetail':
		from lib.meta.tools import MetaTools
		settings = tools.Converter.boolean(parameters.get('settings'))
		MetaTools.settingsDetailShow(settings = settings)

	elif action == 'metadataBulk':
		settings = tools.Converter.boolean(parameters.get('settings'))
		if settings:
			from lib.meta.providers.imdb import MetaImdb
			MetaImdb.bulkSettingsShow(settings = settings)
		else:
			from lib.meta.manager import MetaManager
			selection = tools.Converter.boolean(parameters.get('selection'), none = True)
			MetaManager.instance().bulkImdbRefresh(selection = selection, force = True, refresh = True, silent = False, wait = True)

	elif action == 'metadataExternal':
		from lib.meta.tools import MetaTools
		settings = tools.Converter.boolean(parameters.get('settings'))
		MetaTools.settingsExternalShow(settings = settings)

	elif action == 'metadataPreload':
		from lib.meta.tools import MetaTools
		clean = tools.Converter.boolean(parameters.get('clean'), none = True) # If not provided, ask the user if the cache should be cleaned.
		settings = tools.Converter.boolean(parameters.get('settings'))
		MetaTools.settingsPreloadShow(clean = clean, settings = settings)

	elif action == 'metadataGenerate':
		from lib.meta.manager import MetaManager
		MetaManager.generate()

####################################################
# SOUND
####################################################

elif action.startswith('sound'):

	if action == 'soundPlay':
		mode = parameters.get('mode')
		time = parameters.get('time')
		delay = tools.Converter.boolean(parameters.get('delay'), none = True)
		tools.Sound.execute(mode = mode, time = time, delay = delay)

####################################################
# DUMMY
####################################################

elif action.startswith('dummy'):

	if action == 'dummy':
		tools.System.pluginResolvedSet(success = False)

####################################################
# DEBUG
####################################################

elif action.startswith('debug'):

	if action == 'debug':
		from lib.modules.tester import Tester
		Tester.test()

####################################################
# DEVELOPER
####################################################

elif action.startswith('developer'):

	if action == 'developer':

		from lib.meta.manager import MetaManager
		from lib.meta.cache import MetaCache
		from lib.meta.tools import MetaTools
		from lib.meta.pack import MetaPack
		from lib.meta.image import MetaImage

		from lib.meta.provider import MetaProvider
		from lib.meta.providers.trakt import MetaTrakt
		from lib.meta.providers.tmdb import MetaTmdb
		from lib.meta.providers.tvdb import MetaTvdb
		from lib.meta.providers.imdb import MetaImdb
		from lib.meta.providers.fanart import MetaFanart

		from lib.modules.tester import Tester
		from lib.modules.stream import Stream
		from lib.modules.playback import Playback
		from lib.modules.cache import Cache, Memory
		from lib.modules.clipboard import Clipboard

		# TESTER

		Tester.test()

		# STREAM

		'''
		metaMedia = tools.Media.Show
		metaNiche = []
		metaTitle = 'xxx'
		metaYear = 2005
		metaSeason = 1
		metaEpisode = 1
		metaPack = metaPack
		metaCountry = ['us']
		metaLanguage = ['en']
		metaNetwork = ['amc']
		metaStudio = []
		fileName = 'xxx'

		stream = Stream.load(fileName = fileName, metaMedia = metaMedia, metaNiche = metaNiche, metaTitle = metaTitle, metaYear = metaYear, metaSeason = metaSeason, metaEpisode = metaEpisode, metaPack = metaPack, metaCountry = metaCountry, metaLanguage = metaLanguage, metaNetwork = metaNetwork, metaStudio = metaStudio)
		tools.Logger.log("Stream Info: " + str(stream))

		number = Stream.numberShowExtract(data = fileName)
		tools.Logger.log("Stream Number: " + str(number))
		'''

		# PACK

		'''packTrakt = None
		packTmdb = None
		packTvdb = None
		packImdb = None

		# One Piece
		packTrakt = MetaTrakt.instance().metadataPack(imdb = 'tt0388629', cache = True)
		packTmdb = MetaTmdb.instance().metadataPack(id = '37854', cache = True)
		packTvdb = MetaTvdb.instance().metadataPack(id ='81797', cache = True)
		packImdb = MetaImdb.instance().metadataPack(id = 'tt0388629')

		pack = MetaPack()
		data = pack.generateShow(trakt = packTrakt, tmdb = packTmdb, tvdb = packTvdb, imdb = packImdb, check = MetaPack.CheckForeground)
		#Clipboard.copy(tools.Converter.jsonTo(data))

		#tools.Logger.log("Episode Info: "+str(pack.episode(season = 1, episode = 2, number = MetaPack.NumberSequential)))
		'''


####################################################
# EXECUTION
####################################################

if developer: tools.Logger.log('EXECUTION FINISHING [Action: %s | Duration: %.3f secs]' % (action, timer.time() - timeStart))

try:
	from lib.modules.vpn import Vpn
	Vpn.killStop()

	# Process all Trakt requests that were stored in the cache, since they could not be executed previously due to trakt being down.
	# Do not call this function after each Trakt request, since it will start too many threads.
	# Check trakt.cacheRetry() for more information.
	from lib.modules import trakt
	trakt.cacheRetry(force = False, probability = True, wait = True)

	from lib.modules.concurrency import Pool
	Pool.join()

	# Reset global variables in case the invoker is reused.
	tools.Settings.interpreterReset()
except: tools.Logger.error()

if developer: tools.Logger.log('EXECUTION FINISHED [Action: %s | Duration: %.3f secs]' % (action, timer.time() - timeStart))
