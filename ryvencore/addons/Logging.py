"""
WIP
"""

from logging import Logger as PyLogger
from typing import Optional

from ryvencore.AddOn import AddOn
from ryvencore.Base import Event


class Logger(PyLogger):

    def __init__(self, *args, **kwargs):
        PyLogger.__init__(self, *args, **kwargs)
    #     # events
        self.sig_enabled = Event()
        self.sig_disabled = Event()  # 'disabled' is reserved

    def enable(self):
        self.sig_enabled.emit()

    def disable(self):
        self.sig_disabled.emit()


class LoggingAddon(AddOn):
    """
    This addon implements some very basic logging functionality.

    It provides functions to create and delete loggers that are owned
    by a particular node. The loggers get enabled/disabled
    automatically when the owning node is added to/removed from
    the flow. When a node is serialized, its loggers are saved in
    the state dict of the flow, and when the node is deserialized,
    the loggers get recreated.

    Ownership might eventually be expanded to any component that
    preserves its global ID throughout save and load.

    The contents of logs are currently not preserved. If a log's
    content should be preserved, it should be saved explicitly.

    Refer to Python's logging module documentation.
    """

    name = 'Logging'
    version = '0.0.1'

    def __init__(self):
        super().__init__()

        # logger_created = Event(Logger)

        self.loggers = {}   # {Node: {name: Logger}}

        self.log_created = Event(Logger)
        # TODO: support deletion of loggers?

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
        self.log_created.emit(logger)
        return logger

    def get(self, node, title: str) -> Optional[Logger]:
        """
        Returns the logger with the given name owned by the node,
        or None if it doesn't exist.
        """

        if not self._node_is_registered(node):
            return None

        return self.loggers[node][title]

    def on_node_created(self, node):
        if node.load_data and 'Logging' in node.load_data:
            for title in node.load_data['Logging']['loggers']:
                self.new_logger(node, title)
                # in case the node already created the logger,
                # new_logger() will have no effect

    def _node_is_registered(self, node):
        return node in self.loggers

    def on_node_added(self, node):
        if not self._node_is_registered(node):
            return

        # enable the node's loggers
        for logger in self.loggers[node].values():
            logger.enable()

    def on_node_removed(self, node):
        if not self._node_is_registered(node):
            return

        # disable the node's loggers
        for logger in self.loggers[node].values():
            logger.disable()

    def extend_node_data(self, node, data: dict):
        if not self._node_is_registered(node):
            return

        data['Logging'] = {
            'loggers': [name for name in self.loggers[node].keys()]
        }

addon = LoggingAddon()
