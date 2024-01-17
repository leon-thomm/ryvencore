from typing import Optional, Dict, Tuple

from . import Node
from .Data import Data
from .Base import Base
from .utils import serialize, deserialize

from .RC import PortObjPos
from enum import IntEnum, auto

import json


class ConnValidType(IntEnum):
    """
    Result from a connection validity test between two node ports
    """

    VALID = auto()
    SAME_NODE = auto()
    SAME_IO = auto()  # if both are input or output
    IO_MISSMATCH = auto() # if output has input pos or input has output pos
    DIFF_ALG_TYPE = auto()  # data or exec
    INVALID_PAYLOAD_TYPE = auto()  # the nodes don't accept any of the same payloads
    
    # input has reached max output connections
    # this should be the last of the checks since it
    # isn't inherently important
    MAX_INP_CONN = auto() 

class NodePort(Base):
    """
    Base class for inputs and outputs of nodes. The payload_types
    refers to the allowed types that a Data.payload might receive.
    If none or empty, any type can be connected.
    """

    def __init__(
        self, node: Node, io_pos: PortObjPos, type_: str, label_str: str, payload_types: set = None
    ):
        Base.__init__(self)

        self.node = node
        self.io_pos = io_pos
        self.type_ = type_
        self.label_str = label_str
        self.load_data = None
        self.payload_types = payload_types

    def load(self, data: Dict):
        self.load_data = data
        self.type_ = data['type']
        self.label_str = data['label']

        payload_types = data.get('payload_types')
        if payload_types is None:
            self.payload_types = None
        else:
            self.payload_types = json.loads(payload_types)

    def data(self) -> dict:
        if self.payload_types is None:
            payload_type_data = None
        else:
            payload_type_data = [f'{t.__module__}.{t.__name__}' for t in self.payload_types]
        return {
            **super().data(),
            'type': self.type_,
            'label': self.label_str,
            'payload_types': json.dumps(payload_type_data),
        }


class NodeInput(NodePort):
    """
    A node input port. This allows to specify how many output connections
    are allowed to be made to this port.
    
    max_connections > 0 (default=1): Up to N connections
    max_connections <= 0 : Infinite connections
    """
    
    def __init__(
        self,
        node: Node,
        type_: str,
        label_str: str = '',
        default: Optional[Data] = None,
        payload_types: set = None,
        max_connections: int = 1,
    ):
        super().__init__(node, PortObjPos.INPUT, type_, label_str, payload_types)

        self.default: Optional[Data] = default
        self.max_connections = max_connections

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
    def __init__(self, node: Node, type_: str, label_str: str = '', payload_types: set = None):
        super().__init__(node, PortObjPos.OUTPUT, type_, label_str, payload_types)

        self.val: Optional[Data] = None

    # def data(self) -> dict:
    #     data = super().data()
    #
    #     data['val'] = self.val if self.val is None else self.val.get_data()
    #
    #     return data


def check_conn_validity(out: NodeOutput, inp: NodeInput) -> Tuple[ConnValidType, str]:
    """
    Checks if a connection is valid between two node ports.

    Returns:
        Tuple[ConnValidType, str]: A tuple with the result of the check
        and a detailed reason, if it exists.
    """

    if out.node == inp.node:
        return (ConnValidType.SAME_NODE, "Ports from the same node cannot be connected!")
    
    if out.io_pos == inp.io_pos:
        return (ConnValidType.SAME_IO, "Connections cannot be made between ports of the same pos (inp-inp) or (out-out)")
    
    if out.io_pos != PortObjPos.OUTPUT:
        return (ConnValidType.IO_MISSMATCH, "Output or input must have the corresponding io_pos (PortObjPos) type")
    
    if out.type_ != inp.type_:
        return (ConnValidType.DIFF_ALG_TYPE, "Input and output must both be either exec ports or data ports")
    
    # both ports must require strict payload types for this check
    if out.payload_types and inp.payload_types:
        valid_payload = False
        # at least one payload type must be the same
        for payload_type in out.payload_types:
            if payload_type in inp.payload_types:
                valid_payload = True
                break
        

def check_conn_validity_tuple(conn: Tuple[NodeOutput, NodeInput]):
    out, inp = conn
    return check_conn_validity(out, inp)
