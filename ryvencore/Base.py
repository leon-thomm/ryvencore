"""
This module defines features and behavior that applies to most internal
components. It defines the Base (parent) class featuring events, automatic and
custom ID assignments, serialization, and customizable extension of serialization.
"""


def complete_data(data: dict) -> dict:
    """
    Default implementation for supplementing data with additional (e.g. frontend)
    information. For example, a frontend can store additional information like
    current position, color of a node, etc. by replacing this function by an
    according custom handler.
    """
    return data


class Event:
    def __init__(self, *args):
        self.args = args
        self._slots = []

    def connect(self, callback):
        """
        Registers a callback function. The callback must accept compatible arguments.
        """
        self._slots.append(callback)

    def disconnect(self, callback):
        """
        De-registers a callback function. The function must have been added previously.
        """
        self._slots.remove(callback)

    def emit(self, *args):
        """
        Emits an event by calling all registered callback functions in the order they
        were registered, with parameters given by *args.
        """

        # I am assuming that the for-each loop keeps the overhead small in case
        # there are no slots registered, but one might want to profile that.

        for cb in self._slots:
            cb(*args)


class Base:
    """
    Base class for all abstract components. Provides functionality for ID counting.
    Assigns a global ID to every object and provides an optional custom ID counter for additional custom counting.
    """

    class IDCtr:
        """
        A simple ascending integer counter.
        """

        def __init__(self):
            self.ctr = -1

        def count(self):
            """increases the counter and returns the new count. first time is 0"""
            self.ctr += 1
            return self.ctr

        def set_count(self, cnt):
            if cnt < self.ctr:
                raise Exception("Decreasing ID counters is illegal")
            else:
                self.ctr = cnt

    # all abstract components have a global ID
    global_id_ctr = IDCtr()

    # optional custom ID counter
    id_ctr = None
    # notice that the attribute is static, but a subclass changing it will not change it for Base
    # and hence not for other Base subclasses, only for itself

    # events
    events = {}
    # format: {event_name : tuple_of_argument_types}
    # the arguments tuple only serves documentation purposes

    def __init__(self):
        self.GLOBAL_ID = self.global_id_ctr.count()

        # ignore custom ID if it has already been set
        if self.id_ctr is not None and not (hasattr(self, 'ID') and self.ID is not None):
            self.ID = self.id_ctr.count()

        self._slots = {
            ev: []
            for ev in self.events
        }

    """
    
    CUSTOM DATA
    
    """

    # this can be conveniently set to another function by the host to implement
    # adding additional (e.g. frontend-related) information to the data dict
    complete_data_function = complete_data

    def data(self) -> dict:
        """converts the object to a JSON compatible dict for serialization"""
        return None

    def complete_data(self, data: dict) -> data:
        return Base.complete_data_function(data)

    """
    
    EVENTS
    
    """

    def on(self, ev: Event, callback):
        # self._slots[ev].append(callback)
        ev.connect(callback)

    def off(self, ev: Event, callback):
        # self._slots[ev].remove(callback)
        ev.disconnect(callback)

    # def _emit(self, ev: str, *args, **kwargs):
    #     for s in self._slots[ev]:
    #         s(args, kwargs)
