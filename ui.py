# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

from subprocess import Popen
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np
import time
import websocket
import threading
import json
import logging
import math
import copy
import os
from ws_main import WS_CLIENT, WS_SERVER
from raw_data_plot import Raw_Data_Plot
from csv_file import CSV_FILE
from edf_file import EDF_FILE
from bdf_file import BDF_FILE
import os
from timer import TimeThread

class EEG_Application(QtGui.QApplication):
    def __init__(self):
        super().__init__([])
        self.ws_url = "ws://localhost:8888"

        self.main_win = QtGui.QMainWindow()
        self.main_win.show()

        self.decimated_plot_proc = None
        self.contact_plot_proc = None
        self.spectrum_proc = None
        self.TF_proc = None
        self.bar_proc = None
        self.topo_proc = None
        self.setupUi()
        self.setupSignals()
        self.set_all_button_state(False) 
        self.state = "IDLE"

        self.current_file = None

    def init_ws(self):
        self.connect_btn.setEnabled(False)
        self.ws_client = WS_CLIENT(main_ui=self, url=self.ws_url)
        self.ws_server = WS_SERVER(main_ui=self, ws_client=self.ws_client, port=7777)
        self.set_all_button_state(True) 
        
    def setupUi(self):
        """Create Basic UI layout"""
        self.main_win.setObjectName("MainWindow")
        self.main_win.setWindowTitle("EEG")
        self.main_win.resize(500, 800)
        self.control_panel = QtGui.QWidget()
        self.main_win.setCentralWidget(self.control_panel)

        grid = QtGui.QGridLayout(self.control_panel)
        grid.addWidget(self.device_group(), 0, 0)
        grid.addWidget(self.plot_group(), 1, 0)
        grid.addWidget(self.record_group(), 2, 0)
        grid.addWidget(self.log_group(), 3, 0)

    def device_group(self):
        groupBox = QtGui.QGroupBox("Device")

        _device_id = QtWidgets.QLabel()
        _sampling_rate = QtWidgets.QLabel()
        _Battery_state = QtWidgets.QLabel()
        _resolution = QtWidgets.QLabel()

        _device_id.setText("DeviceID:")
        _sampling_rate.setText("Sampling Rate:")
        _Battery_state.setText("Battery:")
        _resolution.setText("Resolution:")

        self.device_id = QtWidgets.QLabel()
        self.sampling_rate = QtWidgets.QLabel()
        self.Battery_state = QtWidgets.QLabel()
        self.resolution = QtWidgets.QLabel()

        self.connect_btn = QtGui.QPushButton("Connect")

        self.device_id.setText("")
        self.sampling_rate.setText("")
        self.Battery_state.setText("")
        self.resolution.setText("")

        gridlayout = QtGui.QGridLayout()
        gridlayout.addWidget(_device_id, 0, 0, 1, 1)
        gridlayout.addWidget(_sampling_rate, 1, 0, 1, 1)
        gridlayout.addWidget(_Battery_state, 2, 0, 1, 1)
        gridlayout.addWidget(_resolution, 3, 0, 1, 1)

        gridlayout.addWidget(self.device_id, 0, 1, 1, 1)
        gridlayout.addWidget(self.sampling_rate, 1, 1, 1, 1)
        gridlayout.addWidget(self.Battery_state, 2, 1, 1, 1)
        gridlayout.addWidget(self.resolution, 3, 1, 1, 1)
        gridlayout.addWidget(self.connect_btn, 0, 2, 4, 1)

        groupBox.setLayout(gridlayout)
        return groupBox

    def set_device_info(self, id, sample_rate, resolution, bettery):
        self.device_id.setText(id)
        self.sampling_rate.setText(str(sample_rate) + " sps")
        self.Battery_state.setText(str(bettery) + "%")
        self.resolution.setText(str(resolution) + " bit")

    def plot_group(self):
        groupBox = QtGui.QGroupBox("Plot")

        self.contact_btn = QtGui.QPushButton("Contact")
        self.signal_btn = QtGui.QPushButton("Signal")
        self.spectrum_btn = QtGui.QPushButton("Spectrum")
        self.TF_btn = QtGui.QPushButton("Time-Freq.")
        self.bar_btn = QtGui.QPushButton("Bar")
        self.topo_btn = QtGui.QPushButton("Topographic")

        gridlayout = QtGui.QGridLayout()
        gridlayout.addWidget(self.contact_btn, 0, 0, 1, 1)
        gridlayout.addWidget(self.signal_btn, 0, 1, 1, 1)
        gridlayout.addWidget(self.spectrum_btn, 0, 2, 1, 1)
        gridlayout.addWidget(self.TF_btn, 0, 3, 1, 1)
        gridlayout.addWidget(self.bar_btn, 0, 4, 1, 1)
        gridlayout.addWidget(self.topo_btn, 0, 5, 1, 1)

        groupBox.setLayout(gridlayout)
        return groupBox
   
    def set_all_button_state(self, operation):
        self.signal_btn.setEnabled(operation)
        self.contact_btn.setEnabled(operation)
        self.spectrum_btn.setEnabled(operation)
        self.TF_btn.setEnabled(operation)
        self.bar_btn.setEnabled(operation)
        self.topo_btn.setEnabled(operation)
        self.record_btn.setEnabled(operation)
    
    def update_contact_btn_state(self):
        if self.record_btn.isEnabled() and self.signal_btn.isEnabled() \
                and self.spectrum_btn.isEnabled() and self.TF_btn.isEnabled() \
                and self.bar_btn.isEnabled() and self.topo_btn.isEnabled():
            self.contact_btn.setEnabled(True)
        else:
            self.contact_btn.setEnabled(False)

    def record_group(self):
        groupBox = QtGui.QGroupBox("Data Record")

        gridlayout = QtGui.QGridLayout()

        path_label = QtWidgets.QLabel()
        path_label.setText("File Path:")
        self.file_path_input = QtGui.QLineEdit()
        self.file_path_select_btn = QtGui.QPushButton("...")
        gridlayout.addWidget(path_label, 0, 0, 1, 2)
        gridlayout.addWidget(self.file_path_input, 0, 2, 1, 2)
        gridlayout.addWidget(self.file_path_select_btn, 0, 4, 1, 2)

        name_label = QtWidgets.QLabel()
        name_label.setText("File Name:")
        self.file_name_input = QtGui.QLineEdit()
        self.file_type = QtGui.QComboBox()
        self.file_type.addItem(".csv")
        self.file_type.addItem(".bdf")
        self.file_type.addItem(".edf")
        gridlayout.addWidget(name_label, 1, 0, 1, 2)
        gridlayout.addWidget(self.file_name_input, 1, 2, 1, 2)
        gridlayout.addWidget(self.file_type, 1, 4, 1, 2)

        self.record_btn = QtGui.QPushButton("Start Recording")
        self.record_btn.setStyleSheet("background-color: blue")
        self.stop_btn = QtGui.QPushButton("Stop Recording")
        self.stop_btn.setStyleSheet("background-color: red")
        gridlayout.addWidget(self.record_btn, 2, 0, 1, 3)
        gridlayout.addWidget(self.stop_btn, 2, 3, 1, 3)
        groupBox.setLayout(gridlayout)
        return groupBox

    def log_group(self):
        groupBox = QtGui.QGroupBox("Log Message")

        self.log_widget = QtGui.QPlainTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.appendPlainText("11:43:30   System start")

        boxlayout = QtGui.QVBoxLayout()
        boxlayout.addWidget(self.log_widget)

        groupBox.setLayout(boxlayout)
        self.recording_group = groupBox
        return groupBox

    def setupSignals(self):
        self.lastWindowClosed.connect(self.clean_up)
        self.connect_btn.clicked.connect(self.init_ws)
        self.signal_btn.clicked.connect(self.decimated_handler)
        self.contact_btn.clicked.connect(self.contact_handler)
        self.spectrum_btn.clicked.connect(self.spectrum_handler)
        self.TF_btn.clicked.connect(self.TF_handler)
        self.bar_btn.clicked.connect(self.bar_handler)
        self.topo_btn.clicked.connect(self.topo_handler)
        self.record_btn.clicked.connect(self.start_recording)
        self.stop_btn.clicked.connect(self.stop_recording)
        self.file_path_select_btn.clicked.connect(self.select_file_path)

    def decimated_handler(self):
        if self.decimated_plot_proc:
           if self.decimated_plot_proc.poll() is None:
                return
        try:
            self.signal_btn.setEnabled(False)
            self.contact_btn.setEnabled(False)
            if os.name is 'posix':
                self.decimated_plot_proc = Popen(['python3', 'raw_data_plot.py'])
            else:
                self.decimated_plot_proc = Popen(['python', 'raw_data_plot.py'])
        except Exception as e:
            self.decimated_plot_proc.kill()
            logging.error(str(e))

    def contact_handler(self):
        if self.contact_plot_proc:
            if self.contact_plot_proc.poll() is None:
                return
        try:
            self.set_all_button_state(False)
            if os.name is 'posix':
                self.contact_plot_proc = Popen(['python3', 'contact_plot.py'])
            else:
                self.contact_plot_proc = Popen(['python', 'contact_plot.py'])
        except Exception as e:
            self.contact_plot_proc.kill()
            logging.error(str(e))

    def spectrum_handler(self):
        if self.spectrum_proc:
            if self.spectrum_proc.poll() is None:
                return
        try:
            self.spectrum_btn.setEnabled(False)
            self.contact_btn.setEnabled(False)
            if os.name is 'posix':
                self.spectrum_proc = Popen(['python3', 'fft_plot.py'])
            else:            
                self.spectrum_proc = Popen(['python', 'fft_plot.py'])
        except Exception as e:
            self.spectrum_proc.kill()
            logging.error(str(e))
    
    def TF_handler(self):
        if self.TF_proc:
            if self.TF_proc.poll() is None:
                return
        try:
            self.TF_btn.setEnabled(False)
            self.contact_btn.setEnabled(False)        
            if os.name is 'posix':
                self.TF_proc = Popen(['python3', 'TF_plot.py'])
            else:            
                self.TF_proc = Popen(['python', 'TF_plot.py'])
        except Exception as e:
            self.TF_proc.kill()
            logging.error(str(e))
    
    def bar_handler(self):
        if self.bar_proc:
            if self.bar_proc.poll() is None:
                return
        try:
            self.bar_btn.setEnabled(False)
            self.contact_btn.setEnabled(False)
            if os.name is 'posix':
                self.bar_proc = Popen(['python3', 'bar_plot.py'])
            else:            
                self.bar_proc = Popen(['python', 'bar_plot.py'])
        except Exception as e:
            self.bar_proc.kill()
            logging.error(str(e))

    def topo_handler(self):
        if self.topo_proc:
            if self.topo_proc.poll() is None:
                return
        try:
            self.topo_btn.setEnabled(False)
            self.contact_btn.setEnabled(False)
            if os.name is 'posix':
                self.topo_proc = Popen(['python3', 'topo_plot.py'])
            else:            
                self.topo_proc = Popen(['python', 'topo_plot.py'])
        except Exception as e:
            self.topo_proc.kill()
            logging.error(str(e))

    def start_recording(self):
        if self.state == "IDLE":
            self.record_btn.setEnabled(False)
            self.contact_btn.setEnabled(False)
            self.ws_client.raw_data.clear()
            self.ws_client.raw_data_ticks.clear()
            self.ws_client.raw_data_events.clear()
            self.ws_client.send_request_raw()
            self.ws_client.send_setting_raw(True)

            if self.file_path_input.text() == "":
                default_path = os.path.join(os.path.expanduser("~"),"ArtiseBio")
                while os.path.isdir(default_path):
                    os.mkdir(default_path)
                self.file_path_input.setText(default_path)

            #set default filename
            if self.file_name_input.text() == "":
                timestamp = time.strftime("%y%m%d%H%M%S")
                default_filename = timestamp
                self.file_name_input.setText(default_filename)
            else:
                timestamp = time.strftime("%H%M%S")
                self.file_name_input.setText(self.file_name_input.text() + "_" + timestamp)

            file_path = os.path.join(self.file_path_input.text(), self.file_name_input.text()+self.file_type.currentText())

            if self.file_type.currentText() == '.csv':
                self.current_file = CSV_FILE(filepath=file_path, ws_client=self.ws_client)
            elif self.file_type.currentText() == '.edf':
                self.current_file = EDF_FILE(filepath=file_path, ws_client=self.ws_client)
            elif self.file_type.currentText() == '.bdf':
                self.current_file = BDF_FILE(filepath=file_path, ws_client=self.ws_client)

            self.state = "RECORDING"
            self.time_t = TimeThread()
            self.time_t.signal_time.connect(self.update_elapsed_time)
            self.time_t.start_timer()
        elif self.state == "RECORDING":
            pass

    def stop_recording(self):
        if self.state == "RECORDING":
            #check if other plot or record not running
            self.ws_client.send_setting_raw(False)
            self.time_t.stop()
            self.state = "IDLE"
            self.record_btn.setText("Start Recording")
            self.file_name_input.setText("")

            self.current_file.close_raw_record_file()
            self.current_file = None
            self.record_btn.setEnabled(True)
            self.update_contact_btn_state()
        elif self.state == "IDLE":
            pass

    def select_file_path(self):
        file_path = str(QtGui.QFileDialog.getExistingDirectory(self.recording_group, "Select Directory"))
        if file_path == '':
            return
        self.file_path_input.setText(file_path)

    def update_elapsed_time(self, timestamp):
        if self.state == "RECORDING":
            self.record_btn.setText("Elapsed Time "+ "{:.2f}".format(float(timestamp)))

    def clean_up(self):
        if self.decimated_plot_proc and self.decimated_plot_proc.poll() is None:
            self.decimated_plot_proc.kill()
        if self.contact_plot_proc and self.contact_plot_proc.poll() is None:
            self.contact_plot_proc.kill()
        if self.spectrum_proc and self.spectrum_proc.poll() is None:
            self.spectrum_proc.kill()
        if self.TF_proc and self.TF_proc.poll() is None:
            self.TF_proc.kill()
        if self.bar_proc and self.bar_proc.poll() is None:
            self.bar_proc.kill()
        if self.topo_proc and self.topo_proc.poll() is None:
            self.topo_proc.kill()
