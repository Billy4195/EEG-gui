# -*- coding: utf-8 -*-

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
import ScaleUI
from ws_data import WS_Data

class Plot_Scale_Line(object):
    def __init__(self, plot):
        self.v_grid_lines = list()
        for i in range(11):
            grid_lines = pg.InfiniteLine(pos=i, pen=pg.mkPen(color=(192, 192, 192), style=QtCore.Qt.DotLine))
            self.v_grid_lines.append(grid_lines)
            plot.addItem(grid_lines)

        self.zero_base_lines = list()
        self.neg_base_lines = list()
        self.pos_base_lines = list()
        for i in range(1,65):
            zero_line = pg.InfiniteLine(pos=i*10, angle=180, pen=(128, 128, 128))
            neg_line = pg.InfiniteLine(pos=i*10 - 3, angle=180, pen=pg.mkPen(color=(80, 80, 80), style=QtCore.Qt.DotLine))
            pos_line = pg.InfiniteLine(pos=i*10 + 3, angle=180, pen=pg.mkPen(color=(80, 80, 80), style=QtCore.Qt.DotLine))
            self.zero_base_lines.append(zero_line)
            self.neg_base_lines.append(neg_line)
            self.pos_base_lines.append(pos_line)
            plot.addItem(zero_line)
            plot.addItem(neg_line)
            plot.addItem(pos_line)

    def update(self, selected_channels, axises_tick):
        for idx, (val, label) in enumerate(axises_tick):
            self.v_grid_lines[idx].setValue(val)
        for i in range(64):
            if i < len(selected_channels):
                self.zero_base_lines[i].show()
                self.neg_base_lines[i].show()
                self.pos_base_lines[i].show()
            else:
                self.zero_base_lines[i].hide()
                self.neg_base_lines[i].hide()
                self.pos_base_lines[i].hide()
                continue

class Raw_Data_Dock(Dock):
    resized = QtCore.pyqtSignal()
    def __init__(self, url=None):
        """
        Initialize the UI and create ``WS_Data`` to connect to web socket
        url: The url for web socket to connect with
        """
        super().__init__("Raw Data Plot")

        if url is None:
            ws_url = "ws://localhost:8888"
        else:
            ws_url = url

        self.ws_data = WS_Data(url=ws_url)
        self.cursor_time = None
        self.timer_interval = 0.1
        self.curve_size = 27 # 1080 / 2 / 20
        self.selected_channels = list(range(1, 65))
        self.raw_data_mode = "Scan"
        #tmp
        self.saving_file = False
        self.init_ui()
        self.setup_signal_handler()

    def init_ui(self):
        self.mode_btn = QtGui.QPushButton("Change to Scroll Mode")
        self.dtypeCombo = QtWidgets.QComboBox()
        self.dtypeCombo.setObjectName("dtypeCombo")
        self.dtypeCombo.addItem("125")
        self.dtypeCombo.addItem("500")
        self.dtypeCombo.addItem("1000")
        self.ch_select_btn = QtGui.QPushButton("Select Channels")
        self.scale_adjust_btn = QtGui.QPushButton("Adjust Scales")
        self.event_table_btn = QtGui.QPushButton("Show Events")
        #tmp
        self.save_file_btn = QtGui.QPushButton("Save file")

        self.plot = pg.PlotWidget()
        self.plot.setMouseEnabled(x= False, y= False)
        self.plot.setLimits(xMin=0, maxXRange=10)
        self.plot.enableAutoRange(x=True, y=False)
        self.scroll = QtGui.QScrollBar()

        raw_plot_widget = QtGui.QWidget()
        plot_layout = QtGui.QHBoxLayout(raw_plot_widget)
        plot_layout.setSpacing(0)
        plot_layout.addWidget(self.plot)
        plot_layout.addWidget(self.scroll)

        self.addWidget(self.mode_btn, 0, 0, 1, 1)
        self.addWidget(self.dtypeCombo, 0, 1, 1, 1)
        #tmp
        self.addWidget(self.save_file_btn, 0, 2, 1, 1)
        self.addWidget(self.ch_select_btn, 1, 0, 1, 1)
        self.addWidget(self.scale_adjust_btn, 1, 1, 1, 1)
        self.addWidget(self.event_table_btn, 1, 2, 1, 1)
        self.addWidget(raw_plot_widget, 2, 0, 4, 4)

        self.cursor = pg.InfiniteLine(pos=0)
        self.plot.addItem(self.cursor)

        self.scale_lines = Plot_Scale_Line(self.plot)
            
        self.curves = list()
        for i in range(64):
            r = (i + 60 ) * 5 % 256
            g = (i + 2 ) * 7 % 256
            b = (i + 15 ) * 11 % 256
            curve = self.plot.plot(pen=(r,g,b))
            self.curves.append(curve)
        self.update_curves_size()

        self.event_lines = list()
        for i in range(20):
            event_line = pg.InfiniteLine(pos=0)
            self.event_lines.append(event_line)
            self.plot.addItem(event_line)
            event_line.hide()
        
        self.eventTable = QtGui.QTableWidget()
        self.eventTable.setColumnCount(3)
        self.eventTable.setHorizontalHeaderLabels(['Time', 'Name', 'Duration'])

    def setup_signal_handler(self):
        self.resized.connect(self.update_curves_size)
        self.mode_btn.clicked.connect(self.raw_data_mode_handler)
        self.ch_select_btn.clicked.connect(self.show_channel_select_window)
        self.scale_adjust_btn.clicked.connect(self.show_scale_adjust_window)
        self.event_table_btn.clicked.connect(self.show_event_table_window)
        self.scroll.valueChanged.connect(self.update_curves_size)
        #tmp
        self.save_file_btn.clicked.connect(self.save_btn_handler)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.timer_interval*1000)
        self.timer.timeout.connect(self.update_raw_plot)
        self.timer.start()

    def update_curves_size(self):
        geo = self.plot.frameGeometry()
        
        scroll_val = self.scroll.value()
        num_show_curves = geo.height() // self.curve_size
        num_select_channels = len(self.selected_channels)
        if num_select_channels < num_show_curves:
            num_show_curves = len(self.selected_channels)

        maxY = (num_select_channels - scroll_val) * 10 + 5
        minY = (num_select_channels - scroll_val - num_show_curves) * 10 + 5
        if minY < 0:
            minY = 0

        self.plot.setYRange(minY, maxY, padding=0)
        
        self.scroll.setMaximum(num_select_channels - num_show_curves)

    def update_raw_plot(self):
        if not self.ws_data.ws.sock or not self.ws_data.ws.sock.connected:
            return
        if not self.ws_data.decimated_data_time:
            return
        if self.cursor_time is None:
            #TODO determine the start cursor_time
            self.cursor_time = self.ws_data.decimated_data_time[-1]
        elif self.ws_data.decimated_data_time[-1] - self.cursor_time > self.timer_interval:
            self.cursor_time += self.timer_interval
        else:
            self.cursor_time = self.ws_data.decimated_data_time[-1]
        tol_start = time.time()
        plot_data = self.ws_data.get_plot_decimated_data(mode=self.raw_data_mode,
                            channels=self.selected_channels,
                            cursor=self.cursor_time)
        
        for i in range(len(self.event_lines)):
            self.event_lines[i].hide()

        axis = self.plot.getAxis("bottom")
        axis.setTicks([plot_data.axises_tick["bottom"]])
        axis = self.plot.getAxis("left")
        axis.setTicks([plot_data.axises_tick["left"]])

        self.scale_lines.update(self.selected_channels,
                                plot_data.axises_tick["bottom"])
        for i in range(64):
            if i < len(self.selected_channels):
                self.curves[i].show()
            else:
                self.curves[i].hide()
                continue

            self.curves[i].setData(plot_data.time_data, plot_data.channel_data[i])
        
        for idx in range(len(plot_data.trans_events)):
            self.event_lines[idx].setValue(plot_data.trans_events[idx]['time'])
            self.event_lines[idx].show()

        self.plot.setTitle("FPS: {:.1f}".format(1/(time.time()-tol_start)))
        self.cursor.setValue(self.cursor_time % 10)
        self.ws_data.clean_oudated_data(self.cursor_time)

        self.update_event_table()

    def raw_data_mode_handler(self):
        if self.raw_data_mode == "Scan":
            self.raw_data_mode = "Scroll"
            self.mode_btn.setText("Change to Scan Mode")
            self.cursor.hide()

        elif self.raw_data_mode == "Scroll":
            self.raw_data_mode = "Scan"
            self.mode_btn.setText("Change to Scroll Mode")
            self.cursor.show()
            
    def show_scale_adjust_window(self):
        self.scale_adjust_win = QtGui.QDialog(self)
        self.scale_adjust_win.setWindowTitle("Adjust Scales")
        self.scale_adjust_win.resize(500,100)
        gridlayout = QtGui.QGridLayout(self.scale_adjust_win)

        self.slider = ScaleUI.Slider(self.ws_data.get_scale_line_rela_val(),
                                        1, 5)

        button_box = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal,
                                            self.scale_adjust_win)
        button_box.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
        button_box.addButton("Apply", QtGui.QDialogButtonBox.AcceptRole)

        button_box.accepted.connect(self.scale_adjust_handler)
        button_box.rejected.connect(self.scale_adjust_win.close)

        gridlayout.addWidget(self.slider,0,0)
        gridlayout.addWidget(button_box,1,0)
        self.scale_adjust_win.show()
    
    def scale_adjust_handler(self):
        self.ws_data.update_scale_line_rela_val(self.slider.get_value())
        self.scale_adjust_win.close()

    def show_channel_select_window(self):
        self.channel_selector_win = QtGui.QDialog(self)
        self.channel_selector_win.setWindowTitle("Select Channels")
        self.channel_selector_win.resize(500,400)
        vlayout = QtGui.QVBoxLayout(self.channel_selector_win)

        self.channel_selector = QtGui.QListWidget()
        self.channel_selector.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        for i in range(1, 65):
            item = QtGui.QListWidgetItem(self.channel_selector)
            item.setText("Channel {}".format(i))
            item.setData(QtCore.Qt.UserRole, i)
            if i in self.selected_channels:
                item.setSelected(True)

        button_box = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal,
                                            self.channel_selector_win)
        button_box.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
        button_box.addButton("Apply", QtGui.QDialogButtonBox.AcceptRole)
        clear_all_btn = button_box.addButton("Clear All",
                                QtGui.QDialogButtonBox.ResetRole)
        select_all_btn = button_box.addButton("Select All",
                                QtGui.QDialogButtonBox.ActionRole)

        button_box.accepted.connect(self.channel_select_handler)
        button_box.rejected.connect(self.channel_selector_win.close)
        clear_all_btn.clicked.connect(self.select_none_channels)
        select_all_btn.clicked.connect(self.select_all_channels)

        vlayout.addWidget(self.channel_selector)
        vlayout.addWidget(button_box)
        self.channel_selector_win.show()

    def channel_select_handler(self):
        self.selected_channels = sorted([item.data(QtCore.Qt.UserRole) for item in self.channel_selector.selectedItems()])
        self.update_curves_size()
        self.channel_selector_win.close()

    def select_all_channels(self):
        for idx in range(len(self.channel_selector)):
            self.channel_selector.item(idx).setSelected(True)
    
    def select_none_channels(self):
        for idx in range(len(self.channel_selector)):
            self.channel_selector.item(idx).setSelected(False)

    def show_event_table_window(self):
        self.event_table_win = QtGui.QDialog(self)
        self.event_table_win.setWindowTitle("Event List")
        self.event_table_win.resize(500,400)
        gridlayout = QtGui.QGridLayout(self.event_table_win)
        gridlayout.addWidget(self.eventTable)
        self.update_event_table()
        self.event_table_win.show()

    def update_event_table(self):
        self.eventTable.clearContents()
        if len(self.ws_data.events) > 0:
            self.eventTable.setRowCount(len(self.ws_data.events))
            for row, event in enumerate(self.ws_data.events):
                for key, value in event.items():
                    if key is 'time':
                        self.eventTable.setItem(row, 0, QtGui.QTableWidgetItem(str(value)))
                    elif key is 'name':
                        self.eventTable.setItem(row, 1, QtGui.QTableWidgetItem(str(value)))
                    elif key is 'duration':
                        self.eventTable.setItem(row, 2, QtGui.QTableWidgetItem(str(value)))

    def resizeEvent(self, event):
        self.resized.emit()
        return super().resizeEvent(event)

    def wheelEvent(self, event):
        scroll_change = -(event.angleDelta().y() // 120)
        scroll_val = self.scroll.value()
        self.scroll.setValue(scroll_val + scroll_change)

    def save_btn_handler(self):
        if not self.saving_file:
            self.ws_data.open_raw_record_file("tmp.csv")
            self.saving_file = True
            self.save_file_btn.setText("Stop saving")
        else:
            self.ws_data.close_raw_record_file()
            self.saving_file = False
            self.save_file_btn.setText("Save file")

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

        raw_data_dock = Raw_Data_Dock()
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

    def create_dummy_dock(self,title="Dummy"):
        dummy_dock = Dock(title)
        w3 = pg.PlotWidget(title="Plot inside dock")
        w3.plot(np.random.normal(size=100))
        dummy_dock.addWidget(w3)
        return dummy_dock