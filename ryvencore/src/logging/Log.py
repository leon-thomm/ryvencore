from PySide2.QtCore import QObject, Signal


class Log(QObject):

    # TODO: add methods for saving data to a file

    enabled = Signal()
    disabled = Signal()
    wrote = Signal(str)
    cleared = Signal()

    def __init__(self, title: str):
        super(Log, self).__init__()

        self.title: str = title
        self.lines: [str] = []
        self.enabled_: bool = True

    def write(self, *args):
        if not self.enabled_:
            return

        s = ''
        for arg in args:
            s += ' '+str(arg)
        self.lines.append(s)
        self.wrote.emit(s)

    def clear(self):
        self.cleared.emit()

    def disable(self):
        self.enabled_ = False
        self.disabled.emit()

    def enable(self):
        self.enabled_ = True
        self.enabled.emit()