#!/usr/bin/python3
import time

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colorbar import ColorbarBase
from mne.viz import topomap

from ws_data import WS_Data
from channel_loca_dict import channel_dict_2D

class Contact_Plot(QtGui.QWidget):
    def __init__(self, url=None):
        super().__init__()

        if url is None:
            ws_url = "ws://localhost:7777"
        else:
            ws_url = url

        self.setWindowTitle("Decimated Data Plot")
        # self.ws_data = WS_Data(url=ws_url)
        self.timer_interval = 0.5

        self.ch_label = ['Fp1', 'Fpz', 'Fp2', \
         'AF9', 'AF7', 'AF5', 'AF3', 'AF1', 'AFz', 'AF2', 'AF4', 'AF6', 'AF8', 'AF10', \
         'F9', 'F7', 'F5', 'F3', 'F1', 'Fz', 'F2', 'F4', 'F6', 'F8', 'F10', \
         'FT9', 'FT7', 'FC5', 'FC3', 'FC1', 'FCz', 'FC2', 'FC4', 'FC6', 'FT8', 'FT10', \
         'T9', 'T7', 'C5', 'C3', 'C1', 'Cz', 'C2', 'C4', 'C6', 'T8', 'T10', \
         'TP9', 'TP7', 'CP5', 'CP3', 'CP1', 'CPz', 'CP2', 'CP4', 'CP6', 'TP8', 'TP10', \
         'P9', 'P7', 'P5', 'P3', 'P1', 'Pz', 'P2', 'P4', 'P6', 'P8', 'P10', \
         'PO9', 'PO7', 'PO5', 'PO3', 'PO1', 'POz', 'PO2', 'PO4', 'PO6', 'PO8', 'PO10', \
         'O1', 'Oz', 'O2']

        gs_kw = dict(width_ratios=[30,1], height_ratios=[1])
        self.fig, (self.ax, self.ax2) = plt.subplots(1, 2, gridspec_kw=gs_kw)

        self.canvas = FigureCanvas(self.fig)

        self.pos = list(channel_dict_2D.values())                        # get all X,Y values
        self.ch_names_ = list(channel_dict_2D.keys())                    # get all channel's names

        self.plt_idx = [self.ch_names_.index(name) for name in self.ch_label]      # get the index of those required channels 

        self.pos, self.outlines = topomap._check_outlines(self.pos, 'head')        # from mne.viz libs, normalize the pos

        self.cm = plt.cm.get_cmap('RdYlGn_r')
        self.norm = mpl.colors.Normalize(vmin=0, vmax=2000)
        self.colorbar = ColorbarBase(self.ax2, cmap=self.cm, norm=self.norm, ticks=[0, 500, 1000, 1500, 2000])

        self.ch_table = QtGui.QTableWidget(len(self.ch_label), 2, parent=self)
        self.draw(self.ch_label, [0]*len(self.ch_label))

        hlayout = QtGui.QHBoxLayout(self)
        hlayout.addWidget(self.canvas)
        hlayout.addWidget(self.ch_table)

        self.setup_signal_handler()
        self.show()
        self.value = 0

    def update_plot(self):
        self.value = (self.value + 500) % 2500
        self.ax.cla()
        self.draw(self.ch_label, [self.value]*len(self.ch_label))
        self.fig.canvas.draw()

    def draw(self, ch_label, values):
        self.plt_idx = [self.ch_names_.index(name) for name in self.ch_label]      # get the index of those required channels 

        topomap._draw_outlines(self.ax, self.outlines)                        # from mne.viz libs, draw "head lines" on ax

        self.ax.scatter(self.pos[self.plt_idx,0], self.pos[self.plt_idx,1], c=values, marker='o', alpha=0.7, edgecolors=(0,0,0), cmap=self.cm, norm=self.norm)
        for idx in self.plt_idx:
            if self.pos[idx,0]<0:
                self.ax.text(self.pos[idx,0]-0.005, self.pos[idx,1]-0.04, self.ch_names_[idx], fontsize=10, horizontalalignment='center')
            elif self.pos[idx,0]>0:
                self.ax.text(self.pos[idx,0]+0.005, self.pos[idx,1]-0.04, self.ch_names_[idx], fontsize=10, horizontalalignment='center')
            else:
                self.ax.text(self.pos[idx,0]+0, self.pos[idx,1]-0.04, self.ch_names_[idx], fontsize=10, horizontalalignment='center')

        for idx, (ch_name, value) in enumerate(zip(self.ch_label, values)):
            item = QtGui.QTableWidgetItem(ch_name)
            self.ch_table.setItem(idx, 0, item)
            item = QtGui.QTableWidgetItem(str(value))
            self.ch_table.setItem(idx, 1, item)

    def setup_signal_handler(self):
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.timer_interval*1000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()


if __name__ == "__main__":
    app = QtGui.QApplication([])
    plot = Contact_Plot()
    app.exec_()