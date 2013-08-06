#!/usr/bin/python

# openfiledialog.py

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore


class OpenFile(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)

        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('OpenFile')

        self.textEdit = QtGui.QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.statusBar()
       
        self._label = QtGui.QLabel("Einkaufszaehler")
        self.statusBar().addPermanentWidget(self._label)
        self.statusBar().addPermanentWidget(self._label)

        self._label.setText("BLA2")

        self.setFocus()

        openFile = QtGui.QAction(QtGui.QIcon('open.png'), 'Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open new File')
        self.connect(openFile, QtCore.SIGNAL('triggered()'), self.showDialog)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)
    
    def showDialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open file',
                    '/home')
        fname = open(filename)
        data = fname.read()
        self.textEdit.setText(data)

app = QtGui.QApplication(sys.argv)
fd = OpenFile()
fd.show()
app.exec_()

