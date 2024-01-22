"""Namespace for enum types etc."""

from enum import IntEnum, auto


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
    """Invalid Connection due to input / output not accepting the same family of Data"""
