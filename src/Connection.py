import math

from PySide2.QtCore import QRectF, QPointF
from PySide2.QtGui import QPainter, QColor, QRadialGradient, QPainterPath
from PySide2.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem

from .PortInstance import OutputPortInstance, InputPortInstance
from .global_tools.math import pythagoras


class Connection(QGraphicsItem):
    def __init__(self, params):
        super(Connection, self).__init__()

        self.out, self.inp, self.session_design = params
        self.path: QPainterPath = None
        self.gradient = None
        self.changed = False

        self.recompute()


    def activate(self):
        pass


    def boundingRect(self):
        op = self.out.pin.get_scene_center_pos()
        ip = self.inp.pin.get_scene_center_pos()
        top = min(0, (ip-self.pos()).y())
        left = min(0, (op-self.pos()).x())
        w = abs(ip.x()-op.x())
        h = abs(ip.y()-op.y())
        return QRectF(left, top, w, h)


    def recompute(self):
        self.setPos(self.out.pin.get_scene_center_pos())
        self.changed = True


    def connection_path(self, p1: QPointF, p2: QPointF):
        return default_cubic_connection_path(p1, p2)



class ExecConnBase(Connection):
    def activate(self):
        self.inp.update()


class DataConnBase(Connection):
    def get_val(self):
        return self.out.get_val()

    def activate(self):
        self.inp.update()



class ExecConnection(ExecConnBase):

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=...) -> None:

        pen = self.session_design.flow_theme.get_flow_conn_pen_inst(self.out.type_)
        c = pen.color()

        # highlight hovered connections
        if self.out.pin.hovered or self.inp.pin.hovered:
            c = QColor('#c5c5c5')
            pen.setWidth(5)

        if self.changed or not self.path:
            self.changed = False

            self.path = self.connection_path(self.out.pin.get_scene_center_pos() - self.scenePos(),
                                             self.inp.pin.get_scene_center_pos() - self.scenePos())

            w = self.path.boundingRect().width()
            h = self.path.boundingRect().height()
            self.gradient = QRadialGradient(self.path.boundingRect().center(),
                                            pythagoras(w, h) / 2)

            c_r = c.red()
            c_g = c.green()
            c_b = c.blue()
            self.gradient.setColorAt(0.0, QColor(c_r, c_g, c_b, 255))
            self.gradient.setColorAt(0.75, QColor(c_r, c_g, c_b, 200))
            self.gradient.setColorAt(0.95, QColor(c_r, c_g, c_b, 0))

        pen.setBrush(self.gradient)
        painter.setPen(pen)
        painter.drawPath(self.path)




class DataConnection(DataConnBase):

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=...) -> None:

        pen = self.session_design.flow_theme.get_flow_conn_pen_inst(self.out.type_)
        c = pen.color()

        # highlight hovered connections
        if self.out.pin.hovered or self.inp.pin.hovered:
            c = QColor('#c5c5c5')
            pen.setWidth(5)


        if self.changed or not self.path:
            self.changed = False

            self.path = self.connection_path(self.out.pin.get_scene_center_pos() - self.scenePos(),
                                             self.inp.pin.get_scene_center_pos() - self.scenePos())

            w = self.path.boundingRect().width()
            h = self.path.boundingRect().height()
            self.gradient = QRadialGradient(self.path.boundingRect().center(),
                                            pythagoras(w, h) / 2)

            c_r = c.red()
            c_g = c.green()
            c_b = c.blue()

            self.gradient.setColorAt(0.0, QColor(c_r, c_g, c_b, 255))
            self.gradient.setColorAt(0.75, QColor(c_r, c_g, c_b, 200))
            self.gradient.setColorAt(0.95, QColor(c_r, c_g, c_b, 0))
            self.gradient.setColorAt(1.0, QColor(c_r, c_g, c_b, 0))

        pen.setBrush(self.gradient)
        painter.setPen(pen)
        painter.drawPath(self.path)




def default_cubic_connection_path(p1: QPointF, p2: QPointF):
    """Returns the nice looking QPainterPath of a connection for two given points."""

    path = QPainterPath()

    path.moveTo(p1)

    distance_x = abs(p1.x()) - abs(p2.x())
    distance_y = abs(p1.y()) - abs(p2.y())

    if ((p1.x() < p2.x() - 30) or math.sqrt((distance_x ** 2) + (distance_y ** 2)) < 100) and (p1.x() < p2.x()):
        path.cubicTo(p1.x() + ((p2.x() - p1.x()) / 2), p1.y(),
                     p1.x() + ((p2.x() - p1.x()) / 2), p2.y(),
                     p2.x(), p2.y())
    elif p2.x() < p1.x() - 100 and abs(distance_x) / 2 > abs(distance_y):
        path.cubicTo(p1.x() + 100 + (p1.x() - p2.x()) / 10, p1.y(),
                     p1.x() + 100 + (p1.x() - p2.x()) / 10, p1.y() - (distance_y / 2),
                     p1.x() - (distance_x / 2), p1.y() - (distance_y / 2))
        path.cubicTo(p2.x() - 100 - (p1.x() - p2.x()) / 10, p2.y() + (distance_y / 2),
                     p2.x() - 100 - (p1.x() - p2.x()) / 10, p2.y(),
                     p2.x(), p2.y())
    else:
        path.cubicTo(p1.x() + 100 + (p1.x() - p2.x()) / 3, p1.y(),
                     p2.x() - 100 - (p1.x() - p2.x()) / 3, p2.y(),
                     p2.x(), p2.y())
    return path