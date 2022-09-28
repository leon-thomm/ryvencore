"""
This file defines the ``Data`` type, which must be used to pass data between nodes.
It should be subclassed to define custom data types. In particular, serialization
and deserialization must be implemented for each respective type. Types that are
pickle serializable by default can be used directly with ``Data(my_data)``.
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

    Be careful when consuming complex input data: modification can lead to undesired
    effects. In particular, if you share some data object ``D`` with successor nodes
    ``N1`` and ``N2``, and ``N1`` changes ``D`` directly, then ``N2``
    will see the change as well, because they look at the same Data object:

    >>> import ryvencore as rc
    >>>
    >>> class Producer(rc.Node):
    ...     init_outputs = [rc.NodeOutputType()]
    ...
    ...     def push_data(self, D):
    ...         self.D = D
    ...         self.update()
    ...
    ...     def update_event(self, inp=-1):
    ...         self.set_output_val(0, self.D)
    >>>
    >>> class Consumer(rc.Node):
    ...     init_inputs = [rc.NodeInputType()]
    ...
    ...     def update_event(self, inp=-1):
    ...         p = self.input(0).payload
    ...         p.append(4)
    ...         print(p)
    >>>
    >>> def build_and_run(D):
    ...     s = rc.Session()
    ...     f = s.create_flow('main')
    ...     producer =  f.create_node(Producer)
    ...     consumer1 = f.create_node(Consumer)
    ...     consumer2 = f.create_node(Consumer)
    ...     f.connect_nodes(producer.outputs[0], consumer1.inputs[0])
    ...     f.connect_nodes(producer.outputs[0], consumer2.inputs[0])
    ...     producer.push_data(D)
    >>>
    >>> build_and_run(rc.Data([1, 2, 3]))
    [1, 2, 3, 4]
    [1, 2, 3, 4, 4]

    This can be useful for optimization when sharing large data, but might not
    be what you want.
    To avoid this you might want to make sure to copy ``D`` when its payload is
    consumed:

    >>> class MyListData(rc.Data):
    ...     @property
    ...     def payload(self):
    ...         return self._payload.copy()
    >>>
    >>> build_and_run(MyListData([1, 2, 3]))
    [1, 2, 3, 4]
    [1, 2, 3, 4]
    """

    def __init__(self, value=None, load_from=None):
        if load_from is not None:
            self.set_data(load_from)
        else:
            self._payload = value

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value

    def get_data(self):
        """
        Transform the data object to a ``pickle`` serializable object.
        DO NOT use this function to access the payload, use ``payload`` instead.
        """
        return self.payload

    def set_data(self, data):
        """
        Deserialize the data object from the dict created in ``get_data()``.
        """
        self.payload = data
