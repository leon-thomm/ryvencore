"""
This module defines the abstract flow, managing node, edges, etc.
Flow execution is implemented by FlowExecutor class.

A *flow* is a directed, usually but not necessarily acyclic multi-graph of *nodes*
and *edges* (connections between nodes). The nodes are the computational units and
the edges define the flow of data between them. The fundamental operations to
perform on a flow are:

* adding a node
* removing a node and incident edges
* adding an edge between a node output and another node's input
* removing an edge

Flow Execution Modes
--------------------

There are a couple of different modes / algorithms for executing a flow.

**Data Flow**

In the normal data flow mode, data is simply *forward propagated on change*.
Specifically, this means the following:

A node output may have 0 or more outgoing connections/edges. When a node's output
value is updated, the new value is propagated to all connected nodes' inputs. If
there are multiple edges, the order of activation is undefined.

A node input may have 0 or 1 incoming connections/edges. When a node's input receives
new data, the node's *update event* is invoked.

A *flow execution* is started once some node's *update event* is invoked (either
by direct invocation through ``node.update()``, or by receiving input data), or
some node's output value is updated.

A node can consume inputs and update outputs at any time.

Assumptions:

    * no non-terminating feedback loops.

**Data Flow with Optimization**

Since the naive implementation of the above specification can be highly inefficient
in some cases, a more advanced algorithm can be used.
This algorithm ensures that, during a *flow execution*, each *edge* is updated at most
once.
It should implement the same semantics as the data flow algorithm, but with a slightly
tightened assumption:

    * no feedback loops / cycles in the graph
    * nodes never modify their ports (inputs, outputs) during execution (*update event*)

The additional work required for this at the beginning of a *flow execution* is based
on a DP algorithm running in :math:`\\mathcal{O}(|V|+ |E|)` time, where
:math:`|V|` is the number of nodes and
:math:`|E|` is the number of edges.
However, when there are multiple consecutive executions without
any subsequent changes to the graph, this work does not need to be repeated and execution
is fast.

**Execution Flow**

The special *exec mode* uses an additional type of connection (edge): the
*execution connection*.
While pure data flows are the more common use case, some applications call for a slightly
different paradigm. You can think of the exec mode as e.g. UnrealEngine's blueprint system.

In *exec mode*, calling ``node.exec_output(index)`` has a similar effect as calling
``node.set_output_val(index, val)`` in *data mode*,
but without any data being propagated, so it's just a trigger signal.
Pushing output data, however, does not cause updates in successor nodes.

When a node is updated (it received an *update event* through an *exec connection*), once it
needs input data (it calls ``self.input(index)``), if that input is connected to some
predecessor node `P`, then `P` receives an *update event* with ``inp=-1``, during which
it should push the output data.
Therefore, data is not forward propagated on change (``node.set_output_val(index, value)``),
but generated on request (backwards,
``node.input()`` -> ``pred.update_event()`` -> ``pred.set_output_val()`` -> return).

The *exec mode* is still somewhat experimental, because the *data mode* is the far more
common use case. It is not yet clear how to best implement the *exec mode* in a way that
is both efficient and easy to use.

Assumptions:

    * no non-terminating feedback loops with exec connections

"""

from .Base import Base, Event
from .Data import Data
from .FlowExecutor import DataFlowNaive, DataFlowOptimized, FlowExecutor, executor_from_flow_alg
from .Node import Node
from .NodePort import NodeOutput, NodeInput
from .RC import FlowAlg, PortObjPos
from .utils import *
from typing import List, Dict, Optional, Tuple


class Flow(Base):
    """
    Manages all abstract flow components (nodes, edges, executors, etc.)
    and exposes methods for modification.
    """

    def __init__(self, session, title):
        Base.__init__(self)

        # events
        self.node_added = Event(Node)
        self.node_removed = Event(Node)
        self.connection_added = Event((NodeOutput, NodeInput))        # Event(Connection)
        self.connection_removed = Event((NodeOutput, NodeInput))      # Event (Connection)

        self.connection_request_valid = Event(bool)
        self.nodes_created_from_data = Event(list)
        self.connections_created_from_data = Event(list)

        self.algorithm_mode_changed = Event(str)

        # general attributes
        self.session = session
        self.title = title
        self.nodes: [Node] = []

        self.node_successors = {}   # additional data structure for executors
        self.graph_adj = {}         # directed adjacency list relating node ports
        self.graph_adj_rev = {}     # reverse adjacency; reverse of graph_adj

        self.alg_mode = FlowAlg.DATA
        self.executor: FlowExecutor = executor_from_flow_alg(self.alg_mode)(self)

    def load(self, data: dict):
        """Loading a flow from data as previously returned by ``Flow.data()``."""
        super().load(data)

        # set algorithm mode
        self.alg_mode = FlowAlg.from_str(data['algorithm mode'])

        # build flow

        new_nodes = self._create_nodes_from_data(data['nodes'])

        self._set_output_values_from_data(new_nodes, data['output data'])

        self._connect_nodes_from_data(new_nodes, data['connections'])


    def _create_nodes_from_data(self, nodes_data: List):
        """create nodes from nodes_data as previously returned by data()"""

        nodes = []

        for n_c in nodes_data:

            # find class
            node_class = node_from_identifier(
                n_c['identifier'],
                self.session.nodes.union(self.session.invisible_nodes)
            )

            node = self.create_node(node_class, n_c)
            nodes.append(node)

        self.nodes_created_from_data.emit(nodes)

        return nodes


    def _set_output_values_from_data(self, nodes: List[Node], data: List):
        for d in data:
            indices = d['dependent node outputs']
            indices_paired = zip(indices[0::2], indices[1::2])
            for node_index, output_index in indices_paired:

                # find Data class
                dt_id = d['data']['identifier']
                if dt_id == 'Data':
                    data_type = Data
                else:
                    data_type = self.session.data_types.get(dt_id)

                    if data_type is None:
                        print_err(f'Tried to use unregistered Data type '
                                  f'{dt_id} while loading. Skipping. '
                                  f'Please register data types before using them.')
                        continue

                nodes[node_index].outputs[output_index].val = \
                    data_type(load_from=d['data'])


    def create_node(self, node_class, data=None):
        """Creates, adds and returns a new node object"""

        if node_class not in self.session.nodes:
            print_err(f'Node class {node_class} not in session nodes')
            return

        node = node_class((self, self.session, data))
        node.initialize()
        self.add_node(node)

        # notify addons
        for addon in self.session.addons.values():
            addon._on_node_created(self, node)

        return node


    def add_node(self, node: Node):
        """
        Places the node object in the graph, Stores it, and causes the node's
        ``Node.place_event()`` to be executed. ``Flow.create_node()`` automatically
        adds the node already, so no need to call this manually.
        """

        self.nodes.append(node)

        self.node_successors[node] = []
        for out in node.outputs:
            self.graph_adj[out] = []
        for inp in node.inputs:
            self.graph_adj_rev[inp] = None

        node.after_placement()
        self._flow_changed()

        # notify addons
        for addon in self.session.addons.values():
            addon._on_node_added(self, node)

        self.node_added.emit(node)


    def remove_node(self, node: Node):
        """
        Removes a node from the flow without deleting it. Can be added again
        with ``Flow.add_node()``.
        """

        node.prepare_removal()
        self.nodes.remove(node)

        del self.node_successors[node]
        for out in node.outputs:
            del self.graph_adj[out]
        for inp in node.inputs:
            del self.graph_adj_rev[inp]

        self._flow_changed()

        # notify addons
        for addon in self.session.addons.values():
            addon._on_node_removed(self, node)

        self.node_removed.emit(node)


    def _connect_nodes_from_data(self, nodes: List[Node], data: List):
        connections = []

        for c in data:

            c_parent_node_index = c['parent node index']
            c_connected_node_index = c['connected node']
            c_output_port_index = c['output port index']
            c_connected_input_port_index = c['connected input port index']

            if c_connected_node_index is not None:  # which can be the case when pasting
                parent_node = nodes[c_parent_node_index]
                connected_node = nodes[c_connected_node_index]

                connections.append(
                    self.connect_nodes(
                        parent_node.outputs[c_output_port_index],
                        connected_node.inputs[c_connected_input_port_index],
                        silent=True
                    ))

        self.connections_created_from_data.emit(connections)

        return connections


    def check_connection_validity(self, p1: NodeOutput, p2: NodeInput) -> bool:
        """
        Checks whether a considered connect action is legal.
        """

        valid = True

        if p1.node == p2.node:
            valid = False

        if p1.io_pos == p2.io_pos or p1.type_ != p2.type_:
            valid = False

        self.connection_request_valid.emit(valid)

        return valid


    def connect_nodes(self, p1: NodeOutput, p2: NodeInput, silent: bool = False) -> Optional[Tuple[NodeOutput, NodeInput]]:
        """
        Connects nodes or disconnects them if they are already connected.

        TODO: change this; rather introduce ``disconnect_nodes()`` instead
        """

        if not self.check_connection_validity(p1, p2):
            return None

        out = p1
        inp = p2
        if out.io_pos == PortObjPos.INPUT:
            out, inp = inp, out

        if inp in self.graph_adj[out]:
            # disconnect
            self.remove_connection((out, inp))
            return None

        self.add_connection((out, inp), silent=silent)

        return out, inp


    def add_connection(self, c: Tuple[NodeOutput, NodeInput], silent: bool = False):
        """
        Adds an edge between two node ports.
        """

        out, inp = c

        self.graph_adj[out].append(inp)
        self.graph_adj_rev[inp] = out

        self.node_successors[out.node].append(inp.node)
        self._flow_changed()


        self.executor.conn_added(out, inp, silent=silent)

        self.connection_added.emit((out, inp))


    def remove_connection(self, c: Tuple[NodeOutput, NodeInput]):
        """
        Removes an edge.
        """

        out, inp = c

        self.graph_adj[out].remove(inp)
        self.graph_adj_rev[inp] = None

        self.node_successors[out.node].remove(inp.node)
        self._flow_changed()

        self.executor.conn_removed(out, inp)
#
        self.connection_removed.emit((out, inp))


    def connected_inputs(self, out: NodeOutput) -> List[NodeInput]:
        """
        Returns a list of all connected inputs to the given output port.
        """
        return self.graph_adj[out]


    def connected_output(self, inp: NodeInput) -> Optional[NodeOutput]:
        """
        Returns the connected output port to the given input port, or
        ``None`` if it is not connected.
        """
        return self.graph_adj_rev[inp]


    def algorithm_mode(self) -> str:
        """
        Returns the current algorithm mode of the flow as string.
        """

        return FlowAlg.str(self.alg_mode)


    def set_algorithm_mode(self, mode: str):
        """
        Sets the algorithm mode of the flow from a string, possible values
        are 'data', 'data opt', and 'exec'.
        """

        new_alg_mode = FlowAlg.from_str(mode)
        if new_alg_mode is None:
            return False

        self.executor = executor_from_flow_alg(new_alg_mode)(self)
        self.alg_mode = new_alg_mode
        self.algorithm_mode_changed.emit(self.algorithm_mode())

        return True


    def _flow_changed(self):
        self.executor.flow_changed = True


    def data(self) -> dict:
        """
        Serializes the flow: returns a JSON compatible dict containing all
        data of the flow.
        """
        return {
            **super().data(),
            'algorithm mode': FlowAlg.str(self.alg_mode),
            'nodes': self._gen_nodes_data(self.nodes),
            'connections': self._gen_conns_data(self.nodes),
            'output data': self._gen_output_data(self.nodes),
        }


    def _gen_nodes_data(self, nodes: List[Node]) -> List[dict]:
        """Returns the data dicts of the nodes given"""

        return [n.data() for n in nodes]


    def _gen_conns_data(self, nodes: List[Node]) -> List[dict]:
        """Generates the connections data between and relative to the nodes passed"""

        # notice that this is intentionally not part of Connection, because connection data
        # is generated always for a specific set of nodes (like all currently selected ones)
        # and the data dict therefore has the refer to the indices of the nodes in the nodes list

        data = []
        for i, n in enumerate(nodes):
            for j, out in enumerate(n.outputs):
                for inp in self.graph_adj[out]:
                    if inp.node in nodes:
                        data.append({
                            'parent node index': i,
                            'output port index': j,
                            'connected node': nodes.index(inp.node),
                            'connected input port index': inp.node.inputs.index(inp),
                        })

        return data


    def _gen_output_data(self, nodes: List[Node]) -> List[Dict]:
        """Serializes output data of the nodes"""

        outputs_data = {}

        for i_n, n in enumerate(nodes):
            for i_o, out in enumerate(n.outputs):
                d = out.val
                if isinstance(d, Data) and d not in outputs_data:
                    outputs_data[d] = {
                        'data': d.data(),
                        'dependent node outputs': [i_n, i_o],
                    }
                elif isinstance(d, Data):
                    outputs_data[d]['dependent node outputs'] += [i_n, i_o]

        return list(outputs_data.values())
