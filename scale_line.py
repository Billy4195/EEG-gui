import pyqtgraph as pg
from PyQt5 import QtCore

class Plot_Scale_Line(object):
    def __init__(self, plot):
        self.v_grid_lines = list()
        for i in range(11):
            grid_lines = pg.InfiniteLine(pos=i, pen=pg.mkPen(color=(192, 192, 192), style=QtCore.Qt.DotLine))
            self.v_grid_lines.append(grid_lines)
            plot.addItem(grid_lines)

        self.zero_base_lines = list()
        self.neg_base_lines = list()
        self.pos_base_lines = list()
        for i in range(1,65):
            zero_line = pg.InfiniteLine(pos=i*10, angle=180, pen=(128, 128, 128))
            neg_line = pg.InfiniteLine(pos=i*10 - 3, angle=180, pen=pg.mkPen(color=(80, 80, 80), style=QtCore.Qt.DotLine))
            pos_line = pg.InfiniteLine(pos=i*10 + 3, angle=180, pen=pg.mkPen(color=(80, 80, 80), style=QtCore.Qt.DotLine))
            self.zero_base_lines.append(zero_line)
            self.neg_base_lines.append(neg_line)
            self.pos_base_lines.append(pos_line)
            plot.addItem(zero_line)
            plot.addItem(neg_line)
            plot.addItem(pos_line)

    def update(self, selected_channels, axises_tick):
        for idx, (val, label) in enumerate(axises_tick):
            self.v_grid_lines[idx].setValue(val)
        for i in range(64):
            if i < len(selected_channels):
                self.zero_base_lines[i].show()
                self.neg_base_lines[i].show()
                self.pos_base_lines[i].show()
            else:
                self.zero_base_lines[i].hide()
                self.neg_base_lines[i].hide()
                self.pos_base_lines[i].hide()
                continue