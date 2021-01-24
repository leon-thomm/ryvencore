from PySide2.QtCore import QThread, QObject, Signal


# class FlowWorkerThread(QThread):
#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#
#         self.interface = FlowSessionThreadInterface()
#         self.interface.moveToThread(self)


class FlowSessionThreadInterface(QObject):

    node_created = Signal(object, tuple, bool)

    def __init__(self, parent):
        super().__init__(parent=parent)

        print(f'FlowSessionThreadInterface\'s thread: {self.thread()}')

    def trigger_port_connected(self, port):
        port.connected()

    def trigger_port_disconnected(self, port):
        port.disconnected()

    def create_node(self, node_class, params, commanded, pos):
        node = node_class(params)
        node.finish_initialization()
        self.node_created.emit(node, params, commanded, pos)
#
    def trigger_node_update(self, node, input_called=-1):
        node.update(input_called)

    def trigger_node_action(self, method, data=None):
        if data:
            method(data)
        else:
            method()

    def trigger_node_removal(self, node):
        node.prepare_removal()