import pyqtgraph as pg
from pyqtgraph.dockarea import *
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import ScaleUI

class CustomizedDialog(QtGui.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.resize(500,400)

    def closeEvent(self, event):
        raise NotImplementedError

class ChannelSelector(CustomizedDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Select Channels")
        self.init_ui()
        self.show()

    def init_ui(self):
        vlayout = QtGui.QVBoxLayout(self)

        self.selector = QtGui.QListWidget()
        self.selector.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        if len(self.parent.ws_data.ch_label) is 0:
            for i in range(1 ,self.parent.ws_data.channel_num+1):
                item = QtGui.QListWidgetItem(self.selector)
                item.setText("Channel {}".format(i))
                item.setData(QtCore.Qt.UserRole, i)
                if i in self.parent.selected_channels:
                    item.setSelected(True)
        else:
            for i, ch_name in enumerate(self.parent.ws_data.ch_label, start=1):
                item = QtGui.QListWidgetItem(self.selector)
                item.setText(ch_name)
                item.setData(QtCore.Qt.UserRole, i)
                if i in self.parent.selected_channels:
                    item.setSelected(True)

        self.button_box = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal,
                                            self)
        self.button_box.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
        self.button_box.addButton("Apply", QtGui.QDialogButtonBox.AcceptRole)
        clear_all_btn = self.button_box.addButton("Clear All",
                                QtGui.QDialogButtonBox.ResetRole)
        select_all_btn = self.button_box.addButton("Select All",
                                QtGui.QDialogButtonBox.ActionRole)

        self.button_box.accepted.connect(self.channel_select_handler)
        self.button_box.rejected.connect(self.close)
        clear_all_btn.clicked.connect(self.select_none_channels)
        select_all_btn.clicked.connect(self.select_all_channels)

        vlayout.addWidget(self.selector)
        vlayout.addWidget(self.button_box)

    def channel_select_handler(self):
        channels = sorted([item.data(QtCore.Qt.UserRole) for item in self.selector.selectedItems()])
        self.parent.update_selected_channels(channels)
        self.close()

    def select_all_channels(self):
        for idx in range(len(self.selector)):
            self.selector.item(idx).setSelected(True)
    
    def select_none_channels(self):
        for idx in range(len(self.selector)):
            self.selector.item(idx).setSelected(False)

    def closeEvent(self, event):
        self.parent.channel_selector_win = None
        self.close()

class EventTable(CustomizedDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Event List")
        self.init_ui()
        self.update_event_table()
        self.show()

    def init_ui(self):
        self.eventTable = QtGui.QTableWidget()
        self.eventTable.setColumnCount(3)
        self.eventTable.setHorizontalHeaderLabels(['Time', 'Name', 'Duration'])
        gridlayout = QtGui.QGridLayout(self)
        gridlayout.addWidget(self.eventTable)

    def update_event_table(self):
        self.eventTable.clearContents()
        if len(self.parent.ws_data.events) > 0:
            self.eventTable.setRowCount(len(self.parent.ws_data.events))
            for row, event in enumerate(self.parent.ws_data.events):
                for key, value in event.items():
                    if key is 'time':
                        self.eventTable.setItem(row, 0, QtGui.QTableWidgetItem(str(value)))
                    elif key is 'name':
                        self.eventTable.setItem(row, 1, QtGui.QTableWidgetItem(str(value)))
                    elif key is 'duration':
                        self.eventTable.setItem(row, 2, QtGui.QTableWidgetItem(str(value)))

    def closeEvent(self, event):
        self.parent.event_table_win = None
        self.close()

class ScaleHandler(CustomizedDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Adjust Scales")
        self.resize(300,150)
        self.init_ui()
        self.show()

    def init_ui(self):
        gridlayout = QtGui.QGridLayout(self)
        self.current_scale = (self.parent.ws_data.get_scale_line_rela_val(), self.parent.time_scale)
        self.selector = ScaleUI.ScaleSelector(self.current_scale)

        self.button_box = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal,
                                            self)
        self.button_box.addButton("Cancel", QtGui.QDialogButtonBox.RejectRole)
        self.button_box.addButton("Apply", QtGui.QDialogButtonBox.AcceptRole)

        self.button_box.accepted.connect(self.scale_adjust_handler)
        self.button_box.rejected.connect(self.close)

        gridlayout.addWidget(self.selector,0,0)
        gridlayout.addWidget(self.button_box,1,0)

    def scale_adjust_handler(self):
        amp_scale, time_scale = self.selector.get_value()
        if amp_scale != self.current_scale[0]:
            self.parent.ws_data.update_scale_line_rela_val(amp_scale)
        elif time_scale != self.current_scale[1]:
            self.parent.update_time_scale(time_scale)
        self.close()

    def closeEvent(self, event):
        self.parent.scale_adjust_win = None
        self.close()

class Big_Bar_Plot(CustomizedDialog):
    def __init__(self, parent, ch_name):
        super().__init__(parent)
        self.name = ch_name
        self.setWindowTitle("{name} Power Band".format(name=self.name))
        self.init_ui()
        self.show()

    def init_ui(self):
        print("DELETE on close", self.testAttribute(QtCore.Qt.WA_DeleteOnClose))
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel("Band\n%")
        self.ax.xaxis.set_label_coords(0, -0.04)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["bottom"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_visible(False)
        self.ax.yaxis.grid(True)
        self.canvas = FigureCanvas(self.fig)
        grid_layout = QtGui.QGridLayout(self)
        grid_layout.addWidget(self.canvas)
        self.resize(500, 500)

    def draw(self, data, color):
        p_sum = sum(data)
        labels = ["$\delta$", "$\\theta$", "L-$\\alpha$ ", "H-$\\alpha$", "L-$\\beta$",
                    "M-$\\beta$", "H-$\\beta$", "$\gamma$"]
        percentages = ["{:.1f}".format(d/p_sum*100) for d in data]
        self.ax.cla()
        # self.ax.set_title("{name} Power Band".format(name=self.name))
        self.ax.set_ylabel("Power ($uV^2$)")
        self.ax.bar(list(range(8)), data, color=color)
        self.ax.set_xlabel("Band\n%")
        self.ax.xaxis.set_label_coords(0, -0.04)
        self.ax.set_xticks(list(range(8)))
        self.ax.set_xticklabels(["{}\n{}".format(label, per) for label, per in zip(labels,percentages)])
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["bottom"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.spines["left"].set_visible(False)
        self.ax.yaxis.grid(True)
        self.fig.canvas.draw()

    def closeEvent(self, event):
        self.parent.big_plot_closed(self)
        self.close()
        plt.close()

