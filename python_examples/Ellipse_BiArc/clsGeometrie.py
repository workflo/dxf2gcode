#!/usr/bin/python
# -*- coding: cp1252 -*-
#
from math import radians, cos, sin,tan, atan2, sqrt, pow, pi, atan2

#======================================================================
class PointClass:
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
    def __str__(self):
        return ('(%6.2f; %6.2f)' %(self.x,self.y))
    def __cmp__(self, other) : 
      return (self.x == other.x) and (self.y == other.y)
    def __add__(self, other): # add to another point
        return PointClass(self.x+other.x, self.y+other.y)
    def __rmul__(self, other):
        return PointClass(other * self.x,  other * self.y)
    def distance(self,other):
        return sqrt(pow(self.x-other.x,2)+pow(self.y-other.y,2))
    def norm_angle(self,other):
        return atan2(other.y-self.y,other.x-self.x)
    def isintol(self,other,tol):
        return (abs(self.x-other.x)<=tol) & (abs(self.y-other.y)<tol)
    def transform_to_Norm_Coord(self,other,alpha):
        xt=other.x+self.x*cos(alpha)+self.y*sin(alpha)
        yt=other.y+self.x*sin(alpha)+self.y*cos(alpha)
        return PointClass(x=xt,y=yt)
    def plot2gcode(self):
        return ('\nPoint:   X ->%6.2f  Y ->%6.2f' %(self.x,self.y))

#======================================================================
class ArcGeo:
    def __init__(self,Pa,Pe,O,r,s_ang,e_ang):
        self.Pa=Pa
        self.Pe=Pe
        self.O=O
        self.r=r
        self.s_ang=s_ang
        self.e_ang=e_ang

    def __str__(self):
        return ("ARC:\n")+\
               ("  Pa : %s; s_ang: %0.3f\n" %(self.Pa,self.s_ang))+\
               ("  Pe : %s; e_ang: %0.3f\n" %(self.Pe,self.e_ang))+\
               ("  O  : %s; r: %0.3f\n" %(self.O,self.r))

    def plot2plot(self, plot):
        #plot.Arc(xy=[self.O.x,self.O.y],width=self.r*2,height=self.r*2)
        plot.plot([self.Pa.x,self.Pe.x],\
                  [self.Pa.y,self.Pe.y],'-g')
        #plot.plot([self.O.x], [self.O.y],'or') # Mittelpunkte

    def plot2can(self,canvas,p0,sca,tag):
        pass # eine Idee, alles lässt sich auf Arc's und Lines zurückführen -
             # und die erzeugen ihre Zeichnung und GCode selbst

    def plot2gcode(self,paras,sca,p0,dir,axis1,axis2):
        pass # eine Idee, alles lässt sich auf Arc's und Lines zurückführen -
             # und die erzeugen ihre Zeichnung und GCode selbst

#======================================================================
class LineGeo:
    def __init__(self,Pa,Pe):
        self.Pa=Pa
        self.Pe=Pe

    def __str__(self):
        return ("LINE: %s - %s" %(self.Pa, self.Pe))

    def plot2plot(self, plot):
        plot.plot([self.Pa.x,self.Pe.x],\
                  [self.Pa.y,self.Pe.y],'-dm')

    def plot2can(self,canvas,p0,sca,tag):
        pass # eine Idee, alles lässt sich auf Arc's und Lines zurückführen -
             # und die erzeugen ihre Zeichnung und GCode selbst

    def plot2gcode(self,paras,sca,p0,dir,axis1,axis2):
        pass # eine Idee, alles lässt sich auf Arc's und Lines zurückführen -
             # und die erzeugen ihre Zeichnung und GCode selbst
