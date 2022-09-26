'''

--------------------------------------------    LOGGER    --------------------------------------------

from logging import Logger as PyLogger
from ryvencore.Base import Base, Event


class Logger(Base, PyLogger):
    """
    A small wrapper template for the python loggers to add functionality on node events.
    Reimplemented as wrapper by the frontend with according implementations of the below methods.
    """

    def __init__(self, *args, **kwargs):
        Base.__init__(self)
        PyLogger.__init__(self, *args, **kwargs)

        # events
        self.sig_enabled = Event()
        self.sig_disabled = Event()

    def enable(self):
        self.sig_enabled.emit()

    def disable(self):
        self.sig_disabled.emit()


--------------------------------------------    LOGS MANAGER    --------------------------------------------

from ryvencore.Base import Base, Event
from .Logger import Logger


class LogsManager(Base):
    """Manages all logs/loggers that belong to the script."""

    def __init__(self, script, create_default_logs=True):
        Base.__init__(self)

        # events
        self.new_logger_created = Event(Logger)

        self.script = script
        self.session = self.script.session
        self.loggers: [Logger] = []
        self.default_loggers = {
            'global': None,
            'errors': None,
        }

        if create_default_logs:
            self.create_default_loggers()

    def create_default_loggers(self):
        for name in self.default_loggers.keys():
            self.default_loggers[name] = self.new_logger(title=name.title())

    def new_logger(self, title: str) -> Logger:
        # logger = self.session.CLASSES['logger'](name=title)
        logger = Logger(name=title)
        self.loggers.append(logger)
        self.new_logger_created.emit(logger)
        return logger

'''

from ryvencore.AddOn import AddOn

class Logger:
    pass

class LoggingAddon(AddOn):
    """
    This addon implements some logging functionality for nodes.

    It provides an API to create and delete loggers, either owned by a node,
    or owned by a flow.
    """

    name = 'Logging'
    version = '0.0.1'

    class NodeExtensions(...):

        @staticmethod
        def after_placement(node):
            ...

        @staticmethod
        def prepare_removal(node):
            ...




    def __init__(self):
        super().__init__()

        # self.loggers = ...


    # def new_logger(self, title) -> Logger:
    #     """Requesting a new custom Log"""
    #
    #     logger = self.script.logs_manager.new_logger(title)
    #     self.loggers.append(logger)
    #     return logger


# TODO: Logging.py
