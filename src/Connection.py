from PySide2.QtCore import QPointF, QObject
from PySide2.QtGui import QPainterPath

from .ConnectionItem import ExecConnectionItem, DataConnectionItem


class Connection(QObject):
    def __init__(self, params):
        super().__init__()

        self.out, self.inp, _ = params
        self.item = None


    def activate(self):
        pass



class ExecConnection(Connection):
    def __init__(self, params: tuple):
        super().__init__(params)

        _, _, session_design = params
        self.item = ExecConnectionItem(
            out_item=self.out.item,
            inp_item=self.inp.item,
            type_=self.inp.type_,
            session_design=session_design)

    def activate(self):
        self.inp.update()


class DataConnection(Connection):
    def __init__(self, params):
        super().__init__(params)

        _, _, session_design = params
        self.item = DataConnectionItem(
            out_item=self.out.item,
            inp_item=self.inp.item,
            type_=self.inp.type_,
            session_design=session_design)

    def get_val(self):
        return self.out.get_val()

    def activate(self):
        self.inp.update()
