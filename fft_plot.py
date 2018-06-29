#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from ws_fft import WS_FFT


class Spectrum_Plot(QtGui.QWidget):
    def __init__(self, url=None):
        super().__init__()

        if url is None:
            url = "ws://localhost:7777"

        #TODO setup ws
        self.ws_fft = WS_FFT(FFT_plot=self, url=url)

        self.setWindowTitle("Power Spectrum(FFT)")
        self.timer_interval = 0.5
        self.v_scale = 600
        self.h_min = 0
        self.h_max = 30

        #getting these values from ws_fft
        ######
        self.channel_num = 0
        self.freq_num = 0
        self.freq_range = list()
        self.freq_label = list()
        self.ch_label = list()
        ######

        self.init_ui()
        self.setup_signal_handler()
        self.show()

    def init_ui(self):
        # self.resize(500,400)
        self.menu_bar = Menu_bar(self)
        self.plot = Spectrum(self)
        grid_layout = QtGui.QGridLayout(self)
        grid_layout.setMenuBar(self.menu_bar)
        grid_layout.addWidget(self.plot, 0, 0, 15, 4)

    def setup_signal_handler(self):
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.timer_interval*1000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def update_plot(self):
        # get data from websocket

        #fre_range = self.ws_fft.freq_range
        # import numpy as np
        # data = list()
        # for i in range(8):
        #     data.append(list(np.random.randint(5, 100, 50)))
        if self.ws_fft.FFT_data:
            self.plot.draw(self.ws_fft.FFT_data.pop(0))
        else:
            pass


class Menu_bar(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
        self.setup_signal_handler()
        self.show()

    def init_ui(self):
        self.group_box = QtGui.QGroupBox("Scale Parameters")
        self.v_scale_label = QtWidgets.QLabel("Vertical Scale")
        self.v_scale_selector = QtGui.QSpinBox()
        self.v_scale_selector.setMaximum(20000)
        self.v_scale_selector.setValue(self.parent.v_scale)
        self.h_min_label = QtWidgets.QLabel("Min Frequency")
        self.min_spin = QtGui.QSpinBox()
        self.min_spin.setValue(self.parent.h_min)
        self.h_max_label = QtWidgets.QLabel("Max Frequency")
        self.max_spin = QtGui.QSpinBox()
        self.max_spin.setValue(self.parent.h_max)
        self.ch_select_btn = QtGui.QPushButton("Select Channels")
        self.ch_select_btn.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.apply_btn = QtGui.QPushButton("Apply")
        grid_layout = QtGui.QGridLayout(self)
        group_layout = QtGui.QGridLayout(self.group_box)
        group_layout.addWidget(self.v_scale_label, 0, 0, 1, 1)
        group_layout.addWidget(self.v_scale_selector, 1, 0, 1, 1)
        group_layout.addWidget(self.h_min_label, 0, 1, 1, 1)
        group_layout.addWidget(self.min_spin, 1, 1, 1, 1)
        group_layout.addWidget(self.h_max_label, 0 , 2, 1, 1)
        group_layout.addWidget(self.max_spin, 1, 2, 1, 1)
        group_layout.addWidget(self.apply_btn, 2, 2, 1, 1)
        grid_layout.addWidget(self.group_box, 0, 0, 1, 1)
        grid_layout.addWidget(self.ch_select_btn, 0, 1, 3, 1)

    def setup_signal_handler(self):
        self.ch_select_btn.clicked.connect(self.show_channel_select_window)
        self.apply_btn.clicked.connect(self.update_scales)

    def show_channel_select_window(self):
        pass

    def update_scales(self):
        print("V scale", self.v_scale_selector.text())
        print("min ",self.min_spin.value())
        print("max", self.max_spin.value())

class Spectrum(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.bars = list()
        self.init_ui()
        self.show()

    def init_ui(self):
        vbox_layout = QtGui.QVBoxLayout(self)
        self.plots = list()
        for i in range(8):
            self.plots.append(pg.PlotWidget())
            self.plots[i].setMenuEnabled(enableMenu=False)
            self.plots[i].setMouseEnabled(x= False, y= False)
            vbox_layout.addWidget(self.plots[-1])

    def draw(self, data):
        for i in range(8):
            self.plots[i].setYRange(0, self.parent.v_scale)
            self.plots[i].setXRange(self.parent.h_min, self.parent.h_max)
            while len(self.bars) <= i:
                self.bars.append(None)
            if self.bars[i] is None:
                self.bars[i] = pg.BarGraphItem(x0=list(range(len(data[i]))), height=data[i], width=1)
                self.plots[i].addItem(self.bars[i])
            else:
                self.bars[i].opts['height'] = data[i]
                self.bars[i].drawPicture()

if __name__ == "__main__":
    app = QtGui.QApplication([])
    plot = Spectrum_Plot()
    app.exec_()