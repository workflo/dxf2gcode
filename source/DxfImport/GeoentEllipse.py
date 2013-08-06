#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_geoent_ellipse
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

from math import sqrt, sin, cos, atan2, degrees, pi
from Core.Point import Point
from DxfImport.Classes import PointsClass, ContourClass
from DxfImport.biarc import BiarcClass



class GeoentEllipse:
    def __init__(self, Nr=0, caller=None):
        self.Typ = 'Ellipse'
        self.Nr = Nr
        #Initialisieren der Werte
        #Initialise the values
        self.Layer_Nr = 0
        self.center = Point(0, 0) #Mittelpunkt der Geometrie / Centre of the geometry
        self.vector = Point(1, 0) #Vektor A = gro�e Halbachse a, = Drehung der Ellipse
                                  # Vector A = semi-major axis. a = rotation of the ellipse
                                  # http://de.wikipedia.org/wiki/Gro%C3%9Fe_Halbachse
        self.ratio = 1            #Verh�ltnis der kleinen zur gro�en Halbachse (b/a)
                                  #Ratio of the minor to major axis (b/a)
        #self.AngS = 0                 #Startwinkel beim zeichnen eines Ellipsensegments
                                       #Starting angle when drawing an ellipse segment
        #self.AngE = radians(360)      #Endwinkel (Winkel im DXF als Radians!)
                                       #End angle (angle in radians as DXF!)
        #Die folgenden Grundwerte werden sp�ter ein mal berechnet
        #The following limits are calculated later

        self.length = 0
        self.Points = []
        self.Points.append(self.center)
        #Lesen der Geometrie / Read the geometry
        self.Read(caller)

        #Zuweisen der Toleranz f�rs Fitting / Assign the tolerance for fitting
        tol = g.config.fitting_tolerance
        
        #Errechnen der Ellipse / Calculate the ellipse
        self.Ellipse_Grundwerte()
        self.Ellipse_2_Arcs(tol)
        

    def __str__(self):
        # how to print the object #Geht auch so ellegant wie sprintf in C oder Matlab usw. siehe erste zeile  !!!!!!!!!!!!!!!!!!!!!!
        # As elegant as printf in C or Matlab etc. see the first line!
        s = ('Typ: Ellipse\n') + \
        ('Nr:     %i \n' % (self.Nr)) + \
        'Layer:  ' + str(self.Layer_Nr) + '\n' + \
        'center: ' + str(self.center) + '\n' + \
        'vector: ' + str(self.vector) + '\n' + \
        'ratio:  ' + str(self.ratio) + '\n' + \
        'angles: ' + str(degrees(self.AngS)) + ' -> ' + str(degrees(self.AngE)) + '\n' + \
        'extend: ' + str(degrees(self.ext)) + '\n' + \
        'a:      ' + str(self.a) + '\n' + \
        'b:      ' + str(self.b) + '\n' + \
        'length: ' + str(self.length) + \
        ("\nNr. of arcs: %i" % len(self.geo))
        return s

    def reverse(self):
        self.geo.reverse()
        for geo in self.geo:
            geo.reverse()    

    def App_Cont_or_Calc_IntPts(self, cont, points, i, tol, warning):
        #Hinzuf�gen falls es keine geschlossene Polyline ist
        #Add if it is not a closed polyline
        if self.geo[0].Pa.isintol(self.geo[-1].Pe, tol):
            self.analyse_and_opt()
            cont.append(ContourClass(len(cont), 1, [[i, 0]], self.length))
        else:
            points.append(PointsClass(point_nr=len(points), geo_nr=i, \
                          Layer_Nr=self.Layer_Nr, \
                          be=self.geo[0].Pa,
                          en=self.geo[-1].Pe, be_cp=[], en_cp=[]))  
        return warning

    def Read(self, caller):
        #K�rzere Namen zuweisen
        #Assign short name
        lp = caller.line_pairs
        e = lp.index_code(0, caller.start + 1)
        #Layer zuweisen
        #Assign Layer
        s = lp.index_code(8, caller.start + 1)
        self.Layer_Nr = caller.Get_Layer_Nr(lp.line_pair[s].value)
        #XWert, YWert Center
        #Centre X value, Y value
        s = lp.index_code(10, s + 1)
        x0 = float(lp.line_pair[s].value)
        s = lp.index_code(20, s + 1)
        y0 = float(lp.line_pair[s].value)
        self.center = Point(x0, y0)
        #XWert, YWert. Vektor, relativ zum Zentrum, Gro�e Halbachse
        #X value, Y value. Vector relative to the center, Semi-major axis
        s = lp.index_code(11, s + 1)
        x1 = float(lp.line_pair[s].value)
        s = lp.index_code(21, s + 1)
        y1 = float(lp.line_pair[s].value)
        self.vector = Point(x1, y1)
        #Ratio minor to major axis
        s = lp.index_code(40, s + 1)
        self.ratio = float(lp.line_pair[s].value)
        #Start Winkel - Achtung, ist als rad (0-2pi) im dxf
        #Start angle - Note in radian (0-2pi) per dxf
        s = lp.index_code(41, s + 1)
        self.AngS = float(lp.line_pair[s].value)
        #End Winkel - Achtung, ist als rad (0-2pi) im dxf
        #End angle - Note in radian (0-2pi) per dxf
        s = lp.index_code(42, s + 1)
        self.AngE = float(lp.line_pair[s].value)
        #Neuen Startwert f�r die n�chste Geometrie zur�ckgeben
        #New starting value for the next geometry return
        caller.start = e
        

    def analyse_and_opt(self):
        #Richtung in welcher der Anfang liegen soll (unten links)
        #Direction of top (lower left) ???
        Popt = Point(x= -1e3, y= -1e6)
        
        #Suchen des kleinsten Startpunkts von unten Links X zuerst (Muss neue Schleife sein!)
        #Find the smallest starting point from bottom left X (Must be new loop!)
        min_distance = self.geo[0].Pa.distance(Popt)
        min_geo_nr = 0
        for geo_nr in range(1, len(self.geo)):
            if (self.geo[geo_nr].Pa.distance(Popt) < min_distance):
                min_distance = self.geo[geo_nr].Pa.distance(Popt)
                min_geo_nr = geo_nr

        #Kontur so anordnen das neuer Startpunkt am Anfang liegt
        #Contour so the new starting point is at the start order
        self.geo = self.geo[min_geo_nr:len(self.geo)] + self.geo[0:min_geo_nr]
        
    def get_start_end_points(self, direction=0):
        if not(direction):
            punkt, angle = self.geo[0].get_start_end_points(direction)
        elif direction:
            punkt, angle = self.geo[-1].get_start_end_points(direction)
        return punkt, angle
    
    def Ellipse_2_Arcs(self, tol):
        #Anfangswert f�r Anzahl Elemente
        #Initial value for number of elements
        num_elements = 2
        intol = False   
        
        #print degrees(self.AngS)
        #print tol

        while not(intol):
            intol = True
            
            #Anfangswete Ausrechnen
            #Calculate Anfangswete ???
            angle = self.AngS
            Pa = self.Ellipse_Point(angle)
            tana = self.Ellipse_Tangent(angle)

            self.geo = []
            self.PtsVec = []
            self.PtsVec.append([Pa, tana])
            
            
            for sec in range(num_elements):
                #Schrittweite errechnen
                #Calculate Increment
                step = self.ext / num_elements
                
                #print degrees(step)
                
                #Endwerte errechnen
                #Calculate final values
                Pb = self.Ellipse_Point(angle + step)
                tanb = self.Ellipse_Tangent(angle + step)

                #Biarc erstellen und an geo anh�ngen
                #Biarc create and attach them ???
                biarcs = BiarcClass(Pa, tana, Pb, tanb, tol / 100)
                self.geo += biarcs.geos[:]             

                #Letzer Wert = Startwert
                #Last value = Start value
                Pa = Pb
                tana = tanb
                
                self.PtsVec.append([Pa, tana])

                if not(self.check_ellipse_fitting_tolerance(biarcs, tol, angle, angle + step)):
                    intol = False
                    num_elements += 1
                    break
                
                #Neuer Winkel errechnen
                #Calculate new angle
                angle += step
        #print degrees(angle)
        #print self
        
        
                      
    def check_ellipse_fitting_tolerance(self, biarc, tol, ang0, ang1):
        check_step = (ang1 - ang0) / 4
        check_ang = []
        check_Pts = []
        fit_error = []
        
        for i in range(1, 4):
            check_ang.append(ang0 + check_step * i)
            check_Pts.append(self.Ellipse_Point(check_ang[-1]))
            fit_error.append(biarc.get_biarc_fitting_error(check_Pts[-1]))

        if max(fit_error) >= tol:
            return 0
        else:
            return 1            

    def Ellipse_Grundwerte(self):
        #Weitere Grundwerte der Ellipse, die nur einmal ausgerechnet werden m�ssen
        #Other values of the ellipse that are calculated only once
        self.rotation = atan2(self.vector.y, self.vector.x)
        self.a = sqrt(self.vector.x ** 2 + self.vector.y ** 2)
        self.b = self.a * self.ratio
        
        #Aus dem Vorzeichen von dir den extend ausrechnen
        #Calculate angle to extend
        self.ext = self.AngE - self.AngS
        #self.ext=self.ext%(-2*pi)
        #self.ext-=floor(self.ext/(2*pi))*(2*pi)
   
    def Ellipse_Point(self, alpha=0):#Point(0,0)
        #gro�e Halbachse, kleine Halbachse, rotation der Ellipse (rad), Winkel des Punkts in der Ellipse (rad)
        #Semi-major axis, minor axis, rotation of the ellipse (rad), the point in the ellipse angle (rad) ???
        Ex = self.a * cos(alpha) * cos(self.rotation) - self.b * sin(alpha) * sin(self.rotation);
        Ey = self.a * cos(alpha) * sin(self.rotation) + self.b * sin(alpha) * cos(self.rotation);
        return Point(self.center.x + Ex, self.center.y + Ey)
    
    def Ellipse_Tangent(self, alpha=0):#Point(0,0)
        #gro�e Halbachse, kleine Halbachse, rotation der Ellipse (rad), Winkel des Punkts in der Ellipse (rad)
        #Semi-major axis, minor axis, rotation of the ellipse (rad), the point in the ellipse angle (rad) ???
        phi = atan2(self.a * sin(alpha), self.b * cos(alpha)) + self.rotation + pi / 2
        return phi
