from PySide2.QtCore import QThread, Signal, SIGNAL

from .FlowView import FlowView


class SessionThread(QThread):
    """
    Base class for threading sessions.
    This OBJECT is supposed to live in the main (GUI) thread. It's the interface for ryvencore to create GUI.
    """

    flow_view_created = Signal(object)

    # def __init__(self, parent=None):
    #     super().__init__(parent=parent)

    def script_request__create_flow_view(self, script, params):
        print('creating flow view in SessionThread')
        print(self.receivers(SIGNAL("flow_view_created(object)")))

        # TODO: implement this with actual thread safety!

        # self.flow_view_created.connect(script.flow_view_created)
        view = FlowView(*params)
        print('new view:', view)
        print('emitting flow_view created')
        self.flow_view_created.emit(view)
        print('finished in SessionThread')
        # self.flow_view_created.disconnect(script.flow_view_created)
