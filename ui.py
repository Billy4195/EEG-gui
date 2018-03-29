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
        self.raw_data_mode = "Scan"
        self.mode_btn = QtGui.QPushButton("Change to Scroll Mode")
        self.dtypeCombo = QtWidgets.QComboBox()
        self.dtypeCombo.setObjectName("dtypeCombo")
        self.dtypeCombo.addItem("125")
        self.dtypeCombo.addItem("500")
        self.dtypeCombo.addItem("1000")
        self.ch_select_btn = QtGui.QPushButton("Select Channels")
        self.plot = pg.PlotWidget()
        self.plot.setMouseEnabled(x= False, y= True)
        raw_data_dock.addWidget(self.mode_btn, 0, 0, 1, 1)
        raw_data_dock.addWidget(self.dtypeCombo, 0, 1, 1, 1)
        raw_data_dock.addWidget(self.ch_select_btn, 0, 2, 1, 1)
        raw_data_dock.addWidget(self.plot, 1, 0, 4, 4)

        self.cursor = pg.InfiniteLine(pos=0)
        self.plot.addItem(self.cursor)

        for i in range(64):
            self.zeroBaseLine = pg.InfiniteLine(pos=i*10, angle=180, pen=(128, 128, 128))
            self.negBaseLine = pg.InfiniteLine(pos=i*10 - 3, angle=180, pen=pg.mkPen(color=(80, 80, 80), style=QtCore.Qt.DotLine))
            self.posBaseLine = pg.InfiniteLine(pos=i*10 + 3, angle=180, pen=pg.mkPen(color=(80, 80, 80), style=QtCore.Qt.DotLine))
            self.plot.addItem(self.zeroBaseLine)
            self.plot.addItem(self.negBaseLine)
            self.plot.addItem(self.posBaseLine)
            
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
        self.mode_btn.clicked.connect(self.raw_data_mode_handler)
        self.ch_select_btn.clicked.connect(self.show_channel_select_window)
        self.selected_channels = list(range(64))
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
            if i not in self.selected_channels:
                self.curves[i].hide()
                continue
            else:
                self.curves[i].show()
            if self.raw_data_mode == "Scan":
                self.curves[i].setData(config.rawList[i][-config.currentIndex:]+config.rawList[i][:-config.currentIndex])
            elif self.raw_data_mode == "Scroll":
                self.curves[i].setData(config.rawList[i])
        self.plot.setTitle("FPS: {:.1f}".format(1/(time.time()-tol_start)))
        self.cursor.setValue(config.currentIndex)

    def raw_data_mode_handler(self):
        if self.raw_data_mode == "Scan":
            self.raw_data_mode = "Scroll"
            self.mode_btn.setText("Change to Scan Mode")
            self.cursor.hide()

        elif self.raw_data_mode == "Scroll":
            self.raw_data_mode = "Scan"
            self.mode_btn.setText("Change to Scroll Mode")
            self.cursor.show()

    def show_channel_select_window(self):
        self.channel_selector_win = QtGui.QDialog(self.main_win)
        self.channel_selector_win.setWindowTitle("Select Channels")
        self.channel_selector_win.resize(500,400)
        gridlayout = QtGui.QGridLayout(self.channel_selector_win)

        self.channel_selector = QtGui.QListWidget()
        self.channel_selector.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        for i in range(64):
            item = QtGui.QListWidgetItem(self.channel_selector)
            item.setText("Channel {}".format(i))
            item.setData(QtCore.Qt.UserRole, i)
            if i in self.selected_channels:
                item.setSelected(True)

        channel_selector_button_box = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal,self.channel_selector_win)
        channel_selector_button_box.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
        channel_selector_button_box.addButton("Select", QtGui.QDialogButtonBox.AcceptRole)
        select_all_btn = channel_selector_button_box.addButton("Select All", QtGui.QDialogButtonBox.ResetRole)
        channel_selector_button_box.accepted.connect(self.channel_select_handler)
        channel_selector_button_box.rejected.connect(self.channel_selector_win.close)
        select_all_btn.clicked.connect(self.select_all_channels)

        gridlayout.addWidget(self.channel_selector,0,0)
        gridlayout.addWidget(channel_selector_button_box,1,0)
        self.channel_selector_win.show()

    def channel_select_handler(self):
        self.selected_channels = [item.data(QtCore.Qt.UserRole) for item in self.channel_selector.selectedItems()]
        self.channel_selector_win.close()

    def select_all_channels(self):
        for idx in range(len(self.channel_selector)):
            self.channel_selector.item(idx).setSelected(True)
