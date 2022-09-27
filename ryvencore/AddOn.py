"""
This module defines a simple add-on system to extend ryvencore's functionalities.
Some default add-ons are provided in the add-ons.default package, and additional add-ons
can be added and registered in the Session.

An add-on

- has a name, a version, a description
- is session-local, not flow-local (but you can of course implement per-flow functionality)  
- manages its own state (in particular ``get_state()`` and ``set_state()``)
- will be accessible by nodes as attribute (self.add-on_name in the node)

Add-on access is blocked during loading, so nodes should not access any add-ons in set_data(). 
This prevents inconsistent states. Nodes are loaded first, then the add-ons. 
Therefore, the add-on should be sufficiently isolated and self-contained.

To define a custom add-on you need to subclass the ``AddOn`` class in its own module,
instantiate it into a top module level variable ``addon`` (``addon = YourAddon()``),
and put the module into an add-on directory. See ``Session.register_addon`` and
see ``ryvencore.addons.default`` for examples.
"""

from ryvencore.Base import Base


class AddOn(Base):
    name = ''
    version = ''
    description = ''

    def register(self, session):
        """
        Called when the add-on is registered with a session.
        """
        self.session = session

    def _on_node_created(self, flow, node):
        """
        Called when a node is created. This happens only once, whereas
        a node can be added and removed multiple times, see
        on_node_added() and
        on_node_removed().
        """
        pass

    def _on_node_added(self, flow, node):
        """
        Called when a node is added to a flow.
        """
        pass

    def _on_node_removed(self, flow, node):
        """
        Called when a node is removed from a flow.
        """
        pass

    def _extend_node_data(self, node, data: dict):
        """
        Extend the node data dict with additional add-on-related data.
        """
        pass

    # def _extend_flow_data(self, flow, data: dict):
    #     """
    #     Extend the flow data dict with additional add-on-related data.
    #     """
    #     pass
    #
    # def _extend_session_data(self, data: dict):
    #     """
    #     Extend the session data dict with additional add-on-related data.
    #     """
    #     pass

    def get_state(self) -> dict:
        """
        Return the state of the add-on as JSON-compatible a dict.
        """
        return {}

    def set_state(self, state: dict):
        """
        Set the state of the add-on from the dict generated in get_state().
        """
        pass
