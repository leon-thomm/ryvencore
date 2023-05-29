"""
This module defines the :code:`Base` class for most internal components,
implementing features such as a unique ID, a system for save and load,
and a very minimal event system.
"""
from typing import Dict


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
    """
    Implements a generalization of the observer pattern, with additional
    priority support. The lower the value, the earlier the callback
    is called. The default priority is 0.
    ryvencore itself may use negative priorities internally to ensure
    precedence of internal observers over all user-defined ones.
    """

    def __init__(self, *args):
        self.args = args
        self._slots = {i: set() for i in range(-5, 11)}
        self._slot_priorities = {}

    def sub(self, callback, nice=0):
        """
        Registers a callback function. The callback must accept compatible arguments.
        The optional :code:`nice` parameter can be used to set the priority of the
        callback. The lower the priority, the earlier the callback is called.
        :code:`nice` can range from -5 to 10.
        Users of ryvencore are not allowed to use negative priorities.
        """
        assert -5 <= nice <= 10
        assert self._slot_priorities.get(callback) is None

        self._slots[nice].add(callback)
        self._slot_priorities[callback] = nice

    def unsub(self, callback):
        """
        De-registers a callback function. The function must have been added previously.
        """
        nice = self._slot_priorities[callback]
        self._slots[nice].remove(callback)
        del self._slot_priorities[callback]

    def emit(self, *args):
        """
        Emits an event by calling all registered callback functions with parameters
        given by :code:`args`.
        """

        # notice that dicts are insertion ordered since python 3.6
        for nice, cb_set in self._slots.items():
            for cb in cb_set:
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

    def data(self) -> Dict:
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

    def load(self, data: Dict):
        """
        Recreate the object state from the data dict returned by :code:`data()`.

        Convention: don't call this method in the constructor, invoke it manually
        from outside, if other components can depend on it (and be notified of its
        creation).
        Reason: If another component `X` depends on this one (and
        gets notified when this one is created), `X` should be notified *before*
        it gets notified of creation or loading of subcomponents created during
        this load. (E.g. add-ons need to know the flow before nodes are loaded.)
        """

        if data is not None:
            self.prev_global_id = data['GID']
            self._prev_id_objs[self.prev_global_id] = self
            self.prev_version = data.get('version')
