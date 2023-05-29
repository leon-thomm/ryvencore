from typing import Optional, Union
from packaging.version import parse as parse_version

from ryvencore import Node, Data, AddOn, Flow
from ryvencore.Base import Base, Event
from ryvencore.utils import print_err


ADDON_VERSION = '0.4'
# TODO: replace print_err with InfoMsgs


class Variable:
    """
    Implementation of flow variables.
    A Variable can currently only hold pickle serializable data.
    Storing other data will break save&load.
    """

    def __init__(self, addon, flow, name='', val=None, data=None):
        self.addon = addon
        self.flow = flow
        self.name = name
        self.data: Data = Data(value=val, load_from=data)

    def get(self):
        """
        Returns the value of the variable
        """
        return self.data.payload

    def set(self, val, silent=False):
        """
        Sets the value of the variable
        """
        self.data = Data(val)
        if not silent:
            self.addon.update_subscribers(self.flow, self.name)

    def serialize(self):
        return self.data.data()




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
    >>> s.register_node_type(MyNode)
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
    version = ADDON_VERSION

    def __init__(self):
        AddOn.__init__(self)

        # layout:
        #   {
        #       Flow: {
        #           'variable name': {
        #               'var': Variable,
        #               'subscriptions': [(node, method)]
        #           },
        #   }
        self.flow_variables = {}

        # nodes can be removed and re-added, so we need to keep track of the broken
        # subscriptions when nodes get removed, because they might get re-added
        # in which case we need to re-establish their subscriptions
        # layout:
        #   {
        #       Node: {
        #          'variable name': 'callback name'
        #       }
        #   }
        self.removed_subscriptions = {}

        # state data of variables that need to be recreated once their flow is
        # available, see :code:`on_flow_created()`
        self.flow_vars__pending = {}

        # events
        self.var_created = Event(Flow, str, Variable)
        self.var_deleted = Event(Flow, str)

    """
    flow management
    """

    def on_flow_created(self, flow):
        self.flow_variables[flow] = {}

    def on_flow_deleted(self, flow):
        del self.flow_variables[flow]

    """
    subscription management
    """

    def on_node_created(self, node):
        flow = node.flow

        # is invoked *before* the node is added to the flow

        # unfortunately, I cannot do this in on_flow_created because there
        # the flow doesn't have it's prev_global_id yet, but here it does
        if flow.prev_global_id in self.flow_vars__pending:
            for name, data in self.flow_vars__pending[flow.prev_global_id].items():
                self.create_var(flow, name, load_from=data)
            del self.flow_vars__pending[flow.prev_global_id]

    def on_node_added(self, node):
        """
        Reconstruction of subscriptions.
        """

        # if node had subscriptions previously (so it was removed)
        if node in self.removed_subscriptions:
            for name, cb in self.removed_subscriptions[node].items():
                self.subscribe(node, name, cb)
            del self.removed_subscriptions[node]

        # otherwise, check if it has load data and reconstruct subscriptions
        elif node.load_data and 'Variables' in node.load_data:
            for name, cb_name in node.load_data['Variables']['subscriptions'].items():
                self.subscribe(node, name, getattr(node, cb_name))

    def on_node_removed(self, node):
        """
        Remove all subscriptions of the node.
        """

        # store subscription in removed_subscriptions
        # because the node might get re-added later
        self.removed_subscriptions[node] = {}

        for name, varname in self.flow_variables[node.flow].items():
            for (n, cb) in varname['subscriptions']:
                if n == node:
                    self.removed_subscriptions[node][name] = cb.__name__
                    self.unsubscribe(node, name, cb)

    """
    variables api
    """

    def var_name_valid(self, flow, name: str) -> bool:
        """
        Checks if :code:`name` is a valid variable identifier and hasn't been take yet.
        """

        return name.isidentifier() and not self.var_exists(flow, name)

    def create_var(self, flow: Flow, name: str, val=None, load_from=None) -> Optional[Variable]:
        """
        Creates and returns a new variable and None if the name isn't valid.
        """

        if self.var_name_valid(flow, name):
            v = Variable(self, flow, name, val, load_from)
            self.flow_variables[flow][name] = {
                'var': v,
                'subscriptions': []
            }
            self.var_created.emit(flow, name, v)
            return v

    def delete_var(self, flow, name: str):
        """
        Deletes a variable and causes subscription update. Subscriptions are preserved.
        """
        if not self.var_exists(flow, name):
            # print_err(f'Variable {name} does not exist.')
            return

        del self.flow_variables[flow][name]
        self.var_deleted.emit(flow, name)

    def var_exists(self, flow, name: str) -> bool:
        return flow in self.flow_variables and name in self.flow_variables[flow]

    def var(self, flow, name: str) -> Optional[Variable]:
        """
        Returns the variable with the given name or None if it doesn't exist.
        """
        if not self.var_exists(flow, name):
            # print_err(f'Variable {name} does not exist.')
            return None

        return self.flow_variables[flow][name]['var']

    def update_subscribers(self, flow, name: str):
        """
        Called when a Variable object changes or when the var is created or deleted.
        """

        v = self.flow_variables[flow][name]['var']

        for (node, cb) in self.flow_variables[flow][name]['subscriptions']:
            cb(v)

    def subscribe(self, node: Node, name: str, callback):
        """
        Subscribe to a variable. ``callback`` must be a method of the node.
        """
        if not self.var_exists(node.flow, name):
            # print_err(f'Variable {name} does not exist.')
            return

        self.flow_variables[node.flow][name]['subscriptions'].append((node, callback))

    def unsubscribe(self, node, name: str, callback):
        """
        Unsubscribe from a variable.
        """
        if not self.var_exists(node.flow, name):
            # print_err(f'Variable {name} does not exist.')
            return

        self.flow_variables[node.flow][name]['subscriptions'].remove((node, callback))

    """
    serialization
    """

    def extend_node_data(self, node, data: dict):
        """
        Extends the node data with the variable subscriptions.
        """

        if self.flow_variables.get(node.flow) == {}:
            return

        data['Variables'] = {
            'subscriptions': {
                name: cb.__name__
                for name, var in self.flow_variables[node.flow].items()
                for (n, cb) in var['subscriptions']
                if node == n
            }
        }

    def get_state(self) -> dict:
        """"""
        
        return {
            f.global_id: {
                name: var['var'].serialize()
                for name, var in self.flow_variables[f].items()
            }
            for f in self.flow_variables.keys()
        }

    def set_state(self, state: dict, version: str):
        """"""

        if parse_version(version) < parse_version('0.4'):
            print_err('Variables addon state version too old, skipping')
            return

        # JSON converts int keys to strings, so we need to convert them back
        state = {
            int(flow_id): flow_vars
            for flow_id, flow_vars in state.items()
        }

        self.flow_vars__pending = state


addon = VarsAddon()
