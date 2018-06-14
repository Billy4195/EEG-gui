__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QWidget
from PyQt5 import QtGui
import pyqtgraph as pg
import numpy as np
import sys

amp_scales = ['2000', '1000', '500', '250', '200', '150', '100', '75', '50', '25', '10']
time_scales = ['5', '10', '15', '20', '25', '30']

class ScaleSelector(QWidget):
    def __init__(self, current, parent=None):
        super().__init__(parent=parent)
        cur_amp, cur_time = current
        self.layout = QtGui.QGridLayout(self)
        self.row1_label1 = QLabel("Amplitude Scale: ", self)
        self.row1_label2 = QLabel("uV  per channel", self)
        self.row2_label1 = QLabel("Time Scale", self)
        self.row2_label2 = QLabel("Second(s)  per page")

        self.amp_scale_com_box = QtGui.QComboBox()
        for scale in amp_scales:
            self.amp_scale_com_box.addItem(scale)
        cur_idx = self.amp_scale_com_box.findText(str(cur_amp))
        self.amp_scale_com_box.setCurrentIndex(cur_idx)

        self.time_scale_com_box = QtGui.QComboBox()
        for scale in time_scales:
            self.time_scale_com_box.addItem(scale)
        cur_idx = self.time_scale_com_box.findText(str(cur_time))
        self.time_scale_com_box.setCurrentIndex(cur_idx)

        self.layout.addWidget(self.row1_label1, 0, 0)
        self.layout.addWidget(self.amp_scale_com_box, 0, 1)
        self.layout.addWidget(self.row1_label2, 0, 2)
        self.layout.addWidget(self.row2_label1, 1, 0)
        self.layout.addWidget(self.time_scale_com_box, 1, 1)
        self.layout.addWidget(self.row2_label2, 1, 2)
        self.resize(self.sizeHint())
    
    def get_value(self):
        return int(self.amp_scale_com_box.currentText()), int(self.time_scale_com_box.currentText())

  