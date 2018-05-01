__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel, QSlider, QWidget
from PyQt5 import QtGui
import pyqtgraph as pg
import numpy as np
import sys

class Slider(QWidget):
    def __init__(self, current, minimum, maximum, parent=None):
        super(Slider, self).__init__(parent=parent)
        self.layout = QtGui.QGridLayout(self)
        self.label = QLabel(self)
        self.slider = QSlider(self)
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setRange(minimum, maximum)
        self.slider.setValue(current)

        self.layout.addWidget(self.label,0,1)
        self.layout.addWidget(self.slider,0,0)
        self.resize(self.sizeHint())

        self.slider.valueChanged.connect(self.set_label_value)
        self.x = None
        self.set_label_value(self.slider.value())

    def set_label_value(self, value):
        self.label.setText(str(value))
    
    def get_value(self):
        return self.slider.value()

  