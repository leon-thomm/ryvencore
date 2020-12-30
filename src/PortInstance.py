from PySide2.QtWidgets import QGraphicsItem, QGraphicsGridLayout, QGraphicsWidget, \
    QGraphicsLayoutItem
from PySide2.QtCore import Qt, QRectF, QPointF, QSizeF
from PySide2.QtGui import QFontMetricsF, QFont

from .PortInstanceInputWidgets import StdSpinBoxInputWidget, StdLineEditInputWidget_NoBorder, \
    StdLineEditInputWidget
from .global_tools.strings import get_longest_line, shorten
from .RC import PortPos, FlowAlg

from .FlowProxyWidget import FlowProxyWidget


class PortInstance(QGraphicsGridLayout):

    def __init__(self, parent_node_instance, io_pos, type_='', label_str=''):
        super(PortInstance, self).__init__()

        # GENERAL ATTRIBUTES
        self.val = None
        self.parent_node_instance = parent_node_instance
        self.io_pos = io_pos
        self.type_ = type_
        self.label_str = label_str
        self.connections = []  # connections stored here

        # gate/pin
        self.pin = PortInstPin(self, parent_node_instance)

        # label
        self.label = PortInstLabel(self, parent_node_instance)


    def setup_ui(self):
        pass  # reimplemented in subclasses

    def get_val(self):
        # Debugger.write('get value in', self.direction, 'port instance',
        #                self.parent_node_instance.inputs.index(
        #                         self) if self.direction == 'input' else self.parent_node_instance.outputs.index(self),
        #                     'of', self.parent_node_instance.parent_node.title)
        # Debugger.write('val is', self.val)
        pass

    def connected(self):
        pass

    def disconnected(self):
        pass

    def config_data(self):
        pass  # reimplemented


class InputPortInstance(PortInstance):
    def __init__(self, parent_node_instance, type_='', label_str='',
                 config_data=None, widget_name=None, widget_pos='besides'):

        super(InputPortInstance, self).__init__(parent_node_instance, PortPos.INPUT, type_, label_str)

        self.widget_name = widget_name
        self.widget_pos = widget_pos
        self.widget = None
        self.proxy: FlowProxyWidget = None

        if config_data is not None:
            self.create_widget()
            try:
                self.widget.set_data(config_data)
            except Exception as e:
                print('Exception while setting data in', self.parent_node_instance.parent_node.title,
                      'NodeInstance\'s input widget:', e, ' (was this intended?)')
        else:
            self.create_widget()

        self.setup_ui()

    def setup_ui(self):
        self.setSpacing(5)
        self.addItem(self.pin, 0, 0)
        self.setAlignment(self.pin, Qt.AlignVCenter | Qt.AlignLeft)
        self.addItem(self.label, 0, 1)
        self.setAlignment(self.label, Qt.AlignVCenter | Qt.AlignLeft)

        if self.widget is not None:
            if self.widget_pos == 'besides':
                self.addItem(self.proxy, 0, 2)
            elif self.widget_pos == 'below':
                self.addItem(self.proxy, 1, 0, 1, 2)
            self.setAlignment(self.proxy, Qt.AlignCenter)

    def create_widget(self, configuration=None):
        if (self.type_ and self.type_ == 'data') or (configuration and configuration['type'] == 'data'):

            params = (self, self.parent_node_instance)

            if self.widget_name is None:  # no input widget
                return
            elif self.widget_name == 'std line edit s':
                self.widget = StdLineEditInputWidget(params, size='small')
            elif self.widget_name == 'std line edit m' or self.widget_name == 'std line edit':
                self.widget = StdLineEditInputWidget(params)
            elif self.widget_name == 'std line edit l':
                self.widget = StdLineEditInputWidget(params, size='large')
            elif self.widget_name == 'std line edit s r':
                self.widget = StdLineEditInputWidget(params, size='small', resize=True)
            elif self.widget_name == 'std line edit m r':
                self.widget = StdLineEditInputWidget(params, resize=True)
            elif self.widget_name == 'std line edit l r':
                self.widget = StdLineEditInputWidget(params, size='large', resize=True)
            elif self.widget_name == 'std line edit s r nb':
                self.widget = StdLineEditInputWidget_NoBorder(params, size='small',
                                                              resize=True)
            elif self.widget_name == 'std line edit m r nb':
                self.widget = StdLineEditInputWidget_NoBorder(params,
                                                              resize=True)
            elif self.widget_name == 'std line edit l r nb':
                self.widget = StdLineEditInputWidget_NoBorder(params, size='large',
                                                              resize=True)
            elif self.widget_name == 'std spin box':
                self.widget = StdSpinBoxInputWidget(params)
            else:  # custom input widget
                self.widget = self.get_input_widget_class(self.widget_name)((self, self.parent_node_instance))

            self.proxy = FlowProxyWidget(self.parent_node_instance.flow, self.parent_node_instance)
            self.proxy.setWidget(self.widget)

    def get_input_widget_class(self, widget_name):
        """Returns the CLASS of a defined custom input widget by given name"""
        # custom_node_input_widget_classes = \
        #     self.parent_node_instance.flow.script.main_window.custom_node_input_widget_classes
        # widget_class = custom_node_input_widget_classes[self.parent_node_instance.parent_node][widget_name]
        # return widget_class
        return self.parent_node_instance.parent_node.custom_input_widgets[widget_name]

    def connected(self):
        """Disables the widget and causes update"""
        if self.widget:
            self.widget.setEnabled(False)
        if self.type_ == 'data':
            self.update()

    def disconnected(self):
        """Enables the widget again"""
        if self.widget:
            self.widget.setEnabled(True)

    def get_val(self):
        if len(self.connections) == 0:
            if self.widget:
                return self.widget.get_val()
            else:
                return None
        else:
            # Debugger.write('calling connected port for val')
            return self.connections[0].get_val()

    def update(self):
        """applies on INPUT; called NI externally (from another NI)"""
        if (self.parent_node_instance.is_active() and self.type_ == 'exec') or \
           not self.parent_node_instance.is_active():
            self.parent_node_instance.update(self.parent_node_instance.inputs.index(self))

    def config_data(self):
        data_dict = {'type': self.type_,
                     'label': self.label_str}

        has_widget = True if self.widget else False
        data_dict['has widget'] = has_widget
        if has_widget:
            data_dict['widget name'] = self.widget_name
            data_dict['widget data'] = None if self.type_ == 'exec' else self.widget.get_data()
            data_dict['widget position'] = self.widget_pos

        return data_dict


class OutputPortInstance(PortInstance):
    def __init__(self, parent_node_instance, type_='', label_str=''):
        super(OutputPortInstance, self).__init__(parent_node_instance, PortPos.OUTPUT, type_, label_str)

        self.setup_ui()

    def setup_ui(self):
        self.setSpacing(5)
        self.addItem(self.label, 0, 0)
        self.setAlignment(self.label, Qt.AlignVCenter | Qt.AlignRight)
        self.addItem(self.pin, 0, 1)

        self.setAlignment(self.pin, Qt.AlignVCenter | Qt.AlignRight)

    def exec(self):
        for c in self.connections:
            c.activate()

    def get_val(self):
        # Debugger.debug('returning val directly')
        if self.parent_node_instance.flow.alg_mode == FlowAlg.EXEC:
            self.parent_node_instance.update()
        return self.val

    def set_val(self, val):
        """applies on OUTPUT; called NI internally"""
        # Debugger.write('setting value of output port of', self.parent_node_instance.parent_node.title,
        #                     'NodeInstance to', val)

        # note that val COULD be of object type and therefore already changed (because the original object did)
        self.val = val

        # if algorithm mode would be exec flow, all data will be required instead of actively forward propagated
        if self.parent_node_instance.flow.alg_mode == FlowAlg.DATA and \
                not self.parent_node_instance.initializing:
            self.updated_val()

    def updated_val(self):
        """applies on DATA OUTPUT; called NI internally"""
        for c in self.connections:
            c.activate()

    def config_data(self):
        data_dict = {'type': self.type_,
                     'label': self.label_str}

        return data_dict


# CONTENTS -------------------------------------------------------------------------------------------------------------


class PortInstPin(QGraphicsWidget):
    def __init__(self, parent_port_instance, parent_node_instance):
        super(PortInstPin, self).__init__(parent_node_instance)

        self.setGraphicsItem(self)
        self.setAcceptHoverEvents(True)
        self.hovered = False
        self.setCursor(Qt.CrossCursor)
        self.tool_tip_pos = None

        self.parent_port_instance = parent_port_instance
        self.parent_node_instance = parent_node_instance
        self.padding = 2
        self.painting_width = 15
        self.painting_height = 15
        self.width = self.painting_width+2*self.padding
        self.height = self.painting_height+2*self.padding
        self.port_local_pos = None

    def boundingRect(self):
        return QRectF(QPointF(0, 0), self.geometry().size())

    def setGeometry(self, rect):
        self.prepareGeometryChange()
        QGraphicsLayoutItem.setGeometry(self, rect)
        self.setPos(rect.topLeft())

    def sizeHint(self, which, constraint=...):
        return QSizeF(self.width, self.height)

    def paint(self, painter, option, widget=None):
        self.parent_node_instance.session_design.flow_theme.node_inst_painter.paint_PI(
            painter, option, self.parent_node_instance.color,
            self.parent_port_instance.type_,
            len(self.parent_port_instance.connections) > 0,
            self.padding, self.painting_width, self.painting_height
        )

    def mousePressEvent(self, event):
        event.accept()

    def hoverEnterEvent(self, event):
        if self.parent_port_instance.type_ == 'data' and self.parent_port_instance.io_pos == PortPos.OUTPUT:
            self.setToolTip(shorten(str(self.parent_port_instance.val), 1000, line_break=True))

        # hover all connections
        # self.parent_node_instance.flow.hovered_port_inst_gate = self
        # self.parent_node_instance.flow.update()
        self.hovered = True

        QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):

        # turn connection highlighting off
        # self.parent_node_instance.flow.hovered_port_inst_gate = None
        # self.parent_node_instance.flow.update()
        self.hovered = False

        QGraphicsItem.hoverLeaveEvent(self, event)

    def get_scene_center_pos(self):
        return QPointF(self.scenePos().x() + self.boundingRect().width()/2,
                       self.scenePos().y() + self.boundingRect().height()/2)


class PortInstLabel(QGraphicsWidget):
    def __init__(self, parent_port_instance, parent_node_instance):
        super(PortInstLabel, self).__init__(parent_node_instance)
        self.setGraphicsItem(self)

        self.parent_port_instance = parent_port_instance
        self.parent_node_instance = parent_node_instance

        self.font = QFont("Source Code Pro", 10, QFont.Bold)
        font_metrics = QFontMetricsF(self.font)  # approximately! the designs can use different fonts
        self.width = font_metrics.width(get_longest_line(self.parent_port_instance.label_str))
        self.height = font_metrics.height() * (self.parent_port_instance.label_str.count('\n') + 1)
        self.port_local_pos = None

    def boundingRect(self):
        return QRectF(QPointF(0, 0), self.geometry().size())

    def setGeometry(self, rect):
        self.prepareGeometryChange()
        QGraphicsLayoutItem.setGeometry(self, rect)
        self.setPos(rect.topLeft())

    def sizeHint(self, which, constraint=...):
        return QSizeF(self.width, self.height)

    def paint(self, painter, option, widget=None):
        self.parent_node_instance.session_design.flow_theme.node_inst_painter.paint_PI_label(
            painter, option,
            self.parent_port_instance.type_,
            len(self.parent_port_instance.connections) > 0,
            self.parent_port_instance.label_str,
            self.parent_node_instance.color,
            self.boundingRect()
        )


