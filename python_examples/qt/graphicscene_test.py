from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
class myLineItem(QGraphicsLineItem):
    def __init__(self,line):
        QGraphicsLineItem.__init__(self,line)
    def paint(self, painter, options, widget):
        print "Painting"
        QGraphicsLineItem.paint(self, painter,options,widget)
        #self.setPen(QPen(Qt.red))
app=QApplication(sys.argv)
scene=QGraphicsScene()
l=myLineItem(QLineF(-20,0,20,2000))



scene.addItem(l)

view= QGraphicsView(scene)
view.show();
scene.setSceneRect(0,0,800,600)
app.exec_()

