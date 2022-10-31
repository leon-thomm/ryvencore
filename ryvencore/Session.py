import importlib
import glob
import os.path
from typing import List, Dict

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
    ):
        Base.__init__(self)

        # events
        self.new_flow_created = Event(Flow)
        self.flow_renamed = Event(Flow)
        self.flow_deleted = Event(Flow)

        # ATTRIBUTES
        self.addons = {}
        self.flows: [Flow] = []
        self.nodes = set()      # list of node CLASSES
        self.invisible_nodes = set()
        self.data_types = {}
        self.gui: bool = gui
        self.init_data = None

        self.load_addons(pkg_path('addons/default/'))
        self.load_addons(pkg_path('addons/'))


    def load_addons(self, location: str):
        """
        Loads all addons from the given location. ``location`` can be an absolute path to any readable directory.
        See ``ryvencore.AddOn``.
        """

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
            setattr(Node, addon.name, addon)


    def register_nodes(self, node_classes: List):
        """
        Registers a list of Nodes which then become available in the flows.
        Do not attempt to place nodes in flows that haven't been registered in the session before.
        """

        for n in node_classes:
            self.register_node(n)


    def register_node(self, node_class):
        """
        Registers a single node.
        """

        # build node class identifier
        node_class._build_identifier()

        self.nodes.add(node_class)


    def unregister_node(self, node_class):
        """
        Unregisters a node which will then be removed from the available list.
        Existing instances won't be affected.
        """

        self.nodes.remove(node_class)


    def all_node_objects(self) -> List:
        """
        Returns a list of all node objects instantiated in any flow.
        """

        nodes = []
        for s in self.flows:
            for n in s.flow.nodes:
                nodes.append(n)
        return nodes


    def register_data(self, data_type_class):
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


    def create_flow(self, title: str = None, data: Dict = None) -> Flow:
        """
        Creates and returns a new flow.
        If data is provided the title parameter will be ignored.
        """

        flow = Flow(session=self, title=title)
        self.flows.append(flow)

        if data:
            flow.load(data)

        self.new_flow_created.emit(flow)

        return flow


    def rename_flow(self, flow: Flow, title: str) -> bool:
        """
        Renames an existing flow and returns success boolean.
        """

        success = False

        if self.flow_title_valid(title):
            flow.title = title
            success = True

        self.flow_renamed.emit(flow)

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

        # load flows
        new_flows = []

        #   backward compatibility
        if 'scripts' in data:
            flows_data = {
                title: script_data['flow']
                for title, script_data in data['scripts'].items()
            }
        else:
            flows_data = data['flows']

        for fd in flows_data:
            new_flows.append(self.create_flow(data=fd))

        # load addons
        for name, addon_data in data['addons'].items():
            if name in self.addons:
                self.addons[name].load(addon_data)
            else:
                print(f'found missing addon: {name}; attempting to load anyway')

        return new_flows

    def serialize(self):
        """
        Returns the project as JSON compatible dict to be saved and
        loaded again using load()
        """

        return self.complete_data(self.data())


    def data(self) -> dict:
        """
        Serializes the whole project into a JSON compatible dict.
        Pass to :code:`load()` in a new session to restore.
        """

        return {
            **super().data(),
            'flows': [
                s.data() for s in self.flows
            ],
            'addons': {
                name: addon.data() for name, addon in self.addons.items()
            }
        }
