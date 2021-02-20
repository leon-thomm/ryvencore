# set package path
import os
from .src.GlobalAttributes import Location
Location.PACKAGE_PATH = os.path.normpath(os.path.dirname(__file__))


from .src.Node import Node
from .src.NodePort import NodeInput, NodeOutput
from .src.Session import Session
from .src.WidgetBaseClasses import MWB, IWB
from .src.InfoMsgs import InfoMsgs
from .src.Connection import DataConnection, ExecConnection


# CONVENIENCE CLASSES


class GUI:
    from .src.custom_list_widgets.ScriptsListWidget import ScriptsListWidget as ScriptsList
    from .src.custom_list_widgets.VariablesListWidget import VariablesListWidget as VarsList

    from .src.logging.LogWidget import LogWidget

    from .src.PortItemInputWidgets import RCIW_BUILTIN_LineEdit
    from .src.PortItemInputWidgets import RCIW_BUILTIN_LineEdit_small
    from .src.PortItemInputWidgets import RCIW_BUILTIN_SpinBox


class Retain:
    from .src.retain import M
