# -*- coding: utf-8 -*-
import sys

import pyqtgraph as pg
from PyQt5 import QtCore
import time

class TimeThread(QtCore.QThread):
    signal_time = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.working = True

    def start_timer(self):
        self.start_time = time.time()
        self.start()

    def run(self):
        while self.working:
            self.signal_time.emit(str(time.time()-self.start_time))
            self.sleep(0.01)
    
    def stop(self):
        self.working = False