from PySide2.QtWidgets import QGraphicsItem, QGraphicsGridLayout, QGraphicsWidget, \
    QGraphicsLayoutItem
from PySide2.QtCore import Qt, QRectF, QPointF, QSizeF
from PySide2.QtGui import QFontMetricsF, QFont

from .PortItemInputWidgets import StdSpinBoxInputWidget, StdLineEditInputWidget_NoBorder, \
    StdLineEditInputWidget
from .global_tools.strings import get_longest_line, shorten

from .FlowProxyWidget import FlowProxyWidget


class PortItem(QGraphicsGridLayout):

    def __init__(self, node, port, flow):
        super(PortItem, self).__init__()

        self.node = node
        self.port = port
        self.flow = flow

        self.port.has_been_connected.connect(self.port_connected)
        self.port.has_been_disconnected.connect(self.port_disconnected)

        self.pin = PortItemPin(self.port, self.node)

        self.label = PortItemLabel(self.port, self.node)


    def setup_ui(self):
        pass

    def port_connected(self):
        pass

    def port_disconnected(self):
        pass


class InputPortItem(PortItem):
    def __init__(self, node, port):
        super().__init__(node, port, node.flow)

        self.widget = None
        self.proxy: FlowProxyWidget = None

        if self.port.widget_config_data is not None:
            self.create_widget()
            try:
                self.widget.set_data(self.port.widget_config_data)
            except Exception as e:
                print('Exception while setting data in', self.node.title,
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
            if self.port.widget_pos == 'besides':
                self.addItem(self.proxy, 0, 2)
            elif self.port.widget_pos == 'below':
                self.addItem(self.proxy, 1, 0, 1, 2)
            self.setAlignment(self.proxy, Qt.AlignCenter)

    def create_widget(self, configuration=None):
        if (self.port.type_ and self.port.type_ == 'data') or (configuration and configuration['type'] == 'data'):

            wn = self.port.widget_name

            params = (self.port, self.node)

            if wn is None:  # no input widget
                return
            elif wn == 'std line edit s':
                self.widget = StdLineEditInputWidget(params, size='small')
            elif wn == 'std line edit m' or wn == 'std line edit':
                self.widget = StdLineEditInputWidget(params)
            elif wn == 'std line edit l':
                self.widget = StdLineEditInputWidget(params, size='large')
            elif wn == 'std line edit s r':
                self.widget = StdLineEditInputWidget(params, size='small', resize=True)
            elif wn == 'std line edit m r':
                self.widget = StdLineEditInputWidget(params, resize=True)
            elif wn == 'std line edit l r':
                self.widget = StdLineEditInputWidget(params, size='large', resize=True)
            elif wn == 'std line edit s r nb':
                self.widget = StdLineEditInputWidget_NoBorder(params, size='small',
                                                              resize=True)
            elif wn == 'std line edit m r nb':
                self.widget = StdLineEditInputWidget_NoBorder(params,
                                                              resize=True)
            elif wn == 'std line edit l r nb':
                self.widget = StdLineEditInputWidget_NoBorder(params, size='large',
                                                              resize=True)
            elif wn == 'std spin box':
                self.widget = StdSpinBoxInputWidget(params)
            else:  # custom input widget
                self.widget = self.get_input_widget_class(wn)(params)

            self.proxy = FlowProxyWidget(self.flow, parent=self.node.item)
            self.proxy.setWidget(self.widget)

    def get_input_widget_class(self, widget_name):
        """Returns the CLASS of a defined custom input widget"""
        return self.node.input_widget_classes[widget_name]

    def port_connected(self):
        """Disables the widget"""
        if self.widget:
            self.widget.setEnabled(False)

    def port_disconnected(self):
        """Enables the widget again"""
        if self.widget:
            self.widget.setEnabled(True)


class OutputPortItem(PortItem):
    def __init__(self, node, port):
        super().__init__(node, port, node.flow)
        # super(OutputPortItem, self).__init__(parent_node_instance, PortObjPos.OUTPUT, type_, label_str)

        self.setup_ui()

    def setup_ui(self):
        self.setSpacing(5)
        self.addItem(self.label, 0, 0)
        self.setAlignment(self.label, Qt.AlignVCenter | Qt.AlignRight)
        self.addItem(self.pin, 0, 1)

        self.setAlignment(self.pin, Qt.AlignVCenter | Qt.AlignRight)


# CONTENTS -------------------------------------------------------------------------------------------------------------


class PortItemPin(QGraphicsWidget):
    def __init__(self, port, node):
        super(PortItemPin, self).__init__(node.item)

        self.port = port
        self.node = node
        self.node_item = node.item

        self.setGraphicsItem(self)
        self.setAcceptHoverEvents(True)
        self.hovered = False
        self.setCursor(Qt.CrossCursor)
        self.tool_tip_pos = None

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
        self.node_item.session_design.flow_theme.node_item_painter.paint_PI(
            painter, option, self.node_item.color,
            self.port.type_,
            len(self.port.connections) > 0,
            self.padding, self.painting_width, self.painting_height
        )

    def mousePressEvent(self, event):
        event.accept()

    def hoverEnterEvent(self, event):
        if self.port.type_ == 'data':  # and self.parent_port_instance.io_pos == PortPos.OUTPUT:
            self.setToolTip(shorten(str(self.port.val), 1000, line_break=True))

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


class PortItemLabel(QGraphicsWidget):
    def __init__(self, port, node):
        super(PortItemLabel, self).__init__(node.item)
        self.setGraphicsItem(self)

        self.port = port
        self.node = node
        self.node_item = node.item

        self.font = QFont("Source Code Pro", 10, QFont.Bold)
        font_metrics = QFontMetricsF(self.font)  # approximately! the designs can use different fonts
        self.width = font_metrics.width(get_longest_line(self.port.label_str))
        self.height = font_metrics.height() * (self.port.label_str.count('\n') + 1)
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
        self.node_item.session_design.flow_theme.node_item_painter.paint_PI_label(
            painter, option,
            self.port.type_,
            len(self.port.connections) > 0,
            self.port.label_str,
            self.node_item.color,
            self.boundingRect()
        )
