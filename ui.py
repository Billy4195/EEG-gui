# -*- coding: utf-8 -*-

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(500, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.dtypeCombo = QtWidgets.QComboBox(self.centralwidget)
        self.dtypeCombo.setObjectName("dtypeCombo")
        self.dtypeCombo.addItem("")
        self.dtypeCombo.addItem("")
        self.dtypeCombo.addItem("")
        self.plot = pg.PlotWidget()
        self.plot.setMouseEnabled(x= False, y= True)
        self.gridLayout.addWidget(self.plot, 1, 0, 2, 2)
        self.gridLayout.addWidget(self.dtypeCombo, 0, 0, 1, 1)
        
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "EEG"))
        self.dtypeCombo.setItemText(0, _translate("MainWindow", "125"))
        self.dtypeCombo.setItemText(1, _translate("MainWindow", "500"))
        self.dtypeCombo.setItemText(2, _translate("MainWindow", "1000"))

