import copy

class Raw_Data_Plot_Data(object):
    """
    1.
        cursor = 17.6
        plot_origin = 5.2

        Scan:
        origin = 5 -> 15
        (1, 16), (2, 17), (3, 8), (4, 9), (5, 10), (6, 11), (7, 12), (8, 13), (9, 14), (10, 15)

        Scroll:
        origin = 7.6
        (0.4, 8), (1.4, 9), (2.4, 10), (3.4, 11), (4.4, 12), (5.4, 13), (6.4, 14), (7.4, 15), (8.4, 16), (9.4, 17)

    2.
        cursor = 17.6
        plot_origin = 15.2

        Scan:
        origin = 15 -> 25
        (1, 16), (2, 17), (3, 18), (4, 19), (5, 20), (6, 21), (7, 22), (8, 23), (9,24), (10, 25)

        Scroll:
        origin = 15.2
        (0.8, 16), (1.8, 17)

    """
    def __init__(self, time_data, channel_data, events, mode, channels, cursor,
                    window_size=10, plot_origin=None):
        self.trans_events = copy.deepcopy(events)
        self.set_mode(mode)
        self.param = self.cal_mode_param(time_data, cursor, window_size, plot_origin)
        self.axises_tick = self.calculate_axises_tick(time_data, channels,
                                                    window_size, plot_origin)
        self.calculate_plot_data(time_data, channel_data, channels, plot_origin)

    def set_mode(self, mode):
        if mode not in ["Scan", "Scroll"]:
            raise NotImplementedError("{} mode has not be implemented".format(
                mode))
        else:
            self.mode = mode

    def cal_mode_param(self, time_data, cursor, window_size=10, plot_origin=None):
        """
        According to the mode, calculating index of important point in
        time_data, and return the important parameter
        """
        if self.mode == "Scan":
            return self.cal_scan_mode_param(time_data, cursor, window_size, plot_origin)

        elif self.mode == "Scroll":
            return self.cal_scroll_mode_param(time_data, cursor, window_size, plot_origin)

    def cal_scan_mode_param(self, time_data, cursor, window_size, plot_origin):
        """
        ##Scan Mode##
        if
            cursor = 17.2, window_size = 10, plot_origin = 5.2
        then
            origin = 15 { (int(plot_origin) + n*window_size) < cursor }
            last_origin = 7.20999 { (cursor-windows_size) }

        if
            cursor = 17.2, window_size = 10, plot_origin = 15.2
        then
            origin = 15 { (int(plot_origin) + n*window_size) < cursor}
            last_origin = None

        origin_idx: min(time_data >= origin)
        cursor_idx: max(time_data <= cursor)
        last_origin_idx: None or min(time_data > last_origin)

        Return:
        {
            "origin": 10,
            "cursor": 17.2,
            "last_origin": 7.209999999999999,
            "idx": {
                "origin": ``origin_idx``,
                "cursor": ``cursor_idx``,
                "last_origin": ``last_origin_idx``
            }
        }
        """
        origin = int(plot_origin)
        while origin <= cursor:
            origin += window_size
        origin -= window_size

        last_origin = cursor - window_size
        if last_origin < plot_origin:
            last_origin = None

        origin_idx = None
        cursor_idx = 0
        last_origin_idx = None
        for idx, time_stamp in enumerate(time_data):
            if origin_idx is None and time_stamp >= origin:
                origin_idx = idx
            if time_stamp <= cursor:
                cursor_idx = idx

            if last_origin is not None and \
                    last_origin_idx is None and \
                    time_stamp > last_origin:
                last_origin_idx = idx
            if time_stamp > cursor:
                break

        if origin_idx is None:
            origin_idx = 0

        return dict(origin=origin, cursor=cursor, last_origin=last_origin,
                    idx=dict(
                        origin=origin_idx,cursor=cursor_idx,
                        last_origin=last_origin_idx)
                )

    def cal_scroll_mode_param(self, time_data, cursor, window_size, plot_origin):
        """
        if
            cursor = 17.2, window_size = 10, plot_origin = 5.2
        then
            origin = 7.20999 { (cursor - window_size)+0.01 }

        if
            cursor = 17.2, window_size = 10, plot_origin = 15.2
        then
            origin = 15.2 { int(plot_origin) }

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
        origin = cursor - window_size + 0.01
        if origin < plot_origin:
            origin = plot_origin

        origin_idx = None
        cursor_idx = 0
        for idx, time_stamp in enumerate(time_data):
            if origin_idx is None and time_stamp >= origin:
                origin_idx = idx
            if time_stamp <= cursor:
                cursor_idx = idx
            if time_stamp > cursor:
                break

        if origin_idx is None:
            origin_idx = 0

        return dict(origin=origin, cursor=cursor,
                    idx=dict(origin=origin_idx,cursor=cursor_idx)
                )

    def calculate_axises_tick(self, time_data, channels, window_size, plot_origin):
        """
        ## Scan mode
        if
            cursor = 17.2
            plot_origin = 5.2

            origin = 15
            cursor = 17.2
            last_origin = 7.209999999999999
        then
            time_axis_ticks = [15, 16, 17, 8, 9, 10, 11, 12, 13, 14, 15]
            ||
            \/
            time_axis_ticks = [(0, 15), (1, 16), ... , (10, 15)]

        if
            cursor = 17.2
            plot_origin = 15.2

            origin = 15
            cursor = 17.2
            last_origin = None
        then
            time_axis_ticks = [15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
            ||
            \/
            time_axis_ticks = [(0, 15), (1, 16), ... , (10, 25)]

        ## Scroll mode
        if
            cursor = 17.2
            origin = 7.209999
            plot_origin = 5.2
        then
            time_axis_ticks = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
            ||
            \/
            time_axis_ticks = [(0.79, 8), (1.79, 9), ... , (9.79, 17)]

        if
            cursor = 17.2
            origin = 15.2
            plot_origin = 15.2
        then
            time_axis_ticks = [16, 17]
            ||
            \/
            time_axis_ticks = [(0.8, 16), (1.8, 17)]

        channels = [1, 5, 7 ,9]
        channel_axis_ticks = [(40, 'Channel 1'), (30, 'Channel 5'), ... ]
        """
        if self.mode == "Scan":
            origin = self.param['origin']
            cursor = self.param['cursor']
            last_origin = self.param['last_origin']

            if last_origin is not None:
                time_axis_ticks = list( range(int(origin), int(cursor)+1) )
                time_axis_ticks += list( range(int(last_origin)+1, int(origin)+1) )

                for idx, tick in enumerate(time_axis_ticks):
                    if tick >= origin:
                        time_axis_ticks[idx] = (tick - origin, tick)
                    else:
                        time_axis_ticks[idx] = (tick + 10 - origin, tick)
            else:
                time_axis_ticks = list( range(int(origin), int(origin)+11))

                for idx, tick in enumerate(time_axis_ticks):
                    time_axis_ticks[idx] = (tick - origin, tick)

        elif self.mode == "Scroll":
            origin = self.param['origin']
            cursor = self.param['cursor']

            time_axis_ticks = list(range(int(origin)+1, int(cursor)+1))
            for idx, tick in enumerate(time_axis_ticks):
                time_axis_ticks[idx] = (tick - origin, tick)

        channel_axis_ticks = list()
        for idx, ch in enumerate(reversed(channels), start=1):
            #TODO change 10 to window height
            channel_axis_ticks.insert(0, (idx*10, "Channel {}".format(ch)))

        return dict(bottom=time_axis_ticks,left=channel_axis_ticks)

    def calculate_plot_data(self, time_data, channel_data, channels, plot_origin):
        """
        ## Scan mode
        if
            cursor = 17.2
            plot_origin = 5.2

            origin = 15
            cursor = 17.2
            last_origin = 7.209999999999999
        then
            target_time_data = [15.1, 15.3, ... , 22.0, 22.2, 22.4, 12.5, ... , 14.5]
            ||
            \/
            target_time_data = [0.1 ,  0.3, ... ,  7.0,  7.2, 7.4, 7.5, ... , 9.5]

        if
            cursor = 17.2
            plot_origin = 15.2

            origin = 15
            cursor = 17.2
            last_origin = None
        then
            target_time_data = [15.1, 15.3, ... , 16.9, 17.0, 17.1, 17.2]
            ||
            \/
            target_time_data = [0.1 ,  0.3, ... , 1.9,  2.0,  2.1,   2.2]

        ## Scroll mode
        if
            cursor = 17.2
            origin = 7.209999
            plot_origin = 5.2
        then
            target_time_data = [7.3, 7.4, ... ,   16.8, 16.9, 17.2]
            ||
            \/
            target_time_data = [0.09, 0.19, ... , 9.59, 9.69,  10]

        if
            cursor = 17.2
            origin = 15.2
            plot_origin = 15.2
        then
            target_time_data = [15.2, 15.6, ... , 16.8, 17.2]
            ||
            \/
            target_time_data = [0,    0.4, ...  , 1.6, 2.0]

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
            origin = self.param['origin']

            origin_idx = self.param['idx']['origin']
            cursor_idx = self.param['idx']['cursor']
            last_origin_idx = self.param['idx']['last_origin']

            shifted_channel_data = list()
            if last_origin_idx is not None:
                target_time_data = time_data[origin_idx:cursor_idx] \
                                    + time_data[last_origin_idx:origin_idx]
                for idx, time_stamp in enumerate(target_time_data):
                    if time_stamp >= origin:
                        target_time_data[idx] = time_stamp - origin
                    else:
                        target_time_data[idx] = time_stamp + 10 - origin

                for shifted, ch in enumerate(reversed(channels), start=1):
                    channel_d = channel_data[ch-1][origin_idx:cursor_idx] \
                                + channel_data[ch-1][last_origin_idx:origin_idx]
                    shifted_channel_data.insert(0,[x+ shifted*10 \
                                                for x in channel_d])

                self.trans_events[:] = [event for event in self.trans_events
                                        if (event['time'] >= self.param['last_origin'] and \
                                        event['time'] <= self.param['cursor'])]

            else:
                target_time_data = time_data[origin_idx:cursor_idx]
                target_time_data = [t - origin for t in target_time_data]

                for shifted, ch in enumerate(reversed(channels), start=1):
                    channel_d = channel_data[ch-1][origin_idx:cursor_idx]
                    shifted_channel_data.insert(0,[x+ shifted*10 \
                                                for x in channel_d])

                self.trans_events[:] = [event for event in self.trans_events
                                        if (event['time'] >= origin and \
                                        event['time'] <= self.param['cursor'])]

            self.time_data = target_time_data
            self.channel_data = shifted_channel_data

            for idx in range(len(self.trans_events)):
                tmp_time = self.trans_events[idx]['time']
                if tmp_time >= origin:
                    self.trans_events[idx]['time'] -= origin
                elif tmp_time < origin:
                    self.trans_events[idx]['time'] += 10
                    self.trans_events[idx]['time'] -= origin
    
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

            self.trans_events[:] = [event for event in self.trans_events if (event['time'] >= origin and event['time'] <= self.param['cursor'])]
            for event in self.trans_events:
                event['time'] -= origin

        self.cursor = self.param['cursor'] - origin
