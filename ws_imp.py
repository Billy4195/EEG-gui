# -*- coding: utf-8 -*-

__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import time
import threading
import json
import logging
from time import sleep
import websocket 

class WS_Imp(object):
    def __init__(self, contact_plot, url):
        self.contact_plot = contact_plot
        self.url = url
        self.impedance_data = list()
        self.channel_num = 8
        self.tick = 0

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
                if raw["type"]["source_name"] == "impedance":
                    self.add_impedance_data(raw)
            elif raw["type"]["type"] == "response":
                self.channel_num = raw["contents"]["ch_num"]
                self.contact_plot.ch_label = raw["contents"]["ch_label"]                
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
    
    def add_impedance_data(self, data):
        if len(data['contents']['impedance']) != self.channel_num:
            raise AssertionError("The received raw data unmatch channel num")
        self.impedance_data.append(data['contents']['impedance'])
        self.tick = data["contents"]["sync_tick"]

    def clean_oudated_data(self):
        pass

    def send_init_commands(self):
        imp_setting_msg = json.dumps({
            "type": "imp"
        })
        self.ws.send(imp_setting_msg)

