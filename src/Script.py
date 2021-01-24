import time

from PySide2.QtCore import QObject, Signal

from .AbstractFlow import AbstractFlow
from .Flow import Flow
from .logging.Logger import Logger
from .script_variables.VarsManager import VarsManager


class Script(QObject):

    # name_changed = Signal(str)  ->  Script()
    _create_flow_widget_request = Signal(object, tuple)
    _complete_nodes_config_request = Signal(list)
    _complete_connections_config_request = Signal(list)
    _generate_flow_widget_config_request = Signal()

    def __init__(self, session, title: str = None, content_data: dict = None, flow_size: list = None, gui_parent=None,
                 create_default_logs=True):
        super(Script, self).__init__(parent=session)

        self.session = session
        self.logger = Logger(self, create_default_logs)
        self.vars_manager = None
        self.title = title
        self.abstract_flow = AbstractFlow(self.session, self)
        self.flow_widget = None

        self.init_flow_config = content_data['flow'] if content_data is not None else None
        self.init_flow_widget_config = content_data['flow widget'] if content_data is not None else None
        self.init_flow_size = flow_size
        self.init_flow_gui_parent = gui_parent

        # TODO: move the thumbnail source to the list widget
        self._thumbnail_source = ''  # URL to the Script's thumbnail picture

        if self.session.threaded:
            self._create_flow_widget_request.connect(self.thread()._script_request__create_flow)
            if gui_parent is None:
                raise Exception(
                    "When using threading, you must provide a gui_parent."
                )

        flow_widget_params = (session, self, self.abstract_flow, self.init_flow_widget_config, flow_size, gui_parent)

        # TITLE, VARS MANAGER
        if content_data:
            self.title = content_data['name']
            self.vars_manager = VarsManager(self, content_data['variables'])
        else:
            self.vars_manager = VarsManager(self)

        # GUI
        if self.session.threaded:
            self._create_flow_request.emit(self, flow_widget_params)  # leads to flow_created trigger from SessionThread
        else:
            flow_widget = Flow(*flow_widget_params)
            self.flow_widget_created(flow_widget)


    def flow_widget_created(self, flow_widget):
        """Triggered from SessionThread if threading is enabled."""
        self.flow_widget = flow_widget

        self._complete_nodes_config_request.connect(self.flow_widget.complete_nodes_config_data)
        self._complete_connections_config_request.connect(self.flow_widget.complete_connections_config_data)
        self._generate_flow_widget_config_request.connect(self.flow_widget.generate_config_data)

        self.abstract_flow.load(config=self.init_flow_config)


    def content_data(self) -> dict:
        """Returns the config data of the script, including variables and flow content"""

        nodes_cfg, connections_cfg = self.abstract_flow.config_data()

        # complete nodes config
        self.flow_widget._temp_config_data = None
        self._complete_nodes_config_request.emit(nodes_cfg)
        while self.flow_widget._temp_config_data is None:
            time.sleep(0.001)
        nodes_cfg_complete = self.flow_widget._temp_config_data

        # complete connections config
        self.flow_widget._temp_config_data = None
        self._complete_connections_config_request.emit(connections_cfg)
        while self.flow_widget._temp_config_data is None:
            time.sleep(0.001)
        connections_cfg_complete = self.flow_widget._temp_config_data

        # flow widget config
        self.flow_widget._temp_config_data = None
        self._generate_flow_widget_config_request.emit()
        while self.flow_widget._temp_config_data is None:
            time.sleep(0.001)
        flow_widget_config = self.flow_widget._temp_config_data

        script_dict = {
            'name': self.title,
            'variables': self.vars_manager.config_data(),
            'flow': {
                'nodes': nodes_cfg_complete,
                'connections': connections_cfg_complete
            },
            'flow widget config': flow_widget_config}

        return script_dict
