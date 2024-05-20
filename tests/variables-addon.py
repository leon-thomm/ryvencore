import json
import unittest
import ryvencore as rc
from .utils import check_addon_available

check_addon_available('Variables', __file__)

from ryvencore.addons.Variables import addon as Variables


class NodeBase(rc.Node):

    def __init__(self, params):
        super().__init__(params)

        self.Vars: Variables = self.get_addon('Variables')

    def create_var1(self):
        if not self.Vars.var_exists(self.flow, 'var1'):
            self.Vars.create_var(self.flow, 'var1', 'Hello, World!')


class Node1(NodeBase):
    title = 'node 1'
    init_inputs = []
    init_outputs = [
        rc.NodeOutputType(),
        rc.NodeOutputType()
    ]

    def __init__(self, params):
        super().__init__(params)

        self.var_val = None

    def subscribe_to_var1(self):
        self.Vars.subscribe(self, 'var1', self.on_var1_changed)
        self.var_val = self.Vars.var(self.flow, 'var1').get()

    def update_event(self, inp=-1):
        self.set_output_val(0, rc.Data('Hello, World!'))
        self.set_output_val(1, rc.Data(42))
        print('finished')

    def on_var1_changed(self, val):
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


class VariablesBasic(unittest.TestCase):

    def runTest(self):
        s = rc.Session(load_addons=True)
        s.register_node_types([Node1, Node2])

        f = s.create_flow('main')

        n1 = f.create_node(Node1)
        n2 = f.create_node(Node2)
        n3 = f.create_node(Node2)
        n4 = f.create_node(Node2)

        f.connect_nodes(n1.outputs[0], n2.inputs[0])
        f.connect_nodes(n1.outputs[1], n3.inputs[0])
        f.connect_nodes(n1.outputs[1], n4.inputs[0])

        n1.create_var1()

        n1.update()

        self.assertEqual(n1.outputs[0].val.payload, 'Hello, World!')
        self.assertEqual(n1.outputs[1].val.payload, 42)
        self.assertEqual(n3.input(0), n4.input(0))

        # test variables addon

        n1.subscribe_to_var1()
        n2.update_var1(42)
        assert n1.var_val.get() == 42

        print('----------------------------------------------------------')

        # test save and load

        project = s.serialize()
        print(json.dumps(project, indent=4))
        del s

        s2 = rc.Session(load_addons=True)
        s2.register_node_types([Node1, Node2])
        s2.load(project)

        vars = s2.addons.get('Variables')

        f2 = s2.flows[0]
        self.assertEqual(vars.var(f2, 'var1').get(), 42)

        n1_2, n2_2, n3_2, n4_2 = f2.nodes
        n2_2.update_var1('test')

        self.assertEqual(n1_2.var_val.get(), 'test')
        self.assertEqual(n3_2.input(0).payload, 42)
        self.assertEqual(n4_2.input(0).payload, 42)

        n1_2.update()
        n2_2.update_var1(43)

        self.assertEqual(n1_2.var_val.get(), 43)


if __name__ == '__main__':
    unittest.main()
