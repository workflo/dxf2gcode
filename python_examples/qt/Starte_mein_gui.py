# -*- coding: utf-8 -*-

"""The user interface for our app"""

import os,sys

# Import Qt modules
from PyQt4 import QtCore,QtGui

# Import the compiled UI module
from mein_test import Ui_MainWindow

# Create a class for our main window
class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
    
        # This is always the same
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.createActions()
        
        self.myGraphicsScene=myGraphicsScene()
        self.myGraphicsScene.addLine()
        
        self.ui.mygraphicsView.setScene(self.myGraphicsScene)
        self.ui.mygraphicsView.show()
        
    def createActions(self):
        

        self.ui.actionExit.triggered.connect(self.close)
        
        self.ui.actionLoad_File.triggered.connect(self.showDialog)
        
        self.ui.actionAbout.triggered.connect(self.about)
        
        
    def showDialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                    'E:')

        
    def about(self):
        QtGui.QMessageBox.about(self, "About Diagram Scene",
                "The <b>Diagram Scene</b> example shows use of the graphics framework.")
        
class myGraphicsScene(QtGui.QGraphicsScene):        
    def __init__(self):
        QtGui.QGraphicsScene.__init__(self)
        self.setSceneRect(0,-600,800,500)
        
    def addLine(self):
        l=myLineItem(QtCore.QLineF(0,0,2000,-200))
        self.addItem(l)

class myLineItem(QtGui.QGraphicsLineItem):
    def __init__(self,line):
        QtGui.QGraphicsLineItem.__init__(self,line)
    def paint(self, painter, options, widget):
        print "Painting"
        QtGui.QGraphicsLineItem.paint(self, painter,options,widget)
        #self.setPen(QPen(Qt.red))
        


def main():
    # Again, this is boilerplate, it's going to be the same on
    # almost every app you write
    app = QtGui.QApplication(sys.argv)
    window=Main()
    window.show()
    

    # It's exec_ because exec is a reserved word in Python
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

