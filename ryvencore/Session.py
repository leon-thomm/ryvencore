from .Base import Base, Event


from .Script import Script
from .InfoMsgs import InfoMsgs

from typing import List, Dict


class Session(Base):
    """
    The Session is the top level interface to your project. It mainly manages Scripts and registered nodes, and
    provides methods for serialization and deserialization of the project.
    """

    def __init__(
            self,
            gui: bool = False,
    ):
        Base.__init__(self)

        # events
        self.new_script_created = Event(Script)
        self.script_renamed = Event(Script)
        self.script_deleted = Event(Script)

        # ATTRIBUTES
        self.scripts: [Script] = []
        self.nodes = []  # list of node CLASSES
        self.invisible_nodes = []
        self.gui: bool = gui
        self.init_data = None


    def register_nodes(self, node_classes: List):
        """Registers a list of Nodes which then become available in the flows"""

        for n in node_classes:
            self.register_node(n)


    def register_node(self, node_class):
        """Registers a single Node which then becomes available in the flows"""

        # build node class identifier
        node_class.build_identifier()

        self.nodes.append(node_class)


    def unregister_node(self, node_class):
        """Unregisters a Node which will then be removed from the available list.
        Existing instances won't be affected."""

        self.nodes.remove(node_class)


    def all_node_objects(self) -> List:
        """Returns a list of all Node objects instantiated in any flow"""

        nodes = []
        for s in self.scripts:
            for n in s.flow.nodes:
                nodes.append(n)
        return nodes


    def create_script(self, title: str = None, create_default_logs=True,
                      data: Dict = None) -> Script:
        """Creates and returns a new script.
        If data is provided the title parameter will be ignored."""

        script = Script(
            session=self, title=title, create_default_logs=create_default_logs,
            load_data=data
        )

        self.scripts.append(script)
        script.load_flow()

        self.new_script_created.emit(script)

        return script


    def rename_script(self, script: Script, title: str) -> bool:
        """Renames an existing script and returns success boolean"""

        success = False

        if self.script_title_valid(title):
            script.title = title
            success = True

        self.script_renamed.emit(script)

        return success


    def script_title_valid(self, title: str) -> bool:
        """Checks whether a considered title for a new script is valid (unique) or not"""

        if len(title) == 0:
            return False
        for s in self.scripts:
            if s.title == title:
                return False

        return True


    def delete_script(self, script: Script):
        """Removes an existing script."""

        self.scripts.remove(script)

        self.script_deleted.emit(script)


    def info_messenger(self):
        """Returns a reference to InfoMsgs to print info data"""

        return InfoMsgs


    def load(self, project: Dict) -> List[Script]:
        """Loads a project and raises an exception if required nodes are missing"""

        # TODO: perform validity checks

        self.init_data = project

        new_scripts = []
        for sc in project['scripts']:
            new_scripts.append(self.create_script(data=sc))

        return new_scripts

    def serialize(self):
        """Returns the project as JSON compatible dict to be saved and loaded again using load()"""

        return self.complete_data(self.data())


    def data(self) -> dict:
        return {
            'scripts': [
                s.data() for s in self.scripts
            ],
        }
