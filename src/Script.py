from PySide2.QtCore import QObject, Signal

from .Flow import Flow
from .RC import FlowVPUpdateMode, FlowAlg
from .logging.Logger import Logger
from .script_variables.VarsManager import VarsManager


class Script(QObject):

    # name_changed = Signal(str)  ->  Script()
    flow_algorithm_mode_changed = Signal(str)
    flow_viewport_update_mode_changed = Signal(str)

    def __init__(self, session, title: str = None, config: dict = None, flow_size: list = None, flow_parent=None):
        super(Script, self).__init__()

        self.session = session
        self.logger = Logger(self)
        self.vars_manager = None
        self.title = title
        self.flow = None
        self.__thumbnail_source = ''  # URL to the Script's thumbnail picture

        if config:
            self.title = config['name']
            self.vars_manager = VarsManager(self, config['variables'])
            self.flow = Flow(session, self, flow_size, config['flow'], parent=flow_parent)
        else:
            self.flow = Flow(session, self, flow_size, parent=flow_parent)
            self.vars_manager = VarsManager(self)

    def flow_algorithm_mode(self) -> FlowAlg:
        """Returns the current algorithm mode of the flow"""
        return self.flow.algorithm_mode

    def set_flow_algorithm_mode(self, mode: str):
        """
        Sets the algorithm mode of the flow
        :mode: 'data' or 'exec'
        """
        if mode == 'data':
            self.flow.algorithm_mode = FlowAlg.DATA
        elif mode == 'exec':
            self.flow.algorithm_mode = FlowAlg.EXEC

    def flow_viewport_update_mode(self) -> FlowVPUpdateMode:
        """Returns the current viewport update mode (sync or async) of the flow"""
        return self.flow.viewport_update_mode

    def set_flow_viewport_update_mode(self, mode: str):
        """
        Sets the viewport update mode of the flow
        :mode: 'sync' or 'async'
        """
        if mode == 'sync':
            self.flow.viewport_update_mode = FlowVPUpdateMode.SYNC
        elif mode == 'async':
            self.flow.viewport_update_mode = FlowVPUpdateMode.ASYNC

    def config_data(self) -> dict:
        """Returns the config data of the script, including variables and flow content"""
        script_dict = {'name': self.title,
                       'variables': self.vars_manager.config_data(),
                       'flow': self.flow.config_data()}

        return script_dict