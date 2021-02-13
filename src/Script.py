import time

from PySide2.QtCore import QObject, Signal

from .Flow import Flow
from .FlowView import FlowView
from .SessionThreadingBridge import SessionThreadingBridge
from .logging.Logger import Logger
from .script_variables.VarsManager import VarsManager


class Script(QObject):

    create_flow_view_request = Signal(object, tuple)
    generate_flow_view_config_request = Signal(dict)

    def __init__(self, session, title: str = None, content_data: dict = None, flow_size: list = None,
                 create_default_logs=True):
        super(Script, self).__init__(parent=session)

        self.session = session
        self.logger = Logger(self, create_default_logs)
        self.vars_manager = None
        self.title = title
        self.flow = Flow(self.session, self, self)
        self.flow_view = None

        self.init_flow_config = None
        self.init_flow_view_config = None
        if content_data:
            self.init_flow_config = content_data['flow'] if content_data is not None else None
            if 'flow widget config' in content_data:
                self.init_flow_view_config = content_data['flow widget config'] if content_data is not None else None
            else:  # backwards compatibility
                self.init_flow_view_config = content_data['flow']

        self.init_flow_size = flow_size
        self.init_flow_gui_parent = self.session.gui_parent

        # TODO: move the thumbnail source to the list widget
        self._thumbnail_source = ''  # URL to the Script's thumbnail picture

        if self.session.threaded:
            self.create_flow_view_request.connect(
                self.session.threading_bridge.script_request__create_flow_view
            )
            self.tmp_data = None

            if self.session.gui_parent is None:
                raise Exception(
                    "When using threading, you must provide a gui_parent."
                )

        flow_view_params = (session, self, self.flow, self.init_flow_view_config, flow_size, self.session.gui_parent)

        # TITLE, VARS MANAGER
        if content_data:
            self.title = content_data['name']
            self.vars_manager = VarsManager(self, content_data['variables'])
        else:
            self.vars_manager = VarsManager(self)

        # GUI
        if self.session.threaded:
            self.create_flow_view_request.emit(self, flow_view_params)
            while self.tmp_data is None:
                time.sleep(0.001)
            flow_view = self.tmp_data
        else:
            flow_view = FlowView(*flow_view_params)
        self.flow_view_created(flow_view)


    def flow_view_created(self, flow_view):

        self.flow_view = flow_view

        self.generate_flow_view_config_request.connect(self.flow_view.generate_config_data)

        if self.init_flow_config is not None:
            self.flow.load(config=self.init_flow_config)


    def serialize(self) -> dict:
        """Returns the config data of the script, including variables and flow content"""

        abstract_flow_data = self.flow.generate_config_data()
        self.generate_flow_view_config_request.emit(abstract_flow_data)

        # # the flow widget currently creates the whole config
        # self.flow_view._temp_config_data = None
        # self.generate_flow_view_config_request.emit()
        while self.flow_view._temp_config_data is None:
            time.sleep(0.001)  # join threads
        flow_config, flow_view_config = self.flow_view._temp_config_data

        script_dict = {
            'name': self.title,
            'variables': self.vars_manager.config_data(),
            'flow': flow_config,
            'flow widget config': flow_view_config
        }

        return script_dict
