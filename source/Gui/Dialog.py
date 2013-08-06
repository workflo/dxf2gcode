from PyQt4 import QtGui, QtCore
import logging
logger=logging.getLogger("Gui.Dialog") 

class myDialog(QtGui.QDialog):
    
    def __init__(self,title="Test",label=('Value1'),value=(1.0)):
        super(myDialog, self).__init__()

        
        logger.debug(title)
        logger.debug(label)
        logger.debug(value)
        
        self.title=title
        self.label=label
        self.value=value
        
        self.result=None
        
        if not(len(label)==len(value)):
            raise Exception, "Number of labels different to number of values"
        
        self.initUI()
        
    def initUI(self):      

        vbox = QtGui.QVBoxLayout(self)

        top = QtGui.QFrame(self)
        top.setFrameShape(QtGui.QFrame.StyledPanel)
 
        bottom = QtGui.QFrame(self)
        bottom.setFrameShape(QtGui.QFrame.StyledPanel)


        grid1 = QtGui.QGridLayout()
        grid1.setSpacing(10)
        self.lineLabel=[]
        self.lineEdit=[]

        for i in range(len(self.label)):
            self.lineLabel.append(QtGui.QLabel(self.label[i]))
            self.lineEdit.append(QtGui.QLineEdit('%s' %self.value[i]))

            grid1.addWidget(self.lineLabel[i], i, 0)
            grid1.addWidget(self.lineEdit[i], i, 1)

        top.setLayout(grid1) 
        
        grid2 = QtGui.QGridLayout()
        grid2.setSpacing(5)
        
        okButton = QtGui.QPushButton("OK")
        cancelButton = QtGui.QPushButton("Cancel")
        
        okButton.clicked.connect(self.cbOK)
        cancelButton.clicked.connect(self.cbCancel)

        grid2.addWidget(okButton, 0, 0)
        grid2.addWidget(cancelButton, 0, 1) # 5, 1
        
        bottom.setLayout(grid2) 
          
        vbox.addWidget(top)
        vbox.addWidget(bottom)
        
        self.setLayout(vbox)

        self.setGeometry(300, 300, 50, 50)
        self.setWindowTitle(self.title)
        
        self.exec_()
        
    def cbOK(self):

        self.result=[]
        for lineEdit in self.lineEdit:
            self.result.append(lineEdit.text())
        self.close()
        
    def cbCancel(self):
        logger.debug('Cancel')
        self.close()
        
