"""
This module defines the :code:`Base` class for most internal components,
implementing features such as a unique ID, a system for save and load,
and a very minimal event system.
"""


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
    Base class for all abstract components. It provides:

    Functionality for ID counting:
        - an automatic :code:`GLOBAL_ID` unique during the lifetime of the program
        - a :code:`PREV_GLOBAL_ID` for re-identification after save & load,
          automatically set in :code:`load()`

    Serialization:
        - the :code:`data()` method gets reimplemented by subclasses to serialize
        - the :code:`load()` method gets reimplemented by subclasses to deserialize
        - the static attribute :code:`Base.complete_data_function` can be set to
          a function which extends the serialization process by supplementing the
          data dict with additional information, which is useful in many
          contexts, e.g. a frontend does not need to implement separate save & load
          functions for its GUI components
    """

    # static attributes

    _global_id_ctr = IDCtr()

    # TODO: this produces a memory leak, because the objects are never removed
    #  from the dict. It shouldn't be a problem as long as PREF_GLOBAL_ID is
    #  only used for loading, but I'd be happy to avoid this if possible
    _prev_id_objs = {}

    @classmethod
    def obj_from_prev_id(cls, prev_id: int):
        """returns the object with the given previous id"""
        return cls._prev_id_objs.get(prev_id)

    complete_data_function = lambda data: data

    @staticmethod
    def complete_data(data: dict):
        """
        Invokes the customizable :code:`complete_data_function` function
        on the dict returned by :code:`data`. This does not happen automatically
        on :code:`data()` because it is not always necessary (and might only be
        necessary once, not for each component individually).
        """
        return Base.complete_data_function(data)


    # optional version which, if set, will be stored in :code:`data()`
    version: str = None

    # non-static

    def __init__(self):
        self.global_id = self._global_id_ctr.count()

        # the following attributes are set in :code:`load()`
        self.prev_global_id = None
        self.prev_version = None

    def data(self) -> dict:
        """
        Convert the object to a JSON compatible dict.
        Reserved field names are 'GID' and 'version'.
        """
        return {
            'GID': self.global_id,

            # version optional
            **({'version': self.version}
               if self.version is not None
               else {})
        }

    def load(self, data: dict):
        """
        Recreate the object state from the data dict returned by :code:`data()`.
        """
        if dict is not None:
            self.prev_global_id = data['GID']
            self._prev_id_objs[self.prev_global_id] = self
            self.prev_version = data.get('version')
