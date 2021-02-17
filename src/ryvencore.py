from .Node import Node
from .NodePort import NodeInput, NodeOutput
from .Session import Session
from .WidgetBaseClasses import MWB, IWB
from .InfoMsgs import InfoMsgs
from .Connection import DataConnection, ExecConnection


# CONVENIENCE CLASSES

class GUI:
    class Lists:
        from .custom_list_widgets.ScriptsListWidget import ScriptsListWidget as ScriptsList
        from .custom_list_widgets.VariablesListWidget import VariablesListWidget as VarsList

    class Logging:
        from .logging.LogWidget import LogWidget

    class InputWidgets:
        from .PortItemInputWidgets import RCIW_BUILTIN_LineEdit
        from .PortItemInputWidgets import RCIW_BUILTIN_LineEdit_small
        from .PortItemInputWidgets import RCIW_BUILTIN_SpinBox




class Retain:
    from .retain import M
    M = M


# set package path
import os
from .GlobalAttributes import Location
Location.PACKAGE_PATH = os.path.normpath(os.path.dirname(__file__)+'/../')
