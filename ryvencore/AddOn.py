"""
*ALPHA*

This module defines a simple add-on system to extend ryvencore's functionalities.
Some default add-ons are provided in the addons.default package, and additional add-ons
can be added and registered in the Session.

An add-on
    - has a name and a version
    - is session-local, not flow-local (but you can of course implement per-flow functionality)
    - manages its own state (in particular ``get_state()`` and ``set_state()``)
    - can store additional node-specific data in the node's ``data`` dict when it's serialized
    - will be accessible through the nodes API: ``self.get_addon('your_addon')`` in your nodes

Add-on access is blocked during loading (deserialization), so nodes should not access any
add-ons during the execution of ``Node.__init__`` or ``Node.set_data``.
This prevents inconsistent states. Nodes are loaded first, then the add-ons. 
Therefore, the add-on should be sufficiently isolated and self-contained.

To define a custom add-on:
    - create a directory ``your_addons`` for you addons or use ryvencore's addon directory
    - create a module for your addon ``YourAddon.py`` in ``your_addons``
    - create a class ``YourAddon(ryvencore.AddOn)`` that defines your add-on's functionality
    - instantiate it into a top-level variable: ``addon = YourAddon()`` at the end of the module
    - register your addon directory in the Session: ``session.register_addon_dir('path/to/your_addons')``

See ``ryvencore.addons.default`` for examples.
"""

from ryvencore.Base import Base


class AddOn(Base):
    name = ''
    version = ''

    def register(self, session):
        """
        Called when the add-on is registered with a session.
        """
        self.session = session

    def _on_node_created(self, flow, node):
        """
        *VIRTUAL*

        Called when a node is created. This happens only once, whereas
        a node can be added and removed multiple times, see
        on_node_added() and
        on_node_removed().
        """
        pass

    def _on_node_added(self, flow, node):
        """
        *VIRTUAL*

        Called when a node is added to a flow.
        """
        pass

    def _on_node_removed(self, flow, node):
        """
        *VIRTUAL*

        Called when a node is removed from a flow.
        """
        pass

    def _extend_node_data(self, node, data: dict):
        """
        *VIRTUAL*

        Extend the node data dict with additional add-on-related data.
        """
        pass

    def get_state(self) -> dict:
        """
        *VIRTUAL*

        Return the state of the add-on as JSON-compatible a dict.
        This dict will be extended by :code:`AddOn.complete_data()`.
        """
        return {}

    def set_state(self, state: dict, version: str):
        """
        *VIRTUAL*

        Set the state of the add-on from the dict generated in
        :code:`AddOn.get_state()`.
        """
        pass

    def data(self) -> dict:
        """
        Supplements the data dict with additional data.
        """
        return {
            **super().data(),
            'custom state': self.get_state()
        }

    def load(self, data: dict):
        """
        Loads the data dict generated in :code:`AddOn.data()`.
        """
        self.set_state(data['custom state'], data['version'])
