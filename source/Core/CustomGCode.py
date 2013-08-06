# -*- coding: utf-8 -*-
"""
This class contains a "custom gcode" object. Custom GCode objects are part of a layer (LayerContent.py) and are used to insert custom GCode into the generated file.
Customs GCodes are defined in config.cfg file

@purpose: store user defined GCode
@author: Xavier Izard
@since:  2012.10.27
@license: GPL
"""

"""
from PyQt4 import QtCore, QtGui

import Core.Globals as g

from Core.Point import Point
from Core.BoundingBox import BoundingBox
from math import cos, sin, degrees
from copy import deepcopy
from EntitieContent import EntitieContentClass
"""
import logging
logger=logging.getLogger("Core.CustomGCodeClass")


class CustomGCodeClass:
    """
    The Shape Class includes all plotting, GUI functionality and export functions
    related to the Shapes.
    """
    def __init__(self, name, nr, gcode=None, parent=None):
        """
        Standard method to initialize the class
        @param name: the name of the GCode, as defined in the config file
        @param gcode: the user defined gcode
        @param parent: The parent layer Class of the shape
        """
        self.type = "CustomGCode"
        self.name = name
        self.nr = nr
        self.gcode = gcode
        self.LayerContent = parent
        self.disabled = False
        self.send_to_TSP = False #Never optimize path for CustomGCode
    
    
    def __str__(self):
        """
        Standard method to print the object
        @return: A string
        """
        return ('\ntype:        %s' % self.type) + \
               ('\nname:        %s' % self.name) + \
               ('\nnr:          %i' % self.nr) + \
               ('\ngcode:       %s' % self.gcode)
    
    
    
    def setDisable(self, flag=False):
        """
        Function to modify the disable property
        @param flag: The flag to enable or disable Selection
        """
        self.disabled=flag
    
    
    
    def isDisabled(self):
        """
        Returns the state of self.disabled
        """
        return self.disabled
    
    
    
    def Write_GCode(self, LayerContent=None, PostPro=None):
        """
        This method returns the string to be exported for this custom gcode, including
        @param LayerContent: This parameter includes the parent LayerContent
        @param PostPro: this is the Postprocessor class including the methods to export
        """
        
        #initialisation of the string
        exstr = self.gcode
        
        return exstr
