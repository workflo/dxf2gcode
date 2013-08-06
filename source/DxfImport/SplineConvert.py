#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_nurbs_calc
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


from Core.Point import Point
from Core.ArcGeo import ArcGeo
from Core.LineGeo import  LineGeo
from DxfImport.biarc import BiarcClass

from math import atan2, pow

class Spline2Arcs:
    def __init__(self, degree=0, Knots=[], Weights=[], CPoints=[], tol=0.01, check=1):
        #Max Abweichung f�r die Biarc Kurve
        self.epsilon = tol
        self.epsilon_high = self.epsilon * 0.1
        self.segments = 50
        
        #NURBS Klasse initialisieren
        self.NURBS = NURBSClass(degree=degree, Knots=Knots, CPoints=CPoints, Weights=Weights)
        
        #�berpr�fen der NURBS Parameter �berpr�fung der NURBS Kontrollpunkte ob welche doppelt
        #Innerhalb der gegebenen Tolerans sind (=> Ignorieren)
        self.NURBS.check_NURBSParameters(tol, check)
        
        #High Accuracy Biarc fitting of NURBS
        BiarcCurves, self.PtsVec = self.calc_high_accurancy_BiarcCurve()
        
        #Komprimieren der Biarc und der Linien
        self.Curve = self.analyse_and_compress(BiarcCurves)
        
    def analyse_and_compress(self, BiarcCurves):
        #Compress all to one curve
        Curves = []
        for BiarcCurve in BiarcCurves:
            Curve = []
            for Biarc in BiarcCurve:
                for geo in Biarc.geos:
                    Curve.append(geo)
            
            #print ("Vor Linie: Elemente: %0.0f" %len(Curve))
            Curve = self.compress_lines(Curve)
            #print ("Nach Linie: Elemente: %0.0f" %len(Curve))
            Curve = self.compress_biarcs(Curve)
            #print ("Nach Biarc: Elemente: %0.0f" %len(Curve))
            Curves += Curve
        return Curves
    
    def compress_biarcs(self, Curves):
        NewCurve = []
        tau = self.epsilon
        Pts = []
        #Schleife f�r die Anzahl der Geometrirs
        for geo in Curves:
            NewCurve.append(geo)
            #Wenn die L�nge mindestens 3 sind
            if len(NewCurve) >= 3:
                #Steigende Spirale
                if ((NewCurve[-3].type == "ArcGeo")\
                   and(NewCurve[-2].type == "ArcGeo")\
                   and(NewCurve[-1].type == "ArcGeo")):
                    Pts.append(geo.Pe)
                    if(NewCurve[-3].r <= NewCurve[-2].r)\
                        and(NewCurve[-2].r <= NewCurve[-1].r)\
                        and((NewCurve[-3].ext * NewCurve[-2].ext) >= 0.0)\
                        and((NewCurve[-2].ext * NewCurve[-1].ext) >= 0.0):
                        #print "Increasing"
                        anz = len(NewCurve)
                        triarc = NewCurve[anz - 3:anz]
                        Arc0, Arc1 = self.fit_triac_by_inc_biarc(triarc, tau)
                        diff = self.check_diff_to_pts(Pts, Arc0, Arc1)
                        
                        #�berpr�fen ob es in Toleranz liegt
                        try:
                            if max(diff) < self.epsilon:
                                tau = self.calc_active_tolerance_inc(self.epsilon, triarc, Arc0, Arc1)
                                del NewCurve[anz - 3:anz]
                                NewCurve.append(Arc0)
                                NewCurve.append(Arc1)
                        except:
                            pass
                        
                    elif (NewCurve[-3].r > NewCurve[-2].r)\
                         and(NewCurve[-2].r > NewCurve[-1].r)\
                         and((NewCurve[-3].ext * NewCurve[-2].ext) >= 0.0)\
                         and((NewCurve[-2].ext * NewCurve[-1].ext) >= 0.0):
                        #print "Decreasing"
                        anz = len(NewCurve)
                        triarc = NewCurve[anz - 3:anz]
                        Arc0, Arc1 = self.fit_triac_by_dec_biarc(triarc, tau)
                        diff = self.check_diff_to_pts(Pts, Arc1, Arc0)
                        try:
                            if max(diff) < self.epsilon:
                                tau = self.calc_active_tolerance_dec(self.epsilon, triarc, Arc0, Arc1)
                                
                                del NewCurve[anz - 3:anz]
                                NewCurve.append(Arc0)
                                NewCurve.append(Arc1)
                        except:
                            pass
                else:
                    Pts = []
        return NewCurve
    
    def calc_active_tolerance_inc(self, tau, arc, Arc0, Arc1):
        V0 = arc[0].Pa.unit_vector(arc[0].O)
        Vb = Arc1.Pa.unit_vector(Arc1.O)
        
        t_ = (2 * arc[0].r * tau + pow(tau, 2)) / \
            (2 * (arc[0].r + (arc[0].r + tau) * V0 * Vb))
        
        te = arc[0].r + t_ - (Arc0.Pe - (arc[0].O + (t_ * V0))).distance()
        
        tm = arc[1].O.distance(Arc0.Pe) - abs(arc[1].r)
        if tm < 0.0:
            tf = tau
        else:
            tf = tau - tm
        #print("tm: %0.3f; te: %0.3f; tau: %0.3f" %(tm,te,tau))
        epsilon = min([te, tf, tau])
        
        if epsilon < 0.0:
            epsilon = 0.0
        
        return epsilon
    
    def calc_active_tolerance_dec(self, tau, arc, Arc0, Arc1):
        V0 = arc[2].Pa.unit_vector(arc[2].O)
        Vb = Arc1.Pa.unit_vector(Arc1.O)
        
        t_ = (2 * arc[2].r * tau + pow(tau, 2)) / \
            (2 * (arc[2].r + (arc[2].r + tau) * V0 * Vb))
        
        te = arc[2].r + t_ - (Arc0.Pe - (arc[2].O + (t_ * V0))).distance()
        te = tau
        
        tm = -arc[1].O.distance(Arc0.Pe) + abs(arc[1].r)
        if tm < 0.0:
            tf = tau
        else:
            tf = tau - tm
        #print("tm: %0.3f; tf: %0.3f; te: %0.3f; tau: %0.3f" %(tm,tf,te,tau))
        epsilon = min([te, tf, tau])
        
        if epsilon < 0.0:
            epsilon = 0.0
        
        return epsilon
    
    def fit_triac_by_inc_biarc(self, arc, eps):
        
        #Errechnen von tb
        V0 = arc[0].Pa.unit_vector(arc[0].O)
        V2 = arc[2].Pe.unit_vector(arc[2].O)
        
        #Errechnen der Hilfgr�ssen
        t0 = (arc[2].r - arc[0].r)
        D = (arc[2].O - arc[0].O)
        X0 = (t0 * t0) - (D * D)
        X1 = 2 * (D * V0 - t0)
        Y0 = 2 * (t0 - D * V2)
        Y1 = 2 * (V0 * V2 - 1)
        
        #Errechnen von tb
        tb = (pow((arc[1].r - arc[0].r + eps), 2) - ((arc[1].O - arc[0].O) * (arc[1].O - arc[0].O))) / \
            (2 * (arc[1].r - arc[0].r + eps + (arc[1].O - arc[0].O) * V0))
        
        #Errechnen von tc
        tc = (pow(t0, 2) - (D * D)) / (2 * (t0 - D * V0))
        
        #Auswahl von t
        t = min([tb, tc])
        
        #Errechnen von u
        u = (X0 + X1 * t) / (Y0 + Y1 * t)
        
        #Errechnen der neuen Arcs
        Oa = arc[0].O + t * V0
        ra = arc[0].r + t
        Ob = arc[2].O - u * V2
        rb = arc[2].r - u
        Vn = Ob.unit_vector(Oa)
        Pn = Oa + ra * Vn
        
        Arc0 = ArcGeo(Pa=arc[0].Pa, Pe=Pn, O=Oa, r=ra, direction=arc[0].ext)
        Arc1 = ArcGeo(Pa=Pn, Pe=arc[2].Pe, O=Ob, r=rb, direction=arc[2].ext)
        
##        print('\nAlte')
##        print arc[0]
##        print arc[1]
##        print arc[2]
##        print("tb: %0.3f; tc: %0.3f; t: %0.3f; u: %0.3f" %(tb,tc,t,u))
##        print 'Neue'
##        print Arc0
##        print Arc1
        
        return Arc0, Arc1
    
    def fit_triac_by_dec_biarc(self, arc, eps):
        
        V0 = arc[2].Pe.unit_vector(arc[2].O)
        V2 = arc[0].Pa.unit_vector(arc[0].O)
        
        #Errechnen der Hilfgr�ssen
        t0 = (arc[0].r - arc[2].r)
        D = (arc[0].O - arc[2].O)
        X0 = (t0 * t0) - (D * D)
        X1 = 2 * (D * V0 - t0)
        Y0 = 2 * (t0 - D * V2)
        Y1 = 2 * (V0 * V2 - 1)
        
        #Errechnen von tb
        tb = (pow((arc[1].r - arc[2].r + eps), 2) - ((arc[1].O - arc[2].O) * (arc[1].O - arc[2].O))) / \
            (2 * (arc[1].r - arc[2].r + eps + (arc[1].O - arc[2].O) * V0))
        
        #Errechnen von tc
        tc = (pow(t0, 2) - (D * D)) / (2 * (t0 - D * V0))
        
        #Auswahl von t
        t = min([tb, tc])
        
        #Errechnen von u
        u = (X0 + X1 * t) / (Y0 + Y1 * t)
        
        #Errechnen der neuen Arcs
        Oa = arc[0].O - u * V2
        ra = arc[0].r - u
        Ob = arc[2].O + t * V0
        rb = arc[2].r + t
        Vn = Oa.unit_vector(Ob)
        Pn = Ob + rb * Vn
        
        Arc0 = ArcGeo(Pa=arc[0].Pa, Pe=Pn, O=Oa, r=ra, \
                    s_ang=Oa.norm_angle(arc[0].Pa), e_ang=Oa.norm_angle(Pn),
                    direction=arc[0].ext)
        Arc1 = ArcGeo(Pa=Pn, Pe=arc[2].Pe, O=Ob, r=rb, \
                    s_ang=Ob.norm_angle(Pn), e_ang=Ob.norm_angle(arc[2].Pe),
                    direction=arc[2].ext)
        
        return Arc0, Arc1
    
    def check_diff_to_pts(self, Pts, Arc0, Arc1):
        diff = []
        for Pt in Pts:
            w0 = Arc0.O.norm_angle(Pt)
            w1 = Arc1.O.norm_angle(Pt)
            if (w0 >= min([Arc0.s_ang, Arc0.e_ang]))and\
               (w0 <= max([Arc0.s_ang, Arc0.e_ang])):
                diff.append(abs(Arc0.O.distance(Pt) - abs(Arc0.r)))
            elif (w1 >= min([Arc1.s_ang, Arc1.e_ang]))and\
                (w1 <= max([Arc1.s_ang, Arc1.e_ang])):
                diff.append(abs(Arc1.O.distance(Pt) - abs(Arc1.r)))
            else:
                del Pts[Pts.index(Pt)]
        return diff
    
    def compress_lines(self, Curve):
        joint = []
        NewCurve = []
        Pts = []
        for geo in Curve:
            NewCurve.append(geo)
            anz = len(NewCurve)
            if anz >= 2:
                #Wenn Geo eine Linie ist anh�ngen und �berpr�fen
                if (NewCurve[-2].type == "LineGeo") and (NewCurve[-1].type == "LineGeo"):
                    Pts.append(geo.Pe)
                    JointLine = LineGeo(NewCurve[-2].Pa, NewCurve[-1].Pe)
                    
                    #�berpr�fung der Abweichung
                    res = []
                    for Point in Pts:
                        res.append(JointLine.distance2point(Point))
                    #print res
                    
                    #Wenn die Abweichung OK ist Vorheriges anh�ngen
                    if (max(res) < self.epsilon):
                        anz = len(NewCurve)
                        del NewCurve[anz - 2:anz]
                        NewCurve.append(JointLine)
                        points = [geo.Pe]
                    #Wenn nicht nicht anh�ngen und Pts zur�cksetzen
                    else:
                        Pts = [geo.Pe]
                    
                #Wenn es eines eine andere Geometrie als eine Linie ist
                else:
                    Pts = []
        
        return NewCurve
        
    def calc_high_accurancy_BiarcCurve(self):
        #Berechnen der zu Berechnenden getrennten Abschnitte
        u_sections = self.calc_u_sections(self.NURBS.Knots, \
                                          self.NURBS.ignor, \
                                          self.NURBS.knt_m_change[:])
        
        #Step mu� ungerade sein, sonst gibts ein Rundungsproblem um 1
        self.max_step = float(self.NURBS.Knots[-1] / (float(self.segments)))
        
        #Berechnen des ersten Biarcs f�rs Fitting
        BiarcCurves = []
        PtsVecs = []
        
        #Schleife f�r die einzelnen Abschnitte
        for u_sect in u_sections:
            BiarcCurve, PtsVec = self.calc_Biarc_section(u_sect, self.epsilon, self.epsilon_high)
            BiarcCurves.append(BiarcCurve)
            PtsVecs.append(PtsVec)
        return BiarcCurves, PtsVecs
    
    def calc_u_sections(self, Knots, ignor, unsteady):
        
        #Initialisieren
        u_sections = []
        
        #Abfrage ob bereits der Anfang ignoriert wird
        u_beg = Knots[0]
        u_end = Knots[0]
        ig_nr = 0
        
        #Schleife bis u_end==Knots[0]
        while u_end < Knots[-1]:
            u_beg = u_end
            #Wenn Ignor == Start dann Start = Ende von Ignor
            if len(ignor) > ig_nr:
                if u_beg == ignor[ig_nr][0]:
                    u_beg = ignor[ig_nr][1]
                    ig_nr += 1
                    
                    #L�schen der unsteadys bis gr��er als u_beg
                    while (len(unsteady) > 0)and(unsteady[0] <= u_beg):
                        del(unsteady[0])
            
            #Wenn Ignor noch mehr beiinhaltet dann Ignor Anfang = Ende
            if len(ignor) > ig_nr:
                u_end = ignor[ig_nr][0]
            else:
                u_end = Knots[-1]
            
            if (len(unsteady) > 0)and(unsteady[0] < u_end):
                u_end = unsteady[0]
                del(unsteady[0])
            
            #Solange u_beg nicht das Ende ist anh�ngen
            if not(u_beg == u_end):
                u_sections.append([u_beg, u_end])
        return u_sections
    
    def calc_Biarc_section(self, u_sect, nom_tol, max_tol):
        #max_tol=0.1
        #print(max_tol)
        min_u = 1e-12
        BiarcCurve = []
        cur_step = self.max_step
        u = u_sect[0] + min_u
        PtsVec = [self.NURBS.NURBS_evaluate(n=1, u=u)]
        step = 0
        #Berechnen bis alle Biarcs berechnet sind
        while(u < u_sect[-1] - min_u):
            step += 1
            u += cur_step
            
            #Begrenzung von u auf den Maximalwert
            if u > u_sect[-1]:
                cur_step = u_sect[-1] - (u - cur_step) - min_u
                u = u_sect[-1] - min_u
            
            PtVec = self.NURBS.NURBS_evaluate(n=1, u=u)
            
            #Aus den letzten 2 Punkten den n�chsten Biarc berechnen
            Biarc = (BiarcClass(PtsVec[-1][0], PtsVec[-1][1], PtVec[0], PtVec[1], nom_tol * 0.5))
            
            if Biarc.shape == "Zero":
                #print("zero")
                #self.cur_step = min([cur_step * 2, self.max_step])
                cur_step = min([cur_step * 2, self.max_step])
            elif Biarc.shape == "LineGeo":
                #print("LineGeo")
                BiarcCurve.append(Biarc)
                cur_step = min([cur_step * 2, self.max_step])
                PtsVec.append(PtVec)
            else:
                if self.check_biarc_fitting_tolerance(Biarc, max_tol, u - cur_step, u):
                    #print("fit1")
                    PtsVec.append(PtVec)
                    BiarcCurve.append(Biarc)
                    cur_step = min([cur_step / 0.7, self.max_step])
                else:
                    #print("else")
                    u -= cur_step
                    cur_step *= 0.7
            #print cur_step
            if step > 10000:
                raise ValueError, "Iterations above 10000 reduce tolerance"
            
        return BiarcCurve, PtsVec
    
    def check_biarc_fitting_tolerance(self, Biarc, epsilon, u0, u1):
        
        check_step = (u1 - u0) / 5
        check_u = []
        check_Pts = []
        fit_error = []
        
        for i in range(1, 5):
            check_u.append(u0 + check_step * i)
            check_Pts.append(self.NURBS.NURBS_evaluate(n=0, u=check_u[-1]))
            fit_error.append(Biarc.get_biarc_fitting_error(check_Pts[-1]))
#        print(u0)
#        print(u1)
#        print(Biarc)
#        print(check_Pts)
#        print(fit_error)
        if max(fit_error) >= epsilon:
            return 0
        else:
            return 1


class NURBSClass:
    def __init__(self, degree=0, Knots=[], Weights=None, CPoints=None):
        self.degree = degree              #Spline degree
        self.Knots = Knots                #Knoten Vektor
        self.CPoints = CPoints            #Kontrollpunkte des Splines [2D]
        self.Weights = Weights            #Gewichtung der Einzelnen Punkte
        
        #Initialisieren von errechneten Gr��en
        self.HCPts = []                   #Homogenepunkte Vektoren [3D]
        
        #Punkte in Homogene Punkte umwandeln
        self.CPts_2_HCPts()
        
        #Erstellen der BSplineKlasse zur Berechnung der Homogenen Punkte
        self.BSpline = BSplineClass(degree=self.degree, \
                                  Knots=self.Knots, \
                                  CPts=self.HCPts)
    
    
    def check_NURBSParameters(self, tol=1e-6, check=1):
        #�berpr�fen des Knotenvektors
        #Suchen von mehrfachen Knotenpunkte (Anzahl �ber degree+1 => Fehler?!)
        knt_nr = 1
        knt_vec = [[self.Knots[0]]]
        self.knt_m_change = []
        self.ignor = []
        
        if check == 1 or check == 3:
            while knt_nr < len(self.Knots):
                if self.Knots[knt_nr] == knt_vec[-1][-1]:
                    knt_vec[-1].append(self.Knots[knt_nr])
                else:
                    knt_vec.append([self.Knots[knt_nr]])
                knt_nr += 1
            
            for knt_spts in knt_vec:
                if (len(knt_spts) > self.degree + 1):
                    raise ValueError, "Same Knots Nr. bigger then degree+1"
                
                #�berpr�fen der Steigungdifferenz vor und nach dem Punkt wenn Mehrfachknoten
                elif ((len(knt_spts) > self.degree)
                        and(knt_spts[-1] > knt_vec[0][0])
                        and(knt_spts[-1] < knt_vec[-1][-1])):
                    
                    temp, tangent0 = self.NURBS_evaluate(n=1, u=knt_spts[0] - 1e-12)
                    temp, tangent1 = self.NURBS_evaluate(n=1, u=knt_spts[0])
                    
                    if abs(tangent0 - tangent1) > 1e-6:
                        self.knt_m_change.append(knt_spts[0])
                    
                
            #�berpr�fen der Kontrollpunkte
            #Suchen von mehrachen Kontrollpunkten (Anzahl �ber degree+2 => nicht errechnen
        if check == 2 or check == 3:
            ctlpt_nr = 0
            ctlpt_vec = [[ctlpt_nr]]
            while ctlpt_nr < len(self.CPoints) - 1:
                ctlpt_nr += 1
                if self.CPoints[ctlpt_nr].isintol(self.CPoints[ctlpt_vec[-1][-1]], tol):
                    ctlpt_vec[-1].append(ctlpt_nr)
                else:
                    ctlpt_vec.append([ctlpt_nr])
            
            for same_ctlpt in ctlpt_vec:
                if (len(same_ctlpt) > self.degree + 1):
                    self.ignor.append([self.Knots[same_ctlpt[0] + self.degree / 2], \
                                       self.Knots[same_ctlpt[-1] + self.degree / 2]])
        
        #raise ValueError, "Same Controlpoints Nr. bigger then degree+1"
        #print("Same Controlpoints Nr. bigger then degree+2")
        #for ignor in self.ignor:
        #    print("Ignoring u's between u: %s and u: %s" %(ignor[0],ignor[1]))
        
#        if len(self.knt_m_change):
#            print("Non steady Angles between Knots: %s" %self.knt_m_change)
    
    
    #Berechnen von eine Anzahl gleichm�ssig verteilter Punkte und bis zur ersten Ableitung
    def calc_curve(self, n=0, cpts_nr=20):
        #Anfangswerte f�r Step und u
        u = 0; Points = []; tang = []
        
        step = self.Knots[-1] / (cpts_nr - 1)
        
        while u <= 1.0:
            Pt, tangent = self.NURBS_evaluate(n=n, u=u)
            Points.append(Pt)
            
            #F�r die erste Ableitung wird den Winkel der tangente errechnet
            if n >= 1:
                tang.append(tangent)
            u += step
        if n >= 1:
            return Points, tang
        else:
            return Points
    
    #Berechnen eines Punkts des NURBS und der ersten Ableitung
    def NURBS_evaluate(self, n=0, u=0):
        #Errechnen der korrigierten u's
        #cor_u=self.correct_u(u)
        
        #Errechnen der Homogenen Punkte bis zur n ten Ableitung
        HPt = self.BSpline.bspline_ders_evaluate(n=n, u=u)
        
        #Punkt wieder in Normal Koordinaten zur�ck transformieren
        Point = self.HPt_2_Pt(HPt[0])
        
        #Errechnen der ersten Ableitung wenn n>0 als Richtungsvektor
        dPt = []
        tangent = None
        if n > 0:
            #    w(u)*A'(u)-w'(u)*A(u)
            #dPt=---------------------
            #           w(u)^2
            for j in range(len(HPt[0]) - 1):
                dPt.append((HPt[0][-1] * HPt[1][j] - HPt[1][-1] * HPt[0][j]) /
                           pow(HPt[0][-1], 2))
            
            #Berechnen des Winkels des Vektors
            tangent = atan2(dPt[1], dPt[0])
            
            return Point, tangent
        else:
            return Point
    
    
    #Umwandeln der NURBS Kontrollpunkte und Weight in einen Homogenen Vektor
    def CPts_2_HCPts(self):
        for P_nr in range(len(self.CPoints)):
            HCPtVec = [self.CPoints[P_nr].x * self.Weights[P_nr], \
                       self.CPoints[P_nr].y * self.Weights[P_nr], \
                       self.Weights[P_nr]]
            self.HCPts.append(HCPtVec[:])
    
    #Umwandeln eines Homogenen PunktVektor in einen Punkt
    def HPt_2_Pt(self, HPt):
        return Point(x=HPt[0] / HPt[-1], y=HPt[1] / HPt[-1])
    
    
class BSplineClass:
    def __init__(self, degree=0, Knots=[], CPts=[]):
        self.degree = degree
        self.Knots = Knots
        self.CPts = CPts
        
        self.Knots_len = len(self.Knots)
        self.CPt_len = len(self.CPts[0])
        self.CPts_len = len(self.CPts)
        
        #Eingangspr�fung, ober KnotenAnzahl usw. passt
        if  self.Knots_len < self.degree + 1:
            raise ValueError, "degree greater than number of control points."
        if self.Knots_len != (self.CPts_len + self.degree + 1):
            print ("shall be: %s" % (self.CPts_len + self.degree + 1))
            print ("is: %s" % self.Knots_len)
            raise ValueError, "Knot/Control Point/degree number error."
        
    #Berechnen von eine Anzahl gleichm�ssig verteilter Punkte bis zur n-ten Ableitung
    def calc_curve(self, n=0, cpts_nr=20):
        
        #Anfangswerte f�r Step und u
        u = 0
        step = float(self.Knots[-1]) / (cpts_nr - 1)
        Points = []
        
        #Wenn die erste Ableitung oder h�her errechnet wird die ersten
        #Ableitung in dem tan als Winkel in rad gespeichert
        tang = []
        
        while u <= self.Knots[-1]:
            CK = self.bspline_ders_evaluate(n=n, u=u)
            
            #Den Punkt in einem Punkt List abspeichern
            Points.append(Point(x=CK[0][0], y=CK[0][1]))
            
            #F�r die erste Ableitung wird den Winkel der tangente errechnet
            if n >= 1:
                tang.append(atan2(CK[1][1], CK[1][0]))
            u += step
            
        return Points, tang
    
    #Modified Version of Algorithm A3.2 from "THE NURBS BOOK" pg.93
    def bspline_ders_evaluate(self, n=0, u=0):
        #Berechnung der Position im Knotenvektor
        span = self.findspan(u)
        
        #Berechnen der Basis Funktion bis zur n ten Ableitung am Punkt u
        dN = self.ders_basis_functions(span, u, n)
        
        p = self.degree
        du = min(n, p)
        
        CK = []
        dPts = []
        for i in range(self.CPt_len):
            dPts.append(0.0)
        for k in range(n + 1):
            CK.append(dPts[:])
        
        for k in range(du + 1):
            for j in range(p + 1):
                for i in range(self.CPt_len):
                    CK[k][i] += dN[k][j] * self.CPts[span - p + j][i]
        
        return CK
    
    #Algorithm A2.1 from "THE NURBS BOOK" pg.68
    def findspan(self, u):
        #Spezialfall wenn der Wert==Endpunkt ist
        if(u == self.Knots[-1]):
            return self.Knots_len - self.degree - 2 #self.Knots_len #-1
        
        #Bin�re Suche starten
        #(Der Interval von low zu high wird immer halbiert bis
        #wert zwischen im Intervall von Knots[mid:mi+1] liegt)
        low = self.degree
        high = self.Knots_len
        mid = (low + high) / 2
        while ((u < self.Knots[mid])or(u >= self.Knots[mid + 1])):
            if (u < self.Knots[mid]):
                high = mid
            else:
                low = mid
            mid = (low + high) / 2
        return mid

    #Algorithm A2.3 from "THE NURBS BOOK" pg.72
    def ders_basis_functions(self, span, u, n):
        d = self.degree
        
        #initialisieren der a Matrix
        a = []
        zeile = []
        for j in range(d + 1):
            zeile.append(0.0)
        a.append(zeile[:]); a.append(zeile[:])
        
        #initialisieren der ndu Matrix
        ndu = []
        zeile = []
        for i in range(d + 1):
            zeile.append(0.0)
        for j in range(d + 1):
            ndu.append(zeile[:])
        
        #initialisieren der ders Matrix
        ders = []
        zeile = []
        for i in range(d + 1):
            zeile.append(0.0)
        for j in range(n + 1):
            ders.append(zeile[:])
        
        ndu[0][0] = 1.0
        left = [0]
        right = [0]
        
        for j in range(1, d + 1):
            #print('komisch span:%s, j:%s, u:%s, gesamt: %s' %(span,j,u,span+1-j))
            left.append(u - self.Knots[span + 1 - j])
            right.append(self.Knots[span + j] - u)
            saved = 0.0
            for r in range(j):
                #Lower Triangle
                ndu[j][r] = right[r + 1] + left[j - r]
                temp = ndu[r][j - 1] / ndu[j][r]
                #Upper Triangle
                ndu[r][j] = saved + right[r + 1] * temp
                saved = left[j - r] * temp
            ndu[j][j] = saved
            
        #Ergebniss aus S71
        #print("Ndu: %s" %ndu)
        
        #Load the basis functions
        for j in range(d + 1):
            ders[0][j] = ndu[j][d]
        
        #This section computes the derivatives (Eq. [2.9])
        for r in range(d + 1): #Loop over function index
            s1 = 0; s2 = 1  #Alternate rows in array a
            a[0][0] = 1.0
            for k in range(1, n + 1):
                der = 0.0
                rk = r - k; pk = d - k
                
                #print("\nrk: %s" %rk), print("pk: %s" %pk), print("s1: %s" %s1)
                #print("s2: %s" %s2), print("r: %s" %r) ,print("k: %s" %k)
                #print("j: %s" %j)
                
                #wenn r-k>0 (Linker Term) und somit
                if(r >= k):
                    a[s2][0] = a[s1][0] / ndu[pk + 1][rk]                 #2te: a[0][0] 1/
                    #print("a[%s][0]=a[%s][0](%s)/ndu[%s][%s](%s)=%s" \
                    #      %(s2,s1,a[s1][0],pk+1,rk,ndu[pk+1][rk],a[s2][0]))
                    der = a[s2][0] * ndu[rk][pk]
                if (rk >= -1):
                    j1 = 1
                else:
                    j1 = -rk
                if (r - 1 <= pk):
                    j2 = k - 1
                else:
                    j2 = d - r
                
                #Hier geht er bei der ersten Ableitung gar nicht rein
                #print("j1:%s j2:%s" %(j1,j2))
                for j in range(j1, j2 + 1):
                    a[s2][j] = (a[s1][j] - a[s1][j - 1]) / ndu[pk + 1][rk + j]
                    der += a[s2][j] * ndu[rk + j][pk]
                
                if(r <= pk):
                    a[s2][k] = -a[s1][k - 1] / ndu[pk + 1][r]               #1/ u(i+p+1)-u(i+1)
                    der += a[s2][k] * ndu[r][pk]                        #N(i+1)(p-1)
                    #print("a[%s][%s]=-a[%s][%s](%s)/ndu[%s][%s](%s)=%s" \
                    #      %(s2,k,s1,k-1,a[s1][k-1],pk+1,r,ndu[pk+1][r],a[s2][k]))
                    #print("ndu[%s][%s]=%s" %(r,pk,ndu[r][pk]))
                
                ders[k][r] = der
                #print("ders[%s][%s]=%s" %(k,r,der))
                j = s1; s1 = s2; s2 = j #Switch rows
                
                
        #Multiply through by the correct factors
        r = d
        for k in range(1, n + 1):
            for j in range(d + 1):
                ders[k][j] *= r
            r *= (d - k)
        return ders

