#!/usr/bin/python
# -*- coding: cp1252 -*-
#


# Abhängigkeit:
#
# BIARC_TEST.py
#  +--> clsEllipse.py
#        +--> clsBiArc.py


#matplotlib see: http://matplotlib.sourceforge.net/ and  http://www.scipy.org/Cookbook/Matplotlib/
#numpy    see: http://numpy.scipy.org/ and http://sourceforge.net/projects/numpy/
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.numerix import arange, sin, pi
from matplotlib.axes import Subplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

from Tkconstants import TOP, BOTH, BOTTOM, LEFT, RIGHT,GROOVE
from Tkinter import Tk, Button, Frame
from math import radians, degrees, cos, sin, tan, atan, atan2, sqrt, pow, pi, atan
import sys



from clsPoint import PointClass
from clsEllipse import EllipseClass

if 1:
    master = Tk()
    figure = Figure(figsize=(8,8), dpi=100)
    frame_c=Frame(relief = GROOVE,bd = 2)
    frame_c.pack(fill=BOTH, expand=1,)
    canvas = FigureCanvasTkAgg(figure, master=frame_c)
    canvas.show()
    canvas.get_tk_widget().pack(fill=BOTH, expand=1)
    plot1 = figure.add_subplot(111)
    plot1.axis('equal')

    # Parameter der Ellipse
    el = EllipseClass(PointClass(0,0), 200, 100, radians(30))
    polyline_step = 10 # PolyLine - Winkel-Schritt, in dem wir um die Ellipse sausen
    biarc_step    = 35 # BiArc - Winkel-Schritt, in dem wir um die Ellipse sausen

    # Ellipse als PolyLine
    xC=[]; yC=[]; xP=[]; yP=[]
    xC.append(el.Center.x)
    yC.append(el.Center.y)
    for i in range(0, 360, polyline_step):
        P = el.EPoint(radians(i))
        xP.append(P.x)
        yP.append(P.y)
    if (i < 360): # und noch kurzer Bogen, falls es nicht genau naus gegangen ist
        P = el.EPoint(radians(360))
        xP.append(P.x)
        yP.append(P.y)
    # zeichnen:
    plot1.plot(xC,yC,'-.xr',xP,yP,'-xb')
    
    # Test: Steigungsverlauf
    #print "Steigungsverlauf:"
    #for i in range(0, 361, 10):
    #    print "w= " + str(i) + "\t -> t= " + str(el.Tangente(radians(i)))

    # Ellipse als PolyArc :-)
    biarcs = []
    w = 0
    for w in range(biarc_step, 360, biarc_step):
        biarcs.append(el.BiArc(radians(w - biarc_step), radians(w)))
    if (w < 360): # und noch kurzer Bogen, falls es nicht genau naus gegangen ist
        biarcs.append(el.BiArc(radians(w), radians(360)))
   # alle BiArcs zeichnen:
    plot2 = figure.add_subplot(111)
    for biarc in biarcs:
        for geo in biarc.geos:
            geo.plot2plot(plot2)

    master.mainloop()
