# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import time
import threading
import json
import logging
import csv
from time import sleep
import websocket

from raw_data_plot_data import Raw_Data_Plot_Data
         

class WS_Data(object):
    """
    This class create a websocket and handle data which is received from socket
    """
    def __init__(self, url, channel_num=64, scale_line_rela_val=2,
         scale_line_real_val=3, data_window_height=10,
         raw_plot_sample_rate=1000):
        """
        Create a websocket and setup its handler

        url:
            The url for web socket to connect with

        channel_num:
            The number of channels

        scale_line_rela_val:
            The relative value between scale line and real value in channel
            data

        scale_line_real_val:
            The real value of scale line associates with plot y axis

        data_window_height:
            The window height is the shift height of each channel data

        """
        self.url = url
        self.channel_num = channel_num
        self.scale_line_rela_val = scale_line_rela_val
        self.scale_line_real_val = scale_line_real_val
        self.data_window_height = data_window_height
        self.raw_plot_sample_rate = raw_plot_sample_rate
        self.decimated_data_time = list()
        self.decimated_data = list()
        self.transed_decimated_data = list()
        self.raw_sample_rate = 1000 #TODO ask from web socket
        self.plot_origin = None
        self.ch_label = list()
        self.events = list()
        for i in range(self.channel_num):
            self.decimated_data.append(list())
            self.transed_decimated_data.append(list())

        self.raw_cache_size = 1000
        self.file_pointer = None
        self.csv_writer = None
        self.cursor = None
        self.update_time_interval = 0.1

        self.ws = websocket.WebSocketApp(url,
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        self.ws_thread = threading.Thread(target=self.on_connect)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        while not self.ws.sock.connected:
            sleep(1)

        self.send_init_commands()

    def on_connect(self):    
        while True:
            self.ws.run_forever()
            logging.error("Connection closed reconnect in 0.5 sec")
            time.sleep(0.5)
        
    def on_message(self, ws, message):
        """
        Handle data from socket and store it into different plot's data
        structure
        """
        try:
            raw = json.loads(message)
            if raw["type"]["type"] == "data":
                self.add_plot_decimated_data(raw)
            elif raw["type"]["type"] == "response":
                self.ch_label = raw["contents"]["ch_label"]
            else:
                pass
        except Exception as e:
            logging.error(str(e))

    def on_error(self, ws, error):
        """
        Handle websocket error
        """
        pass

    def on_close(self, ws):
        """
        Handle websocket close event
        """
        pass

    def add_plot_decimated_data(self, data):
        """
        Store the raw data plot data received from websocket, and store the
        transformed data.

        The transformation is to let original data fit into specific scale.
        """
        if len(data['contents']['data']) != self.channel_num:
            raise AssertionError("The received raw data unmatch channel num")

        time = data['contents']['sync_tick'] / self.raw_plot_sample_rate

        self.decimated_data_time.append(time)
        for idx, ori_data in enumerate(data['contents']['data']):
            self.decimated_data[idx].append(ori_data)
            self.transed_decimated_data[idx].append(self._tranform_data(ori_data))

        if data['contents']['event'].get('event_id', None) is not None:
            self.events.append({
                'tick': data['contents']['sync_tick'],
                'time': time,
                'name': data['contents']['event']['event_id'],
                'duration': data['contents']['event']['event_duration']        
            })

        if self.cursor is not None and (self.decimated_data_time[-1] - self.cursor) > self.update_time_interval:
            self.cursor = self.decimated_data_time[-1]

    def get_plot_decimated_data(self, mode="Scan", channels=None):
        """
        Return the raw data used to draw ``mode`` mode raw data plot
        The return value follow the order of channels.

        Scan mode x axis:
        origin, origin+1, ... , cursor, last_origin , ... , origin-2, origin-1
        20.1  , 20.2    , ... , 27.2  , 17.5        , ... , 19.95    , 19.98
        ||
        \/
        0.1   , 0.2     , ... , 7.2   , 8.5         , ... , 9.95     , 9.98

        Scroll mode x axis:
        origin, ......... , cursor
        3.5   , 3.6 , ... , 13.5
        ||
        \/
        0     , 0.1 , ... , 10.0

        The ``channels`` is the index of channels,
        if ``channels`` is None, return all channels.
        Return:
        Instance of the ``Raw_Data_Plot_Data`` class
        """
        if self.cursor is None:
            raise AssertionError("Scan mode should provide `cursor`")

        if channels is None:
            channels = range(1, self.channel_num+1)

        data = Raw_Data_Plot_Data(self.decimated_data_time, self.transed_decimated_data,
                                    self.events,mode=mode, channels=channels,
                                    cursor=self.cursor, plot_origin=self.plot_origin,
                                    ch_label=self.ch_label)

        return data

    def clean_oudated_data(self, cursor):
        outdated_time = cursor - 11
        while self.decimated_data_time[0] < outdated_time:
            self.decimated_data_time.pop(0)
            for i in range(self.channel_num):
                self.decimated_data[i].pop(0)
                self.transed_decimated_data[i].pop(0)
        while len(self.events) != 0 and self.events[0]['tick'] / self.raw_plot_sample_rate < outdated_time:
            self.events.pop(0)

    def get_plot_scale_line_pos(self, channels=None):
        """
        Return the scale lines position of ``index`` channels in raw data plot.
        The return value follow the order of channels.

        The ``channels`` is the index of channels,
        if ``channels`` is None, return all channels.

        If
            data_window_height = 10
            scale_line_real_val = 3
        Then
        {
            pos: [13, 23, 33, ...]
            ori: [10, 20, 30, ...]
            neg: [7 , 17, 27, ...]
        }
        """
        if channels is None:
            channels = range(1, self.channel_num)

        pos = list()
        ori = list()
        neg = list()
        for ch_origin in range(1, len(channels)+1):
            ori.append(ch_origin*self.data_window_height)
            pos.append(ori[-1]+self.scale_line_real_val)
            neg.append(ori[-1]-self.scale_line_real_val)

        return dict(pos=pos, ori=ori, neg=neg)

    def _tranform_data(self,ori_data):
        """
        Transform the original data to the specify scale
        """
        return self.scale_line_real_val * (ori_data/self.scale_line_rela_val)

    def update_scale_line_rela_val(self, new_scale_line_rela_val):
        self.scale_line_rela_val = new_scale_line_rela_val
        for idx_ch in range(len(self.decimated_data)):
            for idx_data in range(len(self.decimated_data[idx_ch])):
                self.transed_decimated_data[idx_ch][idx_data] = self._tranform_data(self.decimated_data[idx_ch][idx_data])
                             
    def get_scale_line_rela_val(self):
        return self.scale_line_rela_val

    def send_init_commands(self):
        dec_setting_msg = json.dumps({
            "type": "dec"
        })
        self.ws.send(dec_setting_msg)

