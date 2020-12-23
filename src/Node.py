class NodePort:
    def __init__(self,
                 type_: str = 'data',
                 label: str = '',
                 widget: str = None,
                 widget_pos: str = 'besides'):
        """
        :type_: 'data' or 'exec'
        :label: the displayed name
        :widget: the input widget's name if used
        :widget_pos: 'besides' or 'below'
        """
        self.type_: str = type_
        self.label: str = label
        self.widget_name: str = widget
        self.widget_pos = widget_pos



class Node:
    def __init__(
            self,
            title: str,
            node_inst_class,
            inputs: [NodePort] = [],
            input_widgets: dict = {},
            outputs: [NodePort] = [],
            description: str = '',
            style: str = 'extended',
            color: str = '#A9D5EF',
            widget=None,
            widget_pos: str = 'below ports',
            type_: str = ''
    ):
        """
        :title: the node's displayed title
        :node_inst_class: the class of the corresponding NodeInstance
        :inputs: a list of NodePorts
        :input_widgets: a {name: class} dict. Provide all custom input widgets you may want to use under a
        unique name which you can then use to access it through the API
        (when calling create_new_input(widget_name=...)).
        :outputs: a list of NodePorts
        :description: shown when hovering over the NodeInstance
        :style: 'extended' or 'small'
        :color: color in hex format
        :widget: the main widget's class if used
        :widget_pos: 'between ports' or 'below ports'
        """

        self.title = title
        self.node_inst_class = node_inst_class
        self.inputs = inputs
        self.outputs = outputs
        self.description = description
        self.design_style = style
        self.color = color
        self.main_widget_class = widget
        self.main_widget_pos = widget_pos if widget_pos != 'under ports' else 'below ports'
        self.type_ = type_
        self.custom_input_widgets = input_widgets
