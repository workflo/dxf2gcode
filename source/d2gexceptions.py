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

user defined exceptions

Michael Haberler  20.12.2009
'''

class BadConfigFileError(SyntaxError):
    """
    syntax error in .cfg file
    """
    def __init__(self, value):
        print "bin hier"
        self.value = value
    def __str__(self):
        return repr(self.value)
    
class VersionMismatchError(Exception):
    """
    version mismatch in .cfg file
    """
    def __init__(self,  fileversion, CONFIG_VERSION):
        self.fileversion = fileversion
        self.CONFIG_VERSION = CONFIG_VERSION
    def __str__(self):
        return repr(self.tr('config file versions do not match - internal: %s,'
                            ' config file %s, delete existing file to resolve issue'
                            %(self.CONFIG_VERSION, self.fileversion)))

class OptionError(SyntaxError):
    """
    conflicting command line option
    """

class PluginError(SyntaxError):
    """
    something went wrong during plugin loading or initialization
    """