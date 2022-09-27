"""
This module defines dtypes, definitions of declarative types which can be conveniently used for
data inputs, and an add-on for those.

These dtypes only store some information which might be used by the nodes, or by a frontend, etc.
There is currently no type checking or something like that implemented, but might be added
optionally in the future.

This list may grow significantly over time.
"""

from typing import Dict as t_Dict, List as t_List


class DType:
    def __init__(self, default, bounds: tuple = None, doc: str = "", _load_state=None):

        self.default = default
        self.val = self.default
        self.doc = doc
        self.bounds = bounds

        if _load_state:
            self.set_state(_load_state)

        self._data = ['default', 'val', 'doc', 'bounds']

    def __str__(self):
        return 'DType.'+self.__class__.__name__

    @staticmethod
    def from_str(s):
        for DTypeClass in dtypes:
            if s == 'DType.'+DTypeClass.__name__:
                return DTypeClass

        return None

    def add_data(self, *attr_names):
        self._data += list(attr_names)

    def get_state(self) -> dict:
        return {
            name: getattr(self, name)
            for name in self._data
        }

    def set_state(self, data: dict):
        for name, val in data.items():
            setattr(self, name, val)


class Data(DType):
    """Any kind of data represented by some evaluated text input"""
    def __init__(self, default=None, size: str = 'm', doc: str = "", _load_state=None):
        """
        size: 's' / 'm' / 'l'
        """
        self.size = size
        super().__init__(default=default, doc=doc, _load_state=_load_state)
        self.add_data('size')


class Integer(DType):
    def __init__(self, default: int = 0, bounds: tuple = None, doc: str = "", _load_state=None):
        super().__init__(default=default, bounds=bounds, doc=doc, _load_state=_load_state)


class Float(DType):
    def __init__(self, default: float = 0.0, bounds: tuple = None, decimals: int = 10, doc: str = "", _load_state=None):
        self.decimals = decimals
        super().__init__(default=default, bounds=bounds, doc=doc, _load_state=_load_state)
        self.add_data('decimals')


class Boolean(DType):
    def __init__(self, default: bool = False, doc: str = "", _load_state=None):
        super().__init__(default=default, doc=doc, _load_state=_load_state)


class Char(DType):
    def __init__(self, default: chr = '', doc: str = "", _load_state=None):
        super().__init__(default=default, doc=doc, _load_state=_load_state)


class String(DType):
    def __init__(self, default: str = "", size: str = 'm', doc: str = "", _load_state=None):
        """
        size: 's' / 'm' / 'l'
        """
        self.size = size
        super().__init__(default=default, doc=doc, _load_state=_load_state)
        self.add_data('size')


class Choice(DType):
    def __init__(self, default=None, items: t_List = [], doc: str = "", _load_state=None):
        self.items = items
        super().__init__(default=default, doc=doc, _load_state=_load_state)
        self.add_data('items')


class List(DType):
    def __init__(self, default: t_List = [], doc: str = "", _load_state=None):
        super().__init__(default=default, doc=doc, _load_state=_load_state)


class Date(DType):
    ...


class Time(DType):
    ...


class Color(DType):
    ...


class Range(DType):
    ...


# dtypes = [Data, Integer, Float, Boolean, Char, String, Choice, List]



'''

Node: ...

    def create_input_dt(self, dtype: DType, label: str = '', add_data={}, insert: int = None):
        """Creates and adds a new data input with a DType"""
        # InfoMsgs.write('create_input called')

        inp = NodeInput(
            node=self,
            type_='data',
            label_str=label,
            dtype=dtype,
            add_data=add_data,
        )

        if insert is not None:
            self.inputs.insert(insert, inp)
        else:
            self.inputs.append(inp)


NodePort.data(): ...

        if self.dtype:
            data['dtype'] = str(self.dtype)
            data['dtype state'] = serialize(self.dtype.get_state())
'''

from ryvencore import AddOn
from ryvencore import NodeInputType


class DtypesAddon(AddOn):
    """
    An add-on that adds the ability to create data inputs with a DType.
    A DType simply holds some information about the data supposed to be
    processed at the respective input, but does not perform any typechecks.

    Currently, DType inputs can only be created dynamically through
    ``DTypes.create_dtype_input(self, ...)``, not in ``init_inputs``. This
    might change once we found a way of communicating the DType information
    back to the add-on when node inputs are built from ``init_inputs``,
    which currently isn't easily possible.
    """

    name = 'DTypes'
    version = '0.0.1'

    Data = Data
    Integer = Integer
    Float = Float
    Boolean = Boolean
    Char = Char
    String = String
    Choice = Choice
    List = List

    class NodeInputType(NodeInputType):
        def __init__(self, dtype=None, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.dtype = dtype

    def __init__(self):
        super().__init__()

        self.dtype_inputs = {}  # {NodeInput: DType}
        self.creating_dtype_input = False

    def create_dtype_input(self, node, dtype, *args, **kwargs):
        """
        Dynamically creates a new input and assigns the given dtype.
        """

        self.creating_dtype_input = True
        inp = node.create_input(*args, **kwargs)
        self.creating_dtype_input = False

        # dtypes are only on data inputs allowed
        if inp.type_ != 'data':
            node.delete_input(node.inputs.index(inp))
            return

        self.dtype_inputs[inp] = dtype

    def _on_node_created(self, flow, node):
        """
        Restores the node's dtypes.
        """

        for i, inp in enumerate(node.inputs):
            if inp.type_ == 'data' and 'dtype' in node.init_data['inputs'][i]:
                dtype = DType.from_str(node.init_data['inputs'][i]['dtype'])
                dtype.set_state(node.init_data['inputs'][i]['dtype']['state'])
                self.dtype_inputs[inp] = dtype

    def _extend_node_data(self, node, data: dict):
        for i, inp in enumerate(node.inputs):
            if inp in self.dtype_inputs:
                data['inputs'][i]['dtype'] = {
                    'type': str(self.dtype_inputs[inp]),
                    'state': self.dtype_inputs[inp].get_state(),
                }

# addon = DtypesAddon()
