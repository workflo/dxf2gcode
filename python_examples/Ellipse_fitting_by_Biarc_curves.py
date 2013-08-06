#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#NURBS_fittin_by_Biarc_curves
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
from math import sqrt, sin, cos, tan, atan, atan2, radians, degrees, pi, floor, ceil
import sys

class EllipseClass:
    def __init__(self):
        self.center = PointClass(36.832,-56.715) #Mittelpunkt der Geometrie
        self.vector = PointClass(20,20) #vector A = große Halbachse a, = Drehung der Ellipse
                                      # http://de.wikipedia.org/wiki/Gro%C3%9Fe_Halbachse
        self.ratio = 0.5                #Verhältnis der kleinen zur großen Halbachse (b/a)
        self.AngS = 0                 #Startwinkel beim zeichnen eines Ellipsensegments
        self.AngE = radians(360)      #Endwinkel (Winkel im DXF als Radians!)
        self.Points=[]
        self.Points.append(self.center)
        self.geo=[]
        tol=0.01
        
        self.Ellipse_Grundwerte()
        self.Ellipse_2_Arcs(tol)

    def __str__(self):
        s=('center: '+str(self.center) +'\n' + \
        'vector: '+str(self.vector) +'\n' + \
        'ratio:  '+str(self.ratio) +'\n' + \
        'Winkel: '+str(degrees(self.AngS))+' -> '+str(degrees(self.AngE))+'\n' + \
        'a:      '+str(self.a) +'\n' + \
        'b:      '+str(self.b) +'\n')
        return s

    def Ellipse_2_Arcs(self, tol):

        #Anfangswert für Anzahl Elemente
        num_elements=2
        intol=False   

        while not(intol):
            intol=True
            
            #Anfangswete Ausrechnen
            angle = self.AngS
            Pa = self.Ellipse_Point(angle)
            tana= self.Ellipse_Tangent(angle)

            self.geo=[]
            self.PtsVec=[]
            self.PtsVec.append([Pa,tana])
            
            for sec in range(num_elements*2):
                #Neuer Winkel errechnen
                angle+=-(2*pi)/num_elements/2

                #Endwerte errechnen            
                Pb = self.Ellipse_Point(angle)
                tanb= self.Ellipse_Tangent(angle)

                #Biarc erstellen und an geo anhängen        
                biarcs=BiarcClass(Pa,tana,Pb,tanb,tol/100)
                self.geo+=biarcs.geos[:]             

                #Letzer Wert = Startwert
                Pa=Pb
                tana=tanb
                
                self.PtsVec.append([Pa,tana])

                if not(self.check_ellipse_fitting_tolerance(biarcs,tol,angle,angle+(2*pi)/num_elements/2)):
                    intol=False
                    num_elements+=1
                    break
                      
    def check_ellipse_fitting_tolerance(self,biarc,tol,ang0,ang1):
        check_step=(ang1-ang0)/4
        check_ang=[]
        check_Pts=[]
        fit_error=[]
        
        for i in range(1,4):
            check_ang.append(ang0+check_step*i)
            check_Pts.append(self.Ellipse_Point(check_ang[-1]))
            fit_error.append(biarc.get_biarc_fitting_error(check_Pts[-1]))

        if max(fit_error)>=tol:
            return 0
        else:
            return 1            

    def Ellipse_Grundwerte(self):
        #Weitere Grundwerte der Ellipse, die nur einmal ausgerechnet werden müssen
        self.rotation = atan2(self.vector.y, self.vector.x)
        self.a = sqrt(self.vector.x**2 + self.vector.y**2)
        self.b = self.a * self.ratio

    def Ellipse_Point(self, alpha=0):#PointClass(0,0)
        #große Halbachse, kleine Halbachse, rotation der Ellipse (rad), Winkel des Punkts in der Ellipse (rad)
        Ex = self.a*cos(alpha) * cos(self.rotation) - self.b*sin(alpha) * sin(self.rotation);
        Ey = self.a*cos(alpha) * sin(self.rotation) + self.b*sin(alpha) * cos(self.rotation);
        return PointClass(self.center.x+Ex, self.center.y+Ey)
    
    def Ellipse_Tangent(self, alpha=0):#PointClass(0,0)
        #große Halbachse, kleine Halbachse, rotation der Ellipse (rad), Winkel des Punkts in der Ellipse (rad)
        phi=atan2(self.a*sin(alpha),self.b*cos(alpha))+self.rotation-pi/2
        return phi
    
class BiarcClass:
    def __init__(self,Pa=[],tan_a=[],Pb=[],tan_b=[],min_len=1e-5):
        min_alpha=1e-4      #Winkel ab welchem Gerade angenommen wird inr rad
        max_r=5e3           #Max Radius ab welchem Gerade angenommen wird (10m)
        
        self.Pa=Pa
        self.tan_a=tan_a
        self.Pb=Pb
        self.tan_b=tan_b
        self.l=0.0
        self.shape=None
        self.geos=[]
        self.k=0.0

        #Errechnen der Winkel, Länge und Shape
        norm_angle,self.l=self.calc_normal(self.Pa,self.Pb)

        alpha,beta,self.teta,self.shape=self.calc_diff_angles(norm_angle,\
                                                              self.tan_a,\
                                                              self.tan_b,\
                                                              min_alpha)
        
        if(self.l<min_len):
            self.shape="Zero"
            print "Zero"
            pass
        elif(self.shape=="LineGeo"):
            #Erstellen der Geometrie
            self.shape="LineGeo"
            self.geos.append(LineGeo(self.Pa,self.Pb))
        else:
            #Berechnen der Radien, Mittelpunkte, Zwichenpunkt            
            r1, r2=self.calc_r1_r2(self.l,alpha,beta,self.teta)
            
            if (abs(r1)>max_r)or(abs(r2)>max_r):
                #Erstellen der Geometrie
                self.shape="LineGeo"
                self.geos.append(LineGeo(self.Pa,self.Pb))
                return 
          
            O1, O2, k =self.calc_O1_O2_k(r1,r2,self.tan_a,self.teta)
            
            #Berechnen der Start und End- Angles für das drucken
            s_ang1,e_ang1=self.calc_s_e_ang(self.Pa,O1,k)
            s_ang2,e_ang2=self.calc_s_e_ang(k,O2,self.Pb)

            #Berechnen der Richtung und der Extend
            dir_ang1=(tan_a-s_ang1)%(-2*pi)
            dir_ang1-=ceil(dir_ang1/(pi))*(2*pi)

            dir_ang2=(tan_b-e_ang2)%(-2*pi)
            dir_ang2-=ceil(dir_ang2/(pi))*(2*pi)
            
            
            #Erstellen der Geometrien          
            self.geos.append(ArcGeo(Pa=self.Pa,Pe=k,O=O1,r=r1,\
                                    s_ang=s_ang1,e_ang=e_ang1,dir=dir_ang1))
            self.geos.append(ArcGeo(Pa=k,Pe=self.Pb,O=O2,r=r2,\
                                    s_ang=s_ang2,e_ang=e_ang2,dir=dir_ang2)) 

    def calc_O1_O2_k(self,r1,r2,tan_a,teta):
        #print("r1: %0.3f, r2: %0.3f, tan_a: %0.3f, teta: %0.3f" %(r1,r2,tan_a,teta))
        #print("N1: x: %0.3f, y: %0.3f" %(-sin(tan_a), cos(tan_a)))
        #print("V: x: %0.3f, y: %0.3f" %(-sin(teta+tan_a),cos(teta+tan_a)))

        O1=PointClass(x=self.Pa.x-r1*sin(tan_a),\
                      y=self.Pa.y+r1*cos(tan_a))
        k=PointClass(x=self.Pa.x+r1*(-sin(tan_a)+sin(teta+tan_a)),\
                     y=self.Pa.y+r1*(cos(tan_a)-cos(tan_a+teta)))
        O2=PointClass(x=k.x+r2*(-sin(teta+tan_a)),\
                      y=k.y+r2*(cos(teta+tan_a)))
        return O1, O2, k

    def calc_normal(self,Pa,Pb):
        norm_angle=Pa.norm_angle(Pb)
        l=Pa.distance(Pb)
        return norm_angle, l        

    def calc_diff_angles(self,norm_angle,tan_a,tan_b,min_alpha):
        #print("Norm angle: %0.3f, tan_a: %0.3f, tan_b %0.3f" %(norm_angle,tan_a,tan_b))
        alpha=(norm_angle-tan_a)   
        beta=(tan_b-norm_angle)
        alpha,beta= self.limit_angles(alpha,beta)

        if alpha*beta>0.0:
            shape="C-shaped"
            teta=alpha
        elif abs(alpha-beta)<min_alpha:
            shape="LineGeo"
            teta=alpha
        else:
            shape="S-shaped"
            teta=(3*alpha-beta)/2
            
        return alpha, beta, teta, shape    

    def limit_angles(self,alpha,beta):
        #print("limit_angles: alpha: %s, beta: %s" %(alpha,beta))
        if (alpha<-pi):
           alpha += 2*pi
        if (alpha>pi):
           alpha -= 2*pi
        if (beta<-pi):
           beta += 2*pi
        if (beta>pi):
           beta -= 2*pi
        while (alpha-beta)>pi:
            alpha=alpha-2*pi
        while (alpha-beta)<-pi:
            alpha=alpha+2*pi
        #print("   -->>       alpha: %s, beta: %s" %(alpha,beta))         
        return alpha,beta
            
    def calc_r1_r2(self,l,alpha,beta,teta):
        #print("alpha: %s, beta: %s, teta: %s" %(alpha,beta,teta))
        r1=(l/(2*sin((alpha+beta)/2))*sin((beta-alpha+teta)/2)/sin(teta/2))
        r2=(l/(2*sin((alpha+beta)/2))*sin((2*alpha-teta)/2)/sin((alpha+beta-teta)/2))
        return r1, r2
    
    def calc_s_e_ang(self,P1,O,P2):
        s_ang=O.norm_angle(P1)
        e_ang=O.norm_angle(P2)
        return s_ang, e_ang
    
     
    def get_biarc_fitting_error(self,Pt):
        #Abfrage in welchem Kreissegment der Punkt liegt:
        w1=self.geos[0].O.norm_angle(Pt)
        if (w1>=min([self.geos[0].s_ang,self.geos[0].e_ang]))and\
           (w1<=max([self.geos[0].s_ang,self.geos[0].e_ang])):
            diff=self.geos[0].O.distance(Pt)-abs(self.geos[0].r)
        else:
            diff=self.geos[1].O.distance(Pt)-abs(self.geos[1].r)
        return abs(diff)
            
    def __str__(self):
        s= ("\nBiarc Shape: %s" %(self.shape))+\
           ("\nPa : %s; Tangent: %0.3f" %(self.Pa,self.tan_a))+\
           ("\nPb : %s; Tangent: %0.3f" %(self.Pb,self.tan_b))+\
           ("\nteta: %0.3f, l: %0.3f" %(self.teta,self.l))
        for geo in self.geos:
            s+=str(geo)
        return s
    
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
        print self
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


    def make_ellipse_biarc_plot(self,ellipse):
        self.plot1 = self.figure.add_subplot(111)
        self.plot1.set_title("Ellipse, BIARC Fitting Algorithms: ")

        arrow_len=4
        arrow_width=arrow_len*0.05


        self.plot1.hold(True)
        for PtsVec in ellipse.PtsVec:
            (PtsVec[0].x)
            (PtsVec[0].y)
            self.plot1.plot([PtsVec[0].x],[PtsVec[0].y],'xr')
            
            self.plot1.arrow(PtsVec[0].x,PtsVec[0].y,\
                             cos(PtsVec[1])*arrow_len,\
                             sin(PtsVec[1])*arrow_len,\
                             width=arrow_width)        

        for geo in ellipse.geo:
            geo.plot2plot(self.plot1)
        self.plot1.axis('scaled')     
        self.canvas.show()
    

if 1:
    master = Tk()
    #Wenn der NURBS erstellt und ausgedrückt werden soll
    Pl=PlotClass(master)

    if 1:
        ellipsefitting=EllipseClass()
        master.title("NURBS Ellipse Fitting in PYTHON")
        Pl.make_ellipse_biarc_plot(ellipsefitting)
        
    master.mainloop()


     
