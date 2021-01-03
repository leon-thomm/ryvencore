from PySide2.QtCore import QObject

from .NodeItem import NodeItem
from .NodeObjPort import NodeObjInput, NodeObjOutput
from .NodePort import NodeInput, NodeOutput
from .RC import FlowVPUpdateMode
from .logging.Log import Log
from .retain import M
from .global_tools.Debugger import Debugger


class Node(QObject):

    # FIELDS
    init_inputs: [NodeInput] = []
    init_outputs: [NodeOutput] = []
    title = ''
    type_ = ''
    description = ''
    main_widget_class = None
    main_widget_pos = 'below ports'
    input_widget_classes = {}
    style = 'extended'
    color = '#c69a15'

    def __init__(self, params):
        super().__init__()

        self.flow, design, config = params
        self.script = self.flow.script
        self.session = self.script.session
        self.inputs: [NodeInput] = []
        self.outputs: [NodeOutput] = []
        self.default_actions = default_node_actions
        self.special_actions = {}
        self.logs = []

        self.init_config = config

        self.item = NodeItem(self, params)

    def finish_initialization(self):

        if self.init_config:
            self.setup_ports(self.init_config['inputs'], self.init_config['outputs'])

            self.special_actions = self.set_special_actions_data(self.init_config['special actions'])

            try:
                self.set_data(self.init_config['state data'])
            except Exception as e:
                print('Exception while setting data in', self.title, 'Node:', e,
                      ' (was this intended?)')
        else:
            self.setup_ports()

        self.item.initialized()

        self.initialized()

        self.update()

    def setup_ports(self, inputs_config=None, outputs_config=None):

        if not inputs_config and not outputs_config:
            for i in range(len(self.init_inputs)):
                inp = self.init_inputs[i]
                self.create_input(inp.type_, inp.label,
                                  widget_name=self.init_inputs[i].widget_name,
                                  widget_pos =self.init_inputs[i].widget_pos)

            for o in range(len(self.init_outputs)):
                out = self.init_outputs[o]
                self.create_output(out.type_, out.label)
        else:  # when loading saved NIs, the init_inputs and init_outputs are irrelevant
            for inp in inputs_config:
                has_widget = inp['has widget']

                self.create_input(type_=inp['type'], label=inp['label'],
                                  widget_name=inp['widget name'] if has_widget else None,
                                  widget_pos =inp['widget position'] if has_widget else None,
                                  config=inp['widget data'] if has_widget else None)

            for out in outputs_config:
                self.create_output(out['type'], out['label'])

    def main_widget(self):
        return self.item.main_widget




    #                        __                             _    __     __
    #              ____ _   / /  ____ _   ____     _____   (_)  / /_   / /_     ____ ___
    #             / __ `/  / /  / __ `/  / __ \   / ___/  / /  / __/  / __ \   / __ `__ \
    #            / /_/ /  / /  / /_/ /  / /_/ /  / /     / /  / /_   / / / /  / / / / / /
    #            \__,_/  /_/   \__, /   \____/  /_/     /_/   \__/  /_/ /_/  /_/ /_/ /_/
    #                         /____/

    def update(self, input_called=-1, output_called=-1):
        """This is the method used to activate a Node. Note that this signature shadows the update() method from
        QGraphicsItem used to graphically update a QGraphicsItem which can be accessed via
        QGraphicsItem.update(self)."""

        # if self.session_design.animations_enabled:
        #     self.animator.start()
        self.item.node_updated()

        Debugger.write('update in', self.title, 'on input', input_called)
        try:
            self.update_event(input_called)
        except Exception as e:
            Debugger.write_err('EXCEPTION IN', self.title, 'NI:', e)

    def update_event(self, input_called=-1):
        """Gets called when an input received a signal. This is where the magic begins in subclasses."""

        pass

    def input(self, index: int):
        """Returns the value of a data input.
        If the input is connected, the value of the connected output is used:
        If not, the value of the widget is used."""

        Debugger.write('input called in', self.title, 'NI:', index)
        return self.inputs[index].get_val()

    def input_widget(self, index: int):
        return self.inputs[index].item.widget

    def exec_output(self, index: int):
        """Executes an execution output, sending a signal to all connected execution inputs causing the connected
        NIs to update."""
        self.outputs[index].exec()

    def set_output_val(self, index, val):
        """Sets the value of a data output.
        self.data_outputs_updated() has to be called manually after all values are set."""

        if self.flow.vp_update_mode == FlowVPUpdateMode.ASYNC and not self.item.initializing:  # asynchronous viewport updates
            vp = self.flow.viewport()
            vp.repaint(self.flow.mapFromScene(self.item.sceneBoundingRect()))

        self.outputs[index].set_val(val)

    def remove_event(self):
        """Method to stop all threads in hold of the NI itself."""

        pass

    #                                 _
    #              ____ _   ____     (_)
    #             / __ `/  / __ \   / /
    #            / /_/ /  / /_/ /  / /
    #            \__,_/  / .___/  /_/
    #                   /_/
    #
    # all algorithm-unrelated api methods:

    def initialized(self):
        pass

    #   LOGGING
    def new_log(self, title) -> Log:
        """Requesting a new personal Log."""
        # new_log = self.script.logger.new_log(self, title)
        new_log = self.script.logger.new_log(title)
        self.logs.append(new_log)
        return new_log

    def disable_logs(self):
        """Disables personal Logs. They remain visible unless the user closes them via the appearing button."""
        for log in self.logs:
            log.disable()

    def enable_logs(self):
        """Resets personal Logs to normal state (hiding close button, changing style sheet)."""
        for log in self.logs:
            log.enable()

    def log_message(self, msg: str, target: str):
        """Writes a string to a default log with title target"""

        self.script.logger.log_message(msg, target)

    # SHAPE
    def update_shape(self):
        """Causes recompilation of the whole shape."""
        self.item.update_shape()

    # PORTS
    def create_input(self, type_: str = 'data', label: str = '', widget_name=None,
                     widget_pos='besides', pos=-1, config=None):
        """
        Creates and adds a new input.
        :widget_pos: 'besides' or 'below'
        """
        Debugger.write('create_new_input called')



        # backwards compatibility
        widget_pos = widget_pos if widget_pos != 'under' else 'below'

        inp = NodeObjInput(
            node=self,
            type_=type_,
            label_str=label,
            widget_name=widget_name,
            widget_pos=widget_pos,
            config_data=config
        )

        if pos < -1:
            pos += len(self.inputs)
        if pos == -1:
            self.inputs.append(inp)
        else:
            self.inputs.insert(pos, inp)

        self.item.add_new_input(inp, pos)

        if self.session.threading_enabled:
            inp.moveToThread(self.flow.worker_thread)


    def delete_input(self, i):
        """Disconnects and removes input."""
        inp: NodeObjInput = None
        if type(i) == int:
            inp = self.inputs[i]
        elif type(i) == NodeObjInput:
            inp = i

        # break all connections
        for c in inp.connections:
            self.flow.connect_ports(c.out, inp)

        self.inputs.remove(inp)
        self.item.remove_input(inp)


    def create_output(self, type_: str = 'data', label: str = '', pos=-1):
        """Creates and adds a new output."""

        out = NodeObjOutput(
              node=self,
              type_=type_,
              label_str=label
        )

        # pi = OutputPortInstance(self, type_, label)
        if pos < -1:
            pos += len(self.outputs)
        if pos == -1:
            self.outputs.append(out)
        else:
            self.outputs.insert(pos, out)

        self.item.add_new_output(out, pos)

        if self.session.threading_enabled:
            out.moveToThread(self.flow.worker_thread)

    def delete_output(self, o):
        """Disconnects and removes output. Handy for subclasses."""
        out: NodeObjOutput = None
        if type(o) == int:
            out = self.outputs[o]
        elif type(o) == NodeObjOutput:
            out = o

        # break all connections
        for c in out.connections:
            self.flow.connect_ports(out, c.inp)

        self.outputs.remove(out)
        self.item.remove_output(out)


    # GET, SET DATA
    def get_data(self):
        """
        This method gets subclassed and specified. If the NI has states (so, the behavior depends on certain values),
        all these values must be stored in JSON-able format in a dict here. This dictionary will be used to reload the
        node's state when loading a project or pasting copied/cut nodes in the Flow (the states get copied too), see
        self.set_data(self, data) below.
        Unfortunately, I can't use pickle or something like that due to PySide2 which runs on C++, not Python.
        :return: Dictionary representing all values necessary to determine the NI's current state
        """
        return {}

    def set_data(self, data):
        """
        If the NI has states, it's state should get reloaded here according to what was previously provided by the same
        class in get_data(), see above.
        :param data: Dictionary representing all values necessary to determine the NI's current state
        """
        pass

    def session_stylesheet(self) -> str:
        return self.flow.session.design.global_stylesheet

    # VARIABLES

    def get_vars_manager(self):
        return self.script.vars_manager

    def get_var_val(self, name: str):
        return self.get_vars_manager().get_var_val(name)

    def set_var_val(self, name: str, val):
        return self.get_vars_manager().set_var(name, val)

    def register_var_receiver(self, name: str, method):
        self.get_vars_manager().register_receiver(self, name, method)

    def unregister_var_receiver(self, name: str):
        self.get_vars_manager().unregister_receiver(self, name)







    def set_special_actions_data(self, actions_data):
        actions = {}
        for key in actions_data:
            if type(actions_data[key]) != dict:
                if key == 'method':
                    try:
                        actions['method'] = M(getattr(self, actions_data[key]))
                    except AttributeError:  # outdated method referenced
                        pass
                elif key == 'data':
                    actions['data'] = actions_data[key]
            else:
                actions[key] = self.set_special_actions_data(actions_data[key])
        return actions


    def get_special_actions_data(self, actions):
        cleaned_actions = actions.copy()
        for key in cleaned_actions:
            v = cleaned_actions[key]
            if type(v) == M:  # callable(v):
                cleaned_actions[key] = v.method_name
            elif callable(v):
                cleaned_actions[key] = v.__name__
            elif type(v) == dict:
                cleaned_actions[key] = self.get_special_actions_data(v)
            else:
                cleaned_actions[key] = v
        return cleaned_actions

    def get_extended_default_actions(self):
        actions_dict = self.default_actions.copy()
        for index in range(len(self.inputs)):
            inp = self.inputs[index]
            if inp.type_ == 'exec':
                actions_dict['exec input '+str(index)] = {'method': self.action_exec_input,
                                                          'data': {'input index': index}}
        return actions_dict

    def action_exec_input(self, data):
        self.update(data['input index'])

    def action_remove(self):
        self.item.flow.remove_node_item(self.item)

    def about_to_remove_from_scene(self):
        """Called from Flow when the NI gets removed from the scene
        to stop all running threads and disable personal logs."""

        if self.main_widget():
            self.main_widget().remove_event()
        self.remove_event()

        self.disable_logs()

    def is_active(self):
        for i in self.inputs:
            if i.type_ == 'exec':
                return True
        for o in self.outputs:
            if o.type_ == 'exec':
                return True
        return False

    def has_main_widget(self):
        """Might be used later in CodePreview_Widget to enable not only showing the NI's class but also it's
        main_widget's class."""
        return self.main_widget() is not None


    def config_data(self):
        """Returns all metadata of the NI including position, package etc. in a JSON-able dict format.
        Used to rebuild the Flow when loading a project."""

        # general attributes
        node_dict = {'identifier': self.__class__.__name__,
                     'position x': self.item.pos().x(),
                     'position y': self.item.pos().y()}
        if self.main_widget():
            node_dict['main widget data'] = self.main_widget().get_data()

        node_dict['state data'] = self.get_data()
        node_dict['special actions'] = self.get_special_actions_data(self.special_actions)

        # inputs
        inputs = []
        for i in self.inputs:
            input_dict = i.config_data()
            inputs.append(input_dict)
        node_dict['inputs'] = inputs

        # outputs
        outputs = []
        for o in self.outputs:
            output_dict = o.config_data()
            outputs.append(output_dict)
        node_dict['outputs'] = outputs

        return node_dict






default_node_actions = {'remove': {'method': Node.action_remove},
                   'update shape': {'method': Node.update_shape}}
