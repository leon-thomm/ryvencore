import json
import unittest
import ryvencore as rc


class NodeBase(rc.Node):
    pass


class Node1(NodeBase):
    title = 'node 1'
    init_inputs = []
    init_outputs = [rc.NodeOutputType(type_='data'), rc.NodeOutputType(type_='data')]

    def update_event(self, inp=-1):
        self.set_output_val(0, rc.Data('Hello, World!'))
        self.set_output_val(1, rc.Data(42))
        print('finished')


class Node2(NodeBase):
    title = 'node 2'
    init_inputs = [rc.NodeInputType(default=rc.Data('default value'))]
    init_outputs = []

    def update_event(self, inp=-1):
        print(f'received data on input {inp}: {self.input(inp)}')


class DataFlowBasic(unittest.TestCase):

    def runTest(self):
        s = rc.Session()
        s.register_node_types([Node1, Node2])

        f = s.create_flow('main')

        n1 = f.create_node(Node1)
        n2 = f.create_node(Node2)
        n3 = f.create_node(Node2)
        n4 = f.create_node(Node2)

        n2.update()

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

        # test save and load

        project = s.serialize()
        print(json.dumps(project, indent=4))
        del s

        s2 = rc.Session()
        s2.register_node_types([Node1, Node2])
        s2.load(project)
        f2 = s2.flows[0]

        n1_2, n2_2, n3_2, n4_2 = f2.nodes

        assert n2_2.input(0).payload == 'Hello, World!'
        assert n3_2.input(0).payload == 42
        assert n4_2.input(0).payload == 42

        n1_2.update()


if __name__ == '__main__':
    unittest.main()
