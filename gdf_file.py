import os
import os.path
import logging
import errno
from gdf import GDF

class GDF_FILE(object):
    def __init__(self, filepath, ws_client):
        self.filepath = filepath
        self.ws_client = ws_client
        self.filepath = filepath
        self.ws_client = ws_client
        self.raw_sample_rate = self.ws_client.raw_sample_rate
        self.ch_num = self.ws_client.ch_num
        self.ch_label = self.ws_client.ch_label
        self.raw_cache_size = 1000
        self.record_start_tick = None

        self.open_raw_record_file()
    
    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def open_raw_record_file(self):
        self.ws_client.raw_data.clear()
        self.ws_client.raw_data_ticks.clear()
        self.ws_client.raw_data_events.clear()

        self.mkdir_p(os.path.dirname(self.filepath))
        self.target_file = GDF(filename=self.filepath, ch_num=self.ch_num, ch_label=self.ch_label, sps=self.raw_sample_rate)
    
    def close_raw_record_file(self):
        while self.ws_client.raw_data:
            self.write_raw_data_to_file()

        self.ws_client.raw_data.clear()
        self.ws_client.raw_data_ticks.clear()
        self.ws_client.raw_data_events.clear()

        self.target_file.close_and_save()
        self.target_file = None
    
    def write_raw_data_to_file(self):
        if self.target_file is not None:
            if self.record_start_tick is None:
                self.record_start_tick = self.ws_client.raw_data_ticks[0]

            copied_data = self.ws_client.raw_data[:self.raw_cache_size]
            self.ws_client.raw_data = self.ws_client.raw_data[self.raw_cache_size:]

            copied_ticks = self.ws_client.raw_data_ticks[:self.raw_cache_size]
            self.ws_client.raw_data_ticks = self.ws_client.raw_data_ticks[self.raw_cache_size:]

            copied_events = self.ws_client.raw_data_events[:self.raw_cache_size]
            self.ws_client.raw_data_events = self.ws_client.raw_data_events[self.raw_cache_size:]

            assert len(copied_data) == len(copied_ticks)
            assert len(copied_data) == len(copied_events)
            
            self.target_file.writeSamples(copied_data)

            for tick, events in zip(copied_ticks, copied_events):              
                for event_id, event_duration in zip(events["event_id"], events["event_duration"]):
                    ed = None
                    if event_duration is None:
                        ed = 0
                    else:
                        ed = round(event_duration * self.raw_sample_rate)
                    self.target_file.writeEvent(first_tick=self.record_start_tick, tick=tick, duratoin=ed, event_id=event_id)    