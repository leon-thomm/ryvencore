import unittest
import ryvencore as rc

from ryvencore.data.built_in import *
from ryvencore.data.built_in.collections.abc import *
from ryvencore.data import Data, check_valid_data
from ryvencore.NodePort import check_valid_conn

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
        f.connect_nodes(n1._outputs[0], n2._inputs[0])
        n1.update()

        self.assertTrue(isinstance(n1._outputs[0].val, rc.Data))
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
        f.connect_nodes(n1._outputs[0], n2._inputs[0])
        n1.update()
        self.assertTrue(isinstance(n1._outputs[0].val, DataTypesCustom.MyData))
        self.assertTrue(isinstance(n1._outputs[0].val, self.MyData))

        project = s.serialize()
        rc.utils.json_print(project)

        s2 = rc.Session()
        s2.register_node_types([self.Producer, self.Consumer])
        s2.register_data_type(self.MyData)
        s2.load(project)
        f2 = s2.flows[0]
        n2_1, n2_2 = f2.nodes
        self.assertTrue(isinstance(n2_1._outputs[0].val, self.MyData))
        n2_1.update()
        self.assertEqual(n2_2.x, 42)


class DataTypesBuiltIn(unittest.TestCase):
    
    class Producer(rc.Node):
        init_outputs = [
            rc.NodeOutputType(allowed_data=ComplexData),
            rc.NodeOutputType(allowed_data=ListData),
        ]

        def update_event(self, inp=-1):
            self.set_output_payload(0, 42 + 2j)

    class Consumer(rc.Node):
        init_inputs = [
            rc.NodeInputType(allowed_data=NumberData),
            rc.NodeInputType(allowed_data=ListData),
            rc.NodeInputType(allowed_data=SequenceData),
        ]

        def __init__(self, params):
            super().__init__(params)

            self.x = None

        def update_event(self, inp=-1):
            self.x = self.input(0).payload
            
    def runTest(self):
        self.assertTrue(check_valid_data(ListData, SequenceData))
        self.assertFalse(check_valid_data(NumberData, IntegerData))
        self.assertTrue(check_valid_data(IntegerData, ComplexData))
        
        s = rc.Session()
        self.assertTrue(s.get_data_type(ListData.identifier) is not None)
        
        s.register_node_types([DataTypesBuiltIn.Producer, DataTypesBuiltIn.Consumer])
        f = s.create_flow('flow')
        n1 = f.create_node(self.Producer)
        n2 = f.create_node(self.Consumer)
        
        self.assertIsNotNone(f.connect_nodes(n1._outputs[0], n2._inputs[0])) # ComplexData -> NumberData should be ok
        self.assertIsNone(f.connect_nodes(n1._outputs[0], n2._inputs[1])) # ComplexData -> ListData should not be ok
        
        n1.set_output_val(0, RealData(23.0))
        self.assertTrue(n2.input_payload(0) == 23)
        self.assertTrue(isinstance(n2.input(0), ComplexData))
        self.assertFalse(isinstance(n2.input(0), IntegerData))
        
        self.assertIsNotNone(f.connect_nodes(n1._outputs[1], n2._inputs[1])) # ListData -> ListData should be ok
        self.assertIsNotNone(f.connect_nodes(n1._outputs[1], n2._inputs[2])) # ListData -> SequenceData should be ok 
        
        n1.set_output_val(1, ListData([1, 2, 3]))
        self.assertTrue(isinstance(n2.input(1), ListData))

        
if __name__ == '__main__':
    unittest.main()
