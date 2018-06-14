#!/usr/bin/python3
import time

import pyqtgraph as pg
from pyqtgraph.dockarea import *
from PyQt5 import QtCore, QtGui, QtWidgets

from ws_data import WS_Data
from scale_line import Plot_Scale_Line
from dialogs import ChannelSelector, EventTable, ScaleHandler

class Raw_Data_Plot(QtGui.QWidget):
    resized = QtCore.pyqtSignal()
    def __init__(self, url=None):
        """
        Initialize the UI and create ``WS_Data`` to connect to web socket
        url: The url for web socket to connect with
        """
        super().__init__()

        if url is None:
            ws_url = "ws://localhost:7777"
        else:
            ws_url = url

        self.setWindowTitle("Decimated Data Plot")
        self.ws_data = WS_Data(url=ws_url)
        self.timer_interval = 0.1
        self.curve_size = 27 # 1080 / 2 / 20
        self.selected_channels = list(range(1, 65))
        self.raw_data_mode = "Scan"
        self.last_cursor = 0
        self.channel_selector_win = None
        self.event_table_win = None
        self.scale_adjust_win = None
        self.init_ui()
        self.setup_signal_handler()
        self.show()

    def init_ui(self):
        gridlayout = QtGui.QGridLayout(self)
        self.mode_btn = QtGui.QPushButton("Change to Scroll Mode")
        self.ch_select_btn = QtGui.QPushButton("Select Channels")
        self.scale_adjust_btn = QtGui.QPushButton("Adjust Scales")
        self.event_table_btn = QtGui.QPushButton("Show Events")

        self.plot = pg.PlotWidget()
        self.plot.setMenuEnabled(enableMenu=False)
        self.plot.setMouseEnabled(x= False, y= False)
        self.plot.setLimits(xMin=0, maxXRange=10)
        self.plot.enableAutoRange(x=True, y=False)
        self.scroll = QtGui.QScrollBar()

        raw_plot_widget = QtGui.QWidget()
        plot_layout = QtGui.QHBoxLayout(raw_plot_widget)
        plot_layout.setSpacing(0)
        plot_layout.addWidget(self.plot)
        plot_layout.addWidget(self.scroll)

        gridlayout.addWidget(self.mode_btn, 0, 0, 1, 1)
        gridlayout.addWidget(self.ch_select_btn, 0, 1, 1, 1)
        gridlayout.addWidget(self.scale_adjust_btn, 0, 2, 1, 1)
        gridlayout.addWidget(self.event_table_btn, 0, 3, 1, 1)
        gridlayout.addWidget(raw_plot_widget, 1, 0, 4, 4)

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

    def setup_signal_handler(self):
        self.resized.connect(self.update_curves_size)
        self.mode_btn.clicked.connect(self.raw_data_mode_handler)
        self.ch_select_btn.clicked.connect(self.show_channel_select_window)
        self.scale_adjust_btn.clicked.connect(self.show_scale_adjust_window)
        self.event_table_btn.clicked.connect(self.show_event_table_window)
        self.scroll.valueChanged.connect(self.update_curves_size)

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

        cursor_time = self.ws_data.cursor
        if cursor_time is None:
            self.ws_data.cursor = 0
            return

        # init plot origin
        if self.ws_data.plot_origin is None:
            self.ws_data.plot_origin = cursor_time

        if cursor_time <= self.last_cursor:
            return

        tol_start = time.time()
        plot_data = self.ws_data.get_plot_decimated_data(mode=self.raw_data_mode,
                            channels=self.selected_channels)
        
        for i in range(len(self.event_lines)):
            self.event_lines[i].hide()

        axis = self.plot.getAxis("bottom")
        axis.setTicks([plot_data.axises_tick["bottom"]])
        axis.setLabel("Time (sec)")
        axis = self.plot.getAxis("left")
        axis.setTicks([plot_data.axises_tick["left"]])
        axis.setLabel("Voltage (uV)")

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
        self.cursor.setValue(plot_data.cursor)
        self.ws_data.clean_oudated_data(cursor_time)

        if self.event_table_win:
            self.event_table_win.update_event_table()
        self.last_cursor = cursor_time

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
        if self.scale_adjust_win is None:
            self.scale_adjust_win = ScaleHandler(self)

    def show_channel_select_window(self):
        if self.channel_selector_win is None:
            self.channel_selector_win = ChannelSelector(self)

    def show_event_table_window(self):
        if self.event_table_win is None:
            self.event_table_win = EventTable(self)

    def resizeEvent(self, event):
        self.resized.emit()
        return super().resizeEvent(event)

    def wheelEvent(self, event):
        scroll_change = -(event.angleDelta().y() // 120)
        scroll_val = self.scroll.value()
        self.scroll.setValue(scroll_val + scroll_change)

if __name__ == "__main__":
    app = QtGui.QApplication([])
    plot = Raw_Data_Plot()
    app.exec_()