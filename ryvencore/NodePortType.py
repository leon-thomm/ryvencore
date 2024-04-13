from typing import Optional
from dataclasses import dataclass
from .data.Data import Data


@dataclass
class NodePortType:
    """
    The NodePortBP classes are only placeholders (BP = BluePrint) for the static init_input and
    init_outputs of custom Node classes.
    An instantiated Node's actual inputs and outputs will be of type NodeObjPort (NodeObjInput, NodeObjOutput).
    """

    label: str = ''
    type_: str = 'data'
    allowed_data: Data = None
        

class NodeInputType(NodePortType):
    
    default: Optional[Data] = None


class NodeOutputType(NodePortType):
    pass
