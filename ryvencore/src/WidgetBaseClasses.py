"""The base classes for node custom widgets for nodes."""


class MWB:
    """MainWidgetBase"""

    def __init__(self, params):
        self.node, self.node_item = params

    def get_data(self):
        data = {}
        return data

    def set_data(self, data):
        pass

    def remove_event(self):
        pass

    def update_node_shape(self):
        self.node_item.update_shape()


class IWB:
    """InputWidgetBase"""

    def __init__(self, params):
        self.input, self.input_item, self.node, self.node_item = params

    def get_data(self):
        data = {}
        return data

    def set_data(self, data):
        pass

    def remove_event(self):
        pass

    def val_update_event(self, val):
        pass

    def update_node_shape(self):
        self.node_item.update_shape()
