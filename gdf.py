import sys
import os
import os.path
import time
import struct
import logging
import errno
from itertools import chain

class GDF(object):
    def __init__(self, filename, ch_num, ch_label, sps):
        self.fout = open(filename, 'wb')
        self.ch_num = ch_num
        self.ch_label = ch_label
        self.sps = sps

        self.digi_max = 8388607
        self.digi_min = -8388608
        self.phys_max = 375000
        self.phys_min = -375000

        self.record_num = 0

        self.event_num = 0
        self.event_header = None
        self.event_pos_buffer = bytes()
        self.event_id_buffer = bytes()
        self.event_duration_buffer = bytes()
        
        self.fout.write(self.gen_header())
    
    def gen_header(self):
        gdf_time = round((time.time() / (3600 * 24) + 719529) * 2**32)
        
        lebals_bytes = bytes()
        for label in self.ch_label:
            lebals_bytes = lebals_bytes + struct.pack('=16s', str.encode(label))
        
        min_max = [self.phys_min]*self.ch_num + [self.phys_max]*self.ch_num + [self.digi_min]*self.ch_num + [self.digi_max]*self.ch_num

        header1 = struct.pack('=8s160xq60xq2iH2x', b'GDF 2.11', gdf_time, 0, 1, 1, self.ch_num)
        # number of record q(0) need to write back when closing file(start at 236th bytes, int64)
        header2 = bytes()
        header2 += lebals_bytes
        header2 += bytes.fromhex('20' * 80 * self.ch_num)
        for i in range(self.ch_num):
            header2 += struct.pack('=6s', b'uV')
        header2 += struct.pack('=%sH' % self.ch_num, *([4275]*self.ch_num))
        header2 += struct.pack('=%sd' % len(min_max), *min_max)
        header2 += bytes.fromhex('20' * 80 * self.ch_num)
        header2 += struct.pack('=%sI' % self.ch_num, *([self.sps]*self.ch_num))
        header2 += struct.pack('=%sI' % self.ch_num, *([279]*self.ch_num))
        header2 += bytes.fromhex('20' * 32 * self.ch_num)

        header3 = bytes()
        header3 += struct.pack('=B', 3)
        header3 += (13).to_bytes(3, byteorder=sys.byteorder)
        header3 += struct.pack('=%ss' % len('ArtiseBio-8CH'), b'ArtiseBio-8CH')
        header3 += struct.pack( '=%sx' % (256 - len(header3)) )

        return header1 + header2 + header3
    
    def convert_to_int24_bytes(self, data):
        scaler = (self.digi_max - self.digi_min) / (self.phys_max - self.phys_min)
        tmp = round(data * scaler)
        return (tmp).to_bytes(3, byteorder=sys.byteorder, signed=True)
    
    def writeSamples(self, samples):
        self.record_num += len(samples)
        contents = list(chain.from_iterable(samples))
        contents = [self.convert_to_int24_bytes(x) for x in contents]
        contents = b''.join(contents)
        self.fout.write(contents)

    def gen_event_header(self):
        event_mode = struct.pack('=B', 3) 
        event_num = (self.event_num).to_bytes(3, byteorder=sys.byteorder)
        event_sps = struct.pack('=f', self.sps)
        return event_mode + event_num + event_sps
    
    def writeEvent(self, first_tick, tick, duratoin, event_id):
        event_pos = struct.pack('=I', (tick - first_tick))
        event_id = struct.pack('=H', (event_id))
        event_duration = struct.pack('=I', (duratoin))

        self.event_pos_buffer += event_pos
        self.event_id_buffer += event_id
        self.event_duration_buffer += event_duration
        self.event_num += 1
    
    def close_and_save(self):
        self.event_header = self.gen_event_header()
        event_padding = struct.pack('=%sx' % (2 * self.event_num))

        self.fout.write(self.event_header)
        self.fout.write(self.event_pos_buffer)
        self.fout.write(self.event_id_buffer)
        self.fout.write(event_padding)
        self.fout.write(self.event_duration_buffer)

        # re-write number of record start at 236th byte, int64
        rn = struct.pack('=q', self.record_num)
        self.fout.seek(236)
        self.fout.write(rn)

        self.fout.close()
