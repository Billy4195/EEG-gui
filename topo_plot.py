#!/usr/bin/python3
# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets

from ws_pb import WS_PB
import time


class Topo_Plot(object):
    def __init__(self,url=None):
        super().__init__()

        if url is None:
            url = "ws://localhost:7777"
        
        self.ws_data = WS_PB(url=url, plot_name="PB_topo")
        while(self.ws_data.ch_label is None): True
        print ('ok!')
        time.sleep(100)

if __name__ == "__main__":
    # app = QtGui.QApplication([])
    plot = Topo_Plot()
    # app.exec_()