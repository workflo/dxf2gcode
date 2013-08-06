# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'demo.ui'
#
# Created: Wed Nov 24 21:16:23 2010
#      by: PyQt4 UI code generator 4.5.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_DemoDialog(object):
    def setupUi(self, DemoDialog):
        DemoDialog.setObjectName("DemoDialog")
        DemoDialog.resize(473, 439)
        self.gridlayout = QtGui.QGridLayout(DemoDialog)
        self.gridlayout.setMargin(9)
        self.gridlayout.setSpacing(6)
        self.gridlayout.setObjectName("gridlayout")
        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setObjectName("vboxlayout")
        self.button1 = QtGui.QPushButton(DemoDialog)
        self.button1.setObjectName("button1")
        self.vboxlayout.addWidget(self.button1)
        self.button2 = QtGui.QPushButton(DemoDialog)
        self.button2.setObjectName("button2")
        self.vboxlayout.addWidget(self.button2)
        self.gridlayout.addLayout(self.vboxlayout, 1, 0, 1, 1)
        self.hboxlayout = QtGui.QHBoxLayout()
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setMargin(0)
        self.hboxlayout.setObjectName("hboxlayout")
        spacerItem = QtGui.QSpacerItem(131, 31, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.okButton = QtGui.QPushButton(DemoDialog)
        self.okButton.setObjectName("okButton")
        self.hboxlayout.addWidget(self.okButton)
        self.gridlayout.addLayout(self.hboxlayout, 3, 0, 1, 3)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem1, 2, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridlayout.addItem(spacerItem2, 0, 0, 1, 1)
        self.list = QtGui.QListWidget(DemoDialog)
        self.list.setObjectName("list")
        self.gridlayout.addWidget(self.list, 0, 2, 3, 1)
        self.graphicsView = QtGui.QGraphicsView(DemoDialog)
        self.graphicsView.setObjectName("graphicsView")
        self.gridlayout.addWidget(self.graphicsView, 0, 1, 3, 1)

        self.retranslateUi(DemoDialog)
        QtCore.QObject.connect(self.okButton, QtCore.SIGNAL("clicked()"), DemoDialog.accept)
        QtCore.QObject.connect(self.button2, QtCore.SIGNAL("clicked()"), self.list.clear)
        QtCore.QMetaObject.connectSlotsByName(DemoDialog)

    def retranslateUi(self, DemoDialog):
        DemoDialog.setWindowTitle(QtGui.QApplication.translate("DemoDialog", "PyUIC4 Demo Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.button1.setText(QtGui.QApplication.translate("DemoDialog", "Add items", None, QtGui.QApplication.UnicodeUTF8))
        self.button2.setText(QtGui.QApplication.translate("DemoDialog", "Clear list", None, QtGui.QApplication.UnicodeUTF8))
        self.okButton.setText(QtGui.QApplication.translate("DemoDialog", "OK", None, QtGui.QApplication.UnicodeUTF8))

