import time

from PySide2.QtCore import QObject, Signal

from .Flow import Flow
from .FlowView import FlowView
from .SessionThread import SessionThread
from .logging.Logger import Logger
from .script_variables.VarsManager import VarsManager


class Script(QObject):

    create_flow_view_request = Signal(object, tuple)
    generate_flow_view_config_request = Signal()

    def __init__(self, session, title: str = None, content_data: dict = None, flow_size: list = None, gui_parent=None,
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
        self.init_flow_gui_parent = gui_parent

        # TODO: move the thumbnail source to the list widget
        self._thumbnail_source = ''  # URL to the Script's thumbnail picture

        if self.session.threaded:
            t: SessionThread = self.thread()
            self.create_flow_view_request.connect(t.script_request__create_flow_view)
            if gui_parent is None:
                raise Exception(
                    "When using threading, you must provide a gui_parent."
                )

        flow_view_params = (session, self, self.flow, self.init_flow_view_config, flow_size, gui_parent)

        # TITLE, VARS MANAGER
        if content_data:
            self.title = content_data['name']
            self.vars_manager = VarsManager(self, content_data['variables'])
        else:
            self.vars_manager = VarsManager(self)

        # GUI
        if self.session.threaded:
            t: SessionThread = self.thread()
            print('connecting to SessionThread')
            t.flow_view_created.connect(self.flow_view_created)

            print('emitting create_flow_view_request')
            self.create_flow_view_request.emit(self, flow_view_params)
            # --> flow_view_created
        else:
            flow_view = FlowView(*flow_view_params)
            self.flow_view_created(flow_view)


    def flow_view_created(self, flow_view):
        """Triggered from SessionThread if threading is enabled."""

        print('RECEIVED!')
        return

        t: SessionThread = self.thread()
        t.flow_view_created.disconnect(self.flow_view_created)

        self.flow_view = flow_view

        self.generate_flow_view_config_request.connect(self.flow_view.generate_config_data)

        if self.init_flow_config is not None:
            self.flow.load(config=self.init_flow_config)


    def content_data(self) -> dict:
        """Returns the config data of the script, including variables and flow content"""

        # the flow widget currently creates the whole config
        self.flow_view._temp_config_data = None
        self.generate_flow_view_config_request.emit()
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
