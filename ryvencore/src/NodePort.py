class NodePort:
    """
    The NodePorts (NodeInputs and NodeOutputs) are only placeholders for the static init_input and init_outputs of
    the API.
    An instantiated Node's actual inputs and outputs will be of type NodeObjPort (NodeObjInput, NodeObjOutput).
    """

    def __init__(self,
                 type_: str = 'data',
                 label: str = ''):
        """
        :type_: 'data' or 'exec'
        :label: the displayed name
        """
        self.type_: str = type_
        self.label: str = label


class NodeInput(NodePort):
    def __init__(self,
                 type_: str = 'data',
                 label: str = '',
                 widget: str = None,
                 widget_pos: str = 'besides'):

        super().__init__(type_, label)

        self.widget_name: str = widget
        self.widget_pos = widget_pos


class NodeOutput(NodePort):
    def __init__(self,
                 type_: str = 'data',
                 label: str = ''):
        super().__init__(type_, label)