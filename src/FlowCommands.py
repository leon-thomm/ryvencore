from PySide2.QtCore import Signal, QObject
from PySide2.QtWidgets import QUndoCommand

from .DrawingObject import DrawingObject
from .Node import Node
from .Connection import Connection
from .NodeItem import NodeItem
from .NodeObjPort import NodeObjPort


class MoveComponents_Command(QUndoCommand):
    def __init__(self, flow_widget, items_list, p_from, p_to):
        super(MoveComponents_Command, self).__init__()

        self.flow_widget = flow_widget
        self.items_list = items_list
        self.p_from = p_from
        self.p_to = p_to
        self.last_item_group_pos = p_to

    def undo(self):
        items_group = self.items_group()
        items_group.setPos(self.p_from)
        self.last_item_group_pos = items_group.pos()
        self.destroy_items_group(items_group)

    def redo(self):
        items_group = self.items_group()
        items_group.setPos(self.p_to - self.last_item_group_pos)
        self.destroy_items_group(items_group)


    def items_group(self):
        return self.flow_widget.scene().createItemGroup(self.items_list)

    def destroy_items_group(self, items_group):
        self.flow_widget.scene().destroyItemGroup(items_group)


class PlaceNode_Command(QUndoCommand, QObject):

    create_node_request = Signal(object)
    # add_node_request = Signal(Node)
    remove_node_request = Signal(Node)

    def __init__(self, flow_widget, node_class, pos):
        # super(PlaceNode_Command, self).__init__()
        QUndoCommand.__init__(self)
        QObject.__init__(self)

        self.flow_widget = flow_widget
        self.abstract_flow = self.flow_widget.flow
        self.node_class = node_class
        self.node = None
        self.item_pos = pos

        self.create_node_request.connect(self.abstract_flow.create_node)
        # self.add_node_request.connect(self.abstract_flow.add_node)
        self.remove_node_request.connect(self.abstract_flow.remove_node)

        self.flow_widget.node_placed.connect(self.node_placed_in_flow)

    def undo(self):
        self.remove_node_request.emit(self.node)
        self.node = None
        self.flow_widget.node_placed.connect(self.node_placed_in_flow)

    def redo(self):
        self.create_node_request.emit(self.node_class)
        # --> node_placed_in_flow()

    def node_placed_in_flow(self, node):
        self.node = node
        self.flow_widget.node_placed.disconnect(self.node_placed_in_flow)


class PlaceDrawing_Command(QUndoCommand):
    def __init__(self, flow_widget, posF, drawing):
        super(PlaceDrawing_Command, self).__init__()

        self.flow_widget = flow_widget

        self.drawing = drawing
        self.drawing_obj_place_pos = posF
        self.drawing_obj_pos = self.drawing_obj_place_pos

    def undo(self):
        # The drawing_obj_pos is not anymore the drawing_obj_place_pos because after the
        # drawing object was completed, its actual position got recalculated according to all points and differs from
        # the initial pen press pos (=drawing_obj_place_pos). See DrawingObject.finished().

        self.drawing_obj_pos = self.drawing.pos()

        self.flow_widget.remove_component(self.drawing)

    def redo(self):
        self.flow_widget.add_drawing(self.drawing, self.drawing_obj_pos)


class RemoveComponents_Command(QUndoCommand, QObject):

    add_node_request = Signal(Node)
    remove_node_request = Signal(Node)

    add_connection_request = Signal(Connection)
    remove_connection_request = Signal(Connection)

    def __init__(self, flow, items):
        # super(RemoveComponents_Command, self).__init__()
        QUndoCommand.__init__(self)
        QObject.__init__(self)

        self.flow_widget = flow
        self.abstract_flow = self.flow_widget.flow
        self.items = items
        self.broken_connections = []  # the connections that go beyond the removed nodes and need to be restored in undo
        self.internal_connections = set()

        # static connections
        self.add_node_request.connect(self.abstract_flow.add_node)
        self.remove_node_request.connect(self.abstract_flow.remove_node)
        self.add_connection_request.connect(self.abstract_flow.add_connection)
        self.remove_connections_request.connect(self.abstract_flow.remove_connection)

        self.node_items = []
        self.nodes = []
        self.drawings = []
        for i in self.items:
            if isinstance(i, NodeItem):
                self.node_items.append(i)
                self.nodes.append(i.node)
            elif isinstance(i, DrawingObject):
                self.drawings.append(i)

        for n in self.nodes:
            for i in n.inputs:
                for c in i.connections:
                    cp = c.out
                    cn = cp.node
                    if cn not in self.nodes:
                        self.broken_connections.append(c)
                    else:
                        self.internal_connections.add(c)
            for o in n.outputs:
                for c in o.connections:
                    cp = c.inp
                    cn = cp.node
                    if cn not in self.nodes:
                        self.broken_connections.append(c)
                    else:
                        self.internal_connections.add(c)

    def undo(self):
        # add connections
        self.restore_broken_connections()
        self.restore_internal_connections()

        # add nodes
        for n in self.nodes:
            self.add_node_request.emit(n)

        # add drawings
        for d in self.drawings:
            self.flow_widget.add_drawing(d)

    def redo(self):

        # remove connections
        self.remove_broken_connections()
        self.remove_internal_connections()

        # remove nodes
        for n in self.nodes:
            self.remove_node_request.emit(n)

        # remove drawings
        for d in self.drawings:
            self.flow_widget.remove_drawing(d)

    def restore_internal_connections(self):
        for c in self.internal_connections:
            self.add_connection_request.emmit(c)

    def remove_internal_connections(self):
        for c in self.internal_connections:
            self.remove_connection_request.emit(c)

    def restore_broken_connections(self):
        for c in self.broken_connections:
            self.add_connection_request(c)

    def remove_broken_connections(self):
        for c in self.broken_connections:
            self.remove_connection_request.emit(c)


class ConnectPorts_Command(QUndoCommand, QObject):

    connect_request = Signal(NodeObjPort, NodeObjPort)
    add_connection_request = Signal(Connection)
    remove_connection_request = Signal(Connection)

    def __init__(self, flow, out, inp):
        # super(ConnectPorts_Command, self).__init__()
        QUndoCommand.__init__(self)
        QObject.__init__(self)

        # CAN ALSO LEAD TO DISCONNECT INSTEAD OF CONNECT!!

        self.flow_widget = flow
        self.abstract_flow = self.flow_widget.flow
        self.out = out
        self.inp = inp
        self.connection = None
        self.connecting = True

        # static connections
        self.connect_request.connect(self.abstract_flow.connect_nodes)
        self.add_connection_request.connect(self.abstract_flow.add_connection)
        self.remove_connection_request.connect(self.abstract_flow.remove_connection)

        for c in self.out.connections:
            if c.inp == self.inp:
                self.connection = c
                self.connecting = False


    def undo(self):
        if self.connecting:
            # remove connection
            self.remove_connection_request.emit(self.connection)
        else:
            # recreate former connection
            self.add_connection_request.emit(self.connection)

    def redo(self):
        if self.connecting:
            # connection hasn't been created yet
            self.abstract_flow.connection_added.connect(self.connection_created)
            self.connect_request.emit(self.out, self.inp)
        else:
            # remove existing connection
            self.remove_connection_request.emit(self.connection)

    def connection_created(self, c):
        self.connection = c
        self.abstract_flow.connection_added.disconnect(self.connection_created)




class Paste_Command(QUndoCommand, QObject):

    create_nodes_request = Signal(list)
    create_connections_request = Signal(list)

    add_node_request = Signal(Node)
    remove_node_request = Signal(Node)

    add_connection_request = Signal(Connection)
    remove_connection_request = Signal(Connection)


    def __init__(self, flow_widget, data, offset_for_middle_pos):
        # super(Paste_Command, self).__init__()
        QUndoCommand.__init__(self)
        QObject.__init__(self)

        self.flow_widget = flow_widget
        self.abstract_flow = self.flow_widget.flow
        self.data = data
        self.modify_data_positions(offset_for_middle_pos)
        self.pasted_components = None

        # static connections
        self.add_node_request.connect(self.abstract_flow.add_node)
        self.remove_node_request.connect(self.abstract_flow.remove_node)
        self.add_connection_request.connect(self.abstract_flow.add_connection)
        self.remove_connections_request.connect(self.abstract_flow.remove_connection)


    def modify_data_positions(self, offset):
        """adds the offset to the components' positions in data"""

        for node in self.data['nodes']:
            self.data['nodes'][node]['pos x'] = self.data['nodes'][node]['pos x'] + offset.x()
            self.data['nodes'][node]['pos y'] = self.data['nodes'][node]['pos y'] + offset.y()
        for drawing in self.data['drawings']:
            self.data['drawings'][drawing]['pos x'] = self.data['drawings'][drawing]['pos x'] + offset.x()
            self.data['drawings'][drawing]['pos y'] = self.data['drawings'][drawing]['pos y'] + offset.y()


    def connect_to_flow(self):
        """creates temporary connections to retrieve the created components once"""
        self.abstract_flow.nodes_created_from_config.connect(self.nodes_created)
        self.abstract_flow.connections_created_from_config.connect(self.connections_created)
        self.create_nodes_request.connect(self.abstract_flow.create_nodes_from_config)
        self.create_connections_request.connect(self.abstract_flow.connect_nodes_from_config)

    def disconnect_from_flow(self):
        self.abstract_flow.nodes_created_from_config.disconnect(self.nodes_created)
        self.abstract_flow.connections_created_from_config.disconnect(self.connections_created)
        self.create_nodes_request.disconnect(self.abstract_flow.create_nodes_from_config)
        self.create_connections_request.disconnect(self.abstract_flow.connect_nodes_from_config)


    def redo(self):
        if self.pasted_components is None:
            # create components
            self.connect_to_flow()
            self.create_nodes_request.emit(self.data['nodes'])
            # --> nodes_created()
        else:
            self.add_existing_components()

    def undo(self):
        # remove components and their items from flow
        for n in self.pasted_components['nodes']:
            self.remove_node_request.emit(n)
        for c in self.pasted_components['connections']:
            self.remove_connection_request.emit(c)
        for d in self.pasted_components['drawings']:
            self.flow_widget.remove_drawing(d)

    def add_existing_components(self):
        # add existing components and items to flow
        for n in self.pasted_components['nodes']:
            self.add_node_request.emit(n)
        for c in self.pasted_components['connections']:
            self.add_connection_request.emit(c)
        for d in self.pasted_components['drawings']:
            self.flow_widget.add_drawing(d)



    def nodes_created(self, nodes):
        self.pasted_components = {'nodes': nodes}
        self.create_connections_request.emit(nodes, self.data['connections'])
        # --> connections_created()

    def connections_created(self, connections):
        self.disconnect_from_flow()
        self.pasted_components['connections'] = connections

        self.create_drawings()

    def create_drawings(self):
        drawings = []
        for d in self.data['drawings']:
            self.flow_widget.create_drawing(d)
        self.pasted_components['drawings'] = drawings
