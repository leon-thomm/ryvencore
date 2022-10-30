"""A collection of useful functions used by different components."""

import base64
import importlib.util
import pickle
from os.path import dirname, abspath, join, basename
from typing import List, Tuple


def serialize(data) -> str:
    return base64.b64encode(pickle.dumps(data)).decode('ascii')


def deserialize(data):
    return pickle.loads(base64.b64decode(data))


def node_from_identifier(identifier: str, nodes: List):

    for nc in nodes:
        if nc.identifier == identifier:
            return nc
    else:  # couldn't find a node with this identifier => search for identifier_comp
        for nc in nodes:
            if identifier in nc.legacy_identifiers:
                return nc
        else:
            raise Exception(
                f'could not find node class with identifier \'{identifier}\'. '
                f'if you changed your node\'s class name, make sure to add the old '
                f'identifier to the identifier_comp list attribute to provide '
                f'backwards compatibility.'
            )

def pkg_path(subpath: str = None):
    """
    Returns the path to the installed package root directory, optionally with a relative sub-path appended.
    Notice that this returns the path to the ryvencore package (ryvencore/ryvencore/) not the repository (ryvencore/).
    """

    p = dirname(__file__)
    if subpath is not None:
        p = join(p, subpath)
    return abspath(p)


def load_from_file(file: str, comps: List[str]) -> Tuple:
    """
    Imports components with name in ``comps`` from a python module.
    """
    # https://stackoverflow.com/questions/67631/how-do-i-import-a-module-given-the-full-path

    name = basename(file).split('.')[0]
    spec = importlib.util.spec_from_file_location(name, file)
    importlib.util.module_from_spec(spec)
    mod = spec.loader.load_module(name)
    # using load_module(name) instead of exec_module(mod) here,
    # because exec_module() somehow then registers it as "built-in"
    # which is wrong and e.g. prevents inspect from parsing the source

    def get_comp(c):
        try:
            return getattr(mod, c)
        except AttributeError:
            return None

    return tuple([get_comp(c) for c in comps])
