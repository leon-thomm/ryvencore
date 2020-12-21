import src.GlobalAttributes
import os

GlobalAttributes.package_path = os.path.normpath(os.path.dirname(os.path.abspath(__file__))+'/../')
