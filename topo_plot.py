#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from ws_pb import WS_PB
from topo_widget import TopographicWidget, Menu_Bar


class Topo_Plot(QtGui.QWidget):
    def __init__(self,url=None):
        super().__init__()

        if url is None:
            url = "ws://localhost:7777"
        
        self.ws_data = WS_PB(url=url, plot_name="PB_topo")
        while(self.ws_data.ch_label is None): True
        self.setWindowTitle("Topographic")
        
        self.timer_interval = 0.5
        self.ch_loc = True
        self.display_type = "power"

        self.init_ui()
        self.setup_signal_handler()
        self.show()

    def init_ui(self):
        vbox_layout = QtGui.QVBoxLayout(self)
        self.menu_bar = Menu_Bar(self)
        self.topo_widget = TopographicWidget(self.ws_data.ch_label, self)
        vbox_layout.addWidget(self.topo_widget)
        vbox_layout.setMenuBar(self.menu_bar)
        self.resize(1000, 800)

    def setup_signal_handler(self):
        self.timer = QtCore.QTimer()
        self.timer.setInterval(self.timer_interval*1000)
        self.timer.timeout.connect(self.draw)
        self.timer.start()

    def draw(self):
        if self.ws_data.power_data:
            power_data = self.ws_data.power_data.pop(0)
            if self.display_type == "power":
                self.topo_widget.draw(power_data, self.ws_data.ch_label)

        if self.ws_data.z_all_data:
            z_all = self.ws_data.z_all_data.pop(0)
            if self.display_type == "z_all":
                self.topo_widget.draw(z_all, self.ws_data.ch_label)

        if self.ws_data.z_each_data:
            z_each = self.ws_data.z_each_data.pop(0)
            if self.display_type == "z_each":
                self.topo_widget.draw(z_each, self.ws_data.ch_label)

if __name__ == "__main__":
    app = QtGui.QApplication([])
    plot = Topo_Plot()
    app.exec_()