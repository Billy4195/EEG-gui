import os
import os.path
import logging
import errno
import pyedflib
from numpy  import array

class EDF_FILE(object):
    def __init__(self, filepath, ws_client):
        self.filepath = filepath
        self.ws_client = ws_client
        self.raw_sample_rate = self.ws_client.raw_sample_rate
        self.ch_num = self.ws_client.ch_num
        self.ch_label = self.ws_client.ch_label
        self.raw_cache_size = 1000
        self.record_start_tick = None

        self.open_raw_record_file(self.filepath)

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def open_raw_record_file(self, filename):
        self.ws_client.raw_data.clear()
        self.ws_client.raw_data_ticks.clear()
        self.ws_client.raw_data_events.clear()

        self.mkdir_p(os.path.dirname(filename))
        self.target_file = pyedflib.EdfWriter(filename, self.ch_num, file_type=pyedflib.FILETYPE_EDFPLUS)
        self.target_file.equipment = 'ArtiseBio-8CH'

        self.channel_info = list()

        for label in self.ch_label:
            ch_dict = {
                'label': label,
                'dimension': 'uV',
                'sample_rate': self.raw_sample_rate,
                'physical_max': 100,
                'physical_min': -100,
                'digital_max': 32767,
                'digital_min': -32768,
                'transducer': '',
                'prefilter':''
            }
            self.channel_info.append(ch_dict)
        
        self.target_file.setSignalHeaders(self.channel_info)
    
    def close_raw_record_file(self):
        while self.ws_client.raw_data:
            self.write_raw_data_to_file()

        self.ws_client.raw_data.clear()
        self.ws_client.raw_data_ticks.clear()
        self.ws_client.raw_data_events.clear()

        self.target_file.close()
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

            transpose_data = list(map(list, zip(*copied_data)))
            transpose_data = array( transpose_data )
            
            self.target_file.writeSamples(transpose_data)

            for tick, events in zip(copied_ticks, copied_events):              
                time = (tick - self.record_start_tick) / self.raw_sample_rate
                for event_id, event_duration in zip(events["event_id"], events["event_duration"]):
                    if event_duration is None:
                        ed = -1
                    else:
                        ed = event_duration
                    self.target_file.writeAnnotation(time, ed, str(event_id))
