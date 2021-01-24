from PySide2.QtCore import QObject, Signal

from .Flow import Flow
from .logging.Logger import Logger
from .script_variables.VarsManager import VarsManager


class Script(QObject):

    # name_changed = Signal(str)  ->  Script()
    _create_flow_request = Signal(object, tuple)

    def __init__(self, session, title: str = None, config: dict = None, flow_size: list = None, gui_parent=None,
                 create_default_logs=True):
        super(Script, self).__init__(parent=session)

        self.session = session
        self.logger = Logger(self, create_default_logs)
        self.vars_manager = None
        self.title = title
        self.flow = None

        # TODO: move the thumbnail source to the list widget
        self._thumbnail_source = ''  # URL to the Script's thumbnail picture

        if self.session.threaded:
            self._create_flow_request.connect(self.thread()._script_request__create_flow)
            if gui_parent is None:
                raise Exception(
                    "When using threading, you must provide a gui_parent."
                )

        flow_params = ()
        if config:
            self.title = config['name']
            self.vars_manager = VarsManager(self, config['variables'])

            flow_params = (session, self, flow_size, config['flow'], gui_parent)
        else:
            self.vars_manager = VarsManager(self)

            flow_params = (session, self, flow_size, gui_parent)

        # GUI
        if self.session.threaded:
            self._create_flow_request.emit(self, flow_params)  # leads to flow_created trigger
        else:
            self.flow = Flow(*flow_params)


    def flow_created(self, flow):
        """Triggered from SessionThread if threading is enabled."""
        self.flow = flow

    def config_data(self) -> dict:
        """Returns the config data of the script, including variables and flow content"""
        script_dict = {'name': self.title,
                       'variables': self.vars_manager.config_data(),
                       'flow': self.flow.config_data()}

        return script_dict
