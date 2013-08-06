#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#Kegelstump_Abwicklung_2dxf.py
#Programmer: Christian Kohlöffel
#E-mail:     n/A
#
#Copyright 2008 Christian Kohlöffel
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


import matplotlib
#matplotlib see: http://matplotlib.sourceforge.net/ and  http://www.scipy.org/Cookbook/Matplotlib/
#numpy      see: http://numpy.scipy.org/ and http://sourceforge.net/projects/numpy/
matplotlib.use('TkAgg')

from matplotlib.numerix import arange, sin, pi
from matplotlib.axes import Subplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

from Tkconstants import TOP, BOTH, BOTTOM, LEFT, RIGHT,GROOVE
from Tkinter import Tk, Button, Frame
from math import sqrt, sin, cos, tan, tanh, atan, radians, degrees, pi, floor, ceil
import sys


class KegelstClass:
    def __init__(self):
        #Max Abweichung für die Biarc Kurve
        self.Dm_oben=10.0
        self.Dm_unten=20.0
        self.Hoehe=10.0
        self.Winkel_oben=radians(45.0)
        self.Winkel_unten=radians(0.0)

        #Darstellungsdetail (Segmente pro 360°)        
        self.segments=20
        self.geo=[]

        #Berechnung der Standardwerte
        self.calc_SchraegerSchnitt()

        #Berechnung von Werten und erstellen der Geometrien
        step=10
        points,radius=self.SchrSchn_u.calc_point(0.0)

        for i in range(step,360+step,step):
            pointe,radius=self.SchrSchn_u.calc_point(radians(i))
            self.geo.append(LineGeo(points,pointe))
            points=pointe
            
                     
        #Berechnung von Werten und erstellen der Geometrien
        step=10
        points,radius=self.SchrSchn_o.calc_point(0.0)

        for i in range(step,360+step,step):
            pointe,radius=self.SchrSchn_o.calc_point(radians(i))
            self.geo.append(LineGeo(points,pointe))
            points=pointe
            
            

##        #Berechnen des Startpunkts:
##        self.phi_kurve_oben=[0]
##        self.kurve_oben=[self.abstand_schnittkante_zu_spitze(\
##            0,self.schnitthoehe_oben,self.schnittwinkel_oben)]
##
##        for i in range(self.segments):
##            phi=radians(360)/self.segments*(i+1)
##            self.phi_kurve_oben.append(phi)
##            self.kurve_oben.append(self.abstand_schnittkante_zu_spitze(\
##            phi,self.schnitthoehe_oben,self.schnittwinkel_oben))
##
##            Pa=PointClass(self.phi_kurve_oben[-2],self.kurve_oben[-2])
##            Pe=PointClass(self.phi_kurve_oben[-1],self.kurve_oben[-1])
##            
##            self.geo.append(LineGeo(Pa,Pe))

    def calc_SchraegerSchnitt(self):
        #Sonderfall Zero Division
        if self.Dm_oben==self.Dm_unten:
            self.sch_winkel=radians(90.0)
        else:
            self.sch_winkel=atan(self.Hoehe*2/(-self.Dm_oben+self.Dm_unten))
            
        self.SchrSchn_u=SchraegerSchnitt(dm=self.Dm_unten,a1=self.sch_winkel,a2=self.Winkel_unten)
        self.SchrSchn_o=SchraegerSchnitt(dm=self.Dm_oben,a1=self.sch_winkel,a2=self.Winkel_oben)
        

        
    def __str__(self):
        return("DM_oben:      %0.1f\n" %self.Dm_oben)+\
            ("Dm_unten:     %0.1f\n" %self.Dm_unten)+\
            ("Hoehe:        %0.1f\n" %self.Hoehe)+\
            ("Winkel_oben:  %0.1f\n" %degrees(self.Winkel_oben))+\
            ("Winkel_unten: %0.1f\n" %degrees(self.Winkel_unten))+\
            ("sch_winkel:   %0.1f\n" %degrees(self.sch_winkel))+\
            ("Schnitt unten:\n%s" %self.SchrSchn_u)+\
            ("Schnitt oben:\n%s" %self.SchrSchn_o)

             
class SchraegerSchnitt:
    def __init__(self,dm=20,a1=0,a2=0):
        self.dm=dm
        self.a1=a1
        self.a2=a2
        
        #Berechnen der Funktion
        self.calc_std_parameters()



##        print self        
##        print ("vers:   %0.2f \n" %self.vers)+\
##              ("vers_h: %0.2f \n" %self.vers_h)+\
##              ("vers_d: %0.2f \n" %self.vers_d)+\
##              ("dmv:    %0.2f \n" %self.dmv)

    def calc_point(self,phi=0.0,rotation=0.0):#PointClass(0,0),Radius
        #große Halbachse, kleine Halbachse, rotation der Ellipse (rad), Winkel des Punkts in der Ellipse (rad)
        Ex = self.De*cos(phi) * cos(rotation) - self.de*sin(phi) * sin(rotation)+self.vers_d*cos(rotation);
        Ey = self.De*cos(phi) * sin(rotation) + self.de*sin(phi) * cos(rotation)+self.vers_d*sin(rotation);
        Radius=sqrt(Ex**2+Ey**2)
        return PointClass(Ex, Ey),Radius
              
    def calc_std_parameters(self):
        #Berechnung der langen Seite der Ellipse
        self.De1=self.dm*sin(radians(180)-self.a1)/(2*sin(self.a1-self.a2))
        self.De2=self.dm*sin(self.a1)/(2*sin(radians(180)-self.a1-self.a2))
        self.De=self.De1+self.De2

        #Berechnung des Versatzes von der Mittellinie
        self.vers=(self.De2-(self.De/2))
        self.vers_h=self.vers*sin(self.a2)
        self.vers_d=self.vers*cos(self.a2)

        #Berechnung der kurzen Seite der Ellipse        
        self.dmv=self.dm-2*self.vers_h/tan(self.a1)
        self.de=2*sqrt((self.dmv/2)**2-(self.vers_d/2)**2)
    def __str__(self):
        return("dm:           %0.2f\n" %self.dm)+\
            ("a1:           %0.2f\n" %degrees(self.a1))+\
            ("a2:           %0.2f\n" %degrees(self.a2))+\
            ("De:           %0.2f\n" %self.De)+\
            ("de:           %0.2f\n" %self.de)
    
class ArcGeo:
    def __init__(self,Pa=None,Pe=None,O=None,r=1,s_ang=None,e_ang=None,dir=1):
        self.type="ArcGeo"
        self.Pa=Pa
        self.Pe=Pe
        self.O=O
        self.r=abs(r)

        #Falls nicht übergeben dann Anfangs- und Endwinkel ausrechen            
        if type(s_ang)==type(None):
            s_ang=O.norm_angle(Pa)
        if type(e_ang)==type(None):
            e_ang=O.norm_angle(Pe)

        #Aus dem Vorzeichen von dir den extend ausrechnen
        self.ext=e_ang-s_ang
        if dir>0.0:
            self.ext=self.ext%(-2*pi)
            self.ext-=floor(self.ext/(2*pi))*(2*pi)
        else:
            self.ext=self.ext%(-2*pi)
            self.ext+=ceil(self.ext/(2*pi))*(2*pi)
                   
        self.s_ang=s_ang
        self.e_ang=e_ang
        self.length=self.r*abs(self.ext)
                   
    def plot2plot(self, plot):

        x=[]; y=[]
        #Alle 6 Grad ein Linien Segment Drucken
        segments=int((abs(degrees(self.ext))//6)+1)
        for i in range(segments+1):
            ang=self.s_ang+i*self.ext/segments
            x.append(self.O.x+cos(ang)*abs(self.r))
            y.append(self.O.y+sin(ang)*abs(self.r))
            
        plot.plot(x,y,'-g')
        #plot.plot([x[0],x[-1]],[y[0],y[-1]],'cd')
        plot.plot([self.Pa.x,self.Pe.x],[self.Pa.y,self.Pe.y],'cd')

    def __str__(self):
        return ("\nARC")+\
               ("\nPa : %s; s_ang: %0.5f" %(self.Pa,self.s_ang))+\
               ("\nPe : %s; e_ang: %0.5f" %(self.Pe,self.e_ang))+\
               ("\nO  : %s; r: %0.3f" %(self.O,self.r))+\
               ("\next  : %0.5f; length: %0.5f" %(self.ext,self.length))


class LineGeo:
    def __init__(self,Pa,Pe):
        self.type="LineGeo"
        self.Pa=Pa
        self.Pe=Pe
        self.length=self.Pa.distance(self.Pe)

    def get_start_end_points(self,direction):
        if direction==0:
            punkt=self.Pa
            angle=self.Pe.norm_angle(self.Pa)
        elif direction==1:
            punkt=self.Pe
            angle=self.Pa.norm_angle(self.Pe)
        return punkt, angle

    def plot2plot(self, plot):
        plot.plot([self.Pa.x,self.Pe.x],[self.Pa.y,self.Pe.y],'-dm')
        
    def distance2point(self,point):
        AE=self.Pa.distance(self.Pe)
        AP=self.Pa.distance(point)
        EP=self.Pe.distance(point)
        AEPA=(AE+AP+EP)/2
        return abs(2*sqrt(abs(AEPA*(AEPA-AE)*(AEPA-AP)*(AEPA-EP)))/AE)
            
    def __str__(self):
        return ("\nLINE")+\
               ("\nPa : %s" %self.Pa)+\
               ("\nPe : %s" %self.Pe)+\
               ("\nlength: %0.5f" %self.length) 

class PointClass:
    def __init__(self,x=0,y=0):
        self.x=x
        self.y=y
    def __str__(self):
        return ('X ->%6.4f  Y ->%6.4f' %(self.x,self.y))
    def __cmp__(self, other) : 
      return (self.x == other.x) and (self.y == other.y)
    def __neg__(self):
        return -1.0*self
    def __add__(self, other): # add to another point
        return PointClass(self.x+other.x, self.y+other.y)
    def __sub__(self, other):
        return self + -other
    def __rmul__(self, other):
        return PointClass(other * self.x,  other * self.y)
    def __mul__(self, other):
        if type(other)==list:
            #Skalieren des Punkts
            return PointClass(x=self.x*other[0],y=self.y*other[1])
        else:
            #Skalarprodukt errechnen
            return self.x*other.x + self.y*other.y

    def unit_vector(self,Pto=None):
        diffVec=Pto-self
        l=diffVec.distance()
        return PointClass(diffVec.x/l,diffVec.y/l)
    def distance(self,other=None):
        if type(other)==type(None):
            other=PointClass(x=0.0,y=0.0)
        return sqrt(pow(self.x-other.x,2)+pow(self.y-other.y,2))
    def norm_angle(self,other=None):
        if type(other)==type(None):
            other=PointClass(x=0.0,y=0.0)
        return atan2(other.y-self.y,other.x-self.x)
    def isintol(self,other,tol):
        return (abs(self.x-other.x)<=tol) & (abs(self.y-other.y)<tol)
    def transform_to_Norm_Coord(self,other,alpha):
        xt=other.x+self.x*cos(alpha)+self.y*sin(alpha)
        yt=other.y+self.x*sin(alpha)+self.y*cos(alpha)
        return PointClass(x=xt,y=yt)
    def get_arc_point(self,ang=0,r=1):
        return PointClass(x=self.x+cos(radians(ang))*r,\
                          y=self.y+sin(radians(ang))*r)
    def triangle_height(self,other1,other2):
        #Die 3 Längen des Dreiecks ausrechnen
        a=self.distance(other1)
        b=other1.distance(other2)
        c=self.distance(other2)
        return sqrt(pow(b,2)-pow((pow(c,2)+pow(b,2)-pow(a,2))/(2*c),2))                

class PlotClass:
    def __init__(self,master=[]):
        
        self.master=master
 
        #Erstellen des Fensters mit Rahmen und Canvas
        self.figure = Figure(figsize=(7,7), dpi=100)
        self.frame_c=Frame(relief = GROOVE,bd = 2)
        self.frame_c.pack(fill=BOTH, expand=1,)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame_c)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(fill=BOTH, expand=1)

        #Erstellen der Toolbar unten
        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.frame_c)
        self.toolbar.update()
        self.canvas._tkcanvas.pack( fill=BOTH, expand=1)

    def make_erg_plot(self,kegelst):
        self.plot1 = self.figure.add_subplot(111)
        self.plot1.set_title("Kegelstumpf Abwicklung")

        self.plot1.hold(True)

        for geo in kegelst.geo:
            geo.plot2plot(self.plot1)
   
    

if 1:
    master = Tk()
    kegelst=KegelstClass()

    master.title("Kegelstumpfabwicklung 2 DXF")

    Pl=PlotClass(master)    
    Pl.make_erg_plot(kegelst)
  
    master.mainloop()


     
