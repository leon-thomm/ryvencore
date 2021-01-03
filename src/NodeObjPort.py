from PySide2.QtCore import QObject, Signal

from .PortItem import InputPortItem, OutputPortItem
from .RC import PortObjPos, FlowAlg


class NodeObjPort(QObject):

    has_been_connected = Signal()
    has_been_disconnected = Signal()

    def __init__(self, node, io_pos, type_, label_str):
        super().__init__()

        self.val = None
        self.node = node
        self.io_pos = io_pos
        self.type_ = type_
        self.label_str = label_str
        self.connections = []
        self.item = None


    def get_val(self):
        pass

    def connected(self):
        self.has_been_connected.emit()

    def disconnected(self):
        self.has_been_disconnected.emit()

    def config_data(self):
        pass


class NodeObjInput(NodeObjPort):
    def __init__(self, node, type_, label_str='', widget_name=None, widget_pos='besides', config_data=None):
        super().__init__(node, PortObjPos.INPUT, type_, label_str)

        self.widget_name = widget_name
        self.widget_pos = widget_pos
        self.widget_config_data = config_data

        self.item = InputPortItem(self.node, self)


    def connected(self):
        super().connected()
        if self.type_ == 'data':
            self.update()

    def get_val(self):
        if len(self.connections) == 0:
            if self.item.widget:
                return self.item.widget.get_val()
            else:
                return None
        else:
            return self.connections[0].get_val()

    def update(self):
        """called from another node or from connected()"""
        if self.type_ == 'data':
            self.val = self.get_val()  # might remove that later for performance

        if (self.node.is_active() and self.type_ == 'exec') or \
           not self.node.is_active():
            self.node.update(self.node.inputs.index(self))

    def config_data(self):
        data_dict = {'type': self.type_,
                     'label': self.label_str}

        has_widget = True if self.item.widget else False
        data_dict['has widget'] = has_widget
        if has_widget:
            data_dict['widget name'] = self.widget_name
            data_dict['widget data'] = None if self.type_ == 'exec' else self.item.widget.get_data()
            data_dict['widget position'] = self.widget_pos

        return data_dict


class NodeObjOutput(NodeObjPort):
    def __init__(self, node, type_, label_str=''):
        super().__init__(node, PortObjPos.OUTPUT, type_, label_str)

        self.item = OutputPortItem(node, self)

    def exec(self):
        for c in self.connections:
            c.activate()

    def get_val(self):
        # Debugger.debug('returning val directly')
        if self.node.flow.alg_mode == FlowAlg.EXEC:
            self.node.update()
        return self.val

    def set_val(self, val):

        # note that val COULD be of object type and therefore already changed (because the original object did)
        self.val = val

        # if algorithm mode would be exec flow, all data will be required instead of actively forward propagated
        if self.node.flow.alg_mode == FlowAlg.DATA:  # and \
                # not self.node.initializing
            self.updated_val()

    def updated_val(self):
        for c in self.connections:
            c.activate()

    def config_data(self):
        data_dict = {'type': self.type_,
                     'label': self.label_str}

        return data_dict
