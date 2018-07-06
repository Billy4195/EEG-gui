#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from ws_fft import WS_FFT
from dialogs import ChannelSelector


class Spectrum_Plot(QtGui.QWidget):
    resized = QtCore.pyqtSignal()
    def __init__(self, url=None):
        super().__init__()

        if url is None:
            url = "ws://localhost:7777"

        #TODO setup ws2
        self.ws_data = WS_FFT(url=url, plot_name="FFT_PS")

        self.setWindowTitle("Power Spectrum(FFT)")
        self.timer_interval = 0.5
        self.v_scale = 600
        self.h_min = 0
        self.h_max = 30
        self.sub_plot_size = 150
        self.selected_channels = list(range(1, 9))
        self.channel_selector_win = None

        self.init_ui()
        self.setup_signal_handler()
        self.show()

    def init_ui(self):
        self.menu_bar = Menu_bar(self)
        self.plot = Spectrum(self)
        self.scroll = QtGui.QScrollBar()
        scroll_range = self.ws_data.channel_num - 4
        self.scroll.setMaximum(scroll_range)
        grid_layout = QtGui.QGridLayout(self)
        grid_layout.setMenuBar(self.menu_bar)
        grid_layout.addWidget(self.plot, 0, 0, 15, 4)
        grid_layout.addWidget(self.scroll, 0, 4, 15, 1)
        self.update_display_plot_num()

    def setup_signal_handler(self):
        self.scroll.valueChanged.connect(self.update_display_plot_num)
        self.resized.connect(self.update_display_plot_num)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.timer_interval*1000)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def update_plot(self):
        # get data from websocket
        if self.ws_data.FFT_data:
            self.plot.draw(self.ws_data.FFT_data.pop(0), self.ws_data.freq_label)
        else:
            pass

    def resizeEvent(self, event):
        self.resized.emit()
        return super().resizeEvent(event)

    def wheelEvent(self, event):
        scroll_change = -(event.angleDelta().y() // 120)
        scroll_val = self.scroll.value()
        self.scroll.setValue(scroll_val + scroll_change)

    def update_selected_channels(self, channels):
        self.selected_channels = channels

    def update_display_plot_num(self):
        cur_idx = self.scroll.value()
        plot_widget_height = self.plot.frameGeometry().height()
        max_num_plot_in_widget = plot_widget_height // self.sub_plot_size
        if max_num_plot_in_widget > len(self.selected_channels):
            display_plot_count = len(self.selected_channels)
        else:
            display_plot_count = max_num_plot_in_widget

        scroll_max = len(self.selected_channels) - max_num_plot_in_widget
        if scroll_max < 0:
            scroll_max = 0

        if scroll_max != self.scroll.maximum():
            self.scroll.setMaximum(scroll_max)

        for i in range(self.ws_data.channel_num):
            self.plot.plots[i].hide()
            self.plot.ch_labels[i].hide()

        for idx, i in enumerate(self.selected_channels):
            i -= 1
            if idx in range(cur_idx, cur_idx+max_num_plot_in_widget):
                self.plot.plots[i].show()
                self.plot.ch_labels[i].show()
                self.plot.plots[i].setMaximumHeight((plot_widget_height-50) // display_plot_count)
            else:
                self.plot.ch_labels[i].hide()
                self.plot.plots[i].hide()


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
        self.min_spin.setMinimum(0)
        self.min_spin.setValue(self.parent.h_min)
        self.h_max_label = QtWidgets.QLabel("Max Frequency")
        self.max_spin = QtGui.QSpinBox()
        self.max_spin.setMaximum(20000)
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
        if self.parent.channel_selector_win is None:
            self.parent.channel_selector_win = ChannelSelector(self.parent)

    def update_scales(self):
        self.parent.v_scale = int(self.v_scale_selector.text())
        self.parent.h_min = self.min_spin.value()
        self.parent.h_max = self.max_spin.value()
        self.parent.update_plot()

class Spectrum(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.bars = list()
        self.init_ui()
        self.show()

    def init_ui(self):
        grid_layout = QtGui.QGridLayout(self)
        self.plots = list()
        self.ch_labels = list()
        while(self.parent.ws_data.ch_label is None): True
        for i in range(8):
            self.plots.append(pg.PlotWidget())
            self.plots[i].setMenuEnabled(enableMenu=False)
            self.plots[i].setMouseEnabled(x= False, y= False)
            ch_name = self.parent.ws_data.ch_label[i]
            self.ch_labels.append(QtGui.QLabel(ch_name))
            grid_layout.addWidget(self.ch_labels[-1], i , 0, 1, 1)
            grid_layout.addWidget(self.plots[-1], i, 1, 1, 20)

    def draw(self, data, ticks):
        ticks_labels = [[(v, str(v)) for v in ticks]]
        for i in range(8):
            self.plots[i].setYRange(0, self.parent.v_scale)
            self.plots[i].setXRange(self.parent.h_min, self.parent.h_max)
            bottom_ticks = self.plots[i].getAxis("bottom")
            bottom_ticks.setTicks(ticks_labels)
            while len(self.bars) <= i:
                self.bars.append(None)
            if self.bars[i] is None:
                self.bars[i] = pg.BarGraphItem(x=ticks, height=data[i], width=ticks[1]-ticks[0])
                self.plots[i].addItem(self.bars[i])
            else:
                self.bars[i].opts['height'] = data[i]
                self.bars[i].drawPicture()

        self.parent.update_display_plot_num()

if __name__ == "__main__":
    app = QtGui.QApplication([])
    plot = Spectrum_Plot()
    app.exec_()