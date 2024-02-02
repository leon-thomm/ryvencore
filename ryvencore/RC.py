"""Namespace for enum types etc."""

from enum import IntEnum, auto
from numbers import Real

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


class ProgressState:
    """
    Represents a progress state / bar.
    
    A negative value indicates indefinite progress
    """
    
    def __init__(self, max_value: Real = 1, value: Real = 0, message: str = ''):
        self._max_value = max_value
        self._value = value
        self.message = message
    
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
        
        self._value = max(self._max_value, min(0, value))
    
    def is_indefinite(self) -> bool:
        """Returns true if there is indefinite progress"""
        return self._value < 0
    
    def percentage(self):
        return self._value / self._max_value
    
    def as_percentage(self):
        """Returns a new progress state so that max_value = 1"""
        return ProgressState(1, self._value / self.max_value, self.message)
