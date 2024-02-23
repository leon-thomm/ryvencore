"""Namespace for enum types etc."""

from enum import IntEnum, auto
from numbers import Real
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .NodePort import NodeOutput, NodeInput

class FlowAlg(IntEnum):
    """Used for performance reasons"""

    DATA = 1
    EXEC = 2
    DATA_OPT = 3

    @staticmethod
    def str(mode):
        # not using __str__ here because FlowAlg only serves as an enum,
        # so there won't be any objects instantiated
        if mode == FlowAlg.DATA:
            return 'data'
        elif mode == FlowAlg.EXEC:
            return 'exec'
        elif mode == FlowAlg.DATA_OPT:
            return 'data opt'

        return None

    @staticmethod
    def from_str(mode):
        if mode == 'data':
            return FlowAlg.DATA
        elif mode == 'exec':
            return FlowAlg.EXEC
        elif mode == 'data opt':
            return FlowAlg.DATA_OPT

        return None


class PortObjPos(IntEnum):
    """Used for performance reasons"""

    INPUT = 1
    OUTPUT = 2


class ConnValidType(IntEnum):
    """
    Result from a connection validity test between two node ports
    """

    VALID = auto()
    """Valid Connection"""
    
    SAME_NODE = auto()
    """Invalid Connection due to same node"""
    
    SAME_IO = auto()
    """Invalid Connection due to both ports being input or output"""
    
    IO_MISSMATCH = auto()
    """Invalid Connection due to output being an input and vice-versa"""
    
    DIFF_ALG_TYPE = auto()
    """Invalid Connection due to different algorithm types (data or exec)"""
    
    DATA_MISSMATCH = auto()
    """Invalid Connection due to input / output Data type checking"""
    
    INPUT_TAKEN = auto()
    """Invalid Connection due to input being connected to another output"""
    
    ALREADY_CONNECTED = auto()
    """
    Invalid Connect check
    
    Optional Check - A connect action was attempted but nodes were already connected!
    """
    
    ALREADY_DISCONNECTED = auto()
    """
    Invalid Disconnect check
    
    Optional Check - A disconnect action was attemped on disconnected ports!
    """
    
    @classmethod
    def get_error_message(cls, conn_valid_type: 'ConnValidType', out: 'NodeOutput', inp: 'NodeInput') -> str:
        """An error message for the various ConnValidType types"""
    
        if conn_valid_type == ConnValidType.SAME_NODE: 
            return "Ports from the same node cannot be connected!"
        elif conn_valid_type == ConnValidType.SAME_IO:
            return "Connections cannot be made between ports of the same pos (inp-inp) or (out-out)"
        elif conn_valid_type == ConnValidType.IO_MISSMATCH:
            return f"Output io_pos should be {PortObjPos.OUTPUT} but instead is {out.io_pos}"
        elif conn_valid_type == ConnValidType.DIFF_ALG_TYPE:
            return "Input and output must both be either exec ports or data ports"
        elif conn_valid_type == ConnValidType.DATA_MISSMATCH:
            return f"When input type is defined, output type must be a (sub)class of input type\n [out={out.allowed_data}, inp={inp.allowed_data}]"
    
        return "Valid!"

    
class ProgressState:
    """
    Represents a progress state / bar.
    
    A negative value indicates indefinite progress
    """
    
    __INDEFINITE_PROGRESS: int = -1
    
    @classmethod
    def INDEFINITE_PROGRESS(cls):
        return cls.__INDEFINITE_PROGRESS
    
    def __init__(self, max_value: Real = 1, value: Real = 0, message: str = ''):
        self._max_value = max_value
        self._value = value
        self.message = message
    
    def __str__(self) -> str:
        return f'Value:{self._value} Max:{self._max_value} Message: {self.message}'
    
    @property
    def max_value(self):
        """Max value of the progress."""
        return self._max_value
    
    @max_value.setter
    def max_value(self, max_value: Real):
        self._max_value = max_value
    
    @property
    def value(self):
        """Current value of the progress. A negative value indicates indefinite progress"""
        return self._value

    @value.setter
    def value(self, value: Real):
        if value < 0:
            self._value = value
            return
        
        self._value = min(value, self._max_value)
    
    def is_indefinite(self) -> bool:
        """Returns true if there is indefinite progress"""
        return self._value < 0
    
    def percentage(self):
        return self._value / self._max_value
    
    def as_percentage(self):
        """Returns a new progress state so that max_value = 1"""
        return ProgressState(1, self._value / self.max_value, self.message)
