from enum import IntEnum


class FlowAlg(IntEnum):
    DATA = 1
    EXEC = 2


class PortType(IntEnum):
    DATA = 1
    EXEC = 2


class PortPos(IntEnum):
    INPUT = 1
    OUTPUT = 2


class InpWidgetPos(IntEnum):
    BESIDES = 1
    BELOW = 2


class MainWidgetPos(IntEnum):
    BETWEEN = 1
    BELOW = 2

