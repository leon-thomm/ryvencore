from PySide2.QtCore import QObject, Signal


class FlowSessionThreadInterface(QObject):

    def trigger_node_action(self, method, data=None):
        if data:
            method(data)
        else:
            method()
