# -*- coding: utf-8 -*-

import pyqtgraph as pg
from pyqtgraph.dockarea import *
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np

class EEG_Application(QtGui.QApplication):
    def __init__(self):
        super().__init__([])
        self.main_win = QtGui.QMainWindow()
        self.main_win.show()

        self.setupUi()

    def setupUi(self):
        self.main_win.setObjectName("MainWindow")
        self.main_win.resize(1800, 1000)
        self.centralwidget = QtWidgets.QWidget(self.main_win)
        self.centralwidget.setObjectName("centralwidget")
        dockarea = DockArea()

        raw_data_dock = Dock("Raw data plot")
        self.dtypeCombo = QtWidgets.QComboBox(self.centralwidget)
        self.dtypeCombo.setObjectName("dtypeCombo")
        self.dtypeCombo.addItem("")
        self.dtypeCombo.addItem("")
        self.dtypeCombo.addItem("")
        self.plot = pg.PlotWidget()
        self.plot.setMouseEnabled(x= False, y= True)
        raw_data_dock.addWidget(self.plot, 1, 0, 2, 2)
        raw_data_dock.addWidget(self.dtypeCombo, 0, 0, 1, 1)

        dockarea.addDock(raw_data_dock)
        left_bottom_dock = self.create_dummy_dock('Left bottom')
        dockarea.addDock(left_bottom_dock,'bottom',raw_data_dock)
        mid_top_dock = self.create_dummy_dock('Mid top')
        dockarea.addDock(mid_top_dock,'right',raw_data_dock)
        mid_bottom_dock = self.create_dummy_dock("Mid bottom")
        dockarea.addDock(mid_bottom_dock,'right',left_bottom_dock)
        right_top_dock = self.create_dummy_dock("Right top")
        dockarea.addDock(right_top_dock,'right',mid_top_dock)
        right_bottom_dock = self.create_dummy_dock("Right bottom")
        dockarea.addDock(right_bottom_dock,'right',mid_bottom_dock)

        self.main_win.setCentralWidget(dockarea)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self.main_win)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.main_win.setWindowTitle(_translate("MainWindow", "EEG"))
        self.dtypeCombo.setItemText(0, _translate("MainWindow", "125"))
        self.dtypeCombo.setItemText(1, _translate("MainWindow", "500"))
        self.dtypeCombo.setItemText(2, _translate("MainWindow", "1000"))

    def create_dummy_dock(self,title="Dummy"):
        dummy_dock = Dock(title)
        w3 = pg.PlotWidget(title="Plot inside dock")
        w3.plot(np.random.normal(size=100))
        dummy_dock.addWidget(w3)
        return dummy_dock