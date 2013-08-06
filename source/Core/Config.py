# -*- coding: iso-8859-1 -*-
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
"""
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose:  TBD

@author: Christian Kohlöffel
@since:  26.12.2009
@license: GPL
"""

import os

from Core.configobj import ConfigObj,flatten_errors
from Core.validate import Validator

#from dotdictlookup import DictDotLookup
import time
import pprint

import Core.constants as c
import Core.Globals as g
from d2gexceptions import *

from PyQt4 import QtCore

import logging
logger = logging.getLogger("Core.Config")

CONFIG_VERSION = "5"
"""
version tag - increment this each time you edit CONFIG_SPEC

compared to version number in config file so
old versions are recognized and skipped"
"""

CONFIG_SPEC = str('''
#  Section and variable names must be valid Python identifiers
#      do not use whitespace in names

# do not edit the following section name:
    [Version]

    # do not edit the following value:
    config_version = string(default="'''  + \
    str(CONFIG_VERSION) + '")\n' + \
'''
    [Paths]
    # 
    # look here for DXF files
    import_dir = string(default="D:/Eclipse_Workspace/DXF2GCODE/trunk/dxf")
    
    # store gcode output here 
    output_dir = string(default="D:")
    
    
    [Depth_Coordinates]
    axis3_retract = float(default= 15.0)
    axis3_slice_depth = float(default= -1.5)
    axis3_safe_margin = float(default= 3.0)
    axis3_start_mill_depth = float(default= 0.0)
    axis3_mill_depth = float(default= -3.0)
    
    [Axis_letters]
    ax1_letter = string(default="X")
    ax2_letter = string(default="Y")
    ax3_letter = string(default="Z")
    
    [Plane_Coordinates]
    axis1_start_end = float(default= 0)
    axis2_start_end = float(default= 0)
    
    [General]
    write_to_stdout = boolean(default=False)
    live_update_export_route = boolean(default=False)
    
    
    [Route_Optimisation]
    default_TSP = boolean(default=False)
    
    # Path optimizer behaviour:
    #  CONSTRAIN_ORDER_ONLY: fixed Shapes and optimized Shapes can be mixed. Only order of fixed shapes is kept
    #  CONSTRAIN_PLACE_AFTER: optimized Shapes are always placed after any fixed Shape
    TSP_shape_order = option('CONSTRAIN_ORDER_ONLY', 'CONSTRAIN_PLACE_AFTER', default='CONSTRAIN_ORDER_ONLY')
    mutation_rate = float(default= 0.95)
    max_population = integer(default= 20)
    max_iterations = integer(default= 300)
    begin_art = string(default="heurestic")
    
    [Import_Parameters]
    point_tolerance = float(default= 0.01)
    spline_check = boolean(default=True)
    fitting_tolerance = float(default= 0.01)
    
    [Tool_Parameters]
        [[1]]
        diameter = float(default= 2.0)
        speed = float(default=6000)
        start_radius = float(default= 0.2)
        
        [[2]]
        diameter = float(default=2.0)
        speed = float(default=6000.0)
        start_radius = float(default=1.0)
        
        [[10]]
        diameter = float(default=10.0)
        speed = float(default=6000.0)
        start_radius = float(default=2.0)
        
        [[__many__]]
        diameter = float(default= 3.0)
        speed = float(default=6000)
        start_radius = float(default= 3.0)
    
    [Custom_Actions]
        [[custom_gcode]]
        gcode = string(default='"""(change subsection name and insert your custom GCode here. Use triple quote to place the code on several lines)"""')
        
        [[__many__]]
        gcode = string(default="(change subsection name and insert your custom GCode here. Use triple quote to place the code on several lines)")
    
    
    [Filters]
    pstoedit_cmd = string(default="/opt/local/bin/pstoedit")
    pstoedit_opt = list(default=list('-f', 'dxf', '-mm'))
    
    [Logging]
    
    # set this to 'logfile = <filename>' to turn on file logging
    # or give the '-L logfile' program option
    logfile = string(default="")
    
    # log levels are one in increasing importance:
    #      DEBUG INFO WARNING  ERROR CRITICAL
    # log events with importance >= loglevel are logged to the
    # corresponding output
    
    # this really goes to stderr
    console_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default='DEBUG')
    
    file_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default='DEBUG')
    
    # logging level for the message window
    window_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default='INFO')
    
    [Feed_Rates]
    f_g1_plane = float(default=400)
    f_g1_depth = float(default=150)

''').splitlines()  
""" format, type and default value specification of the global config file"""


class MyConfig(QtCore.QObject):
    """
    This class hosts all functions related to the Config File.
    """
    def __init__(self):
        """
        initialize the varspace of an existing plugin instance
        init_varspace() is a superclass method of plugin
        """
        
        self.folder = os.path.join(g.folder, c.DEFAULT_CONFIG_DIR)
        self.filename =os.path.join(self.folder, 'config.cfg')
        
        self.default_config = False # whether a new name was generated
        self.var_dict = dict()
        self.spec = ConfigObj(CONFIG_SPEC, interpolation=False, list_values=False, _inspec=True)
        
        #try:
        self.load_config()
        
        self.fitting_tolerance=self.vars.Import_Parameters['fitting_tolerance']
        self.point_tolerance=self.vars.Import_Parameters['point_tolerance']
        
        #except Exception,msg:
        #    logger.warning(self.tr("Config loading failed: %s") % (msg))
        #    return False
    
    
    def tr(self,string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string    
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtGui.QApplication.translate("MyConfig",
                                                    string_to_translate,
                                                    None,
                                                    QtGui.QApplication.UnicodeUTF8))  
    
    def make_settings_folder(self):
        # create settings folder if necessary
        try:
            os.mkdir(self.folder)
        except OSError:
            pass
    

    def load_config(self):
        if os.path.isfile(self.filename):
            try:
                # file exists, read & validate it
                self.var_dict = ConfigObj(self.filename, configspec=CONFIG_SPEC)
                _vdt = Validator()
                result = self.var_dict.validate(_vdt, preserve_errors=True)
                validate_errors = flatten_errors(self.var_dict, result)
                
                if validate_errors:
                    g.logger.logger.error(self.tr("errors reading %s:") % (self.filename))

                for entry in validate_errors:
                    section_list, key, error = entry
                    if key is not None:
                        section_list.append(key)
                    else:
                        section_list.append('[missing section]')
                    section_string = ', '.join(section_list)
                    if error == False:
                        error = self.tr('Missing value or section.')
                    g.logger.logger.error( section_string + ' = ' + error)
                
                if validate_errors:
                    raise BadConfigFileError,"syntax errors in config file"
                
                # check config file version against internal version
                if CONFIG_VERSION:
                    fileversion = self.var_dict['Version']['config_version'] # this could raise KeyError
                    
                    if fileversion != CONFIG_VERSION:
                        raise VersionMismatchError, (fileversion, CONFIG_VERSION)
                
            except VersionMismatchError, values:
                raise VersionMismatchError, (fileversion, CONFIG_VERSION)
            
            except Exception,inst:
                logger.error(inst)
                (base,ext) = os.path.splitext(self.filename)
                badfilename = base + c.BAD_CONFIG_EXTENSION
                g.logger.logger.debug(self.tr("trying to rename bad cfg %s to %s") % (self.filename,badfilename))
                try:
                    os.rename(self.filename,badfilename)
                except OSError,e:
                    logger.error(self.tr("rename(%s,%s) failed: %s") % (self.filename,badfilename,e.strerror))
                    raise
                else:
                    logger.debug(self.tr("renamed bad varspace %s to '%s'") %(self.filename,badfilename))
                    self.create_default_config()
                    self.default_config = True
                    logger.debug(self.tr("created default varspace '%s'") %(self.filename))
            else:
                self.default_config = False
                #logger.debug(self.dir())
                #logger.debug(self.tr("created default varspace '%s'") %(self.filename))
                #logger.debug(self.tr("read existing varspace '%s'") %(self.filename))
        else:
            self.create_default_config()
            self.default_config = True
            logger.debug(self.tr("created default varspace '%s'") %(self.filename))
        
        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.var_dict.main.interpolation = False # avoid ConfigObj getting too clever
        self.vars = DictDotLookup(self.var_dict)
    
    
    def create_default_config(self):
        #check for existing setting folder or create one
        self.make_settings_folder()
        
        # derive config file with defaults from spec
        self.var_dict = ConfigObj(configspec=CONFIG_SPEC)
        _vdt = Validator()
        self.var_dict.validate(_vdt, copy=True)
        self.var_dict.filename = self.filename
        self.var_dict.write()
        
        
    def _save_varspace(self):
        self.var_dict.filename = self.filename
        self.var_dict.write()
    
    def print_vars(self):
        print "Variables:"
        for k,v in self.var_dict['Variables'].items():
            print k," = ",v
    

    
class DictDotLookup(object):
    """
    Creates objects that behave much like a dictionaries, but allow nested
    key access using object '.' (dot) lookups.
    """
    def __init__(self, d):
        for k in d:
            if isinstance(d[k], dict):
                self.__dict__[k] = DictDotLookup(d[k])
            elif isinstance(d[k], (list, tuple)):
                l = []
                for v in d[k]:
                    if isinstance(v, dict):
                        l.append(DictDotLookup(v))
                    else:
                        l.append(v)
                self.__dict__[k] = l
            else:
                self.__dict__[k] = d[k]
    
    def __getitem__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
    
    def __iter__(self):
        return iter(self.__dict__.keys())
    
    def __repr__(self):
        return pprint.pformat(self.__dict__)
    
#if __name__ == '__main__':
#    cfg_data = eval("""{
#        'foo' : {
#            'bar' : {
#                'tdata' : (
#                    {'baz' : 1 },
#                    {'baz' : 2 },
#                    {'baz' : 3 },
#                ),
#            },
#        },
#        'quux' : False,
#    }""")
#
#    cfg = DictDotLookup(cfg_data)
#
#    # iterate
#    for k,v in cfg.__iter__(): #foo.bar.iteritems():
#        print k," = ",v
#        
#    print "cfg=",cfg
#    
#    #   Standard nested dictionary lookup.
#    print 'normal lookup :', cfg['foo']['bar']['tdata'][0]['baz']
#
#    #   Dot-style nested lookup.
#    print 'dot lookup    :', cfg.foo.bar.tdata[0].baz
#    
#    print "qux=",cfg.quux
#    cfg.quux = '123'
#    print "qux=",cfg.quux
#    
#    del cfg.foo.bar
#    cfg.foo.bar = 4711
#    print 'dot lookup    :', cfg.foo.bar #.tdata[0].baz

