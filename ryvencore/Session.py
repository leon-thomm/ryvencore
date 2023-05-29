import importlib
import glob
import os.path
from typing import List, Dict, Type, Optional

from .Data import Data
from .Base import Base, Event
from .Flow import Flow
from .InfoMsgs import InfoMsgs
from .utils import pkg_version, pkg_path, load_from_file, print_err
from .Node import Node


class Session(Base):
    """
    The Session is the top level interface to your project. It mainly manages flows, nodes, and add-ons and
    provides methods for serialization and deserialization of the project.
    """

    version = pkg_version()

    def __init__(
            self,
            gui: bool = False,
            load_addons: bool = False,
    ):
        Base.__init__(self)

        # events
        self.flow_created = Event(Flow)
        self.flow_renamed = Event(Flow, str)
        self.flow_deleted = Event(Flow)

        # ATTRIBUTES
        self.addons = {}
        self.flows: [Flow] = []
        self.nodes = set()      # list of node CLASSES
        self.invisible_nodes = set()
        self.data_types = {}
        self.gui: bool = gui
        self.init_data = None

        # self.register_addons(pkg_path('addons/legacy/'))
        # self.register_addons(pkg_path('addons/'))
        if load_addons:
            self.register_addons()


    def register_addons(self, location: Optional[str] = None):
        """
        Loads all addons from the given location, or from ryvencore's
        *addons* directory if :code:`location` is :code:`None`.
        :code:`location` can be an absolute path to any readable directory.
        New addons can be registered at any time.
        Addons cannot be de-registered.
        See :code:`ryvencore.AddOn`.
        """

        if location is None:
            location = pkg_path('addons/')

        # discover all top-level modules in the given location
        addons = filter(lambda p: not p.endswith('__init__.py'), glob.glob(location + '/*.py'))

        for path in addons:
            # extract 'addon' object from module
            addon, = load_from_file(path, ['addon'])

            if addon is None:
                continue

            # register addon
            modname = os.path.split(path)[-1][:-3]
            self.addons[modname] = addon

            addon.register(self)
            # setattr(Node, addon.name, addon)

            # establish event connections
            self.flow_created.sub(addon.on_flow_created, nice=-5)
            self.flow_deleted.sub(addon.on_flow_destroyed, nice=-5)
            for f in self.flows:
                addon.connect_flow_events(f)


    def register_node_types(self, node_types: List[Type[Node]]):
        """
        Registers a list of Nodes which then become available in the flows.
        Do not attempt to place nodes in flows that haven't been registered in the session before.
        """

        for n in node_types:
            self.register_node_type(n)


    def register_node_type(self, node_class: Type[Node]):
        """
        Registers a single node.
        """

        node_class._build_identifier()
        self.nodes.add(node_class)


    def unregister_node(self, node_class: Type[Node]):
        """
        Unregisters a node which will then be removed from the available list.
        Existing instances won't be affected.
        """

        self.nodes.remove(node_class)


    def all_node_objects(self) -> List[Node]:
        """
        Returns a list of all node objects instantiated in any flow.
        """

        return [n for f in self.flows for n in f.nodes]


    def register_data_type(self, data_type_class: Type[Data]):
        """
        Registers a new :code:`Data` subclass which will then be available
        in the flows.
        """

        data_type_class._build_identifier()
        id = data_type_class.identifier
        if id == 'Data' or id in self.data_types:
            print_err(
                f'Data type identifier "{id}" is already registered. '
                f'skipping. You can use the "identifier" attribute of '
                f'your Data subclass.')
            return

        self.data_types[id] = data_type_class


    def register_data_types(self, data_type_classes: List[Type[Data]]):
        """
        Registers a list of :code:`Data` subclasses which will then be available
        in the flows.
        """

        for d in data_type_classes:
            self.register_data_type(d)


    def create_flow(self, title: str = None, data: Dict = None) -> Flow:
        """
        Creates and returns a new flow.
        If data is provided the title parameter will be ignored.
        """

        flow = Flow(session=self, title=title)
        self.flows.append(flow)

        self.flow_created.emit(flow)

        if data:
            flow.load(data)

        return flow


    def rename_flow(self, flow: Flow, title: str) -> bool:
        """
        Renames an existing flow and returns success boolean.
        """

        success = False

        if self.flow_title_valid(title):
            flow.title = title
            success = True

        self.flow_renamed.emit(flow, title)

        return success


    def flow_title_valid(self, title: str) -> bool:
        """
        Checks whether a considered title for a new flow is valid (unique) or not.
        """

        if len(title) == 0:
            return False
        for s in self.flows:
            if s.title == title:
                return False

        return True


    def delete_flow(self, flow: Flow):
        """
        Deletes an existing flow.
        """

        self.flows.remove(flow)

        self.flow_deleted.emit(flow)


    def _info_messenger(self):
        """
        Returns a reference to InfoMsgs to print info data.
        """

        return InfoMsgs


    def load(self, data: Dict) -> List[Flow]:
        """
        Loads a project and raises an exception if required nodes are missing
        (not registered).
        """

        super().load(data)

        self.init_data = data

        # load addons
        for name, addon_data in data['addons'].items():
            if name in self.addons:
                self.addons[name].load(addon_data)
            else:
                print(f'found missing addon: {name}; attempting to load anyway')

        # load flows
        new_flows = []

        #   backward compatibility
        if 'scripts' in data:
            flows_data = {
                title: script_data['flow']
                for title, script_data in data['scripts'].items()
            }
        elif isinstance(data['flows'], list):
            flows_data = {
                f'Flow {i}': flow_data
                for i, flow_data in enumerate(data['flows'])
            }
        else:
            flows_data = data['flows']

        for title, data in flows_data.items():
            new_flows.append(self.create_flow(title=title, data=data))

        return new_flows

    def serialize(self) -> Dict:
        """
        Returns the project as JSON compatible dict to be saved and
        loaded again using load()
        """

        return self.complete_data(self.data())


    def data(self) -> dict:
        """
        Serializes the project's abstract state into a JSON compatible
        dict. Pass to :code:`load()` in a new session to restore.
        Don't use this function for saving, use :code:`serialize()` in
        order to include the effects of :code:`Base.complete_data()`.
        """

        return {
            **super().data(),
            'flows': {
                f.title: f.data()
                for f in self.flows
            },
            'addons': {
                name: addon.data() for name, addon in self.addons.items()
            }
        }
