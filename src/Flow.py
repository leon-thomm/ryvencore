from PySide2.QtCore import Qt, QPointF, QPoint, QRectF, QSizeF, Signal, QTimer, QObject
from PySide2.QtGui import QPainter, QPen, QColor, QKeySequence, QTabletEvent, QImage, QGuiApplication, QFont
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QShortcut, QMenu, QGraphicsItem, QUndoStack

from .FlowCommands import MoveComponents_Command, PlaceNodeItemInScene_Command, \
    PlaceDrawingObject_Command, RemoveComponents_Command, ConnectPorts_Command, Paste_Command
from .FlowProxyWidget import FlowProxyWidget
from .FlowStylusModesWidget import FlowStylusModesWidget
from .FlowWorkerThread import FlowWorkerThread
from .FlowZoomWidget import FlowZoomWidget
from .Node import Node
from .NodeObjPort import NodeObjPort, NodeObjOutput, NodeObjInput
from .node_choice_widget.NodeChoiceWidget import NodeChoiceWidget
from .NodeItem import NodeItem
from .PortItem import PortItem, PortItemPin
from .Connection import Connection
from .ConnectionItem import default_cubic_connection_path
from .DrawingObject import DrawingObject
from .global_tools.Debugger import Debugger
from .RC import PortObjPos, FlowAlg
from .RC import FlowVPUpdateMode as VPUpdateMode

import json


class Flow(QGraphicsView):
    """Manages all GUI of flows"""

    nodes_selection_changed = Signal(list)
    algorithm_mode_changed = Signal(str)
    viewport_update_mode_changed = Signal(str)
    trigger_port_connected = Signal(NodeObjPort)
    trigger_port_disconnected = Signal(NodeObjPort)


    def __init__(self, session, script, flow_size: list = None, config=None, parent=None):
        super(Flow, self).__init__(parent=parent)


        # UNDO/REDO
        self._undo_stack = QUndoStack(self)
        self._undo_action = self._undo_stack.createUndoAction(self, 'undo')
        self._undo_action.setShortcuts(QKeySequence.Undo)
        self._redo_action = self._undo_stack.createRedoAction(self, 'redo')
        self._redo_action.setShortcuts(QKeySequence.Redo)

        # SHORTCUTS
        self._init_shortcuts()

        # GENERAL ATTRIBUTES
        self.script = script
        self.session = session
        self.node_items: [NodeItem] = []
        self.nodes: [Node] = []
        # self.connection_items = []
        self.connections: [Connection] = []
        self.selected_pin: PortItemPin = None
        self.dragging_connection = False
        self.ignore_mouse_event = False  # for stylus - see tablet event
        self._showing_framerate = False
        self._last_mouse_move_pos: QPointF = None
        self._node_place_pos = QPointF()
        self._left_mouse_pressed_in_flow = False
        self._mouse_press_pos: QPointF = None
        self._auto_connection_pin = None  # stores the gate that we may try to auto connect to a newly placed NI
        self._panning = False
        self._pan_last_x = None
        self._pan_last_y = None
        self._current_scale = 1
        self._total_scale_div = 1

        if self.session.threading_enabled:
            self.worker_thread = FlowWorkerThread(self.thread())
            FWT = self.worker_thread
            self.trigger_port_connected.connect(FWT.interface.trigger_port_connected)
            self.trigger_port_disconnected.connect(FWT.interface.trigger_port_disconnected)
            self.worker_thread.start()

        # SETTINGS
        self.alg_mode = FlowAlg.DATA    # Flow_AlgorithmMode()
        self.vp_update_mode: VPUpdateMode = VPUpdateMode.SYNC  # Flow_ViewportUpdateMode()

        # CREATE UI
        scene = QGraphicsScene(self)
        scene.setItemIndexMethod(QGraphicsScene.NoIndex)
        if flow_size is None:
            scene.setSceneRect(0, 0, 10 * self.width(), 10 * self.height())
        else:
            scene.setSceneRect(0, 0, flow_size[0], flow_size[1])

        self.setScene(scene)
        self.setCacheMode(QGraphicsView.CacheBackground)
        self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        scene.selectionChanged.connect(self._scene_selection_changed)
        self.setAcceptDrops(True)

        self.centerOn(QPointF(self.viewport().width() / 2, self.viewport().height() / 2))

        # NODE CHOICE WIDGET
        self._node_choice_proxy = FlowProxyWidget(self)
        self._node_choice_proxy.setZValue(1000)
        self._node_choice_widget = NodeChoiceWidget(self, self.session.nodes)  # , main_window.node_images)
        self._node_choice_proxy.setWidget(self._node_choice_widget)
        self.scene().addItem(self._node_choice_proxy)
        self.hide_node_choice_widget()

        # ZOOM WIDGET
        self._zoom_proxy = FlowProxyWidget(self)
        self._zoom_proxy.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._zoom_proxy.setZValue(1001)
        self._zoom_widget = FlowZoomWidget(self)
        self._zoom_proxy.setWidget(self._zoom_widget)
        self.scene().addItem(self._zoom_proxy)
        self.set_zoom_proxy_pos()

        # STYLUS
        self.stylus_mode = ''
        self._current_drawing = None
        self._drawing = False
        self.drawings = []
        self._stylus_modes_proxy = FlowProxyWidget(self)
        self._stylus_modes_proxy.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._stylus_modes_proxy.setZValue(1001)
        self._stylus_modes_widget = FlowStylusModesWidget(self)
        self._stylus_modes_proxy.setWidget(self._stylus_modes_widget)
        self.scene().addItem(self._stylus_modes_proxy)
        self.set_stylus_proxy_pos()
        self.setAttribute(Qt.WA_TabletTracking)

        # # TOUCH GESTURES
        # recognizer = PanGestureRecognizer()
        # pan_gesture_id = QGestureRecognizer.registerRecognizer(recognizer) <--- CRASH HERE
        # self.grabGesture(pan_gesture_id)

        # DESIGN THEME
        self.session.design.flow_theme_changed.connect(self._theme_changed)

        if config is not None:
            # algorithm mode
            mode = config['algorithm mode']
            if mode == 'data' or mode == 'data flow':  # mode == FlowAlg.DATA
                # self.alg_mode = FlowAlg.DATA
                self.set_algorithm_mode('data')
            elif mode == 'exec' or mode == 'exec flow':  # mode == FlowAlg.EXEC
                # self.alg_mode = FlowAlg.EXEC
                self.set_algorithm_mode('exec')

            # viewport update mode
            vpum = config['viewport update mode']
            if vpum == 'sync':  # vpum == VPUpdateMode.SYNC
                # self.vp_update_mode = VPUpdateMode.SYNC
                self.set_viewport_update_mode('sync')
            elif vpum == 'async':  # vpum == VPUpdateMode.ASYNC
                self.vp_update_mode = VPUpdateMode.ASYNC
                self.set_viewport_update_mode('async')

            self.nodes, self.node_items = self.place_nodes_from_config(config['nodes'])
            self.connect_nodes_from_config(self.nodes, config['connections'])
            if list(config.keys()).__contains__('drawings'):  # not all (old) project files have drawings arr
                self.place_drawings_from_config(config['drawings'])
            self._undo_stack.clear()


        # FRAMERATE TRACKING
        self.num_frames = 0
        self.framerate = 0
        self.framerate_timer = QTimer(self)
        self.framerate_timer.timeout.connect(self._on_framerate_timer_timeout)

        self.show_framerate(m_sec_interval=100)  # for testing


    def show_framerate(self, show: bool = True, m_sec_interval: int = 1000):
        self._showing_framerate = show
        self.framerate_timer.setInterval(m_sec_interval)
        self.framerate_timer.start()

    def _on_framerate_timer_timeout(self):
        self.framerate = self.num_frames
        self.num_frames = 0

    def _init_shortcuts(self):
        place_new_node_shortcut = QShortcut(QKeySequence('Shift+P'), self)
        place_new_node_shortcut.activated.connect(self._place_new_node_by_shortcut)
        move_selected_nodes_left_shortcut = QShortcut(QKeySequence('Shift+Left'), self)
        move_selected_nodes_left_shortcut.activated.connect(self._move_selected_nodes_left)
        move_selected_nodes_up_shortcut = QShortcut(QKeySequence('Shift+Up'), self)
        move_selected_nodes_up_shortcut.activated.connect(self._move_selected_nodes_up)
        move_selected_nodes_right_shortcut = QShortcut(QKeySequence('Shift+Right'), self)
        move_selected_nodes_right_shortcut.activated.connect(self._move_selected_nodes_right)
        move_selected_nodes_down_shortcut = QShortcut(QKeySequence('Shift+Down'), self)
        move_selected_nodes_down_shortcut.activated.connect(self._move_selected_nodes_down)
        select_all_shortcut = QShortcut(QKeySequence('Ctrl+A'), self)
        select_all_shortcut.activated.connect(self.select_all)
        copy_shortcut = QShortcut(QKeySequence.Copy, self)
        copy_shortcut.activated.connect(self._copy)
        cut_shortcut = QShortcut(QKeySequence.Cut, self)
        cut_shortcut.activated.connect(self._cut)
        paste_shortcut = QShortcut(QKeySequence.Paste, self)
        paste_shortcut.activated.connect(self._paste)

        undo_shortcut = QShortcut(QKeySequence.Undo, self)
        undo_shortcut.activated.connect(self._undo_activated)
        redo_shortcut = QShortcut(QKeySequence.Redo, self)
        redo_shortcut.activated.connect(self._redo_activated)

    def _theme_changed(self, t):
        # TODO: repaint background. how?
        self.viewport().update()

    def _scene_selection_changed(self):
        self.nodes_selection_changed.emit(self.selected_nodes())

    def contextMenuEvent(self, event):
        QGraphicsView.contextMenuEvent(self, event)
        # in the case of the menu already being shown by a widget under the mouse, the event is accepted here
        if event.isAccepted():
            return

        for i in self.items(event.pos()):
            if isinstance(i, NodeItem):
                ni: NodeItem = i
                menu: QMenu = ni.get_context_menu()
                menu.exec_(event.globalPos())
                event.accept()

    def _undo_activated(self):
        """Triggered by ctrl+z"""
        self._undo_stack.undo()
        self.viewport().update()

    def _redo_activated(self):
        """Triggered by ctrl+y"""
        self._undo_stack.redo()
        self.viewport().update()

    def mousePressEvent(self, event):
        Debugger.write('mouse press event received, point:', event.pos())

        # to catch tablet events (for some reason, it results in a mousePrEv too)
        if self.ignore_mouse_event:
            self.ignore_mouse_event = False
            return

        # there might be a proxy widget meant to receive the event instead of the flow
        QGraphicsView.mousePressEvent(self, event)

        # to catch any Proxy that received the event. Checking for event.isAccepted() or what is returned by
        # QGraphicsView.mousePressEvent(...) both didn't work so far, so I do it manually
        if self.ignore_mouse_event:
            self.ignore_mouse_event = False
            return

        if event.button() == Qt.LeftButton:
            if self._node_choice_proxy.isVisible():
                self.hide_node_choice_widget()
            else:
                if isinstance(self.itemAt(event.pos()), PortItemPin):
                    self.selected_pin = self.itemAt(event.pos())
                    self.dragging_connection = True

            self._left_mouse_pressed_in_flow = True

        elif event.button() == Qt.RightButton:
            if len(self.items(event.pos())) == 0:
                self._node_choice_widget.reset_list()
                self.show_node_choice_widget(event.pos())

        elif event.button() == Qt.MidButton:
            self._panning = True
            self._pan_last_x = event.x()
            self._pan_last_y = event.y()
            event.accept()

        self._mouse_press_pos = self.mapToScene(event.pos())

    def mouseMoveEvent(self, event):

        QGraphicsView.mouseMoveEvent(self, event)

        if self._panning:  # middle mouse pressed
            self.pan(event.pos())
            event.accept()

        self._last_mouse_move_pos = self.mapToScene(event.pos())

        if self.dragging_connection:
            self.viewport().repaint()

    def mouseReleaseEvent(self, event):
        # there might be a proxy widget meant to receive the event instead of the flow
        QGraphicsView.mouseReleaseEvent(self, event)

        node_item_at_event_pos = None
        for item in self.items(event.pos()):
            if isinstance(item, NodeItem):
                node_item_at_event_pos = item

        if self.ignore_mouse_event or \
                (event.button() == Qt.LeftButton and not self._left_mouse_pressed_in_flow):
            self.ignore_mouse_event = False
            return

        elif event.button() == Qt.MidButton:
            self._panning = False


        # connection dropped over specific pin
        if self.dragging_connection and self.itemAt(event.pos()) and \
                isinstance(self.itemAt(event.pos()), PortItemPin):
            self.connect_node_ports__cmd(self.selected_pin.port,
                                         self.itemAt(event.pos()).port)

        # connection dropped above NodeItem -> auto connect
        elif self.dragging_connection and node_item_at_event_pos:
            # find node item
            ni_under_drop = None
            for item in self.items(event.pos()):
                if isinstance(item, NodeItem):
                    ni_under_drop = item
                    self.auto_connect(self.selected_pin.port, ni_under_drop.node)
                    break

        elif self.dragging_connection:
            # connection dropped somewhere else - show node choice widget
            self._auto_connection_pin = self.selected_pin
            self.show_node_choice_widget(event.pos())

        self._left_mouse_pressed_in_flow = False
        self.dragging_connection = False
        self.selected_pin = None

        self.viewport().repaint()

    def keyPressEvent(self, event):
        QGraphicsView.keyPressEvent(self, event)

        if event.isAccepted():
            return

        if event.key() == Qt.Key_Escape:  # do I need that... ?
            self.clearFocus()
            self.setFocus()
            return True

        elif event.key() == Qt.Key_Delete:
            self.remove_selected_components()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.CTRL and event.angleDelta().x() == 0:
            self.zoom(event.pos(), self.mapToScene(event.pos()), event.angleDelta().y())
            event.accept()
            return True

        QGraphicsView.wheelEvent(self, event)

    def tabletEvent(self, event):
        """tabletEvent gets called by stylus operations.
        LeftButton: std, no button pressed
        RightButton: upper button pressed"""

        # if in edit mode and not panning or starting a pan, pass on to std mouseEvent handlers above
        if self.stylus_mode == 'edit' and not self._panning and not \
                (event.type() == QTabletEvent.TabletPress and event.button() == Qt.RightButton):
            return  # let the mousePress/Move/Release-Events handle it

        scaled_event_pos: QPointF = event.posF()/self._current_scale

        if event.type() == QTabletEvent.TabletPress:
            self.ignore_mouse_event = True

            if event.button() == Qt.LeftButton:
                if self.stylus_mode == 'comment':
                    view_pos = self.mapToScene(self.viewport().pos())
                    new_drawing = self._create_and_place_drawing__cmd(
                        view_pos + scaled_event_pos,
                        config={**self._stylus_modes_widget.get_pen_settings(), 'viewport pos': view_pos}
                    )
                    self._current_drawing = new_drawing
                    self._drawing = True
            elif event.button() == Qt.RightButton:
                self._panning = True
                self._pan_last_x = event.x()
                self._pan_last_y = event.y()

        elif event.type() == QTabletEvent.TabletMove:
            self.ignore_mouse_event = True
            if self._panning:
                self.pan(event.pos())

            elif event.pointerType() == QTabletEvent.Eraser:
                if self.stylus_mode == 'comment':
                    for i in self.items(event.pos()):
                        if isinstance(i, DrawingObject):
                            self.remove_drawing(i)
                            break
            elif self.stylus_mode == 'comment' and self._drawing:
                if self._current_drawing.append_point(scaled_event_pos):
                    self._current_drawing.stroke_weights.append(event.pressure())
                self._current_drawing.update()
                self.viewport().update()

        elif event.type() == QTabletEvent.TabletRelease:
            if self._panning:
                self._panning = False
            if self.stylus_mode == 'comment' and self._drawing:
                Debugger.write('drawing obj finished')
                self._current_drawing.finish()
                self._current_drawing = None
                self._drawing = False

    # https://forum.qt.io/topic/121473/qgesturerecognizer-registerrecognizer-crashes-using-pyside2
    #
    # def event(self, event) -> bool:
    #     # if event.type() == QEvent.Gesture:
    #     #     if event.gesture(PanGesture) is not None:
    #     #         return self.pan_gesture(event)
    #
    #     return QGraphicsView.event(self, event)
    #
    # def pan_gesture(self, event: QGestureEvent) -> bool:
    #     pan: PanGesture = event.gesture(PanGesture)
    #     print(pan)
    #     return True

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat('text/plain'):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat('text/plain'):
            event.acceptProposedAction()

    # def dropEvent(self, event):
    #     text = event.mimeData().text()
    #     item: QListWidgetItem = event.mimeData()
    #     Debugger.write('drop received in Flow:', text)
    #
    #     j_obj = None
    #     type = ''
    #     try:
    #         j_obj = json.loads(text)
    #         type = j_obj['type']
    #     except Exception:
    #         return
    #
    #     if type == 'variable':
    #         self.show_node_choice_widget(event.pos(),  # only show get_var and set_var nodes
    #                                      [n for n in self.session.nodes if find_type_in_object(n, GetVar_Node) or
    #                                       find_type_in_object(n, SetVar_Node)])

    def drawBackground(self, painter, rect):
        painter.fillRect(rect.intersected(self.sceneRect()), self.session.design.flow_theme.flow_background_color)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.sceneRect())

        self.set_stylus_proxy_pos()  # has to be called here instead of in drawForeground to prevent lagging
        self.set_zoom_proxy_pos()

    def drawForeground(self, painter, rect):

        if self._showing_framerate:
            self.num_frames += 1
            pen = QPen(QColor('#A9D5EF'))
            pen.setWidthF(2)
            painter.setPen(pen)

            pos = self.mapToScene(10, 23)
            painter.setFont(QFont('Poppins', round(11 * self._total_scale_div)))
            painter.drawText(pos, "{:.2f}".format(self.framerate))


        # DRAW CURRENTLY DRAGGED CONNECTION
        if self.dragging_connection:
            pen = QPen('#101520')
            pen.setWidth(3)
            pen.setStyle(Qt.DotLine)
            painter.setPen(pen)

            pin_pos = self.selected_pin.get_scene_center_pos()
            spp = self.selected_pin.port
            cursor_pos = self._last_mouse_move_pos

            pos1 = pin_pos if spp.io_pos == PortObjPos.OUTPUT else cursor_pos
            pos2 = pin_pos if spp.io_pos == PortObjPos.INPUT else cursor_pos

            if spp.type_ == 'data':
                painter.drawPath(
                    default_cubic_connection_path(pos1, pos2)
                )
            elif spp.type_ == 'exec':
                painter.drawPath(
                    default_cubic_connection_path(pos1, pos2)
                )


        # DRAW SELECTED NIs BORDER
        for ni in self.selected_node_items():
            pen = QPen(QColor('#245d75'))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            size_factor = 1.2
            x = ni.pos().x() - ni.boundingRect().width() / 2 * size_factor
            y = ni.pos().y() - ni.boundingRect().height() / 2 * size_factor
            w = ni.boundingRect().width() * size_factor
            h = ni.boundingRect().height() * size_factor
            painter.drawRoundedRect(x, y, w, h, 10, 10)


        # DRAW SELECTED DRAWINGS BORDER
        for p_o in self.selected_drawings():
            pen = QPen(QColor('#a3cc3b'))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            size_factor = 1.05
            x = p_o.pos().x() - p_o.width / 2 * size_factor
            y = p_o.pos().y() - p_o.height / 2 * size_factor
            w = p_o.width * size_factor
            h = p_o.height * size_factor
            painter.drawRoundedRect(x, y, w, h, 6, 6)
            painter.drawEllipse(p_o.pos().x(), p_o.pos().y(), 2, 2)

    def get_viewport_img(self) -> QImage:
        """Returns a clear image of the viewport"""

        self.__hide_proxies()
        img = QImage(self.viewport().rect().width(), self.viewport().height(), QImage.Format_ARGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        self.render(painter, self.viewport().rect(), self.viewport().rect())
        self.__show_proxies()
        return img

    def get_whole_scene_img(self) -> QImage:
        """Returns an image of the whole scene, scaled accordingly to current scale factor.
        A bug makes this only work from the viewport position down and right, so the user has to scroll to
        the top left corner in order to get the full scene"""

        self.__hide_proxies()
        img = QImage(self.sceneRect().width() / self._total_scale_div, self.sceneRect().height() / self._total_scale_div,
                     QImage.Format_RGB32)
        img.fill(Qt.transparent)

        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF()
        rect.setLeft(-self.viewport().pos().x())
        rect.setTop(-self.viewport().pos().y())
        rect.setWidth(img.rect().width())
        rect.setHeight(img.rect().height())
        # rect is right... but it only renders from the viewport's point down-and rightwards, not from topleft (0,0) ...
        self.render(painter, rect, rect.toRect())
        self.__show_proxies()
        return img

    # PROXY POSITIONS
    def set_zoom_proxy_pos(self):
        self._zoom_proxy.setPos(self.mapToScene(self.viewport().width() - self._zoom_widget.width(), 0))

    def set_stylus_proxy_pos(self):
        self._stylus_modes_proxy.setPos(
            self.mapToScene(self.viewport().width() - self._stylus_modes_widget.width() - self._zoom_widget.width(), 0))

    def __hide_proxies(self):
        self._stylus_modes_proxy.hide()
        self._zoom_proxy.hide()

    def __show_proxies(self):
        self._stylus_modes_proxy.show()
        self._zoom_proxy.show()

    # NODE CHOICE WIDGET
    def show_node_choice_widget(self, pos, nodes=None):
        """Opens the node choice dialog in the scene."""

        # calculating position
        self._node_place_pos = self.mapToScene(pos)
        dialog_pos = QPoint(pos.x() + 1, pos.y() + 1)

        # ensure that the node_choice_widget stays in the viewport
        if dialog_pos.x() + self._node_choice_widget.width() / self._total_scale_div > self.viewport().width():
            dialog_pos.setX(dialog_pos.x() - (
                    dialog_pos.x() + self._node_choice_widget.width() / self._total_scale_div - self.viewport().width()))
        if dialog_pos.y() + self._node_choice_widget.height() / self._total_scale_div > self.viewport().height():
            dialog_pos.setY(dialog_pos.y() - (
                    dialog_pos.y() + self._node_choice_widget.height() / self._total_scale_div - self.viewport().height()))
        dialog_pos = self.mapToScene(dialog_pos)

        # open nodes dialog
        # the dialog emits 'node_chosen' which is connected to self.place_node,
        # so this all continues at self.place_node below
        self._node_choice_widget.update_list(nodes if nodes is not None else self.session.nodes)
        self._node_choice_widget.update_view()
        self._node_choice_proxy.setPos(dialog_pos)
        self._node_choice_proxy.show()
        self._node_choice_widget.refocus()

    def hide_node_choice_widget(self):
        self._node_choice_proxy.hide()
        self._node_choice_widget.clearFocus()
        self._auto_connection_pin = None

    # PAN
    def pan(self, new_pos):
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (new_pos.x() - self._pan_last_x))
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - (new_pos.y() - self._pan_last_y))
        self._pan_last_x = new_pos.x()
        self._pan_last_y = new_pos.y()

    # ZOOM
    def zoom_in(self, amount):
        local_viewport_center = QPoint(self.viewport().width() / 2, self.viewport().height() / 2)
        self.zoom(local_viewport_center, self.mapToScene(local_viewport_center), amount)

    def zoom_out(self, amount):
        local_viewport_center = QPoint(self.viewport().width() / 2, self.viewport().height() / 2)
        self.zoom(local_viewport_center, self.mapToScene(local_viewport_center), -amount)

    def zoom(self, p_abs, p_mapped, angle):
        by = 0
        velocity = 2 * (1 / self._current_scale) + 0.5
        if velocity > 3:
            velocity = 3

        direction = ''
        if angle > 0:
            by = 1 + (angle / 360 * 0.1 * velocity)
            direction = 'in'
        elif angle < 0:
            by = 1 - (-angle / 360 * 0.1 * velocity)
            direction = 'out'
        else:
            by = 1

        scene_rect_width = self.mapFromScene(self.sceneRect()).boundingRect().width()
        scene_rect_height = self.mapFromScene(self.sceneRect()).boundingRect().height()

        if direction == 'in':
            if self._current_scale * by < 3:
                self.scale(by, by)
                self._current_scale *= by
        elif direction == 'out':
            if scene_rect_width * by >= self.viewport().size().width() and scene_rect_height * by >= self.viewport().size().height():
                self.scale(by, by)
                self._current_scale *= by

        w = self.viewport().width()
        h = self.viewport().height()
        wf = self.mapToScene(QPoint(w - 1, 0)).x() - self.mapToScene(QPoint(0, 0)).x()
        hf = self.mapToScene(QPoint(0, h - 1)).y() - self.mapToScene(QPoint(0, 0)).y()
        lf = p_mapped.x() - p_abs.x() * wf / w
        tf = p_mapped.y() - p_abs.y() * hf / h

        self.ensureVisible(lf, tf, wf, hf, 0, 0)

        target_rect = QRectF(QPointF(lf, tf),
                             QSizeF(wf, hf))
        self._total_scale_div = target_rect.width() / self.viewport().width()

        self.ensureVisible(target_rect, 0, 0)

    # NODE PLACING: -----
    def create_node(self, node_class, config) -> Node:
        """Creates and returns a new Node object."""

        node = node_class(params=(self, self.session.design, config))
        node.finish_initialization()

        if self.session.threading_enabled:
            node.moveToThread(self.worker_thread)
            # from here, node lives in the worker thread but it's doesn't

        return node

    def add_node_item(self, ni: NodeItem, pos=None):
        """Adds a NodeItem to the scene."""

        self.scene().addItem(ni)
        ni.node.enable_logs()
        if pos:
            ni.setPos(pos)

        # select new NI
        self.scene().clearSelection()
        ni.setSelected(True)

        self.node_items.append(ni)
        self.nodes.append(ni.node)

    def add_node_items(self, node_items: [NodeItem]):
        """Adds a list of NodeItems to the scene."""

        for ni in node_items:
            self.add_node_item(ni)

    def remove_node_item(self, ni):
        """Removes a NodeItem from the scene."""

        ni.node.about_to_remove_from_scene()

        self.scene().removeItem(ni)

        self.node_items.remove(ni)
        self.nodes.remove(ni.node)

    def _place_new_node_by_shortcut(self):  # Shift+P
        point_in_viewport = None
        selected_NIs = self.selected_node_items()
        if len(selected_NIs) > 0:
            x = selected_NIs[-1].pos().x() + 150
            y = selected_NIs[-1].pos().y()
            self._node_place_pos = QPointF(x, y)
            point_in_viewport = self.mapFromScene(QPoint(x, y))
        else:  # place in center
            viewport_x = self.viewport().width() / 2
            viewport_y = self.viewport().height() / 2
            point_in_viewport = QPointF(viewport_x, viewport_y).toPoint()
            self._node_place_pos = self.mapToScene(point_in_viewport)

        self._node_choice_widget.reset_list()
        self.show_node_choice_widget(point_in_viewport)

    def place_nodes_from_config(self, nodes_config: list, offset_pos: QPoint = QPoint(0, 0)):
        """Creates Nodes and places them in the scene from nodes_config.
        The exact config list is included in what is returned by the config_data() method at 'nodes'."""

        nodes = []
        node_items = []

        for n_c in nodes_config:
            
            # find class
            node_class = None
            if 'parent node title' in n_c:  # backwards compatibility
                for nc in self.session.nodes:
                    if nc.title == n_c['parent node title']:
                        node_class = nc
                        break
            else:
                for nc in self.session.nodes:
                    if nc.__name__ == n_c['identifier']:
                        node_class = nc
                        break

            node = self.create_node(node_class, n_c)
            self.add_node_item(node.item, QPoint(n_c['position x'], n_c['position y']) + offset_pos)
            nodes.append(node)
            node_items.append(node.item)

        self.nodes += nodes
        self.node_items += node_items

        return nodes, node_items

    def place_node__cmd(self, node_class, config=None):

        node = self.create_node(node_class, config)

        place_command = PlaceNodeItemInScene_Command(self, node.item, self._node_place_pos)

        self._undo_stack.push(place_command)

        if self._auto_connection_pin:
            self.auto_connect(self._auto_connection_pin.port,
                              node)

        return node

    # def remove_node_instance_triggered(self, node_instance):  # called from context menu of NodeInstance
    #     if node_instance in self.selected_node_items():
    #         self.__undo_stack.push(
    #             RemoveComponents_Command(self, self.scene().selectedItems()))
    #     else:
    #         self.__undo_stack.push(RemoveComponents_Command(self, [node_instance]))

    # def get_node_instance_class_from_node(self, node):
    #     return self.all_node_instance_classes[node]

    # def get_custom_input_widget_classes(self):
    #     return self.script.main_window.custom_node_input_widget_classes

    def connect_nodes_from_config(self, nodes: [Node], connections_config: list):
        """Connects Nodes according to the config list. This list is included in what is returned by the
        config_data() method at 'connections'."""

        for c in connections_config:

            c_parent_node_index = -1
            if 'parent node instance index' in c:  # backwards compatibility
                c_parent_node_index = c['parent node instance index']
            else:
                c_parent_node_index = c['parent node index']

            c_output_port_index = c['output port index']

            c_connected_node_index = -1
            if 'connected node instance' in c:  # backwards compatibility
                c_connected_node_index = c['connected node instance']
            else:
                c_connected_node_index = c['connected node']

            c_connected_input_port_index = c['connected input port index']

            if c_connected_node_index is not None:  # which can be the case when pasting
                parent_node = nodes[c_parent_node_index]
                connected_node = nodes[c_connected_node_index]

                self.connect_ports(parent_node.outputs[c_output_port_index],
                                   connected_node.inputs[c_connected_input_port_index])

    # DRAWINGS
    def create_drawing(self, config=None) -> DrawingObject:
        """Creates and returns a new DrawingObject."""

        new_drawing = DrawingObject(self, config)
        return new_drawing

    def add_drawing(self, drawing_obj, posF=None):
        """Adds a DrawingObject to the scene."""

        self.scene().addItem(drawing_obj)
        if posF:
            drawing_obj.setPos(posF)
        self.drawings.append(drawing_obj)

    def add_drawings(self, drawings):
        """Adds a list of DrawingObjects to the scene."""

        for d in drawings:
            self.add_drawing(d)

    def remove_drawing(self, drawing):
        """Removes a drawing from the scene."""

        self.scene().removeItem(drawing)
        self.drawings.remove(drawing)

    def place_drawings_from_config(self, drawings_config: list, offset_pos=QPoint(0, 0)):
        """Creates and places drawings from drawings. The same list is returned by the config_data() method
        at 'drawings'."""

        new_drawings = []
        for d_config in drawings_config:
            x = d_config['pos x']+offset_pos.x()
            y = d_config['pos y']+offset_pos.y()
            new_drawing = self.create_drawing(config=d_config)
            self.add_drawing(new_drawing, QPointF(x, y))
            new_drawings.append(new_drawing)

        return new_drawings

    def _create_and_place_drawing__cmd(self, posF, config=None):
        new_drawing_obj = self.create_drawing(config)
        place_command = PlaceDrawingObject_Command(self, posF, new_drawing_obj)
        self._undo_stack.push(place_command)
        return new_drawing_obj

    def _move_selected_copmonents__cmd(self, x, y):
        new_rel_pos = QPointF(x, y)

        # if one node item would leave the scene (f.ex. pos.x < 0), stop
        left = False
        for i in self.scene().selectedItems():
            new_pos = i.pos() + new_rel_pos
            w = i.boundingRect().width()
            h = i.boundingRect().height()
            if new_pos.x() - w / 2 < 0 or \
                    new_pos.x() + w / 2 > self.scene().width() or \
                    new_pos.y() - h / 2 < 0 or \
                    new_pos.y() + h / 2 > self.scene().height():
                left = True
                break

        if not left:
            # moving the items
            items_group = self.scene().createItemGroup(self.scene().selectedItems())
            items_group.moveBy(new_rel_pos.x(), new_rel_pos.y())
            self.scene().destroyItemGroup(items_group)

            # saving the command
            self._undo_stack.push(
                MoveComponents_Command(self, self.scene().selectedItems(), p_from=-new_rel_pos, p_to=QPointF(0, 0))
            )

        self.viewport().repaint()

    def _move_selected_nodes_left(self):
        self._move_selected_copmonents__cmd(-40, 0)

    def _move_selected_nodes_up(self):
        self._move_selected_copmonents__cmd(0, -40)

    def _move_selected_nodes_right(self):
        self._move_selected_copmonents__cmd(+40, 0)

    def _move_selected_nodes_down(self):
        self._move_selected_copmonents__cmd(0, +40)

    def selected_components_moved(self, pos_diff):
        items_list = self.scene().selectedItems()

        self._undo_stack.push(MoveComponents_Command(self, items_list, p_from=-pos_diff, p_to=QPointF(0, 0)))

    def selected_node_items(self) -> [NodeItem]:
        """Returns a list of the currently selected NodeItems."""

        selected_NIs = []
        for i in self.scene().selectedItems():
            if isinstance(i, NodeItem):
                selected_NIs.append(i)
        return selected_NIs

    def selected_nodes(self) -> [Node]:
        return [item.node for item in self.selected_node_items()]

    def selected_drawings(self) -> [DrawingObject]:
        """Returns a list of the currently selected drawings."""

        selected_drawings = []
        for i in self.scene().selectedItems():
            if isinstance(i, DrawingObject):
                selected_drawings.append(i)
        return selected_drawings

    def select_all(self):
        for i in self.scene().items():
            if i.ItemIsSelectable:
                i.setSelected(True)
        self.viewport().repaint()

    def select_components(self, comps):
        self.scene().clearSelection()
        for c in comps:
            c.setSelected(True)

    def _copy(self):  # ctrl+c
        data = {'nodes': self._get_nodes_config_data(self.selected_nodes()),
                'connections': self._get_connections_config_data(self.selected_nodes()),
                'drawings': self._get_drawings_config_data(self.selected_drawings())}
        QGuiApplication.clipboard().setText(json.dumps(data))

    def _cut(self):  # called from shortcut ctrl+x
        data = {'nodes': self._get_nodes_config_data(self.selected_nodes()),
                'connections': self._get_connections_config_data(self.selected_nodes()),
                'drawings': self._get_drawings_config_data(self.selected_drawings())}
        QGuiApplication.clipboard().setText(json.dumps(data))
        self.remove_selected_components()

    def _paste(self):
        data = {}
        try:
            data = json.loads(QGuiApplication.clipboard().text())
        except Exception as e:
            return

        self.clear_selection()

        # calculate offset
        positions = []
        for d in data['drawings']:
            positions.append({'x': d['pos x'],
                              'y': d['pos y']})
        for n in data['nodes']:
            positions.append({'x': n['position x'],
                              'y': n['position y']})

        offset_for_middle_pos = QPointF(0, 0)
        if len(positions) > 0:
            rect = QRectF(positions[0]['x'], positions[0]['y'], 0, 0)
            for p in positions:
                x = p['x']
                y = p['y']
                if x < rect.left():
                    rect.setLeft(x)
                if x > rect.right():
                    rect.setRight(x)
                if y < rect.top():
                    rect.setTop(y)
                if y > rect.bottom():
                    rect.setBottom(y)

            offset_for_middle_pos = self._last_mouse_move_pos - rect.center()

        self._undo_stack.push(Paste_Command(self, data, offset_for_middle_pos))

    def add_component(self, e):
        if isinstance(e, NodeItem):
            self.add_node_item(e)
        elif isinstance(e, DrawingObject):
            self.add_drawing(e)

    def remove_components(self, comps):
        for c in comps:
            self.remove_component(c)

    def remove_component(self, e):
        if isinstance(e, NodeItem):
            self.remove_node_item(e)
        elif isinstance(e, DrawingObject):
            self.remove_drawing(e)

    def remove_selected_components(self):
        self._undo_stack.push(
            RemoveComponents_Command(self, self.scene().selectedItems()))

        self.viewport().update()

    # NODE SELECTION: ----
    def clear_selection(self):
        self.scene().clearSelection()

    # CONNECTIONS: ----
    def connect_node_ports__cmd(self, p1: NodeObjPort, p2: NodeObjPort):
        """Connects if possible, disconnects if ports are already connected"""

        out = None
        inp = None
        if p1.io_pos == PortObjPos.OUTPUT and p2.io_pos == PortObjPos.INPUT:
            out = p1
            inp = p2
        elif p1.io_pos == PortObjPos.INPUT and p2.io_pos == PortObjPos.OUTPUT:
            out = p2
            inp = p1
        else:
            # ports have same direction
            return

        if out.type_ != inp.type_:
            return

        self._undo_stack.push(ConnectPorts_Command(self, out=out, inp=inp))

    def connect_ports(self, out: NodeObjOutput = None, inp: NodeObjInput = None, connection: Connection = None):
        """
        DEFAULT: connects out and inp if they are not connected, otherwise they get disconnected
        connected() or disconnected() is triggered afterwards of the ports
        IF CONNECTION PROVIDED: the connection gets added to the scene and connected() is triggered on the ports.
        """

        inp = inp if not connection else connection.inp
        out = out if not connection else connection.out


        for c in out.connections:
            if c.inp == inp:
                # disconnect
                self.remove_connection(c)
                out.disconnected()
                inp.disconnected()
                return

        if inp.node == out.node:
            return


        # CONNECT

        # remove all connections from input port instance if it's a data input
        if inp.type_ == 'data':
            for c in inp.connections:
                self.connect_node_ports__cmd(c.out, inp)


        if connection:
            self.add_connection(connection)
            if self.session.threading_enabled:
                self.trigger_port_connected.emit(out)
                self.trigger_port_connected.emit(inp)
            else:
                connection.out.connected()
                connection.inp.connected()
            return


        c = self.new_connection(out, inp)
        self.add_connection(c)

        if self.session.threading_enabled:
            self.trigger_port_connected.emit(out)
            self.trigger_port_connected.emit(inp)
        else:
            c.out.connected()
            c.inp.connected()

    def new_connection(self, out: NodeObjOutput, inp: NodeObjInput) -> Connection:
        """Creates the connection object"""
        c = None
        if inp.type_ == 'data':
            c = self.session.flow_data_conn_class((out, inp, self.session.design))
        elif inp.type_ == 'exec':
            c = self.session.flow_exec_conn_class((out, inp, self.session.design))
        c.item.setZValue(10)
        if self.session.threading_enabled:
            c.moveToThread(self.worker_thread)
        return c

    def add_connection(self, c: Connection):
        """Adds the connection object to the scene and sets it in the ports"""
        c.out.connections.append(c)
        c.inp.connections.append(c)

        self.connections.append(c)

        self.scene().addItem(c.item)
        self.viewport().repaint()

    def remove_connection(self, c: Connection):
        """Removes the connection object from the scene and from the ports"""
        c.out.connections.remove(c)
        c.inp.connections.remove(c)

        self.connections.remove(c)

        self.scene().removeItem(c.item)
        self.viewport().repaint()

    def auto_connect(self, p: NodeObjPort, n: Node):
        if p.io_pos == PortObjPos.OUTPUT:
            for inp in n.inputs:
                if p.type_ == inp.type_:
                    # connect exactly once
                    self.connect_node_ports__cmd(p, inp)
                    return
        elif p.io_pos == PortObjPos.INPUT:
            for out in n.outputs:
                if p.type_ == out.type_:
                    # connect exactly once
                    self.connect_node_ports__cmd(p, out)
                    return

    # MODES API

    def algorithm_mode(self) -> str:
        """Returns the current algorithm mode of the flow as string"""
        return FlowAlg.stringify(self.alg_mode)

    def set_algorithm_mode(self, mode: str):
        """
        Sets the algorithm mode of the flow
        :mode: 'data' or 'exec'
        """
        if mode == 'data':
            self.alg_mode = FlowAlg.DATA
        elif mode == 'exec':
            self.alg_mode = FlowAlg.EXEC

        self.algorithm_mode_changed.emit(self.algorithm_mode())

    def viewport_update_mode(self) -> str:
        """Returns the current viewport update mode as string (sync or async) of the flow"""
        return VPUpdateMode.stringify(self.vp_update_mode)

    def set_viewport_update_mode(self, mode: str):
        """
        Sets the viewport update mode of the flow
        :mode: 'sync' or 'async'
        """
        if mode == 'sync':
            self.vp_update_mode = VPUpdateMode.SYNC
        elif mode == 'async':
            self.vp_update_mode = VPUpdateMode.ASYNC

        self.viewport_update_mode_changed.emit(self.viewport_update_mode())

    def config_data(self) -> dict:
        print(self.nodes)
        flow_dict = {'algorithm mode': FlowAlg.stringify(self.alg_mode),
                     'viewport update mode': VPUpdateMode.stringify(self.vp_update_mode),
                     'nodes': self._get_nodes_config_data(self.nodes),
                     'connections': self._get_connections_config_data(self.nodes),
                     'drawings': self._get_drawings_config_data(self.drawings)}
        return flow_dict

    def _get_nodes_config_data(self, nodes):
        nodes_data = []
        for n in nodes:
            nodes_data.append(n.config_data(n.item.config_data()))

        return nodes_data

    def _get_connections_config_data(self, nodes, only_with_connections_to=None):
        script_ni_connections_list = []
        for n in nodes:
            for out in n.outputs:
                if len(out.connections) > 0:
                    for c in out.connections:
                        connected_port = c.inp

                        # this only applies when saving config data through deleting nodes:
                        if only_with_connections_to is not None and \
                                connected_port.node not in only_with_connections_to and \
                                n not in only_with_connections_to:
                            continue
                        # because I am not allowed to save connections between nodes connected to each other and both
                        # connected to the deleted node, only the connections to the deleted node shall be saved

                        connection_dict = {'parent node index': nodes.index(n),
                                           'output port index': n.outputs.index(out)}

                        # yes, very important: when copying components, there might be connections going outside the
                        # selected lists, these should be ignored. When saving a project, all components are considered,
                        # so then the index values will never be none
                        connected_node_index = nodes.index(connected_port.node) if \
                            connected_port.node in nodes else None

                        connection_dict['connected node'] = connected_node_index

                        connected_ip_index = connected_port.node.inputs.index(connected_port) if \
                            connected_node_index is not None else None
                        connection_dict['connected input port index'] = connected_ip_index

                        script_ni_connections_list.append(connection_dict)

        return script_ni_connections_list

    def _get_drawings_config_data(self, drawings):
        drawings_list = []
        for drawing in drawings:
            drawing_dict = drawing.config_data()

            drawings_list.append(drawing_dict)

        return drawings_list
