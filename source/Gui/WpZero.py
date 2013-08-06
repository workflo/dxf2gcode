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



from PyQt4 import QtCore, QtGui

#Length of the cross.
dl = 0.2
DEBUG = 1

class WpZero(QtGui.QGraphicsItem):
    def __init__(self, center,color=QtCore.Qt.gray):
        self.sc=1
        super(WpZero, self).__init__()

        self.center=center
        self.allwaysshow=False
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, False)
        self.color=color
        self.pen=QtGui.QPen(self.color, 1, QtCore.Qt.SolidLine,
                QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin)
        self.pen.setCosmetic(True)
        
        self.diameter = 20.0
 
    def setSelected(self,flag=True):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        pass
        
    def setallwaysshow(self,flag=False):
        """
        If the directions shall be allwaysshown the paramerter will
        be set and all paths will be shown.
        @param flag: The flag to enable or disable Selection
        """
        self.allwaysshow=flag
        if flag is True:
            self.show()
        else:
            self.hide()
        self.update(self.boundingRect())
               
    def paint(self, painter, option, widget=None):
        demat=painter.deviceTransform()
        self.sc=demat.m11()
        
        diameter1=self.diameter/self.sc
        diameter2=(self.diameter-4)/self.sc
       
        rectangle1=QtCore.QRectF(-diameter1/2, -diameter1/2, diameter1, diameter1)
        rectangle2=QtCore.QRectF(-diameter2/2, -diameter2/2, diameter2, diameter2)
        startAngle1 = 90 * 16
        spanAngle = 90 * 16
        startAngle2 = 270 * 16
    
        painter.drawEllipse(rectangle1)
        painter.drawEllipse(rectangle2)
        painter.drawPie(rectangle2, startAngle1, spanAngle)

        painter.setBrush(self.color)
        painter.drawPie(rectangle2, startAngle2, spanAngle)
        
    def boundingRect(self):
        """
        Override inherited function to enlarge selection of Arrow to include all
        @param flag: The flag to enable or disable Selection
        """
        diameter=self.diameter/self.sc
        return QtCore.QRectF(-20, -20.0, 40.0, 40.0)

 

