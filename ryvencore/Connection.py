"""
deprecated and now unused
"""

from .Base import Base, Event

from .InfoMsgs import InfoMsgs


class Connection(Base):
    """
    The base class for both types of connections. All data is transmitted through a connection from an output
    port to some connected input port.
    """

    def __init__(self, params):
        Base.__init__(self)

        self.activated = Event(object)  # TODO: connections are not activated anymore

        self.out, self.inp, self.flow = params


class ExecConnection(Connection):
    pass


class DataConnection(Connection):

    def __init__(self, params):
        super().__init__(params)

        self.data = None
