
__author__ = "kirintw and Billy Su"
__license__ = "GPL-2.0"

import websocket
import json
import threading

RAW = 0
DEC = 0
FFT = 0

fakeBuffer0 = list()
fakeBuffer1 = list()
fakeBuffer2 = list()

def on_message(ws, message):
    global RAW, DEC, FFT, fakeBuffer0, fakeBuffer1, fakeBuffer2
    raw = json.loads(message)
    msgName = raw['name']
    if msgName == 'raw':
        RAW += 1
        fakeBuffer0.append(raw['data']['eeg'])
        fakeBuffer0.pop(0)
    elif msgName == 'dec':
        DEC += 1
        fakeBuffer1.append(raw['data']['eeg'])
        fakeBuffer1.pop(0)
    elif msgName == 'fft':
        FFT += 1
        fakeBuffer2.append(raw['data'])
        fakeBuffer2.pop(0)


def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def connect():
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp('ws://localhost:9999/',
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

def setInterval(func,time):
    e = threading.Event()
    while not e.wait(time):
        func()

def printMsgCount():
    global RAW, DEC, FFT
    print ('raw', RAW)
    print ('dec', DEC)
    print ('fft', FFT)
    RAW = 0
    DEC = 0
    FFT = 0

connect()
setInterval(printMsgCount, 1)
