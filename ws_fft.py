# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import time
import threading
import json
import logging
import copy
from time import sleep
import websocket

class WS_FFT(object):
    def __init__(self, url, plot_name):
        #plot_name: 
            # "FFT_PS" for Power Spectrum
            # "FFT_TF" for Time Frequency
        self.url = url
        self.plot_name = plot_name
        self.FFT_data = list()
        self.tick = 0
        self.ch_label = None
        self.channel_num = None

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
                if raw["type"]["source_name"] == "FFT":
                    self.add_FFT_data(raw)
            elif raw["type"]["type"] == "response":
                self.channel_num = raw["contents"]["data_size"][0]
                self.freq_num = raw["contents"]["data_size"][1]
                self.freq_range = raw["contents"]["freq_range"]
                self.freq_label = raw["contents"]["freq_label"]
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
    
    def add_FFT_data(self, data):
        self.FFT_data.append(copy.deepcopy(data["contents"]['data']))
        self.tick = data["contents"]["sync_tick"]

    def clean_oudated_data(self):
        pass

    def send_init_commands(self):
        FFT_setting_msg = json.dumps({
            "type": self.plot_name
        })
        self.ws.send(FFT_setting_msg)

