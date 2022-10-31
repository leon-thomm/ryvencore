import json
import unittest
import ryvencore as rc
from utils import check_addon_available

check_addon_available('Variables', __file__)

from ryvencore.addons.default.Variables import addon as Variables
from ryvencore.addons.default.Logging import addon as Logging


class NodeBase(rc.Node):

    def __init__(self, params):
        super().__init__(params)

        self.Vars: Variables = self.get_addon('Variables')
        self.Logging: Logging = self.get_addon('Logging')

    def place_event(self):
        if not self.Vars._var_exists(self.flow, 'var1'):
            self.Vars.create_var(self.flow, 'var1', 'Hello, World!')


class Node1(NodeBase):
    title = 'node 1'
    init_inputs = []
    init_outputs = [rc.NodeOutputType(type_='data'), rc.NodeOutputType(type_='data')]

    def __init__(self, params):
        super().__init__(params)

        self.var_val = None

        self.log1 = self.Logging.new_logger(self, 'log1')
        self.log2 = self.Logging.new_logger(self, 'log2')

    def subscribe_to_var1(self):
        self.Vars.subscribe(self, 'var1', self.var1_changed)
        self.var_val = self.Vars.var(self.flow, 'var1').get()

    def update_event(self, inp=-1):
        self.set_output_val(0, rc.Data('Hello, World!'))
        self.set_output_val(1, rc.Data(42))
        print('finished')

    def var1_changed(self, val):
        self.var_val = val
        print('var1 changed in slot:', val)
        self.update()


class Node2(NodeBase):
    title = 'node 2'
    init_inputs = [rc.NodeInputType()]
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

        f = s.create_flow('main')

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

        n1.subscribe_to_var1()
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

        f2 = s2.flows[0]
        assert vars.var(f2, 'var1').get() == 42

        n1_2, n2_2, n3_2, n4_2 = f2.nodes

        assert n1_2.var_val == 42
        assert n2_2.input(0).payload == 'Hello, World!'
        assert n3_2.input(0).payload == 42
        assert n4_2.input(0).payload == 42

        n1_2.update()
        n2_2.update_var1(43)

        assert n1_2.var_val == 43


if __name__ == '__main__':
    unittest.main()
