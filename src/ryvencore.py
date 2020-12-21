from src.Node import Node, NodePort
from src.NodeInstance import NodeInstance
from src.Session import Session
from src.WidgetBaseClasses import MWB, IWB
from src.global_tools.Debugger import Debugger


# CONVENIENCE CLASSES

class ConvUI:
    from src.custom_list_widgets.ScriptsListWidget import ScriptsListWidget
    from src.custom_list_widgets.VariablesListWidget import VariablesListWidget
    from src.logging.LogWidget import LogWidget

    ScriptsList = ScriptsListWidget
    VarsList = VariablesListWidget
    LogWidget = LogWidget


class Retain:
    from src.retain import M
    M = M
