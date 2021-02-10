from PySide2.QtCore import QPointF, QRectF, Qt
from PySide2.QtWidgets import QGraphicsWidget, QGraphicsLinearLayout

from .FlowProxyWidget import FlowProxyWidget
# from .Node import Node
from .NodeItem_TitleLabel import TitleLabel
from .PortItem import InputPortItem, OutputPortItem


class NodeItemWidget(QGraphicsWidget):
    def __init__(self, node, node_item):
        super().__init__(parent=node_item)

        self.node = node
        self.node_item = node_item
        self.flow_view = self.node_item.flow_view

        self.title_label = TitleLabel(node, node_item)
        self.main_widget_proxy: FlowProxyWidget = None
        if self.node_item.main_widget:
            self.main_widget_proxy = FlowProxyWidget(self.flow_view)
            self.main_widget_proxy.setWidget(self.node_item.main_widget)
        self.body_layout: QGraphicsLinearLayout = None
        self.inputs_layout: QGraphicsLinearLayout = None
        self.outputs_layout: QGraphicsLinearLayout = None
        self.setLayout(self.setup_layout())

    def setup_layout(self) -> QGraphicsLinearLayout:

        #   main layout
        layout = QGraphicsLinearLayout(Qt.Vertical)
        layout.setSpacing(10)

        if self.node.style == 'extended':
            layout.addItem(self.title_label)
            layout.setAlignment(self.title_label, Qt.AlignTop)
        else:
            self.setZValue(self.title_label.zValue()+1)

        #   inputs
        self.inputs_layout = QGraphicsLinearLayout(Qt.Vertical)
        self.inputs_layout.setSpacing(2)

        #   outputs
        self.outputs_layout = QGraphicsLinearLayout(Qt.Vertical)
        self.outputs_layout.setSpacing(2)

        #   body
        self.body_layout = QGraphicsLinearLayout(Qt.Horizontal)

        self.body_layout.setSpacing(4)
        self.body_layout.addItem(self.inputs_layout)
        self.body_layout.setAlignment(self.inputs_layout, Qt.AlignVCenter | Qt.AlignLeft)
        self.body_layout.addStretch()
        self.body_layout.addItem(self.outputs_layout)
        self.body_layout.setAlignment(self.outputs_layout, Qt.AlignVCenter | Qt.AlignRight)


        # if self.node_item.main_widget:
        #     self.main_widget_proxy = FlowProxyWidget(self.flow)
        #     self.main_widget_proxy.setWidget(self.node_item.main_widget)
        #
        #     if self.node.main_widget_pos == 'between ports':
        #         self.body_layout.insertItem(1, self.main_widget_proxy)
        #         self.body_layout.insertStretch(2)
        #         layout.addItem(self.body_layout)
        #
        #     elif self.node.main_widget_pos == 'below ports':
        #         layout.addItem(self.body_layout)
        #         layout.addItem(self.main_widget_proxy)
        #         layout.setAlignment(self.main_widget_proxy, Qt.AlignHCenter)
        # else:
        #     layout.addItem(self.body_layout)

        layout.addItem(self.body_layout)

        return layout

    def rebuild_ui(self):
        """Due to some really strange and annoying behaviour of these QGraphicsWidgets, they don't want to shrink
        automatically when content is removed, they just stay large, even with a Minimum SizePolicy. I didn't find a
        way around that yet, so for now I have to recreate the whole layout and make sure the widget uses the smallest
        size possible."""

        # if I don't manually remove the ports from the layouts,
        # they get deleted when setting the widget's layout to None below
        for i in range(len(self.node.inputs)):
            self.inputs_layout.removeAt(0)
        for i in range(len(self.node.outputs)):
            self.outputs_layout.removeAt(0)

        self.setLayout(None)
        self.resize(self.minimumSize())
        self.setLayout(self.setup_layout())

        for inp in self.node.inputs:
            self.add_input_to_layout(inp.item)
        for out in self.node.outputs:
            self.add_output_to_layout(out.item)

        if self.node_item.main_widget:
            self.add_main_widget_to_layout()

    def update_shape(self):

        # makes extended node items shrink according to resizing input widgets
        if not self.node_item.initializing:
            self.rebuild_ui()
        # strangely, this only works for small node items without this, not for extended ones

        mw = self.node_item.main_widget
        if mw is not None:  # maybe the main_widget got resized
            self.main_widget_proxy.setMaximumSize(mw.size())
            self.adjustSize()
            self.adjustSize()

        self.body_layout.invalidate()
        self.layout().invalidate()
        self.layout().activate()
        # very essential; repositions everything in case content has changed (inputs/outputs/widget)

        if self.node.style == 'small':

            # making it recompute its true minimumWidth here
            self.adjustSize()

            if self.layout().minimumWidth() < self.title_label.width + 15:
                self.layout().setMinimumWidth(self.title_label.width + 15)
                self.layout().activate()

        w = self.boundingRect().width()
        h = self.boundingRect().height()
        rect = QRectF(QPointF(-w / 2, -h / 2),
                      QPointF(w / 2, h / 2))
        self.setPos(rect.left(), rect.top())

        if not self.node.style == 'extended':
            self.title_label.setPos(QPointF(-self.title_label.boundingRect().width() / 2,
                                            -self.title_label.boundingRect().height() / 2))

    def add_main_widget_to_layout(self):
        if self.node.main_widget_pos == 'between ports':
            self.body_layout.insertItem(1, self.main_widget_proxy)
            self.body_layout.insertStretch(2)

        elif self.node.main_widget_pos == 'below ports':
            self.layout().addItem(self.main_widget_proxy)
            self.layout().setAlignment(self.main_widget_proxy, Qt.AlignHCenter)

    def add_input_to_layout(self, inp: InputPortItem):
        if self.inputs_layout.count() > 0:
            self.inputs_layout.addStretch()
        self.inputs_layout.addItem(inp)
        self.inputs_layout.setAlignment(inp, Qt.AlignLeft)

    def insert_input_into_layout(self, index: int, inp: InputPortItem):
        self.inputs_layout.insertItem(index*2+1, inp)   # *2 bcs of the stretches
        self.inputs_layout.setAlignment(inp, Qt.AlignLeft)
        if len(self.node.inputs) > 1:
            self.inputs_layout.insertStretch(index*2+1)  # *2+1 because of the stretches, too

    def remove_input_from_layout(self, inp: InputPortItem):
        self.inputs_layout.removeItem(inp)

        # just a temporary workaround for the issues discussed here:
        # https://forum.qt.io/topic/116268/qgraphicslayout-not-properly-resizing-to-change-of-content
        self.rebuild_ui()

    def add_output_to_layout(self, out: OutputPortItem):
        if self.outputs_layout.count() > 0:
            self.outputs_layout.addStretch()
        self.outputs_layout.addItem(out)
        self.outputs_layout.setAlignment(out, Qt.AlignRight)

    def insert_output_into_layout(self, index: int, out: OutputPortItem):
        self.outputs_layout.insertItem(index*2+1, out)  # *2 because of the stretches
        self.outputs_layout.setAlignment(out, Qt.AlignRight)
        if len(self.node.outputs) > 1:
            self.outputs_layout.insertStretch(index*2+1)  # *2+1 because of the stretches, too

    def remove_output_from_layout(self, out: OutputPortItem):
        self.outputs_layout.removeItem(out)

        # just a temporary workaround for the issues discussed here:
        # https://forum.qt.io/topic/116268/qgraphicslayout-not-properly-resizing-to-change-of-content
        self.rebuild_ui()
