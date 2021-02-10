from PySide2.QtCore import QThread, Signal

from custom_src.ryvencore.src.FlowView import FlowView


class SessionThread(QThread):
    """
    Base class for threading sessions.
    This OBJECT is supposed to live in the main (GUI) thread. It's the interface for ryvencore to create GUI.
    """

    flow_created = Signal(object)

    # def __init__(self, parent=None):
    #     super().__init__(parent=parent)

    def _script_request__create_flow(self, script, params):
        # TODO: implement this with actual thread safety!

        self.flow_created.connect(script.flow_widget_created)
        self.flow_created.emit(FlowView(*params))
        self.flow_created.disconnect(script.flow_widget_created)
