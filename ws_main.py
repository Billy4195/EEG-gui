import os
import os.path
import errno
import time
import threading
import json
import websocket
import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import asyncio
import logging
import csv


class WS_CLIENT(object):
    def __init__(self, main_ui, url):
        self.url = url
        self.main_ui = main_ui
        self.raw_cache_size = 1000
        self.raw_data = list()
        self.raw_data_ticks = list()
        self.raw_data_events = list()
        self.recording_data = False
        self.record_start_tick = None
        self.raw_sample_rate = 1000  # TODO ask from web socket

        self.decimated_data_msg = list()
        self.impedance_data_msg = list()
        self.FFT_data_msg = list()
        self.PB_data_msg = list()

        self.ws = websocket.WebSocketApp(url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws_thread = threading.Thread(target=self.on_connect)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        while not self.ws.sock.connected:
            time.sleep(1)

        self.send_info_req()

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
            if raw["type"]["source_name"] == "device":
                self.main_ui.set_device_info(
                    'mockID', raw["contents"]["sampling_rate"], raw["contents"]["resolution"], raw["contents"]["battery"])
            elif raw["type"]["source_name"] == "raw" and raw["type"]["type"] == "data":
                self.add_raw_data(raw)
            elif raw["type"]["source_name"] == "decimation":
                self.decimated_data_msg.append(message)
            elif raw["type"]["source_name"] == "impedance":
                self.impedance_data_msg.append(message)
            elif raw["type"]["source_name"] == "FFT":
                self.FFT_data_msg.append(message)
            elif raw["type"]["source_name"] == "PowerBand":
                self.PB_data_msg.append(message)
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

    def send_info_req(self):
        device_request_msg = json.dumps({
            "type": {
                "type": "request",
                "target_tpye": "device",
                "target_name": "device"
            },
            "name": None,
            "contents": "device info"
        })
        self.ws.send(device_request_msg)

    def send_setting_raw(self, operation):
        raw_setting_msg = json.dumps({
            "type": {
                "type": "setting",
                "target_tpye": "raw",
                "target_name": "raw"
            },
            "name": None,
            "contents": {
                "enable": operation,
                "chunk_size": 4
            }
        })
        self.ws.send(raw_setting_msg)

    def send_setting_dec(self, operation):
        dec_setting_msg = json.dumps({
            "type": {
                "type": "setting",
                "target_tpye": "algorithm",
                "target_name": "decimation"
            },
            "name": None,
            "contents": {
                "enable": operation,
                "decimate_num": 4
            }
        })
        self.ws.send(dec_setting_msg)

    def send_setting_imp(self, operation):
        imp_setting_msg = json.dumps({
            "type": {
                "type": "setting",
                "target_tpye": "device",
                "target_name": "impedance"
            },
            "name": None,
            "contents": {
                "enable": operation
            }
        })
        self.ws.send(imp_setting_msg)

    def send_setting_FFT(self, operation):
        FFT_setting_msg = json.dumps({
            "type": {
                "type": "setting",
                "target_tpye": "algorithm",
                "target_name": "FFT"
            },
            "name": None,
            "contents": {
                "enable": operation,
                "window_size": 2,
                "window_interval": 0.5,
                "freq_range": [0, 30]
            }
        })
        self.ws.send(FFT_setting_msg)

    def send_setting_PB(self, operation):
        PB_setting_msg = json.dumps({
            "type": {
                "type": "setting",
                "target_tpye": "algorithm",
                "target_name": "PowerBand"
            },
            "name": None,
            "contents": {
                "enable": operation,
                "window_size": 2,
                "window_interval": 0.5,
                "smooth": 4
            }
        })
        self.ws.send(PB_setting_msg)

    def send_request_raw(self):
        raw_request_msg = json.dumps({
            "type": {
                "type": "request",
                "target_tpye": "raw",
                "target_name": "raw"
            },
            "name": None,
            "contents": {
                "requirement": [
                    "enable",
                    "sps_origin",
                    "ch_num",
                    "chunk_size",
                    "ch_label"
                ]
            }
        })
        self.ws.send(raw_request_msg)

    def send_request_dec(self):
        dec_request_msg = json.dumps({
            "type": {
                "type": "request",
                "target_tpye": "algorithm",
                "target_name": "decimation"
            },
            "name": None,
            "contents": {
                "requirement": [
                    "enable",
                    "sps_origin",
                    "sps_decimated",
                    "decimate_num",
                    "ch_num",
                    "ch_label"
                ]
            }
        })
        self.ws.send(dec_request_msg)

    def send_request_imp(self):
        imp_request_msg = json.dumps({
            "type": {
                "type": "request",
                "target_tpye": "device",
                "target_name": "impedance"
            },
            "name": None,
            "contents": [
                "enable",
                "sps_origin",
                "ch_num",
                "ch_label"
            ]
        })
        self.ws.send(imp_request_msg)

    def send_request_FFT(self):
        FFT_request_msg = json.dumps({
            "type": {
                "type": "request",
                "target_tpye": "algorithm",
                "target_name": "FFT"
            },
            "name": None,
            "contents": {
                "requirement": [
                    "enable",
                    "window_size",
                    "window_move",
                    "freq_range",
                    "freq_label",
                    "data_size",
                    "ch_label"
                ]
            }
        })
        self.ws.send(FFT_request_msg)

    def send_request_PB(self):
        PB_request_msg = json.dumps({
            "type": {
                "type": "request",
                "target_tpye": "algorithm",
                "target_name": "PowerBand"
            },
            "name": None,
            "contents": {
                "requirement": [
                    "enable",
                    "window_size",
                    "window_interval",
                    "smooth",
                    "ch_num",
                    "ch_label"
                ]
            }
        })
        self.ws.send(PB_request_msg)

    def add_raw_data(self, data):
        if self.recording_data:
            contents = data["contents"]
            # TODO check event is single or multiple
            if isinstance(contents["sync_tick"], list):
                for eeg, tick, e_id, e_du in zip(contents["eeg"],
                                                 contents["sync_tick"],
                                                 contents["event"]["event_id"],
                                                 contents["event"]["event_duration"]):
                    self.raw_data.append(eeg)
                    self.raw_data_ticks.append(tick)
                    self.raw_data_events.append(dict(event_id=e_id,
                                                     event_duration=e_du))
            else:
                self.raw_data.append(contents["eeg"])
                self.raw_data_ticks.append(contents["sync_tick"])
                self.raw_data_events.append(contents["event"])

            if len(self.raw_data) > self.raw_cache_size:
                self.write_raw_data_to_file()

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def safe_open_w(self, path):
        self.mkdir_p(os.path.dirname(path))
        return open(path, 'w')

    def open_raw_record_file(self, filename):
        self.file_pointer = self.safe_open_w(filename)
        self.csv_writer = csv.writer(self.file_pointer)

        self.raw_data.clear()
        self.raw_data_ticks.clear()
        self.raw_data_events.clear()
        self.recording_data = True

        first_row = list()
        first_row.append("Time:{}Hz".format(self.raw_sample_rate))
        first_row.append("Epoch")
        # TODO chagne to channel name
        for i in range(1, 65):
            first_row.append("Channel_{}".format(i))
        first_row.append("Event ID")
        first_row.append("Event Date")
        first_row.append("Event Duration")
        self.csv_writer.writerow(first_row)

    def write_raw_data_to_file(self):
        if self.csv_writer is not None:
            if self.record_start_tick is None:
                self.record_start_tick = self.raw_data_ticks[0]

            copied_data = self.raw_data[:self.raw_cache_size]
            self.raw_data = self.raw_data[self.raw_cache_size:]

            copied_ticks = self.raw_data_ticks[:self.raw_cache_size]
            self.raw_data_ticks = self.raw_data_ticks[self.raw_cache_size:]

            copied_events = self.raw_data_events[:self.raw_cache_size]
            self.raw_data_events = self.raw_data_events[self.raw_cache_size:]

            assert len(copied_data) == len(copied_ticks)
            assert len(copied_data) == len(copied_events)
            for tick, ch_data, events in zip(copied_ticks, copied_data, copied_events):
                row = list()

                time = (tick - self.record_start_tick) / self.raw_sample_rate
                epoch = 0
                event_id = ":".join([str(id) for id in events["event_id"]])
                event_date = ":".join([str(time) for e in events["event_id"]])
                event_duration = ":".join([str(duration)
                                           for duration in events["event_duration"]])

                row.append(time)
                row.append(epoch)
                row += ch_data
                row.append(event_id)
                row.append(event_date)
                row.append(event_duration)
                self.csv_writer.writerow(row)

    def close_raw_record_file(self):
        self.recording_data = False

        while self.raw_data:
            self.write_raw_data_to_file()

        self.file_pointer.close()
        self.file_pointer = None
        self.csv_writer = None


class WS_SERVER(object):
    def __init__(self, main_ui, ws_client, port):
        self.fft_context = FFT_Context()
        self.pb_context = PB_Context()
        self.port = port
        self.ws_app = tornado.web.Application([
            (r"/", WebSocketHandler, {
                'fft_context': self.fft_context,
                'pb_context': self.pb_context,
                'ws_client': ws_client,
                'main_ui': main_ui
            })
        ])
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def start_server(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.ws_app.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


class FFT_Context(object):
    def __init__(self):
        self.loop = None
        self.PS_client = None
        self.TF_client = None


class PB_Context(object):
    def __init__(self):
        self.loop = None
        self.bar_client = None
        self.topo_client = None


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self, fft_context, pb_context, ws_client, main_ui):
        self.fft_context = fft_context
        self.pb_context = pb_context
        self.main_ui = main_ui
        self.ws_client = ws_client
        self.dec_client = None
        self.imp_client = None

    def check_origin(self, origin):
        return True

    def on_message(self, message):
        #self.write_message(u"Your message was: "+message)
        try:
            cmd = json.loads(message)
            if cmd["type"] == "dec":
                self.ws_client.decimated_data_msg.clear()
                self.ws_client.send_request_dec()
                self.ws_client.send_setting_dec(True)
                self.dec_client = self
                self.dec_loop = tornado.ioloop.PeriodicCallback(
                    self.send_dec, 5)
                self.dec_loop.start()
            elif cmd["type"] == "imp":
                self.ws_client.impedance_data_msg.clear()
                self.ws_client.send_request_imp()
                self.ws_client.send_setting_imp(True)
                self.imp_client = self
                self.imp_loop = tornado.ioloop.PeriodicCallback(
                    self.send_imp, 100)
                self.imp_loop.start()
            elif cmd["type"] == "FFT_PS":
                self.fft_context.PS_client = self
                if self.fft_context.TF_client is None:
                    self.ws_client.FFT_data_msg.clear()
                    self.ws_client.send_setting_FFT(True)
                    if self.fft_context.loop is None:
                        self.fft_context.loop = tornado.ioloop.PeriodicCallback(
                            self.send_FFT, 100)
                        self.fft_context.loop.start()
                self.ws_client.send_request_FFT()
            elif cmd["type"] == "FFT_TF":
                self.fft_context.TF_client = self
                if self.fft_context.PS_client is None:
                    self.ws_client.FFT_data_msg.clear()
                    self.ws_client.send_setting_FFT(True)
                    if self.fft_context.loop is None:
                        self.fft_context.loop = tornado.ioloop.PeriodicCallback(
                            self.send_FFT, 100)
                        self.fft_context.loop.start()
                self.ws_client.send_request_FFT()
            elif cmd["type"] == "PB_bar":
                self.pb_context.bar_client = self
                if self.pb_context.topo_client is None:
                    self.ws_client.PB_data_msg.clear()
                    self.ws_client.send_setting_PB(True)
                    if self.pb_context.loop is None:
                        self.pb_context.loop = tornado.ioloop.PeriodicCallback(
                            self.send_PB, 100)
                        self.pb_context.loop.start()
                self.ws_client.send_request_PB()
            elif cmd["type"] == "PB_topo":
                self.pb_context.topo_client = self
                if self.pb_context.bar_client is None:
                    self.ws_client.PB_data_msg.clear()
                    self.ws_client.send_setting_PB(True)
                    if self.pb_context.loop is None:
                        self.pb_context.loop = tornado.ioloop.PeriodicCallback(
                            self.send_PB, 100)
                        self.pb_context.loop.start()
                self.ws_client.send_request_PB()
            else:
                pass
        except Exception as e:
            logging.error(str(e))

    def on_close(self):
        if self == self.dec_client:
            self.ws_client.send_setting_dec(False)
            self.dec_loop.stop()
            self.dec_client = None
            self.main_ui.signal_btn.setEnabled(True)
            self.main_ui.update_contact_btn_state()
        elif self == self.fft_context.PS_client:
            if self.fft_context.TF_client is None:
                self.ws_client.send_setting_FFT(False)
                if self.fft_context.loop is not None:
                    self.fft_context.loop.stop()
                    self.fft_context.loop = None
            self.fft_context.PS_client = None
            self.main_ui.spectrum_btn.setEnabled(True)
            self.main_ui.update_contact_btn_state()
        elif self == self.fft_context.TF_client:
            if self.fft_context.PS_client is None:
                self.ws_client.send_setting_FFT(False)
                if self.fft_context.loop is not None:
                    self.fft_context.loop.stop()
                    self.fft_context.loop = None
            self.fft_context.TF_client = None
            self.main_ui.TF_btn.setEnabled(True)
            self.main_ui.update_contact_btn_state()
        elif self == self.pb_context.bar_client:
            if self.pb_context.topo_client is None:
                self.ws_client.send_setting_PB(False)
                if self.pb_context.loop is not None:
                    self.pb_context.loop.stop()
                    self.pb_context.loop = None
            self.pb_context.bar_client = None
            self.main_ui.bar_btn.setEnabled(True)
            self.main_ui.update_contact_btn_state()
        elif self == self.pb_context.topo_client:
            if self.pb_context.bar_client is None:
                self.ws_client.send_setting_PB(False)
                if self.pb_context.loop is not None:
                    self.pb_context.loop.stop()
                    self.pb_context.loop = None
            self.pb_context.topo_client = None
            self.main_ui.topo_btn.setEnabled(True)
            self.main_ui.update_contact_btn_state()
        elif self == self.imp_client:
            self.ws_client.send_setting_imp(False)
            self.imp_loop.stop()
            self.imp_client = None
            self.main_ui.set_all_button_state(True)
        else:
            logging.error("client identification gg")

    def send_dec(self):
        while(1):
            try:
                if self.ws_client.decimated_data_msg:
                    packet = self.ws_client.decimated_data_msg.pop(0)
                    self.write_message(packet)
                else:
                    return
            except Exception as e:
                logging.error(str(e))
                return

    def send_imp(self):
        while(1):
            try:
                if self.ws_client.impedance_data_msg:
                    packet = self.ws_client.impedance_data_msg.pop(0)
                    self.write_message(packet)
                else:
                    return
            except Exception as e:
                logging.error(str(e))
                return

    def send_FFT(self):
        while(1):
            try:
                if self.ws_client.FFT_data_msg:
                    packet = self.ws_client.FFT_data_msg.pop(0)
                    if self.fft_context.TF_client is not None:
                        self.fft_context.TF_client.write_message(packet)
                    if self.fft_context.PS_client is not None:
                        self.fft_context.PS_client.write_message(packet)
                else:
                    return
            except Exception as e:
                logging.error(str(e))
                return

    def send_PB(self):
        while(1):
            try:
                if self.ws_client.PB_data_msg:
                    packet = self.ws_client.PB_data_msg.pop(0)
                    if self.pb_context.bar_client is not None:
                        self.pb_context.bar_client.write_message(packet)
                    if self.pb_context.topo_client is not None:
                        self.pb_context.topo_client.write_message(packet)
                else:
                    return
            except Exception as e:
                logging.error(str(e))
                return
