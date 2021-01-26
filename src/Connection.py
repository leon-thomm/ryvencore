from PySide2.QtCore import QPointF, QObject
from PySide2.QtGui import QPainterPath

from .ConnectionItem import ExecConnectionItem, DataConnectionItem


class Connection(QObject):
    def __init__(self, params):
        super().__init__()

        self.out, self.inp = params
        self.item = None


    def activate(self):
        pass



class ExecConnection(Connection):

    def activate(self):
        self.inp.update()


class DataConnection(Connection):

    def get_val(self):
        return self.out.get_val()

    def activate(self):
        self.inp.update()
