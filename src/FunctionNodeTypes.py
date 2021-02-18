from .Node import Node
from .GlobalAttributes import Location


class FunctionInputNode(Node):
    identifier = 'BUILTIN_FunctionInputNode'
    title = 'input'

    def __init__(self, params):
        super().__init__(params)

        self.special_actions = {
            'add parameter': {
                'data': {'method': self.add_function_param, 'data': 'data'},
                'exec': {'method': self.add_function_param, 'data': 'exec'}
            },
            'remove parameter': {

            }
        }

    def add_function_param(self, type_):
        self.create_output(type_, '')

        self.special_actions['remove parameter'][str(len(self.outputs))] = {
            'method': self.remove_function_param,
            'data': len(self.outputs)-1
        }

        self.script.add_parameter(type_, '')

    def remove_function_param(self, index):
        self.delete_output(index)
        del self.special_actions['remove parameter'][str(index+1)]

        # decrease all higher indices
        actions = self.special_actions['remove parameter']
        i = 0
        visited = []
        while i < len(actions.keys()):
            k = list(actions.keys())[i]
            v: dict = actions[k]
            if int(k) > index and int(k) not in visited:
                v['data'] = v['data'] - 1
                new_val = str(int(k)-1)
                actions[new_val] = v
                visited.append(int(new_val))
                del actions[k]
                i -= 1
            i += 1

        self.script.remove_parameter(index)


    def get_data(self):
        return {

        }

    def set_data(self, data):
        pass


class FunctionOutputNode(Node):
    identifier = 'BUILTIN_FunctionOutputNode'
    title = 'output'

    def __init__(self, params):
        super().__init__(params)

        self.special_actions = {
            'add return': {
                'data': {'method': self.add_function_return, 'data': 'data'},
                'exec': {'method': self.add_function_return, 'data': 'exec'}
            },
            'remove return': {

            }
        }

    def add_function_return(self, type_):
        self.create_input(type_)

        self.special_actions['remove return'][str(len(self.inputs))] = {
            'method': self.remove_function_return,
            'data': len(self.inputs)-1
        }

        self.script.add_return(type_, '')

    def remove_function_return(self, index):
        self.delete_input(index)
        del self.special_actions['remove return'][str(index+1)]

        # decrease all higher indices
        actions = self.special_actions['remove return']
        i = 0
        visited = []
        while i < len(actions.keys()):
            k = list(actions.keys())[i]
            v: dict = actions[k]
            if int(k) > index and int(k) not in visited:
                v['data'] = v['data'] - 1
                new_val = str(int(k)-1)
                actions[new_val] = v
                visited.append(int(new_val))
                del actions[k]
                i -= 1
            i += 1

        self.script.remove_return(index)

    def update_event(self, input_called=-1):
        self.script.exec_return(input_called)


class FunctionScriptNode(Node):
    instances = []
    function_script = None
    icon = Location.PACKAGE_PATH+'/resources/pics/function_picture.png'

    def __init__(self, params):
        super().__init__(params)

        self.instances.append(self)

        if not self.init_config:
            # catch up on params and returns
            for p in self.function_script.parameters:
                self.create_input(p['type'], p['label'])
            for r in self.function_script.returns:
                self.create_output(r['type'], r['label'])

    def update_event(self, input_called=-1):
        if input_called != -1:
            self.function_script.caller_stack.append(self)
            self.function_script.exec_input(input_called, self)
        else:
            self.function_script.output_node.update(-1)

    def get_data(self):
        data = self.function_script.title
        return data

    def set_data(self, data):
        # find parent function script
        for fs in self.session.function_scripts:
            if fs.title == data:
                self.function_script = fs
                break
