import os

from PySide2.QtCore import Signal
from PySide2.QtGui import QFontMetrics, QColor
from PySide2.QtWidgets import QSpinBox, QLineEdit


from .WidgetBaseClasses import IWB
from .retain import M
# from custom_src.ryvencore.src.WidgetBaseClasses import IWB
# from custom_src.ryvencore.src.retain import M


class StdSpinBoxInputWidget(QSpinBox, IWB):

    trigger_update = Signal(int)

    def __init__(self, params):
        QSpinBox.__init__(self)
        IWB.__init__(self, params)

        self.trigger_update.connect(self.node.update)

        self.port_local_pos = None

        self.setFixedWidth(50)
        self.setFixedHeight(25)
        # self.setStyleSheet("""
        #     QSpinBox {
        #         color: white;
        #         background: transparent;
        #     }
        # """)
        self.setMaximum(1000000)
        self.editingFinished.connect(self.editing_finished)

    def editing_finished(self):
        # self.node.update(self.node.inputs.index(self.input))
        self.trigger_update.emit(self.node.inputs.index(self.input))

    def remove_event(self):
        pass

    def get_val(self):
        return self.value()

    def get_data(self):
        return self.value()

    def set_data(self, data):
        self.setValue(data)


class StdLineEditInputWidget(QLineEdit, IWB):

    trigger_update = Signal(int)

    def __init__(self, params, size='medium', resize=False):
        IWB.__init__(self, params)
        QLineEdit.__init__(self)

        self.trigger_update.connect(self.node.update)

        self.port_local_pos = None
        self.resizing = resize

        if size == 'small':
            self.base_width = 30
        elif size == 'medium':
            self.base_width = 70
        elif size == 'large':
            self.base_width = 150

        self.setFixedWidth(self.base_width)

        # self.setFixedHeight(25)
        self.setPlaceholderText('')

        # / *border - color: '''+self.node.color+'''; * /

        # c = QColor('#8c8c8c')
        # background_color = f'rgba({c.red()}, {c.green()}, {c.blue()}, 0.2)'

        if self.node.style == 'small':
            self.setStyleSheet('''
QLineEdit{
    padding: 1px 1px ;
    background: transparent;
}

            ''')
        else:
            self.setStyleSheet('''
QLineEdit{ 
    padding: 1px 1px ;
}
            ''')

        f = self.font()
        f.setPointSize(10)
        self.setFont(f)
        self.textChanged.connect(M(self.text_changed))
        self.editingFinished.connect(M(self.editing_finished))

    def text_changed(self, new_text):
        if self.resizing:
            fm = QFontMetrics(self.font())
            text_width = fm.width(new_text)
            new_width = text_width+15
            self.setFixedWidth(new_width if new_width > self.base_width else self.base_width)

            self.node.update_shape()
            # self.parent_node_instance.rebuild_ui()  # see rebuild_ui() for explanation

    def editing_finished(self):
        # self.node.update(self.node.inputs.index(self.input))
        self.trigger_update.emit(self.node.inputs.index(self.input))

    def remove_event(self):
        pass

    def get_val(self):
        val = None
        try:
            val = eval(self.text())
        except Exception as e:
            # type(eval(json.dumps(self.text()))) could be 'dict' <- need that for typing in dicts later if I want to
            val = self.text()
        return val

    def get_data(self):
        return self.text()

    def set_data(self, data):
        if type(data) == str:
            self.setText(data)

    def val_update_event(self, val):
        self.setText(str(val))


class StdLineEditInputWidget_NoBorder(StdLineEditInputWidget):
    def __init__(self, params, size='medium', resize=False):
        StdLineEditInputWidget.__init__(self, params, size, resize)

        c = QColor(self.node.color)

        hover_color = f'rgba({c.red()}, {c.green()}, {c.blue()}, 0.5)'

        self.setStyleSheet(self.styleSheet() + '''
QLineEdit {
    border: none;
}
QLineEdit:hover {
    background-color: '''+hover_color+''';
    border: none;
}
        ''')
