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

from lib.modules.database import Database
from lib.modules.concurrency import Pool, Lock
from lib.modules.tools import Media, Time, Tools, Math, Language, Country, Converter, Logger, File, System, Settings
from lib.modules.compression import Compression
from lib.modules.cache import Memory
from lib.meta.tools import MetaTools

class MetaCache(Database):

	Name					= Database.NameMetadata

	Attribute				= 'cache'
	AttributeRefresh		= 'refresh'
	AttributeStatus			= 'status'
	AttributeTime			= 'time'
	AttributeSettings		= 'settings'
	AttributePart			= 'part'
	AttributeFail			= 'fail'
	AttributeCause			= 'cause'
	AttributeValid			= 'valid'
	AttributeLog			= 'log'
	AttributeSeason			= Media.Season

	TypeMovie				= Media.Movie
	TypeSet					= Media.Set
	TypeShow				= Media.Show
	TypeSeason				= Media.Season
	TypeEpisode				= Media.Episode
	TypePack				= Media.Pack
	TypeBulk				= 'bulk'
	Types					= [TypeMovie, TypeSet, TypeShow, TypeSeason, TypeEpisode, TypePack] # Do not add bulk, since it does not use the same structure as the other tables.

	RefreshNone				= None
	RefreshForeground		= 'foreground'
	RefreshBackground		= 'background'
	RefreshDisabled			= 'disabled'

	StatusCurrent			= 'current'		# Available in database and is still new.
	StatusReleased			= 'released'	# Available in database, but was recently released and needs a background refresh.
	StatusOutdated			= 'outdated'	# Available in database, but the previous refresh was before the release date and therefore needs a foreground/background refresh.
	StatusAntiquated		= 'antiquated'	# Available in database, but is somewhat old and needs a background refresh.
	StatusObsolete			= 'obsolete'	# Available in database, but is very old and needs a foreground refresh.
	StatusPartial			= 'partial'		# Available in database, but some providers have entire chunks of missing metadata and needs a background refresh.
	StatusIncomplete		= 'incomplete'	# Available in database, but some individual metadata attributes are missing and needs a background refresh.
	StatusSettings			= 'settings'	# Available in database, but with a different settings configuration.
	StatusExternal			= 'external'	# Available in external preprocessed database, but might be outdated or not according to the user's settings and therefore needs a background refresh.
	StatusInvalid			= 'invalid'		# Not in database at all.
	StatusMemory			= 'memory'		# Available from memory from a previous call. Can be retrieved without database access, but is only available during the same Python process.
	StatusValid				= [StatusCurrent, StatusReleased, StatusOutdated, StatusAntiquated, StatusObsolete, StatusPartial, StatusIncomplete, StatusMemory]

	ReleasePrimary			= 'primary'
	ReleaseSecondary		= 'secondary'
	ReleaseTertiary			= 'tertiary'
	ReleaseIncomplete		= 'incomplete'
	ReleaseOutdated			= 'outdated'

	# Refresh more frequently the higher the level.
	ReleaseLevelNone		= None
	ReleaseLevel0			= 0 # Very infrequent refreshes.
	ReleaseLevel1			= 1
	ReleaseLevel2			= 2
	ReleaseLevel3			= 3
	ReleaseLevel4			= 4
	ReleaseLevel5			= 5 # Very frequent refreshes.

	#gaairemove - still need these?
	IncompleteNone			= ReleaseLevelNone	# The metadata is complete without any incomplete attributes and no refresh is needed.
	IncompleteMinor			= ReleaseLevel0		# Some minor/unimportant metadata attributes are missing, which do not affect any core functionality and do not require immediate refreshing.
	IncompleteMajor			= ReleaseLevel1		# Some major/important metadata attributes are missing, which affect core functionality and requires immediate refreshing.

	PeriodPast				= 'past'			# The metadata of all episodes for a show/season have been published, with all episodes having aired in the past. Eg: show/season has ended and all episodes have aired.
	PeriodPresent			= 'present'			# The metadata of all episodes for a show/season have been published, but some episodes are still unaired (in the future). Eg: show/season is continuing with some episodes unaired.
	PeriodFuture			= 'future'			# The metadata of all/some episodes for a show/season have not been published yet. Eg: show/season is continuing and new episodes are added on a weekly basis.

	IntervalWeekly			= Media.Weekly		# One episode released per week. Some weeks might not have a release (eg public holidays) and some weeks might have multiple releases (eg double finales).
	IntervalDaily			= Media.Daily		# One episode released per weekday. Some days might not have a release (eg public holidays) and some weeks might have multiple releases (eg specials during certain events).
	IntervalInstantly		= Media.Instantly	# All episodes of a season are released at once.
	IntervalQuickly			= Media.Quickly		# All episodes of a season are almost released at once, over just a few days.
	IntervalBatchly			= Media.Batchly		# Seasons are divided into smaller subgroups and all episodes within a group are released at once.
	IntervalOtherly			= Media.Otherly		# Other types of releases.

	TimeNone				= None
	TimeZero				= 0
	TimeMinute5				= 300
	TimeMinute10			= 600
	TimeMinute15			= 900
	TimeMinute20			= 1200
	TimeMinute25			= 1500
	TimeMinute30			= 1800
	TimeMinute35			= 2100
	TimeMinute40			= 2400
	TimeMinute45			= 2700
	TimeMinute50			= 3000
	TimeMinute55			= 3300
	TimeMinute60			= 3600
	TimeHour1				= 3600
	TimeHour2				= 7200
	TimeHour3				= 10800
	TimeHour4				= 14400
	TimeHour5				= 18000
	TimeHour6				= 21600
	TimeHour7				= 25200
	TimeHour8				= 28800
	TimeHour9				= 32400
	TimeHour10				= 36000
	TimeHour11				= 39600
	TimeHour12				= 43200
	TimeHour13				= 46800
	TimeHour14				= 50400
	TimeHour15				= 54000
	TimeHour16				= 57600
	TimeHour17				= 61200
	TimeHour18				= 64800
	TimeHour19				= 68400
	TimeHour20				= 72000
	TimeHour21				= 75600
	TimeHour22				= 79200
	TimeHour23				= 82800
	TimeHour24				= 86400
	TimeDay1				= 86400
	TimeDay2				= 172800
	TimeDay3				= 259200
	TimeDay4				= 345600
	TimeDay5				= 432000
	TimeDay6				= 518400
	TimeDay7				= 604800
	TimeDay8				= 691200
	TimeDay9				= 777600
	TimeDay10				= 864000
	TimeDay11				= 950400
	TimeDay12				= 1036800
	TimeDay13				= 1123200
	TimeDay14				= 1209600
	TimeWeek1				= 604800
	TimeWeek2				= 1209600
	TimeWeek3				= 1814400
	TimeWeek4				= 2419200
	TimeWeek5				= 3024000
	TimeWeek6				= 3628800
	TimeWeek7				= 4233600
	TimeWeek8				= 4838400
	TimeWeek9				= 5443200
	TimeWeek10				= 6048000
	TimeMonth1				= 2628000
	TimeMonth2				= 5256000
	TimeMonth3				= 7884000
	TimeMonth4				= 10512000
	TimeMonth5				= 13140000
	TimeMonth6				= 15768000
	TimeMonth7				= 18396000
	TimeMonth8				= 21024000
	TimeMonth9				= 23652000
	TimeMonth10				= 26280000
	TimeMonth11				= 28908000
	TimeMonth12				= 31536000
	TimeYear1				= 31557600
	TimeYear1_5				= 47336400
	TimeYear2				= 63115200
	TimeYear2_5				= 78894000
	TimeYear3				= 94672800
	TimeYear3_5				= 110451600
	TimeYear4				= 126230400
	TimeYear4_5				= 142009200
	TimeYear5				= 157788000
	TimeYear10				= 315576000

	# At which point a title is considered to be old, based on the premiere date.
	# Old titles are refreshed slightly less than newer titles, since their metadata will change little, including ratings.
	TimeOld					= (TimeYear5, TimeYear10)	# (Oldish releases, Old releases)

	# When the data is somewhat old and should be refreshed in the background while the old cached data is still returned and displayed.
	# 1 month causes too many refreshes, especially from the smart menus.
	# 2 months is acceptable, but maybe still slightly to low, as it might refresh up to 6 times per year
	# Newer releases are in any case refreshed more often using the TimeRelease brackets.
	TimeAntiquated			= (TimeMonth2, TimeMonth3, TimeMonth4)	# (New releases, Oldish releases, Old releases)

	# When the data is very old and should be forcefully refreshed even if there is old cached data, since the metadata is too outdated to still be considered valid.
	# Keep this at a very long time, since one can always show the new data by reloading the menu after it was refreshed in the background.
	TimeObsolete			= (TimeYear1, TimeYear2, TimeYear3)	# (New releases, Oldish releases, Old releases)

	# Regular refreshes of new releases.
	TimeReleaseRegular1		= (
								# Standard Refreshes [Number of refreshes over 2 months | Avg: 7 or less | Max: 8-12]
								# Refreshes once every 2-5 days during the first two weeks of release, and once every 9-14 days during the next two months.

								# Future 2 Weeks [Refreshes | Avg: 1 | Max: 2]
								# Occasionally refresh titles released in the next few weeks, so the hopefully up-to-date metadata is ready on the day of release.
								# Use a long timeout, since future releases mostly have incomplete metadata, and refreshing too often is a waste of resources.
								(-TimeWeek2	,	TimeDay8),		# 0-14 days		: 8 days

								# Past 1 Week [Refreshes | Avg: 2 | Max: 2-3]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								(TimeWeek1	,	TimeDay3),		# 0-7 days		: 3 days

								# Past 2 Weeks [Refreshes | Avg: 1 | Max: 1-2]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								# Use a medium timeout, since the metadata will probably have been refreshed during the previous bracket.
								(TimeWeek2	,	TimeDay5),		# 7-14 days		: 5 days

								# Past 1 Month [Refreshes | Avg: 1 | Max: 1-2]
								# Occasionally refresh titles to get newer metadata, such as ratings, and other attributes which might only become available after a few weeks.
								# Use a long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek4	,	TimeDay10),		# 14-28 days	: 10 days

								# Past 2 Months [Refreshes | Avg: 2 | Max: 2-3]
								# Occasionally refresh titles to get new metadata, such as ratings, and other attributes which might only become available after a month.
								# Use a very long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek8	,	TimeWeek2),		# 28-56 days	: 14 days
							)
	TimeReleaseRegular2		= (
								# Standard Refreshes [Number of refreshes over 2 months | Avg: 6 or less | Max: 6-10]
								# Refreshes once every 3-5 days during the first two weeks of release, and once every 10-21 days during the next two months.

								# Future 2 Weeks [Refreshes | Avg: 1 | Max: 1-2]
								# Occasionally refresh titles released in the next few weeks, so the hopefully up-to-date metadata is ready on the day of release.
								# Use a long timeout, since future releases mostly have incomplete metadata, and refreshing too often is a waste of resources.
								(-TimeWeek2	,	TimeDay10),		# 0-14 days		: 10 days

								# Past 1 Week [Refreshes | Avg: 2 | Max: 2]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								(TimeWeek1	,	TimeDay4),		# 0-7 days		: 4 days

								# Past 2 Weeks [Refreshes | Avg: 1 | Max: 1-2]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								# Use a medium timeout, since the metadata will probably have been refreshed during the previous bracket.
								(TimeWeek2	,	TimeDay7),		# 7-14 days		: 7 days

								# Past 1 Month [Refreshes | Avg: 1 | Max: 1-2]
								# Occasionally refresh titles to get newer metadata, such as ratings, and other attributes which might only become available after a few weeks.
								# Use a long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek4	,	TimeWeek2),		# 14-28 days	: 14 days

								# Past 2 Months [Refreshes | Avg: 1 | Max: 1-2]
								# Occasionally refresh titles to get new metadata, such as ratings, and other attributes which might only become available after a month.
								# Use a very long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek8	,	TimeWeek3),		# 28-56 days	: 21 days
							)
	TimeReleaseRegular3		= (
								# Standard Refreshes [Number of refreshes over 2 months | Avg: 5 or less | Max: 5-8]
								# Refreshes once every 4-7 days during the first two weeks of release, and once every 14-21 days during the next two months.

								# Future 2 Weeks [Refreshes | Avg: 1 | Max: 1-2]
								# Occasionally refresh titles released in the next few weeks, so the hopefully up-to-date metadata is ready on the day of release.
								# Use a long timeout, since future releases mostly have incomplete metadata, and refreshing too often is a waste of resources.
								(-TimeWeek2	,	TimeDay12),		# 0-14 days		: 12 days

								# Past 1 Week [Refreshes | Avg: 1 | Max: 1-2]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								(TimeWeek1	,	TimeDay5),		# 0-7 days		: 5 days

								# Past 2 Weeks [Refreshes | Avg: 1 | Max: 1]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								# Use a medium timeout, since the metadata will probably have been refreshed during the previous bracket.
								(TimeWeek2	,	TimeDay10),		# 7-14 days		: 10 days

								# Past 1 Month [Refreshes | Avg: 1 | Max: 1]
								# Occasionally refresh titles to get newer metadata, such as ratings, and other attributes which might only become available after a few weeks.
								# Use a long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek4	,	TimeWeek3),		# 14-28 days	: 21 days

								# Past 2 Months [Refreshes | Avg: 1 | Max: 1-2]
								# Occasionally refresh titles to get new metadata, such as ratings, and other attributes which might only become available after a month.
								# Use a very long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek8	,	TimeWeek4),		# 28-56 days	: 28 days
							)
	TimeReleaseRegular4		= (
								# Standard Refreshes [Number of refreshes over 2 months | Avg: 4 or less | Max: 5-7]
								# Refreshes once every 4-10 days during the first two weeks of release, and once every 21 days during the next two months.

								# Future 2 Weeks [Refreshes | Avg: 1 | Max: 1-2]
								# Occasionally refresh titles released in the next few weeks, so the hopefully up-to-date metadata is ready on the day of release.
								# Use a long timeout, since future releases mostly have incomplete metadata, and refreshing too often is a waste of resources.
								(-TimeWeek2	,	TimeWeek2),		# 0-14 days		: 14 days

								# Past 1 Week [Refreshes | Avg: 1 | Max: 1-2]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								(TimeWeek1	,	TimeDay7),		# 0-7 days		: 7 days

								# Past 2 Weeks [Refreshes | Avg: 0 | Max: 1]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								# Use a medium timeout, since the metadata will probably have been refreshed during the previous bracket.
								(TimeWeek2	,	TimeDay12),		# 7-14 days		: 12 days

								# Past 1 Month [Refreshes | Avg: 1 | Max: 1]
								# Occasionally refresh titles to get newer metadata, such as ratings, and other attributes which might only become available after a few weeks.
								# Use a long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek4	,	TimeWeek4),		# 14-28 days	: 28 days

								# Past 2 Months [Refreshes | Avg: 1 | Max: 1]
								# Occasionally refresh titles to get new metadata, such as ratings, and other attributes which might only become available after a month.
								# Use a very long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek8	,	TimeWeek5),		# 28-56 days	: 35 days
							)
	TimeReleaseRegular5		= (
								# Standard Refreshes [Number of refreshes over 2 months | Avg: 3 or less | Max: 5-6]
								# Refreshes once every 7-14 days during the first two weeks of release, and once every 21-42 days during the next two months.

								# Future 2 Weeks [Refreshes | Avg: 1 | Max: 1-2]
								# Occasionally refresh titles released in the next few weeks, so the hopefully up-to-date metadata is ready on the day of release.
								# Use a long timeout, since future releases mostly have incomplete metadata, and refreshing too often is a waste of resources.
								(-TimeWeek2	,	TimeWeek2),		# 0-14 days		: 14 days

								# Past 1 Week [Refreshes | Avg: 1 | Max: 1]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								(TimeWeek1	,	TimeDay10),		# 0-7 days		: 10 days

								# Past 2 Weeks [Refreshes | Avg: 0 | Max: 1]
								# Regularly refresh titles recently released, since newer metadata, such as ratings, might be available within the first week.
								# This will only trigger if the metadata is requested within a week of release, and also serves as a fallback if no refresh occurred during the previous release bracket.
								# Use a medium timeout, since the metadata will probably have been refreshed during the previous bracket.
								(TimeWeek2	,	TimeWeek2),		# 7-14 days		: 14 days

								# Past 1 Month [Refreshes | Avg: 0 | Max: 1]
								# Occasionally refresh titles to get newer metadata, such as ratings, and other attributes which might only become available after a few weeks.
								# Use a long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek4	,	TimeWeek5),		# 14-28 days	: 35 days

								# Past 2 Months [Refreshes | Avg: 1 | Max: 1]
								# Occasionally refresh titles to get new metadata, such as ratings, and other attributes which might only become available after a month.
								# Use a very long timeout, since little metadata will probably change at this point, and refreshing too often is a waste of resources.
								(TimeWeek8	,	TimeWeek6),		# 28-56 days	: 42 days
							)

	# Occasional refreshes of new releases.
	TimeReleaseOccasional1	= (
								# Occasional Refreshes [Number of refreshes over 2 months | Avg: 4 or less | Max: 5-9]

								# Future 1 Week [Refreshes | Avg: 1 | Max: 1-2]
								(-TimeDay7	,	TimeDay7),		# 0-7 days		: 7 days

								# Past 7 Days [Refreshes | Avg: 1 | Max: 1-2]
								(TimeDay7	,	TimeDay7),		# 0-7 days		: 7 days

								# Past 2 Weeks [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek2	,	TimeDay10),		# 7-14 days		: 10 days

								# Past 1 Month [Refreshes | Avg: 1 | Max: 1-2]
								(TimeWeek4	,	TimeWeek2),		# 14-28 days	: 14 days

								# Past 2 Months [Refreshes | Avg: 1 | Max: 1-2]
								(TimeWeek8	,	TimeWeek4),		# 28-56 days	: 28 days
							)
	TimeReleaseOccasional2	= (
								# Occasional Refreshes [Number of refreshes over 2 months | Avg: 3 or less | Max: 5-6]

								# Future 1 Week [Refreshes | Avg: 0 | Max: 1]
								(-TimeDay7	,	TimeDay10),		# 0-7 days		: 10 days

								# Past 7 Days [Refreshes | Avg: 1 | Max: 1-2]
								(TimeDay7	,	TimeDay7),		# 0-7 days		: 7 days

								# Past 2 Weeks [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek2	,	TimeWeek2),		# 7-14 days		: 14 days

								# Past 1 Month [Refreshes | Avg: 1 | Max: 1]
								(TimeWeek4	,	TimeWeek3),		# 14-28 days	: 21 days

								# Past 2 Months [Refreshes | Avg: 1 | Max: 1]
								(TimeWeek8	,	TimeWeek5),		# 28-56 days	: 35 days
							)
	TimeReleaseOccasional3	= (
								# Occasional Refreshes [Number of refreshes over 2 months | Avg: 2 or less | Max: 5-6]

								# Future 1 Week [Refreshes | Avg: 0 | Max: 1]
								(-TimeDay7	,	TimeWeek2),		# 0-7 days		: 14 days

								# Past 7 Days [Refreshes | Avg: 1 | Max: 1-2]
								(TimeDay7	,	TimeDay7),		# 0-7 days		: 7 days

								# Past 2 Weeks [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek2	,	TimeWeek3),		# 7-14 days		: 21 days

								# Past 1 Month [Refreshes | Avg: 1 | Max: 1]
								(TimeWeek4	,	TimeWeek4),		# 14-28 days	: 28 days

								# Past 2 Months [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek8	,	TimeWeek6),		# 28-56 days	: 42 days
							)
	TimeReleaseOccasional4	= (
								# Occasional Refreshes [Number of refreshes over 2 months | Avg: 1 or less | Max: 5 or less]

								# Future 1 Week [Refreshes | Avg: 0 | Max: 1]
								(-TimeDay7	,	TimeWeek3),		# 0-7 days		: 21 days

								# Past 7 Days [Refreshes | Avg: 1 | Max: 1]
								(TimeDay7	,	TimeDay10),		# 0-7 days		: 10 days

								# Past 2 Weeks [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek2	,	TimeWeek4),		# 7-14 days		: 28 days

								# Past 1 Month [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek4	,	TimeWeek5),		# 14-28 days	: 35 days

								# Past 2 Months [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek8	,	TimeWeek7),		# 28-56 days	: 49 days
							)
	TimeReleaseOccasional5	= (
								# Occasional Refreshes [Number of refreshes over 2 months | Avg: 1 or less | Max: 5 or less]

								# Future 1 Week [Refreshes | Avg: 0 | Max: 1]
								(-TimeDay7	,	TimeWeek3),		# 0-7 days		: 21 days

								# Past 7 Days [Refreshes | Avg: 1 | Max: 1]
								(TimeDay7	,	TimeDay12),		# 0-7 days		: 12 days

								# Past 2 Weeks [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek2	,	TimeWeek4),		# 7-14 days		: 28 days

								# Past 1 Month [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek4	,	TimeWeek6),		# 14-28 days	: 42 days

								# Past 2 Months [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek8	,	TimeWeek8),		# 28-56 days	: 56 days
							)

	# Rare refreshes of new releases.
	TimeReleaseRare1		= (
								# Rare Refreshes (Primary) [Number of refreshes over 2 months | Avg: 2 | Max: 2-3]
								# Past 4 Weeks [Refreshes | Avg: 2 | Max: 2-3]
								(TimeWeek4	,	TimeWeek2),		# 0-28 days		: 14 days
							)
	TimeReleaseRare2		= (
								# Rare Refreshes (Secondary) [Number of refreshes over 2 months | Avg: 1 | Max: 1-2]
								# Past 4 Weeks [Refreshes | Avg: 1 | Max: 1-2]
								(TimeWeek4	,	TimeWeek3),		# 0-28 days		: 21 days
							)
	TimeReleaseRare3		= (
								# Rare Refreshes (Tertiary) [Number of refreshes over 2 months | Avg: 1 | Max: 1-2]
								# Past 4 Weeks [Refreshes | Avg: 1 | Max: 1-2]
								(TimeWeek4	,	TimeWeek4),		# 0-28 days		: 28 days
							)
	TimeReleaseRare4		= (
								# Rare Refreshes (Quaternary) [Number of refreshes over 2 months | Avg: 0 | Max: 1]
								# Past 4 Weeks [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek4	,	TimeWeek5),		# 0-28 days		: 35 days
							)
	TimeReleaseRare5		= (
								# Rare Refreshes (Quinary) [Number of refreshes over 2 months | Avg: 0 | Max: 1]
								# Past 4 Weeks [Refreshes | Avg: 0 | Max: 1]
								(TimeWeek4	,	TimeWeek6),		# 0-28 days		: 42 days
							)

	# Additional refreshes if some essential metadata is missing.
	# Some movies might have missing home release dates which are needed for the Arrivals menu to move them closer to the top.
	# Certain dates might be missing, because those dates might not be known early on and are only published later, or a movie gets a very late, maybe unplanned, digital/physical release more than a year later.
	# There might also be a season missing in the seasons metadata, or an episode missing in the episodes or pack metadata.
	# Add future releases, hoping that the new metadata is available at least a few days before release.
	TimeReleaseIncomplete1 	= (
								# Future
								(-TimeDay1	,	TimeDay1),		# 0-1 days		: 1 day

								# Past
								(TimeDay1	,	TimeHour18),	# 0-1 days		: 18 hours (keep below 1 day, in case a future refresh was done recently and did not return the complete data)
								(TimeDay3	,	TimeDay1),		# 1-3 days		: 1 day
								(TimeDay7	,	TimeDay2),		# 4-7 days		: 2 days
								(TimeWeek2	,	TimeDay3),		# 1-2 weeks		: 3 days
								(TimeWeek3	,	TimeDay5),		# 2-3 weeks		: 5 days
								(TimeWeek4	,	TimeDay7),		# 3-4 weeks		: 7 days
								(TimeMonth2	,	TimeDay10),		# 1-2 months	: 10 days
								(TimeMonth3	,	TimeWeek2),		# 2-3 months	: 14 days
								(TimeMonth6	,	TimeWeek3),		# 3-6 months	: 21 days
								(TimeYear1	,	TimeWeek4),		# 6-12 months	: 28 days
								(TimeYear2	,	TimeWeek7),		# 12-24 months	: 49 days
							)
	TimeReleaseIncomplete2 	= (
								# Future
								(-TimeDay1	,	TimeDay2),		# 0-1 days		: 2 days

								# Past
								(TimeDay1	,	TimeDay1),		# 0-1 days		: 1 day (keep below 2 days, in case a future refresh was done recently and did not return the complete data)
								(TimeDay3	,	TimeDay2),		# 1-3 days		: 2 days
								(TimeDay7	,	TimeDay3),		# 4-7 days		: 3 days
								(TimeWeek2	,	TimeDay5),		# 1-2 weeks		: 5 days
								(TimeWeek3	,	TimeDay7),		# 2-3 weeks		: 7 days
								(TimeWeek4	,	TimeDay10),		# 3-4 weeks		: 10 days
								(TimeMonth2	,	TimeWeek2),		# 1-2 months	: 14 days
								(TimeMonth3	,	TimeWeek3),		# 2-3 months	: 21 days
								(TimeMonth6	,	TimeWeek4),		# 3-6 months	: 28 days
								(TimeYear1	,	TimeWeek5),		# 6-12 months	: 35 days
								(TimeYear2	,	TimeWeek7),		# 12-24 months	: 49 days
							)
	TimeReleaseIncomplete3 	= (
								# Future
								(-TimeDay1	,	TimeDay3),		# 0-1 days		: 3 days

								# Past
								(TimeDay1	,	TimeDay2),		# 0-1 days		: 2 days (keep below 3 days, in case a future refresh was done recently and did not return the complete data)
								(TimeDay3	,	TimeDay3),		# 1-3 days		: 3 days
								(TimeDay7	,	TimeDay5),		# 4-7 days		: 5 days
								(TimeWeek2	,	TimeDay7),		# 1-2 weeks		: 7 days
								(TimeWeek3	,	TimeDay10),		# 2-3 weeks		: 10 days
								(TimeWeek4	,	TimeWeek2),		# 3-4 weeks		: 14 days
								(TimeMonth2	,	TimeWeek3),		# 1-2 months	: 21 days
								(TimeMonth3	,	TimeWeek4),		# 2-3 months	: 28 days
								(TimeMonth6	,	TimeWeek5),		# 3-6 months	: 35 days
								(TimeYear1	,	TimeWeek6),		# 6-12 months	: 42 days
								(TimeYear2	,	TimeWeek7),		# 12-24 months	: 49 days
							)

	# NB: The first value is not the age of the release (like with other time brackets above), but the time since the metadata was refresh the last time.
	# Hence, the metadata is ONLY refreshed if a new movie/show release date occurred or a new season/episode was aired AFTER the date of the previous metadata refresh.
	# These brackets should only be triggered once per release date, since if the metadata is refreshed, the new timestamp in the database is greater than the release date, and will therefore not be refreshed again.
	# The only exception to this is that if the metadata is refreshed, it might now contain new/updated dates which are different to the dates in the old metadata, therefore causing a possible second refresh later on. But this should rarely happen.
	# If the 2nd value is greater-equal to the 1st value, it will prevent a refresh during the period of the 1st value.
	# This is useful to prevent too frequent refreshes, in case there is a bug or if the dates changed from the previous refresh.
	TimeReleaseOutdated1 	= (
								(TimeDay1	,	TimeDay1),	# 0-1 days (since last refresh, after latest release)	: 1 day
								(TimeNone	,	TimeDay1),	# 1+ days (since last refresh, after latest release)	: 1 day
							)
	TimeReleaseOutdated2 	= (
								# Since this is used by weekly shows, make it just above 1/2 of a week, aka 4 days.
								(TimeDay1	,	TimeDay1),	# 0-1 days (since last refresh, after latest release)	: 1 day
								(TimeNone	,	TimeDay4),	# 1+ days (since last refresh, after latest release)	: 4 days
							)
	TimeReleaseOutdated3 	= (
								# Since this is used by daily shows, make it as high as possible, but still allow at least one refresh per week.
								(TimeDay1	,	TimeDay1),	# 0-1 days (since last refresh, after latest release)	: 1 day
								(TimeNone	,	TimeDay6),	# 1+ days (since last refresh, after latest release)	: 6 days
							)

	TimeReleaseMovie		= {
								# Movies are relatively lightweight, requiring a maximum of 9 requests for extended metadata.
								# Movies can therefore be refreshed more frequently without impacting servers or processing too much.

								# LEVELS:
								#	The levels for the brackets are based slightly on the release period (past/present/future), but mainly on the release date.
								#	Older releases therefore have a lower level than present or future releases.
								#		Level0: Released a long time ago.
								#		Level1: Released a while ago or to be released far into the future.
								#		Level2: Recently released or soon to be released.

								# Premiere release dates.
								# Refresh most frequently, since a lot of metadata might change around the premiere release.
								ReleasePrimary : [
									TimeReleaseRegular3,	# Released a long time ago.
									TimeReleaseRegular2,	# Released a while ago or to be released far into the future.
									TimeReleaseRegular1,	# Recently released or soon to be released.
								],

								# Limited/theatrical release dates.
								# Refresh slightly less frequently, since the metadata should mostly be complete from the premiere refreshes.
								ReleaseSecondary : [
									TimeReleaseRegular4,	# Released a long time ago.
									TimeReleaseRegular3,	# Released a while ago or to be released far into the future.
									TimeReleaseRegular2,	# Recently released or soon to be released.
								],

								# Digital/physical/television release dates.
								# Refresh even less frequently, since the metadata should mostly be complete from the premiere/limited/theatrical refreshes.
								# Refreshes are only needed to get the latest ratings/votes and home release dates, which are often only added shortly before the home release.
								ReleaseTertiary : [
									TimeReleaseRegular4,	# Released a long time ago.
									TimeReleaseRegular3,	# Released a while ago or to be released far into the future.
									TimeReleaseRegular2,	# Recently released or soon to be released.
								],

								# If the title, plot, home release dates, rating, or poster is missing.
								# Refresh to hopefully get the new dates and other attributes.
								# Do not refresh too frequently, since some lower-budget movies might never get a home release date and only have a premiere date.
								# The period is applied to the most recent release date of all available dates in the past.
								ReleaseIncomplete : [
									TimeReleaseIncomplete3,	# The rating or poster is missing.
									TimeReleaseIncomplete2,	# The title, plot, or ALL home release dates (digital/physical/television) are missing.
								],

								# If the previous refresh was done BEFORE the latest release date, and the latest release date is in the PAST.
								# Hence, this forces an immediate refresh if the current time progressed beyond a release date, irrespective of the time that elapsed between the release date and now.
								# This should only be triggered ONCE after each release date, since the timestamp in the database is updated to the current time on refresh, preventing any future refreshes (except if a release date changes or another release date has passed).
								# NB: Note that the 1st value in the outdated brackets are the age since the last REFRESH, and not the age of the RELEASE date (like with other brackets).
								ReleaseOutdated : [
									TimeReleaseOutdated1,	# Any past release date is after the previous refresh.
								],
							}

	TimeReleaseSet			= {
								# Sets are very lightweight, requiring a maximum of 3 requests for extended metadata.
								# Sets can therefore be refreshed very frequently without impacting servers or processing.
								# Sets will use the dates of their individual movies/parts.

								# LEVELS:
								#	The levels for the brackets are based slightly on the release period (past/present/future), but mainly on the release date of the newest movie in the set.
								#	Older releases therefore have a lower level than present or future releases.
								#	Release dates are from the most recent movie added to the collection.
								#		Level0: Released a long time ago.
								#		Level1: Released a while ago or to be released far into the future.
								#		Level2: Recently released or soon to be released.

								# Premiere release dates.
								# Refresh most frequently, since a lot of metadata might change around the premiere release.
								ReleasePrimary : [
									TimeReleaseRegular3,	# Released a long time ago.
									TimeReleaseRegular2,	# Released a while ago or to be released far into the future.
									TimeReleaseRegular1,	# Recently released or soon to be released.
								],

								# Limited/theatrical release dates.
								# Refresh slightly less frequently, since the metadata should mostly be complete from the premiere refreshes.
								# This should not be triggered, since the individual movies/parts directly inside the set metadata only have the premiere date.
								# Except if one of th emovies appears in Arrivals and might therefore have additional dates.
								ReleaseSecondary : [
									TimeReleaseRegular4,	# Released a long time ago.
									TimeReleaseRegular3,	# Released a while ago or to be released far into the future.
									TimeReleaseRegular2,	# Recently released or soon to be released.
								],

								# Digital/physical/television release dates.
								# Refresh even less frequently, since the metadata should mostly be complete from the premiere/limited/theatrical refreshes.
								# This should not be triggered, since the individual movies/parts directly inside the set metadata only have the premiere date.
								# Except if one of the movies appears in Arrivals and might therefore have additional dates.
								ReleaseTertiary : [
									TimeReleaseRegular4,	# Released a long time ago.
									TimeReleaseRegular3,	# Released a while ago or to be released far into the future.
									TimeReleaseRegular2,	# Recently released or soon to be released.
								],

								# If the set does not contain a newly released movie yet.
								# Refresh to hopefully get the new movie.
								# Do not refresh too frequently, since determining whether a set is missing a movie, is not that accurate.
								ReleaseIncomplete : [
									TimeReleaseIncomplete3,	# The rating of the new movie is missing.
									TimeReleaseIncomplete2,	# The title, plot, or the premiere date of the new movie is missing.
								],

								# If the previous refresh was done BEFORE the latest release date, and the latest release date is in the PAST.
								# Hence, this forces an immediate refresh if the current time progressed beyond a release date, irrespective of the time that elapsed between the release date and now.
								# This should only be triggered ONCE after each release date, since the timestamp in the database is updated to the current time on refresh, preventing any future refreshes (except if a release date changes or another release date has passed).
								# NB: Note that the 1st value in the outdated brackets are the age since the last REFRESH, and not the age of the RELEASE date (like with other brackets).
								ReleaseOutdated : [
									TimeReleaseOutdated1,	# Any past release date is after the previous refresh.
								],
							}

	TimeReleaseShow			= {
								# Shows are relatively lightweight, requiring a maximum of 9 requests for extended metadata.
								# Shows can therefore be refreshed more frequently without impacting servers or processing too much.
								# However, besides more ratings, there is little metadata that needs to be refreshed for shows frequently, since most changes happen in the season, episode, and pack metadata.

								# LEVELS:
								#	The levels for the brackets are based slightly on the release period (past/present/future), but mainly on the release date of the show or the newest season.
								#	Older releases therefore have a lower level than present or future releases.
								#		Level0: Show or latest season released a long time ago.
								#		Level1: Show or latest season released a while ago or to be released far into the future.
								#		Level2: Show or latest season recently released or soon to be released.

								# Show premiere dates (S01E01).
								# Refresh most frequently, since a lot of metadata might change around the show premiere.
								# Refresh more frequently around the show premiere, to get more accurate ratings.
								ReleasePrimary : [
									TimeReleaseRegular3,	# Show/season released a long time ago.
									TimeReleaseRegular2,	# Show /season released a while ago or to be released far into the future.
									TimeReleaseRegular1,	# Show/season recently released or soon to be released.
								],

								# Season premiere dates (SxxE01).
								# Refresh very rarely, since the show metadata will have changed little between seasons.
								# Only one refresh is needed when a new season comes out, just to get new show ratings and cast.
								ReleaseSecondary : [
									TimeReleaseOccasional4,	# Show/season released a long time ago.
									TimeReleaseOccasional3,	# Show /season released a while ago or to be released far into the future.
									TimeReleaseOccasional2,	# Show/season recently released or soon to be released.
								],

								# New episode dates (SxxEyy).
								# Refresh almost never, since the show metadata will have changed little to none between episodes.
								# Only use this as a fallback to refresh very old show metadata that was not refreshed for some reason by another bracket while a new season is airing.
								# Be careful to add more levels with quicker refresh rates, since the level is calculated from the show and season premieres (SxxE01), and not subsequent episodes premieres (SxxEyy).
								# This should refresh a show every now and then while a season is running.
								ReleaseTertiary : [
									TimeReleaseRare3,		# Show/season released a long time ago.
									TimeReleaseRare3,		# Show /season released a while ago or to be released far into the future.
									TimeReleaseRare3,		# Show/season recently released or soon to be released.
								],

								# If the title, plot, premiere date, rating, or poster is missing.
								# This should almost never happen.
								ReleaseIncomplete : [
									TimeReleaseIncomplete3,	# The rating or poster is missing.
									TimeReleaseIncomplete2,	# The title, plot, or premiere date is missing.
								],

								# If the previous refresh was done BEFORE the latest release date, and the latest release date is in the PAST.
								# Hence, this forces an immediate refresh if the current time progressed beyond a release date, irrespective of the time that elapsed between the release date and now.
								# This should only be triggered ONCE after each release date, since the timestamp in the database is updated to the current time on refresh, preventing any future refreshes (except if a release date changes or another release date has passed).
								# NB: Note that the 1st value in the outdated brackets are the age since the last REFRESH, and not the age of the RELEASE date (like with other brackets).
								ReleaseOutdated : [
									TimeReleaseOutdated1,	# The show/season premiere date is in the past and after the previous refresh.
								],
							}

	TimeReleaseSeason		= {
								# Seasons are relatively heavyweight, requiring a maximum of (7 + 4*number-of-seasons) requests for extended metadata.
								# Seasons should therefore not be refreshed too frequently, since it can impact servers and processing.
								# Typically a single refresh around season premieres should be enough, in order to get the latest dates, ratings, cast, and images.
								# If there are less seasons in a show, the season metadata gets refreshed more frequently than for shows with more seasons.
								# This ensures that shows with many seasons (eg: Hollyoaks) do not get refreshed too often, since they require more requests and resources.

								# LEVELS:
								#	The levels for the brackets are based slightly on the release period (past/present/future), but mainly on the number of seasons in the metadata.
								#	Shows with few seasons have a higher level and are therefore refreshed more often, followed by shows with a medium number of seasons, followed by shows with many seasons.
								#		Level0: Far past shows, or shows with a large number of seasons.
								#		Level1: Recent past or far future shows, or shows with a medium number of seasons.
								#		Level2: Present or near future shows, or shows with a small number of seasons.

								# Show premiere dates (S01E01).
								# Refresh most frequently, since a lot of metadata might change around the show premiere.
								# Refresh more frequently around the show premiere, to get more accurate ratings.
								# This will not use up a lot of requests, since only S00+S01 will be in the season metadata when the show premieres.
								# The count-brackets should not matter here, since when S01 premiers, all shows only have 1 or 2 seasons (S00+S01).
								ReleasePrimary : [
									TimeReleaseRegular4,	# Many seasons, or far past.
									TimeReleaseRegular3,	# Average seasons, recent past, or far future.
									TimeReleaseRegular2,	# Few seasons, present, or near future.
								],

								# Season premiere dates (SxxE01).
								# Refresh frequently when a new season is released, so that if the new season premieres, the new season metadata is available.
								# Only one refresh is needed when a new season comes out, just to get new dates, ratings, cast, and images.
								# Refresh less often, since the metadata will typically be refreshed by ReleaseIncomplete if a new season premieres and is missing from the metadata.
								ReleaseSecondary : [
									TimeReleaseRegular4,	# Many seasons, or far past.
									TimeReleaseRegular3,	# Average seasons, recent past, or far future.
									TimeReleaseRegular2,	# Few seasons, present, or near future.
								],

								# New episode dates (SxxEyy).
								# Refresh almost never, since the season metadata will have changed little to none between episodes.
								# Only use this as a fallback to refresh very old season metadata that was not refreshed for some reason by another bracket while a new episode is airing.
								# This should refresh the seasons every now and then while a season is running.
								ReleaseTertiary : [
									TimeReleaseRare5,		# Many seasons, or far past.
									TimeReleaseRare4,		# Average seasons, recent past, or far future.
									TimeReleaseRare3,		# Few seasons, present, or near future.
								],

								# If a new season is missing, or the premiere date of an already released season is missing.
								ReleaseIncomplete : [
									TimeReleaseIncomplete2,	# The premiere date of the new season or an already released seasons is missing.
									TimeReleaseIncomplete1,	# A new season is missing.
								],

								# If the previous refresh was done BEFORE the latest release date, and the latest release date is in the PAST.
								# Hence, this forces an immediate refresh if the current time progressed beyond a release date, irrespective of the time that elapsed between the release date and now.
								# This should only be triggered ONCE after each release date, since the timestamp in the database is updated to the current time on refresh, preventing any future refreshes (except if a release date changes or another release date has passed).
								# NB: Note that the 1st value in the outdated brackets are the age since the last REFRESH, and not the age of the RELEASE date (like with other brackets).
								ReleaseOutdated : [
									TimeReleaseOutdated1,	# The show/season premiere date is after the previous refresh.
								],
							}

	TimeReleaseEpisode		= {
								# Episodes can be very heavyweight, requiring a maximum of (2*number-of-episodes + 5) requests for extended metadata.
								# Many shows only have few episodes per season (eg: 10) and are therefore relatively lightweight.
								# However, other shows, especially anime, late-night, day-time, and daily shows, can have 100s of episodes per season, and are therefore heavyweight.
								# Episodes should therefore not be refreshed too frequently, since it can impact servers and processing.
								# How often episode metadata should be refreshed depends on the manner in which episodes are released.
								# Instant releases, where all episodes are released at once, should have all dates, titles, plots, etc available at season premiere, and only need to refresh occasionally to get newer rates/votes.
								# But for many anime and daily shows, new/future episode metadata is only added a week or two before the episodes actually airs, sometimes only a few days, requiring almost weekly refreshes.
								# If there are less episodes in a season, the episode metadata gets refreshed more frequently than for seasons with more episodes.
								# This ensures that seasons with many episodes (eg: One Piece, Hollyoaks) do not get refreshed too often, since they require more requests and resources.

								# LEVELS:
								#	The levels for the brackets are based mainly on the number of episodes in the metadata.
								#	Seasons with few episodes have a higher level and are therefore refreshed more often, followed by seasons with a medium number of episodes, followed by seasons with many episodes.
								#		Level0: Far past shows, or seasons with a large number of episodes.
								#		Level1: Recent past or far future shows, or seasons with a medium number of episodes.
								#		Level2-5: Present or near future shows, or seasons with a small number of episodes.

								# Season premiere dates (SxxE01).
								# Refresh less often, since the metadata will typically be refreshed by ReleaseIncomplete if a new episode premieres and is missing from the metadata.
								ReleasePrimary : [
									TimeReleaseRegular5,	# Many episodes, or far past.
									TimeReleaseRegular4,	# Average episodes, recent past, or far future.
									TimeReleaseRegular3,	# Few episodes, present, or near future.
									TimeReleaseRegular2,	# Very few episodes and present.
									TimeReleaseRegular2,	# Very few episodes and present.
								],

								# Season, midseason, and alternative premiere dates (SxxEyy).
								# Refresh less often, since the metadata will typically already be refreshed by ReleaseIncomplete and ReleaseOutdated.
								ReleaseSecondary : [
									TimeReleaseOccasional5,	# Many episodes, or far past.
									TimeReleaseOccasional4,	# Average episodes, recent past, or far future.
									TimeReleaseOccasional3,	# Few episodes, present, or near future.
									TimeReleaseOccasional2,	# Very few episodes and present.
									TimeReleaseOccasional2,	# Very few episodes and present.
								],

								# Any standard episode dates (SxxEyy).
								# Refresh less often, since the metadata will typically already be refreshed by ReleaseIncomplete and ReleaseOutdated.
								ReleaseTertiary : [
									TimeReleaseRare5,		# Many episodes, or far past.
									TimeReleaseRare4,		# Average episodes, recent past, or far future.
									TimeReleaseRare3,		# Few episodes, present, or near future.
									TimeReleaseRare2,		# Very few episodes and present.
									TimeReleaseRare1,		# Very few episodes and present.
								],

								# If a new episode is completely missing or the premiere date of an existing episode is missing.
								# This only applies to episodes of the currently airing season, and not past/ended seasons.
								ReleaseIncomplete : [
									TimeReleaseIncomplete3,	# The premiere date of a past or near-future episode is missing. Keep this low, since there can be various reasons why dates are missing (eg: date never added for smaller/unknown shows).
									TimeReleaseIncomplete1,	# A new episode is missing.
								],

								# If the previous refresh was done BEFORE the latest release date, and the latest release date is in the PAST.
								# Hence, this forces an immediate refresh if the current time progressed beyond a release date, irrespective of the time that elapsed between the release date and now.
								# This should only be triggered ONCE after each release date, since the timestamp in the database is updated to the current time on refresh, preventing any future refreshes (except if a release date changes or another release date has passed).
								# NB: Note that the 1st value in the outdated brackets are the age since the last REFRESH, and not the age of the RELEASE date (like with other brackets).
								# NB: Keep this low for episodes/packs, because of the following scenario:
								#	The current metadata might already contain all episodes, including future/unaired episodes.
								#	This will trigger an outdated refresh every time a new episode is aired, even though the metadata might already be complete and does not need an immediate refresh.
								#	This will happen especially often with daily shows (and to an extend weekly shows). Do not refresh the metadata every day once a new episode was aired.
								ReleaseOutdated : [
									TimeReleaseOutdated3,	# Daily shows. Some episodes are in the future. Do not refresh too often, since episodes are released almost every day.
									TimeReleaseOutdated2,	# Non-daily shows. Some episodes are in the future.
									TimeReleaseOutdated1,	# All episodes are in the past.
								],
							}

	TimeReleasePack			= {
								# Packs are the most heavyweight, requiring a maximum of 5-7 requests for extended metadata.
								# Not many requests are needed, since all episodes of the show are retrieved with a single call, or sometimes with a few calls (2-4 for TMDb, depending on the number of seasons).
								# However, the returned data is considerably larger to download and also requires the provider API to retrieve/process more data from their database, which takes longer.
								# The biggest problem is the local pack processing/generation, which takes long and requires a lot of resources, especially for shows with many episodes.
								# Hence, pack refreshes should be kept to a minimum.
								# But packs should be refreshed at a similar rate to episodes, since the episode metadata requires up-to-date packs for the numbers of newly aired episodes.
								# For instance, it does not help if the episode metadata is refreshed once a week for a currently airing weekly show, while the pack metadata is only refreshed once every other week.
								# Packs should therefore not be repeatedly refreshed around show/season/episode dates, but rather stick to only refreshing if an episode is missing (ReleaseIncomplete).

								# LEVELS:
								#	The levels for the brackets are based mainly on the number of episodes in the metadata.
								#	Packs with few episodes have a higher level and are therefore refreshed more often, followed by packs with a medium number of episodes, followed by packs with many episodes.
								#		Level0: Far past shows, or packs with a large number of episodes.
								#		Level1: Recent past or far future shows, or packs with a medium number of episodes.
								#		Level2-5: Present or near future shows, or packs with a small number of episodes.

								# Show premiere dates (S01E01).
								# Only one season is available at this point, so refreshes will not require too much data and processing.
								ReleasePrimary : [
									TimeReleaseRegular5,	# Many episodes, or far past.
									TimeReleaseRegular4,	# Average episodes, recent past, or far future.
									TimeReleaseRegular3,	# Few episodes, present, or near future.
									TimeReleaseRegular2,	# Very few episodes and present.
									TimeReleaseRegular2,	# Very few episodes and present.
								],

								# Season, midseason, and alternative premiere dates (SxxEyy).
								# Refresh less often, since the metadata will typically already be refreshed by ReleaseIncomplete and ReleaseOutdated.
								ReleaseSecondary : [
									TimeReleaseOccasional5,	# Many episodes, or far past.
									TimeReleaseOccasional4,	# Average episodes, recent past, or far future.
									TimeReleaseOccasional3,	# Few episodes, present, or near future.
									TimeReleaseOccasional2,	# Very few episodes and present.
									TimeReleaseOccasional2,	# Very few episodes and present.
								],

								# Any standard episode dates (SxxEyy).
								# Refresh less often, since the metadata will typically already be refreshed by ReleaseIncomplete and ReleaseOutdated.
								ReleaseTertiary : [
									TimeReleaseRare5,		# Many episodes, or far past.
									TimeReleaseRare4,		# Average episodes, recent past, or far future.
									TimeReleaseRare3,		# Few episodes, present, or near future.
									TimeReleaseRare2,		# Very few episodes and present.
									TimeReleaseRare1,		# Very few episodes and present.
								],

								# If a new episode is completely missing or the premiere date of an existing episode is missing.
								# This only applies to episodes of the currently airing season, and not past/ended seasons.
								ReleaseIncomplete : [
									TimeReleaseIncomplete3,	# The premiere date of a past or near-future episode is missing. Keep this low, since there can be various reasons why dates are missing (eg: date never added for smaller/unknown shows).
									TimeReleaseIncomplete1,	# A new episode is missing.
								],

								# If the previous refresh was done BEFORE the latest release date, and the latest release date is in the PAST.
								# Hence, this forces an immediate refresh if the current time progressed beyond a release date, irrespective of the time that elapsed between the release date and now.
								# This should only be triggered ONCE after each release date, since the timestamp in the database is updated to the current time on refresh, preventing any future refreshes (except if a release date changes or another release date has passed).
								# NB: Note that the 1st value in the outdated brackets are the age since the last REFRESH, and not the age of the RELEASE date (like with other brackets).
								# NB: Keep this low for episodes/packs, because of the following scenario:
								#	The current metadata might already contain all episodes, including future/unaired episodes.
								#	This will trigger an outdated refresh every time a new episode is aired, even though the metadata might already be complete and does not need an immediate refresh.
								#	This will happen especially often with daily shows (and to an extend weekly shows). Do not refresh the metadata every day once a new episode was aired.
								ReleaseOutdated : [
									TimeReleaseOutdated3,	# Daily shows. Some episodes are in the future. Do not refresh too often, since episodes are released almost every day.
									TimeReleaseOutdated2,	# Non-daily shows. Some episodes are in the future.
									TimeReleaseOutdated1,	# All episodes are in the past.
								],
							}

	# The 1st value is considered "few", between the 1st and 2nd value is considered "average", and above the 2nd value is considered "many".
	QuantitySeason			= (20, 40)			# The number of seasons for the quantity brackets.
	QuantityEpisode			= (50, 200)			# The number of episodes for the quantity brackets.
	QuantityPack			= (500, 2000)		# The total number of episodes in a pack for the quantity brackets.

	# The minimum age before re-retrieving partial metadata.
	# Metadata can be partial for one of these reasons:
	#	1. API Limits:
	#		Some provider API has not returned certain metadata.
	#		This can happen because the API rate limit was reached.
	#	2. API Errors:
	#		Some provider API has not returned certain metadata.
	#		This can happen because the server is temporarily down, or some other issue preventing the API from returning metadata.
	#	3. Missing Metadata:
	#		There is some missing metadata, which will either be added later on or might never be added.
	#		Season metadata often has missing images or cast, either for a new or future season, or for the special season S0.
	#		Season and episode metadata are typically partial if it is a new or future release, where images, translations, or cast data is missing and might only be added once aired.
	#		Sometimes certain metadata is never available and permanently partial, especially for S0.
	# Note that these "Partial Redo" refreshes (StatusPartial) are different to "Incomplete Release" refreshes (StatusIncomplete).
	#	1. StatusPartial: An entire API request failed or did not return data. Separate API calls are made for images, cast, studios, translations, aliases, and release dates (if it cannot be retrieved with a single API call).
	#	2. StatusIncomplete: The API request succeeded, but individual attributes within the metadata are missing.
	# During partial refreshes, only the parts that previously failed are refreshed. Parts that previously succeeded are retrieved from cache and not refreshed again. Hence, partial refreshes are lightweight.
	PartialUsage			= 'usage'			# The metadata is partial, because a provider's API rate limit was reached.
	PartialServer			= 'server'			# The metadata is partial, because a provider has temporary server problems.
	PartialData				= 'data'			# The metadata is partial, because not all the data is available from the provider (yet or never).

	# How often to re-retrieve partial metadata until giving up.
	# NB: This includes the first/initial retrieval. Eg: a value of 3 = 1 (initial failed retrieval) + 2 (subsequent retries of failed retrievals).
	# Do not make this number too high, otherwise if eg a server is temporarily down, images are not available for a title yet, etc, it will make too many requests with the same partial data.
	# Once given up, the metadata can still be refreshed normally using the various other refresh mechanisms.
	# Do not make "redo" to high, since the metadata might be permanently, or at least for the foreseeable future, partial, as indicated in case #3.
	# Do not make "time" too low, otherwise partial metadata is refreshed too often when reloading the same menu in a short time. Do not make too high, otherwise temporary errors (eg: reaching the Trakt API rate limit) are not redone quickly enough.
	PartialRedo				= {
								None			: 2,				# The default number of times an attempt is made to refresh partial data before giving up.

								# Used when the API rate limits have been reached. These should resolve within a few minutes once the rate limit has gone down again.
								PartialUsage : {
									'limit'		: 0.97,				# The usage percentage a provider has to reach in order for it to be considered a PartialUsage.
									'time'		: TimeMinute15,		# The delay from the previous refresh before attempting a new/redo refresh.
									'redo'		: 3,				# The maximum number of times an attempt is made to refresh partial data before giving up.
								},

								# Used when the server has temporary problems. It might take slightly longer for the server to come back online.
								PartialServer : {
									'limit'		: 3,				# The number of provider errors that need to occur before using a lower partial-redo refresh interval. Do not make too low, otherwise a single/few sporadic/unrelated errors are seen as partial metadata.
									'time'		: TimeHour1,		# The delay from the previous refresh before attempting a new/redo refresh.
									'redo'		: 3,				# The maximum number of times an attempt is made to refresh partial data before giving up.
								},

								# Used when some API requests did not return any data, such as when the metadata is not yet available on one or more providers.
								PartialData : {
									'unknown'	: 2,				# The default redo count if the release date is not known, typically meaning it is a season far into the future.
									'special'	: 1,				# The redo count for specials S0. Too often the data is partial (missing some thumbnails, dates and other data missing), so never redo and let it get refreshed in other/normal ways some time later.
									'time'		: TimeDay2,		# The delay from the previous refresh before attempting a new/redo refresh.
									'redo'		: (					# The maximum number of times an attempt is made to refresh partial data before giving up.
													# These brackets are based on the premiere dates.
													# If not dates are available, the default redo count above (None : 3) is used instead.
													# Keep really old stuff (eg: 1-2+ years) at a redo count of 1, since the data might never be available (eg: Money Heist S05 only on IMDb, but not on Trakt, and therefore the data will always be partial).
													(TimeYear2,		1), # 2+ years old. Never partial-refresh very old data, since this will probably always stay partial (eg: tt3444938 S01 images). Let it get refreshed in other/normal ways some time later.
													(TimeMonth3,	2), # 3+ months old.
													(TimeMonth1,	3), # 1-3 months old.
													(TimeWeek2,		4), # 2-4 weeks old.
													(TimeZero,		5), # 0-2 weeks old.
													(-TimeWeek1,	4), # 0-1 weeks future.
													(-TimeWeek2,	3), # 1-2 weeks future.
													(TimeNone,		2), # 2+ weeks future.
												),
								},
							}

	# Compress the external database using LZMA.
	# It has the best compression ratio so that more metadata can be stored in the addon.
	# LZMA might be slower at decompression than ZLIB, but this will only be done once. After that the metadata will be in the local cache.
	# LZMA should be part of the standard library from Python 3.3, so we are pretty sure it should be available.
	# If not, then the external metadata can simply not be used. Would be the same problem with other compression algorithms.
	# Note that more data can be added if no compression is used and we only compress the entire database with ZIP during release.
	# This is probably because of all the image URls that have similar parts and can be compressed better if all the data is compressed as one in the ZIP, instead of every row individually.
	# When uncompressed, we can add about 15% more movies or shows, but 50% LESS packs.
	# We could just compress the pack table and leave the other tables. But this would complicate the entire process.
	# Just enable compression, even if we can add a little bit less. Plus this also saves disc space.
	ExternalCompression		= Compression.TypeLzma
	ExternalName			= 'external'
	ExternalPath			= None
	ExternalDatabase		= None

	Instance				= {}
	Settings				= None
	Bulk					= None
	Lock					= Lock()

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, generate = False):
		if generate: Database.__init__(self, name = MetaCache.ExternalName, compression = MetaCache.ExternalCompression)
		else: Database.__init__(self, name = MetaCache.Name)
		self.mGenerate = generate
		self.mExternal = not generate
		self.mMemory = {}
		self.mDeveloper = System.developer()
		self.mTest = None
		self._import()

	@classmethod
	def instance(self, generate = False):
		if not generate in MetaCache.Instance:
			MetaCache.Lock.acquire()
			if not generate in MetaCache.Instance: MetaCache.Instance[generate] = MetaCache(generate = generate)
			MetaCache.Lock.release()
		return MetaCache.Instance[generate]

	def _import(self):
		# Recursive imports.
		# Only import ONCE, instead of importing in each function that needs them.
		# Probably not much more efficient than importing in each function, but could be slightly faster if many metadata items are read from MetaCache and the subfucntions are called many times.
		from lib.meta.manager import MetaManager
		from lib.meta.pack import MetaPack
		globals()['MetaManager'] = MetaManager
		globals()['MetaPack'] = MetaPack

	def _initialize(self):
		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTmdb, idTrakt)
			);
			''' % MetaCache.TypeMovie,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeMovie, MetaCache.TypeMovie))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idTmdb)
			);
			''' % MetaCache.TypeSet,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idTmdb);' % (MetaCache.TypeSet, MetaCache.TypeSet))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb, idTrakt)
			);
			''' % MetaCache.TypeShow,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeShow, MetaCache.TypeShow))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeShow, MetaCache.TypeShow))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb, idTrakt)
			);
			''' % MetaCache.TypeSeason,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypeSeason, MetaCache.TypeSeason))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				season INTEGER,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb, idTrakt, season)
			);
			''' % MetaCache.TypeEpisode,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt, season);' % (MetaCache.TypeEpisode, MetaCache.TypeEpisode))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				time INTEGER,
				settings TEXT,

				idImdb TEXT,
				idTmdb TEXT,
				idTvdb TEXT,
				idTrakt TEXT,
				idSlug TEXT,

				part TEXT,
				data TEXT,

				PRIMARY KEY(settings, idImdb, idTvdb, idTrakt)
			);
			''' % MetaCache.TypePack,
		)
		self._create('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (MetaCache.TypePack, MetaCache.TypePack))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (MetaCache.TypePack, MetaCache.TypePack))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (MetaCache.TypePack, MetaCache.TypePack))
		self._create('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (MetaCache.TypePack, MetaCache.TypePack))

		self._create('''
			CREATE TABLE IF NOT EXISTS `%s`
			(
				idImdb TEXT,
				data TEXT,
				PRIMARY KEY(idImdb)
			);
			''' % MetaCache.TypeBulk,
		)

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		# Important for self.mMemory to be reset.
		# We do not want to carry over the memory metadata to the next process, since the metadata might be outdated.
		MetaCache.Instance = {}

		if settings:
			MetaCache.Settings = None
			MetaCache.Bulk = None
			MetaCache.ExternalPath = None
			MetaCache.ExternalDatabase = None

	##############################################################################
	# SETTINGS
	##############################################################################

	@classmethod
	def settingsId(self, refresh = None):
		if refresh or MetaCache.Settings is None:
			MetaCache.Lock.acquire()
			if refresh or MetaCache.Settings is None:
				# This should include all values and settings that change the metadata before it is saved to the database.
				# If any of these settings change, the value  will not be retrieved from the database and force a refresh of the metadata.
				# This is better than clearing the cache and metadata databases everytime the user changes the settings.
				# NB: Do not add the rating settings here. More info under meta -> tools.py -> cleanVoting().

				from lib.modules.tools import Hash
				from lib.meta.image import MetaImage
				from lib.meta.providers.imdb import MetaImdb

				values = []

				# Metadata
				tools = MetaTools.instance()
				values.append(tools.settingsLanguage())
				values.append(tools.settingsCountry())
				values.append(tools.settingsDetail())

				# Do not include this in the settings ID calculation, for these reasons:
				#	1. This would make all users metadata redownload, because the ID changed, invalidating the existing metadata in the database.
				#	2. If the user first enables the bulk setting and later disables it, because it is too slow or causes stability issues, all existing metadata will be invalidated.
				# The bulkdata should be seen as supplementing data, and not as core data that would change the structure of the metadata, except a little with packs (where IMDb could occasionally add future unaired episodes).
				# Hence, bulkdata should not be included in the settings ID.
				# Plus, if we included this, what about the bulkdata used from the external addon. Would this also have to be included in the settings ID? And the external addon only has a subset of the total bulkdata.
				# Plus, there are too many issues with refreshing bulkdata on low-end devices, causing some of the bulkdata to be missing or very outdated, even if the bulk setting is enabled.
				# Plus, we now retrieve the bulkdata only AFTER preloading and not before, because of performance reasons and memory usage. So the preloaded metadata will not use the bulkdata at first, and only use it later on if the metadata is refreshed.
				#values.append(str(MetaImdb.bulkSettingsModeEnabled())) # All modes have the same data, so only check if disabled.

				# Images
				values.append(Converter.jsonTo(MetaImage.settingsInternal()))

				# Accounts
				# This should not be needed anymore. The metadata stored in MetaCache should not contain any user-specific data anymore, such as the user's Trakt rating, unlike Gaia v6 and prior.
				# Only do this for Fanart, since Fanart returns more and more-recent images if a user API key is provided, compared to making "anonymous" calls without a user key. Molre info in account.py.
				#from lib.modules.account import Imdb, Tmdb, Tvdb, Trakt, Fanart
				#values.extend([Imdb.instance().dataId(), Tmdb.instance().key(), Tvdb.instance().pin(), Trakt.instance().dataUsername(), Fanart.instance().dataKey()])
				from lib.modules.account import Fanart
				values.extend([Fanart.instance().dataKey()])

				MetaCache.Settings = Hash.sha256('_'.join([i if i else ' ' for i in values]))
			MetaCache.Lock.release()

		return MetaCache.Settings

	##############################################################################
	# ATTRIBUTE
	##############################################################################

	@classmethod
	def attribute(self, item, *args):
		return Tools.get(item, MetaCache.Attribute, *args)

	@classmethod
	def valid(self, item):
		return self.attribute(item, MetaCache.AttributeValid)

	@classmethod
	def status(self, item):
		return self.attribute(item, MetaCache.AttributeStatus)

	##############################################################################
	# LOG
	##############################################################################

	# Called from MetaManager.
	@classmethod
	def log(self, item):
		try:
			Logger.log(item[MetaCache.Attribute][MetaCache.AttributeLog])
			del item[MetaCache.Attribute][MetaCache.AttributeLog] # Delete here once printed, since it is not used anymore and only clutters.
		except: pass

	def _log(self, message, type = None, item = None, extra = None, developer = True, log = True):
		if not developer or self.mDeveloper:
			return self.__log(message = message, type = type, item = item, extra = extra, developer = developer, log = log)
		return None

	@classmethod
	def __log(self, message, type = None, item = None, extra = None, developer = True, log = True):
		media = self._logMedia(type = type, item = item)
		id = self._logId(item = item)
		extra = extra or ''
		message = 'METACACHE%s: %s%s%s' % (media, message, id, extra)
		if log: Logger.log(message)
		else: return message

	@classmethod
	def _logMedia(self, type, item):
		value = []
		if type: value.append(type.upper())
		if item:
			season = item.get('season')
			if not season is None: value.append('S%02d' % season)
		return (' [%s]' % (' '.join(value))) if value else ''

	@classmethod
	def _logId(self, item):
		value = []
		if item:
			for i in (('imdb', 'IMDb'), ('trakt', 'Trakt'), ('tmdb', 'TMDb'), ('tvdb', 'TVDb')):
				id = item.get(i[0])
				if id: value.append('%s: %s' % (i[1], id))
		return (' [%s]' % (' | '.join(value))) if value else ''

	def _logRefresh(self, type, refresh, status, time, current, extra = None, item = None, developer = True, log = True):
		if refresh and (not developer or self.mDeveloper):
			indent = '             '
			message1 = '%s REFRESH' % status.upper()
			message2 = '\n%sStatus: %s | Refresh: %s' % (indent, status.capitalize(), refresh.capitalize())
			if time: message2 += ' | Cache Age: %s' % self._logDuration(current - time)
			if extra: message2 += '\n%s%s' % (indent, extra)
			return self._log(message = message1, type = type, item = item, extra = message2, log = log)
		return None

	def _logPartial(self, type, fail, extra = None, item = None, developer = True, log = True):
		if not developer or self.mDeveloper:
			indent = '             '
			message1 = 'PARTIAL DATA'
			message2 = '\n%sFailures: %s' % (indent, fail)
			if extra:
				if extra[0]: message2 += ' | %s' % (extra[0])
				if extra[1]: message2 += '\n%s%s' % (indent, extra[1])
			return self._log(message = message1, type = type, item = item, extra = message2, log = log)
		return None

	def _logDuration(self, seconds, places = None):
		from lib.modules.convert import ConverterDuration
		if seconds is None: return str(seconds)
		elif Tools.isString(seconds): return seconds
		if places is True:
			if seconds < 604800: places = None
			elif seconds < 31557600: places = 0
		elif places is False:
			if seconds < 31557600: places = 0
		return ConverterDuration(seconds, unit = ConverterDuration.UnitSecond).string(format = ConverterDuration.FormatAbbreviationMinimal, places = places)

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _type(self, type):
		typeMovie = False
		typeSet = False
		typeShow = False
		typeSeason = False
		typeEpisode = False
		typePack = False
		if type == MetaCache.TypeMovie: typeMovie = True
		elif type == MetaCache.TypeSet: typeSet = True
		elif type == MetaCache.TypeShow: typeShow = True
		elif type == MetaCache.TypeSeason: typeSeason = True
		elif type == MetaCache.TypeEpisode: typeEpisode = True
		elif type == MetaCache.TypePack: typePack = True
		return typeMovie, typeSet, typeShow, typeSeason, typeEpisode, typePack

	@classmethod
	def _id(self, item):
		idImdb = None
		idTmdb = None
		idTvdb = None
		idTrakt = None
		idSlug = None

		id = item.get('id')
		if id:
			idImdb = id.get('imdb')
			idTmdb = id.get('tmdb')
			idTvdb = id.get('tvdb')
			idTrakt = id.get('trakt')
			idSlug = id.get('slug')

		if not idImdb: idImdb = item.get('imdb')
		if not idTmdb: idTmdb = item.get('tmdb')
		if not idTvdb: idTvdb = item.get('tvdb')
		if not idTrakt: idTrakt = item.get('trakt')
		if not idSlug: idSlug = item.get('slug')

		return idImdb, idTmdb, idTvdb, idTrakt, idSlug

	@classmethod
	def _season(self, item):
		try:
			season = item['season']
			if not season is None: season = int(season)
		except: season = None
		return season

	##############################################################################
	# OLD
	##############################################################################

	def _time(self, type, item):
		if type == MetaCache.TypeMovie or type == MetaCache.TypeSet or type == MetaCache.TypeShow:
			try: return item['time'][MetaTools.TimePremiere]
			except: pass
		elif type == MetaCache.TypeSet:
			try: return item['time'][MetaTools.TimePremiere]
			except: pass
		elif type == MetaCache.TypeSeason:
			# Last/future season might not have a date yet.
			try: return next(i['time'][MetaTools.TimePremiere] for i in reversed(item['seasons']) if Tools.get(i, 'time', MetaTools.TimePremiere))
			except: pass
		elif type == MetaCache.TypeEpisode:
			# Last/future episode might not have a date yet.
			try: return next(i['time'][MetaTools.TimePremiere] for i in reversed(item['episodes']) if Tools.get(i, 'time', MetaTools.TimePremiere))
			except: pass
		elif type == MetaCache.TypePack:
			# Not "item['time'][MetaPack.ValueMaximum]", since this includes specials that might be released years after the show ended.
			try: return item['time'][MetaPack.NumberStandard][MetaPack.ValueMaximum]
			except: pass
		return None

	def _old(self, type, item, current):
		index = 1 # Default if no date is available.
		time = self._time(type = type, item = item)
		if time:
			old = current - time
			if old > MetaCache.TimeOld[1]: index = 2
			elif old > MetaCache.TimeOld[0]: index = 1
			else: index = 0
		return index

	##############################################################################
	# PARTIAL
	##############################################################################

	def _partial(self, type, fail, time, item, usage = True, error = True):
		redo = MetaCache.PartialRedo[None] # Default redo count.
		partial = None
		indicator = None
		message = None
		temporary = False

		# API rate limits reached.
		if partial is None and usage:
			# Cache the usage data for 30 seconds, otherwise it requires too much extra time if called repeatedly.
			# Also check the wait period, since Trakt does not always include the limit counters in the headers, sued for providerUsage().
			# Update: do not cache the calls anymore. Otherwise if the Trakt API limit is reached, the partial metadata gets inserted BEFORE this cached value is updated.
			# This causes the PartialUsage bracket to be ignored and the PartialData to be used instead.
			# Since this function is only called if the data is partial and being inserted into the database, this little overhead (only a few milliseconds) should not have a huge impact.
			#usage = MetaManager.providerUsage(cache = True)
			#wait = MetaManager.providerWait(cache = True)
			usage = MetaManager.providerUsage()
			wait = MetaManager.providerWait()
			if (usage and usage >= MetaCache.PartialRedo[MetaCache.PartialUsage]['limit']) or (wait and wait > Time.timestamp()): # If the usage limit is almost reached, use the lower interval.
				partial = MetaCache.PartialUsage
				redo = MetaCache.PartialRedo[partial]['redo']
				temporary = True
				if self.mDeveloper:
					indicator = 'Provider Usage: %d%%' % (usage * 100)
					message = 'Some providers have reached their API limits, which should hopefully be reset in the near future.'

		# Temporary server issues.
		if partial is None and error:
			error = MetaManager.providerError(cache = True) # Cache the usage data for 30 seconds, otherwise it requires too much extra time if called repeatedly.
			if error and error >= MetaCache.PartialRedo[MetaCache.PartialServer]['limit']: # The maximum errors amongst all providers. Ignore single/few sporadic errors and only do if a least a few errors occured.
				partial = MetaCache.PartialServer
				redo = MetaCache.PartialRedo[partial]['redo']
				temporary = True
				if self.mDeveloper:
					indicator = 'Provider Errors: %d' % error
					message = 'Some providers have temporary server problems, which should hopefully be resolved in the near future.'

		# Partial metadata from provider.
		if partial is None:
			partial = MetaCache.PartialData

			# Redo less (or actually never) for S0, since those seasons have a lot of (often permanent) missing data.
			if type == MetaCache.TypeEpisode and item.get('season') == 0:
				redo = MetaCache.PartialRedo[partial]['special']
			else:
				# Uses the first available date, which is the premiere (for movies, sets, shows, packs) and the season premiere (for seasons, episodes).
				release = self._releaseTime(type = type, item = item)
				if release:
					difference = time - release
					for k, v in MetaCache.PartialRedo[partial]['redo']:
						if k is MetaCache.TimeNone or difference >= k: # Specific time bracket, or the last bracket (far into the future).
							redo = v
							break
				else:
					# No release date is available.
					# This typically means far future seasons without any dates yet, which is partial metadata.
					redo = MetaCache.PartialRedo[partial]['unknown']

			if self.mDeveloper: message = 'Some providers have partial metadata, which could be temporary or permanent.'

		# Allow more redos when generating the external database.
		# This allows provider-failed metadata to be refreshed again if MetaManager.generate() is paused and later restarted.
		if self.mGenerate:
			if temporary: redo = max(3, min(10, redo * 3))
			else: redo = max(3, redo)

		if fail and fail >= redo:
			indicator = 'Failure Limit: %d' % redo
			message = 'Some providers failed too often and partial refreshes are stopped.'

		return {
			MetaCache.AttributeCause : partial,
			MetaCache.AttributeFail : redo,
			'log' : [indicator, message],
		}

	def _partialTime(self, partial):
		# Use a quicker refresh interval if a provider's API rate limit was reached or a certain number of server errors occurred.
		# This refreshes partial metadata more quickly if the server has a temporary problem.
		# Partial metadata caused by other reasons unrelated to the server are refreshed less often. Eg: new/future seasons/episodes might not have images yet.
		# This is not perfect, since it is not always clear why metadata is partial. It could be a single sporadic error, reaching an API rate limit, or long-term server outages.
		try: return MetaCache.PartialRedo[partial]['time']
		except: return MetaCache.PartialRedo[MetaCache.PartialData]['time']

	def _partialLog(self, partial, fail, developer = True):
		log = None
		if not developer or self.mDeveloper:
			log = 'Failures: %s | Cause: ' % fail
			if partial == MetaCache.PartialUsage: log += 'Provider API limit reached'
			elif partial == MetaCache.PartialServer: log += 'Temporary provider server issues'
			else: log += 'Provider has partial metadata'
		return log

	##############################################################################
	# RELEASE
	##############################################################################

	def _release(self, type, item = None, current = None, time = None):
		result = None
		try:
			if current is None: current = Time.timestamp()

			release = self._releaseLookup(type = type, item = item)

			if release:
				releaseTime = release.get('time')
				if releaseTime:
					brackets = None
					if type == MetaCache.TypeMovie: brackets = MetaCache.TimeReleaseMovie
					elif type == MetaCache.TypeSet: brackets = MetaCache.TimeReleaseSet
					elif type == MetaCache.TypeShow: brackets = MetaCache.TimeReleaseShow
					elif type == MetaCache.TypeSeason: brackets = MetaCache.TimeReleaseSeason
					elif type == MetaCache.TypeEpisode: brackets = MetaCache.TimeReleaseEpisode
					elif type == MetaCache.TypePack: brackets = MetaCache.TimeReleasePack

					if brackets:
						level = self._releaseLevel(type = type, item = item, release = release, current = current)

						# Take the minimum timeout from all brackets, instead of returning the timeout from the first matching bracket.
						# Otherwise if one of the movie's theatrical/digitial/physical dates are close to the premiere date (less than 2 months), they will often be ignored.
						# Since an age-match will often be found inside the 1st bracket, since the premiere date was relatively recent.
						# Eg: Today 11 Mar - Premiere 10 Feb - Digital 10 Mar. The 1st (premiere) bracket's 28-56 days timeout will be returned, instead of the the 3rd (digital) bracket's 1-3 days timeout.
						matches = []
						for refresh, bracket in brackets.items():
							index = 0
							if refresh == MetaCache.ReleasePrimary: index = 0
							elif refresh == MetaCache.ReleaseSecondary: index = 1
							elif refresh == MetaCache.ReleaseTertiary: index = 2
							elif refresh == MetaCache.ReleaseIncomplete:
								if type == MetaCache.TypeMovie: index = [2, 1, 0]
								elif type == MetaCache.TypeSet: index = 0
								elif type == MetaCache.TypeShow: index = 0
								elif type == MetaCache.TypeSeason: index = 1
								elif type == MetaCache.TypeEpisode: index = 2
								elif type == MetaCache.TypePack: index = 2
							elif refresh == MetaCache.ReleaseOutdated:
								if type == MetaCache.TypeShow or type == MetaCache.TypeSeason: index = [1, 0]
								else: index = [2, 1, 0]

							date = None
							if Tools.isList(index):
								for i in index:
									try:
										date = releaseTime[i]
										if date < current: break # Only if the date is in the past. For _releaseIncomplete().
									except: pass
							else:
								try: date = releaseTime[index]
								except: pass

							if date:
								leveled = None
								status = None
								age = aged = current - date

								# Incomplete metadata with important attributes missing.
								if refresh == MetaCache.ReleaseIncomplete:
									try: premiere = releaseTime[0]
									except: premiere = date
									incomplete = self._releaseIncomplete(type = type, item = item, release = release, date = date, premiere = premiere, age = age)
									if not incomplete is MetaCache.IncompleteNone:
										status = MetaCache.StatusIncomplete
										leveled = incomplete

								# The last refresh was before the current release date.
								elif refresh == MetaCache.ReleaseOutdated:
									outdated, closest = self._releaseOutdated(type = type, item = item, release = release, time = time, current = current)
									if not outdated is MetaCache.ReleaseLevelNone:
										status = MetaCache.StatusOutdated
										leveled = outdated

										# Use the age since the last refresh, and not the age of the release date.
										age = current - time

										# Get a more accurate age.
										# This is if the closest episode date (time[2]) is in the future, which makes the releaseTime for-loop above use the season premiere instead (time[1]), which can be far off the episode date.
										# The "previous" time is also added in _releaseOutdated().
										# This is only used for _releaseLog(), but can avoid confusion during logging about how old the "Release Age" really is.
										if type == MetaCache.TypeEpisode or type == MetaCache.TypePack:
											if not closest:
												closest = release.get('previous')
												if closest: closest = closest.get('time')
											if closest: aged = current - closest

								# Full metadata for releases in the near future or recent past.
								else:
									status = MetaCache.StatusReleased
									leveled = level

								if status:
									try:
										if Tools.isArray(bracket[0][0]):
											try: bracket = bracket[leveled]
											except: bracket = bracket[-1]
									except: pass

									match = None
									for period, outdated in bracket:
										if period is MetaCache.TimeNone: # Outdated unlimited periods.
											match = (period, outdated)
											break # Only break out of the inner loop, since all 3 brackets should be checked in the outer loop.
										elif period < 0 and age < 0: # Future
											if age >= period:
												match = (period, outdated)
												break # Only break out of the inner loop, since all 3 brackets should be checked in the outer loop.
										elif period >= 0 and age >= 0: # Past
											if age <= period:
												match = (period, outdated)
												break # Only break out of the inner loop, since all 3 brackets should be checked in the outer loop.
									if match: matches.append({'status' : status, 'refresh' : refresh, 'period' : match[0], 'outdated' : match[1], 'bracket' : bracket, 'level' : leveled, 'age' : aged})

						if matches:
							match = min(matches, key = lambda i : i['outdated'])
							if match:
								result = {
									'status' : match['status'],
									'time' : match['outdated'],
									'log' : self._releaseLog(type = type, status = match['status'], refresh = match['refresh'], bracket = match['bracket'], level = match['level'], period = match['period'], outdated = match['outdated'], age = match['age']),
								}
		except: Logger.error()
		return result

	# Determines if the previous metadata refresh occured before the current release date.
	def _releaseOutdated(self, type, item, release, time, current):
		level = MetaCache.ReleaseLevelNone
		closest = None
		try:
			if release and time:
				times = release.get('time')

				if times:
					# Refresh shows/seasons only if a new season premieres, not if a new episode is aired.
					if type == MetaCache.TypeShow or type == MetaCache.TypeSeason: times = times[:2]
					else: times = times[:3] # Ignore unknown times.

					# The release times has the closest episode date, and not always the last aired episode date.
					# Eg: release['time'][2] is the next episode in 3 days (future) and not the previous episode 4 days ago (past).
					# Hence, if the future episode is closer than the previous episode, this function returns None instead.
					# Add the previously aired episode if available (up-to-date) and the most recently aired episode from the existing metadata (could be outdated).
					if type == MetaCache.TypeEpisode or type == MetaCache.TypePack:
						previous = release.get('previous')
						if previous and (type == MetaCache.TypePack or previous.get('season') == item.get('season')): times.append(previous.get('time'))
						if type == MetaCache.TypeEpisode:
							try:
								for i in reversed(item['episodes']):
									premiere = Tools.get(i, 'time', MetaTools.TimePremiere)
									if premiere and premiere < current:
										times.append(premiere)
										break
							except: Logger.error()
						elif type == MetaCache.TypePack:
							try:
								for premiere in reversed(item['time'][MetaPack.NumberStandard][MetaPack.ValueValues]):
									if premiere and premiere < current:
										times.append(premiere)
										break
							except: Logger.error()

					# Only past dates, not future dates.
					times = [i for i in times if i and i < current and i > time]

					if times:
						closest = max(times)

						# For episodes and packs, check that the last episode's release date is before the current time, since these refreshes are heavyweight.
						# Otherwise if the metadata has future/unaired episodes, as time progresses and new episodes air, it will force an outdated-refresh.
						# The forced refresh is unnecessary, since the episode is already in the metadata and does not need an urgent refresh.
						# This is especially prominent with daily shows, and to an extend weekly shows.
						# Otherwise the episode and pack metadata is outdated-refreshed every day if a new episode airs, even though the episode is already in the metadata.
						# If an episode is missing from the metadata, it will in any case be refreshed by _releaseIncomplete().
						if type == MetaCache.TypeEpisode or type == MetaCache.TypePack:
							last = None

							if type == MetaCache.TypeEpisode:
								for i in item['episodes']:
									premiere = Tools.get(i, 'time', MetaTools.TimePremiere)
									if premiere and (last is None or premiere > last): last = premiere

							elif type == MetaCache.TypePack:
								pack = MetaPack.instance(item)
								episodes = []

								season1 = pack.lastSeasonOfficial()
								if season1:
									season1 = pack.number(item = season1)
									episode = pack.episode(season = season1)
									if episode: episodes.extend(episode)

								season2 = pack.lastSeasonStandard()
								if season2:
									season2 = pack.number(item = season2)
									if not season1 == season2:
										episode = pack.episode(season = season2)
										if episode: episodes.extend(episode)

								if episodes:
									for i in episodes:
										premiere = pack.time(item = i)
										if premiere and (last is None or premiere > last): last = premiere

							if last and last < current:
								level = MetaCache.ReleaseLevel2
							else:
								interval = release.get('interval')
								if interval == MetaPack.IntervalDaily: level = MetaCache.ReleaseLevel0
								else: level = MetaCache.ReleaseLevel1

						else:
							level = MetaCache.ReleaseLevel0
		except: Logger.error()
		return level, closest

	# Determine if there are important missing attributes in the metadata, or if there are missing seasons or episodes.
	def _releaseIncomplete(self, type, item, release, date, premiere, age):
		incomplete = MetaCache.IncompleteNone

		# MOVIES
		#	IncompleteMajor: title, plot, digitial/physical/televison date
		#	IncompleteMinor: rating, poster
		if type == MetaCache.TypeMovie:
			# Only past releases, since future releases will obviously have missing attributes.
			if age >= 0:
				# The title/plot is missing, causing gaps in the menu and are therefore marked as IncompleteMajor.
				if not item.get('title') or not item.get('plot'): incomplete = MetaCache.IncompleteMajor

				else:
					times = item.get('time')

					# Movies with missing home release dates are important for the Arrivals menu.
					# Only apply these brackets if none of the digital, physical, and televison dates are available.
					# Do not do this if only a single of those dates is missing, since many movies only have one of those dates.
					# Eg: Almost all Netflix original movies only have a digital release date, but no physical/televison release dates.
					# Also do not do for very old movies, since many of them never had a digitial/physical/televison release date.
					if not times: incomplete = MetaCache.IncompleteMajor

					# Sometimes movies get a new releases years/decades later.
					# Eg: tt0819953 released in 2007, but was listed in MetaManager.release().
					# However, Trakt/TMDb still do not a home release date for this movie. Hence, it constantly triggers a incomplete refresh.
					# Therefore, only do a incomplete refresh if the home release date is missing, if the movie premiered Therefore recently, and is not years/decades old.
					elif not release.get('period') == MetaCache.PeriodPast and not any(times.get(i) for i in MetaTools.TimesHome): incomplete = MetaCache.IncompleteMajor

					# The rating or poster is missing.
					elif not item.get('rating') or not Tools.get(item, 'image', 'poster'): incomplete = MetaCache.IncompleteMinor

		# SETS
		#	IncompleteMajor: title, plot, premiere date
		#	IncompleteMinor: rating
		elif type == MetaCache.TypeSet:
			# If a new movie was released, but the set does not contain it yet.
			# This is difficult to determine accurately. Check if the there is a premiere date from release() that is substantially different to any of the part/movie dates.
			# The difference between the new release() date and the closests date of the parts is more than 3 months, indicating that a movie is missing.
			# Is Incomplete (refresh): Either the new movie is not in part yet, or it is in part, but does not have a premiere date yet.
			# Is Not Incomplete (no refresh): Or it is in part and the premiere date is the "same" (+- 3 months) as the release() date.
			times = None
			part = item.get('part')
			if part and premiere:
				times = [Tools.get(i, 'time', MetaTools.TimePremiere) for i in part if i] # The parts in sets only have a premiere date.
				times = [abs(premiere - i) for i in times if i] # The release() date is the premiere date.
			if not times or min(times) > MetaCache.TimeMonth3: incomplete = MetaCache.IncompleteMajor # 3 months. Allow some leeway if the release() premiere date is not exactly the same as the premiere date in the set's parts.

			# The part that has just been released has missing attributes.
			else:
				if part and age >= 0:
					id = Tools.get(release, 'id', 'tmdb')
					if id:
						for i in reversed(part):
							if i and id == Tools.get(i, 'id', 'tmdb'):
								if not Tools.get(i, 'time', MetaTools.TimePremiere): incomplete = MetaCache.IncompleteMajor
								elif not i.get('title') or not i.get('plot'): incomplete = MetaCache.IncompleteMajor
								elif not i.get('rating'): incomplete = MetaCache.IncompleteMinor
								break

		# SHOWS
		#	IncompleteMajor: title, plot, premiere date
		#	IncompleteMinor: rating, poster
		elif type == MetaCache.TypeShow:
			# Only past releases, since future releases will obviously have missing attributes.
			if age >= 0:
				# The title/plot is missing, causing gaps in the menu and are therefore marked as IncompleteMajor.
				if not item.get('title') or not item.get('plot'): incomplete = MetaCache.IncompleteMajor

				else:
					# Shows with missing premiere dates.
					# This should not happen, since shows without a date will not be in the releases table and the outer if-statement will not be executed.
					if not Tools.get(item, 'time', MetaTools.TimePremiere): incomplete = MetaCache.IncompleteMajor

					# The rating or poster is missing.
					elif not item.get('rating') or not Tools.get(item, 'image', 'poster'): incomplete = MetaCache.IncompleteMinor

		# SEASONS
		#	IncompleteMajor: season (season metadata missing)
		#	IncompleteMinor: date (only past seasons)
		elif type == MetaCache.TypeSeason:
			# A new season is not in the seasons metadata yet.
			# Incomplete if there are no seasons at all.
			# Incomplete if a season has no premiere date yet. Future seasons are often added way ahead of time with little metadata and typically no dates.
			# Incomplete if release() returns an episode, but there is not corresponding season number in the metadata.
			# Incomplete if release() returns a special, but there is no S0 in the metadata.
			part = item.get('seasons')
			if part:
				numbers = [i.get('season') for i in part]
				numbers = [i for i in numbers if not i is None]
				if not numbers:
					# Only past releases, since future releases will obviously have missing seasons.
					if age >= 0: incomplete = MetaCache.IncompleteMajor
				else:
					count = release.get('count')
					if count:
						releaseSpecial = count.get(Media.Special) # Number of special episodes in S0.
						if releaseSpecial and not 0 in numbers: incomplete = MetaCache.IncompleteMajor

						# Use the count instead of the season number, since Trakt might have a different season number, like the year as season.
						releaseSeason = count.get(Media.Season) # Number of seasons, excluding S0.
						if releaseSeason and releaseSeason > max(numbers): incomplete = MetaCache.IncompleteMajor

					# Do not check the title or plot, since most seasons do not have a custom title or plot.
					# Do not check the poster, since some seasons, especially newer ones, might not have a poster yet.
					# The rating could be checked, but since seasons are only rated directly on Trakt, there is a good chance newer seasons do not have a rating yet.
					if incomplete is MetaCache.IncompleteNone:
						# Use the last season number, and not the season count.
						# IMDb often adds 1-2 future seasons, sometimes months/years ahead of time.
						# Eg: South Park is currently at S27, but IMDb has already up to S30 listed.
						try: lastSeason = release['last'][Media.Season]
						except: lastSeason = -1

						for i in part:
							season = i.get('season')
							if season: # Ignore S0, which might not have any episodes and therefore no premiere date.
								if not Tools.get(i, 'time', MetaTools.TimePremiere):
									# Future seasons typically do not have a date yet.
									# The status itself might be outdated and this will often not work.
									# Eg: the season status might be "upcoming" in the current metadata, but the season might actually already be "continuing".
									# Hence, ignore the status for the newly released season and only use the status for old seasons.
									status = i.get('status')
									if (age >= 0 and status and not status in MetaTools.StatusesFuture and lastSeason and season < lastSeason) or (lastSeason and lastSeason == season):
										incomplete = MetaCache.IncompleteMinor
										break
			else:
				# No seasons in the metadata.
				# Probably means there is something wrong with the metadata.
				# Not sure if there are future shows without at least the first season. Most in-production shows have at least one season/episode.
				# Only past releases, since future releases will obviously have missing seasons.
				if age >= 0: incomplete = MetaCache.IncompleteMajor

		# EPISODES
		#	IncompleteMajor: episode (missing episodes)
		#	IncompleteMinor: date (only past or near future episodes)
		elif type == MetaCache.TypeEpisode:
			# Episode metadata is incomplete if the metadata does not contain the recently released episode.
			# For instance, S05E07 has just aired, but the episode metadata only contains up to S05E06.
			part = item.get('episodes')
			if part:
				count = release.get('count')
				if count:
					numbers = [i.get('episode') for i in part]
					numbers = [i for i in numbers if not i is None]

					season = item.get('season')
					releaseSeason = None
					releaseEpisode = None

					# Specials in S0.
					if season == 0:
						try:
							releaseEpisode = release['special']['episode']
							releaseSeason = 0
						except: pass
					else:
						# Use the last known episode and not the closest/previous episode.
						# If the "last" episode number is in the releases, it has to come from Trakt/Arrivals/Progress.
						# This means that the last episode should be available in the detailed metadata.
						last = release.get('last')

						try: releaseSeason = last[Media.Season]
						except: pass
						if releaseSeason is None:
							# Inaccurate, since it is the number of seasons (count) and not necessarily the season number.
							try: releaseSeason = count[Media.Season]
							except: pass

						releaseEpisode = None
						try: releaseEpisode = last[Media.Episode]
						except: pass
						if releaseEpisode is None:
							# Inaccurate, since it is the number of episodes (count) and not necessarily the episode number.
							try: releaseEpisode = count[Media.Episode]
							except: pass

					# Only for the same season.
					# For instance, if the last aired episode in "release" is S22E10, do not apply this code to any other season, eg S01 - S21.
					# Assume that all earlier seasons have up-to-date metadata.
					# It could be that eg S21 still has some missing episodes, since it was updated a long time ago, while S22 is the latest season.
					# But since there are no episode numbers from earlier seasons in "release", we cannot determined if S21 is incomplete.
					# In such a case, the S21 metadata just has to be refreshed in the normal way, and not because it is incomplete.
					if not season is None and not releaseEpisode is None:
						# In case Trakt uses a different season number, like the year.
						same = releaseSeason == season
						if not same:
							try: same = releaseSeason == part[0]['number'][MetaPack.ProviderTrakt][MetaPack.NumberStandard][MetaPack.PartSeason]
							except: pass

						if same:
							# The episode number coming from "release" might use a different numbering system to the official Gaia numbers.
							# For instance, the Trakt calendar might return absolute numbers.
							# Eg: One Piece S22E1147.
							# Hence, check the standard numbers of all providers to see if any of the numbers match.
							if numbers:
								if season == 0 or releaseEpisode > max(numbers):
									extra = []
									for i in reversed(part):
										number = i.get('number')
										if number:
											try:
												episode = number[MetaPack.NumberStandard][MetaPack.PartEpisode]
												if episode == releaseEpisode: # Break out earlier if the exact number was found.
													incomplete = False
													break
												elif not episode is None:
													extra.append(episode)
											except: pass
											for provider in MetaPack.Providers:
												try:
													number2 = number[provider][MetaPack.NumberStandard]
													if number2[MetaPack.PartSeason] == releaseSeason:
														episode = number2[MetaPack.PartEpisode]
														if episode == releaseEpisode: # Break out earlier if the exact number was found.
															incomplete = False
															break
														elif not episode is None:
															extra.append(episode)
												except: pass
											if not incomplete is MetaCache.IncompleteNone: break

										# Do this at the end, so that at least the last episode is added.
										# Not for specials, since the episode number order does not always correspond to the date order of the episodes.
										if season and (not number or not i.get('status') in MetaTools.StatusesFuture):
											# Continue to add older episodes if the main season-episode number does not match the standard pack number calculated from the pack.
											# This is for number discrpencies on TVDb, where additional unofficial/alternate episodes from TVDb are added to the end of the episode list.
											# Eg: One Piece S22E60 (TVDb) is actually S22E57 (Trakt - S22E1145).
											# The last official episode from "release" is S22E1147 (S22E59), which is lower than the last episode in the metadata S22E60.

											# This works, but checking the type might better.
											#try: standard = number[MetaPack.NumberStandard]
											#except: standard = None
											#if standard == [i.get('season'), i.get('episode')]: break
											typed = i.get('type')
											if typed and not MetaPack.NumberUnofficial in typed: break

									# If not broken out earlier with an exact number, check if the release episode is later/larger than the last known episode in the metadata.
									if incomplete is False: incomplete = MetaCache.IncompleteNone # Exact episode was found.
									elif extra and releaseEpisode > max(extra): incomplete = MetaCache.IncompleteMajor

								# Episodes with missing dates.
								# Only past episodes and near future episodes of the currently airing season are considered.
								# Episodes after the currently airing episode are also ignored.
								# Do not check the title, plot, rating, or thumbnail of these episodes, since they can be missing for smaller/unknown shows, even after being aired.
								if incomplete is MetaCache.IncompleteNone and age >= -MetaCache.TimeDay3: # Past or up to 3 days into the future.
									count = 0
									for i in reversed(part):
										number = i.get('number')
										if number:
											# Ignore the future unaired episodes.
											try:
												if number[MetaPack.NumberStandard][MetaPack.PartEpisode] > releaseEpisode: continue
											except: continue # If there is no number, continue to the next (previous) episode.
											future = False
											for provider in MetaPack.Providers:
												try:
													number2 = number[provider][MetaPack.NumberStandard]
													if number2[MetaPack.PartSeason] == releaseSeason and number2[MetaPack.PartEpisode] > releaseEpisode:
														future = True
														break
												except: pass
											if future: continue

											# For efficiency, only scan up to 5 of the most recent episodes.
											# Scanning all episodes in the season is not much slower, but in most cases unnecessary.
											count += 1
											if count > 5: break

											if not Tools.get(i, 'time', MetaTools.TimePremiere):
												incomplete = MetaCache.IncompleteMinor
												break

							elif not numbers and age >= 0: incomplete = MetaCache.IncompleteMajor

					# Fallback incomplete detection for specials, if the release data does not contain the last known special.
					# Only do this if the exact episode number was not checked, since using the count is less accurate.
					if incomplete is MetaCache.IncompleteNone and season == 0 and not releaseEpisode:
						releaseSpecial = count.get(Media.Special) # Number of special episodes in S0. Less accurate than the actual episode number.
						if releaseSpecial:
							# Do not check the last episode number, max(numbers), since sometimes there are missing episodes.
							# Eg: GoT S0 has some missing episodes, like S00E41.
							#if numbers and releaseSpecial > max(numbers): incomplete = MetaCache.IncompleteMajor
							if numbers and releaseSpecial > len(numbers): incomplete = MetaCache.IncompleteMajor
							elif not numbers and age >= 0: incomplete = MetaCache.IncompleteMajor
			else:
				# No episodes in the metadata.
				# It is common for future seasons to not have an episode added yet.
				# Only past releases, since future releases will obviously have missing episodes.
				if age >= 0: incomplete = MetaCache.IncompleteMajor

		# PACK
		#	IncompleteMajor: episode (missing episodes)
		#	IncompleteMinor: date (only past or near future episodes)
		elif type == MetaCache.TypePack:
			# A pack is incomplete if a newly aired episode is not in the pack.
			# Initializing a pack here, just to check for missing episodes, might seem like a bad idea.
			# However, MetaPack.instance(...) only initializes the pack once for a new dict, and simply returns the already-initialized pack for the same dict.
			# Assuming that the pack will always be used (aka initialized) when retrieve from cache, we already know MetaPack.instance(...) will be called later on (eg by MetaManager).
			# So calling it here already should not increase computational time.
			pack = MetaPack.instance(item)

			if pack:
				last = release.get('last')

				releaseSeason = None
				try: releaseSeason = last[Media.Season]
				except: pass
				if releaseSeason is None:
					# Inaccurate, since it is the number of seasons (count) and not necessarily the season number.
					try: releaseSeason = count[Media.Season]
					except: pass

				releaseEpisode = None
				try: releaseEpisode = last[Media.Episode]
				except: pass
				if releaseEpisode is None:
					# Inaccurate, since it is the number of episodes (count) and not necessarily the episode number.
					try: releaseEpisode = count[Media.Episode]
					except: pass

				if not releaseSeason is None and not releaseEpisode is None:
					episode = pack.episodeStandard(season = releaseSeason, episode = releaseEpisode)
					if not episode: episode = pack.episode(season = releaseSeason, episode = releaseEpisode)
					if not episode:
						for provider in MetaPack.Providers:
							# Do not use episodeStandard(), since "provider" does not work in combination with "number".
							episode = pack.episode(season = releaseSeason, episode = releaseEpisode, provider = provider)
							if episode: break
					if not episode: incomplete = MetaCache.IncompleteMajor

					# Episodes with missing dates.
					# Only past episodes and near future episodes of the currently airing season are considered.
					# Episodes after the currently airing episode are also ignored.
					if incomplete is MetaCache.IncompleteNone and age >= -MetaCache.TimeDay3: # Past or up to 3 days into the future.
						if releaseSeason and releaseEpisode:
							episodes = pack.episodeOfficial(season = releaseSeason)
							if not episodes: episodes = pack.episodeOfficial(season = releaseSeason, provider = MetaPack.ProviderTrakt)
							if episodes:
								count = 0
								for i in reversed(episodes):
									if pack.numberEpisode(item = i, default = -1) > releaseEpisode: continue
									else:
										future = False
										for provider in MetaPack.Providers:
											number = pack.number(item = i, provider = provider)
											if number and number[MetaPack.PartSeason] == releaseSeason and number[MetaPack.PartEpisode] > releaseEpisode:
												future = True
												break
										if future: continue

									# For efficiency, only scan up to 5 of the most recent episodes.
									# Scanning all episodes in the season is not much slower, but in most cases unnecessary.
									count += 1
									if count > 5: break

									if not pack.time(item = i):
										incomplete = MetaCache.IncompleteMinor
										break

		return incomplete

	'''
		Refresh metadata more frequently, depending on various attributes.
		Shows that are still airing and/or released daily/weekly are refreshed more often than ended or instantly-released shows.
		The higher the level, the more frequently metadata is being refreshed.

		MOVIES
			1. Past
				Level0:	Premiere in the far past (9+ months) and digital in the medium past (6+ months).
				Level0:	Premiere/digital in the medium past (4+ months).
				Level0:	Only digital in the far past (1+ years).
			2. Present
				Level2:	Premiere/theatrical in the recent past (2+ weeks).
				Level2:	Premiere in the medium past (2+ months) and theatrical/digital in the recent past (2+ weeks).
				Level2: Premiere/theatrical in the medium past (3+ months), digital in the medium past (2+ months), and physical/television in the recent past (1+ months).
			3. Future
				Level0:	Premiere in the far future (3+ months).
				Level1:	Premiere in the medium future (1+ months).
				Level1:	Premiere in the near future (1+ weeks).
				Level2:	Premiere in the near future (1- weeks).
			4. Overlapping (considered a "present" release, since there is no home date and the premiere date is not too long ago)
				Level1:	Premiere in the medium past (2+ months), theatrical in the far future (3+ months), and no digital/physical release yet.
				Level2:	Theatrical in the far past (1+ years), no premiere and no digital/physical release yet (and maybe never).

		SETS
			1. Past
				Level0: Premiere/digital in the far past (3+ years).
				Level0: Premiere/digital in the medium past (4+ months).
				Level1: Premiere in the medium past (5+ months) and digital in the recent past (2+ months).
			2. Present
				Level2: Premiere/theatrical in the recent past (2+ weeks).
				Level2: Premiere/theatrical in the recent past (1+ weeks) and no digital/physical release yet.
				Level2: Premiere/theatrical in the medium past (3+ months), digital in the medium past (2+ months), and physical/television in the recent past (1+ months).
			3. Future
				Level1: Premiere/theatrical in the medium future (1+ months).
			4. Overlapping (considered a "present" release, since there is no home date and the premiere date is not too long ago)
				Level1: Premiere for the NEXT movie in the medium future (1+ months) without a digitial release yet, and the digitial release of the PREVIOUS movie in the far past (9+ months).

		SHOWS
			1. Past
				Level0: Premiere in the far past (2+ months).
				Level1: Premiere in the medium past (1+ months).
				Level1: Premiere in the recent past (2+ weeks).
			2. Present
				Level2: Premiere in the recent past (1- weeks).
				Level2: Premiere today (1- days).
				Level2: Old show with a new season premiere in the recent past (1- weeks).
			3. Future
				Level0: Premiere in the far future (1+ months).
				Level1: Premiere in the near future (1+ weeks).
				Level2: Premiere in the next few days (3- days).

		SEASONS
			1. Past
				Level0: Any season premiere in the far past (1+ years). Number of seasons: [0,20].
				Level0: Any season premiere in the recent past (2- weeks) with all episodes already aired. Number of seasons: [0,20].
			2. Present
				Level1: Any season currently airing. Number of seasons: [20,40].
				Level2: Any season currently airing. Number of seasons: [0,20].
			3. Future
				Level0: Any season premiere in the far future (1+ months). Number of seasons: [0,20].
				Level1: All seasons in the (unknown) future and no release dates are available yet. Number of seasons: [0,20].
				Level1: Any season premiere in the medium future (2+ weeks). Number of seasons: [0,20].
				Level1: Any season premiere in the near future (1+ weeks). Number of seasons: [0,20].
				Level2: Any season premiere in next few days (3- days). Number of seasons: [0,20].

		EPISODES
			1. Past
				Level0: All episodes in the season aired in the far past (1+ years). Number of episodes: [0,50].
				Level1: All episodes in the season aired in the medium past (1+ months). Number of episodes: [0,50].
				Level1: The last episodes in the season aired in the recent past (1- months). Number of episodes: [0,50].
			2. Present
				Level2-5: Some episodes in the season have already aired, while others have not yet aired. Number of episodes: [0,50]. Level is dependent on the number of episodes and release interval.
				Level3: Season premiere in the next few days (3- days).
			3. Future
				Level1: All episodes in the season air in the (unknown) future and no release dates are available yet. Number of episodes: [0,50].
				Level1: All episodes in the season air in the near future (1+ weeks). Number of episodes: [0,50].
				Level1: All episodes in the season air in the far future (1+ months). Number of episodes: [0,50].

	'''
	def _releaseLevel(self, type, item, release, current):
		level = 0.0001 # Small value, so that 0.5 is rounded up to the closest. Eg: 2.4 -> 2.0 | 2.5 -> 3.0.

		# Adjust refreshes based on the period.
		period = release.get('period') or MetaCache.PeriodPresent # Default to PeriodPresent if the period is None.
		past = period == MetaCache.PeriodPast
		future = period == MetaCache.PeriodFuture
		if period:
			if period == MetaCache.PeriodPast: level -= 0.25
			elif period == MetaCache.PeriodPresent: level += 1.5
			elif period == MetaCache.PeriodFuture: level += 1.25

		# Adjust the level slightly based on the closest release date.
		closest = None
		times = release.get('time')
		if times:
			if type == MetaCache.TypeShow or type == MetaCache.TypeSeason:
				# Only use the show's premiere date (S01E01) and the new season premiere date (SxxE01), but not the episode dates.
				# Use the season premiere as well, otherwise older shows with a new season has a low level (Level1), due to the subtractions below.
				times = times[:2]
			elif type == MetaCache.TypeEpisode or type == MetaCache.TypePack:
				# Use the dates for season premieres, mideason finales, stanadard episodes, and season-end specials.
				times = times[:3]
			else:
				# Do not use the 4th time ("Unknown" time at index 3), since it can be slightly off for movies.
				times = times[:3]

			closest = MetaTools.instance().timeClosest(times = times, future = True)
			if closest:
				closest = current - closest
				if type == MetaCache.TypeMovie or type == MetaCache.TypeSet:
					if closest < 0:
						if closest > -MetaCache.TimeDay7: level += 0.30			# 1- week (future).
						elif closest > -MetaCache.TimeMonth1: level -= 0.50		# 1- month (future).
						elif closest > -MetaCache.TimeMonth2: level -= 0.70		# 2- months (future).
						elif closest <= -MetaCache.TimeMonth2: level -= 0.80	# 2+ months (future). Subtract more so that this goes to ReleaseLevel0.
					else:
						if closest > MetaCache.TimeYear3: level -= 0.50			# 3+ years (past).
						elif closest > MetaCache.TimeYear2: level -= 0.30		# 2+ years (past).
						elif closest > MetaCache.TimeYear1_5: level -= 0.20		# 1.5+ years (past).
						elif closest > MetaCache.TimeYear1: level -= 0.10		# 1+ year (past).
						elif closest > MetaCache.TimeMonth9: level += 0.00		# 9+ months (past).
						elif closest > MetaCache.TimeMonth6: level += 0.10		# 6+ months (past).
						elif closest > MetaCache.TimeMonth3: level += 0.20		# 3+ months (past).
						elif closest > MetaCache.TimeMonth2: level += 0.30		# 2+ months (past).
						elif closest > MetaCache.TimeMonth1: level += 0.50		# 1+ month (past).
						else: level += 0.80										# 1- month (past).
				elif type == MetaCache.TypeShow or type == MetaCache.TypeSeason:
					if closest < 0:
						if closest > -MetaCache.TimeDay7: level += 0.30			# 1- week (future).
						elif closest > -MetaCache.TimeMonth1: level -= 0.50		# 1- month (future).
						elif closest <= -MetaCache.TimeMonth1: level -= 0.80	# 1+ months (future). Subtract more so that this goes to ReleaseLevel0.
					else:
						if closest > MetaCache.TimeMonth6: level -= 0.50		# 6+ months (past).
						elif closest > MetaCache.TimeMonth3: level -= 0.30		# 3+ months (past).
						elif closest > MetaCache.TimeMonth2: level -= 0.20		# 2+ month (past).
						elif closest > MetaCache.TimeMonth1: level -= 0.10		# 1+ month (past).
						else: level += 0.80										# 1- month (past). Important for recently ended shows that are instantly released.
				elif type == MetaCache.TypeEpisode or type == MetaCache.TypePack:
					if closest < 0:
						if closest > -MetaCache.TimeDay7: level += 0.10			# 1- week (future).
						elif closest > -MetaCache.TimeMonth1: level -= 0.50		# 1- month (future).
						if closest <= -MetaCache.TimeMonth1: level -= 0.80		# 1+ months (future).
					else:
						if closest > MetaCache.TimeMonth6: level -= 0.50		# 6+ months (past).
						elif closest > MetaCache.TimeMonth3: level -= 0.30		# 3+ months (past).
						elif closest > MetaCache.TimeMonth2: level -= 0.20		# 2+ month (past).
						elif closest > MetaCache.TimeMonth1: level -= 0.10		# 1+ month (past).
						else: level += 0.80										# 1- month (past). Important for recently ended shows that are instantly released.

			# Future shows/seasons/episodes where all times are None, since no release dates are available yet.
			# Reduce the level, otherwise they can be Level2+.
			elif future:
				if type == MetaCache.TypeMovie or type == MetaCache.TypeSet: level -= 0.30
				else: level -= 0.50

		# Adjust refreshes based on the release interval.
		interval = release.get('interval')
		if interval:
			if type == MetaCache.TypeSeason:
				if interval == MetaCache.IntervalInstantly and past:
					# Instantly released shows from the past few weeks should get an increase, while older ones should get a decrease.
					if closest and closest > 0 and closest < MetaCache.TimeWeek2: level += (1.0 if closest < MetaCache.TimeDay7 else 0.5) # 1-2 weeks.
					else: level -= 0.2
			elif type == MetaCache.TypeEpisode or type == MetaCache.TypePack: # Not for seasons.
				# If all episodes were already released, reduce the impact on the level adjustment.
				adjust = 1.0
				if past:
					status = release.get('status')
					try: last = release['last']['type'][Media.Episode]
					except: last = None
					if status in MetaTools.StatusesPast: adjust = 0.2 # Show has ended.
					elif last and Media.Finale in last and (Media.Outer in last or Media.Inner in last): adjust = 0.3 # Season has ended.
					else: adjust = 0.5
				elif future:
					adjust = 0.5

				if interval == MetaCache.IntervalDaily: level += (3.5 if type == MetaCache.TypePack else 3.0) * adjust
				elif interval == MetaCache.IntervalWeekly: level += (3.0 if type == MetaCache.TypePack else 2.5) * adjust
				elif interval == MetaCache.IntervalBatchly: level += 0.5 * adjust
				elif interval == MetaCache.IntervalInstantly and past:
					# Instantly released shows from the past few weeks should get an increase, while older ones should get a decrease.
					if closest and closest > 0 and closest < MetaCache.TimeWeek2: level += (3.0 if closest < MetaCache.TimeDay7 else 1.5) # 1-2 weeks.
					else: level -= 0.5 * adjust

		# Adjust refreshes based on the number of seasons/episodes.
		if type == MetaCache.TypeSeason or type == MetaCache.TypeEpisode or type == MetaCache.TypePack:
			count = release.get('count')
			count = (count.get(type) or 0) if count else 0
			if count:
				if type == MetaCache.TypeSeason: quantity = MetaCache.QuantitySeason
				elif type == MetaCache.TypeEpisode: quantity = MetaCache.QuantityEpisode
				elif type == MetaCache.TypePack: quantity = MetaCache.QuantityPack
				else: quantity = None

				if quantity:
					if count <= quantity[0]: # Few
						level += min(0.7 if past else 0.35 if future else 1.0, 1 - (count / float(quantity[0])))
					else:
						exceed = count > quantity[1]
						base1 = 1.5 if past else 1.0 if future else (0.8 if exceed else 0.6)
						base2 = (count / float(quantity[1])) if exceed else ((count - quantity[0]) / float(quantity[1] - quantity[0]))
						level -= min(base1, base2) # Only subtract base1 OR base2 (min), but not both, otherwise too much would be subtracted.

		level = Math.roundClosest(level, base = 1)
		level = min(max(level, MetaCache.ReleaseLevel0), MetaCache.ReleaseLevel5)

		self._releaseTest(type = type, item = item, release = release, level = level)

		return level

	def _releaseLookup(self, type, item):
		# This takes 15-30ms for 50 titles.
		# 99% of this time is spend on the first lookup, which will initialize things in MetaManager.release(), but after that each additional lookup only takes nanoseconds.
		# Packs take slightly longer than the rest of the metadata, since they are initialized with MetaPack.instance(), which can take long, especially for larger packs.
		# However, since the pack will be used later on by the calling code, the initialization will be done in any case, and this will therefore not increase the overall process time.
		return MetaManager.release(media = type, metadata = item, extract = True)

	def _releaseTime(self, type, item):
		try:
			release = self._releaseLookup(type = type, item = item)
			if release:
				release = release.get('time')
				if release:
					# For seasons, use the latest season premiere instead of the show premiere.
					# Otherwise, if there is a new future season which is on IMDb, but not on Trakt yet, the metadata will remain partial until the season appears on Trakt/TVDb.
					# Then there will be no redos, since the show's premiere might have been years ago, and the first bracket's redo limit is only 1, aka no redos.
					# By using the last season premiere instead, the redo age is shorter, and therefore a later bracket will be picked, which will have a few redos before giving up.
					if type == MetaCache.TypeSeason:
						try:
							if release[1]: return release[1]
						except: pass

					return next(i for i in release if i)
		except: pass
		return None

	def _releaseLog(self, type, status, refresh, bracket, level, period, outdated, age, developer = True):
		if not developer or self.mDeveloper:
			releases = {
				'Regular1'		: MetaCache.TimeReleaseRegular1,
				'Regular2'		: MetaCache.TimeReleaseRegular2,
				'Regular3'		: MetaCache.TimeReleaseRegular3,
				'Regular4'		: MetaCache.TimeReleaseRegular4,
				'Regular5'		: MetaCache.TimeReleaseRegular5,

				'Occasional1'	: MetaCache.TimeReleaseOccasional1,
				'Occasional2'	: MetaCache.TimeReleaseOccasional2,
				'Occasional3'	: MetaCache.TimeReleaseOccasional3,
				'Occasional4'	: MetaCache.TimeReleaseOccasional4,
				'Occasional5'	: MetaCache.TimeReleaseOccasional5,

				'Rare1'			: MetaCache.TimeReleaseRare1,
				'Rare2'			: MetaCache.TimeReleaseRare2,
				'Rare3'			: MetaCache.TimeReleaseRare3,
				'Rare4'			: MetaCache.TimeReleaseRare4,
				'Rare5'			: MetaCache.TimeReleaseRare5,

				'Incomplete1'	: MetaCache.TimeReleaseIncomplete1,
				'Incomplete2'	: MetaCache.TimeReleaseIncomplete2,
				'Incomplete3'	: MetaCache.TimeReleaseIncomplete3,

				'Outdated1'		: MetaCache.TimeReleaseOutdated1,
				'Outdated2'		: MetaCache.TimeReleaseOutdated2,
				'Outdated3'		: MetaCache.TimeReleaseOutdated3,
			}

			message = 'Bracket: %s-Level%s-%s | Period: %s -> %s | Release Age: %s' % (refresh.capitalize(), level, '%s', self._logDuration(period, places = False), self._logDuration(outdated, places = False), self._logDuration(age))
			for k, v in releases.items():
				if v == bracket: return message % k

			# This should only happen if a new bracket was created, but not added to the "releases" dict above.
			return message % 'UNKNOWN'

	# Run a test for the release level calculation.
	# Input: item = [{'media' : Media.Show, 'imdb' : 'tt...', 'season' : 1}, {'media' : Media.Show, 'imdb' : 'tt...', 'season' : 2}]
	def releaseTest(self, items, preload = True):
		# Make sure the metadata is in the database.
		if preload:
			manager = MetaManager.instance()
			items2 = Tools.copy(items) # Since the dicts get filled with the full metadata.
			for item in items2:
				if MetaCache.TypeSeason in item: item['media'] = Media.Episode
				elif not item.get('media'): item['media'] = Media.Movie
				manager.instance().metadata(items = [item], quick = 100)

		self.mTest = []
		for item in items:
			type = item.get('type') or item.get('media')
			if not type and MetaCache.TypeSeason in item: type = MetaCache.TypeShow

			types = [type]
			if Media.isSerie(type):
				type = MetaCache.TypeShow
				types = [MetaCache.TypeShow, MetaCache.TypeSeason, MetaCache.TypeEpisode, MetaCache.TypePack]

			test = {'type' : type, 'id' : {i : item.get(i) for i in ['imdb', 'trakt', 'tmdb', 'tvdb']}, 'test' : {}}
			self.mTest.append(test)

			for i in types:
				self.select(type = i, items = [Tools.copy(item)], memory = False)

		current = Time.timestamp()
		self._log('Release Level Tests')
		for test in self.mTest:
			Logger.log('%s [IMDb: %s | Trakt: %s | TMDb: %s | TVDb: %s] %s' % (test['type'].upper(), test['id']['imdb'], test['id']['trakt'], test['id']['tmdb'], test['id']['tvdb'], test['title']))
			for k, v in test['test'].items():
				count = v['count']
				count = (str(count)) if count else '--'

				interval = v['interval']
				interval = (str(interval.capitalize())) if interval else '--'

				time = v['time']
				age = '--'
				if time:
					age = self._logDuration(current - time)
					time = Time.format(v['time'], format = '%Y-%m-%d %H:%M')
				else:
					time = '--'

				Logger.log('     %s Level: %s Count: %s Interval: %s Age: %s Time: %s' % ((k.capitalize() + ':').ljust(10), (str(v['level'])).ljust(4), count.ljust(4), interval.ljust(12), age.ljust(10), time))

	def _releaseTest(self, type, item, release, level):
		if not self.mTest is None:
			test = None
			for i in self.mTest:
				for j in ['imdb', 'trakt', 'tmdb', 'tvdb']:
					id = i['id'].get(j)
					if id and id == item.get(j):
						test = i
						for k in ['imdb', 'trakt', 'tmdb', 'tvdb']:
							test['id'][k] = item.get(k)
						break
				if test: break

			test['title'] = item.get('tvshowtitle') or item.get('title')

			try: time = release.get('time')[0 if (type == MetaCache.TypeMovie or type == MetaCache.TypeSet or type == MetaCache.TypeShow) else 1 if type == MetaCache.TypeSeason else 2]
			except: time = None

			try: count = release['count'][type]
			except: count = None

			try: interval = release['interval']
			except: interval = None

			test['test'][type] = {
				'level' : level,
				'time' : time,
				'count' : count,
				'interval' : interval,
			}

	##############################################################################
	# EXTERNAL
	##############################################################################

	@classmethod
	def external(self):
		if MetaCache.ExternalPath is None:
			MetaCache.Lock.acquire()
			if MetaCache.ExternalPath is None:
				try:
					path = System.pathMetadata()
					if path:
						path = File.joinPath(path, 'resources', 'data', 'metadata.db')
						if File.exists(path):
							if MetaTools.instance().settingsExternal():
								MetaCache.ExternalPath = path
							else:
								self.__log(message = 'The "Preprocessed Metadata" setting is disabled although the Gaia Metadata addon is installed. Menus might load faster if you enable the "Preprocessed Metadata" setting.')
								MetaCache.ExternalPath = False
						else:
							MetaCache.ExternalPath = False
					else:
						MetaCache.ExternalPath = False
				except:
					Logger.error()
					MetaCache.ExternalPath = False
			MetaCache.Lock.release()
		return MetaCache.ExternalPath

	@classmethod
	def externalAvailable(self):
		return bool(self.external())

	def _external(self):
		if MetaCache.ExternalDatabase is None:
			path = self.external()
			if path:
				MetaCache.Lock.acquire()
				MetaCache.ExternalDatabase = Database(path = path)
				MetaCache.Lock.release()
		return MetaCache.ExternalDatabase

	@classmethod
	def _externalEnable(self):
		MetaCache.ExternalPath = None
		MetaCache.ExternalDatabase = None

	@classmethod
	def _externalDisable(self):
		MetaCache.ExternalPath = False
		MetaCache.ExternalDatabase = False

	@classmethod
	def externalBulk(self):
		return MetaCache.instance(generate = True)._selectValue(query = 'SELECT COUNT(*) FROM `%s`;' % MetaCache.TypeBulk)

	@classmethod
	def externalGenerate(self, input = None, output = None, sets = None):
		from lib.meta.providers.imdb import MetaImdb

		if input is None:
			input = MetaCache.instance(generate = True)._mPath
		if output is None:
			output = System.temporary(directory = 'metadata', gaia = True, make = True, clear = True)
			output = File.joinPath(output, 'metadata.db')

		copied = File.copy(pathFrom = input, pathTo = output, overwrite = True)
		if not copied:
			self.__log(message = 'The external database could not be copied.')
			return False

		queries = []
		database = Database(path = output, compression = MetaCache.ExternalCompression)

		# Remove unnecessary IMDb bulk entries which makes the database too large.

		bulk = MetaCache.TypeBulk
		database._execute(query = 'CREATE TABLE `temp_%s` (idImdb TEXT, data TEXT, PRIMARY KEY(idImdb));' % bulk, commit = True)

		# Remove titles with too few votes, and remove episodes for unpopular shows.
		limitGlobal = 50 # Minimum votes to be included.
		limitShow = 500 # Less votes than this and only the show rating is included.
		limitEpisode = 2000 # Less votes than this and only the show and S01 ratings are included.

		chunks = []
		items = database._select(query = 'SELECT idImdb, data FROM `%s`;' % bulk)
		for item in items:
			if Pool.aborted(): return False

			data = Converter.jsonFrom(database._decompress(item[1]))
			if not data:
				self.__log(message = 'Invalid IMDb bulk entry or incorrect compression algorithm.')
				continue

			votes = None
			media = None
			if Tools.isArray(data):
				media = Media.Movie
				votes = data[1]
			elif Tools.isDictionary(data) and MetaImdb.BulkIdShow in data:
				media = Media.Show
				votes = data[MetaImdb.BulkIdShow][1]
			if votes and votes >= limitGlobal:
				if media == Media.Show:
					if votes < limitShow: data = data[MetaImdb.BulkIdShow]
					elif votes < limitEpisode: data = {k : v for k, v in data.items() if k == MetaImdb.BulkIdShow or k == '1'}

				chunks.append(item[0])
				chunks.append(database._compress(Converter.jsonTo(data), limit = 1))
				if len(chunks) >= 1000:
					query = 'INSERT OR REPLACE INTO `temp_%s` (idImdb, data) VALUES %s;' % (bulk, ', '.join((['(?, ?)'] * int(len(chunks) / 2.0))))
					database._insert(query = query, parameters = chunks, commit = False)
					chunks = []

		database._commit()
		database._execute(query = 'DROP TABLE `%s`;' % bulk, commit = True, compact = False)
		database._execute(query = 'ALTER TABLE `temp_%s` RENAME TO `%s`;' % (bulk, bulk), commit = True, compact = False)
		database._commit()
		database._compact()

		for i in database._tables():
			primary = ''
			extra1 = ''
			extra2 = ''
			extra3 = ''
			if i == MetaCache.TypeMovie:
				primary = 'idImdb, idTmdb, idTrakt'
			elif i == MetaCache.TypeSet:
				primary = 'idTmdb'
				if sets: queries.append('DELETE FROM `%s` WHERE idTmdb NOT IN (%s);' % (i, ','.join(['"%s"' % j for j in sets]))) # Remove less popular sets.
			elif i == MetaCache.TypeShow or i == MetaCache.TypeSeason:
				primary = 'idImdb, idTvdb, idTrakt'
			elif i == MetaCache.TypeEpisode:
				extra1 = 'season INTEGER, '
				extra2 = 'season, '
				extra3 = ', season'
				primary = 'idImdb, idTvdb, idTrakt, season'
			elif i == MetaCache.TypePack:
				primary = 'idImdb, idTvdb, idTrakt'
			elif i == MetaCache.TypeBulk:
				continue

			# Old SQLite does not have "DROP COLUMN", copy the table instead.
			#queries.append('DELETE FROM `%s` WHERE complete != 1;' % i) # Many specials have incomplete metadata. Keep them. We now copy this value below.
			queries.append('CREATE TABLE `temp_%s` (idImdb TEXT, idTmdb TEXT, idTvdb TEXT, idTrakt TEXT, %sdata TEXT, PRIMARY KEY(%s));' % (i, extra1, primary))

			queries.append('INSERT INTO `temp_%s` SELECT idImdb, idTmdb, idTvdb, idTrakt, %sdata FROM `%s`;' % (i, extra2, i))
			queries.append('DROP TABLE `%s`;' % i)
			queries.append('ALTER TABLE `temp_%s` RENAME TO `%s`;' % (i, i))

			# Do not add too many extra indices, since it can substantially increase the database size.
			if i == MetaCache.TypeSet:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idTmdb);' % (i, i))
			elif i == MetaCache.TypeEpisode:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb, season);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb, season);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb, season);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt, season);' % (i, i))
			else:
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_1 ON `%s`(idImdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_2 ON `%s`(idTmdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_3 ON `%s`(idTvdb);' % (i, i))
				queries.append('CREATE INDEX IF NOT EXISTS %s_index_4 ON `%s`(idTrakt);' % (i, i))

		for query in queries:
			if Pool.aborted(): return False
			database._execute(query = query, commit = True, compact = False)
		database._commit()
		database._compact()

		return output

	##############################################################################
	# COPY
	##############################################################################

	@classmethod
	def copy(self, type, data, deep = False, cache = False):
		# Do not do this for packs, since they should not change between calls, and can take very long to copy (eg: One Piece 150-250ms).
		# Update (2025-11): Packs are now also shallow-copied, so that MetaCache.Attribute can be edited for different callers getting the metadata from memory.
		# This is important for pack metadata when MetaManager._metadataClean() removes MetaCache.Attribute, which would remove it for all dicts if it was not shallow copied.
		# More info on this in MetaPack.instanceId().
		#if not type == MetaCache.TypePack:

		# NB: This DEEP copy can be very slow, and ends up defeating the purpose of "faster" memory access.
		# This can take 100-200 ms for an episode list with 20+ episodes, and even longer if there are 100s of episodes in the season.
		# When loading the episode Progress menu, multiple episode lists have to be loaded for each entry, and if many have 20+ episodes, it can cause a multiple-second delay in the menu loading.
		# Not sure if a deep copy is really necessary for some code?
		# Instead, do a semi-deep-shallow copy. Aka only copy the outer dict structure, the seasons/episodes outer list structure and the outer dict for each of the season/episode in the list.
		# Also deep-copy the "number" dict which is edited later on, and if not copied, causes issues when the same episode is retrieved during the same execution with different number types, eg: Core._scrapeNumber().
		# The semi-deep-shallow copy only takes 2-5ms, even for 20+ episodes.
		# NB: We might need to add additional nested attributes to deep-copy if we at some point discover bugs with edited dicts.
		#data = Tools.copy(data)

		# List of metadata dicts.
		if Tools.isArray(data):
			data = [self.copy(type = type, data = i, deep = deep, cache = cache) for i in data]

		# Single metadata dict.
		else:
			# If "deep=None": Do a deep copy, except for packs.
			# Movies/sets/shows/seasons are very quick to deep-copy (less than 10ms).
			# Episodes can take slightly longer, especially if there are a lot of episodes in a season (20-50ms).
			# Packs take by far the longest. Small packs take less than 10-50ms. Medium packs take 100-300ms (eg: tt0388629). Larger packs take 500-1000ms (eg: tt0112004).
			# Since the nested data in packs is not supposed to change, a shallow copy is fine and very fast (0-1ms).
			# The only thing that might change in a pack dict are the outer-most values, such as the MetaCache.Attribute and MetaPack.Identifier. But these are copied in any case with a shallow-copy.
			if deep is None: deep = False if type == MetaCache.TypePack else True

			data = Tools.copy(data, deep = deep)

			# Only if shallow-copied.
			if not deep:
				# In some cases copy the cache attribute data, since it might get changed if the metadata is refreshed.
				# A shallow copy should be fine, since only the first-level MetaCache.Attribute dict values are changed.
				# And this avoids a costly copy of the MetaCache.AttributePart data.
				if cache:
					try: data[MetaCache.Attribute] = Tools.copy(data[MetaCache.Attribute], deep = False)
					except: pass

				if type == MetaCache.TypeSeason or type == MetaCache.TypeEpisode:
					lookup = 'seasons' if type == MetaCache.TypeSeason else 'episodes'
					values = data.get(lookup)
					if values:
						temp = []
						for i in values:
							value = Tools.copy(i, deep = False)

							# Important to copy, since we update the dictionary, and its internal lists.
							# Otherwise the same episode lookup, but with different number types might cause inconsistencies with the nested "number" dictionary.
							number = i.get('number')
							if number: value['number'] = Tools.copy(number, deep = True) # Deep copy.

							temp.append(value)
						data[lookup] = temp

		return data

	##############################################################################
	# MEMORY
	##############################################################################

	# These functions store previously retrieved/select() and updated/insert() metadata in memory until the end of the Python process execution.
	# This can substantially improve overall performance when the same metadata is retrieved multiple times during the same execution.
	# This is especially important for pack metadata retrieval, which can easily take 100-200+ ms for most packs, but even longer for larger packs.
	# In MetaManager.metadataEpisode(), the pack is retrieved multiple times through _metadataPackLookup() and _metadataPackAggregate(), and we do not always want to use disk I/O, decoding the JSON, and initializing MetaPack every time we access it.

	def _memory(self, type, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None, copy = True):
		for id in self._memoryId(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season):
			item = self.mMemory.get(id)
			if item:
				# Copy here again, since we do not want to send out the dictionary that we might later access/copy again.
				# This should be fast and not cause too much delay, since it is a shallow-copy.
				if copy: item = self._memoryCopy(type = type, item = item, cache = True)
				return item
		return None

	def _memoryUpdate(self, item, type, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None, copy = True):
		if copy: item = self._memoryCopy(type = type, item = item)
		for id in self._memoryId(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season):
			self.mMemory[id] = item

	def _memoryRemove(self, type, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None):
		for id in self._memoryId(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season):
			try: del self.mMemory[id]
			except: pass

	def _memoryId(self, type, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None):
		ids = []

		base = str(type) + '_%s_%s'
		if not season is None: base += '_' + str(season)

		if idTrakt: ids.append(base % (MetaTools.ProviderTrakt, idTrakt))
		if idImdb: ids.append(base % (MetaTools.ProviderImdb, idImdb))
		if idTmdb: ids.append(base % (MetaTools.ProviderTmdb, idTmdb))
		if idTvdb: ids.append(base % (MetaTools.ProviderTvdb, idTvdb))

		return ids

	def _memoryCopy(self, type, item, deep = False, cache = False):
		# NB: If item is None, it probably means the compression algorithm used for the local metadata.db is different to the one currently used for decompression.
		# Eg: the user imported and old database, but the new system uses different compression algorithm, or has differnt benchmarks for the algorithms.
		# This should not happen.
		#if not item is None:

		# Important to copy here when called from select(), since the returned dict can be updated.
		return self.copy(type = type, data = item, deep = deep, cache = cache)

	##############################################################################
	# QUERY
	##############################################################################

	def _query(self, type, idImdb = None, idTmdb = None, idTvdb = None, idTrakt = None, season = None, best = False, full = False):
		values = []
		parameters = []

		values1 = {}
		values2 = {}
		if type == MetaCache.TypeMovie:
			values1 = {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'idTmdb' : idTmdb}
			values2 = {'idTvdb' : idTvdb}
		elif type == MetaCache.TypeSet:
			values1 = {'idTmdb' : idTmdb}
		elif type == MetaCache.TypeShow or type == MetaCache.TypeSeason or type == MetaCache.TypeEpisode:
			values1 = {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'idTvdb' : idTvdb}
			values2 = {'idTmdb' : idTmdb}
		elif type == MetaCache.TypePack:
			values1 = {'idImdb' : idImdb, 'idTrakt' : idTrakt, 'idTvdb' : idTvdb}
			values2 = {'idTmdb' : idTmdb}

		for k, v in values1.items():
			if v:
				values.append(k)
				parameters.append(v)
		if not values or full or full is None:
			for k, v in values2.items():
				if v:
					values.append(k)
					parameters.append(v)

		if values:
			if best: base = Tools.copy(parameters)

			# Check the comment below on why to use AND for delete queries.
			operator = ' AND ' if full else ' OR '

			query = '(%s)' % operator.join(['%s = ?' % i for i in values])
			if not season is None:
				query = '(%s AND season = ?)' % query
				parameters.append(season)

			# Sometimes there is a mismatch between IDs on the different platforms.
			# In these cases, Trakt often adds 2 (technically identical) shows to their database, one pointing to the TMDb show, and one to the TVDb show.
			# 	Eg: The Vikings (2015)
			#		IMDb: -				TMDb: 204558	TVDb: 313970	Trakt: 108936 (the-vikings-2015)
			#		IMDb: tt19401686	TMDb: 204558	TVDb: -			Trakt: 248534 (the-vikings-2015-248534)
			# This has also been observed with other shows, which have been "fixed" on Trakt by now.
			#	Eg:
			#		{"trakt":100814,"slug":"tvf-pitchers-2015","tvdb":298807,"imdb":"tt4742876","tmdb":63180}
			#		{"trakt":185757,"slug":"tvf-pitchers-2015-185757","tvdb":298868,"imdb":"tt4742876","tmdb":63180}
			# When searching for "Vikings" under the shows search menu, and we then reopen the cached menu again and again, all titles are cached, except this one, which is always re-retrieved in the foreground, making the menu take a short while to load.
			# The issue is the DELETE statement which deletes if ANY of the IDs match (in this case TMDb), even if the other IDs do no match.
			# If the menu is opened once, it retrieves the 1st show. If opened again, it deletes the first show (since the TMDb matches), and then inserts the 2nd show.
			# If the menu is opened again, it deletes the 2nd show (since the TMDb matches) and inserts the 1st show. This cycle continues forever and the menu is never fully cached, since this title has to be retrieved in the foreground again and again.
			# We basically want to SELECT and DELETE based on the MOST ID matches instead of ANY matches.
			# We could have multiple queries, first trying to find a row with all IDs matching, if nothing is found try to find with one less ID, and so on. But this would require multiple queries and would slow down things.
			# Instead we count the number of ID matches using the IFF clause below and do the following:
			#	SELECT queries: match any ID, but sort based on how many IDs match, and then pick the one with most ID matches.
			#	DELETE queries: delete a row only if all IDs match. If one or more IDs do not match, do not delete, and insert the item a second time with the alternative IDs. This should not happen very often and therefore not waste too much extra disk space.
			# UPDATE (2025-01): Many Windows devices seem to still use an old SQLite version (prior to 3.32.0) that does not have IFF function, causing the error:
			#	GAIA ERROR [Database Query]: no such function: IIF -- SELECT data ...
			# https://stackoverflow.com/questions/4874285/if-statement-alternative-in-sqlite/61826915#61826915
			if best:
				parameters += base
				#query = (query, '(%s)' % ' + '.join(['IIF(%s = ?, 1, 0)' % i for i in values]))
				query = (query, '(%s)' % ' + '.join(['(CASE WHEN %s = ? THEN 1 ELSE 0 END)' % i for i in values]))

			return query, parameters

		return None, None

	##############################################################################
	# DETAILS
	##############################################################################

	def details(self):
		count = {}
		for media in [Media.Movie, Media.Set, Media.Show, Media.Pack, Media.Season, Media.Episode]:
			count[media] = self._selectValue(query = 'SELECT COUNT(*) FROM `%s`' % media)
		return {
			'time'	: Time.timestamp(),
			'size'	: File.size(self._mPath), # Sometimes this returns 0 if a new database is created. Restart Kodi after having created the file to get the size.
			'count'	: count,
		}

	##############################################################################
	# INSERT
	##############################################################################

	# NB: "deep=None": deep-copy all, except for packs which are only shallow-copied.
	def insert(self, type, items, time = None, wait = None, copy = True, deep = None):
		if not items: return None

		# Make a copy of the items.
		# Even for large lists, this should only take a few milliseconds.
		# This is needed, since we delete the "temp" attribute in _insertItems() before inserting the item into the database.
		# This "temp" attribute is still needed outside this function, and we do not want to delete it there as well, because lists/dicts are passed by reference. Deleting the attribute here, deletes it everywhere this dict reference is used.
		# Technically we could only make a shallow copy of each item individually: [Tools.copy(i, deep = False) for i in items], since we only remove an attribute on the first dict level, which only requires a shallow copy.
		# However, since the database insert below can run in a thread, other code, like from MetaTools, could manipulate the dict, which we might not want for the database insert. So rather do a deep copy.
		# Also, do the deep copy here, and not in the thread. Since we do not want other code, which might possibly edit the dict, to continue before the thread gets a chance to do the copy.
		# Note that packs can take very long to copy. Eg: One Piece (150-200ms), Hollyoaks (800-900ms).
		# Update (2025-11): Only copy if it is a foreground refresh. Background refreshes already make a deep copy before the refresh in MetaManager._metadataCache().
		# Background refreshes should only do a refresh without any code using the metadata afterwards. Note that it still gets inserted in the MetaCache._memory().
		if copy: items = self.copy(type = type, data = items, deep = deep)

		if wait is None: wait = len(items) <= 1 # Do not use threads for small tasks.
		if wait: return self._insertItems(type = type, items = items, time = time)
		else: return Pool.thread(target = self._insertItems, kwargs = {'type' : type, 'items' : items, 'time' : time}, start = True)

	def _insertItems(self, type, items, memory = True, time = None): # _insert() already used in database.py.
		try:
			result = True
			settings = self.settingsId()
			typeMovie, typeSet, typeShow, typeSeason, typeEpisode, typePack = self._type(type)

			if time is None: time = Time.timestamp()

			# Sometimes the IDs are incorrect.
			# Especially Trakt sometimes returns the incorrect IMDb/TMDb/TVDb ID, specfically for less-known titles or newley/not-yet released titles.
			# First lookup with all available IDs and if not found, try to use individual IDs if order of importance.
			# Update: Some shows only appear on Trakt/TMDb, but not on IMDb/TVDb (eg: AVASTARS - Trakt:180301 - TMDb:125266).
			# Update: The cache ID lookups have been simplified. Any ID can now match.
			if typeEpisode: queryInsert = 'INSERT INTO `%s` (time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug, season, part, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);' % type
			else: queryInsert = 'INSERT INTO `%s` (time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug, part, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);' % type
			queryDelete = 'DELETE FROM `%s` WHERE settings = ? AND %s;' % (type, '%s')

			if not Tools.isArray(items): items = [items]
			for item in items:
				try:
					if item:
						idImdb, idTmdb, idTvdb, idTrakt, idSlug = self._id(item)

						# Too many times the requests return partial metadata.
						# Give up and mark the data as complete.
						# Clear the part BLOB to save some disk space.
						# The data can still be refreshed in the normal way.
						try:
							try: part = item[MetaCache.Attribute][MetaCache.AttributePart]
							except: part = None
							if part:
								fail = part.get(MetaCache.AttributeFail, 0)
								partial = self._partial(type = type, fail = fail, time = time, item = item)
								if fail >= partial[MetaCache.AttributeFail]: part = None
								else: part[MetaCache.AttributeCause] = partial[MetaCache.AttributeCause]
								self._logPartial(type = type, fail = fail, extra = partial['log'], item = item)
						except:
							Logger.error()
							part = None

						try: del item[MetaCache.Attribute]
						except: pass
						try: del item['temp']
						except: pass
						for i in ['seasons', 'episodes']:
							values = item.get(i)
							if values:
								for j in values:
									try: del j['temp']
									except: pass

						season = None
						insert = []

						if typeEpisode:
							season = self._season(item)
							insert.append(season)

						if memory: self._memoryUpdate(item = item, type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season)

						# Check _query() for more info on the use of "full".
						query, parameters = self._query(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season, full = True)
						if query and parameters:
							deleted = self._delete(query = queryDelete % query, commit = False, parameters = [settings] + parameters)

							# Sometimes the TMDb or IMDb IDs of a title change at a later time.
							# Eg: Mexico Countryballs (tt35508234) had a TMDb ID in MetaCache "282395" and no Trakt ID at all.
							# Eg: Later when the metadata was refreshed, the new metadata had a TMDb ID of "283851" and a Trakt ID of "273938".
							# This causes the delete statement to fail if not all the provided IDs match a row, and the newly refreshed metadata therefore cannot be inserted.
							#	UNIQUE constraint failed: show.settings, show.idImdb, show.idTvdb, show.idTrakt -- INSERT INTO `show` (time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug, part, data) ...
							# If the delete fails, try to delete by individual IDs.
							# This is slightly inefficient, since a 2nd DELETE query is executed if the 1st query did not delete anything.
							# If the item is not in the database, the 2nd query is still executed, but this should not take too long and only happens the 1sat time if an item is not in the database yet.
							# We can add the MetaCache.Attribute to the new metadata in eg MetaManager.metadataShowUpdate(), and only execute the 2nd delete if the metadata actually comes from the cache.
							# But this will probably create more overhead compared to just executing the 2nd query unnecessarily if it is inserted the 1st time.
							if not deleted:
								query, parameters = self._query(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season, full = None)
								if query and parameters: deleted = self._delete(query = queryDelete % query, commit = False, parameters = [settings] + parameters)

						query, parameters = self._query(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season)
						if query and parameters: # At least one of the IDs has been set.
							compressedPart = self._compress(Converter.jsonTo(part)) if part else None
							compressedData = self._compress(Converter.jsonTo(item)) if item else None
							self._insert(query = queryInsert, commit = False, parameters = [time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug] + insert + [compressedPart, compressedData])
				except:
					Logger.error()
					result = False

			self._commit()
			return result
		except:
			Logger.error()
			return False

	##############################################################################
	# SELECT
	##############################################################################

	def select(self, type, items, memory = True):
		try:
			settings = self.settingsId()
			typeMovie, typeSet, typeShow, typeSeason, typeEpisode, typePack = self._type(type)

			current = Time.timestamp()

			# Sometimes the IDs are incorrect.
			# Especially Trakt sometimes returns the incorrect IMDb/TMDb/TVDb ID, specfically for less-known titles or newley/not-yet released titles.
			# First lookup with all available IDs and if not found, try to use individual IDs if order of importance.
			querySelect = 'SELECT time, settings, part, data FROM `%s` WHERE %s ORDER BY %s DESC, time DESC;' % (type, '%s', '%s')

			for i in range(len(items)):
				try:
					items[i][MetaCache.Attribute] = {MetaCache.AttributeRefresh : MetaCache.RefreshForeground, MetaCache.AttributeValid : False, MetaCache.AttributeStatus : MetaCache.StatusInvalid, MetaCache.AttributeTime : None, MetaCache.AttributeSettings : None, MetaCache.AttributePart : None}
					idImdb, idTmdb, idTvdb, idTrakt, idSlug = self._id(items[i])

					season = self._season(items[i]) if typeEpisode else None

					if memory:
						metadata = self._memory(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season)
						if metadata:
							# Do not update the dict for packs. Check comments at the end of this function.
							# Update (2025-11): Pack metadata is now also shallow-copied. So this is not needed anymore and would only create problems with MetaManager._metadataClean().
							#items[i][MetaCache.Attribute][MetaCache.AttributeRefresh] = MetaCache.RefreshNone
							#items[i][MetaCache.Attribute][MetaCache.AttributeStatus] = MetaCache.StatusMemory
							#items[i][MetaCache.Attribute][MetaCache.AttributeTime] = current
							#items[i][MetaCache.Attribute][MetaCache.AttributeValid] = True # Set to True, since only valid items to added to memory.
							#if type == MetaCache.TypePack:
							#	metadata[MetaCache.Attribute] = items[i][MetaCache.Attribute]
							#	items[i] = metadata
							#else:
							#	Tools.update(items[i], metadata, none = False, lists = True, unique = True, inverse = True)

							Tools.update(items[i], metadata, none = False, lists = True, unique = True, inverse = True)

							# Update these after Tools.update(), since the memory data already has MetaCache.Attribute from when it was saved to memory.
							items[i][MetaCache.Attribute][MetaCache.AttributeRefresh] = MetaCache.RefreshNone
							items[i][MetaCache.Attribute][MetaCache.AttributeStatus] = MetaCache.StatusMemory
							items[i][MetaCache.Attribute][MetaCache.AttributeTime] = current
							items[i][MetaCache.Attribute][MetaCache.AttributeValid] = True # Set to True, since only valid items are added to memory.

							continue

					# Check _query() for more info on the use of "best".
					query, parameters = self._query(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season, best = True)

					if query and parameters:
						query = querySelect % query
						datas = self._select(query = query, parameters = parameters)

						# Check the external preprocessed database.
						external = False
						if not datas and self.mExternal:
							externaled = self._external()
							if externaled:
								datas = externaled._select(query = query.replace('time, settings, part,', '').replace(', time DESC', ''), parameters = parameters)
								if datas:
									for j in range(len(datas)):
										datas[j] = [current, None, None, datas[j][0]]
									external = True

						if datas:
							selection = None

							# First try to pick the one with the same settings.
							for data in datas:
								if data[1] == settings:
									selection = data
									break

							# Otherwise pick the one with different settings.
							# Note that query returns the values in order of time, so picking the first is picking the newest.
							if not selection: selection = datas[0]
							time = selection[0]
							setting = selection[1]
							part = selection[2]
							difference = current - time

							metadata, error = self._decompress(selection[3], type = MetaCache.ExternalCompression if external else None, full = True)
							if metadata: metadata = Converter.jsonFrom(metadata)
							if part: part = Converter.jsonFrom(self._decompress(part))

							# Add a new random pack identifier the first time the pack metadata was retrieved from memory.
							# This ensure that the pack is only initialized once for the same data, improving efficiency.
							# More details under MetaPack.instanceId().
							# NB: Do this BEFORE adding the dict to memory, since it gets shallow-copied there and the identifier should also be copied.
							# NB: Do this BEFORE _release() below.
							if type == MetaCache.TypePack and metadata: MetaPack.instanceId(pack = metadata, update = True)

							if not(external and metadata is None): # Cannot decompress the external metadata, due to an unsupported compression algorithm.
								log = None
								old = self._old(type = type, item = metadata, current = current) # Refresh slightly more for newer titles.

								refresh = MetaCache.RefreshNone
								status = MetaCache.StatusCurrent

								# This should rarely happen.
								# Sometimes when something goes wrong during a database insert, the data in the database can be corrupt, which causes decompression to fail.
								# Eg: Kodi is killed while Gaia was still writing to the databases.
								# If the data becomes corrupt, do a foreground refresh and write the new data to the database.
								# There is one exception to this. In some of these cases the entire database becomes corrupt, not just a single row.
								# Refreshing the data will not help in this case, since there will be an error when trying to insert the refreshed data into the database.
								# In this case, the only thing that works is deleting the entire database and repopulate it anew (not great if it took a long time to build up the metadata cache).
								if error and metadata is None:
									refresh = MetaCache.RefreshForeground
									status = MetaCache.StatusInvalid

								# Data comes from the external preprocessed database.
								# Always force a refresh, since external data might be outdated or not according to the users settings.
								elif setting is None:
									refresh = MetaCache.RefreshBackground
									status = MetaCache.StatusExternal

								# Always refresh obsolete data, even when they are from differnt settings.
								elif difference > MetaCache.TimeObsolete[old]:
									refresh = MetaCache.RefreshForeground
									status = MetaCache.StatusObsolete

								# Data available, but with different settings.
								# Refresh in the background and return the old data.
								elif not setting == settings:
									refresh = MetaCache.RefreshBackground
									status = MetaCache.StatusSettings

								# Data antiquated and needs a fresh update.
								# Refresh in the background.
								elif difference > MetaCache.TimeAntiquated[old]:
									refresh = MetaCache.RefreshBackground
									status = MetaCache.StatusAntiquated

								else:
									# Data outdated according to the release date and needs a fresh update.
									#	If the release date of the title is recent, reduce the refresh time to update the metadata more often.
									#	For recently released movies, the rating is often higher than it should be, since the early ratings cast by people are often higher than the average rating after a few days/weeks with more votes.
									#	For newley released seasons/episodes, besides the rating, there might be other outdated metadata, like the plot, cast, episode title, or release date. For many new episodes there are no ratings within the first day or so of release.
									# Some important metadata is missing and needs a fresh update.
									#	Movies might not have a digital/physical release date yet, and needs to be refreshed, since those dates are needed for the Arrivals menu.
									# Refresh in the background.
									release = self._release(type = type, item = metadata, time = time, current = current)
									if release and difference > release['time']:
										refresh = MetaCache.RefreshBackground
										status = release.get('status') or MetaCache.StatusReleased # Do not use StatusPartial here, since that status is reserved for partial provider data instead of missing attributes.
										log = release.get('log')

									elif part:
										# Data is available, but the data is partial.
										# Refresh in the background.
										# Do this AFTER checking checking _release() above, since partial refreshes should only be done for newer data.
										# Do this a maximum of once an hour, to avoid constant refreshes if the menu is reloaded in a short period of time.
										partial = part.get(MetaCache.AttributeCause)
										if difference > self._partialTime(partial = partial):
											refresh = MetaCache.RefreshBackground
											status = MetaCache.StatusPartial
											log = self._partialLog(partial = partial, fail = part.get(MetaCache.AttributeFail))

								# Do not print to log here, since MetaManager._metadataCache() might not actually do a refresh if "quick" is used.
								# Return the log message an print from MetaManager.
								log = self._logRefresh(type = type, refresh = refresh, status = status, time = time, current = current, extra = log, item = metadata, log = False)

								valid = status in MetaCache.StatusValid
								items[i][MetaCache.Attribute][MetaCache.AttributeRefresh] = refresh
								items[i][MetaCache.Attribute][MetaCache.AttributeValid] = valid
								items[i][MetaCache.Attribute][MetaCache.AttributeStatus] = status
								items[i][MetaCache.Attribute][MetaCache.AttributeTime] = time
								items[i][MetaCache.Attribute][MetaCache.AttributeSettings] = setting
								if part: items[i][MetaCache.Attribute][MetaCache.AttributePart] = part
								if log: items[i][MetaCache.Attribute][MetaCache.AttributeLog] = log

								if memory and valid and not external and not metadata is None and refresh == MetaCache.RefreshNone:
									self._memoryUpdate(item = metadata, type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season)

								# Update (2025-11): This is not needed anymore, since pack metadata is now also shallow-copied and MetaPack.instance() uses a different ID to handle singular initializations.
								# More info in MetaPack.instanceId().
								#if type == MetaCache.TypePack:
								#	# For packs, do not update the "items" dictionaries passed in, but instead replace them with the retrieved dictionaries.
								#	# Otherwise when calling MetaPack.instance(...) internally from MetaCache, MetaCache will use in a different dict than returned to MetaManager.
								#	# This will therefore result in two initializtions inside MetaPack.instance(...), because they are two different dicts, although with the same data, which increases computational time.
								#	# The "items" dictionaries only contain IDs anyway, but no other important metadata which would require a dict update, like with the other media types.
								#	# Not sure if not updating the dict, or at least creating a copy, might result in some weird behaviour, since the metadata is also cached in memory in MetaCache.
								#	# But the pack dictionary is typically only retrieved, but not edited afterwards like with other media, so it should be fine.
								#	# Also view the comments in MetaManager._metadataClean() on the implications of not copying (or doing Tools.update()) pack data.
								#	metadata[MetaCache.Attribute] = items[i][MetaCache.Attribute]
								#	items[i] = metadata
								#else:
								#	Tools.update(items[i], metadata, none = False, lists = True, unique = True, inverse = True)

								# Do not just update(), otherwise some nested dictionaries will be replaced.
								# Eg: If from movies progress, items are passed, the metadata should be added into nested dictionaries.
								# Eg: {'time' : {'watched' : 123}}
								# With just update(), the entire 'time' dictionary will be replaced with the one from metadata.
								# With Tools.update(), the 'time' dictionary gets the new values from metadata, but still keeps the old 'watched' time.
								# Also important for IMDb. Searching IMDb by genre, IMDb lists and Advanced Search only returns 1-3 genres, although the searched genre might only be 4th or 5th.
								# TMDb/Trakt often also has different genres. The searched genre is therefore manually added in MetaImdb, but might not be available from detailed metadata retrieval.
								# Hence, the basic dictionary passed into this function might contain some metadata that is not available in the cache. Do not replace it, but extend the dictionary.
								#items[i].update(metadata)
								# Update: Important to use "inverse = True".
								# This will merge lists as: metadata+items[i], instead of items[i]+metadata.
								# Otherwise if a barebone item (eg: from Discover or Search) is passed in, in can already have lists with values, but those might be incomplete or less-relevant.
								# For instance, a Trakt search returns "Vikings" with network=['Amazon'], but the detailed metadata has ['History Canada', 'History', 'Amazon', 'Prime Video'].
								# Without inverse=True, the list will be merged with 'Amazon' first in the list, but it should rather be added to the end.
								# NB: if this call is changed, also change for the memory call above.
								Tools.update(items[i], metadata, none = False, lists = True, unique = True, inverse = True)

				except: Logger.error()
		except: Logger.error()
		return items

	##############################################################################
	# LOOKUP
	##############################################################################

	# Quickly determine if items are in the ddatabase without fully retrieveing the data.
	def lookup(self, type, items):
		try:
			typeMovie, typeSet, typeShow, typeSeason, typeEpisode, typePack = self._type(type)
			current = Time.timestamp()

			queryGeneral = 'SELECT time FROM `%s` WHERE %s LIMIT(1);' % (type, '%s')
			if typeEpisode: queryEpisode = 'SELECT MAX(time), season FROM `%s` WHERE %s GROUP BY season ORDER BY season ASC;' % (type, '%s')

			for i in range(len(items)):
				try:
					idImdb, idTmdb, idTvdb, idTrakt, idSlug = self._id(items[i])
					season = self._season(items[i]) if typeEpisode else None
					episode = bool(typeEpisode and season is None)

					items[i][MetaCache.Attribute] = {MetaCache.AttributeValid : False, MetaCache.AttributeTime : None}
					if episode: items[i][MetaCache.Attribute][MetaCache.AttributeSeason] = None

					query, parameters = self._query(type = type, idImdb = idImdb, idTmdb = idTmdb, idTvdb = idTvdb, idTrakt = idTrakt, season = season, best = False)
					if query and parameters:
						query = (queryEpisode if episode else queryGeneral) % query
						if episode:
							values = self._select(query = query, parameters = parameters)
							if values:
								items[i][MetaCache.Attribute][MetaCache.AttributeValid] = True
								items[i][MetaCache.Attribute][MetaCache.AttributeTime] = max([j[0] for j in values])
								items[i][MetaCache.Attribute][MetaCache.AttributeSeason] = [j[1] for j in values]
						else:
							time = self._selectValue(query = query, parameters = parameters)
							if time:
								items[i][MetaCache.Attribute][MetaCache.AttributeValid] = True
								items[i][MetaCache.Attribute][MetaCache.AttributeTime] = time
				except: Logger.error()
		except: Logger.error()
		return items

	##############################################################################
	# DELETE
	##############################################################################

	def delete(self, type, setting):
		query = 'DELETE FROM `%s` WHERE setting = ?;' % type
		return self._delete(query = query, parameters = [setting])

	##############################################################################
	# CLEAN
	##############################################################################

	def _clean(self, time, commit = True, compact = True):
		if time:
			count = 0
			query = 'DELETE FROM `%s` WHERE time <= ?;'
			for type in MetaCache.Types:
				count += self._delete(query = query % type, parameters = [time], commit = commit, compact = compact)
			return count
		return False

	def _cleanTime(self, count):
		if count:
			times = []
			query = 'SELECT time FROM `%s` ORDER BY time ASC LIMIT ?;'
			for type in MetaCache.Types:
				time = self._selectValues(query = query % type, parameters = [count])
				if time: times.extend(time)
			if times: return Tools.listSort(times)[:count][-1]
		return None

	# Remove old records with a different settings id.
	def clearOld(self, commit = True, compact = True):
		settings = self.settingsId(refresh = True)
		query = 'DELETE FROM `%s` WHERE settings != ?;'
		for type in MetaCache.Types:
			self._delete(query = query % type, parameters = [settings], commit = commit, compact = compact)
		self._commit()
		self._compact()
		return True

	##############################################################################
	# IMPORT
	##############################################################################

	def importData(self, path, type = None):
		database = Database(path = path)

		if type is None: type = MetaCache.Types
		elif not Tools.isArray(type): type = [type]

		for i in type:
			episode = i == MetaCache.TypeEpisode
			values = database._select(query = 'SELECT time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug%s, part, data FROM `%s`;' % (', season' if episode else '', i))
			for value in values:
				query = 'INSERT INTO `%s` (time, settings, idImdb, idTmdb, idTvdb, idTrakt, idSlug%s, part, data) VALUES (?, ?, ?, ?, ?, ?, ?%s, ?, ?);' % (i, ', season' if episode else '', ', ?' if episode else '')
				self._insert(query = query, commit = False, parameters = value)

		self._commit()
		self._compact()

	##############################################################################
	# BULK
	##############################################################################

	@classmethod
	def bulkAvailable(self):
		if MetaCache.Bulk is None:
			values = self.instance()._select(query = 'SELECT idImdb FROM `%s` LIMIT(1);' % MetaCache.TypeBulk)
			MetaCache.Bulk = True if values else False
		return MetaCache.Bulk

	def bulkInsert(self, items, wait = None):
		if not items: return None
		if wait is None: wait = len(items) <= 1 # Do not use threads for small tasks.
		if wait: return self._bulkInsert(items = items)
		else: return Pool.thread(target = self._bulkInsert, kwargs = {'items' : items}, start = True)

	def _bulkInsert(self, items, memory = True):
		try:
			# The entire function takes about 25 secs on a high-end CPU and SSD.
			# The total compressed size in the database is 90MB.
			# Both time and size w1ill increase in the future as more items are added on IMDb.

			from lib.meta.providers.imdb import MetaImdb

			if Pool.aborted(): return False

			result = True
			type = MetaCache.TypeBulk

			count = 0
			limit = 2500
			delay = Pool.DelayShort

			# It is considerably faster inserting multiple rows at once.
			# For 900k items: from 3 mins down to 30 secs.
			#	50:		35-37secs
			#	100:	34-35secs
			#	200:	30-32secs
			#	250:	28-30secs
			#	300:	28-31secs
			#	400:	28-30secs
			#	500:	28-29secs
			#	750:	29-31secs
			#	1000:	29-30secs
			#	1500:	29-30secs
			#	2000:	29-30secs
			#	2500:	29-31secs
			#	5000:	29-31secs
			chunkLimit = 250 # Not much faster with a larger size. 500 works, but use less for low-end devices with limited memory.
			chunkCount = 2
			chunkTotal = chunkLimit * chunkCount

			# Updating the table can be done in one of these manners:
			#	1. Delete all rows (1 query) and then insert all (multiple queries): Fast delete, but if Pool.aborted(), either do not exit immediatly and let the queries finish, or end up with a partial database.
			#	2. Delete each row (multiple queries) and then insert all (multiple queries): Slow, but allows us to break out of the loop if Pool.aborted() and still have the full database.
			#	3. Insert-ignore all (multiple queries) and then update all (multiple queries): Slow, but allows us to break out of the loop if Pool.aborted() and still have the full database.
			#	4. Insert-or-replace (multiple queries): Fast and allows us to break out of the loop if Pool.aborted() and still have the full database.
			# Note that "commit = False" does not actually withhold writes. They are still auto-commited most of the time, even when changing SQLite's "isolation_level".
			# Hence, we cannot delete all rows with "commit = False" and exit this function without calling self._commit(). The rows are still deleted in most of the cases.
			queryInsert1 = 'INSERT OR REPLACE INTO `%s` (idImdb, data) VALUES (?, ?);' % type
			queryInsert2 = 'INSERT OR REPLACE INTO `%s` (idImdb, data) VALUES %s;' % (type, ', '.join((['(?, ?)'] * chunkLimit)))

			chunks = []
			for idImdb in list(items.keys()):  # So that we can delete from the dict while looping.
				try:
					# Free up some memory, since new JSON objects are created below.
					# This is important for low-end devices with little memory, otherwise the device might run out of free memory.
					item = items[idImdb]
					del items[idImdb]
					idImdb, item = MetaImdb.bulkPrepare(id = idImdb, data = item)

					if idImdb and item:
						# This can take quite a while.
						# Sleep in between to allow other code to execute.
						# There are around 900k items to insert, so total delay should be 3.6 secs (limit = 2500, delay = Pool.DelayShort).
						# Note that the insert does not happen with each iteration.
						count += 1
						if count > limit:
							if not Pool.check(delay = delay): break
							count = 0

						if memory: self._memoryRemove(type = type, idImdb = idImdb)

						chunks.append(idImdb)
						chunks.append(self._compress(Converter.jsonTo(item), limit = 1)) # Compress even small data.
						if len(chunks) == chunkTotal:
							self._insert(query = queryInsert2, parameters = chunks, commit = False)
							chunks = []
				except:
					Logger.error()
					result = False

			# Write the leftovers.
			if not Pool.check(delay = delay): return None
			if chunks:
				chunks = Tools.listChunk(chunks, chunk = chunkCount)
				for i in chunks:
					try:
						self._insert(query = queryInsert1, parameters = i, commit = False)
					except:
						Logger.error()
						result = False

			if not Pool.check(delay = delay): return None
			self._commit()
			self._compact()
			return result
		except:
			Logger.error()
			return False

	def bulkSelect(self, idImdb, memory = True):
		try:
			# Do not copy, since it is not needed and only requires additional processing time.
			# Plus the lookup table might be added to the item/dict from MetaImdb.bulk() which we want to reuse.
			copy = False

			data = None
			type = MetaCache.TypeBulk
			querySelect = 'SELECT data FROM `%s` WHERE idImdb = ?;' % type

			# Check the local memory.
			if memory:
				data = self._memory(type = type, idImdb = idImdb, copy = copy)
				if data: return data

			# Retrieve from the database.
			if not data:
				data = self._selectValue(query = querySelect, parameters = [idImdb])

			# Check the external preprocessed database.
			# The external database only has some of the ratings (for titles with more votes) in order to reduce the size, since Github has a 100MB limit for files.
			external = False
			if not data and self.mExternal:
				externaled = self._external()
				if externaled:
					data = externaled._selectValue(query = querySelect, parameters = [idImdb])
					if data: external = True

			if data:
				data = Converter.jsonFrom(self._decompress(data, type = MetaCache.ExternalCompression if external else None))
				if memory and not external and not data is None: self._memoryUpdate(item = data, type = type, idImdb = idImdb, copy = copy)
				return data
		except: Logger.error()
		return None
