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


from math import sqrt, sin, cos, degrees, pi, floor, ceil

from PyQt4 import QtCore

from Core.Point import Point

import logging
logger=logging.getLogger("Core.ArcGeo")

#Length of the cross.
dl = 0.2
DEBUG = 1

class ArcGeo(QtCore.QObject):
    """
    Standard Geometry Item used for DXF Import of all geometries, plotting and
    G-Code export.
    """ 
    def __init__(self, Pa=None, Pe=None, O=None, r=1,
                 s_ang=None, e_ang=None, direction=1):
        """
        Standard Method to initialize the LineGeo
        """
        QtCore.QObject.__init__(self)
        
        self.type = "ArcGeo"
        self.Pa = Pa
        self.Pe = Pe
        self.O = O
        self.r = abs(r)
        self.s_ang = s_ang
        self.e_ang = e_ang
        self.col = 'Black'
        
        
        # Get the Circle Milllw with known Start and End Points
        if type(self.O) == type(None):
            
            if (type(Pa) != type(None)) and \
            (type(Pe) != type(None)) and \
            (type(direction) != type(None)):
                
                arc = self.Pe.norm_angle(Pa) - pi / 2
                Ve = Pe - Pa
                m = (sqrt(pow(Ve.x, 2) + pow(Ve.y, 2))) / 2
                lo = sqrt(pow(r, 2) - pow(m, 2))
                if direction < 0:
                    d = -1
                else:
                    d = 1
                self.O = Pa + 0.5 * Ve
                self.O.y += lo * sin(arc) * d
                self.O.x += lo * cos(arc) * d
                
                
        # Falls nicht übergeben Mittelpunkt ausrechnen
        # Compute centre...
            elif (type(self.s_ang) != type(None)) and (type(self.e_ang) != type(None)):
                self.O.x = self.Pa.x - r * cos(self.s_ang)
                self.O.y = self.Pa.y - r * sin(self.s_ang)
            else:
                logger.error(self.tr("Missing value for Arc Geometry"))
        
        #Falls nicht übergeben dann Anfangs- und Endwinkel ausrechen
        #Calculate start and end angles
        if type(self.s_ang) == type(None):
            self.s_ang = self.O.norm_angle(Pa)
        
        if type(self.e_ang) == type(None):
            self.e_ang = self.O.norm_angle(Pe)
        
        self.ext=self.dif_ang(self.Pa, self.Pe, direction)
        #self.get_arc_extend(direction)
        
        #Falls es ein Kreis ist Umfang 2pi einsetzen
        #If there is a circumference use 2*pi
        if self.ext == 0.0:
            self.ext = 2 * pi
        
        self.length = self.r * abs(self.ext)
    
    
    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ("\nArcGeo") + \
               ("\nPa : %s; s_ang: %0.5f" % (self.Pa, self.s_ang)) + \
               ("\nPe : %s; e_ang: %0.5f" % (self.Pe, self.e_ang)) + \
               ("\nO  : %s; r: %0.3f" % (self.O, self.r)) + \
               ("\next  : %0.5f; length: %0.5f" % (self.ext, self.length))
    
    
    def add2path(self, papath=None, parent=None):
        """
        Plots the geometry of self into defined path for hit testing. Refer
        to http://stackoverflow.com/questions/11734618/check-if-point-exists-in-qpainterpath
        for description
        @param hitpath: The hitpath to add the geometrie
        @param parent: The parent of the shape
        """
        
        abs_geo=self.make_abs_geo(parent, 0)
        
        segments = int((abs(degrees(abs_geo.ext)) // 3) + 1)
        
        for i in range(segments + 1):
            
            ang = abs_geo.s_ang + i * abs_geo.ext / segments
            p_cur = Point(x=(abs_geo.O.x + cos(ang) * abs(abs_geo.r)), \
                       y=(abs_geo.O.y + sin(ang) * abs(abs_geo.r)))
            
            if i >= 1:
                papath.lineTo(p_cur.x, -p_cur.y)
    
#
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
#        
#        self.add2path(papath=hitpath, parent=parent)
#    
    def dif_ang(self, P1, P2, direction,tol=0.005):
        """
        Calculated the angle of extend based on the 3 given points. Center Point,
        P1 and P2.
        @param P1: the start Point of the arc
        @param P2: the end Point of the arc
        @param direction: the direction of the arc
        @return: Returns the angle between -2* pi and 2 *pi for the arc extend
        """
        
        #FIXME Das könnte Probleme geben bei einem reelen Kreis
        #FIXME This could indicate problems in a real arc
#        if P1.isintol(P2,tol):
#            return 0.0
#        
        sa = self.O.norm_angle(P1)
        ea = self.O.norm_angle(P2)
        
        if(direction > 0.0):     # GU
            dif_ang = (ea-sa)%(-2*pi)
            dif_ang -= floor(dif_ang / (2 * pi)) * (2 * pi)
        else:
            dif_ang = (ea-sa)%(-2*pi)
            dif_ang += ceil(dif_ang / (2 * pi)) * (2 * pi)
        
        return dif_ang
    
    def reverse(self):
        """
        Reverses the direction of the arc (switch direction).
        """
        Pa = self.Pa
        Pe = self.Pe
        ext = self.ext
        s_ang = self.e_ang
        e_ang = self.s_ang
        
        self.Pa = Pe
        self.Pe = Pa
        self.ext = ext * -1
        self.s_ang = s_ang
        self.e_ang = e_ang
    
    def make_abs_geo(self, parent=None, reverse=0):
        """
        Generates the absolute geometry based on the geometry self and the
        parent. If reverse=1 is given the geometry may be reversed.
        @param parent: The parent of the geometry (EntitieContentClass)
        @param reverse: If 1 the geometry direction will be switched.
        @return: A new ArcGeoClass will be returned.
        """ 
        
        Pa = self.Pa.rot_sca_abs(parent=parent)
        Pe = self.Pe.rot_sca_abs(parent=parent)
        O = self.O.rot_sca_abs(parent=parent)
        r = self.scaleR(self.r, parent)
        #s_ang=self.rot_angle(self.s_ang,parent)
        #e_ang=self.rot_angle(self.e_ang,parent)
        
        if self.ext>0.0:
            direction=1
        else:
            direction=-1
        
        if type(parent) != type(None):
            if parent.sca[0]*parent.sca[1]<0.0:
                direction=direction*-1
        
        #abs_geo = ArcGeo(Pa=Pa, Pe=Pe, O=O, r=r, s_ang=s_ang,e_ang=e_ang, direction=direction)
        abs_geo = ArcGeo(Pa=Pa, Pe=Pe, O=O, r=r, direction=direction)
        
        if reverse:
            abs_geo.reverse()
        
        return abs_geo
    
    
    def get_start_end_points(self, direction,parent=None):
        """
        Returns the start/end Point and its direction
        @param direction: 0 to return start Point and 1 to return end Point
        @return: a list of Point and angle Returns the hdl or hdls of the plotted objects.
        """
        
        abs_geo=self.make_abs_geo(parent)
        
        if not(direction):
            punkt=abs_geo.Pa
            angle=abs_geo.s_ang+pi/2*abs_geo.ext/abs(abs_geo.ext)
        elif direction:
            punkt=abs_geo.Pe
            angle=abs_geo.e_ang-pi/2*abs_geo.ext/abs(abs_geo.ext)
        return punkt,angle
    
    def angle_between(self, min_ang, max_ang, angle):
        """
        Returns if the angle is in the range between 2 other angles
        @param min_ang: The starting angle
        @param parent: The end angle. Always in ccw direction from min_ang
        @return: True or False
        """
        if min_ang < 0.0:
            min_ang += 2 * pi
        
        while max_ang < min_ang:
            max_ang += 2 * pi
        
        while angle < min_ang:
            angle += 2 * pi
        
        return (min_ang < angle) and (angle <= max_ang)
    
#    def rot_angle(self, angle, parent):
#        """
#        Rotates the given angle based on the rotations given in its parents.
#        @param angle: The angle which shall be rotated
#        @param parent: The parent Entitie (Instance: EntitieContentClass)
#        @return: The rotated angle.
#        """
#
##        #Rekursive Schleife falls mehrfach verschachtelt.
##        #Recursive loop if nested
#        if type(parent) != type(None):
#            angle += parent.rot
#            
#            if parent.sca[0]<0.0:
#                angle=pi-angle
#                
#            if parent.sca[1]<0.0:
#                angle=pi-angle
#                
#            angle = self.rot_angle(angle, parent.parent)
#        
#        
#        return angle
    
    def scaleR(self, sR, parent):
        """
        Scales the radius based on the scale given in its parents. This is done
        recursively.
        @param sR: The radius which shall be scaled
        @param parent: The parent Entitie (Instance: EntitieContentClass)
        @return: The scaled radius
        """
        
        #Rekursive Schleife falls mehrfach verschachtelt.
        #Recursive loop if nested.
        if type(parent) != type(None):
            sR = sR * parent.sca[0]
            sR = self.scaleR(sR, parent.parent)
        
        return sR
    
    def Write_GCode(self, parent=None, PostPro=None):
        """
        Writes the GCODE for a ARC.
        @param parent: This is the parent EntitieContent Class
        @param PostPro: The PostProcessor instance to be used
        @return: Returns the string to be written to a file.
        """
        
        abs_geo=self.make_abs_geo(parent, 0)
        
        anf, s_ang=abs_geo.get_start_end_points(0)
        ende, e_ang=abs_geo.get_start_end_points(1)
        
        O=abs_geo.O
        sR=abs_geo.r
        IJ=(O-anf)
        
        #If the radius of the element is bigger then the max. radius export
        #the element as an line.
        
        if sR>PostPro.vars.General["max_arc_radius"]:
            string=PostPro.lin_pol_xy(anf,ende)
        else:
            if (self.ext>0):
                #string=("G3 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,ende.x,axis2,ende.y,IJ.x,IJ.y))
                string=PostPro.lin_pol_arc("ccw",anf,ende,s_ang,e_ang,sR,O,IJ)
            elif (self.ext<0) and PostPro.vars.General["export_ccw_arcs_only"]:
                string=PostPro.lin_pol_arc("ccw",ende,anf,e_ang,s_ang,sR,O,(O-ende))
            else:
                #string=("G2 %s%0.3f %s%0.3f I%0.3f J%0.3f\n" %(axis1,ende.x,axis2,ende.y,IJ.x,IJ.y))
                string=PostPro.lin_pol_arc("cw",anf,ende,s_ang,e_ang,sR,O,IJ)
        return string
