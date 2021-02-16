from PySide2.QtCore import QObject

from .FlowView import FlowView


class SessionThreadingBridge(QObject):
    """
    ...
    """

    def script_request__create_flow_view(self, script, params):
        view = FlowView(*params)
        script.tmp_data = view
