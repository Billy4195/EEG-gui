#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import time

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colorbar import ColorbarBase
from mne.viz import topomap

from channel_loca_dict import channel_dict_2D
from ws_pb import WS_PB
import time
from dialogs import Big_Bar_Plot


class Bar_Plot(QtGui.QWidget):
    def __init__(self,url=None):
        super().__init__()

        if url is None:
            url = "ws://localhost:7777"
        
        self.ws_data = WS_PB(url=url, plot_name="PB_bar")
        self.setWindowTitle("Bar Plot")
        self.timer_interval = 0.5

        while self.ws_data.ch_label is None:
            pass

        self.num_color = 8
        self.big_plots = [None] * len(self.ws_data.ch_label)

        self.init_ui()
        self.setup_signal_handler()
        self.show()
        self.value = 0

    def init_ui(self):
        self.cmap = mpl.cm.get_cmap('Dark2')
        self.norm = mpl.colors.Normalize(vmin=0, vmax=8)
        self.fig, (self.axes) = plt.subplots(len(self.ws_data.ch_label)+2, 1)

        self.colorbar = ColorbarBase(self.axes[-1], cmap=self.cmap, norm=self.norm, ticks=[i+0.5 for i in range(8)])
        self.colorbar.set_ticklabels(['Delta (1-3 Hz)',
                                        'Theta (4-7 Hz)',
                                        'Low Alpha (8-10 Hz)',
                                        'High Alpha (11-12 Hz)',
                                        'Low Beta (13-15 Hz)',
                                        'Mid Beta (16-19 Hz)',
                                        'High Beta (20-35 Hz)',
                                        'Gamma (36-50 Hz)'])

        self.canvas = FigureCanvas(self.fig)

        self.pos = list(channel_dict_2D.values())                        # get all X,Y values
        self.ch_names_ = list(channel_dict_2D.keys())                    # get all channel's names
        

        self.pos, self.outlines = topomap._check_outlines(self.pos, 'head')        # from mne.viz libs, normalize the pos

        topomap._draw_outlines(self.axes[0], self.outlines)
        self.plt_idx = [self.ch_names_.index(name) for name in self.ws_data.ch_label]      # get the index of those required channels 
        ch_pos = [self.pos[idx]*5/6 for idx in self.plt_idx]
        for idx, pos in enumerate(ch_pos):
            pos += [0.47, 0.47]
            self.axes[idx+1].set_position(list(pos) + [0.06, 0.06])
            self.axes[idx+1].axis("off")
            self.axes[idx+1].grid(True, axis='y')

        self.axes[0].set_position([0, 0, 1, 1])
        self.axes[-1].set_position([0.80, 0.85, 0.03, 0.13])
        self.resize(1000, 800)

        hlayout = QtGui.QHBoxLayout(self)
        hlayout.addWidget(self.canvas)
    
    def setup_signal_handler(self):
        cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.timer_interval*1000)
        self.timer.timeout.connect(self.draw)
        self.timer.start()

    def onclick(self, event):
        for idx, ax in enumerate(self.axes[1:]):
            if ax == event.inaxes:
                print(self.ws_data.ch_label[idx])
                if self.big_plots[idx] == None:
                    self.big_plots[idx] = Big_Bar_Plot(self, self.ws_data.ch_label[idx])

    def big_plot_closed(self, plot):
        for idx, p in enumerate(self.big_plots):
            if plot == p:
                self.big_plots[idx] = None

    def draw(self):
        if self.ws_data.power_data:
            ch_data = self.ws_data.power_data.pop()
            for idx, data in enumerate(ch_data):
                color = [self.cmap(self.norm(i)) for i in range(8)]
                self.axes[idx+1].cla()
                self.axes[idx+1].bar(list(range(8)), data, color=color)
                self.axes[idx+1].spines["bottom"].set_visible(False)
                self.axes[idx+1].spines["top"].set_visible(False)
                self.axes[idx+1].spines["right"].set_visible(False)
                self.axes[idx+1].spines["left"].set_visible(False)
                self.axes[idx+1].yaxis.grid(True, c='r')
                self.axes[idx+1].get_xaxis().set_visible(False)
                if self.big_plots[idx] != None:
                    self.big_plots[idx].draw(data, color)
            self.fig.canvas.draw()

if __name__ == "__main__":
    app = QtGui.QApplication([])
    plot = Bar_Plot()
    app.exec_()