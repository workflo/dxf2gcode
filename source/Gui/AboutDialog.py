from PyQt4 import QtGui, QtCore
import logging
logger=logging.getLogger("Gui.AboutDialog") 

class myAboutDialog(QtGui.QDialog):
    
    def __init__(self,title="Test",message="Test Text"):
        super(myAboutDialog, self).__init__()

        self.title=title
        self.message=message
        
        self.initUI()
        
    def initUI(self):      

        vbox = QtGui.QVBoxLayout(self)
        grid1 = QtGui.QGridLayout()
        grid1.setSpacing(10)

        self.text=QtGui.QTextBrowser()
        self.text.setReadOnly(True)
        self.text.setOpenExternalLinks(True)
        self.text.append(self.message)
        self.text.moveCursor(QtGui.QTextCursor.Start)
        self.text.ensureCursorVisible()
        
        vbox.addWidget(self.text)
       
        self.setLayout(vbox)
        self.setMinimumSize(550, 450)
        self.setGeometry(200, 150, 550, 800)
        self.setWindowTitle(self.title)
        
        self.exec_()
    
