"""A collection of useful functions used by different components."""

import base64
import json
import pickle
import sys
from os.path import dirname, abspath, join, basename
from typing import List, Tuple, Dict
from packaging.version import Version, parse as _parse_version
import importlib.util

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

def pkg_version() -> str:
    return importlib_metadata.version('ryvencore')


def pkg_path(subpath: str = None):
    """
    Returns the path to the installed package root directory, optionally with a relative sub-path appended.
    Notice that this returns the path to the ryvencore package (ryvencore/ryvencore/) not the repository (ryvencore/).
    """

    p = dirname(__file__)
    if subpath is not None:
        p = join(p, subpath)
    return abspath(p)


def serialize(data) -> str:
    return base64.b64encode(pickle.dumps(data)).decode('ascii')


def deserialize(data):
    return pickle.loads(base64.b64decode(data))


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def json_print(d: Dict):
    # I just need this all the time
    print(json.dumps(d, indent=4))


def load_from_file(file: str, comps: List[str]) -> Tuple:
    """
    Imports components with name in ``comps`` from a python module.
    """
    # https://stackoverflow.com/questions/67631/how-do-i-import-a-module-given-the-full-path

    name = basename(file).split('.')[0]
    spec = importlib.util.spec_from_file_location(name, file)
    importlib.util.module_from_spec(spec)

    # TODO
    #  I'm using the deprecated load_module() instead of
    #  exec_module() because I had issues with exec_module().
    #  exec_module() somehow registers it as "built-in" which
    #  is wrong and prevents features, such as inspecting
    #  the source with inspect
    mod = spec.loader.load_module(name)

    def get_comp(c):
        try:
            return getattr(mod, c)
        except AttributeError:
            return None

    return tuple([get_comp(c) for c in comps])



    