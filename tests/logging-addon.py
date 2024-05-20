import unittest
import ryvencore as rc
from .utils import check_addon_available

check_addon_available('Logging', __file__)

from ryvencore.addons.Logging import addon as Logging


class NodeBase(rc.Node):

    def __init__(self, params):
        super().__init__(params)

        self.Logging: Logging = self.get_addon('Logging')


class Node1(NodeBase):
    title = 'node 1'
    init_inputs = []
    init_outputs = [rc.NodeOutputType(type_='data'), rc.NodeOutputType(type_='data')]

    def __init__(self, params):
        super().__init__(params)

        self.log1 = self.Logging.new_logger(self, 'log1')
        self.log2 = self.Logging.new_logger(self, 'log2')

    def update_event(self, inp=-1):
        self.set_output_val(0, rc.Data('Hello, World!'))
        self.set_output_val(1, rc.Data(42))
        print('finished')


class Node2(NodeBase):
    title = 'node 2'
    init_inputs = [rc.NodeInputType()]
    init_outputs = []

    def update_event(self, inp=-1):
        print(f'received data on input {inp}: {self.input(inp)}')


class DataFlowBasic(unittest.TestCase):

    def runTest(self):
        s = rc.Session(load_addons=True)
        s.register_node_types([Node1, Node2])

        f = s.create_flow('main')

        # TODO: logging tests


if __name__ == '__main__':
    unittest.main()
