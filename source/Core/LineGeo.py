#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
#
#dxf2gcode_b02_point
#Programmers:   Christian Kohlöffel
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


from math import sqrt
from Point import Point
from PyQt4 import QtCore, QtGui

import logging
logger=logging.getLogger("Core.LineGeo") 

#Length of the cross.
dl = 0.2
DEBUG = 1

class LineGeo(QtCore.QObject):
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """ 
    def __init__(self, Pa, Pe):
        """
        Standard Method to initialise the LineGeo
        """
        self.type = "LineGeo"
        self.Pa = Pa
        self.Pe = Pe
        self.col = 'Black'
        self.length = self.Pa.distance(self.Pe)
        
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nLineGeo") + \
               ("\nPa : %s" % self.Pa) + \
               ("\nPe : %s" % self.Pe) + \
               ("\nlength: %0.5f" % self.length)        

    def reverse(self):
        """ 
        Reverses the direction of the arc (switch direction).
        """ 
        Pa = self.Pa
        Pe = self.Pe
        
        self.Pa = Pe
        self.Pe = Pa

    def tr(self,string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string    
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtGui.QApplication.translate("ReadDXF",
                                                    string_to_translate,
                                                    None,
                                                    QtGui.QApplication.UnicodeUTF8)) 
   
    def make_abs_geo(self, parent=None, reverse=0):
        """
        Generates the absolut geometry based on the geometry self and the
        parent. If reverse 1 is given the geometry may be reversed.
        @param parent: The parent of the geometry (EntitieContentClass)
        @param reverse: If 1 the geometry direction will be switched.
        @return: A new LineGeoClass will be returned.
        """ 
        
        Pa = self.Pa.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)
        abs_geo = LineGeo(Pa=Pa, Pe=Pe)
        if reverse:
            abs_geo.reverse()
          
        return abs_geo
    
        
    def add2path(self, papath=None, parent=None):
        """
        Plots the geometry of self into defined path for hit testing..
        @param hitpath: The hitpath to add the geometrie
        @param parent: The parent of the shape
        @param tolerance: The tolerance to be added to geometrie for hit
        testing.
        """

        abs_geo=self.make_abs_geo(parent, 0)
        papath.lineTo(abs_geo.Pe.x, -abs_geo.Pe.y)
        #self.add2hitpath(hitpath=papath,parent=parent, tolerance=5)

#    def add2hitpath(self, hitpath=None, parent=None, tolerance=None):
#        """
#        Plots the geometry of self into defined path for hit testing. Refer
#        to http://stackoverflow.com/questions/11734618/check-if-point-exists-in-qpainterpath
#        for description
#        @param hitpath: The hitpath to add the geometrie
#        @param parent: The parent of the shape
#        @param tolerance: The tolerance to be added to geometrie for hit
#        testing.
#        """
#        #offset = the distance vector from p1 to p2 
#        abs_geo=self.make_abs_geo(parent, 0)
#        abs_geo.Pa.y=-abs_geo.Pa.y
#        abs_geo.Pe.y=-abs_geo.Pe.y
#        
#        offset=abs_geo.Pe-abs_geo.Pa
#        length = abs_geo.Pa.distance(abs_geo.Pe)
#        offset = offset*[tolerance / length, tolerance/ length]
#        
#        leftOffset=Point(-offset.y, offset.x)
#        rightOffset=Point(offset.y, -offset.x)
# 
#        #if (p1, p2) goes downwards, then left lies to the left and 
#        #right to the right of the source path segment 
#        left1 = abs_geo.Pa + leftOffset
#        left2 = abs_geo.Pe + leftOffset
#        right1 = abs_geo.Pa + rightOffset
#        right2 = abs_geo.Pe + rightOffset
#        
#        hitpath2=QtGui.QPainterPath()
#        hitpath2.moveTo(left1.x,left1.y)
#        hitpath2.lineTo(left2.x,left2.y)
#        hitpath2.lineTo(right2.x,right2.y)
#        hitpath2.lineTo(right1.x, right1.y)
#        hitpath2.lineTo(left1.x, left1.y)
#        hitpath +=hitpath2
#        
#        hitpath3=QtGui.QPainterPath()
#        hitpath +=hitpath3.addEllipse(abs_geo.Pe.x,abs_geo.Pe.y,tolerance, tolerance)
#        
    def get_start_end_points(self, direction, parent=None):
        """
        Returns the start/end Point and its direction
        @param direction: 0 to return start Point and 1 to return end Point
        @return: a list of Point and angle 
        """
        if not(direction):
            punkt=self.Pa.rot_sca_abs(parent=parent)
            punkt_e=self.Pe.rot_sca_abs(parent=parent)
            angle=punkt.norm_angle(punkt_e)
        elif direction:
            punkt_a=self.Pa.rot_sca_abs(parent=parent)
            punkt=self.Pe.rot_sca_abs(parent=parent)
            angle=punkt.norm_angle(punkt_a)
        return punkt, angle
    
    def Write_GCode(self, parent=None, PostPro=None):
        """
        To be called if a LineGeo shall be written to the PostProcessor.
        @param pospro: The used Posprocessor instance
        @return: a string to be written into the file
        """
        anf, anf_ang=self.get_start_end_points(0,parent)
        ende, end_ang=self.get_start_end_points(1,parent)

        return PostPro.lin_pol_xy(anf,ende)

    def distance2point(self, Point):
        """
        Returns the distance between a line and a given Point
        @param Point: The Point which shall be checked
        @return: returns the distance to the Line
        """
        try:
            AE = self.Pa.distance(self.Pe)
            AP = self.Pa.distance(Point)
            EP = self.Pe.distance(Point)
            AEPA = (AE + AP + EP) / 2
            return abs(2 * sqrt(abs(AEPA * (AEPA - AE) * \
                                     (AEPA - AP) * (AEPA - EP))) / AE)
        except:
            return 1e10
            
