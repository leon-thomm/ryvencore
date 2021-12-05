from .Base import Base
from .logging import LogsManager
from .script_variables import VarsManager
from .Flow import Flow


class Script(Base):
    """A Script consists of a Flow, a VarsManager and a Logger object."""

    def __init__(self, session, title: str = None, load_data: dict = None, create_default_logs=True):
        Base.__init__(self)

        self.session = session
        self.logs_manager = None
        self._create_default_logs = create_default_logs
        self.vars_manager = None
        self.title = title
        self.flow = None

        if title is None and load_data is not None:
            self.title = load_data['title'] \
                if 'title' in load_data else load_data['name']  # backwards compatibility

        self.init_data = load_data
        self.init_flow_data = None
        self.init_vars_manager_data = None

        # loading from saved data
        if load_data:
            self.init_flow_data = load_data['flow'] if load_data else None
            self.init_vars_manager_data = load_data['variables']

        # logging
        self.logs_manager = LogsManager(self, self._create_default_logs)

        # vars manager
        self.vars_manager = VarsManager(self, self.init_vars_manager_data)

        # flow
        self.flow = Flow(self.session, self)


    def load_flow(self):
        if self.init_flow_data:
            self.flow.load(self.init_flow_data)


    def data(self) -> dict:
        return {
            'title': self.title,
            'variables': self.vars_manager.data(),
            'flow': self.flow.data(),
            'GID': self.GLOBAL_ID,
        }
