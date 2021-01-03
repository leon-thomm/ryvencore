from PySide2.QtCore import QThread, QObject


class FlowWorkerThread(QThread):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.interface = FlowWorkerThreadInterface()
        self.interface.moveToThread(self)


class FlowWorkerThreadInterface(QObject):

    def trigger_port_connected(self, port):
        port.connected()

    def trigger_port_disconnected(self, port):
        port.disconnected()

    def trigger_node_update(self, node, input_called=-1):
        node.update(input_called)