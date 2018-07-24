import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui
import matplotlib.pyplot as plt
import matplotlib as mpl
import mne
from mne.viz import topomap
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colorbar import ColorbarBase

from channel_loca_dict import channel_dict_2D

class TopographicWidget(QtGui.QWidget):
    def __init__(self, ch_label, parent):
        super().__init__()

        self.parent = parent
        self.fig, self.axes = plt.subplots(2, 4)
        self.colorbar_ax = self.fig.add_subplot(2, 5, 5)
        self.cmap = 'RdBu_r'
        self.norm = mpl.colors.Normalize(vmin=0, vmax=100)
        self.colorbar_ax.set_position([0.9, 0.04, 0.03, 0.15])
        self.colorbar = ColorbarBase(self.colorbar_ax, cmap=self.cmap, norm=self.norm)
        self.canvas = FigureCanvas(self.fig)

        self.titles = ['Delta',
                        'Theta',
                        'Low Alpha',
                        'High Alpha',
                        'Low Beta',
                        'Mid Beta',
                        'High Beta',
                        'Gamma']

        hlayout = QtGui.QHBoxLayout(self)
        hlayout.addWidget(self.canvas)
        self.show()

    def draw(self, data, ch_label):
        self.pos = np.array(list(channel_dict_2D.values()))
        self.ch_names_ = list(channel_dict_2D.keys())

        self.pos, self.outlines = topomap._check_outlines(self.pos, 'head')
        center = 0.5 * (self.pos.max(axis=0) + self.pos.min(axis=0))
        scale = 1.0 / (self.pos.max(axis=0) - self.pos.min(axis=0))
        scale[0] = scale[0] * 1.3
        self.plt_idx = [self.ch_names_.index(name) for name in ch_label]
        ch_pos = np.array([self.pos[idx]*5/6 for idx in self.plt_idx])
        mask = np.ones((len(ch_pos), 1), dtype=bool)

        for idx in range(8):
            x_idx = idx // 4
            y_idx = idx % 4
            self.axes[x_idx][y_idx].cla()
            self.axes[x_idx][y_idx].set_title(self.titles[idx])
            if self.parent.ch_loc:
                marker = "."
            else:
                marker = ""

            mne.viz.plot_topomap(data[idx], ch_pos, axes=self.axes[x_idx][y_idx], contours=10,
                                show=False, mask=mask, mask_params=dict(marker=marker),
                                head_pos=dict(center=center, scale=scale*1.1), cmap="RdBu_r",
                                names=ch_label, show_names=self.parent.ch_loc)
        self.colorbar_ax.set_position([0.9, 0.04, 0.03, 0.15])
        self.fig.canvas.draw()

    def update_color_bar(self, scale_min, scale_max):
        norm = mpl.colors.Normalize(vmin=scale_min, vmax=scale_max)
        self.colorbar.norm = norm
        self.colorbar.draw_all()

class Menu_Bar(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent
        self.scale_min = 0
        self.scale_max = 100

        self.init_ui()
        self.setup_signal_handler()
        self.power_handler()

    def init_ui(self):
        grid_layout = QtGui.QGridLayout(self)

        self.z_each_btn = QtGui.QPushButton("Z-Score to each band")
        self.z_all_btn = QtGui.QPushButton("Z-Score to all bands")
        self.power_btn = QtGui.QPushButton("Power")
        self.ch_loc_btn = QtGui.QPushButton("Channel Location")

        scale_group_box = QtGui.QGroupBox()
        scale_layout = QtGui.QHBoxLayout(scale_group_box)
        self.spin_min = QtGui.QSpinBox()
        self.spin_min.setValue(0)
        self.spin_max = QtGui.QSpinBox()
        self.spin_max.setMaximum(10000)
        self.spin_max.setValue(100)
        scale_layout.addWidget(QtGui.QLabel("Scale: "))
        scale_layout.addWidget(self.spin_min)
        scale_layout.addWidget(QtGui.QLabel(" to "))
        scale_layout.addWidget(self.spin_max)
        scale_layout.addWidget(QtGui.QLabel("uV<sup>2</sup>"))

        grid_layout.addWidget(self.z_each_btn, 0, 0, 1, 1)
        grid_layout.addWidget(self.z_all_btn, 0 , 1, 1, 1)
        grid_layout.addWidget(self.power_btn, 0, 2, 1, 1)
        grid_layout.addWidget(scale_group_box, 0, 3, 1, 1)
        grid_layout.addWidget(self.ch_loc_btn, 0, 4, 1, 1)

    def setup_signal_handler(self):
        self.ch_loc_btn.clicked.connect(self.ch_loc_handler)
        self.z_each_btn.clicked.connect(self.z_each_handler)
        self.z_all_btn.clicked.connect(self.z_all_handler)
        self.power_btn.clicked.connect(self.power_handler)
        self.spin_min.valueChanged.connect(self.scale_change_handler)
        self.spin_max.valueChanged.connect(self.scale_change_handler)

    def ch_loc_handler(self):
        self.parent.ch_loc = not self.parent.ch_loc
        
    def z_each_handler(self):
        self.parent.display_type = "z_each"
        self.z_each_btn.setEnabled(False)
        self.z_all_btn.setEnabled(True)
        self.power_btn.setEnabled(True)
        self.spin_min.setMinimum(-5)
        self.spin_min.setValue(-2)
        self.spin_min.setEnabled(False)
        self.spin_max.setValue(2)
        self.spin_max.setEnabled(False)

    def z_all_handler(self):
        self.parent.display_type = "z_all"
        self.z_each_btn.setEnabled(True)
        self.z_all_btn.setEnabled(False)
        self.power_btn.setEnabled(True)
        self.spin_min.setMinimum(-5)
        self.spin_min.setValue(-2)
        self.spin_min.setEnabled(False)
        self.spin_max.setValue(2)
        self.spin_max.setEnabled(False)

    def power_handler(self):
        self.parent.display_type = "power"
        self.z_each_btn.setEnabled(True)
        self.z_all_btn.setEnabled(True)
        self.power_btn.setEnabled(False)
        self.spin_min.setMinimum(0)
        self.spin_min.setValue(0)
        self.spin_min.setEnabled(True)
        self.spin_max.setValue(100)
        self.spin_max.setEnabled(True)

    def scale_change_handler(self):
        self.scale_min = self.spin_min.value()
        self.scale_max = self.spin_max.value()
        self.parent.topo_widget.update_color_bar(self.scale_min, self.scale_max)
