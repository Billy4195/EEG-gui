import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import ui
import numpy as np
import time
import config
import wsSetup
config.init()
wsSetup.connect() 

app = ui.EEG_Application()
cursor = pg.InfiniteLine(pos=0)
app.plot.addItem(cursor)

curves = list()

for i in range(64):
    r = (i + 60 ) * 5 % 256
    g = (i + 2 ) * 7 % 256
    b = (i + 15 ) * 11 % 256
    curve = app.plot.plot(pen=(r,g,b))
    curve.setData(config.rawList[i])
    curves.append(curve)
    app.plot.resize(5,100)

def update():
    global curves, plot, win
    tol_start = time.time()
    for i in range(64):
        start = time.time()
        curves[i].setData(config.rawList[i])
        end = time.time()
    app.plot.setTitle("FPS: {:.1f}".format(1/(time.time()-tol_start)))
    cursor.setValue(config.currentIndex)

timer = QtCore.QTimer()
timer.setInterval(100)
timer.timeout.connect(update)
timer.start()



app.exec_()