"""
This module defines features and behavior that applies to most internal
components. It defines the Base (parent) class.
"""


def complete_data(data: dict) -> dict:
    """
    See ``Base.complete_data_function``.
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

class IDCtr:
    """
    A simple ascending integer ID counter.
    Guarantees uniqueness during lifetime or the program (not only of the Session).
    This approach is preferred over UUIDs because UUIDs need a networking context
    and require according system support which might not be available everywhere.
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

class Base:
    """
    Base class for all abstract components. It provides:

    Functionality for ID counting:
        - an automatic ``GLOBAL_ID`` unique during the lifetime of the program
        - a ``PREV_GLOBAL_ID`` for re-identification after save & load,
          automatically set in ``load()``

    Serialization:
        - the ``data()`` method gets reimplemented by subclasses to serialize
        - the ``load()`` method gets reimplemented by subclasses to deserialize
        - the static attribute ``Base.complete_data_function`` can be set to
          a function which extends the data dict of any component with additional
          information, which is useful e.g. in a frontend context
    """

    # all abstract components have a global ID
    _global_id_ctr = IDCtr()

    # TODO: this produces a memory leak, because the objects are never removed
    #  from the dict. It shouldn't be a problem as long as PREF_GLOBAL_ID is
    #  only used for loading.
    _prev_id_objs = {}

    @classmethod
    def obj_from_prev_id(cls, prev_id: int):
        """returns the object with the given previous id"""
        return cls._prev_id_objs.get(prev_id)

    complete_data_function = complete_data

    def __init__(self):
        self.GLOBAL_ID = self._global_id_ctr.count()
        self.PREV_GLOBAL_ID = None

    def data(self) -> dict:
        """converts the object to a JSON compatible dict for serialization"""
        return {'GID': self.GLOBAL_ID}

    def complete_data(self, data: dict) -> data:
        return Base.complete_data_function(data)

    def load(self, data: dict):
        """recreate the object from the data dict returned by ``data()``"""
        if dict is not None:
            self.PREV_GLOBAL_ID = data['GID']
            self._prev_id_objs[self.PREV_GLOBAL_ID] = self
