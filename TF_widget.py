import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
from matplotlib.colorbar import ColorbarBase

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class SpectrogramWidget(QtGui.QWidget):
    def __init__(self):
        super().__init__()

        gs_kw = dict(width_ratios=[30,1], height_ratios=[1])
        self.fig, (self.ax, self.ax2) = plt.subplots(1, 2, gridspec_kw=gs_kw)

        self.canvas = FigureCanvas(self.fig)

        self.cm = plt.cm.get_cmap('Spectral_r')
        self.norm = mpl.colors.Normalize(vmin=-200, vmax=1000)
        self.colorbar = ColorbarBase(self.ax2, cmap=self.cm, norm=self.norm, ticks=[-200, -100, 0, 100, 200, 400, 600, 800, 1000])
        self.img_array = None
        self.init_tick = None

        hlayout = QtGui.QHBoxLayout(self)
        hlayout.addWidget(self.canvas)
        self.show()

    def draw(self, new_tick_data, tick):
        tick /= 1000
        tick = int(tick)
        
        if self.img_array is None:
            self.img_array = np.array([new_tick_data]).T
            self.init_tick = tick
        elif len(self.img_array[0]) == 500:
            self.img_array = self.img_array[:, 1:]
            self.img_array = np.append(self.img_array, np.array([new_tick_data]).T, axis=1)
        else:
            self.img_array = np.append(self.img_array, np.array([new_tick_data]).T, axis=1)

        self.ax.cla()
        self.ax.imshow(self.img_array, cmap="Spectral_r")

        self.ax.invert_yaxis()
        ticks = self.ax.get_xticks()
        labels = [str(self.init_tick + tick) for tick in ticks]
        self.ax.set_xticklabels(labels)
        
        self.ax.set_xmargin(0)
        self.fig.canvas.draw()
