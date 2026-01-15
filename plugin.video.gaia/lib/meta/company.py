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

from lib.modules.tools import Media, Settings, Logger, Tools, Extension, System, Converter, File
from lib.modules.interface import Dialog, Format, Translation, Skin
from lib.modules.cache import Memory

class MetaCompany(object):

	Company20thcentury			= '20thcentury'		# 20th Century Studios
	CompanyAbc					= 'abc'				# ABC
	CompanyAe					= 'ae'				# A&E
	CompanyAcorn				= 'acorn'			# Acorn TV
	CompanyAdultswim			= 'adultswim'		# Adult Swim
	CompanyAmazon				= 'amazon'			# Amazon Studios
	CompanyAmc					= 'amc'				# AMC
	CompanyApple				= 'apple'			# Apple
	CompanyArd					= 'ard'				# ARD
	CompanyAubc					= 'aubc'			# AUBC
	CompanyBbc					= 'bbc'				# BBC
	CompanyBoomerang			= 'boomerang'		# Boomerang
	CompanyBravo				= 'bravo'			# Bravo TV
	CompanyBritbox				= 'britbox'			# BritBox
	CompanyCartoonnet			= 'cartoonnet'		# Cartoon Network
	CompanyCbc					= 'cbc'				# CBC
	CompanyCbs					= 'cbs'				# CBS
	CompanyChannel4				= 'channel4'		# Channel Four
	CompanyChannel5				= 'channel5'		# Channel Five
	CompanyCineflix				= 'cineflix'		# Cineflix
	CompanyCinemax				= 'cinemax'			# Cinemax
	CompanyColumbia				= 'columbia'		# Columbia Pictures
	CompanyComedycen			= 'comedycen'		# Comedy Central
	CompanyConstantin			= 'constantin'		# Constantin Film
	CompanyCrave				= 'crave'			# Crave
	CompanyCrunchyroll			= 'crunchyroll'		# Crunchyroll
	CompanyCw					= 'cw'				# CW
	CompanyDarkhorse			= 'darkhorse'		# Dark Horse Comics
	CompanyDccomics				= 'dccomics'		# DC Comics
	CompanyDimension			= 'dimension'		# Dimension Films
	CompanyDiscovery			= 'discovery'		# Discovery
	CompanyDisney				= 'disney'			# Walt Disney
	CompanyDreamworks			= 'dreamworks'		# DreamWorks Pictures
	CompanyFacebook				= 'facebook'		# Facebook
	CompanyFox					= 'fox'				# Fox
	CompanyFreevee				= 'freevee'			# Freevee
	CompanyFx					= 'fx'				# FX
	CompanyGaumont				= 'gaumont'			# Gaumont
	CompanyGoogle				= 'google'			# Google
	CompanyHayu					= 'hayu'			# Hayu
	CompanyHbo					= 'hbo'				# HBO
	CompanyHistory				= 'history'			# History Channel
	CompanyHulu					= 'hulu'			# Hulu
	CompanyItv					= 'itv'				# ITV
	CompanyLionsgate			= 'lionsgate'		# Lionsgate Films
	CompanyLucasfilm			= 'lucasfilm'		# Lucasfilm
	CompanyMarvel				= 'marvel'			# Marvel Studios
	CompanyMgm					= 'mgm'				# Metro-Goldwyn-Mayer
	CompanyMiramax				= 'miramax'			# Miramax
	CompanyMtv					= 'mtv'				# MTV
	CompanyNationalgeo			= 'nationalgeo'		# National Geographic
	CompanyNbc					= 'nbc'				# NBC
	CompanyNetflix				= 'netflix'			# Netflix
	CompanyNewline				= 'newline'			# New Line Cinema
	CompanyNickelodeon			= 'nickelodeon'		# Nickelodeon
	CompanyParamount			= 'paramount'		# Paramount Pictures
	CompanyPeacock				= 'peacock'			# Peacock
	CompanyPhilo				= 'philo'			# Philo
	CompanyPixar				= 'pixar'			# Pixar
	CompanyPluto				= 'pluto'			# Pluto TV
	CompanyRegency				= 'regency'			# Regency Enterprises
	CompanyRko					= 'rko'				# RKO Pictures
	CompanyRoku					= 'roku'			# Roku
	CompanyScreengems			= 'screengems'		# Screen Gems
	CompanyShowtime				= 'showtime'		# Showtime
	CompanySky					= 'sky'				# Sky
	CompanySony					= 'sony'			# Sony Pictures
	CompanyStarz				= 'starz'			# Starz
	CompanySyfy					= 'syfy'			# Syfy
	CompanyTbs					= 'tbs'				# TBS
	CompanyTnt					= 'tnt'				# TNT
	CompanyTouchstone			= 'touchstone'		# Touchstone Pictures
	CompanyTristar				= 'tristar'			# Tristar Pictures
	CompanyTrutv				= 'trutv'			# TruTV
	CompanyTubi					= 'tubi'			# Tubi
	CompanyTurner				= 'turner'			# Turner
	CompanyUniversal			= 'universal'		# Universal Pictures
	CompanyUsa					= 'usa'				# USA
	CompanyWarner				= 'warner'			# Warner Bros Pictures
	CompanyWeinstein			= 'weinstein'		# The Weinstein Company
	CompanyYoutube				= 'youtube'			# YouTube
	CompanyZdf					= 'zdf'				# ZDF

	TypeWhite					= 'white'
	TypeColor					= 'color'

	ReleaseOld					= 'old'
	ReleaseNew					= 'new'

	VersionWhite				= (0, 0, 30) # Version of the white addon considered old. All versions above this are considered new.
	VersionColor				= (0, 0, 23) # Version of the color addon considered old. All versions above this are considered new.

	ModeDisabled				= 'disabled'	# Remove the studio metadata attribute to forcefully hide the studio icon.
	ModeSingle					= 'single'		# Do not apply the white/color studio icons, but reduce the studio attribute to a single studio. For skins that display the studio as a string instead of an icon.
	ModeMultiple				= 'multiple'	# Do not apply the white/color studio icons, and keep multiple studios.
	ModeAutomatic				= 'automatic'	# Tries to detect the skin dependecies and use the white/color studio icons if available.
	ModeWhite					= 'white'		# Use the white studio icons in default mode.
	ModeColor					= 'color'		# Use the color studio icons in default mode.
	ModeForceWhite				= 'forcewhite'	# Replace the color studio icon addon textures with the white textures.
	ModeForceColor				= 'forcecolor'	# Replace the white studio icon addon textures with the color textures.

	SettingEnabled				= 'menu.icon.enabled'
	SettingCompany				= 'menu.icon.company'

	IdWhite						= Extension.IdStudioWhite
	IdColor						= Extension.IdStudioColor
	Ids							= [IdWhite, IdColor]

	Companies					= None
	Helper						= None

	##############################################################################
	# RESET
	##############################################################################

	@classmethod
	def reset(self, settings = True):
		if settings: MetaCompany.Helper = None

	###################################################################
	# COMPANY
	###################################################################

	@classmethod
	def company(self, company = None):
		# Companies are categorized as follows:
		#	1. Studios/Producers
		#		Companies producing/filming titles.
		#		IMDb: Many titles. Although there are some mistakes that some networks/distributors appear as producer, or a producer occasionally also being listed as a distributor.
		#		Trakt: Few titles. However, most of them are correct.
		#	2. Networks
		#		Streaming service or TV channels airing titles.
		#		IMDb: Many titles. Often difficult to distinguish between networks and distributors.
		#		Trakt: Few titles. However, most of them are correct.
		#	3. Vendors
		#		Companies that distribute or license-out titles. This is often not the same as a network, since distributors often do not have their own network, and distribute it over other networks.
		#		For instance, Warner Bros has many distributing companies, but no network. Instead it owns Discovery (network) which it uses as a streaming service.
		#		In the menus, vendors combine studios+networks+vendors into one group.
		#		IMDb: Many-many titles. However, it is difficult to distinguish original titles, since often there are multiple competing distributors for the same title (eg Warner Bros, Universal, Disney).
		#		Trakt: Not supported.
		#	4. Originals
		#		There is no easy way of determining originals.
		#		Simply looking at the studios is not enough, since many originals are produced by other studios (eg: only a small portion of Netflix originals are produced by Netflix Studios).
		#		Looking at the networks either does not return all originals, or more problematic, returns tons of false-positives.
		#		IMDb: Many titles. Looking only at studio or networks might return too few titles. Using the distributors returns too many false-positives. The best is to lookup all studios+networks+distributors of a company, but exclude all other major competing companies (eg: return all titles distributed by Netflix, but exclude titles that are also distributed by Amazon/Apple/Disney/etc).
		#		Trakt: We cannot combine studio+network queries. Using networks also return other titles that are not originals. Best is to use the studio, but this will return few titles.
		# Find IDs:
		#		IMDb:
		#			https://www.imdb.com/find/?s=co&q=Paramount
		#			Studios: Use companies labelled as "Production" or contains "product" in their name as studios.
		#			Networks: Use companies labelled as "Distributor" (or "Production") with specific network name as networks (eg: Paramount+).
		#			Vendors: Use companies labelled as "Distributor" or contains "distribut" in their name as vendors. Note that some do not contain any label and only have a country listed - also incluide these as vendors.
		#		Trakt:
		#			https://trakt.tv/search?studio_ids=1
		#			https://trakt.tv/search?network_ids=1
		#			Studios: No complete list available. Must manually lookup titles on IMDb, then search them on Trakt, and if they have a studio, use: https://api.trakt.tv/movies-shows/.../studios
		#			Networks: https://api.trakt.tv/networks
		#			Vendors: Use networks that are not actually networks.
		#			UPDATE: It seems that the networks endpoint is outdated or does not contain all available networks.
		#				Eg: https://trakt.tv/shows/hullabaloo-1963 has ITV1 listed as the network, but https://api.trakt.tv/networks does not return it.
		# Extract IDs from text:
		#		IMDb: cat /tmp/x.txt | grep -oP '(?<!\-)(co\d+\s*\(\d+\))' | sort -r -nt "(" -k2 | grep -oP '(co\d+)'
		#		Trakt: cat /tmp/x.txt | grep -oP '(?<!co)(?<!\d)(?<!\-)(\d+\s*\(\d+\))' | sort -r -nt "(" -k2 | grep -oP '^(\d+)'
		#
		#################################################################################################################################
		#
		# Most studios and networks belong to one of the Hollywood conglomerates (Big Five).
		# They typically own a larger trandtional TV network (ABC, NBC, CBS, etc) and one or more streaming services (Peacock, Max, Paramount+, etc)
		#
		#################################################################################################################################
		#
		# Warner Bros ("original" and "modern" Big Five)
		#
		#	Parent:		Warner Bros Discovery (Warner+Discovery), AT&T (preevious)
		#	Studios:	Warner Bros, DC Studios, Turner, New Line, Castle Rock, Spyglass, Renegade, Hanna-Barbera, Williams Street,
		#				All3Media (partial), Bad Wolf (previous, partial), MGM (previous, partial), TriStar (previous, partial)
		#	Networks:	HBO, Discovery, CNN, The WB (defunct) The CW (partial, CBS+Warner), Bravo (partial, Universal+Warner),
		#				Adult Swim, Cartoon Network, Boomerang, TLC
		#				Turner, TBS, TNT, truTV, HGTV, Animal Planet, Oprah Winfrey, Magnolia, Network Ten,
		#				BET (previous, partial), Comedy Central (previous, partial), Crunchyroll (previous), E! (previous)
		#	News:		CNN News
		#	Animations:	Adult Swim, Cartoon Network, Boomerang, TLC, Hanna-Barbera, Williams Street
		#	Streamers:	(HBO) Max, Discovery+, Philo (partial, Hearst+Disney+AMC+Paramount+Warner), Hulu (previous)
		#
		#################################################################################################################################
		#
		# Paramount ("original" and "modern" Big Five)
		#
		#	Parent:		Paramount
		#	Studios:	Paramount, United International Pictures (partial, Paramount+Universal), Miramax (partial),
		#				DreamWorks (previous), Orion (previous), TriStar (previous)
		#	Networks:	CBS, Viacom (defunct), BET, VH1, MTV, Comedy Central
		#				Nickelodeon, Noggin, Awesomeness,
		#				Showtime, SkyShowtime (partial, Comcast+Paramount), The Movie Channel (TMC),
		#				The CW (partial, CBS+Warner), TNN, Spike TV, Channel 5, Network Ten, Telefe,
		#				Telecine (partial, Paramount+Universal+MGM+Disney), True Crime (partial, AMC+Paramount),
		#				MGM+ (previous), Epix (previous), Lifetime (previous), Sundance (previous), USA Networks (previous),
		#	News:		CBS News
		#	Animations:	Nickelodeon, Noggin, Awesomeness,
		#	Streamers:	Paramount+, Pluto TV, Philo (partial, Hearst+Disney+AMC+Paramount+Warner), FuboTV (partial)
		#
		#################################################################################################################################
		#
		# Disney ("modern" Big Five)
		#
		#	Parent:		Walt Disney
		#	Studios:	Buena Vista, Pixar, Touchstone, Marvel, Lucasfilm, Star Wars, Hollywood Pictures,
		#				20th Studios/Television (previous Fox), Searchlight (previous Fox), Regency (partial)
		#	Networks:	ABC, FX (previous Fox), Fox (partial, some subsidiaries), Star, Hotstar, A&E, NatGeo, History,
		#				Asianet, Vice, Freeform, Lifetime, ESPN, Babble, Telecine (partial, Paramount+Universal+MGM+Disney)
		#	News:		ABC News
		#	Animations:	Disney, Pixar, Marvel, Lucasfilm
		#	Streamers:	Disney+, Hulu (previous Fox+Universal, now 100% Disney), Philo (partial, Hearst+Disney+AMC+Paramount+Warner)
		#
		#################################################################################################################################
		#
		# Universal ("modern" Big Five)
		#
		#	Parent:		Universal, Comcast (through NBCUniversal)
		#	Studios:	Universal Studios, Focus Features, Illumination, DreamWorks, Working Title, Carnival Films,
		#				Amblin (partial), United International Pictures (partial, Paramount+Universal)
		#	Networks:	NBC, CNBC, MSNBC, many other local US stations,
		#				E!, SyFy, USA Network, Oxygen, Telemundo, 13th Street
		#				Toonation, Bravo (partial, Universal+Warner), Telecine (partial, Paramount+Universal+MGM+Disney)
		#	News:		NBC News
		#	Animations:	Toonation, Illumination, DreamWorks
		#	Streamers:	Peacock, Hayu, Hulu (previous)
		#
		#################################################################################################################################
		#
		# Sony ("modern" Big Five)
		#
		#	Parent:		Sony
		#	Studios:	Sony Pictures, Columbia Pictures, TriStar Pictures, Screen Gems, Bad Wolf, Embassy Row, 3000 Pictures
		#	Networks:	Crunchyroll, Animax, Aniplex, AXN, Lifetime Latin America (partial Sony+A&E)
		#	News:		-
		#	Animations:	Crunchyroll, Animax
		#	Streamers:	Crunchyroll, Sony Pictures Core (previously known as Bravia Core)
		#
		#################################################################################################################################
		#
		#	Netflix:	No major ownership or collaboration. Most originals are produced in-house or licensed from other studios/networks.
		#	Apple:		No major ownership or collaboration. Most originals are produced in-house or licensed from other studios/networks.
		#	Amazon:		Now owns MGM. Most originals are produced in-house, nowadays with Amazon MGM, or licensed from other studios/networks.
		#
		#################################################################################################################################

		# Only initialize the dictionary here, instead as a class variable, since this is only used occasionally, and we do not want to initialize it simply by importing MetaTools.
		if MetaCompany.Companies is None:
			MetaCompany.Companies = {

				#################################################################################################################################
				# 20th Century
				#
				#	Parent Companies:		Disney, Fox (previous)
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			20th Century Studios
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(6720)					(2582)
				#	Networks																(0)						(0)
				#	Vendors																	(7625)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		20th Century Studios												co0781821 (94)			25519 (85)			127928
				#		20th Century Pictures												co0067247 (24)			13260 (24)			4985
				#		20th Century Studios (MX)											co1023009 (3)
				#		20th Century Productions (GB)										co0166475 (1)
				#		20th Century Hound Productions (US)									co0039396 (1)
				#		20th Century Adventures Production (US)								co0378436 (1)
				#
				#		20th Television														co0161074 (337)			95 (94)				21659
				#		20th Digital Studios												co0365818 (26)			95378 (41)			148042
				#		20th Television Animation											co0822480 (24)			103387 (21)			154887
				#		20th Century Foss													co0048444 (1)			67348 (1)			49469
				#		20th Century Vixen													co0103751 (1)			126816 (1)			177462
				#
				#		Twentieth Century Animation											co0840157 (8)
				#		Twentieth TV														co0049339 (5)
				#		Twentieth Century Vixen												co0103726 (3)			39532 (3)			95164
				#		Twentieth Century Feature Film Company								co0423469 (2)
				#		Twentieth Century Productions										co0530625 (1)
				#		Twentieth Century Productions Ltd									co0039745 (0)			39950 (5)			17990
				#
				#		20th Century Fox													co0000756 (3669)		50 (1741)			25
				#		20th Century Fox Television											co0056447 (610)			42 (403)			1556
				#		20th Century Fox Studios											co0096253 (223)
				#		20th Century Fox Brazil												co0010685 (138)			68257 (34)			89438
				#		20th Century Fox Home Entertainment															5039 (84)			3635
				#		20th Century Fox Animation											co0179259 (36)			5168 (22)			11749
				#		20th Century Fox Korea												co0077505 (1)			6254 (8)			112148
				#		20th Century Fox Consumer Products									co0645300 (1)
				#		20th Century Fox Cartoons											co1031931 (1)
				#		20th Century Fox Japan																		150785 (2)			202328
				#		Fox 2000 Pictures													co0017497 (80)			3965 (76)			711
				#		Twentieth Century-Fox Productions									co0103215 (61)
				#		Twentieth Century Fox/Icon Productions								co0098487 (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		20th Television														co0161074 (337)			1569 (0)			4069
				#		20th Century Studios												co0781821 (94)
				#
				#		20th Century Fox (BR)												co0010685 (138)
				#		20th Century Fox (IT)												co0943364 (49)
				#		20th Century Fox (DE)												co0952616 (40)
				#		20th Century Fox (GB)												co0931863 (21)
				#		20th Century Fox (KR)												co0051662 (19)
				#		20th Century Fox (ZA)												co1051152 (2)
				#
				#		20th Century Fox Argentina											co0007180 (786)
				#		20th Century Fox India												co0092296 (441)
				#		20th Century Fox Australia											co0063989 (133)
				#		20th Century Fox Korea												co0853216 (81)
				#		20th Century Fox de Venezuela										co0421648 (75)
				#		20th Century Fox España												co0368892 (9)
				#		20th Century Fox Latin America										co0092951 (9)
				#		20th Century Fox Netherlands										co0078923 (5)
				#		20th Century Fox Norway												co0148451 (5)
				#		20th Century Fox Sweden												co0380710 (3)
				#		20th Century Fox Israel												co0368801 (1)
				#		20th Century Fox Iceland											co0368843 (1)
				#		20th Century Fox de Chile											co0270675 (1)
				#		20th Century Fox Serbia (CSHH)										co0379325 (0)
				#		20th Century Fox Uruguay (UY)										co0368661 (0)
				#		20th Century Fox Sweden (NZ)										co0379362 (0)
				#		20th Century Fox East Africa (KE)									co0379346 (0)
				#		20th Century Fox Portugal (PT)										co0368861 (0)
				#		20th Century Fox New Zealand (NZ)									co0379300 (0)
				#
				#		20th Century Fox International										co0256824 (12)
				#		20th Century Fox International Classics								co0012812 (8)
				#
				#		20th Century Fox Films of Bangalore (IN)							co0547664 (0)
				#		20th Century Fox Films of Bombay (IN)								co0547663 (0)
				#
				#		20th Century Fox Home Entertainment (US)							co0010224 (2260)
				#		20th Century Fox Home Entertainment (DE)							co0280047 (783)
				#		20th Century Fox Home Entertainment (BR)							co0150813 (377)
				#		20th Century Fox Home Entertainment (GB)							co0063964 (371)
				#		20th Century Fox Home Entertainment (AU)							co0159046 (200)
				#		20th Century Fox Home Entertainment (AR)							co0296943 (177)
				#		20th Century Fox Home Entertainment (CA)							co0297163 (168)
				#		20th Century Fox Home Entertainment (MX)							co0751509 (127)
				#		20th Century Fox Home Entertainment (IT)							co0108018 (67)
				#		20th Century Fox Home Entertainment (FR)							co0226330 (49)
				#		20th Century Fox Home Entertainment (BE)							co0286182 (32)
				#		20th Century Fox Home Entertainment (ES)							co0794652 (22)
				#		20th Century Fox Home Entertainment (HK)							co0544968 (21)
				#		20th Century Fox Home Entertainment (JP)							co0788854 (20)
				#		20th Century Fox Home Entertainment (SE)							co0273176 (8)
				#		20th Century Fox Home Entertainment (TR)							co0665472 (4)
				#		20th Century Fox Home Entertainment (NL)							co0918688 (2)
				#		20th Century Fox Home Entertainment (VE)							co0421647 (1)
				#		20th Century Fox Home Entertainment (HU)							co0613528 (1)
				#		20th Century Fox Home Entertainment (DK)							co0918844 (1)
				#		20th Century Fox Home Entertainment (KR)							co0883912 (1)
				#		20th Century Fox Home Entertainment (NO)							co0918845 (1)
				#		20th Century Fox Home Entertainment (CN)							co0200961 (1)
				#		20th Century Fox Home Entertainment (GR)							co0094759 (0)
				#
				#		20th Century Fox Video (US)											co0605838 (113)
				#		20th Century Fox Video (GB)											co0581069 (10)
				#		20th Century Fox Video (JP)											co0662791 (2)
				#		20th Century Fox Video (AU)											co0662795 (2)
				#		20th Century Fox Video												co0030446 (0)
				#
				#		20th Century Fox CIS (RU)											co0209782 (190)
				#		20th Century Fox Television Distribution							co0197226 (15)
				#		20th Century Fox Hellas (GR)										co0764128 (15)
				#		20th Century Fox Digital Unit										co0046053 (2)
				#		20th Century Fox Library Services (US)								co0173400 (1)
				#		20th Century Fox Television International (US)						co0451003 (0)
				#		20th Century Fox Still Collection (US)								co0195082 (0)
				#
				#		Twentieth Century Fox (US)											co0000756 (3669)
				#		Twentieth Century-Fox (MX)											co0862964 (678)
				#		Twentieth Century Fox (FR)											co0937473 (127)
				#		Twentieth Century Fox (MX)											co0826899 (122)
				#		Twentieth Century Fox (BE)											co0937474 (56)
				#		Twentieth Century Fox (CA)											co0711817 (27)
				#		Twentieth Century-Fox (BR)											co0866807 (7)
				#		Twentieth Century-Fox (AR)											co0863455 (6)
				#		Twentieth Century-Fox (CA)											co0866288 (4)
				#		Twentieth Century-Fox (CU)											co0862965 (3)
				#		Twentieth Century-Fox (PR)											co0863456 (2)
				#		Twentieth Century Fox (NO)											co0271701 (1)
				#		Twentieth Century Fox (SD)											co0924784 (0)
				#
				#		Twentieth Century Fox Home Entertainment (NL)						co0189783 (785)
				#		Twentieth Century Fox Home Entertainment (FI)						co0643891 (51)
				#		Twentieth Century Fox Home Entertainment (US)						co0785884 (13)
				#		Twentieth Century Fox Home Entertainment (NO)						co0623011 (6)
				#		Twentieth Century Fox Home Entertainment (RU)						co0746852 (5)
				#		Twentieth Century Fox Home Entertainment (DK)						co0643890 (4)
				#		Twentieth Century Fox Home Entertainment (SE)						co0662285 (2)
				#		Twentieth Century Fox Home Entertainment (DE)						co1034313 (1)
				#		Twentieth Century Fox Home Entertainment (ZA)						co0855510 (1)
				#
				#		Twentieth Century Fox Film Company (GB)								co0053239 (1359)
				#		Twentieth Century Fox Film Company (BE)								co0491690 (10)
				#		Twentieth Century Fox Film Company (FI)								co0491691 (3)
				#		Twentieth Century Fox Film Company (DE)								co0947212 (3)
				#		Twentieth Century Fox Film Company (CA)								co0707661 (3)
				#		Twentieth Century-Fox Film Company (GB)								co0832095 (7)
				#		Twentieth Century-Fox Film Company (CA)								co0867515 (3)
				#		Twentieth Century-Fox Film Company (MX)								co0867516 (2)
				#		Twentieth Century-Fox Film Company (BR)								co0867517 (1)
				#		Twentieth Century-Fox Film Company (PR)								co0867518 (1)
				#		Twentieth Century-Fox Film Company (CU)								co0867519 (1)
				#		Twentieth Century-Fox Film Company (AR)								co0870304 (1)
				#		Twentieth Century Fox Film Company (AU)								co0611815 (0)
				#
				#		Twentieth Century Fox Film (AT)										co0241365 (9)
				#		Twentieth Century-Fox Film (NL)										co0814039 (2)
				#
				#		Twentieth Century Fox Central Files (US)							co0080169 (1)
				#		Twentieth Century Fox Promotional Programming (US)					co0160971 (1)
				#		Twentieth Century Fox Photo Archives (US)							co1027357 (1)
				#		Twentieth Century Fox Film (US)										co1040440 (1)
				#		Twentieth Century Fox Collection, UCLA Arts Special Collections		co0196456 (0)
				#		Twentieth Century Fox Travel (US)									co0197792 (0)
				#		Twentieth Century Fox/Davis Entertainment							co0099617 (0)
				#		Twentieth Century Fox Feature Publicity								co0118485 (0)
				#
				#		20th Century Draperies (US)											co0295671 (3)
				#		20th Century Film Archives (US)										co0941233 (1)
				#		20th Century Theatre (GB)											co0246174 (1)
				#		20th Century Revisited History Group (GB)							co0723134 (1)
				#		20th Century Studios Home Entertainmen Brazil (BR)					co0877266 (0)
				#		20th Century Frocks (US)											co0212696 (0)
				#		20th Century Spatchcock (GB)										co0419314 (0)
				#		20th Century Studios España (ES)									co0893064 (0)
				#
				#		Twentieth Century Fund (US)											co0560127 (1)
				#		Twentieth Century Studios Home Entertainment (US)					co0782188 (0)
				#
				#		Twentieth Century Fox Music (US)									co0195278 (4)
				#		20th Century Fox Records (US)										co0346045 (3)
				#		20th Century Records (US)											co0642443 (2)
				#		20th Century Fox Music Corporation (US)								co0694711 (1)
				#
				#################################################################################################################################
				MetaCompany.Company20thcentury : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : '20th Century Studios'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : '20th Century'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '((?:20th|twentieth)[\s\-\_\.\+]*(?:century|fox|tv|television|digital)|fox[\s\-\_\.\+]*2000)',
				},

				#################################################################################################################################
				# ABC
				#
				#	There are multiple companies with the same name:
				#		1. American Broadcasting Company (ABC) - US
				#		2. Australian Broadcasting Corporation (ABC) - AU
				#		3. Associated British Cinemas (ABC) - UK
				#		4. Asahi Broadcasting Corporation (ABC) - JP
				#		5. ABC Films - IN
				#
				#	Parent Companies:		Disney, Paramount (previous)
				#	Sibling Companies:		Freeform, Disney, FX, NatGeo, ESPN
				#	Child Companies:		-
				#
				#	Owned Studios:			ABC Studios
				#	Owned Networks:			ABC, Freeform
				#
				#	Streaming Services:		Disney+, ESPN+, Hulu
				#	Collaborating Partners:	Netflix, Marvel
				#
				#	Content Provider:		-
				#	Content Receiver:		Disney+, ESPN+, Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1500)					(926)
				#	Networks																(7589)					(1664)
				#	Vendors																	(308)					(1)
				#	Originals																(2249 / 2108)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		American Broadcasting Company (ABC)															125476 (297)		176162
				#		ABC Signature (US)													co0209226 (290)			1178 (74)			76871
				#
				#		ABC Studios (US)													co0852654 (19)			29 (225)			19366
				#		ABC Studios International (US)										co0752381 (1)			1154 (1)			121713
				#
				#		ABC Pictures (US)													co0056365 (15)			3500 (22)			634
				#		ABC Pictures International (US)										co0009307 (4)			38090 (1)			68340
				#		ABC Pictures Corporation (US)										co0636045 (1)
				#
				#		ABC Television Network (US)											co0314763 (40)
				#		ABC Television Studios (US)											co0348603 (5)
				#		ABC Television Studio (US)											co0202583 (2)			30451 (7)			44081
				#		ABC Owned Television Stations (US)									co0825786 (2)
				#
				#		ABC Digital Studio (US)												co0377134 (5)
				#		ABC Digital Media Studio (US)										co0383943 (4)
				#
				#		ABC News (US)														co0074648 (139)			3328 (130)			25992
				#		ABC News Studios (US)												co0899934 (23)			128742 (77)			179418
				#		ABC News Productions (US)											co0129642 (3)
				#		ABC News Closeup (US)												co0152669 (2)			162298 (1)			61945
				#		ABC NEWS NOW (US)													co0508214 (2)
				#		ABC News Production Company (US)									co0257987 (1)
				#		ABC News and Public Affairs											co0055400 (1)
				#		ABC News Originals (US)												co0847123 (1)
				#		ABC News Primetime Live (US)										co0299815 (1)
				#		ABC News Investigative Unit (US)									co0875134 (0)
				#
				#		American Broadcasting Company (ABC) Sports (US)						co0061107 (10)
				#		NBA on ABC (US)														co0385264 (2)
				#		ABC/American Sportsman Film (US)									co0184398 (1)
				#		ABC World Wide Sports (US)											co0049424 (1)
				#
				#		ABC Radio (US)														co0875139 (1)
				#		ABC Audio (US)														co0868474 (1)
				#
				#		ABC Productions (US)												co0033326 (26)			361 (36)			3668
				#		ABC Video Enterprises												co0048955 (21)			53385 (13)			8968
				#		ABC Entertainment (US)												co0021273 (20)			496 (19)			18742
				#		ABC Circle Films (US)												co0033054 (7)			457 (86)			2166
				#		ABC Motion Pictures (US)											co0641809 (7)
				#		ABC Motion Pictures													co0044833 (2)			67160 (7)			13671
				#		ABC Media Group (US)												co0432287 (2)			973 (1)				65725
				#		ABC Public Affairs													co0043308 (2)
				#		ABC Documentaries (US)												co0794140 (1)			177437 (1)			227965
				#		ABC Entertainment Productions (US)									co0387413 (1)
				#		ABC Education's Lifelong Learning (US)								co0092661 (1)
				#		ABC World of Discovery (US)											co0339897 (1)
				#		ABC EM (US)															co0646998 (1)
				#		ABC Localish Studios (US)											co0869949 (1)
				#		ABC Projects (US)													co0728048 (1)
				#		Nightline on ABC (US)												co0171572 (1)
				#		ABC Media Productions (US)											co0296206 (0)
				#		ABC Video Productions Inc. (US)										co0048784 (0)
				#		ABC, Vin Di Bona Productions (US)									co0924094 (0)
				#
				#		ABC 7 Chicago (US)													co0671036 (2)
				#		ABC New York Film & Television Productions (US)						co0088355 (1)
				#		ABC Puerto Rico (PR)												co0742232 (1)
				#
				#		WABC-TV																						94804 (2)			104442
				#
				#		ABC/Kane Productions (US)											co0181606 (5)
				#		Capital Cities/ABC Video Enterprises Inc. (US)						co0112209 (3)			36654 (21)			28085
				#		Hearst / ABC Arts (US)												co0401142 (1)
				#
				#		Freeform Studios (US)												co0755246 (5)			5647 (16)			68467
				#
				#	Other production companies.
				#
				#		ABC Sports (US)														--co0010108-- (37)
				#		ABC Records (US)													--co0478652-- (4)
				#		ABC Cable & International Broadcast Inc. (US)						--co0033016-- (3)
				#		ABC Productions (CA)												--co0555144-- (1)
				#		ABC News Nightline (US)												--co0875165-- (1)
				#		ABC Enterprises (US)												--co0072144-- (1)
				#		ABC4Explore (US)													--co0401580-- (1)
				#		ABC4Films (US)														--co0874426-- (1)
				#
				#	Other companies with the same name.
				#
				#		ABC Weekend Television (GB)											--co0103273-- (68)		--75191-- (47)		132792
				#		ABC Television (GB)	(people added ABS-US stuff here)				--co0104278-- (32)
				#		ABC Hydra Photography (US)											--co0834124-- (1)
				#		ABC Productions (HK)												--co0197516-- (1)
				#		ABC Film A/S (NO)													--co0027937-- (5)
				#		ABC Production (GB)													--co0480133-- (0)
				#		ABC Film (UA)														--co0557954-- (2)
				#		ABCD Productions													--co0034536-- (1)
				#		ABCB Productions (US)												--co0347522-- (1)
				#		ABCG Productions (US)												--co0823648-- (1)
				#		ABCQ Productions (US)												--co0511565-- (1)
				#		ABC Productions (BR)												--co0644306-- (1)
				#		ABC Pro Wrestling (TH)												--co0801968-- (1)
				#		Tempo ABC TV (US)													--co0541590-- (1)
				#		ABC No Rio (US)														--co0740193-- (1)
				#		ABC Cinematográfica (ES)											--co0076004-- (6)
				#		ABC Production (HK)													--co0974866-- (1)
				#		Les Films ABC (FR)													--co0013491-- (14)
				#		ABC-Filmgesellschaft (DE)											--co0186917-- (1)
				#		ABC (BR)															--co0893024-- (1)
				#		ABC Film (IT)														--co0271162-- (1)
				#		ABC Conceptions (DE)												--co0453737-- (1)
				#		ABC productions (GR)												--co0632629-- (2)
				#		A.B.C. (DE)															--co0042411-- (1)
				#		ABC Cinema (BE)														--co0749344-- (1)
				#		ABC (Italy) (IT)													--co0117641-- (1)
				#		ABC Cursos de Cinema (BR)											--co0846900-- (1)
				#		ABC Talk Productions (FR)											--co0828661-- (0)
				#		ABC Film (TR)														--co0666979-- (1)
				#		ABCi Media (GB)														--co0655735-- (1)
				#		ABC Produits SA (CH)												--co0753322-- (1)
				#		ABC Production (GR)													--co0497574-- (3)
				#		ABC de Floirac (FR)													--co0995548-- (1)
				#		A.B.C. Pictures														--co0074766-- (1)
				#		A.B.C.-Film (DE)													--co0146261-- (9)
				#		ABC Weekend Network Production (GB)									--co0613932-- (1)
				#		ABCFilm (DK)														--co0348574-- (1)
				#		Sdruzhenie ABC														--co0011279-- (1)
				#		ABCya (US)															--co0400622-- (0)
				#		ABC TV London (GB)													--co0104749-- (1)
				#		ABC-Studio GmbH (DE)												--co0112001-- (3)
				#		Studio ABC															--co0069455-- (2)
				#		ABC (ES)															--co0933439-- (1)
				#		ABC Pictures (VN)													--co0781254-- (1)
				#		ABC Cineproducciones S.A. (MX)										--co0023057-- (3)
				#		A.B.C. Productions													--co0002013-- (2)
				#		ABC-CBN Channel 3 TV Series (PH)									--co0679264-- (1)
				#
				#		Freeform Productions (CA)											--co0099652-- (0)
				#		Freeform Spain (ES)													--co0198945-- (3)		--24045-- (2)		23191
				#		Freeform Productions (GB)											--co0104480-- (12)
				#		Free Form Productions (CA)											--co0193573-- (2)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		ABC (US)															co0037052 (1535)		16 (1513)			2
				#		ABC																							2931 (1)			6778
				#
				#		ABC Family (US)														co0050794 (276)			9 (94)				75
				#		ABC Family Worldwide (US)											co0113687 (7)
				#		ABC Childrens Television (US)										co0051484 (2)
				#
				#		ABC Films (US)														co0038002 (31)
				#		ABC Television Films Limited										co0071029 (1)
				#		ABC Film Syndication Inc. (US)										co0160591 (0)
				#
				#		ABC Productions (US)												co0033326 (26)
				#		ABC Video Enterprises (US)											co0048955 (21)
				#		ABC Television (ABC) (GB)											co0547748 (21)
				#		ABC Network (US)													co0072128 (15)
				#		ABC Spark (CA)														co0366131 (9)			986 (2)				1345
				#		ABC-TV (US)															co0717722 (8)
				#		ABC.com																						1754 (2)			3322
				#		ABCd (US)															co0815633 (1)			1561 (12)			2791
				#		ABC Daytime (US)													co0095158 (1)
				#		ABC Theater for Young Americans (US)								co0093288 (1)
				#		ABC Media Concepts (US)												co0885117 (1)
				#		ABC Studios On Demand (NL)											co0604632 (1)
				#
				#		Freeform (US)														co0571670 (223)			425 (49)			1267
				#
				#	Other companies with the same name.
				#
				#		ABCmouse Early Learning Academy (US)								--co0626111-- (9)
				#		ABC / Cinemien Filmdistributie (NL)									--co0365667-- (9)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		ABC Television Center (US)											co0016203 (29)
				#		ABC Distribution Co. (US)											co0081188 (10)
				#		ABC Home Video (US)													co0043953 (8)
				#		ABC Video Entertainment (US)										co0269174 (1)
				#		ABC Television Center in New York (US)								co0274340 (1)
				#		ABC Video Publishing Inc. (US)										co0009893 (1)
				#		ABC Entertainment Group (US)										co0287995 (1)
				#		ABC Entertainment Marketing (US)									co0499524 (1)
				#		ABC Distribution Company (US)										co0430836 (1)
				#		ABC Internatonal (US)												co0272294 (1)
				#		ABC Media Films (US)												co0224390 (0)
				#		ABC Music (US)														co0695216 (0)
				#		ABC Primetime Archives (US)											co0813557 (0)
				#		ABC Television Center Hollywood (US)								co0233792 (0)
				#
				#		ABC News 20/20 (US)													co0078518 (5)
				#		ABC News World News Tonight (US)									co0138770 (3)
				#		The ABC Evening News (US)											co0297296 (1)
				#		ABC NewsLive (US)													co0860670 (1)
				#		ABC News Digital (US)												co0625846 (1)
				#		ABC News/Washington Post (US)										co1024565 (0)
				#
				#		ABC 4 Utah (US)														co0503538 (2)
				#		ABC 7 Los Angeles (US)												co0776976 (2)
				#		ABC 30 (US)															co0712561 (1)
				#		ABC 15 (US)															co0704979 (1)
				#		ABC24 Memphis (US)													co0976554 (1)
				#		ABC 7 New York (US)													co0923262 (1)
				#		ABC 5 Plus (US)														co0598951 (1)
				#		ABC 10 San Diego (US)												co0465399 (1)
				#		ABC 24 (US)															co0391449 (1)
				#		ABC 7 Broadcast Center, Hollywood (US)								co0075098 (0)
				#
				#		WABC (US)															co0024582 (26)
				#		WABC-TV Channel 7 (US)												co0427720 (11)
				#		77 WABC (US)														co0980699 (0)
				#		WABC-TV (US)																				808 (0)				241
				#
				#		KABC Los Angeles (US)												co0090366 (11)
				#		KABC-TV (US)														co0504198 (7)
				#		KABC-TV Channel 7, Los Angeles, California (US)						co0716481 (1)
				#		KABC-TV News (US)													co0431081 (1)
				#		KABC Radio (US)														co1027259 (1)
				#
				#		KESQ-TV (ABC) (US)													co0795985 (4)
				#		KSPR-TV, ABC Channel 33 (US)										co0723944 (2)
				#		(KEYT-TV) ABC (US)													co0795983 (1)
				#		KCRG-TV (ABC) (US)													co0493121 (1)
				#		ABC-WTEN (US)														co0747268 (1)
				#		KFSN-TV (ABC30) (US)												co0825785 (1)
				#		WTVD-TV (ABC11) (US)												co0825784 (1)
				#		WPLG-TV Miami-FTL (ABC) (US)										co0992781 (1)
				#		WFTV-ABC (US)														co0266935 (1)
				#		WXYZ (ABC - Detroit)																		2260 (1)			5577
				#		WBUP-ABC 10, Ishpeming, MI (US)										co1008959 (0)
				#		WTFS-TV/ABC 28 (US)													co0928550 (0)
				#
				#		Disney-ABC Domestic Television (US)									co0213225 (382)
				#		Disney-ABC International Television (US)							co0212150 (27)
				#		Disney-ABC Television Group (US)									co0094898 (14)
				#		Disney-ABC Home Entertainment & Television Distribution (US)		co0739072 (8)
				#		Disney-ABC (US)														co0913419 (1)
				#		Disney-ABC Cable Networks Group (US)								co0094890 (1)
				#
				#		Capital Cities/ABC (US)												co0053123 (6)
				#		ABC Capital Cities Television Network (US)							co0086850 (3)
				#		Capital Cities/ABC Video Publishing (US)							co0793020 (1)
				#
				#		ABC Studios/Sony Pictures Television (US)							co0859939 (0)
				#		Sony Pictures Television/ABC (US)									co0868243 (0)
				#		ABC / Sony Pictures Television (US)									co0842694 (0)
				#
				#		Hearst / ABC ARTS (US)												co0399064 (7)
				#		ABC-Paramount (US)													co0327798 (1)
				#		ABC / Werner Entertainment (US)										co0852116 (0)
				#
				#		Freeform Media Group (US)											co0303200 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyAbc : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'ABC Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'ABC'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'ABC'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'ABC Originals'},
					'expression'	: '([kw]?abc[d\d]?|american[\s\-\_\.\+]*broadcast(?:ing)?[\s\-\_\.\+]*(?:company|corporation)|freeform)',
				},

				#################################################################################################################################
				# A&E
				#
				#	Arts & Entertainment Network (A&E or A+E or AEN)
				#
				#	Parent Companies:		Hearst (partial), Disney (partial), NBCUniversal (previous)
				#	Sibling Companies:		ABC, Disney, FX, ESPN, Lifetime, History, NatGeo
				#	Child Companies:		-
				#
				#	Owned Studios:			Reel One (partial, minority)
				#	Owned Networks:			A&E, History Channel, Lifetime, FYI,
				#							Defy (partial), Vice (partial, minority), Philo (partial, Hearst+Disney+AMC+Paramount+Warner)
				#
				#	Streaming Services:		Philo
				#	Collaborating Partners:	Disney, History, Lifetime, BBC, Netflix
				#
				#	Content Provider:		Philo, A&E, Netflix
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(168)					(266)
				#	Networks																(1158)					(290)
				#	Vendors																	(173)					(0)
				#	Originals																(476 / 582)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		A+E Studios (US)													co0467028 (45)			1072 (122)			18441
				#		A&E Television Networks (US)																7913 (110)			106324
				#		A&E IndieFilms (US)													co0152564 (22)			20259 (15)			7315
				#		A&E Studios (US)													co0883720 (18)
				#		A&E Home Entertainment																		38080 (14)			8376
				#		A&E Originals (US)													co0741969 (9)			129828 (1)			174062
				#		A+E Factual Productions (US)										co1024705 (7)
				#		A&E Music Services (US)												co0933418 (2)
				#		A+E Media Group (GB)												co1047517 (2)
				#		A+E Factual Studios																			182433 (2)			232549
				#		A&E Productions (GB)												co0703903 (1)
				#		A&E Pictures (GB)													co0368082 (1)
				#		A&E Films (JP)														co0347017 (1)
				#		A+E Creative Partners (JP)											co0843022 (1)
				#		A+E Broadband (US)													co0587318 (1)
				#
				#		Arts & Entertainment Network (AEN) (US)								co0779123 (1)			100570 (5)			152363
				#		Arts and Entertainment Network (US)									co0624428 (4)
				#		Arts & Entetainment Network (AEN) (US)								co0778575 (1)
				#		Arts & Entertainmnet Network (AEN) (US)								co0778574 (0)
				#
				#		Lifetime/A+E Studios (US)											co0600239 (1)
				#		Mills Productions for A&E (US)										co0995059 (1)
				#
				#	Other production companies.
				#
				#		TFI/A&E IndieFilms StoryLab (US)									--co0814033-- (1)
				#		A&E Adventures (GB)													--co0673784-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		A&E (US)																					44 (267)			129
				#		A&E																							2547 (5)			5202
				#		A&E (BR)																					2226 (4)			2639
				#		A&E (AU)																					2742 (3)			3688
				#		A&E (DE)															co0979954 (3)			3624 (1)			7401
				#		A&E																							3216 (0)			7093
				#
				#		A+E Networks (US)													co0056790 (481)
				#		A&E Network (US)													co0976488 (31)
				#		A&E Networks UK (GB)												co0736175 (14)
				#		A+E Networks Germany (DE)											co0452284 (11)
				#		A+E Networks Japan (JP)												co0723513 (8)
				#		A+E Networks Korea (KR)												co0930307 (6)
				#		A+E Networks Asia (SG)												co0441521 (3)
				#		A+E Networks (GR)													co1048176 (1)
				#		A +E Networks (IT)													co0889192 (1)
				#		A+E Networks (GB)																			2495 (2)			5539
				#
				#		A&E Television Networks Latin America (US)							co0450920 (4)
				#		A+E Television Networks International (US)							co0783041 (3)
				#		A&E Television Networks (US)										co1002360 (1)
				#		A&E Television Networks (IT)										co1021426 (1)
				#
				#		Planète+ A&E (FR)																			1752 (9)			3050
				#		A&E Casting (US)													co0580178 (1)
				#
				#		Arts and Entertainment Network (US)									co0624428 (4)
				#		Arts Entertainment Network (GB)										co0159554 (2)
				#		Arts & Entetainment Network (AEN) (US)								co0778575 (1)
				#		Arts & Entertainment Network (AEN) (US)								co0779123 (1)
				#		Arts & Entertainmnet Network (AEN) (US)								co0778574 (0)
				#
				#	Other companies with the same name.
				#
				#		Dongwoo A&E (KR)													--co0736572-- (6)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		A&E Home Video (US)													co0023845 (69)
				#		A&E Library (US)													co0331411 (4)
				#		A&E Networks Home Entertainment (US)								co0674785 (3)
				#		A&E Archives (US)													co0625685 (1)
				#		A+E Unlimited (US)													co1057623 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyAe : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'A&E Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'A&E'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'A&E'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'A&E Originals'},
					'expression'	: '(a\s*(?:[\+\&]|and)\s*e|^aen$|arts?\s*(?:[\+\&]|and)?\s*enter?tainmn?en?t\s*network)',
				},

				#################################################################################################################################
				# Acorn TV
				#
				#	Parent Companies:		AMC, RLJ Entertainment
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	AMC, ITV, BBC, Sky
				#
				#	Content Provider:		AMC+, Shudder
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(14)					(19)
				#	Networks																(213)					(18)
				#	Vendors																	(8)						(0)
				#	Originals																(27 / 176)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Acorn Media Enterprises (US)										co0595504 (8)			2341 (14)			84098
				#		Acorn TV (US)																				161589 (4)			212651
				#		Athena Learning / Documentaries (Acorn Media Group) (US)			co0524201 (1)			136323 (1)			154684
				#
				#	Other companies with the same name.
				#
				#		Bridge and Acorn Entertainment (US)									--co0790829-- (12)
				#		Acorn Communications (US)											--co0723266-- (1)
				#		Acorn Village Productions (US)										--co0573752-- (1)
				#		Acorn Explosion (GB)												--co0849113-- (1)
				#		Acorn Studio (CN)													--co0696840-- (1)
				#		Acorn Pictures														--co0042781-- (2)
				#		Littlest Acorn Productions (CA)										--co0256392-- (1)
				#		Acorn Studio (ES)													--co0696836-- (2)
				#		Little Acorn (US)													--co0339865-- (1)
				#		Small Acorn Productions (GB)										--co0125575-- (1)
				#		Acorn (GB)															--co0375828-- (1)
				#		Little Acorn Films													--co0012009-- (1)
				#		Acorn Video Bfd (GB)												--co0944650-- (1)
				#		Acorn Productions (US)												--co0037915-- (3)
				#		Acorn Films															--co0074960-- (0)
				#		Acorn Features (US)													--co0204362-- (1)
				#		Ambling Acorn Productions (CA)										--co0062029-- (1)
				#		Acorn Arts and Entertainment (US)									--co0794207-- (1)
				#		Acorn2oak Productions (US)											--co0381321-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Acorn TV (US)														co0463759 (47)			557 (18)			2697
				#		Acorn tv																					2288 (0)			5630
				#		Acorn tv UK																					2316 (0)			5693
				#
				#		Acorn Media Group (US)												co0178134 (33)
				#		Acorn Media (GB)													co0174662 (31)
				#		AcornMedia (US)														co0098270 (8)
				#		Acorn Media (AU)													co0277845 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Acorn DVD (GB)														co0489114 (4)
				#
				#		Acorn																co0066950 (1)
				#
				#		RLJ Entertainment/Acorn (US)										co0502394 (2)
				#
				#	Not sure if these are the same company.
				#
				#		Acorn Film and TV (GB)												--co0572039-- (1)
				#		Acorn Film and Television (GB)										--co0947956-- (1)
				#		Acorn Direct (US)													--co0219287-- (0)
				#		Acorn Films (US)													--co0894424-- (0)
				#
				#	Other companies with the same name.
				#
				#		Acorn Press Canada (CA)												--co0571746-- (1)
				#		Acorn Theater (US)													--co0353514-- (1)
				#		Acorn Video (Bradford) (GB)											--co1004903-- (1)
				#		Acorn Video (US)													--co0785075-- (2)
				#		Acorn Video															--co0033292-- (3)
				#
				#################################################################################################################################
				MetaCompany.CompanyAcorn : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Acorn Enterprises'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Acorn TV'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Acorn'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Acorn Originals'},
					'expression'	: '(acorn[\s\-\_\.\+]*(?:$|tv|media|dvd))',
				},

				#################################################################################################################################
				# Adult Swim
				#
				#	Williams Street is the in-house studio for Adult Swim, although they also produce content for other networks.
				#
				#	Parent Companies:		Warner Bros Discovery (through Cartoon Network)
				#	Sibling Companies:		Cartoon Network, Boomerang, HBO, The CW, Cinemax, Discovery, TBS, TNT, TCM, TLC, TruTV, many more
				#	Child Companies:		-
				#
				#	Owned Studios:			Williams Street
				#	Owned Networks:			Adult Swim
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Cartoon Network
				#
				#	Content Provider:		Cartoon Network
				#	Content Receiver:		Cartoon Network, HBO, The CW
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(160)					(225)
				#	Networks																(500)					(136)
				#	Vendors																	(0)						(0)
				#	Originals																(28 / 216)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Adult Swim																					12260 (116)			6759
				#		Adult Swim Movies (US)												co1040171 (0)
				#
				#		Williams Street (US)												co0008281 (90)			259 (173)			6760
				#		Williams Street West (US)											co0777394 (1)			89195 (2)			142738
				#		Williams Street Movies (US)											co1040172 (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Adult Swim (US)														co0153115 (295)			104 (131)			80
				#		Adult Swim (CA)														co1019499 (16)			3020 (1)			6929
				#		Adult Swim (GB)														co0583876 (3)
				#		Adult Swim (FR)																				2334 (2)			5629
				#
				#		Adult Swim Latin America (AR)										co1003525 (2)
				#		AdultSwim.com (US)																			3571 (2)			7377
				#		Adult Swim Games (US)												co0600922 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Williams Street Records (US)										co0546259 (0)
				#		Williams Street Games (US)											co0635386 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyAdultswim : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Adult Swim Productions'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Adult Swim'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Adult Swim'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Adult Swim Originals'},
					'expression'	: '(adult[\s\-\_\.\+]*swim|william\'?s[\s\-\_\.\+]*street)',
				},

				#################################################################################################################################
				# Amazon
				#
				#	Amazon Studios acquired MGM, and with that, also Epix, ScreenPix, Orion, and United Artists.
				#
				#	Parent Companies:		Amazon
				#	Sibling Companies:		-
				#	Child Companies:		MGM
				#
				#	Owned Studios:			MGM, Orion, United Artists, American International Pictures
				#	Owned Networks:			MGM+, Epix, ScreenPix, Impact, Telecine (partial, Paramount+Universal+MGM+Disney)
				#
				#	Streaming Services:		Amazon Prime, MGM+
				#	Collaborating Partners:	MGM
				#
				#	Content Provider:		-
				#	Content Receiver:		Amazon Prime, MGM+, Hulu (almost none)
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1050)					(476)
				#	Networks																(6458)					(1081)
				#	Vendors																	(528)					(0)
				#	Originals																(1492 / 1221)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Amazon Studios														co0319272 (757)			179 (347)			20580
				#		Amazon MGM Studios													co1025982 (99)			158509 (133)		210099
				#		Amazon Kids+														co0888198 (7)
				#		Amazon Game Studios													co0477966 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Amazon (US)															co0515031 (267)			47 (1032)			1024
				#		Amazon (JP)															co0260409 (14)
				#		Amazon (CA)															co0904701 (2)
				#		Amazon (NZ)															co0904703 (1)
				#		Amazon (AU)															co0904702 (1)
				#
				#		Amazon Prime Video (US)												co0476953 (3495)		2385 (0)			5848
				#		Amazon Prime Video (IN)												co0939864 (460)
				#		Amazon Prime Video (GB)												co0931938 (50)
				#		Amazon Prime Video (PH)												co0963571 (5)
				#		Amazon Prime Video (PT)												co0981326 (3)
				#		Amazon Prime Video																			2385 (0)			5848
				#
				#		Prime Video (ES)													co0946652 (15)
				#		Prime Video (AU)													co0994447 (4)
				#		Prime Video (CA)													co1003340 (3)
				#		Prime Video (NZ)													co0994448 (3)
				#		Prime Video (IT)													co1028072 (1)
				#		Prime Video (ID)													co0999701 (1)
				#		Prime Video (AT)													co1000687 (1)
				#
				#		Amazon Freevee (US)													co0796766 (213)
				#		Amazon Freevee (DE)																			3205 (4)			6550
				#		Amazon Freevee (GB)																			3596 (1)			7385
				#		Freevee (US)																				2392 (26)			5865
				#
				#		Amazon miniTV (IN)													co0869098 (50)			2214 (0)			5468
				#		Amazon miniTV																				2501 (44)			5920
				#
				#		Amazon Music (US)													co0664543 (13)
				#		Amazon Music UK (GB)												co1025228 (1)
				#
				#		Amazon Instant Video (US)											co0337718 (848)
				#		Amazon Video Direct (US)											co0665882 (29)
				#		Amazon Seller Services Private Limited (IN)							co0609198 (13)
				#		Amazon Kids+														co0888198 (7)			2256 (5)			5533
				#		Amazon Direct (US)													co0616693 (7)
				#		Amazon Digital Services (US)										co0348775 (6)
				#		Amazon Instant Streaming (US)										co0409640 (6)
				#		Amazon Strike (US) (Amazon's Anime platform)						co0630540 (3)
				#		Amazon Media EU (GB)												co0653187 (1)
				#		Prime Video Terms (US)												co1011011 (1)
				#		Prime Video Productions (US)										co0115743 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Amazon.com (US)														co0042083 (322)
				#		Amazon.co.uk (GB)													co0250772 (8)
				#		Amazon.de (DE)														co0249265 (8)
				#		Amazon.co.jp (JP)													co0491850 (3)
				#		Amazon.fr (FR)														co0389614 (1)
				#		Amazon.it (IT)														co0785664 (0)
				#
				#		Amazon Web Services (US)											co0850778 (4)
				#		Prime Video X-Ray (US)												co0968084 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyAmazon : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Amazon Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Amazon Prime'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Amazon'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Amazon Originals'},
					'expression'	: '(amazon|prime[\s\-\_\.\+]*video)',
				},

				#################################################################################################################################
				# AMC
				#
				#	https://en.wikipedia.org/wiki/AMC_Networks#Television_channels
				#	https://ideas.fandom.com/wiki/AMC_Family
				#
				#	Parent Companies:		AMC, Disney-ABC (previous, probably?)
				#	Sibling Companies:		-
				#	Child Companies:		IFC Films RLJE Films, Sentai Filmworks
				#
				#	Owned Studios:			IFC Films, RLJ Entertainment, Shaftesbury Films (partial, minority)
				#	Owned Networks:			AMC, Shudder, IFC, Allblk, Acorn TV, Sundance TV/Now, We TV, Sentai/Hidive, Chellomedia,
				#							BBC America (partial, BBC+AMC), Philo (partial, Hearst+Disney+AMC+Paramount+Warner), BritBox (partial, minority)
				#							Bravo (previous), Funny or Die (previous)
				#
				#	Streaming Services:		AMC+, Shudder
				#	Collaborating Partners:	BBC America, BBC (Earth, Food, Home, Kids), BritBox, Philo
				#							Movie library agreements (Disney, Dreamworks, Pixar, Touchstone, Lucasfilm, Marvel,
				#							MGM, Universal, Warner, 20th Century, Searchlight, Sony, Columbia, TriStar, Screen Gems)
				#
				#	Content Provider:		BBC America
				#	Content Receiver:		BBC America
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(456)					(198)
				#	Networks																(2735)					(317)
				#	Vendors																	(494)					(0)
				#	Originals																(11 / 246)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		AMC Networks (US)													co0332012 (88)			289 (74)			23242
				#		AMC Studios (US)													co0318834 (60)
				#		AMC Networks Content Room (US)										co0992498 (1)			159017 (5)			199102
				#		AMC Productions (US)												co0039494 (1)
				#		AMC Networks Iberia (ES)											co0896081 (1)
				#		AMC Networks International Iberia															11703 (7)			122678
				#
				#		Shudder Films (GB)													co0287744 (6)
				#		Shudder Films																				12295 (4)			51159
				#
				#		Shudder Films (US)													co0329743 (1)
				#		Shudder Studios (US)												co0649866 (1)
				#
				#		IFC Films (US)																				3789 (34)			307
				#		IFC Productions (US)												co0163116 (26)			18519 (23)			26468
				#		Independent Film Channel (IFC) Canada (CA)							co0109271 (10)
				#		The Independent Film Channel Productions (US)						co0164785 (4)			10257 (7)			54
				#		Independent Film Channel (US)										co0609786 (2)			11389 (15)			4059
				#
				#		BBC America															co0118334 (112)			2808 (30)			105182
				#		WE tv																						65890 (0)			90241
				#		ALLBLK Original Series (US)											co0985922 (2)
				#
				#	Other companies with the same name.
				#
				#		AMC Pictures (GB)													--co0178817-- (5)
				#		AMC Unlimited (US)													--co0630558-- (1)
				#		AMC-Migrations de Culture (CH)										--co0342810-- (1)
				#		AMC-UCLan Film Production (IN)										--co0776985-- (1)
				#		AMC2 Productions (FR)												--co0701123-- (1)
				#		AMC Films (FR)														--co0361105-- (1)
				#		Runn AMC Productions (US)											--co0264216-- (1)
				#		AMC Media Production (SY)											--co1053733-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		AMC (US)															co0019701 (191)			107 (80)			174
				#		AMC (NL)															co0759230 (3)
				#		AMC España (ES)														co0737214 (5)
				#
				#		AMC+ (US)															co0815501 (85)			1858 (13)			4661
				#		AMC Plus (US)														co0822529 (2)
				#		AMC.com (US)																				2768 (6)			6400
				#
				#		AMC Networks (US)													co0332012 (88)
				#		AMC Networks (ES)													co1070323 (1)
				#
				#		AMC Networks International (GB)										co0668189 (28)
				#		AMC Networks International Central Europe (HU)						co0570103 (14)
				#
				#		AMC Entertainment (NL)												co0251921 (5)
				#		AMC Magyarország (HU)												co0797042 (2)
				#
				#		Shudder (US)														co0602021 (212)			546 (26)			2949
				#
				#		SundanceTV (US)														co0007113 (227)			153 (38)			270
				#		Sundance Now (US)													co0746323 (36)			151 (5)				2363
				#		Sundance Channel Global (US)										co0536718 (10)
				#		Sundance Channel (CA)												co0319525 (6)
				#		SundanceTV (ES)														co0822328 (4)
				#		SundanceNOW.com (US)												co0354847 (4)
				#		Sundance Channel (GB)												co0816708 (3)
				#		SundanceNow Doc Club (US)											co0536717 (3)
				#		SundanceTV (GR)														co1036643 (1)
				#		SundanceTV (PL)														co0888151 (1)
				#		sundancechannel.com (US)																	1761 (1)			3044
				#
				#		IFC Films (US)														co0015762 (678)
				#		IFC Midnight (US)													co0310156 (191)
				#		Independent Film Channel (IFC) (US)									co0046530 (178)
				#		IFC First Take (US)													co0180145 (49)
				#		IFC (US)																					467 (43)			124
				#		IFC TV (US)															co0252564 (13)
				#		Sundance Independent Film Channel (US)								co0013560 (5)
				#		IFC Festival Direct (US)											co0258945 (4)
				#		IFC Films Unlimited (US)											co0832893 (3)
				#		IFC (CA)																					3647 (1)			672
				#
				#		WE tv (US)																					194 (52)			448
				#		We TV Network (US)													co0340786 (44)
				#		WEtv (US)															co0217619 (26)
				#
				#		BBC America															co0118334 (112)			173 (40)			493
				#		Allblk (US)															co0848594 (40)			1955 (25)			4810
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		AMC Film Holdings (US)												co0442035 (9)
				#		AMC Independent (US)												co0441631 (4)
				#		AMC Studios Content Distribution (US)								co0861142 (1)
				#		AMC Foundation (US)													--co0580737-- (1)
				#
				#		Film1 Sundance Channel (NL)											co0379646 (352)
				#		Sundance Channel Home Entertainment (US)							co0092267 (21)
				#		IFC TV/ Sundance Channel Partnerships (US)							co0495248 (1)
				#
				#		IFC in Theaters (US)												co0208997 (6)
				#		IFC Releasing (US)													co0163378 (2)
				#
				#		Cbs Amc Networks Uk Emea Channels Partnership (GB)					co0794271 (18)
				#
				#	Different companies with the same name.
				#
				#		AMC Theatres (US)													--co0130438-- (34)
				#		AMC Theaters (US)													--co0292045-- (11)
				#		Neshaminy Mall & AMC Theater (US)									--co0356776-- (1)
				#		AMC Theatres Distribution (US)										--co1019122-- (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyAmc : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'AMC Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'AMC+'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'AMC'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'AMC Originals'},
					'expression'	: '(^(?:.*?(?:cbs|\&[\s\-\_\.\+]*)[\s\-\_\.\+]*)?amc[\s\-\_\.\+]*(?:$|\+|plus|\.com|studio|network|production|film|entertainment|independent|theat(?:er|re)|foundation|espa[nñ]a|magyarorsz[aá]g)|american?[\s\-\_\.\+]*movie[\s\-\_\.\+]*classics?|shudder|ifc[\s\-\_\.\+]*(?:$|studio|film|production|midnight|first|tv|releas|in[\s\-\_\.\+]*theat(?:er|re)|festival[\s\-\_\.\+]*direct)|independent[\s\-\_\.\+]*film[\s\-\_\.\+]*channel|sundance[\s\-\_\.\+]*(?:tv|now|channel)|bbc[\s\-\_\.\+]*america|we[\s\-\_\.\+]*tv|allblk)',
				},

				#################################################################################################################################
				# Apple
				#
				#	Apple does not seem to own any other studios and also does not have partnerships with other companies.
				#
				#
				#	Parent Companies:		Apple
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Apple Studios
				#	Owned Networks:			Apple TV+
				#
				#	Streaming Services:		Apple TV+
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(96)					(56)
				#	Networks																(345)					(194)
				#	Vendors																	(1117)					(16)
				#	Originals																(57 / 174)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Apple Studios														co0861654 (49)			142848 (56)			194232
				#		Apple Original Films												co0822606 (38)
				#		Apple TV (only very few produced, mostly distributed)				--co0854529-- (31)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Apple TV+															co0546168 (345)			256 (194)			2552
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Apple TV (US)														co0854529 (31)
				#		Apple TV (GB)														co0931939 (5)
				#		Apple TV (IT)														co0750014 (5)
				#		Apple TV (IN)														co1033989 (4)
				#		Apple TV (ES)														co0887931 (1)
				#
				#		Apple Music (US)													co0585513 (15)			638 (4)				1932
				#		Apple Podcasts (US)													co0804590 (12)
				#		Apple I-tunes (US)													co0239755 (5)
				#		iTunes Store																				685	(12)			1377
				#
				#		iTunes (DE)															co0694131 (646)
				#		iTunes (US)															co0177409 (162)
				#		iTunes (CA)															co0424544 (20)
				#		iTunes (GB)															co0531699 (12)
				#		iTunes (IT)															co0428931 (11)
				#		iTunes (AU)															co0657282 (3)
				#		iTunes (BR)															co0636343 (3)
				#		iTunes (IN)															co1021371 (2)
				#		iTunes (NO)															co0613564 (2)
				#
				#		Apple																--co0000267-- (246)
				#		Apple inc															--co0541350-- (6)
				#
				#################################################################################################################################
				MetaCompany.CompanyApple : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Apple Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Apple TV+'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Apple'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Apple Originals'},
					'expression'	: '(^apple(?:[\s\-\_\.\+]*(?:studios?|tv[\s\-\_\.\+]*|original[\s\-\_\.\+]*films?|music|podcasts?|inc))?$|i[\s\-\_\.\+]*tunes)',
				},

				#################################################################################################################################
				# ARD
				#
				#	Owned and funded by the German governament.
				#	ARD consist of a ton of local network stations across Germany.
				#	A lot of titles also produced with various German (and British, and French) Film Funds.
				#	Co-productions and content sharing with UK (BBC, ITV, etc), France (ARTE, etc), Scandinavian and most other European countries.
				#
				#	Parent Companies:		German Governament
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Degeto Film
				#	Owned Networks:			ARD, NDR, WDR, MDR, SWR, RBB, SWF, SDR, ORB, SFB, SDRW, NWDR, BR, HR, RB, SR,
				#							DW, Funk, one, KiKa (ARD+ZDF), Phoenix (ARD+ZDF), 3sat (ARD+ZDF+ORF+SSR),
				#							Previous East-Germany: DFF, DDDE, DFF, DDR, DDR-F1, DDR-F2
				#
				#	Streaming Services:		ARD Mediathek
				#	Collaborating Partners:	ZDF, ARTE, ITV, BBC
				#
				#	Content Provider:		NDR, WDR, MDR, SWR, RBB, SWF, SDR, ORB, SFB, SDRW, NWDR, BR, HR, RB, SR,
				#							DW, Funk
				#	Content Receiver:		one, KiKa, Phoenix, 3sat
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(3821)					(5935)
				#	Networks																(20562)					(2070)
				#	Vendors																	(65)					(0)
				#	Originals																(14053 / 4161)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		ARD (DE)															co1069396 (32)			1629 (1635)			1251
				#		Das Erste (ARD) (DE)																		15170 (34)			35944
				#		ARD 2 (DE)															co0380454 (11)
				#		ARD Werbung (DE)													co0323874 (6)
				#
				#		ARD Studio Washington (US)											co0827406 (1)			89260 (2)			142851
				#		ARD-Studio Wien (AT)												co0527723 (1)
				#		ARD-Studio Warschau (PL)											co1018274 (1)
				#		ARD Studio DDR (DDDE)												co1017738 (1)
				#
				#		ARD/ZDF (DE)														co0297730 (7)
				#		Funk (ARD/ZDF) (DE)													co0622438 (1)
				#
				#		ARD/Degeto Film (DE)												co0061958 (305)			1587 (373)			6187
				#		Degeto Film																					6988 (45)			986
				#
				#		Norddeutscher Rundfunk (DE)																	2916 (724)			7201
				#		NDR International (DE)												co0087780 (9)			153470 (2)			185585
				#		NDR Naturalfilm (DE)												co0787553 (4)			2292 (93)			18407
				#		NDR Kulturförderung in MVP (DE)										co1039527 (1)
				#		NDR in Association with Altayfilm (DE)								co0879011 (1)
				#		NDR/ARD (DE)														co0959826 (1)
				#
				#		Westdeutscher Rundfunk (DE)																	1187 (1061)			46
				#		WDRE																co0011697 (1)
				#
				#		Hessischer Rundfunk (DE)																	5018 (246)			9291
				#		HR Werbung (DE)														co0242006 (1)
				#		hr-Filmförderung (DE)												co0000497 (1)
				#
				#		SWF																							26657 (106)			13983
				#		SWF Werbung (DE)													co0194454 (1)
				#		Werbung im Südwestfunk (DE)											co0632705 (1)
				#
				#		WDR/Arte (DE)														co0237938 (71)			9198 (102)			10946
				#		NDR/Arte (DE)														co0442963 (22)
				#		SWR/Arte (DE)														co0908647 (16)			30132 (31)			99085
				#		RBB/Arte (FR)														co0174684 (13)
				#		RBB/Arte (DE)														co0695411 (11)
				#		MDR / Arte (DE)														co0319227 (4)
				#		RB/Arte (DE)														co0753522 (2)
				#		WDR/Arte Grand Accord (DE)											co0378995 (2)
				#		HR Arte (DE)														co0910946 (1)
				#		SR / Arte (DE)														co0291283 (1)
				#		Rundfunk Berlin-Brandenburg in Zusammenarbeit mit ARTE (DE)			co0626833 (1)
				#
				#		Deutsche Welle (DE)													co0065221 (39)			69625 (39)			95576
				#		Deutsche Welle TV (DE)												co0763053 (3)
				#		DW Studios (DE)																				97309 (3)			10263
				#		Deutsche Welle Akademie (DE)										co0805147 (1)
				#		DW Akademie (DE)													co1063921 (1)
				#		DW-Filmproduktion (DE)												co1045188 (1)
				#		DW (DE)																co0622450 (1)
				#
				#		Deutscher Fernsehfunk (DFF)											co0114174 (176)			10128 (370)			23372
				#		Deutscher Fernsehfunk (DFF)/Fernsehen der DDR												12989 (3)			121235
				#
				#		Sender Freies Berlin (DE)											co0041492 (188)			3373 (95)			7024
				#		SFB Werbung GmbH (DE)												co0084641 (2)
				#
				#		Rundfunk Berlin-Brandenburg (DE)															1371 (274)			2067
				#		Rbb 24 (DE)															co0888797 (1)
				#
				#		Südwestrundfunk (DE)																		2918 (420)			124
				#		Südwestdeutscher Rundfunk (DE)																7954 (101)			210
				#
				#		Bayerischer Rundfunk (DE)																	2919 (755)			162
				#		Mitteldeutscher Rundfunk (DE)																269 (253)			588
				#		Saarländischer Rundfunk (DE)																14182 (73)			23983
				#		Radio Bremen																				22344 (72)			1775
				#		Nord- und Westdeutscher Rundfunkverband (NWRV) (DE)					co0128591 (10)			22294 (15)			84113
				#		ORB Filmproduktion Wiesbaden (DE)									co0285377 (5)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Arbeitsgemeinschaft ... Rundfunkanstalten der ... (ARD) (DE)		co0024077 (1099)
				#		ARD (DE)															co1069396 (32)			265 (865)			308
				#		ARD Mediathek (DE)													co0840291 (441)
				#		Das Erste (DE)														co0799614 (439)			269 (18)			442
				#		ARD TV (DE)															co0852680 (233)
				#		ARD-alpha (DE)														co0091806 (61)			871 (20)			2147
				#		ARD Plus (DE)														co0918729 (41)
				#		ARD Video (DE)														co0223205 (7)
				#		ARD Aktuell (DE)													co1020144 (1)
				#		ARD Panorama (DE)													co0878991 (1)
				#		ARD Design (DE)														co0489664 (0)
				#		ARD																							3195 (0)			7141
				#
				#		Norddeutscher Rundfunk (NDR) (DE)									co0028284 (998)
				#		NDR Fernsehen (DE)													co0274575 (199)			568 (175)			577
				#		NDR (DE)															co0989452 (138)
				#
				#		Süddeutscher Rundfunk (SDR) (DE)									co0059346 (162)
				#		SDR Fernsehen (DE)													co0476379 (13)
				#		SDR																							2995 (5)			2946
				#		SDRW - SDR Regionalprogramm																	3843 (1)			7534
				#		Süddeutscher Rundfunk 3 (SDR3) (DE)									co0905950 (1)
				#
				#		Westdeutscher Rundfunk (WDR) (DE)									co0075650 (1780)
				#		WDR Fernsehen (DE)													co0217768 (246)			270 (213)			1135
				#		Rockpalast WDR (DE)													co0577985 (1)
				#		WDR Online Hörfunk (DE)												co0891048 (0)
				#
				#		Südwestrundfunk (SWR) (DE)											co0047104 (791)
				#		SWR Fernsehen (DE)													co0961937 (152)			271 (140)			1162
				#		SWR3 (DE)															co0988580 (0)
				#		SWR2 (DE)															co1035748 (1)
				#
				#		Südwestfunk (SWF) (DE)												co0014369 (224)
				#		SWF																							3143 (2)			3952
				#
				#		Ostdeutscher Rundfunk Brandenburg (ORB) (DE)						co0001882 (85)
				#		ORB-Fernsehen (DE)													co0839861 (26)
				#		ORB (DE)															co0894463 (24)
				#
				#		Nordwestdeutscher Rundfunk (NWDR) (DE)								co0055445 (22)
				#		NWDR																co0064040 (22)
				#
				#		Mitteldeutscher Rundfunk (MDR) (DE)									co0015124 (576)
				#		MDR Fernsehen														co0452750 (192)			106 (89)			1118
				#		MDR (DE)															co1034271 (89)
				#		MDR Sputnik (DE)													co0613282 (2)
				#
				#		Bayerischer Rundfunk (BR) (DE)										co0051615 (1363)
				#		BR Fernsehen (DE)													co0203048 (210)			492 (161)			871
				#		BR-alpha															co0860660 (22)			3417 (12)			5870
				#
				#		Hessischer Rundfunk (HR) (DE)										co0072480 (550)
				#		hr-fernsehen (DE)													co0248658 (172)			654 (76)			1033
				#		German Television ARD / Hessischer Rundfunk (DE)					co0497336 (2)
				#
				#		Saarländischer Rundfunk (SR) (DE)									co0003707 (125)
				#		SR Fernsehen														co0840146 (20)			2814 (2)			5977
				#		SR (DE)																co0227567 (14)
				#
				#		Rundfunk Berlin-Brandenburg (RBB) (DE)								co0099654 (591)
				#		RBB Fernsehen														co0768255 (196)			346 (74)			1220
				#		RBB (DE)															co1059146 (54)
				#		RBB Media (DE)														co0208114 (20)
				#		RBB Berlin (DE)														co0992810 (7)
				#		RBB Brandenburg (DE)												co1000425 (4)
				#		rbb 88.8 (DE)														co0914202 (1)
				#
				#		Sender Freies Berlin (SFB) (DE)										co0041492 (188)
				#		SFB (DE)															co0894460 (24)			2507 (6)			1036
				#		SFB Fersehen (DE)													co0895263 (16)
				#		SFB1 (DE)															co0839856 (12)
				#
				#		Radio Bremen (RB) (DE)												co0048844 (102)
				#		Radio Bremen TV (DE)												co0968172 (16)
				#		Radio Bremen Fernsehen																		1804 (5)			4495
				#
				#		Deutscher Fernsehfunk (DFF) (DDDE)									co0114174 (176)			3635 (0)			6900
				#		Fernsehen der DDR (DDDE)											co0181346 (98)
				#		Fernsehen der DDR 1 (DDR-F1) (DDDE)									co0685769 (22)
				#		Fernsehen der DDR 2 (DDR-F2) (DDDE)									co0971729 (11)
				#		DFF 1 (DDDE)														co0180705 (8)			345 (79)			1084
				#		DFF 2 (DDDE)														co0889776 (4)			2071 (1)			2132
				#		DFF Länderkette (DE)												co0982164 (3)
				#		DDR1 (DE)																					2070 (6)			3340
				#		DDR-F1																						1703 (3)			3936
				#		Fernsehen der DDR																			2883 (0)			6609
				#
				#		Funk (DE)															co0609268 (22)			76638 (21)			111979
				#		funk (DE)																					428 (17)			1665
				#
				#		DW News (DE)														co0804512 (1)
				#		Deutsche Welle (DE)																			1594 (3)			3803
				#
				#		Kinderkanal (KiKA) (DE)												co0030553 (376)
				#		Kika (DE)															co0895262 (145)			268 (215)			239
				#		ARD / ZDF Kinderkanal (KIKA) (DE)									co0937862 (126)
				#		KIKA Mediathek (DE)													co1050978 (25)
				#
				#		one (DE)															co0185608 (103)			2595 (4)			6147
				#		Phoenix (DE)														co0178657 (90)			2325 (13)			3860
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Symphonic Orchestra of the Mitteldeutscher Rundfunk (DE)			co0328560 (1)
				#		MDR Rundfunkchor (DE)												co0549240 (1)
				#		Norddeutscher Rundfunk Sinfonieorchester (DE)						co0125086 (1)
				#		Norddeutscher Rundfunk Chor (DE)									co0125085 (1)
				#		HR-Sinfonieorchester (DE)											co0503369 (1)
				#		NDR Chor (DE)														co0125914 (1)
				#		NDR Sinfonieorchester (DE)											co0125915 (1)
				#		NDR Philharmonic Orchestra (DE)										co0298180 (1)
				#		Radio-Philharmonie Hannover des NDR (DE)							co0125917 (1)
				#		RTO - Orchester des NWDR (DE)										co0264412 (1)
				#		ARD Hauptstadtstudio Berlin (DE)									co1011585 (1)
				#		HR Media Lizenz (DE)												co0604266 (1)
				#		MDR Sinfonieorchester (DE)											co0549239 (0)
				#		Symphonieorchester des NDR (DE)										co0135975 (0)
				#		Sinfonieorchester des Südwestfunks (DE)								co0107837 (0)
				#		Chor des NWDR (DE)													co0212720 (0)
				#
				#		Deutsches Rundfunkarchiv Babelsberg (DE)							co0085892 (5)
				#		Fernseharchiv Rbb (DE)												co0833555 (3)
				#		SFB Archiv (DE)														co0738126 (2)
				#		NDR-Archiv (DE)														co0298474 (1)
				#		German Broadcasting Archives (DE)									co0760311 (1)
				#		Stiftung Deutsches Rundfunkarchiv (DE)								co0616840 (1)
				#		Deutches Rund Funk Archiv, Frankfurt (DE)							co0382269 (1)
				#
				#		Fernsehballett des DFF (DDDE)										co0114620 (1)
				#
				#		Degeto-Commerzbank (DE)												co0294660 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyArd : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ARD Studio'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ARD'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ARD'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ARD Originals'},
					'expression'	: '((?:^|[\s\-\/])(?:ard|ndr|wdre?|hr|swf|sdrw?|sfb|swr|rbb|br|rb|sr|mdr|orb|nwdr|dw|dff|funk|kika|ddr(?:[\s\-\_\.\+]*f)?)\d?(?:$|[\s\-\/])|das[\s\-\_\.\+]*erste|arbeitsgemeinschaft.*?rundfunkanstalten|degeto|(?:norddeutscher|süddeutscher|(?:nord)?westdeutscher|ostdeutscher|hessischer|mitteldeutscher|saarländischer)[\s\-\_\.\+]*rundfunk|südwest(?:deutscher)?[\s\-\_\.\+]*(?:rund)?funk|deutsche[\s\-\_\.\+]*welle|deutscher[\s\-\_\.\+]*fernsehfunk|fernsehen[\s\-\_\.\+]*der[\s\-\_\.\+]*ddr|sender[\s\-\_\.\+]*freies[\s\-\_\.\+]*berlin|rundfunk[\s\-\_\.\+]*berlin[\s\-\_\.\+]*brandenburg|bayerischer[\s\-\_\.\+]*rundfunk|radio[\s\-\_\.\+]*bremen|deutsches[\s\-\_\.\+]*rundfunk|german[\s\-\_\.\+]*broadcasting|kinder[\s\-\_\.\+]*kanal|^(?:one|phoenix)$)',
				},

				#################################################################################################################################
				# ABC (AU)
				#
				#	Parent Companies:		Australian Government
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			ABC
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	BBC, ITV, Channel 4, Sky, ARD, ZDF
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1818)					(335)
				#	Networks																(2201)					(641)
				#	Vendors																	(205)					(0)
				#	Originals																(729 / 871)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Australian Broadcasting Corporation (ABC) (AU)						co0051111 (866)			401 (313)			1253
				#		ABC																							166275 (11)			216247
				#		ABC3																						108530 (1)			159979
				#
				#		ABC-TV Productions (AU)												co0573602 (13)
				#		ABC TV																						426 (12)			5026
				#
				#		ABC for Kids (AU)													--co0530354-- (60)
				#		ABC TV Children's Melbourne (AU)									co0451084 (2)
				#		ABC TV Children's Department Adelaide (AU)							co0142606 (1)
				#		ABC TV Children's Department Sydney (AU)							co0798189 (1)
				#
				#		ABC TV News and Current Affairs (AU)								co0674885 (2)
				#		ABC TV Indigenous Programs Unit (AU)								co0691266 (2)
				#		ABC TV Religious Unit (AU)											co0691282 (1)
				#		ABC Natural History Unit (AU)										co0805649 (1)
				#		ABC R+D (AU)														co0699016 (1)
				#		Science Unit - Australian Broadcasting Commission (ABC) (AU)		co0595394 (1)
				#
				#		ABC Radio National (AU)												--co0640667-- (1)
				#		ABC listen (AU)														--co1016505-- (0)
				#		ABC Podcasts (AU)													--co1001110-- (0)
				#
				#	Other production companies.
				#
				#		Australian Broadcasting Corporation (ABC), Radio Archives (AU)		--co0107728-- (5)
				#		ABC Studios Artarmon (AU)											--co0647385-- (1)
				#		ABC FM (AU)															--co0805995-- (1)
				#
				#	Other companies with the same name.
				#
				#		ABC of Love and Sex Film Productions (AU)							--co0027159-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		ABC (AU)															co0051111 (866)			60 (532)			18
				#		Australian Broadcasting Company (AU)								co0513317 (33)
				#		Australian Broadcast Corporation															1228 (1)			3713
				#
				#		ABC3 (AU)															co0385785 (54)
				#		ABC2 (AU)															co0202700 (19)
				#		ABC1 (AU)															co0395856 (16)
				#		ABC Channel 2 (AU)													co0892147 (1)
				#
				#		ABC for Kids (AU)													co0530354 (60)
				#		ABC KIDS (AU)																				193 (14)			2854
				#
				#		ABC News 24 (AU)													co0396190 (4)
				#		ABC News (AU)																				141 (3)				601
				#
				#		ABC Me (AU)															co0638282 (104)			138 (59)			279
				#		ABC iview (AU)														co0589680 (67)			1327 (4)			142
				#		ABC Comedy (AU)														co0772897 (3)			135 (28)			321
				#
				#		ABC TV Asia Pacfic (AU)												co0142963 (19)
				#		ABC-TV Productions (AU)												co0573602 (13)
				#		ABC TV Plus (AU)													co1030092 (1)			2057 (9)			5069
				#
				#		ABC Commercial (AU)													co0432662 (50)
				#		ABC Video (AU)														co0061664 (23)
				#		ABC Toons (AU)														co1059801 (8)
				#		ABC Countrywide (AU)												co0157128 (1)
				#		ABC Classics (AU)													co0892324 (1)
				#
				#	Other companies with similar names.
				#
				#		Australian Broadcasting Commission (AU)								--co0207399-- (231)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		ABC DVD (AU)														co0324755 (9)
				#		ABC International (AU)												co0099385 (6)
				#		Australian Broadcasting Corporation (ABC), Radio Archives (AU)		co0107728 (5)
				#		ABC Enterprises (AU)												co0167586 (4)
				#		ABC TV Marketing (AU)												co0404882 (3)
				#		ABC Films (AU)														co0771493 (1)
				#		ABC Video Enterprises (AU)											co0730018 (1)
				#		ABC Open (AU)														co0610625 (1)
				#		ABC Art (AU)														co1055432 (1)
				#		ABC New Media and Digital Services (AU)								co0211730 (1)
				#
				#		Australian Broadcasting Corporation (ABC) Content Sales (AU)		co0146211 (71)
				#		Australian Broadcasting Corporation Library Sales (AU)				co0300082 (7)
				#		ABC Australia Footage Sales (AU)									co0225761 (3)
				#		ABC Australia Footage Sales (AU)									co0225761 (3)
				#		Australian Broadcasting Corporation Footage Sales (AU)				co0298327 (1)
				#		ABC Video Program Sales (AU)										co0696457 (1)
				#		ABC Library Sales (AU)												co0805351 (1)
				#
				#		ABC Radio Adelaide (AU)												co0690730 (1)
				#		ABC Radio Melbourne (AU)											co0649060 (1)
				#		ABC FM (AU)															co0805995 (1)
				#		ABC Music (AU)														co0960276 (1)
				#		ABC Symphony Orchestra (AU)											co0220836 (1)
				#
				#		ABC Studios Artarmon (AU)											co0647385 (1)
				#		ABC Studios, Gore Hill (AU)											co0752802 (1)
				#		ABC Melbourne (AU)													co0326245 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyAubc : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'AUBC Productions'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'AUBC'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'AUBC'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'AUBC Originals'},
					'expression'	: '(abc\d?|australian?[\s\-\_\.\+]*broadcast(?:ing)?[\s\-\_\.\+]*(?:company|corporation))',
				},

				#################################################################################################################################
				# BBC
				#
				#	BBC does a lot of collaborations with their local competitors (ITV, CH4) and internationally in the US (BBC America),
				#	and Canada, Australia, New Zealand, Germany, France, and other European countries.
				#
				#	Parent Companies:		UK government
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			BBC Studios
				#	Owned Networks:			BBC 1-3
				#
				#	Streaming Services:		BBC iPlayer, BritBox
				#	Collaborating Partners:	BritBox, ITV, CH4, Sky, AUBC, ARD, ZDF, Netflix, HBO
				#
				#	Content Provider:		BBC America (BBC+AMC), Netflix, HBO, Hulu, Amazon, Disney, ITV, CH4, Sky, AUBC, ARD, ZDF
				#	Content Receiver:		BBC America (BBC+AMC), Netflix, HBO, Hulu, Amazon, Disney, ITV, CH4, Sky, AUBC, ARD, ZDF
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(4581)					(6345)
				#	Networks																(21991)					(4787)
				#	Vendors																	(1168)					(1)
				#	Originals																(3035 / 3510)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		BBC																							1149 (4320)			3324
				#		BBC One																						1442 (32)			7710
				#		BBC Two																						91307 (30)			144640
				#		BBC Four																					3383 (189)			16630
				#
				#		BBC Films (GB)														co0103694 (414)			3510 (372)			288
				#		BBC Two Films (GB)													co0307892 (6)
				#		BBC Two England (GB)												co0726893 (4)
				#
				#		BBC Studios (GB)													co0592426 (292)			1012 (270)			80893
				#		BBC Studios (US)													co0698073 (29)			88204 (19)			108563
				#		BBC Studios (IN)													co0740959 (16)			33592 (12)			123348
				#		BBC Studios (AU)													co0752302 (7)			104679 (12)			120868
				#		BBC Studios Germany													co0875442 (4)			167937 (3)			216932
				#		BBC Studios France													co0728849 (2)			81883 (8)			137002
				#		BBC Studios Wales (GB)												co0606007 (4)
				#		BBC Studios (NZ)													co1000688 (1)			104679 (4)			120868
				#
				#		BBC Studios Science Unit																	76598 (20)			113381
				#		BBC Studios Documentary Unit										co0657045 (8)			85965 (12)			130993
				#		BBC Studios Unscripted Productions (GB)								co0653588 (7)			70416 (4)			96885
				#		BBC Studios Factual Entertainment Productions (GB)					co0855002 (6)
				#		BBC Studios Kids & Family											co0952028 (5)			165545 (5)			205723
				#		BBC Studios Productions																		162938 (5)			214718
				#		BBC Studios Entertainment Productions														171670 (4)			222625
				#		BBC Studios Drama Productions																165372 (2)			216944
				#		BBC Studios Events Productions (GB)									co0971251 (1)			108532 (18)			159981
				#		BBC Studios Auntie Productions (GB)									co0692523 (1)
				#		BBC Studios Topical & Live (GB)										co0658426 (1)
				#		BBC Studios Productions Nordics (GB)								co0768859 (1)
				#		BBC Studios Nordic Productions (DK)									co1050406 (0)
				#		BBC Studios Distribution (GB)										co0775667 (4)			170766 (3)			221844
				#
				#		BBC Earth															co0317480 (15)			18003 (8)			8090
				#		BBC Earth Productions (GB)											co0545593 (2)
				#		BBC Earth MD (WWD) (GB)												co0491244 (1)
				#		BBC Earth Productions (Life) (GB)									co0353205 (1)
				#		BBC Earth Productions (Africa) (GB)									co0491243 (0)
				#
				#		BBC Science (GB)													co0872432 (1)
				#		BBC Scienceworld (GB)												co0537139 (0)
				#
				#		BBC Natural History Unit											co0303279 (21)			2032 (75)			9050
				#		BBC Natural History													co0098758 (18)
				#		BBC History Production (GB)											co0445171 (2)
				#
				#		BBC Drama Productions												co0231124 (11)			1895 (24)			25570
				#		BBC Drama Group (GB)												co0103536 (6)			2748 (11)			6710
				#		BBC Northern Ireland Drama Productions (GB)							co0544782 (1)
				#
				#		BBC Radio 4 (GB)													co0314450 (81)
				#		BBC Radio 3 (GB)													co0545558 (11)			61433 (2)			27900
				#		BBC Radio 2 (GB)													co0277403 (7)			38914 (19)			35651
				#		BBC Radio 1 (GB)													co0501395 (5)
				#		BBC Radio (GB)														co0020220 (4)
				#		BBC Radio Collection (GB)											co1072031 (1)
				#
				#		BBC Music															co0377983 (13)			13491 (117)			104151
				#		BBC Worldwide Music (GB)											co0526172 (1)
				#		BBC Music Entertainment (GB)										co0127837 (1)
				#
				#		BBC Comedy															co0256436 (10)			2873 (25)			44332
				#		BBC Comedy-North (GB)												co0150936 (3)
				#
				#		BBC Arabic (GB)														co0687055 (16)
				#		BBC Arabic (IL)																				73598 (5)			108529
				#
				#		BBC Current Affairs (GB)											co0245082 (7)			126758 (1)			169941
				#		BBC Digital Current Affairs (GB)									co0685213 (2)			95633 (1)			100621
				#
				#		BBC Media Action (GB)												co0470945 (3)
				#		BBC Media Action (BD)												co0579133 (1)
				#
				#		BBC Arts															co0466169 (4)			27566 (44)			12935
				#		BBC Scotland Arts (GB)												co0598746 (1)
				#		BBC Art (GB)														co1011972 (1)
				#
				#		British Broadcasting Corporation (BBC West) (GB)					co0432727 (11)
				#		British Broadcasting Corporation (BBC Bristol) (GB)					co0402393 (11)
				#		British Broadcasting Corporation (BBC North) (GB)					co0486599 (9)
				#		British Broadcasting Corporation (BBC Midlands) (GB)				co0485419 (9)
				#		British Broadcasting Corporation (BBC Scotland) (GB)				co0486601 (4)
				#		British Broadcasting Corporation (BBC Wales) (GB)					co0486603 (3)
				#		British Broadcasting Corporation (BBC Northern Ireland) (GB)		co0486613 (2)
				#		British Broadcasting Corporation (BBC Birmingham) (GB)				co0486604 (1)
				#		British Broadcasting Corporation (BBC Manchester) (GB)				co0572286 (1)
				#		British Broadcasting Corporation (BBC East) (GB)					co0679922 (1)
				#		British Broadcasting Corporation (BBC South) (GB)					co0608298 (1)
				#
				#		BBC Worldwide																				120 (88)			3164
				#		BBC Worldwide Productions											co0304634 (25)			30777 (16)			128577
				#		BBC Worldwide Productions (US)																30777 (17)			128577
				#		BBC Worldwide Productions India (IN)								co0401549 (11)
				#		BBC Worldwide France																		70448 (8)			56580
				#		BBC Worldwide Americas																		10236 (3)			59554
				#		BBC Worldwide Productions (GB)										co0274311 (4)
				#		BBC Worldwide Productions (FR)										co0488378 (2)			70448 (8)			56580
				#		BBC Worldwide Digital Studios (GB)									co0576599 (3)
				#		BBC Worldwide ANZ (AU)												co0659811 (1)
				#
				#		BBC North West (GB)													co0242639 (11)
				#		BBC North (GB)														co0305383 (7)
				#		BBC South-West (GB)													co0130009 (6)
				#		BBC West (GB)														co0516659 (1)
				#		BBC South East (GB)													co0283200 (3)
				#		BBC South (GB)														co0369502 (2)
				#		BBC East (GB)														co0801365 (1)
				#		BBC North East & Cumbria (GB)										co0516676 (1)
				#		BBC East Anglia (GB)												co0299328 (1)
				#		BBC North East and Cumbria (GB)										co0853286 (1)
				#		BBC South and East (Norwich) (GB)									co0621097 (1)
				#		BBC East Midlands (GB)												co0463969 (1)
				#		BBC West Midlands (GB)												co0516672 (1)
				#
				#		BBC Scotland														co0086182 (272)			1200 (201)			3712
				#		BBC America															--co0118334-- (112)		2808 (30)			105182
				#		BBC Wales															co0103752 (89)			2080 (141)			4762
				#		BBC Wales (GB)														co0103752 (88)			2080 (144)			4762
				#		BBC Manchester (GB)													co0125663 (52)			2253 (23)			52763
				#		BBC Birmingham (GB)													co0129827 (36)			219 (11)			44918
				#		BBC Cymru Wales														co0197209 (35)
				#		BBC England (GB)													co0813700 (6)
				#		BBC London (GB)														co0398746 (3)			84100 (3)			107027
				#		BBC Yorkshire (GB)													co0534033 (2)
				#		BBC Newcastle (GB)													co0458044 (1)
				#		BBC Midlands (GB)													co0408144 (1)
				#		BBC Elstree (GB)													co0485699 (1)
				#		BBC Cambridgeshire & East (GB)										co0516725 (0)
				#
				#		BBC Bristol (GB)													co0130080 (98)			2807 (37)			31272
				#		BBC Bristol Factual (GB)											co0315578 (4)
				#		BBC Bristol Productions												co0418400 (1)
				#		BBC Bristol Film Lab (GB)											co0263467 (1)
				#
				#		BBC Productions														co0296207 (23)			108941 (20)			158991
				#		BBC Production USA (US)												co0098707 (13)
				#		BBC Production Yorkshire (GB)										co0945424 (1)			146600 (2)			198017
				#		BBC Productions West Midlands (GB)									co0442163 (1)
				#		BBC Productions West (GB)											co0920461 (1)
				#		BBC Productions North West (GB)										co0363467 (1)
				#		BBC Productions Manchester (GB)										co0838768 (0)
				#
				#		BBC CBeebies																				57894 (42)			79173
				#		CBeebies (GB)														co0219933 (208)
				#		CBBC In-House (GB)													co0451949 (12)
				#		CBBC Productions													co0639136 (4)			1763 (11)			87768
				#		CBBC Productions Scotland																	138224 (4)			188723
				#		CBBC Development (GB)												co0381268 (2)
				#
				#		BBC Schools (GB)													co0457128 (34)
				#		BBC Children's Productions											co0324563 (11)			33006 (2)			125982
				#		BBC Education (GB)													co0134301 (10)
				#		BBC Children's International (GB)									co0219545 (3)
				#		BBC Children's Drama												co0104248 (2)			47824 (3)			26363
				#		BBC Teach (GB)														co0831132 (1)			126759 (1)			176597
				#
				#		BBC TV (GB)															co0294698 (163)			114813 (86)			161115
				#		BBC Television Centre																		20472 (17)			110808
				#		BBC-TV Productions (GB)												co0417954 (9)
				#		BBC Lionheart Television (GB)										co0178363 (4)			72707 (4)			107595
				#		BBC Television Enterprises Production Unit (GB)						co1006872 (1)
				#		BBC Television Enterprises (GB)										co1006871 (1)
				#
				#		BBCi (GB)															co0206538 (7)
				#		BBCI (US)															co0338843 (1)
				#
				#		BBC Northern Film Unit (GB)											co0246062 (1)
				#		BBC Film Lab (GB)													co0262608 (1)
				#		BBC Film Club (GB)													co0761679 (1)
				#
				#		BBC One Creative Services											co0610967 (1)
				#		BBC New Creatives North (GB)										co1048403 (1)
				#
				#		BBC Scotland Studios (GB)											co0659275 (14)
				#		BBC English Regions (GB)											co0403283 (3)			109660 (2)			158939
				#		BBC Birmingham Lifestyle and Features (GB)							co0370496 (1)
				#		BBC Northern Ireland Features Production (GB)						co0901031 (0)
				#
				#		BBC Storyville														co0119621 (46)			13992 (40)			50510
				#		BBC Entertainment													co0103738 (32)
				#		BBC Pebble Mill (GB)												co0159688 (18)
				#		BBC Arena (GB)														co0104639 (14)			11055 (44)			17179
				#		BBC Open University Production Centre (GB)							co0402320 (11)
				#		BBC Persian (GB)													co0618243 (11)			32272 (9)			128909
				#		BBC World Service (GB)												co0377087 (9)
				#		BBC News																					17351 (9)			99697
				#		BBC Switch (GB)														co0239708 (5)
				#		BBC Documentaries													co0500559 (4)			41817 (9)			76010
				#		BBC Legends (GB)													co1016646 (3)
				#		BBC Wildvision (GB)													co0131402 (3)
				#		BBC Community Programme Unit (GB)									co0295789 (3)
				#		BBC Horizon (GB)													co0078164 (2)			50067 (21)			78442
				#		BBC Events Production, London (GB)									co0441937 (2)
				#		BBC di Renato Barbieri												co0288712 (1)			66174 (1)			53451
				#		BBC Writersroom	(GB)												co0364786 (1)			56143 (1)			39454
				#		BBC VR Hub (GB)														co0747089 (1)
				#		BBC (NL)															co0921192 (1)
				#		BBC Gamezlab (GB)													co0167164 (1)
				#		BBC FictionLab (GB)													co0146506 (1)
				#		BBC Academy (GB)													co0437284 (1)
				#		BBC World Service Trust (GB)										co0360835 (1)
				#		BBC 7 (GB)															co1067108 (0)
				#		British Broadcasting Corporation Studios Cymru Wales (GB)			co0717843 (0)
				#
				#		BBC Studioworks (GB)												--co0654320-- (10)
				#		BBC Motion Gallery, British Broadcasting Corporation Worldwide (GB)	--co0273078-- (4)
				#		BBC Radio and Television (GB)										--co0758651-- (1)
				#		BBC Proms (GB)														--co0366863-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		British Broadcasting Corporation (BBC) (GB)							co0043107 (7458)
				#		BBC (GB)															co1039429 (15)			246 (0)				7
				#		BBC																							2625 (2)			6052
				#		BBC																							3048 (1)			6977
				#		BBC																							2448 (0)			5909
				#		BBC																							1217 (0)			3700
				#		BBC																							1598 (0)			4173
				#
				#		BBC One																co0234667 (916)			77 (2108)			4
				#		BBC One Wales (GB)													co0164585 (25)			2607 (6)			6142
				#		BBC One Northern Ireland (GB)										co0561347 (6)			2689 (9)			6291
				#		BBC One Scotland (GB)												co0642119 (5)			3001 (5)			6824
				#		BBC One North West (GB)												co0473661 (5)
				#		BBC One North East & Cumbria (GB)									co0853285 (2)
				#		BBC One South East													co0883449 (1)			3709 (1)			6980
				#		BBC One West Midlands (GB)											co0780894 (1)
				#		BBC One London (GB)													co0882716 (1)
				#		BBC One Yorkshire (GB)												co0918458 (1)
				#		BBC One South & Oxfordshire (GB)									co1045058 (1)
				#		BBC One West (GB)													co0883438 (1)
				#		BBC One East & Cambridgeshire (GB)									co0781048 (1)
				#		BBC One Yorkshire & Lincolnshire (GB)								co0803582 (1)
				#		BBC One South West & Channel Islands (GB)							co0883439 (1)
				#		BBC One Wales																				1992 (0)			4991
				#		BBC One Northern Ireland																	2186 (0)			5382
				#		BBC One Scotland																			900 (0)				3543
				#
				#		BBC Two																co0234496 (805)			33 (1694)			332
				#		BBC Two Scotland													co0503643 (7)			3172 (4)			7111
				#		BBC Two England (GB)												co0726893 (4)
				#		BBC Two Northern Ireland											co0625141 (3)			3568 (1)			6419
				#		BBC Two Wales																				899 (0)				3542
				#		BBC TWO																						3717 (0)			7432
				#		BBC TWO																						3718 (0)			7432
				#		BBC2 (GB)															co0308047 (75)
				#		BBC2 Wales (GB)														co0348803 (3)
				#
				#		BBC Three															co0399177 (243)			278 (339)			3
				#		BBC3 (GB)															co0415789 (26)
				#		BBC 3 Fresh Online (GB)												co0471188 (1)
				#		BBC Three Fresh (GB)												co1067868 (1)
				#
				#		BBC Four															co0290595 (161)			121 (402)			100
				#
				#		BBC Scotland														co0086182 (274)			616 (65)			3278
				#		BBC America															co0118334 (112)			173 (40)			493
				#		BBC Northern Ireland												co0103544 (97)			2319 (1)			5687
				#		BBC Canada															co0142197 (8)
				#
				#		BBC iPlayer (GB)													co0534118 (142)			279 (40)			1155
				#		BBC Online (GB)														co0477883 (11)
				#		BBCi																co0206538 (7)			3592 (1)			7381
				#		BBC Player (DE)														co0989615 (7)
				#		BBC Comedy Online (GB)												co0315543 (7)
				#
				#		BBC Choice (GB)														co0104650 (25)			736 (12)			126
				#		BBC Choice Scotland (GB)											co0482050 (1)

				#		BBC Knowledge														co0365373 (1)			2402 (2)			3590
				#		BBC Knowledge (ZA)													co0401989 (1)
				#		BBC Knowledge (PL)													co0401784 (1)
				#
				#		BBC Television														co0422378 (109)			909 (62)			3546
				#		BBCTV (GB)															co0321381 (3)
				#		BBC Television Centre												co0270289 (1)			1076 (0)			3655
				#		BBC UKTV															co0479331 (0)			460 (3)				1001
				#
				#		BBC Earth (GB)														co0317480 (15)			3242 (2)			6852
				#		BBC Earth																					1692 (0)			3859
				#
				#		CBBC (GB)															co0219933 (208)			137	(178)			15
				#		CBeebies (GB)														co0265997 (165)			486 (143)			166
				#		CBeebies (PL)														co0871749 (1)
				#		Children's BBC														co0832669 (22)
				#		BBC Kids (CA)														co0410030 (5)			1127 (4)			414
				#
				#		BBC News															co0530479 (44)			455 (15)			375
				#		BBC World (GB)														co0114729 (39)
				#		BBC World News														co0460362 (15)			618 (16)			317
				#		BBC News 24 (GB)													co0114728 (15)
				#		BBC News Channel (GB)												co0531653 (15)
				#		BBC World News Japan (JP)											co0405647 (6)
				#		BBC News NI (GB)													co0861902 (1)
				#		BBC World News America (US)											co0324701 (1)
				#
				#		BBC First															co0537097 (75)			838 (1)				1051
				#		BBC Sport															co0132809 (69)			2191 (1)			5421
				#		BBC Alba															co0246015 (49)			2179 (3)			5384
				#		BBC Red Button														co0453153 (31)			1118 (5)			428
				#		BBC HD																co0334989 (11)
				#		BBC Parliament														co0471445 (5)			2857 (2)			6223
				#		BBC Brit (NO)														co0621988 (5)
				#		BBC Lifestyle														co0370496 (1)			3071 (1)			7033
				#		BBC Select																					3688 (1)			7440
				#		BBC Ideas (GB)														co0806831 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		BBC Worldwide														co0103957 (319)			1661 (0)			4337
				#		BBC Worldwide Americas												co0065632 (30)
				#		BBC Worldwide North America											co0593490 (4)
				#		BBC Worldwide Digital Entertainment (GB)							co0344444 (2)
				#		BBC Worldwide Motion Gallery (GB)									co0272944 (2)
				#		BBC Worldwide Canada (CA)											co0497354 (1)
				#		BBC Worldwide Japan (JP)											co0210507 (1)
				#
				#		BBC Oxford (GB)														co0659116 (1)
				#		BBC Essex (GB)														co0628629 (1)
				#		BBC South West and Channel Islands (GB)								co0516755 (1)
				#		BBC Yorkshire & Lincolnshire (GB)									co0516737 (1)
				#		BBC Belfast (GB)													co0756060 (0)
				#
				#		BBC Video (GB)														co0114992 (49)
				#		BBC Video															co0137763 (36)
				#		BBC Video (AU)														co0811069 (1)
				#		BBC Video (JP)														co0963204 (1)
				#
				#		BBC Home Service (GB)												co0990657 (3)
				#		BBC Home Video (GB)													co0417955 (2)
				#		BBC Studios Home Entertainment (GB)									co0960250 (1)
				#		BBC Active Video for Learning (GB)									co0631186 (1)
				#		BBC Video Limited (GB)												co0426629 (1)
				#
				#		BBC Sounds (GB)														co0858275 (2)
				#		BBC Radio Oxford (GB)												co0548872 (1)
				#		BBC Audio (GB)														co1007584 (1)
				#		BBC Classical Music (GB)											co0261608 (1)
				#		BBCRecorders (US)													co0321397 (1)
				#
				#		BBC Hulton Library, London (GB)										co0105842 (2)
				#		BBC Television Library (GB)											co0660947 (1)
				#		BBC Stills Library (GB)												co0440119 (1)
				#		BBC Film & Videotape Library (GB)									co0377398 (1)
				#		BBC Wales Film Library (GB)											co0411485 (0)
				#		BBC Library (GB)													co0801464 (0)
				#
				#		BBC Archive (GB)													co0874518 (3)
				#		BBC Broadcast Archive (GB)											co0709699 (3)
				#		BBC Written Archives (GB)											co0976553 (1)
				#		BBC South Archive (GB)												co0795915 (1)
				#		Getty - BBC Archive (GB)											co0942671 (1)
				#
				#		BBC Arts (GB)														co0200731 (17)
				#		BBC Enterprises (GB)												co0104087 (17)
				#		BBC Television Service (GB)											co0649102 (4)
				#		BBC Studios Distribution (GB)										co0775667 (4)
				#		BBC DVD (GB)														co0281995 (3)
				#		BBC Vision Productions (GB)											co0294183 (3)
				#		BBC The Social (GB)													co0675085 (3)
				#		BBC Learning Zone (GB)												co0291731 (3)
				#		BBC Reel (GB)														co0815297 (1)
				#		BBC Light Programme (GB)											co0990658 (1)
				#		BBC Film Network (GB)												co0247569 (1)
				#		BBC Active (GB)														co0669375 (1)
				#		BBC Blast (GB)														co1019605 (1)
				#		BBC Universal (GB)													co0786705 (1)
				#		BBC Outreach (GB)													co0955257 (1)
				#		BBC Ouch! (GB)														co0912517 (1)
				#		BBC Entertainment (PL)												co0492919 (0)
				#		BBC Asian Network (GB)												co0870149 (0)
				#		BBC Crimewatch (GB)													co0797002 (0)
				#		BBC cymru Wales Creative Services (GB)								co0388502 (0)
				#		BBC Content (GB)													co0913252 (0)
				#		BBC National History (GB)											co0780683 (0)
				#		Children's BBC International (GB)									co0178374 (0)
				#
				#		BBC Warner															co0225995 (15)
				#		BBC & Open University (GB)											co0397748 (2)
				#		BBC Opus Arte (GB)													co0106311 (2)
				#		Sony BBC Earth																				3501 (1)			7242
				#		BBC Sales Company (GB)												co0131862 (1)
				#		Naxos of America/BBC Opus (US)										co0094787 (1)
				#		BBC/Paramount Pictures (GB)											co0774810 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyBbc : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'BBC Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'BBC'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'BBC'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'BBC Originals'},
					'expression'	: '(c?bbc[i\d]?|british[\s\-\_\.\+]*broadcasting[\s\-\_\.\+]*corporation)',
				},

				#################################################################################################################################
				# Boomerang
				#
				#	Parent Companies:		Warner Bros Discovery
				#	Sibling Companies:		Cartoon Network, Adult Swim, HBO, The CW, Cinemax, Discovery, TBS, TNT, TCM, TLC, TruTV, many more
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			Boomerang
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Cartoon Network, Adult Swim
				#
				#	Content Provider:		Cartoon Network, Adult Swim
				#	Content Receiver:		Cartoon Network, Adult Swim, HBO, The CW
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(0)						(0)
				#	Networks																(282)					(22)
				#	Vendors																	(0)						(0)
				#	Originals																(11 / 83)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#	Other companies with the same name.
				#
				#		Boomerang Productions (US)											--co0136321-- (1)
				#		Boomerang Film Company (RU)											--co0852964-- (1)
				#		Boomerang Productions (GB)											--co0138255-- (3)
				#		boomerang films (CA)												--co0137409-- (3)
				#		Boomerang Studios (GB)												--co0810289-- (1)
				#		Boomerang Producties (NL)											--co0532000-- (1)
				#		Boomerangfilm														--co0040486-- (3)
				#		Boomerang Productions (FR)											--co0032765-- (17)
				#		Boomerang Original (VE)												--co1073678-- (1)
				#		Boomerang Media.AM (AM)												--co0984122-- (2)
				#		Boomerang Vidéo (FR)												--co0133384-- (1)
				#		Boomerang Studios (IN)												--co0699306-- (1)
				#		Boomerang TV (ES)													--co0185643-- (45)
				#		Studio Boomerang (JP)												--co0156899-- (79)
				#		Boomerang Cine (ES)													--co0254856-- (2)
				#		Boomerang Plus (GB)													--co0304763-- (1)
				#		Boomerang Services (NZ)												--co0235159-- (1)
				#		Boomerang Studios (US)												--co0278173-- (1)
				#		Boomerang Productions Media (US)									--co0411975-- (5)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Boomerang (GB)														co0211390 (59)			2257 (3)			5459
				#		Boomerang Latin America (US)										co0444611 (55)
				#		Boomerang (US)														co0530659 (47)			254 (18)			523
				#		Boomerang (BR)														co0124378 (31)
				#		Boomerang (DE)														co0962875 (27)			3600 (1)			5817
				#		Boomerang (MX)														co1020840 (12)
				#		Boomerang (IT)														co0491815 (11)
				#		Boomerang Germany (DE)												co0333438 (8)
				#		Boomerang (FR)														co0250141 (5)
				#		Boomerang (CA)														co1012356 (2)			3066 (0)			7017
				#		Boomerang (AU)														co0676555 (2)
				#		Boomerang (II) (GB)													co0344625 (2)
				#		Boomerang (FI)														co0919362 (1)
				#		Boomerang (NZ)														co0806729 (1)
				#		Boomerang (RU)														co0679000 (1)
				#		Boomerang (PL)														co0505996 (1)
				#
				#	Some titles belong here, but either other titles have been miscategorized under this company, or this is
				#	a different company with the same name.
				#
				#		Boomerang															--co0062919-- (29)
				#
				#	Other companies with the same name.
				#
				#		Boomerang Distribution (FR)											--co0028395-- (1)
				#		Boomerang Films Inc. (US)											--co0089190-- (2)
				#		Boomerang Classics (BE)												--co0152054-- (1)
				#		Boomerang (TH)														--co1049418-- (1)
				#		Boomerang Pictures (BE)												--co0156082-- (3)
				#		BoomerangStudios (IN)												--co0533902-- (1)
				#		Boomerang Studio (JP)												--co1027166-- (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyBoomerang : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Boomerang'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Boomerang'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Boomerang Originals'},
					'expression'	: '(boomerang)',
				},

				#################################################################################################################################
				# Bravo
				#
				#	There is an unrelated, now defunct, UK Bravo channel.
				#	CTV Drama Channel is the Canadian version of Bravo, also owned by NBCUniversal.
				#
				#	Parent Companies:		Universal (NBCUniversal), Warner (co-owns NZ channel)
				#	Sibling Companies:		Peacock, USA
				#	Content Receiver:		Universal, Warner
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(88)					(8)
				#	Networks																(1000)					(190)
				#	Vendors																	(0)						(0)
				#	Originals																(164 / 270)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Bravo Cable (US)													co0076928 (41)			1920 (4)			66729
				#		Bravo Network Canada																		38665 (7)			66789
				#		Bravo Studios (US)													co0289501 (4)
				#		Bravo! Studios																				157883 (2)			181552
				#		Bravo Original Production (US)										co0208168 (1)			43510 (1)			73473
				#
				#	Other production companies.
				#
				#		Bravo Media (US)													--co0124292-- (9)

				#	Other companies with the same name.
				#
				#		Bravo Productions (US)												--co0564324-- (3)
				#		Bravo Charlie (CA)													--co0664701-- (3)
				#		Bravo Films (US)													--co0084158-- (3)
				#		Bravo Hotel (US)													--co0543777-- (1)
				#		Bravo Studios (ES)													--co0387909-- (1)
				#		Cine Bravo Productions (US)											--co0693540-- (2)
				#		Bravo Kid Productions (US)											--co0650320-- (1)
				#		Echo Bravo Productions (US)											--co0722885-- (1)
				#		Alpha Bravo Studios (GB)											--co0976002-- (1)
				#		Cinema Bravo														--co0026919-- (4)
				#		Uno Bravo (CA)														--co0388938-- (1)
				#		Bravo Communications (NZ)											--co0536256-- (2)
				#		Bravo Film (JP)														--co0568206-- (1)
				#		Bravo Company Entertainment (US)									--co0902279-- (3)
				#		Bravo, Flike! (US)													--co0266820-- (9)
				#		Bravo Fox Films (CA)												--co0172323-- (1)
				#		Bravo Cinematográfica (BR)											--co1013186-- (1)
				#		Bravo Films (RO)													--co0940483-- (2)
				#		Bravo!FACT (Canadian Talent Award) (CA)								--co0546223-- (1)
				#		Bravo Entertainment (IN)											--co0880632-- (1)
				#		Bravo Productions (PH)												--co0355064-- (1)
				#		Bravo Films (MX)													--co0128632-- (3)
				#		Bravo Production (IT)												--co0089300-- (4)
				#		Bravo Films (EE)													--co0751469-- (1)
				#		Bravo Zulu Pictures (NZ)											--co0763935-- (1)
				#		Bravo (IT)															--co1030476-- (1)
				#		Bravo Cinema (MX)													--co0737265-- (1)
				#		Bravo Entertainment (US)											--co0081072-- (1)
				#		BRAVÒ (US)															--co0573271-- (1)
				#		Bravo Anchor Productions (US)										--co0890335-- (1)
				#		Bravo Entertainment Inc. (CN)										--co0517939-- (0)
				#		Bravò (US)															--co0572606-- (1)
				#		Bravo Film Productions												--co0024586-- (10)
				#		BravoEcho Entertainment (US)										--co0645278-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Bravo (US)																					84 (183)			74
				#		bravo (CA)																					117 (7)				485
				#		Bravo (NZ)															co0871340 (2)
				#
				#		Bravo! (US)															co0055388 (170)
				#		Bravo! CTV Limited (CA)												co0321399 (3)
				#		Bravo!FACT (CA)														co0089713 (1)
				#
				#		Bravo TV (AR)														co0913432 (9)
				#		Bravo TV (US)														co0544037 (8)
				#		Bravo TV (AU)														co1005022 (1)
				#
				#		7Bravo (AU)															co0979519 (83)
				#		Bravo Networks (US)													co0044418 (58)
				#		Bravo! Television (CA)												co0093310 (39)
				#		Bravo Network Canada (CA)											co0051348 (28)
				#		Bravo Arts Channel													co0073234 (2)
				#
				#	Not sure if these are the same company.
				#
				#		Bravo North America (US)											--co0762555-- (0)
				#
				#	Other companies with the same name.
				#
				#		Bravo (GB)															--co0104463-- (34)		--1105-- (5)		312
				#		Bravo Television (GB)												--co0106168-- (29)
				#		Bravokids																					--3840-- (1)		7531
				#		Bravo Communications (CA)											--co0089178-- (3)
				#		Bravo Romeo Entertainment (US)										--co0183552-- (1)
				#		Bravo Oscar (GB)													--co0503864-- (1)
				#		Bravo Company Manufacturer, (US)									--co0681567-- (1)
				#		Bravo Ocean Studios (US)											--co0866152-- (2)
				#		Bravò LCC (US)														--co0567123-- (0)
				#		The Bravo Group (US)												--co1027639-- (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyBravo : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Bravo Studios'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Bravo TV'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Bravo'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Bravo Originals'},
					'expression'	: '(^[7]?bravo(?:$|\!|[\s\-\_\.\+]*(?:tv|cable|networks?|studios?|originals?|arts?)))',
				},

				#################################################################################################################################
				# BritBox
				#
				#	Created to digitially distribute BBC and ITV content.
				#	Now also has a large collection of Channel 4 and Channel 5 content.
				#
				#	Parent Companies:		BBC, ITV
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			BritBox
				#
				#	Streaming Services:		BritBox
				#	Collaborating Partners:	BBC, ITV, Channel 4, Channel 5
				#
				#	Content Provider:		-
				#	Content Receiver:		BBC, ITV, Channel 4, Channel 5
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(0)						(0)
				#	Networks																(139)					(17)
				#	Vendors																	(0)						(0)
				#	Originals																(31 / 100)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		BritBox (GB)														co0685539 (90)
				#		BritBox (US)														co0859609 (14)
				#		BritBox																						553 (17)			4025
				#		BritBox International (GB)											co0957541 (6)
				#		BritBox Australia (AU)												co1058884 (1)
				#		BritBox (CA)														co1063503 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyBritbox : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'BritBox'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'BritBox'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'BritBox Originals'},
					'expression'	: '(brit[\s\-\_\.\+]*box)',
				},

				#################################################################################################################################
				# Cartoon Network
				#
				#	Parent Companies:		Warner Bros Discovery
				#	Sibling Companies:		Adult Swim, Boomerang, HBO, The CW, Cinemax, Discovery, TBS, TNT, TCM, TLC, TruTV, many more
				#	Child Companies:		-
				#
				#	Owned Studios:			Cartoon Network Studios
				#	Owned Networks:			Cartoon Network
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Adult Swim
				#
				#	Content Provider:		Adult Swim
				#	Content Receiver:		Adult Swim, HBO, The CW
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(275)					(305)
				#	Networks																(1339)					(252)
				#	Vendors																	(0)						(0)
				#	Originals																(109 / 626)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Cartoon Network Studios (US)										co0238110 (112)			1321 (279)			7899
				#		Cartoon Network Studios Europe (GB)									co0844092 (1)
				#		Cartoon Network Studios Arabia (AE)									co0593002 (1)
				#		Cartoon Network Studios (TR)										co0655772 (0)
				#		Cartoon Network Studios (AE)										co0592194 (0)
				#
				#		Cartoon Network Productions (US)									co1060195 (13)			129704 (18)			176067
				#		Cartoon Network Development Studio Europe (GB)						co0340724 (4)			1329 (11)			67225
				#		Cartoon Network Movies (US)											co0674218 (5)
				#
				#		Cartoon Network India																		40089 (3)			103168
				#		Cartoon Network Asia																		96727 (1)			149061
				#
				#		Cartoon Network Studios/Hanna-Barbera (US)							co0764593 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Cartoon Network (US)												co0005780 (773)			120 (189)			56
				#		Cartoon Network (MX)												co1006606 (316)
				#		Cartoon Network (BR)												co1014644 (32)
				#		Cartoon Network (CA)												co1019493 (30)			3191 (1)			7072
				#		Cartoon Network (DE)												co0967426 (19)
				#		Cartoon Network (GB)												co0967683 (15)			234 (10)			217
				#		Cartoon Network (KR)												co1001745 (15)			2665 (1)			6206
				#		Cartoon Network (SG)												co1010748 (13)
				#		Cartoon Nework (IN)																			1945 (7)			4945
				#		Cartoon Network (JP)												co1065573 (6)			3164 (1)			7109
				#		Cartoon Network (MY)												co1006909 (6)
				#		Cartoon Network (PH)												co0970248 (5)
				#		Cartoon Network																				2979 (4)			6315
				#		Cartoon Network (AU)												co1035369 (1)			1209 (3)			1232
				#		Cartoon Network (TR)												co1060525 (1)			3788 (1)			6033
				#		Cartoon Network (IT)												co1030543 (1)
				#		Cartoon Network (FR)												co1039942 (1)
				#		Cartoon Network (TW)																		1388 (1)			3917
				#		Cartoon Network (ES)												co1048006 (0)			1386 (1)			2193
				#		Cartoon Network																				3008 (1)			6869
				#		Cartoon Network (CA)																		1882 (0)			4700
				#		Cartoon Network (IN)												co1049124 (0)			2518 (0)			5986
				#		Cartoon Network (RU)												co1030544 (0)
				#		Cartoon Network (RO)												co1045413 (0)
				#
				#		Cartoon Network Latin America (AR)									co1015360 (16)			1061 (27)			1483
				#		Cartoon Network Asia																		3204 (2)			7133
				#		Cartoon Network Europe																		1961 (0)			4771
				#		Cartoon Network Türkiye (TR)										co1059342 (0)
				#
				#		CNX (GB)															co0323319 (5)
				#		Cartoon Network Too (GB)											co0252029 (4)
				#		Cartoon Network Anything (MX)																2582 (1)			6018
				#
				#		Cartoonito (GB)														co0445677 (46)			1151 (4)			1261
				#		Cartoonito (US)														co0873854 (15)
				#		Cartoonito (IT)														co0323359 (12)
				#		Cartoonito (DE)														co1008286 (4)
				#		Cartoonito Latin America (AR)										co1025810 (2)
				#		Cartoonito (BR)														co1065574 (1)
				#
				#		Toonami (US)														co0177449 (49)
				#		Toonami Jetstream (US)												co0188542 (12)
				#		Toonami Rewind (US)													co1064907 (3)
				#		Toonami (SG)														co1039856 (2)
				#		Toonami (GB)														co0990387 (1)
				#		Toonami (FR)														co0979463 (1)
				#		Toonami II (GB)														co0727598 (0)
				#		Toonami																						989 (0)				3341
				#
				#		Checkered Past (US)													co1057333 (0)
				#
				#		TNT & Cartoon Network Asia (HK)										co0868070 (0)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Cartoon Network Television (FR)										co1048303 (0)
				#		Cartoon Network Television France (FR)								co1048340 (0)
				#
				#		Cartoon Network Home Entertainment (US)								co0919200 (0)
				#		Cartoon Network Interactive (US)									co0087030 (0)
				#		Cartoon Network Games (US)											co0642967 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyCartoonnet : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Cartoon Network Studios'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Cartoon Network'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Cartoon Network'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Cartoon Network Originals'},
					'expression'	: '(cartoon[\s\-\_\.\+]*net?work|cartoonito|toonami|checkered[\s\-\_\.\+]*past)',
				},

				#################################################################################################################################
				# CBC
				#
				#	Parent Companies:		Canadian Government
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			CBC Films
				#	Owned Networks:			CBC
				#
				#	Streaming Services:		CBC Gem
				#	Collaborating Partners:	Netflix, BBC, The CW
				#
				#	Content Provider:		-
				#	Content Receiver:		Netflix
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(2686)					(384)
				#	Networks																(2940)					(466)
				#	Vendors																	(89)					(0)
				#	Originals																(1089 / 998)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		CBC (CA)															co0045850 (1253)		900 (369)			12113
				#		CBC Documentary Unit (CA)											co0986283 (17)
				#		CBC Arts (CA)														co0801639 (2)
				#		CBC Media (US)														co0193428 (1)
				#		CBC Family Pictures (CA)											co0077499 (1)
				#
				#		CBC Films																					106097 (15)			157741
				#		CBC Film Sales														co0054718 (4)
				#
				#		CBC News															co0004543 (27)
				#		CBC Music (CA)														co0809993 (1)
				#
				#	Other production companies.
				#
				#		CBC News Studios (CA)												--co0921720-- (1)
				#		CBC TV News (CA)													--co0133736-- (12)
				#		CBC Halifax Production Services (CA)								--co0366734-- (5)
				#		CBC Radio (CA)														--co0166315-- (5)
				#		CBC Audio Doc Unit (CA)												--co1046216-- (1)
				#
				#	Other companies with the same name.
				#
				#		CBC Produções Cinematográficas (BR)									--co0084060-- (1)
				#		The CBC (GB)														--co0722179-- (1)
				#		CBC Productions (PH)												--co0274255-- (1)
				#		CBC Cologne Broadcasting Center (DE)								--co0195529-- (1)
				#		CBC Nagoya (JP)														--co0755463-- (1)
				#		CBC (IT)															--co1049806-- (1)
				#		CBC Media Enterprises (US)											--co1048088-- (1)
				#		CBC Creations (IN)													--co1032452-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Canadian Broadcasting Corporation (CBC) (CA)						co0045850 (1253)
				#		CBC (US)															co0274055 (1)
				#		Canadian Broadcast Company																	3881 (0)			3834
				#
				#		CBC Gem (CA)														co0737690 (96)			163 (69)			2981
				#		CBC Television (CA)													co0945984 (9)			97 (401)			23
				#		CBC documentary channel (CA)										co0407617 (21)
				#		CBC Sports (CA)														co0145787 (11)
				#		CBC Enterprises														co0017485 (2)
				#
				#		CBC Comedy (CA)														co0684928 (1)			1747 (2)			2298
				#		Comedy Coup / (CBC) (CA)											co0578570 (1)
				#		CBC Punchline (CA)													co0684927 (1)
				#
				#		CBC Kids (CA)														co0732227 (22)
				#		CBC Learning (CA)													co0256692 (2)
				#
				#		CBC News Network (CA)												co0526683 (33)			1686 (3)			90
				#		CBC Newsworld (CA)													co0018033 (23)
				#		CBC National News (CA)												co0006230 (3)
				#
				#		CBC Radio Canada (CA)												co0365169 (16)
				#		CBC Radio One (CA)													co0849552 (1)
				#
				#	Other companies with the same name.
				#
				#		CBC (JP)																					--416-- (87)		201
				#		CBC (EG)																					--2284-- (24)		2548
				#		CBCDrama (EG)																				--1839-- (13)		1952
				#		C.B.C. Film Sales Corp. (US)										--co0127409-- (17)
				#		CBC (EG)															--co0434338-- (7)
				#		CBC Television (JP)													--co0944868-- (2)
				#		CBC Sport (AZ)														--co1015102-- (1)
				#		CBC (JP)															--co0548202-- (1)
				#		CBC TV 8 (BB)														--co0563460-- (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		CBC Breaking Barriers Film Fund (CA)								co0645943 (15)
				#		CBC International Sales (CA)										co0057201 (9)
				#		CBC Home Video														co0044672 (1)
				#		CBC Educational Sales												co0033534 (1)
				#		CBC Distributing Company (US)										co0804510 (1)
				#
				#		CBC Vancouver (CA)													co0384853 (9)
				#		CBC Atlantic (CA)													co0725740 (1)
				#		CBC Manitoba (CA)													co0689721 (1)
				#		CBC Winnipeg (CA)													co0579073 (1)
				#		CBC North, Kivalliq (CA)											co0727824 (1)
				#		CBC Vancouver Island (CA)											co0294079 (1)
				#		CBC Edmonton (CA)													co0989392 (1)
				#		CBC Toronto (CA)													co0989391 (1)
				#		CBC Ottawa (CBOT) (CA)												co0914225 (1)
				#		CBC Saskatoon (CA)													co0990830 (0)
				#
				#		CBC Weekend AM (CA)													co1065081 (1)
				#		CBC On The Go (CA)													co1065113 (1)
				#		CBC Here and Now (CA)												co1065111 (1)
				#		CBC Records (CA)													co0921956 (1)
				#		Cbc.Ca/bc (CA)														co0849553 (1)
				#
				#		CBC Maritimes (CA)													co0583459 (1)
				#		Land and Sea, CBC (CA)												co0380822 (1)
				#
				#		CBC Central Morning Show (CA)										co1065112 (1)
				#		CBC West Coast Morning Show (CA)									co1064971 (1)
				#
				#		CBC Studio One (CA)													co0296164 (1)
				#		CBC Studio 44 (CA)													co0031756 (1)
				#
				#		CBC - CBNT Archives (CA)											co1066695 (1)
				#		CBC/CTV (CA)														co0922467 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyCbc : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'CBC Studios'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'CBC'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'CBC'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'CBC Originals'},
					'expression'	: '(cbc|canadian[\s\-\_\.\+]*broadcast(?:ing)?[\s\-\_\.\+]*(?:corporation|company))',
				},

				#################################################################################################################################
				# CBS
				#
				#	Although the abriviation is for Columbia Broadcasting System, it does not seem to have anything to do with Columbia Pictures,
				#	except for the occasional collaboration. Fully owned by Paramount since the 1920s.
				#	https://paramount.fandom.com/wiki/CBS_Television_Stations
				#
				#	Owned by:
				#		Current:			Paramount
				#		Previous:			Viacom (merged and renamed to ViacomCBS and later to Paramount Global)
				#
				#	Owner of:
				#		Current:			The CW (partial), Owns 100s of local channels across the US.
				#		Previous:			TriSar (partial)
				#
				#	Collaborations with:
				#		Current:			Nickelodeon, VH1, MTV, Comedy Central, MGM, Fox, NBC, AMC, Warner, Sony, TriSar,
				#							HBO (through TriSar), Viacom18 (previous through TV18)
				#
				#	Content provider to:
				#		Current:			Paramount+, Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1795)					(1127)
				#	Networks																(7634)					(1367)
				#	Vendors																	(2853)					(0)
				#	Originals																(2706 / 1862)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		CBS Studios (US)													co0007821 (178)
				#		CBS Studios (GB)																			173345 (5)			224196
				#
				#		CBS Television Studios (US)											co0274041 (251)			203 (333)			1081
				#		CBS Television Network (US)											co0049888 (132)			77016 (94)			134046
				#		CBS Television Productions (US)										co0787164 (2)
				#
				#		CBS Films (US)														co0047306 (75)			4493 (31)			5490
				#		CBS Theatrical Films												co0123634 (10)			24674 (11)			46410
				#		CBS Films Italiana (IT)												co0112904 (1)
				#
				#		CBS Productions (US)												co0048735 (72)			738 (113)			2161
				#		CBS Productions														co0095142 (3)
				#		CBS UK Productions (GB)												co0883452 (0)
				#
				#		CBS Entertainment Production (US)									co0040329 (27)			33269 (105)			124448
				#		CBS Interactive Entertainment (US)									co0249961 (17)
				#		CBS Entertainment Productions (US)									co0810398 (3)
				#		CBS Interactive (US)												co0857109 (1)
				#
				#		CBS Eye Productions (US)											co0356030 (9)			1744 (5)			68835
				#		CBS Eye Animation Productions (US)									co0719327 (5)			3159 (4)			113625
				#		CBS Eye Too Productions (US)										co0682166 (1)
				#
				#		CBS News Productions (US)											co0090662 (42)			40809 (22)			55052
				#		CBS News Incorperated (US)											co0554468 (1)
				#
				#		Columbia Broadcasting System (CBS)															733 (406)			4898
				#		Columbia Broadcasting System (CBS)															121407 (4)			172280
				#		CBS do Brasil (BR)													co0009808 (1)			19212 (1)			8426
				#		CBS (ZA)															co0885423 (1)
				#
				#		CBS Sports															co0006057 (39)			75125 (12)			110640
				#		CBS Sports Network (US)												co0422485 (24)
				#
				#		CBS Public Affairs (US)												co0174020 (3)			139167 (1)			89509
				#		CBS 1A1 Motion Picture Fund (GB)									co0839930 (2)			100902 (1)			152672
				#		CBS Mobile (US)														co0379901 (2)
				#		CBS Web Originals (US)												co0270636 (1)
				#		CBS Schoolbreak Special Telefilm									co0059861 (1)
				#		CBS Terrytoons (US)													co0026997 (1)
				#		CBSN Originals (US)													co0741478 (1)
				#		CBS Live Experiences (US)											co0489623 (1)
				#
				#		CBS3 Philadelphia (US)												co0512488 (2)
				#		CBS Toronto (CA)													co0119022 (2)
				#		CBS 2 Chicago (US)													co0876845 (1)
				#		CBS 2 New York (US)													co0907180 (1)
				#		CBS12 (US)															co0406924 (1)
				#		CBS Austin (US)														co0822007 (1)
				#		CBS 4 - Denver (US)													co0635749 (1)
				#		CBS4- Denver (US)													co0635748 (0)
				#
				#		CBS Paramount Network Television									co0183875 (47)			168927 (20)			220148
				#		CBS Paramount Television & Belisarius Productions! (US)				co0405466 (1)
				#		CBS Paramount (US)													co0319948 (0)
				#
				#	Also produces content for Amazon, Netflix, and MTV, although most are for Paramount+.
				#	Do not include normal Viacom companies, since Paramount exited Viacom and Viacom is now dysfunct.
				#
				#		ViacomCBS International Studios (GB)								co0817261 (75)
				#		ViacomCBS Digital Studios International (US)						co0796824 (3)
				#		ViacomCBS Entertainment & Youth Studios (US)						co0820546 (0)
				#
				#		Viacom International Studios (VIS) (GB)								--co0792121-- (21)		--126691-- (16)		177200
				#		Viacom International Studios (VIS) (US)								--co0777272-- (6)		--168032-- (1)		219468
				#		Viacom International Studios (VIS) (ES)								--co0986109-- (1)		--129492-- (10)		180175
				#		Viacom International Studios (VIS) (IT)								--co0981944-- (1)
				#		Viacom International Studios (VIS) (MX)								--co1036784-- (0)
				#		Viacom International Studios																--4732-- (15)		125586
				#		Viacom International Studios (VIS) (AR)														--129504-- (6)		180176
				#		Viacom International																		--86385-- (2)		133605
				#
				#		Viacom Productions (US)												--co0059559-- (75)		--392-- (143)		12077
				#		Viacom Digital Studios (US)											--co0711545-- (9)
				#		Viacom New Media (US)												--co0046874-- (5)
				#		Viacom Canada (CA)													--co0014596-- (4)		--8978-- (1)		22211
				#		Viacom 2018 (US)													--co0799268-- (1)
				#		Viacom Music Group (US)												--co0500949-- (1)
				#		Viacom Brand Solutions (DE)											--co0310688-- (1)
				#		Viacom Media Networks Production Development (US)					--co0503634-- (0)
				#
				#		Viacom18 Motion Pictures (IN)										--co0328195-- (93)		--8462-- (114)		6808
				#		Viacom18 Studios (IN)												--co0948947-- (12)
				#		Viacom 18 Motion Pictures (IN)										--co0833681-- (9)
				#
				#	Other production companies.
				#
				#		CBS News (US)														--co0011682-- (90)
				#		CBS Broadcasting (US)												--co0093604-- (39)
				#		CBS Broadcast International											--co0030685-- (9)
				#		CBS Television Stations (US)										--co0214398-- (6)
				#		CBS Enterprises (US)												--co0052263-- (3)
				#		CBS TV Archives (US)												--co0587108-- (2)
				#		CBS Columbia Square, Los Angeles (US)								--co0014579-- (2)
				#		CBSN (US)															--co0524636-- (2)
				#		CBS News Poll (US)													--co0601875-- (1)
				#		CBS/Sony Music (US)													--co0139343-- (1)
				#		CBS Consumer Products (US)											--co0276640-- (1)
				#		ViacomCBS Consumer Products (US)									--co0901286-- (1)
				#		ViacomCBS Benelux (NL)												--co0900215-- (1)
				#		Viacom Consumer Products (US)										--co0091021-- (1)
				#		Viacom Catalyst (US)												--co0698878-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		CBS (US)															co0070627 (3477)		22 (1327)			16
				#		CBS																							2511 (0)			6000
				#		CBS (JP)																					839 (0)				3457
				#		CBS (GR)															co0972197 (0)
				#
				#		CBS All Access (US)													co0598660 (223)			149 (21)			1709
				#		CBS Cable (US)														co0047863 (4)			4001 (1)			7643
				#
				#		CBS Drama (GB)														co0326888 (6)
				#		CBS Drama (RU)																				1226 (0)			3190
				#
				#		CBS Reality (GB)													co0453313 (28)			818 (11)			2528
				#		CBS Reality Polska (PL)												co0877435 (1)
				#
				#		CBS Action (GB)														co0313883 (3)
				#
				#		CBS.com (US)																				1725 (2)			2621
				#
				#		CBSNews.com (US)													co0361334 (1)
				#		CBS News															co0754315 (0)			2477 (3)			5970
				#		CBS News 24/7 (US)																			3736 (0)			7478
				#
				#		Viacom TV (US)																				--1225-- (0)		3189
				#		Viacom Media Networks (US)											--co0501767-- (35)
				#		Viacom International Media Networks (VIMN) (US)						--co0557187-- (24)
				#		Viacom International Media Networks (VIMN) (GB)						--co0623530-- (5)
				#		Viacom International Media Networks Germany (DE)					--co0967236-- (1)
				#
				#		Viacom International (US)											--co0109027-- (60)
				#		Viacom International Asia Pacific (HK)								--co0511913-- (0)
				#
				#		Viacom (US)															--co0077647-- (628)
				#		Viacom18 (IN)														--co0246047-- (159)
				#		Viacom Enterprises													--co0020918-- (29)
				#		Viacom Velocity (US)												--co0668963-- (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		CBSN (US)															co0524636 (2)
				#		CBS News London Bureau (GB)											co0699401 (1)
				#		CBS News Home Video (US)											co0232339 (1)
				#		CBS Evening News (US)												co0643897 (0)
				#
				#		CBS Television Studios (US)											co0274041 (251)
				#		CBS Television Distribution (US)									co0878295 (7)
				#		CBS Television Stations (US)										co0214398 (6)
				#		CBS Television Sales (US)											co0306937 (1)
				#		CBS Television (US)													co1074129 (0)
				#
				#		CBS Video (US)														co0176590 (19)
				#		CBS Video (GR)														co0399026 (10)
				#		CBS Video (GB)														co0121770 (2)
				#
				#		CBS Entertainment (US)												co0225608 (50)
				#		CBS Home Entertainment (US)											co0405556 (20)
				#
				#		CBS Worldwide (US)													co0840165 (1)
				#		CBS Worldwide Inc. (US)												co0017523 (1)
				#
				#		CBS TV Archives (US)												co0587108 (2)
				#		CBS Archive (US)													co1038688 (1)
				#
				#		CBS Media Ventures (US)												co0213710 (160)
				#		CBS Electronics (GR)												co0248464 (148)
				#		CBS DVD (US)														co0266490 (25)
				#		CBS Europa (PL)														co0457912 (24)
				#		CBS Studios International (US)										co0276665 (11)
				#		CBS Local Media (US)												co0361085 (11)
				#		CBS Broadcast International											co0030685 (9)
				#		Columbia Broadcasting System (CBS) (US)								co1047418 (8)
				#		CBS Films Distribution (US)											co0791015 (5)
				#		CBS Catchup Channels (GB)											co1032498 (3)
				#		CBS Films Sales Inc. (US)											co0147772 (3)
				#		CBS Network (IN)													co0842403 (2)
				#		CBS Music Video Enterprises (US)									co0032142 (2)
				#		CBS Eye on People (US)												co0905313 (2)
				#		C.B.S. (CA)															co0172946 (1)
				#		CBS Justice (GB)													co1034107 (1)
				#		CBS Boston (US)														co0493419 (1)
				#		CBS College Sports (US)												co0276655 (1)
				#		CBS Electronics (US)												co0079206 (1)
				#		CBS International (US)												co0093670 (1)
				#		CBS-TV2 (VI)														co0479557 (1)
				#		CBS Owned and Operated Stations (US)								co0434383 (1)
				#		CBS - Telenoticias (US)												co0181494 (1)
				#		CBS/Private 1 (US)													co0116822 (1)
				#		CBS Studio Services (US)											co0528740 (1)
				#		CBS Robbins Catalog (US)											co0282920 (1)
				#		CBS Mornings (US)													co0940354 (1)
				#		CBS Global Distribution Group (US)									co0396072 (0)
				#		CBS Marketing Group (US)											co0214620 (0)
				#		CBS Outernet (US)													co0276644 (0)
				#		CBS Film Sales (US)													co0710679 (0)
				#		Fremantle CBS (US)													co0953815 (0)
				#		CBS Outdoor (US)													co0276671 (0)
				#		CBS Consumer Division (US)											co0638970 (0)
				#		CBS / Landov (US)													co0220929 (0)
				#		CBS. (US)															co0803988 (0)
				#		CBS Group															co0095978 (0)
				#
				#		CBS Television, Studio 50 (US)										co0007214 (2)
				#		CBS Television, Studio 43 (US)										co0024107 (1)
				#		CBS Television City, Studio 31 (US)									co0679175 (1)
				#
				#		CBS 4 WFOR Miami (US)												co0616372 (5)
				#		CBS46-Atlanta (US)													co0622518 (1)
				#		CBS 11 (US)															co0216642 (1)
				#		CBS 4 (US)															co0634761 (1)
				#		CBS 23 (US)															co0672682 (1)
				#		CBS New York City (US)												co1067273 (1)
				#		CBS 47 (US)															co0713727 (0)
				#		CBS4- Denver (US)													co0635748 (0)
				#		CBS4 (US)															co0635516 (0)
				#		CBS Washington (US)													co0868761 (0)
				#
				#		WLNY-TV (CBS) (US)													co0453962 (4)
				#		WCCO Television (CBS) (US)											co0176456 (3)
				#		WCTV (CBS) (US)														co0481698 (1)
				#		KPSP-TV (CBS) (US)													co0795987 (1)
				#		WPEC-TV West Palm Beach (CBS) (US)									co0992782 (1)
				#		WIAT TV CBS Birmingham (US)											co0805424 (1)
				#		KHOU Channel 11, CBS Houston, Tx (US)								co0489870 (1)
				#
				#		CBS/Fox (US)														co0007496 (600)
				#		CBS/Fox (DE)														co0226201 (280)
				#		CBS/Fox (AR)														co0094754 (94)
				#		CBS/Fox (GR)														co0130300 (4)
				#		CBS/Fox (MX)														co0761328 (1)
				#
				#		CBS / Fox Video (GB)												co0106097 (142)
				#		CBS/Fox Video (BE)													co0212901 (82)
				#		CBS / Fox Video (NL)												co0266215 (63)
				#		CBS/Fox Video (US)													co0806725 (43)
				#		CBS/Fox Video (FR)													co0244801 (41)
				#		CBS/Fox Video (JP)													co0223570 (30)
				#		CBS/Fox Video (DE)													co0244996 (14)
				#		CBS/Fox Video (ES)													co0124383 (7)
				#		CBS Fox Video (AU)													co0304538 (6)
				#		CBS/Fox Video (AU)													co0877389 (4)
				#		CBS/Fox Video (IT)													co0680153 (3)
				#		CBS/Fox Video (BR)													co0700002 (2)
				#		CBS/Fox Video (GR)													co0698066 (1)
				#
				#		CBS/Fox Home Video (AU)												co0042311 (865)
				#		CBS/Fox Home Video (NO)												co0599875 (2)
				#		CBS/Fox Home Video (NZ)												co0939093 (1)
				#
				#		Shochiku CBS/Fox Video (SCF) (JP)									co0257036 (23)
				#		Shochiku CBS/Fox Video (JP)											co0670562 (2)
				#
				#		CBS/Fox Video Far East (JP)											co0445889 (21)
				#		CBS/Fox Video Sports (US)											co0481487 (1)
				#		CBS / Fox Video Music (US)											co0400863 (1)
				#		CBS Studios/FOX (US)												co0855511 (0)
				#
				#		MGM/CBS Home Video (US)												co0172646 (51)
				#		Cbs Amc Networks Uk Emea Channels Partnership (GB)					co0794271 (18)
				#		Warner Bros. Television/CBS Studios (US)							co0856617 (0)
				#		NBC/CBS Studios (US)												co1042083 (0)
				#
				#		CBS Sony Group Inc. (JP) 											co0064922 (14)
				#		CBS/Sony Records (JP) 												co0101612 (5)
				#		Movic / CBS Sony Group (JP) 										co0309278 (1)
				#		Sony Pictures Television/CBS (US)									co0927303 (0)
				#
				#		CBS Paramount Domestic Television (US)								co0170466 (84)
				#		CBS Paramount International Television (US)							co0135308 (41)
				#		CBS Studios/Paramount+ (US)											co0865737 (0)
				#
				#		ViacomCBS Global Distribution Group (US)							co0776051 (56)
				#		ViacomCBS Domestic Media Networks (US)								co1072706 (1)
				#		ViacomCBS Streaming (US)											co0870263 (0)
				#
				#		BET Networks/Viacom (US)											--co0176390-- (75)
				#		Viacom Entertainment Group (US)										--co0070713-- (7)
				#		Scratch, Viacom Media Networks (US)									--co0367788-- (1)
				#		Viacom Music Library (US)											--co1043873-- (0)
				#
				#		CBS Records (US)													--co0019083-- (28)
				#		CBS Radio (US)														--co0200107-- (6)
				#		Pasha / CBS Records (US)											--co0307324-- (2)
				#		CBS Music Video (CMV) Enterprises (US)								--co0108327-- (1)
				#		CBS Television Distribution (CTD) Clip Licensing (US)				--co0411671-- (1)
				#		CBS Records (GB)													--co0248486-- (1)
				#		Cbs Recording Academy (US)											--co0999056-- (1)
				#		CBS Recording Studios (GB)											--co0438974-- (1)
				#		CBS SQ/Tate Systems (US)											--co0811181-- (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyCbs : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'CBS Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'CBS'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'CBS'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'CBS Originals'},
					'expression'	: '(cbsn?|columbia[\s\-\_\.\+]*broadcasting[\s\-\_\.\+]*system|viacom[\s\-\_\.\+]*cbs)',
				},

				#################################################################################################################################
				# Channel 4
				#
				#	Created by the UK government to counter the monopoly of BBC.
				#	Is publicly owned, but unlike the BBC, does not receive public funding.
				#	Although a competitor of BBC, does a lot of collaborations with them.
				#
				#	Parent Companies:		UK Government
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Channel Four Films
				#	Owned Networks:			Channel 4, E4, More4
				#
				#	Streaming Services:		BritBox
				#	Collaborating Partners:	BBC, ITV
				#
				#	Content Provider:		-
				#	Content Receiver:		BritBox
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1992)					(1368)
				#	Networks																(2564)					(1429)
				#	Vendors																	(4379)					(0)
				#	Originals																(2611 / 2435)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Channel 4 Television 												co0290683 (337)			1328 (790)			5778
				#		Channel Four Films													co0103532 (295)			3661 (18)			181
				#		Channel Four Film													co0103747 (16)
				#		Channel Four Productions											co0019406 (5)
				#		Channel 4 British Documentary Film Foundation						co0977444 (2)
				#		Channel 4 News														co0674378 (2)
				#		Channel 4 Television Global Format Fund								co0993801 (1)
				#
				#		Film4 (GB)															co0167631 (417)			129465 (5)			180148
				#		FilmFour															co0002948 (92)			52611 (2)			109795
				#		Film Four International												co0000063 (62)			4500 (6)			9210
				#		Film4 Productions (GB)												co0940546 (4)			5512 (534)			6705
				#
				#		E4 Productions														co0391865 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Channel 4															co0706824 (576)			150 (1282)			26
				#		Channel 4 (GB)																				2889 (0)			6635
				#		Channel Four														co0159436 (109)
				#		Channel Four Television												co0007824 (99)
				#
				#		Film4																co0167631 (417)
				#
				#		E4 (GB)																co0106185 (222)			294 (96)			136
				#		E4																							3285 (0)			7207
				#
				#		More4																co0163162 (109)			124 (48)			298
				#		More4																co0523488 (15)
				#
				#		All4 (GB)															co0651210 (152)			718 (12)			1988
				#
				#		The Box																co0557933 (2)
				#		The Box Plus Network												co0691823 (1)
				#
				#		Kerrang!															co0361173 (4)
				#
				#	Was previously added as a vendor, since it contains too much other content.
				#	But "Corporation" here means that it is the parent company of CH4.
				#	Plus there are some CH4 Originals listed only under this company (eg tt2384811, tt5711280, tt4051832, tt2616280, tt2432604).
				#
				#		Channel 4 Television Corporation									co0103528 (1837)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Channel 4 International												co0044785 (30)
				#		Channel 4 DVD														co0235537 (21)
				#		Channel 4 Video														co0106289 (10)
				#		Channel Four International (C4i)									co0200324 (3)
				#		Channel 4 Learning													co0792816 (2)
				#
				#		Film Four Distributors												co0167590 (19)
				#		FilmFour Video														co0108028 (4)
				#
				#		ITN Source / Channel 4												co0412137 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyChannel4 : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Channel 4 Productions'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Channel 4'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Channel 4'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Channel 4 Originals'},
					'expression'	: '((?:channel|film)[\s\-\_\.\+]*(?:4[^\d]|four)|^e4(?:$|[\s\-\_\.\+]*)|more4[^\d]|kerrang|^the[\s\-\_\.\+]*box[\s\-\_\.\+]*(?:$|plus))',
				},

				#################################################################################################################################
				# Channel 5
				#
				#	Was launched as an alternative to BBC and Channel 4.
				#	Public braodcaster, but privatly owned.
				#	However, it does not seem to have that many co-productions with BBC, Channel 4, ITV.
				#
				#	Parent Companies:		Paramount (UK/AU division)
				#	Sibling Companies:		Paramount, CBS
				#	Child Companies:		-
				#
				#	Owned Studios:			Channel 5 Productions
				#	Owned Networks:			Channel 5, 5Star, My5, Five, 5USA, 5Select, 5Action, Fiver, Spike
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Paramount, CBS
				#
				#	Content Provider:		-
				#	Content Receiver:		BritBox
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(12)					(191)
				#	Networks																(2280)					(688)
				#	Vendors																	(84)					(0)
				#	Originals																(740 / 966)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Channel 5																					2995 (185)			27856
				#		Channel 5 Productions (GB)											co0572210 (5)			66981 (7)			111371
				#
				#		5+one Productions (GB)												co0419882 (1)
				#		5 + One Productions (GB)											co0445528 (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Channel 5 (GB)																				409 (667)			99
				#		Channel 5																					2165 (0)			5312
				#		Channel 5																					1999 (0)			5101
				#		Channel 5																					2676 (0)			6255
				#		Channel 5																					3326 (0)			7245
				#
				#		Channel 5 Television (GB)											co0003500 (859)
				#		Channel 5 Video (GB)												co0773190 (42)
				#		Channel Five (GB)													co1040344 (8)
				#		Channel 5 International (GB)										co0106315 (1)
				#		Channel 5 News (GB)													co0797466 (0)
				#
				#		5*																	co0360612 (49)			3593 (2)			7382
				#		5Star (GB)															co0836811 (31)			511 (20)			507
				#		5 Star (GB)															co0594710 (14)
				#		5 Star Broadcasting (GB)											co0732834 (0)
				#
				#		My5																	co0616900 (154)			2205 (9)			5448
				#		My 5 (GB)															co1047381 (0)
				#
				#		Five (GB)															co0174820 (138)
				#		Five Life (GB)														co0187281 (27)
				#		Five US (GB)														co0187155 (24)
				#		Five TV (GB)														co0358510 (1)
				#
				#		5USA (GB)															co0340961 (27)			916 (1)				842
				#		Five US (GB)														co0187155 (24)
				#
				#		5Select (GB)														co0798902 (32)
				#		5Action (GB)														co0901456 (25)			3939 (1)			7588
				#
				#		Fiver (GB)															co0237619 (9)
				#		Spike (GB)															co0533814 (63)			2005 (1)			5122
				#
				#	Other companies with the same name.
				#
				#		Five Star Films Ltd. (GB)											--co0145708-- (3)
				#		Five Films (GB)														--co0106060-- (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Channel 5 Video Distribution (GB)									co0106195 (51)
				#		Five Star Entertainment (GB)										co0242515 (2)
				#
				#################################################################################################################################
				MetaCompany.CompanyChannel5 : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Channel 5 Productions'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Channel 5'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Channel 5'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Channel 5 Originals'},
					'expression'	: '(channel[\s\-\_\.\+]*(?:5|five)|(?:five|5)[\s\-\_\.\+]*(?:\+[\s\-\_\.\+]*one|\*|star|usa?|select|action|spike|life|tv)|my[\s\-\_\.\+]*(?:five|5)|fiver?|spike)',
				},

				#################################################################################################################################
				# Cineflix
				#
				#	Parent Companies:		Cineflix
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Cineflix Productions, Buccaneer Media
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(151)					(61)
				#	Networks																(0)						(0)
				#	Vendors																	(70)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Cineflix Productions (CA)											co0064070 (94)			1654 (61)			32205
				#		Cineflix Productions (GB)											co0344403 (1)
				#
				#		Cineflix Media (CA)													co0376305 (13)
				#		Cineflix Studios (US)												co0317170 (7)
				#		Cineflix International Media (US)									co0658624 (2)
				#
				#		Cineflix (APS) (US)													co0467141 (1)
				#		Cineflix (Flipping Virgins 2) (CA)									co0645818 (0)
				#		Cineflix (Takaya) (CA)												co0765221 (0)
				#		Cineflix (Bizarre) (CA)												co0691772 (0)
				#		Cineflix (Detectives) (CA)											co0647273 (0)
				#		Cineflix (Bikers) (CA)												co0522055 (0)
				#
				#	Other companies with the same name.
				#
				#		CineFlix Films Productions (IN)										--co0994816-- (1)
				#		I-Quick Cineflix (IN)												--co1001879-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Cineflix Rights (GB)												co0182284 (53)
				#		Cineflix International (CA)											co0510368 (5)
				#		cineflix (US)														co0775253 (4)
				#
				#################################################################################################################################
				MetaCompany.CompanyCineflix : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Cineflix Productions'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Cineflix'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(cineflix)',
				},

				#################################################################################################################################
				# Cinemax
				#
				#	Parent Companies:		Warner Bros. Discovery, HBO
				#	Sibling Companies:		HBO
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	HBO, BBC, Sky, Fox
				#
				#	Content Provider:		HBO, Hulu (some)
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(19)					(29)
				#	Networks																(1094)					(37)
				#	Vendors																	(0)						(0)
				#	Originals																(636 / 39) Probably not real Film Originals.
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Cinemax																						3190 (21)			74097
				#		Cinemax Reel Life (US)												co0027725 (9)			41495 (5)			12911
				#		World Cinemax (US)													co0005144 (2)			34297 (3)			48943
				#
				#	Other companies with the same name.
				#
				#		Cinémax (FR)														--co0047270-- (16)		--20167-- (9)		20576
				#		Cinémax (CA)														--co0093399-- (1)
				#		Avni Cinemax (IN)													--co0387796-- (15)
				#		World Cinemax Productions Inc. (US)									--co0147221-- (1)
				#		Cinemax Studios (PH)												--co0266173-- (23)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Cinemax (US)														co0042496 (842)			52 (37)				359
				#		Cinemax (RU)														co0268340 (39)
				#		Cinemax (PL)														co0861398 (19)
				#		Cinemax (CZ)														co0872473 (4)
				#		Cinemax (HU)														co0778313 (3)
				#		Cinemax (RS)														co0625219 (2)
				#		Cinemax (SK)														co0790278 (2)
				#		Cinemax (GR)														co0802222 (1)
				#
				#		HBO/Cinemax Documentary (US)										co0123742 (11)
				#		HBO / Cinemax (US)													co0368145 (7)
				#		Cinemax 2 (PL)														co0913502 (2)
				#		Cinemax Latin America (AR)											co0887358 (1)
				#		Cinemax Documentary Theatrical Presentations						co0011668 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyCinemax : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Cinemax Productions '},
					'network'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'Cinemax'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Cinemax'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'Cinemax Originals'},
					'expression'	: '(cinem[aá]x)',
				},

				#################################################################################################################################
				# Columbia
				#
				#	Member of the "original" Big Five.
				#	Although CBS is "Columbia Broadcasting System", there seem to be little to no relation between Columbia and CBS,
				#	except maybe from the early 1900s, both branched of from Columbia Records?
				#
				#	Parent Companies:		Sony
				#	Sibling Companies:		TriStar Pictures, Screen Gems, Affirm Films
				#	Child Companies:		-
				#
				#	Owned Studios:			Columbia Pictures
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	TriStar Pictures, Screen Gems
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(6247)					(3231)
				#	Networks																(0)						(0)
				#	Vendors																	(10952)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Columbia Pictures													co0050868 (3568)	865 (2821)				5
				#
				#		Columbia Pictures Television										co0041442 (232)		69 (221)				3614
				#		Columbia Pictures Television (CA)									co0198276 (2)
				#		Columbia Pictures Television Trading Company						co0075055 (2)
				#
				#		Columbia Pictures Film Production Asia								co0041248 (19)		13897 (12)				2798
				#		Columbia Pictures do Brasil											co0072216 (4)		26163 (4)				93327
				#		Columbia Pictures Film Production New York (US)						co0985783 (4)
				#		Columbia Pictures Producciones Mexico (MX)							co0136288 (3)		28419 (3)				3928
				#		Columbia Pictures Entertainment (US)								co0446085 (2)
				#		Columbia Pictures Film Production Asia Limited											30269 (2)				76795
				#		Columbia Pictures Corp (IE)											co0772149 (0)
				#		Columbia Pictures Films Productions (FR)							co0206582 (0)
				#
				#		Columbia Records (US)																	10649 (42)				10691
				#		Columbia British Productions (GB)									co0103416 (26)		9766 (14)				16124
				#		Colombia Pictures																		45819 (6)				4154
				#		Columbia Productions												co0063529 (2)
				#		Columbia (IN)														co0324275 (1)
				#		Columbia Films Productions (ES)										co0110462 (1)
				#
				#		Deutsche Columbia Pictures Film Produktion (DE)						co0239725 (18)		13366 (12)				26976
				#		Deutsche Columbia TriStar Filmproduktion (DE)						co0032932 (8)
				#
				#		Columbia TriStar Television (US)									co0074221 (229)		443 (72)				10471
				#		Columbia TriStar																		21614 (12)				177
				#		Columbia TriStar Filmes do Brasil														14283 (8)				77682
				#		Columbia TriStar Children's Television (US)							co0001581 (3)		21402 (1)				23549
				#		Columbia TriStar Carlton TV (GB)									co0624442 (3)
				#		Columbia TriStar TV Productions (FR)								co0147951 (3)
				#		Columbia TriStar Productions (UK) Ltd. (GB)							co0113915 (2)
				#		Columbia TriStar Films (US)											co0113868 (2)
				#		Columbia TriStar Television Pty. Ltd. (AU)							co0142305 (2)
				#		Columbia TriStar Comercio Inter. (Madeira) (PT)						co0008439 (1)
				#		Columbia TriStar Television Productions (UK) Ltd.					co0142304 (1)
				#		Columbia TriStar Entertainment (US)									co0245365 (1)
				#		Columbia TriStar Productions Pty. Ltd. (AU)							co0093452 (1)
				#
				#		Columbia-Delphi Productions											co0562672 (1)		115848 (1)				166898
				#		Columbia-Delphi Productions (US)									co0562672 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Columbia Pictures (US)												co0050868 (3568)
				#		Columbia Pictures (AU)												co0807814 (181)
				#		Columbia Pictures (MX)												co0877032 (64)
				#		Columbia Pictures (JP)												co0897405 (14)
				#		Columbia Pictures (IT)												co0325928 (14)
				#		Columbia Pictures (GB)												co0835295 (1)
				#		Columbia Pictures (ES)												co0996230 (1)
				#		Columbia Pictures (DE)												co0929000 (0)
				#		Columbia Pictures (NZ)												co0806647 (0)
				#
				#		Columbia Pictures of Canada (CA)									co0130303 (1329)
				#		Columbia Pictures of Argentina (AR)									co0221123 (620)
				#		Columbia Pictures de Cuba (CU)										co0218288 (432)
				#		Columbia Pictures do Brasil (BR)									co0014351 (355)
				#		Columbia Pictures of Panama (PA)									co0218192 (219)
				#		Columbia Pictures of Chile (CL)										co0231770 (137)
				#		Columbia Pictures of Peru (PE)										co0218290 (114)
				#		Columbia Pictures Mexico (MX)										co0115734 (29)
				#		Columbia Pictures of Philippines (PH)								co0215095 (14)
				#		Columbia Pictures. (IE)												co0770848 (0)
				#		Columbia Pictures Near East (EG)									co0219416 (0)
				#
				#		Columbia Pictures Home Entertainment (US)							co0051419 (36)
				#		Columbia Pictures Home Entertainment (MX)							co0778447 (5)
				#
				#		Columbia Pictures Home Video (US)									co0032747 (33)
				#		Columbia Pictures Home Video (MX)									co0751516 (6)
				#
				#		Columbia Pictures Corporation (GB)									co0108852 (1822)
				#		Columbia Pictures Corporation (IE)									co0659417 (0)
				#
				#		Columbia Pictures Proprietary (AU)									co0215212 (630)
				#		Columbia Pictures Industries (US)									co0055524 (61)
				#		Columbia Pictures Video Ltd. (GB)									co0118300 (3)
				#		Columbia Pictures Entertainment Inc. (US)							co0054490 (2)
				#
				#		Columbia (FR)														co0076384 (50)
				#		Columbia (NL)														co0488192 (21)
				#		Columbia (AR)														co0400389 (19)
				#		Columbia (BE)														co0178866 (14)
				#		Columbia (DE)														co0185878 (4)
				#		Columbia (US)														co0200952 (2)
				#		Columbia (IT)														co1041459 (2)
				#
				#		Columbia Film (SE)													co0219440 (505)
				#		Columbia Film (DK)													co0229304 (3)
				#		Columbia Film (AT)													co0301411 (2)
				#		Columbia Film (AR)													co0797841 (1)
				#		Columbia Film (US)													co0213635 (0)
				#		Columbia Film (FI)													co0206425 (0)
				#
				#		Columbia Films (FR)													co0031545 (152)
				#		Columbia Films (JP)													co0215270 (108)
				#		Columbia Films (BE)													co0139447 (66)
				#		Columbia Films (FI)													co0176177 (33)
				#		Columbia Films (ES)													co0092245 (21)
				#		Columbia Films (HK)													co0717323 (4)
				#		Columbia Films (DE)													co0250208 (4)
				#		Columbia Films (US)													co0213673 (3)
				#		Columbia Films (DK)													co0300278 (2)
				#		Columbia Films (NL)													co0692171 (0)
				#		Columbia Films (MX)													co0221049 (0)
				#		Columbia Films (SE)													co0455563 (0)
				#
				#		Columbia Films S. A. (MX)											co0282638 (935)
				#		Columbia Film Aktieselskap (DK)										co0237854 (119)
				#		Columbia Films of India (IN)										co0215257 (93)
				#		Columbia Film A. B. (SE)											co0805428 (86)
				#		Columbia Filmes (PT)												co0108003 (75)
				#		Columbia Films. S.A. (FR)											co1013825 (22)
				#		Columbia Films S.A.B. (BE)											co0837462 (4)
				#		Columbia Films, S.A. (ES)											co0796316 (4)
				#		Columbia Films. (BE)												co0937939 (3)
				#		Columbia Filmes (BR)												co0053661 (2)
				#		Columbia Films. (FR)												co0937938 (2)
				#		Columbia Film A. S. (DK)											co0232073 (2)
				#		Columbia Fims (BE)													co0296648 (1)
				#
				#		Columbia Films of China. (CN)										co0771804 (0)
				#		Columbia Films of China (CN)										co0215137 (0)
				#
				#		Columbia Film-Verleih (DE)											co0095798 (204)
				#		Columbia Film-Verleih (AT)											co0257569 (49)
				#
				#		Columbia Filmgesellschaft (AT)										co0118302 (3)
				#		Columbia Filmgesellschaft (DE)										co0930442 (2)
				#
				#		Columbia Pictures Television Distribution (US)						co0232238 (42)
				#		Columbia Pictures Television Trading Company						co0075055 (2)
				#		Columbia Pictures TV (US)											co1044199 (1)
				#		Columbia Television (US)											co0040618 (1)
				#
				#		Columbia International Films (NL)									co0302174 (139)
				#		Columbia Internacional (MX)											co0289892 (1)
				#
				#		Columbia House (US)													co0008806 (7)
				#		Columbia House Video (US)											co0492268 (1)
				#
				#		Columbia Classics (US)												co0274904 (1)
				#		Columbia Pictures Screen Classics (US)								co0660474 (0)
				#
				#		Columbia C.E.I.A.D. (IT)											co0092241 (123)
				#		Columbia-Kamera (NO)												co0651764 (33)
				#		Columbia Home Video (BR)											co0081792 (9)
				#		Columbia Home Entertainment (GB)									co0455564 (2)
				#		Columbia Video (US)													co0924447 (1)
				#
				#		Columbia TriStar Home Entertainment (DE)							co0127120 (537)
				#		Columbia TriStar Home Entertainment (US)							co0098048 (321)
				#		Columbia TriStar Home Entertainment (NL)							co0213457 (308)
				#		Columbia TriStar Home Entertainment (BR)							co0170439 (139)
				#		Columbia TriStar Home Entertainment (GB)							co0182605 (126)
				#		Columbia TriStar Home Entertainment (CA)							co0225408 (57)
				#		Columbia TriStar Home Entertainment (AU)							co0638112 (50)
				#		Columbia TriStar Home Entertainment (MX)							co0720168 (35)
				#		Columbia TriStar Home Entertainment (ES)							co0393411 (32)
				#		Columbia TriStar Home Entertainment (IT)							co0115429 (28)
				#		Columbia TriStar Home Entertainment (DK)							co0754056 (8)
				#		Columbia TriStar Home Entertainment (SE)							co0373110 (12)
				#		Columbia TriStar Home Entertainment (HK)							co0625795 (2)
				#		Columbia TriStar Home Entertainment (CH)							co0919176 (2)
				#		Columbia TriStar Home Entertainment (FI)							co0753593 (2)
				#		Columbia Tristar Home Entertainment (NL)							co0919014 (2)
				#		Columbia Tristar Home Entertainment (DK)							co0919019 (1)
				#		Columbia TriStar Home Entertainment (NU)							co0919175 (1)
				#		Columbia Tristar Home Entertainment (SE)							co0919013 (1)
				#		Columbia TriStar Home Entertainment (KR)							co0853923 (1)
				#		Columbia TriStar Home Entertainment (JP)							co0793712 (1)
				#		Columbia Tristar Home Entertainment (NU)							co0919015 (1)
				#		Columbia Tristar Home Entertainment (AU)							co0919016 (1)
				#		Columbia TriStar Home Entertainment / Aurum (ES)					co0833779 (1)
				#
				#		Columbia TriStar Home Video (US)									co0001850 (1518)
				#		Columbia TriStar Home Video (NL)									co0189864 (349)
				#		Columbia TriStar Home Video (AU)									co0045926 (238)
				#		Columbia TriStar Home Video (GB)									co0942170 (30)
				#		Columbia TriStar Home Video (MX)									co0751613 (30)
				#		Columbia TriStar Home Video (DE)									co0942169 (22)
				#		Columbia TriStar Home Vidéo (FR)									co0954396 (9)
				#		Columbia TriStar Home Video (CA)									co1020466 (6)
				#		Columbia TriStar Home Video (PL)									co0723390 (3)
				#		Columbia TriStar Home Video (DK)									co0826726 (3)
				#		Columbia TriStar Home Video (BE)									co0120629 (2)
				#		Columbia TriStar Home Video (IT)									co1042290 (2)
				#		Columbia Tri-Star Home Video (IT)									co0943399 (1)
				#		Columbia TriStar Home Video (HK)									co0337735 (0)
				#
				#		Columbia TriStar Films (FR)											co0077851 (318)
				#		Columbia TriStar Films (NL)											co0003949 (241)
				#		Columbia TriStar Films (GB)											co0613324 (115)
				#		Columbia TriStar Films (ES)											co0037988 (46)
				#		Columbia TriStar Films (MX)											co0152638 (45)
				#		Columbia Tristar Films (KR)											co0884352 (36)
				#		Columbia TriStar Films (NZ)											co0057970 (13)
				#		Columbia TriStar Films (KR)											co0382360 (7)
				#		Columbia TriStar Films (NO)											co0982368 (7)
				#		Columbia TriStar Films (BE)											co1002119 (5)
				#		Columbia TriStar Films (TW)											co0802980 (3)
				#		Columbia TriStar Films (DK)											co0628032 (4)
				#		Columbia TriStar Films (VE)											co0428560 (4)
				#		Columbia Tristar Films (PT)											co0960786 (2)
				#		Columbia Tristar Films (AU)											co0960788 (2)
				#		Columbia Tristar Films (FI)											co0137852 (0)
				#		Columbia Tristar Films (IS)											co0960785 (0)
				#
				#		Columbia TriStar Films de Argentina (AR)							co0003581 (523)
				#		Columbia TriStar Films de España (ES)								co0057443 (268)
				#		Columbia TriStar Films AB (SE)										co0005726 (221)
				#		Columbia TriStar Film (DE)											co0060005 (199)
				#		Columbia Tristar Films of India (IN)								co0774471 (142)
				#		Columbia TriStar Film (IT)											co0006448 (132)
				#		Columbia TriStar Film (NO)											co0728184 (67)
				#		Columbia TriStar Film (SE)											co0539852 (61)
				#		Columbia TriStar Films Pty. Ltd. (AU)								co0015669 (42)
				#		Columbia TriStar Films Italia (IT)									co0815627 (23)
				#		Columbia TriStar Film (JP)											co0382315 (21)
				#		Columbia TriStar Film (AU)											co0379792 (10)
				#		Columbia TriStar Films of Germany (DE)								co0379620 (6)
				#		Columbia TriStar Film Mexico (MX)									co0382011 (1)
				#		Columbia Tristar Film (HU)											co0960784 (0)
				#		Columbia TriStar Filmes do Brasil (BR)								co0004899 (0)
				#		Columbia TrSstar Films (HK)											co0981289 (1)
				#
				#		Columbia TriStar Film Distributors (GB)								co0047778 (119)
				#		Columbia TriStar Film Distributors (HK)								co0802979 (1)
				#
				#		Columbia TriStar Film Distributors Inter. (SG)						co0135318 (32)
				#		Columbia TriStar Film Distributors Inter. (US)						co0045347 (28)
				#		Columbia TriStar Film Distributors Inter. (ID)						co0613216 (4)
				#
				#		Columbia TriStar Domestic Television (US)							co0009297 (371)
				#		Columbia Tristar Television Distribution (US)						co0287692 (53)
				#		Columbia TriStar International Television (US)						co0163983 (21)
				#
				#		Columbia TriStar Egmont Film Distributors (FI)						co0035705 (88)
				#		Columbia TriStar Nordisk Film Distributors A/S (NO)					co0094232 (54)
				#		Columbia TriStar Nordisk Film Distributors (FI)						co0114725 (50)
				#		Columbia Tri-Star Films (BE)										co0700140 (11)
				#		Columbia Tri Star (MX)												co0890192 (2)
				#		Columbia TriStar / Kinekor (ZA)										co0210948 (1)
				#		Columbia Tristar Motion Picture Group (US)							co0209928 (0)
				#
				#		RCA/Columbia Pictures International Video (DE)						co0128198 (552)
				#		RCA/Columbia Pictures Home Video (US)								co0070977 (542)
				#		RCA / Columbia Pictures Video (GB)									co0117455 (152)
				#		RCA/Columbia Pictures Video (JP)									co0252452 (140)
				#		RCA/Columbia Pictures International Video (NL)						co0358260 (138)
				#		RCA/Columbia Pictures Video (NL)									co0351835 (63)
				#		RCA/Columbia Pictures International Video (GB)						co0359121 (59)
				#		RCA/Columbia Pictures International (IT)							co0113976 (27)
				#		RCA/Columbia Pictures Home Video (ES)								co0117466 (26)
				#		RCA/Columbia Pictures International Video (BE)						co0211796 (19)
				#		RCA/Columbia Pictures International Video (AR)						co0371171 (5)
				#		RCA/Columbia Pictures International Video (IT)						co0728653 (4)
				#		RCA / Columbia Pictures International Video (US)					co0208202 (3)
				#		RCA/Columbia Pictures International Video (JP)						co0793829 (2)
				#		RCA/Columbia Pictures International Video (SE)						co1061942 (1)
				#		RCA/Columbia Pictures International Video (AU)						co0787177 (1)
				#		RCA/Columbia Pictures International Video (ES)						co0913591 (1)
				#		LK-TEL RCA/Columbia Pictures Home Video (BR)						co0517926 (1)
				#
				#		Warner-Columbia Film (SE)											co0214905 (385)
				#		Columbia-EMI-Warner (GB)											co0106070 (266)
				#		Columbia-Warner Distributors (GB)									co0110090 (258)
				#		Columbia-Warner Filmes de Portugal (PT)								co0438107 (228)
				#		Warner-Columbia Films (AR)											co0372744 (222)
				#		Warner-Columbia Filmverleih (DE)									co0118308 (218)
				#		Columbia TriStar Warner Filmes de Portugal (PT)						co0075764 (179)
				#		Warner-Columbia Film (FR)											co0053539 (160)
				#		Warner-Columbia Films (FI)											co0176140 (125)
				#		Columbia-Cannon-Warner (GB)											co0120631 (67)
				#		Warner-Columbia (AT)												co0108012 (36)
				#		Warner Bros. / Columbia Pictures (FI)								co0185616 (18)
				#		Warner Columbia Film (BE)											co0162942 (14)
				#		Warner Columbia Film (BE)											co0162942 (14)
				#		Warner-Columbia (NL)												co0991324 (10)
				#		Warner-Columbia (BE)												co0537026 (7)
				#		Warner-Columbia Film (PT)											co0730604 (5)
				#		Columbia-Warner Distributors (FR)									co0825783 (5)
				#		Columbia-Warner Films (BR)											co0840651 (1)
				#		Warner-Columbia Films (ES)											co0544343 (1)
				#		Columbia-Warner Distributiors (FR)									co0793828 (0)
				#		Warner-Columbia (IT)												co0453812 (0)
				#		Columbia-Warner Distributiors (FR)									co0793828 (0)
				#
				#		Fox Columbia TriStar Films (AU)										co0628925 (175)
				#		Fox Columbia Film Distributors (AU)									co0629458 (131)
				#		Columbia-Fox (GR)													co0025186 (13)
				#		Columbia-Fox (DK)													co0628924 (5)
				#		Columbia TriStar Fox Films (NL)										co1021830 (2)
				#
				#		Buenavista Columbia Tri Star Films de Mexico						co0039725 (30)
				#		Columbia TriStar Buena Vista Filmes. do Brasil (BR)					co0241443 (13)
				#		Buena Vista Columbia TriStar Films (MY)								co1037590 (1)
				#
				#		Gaumont/Columbia TriStar Home Video (FR)							co0108034 (229)
				#		Gaumont-Columbia-RCA (GCR) (FR)										co0159180 (81)
				#		Gaumont/Columbia TriStar Films (FR)									co0135317 (56)
				#
				#		RCA/Columbia-Hoyts Home Video (AU)									co0057923 (1150)
				#		Hoyts Fox Columbia TriStar Films (AU)								co0768357 (152)
				#		Columbia TriStar Hoyts Home Video (AU)								co0768425 (52)
				#		Hoyts Columbia Tristar Films (AU)									co0961122 (3)
				#		RCA Columbia Pictures Hoyts Video (AU)								co0303509 (2)
				#
				#		Columbia-Bavaria Filmgesellschaft m.b.H. (DE)						co0089682 (121)
				#		British Lion-Columbia Distributors (BLC) (GB)						co0139446 (23)
				#		Ese Films Columbia Films S.A.										co0073559 (2)
				#		Cinemark Columbia (LT)												co0354514 (2)
				#		UA-Columbia (US)													co0543768 (1)
				#		Ifisa Columbia Films S.A.											co0011801 (1)
				#		Universal - Columbia TriStar Home Entertainment (FI)				co0201367 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyColumbia : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Columbia Pictures'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Columbia'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(columbia[\s\-\_\.\+]*(?:tr[is][\s\-\_\.\+]*star|picture|fil?m|studio|television|tv|animation|home|video|entertainment|network|distribut|production|global|interna[ct]ional|domestic|house|classic|record|[ck]amera|c\.?e\.?i\.?a\.?d|bavaria|rca|warner|fox|emi|cannon|delphi|hoyts|british|$))',
				},

				#################################################################################################################################
				# Comedy Central
				#
				#	Parent Companies:		Paramount (through MTV), Warner (previous)
				#	Sibling Companies:		MTV, Nickelodeon, CBS, The CW, Showtime, VH1, BET, TMC, Pop TV
				#	Child Companies:		-
				#
				#	Owned Studios:			Comedy Central Films
				#	Owned Networks:			Comedy Central
				#
				#	Streaming Services:		Paramount+, Philo
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		Paramount+, Philo, Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(56)					(158)
				#	Networks																(1442)					(266)
				#	Vendors																	(13)					(0)
				#	Originals																(183 / 527)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Comedy Central																				1663 (149)			1538
				#		Comedy Central Films (US)											co0116486 (14)			5444 (10)			7480
				#		Comedy Central Productions (US)										co0239378 (9)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Comedy Central (US)													co0029768 (674)			45 (174)			47
				#		Comedy Central (GB)													co0811133 (25)			649 (25)			1087
				#		Comedy Central (DE)													co0903459 (24)			2065 (3)			2436
				#		Comedy Central (ES)													co0886579 (5)			1117 (4)			278
				#		Comedy Central (HU)													co0877841 (4)			1313 (3)			1226
				#		Comedy Central (PL)													co0913861 (2)			2626 (3)			6168
				#		Comedy Central (IL)													co0947125 (2)			2492 (1)			5847
				#		Comedy Central (BR)													co0810091 (1)			604 (7)				3082
				#		Comedy Central (AU)																			1528 (6)			2988
				#		Comedy Central (RO)																			1728 (1)			2178
				#		Comedy Central (DK)																			3981 (1)			4535
				#		Comedy Central (NL)													co1010895 (1)			950 (1)				3575
				#		Comedy Central (CH)													co0903461 (1)
				#		Comedy Central (AT)													co0903460 (1)
				#		Comedy Central (MX)													co1073642 (1)
				#		Comedy Central																				2757 (0)			6207
				#
				#		Comedy Central Extra (HU)											co0409231 (11)
				#		Comedy Central Extra (NL)											co0360149 (7)
				#
				#		Comedy Central Deutschland (DE)										co0226227 (46)
				#		Comedy Central+1 (DE)												co0984705 (4)
				#		Comedy Central Africa (ZA)											co0393953 (3)
				#		Comedy Central Latinoamérica																2096 (3)			5066
				#		Comedy Central Family (NL)											co0476675 (2)
				#
				#		The Comedy Network (CA)												co0076380 (56)			903 (21)			51
				#		The Comedy Network													co0003869 (29)
				#		Comedy Network (CA)													co0049249 (16)
				#		The Comedy Channel (AU)																		841 (13)			102
				#		Comedy Channel (US)													co0047312 (7)
				#		Ha! TV Comedy Network (US)											co0387083 (5)
				#		Ha! (US)															co0131848 (4)
				#		CTV Comedy Channel (CA)												co0768658 (3)			1573 (2)			4226
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Comedy Central Records (US)											co0308378 (2)
				#		Comedy Central Design Group (US)									co0401415 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyComedycen : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Comedy Central Productions'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Comedy Central'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Comedy Central'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Comedy Central Originals'},
					'expression'	: '(comedy[\s\-\_\.\+]*(?:central|channel|network)|ha!)',
				},

				#################################################################################################################################
				# Constantin
				#
				#	Parent Companies:		Highlight Communications
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Rat Pack Filmproduktion (not the same as RatPac Entertainment)
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		Netflix, Amazon, others
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1775)					(342)
				#	Networks																(0)						(0)
				#	Vendors																	(2059)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Constantin Film (DE)												co0002257 (1524)		1829 (300)			47
				#		Constantin Film (US)												co0886172 (1)
				#		Constantin Film International (DE)									co0368853 (4)
				#
				#		Constantin Entertainment (DE)										co0117695 (88)			44700 (19)			80748
				#		Constantin Entertainment Polska (PL)								co0756918 (11)
				#		Constantin Entertainment Hellas (GR)								co0401773 (8)
				#		Constantin Entertainment Croatia (HR)								co0675006 (5)
				#		Constantin Entertainment (RS)										co0676507 (4)
				#		Constantin Entertainment (HU)										co0501831 (2)
				#		Constantin Entertainment Israel (IL)								co0435989 (1)
				#
				#		Constantin Television (DE)											co0276919 (17)			1579 (23)			114791
				#		Constantin Dokumentation (DE)										co0942297 (2)			151477 (3)			203051
				#		Constantin Animation (DE)											co0975833 (0)
				#		Constantin Cartoon (DE)												co0866740 (0)
				#
				#	Other production companies.
				#
				#		Constantin Film Services (DE)										--co0785324-- (5)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Constantin Film (DE)												co0002257 (1524)
				#		Constantin-Film (AT)												co0080484 (562)
				#		Constantin Film (DK)												co1005885 (4)
				#		Constantin Film Ltd. (GB)											co0167676 (0)
				#		Constantin Film USA (US)											co0883893 (0)
				#
				#		Constantin Film Verleih (DE)										co0504319 (77)
				#		Constantin Film-Holding GmbH (AT)									co0962732 (1)
				#		Constantin Film Development Inc.									co0094921 (0)
				#
				#		Constantin Video (DE)												co0233657 (77)
				#		Constantin Home Entertainment (DE)									co0895098 (3)
				#		Neue Constantin Film (AT)											co0244344 (2)
				#		Constantin Distribution (DK)										co1053231 (1)
				#		Austria Constantin (DE)												co0995200 (1)
				#		Constantin (DK)														co0837068 (1)
				#		Constantin Network (DE)												co0877579 (0)
				#
				#		Warner-Constantin (DK)												co0179125 (6)
				#
				#################################################################################################################################
				MetaCompany.CompanyConstantin : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Constantin Film'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Constantin'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(constantin)',
				},

				#################################################################################################################################
				# Crave
				#
				#	Formerly known as The Movie Network (TMN).
				#	Provides HBO and Starz content in Canada.
				#
				#	Parent Companies:		Bell Media
				#	Sibling Companies:		HBO, Showtime, Starz
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			Crave, TMN
				#
				#	Streaming Services:		Crave
				#	Collaborating Partners:	-
				#
				#	Content Provider:		HBO, Showtime, Starz
				#	Content Receiver:		Bell
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(38)					(85)
				#	Networks																(378)					(83)
				#	Vendors																	(1)						(0)
				#	Originals																(212 / 48)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Crave (CA)																					106096 (27)			157740
				#		Crave (US)															co0734142 (1)
				#
				#		The Movie Network (CA)												co0243465 (32)			4785 (58)			808
				#
				#	Other companies with the same name.
				#
				#		CraveOnline (US)													--co0303237-- (8)
				#		Craven Street (GB)													--co0439978-- (7)
				#		Crave Films (US)													--co0146364-- (6)
				#		Crave Works (KR)													--co0751031-- (4)
				#		Crave Pictures (ZA)													--co0511879-- (3)
				#		Crave Art (IN)														--co0997361-- (1)
				#		Craven Studios (CA)													--co0193508-- (1)
				#		CraveOnline.com (US)												--co0387680-- (1)
				#		Crave Media (US)													--co0699731-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Crave (CA)																co0605105 (95)
				#		Crave																						3652 (0)			7411
				#		CraveTV (CA)																				401 (69)			1344
				#
				#		The Movie Network (TMN) (CA)											co0043355 (180)		935 (14)			245
				#		TMN GO (CA)																co0667174 (4)
				#		TMN, Government of Quebec - Super Channel (CA)							co0584469 (1)
				#		The Cult Movie Network (CA)												co0758813 (1)
				#
				#	Other companies with the same name.
				#
				#		The Movie Network (AU)													--co0062928-- (10)
				#		The Movie Network Channels (AU)											--co0221567-- (10)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Crave Entertainment (US)												co0047549 (1)
				#
				#		TMN/Movie Entertainment Magazine (CA)									co0493530 (1)
				#		The Movie Network a Division of Bell Media (CA)							co0611544 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyCrave : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Crave Productions'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Crave'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Crave'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Crave Originals'},
					'expression'	: '(crave|tmn|the[\s\-\_\.\+]*(?:cult[\s\-\_\.\+]*)?movie[\s\-\_\.\+]*network)',
				},

				#################################################################################################################################
				# Crunchyroll																IMDb					Trakt				TMDb
				#
				#	Studios																	(689)					(95)
				#	Networks																(717)					(16)
				#	Vendors																	(51)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Crunchyroll															co0251163 (621)			15770 (74)			98553
				#		Crunchyroll (US)																			147379 (30)			198847
				#		Crunchyroll Studios (US)																	155485 (4)			198849
				#		Crunchyroll Production France (FR)									co0997614 (1)
				#
				#		Ellation Studios (US)												co0873834 (2)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Crunchyroll (US)													co0251163 (621)
				#		Crunchyroll (DE)													co0931273 (149)
				#		Crunchyroll (FR)													co0977033 (39)
				#		Crunchyroll																					502 (16)			1112
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Right Stuf International (US)										co0114007 (38)
				#		Right Stuf Home Video (US)											co0316684 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyCrunchyroll : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Crunchyroll Studios'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Crunchyroll'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Crunchyroll'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Crunchyroll Originals'},
					'expression'	: '(crunchy[\s\-\_\.\+]*roll|ellation|right[\s\-\_\.\+]*stuf)',
				},

				#################################################################################################################################
				# The CW
				#
				#	Joint venture between CBS and Warner.
				#	Replaces the old "The WB".
				#
				#	Parent Companies:		CBS (Paramount), Warner Bros
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(0)						(0)
				#	Networks																(897)					(186)
				#	Vendors																	(40)					(0)
				#	Originals																(91 / 229)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#	Other companies with the same name.
				#
				#		CW Studios (US)														--co0394796-- (8)
				#		Mac-Tin CW Productions (US)											--co0525737-- (4)
				#		CW Syndicate (US)													--co0316472-- (1)
				#		C.W. Studios (US)													--co1058261-- (1)
				#		CW Films (AR)														--co0612491-- (1)
				#		CW Productions (II) (US)											--co0094852-- (0)
				#		C.W. Entertainment Company (US)										--co0183874-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		The CW (US)															co0174148 (377)			18 (169)			71
				#		CW (US)																						3377 (0)			7268
				#		CW Network (CW) (US)												co1049674 (1)
				#
				#		CW Seed (US)														co0481314 (16)			640 (12)			1049
				#		Vortexx CW (US)														co1024509 (17)
				#		The CW4Kids (US)													co0786540 (7)
				#		The CW Plus (US)													co0371051 (2)
				#		The Duluth CW (US)													co0664978 (1)
				#
				#		CWtv.com (US)														co0509842 (1)
				#		CW TV (US)															co0369245 (1)
				#
				#		WTCG TV (US)														co0767441 (2)
				#
				#		WPIX (US)															co0000647 (107)			1762 (2)			2169
				#		WPIX-TV (US)														co0374263 (14)
				#		WPIX Channel 11 (US)												co0523775 (11)
				#
				#		KTLA (US)															co0007077 (101)			843 (4)				134
				#		KTLA																						3970 (1)			7599
				#		KTLA-TV (US)														co0378383 (13)
				#
				#	Other companies with the same name.
				#
				#		CW Theatres (US)													--co0708235-- (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		The CW69 (US)														co0469845 (2)
				#		CW 11																co0221492 (2)
				#		Cw 17 (US)															co0402268 (1)
				#		CW 4 (US)															co0710892 (1)
				#		CW 6 (US)															co0725543 (1)
				#		CW59 (US)															co0652452 (1)
				#		CW 2 News (US)														co0672687 (1)
				#		CW 31 Films (US)													co0664164 (0)
				#
				#		CW Cape Fear (US)													co0615111 (1)
				#		CW Austin (US)														co0217572 (1)
				#		CW Columbus (US)													co0391210 (1)
				#
				#		WKBD CW50 Detroit (US)												co0547811 (3)
				#		WCWG (Triad CW) (US)												co0832948 (1)
				#		WBCB - CW Affiliate (US)											co0357335 (1)
				#		KIAH - CW 39 Houston (US)											co0826832 (0)
				#		KVCW (US)																					945 (0)				2693
				#
				#		Nexstar-WPIX, New York (US)											co0964315 (1)
				#		Pix11 News, New York (US)											co0800524 (1)
				#		Pix11 (US)															co0793958 (1)
				#
				#		KTLA News LA (US)													co0432088 (2)
				#		KTLA Channel 5, Los Angeles, California (US)						co0593960 (5)
				#
				#################################################################################################################################
				MetaCompany.CompanyCw : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'The CW'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'The CW'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'The CW Originals'},
					'expression'	: '((?:the)?[\s\-\_\.\+]*cw(?:tv|\d+)?|wpix|pix[\s\-\_\.\+]*11|ktla|kvcw|wcwg)',
				},

				#################################################################################################################################
				# Dark Horse Comics
				#
				#	Third biggest comic producer, after Marvel and DC Comics.
				#
				#	Parent Companies:		Embracer Group
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Dark Horse Entertainment, Dark Horse Indie
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(76)					(36)
				#	Networks																(0)						(0)
				#	Vendors																	(0)						(0)
				#	Originals																(33 / 12)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Dark Horse Entertainment (US)										co0020061 (70)		696 (33)			552
				#		Dark Horse Indie (US)												co0166969 (3)		61823 (3)			4574
				#
				#	Other production company, like "Thank You".
				#
				#		Dark Horse Comics (US)												--co0234569-- (8)
				#
				#	Not sure if it is the same company, probably not.
				#
				#		Dark Horse Productions and Entertainment (US)						--co0942987-- (3)
				#		Dark Horse Productions and Entertainment (US)						--co0942987-- (3)
				#		Dark Horse Studios (US)												--co0757949-- (1)
				#		Dark Horse Pictures (II) (US)										--co0244622-- (0)
				#		Dark Horse Films (US)												--co0259542-- (5)
				#		Dark Horse Productions (GB)											--co0688859-- (1)
				#		Dark Horse Productions (US)											--co0145876-- (2)
				#		Dark Horse (US)														--co0407538-- (2)
				#		Dark Horse Pictures													--co0079284-- (3)
				#
				#	Other companies with the same name.
				#
				#		Dark Horse Studios (IN)												--co0873202-- (1)
				#		Dark Horse Pictures (AU)											--co0580608-- (1)
				#		Dark Horse Cinematics (US)											--co0904153-- (1)
				#		Dark Horse Films (AU)												--co0287768-- (1)
				#		Dark Horse Productions (IN)											--co1075092-- (1)
				#		Dark Horse Pictures (PH)											--co0222712-- (1)
				#		Dark Horse Films (NZ)												--co0187029-- (3)
				#		Dark Horse Rising Productions (CA)									--co0764594-- (1)
				#		Dark Horse Cinemas (IN)												--co0695197-- (2)
				#		Darkhorse Films (SG)												--co0945107-- (1)
				#		Dark Horse Films (FR)												--co0498215-- (1)
				#		Dark Horse Records (GB)												--co0534820-- (1)
				#		Dark Horse Entertainment (NP)										--co1049837-- (1)
				#		Dark Horse Productions (LA)											--co0679442-- (1)
				#		Dark Horse Films (ZA)												--co0660707-- (1)
				#		Dark Horse Studio (IN)												--co0873542-- (1)
				#		Dark Horse Image (TW)												--co0525081-- (1)
				#		Darkhorse Productions (CA)											--co0265773-- (1)
				#		Dark Horses Productions (US)										--co0496148-- (1)
				#		DarkHorse Productions (US)											--co0189646-- (0)
				#		Dark Horse Films (CA)												--co0644162-- (0)
				#		Come Ride the Dark Horse Inc. (US)									--co0163628-- (1)
				#		Darkhorse Pictures (AU)												--co0939801-- (0)
				#		Dark Horse Wine (US)												--co0472751-- (1)
				#		Dark Horse Studios (IN)												--co0873202-- (1)
				#		Dark Horse Pictures (AU)											--co0580608-- (1)
				#		Dark Horse Cinematics (US)											--co0904153-- (1)
				#		Dark Horse Films (AU)												--co0287768-- (1)
				#		Dark Horse Productions (IN)											--co1075092-- (1)
				#		Dark Horse Pictures (PH)											--co0222712-- (1)
				#		Dark Horse Films (NZ)												--co0187029-- (3)
				#		Dark Horse Rising Productions (CA)									--co0764594-- (1)
				#		Dark Horse Cinemas (IN)												--co0695197-- (2)
				#		Darkhorse Films (SG)												--co0945107-- (1)
				#		Dark Horse Films (FR)												--co0498215-- (1)
				#		Dark Horse Records (GB)												--co0534820-- (1)
				#		Dark Horse Entertainment (NP)										--co1049837-- (1)
				#		Dark Horse Productions (LA)											--co0679442-- (1)
				#		Dark Horse Films (ZA)												--co0660707-- (1)
				#		Dark Horse Studio (IN)												--co0873542-- (1)
				#		Dark Horse Image (TW)												--co0525081-- (1)
				#		Darkhorse Productions (CA)											--co0265773-- (1)
				#		Dark Horses Productions (US)										--co0496148-- (1)
				#		DarkHorse Productions (US)											--co0189646-- (0)
				#		Dark Horse Films (CA)												--co0644162-- (0)
				#		Come Ride the Dark Horse Inc. (US)									--co0163628-- (1)
				#		Darkhorse Pictures (AU)												--co0939801-- (0)
				#		Dark Horse Wine (US)												--co0472751-- (1)
				#		Darkhorse Pictures (GB)												--co0108173-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Dark Horse Books (US)												co0978106 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyDarkhorse : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Dark Horse Entertainment'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Dark Horse'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Dark Horse Originals'},
					'expression'	: '(dark[\s\-\_\.\+]*horse[\s\-\_\.\+]*(?:entertainment|indie|comics?|books?))',
				},

				#################################################################################################################################
				# DC Comics
				#
				#	Parent Companies:		Warner Bros. Discovery
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			DC Entertainment, DC Studios
				#	Owned Networks:			-
				#
				#	Streaming Services:		(HBO) Max, The CW, The WB
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		(HBO) Max, The CW, The WB, Netflix (many), and occasional other networks (eg Fox, NBC, etc)
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(259)					(301)
				#	Networks																(0)						(0)
				#	Vendors																	(20)					(8)
				#	Originals																(95 / 79)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		DC Entertainment													co0123927 (125)			167 (176)			9993
				#		DC Comics															co0038332 (87)			60 (136)			429
				#		DC Studios (US)														co1064049 (3)			134194 (27)			184898
				#		DC Studios (GB)														co1036036 (1)
				#		DC Vertigo															co0748686 (1)			121146 (6)			165407
				#		Vertigo (DC Comics)													co0584833 (1)
				#		DC																	co0752503 (1)
				#		DC Films																					26741 (19)			128064
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		DC Universe															co0697225 (10)			36 (8)				2243
				#		Sky Cinema DC Helden												co1058414 (4)
				#		DC Kids																co0951237 (1)
				#		DC Film Television & Entertainment Rebate Fund (US)					co0755173 (1)
				#		DC Universe Infinite (US)											co0881612 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyDccomics : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'DC Studios'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'DC Comics'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'DC Originals'},
					'expression'	: '(detective[\s\-\_\.\+]*comics?|(?:^|(?:vertigo|cinema).*)?dc[\s\-\_\.\+]*(?:$|comic|studio|film|entertainment|universe|helden|kid|vertigo))',
				},

				#################################################################################################################################
				# Dimension Films
				#
				#	Initially a label under Miramax for Horror ans Scifi titles.
				#	When Miramax was sold to Disney, the Weinstein Brothers took this label with them to The Weinstein Company.
				#	Then it was purchased by Lantern Entertainment and is now part of Paramount.
				#
				#	Parent Companies:		Lantern Entertainment, Paramount, Lionsgate (previous),
				#							Miramax (previous), The Weinstein Company (previous)
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Dimension Films, Dimension Television
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Miramax, The Weinstein Compan
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(197)					(143)
				#	Networks																(0)						(0)
				#	Vendors																	(31)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Dimension Films (US)												co0019626 (183)			2247 (141)			7405
				#		Dimension Television (US)											co0079757 (5)			1503 (3)			55328
				#
				#	Other companies with the same name.
				#
				#		Dimension Films (II) (US)											--co0741886-- (1)
				#		Dimension Films (III) (US)											--co0887642-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Dimension Extreme (US)												co0210118 (31)
				#		Dimension Films/Outerbanks Entertainment							co0098484 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyDimension : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Dimension Films'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Dimension'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(dimension[\s\-\_\.\+]*(?:films?|television|extreme))',
				},

				#################################################################################################################################
				# Discovery
				#
				#	Parent Companies:		Warner Bros Discovery (partnership)
				#	Sibling Companies:		HBO, Cinemax, Magnolia, WBTV, Cartoon Network, Adult Swim, Boomerang,
				#							Turner, TMC, TNT, TBS, truTV, Animal Planet, Oprah Winfrey, HGTV, TLC, CNN
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			Discovery Channel, TLC
				#
				#	Streaming Services:		Discovery+, DMAX, (HBO) Max, Philo (partial, Hearst+Disney+AMC+Paramount+Warner)
				#	Collaborating Partners:	Warner, HBO, Animal Planet, Travel Channel, Food Network, TLC, HGTV, BBC, Netflix, Channel 4
				#
				#	Content Provider:		BBC, A&E Networks
				#	Content Receiver:		Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(2424)					(392)
				#	Networks																(5522)					(1502)
				#	Vendors																	(1175)					(0)
				#	Originals																(1362 / 2555)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Discovery Channel													co0045277 (733)			2069 (219)			6790
				#		Discovery Channel Canada (CA)																7638 (15)			7026
				#		Discovery Channel Pictures											co0056361 (14)			67423 (4)			7492
				#		Discovery Channel Images (US)										co0634119 (1)
				#
				#		Discovery Kids														co0092660 (77)			43448 (12)			23816
				#		Discovery Kids (GB)													co0525521 (3)
				#
				#		Discovery UK																				20112 (33)			13007
				#		Discovery (JP)														co0132346 (4)
				#		Discovery LATAM (AR)												co1003986 (2)
				#		Discovery ANZ (NZ)													co0912981 (1)
				#		Discovery Germany (DE)												co0100704 (1)
				#
				#		Discovery Networks Sweden											co0521172 (32)			1061 (8)			49615
				#		Discovery Network													co0021831 (27)
				#
				#		Discovery Communications Europe (GB)								co0134725 (14)
				#		Discovery Communications International (US)							co0265049 (9)
				#
				#		Discovery Production Group (US)										co0213496 (2)
				#		Discovery Creative & Production (US)								co0763811 (2)
				#		Discovery Productions Worldwide (US)								co0241703 (1)
				#		Discovery Productions (II) (US)										co0271061 (1)
				#
				#		Investigation Discovery												co0225421 (308)			3313 (49)			73761
				#		Discovery Studios													co0225759 (53)			1786 (24)			53648
				#		Discovery Productions												co0003317 (9)			17469 (29)			16798
				#		Discovery Digital Networks (US)										co0504839 (4)
				#		Discovery Docs														co0124561 (1)			72759 (4)			274
				#		Discovery Wings (US)												co0256092 (1)
				#		Discovery Firm (JP)													co0255454 (1)
				#		Discovery New Media (US)											co0274735 (1)
				#		SBS Discovery Production											co0453652 (1)
				#
				#	Other production companies.
				#
				#		Discovery Music Source (US)											--co0357680-- (5)
				#		Discovery Music (US)												--co0768937-- (2)
				#
				#	Other companies with the same name.
				#
				#		Discovery Hill Productions (US)										--co0318498-- (2)
				#		Discovery Entertainment (US)										--co0014067-- (2)
				#		Discovery Films UK (GB)												--co0295295-- (2)
				#		Discovery Program (US)												--co0171418-- (1)
				#		Discovery Media Productions (US)									--co0779289-- (1)
				#		Discovery Venture Capital (KR)										--co0315256-- (1)
				#		Discovery Bay Films (US)											--co0360022-- (1)
				#		Discovery Next (JP)													--co0972743-- (1)
				#		Discovery Street Films (CA)											--co0300480-- (1)
				#		Discovery Dance (CA)												--co0093155-- (1)
				#		Global Discovery Group (US)											--co0379842-- (1)
				#		New Discovery Media (US)											--co0423372-- (1)
				#		Discovery Films Company (HK)										--co0968076-- (1)
				#		Discovery Films International (IN)									--co0725594-- (1)
				#		Discovery Media Procuctions (US)									--co0316517-- (1)
				#		Discovery I (US)													--co0974851-- (0)
				#		Corps of Discovery Films (US)										--co0190505-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		discovery+ (US)														co0834810 (416)			1662 (199)			4353
				#		Discovery+ (UK)														co0726548 (131)			1937 (53)			4883
				#		Discovery+ (IN)														co0833882 (10)			2025 (7)			4983
				#		Discovery+ (DK)														co0869091 (5)			1807 (37)			4440
				#		discovery+ (NO)														co0923071 (5)			1993 (39)			4784
				#		Discovery+ (IT)																				1971 (22)			4741
				#		discovery+ (BR)																				2200 (11)			5431
				#		Discovery+ (NL)																				2042 (10)			5192
				#		Discovery+ (FI)																				2599 (5)			5408
				#		discovery+ (DE)																				2668 (5)			6026
				#		discovery+ (ES)																				3038 (3)			6966
				#		Discovery+ (PH)																				2589 (2)			5470
				#		Discovery+ (SE)														co0964265 (1)
				#		discovery+ (SE)														co0965409 (0)			1695 (34)			4462
				#		Discovery Plus (US)													co0848923 (5)
				#
				#		Discovery Channel (NL)												co0210778 (93)
				#		Discovery Channel (US)												co0045277 (71)
				#		Discovery Channel (DE)												co0188065 (37)			3138 (1)			2692
				#		Discovery Channel (AU)												co0182992 (10)			762 (11)			2087
				#		Discovery Channel (IN)												co0197261 (8)
				#		Discovery Channel (IT)												co0243945 (6)
				#		Discovery Channel (LA)												co0350346 (5)
				#		Discovery Channel (PT)												co0404321 (5)
				#		Discovery Channel (HU)												co0405559 (5)
				#		Discovery Channel (NO)												co0268270 (4)
				#		Discovery Channel (FR)												co0511125 (3)
				#		Discovery Channel (GB)												co0894752 (3)			1392 (0)			3926
				#		Discovery Channel (PL)												co0534443 (2)			1541 (14)			3045
				#		Discovery Channel (GR)												co0486937 (2)
				#		Discovery Channel (SE)												co0746360 (2)
				#		Discovery Channel (ES)												co0683600 (1)
				#		Discovery Channel (ZA)												co0565776 (1)
				#		Discovery Channel (RU)												co0654638 (1)
				#		Discovery Channel (RO)												co0397571 (1)
				#
				#		Discovery Channel Canada											co0089706 (100)			1279 (0)			3487
				#		Discovery Channel Canada																	2308 (0)			5668
				#		Discovery Channel UK (GB)											co0120666 (48)
				#		Discovery Channel International										co0070253 (40)
				#		Discovery Channel Asia												co0163534 (13)
				#		discovery channel japan												co0253720 (10)			2516 (1)			5990
				#
				#		Discovery (US)														co0885467 (16)			108 (425)			64
				#		Discovery (US)																				3041 (0)			6978
				#		Discovery (GB)														co0224615 (69)			725 (58)			1079
				#		Discovery (CA)																				352 (45)			106
				#		Discovery (DK)																				1826 (13)			3953
				#		Discovery (BR)																				2219 (12)			3900
				#		Discovery (IT)														co0465058 (21)
				#		Discovery (NL)														co0870258 (2)
				#		Discovery (JP)														co0828614 (1)
				#		Discovery																					2386 (0)			5648
				#		Discovery																					3151 (1)			6903
				#
				#		Discovery Europe													co0102909 (11)
				#		Discovery Latin America/Iberia										co0147826 (16)
				#		Discovery International												co0131594 (9)			2309 (1)			5669
				#		Discovery Asia														co0166855 (2)			1749 (3)			1302
				#		Discovery World																				952 (2)				1534
				#
				#		Investigation Discovery (US)										co0225421 (308)			248 (316)			244
				#		Investigation Discovery (GB)										co0457897 (14)
				#		Investigation Discovery (CA)										co0315118 (10)			1967 (1)			4562
				#		Investigation Discovery (FR)										co0933193 (2)
				#		Investigação Discovery (BR)											co0693803 (2)			2398 (1)			5472
				#
				#		Discovery Health (US)												co0074719 (58)
				#		Discovery Health (CA)												co0147813 (5)
				#		Discovery Health (GB)												co0106294 (4)
				#		Discovery Health Channel											co0427466 (6)			628 (20)			10
				#
				#		Discovery Home & Health (AR)										co0943778 (14)
				#		Discovery Home & Health Brasil										co0564243 (9)			2283 (5)			5451
				#		Discovery Home & Health																		2916 (2)			6083
				#		Discovery Home & Health																		1343 (0)			3427
				#
				#		Discovery Home & Leisure											co0064712 (5)
				#		Discovery Home & Leisure (GB)										co0168990 (1)
				#
				#		Discovery Home Channel												co0155054 (9)
				#		Discovery Life Channel												co0531164 (8)			1321 (2)			670
				#		Discovery Real Time (GB)											co0225264 (5)			315 (7)				626
				#		Discovery Fit & Health												co0389407 (3)
				#		Discovery Travel & Living											co0396789 (3)
				#
				#		Discovery Family													co0500808 (143)			228 (10)			1287
				#		Discovery Familia													co0979624 (7)
				#		Discovery Education (US)											co0328002 (2)
				#
				#		Discovery Kids (BR)													co0614571 (394)			733 (11)			2630
				#		Discovery Kids (US)													co0092660 (77)			601 (28)			22
				#		Discovery Kids (AR)													co1010769 (55)
				#		Discovery Kids Latin America										co0598558 (46)
				#		Discovery Kids (MX)													co1061317 (11)
				#		Discovery Kids (CA)													co0275477 (9)
				#		Discovery Kids (MY)													co0984881 (8)
				#		Discovery Kids (SG)													co1067092 (7)
				#		Discovery Kids (IN)													co0788357 (6)			2884 (4)			6622
				#		Discovery Kids (GB)													co0525521 (3)
				#		Discovery Kids (AE)													co1012796 (2)
				#		Discovery Kíds (SG)													co1067096 (1)
				#
				#		Discovery Toons (MX)												co0981669 (886)
				#		Discovery Toons (MY)												co0984883 (272)
				#		Discovery Toons (US)												co0981827 (66)
				#		Discovery Toons (SG)												co1006785 (12)
				#		Discovery Toons (AE)												co1006154 (6)
				#		Discovery Toons (HK)												co1012797 (3)
				#		Discovery Toons (CA)												co0981825 (2)
				#		Discovery Toons (ES)												co1006964 (1)
				#		Discovery Toons (BR)												co1048735 (1)
				#		Discovery Toons (GB)												co1070858 (1)
				#
				#		Discovery Toons Latin America (AR)									co0981619 (67)
				#		Discovery Toons Latin America (CL)									co1048736 (1)
				#		Discovery Toons Latin America (CO)									co1048737 (1)
				#		Discovery Toons Latin America (MX)									co1048738 (1)
				#
				#		Discovery Toons at Night Latin America (AR)							co0981643 (2)
				#		Discovery Toons at Night (MX)										co0981689 (2)
				#		Discovery Toons Network (BR)										co1005826 (1)
				#
				#		Discovery Science Channel (US)										co0030015 (49)			1968 (4)			3591
				#		Discovery Science Channel (FR)										co0924477 (3)
				#		Discovery Science Channel (GB)										co0904378 (2)
				#		Discovery Science Channel (IT)										co0245318 (1)
				#		Discovery Science Channel (CA)										co0997619 (0)
				#
				#		Science Channel (US)												co0267805 (103)
				#		The Science Channel (US)											co0891875 (1)
				#
				#		Discovery Force Channel (US)										co0981653 (411)
				#		Discovery Force Channel (MY)										co1006802 (0)
				#
				#		Discovery Force (US)												co1023494 (48)
				#		Discovery Forced (US)												co1023840 (2)
				#		Discovery Force (MY)												co1006908 (1)
				#
				#		Discovery Turbo (GB)												co0809123 (1)
				#		Discovery Turbo Brasil																		3316 (1)			5471
				#
				#		Discovery HD (CA)													co0271708 (8)
				#		Discovery HD (DE)													co0896334 (5)
				#		Discovery HD (JP)													co0205109 (1)
				#		Discovery HD Theater												co0274712 (12)
				#
				#		DMAX (DE)															co0212711 (91)			314 (53)			1113
				#		DMAX (DE)															co0500448 (39)
				#		DMAX (IT)															co0504369 (18)			1165 (4)			2742
				#		DMAX (GB)															co0927174 (6)			2604 (1)			5515
				#		DMAX (ES)															co0610831 (3)			728 (19)			2531
				#		DMAX (CH)															co1027849 (1)
				#		DMAX (AT)															co1027848 (1)
				#
				#		Discovery MAX (ES)													co0409438 (9)
				#		Discovery Go														co0656406 (7)
				#		Discovery Times Channel												co0130326 (6)
				#		Discovery Geschichte (DE)											co0225758 (5)
				#		Discovery Military													co0195831 (3)
				#		Discovery VR														co0583138 (2)
				#		Discovery JEET																				1733 (2)			3197
				#		Discovery Historia (PL)												co0314157 (1)
				#		Discovery TV Plus (US)												co1036969 (1)
				#
				#		Animal Planet / Discovery											co0278859 (11)
				#		Canal+ Discovery													co0664644 (4)			2483 (1)			3068
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Discovery Networks (SE)												co0521172 (32)
				#		Discovery Networks (NO)												co0639652 (27)
				#		Discovery Networks (DK)												co0543688 (16)
				#		Discovery Networks (US)												co0625938 (6)
				#		Discovery Networks (ES)												co0165242 (5)
				#		Discovery Networks (DE)												co0284818 (2)
				#		Discovery Networks (FI)												co0607065 (1)
				#
				#		Discovery Networks Europe											co0131861 (99)
				#		Discovery Network (US)												co0021831 (27)
				#		Discovery Networks International									co0601745 (23)
				#		Discovery Network Asia												co0298300 (12)
				#		The Discovery Network												co0051998 (9)
				#		Discovery Networks Latin America/ US Hispanic						co0876160 (8)
				#		Discovery Networks Asia-Pacific										co0808524 (4)
				#		Discovery Networks Southern Europe									co0503443 (1)
				#
				#		Warner Bros. Discovery (US)											co0863266 (146)
				#		Warner Bros. Discovery (NZ)											co1005816 (3)
				#		Warner Bros. Discovery (AU)											co1031568 (1)
				#		Warner Bros. Discovery (TW)											co1031570 (1)
				#		Warner Bros. Discovery (HK)											co1031569 (1)
				#		Warner Bros. Discovery (DE)											co1063267 (1)
				#		Warner Bros. Discovery (GB)											co1008104 (1)
				#		Warner Bros. Discovery (NO)											co1058424 (0)
				#
				#		Discovery Communications											co0077924 (260)			2087 (0)			4990
				#		Discovery Film & Video Distribution									co0212079 (57)
				#		Discovery Films														co0013509 (11)
				#		Discovery Productions												co0003317 (9)
				#		Discovery Planet Green (US)											co0318256 (3)
				#		Discovery Home Video												co0108234 (2)
				#		Discovery Video (AU)												co0322476 (2)
				#		Discovery Store (US)												co0924483 (2)
				#		Discovery Channel Multimedia (US)									co0574955 (1)
				#		Discovery Velocity (CA)												co0759066 (1)
				#		Discovery Enterprises (US)											co0027586 (1)
				#		Discovery (HR)														co1037501 (1)
				#		Discovery Entertainment (JP)										co0211019 (1)
				#		Discovery Adventure (GB)											co0758186 (0)
				#		Discovery Brand Studios (US)										co0583140 (0)
				#		Discovery Web-Native Networks (US)									co0583139 (0)
				#		Discovery Spotlight (US)											co0877509 (0)
				#		Discovery Media Center (US)											co0642760 (0)
				#
				#		SBS Discovery Television											co0473690 (12)
				#		SBS Discovery Media													co0453651 (4)
				#		SBS Discovery Production											co0453652 (1)
				#
				#		TVN Discovery Historia (PL)											co0986413 (1)
				#		TVN Warner Bros. Discovery (PL)										co1044762 (1)
				#
				#		TLC- Discovery (US)													co0394091 (8)
				#		Discovery/DMC (US)													co0930735 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyDiscovery : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Discovery Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Discovery+'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Discovery'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Discovery Originals'},
					'expression'	: '((?:^|the|investiga(?:tion|ção)|warner\s*(?:bros\.?|home)?|canal\+|sbs|animal\s*planet.*|tvn[\s\-\_\.\+]*|tlc[\s\-\_\.\+]*)\s*(?:discovery|dmax)|^(?:the[\s\-\_\.\+]*)?science[\s\-\_\.\+]*channel)',
				},

				#################################################################################################################################
				# Disney
				#
				#	Member of the "modern" Big Five.
				#		https://disney.fandom.com/wiki/Category:Walt_Disney_Company_subsidiaries
				#		https://disney.fandom.com/wiki/List_of_assets_owned_by_Disney
				#		https://en.wikipedia.org/wiki/Category:The_Walt_Disney_Company_subsidiaries
				#
				#	Parent Companies:		Walt Disney
				#	Sibling Companies:		-
				#	Child Companies:		ABC, Buena Vista, Pixar, Touchstone, DreamWorks (previous)
				#
				#	Owned Studios:			Walt Disney, Buena Vista, Pixar, Touchstone, Marvel, Lucasfilm, Star Wars, Hollywood Pictures,
				#							20th Studios/Television (previous Fox), Searchlight (previous Fox), Regency (partial)
				#	Owned Networks:			ABC, FX (previous Fox), Fox (partial, some subsidiaries), Star, Hotstar, A&E, NatGeo, History
				#							Asianet, Vice, Freeform, Lifetime, ESPN, Babble, Telecine (partial, Paramount+Universal+MGM+Disney)
				#
				#	Streaming Services:		Disney+, Hulu (previous Fox+Universal, now 100% Disney), Philo (partial, Hearst+Disney+AMC+Paramount+Warner)
				#	Collaborating Partners:	Hulu, NatGeo, History, Star, Hotstar, ABC, Sony, Universal, Columbia, TriStar, Gaumont, Telecine
				#
				#	Content Provider:		-
				#	Content Receiver:		Disney+, Hulu, Philo, NatGeo, DreamWorks (previous through Touchstone)
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(2752)					(2463)
				#	Networks																(5724)					(838)
				#	Vendors																	(5488)					(1)
				#	Originals																(934 / 804)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Walt Disney Pictures												co0008970 (544)			3542 (609)			2
				#		Walt Disney Studios													co0059516 (149)
				#
				#		Disney Television Animation											co0030830 (196)			244 (297)			3475
				#		Walt Disney Animation Studios										co0074039 (89)			4156 (107)			6125
				#		Walt Disney Animation Japan											co0007273 (19)
				#		Walt Disney Animation (Australia) PTY. LTD.							co0046531 (14)			126396 (4)			177000
				#		Walt Disney Feature Animation										co0075995 (13)			120781 (29)			171656
				#		Walt Disney Feature Animation Florida								co0647646 (8)
				#		Walt Disney Feature Animation Paris									co0473608 (8)
				#		Walt Disney Animation																		11001 (6)			112779
				#		Walt Disney Animation Canada										co0060743 (3)			116243 (5)			158526
				#		Walt Disney Animation Australia										co0032298 (3)
				#
				#		The Walt Disney Company												co0044374 (297)
				#		The Walt Disney Company Japan																113755 (15)			164892
				#		The Walt Disney Company France																80365 (15)			135745
				#		The Walt Disney Company Italia																9951 (11)			81026
				#		Walt Disney Company Italia (IT)										co0233857 (4)			9951 (11)			81026
				#		Walt Disney Company Russia & CIS															15644 (4)			101999
				#		The Walt Disney Company Nordic (SE)															17991 (4)			12925
				#		The Walt Disney Company Germany																162834 (1)			214202
				#
				#		Walt Disney Television (US)																	145 (209)			670
				#		Disney Branded Television											co0858960 (43)
				#		Walt Disney Television Italia										co0487331 (7)
				#		Disney Television France (FR)										co0185084 (6)
				#		Walt Disney Television International India							co0218992 (3)
				#		Walt Disney Television International Japan							co0269268 (2)
				#		Walt Disney Television Alternative									co1019732 (1)			128651 (6)			175458
				#
				#		Disney Educational Productions										co0067765 (8)			76390 (29)			13571
				#		Disney Educational Productions										co0067765 (6)
				#
				#		Walt Disney Productions												co0098836 (280)			897 (1029)			3166
				#		Disneynature (US)													co0236496 (22)			5677 (24)			4436
				#		DisneyToon Studios													co0092035 (13)			6809 (37)			5391
				#		Walt Disney Home Video																		12814 (20)			126540
				#		Disney Destinations													co0228775 (12)			90039 (5)			104966
				#		Disneynature (FR)													co0236193 (7)
				#		Walt Disney Imagineering (US)										co0108298 (7)			33725 (19)			15935
				#		Disney Original Documentary (US)									co0911059 (6)			173936 (2)			224803
				#		Disney Theatrical Productions (DTP)									co0587555 (5)			74559 (6)			107038
				#		Disney Digital Network (US)											co0648616 (4)			74242 (2)			91233
				#		Walt Disney British Films (GB)										co0330557 (4)
				#		Disney Latino (US)													co0251003 (3)
				#		Disney Concerts														co0863227 (2)			134465 (2)			185119
				#		Disney OTV (US)														co0861755 (2)
				#		Disney Broadcast Production											co0629374 (1)			93807 (1)			107039
				#		Disney HSM China Productions										co0323370 (1)			127553 (1)			178202
				#		Walt Disney Archives																		151455 (2)			202949
				#		Disney Interactive (CA)												co0876136 (1)			74241 (1)			41712
				#		Walt Disney Family Foundation (US)									co0060584 (1)
				#
				#		Buena Vista International (US)																9882 (48)			5892
				#		Buena Vista International Film Production (Germany) (DE)			co0127587 (5)
				#		Buena Vista International (Germany) Filmproduktion GmbH (München)							23614 (7)			106
				#		Buena Vista International (Sweden) (SE)								co0057494 (3)
				#		Buena Vista International Film Production France (FR)				co0136752 (3)
				#		Buena Vista Original Productions (BR)								co0775889 (2)
				#		Buena Vista International Films Productions (ES)					co0081470 (2)
				#		Buena Vista Internacional																	117047 (2)			168067
				#		Buena Vista Productions International (US)							co0577273 (1)
				#		Buena Vista Films Cuba (CU)											co0756059 (1)
				#		Buena Vista Original Productions (AR)								co0782717 (0)
				#
				#		Walt Disney EMEA Productions (GB)									co0680423 (16)			114864 (30)			103374
				#		Disney - Vamanos (GB)												co0495414 (1)
				#		Disney's Yellow Shoes Creative Group (US)							co0985230 (1)
				#		Paramount Pictures Corporation and Walt Disney Productions (US)		co0227227 (0)
				#
				# 	Companies mostly for special effects, studio facilities, or copyright, but not production.
				#
				#		Disney Studios Australia											--co0046850-- (81)
				#		Disney Television Studios (US)										--co0090850-- (66)
				#		Disney Enterprises (US)												--co0021471-- (62)
				#		Disney Interactive (US)												--co0040713-- (26)
				#		Disney-ABC Television Group (US)									--co0094898-- (14)
				#		Disney Publishing Worldwide (US)									--co0424315-- (10)
				#		Walt Disney Animation France S.A. (FR)								--co0077580-- (10)
				#		Disneynature (FR)													--co0236193-- (7)
				#		Disney Interactive Media Group (US)									--co0249796-- (4)
				#		Walt Disney Animation Research Library (US)							--co0207427-- (3)
				#		The Walt Disney Family Museum (US)									--co0604056-- (2)
				#		Walt Disney Company (AR)											--co0395729-- (2)
				#		Walt Disney Music Company											--co0654909-- (1)
				#		Disney Entertainment (US)											--co1030682-- (1)
				#		Disney-ABC (US)														--co0913419-- (1)
				#		Disney Interactive Labs (US)										--co0754403-- (1)
				#		Walt Disney Company (CN)											--co0377129-- (1)
				#		Walt Disney World Media Relations (US)								--co0373925-- (1)
				#		Disneyland Entertainment Division (US)								--co0312649-- (1)
				#		Disney Productions (AU)												--co0294111-- (1)
				#		Walt Disney International Television Productions and Broadcasting	--co0348142-- (0)
				#		Walt Disney Philippines (PH)										--co0840391-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Disney+ (US)														co0721120 (2491)		41 (316)			2739
				#		Disney+ (JP)														co0838196 (10)
				#		Disney+																						2597 (0)			6108
				#
				#		Disney+ Hotstar (IN)												co0847080 (403)
				#		Disney+ Hotstar (ID)												co0930616 (9)			2567 (11)			6074
				#		Disney+ Hotstar (MY)												co0930627 (3)			2566 (6)			6029
				#		Disney+ Hotstar (TH)												co1046200 (1)
				#
				#		Disney Channel (US)													co0022105 (1463)		93 (204)			54
				#		Disney Channel (GB)													co0831766 (47)			760 (14)			515
				#		Disney Channel (DE)													co0875800 (43)			853 (5)				539
				#		Disney Channel (IT)													co0326117 (34)			1530 (8)			2897
				#		Disney Channel (IN)													co0507878 (31)			1536 (13)			3874
				#		Disney Channel (ES)													co0124426 (22)			1368 (11)			2327
				#		Disney Channel (BR)																			2026 (13)			1996
				#		Disney Channel (FR)													co0931913 (12)			1265 (11)			3408
				#		Disney Channel (JP)													co0899094 (5)			1744 (4)			4350
				#		Disney Channel (TR)													co0854831 (3)			3119 (1)			6005
				#		Disney Channel (AU)																			1948 (2)			730
				#		Disney Channel (NL)																			2077 (2)			2534
				#		Disney Channel (TW)													co0818715 (2)
				#		Disney Channel (MY)													co0438719 (2)
				#		Disney Channel (RO)													co0410034 (1)
				#		Disney Channel (HK)													co0833749 (1)
				#		Disney Channel (CA)													co0864435 (1)
				#		Disney Channel (BG)													co0410033 (1)
				#		Disney Channel (DK)																			3744 (1)			7482
				#		Disney Channel (RU)																			1519 (1)			4006
				#		Disney Channel (UA)													co0781340 (0)
				#		Disney Channel (KR)																			1837 (0)			4426
				#		Disney Channel (CZ)																			1845 (0)			4610
				#		Disney Channel (PH)																			2519 (0)			5987
				#		Disney Channel HD (US)												co0497271 (21)
				#		Disney Channel Asia (PH)											co0269642 (16)			2478 (2)			5465
				#		The Disney Channel (AU)												co0127640 (15)
				#		Disney Channel Latin America (AR)									co0483030 (13)			176 (12)			835
				#		Disney Channel Australia (AU)										co0479835 (8)
				#		Disney Channel Israel																		1189 (5)			1385
				#		Disney Channels Australia (AU)										co0479836 (4)
				#		Disney Channel Scandinavia (SE)										co0308696 (3)
				#		Disney Channel Middle East (AE)										co0830701 (1)			2835 (1)			6006
				#
				#		Disney XD (US)														co0243675 (228)			48 (75)				44
				#		Disney XD (TR)														co0410032 (46)
				#		Disney XD (GB)														co0293280 (41)			1603 (3)			2324
				#		Disney XD (AR)														co0655773 (31)
				#		Disney XD (NL)														co0293235 (23)
				#		Disney XD (CA)														co0472570 (12)			2107 (1)			5137
				#		Disney XD (DE)														co0962993 (12)
				#		Disney XD (IT)														co0410031 (10)
				#		Disney XD (ES)														co0510795 (9)
				#		Disney XD (JP)														co0311814 (7)
				#		Disney XD (IN)														co0492228 (4)			3622 (1)			6752
				#		Disney XD (NO)														co0503291 (4)
				#		Disney XD (AU)														co0471424 (4)
				#		Disney XD (FR)														co0638820 (3)			2845 (1)			6463
				#		Disney XD (MY)														co0970093 (3)
				#		Disney XD (BR)																				2692 (1)			6244
				#		Disney XD (DK)														co0503273 (2)
				#		Disney XD (UA)														co0693410 (2)
				#		Disney XD (FI)														co0503276 (2)
				#		Disney XD (PL)														co0971893 (1)
				#		Disney XD (SE)														co0503301 (1)
				#		Disney XD (IE)														co0545024 (1)
				#		Disney XD (GR)														co0333590 (1)
				#		Disney XD																					606 (4)				2326
				#		Disney XD Japan (JP)												co0487401 (4)
				#		Disney XD India (IN)												co0492228 (4)
				#
				#		Disney Junior (US)													co0311978 (126)			105 (83)			281
				#		Disney Junior (GB)													co0363715 (24)			2418 (1)			5536
				#		Disney Junior (AR)													co1069365 (6)
				#		Disney Junior (BR)													co0616595 (5)			2766 (2)			5339
				#		Disney Junior (NO)													co0626229 (4)
				#		Disney Junior (TR)													co0503303 (3)
				#		Disney Junior (AU)													co0743057 (3)			171 (1)				2771
				#		Disney Junior (CA)																			3331 (2)			2325
				#		Disney Junior (PH)																			2286 (2)			5611
				#		Disney Junior (PH)																			2282 (0)			5612
				#		Disney Junior (PT)																			1433 (0)			4011
				#		Disney Junior (JP)													co0460088 (2)
				#		Disney Junior (KZ)													co1070494 (1)
				#		Disney Junior (IN)													co0646640 (1)
				#		Disney Junior (FR)													co0940491 (1)
				#		Disney Junior (PL)													co1031882 (1)
				#		Disney Junior (IT)													co0716227 (1)
				#		Disney Jr. (US)														co0328976 (10)
				#		Disney Junior Latin America																	1951 (6)			4242
				#		Disney Junior Educational Resource Group (US)						co0586391 (9)
				#		Disney Junior Television Network (US)								co0475581 (5)
				#
				#		Playhouse Disney (GB)												co0465045 (20)
				#		Playhouse Disney													co0148907 (19)			798 (11)			2991
				#		Playhouse Disney France (FR)										co0654197 (1)
				#
				#		Toon Disney															co0172644 (114)			133 (20)			142
				#		DisneyLife																					1316 (0)			3624
				#		disneynow																					2716 (0)			6332
				#		Disney+ Star (AU)																			2018 (0)			5142
				#		Hulu on Disney+																				3710 (0)			7460
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Walt Disney Home Video (US)											co0039330 (282)
				#		Walt Disney Home Video (DE)											co0108188 (91)
				#		Walt Disney Home Video (MX)											co0774696 (45)
				#		Walt Disney Home Video (GB)											co0119593 (27)
				#		Walt Disney Home Video (NO)											co0565114 (26)
				#		Walt Disney Home Video (AU)											co0497272 (20)
				#		Walt Disney Home Video (NL)											co0279419 (20)
				#		Walt Disney Home Video (JP)											co0472915 (10)
				#		Walt Disney Home Video (BR)											co0090520 (7)
				#		Walt Disney Home Video (FI)											co0380199 (7)
				#		Walt Disney Home Video (FR)											co0406107 (5)
				#		Walt Disney Home Video (NZ)											co0497275 (3)
				#		Walt Disney Home Video (ES)											co0506477 (3)
				#		Walt Disney Home Video (IT)											co0405683 (2)
				#		Walt Disney Home Video (HK)											co0512778 (2)
				#		Walt Disney Home Video (HU)											co0497274 (2)
				#		Walt Disney Home Video (DK)											co0497273 (2)
				#		Walt Disney Home Video (VE)											co0976075 (1)
				#		Walt Disney Home Video (KR)											co0506478 (1)
				#
				#		Walt Disney Studios Home Entertainment (DE)							co0229306 (275)
				#		Walt Disney Studios Home Entertainment (US)							co0227555 (245)
				#		Walt Disney Studios Home Entertainment (NL)							co0244964 (164)
				#		Walt Disney Studios Home Entertainment (AR)							co0292142 (146)
				#		Walt Disney Studios Home Entertainment (FI)							co0248598 (98)
				#		Walt Disney Studios Home Entertainment (GB)							co0235043 (96)
				#		Walt Disney Studios Home Entertainment (NO)							co0565163 (83)
				#		Walt Disney Studios Home Entertainment (MX)							co1042820 (63)
				#		Walt Disney Studios Home Entertainment (TR)							co0660110 (51)
				#		Walt Disney Studios Home Entertainment (JP)							co0218422 (36)
				#		Walt Disney Studios Home Entertainment (SE)							co0256585 (32)
				#		Walt Disney Studios Home Entertainment (AU)							co0226005 (24)
				#		Walt Disney Studios Home Entertainment (FR)							co0298029 (16)
				#		Walt Disney Studios Home Entertainment (BE)							co0286221 (11)
				#		Walt Disney Studios Home Entertainment (CA)							co0360208 (8)
				#		Walt Disney Studios Home Entertainment (DK)							co0474398 (8)
				#		Walt Disney Studios Home Entertainment (CH)							co0244024 (8)
				#		Walt Disney Studios Home Entertainment (IT)							co0448448 (7)
				#		Walt Disney Studios Home Entertainment (ES)							co0297226 (5)
				#		Walt Disney Studios Home Entertainment (RU)							co0597852 (2)
				#		Walt Disney Studios Home Entertainment (AT)							co0429426 (1)
				#		Walt Disney Studios Home Entertainment (SG)							co0338803 (1)
				#
				#		Walt Disney Home Entertainment (US)									co0087337 (92)
				#		Walt Disney Home Entertainment (MX)									co0774695 (59)
				#		Walt Disney Home Entertainment (NO)									co0595116 (31)
				#		Walt Disney Home Entertainment (GB)									co0144563 (6)
				#		Walt Disney Home Entertainment (DK)									co0595115 (2)
				#		Walt Disney Home Entertainment (IE)									co0144564 (0)
				#
				#		Walt Disney Studios Motion Pictures (US)							co0226183 (663)
				#		Walt Disney Studios Motion Pictures Argentina (AR)					co0811166 (233)
				#		Walt Disney Studios Motion Pictures Germany (DE)					co0234296 (105)
				#		Walt Disney Studios Motion Pictures Finland (FI)					co0239645 (98)
				#		Walt Disney Studios Motion Pictures Mexico (MX)						co0882527 (67)
				#		Walt Disney Studios Motion Pictures (BR)							co0813447 (64)
				#		Walt Disney Studios Motion Pictures International (US)				co0230605 (45)
				#		Walt Disney Studios Motion Pictures, Italia (IT)					co0233849 (51)
				#		Walt Disney Studios Motion Pictures Norway (NO)						co0238690 (17)
				#		Walt Disney Studios Motion Pictures Japan (JP)						co0225392 (13)
				#
				#		Disney Cinemagic (GB)												co0514544 (34)
				#		Disney Cinemagic (PT)												co0269496 (24)
				#		Disney Cinemagic (FR)												co0228542 (3)
				#		Disney Cinemagic (DE)												co0291721 (2)
				#		Disney Cinemagic (ES)												co0503297 (1)
				#
				#		Walt Disney Company Nordic (NO)										co0351644 (188)
				#		Walt Disney Company (JP)											co0229701 (117)
				#		The Walt Disney Company Iberia (ES)									co0602039 (34)
				#		Walt Disney Company Russia & CIS (RU)								co0303939 (29)
				#		Walt Disney Company France (FR)										co0188047 (13)
				#		Walt Disney Company (GB)											co0817519 (4)
				#		Walt Disney Company (KR)											co0627160 (4)
				#		Walt Disney Company (MX)											co0336503 (3)
				#		The Walt Disney company (IN)										co0799546 (3)
				#		Walt Disney Company (CH)											co0383487 (3)
				#		Walt Disney Company (BR)											co0646695 (1)
				#
				#		Disney DVD (GB)														co0200835 (3)
				#		Disney DVD (CA)														co0595325 (2)
				#		Disney DVD (DE)														co0557891 (1)
				#		Disney DVD (FR)														co0419912 (1)
				#		Disney DVD (ES)														co0419911 (1)
				#
				#		Walt Disney Television												co0013021 (470)
				#		Disney Junior Television Network (US)								co0475581 (5)
				#		Walt Disney Television International India (IN)						co0218992 (3)
				#		Walt Disney International Television Productions and Broadcasting	co0348142 (0)
				#
				#		Disney Junior Educational Resource Group (US)						co0586391 (9)
				#		Walt Disney Educational Materials Company (US)						co0761450 (1)
				#		Walt Disney Educational Media Company (US)							co0120700 (1)
				#		Disney Educational Presentations (US)								co0042428 (1)
				#
				#		Walt Disney International (US)										co0654909 (2)
				#		Walt Disney International Pictures (TW)								co0361752 (1)
				#		Walt Disney International (ES)										co0356845 (1)
				#
				#		Toon Disney (US)													co0172644 (126)
				#		Disney Media Distribution (DMD) (US)								co0385962 (122)
				#		Disney Media & Entertainment Distribution (US)						co0824956 (63)
				#		Walt Disney Productions (FR)										co0251885 (52)
				#		Walt Disney Telecommunications and Non-Theatrical Company (US)		co0050977 (21)
				#		Disney Interactive Studios (US)										co0256904 (21)
				#		Disney UTV (IN)														co0646633 (14)
				#		Disney Studios (RU)													co0786439 (9)
				#		Walt Disney Productions (SE)										co0298883 (6)
				#		Walt Disney Productions (SE)										co0298883 (6)
				#		Walt Disney Filmverleih (DE)										co0306723 (6)
				#		Disney Blu-ray (FR)													co0292086 (6)
				#		Walt Disney World (US)												co0076708 (5)
				#		Disney Interactive Entertainment (US)								co0381864 (5)
				#		Disney Channels Australia (AU)										co0479836 (4)
				#		Disney Deluxe (JP)													co0777984 (4)
				#		Disney Movies Anywhere (US)											co0494199 (4)
				#		Disney Online Originals (US)										co0356736 (3)
				#		Walt Disney Animation U.K. (GB)										co0445522 (3)
				#		Kanal Disney (RU)													co0671586 (3)
				#		Disney Media Networks (IN)											co0727433 (3)
				#		Disney XYZ (US)														co1005822 (3)
				#		Disney Theatrical Group (US)										co0366876 (3)
				#		The Walt Disney Studio Archives (US)								co0006618 (3)
				#		Disney Digital 3-D (US)												co0252715 (2)
				#		Disney Movie Club (US)												co1035870 (2)
				#		Disney X-Action (KR)												co0688938 (2)
				#		Disney Polska (PL)													co0808425 (2)
				#		Walt Disney Attractions (US)										co0004375 (2)
				#		Walt Disney Motion Pictures Group (US)								co0225453 (1)
				#		Radio Disney (US)													co0796300 (1)
				#		Disney Media & Entertainment Distribution Technology (US)			co0874690 (1)
				#		The Walt Disney Theatrical Company (US)								co0858033 (1)
				#		Zoog Disney (US)													co1071047 (1)
				#		Disney Media Distribution (HK)										co0325880 (1)
				#		Shanghai Disney Resort (CN)											co0545133 (1)
				#		Disney California Adventure (US)									co0836847 (1)
				#		Disneynature (HK)													co0338893 (1)
				#		Walt Disney Home Records (FR)										co0406009 (1)
				#		Disney Media & Entertainment Distribution Technology (US)			co0874690 (1)
				#		Disney Travel on Demand Network (US)								co0228631 (1)
				#		Disneyland (US)														co0127032 (1)
				#		Disney Sound Recording Co. (US)										co0044682 (1)
				#		Disney Cruise Line (US)												co0887985 (1)
				#		Walt Disney Art Classics (US)										co0209424 (1)
				#		Disney Worldwide Services (US)										co0247714 (1)
				#		The Walt Disney Company Foundation (US)								co0663602 (1)
				#		The Walt Disney Company Archive (US)								co0927318 (1)
				#		Disney CIS (RU)														co0247742 (0)
				#		Disney Streaming Service (US)										co0712949 (0)
				#		Disney Hyperion (US)												co1044874 (0)
				#		disney.com																					2357 (1)			5769
				#
				#		Buena Vista International (US)										co0000779 (1197)
				#		Buena Vista International Finland (FI)								co0014626 (162)
				#		Buena Vista International Mexico (MX)								co0121807 (121)
				#		Buena Vista International (BR)										co0123419 (89)
				#		Buena Vista International (SG)										co0126002 (77)
				#		Buena Vista International (GB)										co0916747 (71)
				#		Buena Vista International (IN)										co0792679 (61)
				#		Buena Vista International (Australia) (AU)							co0133895 (55)
				#		Buena Vista International (PH)										co0170500 (52)
				#		Buena Vista International (SE)										co0916748 (45)
				#		Buena Vista International (DK)										co0606140 (44)
				#		Buena Vista International (BE)										co0331976 (42)
				#		Buena Vista International (AR)										co0991889 (38)
				#		Buena Vista International (NL)										co0916028 (37)
				#		Buena Vista International (FR)										co0135322 (34)
				#		Buena Vista International (AT)										co0280125 (28)
				#		Buena Vista International (DE)										co0966487 (26)
				#		Buena Vista International (ES)										co0972210 (23)
				#		Buena Vista International (KR)										co0028786 (22)
				#		Buena Vista International (IE)										co0127146 (22)
				#		Buena Vista International (TW)										co0162996 (21)
				#		Buena Vista International (IT)										co0967209 (21)
				#		Buena Vista International (MX)										co0894430 (18)
				#		Buena Vista International (NO)										co0606141 (18)
				#		Buena Vista International (Norway) (NO)								co0148456 (16)
				#		Buena Vista International (JP)										co0958910 (15)
				#		Buena Vista International (TH)										co0136583 (11)
				#		Buena Vista International (AU)										co0956237 (10)
				#		Buena Vista International (CL)										co0242391 (10)
				#		Buena Vista International (HK)										co0799752 (9)
				#		Buena Vista International (FI)										co1009765 (7)
				#		Buena Vista International (CH)										co1011371 (6)
				#		Buena Vista International (NZ)										co0806192 (5)
				#		Buena Vista International (PL)										co0175122 (4)
				#		Buena Vista International (MY)										co0816614 (4)
				#		Buena Vista International (ID)										co0817786 (3)
				#		Buena Vista International (UY)										co0122790 (3)
				#		Buena Vista International (IS)										co0968316 (3)
				#		Buena Vista International (TR)										co0968314 (3)
				#		Buena Vista International (PT)										co0968309 (3)
				#		Buena Vista International (BO)										co0242525 (2)
				#		Buena Vista International (HU)										co0968313 (2)
				#		Buena Vista International (ZA)										co0187099 (2)
				#		Buena Vista International Italia (IT)								co0990094 (1)
				#		Buena Vista International (Austria) GmbH (AT)						co0122778 (1)
				#		Buena Vista International (CA)										co0243626 (1)
				#		Buena Vista International (CZ)										co0968315 (1)
				#		Buena Vista International (BG)										co1011338 (1)
				#		Buena Vista International (RU)										co0968312 (1)
				#		Buena Vista International (CO)										co1009357 (1)
				#		Buena Vista International (KZ)										co1011345 (1)
				#		Buena Vista International (KW)										co1014399 (1)
				#		Buena Vista International (EG)										co1011337 (1)
				#		Buena Vista International (VN)										co1064117 (1)
				#		Buena Vista International (IL)										co0968311 (1)
				#		Buena Vista International (AE)										co0968310 (0)
				#		Buena Vista International (EC)										co1050658 (0)
				#		Buena Vista International (LU)										co1044115 (0)
				#		Buena Vista International (Denmark) (DK)							co0099937 (0)
				#		Buena Vista International (AZ)										co1044113 (0)
				#		Buena Vista International (GR)										co1051277 (0)
				#		Buena Vista International (CN)										co1050960 (0)
				#		Buena Vista International (VE)										co1050659 (0)
				#		Buena Vista International (LI)										co1044114 (0)
				#		Buena Vista International (PE)										co1051278 (0)
				#		Buena Vista International (KG)										co1044112 (0)
				#
				#		Buena Vista International Television (US)							co0077596 (29)
				#		Buena Vista International Television (JP)							co0968981 (1)
				#		Buena Vista International Television (AU)							co0968983 (1)
				#		Buena Vista International Television (FR)							co0968980 (1)
				#		Buena Vista International Television (GB)							co0968982 (1)
				#		Buena Vista International Television (BR)							co0968984 (1)
				#
				#		Buena Vista Home Entertainment (US)									co0049546 (587)
				#		Buena Vista Home Entertainment (TR)									co0659852 (189)
				#		Buena Vista Home Entertainment (GB)									co0989959 (11)
				#		Buena Vista Home Entertainment (FR)									co0972527 (10)
				#		Buena Vista Home Entertainment (FI)									co0979350 (9)
				#		Buena Vista Home Entertainment (IT)									co0998459 (7)
				#		Buena Vista Home Entertainment (MX)									co1041397 (7)
				#		Buena Vista Home Entertainment (ES)									co1033923 (5)
				#		Buena Vista Home Entertainment (AU)									co1000896 (5)
				#		Buena Vista Home Entertainment (JP)									co1025506 (2)
				#
				#		Buena Vista Home Video (US)											co0193692 (234)
				#		Buena Vista Home Video (GB)											co0110121 (20)
				#		Buena Vista Home Video (BVHV) (US)									co0011680 (19)
				#		Buena Vista Home Video (DE)											co0937874 (5)
				#		Buena Vista Home Video (AU)											co0850185 (5)
				#		Buena Vista Home Video (ES)											co0118321 (5)
				#		Buena Vista Home Video (SE)											co0918597 (4)
				#		Buena Vista Home Video (DK)											co0582081 (3)
				#		Buena Vista Home Video (FR)											co0937873 (2)
				#		Buena Vista Home Video (CN)											co0686598 (2)
				#		Buena Vista Home Video (BE)											co0350074 (1)
				#		Buena Vista Home Video (IS)											co1009793 (1)
				#		Buena Vista Home Video (RU)											co1050629 (1)
				#
				#		Buena Vista Television (US)											co0078478 (289)
				#		Buena Vista Television (AU)											co0503268 (2)
				#		Buena Vista Television (NZ)											co0503269 (1)
				#
				#		Buena Vista Pictures Distribution (US)								co0114699 (520)
				#		Buena Vista Pictures Distribution (CA)								co0302554 (53)
				#		Buena Vista Pictures Distribution (IN)								co0752998 (1)
				#		Buena Vista Pictures Distribution (TH)								co0305751 (1)
				#
				#		Buena Vista Pictures (US)											co0044279 (191)
				#		Buena Vista Pictures (FR)											co0330522 (2)
				#		Buena Vista Pictures (MX)											co0770520 (2)
				#		Buena Vista Pictures (AU)											co0482409 (2)
				#		Buena Vista Pictures (NL)											co0482408 (0)
				#
				#		Buena Vista Japan (JP)												co0212721 (14)
				#		Buena Vista Korea (KR)												co0118329 (3)
				#		Buena Vista (AU)													co1052155 (2)
				#		Buena Vista (Austria) GmbH (AT)										co0016858 (0)
				#		Buena Vista Ireland													co0066549 (0)
				#
				#		Buena Vista Animation Studios (US)									co0918614 (6)
				#		Buena Vista Games (US)												co0167716 (5)
				#		Buena Vista Film Sales (US)											co0039576 (4)
				#		Buena Vista Productions (US)										co0203040 (4)
				#		Buena Vista Films (TW)												co0480703 (1)
				#		BuenaVista International Spain (ES)									co0936067 (1)
				#		CDI Buena Vista International (IT)									co0058858 (0)
				#		Buena Vista Theatical Group (US)									co1038671 (0)
				#		Buena Vista Original Productions (AR)								co0782717 (0)
				#
				#		Disney-ABC Domestic Television (US)									co0213225 (382)
				#		Disney-ABC International Television (US)							co0212150 (27)
				#		Disney-ABC Television Group (US)									co0094898 (14)
				#		Disney-ABC Home Entertainment & Television Distribution (US)		co0739072 (8)
				#		Disney-ABC (US)														co0913419 (1)
				#		Disney-ABC Cable Networks Group (US)								co0094890 (1)
				#
				#		Walt Disney Studios Sony Pictures Releasing (WDSSPR) (RU)			co0209825 (269)
				#		Walt Disney Pictures / Sony Pictures (RU) 							co0310744 (2)
				#		Walt Disney Pictures / Sony Pictures (DK)							co0254863 (0)
				#
				#		YouTube: Disney India (IN)											co0806509 (3)
				#		KCAL - Disney (US)													co0605619 (2)
				#		Walt Disney Pictures/Jerry Bruckheimer Films (US)					co0100079 (1)
				#		Hollywood Records / Disney (US)										co0330842 (1)
				#		Universal-Walt Disney Home Video (IT)								co0189485 (1)
				#		Disney/MGM Studios Florida (US)										co0663644 (1)
				#		Walt Disney Pathé Pictures (FR)										co0863768 (0)
				#
				#		Buenavista Columbia Tri Star Films de Mexico, S. de R.L. de C.V.'	co0039725 (30)
				#		Columbia TriStar Buena Vista Filmes. do Brasil (BR)					co0241443 (13)
				#		Buena Vista Columbia TriStar Films (MY)								co1037590 (1)
				#
				#		Gaumont Buena Vista International (GBVI) (FR)						co0033410 (263)
				#		Ab Svensk Filmindustri / Buena Vista Home Entertainment (FI)		co0183512 (11)
				#
				#################################################################################################################################
				MetaCompany.CompanyDisney : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Walt Disney Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Disney+'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Disney'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Disney Originals'},
					'expression'	: '(disney|buena[\s\-\_\.\+]*vista)',
				},

				#################################################################################################################################
				# DreamWorks
				#
				#	Parent Companies:		Universal
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		NBC, Universal, Netflix, HBO, TNT, Hulu, and more
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(702)					(411)
				#	Networks																(0)						(0)
				#	Vendors																	(179)					(0)
				#	Originals																(267 / 196)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		DreamWorks Animation												co0129164 (160)			249 (180)			521
				#		DreamWorks															co0040938 (159)
				#		DreamWorks Pictures													co0819670 (134)			335 (157)			7
				#		DreamWorks Animation Television										co0461500 (76)			252 (61)			42141
				#		DreamWorksTV														co0554810 (48)
				#		DreamWorks Television												co0003158 (41)			56 (31)				15258
				#		DreamWorks Studios													co0252576 (15)
				#		DreamWorks Theatricals												co0527751 (2)			12040 (1)			73933
				#		DreamWorks Animation Pictures (ES)									co0669071 (2)
				#		DreamWorks Productions (US)											co0102694 (0)
				#
				#	Other production companies.
				#
				#		DreamWorks Records (US)												--co0126930-- (20)
				#
				#	Other "Dreamworks" companies.
				#
				#		Dreamworks Digital (HK)												--co0214559-- (15)
				#		Sucheta DreamWorks Productions (IN)									--co0811038-- (9)
				#		Kaustav Dreamworks (IN)												--co0842036-- (8)
				#		Sucheta DreamWorks Productions [IND] (US)							--co0810983-- (3)
				#		Legend DreamWorks (IN)												--co0656374-- (2)
				#		Giant DreamWorks (IN)												--co0690970 --(1)
				#		Dreamworks Production (LK)											--co0678470-- (1)
				#		Phoenix Dreamworks (IN)												--co0714346-- (1)
				#		Shadow Dreamworks (US)												--co0954531-- (1)
				#		KSS Dreamworks Entertainment (IN)									--co0709657-- (1)
				#		WAO Dreamworks (IN)													--co0857231-- (1)
				#		Dream Works Deliver (US)											--co0562414-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		DreamWorks Home Entertainment (US)					co0027541 (86)
				#		DreamWorks Home Entertainment (CA)					co0299243 (28)
				#		DreamWorks Home Entertainment (AU)					co0772464 (14)
				#		DreamWorks Home Entertainment (GB)					co0289670 (10)
				#		DreamWorks Home Entertainment (NL)					co0397133 (7)
				#		Dreamworks Home Entertainment (MX)					co0961518 (6)
				#		DreamWorks Home Entertainment (FR)					co0121773 (4)
				#		Dreamworks Home Entertainment (BE)					co0431502 (2)
				#
				#		DreamWorks Animation Home Entertainment (US)		co0405898 (14)
				#		DreamWorks Animation Home Entertainment (MX)		co0882259 (1)
				#
				#		DreamWorks Distribution (US)						co0067641 (79)
				#		DreamWorks Distribution (CA)						co0377564 (5)
				#		DreamWorks Distribution (GB)						co0751021 (2)
				#		Dreamworks Distribution LLC (US)					co0169654 (1)
				#
				#		DreamWorks Classics (US)							co0396719 (18)
				#		Oriental DreamWorks (CN)							co0371886 (7)
				#		The DreamWorks Channel (SG)							co0513025 (2)
				#
				#		Beijing Chuangyi DreamWorks Media (CN)				co0646563 (1)
				#		Dreamworks / Paramount Distribution (US)			co0253584 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyDreamworks : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'DreamWorks Pictures'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'DreamWorks'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'DreamWorks Originals'},
					'expression'	: '(dreamworks)',
				},

				#################################################################################################################################
				# Facebook
				#
				#	Parent Companies:		Facebook
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			Facebook Watch
				#
				#	Streaming Services:		Facebook Watch
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(0)						(0)
				#	Networks																(525)					(76)
				#	Vendors																	(8)						(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Facebook Watch														co0667127 (171)			434 (36)			2371
				#		Facebook															co0321654 (151)			1002 (35)			1244
				#		Facebook Live																				1738 (8)			1689
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Facebook Page (US)													co0776772 (2)
				#		Facebook Sound Collection (US)										co0933562 (1)
				#		Facebook The Garcias (US)											co0872204 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyFacebook : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Facebook Watch'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Facebook'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Facebook Originals'},
					'expression'	: '(facebook)',
				},

				#################################################################################################################################
				# Fox
				#
				#	Although "Fox" is in "20th Century Fox", 20th Century was not renamed after the Fox Corporation, like with some other mergers.
				#	Instead the "Fox" came from the original founder's name, when Fox Film and Twentieth Century Pictures merged.
				#	Fox (News Corporation) just kept the name when purchasing the studios in the 1980s, probably due to the coincidence.
				#	In 2019, Disney purchased most of Fox. Disney then renamed it to "20th Century Studios" to remove the relation with Fox.
				#	All the studios/assets that were not purchased by Disney (mainly Fox News), spun off into the new "Fox Corporation".
				#
				#	Parent Companies:		Fox Corporation, News Corporation (previous)
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			MarVista Entertainment, Bento Box Entertainment[
				#							20th Century Fox (previous), Searchlight Pictures (previous), Fox 2000 Picturess (previous),
				#							(New) Regency Enterprises (previous), Endemol Shine (previous), Star Wars (previous)
				#	Owned Networks:			Fox, TMZ, Foxtel (partial),
				#							FX/FXX/FXM (previous), National Geographic (previous), Star (previous), Sky (previous partial)
				#
				#	Streaming Services:		Tubi, Hulu (previous partial), DirecTV (previous partial)
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		Tubi, Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(7225)					(2830)
				#	Networks																(2392)					(930)
				#	Vendors																	(13383)					(0)
				#	Originals																(373 / 870)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		20th Century Fox													co0000756 (3669)		50 (1741)			25
				#		20th Century Fox Studios											co0096253 (223)
				#		20th Century Fox Television											co0056447 (610)			42 (403)			1556
				#		20th Century Fox Animation											co0179259 (36)			5168 (22)			11749
				#		20th Century Fox Consumer Products									co0645300 (0)
				#		20th Century Fox Cartoons											co1031931 (1)
				#		20th Century Fox Home Entertainment															5039 (84)			3635
				#
				#		20th Century Fox Brazil												co0010685 (138)			68257 (34)			89438
				#		20th Century Fox Korea												co0077505 (1)			6254 (8)			112148
				#		20th Century Fox Japan																		150785 (2)			202328
				#
				#		Twentieth Century-Fox Productions									co0103215 (61)
				#		Fox 2000 Pictures													co0017497 (80)			3965 (76)			711
				#
				#		FOX Entertainment													co0738806 (118)			1570 (47)			85721
				#		Fox Alternative Entertainment										co0745899 (28)			106306 (25)			156646
				#		FOX Entertainment Studios											co1000157 (7)			137334 (7)			187918
				#		FOX Entertainment Group																		1570 (47)			85721
				#
				#		Fox Television Animation											co0159275 (36)			1780 (14)			67210
				#		Fox Television Network												co0044236 (34)			2998 (12)			17266
				#		Fox Television Studios												co0094955 (53)			16 (64)				6529
				#		Fox Television Studios Pictures										co0837708 (1)
				#		Fox Television Studios (GB)											co0205994 (3)
				#		FOX Television Productions											co0219533 (1)
				#
				#		Fox 21																co0153896 (25)			7 (14)				19699
				#		Fox 21 Television Studios											co0511631 (32)			17 (31)				86063
				#		Fox 9																co0708085 (2)
				#
				#		Fox Searchlight Pictures											co0982337 (190)			4413 (139)			43
				#		Fox Star Studios													co0241299 (7)			6068 (65)			12154
				#		Foxstar Productions													co0036884 (4)			112608 (20)			4450
				#		Fox Searchlab														co0029761 (3)
				#		Fox West Pictures													co0096046 (1)			4213 (11)			3401
				#		Fox Nitetime Productions											co0073335 (1)			136447 (1)			187091
				#
				#		Fox Latin American Channels											co0540029 (9)			144304 (15)			177366
				#		Fox International Channels											co0389268 (10)			107 (33)			50011
				#		Fox International Channels Hong Kong								co0526787 (8)			68794 (2)			48198
				#		Fox International Productions										co0237611 (35)			110 (15)			7485
				#		Fox International Productions Spain									co0523978 (3)			155752 (9)			207356
				#		Fox International Productions China									co0355206 (2)			155826 (1)			207365
				#		Fox International Productions Brazil								co0478329 (6)			155821 (4)			207362
				#		Fox International Productions Japan									co0505758 (7)			155817 (5)			207355
				#		Fox International Productions Germany								co0381995 (7)			155810 (8)			207357
				#		Fox International Productions Italy									co0324816 (3)			155818 (1)			207359
				#		Fox International Productions India															155809 (3)			207354
				#		Fox International Production (KR)									co0658666 (1)
				#		Fox International Studios											co0592896 (1)
				#
				#		Fox Children's Productions											co0161155 (7)
				#		Fox Children's Network Inc.											co0016208 (4)
				#
				#		Fox World (US)														co0111263 (5)
				#		Fox World Australia (AU)											co0119101 (4)			109665 (2)			87138
				#		Fox World (AU)														co0145961 (1)
				#
				#		Fox Animation Studios												co0043064 (13)			11610 (3)			11231
				#		Fox Studios (US)													co0359883 (8)
				#		Fox Studio (US)														co0089950 (3)
				#		Fox Studios Sydney													co0145584 (4)
				#
				#		Fox Sports															co0230438 (111)			9574 (28)			79258
				#		Fox Sports Originals												co0481724 (3)
				#
				#		Fox Family Films													co0049229 (13)
				#		Fox Atomic															co0176225 (10)			7531 (10)			2890
				#		Fox Entertainment News												co0282311 (1)			131257 (1)			181895
				#		FOX Original Productions											co0864210 (1)			84751 (2)			117823
				#		Fox Movie Channel Productions										co0564373 (2)
				#		Fox Digital Studios													co0330294 (1)			593 (9)				25250
				#		Fox Video Productions (GB)											co0494836 (1)
				#		Fox Special Ops														co0568535 (0)
				#
				#		FOXTEL																						20983 (27)			79082
				#		Foxtel Productions (AU)												co0119102 (12)
				#		Fox-Walden (US)														co0201557 (2)
				#		Warner Bros. Television / Fox										co0858861 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Fox Network (US)													co0070925 (978)
				#
				#		FOX																							2569 (3)			6088
				#		FOX (US)															co0761770 (0)			5 (601)				19
				#		Fox (GB)															co0751740 (13)			26 (3)				961
				#		FOX (TR)																					29 (129)			303
				#		Fox (AR)															co0202535 (268)
				#		FOX (NL)															co0440497 (166)
				#		Fox (FI)															co0771707 (37)
				#		Fox (IT)															co0478980 (11)
				#		Fox (JP)															co0877386 (8)
				#		FOX (RU)															co0449297 (7)
				#		Fox (KR)															co0135313 (5)
				#		FOX (ES)															co0804693 (4)			32 (2)				2145
				#		FOX (ZA)															co0448576 (4)
				#		Fox (BR)															co0589037 (3)			764 (9)				2319
				#		Fox (AT)															co0187655 (3)
				#		Fox (GR)															co0780552 (2)
				#		FOX (TW)															co0495243 (1)
				#		FOX (GE)															co0488293 (1)
				#		Fox (NL)															co0953613 (0)
				#		Fox (FR)															co0233692 (0)
				#
				#		Fox Kids (US)																				7 (43)				2686
				#		Fox Kids (FR)																				484 (3)				2446
				#		Fox Kids (NL)																				1936 (1)			4522
				#		Fox Kids (BR)																				2526 (1)			5996
				#
				#		Fox Kids Network (US)												co0007893 (202)
				#		Fox Kids Video (US)													co1071109 (1)
				#		Fox Family Channel (US)												co0054541 (98)
				#
				#		Fox Sports Networks (US)											co0048418 (115)			13 (7)				360
				#		Fox Sports 1 (US)													co0545358 (43)			35 (8)				2317
				#		Fox Sports (AU)														co0247100 (39)			1315 (10)			338
				#		Fox Sports Films (US)												co0682531 (14)
				#		Fox Sports One (US)													co0447568 (14)
				#		Fox National Cable Sports Networks (US)								co0198143 (8)
				#		Fox Soccer (US)														co0267041 (7)			2164 (2)			415
				#		Fox Sports & Entertainment (JP)										co0575133 (6)
				#		Fox Sports 2 (US)													co0489335 (4)			24 (3)				875
				#		Fox Sports Sun (US)																			574 (2)				131
				#		Fox Sports Detroit (US)																		2259 (1)			87
				#
				#		Fox Life HD (JP)													co0202732 (27)
				#		FOX Life (GR)														co0277812 (17)
				#		Fox Life (IT)														co0203823 (14)
				#		Fox Life (JP)														co0306913 (12)
				#		FOX Life (FR)														co0249996 (7)
				#		FOX Life (ES)														co0558237 (6)			829 (0)				3516
				#		Fox Life																					2413 (3)			5201
				#		Fox Life (PT)														co0284410 (3)
				#		FOX Life (BR)														co0571347 (3)
				#		FOX Life (CL)														co0540887 (3)
				#		FOX Life (AR)														co0540030 (2)
				#		FOX Life (CO)														co0540882 (2)
				#		Fox Life (TR)														co0231938 (1)
				#		FOX Life (PE)														co0540885 (1)
				#		FOX Life (NI)														co0540881 (1)
				#		FOX Life (SV)														co0540032 (1)
				#		FOX Life (HN)														co0540880 (1)
				#		FOX Life (EC)														co0540884 (1)
				#		FOX Life (VE)														co0540886 (1)
				#		Fox Life (CO)														co0203920 (1)
				#		FOX Life (GT)														co0540879 (1)
				#		FOX Life (UY)														co0540031 (1)
				#		FOX Life (CR)														co0540033 (1)
				#		Fox Life (PL)														co0417565 (0)
				#
				#		FOXlife (TR)														co0375871 (59)
				#		FOXlife (NL)														co0301422 (23)
				#		FOXlife (GR)														co0356177 (13)
				#		FOXlife (PT)														co0355485 (5)
				#		FOXlife (CSHH)														co0355572 (5)
				#		FOXlife (PL)														co0365499 (4)
				#		FOXlife (EE)														co0355970 (4)
				#		FOXlife (BR)																				1175 (4)			1117
				#		FOXlife (BG)														co0367831 (2)			1181 (2)			1498
				#		FOXlife (RU)														co0326196 (2)
				#		FOXlife (MK)														co0367883 (2)
				#		Foxlife (FR)														co0201790 (1)
				#		FOXlife (SI)														co0364689 (1)
				#		FOXlife (HR)														co0375893 (1)
				#		FoxLife Africa (ZA)													co0764281 (1)
				#
				#		Fox Crime (JP)														co0202574 (48)
				#		Fox Crime (TR)														co0449463 (32)
				#		Fox Crime (IT)														co0206943 (17)			1079 (2)			1414
				#		Fox Crime (ES)														co0341010 (2)
				#		Fox Crime (BG)														co0350472 (2)
				#		Fox Crime (ZA)														co0546196 (1)
				#		Fox Crime (RS)														co0619897 (1)
				#		Fox Crime Platinum (JP)												co0403745 (5)
				#
				#		Fox Premium Action																			23 (1)				1067
				#		Fox Premium Series																			28 (7)				1640
				#		Fox Premium Series (AR)												co0710263 (16)
				#
				#		Fox Footy (AU)														co0247220 (1)			3199 (1)			2316
				#		Fox Footy Channel (AU)												co0457833 (2)			12 (1)				481
				#
				#		FOX Docos (AU)														co1028671 (1)
				#		Fox Docos (US)														co0974098 (0)
				#
				#		Fox Box (US)														co0051829 (19)
				#		FoxBox (US)															co0823247 (2)
				#
				#		Fox Business Network (US)											co0258754 (40)			1174 (2)			2320
				#		Fox Business Channel (US)											co0210247 (13)
				#		Fox Business (US)													co0857401 (1)
				#
				#		Fox Classics														co0189391 (2)			1981 (1)			5028
				#		Fox Classics (JP)													co0542537 (12)
				#
				#		Canal FOX (AR)														co0107413 (2)			2805 (2)			2678
				#		Canal Fox (MX)														co0363535 (4)
				#		Canal Fox (BR)														co0359063 (7)
				#
				#		Foxtel (AU)															co0039238 (116)			2263 (0)			5296
				#		FOXTELECOLOMBIA (co)												co0227681 (44)			1901 (0)			2538
				#		Foxtel Now (AU)														co0778133 (11)
				#		Foxtel Digital (AU)													co0174174 (8)
				#		Foxtel Arts															co0626569 (5)			734 (1)				2687
				#		foxtel GO																					1902 (2)			4578
				#		Foxtel History Channel (AU)											co0919693 (2)
				#		Factual Foxtel (AU)													co0974175 (1)
				#		showcase (AU)																				326 (10)			1630
				#
				#		Fox Movie Channel (US)												co0004295 (16)
				#		Fox Movies Premium (JP)												co0520126 (1)
				#		Fox Action Movies																			388 (1)				2648
				#
				#		Fox Reality Channel (US)											co0250861 (14)			10 (13)				243
				#		Fox Reality (US)													co0159248 (12)
				#
				#		Fox Nation (US)														co0721667 (96)			2109 (27)			5259
				#		Fox8 (AU)															co0204898 (47)			11 (18)				327
				#		Fox Now (US)														co0908997 (39)
				#		Fox Latin America													co0078297 (22)			25 (10)				1651
				#		FOX Showcase (AU)													co0736326 (8)			2743 (7)			6379
				#		Fox News Channel (US)												co0085044 (8)			1045 (31)			45
				#		FoxPlay																co0731654 (4)			2108 (1)			3483
				#		fox.com (US)																				1958 (2)			4774
				#		Fox One (AU)														co0773182 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Fox Video (US)														co0017628 (414)
				#		Fox Video (AU)														co0077922 (131)
				#		Fox Video (DE)														co0166027 (60)
				#		Fox Video (GB)														co0117449 (35)
				#		Fox Video Japan (JP)												co0442630 (32)
				#		Fox Video (NL)														co0279204 (21)
				#		Fox Video (IT)														co0613529 (18)
				#		Fox Video (JP)														co0226875 (11)
				#		Fox Vidéo (FR)														co0186658 (9)
				#		Fox Video															co0044433 (8)
				#		Fox Video (FR)														co0410408 (7)
				#		Fox Video (ES)														co0794651 (3)
				#		Fox Video (GR)														co0258074 (3)
				#		FoxVideo (CA)														co0663130 (4)
				#		FoxVideo (HK)														co0662785 (2)
				#		Fox Video España S.A. (ES)											co0117468 (1)
				#		Fox Video (BE)														co0212875 (1)
				#		Fox Video (PL)														co0723388 (1)
				#		Fox Video (II) (IT)													co0663129 (0)
				#
				#		Fox Channel (DE)													co0873684 (24)
				#		FOX channels portugal (PT)											co0350138 (6)
				#		Fox Channel Italy (IT)												co0838082 (3)
				#		FOX channel (ES)													co0951793 (1)
				#		Fox Channel (AR)													co0981624 (1)
				#
				#		Fox International Channels (IT)										co0169177 (16)
				#		Fox International Channels (US)										co0389268 (10)
				#		Fox International Channels (JP)										co0376922 (7)
				#		Fox International Channels (AR)										co0534355 (7)
				#		Fox International Channels (HK)										co0526787 (7)
				#		Fox International Channels (GB)										co0373782 (4)
				#		FOX International Channels Latin America (US)						co0540029 (9)
				#		Fox International Channels Asia Pacific (HK)						co0569543 (5)
				#		Fox International Channels Content Sales [us] (GB)					co0506412 (2)
				#		FOX International Channels (PL)										co0590259 (2)
				#		Fox International Channels (ES)										co0534310 (1)
				#		Fox International Channel (ID)										co0602412 (1)
				#
				#		Fox Television (US)													co0004762 (71)
				#		Fox Television Stations (US)										co0034633 (47)
				#		FOX Television (RS)													co0287474 (2)
				#		Fox TV (TR)															co0296277 (181)
				#		Fox-TV (US)															co0037196 (11)
				#		Fox TV																						1653 (0)			4230
				#
				#		Fox Broadcasting Company (US)										co0030121 (57)
				#		Fox Broadcasting Network (US)										co0660503 (1)
				#
				#		Fox Networks Group (US)												co0198140 (26)
				#		Fox Networks Group Latin America (AR)								co0653064 (5)
				#		Fox Networks Group Asia Pacific (HK)								co0746833 (5)
				#		Fox Networks Group (PH)												co0743189 (3)
				#		Fox Networks Group Asia Pacific Taiwan								co0817521 (2)
				#		Fox Networks Group. (AR)											co0771917 (1)
				#
				#		FoxFaith (US)														co0188813 (9)
				#		Fox Faith (US)														co0202504 (1)
				#		FOX SOUL (US)														co0819148 (14)
				#
				#		Fox Guild Home Entertainment (GB)									co0775365 (5)
				#		Fox / Guild Video (GB)												co0197094 (3)
				#
				#		Fox Film Corporation (US)											co0028775 (1237)
				#		Fox STAR Studios (IN) (not a studio)								co0266060 (118)
				#		Fox Traveller (IN)													co0544609 (7)
				#		Fox World Cinema (US)												co0339536 (6)
				#		Fox Home Entertainment (US)											co0496965 (5)
				#		Fox Cable Networks (US)												co0111795 (5)
				#		Fox Interactive (US)												co0009425 (3)
				#		Fox Entertainment Global (US)										co0947625 (3)
				#		Fox History and Entertainment Channel (IN)							co0279054 (2)
				#		Fox Connect (US)													co0472872 (1)
				#		Fox Digital Entertainment (US)										co0443515 (0)
				#
				#		20th Century Fox (BR)												co0010685 (138)
				#		20th Century Fox (IT)												co0943364 (49)
				#		20th Century Fox (DE)												co0952616 (40)
				#		20th Century Fox (GB)												co0931863 (21)
				#		20th Century Fox (KR)												co0051662 (19)
				#		20th Century Fox (ZA)												co1051152 (2)
				#
				#		20th Century Fox Argentina											co0007180 (786)
				#		20th Century Fox India												co0092296 (441)
				#		20th Century Fox Australia											co0063989 (133)
				#		20th Century Fox Korea												co0853216 (81)
				#		20th Century Fox de Venezuela										co0421648 (75)
				#		20th Century Fox España												co0368892 (9)
				#		20th Century Fox Netherlands										co0078923 (5)
				#		20th Century Fox Norway												co0148451 (5)
				#		20th Century Fox Sweden												co0380710 (3)
				#		20th Century Fox Israel												co0368801 (1)
				#		20th Century Fox Iceland											co0368843 (1)
				#		20th Century Fox de Chile											co0270675 (1)
				#		20th Century Fox Serbia (CSHH)										co0379325 (0)
				#		20th Century Fox Uruguay (UY)										co0368661 (0)
				#		20th Century Fox Sweden (NZ)										co0379362 (0)
				#		20th Century Fox East Africa (KE)									co0379346 (0)
				#		20th Century Fox Portugal (PT)										co0368861 (0)
				#		20th Century Fox New Zealand (NZ)									co0379300 (0)
				#
				#		20th Century Fox International										co0256824 (12)
				#		20th Century Fox International Classics								co0012812 (8)
				#		20th Century Fox Latin America										co0092951 (9)
				#
				#		20th Century Fox Films of Bangalore (IN)							co0547664 (0)
				#		20th Century Fox Films of Bombay (IN)								co0547663 (0)
				#
				#		20th Century Fox Home Entertainment (US)							co0010224 (2260)
				#		20th Century Fox Home Entertainment (DE)							co0280047 (783)
				#		20th Century Fox Home Entertainment (BR)							co0150813 (377)
				#		20th Century Fox Home Entertainment (GB)							co0063964 (371)
				#		20th Century Fox Home Entertainment (AU)							co0159046 (200)
				#		20th Century Fox Home Entertainment (AR)							co0296943 (177)
				#		20th Century Fox Home Entertainment (CA)							co0297163 (168)
				#		20th Century Fox Home Entertainment (MX)							co0751509 (127)
				#		20th Century Fox Home Entertainment (IT)							co0108018 (67)
				#		20th Century Fox Home Entertainment (FR)							co0226330 (49)
				#		20th Century Fox Home Entertainment (BE)							co0286182 (32)
				#		20th Century Fox Home Entertainment (ES)							co0794652 (22)
				#		20th Century Fox Home Entertainment (HK)							co0544968 (21)
				#		20th Century Fox Home Entertainment (JP)							co0788854 (20)
				#		20th Century Fox Home Entertainment (SE)							co0273176 (8)
				#		20th Century Fox Home Entertainment (TR)							co0665472 (4)
				#		20th Century Fox Home Entertainment (NL)							co0918688 (2)
				#		20th Century Fox Home Entertainment (VE)							co0421647 (1)
				#		20th Century Fox Home Entertainment (HU)							co0613528 (1)
				#		20th Century Fox Home Entertainment (DK)							co0918844 (1)
				#		20th Century Fox Home Entertainment (KR)							co0883912 (1)
				#		20th Century Fox Home Entertainment (NO)							co0918845 (1)
				#		20th Century Fox Home Entertainment (CN)							co0200961 (1)
				#		20th Century Fox Home Entertainment (GR)							co0094759 (0)
				#
				#		20th Century Fox Video (US)											co0605838 (113)
				#		20th Century Fox Video (GB)											co0581069 (10)
				#		20th Century Fox Video (JP)											co0662791 (2)
				#		20th Century Fox Video (AU)											co0662795 (2)
				#		20th Century Fox Video												co0030446 (0)
				#
				#		20th Century Fox CIS (RU)											co0209782 (190)
				#		20th Century Fox Hellas (GR)										co0764128 (15)
				#		20th Century Fox Television Distribution							co0197226 (15)
				#		20th Century Fox Digital Unit										co0046053 (2)
				#		20th Century Fox Digital Unit										co0046053 (2)
				#		20th Century Fox Library Services (US)								co0173400 (1)
				#		20th Century Fox Still Collection (US)								co0195082 (0)
				#		20th Century Fox Television International (US)						co0451003 (0)
				#
				#		Twentieth Century Fox (US)											co0000756 (3669)
				#		Twentieth Century-Fox (MX)											co0862964 (678)
				#		Twentieth Century Fox (FR)											co0937473 (127)
				#		Twentieth Century Fox (MX)											co0826899 (122)
				#		Twentieth Century Fox (BE)											co0937474 (56)
				#		Twentieth Century Fox (CA)											co0711817 (27)
				#		Twentieth Century-Fox (BR)											co0866807 (7)
				#		Twentieth Century-Fox (AR)											co0863455 (6)
				#		Twentieth Century-Fox (CA)											co0866288 (4)
				#		Twentieth Century-Fox (CU)											co0862965 (3)
				#		Twentieth Century-Fox (PR)											co0863456 (2)
				#		Twentieth Century Fox (NO)											co0271701 (1)
				#		Twentieth Century Fox (SD)											co0924784 (0)
				#
				#		Twentieth Century Fox Home Entertainment (NL)						co0189783 (785)
				#		Twentieth Century Fox Home Entertainment (FI)						co0643891 (51)
				#		Twentieth Century Fox Home Entertainment (US)						co0785884 (13)
				#		Twentieth Century Fox Home Entertainment (NO)						co0623011 (6)
				#		Twentieth Century Fox Home Entertainment (RU)						co0746852 (5)
				#		Twentieth Century Fox Home Entertainment (DK)						co0643890 (4)
				#		Twentieth Century Fox Home Entertainment (SE)						co0662285 (2)
				#		Twentieth Century Fox Home Entertainment (DE)						co1034313 (1)
				#		Twentieth Century Fox Home Entertainment (ZA)						co0855510 (1)
				#
				#		Twentieth Century Fox Film Company (GB)								co0053239 (1359)
				#		Twentieth Century Fox Film Company (BE)								co0491690 (10)
				#		Twentieth Century Fox Film Company (FI)								co0491691 (3)
				#		Twentieth Century Fox Film Company (DE)								co0947212 (3)
				#		Twentieth Century Fox Film Company (CA)								co0707661 (3)
				#		Twentieth Century-Fox Film Company (GB)								co0832095 (7)
				#		Twentieth Century-Fox Film Company (CA)								co0867515 (3)
				#		Twentieth Century-Fox Film Company (MX)								co0867516 (2)
				#		Twentieth Century-Fox Film Company (BR)								co0867517 (1)
				#		Twentieth Century-Fox Film Company (PR)								co0867518 (1)
				#		Twentieth Century-Fox Film Company (CU)								co0867519 (1)
				#		Twentieth Century-Fox Film Company (AR)								co0870304 (1)
				#		Twentieth Century Fox Film Company (AU)								co0611815 (0)
				#
				#		Twentieth Century Fox Film (AT)										co0241365 (9)
				#		Twentieth Century-Fox Film (NL)										co0814039 (2)
				#
				#		Twentieth Century Fox Central Files (US)							co0080169 (1)
				#		Twentieth Century Fox Promotional Programming (US)					co0160971 (1)
				#		Twentieth Century Fox Photo Archives (US)							co1027357 (1)
				#		Twentieth Century Fox Film (US)										co1040440 (1)
				#		Twentieth Century Fox Collection, UCLA Arts Special Collections		co0196456 (0)
				#		Twentieth Century Fox Travel (US)									co0197792 (0)
				#		Twentieth Century Fox/Davis Entertainment							co0099617 (0)
				#		Twentieth Century Fox Feature Publicity								co0118485 (0)
				#
				#		Twentieth Century Fox Music (US)									co0195278 (4)
				#		20th Century Fox Records (US)										co0346045 (3)
				#		20th Century Fox Music Corporation (US)								co0694711 (1)
				#
				#		21st Century Fox (US)												co0423932 (1)
				#		21st Century Fox Australia (AU)										co0040586 (1)
				#		21st Century Afrikan Fox (NG)										co0209926 (1)
				#		21st Century Fox (IT)												co0293095 (0)
				#
				#		CBS/Fox (US)														co0007496 (600)
				#		CBS/Fox (DE)														co0226201 (280)
				#		CBS/Fox (AR)														co0094754 (94)
				#		CBS/Fox (GR)														co0130300 (4)
				#		CBS/Fox (MX)														co0761328 (1)
				#
				#		CBS / Fox Video (GB)												co0106097 (142)
				#		CBS/Fox Video (BE)													co0212901 (82)
				#		CBS / Fox Video (NL)												co0266215 (63)
				#		CBS/Fox Video (JP)													co0223570 (30)
				#		CBS/Fox Video (US)													co0806725 (43)
				#		CBS/Fox Video (FR)													co0244801 (41)
				#		CBS/Fox Video (DE)													co0244996 (14)
				#		CBS/Fox Video (ES)													co0124383 (7)
				#		CBS Fox Video (AU)													co0304538 (6)
				#		CBS/Fox Video (AU)													co0877389 (4)
				#		CBS/Fox Video (IT)													co0680153 (3)
				#		CBS/Fox Video (BR)													co0700002 (2)
				#		CBS/Fox Video (GR)													co0698066 (1)
				#
				#		CBS/Fox Home Video (AU)												co0042311 (865)
				#		CBS/Fox Home Video (NO)												co0599875 (2)
				#		CBS/Fox Home Video (NZ)												co0939093 (1)
				#
				#		Shochiku CBS/Fox Video (SCF) (JP)									co0257036 (23)
				#		Shochiku CBS/Fox Video (JP)											co0670562 (2)
				#
				#		CBS/Fox Video Far East (JP)											co0445889 (21)
				#		CBS/Fox Video Sports (US)											co0481487 (1)
				#		CBS / Fox Video Music (US)											co0400863 (1)
				#		CBS Studios/FOX (US)												co0855511 (0)
				#
				#		Fox-Warner (CH)														co0125154 (305)
				#		Fox-Warner (NL)														co0815746 (3)
				#		Warner/Fox (PE)														co0224399 (1)
				#
				#		Fox-Paramount Home Entertainment (FI)								co0453999 (78)
				#		Fox-Paramount Home Entertainment (NO)								co0565880 (32)
				#		Fox-Paramount Home Entertainment (DK)								co0601119 (23)
				#		Fox-Paramount Home Entertainment (SE)								co0604098 (16)
				#
				#		Fox Columbia TriStar Films (AU)										co0628925 (175)
				#		Hoyts Fox Columbia TriStar Films (AU)								co0768357 (152)
				#		Fox Columbia Film Distributors (AU)									co0629458 (131)
				#		Columbia-Fox (GR)													co0025186 (13)
				#		Columbia-Fox (DK)													co0628924 (5)
				#		Columbia TriStar Fox Films (NL)										co1021830 (2)
				#
				#		Fox Pathé Europa (FR)												co0107998 (216)
				#		Fox Pathe Home Entertainment (GB)									co0035270 (10)
				#		Fox-Pathé															co0039408 (2)
				#		Fox Pathe Europa (DE)												co0292578 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyFox : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Fox Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Fox'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Fox'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Fox Originals'},
					'expression'	: '(^fox[\s\-\_\.\+]*(?:$|\d+|kid|family|sport|soccer|national|life|crime|premium|movie|film|action|reality|nation|international|world|home|footy|doco|box|business|classic|now|play|one|connect|digital|news|broadcast|network|cable|showcase|latin|vid[eé]o|channel|tv|television|faith|soul|star|travel|guild|interactive|entertainment|history|\/|\.com)|canal[\s\-\_\.\+]*fox|foxtel|(?:20th|twentieth|21st|twenty[\s\-\_\.\+]*first |cbs|warner|paramount|columbia|path[eé]).*?fox|fox.*?(?:warner|paramount|columbia|path[eé]))',
				},

				#################################################################################################################################
				# Freevee
				#
				#	Freevee/FV owned by Amazon.
				#	Previously named IMDb Freedive and IMDb TV.
				#
				#	Parent Companies:		Amazon
				#	Content Provider:		Amazon
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(58)					(0)
				#	Networks																(336)					(40)
				#	Vendors																	(0)						(0)
				#	Originals																(67 / 51)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		IMDb Originals (US)													co0699104 (58)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Amazon Freevee (US)													co0796766 (213)
				#		Amazon Freevee (DE)																			3205 (4)			6550
				#		Amazon Freevee (GB)																			3596 (1)			7385
				#		Freevee (US)																				2392 (26)			5865
				#
				#		IMDb Originals (US)													co0699104 (58)
				#		IMDb (US)															co0047972 (32)			923 (2)				2996
				#		IMDb Freedive (US)																			1517 (1)			2906
				#		IMDb TV (GB)																				2230 (1)			5495
				#		IMDb TV (US)																				1628 (10)			4042
				#		IMDbPro (US)														co0890032 (0)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyFreevee : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Freevee'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Freevee'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Freevee Originals'},
					'expression'	: '(free(?:vee|dive)|imdb)',
				},

				#################################################################################################################################
				# FX
				#
				#	FX (FOX eXtended) was originally owned by FOX, but is now owned by Walt Disney.
				#	It operates as its own network, independent from Disney+, and does a lot of collaborations with Hulu (FX on Hulu).
				#	At this time it seems that all FX titles are included with one of FOX companies.
				#	On IMDb the total number of titles under FOX and under FOX+FX are the same. On Trakt there is a difference.
				#
				#	Parent Companies:		Disney, Fox (previous)
				#	Content Provider:		Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(115)					(99)
				#	Networks																(579)					(105)
				#	Vendors																	(0)						(0)
				#	Originals																(46 / 178)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		FX Productions														co0216537 (66)			4 (99)				15990
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		FX																							2409 (1)			5628
				#		FX (US)																co0777254 (5)			2 (87)				88
				#		FX (GB)																co0902824 (1)
				#
				#		FX Canada															co0362128 (11)
				#		FX Italia															co0197517 (3)
				#		FX Brasil															co0157673 (2)			1885 (4)			1641
				#		FX Argentina														co0960667 (1)
				#
				#		FX Network (US)														co0060381 (299)
				#		fX Networks (US)													co0186186 (30)
				#		FX Network (GR)														co1032328 (1)
				#		FX Channel (GB)														co0263771 (1)
				#
				#		Canal FX (BR)														co0448574 (1)
				#		Canal FX Latin America (AR)											co0448575 (2)
				#
				#		FXX (US)																					4 (18)				1035
				#		FXX Network (US)													co0421362 (95)
				#		FXX Canada (CA)														co0746872 (0)
				#
				#		FXM (US)																					1642 (0)			4370
				#		FXM Network (US)													co0481858 (8)
				#		FX Movie Channel (US)												co0385924 (2)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyFx : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'FX Productions'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'FX'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'FX'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'FX Originals'},
					'expression'	: '(^fx[xm]?(?:$|[\s\-\_\.\+]*(?:network|channel|movie|production|studio|canada|brasil|argentina|italia))|canal[\s\-\_\.\+]*fx)',
				},

				#################################################################################################################################
				# Gaumont
				#
				#	The oldest extant film company in the world (1895).
				#
				#	Parent Companies:		Sidonie Dumas
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Gaumont
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Netflix
				#
				#	Content Provider:		-
				#	Content Receiver:		Netflix, NBC, French channels.
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(6207)					(1158)
				#	Networks																(0)						(0)
				#	Vendors																	(3611)					(0)
				#	Originals																(1444 / 111)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Gaumont (FR)														co0172053 (954)			1995 (741)			9
				#		Gaumont (DE)														co1053226 (2)			69335 (9)			130675
				#		Gaumont (GB)														co0844356 (4)			159271 (12)			202617
				#		Gaumont (US)																				154611 (10)			206133
				#		Gaumont American (US)												co0120389 (1)
				#
				#		Gaumont Production (FR)												co0042098 (25)			4745 (15)			45441
				#		Gaumont Production 2 (FR)											co0277376 (2)
				#		A Gaumont Production																		150081 (1)			201585
				#
				#		Gaumont Television (FR)												co0011191 (45)			1941 (36)			24554
				#		Gaumont Série Pax (FR)												co0125456 (14)			22325 (5)			9042
				#
				#		Gaumont International																		2805 (73)			7961
				#		Gaumont International Television (US)								co0353668 (19)			630 (12)			36812
				#		Gaumont International Production 2000 (FR)							co0005388 (0)
				#
				#		Gaumont Animation (FR)												co0455873 (15)			1945 (10)			79466
				#		Gaumont Animation & Family (US)										co0778046 (0)
				#
				#		Société des Etablissements L. Gaumont (FR)							co0059061 (242)			78921 (55)			135315
				#		Société Nouvelle des Établissements Gaumont (SNEG) (FR)				co0051263 (65)			5310 (47)			22396
				#		S.N.E. Gaumont (FR)													co0126294 (11)			8267 (6)			22275
				#
				#		Actualités Gaumont (BE)												co0051969 (20)
				#		Gaumont Actualités (FR)												co0374778 (3)			88654 (2)			142320
				#
				#		Gaumont Multimedia													co0054362 (3)
				#		Gaumont Multimédia (FR)												co0961384 (1)
				#
				#		Gaumont Éditions Musicales (FR)										co0112349 (7)
				#		Gaumont Española (ES)												co0002907 (3)
				#		Gaumont Images 2 (FR)												co0099681 (1)			33189 (1)			36894
				#		Casa Gaumont Barcelona (ES)											co0056284 (1)
				#		Gaumont Graphic (GB)												co0341836 (1)
				#		The Gaumont Agency (AU)												co0091513 (1)
				#		Gaumont Cinemaphonic												co0022037 (1)
				#		Edición Nacional Gaumont (ES)										co0083850 (1)
				#
				#		Gaumont British Picture Corporation (GB)							co0053065 (156)			4871 (131)			4978
				#		Gaumont-British Instructional (GB)									co0197001 (7)
				#		Gaumont British News (GB)											co0243598 (3)
				#		Gaumont British Animation											co0012779 (1)			40478 (4)			104012
				#		Gaumont-British Screen Services (GB)								co0332544 (1)			91022 (1)			144387
				#		Gaumont-Westminster (GB)											co0118687 (5)
				#
				#		Gaumont-Franco Film-Aubert (G.F.F.A) (FR)							co0059676 (52)			22722 (14)			27644
				#		Gaumont-Alphanim (FR)												co0285075 (22)			15543 (6)			39092
				#		Gaumont-Alcina (FR)													co0135492 (1)
				#		Elge Gaumont (FR)													co0726353 (1)
				#		Gaumont Robur Télévision (FR)										co0131371 (1)
				#		Gaumont-Terra-Film (AT)												co0278881 (1)
				#
				#	Other production companies.
				#
				#		Gaumont Pathé Archives (FR)											--co0459311-- (10)
				#		Studios Gaumont (FR)												--co0810592-- (1)
				#		Gaumont Pictures													--co0060516-- (0)
				#		Gaumont Production Services (FR)									--co1069831-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Gaumont (FR)														co0172053 (954)
				#		Gaumont Italia (IT)													co0036160 (64)
				#		Gaumont S.A.B. (BE)													co0140056 (22)
				#		Gaumont do Brasil (BR)												co0080245 (6)
				#		Gaumont SA (BE)														co0949530 (1)
				#
				#		Gaumont-Film (DE)													co0274195 (1)
				#		Gaumont-Film (AT)													co0241665 (1)
				#
				#		Gaumont TV (US)														co0910931 (0)
				#		Gaumont Television Us (US)											co0859868 (0)
				#
				#		Gaumont Vidéo (FR)													co0182000 (172)
				#		Gaumont Home Vidéo (FR)												co0028520 (9)
				#
				#		Gaumont Ideal (GB)													co0217840 (2)
				#		Gaumont Ideal Limited (US)											co0147769 (0)
				#
				#		Gaumont British Distributors (GB)									co0105966 (401)
				#		Gaumont British Picture Corporation of America (US)					co0026280 (86)
				#		Gaumont British Equipments (GB)										co0326260 (1)
				#
				#		Gaumont International (FR)											co0064278 (139)
				#		Gaumont Distribution (FR)											co0212919 (83)
				#		Gaumont Ges.m.b.H. (AT)												co0064878 (14)
				#		Gaumont Company (GB)												co0172122 (11)
				#		Gaumont Verleih (AT)												co0240792 (4)
				#		Gaumont-Gesellschaft (AT)											co0181164 (4)
				#		Gaumont-France Distribution (FR)									co0175932 (3)
				#		Edition Gaumont (FR)												co0301531 (1)
				#		American Gaumont (US)												co0100931 (1)
				#		Reprezentacja Wytwórni Filmów Gaumont (PL)							co0521315 (1)
				#		Exclusivité Gaumont (FR)											co0304207 (1)
				#		Fictions Gaumont (FR)												co0902798 (0)
				#
				#		Léon Gaumont (CSHH)													co0308033 (1)
				#		Leon Gaumont (HU)													co0594645 (1)
				#
				#		Gaumont-Eagle Lion (BE)												co0186581 (23)
				#		Gaumont-Eagle Lion (FR)												co0008471 (17)
				#
				#		Gaumont-Franco-Film-Aubert (GFFA) (BE)								co0864902 (18)
				#		Gaumont-Franco-Film-Aubert (FR)										co0066838 (3)
				#
				#		Gaumont & J. Arthur Rank Distribution de Films (BE)					co0398337 (8)
				#		Gaumont-J.Arthur Rank (BE)											co0173397 (2)
				#		Gaumont & J. Arthur Rank Distribution de Films (FR)					co0456755 (1)
				#
				#		Gaumont/Columbia TriStar Home Video (FR)							co0108034 (229)
				#		Gaumont/Columbia TriStar Films (FR)									co0135317 (56)
				#		Gaumont-Columbia-RCA (GCR) (FR)										co0159180 (81)
				#
				#		Gaumont Buena Vista International (GBVI) (FR)						co0033410 (263)
				#		Comptoir Ciné-Location Gaumont (FR)									co0187612 (63)
				#		Gaumont-Metro-Goldwyn (FR)											co0128844 (7)
				#		Gaumont Belas Artes (BR)											co0699827 (3)
				#		Gaumont-Pagnol (FR)													co0247165 (1)
				#		Gaumont-Kalee (GB)													co0516770 (1)
				#		Gaumont-Vale-Domovideo (IT)											co0772044 (1)
				#		Fechner Gaumont (FR)												co0108027 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyGaumont : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Gaumont Production'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Gaumont'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Gaumont Originals'}, # Not really originals, since they are produced for other networks (eg Netflix), but still add here for the Frenchies.
					'expression'	: '(gaumont)',
				},

				#################################################################################################################################
				# Google
				#
				#	Parent Companies:		Google
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Google Spotlight
				#	Owned Networks:			Google Play, Google TV
				#
				#	Streaming Services:		Google Play, Google TV
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(26)					(15)
				#	Networks																(812)					(3)
				#	Vendors																	(138)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Google Spotlight Stories											co0582980 (1)			49108 (15)			88151
				#		Google.org (US)														co0265703 (1)
				#		Google (JP)															co0944862 (1)
				#		Google Chromebooks (US)												co0678053 (1)
				#		Google ATAP (US)													co0507176 (1)
				#		Google TV (US)														co0352536 (1)
				#		Google Developer Studios (US)										co0729093 (1)
				#
				#	Other production companies.
				#
				#		Google Cloud Platform (US)											--co0881159-- (3)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Google Play																					1446 (3)			1102
				#		Google Play (DE)													co0879800 (599)
				#		Google Play (US)													co0422781 (84)
				#		Google Play (JP)													co0992738 (5)
				#		Google Play (BR)													co0625172 (5)
				#		Google Play (GB)													co0642369 (5)
				#		Google Play (IT)													co0564081 (3)
				#		Google Play (CA)													co0657283 (2)
				#		Google Play Music (US)												co0623478 (1)
				#		Google Play (PL)													co1001116 (1)
				#		Google Play (NO)													co0613563 (1)
				#		Google Play Movies (IN)												co1033988 (10)
				#
				#		Google TV (IN)														co1021372 (2)
				#		Google TV (US)														co0352536 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Google (US)															co0123378 (61)
				#		Google (GB)															co0379677 (2)
				#
				#		Google Hangouts (US)												co0487508 (7)
				#		Google Video (US)													co0552365 (2)
				#		Google Drive (US)													co1008843 (1)
				#		The Google Assistant (US)											co0680753 (1)
				#		Google Arts & Culture (US)											co0635012 (1)
				#		Google Daydream VR Platform (US)									co0628498 (1)
				#		Google Podcasts (US)												co0821394 (1)
				#
				#		Google Earth Outreach (US)											--co0523974-- (1)
				#		Google Answers (US)													--co0136894-- (1)
				#		Google Space Initiatives (US)										--co0836210-- (1)
				#		G+ Google (MX)														--co1070362-- (1)
				#		Sparky Google (US)													--co0460477-- (1)
				#		Google Flu (US)														--co0432118-- (1)
				#		Google Earth Studio (US)											--co0634943-- (1)
				#		Google Images (US)													--co1008103-- (1)
				#		Google CS Education in Media (US)									--co0785449-- (1)
				#		Google Slides (US)													--co0917341-- (0)
				#		Google Pixel (US)													--co0922034-- (0)
				#		Faksimile Google (US)												--co0911939-- (0)
				#		Google Science Fair (US)											--co0997763-- (0)
				#		Google Duo (US)														--co0732454-- (0)
				#		Google Chrome (US)													--co0818389-- (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyGoogle : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Google Spotlight'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Google Play'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Google'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(google)',
				},

				#################################################################################################################################
				# Hayu
				#
				#	Streaming service owned by NBCUniversal.
				#
				#	Parent Companies:		NBCUniversal, Comcast
				#	Content Provider:		NBC, Universal
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(0)						(0)
				#	Networks																(26)					(0)
				#	Vendors																	(0)						(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Hayu (GB)															co0764723 (26)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyHayu : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Hayu'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Hayu'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(hayu)',
				},

				#################################################################################################################################
				# HBO
				#
				#	Created and owned by Warner, it has a lot of collaborations with, and receives content from, Warner subsidiaries.
				#	HBO used different names for their streaming service (HBO HD, HBO on Demand, HBO Go, HBO Now, HBO Max).
				#	The new "Max" is technically not "HBO Max", but owned directly by Warner Bros Discovery, but most of its content
				#	is still provided by HBO and in some areas it is still labeled as "HBO Max".
				#
				#	Parent Companies:		Warner Bros Discovery
				#	Sibling Companies:		Cinemax, Magnolia
				#	Child Companies:		-
				#
				#	Owned Studios:			Bad Wolf (partial), TriStar (partial)
				#	Owned Networks:			Comedy Central (partial)
				#
				#	Streaming Services:		(HBO) Max
				#	Collaborating Partners:	Discovery, Cinemax, Magnolia, BBC, Showtime
				#
				#	Content Provider:		On the new "Max" directly from:
				#								Warner Bros, Discovery, HBO, CNN, Cartoon Network, Adult Swim, Animal Planet, TBS, TNT, TCM, TLC
				#								Boomerang, DC Entertainment, Cooking Channel, Magnolia, TruTV, Turner, Eurosport
				#							On the new "Max" indirectly from 3rd parties:
				#								Amazon, MGM, United Artists, AMC, A24, All3Media, BBC, ITV, Sky, Bad Robot, Castle Rock, Shout!
				#								The Criterion Collection, Lionsgate, Orion, Paramount, Sony, Universal, NBC, Entertainment One
				#	Content Receiver:		Max, Amazon Prime (limited), YouTube (limited), Hulu (previous at least)
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1005)					(1436)
				#	Networks																(7253)					(766)
				#	Vendors																	(1881)					(126)
				#	Originals																(629 / 969)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		HBO																							1030 (693)			3268
				#		HBO Films															co0005861 (86)			2531 (187)			7429
				#		HBO Sports																					6471 (76)			6751
				#		HBO Latin America Group												co0199013 (44)			1357 (28)			44618
				#		HBO Asia															co0229386 (26)			88810 (20)			142414
				#		HBO Premiere Films (US)												co0074198 (23)
				#		HBO Entertainment													co0284741 (22)
				#		HBO Independent Productions											co0002401 (14)			2205 (10)			21222
				#		HBO Downtown Productions											co0036039 (13)			721 (6)				67207
				#		HBO Pictures														co0095169 (11)
				#		HBO NYC Productions (US)											co0149507 (7)
				#		HBO Studio Productions												co0080413 (4)
				#		HBO Creative Services (US)											co0112313 (3)
				#		HBO Studio Services (US)											co0768628 (2)
				#		HBO Showcase (US)													co0273255 (2)
				#		HBO Animation														co0051804 (1)
				#		HBO Project Knowledge (US)											co0179190 (0)
				#		HBO Family Programming (US)											co0728364 (0)
				#
				#		HBO Documentary Films												co0139821 (221)			2764 (486)			14914
				#		HBO Theatrical Documentary (US)										co0068811 (2)
				#
				#		HBO Europe																					2866 (56)			48582
				#		HBO Europe (HU)														co0391378 (27)
				#		HBO Europe (CZ)														co0490785 (22)			81327 (13)			136561
				#		HBO Europe (PL)														co0561930 (20)
				#		HBO Europe (RO)														co0625707 (13)
				#
				#		HBO Romania (RO)													co0281949 (27)			32065 (11)			13670
				#		HBO Czech Republic (CZ)												co0320834 (9)
				#
				#		HBO Latin America Originals											co0440095 (11)			1357 (29)			44618
				#		Home Box Office Ole Originals										co0193395 (5)
				#		HBO Original Programming											co0095172 (3)
				#		HBO Europe Original Programming (GB)								co0478999 (2)
				#		HBO Original (RO)													co0363290 (1)
				#
				#		WarnerMax															co0784743 (8)			83538 (7)			138252
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		HBO (US)															co0008693 (2021)		1 (349)				49
				#
				#		HBO Max (US)														co0754095 (3153)		514 (119)			3186
				#		HBO Max																						2224 (48)			5484
				#		HBO Max (ES)																				2227 (24)			5479
				#		HBO Max																						2228 (7)			5485
				#		HBO Max (RO)																				2346 (4)			5750
				#		HBO Max (PL)																				2358 (3)			5764
				#		HBO Max (HU)																				2351 (2)			5666
				#		HBO Max (CZ)																				2394 (1)			5836
				#		HBO Max Central Europe (US)											co0869157 (17)
				#
				#		Max (US)															co0095413 (182)			2934 (76)			6783
				#		Max																							3563 (13)			7375
				#		Max (ES)																					3897 (7)			7560
				#		Max																							3826 (4)			7526
				#		Max																							3757 (2)			7492
				#		Max (AU)																					1098 (1)			505
				#		Max																							3564 (0)			7375
				#		MAX International (US)												co1020089 (1)
				#
				#		HBO Go (PL)															co0777335 (11)
				#		HBO Go (TW)															co1010749 (2)			3551 (1)			7368
				#		HBO Go (HK)															co1010750 (1)
				#		HBO Go (PH)																					2844 (1)			6305
				#
				#		HBO NOW (US)														co0644177 (9)
				#
				#		HBO 3 (US)															co0909975 (25)
				#		HBO 2 (US)															co0913428 (10)
				#
				#		HBO Latino (US)														co0140098 (10)
				#		HBO Latino (EC)														co0092268 (3)
				#
				#		HBO Comedy (US)														co0915296 (1)
				#		HBO Signature (HK)													co0312842 (1)
				#		HBO Zone (US)														co0167627 (44)
				#		HBO Family (US)														co0006163 (28)			1585 (7)			2593
				#
				#		HBO Europe																					487 (30)			1129
				#		HBO Brasil (BR)																				1355 (30)			3618
				#		HBO Asia																					212 (25)			1303
				#		HBO Latin America (AR)																		340 (17)			1089
				#		HBO España (ES)																				1364 (12)			3877
				#		HBO Nordic																					83 (7)				1062
				#		HBO Canada																					244 (5)				1590
				#		HBO (CZ)																					1780 (1)			3308
				#		HBO Mundi (BR)																				2360 (1)			5646
				#
				#		HBO/Cinemax Documentary (US)										co0123742 (11)
				#		HBO / Cinemax (US)													co0368145 (7)
				#
				#	These are other comapines named "MAX".
				#
				#		Max (IN)															--co0323158-- (10)
				#		MAX (NO)															--co0365918-- (7)
				#		MAX (AU)															--co0812191-- (2)
				#		MAX (NO)															--co0067922-- (7)		--1757-- (2)		4383
				#		MAX (NL)																					--500-- (27)		1074
				#		MAX																							--2184-- (0)		5360
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		HBO Europe																					487 (30)			1129
				#		HBO Europe (BG)														co0638197 (7)
				#		HBO Europe (SI)														co0638196 (6)
				#		HBO Europe (ES)														co0736914 (6)
				#		HBO Europe (RS)														co0638200 (5)
				#		HBO Europe (MD)														co0638198 (5)
				#		HBO Europe (HR)														co0638199 (4)
				#		HBO Europe (ME)														co0638201 (4)
				#		HBO Europe (MK)														co0638203 (1)
				#
				#		HBO Nordic (SE)														co0450274 (13)
				#		HBO Nordic (NO)														co0622841 (11)
				#		HBO Nordic (DK)														co0625624 (8)
				#		HBO Nordic (FI)														co0625625 (7)
				#		HBO Nordic																					83 (7)				1062
				#
				#		HBO Hungary (HU)													co0101990 (282)
				#		HBO Polska (PL)														co0113668 (149)
				#		HBO España (ES)														co0680232 (113)			1364 (12)			3877
				#		HBO Central Europe (HU)												co0289307 (27)
				#		HBO Asia															co0229386 (26)			212 (25)			1303
				#		HBO Brasil (BR)														co0891644 (3)			1355 (30)			3618
				#		HBO Bulgaria (BG)													co0487453 (6)
				#		HBO Canada																					244 (5)				1590
				#		HBO (CZ)																					1780 (1)			3308
				#
				#		HBO Video (US)														co0248784 (70)
				#		HBO Video (GB)														co0148466 (1)
				#		HBO Home Entertainment (US)											co0306346 (24)
				#		HBO Home Entertainment (GB)											co0620979 (1)
				#		HBO Home Video (US)													co0703486 (7)
				#
				#		HBO Pacific Partners of Netherlands Antilles (IN)					co0840644 (122)
				#		HBO Latin America (AR)												co0112024 (116)			340 (17)			1089
				#		HBO Sports															co0033562 (42)
				#		HBO Documentary (US)												co0037614 (40)
				#		HBO Defined (IN)													co0450282 (2)
				#		HBO Media Operations and Distribution (US)							co0484616 (1)
				#		HBO Mundi (BR)																				2360 (1)			5646
				#		HBO Kids (US)														co0640662 (0)
				#
				#		Home Box Office Home Video (HBO) (US)								co0077623 (326)
				#		Home Box Office Latin America (HBO) (BR)							co0178216 (24)
				#		Home Box Office Premiere Films										co0035311 (2)
				#		Home Box Office Home Video (HBO) (TR)								co0720309 (1)
				#		Home Box Office Canada 2 (CA)										co0721140 (0)
				#
				#		HBO/Cannon Video (US)												co0114708 (42)
				#		Thorn EMI/HBO Video (US)											co0031966 (35)
				#		HBO Adria (HR)														co0799745 (1)
				#		HBO / Shout (US)													co0207690 (1)
				#		TBS/HBO Comedy Festival (US)										co0568014 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyHbo : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'HBO Productions'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'HBO Max'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'HBO'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'HBO Originals'},
					'expression'	: '(hbo|home[\s\-\_\.\+]*box[\s\-\_\.\+]*office|^max(?:[\s\-\_\.\+]*international)?$|warner[\s\-\_\.\+]*max)',
				},

				#################################################################################################################################
				# History Channel
				#
				#	Most production done by A&E Studios, also owned by Disney.
				#
				#	Parent Companies:		Disney
				#	Sibling Companies:		NatGeo
				#	Child Companies:		-
				#
				#	Owned Studios:			History Channel
				#	Owned Networks:			History Channel
				#
				#	Streaming Services:		Disney+
				#	Collaborating Partners:	A&E
				#
				#	Content Provider:		-
				#	Content Receiver:		A&E Studios, Disney
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1230)					(224)
				#	Networks																(1358)					(498)
				#	Vendors																	(3)						(0)
				#	Originals																(698 / 576)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		History Channel														co0003716 (442)			13860 (224)			3507
				#		History Channel International (US)									co0262451 (5)
				#		The History Channel Iberia (ES)										co0579401 (4)
				#		History Television Network Productions (H-TV) (US)					co0118166 (2)
				#
				#	Other companies with the same name.
				#
				#		Foxtel History Channel (AU)											--co0919693-- (2)
				#		Historia (JP)														--co0943288-- (1)
				#		Historia (FR)														--co0364739-- (1)
				#		Historia Films (US)													--co0400241-- (10)
				#		Canal de Historia (ES)												--co0349173-- (10)
				#		Historia Films (KE)													--co0459553-- (5)
				#		Histoire (FR)														--co0131280-- (36)
				#		Historia Productions (US)											--co0708007-- (0)
				#		TVN Discovery Historia (PL)											--co0986413-- (1)
				#		Historia-Film (AT)													--co0195936-- (1)
				#		Canal Historia Iberia (ES)											--co0581022-- (1)
				#		Historiathek (DE)													--co0859994-- (1)
				#		History D&C Entertainment (KR)										--co0888484-- (2)
				#		History Underground (US)											--co0929476-- (1)
				#		History Doc (GR)													--co0736484-- (1)
				#		History Dreams (GB)													--co0104139-- (1)
				#		History Media (DE)													--co0232208-- (4)
				#		History Productions Limited											--co0016246-- (1)
				#		History Films (US)													--co0314375-- (5)
				#		History Productions (GB)											--co0291305-- (0)
				#		History Film (DE)													--co0658291-- (1)
				#		History Doc TV (GB)													--co0589892-- (1)
				#		History SA (AU)														--co0665290-- (1)
				#		History Television International (GB)								--co0942777-- (1)
				#		History film production (ET)										--co0945844-- (1)
				#		History Hit (GB)													--co0926878-- (3)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		History (US)																				198 (378)			65
				#		History (NL)														co0342233 (64)
				#		History (GB)														co0308904 (28)			1000 (61)			1755
				#		History (CA)														co0379713 (20)			293 (20)			2360
				#		History (DE)														co0625848 (19)			3673 (2)			7429
				#		History (SE)														co0688432 (2)
				#		History (IT)														co0733710 (2)
				#		History (BR)																				2664 (2)			5433
				#		History (AU)														co0655111 (1)			1018 (6)			2382
				#		History (PL)														co0500387 (1)
				#		History (HU)														co0510420 (1)
				#		History (DK)														co0672898 (1)
				#		History																						1400 (0)			3934
				#		History (JP)																				2455 (0)			5922
				#
				#		Historia (CA)																				1334 (22)			1245
				#		Historia (ES)																				1715 (8)			3010
				#		Historia (FR)																				1373 (0)			3890
				#
				#		History Channel (US)												co0003716 (442)
				#		History Channel (DE)												co0889133 (38)
				#		History Channel Japan (JP)											co0626674 (7)
				#		History Channel Espanol (US)										co0262373 (5)
				#		History Channel Asia (SG)											co0473691 (5)
				#		History Channel Italia (IT)																	2711 (2)			1354
				#		History Channel Africa (ZA)											co1048877 (1)
				#		History Channel (CA)												co0904694 (1)
				#		History Channel (AU)												co1039714 (1)
				#
				#		The History Channel Latin America (US)								co0524434 (7)
				#		The History Channel (IN)											co0880224 (3)
				#
				#		History Play (DE)													co0995097 (7)
				#		History TV 18 (IN)													co0665299 (7)
				#		History HD (DE)														co1057532 (1)
				#		History Latin America (US)											co0522483 (0)
				#
				#	Other companies with the same name.
				#
				#		History Television (CA)												--co0031218-- (43)
				#		History Partners (US)												--co0533930-- (0)
				#		Uniform History YouTube Channel (US)								--co0930110-- (0)
				#		Kidz History (US)													--co0234684-- (1)
				#		Sky History Channel (GB)											--co0825565-- (26)
				#		Fox History and Entertainment Channel (IN)							--co0279054-- (2)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		History Channel Video (US)											co0376124 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyHistory : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'History Productions'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'History Channel'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'History'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'History Originals'},
					'expression'	: '((?:^|the[\s\-\_\.\+]*)histor(?:y|ia)(?:$|[\s\-\_\.\+]*(?:channel|television|tv|play|hd|latin)))',
				},

				#################################################################################################################################
				# Hulu
				#
				#	Hulu was a joint venture between News Corporation and NBCUniversal, but since 2023 is fully owned by Disney.
				#	Hulu does not create its own content, but gets supplied from other companies.
				#	Hulu is owned and provided by Disney, but also receives content from Star, Fx, etc.
				#	Sometimes Hulu Originals also appear on other platforms like Netflix, Amazon, and Apple (eg: tt1844624, tt5834204).
				#	https://en.wikipedia.org/wiki/Hulu
				#
				#	Owned by:
				#		Current:			Disney, Nippon TV (Hulu Japan only)
				#		Previous:			News Corporation, NBCUniversal, Warner (partial)
				#
				#	Content provided by:
				#		Current:			Disney, Star, Hotstar, FX, Fox, NatGeo, ABC, Freeform, Lucasfilm, Marvel,
				#							Hollywood Pictures, Touchstone, 20th Century, Searchlight, Screen Media,
				#							Lionsgate, Summit Entertainment, Roadside Attractions, Entertainment One,
				#							AMC, IFC, HIDIVE, Sundance TV, We TV
				#							NBC, Universal, Syfy, Oxygen, Telemundo, E!,
				#							Paramount, BET, CBS, Comedy Central, MTV, Nickelodeon, VH1,
				#							Sony, Aniplex, Columbia, TriStar, Crunchyroll,
				#							Warner, Adult Swim, All3Media, Animal Planet, Boomerang, Cartoon Network, CNN, Magnolia
				#							HBO, Discovery, Cinemax,
				#							PBS, Amazon (almost none)
				#							Many others, often subsidiaries of Disney or one of the other content providers.
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(43)					(0)
				#	Networks																(1294)					(303)
				#	Vendors																	(0)						(0)
				#	Originals																(225 / 515)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Hulu Originals														co0687042 (31)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Hulu																co0218858 (880)			87 (268)			453
				#		Hulu Japan															co0381648 (140)			635 (35)			1772
				#		Hulu Originals														co0687042 (31)
				#		Hulu Kids															co0630515 (2)
				#		Hulu Documentary Films												co0588218 (2)
				#		Hulu on Disney+																				3710 (0)			7460
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		MGM/Hulu															co0857173 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyHulu : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Hulu'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Hulu'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Hulu Originals'},
					'expression'	: '(hulu)',
				},

				#################################################################################################################################
				# ITV
				#
				#	ITV, legally known as Channel 3, was created as competition to BBC and Channel 4.
				#	Unlike BBC and Channel 4, ITV seems to be privatly owned.
				#	In Scottland it is branded as STV, and in Ireland as UTV.
				#
				#	Parent Companies:		ITV plc, STV Group
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			ITV Studios
				#	Owned Networks:			ITV, STV, UTV
				#
				#	Streaming Services:		ITVX
				#	Collaborating Partners:	BBC, Channel 4, ITV America (Fox, NBC, CBS, MTV), ITV Germany (RTL, ARD), ITV France (TF1)
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1639)					(824)
				#	Networks																(6185)					(1941)
				#	Vendors																	(268)					(0)
				#	Originals																(1600 / 3752)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		ITV Studios (GB) 													co0269801 (277)			1332 (191)			24546
				#		ITV Studios Germany (DE) 											co0367108 (26)			12737 (18)			101412
				#		ITV Studios Norway (NO) 											co0551019 (17)			2236 (12)			81652
				#		ITV Studios Australia (AU) 											co0444635 (16)			489 (15)			73038
				#		ITV Studios Netherlands (NL) 										co0824500 (12)			82190 (10)			137204
				#		ITV Studios Finland (FI) 											co0499176 (11)			56999 (5)			74697
				#		ITV Studios Sweden (SE) 											co0899320 (7)			69163 (11)			118510
				#		ITV Studios America (US) 											co0693477 (7)			194 (34)			21040
				#		ITV Studios France (FR) 											co0444747 (6)			19698 (24)			117235
				#
				#		ITV America (US) 													co0325317 (64)
				#		ITV USA (US) 														co0579802 (2)
				#
				#		ITV (GB) 																					2394 (363)			3448
				#		ITV Cymru Wales (GB) 												co0508070 (6)			112075 (3)			162698
				#		ITV Yorkshire (GB) 													co0898028 (1)
				#
				#		ITV Productions (GB) 												co0178626 (100)			14352 (27)			71541
				#		ITV Productions (Granada) (GB) 										co0595686 (1)
				#		ITV Productions Limited (GB) 										co0435936 (1)
				#		ITV Television Productions (GB) 									co0423164 (0)
				#
				#		ITV Entertainment (US) 												co0592609 (14)			116493 (12)			167492
				#		ITV Studios Entertainment (GB) 										co0512531 (8)
				#		ITV Global Entertainment 																	16749 (7)			67330
				#
				#		ITV Sport (GB) 														co0323983 (23)
				#		ITV Sports (GB) 													co0121698 (1)
				#
				#		ITV Movie (IT) 														co0518213 (5)			102835 (1)			143021
				#		ITV News & Current Affairs (GB) 									co0644045 (5)
				#		ITV Breakfast (GB) 													co0659706 (3)
				#		Potato part of ITV Studios (GB) 									co0572222 (2)
				#		Itv Signpost (GB) 													co0667771 (2)
				#		ITV Tyne Tees News (GB) 											co0795301 (1)
				#		ITV Film (GB) 														co0939606 (1)
				#		ITV Daytime (GB) 													co0718789 (1)
				#		ITV News (US) 														co0974673 (1)
				#		ITV Fixers (GB) 													co0339733 (1)
				#
				#		Scottish Television (STV) (GB) 										co0103509 (60)			2365 (18)			13766
				#		STV Productions (GB) 												co0271278 (56)			2367 (22)			75600
				#		Scottish Television Enterprises 															71 (22)				56064
				#		Scottish Television (STV) 																	2365 (18)			13766
				#		STV Productions / MG Alba (GB) 										co0370371 (5)
				#		STV - Scottish Television (GB) 										co0836810 (2)
				#		STV Studios (GB) 													co1006968 (1)
				#		British STV Film Enterprises 										co0046794 (1)
				#		stv.tv (GB) 														co0248792 (0)
				#
				#		SMG Productions (GB) 												co0104311 (16)			2366 (5)			77418
				#		Scottish Media Group (SMG) (GB) 									co0102232 (4)
				#
				#		Ulster Television (UTV) (GB) 										co0062263 (25)			43445 (5)			57907
				#
				#		Central Independent Television (GB) 								co0103328 (133)
				#		ITV Central (GB) 																			22623 (42)			5238
				#
				#		Southern Independent Television (GB) 								co1060623 (1)
				#
				#	Other companies with the same name.
				#
				#		STV Production (DK) 												--co0080995-- (47)
				#		STV Film Company (RU) 												--co0112464-- (6)
				#		STV Production Norway AS (NO)										--co0771418-- (2)
				#		UTV Studios (US) 													--co0685097-- (1)
				#		UTV Productions (GB) 												--co0871680-- (1)
				#		Independent Television (ITC) (GB)									--co0395221-- (1)
				#
				#	Other production companies.
				#
				#		Independent Television News (ITN) (GB)								--co0104098-- (37)
				#		ITV Studios Bovingdon (GB) 											--co0779978-- (4)
				#		ITV News Granada Reports (GB) 										--co0660703-- (3)
				#		ITV, a division of Western TV Group Ltd. 							--co0052283-- (1)
				#		ITV Films (GB) 														--co0223432-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		ITV - Independent Television (GB) 									co0015194 (2811)
				#		Independent Television (ITV) (GB) 									co0940556 (97)
				#		ITV (GB) 																					68 (1659)			9
				#		ITV (GB) 																					3435 (2)			7316
				#		Itv (GB) 															co0777792 (11)
				#		ITV. (GB) 															co0786320 (4)
				#
				#		ITV 1 (GB) 															co0356585 (278)
				#		ITV1 (GB) 															co0832896 (70)
				#
				#		ITV2 (GB) 															co0832898 (40)			207 (83)			149
				#		ITV 2 (GB) 															co0260257 (68)
				#
				#		ITV3 (GB) 															co0262036 (11)			1001 (8)			590
				#		ITV4 (GB) 															co0165745 (83)			1138 (29)			261
				#
				#		ITV Wales (GB) 														co0139023 (20)
				#		ITV-West (GB) 														co0225802 (11)
				#		ITV Central (GB) 													co0209174 (6)
				#		ITV Westcountry (GB) 												co0234812 (6)
				#		ITV Granada (GB) 													co0862078 (3)
				#		ITV Anglia (GB) 													co0617637 (2)
				#		ITV London (GB) 													co0862080 (1)
				#		ITV Cymru Wales (GB) 																		3877 (1)			7553
				#
				#		ITVX (GB) 															co0911004 (449)			2502 (50)			5871
				#		ITVX Kids (GB) 														co0984960 (44)
				#
				#		ITV Hub (GB) 														co0688964 (103)			2369 (0)			5812
				#		ITV Hub 																					3590 (1)			7383
				#
				#		ITV Plc (GB) 														co0836808 (1)
				#		ITV Choice (CF) 													co0701469 (1)
				#		ITV Choice (ZA) 													co0749906 (1)
				#
				#		ITV Network (GB) 													co0228738 (35)
				#		ITVBe (GB) 															co0533816 (30)			605 (19)			1159
				#		ITV Play (GB) 														co0177163 (6)			3579 (16)			307
				#		ITV Encore (GB) 													co0661472 (2)			113 (3)				3187
				#		ITV Digital (GB) 													co0038954 (3)
				#		ITV Broadcasting (GB) 												co0265624 (2)
				#		Itv Woo (GB) 														co0916015 (1)
				#
				#		Children's Independent Television (CiTV) (GB) 						co0104833 (222)
				#		CITV Channel (GB) 													co0832781 (44)
				#		CITV (GB) 															co0600871 (30)			167 (75)			112
				#		CITV - Children's Independent Television (GB) 						co0662116 (4)
				#
				#		STV (GB) 															co0047173 (3)			318 (26)			148
				#		STV2 (GB) 															co0732240 (1)
				#		STV Player (GB) 													co0986030 (1)
				#
				#		UTV (IE) 																					329 (4)				151
				#		UTV - Ulster Television (GB) 										co0836774 (3)
				#		UTV Ireland (IE) 													co0743872 (3)
				#
				#		Granada Sky Broadcasting (GB)										co0122767 (5)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		ITV Studios Global Entertainment (GB) 								co0382999 (78)
				#		ITV Studios Home Entertainment (GB) 								co0312028 (21)
				#		ITV Studios Global Distribution (GB) 								co0980080 (3)
				#		ITV Studios (Granada Productions) (US) 								co0276713 (3)
				#		ITV Studios (CA) 													co0951620 (0)
				#		ITV Studios, Cardiff (GB) 											co1066271 (0)
				#
				#		ITV DVD (GB) 														co0195491 (34)
				#		ITV Global Entertainment (GB) 										co0260221 (19)
				#		ITV Mobile (GB) 													co0496248 (1)
				#		ITV Box Office (GB) 												co0658525 (1)
				#		ITV Technology North (GB) 											co0987704 (1)
				#		ITV Meridian News (GB) 												co1019849 (1)
				#		ITV Regions (GB) 													co0473492 (0)
				#		ITV News Graphics Hub (GB) 											co0975815 (0)
				#		ITV (FI) 															co0913255 (0)
				#		ITV Racing (GB) 													co0735462 (0)
				#
				#		The Perivale Archive for ITV Studios Global Entertainment (GB) 		co0589309 (1)
				#		ITV Archive National Library of Wales (GB) 							co0840012 (1)
				#
				#		STV Group (GB) 														co0592953 (1)
				#		SMG Broadcast and Event Solutions (GB) 								co0158907 (1)
				#
				#		UTV Communications (UK) Ltd. (GB) 									co0169176 (3)
				#		UTV Media (GB) 														co0945425 (1)
				#		ITN Source / UTV (GB) 												co0596155 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyItv : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ITV Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'ITV'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ITV'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ITV Originals'},
					'expression'	: '(c?itv(?:\d|x|be)?|^(?:(?:children(?:\'?s)?|central|northern|southern)[\s\-\_\.\+]*)?independent[\s\-\_\.\+]*(?:television|tv)(?:$|[\s\-\_\.\+]*(?:news))|stv\d?|scottish[\s\-\_\.\+]*(?:television|tv)|smg|utv\d?|scottish[\s\-\_\.\+]*media[\s\-\_\.\+]*group|ulster[\s\-\_\.\+]*(?:television|tv)|granada[\s\-\_\.\+]*sky)',
				},

				#################################################################################################################################
				# Lionsgate
				#
				#	Lionsgate+ was previously named Starzplay.
				#	Lionsgate+ mostly operated in non-US countries, but has since seemed to have stopped operating in most countries.
				#	They probably focus their VOD through Starz now.
				#	There don't really seem to be Lionsgate+ originals, only Starz originals.
				#
				#	Parent Companies:		Lionsgate
				#	Sibling Companies:		Starz
				#	Child Companies:		-
				#
				#	Owned Studios:			Lionsgate Studios, Artisan Entertainment (previous)
				#	Owned Networks:			Starz
				#
				#	Streaming Services:		Starz
				#	Collaborating Partners:	MGM+ (initially MGM+Lionsgate+Paramount)
				#
				#	Content Provider:		Starz
				#	Content Receiver:		Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(2067)					(749)
				#	Networks																(2082)					(7)
				#	Vendors																	(1930)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Lionsgate Films (US)												co0060306 (1617)
				#		Lions Gate Films (US)																		4867 (97)			35
				#		Lion's Gate Films (US)												co0306113 (15)			102047 (14)			153682
				#
				#		Lionsgate Television (CA)											co0026995 (124)
				#		Lionsgate Television (US)																	12 (120)			28523
				#		Lions Gate Television (CA)											co0188462 (25)
				#		Lionsgate Television (GB)																	173996 (2)			224800
				#
				#		Lionsgate UK TV (GB)												co0592395 (6)
				#		Lionsgate Television/NBC (US)										co0857626 (5)
				#		Lionsgate Alternative Television (US)								co1042265 (2)			173852 (1)			224652
				#
				#		Lionsgate Productions (US)											co0006881 (37)
				#		Lionsgate Productions (CA)											co0331257 (1)
				#
				#		Lionsgate (US)																				538 (509)			1632
				#		Lions Gate (CN)														co1064776 (1)
				#
				#		Lions Gate Entertainment (US)										co0086772 (38)
				#		Lions Gate Family Entertainment (US)								co0150906 (4)
				#
				#		Lions Gate Properties (US)											co0888885 (1)
				#		Lionsgate Interactive Ventures & Games (US)							co0757364 (1)
				#
				#		Lionsgate Premiere (US)												--co0530439-- (47)		19564 (14)			85885
				#
				#		Lionsgate Sound (US)												--co0975629-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Lionsgate+																					2701 (3)			6293
				#		Lionsgate+ (GB)														co0983801 (3)
				#		Lionsgate+ (ES)																				2638 (0)			6220
				#		Lionsgate+ (DE)																				3632 (0)			6221
				#
				#		Lionsgate Premiere (US)												co0530439 (47)
				#		Lionsgate Play (IN)													co0850058 (10)			2229 (4)			3464
				#		Lionsgate Television																		3166 (0)			7112
				#
				#		Lions Gate Entertainment (US)										co0086772 (38)
				#		Lions Gate Entertainment (CA)										co0580785 (4)
				#
				#		Lionsgate Films (US)												co0060306 (1617)
				#		Lions Gate Films (CA)												co0129819 (32)
				#		Lions Gate Films (GB)												co0183764 (5)
				#
				#		Lionsgate UK (GB)													co0179392 (306)
				#		Lionsgate (IE)														co0807819 (20)
				#		Lionsgate Australia (AU)											co0199862 (11)
				#		Lionsgate India (IN)												co0811073 (11)
				#
				#		Lions Gate International (US)										co0165815 (10)
				#		Lionsgate International (US)										co0732499 (2)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Lionsgate Home Entertainment (US)									co0292909 (1047)
				#		Lionsgate Home Entertainment (GB)									co0292919 (218)
				#		Lions Gate Home Entertainment (US)									co1021057 (9)
				#		Lions Gate Home Entertainment (CA)									co1020766 (6)
				#		Lionsgate Home Entertainment (BE)									co0363154 (1)
				#
				#		Lions Gate Films Home Entertainment (US)							co0082557 (520)
				#		Lions Gate Films Home Entertainment (CA)							co0301387 (45)
				#		Lions Gate Films Home Entertainment (AU)							co0292916 (4)
				#
				#		Lionsgate Worldwide Television Distribution Group (US)				co1013271 (1)
				#		NBC/Lionsgate (US)													co1042082 (0)
				#
				#		Lions Gate Studios (CA)												--co0017975-- (8)
				#		Lions Gate Jamatkhana (CA)											--co0725807-- (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyLionsgate : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Lionsgate Films'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Lionsgate+'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Lionsgate'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(lion\'?s[\s\-\_\.\+]*gate)',
				},

				#################################################################################################################################
				# Lucasfilm
				#
				#	Parent Companies:		Disney
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Lucasfilm
				#	Owned Networks:			-
				#
				#	Streaming Services:		Disney+, Hulu
				#	Collaborating Partners:	Disney
				#
				#	Content Provider:		-
				#	Content Receiver:		Disney, Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(256)					(210)
				#	Networks																(0)						(0)
				#	Vendors																	(2)						(0)
				#	Originals																(75 / 52)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Lucasfilm (US)														co0071326 (144)			174 (224)			1
				#
				#		Lucasfilm Animation (US)											co0196838 (12)			186 (30)			108270
				#		Lucasfilm Animation Singapore (SG)									co0243324 (3)
				#
				#		Lucasfilm Television (US)											co0034535 (1)
				#		Lucasfilm Games (US)												co0396757 (1)
				#		Lucasfilm Commercial Productions (US)								co0634381 (0)
				#
				#	Other production companies.
				#
				#		LucasArts Entertainment Company (US)								--co0019779-- (3)
				#		Lucas Arts/ Day 1 Studios (US)										--co0241636-- (0)
				#		LucasArts Editing System (US)										--co0152703-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Lucasfilm Archives (US)												co0134604 (1)
				#		Lucasfilm Research Library (US)										co0135295 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyLucasfilm : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Lucasfilm Productions'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Lucasfilm'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Lucasfilm Originals'},
					'expression'	: '(lucasfilm)',
				},

				#################################################################################################################################
				# Marvel
				#
				#	Parent Companies:		Disney, Marvel Entertainment (previous)
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Marvel Studios
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Disney
				#
				#	Content Provider:		-
				#	Content Receiver:		Disney+, Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(401)					(319)
				#	Networks																(0)						(0)
				#	Vendors																	(57)					(0)
				#	Originals																(120 / 173)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Marvel Entertainment												co0047120 (92)			183 (52)			7505
				#		Marvel Studios														co0051941 (84)			181 (138)			420
				#		Marvel Productions													co0106768 (46)			46 (45)				2301
				#		Marvel Enterprises													co0095134 (30)			45 (18)				19551
				#		Marvel Animation													co0249290 (20)			974 (40)			13252
				#		Marvel Television													co0377521 (19)			146 (20)			38679
				#		Marvel Entertainment Group											co0578069 (16)			109306 (6)			160251
				#		Marvel New Media													co0741611 (4)			3225 (5)			125136
				#		Marvel Films																				2483 (4)			108634
				#		Marvel Knights														co0255123 (2)			7159 (19)			11106
				#		Marvel Productions Inc.												co0014418 (2)
				#		Marvel Animation and Family Entertainment							co0761154 (2)
				#		MVL Incredible Productions											co0312886 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Marvel Characters (US)												co0133841 (8)
				#		Marvel Audio Drama Universe											co0782734 (1)
				#		Marvel.com (US)														co0672091 (1)
				#		Marvel Digital Support (US)											co0501997 (1)
				#		Marvel Faniverse (US)												co0597450 (0)
				#		Marvel Family Entertainment (US)									co0769644 (0)
				#		Marvel Comics Music (US)											co0345534 (0)
				#		MVL Film Finance (US)												co0276246 (0)
				#
				#	 Only the comic books.
				#
				#		Marvel Comics														co0131570 (29)
				#		Marvel/Malibu Comics (US)											co0013122 (5)
				#		Marvel Digital Comics												co0310115 (1)
				#		Marvel Comics Group (US)											co0390765 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyMarvel : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Marvel Studios'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Marvel'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Marvel Originals'},
					'expression'	: '((?:marvel|mvl)(?:$|[\s\-\_\.\+\/]))',
				},

				#################################################################################################################################
				# Metro Goldwyn Mayer
				#
				#	Parent Companies:		Amazon
				#	Sibling Companies:		Amazon Prime, Amazon Freevee
				#	Child Companies:		-
				#
				#	Owned Studios:			MGM Studios, Orion Pictures, Samuel Goldwyn Company, United Artists
				#	Owned Networks:			MGM+ (initially MGM+Lionsgate+Paramount), Epix
				#
				#	Streaming Services:		MGM+, Epix(renamed to MGM+), Amazon Prime
				#	Collaborating Partners:	Amazon
				#
				#	Content Provider:		Amazon, Apple TV, Roku, YouTube TV
				#	Content Receiver:		Hulu (few tt5834204)
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(5950)					(3279)
				#	Networks																(200)					(50)
				#	Vendors																	(7854)					(0)
				#	Originals																(165 / 99)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Metro-Goldwyn-Mayer													co0007143 (3263)		123 (2769)			21
				#		Metro-Goldwyn-Mayer British Studios									co0071784 (56)			21264 (64)			5579
				#		Metro-Goldwyn-Mayer Animation										co0094507 (9)			29551 (9)			40147
				#		Metro-Goldwyn-Mayer Television										co0033274 (4)
				#		Metro Goldwyn Mayer Home Entertainment								co0784982 (1)
				#
				#		MGM																							81503 (55)			136673
				#		MGM Television														co0071026 (210)			236 (188)			2230
				#		MGM Home Entertainment																		9864 (81)			6434
				#		MGM+ Studios														co1041306 (3)			140095 (8)			190164
				#		MGM Alternative														co1002105 (4)			1463 (8)			89422
				#		MGM Cartoon Studio													co0637869 (3)
				#		MGM International TV Productions									co0118337 (2)
				#		MGM Family Entertainment											co0014753 (2)			89259 (2)			142842
				#		MGM Telecommunications												co0072132 (2)			26288 (1)			91286
				#		MGM Worldwide Television Productions								co0129775 (2)
				#		MGM Animation/Visual Arts											co0756630 (2)
				#		MGM Global Holdings													co0217741 (1)			21495 (1)			57749
				#		MGM Enterprises														co0390374 (1)			72762 (2)			117635
				#
				#		Epix																						2269 (29)			6805
				#		Epix Film Production (US)											co0137531 (2)
				#		Epix Studios (CA)													co0351819 (9)
				#
				#		Screenpix															co0054424 (1)
				#
				#		Amazon MGM Studios													co1025982 (99)			158509 (87)			210099
				#		MGM/UA Television													co0108881 (38)			83 (26)				10278
				#		MGM/UA Family Entertainment																	160118 (2)			211614
				#		MGM-Pathé Communications											co0133275 (5)			64428 (2)			15526
				#
				#	Other production companies.
				#
				#		Metro-Goldwyn-Mayer Studios											--co0071194-- (61)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		MGM+																co0963655 (26)			2639 (21)			6219
				#
				#		MGM Channel (DE)													co0989613 (12)
				#		MGM Brasil																					1991 (1)			4956
				#		MGM Television																				3159 (1)			6925
				#		MGM HD (GB)															co0372220 (1)
				#
				#		Epix (US)															co0287003 (101)			334 (31)			922
				#		Epix (CA)															co0757549 (4)
				#		EpixHD (US)															co0500325 (2)
				#
				#		MGM/Hulu (US)														co0857173 (0)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Metro-Goldwyn-Mayer													co0007143 (3263)
				#		Metro-Goldwyn-Mayer (AU)											co0629989 (354)
				#		Metro Goldwyn Mayer (MX)											co0774691 (208)
				#		Metro-Goldwyn-Mayer (AT)											co0241239 (159)
				#		Metro-Goldwyn-Mayer (IN)											co0795735 (92)
				#		Metro-Goldwyn-Mayer (DK)											co0296819 (37)
				#		Metro-Goldwyn-Mayer (IT)											co0813670 (22)
				#		Metro-Goldwyn-Mayer (MX)											co0877383 (9)
				#		Metro-Goldwyn-Mayer (FI)											co0940671 (2)
				#		Metro-Goldwyn-Mayer (VE)											co0868221 (0)
				#		Metro-Goldwyn-Mayer (PL)											co0522682 (0)
				#		Metro Goldwyn Mayer (FR)											co0719194 (0)
				#
				#		Metro-Goldwyn-Mayer (MGM) (US)										co0007143 (3263)
				#		Metro-Goldwyn-Mayer (MGM) (GB)										co0811496 (374)
				#		Metro-Goldwyn-Mayer (MGM) (BE)										co0819129 (157)
				#		Metro-Goldwyn-Mayer (MGM) (FR)										co0854778 (131)
				#		Metro-Goldwyn-Mayer (MGM) (NO)										co0811498 (126)
				#		Metro-Goldwyn-Mayer (MGM) (AR)										co0812330 (108)
				#		Metro-Goldwyn-Mayer (MGM) (CA)										co0847176 (81)
				#		Metro-Goldwyn-Mayer (MGM) (FI)										co0812376 (64)
				#		Metro-Goldwyn-Mayer (MGM) (DE)										co0815526 (49)
				#		Metro-Goldwyn-Mayer (MGM) (PT)										co0838580 (49)
				#		Metro-Goldwyn-Mayer (MGM) (SE)										co0824157 (43)
				#		Metro-Goldwyn-Mayer (MGM) (NL)										co0834362 (33)
				#		Metro-Goldwyn-Mayer (MGM) (IT)										co0901928 (18)
				#		Metro-Goldwyn-Mayer (MGM) (JP)										co0976477 (18)
				#		Metro-Goldwyn-Mayer (MGM) (ES)										co0897318 (11)
				#		Metro-Goldwyn-Mayer (MGM) (BR)										co0972214 (1)
				#		Metro-Goldwyn-Mayer (MGM) (CU)										co0870314 (1)
				#		Metro-Goldwyn-Mayer (MGM) (SD)										co0811497 (0)
				#		Metro-Goldwyn-Mayer (MGM) (VE)										co0867990 (0)
				#		Metro-Goldwyn Mayer (MGM) (PR)										co0867937 (0)
				#		Metro-Goldwyn Mayer (MGM) (PA)										co0867934 (0)
				#		Metro-Goldwyn Mayer (MGM) (PE)										co0867933 (0)
				#		Metro-Goldwyn Mayer (MGM) (BR)										co0867930 (0)
				#		Metro-Goldwyn Mayer (MGM) (CL)										co0867935 (0)
				#		Metro-Goldwyn Mayer (MGM) (VE)										co0867936 (0)
				#		Metro-Goldwyn Mayer (MGM) (MX)										co0867931 (0)
				#
				#		Metro-Goldwyn-Mayer de Mexico (MX)									co0864701 (7)
				#		Metro Goldwyn Mayer Filmmaatschappij (NL)							co1021676 (1)
				#		Metro-Goldwyn-Mayer de Cuba (CU)									co0865131 (0)
				#		Metro-Goldwyn-Mayer de Uruguay (UY)									co0864451 (0)
				#		Metro-Goldwyn-Mayer Filmverleih GmbH (DE)							co0099361 (0)
				#		Metro-Goldwyn-Mayer Synchronstudios (DE)							co0393210 (0)
				#		Metro-Goldwyn-Mayer de la Argentina (AR)							co0864452 (0)
				#		Metro-Goldwyn-Mayer Ibérica S.A. (ES)								co0089126 (0)
				#		Metro-Goldwyn-Mayer de Chile (CL)									co0864453 (0)
				#		Metro-Goldwyn-Mayer do Brasil (BR)									co0088925 (0)
				#		Metro-Goldwyn-Mayer de Panama (PA)									co0865133 (0)
				#		Metro-Goldwyn-Mayer de Colombia (CO)								co0864454 (0)
				#		Metro-Goldwyn-Mayer S.A.											co0077433 (0)
				#		Metro-Goldwyn-Mayer del Peru (PE)									co0865129 (0)
				#		Metro Goldwyn Mayer S.A.I.											co0036731 (0)
				#		Metro-Goldwyn-Mayer Pictures of Canada (CA)							co0902145 (0)
				#		Metro-Goldwyn-Mayer de Puerto Rico (PR)								co0865130 (0)
				#		Metro-Goldwyn-Mayer de Dominican Republic (DO)						co0865132 (0)
				#		The Goldwyn Company/Metro-Goldwyn-Mayer								co0007839 (0)
				#
				#		MGM Home Entertainment (US)											co0015461 (2120)
				#		MGM Home Entertainment (ES)											co0267112 (24)
				#		MGM Home Entertainment (JP)											co0541388 (2)
				#		MGM Home Entertainment (AU)											co1002361 (2)
				#
				#		MGM Home Video (MX)													co0752365 (2)
				#		MGM Home Video (FR)													co0423099 (2)
				#
				#		Metro-Goldwyn-Mayer Distributing Corporation (MGM)					co0108601 (77)
				#		MGM Networks (IN)													co0842411 (67)
				#		Metro-Goldwyn-Mayer Studios											co0071194 (61)
				#		MGM Worldwide Television (US)										co0045081 (54)
				#		MGM Domestic Television Distribution (US)							co0017533 (36)
				#		MGM (PT)															co0831915 (22)
				#		MGM International Television Distribution (US)						co0903518 (12)
				#		MGM World Films (US)												co0956201 (12)
				#		MGM Networks Latin America (US)										co0308798 (11)
				#		Metro Goldwyn Mayer Home Entertainment (MX)							co0890175 (8)
				#		MGM UK (US)															co0980207 (7)
				#		MGM Network (IN)													co0842533 (6)
				#		Metro Goldwyn Mayer Home Video (MX)									co0980535 (2)
				#		MGM Worldwide Digital Media (US)									co0228545 (1)
				#		MGM British (GB)													co0119613 (1)
				#		MGM DVD (GB)														co0879364 (1)
				#		MGM Distribution (AU)												co0544449 (1)
				#		MGM Television Entertainment (US)									co0845802 (1)
				#		Metro-Goldwyn-Mayer Domestic Television Dist. (US)					co0630394 (0)
				#		MGM Networks (US)													co0389002 (0)
				#		MGM Distibutors France (FR)											co0049562 (0)
				#		Metro-Goldwyn-Mayer Distubuting (US)								co0716032 (0)
				#
				#		Screen Pix Home Video												co0002778 (7)
				#
				#		MGM/UA Home Entertainment (US)										co0001770 (1132)
				#		MGM/UA Entertainment Company (US)									co0110106 (99)
				#		MGM/UA Distribution Company (US)									co0028432 (49)
				#		MGM/UA Communications Co. (US)										co0312972 (19)
				#		MGM/UA Home Video (DE)												co0892556 (13)
				#		MGM/UA Home Video (GB)												co1020459 (12)
				#		MGM/UA Television Distribution (US)									co0431795 (12)
				#		MGM/UA Classics (US)												co0057424 (8)
				#		MGM/UA France (FR)													co0093679 (6)
				#		MGM/UA Telecommunications (US)										co0061822 (5)
				#		MGM/UA Distribution Company (CA)									co1011157 (1)
				#		MGM/UA Home Communications Group (US)								co0373431 (1)
				#		CEL-MGM/UA Home Video (AU)											co0884625 (6)
				#		MGM/United Artists (US)												co0959574 (0)
				#
				#		Fox-MGM Film (SE)													co0218708 (49)
				#		MGM-Fox (NO)														co0615541 (47)
				#		MGM-Fox Films (AR)													co0373148 (44)
				#		Fox-MGM (DE)														co0223702 (23)
				#		MGM-Fox (FI)														co0182522 (11)
				#		Fox / MGM (BE)														co0398306 (1)
				#		A/S MGM-FOX (NO)													co0834722 (1)
				#		MGM-Fox Films (FI)													co0268150 (0)
				#		Fox/MGM (BE)														co0399951 (0)
				#		Fox/MGM (AU)														co0541390 (0)
				#
				#		MGM-EMI (GB)														co0106028 (108)
				#		MGM-EMI (MT)														co0713989 (2)
				#		MGM-EMI Distributors (GB)											co0342528 (7)
				#		MGM / EMI Distributors (GB)											co0259336 (0)
				#		MGM / EMI Distributors (GB)											co0259336 (0)
				#
				#		MGM/CBS Home Video (US)												co0172646 (51)
				#		MGM/BEF Film Distributors (AU)										co0379710 (3)
				#		MGM / PFC (FR)														co0364999 (1)
				#		Turner/MGM/UA (US)													co0219076 (0)
				#		MGM/Warner (US)														co0194242 (0)
				#		Disney/MGM Studios Florida (US)										co0663644 (0)
				#		MGM/Columbia (US)													co0757306 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyMgm : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'MGM Studios'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'MGM+'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'MGM'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'MGM Originals'},
					'expression'	: '(?:(?:^|[^a-z])mgm(?:$|[^a-z])|metro[\s\-\_\.\+]*goldwyn[\s\-\_\.\+]*mayer|^(?:epix(?:[\s\-\_\.\+]*hd)?|screen[\s\-\_\.\+]*pix))',
				},

				#################################################################################################################################
				# Miramax
				#
				#	Parent Companies:		Paramount, beIN, Weinstein (previous), Disney (previous), Filmyard Holdings (previous)
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Miramax, Dimension Films
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(893)					(332)
				#	Networks																(0)						(0)
				#	Vendors																	(102)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Miramax (US)														co0022594 (803)			332 (332)			14
				#		Miramax Television (US)												co0761033 (25)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Miramax Home Entertainment (US)										co0564364 (39)
				#		Miramax Home Entertainment (AU)										co0777547 (5)
				#
				#		Miramax Family Films (US)											co0567610 (33)
				#		Miramax Films (US)													co0995068 (18)
				#
				#		Miramax International (US)											co0681704 (13)
				#		Miramax Dimension International (US)								co0990661 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyMiramax : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Miramax Productions'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Miramax'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(miramax)',
				},

				#################################################################################################################################
				# MTV
				#
				#	Parent Companies:		Paramount
				#	Sibling Companies:		Comedy Central, Nickelodeon, Showtime, CBS, The CW, Showtime, VH1, BET, TMC, Pop TV
				#	Child Companies:		Comedy Central
				#
				#	Owned Studios:			MTV Studios
				#	Owned Networks:			MTV
				#
				#	Streaming Services:		Paramount+, Philo, Hulu
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		Paramount+, Philo, Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1606)					(549)
				#	Networks																(2756)					(453)
				#	Vendors																	(274)					(0)
				#	Originals																(618 / 921)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		MTV																							3537 (191)			8136
				#		MTV Brasil (BR)														co0079817 (47)			23361 (27)			127657
				#
				#		MTV Entertainment Studios (US)										co0849655 (69)
				#		MTV Studios (US)													co0268131 (20)			10908 (88)			6329
				#		MTV Studios (GB)													co0269523 (2)
				#		Studio MTV (JP)														co0826001 (1)
				#
				#		MTV Productions (US)												co0001660 (60)			1456 (38)			11534
				#		MTV Produktion (DK)													co0008784 (38)
				#		MTV/Remote Productions (US)											co0086778 (22)			1457 (4)			36457
				#		MTV Produktion (SE)													co0007798 (15)			23318 (10)			21830
				#		MTV Production Development (US)										co0359673 (1)			2491 (4)			65210
				#		MTV Productions (GB)												co0158087 (1)
				#		MTV Productions (CH)												co0196833 (1)
				#		MTV Filmproduktion (SE)												co0732848 (1)
				#
				#		MTV Films (US)														co0034438 (63)			3520 (56)			746
				#		MTV Films Europe (GB)												co0174753 (4)
				#
				#		MTV Networks (US)													co0066916 (411)			2363 (68)			6043
				#		MTV Networks Europe (GB)											co0149533 (60)
				#		MTV Network Latin America											co0895958 (2)			61353 (1)			60079
				#		Network Enterprises (MTV Networks) (US)								co0108413 (1)
				#
				#		MTV Documentary Films												co0753138 (20)			97024 (47)			147938
				#		MTV News and Docs (US)												co0032412 (11)			27021 (4)			57098
				#
				#		MTV Enterprises (AU)												co0924598 (1)
				#		MTV Enterprises (US)												co0348760 (1)
				#
				#		MTV Mastiff (SE)													co0164271 (3)
				#		MTV Mastiff (NO)													co0168324 (1)
				#
				#		MTVU (US)															co0174093 (22)
				#		MTV Animation (US)													co0054176 (21)			2364 (19)			6042
				#		MTV World (US)														co0452480 (6)
				#		MTV Staying Alive Foundation (GB)									co0461358 (4)			171314 (2)			222295
				#		MTV Other (US)														co0509399 (4)
				#		MTV Channel (Pvt) Limited (LK)										co0649578 (3)			78156 (2)			101213
				#		MTV Concerts														co0067273 (1)			23548 (15)			3368
				#		MTV Entertainment Events (US)										co0943653 (1)			131403 (1)			181729
				#		MTV / NRG (CY)														co0544112 (3)
				#		MTV Base (FR)														co1021416 (1)
				#		MTV New Media (US)													co0226989 (1)
				#		MTV.com (US)														co0338192 (1)
				#		Live Animals, MTV/LA (US)											co0169031 (1)
				#
				#	Other companies with the same name.
				#
				#		MTV Lebanon (LB)													--co0585967-- (11)
				#		MTV Viihdetoimitus (FI)												--co0135512-- (2)
				#		MTV-Viihde (FI)														--co0801991-- (1)
				#		MTV Kereskedelmi Iroda (HU)											--co0193063-- (0)
				#		MTV-Viihde Oy (FI)													--co0929795-- (3)
				#		MTV-Musiikki Oy (FI)												--co0651938-- (1)
				#		MTV Teatteritoimitus (FI)											--co0091089-- (2)
				#		Oy Mainos-TV-Reklam Ab (MTV) (FI)									--co0432842-- (3)
				#		MTV Dokumentum Stúdió												--co0069769-- (3)
				#		MTV Hungaria														--co0020648-- (5)
				#		MTV Video Productions (CY)											--co0684093-- (1)
				#		MTV EXIT (TH)														--co0385406-- (1)
				#		MTV Drámai Stúdió													--co0028755-- (3)
				#		MTV Rt. Drámai Stúdió, Budapest (HU)								--co0014900-- (3)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		MTV (US)																					94 (309)			33
				#		MTV (GB)															co0749671 (6)			459 (36)			488
				#		MTV UK (GB)															co0499552 (17)
				#		MTV (ES)																					912 (3)				2972
				#		MTV (AU)															co0790620 (2)
				#		Mtv (BR)															co0804934 (2)
				#		MTV																							1689 (1)			4431
				#		MTV (FR)																					3299 (0)			7221
				#
				#		Music Television (MTV) (US)											co0023307 (576)
				#		Music Television (MTV) Brazil (BR)									co0170931 (63)
				#		Music Television (MTV) (DE)											co0963160 (17)
				#		Music Television (MTV) (GB)											co0197096 (13)
				#		Music Television (MTV) India (IN)									co0120556 (11)
				#		Music Television Finland (FI)										co0484806 (1)
				#		Music Television (MTV) (IT)											co0782074 (1)
				#
				#		Music Television 2 (MTV2) (US)										co0005971 (29)
				#		MTV2 (US)															co0833608 (11)			488 (27)			17
				#		Music Television 2 (MTV2) (GB)										co0557951 (3)
				#		MTV 2 Pop (DE)														co0893707 (1)
				#		MTV2 (DE)															co1048003 (1)
				#		MTV2 Films (US)														co0264230 (1)
				#		MTV 2 Europe (GB)													co0531814 (0)
				#
				#		MTV Italy (IT)														co0185136 (94)			1004 (8)			410
				#		MTV Netherlands (NL)												co0120656 (79)			1073 (3)			2294
				#		MTV Brasil (BR)														co0079817 (47)			390 (38)			867
				#		MTV Germany (DE)													co0110193 (17)			1013 (5)			924
				#		MTV Japan (JP)														co0164112 (17)			646 (2)				2234
				#		MTV Hungary (HU)													co0312264 (16)
				#		MTV India (IN)														co0215384 (13)
				#		MTV Australia (AU)													co0149831 (12)			1157 (2)			304
				#		MTV Canada (CA)														co0189216 (11)
				#		MTV Finland (FI)													co0476397 (8)
				#		MTV Spain (ES)														co0338315 (6)			2719 (0)			6335
				#		MTV Russia (RU)														co0329982 (6)
				#		MTV Canada (CA)																				1112 (5)			335
				#		MTV Poland (PL)														co0147811 (4)			3002 (1)			959
				#		MTV Deutschland (DE)												co0357453 (4)
				#		MTV France (FR)														co0288173 (3)
				#		MTV Greece (GR)														co0367666 (2)
				#		MTV Portugal (PT)													co0593261 (1)			2720 (0)			6336
				#		MTV Denmark (DK)													co0403913 (1)			2718 (0)			976
				#		MTV Brasil (BR)																				2517 (1)			6003
				#		MTV Indonesia (ID)													co0092945 (1)
				#		MTV Ukraine (UA)													co0595428 (1)
				#		MTV Philippines (PH)												co0934596 (1)
				#		MTV-Pilipinas (PH)													co0169536 (1)
				#		MTV Sweden (SE)														co0939005 (1)
				#
				#		MTV Networks (US)													co0066916 (411)
				#		MTV Networks Europe (GB)											co0149533 (60)
				#		MTV Network Latin America (MX)										co0142523 (25)
				#		MTV Networks Latin America (US)										co0193440 (12)
				#		MTV Networks (LT)													co0254798 (7)
				#		MTV Networks Germany (DE)											co0238894 (3)
				#		MTV Network Latin America (AR)										co0895958 (2)
				#		MTV Networks (PL)													co0482778 (2)
				#		MTV Networks Baltic (LT)											co0256098 (2)
				#		MTV Networks International (GB)										co0189546 (1)
				#		MTV Networks Asia (SG)												co0199873 (1)
				#		MTV Networks de Mexico (MX)											co0142524 (1)
				#		MTV Networks Baltic (EE)											co1049500 (0)
				#		MTV Networks (NZ)													co0268026 (1)
				#		MTV Networks Netherlands (NL)										co0015808 (1)
				#		MTV Networks Benelux (BE)											co0190708 (1)
				#
				#		MTV Base (GB)														co0283024 (3)
				#		MTV Base Africa																				2564 (2)			6079
				#		MTV Base (FR)														co1021416 (1)
				#
				#		MTV Europe															co0074952 (36)			958 (3)				454
				#		MTV Latin America																			1233 (14)			2116
				#		MTV-Hindi																					1048 (4)			3402
				#		MTV Arabia (AE)														co0233926 (3)
				#		MTV Africa (ZA)														co0398445 (1)
				#		MTV Asia (SG)														co0188755 (1)			1776 (1)			931
				#		MTV Southeast Asia (SG)												co0499551 (1)
				#		MTV Amsterdam (NL)													co0188430 (1)
				#		MTV Mandarin (HK)													co0938465 (0)
				#		MTV Nordic (FI)														co0781615 (0)
				#
				#		MTV Juniori (FI)													co0526986 (5)
				#		MTV Kids (US)														co0963395 (4)
				#
				#		MTV Overdrive (GB)													co0189533 (1)
				#		MTV Overdrive (US)													co0692922 (1)
				#
				#		MTV On-Demand (US)													co0338237 (1)
				#		MTV Online (US)														co0628441 (0)
				#
				#		MTV Documentary Films (US)											co0753138 (20)
				#		MTV Tres (US)														co0210232 (7)
				#		Club MTV (GB)														co0887610 (2)
				#		MTV Studios London (GB)												co0375670 (1)
				#		MTV Films (IN)														co0478015 (1)
				#		MTV Fully Faltoo Films (IN)											co0514535 (1)
				#
				#	Other companies with the same name.
				#
				#		MTV3 (FI)															--co1039885-- (53)		--1038-- (67)		295
				#		MTV Hungary																					--2721-- (0)		6337
				#		MTV Lebanon (LB)																			--1500-- (8)		1173
				#		MTV 1 (MK)																					--2004-- (1)		2414
				#		MTV Katsomo (FI)													--co0946012-- (3)		--3707-- (2)		7452
				#		MTV Media (FI)														--co0475638-- (1)
				#		MTV Almutawassit (TN)												--co0922709-- (1)
				#		MTV3 MAX (FI)														--co0353213-- (3)
				#		MTV Film Televizyon (TR)											--co0304266-- (4)
				#		MTV Hungarian Television Co. (HU)									--co0384060-- (8)
				#		MTV Video (FI)														--co0361622-- (1)
				#		MTV-1 (HU)															--co0910570-- (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		MTV Home Video														co0046412 (1)
				#		MTV Home Entertainment (US)											co0122521 (2)
				#
				#		MTV 00s (GB)														co0878591 (3)
				#		MTV 80s (GB)														co0872843 (3)
				#		MTV 90s (GB)														co0873365 (1)
				#
				#		MTV Games (US)														co0171600 (0)
				#		MTV Live (GB)														co0625916 (1)
				#		MTV Hits (GB)														co0502802 (1)
				#		MTV Jams (US)														co0252808 (1)
				#		MTV Music (US)														co0350566 (1)
				#
				#		Nickelodeon/MTV Networks (US)										co0295362 (9)
				#		SBS MTV (KR)														co0606143 (2)
				#		AG Entertainment/MTV Entertainment (LU)								co0817756 (1)
				#		AG Entertainment/MTV Europe (LU)									co0817583 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyMtv : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'MTV Studios'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'MTV'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'MTV'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'MTV Originals'},
					'expression'	: '(mtv[u\d]?|music[\s\-\_\.\+]*television)',
				},

				#################################################################################################################################
				# National Geographic
				#
				#	Parent Companies:		Disney
				#	Sibling Companies:		History
				#	Child Companies:		-
				#
				#	Owned Studios:			NatGeo
				#	Owned Networks:			NatGeo
				#
				#	Streaming Services:		NatGeo, Disney+, Hulu
				#	Collaborating Partners:	Disney
				#
				#	Content Provider:		Disney+, Hulu
				#	Content Receiver:		Disney
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1043)					(893)
				#	Networks																(1923)					(739)
				#	Vendors																	(71)					(0)
				#	Originals																(1109 / 845)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		National Geographic (US)											co0005084 (223)			1392 (782)			7521
				#		National Geographic Documentary Films								co0624013 (33)			138750 (38)			189457
				#		National Geographic Channels International (US)						co0203553 (23)			2321 (106)			123388
				#		National Geographic Films (US)										co0145734 (10)			138750 (38)			189457
				#
				#		National Geographic Kids' Programming & Production (US)				co0184091 (4)
				#		National Geographic Kids																	127133 (4)			171426
				#
				#		National Geographic Original Productions (US)						co0925467 (2)
				#		National Geographic Television and Film (US)						co0272910 (4)
				#		National Geographic World Films (US)								co0176729 (2)
				#		National Geographic Television / Pangloss Films (US)				co0235837 (1)
				#		National Geographic Studios (US)									co0512191 (15)
				#
				#		National Geographic Television (US)									co0056555 (113)
				#		National Geographic TV (US)											co0846485 (1)
				#
				#		National Geographic Latin America (US)								co0965804 (3)
				#		National Geographic (IN)											co0863016 (2)
				#		National Geographic (AR)											co0916743 (1)
				#		National Geographic Canada (CA)										co0204659 (1)
				#		National Geographic (FR)											co1001450 (1)
				#		National Geographic (ES)											co0943055 (0)
				#		National Geographic New Zealand (NZ)								co0748068 (0)
				#
				#		National Geographic Wild (US)										co0459291 (19)
				#		NatGeo Wild (BR)													co0649860 (7)
				#
				#		National Geographic Channel (BG)									co0647865 (1)
				#		National Geographic Channels (US)									co0871114 (1)
				#
				#		National Geographic Explorer (US)									co0335470 (2)
				#		National Geographic Ventures (US)									co0282842 (1)
				#		National Geographic Society Mission Programs (US)					co0213988 (1)
				#
				#	Other production companies.
				#
				#		National Geographic Society (US)									--co0059975-- (41)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		National Geographic (US)											co0005084 (223)			80 (480)			43
				#		National Geographic (DE)											co0279494 (32)
				#		National Geographic																			1880 (20)			4293
				#		National Geographic (IN)											co0645043 (11)			2403 (4)			4404
				#		NatGeo (BR)															co0410009 (11)
				#		National Geographic (BR)											co0638684 (7)			1755 (10)			4227
				#		National Geographic (NL)																	1557 (5)			3355
				#		National Geographic																			3315 (5)			6750
				#		National Geographic (PL)											co0530592 (4)
				#		National Geographic Latin America (US)								co0965804 (3)
				#		National Geographic (IN)											co0863016 (2)
				#		National Geographic (GR)											co0735946 (2)
				#		National Geographic (IT)											co0886585 (2)			3024 (1)			6031
				#		National Geographic (HU)											co1058738 (1)			3137 (1)			6638
				#		National Geographic Abu Dhabi (AE)									co0546833 (1)
				#		National Geographic (AR)											co0916743 (1)
				#		National Geographic Canada (CA)										co0204659 (1)
				#		National Geographic (FR)											co1001450 (1)
				#		National Geographic Asia (HK)																3247 (1)			5805
				#		National Geographic																			2382 (0)			5432
				#		National Geographic (ES)											co0943055 (0)
				#		National Geographic New Zealand (NZ)								co0748068 (0)
				#
				#		National Geographic Channel (US)									co0139461 (405)
				#		National Geographic Channel (GB)									co0170411 (48)			567 (51)			1825
				#		National Geographic Channel (NL)									co0376245 (38)
				#		National Geographic Channel (CA)															446 (8)				799
				#		National Geographic Channel (DE)															3726 (3)			6748
				#		National Geographic Channel (AU)									co0965214 (0)			1756 (1)			1702
				#		National Geographic Channel (ES)									co0965465 (1)
				#		National Geographic Channel (FR)									co0879628 (1)
				#		National Geographic Channel (TW)									co0930019 (1)
				#		National Geographic Channel (BG)									co0648039 (0)
				#
				#		National Geographic Channel International (US)						co0282022 (33)
				#		National Geographic Channel Network (IN)							co0130013 (15)
				#
				#		National Geographic Television (US)									co0056555 (113)
				#		National Geographic International (US)								co0040897 (31)
				#		National Geographic Television International (GB)					co0303924 (13)
				#		National Geographic TV (US)											co0846485 (1)
				#
				#		Nat Geo Wild (US)													co0286617 (92)			185 (154)			1043
				#		National Geographic Wild (US)										co0459291 (19)
				#		National Geographic Wild (DE)										co0875566 (8)
				#		NatGeo Wild (BR)													co0649860 (7)
				#		Nat Geo Wild (CA)													co0468870 (5)
				#		National Geographic Wild (NL)										co0782472 (3)
				#		Nat Geo Wild (DE)													co0882848 (2)
				#		Nat Geo Wild (VN)													co0224810 (2)
				#		National Geographic Wild (GB)										co0792207 (1)
				#		Nat Geo Wild (JP)													co0474480 (1)
				#
				#		Nat Geo Kids Latin America (BR)										co0781136 (25)
				#		Nat Geo Kids																				1985 (7)			4476
				#		National Geographic Kids (US)										co0713969 (2)
				#
				#		Nat Geo Mundo (US)													co0381565 (7)
				#		Nat Geo Mundo (US)																			2914 (4)			6664
				#
				#		Nat Geo Toons Latin America (MX)									co1004777 (71)
				#		Nat Geo Toons Latin America (AR)									co1044140 (5)
				#		Nat Geo Toons (TW)													co1020472 (1)
				#		Nat Geo Toons Abu Dhabi (AE)										co1020838 (1)
				#		Nat Geo Toons Hong Kong (HK)										co1020525 (1)
				#		Nat Geo Toons Asia-Pacific (MY)										co1020527 (1)
				#
				#		National Geographic Network Asia									co0097694 (12)
				#		National Geographic Video (US)										co0139462 (5)
				#		National Geographic Cinema Ventures (US)							co0223788 (5)
				#		National Geographic Adventure (SG)									co0217749 (5)
				#		National Geographic World (US)										co0243269 (3)
				#		National Geographic Partners (US)									co0606234 (3)
				#		National Geographic Adventure Australia (AU)						co0369810 (2)
				#		National Geographic Giant Screen Films (US)							co0195887 (1)
				#		National Geographic HD (DE)											co0983810 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		National Geographic Entertainment (US)								co0223903 (15)
				#
				#		National Geographic Television & Film (NGT&F) Film Library (US)		co0273006 (4)
				#		National Geographic Television Film Library (US)					co0088666 (3)
				#		National Geographic Image Collections (US)							co0347855 (1)
				#		National Geographic Television & Film Library (US)					co0272951 (1)
				#		National Geographic Remote Imaging (US)								co0694600 (0)
				#		National Geographic Television and Film Library (US)				co0272982 (0)
				#		National Geographic Television & Film (NGT&F) Library (US)			co0272950 (0)
				#
				#		National Geographic Books (US)										co0694343 (1)
				#		National Geographic Images (US)										co0815045 (1)
				#		National Geographic Magazine (US)									co0334531 (1)
				#		National Geographic Magazine, Russia (RU)							co0687580 (0)
				#
				#		National Geographic Digital Motion (US)								co0195888 (4)
				#		Nat Geo Motion (US)													co0814599 (1)
				#
				#		National Geographic Creative (US)									co0479685 (4)
				#		NatGeo Creative (US)												co0824877 (0)
				#
				#		National Geographic People (DE)										co0975541 (2)
				#		National Geographic Museum (US)										co0544568 (1)
				#		Nationalgeographic.com (US)											co0421612 (1)
				#		National Geographic Expeditions Council (US)						co0453441 (1)
				#		National Geographic Crittercam (US)									co0874431 (1)
				#
				#		Thought Equity - National Geographic Films (US)						co0300041 (1)
				#		National Geographic Entertainment / Cinema Ventures (US)			co0290280 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyNationalgeo : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'National Geographic Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'National Geographic'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'National Geographic'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'National Geographic Originals'},
					'expression'	: '(nat(?:ional)?[\s\-\_\.\+]*geo(?:graphics?)?)',
				},

				#################################################################################################################################
				# NBC																		IMDb					Trakt				TMDb
				#
				#	Studios																	(8856)					(887)
				#	Networks																(8489)					(1529)
				#	Vendors																	(2122)					(103)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		NBC																	co0072315 (3476)		8037 (519)			1502
				#		NBC Studios (US)													co0022762 (110)			313 (120)			7928
				#		NBC Productions (US)												co0065874 (67)			1311 (156)			5253
				#		NBC Entertainment (US)												co0048970 (23)
				#		NBC Enterprises (US)												co0009465 (17)			2756 (6)			55683
				#		NBC Public Affairs (US)												co0059726 (4)			138024 (2)			69517
				#		NBC Productions Inc.												co0114840 (2)
				#		NBC Television Network (US)											co0865080 (1)
				#		NBC Media Productions (US)											co0368618 (1)
				#
				#		NBC News (US)														co0095173 (90)			304 (21)			60324
				#		NBC News Studios (US)												co0851289 (12)			111102 (14)			162351
				#		NBC News Productions (US)											co0066042 (7)
				#		NBC News Digital (US)												co0726999 (1)
				#
				#		NBC Learn (US)														co0518674 (1)
				#		NBC Sports Originals (US)											co0649559 (1)
				#
				#		NBC-Blue (US)														co0147866 (1)
				#		NBC-Red (US)														co0147867 (1)
				#		NBC Connecticut (US)												co0738026 (1)
				#		NBC Project X														co0046728 (1)
				#		Television Religious Programs Unit for NBC (US)						co0376914 (1)
				#		NBC Bay Area (US)													co0756108 (1)
				#
				#		NBC Film (US)														co0111876 (2)			7862 (14)			27101
				#		NBC Films (US)														co0112163 (2)
				#
				#		NBC Universal Television											co0129175 (187)			155816 (6)			207345
				#		NBCUniversal														co0195910 (100)			1071 (40)			26559
				#		NBC Universal Studios 												co0242700 (13)
				#		NBCUniversal International Studios									co0216142 (11)			1896 (11)			95155
				#		NBC Universal International Studios															2443 (16)			87455
				#		NBCUniversal Content Studios										co0733397 (5)
				#		NBC Universal Digital Studio										co0284326 (3)			75288 (2)			78166
				#		NBC Universal International Television Pro.							co0485242 (2)
				#		NBC Universal Brand Development (NBCUBD)							co0608727 (2)
				#		NBC Universal Global Networks										co0242277 (2)			70892 (4)			2975
				#		NBCUniversal Skycastle (US)											co0574746 (1)
				#		Stamford Studios: A Division of NBC Universal (US)					co0947572 (1)
				#		NBCUniversal International Studios (US)								co1048379 (0)
				#
				#		CNBC																						44641 (12)			28408
				#		CNBC America's Talking (US)											co0187587 (3)
				#		CNBC Media Productions (US)											co0809813 (1)
				#
				#		MSNBC Network																				41837 (2)			15426
				#
				#		Lionsgate Television/NBC (US)										co0857626 (5)
				#
				#	Other production companies.
				#
				#		NBC Studios, Burbank												--co0046009-- (21)
				#		NBC Today Show (US)													--co0648389-- (2)
				#		NBC Radio (US)														--co0372813-- (2)
				#		The NBC Production Staff (US)										--co0339138-- (1)
				#
				#	Other companies with the same name.
				#
				#		NBC Film (TR)														--co0109140-- (10)
				#		Namibia Broadcasting Company (NBC) (NA)								--co0537302-- (9)
				#		NBC (NA)															--co0847663-- (1)
				#		NBC Left Field (US)													--co0767156-- (1)
				#		NBC Apple (JP)														--co0337629-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		NBC (US)															co0072315 (3476)		21 (1529)			6
				#		NBC Europe (GB)														co0071577 (10)
				#		NBC Asian America (US)												co0637717 (1)
				#		NBC (MX)															co0893655 (1)
				#
				#		NBC Universal Network TV (US)										co0196211 (15)
				#		NBC Universal Global Networks (IT)									co0261403 (5)
				#		NBC Universal Cable Entertainment									co0197667 (5)
				#		NBCUniversal International Networks (GB)							co0704497 (4)
				#		NBCUniversal International Networks (BR)							co0758126 (2)
				#		NBC Universal Global Networks										co0213416 (1)
				#		NBCUniversal International Networks (DE)							co0616374 (1)
				#		NBC Universal Global Networks (GB)									co0260407 (0)
				#		NBC Universal International (US)									co0216142 (11)
				#
				#		NBC News NOW (US)													co0854498 (8)
				#		NBCNews.com (US)													co0889394 (1)
				#
				#		NBC Sports (US)														co0135684 (100)
				#		NBC Sports Network (US)												co0588377 (17)
				#		NBC Sports Special													co0015493 (5)
				#		National Broadcasting Company (NBC) Sports (US)						co0093506 (1)
				#
				#		NBC Television Stations (US)										co0003209 (5)
				#		NBC Television (US)													co0816726 (4)
				#
				#		NBC Telemundo Network (US)											co0147812 (62)
				#		NBC Film															co0046828 (11)
				#		NBC Universo (US)													co0622734 (6)
				#		NBC Special Treat (US)												co0054488 (0)
				#		NBC Family (US)														co0814736 (0)
				#
				#	Other companies with the same name.
				#
				#		NBC (JP)																					--627-- (29)			2462
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		NBC Universal Television Distribution								co0131785 (434)
				#		NBCUniversal Entertainment (JP)										co0474968 (132)
				#		NBC Universal Entertainment (JP)									co0459508 (53)
				#		NBCUniversal Global Distribution (US)								co0800079 (32)
				#		NBCUniversal Media (US)												co0345290 (14)
				#		NBC Universal Domestic Television Distribution						co0198120 (13)
				#		NBC Universal Digital Distribution									co0196214 (6)
				#		NBCUniversal Syndication Studios (US)								co0839122 (5)
				#		NBCUniversal International Television Distribution (US)				co0722053 (5)
				#		Sparrowhawk NBC Universal (GB)										co0256170 (4)
				#		NBCUniversal Canada (CA)											co0468247 (3)
				#		NBC Universal Global Distribution									co0775963 (3)
				#		NBC Universal Sports Boston (US)									co0315124 (3)
				#		NBC Universal Studios (MX)											co0728905 (2)
				#		NBC Universal Sound (US)											co0514291 (2)
				#		NBC Universal Media													co0852261 (2)
				#		Getty NBC Universal Collection (US)									co0879192 (2)
				#		Betty NBC Universal Collection (US)									co0879183 (1)
				#		NBC Universal Cable Studio											co0233867 (1)
				#		NBC Universal Entertainment Cable Group								co0416933 (1)
				#		NBCUniversal News Group												co0517613 (1)
				#		NBCUniversal Music (US)												co1021678 (1)
				#		NBC Universal Brand Development (NBCUBD) (US)						co0608727 (1)
				#
				#		NHL on NBC (US)														co0306219 (3)
				#		NBC.com (US)														co0354562 (2)
				#		NBC Home Entertainment (US)											co0976901 (1)
				#		NBC Home Video (US)													co0075133 (1)
				#		NBC Cable Networks (US)												co0099445 (1)
				#		NBC Live Theater (US)												co0093287 (1)
				#		NBC Television Sales (US)											co0101920 (1)
				#		NBC Olympics (US)													co0871957 (1)
				#		NBC Weather Plus (US)																		1671 (1)			790
				#
				#		NBC Nightly News (US)												co0672689 (1)
				#		NBC 29 News (US)													co0926776 (1)
				#		NBC News 15 (US)													co0916077 (0)
				#
				#		NBC Sports Chicago (US)												co1067279 (1)
				#		NBC Sports Bay Area (US)											co0868952 (0)
				#
				#		NBC Symphony Orchestra (US)											co0051472 (3)
				#		NBC Opera Chorus (US)												co0123321 (1)
				#		NBC Opera Company (US)												co0638541 (0)
				#
				#		NBC 33 (US)															co0537945 (1)
				#		NBC 40 (US)															co0655265 (1)
				#		NBC LA (US)															co0607404 (1)
				#		NBC 12 (US)															co0435778 (1)
				#		NBC 4 Washington (US)												co0537942 (1)
				#		NBC Montana (US)													co0127161 (1)
				#		NBC Seattle (US)													co0731677 (1)
				#		NBC Palm Springs (US)												co0857116 (1)
				#		NBC4 Columbus (US)													co0958317 (1)
				#		NBC 4 Los Angeles (US)												co0918373 (1)
				#		NBC 7 San Diego (US)												co0488771 (1)
				#		NBC 29 (US)															co0926779 (1)
				#		NBC, Burbank (US)													co0452922 (1)
				#		NBC Stamford (US)													co0403386 (0)
				#
				#		NBC Electricial (US)												co0793937 (0)
				#		NBC Rotoworld (US)													co0557651 (0)
				#		NBC Agency (US)														co0215788 (0)
				#		NBC Skycastle (US)													co0271452 (0)
				#		NBC Everywhere (US)													co0229385 (0)
				#		NBC/CBS Studios (US)												co1042083 (0)
				#
				#		NBC One (US)														co0763972 (3)
				#		NBC Two (US)														co0763971 (2)
				#
				#		CNBC-e (TR)															co0203432 (191)
				#		CNBC (US)															co0014503 (152)			469 (39)			175
				#		Nikkei CNBC (JP)													co0203354 (19)
				#		CNBC Europe (GB)													co0211414 (18)			3414 (1)			186
				#		CNBC World (US)														co0443630 (5)
				#		CNBC Asia (SG)														co0384687 (3)
				#		CNBC (IN)															co0219279 (3)
				#		CNBC (ZA)															co0219254 (2)
				#		CNBC (PK)															co0219220 (2)
				#		CNBC TV18 (IN)														co0384730 (1)
				#		CNBC Arabia (AE)													co0338179 (1)
				#		Class CNBC (IT)														co0993178 (0)
				#
				#		KNBC (US)															co0068602 (25)			2602 (1)			624
				#		KNBC-TV (US)														co0387785 (5)
				#		KNBC Action News (US)												co0416000 (1)
				#		KNBC Los Angeles (US)												co0610076 (1)
				#		KNBC Public Affairs (US)											co0793935 (0)
				#
				#		MSNBC Network (US)													co0108351 (177)
				#		MSNBC News (US)														co0672698 (53)
				#		MSNBC Films (US)													co0240399 (24)
				#		MSNBC (US)															co0945036 (17)			209 (52)			37
				#		Msnbc.com (US)														co0302702 (4)
				#
				#		NBCSN (US)															co0373481 (35)			201 (13)			413
				#
				#		Comcast/NBC Chabot TV (US)											co0537229 (3)
				#		Kmir NBC (US)														co0610705 (2)
				#		WJAR-TV NBC 10 (US)													co0154456 (2)
				#		KSL-TV NBC (US)														co0508202 (1)
				#		NBC KXAS Television News Collection (US)							co0925618 (1)
				#		WWBT-Richmond NBC (US)												co0922214 (1)
				#		WPTV West Palm Beach (NBC) (US)										co0992783 (1)
				#
				#		NBC/Lionsgate (US)													co1042082 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyNbc : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'NBC Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'NBC'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'NBC'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'NBC Originals'},
					'expression'	: '((?:[ck]|ms)?nbc|national[\s\-\_\.\+]*broadcast(?:ing)?[\s\-\_\.\+]*(?:company|corporation))',
				},

				#################################################################################################################################
				# Netflix
				#
				#	Netflix does not own or collaborate with any major partner. It owns a few very small companies.
				#	https://npfp.netflixstudios.com/region/global/
				#
				#	Owned by:
				#		Current:			Netflix
				#
				#	Owner of:
				#		Current:			Roald Dahl
				#
				#	Content provider to:
				#		Current:			Hulu (almost none)
				#
				#	Content provided by:
				#		Current:			Many smaller studios and networks around the world.
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(334)					(48)
				#	Networks																(10375)					(2153)
				#	Vendors																	(10398)					(2153)
				#	Originals																(3508 / 2805)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Netflix Studios														co0650527 (176)			127791 (41)			178464
				#		Netflix Animation													co0743375 (62)			120480 (7)			171251
				#		Netflix Worldwide Productions										co0933900 (9)
				#		Netflix Original Documentary										co0825975 (6)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Netflix																co0144901 (8426)		53 (2153)			213
				#		Netflix	II																					1465 (0)			4095
				#		Netflix India														co0944055 (268)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Netflix																co0144901 (8426)		53 (2153)			213
				#		Netflix	II																					1465 (0)			4095
				#		Netflix India														co0944055 (268)
				#		Netflix Worldwide Entertainment (US)								co0805756 (23)
				#		Still Watching Netflix (US)											co0950660 (1)
				#		Netflix Services (GB)												co1048172 (0)
				#		Birds for Netflix (US)												co0803020 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyNetflix : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Netflix Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Netflix'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Netflix'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Netflix Originals'},
					'expression'	: '(netflix)',
				},

				#################################################################################################################################
				# New Line Cinema
				#
				#	Parent Companies:		Warner Bros Discovery, Warner (previous), TBS/Turner (previous)
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			New Line Cinema, New Line Television, Fine Line Features
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Warner, Turner
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(966)					(522)
				#	Networks																(0)						(0)
				#	Vendors																	(472)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		New Line Cinema (US)												co0046718 (745)			1227 (452)			12
				#		New Line Cinema (MX)												co0765072 (9)
				#		New Line Cinema (JP)												co0421859 (2)
				#
				#		New Line Productions (US)											co0001803 (34)
				#		New Line Television (US)											co0002753 (18)			2191 (17)			3402
				#
				#		Fine Line Features (US)												co0043853 (126)			5610 (60)			8
				#
				#	Not sure if this is the same company, probably not.
				#
				#		Fine Line Producers (US)											--co0112037-- (0)
				#		Fine Line Production (US)											--co0545947-- (0)
				#		Fine Line Entertainment (US)										--co0432654-- (1)
				#		Fine Line Productions (GB)											--co0775304-- (1)
				#		Fine Line Pictures (US)												--co0950748-- (1)
				#		Fine Line Media (US)												--co0251918-- (4)
				#		Fine Line Production (LB)											--co0940946-- (1)
				#		Fine Line Productions (CA)											--co0218916-- (3)
				#		Fine Lines Creations (IN)											--co0203394-- (1)
				#
				#	Other companies with the same name.
				#
				#		New Line Film Productions (US)										--co0738976-- (3)
				#		New Line Entertainment (PH)											--co0977948-- (3)
				#		New Line (JP)														--co0236360-- (10)
				#		New Line Films S.L. (ES)											--co0064946-- (5)
				#		New Line Entertainment (ES)											--co0779815-- (5)
				#		New Line Pictures (PH)												--co1002366-- (1)
				#		New Line Korea (KR)													--co0086224-- (1)
				#		New Lineo Cinemas de Portugal (PT)									--co0397612-- (1)
				#		New Lineo Cinemas (PT)												--co0023428-- (9)
				#		New-Line Studio														--co0165897-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		New Line Home Video (US)											co0079450 (366)
				#		New Line Home Vídeo (BR)											co0098273 (19)
				#		New Line Home Video (CA)											co0225343 (3)
				#		New Line Home Video (JP)											co0497163 (1)
				#
				#		New Line Home Entertainment (US)									co0228937 (90)
				#		New Line International (US)											co0042275 (7)
				#
				#		SEL & GFO and New Line Cinema in Association with ... (US)			co0346875 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyNewline : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1, 	'label' : 'New Line Cinema'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'New Line'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(new[\s\-\_\.\+]*line[\s\-\_\.\+]*(?:cinema|production|television|home|international)|fine[\s\-\_\.\+]*line[\s\-\_\.\+]*features?)',
				},

				#################################################################################################################################
				# Nickelodeon
				#
				#	Parent Companies:		Paramount
				#	Sibling Companies:		VH1, MTV
				#	Child Companies:		-
				#
				#	Owned Studios:			Nickelodeon Studios
				#	Owned Networks:			Nickelodeon, Nick Jr, Nicktoons, Nick at Nite, TeenNick, Noggin, NickMusic
				#
				#	Streaming Services:		Paramount+
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(531)					(490)
				#	Networks																(2129)					(418)
				#	Vendors																	(6)						(0)
				#	Originals																(248 / 950)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Nickelodeon Animation Studio (US)															1533 (204)			4859
				#		Nickelodeon Animation Studios (US)									co0044395 (144)
				#		Nickelodeon Digital Animation Studios (US)							co0130123 (3)
				#
				#		Nickelodeon Productions (US)										co0011615 (111)			1119 (250)			5371
				#		Nickelodeon Movies (US)												co0004265 (80)			4568 (71)			2348
				#		Nickelodeon Studios (US)											co0078560 (25)
				#		Nickelodeon Latinoamérica																	151752 (6)			194498
				#		Nickelodeon Films (IT)												co0090721 (2)			70634 (2)			131043
				#
				#		Nicktoons Productions (US)											co0093767 (13)			24136 (5)			67245
				#		Nicktoons Network Studios (US)										co0888450 (1)
				#		The Friday Night Nicktoons Podcast (US)								co0858405 (1)
				#		Nicktoons Original Productions (US)									co0516455 (0)
				#
				#		Nick Jr. Productions (US)											co0652791 (18)			84694 (11)			139142
				#		Nicktroop Productions (CA)											co0298878 (1)
				#
				#	Other production companies.
				#
				#		Nickelodeon on Sunset (US)											--co0017841-- (3)
				#
				#	Other companies with the same name.
				#
				#		Nickel Odeon (ES)													--co0012941-- (16)
				#		Nickel Odeón Dos (ES)												--co0057688-- (8)		--17658-- (14)		6860
				#		Nickelodeon Productions (FR)										--co0043436-- (4)
				#		Nickelodeon Film and TV (ZA)										--co0448853-- (3)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Nickelodeon (US)																			230 (270)			13
				#		Nickelodeon																					612 (15)			794
				#		Nickelodeon (GB)																			845 (9)				286
				#		Nickelodeon (IL)																			999 (9)				2314
				#		Nickelodeon (NL)																			231 (7)				474
				#		Nickelodeon (DE)																			877 (4)				775
				#		Nickelodeon (BR)																			1439 (4)			4015
				#		Nickelodeon (IN)																			2823 (4)			2313
				#		Nickelodeon (HR)													co0421170 (3)
				#		Nickelodeon (MX)													co1070844 (2)
				#		Nickelodeon (AU)																			1719 (1)			416
				#		Nickelodeon																					3697 (1)			7413
				#		Nickelodeon (KR)																			3903 (1)			7563
				#		Nickelodeon																					2922 (0)			6751
				#		Nickelodeon (IT)													co1074587 (0)
				#
				#		Nickelodeon Network (US)											co0007546 (1299)
				#		Nickelodeon Network (MX)											co1072030 (1)
				#
				#		Nick Jr. (GB)														co0106182 (89)			1036 (8)			2315
				#		Nick Jr. (US)														co0301237 (71)			403 (28)			35
				#		Nick Jr. (DE)														co0249384 (18)
				#		Nick Jr. (AU)														co0385703 (5)			1121 (2)			594
				#		Nick Jr. (IT)														co0981291 (2)
				#		Nick Jr. (BR)														co0874875 (2)
				#		Nick Jr. (MX)														co0874876 (1)
				#		Nick Jr. (UA)														co1070495 (1)
				#
				#		Nickelodeon Junior (FR)												co0469424 (7)
				#		Nickelodeon Jnr (US)												co0672931 (0)
				#
				#		TeenNick (US)														co0467568 (40)
				#		TeenNick (US)																				281 (7)				234
				#		TeenNick (IL)																				3559 (7)			4734
				#		TeenNick (IL)														co0851270 (5)
				#		Teen Nick Israel (IL)												co0990497 (4)
				#		TeenNick (HU)														co0847982 (0)
				#
				#		Nicktoons Network (US)												co0167426 (82)
				#		Nicktoons (GB)														co0465477 (47)
				#		Nicktoons (US)																				330 (31)			224
				#		Nicktoons (US)														co0698648 (19)
				#		Nicktoons (DE)														co0492047 (13)
				#		Nicktoons (MX)														co1028177 (5)
				#		Nicktoons TV (US)													co1017467 (5)
				#		Nicktoonsters (GB)													co0328444 (3)
				#		Nicktoons (HU)														co0912620 (0)
				#
				#		Noggin (US)															co0031641 (92)			761 (16)			188
				#		Noggin by Nick Jr. (DE)												co1040835 (2)
				#		Noggin TV (US)														co0479262 (1)
				#
				#		The N																						2755 (8)			5099
				#		The N (US)															co0040603 (15)
				#		The N (CA)															co0539580 (0)
				#
				#		Nick at Nite (US)													co0154874 (44)
				#		Nick @ Nite (US)													co0184885 (12)
				#		Nick at Nite (US)																			1135 (7)			259
				#		Nick at Night (US)													co1053065 (1)
				#
				#		NICK (DE)															co0164662 (19)
				#		Nick (DE)															co0893565 (18)
				#		nick (DE)																					3782 (1)			7499
				#		NickIndia (IN)														co0300565 (3)
				#		Nick Pakistan (PK)																			1711 (1)			1703
				#
				#		Nick GAS (US)														co0513608 (4)
				#		Nickelodeon Games and Sports for Kids (US)							co0577889 (2)
				#
				#		Nickelodeon Pictures (GB)											co1073978 (5)
				#		Nickelodeon Universe (US)											co0843315 (0)
				#		Nickelodeon Open and Close (US)										co0296940 (0)
				#		Nickelodeon Movies UK (GB)											co0329703 (0)
				#		Nickelodeon Latin America (US)																1438 (0)			4016
				#
				#		NickMom (US)														co0397805 (4)
				#		Snick (US)															co1053063 (1)
				#		NickSplat (US)														co1053067 (1)
				#		Kids Nick Polska																			1026 (0)			3620
				#
				#		Sonic Nickelodeon (IN)												co0492991 (11)
				#		Nickelodeon/MTV Networks (US)										co0295362 (9)
				#
				#	Other companies with the same name.
				#
				#		Noggins Farm (CA)													--co0792448-- (0)
				#		Noggin Films (NZ)													--co0318575-- (1)
				#		Noggin Sauce Pictures (US)											--co0554758-- (0)
				#		Empty Noggin (US)													--co1022142-- (0)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Nickelodeon Filmverleih (DE)										co0216996 (3)
				#		Nickelodeon Virtual Worlds Group (US)								co0896623 (0)
				#		Nickelodeon Games (US)												co0472950 (0)
				#		Nickelodeon Studios Florida (US)									co0619583 (0)
				#
				#		Nick Records (US)													co0741051 (3)
				#		Nick Digital Services (US)											co1049678 (0)
				#		Nick Jr / Vestron Home Video (NZ)									co0280606 (0)
				#
				#	Unsure if these are the same company.
				#
				#		NickFilms (US)														--co0100888-- (1)
				#		NickFilm (GB)														--co0442058-- (1)
				#		Nick DVD (US)														--co0128252-- (0)
				#		Nickstars (JP)														--co0674212-- (0)
				#		Nick Swim (US)														--co0889181-- (0)
				#		Nicknopoly Entertainment (CA)										--co0640494-- (0)
				#
				#	Other companies with the same name.
				#
				#		Nick Video (US)														--co0993727-- (3)
				#		Nick Fox-Gieg Animation (CA)										--co0287891-- (3)
				#
				#################################################################################################################################
				MetaCompany.CompanyNickelodeon : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Nickelodeon Studios'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Nickelodeon'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Nickelodeon'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Nickelodeon Originals'},
					'expression'	: '(nickelodeon|nick(?:toons?|troops?)|^nick$|nick[\s\-\_\.\+]*(?:jr|junior|(?:(?:at|@)[\s\-\_\.\+]*(?:nite|night))|india|pakistan|polska|gas|mom|splat|recors?|digital)|teen[\s\-\_\.\+]*nick|noggin|the[\s\-\_\.\+]*n(?:$|[\s\-\_\.\+])|^snick$)',
				},

				#################################################################################################################################
				# Paramount
				#
				#	Member of the "original" and "modern" Big Five.
				#	Most outside content is provided through CBS/Viacom and it subsidiaries.
				#		https://paramount.fandom.com/wiki/Category:Subsidiaries
				#		https://paramount.fandom.com/wiki/List_of_companies_owned_by_Paramount
				#		https://en.wikipedia.org/wiki/List_of_assets_owned_by_Paramount_Global
				#		https://en.wikipedia.org/wiki/Paramount_Streaming
				#
				#	Parent Companies:		Paramount
				#	Sibling Companies:		-
				#	Child Companies:		CBS, Showtime, The CW
				#
				#	Owned Studios:			Paramount, United International Pictures (partial, Paramount+Universal), Miramax (partial),
				#							DreamWorks (previous), Orion (previous), TriStar (previous)
				#	Owned Networks:			CBS, Viacom (defunct), BET, VH1, MTV, Comedy Central
				#							Nickelodeon, Noggin, Awesomeness,
				#							Showtime, SkyShowtime (partial, Comcast+Paramount), The Movie Channel (TMC),
				#							The CW (partial, CBS+Warner), TNN, Spike TV, Channel 5, Network Ten, Telefe,
				#							Telecine (partial, Paramount+Universal+MGM+Disney), True Crime (partial, AMC+Paramount),
				#							MGM+ (previous), Epix (previous), Lifetime (previous), Sundance (previous), USA Networks (previous),
				#
				#	Streaming Services:		Paramount+, Pluto TV, Philo (partial, Hearst+Disney+AMC+Paramount+Warner), FuboTV (partial)
				#	Collaborating Partners:	CBS, Fox, Sky, ABC, BBC, DreamWorks, Miramax, Telecine, Global, RTL (previous through RTL CBS Entertainment)
				#
				#	Content Provider:		-
				#	Content Receiver:		Paramount+, CBS, Pluto TV, Philo, The CW, Hulu (previous at least)
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(9007)					(3269)
				#	Networks																(1446)					(350)
				#	Vendors																	(12008)					(4)
				#	Originals																(121 / 227)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Paramount															co0858764 (19)			455 (2689)			4
				#		Paramount Pictures													co0023400 (4663)
				#		Paramount Pictures Digital Entertainment							co0226970 (26)			3130 (8)			21834
				#		Paramount British Pictures																	44425 (24)			8913
				#		Paramount Pictures International															22388 (7)			100612
				#		Paramount Pictures Cartoon Studios (US)								co0509323 (0)
				#		Paramount Pictures Corporation and Walt Disney Productions (US)		co0227227 (0)
				#
				#		Paramount Television												co0053559 (470)			352 (310)			9223
				#		Paramount Television II																		150364 (15)			201841
				#
				#		Paramount Network Television										co0066107 (37)
				#		Paramount Television Studios										co0781350 (36)
				#		Paramount Television International Studios													163403 (4)			215140
				#		Paramount Television Studios International (PTSI) (BR)										151215 (4)			202709
				#		Paramount Network Television Productions							co0187272 (15)
				#		Paramount Television Animation (US)									co0942448 (4)
				#		Paramount TV (US)													co0754886 (4)
				#		Paramount International Television									co0031170 (2)
				#		Paramount Television Productions (US)								co0447745 (2)
				#		Paramount Television Service (US)									co0614985 (2)
				#		Paramount Domestic Television (US)									--co0057237-- (115)
				#
				#		Paramount Animation													co0390995 (49)			4569 (16)			24955
				#		Paramount Animation Studios (US)									co0969496 (1)
				#
				#		Paramount Film Company (IN)											co0641896 (9)
				#		Paramount Film (IN)													co0028548 (6)
				#		Paramount Filmproduction GmbH (DE)									co0076598 (5)			45935 (2)			19541
				#		Paramount Films (India) (IN)										co0336713 (2)
				#		Paramount Films of Uruguay (UY)										co0834862 (0)
				#
				#		Paramount Famous Productions (US)									co0245466 (3)			13240 (6)			52010
				#		Paramount Productions (JP)											co0334177 (0)
				#		Paramount Overseas Productions Inc.									co0012106 (0)
				#		Paramount Productions (US)											co0428828 (0)
				#		Paramount British Productions (GB)									co0750721 (0)
				#
				#		Paramount Home Entertainment																7085 (98)			6548
				#		Paramount Vantage													co0179341 (48)			4071 (31)			838
				#		Paramount Players													co0663819 (44)			5793 (32)			96540
				#		Paramount Australia & New Zealand									co0665829 (3)			151548 (3)			202077
				#		Paramount International Networks (DE)								co0969494 (2)
				#		British Paramount News												co0499895 (1)			137858 (1)			188526
				#		Paramount News (US)													co0101044 (1)
				#		Paramount Brand Studio (US)											co1027703 (1)
				#		Paramount Digital Entertainment (US)								co0876322 (1)
				#		Paramount Scope (US)												co0501627 (1)
				#		Paramount - Philippines (PH)										co0075668 (1)
				#		Paramount Comedy (ES)												--co0047950-- (12)
				#
				#		CBS Paramount Network Television									co0183875 (47)			168927 (20)			220148
				#		CBS Paramount Television & Belisarius Productions! (US)				co0405466 (1)
				#		CBS Paramount (US)													co0319948 (0)
				#
				#		Les Studios Paramount												co0094501 (71)			41123 (28)			55709
				#		Les Studios Paramount (Joinville)									--co0066728-- (8)
				#		Paramount Studios, Joinville France (FR)							co0019613 (2)
				#
				#		Vikram-Paramount Studios (IN)										co0445608 (2)			91489 (1)			144771
				#		Paramount-Orion Filmproduktion (DE)									co0069040 (7)			12500 (7)			1407
				#
				#		The Nashville Network (US)											co0465238 (3)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Paramount+ (US)														co0820547 (624)			1623 (112)			4330
				#		Paramount+ (GB)																				2579 (23)			6100
				#		Paramount+ (AU)																				2232 (13)			5506
				#		Paramount+																					2269 (12)			5567
				#		Paramount+ (BR)																				2239 (9)			5511
				#		Paramount+ (DE)																				2790 (8)			6318
				#		Paramount+ (IT)																				2631 (5)			6183
				#		Paramount+ (FR)																				3097 (3)			6445
				#		Paramount+ (KR)																				2444 (0)			5722
				#		Paramount+ (MX)																				2970 (0)			6857
				#		Paramount+ with Showtime											co0979606 (2)			2876 (7)			6631
				#		Paramount Plus (GB)													co0913243 (4)
				#		CBS Studios/Paramount+ (US)											co0865737 (0)
				#
				#		Paramount Network (US)												co0632516 (56)			118 (22)			2076
				#		Paramount Network (GB)												co0778495 (13)
				#		Paramount Network (FI)												co0777243 (11)
				#		Paramount Network (NL)												co0947664 (2)
				#		Paramount Network (ES)																		614 (1)				2604
				#		Paramount Network (IT)																		2605 (1)			6101
				#
				#		The Nashville Network (TNN) (US)									co0046264 (53)			1778 (6)			588
				#		The National Network (TNN) (US)										co0027042 (24)
				#		The New TNN (US)													co0985255 (1)			440 (4)				2103
				#
				#		Spike (NL)																					1324 (2)			1735
				#		Spike (US)															co0053846 (12)			34 (121)			55
				#		Spike (GB)															co0533814 (63)			2005 (1)			5122
				#		Spike TV (US)														co0099482 (172)
				#		Spike TV (IT)														co0926308 (1)
				#		Spike.com (US)														co0673785 (1)
				#		Spike Cable Networks (US)											co0456008 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Paramount Pictures (US)												co0023400 (4663)
				#		Paramount Pictures (MX)												co0819892 (79)
				#		Paramount Pictures (BR)												co0033409 (77)
				#		Paramount Pictures (CA)												co0808354 (51)
				#		Paramount Pictures (AR)												co0817224 (22)
				#		Paramount Pictures (ES)												co0834967 (18)
				#		Paramount Pictures (GB)												co0940470 (3)
				#		Paramount Pictures (NO)												co0809207 (0)
				#		Paramount Pictures (FI)												co0817225 (0)
				#
				#		Paramount Channel (FR)												co0796240 (436)
				#		Paramount Channel (IT)												co0591004 (146)
				#		Paramount Channel (PL)												co0793559 (6)
				#		Paramount Channel España (ES)										co0611782 (3)
				#		Paramount Channel (HU)												co0508924 (2)
				#		Paramount Channel (US)												co0749795 (2)
				#		Paramount Channel (MX)																		3354 (1)			7244
				#		Paramount Comedy Channel (GB)										co0051884 (29)
				#
				#		Paramount Films (NL)												co0011257 (145)
				#		Paramount Films (GB)												co0878210 (0)
				#		Paramount Films (FI)												co0807232 (0)
				#		Paramount Films (MX)												co0896806 (0)
				#		Paramount Film (DK)													co0297121 (0)
				#
				#		Paramount Home Entertainment (US)									co0051891 (1929)
				#		Paramount Home Entertainment (JP)									co0087315 (84)
				#		Paramount Home Entertainment (DE)									co0309607 (67)
				#		Paramount Home Entertainment (MX)									co0819893 (59)
				#		Paramount Home Entertainment (AU)									co0999387 (6)
				#		Paramount Home Entertainment (ES)									co0986034 (5)
				#		Paramount Home Entertainment (FI)									co1071435 (1)
				#
				#		Paramount Home Video (US)											co1044155 (16)
				#		Paramount Home Video (GB)											co0204503 (10)
				#		Paramount Home Video (DE)											co0204462 (1)
				#		Paramount Pictures Home Video (MX)									co1061662 (8)
				#
				#		Paramount (FR)														co0021163 (91)
				#		Paramount (IT)														co0160703 (62)
				#		Paramount (JP)														co0231973 (44)
				#		Paramount (US)														co0858764 (19)
				#		Paramount (GB)														co0739819 (3)			2192 (0)			5419
				#
				#		Paramount Pictures (US)												co0023400 (4663)
				#		Paramount Pictures Germany (DE)										co0317706 (81)
				#		Paramount Pictures UK (GB)											co0822247 (75)
				#		Paramount Pictures France (FR)										co0919972 (45)
				#		Paramount Pictures Spain (ES)										co0638721 (36)
				#		Paramount Pictures Japan (JP)										co0573273 (27)
				#		Paramount Pictures Australia (AU)									co0822249 (26)
				#		Paramount Pictures Nordic (SE)										co0202723 (0)
				#		Paramount Pictures of Panama (PA)									co0847149 (0)
				#
				#		Paramount Pictures International (US)								co0198704 (53)
				#		Paramount Pictures International (BR)								co0349683 (15)
				#		Paramount Pictures International (MX)								co0349864 (14)
				#		Paramount Pictures International (AU)								co0349935 (13)
				#		Paramount Pictures International (CN)								co0277788 (5)
				#		Paramount Pictures International (NZ)								co0235370 (2)
				#		Paramount Pictures International (BO)								co0349601 (1)
				#		Paramount Pictures International (GB)								co0198680 (0)
				#
				#		Paramount Pictures Digital Entertainment							co0226970 (9)
				#		Paramount Pictures Corporation (CA)									co0138659 (1)
				#		Paramount Pictures Drapery Department (US)							co0440806 (2)
				#		Paramount Pictures/Broadway Video Motion Pictures					co0111166 (0)
				#		Paramount Pictures Entertainment (CA)								co0245428 (0)
				#
				#		Paramount Film Service (AU)											co0316662 (763)
				#		Paramount Film Service (CA)											co0754555 (762)
				#		Paramount Film Service (GB)											co0107991 (1)
				#		Paramount Film Service (SG)											co0316628 (0)
				#		Paramount Film Service (US)											co0219746 (0)
				#		Paramount Film Service (MY)											co0868203 (0)
				#		Paramount Film Service Pty. (NZ)									co0847150 (0)
				#
				#		Paramount Films of India (IN)										co0318358 (362)
				#		Paramount Films of Mexico (MX)										co0834860 (155)
				#		Paramount Films of Argentina (AR)									co0866247 (70)
				#		Paramount Films de España (ES)										co0086041 (63)
				#		Paramount Films of Italy (IT)										co0068790 (33)
				#		Paramount Films of Norway (NO)										co0867803 (1)
				#		Paramount Films of England (GB)										co0848844 (0)
				#		Paramount Films of Peru (PE)										co0695983 (0)
				#		Paramount Films of Columbia (CO)									co0689776 (0)
				#		Paramount Films of Egypt (EG)										co0870433 (0)
				#		Paramount Films of Philippines (PH)									co0847151 (0)
				#		Paramount Films of Cuba (CU)										co0834861 (0)
				#		Paramount Films of Belgium (BE)										co0662231 (0)
				#		Paramount Films of Chile (CL)										co0662236 (0)
				#		Paramount Films de Venezuela (VE)									co0662229 (0)
				#		Paramount Films of China (CN)										co0877199 (0)
				#		Paramount Films of France (FR)										co0868045 (0)
				#		Paramount Films of French North Africa (FR)							co0666792 (0)
				#
				#		Paramount-Films (FI)												co0184442 (245)
				#		Paramount-Film (DE)													co0160099 (112)
				#		Paramount-Film (AT)													co0244783 (27)
				#		Paramount-Film (FR)													co0151286 (0)
				#
				#		Films Paramount (BE)												co0850646 (120)
				#		Films Paramount (IT)												co0052142 (2)
				#		Films Paramount (FR)												co0076191 (0)
				#
				#		Les Films Paramount (FR)											co0094762 (347)
				#		Les Films Paramount S.A. (FR)										co0128329 (0)
				#		Les Studios Paramount de Saint-Maurice (US)							co0039221 (1)
				#
				#		Film AB Paramount (SE)												co0220414 (978)
				#		Paramount Filmes (PT)												co0803844 (226)
				#		Filmaktieselskabet Paramount (DK)									co0316507 (222)
				#		Filmaktieselskapet Paramount (NO)									co1022855 (199)
				#		Paramount Oxford Films (US)											co0943142 (1)
				#
				#		CBS Paramount Domestic Television (US)								co0170466 (84)
				#		CBS Paramount International Television (US)							co0135308 (41)
				#		Paramount International Television (US)								co0090065 (4)
				#		Paramount's Worldwide Television Licensing & Distribution (US)		co0599662 (4)
				#		Paramount Worldwide Television Distribution (US)					co0037676 (1)
				#		Paramount Television & Digital Television Distribution (ES)			co0583146 (1)
				#		Paramount Television Ltd. (GB)										co0005212 (0)
				#
				#		Paramount British Pictures (GB)										co0074341 (1482)
				#		British Paramount													co0039958 (1)
				#		British Paramount (GB)												co0499762 (0)
				#		Paramount British Productions (GB)									co0750721 (0)
				#
				#		Paramount Distribution (US)											co0296075 (1)
				#		Paramount Distribution (FR)											co0031167 (0)
				#
				#		United Paramount Network											co0001860 (375)			1989 (0)			5077
				#		Paramount-Ufa-Metro-Verleihbetriebe GmbH (Parufamet) (DE)			co0034406 (86)
				#		Paramount Global Content Distribution (US)							co0957308 (75)
				#		Paramount Classics													co0029291 (58)
				#		Paramount Global													co0906551 (19)
				#		Paramount On Location (US)											co0483087 (9)
				#		Paramount Gateway Video (US)										co0246986 (7)
				#		Paramount Video (PV) (JP)											co0375685 (7)
				#		Paramount Comedy 1																			1111 (3)			2435
				#		Paramount Media Networks (US)										co1019841 (2)
				#		Paramount International (US)										co0048308 (2)
				#		Paramount Worldwide Acquisitions Group (US)							co0242103 (1)
				#		Paramount Communications Company									co0043519 (1)
				#		Paramount Insurge (US)												co0327534 (1)
				#		Paramount Presents (US)												co1042408 (1)
				#		Paramount Travel (ZA)												co0254086 (1)
				#		Paramount Video Transfer (US)										co0221920 (1)
				#		Paramount Newsreel Library (US)										co0651759 (1)
				#		Paramount Images (US)												co0124108 (1)
				#		Paramount Magazine													co0038360 (0)
				#		Paramount Group (US)												co0267721 (0)
				#		Paramount Productions (JP)											co0334177 (0)
				#		Paramount Home Media Distribution (US)								co0985535 (0)
				#		Paramount Overseas Productions Inc.									co0012106 (0)
				#		Paramount Movies (GB)												co0962134 (0)
				#		Paramount Collection (DE)											co0194150 (0)
				#		Paramount Filmforgalmi (HU)											co0316667 (0)
				#		Paramount Camera (US)												co0630473 (0)
				#		Paramount S.A. (BE)													co0142091 (0)
				#		Paramount Consumer Products (US)									co0963678 (0)
				#		Paramount Artcraft Pictures (US)									co0003407 (0)
				#
				#		Fox-Paramount Home Entertainment (FI)								co0453999 (78)
				#		Fox-Paramount Home Entertainment (NO)								co0565880 (32)
				#		Fox-Paramount Home Entertainment (DK)								co0601119 (23)
				#		Fox-Paramount Home Entertainment (SE)								co0604098 (16)
				#
				#		Société Anonyme Française des Films Paramount (FR)					co0131790 (167)
				#		Paramount Famous Lasky Corporation (US)								co0048343 (39)
				#		Paramount-Artcraft Pictures (US)									co0001917 (36)
				#		Ananey - Paramount (IL)												co0097692 (33)
				#		Dzwiekowy film "Paramountu" (PL)									co0521586 (4)
				#		Film Wytwórni Paramount (PL)										co0521548 (3)
				#		ABC-Paramount (US)													co0327798 (1)
				#		Paramount-Arbuckle													co0049835 (0)
				#		Paramount-Revcom (US)												co0626466 (0)
				#		Paramount / United International Pictures (ZA)						co0210910 (0)
				#		Paramount/Sony														co0028920 (0)
				#		Dreamworks / Paramount Distribution (US)							co0253584 (0)
				#		BBC/Paramount Pictures (GB)											co0774810 (0)
				#
				#	Place all Viacom companies here, since they would clutter the Paramount studio/network menus too much.
				#	These are included in the CBS studios/networks.
				#
				#		ViacomCBS International Studios (GB)								co0817261 (75)
				#		ViacomCBS Digital Studios International (US)						co0796824 (3)
				#		ViacomCBS Entertainment & Youth Studios (US)						co0820546 (0)
				#
				#		Viacom International Studios (VIS) (GB)								--co0792121-- (21)
				#		Viacom International Studios (VIS) (US)								--co0777272-- (6)
				#		Viacom International Studios (VIS) (ES)								--co0986109-- (1)
				#		Viacom International Studios (VIS) (IT)								--co0981944-- (1)
				#		Viacom International Studios (VIS) (MX)								--co1036784-- (0)
				#
				#		Viacom Productions (US)												--co0059559-- (75)
				#		Viacom Digital Studios (US)											--co0711545-- (9)
				#		Viacom New Media (US)												--co0046874-- (5)
				#		Viacom Canada (CA)													--co0014596-- (4)
				#		Viacom 2018 (US)													--co0799268-- (1)
				#		Viacom Music Group (US)												--co0500949-- (1)
				#		Viacom Brand Solutions (DE)											--co0310688-- (1)
				#		Viacom Media Networks Production Development (US)					--co0503634-- (0)
				#
				#		Viacom18 Motion Pictures (IN)										--co0328195-- (93)
				#		Viacom18 Studios (IN)												--co0948947-- (12)
				#		Viacom 18 Motion Pictures (IN)										--co0833681-- (9)
				#		Viacom TV (US)																			--1225-- (0)		3189
				#		Viacom Media Networks (US)											--co0501767-- (35)
				#		Viacom International Media Networks (VIMN) (US)						--co0557187-- (24)
				#		Viacom International Media Networks (VIMN) (GB)						--co0623530-- (5)
				#		Viacom International Media Networks Germany (DE)					--co0967236-- (1)
				#
				#		Viacom International (US)											--co0109027-- (60)
				#		Viacom International Asia Pacific (HK)								--co0511913-- (0)
				#
				#		Viacom (US)															--co0077647-- (628)
				#		Viacom18 (IN)														--co0246047-- (159)
				#		Viacom Enterprises													--co0020918-- (29)
				#		Viacom Velocity (US)												--co0668963-- (1)
				#
				#		ViacomCBS Global Distribution Group (US)							--co0776051-- (56)
				#		Viacom Entertainment Group (US)										--co0070713-- (7)
				#		ViacomCBS Domestic Media Networks (US)								--co1072706-- (1)
				#		ViacomCBS Streaming (US)											--co0870263-- (0)
				#
				#		BET Networks/Viacom (US)											--co0176390-- (75)
				#		Scratch, Viacom Media Networks (US)									--co0367788-- (1)
				#
				#		Viacom Music Library (US)											--co1043873-- (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyParamount : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Paramount Pictures'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Paramount+'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Paramount'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Paramount Originals'},
					'expression'	: '(paramount|viacom[\s\-\_\.\+]*cbs)',
				},

				#################################################################################################################################
				# Peacock
				#
				#	Co-productions with Hulu, Sky, etc.
				#		https://en.wikipedia.org/wiki/List_of_Peacock_original_programming
				#	All other "Peacock ..." companies listed on IMDb are other unrelated companies.
				#
				#	Parent Companies:		NBCUniversal
				#	Sibling Companies:		NBC, Universal, Hayu, Bravo, Hulu (previous)
				#	Child Companies:		-
				#
				#	Owned Studios:			Peacock Productions
				#	Owned Networks:			Peacock
				#
				#	Streaming Services:		Peacock
				#	Collaborating Partners:	NBC, Universal, Hayu, Bravo, Hulu, Sky
				#
				#	Content Provider:		NBC, Universal
				#	Content Receiver:		Hayu, Bravo
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(191)					(37)
				#	Networks																(829)					(178)
				#	Vendors																	(0)						(0)
				#	Originals																(165 / 272)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Peacock Productions (US)											co0011738 (56)			19161 (37)		5656
				#		Peacock Kids (US)													co0848470 (9)
				#		Peacock Jr. (US)													co0848665 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Peacock (US)														co0764707 (676)			550 (178)			3353
				#		Peacock (GB)														co0893462 (3)
				#		Peacock / Universal Television										co0859748 (1)
				#		Peacock																						3027 (0)			6951
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyPeacock : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Peacock Productions'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Peacock'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Peacock'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Peacock Originals'},
					'expression'	: '(^(?:(?:nbc|universal).*)?peacock(?:.*(?:nbc|universal|kid|junior|jr|production)|$))',
				},

				#################################################################################################################################
				# Philo
				#
				#	Joint venture between various companies.
				#
				#	Parent Companies:		Hearst, A&E, AMC, Paramount, Warner, Disney
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		A&E, AMC, Paramount, Warner, Disney
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(0)						(0)
				#	Networks																(6)						(0)
				#	Vendors																	(0)						(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Philo																co0035988 (5)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyPhilo : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Philo'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Philo'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(philo)',
				},

				#################################################################################################################################
				# Pixar
				#
				#	Parent Companies:		Disney
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Disney
				#
				#	Content Provider:		-
				#	Content Receiver:		Disney+, Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(143)					(173)
				#	Networks																(0)						(0)
				#	Vendors																	(12)					(0)
				#	Originals																(48 / 15)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Pixar Animation Studios												co0017902 (143)			1690 (173)			3
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Pixar (CA)															co0348691 (4)
				#		Pixarvision (US)													co0593882 (3)
				#		Pixar Talking Pictures (GB)											co0791909 (1)
				#		Pixar Archives (US)													co0894998 (1)
				#		Pixar Information Systems (US)										co0087268 (1)
				#		The Pixar Co-Operative Film Program (US)							co1070967 (1)
				#		Pixar Animation Studios - Facilities, Security & Media CC (US)		co1042473 (1)
				#		Pixar Systems Group (US)											co0754045 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyPixar : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Pixar Studios'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Pixar'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Pixar Originals'},
					'expression'	: '(pixar(?:[\s\-\_\.\+]*vision)?)',
				},

				#################################################################################################################################
				# Pluto TV
				#
				#	Free ad-supported streaming television service owned by Paramount.
				#
				#	Parent Companies:		Paramount
				#	Sibling Companies:		Paramount+
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			Pluto TV
				#
				#	Streaming Services:		Pluto TV
				#	Collaborating Partners:	Paramount
				#
				#	Content Provider:		-
				#	Content Receiver:		Paramount
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(0)						(0)
				#	Networks																(967)					(8)
				#	Vendors																	(0)						(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Pluto TV (US)														co0545791 (931)			744 (7)			3245
				#		Pluto TV (BR)																				3133 (1)		7091
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyPluto : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Pluto TV'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Pluto'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(pluto[\s\-\_\.\+]*tv)',
				},

				#################################################################################################################################
				# Regency Enterprises
				#
				#	Previously called "Embassy International Pictures N.V." (not be be confused with "Embassy Pictures")
				#	and "Regency International Pictures".
				#
				#	There was also an unrelated Australian company "Regency Media Group".
				#
				#	Parent Companies:		Arnon Milchan (partial, majority), 20th Century Studios (partial, minority)
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			New Regency Productions, New Regency Television International
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(325)					(192)
				#	Networks																(0)						(0)
				#	Vendors																	(11)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		New Regency Productions (US)										co0007127 (268)			5947 (8)			490
				#		New Regency Pictures (US)																	4662 (94)			10104
				#		New Regency (US)													co1007086 (4)
				#
				#		Regency Enterprises (US)											co0867908 (24)			4659 (122)			508
				#		Regency Enterprizes (US)											co0172093 (1)
				#
				#		Regency Television																			2589 (12)			37714
				#		Regency Entertainment												co0057227 (3)
				#
				#		Regency International Pictures (AU)									co0023875 (6)
				#		Regency International Pictures																15831 (2)			22639
				#
				#		Embassy International Pictures (US)									co0066289 (8)			13896 (5)			10214
				#
				#	Not sure if it is the same company, probably not.
				#
				#		Regency Productions													--co0056359-- (7)		--11804-- (8)		42121
				#		Regency																--co0040632-- (3)
				#		Regency Films														--co0027859-- (2)
				#		Regency Films (GB)													--co0271310-- (1)
				#		Regency Films (US)													--co1048660-- (0)
				#
				#	Other companies with the same name.
				#
				#		Regency Square Entertainment (GB)									--co0753563-- (1)
				#		Regency Vision														--co0053514-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Regency Entertainment (US)											co0169144 (7)
				#
				#		Regency International (US)											co0802353 (4)
				#		Regency International (HK)											--co0349867-- (1)
				#
				#	Other companies with the same name.
				#
				#		Regency Media (AU)													--co0321874-- (31)
				#		Regency Home Video													--co0052337-- (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyRegency : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'New Regency Pictures'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Regency'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(new[\s\-\_\.\+]*regency|regency[\s\-\_\.\+]*(?:enterpri[sZ]es?|television|entertainment|international)|embassy[\s\-\_\.\+]*international[\s\-\_\.\+]*pictures)',
				},

				#################################################################################################################################
				# RKO Pictures
				#
				#	Member of the "original" Big Five.
				#	Disolved in 1957. Few smaller "revival" companies started in the 70s and 80s.
				#	Now the RKO library is controlled by Warner Bros Discovery.
				#
				#	Parent Companies:		Radio-Keith-Orpheum Corp. (previous), Warner Bros Discovery (library rights)
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			RKO Pictures
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(2577)					(1248)
				#	Networks																(0)						(0)
				#	Vendors																	(2833)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		RKO Radio Pictures													co0041421 (1104)		3490 (1178)			6
				#		RKO Pictures (US)													co1012051 (10)
				#		RKO Pictures LLC (US) (new revived company)													7103 (29)			46976
				#
				#		RKO Radio British Productions (GB)									co0103147 (8)			17698 (7)			14128
				#		Radio Keith Orpheum (R.K.O.) (FR)									co0570527 (1)
				#
				#		RKO Pathé Pictures (US)												co0055570 (32)			17058 (51)			105710
				#		RKO-Pathe Studios Inc.												co0015766 (1)
				#
				#		RKO/Nederlander Productions											co0032881 (1)			117985 (4)			169052
				#		RKO/Nederlander														co0041353 (1)
				#
				#		RKO Vaudeville Circuit (US)											co0434677 (1)
				#		RKO-Jomar Productions (US)											co0030174 (1)
				#		RKO Stanley-Warner Corporation (US)									co0063400 (1)
				#		Cooperativa Cinematográfica RKO de Cuba (CU)						co0181377 (1)
				#		RKO Van Beuren Productions (US)										co0142236 (0)
				#		R K O Productions (US)												co0181770 (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		RKO Radio Pictures (US)												co0041421 (1104)
				#		RKO Radio Pictures (GB)												co0119009 (859)
				#		RKO Radio Pictures de México (MX)									co0010029 (224)
				#		RKO Radio Pictures Argentina (AR)									co0227201 (186)
				#		RKO Radio Pictures do Brazil (BR)									co0536351 (115)
				#		RKO Radio Pictures Chilena (CL)										co0227091 (74)
				#		RKO Radio Pictures del Peru (PE)									co0232178 (71)
				#		RKO Radio Pictures (SE)												co0553775 (52)
				#		RKO Radio Pictures of Cuba (CU)										co0686069 (52)
				#		RKO Radio Pictures (NO)												co0179449 (44)
				#		RKO Radio Pictures (BE)												co0231823 (42)
				#		RKO Radio Pictures (DE)												co0187385 (40)
				#		RKO Radio Pictures S.A. (FR)										co0787886 (21)
				#		RKO Radio Pictures (FR)												co0228093 (16)
				#		RKO Radio Pictures (FI)												co0185060 (8)
				#		RKO Radio Pictures S. A. B. (BE)									co0800706 (5)
				#		RKO Radio Pictures (JP)												co0228057 (1)
				#		RKO Radio Pictures (AU)												co0228654 (1)
				#		RKO Radio Pictures (A/SIA) (AU)										co0088033 (1)
				#		RKO Radio Pictures (PA)												co0226998 (0)
				#		RKO Radio Pictures (MY)												co0727473 (0)
				#		RKO Radio Pictures (Philippines) (PH)								co0658761 (0)
				#		RKO Radio Pictures (PH)												co0228795 (0)
				#		RKO Radio Pictures (Trinidad) (TR)									co0658762 (0)
				#		RKO Radio Pictures (TT)												co0231046 (0)
				#		RKO Radio Pictures (PL)												co0444348 (0)
				#		RKO Radio Pictures. (IN)											co0937233 (0)
				#		RKO Radio Pictures (IN)												co0227165 (0)
				#		RKO Radio Pictures (DK)												co0477404 (0)
				#		RKO Radio Pictures (CH)												co0244861 (0)
				#		RKO Radio Pictures I (IN)											co0864136 (0)
				#		RKO Radio Pictures Near East (EG)									co0232138 (0)
				#		RKO Radio Pictures (NZ)												co0730403 (0)
				#		RKO Radio Pictures (IT)												co0413143 (0)
				#		RKO Radio Pictures (TR)												co0229869 (0)
				#		RKO Radio Pictures of Japan (JP)									co0659060 (0)
				#		RKO Radio Pictures. (BE)											co0673681 (0)
				#		RKO Radio Pictures (Asia) (AU)										co0781566 (0)
				#		RKO Radio Pictures (EG)												co0227029 (0)
				#		RKO Radio Pictures (BR)												co0228777 (0)
				#		RKO Radio Pictures (UY)												co0727706 (0)
				#		RKO Radio Pictures (CA)												co0674253 (0)
				#		RKO Radio Pictures (Asia) Pty (MY)									co0863848 (0)
				#		RKO Radio Pictures (CU)												co0867874 (0)
				#		RKO Radio Pictures (PE)												co0228660 (0)
				#		RKO Radio Pictures (Asia) Pty (NZ)									co0863849 (0)
				#
				#		RKO Radio Films (SE)												co0413144 (334)
				#		RKO Radio Films A/S (NO)											co0134686 (153)
				#		RKO Radio Films (NL)												co0237410 (53)
				#		RKO Radio Films (FR)												co0217289 (44)
				#		RKO Radio Films (FI)												co0216147 (40)
				#		RKO Radio Films (BE)												co0647480 (27)
				#		RKO Radio Films (IT)												co0644319 (26)
				#		RKO Radio Films (ES)												co0422029 (14)
				#		RKO Radio Filmgesellschaft (DE)										co0786409 (11)
				#		RKO Radio Films SpA (IT)											co0070644 (5)
				#		RKO Radio Film (DK)													co0298865 (3)
				#		RKO Radio Films (DE)												co0294557 (1)
				#		RKO Radio Films (SD)												co0228656 (0)
				#		RKO Radio Films A. B. (SD)											co0671570 (0)
				#		RKO Radio Films Sp. Z. O. O. (PL)									co0781567 (0)
				#		RKO Radio Films (PL)												co0522672 (0)
				#		RKO Radio Films (PT)												co0229874 (0)
				#		RKO Radio Films (AT)												co0227694 (0)
				#
				#		RKO Radio (MX)														co0885328 (1)
				#		RKO Radio (FR)														co0158195 (1)
				#		RKO Radio (US)														co0462005 (0)
				#		RKO Radio (IT)														co0380711 (0)
				#
				#		RKO General (US)													co0092195 (14)
				#		RKO General Pictures (US) (black-and-white TV)						co0056735 (9)
				#
				#		RKO Classic (JP)													co0363180 (1)
				#		RKO Comedy Classics (US)											co0273555 (1)
				#
				#		R.K.O. Radio Films (IT)												co0878304 (2)
				#		R.K.O. Radio Pictures (AT)											co0218291 (0)
				#		R. K. O. Radio Pictures (IT)										co0187074 (0)
				#
				#		RKO Distributing Corporation of Canada (CA)							co0786380 (564)
				#		RKO Pictures (Australasia) (AU)										co0786630 (531)
				#		RKO Home Video (US)													co0052638 (78)
				#		RKO (JP)															co0226417 (7)
				#		RKO Films (ES)														co0577797 (1)
				#		RKO Videogroup (US)													co0530337 (1)
				#		RKO Central (US)													co0944451 (1)
				#		RKO International (US)												co0067639 (0)
				#		R K O Productions (US)												co0181770 (0)
				#		RKO Teleradio Pictures (US)											co0047507 (0)
				#		RKO Tobis (FR)														co0035000 (0)
				#		RKO Challenge (AU)													co0044939 (0)
				#
				#		RKO-Pathé Distributing Corp. (US)									co0053128 (26)
				#		Nippon RKO Eiga (JP)												co0980884 (2)
				#		Leopold Barth R.K.O. Radio Pictures (AT)							co0220630 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyRko : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'RKO Pictures'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'RKO'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '((?:^|[\s\-\_\.\+])r[\s.]*k[\s.]*o(?:$|[\s\-\_\.\+\/])|radio[\s\-\_\.\+]*keith[\s\-\_\.\+]*orpheum)',
				},

				#################################################################################################################################
				# Roku
				#
				#	Started as a brand selling streaming boxes and smart TVs.
				#	Now they also have an own channel and a few originals.
				#	Roku bought all the Quibi content.
				#
				#	Parent Companies:		Roku
				#	Sibling Companies:		-
				#	Child Companies:		Quibi (Roku bought all Quibi content)
				#
				#	Owned Studios:			-
				#	Owned Networks:			The Roku Channel
				#
				#	Streaming Services:		The Roku Channel, Quibi
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(0)						(0)
				#	Networks																(358)					(58)
				#	Vendors																	(0)						(0)
				#	Originals																(34 / 192)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Roku (US)															co0364962 (123)
				#		The Roku Channel (US)												co0850678 (94)			1867 (2)			4692
				#		Roku Television (US)												co0566316 (23)
				#		Roku Originals (US)													co0952202 (19)
				#		The Roku Network (US)												co0495245 (3)
				#
				#		Gospel Express Showcase (Roku Channel)														3853 (8)			7542
				#		TCL Roku (US)														co0699790 (6)
				#		Flamingo Network on Roku (US)										co1031799 (6)
				#		RM Entertainment Channel for Roku (US)								co0864985 (5)
				#		Beta Max TV, Roku (US)												co0577538 (2)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyRoku : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Roku Channel'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Roku'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Roku Originals'},
					'expression'	: '((?:$^|[^a-z\d])roku(?:$|[^a-z\d]))',
				},

				#################################################################################################################################
				# Screen Gems
				#
				#	Parent Companies:		Sony
				#	Sibling Companies:		Columbia Pictures, TriStar Pictures, Affirm Films
				#	Child Companies:		-
				#
				#	Owned Studios:			Screen Gems
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Columbia Pictures, TriStar Pictures
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(2020)					(186)
				#	Networks																(0)						(0)
				#	Vendors																	(2009)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Screen Gems (US)													co0010568 (1263)		391 (130)			3287
				#		Screen Gems (IN)													co0145747 (3)
				#		Screen Gems																					59039 (2)			102506
				#
				#		Screen Gems Television (US)											co0033007 (139)			376 (53)			12551
				#
				#		Screen Gems Productions (US)										co0148620 (2)
				#		Screen Gems Productions (IN)										co0675845 (1)
				#
				#		Screen Gems of Brasil (BR)											co0075450 (2)			51582 (1)			53877
				#		Screen Gems GmbH (DE)												co0240976 (1)
				#		Europe Screen Gems													co0011282 (1)
				#		Screen Gems Cartoons (US)											co0830233 (0)
				#
				#	Other production companies.
				#
				#		EUE/Screen Gems Studios (US)										--co0000502-- (19)
				#		EUE/Screen Gems Video Services (US)									--co0056083-- (2)
				#		Screen Gems EMI Music Inc. (US)										--co0152848-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Screen Gems (US)													co0010568 (1263)
				#		Screen Gems Television (US)											co0033007 (139)
				#		EUE Screen Gems Documentaries (US)									co0964193 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyScreengems : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Screen Gems Productions'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Screen Gems'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(screen[\s\-\_\.\+]*gems?)',
				},

				#################################################################################################################################
				# Showtime
				#
				#	Parent Companies:		Paramount, Viacom (previous), CBS (previous), Warner (previous)
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			Flix, SkyShowtime (Showtime+Sky+Peacock)
				#
				#	Streaming Services:		Showtime, SkyShowtime
				#	Collaborating Partners:	HBO, Cinemax, Sky (SkyShowtime), Paramount+, ITV, CBS, Peacock, BET, A24, MGM, Lionsgate, and many more
				#
				#	Content Provider:		-
				#	Content Receiver:		Netflix, Apple, Amazon, Hulu, Roku, HBO, Playstation Vue
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1841)					(376)
				#	Networks																(1995)					(229)
				#	Vendors																	(329)					(0)
				#	Originals																(109 / 310)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Showtime Networks													co0052980 (846)			191 (327)			4343
				#		Showtime Entertainment												co0048667 (39)
				#		Showtime Documentary Films											co0628396 (23)			43380 (39)			66479
				#		Showtime																					125949 (19)			148935
				#		Showtime Films																				12808 (9)			5861
				#		Showtime Independent Films											co0161345 (8)			69830 (3)			109369
				#		Showtime Original Pictures											co0048307 (4)
				#		Showtime Pictures													co0074825 (2)
				#		Showtime Entertainment Television									co0045143 (2)			25867 (7)			72494
				#		Showtime Pictures Inc.												co0065559 (1)			36301 (6)			37014
				#		Showtime Pictures Production (AU)									co1021008 (1)
				#		Showtime Pro Wrestling (Showtime) (US)								co0866626 (1)
				#		Showtime Championship Boxing (US)									co0877020 (1)
				#		Showtime Pictures Development Company (US)							co0458723 (1)
				#		Showtime Original Pictures for All Ages								co0047886 (1)
				#		Showtime Entertainment Group										co0049409 (1)
				#		Showtime Theatre Productions (US)									co0166446 (1)
				#
				#	Other companies with the same name.
				#
				#		Showtime Productions (GR)											--co0399743-- (10)
				#		Showtime Productions GVL (US)										--co0717602-- (9)
				#		Showtime Productions (GB)											--co0486329-- (2)
				#		Showtime Films														--co0051333-- (1)
				#		Showtime International (TW)	(unsure if a different company)			--co0700148-- (4)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Showtime Networks													co0052980 (846)
				#
				#		Showtime																					50 (201)			67
				#		Showtime (FI)														co0903913 (16)
				#		Showtime (KR)														co0212571 (14)
				#		Showtime (IT)														co0014147 (0)
				#
				#		Showtime Australia													co0011881 (51)
				#		Showtime Arabia														co0329011 (3)
				#
				#		Showtime 2															co0913372 (43)
				#		Showtime Sports														co0553743 (8)
				#		Showtime Beyond														co0927319 (2)
				#
				#		SHO.com																						1834 (2)			1814
				#		SHO Entertainment Inc.												co0067309 (1)			42814 (1)			96024
				#		SHO Films															co0652000 (1)
				#		showcase (AU)																				326 (10)			1630
				#
				#		SkyShowtime															co0901457 (17)			2737 (11)			5944
				#		SkyShowtime (GB)													co0944921 (4)
				#		SkyShowtime España (ES)												co1036849 (2)
				#		SkyShowtime Norge (NO)												co0984498 (1)
				#
				#		Paramount+ with Showtime											co0979606 (2)			2876 (7)			6631
				#
				#	Other companies with the same name.
				#
				#		Showcase (CA)																				--3-- (26)			105
				#		Showcase TV (GB)																			--1136-- (1)		471
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Showtime Video (FI)													co0087627 (145)
				#		Showtime DVD (AU)													co0121751 (21)
				#		Showtime Showtime Home Video										co0630026 (2)
				#		Showtime Home Video													co0125959 (0)
				#		Showtime Video Distribution Inc.									co0081812 (0)
				#		Showtime Event Television											co0377252 (0)
				#
				#		Orbit Showtime Network												co0363506 (25)
				#		Showtime/The Movie Channel											co0362187 (5)
				#		Rautakirja / Showtime (FI)											co0316643 (3)
				#		Showtime/Premium Movie Partnership									co0029265 (1)
				#		Showtime Films (CA)													co0142105 (1)
				#		ShowTime International (AE)											co0329014 (1)
				#		Sony Pictures Television Showtime (US)								co0872067 (0)
				#		XTRM (ES)															co0698040 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyShowtime : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Showtime Pictures'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Showtime'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Showtime'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'Showtime Originals'},
					'expression'	: '(showtime|^(?:showcase|xtrm)$|^sho(?:$|\.com|[\s\-\_\.\+]*(?:film|entertainment)))',
				},

				#################################################################################################################################
				# Sky
				#
				#	Parent Companies:		Comcast
				#	Sibling Companies:		NBC, Universal, SkyShowtime
				#	Child Companies:		-
				#
				#	Owned Studios:			Sky Studios
				#	Owned Networks:			Sky, Sky Showcase, Sky Max, Sky Atlantic, BSkyB, NOW, WOW
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	NBC, Universal, Peacock, HBO, Cinemax, Showtime, SkyShowtime
				#
				#	Content Provider:		-
				#	Content Receiver:		Peacock, HBO, Cinemax, Showtime, NOW, WOW
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(420)					(376)
				#	Networks																(3917)					(567)
				#	Vendors																	(98)					(7)
				#	Originals																(701 / 1026)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Sky Original Productions																	75014 (36)			117455
				#		Sky Originals (GB)													co0542151 (11)
				#		Sky Original Films (GB)												co1021520 (4)
				#		sky Reality Originals (GB)											co1025909 (1)
				#
				#		Sky Studios (GB)													co0716013 (67)			78934 (57)			135346
				#		Sky Studios International (US)										co0445144 (7)			65407 (4)			35398
				#		Sky Studios (IT)																			162046 (6)			213972
				#		Sky Studio (US)														co0545188 (2)
				#		SKY Studios (IT)													co1069222 (1)
				#		Sky Studios I (GB)													co0857784 (1)
				#
				#		Sky Pictures																				8184 (11)			1097
				#		Sky Pictures (GB)													co0103904 (11)
				#		Sky Pictures (AU)													co0295048 (1)
				#
				#		Sky Cinema Production (GB)											co0612777 (3)
				#		Sky Cinema (GB)																				166142 (2)			217564
				#
				#		Sky Vision Productions (GB)																	7006 (18)			14543
				#		Sky Vision Productions (US)											co0490861 (1)
				#
				#		Sky One Productions (GB)											co0104200 (3)
				#		Sky One Productions (US)											co0397479 (1)
				#		Sky 1																						16105 (3)			56337
				#		Sky 1 Productions (US)												co0398019 (0)
				#
				#		Sky Arte (IT)														co0415969 (39)
				#		Sky Arts																					12080 (33)			85575
				#		Sky Arte HD (IT)																			9581 (23)			41019
				#		Sky Arts Production Hub (IT)										co0703862 (7)
				#
				#		Sky News / News International (GB)									co0190730 (1)
				#		Sky News																					74838 (12)			100498
				#
				#		Sky Productions														co0023737 (1)			1874 (7)			66595
				#		Sky Production Services (GB)										co0726023 (2)
				#		Sky Movies Production (GB)											co0226867 (1)
				#		Sky Productions (US)												co0654428 (1)
				#		Sky World Productions (US)											co0155760 (0)
				#
				#		Sky Italia (IT)														co0196688 (113)			1208 (62)			53597
				#		Sky Deutschland														--co0277926-- (91)		2276 (14)			62274
				#		Sky Schweiz															co0979861 (12)			115008 (1)			166005
				#
				#		Sky (GB)																					136528 (35)			181068
				#		Sky TV																						2779 (17)			2954
				#		Sky Movies																					32502 (14)			17685
				#		Sky 3D																						46389 (7)			41021
				#		Sky Entertainment Group (US)										co0151983 (8)			65406 (2)			35397
				#		Sky Creative (GB)													co0798268 (1)
				#		Sky Drama (GB)														co0950126 (1)
				#		Sky Family Life TV (IT)												co0253854 (1)
				#		Sky Sport News (DE)													co0854725 (1)
				#		Sky Bet (GB)														co0984914 (1)
				#
				#		British Sky Broadcasting (BSkyB) (GB)								--co0103727-- (231)		3192 (28)			7102
				#		B Sky B (GB)														co0466362 (2)
				#		ACEtrax Productions (US)											co0299588 (1)
				#
				#	Not sure if these are part of the Sky Group. Leave disabled for now.
				#
				#		Sky Studios (US)													--co0637734-- (4)
				#		Sky Pictures (US)													--co0388225-- (4)
				#		Sky Penguin (GB)													--co0527935-- (1)
				#		Sky Radio (US)														--co0342863-- (1)
				#		Sky Penguin Media (GB)												--co0492142-- (1)
				#		British Sky (GB)													--co0998090-- (1)
				#		Sky Rentals (US)													--co0662803-- (1)
				#		Sky 21 Productions (US)												--co0230906-- (0)
				#		Sky 1 Productions (US)												--co0398019-- (0)
				#
				#	Other companies with the same name.
				#
				#		Sky Crew Productions (CA)											--co1031951-- (1)
				#		Grey/Sky Pictures (US)												--co0421498-- (1)
				#		Sky Sea Films (TW)													--co0358228-- (2)
				#		SkyWatchTV (US)														--co0599665-- (8)
				#		skyTV (KR)															--co0891103-- (1)
				#		SkyWatch Studios Inc. (US)											--co0349588-- (1)
				#		Skyplex Pictures (US)												--co0314052-- (1)
				#		SKYFILM Studio Ltd.													--co0106679-- (4)
				#		Skyland Films (GB)													--co0649529-- (1)
				#		Skydirects Flix (US)												--co0954523-- (1)
				#		Skyworks Films (US)													--co0852184-- (1)
				#		Skybox Films (US)													--co0384451-- (3)
				#		Skyvision Entertainment (CA)										--co0469672-- (1)
				#		SkySoft Entertainment (US)											--co0615710-- (5)
				#		SkyFoxx Productions (CA)											--co0823343-- (1)
				#		Sky Reach Productions (GB)											--co0459636-- (1)
				#		Sky High Media (US)													--co0370939-- (1)
				#		Skyfarm Entertainment (CA)											--co0400513-- (4)
				#		SkyCross Entertainment (AU)											--co0769884-- (4)
				#		SKY Reel Productions (US)											--co0303849-- (1)
				#		Sky Visuals (AU)													--co0695526-- (2)
				#		SKY Studios (IN)													--co0440658-- (1)
				#		SKY Pictures (IN)													--co1073541-- (1)
				#		Sky High Entertainment (CA)											--co0093441-- (1)
				#		Skyworks (GB)														--co0110470-- (14)
				#		Second Sky Studios (US)												--co0608155-- (1)
				#		Sky Production (RU)													--co0731762-- (1)
				#		SKY HD (KR)															--co0569322-- (1)
				#		Sky Bridge (US)														--co0524118-- (1)
				#		Sky TV Pvt. Ltd. (IN)												--co0063766-- (1)
				#		SkyWatch Films (US)													--co0821628-- (1)
				#		Sky Touching Films (AU)												--co0926235-- (1)
				#		Sky High Productions (US)											--co0520393-- (1)
				#		Sky Movies (NG)														--co0304708-- (5)
				#		Sky Arts (RU)														--co1061704-- (1)
				#		Sky King Productions (US)											--co0138295-- (1)
				#		SkyCo Productions (US)												--co0647574-- (0)
				#		Sky Media Filmz (CA)												--co1018225-- (1)
				#		Asian Sky Entertainment (IN)										--co0385496-- (1)
				#		Sky Machine (AU)													--co0263086-- (1)
				#		Sky Quest Entertainment (US)										--co0977300-- (5)
				#		Sky Media Production (RU)											--co0999095-- (1)
				#		Sky Theory Studios (US)												--co1013572-- (3)
				#		SKY Perfect Broadcasting (JP)										--co0339119-- (2)
				#		Sky Nine Productions (US)											--co0475251-- (2)
				#		Sky Production (IN)													--co0711484-- (1)
				#		Sky Pictures (BR)													--co0530331-- (8)
				#		Sky Woman Productions (AU)											--co0756100-- (1)
				#		Sky Tribe Pictures (US)												--co0695714-- (1)
				#		Sky Culture Entertainment (US)										--co0607630-- (3)
				#		Sky Direct Action (US)												--co0657521-- (1)
				#		Sky Point															--co0001681-- (1)
				#		Skymax Cine Vision (IN)												--co0994771-- (1)
				#		Ský (IS)															--co0211632-- (2)
				#		Sky Entertainment (TH)												--co0984772-- (1)
				#		Sky Definition (CA)													--co1000799-- (1)
				#		Sky Productions. (IL)												--co0941569-- (0)
				#		Sky Link TV (US)													--co0939677-- (1)
				#		Sky Motion Pictures (IN)											--co0268983-- (1)
				#		Sky Media Polska (PL)												--co0329096-- (1)
				#		Sky Cinema Productions (IN)											--co0615874-- (1)
				#		Sky Safari (US)														--co0753784-- (1)
				#		Popcorn Sky Productions (US)										--co0255502-- (3)
				#		Sky Pictures (TR)													--co0851743-- (1)
				#		Skymax (NL)															--co0923904-- (1)
				#		Sky Limit Group (US)												--co1008836-- (0)
				#		SkyNation Publishing (AU)											--co0930753-- (0)
				#		Contented Sky Productions (US)										--co0330580-- (1)
				#		Sky Films (IN)														--co0703776-- (1)
				#		Sky Earth Productions (TW)											--co0264326-- (1)
				#		Sky Lantern Productions (US)										--co0715569-- (1)
				#		Sky High Films (US)													--co0694066-- (1)
				#		Sky Train Entertainment (US)										--co0528026-- (1)
				#		Skyflix (US)														--co1027617-- (1)
				#		SkyHi Digital (US)													--co0955254-- (1)
				#		Sky Ops Entertainment (US)											--co0479658-- (1)
				#		Sky City Entertainment												--co0038580-- (1)
				#		Sky (RS)															--co0736865-- (1)
				#		Sky Net Pictures (IN)												--co0826490-- (1)
				#		SkyMedia (SG)														--co0335584-- (4)
				#		Sky Dojo Media (US)													--co0703727-- (1)
				#		Skyhigh TV (NL)														--co0184144-- (22)
				#		Skynet Media (US)													--co0912665-- (1)
				#		Sky Dragon International (US)										--co0521536-- (1)
				#		Sky Films (US)														--co0073579-- (3)
				#		Sky Media Entertainment (US)										--co0730263-- (1)
				#		Sky High Entertainment (US)											--co0221606-- (1)
				#		SKY Argentina (AR)													--co0549573-- (1)
				#		Sky Media (ID)														--co0979013-- (3)
				#		Sky Candy Studios (US)												--co0703784-- (1)
				#		Sky Media (CA)														--co0675805-- (0)
				#		Skyfox Media (CA)													--co1053347-- (1)
				#		Sky Prime Productions (US)											--co0837695-- (1)
				#		Sky Films (TR)														--co0853716-- (16)
				#		SKY Motion Pictures Group (HK)										--co0388293-- (1)
				#		Sky Film (TW)														--co0166643-- (1)
				#		Sky Media (US)														--co0833745-- (1)
				#		Sky Films (ID)														--co0841096-- (4)
				#		Sky Film Production (IN)											--co0855166-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Sky (GB)															co0050995 (277)
				#		Sky (IT)															co0169165 (99)			583 (13)			1114
				#		Sky UK (GB)															co0701341 (11)
				#		Sky (DE)															co1005815 (6)			2237 (9)			5136
				#		Sky (NZ)															co0943021 (4)			2347 (9)			5735
				#		Sky (IE)															co0951621 (3)
				#		Sky (CH)															co1062041 (1)
				#		Sky (II) (GB)														co0614200 (1)
				#		Sky																							2905 (0)			6713
				#
				#		Sky Deutschland (DE)												co0277926 (91)
				#		Sky Österreich (AT)													co0979860 (12)
				#		Sky Schweiz (CH)													co0979861 (12)
				#		Sky Austria (AT)													co1017869 (2)
				#		Sky España (ES)														co0774567 (1)
				#
				#		Sky One (GB)														co0104193 (204)			187 (199)			214
				#		Sky One (DE)														co0615219 (45)
				#		Sky 1 (DE)															co0995552 (13)			496 (13)			1431
				#		Sky 1 +1 (DE)														co0894261 (10)
				#		Sky One HD (GB)														co0187094 (7)
				#		Sky1HD (GB)															co0323771 (5)
				#		Sky 1 (GB)															co0488036 (4)
				#		Sky One (MX)														co1073520 (1)
				#		Sky One (MX)																				2100 (1)			5059
				#		Sky One (UK)																				2521 (0)			5989
				#		Sky 1 HD (GB)														co0909121 (0)
				#
				#		Sky Uno (IT)														co0481199 (9)			750 (23)			1076
				#		Sky Three (GB)														co0187356 (3)
				#		Sky Two (GB)																				1116 (1)			405
				#
				#		Sky Serien & Shows (DE)												co0901569 (26)
				#		SKY Show (IT)														co0228600 (1)
				#		Sky serie																					3070 (1)			7030
				#		Sky Show (DE)																				2241 (0)			5525
				#
				#		Sky TV (GB)															co0103971 (73)
				#		Sky TV (IT)															co0887040 (3)
				#
				#		Sky History Channel (GB)											co0825565 (26)
				#		Sky Channel (NL)													co0248896 (13)
				#		Sky Channel (GB)													co0547057 (6)
				#		Active Channel (Sky TV) (GB)										co0376754 (2)
				#		Showcase TV Sky Channel (GB)										co0577710 (2)
				#
				#		Sky Movies (GB)														co0169100 (22)
				#		Sky Movies (NZ)														co0301439 (2)
				#
				#		Sky Cinema (GB)														co0276736 (110)
				#		Sky Cinema (DE)														co0952255 (83)
				#		Sky Cinema (IT)														co0254125 (82)			678 (10)			877
				#
				#		Sky Cinema Special (DE)												co0919122 (68)
				#		Sky Cinema Best Of (DE)												co0985385 (61)
				#		Sky Cinema Premieren (DE)											co0971524 (61)
				#		Sky Cinema Premieren +24 (DE)										co0971525 (57)
				#		Sky Cinema Action (DE)												co0919121 (57)
				#		Sky Cinema Hits (DE)												co0952256 (40)
				#		Sky Cinema +1 (DE)													co0985309 (39)
				#		Sky Cinema +24 (DE)													co0985310 (39)
				#		Sky Cinema Family (DE)												co0970200 (37)
				#		Sky Cinema Fun (DE)													co0985311 (30)
				#		Sky Cinema Transformers (DE)										co1056655 (28)
				#		Sky Cinema Classics (DE)											co0905512 (23)
				#		Sky Cinema Thriller (DE)											co0919123 (22)
				#		Sky Cinema Nostalgie (DE)											co0905511 (19)
				#		Sky Cinema Premiere (DE)											co1061120 (16)
				#		Sky Cinema Comedy (DE)												co1003875 (15)
				#		Sky Cinema Emotion (DE)												co0986610 (14)
				#		Sky Cinema Highlights (DE)											co1056656 (10)
				#		Sky Cinema Awards (DE)												co0985384 (3)
				#		Sky Cinema Distribution (CZ)										co1067888 (4)
				#		Sky Cinema Back to the 80s (DE)										co1058027 (1)
				#
				#		Sky Atlantic HD (DE)												co0374625 (101)
				#		Sky Atlantic (GB)													co0329071 (55)			284 (42)			1063
				#		Sky Atlantic (IT)													co0472197 (21)			1022 (27)			2667
				#		Sky Atlantic (DE)																			1996 (5)			5090
				#		Sky Atlantic +1 (DE)												co0989607 (2)
				#
				#		Sky Vision (GB)														co0447329 (59)
				#		Sky Vision																					1424 (6)			3138
				#		Sky Vision (US)														co0401180 (5)
				#		Sky Vision (ID)														co0088784 (4)
				#		SkyVision															co0060930 (1)
				#		Sky Vision B.V. Belgium (BE)										co1020952 (0)
				#
				#		Sky Go (DE)															co0893022 (189)
				#		Sky Go (GB)															co0663240 (2)
				#		Sky Go (NZ)																					3817 (1)			7520
				#		SkyGo																						3550 (0)			5505
				#
				#		Sky 3D (DE)															co0391299 (10)
				#		Sky 3d (GB)															co0315254 (2)
				#		Sky 3D (IT)															co0569926 (2)
				#
				#		Sky Showcase HD (DE)												co0967014 (45)
				#		Sky Showcase (GB)													co0878025 (9)			3823 (1)			7524
				#		Sky Showcase (GB)																			2372 (0)			5651
				#
				#		Sky Store (DE)														co0985386 (249)
				#		Sky Store (GB)														co0931305 (1)
				#
				#		Sky Krimi (DE)														co0840513 (39)			3179 (2)			2699
				#		Sky Crime (GB)														co0788771 (19)			1071 (20)			3653
				#		Sky Crime (DE)														co0965885 (15)			3597 (1)			6179
				#
				#		Sky Comedy (DE)														co0285888 (33)
				#		Sky Comedy (GB)														co0787982 (24)			2050 (7)			5213
				#
				#		Sky Documentaries (GB)												co0803868 (67)			1601 (25)			4148
				#		Sky Documentaries (DE)												co0885421 (21)
				#		Sky Documentaries (IT)																		2421 (2)			5481
				#
				#		Sky Nature (GB)														co0804062 (31)
				#		Sky Nature																					1682 (20)			4439
				#		sky nature (DE)														co0966569 (11)			3685 (1)			7438
				#
				#		Sky Arts (GB)														co0228643 (75)
				#		Sky Arte HD (IT)													co0411058 (27)
				#		Sky Arts (GB)																				695 (53)			553
				#		Sky Arts 1 (GB)														co0305913 (4)
				#		Sky Arte (IT)																				2953 (1)			6845
				#		SKY Artsworld (GB)													co0211903 (1)
				#		Sky Arts (DE)														co0573344 (1)
				#		Sky Arts HD Deutschland (DE)										co0703068 (0)
				#
				#		SkyShowtime (US)													co0901457 (17)
				#		SkyShowtime (GB)													co0944921 (4)			2737 (11)			5944
				#		SkyShowtime España (ES)												co1036849 (2)
				#		SkyShowtime Norge (NO)												co0984498 (1)
				#
				#		British Sky Broadcasting (BSkyB) (GB)								co0103727 (231)
				#
				#		Sky Ticket (DE)														co0885190 (96)
				#		Sky Ticket																					2292 (0)			4909
				#
				#		Sky Kids (GB)														co0873210 (86)			2496 (4)			5946
				#		Sky Network Television (NZ)											co0217380 (46)
				#		Sky Replay (DE)														co0899218 (36)
				#		Sky Living (GB)														co0352403 (30)			617 (25)			115
				#		Sky Hits/Sky Hits HD (DE)											co0379754 (24)
				#		Sky Witness (GB)													co0702154 (23)			545 (3)				2691
				#		Sky Max (GB)														co0878026 (21)			2082 (26)			5237
				#		Sky Action (DE)														co0986206 (19)
				#		Sky Nostalgie (DE)													co0905510 (14)
				#		Sky Emotion (DE)													co0995452 (9)
				#		Sky Mix (GB)														co1026404 (6)
				#		Sky Sci-Fi (GB)														co0932376 (4)
				#		Sky Travel (GB)														co0188660 (3)
				#		SKY Vivo (IT)														co0228496 (3)
				#		Sky Box Office (GB)													co0217851 (3)
				#		Sky Business (AU)													co0560305 (1)
				#		Sky Digimedia (MX)													co0693280 (1)
				#		Sky Real Lives (GB)													co0297571 (1)
				#		Sky Investigation (IT)												co0980132 (1)
				#		Sky On Demand (GB)													co0497417 (1)
				#
				#		Sky News Australia (AU)												co0329023 (85)			1159 (4)			819
				#		Sky News (GB)														co0137267 (59)			3346 (4)			480
				#
				#		Sky Sports (GB)														co0106276 (81)			1046 (12)			107
				#		Sky Sport (DE)														co0894054 (4)
				#		Sky Sport (IT)														co0136570 (3)			891 (2)				753
				#		Sky Sport (NZ)														co0811948 (2)
				#
				#		Now TV (GB)															co0778032 (30)			802 (3)			1596
				#		NOW TV (IT)															co1003057 (9)
				#		Now (IT)																					2464 (1)			5652
				#		NOW (GB)															co1034749 (2)
				#		NOW (DE)															co1062045 (1)
				#		NOW (CH)															co1062046 (1)
				#		NOW (IE)															co1062043 (1)
				#		NOW (IT)															co1062044 (1)
				#
				#		WOW (DE)															co0964826 (181)
				#
				#	Other companies with the same name.
				#
				#		Now (TR)																					--3585-- (8)		7380
				#		NOW Claro																					--1972-- (2)		4781
				#		sky Drama (KR)																				--2044-- (1)		3561
				#		SkyLife																						--2046-- (2)		5209
				#		skyTV																						--2047-- (2)		5210
				#		SKY PerfecTV! (JP)													--co0132991-- (18)		--499-- (5)			1037
				#		Sky Films (TW)														--co0451783-- (17)
				#		Sky Films Entertainment (TW)										--co0887398-- (6)
				#		Sky Turk 360 (TR)													--co1066269-- (1)
				#		Sky Entertainment (HK)												--co0228924-- (2)
				#		Sky Entertainment (US)												--co0142902-- (10)
				#		Sky Films (PH)														--co0155754-- (12)
				#		Sky Entertainment (IN)												--co0076685-- (9)
				#		Sky Release (IN)													--co0276566-- (1)
				#		Sky 9 (IN)															--co0840727-- (1)
				#		Sierra Sky Entertainment											--co0077284-- (1)
				#		Sky Digi Entertainment (TW)											--co0334782-- (84)
				#		Escenario SKY (AR)													--co0547279-- (1)
				#		Big Sky Video (AU)													--co0124380-- (28)
				#		Skyline Video (GB)													--co0106011-- (1)
				#		Sky Entertainment Distribution (HK)									--co0203367-- (1)
				#		Sky-Skan (US)														--co0286885-- (1)
				#		Electric Sky (GB)													--co0044260-- (35)
				#		Sky Island Films (US)												--co0100092-- (4)
				#		SKY (GR)															--co0037351-- (1)
				#		Sky A Sports (JP)													--co0212844-- (1)
				#		SKY Türk (TR)														--co0493879-- (2)
				#		Sky Cable (PH)														--co0766830-- (3)
				#		SkyBox International (US)											--co0099478-- (0)
				#		My Sky 219 (GB)														--co0369261-- (0)
				#		Sky Link (US)														--co0229353-- (2)
				#		Skylark (DE)														--co0364065-- (0)
				#		SKYmedia (MN)														--co0876054-- (1)
				#		Sky Den Games (NL)													--co1060505-- (1)
				#		SkySkan (US)														--co0445040-- (1)
				#		Sky Phoenix (US)													--co0232574-- (1)
				#		Sky Entertainment (AE)												--co1031305-- (1)
				#		Skyline Video (DE)													--co0467381-- (33)
				#		Sky Cinema Productions (IN)											--co0615874-- (1)
				#		C-Sky Enterprise (AU)												--co0063627-- (5)
				#		Skylex (DE)															--co0153509- (0)
				#		Odeon Sky Filmworks (GB)											--co0200108-- (5)
				#		Skymedia (MN)														--co0839761-- (1)
				#		Sky Perfect TV! On Demand (JP)										--co0476641-- (1)
				#		SkyDoesMinecraft (US)												--co0874045-- (1)
				#		SKYFILMS Entertainment (CN)											--co0339503-- (1)
				#		Skytail (GB)														--co0919773-- (1)
				#		KT SkyLife (KR)														--co0999691-- (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Sky Sports F1																				2680 (5)			6280
				#		Sky Sports 3 (GB)													co0249192 (4)
				#		Sky Sports F1 (GB)													co0814668 (3)			949 (0)				1852
				#		Sky Sports Boxing (GB)												co0429154 (3)
				#		Sky Sports Main Event (GB)											co0924398 (3)
				#		Sky Sports 1 (GB)													co0944551 (3)
				#		Sky Sports Football (GB)											co0714728 (3)
				#		Sky Sports Mix (GB)													co0816028 (2)
				#		Sky Sports Premier League (GB)										co0958729 (2)
				#		Sky Sports 2 (GB)													co0540454 (1)
				#		Sky Sports Action (GB)												co0849558 (1)
				#		Sky Sports News HQ (SSNHQ) (GB)										co0535961 (1)
				#		Sky Sport F1 (DE)													co0975175 (1)
				#		Sky Sports App (GB)													co0924399 (1)
				#		Sky Sports Golf (GB)												co0790533 (1)
				#		Sky Sports Arena (GB)												co0790669 (1)
				#		sky sport (DE)																				3813 (1)			7516
				#		Sky Sport News																				3914 (1)			7188
				#		Sky Sports Box Office (GB)											co0924319 (0)
				#
				#		Sky News Business (AU)												co0712274 (4)
				#		Sky News Library (GB)												co0293012 (2)
				#		Sky News HD (GB)													co0909049 (1)
				#		Sky News Ireland (IE)												co0232548 (1)
				#		Sky News Arabia (AE)												co0454785 (1)
				#		Sky News Archive (GB)												co0909123 (1)
				#
				#		Sky Cinema DC Helden												co1058414 (4)
				#		SkyMedia Film Distribution (MX)										co0751407 (3)
				#		Sky Media Distribution (MX)											co0972316 (2)
				#		Sky Racing (AU)														co0449873 (1)
				#
				#		Granada Sky Broadcasting (GB)										co0122767 (5)
				#		Sky tv - Canale Marcopolo (IT)										co0334986 (3)
				#
				#		SKY 887 Family Life TV (IT)											co0253846 (2)
				#		Sky TG 24 (IT)														co0253892 (2)
				#		Showcase Sky Channel 192 (GB)										co0577711 (1)
				#		Sky Channel 203 (GB)												co0256832 (1)
				#		Information TV - Sky Channel 212 (GB)								co0577709 (1)
				#		Face Television - Sky Channel 083 (NZ)								co0734975 (1)
				#		My TV Sky 203 UK (GB)												co0469192 (0)
				#
				#		Getty/Sky (GB)														co0703461 (1)
				#		Getty Images/Sky News (GB)											co0978844 (0)
				#
				#	Not sure if these are part of the Sky Group. Leave disabled for now.
				#
				#		Sky View (GB)														--co0335055-- (0)
				#		Sky Perth (AU)														--co1053058-- (0)
				#		Sky Enterprises (US)												--co0485777-- (0)
				#		Sky Networks (US)													--co0182827-- (0)
				#		Sky 0 (GB)															--co0873209-- (0)
				#		Skymax (AU)															--co0731849-- (0)
				#		Skyvision Partners													--co0070128-- (2)
				#		Sky Vision Music Library (US)										--co0786477-- (1)
				#		SkyVR (US)															--co0601347-- (2)
				#
				#################################################################################################################################
				MetaCompany.CompanySky : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Sky Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Sky'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Sky'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Sky Originals'},
					'expression'	: '((?:^|(?:british|tv|showcase|granada)[\s\-\_\.\+]*)sky(?:\d|tv|\d?hd|vision|go|showtime|media)?(?:$|\s)|sky\s(?:tv|channel)|getty.*?sky|b\s*sky\s*b|acetrax|^(?:now|wow)(?:[\s\-\_\.\+]*tv)?$)',
				},

				#################################################################################################################################
				# Sony
				#
				#	Member of the "modern" Big Five.
				#	Since Sony is a Japanese company, they mostly do not own US companies, except for some minority shareholding.
				#	Sony owns mostly Japanese media and Anime companies.
				#		https://sonyentertainment.fandom.com/wiki/List_of_Sony_subsidiaries
				#		https://sony.fandom.com/wiki/Category:Sony_subsidiaries
				#		https://en.wikipedia.org/wiki/Category:Sony_subsidiaries
				#		https://en.wikipedia.org/wiki/List_of_assets_owned_by_Sony
				#	Sony has Originals, but they are mostly Indian/Hindi (Sony Liv) or east-Asian productions.
				#	Also a few other originals under "Sony Pictures Television Original Production".
				#		https://en.wikipedia.org/wiki/Category:Sony_Entertainment_Television_original_programming
				#
				#	Parent Companies:		Sony
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			Sony Pictures, Columbia Pictures, TriStar Pictures, Screen Gems, Bad Wolf, Embassy Row, 3000 Pictures
				#	Owned Networks:			Crunchyroll, Animax, Aniplex, AXN, Lifetime Latin America (partial Sony+A&E)
				#
				#	Streaming Services:		Crunchyroll, Sony Pictures Core (previously known as Bravia Core)
				#	Collaborating Partners:	Columbia Pictures, TriStar Pictures
				#
				#	Content Provider:		-
				#	Content Receiver:		Crunchyroll, Sony Pictures Core
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(2817)					(1182)
				#	Networks																(683)					(174)
				#	Vendors																	(7118)					(0)
				#	Originals																(198 / 233)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Sony Pictures Television 											co0086397 (1334)		8 (277)				11073
				#		Sony Pictures Television International (US) 						co0095398 (265)			2392 (32)			86203
				#		Sony Pictures Television Original Production CEE 					co0628249 (19)
				#		Sony Pictures Television (MX) 										co0622733 (10)
				#		Sony Pictures Television Productions France 						co0147952 (6)
				#		Sony Pictures Television Production UK 								co0312488 (5)
				#		Sony Pictures Television - Kids (US) 								co1002159 (4)
				#		Sony Pictures Television (BR) 										co0443771 (3)
				#		Sony Pictures Television International (IN) 						co0843409 (1)
				#		Sony Pictures Television Studios (US) 								co0782033 (1)
				#
				#		Sony Pictures Animation 											co0121181 (94)			2305 (75)			2251
				#		Sony Animation (JP) 												co0107410 (0)
				#
				#		Sony Pictures (JP) 																			6617 (40)			82346
				#		Sony Pictures (US) 																			1968 (198)			34
				#
				#		Sony Pictures International Productions								co0660299 (45)
				#		Sony Pictures International 										co0053000 (29)			10753 (50)			63520
				#		Sony Pictures International Productions (IN) 						co1006768 (2)
				#		Sony Pictures International Productions (ES) 						co0905480 (2)
				#
				#		Sony Pictures Film und Fernseh Produktions GmbH 					co0171368 (25)			75899 (8)			133259
				#		Sony Pictures Films India 											co0881672 (6)			105856 (12)			157559
				#		Sony Pictures Film- und Fernsehproduktions (DE) 					co0199078 (1)
				#		Sony Pictures Film (DE) 											co0198299 (0)
				#
				#		Sony Pictures Imageworks 											co0042679 (192)			41016 (6)			30692
				#		Sony Pictures Imageworks (US)																173773 (1)			224658
				#		Sony Pictures Classics (US) 																10723 (65)			58
				#		Sony Pictures Networks Productions (IN) 							co0660268 (7)			20585 (11)			94444
				#		Sony Pictures Family Entertainment (US) 							co0013837 (7)
				#		Sony Pictures Digital (US) 											co0074006 (5)			2457 (10)			65451
				#		Sony Pictures Entertainment Company (IN) 							co0304476 (4)
				#		Sony Pictures FFP GmbH (DE) 										co0107503 (4)
				#
				#		Sony Music Entertainment Japan 										co0013638 (208)			3342 (137)			648
				#		Sony Music Entertainmant (US) 																11799 (229)			4375
				#		Sony Music Communications (JP) 										co0181130 (26)			1929 (9)			87086
				#		Sony Music Solutions (JP) 											co0780213 (11)
				#		Sony Music (US) 													co0898832 (8)
				#		Sony Music Associated Records Inc. 									co0164272 (7)			48497 (23)			83980
				#		Sony Music Entertainment Canada 									co0450028 (6)			144379 (2)			195732
				#		Sony Music Spain 													co0151953 (4)			11918 (2)			118997
				#		Sony Music Latin													co0520898 (4)			27372 (10)			19521
				#		Sony Music Entertainment (MX) 										co0611794 (3)
				#		Sony BMG Music Entertainment (FR) 									co0460527 (2)
				#		Sony Music Vision 													co1051393 (1)			168161 (4)			219575
				#		Sony Music Film (US) 												co0251998 (1)
				#		Sony Music Entertainment Picture Works (JP) 						co0101361 (1)
				#
				#		Sony Corporation of Japan (JP) 										co0128891 (12)
				#		Sony Hellas (GR) 													co0221897 (4)
				#		Sony Magazines (JP) 												co0208409 (2)
				#		Sony Mix (IN) 														co0546495 (2)
				#		Sony New Technologies 												co0044974 (1)			80195 (1)			53390
				#		Sony International Motion Picture Production Group 					co0268017 (1)
				#		Sony Digital Entertainment Services (JP) 							co0357755 (1)
				#		Sony Producciones España (ES) 										co0282519 (1)
				#		Sony Film (TW) 														co0703484 (1)
				#		Sony Films (IN) 													co0504899 (1)
				#
				#		Sony / Monumental Pictures 											co0209115 (2)			36601 (2)			15454
				#		Walt Disney Pictures / Sony Pictures (RU) 							co0310744 (2)
				#
				#	Too many other titles.
				#
				#		Sony PCL (JP) 														--co0048780-- (161)
				#		Sony Music Artists (JP) 											--co0165917-- (8)
				#		Sony Pictures (US) 													--co0944611-- (5)
				#		Sony España (ES) 													--co0467534-- (5)
				#		Sony Australia (AU) 												--co0128004-- (4)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Sony Channel (BR) 																			3025 (7)		6850
				#		Sony Channel Latinoamérica (AR) 									co0888494 (5)
				#		Sony Channel (DE) 													co0777056 (1)
				#		Sony Channel Africa (ZA) 											co0624286 (1)
				#
				#		Sony Movie Channel (GB) 											co0372942 (32)
				#		Sony Movie Channel (US) 											co0315317 (17)
				#		Sony Movie Channel (CA) 											co0468659 (2)
				#
				#		Sony Liv (IN) 														co0546496 (130)			1322 (75)		2646
				#		Sonyliv (IN) 														co0777877 (13)
				#		SonyLiv_India (IN) 													co0806273 (5)
				#
				#		Sony Pictures Core (JP) 																	3213 (0)		7144
				#		Sony Pictures CORE (US) 																	3797 (1)		7507
				#
				#		Canal Sony 															co0629937 (1)			1051 (9)		320
				#		Canal Sony (BR) 													co0629936 (7)
				#
				#		Sony Max (IN) 														co0544611 (75)
				#		Sony Crime Channel (GB) 											co0725671 (31)
				#		Sab Sony TV (IN) 													co0547466 (25)
				#		Sony Marathi (IN) 													co0725762 (19)
				#		Sony AXN (DE) 														co0879659 (12)
				#		Sony Rox HD (IN) 													co0657603 (6)
				#		Sony SIX (IN) 														co0431737 (4)
				#		Sony PIX (IN) 														co0460639 (3)
				#		Sony Yay (IN) 														co0822760 (3)			2379 (2)		5619
				#		Sony Spin (BR) 														co0373830 (3)
				#		Sony Pal (IN) 														co0546494 (1)			3335 (1)		1791
				#		Sony Aath (IN) 														co1037981 (1)			3755 (1)		5810
				#		Sony BBC Earth (IN) 																		3501 (1)		7242
				#		Sony Sci-Fi (RU) 													co0479937 (1)
				#		Sony Turbo (RU) 													co0493700 (1)
				#
				#		Sony Entertainment Television 																3378 (1)		7151
				#		Sony Entertainment Television (SET) (IN) 							co0246050 (77)
				#		Sony Entertainment Television Asia (IN) 							co0081728 (34)
				#		Sony Entertainment Television (DE) 									co0434265 (22)
				#		Sony Entertainment Television (MX) 									co0295187 (13)
				#		Sony Entertainment Television (BR) 									co0186035 (11)
				#		Sony Entertainment Television (GB) 									co0361294 (10)
				#		Sony Entertainment Television (AR) 									co0367891 (8)
				#		Sony Entertainment Television (IN) 									co0896022 (6)				309 (89)		676
				#		Sony Entertainment Television (VE) 									co0367866 (4)
				#		Sony Entertainment Television (RU) 									co0351299 (3)
				#		Sony Entertainment Television (HN) 									co0415756 (3)
				#		Sony Entertainment Television (PA) 									co0367927 (2)
				#		Sony Entertainment Television (CL) 									co0367949 (2)
				#		Sony Entertainment Television (NI) 									co0415757 (2)
				#		Sony Entertainment Television (LC) 									co0415760 (2)
				#		Sony Entertainment Television (PY) 									co0415758 (2)
				#		Sony Entertainment Television (CR) 									co0415753 (1)
				#		Sony Entertainment Television (PT) 									co0420621 (1)
				#		Sony Entertainment Television (ZA) 									co0364235 (1)
				#		Sony Entertainment Television Latinoamérica (VE) 					co0482699 (2)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Sony (US) 															co0001799 (130)
				#		Sony (JP) 															co0188620 (74)
				#		Sony (CA) 															co0099317 (8)
				#		Sony (GB) 															co0341744 (6)
				#		Sony (IT) 															co0179937 (5)
				#		Sony (DK) 															co0475310 (4)
				#		Sony (DE) 															co0057635 (2)
				#		Sony (PT) 															co0547312 (1)
				#		Sony (AU) 															co0032740 (1)
				#		Sony (IE) 															co0157130 (0)
				#		Sony (NL) 															co0131639 (0)
				#		Sony Benelux (NL)													co0378943 (1)
				#
				#		Sony Pictures (ES) 													co0775797 (84)
				#		Sony Pictures (MX) 													co0880495 (12)
				#		Sony Pictures (RU) 													co0767764 (11)
				#		Sony Pictures (TH) 													co0832871 (3)
				#		Sony Pictures (NZ) 													co0405210 (3)
				#		Sony Pictures (SG) 													co0796214 (2)
				#		Sony Pictures (FI) 													co0369424 (0)
				#
				#		Sony Pictures Television International (US) 						co0095398 (265)
				#		Sony Pictures Television International (GB) 						co0410527 (5)
				#		Sony Pictures Television (Japan) (JP) 								co0071392 (3)
				#		Sony Pictures Television Networks - Asia (SG) 						co0618335 (3)
				#		Sony Pictures Télévision (FR) 										co0828650 (1)
				#
				#		Sony Pictures Releasing (US) 										co0026545 (863)
				#		Sony Pictures Releasing (BR) 										co0110101 (860)
				#		Sony Pictures Releasing (JP) 										co0052145 (556)
				#		Sony Pictures Releasing (IN) 										co0145664 (334)
				#		Sony Pictures Releasing (AR) 										co0811162 (183)
				#		Sony Pictures Releasing (DE) 										co0873390 (88)
				#		Sony Pictures Releasing (AU) 										co0144567 (67)
				#		Sony Pictures Releasing (CA) 										co0243381 (63)
				#		Sony Pictures Releasing (MX) 										co0881365 (61)
				#		Sony Pictures Releasing (GB) 										co0847351 (60)
				#		Sony Pictures Releasing (IT) 										co0865164 (34)
				#		Sony Pictures Releasing (SE) 										co1003784 (9)
				#		Sony Pictures Releasing (TW) 										co0902939 (7)
				#		Sony Pictures Releasing (RU) 										co0951251 (1)
				#
				#		Sony Pictures Releasing International (FR) 							co0655055 (88)
				#		Sony Pictures Releasing International (BE) 							co0307036 (76)
				#		Sony Pictures Releasing International (HK) 							co0653605 (30)
				#		Sony Pictures Releasing International (TH) 							co0305812 (11)
				#
				#		Sony Pictures Entertainment Iberia (ES) 							co0810034 (24)
				#		Sony Pictures Entertainment (US) 									co0732568 (12)
				#
				#		Sony Entertainment (IN) 											co0163321 (131)
				#		Sony Entertainment (US) 											co0651690 (6)
				#		Sony Entertainment (FR) 											co0213247 (1)
				#		Sony Entertainment (NZ) 											co0122709 (1)
				#
				#		Sony Pictures Home Entertainment (US) 								co0137851 (2836)
				#		Sony Pictures Home Entertainment (DE) 								co0769046 (254)
				#		Sony Pictures Home Entertainment (FI) 								co0185481 (205)
				#		Sony Pictures Home Entertainment (NL) 								co0795863 (110)
				#		Sony Pictures Home Entertainment (GB) 								co0852957 (68)
				#		Sony Pictures Home Entertainment (MX) 								co0765733 (65)
				#		Sony Pictures Home Entertainment (FR) 								co0802090 (63)
				#		Sony Pictures Home Entertainment (AU) 								co0770268 (51)
				#		Sony Pictures Home Entertainment (ES) 								co0789116 (35)
				#		Sony Pictures Home Entertainment (SE) 								co0802089 (23)
				#		Sony Pictures Home Entertainment (IT) 								co0802091 (20)
				#		Sony Pictures Home Entertainment (DK) 								co0835413 (4)
				#		Sony Pictures Home Entertainment (RU) 								co0935482 (3)
				#		Sony Pictures Home Entertainment (CA) 								co1034913 (3)
				#
				#		Sony Video (US) 													co0080433 (69)
				#		Sony Video (JP) 													co0080266 (12)
				#		Sony Video (DE) 													co0514017 (8)
				#		Sony Video (NL) 													co0384875 (6)
				#		Sony Video (ES) 													co0909503 (1)
				#		Sony Vidéo (BE) 													co0328292 (2)
				#
				#		Sony PlayStation (JP) 												co0617378 (3)
				#		Sony Playstation (GB) 												co0246535 (3)
				#
				#		Sony Pictures Classics (US) 										co0014453 (540)
				#		Sony Classical International (DE) 									co0457297 (2)
				#		Sony Classical Film & Video (US) 									co0424487 (1)
				#		Sony Classical (JP) 												co0127139 (0)
				#
				#		Sony Music (US) 													co0898832 (8)
				#		Sony Music (GB) 													co0393339 (4)
				#		Sony Music (BR) 													co0045940 (3)
				#		Sony Music (JP) 													co0226000 (1)
				#
				#		Sony Music Entertainment (US) 										co0072831 (132)
				#		Sony Music Entertainment (DE) 										co0510488 (10)
				#		Sony Music Entertainment (GB) 										co0104245 (9)
				#		Sony Music Entertainment (FR) 										co0281373 (8)
				#		Sony Music Entertainment (IN) 										co0043827 (6)
				#		Sony Music Entertainment (AU) 										co0132903 (3)
				#		Sony Music Entertainment (FI) 										co0462171 (2)
				#		Sony Music Entertainment UK (GB) 									co0980862 (2)
				#		Sony Music Entertainment / Columbia Records (US) 					co0488996 (1)
				#
				#		Sony Music Records (JP) 											co0215255 (22)
				#		Sony Music Direct (JP) 												co0215082 (14)
				#		Sony Music Labels (JP) 												co0472728 (9)
				#		Sony Music France (FR) 												co0009479 (8)
				#		Sony Music Japan International (JP) 								co0309356 (5)
				#		Sony Music Distribution (JP) 										co0219581 (4)
				#
				#		Sony BMG Music Entertainment (US) 									co0151916 (42)
				#		Sony BMG Music Entertaintment (DE) 									co0208861 (9)
				#		Sony BMG Music Entertainment (GB) 									co0270513 (3)
				#		Sony BMG Music Entertainment (ES) 									co0291223 (2)
				#		Sony BMG Music Entertainment (NL) 									co0259638 (2)
				#
				#		Sony BMG (IN) 														co0256964 (15)
				#		Sony/BMG (DK) 														co0165909 (4)
				#		Sony BMG Feature Films (US) 										co0172249 (5)
				#		Sony Music BMG DVD (DE) 											co0253404 (1)
				#
				#		Sony Pictures Filmverleih (AT) 										co0402495 (213)
				#		Sony Pictures Networks (IN) 										co0584895 (98)
				#		Sony Pictures Video (JP) 											co0087306 (76)
				#		Sony Pictures Productions and Releasing (SPPR) (RU) 				co0850664 (12)
				#		Sony Picture Studios (ZA) 											co0469521 (1)
				#		Sony Pictures (Choice Collection) (US) 								co0577179 (1)
				#
				#		SET India (IN)														co0121331 (94)
				#		Sony Wonder (US) 													co0060012 (56)
				#		Sony Corporation of America (US) 									co0071829 (35)
				#		Sony DADC Europe (GB) 												co0815089 (11)
				#		Sony International 													co0143764 (9)
				#		Sony Creative Products (JP) 										co0211045 (8)
				#		Sony Online Entertainment (US) 										co0065232 (6)
				#		Sony Digital Entertainment 											co0033361 (4)
				#		Sony Legacy (US) 													co0613276 (3)
				#		Sony DADC (US) 														co0280381 (3)
				#		Sony Network Entertainment (US) 									co0349334 (2)
				#		Sony Home Entertainment (GB) 										co0825216 (1)
				#		Sony Special Products (US) 											co0139175 (1)
				#		SONY Projection screens (US) 										co0558021 (1)
				#		Sony Signatures (US) 												co0211298 (0)
				#		Sony (CDA) 															co0064651 (0)
				#		Sony Pictures Worldwide Acquisitions (SPWA) (US) 					--co0208736-- (289)
				#
				#		Universal Sony Pictures Home Ent. (AU) 								co0375381 (358)
				#		Universal Sony Pictures Home Ent. Nordic (FI) 						co0533783 (248)
				#		Universal Sony Pictures Home Ent. Nordic (SE) 						co0600878 (82)
				#		Universal Sony Pictures Home Ent. Nordic (NO) 						co0565929 (70)
				#		Universal Sony Pictures Home Ent. Nordic (DK) 						co0565928 (42)
				#
				#		Walt Disney Studios Sony Pictures Releasing (WDSSPR) (RU)			co0209825 (269)
				#		Walt Disney Pictures / Sony Pictures (RU) 							co0310744 (2)
				#		Walt Disney Pictures / Sony Pictures (DK)							co0254863 (0)
				#
				#		CBS Sony Group Inc. (JP) 											co0064922 (14)
				#		CBS/Sony Records (JP) 												co0101612 (5)
				#		Movic / CBS Sony Group (JP) 										co0309278 (1)
				#		Sony Pictures Television/CBS (US)									co0927303 (0)
				#
				#		ABC Studios/Sony Pictures Television (US)							co0859939 (0)
				#		Sony Pictures Television/ABC (US)									co0868243 (0)
				#		ABC / Sony Pictures Television (US)									co0842694 (0)
				#
				#		Epic/Sony (JP) 														co0088857 (5)
				#		Cine Sony (IT) 														co0665131 (3)
				#		Paramount/Sony														co0028920 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanySony : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Sony Pictures'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Sony Channel'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Sony'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Sony Originals'},
					'expression'	: '((?:^|[^a-z])sony(?:[\s\-\_\.\+]*liv)?(?:$|[^a-z]))',
				},

				#################################################################################################################################
				# Starz
				#
				#	Parent Companies:		Lionsgate
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			Starz
				#
				#	Streaming Services:		Starz
				#	Collaborating Partners:	Lionsgate
				#
				#	Content Provider:		Lionsgate
				#	Content Receiver:		Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(21)					(2)
				#	Networks																(633)					(77)
				#	Vendors																	(47)					(0)
				#	Originals																(231 / 107)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Starz Originals (US)												co0280576 (10)
				#		Starz! Pictures														co0067269 (1)			19655 (2)			25277
				#		Starz & FX Photography (US)											co0482786 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Starz (US)															co0000869 (315)			272 (70)			318
				#		Starz 2 (CA)														co0793760 (1)
				#		Starz (II) (US)														co0635080 (0)
				#
				#		StarzPlay (GB)														co0746532 (14)
				#		StarzPlay (US)														co0740154 (13)
				#		StarzPlay (DE)														co0746531 (9)
				#		StarzPlay Arabia (AE)												co0809057 (5)			2270 (1)			5594
				#		Starzplay																					2700 (3)			6292
				#		Starzplay																					3323 (1)			6222
				#		Starzplay																					2298 (0)			5650
				#		Starzplay By Cinepax (PK)											co0786037 (1)
				#
				#		Starz Encore (US)													co0002342 (33)			1053 (2)			758
				#		Starz! Movie Channel												co0010826 (12)
				#		Starz Edge (US)														co1069971 (1)
				#
				#		Starz Kids and Family (US)											co0238789 (14)
				#		Starz Kids & Family (US)											co1042752 (3)
				#		Starz Kidz & Family (US)											co1042751 (0)
				#
				#		Starz InBlack (US)													co0186042 (3)
				#		Black Starz! (US)													co0002075 (1)
				#
				#		Starz / Anchor Bay (US)												co0316607 (18)
				#		Starz / Anchor Bay (GB)												co0530112 (4)
				#
				#		Starz Digital Media (US)											co0324445 (31)
				#
				#		Movieplex Entertainment (CA)										co1018571 (1)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Starz Home Entertainment (US)										co0198595 (19)
				#		Starz Home Entertainment (AU)										co0209315 (11)
				#		Starz Home Entertainment (GB)										co0224655 (5)
				#
				#################################################################################################################################
				MetaCompany.CompanyStarz : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Starz'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Starz'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'Starz Originals'},
					'expression'	: '(starz[\s\-\_\.\+]*(?:play|encore|edge|\!)?|(?:movie|indie|retro)[\s\-\_\.\+]*plex)',
				},

				#################################################################################################################################
				# Syfy
				#
				#	Parent Companies:		NBCUniversal, USA Network (previous), Paramount (previous), Universal (previous)
				#	Sibling Companies:		NBC, Bravo, CNBC, MSNBC, E!, Oxygen, USA Network, DreamWorks Channel, Telemundo
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			Sci-Fi Channel, SyFy
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	NBC, Universal, CTV Sci-Fi Channel
				#
				#	Content Provider:		-
				#	Content Receiver:		Peacock, Hulu, CTV Sci-Fi Channel
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(38)					(116)
				#	Networks																(1244)					(156)
				#	Vendors																	(0)						(0)
				#	Originals																(454 / 203)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Syfy (US)																					253 (82)			6677
				#		Sci-Fi Channel (US)																			1871 (23)			5856
				#		Syfy Films (US)														co0321669 (7)
				#		Sci Fi Pictures (US)												co0169785 (3)			17816 (14)			4774
				#		Sci Fi Films (US)													co0242100 (0)
				#
				#	Other production companies.
				#
				#		SyFy Wire (US)														--co0908226-- (1)
				#
				#	Not sure if these belong to Syfy. Leave disabled for now.
				#
				#		Sci-Fi Productions													--co0029087-- (2)		--27339-- (3)		24196
				#		Sci-Fi Studios (US)													--co0984787-- (1)
				#		Sci Fi Geek Productions (US)										--co0539486-- (5)
				#		Sci-Fi Works (US)													--co0282953-- (1)
				#		Sci-Fi-London Films (GB)											--co0431053-- (1)
				#		Sci-Fi Lab (US)														--co0064892-- (1)
				#		Sci-Fi Polska (PL)													--co0938915-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Syfy (US)															co0282285 (391)			17 (152)			77
				#		SyFy (DE)															co0876404 (35)
				#		Syfy (FR)															co0951622 (10)
				#		Syfy (DE)																					1219 (2)			3701
				#		Syfy (ES)															co0951623 (2)
				#		Syfy (CH)															co0951626 (1)
				#		Syfy (BE)															co0951625 (1)
				#		Syfy (PT)															co0951624 (1)
				#
				#		Syfy Universal (NL)													co0298911 (32)
				#		Syfy Universal (FR)													co0308282 (26)
				#		Syfy Universal (ES)													co0370054 (5)
				#		Syfy Universal (PT)													co0307546 (2)
				#		Syfy Universal (SG)													co0619890 (1)
				#		Syfy Universal (RU)													co0311751 (1)
				#
				#		Syfy España (ES)													co1041024 (2)
				#		SyFy Venture (US)													co0561779 (1)
				#
				#		The Sci-Fi Channel (US)												co0024368 (230)
				#		The Sci-Fi Channel (GB)												co0002937 (31)
				#		The Sci-Fi Channel (AU)												co0293780 (1)
				#
				#		Sci-Fi Channel (PL)													co0470060 (16)
				#		Sci Fi Channel (NL)													co0288390 (8)
				#		Sci-Fi Channel (US)													co1049885 (1)
				#		Sci Fi Channel (BA)													co0619861 (1)
				#		Sci-Fi Channel (PH)													co0619887 (1)
				#		Sci Fi Channel (HR)													co0619866 (1)
				#		Sci Fi Channel (NI)													co0619878 (1)
				#		Sci Fi Channel (BR)													co0619860 (1)
				#
				#		Sci Fi (JP)															co0234798 (16)
				#		Sci Fi (FR)															co0289068 (13)
				#		Sci Fi (DE)															co0188604 (7)
				#		Sci Fi (US)															co0174586 (4)
				#		Sci Fi (AU)															co0306623 (4)
				#		Sci Fi (ES)															co0229476 (2)
				#		Sci-Fi (DE)															co1056650 (2)
				#		Sci Fi (PL)															co0369798 (1)
				#
				#		Sci Fi Universal (PL)												co0370118 (2)
				#		Sci Fi Pulse (US)													co0220940 (1)
				#
				#		SF Channel (AU)														co0449313 (4)
				#		SF Channel (JP)														co0311104 (1)
				#
				#	Gets most programs from Syfy.
				#
				#		CTV Sci-Fi Channel (CA)												co0810364 (6)			2167 (3)			5337
				#
				#	Not sure if these belong to Syfy. Leave disabled for now.
				#
				#		SyFy Media (CN)														--co1049391-- (0)
				#		SyFy Media Group (CN)												--co1049390-- (0)
				#		Sci Fi Mombie Podcast (US)											--co1030488-- (0)
				#
				#	Other companies with the same name.
				#
				#		Sci-Fi Alliance (US)												--co0464785-- (1)
				#		Sci-Fi Verse (US)													--co0631019-- (1)
				#		Sci-Fi-London (GB)													--co0273464-- (1)
				#		Sci-Fi Center (US)													--co0357262-- (1)
				#		Sci-Fi Central (US)													--co0943730-- (1)
				#		Sci-Fi Pictures Inc./Magna Distribution Corp.						--co0070936-- (1)
				#		Sci-Fi Locker (AU)													--co0707955-- (0)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanySyfy : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Syfy Pictures'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Syfy'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Syfy'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'Syfy Originals'},
					'expression'	: '(syfy|(?:^|(?:the|ctv)\s)sci[\s\-]fi(?:$|\s(?:channel|picture|film|universal|pulse))|sf[\s\-\_\.\+]*channel)',
				},

				#################################################################################################################################
				# TBS
				#
				#	Name also used by Tokyo Broadcasting System (TBS). Exclude all Japanese companies.
				#
				#	Parent Companies:		Warner Bros. Discovery, Turner (previous)
				#	Sibling Companies:		TNT, HBO, The CW, The WB, other Warner companies
				#	Child Companies:		-
				#
				#	Owned Studios:			TBS Productions
				#	Owned Networks:			TBS, WTBS
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Turner, Warner, Discovery
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(33)					(26)
				#	Networks																(820)					(107)
				#	Vendors																	(3)						(0)
				#	Originals																(212 / 251)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		TBS Productions Inc. (US)											co0100472 (5)			53929 (7)			118582
				#		TBS Productions (US)												co0573042 (4)
				#		TBS Productions (GB)												co0683031 (0)
				#
				#		Turner Broadcasting System																	38744 (18)			118356
				#		Turner Broadcasting System Asia Pacific														45876 (1)			75182
				#
				#		TBS TV (US)															co0334947 (3)
				#		TBS On Demand (KR)													co1037480 (1)
				#		TBS Pictures																				110634 (1)			161846
				#
				#	Other companies with the same name.
				#
				#		tbsProductions (NL)													--co0251735-- (3)
				#		TBS Films (ID)														--co0747605-- (1)
				#		TBS Medien GmbH (DE)												--co0028039-- (1)
				#		TBS Retecapri (IT)													--co0483916-- (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		TBS (US)																					161 (105)			68
				#		TBS (BR)																					2514 (1)			5968
				#		TBS (KR)																					2909 (0)			5012
				#		TBS																							1892 (0)			4718
				#		TBS																							3682 (0)			7436
				#		TBS (ES)															co0867778 (1)
				#		TBS (AR)															co0688123 (5)
				#
				#		Turner Broadcasting System (TBS) (US)								co0005051 (306)
				#		Turner Broadcasting System (ES)										co0418169 (9)
				#		Turner Broadcasting System Deutschland (DE)							co0396917 (9)
				#		Turner Broadcasting System (BR)										co0528223 (6)
				#		Turner Broadcasting System (CL)										co0756309 (6)
				#		Turner Broadcasting System (FR)										co0505494 (3)
				#		Turner Broadcasting System Asia Pacific (HK)						co0569273 (2)
				#		Turner Broadcasting System Europe (GB)								co1000321 (0)
				#
				#		TBS Superstation (US)												co0183474 (176)
				#		WTBS (US)															co0057274 (16)
				#		WTBS Atlanta																				3899 (1)			2517
				#
				#		TBS.com (US)																				3572 (1)			5625
				#		TBS-CHANNEL1																				1953 (0)			4872
				#		TBS On Demand (KR)													co1037480 (1)
				#		TBS Films (US)														co0541624 (0)
				#
				#	Other companies with the same name.
				#
				#		TBS (JP)																					--73-- (750)		160
				#		TBS (JP)																					--3956-- (1)		7592
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		TBS Distributing													co0012522 (1)
				#		TBS Theatrical Booking Company (US)									co0972823 (1)
				#		TBS/HBO Comedy Festival (US)										co0568014 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyTbs : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'TBS Productions'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'TBS'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'TBS'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'TBS Originals'},
					'expression'	: '(tbs|turner[\s\-\_\.\+]*broadcasting[\s\-\_\.\+]*system)',
				},

				#################################################################################################################################
				# TNT
				#
				#	Formerly part of Turner, now owned by Warner Bros. Discovery.
				#	TCM was launched as "TNT Film" and later rebranded to TCM.
				#	In some countries it TCM operates as TNT, in others as TCM.
				#	Currently it seems TCM only has a subset of TNT content.
				#	TNT Serie and other TNT European companies are now WarnerTV.
				#
				#	Parent Companies:		Warner Bros. Discovery, Turner (previous)
				#	Sibling Companies:		TBS, HBO, The CW, The WB, other Warner companies
				#	Child Companies:		-
				#
				#	Owned Studios:			TNT Productions
				#	Owned Networks:			TNT
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Turner, Warner, Discovery
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(83)					(111)
				#	Networks																(1409)					(141)
				#	Vendors																	(103)					(0)
				#	Originals																(337 / 234)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Turner Network Television (US)																2027 (95)			678
				#		TNT (GR)															co0224166 (9)
				#		TNT Spain (ES)														co0447313 (4)
				#		TNT (PL)															co0617058 (1)
				#		TNT (DE)															co0617059 (0)
				#
				#		TNT Originals (US)													co0088248 (9)
				#		TNT Original Prods (US)												co0366683 (0)
				#
				#		TNT Film Productions (US)											co0212433 (9)			15890 (4)			26508
				#		TNT Film on Site Productions (US)									co0407107 (1)
				#		TNT Films (GB)														co0480705 (1)
				#		TNT Filmworks (US)													co0873052 (1)
				#
				#		TNT Productions (US)												co0447226 (2)
				#		TNT Productions (GB)												co0474332 (1)
				#
				#		TNT Entertainment (US)												co0344872 (1)
				#		TNT Digital Media Production (US)									co0375990 (1)
				#		TNT Titalators (US)													co0259875 (0)
				#
				#		TCM ESPAÑA																					5006 (12)			107074
				#		TCM Original (ES)													co0499377 (3)
				#		TCM Productions (US)												co0465048 (0)
				#
				#	Companies with the same name.
				#
				#		TNT Premier Studios													--co0748384-- (9)		--1741-- (161)		119813
				#		Tnt Limited Productions (US)										--co0341552-- (2)
				#		TNT Production (CZ)													--co0457876-- (1)
				#		TNT Studio (RO)														--co0583994-- (1)
				#		TNT Eventures (DE)													--co0313233-- (1)
				#		TNT: Dynamite Productions (US)										--co0720811-- (1)
				#		TNT Operations														--co0040985-- (1)
				#		TnT Creative Ventures (US)											--co0654953-- (1)
				#		TNT Extreme Wrestling (GB)											--co0861639-- (1)
				#		TnT Films Production (ES)											--co0722089-- (0)
				#		TNT Team (US)														--co0832158-- (0)
				#		TnT Films (ES)														--co0722092-- (0)
				#		TNT Filmproduktion Berlin (DE)										--co0672703-- (0)
				#		asso TNT (FR)														--co0291421-- (0)
				#
				#		TCM Creative (US)													--co0930037-- (1)
				#		TCM (IN)															--co0738637-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		TNT (US)															co0009512 (342)			382 (97)			41
				#		TNT (ES)																					1356 (7)			3501
				#		TNT (GR)															co0224166 (9)
				#		TNT (TR)															co1010896 (4)
				#		TNT (BR)															co0675903 (3)
				#		TNT (ES)															co0893018 (2)
				#		TNT (NL)															co1029550 (1)
				#		TNT (AR)															co1064922 (1)
				#		TNT (PL)															co0617058 (1)
				#		TNT (DE)															co0617059 (0)
				#		TNT (GB)															co1068047 (0)
				#
				#		TNT Latin America																			320 (16)			1530
				#		TNT Latin America (AR)												co0418278 (6)
				#		TNT América Latina													co0024749 (5)
				#
				#		TNT Sports (AR)														co0771916 (16)
				#		TNT Sports (GB)																				3117 (4)			7043
				#		TNT Sports (US)														co0241737 (3)
				#		TNT Sports (CL)														co0852643 (3)
				#
				#		TNT Serie (DE)														co0257711 (84)			497 (6)			904
				#		TNT Series (AR)														co0724274 (20)
				#
				#		TNT Sverige (SE)													co0449308 (4)
				#		TNT España (ES)														co0887203 (3)
				#		TNT Türkiye (TR)													co1059526 (0)
				#
				#		TNT Film (DE)														co0350722 (54)
				#		TNT Comedy															co0607678 (21)			910 (4)			2857
				#		TNT Glitz (DE)														co0561952 (6)
				#		Turner Network Television (TNT) (US)								co0835799 (5)
				#		TNT Pictures														co0037608 (2)
				#		TNT Media (US)														co0239363 (1)
				#		TNT & Cartoon Network Asia (HK)										co0868070 (0)
				#
				#		Turner Classic Movies (US)											co0011489 (199)			1110 (7)			408
				#		TCM Cinema (FR)														co0505495 (46)
				#		TCM Movies (GB)														co0988991 (1)
				#
				#	Russian state-owned channel.
				#
				#		TNT (RU)															--co0153579-- (261)		--263-- (137)		1191
				#		TNT-Premier (RU)																			--445-- (132)		2859
				#		TNT4 (RU)															--co0975071-- (8)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		TNT Digital Media Production (US)									co0375990 (1)
				#		TNT Film on Site Productions (US)									co0407107 (1)
				#		TNT Amusement (US)													co0361258 (1)
				#		TNT Video (US)														co0671664 (0)
				#
				#		TCM Vault Collection (US)											co0448330 (99)
				#
				#		TNT (PK)															--co0528492-- (1)
				#		TNT Pyro (NO)														--co1050808-- (1)
				#		TNT Global Express (IT)												--co0546317-- (1)
				#		TNT Express (DE)													--co0259015-- (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyTnt : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'TNT Productions'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'TNT'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'TNT'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'TNT Originals'},
					'expression'	: '(tnt|tcm|turner[\s\-\_\.\+]*network[\s\-\_\.\+]*(?:television|tv)|turner[\s\-\_\.\+]*originals?|turner[\s\-\_\.\+]*classics?[\s\-\_\.\+]*movies?)',
				},

				#################################################################################################################################
				# Touchstone
				#
				#	Does not exist anymore.
				#	A studio created and owned by Disney to target older/adult audiences.
				#	When closed, Touchstone Television was renamed/merged into ABC Signature.
				#
				#	Parent Companies:		Disney
				#	Sibling Companies:		Disney, ABC, ABC Signature
				#	Child Companies:		-
				#
				#	Owned Studios:			Touchstone Pictures
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Disney, ABC, DreamWorks, Paramount
				#
				#	Content Provider:		-
				#	Content Receiver:		Disney, ABC
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(535)					(334)
				#	Networks																(0)						(0)
				#	Vendors																	(250)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Touchstone Pictures (US)											co0049348 (242)			3800 (236)			9195
				#		Touchstone Television (US)											co0067205 (149)			32 (98)				1558
				#		Touchstone Films (US)												co0925713 (7)
				#		Touchstone (GB)														co0110398 (2)
				#		Touchstone (US)														co0759606 (1)
				#		Touchstone Theatre (US)												co0426272 (1)
				#		Touchstone Animation (US)											co0747847 (0)
				#		Costard & Touchstone Productions (US)								co1066685 (0)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Touchstone Home Video (US)											co0041517 (163)
				#		Touchstone Home Video (DE)											co0226864 (77)
				#		Touchstone Home Video (GB)											co0233977 (13)
				#		Touchstone Home Video (FI)											co0883363 (5)
				#		Touchstone Home Video (FR)											co0194602 (5)
				#		Touchstone Home Video (AU)											co1002359 (2)
				#		Touchstone Home Video (SI)											co0539616 (2)
				#		Touchstone Home Video (BR)											co0241748 (1)
				#
				#		Touchstone Home Entertainment (TR)									co0659855 (78)
				#		Touchstone Home Entertainment (US)									co0477440 (76)
				#		Touchstone Home Entertainment (DE)									co0300570 (30)
				#		Touchstone Home Entertainment (AU)									co0387386 (4)
				#		Touchstone Home Entertainment (NL)									co0735841 (2)
				#
				#		Touchstone Pictures Home Entertainment (MX)							co0750134 (7)
				#		Touchstone Pictures México (MX)										co0886556 (7)
				#
				#		Touchstone (DK)														co0501762 (1)
				#		Touchstone (FI)														co0501763 (0)
				#
				#		Touchstone Theater (CA)												co0662162 (1)
				#		Touchstone Games (US)												co0229151 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyTouchstone : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Touchstone Pictures'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Touchstone'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(touchstone)',
				},

				#################################################################################################################################
				# TriStar
				#
				#	Parent Companies:		Sony
				#	Sibling Companies:		Columbia Pictures, Screen Gems, Affirm Films
				#	Child Companies:		-
				#
				#	Owned Studios:			TriStar Pictures
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Columbia Pictures, Screen Gems
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(803)					(378)
				#	Networks																(0)						(0)
				#	Vendors																	(4204)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		TriStar Pictures (US)												co0005883 (354)			3595 (237)			559
				#		TriStar Television (US)												co0051191 (43)			188 (44)			8609
				#		TriStar Productions													co0440338 (9)
				#		Tri Star															co0015605 (3)
				#		Tri Star Productions (US)											co0250475 (2)
				#		TriStar Pictures Productions (US)															140649 (1)			192007
				#		Tristar Studios (US)												co0355277 (1)
				#		TriStar Television (US)												co0168261 (1)
				#		Tri Star Movies (IN)												co0773877 (1)
				#		Bizarre Tri Star Productions (US)									co0348512 (1)
				#
				#		Columbia TriStar Television (US)									co0074221 (229)			443 (72)			10471
				#		Columbia TriStar																			21614 (12)			177
				#		Columbia TriStar Filmes do Brasil															14283 (8)			77682
				#		Columbia TriStar Children's Television (US)							co0001581 (3)			21402 (1)			23549
				#		Columbia TriStar Carlton TV (GB)									co0624442 (3)
				#		Columbia TriStar TV Productions (FR)								co0147951 (3)
				#		Columbia TriStar Productions (UK) Ltd. (GB)							co0113915 (2)
				#		Columbia TriStar Films (US)											co0113868 (2)
				#		Columbia TriStar Television Pty. Ltd. (AU)							co0142305 (2)
				#		Columbia TriStar Comercio Inter. (Madeira) (PT)						co0008439 (1)
				#		Columbia TriStar Television Productions (UK) Ltd.					co0142304 (1)
				#		Columbia TriStar Entertainment (US)									co0245365 (1)
				#		Columbia TriStar Productions Pty. Ltd. (AU)							co0093452 (1)			82509 (1)			137499
				#		Deutsche Columbia TriStar Filmproduktion (DE)						co0032932 (8)
				#
				#	Other production company.
				#
				#		Tri-Star Pictures (US)												--co0806163-- (2)
				#
				#	Other companies with the same name.
				#
				#		Fusion Tristar (GB)													--co0104866-- (1)
				#		Tristar Products (US)												--co0534804-- (1)		--161770-- (1)		213747
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		TriStar Pictures (US)												co0005883 (354)
				#
				#		Tristar Film Finance (CA)											co0294950 (2)
				#		TriStar Pictures (MX)												co0976563 (1)
				#		TriStar International (US)											co0367774 (1)
				#		Tri Star Sports and Entertainment (US)								co0232258 (1)
				#		TriStar Television Distribution (US)								co0284253 (1)
				#		Tri-Star Pictures (MX)												co1055336 (1)
				#		Tristar Industries (CA)												co0189829 (1)
				#		Tri-Star Motor Group (US)											co0670235 (1)
				#		TriStar Appearances (US)											co0774102 (0)
				#		TriStar Entertainment (US)											co0217342 (0)
				#		Tristar Management (US)												co0313694 (0)
				#		Tristar (DE)														co1062404 (0)
				#		Tristar Global investment Fund (US)									co0820799 (0)
				#		Tristar Global Entertainment (US)									co0820798 (0)
				#
				#		Columbia TriStar Home Entertainment (DE)							co0127120 (537)
				#		Columbia TriStar Home Entertainment (US)							co0098048 (321)
				#		Columbia TriStar Home Entertainment (NL)							co0213457 (308)
				#		Columbia TriStar Home Entertainment (BR)							co0170439 (139)
				#		Columbia TriStar Home Entertainment (GB)							co0182605 (126)
				#		Columbia TriStar Home Entertainment (CA)							co0225408 (57)
				#		Columbia TriStar Home Entertainment (AU)							co0638112 (50)
				#		Columbia TriStar Home Entertainment (MX)							co0720168 (35)
				#		Columbia TriStar Home Entertainment (ES)							co0393411 (32)
				#		Columbia TriStar Home Entertainment (IT)							co0115429 (28)
				#		Columbia TriStar Home Entertainment (DK)							co0754056 (8)
				#		Columbia TriStar Home Entertainment (SE)							co0373110 (12)
				#		Columbia TriStar Home Entertainment (HK)							co0625795 (2)
				#		Columbia TriStar Home Entertainment (CH)							co0919176 (2)
				#		Columbia TriStar Home Entertainment (FI)							co0753593 (2)
				#		Columbia Tristar Home Entertainment (NL)							co0919014 (2)
				#		Columbia Tristar Home Entertainment (DK)							co0919019 (1)
				#		Columbia TriStar Home Entertainment (NU)							co0919175 (1)
				#		Columbia Tristar Home Entertainment (SE)							co0919013 (1)
				#		Columbia TriStar Home Entertainment (KR)							co0853923 (1)
				#		Columbia TriStar Home Entertainment (JP)							co0793712 (1)
				#		Columbia Tristar Home Entertainment (NU)							co0919015 (1)
				#		Columbia Tristar Home Entertainment (AU)							co0919016 (1)
				#		Columbia TriStar Home Entertainment / Aurum (ES)					co0833779 (1)
				#
				#		Columbia TriStar Home Video (US)									co0001850 (1518)
				#		Columbia TriStar Home Video (NL)									co0189864 (349)
				#		Columbia TriStar Home Video (AU)									co0045926 (238)
				#		Columbia TriStar Home Video (GB)									co0942170 (30)
				#		Columbia TriStar Home Video (MX)									co0751613 (30)
				#		Columbia TriStar Home Video (DE)									co0942169 (22)
				#		Columbia TriStar Home Vidéo (FR)									co0954396 (9)
				#		Columbia TriStar Home Video (CA)									co1020466 (6)
				#		Columbia TriStar Home Video (PL)									co0723390 (3)
				#		Columbia TriStar Home Video (DK)									co0826726 (3)
				#		Columbia TriStar Home Video (BE)									co0120629 (2)
				#		Columbia TriStar Home Video (IT)									co1042290 (2)
				#		Columbia Tri-Star Home Video (IT)									co0943399 (1)
				#		Columbia TriStar Home Video (HK)									co0337735 (0)
				#
				#		Columbia TriStar Films (FR)											co0077851 (318)
				#		Columbia TriStar Films (NL)											co0003949 (241)
				#		Columbia TriStar Films (GB)											co0613324 (115)
				#		Columbia TriStar Films (ES)											co0037988 (46)
				#		Columbia TriStar Films (MX)											co0152638 (45)
				#		Columbia Tristar Films (KR)											co0884352 (36)
				#		Columbia TriStar Films (NZ)											co0057970 (13)
				#		Columbia TriStar Films (KR)											co0382360 (7)
				#		Columbia TriStar Films (NO)											co0982368 (7)
				#		Columbia TriStar Films (BE)											co1002119 (5)
				#		Columbia TriStar Films (TW)											co0802980 (3)
				#		Columbia TriStar Films (DK)											co0628032 (4)
				#		Columbia TriStar Films (VE)											co0428560 (4)
				#		Columbia Tristar Films (PT)											co0960786 (2)
				#		Columbia Tristar Films (AU)											co0960788 (2)
				#		Columbia Tristar Films (FI)											co0137852 (0)
				#		Columbia Tristar Films (IS)											co0960785 (0)
				#
				#		Columbia TriStar Films de Argentina (AR)							co0003581 (523)
				#		Columbia TriStar Films de España (ES)								co0057443 (268)
				#		Columbia TriStar Films AB (SE)										co0005726 (221)
				#		Columbia TriStar Film (DE)											co0060005 (199)
				#		Columbia Tristar Films of India (IN)								co0774471 (142)
				#		Columbia TriStar Film (IT)											co0006448 (132)
				#		Columbia TriStar Film (NO)											co0728184 (67)
				#		Columbia TriStar Film (SE)											co0539852 (61)
				#		Columbia TriStar Films Pty. Ltd. (AU)								co0015669 (42)
				#		Columbia TriStar Films Italia (IT)									co0815627 (23)
				#		Columbia TriStar Film (JP)											co0382315 (21)
				#		Columbia TriStar Film (AU)											co0379792 (10)
				#		Columbia TriStar Films of Germany (DE)								co0379620 (6)
				#		Columbia TriStar Film Mexico (MX)									co0382011 (1)
				#		Columbia Tristar Film (HU)											co0960784 (0)
				#		Columbia TriStar Filmes do Brasil (BR)								co0004899 (0)
				#		Columbia TrSstar Films (HK)											co0981289 (1)
				#
				#		Columbia TriStar Film Distributors (GB)								co0047778 (119)
				#		Columbia TriStar Film Distributors (HK)								co0802979 (1)
				#
				#		Columbia TriStar Film Distributors Inter. (SG)						co0135318 (32)
				#		Columbia TriStar Film Distributors Inter. (US)						co0045347 (28)
				#		Columbia TriStar Film Distributors Inter. (ID)						co0613216 (4)
				#
				#		Columbia TriStar Domestic Television (US)							co0009297 (371)
				#		Columbia Tristar Television Distribution (US)						co0287692 (53)
				#		Columbia TriStar International Television (US)						co0163983 (21)
				#
				#		Columbia TriStar Egmont Film Distributors (FI)						co0035705 (88)
				#		Columbia TriStar Nordisk Film Distributors A/S (NO)					co0094232 (54)
				#		Columbia TriStar Nordisk Film Distributors (FI)						co0114725 (50)
				#		Columbia Tri-Star Films (BE)										co0700140 (11)
				#		Columbia Tri Star (MX)												co0890192 (2)
				#		Columbia TriStar / Kinekor (ZA)										co0210948 (1)
				#		Columbia Tristar Motion Picture Group (US)							co0209928 (0)
				#
				#		Fox Columbia TriStar Films (AU)										co0628925 (175)
				#		Columbia TriStar Fox Films (NL)										co1021830 (2)
				#
				#		Buenavista Columbia Tri Star Films de Mexico						co0039725 (30)
				#		Columbia TriStar Buena Vista Filmes. do Brasil (BR)					co0241443 (13)
				#		Buena Vista Columbia TriStar Films (MY)								co1037590 (1)
				#
				#		Gaumont/Columbia TriStar Home Video (FR)							co0108034 (229)
				#		Gaumont/Columbia TriStar Films (FR)									co0135317 (56)
				#
				#		Hoyts Fox Columbia TriStar Films (AU)								co0768357 (152)
				#		Columbia TriStar Hoyts Home Video (AU)								co0768425 (52)
				#		Hoyts Columbia Tristar Films (AU)									co0961122 (3)
				#
				#		Columbia TriStar Warner Filmes de Portugal (PT)						co0075764 (179)
				#		Universal - Columbia TriStar Home Entertainment (FI)				co0201367 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyTristar : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'TriStar Pictures'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'TriStar'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(tr[is][\s\-\_\.\+]*star)',
				},

				#################################################################################################################################
				# TruTV
				#
				#	Previously named "Court TV".
				#
				#	Parent Companies:		Warner Bros Discovery, Turner (previous), Warner (previous), NBC (previous)
				#	Sibling Companies:		TBS, TNT, HBO
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			TruTV
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		(HBO) Max
				#	Content Receiver:		(HBO) Max, Hulu, YouTube
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(2)						(0)
				#	Networks																(339)					(96)
				#	Vendors																	(0)						(0)
				#	Originals																(78 / 194)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Court TV Original Productions (US)									co0213659 (2)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		truTV (US)															co0214175 (128)			69 (91)			364
				#		TruTV (GB)															co0494156 (22)
				#
				#		Court TV (US)														co0036798 (77)			1522 (7)		4138
				#		Court Tv (CA)														co0670573 (2)
				#		Court TV Pro (US)													co0200080 (0)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyTrutv : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'TruTV Productions'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'TruTV'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'TruTV'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'TruTV Originals'},
					'expression'	: '((?:tru|court)[\s\-\_\.\+]*tv)',
				},

				#################################################################################################################################
				# Tubi
				#
				#	Parent Companies:		Fox
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			Tubi TV
				#
				#	Streaming Services:		Tubi TV
				#	Collaborating Partners:	-
				#
				#	Content Provider:		Fox
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(0)						(0)
				#	Networks																(1828)					(14)
				#	Vendors																	(0)						(0)
				#	Originals																(959? / 43)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Tubi TV (US)														co0724460 (1505)		2166 (14)		5187
				#		Tubi Movies (US)													co0866625 (135)
				#		Tubi Films (US)														co0983179 (30)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				MetaCompany.CompanyTubi : {
					'studio'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Tubi TV'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Tubi'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Tubi Originals'},
					'expression'	: '(^tubi(?:$|[\s\-\_\.\+]*(?:tv|television|movie|film)))',
				},

				#################################################################################################################################
				# Turner
				#
				#	There are a bunch of other companies named after other Turners.
				#	Eg: Margate Turner Contemporary, Chet Turner Films, etc.
				#
				#	Parent Companies:		Warner Bros, TBS (previous)
				#	Sibling Companies:		HBO, Waner Bros companies
				#	Child Companies:		TBS, TNT, TCM
				#
				#	Owned Studios:			Turner Pictures, Hanna-Barbera, Castle Rock Entertainment, New Line Cinema
				#	Owned Networks:			TBS, TNT, TCM
				#
				#	Streaming Services:		truTV
				#	Collaborating Partners:	TBS, TNT, TCM, HBO, Waner Bros companies
				#
				#	Content Provider:		-
				#	Content Receiver:		TBS, TNT, TCM
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(248)					(161)
				#	Networks																(0)						(0)
				#	Vendors																	(1447)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Turner (AR)															co0781641 (3)			69654 (1)			130573
				#		Turner (ES)															co0728074 (2)
				#
				#		Turner Pictures																				8665 (37)			1765
				#		Turner Pictures (I) (CA)																	1523 (20)			6189
				#		Turner Pictures (I) (US)											co0045447 (19)
				#		Turner Pictures (II) (US)											co0159949 (2)
				#		Turner Pictures (III) (US)											co0662531 (1)
				#
				#		Turner Original Productions (US)									co0064735 (8)			2762 (7)			25928
				#		Turner Studios Original Productions (US)							co0150930 (4)
				#
				#		Turner Studios (US)													co0046564 (14)			58702 (1)			129891
				#		Turner Production Studios (US)										co0971288 (1)
				#		Turner Productions (US)												co0900992 (1)
				#
				#		Turner Films																				66219 (2)			67564
				#		Turner Films (ES)													co0038957 (1)
				#		Turner Films Inc.													co0007241 (1)
				#		Turner Film Productions (GB)										co0142333 (1)
				#
				#		Turner Network Televisions (US)																2027 (95)			678
				#		Turner Television (US)												co0040732 (5)			31337 (2)			77725
				#
				#		Turner Internacional Argentina (AR)									co0458361 (4)
				#		Turner International Asia Pacific Limited (HK)						co0453802 (1)			54310 (1)			90599
				#
				#		Turner Sports (US)													co0099229 (14)
				#		Turner Feature Animation (US)										co0079227 (3)			69727 (1)			90511
				#		Turner Learning (US)												co0446580 (1)
				#		Turner Enterprises (US)												co0198473 (1)
				#		Turner Cinematography (US)											co0471992 (1)
				#
				#		Ted Turner Pictures (US)											co0981578 (1)
				#		Ted Turner Enterprises (US)											co0748955 (1)
				#		Ted Turner Documentaries (US)										co0098174 (1)
				#
				#	Majority is distribution, not production.
				#
				#		Turner Entertainment (US)																	5643 (68)			8922
				#		Turner Entertainment Networks (US)									--co0213389-- (4)
				#		Turner Entertainment Group (US)										--co0000078-- (10)
				#		Turner Entertainment (US)											--co0183824-- (670)
				#
				#	Other production companies.
				#
				#		Turner Production Effects (US)										--co0043156-- (1)
				#
				#	Companies with the same name.
				#
				#		Turner Media Productions (US)										--co0319451-- (4)		--139561-- (1)		190335
				#		Turner/Love (US)													--co0257065-- (0)
				#		Favor Nobody Pat and Turner Productions (US)						--co1055796-- (1)
				#		Turner & Jones (GB)													--co0779711-- (1)
				#		Turner Gang Productions (GB)										--co0640954-- (1)
				#		The Al Turner Company (US)											--co0812095-- (1)
				#		Helfgott-Turner Productions (US)									--co0066595-- (2)
				#		TurnerWorks Productions (US)										--co0748151-- (1)
				#		TurnerGang Productions (GB)											--co0773908-- (1)
				#		Blake / Turner Films (GB)											--co0293060-- (1)
				#		Turner & Tailor (DE)												--co0212128-- (1)
				#		Turner and Associates (US)											--co0322664-- (1)
				#		Turner Fox Productions (US)											--co0922561-- (1)
				#		Turner/Smith Productions (US)										--co0780218-- (1)
				#		Turner-Hader Entertainment											--co0019854-- (1)
				#		Turner-Cray Inc.													--co0106480-- (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Turner (IN)															co0337017 (7)
				#		Turner (GB)															co0228203 (2)
				#		Turner (US)															co0840781 (1)
				#		Turner (JP)															co0397542 (1)
				#
				#		Turner Entertainment (US)											co0183824 (670)
				#		Turner Entertainment Group (US)										co0000078 (10)
				#		Turner Entertainment Co. (US)										co1005738 (1)
				#		Turner Entertainment Animation (US)									co0917898 (0)
				#		Turner Entertainment Networks (US)									co0213389 (4)
				#
				#		Turner Home Entertainment (US)										co0093282 (280)
				#		Turner Home Entertainment (MX)										co0974338 (1)
				#		Turner Home Entertainment International (DE)						co0507520 (1)
				#
				#		Turner Films (US)													co0147789 (1)
				#		Turner Films (GB)													co0199827 (0)
				#
				#		Turner Group (US)													co0381252 (2)
				#		Turner Group (AU)													co0379858 (1)
				#		The Turner Group (US)												co0386061 (0)
				#
				#		Turner Program Services (TPS) (US)									co0084770 (93)
				#		Turner International India (IN)										co0386603 (52)
				#		Turner Pictures Worldwide											co0009902 (14)
				#		Turner South (US)													co0147819 (8)
				#		Turner Publishing (US)												co0206108 (1)
				#		Turner Content Solutions (GB)										co0342533 (1)
				#		Turner Creations (US)												co0808042 (0)
				#		The Turner Collection (US)											co0969989 (0)
				#		Turner Properties (US)												co0639907 (0)
				#		Turner Interactive (US)												co0580410 (0)
				#
				#		Turner Music (US)													co0850163 (0)
				#		Turner Music Library (US)											co0606930 (0)
				#		Turner Movie Music / Rhino Records (US)								co0310903 (0)
				#
				#		Concorde-Castle Rock/Turner (DE)									co0134695 (54)
				#		Filmayer-Castle Rock-Turner S.A. (ES)								co0134697 (11)
				#		Turner/MGM/UA (US)													co0219076 (0)
				#
				#		Turner Access (GB)													--co0588799-- (1)
				#		The Turner Family (US)												--co0625023-- (1)
				#		Turner's House Trust (GB)											--co0872716-- (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyTurner : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Turner Pictures'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Turner'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(turner)',
				},

				#################################################################################################################################
				# Universal
				#
				#	Member of the "modern" Big Five.
				#	Universal does not really own NBC. Rather Comcast owns NBCUniversal, consiting of NBC and Universal.
				#
				#		https://universalstudios.fandom.com/wiki/Universal_Pictures
				#		https://fanon-kingdom.fandom.com/wiki/List_of_assets_owned_by_NBCUniversal
				#		https://en.wikipedia.org/wiki/Universal_Pictures#Units
				#
				#	Parent Companies:		Universal, Comcast (through NBCUniversal)
				#	Sibling Companies:		Sky
				#	Child Companies:		-
				#
				#	Owned Studios:			Universal Studios, Focus Features, Illumination, DreamWorks, Working Title, Carnival Films,
				#							Amblin (partial), United International Pictures (partial, Paramount+Universal)
				#	Owned Networks:			NBC, CNBC, MSNBC, many other local US stations,
				#							E!, SyFy, USA Network, Oxygen, Telemundo, 13th Street
				#							Toonation, Bravo (partial, Universal+Warner), Telecine (partial, Paramount+Universal+MGM+Disney)
				#
				#	Streaming Services:		Peacock, Hayu, Hulu (previous)
				#	Collaborating Partners:	NBC, Sky
				#
				#	Content Provider:		-
				#	Content Receiver:		Peacock, Hayu, Sky, Hulu (previous at least)
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(10098)					(4206)
				#	Networks																(1678)					(27)
				#	Vendors																	(21208)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Universal Pictures													co0005073 (4718)		937 (2625)			33
				#		Universal Pictures France																	23680 (40)			1546
				#		Universal Pictures Productions GmbH									co0048374 (2)
				#		Universal International Pictures									co0021358 (376)			3565 (354)			10330
				#		Universal Pictures Home Entertainment														28448 (51)			64471
				#		Universal Pictures Australia																79732 (1)			135539
				#
				#		Universal Media Studios (UMS)										co0196576 (48)			839 (30)			8301
				#		Universal Studio Group												co0882993 (9)
				#		Universal Studios Home Ent. Family Productions						co0163456 (4)
				#		Universal Studios Recreation Group									co0064407 (3)			98984 (2)			113542
				#		Universal Studios Animation											co0035434 (0)
				#		Universal Studios Hollywood											co0017927 (0)
				#
				#		Universal Television												co0046592 (588)			64 (761)			26727
				#		Universal Television Alternative Studio								co0598523 (33)			1361 (20)			95243
				#		Universal Pictures Television										co0186420 (28)
				#		Universal TV (US)													co0770762 (20)
				#		Universal Network Television										co0080319 (20)
				#		Universal Pay Television											co0075806 (1)			29867 (2)			82569
				#		Universal Television Entertainment									co0451692 (0)			67776 (25)			104278
				#
				#		Universal Cable Productions											co0242101 (89)			189 (84)			7938
				#		Universal Content Productions (UCP)									co0769928 (56)
				#		Universal Animation Studios											co0202966 (54)			293 (19)			5556
				#		Universal Studios Home Video																34467 (34)			10713
				#		Universal International Studios										co0186606 (23)
				#		Universal Productions France S.A.									co0040731 (15)			11852 (7)			1408
				#		Universal Networks International									co0302927 (6)
				#		Universal Spectrums Entertainment									co0751260 (6)
				#		Universal Family Entertainment										co0438125 (5)			134886 (1)			185212
				#		Universal Stage Productions											co0514005 (4)			69970 (2)			42327
				#		Universal Remote													co0818184 (3)			145816 (2)			197228
				#		Universal Vision Productions										co0175276 (2)
				#		Universal Pictures International Production							co0486437 (2)			13486 (1)			47036
				#		Universal Media & Entertainment Group Limited						co0263504 (2)			31546 (1)			125249
				#		Universal Parks & Resorts																	114586 (1)			165715
				#		Universal Creative													co0018727 (0)			98983 (2)			151071
				#
				#		Global Universal Pictures											co0118092 (4)			35010 (3)			7556
				#		Global Universal Pictures (CA)										co0272828 (3)
				#
				#		Universal Culture													co0313476 (3)			40271 (2)			90209
				#		Universal Culture (CN)												co0338344 (1)
				#
				#		NBC Universal Television											co0129175 (187)			155816 (6)			207345
				#		NBCUniversal														co0195910 (100)			1071 (40)			26559
				#		NBC Universal Studios 												co0242700 (13)
				#		NBCUniversal International Studios									co0216142 (11)			1896 (11)			95155
				#		NBC Universal International Studios															2443 (16)			87455
				#		NBCUniversal Content Studios										co0733397 (5)
				#		NBC Universal Digital Studio										co0284326 (3)			75288 (2)			78166
				#		NBC Universal International Television Pro.							co0485242 (2)
				#		NBC Universal Brand Development (NBCUBD)							co0608727 (2)
				#		NBC Universal Global Networks										co0242277 (2)			70892 (4)			2975
				#		NBCUniversal Skycastle (US)											co0574746 (1)
				#		NBCUniversal International Studios (US)								co1048379 (0)
				#
				#		Universal Music Group																		21822 (216)			9339
				#		Universal Music France																		7331 (49)			104897
				#
				#		Universal 1440 Entertainment										co0359888 (39)			4492 (59)			17009
				#		Rio Vista Universal													co0443986 (14)			31159 (4)			128700
				#		MCA/Universal Television											co0066651 (11)
				#		Universal Tri Connection Studios									co0453011 (7)
				#		Universal/Public Arts Production									co0029904 (2)			30650 (7)			55901
				#		Universal CGI (US)													co0086865 (1)
				#
				#	Companies with the same name.
				#
				#		Universal Media (IN)												--co0186347-- (8)		--18538-- (6)		102132
				#		Universal Cinemas (IN)												--co0479456-- (3)		--83394-- (2)		118181
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Universal Channel (HU)												co0227561 (29)
				#		Universal Channel (DE)												co0440561 (28)
				#		Universal Channel (JP)												co0305757 (24)
				#		Universal Channel (GB)												co0365525 (21)
				#		Universal Channel (TR)												co0603572 (19)
				#		Universal Channel (BR)												co0356636 (9)			1458 (4)			4014
				#		Universal Channel (AU)												co0395977 (4)			859 (1)				2238
				#		Universal Channel (CL)												co0464716 (3)
				#		Universal Channel (AR)												co0420019 (3)
				#		Universal Channel (RO)												co0465167 (2)
				#		Universal Channel (MX)												co0420018 (2)
				#		Universal Channel (PL)												co0470442 (1)
				#		Universal Channel (GR)												co0406980 (1)
				#		Universal Channel (ID)												co0406983 (1)
				#		Universal Channel (TH)												co0464717 (1)
				#		Universal Channel (CZ)												co0323517 (0)
				#
				#		Universal Television												co0046592 (588)			1192 (1)			3683
				#		Universal TV (US)													co0770762 (20)
				#		Universal TV (GB)																			1449 (1)			3412
				#
				#		Universal Toons (US)												co1013700 (189)
				#		Universal Toons (MY)												co1006786 (1)
				#
				#		Universal Kids														co0667778 (73)			145 (19)			2133
				#		Universal HD														co0326139 (3)
				#		Universal All Access												co0878217 (1)
				#		Universal Premiere																			3613 (1)			7392
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Universal (FR)														co0234421 (18)
				#		Universal (IT)														co0651230 (12)
				#		Universal (ES)														co0291326 (3)
				#		Universal (PT)														co0497968 (2)
				#		Universal (KR)														co0454779 (1)
				#		Universal (SE)														co0454780 (1)
				#		Universal (DE)														co0784876 (0)
				#		Universal (ZA)														co0658490 (0)
				#		Universal (AR)														co0784875 (0)
				#		Universal Italia													co0361097 (1)
				#
				#		Universal Studios 													co0000534 (197)
				#		Universal Studios (GB)												co0487454 (6)
				#		Universal Studios Canada											co0458146 (3)
				#		Universal Studios Japan												co0232391 (1)
				#
				#		Universal Pictures													co0005073 (4718)
				#		Universal Pictures (GB)												co0105063 (513)
				#		Universal Pictures (JP)												co0137262 (81)
				#		Universal Pictures (FR)												co0055043 (64)
				#		Universal Pictures (AU)												co0813571 (61)
				#		Universal Pictures (IT)												co0063715 (60)
				#		Universal Pictures (MX)												co0840675 (60)
				#		Universal Pictures (BR)												co0151315 (45)
				#		Universal Pictures (ES)												co0809355 (33)
				#		Universal Pictures (CA)												co0844550 (19)
				#		Universal Pictures (NL)												co0899185 (7)
				#		Universal Pictures (KR)												co0226568 (4)
				#		Universal Pictures (HK)												co0983635 (2)
				#		Universal Pictures (AT)												co0843089 (1)
				#		Universal Pictures (AL)												co0800639 (0)
				#
				#		Universal Pictures Finland											co0388514 (526)
				#		Universal Pictures do Brazil										co0067464 (324)
				#		Universal Pictures Argentina										co0816494 (173)
				#		Universal Pictures Spain											co0055622 (107)
				#		Universal Pictures Canada											co0056049 (54)
				#		Universal Pictures Japan											co0353649 (38)
				#		Universal Pictures Russia											co0184745 (24)
				#		Universal Pictures UK												co0202418 (13)
				#		Universal Pictures Germany											co0196530 (11)
				#		Universal Pictures Nordic											co0823296 (8)
				#		Universal Pictures UK & Eire										co0410007 (8)
				#		Universal Pictures Benelux											co0548735 (6)
				#		Universal Pictures Singapore										co0215092 (2)
				#		Universal Pictures Switzerland										co0330119 (0)
				#		Universal Pictures India											co0215185 (0)
				#		Universal Pictures Finland Oy										co0125160 (0)
				#
				#		Universal Pictures International									co0183709 (577)
				#		Universal Pictures International (DE)								co0198457 (395)
				#		Universal Pictures International (GB)								co0219608 (338)
				#		Universal Pictures International (NL)								co0820078 (291)
				#		Universal Pictures International (IT)								co0236977 (155)
				#		Universal Pictures International (ES)								co0854301 (131)
				#		Universal Pictures International (AT)								co0811906 (87)
				#		Universal Pictures International (MX)								co0812374 (83)
				#		Universal Pictures International (CH)								co0811907 (74)
				#		Universal Pictures International (RU)								co0820080 (52)
				#		Universal Pictures International (PT)								co0820079 (12)
				#		Universal Pictures International (NO)								co0838692 (7)
				#		Universal Pictures International Entertainment						co0379771 (11)
				#
				#		Universal Pictures Corporation (US)									co0679150 (1)
				#		Universal Pictures Corporation (PL)									co0215193 (1)
				#		Universal Pictures Corporation (PT)									co0244009 (0)
				#
				#		Universal Pictures Corporation of Far East							co0215138 (406)
				#		Universal Pictures Corporation of Mexico							co0215174 (348)
				#		Universal Pictures Corporation of Peru								co0215157 (155)
				#		Universal Pictures Corporation of Chile								co0215102 (153)
				#		Universal Pictures Corporation of Puerto Rico						co0768338 (174)
				#		Universal Pictures Corporation of Porta Rico						co0215218 (1)
				#		Universal Pictures Corporation of Egypt								co0215215 (1)
				#		Universal Pictures Corporation of China								co0215243 (0)
				#		Universal Pictures Corporation of Panama							co0804920 (0)
				#		Universal Pictures Corp.											co0636388 (0)
				#		Universal Pictures Corporation sp. z. Org. (PT)						co0405240 (0)
				#
				#		Universal Pictures Company (GB)										co0412392 (1)
				#		Universal Pictures Company Inc.										co0063145 (0)
				#
				#		Universal Film (SE)													co0251089 (779)
				#		Universal Film (NO)													co0666801 (325)
				#		Universal Film (IT)													co0223327 (5)
				#		Universal Film (FR)													co0215160 (3)
				#		Universal Film														co0034656 (2)
				#		Universal Film (SE)													co0797158 (2)
				#		Universal Film (DE)													co0220548 (0)
				#		Universal Film (CZ)													co0042035 (0)
				#
				#		Universal Films (PA)												co0215234 (181)
				#		Universal Films (GB)												co0309423 (1)
				#		Universal Films (UY)												co0721998 (0)
				#		Universal Films (GT)												co0721999 (0)
				#		Universal Films (NI)												co0715061 (0)
				#		Universal Films (AL)												co0215282 (0)
				#		Universal Films (BE)												co0140051 (0)
				#		Universal Films (CR)												co0694362 (0)
				#		Universal Films (HU)												co0215283 (0)
				#		Universal Films (EX)												co0715059 (0)
				#		Universal Films (DK)												co0215271 (0)
				#		Universal Films (PY)												co0721997 (0)
				#		Universal Films (HN)												co0722000 (0)
				#		Universal Films (BO)												co0726722 (0)
				#
				#		Universal Films Argentina											co0215230 (324)
				#		Universal Films of India											co0794561 (179)
				#		Universal Film A/S (DK)												co0233831 (123)
				#		Universal Films Española											co0030491 (111)
				#		Universal Films of Norway Akfieselskap (NO)							co0770680 (101)
				#		Universal Film S.A. (BE)											co0872541 (30)
				#		Universal Films of Norway											co0215112 (7)
				#		Universal Filmes (BR)												co0018085 (3)
				#		Universal Films S.A. (BE)											co0140049 (2)
				#		Universal Film S.A. (FR)											co0030062 (1)
				#		Universal Film (UFA) (NO)											co0691059 (1)
				#		Universal Films & Video (HK)										co1060162 (1)
				#		Universal Films (FR)												co0162928 (0)
				#		Universal Film Sp. S.R.O. (CZ)										co0773033 (0)
				#		Universal Films Canada												co0243802 (0)
				#
				#		Universal Film Manufacturing Company								co0048238 (650)
				#		Universal Film Manufacturing Company (AU)							co1003954 (285)
				#		Universal Film Agency (NL)											co0305143 (75)
				#		Universal Films (CSHH)												co0213976 (4)
				#		Universal Film Agency (DK)											co0305123 (0)
				#		Universal Filmed Entertainment Group								co0896256 (0)
				#		Universal Film & TV Division (GB)									co0125927 (0)
				#		Universal Film Corporation (US)										co0006624 (0)
				#
				#		Universal Filmverleih (DE)											co0241799 (167)
				#		Universal Filmverleih (AT)											co0240556 (8)
				#
				#		Universal International (JP)										co0235121 (4)
				#		Universal International (DE)										co0340231 (1)
				#		Universal International (IT)										co0555207 (1)
				#		Universal Internacional (ES)										co0867345 (1)
				#
				#		Universal International Pictures (US)								co0021358 (376)
				#		Universal International Pictures (NL)								co0304386 (44)
				#		Universal International Pictures (AU)								co0524308 (9)
				#		Universal International Pictures (ES)								co0408923 (7)
				#		Universal International Pictures (AR)								co0647543 (1)
				#		Universal International Pictures (BE)								co0648656 (1)
				#		Universal International Pictures (JP)								co0648655 (1)
				#		Universal International Pictures (DK)								co0679102 (0)
				#		Universal International Pictures (IT)								co0632635 (0)
				#		Universal International Pictures (FR)								co0648654 (0)
				#
				#		Universal Pictures Home Entertainment (US)							co0023827 (1771)
				#		Universal Pictures Home Entertainment (DE)							co0297627 (642)
				#		Universal Pictures Home Entertainment (NL)							co0814477 (257)
				#		Universal Pictures Home Entertainment (GB)							co0743251 (95)
				#		Universal Pictures Home Entertainment (AR)							co0656151 (83)
				#		Universal Pictures Home Entertainment (MX)							co0752505 (79)
				#		Universal Pictures Home Entertainment (BR)							co0320855 (57)
				#		Universal Pictures Home Entertainment (CA)							co0762550 (22)
				#		Universal Pictures Home Entertainment (IT)							co0420666 (12)
				#		Universal Pictures Home Entertainment (ES)							co0388893 (12)
				#		Universal Pictures Home Entertainment (AU)							co0813065 (12)
				#		Universal Pictures Home Entertainment (CH)							co0542755 (3)
				#
				#		Universal Pictures Home Video (AU)									co0180647 (47)
				#		Universal Pictures Home Video (MX)									co0752504 (37)
				#		Universal Pictures Home Video (US)									co0688663 (13)
				#
				#		Universal Studios Home Entertainment (CA)							co0429910 (76)
				#		Universal Studios Home Entertainment (GB)							co0443270 (12)
				#		Universal Studios Home Entertainment (HK)							co0592768 (5)
				#		Universal Studios Home Entertainment (FR)							co0573772 (3)
				#
				#		Universal Studios Home Video (US)									co0021294 (356)
				#		Universal Studios Home Video (CA)									co0295614 (163)
				#		Universal Studios Home Video (BR)									co0842674 (45)
				#		Universal Studios Home Video (NL)									co0385643 (1)
				#
				#		Universal Home Entertainment (GB)									co0110681 (296)
				#		Universal Home Entertainment (FR)									co0108183 (24)
				#		Universal Home Entertainment (IT)									co0121774 (21)
				#		Universal Home Entertainment (ES)									co0117469 (8)
				#		Universal Home Entertainment (DE)									co0835320 (5)
				#
				#		Universal Home Video (US)											co0035519 (260)
				#		Universal Home Video (DE)											co0981888 (1)
				#		Universal Home Video (CH)											co0919416 (1)
				#
				#		Universal Video (IT)												co0047319 (13)
				#		Universal Video (FR)												co0030676 (5)
				#		Universal Video Spiel (DE)											co0353338 (0)
				#
				#		Universal Pictures Video (NL)										co0219620 (363)
				#		Universal Pictures Video (FR)										co0117467 (239)
				#		Universal Pictures Video (DE)										co0824421 (180)
				#		Universal Pictures Video (SE)										co0824424 (118)
				#		Universal Pictures Video (NO)										co0824425 (40)
				#		Universal Pictures Video (AU)										co0251706 (29)
				#		Universal Pictures Video (GB)										co0199066 (26)
				#		Universal Pictures Video (DK)										co0824435 (17)
				#		Universal Pictures Video (ES)										co0205372 (12)
				#		Universal Pictures Video (BE)										co0523203 (6)
				#		Universal Pictures Video (MX)										co0824436 (5)
				#		Universal Pictures Video (IT)										co0682067 (5)
				#		Universal Pictures Video (PL)										co0824439 (3)
				#		Universal Pictures Video (CH)										co0824611 (3)
				#		Universal Pictures Video (AR)										co0824438 (1)
				#
				#		Universal Sony Pictures Home Ent. (AU)								co0375381 (358)
				#		Universal Sony Pictures Home Ent. Nordic (FI)						co0533783 (248)
				#		Universal Sony Pictures Home Ent. Nordic (SE)						co0600878 (82)
				#		Universal Sony Pictures Home Ent. Nordic (NO)						co0565929 (70)
				#		Universal Sony Pictures Home Ent. Nordic (DK)						co0565928 (42)
				#
				#		Studio Universal (IT)												co0093119 (3)
				#		Studio Universal (AR)												co0570325 (3)
				#		Studio Universal Africa												co0572760 (1)
				#		Studio Universal Latin America										co0570326 (1)
				#		Studio Universal (BR)												co0967328 (0)
				#
				#		Universal Domestic Television (US)									co0028565 (47)
				#		Universal Music Group International (GB)							co0292422 (9)
				#		Universal Television Enterprises									co0380632 (6)
				#		Universal Worldwide Television (US)									co0076154 (4)
				#
				#		Universal Classics													co0053942 (4)
				#		Universal Classics Group											co0318230 (0)
				#
				#		Universal Pictures Proprietary (AU)									co0219586 (653)
				#		Deutsche Universal-Film												co0141128 (79)
				#		Universal Pictures Content Group									co0710991 (41)
				#		Universal Entertainment (GB)										co0046866 (12)
				#		Universal-Studio Canal (FR)											co0233644 (11)
				#		Universal Sports													co0246106 (11)
				#		Universal Connect (JP)												co0643665 (4)
				#		Universal J (JP)													co0751668 (4)
				#		Universal Music Group (DE)											co0497044 (3)
				#		Universal Entertainment Corp.										co0023945 (2)
				#		Universal Studios Networks of Germany								co0021866 (2)
				#		Universal Cinema (IT)												co0049911 (2)
				#		Universal/CIC (DE)													co0193613 (1)
				#		Universal Media Group												co0725110 (1)
				#
				#		NBC Universal Television Distribution								co0131785 (434)
				#		NBC Universal Television											co0129175 (187)
				#		NBCUniversal Entertainment (JP)										co0474968 (132)
				#		NBCUniversal														co0195910 (100)
				#		NBC Universal Entertainment (JP)									co0459508 (53)
				#		NBCUniversal Global Distribution (US)								co0800079 (32)
				#		NBC Universal Network TV (US)										co0196211 (15)
				#		NBCUniversal Media (US)												co0345290 (14)
				#		NBC Universal Domestic Television Distribution						co0198120 (12)
				#		NBC Universal Digital Distribution									co0196214 (6)
				#		NBC Universal Global Networks (IT)									co0261403 (5)
				#		NBCUniversal Syndication Studios (US)								co0839122 (5)
				#		NBCUniversal International Television Distribution (US)				co0722053 (5)
				#		NBC Universal Cable Entertainment									co0197667 (5)
				#		NBCUniversal International Networks (GB)							co0704497 (4)
				#		Sparrowhawk NBC Universal (GB)										co0256170 (4)
				#		NBC Universal Global Distribution									co0775963 (3)
				#		NBCUniversal Canada (CA)											co0468247 (3)
				#		NBC Universal Sports Boston (US)									co0315124 (3)
				#		NBC Universal Studios (MX)											co0728905 (2)
				#		NBC Universal Media													co0852261 (2)
				#		NBCUniversal International Networks (BR)							co0758126 (2)
				#		NBC Universal Sound (US)											co0514291 (2)
				#		Getty NBC Universal Collection (US)									co0879192 (2)
				#		Betty NBC Universal Collection (US)									co0879183 (1)
				#		NBCUniversal International Networks (DE)							co0616374 (1)
				#		NBC Universal Cable Studio											co0233867 (1)
				#		NBC Universal Global Networks										co0213416 (1)
				#		NBC Universal Entertainment Cable Group								co0416933 (1)
				#		NBCUniversal News Group												co0517613 (1)
				#		NBCUniversal Music (US)												co1021678 (1)
				#		NBC Universal Global Networks (GB)									co0260407 (0)
				#
				#		MCA/Universal Pictures												co0026044 (800)
				#		MCA/Universal Home Video											co0060214 (725)
				#		MCA/Universal Television											co0066651 (11)
				#
				#		Indepent Films/Universal Pictures Benelux							co0074924 (4)
				#		Peacock / Universal Television										co0859748 (1)
				#		Universal-Walt Disney Home Video (IT)								co0189485 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyUniversal : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Universal Pictures'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Universal TV'}, # Not much content, since most is on Peacock.
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Universal'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None}, # These are rather NBC Originals, or originals for other platforms.
					'expression'	: '((?:(?:nbc)[\s\-\_\.\+]*)?(?:universal)[\s\-\_\.\+]*(?:media|cable|content|picture|film|studio|television|tv|channel|animation|home|video|entertainment|network|production|global|interna[tc]ional|worldwide|domestic|music|classic|toon|kid|family|sport|premier|cinema|connect|all|hd|digital|news|pay|cgi|j|remote|spectrum|park|vision|stage|creative|culture|brand|1440|italia|sony|walt|.?(?:cic|public|tri)|$)|(?:studio|vista)[\s\-\_\.\+]*universal)',
				},

				#################################################################################################################################
				# USA Network
				#
				#	Parent Companies:		NBCUniversal, UA-Columbia (previous), Time Inc. (previous, Paramount/Viacom (previous)
				#	Sibling Companies:		NBC
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			USA Network
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	NBC
				#
				#	Content Provider:		-
				#	Content Receiver:		NBC, Hulu
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(905)					(140)
				#	Networks																(1224)					(151)
				#	Vendors																	(138)					(0)
				#	Originals																(247 / 283)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		USA Network (US)													co0014957 (449)			312 (87)			16642
				#		Studios USA															co0082039 (12)			57011 (18)			56401
				#		USA Pictures (US)													co0044731 (4)			18350 (14)			65087
				#		USA Networks Studios												co0055632 (1)
				#		USA Cable Entertainment (US)										co0107062 (4)			8505 (8)			11282
				#		USA Networks Studios												co0055632 (1)			67775 (4)			104277
				#		USA Films															co0043969 (51)			6648 (14)			987
				#		USA Network Pictures (US)											o0016587 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		USA																	co0019361 (31)
				#
				#		USA Network (US)													co0014957 (449)			51 (151)			30
				#		USA Networks Studios												co0055632 (1)
				#
				#		USA Broadcasting (US)												co0058588 (4)
				#		USA Broadcasting Stations Group (US)								co0094214 (4)
				#
				#		Studios USA Television (US)											co0069685 (215)
				#		Studios USA (US)													co0082039 (12)
				#		Studio USA (US)														co0046901 (0)
				#		Studios USA															co0027352 (0)
				#
				#		USA Films (US)														co0043969 (51)
				#		PPI/USA Films (US)													co0724032 (1)
				#
				#		USA Cable Network (US)												co0006634 (17)
				#		USA Cable Entertainment (US)										co0107062 (4)
				#
				#		USA Television Network (US)											co0077920 (9)
				#		USA Entertainment (US)												co0005674 (3)
				#
				#	Not sure if these are the same company, disable for now.
				#
				#		USA Production (US)													--co0320340-- (0)
				#		USA Group															--co0114841-- (0)
				#
				#	Other companies with the same name.
				#
				#		USA Productions (IN)												--co0958736-- (2)
				#		USA Talk Network (US)												--co0238628-- (1)
				#		USA Films (PH)														--co0402540-- (1)
				#		USA Projects (US)													--co0391425-- (1)
				#		USA Comedy (US)														--co0821879-- (1)
				#		USA Productions (US)												--co0319091-- (1)
				#		USA Distribution (US)												--co0712907-- (3)
				#		USA The Movie (US)													--co0198814-- (1)
				#		USA IVE (US)														--co0244395-- (1)
				#		USA Direct (US)														--co0196185-- (2)
				#		USAN Group (US)														--co0413866-- (0)
				#		Online USA (US)														--co0286597-- (2)
				#		USA Global Films (US)												--co0055598-- (1)
				#		USA Hollywood Pictures International (US)							--co0663199-- (0)
				#		Televisa USA (US)													--co0468558-- (7)
				#		USA Video (MX)														--co0749979-- (6)
				#		USA Home Video (US)													--co0030963-- (29)
				#		USATV (US)															--co0302804-- (6)
				#		USA for Africa (US)													--co0185918-- (2)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		USA Video (DE)														co0429394 (59)
				#		USA Home Video (II) (US)											co0198469 (27)
				#		USA Home Entertainment (US)											co0419861 (7)
				#
				#################################################################################################################################
				MetaCompany.CompanyUsa : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'USA Studios'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'USA'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'USA'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1,		'label' : 'USA Originals'},
					'expression'	: '((?:^|(?:studios?|\/)[\s\-\_\.\+]*)?usa[\s\-\_\.\+]*(?:$|network|picture|film|cable|broadcast|television|entertainment|video|home))',
				},

				#################################################################################################################################
				# Warner Bros
				#
				#	Member of the "original" and "modern" Big Five.
				#	Established in 1923 as Warner Bros, merged with Time Inc in 1990 into Time Warner.
				#	Sold to AT&T in 2018, then sold, and merged with Discovery in 2021 into Warner Bros Discovery.
				#	Since 2022, owns all Truner, TBS, TNT, etc companies.
				#		https://warnerbros.fandom.com/wiki/Category:Subsidiaries
				#		https://warnerbros.fandom.com/wiki/List_of_assets_owned_by_Warner_Bros._Discovery
				#		https://en.wikipedia.org/wiki/Warner_Bros.#Company_units
				#
				#	Parent Companies:		Warner Bros Discovery (Warner+Discovery), AT&T (preevious)
				#	Sibling Companies:		Discovery
				#	Child Companies:		HBO, CNN, Max, The CW
				#
				#	Owned Studios:			Warner Bros, DC Studios, Turner, New Line, Castle Rock, Spyglass, Renegade, Hanna-Barbera, Williams Street,
				#							All3Media (partial), Bad Wolf (previous, partial), MGM (previous, partial), TriStar (previous, partial)
				#	Owned Networks:			HBO, Discovery, CNN, The WB (defunct) The CW (partial, CBS+Warner), Bravo (partial, Universal+Warner),
				#							Adult Swim, Cartoon Network, Boomerang, TLC
				#							Turner, TBS, TNT, truTV, HGTV, Animal Planet, Oprah Winfrey, Magnolia, Network Ten,
				#							BET (previous, partial), Comedy Central (previous, partial), Crunchyroll (previous), E! (previous)
				#
				#	Streaming Services:		(HBO) Max, Discovery+, Philo (partial, Hearst+Disney+AMC+Paramount+Warner), Hulu (previous)
				#	Collaborating Partners:	Discovery, Universal
				#
				#	Content Provider:		-
				#	Content Receiver:		(HBO) Max, Discovery+, Philo, The CW, Hulu (previous at least)
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(11706)					(4890)
				#	Networks																(587)					(153)
				#	Vendors																	(18357)					(0)
				#	Originals																(59 / 114)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		Warner Bros. Pictures												co0002663 (5386)		113 (3251)			174
				#		Warner Bros. Television												co0005035 (1036)		51 (618)			1957
				#
				#		Warner Bros. Animation												co0072876 (219)			76 (407)			2785
				#		Warner Bros. Television Animation									co0050690 (20)
				#		Warner Bros. Pictures Animation										co0468593 (27)
				#		Warner Animation Group 																		7241 (37)			25120
				#		Warner Bros. Feature Animation (US)									co0012442 (4)
				#		Warner Classic Animation											co0070192 (1)			48347 (2)			45030
				#
				#		Warner Bros. International Television Production (DE)				co0546827 (26)			998 (19)			109759
				#		Warner Bros. International Television Production (FI)				co0623967 (20)			75435 (6)			117428
				#		Warner Bros. International Television Production (SE)				co0579299 (16)			28691 (10)			94521
				#		Warner Bros. International Television Production (AU)				co0646652 (16)			555 (8)				109758
				#		Warner Bros. International Television Production (NL)				co0565728 (7)			2297 (12)			64649
				#		Warner Bros. International Television Production (BE)				co0733785 (3)			131941 (12)			182511
				#		Warner Bros. International Television Production (DK)				co0604772 (3)
				#		Warner Bros. International Television Production (ES)				co0806515 (1)
				#		Warner Bros. International Television Production (PT)				co0591733 (1)
				#		Warner Bros. International Television (NZ)							co0542039 (13)
				#
				#		Warner Bros. ITVP Deutschland (DE)									co0612253 (8)
				#		Warner Bros. ITVP España (ES)										co0662241 (6)			137523 (3)			187131
				#		Warner Bros. ITVP (ES)												co0661753 (5)
				#		Warner Bros. ITVP (BE)												co0837070 (3)
				#		Warner Bros ITPV France (FR)										co0747991 (1)
				#		Warner Bros. ITPV (ES)												co0823881 (1)
				#		Warner Bros ITVP (DK)												co0913697 (1)
				#		Warner Bros. ITVP (DE)												co0612161 (1)
				#
				#		Warner Bros. Television Productions UK (GB)							co0689167 (13)			147701 (5)			197829
				#		Warner Bros. Television Group (US)									co0253255 (7)
				#		Warner Bros. Television Studios Inter. (GB)							co0823040 (1)
				#
				#		Warner Bros. Discovery (US)											co0863266 (146)
				#		TVN Warner Bros. Discovery (PL)										co1044762 (1)
				#		Warner Bros. Discovery U.K (GB)										co1008104 (1)
				#		Warner Bros. Discovery (DE)											co1063267 (1)
				#
				#		WarnerMedia															co0725649 (40)
				#		WarnerMedia Latin America (US)										co0879145 (7)			113193 (5)			164311
				#		WarnerMedia Kids & Family (US)										co0907088 (3)
				#		WarnerMedia Germany (US)											co0893584 (2)
				#
				#		Warner Sisters Productions (US)										co0121034 (1)			14866 (13)			57844
				#		Warner Sisters Productions (GB)										co0216236 (3)
				#		Warner Cousins (US)													co0636018 (2)
				#
				#		Warner Specialty Productions (US)									co0216628 (1)
				#		Warner Specialty Video Productions (US)								co0675376 (1)
				#
				#		Warner Bros. Japan																			3062 (102)			3627
				#		Warner Bros. Deutschland											co0314266 (50)			15782 (34)			96105
				#		Warner Bros. (DE)													co0968965 (20)
				#		Warner Bros. New Zealand																	2461 (6)			105378
				#
				#		Warner Bros. Entertainment (IMDb "Other Co")						--co0080422-- (401)		4615 (136)			17
				#		Warner Bros. Family Entertainment									co0064773 (41)			4757 (20)			3592
				#		Warner Independent Pictures (US)									co0106448 (31)			6863 (11)			11509
				#		Warner Music Vision																			21788 (28)			48503
				#		Warner Music Entertainment											co0205800 (20)			7835 (27)			3345
				#		WarnerVision Films													co0041822 (14)			37897 (8)			8316
				#		Warner Reprise Video (US)											co0057786 (12)			63462 (5)			17020
				#		WarnerMax															co0784743 (8)			83538 (7)			138252
				#		Warner Bros. Pictures de España																59370 (19)			11652
				#		Warner Bros. Studios Leavesden (GB)									co0391813 (6)
				#		Warner Brothers Productions (GB)									co0812623 (6)
				#		Warner Premiere														co0274647 (4)			5342 (42)			4811
				#		Warner Bros. Studio 2.0												co0256403 (4)			139432 (1)			178263
				#		Warner France TV (FR)												co0110958 (4)
				#		Warner Bros. Digital Networks (US)									co0652719 (3)
				#		Warner Entertainment Japan (JP)										co0212511 (3)
				#		Warner Bros. Productions (GB)										co0304934 (2)
				#		Warner & Company (US)												co0614052 (2)
				#		Warner Classics (PL)												co0631770 (1)
				#		Warner Bros. Productions											co0211276 (1)			161686 (1)			213688
				#		Warner New Asia (US)												co0507517 (1)
				#		Warner Bros. Pictures Film Prod. Award Fund							co0129483 (1)
				#		Warner Bros. Cartoon Studios (US)									co0658156 (1)
				#		Warner Bros. Consumer Products (US)									co0198927 (0)
				#
				#		Warner Horizon Television											co0183230 (78)			512 (43)			29347
				#		Warner Horizon Unscripted & Alt. Television							co0768835 (17)			51994 (19)			115672
				#
				#		Warner Brothers-Seven Arts																	4841 (46)			4051
				#		Warner Brothers/Seven Arts Television (US)							co0059798 (5)
				#		Warner Brothers/Seven Arts Animation (US)							co0189247 (0)
				#
				#		Warner Bros. First National											co0137898 (135)			9955 (40)			5301
				#		Warner Bros. First National (US)									co0065023 (4)
				#		Warner Bros.-First National Pictures (US)							co0152143 (2)
				#
				#		Warner Amex Satellite Communications								co0003381 (5)			131813 (2)			182219
				#		Warner Chappell														co0371351 (2)			61428 (3)			130062
				#		Telepictures / Warner Bros. (US)									co0279994 (2)
				#		Warner-Pathe (US)													co0809022 (1)
				#		RKO Stanley-Warner Corporation (US)									co0063400 (1)
				#		Leva FilmWorks Warner Bros. Pictures (US)							co0378906 (1)
				#		Warner Bros. Television / Fox										co0858861 (1)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		The WB																co0077535 (199)			27 (143)			21
				#		The WB Television Network (The WB) (US)								co0569058 (6)
				#
				#		Kids' WB															co0108606 (70)			1588 (0)			3932
				#		Kids' WB (US)																				2549 (0)			6050
				#		Kids WB (MX)														co1064788 (14)
				#		Kids WB (CA)														co0065120 (3)
				#
				#		Warner TV Film (DE)													co0919124 (29)
				#		WarnerTV Serie (DE)													co0909338 (24)			2570 (3)			6044
				#		Warner TV Next (FR)													co0740777 (13)			3178 (1)			7096
				#		Warner Bros. Domestic Pay TV / Cable (US)							co0301671 (13)
				#		WarnerTV Toons (MX)													co1014492 (11)
				#		Warner TV Comedy (DE)												co1010891 (4)			2993 (1)			6874
				#		Warner TV Comedy (US)												co0893585 (3)
				#		Warner TV Deutschland (DE)											co0908564 (1)
				#		Warner TV Next (FR)													co1063231 (1)
				#		Warner TV																					2218 (2)			5016
				#		Warner Tv																					2982 (0)			6871
				#		Warner TV (PL)														co0983586 (0)
				#		WarnerTV Serie (DE)													co0909047 (0)
				#
				#		Time Warner Cable (US)												co0068578 (89)
				#		Warner Channel Latin America (BR)									co0204431 (34)
				#		Warner Channel Latin America (CL)									co0545732 (19)
				#		Warner Channel (BR)																			2343 (2)			5712
				#
				#	Companies with the same name.
				#
				#		W&B Television (DE)													--co0312451-- (29)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		Warner Bros. (US)													co0002663 (5386)
				#		Warner Bros. (IT)													co0256390 (211)
				#		Warner Bros. (ca)													co0134706 (208)
				#		Warner Bros. (JP)													co0307857 (141)
				#		Warner Bros. (NL)													co0826866 (53)
				#		Warner Bros. (GB)													co0870245 (43)
				#		Warner Bros. (BE)													co0940463 (41)
				#		Warner Bros. (AR)													co0810652 (35)
				#		Warner Bros. (SE)													co0870244 (25)
				#		Warner Bros. (AU)													co0920944 (11)
				#		Warner Bros. (IE)													co0959586 (7)
				#		Warner Bros. (DK)													co1009463 (3)
				#		Warner Bros. (IN)													co1063179 (1)
				#
				#		Warner Bros. Pictures (IN)											co0342489 (488)
				#		Warner Bros. Pictures (AR)											co0498895 (343)
				#		Warner Bros. Pictures (MX)											co0158349 (170)
				#		Warner Bros. Pictures (DE)											co0519888 (160)
				#		Warner Bros. Pictures (BR)											co0350543 (135)
				#		Warner Bros. Pictures (GB)											co0816712 (101)
				#		Warner Bros. Pictures (ES)											co0782945 (96)
				#		Warner Bros. Pictures (CH)											co0239855 (68)
				#		Warner Bros. Pictures (AT)											co0456097 (67)
				#		Warner Bros. Pictures (JP)											co0633129 (39)
				#		Warner Bros. Pictures (MY)											co0362429 (13)
				#		Warner Bros. Pictures (TH)											co0245917 (11)
				#		Warner Bros. Pictures (BO)											co0364444 (9)
				#		Warner Bros. Pictures (BE)											co0822856 (3)
				#
				#		Warner Brothers Pictures (GB)										co0812621 (660)
				#		Warner Independent Pictures (US)									co0106448 (31)
				#		Warner Bros. Pictures International (US)							co0215074 (19)
				#		Warner Bros Pictures International (ES)								co0670752 (0)
				#
				#		Warner Home Video (US)												co0059995 (5982)		1549 (0)			3485
				#		Warner Home Video (NL)												co0189793 (1009)
				#		Warner Home Vídeo (BR)												co0089683 (866)
				#		Warner Home Video (AU)												co0006383 (450)
				#		Warner Home Video (CA)												co0142160 (375)
				#		Warner Home Video (JP)												co0087314 (342)
				#		Warner Home Vidéo (FR)												co0101941 (298)
				#		Warner Home Video (SE)												co0077674 (184)
				#		Warner Home Video (ES)												co0094757 (132)
				#		Warner Home Video (IT)												co0094779 (87)
				#		Warner Home Video (MX)												co0504146 (86)
				#		Warner Home Video (NO)												co0421999 (67)
				#		Warner Home Video (GB)												co0934836 (53)
				#		Warner Home Video (DE)												co0918687 (41)
				#		Warner Home Video (BE)												co0209324 (35)
				#		Warner Home Video (HK)												co0237555 (21)
				#		Warner Home Video (PL)												co0505091 (17)
				#		Warner Home Video (DK)												co0563079 (11)
				#		Warner Home Video (TR)												co0664213 (5)
				#		Warner Home Video (FI)												co1017479 (5)
				#		Warner Home Video (IL)												co0118328 (5)
				#		Warner Home Video (CZ)												co0491625 (4)
				#		Warner Home Video (SG)												co0504952 (4)
				#		Warner Home Video (HU)												co0609695 (3)
				#		Warner Home Video (KR)												co0252812 (2)
				#		Warner Home Video (NZ)												co0505090 (2)
				#		Warner Home Video (TW)												co0131854 (2)
				#		Warner Home Video (CR)												co0491626 (1)
				#		Warner Home Video (TH)												co0676595 (1)
				#
				#		Warner Bros. Home Video (MX)										co0796988 (14)
				#		Warner Bros. Home Video (US)										co0007935 (8)
				#		Warner Home Video Italia (IT)										co0570824 (4)
				#		Warner Home Video Española S.A. (ES)								co0117476 (1)
				#		Warner Home Video Inc.												co0060316 (1)
				#
				#		Warner Bros. Home Entertainment (US)								co0200179 (461)
				#		Warner Bros. Home Entertainment (DE)								co0302997 (194)
				#		Warner Bros. Home Entertainment (GB)								co0705983 (110)
				#		Warner Bros. Home Entertainment (NL)								co0720464 (97)
				#		Warner Bros. Home Entertainment (FR)								co0705982 (80)
				#		Warner Bros. Home Entertainment (AR)								co0626392 (49)
				#		Warner Bros. Home Entertainment (MX)								co0758947 (67)
				#		Warner Bros. Home Entertainment (JP)								co0495055 (8)
				#		Warner Bros. Home Entertainment (NO)								co0724683 (5)
				#		Warner Bros. Home Entertainment (SE)								co0724684 (3)
				#		Warner Bros. Home Entertainment (IT)								co0904295 (3)
				#		Warner Bros. Home Entertainment (ID)								co0738220 (3)
				#		Warner Bros. Home Entertainment (DK)								co0725007 (3)
				#		Warner Bros. Home Entertainment (BR)								co0701804 (2)
				#		Warner Bros. Home Entertainment (HK)								co0764375 (1)
				#		Warner Bros. Home Entertainment (FI)								co0725008 (1)
				#		Warner Bros. Home Entertainment (BE)								co0738052 (1)
				#		Warner Bros. Home Entertainment (CH)								co1051569 (1)
				#
				#		Warner Bros. Entertainment Finland (FI)								co0011555 (250)
				#		Warner Bros. Entertainment Australia (AU)							co0619970 (20)
				#		Warner Bros. Entertainment (CZ)										co0497928 (8)
				#		Warner Bros. Entertainment España (ES)								co0819108 (4)
				#		Warner Bros. Entertainment Sverige (SE)								co0416473 (3)
				#		Warner Bros. Entertainment (GB)										co0705919 (3)
				#		Warner Bros. Entertainment (CA)										co0245148 (2)
				#		Warner Bros. Entertainment (RU)										co0497383 (1)
				#		Warner Bros. Entertainment (ES)										co0764429 (1)
				#		Warner Bros. Entertainment Finland Oy (FI)							co0173783 (0)
				#		Warner Bros Entertainment (NO)										co0308496 (0)
				#		Warner Bros. Entertainment (SE)										co0333669 (0)
				#		Warner Bros. Entertainment (AU)										co0240701 (0)
				#		Warner Bros. Entertainment (DK)										co0352634 (0)
				#		Warner Bros. Entertainment (TW)										co0395391 (0)
				#
				#		Warner Bros. Discovery (US)											co0863266 (146)
				#		Warner Bros. Discovery (NZ)											co1005816 (3)
				#		Warner Bros. Discovery (AU)											co1031568 (1)
				#		Warner Bros. Discovery (TW)											co1031570 (1)
				#		Warner Bros. Discovery (HK)											co1031569 (1)
				#		Warner Bros. Discovery (NO)											co1058424 (0)
				#
				#		Warner Bros. Film (SE)												co0565132 (71)
				#		Warner Bros. Film (DK)												co0297444 (7)
				#		Warner Bros. Film (NO)												co0812966 (7)
				#
				#		Warner Brothers First National Films (SE)							co0535067 (335)
				#		Warner Brothers First National Films (NO)							co0692919 (219)
				#		Warner Bros. First National Films (BE)								co0350637 (77)
				#		Warner Bros First National (FR)										co0301198 (55)
				#		Warner Bros. First National Films (AT)								co0220585 (46)
				#		Warner Bros. First National Films (SE)								co0535056 (32)
				#		Warner Bros. First National Pictures (NL)							co0304370 (14)
				#		Warner Brothers First National Films (AT)							co0219725 (3)
				#		Warner Bros.-First National S.A.E. (ES)								co0780034 (3)
				#		Warner Bros.-First National Studios (GB)							co0524188 (1)
				#		Warner Brothers First National Films (CA)							co0662755 (0)
				#
				#		Warner Bros. Records (US)											co0006819 (159)
				#		Warner Records (US)													co0830537 (6)
				#
				#		Warner Music Group (US)												co0009906 (27)
				#		Warner Music Group (DE)												co0258778 (7)
				#
				#		Warner Music Group / Rhino Entertainment Co.						co0427039 (5)
				#		Warner Bros. Music (AU)												co0025297 (2)
				#		Warner Music International (US)										co0077865 (2)
				#		Warner Music Enterprises (US)										co0497257 (1)
				#		Warner Music Latina (US)											co0745167 (1)
				#
				#		Warner Music (GB)													co0221830 (8)
				#		Warner Music (FR)													co0113272 (3)
				#		Warner Music (BR)													co0017870 (2)
				#		Warner Music (AU)													co0225757 (2)
				#		Warner Music (DE)													co0357957 (1)
				#
				#		Warner Music Vision (GB)											co0013187 (6)
				#		Warner Music Vision (US)											co0039510 (4)
				#
				#		Warner Chappell Music (US)											co0882558 (6)
				#		Warner Chappell Music (GB)											co1022038 (4)
				#		Warner Chappel Music (US)											co0836843 (2)
				#		Warner / Chappell Music (CA)										co0410678 (1)
				#
				#		Warner Vision Entertainment (US)									co0072019 (12)
				#		Warner Vision France (FR)											co0101954 (11)
				#		Warner Vision International											co0030066 (7)
				#		Warner Vision Australia (AU)										co0051678 (6)
				#		Warner Vision (DE)													co0108205 (5)
				#		Warner Vision Germany (DE)											co0177654 (2)
				#		Warner Vision (JP)													co0227481 (1)
				#		Warner Vision (AU)													co0031565 (1)
				#		Warner Vision (GB)													co0104518 (1)
				#		Warner Chapel Vision (LU)											co0382216 (1)
				#
				#		Warner Bros. Dom. Television Distribution (US)						co0056265 (195)
				#		Warner Horizon Television (US)										co0183230 (79)
				#		Warner Bros. Television Distribution (US)							co0804751 (29)
				#		Warner Bros. International Television (US)							co0002939 (23)
				#		Warner Bros. Worldwide Television Distribution						co0445543 (4)
				#		Time Warner Community Access Television (US)						co0416202 (4)
				#		Warner Television													co0052955 (2)
				#		Warner Brothers Television Telepictures (US)						co0981172 (0)
				#		Warner Bros. International Television (NL)							co1040646 (0)
				#
				#		Warner Bros. Domestic Cable Distribution (US)						co0078954 (11)
				#		Time Warner Cable News (US)											co0516429 (6)
				#		Time Warner / Texas Channel (US)									co0335868 (3)
				#		DATV, Time Warner Cable Channel 20 (US)								co0748065 (2)
				#		Time Warner Cable SportsChannel (US)								co0620395 (2)
				#		Time Warner channel 6 (US)											co0543922 (1)
				#		Time Warner Cable Channel 98 (US)									co0769869 (1)
				#		Warner Film Channel (CA)											co0502853 (1)
				#		OPA Time-Warner Channel 72 (US)										co0817266 (1)
				#
				#		Time Warner Communications (US)										co0075148 (5)
				#		Warner Communications (US)											co0399929 (2)
				#		Warner Communications Company (GB)									co0011676 (0)
				#
				#		Warner (US)															co0423665 (4)
				#		Warner (FR)															co0813815 (2)
				#
				#		Warner Bros. Singapore (SG)											co0770152 (88)
				#		Warner Española S.A. (ES)											co0032440 (81)
				#		Warner Bros. Korea (KR)												co0858195 (74)
				#		Warner Bros. Turkey (TR)											co0764931 (44)
				#		Warner Bros. Finland (FI)											co0850083 (35)
				#		Warner Bros. Transatlantic											co0046746 (13)
				#		Warner Bros. Polska (PL)											co0823159 (3)
				#		Warner Slovenia (SI)												co0312698 (1)
				#		Warner Bros. South (BR)												co0498720 (0)
				#		Warner British (GB)													co0150853 (0)
				#
				#		Warner Classics (US)												co0152618 (7)
				#		Warner Classics (GB)												co0106320 (3)
				#
				#		Warner Archive Collection (US)										co0270424 (639)
				#		Warner Bros. F.E. (PH)												co0135321 (332)
				#		Time Warner															co0187668 (55)
				#		Warner Media, LLC													co0725649 (40)			2097 (0)			3233
				#		Warner Bros. Family Entertainment									co0064773 (41)
				#		Time Warner Entertainment Company									co0038141 (13)
				#		Warner Brothers Entertainment (US)									co0185428 (14)
				#		Warner Bros. Digital Distribution (US)								co0218220 (34)
				#		Warner Features Company (US)										co0128866 (31)
				#		Warner China Film HG Corporation (CN)								co0179187 (12)
				#		Warner Premiere (US)												co0197868 (7)
				#		Warner Bros. Continental Films										co0028883 (7)
				#		Warner Special Products (US)										co0139177 (4)
				#		Warner Bros. Interactive Entertainment (US)							co0108370 (4)
				#		Warner On Demand (JP)												co0403730 (2)
				#		Warner Bros. Online (US)											co0031809 (2)
				#		WarnerMedia Sales & International (US)								co0775557 (2)
				#		Warner Bros. Publications (US)										co0131608 (2)
				#		Warner Books (US)													co0206213 (2)
				#		Warner Features Company (CL)										co0298415 (1)
				#		Warner Home Video & Digital Distribution (JP)						co0932647 (1)
				#		Time Warner Interactive (US)										co0125165 (1)
				#		Warner Bros. Short Films (US)										co0004441 (1)
				#		Warner's Feature Film Co (GB)										co0805127 (1)
				#		Warner Company (US)													co0077784 (1)
				#		Warner's Features (GB)												co0339073 (0)
				#		Vod-Warner Home Video (US)											co0218114 (0)
				#		Warner Films HD (CA)												co0502722 (0)
				#		WarnerMedia Direct (US)												co0937798 (0)
				#		Warner Bros. Movie World (ES)										co0108196 (0)
				#		Warner Bros. Movie World (AU)										co0183782 (0)
				#		Warner Bros Films (US)												co0635467 (0)
				#
				#		Warner-Columbia Film (SE)											co0214905 (385)
				#		Columbia-EMI-Warner (GB)											co0106070 (266)
				#		Columbia-Warner Distributors (GB)									co0110090 (258)
				#		Columbia-Warner Filmes de Portugal (PT)								co0438107 (228)
				#		Warner-Columbia Films (AR)											co0372744 (222)
				#		Warner-Columbia Filmverleih (DE)									co0118308 (218)
				#		Columbia TriStar Warner Filmes de Portugal (PT)						co0075764 (179)
				#		Warner-Columbia Film (FR)											co0053539 (160)
				#		Warner-Columbia Films (FI)											co0176140 (125)
				#		Columbia-Cannon-Warner (GB)											co0120631 (67)
				#		Warner-Columbia (AT)												co0108012 (36)
				#		Warner Bros. / Columbia Pictures (FI)								co0185616 (18)
				#		Warner Columbia Film (BE)											co0162942 (14)
				#		Warner Columbia Film (BE)											co0162942 (14)
				#		Warner-Columbia (NL)												co0991324 (10)
				#		Warner-Columbia (BE)												co0537026 (7)
				#		Warner-Columbia Film (PT)											co0730604 (5)
				#		Columbia-Warner Distributors (FR)									co0825783 (5)
				#		Columbia-Warner Films (BR)											co0840651 (1)
				#		Warner-Columbia Films (ES)											co0544343 (1)
				#		Columbia-Warner Distributiors (FR)									co0793828 (0)
				#		Warner-Columbia (IT)												co0453812 (0)
				#		Columbia-Warner Distributiors (FR)									co0793828 (0)
				#
				#		Warner Bros./Seven Arts (US)										co0076018 (71)
				#		Warner Bros./Seven Arts (NL)										co0402893 (17)
				#		Warner Bros./Seven Arts (FR)										co0286417 (14)
				#		Warner Bros./Seven Arts (JP)										co0237970 (6)
				#		Warner Bros./Seven Arts (DE)										co0227665 (8)
				#		Warner Bros./Seven Arts (AR)										co0679446 (6)
				#		Warner Bros./Seven Arts (IT)										co0649990 (5)
				#		Warner Bros./Seven Arts (ES)										co0654365 (3)
				#		Warner Bros./Seven Arts (FI)										co0453813 (2)
				#		Warner Bros./Seven Arts (BE)										co0352118 (2)
				#		Warner Bros./Seven Arts (HK)										co0747433 (1)
				#
				#		Fox-Warner (CH)														co0125154 (305)
				#		Fox-Warner (NL)														co0815746 (3)
				#		Warner/Fox (PE)														co0224399 (1)
				#
				#		Warner Pioneer Video												co0070086 (2)
				#		Warner Pioneer (JP)													co0256160 (2)
				#		Warner-Pioneer (US)													co0146101 (1)
				#
				#		Warner-Pathé Distributors (GB)										co0106012 (315)
				#		Warner Sogefilms S.A. (ES)											co0040785 (94)
				#		Warner-Tonefilm (SE)												co0214931 (76)
				#		Warner Sogefilms A.I.E. (ES)										co0081227 (74)
				#		Warner-Sergel Film (SE)												co0287772 (28)
				#		Warner Filipacchi Vidéo (FR)										co0512860 (25)
				#		Warner Roadshow Film Distributors (GR)								co0029726 (22)
				#		AOL Time Warner														co0123357 (20)
				#		BBC Warner															co0225995 (15)
				#		Warner & Metronome Film (DK)										co0094755 (11)
				#		Marvista Entertainment / Warner VOD (US)							co0290255 (11)
				#		Warner-Constantin (DK)												co0179125 (6)
				#		Warner Mycal K.K. (JP)												co0154279 (5)
				#		Warner-Lusomundo (PT)												co0166128 (4)
				#		Warner-Golden Village (SG)											co0030701 (3)
				#		Dear-Warner Home Video (IT)											co0191174 (2)
				#		Warner-Allender Roadshows Inc.										co0043200 (2)
				#		Jack Records/Warner Brothers Records (US)							co0244887 (2)
				#		Warner / Eurpac (RU)												co0427898 (1)
				#		Intravision/Warner (US)												co0112558 (1)
				#		IFISA Warner Bros IFISA												co0056681 (1)
				#		Warner-Tamerlane Publishing (US)									co0626379 (1)
				#		MGM/Warner (US)														co0194242 (0)
				#		Warner Bros. Television/CBS Studios (US)							co0856617 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyWarner : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Warner Bros Pictures'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'The WB'},
					'vendor'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'Warner Bros'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'The WB Originals'},
					'expression'	: '(warner(?:[\s\-\_\.\+]*(?:media|max))?|(?:^|the[\s\-\_\.\+]*|kids.?[\s\-\_\.\+]*)wb)',
				},

				#################################################################################################################################
				# The Weinstein Company
				#
				#	The Weinstein Brothers created this company after leaving Miramax after it was sold to Disney.
				#
				#	Parent Companies:		Weinstein Brothers
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			The Weinstein Company, Dimension Films (previous, now Paramount), Dragon Dynasty, Mizchief,
				#							TWC-Dimension, RADiUS-TWC, Kaleidoscope-TWC, The Miriam Collection
				#	Owned Networks:			-
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	Dimension Films
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(400)					(116)
				#	Networks																(0)						(0)
				#	Vendors																	(62)					(0)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		The Weinstein Company (US)											co0150452 (342)			613 (116)			308
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		RADiUS-TWC (US)														co0368345 (50)
				#		TWC-Dimension (US)													co0446953 (9)
				#		Kaleidoscope TWC (US)												co0210128 (1)
				#		TWC Asian Film Fund (US)											co0349607 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyWeinstein : {
					'studio'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'The Weinstein Company'},
					'network'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'Weinstein'},
					'original'		: {Media.Movie : False,	Media.Show : False,	'label' : None},
					'expression'	: '(weinstein[\s\-\_\.\+]*company|(?:^|[\s\-])twc(?:$|[\s\-]))',
				},

				#################################################################################################################################
				# YouTube
				#
				#	Parent Companies:		YouTube
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			-
				#	Owned Networks:			YouTube, YouTube Red, YouTube Premium, YouTube TV
				#
				#	Streaming Services:		-
				#	Collaborating Partners:	-
				#
				#	Content Provider:		-
				#	Content Receiver:		-
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(229)					(258)
				#	Networks																(25982)					(2463)
				#	Vendors																	(35)					(0)
				#	Originals																(54 / 176)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		YouTube																						10650 (202)			114247
				#		YouTube Originals													co0715084 (124)			93922 (35)			144823
				#		YouTube Red															co0722763 (5)			3067 (25)			73091
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		YouTube (US)														co0202446 (11037)
				#		YouTube (IN)														co1017567 (109)
				#		YouTube (ES)														co0925788 (11)
				#		YouTube (CA)														co1020655 (5)
				#		YouTube (AU)														co1009431 (2)
				#		YouTube (IT)														co1038049 (1)
				#		YouTube (MX)														co1025883 (1)
				#
				#		YouTube																						1205 (1)			3692
				#		YouTube																						49 (2387)			247
				#		YouTube																						2907 (0)			6720
				#		YouTube																						2908 (0)			6721
				#		Youtube																						2149 (0)			5234
				#
				#		YouTube Originals (US)												co0715084 (124)
				#		YouTube Premium (US)												co0574035 (76)			240 (78)			1436
				#		YouTube Red (US)													co0722763 (5)
				#		YouTube Kids														co0687834 (5)			2248 (0)			5534
				#
				#		YouTube TV (US)														co0883766 (20)
				#		Youtube TV (BR)														co1045018 (2)
				#
				#		Youtube Filme & TV (DE)												co1055457 (193)
				#		YouTube Movies (US)													co0847367 (29)
				#		YouTube Movie/Films (US)											co0494570 (4)
				#		YouTube Music (US)													co0701624 (2)
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		YouTube Space (US)													co0506705 (2)
				#		YouTube Space LA (US)												co0457964 (2)
				#		YouTube Space Brazil (BR)											co0932994 (1)
				#		YouTube Space Paris (FR)											co0711702 (1)
				#		YouTube Space House of Horrors (US)									co0506486 (1)
				#		YouTube Space London (GB)											co0702332 (1)
				#		YouTube Space São Paulo (BR)										co0957563 (0)
				#
				#################################################################################################################################
				MetaCompany.CompanyYoutube : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'YouTube Productions'},
					'network'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'YouTube'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'YouTube'},
					'original'		: {Media.Movie : 1,		Media.Show : 1,		'label' : 'YouTube Originals'},
					'expression'	: '(you[\s\-\_\.\+]*tube[\s\-\_\.\+]*(?:red|premium|originals?|kids?|space)?|^yt$)',
				},

				#################################################################################################################################
				# ZDF
				#
				#	Owned and funded by German Government.
				#	Was created to combat the monopoly of ARD.
				#	Unlike ARD, does not own a bunch of local networks.
				#	Co-productions and content sharing with UK (BBC, ITV, etc), France (ARTE, etc), Scandinavian and most other European countries.
				#
				#	Parent Companies:		German government
				#	Sibling Companies:		-
				#	Child Companies:		-
				#
				#	Owned Studios:			ZDF Studios
				#	Owned Networks:			ZDF, KiKa (ARD+ZDF), Phoenix (ARD+ZDF), 3sat (ARD+ZDF+ORF+SSR)
				#
				#	Streaming Services:		ZDF Mediathek
				#	Collaborating Partners:	BBC, ITV, ARTE
				#
				#	Content Provider:		-
				#	Content Receiver:		Phoenix, 3sat
				#
				#################################################################################################################################
				#
				#																			IMDb					Trakt				TMDb
				#	Studios																	(1878)					(2980)
				#	Networks																(10373)					(1384)
				#	Vendors																	(11)					(0)
				#	Originals																(6858 / 2161)
				#
				#################################################################################################################################
				#	Studios
				#################################################################################################################################
				#
				#		ZDF (DE)																					1628 (2723)			4606
				#		ZDF Productions (DE)												co0075883 (21)
				#		ZDF Studios (DE)													co0908556 (99)			175124 (6)			225782
				#		ZDF Digital (DE)													co0678159 (2)			175071 (2)			225783
				#
				#		ZDF Enterprises (DE)												co0038987 (301)
				#		Das kleine Fernsehspiel (ZDF) (DE)									co0222794 (201)
				#		2DF																							12725 (66)			84339
				#		ZDFinfo (DE)																				107311 (33)			158863
				#		ZDF Tivi (DE)														co0196399 (14)			136686 (1)			187421
				#
				#		ZDF/Arte (DE)														co0174795 (369)			5028 (195)			11237
				#		ARD/ZDF (DE)														co0297730 (7)
				#		Funk (ARD/ZDF) (DE)													co0622438 (1)
				#		ZDF / 3sat (DE)														co1040317 (1)
				#		ZDF/Quantum (DE)													co0576396 (0)
				#
				#	Other companies with the same name.
				#
				#		2DF Enterprises (US)												--co0188641-- (2)
				#
				#################################################################################################################################
				#	Networks
				#################################################################################################################################
				#
				#		Zweites Deutsches Fernsehen (ZDF) (DE)								co0078814 (3261)
				#		ZDF (DE)															co1069160 (53)			139 (1030)			31
				#
				#		ZDF Theaterkanal (DE)												co0126641 (30)			3861 (2)			5787
				#		ZDFdokukanal (DE)													co0187579 (24)
				#
				#		ZDFneo (DE)															co0284784 (293)			178 (93)			1274
				#		ZDFinfo (DE)														co0269033 (114)			482 (56)			1350
				#		ZDFinfo (DE)																				2704 (0)			6272
				#		ZDFkultur (DE)														co0337126 (70)			1201 (6)			3170
				#		ZDFComedy (DE)														co0949312 (1)
				#
				#		ZDF Select (DE)														co0989446 (45)
				#		ZDF Tivi Select (DE)												co1035686 (8)
				#
				#		ZDF Mediathek (DE)													co0364332 (391)
				#		ZDF Krimi (DE)														co0993663 (20)
				#		ZDF Herzkino (DE)													co0993978 (12)
				#		ZDF German Television (DE)											co0866170 (3)
				#		ZDF Contemporary History Department (DE)							co0473935 (1)
				#
				#		Kinderkanal (KiKA) (DE)												co0030553 (376)
				#		Kika (DE)															co0895262 (145)			268 (215)			239
				#		ARD / ZDF Kinderkanal (KIKA) (DE)									co0937862 (126)
				#		KIKA Mediathek (DE)													co1050978 (25)
				#
				#		Phoenix (DE)														co0178657 (90)			2325 (13)			3860
				#
				#################################################################################################################################
				#	Vendors
				#################################################################################################################################
				#
				#		ZDF Archive (DE)													co0236711 (1)
				#		ZDF Programmservice (DE)											co0572131 (1)
				#
				#################################################################################################################################
				MetaCompany.CompanyZdf : {
					'studio'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ZDF Studio'},
					'network'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ZDF'},
					'vendor'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ZDF'},
					'original'		: {Media.Movie : 1000,	Media.Show : 1000,	'label' : 'ZDF Originals'},
					'expression'	: '([z2]df|zweites[\s\-\_\.\+]*deutsches[\s\-\_\.\+]*fernsehen|ki\.?ka|kinder[\s\-\_\.\+]*kanal|^phoenix$)',
				},
			}

		return MetaCompany.Companies if company is None else MetaCompany.Companies.get(company)

	###################################################################
	# ADDON
	###################################################################

	@classmethod
	def addon(self):
		mode = self.settingsMode()
		if mode == MetaCompany.ModeDisabled or mode == MetaCompany.ModeSingle or mode == MetaCompany.ModeMultiple: ids = []
		elif mode == MetaCompany.ModeWhite: ids = [MetaCompany.IdWhite]
		elif mode == MetaCompany.ModeColor: ids = [MetaCompany.IdColor]
		elif mode == MetaCompany.ModeForceWhite: ids = [MetaCompany.IdColor, MetaCompany.IdWhite] # The white textures are added to the color addon, so use IdColor first. Still add IdWhite as a backup, in case the color addon is not installed.
		elif mode == MetaCompany.ModeForceColor: ids = [MetaCompany.IdWhite, MetaCompany.IdColor] # The color textures are added to the white addon, so use IdWhite first. Still add IdColor as a backup, in case the white addon is not installed.
		else:
			ids = [MetaCompany.IdWhite, MetaCompany.IdColor] # Most skins use the white icons. Use IdWhite first.
			if mode == MetaCompany.ModeAutomatic:
				# Determine the default studio icons based on the skin dependencies.
				# Most skins do not have studio icons listed as a dependency at all, or they only have white icons as dependency, although they support color icons as well (through an advanced skin setting).
				# Hence, even if they are not listed as dependency, still include them. Just order based on available dependencies.
				dependencies = Skin.dependencies(detail = False)
				if dependencies:
					if MetaCompany.IdWhite in dependencies: ids = [MetaCompany.IdWhite, MetaCompany.IdColor]
					elif MetaCompany.IdColor in dependencies: ids = [MetaCompany.IdColor, MetaCompany.IdWhite]

		id = None
		enabled = False
		version = None
		white = False
		color = False
		old = False
		new = False

		for id in ids:
			addon = System.addonDetails(id = id)
			if addon:
				white = 'white' in id
				color = not white
				enabled = addon.get('installed') and addon.get('enabled')
				version = addon.get('version')

				if mode == MetaCompany.ModeForceWhite:
					white = True
					color = False
					addon2 = System.addonDetails(id = MetaCompany.IdWhite)
					if addon2: version = addon2.get('version')
				elif mode == MetaCompany.ModeForceColor:
					white = False
					color = True
					addon2 = System.addonDetails(id = MetaCompany.IdColor)
					if addon2: version = addon2.get('version')

				try:
					# The addon v0.0.30 (white) / v0.0.23 (coloured) and prior have a lot less icons. Make special accomodation for that.
					# As of Apr 2025, v0.0.30/v0.0.23 is still the official version on the Kodi repo.
					# More details at: https://github.com/gaiakodi/gaiamain/tree/master/common/resource.images.studios.white/readme.txt
					if version:
						versioned = version.split('~')[0] # Alpha/beta for the custom versions in Gaia's repo.
						versioned = [int(i) for i in versioned.split('.')]
						maximum = MetaCompany.VersionColor if color else MetaCompany.VersionWhite
						old = versioned[0] == maximum[0] and versioned[1] == maximum[1] and versioned[2] <= maximum[2]
						new = not old
				except: Logger.error()

				if enabled: break

		return {
			'id' : id,
			'mode' : mode,
			'type' : MetaCompany.TypeColor if color else MetaCompany.TypeWhite,
			'release' : MetaCompany.ReleaseNew if new else MetaCompany.ReleaseOld,
			'enabled' : enabled,
			'version' : version,
		}

	###################################################################
	# HELPER
	###################################################################

	@classmethod
	def helper(self, *key):
		if MetaCompany.Helper is None:
			# Cache the entire structure, not only the "include" dict.
			id = 'GaiaCompanyHelper_' + self.settingsMode() # Do not use if the settings were changed.
			MetaCompany.Helper = Memory.get(id = id, local = False, kodi = True)

			if MetaCompany.Helper is None:
				addon = MetaCompany.addon()
				if addon and addon.get('enabled'):
					include = MetaCompany._helperInclude(type = addon.get('type'), release = addon.get('release'))
					replacement = MetaCompany._helperReplacement(type = addon.get('type'), release = addon.get('release'))
				else:
					include = None
					replacement = None

				MetaCompany.Helper = {
					'addon' : addon,
					'include' : include,
					'replacement' : replacement,

					'partial' : {
						# A lot more icons for "Twentieth" than for "20th".
						'(20th[\s\-]*century)(?![\s\-]fox)' : 'Twentieth Century Fox',
						'(20th[\s\-]*century)' : 'Twentieth Century',
					},

					# Prefer these over other names.
					# Eg: Rather pick "HBO Max" over "HBO" for the icon.
					'preference' : {
						Media.Show : ('HBO Max', 'Max'), # Only do this for shows. Otherwise the HBO logo is shown for movies (eg: Jack Snyder's Justice League)
					},

					# Values should contain as many words as possible.
					# Used for merging multiple arrays and determine how frequent a studio is.
					# Eg: TMDb/TVDb return "Prime Video", while Trakt uses "Amazon".
					'alias' : {
						'Prime Video' : 'Amazon Prime Video',
						'Amazon' : 'Amazon Prime Video',
					},

					# Words to exclude for networks matching.
					'ignore' : {
						'studio' : True, 'studios' : True,
						'network' : True, 'networks' : True, 'networking' : True,
						'broadcaster' : True, 'broadcasters' : True, 'broadcasting' : True,
						'production' : True, 'productions' : True,
						'television' : True, 'tv' : True,
						'film' : True, 'films' : True,
						'picture' : True, 'pictures' : True,
						'channel' : True, 'channels' : True,
						'comic' : True, 'comics' : True,
						'enterprise' : True, 'enterprises' : True,
						'company' : True, 'companies' : True,
						'corporation' : True, 'corporations' : True, 'corp' : True,
						'enterprise' : True, 'enterprises' : True,
						'industries' : True, 'ltd' : True, 'media' : True, 'entertainment' : True, 'content' : True,
						'international' : True, 'global' : True, 'i' : True, 'ii' : True, 'iii' : True,
						'us' : True, 'uk' : True, 'ca' : True, 'canada' : True, 'au' : True, 'australia' : True,
					},

					# Also used by MetaManager.
					# This means it was released/licensed to multiple TV stations, mostly old shows, but sometimes new ones as well.
					# Eg: Star Trek (1966).
					'syndication' : {
						'Syndication' : True,
						'Syndications' : True,
						'Syndicator' : True,
						'Syndicators' : True,
						'Syndicate' : True,
						'Syndicated' : True,
						'Syndicating' : True,
						'Syndicatings' : True,
					},
				}

				Memory.set(id = id, value = MetaCompany.Helper, local = False, kodi = True)

		try:
			result = MetaCompany.Helper
			for i in key: result = result.get(i)
			return result
		except: Logger.error()
		return None

	@classmethod
	def helperAddon(self):
		return self.helper('addon')

	@classmethod
	def helperInclude(self):
		return self.helper('include')

	@classmethod
	def helperReplacement(self):
		return self.helper('replacement')

	@classmethod
	def helperPartial(self):
		return self.helper('partial')

	@classmethod
	def helperPreference(self):
		return self.helper('preference')

	@classmethod
	def helperAlias(self):
		return self.helper('alias')

	@classmethod
	def helperIgnore(self):
		return self.helper('ignore')

	@classmethod
	def helperSyndication(self):
		return self.helper('syndication')

	@classmethod
	def _helperInclude(self, type, release):
		# There are a few problems with the studio icons addons:
		#	1. Many logos are not included in the addon at all and will therefore not be displayed.
		#	2. Encoding, unicode, and accents can cause logos not to be displayed. Eg: "RTÉ" vs "RTE", spaces vs dashes, etc.
		#	3. Differences in names can cause logos not to be displayed. Eg: "XYZ Ltd" vs "XYZ Ltd." vs "XYZ Limited" vs "XYZ, Ltd.", "20th" vs "Twentieth".
		#	4. Lower vs upper case letters. This is only a problem if the addon contains individual PNG images. If Textures.xbt is used, lower/upper case characters work correctly and are NOT a problem. Eg: "AMC" vs "Amc" vs "amc".
		# Shows are mostly not a problem, since they use the network for the icon and 95% of titles have an icon.
		# Movies are a bigger problem. Many movies these days are produced by smaller studio that do not have an icon.
		# However, often there is a larger studio with an icon listed later in the studio list.
		#	Eg: Small Studio 1 (no icon) / Small Studio 2 (no icon) / Big Studio 1 (icon) / Big Studio 2 (no icon) / Small Studio 3 (icon)
		# Previously there was an "exclude" section here which listed a bunch of studios without an icon that should be ignored.
		# However, this is not a feasible method. There are simply too many smaller studios (and many more to come in the future) to exclude them all.
		# A better method is to create a list of names that are available in the studio icon addons. Then scan through the studio list until one is found that is available in the addon.

		#gaiaremove - The company JSON list in script.gaia.resources should be regenerated (tools/texture/texture.py) if a new version of these addons is released (current version in the official repo: resource.images.studios.white-0.0.30, resource.images.studios.coloured-0.0.23)
		# Update (2025-12):
		#	White: Created the custom 0.0.33~alpha1 from the XBMC-Addons Github repo's 0.0.33 release. The version in the official Kodi Omega repo is still 0.0.30.
		#	Colored: Created the custom 0.0.24~alpha1 rom the XBMC-Addons Github repo's 0.0.23 release, plus latest Lynxstrike icons, plus the new 0.0.33 white icons. The version in the official Kodi Omega repo is still 0.0.23.

		try:
			path = File.joinPath(System.pathResources(), 'resources', 'media', 'company', '%s%s.json' % (type, release))
			data = Converter.jsonFrom(File.readNow(path))
			return {i : True for i in data} # Create a dictionary from the list, for faster lookups.
		except: Logger.error()
		return None

	@classmethod
	def _helperReplacement(self, type, release):
		base = {
			# Example: A Netflix Original Documentary
			'^(?:(?:a|the)\s)?netflix' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Netflix',							MetaCompany.ReleaseNew : 'Netflix'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Netflix',							MetaCompany.ReleaseNew : 'Netflix'},
			},

			# Example: Amazon Video
			'^amazon[\s\-]*video' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Amazon',							MetaCompany.ReleaseNew : 'Amazon Prime Video'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Amazon Video',						MetaCompany.ReleaseNew : 'Amazon Video'},
			},
			# Example: Amazon Prime Video
			# Example: Prime Video
			'^(?:amazon[\s\-]*prime|prime[\s\-]*video)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Amazon',							MetaCompany.ReleaseNew : 'Amazon Prime Video'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Amazon Prime Video',				MetaCompany.ReleaseNew : 'Amazon Prime Video'},
			},
			# Example: Amazon Freevee
			'^amazon[\s\-]*freevee' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Amazon',							MetaCompany.ReleaseNew : 'Amazon'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Freevee',							MetaCompany.ReleaseNew : 'Amazon Freevee'},
			},

			# Example: Peacock
			'^peacock$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'NBC Universal Television',			MetaCompany.ReleaseNew : None}, # No icon in the old pack, use a different icon to "NBC".
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},
			# Example: Comcast
			'^comcast' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'NBC Universal Global Networks',	MetaCompany.ReleaseNew : 'NBC Universal Global Networks'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'NBC Universal Global Networks',	MetaCompany.ReleaseNew : 'NBC Universal Global Networks'},
			},

			# Example: discovery+
			'^discovery[\s\-]*(?:\+|plus)$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Discovery',						MetaCompany.ReleaseNew : 'Discovery+'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Discovery+',						MetaCompany.ReleaseNew : 'Discovery+'},
			},
			# Example: Discovery+1
			'^discovery[\s\-]*(?:\+|plus).+' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Discovery',						MetaCompany.ReleaseNew : 'Discovery+'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None}, # Has various other Discovery+X icons.
			},
			# Example: Discovery Family
			'^discovery[\s\-]*(?:family|kids?)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Discovery',						MetaCompany.ReleaseNew : 'Discovery'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Discovery Kids',					MetaCompany.ReleaseNew : 'Discovery Kids'},
			},

			'^national[\s\-]*geographic[\s\-]*hd' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'National Geographic',				MetaCompany.ReleaseNew : 'National Geographic'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'National Geographic HD',			MetaCompany.ReleaseNew : 'National Geographic HD'},
			},
			'^national[\s\-]*geographic[\s\-]*channel' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'National Geographic',				MetaCompany.ReleaseNew : 'National Geographic'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'National Geographic Channel',		MetaCompany.ReleaseNew : 'National Geographic Channel'},
			},
			# Example: National Geographic Documentary Films
			'^national[\s\-]*geographic' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'National Geographic',				MetaCompany.ReleaseNew : 'National Geographic'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'National Geographic',				MetaCompany.ReleaseNew : 'National Geographic'},
			},

			# This is rather Showtime, even if Paramount is listed first.
			# Example: Paramount+ with Showtime
			'^paramount[\s\-]*(?:\+|plus)[\s\-]*with' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Showtime',							MetaCompany.ReleaseNew : 'Showtime'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Showtime',							MetaCompany.ReleaseNew : 'Showtime'},
			},

			# Example: Disney Jr.
			'^disney[\s\-]*(?:jr|junior)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Disney Junior',					MetaCompany.ReleaseNew : 'Disney Junior'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Disney Channel',					MetaCompany.ReleaseNew : 'Disney Channel'},
			},
			# Example: Toon Disney
			'^toon[\s\-]*disney' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'DisneyToon Studios',				MetaCompany.ReleaseNew : 'DisneyToon Studios'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Toon Disney',						MetaCompany.ReleaseNew : 'Toon Disney'},
			},
			# Example: Disney Toon
			'^disney[\s\-]*toon' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'DisneyToon Studios',				MetaCompany.ReleaseNew : 'DisneyToon Studios'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Disney Toon',						MetaCompany.ReleaseNew : 'Disney Toon'},
			},
			# Example: Disney Channels Worldwide
			'^disney[\s\-]*channels?[\s\-]*(?:world|international)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Disney Channel',					MetaCompany.ReleaseNew : 'Disney Channel'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Disney Channel',					MetaCompany.ReleaseNew : 'Disney Channel'},
			},
			# Example: Disney Enterprises
			'^disney[\s\-]*enterprises?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Disney',							MetaCompany.ReleaseNew : 'Disney'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Disney',							MetaCompany.ReleaseNew : 'Disney'},
			},

			# Example: Sky HD
			# Example: Sky+
			'^sky[\s\-]*(?:hd|\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
			},
			# Example: Sky Max
			'^sky[\s\-]*max' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky Max',							MetaCompany.ReleaseNew : 'Sky Max'},
			},
			# Example: Sky Showcase
			'^sky[\s\-]*showcase' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky Showcase',						MetaCompany.ReleaseNew : 'Sky Showcase'},
			},
			# Example: SkyShowtime
			'^sky[\s\-]*showtime' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
			},
			# Example: Sky Deutschland
			'^sky[\s\-]*[\s\(\[](?:germany|deutschland|de)(?:[\s\)\]]|$)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky Deutschland'},
			},
			# Example: Sky Italia
			'^sky[\s\-]*[\s\(\[](?:italia|italy|it)(?:[\s\)\]]|$)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
			},
			# Example: Sky Atlantic (UK)
			'^sky[\s\-]*atlantic[\s\-]*[\s\(\[](?:uk|gb)(?:[\s\)\]]|$)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky Atlantic (UK)',				MetaCompany.ReleaseNew : 'Sky Atlantic (UK)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky Atlantic',						MetaCompany.ReleaseNew : 'Sky Atlantic (UK)'},
			},
			# Example: Sky Atlantic (DE)
			'^sky[\s\-]*atlantic[\s\-]*[\s\(\[](?:germany|deutschland|de)(?:[\s\)\]]|$)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky Atlantic',						MetaCompany.ReleaseNew : 'Sky Atlantic (DE)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky Atlantic',						MetaCompany.ReleaseNew : 'Sky Atlantic (DE)'},
			},
			# Example: Sky Documentaries
			'^sky[\s\-]*documentar' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky Documentaries',				MetaCompany.ReleaseNew : 'Sky Documentaries'},
			},
			# Example: Sky Studios
			'^sky[\s\-]*studios?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sky',								MetaCompany.ReleaseNew : 'Sky'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sky Cinema',						MetaCompany.ReleaseNew : 'Sky Cinema'},
			},
			# Example: BSkyB
			'^bskyb' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BSkyB',							MetaCompany.ReleaseNew : 'BSkyB'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'British Sky Broadcasting (BSkyB)',	MetaCompany.ReleaseNew : 'British Sky Broadcasting (BSkyB)'},
			},

			# Example: MGM+
			'^mgm[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'MGM',								MetaCompany.ReleaseNew : 'MGM'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'MGM',								MetaCompany.ReleaseNew : 'MGM+'},
			},
			# Example: MGM HD
			'^mgm[\s\-]*hd' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'MGM',								MetaCompany.ReleaseNew : 'MGM'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'MGM HD',							MetaCompany.ReleaseNew : 'MGM HD'},
			},
			# Example: Amazon MGM Studios
			'^amazon.*(?:mgm|metro.*goldwyn.*mayer)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'MGM',								MetaCompany.ReleaseNew : 'MGM'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'MGM',								MetaCompany.ReleaseNew : 'MGM'},
			},

			# Example: Apple TV
			'^apple[\s\-]*(?:tv|plus|\+)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Apple TV+',						MetaCompany.ReleaseNew : 'Apple TV+'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Apple TV+',						MetaCompany.ReleaseNew : 'Apple TV+'},
			},

			# Example: Apple Original Films
			# Example: Apple Studios
			'^apple[\s\-]*(?:original|studio)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Apple TV+',						MetaCompany.ReleaseNew : 'Apple TV+'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Apple TV+',						MetaCompany.ReleaseNew : 'Apple Studios'},
			},

			# Example: HBO Latino
			'^hbo[\s\-]*latin[oa]' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'HBO',								MetaCompany.ReleaseNew : 'HBO'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'HBO',								MetaCompany.ReleaseNew : 'HBO'},
			},
			# In the new color icons there is a "Max" from a different studio.
			# But assume this is HBO.
			# Example: Max
			'^max$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'HBO Max',							MetaCompany.ReleaseNew : 'HBO Max'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'HBO Max',							MetaCompany.ReleaseNew : 'HBO Max'},
			},

			# Example: AMC+
			'^amc[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'AMC',								MetaCompany.ReleaseNew : 'AMC'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'AMC+',								MetaCompany.ReleaseNew : 'AMC+'},

			},
			# Example: AMC HD
			'^amc[\s\-]*hd' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'AMC',								MetaCompany.ReleaseNew : 'AMC'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'AMC HD',							MetaCompany.ReleaseNew : 'AMC HD'},
			},
			# Example: Shudder
			'^shudder$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'AMC',								MetaCompany.ReleaseNew : None}, # No icon the the old pack.
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},

			# Example: CBS Studios
			'^cbs[\s\-]*studios?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'CBS Productions',					MetaCompany.ReleaseNew : 'CBS Productions'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'CBS Productions',					MetaCompany.ReleaseNew : 'CBS Productions'},
			},

			# Example: STARZ+
			'^starz[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'STARZ',							MetaCompany.ReleaseNew : 'STARZ'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'STARZ',							MetaCompany.ReleaseNew : 'STARZ'},
			},

			# Example: BBC Scotland
			'^bbc[\s\-]*scotland' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BBC',								MetaCompany.ReleaseNew : 'BBC'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BBC 1 Scotland',					MetaCompany.ReleaseNew : 'BBC 1 Scotland'},
			},
			# Example: BBC Wales
			'^bbc[\s\-]*scotland' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BBC',								MetaCompany.ReleaseNew : 'BBC'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BBC 1 Wales',						MetaCompany.ReleaseNew : 'BBC 1 Wales'},
			},
			# Example: BBC One Northern Island
			'^bbc[\s\-]*one[\s\-\(\[]*[a-z]' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BBC One',							MetaCompany.ReleaseNew : 'BBC One'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BBC One',							MetaCompany.ReleaseNew : 'BBC One'},
			},
			# Example: BBC Film
			'^bbc[\s\-]*film' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BBC Films',						MetaCompany.ReleaseNew : 'BBC Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BBC Films',						MetaCompany.ReleaseNew : 'BBC Films'},
			},
			# Used by shows, so replacing with "BBC" instead of "BBC Films" is probably better.
			# Example: BBC Studios
			'^bbc[\s\-]*studio' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BBC',								MetaCompany.ReleaseNew : 'BBC'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BBC',								MetaCompany.ReleaseNew : 'BBC'},
			},
			# Example: BBC Worldwide
			'^bbc[\s\-]*(?:worldwide|international)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BBC',								MetaCompany.ReleaseNew : 'BBC'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BBC',								MetaCompany.ReleaseNew : 'BBC'},
			},

			# Sometimes returned by TMDb and should already be replaced in _mergeMetaCompany().
			# Example: 5
			'^5$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Channel 5',						MetaCompany.ReleaseNew : 'Channel 5'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Channel 5',						MetaCompany.ReleaseNew : 'Channel 5'},
			},

			# Not sure if this happens, but do the same as for Channel 5.
			# Example: 4
			'^4$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Channel 4',						MetaCompany.ReleaseNew : 'Channel 4'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Channel 4',						MetaCompany.ReleaseNew : 'Channel 4'},
			},
			# Example: More4
			'^more[\s\-]*(?:4|four)$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Channel 4',						MetaCompany.ReleaseNew : 'Channel 4'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'More4',							MetaCompany.ReleaseNew : 'More4'},
			},
			# Example: Film4 Productions
			'^film[\s\-]*(?:4|four)[\s\-]*productions?$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Film4',							MetaCompany.ReleaseNew : 'Film4 Productions'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Film4 Productions',				MetaCompany.ReleaseNew : 'Film4 Productions'},
			},

			# Example: ITVX
			'^itv[\s\-]*x' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ITV',								MetaCompany.ReleaseNew : 'ITV'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ITVX',								MetaCompany.ReleaseNew : 'ITVX'},
			},

			# Example: History Canada
			'^history[\s\-]*(?:[\s\(\[]canada|ca(?:[\s\)\]]|$))' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'History (CA)',						MetaCompany.ReleaseNew : 'History (CA)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'History',							MetaCompany.ReleaseNew : 'History'},
			},

			# Example: Spike
			'^spike$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Spike TV',							MetaCompany.ReleaseNew : 'Spike TV'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Spike TV',							MetaCompany.ReleaseNew : 'Spike TV'},
			},

			# Example: Fox Sports 1
			'^fox[\s\-]*sport' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Fox Sports (AU)',					MetaCompany.ReleaseNew : 'Fox Sports (AU)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Fox',								MetaCompany.ReleaseNew : 'Fox'},
			},
			# Example: Fox Nation
			'^fox[\s\-]*nation' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Fox',								MetaCompany.ReleaseNew : 'Fox'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Fox',								MetaCompany.ReleaseNew : 'Fox'},
			},
			# Example: Fox Kids
			'^fox[\s\-]*(?:kids|children|family)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Fox',								MetaCompany.ReleaseNew : 'Fox'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Fox Family',						MetaCompany.ReleaseNew : 'Fox Family'},
			},

			# Example: Nickelodeon (US)
			'^nickelodeon[\s\-]*[\(\[]' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Nickelodeon',						MetaCompany.ReleaseNew : 'Nickelodeon'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Nickelodeon',						MetaCompany.ReleaseNew : 'Nickelodeon'},
			},

			# Example: Cartoon Network (UK)
			'^cartoon[\s\-]*network[\s\-]*[\s\(\[]' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Cartoon Network',					MetaCompany.ReleaseNew : 'Cartoon Network'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Cartoon Network',					MetaCompany.ReleaseNew : 'Cartoon Network'},
			},

			# Example: BET+
			'^bet[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BET',								MetaCompany.ReleaseNew : 'BET'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BET',								MetaCompany.ReleaseNew : 'BET'},
			},

			# Example: Vice TV (US)
			'^vice(?:$|[\s\-]*tv)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Viceland',							MetaCompany.ReleaseNew : 'Viceland'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Vice',								MetaCompany.ReleaseNew : 'Vice'},
			},

			# Example: MTV Studios
			'^mtv[\s\-]*studio' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'MTV Films',						MetaCompany.ReleaseNew : 'MTV Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'MTV Films',						MetaCompany.ReleaseNew : 'MTV Entertainment Studios'},
			},

			# Example: CBC Television
			# Example: CBC Gem
			'^cbc[\s\-]*(?:television|gem)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'CBC',								MetaCompany.ReleaseNew : 'CBC'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'CBC',								MetaCompany.ReleaseNew : 'CBC'},
			},

			# Example: ABC 1
			'^abc[\s\-]*(?:1|one)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ABC1',								MetaCompany.ReleaseNew : 'ABC1'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ABC1',								MetaCompany.ReleaseNew : 'ABC1'},
			},
			# Example: ABC 2
			'^abc[\s\-]*(?:2|two)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ABC2',								MetaCompany.ReleaseNew : 'ABC2'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ABC2',								MetaCompany.ReleaseNew : 'ABC2'},
			},
			# Example: ABC 3
			'^abc[\s\-]*(?:3|three)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ABC (AU)',							MetaCompany.ReleaseNew : 'ABC (AU)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ABC3',								MetaCompany.ReleaseNew : 'ABC3'},
			},
			# Example: ABC Kids
			# Example: ABC for Kids
			'^abc.*?kids' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ABC (AU)',							MetaCompany.ReleaseNew : 'ABC (AU)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ABC (AU)',							MetaCompany.ReleaseNew : 'ABC Kids'},
			},

			# Example: Global TV
			'^global[\s\-]*tv' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Global',							MetaCompany.ReleaseNew : 'Global'}, # "Global-TV" exists, but the logo is skewed.
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Global TV',						MetaCompany.ReleaseNew : 'Global TV'},
			},

			# Example: Science
			'^science$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Science Channel',					MetaCompany.ReleaseNew : 'Science Channel'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},

			# Example: TNT Sports
			'^tnt.*?sport' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TNT',								MetaCompany.ReleaseNew : 'TNT'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TNT',								MetaCompany.ReleaseNew : 'TNT'},
			},

			# Example: Hallmark+
			'^hallmark[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Hallmark Channel',					MetaCompany.ReleaseNew : 'Hallmark Channel'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Hallmark Channel',					MetaCompany.ReleaseNew : 'Hallmark Channel'},
			},
			# Example: Hallmark ...
			'^hallmark' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Hallmark Channel',					MetaCompany.ReleaseNew : 'Hallmark Channel'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None}, # Has other icons starting with "Hallmark".
			},

			# Example: Magnolia Network
			'^magnolia[\s\-]*network' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Magnolia',							MetaCompany.ReleaseNew : 'Magnolia'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Magnolia',							MetaCompany.ReleaseNew : 'Magnolia'},
			},

			# Example: Virgin TV
			'^virgin[\s\-]*(?:tv|media|1|one)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Virgin Media One',					MetaCompany.ReleaseNew : 'Virgin Media One'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None}, # Has a few other icons.
			},

			# Example: Twin Cities PBS
			'^twin[\s\-]*cities.*pbs' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'PBS Television',					MetaCompany.ReleaseNew : 'PBS Television'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'PBS Television',					MetaCompany.ReleaseNew : 'PBS Television'},
			},

			# Example: Stan.
			# Example: Stan Australia
			'^stan\.?(?:$|.*?(?:au(?:$|[^a-z])|australia))' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Stan',								MetaCompany.ReleaseNew : 'Stan'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Stan',								MetaCompany.ReleaseNew : 'Stan'},
			},

			# Example: RTL+
			'^rtl[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'RTL Television',					MetaCompany.ReleaseNew : 'RTL Television'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'RTL Television',					MetaCompany.ReleaseNew : 'RTL Television'},
			},

			# Example: VRT 1
			'^vrt[\s\-]*(?:[12]|one|two)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'VRT',								MetaCompany.ReleaseNew : 'VRT'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'VRT',								MetaCompany.ReleaseNew : None},
			},

			# Example: Canal+ Family
			'^canal[\s\-]*(?:\+|plus)[\s\-]*family' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Canal+',							MetaCompany.ReleaseNew : 'Canal+'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Canal+ Family',					MetaCompany.ReleaseNew : 'Canal+ Family'},
			},
			# Example: Canal+ HD
			'^canal[\s\-]*(?:\+|plus)[\s\-]*hd' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Canal+',							MetaCompany.ReleaseNew : 'Canal+'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Canal+ HD',						MetaCompany.ReleaseNew : 'Canal+ HD'},
			},
			# Example: Canal+ Polska
			'^canal[\s\-]*(?:\+|plus).*(?:[^a-z]pl[^a-z]|polska)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Canal+',							MetaCompany.ReleaseNew : 'Canal+'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Canal+',							MetaCompany.ReleaseNew : 'Canal+'},
			},

			# Example: RTÉ
			'^rt(?:É|é|e|É)$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'RTÉ',								MetaCompany.ReleaseNew : 'RTÉ'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'RTE',								MetaCompany.ReleaseNew : 'RTE'}, # RTÉ has white logo.
			},
			# Example: RTÉ One
			# Example: RTE One
			'^rt(?:É|é|e|É)[\s\-]*(?:1|one)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'RTÉ',								MetaCompany.ReleaseNew : 'RTÉ One'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'RTE One',							MetaCompany.ReleaseNew : 'RTÉ One'},
			},
			# Example: RTÉ Two
			# Example: RTE Two
			'^rt(?:É|é|e)[\s\-]*(?:2|two)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'RTÉ',								MetaCompany.ReleaseNew : 'RTÉ'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'RTE Two',							MetaCompany.ReleaseNew : 'RTÉ Two'},
			},
			# Example: RTÉjr
			'^rt(?:É|é|e)(?:$|[\s\-]*.+)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'RTÉ',								MetaCompany.ReleaseNew : 'RTÉ'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'RTE',								MetaCompany.ReleaseNew : 'RTE'},
			},

			# Example: TVNZ 1
			'^tv[\s\-]*nz[\s\-]*(?:1|one)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TVNZ1',							MetaCompany.ReleaseNew : 'TVNZ1'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TVNZ 1',							MetaCompany.ReleaseNew : 'TVNZ 1'},
			},
			# Example: TVNZ 2
			'^tv[\s\-]*nz[\s\-]*(?:2|two)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TVNZ2',							MetaCompany.ReleaseNew : 'TVNZ2'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TVNZ 2',							MetaCompany.ReleaseNew : 'TVNZ 2'},
			},
			# Example: TVNZ 3
			'^tv[\s\-]*nz[\s\-]*(?:3|three)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TV3 (NZ)',							MetaCompany.ReleaseNew : 'TV3 (NZ)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TVNZ',								MetaCompany.ReleaseNew : 'TV3 (NZ) Three'},
			},
			# Example: TVNZ+
			'^tv[\s\-]*nz[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TVNZ',								MetaCompany.ReleaseNew : 'TVNZ'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TVNZ+',							MetaCompany.ReleaseNew : 'TVNZ+'},
			},

			# Same as TVNZ1. Seems to use the old logo.
			# Example: TV1 (NZ) One
			'^tv[\s\-]*(?:1|one).*(?:nz|new[\s\-]*zealand)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TV One (NZ)',						MetaCompany.ReleaseNew : 'TV One (NZ)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TVNZ 1',							MetaCompany.ReleaseNew : 'TVNZ 1'},
			},
			# Same as TVNZ2. Seems to use the old logo.
			# Example: TV2 (NZ) Two
			'^tv[\s\-]*(?:2|two).*(?:nz|new[\s\-]*zealand)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TV2 (NZ)',							MetaCompany.ReleaseNew : 'TV2 (NZ)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TVNZ 2',							MetaCompany.ReleaseNew : 'TVNZ 2'},
			},
			# Same as TVNZ3. Seems to use the old logo.
			# Example: TV3 (NZ) Three
			'^tv[\s\-]*(?:3|three).*(?:nz|new[\s\-]*zealand)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TV3 (NZ)',							MetaCompany.ReleaseNew : 'TV3 (NZ)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TVNZ',								MetaCompany.ReleaseNew : 'TV3 (NZ) Three'},
			},

			# Example: BNNVARA
			'^bnn[\s\-]*vara' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BNN',								MetaCompany.ReleaseNew : 'BNN'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BNN',								MetaCompany.ReleaseNew : 'BNNVARA'},
			},

			# Example: KBS2
			'^kbs[\s\-]*\d' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'KBS',								MetaCompany.ReleaseNew : 'KBS'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'KBS',								MetaCompany.ReleaseNew : 'KBS'},
			},

			# Example: TV4 Plus
			'^tv[\s\-]*4[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TV4',								MetaCompany.ReleaseNew : 'TV4'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TV4 Plus',							MetaCompany.ReleaseNew : 'TV4 Plus'},
			},

			# Example: La 1
			'^la[\s\-]*(?:1|one)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TVE1, La 1',						MetaCompany.ReleaseNew : 'TVE1, La 1'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'La 1',								MetaCompany.ReleaseNew : 'La 1'},
			},
			# Example: La 2
			'^la[\s\-]*(?:2|two)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TVE2, La 2',						MetaCompany.ReleaseNew : 'TVE2, La 2'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'La 2',								MetaCompany.ReleaseNew : 'La 2'},
			},

			# Example: S4C
			'^s4c$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'S4C2',								MetaCompany.ReleaseNew : 'S4C2'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'S4C',								MetaCompany.ReleaseNew : 'S4C'},
			},

			# Owned by A&E
			# Example: Crime + Investigation
			'^crime[\s\-]*(?:and|\+|\&)[\s\-]*investigation' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'A&E',								MetaCompany.ReleaseNew : 'A&E'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Crime And Investigation',			MetaCompany.ReleaseNew : 'Crime And Investigation'},
			},

			# Example: Tubi
			'^tubi$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'Tubi TV'},
			},

			# Example: Videoland (NL)
			'^video[\s\-]*land$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'Videoland'},
			},

			# Example: TV2 (HU)
			'^tv[\s\-]*(?:2|two).*(?:[^a-z]hu(?:$|[^a-z])|hungary)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TV2',								MetaCompany.ReleaseNew : 'TV2'},
			},

			# Example: TV3 (ES)
			'^tv[\s\-]*(?:3|three).*(?:[^a-z]es(?:$|[^a-z])|spain|espa.ol)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TV3',								MetaCompany.ReleaseNew : 'TV3'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TV3',								MetaCompany.ReleaseNew : 'TV3'},
			},

			# Example: Premier (RU)
			# Example: TNT-Premier
			'^(?:premier(?:$|\s+)(?:ru(?:$|[^a-z])|russia)|tnt.?premier)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'Premier (Russia)'},
			},

			# Example: Star+
			'^star[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Star Plus',						MetaCompany.ReleaseNew : 'Star Plus'},
			},

			# Example: Drama
			'^drama$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'U&Drama'},
			},

			# Example: iQiyi
			'^iqiyi' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'IQIYI Pictures'},
			},

			# Example: SVT1
			'^svt[\s\-]*(?:1|one)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'SVT 1',							MetaCompany.ReleaseNew : 'SVT 1'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'SVT1',								MetaCompany.ReleaseNew : 'SVT1'},
			},
			# Example: SVT2
			'^svt[\s\-]*(?:2|two)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'SVT 2',							MetaCompany.ReleaseNew : 'SVT 2'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'SVT2',								MetaCompany.ReleaseNew : 'SVT2'},
			},

			# Example: RTP1
			'^rtp[\s\-]*(?:1|one)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'RTP',								MetaCompany.ReleaseNew : 'RTP1'},
			},
			# Example: RTP2
			'^rtp[\s\-]*(?:2|3|two|three)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'RTP',								MetaCompany.ReleaseNew : 'RTP'},
			},

			# Example: Network 10
			'^network[\s\-]*10$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Network Ten',						MetaCompany.ReleaseNew : 'Network Ten'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Network Ten',						MetaCompany.ReleaseNew : 'Network Ten'},
			},

			# Example: ESPN+
			'^espn[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ESPN',								MetaCompany.ReleaseNew : 'ESPN'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ESPN',								MetaCompany.ReleaseNew : 'ESPN'},
			},

			# Example: Atresplayer
			'^atres[\s\-]*player$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ATRESplayer Premium',				MetaCompany.ReleaseNew : 'ATRESplayer'},
			},

			# Example: Norsk Rikskringkasting (NRK)
			'^(?:norsk[\s\-]*rikskringkasting[\s\-]*[^\d]|nrk$)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'NRK1',								MetaCompany.ReleaseNew : 'NRK1'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'NRK HD',							MetaCompany.ReleaseNew : 'NRK HD'},
			},

			# Example: kykNet
			'^kyk[\s\-]*net' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'M-Net',							MetaCompany.ReleaseNew : 'M-Net'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},

			# Example: E.R.T.
			'^e\.r\.t\.' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ERT',								MetaCompany.ReleaseNew : 'ERT'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ERT Sat',							MetaCompany.ReleaseNew : 'ERT Sat'},
			},

			# Example: Prima+
			'^prima[\s\-]*(?:\+|plus|tv)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Prima TV',							MetaCompany.ReleaseNew : 'Prima TV'},
			},

			# Example: IRIB
			'^irib$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'IRIB TV 1',						MetaCompany.ReleaseNew : 'IRIB TV 1'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},

			# Example: Ciné+
			'^cin(?:e|é)[\s\-]*(?:\+|plus)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Cine+',							MetaCompany.ReleaseNew : 'Cine+'},
			},
			# Example: CinéCinéma
			'^cin(?:e|é)[\s\-]*cin(?:e|é)ma' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Cinecinema Club',					MetaCompany.ReleaseNew : 'Cinecinema Club'},
			},

			# Example: U&Dave
			'^u\s*(?:\&|\+|and)\s*dave' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Dave',								MetaCompany.ReleaseNew : 'Dave'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Dave',								MetaCompany.ReleaseNew : 'Dave'},
			},

			# Example: Audience
			'^audience$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Audience Network',					MetaCompany.ReleaseNew : 'Audience Network'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Audience',							MetaCompany.ReleaseNew : 'Audience'},
			},

			# Example: Turner Network Television
			'^turner[\s\-]*network' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Turner Network Television (TNT)',	MetaCompany.ReleaseNew : 'Turner Network Television (TNT)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Turner Network Television (TNT)',	MetaCompany.ReleaseNew : 'Turner Network Television (TNT)'},
			},

			# Example: NPO 1 HD
			'^(?:npo|nederland)[\s\-]*(?:1|one)[\s\-]*hd' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Nederland 1',						MetaCompany.ReleaseNew : 'Nederland 1'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Nederland 1 HD',					MetaCompany.ReleaseNew : 'Nederland 1 HD'},
			},
			# Example: NPO 1
			'^(?:npo|nederland)[\s\-]*(?:1|one)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Nederland 1',						MetaCompany.ReleaseNew : 'Nederland 1'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Nederland 1',						MetaCompany.ReleaseNew : 'Nederland 1'},
			},
			# Example: NPO 2 HD
			'^(?:npo|nederland)[\s\-]*(?:2|two)[\s\-]*hd' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Nederland 2',						MetaCompany.ReleaseNew : 'Nederland 2'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Nederland 2 HD',					MetaCompany.ReleaseNew : 'Nederland 2 HD'},
			},
			# Example: NPO 2
			'^(?:npo|nederland)[\s\-]*(?:2|two)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Nederland 2',						MetaCompany.ReleaseNew : 'Nederland 2'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Nederland 2',						MetaCompany.ReleaseNew : 'Nederland 2'},
			},
			# Example: NPO 3 HD
			'^(?:npo|nederland)[\s\-]*(?:3|three)[\s\-]*hd' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Nederland 3',						MetaCompany.ReleaseNew : 'Nederland 3'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Nederland 3 HD',					MetaCompany.ReleaseNew : 'Nederland 3 HD'},
			},
			# Example: NPO 3
			'^(?:npo|nederland)[\s\-]*(?:3|three)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Nederland 3',						MetaCompany.ReleaseNew : 'Nederland 3'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Nederland 3',						MetaCompany.ReleaseNew : 'Nederland 3'},
			},

			# Example: CCTV
			'^cctv$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'CCTV',								MetaCompany.ReleaseNew : 'CCTV'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'CCTV',								MetaCompany.ReleaseNew : 'CCTV'},
			},
			# Example: CCTV 4
			# Example: CCTV 9
			'^cctv[\s\-]*[49]' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'CCTV',								MetaCompany.ReleaseNew : 'CCTV'}, # Not available.
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None}, # Has multiple icons.
			},
			# Example: CCTV 8
			'^cctv[\s\-]*\d' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'CCTV',								MetaCompany.ReleaseNew : 'CCTV'}, # Not available.
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'CCTV F',							MetaCompany.ReleaseNew : 'CCTV F'},
			},

			# Example: RaiPlay
			'^rai[\s\-]*play' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'RAI',								MetaCompany.ReleaseNew : 'RAI'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'RAI',								MetaCompany.ReleaseNew : 'RAI'},
			},

			# Example: YTV (JP)
			'^ytv.*?(?:j[pa][^a-z]|japan)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'YTV',								MetaCompany.ReleaseNew : 'YTV (JP)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'YTV',								MetaCompany.ReleaseNew : 'YTV'},
			},

			# Added in mergeMetaCompany() for CBC (JP).
			# Example: Chubu-Nippon Broadcasting MetaCompany
			'^(?:cbc.*?(?:j[pa][^a-z]|japan)|chubu[\s\-]*nippon[\s\-]*broadcast)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'CBC (JP)',							MetaCompany.ReleaseNew : 'CBC (JP)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'Chubu-Nippon Broadcasting MetaCompany'},
			},

			# Example: Chiba TV
			'^(?:chiba[\s\-]*tv|ctc(?:$|.*?(?:j[pa][^a-z]|japan)))' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'CTC (JA)',							MetaCompany.ReleaseNew : 'CTC (JA)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'CTC',								MetaCompany.ReleaseNew : 'CTC'},
			},

			# The US also has an unrelated TBS channel.
			# Example: TBS (JP)
			'^(?:tbs|tokyo[\s\-]*broadcasting[\s\-]*system).*?(?:j[pa][^a-z]|japan)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Tokyo Broadcasting System',		MetaCompany.ReleaseNew : 'Tokyo Broadcasting System'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Tokyo Broadcasting System',		MetaCompany.ReleaseNew : 'Tokyo Broadcasting System'},
			},

			# Example: NHK WORLD-JAPAN
			'^nhk.*?world.*?(?:j[pa][^a-z]|japan)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'NHK World',						MetaCompany.ReleaseNew : 'NHK World'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'NHK World',						MetaCompany.ReleaseNew : 'NHK World'},
			},
			# Example: NHK BS Premium
			'^nhk.*(?:bs|premium)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'NHK',								MetaCompany.ReleaseNew : 'NHK'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'NHK',								MetaCompany.ReleaseNew : 'NHK'},
			},

			# Example: BS4
			'^bs[\s\-]*4$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Nippon TV',									MetaCompany.ReleaseNew : 'Nippon TV'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Nippon Television Network Corporation (NTV)',	MetaCompany.ReleaseNew : 'Nippon Television Network Corporation (NTV)'},
			},

			# Example: 20th Century
			'^(?:20th|twentieth)[\s\-]*century$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : '20th Century Fox',					MetaCompany.ReleaseNew : '20th Century Studios'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : '20th Century Fox',					MetaCompany.ReleaseNew : '20th Century Fox'},
			},
			# Example: Twentieth Television
			'^(?:20th|twentieth)[\s\-]*television$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Twentieth Television',				MetaCompany.ReleaseNew : 'Twentieth Television'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Twentieth Television',				MetaCompany.ReleaseNew : 'Twentieth Television'},
			},
			# Example: 20th Century Studios
			'^(?:20th|twentieth)[\s\-]*century[\s\-]*studio' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : '20th Century Fox Studios',			MetaCompany.ReleaseNew : '20th Century Studios'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : '20th Century Fox Studios',			MetaCompany.ReleaseNew : '20th Century Fox Studios'},
			},
			# Example: 20th Century Fox Studios
			'^(?:20th|twentieth)[\s\-]*century[\s\-]*fox[\s\-]*studio' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : '20th Century Fox Studios',			MetaCompany.ReleaseNew : '20th Century Fox Studios'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : '20th Century Fox Studios',			MetaCompany.ReleaseNew : '20th Century Fox Studios'},
			},
			# Example: Twentieth Century Fox Film
			'^(?:20th|twentieth)[\s\-]*century[\s\-]*fox[\s\-]*films?$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Twentieth Century Fox Film',		MetaCompany.ReleaseNew : 'Twentieth Century Fox Film'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Twentieth Century Fox Film',		MetaCompany.ReleaseNew : 'Twentieth Century Fox Film'},
			},
			# Example: 20th Century Fox Television
			'^(?:20th|twentieth)[\s\-]*fox[\s\-]*television$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : '20th Century Fox Television',		MetaCompany.ReleaseNew : '20th Century Fox Television'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : '20th Century Fox Television',		MetaCompany.ReleaseNew : '20th Century Fox Television'},
			},

			# Example: Sony Entertainment Television
			'^sony[\s\-]*entertainment[\s\-]*(?:tv|television)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sony Pictures Television',			MetaCompany.ReleaseNew : 'Sony Pictures Television'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sony Pictures Television',			MetaCompany.ReleaseNew : 'Sony Pictures Television'},
			},
			# Example: SonyLIV
			'^sony[\s\-]*liv' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sony Pictures Television International',	MetaCompany.ReleaseNew : 'Sony Pictures Television International'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sony TV Asia',								MetaCompany.ReleaseNew : 'Sony TV Asia'},
			},
			# Example: Sony Music
			'^sony[\s\-]*music' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sony',								MetaCompany.ReleaseNew : 'Sony'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sony',								MetaCompany.ReleaseNew : 'Sony'},
			},
			# Example: Sony Pictures International
			'^sony[\s\-]*pictures?[\s\-]*int' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sony Pictures Studios',			MetaCompany.ReleaseNew : 'Sony Pictures Studios'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sony Pictures Studios',			MetaCompany.ReleaseNew : 'Sony Pictures Studios'},
			},

			# Example: Warner Bros. Feature Animation
			'^warner[\s\-]*bros\.?[\s\-]*feature.*animation$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Warner Bros. Animation',			MetaCompany.ReleaseNew : 'Warner Bros. Animation'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Warner Bros. Animation',			MetaCompany.ReleaseNew : 'Warner Bros. Animation'},
			},
			# Example: Warner Bros. International Television Production Germany
			# Example: Warner Bros. ITVP Deutschland
			'^warner[\s\-]*bros\.?.*?(?:television|tv|itvp)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Warner Bros. Television',			MetaCompany.ReleaseNew : 'Warner Bros. Television'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Warner Bros. Television',			MetaCompany.ReleaseNew : 'Warner Bros. Television'},
			},
			# Example: Warner Horizon Unscripted Television
			'^warner.*?(?:horizon|television)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Warner Bros. Television',			MetaCompany.ReleaseNew : 'Warner Bros. Television'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Warner Bros. Television',			MetaCompany.ReleaseNew : 'Warner Bros. Television'},
			},
			# Example: Warner Bros.-Seven Arts
			'^warner[\s\-]*bros\.?.*?seven' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Warner Bros.',						MetaCompany.ReleaseNew : 'Warner Bros.'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Warner Bros.',						MetaCompany.ReleaseNew : 'Warner Bros.'},
			},
			# Example: Warner Bros. Family Entertainment.png
			'^warner[\s\-]*bros\.?[\s\-]*(?:family|entertainment)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Warner Bros. Entertainment',		MetaCompany.ReleaseNew : 'Warner Bros. Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Warner Bros. Entertainment',		MetaCompany.ReleaseNew : 'Warner Bros. Entertainment'},
			},
			# Example: Warner Bros. Japan
			'^warner[\s\-]*bros?\.?.*?(?:j[pa][^a-z]|japan)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Warner Bro. Japan',				MetaCompany.ReleaseNew : 'Warner Bro. Japan'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Warner Bros.',						MetaCompany.ReleaseNew : 'Warner Bros.'},
			},
			# Example: Warner Bros. Korea
			'^warner[\s\-]*bros?\.?.*?(?:[^a-z]kr[^a-z]|Korea)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Warner Bros.',						MetaCompany.ReleaseNew : 'Warner Bros.'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Warner Bros.',						MetaCompany.ReleaseNew : 'Warner Bros.'},
			},

			# Example: Searchlight Pictures
			'^searchlight[\s\-]*pictures?$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Searchlight',						MetaCompany.ReleaseNew : 'Searchlight'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Fox Searchlight Pictures',			MetaCompany.ReleaseNew : 'Searchlight Pictures'},
			},

			# Example: New Regency Productions
			'^new[\s\-]*regency[\s\-]*production' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'New Regency Pictures',				MetaCompany.ReleaseNew : 'New Regency Pictures'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'New Regency Productions',			MetaCompany.ReleaseNew : 'New Regency Productions'},
			},

			# Example: Paramount Famous Productions
			'^paramount[\s\-]*famous' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Paramount Pictures',				MetaCompany.ReleaseNew : 'Paramount Pictures'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Paramount Pictures',				MetaCompany.ReleaseNew : 'Paramount Pictures'},
			},

			# Example: DC Films
			'^dc[\s\-]*(?:film|studio|production)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'DC Entertainment',					MetaCompany.ReleaseNew : 'DC Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'DC Entertainment',					MetaCompany.ReleaseNew : None},
			},

			# Example: Spyglass Media Group
			'^spyglass[\s\-]*media' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Spyglass Entertainment',			MetaCompany.ReleaseNew : 'Spyglass Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Spyglass Media Group',				MetaCompany.ReleaseNew : 'Spyglass Media Group'},
			},

			# Example: Big Beach
			'^big[\s\-]*beach$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Big Beach Films',					MetaCompany.ReleaseNew : 'Big Beach Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Big Beach Productions',			MetaCompany.ReleaseNew : 'Big Beach Productions'},
			},

			# Example: TF1 Films Production
			# Example: TF1 International
			'^tf1[\s\-]*(?:film|studio|production|international)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'TF1 Films Productions',			MetaCompany.ReleaseNew : 'TF1 Films Productions'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'TF1 Films Production',				MetaCompany.ReleaseNew : 'TF1 Films Production'},
			},

			# Example: Marv
			'^marv$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Marv Films',						MetaCompany.ReleaseNew : 'Marv Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Marv Films',						MetaCompany.ReleaseNew : 'Marv Films'},
			},

			# Example: Maverick Film
			'^maverick[\s\-]*films?$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Maverick Films',					MetaCompany.ReleaseNew : 'Maverick Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Maverick Films',					MetaCompany.ReleaseNew : 'Maverick Films'},
			},

			# Example: Black Bear
			'^black[\s\-]*bear$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Black Bear Pictures',				MetaCompany.ReleaseNew : 'Black Bear Pictures'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Black Bear Pictures',				MetaCompany.ReleaseNew : 'Black Bear Pictures'},
			},

			# Example: Illumination
			'^illumination$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Illumination Entertainment',		MetaCompany.ReleaseNew : 'Illumination Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Illumination Entertainment',		MetaCompany.ReleaseNew : 'Illumination Entertainment'},
			},

			# Example: Media Rights Capital (MRC)
			'^media[\s\-]*rights[\s\-]*capital' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Media Rights Capital',				MetaCompany.ReleaseNew : 'Media Rights Capital'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Media Rights Capital',				MetaCompany.ReleaseNew : 'Media Rights Capital'},
			},

			# Example: El Dorado Pictures
			'^el[\s\-]*dorado$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'El Dorado Films',					MetaCompany.ReleaseNew : 'El Dorado Films'},
			},

			# "Pandora Films" (ending in an s) seems like a different studio.
			# Example: Pandora Film
			'^pandora[\s\-]*film$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Pandora Filmproduktion',			MetaCompany.ReleaseNew : 'Pandora Filmproduktion'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Pandora Film',						MetaCompany.ReleaseNew : 'Pandora Film'},
			},

			# Example: Python (Monty) Pictures Limited
			'^python.*?monty' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Python (Monty) Pictures Ltd',		MetaCompany.ReleaseNew : 'Python (Monty) Pictures Ltd'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Python (Monty) Pictures Limited',	MetaCompany.ReleaseNew : 'Python (Monty) Pictures Limited'},
			},

			# Example: Blumhouse Television
			'^blumhouse' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Blumhouse Productions',			MetaCompany.ReleaseNew : 'Blumhouse Productions'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Blumhouse Productions',			MetaCompany.ReleaseNew : 'Blumhouse Television'},
			},

			# Example: Big Talk Studios
			'^big[\s\-]*talk' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Big Talk Productions',				MetaCompany.ReleaseNew : 'Big Talk Productions'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Big Talk Productions',				MetaCompany.ReleaseNew : 'Big Talk Productions'},
			},

			# Example: Pacific Data Images
			'^pacific[\s\-]*data[\s\-]*image' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Pacific Data Images (PDI)',		MetaCompany.ReleaseNew : 'Pacific Data Images (PDI)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Pacific Data Images (PDI)',		MetaCompany.ReleaseNew : 'Pacific Data Images (PDI)'}, # Not available.
			},

			# Example: Double Dare You (DDY)
			'^(?:ddy$|double[\s\-]*dare[\s\-]*you)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Double Dare You Productions',		MetaCompany.ReleaseNew : 'Double Dare You Productions'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Double Dare You Productions',		MetaCompany.ReleaseNew : 'Double Dare You Productions'},
			},

			# Example: The Kennedy/Marshall MetaCompany
			'^(?:the[\s\-]*)?kennedy.*?marshall' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'The KennedyMarshall MetaCompany',		MetaCompany.ReleaseNew : 'The KennedyMarshall MetaCompany'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'The KennedyMarshall MetaCompany',		MetaCompany.ReleaseNew : 'The KennedyMarshall MetaCompany'},
			},

			# Example: Madhouse Entertainmet
			'^madhouse' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'MadHouse',							MetaCompany.ReleaseNew : 'MadHouse'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'MadHouse',							MetaCompany.ReleaseNew : 'MadHouse'},
			},

			# Example: 87North
			'^87\s*north' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : '87Eleven',							MetaCompany.ReleaseNew : '87Eleven'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : '87Eleven',							MetaCompany.ReleaseNew : '87 North Productions'},
			},

			# Example: Sierra / Affinity
			'^sierra[\s\-]*(?:\/|affinity|entertainment|picture)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Sierra Pictures',					MetaCompany.ReleaseNew : 'Sierra Pictures'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Sierra Entertainment‚ Inc.',		MetaCompany.ReleaseNew : 'Sierra Entertainment‚ Inc.'},
			},

			# Example: Legendary East
			'^legendary[\s\-]*east' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Legendary',						MetaCompany.ReleaseNew : 'Legendary'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Legendary',						MetaCompany.ReleaseNew : 'Legendary East'},
			},

			# Example: Univision Studios
			'^univision[\s\-]*studios?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Univision',						MetaCompany.ReleaseNew : 'Univision'},
			},

			# Example: Brooksfilms Ltd.
			'^brooks[\s\-]*films?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Brooksfilms',						MetaCompany.ReleaseNew : 'Brooksfilms'},
			},

			# Not sure if "Grand Illusion Films" and "Grand Illusions Entertainment" is the same company.
			# Example: Grand Illusion Films
			'^grand[\s\-]*illusion[\s\-]*films?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Grand Illusions Entertainment',	MetaCompany.ReleaseNew : 'Grand Illusions Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},

			# Example: Signature Films
			'^signature[\s\-]*films?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Signature Entertainment',			MetaCompany.ReleaseNew : 'Signature Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Signature Entertainment',			MetaCompany.ReleaseNew : 'Signature Films'},
			},

			# Example: LuckyChap
			'^lucky[\s\-]*chap' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'LuckyChap Entertainment',			MetaCompany.ReleaseNew : 'LuckyChap Entertainment'},
			},

			# Example: Sega Sammy Group
			'^sega(?:$|\s)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'SEGA Studios',						MetaCompany.ReleaseNew : 'SEGA Studios'},
			},

			# Example: 2AM
			'^2am' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : '2AM Films',						MetaCompany.ReleaseNew : '2AM Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : '2AM Films',						MetaCompany.ReleaseNew : '2AM Films'},
			},

			# Example: Beta Cinema
			'^beta[\s\-]*cinema' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Beta Film',						MetaCompany.ReleaseNew : 'Beta Film'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Beta Film GmbH',					MetaCompany.ReleaseNew : 'Beta Film GmbH'},
			},

			# Example: Tea Shop Productions
			'^tea[\s\-]*shop' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Tea Shop & Film MetaCompany',		MetaCompany.ReleaseNew : 'Tea Shop & Film MetaCompany'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},

			# Example: BFI Doc Society Fund
			'^(?:bfi|british[\s\-]*film[\s\-]*institute).*?fund' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'British Film Institute (BFI)',		MetaCompany.ReleaseNew : 'British Film Institute (BFI)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BFI Film Fund',					MetaCompany.ReleaseNew : 'BFI Film Fund'},
			},
			# Example: BFI
			'^(?:bfi(?:$|\s)|british[\s\-]*film[\s\-]*institute)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'British Film Institute (BFI)',		MetaCompany.ReleaseNew : 'British Film Institute (BFI)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BFI Film Fund',					MetaCompany.ReleaseNew : 'British Film Institute (BFI)'},
			},

			# Example: Wildside
			'^wildside$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'Wild Side'},
			},

			# Example: Cecchi Gori Group Tiger Cinematografica
			# Example: Mario e Vittorio Cecchi Gori - C.E.I.A.D.
			'cecchi[\s\-]*gori' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Cecchi Gori',						MetaCompany.ReleaseNew : 'Cecchi Gori'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Cecchi Gori',						MetaCompany.ReleaseNew : 'Cecchi Gori'},
			},

			# Example: Shochiku
			'^shochiku' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Shochiku MetaCompany',				MetaCompany.ReleaseNew : 'Shochiku MetaCompany'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Shochiku',							MetaCompany.ReleaseNew : 'Shochiku'},
			},

			# Example: Egg Film
			'^egg[\s\-]*films?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Egg Films',						MetaCompany.ReleaseNew : 'Egg Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Egg Films',						MetaCompany.ReleaseNew : 'Egg Films'},
			},

			# Example: Memento Films Production
			'^memento[\s\-]*films?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Memento Films',					MetaCompany.ReleaseNew : 'Memento Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Memento Films Production',			MetaCompany.ReleaseNew : 'Memento Films Production'},
			},

			# Example: Daiei
			# Example: Daiei Film
			# Example: Daiei Motion Picture Co., Ltd.
			'^daiei(?:$|[\s\-])' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'Daiei Film'},
			},

			# Example: Hemdale
			'^hemdale(?:$|[\s\-])' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Hemdale Film',						MetaCompany.ReleaseNew : 'Hemdale Film'},
			},

			# Example: Pacific Western
			'^pacific[\s\-]*western' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'Pacific Western Productions'},
			},

			# Example: Euro Film Funding
			'^euro[\s\-]*film' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Eurofilm Stúdió',					MetaCompany.ReleaseNew : 'Eurofilm Stúdió'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'Euro Film Funding'},
			},

			# "Svenska Filminstitutet" is a different studio.
			# Example: Svensk Filmindustri
			'^svensk[\s\-]*filmindu' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Svensk Filmindustri (SF)',			MetaCompany.ReleaseNew : 'Svensk Filmindustri (SF)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Svensk Filmindustri (SF)',			MetaCompany.ReleaseNew : 'Svensk Filmindustri (SF)'},
			},
			# Example: SF Studios
			'^svensk[\s\-]*filmindu' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Svensk Filmindustri (SF)',			MetaCompany.ReleaseNew : 'Svensk Filmindustri (SF)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'SF Studios',						MetaCompany.ReleaseNew : 'SF Studios'},
			},

			# Example: Samuel Goldwyn MetaCompany
			'^samuel[\s\-]*goldwyn' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Samuel Goldwyn',					MetaCompany.ReleaseNew : 'Samuel Goldwyn'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Samuel Goldwyn',					MetaCompany.ReleaseNew : 'Samuel Goldwyn'},
			},

			# Example: Falcon International Productions
			'^falcon' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Falcon Studios',					MetaCompany.ReleaseNew : 'Falcon Studios'},
			},

			# Example: Next Entertainment World (NEW)
			'^(?:new$|next[\s\-]*entertainment[\s\-]*world)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Next Entertainment World',			MetaCompany.ReleaseNew : 'Next Entertainment World'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Next Entertainment World',			MetaCompany.ReleaseNew : 'Next Entertainment World'},
			},

			# Example: Act III Productions
			'^act[\s\-]*(?:iii|3|three)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Act III Communications',			MetaCompany.ReleaseNew : 'Act III Communications'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Act III Communications',			MetaCompany.ReleaseNew : 'Act III Communications'},
			},

			# Example: Limelight
			'^lime[\s\-]*light' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Limelight International Media Entertainment',	MetaCompany.ReleaseNew : 'Limelight International Media Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Limelight International Media Entertainment',	MetaCompany.ReleaseNew : 'Limelight International Media Entertainment'},
			},

			# Example: Wolper Pictures
			'^wolper' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Wolper Pictures Ltd.',				MetaCompany.ReleaseNew : 'Wolper Pictures Ltd.'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'David L. Wolper Productions',		MetaCompany.ReleaseNew : 'David L. Wolper Productions'},
			},

			# Example: IFC Productions
			'^ifc(?:$|[\s\-]*(?:film|studio|production))' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'IFC Films',						MetaCompany.ReleaseNew : 'IFC Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'IFC Films',						MetaCompany.ReleaseNew : 'IFC Films'},
			},

			# Example: STX Films
			'^stx[\s\-]*film' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'STX Entertainment',				MetaCompany.ReleaseNew : 'STX Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'STX Films',						MetaCompany.ReleaseNew : 'STX Films'},
			},
			'^stx(?:$|\s)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'STX Entertainment',				MetaCompany.ReleaseNew : 'STX Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'STX Entertainment',				MetaCompany.ReleaseNew : 'STX Entertainment'},
			},

			# Example: The De Laurentiis MetaCompany
			'^(?:the[\s\-]*)?de[\s\-]*laurentiis' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'De Laurentiis',					MetaCompany.ReleaseNew : 'De Laurentiis'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'De Laurentiis',					MetaCompany.ReleaseNew : 'De Laurentiis'},
			},

			# Example: ABS-CBN Film Productions
			# Example: ABS-CBN Studios
			'^abs[\s\-]*cbn' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ABS-CBN Entertainment',			MetaCompany.ReleaseNew : 'ABS-CBN Entertainment'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ABS-CBN Entertainment',			MetaCompany.ReleaseNew : 'ABS-CBN Entertainment'},
			},

			# Example: Trésor Films
			'^tr(?:é|e)sor[\s\-]*film' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Trésor Films',						MetaCompany.ReleaseNew : 'Trésor Films'},
			},

			# Example: OddLot Entertainment
			'^odd[\s\-]*lot' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Oddlot',							MetaCompany.ReleaseNew : 'Oddlot'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Oddlot',							MetaCompany.ReleaseNew : 'Oddlot'},
			},

			# Example: Edko Films
			'^edko[\s\-]*films?' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Edko Film',						MetaCompany.ReleaseNew : 'Edko Film'},
			},

			# Example: China Film Co-Production Corp.
			'^china[\s\-]*film' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'China Film Group Corporation',		MetaCompany.ReleaseNew : 'China Film Group Corporation'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'China Film Group Corporation',		MetaCompany.ReleaseNew : 'China Film Group Corporation'},
			},

			# Example: Beijing New Picture Film Co. Ltd.
			'^beijing[\s\-]*new[\s\-]*picture' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Beijing New Picture Film Co.',		MetaCompany.ReleaseNew : 'Beijing New Picture Film Co.'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},

			# "Zazen Produções" in the addon, but for some reason does not load. However, "Zazen Produçoes" does load.
			# Example: Zazen Produções
			'^zazen(?:$|\s)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Zazen Produçoes',					MetaCompany.ReleaseNew : 'Zazen Produçoes'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Zazen Produçoes',					MetaCompany.ReleaseNew : 'Zazen Produçoes'},
			},

			# Example: Tribeca Productions
			'^tribeca' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Tribeca Film',						MetaCompany.ReleaseNew : 'Tribeca Film'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Tribeca Productions',				MetaCompany.ReleaseNew : 'Tribeca Productions'},
			},

			# Example: Absolute Entertainment
			'^absolute(?:$|[\s\-]*entertainment)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Absolute',							MetaCompany.ReleaseNew : 'Absolute'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Absolute Entertainment‚ Inc.',		MetaCompany.ReleaseNew : 'Absolute Entertainment‚ Inc.'},
			},

			# Not sure if "Parallel Films" and "Parallel Film Productions" are the same studio.
			# Example: Parallel Films
			'^parallel[\s\-]*film' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Parallel Film Productions',		MetaCompany.ReleaseNew : 'Parallel Film Productions'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Parallel Film Productions',		MetaCompany.ReleaseNew : 'Parallel Film Productions'},
			},

			# Example: Oscilloscope
			'^oscilloscope' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Oscilloscope Laboratories',		MetaCompany.ReleaseNew : 'Oscilloscope Laboratories'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Oscilloscope Laboratories',		MetaCompany.ReleaseNew : 'Oscilloscope Laboratories'},
			},

			# Example: Chiodo Bros. Production
			'^chiodo[\s\-]*bro' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Chiodo Brothers Productions',		MetaCompany.ReleaseNew : 'Chiodo Brothers Productions'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},

			# Example: Decla Film Gesellschaft Holz & Co.
			'^decla(?:$|[\s\-])' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,									MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Decla-Film-Gesellschaft Holz & Co.',	MetaCompany.ReleaseNew : 'Decla-Film-Gesellschaft Holz & Co.'},
			},

			# Example: Altitude Film Entertainment
			'^altitude(?:$|[\s\-]*film)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Altitude',							MetaCompany.ReleaseNew : 'Altitude'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Altitude Film Entertainment',		MetaCompany.ReleaseNew : 'Altitude Film Entertainment'},
			},

			# Example: Matchbox Pictures
			'^matchbox(?:$|[\s\-]*(?:film|picture|studio))' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : 'Matchbox Films'},
			},

			# Example: Viacom18 Studios
			'^viacom[\s\-]*18' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Viacom18 Motion Pictures',			MetaCompany.ReleaseNew : 'Viacom18 Motion Pictures'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Viacom18 Motion Pictures',			MetaCompany.ReleaseNew : 'Viacom18 Motion Pictures'},
			},

			# Example: Huayi Tencent Entertainment
			'^huayi(?:$|[\s\-])' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Huayi Brothers',					MetaCompany.ReleaseNew : 'Huayi Brothers'},
			},

			# Example: Arcadia Motion Pictures
			'^arcadia(?:$|[\s\-]*(?:motion|picture))' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Arcadia',							MetaCompany.ReleaseNew : 'Arcadia'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : None,								MetaCompany.ReleaseNew : None},
			},

			# Example: Goldcrest
			'^goldcrest' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Goldcrest Films',					MetaCompany.ReleaseNew : 'Goldcrest Films'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Goldcrest',						MetaCompany.ReleaseNew : 'Goldcrest'},
			},

			# Example: Instituto Nacional de Cine y Artes Audiovisuales
			# Example: INCAA
			'^(?:incaa$|instituto[\s\-]*nacional.*?audiovisuales)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Instituto Nacional De Cine Y Artes Audiovisuales (INCAA)',	MetaCompany.ReleaseNew : 'Instituto Nacional De Cine Y Artes Audiovisuales (INCAA)'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Instituto Nacional De Cine Y Artes Audiovisuales (INCAA)',	MetaCompany.ReleaseNew : 'Instituto Nacional De Cine Y Artes Audiovisuales (INCAA)'},
			},

			# More info below at "syndication".
			# Example: Syndicated
			'^syndicat(?:ion|or|ing|ed)s?$' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Syndicated',						MetaCompany.ReleaseNew : 'Syndicated'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'Syndicated',						MetaCompany.ReleaseNew : 'Syndicated'},
			},

			# Example: Erstes Deutsches Fernsehen
			'^erstes?[\s\-]*deutsches[\s\-]*fernsehen' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ARD',								MetaCompany.ReleaseNew : 'ARD'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ARD',								MetaCompany.ReleaseNew : 'ARD'},
			},
			# Example: ARD/Degeto Film vs ARD Degeto
			'^ard.*degeto' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ARD',								MetaCompany.ReleaseNew : 'ARD'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ARD',								MetaCompany.ReleaseNew : 'ARD'},
			},
			# Example: Zweites Deutsches Fernsehen
			'^zweites?[\s\-]*deutsches[\s\-]*fernsehen' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'ZDF',								MetaCompany.ReleaseNew : 'ZDF'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'ZDF',								MetaCompany.ReleaseNew : 'ZDF'},
			},
			# Example: Norddeutscher Rundfunk
			'^norddeutscher[\s\-]*rundfunk' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'NDR',								MetaCompany.ReleaseNew : 'NDR'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'NDR Fernsehen',					MetaCompany.ReleaseNew : 'NDR Fernsehen'},
			},
			# Example: Westdeutscher Rundfunk
			'^westdeutscher[\s\-]*rundfunk' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'WDR',								MetaCompany.ReleaseNew : 'WDR'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'WDR',								MetaCompany.ReleaseNew : 'WDR'},
			},

			# Example: Mitteldeutscher Rundfunk
			'^mitteldeutscher[\s\-]*rundfunk' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'MDR',								MetaCompany.ReleaseNew : 'MDR'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'MDR Fernsehen',					MetaCompany.ReleaseNew : 'MDR Fernsehen'},
			},
			# Example: Bayerischer Rundfunk
			'^bayerischer[\s\-]*rundfunk' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'BR',								MetaCompany.ReleaseNew : 'BR'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'BR',								MetaCompany.ReleaseNew : 'BR'},
			},
			# Example: Hessischer Rundfunk
			'^hessischer[\s\-]*rundfunk' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'Hessischer Rundfunk',				MetaCompany.ReleaseNew : 'Hessischer Rundfunk'}, # HDR not available.
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'HR-Fernsehen',						MetaCompany.ReleaseNew : 'HR-Fernsehen'},
			},
			# Example: Südwestrundfunk
			# Example: SWR Fernsehen
			'^(?:südwestrundfunk|swr[\s\-]*fernsehen)' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'SWR',								MetaCompany.ReleaseNew : 'SWR'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'SWR Fernsehen BW',					MetaCompany.ReleaseNew : 'SWR Fernsehen BW'}, # SWR not available.
			},
			# Example: RBB Brandenburg
			'^rbb(?:$|[\s\-]*(?:brandenburg|berlin))' : {
				MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'RBB',								MetaCompany.ReleaseNew : 'RBB'},
				MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'RBB Brandenburg',					MetaCompany.ReleaseNew : 'RBB Brandenburg'},
			},
			# Example: Süddeutscher Rundfunk
			#'^süddeutscher[\s\-]*rundfunk' : {
			#	MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'SDR',								MetaCompany.ReleaseNew : 'SDR'}, # Not available.
			#	MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'SDR',								MetaCompany.ReleaseNew : 'SDR'}, # Not available.
			#},
			# Example: Nordwestdeutscher Rundfunk
			#'^nordwestdeutscher[\s\-]*rundfunk' : {
			#	MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'WDR',								MetaCompany.ReleaseNew : 'WDR'}, # NWDR not available.
			#	MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'WDR',								MetaCompany.ReleaseNew : 'WDR'}, # NWDR not available.
			#},
			# Example: Südwestfunk
			#'^südwestfunk' : {
			#	MetaCompany.TypeWhite	: {MetaCompany.ReleaseOld : 'SWF',								MetaCompany.ReleaseNew : 'SWF'}, # SWF not available.
			#	MetaCompany.TypeColor	: {MetaCompany.ReleaseOld : 'SWF',								MetaCompany.ReleaseNew : 'SWF'}, # SWF not available.
			#},
		}

		# Pick the replacements based on the icon addon type and release.
		replacement = {}
		for k, v in base.items():
			value = v
			if Tools.isDictionary(value): value = value.get(type)
			if Tools.isDictionary(value): value = value.get(release)

			# Allow None, to stop early when a match was found.
			#if value: replacement[k] = value
			if Tools.isString(value) or not value: replacement[k] = value
		return replacement

	###################################################################
	# SETTINGS
	###################################################################

	@classmethod
	def settingsMode(self):
		if Settings.getBoolean(MetaCompany.SettingEnabled):
			label = Settings.getString(MetaCompany.SettingCompany)
			mode = self._settingsConvert(label = label)
			return mode if mode else MetaCompany.ModeAutomatic
		else:
			return MetaCompany.ModeDisabled

	@classmethod
	def settingsWizard(self):
		title = 33360
		choice = Dialog.options(title = title, message = 36734, labelConfirm = 35102, labelDeny = 33743, labelCustom = 33736, default = Dialog.ChoiceCustom)
		if choice == Dialog.ChoiceCustom:
			return [MetaCompany.IdWhite]
		elif choice == Dialog.ChoiceYes:
			items = [
				{'label' : 33239, 'description' : 36735, 'action' : self.help},
				{'label' : 36731, 'description' : 36736, 'action' : [MetaCompany.IdWhite]},
				{'label' : 35468, 'description' : 36737, 'action' : [MetaCompany.IdColor]},
				{'label' : 33124, 'description' : 36738, 'action' : [MetaCompany.IdWhite, MetaCompany.IdColor]},
			]
			while True:
				choice = Dialog.select(title = title, items = ['%s: %s' % (Format.fontBold(item['label']), Translation.string(item['description'])) for item in items])
				if choice >= 0:
					choice = items[choice]
					action = choice['action']
					if Tools.isArray(action): return action
					else: action()
				else: break
		return None

	@classmethod
	def settingsSelect(self, settings = False):
		title = 33360
		texture = 'Textures.xbt'
		extension = '.' + System.name().lower()

		restart = False
		close = False
		while not close:
			choice = Dialog.options(title = title, message = 36748, labelConfirm = 33239, labelDeny = 33743, labelCustom = 33821, default = Dialog.ChoiceCustom)
			if choice == Dialog.ChoiceCustom:
				items = [
					{'mode' : MetaCompany.ModeDisabled, 'description' : 36741},
					{'mode' : MetaCompany.ModeSingle, 'description' : 36742},
					{'mode' : MetaCompany.ModeMultiple, 'description' : 36750},
					{'mode' : MetaCompany.ModeAutomatic, 'description' : 36743},
					{'mode' : MetaCompany.ModeWhite, 'description' : 36744},
					{'mode' : MetaCompany.ModeColor, 'description' : 36745},
					{'mode' : MetaCompany.ModeForceWhite, 'description' : 36746},
					{'mode' : MetaCompany.ModeForceColor, 'description' : 36747},
				]
				for item in items:
					item['label'] = self._settingsConvert(mode = item['mode'])

				while not close:
					choice = Dialog.select(title = title, items = ['%s: %s' % (Format.fontBold(item['label']), Translation.string(item['description'])) for item in items])
					if choice >= 0:
						choice = items[choice]
						mode = choice['mode']

						allow = True
						if mode in (MetaCompany.ModeForceWhite, MetaCompany.ModeForceColor):
							# Create a copy for both addons.
							# Otherwise if the user switches between ModeForceWhite and ModeForceColor, it might use the replaced texture instead of the original texture.
							for id in MetaCompany.Ids:
								addon = System.path(id = id)
								path = File.joinPath(addon, 'resources', texture + extension)
								if not File.exists(path): File.copy(pathFrom = File.joinPath(addon, 'resources', texture), pathTo = path)

							addon = System.path(MetaCompany.IdColor if mode == MetaCompany.ModeForceWhite else MetaCompany.IdWhite)
							pathCurrent = File.joinPath(addon, 'resources', texture)
							pathOriginal = File.joinPath(addon, 'resources', texture + extension)
							addon = System.path(MetaCompany.IdWhite if mode == MetaCompany.ModeForceWhite else MetaCompany.IdColor)
							pathReplace = File.joinPath(addon, 'resources', texture + extension)

							while True:
								labelWhite = self._settingsConvert(mode = MetaCompany.ModeWhite)
								labelColor = self._settingsConvert(mode = MetaCompany.ModeColor)
								message = Translation.string(36739) % ((labelColor, labelWhite) if mode == MetaCompany.ModeForceWhite else (labelWhite, labelColor))
								choice2 = Dialog.options(title = title, message = message, labelConfirm = 33239, labelDeny = 35479, labelCustom = 33726, default = Dialog.ChoiceCustom)
								if choice2 == Dialog.ChoiceCustom:
									allow = True
									break
								elif choice2 == Dialog.ChoiceYes:
									self._settingsHelp()
								else:
									if not choice2 == Dialog.ChoiceCanceled:
										if File.exists(pathOriginal):
											File.copy(pathFrom = pathOriginal, pathTo = pathCurrent, overwrite = True)
										if self._settingsConvert(label = Settings.getString(id = MetaCompany.SettingCompany)) in (MetaCompany.ModeForceWhite, MetaCompany.ModeForceColor):
											Settings.default(id = MetaCompany.SettingCompany)

										choice2 = Dialog.option(title = title, message = 36740, labelConfirm = 32501, labelDeny = 35015, default = Dialog.ChoiceYes)
										if choice2 == Dialog.ChoiceYes: restart = True

									close = True
									allow = False
									break

						if allow:
							# Install the required addons.
							ids = []
							if mode in (MetaCompany.ModeWhite, MetaCompany.ModeForceWhite, MetaCompany.ModeForceColor): ids.append(MetaCompany.IdWhite)
							if mode in (MetaCompany.ModeColor, MetaCompany.ModeForceWhite, MetaCompany.ModeForceColor): ids.append(MetaCompany.IdColor)
							for id in ids:
								if not Extension.installed(id = id, enabled = True):
									Extension.enable(id = id)

							# Do not continue if the addon installation was aborted.
							if not ids or all(Extension.installed(id = id, enabled = True) for id in ids):
								if mode in (MetaCompany.ModeForceWhite, MetaCompany.ModeForceColor) and File.exists(pathReplace):
									File.copy(pathFrom = pathReplace, pathTo = pathCurrent, overwrite = True)
									choice2 = Dialog.option(title = title, message = 36740, labelConfirm = 32501, labelDeny = 35015, default = Dialog.ChoiceYes)
									if choice2 == Dialog.ChoiceYes: restart = True

								Settings.set(id = MetaCompany.SettingCompany, value = choice['label'])
								close = True
								break

					else:
						close = True
						break

			elif choice == Dialog.ChoiceYes:
				self._settingsHelp()
			else:
				close = True
				break

		if restart: System.power(action = System.PowerRestart, warning = False) # System.PowerReload does not seem to reload the textures.
		elif settings: Settings.launch(id = MetaCompany.SettingCompany)

	@classmethod
	def _settingsHelp(self):
		Dialog.details(title = 33360, items = [
			{'type' : 'title', 'value' : 'Studio Icons', 'break' : 2},
			{'type' : 'text', 'value' : 'Studio Icons is a third-party addon that adds icons for studios and networks to menus. Not all Kodi skins support these icons.', 'break' : 2},

			{'type' : 'subtitle', 'value' : 'Color Palettes', 'break' : 2},
			{'type' : 'text', 'value' : 'There are two different studio icon addons, one with a white and one with a colored palette.'},
			{'type' : 'list', 'number' : False, 'value' : [
				{'title' : 'White Icons', 'value' : 'Supported by more skins. Fits aesthetically better in with more skins, since color palettes are more uniform. Contains less than half the number of icons compared to the colored ones.'},
				{'title' : 'Color Icons', 'value' : 'Supported by less skins. Might not fit aesthetically in with some skins, since color palettes might clash. Contains more than twice the number of icons compared to the white ones.'},
			]},

			{'type' : 'subtitle', 'value' : 'Kodi Skins', 'break' : 2},
			{'type' : 'text', 'value' : 'Whether studio icons are displayed or not depends on your Kodi skin. Many skins support the white icons, but few support the colored icons. Some skins might also display the studios as a label instead of using the icons.', 'break' : 2},
			{'type' : 'text', 'value' : 'Some skins support both palettes and have a skin setting allowing you to switch between them. Even if your skin does not support one of the palettes, you can still use them by applying one of the [I]Force[/I]  settings discussed below.'},

			{'type' : 'subtitle', 'value' : 'Addon Versions', 'break' : 2},
			{'type' : 'text', 'value' : 'The Studio Icons addon has not been updated on the official Kodi repository in years. The addon developers have updated versions on their GitHub, but they have not been pushed to the official repositories yet.', 'break' : 2},
			{'type' : 'text', 'value' : 'There are up-to-date versions of these addons in the Gaia [I]Full[/I]  repository, marked as [I]alpha[/I]  versions. Both the updated version and the older official version of the addon will work. The older version just has considerably fewer icons, including those for major new streaming services.'},

			{'type' : 'subtitle', 'value' : 'Icon Settings', 'break' : 2},
			{'type' : 'text', 'value' : 'The different addons, white and colored, new and old, have inconsistencies in their studio names, which makes many icons not show up. Gaia applies various optimizations and adjusts the names to make more icons show. It is therefore important to use the correct setting to get more icons to show.', 'break' : 2},
			{'type' : 'list', 'number' : False, 'value' : [
				{'title' : 'Disabled', 'value' : 'Removes the studio attribute to hide icons completely. The studio attribute will also be unavailable in other places, like the info dialog. If you just want to hide the icons without removing the studio attribute, check if your skin has a setting for that, or disable the Studio Icons addon.'},
				{'title' : 'Single', 'value' : 'Does not adjust the studio names in any way and is therefore not suited if icons are used. Only a single studio is listed if multiple ones are available. This option is useful for skins that do not use icons, but instead display the studio as a label. Using a single studio name keeps the label short.'},
				{'title' : 'Multiple', 'value' : 'Does not adjust the studio names in any way and is therefore not suited if icons are used. Keeps all available studios. This option is useful for skins that do not use icons or labels for studios, but you still want to keep all studio names.'},
				{'title' : 'Automatic', 'value' : 'Attempts to detect which Studio Icons addon the skin is using and applies optimizations accordingly. Since many skins do not explicitly list the Studio Icons addon as a dependency, this might not always work optimally. Rather pick one of the options below for better results.'},
				{'title' : 'White', 'value' : 'Adjusts studio names to work optimally with the white Studio Icons addon. Only a single studio is listed if multiple ones are available. This option should be used if the white Studio Icons addon is installed and used by your skin.'},
				{'title' : 'Color', 'value' : 'Adjusts studio names to work optimally with the colored Studio Icons addon. Only a single studio is listed if multiple ones are available. This option should be used if the colored Studio Icons addon is installed and used by your skin.'},
				{'title' : 'Force White', 'value' : 'This option is useful if your skin only supports colored icons, but you want to use white icons. Both the white and colored Studio Icons addon must be installed. The texture file of the colored addon will be replaced with the textures of the white addon. This applies globally in Kodi, so all other addons and menus will also use the replaced white textures. The textures can be reset back to the original.'},
				{'title' : 'Force Color', 'value' : 'This option is useful if your skin only supports white icons, but you want to use colored icons. Both the white and colored Studio Icons addon must be installed. The texture file of the white addon will be replaced with the textures of the colored addon. This applies globally in Kodi, so all other addons and menus will also use the replaced colored textures. The textures can be reset back to the original.'},
			]},
		])

	@classmethod
	def _settingsConvert(self, mode = None, label = None):
		modes = {
			MetaCompany.ModeDisabled	: 33022,
			MetaCompany.ModeSingle		: 35224,
			MetaCompany.ModeMultiple	: 36749,
			MetaCompany.ModeAutomatic	: 33800,
			MetaCompany.ModeWhite		: 36731,
			MetaCompany.ModeColor		: 35468,
			MetaCompany.ModeForceWhite	: 36732,
			MetaCompany.ModeForceColor	: 36733,
		}
		if mode:
			label = modes.get(mode)
			if label: return Translation.string(label)
		elif label:
			label = Translation.string(label).lower()
			for k, v in modes.items():
				if label == Translation.string(v).lower(): return k
		return None
