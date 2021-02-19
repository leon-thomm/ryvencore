from PySide2.QtCore import QObject, Signal, QThread
from PySide2.QtGui import QFontDatabase
from PySide2.QtWidgets import QWidget

from .GlobalAttributes import Location
from .Script import Script
from .FunctionScript import FunctionScript
from .FunctionNodeTypes import FunctionInputNode, FunctionOutputNode
from .SessionThreadingBridge import SessionThreadingBridge
from .InfoMsgs import InfoMsgs
from .Design import Design


class Session(QObject):
    """The Session class represents a project and holds all project-level
    data such as nodes."""

    new_script_created = Signal(Script)
    script_renamed = Signal(Script)
    script_deleted = Signal(Script)


    def __init__(
            self,
            threaded: bool = False,
            gui_parent: QWidget = None,
            gui_thread: QThread = None,
            flow_theme_name=None,
            performance_mode=None,
            parent: QObject = None
    ):
        super().__init__(parent=parent)

        self._register_fonts()

        self.scripts: [Script] = []
        self.function_scripts: [FunctionScript] = []
        self.nodes = []  # list of node CLASSES
        self.invisible_nodes = [FunctionInputNode, FunctionOutputNode]
        self.threaded = threaded
        self.threading_bridge = None
        self.gui_parent = gui_parent
        if self.threaded:
            self.threading_bridge = SessionThreadingBridge()
            self.threading_bridge.moveToThread(gui_parent.thread())

        self.design = Design()
        if flow_theme_name:
            self.design.set_flow_theme(name=flow_theme_name)
        if performance_mode:
            self.design.set_performance_mode(performance_mode)


    def _register_fonts(self):
        QFontDatabase.addApplicationFont(Location.PACKAGE_PATH+'/resources/fonts/poppins/Poppins-Medium.ttf')
        QFontDatabase.addApplicationFont(Location.PACKAGE_PATH+'/resources/fonts/source code pro/SourceCodePro-Regular.ttf')
        QFontDatabase.addApplicationFont(Location.PACKAGE_PATH+'/resources/fonts/asap/Asap-Regular.ttf')


    def register_nodes(self, node_classes):
        """Registers a list of Nodes which you then can access in all scripts"""

        for n in node_classes:
            self.register_node(n)


    def register_node(self, node_class):
        """Registers a Node which then can be accessed in all scripts"""
        if not node_class.identifier:
            node_class.identifier = node_class.__name__
            InfoMsgs.write('assigned identifier:', node_class.identifier)

        self.nodes.append(node_class)


    def unregister_node(self, node_class):
        """Unregisters a Node which will then be removed from the available list.
        Existing instances won't be affected."""

        self.nodes.remove(node_class)


    def create_script(self, title: str, flow_view_size: list = None, create_default_logs=True) -> Script:
        """Creates and returns a new script"""

        script = Script(session=self, title=title, flow_view_size=flow_view_size, create_default_logs=create_default_logs)

        self.scripts.append(script)
        self.new_script_created.emit(script)

        return script


    def create_func_script(self, title: str, flow_view_size: list = None, create_default_logs=True) -> Script:
        """Creates and returns a new FUNCTION script"""

        func_script = FunctionScript(
            session=self, title=title, flow_view_size=flow_view_size, create_default_logs=create_default_logs
        )
        func_script.initialize()

        self.function_scripts.append(func_script)
        self.new_script_created.emit(func_script)

        return func_script


    def all_scripts(self) -> list:
        """Returns a list containing all scripts and function scripts"""
        return self.function_scripts + self.scripts


    def _load_script(self, config: dict):
        """Loads a script from a project dict"""

        script = Script(session=self, config_data=config)
        self.scripts.append(script)
        self.new_script_created.emit(script)
        return script

    def _load_func_script(self, config: dict):
        """Loads a function script from a project dict without initializing it"""

        fscript = FunctionScript(session=self, config_data=config)
        self.function_scripts.append(fscript)

        # NOTE: no script_created emit here because the fscript hasn't finished initializing yet

        return fscript


    def rename_script(self, script: Script, title: str):
        """Renames an existing script"""
        script.title = title
        self.script_renamed.emit(script)


    def check_new_script_title_validity(self, title: str) -> bool:
        if len(title) == 0:
            return False
        for s in self.all_scripts():
            if s.title == title:
                return False

        return True


    def delete_script(self, script: Script):
        """Deletes an existing script"""

        if isinstance(script, FunctionScript):
            self.unregister_node(script.function_node_class)
            self.function_scripts.remove(script)
        else:
            self.scripts.remove(script)

        self.script_deleted.emit(script)


    def info_messenger(self):
        """Returns a reference to InfoMsgs to print info data"""
        return InfoMsgs


    def load(self, project: dict) -> bool:
        """Loads a project and raises an error if required nodes are missing"""
        if 'scripts' not in project and 'function scripts' not in project:
            return False

        if 'function scripts' in project:
            new_func_scripts = []
            for fsc in project['function scripts']:
                new_func_scripts.append(self._load_func_script(config=fsc))

            # now all func nodes have been registered, so we can initialize the scripts

            for fs in new_func_scripts:
                fs.initialize()
                self.new_script_created.emit(fs)

        for sc in project['scripts']:
            self._load_script(config=sc)

        return True


    def serialize(self) -> dict:
        """Returns a list with 'config data' of all scripts for saving the project"""

        data = {}

        func_scripts_list = []
        for fscript in self.function_scripts:
            func_scripts_list.append(fscript.serialize())
        data['function scripts'] = func_scripts_list

        scripts_list = []
        for script in self.scripts:
            scripts_list.append(script.serialize())
        data['scripts'] = scripts_list

        return data


    def all_nodes(self):
        """Returns a list containing all Node objects used in any flow which is useful for advanced project analysis"""

        nodes = []
        for s in self.all_scripts():
            for n in s.flow.nodes:
                nodes.append(n)
        return nodes


    def save_as_project(self, fpath: str):
        """Convenience method for directly saving the the all content as project to a file"""
        pass


    def set_stylesheet(self, s: str):
        """Sets the session's stylesheet which can be accessed by NodeItems.
        You usually want this to be the same as your window's stylesheet."""

        self.design.global_stylesheet = s
