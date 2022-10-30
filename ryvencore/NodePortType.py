
# TODO: make this a dataclass
class NodePortType:
    """
    The NodePortBP classes are only placeholders (BP = BluePrint) for the static init_input and
    init_outputs of custom Node classes.
    An instantiated Node's actual inputs and outputs will be of type NodeObjPort (NodeObjInput, NodeObjOutput).
    """

    def __init__(self, label: str = '', type_: str = 'data'):

        self.type_: str = type_
        self.label: str = label


class NodeInputType(NodePortType):
    def __init__(self, label: str = '', type_: str = 'data', add_data={}):
        super().__init__(label, type_)

        self.add_data = add_data


class NodeOutputType(NodePortType):
    def __init__(self, label: str = '', type_: str = 'data'):
        super().__init__(label, type_)
