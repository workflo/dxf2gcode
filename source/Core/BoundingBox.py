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



from Core.Point import Point
from copy import copy


class BoundingBox:
    """ 
    Bounding Box Class. This is the standard class which provides all std.
    Bounding Box methods.
    """ 
    def __init__(self, Pa=Point(0, 0), Pe=Point(0, 0), hdl=[]):
        """ 
        Standard method to initialize the class
        """ 
        self.Pa = Pa
        self.Pe = Pe
    
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        s = ("\nPa : %s" % (self.Pa)) + \
           ("\nPe : %s" % (self.Pe))
        return s
    
    def joinBB(self, other):
        """
        Joins two Bounding Box Classes and returns the new one
        @param other: The 2nd Bounding Box
        @return: Returns the joined Bounding Box Class
        """
        
        if type(self.Pa) == type(None) or type(self.Pe) == type(None):
            return BoundingBox(copy(other.Pa), copy(other.Pe))
        
        xmin = min(self.Pa.x, other.Pa.x)
        xmax = max(self.Pe.x, other.Pe.x)
        ymin = min(self.Pa.y, other.Pa.y)
        ymax = max(self.Pe.y, other.Pe.y)
        
        return BoundingBox(Pa=Point(xmin, ymin), Pe=Point(xmax, ymax))
    
    def hasintersection(self, other=None, tol=0.0):
        """
        Checks if the two bounding boxes have an intersection
        @param other: The 2nd Bounding Box
        @return: Returns true or false
        """
        x_inter_pos = (self.Pe.x + tol > other.Pa.x) and \
                      (self.Pa.x - tol < other.Pe.x)
        y_inter_pos = (self.Pe.y + tol > other.Pa.y) and \
                      (self.Pa.y - tol < other.Pe.y)
        
        return x_inter_pos and y_inter_pos
    
    def pointisinBB(self, Point=Point(), tol=0.01):
        """
        Checks if the Point is within the bounding box
        @param Point: The Point which shall be checked
        @return: Returns true or false
        """
        x_inter_pos = (self.Pe.x + tol > Point.x) and \
                      (self.Pa.x - tol < Point.x)
        y_inter_pos = (self.Pe.y + tol > Point.y) and \
                      (self.Pa.y - tol < Point.y)
        return x_inter_pos and y_inter_pos

