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


#import matplotlib
#matplotlib see: http://matplotlib.sourceforge.net/ and  http://www.scipy.org/Cookbook/Matplotlib/
#numpy      see: http://numpy.scipy.org/ and http://sourceforge.net/projects/numpy/
#matplotlib.use('TkAgg')

import matplotlib

# uncomment the following to use wx rather than wxagg
#matplotlib.use('WX')
#from matplotlib.backends.backend_wx import FigureCanvasWx as FigureCanvas

# comment out the following to use wx rather than wxagg
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from matplotlib.figure import Figure

import wx

from math import sqrt, sin, cos, atan2, radians, degrees, pi, floor, ceil
import sys

class NURBSClass:
    def __init__(self,degree=0,Knots=[],Weights=None,CPoints=None):
        self.degree=degree                #Spline degree
        self.Knots=Knots                #Knoten Vektor
        self.CPoints=CPoints            #Kontrollpunkte des Splines [2D]
        self.Weights=Weights            #Gewichtung der Einzelnen Punkte

        #Initialisieren von errechneten Größen
        self.HCPts=[]                   #Homogenepunkte Vektoren [3D]           

        #Punkte in Homogene Punkte umwandeln
        self.CPts_2_HCPts()

        print self

        #Erstellen der BSplineKlasse zur Berechnung der Homogenen Punkte
        self.BSpline=BSplineClass(degree=self.degree,\
                                  Knots=self.Knots,\
                                  CPts=self.HCPts)

    def __str__(self):
        print len(self.Knots)
        print len(self.Weights)
        print len(self.CPoints)
        str='\ndegree:    %s' %self.degree
        
        for j in range((self.degree+1)/2):
            str=str+'\n'
            str=str+'Knots[%s]: %s' % (j,self.Knots[j])
        for i in range(len(self.Knots)-j-1):
            str=str+'\n'
            if i<len(self.CPoints):
                str=str+'  CPoints[%s]: %s' % (i,self.CPoints[i])
                str=str+'  Weights[%s]: %s' % (i,self.Weights[i])
            str=str+'Knots[%s]: %s' % (i+j+1,self.Knots[i+j+1])
            
        return str
    def check_NURBSParameters(self,tol):
        #Überprüfen des Knotenvektors
        #Suchen von mehrfachen Knotenpunkte (Anzahl über degree+1 => Fehler?!)
        knt_nr=1
        knt_vec=[[self.Knots[0]]]
        self.knt_m_change=[]
        
        while knt_nr < len(self.Knots):
            if self.Knots[knt_nr]==knt_vec[-1][-1]:
                knt_vec[-1].append(self.Knots[knt_nr])
            else:
                knt_vec.append([self.Knots[knt_nr]])
            knt_nr+=1
        
        for knt_spts in knt_vec:
            if (len(knt_spts)>self.degree+1):
                raise ValueError, "Same Knots Nr. bigger then degree+1"
            
            #Überprüfen der Steigungdifferenz vor und nach dem Punkt wenn Mehrfachknoten
            elif ((len(knt_spts)>self.degree)and(knt_spts[-1]>0.0)and(knt_spts[-1]<1.0)):
                temp, tangent0=self.NURBS_evaluate(n=1,u=knt_spts[0]-1e-12)
                temp, tangent1=self.NURBS_evaluate(n=1,u=knt_spts[0])
                if abs(tangent0-tangent1)>1e-6:
                    self.knt_m_change.append(knt_spts[0])
                               
        #Überprüfen der Kontrollpunkte
        #Suchen von mehrachen Kontrollpunkten (Anzahl über degree+2 => nicht errechnen
        ctlpt_nr=0
        ctlpt_vec=[[ctlpt_nr]]
        while ctlpt_nr < len(self.CPoints)-1:
            ctlpt_nr+=1
            if self.CPoints[ctlpt_nr].isintol(self.CPoints[ctlpt_vec[-1][-1]],tol):
                ctlpt_vec[-1].append(ctlpt_nr)
            else:
                ctlpt_vec.append([ctlpt_nr])
            
        self.ignor=[]
        for same_ctlpt in ctlpt_vec:
            if (len(same_ctlpt)>self.degree):
                self.ignor.append([self.Knots[same_ctlpt[0]+self.degree/2],\
                                   self.Knots[same_ctlpt[-1]+self.degree/2]])

        #raise ValueError, "Same Controlpoints Nr. bigger then degree+1"
        #print("Same Controlpoints Nr. bigger then degree+2")
        for ignor in self.ignor:
            print("Ignoring u's between u: %s and u: %s" %(ignor[0],ignor[1]))    
        
        if len(self.knt_m_change):
            print("Non steady Angles between Knots: %s" %self.knt_m_change)
                                               
    #Berechnen von eine Anzahl gleichmässig verteilter Punkte und bis zur ersten Ableitung
    def calc_curve(self,n=0, cpts_nr=20):
        #Anfangswerte für Step und u
        u=0; Points=[]; tang=[]

        step=self.Knots[-1]/(cpts_nr-1)        

        while u<=1.0:
            Pt,tangent=self.NURBS_evaluate(n=n,u=u)
            Points.append(Pt)
            
            #Für die erste Ableitung wird den Winkel der tangente errechnet
            if n>=1:
                tang.append(tangent)
            u+=step        
        if n>=1:
            return Points, tang
        else:
            return Points

    #Berechnen eines Punkts des NURBS und der ersten Ableitung
    def NURBS_evaluate(self,n=0,u=0):
        #Errechnen der korrigierten u's
        #cor_u=self.correct_u(u)
        
        #Errechnen der Homogenen Punkte bis zur n ten Ableitung         
        HPt=self.BSpline.bspline_ders_evaluate(n=n,u=u)

        #Punkt wieder in Normal Koordinaten zurück transformieren        
        Point=self.HPt_2_Pt(HPt[0])
        
        #Errechnen der ersten Ableitung wenn n>0 als Richtungsvektor
        dPt=[]
        tangent=None
        if n>0:
            #    w(u)*A'(u)-w'(u)*A(u)
            #dPt=---------------------
            #           w(u)^2
            for j in range(len(HPt[0])-1):
                dPt.append((HPt[0][-1]*HPt[1][j]-HPt[1][-1]*HPt[0][j])/
                           pow(HPt[0][-1],2))

            #Berechnen des Winkels des Vektors
            tangent=atan2(dPt[1],dPt[0])
                           
            return Point, tangent
        else:
            return Point


    #Umwandeln der NURBS Kontrollpunkte und Weight in einen Homogenen Vektor
    def CPts_2_HCPts(self):
        for P_nr in range(len(self.CPoints)):
            HCPtVec=[self.CPoints[P_nr].x*self.Weights[P_nr],\
                       self.CPoints[P_nr].y*self.Weights[P_nr],\
                       self.Weights[P_nr]]
            self.HCPts.append(HCPtVec[:])

    #Umwandeln eines Homogenen PunktVektor in einen Punkt
    def HPt_2_Pt(self,HPt):
        return PointClass(x=HPt[0]/HPt[-1],y=HPt[1]/HPt[-1])
            

class BSplineClass:
    def __init__(self,degree=0,Knots=[],CPts=[]):
        self.degree=degree
        self.Knots=Knots
        self.CPts=CPts

        self.Knots_len=len(self.Knots)        
        self.CPt_len=len(self.CPts[0])
        self.CPts_len=len(self.CPts)

        #Eingangsprüfung, ober KnotenAnzahl usw. passt        
        if  self.Knots_len< self.degree+1:
            raise ValueError, "degree greater than number of control points."
        if self.Knots_len != (self.CPts_len + self.degree+1):
            print ("shall be: %s" %(self.CPts_len + self.degree+1))
            print ("is: %s" %self.Knots_len)
            raise ValueError, "Knot/Control Point/degree number error."       

    #Berechnen von eine Anzahl gleichmässig verteilter Punkte bis zur n-ten Ableitung
    def calc_curve(self,n=0,cpts_nr=20):
        
        #Anfangswerte für Step und u
        u=0
        step=float(self.Knots[-1])/(cpts_nr-1)
        Points=[]

        #Wenn die erste Ableitung oder höher errechnet wird die ersten
        #Ableitung in dem tan als Winkel in rad gespeichert
        tang=[]

        while u<=self.Knots[-1]:
            CK=self.bspline_ders_evaluate(n=n,u=u)

            #Den Punkt in einem Punkt List abspeichern            
            Points.append(PointClass(x=CK[0][0],y=CK[0][1]))
            
            #Für die erste Ableitung wird den Winkel der tangente errechnet
            if n>=1:
                tang.append(atan2(CK[1][1],CK[1][0]))   
            u+=step

        return Points, tang
    
    #Modified Version of Algorithm A3.2 from "THE NURBS BOOK" pg.93
    def bspline_ders_evaluate(self,n=0,u=0):
        #Berechnung der Position im Knotenvektor        
        span=self.findspan(u)

        #Berechnen der Basis Funktion bis zur n ten Ableitung am Punkt u        
        dN=self.ders_basis_functions(span,u,n)

        p=self.degree
        du=min(n,p) 

        CK=[]
        dPts=[]
        for i in range(self.CPt_len):
            dPts.append(0.0)
        for k in range(n+1):
            CK.append(dPts[:])

        for k in range(du+1):
            for j in range(p+1):
                for i in range(self.CPt_len):
                    CK[k][i]+=dN[k][j]*self.CPts[span-p+j][i]
                    
        return CK

    #Algorithm A2.1 from "THE NURBS BOOK" pg.68
    def findspan(self,u):
        #Spezialfall wenn der Wert==Endpunkt ist
        if(u==self.Knots[-1]):
            return self.Knots_len-self.degree-2 #self.Knots_len #-1
        
        #Binäre Suche starten
        #(Der Interval von low zu high wird immer halbiert bis
        #wert zwischen im Intervall von Knots[mid:mi+1] liegt)
        low=self.degree
        high=self.Knots_len
        mid=(low+high)/2
        while ((u <self.Knots[mid])or(u>=self.Knots[mid+1])):
            if (u<self.Knots[mid]):
                high=mid
            else:
                low=mid
            mid=(low+high)/2
        return mid

    #Algorithm A2.3 from "THE NURBS BOOK" pg.72
    def ders_basis_functions(self,span,u,n):
        d=self.degree
        
        #initialisieren der a Matrix
        a=[]
        zeile=[]
        for j in range(d+1):
            zeile.append(0.0)
        a.append(zeile[:]); a.append(zeile[:])
        
        #initialisieren der ndu Matrix
        ndu=[]
        zeile=[]
        for i in range(d+1):
            zeile.append(0.0)
        for j in range(d+1):
            ndu.append(zeile[:])

        #initialisieren der ders Matrix
        ders=[]
        zeile=[]
        for i in range(d+1):
            zeile.append(0.0)    
        for j in range(n+1):
            ders.append(zeile[:])
            
        ndu[0][0]=1.0
        left=[0]
        right=[0]

        for j in range(1,d+1):
            #print('komisch span:%s, j:%s, u:%s, gesamt: %s' %(span,j,u,span+1-j))
            left.append(u-self.Knots[span+1-j])
            right.append(self.Knots[span+j]-u)
            saved=0.0
            for r in range(j):
                #Lower Triangle
                ndu[j][r]=right[r+1]+left[j-r]
                temp=ndu[r][j-1]/ndu[j][r]
                #Upper Triangle
                ndu[r][j]=saved+right[r+1]*temp
                saved=left[j-r]*temp
            ndu[j][j]=saved
            
        #Ergebniss aus S71
        #print("Ndu: %s" %ndu)
            
        #Load the basis functions
        for j in range(d+1):
            ders[0][j]=ndu[j][d]

        #This section computes the derivatives (Eq. [2.9])
        for r in range(d+1): #Loop over function index
            s1=0; s2=1  #Alternate rows in array a
            a[0][0]=1.0
            for k in range(1,n+1):
                der=0.0
                rk=r-k; pk=d-k
                
                #print("\nrk: %s" %rk), print("pk: %s" %pk), print("s1: %s" %s1)
                #print("s2: %s" %s2), print("r: %s" %r) ,print("k: %s" %k)
                #print("j: %s" %j)

                #wenn r-k>0 (Linker Term) und somit 
                if(r>=k):
                    a[s2][0]=a[s1][0]/ndu[pk+1][rk]                 #2te: a[0][0] 1/
                    #print("a[%s][0]=a[%s][0](%s)/ndu[%s][%s](%s)=%s" \
                    #      %(s2,s1,a[s1][0],pk+1,rk,ndu[pk+1][rk],a[s2][0]))
                    der=a[s2][0]*ndu[rk][pk]
                if (rk>=-1):
                    j1=1
                else:
                    j1=-rk
                if (r-1<=pk):
                    j2=k-1
                else:
                    j2=d-r

                #Hier geht er bei der ersten Ableitung gar nicht rein
                #print("j1:%s j2:%s" %(j1,j2))
                for j in range(j1,j2+1):
                    a[s2][j]=(a[s1][j]-a[s1][j-1])/ndu[pk+1][rk+j]
                    der+=a[s2][j]*ndu[rk+j][pk]
            
                if(r<=pk):
                    a[s2][k]=-a[s1][k-1]/ndu[pk+1][r]               #1/ u(i+p+1)-u(i+1)
                    der+=a[s2][k]*ndu[r][pk]                        #N(i+1)(p-1)
                    #print("a[%s][%s]=-a[%s][%s](%s)/ndu[%s][%s](%s)=%s" \
                    #      %(s2,k,s1,k-1,a[s1][k-1],pk+1,r,ndu[pk+1][r],a[s2][k]))
                    #print("ndu[%s][%s]=%s" %(r,pk,ndu[r][pk]))

                ders[k][r]=der
                #print("ders[%s][%s]=%s" %(k,r,der)) 
                j=s1; s1=s2; s2=j #Switch rows

                       
        #Multiply through by the the correct factors   
        r=d
        for k in range(1,n+1):
            for j in range(d+1):
                ders[k][j] *=r
            r*=(d-k)     
        return ders


class BiarcFittingClass:
    def __init__(self,degree, CPoints, Weights, Knots):
        #Max Abweichung für die Biarc Kurve
        self.epsilon=0.01
        self.epsilon_high=self.epsilon*0.03
        self.segments=50


        #NURBS Klasse initialisieren
        self.NURBS=NURBSClass(degree=degree,Knots=Knots,CPoints=CPoints,Weights=Weights)
        
        #Überprüfen der NURBS Parameter Überprüfung der NURBS Kontrollpunkte ob welche doppelt
        #Innerhalb der gegebenen Tolerans sind (=> Ignorieren)
        self.NURBS.check_NURBSParameters(self.epsilon)

        #High Accuracy Biarc fitting of NURBS        
        BiarcCurves, self.PtsVec=self.calc_high_accurancy_BiarcCurve()

        #Komprimieren der Biarc und der Linien
        self.Curve=self.analyse_and_compress(BiarcCurves)
           
    def analyse_and_compress(self,BiarcCurves):
        #Compress all to one curve
        Curves=[]
        for BiarcCurve in BiarcCurves:
            Curve=[]
            for Biarc in BiarcCurve:
                for geo in Biarc.geos:
                    Curve.append(geo)

            #print ("Vor Linie: Elemente: %0.0f" %len(Curve))
            Curve=self.compress_lines(Curve)
            #print ("Nach Linie: Elemente: %0.0f" %len(Curve))
            Curve=self.compress_biarcs(Curve)
            #print ("Nach Biarc: Elemente: %0.0f" %len(Curve))
            Curves+=Curve
        return Curves

    def compress_biarcs(self,Curves):
        NewCurve=[]
        tau=self.epsilon
        Pts=[]
        #Schleife für die Anzahl der Geometrirs
        for geo in Curves:
            NewCurve.append(geo)        
            #Wenn die Länge mindestens 3 sind
            if len(NewCurve)>=3:
                #Steigende Spirale
                if ((NewCurve[-3].type=="ArcGeo")\
                   and(NewCurve[-2].type=="ArcGeo")\
                   and(NewCurve[-1].type=="ArcGeo")):
                    Pts.append(geo.Pe)
                    if(NewCurve[-3].r<=NewCurve[-2].r)\
                        and(NewCurve[-2].r<=NewCurve[-1].r)\
                        and((NewCurve[-3].ext*NewCurve[-2].ext)>=0.0)\
                        and((NewCurve[-2].ext*NewCurve[-1].ext)>=0.0):
                        #print "Increasing"
                        anz=len(NewCurve)
                        triarc=NewCurve[anz-3:anz]
                        Arc0,Arc1= self.fit_triac_by_inc_biarc(triarc,tau)
                        diff=self.check_diff_to_pts(Pts,Arc0,Arc1)

                        #Überprüfen ob es in Toleranz liegt
                        try:
                            if max(diff)<self.epsilon:
                                tau=self.calc_active_tolerance_inc(self.epsilon,triarc,Arc0,Arc1)
                                del NewCurve[anz-3:anz]
                                NewCurve.append(Arc0)
                                NewCurve.append(Arc1)
                        except:
                            pass

                            
                    elif (NewCurve[-3].r>NewCurve[-2].r)\
                         and(NewCurve[-2].r>NewCurve[-1].r)\
                         and((NewCurve[-3].ext*NewCurve[-2].ext)>=0.0)\
                         and((NewCurve[-2].ext*NewCurve[-1].ext)>=0.0):
                        #print "Decreasing"
                        anz=len(NewCurve)
                        triarc=NewCurve[anz-3:anz]
                        Arc0,Arc1= self.fit_triac_by_dec_biarc(triarc,tau)
                        diff=self.check_diff_to_pts(Pts,Arc1,Arc0)
                        try:
                            if max(diff)<self.epsilon:
                                tau=self.calc_active_tolerance_dec(self.epsilon,triarc,Arc0,Arc1)

                                del NewCurve[anz-3:anz]
                                NewCurve.append(Arc0)
                                NewCurve.append(Arc1)
                        except:
                            pass
                  
                else:
                    Pts=[]
        return NewCurve
    
    def calc_active_tolerance_inc(self,tau,arc,Arc0,Arc1):
        V0=arc[0].Pa.unit_vector(arc[0].O)
        Vb=Arc1.Pa.unit_vector(Arc1.O)

        t_=(2*arc[0].r*tau+pow(tau,2))/\
            (2*(arc[0].r+(arc[0].r+tau)*V0*Vb))
        
        te=arc[0].r+t_-(Arc0.Pe-(arc[0].O+(t_*V0))).distance()

        tm=arc[1].O.distance(Arc0.Pe)-abs(arc[1].r)
        if tm<0.0:
            tf=tau
        else:   
            tf=tau-tm
        #print("tm: %0.3f; te: %0.3f; tau: %0.3f" %(tm,te,tau))
        epsilon=min([te,tf,tau])

        if epsilon<0.0:
            epsilon=0.0
        
        return epsilon

    def calc_active_tolerance_dec(self,tau,arc,Arc0,Arc1):
        V0=arc[2].Pa.unit_vector(arc[2].O)
        Vb=Arc1.Pa.unit_vector(Arc1.O)

        t_=(2*arc[2].r*tau+pow(tau,2))/\
            (2*(arc[2].r+(arc[2].r+tau)*V0*Vb))
        
        te=arc[2].r+t_-(Arc0.Pe-(arc[2].O+(t_*V0))).distance()
        te=tau


        tm=-arc[1].O.distance(Arc0.Pe)+abs(arc[1].r)
        if tm<0.0:
            tf=tau
        else:   
            tf=tau-tm
        #print("tm: %0.3f; tf: %0.3f; te: %0.3f; tau: %0.3f" %(tm,tf,te,tau))
        epsilon=min([te,tf,tau])

        if epsilon<0.0:
            epsilon=0.0
        
        return epsilon    
   
    def fit_triac_by_inc_biarc(self,arc,eps):

        #Errechnen von tb        
        V0=arc[0].Pa.unit_vector(arc[0].O)
        V2=arc[2].Pe.unit_vector(arc[2].O)

        #Errechnen der Hilfgrössen
        t0=(arc[2].r-arc[0].r)
        D=(arc[2].O-arc[0].O)
        X0=(t0*t0)-(D*D)
        X1=2*(D*V0-t0)
        Y0=2*(t0-D*V2)
        Y1=2*(V0*V2-1)

        #Errechnen von tb
        tb=(pow((arc[1].r-arc[0].r+eps),2)-((arc[1].O-arc[0].O)*(arc[1].O-arc[0].O)))/\
            (2*(arc[1].r-arc[0].r+eps+(arc[1].O-arc[0].O)*V0))

        #Errechnen von tc
        tc=(pow(t0,2)-(D*D))/(2*(t0-D*V0))

        #Auswahl von t
        t=min([tb,tc])

        #Errechnen von u
        u=(X0+X1*t)/(Y0+Y1*t)

        #Errechnen der neuen Arcs
        Oa=arc[0].O+t*V0
        ra=arc[0].r+t
        Ob=arc[2].O-u*V2
        rb=arc[2].r-u
        Vn=Ob.unit_vector(Oa)
        Pn=Oa+ra*Vn

        Arc0=ArcGeo(Pa=arc[0].Pa,Pe=Pn,O=Oa,r=ra,dir=arc[0].ext)
        Arc1=ArcGeo(Pa=Pn,Pe=arc[2].Pe,O=Ob,r=rb,dir=arc[2].ext)

##        print('\nAlte')
##        print arc[0]
##        print arc[1]
##        print arc[2]
##        print("tb: %0.3f; tc: %0.3f; t: %0.3f; u: %0.3f" %(tb,tc,t,u))
##        print 'Neue'
##        print Arc0
##        print Arc1
        
        return Arc0, Arc1

    def fit_triac_by_dec_biarc(self,arc,eps):
        
        V0=arc[2].Pe.unit_vector(arc[2].O)
        V2=arc[0].Pa.unit_vector(arc[0].O)

        #Errechnen der Hilfgrössen
        t0=(arc[0].r-arc[2].r)
        D=(arc[0].O-arc[2].O)
        X0=(t0*t0)-(D*D)
        X1=2*(D*V0-t0)
        Y0=2*(t0-D*V2)
        Y1=2*(V0*V2-1)

        #Errechnen von tb
        tb=(pow((arc[1].r-arc[2].r+eps),2)-((arc[1].O-arc[2].O)*(arc[1].O-arc[2].O)))/\
            (2*(arc[1].r-arc[2].r+eps+(arc[1].O-arc[2].O)*V0))


        #Errechnen von tc
        tc=(pow(t0,2)-(D*D))/(2*(t0-D*V0))

        #Auswahl von t
        t=min([tb,tc])     

        #Errechnen von u
        u=(X0+X1*t)/(Y0+Y1*t)

        #Errechnen der neuen Arcs
        Oa=arc[0].O-u*V2
        ra=arc[0].r-u
        Ob=arc[2].O+t*V0
        rb=arc[2].r+t
        Vn=Oa.unit_vector(Ob)
        Pn=Ob+rb*Vn

        Arc0=ArcGeo(Pa=arc[0].Pa,Pe=Pn,O=Oa,r=ra,\
                    s_ang=Oa.norm_angle(arc[0].Pa),e_ang=Oa.norm_angle(Pn),dir=arc[0].ext)
        Arc1=ArcGeo(Pa=Pn,Pe=arc[2].Pe,O=Ob,r=rb,\
                    s_ang=Ob.norm_angle(Pn),e_ang=Ob.norm_angle(arc[2].Pe),dir=arc[2].ext)

            
        return Arc0, Arc1

    def check_diff_to_pts(self,Pts,Arc0,Arc1):
        diff=[]
        for Pt in Pts:
            w0=Arc0.O.norm_angle(Pt)
            w1=Arc1.O.norm_angle(Pt)
            if (w0>=min([Arc0.s_ang,Arc0.e_ang]))and\
               (w0<=max([Arc0.s_ang,Arc0.e_ang])):
                diff.append(abs(Arc0.O.distance(Pt)-abs(Arc0.r)))
            elif (w1>=min([Arc1.s_ang,Arc1.e_ang]))and\
                (w1<=max([Arc1.s_ang,Arc1.e_ang])):
                diff.append(abs(Arc1.O.distance(Pt)-abs(Arc1.r)))
            else:
                del Pts[Pts.index(Pt)]
        return diff
    def compress_lines(self,Curve):
        joint=[]
        NewCurve=[]
        Pts=[]
        for geo in Curve:
            NewCurve.append(geo)
            anz=len(NewCurve)
            if anz>=2:
                #Wenn Geo eine Linie ist anhängen und überprüfen
                if (NewCurve[-2].type=="LineGeo") and (NewCurve[-1].type=="LineGeo"):
                    Pts.append(geo.Pe)
                    JointLine=LineGeo(NewCurve[-2].Pa,NewCurve[-1].Pe)
                    
                    #Überprüfung der Abweichung
                    res=[]
                    for point in Pts:
                        res.append(JointLine.distance2point(point))
                    #print res
                        
                    #Wenn die Abweichung OK ist Vorheriges anhängen
                    if (max(res)<self.epsilon):
                        anz=len(NewCurve)
                        del NewCurve[anz-2:anz]
                        NewCurve.append(JointLine)
                        points=[geo.Pe]
                    #Wenn nicht nicht anhängen und Pts zurücksetzen
                    else:
                        Pts=[geo.Pe]
                        

                              
                #Wenn es eines eine andere Geometrie als eine Linie ist        
                else:
                    Pts=[]
                                   
        return NewCurve
        
    def calc_high_accurancy_BiarcCurve(self):
        #Berechnen der zu Berechnenden getrennten Abschnitte
        u_sections=self.calc_u_sections(self.NURBS.Knots,\
                                        self.NURBS.ignor,\
                                        self.NURBS.knt_m_change[:])

        #Step muß ungerade sein, sonst gibts ein Rundungsproblem um 1
        self.max_step=float(self.NURBS.Knots[-1]/(float(self.segments)))

        #Berechnen des ersten Biarcs fürs Fitting
        BiarcCurves=[]
        PtsVecs=[]

        #Schleife für die einzelnen Abschnitte        
        for u_sect in u_sections:
            BiarcCurve, PtsVec=self.calc_Biarc_section(u_sect,self.epsilon_high)
            BiarcCurves.append(BiarcCurve)
            PtsVecs.append(PtsVec)
        return BiarcCurves, PtsVecs
        
    def calc_u_sections(self,Knots,ignor,unsteady):

        #Initialisieren
        u_sections=[]

        #Abfrage ob bereits der Anfang ignoriert wird
        u_beg=Knots[0]
        u_end=Knots[0]
        ig_nr=0

        #Schleife bis u_end==Knots[0]      
        while u_end<Knots[-1]:
            u_beg=u_end
            #Wenn Ignor == Start dann Start = Ende von Ignor              
            if len(ignor)>ig_nr:
                if u_beg==ignor[ig_nr][0]:
                    u_beg=ignor[ig_nr][1]
                    ig_nr+=1

                    #Löschen der unsteadys bis größer als u_beg
                    while (len(unsteady)>0)and(unsteady[0]<=u_beg):
                        del(unsteady[0])

            #Wenn Ignor noch mehr beiinhaltet dann Ignor Anfang = Ende   
            if len(ignor)>ig_nr:
                u_end=ignor[ig_nr][0]
            else:
                u_end=Knots[-1]

            if (len(unsteady)>0)and(unsteady[0]<u_end):
                u_end=unsteady[0]
                del(unsteady[0])

            #Solange u_beg nicht das Ende ist anhängen
            if not(u_beg==u_end):            
                u_sections.append([u_beg,u_end])
        return u_sections

    def calc_Biarc_section(self,u_sect,max_tol):
        min_u=1e-9
        BiarcCurve=[]
        cur_step=self.max_step
        u=u_sect[0]+min_u
        PtsVec=[self.NURBS.NURBS_evaluate(n=1,u=u)]
        step=0
        #Berechnen bis alle Biarcs berechnet sind
        while(u<u_sect[-1]-min_u):
            step+=1
            u+=cur_step

            #Begrenzung von u auf den Maximalwert
            if u>u_sect[-1]:
                cur_step=u_sect[-1]-(u-cur_step)-min_u
                u=u_sect[-1]-min_u

            PtVec=self.NURBS.NURBS_evaluate(n=1,u=u)

            #Aus den letzten 2 Punkten den nächsten Biarc berechnen
            Biarc=BiarcClass(PtsVec[-1][0],PtsVec[-1][1],PtVec[0],PtVec[1],max_tol)

            if Biarc.shape=="Zero":
                self.cur_step=min([cur_step*2,self.max_step])
            elif Biarc.shape=="LineGeo":
                BiarcCurve.append(Biarc)
                cur_step=min([cur_step*2,self.max_step])
                PtsVec.append(PtVec)
            else:
                if Biarc.check_biarc_fitting_tolerance(self.NURBS,max_tol,u-cur_step,u):
                    PtsVec.append(PtVec)
                    BiarcCurve.append(Biarc)
                    cur_step=min([cur_step/0.7,self.max_step])
                else:
                    u-=cur_step
                    cur_step*=0.7
                    
            if step>1000:
                raise ValueError, "Iteraitions above 1000 reduce tolerance"
            
        return BiarcCurve, PtsVec
    
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

        #print self
        x=[]; y=[]
        #Alle 6 Grad ein Linien Segment Drucken
        segments=int((abs(degrees(self.ext))//0.01)+1)
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
        #print self
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







class PlotClass(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self,None,-1,
                         'CanvasFrame',size=(550,350))



        self.SetBackgroundColour(wx.NamedColor("WHITE"))

        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)

        self.canvas = FigureCanvas(self, -1, self.figure)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

        self.add_toolbar()  # comment this out for no toolbar
        
        self.axes.set_title("NURBS and B-Spline Algorithms: ")


    def add_toolbar(self):
        self.toolbar = NavigationToolbar2Wx(self.canvas)
        self.toolbar.Realize()
        if wx.Platform == '__WXMAC__':
            # Mac platform (OSX 10.3, MacPython) does not seem to cope with
            # having a toolbar in a sizer. This work-around gets the buttons
            # back, but at the expense of having the toolbar at the top
            self.SetToolBar(self.toolbar)
        else:
            # On Windows platform, default window size is incorrect, so set
            # toolbar width to figure width.
            tw, th = self.toolbar.GetSizeTuple()
            fw, fh = self.canvas.GetSizeTuple()
            # By adding toolbar in sizer, we are able to put it at the bottom
            # of the frame - so appearance is closer to GTK version.
            # As noted above, doesn't work for Mac.
            self.toolbar.SetSize(wx.Size(fw, th))
            self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()

    def OnPaint(self, event):
        self.canvas.draw()

    def make_nurbs_plot(self,CPoints=[],Points=[],Tang=[]):


                
        xC=[]; yC=[]; xP=[]; yP=[]

        for Cpt in CPoints:
            xC.append(Cpt.x)
            yC.append(Cpt.y)
        for Pt in Points:
            xP.append(Pt.x)
            yP.append(Pt.y)
        self.axes.plot(xC,yC,'-.xr',xP,yP,'-og')

        if len(Tang)>0:
            arrow_len=0.3
            self.axes.hold(True)
            
            for nr in range(len(Tang)):
                self.axes.arrow(Points[nr].x,Points[nr].y,\
                                 cos(Tang[nr])*arrow_len,\
                                 sin(Tang[nr])*arrow_len,\
                                 width=0.02)
                
        self.canvas.show()
    def make_nurbs_biarc_plot(self,biarcs):
        self.axes.set_title("NURBS, BIARC Fitting Algorithms: ")

        arrow_len=0.3
        arrow_width=arrow_len*0.05

        xP=[]
        yP=[]
        self.axes.hold(True)
        for PtsVec in biarcs.PtsVec:
            for Pt in PtsVec:
                (Pt[0].x)
                (Pt[0].y)
                self.axes.plot([Pt[0].x],[Pt[0].y],'xr')
                
##                self.plot1.arrow(Pt[0].x,Pt[0].y,\
##                                 cos(Pt[1])*arrow_len,\
##                                 sin(Pt[1])*arrow_len,\
##                                 width=arrow_width)        

        for geo in biarcs.Curve:
            geo.plot2plot(self.axes)
        self.axes.axis('scaled')     
        #self.canvas.show()
        
    def _onSize(self, event):
        self._resizeflag = True

    def _onIdle(self, evt):
        if self._resizeflag:
            self._resizeflag = False
            self._SetSize()
            self.draw()

    def _SetSize(self, pixels = None):
        """
        This method can be called to force the Plot to be a desired size, which defaults to
        the ClientSize of the panel
        """
        if not pixels:
            pixels = self.GetClientSize()
        self.canvas.SetSize(pixels)
        self.figure.set_figsize_inches(pixels[0]/self.figure.get_dpi(),
        pixels[1]/self.figure.get_dpi())


    
class ExamplesClass:
    def __init__(self):
        pass
        
    def calc_nurbs_1(self):
            #Initialisieren der NURBS Klasse
            degree, CPoints, Weights, Knots=self.get_nurbs_()
            Nurbs=NURBSClass(degree=degree,Knots=Knots,CPoints=CPoints,Weights=Weights)

            #Berechnen von 30 Punkten des NURBS
            Points, Tang=Nurbs.calc_curve(n=1,cpts_nr=30)
            CPoints=CPoints
            
            return CPoints, Points, Tang

    def calc_bspline_1(self):
            #Initialisieren der B-Spline Klasse
            degree, CPts, Knots=self.get_bspline_1()
            BSpline=BSplineClass(degree=degree,Knots=Knots,CPts=CPts)

            #Berechnen von 30 Punkten des B-Spline bis zur ersten Ableitung
            Points, Tang=BSpline.calc_curve(n=1,cpts_nr=30)
            
            self.CPoints=[]
            for CPt in CPts:
                CPoints.append(PointClass(x=CPt[0],y=CPt[1]))
                
            return CPoints, Points, Tang

    def get_nurbs_6(self):
        degree=3
        Knots = [0.0, 0.0, 0.0, 0.0,\
                 0.10000000000000001, 0.10000000000000001, 0.10000000000000001, 0.10000000000000001,\
                 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001,\
                 0.29999999999999999, 0.29999999999999999, 0.29999999999999999, 0.29999999999999999,\
                 0.40000000000000002, 0.40000000000000002, 0.40000000000000002, 0.40000000000000002,\
                 0.5, 0.5, 0.5, 0.5,\
                 0.59999999999999998, 0.59999999999999998, 0.59999999999999998, 0.59999999999999998,\
                 0.69999999999999996, 0.69999999999999996, 0.69999999999999996, 0.69999999999999996,\
                 0.79999999999999993, 0.79999999999999993, 0.79999999999999993, 0.79999999999999993,\
                 0.89999999999999991, 0.89999999999999991, 0.89999999999999991, 0.89999999999999991,\
                 1.0, 1.0, 1.0, 1.0]
        Weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        CPoints=[]
        CPoints.append(PointClass(x=-69.25000, y=-77.50000))
        CPoints.append(PointClass(x=-69.25000, y=-77.50000))
        CPoints.append(PointClass(x=-69.24930, y=-77.50000))
        CPoints.append(PointClass(x=-69.24930, y=-77.50000))
        CPoints.append(PointClass(x=-69.24930, y=-77.50000))
        CPoints.append(PointClass(x=-60.97700, y=-77.50020))
        CPoints.append(PointClass(x=-53.35560, y=-80.37450))
        CPoints.append(PointClass(x=-47.33170, y=-85.17480))
        CPoints.append(PointClass(x=-47.33170, y=-85.17480))
        CPoints.append(PointClass(x=-47.33170, y=-85.17480))
        CPoints.append(PointClass(x=-49.82390, y=-87.66700))
        CPoints.append(PointClass(x=-49.82390, y=-87.66700))
        CPoints.append(PointClass(x=-49.82390, y=-87.66700))
        CPoints.append(PointClass(x=-55.19980, y=-83.49120))
        CPoints.append(PointClass(x=-61.94320, y=-81.00010))
        CPoints.append(PointClass(x=-69.24930, y=-81.00000))
        CPoints.append(PointClass(x=-69.24930, y=-81.00000))
        CPoints.append(PointClass(x=-69.24930, y=-81.00000))
        CPoints.append(PointClass(x=-69.25000, y=-81.00000))
        CPoints.append(PointClass(x=-69.25000, y=-81.00000))
        CPoints.append(PointClass(x=-69.25000, y=-81.00000))
        CPoints.append(PointClass(x=-69.25000, y=-81.00000))
        CPoints.append(PointClass(x=-69.25150, y=-81.00000))
        CPoints.append(PointClass(x=-69.25150, y=-81.00000))
        CPoints.append(PointClass(x=-69.25150, y=-81.00000))
        CPoints.append(PointClass(x=-76.55740, y=-81.00030))
        CPoints.append(PointClass(x=-83.30040, y=-83.49120))
        CPoints.append(PointClass(x=-88.67610, y=-87.66700))
        CPoints.append(PointClass(x=-88.67610, y=-87.66700))
        CPoints.append(PointClass(x=-88.67610, y=-87.66700))
        CPoints.append(PointClass(x=-91.16830, y=-85.17480))
        CPoints.append(PointClass(x=-91.16830, y=-85.17480))
        CPoints.append(PointClass(x=-91.16830, y=-85.17480))
        CPoints.append(PointClass(x=-85.14470, y=-80.37460))
        CPoints.append(PointClass(x=-77.52360, y=-77.50030))
        CPoints.append(PointClass(x=-69.25150, y=-77.50000))
        CPoints.append(PointClass(x=-69.25150, y=-77.50000))
        CPoints.append(PointClass(x=-69.25150, y=-77.50000))
        CPoints.append(PointClass(x=-69.25000, y=-77.50000))
        CPoints.append(PointClass(x=-69.25000, y=-77.50000))
        return degree, CPoints, Weights, Knots

    def get_nurbs_61(self):
        degree=3
        Knots = [0.0, 0.0, 0.0, 0.0,\
                 0.10000000000000001, 0.10000000000000001, 0.10000000000000001, 0.10000000000000001,\
                 0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001]
        Weights = [1, 1, 1, 1, 1, 1, 1, 1]
        CPoints=[]
        CPoints.append(PointClass(x=-69.25000, y=-77.50000))
        CPoints.append(PointClass(x=-69.25000, y=-77.50000))
        CPoints.append(PointClass(x=-69.24930, y=-77.50000))
        CPoints.append(PointClass(x=-69.24930, y=-77.50000))
        CPoints.append(PointClass(x=-69.24930, y=-77.50000))
        CPoints.append(PointClass(x=-60.97700, y=-77.50020))
        CPoints.append(PointClass(x=-53.35560, y=-80.37450))
        CPoints.append(PointClass(x=-47.33170, y=-85.17480))
        
        return degree, CPoints, Weights, Knots

    def get_nurbs_62(self):
        degree=3
        Knots = [0.20000000000000001, 0.20000000000000001, 0.20000000000000001, 0.20000000000000001,\
                 0.29999999999999999, 0.29999999999999999, 0.29999999999999999, 0.29999999999999999,\
                 0.40000000000000002, 0.40000000000000002, 0.40000000000000002, 0.40000000000000002,\
                 0.5, 0.5, 0.5, 0.5,\
                 0.59999999999999998, 0.59999999999999998, 0.59999999999999998, 0.59999999999999998,\
                 0.69999999999999996, 0.69999999999999996, 0.69999999999999996, 0.69999999999999996,\
                 0.79999999999999993, 0.79999999999999993, 0.79999999999999993, 0.79999999999999993,\
                 0.89999999999999991, 0.89999999999999991, 0.89999999999999991, 0.89999999999999991,\
                 1.0, 1.0, 1.0, 1.0]
        Weights = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        CPoints=[]
        CPoints.append(PointClass(x=-47.33170, y=-85.17480))
        CPoints.append(PointClass(x=-47.33170, y=-85.17480))
        CPoints.append(PointClass(x=-49.82390, y=-87.66700))
        CPoints.append(PointClass(x=-49.82390, y=-87.66700))
        CPoints.append(PointClass(x=-49.82390, y=-87.66700))
        CPoints.append(PointClass(x=-55.19980, y=-83.49120))
        CPoints.append(PointClass(x=-61.94320, y=-81.00010))
        CPoints.append(PointClass(x=-69.24930, y=-81.00000))
        CPoints.append(PointClass(x=-69.24930, y=-81.00000))
        CPoints.append(PointClass(x=-69.24930, y=-81.00000))
        CPoints.append(PointClass(x=-69.25000, y=-81.00000))
        CPoints.append(PointClass(x=-69.25000, y=-81.00000))
        CPoints.append(PointClass(x=-69.25000, y=-81.00000))
        CPoints.append(PointClass(x=-69.25000, y=-81.00000))
        CPoints.append(PointClass(x=-69.25150, y=-81.00000))
        CPoints.append(PointClass(x=-69.25150, y=-81.00000))
        CPoints.append(PointClass(x=-69.25150, y=-81.00000))
        CPoints.append(PointClass(x=-76.55740, y=-81.00030))
        CPoints.append(PointClass(x=-83.30040, y=-83.49120))
        CPoints.append(PointClass(x=-88.67610, y=-87.66700))
        CPoints.append(PointClass(x=-88.67610, y=-87.66700))
        CPoints.append(PointClass(x=-88.67610, y=-87.66700))
        CPoints.append(PointClass(x=-91.16830, y=-85.17480))
        CPoints.append(PointClass(x=-91.16830, y=-85.17480))
        CPoints.append(PointClass(x=-91.16830, y=-85.17480))
        CPoints.append(PointClass(x=-85.14470, y=-80.37460))
        CPoints.append(PointClass(x=-77.52360, y=-77.50030))
        CPoints.append(PointClass(x=-69.25150, y=-77.50000))
        CPoints.append(PointClass(x=-69.25150, y=-77.50000))
        CPoints.append(PointClass(x=-69.25150, y=-77.50000))
        CPoints.append(PointClass(x=-69.25000, y=-77.50000))
        CPoints.append(PointClass(x=-69.25000, y=-77.50000))
        return degree, CPoints, Weights, Knots


class App(wx.App):
    def OnInit(self):
        'Create the main window and insert the custom frame'
        frame = PlotClass()
        
        if 1:
            examples=ExamplesClass()
            CPoints, Points, Tang=examples.calc_nurbs_1()
            frame.make_nurbs_plot(CPoints,Points,Tang)
        if 0:
            examples=ExamplesClass()
            
            degree, CPoints, Weights, Knots=examples.get_nurbs_6()   
            biarcfitting=BiarcFittingClass(degree, CPoints, Weights, Knots)
            frame.make_nurbs_biarc_plot(biarcfitting)
            
#            degree, CPoints, Weights, Knots=examples.get_nurbs_62()   
#            biarcfitting=BiarcFittingClass(degree, CPoints, Weights, Knots)
#            frame.make_nurbs_biarc_plot(biarcfitting)
            
        frame.Show(True)

        return True

app = App(0)
app.MainLoop()

     
