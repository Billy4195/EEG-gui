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

class WS_PB(object):
    def __init__(self, url, plot_name):
        #plot_name: 
            # "PB_bar" for bar chart
            # "PB_topo" for topo. chart
        self.url = url
        self.plot_name = plot_name
        self.power_data = list()
        self.z_all_data = list()
        self.z_each_data = list()
        self.ticks = list()
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
                if raw["type"]["source_name"] == "PowerBand":
                    self.add_PB_data(raw)
            elif raw["type"]["type"] == "response":
                self.channel_num = raw["contents"]["ch_num"]
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
    
    def add_PB_data(self, data):
        self.power_data.append(copy.deepcopy(data["contents"]['power']))
        self.z_all_data.append(copy.deepcopy(data["contents"]['z_score_all']))
        self.z_each_data.append(copy.deepcopy(data["contents"]['z_score_each']))
        self.ticks.append(data["contents"]["sync_tick"])

    def clean_oudated_data(self):
        pass

    def send_init_commands(self):
        PB_setting_msg = json.dumps({
            "type": self.plot_name
        })
        self.ws.send(PB_setting_msg)

