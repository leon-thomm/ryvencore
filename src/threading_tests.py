import sys

from PySide2.QtWidgets import QMainWindow, QApplication
from PySide2.QtCore import QObject, Signal, QThread


class ThreadBridge(QObject):

    done = Signal()

    def do_something(self):
        self.done.emit()


class Controller(QObject):

    some_request = Signal()

    def __init__(self, main_thread):
        super().__init__()
        self.bridge = ThreadBridge()
        self.bridge.moveToThread(main_thread)

    def create(self):
        self.some_request.connect(self.bridge.do_something)
        self.bridge.done.connect(self.finish)
        self.some_request.emit()

    def finish(self):
        print('success!')


class MainWindow(QMainWindow):
    init_controller_signal = Signal()

    def __init__(self):
        super().__init__()

        self.controller_thread = QThread(self)
        self.controller_thread.start()

        self.controller = Controller(self.thread())
        self.init_controller_signal.connect(self.controller.create)
        self.controller.moveToThread(self.controller_thread)
        self.init_controller_signal.emit()


if __name__ == "__main__":
    app = QApplication()
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
