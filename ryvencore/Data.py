"""
This file defines the Data type, which must be used to pass data between nodes.
It is subclassed by the nodes to define the data type they work with.
It's primary purpose is to provide serialization and deserialization methods of the data.
Refer to my notes about graph state and serialization.
"""


class Data:
    """
    Base class for data objects.
    Subclass this class to send data to other nodes. You can directly extend the class
    to provide a common interface for your types, but you must implement serialization
    and deserialization accordingly.
    As data that is ready for sharing between nodes through the graph is part of the
    state of the graph, it must be serializable and deserializable.

    In case of large data sets being shared, you might want to leave serialization
    empty, which means the graph will not enter the same state when you reload it,
    which is fine as long as your nodes are built appropriately e.g. such that you can
    quickly regenerate that state by updating the root node.

    Be careful with nodes built for sharing complex output data over multiple outputs.
    Refer to python's object referencing rules. In particular, if you share data object
    D with successor nodes N1 and N2, and N1 changes D, then N2 will also see the change.
    To avoid this you might want to make sure to copy D once it's consumed for the second
    time, which you can also conveniently implement in your Data class.
    """

    def __init__(self, value=None, deserialize_from=None):
        if deserialize_from is not None:
            self.deserialize(deserialize_from)
        else:
            self.value = value

    def serialize(self) -> dict:
        """
        Serialize the data object to a JSON-compatible dict.
        """
        return {'value': self.value}

    def deserialize(self, data):
        """
        Deserialize the data object from a dict.
        """
        self.value = data['value']
