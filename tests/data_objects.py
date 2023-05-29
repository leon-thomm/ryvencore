import unittest
import ryvencore as rc


class DataTypesBasic(unittest.TestCase):

    class Producer(rc.Node):
        init_outputs = [rc.NodeOutputType()]

        def update_event(self, inp=-1):
            self.set_output_val(0, rc.Data(42))

    class Consumer(rc.Node):
        init_inputs = [rc.NodeInputType()]

        def __init__(self, params):
            super().__init__(params)

            self.x = None

        def update_event(self, inp=-1):
            self.x = self.input(0).payload

    def runTest(self):
        s = rc.Session()
        s.register_node_types([self.Producer, self.Consumer])
        f = s.create_flow('main')
        n1 = f.create_node(self.Producer)
        n2 = f.create_node(self.Consumer)
        f.connect_nodes(n1.outputs[0], n2.inputs[0])
        n1.update()

        self.assertTrue(isinstance(n1.outputs[0].val, rc.Data))
        self.assertEqual(n2.x, 42)


class DataTypesCustom(unittest.TestCase):

    class MyData(rc.Data):
        def get_data(self):
            return {
                'info': 'something important',
                'data': self.payload
            }

        def set_data(self, data):
            self.payload = data['data']

    class Producer(rc.Node):
        init_outputs = [rc.NodeOutputType()]

        def update_event(self, inp=-1):
            self.set_output_val(0, DataTypesCustom.MyData(42))

    class Consumer(rc.Node):
        init_inputs = [rc.NodeInputType()]

        def __init__(self, params):
            super().__init__(params)
            self.x = None

        def update_event(self, inp=-1):
            self.x = self.input(0).payload

    def runTest(self):
        s = rc.Session()
        s.register_node_types([self.Producer, self.Consumer])
        s.register_data_type(self.MyData)
        f = s.create_flow('main')
        n1 = f.create_node(self.Producer)
        n2 = f.create_node(self.Consumer)
        f.connect_nodes(n1.outputs[0], n2.inputs[0])
        n1.update()
        self.assertTrue(isinstance(n1.outputs[0].val, DataTypesCustom.MyData))
        self.assertTrue(isinstance(n1.outputs[0].val, self.MyData))

        project = s.serialize()
        rc.utils.json_print(project)

        s2 = rc.Session()
        s2.register_node_types([self.Producer, self.Consumer])
        s2.register_data_type(self.MyData)
        s2.load(project)
        f2 = s2.flows[0]
        n2_1, n2_2 = f2.nodes
        self.assertTrue(isinstance(n2_1.outputs[0].val, self.MyData))
        n2_1.update()
        self.assertEqual(n2_2.x, 42)


if __name__ == '__main__':
    unittest.main()
