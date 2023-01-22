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

class Sets(object):

	pass
