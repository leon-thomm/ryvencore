from typing import Optional, Dict

from . import Node
from .Data import Data
from .Base import Base
from .utils import serialize, deserialize

from .RC import PortObjPos


class NodePort(Base):
    """Base class for inputs and outputs of nodes"""

    def __init__(self, node: Node, io_pos: PortObjPos, type_: str, label_str: str):
        Base.__init__(self)

        self.node = node
        self.io_pos = io_pos
        self.type_ = type_
        self.label_str = label_str
        self.load_data = None

    def load(self, data: Dict):
        self.load_data = data
        self.type_ = data['type']
        self.label_str = data['label']

    def data(self) -> dict:
        return {
            **super().data(),
            'type': self.type_,
            'label': self.label_str,
        }


class NodeInput(NodePort):

    def __init__(self, node: Node, type_: str, label_str: str = '', default: Optional[Data] = None):
        super().__init__(node, PortObjPos.INPUT, type_, label_str)

        self.default: Optional[Data] = default

    def load(self, data: Dict):
        super().load(data)

        self.default = Data(load_from=data['default']) if 'default' in data else None

    def data(self) -> Dict:
        default = {'default': self.default.data()} if self.default is not None else {}

        return {
            **super().data(),
            **default,
        }

class NodeOutput(NodePort):
    def __init__(self, node: Node, type_: str, label_str: str = ''):
        super().__init__(node, PortObjPos.OUTPUT, type_, label_str)

        self.val: Optional[Data] = None

    # def data(self) -> dict:
    #     data = super().data()
    #
    #     data['val'] = self.val if self.val is None else self.val.get_data()
    #
    #     return data
