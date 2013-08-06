#!/usr/bin/python
# -*- coding: cp1252 -*-
#
from math import radians, cos, sin, tan, atan2, sqrt, pow, pi
from clsGeometrie import PointClass
from clsGeometrie import ArcGeo
from clsGeometrie import LineGeo

class BiarcClass:
    def __init__(self,Pa=[],tan_a=[],Pb=[],tan_b=[]):
        min_len=1e-5        #Min Abstand für doppelten Punkt
        min_alpha=1e-5      #Winkel ab welchem Gerade angenommen wird inr rad
        max_r=1e4           #Max Radius ab welchem Gerade angenommen wird (10m)
        
        self.Pa=Pa
        self.tan_a=tan_a
        self.Pb=Pb
        self.tan_b=tan_b
        self.l=0.0
        self.shape=None
        self.geos=[]
        self.k=0.0
        #norm_angle=0; self.alpha=0; self.beta=0

        #Errechnen der Winkel, Länge und Shape
        norm_angle,self.l=self.calc_normal(self.Pa,self.Pb)     
        alpha,beta,self.teta,self.shape=self.calc_diff_angles(norm_angle,\
                                                              self.tan_a,\
                                                              self.tan_b,\
                                                              min_alpha)

        if(self.l<min_len):
            self.shape="Zero"
            pass
        elif(self.shape=="Line"):
            #Erstellen der Geometrie
            self.shape="Line"
            self.geos.append(LineGeo(self.Pa,self.Pb)) 
        else:
            #Berechnen der Radien, Mittelpunkte, Zwichenpunkt            
            r1, r2=self.calc_r1_r2(self.l,alpha,beta,self.teta)
            
            if (abs(r1)>max_r):
                #Erstellen der Geometrie
                self.shape="Line"
                self.geos.append(LineGeo(self.Pa,self.Pb))
                return 
                
            O1, O2, k =self.calc_O1_O2_k(r1,r2,self.tan_a,self.teta)
            
            #Berechnen der Start und End- Angles für das drucken
            s_ang1,e_ang1=self.calc_s_e_ang(self.Pa,O1,k)
            s_ang2,e_ang2=self.calc_s_e_ang(k,O2,self.Pb)

            self.geos.append(ArcGeo(self.Pa,k,O1,r1,s_ang1,e_ang1))
            self.geos.append(ArcGeo(k,self.Pb,O2,r2,s_ang2,e_ang2)) 

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
        alpha=(norm_angle-tan_a)   
        beta=(tan_b-norm_angle)
        alpha,beta= self.limit_angles(alpha,beta)
        if alpha*beta>0.0:
            shape="C-shaped"
            teta=alpha
        elif abs(alpha-beta)<min_alpha:
            shape="Line"
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
        #print("calc_r1_r2: alpha: %s, beta: %s, teta: %s, 2pi: %s" %(alpha,beta,teta,2*pi))
        r1=(l/(2*sin((alpha+beta)/2))*sin((beta-alpha+teta)/2)/sin(teta/2))
        r2=(l/(2*sin((alpha+beta)/2))*sin((2*alpha-teta)/2)/sin((alpha+beta-teta)/2))
        return r1, r2
    
    def calc_s_e_ang(self,P1,O,P2):
        s_ang=O.norm_angle(P1)
        e_ang=O.norm_angle(P2)
        return s_ang, e_ang
    
    def check_biarc_fitting_tolerance(self,NURBS,epsilon,u0,u1):
        check_step=(u1-u0)/5
        check_u=[]
        check_Pts=[]
        fit_error=[]
        
        for i in range(1,5):
            check_u.append(u0+check_step*i)
            check_Pts.append(NURBS.NURBS_evaluate(n=0,u=check_u[-1]))
            fit_error.append(self.get_biarc_fitting_error(check_Pts[-1]))
        if max(fit_error)>=epsilon:
            #print self
            #print fit_error
            #print "Nein"
            return 0
        else:
            #print "Ja"
            #print self
            return 1
        
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