import traceback
from typing import List, Optional

from .Base import Base

from .NodePort import NodeInput, NodeOutput
from .NodePortType import NodeInputType, NodeOutputType
from .RC import FlowAlg
from .Data import Data
from .InfoMsgs import InfoMsgs
from .utils import serialize, deserialize


class Node(Base):
    """
    Base class for all node blueprints. Such a blueprint is made by subclassing this class and registering that subclass
    in the session. Actual node objects are instances of it. The node's static properties are static attributes.
    Refer to python's static class attributes behavior.
    """

    title = ''
    """the node's title"""

    tags: List[str] = []
    """a list of tag strings, often useful for searching etc."""

    version: str = None
    """version tag, use it!"""

    init_inputs: List[NodeInputType] = []
    """list of node input types determining the initial inputs"""

    init_outputs: List[NodeOutputType] = []
    """initial outputs list, see ``init_inputs``"""

    identifier: str = None
    """unique node identifier string. if not given it will set it to the class name when registering in the session"""

    legacy_identifiers: List[str] = []
    """a list of compatible identifiers, useful when you change the class name (and hence the identifier) to provide 
    backward compatibility to load old projects that rely on the old identifier"""

    identifier_prefix: str = None
    """becomes part of the identifier if set; can be useful for grouping nodes"""

    #
    # INITIALIZATION
    #

    @classmethod
    def _build_identifier(cls):
        """
        Sets the identifier to the class name and prepends f"{identifier_prefix}." if
        the identifier prefix is set.
        """

        prefix = ''
        if cls.identifier_prefix is not None:
            prefix = cls.identifier_prefix + '.'

        if cls.identifier is None:
            cls.identifier = cls.__name__

        cls.identifier = prefix + cls.identifier

        # notice that we do not touch the legacy identifier fields

    def __init__(self, params):
        Base.__init__(self)

        self.flow, self.session, self.init_data = params
        self.inputs: List[NodeInput] = []
        self.outputs: List[NodeOutput] = []

        self.initialized = False

        self.block_init_updates = False
        self.block_updates = False

    def initialize(self):
        """
        Called by the Flow. This method

        - loads all default properties from initial data if it was provided
        - sets up inputs and outputs
        - loads user_data

        It does not crash on exception when loading user_data,
        as this is not uncommon when developing nodes.
        """

        if self.init_data:  # load from data
            # setup ports
            self._setup_ports(self.init_data['inputs'], self.init_data['outputs'])

            # set state
            if 'additional data' in self.init_data:
                add_data = self.init_data['additional data']
            else:   # backwards compatibility
                add_data = self.init_data
            self.load_additional_data(add_data)

            try:
                if 'version' in self.init_data:
                    version = self.init_data['version']
                else:  # backwards compatibility
                    version = None

                self.set_state(deserialize(self.init_data['state data']), version)

            except Exception as e:
                InfoMsgs.write_err(
                    f'Exception while setting data in {self.title} node:'
                    f'{e} (was this intended?)')

        else:   # default setup

            # setup ports
            self._setup_ports()

        self.initialized = True

    def _setup_ports(self, inputs_data=None, outputs_data=None):

        if not inputs_data and not outputs_data:
            # generate initial ports

            for i in range(len(self.init_inputs)):
                inp = self.init_inputs[i]

                self.create_input(inp.label, inp.type_, add_data=self.init_inputs[i].add_data)

            for o in range(len(self.init_outputs)):
                out = self.init_outputs[o]
                self.create_output(out.label, out.type_)

        else:
            # load from data
            # initial ports specifications are irrelevant then

            for inp in inputs_data:
                self.create_input(label=inp['label'], type_=inp['type'], add_data=inp)

                # if 'val' in inp:
                #     # this means the input is 'data' and did not have any connections,
                #     # so we saved its value which was probably represented by some widget
                #     # in the front end which has probably overridden the Node.input() method
                #     self.inputs[-1].val = deserialize(inp['val'])

            for out in outputs_data:
                self.create_output(out['label'], out['type'])

    def after_placement(self):
        """Called from Flow when the nodes gets added."""

        self.place_event()

    def prepare_removal(self):
        """Called from Flow when the node gets removed."""

        self.remove_event()

    """
    
    ALGORITHM
    
    """

    # notice that all the below methods check whether the flow currently 'runs with an executor', which means
    # the flow is running in a special execution mode, in which case all the algorithm-related methods below are
    # handled by the according executor

    def update(self, inp=-1):  # , output_called=-1):
        """
        Activates the node, causing an ``update_event()`` if ``block_updates`` is not set.
        For performance-, simplicity-, and maintainability-reasons activation is now
        fully handed over to the operating ``FlowExecutor``, and not managed decentralized
        in Node, NodePort, and Connection anymore.
        """

        if self.block_updates:
            InfoMsgs.write('update blocked in', self.title, 'node')
            return

        InfoMsgs.write('update in', self.title, 'node on input', inp)

        # invoke update_event
        self.flow.executor.update_node(self, inp)

    def update_error(self, e):
        InfoMsgs.write_err('EXCEPTION in', self.title, '\n', traceback.format_exc())

    def input(self, index: int) -> Optional[Data]:
        """
        Returns the data residing at the data input of given index.

        Do not call on exec inputs.
        """

        InfoMsgs.write('input called in', self.title, ':', index)

        return self.flow.executor.input(self, index)

    def exec_output(self, index: int):
        """
        Executes an exec output, causing activation of all connections.

        Do not call on data outputs.
        """

        InfoMsgs.write('executing output', index, 'in:', self.title)

        self.flow.executor.exec_output(self, index)

    def set_output_val(self, index, data: Data):
        """
        Sets the value of a data output causing activation of all connections in data mode.
        """
        assert isinstance(data, Data), "Output value must be of type ryvencore.Data"

        InfoMsgs.write('setting output', index, 'in', self.title)

        self.flow.executor.set_output_val(self, index, data)

    """
    
    EVENT SLOTS
    
    """

    # these methods get implemented by node implementations

    def update_event(self, inp=-1):
        """
        *VIRTUAL*

        Gets called when an input received a signal or some node requested data of an output in exec mode.
        Implement this in your node class, this is the place where the main processing of your node should happen.
        """

        pass

    def place_event(self):
        """
        *VIRTUAL*

        Called once the node object has been fully initialized and placed in the flow.
        When loading content, ``place_event()`` is executed *before* connections are built,
        so updating output values here will not cause any other nodes to be updated during loading.

        Notice that this method gets executed *every time* the node is added to the flow, which can happen
        multiple times for the same object (e.g. due to undo/redo operations).
        """

        pass

    def remove_event(self):
        """
        *VIRTUAL*

        Called when the node is removed from the flow; useful for stopping threads and timers etc.
        """

        pass

    def additional_data(self) -> dict:
        """
        *VIRTUAL*

        ``additional_data()``/``load_additional_data()`` is almost equivalent to
        ``get_state()``/``set_state()``,
        but it turned out to be useful for frontends to have their own dedicated version,
        so ``get_state()``/``set_state()`` stays clean for all specific node subclasses.
        """

        return {}

    def load_additional_data(self, data: dict):
        """
        *VIRTUAL*

        For loading the data returned by ``additional_data()``.
        """
        pass

    def get_state(self) -> dict:
        """
        *VIRTUAL*

        If your node is stateful, implement this method for serialization. It should return a JSON compatible
        dict that encodes your node's state. The dict will be passed to ``set_state()`` when the node is loaded.
        """
        return {}

    def set_state(self, data: dict, version):
        """
        *VIRTUAL*

        Opposite of ``get_state()``, reconstruct any custom internal state here.
        """
        pass

    """
    
    API
    
    """

    #   PORTS

    def create_input(self, label: str = '', type_: str = 'data', add_data={}, insert: int = None):
        """
        Creates and adds a new input at the end or index ``insert`` if specified.
        """
        # InfoMsgs.write('create_input called')

        inp = NodeInput(
            node=self,
            type_=type_,
            label_str=label,
            add_data=add_data,
        )

        if insert is not None:
            self.inputs.insert(insert, inp)
        else:
            self.inputs.append(inp)

        return inp

    def rename_input(self, index: int, label: str):
        self.inputs[index].label_str = label

    def delete_input(self, index: int):
        """
        Disconnects and removes an input.
        """

        inp: NodeInput = self.inputs[index]

        # break all connections
        out = self.flow.connected_output(inp)
        if out is not None:
            self.flow.connect_nodes(out, inp)

        self.inputs.remove(inp)

    def create_output(self, label: str = '', type_: str = 'data', insert: int = None):
        """
        Creates and adds a new output at the end or index ``insert`` if specified.
        """

        out = NodeOutput(
              node=self,
              type_=type_,
              label_str=label
        )

        if insert is not None:
            self.outputs.insert(insert, out)
        else:
            self.outputs.append(out)

        return out

    def rename_output(self, index: int, label: str):
        self.outputs[index].label_str = label

    def delete_output(self, index: int):
        """
        Disconnects and removes output.
        """

        out: NodeOutput = self.outputs[index]

        # break all connections
        for inp in self.flow.connected_inputs(out):
            self.flow.connect_nodes(out, inp)

        self.outputs.remove(out)

    #   VARIABLES

    def get_addon(self, name: str):
        """
        Returns an add-on registered in the session by name, or None if it wasn't found.
        """
        return self.session.addons.get(name)

    """
    
    UTILITY METHODS
    
    """

    def is_active(self):
        for i in self.inputs:
            if i.type_ == 'exec':
                return True
        for o in self.outputs:
            if o.type_ == 'exec':
                return True
        return False

    def _inp_connected(self, index):
        return self.flow.connected_output(self.inputs[index]) is not None

    """
    
    SERIALIZATION
    
    """

    def data(self) -> dict:
        """
        Returns all metadata of the node in JSON-compatible dict, including custom state.
        Used to rebuild the Flow when loading a project or pasting components.
        """

        d = {
            **super().data(),

            'identifier': self.identifier,
            'version': self.version,    # this overrides the version field from Base

            'state data': serialize(self.get_state()),
            'additional data': self.additional_data(),

            'inputs': [i.data() for i in self.inputs],
            'outputs': [o.data() for o in self.outputs],
        }

        # extend with data from addons
        for name, addon in self.session.addons.items():
            # addons can modify anything, there is no isolation enforcement
            addon._extend_node_data(self, d)

        return d
