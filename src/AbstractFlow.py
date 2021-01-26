from PySide2.QtCore import QObject, Signal

from .Connection import Connection, DataConnection, ExecConnection
from .Node import Node
from .NodeObjPort import NodeObjOutput, NodeObjInput, NodeObjPort
from .RC import FlowAlg, PortObjPos


class AbstractFlow(QObject):

    node_added = Signal(Node)
    node_removed = Signal(Node)
    connection_added = Signal(Connection)
    connection_removed = Signal(Connection)
    connection_request_valid = Signal(bool)
    nodes_created_from_config = Signal(list)
    connections_created_from_config = Signal(list)
    test_signal = Signal()

    algorithm_mode_changed = Signal(int)

    # nodes_config_generated = Signal(dict)
    # connections_config_generated = Signal(dict)

    def __init__(self, session, script, parent=None):
        super().__init__(parent=parent)

        self.session = session
        self.script = script
        self.nodes: [Node] = []
        self.connections: [Connection] = []
        self._temp_config_data = None

        self.alg_mode = FlowAlg.DATA

        # self.node_added.emit(None)


    def load(self, config):
        # algorithm mode
        mode = config['algorithm mode']
        if mode == 'data' or mode == 'data flow':
            self.set_algorithm_mode('data')
        elif mode == 'exec' or mode == 'exec flow':
            self.set_algorithm_mode('exec')

        # build flow
        self.create_nodes_from_config(config['nodes'])
        self.connect_nodes_from_config(self.nodes, config['connections'])


    def create_nodes_from_config(self, nodes_config: list):
        """
        Creates Nodes from nodes_config, previously returned by config_data.
        """

        nodes = []

        for n_c in nodes_config:

            # find class
            node_class = None
            if 'parent node title' in n_c:  # backwards compatibility
                for nc in self.session.nodes:
                    if nc.title == n_c['parent node title']:
                        node_class = nc
                        break
            else:
                for nc in self.session.nodes:
                    if nc.__name__ == n_c['identifier']:
                        node_class = nc
                        break

            node = self.create_node(node_class, n_c)
            nodes.append(node)
            # self.add_node(node)
            # self.node_created.emit(Node, n_c)  # info={'scene pos': [n_c['position x'], n_c['position y']]})

        self.nodes_created_from_config.emit(nodes)
        return nodes


    def create_node(self, node_class, config=None):
        node = node_class((self, self.session, config))
        self.add_node(node)
        return node


    def add_node(self, node: Node):
        node.enable_logs()
        self.nodes.append(node)
        # thread = self.thread()
        self.node_added.emit(node)


    def node_placed(self, node: Node):
        """Triggered after the FlowWidget added the item to the scene."""
        node.finish_initialization()
        node.place_event()


    def remove_node(self, node: Node):
        node.prepare_removal()
        self.nodes.remove(node)
        self.node_removed.emit(node)


    def connect_nodes_from_config(self, nodes: [Node], config: list):
        connections = []

        for c in config:

            c_parent_node_index = -1
            if 'parent node instance index' in c:  # backwards compatibility
                c_parent_node_index = c['parent node instance index']
            else:
                c_parent_node_index = c['parent node index']

            c_output_port_index = c['output port index']

            c_connected_node_index = -1
            if 'connected node instance' in c:  # backwards compatibility
                c_connected_node_index = c['connected node instance']
            else:
                c_connected_node_index = c['connected node']

            c_connected_input_port_index = c['connected input port index']

            if c_connected_node_index is not None:  # which can be the case when pasting
                parent_node = nodes[c_parent_node_index]
                connected_node = nodes[c_connected_node_index]

                c = self.connect_nodes(parent_node.outputs[c_output_port_index],
                                       connected_node.inputs[c_connected_input_port_index])
                connections.append(c)

        self.connections_created_from_config.emit(connections)

        return connections


    def check_connection_validity(self, p1: NodeObjPort, p2: NodeObjPort) -> bool:
        """
        Checks whether a considered connect action is legal.
        """
        valid = True

        if p1.node == p2.node:
            valid = False

        if p1.io_pos == p2.io_pos or p1.type_ != p2.type_:
            valid = False

        # used by FlowWidget
        self.connection_request_valid.emit(valid)

        return valid


    def connect_nodes(self, p1: NodeObjPort, p2: NodeObjPort):
        """
        Used to connect/disconnect nodes. If the ports are compatible but not yet connected,
        existing connections that are not allowed with the new connection get removed automatically.
        """

        if not self.check_connection_validity(p1, p2):
            raise Exception('Illegal connection request. Use check_connection_validity to check if a request is legal.')

        out = p1
        inp = p2
        if out.io_pos == PortObjPos.INPUT:
            out, inp = inp, out

        for c in out.connections:
            if c.inp == inp:
                # DISCONNECT
                self.remove_connection(c)
                return

        if inp.type_ == 'data':
            for c in inp.connections:
                self.remove_connection(c)

        c = DataConnection((out, inp)) if out.type_ == 'data' else ExecConnection((out, inp))
        self.add_connection(c)

        return c


    def add_connection(self, c: Connection):
        c.out.connections.append(c)
        c.inp.connections.append(c)
        c.out.connected()
        c.inp.connected()
        self.connections.append(c)
        self.connection_added.emit(c)


    def remove_connection(self, c: Connection):
        c.out.connections.remove(c)
        c.inp.connections.remove(c)
        c.out.disconnected()
        c.inp.disconnected()
        self.connections.remove(c)
        self.connection_removed.emit(c)


    def algorithm_mode(self) -> str:
        """returns the current algorithm mode of the flow as string"""

        return FlowAlg.stringify(self.alg_mode)


    def set_algorithm_mode(self, mode: str):
        """
        sets the algorithm mode of the flow
        """

        if mode == 'data':
            self.alg_mode = FlowAlg.DATA
        elif mode == 'exec':
            self.alg_mode = FlowAlg.EXEC

        self.algorithm_mode_changed.emit(self.algorithm_mode())


    def generate_config_data(self):
        """
        generates the abstract config data and saves as well as returns it as tuple (flow config, nodes, connections)
        """

        cfg = {'algorithm mode': FlowAlg.stringify(self.alg_mode)}, \
            self.generate_nodes_config(self.nodes), \
            self.generate_connections_config(self.nodes)

        self._temp_config_data = cfg
        return cfg


    def generate_nodes_config(self, nodes: [Node]):
        cfg = {}
        for n in nodes:
            cfg[n] = n.config_data()
        self._temp_config_data = cfg
        # self.nodes_config_generated.emit(cfg)
        return cfg


    def generate_connections_config(self, nodes: [Node]):
        cfg = []
        for i in range(len(nodes)):
            n = nodes[i]
            for j in range(len(n.outputs)):
                out = n.outputs[j]

                for c in out.connections:
                    connected_port = c.inp
                    connected_node = connected_port.node

                    # When copying components, there might be connections going outside the selected list of nodes.
                    # These should be ignored.
                    if connected_node not in nodes:
                        continue

                    connected_port_index = connected_node.inputs.index(connected_port)
                    connected_node_index = nodes.index(connected_node)

                    c_dict = {
                        'parent node index': i,
                        'output port index': j,
                        'connected node': connected_node_index,
                        'connected input port index': connected_port_index
                    }

                    cfg[c] = c_dict

        self._temp_config_data = cfg
        # self.connections_config_generated.emit(cfg)
        return cfg
