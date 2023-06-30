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

from lib.modules.tools import System, Settings, Lightpack
from lib.modules.interface import Context
from lib.modules.library import Library
from lib.modules.vpn import Vpn
from lib.modules.bluetooth import Bluetooth
from lib.modules.cache import Cache
from lib.modules.concurrency import Pool
from lib.modules.external import Importer, Loader

# Reset possible old modules after the addon was updated.
# Otherwise after upgrade, Gaia throws errors about copied modules under the __gaia__ directory.
Importer.reset()
Loader.reset()

# Reset launch data to force Gaia to fully launch after the addon was upgraded.
System.launchDataClear(full = True)

# Reload here if the invoker settings changed after upgrading Gaia.
# This will cause Kodi to freeze for a bit.
# Once reloaded, Kodi will restart all services, so this script will be called again.
if not Settings.interpreterSelect(notification = True, silent = True):

	# Remove Old Settings
	# Do here instead of during the addon launch, since this function can fail and also takes very long.
	# The function is also more likley to work correctly here, since there are less threads writing to settings.
	Settings.clean()

	# Initialize Gaia during Kodi boot.
	if Settings.getBool('general.launch.acceleration'): System.launch(hidden = True)

	# VPN
	Vpn.monitor(silent = True)

	# Local Library Update
	Library.service()

	# Context Menu
	Context.initialize()

	# Bluetooth Monitor
	Bluetooth.service()

	# Launch Lightpack
	Lightpack().launchAutomatic()

	# Launch Gaia
	System.launchAutomatic()

	# Wait for threads.
	Pool.join()

	# Do this at the end, so that timestamps of reloaded requests can be updated and won't be deleted.
	# Do this after the thread pool joining, since the cache might still have threads executing (refreshing data in the background).
	Cache.instance().limitClear(log = False)
