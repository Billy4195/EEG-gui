# -*- coding: utf-8 -*-

import pyqtgraph as pg
from pyqtgraph.dockarea import *
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import time
import config
import wsSetup
import websocket
import threading
import json
import logging

class WS_Data(object):
    """
    This class create a websocket and handle data which is received from socket
    """
    def __init__(self, url, channel_num=64, scale_line_rela_val=2,
         scale_line_real_val=3, data_window_height=10,
         raw_plot_sample_rate=1000):
        """
        Create a websocket and setup its handler

        url:
            The url for web socket to connect with

        channel_num:
            The number of channels

        scale_line_rela_val:
            The relative value between scale line and real value in channel
            data

        scale_line_real_val:
            The real value of scale line associates with plot y axis

        data_window_height:
            The window height is the shift height of each channel data

        """
        self.url = url
        self.channel_num = channel_num
        self.scale_line_rela_val = scale_line_rela_val
        self.scale_line_real_val = scale_line_real_val
        self.data_window_height = data_window_height
        self.raw_plot_sample_rate = raw_plot_sample_rate
        self.raw_data_time = list()
        self.raw_data = list()
        self.transed_raw_data = list()

        self.ws = websocket.WebSocketApp(url,
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        self.ws_thread = threading.Thread(target=self.on_connect)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        self.events = list()
        for i in range(self.channel_num):
            self.raw_data.append(list())
            self.transed_raw_data.append(list())

    def on_connect(self):
        while True:
            self.ws.run_forever()
            logging.error("Connection closed reconnect in 0.5 sec")
            time.sleep(0.5)

    def on_message(self, ws, message):
        """
        Handle data from socket and store it into different plot's data
        structure
        """
        raw = json.loads(message)
        try:
            self.add_plot_raw_data(raw)
        except Exception as e:
            logging.error(str(e))

    def on_error(self, ws, error):
        """
        Handle websocket error
        """
        pass

    def on_close(self, ws):
        """
        Handle websocket close event
        """
        pass

    def add_plot_raw_data(self, data):
        """
        Store the raw data plot data received from websocket, and store the
        transformed data.

        The transformation is to let original data fit into specific scale.
        """
        if len(data['data']['eeg']) != self.channel_num:
            raise AssertionError("The received raw data unmatch channel num")

        time = data['tick'] / self.raw_plot_sample_rate

        self.raw_data_time.append(time)
        for idx, ori_data in enumerate(data['data']['eeg']):
            self.raw_data[idx].append(ori_data)
            self.transed_raw_data[idx].append(self._tranform_data(ori_data))

        if data['data']['event']:
            self.events.append({
                'time': time,
                'name': data['data']['event']['name'],
                'duration': data['data']['event']['duration']
            })

    def get_plot_raw_data(self, mode="Scan", channels=None):
        """
        Return the raw data used to draw ``mode`` mode raw data plot
        The return value follow the order of channels.

        The ``channels`` is the index of channels,
        if ``channels`` is None, return all channels.
        [
            [
                {x: 0.5, y: 1.0},
                ...
            ],
            ...
        ]
        """
        pass

    def get_plot_scale_line_pos(self, channels=None):
        """
        Return the scale lines position of ``index`` channels in raw data plot.
        The return value follow the order of channels.

        The ``channels`` is the index of channels,
        if ``channels`` is None, return all channels.

        If
            data_window_height = 10
            scale_line_real_val = 3
        Then
        {
            pos: [13, 23, 33, ...]
            ori: [10, 20, 30, ...]
            neg: [7 , 17, 27, ...]
        }
        """
        if channels is None:
            channels = range(1, self.channel_num)

        pos = list()
        ori = list()
        neg = list()
        for ch_origin in range(1, len(channels)+1):
            ori.append(ch_origin*self.data_window_height)
            pos.append(ori[-1]+self.scale_line_real_val)
            neg.append(ori[-1]-self.scale_line_real_val)

        return dict(pos=pos, ori=ori, neg=neg)

    def _tranform_data(self,ori_data):
        """
        Transform the original data to the specify scale
        """
        return self.scale_line_real_val * (ori_data/self.scale_line_rela_val)


class Raw_Data_Dock(Dock):
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
        self.init_ui()

    def init_ui(self):
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
        self.plot.setLimits(xMin=0, xMax=2500, yMin=-10, yMax=650, minYRange=-10, maxYRange=650)
        self.addWidget(self.mode_btn, 0, 0, 1, 1)
        self.addWidget(self.dtypeCombo, 0, 1, 1, 1)
        self.addWidget(self.ch_select_btn, 0, 2, 1, 1)
        self.addWidget(self.plot, 1, 0, 4, 4)

        self.cursor = pg.InfiniteLine(pos=0)
        self.plot.addItem(self.cursor)

        for i in range(10):
            self.tmp_ref_line = pg.InfiniteLine(pos=i*250, pen=pg.mkPen(color=(192, 192, 192), style=QtCore.Qt.DotLine))
            self.plot.addItem(self.tmp_ref_line)

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
        self.timer.setInterval(self.timer_interval*1000)
        self.timer.timeout.connect(self.update_raw_plot)
        self.timer.start()
        self.mode_btn.clicked.connect(self.raw_data_mode_handler)
        self.ch_select_btn.clicked.connect(self.show_channel_select_window)
        self.selected_channels = list(range(64))

    def update_raw_plot(self):
        if not self.ws_data.ws.sock or not self.ws_data.ws.sock.connected:
            return

        if self.cursor_time is None:
            #TODO determine the start cursor_time
            self.cursor_time = self.ws_data.raw_data_time[-1]
        else:
            self.cursor_time += self.timer_interval
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
        self.channel_selector_win = QtGui.QDialog(self)
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