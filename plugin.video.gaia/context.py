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

import xbmcaddon
developer = xbmcaddon.Addon().getAddonInfo('version') == '999.999.999'
if developer:
	import time as timer
	timeStart = timer.time()

from lib.modules.tools import Logger
if developer: Logger.log('EXECUTION STARTED [Action: %s]' % 'Context')

try:
	from lib.modules.interface import Context
	Context.create()
except: Logger.error()

if developer: Logger.log('EXECUTION FINISHING [Action: %s | Duration: %.3f secs]' % ('Context', timer.time() - timeStart))

from lib.modules.concurrency import Pool
Pool.join()

# Do this at the end, so that timestamps of reloaded requests can be updated and won't be deleted.
# Do this after the thread pool joining, since the cache might still have threads executing (refreshing data in the background).
from lib.modules.cache import Cache
Cache.instance().limitClear(log = developer)

if developer: Logger.log('EXECUTION FINISHED [Action: %s | Duration: %.3f secs]' % ('Context', timer.time() - timeStart))
