"""
This setup file can be used to manually compile ryvencore to a C extension using Cython, behavior should be the same.
To compile ryvencore from sources on your system, from the top level 'ryvencore' directory run:

$ python -m setup_cython build_ext --inplace
$ python setup_cython.py sdist bdist_wheel
$ pip install ./dist/ryvencore-<version>-<platform>.whl

remember to remove any old ryvencore version before
$ pip uninstall ryvencore

This will compile the sources on your system. note that you will need Cython and an according C compiler.

To verify that the package successfully runs from the compiled c extension modules you can check whether
the imported ryvencore package shows the __init__.so file and not __init__.py, and you can manually remove
all .py files in the installation directory
(on linux: `.../site-packages/ryvencore>find . -name "*.py" -type f -delete`)
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
        get_ext_paths('ryvencore')
    )
)
