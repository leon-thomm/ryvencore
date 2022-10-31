"""
This file defines the :code:`Data` type, which must be used to pass data between nodes.
It should be subclassed to define custom data types. In particular, serialization
and deserialization must be implemented for each respective type. Types that are
pickle serializable by default can be used directly with :code`Data(my_data)`.
"""
from ryvencore.Base import Base
from ryvencore.utils import serialize, deserialize, print_err


class Data(Base):
    """
    Base class for data objects.

    Subclass this class and implement serialization and deserialization accordingly
    to send data to other nodes. You must register your custom :code:`Data` subclass
    with the :code:`Session.register_data()` before using it (which especially applies
    to loading a project, custom :code:`Data` subclasses used must be registered in
    advance).

    In case of large data sets being shared, you might want to leave serialization
    empty, which means the graph will not enter the same state when you reload it,
    which is fine as long as your nodes are built appropriately e.g. such that you can
    quickly regenerate that state by updating the root node.

    Be careful when consuming complex input data: modification can lead to undesired
    effects. In particular, if you share some data object :math:`d` with successor nodes
    :math:`N1` and :math:`N2`, and :math:`N1` changes :math:`d` directly, then :math:`N2`
    will see the change as well, because they look at the same Data object:

    >>> import ryvencore as rc
    >>>
    >>> class Producer(rc.Node):
    ...     init_outputs = [rc.NodeOutputType()]
    ...
    ...     def push_data(self, d):
    ...         self.d = d
    ...         self.update()
    ...
    ...     def update_event(self, inp=-1):
    ...         self.set_output_val(0, self.d)
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
    To avoid this you might want to make sure to copy :math:`d` when its payload is
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

    # will be 'Data' by default, see :code:`_build_identifier()`
    identifier: str = None
    """unique Data identifier; you can set this manually in subclasses, if
    you don't the class name will be used"""

    legacy_identifiers = []
    """a list of compatible identifiers in case you change the identifier"""

    @classmethod
    def _build_identifier(cls):
        cls.identifier = cls.__name__

    def __init__(self, value=None, load_from=None):
        super().__init__()

        if load_from is not None:
            self.load(load_from)
        else:
            self._payload = value

    def __str__(self):
        return f'<{self.__class__.__name__}({self.payload}) object, GID: {self.global_id}>'

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value

    def get_data(self):
        """
        *VIRTUAL*

        Transform the data object to a :code:`pickle` serializable object.
        **Do not** use this function to access the payload, use :code:`payload` instead.
        """
        return self.payload     # naive default implementation

    def set_data(self, data):
        """
        *VIRTUAL*

        Deserialize the data object from the dict created in :code:`get_data()`.
        """
        self.payload = data     # naive default implementation

    def data(self) -> dict:
        return {
            **super().data(),
            'identifier': self.identifier,
            'serialized': serialize(self.get_data())
        }

    def load(self, data: dict):
        super().load(data)

        if data['identifier'] != self.identifier and \
                data['identifier'] not in self.legacy_identifiers:
            # this should not happen when loading a Flow, because the flow checks
            print_err(f'WARNING: Data identifier {data["identifier"]} '
                      f'is not compatible with {self.identifier}. Skipping.'
                      f'Did you forget to add it to legacy_identifiers?')
            return

        self.set_data(deserialize(data['serialized']))


# build identifier for Data
Data._build_identifier()
