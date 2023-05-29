"""
*ALPHA*

This module defines a simple add-on system to extend ryvencore's functionalities.
Some add-ons are provided in the addons package, and additional add-ons
can be added and registered in the Session.

An add-on
    - has a name and a version
    - is session-local, not flow-local (but you can of course implement per-flow functionality)
    - manages its own state (in particular :code:`get_state()` and :code:`set_state()`)
    - can store additional node-specific data in the node's :code:`data` dict when it's serialized
    - will be accessible through the nodes API: :code:`self.get_addon('your_addon')` in your nodes

TODO: The below statement is not true, I think. Add-ons are loaded first, and nodes can access
 them during their initialization (but it may be a bad idea).

Add-on access is blocked during loading (deserialization), so nodes should not access any
add-ons during the execution of :code:`Node.__init__` or :code:`Node.set_data`.
This prevents inconsistent states. Nodes are loaded first, then the add-ons. 
Therefore, the add-on should be sufficiently isolated and self-contained.

To define a custom add-on:
    - create a directory :code:`your_addons` for you addons or use ryvencore's addon directory
    - create a module for your addon :code:`YourAddon.py` in :code:`your_addons`
    - create a class :code:`YourAddon(ryvencore.AddOn)` that defines your add-on's functionality
    - instantiate it into a top-level variable: :code:`addon = YourAddon()` at the end of the module
    - register your addon directory in the Session: :code:`session.register_addon_dir('path/to/your_addons')`

See :code:`ryvencore.addons` for examples.
"""
from typing import Dict

from .Session import Session
from .Flow import Flow
from .Node import Node
from .Base import Base


class AddOn(Base):
    name = ''
    version = ''

    def register(self, session: Session):
        """
        Called when the add-on is registered with a session.
        """
        self.session = session

    def connect_flow_events(self, flow: Flow):
        """
        Connects flow events to the add-on.
        """
        flow.node_created.sub(self.on_node_created, nice=-4)
        flow.node_added.sub(self.on_node_added, nice=-4)
        flow.node_removed.sub(self.on_node_removed, nice=-4)

    def on_flow_created(self, flow: Flow):
        """
        *VIRTUAL*

        Called when a flow is created.
        """
        pass

    def on_flow_destroyed(self, flow: Flow):
        """
        *VIRTUAL*

        Called when a flow is destroyed.
        """
        pass

    def on_node_created(self, node: Node):
        """
        *VIRTUAL*

        Called when a node is created and fully initialized
        (:code:`Node.load()` has already been called, if necessary),
        but not yet added to the flow. Therefore, this is a good place
        to initialize the node with add-on-specific data.

        This happens only once per node, whereas it can be added and
        removed multiple times, see :code:`AddOn.on_node_added()` and
        :code:`AddOn.on_node_removed()`.
        """
        pass

    def on_node_added(self, node: Node):
        """
        *VIRTUAL*

        Called when a node is added to a flow.
        """
        pass

    def on_node_removed(self, node: Node):
        """
        *VIRTUAL*

        Called when a node is removed from a flow.
        """
        pass

    def extend_node_data(self, node: Node, data: Dict):
        """
        *VIRTUAL*

        Invoked whenever any node is serialized. This method can be
        used to extend the node's data dict with additional
        add-on.related data.
        """
        pass

    def get_state(self) -> Dict:
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
        :code:`AddOn.get_state()`. Notice that add-ons are loaded
        *before* the flows. If you need to re-establish any sort
        of connections between flows or nodes and your add-on,
        you should store :code:`state` and do so in the according
        slot methods (e.g. :code:`on_node_added()`).
        """
        pass

    def data(self) -> Dict:
        """
        Supplements the data dict with additional data.
        """
        return {
            **super().data(),
            'custom state': self.get_state()
        }

    def load(self, data: Dict):
        """
        Loads the data dict generated in :code:`AddOn.data()`.
        """
        self.set_state(data['custom state'], data['version'])
