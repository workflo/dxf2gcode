#!/usr/bin/python
# -*- coding: cp1252 -*-
#
from math import radians, cos, sin, tan, atan, atan2, sqrt, pow, pi
from clsGeometrie import PointClass
from clsBiArc import BiarcClass

#======================================================================
class EllipseClass:
    def __init__(self, center=PointClass(0,0), a=1, b=0.5, rot=0):
        #Mittelpunkt, große Halbachse, kleine Halbachse, Rotation der Ellipse (rad)
        self.a = a
        self.b = b
        self.rot = rot
        self.Center = center

    def EPoint(self, alfa=0.00):#Winkel als rad!  return PointClass
        #Winkel des Punkts in der Ellipse (rad)
        #große Halbachse, kleine Halbachse, Rotation der Ellipse (rad), Winkel des Punkts in der Ellipse (rad)
        Ex = self.a*cos(alfa) * cos(self.rot) - self.b*sin(alfa) * sin(self.rot);
        Ey = self.a*cos(alfa) * sin(self.rot) + self.b*sin(alfa) * cos(self.rot);
        return PointClass(self.Center.x+Ex, self.Center.y+Ey)

    def Steigung(self, alfa=0.00):#Winkel als rad!  return 0.00
        #Winkel des Punkts in der Ellipse (rad)
        winkel = pi/2 + atan( (self.a**2 / self.b**2) * tan(alfa) )
        if ((alfa>pi/2)  and  (alfa<=pi*3/2)):
            winkel += pi
        #hier winkel = Tangente-Steigung der geraden Ellipse im Bereich 0 bis 2*pi
        winkel += self.rot
        if (winkel>2*pi):
            winkel -= 2*pi
        #hier winkel = Tangente-Steigung der gedrehten Ellipse im Bereich 0 bis 2*pi
        if (winkel>pi):
            winkel -= 2*pi
        #jetzt liegt die Steigung im Bereich -pi bis pi
        return winkel

    def BiArc(self, alfa=0.00, beta=0.00):#Winkel von, bis als rad!  return BiarcClass
        if (alfa > beta):
            alfa, beta = swap(alfa, beta)
        return BiarcClass(self.EPoint(alfa),  \
                          self.Steigung(alfa), \
                          self.EPoint(beta),  \
                          self.Steigung(beta) ) 
    def swap(a, b):
        return b, a
