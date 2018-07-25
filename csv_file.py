import os
import os.path
import logging
import csv
import errno


class CSV_FILE(object):
    def __init__(self, filepath, ws_client):
        self.filepath = filepath
        self.ws_client = ws_client
        self.record_start_tick = None
        self.raw_sample_rate = self.ws_client.raw_sample_rate
        self.ch_num = self.ws_client.ch_num
        self.ch_label = self.ws_client.ch_label
        self.raw_cache_size = 1000

        self.open_raw_record_file(self.filepath)

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

        self.ws_client.raw_data.clear()
        self.ws_client.raw_data_ticks.clear()
        self.ws_client.raw_data_events.clear()

        first_row = list()
        first_row.append("Time:{}Hz".format(self.raw_sample_rate))
        first_row.append("Epoch")
        # TODO chagne to channel name
        for label in self.ch_label:
            first_row.append(label)
        first_row.append("Event ID")
        first_row.append("Event Date")
        first_row.append("Event Duration")
        self.csv_writer.writerow(first_row)

    def close_raw_record_file(self):
        while self.ws_client.raw_data:
            self.write_raw_data_to_file()

        self.ws_client.raw_data.clear()
        self.ws_client.raw_data_ticks.clear()
        self.ws_client.raw_data_events.clear()

        self.file_pointer.close()
        self.file_pointer = None
        self.csv_writer = None

    def write_raw_data_to_file(self):
        if self.csv_writer is not None:
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
