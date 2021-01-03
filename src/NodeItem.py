from PySide2.QtWidgets import QGraphicsItem, QMenu, QGraphicsDropShadowEffect
from PySide2.QtCore import Qt, QRectF
from PySide2.QtGui import QColor

from .NodeObjPort import NodeObjInput, NodeObjOutput
from .NodeItemAction import NodeItemAction
from .NodeItemAnimator import NodeItemAnimator
from .NodeItemWidget import NodeItemWidget
from .RC import FlowVPUpdateMode
from .global_tools.Debugger import Debugger
from .global_tools.MovementEnum import MovementEnum
from .logging.Log import Log

from .PortItem import InputPortItem, OutputPortItem
from .retain import M


class NodeItem(QGraphicsItem):

    # # FIELDS
    # init_inputs = []
    # init_outputs = []
    # title = ''
    # type_ = ''
    # description = ''
    # main_widget_class = None
    # main_widget_pos = 'below ports'
    # input_widget_classes = {}
    # style = 'extended'
    # color = '#c69a15'

    def __init__(self, node, params):
        super(NodeItem, self).__init__()

        self.node = node
        flow, design, config = params
        self.flow = flow
        self.session_design = design
        self.movement_state = None
        self.movement_pos_from = None
        self.painted_once = False
        self.inputs = []
        self.outputs = []
        self.color = QColor(self.node.color)  # manipulated by self.animator

        # self.default_actions = {'remove': {'method': self.action_remove},
        #                         'update shape': {'method': self.update_shape}}
                                # 'console ref': {'method': self.set_console_scope}}  # for context menus
        # self.special_actions = {}  # only gets written in custom NodeInstance-subclasses
        self.personal_logs = []

        # 'initializing' will be set to False below. It's needed for the ports setup, to prevent shape updating stuff
        self.initializing = True

        # self.temp_state_data = None
        self.init_config = config


        # FLAGS
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsScenePositionChanges)
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)



        # UI
        self.shadow_effect = None
        self.main_widget = None
        if self.node.main_widget_class is not None:
            self.main_widget = self.node.main_widget_class(self.node)
        self.widget = NodeItemWidget(self.node, self)  # QGraphicsWidget(self)

        self.animator = NodeItemAnimator(self)  # needs self.title_label

        # TOOLTIP
        if self.node.description != '':
            self.setToolTip('<html><head/><body><p>'+self.node.description+'</p></body></html>')
        self.setCursor(Qt.SizeAllCursor)

        # DESIGN THEME
        self.session_design.flow_theme_changed.connect(self.update_design)



    def initialized(self):
        """All ports and the main widget get finally created here."""

        # LOADING CONFIG
        if self.init_config is not None:
            # self.setPos(config['position x'], config['position y'])
            # self.setup_ports(self.init_config['inputs'], self.init_config['outputs'])
            if self.main_widget:
                try:
                    self.main_widget.set_data(self.init_config['main widget data'])
                except Exception as e:
                    print('Exception while setting data in', self.title, 'Node\'s main widget:', e,
                          ' (was this intended?)')

            # self.special_actions = self.set_special_actions_data(self.init_config['special actions'])
            # self.temp_state_data = self.init_config['state data']
        # else:
        #     self.setup_ports()


        self.initializing = False

        # No self.update_shape() here because for some reason, the bounding rect hasn't been initialized yet, so
        # self.update_shape() gets called when the item is being drawn the first time (see paint event in NI painter)
        # TODO: change that ^ once there is a solution for this: https://forum.qt.io/topic/117179/force-qgraphicsitem-to-update-immediately-wait-for-update-event

        self.update_design()  # load current design, update QGraphicsItem

        self.update()  # ... not sure if I need that



    # --------------------------------------------------------------------------------------
    # UI STUFF ----------------------------------------

    # def set_console_scope(self):
    #     # extensive_dict = {}  # unlike self.__dict__, it also includes methods to call! :)
    #     # for att in dir(self):
    #     #     extensive_dict[att] = getattr(self, att)
    #     MainConsole.main_console.add_obj_context(self)

    def node_updated(self):
        if self.session_design.animations_enabled:
            self.animator.start()


    def add_new_input(self, inp: NodeObjInput, pos: int):
        if pos == -1:
            self.inputs.append(inp.item)
            self.widget.add_input_to_layout(inp.item)
        else:
            self.inputs.insert(pos, inp.item)
            self.widget.insert_input_into_layout(pos, inp.item)

        if not self.initializing:
            self.update_shape()
            self.update()

    def remove_input(self, inp: NodeObjInput):
        item = inp.item

        # for some reason, I have to remove all widget items manually from the scene too. setting the items to
        # ownedByLayout(True) does not work, I don't know why.
        self.scene().removeItem(item.pin)
        self.scene().removeItem(item.label)
        if item.proxy is not None:
            self.scene().removeItem(item.proxy)

        self.inputs.remove(item)
        self.widget.remove_input_from_layout(item)

        if not self.initializing:
            self.update_shape()
            self.update()

    def add_new_output(self, out: NodeObjOutput, pos: int):
        if pos == -1:
            self.outputs.append(out.item)
            self.widget.add_output_to_layout(out.item)
        else:
            self.outputs.insert(pos, out.item)
            self.widget.insert_output_into_layout(pos, out.item)

        if not self.initializing:
            self.update_shape()
            self.update()

    def remove_output(self, out: NodeObjOutput):
        item = out.item

        # see remove_input() for info!
        self.scene().removeItem(item.pin)
        self.scene().removeItem(item.label)

        self.outputs.remove(item)
        self.widget.remove_output_from_layout(item)

        if not self.initializing:
            self.update_shape()
            self.update()


    def update_shape(self):
        self.widget.update_shape()
        self.flow.viewport().update()

    def update_design(self):
        """Loads the shadow effect option and causes redraw with active theme."""

        if self.session_design.node_item_shadows_enabled:
            self.shadow_effect = QGraphicsDropShadowEffect()
            self.shadow_effect.setXOffset(12)
            self.shadow_effect.setYOffset(12)
            self.shadow_effect.setBlurRadius(20)
            self.shadow_effect.setColor(QColor('#2b2b2b'))
            self.setGraphicsEffect(self.shadow_effect)
        else:
            self.setGraphicsEffect(None)

        self.widget.update()
        self.animator.reload_values()

        QGraphicsItem.update(self)

    def boundingRect(self):
        # remember: (0, 0) shall be the NI's center!
        rect = QRectF()
        w = self.widget.layout().geometry().width()
        h = self.widget.layout().geometry().height()
        rect.setLeft(-w/2)
        rect.setTop(-h/2)
        rect.setWidth(w)
        rect.setHeight(h)
        return rect

    #   PAINTING
    def paint(self, painter, option, widget=None):
        """All painting is done by NodeItemPainter"""

        # in order to access a meaningful geometry of GraphicsWidget contents in update_shape(), the paint event
        # has to be called once. See here:
        # https://forum.qt.io/topic/117179/force-qgraphicsitem-to-update-immediately-wait-for-update-event/4
        if not self.painted_once:

            # ok, quick notice. Since I am using a NodeItemWidget, calling self.update_design() here (again)
            # leads to a QT crash without error, which is really strange. Calling update_design multiple times
            # principally isn't a problem, but, for some reason, here it leads to a crash in QT. It's not necessary
            # anymore, so I just removed it.
            # self.update_design()

            self.update_shape()
            self.update_conn_pos()

        self.session_design.flow_theme.node_item_painter.paint_NI(
            design_style=self.node.style,
            painter=painter,
            option=option,
            c=self.color,
            w=self.boundingRect().width(),
            h=self.boundingRect().height(),
            bounding_rect=self.boundingRect(),
            title_rect=self.widget.title_label.boundingRect()
        )

        self.painted_once = True

    def get_context_menu(self):
        menu = QMenu(self.flow)

        for a in self.get_actions(self.node.get_extended_default_actions(), menu):  # menu needed for 'parent'
            if type(a) == NodeItemAction:
                menu.addAction(a)
            elif type(a) == QMenu:
                menu.addMenu(a)

        menu.addSeparator()

        actions = self.get_actions(self.node.special_actions, menu)
        for a in actions:  # menu needed for 'parent'
            if type(a) == NodeItemAction:
                menu.addAction(a)
            elif type(a) == QMenu:
                menu.addMenu(a)

        return menu

    def itemChange(self, change, value):
        """This method ensures that all connections, selection borders etc. that get drawn in the Flow are constantly
        redrawn during a NI drag. Also updates the positions of connections"""

        if change == QGraphicsItem.ItemPositionChange:
            if self.session_design.performance_mode == 'pretty':
                self.flow.viewport().update()
            if self.movement_state == MovementEnum.mouse_clicked:
                self.movement_state = MovementEnum.position_changed

        self.update_conn_pos()

        return QGraphicsItem.itemChange(self, change, value)

    def update_conn_pos(self):
        """Updates the global positions of connections at outputs"""
        for o in self.node.outputs:
            for c in o.connections:
                c.item.recompute()
        for i in self.node.inputs:
            for c in i.connections:
                c.item.recompute()

    def hoverEnterEvent(self, event):
        self.widget.title_label.set_NI_hover_state(hovering=True)
        QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        self.widget.title_label.set_NI_hover_state(hovering=False)
        QGraphicsItem.hoverLeaveEvent(self, event)

    def mousePressEvent(self, event):
        """Used for Moving-Commands in Flow - may be replaced later with a nicer determination of a moving action."""
        self.movement_state = MovementEnum.mouse_clicked
        self.movement_pos_from = self.pos()
        return QGraphicsItem.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """Used for Moving-Commands in Flow - may be replaced later with a nicer determination of a moving action."""
        if self.movement_state == MovementEnum.position_changed:
            self.flow.selected_components_moved(self.pos() - self.movement_pos_from)
        self.movement_state = None
        return QGraphicsItem.mouseReleaseEvent(self, event)

    # ACTIONS
    def get_actions(self, actions_dict, menu):
        actions = []

        for k in actions_dict:
            v_dict = actions_dict[k]
            try:
                method = v_dict['method']
                data = None
                try:
                    data = v_dict['data']
                except KeyError:
                    pass
                action = NodeItemAction(k, menu, data)
                action.triggered_with_data.connect(method)  # see NodeItemAction for explanation
                action.triggered_without_data.connect(method)  # see NodeItemAction for explanation
                actions.append(action)
            except KeyError:
                action_menu = QMenu(k, menu)
                sub_actions = self.get_actions(v_dict, action_menu)
                for a in sub_actions:
                    action_menu.addAction(a)
                actions.append(action_menu)

        return actions

    # def get_special_actions_data(self, actions):
    #     cleaned_actions = actions.copy()
    #     for key in cleaned_actions:
    #         v = cleaned_actions[key]
    #         if type(v) == M:  # callable(v):
    #             cleaned_actions[key] = v.method_name
    #         elif callable(v):
    #             cleaned_actions[key] = v.__name__
    #         elif type(v) == dict:
    #             cleaned_actions[key] = self.get_special_actions_data(v)
    #         else:
    #             cleaned_actions[key] = v
    #     return cleaned_actions

    # def set_special_actions_data(self, actions_data):
    #     actions = {}
    #     for key in actions_data:
    #         if type(actions_data[key]) != dict:
    #             if key == 'method':
    #                 try:
    #                     actions['method'] = M(getattr(self, actions_data[key]))
    #                 except AttributeError:  # outdated method referenced
    #                     pass
    #             elif key == 'data':
    #                 actions['data'] = actions_data[key]
    #         else:
    #             actions[key] = self.set_special_actions_data(actions_data[key])
    #     return actions

    # PORTS
    # def setup_ports(self, inputs_config=None, outputs_config=None):
    #     if not inputs_config and not outputs_config:
    #         for i in range(len(self.init_inputs)):
    #             inp = self.init_inputs[i]
    #             self.create_new_input(inp.type_, inp.label,
    #                                   widget_name=self.init_inputs[i].widget_name,
    #                                   widget_pos =self.init_inputs[i].widget_pos)
    #
    #         for o in range(len(self.init_outputs)):
    #             out = self.init_outputs[o]
    #             self.create_new_output(out.type_, out.label)
    #     else:  # when loading saved NIs, the port instances might not be synchronised to the parent's ports anymore
    #         for inp in inputs_config:
    #             has_widget = inp['has widget']
    #
    #             self.create_new_input(inp['type'], inp['label'],
    #                                   widget_name=inp['widget name'] if has_widget else None,
    #                                   widget_pos =inp['widget position'] if has_widget else None,
    #                                   config=inp['widget data'] if has_widget else None)
    #
    #         for out in outputs_config:
    #             self.create_new_output(out['type'], out['label'])

    # def add_input_to_scene(self, i):
    #     self.flow.scene().addItem(i.pin)
    #     self.flow.scene().addItem(i.label)
    #     if i.widget:
    #         self.flow.scene().addItem(i.proxy)
    #
    # def add_output_to_scene(self, o):
    #     self.flow.scene().addItem(o.pin)
    #     self.flow.scene().addItem(o.label)

    # # GENERAL
    # def about_to_remove_from_scene(self):
    #     """Called from Flow when the NI gets removed from the scene
    #     to stop all running threads and disable personal logs."""
    #
    #     if self.main_widget:
    #         self.main_widget.remove_event()
    #     self.remove_event()
    #
    #     self.disable_logs()
    #
    # def is_active(self):
    #     for i in self.inputs:
    #         if i.type_ == 'exec':
    #             return True
    #     for o in self.outputs:
    #         if o.type_ == 'exec':
    #             return True
    #     return False
    #
    # def has_main_widget(self):
    #     """Might be used later in CodePreview_Widget to enable not only showing the NI's class but also it's
    #     main_widget's class."""
    #     return self.main_widget is not None

    # def get_input_widgets(self):
    #     """Might be used later in CodePreview_Widget to enable not only showing the NI's class but its input widgets'
    #     classes."""
    #     input_widgets = []
    #     for i in range(len(self.inputs)):
    #         inp = self.inputs[i]
    #         if inp.widget is not None:
    #             input_widgets.append({i: inp.widget})
    #     return input_widgets

    # def config_data(self):
    #     """Returns all metadata of the NI including position, package etc. in a JSON-able dict format.
    #     Used to rebuild the Flow when loading a project."""
    #
    #     # general attributes
    #     node_instance_dict = {'parent node title': self.title,
    #                           'parent node type': self.type_,
    #                           # 'parent node package': self.parent_node.package,
    #                           'parent node description': self.description,
    #                           'position x': self.pos().x(),
    #                           'position y': self.pos().y()}
    #     if self.main_widget:
    #         node_instance_dict['main widget data'] = self.main_widget.get_data()
    #
    #     node_instance_dict['state data'] = self.get_data()
    #     node_instance_dict['special actions'] = self.get_special_actions_data(self.special_actions)
    #
    #     # inputs
    #     node_instance_inputs_list = []
    #     for i in self.inputs:
    #         input_dict = i.config_data()
    #         node_instance_inputs_list.append(input_dict)
    #     node_instance_dict['inputs'] = node_instance_inputs_list
    #
    #     # outputs
    #     node_instance_outputs_list = []
    #     for o in self.outputs:
    #         output_dict = o.config_data()
    #         node_instance_outputs_list.append(output_dict)
    #     node_instance_dict['outputs'] = node_instance_outputs_list
    #
    #     return node_instance_dict