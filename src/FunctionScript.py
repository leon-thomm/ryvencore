from .Script import Script
from .FunctionNodeTypes import FunctionInputNode, FunctionOutputNode, FunctionScriptNode


class FunctionScript(Script):
    def __init__(self, session, title: str = None, config_data: dict = None, flow_view_size: list = None,
                 create_default_logs=True):

        super().__init__(session, title, config_data, flow_view_size, create_default_logs,
                         False)  # initialization blocked here!


        class CustomFunctionScriptNode(FunctionScriptNode):
            identifier = 'FUNCTION_NODE_'+self.title
            # notice that script titles have to be unique!
            # and the script's title has already been set in Script.__init__

            title = self.title
            function_script = self


        self.function_node_class = CustomFunctionScriptNode
        self.session.register_node(self.function_node_class)

        self.input_node, self.output_node = None, None
        self.parameters: [dict] = []
        self.returns: [dict] = []
        # self.current_caller: FunctionScriptNode = None
        self.caller_stack: [FunctionScriptNode] = []


    def initialize(self):
        if self.init_config:
            self.parameters = self.init_config['parameters']
            self.returns = self.init_config['returns']

        super().initialize()

        if self.init_config:
            # find input and output node that have already been created by the flow
            for node in self.flow.nodes:
                if node.identifier == FunctionInputNode.identifier:
                    self.input_node = node
                elif node.identifier == FunctionOutputNode.identifier:
                    self.output_node = node
        else:
            self.input_node = self.flow.create_node(FunctionInputNode)
            self.output_node = self.flow.create_node(FunctionOutputNode)


    def add_parameter(self, type_, label):
        self.parameters.append({'type': type_, 'label': label})

        for fn in self.function_node_class.instances:
            fn: FunctionScriptNode
            fn.create_input(type_, label)

    def remove_parameter(self, index):
        self.parameters.remove(self.parameters[index])

        for fn in self.function_node_class.instances:
            fn: FunctionScriptNode
            fn.delete_input(index)

    def add_return(self, type_, label):
        self.returns.append({'type': type_, 'label': label})

        for fn in self.function_node_class.instances:
            fn: FunctionScriptNode
            fn.create_output(type_, label)

    def remove_return(self, index):
        self.returns.remove(self.returns[index])

        for fn in self.function_node_class.instances:
            fn: FunctionScriptNode
            fn.delete_output(index)

    def exec_input(self, index: int, caller: FunctionScriptNode):
        self.caller_stack.append(caller)

        if self.parameters[index]['type'] == 'data':
            self.input_node.set_output_val(index, caller.input(index))
        else:
            self.input_node.exec_output(index)

        self.caller_stack.pop()

    def exec_return(self, index: int):
        if self.returns[index]['type'] == 'data':
            self.caller_stack[-1].set_output_val(index, self.output_node.input(index))
        else:
            self.self.caller_stack[-1].exec_output(index)


    def serialize(self) -> dict:
        script_dict = super().serialize()

        script_dict['parameters'] = self.parameters
        script_dict['returns'] = self.returns

        return script_dict
