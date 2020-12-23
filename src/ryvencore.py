from .Node import Node, NodePort
from .NodeInstance import NodeInstance
from .Session import Session
from .WidgetBaseClasses import MWB, IWB
from .global_tools.Debugger import Debugger
from .CONSTANTS import FlowAlg, MainWidgetPos, InpWidgetPos


# CONVENIENCE CLASSES

class ConvUI:
    from .custom_list_widgets.ScriptsListWidget import ScriptsListWidget
    from .custom_list_widgets.VariablesListWidget import VariablesListWidget
    from .logging.LogWidget import LogWidget

    ScriptsList = ScriptsListWidget
    VarsList = VariablesListWidget
    LogWidget = LogWidget


class Retain:
    from .retain import M
    M = M


# set package path
import os
from .GlobalAttributes import Location
Location.PACKAGE_PATH = os.path.normpath(os.path.dirname(__file__)+'/../')
print(Location.PACKAGE_PATH)
