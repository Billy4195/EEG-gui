import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import ui
import numpy as np
import time

app = ui.EEG_Application()
cursor = pg.InfiniteLine(pos=0)
app.plot.addItem(cursor)
cursor_index = 0
data_list = list()
curves = list()
for i in range(64):
    data = list(np.random.normal(size=[2500])+i*10)
    r = (i + 60 ) * 5 % 256
    g = (i + 2 ) * 7 % 256
    b = (i + 15 ) * 11 % 256
    curve = app.plot.plot(pen=(r,g,b))
    curve.setData(data)
    curves.append(curve)
    data_list.append(data)
    app.plot.resize(5,100)

def update():
    global curves, plot, data, win, cursor_index
    tol_start = time.time()
    for i in range(64):
        data_list[i] += list(np.random.normal(size=[25])+i*10)
        data_list[i] = data_list[i][25:]
        start = time.time()
        curves[i].setData(data_list[i])
        end = time.time()
    app.plot.setTitle("FPS: {:.1f}".format(1/(time.time()-tol_start)))
    cursor_index = (cursor_index+25)%2500
    cursor.setValue(cursor_index)

timer = QtCore.QTimer()
timer.setInterval(100)
timer.timeout.connect(update)
timer.start()



app.exec_()