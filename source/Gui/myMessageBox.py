# -*- coding: utf-8 -*-
"""
Special purpose canvas including all required plotting function etc.
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose:  Plotting all
@author: Christian Kohl�ffel 
@since:  22.04.2011
@license: GPL
"""
from PyQt4 import QtCore, QtGui
import Core.Globals as g
import Core.constants as c

class myMessageBox(QtGui.QTextBrowser):
    """
    The myMessageBox Class performs the write functions in the Message Window.
    The previous defined MyMessageBox_org class is used as output (Within ui). 
    @sideeffect: None                            
    """
        
    def __init__(self, origobj):
        """
        Initialization of the myMessageBox class.
        @param origobj: This is the reference to to parent class initialized 
        previously.
        """
        super(myMessageBox, self).__init__() 
        self.setOpenExternalLinks(True)
        
        self.append("You are using DXF2GCODE")
        self.append("Version %s (%s)" %(c.VERSION,c.DATE))
        self.append("For more information und updates visit:")
        self.append("<a href=http://code.google.com/p/dxf2gcode>http://code.google.com/p/dxf2gcode</a>")

    def write(self,charstr):
        """
        The function is called by the window logger to write the log message to
        the Messagebox
        @param charstr: The log message which will be written.
        """

        self.append(charstr[0:-1])
        self.verticalScrollBar().setValue(1e9)
