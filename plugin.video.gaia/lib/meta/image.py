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

from lib.modules.tools import Media, Regex, Tools, Settings, Language, Logger
from lib.modules.network import Networker
from lib.modules.theme import Theme
from lib.modules.concurrency import Lock

class MetaImage(object):

	Attribute						= 'image'
	AttributeLink					= 'link'
	AttributeProvider				= 'provider'
	AttributeLanguage				= 'language'
	AttributeTheme					= 'theme'
	AttributeSort					= 'sort'

	ModeStyle						= 'style'
	ModeSelection					= 'selection'

	OptionLimit						= 'limit'
	OptionMedia						= 'media'
	OptionIndex						= 'index'
	OptionType						= 'type'
	OptionProvider					= 'provider'
	OptionSort						= 'sort'
	OptionOrder						= 'order'
	OptionChoice					= 'choice'
	OptionDecor						= 'decor'
	OptionLanguage					= 'language'
	Options							= {ModeStyle : [OptionProvider, OptionSort, OptionOrder, OptionDecor, OptionLanguage], ModeSelection : [OptionMedia, OptionIndex, OptionType, OptionChoice]}

	SelectionGeneral				= 'general'
	SelectionPreference				= 'preference'
	SelectionFallback				= 'fallback'
	Selections						= [SelectionPreference, SelectionFallback]

	ChoiceRandom					= 'random'
	ChoicePrimary					= 'primary'
	ChoiceSecondary					= 'secondary'
	ChoiceTertiary					= 'tertiary'
	ChoiceQuaternary				= 'quaternary'
	ChoiceQuinary					= 'quinary'
	ChoiceDefault					= ChoicePrimary
	Choices							= [ChoicePrimary, ChoiceSecondary, ChoiceTertiary, ChoiceQuaternary, ChoiceQuinary] # Order is important for fallbacks.

	CustomSmart						= 'smart'				# Smart menus.
	CustomBase						= 'base'				# Interface and windows (loading, scraping, streams, rating, and binge dialogs).
	CustomPlayer					= 'player'				# Kodi player and Kore app.

	MediaMovie						= Media.Movie
	MediaSet						= Media.Set
	MediaShow						= Media.Show
	MediaSeason						= Media.Season
	MediaEpisode					= Media.Episode
	MediaRecap						= Media.Recap
	MediaExtra						= Media.Extra
	MediaSeasonx					= MediaSeason + 'x'		# Special season (S0).
	MediaEpisodex					= MediaEpisode + 'x'	# Special episode (SxE0).
	MediaSmart						= CustomSmart
	MediaBase						= CustomBase
	MediaPlayer						= CustomPlayer
	Medias							= {ModeStyle : [MediaMovie, MediaSet, MediaShow, MediaSeason, MediaEpisode], ModeSelection : [MediaMovie, MediaSet, MediaShow, MediaSeason, MediaEpisode, MediaSeasonx, MediaEpisodex, MediaRecap, MediaExtra, MediaSmart, MediaBase, MediaPlayer]}

	TypePoster						= 'poster'
	TypeThumb						= 'thumb'
	TypeFanart						= 'fanart'
	TypeLandscape					= 'landscape'
	TypeBanner						= 'banner'
	TypeClearlogo					= 'clearlogo'
	TypeClearart					= 'clearart'
	TypeDiscart						= 'discart'
	TypeKeyart						= 'keyart'
	TypePhoto						= 'photo' # Used internally for actor/character photos.
	TypeIcon						= 'icon' # Not listed under Kodi artwork wiki, but listed under the Python ListItem docs.
	Types							= [TypePoster, TypeThumb, TypeFanart, TypeLandscape, TypeBanner, TypeClearlogo, TypeClearart, TypeDiscart, TypeKeyart]
	TypesAlternative				= {TypePoster : TypeThumb, TypeThumb : TypeFanart, TypeFanart : TypeLandscape, TypeLandscape : TypeFanart, TypeBanner : TypeFanart, TypeClearlogo : TypeClearart, TypeClearart : TypeClearlogo, TypeDiscart : TypeKeyart, TypeKeyart : TypeDiscart}
	TypesPreference					= {
										# These were used previously.
										# The show images were used in most cases, which had more consistency when navigating through the show, season, and episode menus (eg: all used the show fanart).
										# But this is not great for anthology shows (eg: White Lotus) where the seasons and episodes should rather use the season fanart.

										# Test this with:
										#	1. The Big Bang Theory
										#	2. One Piece (Anime)
										#	3. White Lotus
										#	4. That '70s show
										#	5. Game of Thrones
										#	6. House
										#	7. The Righteous Gemstones
										#	8. True Detective

										#MediaSeason : {TypeFanart : MediaShow, TypeLandscape : MediaShow},
										#MediaEpisode : {TypeFanart : MediaShow, TypeLandscape : MediaShow},
										#MediaSeasonx : {TypeFanart : MediaShow, TypeLandscape : MediaShow},
										#MediaEpisodex : {TypeFanart : MediaShow, TypeLandscape : MediaShow},
										#MediaRecap : {TypeFanart : MediaShow, TypeLandscape : MediaShow},
										#MediaExtra : {TypeFanart : MediaShow, TypeLandscape : MediaShow},
										#MediaSmart : {TypePoster : MediaShow, TypeThumb : MediaShow, TypeFanart : MediaShow, TypeLandscape : MediaShow, TypeBanner : MediaShow, TypeClearlogo : MediaShow, TypeClearart : MediaShow, TypeDiscart : MediaShow, TypeKeyart : MediaShow},

										MediaSeason : {
											# Use the show fanart, so that the entire season menu uses the same consistent background.
											TypeFanart : MediaShow,
											TypeLandscape : MediaShow,
										},
										MediaEpisode : {
											# Episodes probably never have posters.
											TypePoster : MediaSeason,

											TypeFanart : MediaSeason,
											TypeLandscape : MediaSeason,

											TypeBanner : MediaSeason,

											# Episodes probably never have logos. Use the season logo which probably also does not exist, or the show logo as fallback.
											TypeClearlogo : MediaSeason,

											TypeClearart : MediaSeason,
											TypeDiscart : MediaSeason,
											TypeKeyart : MediaSeason,
										},
										MediaSeasonx : {
											TypeFanart : MediaShow,
											TypeLandscape : MediaShow,
										},
										MediaEpisodex : {
											# Episodes probably never have posters.
											TypePoster : MediaSeason,

											# For consistency with episode images.
											TypeFanart : MediaSeason,
											TypeLandscape : MediaSeason,
											TypeBanner : MediaSeason,
											TypeClearlogo : MediaSeason,
											TypeClearart : MediaSeason,
											TypeDiscart : MediaSeason,
											TypeKeyart : MediaSeason,
										},
										MediaRecap : {
											# Many shows do not have season thumbnails/landscape, or only have for some seasons.
											# Use the season landscape with text to specifically indicate that it is recaps/extras, in contrast to the episode thumbnails which do not have text.
											# We could use the season fanart instead, which will be more consitency with the episode none-text thumbnails, and there will be more consitency with all recaps/extras which are way more likley to have fanart.
											TypeThumb : MediaSeason,

											# For consistency with episode images.
											TypePoster : MediaSeason,
											TypeFanart : MediaSeason,
											TypeLandscape : MediaSeason,
											TypeBanner : MediaSeason,
											TypeClearlogo : MediaSeason,
											TypeClearart : MediaSeason,
											TypeDiscart : MediaSeason,
											TypeKeyart : MediaSeason,
										},
										MediaExtra : {
											# Many shows do not have season thumbnails/landscape, or only have for some seasons.
											TypeThumb : MediaSeason,

											# For consistency with episode images.
											TypePoster : MediaSeason,
											TypeFanart : MediaSeason,
											TypeLandscape : MediaSeason,
											TypeBanner : MediaSeason,
											TypeClearlogo : MediaSeason,
											TypeClearart : MediaSeason,
											TypeDiscart : MediaSeason,
											TypeKeyart : MediaSeason,
										},
										MediaSmart : {
											# Use the season fanart for anthology series (eg: White Lotus).
											# Still use the show posters, since season posters look too cluttered for these menus.
											TypeFanart : MediaSeason,
											TypeLandscape : MediaSeason,

											TypePoster : MediaShow,
											TypeThumb : MediaShow,
											TypeBanner : MediaShow,
											TypeClearlogo : MediaShow,
											TypeClearart : MediaShow,
											TypeDiscart : MediaShow,
											TypeKeyart : MediaShow,
										},
										MediaBase : {
											TypePoster : MediaShow,
											TypeKeyart : MediaShow,

											TypeThumb : MediaSeason,
											TypeFanart : MediaSeason,
											TypeLandscape : MediaSeason,
											TypeBanner : MediaSeason,
											TypeClearlogo : MediaSeason,
											TypeClearart : MediaSeason,
											TypeDiscart : MediaSeason,
										},
										MediaPlayer : {
											TypePoster : MediaShow,
											TypeKeyart : MediaShow,

											TypeThumb : MediaSeason,
											TypeFanart : MediaSeason,
											TypeLandscape : MediaSeason,
											TypeBanner : MediaSeason,
											TypeClearlogo : MediaSeason,
											TypeClearart : MediaSeason,
											TypeDiscart : MediaSeason,
										},
									}
	TypesFallback					= {
										#MediaSeason : {TypePoster : {OptionMedia : MediaShow, OptionType : TypePoster}},
										#MediaEpisode : {TypePoster : {OptionMedia : MediaShow, OptionType : TypePoster}},
										#MediaSeasonx : {TypePoster : {OptionMedia : MediaShow, OptionType : TypePoster}},
										#MediaEpisodex : {TypePoster : {OptionMedia : MediaShow, OptionType : TypePoster}, TypeThumb : {OptionMedia : MediaSeason, OptionType : TypeLandscape}},
										#MediaRecap : {TypePoster : {OptionMedia : MediaShow, OptionType : TypePoster}, TypeThumb : {OptionMedia : MediaSeason, OptionType : TypeLandscape}},
										#MediaExtra : {TypePoster : {OptionMedia : MediaShow, OptionType : TypePoster}, TypeThumb : {OptionMedia : MediaSeason, OptionType : TypeLandscape}},

										MediaSeason : {
											# Use the quaternary poster for future/unreleased seasons.
											# Since the Series menu uses the primary poster, the Absolute menu the secondary poster, and the Specials menu the tertiary image.
											TypePoster		: {OptionMedia : MediaShow,		OptionType : TypePoster,	OptionChoice : ChoiceQuaternary},

											# Rather use the landscape instead of the fanart, since both the season thumbnail and landscape contain text.
											TypeThumb		: {OptionMedia : MediaSeason,	OptionType : TypeLandscape},

											# Uses the show fanart by default.
											TypeFanart		: {OptionMedia : MediaSeason,	OptionType : TypeFanart},

											# Uses the show landscape by default.
											TypeLandscape	: {OptionMedia : MediaSeason,	OptionType : TypeLandscape},

											# Rather use the show banner, instead of another season image, to have the same aspect ratio for the image.
											TypeBanner		: {OptionMedia : MediaShow,		OptionType : TypeBanner,	OptionChoice : ChoiceSecondary},

											# Not sure if any skin has a logo-based season view.
											# Use the show logo as fallback, since pretty much all seasons do not have their own logo.
											TypeClearlogo	: {OptionMedia : MediaShow,		OptionType : TypeClearlogo},

											# Rather use the show images, instead of another season image.
											TypeClearart	: {OptionMedia : MediaShow,		OptionType : TypeClearart,	OptionChoice : ChoiceSecondary},
											TypeDiscart		: {OptionMedia : MediaShow,		OptionType : TypeDiscart,	OptionChoice : ChoiceSecondary},
											TypeKeyart		: {OptionMedia : MediaShow,		OptionType : TypeKeyart,	OptionChoice : ChoiceSecondary},
										},
										MediaEpisode : {
											TypePoster		: {OptionMedia : MediaShow,		OptionType : TypePoster,	OptionChoice : ChoiceSecondary},

											# If available, use a different fanart to the one used as background.
											TypeThumb		: {OptionMedia : MediaSeason,	OptionType : TypeFanart,	OptionChoice : ChoiceSecondary},

											# Use the show fanart (without text) instead of the season landscape (with text) which looks ugly.
											# Use the secondary fanart to create deviation between the season menu fanart and the episode menu fanart.
											# If there is no secondary fanart, it will default to the primary fanart.
											# Eg: The Righteous Gemstones S01 + S04
											# Eg: GoT S08
											TypeFanart		: {OptionMedia : MediaShow,		OptionType : TypeFanart,	OptionChoice : ChoiceSecondary},
											TypeLandscape	: {OptionMedia : MediaShow,		OptionType : TypeLandscape,	OptionChoice : ChoiceSecondary},

											TypeBanner		: {OptionMedia : MediaShow,		OptionType : TypeBanner,	OptionChoice : ChoiceSecondary},

											# Season logos are mostly not available.
											TypeClearlogo	: {OptionMedia : MediaShow,		OptionType : TypeClearlogo},

											# Rather use the show images, instead of another episode image.
											TypeClearart	: {OptionMedia : MediaShow,		OptionType : TypeClearart,	OptionChoice : ChoiceSecondary},
											TypeDiscart		: {OptionMedia : MediaShow,		OptionType : TypeDiscart,	OptionChoice : ChoiceSecondary},
											TypeKeyart		: {OptionMedia : MediaShow,		OptionType : TypeKeyart,	OptionChoice : ChoiceSecondary},
										},
										MediaSeasonx : {
											# Use the tertiary image to create some diversity.
											# The Absolute menu uses the ChoiceSecondary poster.
											TypePoster		: {OptionMedia : MediaShow,		OptionType : TypePoster,	OptionChoice : ChoiceTertiary},

											TypeThumb		: {OptionMedia : MediaSeason,	OptionType : TypeLandscape},
											TypeFanart		: {OptionMedia : MediaSeason,	OptionType : TypeFanart},
											TypeLandscape	: {OptionMedia : MediaSeason,	OptionType : TypeLandscape},
											TypeBanner		: {OptionMedia : MediaShow,		OptionType : TypeBanner,	OptionChoice : ChoiceTertiary},
											TypeClearlogo	: {OptionMedia : MediaShow,		OptionType : TypeClearlogo},
											TypeClearart	: {OptionMedia : MediaShow,		OptionType : TypeClearart,	OptionChoice : ChoiceTertiary},
											TypeDiscart		: {OptionMedia : MediaShow,		OptionType : TypeDiscart,	OptionChoice : ChoiceTertiary},
											TypeKeyart		: {OptionMedia : MediaShow,		OptionType : TypeKeyart,	OptionChoice : ChoiceTertiary},
										},
										MediaEpisodex : {
											TypePoster		: {OptionMedia : MediaShow,		OptionType : TypePoster,	OptionChoice : ChoiceTertiary},
											TypeThumb		: {OptionMedia : MediaShow,		OptionType : TypeFanart,	OptionChoice : ChoiceSecondary},

											# Use the show fanart (without text) instead of the season landscape (with text) which looks ugly.
											# Use the tertiary fanart to create deviation between the season menu fanart and the episode menu fanart.
											TypeFanart		: {OptionMedia : MediaShow,		OptionType : TypeFanart,	OptionChoice : ChoiceTertiary},
											TypeLandscape	: {OptionMedia : MediaShow,		OptionType : TypeLandscape,	OptionChoice : ChoiceTertiary},

											TypeBanner		: {OptionMedia : MediaShow,		OptionType : TypeBanner,	OptionChoice : ChoiceTertiary},

											# For consistency with episode logos.
											TypeClearlogo	: {OptionMedia : MediaShow,		OptionType : TypeClearlogo},

											# Rather use the show images, instead of another episode image.
											TypeClearart	: {OptionMedia : MediaShow,		OptionType : TypeClearart,	OptionChoice : ChoiceTertiary},
											TypeDiscart		: {OptionMedia : MediaShow,		OptionType : TypeDiscart,	OptionChoice : ChoiceTertiary},
											TypeKeyart		: {OptionMedia : MediaShow,		OptionType : TypeKeyart,	OptionChoice : ChoiceTertiary},
										},
										MediaRecap : {
											TypePoster		: {OptionMedia : MediaShow,		OptionType : TypePoster,	OptionChoice : ChoiceSecondary},

											# Rather use the landscape instead of the fanart, since both the season thumbnail and landscape contain text.
											# We could use the show thumbnail instead, which contains text and looks better than plain fanart (eg: The Righteous Gemstones).
											# But this might show incorrect characters for anthology series (eg: True Detective).
											TypeThumb		: {OptionMedia : MediaSeason,	OptionType : TypeLandscape},

											# Use the show fanart (without text) instead of the season landscape (with text) which looks ugly.
											# Use the secondary fanart to ensure consistency in the episode menu, since the episode fallback uses secondary fanart.
											TypeFanart		: {OptionMedia : MediaShow,		OptionType : TypeFanart,	OptionChoice : ChoiceSecondary},
											TypeLandscape	: {OptionMedia : MediaShow,		OptionType : TypeLandscape,	OptionChoice : ChoiceSecondary},

											TypeBanner		: {OptionMedia : MediaShow,		OptionType : TypeBanner,	OptionChoice : ChoiceSecondary},

											# Season logos are mostly not available.
											TypeClearlogo	: {OptionMedia : MediaShow,		OptionType : TypeClearlogo},

											# Rather use the show images, instead of another episode image.
											TypeClearart	: {OptionMedia : MediaShow,		OptionType : TypeClearart,	OptionChoice : ChoiceSecondary},
											TypeDiscart		: {OptionMedia : MediaShow,		OptionType : TypeDiscart,	OptionChoice : ChoiceSecondary},
											TypeKeyart		: {OptionMedia : MediaShow,		OptionType : TypeKeyart,	OptionChoice : ChoiceSecondary},
										},
										MediaExtra : {
											TypePoster		: {OptionMedia : MediaShow,		OptionType : TypePoster,	OptionChoice : ChoiceSecondary},

											# Rather use the landscape instead of the fanart, since both the season thumbnail and landscape contain text.
											# We could use the show thumbnail instead, which contains text and looks better than plain fanart (eg: The Righteous Gemstones).
											# But this might show incorrect characters for anthology series (eg: True Detective).
											TypeThumb		: {OptionMedia : MediaSeason,	OptionType : TypeLandscape},

											# Use the show fanart (without text) instead of the season landscape (with text) which looks ugly.
											# Use the secondary fanart to ensure consistency in the episode menu, since the episode fallback uses secondary fanart.
											TypeFanart		: {OptionMedia : MediaShow,		OptionType : TypeFanart,	OptionChoice : ChoiceSecondary},
											TypeLandscape 	: {OptionMedia : MediaShow,		OptionType : TypeLandscape,	OptionChoice : ChoiceSecondary},

											TypeBanner		: {OptionMedia : MediaShow,		OptionType : TypeBanner,	OptionChoice : ChoiceSecondary},

											# Season logos are mostly not available.
											TypeClearlogo	: {OptionMedia : MediaShow,		OptionType : TypeClearlogo},

											# Rather use the show images, instead of another episode image.
											TypeClearart	: {OptionMedia : MediaShow,		OptionType : TypeClearart,	OptionChoice : ChoiceSecondary},
											TypeDiscart		: {OptionMedia : MediaShow,		OptionType : TypeDiscart,	OptionChoice : ChoiceSecondary},
											TypeKeyart		: {OptionMedia : MediaShow,		OptionType : TypeKeyart,	OptionChoice : ChoiceSecondary},
										},
										MediaSmart : {
											# If the season fanart is not available, use the show fanart, otherwise the season landscape is used.
											TypeFanart		: {OptionMedia : MediaShow,		OptionType : TypeFanart},
											TypeLandscape	: {OptionMedia : MediaShow,		OptionType : TypeLandscape},

											TypePoster		: {OptionMedia : MediaSeason,	OptionType : TypePoster},
											TypeThumb		: {OptionMedia : MediaSeason,	OptionType : TypeThumb},
											TypeBanner		: {OptionMedia : MediaSeason,	OptionType : TypeBanner},
											TypeClearlogo	: {OptionMedia : MediaSeason,	OptionType : TypeClearlogo},
											TypeClearart	: {OptionMedia : MediaSeason,	OptionType : TypeClearart},
											TypeDiscart		: {OptionMedia : MediaSeason,	OptionType : TypeDiscart},
											TypeKeyart		: {OptionMedia : MediaSeason,	OptionType : TypeKeyart},
										},
										MediaBase : {
											TypePoster		: {OptionMedia : MediaSeason,	OptionType : TypePoster},
											TypeKeyart		: {OptionMedia : MediaSeason,	OptionType : TypeKeyart},

											TypeFanart		: {OptionMedia : MediaShow,		OptionType : TypeFanart},
											TypeLandscape	: {OptionMedia : MediaShow,		OptionType : TypeLandscape},
											TypeThumb		: {OptionMedia : MediaShow,		OptionType : TypeThumb},
											TypeBanner		: {OptionMedia : MediaShow,		OptionType : TypeBanner},
											TypeClearlogo	: {OptionMedia : MediaShow,		OptionType : TypeClearlogo},
											TypeClearart	: {OptionMedia : MediaShow,		OptionType : TypeClearart},
											TypeDiscart		: {OptionMedia : MediaShow,		OptionType : TypeDiscart},
										},
										MediaPlayer : {
											TypePoster		: {OptionMedia : MediaSeason,	OptionType : TypePoster},
											TypeKeyart		: {OptionMedia : MediaSeason,	OptionType : TypeKeyart},

											TypeFanart		: {OptionMedia : MediaShow,		OptionType : TypeFanart},
											TypeLandscape	: {OptionMedia : MediaShow,		OptionType : TypeLandscape},
											TypeThumb		: {OptionMedia : MediaShow,		OptionType : TypeThumb},
											TypeBanner		: {OptionMedia : MediaShow,		OptionType : TypeBanner},
											TypeClearlogo	: {OptionMedia : MediaShow,		OptionType : TypeClearlogo},
											TypeClearart	: {OptionMedia : MediaShow,		OptionType : TypeClearart},
											TypeDiscart		: {OptionMedia : MediaShow,		OptionType : TypeDiscart},
										},
									}
	TypesRecover					= {
										TypePoster : [TypeKeyart, TypeThumb, TypeLandscape, TypeFanart, TypeBanner, TypeClearart, TypeClearlogo, TypeDiscart],
										TypeThumb : [TypeKeyart, TypeThumb, TypeLandscape, TypeFanart, TypeBanner, TypeClearart, TypeClearlogo, TypeDiscart],
										TypeFanart : [TypeLandscape, TypeThumb, TypeKeyart, TypePoster, TypeBanner, TypeClearart, TypeClearlogo, TypeDiscart],
										TypeLandscape : [TypeFanart, TypeThumb, TypeKeyart, TypePoster, TypeBanner, TypeClearart, TypeClearlogo, TypeDiscart],
										TypeBanner : [TypeFanart, TypeLandscape, TypeKeyart, TypePoster, TypeThumb, TypeClearart, TypeClearlogo, TypeDiscart],
										TypeClearlogo : [TypeClearart],
										TypeClearart : [TypeClearlogo],
										TypeKeyart : [TypePoster, TypeThumb, TypeFanart, TypeLandscape, TypeBanner, TypeClearart, TypeClearlogo, TypeDiscart],
									}

	ProviderImdb					= 'imdb'
	ProviderTmdb					= 'tmdb'
	ProviderTvdb					= 'tvdb'
	ProviderTrakt					= 'trakt'
	ProviderFanart					= 'fanart'
	ProviderTvmaze					= 'tvmaze'
	Providers						= [ProviderTmdb, ProviderTvdb, ProviderFanart, ProviderTrakt, ProviderImdb, ProviderTvmaze]
	ProvidersDefault				= {MediaMovie : ProviderTmdb, MediaSet : ProviderTmdb, MediaShow : ProviderTvdb, MediaSeason : ProviderTvdb, MediaEpisode : ProviderTvdb}

	# Should correspond with Metadata.Sort values.
	SortNone						= 'none'
	SortIndex						= 'index'
	SortId							= 'id'
	SortVote						= 'vote'
	SortVoteIndex					= 'voteindex'
	SortVoteId						= 'voteid'
	SortVoteOrigin					= 'voteorigin'
	SortVoteOriginIndex				= 'voteoriginindex'
	SortVoteOriginId				= 'voteoriginid'
	SortOrigin						= 'origin'
	SortOriginIndex					= 'originindex'
	SortOriginId					= 'originid'
	SortOriginVote					= 'originvote'
	SortOriginVoteIndex				= 'originvoteindex'
	SortOriginVoteId				= 'originvoteid'
	SortIgnore						= 'ignore'		# Internal. Used by MetaTvdb to indicate to rather use Fanart/TMDb images, instead of TVDb images.
	SortLanguage					= 'language'	# Internal.
	SortTheme						= 'theme'		# Internal.
	SortsDefault					= {ProviderTmdb : SortIndex, ProviderTvdb : SortVote, ProviderFanart : SortVote, ProviderTrakt : SortIndex}

	# Do not call them Ascending/Descending, since that is not necessarily the order.
	# Vote/Origin are from highest to lowest (where highest is the best), whereas index/ID are from lowest to highest (where lowest is the best).
	# Use Forward/Reversed as labels for users in order not to confuse them, but still use the ascending/descending string values, since they are passed to metadata.py.
	OrderForward					= 'descending'
	OrderReversed					= 'ascending'
	OrderDefault					= OrderForward

	DecorAny						= 'any'
	DecorPlain						= 'plain'
	DecorEmbell						= 'embell'
	DecorsDefault					= {TypeThumb : DecorPlain, TypeFanart : DecorPlain, TypeKeyart : DecorPlain, TypePoster : DecorEmbell, TypeLandscape : DecorEmbell, TypeBanner : DecorEmbell, TypeClearlogo : DecorEmbell, TypeClearart : DecorEmbell, TypeDiscart : DecorEmbell}

	IndexCurrent					= 'current'
	IndexPrevious					= 'previous'
	IndexNext						= 'next'
	IndexDefault					= IndexCurrent

	# Previously the recap used the fanart from the previous season, which was not noticeable, since all episodes/recaps/extras used the show fanart.
	# Now that episode menus use the season fanart, this causes a visual disruption when flipping through the menu.
	# Use the current season's fanart to ensure consistency when navigating through the episode menus.
	#IndexesDefault					= {MediaRecap : IndexPrevious, MediaExtra : IndexCurrent}
	IndexesDefault					= {
										MediaRecap : {
											None : IndexCurrent,
											TypePoster : IndexPrevious,
											TypeKeyart : IndexPrevious,
											TypeThumb : IndexPrevious,
										},
										MediaExtra : IndexCurrent,
									}

	LimitAutomatic					= 'automatic'
	LimitUnlimited					= 'unlimited'
	LimitSingle						= 'single'
	LimitDouble						= 'double'
	LimitTriple						= 'triple'
	LimitQuadruple					= 'quadruple'
	LimitQuintuple					= 'quintuple'
	LimitDefault					= LimitAutomatic
	Limits							= {LimitAutomatic : None, LimitUnlimited : 0, LimitSingle : 1, LimitDouble : 2, LimitTriple : 3, LimitQuadruple : 4, LimitQuintuple : 5}

	PrefixNone						= ''
	PrefixShow						= 'tvshow.'
	PrefixSeason					= 'season.'
	PrefixPrevious					= 'previous.'
	PrefixNext						= 'next.'
	PrefixsMedia					= {MediaShow : PrefixShow, MediaSeason : PrefixSeason}
	PrefixsIndex					= {IndexCurrent : PrefixNone, IndexPrevious : PrefixPrevious, IndexNext : PrefixNext}

	NumberPrimary					= ''
	NumberSecondary					= '1'
	NumberTertiary					= '2'
	NumberQuaternary				= '3'
	NumberQuinary					= '4'
	Numbers							= [NumberPrimary, NumberSecondary, NumberTertiary, NumberQuaternary, NumberQuinary]
	NumbersChoice					= {ChoicePrimary : NumberPrimary, ChoiceSecondary : NumberSecondary, ChoiceTertiary : NumberTertiary, ChoiceQuaternary : NumberQuaternary, ChoiceQuinary : NumberQuinary}

	Invalid							= '0'

	SettingsLimit					= 'image.general.limit'
	SettingsLanguage				= 'image.region.language'

	SettingsStyleMovie				= 'image.style.movie'
	SettingsStyleSet				= 'image.style.set'
	SettingsStyleShow				= 'image.style.show'
	SettingsStyleSeason				= 'image.style.season'
	SettingsStyleEpisode			= 'image.style.episode'
	SettingsStyle					= {MediaMovie : SettingsStyleMovie, MediaSet : SettingsStyleSet, MediaShow : SettingsStyleShow, MediaSeason : SettingsStyleSeason, MediaEpisode : SettingsStyleEpisode}

	SettingsSelectionMovie			= 'image.selection.movie'
	SettingsSelectionSet			= 'image.selection.set'
	SettingsSelectionShow			= 'image.selection.show'
	SettingsSelectionSeason			= 'image.selection.season'
	SettingsSelectionEpisode		= 'image.selection.episode'
	SettingsSpecialSeason			= 'image.special.season'
	SettingsSpecialEpisode			= 'image.special.episode'
	SettingsSpecialRecap			= 'image.special.recap'
	SettingsSpecialExtra			= 'image.special.extra'
	SettingsSelectionSmart			= 'image.other.smart'
	SettingsSelectionBase			= 'image.other.base'
	SettingsSelectionPlayer			= 'image.other.player'
	SettingsSelection				= {MediaMovie : SettingsSelectionMovie, MediaSet : SettingsSelectionSet, MediaShow : SettingsSelectionShow, MediaSeason : SettingsSelectionSeason, MediaEpisode : SettingsSelectionEpisode, MediaSeasonx : SettingsSpecialSeason, MediaEpisodex : SettingsSpecialEpisode, MediaRecap : SettingsSpecialRecap, MediaExtra : SettingsSpecialExtra, MediaSmart : SettingsSelectionSmart, MediaBase : SettingsSelectionBase, MediaPlayer : SettingsSelectionPlayer}

	SettingsData					= {}
	SettingsDefault					= {}
	SettingsLock					= Lock()

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings:
			MetaImage.SettingsData = {}

	###################################################################
	# SETTINGS
	###################################################################

	@classmethod
	def settings(self, mode, media, type = None):
		if not media: media = MetaImage.MediaMovie # For exact searches.
		if not mode in MetaImage.SettingsData or not media in MetaImage.SettingsData[mode]:
			MetaImage.SettingsLock.acquire()
			if not mode in MetaImage.SettingsData or not media in MetaImage.SettingsData[mode]:
				if not mode in MetaImage.SettingsData: MetaImage.SettingsData[mode] = {}

				if mode == MetaImage.ModeStyle: id = MetaImage.SettingsStyle[media]
				elif mode == MetaImage.ModeSelection: id = MetaImage.SettingsSelection[media]

				settings = Settings.getData(id)
				if not settings: settings = self.settingsDefault(mode = mode, media = media, copy = True, lock = False)
				if mode == MetaImage.ModeStyle:
					language = self.settingsLanguage()
					for key, val in settings.items():
						if val[MetaImage.OptionLanguage] == Language.CodeAutomatic: settings[key][MetaImage.OptionLanguage] = language
				elif mode == MetaImage.ModeSelection:
					# Reset the Index attribute if the media is not season.
					# In case the index was changed, and later the media was changed from season to show.
					for key, val in settings.items():
						for selection in MetaImage.Selections:
							if not val[selection][MetaImage.OptionMedia] == MetaImage.MediaSeason: settings[key][selection][MetaImage.OptionIndex] = MetaImage.IndexCurrent

				MetaImage.SettingsData[mode][media] = settings

			MetaImage.SettingsLock.release()
		if type is None: return MetaImage.SettingsData[mode][media]
		else: return MetaImage.SettingsData[mode][media][type]

	@classmethod
	def settingsLanguage(self, media = None, type = None):
		if media and type: return self.settingsStyle(media = media, type = type)[MetaImage.OptionLanguage]
		else: return Language.settingsCustom(id = MetaImage.SettingsLanguage)

	@classmethod
	def settingsLimit(self):
		return Settings.getInteger(id = MetaImage.SettingsLimit)

	@classmethod
	def settingsInternal(self):
		# All settings that require the metacache to be cleared to get the new values.
		data = {}
		for media in [MetaImage.MediaMovie, MetaImage.MediaSet, MetaImage.MediaShow, MetaImage.MediaSeason, MetaImage.MediaEpisode]:
			data[media] = self.settings(mode = MetaImage.ModeStyle, media = media)
		return data

	@classmethod
	def settingsStyle(self, media, type):
		return self.settings(mode = MetaImage.ModeStyle, media = media, type = type)

	@classmethod
	def settingsStyleSort(self, media, type, default = True):
		settings = self.settingsStyle(media = media, type = type)
		sort = settings[MetaImage.OptionSort]
		if sort is None and default:
			provider = settings[MetaImage.OptionProvider]
			if not provider: provider = MetaImage.ProvidersDefault[media]
			sort = MetaImage.SortsDefault[provider]
		if sort == MetaImage.SortNone: sort = None
		return sort

	@classmethod
	def settingsStyleOrder(self, media, type, default = True):
		order = self.settingsStyle(media = media, type = type)[MetaImage.OptionOrder]
		if order is None and default: order = MetaImage.OrderDefault
		return order

	@classmethod
	def settingsSelection(self, media, type):
		return self.settings(mode = MetaImage.ModeSelection, media = media, type = type)

	@classmethod
	def settingsFallback(self, media, fallback):
		if media == MetaImage.MediaSeason: id = MetaImage.SettingsSelectionSeason
		elif media == MetaImage.MediaEpisode: id = MetaImage.SettingsSelectionEpisode
		elif media == MetaImage.MediaSeasonx: id = MetaImage.SettingsSpecialSeason
		elif media == MetaImage.MediaEpisodex: id = MetaImage.SettingsSpecialEpisode
		elif media == MetaImage.MediaSmart: id = MetaImage.SettingsSelectionSmart
		elif media == MetaImage.MediaBase: id = MetaImage.SettingsSelectionBase
		elif media == MetaImage.MediaPlayer: id = MetaImage.SettingsSelectionPlayer
		else: return False
		return Settings.getBoolean(id = id + '.' + fallback)

	@classmethod
	def settingsDefault(self, mode = None, media = None, type = None, copy = False, lock = True):
		if not mode in MetaImage.SettingsDefault:
			if lock: MetaImage.SettingsLock.acquire()
			if not mode in MetaImage.SettingsDefault:
				result = {}
				medias = MetaImage.Medias[mode]

				if mode == MetaImage.ModeSelection:
					for i in medias:
						result[i] = {}
						for j in MetaImage.Types:
							result[i][j] = {
								MetaImage.SelectionGeneral : {
									MetaImage.OptionLimit : MetaImage.LimitDefault,
								},
							}
							for k in MetaImage.Selections:
								m = i
								if m == MetaImage.MediaSeasonx: m = MetaImage.MediaSeason
								elif m == MetaImage.MediaEpisodex: m = MetaImage.MediaEpisode
								elif m == MetaImage.MediaRecap: m = MetaImage.MediaSeason
								elif m == MetaImage.MediaExtra: m = MetaImage.MediaSeason
								elif m == MetaImage.MediaSmart: m = MetaImage.MediaEpisode
								elif m == MetaImage.MediaBase: m = MetaImage.MediaEpisode
								elif m == MetaImage.MediaPlayer: m = MetaImage.MediaEpisode

								try: index = MetaImage.IndexesDefault[i]
								except: index = MetaImage.IndexDefault
								if Tools.isDictionary(index):
									try: index = index[j]
									except: index = index[None]

								result[i][j][k] = {
									MetaImage.OptionMedia : m,
									MetaImage.OptionIndex : index,
									MetaImage.OptionType : j if k == MetaImage.SelectionPreference else MetaImage.TypesAlternative[j],
									MetaImage.OptionChoice : MetaImage.ChoiceDefault,
								}

					for i, v in MetaImage.TypesPreference.items():
						for j, w in v.items():
							if Tools.isDictionary(w):
								for k, x in w.items():
									result[i][j][MetaImage.SelectionPreference][k] = x
							else:
								result[i][j][MetaImage.SelectionPreference][MetaImage.OptionMedia] = w

					for i, v in MetaImage.TypesFallback.items():
						for j, w in v.items():
							if Tools.isDictionary(w):
								for k, x in w.items():
									result[i][j][MetaImage.SelectionFallback][k] = x
							else:
								result[i][j][MetaImage.SelectionFallback][MetaImage.OptionMedia] = w

				elif mode == MetaImage.ModeStyle:
					# Some of the fanart from TVDb contains the title/logo of the show.
					# This looks bad for some views, like the Logo view where the logo is overlaid on top of the fanart and now could show the logo twice.
					# Force the language to CodeNone to get images that are indeed plain.
					# A drawback is that many of the plain/language-less fanarts are still marked a English on TVDb (eg Game of Thrones / Rick & Morty).
					# Now a worse fanart with lower votes might be picked, because we specifically look for fanart without language.
					plain = [MetaImage.TypeFanart, MetaImage.TypeKeyart]

					for i in medias:
						result[i] = {}
						for j in MetaImage.Types:
							result[i][j] = {
								MetaImage.OptionProvider : MetaImage.ProvidersDefault[i],
								MetaImage.OptionSort : MetaImage.SortsDefault[MetaImage.ProvidersDefault[i]],
								MetaImage.OptionOrder : MetaImage.OrderDefault,
								MetaImage.OptionDecor : MetaImage.DecorsDefault[j],
								MetaImage.OptionLanguage : Language.CodeNone if j in plain else Language.CodeAutomatic,
							}

				MetaImage.SettingsDefault[mode] = result

			if lock: MetaImage.SettingsLock.release()

		result = MetaImage.SettingsDefault[mode]
		if copy: result = Tools.copy(result)
		try: result = result[media]
		except: pass
		try: result = result[type]
		except: pass
		return result

	@classmethod
	def settingsSelect(self, mode, media, settings = False, clear = True):
		from lib.modules.interface import Dialog, Format, Translation

		self.mClose = False
		self.mTitle = None
		self.mSettings = None
		self.mMedia = media

		if media == MetaImage.MediaMovie: self.mTitle = 35594 if mode == MetaImage.ModeStyle else 35588
		elif media == MetaImage.MediaSet: self.mTitle = 36083 if mode == MetaImage.ModeStyle else 36084
		elif media == MetaImage.MediaShow: self.mTitle = 35595 if mode == MetaImage.ModeStyle else 35589
		elif media == MetaImage.MediaSeason: self.mTitle = 35596 if mode == MetaImage.ModeStyle else 35590
		elif media == MetaImage.MediaEpisode: self.mTitle = 35597 if mode == MetaImage.ModeStyle else 35591
		elif media == MetaImage.MediaSeasonx: self.mTitle = None if mode == MetaImage.ModeStyle else 35590
		elif media == MetaImage.MediaEpisodex: self.mTitle = None if mode == MetaImage.ModeStyle else 35591
		elif media == MetaImage.MediaRecap: self.mTitle = None if mode == MetaImage.ModeStyle else 35592
		elif media == MetaImage.MediaExtra: self.mTitle = None if mode == MetaImage.ModeStyle else 35593
		elif media == MetaImage.MediaSmart: self.mTitle = None if mode == MetaImage.ModeStyle else 35598
		elif media == MetaImage.MediaBase: self.mTitle = None if mode == MetaImage.ModeStyle else 36751
		elif media == MetaImage.MediaPlayer: self.mTitle = None if mode == MetaImage.ModeStyle else 36752

		if mode == MetaImage.ModeStyle: self.mSettings = MetaImage.SettingsStyle[media]
		elif mode == MetaImage.ModeSelection: self.mSettings = MetaImage.SettingsSelection[media]

		self.mData = self.settingsDefault(mode = mode, media = self.mMedia, copy = True)
		data = Settings.getData(self.mSettings)
		if data: self.mData = Tools.update(self.mData, data)
		dataOriginal = Tools.copy(data)

		def _settingsClose():
			self.mClose = True

		def _settingsHelp(mode):
			items = []
			introduction = 'Various images can be displayed in Kodi menus and other places, depending on your skin and the selected view. Changing the style or selection settings does not guarantee that a specific image is picked, but rather a best effort is made to pick the image closest to your preferences.'
			types = [
				{'type' : 'title', 'value' : 'Image Type', 'break' : 2},
				{'type' : 'text', 'value' : 'The following images types are available:', 'break' : 2},
				{'type' : 'list', 'value' : [
					{'title' : 'Poster', 'value' : 'A portrait image for movies, shows, and seasons displayed in the front. Posters typically contain the title and sometimes additional decor or text. Posters are almost always available and supported all skins.'},
					{'title' : 'Thumbnail', 'value' : 'A portrait screenshot for movies, shows, seasons, and episodes. Episode thumbnails are typically screengrabs directly from the video without titles or decor. Thumbnails for movies, shows, and seasons rather use artwork images with titles. Thumbnails are almost always available and supported all skins.'},
					{'title' : 'Background', 'value' : 'A landscape fanart image displayed behind the menus for movies, shows, and seasons. Backgrounds are plain artwork, typically without titles or decor. Backgrounds are almost always available and supported all skins.'},
					{'title' : 'Landscape', 'value' : 'A landscape fanart image often displayed in the front and mostly only available for movies. Landscapes are very similar to backgrounds, but contain the title and sometimes additional decor. Landscapes are rarely available and supported by some skins.'},
					{'title' : 'Banner', 'value' : 'A wide landscape image for movies, shows, and seasons displayed in the front. Banners are typically used for the entire selectable menu item grouped into a grid. Banners are mostly available, with a few exceptions, and supported by many skins.'},
					{'title' : 'Logo', 'value' : 'A transparent icon containing the title for movies and shows. Logos are typically overlaid with backgrounds or landscapes. Logos are mostly available, with a few exceptions, and supported by some skins.'},
					{'title' : 'Clear Art', 'value' : 'A transparent icon for movies and shows. Clear art is similar to logos, but typically also contains art or characters together with the title. Clear art is less commonly available and supported by very few skins.'},
					{'title' : 'Disc Art', 'value' : 'A transparent image containing artwork overlaid on a DVD or BluRay disc, mostly only available for movies. Clear art is less commonly available and supported by very few skins.'},
					{'title' : 'Key Art', 'value' : 'A portrait image for movies, shows, and seasons displayed in the front. Key art is similar to posters, but does not containing any title, decor, or other text. Key art is rarely available and supported by very few skins.'},
				]}
			]

			if mode == MetaImage.ModeStyle:
				items.extend([{'type' : 'title', 'value' : 'Image Style', 'break' : 2}, {'type' : 'text', 'value' : introduction + ' Note that any changes to the image style settings requires new images to be retrieved, which can temporarily slow down menu loading while the cache is being filled up again.', 'break' : 2}])
				items.extend(types)
				items.extend([
					{'type' : 'title', 'value' : 'Image Provider', 'break' : 2},
					{'type' : 'text', 'value' : 'Images come from the following sources:', 'break' : 2},
					{'type' : 'list', 'value' : [
						{'title' : 'IMDb', 'value' : 'Only provides movie and show posters that are often cluttered with decor and additional text, like the posters used in physical movie theaters. IMDb only has a single poster and these are only available for menus with IMDb lists. Posters contain text in the language specified by the main [I]Metadata Language[/I]  setting if available, otherwise the English version is returned.'},
						{'title' : 'TMDb', 'value' : 'Provides posters, backgrounds, and logos for movies and sets. Multiple images are available from a range of languages.'},
						{'title' : 'TVDb', 'value' : 'Provides posters, thumbnails, backgrounds, banners, logos, and clear art for shows, seasons, and episodes. Multiple images are available from a range of languages. Images are often not grouped and different styled images might be displayed for seasons.'},
						{'title' : 'Fanart', 'value' : 'Provides posters, thumbnails, backgrounds, banners, logos, clear art, and disc art for movies, shows, and seasons. Multiple images are available from a range of languages. Fanart mostly has images in their original solution with a large file size and might therefore take slightly longer to download. If you intend on using Fanart images, you should consider authenticating a Fanart account, since it will return more recent images.'},
						{'title' : 'Trakt', 'value' : 'Provides posters, thumbnails, backgrounds, banners, logos, and clear art for movies, shows, seasons, and episodes. Typically only a single image is available in English. Images are often not grouped and different styled images might be displayed for seasons.'},
						{'title' : 'TVmaze', 'value' : 'Only provides show posters for certain submenus. TVmaze only has a single poster and it is typically in English.'},
					]},

					{'type' : 'title', 'value' : 'Image Sorting', 'break' : 2},
					{'type' : 'text', 'value' : 'Some providers, like TDMb, TVDb, and Fanart, have many alternative images. These images can be sorted in specific ways to better pick the ones that suit your preferences. Sorting can also be useful for TVDb to group show and season posters that have the same style and belong together as an image set. Note that none of the TVDb sorting options are prefect and there will always be some shows where the image grouping does not work and images, like season posters, of different styles are picked. Images can be sorted as follows:', 'break' : 2},
					{'type' : 'list', 'value' : [
						{'title' : 'None', 'value' : 'Do not apply any sorting and use the default sequence.'},
						{'title' : 'Index', 'value' : 'Sort images in the same order as returned by the API.'},
						{'title' : 'ID', 'value' : 'Sort images by their API ID. Most providers use incrementing integers as IDs, which often means that the ID represents the date or order in which the images were uploaded. '},
						{'title' : 'Vote', 'value' : 'Sort images by the average vote cast by users. Although sorting by vote seems like the most natural way of picking images, sometimes images with a lower vote might be preferred over those with a higher vote. Certain images on TMDb might be moved to the front by moderators as the primary image, although there are other images with a higher user rating. The primary images from TMDb should therefore be picked by index instead of vote.'},
						{'title' : 'Origin', 'value' : 'Image links on TVDb can have different formats. There is not documentation on why there are different formats, but it seems that certain formats are used for moderator uploads, whereas other formats are used for normal user uploads. Sorting by origin might therefore help to pick official images over fan-made images, although this is not perfect.'},
						{'title' : 'Combinations', 'value' : 'Sorting can also be based on two or more attributes. For instance, one might first sort by origin, then by vote, and finally by ID.'},
					]},

					{'type' : 'title', 'value' : 'Image Ordering', 'break' : 2},
					{'type' : 'text', 'value' : 'Sorting can be applied in two directions:', 'break' : 2},
					{'type' : 'list', 'value' : [
						{'title' : 'Forward', 'value' : 'Use the default forward order after sorting. This means that the [I]best[/I]  values are listed first. For votes and origins, the highest value is used, whereas for index and ID, the lowest value is used.'},
						{'title' : 'Reversed', 'value' : 'This means that the [I]worst[/I]  values are listed first. For votes and origins, the lowest value is used, whereas for index and ID, the highest value is used.'},
					]},

					{'type' : 'title', 'value' : 'Image Decor', 'break' : 2},
					{'type' : 'text', 'value' : 'Images have the following decorations:', 'break' : 2},
					{'type' : 'list', 'value' : [
						{'title' : 'Plain', 'value' : 'Images without any additional text and decor. For certain image types, like posters, the title might still be present. Images are assumed to be plain if they do not have a language associated with them.'},
						{'title' : 'Embell', 'value' : 'Images with additional text and decor, besides the title. For certain image types, like posters, the additional decoration might be cluttered and aesthetically unpleasant. Images are assumed to be embelled if they do have a language associated with them.'},
					]},

					{'type' : 'title', 'value' : 'Image Language', 'break' : 2},
					{'type' : 'text', 'value' : 'The title or other text in images can be in a specific language:', 'break' : 2},
					{'type' : 'list', 'value' : [
						{'title' : 'None', 'value' : 'The image does not have any language associated with it. In most cases this means it is a plain image without any text or decorations. But this is not always the case. Sometimes images contain text in a specific language, but it is not labeled as such. In other cases, an image might be labeled with a specific language, but actually does not contain any text.'},
						{'title' : 'Automatic', 'value' : 'The image language is automatically determined from the global language setting. It will first try to use the [I]Image Language[I]  setting under the [I]Images[/I]  tab. If that is also set to [I]Automatic[I]  , the [I]Primary Language[I]  setting under the [I]General[/I]  tab. Note the IMDb images are an exception to this and instead use the [I]Metadata Language[I]  setting under the [I]Metadata[/I]  tab, since the image is part of  the IMDb webpage.'},
						{'title' : 'Specific', 'value' : 'A specific language can also be chosen for each image type that overwrites the global language settings.'},
					]},
				])
			else:
				items.extend([{'type' : 'title', 'value' : 'Image Selection', 'break' : 2}, {'type' : 'text', 'value' : introduction + ' In most cases multiple images of the same type are available. The image selection settings are used to choose the preferred images.', 'break' : 2}])
				items.extend(types)
				items.extend([
					{'type' : 'title', 'value' : 'Image Option', 'break' : 2},

					{'type' : 'text', 'value' : 'Images can be selected with the following general settings:', 'break' : 2},
					{'type' : 'list', 'value' : [
						{'title' : 'Limit', 'value' : 'Most types have multiple images. Some Kodi skins support multiple images and will cycle through them in a slideshow-fashion. Other Kodi skins might only display the first available image. If your Kodi skins supports multiple images, but you do not like the constant cycling, the single or specific number of images can be used.'},
					]},

					{'type' : 'text', 'value' : 'For each image type, [I]Preferred[/I]  settings can be specified which are the first choice for any given image. If the preferred image is not available, the [I]Fallback[/I]  settings are used to select an alternative image instead. If the fallback image is also not available, the next best image will be used instead. If no images are available, the default theme images are used as specified under the [I]Theme[/I]  settings tab. The following image selection is available:', 'break' : 2},
					{'type' : 'list', 'value' : [
						{'title' : 'Media', 'value' : 'Select between show, season, or episode artwork. Sometimes using the artwork of a higher level might look better. For instance, many shows have separate season backgrounds typically containing the season name or number. This might not be aesthetically pleasing to some, and the default show background can be used instead for all seasons, creating a more consistent theme when navigating through the season menus.'},
						{'title' : 'Type', 'value' : 'Select a different image type instead of using the default type. For instance, a poster can be displayed in place of an episode thumbnail.'},
						{'title' : 'Choice', 'value' : 'Select a random image from those available each time the menu is loaded, or use a specific image.'}
					]},
				])

			Dialog.details(title = self.mTitle, items = items)

		def _settingsDefault(mode = None, type = None, selection = None, option = None):
			default = self.settingsDefault(mode = mode, media = self.mMedia, copy = True)
			if type:
				if option is None and selection is None: self.mData[type] = default[type]
				elif option is None: self.mData[type][selection] = default[type][selection]
				else: self.mData[type][option] = default[type][option]
			else:
				self.mData = default

		def _settingsLabel(value, option = None):
			if value is None: return 33564

			elif value == MetaImage.MediaMovie: return 35496
			elif value == MetaImage.MediaSet: return 35534
			elif value == MetaImage.MediaShow: return 35498
			elif value == MetaImage.MediaSeason: return 32055
			elif value == MetaImage.MediaEpisode: return 33028

			elif value == MetaImage.TypePoster: return 32042
			elif value == MetaImage.TypeThumb: return 35467
			elif value == MetaImage.TypeFanart and not option == MetaImage.OptionProvider: return 32337
			elif value == MetaImage.TypeLandscape: return 32044
			elif value == MetaImage.TypeBanner: return 32043
			elif value == MetaImage.TypeClearlogo: return 35300
			elif value == MetaImage.TypeClearart: return 32045
			elif value == MetaImage.TypeDiscart: return 32046
			elif value == MetaImage.TypeKeyart: return 32047

			elif value == MetaImage.ProviderImdb: return 32034
			elif value == MetaImage.ProviderTmdb: return 33508
			elif value == MetaImage.ProviderTvdb: return 35668
			elif value == MetaImage.ProviderTvmaze: return 35669
			elif value == MetaImage.ProviderTrakt: return 32315
			elif value == MetaImage.ProviderFanart: return 35260

			elif value == MetaImage.SortNone: return 33112
			elif value == MetaImage.SortIndex: return 35364
			elif value == MetaImage.SortId: return 32305
			elif value == MetaImage.SortVote: return 33511
			elif value == MetaImage.SortVoteIndex: return 33512
			elif value == MetaImage.SortVoteId: return 33513
			elif value == MetaImage.SortVoteOrigin: return 33514
			elif value == MetaImage.SortVoteOriginIndex: return 33515
			elif value == MetaImage.SortVoteOriginId: return 33516
			elif value == MetaImage.SortOrigin: return 33510
			elif value == MetaImage.SortOriginIndex: return 33517
			elif value == MetaImage.SortOriginId: return 33518
			elif value == MetaImage.SortOriginVote: return 33519
			elif value == MetaImage.SortOriginVoteIndex: return 33520
			elif value == MetaImage.SortOriginVoteId: return 33521

			elif value == MetaImage.OrderForward: return 33856
			elif value == MetaImage.OrderReversed: return 33857

			elif value == MetaImage.ChoiceRandom: return 35375
			elif value == MetaImage.ChoicePrimary: return 35486
			elif value == MetaImage.ChoiceSecondary: return 35487
			elif value == MetaImage.ChoiceTertiary: return 35334
			elif value == MetaImage.ChoiceQuaternary: return 32025
			elif value == MetaImage.ChoiceQuinary: return 32026

			elif value == MetaImage.DecorAny: return 33113
			elif value == MetaImage.DecorPlain: return 33455
			elif value == MetaImage.DecorEmbell: return 33475

			elif value == MetaImage.IndexCurrent: return 33021
			elif value == MetaImage.IndexPrevious: return 36051
			elif value == MetaImage.IndexNext: return 36087

			elif value == MetaImage.LimitAutomatic: return 33800
			elif value == MetaImage.LimitUnlimited: return 35221
			elif value == MetaImage.LimitSingle: return 35224
			elif value == MetaImage.LimitDouble: return 35225
			elif value == MetaImage.LimitTriple: return 35226
			elif value == MetaImage.LimitQuadruple: return 35227
			elif value == MetaImage.LimitQuintuple: return 35228

			elif value == MetaImage.OptionLimit: return 32311
			elif value == MetaImage.OptionProvider: return 33681
			elif value == MetaImage.OptionSort: return 33335
			elif value == MetaImage.OptionOrder: return 35011
			elif value == MetaImage.OptionChoice: return 35141
			elif value == MetaImage.OptionDecor: return 32348
			elif value == MetaImage.OptionLanguage: return 33787
			elif value == MetaImage.OptionMedia: return 35235
			elif value == MetaImage.OptionType: return 33343
			elif value == MetaImage.OptionIndex: return 35364

			elif value == MetaImage.SelectionGeneral: return 32310
			elif value == MetaImage.SelectionPreference: return 35167
			elif value == MetaImage.SelectionFallback: return 35194

			elif len(value) == 2:
				if value == Language.CodeNone: return 33112
				elif value == Language.CodeAutomatic: return 33800
				else: return Language.name(value)

		def _settingsDescription(value, option = None):
			from lib.modules.interface import Translation

			if value == MetaImage.MediaMovie: return Translation.string(32322) % Translation.string(35496).lower()
			elif value == MetaImage.MediaSet: return Translation.string(32322) % Translation.string(35534).lower()
			elif value == MetaImage.MediaShow: return Translation.string(32322) % Translation.string(35498).lower()
			elif value == MetaImage.MediaSeason: return Translation.string(32322) % Translation.string(32055).lower()
			elif value == MetaImage.MediaEpisode: return Translation.string(32322) % Translation.string(33028).lower()

			elif value == MetaImage.TypePoster: return Translation.string(32322) % Translation.string(32042).lower()
			elif value == MetaImage.TypeThumb: return Translation.string(32322) % Translation.string(35467).lower()
			elif value == MetaImage.TypeFanart and not option == MetaImage.OptionProvider: return Translation.string(32322) % Translation.string(32337).lower()
			elif value == MetaImage.TypeLandscape: return Translation.string(32322) % Translation.string(32044).lower()
			elif value == MetaImage.TypeBanner: return Translation.string(32322) % Translation.string(32043).lower()
			elif value == MetaImage.TypeClearlogo: return Translation.string(32322) % Translation.string(35300).lower()
			elif value == MetaImage.TypeClearart: return Translation.string(32322) % Translation.string(32045).lower()
			elif value == MetaImage.TypeDiscart: return Translation.string(32322) % Translation.string(32046).lower()
			elif value == MetaImage.TypeKeyart: return Translation.string(32322) % Translation.string(32047).lower()

			elif value in MetaImage.Providers: return Translation.string(32316) % Translation.string(_settingsLabel(value, option = option))

			elif value == MetaImage.ChoiceRandom: return 32317
			elif value == MetaImage.ChoicePrimary: return Translation.string(32318) % Translation.string(32350)
			elif value == MetaImage.ChoiceSecondary: return Translation.string(32318) % Translation.string(32351)
			elif value == MetaImage.ChoiceTertiary: return Translation.string(32318) % Translation.string(32352)
			elif value == MetaImage.ChoiceQuaternary: return Translation.string(32318) % Translation.string(32354)
			elif value == MetaImage.ChoiceQuinary: return Translation.string(32318) % Translation.string(32355)

			elif value == MetaImage.SortNone: return 33758
			elif value == MetaImage.SortIndex: return Translation.string(33759) % Translation.string(35364).lower()
			elif value == MetaImage.SortId: return Translation.string(33759) % Translation.string(32305)
			elif value == MetaImage.SortVote: return Translation.string(33759) % Translation.string(33511).lower()
			elif value == MetaImage.SortVoteIndex: return Translation.string(33760) % (Translation.string(33511).lower(), Translation.string(35364).lower())
			elif value == MetaImage.SortVoteId: return Translation.string(33760) % (Translation.string(33511).lower(), Translation.string(32305))
			elif value == MetaImage.SortVoteOrigin: return Translation.string(33760) % (Translation.string(33511).lower(), Translation.string(33510).lower())
			elif value == MetaImage.SortVoteOriginIndex: return Translation.string(33761) % (Translation.string(33511).lower(), Translation.string(33510).lower(), Translation.string(35364).lower())
			elif value == MetaImage.SortVoteOriginId: return Translation.string(33761) % (Translation.string(33511).lower(), Translation.string(33510).lower(), Translation.string(32305))
			elif value == MetaImage.SortOrigin: return Translation.string(33759) % Translation.string(33510).lower()
			elif value == MetaImage.SortOriginIndex: return Translation.string(33760) % (Translation.string(33510).lower(), Translation.string(35364).lower())
			elif value == MetaImage.SortOriginId: return Translation.string(33760) % (Translation.string(33510).lower(), Translation.string(32305))
			elif value == MetaImage.SortOriginVote: return Translation.string(33760) % (Translation.string(33510).lower(), Translation.string(33511).lower())
			elif value == MetaImage.SortOriginVoteIndex: return Translation.string(33761) % (Translation.string(33510).lower(), Translation.string(33511).lower(), Translation.string(35364).lower())
			elif value == MetaImage.SortOriginVoteId: return Translation.string(33761) % (Translation.string(33510).lower(), Translation.string(33511).lower(), Translation.string(32305))

			elif value == MetaImage.OrderForward: return 33762
			elif value == MetaImage.OrderReversed: return 33763

			elif value == MetaImage.DecorAny: return 32338
			elif value == MetaImage.DecorPlain: return 32339
			elif value == MetaImage.DecorEmbell: return 32340

			elif value == MetaImage.IndexCurrent: return Translation.string(35358) % Translation.string(33021).lower()
			elif value == MetaImage.IndexPrevious: return Translation.string(35358) % Translation.string(36051).lower()
			elif value == MetaImage.IndexNext: return Translation.string(35358) % Translation.string(36087).lower()

			elif value == MetaImage.LimitAutomatic: return 35229
			elif value == MetaImage.LimitUnlimited: return 35230
			elif value == MetaImage.LimitSingle: return Translation.string(35231) % 1
			elif value == MetaImage.LimitDouble: return Translation.string(35232) % 2
			elif value == MetaImage.LimitTriple: return Translation.string(35232) % 3
			elif value == MetaImage.LimitQuadruple: return Translation.string(35232) % 4
			elif value == MetaImage.LimitQuintuple: return Translation.string(35232) % 5

			elif value == MetaImage.LimitAutomatic: return 33800
			elif value == MetaImage.LimitUnlimited: return 35221
			elif value == MetaImage.LimitSingle: return 35224
			elif value == MetaImage.LimitDouble: return 35225
			elif value == MetaImage.LimitTriple: return 35226
			elif value == MetaImage.LimitQuadruple: return 35227
			elif value == MetaImage.LimitQuintuple: return 35228

		def _settingsSummary(mode = None, type = None):
			default = self.settingsDefault(mode = mode, media = self.mMedia, type = type)
			data = self.mData
			if type: data = data[type]
			if default == data: return 33564
			else: return 35233

		def _settingsSupport(mode, type, option, selection = None):
			support							= {
				MetaImage.ModeSelection			: {
					MetaImage.OptionMedia		: {MetaImage.OptionMedia : (MetaImage.MediaShow, MetaImage.MediaSeason, MetaImage.MediaEpisode, MetaImage.MediaSeasonx, MetaImage.MediaEpisodex, MetaImage.MediaRecap, MetaImage.MediaExtra, MetaImage.MediaSmart, MetaImage.MediaBase, MetaImage.MediaPlayer)},
					MetaImage.OptionIndex		: {MetaImage.OptionMedia : (MetaImage.MediaRecap, MetaImage.MediaExtra)},
					MetaImage.OptionType		: None,
					MetaImage.OptionChoice		: None,
				},
				MetaImage.ModeStyle				: {
					MetaImage.OptionProvider	: None,
					MetaImage.OptionSort		: {MetaImage.OptionProvider : (None, MetaImage.ProviderTmdb, MetaImage.ProviderTvdb, MetaImage.ProviderFanart, MetaImage.ProviderTrakt)},
					MetaImage.OptionOrder		: {MetaImage.OptionProvider : (None, MetaImage.ProviderTmdb, MetaImage.ProviderTvdb, MetaImage.ProviderFanart, MetaImage.ProviderTrakt)},
					MetaImage.OptionChoice		: {MetaImage.OptionProvider : (None, MetaImage.ProviderTmdb, MetaImage.ProviderTvdb, MetaImage.ProviderFanart, MetaImage.ProviderTrakt)},
					MetaImage.OptionDecor		: {MetaImage.OptionProvider : (None, MetaImage.ProviderTmdb, MetaImage.ProviderTvdb, MetaImage.ProviderFanart, MetaImage.ProviderTrakt)},
					MetaImage.OptionLanguage	: {MetaImage.OptionProvider : (None, MetaImage.ProviderTmdb, MetaImage.ProviderTvdb, MetaImage.ProviderFanart, MetaImage.ProviderTrakt)},
				}
			}
			support = support[mode][option]
			if support:
				for key, values in support.items():
					value = self.mMedia if key == MetaImage.OptionMedia else self.mData[type][key]
					if not value in values: return False

			# Previous and next are always seasons.
			if selection and option == MetaImage.OptionIndex and not self.mData[type][selection][MetaImage.OptionMedia] == MetaImage.MediaSeason: return False

			return True

		def _settingsOption(type, mode, option, selection = None):
			if option == MetaImage.OptionLanguage:
				language = Language.settingsSelect(id = MetaImage.SettingsLanguage, title = self.mTitle, automatic = True, none = True, current = self.mData[type][option], update = False, result = Language.Code)
				if language: self.mData[type][option] = language
			else:
				items = [
					{'title' : Dialog.prefixBack(35374), 'close' : True, 'return' : False},
					{'title' : Dialog.prefixNext(33239)},
					{'title' : Dialog.prefixNext(33564)},
				]

				if option == MetaImage.OptionLimit: values = list(MetaImage.Limits.keys())
				elif option == MetaImage.OptionType: values = MetaImage.Types
				elif option == MetaImage.OptionChoice: values = [MetaImage.ChoiceRandom, MetaImage.ChoicePrimary, MetaImage.ChoiceSecondary, MetaImage.ChoiceTertiary, MetaImage.ChoiceQuaternary, MetaImage.ChoiceQuinary]
				elif option == MetaImage.OptionDecor: values = [MetaImage.DecorAny, MetaImage.DecorPlain, MetaImage.DecorEmbell]
				elif option == MetaImage.OptionIndex: values = [MetaImage.IndexCurrent, MetaImage.IndexPrevious, MetaImage.IndexNext]
				elif option == MetaImage.OptionOrder: values = [ MetaImage.OrderForward, MetaImage.OrderReversed]
				elif option == MetaImage.OptionSort:
					provider = self.mData[type][MetaImage.OptionProvider]
					if provider == MetaImage.ProviderTvdb: values = [MetaImage.SortNone, MetaImage.SortIndex, MetaImage.SortId, MetaImage.SortVote, MetaImage.SortVoteIndex, MetaImage.SortVoteId, MetaImage.SortVoteOrigin, MetaImage.SortVoteOriginIndex, MetaImage.SortVoteOriginId, MetaImage.SortOrigin, MetaImage.SortOriginIndex, MetaImage.SortOriginId, MetaImage.SortOriginVote, MetaImage.SortOriginVoteIndex, MetaImage.SortOriginVoteId]
					elif provider == MetaImage.ProviderTmdb: values = [MetaImage.SortNone, MetaImage.SortIndex, MetaImage.SortVote, MetaImage.SortVoteIndex]
					elif provider == MetaImage.ProviderFanart: values = [MetaImage.SortNone, MetaImage.SortIndex, MetaImage.SortId, MetaImage.SortVote, MetaImage.SortVoteIndex, MetaImage.SortVoteId]
					elif provider == MetaImage.ProviderTrakt: values = [MetaImage.SortNone, MetaImage.SortIndex]
				elif option == MetaImage.OptionProvider:
					values = []
					if type == MetaImage.TypePoster and not self.mMedia == Media.Set: values.append(MetaImage.ProviderImdb) # IMDb only has posters.
					if self.mMedia == Media.Episode: values.extend([MetaImage.ProviderTvdb, MetaImage.ProviderFanart, MetaImage.ProviderTrakt, MetaImage.ProviderTvmaze]) # Currently not retrieving episode images from TMDb, since it would require additional requests for each individual episode.
					elif self.isSerie(self.mMedia): values.extend([MetaImage.ProviderTvdb, MetaImage.ProviderTmdb, MetaImage.ProviderFanart, MetaImage.ProviderTrakt, MetaImage.ProviderTvmaze])
					elif self.mMedia == Media.Set: values.extend([MetaImage.ProviderTmdb])
					else: values.extend([MetaImage.ProviderTmdb, MetaImage.ProviderFanart, MetaImage.ProviderTrakt])
				elif option == MetaImage.OptionMedia:
					values = []
					if self.mMedia in [MetaImage.MediaShow, MetaImage.MediaSeason, MetaImage.MediaEpisode, MetaImage.MediaSeasonx, MetaImage.MediaEpisodex, MetaImage.MediaRecap, MetaImage.MediaExtra, MetaImage.MediaSmart, MetaImage.MediaBase, MetaImage.MediaPlayer]:
						values.append(MetaImage.MediaShow)
					if self.mMedia in [MetaImage.MediaSeason, MetaImage.MediaEpisode, MetaImage.MediaSeasonx, MetaImage.MediaEpisodex, MetaImage.MediaRecap, MetaImage.MediaExtra, MetaImage.MediaSmart, MetaImage.MediaBase, MetaImage.MediaPlayer]:
						values.append(MetaImage.MediaSeason)
					if self.mMedia in [MetaImage.MediaEpisode, MetaImage.MediaEpisodex, MetaImage.MediaSmart, MetaImage.MediaBase, MetaImage.MediaPlayer]:
						values.append(MetaImage.MediaEpisode)

				subitems = []
				for value in values: subitems.append({'title' : _settingsLabel(value, option = option), 'value' : _settingsDescription(value, option = option)})
				items.append({'title' : _settingsLabel(option), 'items' : subitems})

				choice = Dialog.information(title = self.mTitle, items = items, reselect = Dialog.ReselectMenu)
				if choice is None or choice < 0: _settingsClose()
				elif choice == 1: _settingsHelp(mode = mode)
				else:
					if choice == 2: _settingsDefault(mode = mode, type = type, option = option, selection = selection)
					elif choice >= 5:
						choice = values[choice - 5]
						if selection: self.mData[type][selection][option] = choice
						else: self.mData[type][option] = choice

					# Reset sort/order when the provider changes, since there are different sorting options for each provider.
					if option == MetaImage.OptionProvider:
						try:
							self.mData[type][MetaImage.OptionSort] = MetaImage.SortsDefault[self.mData[type][MetaImage.OptionProvider]]
							self.mData[type][MetaImage.OptionOrder] = MetaImage.OrderDefault
						except: pass # IMDb

		def _settingsOptions(mode, type):
			def _settingsOptionsItems():
				if self.mClose: return None
				items = [
					{'title' : Dialog.prefixBack(35374), 'close' : True, 'return' : False},
					{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp, 'parameters' : {'mode' : mode}},
					{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'mode' : mode, 'type' : type}},
				]

				options = MetaImage.Options[mode]
				if mode == MetaImage.ModeStyle:
					subitems = []
					for option in options:
						if _settingsSupport(mode = mode, type = type, option = option):
							subitems.append({'title' : _settingsLabel(option, option = option), 'value' : _settingsLabel(self.mData[type][option], option = option), 'action' : _settingsOption, 'parameters' : {'mode' : mode, 'type' : type, 'option' : option}})
					items.append({'title' : 35202, 'items' : subitems})
				elif mode == MetaImage.ModeSelection:
					subitems = [
						{'title' : _settingsLabel(MetaImage.OptionLimit), 'value' : _settingsLabel(self.mData[type][MetaImage.SelectionGeneral][MetaImage.OptionLimit]), 'action' : _settingsOption, 'parameters' : {'mode' : mode, 'type' : type, 'option' : MetaImage.OptionLimit, 'selection' : MetaImage.SelectionGeneral}},
					]
					items.append({'title' : _settingsLabel(MetaImage.SelectionGeneral), 'items' : subitems})
					for selection in MetaImage.Selections:
						subitems = []
						for option in options:
							if _settingsSupport(mode = mode, type = type, selection = selection, option = option):
								subitems.append({'title' : _settingsLabel(option), 'value' : _settingsLabel(self.mData[type][selection][option]), 'action' : _settingsOption, 'parameters' : {'mode' : mode, 'type' : type, 'option' : option, 'selection' : selection}})
						items.append({'title' : _settingsLabel(selection), 'items' : subitems})

				return items

			choice = Dialog.information(title = self.mTitle, items = _settingsOptionsItems(), refresh = _settingsOptionsItems, reselect = Dialog.ReselectMenu)
			if choice is None or choice < 0: _settingsClose()

		def _settingsTypes(mode):
			def _settingsTypesItems():
				if self.mClose: return None
				subitems = []
				for type in MetaImage.Types: subitems.append({'title' : _settingsLabel(type), 'value' : _settingsSummary(mode = mode, type = type), 'action' : _settingsOptions, 'parameters' : {'mode' : mode, 'type' : type}})
				items = [
					{'title' : Dialog.prefixBack(33486), 'close' : True},
					{'title' : Dialog.prefixNext(33239), 'action' : _settingsHelp, 'parameters' : {'mode' : mode}},
					{'title' : Dialog.prefixNext(33564), 'action' : _settingsDefault, 'parameters' : {'mode' : mode}},
					{'title' : 36202, 'items' : subitems},
				]
				return items

			Dialog.information(title = self.mTitle, items = _settingsTypesItems(), refresh = _settingsTypesItems, reselect = Dialog.ReselectMenu)

		_settingsTypes(mode = mode)
		Settings.setData(self.mSettings, self.mData, label = _settingsSummary(mode = mode))

		if clear and mode == MetaImage.ModeStyle and dataOriginal and not dataOriginal == self.mData:
			Dialog.confirm(title = self.mTitle, message = 35615)

		if settings: Settings.launchData(self.mSettings)

	###################################################################
	# GENERAL
	###################################################################

	@classmethod
	def valid(self, image):
		return image and not image == MetaImage.Invalid

	@classmethod
	def imdbLanguage(self, link, language = None):
		# IMDb can return differnt metadata and images based on the language set in the request header.
		# For most titles/languages, the English image is returned.
		# However, there are a few exceptions:
		# Eg: https://www.imdb.com/title/tt2058107/
		#	EN: https://m.media-amazon.com/images/M/MV5BMTQzNDU1NjE0NF5BMl5BanBnXkFtZTgwODA3NDczMDE@._V1_QL75_UX380_CR0,0,380,562_.jpg
		#	DE: https://m.media-amazon.com/images/M/MV5BMGNhYjlmMTgtZDQ3Yy00NDkzLTkyZTAtZTQ2MjI1NGQ2MzVkXkEyXkFqcGdeQXVyMTA4NjE0NjEy._V1_QL75_UX380_CR0,4,380,562_.jpg
		#	ES: https://m.media-amazon.com/images/M/MV5BODc2M2YyMWEtNWU3NC00MjAwLTk5ZDAtZTRlMTllN2NjMTZiXkEyXkFqcGdeQXVyMTEyOTQ1OTk4._V1_QL75_UY562_CR6,0,380,562_.jpg
		try:
			if language is None: language = Language.settingsCustom('metadata.region.language')
			index = link.rindex('/')
			if len(link[index:]) > 100: return language
		except: Logger.error()
		return Language.EnglishCode # Always default to English, and not None, since IMDb posters almost always have text.

	@classmethod
	def isSerie(self, media):
		return Media.isSerie(media) or media == MetaImage.MediaSeasonx or media == MetaImage.MediaEpisodex

	###################################################################
	# REPLACE
	###################################################################

	@classmethod
	def replace(self, images, missing, replacement, all = True, force = False):
		if (force or not missing in images) and replacement in images:
			if all:
				for number in MetaImage.Numbers:
					try: images[missing + number] = images[replacement + number]
					except: pass
			else:
				images[missing] = images[replacement]
		return images

	@classmethod
	def replaceThumbnail(self, images, all = True, force = False):
		# Some skins (eg: Aeon Nox Silvo) are not intelligent enough to pick the poster if no thumb is available.
		return self.replace(images = images, missing = MetaImage.TypeThumb, replacement = MetaImage.TypePoster, all = all, force = force)

	@classmethod
	def replacePoster(self, images, all = True, force = False):
		# Some skins (eg: Estaury) always display a poster (if available) in episode lists, even if thumbnails are available.
		return self.replace(images = images, missing = MetaImage.TypePoster, replacement = MetaImage.TypeThumb, all = all, force = force)

	@classmethod
	def replaceSeason(self, images):
		# Delete season images, otherwise some skins (eg Aeon Nox) might still display the season images, although episode images are available.
		for type in MetaImage.Types:
			for number in MetaImage.Numbers:
				try: del images[MetaImage.PrefixSeason + type + number]
				except: pass
		return images

	###################################################################
	# FILTER
	###################################################################

	@classmethod
	def filter(self, items, types):
		result = []
		for item in items:
			if MetaImage.Attribute in item:
				for type in types:
					if type in item[MetaImage.Attribute] and item[MetaImage.Attribute][type]:
						result.append(item)
		return result

	@classmethod
	def filterPoster(self, items):
		return self.filter(items = items, types = [MetaImage.TypePoster])

	###################################################################
	# CREATE
	###################################################################

	@classmethod
	def create(self, link, provider, language = None, theme = None, sort = None):
		if not link: return None

		# Newer movies (eg: No Time to Die) have SVG logos on TMDb. Ignore those for now, since Kodi cannot render them (yet).
		if link.lower().endswith('.svg'): return None

		if language:
			if language == '00': language = None # Fanart
		elif provider == MetaImage.ProviderImdb:
			language = MetaImage.imdbLanguage(link = link)
		if not language: language = None

		return {
			MetaImage.AttributeLink : link,
			MetaImage.AttributeProvider : provider,
			MetaImage.AttributeLanguage : language,
			MetaImage.AttributeTheme : theme,
			MetaImage.AttributeSort : sort,
		}

	###################################################################
	# THEMES
	###################################################################

	@classmethod
	def themes(self, media, images = None, sort = None):
		themes = {}
		if Tools.isDictionary(images):
			for i in images.values():
				self.update(media = media, images = i, sort = sort, themes = themes)
		else:
			self.update(media = media, images = images, sort = sort, themes = themes)
		return themes

	###################################################################
	# UPDATE
	###################################################################

	# sort: force a final sort based on the providers, which overwrites the sorting preference fromth e user's settings. This is useful if we know some images might be wrong (eg: GoT S00E56 TVDb vs Trakt/TMDb).
	@classmethod
	def update(self, media, data = None, category = None, images = None, copy = False, sort = None, themes = None):
		if sort:
			type = None # Used inside _sort()
			prepare = not bool(data)

			if Tools.isDictionary(sort):
				if not Tools.isDictionary(next(iter(sort.values()))): # Already processed when this fucntion was called previously with the same sort dict/list.
					for k, v in sort.items():
						sort[k] = {v[i] : i for i in range(len(v))}
			elif Tools.isList(sort):
				sort = {None : {sort[i] : i for i in range(len(sort))}}

			def _sort(value, untheme = False):
				base = 999999999
				language = 0
				theme = 0
				vote = 0
				index = 0

				# Set by TVDb indicating to rather use Fanart/TMDb images.
				try: ignore = base * value[MetaImage.AttributeSort][MetaImage.SortIgnore]
				except: ignore = None

				# Add the language to sorting to prefer images that are in the user's language setting.
				# Do not do this for episodes, otherwise thumbnails from different providers are selected which can have different aspect ratios, quality, etc, which does not lookup consistent.
				# Eg: GoT S04
				if not media == Media.Episode:
					try: language = 100000 * value[MetaImage.AttributeSort][MetaImage.SortLanguage]
					except: pass

				# Prefer images fromt he same theme/group.
				if not media == Media.Episode and not untheme:
					try: theme = 10 * value[MetaImage.AttributeSort][MetaImage.SortTheme]
					except: pass

				if media == Media.Season:
					try: vote = value[MetaImage.AttributeSort][MetaImage.SortVote]
					except: pass
					if Tools.isArray(vote) and vote: vote = vote[0]
					if not vote: vote = 0
					vote = 1 - (vote / 10000.0)

				# Add the index to prefer TVDb images with a lower index.
				# Eg: White Lotus S04 (unreleased - does not have a poster yet - pick the quaternary show poster).
				# Without index: https://artworks.thetvdb.com/banners/v4/series/390430/posters/6385388010b75.jpg
				# With index: https://artworks.thetvdb.com/banners/v4/series/390430/posters/63987a7338b93.jpg
				if Media.isSerie(media):
					try: index = value[MetaImage.AttributeSort][MetaImage.SortIndex]
					except: pass
					if Tools.isArray(index) and index: index = index[0]
					if not index: index = 0
					index = 1 - (index / 10000000.0)

				extra = language + theme + vote + index

				if ignore is None:
					sorting = (sort.get(type) or sort.get(None) or {}).get(value.get('provider'))
					sorting = (sorting * ((base + 1) / 10.0)) if not sorting is None else base
					return sorting + extra
				else:
					return base + ignore + extra

		if copy: images = Tools.copy(images)

		# Filter out invalid images (eg: SVG returned by create()).
		for key, values in images.items():
			images[key] = [i for i in values if i]

		result = {}
		limit = len(MetaImage.Numbers)
		for type in MetaImage.Types:
			result[type] = []
			if type in images and images[type]:
				values = images[type]
				if not Tools.isArray(values): values = [values]
				if values and Tools.isDictionary(values[0]):
					values1 = []
					values2 = self.updateProvider(media = media, type = type, images = values)
					for values3 in values2:
						values3 = self.updateLanguage(media = media, type = type, images = values3)
						values1.append(values3)
					values1 = Tools.listFlatten(data = values1, recursive = False)

					# If a single season does not have any images belonging to a theme that was used by the previous seasons, do not use the theme for sorting, but stick to the other attributes (votes, index, etc).
					# Eg: Rick & Morty S01-S07 all have posters belonging to the "652d6" theme on TVDb. But S08 is new and has only 2 posters.
					# The first poster does belong the theme picked for S01-S07, but it has a different ID and therefore the theme does not match.
					#	https://artworks.thetvdb.com/banners/v4/season/2181257/posters/6834b02986ca5.jpg
					# The second poster belongs to another highly-ranked theme (with fewer images). But this poster should not be sorted before the first poster, even though it has a "better" theme.
					#	https://artworks.thetvdb.com/banners/v4/season/2181257/posters/68334c15d87f6.jpg
					# Hence, if we get to a season that does not have posters belonging to the same theme as the previous seasons, ignore the theme during sorting.
					# This approach also seems to pick slightly better and more consistent posters for Pokémon, although it is still a bit of a mess.
					# Also test this with S.W.A.T. where S01-S06 should have consistent posters, while S07-S08 will have different posters/themes.
					# Not sure if this would cause the incorrect poster to be picked for other shows.
					# Not sure if this should also be applied to other image types.
					untheme = False
					if not prepare and themes and media == Media.Season and type == MetaImage.TypePoster: # Only untheme during the final run when "data" has a value.
						themed = themes.get(type)
						if themed and sum(themed.get(j.get(MetaImage.SortTheme)) or 0 for j in values1) <= 1: untheme = True

					if sort: values1 = Tools.listSort(values1, key = lambda x : _sort(value = x, untheme = untheme))

					if prepare and media == Media.Season and type == MetaImage.TypePoster: # Only add the theme during preparation from themes().
						try:
							if not themes is None and values1:
								if not type in themes: themes[type] = {}
								try: themes[type][values1[0].get(MetaImage.SortTheme)] += 1
								except: themes[type][values1[0].get(MetaImage.SortTheme)] = 1
						except: Logger.error()

					result[type] = [i[MetaImage.AttributeLink] for i in values1]
				else: # Already processed images.
					result[type] = values
				result[type] = Tools.listUnique(result[type])[:limit]

		if data:
			if not MetaImage.Attribute in data: data[MetaImage.Attribute] = {}
			if category: data[MetaImage.Attribute][category] = result
			else: data[MetaImage.Attribute] = result
		return result

	@classmethod
	def updateProvider(self, media, type, images):
		setting = self.settings(mode = MetaImage.ModeStyle, media = media, type = type)[MetaImage.OptionProvider]
		settingDefault = False
		if setting is None:
			settingDefault = True
			setting = MetaImage.ProviderTvdb if self.isSerie(media) else MetaImage.ProviderTmdb

		settingSort = self.settingsStyleSort(media = media, type = type, default = True)
		settingOrder = self.settingsStyleOrder(media = media, type = type, default = True)

		if images and not MetaImage.OptionProvider in images[0]:
			map = {
				MetaImage.ProviderImdb : ['imdb.com', 'amazon.com', 'media-amazon'],
				MetaImage.ProviderTmdb : ['tmdb.org', 'themoviedb.org'],
				MetaImage.ProviderTvdb : ['thetvdb.com'],
				MetaImage.ProviderTvmaze : ['tvmaze.com'],
				MetaImage.ProviderTrakt : ['trakt.tv'],
				MetaImage.ProviderFanart : ['fanart.tv'],
			}
			for i in range(len(images)):
				link = images[i][MetaImage.AttributeLink]
				for key, values in map.items():
					if any(j in link for j in values):
						images[i][MetaImage.OptionProvider] = key
						break

		# The sort setting is only available for the provider selected in the settings.
		# When sorting images from other providers (eg: fallback images), use that  provider's default sorting.
		# Do not sort TVDb, since it already has internal sorting in metadata.py.
		sort = {i : [MetaImage.SortsDefault[i], MetaImage.OrderDefault == MetaImage.OrderForward] for i in [MetaImage.ProviderTmdb, MetaImage.ProviderFanart]}
		if setting in sort: sort[setting] = [settingSort, settingOrder == MetaImage.OrderForward]

		providers = {}
		for provider in MetaImage.Providers:
			providers[provider] = [i for i in images if i[MetaImage.AttributeProvider] == provider]
			if provider in sort:
				attribute = sort[provider]
				attributeSort = attribute[0]
				if attributeSort: providers[provider].sort(key = lambda i : (i.get(MetaImage.AttributeSort) or {}).get(attributeSort) or 0, reverse = attribute[1])

		result = []
		if settingDefault:
			# This allows to later select an image with a specific language/decor from another provider if the default provider does not have one.
			result = []
			try:
				result.extend(providers[setting])
				del providers[setting]
			except: pass
			for key, values in providers.items():
				result.extend(values)
			return [result]
		else:
			for key, values in providers.items():
				if not key == setting: result.extend(values)
			return [providers[setting], result]

	@classmethod
	def updateLanguage(self, media, type, images):
		settings = self.settings(mode = MetaImage.ModeStyle, media = media, type = type)

		settingDecor = settings[MetaImage.OptionDecor]
		if settingDecor is None: settingDecor = MetaImage.DecorEmbell if type in [MetaImage.TypePoster, MetaImage.TypeLandscape, MetaImage.TypeBanner, MetaImage.TypeClearlogo, MetaImage.TypeClearart, MetaImage.TypeDiscart] else MetaImage.DecorPlain

		settingLanguage = settings[MetaImage.OptionLanguage]
		if settingLanguage == Language.CodeEnglish: settingLanguage = None

		settingsGeneral = Language.settingsCode()

		plain = settingDecor == MetaImage.DecorPlain
		none = (None, Language.CodeUniversal, Language.CodeNone, Language.CodeUnknown)
		result = [[], [], [], [], []]

		for i in images:
			if not i.get(MetaImage.AttributeSort): i[MetaImage.AttributeSort] = {}

			extra = 0
			language = i[MetaImage.AttributeLanguage]
			if language in none:
				index = 0 if plain else 3
			elif settingLanguage and language == settingLanguage:
				index = 1 if plain else 0
			elif settingsGeneral and language in settingsGeneral:
				index = 2 if plain else 1
				extra = (10 - settingsGeneral.index(language)) / 100.0 # Prefer the primary over the secondary language.
			elif language == Language.CodeEnglish:
				index = 3 if plain else 2
			else:
				index = 4

			i[MetaImage.AttributeSort][MetaImage.SortLanguage] = index - extra
			result[index].append(i)

		result = result[0] + result[1] + result[2] + result[3] + result[4]
		return result

	###################################################################
	# EXTRACT
	###################################################################

	@classmethod
	def extract(self, data, media = None, preference = True, fallback = True, recover = True, limit = True, default = True, show = True, season = True, episode = True, previous = True, next = True, choice = None, specific = None):
		try:
			if media is None:
				if data:
					if 'tvshowtitle' in data:
						if 'season' in data:
							if 'episode' in data: media = MetaImage.MediaEpisode
							else: media = MetaImage.MediaSeason
						else: media = MetaImage.MediaShow
					else:
						if 'set' in data and data['set'] and 'tmdb' in data and data['tmdb'] and not('imdb' in data and data['tmdb']) and not('trakt' in data and data['trakt']): media = MetaImage.MediaSet
						else: media = MetaImage.MediaMovie

			serie = self.isSerie(media) or Media.isBonus(media) or media == MetaImage.MediaSmart or media == MetaImage.MediaBase or media == MetaImage.MediaPlayer

			images = {}
			if data and MetaImage.Attribute in data:
				levels = []
				if specific:
					if not serie or episode: levels.append(MetaImage.PrefixNone)
					if serie:
						if season: levels.append((MetaImage.MediaSeason, MetaImage.PrefixSeason))
						if show: levels.append((MetaImage.MediaShow, MetaImage.PrefixShow))
						if previous: levels.append((MetaImage.IndexPrevious, MetaImage.PrefixPrevious))
						if next: levels.append((MetaImage.IndexNext, MetaImage.PrefixNext))
				else:
					if serie:
						if show: levels.append((MetaImage.MediaShow, MetaImage.PrefixShow))
						if season: levels.append((MetaImage.MediaSeason, MetaImage.PrefixSeason))
						if previous: levels.append((MetaImage.IndexPrevious, MetaImage.PrefixPrevious))
						if next: levels.append((MetaImage.IndexNext, MetaImage.PrefixNext))
					if not serie or episode: levels.append(MetaImage.PrefixNone)

				values = data[MetaImage.Attribute]
				for level in levels:
					if level:
						if not level[0] in values: continue
						values1 = values[level[0]]
						level = level[1]
					else:
						values1 = values

					# If the 1st fanart image is the same as the 1st landscape image, use the 2nd best landscape image.
					# This is for landscape views (eg Aeon Nox) where both the fanart and landscape images are shown.
					# It doesn't look good if both images are the same.
					if MetaImage.TypeFanart in values1 and MetaImage.TypeLandscape in values1:
						if values1[MetaImage.TypeFanart] and values1[MetaImage.TypeLandscape] and values1[MetaImage.TypeFanart][0] == values1[MetaImage.TypeLandscape][0]:
							values1[MetaImage.TypeLandscape].append(values1[MetaImage.TypeLandscape].pop(0))

					for type in MetaImage.Types:
						if type in values1:
							values2 = values1[type]
							for i in range(len(values2)):
								image = values2[i]
								if self.valid(image):
									images[level + type + MetaImage.Numbers[i]] = image

			if preference: images = self.extractSelection(selection = MetaImage.SelectionPreference, media = media, images = images, choice = choice, specific = specific, fallback = False)
			if fallback: images = self.extractSelection(selection = MetaImage.SelectionFallback, media = media, images = images, choice = choice, specific = specific)

			# Add show.xxx and season.xxx images.
			# Only do here, after preference/fallback, since we might not want to use these images as replacements.
			if data and MetaImage.Attribute in data and serie:
				levels = []
				if specific:
					if media in [MetaImage.MediaEpisode, MetaImage.MediaEpisodex, MetaImage.MediaRecap, MetaImage.MediaExtra, MetaImage.MediaSmart, MetaImage.MediaBase, MetaImage.MediaPlayer]: levels.append((MetaImage.MediaSeason, MetaImage.PrefixSeason))
					if media in [MetaImage.MediaSeason, MetaImage.MediaEpisode, MetaImage.MediaSeasonx, MetaImage.MediaEpisodex, MetaImage.MediaRecap, MetaImage.MediaExtra, MetaImage.MediaSmart, MetaImage.MediaBase, MetaImage.MediaPlayer]: levels.append((MetaImage.MediaShow, MetaImage.PrefixShow))
				else:
					if media in [MetaImage.MediaSeason, MetaImage.MediaEpisode, MetaImage.MediaSeasonx, MetaImage.MediaEpisodex, MetaImage.MediaRecap, MetaImage.MediaExtra, MetaImage.MediaSmart, MetaImage.MediaBase, MetaImage.MediaPlayer]: levels.append((MetaImage.MediaShow, MetaImage.PrefixShow))
					if media in [MetaImage.MediaEpisode, MetaImage.MediaEpisodex, MetaImage.MediaRecap, MetaImage.MediaExtra, MetaImage.MediaSmart, MetaImage.MediaBase, MetaImage.MediaPlayer]: levels.append((MetaImage.MediaSeason, MetaImage.PrefixSeason))

				if levels:
					values = data[MetaImage.Attribute]
					for level in levels:
						if level:
							if not level[0] in values: continue
							values1 = values[level[0]]
							level = level[1]
						else:
							values1 = values

						for type in MetaImage.Types:
							if type in values1:
								values2 = values1[type]
								for i in range(len(values2)):
									image = values2[i]
									if self.valid(image):
										id = level + type + MetaImage.Numbers[i]
										if not id in images or not images[id]: images[id] = image

			if recover: images = self.extractRecover(images = images)
			if limit: images = self.extractLimit(media = media, images = images)
			if default: images = self.extractDefault(images = images)
			images = self.extractClean(images = images)

			return images
		except:
			Logger.error()
			return {}

	@classmethod
	def extractRandom(self, images, media = None, index = None, type = None):
		values = []
		prefix = ''
		if not index or index == MetaImage.IndexCurrent:
			try: prefix = MetaImage.PrefixsMedia[media]
			except: prefix = ''
		else:
			try: prefix = MetaImage.PrefixsIndex[index]
			except: pass
		prefix += type
		for number in MetaImage.Numbers:

			try: values.append(images[prefix + number])
			except: pass
		if values: return Tools.listPick(Tools.listUnique(values))
		else: return None

	@classmethod
	def extractChoice(self, images, media = None, index = None, type = None, choice = None, fallback = True, alternative = True):
		if choice == MetaImage.ChoiceRandom:
			image = self.extractRandom(images = images, media = media, index = index, type = type)
			if image: return image
		else:
			if not index or index == MetaImage.IndexCurrent:
				try: prefix = MetaImage.PrefixsMedia[media]
				except: prefix = ''
			else:
				try: prefix = MetaImage.PrefixsIndex[index]
				except: pass
			prefix += type
			try: return images[prefix + MetaImage.NumbersChoice[choice]]
			except:
				try:
					# If we use ChoiceTertiary, but there are only 1 or 2 images, try ChoiceSecondary and then ChoicePrimary.
					# Eg: True Detectives (CBS 1990) - only a show psoter from IMDb.
					if alternative and choice:
						index = MetaImage.Choices.index(choice)
						if index > 0:
							for i in range(index - 1, -1, -1):
								try: return images[prefix + MetaImage.NumbersChoice[MetaImage.Choices[i]]]
								except: pass
				except: Logger.error()
		if fallback:
			try: index = MetaImage.PrefixsIndex[index]
			except: pass
			for number in MetaImage.Numbers:
				try: return images[type + number]
				except: pass
			if media == MetaImage.MediaEpisode:
				for number in MetaImage.Numbers:
					try: return images[index + type + number]
					except: pass
					try: return images[MetaImage.PrefixSeason + type + number]
					except: pass
			if media == MetaImage.MediaEpisode or media == MetaImage.MediaSeason:
				for number in MetaImage.Numbers:
					try: return images[index + type + number]
					except: pass
					try: return images[MetaImage.PrefixShow + type + number]
					except: pass
		return None

	@classmethod
	def extractSelection(self, selection, media, images, choice = None, specific = False, fallback = True):
		default = self.settingsDefault(mode = MetaImage.ModeSelection)
		for type in MetaImage.Types:
			if selection == MetaImage.SelectionPreference or not type in images:
				data = self.settingsSelection(media = media, type = type)[selection]
				if data is None:
					data = default[media][type]
				else:
					for key, value in data.items():
						if value is None: data[key] = default[media][type][key]
				if data:
					mediaCurrent = data[MetaImage.OptionMedia]
					mediaOriginal = None

					if specific and mediaCurrent == Media.Show and (media == MetaImage.MediaEpisode or media == MetaImage.MediaEpisodex or media == MetaImage.MediaRecap or media == MetaImage.MediaExtra or media == MetaImage.MediaSmart or media == MetaImage.MediaBase or media == MetaImage.MediaPlayer):
						mediaOriginal = mediaCurrent
						mediaCurrent = Media.Season

					# Allow to use a different choice than "primary" for Absolute menus.
					choose = data[MetaImage.OptionChoice]
					if choice:
						if Tools.isDictionary(choice):
							value = choice.get(type)
							if value: choose = value
						else:
							choose = choice

					image = self.extractChoice(images = images, media = mediaCurrent, index = data[MetaImage.OptionIndex], type = data[MetaImage.OptionType], choice = choose, fallback = fallback)
					if not image and specific and not mediaOriginal == mediaCurrent: image = self.extractChoice(images = images, media = mediaOriginal, index = data[MetaImage.OptionIndex], type = data[MetaImage.OptionType], choice = choose, fallback = fallback)
					if not image and mediaCurrent == media: image = self.extractChoice(images = images, index = data[MetaImage.OptionIndex], type = data[MetaImage.OptionType], choice = choose, fallback = fallback)
					if image: images[type] = image
		return images

	@classmethod
	def extractLimit(self, media, images):
		setting = self.settingsLimit()
		for type in MetaImage.Types:
			limit = self.settingsSelection(media = media, type = type)[MetaImage.SelectionGeneral][MetaImage.OptionLimit]
			if limit:
				limit = MetaImage.Limits[limit]
				if limit is None:
					limit = setting
				if limit:
					numbers = MetaImage.Numbers[limit:]
					for level in [MetaImage.PrefixShow, MetaImage.PrefixSeason, MetaImage.PrefixNone]:
						prefix = level + type
						for number in numbers:
							try: del images[prefix + number]
							except: pass
		return images

	@classmethod
	def extractRecover(self, images):
		# Try to use the next best image before using the default theme images.
		for prefix in [MetaImage.PrefixShow, MetaImage.PrefixSeason, MetaImage.PrefixPrevious, MetaImage.PrefixNext, MetaImage.PrefixNone]:
			fanart = False

			for type, defaults in MetaImage.TypesRecover.items():
				attribute1 = prefix + type
				if not attribute1 in images:
					for default in defaults:
						attribute2 = prefix + default
						if attribute2 in images and self.valid(images[attribute2]):
							images[attribute1] = images[attribute2]
							if type == MetaImage.TypeFanart: fanart = True
							break

			# If the 1st fanart image is the same as the 1st landscape image, use the 2nd best landscape image.
			# This is for landscape views (eg Aeon Nox) where both the fanart and landscape images are shown.
			# It doesn't look good if both images are the same.
			# This is already done in extract(), but we have to do it here again, since we are using replacement images.
			if fanart: # Only do this if the fanart was actually replaced.
				attribute1 = prefix + MetaImage.TypeFanart
				attribute2 = prefix + MetaImage.TypeLandscape
				if attribute1 in images and attribute2 in images and images[attribute1] and images[attribute2] and images[attribute1] == images[attribute2]:
					numbers = MetaImage.Numbers[1:]
					found = False
					for number in numbers:
						for default in MetaImage.TypesRecover[MetaImage.TypeLandscape]:
							attribute3 = prefix + default + number
							if attribute3 in images and self.valid(images[attribute3]):
								images[attribute2] = images[attribute3]
								found = True
								break
						if found: break

		return images

	@classmethod
	def extractDefault(self, images):
		if not MetaImage.TypePoster in images: images[MetaImage.TypePoster] = Theme.poster()

		# Rather use landscape image (fanart) than potrait image (poster), otherwise the image ratio between available and missing thumbnails will differ.
		# Important for sets without a thumb/fanart.
		#if not MetaImage.TypeThumb in images: images[MetaImage.TypeThumb] = Theme.thumbnail()
		if not MetaImage.TypeThumb in images: images[MetaImage.TypeThumb] = Theme.fanart()

		if not MetaImage.TypeBanner in images: images[MetaImage.TypeBanner] = Theme.banner()
		if not MetaImage.TypeFanart in images: images[MetaImage.TypeFanart] = Theme.fanart()
		if not MetaImage.TypeLandscape in images: images[MetaImage.TypeLandscape] = Theme.fanart()
		if not Theme.artwork():
			try: del images[MetaImage.TypeFanart]
			except: pass
			try: del images[MetaImage.TypeLandscape]
			except: pass
		return images

	@classmethod
	def extractClean(self, images):
		# Sometimes URLs contain a space and then do not show:
		#	error <general>: CCurlFile::Stat - <http://assets.fanart.tv/fanart/tv/75299/seasonthumb/Sopranos (3).jpg> Failed: URL using bad/illegal format or missing URL(3)
		for type, link in images.items():
			if ' ' in link: images[type] = link.replace(' ', '%20')
		return images

	@classmethod
	def _extractPoster(self, data = None, images = None, specific = False):
		posters = []
		if images:
			if specific: types = [MetaImage.TypePoster, MetaImage.PrefixSeason + MetaImage.TypePoster, MetaImage.PrefixShow + MetaImage.TypePoster]
			else: types = [MetaImage.PrefixShow + MetaImage.TypePoster, MetaImage.PrefixSeason + MetaImage.TypePoster, MetaImage.TypePoster]
			for type in types:
				for number in MetaImage.Numbers:
					try:
						prefix = type + number
						image = data[prefix]
						if self.valid(image): posters.append(image)
					except: pass
		elif data:
			if MetaImage.Attribute in data:
				if specific: types = [None, MetaImage.MediaSeason, MetaImage.MediaShow]
				else: types = [MetaImage.MediaShow, MetaImage.MediaSeason, None]
				images = data[MetaImage.Attribute]
				for type in types:
					try:
						poster = images[type][MetaImage.TypePoster] if type else images[MetaImage.TypePoster]
						if poster: posters.extend(poster)
					except: pass
		return posters

	@classmethod
	def _extractFanart(self, data = None, images = None, specific = False, default = False):
		fanarts = []
		if images:
			if specific: types = [MetaImage.TypeFanart, MetaImage.PrefixSeason + MetaImage.TypeFanart, MetaImage.PrefixShow + MetaImage.TypeFanart]
			else: types = [MetaImage.PrefixShow + MetaImage.TypeFanart, MetaImage.PrefixSeason + MetaImage.TypeFanart, MetaImage.TypeFanart]
			for type in types:
				for number in MetaImage.Numbers:
					try:
						prefix = type + number
						image = data[prefix]
						if self.valid(image): fanarts.append(image)
					except: pass
		elif data:
			if MetaImage.Attribute in data:
				if specific: types = [None, MetaImage.MediaSeason, MetaImage.MediaShow]
				else: types = [MetaImage.MediaShow, MetaImage.MediaSeason, None]
				images = data[MetaImage.Attribute]
				for type in types:
					try:
						fanart = images[type][MetaImage.TypeFanart] if type else images[MetaImage.TypeFanart]
						if fanart: fanarts.extend(fanart)
					except: pass
		if not fanarts and default: return [Theme.fanart()]
		return fanarts

	@classmethod
	def _extractBackground(self, images, specific = False, default = True):
		if default and not Theme.artwork(): return None
		if specific: types = [MetaImage.TypeFanart, MetaImage.TypeLandscape, MetaImage.PrefixSeason + MetaImage.TypeFanart, MetaImage.PrefixSeason + MetaImage.TypeLandscape, MetaImage.PrefixShow + MetaImage.TypeFanart, MetaImage.PrefixShow + MetaImage.TypeLandscape]
		else: types = [MetaImage.TypeFanart, MetaImage.TypeLandscape, MetaImage.PrefixShow + MetaImage.TypeFanart, MetaImage.PrefixShow + MetaImage.TypeLandscape, MetaImage.PrefixSeason + MetaImage.TypeFanart, MetaImage.PrefixSeason + MetaImage.TypeLandscape]
		for type in types:
			for number in MetaImage.Numbers:
				try:
					prefix = type + number
					image = images[prefix]
					if self.valid(image): return image
				except: pass
		if default: return Theme.fanart()
		return None

	###################################################################
	# IMAGE
	###################################################################

	@classmethod
	def image(self, media = None, data = None, type = None, custom = None, default = True, choice = None):
		image = self.setMedia(media = media, data = data, custom = custom, default = default, choice = choice)
		if type and image: return image.get(type)
		else: return image

	@classmethod
	def imagePoster(self, media = None, data = None, custom = None, default = True, choice = None):
		return self.image(type = MetaImage.TypePoster, media = media, data = data, custom = custom, default = default, choice = choice)

	@classmethod
	def imageFanart(self, media = None, data = None, custom = None, default = True, choice = None):
		return self.image(type = MetaImage.TypeFanart, media = media, data = data, custom = custom, default = default, choice = choice)

	###################################################################
	# SET
	###################################################################

	@classmethod
	def set(self, item = None, images = None, default = True):
		if default: images = self.extractDefault(images = images)
		if item:
			if images:
				# Most image URLs returned by Fanart's API do not return any data or headers if accessed.
				# Not sure if this is a temporary problem, but replacing the link as below works (these links are used on Fanart's website).
				# Check if movies clearlogo shows.
				# Update: Seems to have been fixed.
				'''
				for type, link in images.items():
					if 'fanart.tv/' in link:
						path = Regex.extract(data = link, expression = '.*\/(.*?)$')
						images[type] = 'https://images.fanart.tv/fanart/' + path
				'''

				# On Android (Nvidia Shield) I noticed this error once:
				#	'TypeError: argument "value" for method "setArt" must be unicode or str
				# Remove None values. In worst case, use a try-catch to prevent the error from propagating.
				try: item.setArt({k : v for k, v in images.items() if v})
				except:
					Logger.error()
					Logger.log('Failed Images: ' + str(images))

			# NB: Although deprecated, this is still used by most skins today (2022).
			# Most skins will use this value above the one from setArt().
			# If not set, skins seem to pick the one from setArt().
			if MetaImage.TypeFanart in images: fanart = images[MetaImage.TypeFanart]
			else: fanart = self._extractBackground(images = images, default = default)
			if fanart: item.setProperty('Fanart_Image', fanart)

		return images

	@classmethod
	def _set(self, media, data, item, default = True, show = None, season = None, episode = True, previous = True, next = True, choice = None, specific = None, function = None):
		images = {}
		if data: # No data for exact searches.
			if show is None: show = self.settingsFallback(media = media, fallback = MetaImage.MediaShow)
			if season is None: season = self.settingsFallback(media = media, fallback = MetaImage.MediaSeason)

			images = self.extract(media = media, data = data, default = False, show = show, season = season, episode = episode, previous = previous, next = next, choice = choice, specific = specific)

			images = self.replaceThumbnail(images = images)
			if media == MetaImage.MediaRecap or media == MetaImage.MediaExtra: images = self.replacePoster(images = images, force = True)
			if media == MetaImage.MediaSmart or media == MetaImage.MediaBase or media == MetaImage.MediaPlayer: images = self.replaceSeason(images = images)
			if function: function(images)

			# Delete the poster for episode menus.
			# Otherwise many skins (eg: Estaury), the Kore remote app, and the info dialog, will use this instead of the thumbnail.
			# Most skins will automatically use the season.poster or tvshow.poster if a poster (instead of a thumbnail) has to be displayed.
			# NB: Do not delete the image, otherwise it will be replaced by the gaia default in set().
			# Update (2025-04): Aslo do for recaps/extras so that the season poster + thumbnail are displayed in the info dialog.
			if media == MetaImage.MediaEpisode or media == MetaImage.MediaEpisodex or media == MetaImage.MediaRecap or media == MetaImage.MediaExtra: images['poster'] = None

		if item: self.set(images = images, item = item, default = default)
		return images

	@classmethod
	def setMedia(self, media = None, data = None, item = None, default = True, custom = None, show = None, season = None, episode = True, previous = True, next = True, choice = None, specific = None):
		if not media and data: media = data.get('media')

		if media == MetaImage.MediaMovie: return self.setMovie(data = data, item = item, default = default, choice = choice, specific = specific)
		elif media == MetaImage.MediaSet: return self.setSet(data = data, item = item, default = default, choice = choice, specific = specific)
		elif media == MetaImage.MediaShow: return self.setShow(data = data, item = item, default = default, choice = choice, specific = specific)
		elif media == MetaImage.MediaSeason: return self.setSeason(data = data, item = item, default = default, custom = custom, show = show, choice = choice, specific = specific)
		elif media == MetaImage.MediaEpisode: return self.setEpisode(data = data, item = item, default = default, custom = custom, show = show, season = season, episode = episode, previous = previous, next = next, choice = choice, specific = specific)
		elif media == MetaImage.MediaRecap: return self.setRecap(data = data, item = item, default = default, choice = choice, specific = specific)
		elif media == MetaImage.MediaExtra: return self.setExtra(data = data, item = item, default = default, choice = choice, specific = specific)

		return None

	@classmethod
	def setMovie(self, data, item = None, default = True, choice = None, specific = None):
		return self._set(media = MetaImage.MediaMovie, data = data, item = item, default = default, choice = choice, specific = specific)

	@classmethod
	def setSet(self, data, item = None, default = True, choice = None, specific = None):
		return self._set(media = MetaImage.MediaSet, data = data, item = item, default = default, choice = choice, specific = specific)

	@classmethod
	def setShow(self, data, item = None, default = True, choice = None, specific = None):
		return self._set(media = MetaImage.MediaShow, data = data, item = item, default = default, choice = choice, specific = specific)

	@classmethod
	def setSeason(self, data, item = None, default = True, custom = None, show = None, choice = None, specific = None):
		if custom: media = custom
		else: media = MetaImage.MediaSeasonx if int(data['season']) == 0 else MetaImage.MediaSeason
		return self._set(media = media, data = data, item = item, default = default, show = show, choice = choice, specific = specific)

	@classmethod
	def setEpisode(self, data, item = None, default = True, custom = None, show = None, season = None, episode = True, previous = True, next = True, choice = None, specific = None):
		if custom: media = custom
		elif int(data['season']) == 0: media = MetaImage.MediaEpisodex
		else: media = MetaImage.MediaEpisode

		if specific and season is None: season = True

		return self._set(media = media, data = data, item = item, default = default, show = show, season = season, episode = episode, previous = previous, next = next, choice = choice, specific = specific)

	@classmethod
	def setRecap(self, data, item = None, default = True, show = True, season = True, episode = True, choice = None, specific = None):
		return self._set(media = MetaImage.MediaRecap, data = data, item = item, default = default, show = show, season = season, episode = episode, choice = choice, specific = specific)

	@classmethod
	def setExtra(self, data, item = None, default = True, show = True, season = True, episode = True, choice = None, specific = None):
		return self._set(media = MetaImage.MediaExtra, data = data, item = item, default = default, show = show, season = season, episode = episode, choice = choice, specific = specific)

	@classmethod
	def setUpNext(self, data, item = None, default = True, choice = None, specific = None):
		return self._set(media = MetaImage.MediaEpisode, data = data, item = item, default = default, previous = False, next = False, choice = choice, specific = specific, function = lambda images : self.replace(images = images, missing = MetaImage.PrefixShow + MetaImage.TypeLandscape, replacement = MetaImage.PrefixShow + MetaImage.TypeThumb, all = False, force = True))
