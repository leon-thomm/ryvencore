from PySide2.QtCore import QPointF, QObject, Signal
from PySide2.QtGui import QPainterPath

from .ConnectionItem import ExecConnectionItem, DataConnectionItem
from .InfoMsgs import InfoMsgs


class Connection(QObject):

    # activation_request = Signal(object)

    def __init__(self, params):
        super().__init__()

        self.out, self.inp, self.flow = params
        # self.item = None
        # self.activation_request.connect(self.flow.connection_activation_request)


    # def queue(self):
    #     self.activation_request.emit(self)

    def activate(self):
        pass



class ExecConnection(Connection):

    def activate(self):
        InfoMsgs.write('activating exec connection')
        self.inp.update()


class DataConnection(Connection):

    def get_val(self):
        InfoMsgs.write('getting value from data connection')
        return self.out.get_val()

    def activate(self, data=None):
        InfoMsgs.write('activating data connection')
        self.inp.update(data)
