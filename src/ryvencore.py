from .Node import Node, NodePort
from .NodeInstance import NodeInstance
from .Session import Session
from .WidgetBaseClasses import MWB, IWB
from .global_tools.Debugger import Debugger
from .Connection import DataConnBase, ExecConnBase


# CONVENIENCE CLASSES

class GUI:
    class Lists:
        from .custom_list_widgets.ScriptsListWidget import ScriptsListWidget as ScriptsList
        from .custom_list_widgets.VariablesListWidget import VariablesListWidget as VarsList

    class Logging:
        from .logging.LogWidget import LogWidget

    class InputWidgets:
        # class LineEdits:
        #     class Std:
        #         class Static:
        #             from .PortInstance import LineEdit_PortInstWidget_Std_S as Small
        #             from .PortInstance import LineEdit_PortInstWidget_Std_M as Medium
        #             from .PortInstance import LineEdit_PortInstWidget_Std_L as Large
        #
        #         class Resizing:
        #             from .PortInstance import LineEdit_PortInstWidget_Std_Resizing_S as Small
        #             from .PortInstance import LineEdit_PortInstWidget_Std_Resizing_M as Medium
        #             from .PortInstance import LineEdit_PortInstWidget_Std_Resizing_L as Large
        #
        #     class NoBorder:
        #
        #         # no Static for now...
        #         class Resizing:
        #             from .PortInstance import LineEdit_PortInstWidget_NoBorder_Resizing_S as Small
        #             from .PortInstance import LineEdit_PortInstWidget_NoBorder_Resizing_M as Medium
        #             from .PortInstance import LineEdit_PortInstWidget_NoBorder_Resizing_L as Large

        from .PortInstanceInputWidgets import StdLineEditInputWidget as StdLineEdit
        from .PortInstanceInputWidgets import StdLineEditInputWidget_NoBorder as StdLineEdit_NoBorder
        from .PortInstanceInputWidgets import StdSpinBoxInputWidget as StdSpinBox

    # ScriptsList = ScriptsListWidget
    # VarsList = VariablesListWidget
    # LogWidget = LogWidget



class Retain:
    from .retain import M
    M = M


# set package path
import os
from .GlobalAttributes import Location
Location.PACKAGE_PATH = os.path.normpath(os.path.dirname(__file__)+'/../')
print(Location.PACKAGE_PATH)
