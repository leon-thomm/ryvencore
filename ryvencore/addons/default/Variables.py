from typing import Optional

from ryvencore import Node
from ryvencore.Base import Base, Event
from ryvencore.utils import serialize, deserialize
from ryvencore import AddOn



class Variable:
    """
    *currently disabled; breaking changes upcoming*

    Implementation of flow variables.
    A Variable can currently only hold pickle serializable data.
    Storing other data will break save&load.
    """

    def __init__(self, addon, flow, name='', val=None, data=None):
        self.addon = addon
        self.flow = flow
        self.name = name
        self.val = val

        if data and 'serialized' in data.keys():
            self.val = deserialize(data['serialized'])

    def get(self):
        """
        Returns the value of the variable
        """
        return self.val

    def set(self, val):
        """
        Sets the value of the variable
        """
        self.val = val
        self.addon._var_updated(self.flow, self.name)

    def serialize(self):
        return serialize(self.val)




class VarsAddon(AddOn):
    """
    This addon provides a simple variable system.

    It provides an API to create Variable objects which can wrap any Python object.

    Nodes can subscribe to variable names with a callback that is executed once a
    variable with that name changes or is created. The callback must be a method of
    the node, so the subscription can be re-established on loading.

    This way nodes can react to changes of data and non-trivial data-flow is introduced,
    meaning that data dependencies are determined also by variable subscriptions and not
    purely by the edges in the graph anymore. This can be useful, but it can also prevent
    optimization. Variables are flow-local.

    >>> import ryvencore as rc
    >>>
    >>> class MyNode(rc.Node):
    ...     init_outputs = []
    ...
    ...     def __init__(self, params):
    ...         super().__init__(params)
    ...
    ...         self.Vars = self.get_addon('Variables')
    ...         self.var_val = None
    ...
    ...     def place_event(self):
    ...         self.Vars.subscribe(self, 'var1', self.var1_changed)
    ...         self.var_val = self.Vars.var(self.flow, 'var1').get()
    ...
    ...     def var1_changed(self, val):
    ...         print('var1 changed!')
    ...         self.var_val = val
    >>>
    >>> s = rc.Session()
    >>> s.register_node(MyNode)
    >>> f = s.create_flow('main')
    >>>
    >>> Vars = s.addons['Variables']
    >>> v = Vars.create_var(f, 'var1', None)
    >>>
    >>> n1 = f.create_node(MyNode)
    >>> v.set(42)
    var1 changed!
    >>> print(n1.var_val)
    42
    """

    name = 'Variables'
    version = '0.0.3'

    def __init__(self):
        AddOn.__init__(self)

        # {
        #   Flow: {
        #       'variable name': {
        #           'var': Variable,
        #           'subscriptions': [Node method]
        #        },
        # }
        self.flow_variables = {}

    def var_name_valid(self, flow, name: str) -> bool:
        """
        Checks if ``name`` is a valid variable identifier and hasn't been take yet.
        """

        return name.isidentifier() and not self._var_exists(flow, name)

    def create_var(self, flow, name: str, val=None, data=None) -> Optional[Variable]:
        """
        Creates and returns a new variable and None if the name isn't valid.
        """

        if flow not in self.flow_variables:
            self.flow_variables[flow] = {}

        if self.var_name_valid(flow, name):
            v = Variable(self, flow, name, val, data)
            self.flow_variables[flow][name] = {
                'var': v,
                'subscriptions': []
            }
            return v
        else:
            return None

    def delete_var(self, flow, name: str):
        """
        Deletes a variable and causes subscription update. Subscriptions are preserved.
        """
        if not self._var_exists(flow, name):
            return

        del self.flow_variables[flow][name]['var']

    def _var_exists(self, flow, name: str) -> bool:
        return flow in self.flow_variables and name in self.flow_variables[flow]

    def var(self, flow, name: str):
        """
        Returns the variable with the given name or None if it doesn't exist.
        """
        if not self._var_exists(flow, name):
            return None

        return self.flow_variables[flow][name]['var']

    def _var_updated(self, flow, name: str):
        """
        Called when a Variable object changes or when the var is created or deleted.
        """

        v = self.flow_variables[flow][name]['var']

        for (node, cb) in self.flow_variables[flow][name]['subscriptions']:
            cb(v.val)

    def subscribe(self, node: Node, name: str, callback):
        """
        Subscribe to a variable. ``callback`` must be a method of the node.
        """
        if not self._var_exists(node.flow, name):
            return

        self.flow_variables[node.flow][name]['subscriptions'].append((node, callback))

    def unsubscribe(self, node, name: str, callback):
        """
        Unsubscribe from a variable.
        """
        if not self._var_exists(node.flow, name):
            return

        self.flow_variables[node.flow][name]['subscriptions'].remove((node, callback))

    def _extend_node_data(self, node, data: dict):
        """
        Extends the node data with the variable subscriptions.
        """

        data['Variables'] = {
            'subscriptions': {
                name: cb.__name__
                for name, var in self.flow_variables[node.flow].items()
                for (n, cb) in var['subscriptions']
                if node == n
            }
        }

        if data['Variables']['subscriptions'] == {}:
            del data['Variables']

    def _on_node_created(self, flow, node):
        """
        Reconstruction of subscriptions.
        """
        if node.init_data and 'Variables' in node.init_data:
            for name, cb_name in node.init_data['Variables']['subscriptions'].items():
                self.subscribe(node, name, getattr(node, cb_name))

    def get_state(self) -> dict:
        return {
            f.GLOBAL_ID: {
                name: {
                    'serialized': var['var'].serialize()
                }
                for name, var in self.flow_variables[f].items()
            }
            for f in self.flow_variables.keys()
        }

    def set_state(self, state: dict):

        for pref_flow_id, variables in state.items():
            f = Base.obj_from_prev_id(pref_flow_id)

            # recreate variables
            for name, var in variables.items():
                if self._var_exists(f, name):
                    self.var(f, name).set(deserialize(var['serialized']))
                else:
                    self.create_var(f, name, data=var)


# addon = VarsAddon()
