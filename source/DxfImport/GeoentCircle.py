#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_geoent_circle
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

from math import  sin, cos, pi
from PyQt4 import QtCore, QtGui

from Core.Point import Point
from DxfImport.Classes import ContourClass
from Core.ArcGeo import  ArcGeo 

import logging
logger=logging.getLogger("DXFImport.GeoentCircle") 

class GeoentCircle(QtCore.QObject):
    def __init__(self, Nr=0, caller=None):
        self.Typ = 'Circle'
        self.Nr = Nr
        self.Layer_Nr = 0
        self.length = 0.0
        self.geo = []

        #Lesen der Geometrie
        #Read the geometry
        self.Read(caller)
        
    def __str__(self):
        # how to print the object
        return("\nTyp: Circle ") + \
              ("\nNr: %i" % self.Nr) + \
              ("\nLayer Nr:%i" % self.Layer_Nr) + \
              str(self.geo[-1])
              
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
   

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol, warning):
        cont.append(ContourClass(len(cont), 1, [[i, 0]], self.length))
        return warning
        
    def Read(self, caller):

        #K�rzere Namen zuweisen
        #Assign short name
        lp = caller.line_pairs
        e = lp.index_code(0, caller.start + 1)


        #Layer zuweisen
        #Assign layer
        s = lp.index_code(8, caller.start + 1)
        self.Layer_Nr = caller.Get_Layer_Nr(lp.line_pair[s].value)
        #XWert
        #X Value
        s = lp.index_code(10, s + 1)
        x0 = float(lp.line_pair[s].value)
        #YWert
        #Y Value
        s = lp.index_code(20, s + 1)
        y0 = float(lp.line_pair[s].value)

        #Radius
        s = lp.index_code(40, s + 1)
        r = float(lp.line_pair[s].value)
        
        #Searching for an extrusion direction
        s_nxt_xt = lp.index_code(230, s + 1, e)
        #If there is a extrusion direction given flip around x-Axis
        if s_nxt_xt != None:
            extrusion_dir = float(lp.line_pair[s_nxt_xt].value)
            logger.debug(self.tr('Found extrusion direction: %s') %extrusion_dir)
            if extrusion_dir == -1:
                x0=-x0
                
        O = Point(x0, y0)

        #Berechnen der Start und Endwerte des Kreises ohne �berschneidung
        #Calculate the start and end values of the circle without clipping
        s_ang = -3 * pi / 4
        m_ang = s_ang -pi
        e_ang = -3 * pi / 4

        #Berechnen der Start und Endwerte des Arcs
        #Calculate the start and end values of the arcs
        Pa = Point(x=cos(s_ang) * r, y=sin(s_ang) * r) + O
        Pm = Point(x=cos(m_ang) * r, y=sin(m_ang) * r) + O
        Pe = Point(x=cos(e_ang) * r, y=sin(e_ang) * r) + O

        #Anh�ngen der ArcGeo Klasse f�r die Geometrie
        #Annexes to ArcGeo class for geometry
        self.geo.append(ArcGeo(Pa=Pa, Pe=Pm, O=O, r=r,
                               s_ang=s_ang, e_ang=m_ang, direction=-1))
        self.geo.append(ArcGeo(Pa=Pm, Pe=Pe, O=O, r=r,
                               s_ang=m_ang, e_ang=e_ang, direction=-1))

        #L�nge entspricht der L�nge des Kreises
        #Length corresponds to the length (circumference?) of the circle
        self.length = self.geo[-1].length+self.geo[-2].length
       
        #Neuen Startwert f�r die n�chste Geometrie zur�ckgeben
        #New starting value for the next geometry
        caller.start = s        

    def get_start_end_points(self, direction=0):
        if not(direction):
            punkt, angle = self.geo[0].get_start_end_points(direction)
        elif direction:
            punkt, angle = self.geo[-1].get_start_end_points(direction)
        return punkt, angle
