#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
#
#dxf2gcode_b02_point
#Programmers:   Christian Kohlöffel
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

from math import pi

import Core.Globals as g
from Core.LineGeo import LineGeo
from Core.ArcGeo import ArcGeo
from Gui.Arrow import Arrow

import logging
logger=logging.getLogger('Gui.StMove')

from PyQt4 import QtCore, QtGui

#Length of the cross.
dl = 0.2
DEBUG = 1

class StMove(QtGui.QGraphicsLineItem):
    """
    This is the Function which generates the StartMove for each shape. This 
    function also performs the Plotting and Export of this moves. It is linked
    to the shape as its parent
    """
    def __init__(self, startp, angle, 
                 pencolor=QtCore.Qt.green,
                 shape=None,parent=None):
        """
        Initialisation of the class.
        @param startp: Startpoint of the shape where to add the move.
        The coordinates are given in scaled coordinates.
        @param angle: Angle of the Startmove to end with.
        @param pencolor: Used only for plotting purposes
        @param shape: Shape for which the start move is created
        @param parent: parent EntitieContent Class on which the 
        geometries are added.
        """
        self.sc=1
        super(StMove, self).__init__()

        self.startp = startp
        self.endp=startp
        self.angle=angle
        self.shape=shape
        self.parent=parent
        self.allwaysshow=False
        self.geos=[]
        self.path=QtGui.QPainterPath()
        
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        
        self.pen=QtGui.QPen(pencolor, 1, QtCore.Qt.SolidLine,
                QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.pen.setCosmetic(True)
        
        self.make_start_moves()
        self.createccarrow()
        self.make_papath()
        
        
    def make_start_moves(self):
        """
        This function is called to create the start move. It will
        be generated based on the given values for start and angle.
        """
        del(self.geos[:])

        #Get the start radius and the length of the line segment at begin. 
        start_rad = self.shape.LayerContent.start_radius
        start_ver = start_rad

        #Get tool radius based on tool diameter.   
        tool_rad = self.shape.LayerContent.tool_diameter/2
        
        #Calculate the starting point with and without compensation.        
        start=self.startp
        angle=self.angle
      
        if self.shape.cut_cor == 40:              
            self.geos.append(start)

        #Cutting Compensation Left        
        elif self.shape.cut_cor == 41:
            #Center of the Starting Radius.
            Oein = start.get_arc_point(angle + pi/2, start_rad + tool_rad)
            #Start Point of the Radius
            Pa_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            #Start Point of the straight line segment at begin.
            Pg_ein = Pa_ein.get_arc_point(angle + pi/2, start_ver)
            
            #Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.geos.append(start_ein)

            #generate the Start Line and append it including the compensation. 
            start_line = LineGeo(Pg_ein, Pa_ein)
            self.geos.append(start_line)

            #generate the Start Radius and append it.
            start_rad = ArcGeo(Pa=Pa_ein, Pe=start, O=Oein, 
                               r=start_rad + tool_rad, direction=1)
            self.geos.append(start_rad)
            
        #Cutting Compensation Right            
        elif self.shape.cut_cor == 42:
            #Center of the Starting Radius.
            Oein = start.get_arc_point(angle - pi/2, start_rad + tool_rad)
            #Start Point of the Radius
            Pa_ein = Oein.get_arc_point(angle + pi, start_rad + tool_rad)
            #Start Point of the straight line segment at begin.
            Pg_ein = Pa_ein.get_arc_point(angle - pi/2, start_ver)
            
            #Get the dive point for the starting contour and append it.
            start_ein = Pg_ein.get_arc_point(angle, tool_rad)
            self.geos.append(start_ein)

            #generate the Start Line and append it including the compensation.
            start_line = LineGeo(Pg_ein, Pa_ein)
            self.geos.append(start_line)

            #generate the Start Radius and append it.
            start_rad = ArcGeo(Pa=Pa_ein, Pe=start, O=Oein, 
                               r=start_rad + tool_rad, direction=0)
            self.geos.append(start_rad)
            
            
    def updateCutCor(self, cutcor):
        """
        This function is called to update the Cutter Correction, and therefore 
        the start moves, if something has changed or it shall be generated for 
        first time.
        """
        logger.debug("Updating CutterCorrection of Selected shape")

        self.cutcor=cutcor
        self.make_start_moves()
   
    def updateCCplot(self):
        """
        This function is called to update the Cutter Correction, and therefore 
        the start moves, if something has changed or it shall be generated for 
        first time.
        """
        logger.debug("Updating CutterCorrection of Selected shape plotting")
        
        if not(self.ccarrow is None):
            logger.debug("Removing ccarrow from scene")
            self.ccarrow.hide()
            logger.debug("Parent Item: %s" %self.ccarrow.parentItem())
            del(self.ccarrow)
            self.ccarrow=None
        
        self.createccarrow()
        self.make_papath()
        self.update()
        
    def createccarrow(self):
         
        length=20
        if self.shape.cut_cor==40:
            self.ccarrow=None
        elif self.shape.cut_cor==41:
            self.ccarrow=Arrow(startp=self.startp,
                        length=length,
                        angle=self.angle+pi/2,
                        color=QtGui.QColor(200, 200, 255),
                        pencolor=QtGui.QColor(200, 100, 255))
            self.ccarrow.setParentItem(self)
        else:
            self.ccarrow=Arrow(startp=self.startp,
                        length=length,
                        angle=self.angle-pi/2,
                        color=QtGui.QColor(200, 200, 255),
                        pencolor=QtGui.QColor(200, 100, 255))
            self.ccarrow.setParentItem(self)
    
    def update_plot(self,startp,angle):
        """
        Method is called after update of the Shapes Startpoint
        @param startp: The new startpoint
        @param angle: the new Angle of the Startpoint
        """  
        self.startp = startp
        self.endp=startp
        self.angle=angle
        
        if self.shape.cut_cor==40:
            self.ccarrow=None
        elif self.shape.cut_cor==41:
            self.ccarrow.updatepos(startp, angle=angle+pi/2)
        else:
            self.ccarrow.updatepos(startp, angle=angle-pi/2)
            
        self.make_start_moves()
        self.make_papath()
         
    def make_papath(self):
        """
        To be called if a Shape shall be printed to the canvas
        @param canvas: The canvas to be printed in
        @param pospro: The color of the shape 
        """
        self.hide()
        del(self.path)
        self.path=QtGui.QPainterPath()
        
        for geo in self.geos:
            geo.add2path(papath=self.path,parent=self.parent)
        self.show()

    def setSelected(self,flag=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        if self.allwaysshow:
            pass
        elif flag is True:
            self.show()
        else:
            self.hide()
        
        self.update(self.boundingRect())
        
    def reverseshape(self,startp,angle):
        """
        Method is called when the shape direction is changed and therefore the
        arrow gets new Point and direction
        @param startp: The new startpoint
        @param angle: The new angle of the arrow
        """
        self.startp=startp
        self.angle=angle
        self.update_plot(startp,angle)
        
    def setallwaysshow(self,flag=False):
        """
        If the directions shall be allwaysshown the parameter will be set and 
        all paths will be shown.
        @param flag: The flag to enable or disable Selection
        """
        self.allwaysshow=flag
        if flag is True:
            self.show()
        elif flag is True and self.isSelected():
            self.show()
        else:
            self.hide()
        self.update(self.boundingRect())
            
               
    def paint(self, painter, option, widget=None):
        """
        Method for painting the arrow.
        """
        painter.setPen(self.pen)
        painter.drawPath(self.path) 

    def boundingRect(self):
        """ 
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """ 
        return self.path.boundingRect()
    

