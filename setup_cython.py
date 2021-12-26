"""
This setup file can be used to manually compile ryvencore to a C extension using Cython, behavior should be the same.
To compile ryvencore from sources on your system, from the top level 'ryvencore' directory run:
$ python -m setup_cython sdist
$ pip install ./dist/ryvencore-<version>.tar.gz

remember to remove any old ryvencore version before
$ pip uninstall ryvencore

this will compile the sources on your system. note that you will need Cython and an according C compiler.
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
