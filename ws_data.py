# -*- coding: utf-8 -*-

import time
import threading
import json
import logging
import copy

import websocket


class Raw_Data_Plot_Data(object):
    def __init__(self, time_data, channel_data, events, mode, channels, cursor,
                    window_size=10):
        self.trans_events = copy.deepcopy(events)
        self.set_mode(mode)
        self.param = self.cal_mode_param(time_data, cursor, window_size)
        self.axises_tick = self.calculate_axises_tick(time_data, channels,
                                                    window_size)
        self.calculate_plot_data(time_data, channel_data, channels)
    def set_mode(self, mode):
        if mode not in ["Scan", "Scroll"]:
            raise NotImplementedError("{} mode has not be implemented".format(
                mode))
        else:
            self.mode = mode

    def cal_mode_param(self, time_data, cursor, window_size=10):
        """
        According to the mode, calculating index of important point in
        time_data, and return the important parameter
        """
        if self.mode == "Scan":
            return self.cal_scan_mode_param(time_data, cursor, window_size)

        elif self.mode == "Scroll":
            return self.cal_scroll_mode_param(time_data, cursor, window_size)

    def cal_scan_mode_param(self, time_data, cursor, window_size):
        """
        ##Scan Mode##
        if
            cursor = 17.2, window_size = 10
        then
            origin = 10
            last_origin = 7.299999999999999

        origin_idx: min(time_data >= origin)
        cursor_idx: max(time_data <= cursor)
        last_origin_idx: min(time_data > last_origin)

        Return:
        {
            "origin": 10,
            "cursor": 17.2,
            "last_origin": 7.299999999999999,
            "idx": {
                "origin": ``origin_idx``,
                "cursor": ``cursor_idx``,
                "last_origin": ``last_origin_idx``
            }
        }
        """
        origin = (cursor // window_size) * window_size
        last_origin = cursor - window_size + 0.1
        if last_origin < 0: last_origin = 0

        origin_idx = None
        cursor_idx = 0
        last_origin_idx = None
        for idx, d in enumerate(time_data):
            if origin_idx is None and d >= origin:
                origin_idx = idx
            if d <= cursor:
                cursor_idx = idx
            if last_origin_idx is None and d > last_origin:
                last_origin_idx = idx
            if d > cursor:
                break

        if origin_idx is None:
            origin_idx = 0
        if last_origin_idx is None:
            last_origin_idx = 0

        return dict(origin=origin, cursor=cursor, last_origin=last_origin,
                    idx=dict(
                        origin=origin_idx,cursor=cursor_idx,
                        last_origin=last_origin_idx)
                )

    def cal_scroll_mode_param(self, time_data, cursor, window_size):
        """
        cursor = 17.2
        origin = 7

        origin_idx: min(time_data >= origin)
        cursor_idx: max(time_data <= cursor)

        Return:
        {
            "origin": 10,
            "cursor": 17.2,
            "idx": {
                "origin": ``origin_idx``,
                "cursor": ``cursor_idx``
            }
        }
        """
        origin = cursor - window_size

        origin_idx = None
        cursor_idx = 0
        for idx, d in enumerate(time_data):
            if origin_idx is None and d >= origin:
                origin_idx = idx
            if d <= cursor:
                cursor_idx = idx
            if d > cursor:
                break

        if origin_idx is None:
            origin_idx = 0

        return dict(origin=origin, cursor=cursor,
                    idx=dict(origin=origin_idx,cursor=cursor_idx)
                )

    def calculate_axises_tick(self, time_data, channels, window_size):
        """
        origin = 10
        cursor = 17.2
        last_origin = 7.299999999999999
        time_axis_ticks = [10, 11, 12, 13, 14, 15, 16, 17, 8, 9]
        ||
        \/
        time_axis_ticks = [(0, 10), (1, 11), ... , (9, 9)]

        channels = [1, 5, 7 ,9]
        channel_axis_ticks = [(40, 'Channel 1'), (30, 'Channel 5'), ... ]
        """
        if self.mode == "Scan":
            origin = self.param['origin']
            cursor = self.param['cursor']
            last_origin = self.param['last_origin']

            origin_idx = self.param['idx']['origin']
            cursor_idx = self.param['idx']['cursor']
            last_origin_idx = self.param['idx']['last_origin']

            time_axis_ticks = list(range(int(origin), int(cursor)+1)) \
                                + list(range(int(last_origin+1), int(origin)))
            for idx, tick in enumerate(time_axis_ticks):
                time_axis_ticks[idx] = (tick % window_size, tick)

        elif self.mode == "Scroll":
            origin = self.param['origin']
            cursor = self.param['cursor']

            origin_idx = self.param['idx']['origin']
            cursor_idx = self.param['idx']['cursor']

            time_axis_ticks = list(range(int(origin), int(cursor)+1))
            for idx, tick in enumerate(time_axis_ticks):
                time_axis_ticks[idx] = (tick - origin, tick)

        channel_axis_ticks = list()
        for idx, ch in enumerate(reversed(channels), start=1):
            #TODO change 10 to window height
            channel_axis_ticks.insert(0, (idx*10, "Channel {}".format(ch)))

        return dict(bottom=time_axis_ticks,left=channel_axis_ticks)

    def calculate_plot_data(self, time_data, channel_data, channels):
        """
        origin = 10
        cursor = 17.2
        last_origin = 7.299999999999999

        target_time_data = [10.1, 10.3, ... , 17.0, 17.2, 7.4, 7.5, ... , 9.5]
        ||
        \/
        target_time_data = [0.1 ,  0.3, ... ,  7.0,  7.2, 7.4, 7.5, ... , 9.5]

        target_channel_data =
        [
            [0.1, 0.3, ... , 0.7],
            [0.2, 0.6, ... , 0.8],
        ]
        ||
        \/
        target_channel_data =
        [
            [20.1, 20.3, ... , 20.7],
            [10.2, 10.6, ... , 10.8],
        ]
        """
        if self.mode == "Scan":
            origin_idx = self.param['idx']['origin']
            cursor_idx = self.param['idx']['cursor']
            last_origin_idx = self.param['idx']['last_origin']

            target_time_data = time_data[origin_idx:cursor_idx] \
                                + time_data[last_origin_idx:origin_idx]
            #TODO change 10 to window height
            target_time_data = [t % 10 for t in target_time_data]

            shifted_channel_data = list()
            for shifted, ch in enumerate(reversed(channels), start=1):
                channel_d = channel_data[ch-1][origin_idx:cursor_idx] \
                            + channel_data[ch-1][last_origin_idx:origin_idx]
                shifted_channel_data.insert(0,[x+ shifted*10 \
                                            for x in channel_d])

            self.time_data = target_time_data
            self.channel_data = shifted_channel_data

            self.trans_events[:] = [event for event in self.trans_events if (event['time'] >= self.param['last_origin'] and event['time'] <= self.param['cursor'])]

            for idx in range(len(self.trans_events)):
                tmp_time = self.trans_events[idx]['time']
                if tmp_time >= self.param['origin']:
                    self.trans_events[idx]['time'] -= self.param['origin']
                elif tmp_time < self.param['origin']:
                    self.trans_events[idx]['time'] += 10
                    self.trans_events[idx]['time'] -= self.param['origin']
    
        elif self.mode == "Scroll":
            origin = self.param['origin']

            origin_idx = self.param['idx']['origin']
            cursor_idx = self.param['idx']['cursor']

            target_time_data = time_data[origin_idx:cursor_idx+1]
            target_time_data = [t - origin for t in target_time_data]

            shifted_channel_data = list()
            for shifted, ch in enumerate(reversed(channels), start=1):
                channel_d = channel_data[ch-1][origin_idx:cursor_idx+1]
                shifted_channel_data.insert(0,[x+shifted*10 \
                                            for x in channel_d])

            self.time_data = target_time_data
            self.channel_data = shifted_channel_data

            self.trans_events[:] = [event for event in self.trans_events if (event['time'] >= self.param['origin'] and event['time'] <= self.param['cursor'])]
            for event in self.trans_events:
                event['time'] -= self.param['origin']          

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

        self.ws = websocket.WebSocketApp(url,
                                    on_message = self.on_message,
                                    on_error = self.on_error,
                                    on_close = self.on_close)
        self.ws_thread = threading.Thread(target=self.on_connect)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        self.events = list()
        for i in range(self.channel_num):
            self.decimated_data.append(list())
            self.transed_decimated_data.append(list())

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
        raw = json.loads(message)
        try:
            self.add_plot_decimated_data(raw)
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
        if len(data['data']['eeg']) != self.channel_num:
            raise AssertionError("The received raw data unmatch channel num")

        time = data['tick'] / self.raw_plot_sample_rate

        self.decimated_data_time.append(time)
        for idx, ori_data in enumerate(data['data']['eeg']):
            self.decimated_data[idx].append(ori_data)
            self.transed_decimated_data[idx].append(self._tranform_data(ori_data))

        if data['data']['event']:
            self.events.append({
                'tick': data['tick'],
                'time': time,
                'name': data['data']['event']['name'],
                'duration': data['data']['event']['duration']        
            })

    def get_plot_decimated_data(self, mode="Scan", channels=None, cursor=None):
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
        if cursor is None:
            raise AssertionError("Scan mode should provide `cursor`")

        if channels is None:
            channels = range(1, self.channel_num+1)

        data = Raw_Data_Plot_Data(self.decimated_data_time, self.transed_decimated_data, self.events,
                                    mode=mode, channels=channels,
                                    cursor=cursor)

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
