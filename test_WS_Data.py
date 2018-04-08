import unittest
import logging

import numpy as np

from ui import Raw_Data_Plot_Data

class TestHelperFunc(unittest.TestCase):
    def test_cal_mode_param(self):
        cursor = 17.2
        time_data = list(np.linspace(5, 31, num=500))
        channels = [1, 2, 4, 7, 8]
        channel_data = list()
        for i in range(8):
            channel_data.append(list(np.random.normal(size=500)))

        ### Test Scan mode param
        plot_data = Raw_Data_Plot_Data(time_data, channel_data, mode="Scan",
                                        channels=channels, cursor=cursor)
        param = plot_data.param
        self.assertEqual(param["origin"], 10.)
        self.assertEqual(param["last_origin"], (cursor- 10 + 0.1))

        origin_idx = param["idx"]["origin"]
        cursor_idx = param["idx"]["cursor"]
        last_origin_idx = param["idx"]["last_origin"]

        self.assertGreaterEqual(time_data[origin_idx], param["origin"])
        self.assertLess(time_data[origin_idx-1], param["origin"])

        self.assertLessEqual(time_data[cursor_idx], cursor)
        self.assertGreater(time_data[cursor_idx+1], cursor)

        self.assertGreater(time_data[last_origin_idx], param["last_origin"])
        self.assertLessEqual(time_data[last_origin_idx-1], param["last_origin"])

        ### Test Scroll mode param
        plot_data = Raw_Data_Plot_Data(time_data, channel_data, mode="Scroll",
                                        channels=channels, cursor=cursor)

        param = plot_data.param
        self.assertEqual(param["origin"], 7)

        origin_idx = param["idx"]["origin"]
        cursor_idx = param["idx"]["cursor"]

        self.assertGreaterEqual(time_data[origin_idx], 7)
        self.assertLess(time_data[origin_idx-1], 7)

        self.assertLessEqual(time_data[cursor_idx], cursor)
        self.assertGreater(time_data[cursor_idx+1], cursor)

    def test_Raw_Data_Plot_Data(self):
        cursor = 17.2
        time_data = list(np.linspace(5, 31, num=500))
        channels = [1, 2, 4, 7, 8]
        channel_data = list()
        for i in range(8):
            channel_data.append(list(np.random.normal(size=500)))

        """
        Test for Scan mode
        """
        plot_data = Raw_Data_Plot_Data(time_data, channel_data, mode="Scan",
                            channels=channels, window_size=10, cursor=cursor)

        param = plot_data.param
        axises_tick = plot_data.axises_tick

        origin_idx = param["idx"]["origin"]
        cursor_idx = param["idx"]["cursor"]
        last_origin_idx = param["idx"]["last_origin"]
        ### check bottom axis
        bottom_axis = [(0, 10), (1, 11), (2, 12), (3,13), (4, 14), (5, 15),
                        (6, 16), (7, 17), (8, 8), (9, 9)]
        for ground, gen in zip(bottom_axis, axises_tick["bottom"]):
            self.assertEqual(ground, gen)

        ### check left axis
        left_axis = [(50, "Channel 1"), (40, "Channel 2"), (30, "Channel 4"),
                        (20, "Channel 7"), (10, "Channel 8")]
        for ground, gen in zip(left_axis, axises_tick["left"]):
            self.assertEqual(ground, gen)

        ### check time_data
        time_data_gen = plot_data.time_data
        target_time_data = time_data[origin_idx:cursor_idx] \
                            + time_data[last_origin_idx:origin_idx]
        logging.debug("origin cursor last_origin last")
        logging.debug("{} {} {} {}".format(time_data[origin_idx],
                                            time_data[cursor_idx],
                                            time_data[last_origin_idx],
                                            time_data[origin_idx-1]))
        #TODO change 10 to window size
        target_time_data = [t % 10 for t in target_time_data]
        logging.debug("origin last")
        logging.debug("{} {}".format(target_time_data[0],
                                    target_time_data[-1]))
        for ground, gen in zip(target_time_data, time_data_gen):
            self.assertEqual(ground, gen)

        ### check channel_data
        channels_data_gen = plot_data.channel_data
        target_channel_data = [channel_data[i-1] for i in channels]
        for idx, ch_d in enumerate(target_channel_data):
            target_channel_data[idx] = ch_d[origin_idx:cursor_idx] \
                                    + ch_d[last_origin_idx:origin_idx]
        shifted_w = range(50, 0, -10)
        for sh, (idx, ch_d) in zip(shifted_w, enumerate(target_channel_data)):
            target_channel_data[idx] = [v+sh for v in ch_d]

            logging.debug("Before shift")
            logging.debug("origin: {},last: {}".format(ch_d[0],ch_d[-1]))
            logging.debug("After shift")
            logging.debug("origin: {},last: {}".format(
                target_channel_data[idx][0],target_channel_data[idx][-1]))

        for ground, gen in zip(target_channel_data, channels_data_gen):
            for gr, ge in zip(ground, gen):
                self.assertEqual(gr,ge)

        """
        Test for Scan mode
        """
        plot_data = Raw_Data_Plot_Data(time_data, channel_data, mode="Scroll",
                                        channels=channels, cursor=cursor)
        param = plot_data.param
        axises_tick = plot_data.axises_tick

        origin = param["origin"]
        origin_idx = param["idx"]["origin"]
        cursor_idx = param["idx"]["cursor"]
        ### Test bottom axis
        bottom_axis = [(0, 7), (1, 8), (2, 9), (3, 10), (4, 11), (5, 12),
                        (6, 13), (7, 14), (8, 15), (9, 16), (10, 17)]
        for ground, gen in zip(bottom_axis, axises_tick["bottom"]):
            self.assertEqual(ground, gen)

        ### Test time data
        target_time_data = time_data[origin_idx:cursor_idx+1]
        logging.debug("origin: {}, cursor: {}".format(origin, cursor))
        logging.debug("origin cursor(last)")
        logging.debug("{} {}".format(target_time_data[0],
                                        target_time_data[-1]))

        target_time_data = [t-origin for t in target_time_data]
        logging.debug("origin cursor(last)")
        logging.debug("{} {}".format(target_time_data[0],
                                        target_time_data[-1]))

        for ground, gen in zip(target_time_data, plot_data.time_data):
            self.assertEqual(ground, gen)

        ### Test channel data
        channels_data_gen = plot_data.channel_data
        target_channel_data = [channel_data[ch-1] for ch in channels]
        for idx, ch_d in enumerate(target_channel_data):
            target_channel_data[idx] = ch_d[origin_idx:cursor_idx]

        shifted_w = range(50, 0, -10)
        for sh, (idx, ch_d) in zip(shifted_w, enumerate(target_channel_data)):
            target_channel_data[idx] = [v+sh for v in ch_d]

        for ground, gen in zip(target_channel_data, channels_data_gen):
            for gr, ge in zip(ground, gen):
                self.assertEqual(gr,ge)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()