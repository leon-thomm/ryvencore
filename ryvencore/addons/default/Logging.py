"""
WIP
"""

from logging import Logger as PyLogger
from typing import Optional

from ryvencore.AddOn import AddOn


class Logger(PyLogger):

    def __init__(self, *args, **kwargs):
        PyLogger.__init__(self, *args, **kwargs)
    #     # events
    #     self.sig_enabled = Event()
    #     self.sig_disabled = Event()

    def enable(self):
        # self.sig_enabled.emit()
        pass

    def disable(self):
        # self.sig_disabled.emit()
        pass


class LoggingAddon(AddOn):
    """
    This addon implements very basic some logging functionality.

    It provides an API to create and delete loggers that are owned
    by a particular node. The logger gets enabled/disabled
    automatically when the owning node is added to/removed from
    the flow.

    Ownership might eventually be expanded to any component that
    preserves its global ID throughout save and load.

    The contents of logs are currently not preserved. If a log's
    content should be preserved, it should be saved in a file.

    Refer to Python's logging module documentation.
    """

    name = 'Logging'
    version = '0.0.1'

    def __init__(self):
        super().__init__()

        # logger_created = Event(Logger)

        self.loggers = {}   # {Node: {name: Logger}}

    def new_logger(self, node, title: str) -> Optional[Logger]:
        """
        Creates a new logger owned by the node, returns None if
        one with the given name already exists.
        """

        if not self._node_is_registered(node):
            self.loggers[node] = {}

        elif title in self.loggers[node]:
            return None

        logger = Logger(name=title)
        self.loggers[node][title] = logger
        # self.logger_created.emit(logger)
        return logger

    def _on_node_created(self, flow, node):
        if node.init_data and 'Logging' in node.init_data:
            for title in node.init_data['Logging']['loggers']:
                self.new_logger(node, title)
                # in case the node already created the logger,
                # new_logger() will have no effect

    def _node_is_registered(self, node):
        return node in self.loggers

    def _on_node_added(self, flow, node):
        if not self._node_is_registered(node):
            return

        # enable the node's loggers
        for logger in self.loggers[node].values():
            logger.enable()

    def _on_node_removed(self, flow, node):
        if not self._node_is_registered(node):
            return

        # disable the node's loggers
        for logger in self.loggers[node].values():
            logger.disable()

    def _extend_node_data(self, node, data: dict):
        if not self._node_is_registered(node):
            return

        data['Logging'] = {
            'loggers': [name for name in self.loggers[node].keys()]
        }

addon = LoggingAddon()
