from PySide2.QtCore import Qt, QPointF, QPoint, QRectF, QSizeF, Signal, QTimer
from PySide2.QtGui import QPainter, QPen, QColor, QKeySequence, QTabletEvent, QImage, QGuiApplication, QFont
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QShortcut, QMenu, QGraphicsItem, QUndoStack

from .FlowCommands import MoveComponents_Command, PlaceNodeInstanceInScene_Command, \
    PlaceDrawingObject_Command, RemoveComponents_Command, ConnectPorts_Command, Paste_Command
from .FlowProxyWidget import FlowProxyWidget
from .FlowStylusModesWidget import FlowStylusModesWidget
from .FlowZoomWidget import FlowZoomWidget
from .node_choice_widget.NodeChoiceWidget import NodeChoiceWidget
from .Node import Node
from .NodeInstance import NodeInstance
from .PortInstance import PortInstance, PortInstPin
from .Connection import Connection, default_cubic_connection_path
from .DrawingObject import DrawingObject
from .global_tools.Debugger import Debugger
from .RC import PortPos, FlowAlg
from .RC import FlowVPUpdateMode as VPUpdateMode

import json


class Flow(QGraphicsView):
    """Manages all GUI of flows"""

    node_inst_selection_changed = Signal(list)
    algorithm_mode_changed = Signal(str)
    viewport_update_mode_changed = Signal(str)

    def __init__(self, session, script, flow_size: list = None, config=None, parent=None):
        super(Flow, self).__init__(parent=parent)


        # UNDO/REDO
        self.__undo_stack = QUndoStack(self)
        self.__undo_action = self.__undo_stack.createUndoAction(self, 'undo')
        self.__undo_action.setShortcuts(QKeySequence.Undo)
        self.__redo_action = self.__undo_stack.createRedoAction(self, 'redo')
        self.__redo_action.setShortcuts(QKeySequence.Redo)

        # SHORTCUTS
        self.__init_shortcuts()

        # GENERAL ATTRIBUTES
        self.script = script
        self.session = session
        self.node_instances: [NodeInstance] = []
        self.connections: [Connection] = []
        self.selected_pin: PortInstPin = None
        self.dragging_connection = False
        self.ignore_mouse_event = False  # for stylus - see tablet event
        self.__showing_framerate = False
        self.__last_mouse_move_pos: QPointF = None
        self.__node_place_pos = QPointF()
        self.__left_mouse_pressed_in_flow = False
        self.__mouse_press_pos: QPointF = None
        self.__auto_connection_pin = None  # stores the gate that we may try to auto connect to a newly placed NI
        self.__panning = False
        self.__pan_last_x = None
        self.__pan_last_y = None
        self.__current_scale = 1
        self.__total_scale_div = 1

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
        scene.selectionChanged.connect(self.__scene_selection_changed)
        self.setAcceptDrops(True)

        self.centerOn(QPointF(self.viewport().width() / 2, self.viewport().height() / 2))

        # NODE CHOICE WIDGET
        self.__node_choice_proxy = FlowProxyWidget(self)
        self.__node_choice_proxy.setZValue(1000)
        self.__node_choice_widget = NodeChoiceWidget(self, self.session.nodes)  # , main_window.node_images)
        self.__node_choice_proxy.setWidget(self.__node_choice_widget)
        self.scene().addItem(self.__node_choice_proxy)
        self.hide_node_choice_widget()

        # ZOOM WIDGET
        self.__zoom_proxy = FlowProxyWidget(self)
        self.__zoom_proxy.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.__zoom_proxy.setZValue(1001)
        self.__zoom_widget = FlowZoomWidget(self)
        self.__zoom_proxy.setWidget(self.__zoom_widget)
        self.scene().addItem(self.__zoom_proxy)
        self.set_zoom_proxy_pos()

        # STYLUS
        self.stylus_mode = ''
        self.__current_drawing = None
        self.__drawing = False
        self.drawings = []
        self.__stylus_modes_proxy = FlowProxyWidget(self)
        self.__stylus_modes_proxy.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.__stylus_modes_proxy.setZValue(1001)
        self.__stylus_modes_widget = FlowStylusModesWidget(self)
        self.__stylus_modes_proxy.setWidget(self.__stylus_modes_widget)
        self.scene().addItem(self.__stylus_modes_proxy)
        self.set_stylus_proxy_pos()
        self.setAttribute(Qt.WA_TabletTracking)

        # # TOUCH GESTURES
        # recognizer = PanGestureRecognizer()
        # pan_gesture_id = QGestureRecognizer.registerRecognizer(recognizer) <--- CRASH HERE
        # self.grabGesture(pan_gesture_id)

        # DESIGN THEME
        self.session.design.flow_theme_changed.connect(self.__theme_changed)

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

            node_instances = self.place_nodes_from_config(config['nodes'])
            self.connect_nodes_from_config(node_instances, config['connections'])
            if list(config.keys()).__contains__('drawings'):  # not all (old) project files have drawings arr
                self.place_drawings_from_config(config['drawings'])
            self.__undo_stack.clear()


        # FRAMERATE TRACKING
        self.num_frames = 0
        self.framerate = 0
        self.framerate_timer = QTimer(self)
        self.framerate_timer.timeout.connect(self.on_framerate_timer_timeout)

        self.show_framerate(m_sec_interval=100)  # for testing


    def show_framerate(self, show: bool = True, m_sec_interval: int = 1000):
        self.__showing_framerate = show
        self.framerate_timer.setInterval(m_sec_interval)
        self.framerate_timer.start()

    def on_framerate_timer_timeout(self):
        self.framerate = self.num_frames
        self.num_frames = 0

    def __init_shortcuts(self):
        place_new_node_shortcut = QShortcut(QKeySequence('Shift+P'), self)
        place_new_node_shortcut.activated.connect(self.__place_new_node_by_shortcut)
        move_selected_nodes_left_shortcut = QShortcut(QKeySequence('Shift+Left'), self)
        move_selected_nodes_left_shortcut.activated.connect(self.__move_selected_nodes_left)
        move_selected_nodes_up_shortcut = QShortcut(QKeySequence('Shift+Up'), self)
        move_selected_nodes_up_shortcut.activated.connect(self.__move_selected_nodes_up)
        move_selected_nodes_right_shortcut = QShortcut(QKeySequence('Shift+Right'), self)
        move_selected_nodes_right_shortcut.activated.connect(self.__move_selected_nodes_right)
        move_selected_nodes_down_shortcut = QShortcut(QKeySequence('Shift+Down'), self)
        move_selected_nodes_down_shortcut.activated.connect(self.__move_selected_nodes_down)
        select_all_shortcut = QShortcut(QKeySequence('Ctrl+A'), self)
        select_all_shortcut.activated.connect(self.select_all)
        copy_shortcut = QShortcut(QKeySequence.Copy, self)
        copy_shortcut.activated.connect(self.__copy)
        cut_shortcut = QShortcut(QKeySequence.Cut, self)
        cut_shortcut.activated.connect(self.__cut)
        paste_shortcut = QShortcut(QKeySequence.Paste, self)
        paste_shortcut.activated.connect(self.__paste)

        undo_shortcut = QShortcut(QKeySequence.Undo, self)
        undo_shortcut.activated.connect(self.__undo_activated)
        redo_shortcut = QShortcut(QKeySequence.Redo, self)
        redo_shortcut.activated.connect(self.__redo_activated)

    def __theme_changed(self, t):
        # TODO: repaint background. how?
        self.viewport().update()

    def __scene_selection_changed(self):
        self.node_inst_selection_changed.emit(
            [ni for ni in self.scene().selectedItems() if isinstance(ni, NodeInstance)]
        )

    def contextMenuEvent(self, event):
        QGraphicsView.contextMenuEvent(self, event)
        # in the case of the menu already being shown by a widget under the mouse, the event is accepted here
        if event.isAccepted():
            return

        for i in self.items(event.pos()):
            if isinstance(i, NodeInstance):
                ni: NodeInstance = i
                menu: QMenu = ni.get_context_menu()
                menu.exec_(event.globalPos())
                event.accept()

    def __undo_activated(self):
        """Triggered by ctrl+z"""
        self.__undo_stack.undo()
        self.viewport().update()

    def __redo_activated(self):
        """Triggered by ctrl+y"""
        self.__undo_stack.redo()
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
            if self.__node_choice_proxy.isVisible():
                self.hide_node_choice_widget()
            else:
                if isinstance(self.itemAt(event.pos()), PortInstPin):
                    self.selected_pin = self.itemAt(event.pos())
                    self.dragging_connection = True

            self.__left_mouse_pressed_in_flow = True

        elif event.button() == Qt.RightButton:
            if len(self.items(event.pos())) == 0:
                self.__node_choice_widget.reset_list()
                self.show_node_choice_widget(event.pos())

        elif event.button() == Qt.MidButton:
            self.__panning = True
            self.__pan_last_x = event.x()
            self.__pan_last_y = event.y()
            event.accept()

        self.__mouse_press_pos = self.mapToScene(event.pos())

    def mouseMoveEvent(self, event):

        QGraphicsView.mouseMoveEvent(self, event)

        if self.__panning:  # middle mouse pressed
            self.pan(event.pos())
            event.accept()

        self.__last_mouse_move_pos = self.mapToScene(event.pos())

        if self.dragging_connection:
            self.viewport().repaint()

    def mouseReleaseEvent(self, event):
        # there might be a proxy widget meant to receive the event instead of the flow
        QGraphicsView.mouseReleaseEvent(self, event)

        if self.ignore_mouse_event or \
                (event.button() == Qt.LeftButton and not self.__left_mouse_pressed_in_flow):
            self.ignore_mouse_event = False
            return

        elif event.button() == Qt.MidButton:
            self.__panning = False


        # connection dropped over specific pin
        if self.dragging_connection and self.itemAt(event.pos()) and \
                isinstance(self.itemAt(event.pos()), PortInstPin):
            self.connect_port_insts__cmd(self.selected_pin.parent_port_instance,
                                         self.itemAt(event.pos()).parent_port_instance)

        # connection dropped above NodeInstance - auto connect
        elif self.dragging_connection and any(isinstance(item, NodeInstance) for item in self.items(event.pos())):
            # find node instance
            ni_under_drop = None
            for item in self.items(event.pos()):
                if isinstance(item, NodeInstance):
                    ni_under_drop = item
                    break
            # connect
            self.auto_connect(self.selected_pin.parent_port_instance, ni_under_drop)

        # connection dropped somewhere else - show node choice widget
        elif self.dragging_connection:
            self.__auto_connection_pin = self.selected_pin
            self.show_node_choice_widget(event.pos())

        self.__left_mouse_pressed_in_flow = False
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
        if self.stylus_mode == 'edit' and not self.__panning and not \
                (event.type() == QTabletEvent.TabletPress and event.button() == Qt.RightButton):
            return  # let the mousePress/Move/Release-Events handle it

        scaled_event_pos: QPointF = event.posF()/self.__current_scale

        if event.type() == QTabletEvent.TabletPress:
            self.ignore_mouse_event = True

            if event.button() == Qt.LeftButton:
                if self.stylus_mode == 'comment':
                    view_pos = self.mapToScene(self.viewport().pos())
                    new_drawing = self.__create_and_place_drawing__cmd(
                        view_pos + scaled_event_pos,
                        config={**self.__stylus_modes_widget.get_pen_settings(), 'viewport pos': view_pos}
                    )
                    self.__current_drawing = new_drawing
                    self.__drawing = True
            elif event.button() == Qt.RightButton:
                self.__panning = True
                self.__pan_last_x = event.x()
                self.__pan_last_y = event.y()

        elif event.type() == QTabletEvent.TabletMove:
            self.ignore_mouse_event = True
            if self.__panning:
                self.pan(event.pos())

            elif event.pointerType() == QTabletEvent.Eraser:
                if self.stylus_mode == 'comment':
                    for i in self.items(event.pos()):
                        if isinstance(i, DrawingObject):
                            self.remove_drawing(i)
                            break
            elif self.stylus_mode == 'comment' and self.__drawing:
                if self.__current_drawing.append_point(scaled_event_pos):
                    self.__current_drawing.stroke_weights.append(event.pressure())
                self.__current_drawing.update()
                self.viewport().update()

        elif event.type() == QTabletEvent.TabletRelease:
            if self.__panning:
                self.__panning = False
            if self.stylus_mode == 'comment' and self.__drawing:
                Debugger.write('drawing obj finished')
                self.__current_drawing.finish()
                self.__current_drawing = None
                self.__drawing = False

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

        if self.__showing_framerate:
            self.num_frames += 1
            pen = QPen(QColor('#A9D5EF'))
            pen.setWidthF(2)
            painter.setPen(pen)

            pos = self.mapToScene(10, 23)
            painter.setFont(QFont('Poppins', round(11*self.__total_scale_div)))
            painter.drawText(pos, "{:.2f}".format(self.framerate))


        # DRAW CURRENTLY DRAGGED CONNECTION
        if self.dragging_connection:
            pen = QPen('#101520')
            pen.setWidth(3)
            pen.setStyle(Qt.DotLine)
            painter.setPen(pen)

            pin_pos = self.selected_pin.get_scene_center_pos()
            sppi = self.selected_pin.parent_port_instance
            cursor_pos = self.__last_mouse_move_pos

            pos1 = pin_pos if sppi.io_pos == PortPos.OUTPUT else cursor_pos
            pos2 = pin_pos if sppi.io_pos == PortPos.INPUT else cursor_pos

            if sppi.type_ == 'data':
                painter.drawPath(
                    default_cubic_connection_path(pos1, pos2)
                )
            elif sppi.type_ == 'exec':
                painter.drawPath(
                    default_cubic_connection_path(pos1, pos2)
                )


        # DRAW SELECTED NIs BORDER
        for ni in self.selected_node_instances():
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
        img = QImage(self.sceneRect().width() / self.__total_scale_div, self.sceneRect().height() / self.__total_scale_div,
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
        self.__zoom_proxy.setPos(self.mapToScene(self.viewport().width() - self.__zoom_widget.width(), 0))

    def set_stylus_proxy_pos(self):
        self.__stylus_modes_proxy.setPos(
            self.mapToScene(self.viewport().width() - self.__stylus_modes_widget.width() - self.__zoom_widget.width(), 0))

    def __hide_proxies(self):
        self.__stylus_modes_proxy.hide()
        self.__zoom_proxy.hide()

    def __show_proxies(self):
        self.__stylus_modes_proxy.show()
        self.__zoom_proxy.show()

    # NODE CHOICE WIDGET
    def show_node_choice_widget(self, pos, nodes=None):
        """Opens the node choice dialog in the scene."""

        # calculating position
        self.__node_place_pos = self.mapToScene(pos)
        dialog_pos = QPoint(pos.x() + 1, pos.y() + 1)

        # ensure that the node_choice_widget stays in the viewport
        if dialog_pos.x() + self.__node_choice_widget.width() / self.__total_scale_div > self.viewport().width():
            dialog_pos.setX(dialog_pos.x() - (
                    dialog_pos.x() + self.__node_choice_widget.width() / self.__total_scale_div - self.viewport().width()))
        if dialog_pos.y() + self.__node_choice_widget.height() / self.__total_scale_div > self.viewport().height():
            dialog_pos.setY(dialog_pos.y() - (
                    dialog_pos.y() + self.__node_choice_widget.height() / self.__total_scale_div - self.viewport().height()))
        dialog_pos = self.mapToScene(dialog_pos)

        # open nodes dialog
        # the dialog emits 'node_chosen' which is connected to self.place_node,
        # so this all continues at self.place_node below
        self.__node_choice_widget.update_list(nodes if nodes is not None else self.session.nodes)
        self.__node_choice_widget.update_view()
        self.__node_choice_proxy.setPos(dialog_pos)
        self.__node_choice_proxy.show()
        self.__node_choice_widget.refocus()

    def hide_node_choice_widget(self):
        self.__node_choice_proxy.hide()
        self.__node_choice_widget.clearFocus()
        self.__auto_connection_pin = None

    # PAN
    def pan(self, new_pos):
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (new_pos.x() - self.__pan_last_x))
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - (new_pos.y() - self.__pan_last_y))
        self.__pan_last_x = new_pos.x()
        self.__pan_last_y = new_pos.y()

    # ZOOM
    def zoom_in(self, amount):
        local_viewport_center = QPoint(self.viewport().width() / 2, self.viewport().height() / 2)
        self.zoom(local_viewport_center, self.mapToScene(local_viewport_center), amount)

    def zoom_out(self, amount):
        local_viewport_center = QPoint(self.viewport().width() / 2, self.viewport().height() / 2)
        self.zoom(local_viewport_center, self.mapToScene(local_viewport_center), -amount)

    def zoom(self, p_abs, p_mapped, angle):
        by = 0
        velocity = 2 * (1 / self.__current_scale) + 0.5
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
            if self.__current_scale * by < 3:
                self.scale(by, by)
                self.__current_scale *= by
        elif direction == 'out':
            if scene_rect_width * by >= self.viewport().size().width() and scene_rect_height * by >= self.viewport().size().height():
                self.scale(by, by)
                self.__current_scale *= by

        w = self.viewport().width()
        h = self.viewport().height()
        wf = self.mapToScene(QPoint(w - 1, 0)).x() - self.mapToScene(QPoint(0, 0)).x()
        hf = self.mapToScene(QPoint(0, h - 1)).y() - self.mapToScene(QPoint(0, 0)).y()
        lf = p_mapped.x() - p_abs.x() * wf / w
        tf = p_mapped.y() - p_abs.y() * hf / h

        self.ensureVisible(lf, tf, wf, hf, 0, 0)

        target_rect = QRectF(QPointF(lf, tf),
                             QSizeF(wf, hf))
        self.__total_scale_div = target_rect.width() / self.viewport().width()

        self.ensureVisible(target_rect, 0, 0)

    # NODE PLACING: -----
    def create_node_instance(self, node, config) -> NodeInstance:
        """Creates and returns a new NodeInstance object."""

        # This is where a NodeInstance is finally instantiated.
        # - The brackets around node, self, config create a tuple (node, self, config). See NodeInstance constructor.
        # - The initialized() method needs to be called after all manual constructing has been done. This was once called
        # at the end of every custom NI's constructor, which can lead to problems when using custom NI class hierarchies.
        # That's why I moved it here.

        new_NI = (node.node_inst_class)((node, self, self.session.design, config))
        new_NI.initialized()
        return new_NI

    def add_node_instance(self, ni, pos=None):
        """Adds a NodeInstance to the scene."""

        self.scene().addItem(ni)
        ni.enable_logs()
        if pos:
            ni.setPos(pos)

        # select new NI
        self.scene().clearSelection()
        ni.setSelected(True)

        self.node_instances.append(ni)

    def add_node_instances(self, node_instances):
        """Adds a list of NodeInstances to the scene."""

        for ni in node_instances:
            self.add_node_instance(ni)

    def remove_node_instance(self, ni):
        """Removes a NodeInstance from the scene."""

        ni.about_to_remove_from_scene()  # to stop running threads

        self.scene().removeItem(ni)

        self.node_instances.remove(ni)

    def __place_new_node_by_shortcut(self):  # Shift+P
        point_in_viewport = None
        selected_NIs = self.selected_node_instances()
        if len(selected_NIs) > 0:
            x = selected_NIs[-1].pos().x() + 150
            y = selected_NIs[-1].pos().y()
            self.__node_place_pos = QPointF(x, y)
            point_in_viewport = self.mapFromScene(QPoint(x, y))
        else:  # place in center
            viewport_x = self.viewport().width() / 2
            viewport_y = self.viewport().height() / 2
            point_in_viewport = QPointF(viewport_x, viewport_y).toPoint()
            self.__node_place_pos = self.mapToScene(point_in_viewport)

        self.__node_choice_widget.reset_list()
        self.show_node_choice_widget(point_in_viewport)

    def place_nodes_from_config(self, nodes_config: list, offset_pos: QPoint = QPoint(0, 0)):
        """Creates NodeInstances and places them in the scene from nodes_config.
        The exact config list is included in what is returned by the config_data() method at 'nodes'."""

        new_node_instances = []

        for n_c in nodes_config:
            # find parent node by title, type, and description as identifiers
            parent_node_title = n_c['parent node title']
            # parent_node_package_name = n_c['parent node package']
            parent_node = None
            for pn in self.session.nodes:
                pn: Node = pn
                if pn.title == parent_node_title:
                    # and \
                    #     pn.package == parent_node_package_name:
                    parent_node = pn
                    break

            new_NI = self.create_node_instance(parent_node, n_c)
            self.add_node_instance(new_NI, QPoint(n_c['position x'], n_c['position y']) + offset_pos)
            new_node_instances.append(new_NI)

        return new_node_instances

    def place_node__cmd(self, node: Node, config=None):

        new_NI = self.create_node_instance(node, config)

        place_command = PlaceNodeInstanceInScene_Command(self, new_NI, self.__node_place_pos)

        self.__undo_stack.push(place_command)

        if self.__auto_connection_pin:
            self.auto_connect(self.__auto_connection_pin.parent_port_instance,
                              place_command.node_instance)

        return place_command.node_instance

    def remove_node_instance_triggered(self, node_instance):  # called from context menu of NodeInstance
        if node_instance in self.selected_node_instances():
            self.__undo_stack.push(
                RemoveComponents_Command(self, self.scene().selectedItems()))
        else:
            self.__undo_stack.push(RemoveComponents_Command(self, [node_instance]))

    # def get_node_instance_class_from_node(self, node):
    #     return self.all_node_instance_classes[node]

    # def get_custom_input_widget_classes(self):
    #     return self.script.main_window.custom_node_input_widget_classes

    def connect_nodes_from_config(self, node_instances: [NodeInstance], connections_config: list):
        """Connects NodeInstances according to the config list. This list is included in what is returned by the
        config_data() method at 'connections'."""

        for c in connections_config:
            c_parent_node_instance_index = c['parent node instance index']
            c_output_port_index = c['output port index']
            c_connected_node_instance = c['connected node instance']
            c_connected_input_port_index = c['connected input port index']

            if c_connected_node_instance is not None:  # which can be the case when pasting
                parent_node_instance = node_instances[c_parent_node_instance_index]
                connected_node_instance = node_instances[c_connected_node_instance]

                self.connect_pins(parent_node_instance.outputs[c_output_port_index],
                                  connected_node_instance.inputs[c_connected_input_port_index])

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

    def __create_and_place_drawing__cmd(self, posF, config=None):
        new_drawing_obj = self.create_drawing(config)
        place_command = PlaceDrawingObject_Command(self, posF, new_drawing_obj)
        self.__undo_stack.push(place_command)
        return new_drawing_obj

    def __move_selected_copmonents__cmd(self, x, y):
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
            self.__undo_stack.push(
                MoveComponents_Command(self, self.scene().selectedItems(), p_from=-new_rel_pos, p_to=QPointF(0, 0))
            )

        self.viewport().repaint()

    def __move_selected_nodes_left(self):
        self.__move_selected_copmonents__cmd(-40, 0)

    def __move_selected_nodes_up(self):
        self.__move_selected_copmonents__cmd(0, -40)

    def __move_selected_nodes_right(self):
        self.__move_selected_copmonents__cmd(+40, 0)

    def __move_selected_nodes_down(self):
        self.__move_selected_copmonents__cmd(0, +40)

    def selected_components_moved(self, pos_diff):
        items_list = self.scene().selectedItems()

        self.__undo_stack.push(MoveComponents_Command(self, items_list, p_from=-pos_diff, p_to=QPointF(0, 0)))

    def selected_node_instances(self) -> [NodeInstance]:
        """Returns a list of the currently selected NodeInstances."""

        selected_NIs = []
        for i in self.scene().selectedItems():
            if isinstance(i, NodeInstance):
                selected_NIs.append(i)
        return selected_NIs

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

    def __copy(self):  # ctrl+c
        data = {'nodes': self.__get_node_instances_config_data(self.selected_node_instances()),
                'connections': self.__get_connections_config_data(self.selected_node_instances()),
                'drawings': self.__get_drawings_config_data(self.selected_drawings())}
        QGuiApplication.clipboard().setText(json.dumps(data))

    def __cut(self):  # called from shortcut ctrl+x
        data = {'nodes': self.__get_node_instances_config_data(self.selected_node_instances()),
                'connections': self.__get_connections_config_data(self.selected_node_instances()),
                'drawings': self.__get_drawings_config_data(self.selected_drawings())}
        QGuiApplication.clipboard().setText(json.dumps(data))
        self.remove_selected_components()

    def __paste(self):
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

            offset_for_middle_pos = self.__last_mouse_move_pos - rect.center()

        self.__undo_stack.push(Paste_Command(self, data, offset_for_middle_pos))

    def add_component(self, e):
        if isinstance(e, NodeInstance):
            self.add_node_instance(e)
        elif isinstance(e, DrawingObject):
            self.add_drawing(e)

    def remove_components(self, comps):
        for c in comps:
            self.remove_component(c)

    def remove_component(self, e):
        if isinstance(e, NodeInstance):
            self.remove_node_instance(e)
        elif isinstance(e, DrawingObject):
            self.remove_drawing(e)

    def remove_selected_components(self):
        self.__undo_stack.push(
            RemoveComponents_Command(self, self.scene().selectedItems()))

        self.viewport().update()

    # NODE SELECTION: ----
    def clear_selection(self):
        self.scene().clearSelection()

    # CONNECTIONS: ----
    def connect_port_insts__cmd(self, p1: PortInstance, p2: PortInstance):
        """Connects if possible, disconnects if ports are already connected"""

        out = None
        inp = None
        if p1.io_pos == PortPos.OUTPUT and p2.io_pos == PortPos.INPUT:
            out = p1
            inp = p2
        elif p1.io_pos == PortPos.INPUT and p2.io_pos == PortPos.OUTPUT:
            out = p2
            inp = p1
        else:
            # ports have same direction
            return

        if out.type_ != inp.type_:
            return

        self.__undo_stack.push(ConnectPorts_Command(self, out=out, inp=inp))

    def connect_pins(self, out: PortInstance = None, inp: PortInstance = None, connection: Connection = None):
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

        if inp.parent_node_instance == out.parent_node_instance:
            return


        # CONNECT

        # remove all connections from input port instance if it's a data input
        if inp.type_ == 'data':
            for c in inp.connections:
                self.connect_port_insts__cmd(c.out, inp)


        if connection:
            self.add_connection(connection)
            connection.out.connected()
            connection.inp.connected()
            return


        c = self.new_connection(out, inp)
        self.add_connection(c)

        out.connected()
        inp.connected()

    def new_connection(self, out: PortInstance, inp: PortInstance) -> Connection:
        """Creates the connection object"""
        c = None
        if inp.type_ == 'data':
            c = self.session.flow_data_conn_class((out, inp, self.session.design))
        elif inp.type_ == 'exec':
            c = self.session.flow_exec_conn_class((out, inp, self.session.design))
        c.setZValue(10)
        return c

    def add_connection(self, c: Connection):
        """Adds the connection object to the scene"""
        c.out.connections.append(c)
        c.inp.connections.append(c)

        self.connections.append(c)

        self.scene().addItem(c)
        self.viewport().repaint()

    def remove_connection(self, c: Connection):
        """Removes the connection object from the scene"""
        c.out.connections.remove(c)
        c.inp.connections.remove(c)

        self.connections.remove(c)

        self.scene().removeItem(c)
        self.viewport().repaint()

    def auto_connect(self, pi: PortInstance, ni: NodeInstance):
        if pi.io_pos == PortPos.OUTPUT:
            for inp in ni.inputs:
                if pi.type_ == inp.type_:
                    # connect exactly once
                    self.connect_port_insts__cmd(pi, inp)
                    return
        elif pi.io_pos == PortPos.INPUT:
            for out in ni.outputs:
                if pi.type_ == out.type_:
                    # connect exactly once
                    self.connect_port_insts__cmd(pi, out)
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

    def config_data(self):
        flow_dict = {'algorithm mode': FlowAlg.stringify(self.alg_mode),
                     'viewport update mode': VPUpdateMode.stringify(self.vp_update_mode),
                     'nodes': self.__get_node_instances_config_data(self.node_instances),
                     'connections': self.__get_connections_config_data(self.node_instances),
                     'drawings': self.__get_drawings_config_data(self.drawings)}
        return flow_dict

    def __get_node_instances_config_data(self, node_instances):
        script_node_instances_list = []
        for ni in node_instances:
            node_instance_dict = ni.config_data()
            script_node_instances_list.append(node_instance_dict)

        return script_node_instances_list

    def __get_connections_config_data(self, node_instances, only_with_connections_to=None):
        script_ni_connections_list = []
        for ni in node_instances:
            for out in ni.outputs:
                if len(out.connections) > 0:
                    for c in out.connections:
                        connected_port = c.inp

                        # this only applies when saving config data through deleting node instances:
                        if only_with_connections_to is not None and \
                                connected_port.parent_node_instance not in only_with_connections_to and \
                                ni not in only_with_connections_to:
                            continue
                        # because I am not allowed to save connections between nodes connected to each other and both
                        # connected to the deleted node, only the connections to the deleted node shall be saved

                        connection_dict = {'parent node instance index': node_instances.index(ni),
                                           'output port index': ni.outputs.index(out)}

                        # yes, very important: when copying components, there might be connections going outside the
                        # selected lists, these should be ignored. When saving a project, all components are considered,
                        # so then the index values will never be none
                        connected_ni_index = node_instances.index(connected_port.parent_node_instance) if \
                            node_instances.__contains__(connected_port.parent_node_instance) else \
                            None
                        connection_dict['connected node instance'] = connected_ni_index

                        connected_ip_index = connected_port.parent_node_instance.inputs.index(connected_port) if \
                            connected_ni_index is not None else None
                        connection_dict['connected input port index'] = connected_ip_index

                        script_ni_connections_list.append(connection_dict)

        return script_ni_connections_list

    def __get_drawings_config_data(self, drawings):
        drawings_list = []
        for drawing in drawings:
            drawing_dict = drawing.config_data()

            drawings_list.append(drawing_dict)

        return drawings_list
