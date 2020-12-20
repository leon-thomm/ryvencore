class Node:
    def __init__(
            self,
            title: str,
            node_inst_class,
            inputs: list = [],
            input_widgets: dict = {},
            outputs: list = [],
            description: str = '',
            style: str = 'extended',
            color: str = '#A9D5EF',
            widget=None,
            widget_pos: str = 'under ports',
            type_: str = ''
    ):

        self.title = title
        self.node_inst_class = node_inst_class
        self.inputs = inputs
        self.outputs = outputs
        self.description = description
        self.design_style = style
        self.color = color
        self.main_widget_class = widget
        self.main_widget_pos = widget_pos
        self.type_ = type_
        self.custom_input_widgets = input_widgets


class NodePort:
    def __init__(self,
                 type_: str = 'data',
                 label: str = '',
                 widget: str = None,
                 widget_pos: str = 'under'):
        self.type_ = type_
        self.label = label
        self.widget_name = widget
        self.widget_pos = widget_pos
