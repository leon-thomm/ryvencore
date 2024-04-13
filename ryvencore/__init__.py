from .InfoMsgs import InfoMsgs
from .RC import *
from .Session import Session
from .Flow import Flow
from .data.Data import Data
from .AddOn import AddOn
from .Node import Node
from .NodePortType import NodeInputType, NodeOutputType
from .utils import serialize, deserialize

def set_complete_data_func(func):
    from .Base import Base
    Base.complete_data_function = func
