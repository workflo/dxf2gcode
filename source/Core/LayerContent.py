#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#Programmers:   Christian Kohl�ffel
#               Vinzenz Schulz
#
#Distributed under the terms of the GPL (GNU Public License)
#
#dxf2gcode is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import Core.Globals as g

import logging
logger=logging.getLogger("Core.LayerContent") 

class LayerContentClass:
    """
    The LayerContentClass is used for the definition of the shape order to 
    export and to store and change (GUI) the different export parameters. The
    LayerConentClasses for each Layer is stored in a list. This List Defines the
    order for Layers to be exported. 
    """
    def __init__(self,LayerNr=None,LayerName='',shapes=[]):
        """
        Initialization of the LayerContentClass. This is performed during the
        shapes creation in the main dxf2gcode.py file. 
        @param LayerNr: This parameter is forwarded from the dxf import
        @param LayerName: This parameter is forwarded from the dxf import
        @param shapes: This is a list which includes all shapes on the layer.
        """
        
        #Define Short Name for config.vars
        vars=g.config.vars
        
        self.type = "Layer"
        self.LayerNr=LayerNr
        self.LayerName=LayerName
        self.shapes=shapes
        self.exp_order=[] #used for shape order optimization, ... Only contains shapes
        self.exp_order_complete=[] #used for outputing the GCODE ; can contain shapes, custom gcode, ...
        self.axis3_slice_depth=vars.Depth_Coordinates['axis3_slice_depth']
        self.axis3_start_mill_depth=vars.Depth_Coordinates['axis3_start_mill_depth']
        self.axis3_mill_depth=vars.Depth_Coordinates['axis3_mill_depth']
        self.axis3_retract=vars.Depth_Coordinates['axis3_retract']
        self.axis3_safe_margin=vars.Depth_Coordinates['axis3_safe_margin']

        #Use default tool 1 (always exists in config)
        self.tool_nr=1
        self.tool_diameter=vars.Tool_Parameters['1']['diameter']
        self.speed=vars.Tool_Parameters['1']['speed']
        self.start_radius=vars.Tool_Parameters['1']['start_radius']
        self.f_g1_plane=vars.Feed_Rates['f_g1_plane']
        self.f_g1_depth=vars.Feed_Rates['f_g1_depth']
        
        
    def __cmp__(self, other):
        return cmp(self.LayerNr, other.LayerNr)
        """
        This function just compares the LayerNr to sort the List of LayerContents
        @param other: This is the 2nd of the LayerContentClass to be compared.
        """

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """
        return ('\ntype:          %s' %self.type) +\
               ('\nLayerNr :      %i' %self.LayerNr) +\
               ('\nLayerName:     %s' %self.LayerName)+\
               ('\nshapes:        %s' %self.shapes)+\
               ('\nexp_order:     %s' %self.exp_order)+\
               ('\nexp_order_comp:%s' %self.exp_order_complete)+\
               ('\ntool_diameter: %i' %self.tool_nr)
