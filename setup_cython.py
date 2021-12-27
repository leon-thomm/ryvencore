"""
This setup file can be used to manually compile ryvencore to a C extension using Cython, behavior should be the same.

HOW TO COMPILE

Run all commands from the top level 'ryvencore' directory, and remember to remove any old ryvencore version initially
$ pip uninstall ryvencore
The below instructions show how to compile the sources on your system. Note that you will need Cython and an according
C compiler for this.

$ python -m setup_cython build_ext --inplace
$ python setup_cython.py sdist bdist_wheel
$ pip install ./dist/ryvencore-<version>-<platform>.whl

NOTE
-   if you don't want to keep the source files (.py and compiled .c) in the installed package (only the compiled .so
    files), simply comment out the line `packages = find:` in setup.cfg

To verify that the package successfully runs from the compiled C extension modules you can check whether
the imported ryvencore package shows the __init__.so file and not __init__.py
> import ryvencore as rc
> print(rc)
and to really be sure you can also manually remove all .py files in the installation directory
(on linux: $ .../site-packages/ryvencore>find . -name "*.py" -type f -delete)
and check whether you can successfully load the package from Python.
"""


from setuptools import setup
from Cython.Build import cythonize
import os


def get_ext_paths(root_dir, exclude_files=[], recursive=True):
    """get filepaths for compilation"""
    paths = []

    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            if os.path.splitext(filename)[1] != '.py':
                continue

            file_path = os.path.join(root, filename)
            if file_path in exclude_files:
                continue

            paths.append(file_path)

        if recursive:
            for d in dirs:
                paths += get_ext_paths(d, exclude_files)
    return paths


setup(
    ext_modules=cythonize(
        get_ext_paths('ryvencore'),
        compiler_directives={'language_level': 3}
    )
)
