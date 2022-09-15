from .Base import Base

from .RC import PortObjPos, FlowAlg
from .dtypes import DType
from .utils import serialize
from .InfoMsgs import InfoMsgs


class NodePort(Base):
    """Base class for inputs and outputs of nodes"""

    def __init__(self, node, io_pos, type_, label_str):
        Base.__init__(self)

        self.node = node
        self.io_pos = io_pos
        self.type_ = type_
        self.label_str = label_str

    def data(self) -> dict:
        return {
            'type': self.type_,
            'label': self.label_str,
            'GID': self.GLOBAL_ID,
        }


class NodeInput(NodePort):

    def __init__(self, node, type_, label_str='', add_data=None, dtype: DType = None):
        super().__init__(node, PortObjPos.INPUT, type_, label_str)

        # data can be used to store additional data for enhanced data input ports
        self.add_data = add_data

        # optional dtype
        self.dtype: DType = dtype

    def data(self) -> dict:
        data = super().data()

        if self.dtype:
            data['dtype'] = str(self.dtype)
            data['dtype state'] = serialize(self.dtype.get_state())

        return data



class NodeOutput(NodePort):
    def __init__(self, node, type_, label_str=''):
        super().__init__(node, PortObjPos.OUTPUT, type_, label_str)

        self.data = None
