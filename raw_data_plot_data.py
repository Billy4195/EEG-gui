import copy

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