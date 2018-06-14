import pyqtgraph as pg
from pyqtgraph.dockarea import *
from PyQt5 import QtCore, QtGui, QtWidgets

class CustomizedDialog(QtGui.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.resize(500,400)

    def closeEvent(self, event):
        self.parent.channel_selector_win = None

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
            for i in range(1, 65):
                item = QtGui.QListWidgetItem(self.selector)
                item.setText("Channel {}".format(i))
                item.setData(QtCore.Qt.UserRole, i)
                if i in self.parent.selected_channels:
                    item.setSelected(True)
        else:
            for i in range(1, 65):
                item = QtGui.QListWidgetItem(self.selector)
                item.setText("Channel {}".format(i))
                item.setText(self.parent.ws_data.ch_label[i - 1])
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
        self.parent.selected_channels = sorted([item.data(QtCore.Qt.UserRole) for item in self.selector.selectedItems()])
        self.parent.update_curves_size()
        self.close()

    def select_all_channels(self):
        for idx in range(len(self.selector)):
            self.selector.item(idx).setSelected(True)
    
    def select_none_channels(self):
        for idx in range(len(self.selector)):
            self.selector.item(idx).setSelected(False)

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
