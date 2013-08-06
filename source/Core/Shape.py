#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_shape.py
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
#
#Main Class Shape



#import sys, os, string, ConfigParser 

from PyQt4 import QtCore, QtGui

import Core.Globals as g

from Core.Point import Point
from Core.BoundingBox import BoundingBox
from math import cos, sin, degrees, pi
from copy import deepcopy
from EntitieContent import EntitieContentClass

import logging
logger=logging.getLogger("Core.Shape") 

class ShapeClass(QtGui.QGraphicsItem):
    """
    The Shape Class includes all plotting, GUI functionality and export functions
    related to the Shapes.  
    """
    def __init__(self, nr='None', closed=0,
                cut_cor=40, length=0.0,
                parent=None,
                geos=[],
                axis3_start_mill_depth=None, axis3_mill_depth=None, axis3_slice_depth=None, f_g1_plane=None, f_g1_depth=None):
        """ 
        Standard method to initialize the class
        @param nr: The number of the shape. Starting from 0 for the first one 
        @param closed: Gives information about the shape, when it is closed this
        value becomes 1
        @param cut_cor: Gives the selected Curring Correction of the shape
        (40=None, 41=Left, 42= Right)
        @param length: The total length of the shape including all geometries
        @param parent: The parent EntitieContent Class of the shape
        @param geow: The list with all geometries included in the shape
        @param axis3_mill_depth: Optional parameter for the export of the shape.
        If this parameter is None the mill_depth of the parent layer will be used.
        """
        QtGui.QGraphicsItem.__init__(self) 
        
        
        self.pen=QtGui.QPen(QtCore.Qt.black,2)
        self.pen.setCosmetic(True)
        self.sel_pen=QtGui.QPen(QtCore.Qt.red,2) #,QtCore.Qt.DashLine
        self.sel_pen.setCosmetic(True)
        self.dis_pen=QtGui.QPen(QtCore.Qt.gray) #2,QtCore.Qt.DotLine
        self.dis_pen.setCosmetic(True)
        self.sel_dis_pen=QtGui.QPen(QtCore.Qt.blue) #2,QtCore.Qt.DotLine
        self.sel_dis_pen.setCosmetic(True)
        
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptedMouseButtons(QtCore.Qt.NoButton)

        self.disabled=False
        self.send_to_TSP=g.config.vars.Route_Optimisation['default_TSP']
        self.type = "Shape"
        self.nr = nr
        self.closed = closed
        self.cut_cor = 40
        self.length = length
        self.parent = parent
        self.stmove = []
        self.LayerContent=None
        self.geos = geos
        #self.BB = BoundingBox(Pa=None, Pe=None)
        self.axis3_mill_depth = axis3_mill_depth
        self.axis3_start_mill_depth = axis3_start_mill_depth
        self.axis3_slice_depth = axis3_slice_depth
        self.f_g1_plane = f_g1_plane
        self.f_g1_depth = f_g1_depth
        self.selectionChangedCallback = None
        self.enableDisableCallback = None

    def __str__(self):
        """ 
        Standard method to print the object
        @return: A string
        """ 
        return ('\ntype:        %s' % self.type) + \
               ('\nnr:          %i' % self.nr) + \
               ('\nclosed:      %i' % self.closed) + \
               ('\ncut_cor:     %s' % self.cut_cor) + \
               ('\nlen(geos):   %i' % len(self.geos)) + \
               ('\ngeos:        %s' % self.geos) + \
               ('\nsend_to_TSP: %i' % self.send_to_TSP)

    def tr(self,string_to_translate):
        """
        Translate a string using the QCoreApplication translation framework
        @param: string_to_translate: a unicode string    
        @return: the translated unicode string if it was possible to translate
        """
        return unicode(QtGui.QApplication.translate("ShapeClass",
                                                    string_to_translate,
                                                    None,
                                                    QtGui.QApplication.UnicodeUTF8))

    def setSelectionChangedCallback(self, callback):
        """
        register a callback function in order to inform parents when the selection has changed.
        Note: we can't use QT signals here because ShapeClass doesn't inherits from a QObject
        @param callback: the function to be called, with the prototype callbackFunction(shape, select)
        """
        self.selectionChangedCallback = callback

    def setEnableDisableCallback(self, callback):
        """
        register a callback function in order to inform parents when a shape has been enabled or disabled.
        Note: we can't use QT signals here because ShapeClass doesn't inherits from a QObject
        @param callback: the function to be called, with the prototype callbackFunction(shape, enabled)
        """
        self.enableDisableCallback = callback

    def setPen(self,pen):
        """ 
        Method to change the Pen of the outline of the object and update the
        drawing
        """ 
        self.pen=pen
        self.update(self.boundingRect())

    def paint(self, painter, option, _widget):
        """ 
        Method will be triggered with each paint event. Possible to give
        options
        @param painter: Reference to std. painter
        @param option: Possible options here
        @param _widget: The widget which is painted on.
        """ 
        
        if self.isSelected() and not(self.isDisabled()):
            painter.setPen(self.sel_pen)
        elif not(self.isDisabled()):
            painter.setPen(self.pen)
        elif self.isSelected() and self.isDisabled():
            painter.setPen(self.sel_dis_pen)
        else:
            painter.setPen(self.dis_pen)
    
        painter.drawPath(self.path) 
        
    def boundingRect(self):
        """ 
        Required method for painting. Inherited by Painterpath
        @return: Gives the Bounding Box
        """ 
        return self.path.boundingRect()

    def shape(self):
        """ 
        Reimplemented function to select outline only.
        @return: Returns the Outline only
        """ 
#        tolerance=5
#        
#        start, start_ang=self.get_st_en_points()
#        hitpath=QtGui.QPainterPath()
#        
#        # begin with a circle around the start point 
#        hitpath.addEllipse(start.x,start.y, tolerance, tolerance);  
## 
##    //input now starts with the 2nd point (there was a takeFirst) 
#        for geo in self.geos:
#            geo.add2hitpath(hitpath=hitpath,
#                            parent=self.parent,
#                            tolerance=tolerance)
        
        painterStrock=QtGui.QPainterPathStroker()
        painterStrock.setCurveThreshold(0.01)
        painterStrock.setWidth(0)

        stroke = painterStrock.createStroke(self.path)
        return stroke
    
    
#    def make_papath(self):
#        """
#        To be called if a Shape shall be printed to the canvas
#        """
#        start, start_ang=self.get_st_en_points()
#        
#        self.path=QtGui.QPainterPath()
#
#        self.path.moveTo(start.x,-start.y)
#        
#        logger.debug(self.tr("Adding shape to Scene Nr: %i") % (self.nr))
#        
#        for geo in self.geos:
#            geo.add2path(papath=self.path,parent=self.parent)
#            
#    
#    QPainterPath intersectionTestPath(QList<QPointF> input, qreal tolerance) 
#{ 
#    //will be the result 
#    QPainterPath path; 
# 
#    //during the loop, p1 is the "previous" point, initially the first one 
#    QPointF p1 = input.takeFirst();  
# 
#    //begin with a circle around the start point 
#    path.addEllipse(p1, tolerance, tolerance);  
# 
#    //input now starts with the 2nd point (there was a takeFirst) 
#    foreach(QPointF p2, input)  
#    { 
#        //note: during the algorithm, the pair of points (p1, p2) 
#        //      describes the line segments defined by input. 
# 
#        //offset = the distance vector from p1 to p2 
#        QPointF offset = p2 - p1; 
# 
#        //normalize offset to length of tolerance 
#        qreal length = sqrt(offset.x() * offset.x() + offset.y() * offset.y()); 
#        offset *= tolerance / length; 
# 
#        //"rotate" the offset vector 90 degrees to the left and right 
#        QPointF leftOffset(-offset.y(), offset.x()); 
#        QPointF rightOffset(offset.y(), -offset.x()); 
# 
#        //if (p1, p2) goes downwards, then left lies to the left and 
#        //right to the right of the source path segment 
#        QPointF left1 = p1 + leftOffset;
#        QPointF left2 = p2 + leftOffset;
#        QPointF right1 = p1 + rightOffset;
#        QPointF right2 = p2 + rightOffset;
# 
#        //rectangular connection from p1 to p2
#        { 
#            QPainterPath p;
#            p.moveTo(left1);
#            p.lineTo(left2);
#            p.lineTo(right2);
#            p.lineTo(right1);
#            p.lineTo(left1);
#            path += p; //add this to the result path
#        }
# 
#        //circle around p2
#        {
#            QPainterPath p;
#            p.addEllipse(p2, tolerance, tolerance);
#            path += p; //add this to the result path
#        }
# 
#        p1 = p2; 
#    } 
# 
#    //This does some simplification; you should use this if you call 
#    //path.contains() multiple times on a pre-calculated path, but 
#    //you won't need this if you construct a new path for every call 
#    //to path.contains(). 
#    return path.simplified(); 
#} 
#
#    
#    
    
    

    def mousePressEvent(self, event):
        """
        Right Mouse click shall have no function, Therefore pass only left 
        click event
        @purpose: Change inherited mousePressEvent
        @param event: Event Parameters passed to function
        """
        pass
        #scene=self.scene()
     
#        if event.button() == QtCore.Qt.LeftButton:
#            super(ShapeClass, self).mousePressEvent(event)

    def setSelected(self,flag=True,blockSignals=False):
        """
        Override inherited function to turn off selection of Arrows.
        @param flag: The flag to enable or disable Selection
        """
        self.starrow.setSelected(flag)
        self.enarrow.setSelected(flag)
        self.stmove.setSelected(flag)

        super(ShapeClass, self).setSelected(flag)

        if self.selectionChangedCallback and not blockSignals:
            self.selectionChangedCallback(self, flag)

    def setDisable(self,flag=False,blockSignals=False):
        """
        New implemented function which is in parallel to show and hide. 
        @param flag: The flag to enable or disable Selection
        """
        self.disabled=flag
        scene=self.scene()

        if not(scene.showDisabled) and flag:
            self.hide()
            self.starrow.setSelected(False)
            self.enarrow.setSelected(False)
            self.stmove.setSelected(False)
        else:
            self.show()

        self.update(self.boundingRect()) #Needed to refresh view when setDisabled() function is called from a TreeView event

        if self.enableDisableCallback and not blockSignals:
            self.enableDisableCallback(self, not flag)

    def isDisabled(self):
        """
        Returns the state of self.Disabled
        """
        return self.disabled

    def setToolPathOptimized(self,flag=False):
        """
        @param flag: The flag to enable or disable tool path optimisation for this shape
        """
        self.send_to_TSP=flag

    def isToolPathOptimized(self):
        """
        Returns the state of self.send_to_TSP
        """
        return self.send_to_TSP

    def AnalyseAndOptimize(self):
        """ 
        This method is called after the shape has been generated before it gets
        plotted to change all shape direction to a CW shape.
        FIXME
        """ 
        
        logger.debug(self.tr("Analysing the shape for CW direction Nr: %s") % (self.nr))
        #Optimization for closed shapes
        if self.closed:
            #Startwert setzen f�r die erste Summe
            #Start value for the first sum
            start, dummy = self.geos[0].get_start_end_points(0)
            summe = 0.0
            for geo in self.geos:
                if geo.type == 'LineGeo':
                    ende, dummy = geo.get_start_end_points(1)
                    summe += (start.x + ende.x) * (ende.y - start.y) / 2
                    start = deepcopy(ende)
                elif geo.type == 'ArcGeo':
                    segments = int((abs(degrees(geo.ext)) // 90) + 1)
                    for i in range(segments): 
                        ang = geo.s_ang + (i + 1) * geo.ext / segments
                        ende = Point(x=(geo.O.x + cos(ang) * abs(geo.r)), y=(geo.O.y + sin(ang) * abs(geo.r)))
                        summe += (start.x + ende.x) * (ende.y - start.y) / 2
                        start = deepcopy(ende)

            if summe > 0.0:
                self.reverse()
                logger.debug(self.tr("Had to reverse the shape to be ccw"))
               

    def FindNearestStPoint(self,StPoint=Point(x=0.0, y=0.0)):
        """
        Find Nearest Point to given StartPoint. This is used to change the
        start of closed contours
        @param StPoint: This i sthe point for which the nearest point shall
        be searched.
        """
        
        
        if self.closed:
            logger.debug(self.tr("Clicked Point: %s") %StPoint)
            start, dummy=self.geos[0].get_start_end_points(0,self.parent)
            min_distance=start.distance(StPoint)
            
            logger.debug(self.tr("Old Start Point: %s") %start)
            
            min_geo_nr=0
            for geo_nr in range(1,len(self.geos)):
                start, dummy=self.geos[geo_nr].get_start_end_points(0,self.parent)
                
                if (start.distance(StPoint)<min_distance):
                    min_distance=start.distance(StPoint)
                    min_geo_nr=geo_nr
    
            #Overwrite the geometries in changed order.
            self.geos=self.geos[min_geo_nr:len(self.geos)]+self.geos[0:min_geo_nr]
            
            start, dummy=self.geos[0].get_start_end_points(0,self.parent)
            logger.debug(self.tr("New Start Point: %s") %start)
                     
    def reverse(self):
        """ 
        Reverses the direction of the whole shape (switch direction).
        """ 
        self.geos.reverse()
        for geo in self.geos: 
            geo.reverse()
            


    def reverseGUI(self):
        """
        This function is called from the GUI if the GUI needs to be updated after
        the reverse of the shape to.
        """
        start, start_ang = self.get_st_en_points(0)
        end, end_ang = self.get_st_en_points(1)
        
        self.update(self.boundingRect())
        self.enarrow.reverseshape(end,end_ang)
        self.starrow.reverseshape(start,start_ang)
        self.stmove.reverseshape(start,start_ang)
        
    def switch_cut_cor(self):
        """ 
        Switches the cutter direction between 41 and 42.
        """ 
        if self.cut_cor == 41:
            self.cut_cor = 42
        elif self.cut_cor == 42:
            self.cut_cor = 41
            
        self.updateCutCor()

    def get_st_en_points(self, dir=None):
        """
        Returns the start/end Point and its direction
        @param direction: 0 to return start Point and 1 to return end Point
        @return: a list of Point and angle 
        """
        start, start_ang=self.geos[0].get_start_end_points(0,self.parent)
        ende, end_ang=self.geos[-1].get_start_end_points(1,self.parent)
        
        if dir==None:
            return start,ende
        elif dir==0:
            return start,start_ang
        elif dir==1:
            return ende, end_ang
        
    def make_papath(self):
        """
        To be called if a Shape shall be printed to the canvas
        """
        start, start_ang=self.get_st_en_points()
        
        self.path=QtGui.QPainterPath()

        self.path.moveTo(start.x,-start.y)
        
        logger.debug(self.tr("Adding shape to Scene Nr: %i") % (self.nr))
        
        for geo in self.geos:
            geo.add2path(papath=self.path,parent=self.parent)
            
    
    def update_plot(self):
        """
        This function is called from the GUI if the GUI needs to be updated after
        the reverse of the shape to.
        """
        #self.update(self.boundingRect())
        start, start_ang = self.get_st_en_points(0)
        self.starrow.updatepos(start, angle=start_ang)
        
        end, end_ang = self.get_st_en_points(1)
        self.enarrow.updatepos(end, angle=end_ang)

        self.stmove.update_plot(start, angle=start_ang)
        
    def updateCutCor(self):
        """
        This function is called to update the Cutter Correction and therefore 
        the  startmoves if smth. has changed or it shall be generated for 
        first time.
        FIXME This shall be different for Just updating it or updating it for 
        plotting.
        """
        self.stmove.updateCutCor(self.cut_cor)
        
    def updateCCplot(self):
        """
        This function is called to update the Cutter Correction Plot and therefore 
        the  startmoves if smth. has changed or it shall be generated for 
        first time.
        """
        self.stmove.updateCCplot()  
        
            
    def Write_GCode(self, LayerContent=None, PostPro=None):
        """
        This method returns the string to be exported for this shape, including
        the defined start and end move of teh shape.
        @param LayerContent: This parameter includes the parent LayerContent 
        which includes tool and additional cutting parameters.
        @param PostPro: this is the Postprocessor class including the methods
        to export        
        """
        #initialisation of the string
        exstr=""
        
        #Create the Start_moves once again if something was changed.
        self.stmove.make_start_moves()
        
        #Calculate tool Radius.        
        tool_rad = LayerContent.tool_diameter / 2

        #BaseEntitie created to add the StartMoves etc. This Entitie must not
        #be offset or rotated etc.
        BaseEntitie = EntitieContentClass(Nr= -1, Name='BaseEntitie',
                                        parent=None,
                                        children=[],
                                        p0=Point(x=0.0, y=0.0),
                                        pb=Point(x=0.0, y=0.0),
                                        sca=[1, 1, 1],
                                        rot=0.0)


        #Get the mill settings defined in the GUI
        safe_retract_depth = LayerContent.axis3_retract
        safe_margin = LayerContent.axis3_safe_margin
        #If defined, choose the parameters from the Shape itself. Otherwise, choose the parameters from the parent Layer
        max_slice = LayerContent.axis3_slice_depth if self.axis3_slice_depth is None else self.axis3_slice_depth
        workpiece_top_Z = LayerContent.axis3_start_mill_depth if self.axis3_start_mill_depth is None else self.axis3_start_mill_depth
        initial_mill_depth = workpiece_top_Z - abs(max_slice) #We want to mill the piece, even for the first pass, so remove one "slice"
        depth = LayerContent.axis3_mill_depth if self.axis3_mill_depth is None else self.axis3_mill_depth
        f_g1_plane = LayerContent.f_g1_plane if self.f_g1_plane is None else self.f_g1_plane
        f_g1_depth = LayerContent.f_g1_depth if self.f_g1_depth is None else self.f_g1_depth

        #Save the initial Cutter correction in a variable
        has_reversed = 0

        #If the Output Format is DXF do not perform more then one cut.
        if PostPro.vars.General["output_type"] == 'dxf':
            depth = max_slice

        if max_slice == 0:
            logger.error(self.tr("ERROR: Z infeed depth is null!"))

        if initial_mill_depth < depth:
            logger.warning(self.tr("WARNING: initial mill depth (%i) is lower than end mill depth (%i). Using end mill depth as final depth.") % (initial_mill_depth, depth))

            #Do not cut below the depth.
            initial_mill_depth = depth

        mom_depth = initial_mill_depth


        #Move the tool to the start.          
        exstr+=self.stmove.geos[0].Write_GCode(parent=BaseEntitie, PostPro=PostPro)
        
        #Add string to be added before the shape will be cut.
        exstr+=PostPro.write_pre_shape_cut()

        #Cutter radius compensation when G41 or G42 is on, AND cutter compensation option is set to be done outside the piece
        if self.cut_cor != 40 and PostPro.vars.General["cc_outside_the_piece"]:
            #Calculate the starting point without tool compensation
            #and add the compensation
            start, start_ang = self.get_st_en_points(0)
            exstr+=PostPro.set_cut_cor(self.cut_cor, start)
            
            exstr+=PostPro.chg_feed_rate(f_g1_plane) #Added by Xavier because of code move (see above)
            exstr+=self.stmove.geos[1].Write_GCode(parent=BaseEntitie, PostPro=PostPro)
            exstr+=self.stmove.geos[2].Write_GCode(parent=BaseEntitie, PostPro=PostPro)


        exstr+=PostPro.rap_pos_z(workpiece_top_Z + abs(safe_margin)) #Compute the safe margin from the initial mill depth
        exstr+=PostPro.chg_feed_rate(f_g1_depth)
        exstr+=PostPro.lin_pol_z(mom_depth)
        exstr+=PostPro.chg_feed_rate(f_g1_plane)

        #Cutter radius compensation when G41 or G42 is on, AND cutter compensation option is set to be done inside the piece
        if self.cut_cor != 40 and not PostPro.vars.General["cc_outside_the_piece"]:
            #Calculate the starting point without tool compensation
            #and add the compensation
            start, start_ang = self.get_st_en_points(0)
            exstr+=PostPro.set_cut_cor(self.cut_cor, start)
            
            exstr+=self.stmove.geos[1].Write_GCode(parent=BaseEntitie, PostPro=PostPro)
            exstr+=self.stmove.geos[2].Write_GCode(parent=BaseEntitie, PostPro=PostPro)


        #Write the geometries for the first cut
        for geo in self.geos:
            exstr+=geo.Write_GCode(self.parent, PostPro)

        #Turning the cutter radius compensation
        if (not(self.cut_cor == 40)) & (PostPro.vars.General["cancel_cc_for_depth"] == 1):
            ende, en_angle = self.get_st_en_points(1)
            if self.cut_cor == 41:
                pos_cut_out = ende.get_arc_point(en_angle - pi/2, tool_rad)
            elif self.cut_cor == 42:
                pos_cut_out = ende.get_arc_point(en_angle + pi/2, tool_rad)
            exstr+=PostPro.deactivate_cut_cor(pos_cut_out)
        
        #Numbers of loops
        snr = 0
        #Loops for the number of cuts
        while mom_depth > depth and max_slice != 0.0:
            snr += 1
            mom_depth = mom_depth - abs(max_slice)
            if mom_depth < depth:
                mom_depth = depth
            
            #Erneutes Eintauchen
            #???
            exstr+=PostPro.chg_feed_rate(f_g1_depth)
            exstr+=PostPro.lin_pol_z(mom_depth)
            exstr+=PostPro.chg_feed_rate(f_g1_plane)
            
            #If it is not a closed contour
            if self.closed == 0:
                self.reverse()
                self.switch_cut_cor()
                has_reversed = 1 - has_reversed #switch the "reversed" state (in order to restore it at the end)
                
            #If cutter correction is enabled
            if ((not(self.cut_cor == 40)) & (self.closed == 0))or(PostPro.vars.General["cancel_cc_for_depth"] == 1):
                #Calculate the starting point without tool compensation
                #and add the compensation
                start, start_ang = self.get_st_en_points(0)
                exstr+=PostPro.set_cut_cor(self.cut_cor, start)
                
            for geo_nr in range(len(self.geos)):
                exstr+=self.geos[geo_nr].Write_GCode(self.parent, PostPro)

            #Calculate the contour values with cutter radius compensation and without
            ende, en_angle = self.get_st_en_points(1)
            if self.cut_cor == 41:
                pos_cut_out = ende.get_arc_point(en_angle - pi/2, tool_rad)
            elif self.cut_cor == 42:
                pos_cut_out = ende.get_arc_point(en_angle + pi/2, tool_rad)

            #Turning off the cutter radius compensation if needed
            if (not(self.cut_cor == 40)) & (PostPro.vars.General["cancel_cc_for_depth"] == 1):
                exstr+=PostPro.deactivate_cut_cor(pos_cut_out)
        
        #Do the tool retraction
        exstr+=PostPro.lin_pol_z(workpiece_top_Z + abs(safe_margin))
        exstr+=PostPro.rap_pos_z(safe_retract_depth)

        #If cutter radius compensation is not turned off.
        if (not(self.cut_cor == 40)) & (not(PostPro.vars.General["cancel_cc_for_depth"])):
            #Calculate the contour values - with cutter radius compensation and without
            ende, en_angle = self.get_st_en_points(1)
            exstr+=PostPro.deactivate_cut_cor(ende)        

        #Initial value of direction restored if necessary
        if has_reversed != 0:
            self.reverse()
            self.switch_cut_cor()
            
        #Add string to be added before the shape will be cut.
        exstr+=PostPro.write_post_shape_cut()

        return exstr
