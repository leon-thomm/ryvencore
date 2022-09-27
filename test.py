import json
import unittest
import ryvencore as rc
from ryvencore import Data
from ryvencore.addons.default.Variables import addon as VarsAddon


class NodeBase(rc.Node):

    def __init__(self, params):
        super().__init__(params)

        self.Vars: VarsAddon = self.get_addon('Variables')

    def place_event(self):
        if not self.Vars._var_exists(self.flow, 'var1'):
            self.Vars.create_var(self.flow, 'var1', 'Hello, World!')


class Node1(NodeBase):
    title = 'node 1'
    init_inputs = []
    init_outputs = [rc.NodeOutputBP(type_='data'), rc.NodeOutputBP(type_='data')]

    def __init__(self, params):
        super().__init__(params)

        self.var_val = None

    def place_event(self):
        super().place_event()

        self.Vars.subscribe(self, 'var1', self.var1_changed)
        self.var_val = self.Vars.var(self.flow, 'var1').get()

    def update_event(self, inp=-1):
        self.set_output_val(0, Data('Hello, World!'))
        self.set_output_val(1, Data(42))
        print('finished')

    def var1_changed(self, val):
        self.var_val = val
        print('var1 changed in slot:', val)
        self.update()


class Node2(NodeBase):
    title = 'node 2'
    init_inputs = [rc.NodeInputBP('data')]
    init_outputs = []

    def update_event(self, inp=-1):
        print(f'received data on input {inp}: {self.input(inp)}')

    def update_var1(self, val):
        self.Vars.var(self.flow, 'var1').set(val)
        print('var1 successfully updated:', val)


class DataFlowBasic(unittest.TestCase):

    def runTest(self):
        s = rc.Session()
        s.register_nodes([Node1, Node2])

        f = s.create_script('main').flow

        n1 = f.create_node(Node1)
        n2 = f.create_node(Node2)
        n3 = f.create_node(Node2)
        n4 = f.create_node(Node2)

        f.connect_nodes(n1.outputs[0], n2.inputs[0])
        f.connect_nodes(n1.outputs[1], n3.inputs[0])
        f.connect_nodes(n1.outputs[1], n4.inputs[0])

        # test data model

        self.assertEqual(n1.outputs[0].val, None)
        self.assertEqual(n1.outputs[1].val, None)

        n1.update()

        self.assertEqual(n1.outputs[0].val.payload, 'Hello, World!')
        self.assertEqual(n1.outputs[1].val.payload, 42)
        self.assertEqual(n3.input(0), n4.input(0))

        # test variables addon

        n2.update_var1(42)
        assert n1.var_val == 42

        print('----------------------------------------------------------')

        # test save and load

        project = s.serialize()
        print(json.dumps(project, indent=4))
        del s

        s2 = rc.Session()
        s2.register_nodes([Node1, Node2])
        s2.load(project)

        vars = s2.addons.get('Variables')

        f2 = s2.scripts[0].flow
        assert vars.var(f2, 'var1').get() == 42

        n1_2, n2_2, n3_2, n4_2 = f2.nodes

        assert n1_2.var_val == 42
        assert n2_2.input(0).payload == 'Hello, World!'
        assert n3_2.input(0).payload == 42
        assert n4_2.input(0).payload == 42

        n1_2.update()
        n2_2.update_var1(43)

        assert n1_2.var_val == 43


class ExecFlowBasic(unittest.TestCase):

    class Node1(rc.Node):
        title = 'node 1'
        init_inputs = []
        init_outputs = [rc.NodeOutputBP(type_='exec'), rc.NodeOutputBP(type_='data')]

        def update_event(self, inp=-1):
            self.set_output_val(1, Data('Hello, World!'))
            self.exec_output(0)
            print('finished')

    class Node2(rc.Node):
        title = 'node 2'
        init_inputs = [rc.NodeInputBP(type_='exec'), rc.NodeInputBP(type_='data')]
        init_outputs = []

        def __init__(self, params):
            super().__init__(params)

            self.data = None

        def update_event(self, inp=-1):
            self.data = self.input(1)
            print(f'received data on input {inp}: {self.input(inp)}')


    def runTest(self):
        # rc.InfoMsgs.enable(True)
        s = rc.Session()
        f = s.create_script('main').flow
        f.set_algorithm_mode('exec')

        n1 = f.create_node(Node1)
        n2 = f.create_node(Node2)
        n3 = f.create_node(Node2)

        f.connect_nodes(n1.outputs[0], n2.inputs[0])
        f.connect_nodes(n1.outputs[1], n2.inputs[1])
        f.connect_nodes(n1.outputs[0], n3.inputs[0])
        # f.connect_nodes(n1.outputs[1], n3.inputs[1])

        self.assertEqual(n1.outputs[0].val, None)
        self.assertEqual(n1.outputs[1].val, None)

        n1.update()

        self.assertEqual(n1.outputs[1].val.payload, 'Hello, World!')
        self.assertEqual(n2.val.payload, 'Hello, World!')
        self.assertEqual(n3.val, None)
