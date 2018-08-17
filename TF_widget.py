import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter
from matplotlib.colorbar import ColorbarBase

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class ColorBar(pg.GraphicsObject):
    """
    Ref: https://gist.github.com/maedoc/b61090021d2a5161c5b9
    """
    def __init__(self, cmap, width, height, ticks=None, tick_labels=None, label=None, norm=None):
        pg.GraphicsObject.__init__(self)
        self.norm = norm

        # handle args
        label = label or ''
        w, h = width, height
        stops, colors = cmap.getStops('float')
        smn, spp = stops.min(), stops.ptp()
        stops = (stops - stops.min())/stops.ptp()
        if ticks is None:
            ticks = np.r_[0.0:1.0:5j, 1.0] * spp + smn

        if self.norm:
            ticks = self.norm(ticks)

        if tick_labels is None:
            tick_labels =  ["{:2.2f}".format(t) for t in self.norm.inverse(ticks)]

        # setup picture
        self.pic = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.pic)

        # draw bar with gradient following colormap
        p.setPen(pg.mkPen('k'))
        grad = pg.QtGui.QLinearGradient(w/2.0, 0.0, w/2.0, h*1.0)
        for stop, color in zip(stops, colors):
            grad.setColorAt(1.0 - stop, pg.QtGui.QColor(*color))
        p.setBrush(pg.QtGui.QBrush(grad))
        p.drawRect(pg.QtCore.QRectF(0, 0, w, h))

        # draw ticks & tick labels
        mintx = 0.0
        for tick, tick_label in zip(ticks, tick_labels):
            y_ = (1.0 - (tick - smn)/spp) * h
            p.drawLine(0.0, y_, -5.0, y_)
            br = p.boundingRect(0, 0, 0, 0, pg.QtCore.Qt.AlignRight, tick_label)
            if br.x() < mintx:
                mintx = br.x()
            p.drawText(br.x() - 10.0, y_ + br.height() / 4.0, tick_label)

        # draw label
        br = p.boundingRect(0, 0, 0, 0, pg.QtCore.Qt.AlignRight, label)
        p.drawText(-br.width() / 2.0, h + br.height() + 5.0, label)

        # done
        p.end()

        # compute rect bounds for underlying mask
        self.zone = mintx - 12.0, -15.0, br.width() - mintx + w + 20, h + br.height() + 30.0

    def paint(self, p, *args):
        # paint underlying mask
        p.setPen(pg.QtGui.QColor(255, 255, 255, 0))
        p.setBrush(pg.QtGui.QColor(255, 255, 255, 200))
        p.drawRoundedRect(*(self.zone + (9.0, 9.0)))

        # paint colorbar
        p.drawPicture(0, 0, self.pic)

    def boundingRect(self):
        return pg.QtCore.QRectF(self.pic.boundingRect())


class SpectrogramWidget(QtGui.QWidget):
    def __init__(self, freq_limit, time_scale, freq_labels):
        super().__init__()

        self.img = pg.ImageItem()

        self.img_array = None
        self.tick_array = None
        self.init_tick = None
        self.min_freq, self.max_freq = freq_limit
        self.time_scale = time_scale
        self.freq_labels = freq_labels

        pos = np.array([0., 0.5, 1.])
        color = np.array([[0,0,255,255], [0,255,0,255], [255,0,0,255]], dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        norm = mpl.colors.Normalize(-200, 500)

        # set colormap
        self.img.setLookupTable(lut)
        self.img.setLevels([-200, 500])

        self.cb = ColorBar(cmap, 10, 100, ticks=[-200, 0, 200, 500], norm=norm)
        #Move colorbar position
        self.cb.setPos(620, 50)

        self.plot = pg.PlotWidget()
        self.plot.addItem(self.img)
        self.plot.scene().addItem(self.cb)

        hlayout = QtGui.QHBoxLayout(self)
        hlayout.addWidget(self.plot)
        self.show()

    def draw(self, new_tick_data, tick, show):
        tick /= 1000
        tick = tick

        if self.img_array is None:
            self.img_array = np.array([new_tick_data]).T
            self.tick_array = [tick]
            self.init_tick = tick
        else:
            self.img_array = np.append(self.img_array, np.array([new_tick_data]).T, axis=1)
            self.tick_array.append(tick)

        while self.tick_array[0] <= self.tick_array[-1] - self.time_scale:
            self.img_array = self.img_array[:, 1:]
            self.tick_array.pop(0)

        if show:
            self.update()

    def update(self):
        img = self.img_array
        self.img.setImage(self.img_array.T, autoLevels=False)
        axis = self.plot.getAxis("bottom")

        labels = list()
        for idx, tick in enumerate(self.tick_array):
            if len(self.tick_array) < 10:
                labels.append( (idx+0.5, "{:5.2f}".format(tick)) )
            else:
                if (idx % 10 == 0 and len(self.tick_array) - idx > 8) or self.tick_array[-1] == tick:
                    labels.append( (idx+0.5, "{:5.2f}".format(tick)) )

        axis.setTicks([labels])

        for idx, label in enumerate(self.freq_labels):
            if label <= self.min_freq:
                min_limit = idx

            if label >= self.max_freq:
                max_limit = idx
                break

        self.plot.setLimits(xMin=0,
                            xMax=len(self.tick_array),
                            yMin=min_limit-0.5,
                            yMax=max_limit+0.5)
        axis = self.plot.getAxis("left")

        y_labels = [(i, str(self.freq_labels[int(i)])) for i in range(0, len(self.freq_labels), 5)]
        axis.setTicks([y_labels])

        # y_labels = [self.freq_labels[int(i)] for i in y_ticks]
        # self.ax.set_yticklabels(y_labels)

    def set_freq_limit(self, freq_limit):
        self.min_freq, self.max_freq = freq_limit

    def resizeEvent(self, event):
        if self.cb:
            self.cb.setPos(self.size().width() - 45 , 50.0)