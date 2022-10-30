from typing import Optional

from .Data import Data
from .Base import Base

from .RC import PortObjPos


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
            **super().data(),
            'type': self.type_,
            'label': self.label_str,
        }


class NodeInput(NodePort):

    def __init__(self, node, type_, label_str='', add_data=None):
        super().__init__(node, PortObjPos.INPUT, type_, label_str)

        # data can be used to store additional data for enhanced data input ports
        self.add_data = add_data

    def data(self) -> dict:
        d = super().data()
        return d


class NodeOutput(NodePort):
    def __init__(self, node, type_, label_str=''):
        super().__init__(node, PortObjPos.OUTPUT, type_, label_str)

        self.val: Optional[Data] = None

    # def data(self) -> dict:
    #     data = super().data()
    #
    #     data['val'] = self.val if self.val is None else self.val.get_data()
    #
    #     return data
