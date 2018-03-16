import websocket
import json
import threading
import config

def on_message(ws, message):
    raw = json.loads(message)  
    for i in range(config.CH):
        config.rawList[i][config.currentIndex] = raw['data']['eeg'][i] + i * 10 
    
    if config.currentIndex < config.HZ * config.DURATION - 1:
        config.currentIndex += 1
    else:
        config.currentIndex = 0

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def connect():
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(config.WSURI,
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()