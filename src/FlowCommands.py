from PySide2.QtWidgets import QUndoCommand

from .NodeItem import NodeItem


class MoveComponents_Command(QUndoCommand):
    def __init__(self, flow, items_list, p_from, p_to):
        super(MoveComponents_Command, self).__init__()

        self.flow = flow
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
        return self.flow.scene().createItemGroup(self.items_list)

    def destroy_items_group(self, items_group):
        self.flow.scene().destroyItemGroup(items_group)


class PlaceNodeItemInScene_Command(QUndoCommand):
    def __init__(self, flow, node_item, pos):
        super(PlaceNodeItemInScene_Command, self).__init__()

        self.flow = flow
        self.node_item = node_item
        self.NI_pos = pos

    def undo(self):
        self.flow.remove_node_item(self.node_item)

    def redo(self):
        self.flow.add_node_item(self.node_item, self.NI_pos)


class PlaceDrawingObject_Command(QUndoCommand):
    def __init__(self, flow, posF, drawing_obj):
        super(PlaceDrawingObject_Command, self).__init__()

        self.flow = flow

        self.drawing_obj = drawing_obj
        self.drawing_obj_place_pos = posF
        self.drawing_obj_pos = self.drawing_obj_place_pos

    def undo(self):
        """Important: The drawing_obj_pos is not anymore the drawing_obj_place_pos here anymore because after the
        drawing object was completed, it's actual position got recalculated according to all points and differs from
        the initial pen press pos (=drawing_obj_place_pos). See DrawingObject.finished()."""

        self.drawing_obj_pos = self.drawing_obj.pos()

        self.flow.remove_component(self.drawing_obj)

    def redo(self):
        self.flow.add_drawing(self.drawing_obj, self.drawing_obj_pos)


class RemoveComponents_Command(QUndoCommand):
    def __init__(self, flow, items):
        super(RemoveComponents_Command, self).__init__()

        self.flow = flow
        self.items = items
        self.broken_connections = []  # the connections that go beyond the removed ports and need to be restored in undo
        self.internal_connections = set()
        # self.connections = set()

        self.node_items = []
        self.nodes = []
        for i in self.items:
            if isinstance(i, NodeItem):
                self.node_items.append(i)
                self.nodes.append(i.node)

        self.connected_nodes_indices_not_in_del_selection = []
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
        for i in self.items:
            self.flow.add_component(i)
        # reconnect
        self.restore_broken_connections()
        for c in self.internal_connections:
            self.flow.add_connection(c)

        self.flow.select_components(self.items)

    def redo(self):
        # disconnect
        self.remove_broken_connections()
        for c in self.internal_connections:
            self.flow.remove_connection(c)

        for i in self.items:
            self.flow.remove_component(i)

    def restore_broken_connections(self):
        for b_c in self.broken_connections:
            self.flow.connect_ports(connection=b_c)

    def remove_broken_connections(self):
        for b_c in self.broken_connections:
            self.flow.connect_ports(b_c.out, b_c.inp)


class ConnectPorts_Command(QUndoCommand):
    def __init__(self, flow, out, inp):
        super(ConnectPorts_Command, self).__init__()

        self.flow = flow
        self.out = out
        self.inp = inp
        self.connection = None
        self.connecting = True

        for c in self.out.connections:
            if c.inp == self.inp:
                self.connection = c
                self.connecting = False

    def undo(self):
        if self.connecting:
            # disconnect
            self.flow.connect_ports(self.out, self.inp)
        else:
            # connect
            self.flow.connect_ports(connection=self.connection)

    def redo(self):
        if self.connecting:

            if not self.connection:
                self.connection = self.flow.new_connection(self.out, self.inp)

            # connect using the new or cached connection
            self.flow.connect_ports(connection=self.connection)

        else:
            # disconnect
            self.flow.connect_ports(self.out, self.inp)



class Paste_Command(QUndoCommand):
    def __init__(self, flow, data, offset_for_middle_pos):
        super(Paste_Command, self).__init__()

        self.flow = flow
        self.data = data
        self.offset_for_middle_pos = offset_for_middle_pos
        self.pasted_items = None
        self.pasted_nodes = None
        self.pasted_drawing_objects = None

        # TODO: also cache pasted_connections; replace self.flow.connect_pins in undo with self.flow.remove_connection
        #  and replace self.flow.connect_nodes_from_config with self.flow.add_connection(s) in redo
        #  problem: Flow.connect_nodes_from_config has to return the new connections which might get messy...

    def undo(self):
        self.flow.remove_components(self.pasted_items)

        # remove connections
        for ni in self.pasted_nodes:
            for o in ni.outputs:
                for i in range(len(o.connections)):
                    c = o.connections[0]
                    # disconnect pins here so they can be connected in connect_nodes_from_config in redo below again
                    self.flow.connect_ports(c.out, c.inp)

    def redo(self):
        if self.pasted_items is None:
            new_nodes, new_node_items = self.flow.place_nodes_from_config(
                self.data['nodes'],
                offset_pos=self.offset_for_middle_pos.toPoint()
            )

            self.flow.connect_nodes_from_config(new_nodes, self.data['connections'])

            new_drawing_objects = self.flow.place_drawings_from_config(self.data['drawings'],
                                                                       offset_pos=self.offset_for_middle_pos.toPoint())

            self.pasted_items = new_node_items + new_drawing_objects
            self.pasted_nodes = new_nodes
            self.pasted_drawing_objects = new_drawing_objects
        else:
            self.flow.add_node_items([n.item for n in self.pasted_nodes])
            self.flow.add_drawings(self.pasted_drawing_objects)

            # not keeping them cached for now...
            self.flow.connect_nodes_from_config(self.pasted_nodes, self.data['connections'])

        self.flow.select_components(self.pasted_items)
