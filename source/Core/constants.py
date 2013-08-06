# -*- coding: iso-8859-15 -*-
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

'''
All global constants are initialized in this module.
They are used in the other modules.

see http://code.activestate.com/recipes/65207/ for module const

@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose:  initialization of the global constants used within the other modules.
@author: Christian Kohlöffel
@since:  21.12.2010
@license: GPL
'''

import logging

# Global Variables
APPNAME = "dxf2gcode"
VERSION = "pyQT Beta"


DATE =       "$Date:: 2013-07-24 20:22:16#$:"
REVISION =   "$Rev:: 377                  $:"
AUTHOR=      "$Author:: Christian KohlÃ¶ffel             $:"

CONFIG_EXTENSION = '.cfg'
PY_EXTENSION = '.py'

#Rename unreadable config/varspace files to .bad
BAD_CONFIG_EXTENSION = '.bad'
DEFAULT_CONFIG_DIR = 'config'
DEFAULT_POSTPRO_DIR = 'postpro_config'

# log related
DEFAULT_LOGFILE = 'dxf2gcode.log'
STARTUP_LOGLEVEL = logging.DEBUG
#PRT = logging.INFO

