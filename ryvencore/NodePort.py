from typing import Optional, Dict, Type, Tuple, TYPE_CHECKING

from .Base import Base
from .utils import serialize, deserialize

from .RC import PortObjPos, ConnValidType
from .data import Data, check_valid_data

if TYPE_CHECKING:
    from .Node import Node

class NodePort(Base):
    """Base class for inputs and outputs of nodes"""

    def __init__(self, node, io_pos: PortObjPos, type_: str, label_str: str, allowed_data: Optional[Type[Data]] = None):
        Base.__init__(self)

        self.node: Node = node
        self.io_pos = io_pos
        self.type_ = type_
        self.label_str = label_str
        self.load_data = None
        self.allowed_data = allowed_data

    def load(self, data: Dict):
        self.load_data = data
        self.type_ = data['type']
        self.label_str = data['label']
        # allowed data - backwards compatibility
        data_id = data.get('allowed_data')
        if data_id is not None:
            self.allowed_data = self.node.session.get_data_type(data_id)
        
    def data(self) -> dict:
        return {
            **super().data(),
            'type': self.type_,
            'label': self.label_str,
            'allowed_data': self.allowed_data.identifier if self.allowed_data is not None else None
        }


class NodeInput(NodePort):

    def __init__(self, node, type_: str, label_str: str = '', default: Optional[Data] = None, allowed_data: Optional[Type[Data]] = None):
        super().__init__(node, PortObjPos.INPUT, type_, label_str, allowed_data)

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
    def __init__(self, node, type_: str, label_str: str = '', allowed_data: Optional[Type[Data]] = None):
        super().__init__(node, PortObjPos.OUTPUT, type_, label_str, allowed_data)

        self.val: Optional[Data] = None

    # def data(self) -> dict:
    #     data = super().data()
    #
    #     data['val'] = self.val if self.val is None else self.val.get_data()
    #
    #     return data

def check_valid_conn(out: NodeOutput, inp: NodeInput) -> ConnValidType:
    """
    Checks if a connection is valid between two node ports.

    Returns:
        An enum representing the check result
    """
    
    if out.node == inp.node:
        return ConnValidType.SAME_NODE
    
    if out.io_pos == inp.io_pos:
        return ConnValidType.SAME_IO
    
    if out.io_pos != PortObjPos.OUTPUT:
        return ConnValidType.IO_MISSMATCH
    
    if out.type_ != inp.type_:
        return ConnValidType.DIFF_ALG_TYPE
    
    if not check_valid_data(out.allowed_data, inp.allowed_data):
        return ConnValidType.DATA_MISSMATCH
    
    return ConnValidType.VALID

def check_valid_conn_tuple(connection: Tuple[NodeOutput, NodeInput]):
    out, inp = connection
    return check_valid_conn(out, inp)
    