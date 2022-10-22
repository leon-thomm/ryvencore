"""
This setup file can be used to manually compile ryvencore to a C extension using Cython, behavior should be the same.

Follow the below process to compile ryvencore with Cython and install it as a regular package.
Points 1 - 4 are only necessary if they are not satisfied already.
Run all commands from the top level 'ryvencore' directory. The process is shown for Ubuntu Linux.

1. Remove old ryvencore versions

    $ pip uninstall ryvencore

2. Install GCC

    $ sudo apt install build-essential

3. Install Python dev tools

    $ sudo apt install python3-dev

4. Install dependencies

    $ pip install cython wheel

5. Compile

    $ python -m setup_cython build_ext --inplace

6. Build wheel

    $ python setup_cython.py sdist bdist_wheel

7. Install package from wheel

    $ pip install ./dist/ryvencore-<version>-<platform>.whl

NOTE
-   if you don't want to keep the source files (.py and compiled .c) in the installed package (only the compiled .so
    files), simply comment out the line `packages = find:` in setup.cfg

To verify that the package successfully runs from the compiled C extension modules you can check whether
the imported ryvencore package shows the __init__.so file and not __init__.py

    $ python
    > import ryvencore as rc
    > print(rc)

and to really be sure you can also manually remove all .py files in the installation directory

    on Linux: $ .../site-packages/ryvencore> find . -name "*.py" -type f -delete

and check whether you can successfully load the package from Python.
"""


from setuptools import setup
from Cython.Build import cythonize, build_ext
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
    cmaclass={'build_ext': build_ext},
    ext_modules=cythonize(
        get_ext_paths('ryvencore', exclude_files=['ryvencore/addons/default/DTypes.py']),
        compiler_directives={'language_level': 3},
        annotate=True,
    )
)
