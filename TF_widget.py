import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
from matplotlib.colorbar import ColorbarBase

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class SpectrogramWidget(QtGui.QWidget):
    def __init__(self, freq_limit, time_scale, freq_labels):
        super().__init__()

        gs_kw = dict(width_ratios=[30,1], height_ratios=[1])
        self.fig, (self.ax, self.ax2) = plt.subplots(1, 2, gridspec_kw=gs_kw)

        self.canvas = FigureCanvas(self.fig)

        self.cm = plt.cm.get_cmap('Spectral_r')
        self.norm = mpl.colors.Normalize(vmin=-200, vmax=1000)
        self.colorbar = ColorbarBase(self.ax2, cmap=self.cm, norm=self.norm, ticks=[-200, -100, 0, 100, 200, 400, 600, 800, 1000])
        self.img_array = None
        self.tick_array = None
        self.init_tick = None
        self.min_freq, self.max_freq = freq_limit
        self.time_scale = time_scale
        self.freq_labels = freq_labels

        hlayout = QtGui.QHBoxLayout(self)
        hlayout.addWidget(self.canvas)
        self.show()

    def draw(self, new_tick_data, tick, show):
        tick /= 1000
        tick = int(tick)
        
        if self.img_array is None:
            self.img_array = np.array([new_tick_data]).T
            self.tick_array = [tick]
            self.init_tick = tick
        while self.tick_array[0] <= self.tick_array[-1] - self.time_scale :
            self.img_array = self.img_array[:, 1:]
            self.tick_array.pop(0)

        self.img_array = np.append(self.img_array, np.array([new_tick_data]).T, axis=1)
        self.tick_array.append(tick)
        if show:
            self.update()

    def update(self):
        self.ax.cla()
        if self.tick_array[0] + self.time_scale - self.tick_array[-1]:
            zeros = np.zeros((len(self.img_array),
                                self.tick_array[0] + self.time_scale - self.tick_array[-1] ))
            img = np.append(self.img_array, zeros, axis=1)
        else:
            img = self.img_array

        self.ax.imshow(img, cmap="Spectral_r", norm=self.norm)
        self.ax.invert_yaxis()
        ticks = self.ax.get_xticks()
        labels = [str(self.init_tick + tick) for tick in ticks]
        self.ax.set_xticklabels(labels)
        for idx, label in enumerate(self.freq_labels):
            if label <= self.min_freq:
                min_limit = idx

            if label >= self.max_freq:
                max_limit = idx
                break

        self.ax.set_ylim(min_limit, max_limit)
        y_ticks = self.ax.get_yticks()
        y_labels = [self.freq_labels[int(i)] for i in y_ticks]
        self.ax.set_yticklabels(y_labels)
        
        self.ax.set_xmargin(0)
        self.fig.canvas.draw()

    def set_freq_limit(self, freq_limit):
        self.min_freq, self.max_freq = freq_limit
