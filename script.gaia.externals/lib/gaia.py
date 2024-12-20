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

# To call these functions from sub-modules:
#       from importlib import import_module # GAIACODE
#       command = getattr(import_module('gaia'), 'gaiaCommand')(command) # GAIACODE
# Or:
#       from importlib import import_module # GAIACODE
#       gaiaCommand = getattr(import_module('gaia'), 'gaiaCommand') # GAIACODE
#       gaiaCommand(command) # GAIACODE

GaiaEnvironment = None

def gaiaEnvironment():
    global GaiaEnvironment
    if GaiaEnvironment is None:
        from importlib import import_module
        GaiaEnvironment = getattr(import_module('lib.modules.environment'), 'Environment')
    return GaiaEnvironment

def gaiaCommand(command):
    try:
        command = gaiaEnvironment().command(command)
    except Exception as error:
        import xbmc
        xbmc.log('Gaia external command error (script.gaia.externals): ' + str(error), xbmc.LOGERROR)
    return command
