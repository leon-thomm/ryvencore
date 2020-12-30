from PySide2.QtCore import QObject, Signal

from .Flow import Flow
from .RC import FlowVPUpdateMode, FlowAlg
from .logging.Logger import Logger
from .script_variables.VarsManager import VarsManager


class Script(QObject):

    # name_changed = Signal(str)  ->  Script()

    def __init__(self, session, title: str = None, config: dict = None, flow_size: list = None, flow_parent=None,
                 create_default_logs=True):
        super(Script, self).__init__()

        self.session = session
        self.logger = Logger(self, create_default_logs)
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

    def config_data(self) -> dict:
        """Returns the config data of the script, including variables and flow content"""
        script_dict = {'name': self.title,
                       'variables': self.vars_manager.config_data(),
                       'flow': self.flow.config_data()}

        return script_dict