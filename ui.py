# -*- coding: utf-8 -*-

import pyqtgraph as pg
from pyqtgraph.dockarea import *
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import time
import config
import wsSetup

class EEG_Application(QtGui.QApplication):
    def __init__(self):
        super().__init__([])
        self.main_win = QtGui.QMainWindow()
        self.main_win.show()

        config.init()
        wsSetup.connect() 
        self.setupUi()

    def setupUi(self):
        """Create Basic UI layout"""
        self.main_win.setObjectName("MainWindow")
        self.main_win.setWindowTitle("EEG")
        self.main_win.resize(1800, 1000)

        dockarea = DockArea()

        raw_data_dock = self.create_raw_data_dock()
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
        QtCore.QMetaObject.connectSlotsByName(self.main_win)

    def create_raw_data_dock(self):
        raw_data_dock = Dock("Raw data plot")
        self.dtypeCombo = QtWidgets.QComboBox()
        self.dtypeCombo.setObjectName("dtypeCombo")
        self.dtypeCombo.addItem("125")
        self.dtypeCombo.addItem("500")
        self.dtypeCombo.addItem("1000")
        self.plot = pg.PlotWidget()
        self.plot.setMouseEnabled(x= False, y= True)
        raw_data_dock.addWidget(self.dtypeCombo, 0, 0, 1, 1)
        raw_data_dock.addWidget(self.plot, 1, 0, 2, 2)
        
        self.cursor = pg.InfiniteLine(pos=0)
        self.plot.addItem(self.cursor)

        self.curves = list()

        for i in range(64):
            r = (i + 60 ) * 5 % 256
            g = (i + 2 ) * 7 % 256
            b = (i + 15 ) * 11 % 256
            curve = self.plot.plot(pen=(r,g,b))
            curve.setData(config.rawList[i])
            self.curves.append(curve)
        
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_raw_plot)
        self.timer.start()

        return raw_data_dock

    def create_dummy_dock(self,title="Dummy"):
        dummy_dock = Dock(title)
        w3 = pg.PlotWidget(title="Plot inside dock")
        w3.plot(np.random.normal(size=100))
        dummy_dock.addWidget(w3)
        return dummy_dock

    def update_raw_plot(self):
        tol_start = time.time()
        for i in range(64):
            self.curves[i].setData(config.rawList[i])
        self.plot.setTitle("FPS: {:.1f}".format(1/(time.time()-tol_start)))
        self.cursor.setValue(config.currentIndex)