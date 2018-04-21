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

class Raw_Data_Plot_Data(object):
    def __init__(self, time_data, channel_data, events, mode, channels, cursor,
                    window_size=10):
        self.trans_events = copy.deepcopy(events)
        self.set_mode(mode)
        self.param = self.cal_mode_param(time_data, cursor, window_size)
        self.axises_tick = self.calculate_axises_tick(time_data, channels,
                                                    window_size)
        self.calculate_plot_data(time_data, channel_data, channels)
    def set_mode(self, mode):
        if mode not in ["Scan", "Scroll"]:
            raise NotImplementedError("{} mode has not be implemented".format(
                mode))
        else:
            self.mode = mode

    def cal_mode_param(self, time_data, cursor, window_size=10):
        """
        According to the mode, calculating index of important point in
        time_data, and return the important parameter
        """
        if self.mode == "Scan":
            return self.cal_scan_mode_param(time_data, cursor, window_size)

        elif self.mode == "Scroll":
            return self.cal_scroll_mode_param(time_data, cursor, window_size)

    def cal_scan_mode_param(self, time_data, cursor, window_size):
        """
        ##Scan Mode##
        if
            cursor = 17.2, window_size = 10
        then
            origin = 10
            last_origin = 7.299999999999999

        origin_idx: min(time_data >= origin)
        cursor_idx: max(time_data <= cursor)
        last_origin_idx: min(time_data > last_origin)

        Return:
        {
            "origin": 10,
            "cursor": 17.2,
            "last_origin": 7.299999999999999,
            "idx": {
                "origin": ``origin_idx``,
                "cursor": ``cursor_idx``,
                "last_origin": ``last_origin_idx``
            }
        }
        """
        origin = (cursor // window_size) * window_size
        last_origin = cursor - window_size + 0.1
        if last_origin < 0: last_origin = 0

        origin_idx = None
        cursor_idx = 0
        last_origin_idx = None
        for idx, d in enumerate(time_data):
            if origin_idx is None and d >= origin:
                origin_idx = idx
            if d <= cursor:
                cursor_idx = idx
            if last_origin_idx is None and d > last_origin:
                last_origin_idx = idx
            if d > cursor:
                break

        if origin_idx is None:
            origin_idx = 0
        if last_origin_idx is None:
            last_origin_idx = 0

        return dict(origin=origin, cursor=cursor, last_origin=last_origin,
                    idx=dict(
                        origin=origin_idx,cursor=cursor_idx,
                        last_origin=last_origin_idx)
                )

    def cal_scroll_mode_param(self, time_data, cursor, window_size):
        """
        cursor = 17.2
        origin = 7

        origin_idx: min(time_data >= origin)
        cursor_idx: max(time_data <= cursor)

        Return:
        {
            "origin": 10,
            "cursor": 17.2,
            "idx": {
                "origin": ``origin_idx``,
                "cursor": ``cursor_idx``
            }
        }
        """
        origin = cursor - window_size

        origin_idx = None
        cursor_idx = 0
        for idx, d in enumerate(time_data):
            if origin_idx is None and d >= origin:
                origin_idx = idx
            if d <= cursor:
                cursor_idx = idx
            if d > cursor:
                break

        if origin_idx is None:
            origin_idx = 0

        return dict(origin=origin, cursor=cursor,
                    idx=dict(origin=origin_idx,cursor=cursor_idx)
                )

    def calculate_axises_tick(self, time_data, channels, window_size):
        """
        origin = 10
        cursor = 17.2
        last_origin = 7.299999999999999
        time_axis_ticks = [10, 11, 12, 13, 14, 15, 16, 17, 8, 9]
        ||
        \/
        time_axis_ticks = [(0, 10), (1, 11), ... , (9, 9)]

        channels = [1, 5, 7 ,9]
        channel_axis_ticks = [(40, 'Channel 1'), (30, 'Channel 5'), ... ]
        """
        if self.mode == "Scan":
            origin = self.param['origin']
            cursor = self.param['cursor']
            last_origin = self.param['last_origin']

            origin_idx = self.param['idx']['origin']
            cursor_idx = self.param['idx']['cursor']
            last_origin_idx = self.param['idx']['last_origin']

            time_axis_ticks = list(range(int(origin), int(cursor)+1)) \
                                + list(range(int(last_origin+1), int(origin)))
            for idx, tick in enumerate(time_axis_ticks):
                time_axis_ticks[idx] = (tick % window_size, tick)

        elif self.mode == "Scroll":
            origin = self.param['origin']
            cursor = self.param['cursor']

            origin_idx = self.param['idx']['origin']
            cursor_idx = self.param['idx']['cursor']

            time_axis_ticks = list(range(int(origin), int(cursor)+1))
            for idx, tick in enumerate(time_axis_ticks):
                time_axis_ticks[idx] = (tick - origin, tick)

        channel_axis_ticks = list()
        for idx, ch in enumerate(reversed(channels), start=1):
            #TODO change 10 to window height
            channel_axis_ticks.insert(0, (idx*10, "Channel {}".format(ch)))

        return dict(bottom=time_axis_ticks,left=channel_axis_ticks)

    def calculate_plot_data(self, time_data, channel_data, channels):
        """
        origin = 10
        cursor = 17.2
        last_origin = 7.299999999999999

        target_time_data = [10.1, 10.3, ... , 17.0, 17.2, 7.4, 7.5, ... , 9.5]
        ||
        \/
        target_time_data = [0.1 ,  0.3, ... ,  7.0,  7.2, 7.4, 7.5, ... , 9.5]

        target_channel_data =
        [
            [0.1, 0.3, ... , 0.7],
            [0.2, 0.6, ... , 0.8],
        ]
        ||
        \/
        target_channel_data =
        [
            [20.1, 20.3, ... , 20.7],
            [10.2, 10.6, ... , 10.8],
        ]
        """
        if self.mode == "Scan":
            origin_idx = self.param['idx']['origin']
            cursor_idx = self.param['idx']['cursor']
            last_origin_idx = self.param['idx']['last_origin']

            target_time_data = time_data[origin_idx:cursor_idx] \
                                + time_data[last_origin_idx:origin_idx]
            #TODO change 10 to window height
            target_time_data = [t % 10 for t in target_time_data]

            shifted_channel_data = list()
            for shifted, ch in enumerate(reversed(channels), start=1):
                channel_d = channel_data[ch-1][origin_idx:cursor_idx] \
                            + channel_data[ch-1][last_origin_idx:origin_idx]
                shifted_channel_data.insert(0,[x+ shifted*10 \
                                            for x in channel_d])

            self.time_data = target_time_data
            self.channel_data = shifted_channel_data

            self.trans_events[:] = [event for event in self.trans_events if (event['time'] >= self.param['last_origin'] and event['time'] <= self.param['cursor'])]

            for idx in range(len(self.trans_events)):
                tmp_time = self.trans_events[idx]['time']
                if tmp_time >= self.param['origin']:
                    self.trans_events[idx]['time'] -= self.param['origin']
                elif tmp_time < self.param['origin']:
                    self.trans_events[idx]['time'] += 10
                    self.trans_events[idx]['time'] -= self.param['origin']
    
        elif self.mode == "Scroll":
            origin = self.param['origin']

            origin_idx = self.param['idx']['origin']
            cursor_idx = self.param['idx']['cursor']

            target_time_data = time_data[origin_idx:cursor_idx+1]
            target_time_data = [t - origin for t in target_time_data]

            shifted_channel_data = list()
            for shifted, ch in enumerate(reversed(channels), start=1):
                channel_d = channel_data[ch-1][origin_idx:cursor_idx+1]
                shifted_channel_data.insert(0,[x+shifted*10 \
                                            for x in channel_d])

            self.time_data = target_time_data
            self.channel_data = shifted_channel_data

            self.trans_events[:] = [event for event in self.trans_events if (event['time'] >= self.param['origin'] and event['time'] <= self.param['cursor'])]
            for event in self.trans_events:
                event['time'] -= self.param['origin']          

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
                'tick': data['tick'],
                'time': time,
                'name': data['data']['event']['name'],
                'duration': data['data']['event']['duration']        
            })

    def get_plot_raw_data(self, mode="Scan", channels=None, cursor=None):
        """
        Return the raw data used to draw ``mode`` mode raw data plot
        The return value follow the order of channels.

        Scan mode x axis:
        origin, origin+1, ... , cursor, last_origin , ... , origin-2, origin-1
        20.1  , 20.2    , ... , 27.2  , 17.5        , ... , 19.95    , 19.98
        ||
        \/
        0.1   , 0.2     , ... , 7.2   , 8.5         , ... , 9.95     , 9.98

        Scroll mode x axis:
        origin, ......... , cursor
        3.5   , 3.6 , ... , 13.5
        ||
        \/
        0     , 0.1 , ... , 10.0

        The ``channels`` is the index of channels,
        if ``channels`` is None, return all channels.
        Return:
        Instance of the ``Raw_Data_Plot_Data`` class
        """
        if cursor is None:
            raise AssertionError("Scan mode should provide `cursor`")

        if channels is None:
            channels = range(1, self.channel_num+1)

        data = Raw_Data_Plot_Data(self.raw_data_time, self.transed_raw_data, self.events,
                                    mode=mode, channels=channels,
                                    cursor=cursor)

        return data

    def clean_oudated_data(self, cursor):
        outdated_time = cursor - 11
        while self.raw_data_time[0] < outdated_time:
            self.raw_data_time.pop(0)
            for i in range(self.channel_num):
                self.raw_data[i].pop(0)
                self.transed_raw_data[i].pop(0)
        while len(self.events) != 0 and self.events[0]['tick'] / self.raw_plot_sample_rate < outdated_time:
            self.events.pop(0)

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

    def update_scale_line_rela_val(self, new_scale_line_rela_val):
        self.scale_line_rela_val = new_scale_line_rela_val
        for idx_ch in range(len(self.raw_data)):
            for idx_data in range(len(self.raw_data[idx_ch])):
                self.transed_raw_data[idx_ch][idx_data] = self._tranform_data(self.raw_data[idx_ch][idx_data])
                             
    def get_scale_line_rela_val(self):
        return self.scale_line_rela_val

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
        self.scale_adjust_btn = QtGui.QPushButton("Adjust Scales")
        self.event_table_btn = QtGui.QPushButton("Show Events")
        raw_plot_widget = QtGui.QWidget()
        plot_layout = QtGui.QHBoxLayout()
        plot_layout.setSpacing(0)
        self.plot = pg.PlotWidget()
        self.plot.setMouseEnabled(x= False, y= False)
        self.plot.setLimits(xMin=0, maxXRange=10)
        self.plot.enableAutoRange(x=True, y=False)
        self.scroll = QtGui.QScrollBar()
        plot_layout.addWidget(self.plot)
        plot_layout.addWidget(self.scroll)
        raw_plot_widget.setLayout(plot_layout)
        self.addWidget(self.mode_btn, 0, 0, 1, 1)
        self.addWidget(self.dtypeCombo, 0, 1, 1, 1)
        self.addWidget(self.ch_select_btn, 1, 0, 1, 1)
        self.addWidget(self.scale_adjust_btn, 1, 1, 1, 1)
        self.addWidget(self.event_table_btn, 1, 2, 1, 1)
        self.addWidget(raw_plot_widget, 2, 0, 4, 4)
        self.resized.connect(self.update_curves_size)

        self.cursor = pg.InfiniteLine(pos=0)
        self.plot.addItem(self.cursor)

        self.tmp_ref_lines = list()
        for i in range(11):
            ref_line = pg.InfiniteLine(pos=i, pen=pg.mkPen(color=(192, 192, 192), style=QtCore.Qt.DotLine))
            self.tmp_ref_lines.append(ref_line)
            self.plot.addItem(ref_line)

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
            self.plot.addItem(zero_line)
            self.plot.addItem(neg_line)
            self.plot.addItem(pos_line)
            
        self.curves = list()

        for i in range(64):
            r = (i + 60 ) * 5 % 256
            g = (i + 2 ) * 7 % 256
            b = (i + 15 ) * 11 % 256
            curve = self.plot.plot(pen=(r,g,b))
            self.curves.append(curve)
        self.update_curves_size()
        
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.timer_interval*1000)
        self.timer.timeout.connect(self.update_raw_plot)
        self.timer.start()
        self.mode_btn.clicked.connect(self.raw_data_mode_handler)
        self.ch_select_btn.clicked.connect(self.show_channel_select_window)
        self.scale_adjust_btn.clicked.connect(self.show_scale_adjust_window)
        self.event_table_btn.clicked.connect(self.show_event_table_window)
        self.scroll.valueChanged.connect(self.update_curves_size)

        self.event_lines = list()
        for i in range(20):
            event_line = pg.InfiniteLine(pos=0)
            self.event_lines.append(event_line)
            self.plot.addItem(event_line)
            event_line.hide()
        
        self.eventTable = QtGui.QTableWidget()
        self.eventTable.setColumnCount(3)
        self.eventTable.setHorizontalHeaderLabels(['Time', 'Name', 'Duration'])

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

        if self.cursor_time is None:
            #TODO determine the start cursor_time
            self.cursor_time = self.ws_data.raw_data_time[-1]
        elif self.ws_data.raw_data_time[-1] - self.cursor_time > self.timer_interval:
            self.cursor_time += self.timer_interval
        else:
            self.cursor_time = self.ws_data.raw_data_time[-1]
        tol_start = time.time()
        plot_data = self.ws_data.get_plot_raw_data(mode=self.raw_data_mode,
                            channels=self.selected_channels,
                            cursor=self.cursor_time)
        
        for i in range(len(self.event_lines)):
            self.event_lines[i].hide()

        axis = self.plot.getAxis("bottom")
        axis.setTicks([plot_data.axises_tick["bottom"]])
        axis = self.plot.getAxis("left")
        axis.setTicks([plot_data.axises_tick["left"]])

        for idx, (val, label) in enumerate(plot_data.axises_tick["bottom"]):
            self.tmp_ref_lines[idx].setValue(val)
        for i in range(64):
            if i < len(self.selected_channels):
                self.curves[i].show()
                self.zero_base_lines[i].show()
                self.neg_base_lines[i].show()
                self.pos_base_lines[i].show()
            else:
                self.curves[i].hide()
                self.zero_base_lines[i].hide()
                self.neg_base_lines[i].hide()
                self.pos_base_lines[i].hide()
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

        self.slider = ScaleUI.Slider(self.ws_data.get_scale_line_rela_val(), 0, 5)

        scale_adjust_button_box = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal,self.scale_adjust_win)
        scale_adjust_button_box.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
        scale_adjust_button_box.addButton("Apply", QtGui.QDialogButtonBox.AcceptRole)
        scale_adjust_button_box.accepted.connect(self.scale_adjust_handler)
        scale_adjust_button_box.rejected.connect(self.scale_adjust_win.close)

        gridlayout.addWidget(self.slider,0,0)
        gridlayout.addWidget(scale_adjust_button_box,1,0)

        self.scale_adjust_win.show()
    
    def scale_adjust_handler(self):
        self.ws_data.update_scale_line_rela_val(self.slider.get_value())
        self.scale_adjust_win.close()

    def show_channel_select_window(self):
        self.channel_selector_win = QtGui.QDialog(self)
        self.channel_selector_win.setWindowTitle("Select Channels")
        self.channel_selector_win.resize(500,400)
        gridlayout = QtGui.QGridLayout(self.channel_selector_win)

        self.channel_selector = QtGui.QListWidget()
        self.channel_selector.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        for i in range(1, 65):
            item = QtGui.QListWidgetItem(self.channel_selector)
            item.setText("Channel {}".format(i))
            item.setData(QtCore.Qt.UserRole, i)
            if i in self.selected_channels:
                item.setSelected(True)

        channel_selector_button_box = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal,self.channel_selector_win)
        channel_selector_button_box.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
        channel_selector_button_box.addButton("Apply", QtGui.QDialogButtonBox.AcceptRole)
        deselect_all_btn = channel_selector_button_box.addButton("Deselect All", QtGui.QDialogButtonBox.ResetRole)
        select_all_btn = channel_selector_button_box.addButton("Select All", QtGui.QDialogButtonBox.ActionRole)
        channel_selector_button_box.accepted.connect(self.channel_select_handler)
        channel_selector_button_box.rejected.connect(self.channel_selector_win.close)
        deselect_all_btn.clicked.connect(self.select_none_channels)
        select_all_btn.clicked.connect(self.select_all_channels)

        gridlayout.addWidget(self.channel_selector,0,0)
        gridlayout.addWidget(channel_selector_button_box,1,0)
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