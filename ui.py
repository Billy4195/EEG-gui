# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import pyqtgraph as pg
from pyqtgraph.dockarea import *
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import time
import websocket
import threading
import json
import logging
import math
import copy
from ws_data import WS_Data
from raw_data_plot import Raw_Data_Plot

class EEG_Application(QtGui.QApplication):
    def __init__(self):
        super().__init__([])
        self.main_win = QtGui.QMainWindow()
        self.main_win.show()

        self.setupUi()

    def setupUi(self):
        """Create Basic UI layout"""
        self.main_win.setObjectName("MainWindow")
        self.main_win.setWindowTitle("EEG")
        self.main_win.resize(1800, 1000)

        dockarea = DockArea()

        raw_data_plot= Raw_Data_Plot()
        self.raw_data_plot = raw_data_plot
        self.main_win.setCentralWidget(dockarea)
        QtCore.QMetaObject.connectSlotsByName(self.main_win)

    def create_dummy_dock(self,title="Dummy"):
        dummy_dock = Dock(title)
        w3 = pg.PlotWidget(title="Plot inside dock")
        w3.plot(np.random.normal(size=100))
        dummy_dock.addWidget(w3)
        return dummy_dock