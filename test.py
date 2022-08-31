import unittest
import ryvencore as rc


class DataFlowBasic(unittest.TestCase):

    class Node1(rc.Node):
        title = 'node 1'
        init_inputs = []
        init_outputs = [rc.NodeOutputBP(type_='data'), rc.NodeOutputBP(type_='data')]

        def update_event(self, inp=-1):
            self.set_output_val(0, 'Hello, World!')
            self.set_output_val(1, 42)
            print('finished')

    class Node2(rc.Node):
        title = 'node 2'
        init_inputs = [rc.NodeInputBP('data')]
        init_outputs = []

        def update_event(self, inp=-1):
            print(f'received data on input {inp}: {self.input(inp)}')

    def runTest(self):
        s = rc.Session()
        f = s.create_script('main').flow

        n1 = f.create_node(self.Node1)
        n2 = f.create_node(self.Node2)
        n3 = f.create_node(self.Node2)

        f.connect_nodes(n1.outputs[0], n2.inputs[0])
        f.connect_nodes(n1.outputs[1], n3.inputs[0])

        self.assertEqual(n1.outputs[0].val, None)
        self.assertEqual(n1.outputs[1].val, None)

        n1.update()

        self.assertEqual(n1.outputs[0].val, 'Hello, World!')
        self.assertEqual(n1.outputs[1].val, 42)


class ExecFlowBasic(unittest.TestCase):

    class Node1(rc.Node):
        title = 'node 1'
        init_inputs = []
        init_outputs = [rc.NodeOutputBP(type_='exec'), rc.NodeOutputBP(type_='data')]

        def update_event(self, inp=-1):
            self.set_output_val(1, 'Hello, World!')
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
        s = rc.Session()
        f = s.create_script('main').flow
        f.set_algorithm_mode('exec')

        n1 = f.create_node(self.Node1)
        n2 = f.create_node(self.Node2)
        n3 = f.create_node(self.Node2)

        f.connect_nodes(n1.outputs[0], n2.inputs[0])
        f.connect_nodes(n1.outputs[1], n2.inputs[1])
        f.connect_nodes(n1.outputs[0], n3.inputs[0])
        # f.connect_nodes(n1.outputs[1], n3.inputs[1])

        self.assertEqual(n1.outputs[0].val, None)
        self.assertEqual(n1.outputs[1].val, None)

        n1.update()

        self.assertEqual(n1.outputs[1].val, 'Hello, World!')
        self.assertEqual(n2.data, 'Hello, World!')
        self.assertEqual(n3.data, None)
