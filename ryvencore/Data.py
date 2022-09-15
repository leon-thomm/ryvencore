"""
This file defines the Data type, which must be used to pass data between nodes.
It should be subclassed to define custom data types. In particular, serialization
and deserialization must be implemented for each respective type. Types that are
pickle serializable by default can be used without subclassing (``Data(my_data)``).
"""


class Data:
    """
    Base class for data objects.

    Subclass this class and implement serialization and deserialization accordingly
    to send data to other nodes.

    In case of large data sets being shared, you might want to leave serialization
    empty, which means the graph will not enter the same state when you reload it,
    which is fine as long as your nodes are built appropriately e.g. such that you can
    quickly regenerate that state by updating the root node.

    Be careful with nodes built for sharing complex output data over multiple outputs.
    Refer to python's object referencing rules. In particular, if you share data object
    `D` with successor nodes `N1` and `N2`, and `N1` changes `D`, then `N2` will also
    see the change.
    To avoid this you might want to make sure to copy `D` once it's consumed for the
    second time, which you can also conveniently implement in your ``Data`` class.
    """

    def __init__(self, value=None, load_from=None):
        if load_from is not None:
            self.set_data(load_from)
        else:
            self.payload = value

    def get_data(self):
        """
        Transform the data object to a ``pickle``serializable object.
        """
        return self.payload

    def set_data(self, data):
        """
        Deserialize the data object from the dict created in ``serialize()``.
        """
        self.payload = data
