"""
This setup file can be used to manually compile ryvencore to a C extension using Cython, behavior should be the same.

Follow the below process to compile ryvencore with Cython and install it as a regular package.
Points 1 - 4 are only necessary if they are not satisfied already.
Run all commands from the top level 'ryvencore' directory. The process is shown for Ubuntu Linux.
Assuming only Python is installed already:

1. Remove old ryvencore versions

.. code-block:: bash

    $ pip uninstall ryvencore

2. Install GCC

.. code-block:: bash

    $ sudo apt install build-essential

3. Install Python dev tools

.. code-block:: bash

    $ sudo apt install python3-dev

4. Install Python dependencies

.. code-block:: bash

    $ pip install cython wheel

5. Compile

.. code-block:: bash

    $ python -m setup_cython build_ext --inplace

6. Build wheel

.. code-block:: bash

    $ python setup_cython.py sdist bdist_wheel

7. Install package from wheel

.. code-block:: bash

    $ pip install ./dist/ryvencore-<version>-<platform>.whl

NOTE

- if you don't want to keep the source files (.py and compiled .c) in the installed package (only the compiled .so \
files), simply comment out the line `packages = find:` in setup.cfg
- you can remove all the generated files and directories by running :code:`python cleanup_cython.py`

To verify that the package successfully runs from the compiled C extension modules you can check whether
the imported ryvencore package shows the :code:`__init__.so` file and not :code:`__init__.py`.


.. code-block:: bash

    $ python
    > import ryvencore as rc
    > print(rc)

and to really be sure you can also manually remove all .py files in the installation directory

.. code-block:: bash

   .../site-packages/ryvencore> find . -name "*.py" -type f -delete

and check whether you can successfully load the package from Python.
"""


import os


def get_ext_paths(root_dir, exclude_files=[], recursive=True):

    # get filepaths for compilation

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


if __name__ == '__main__':

    # these dependencies are not required for ryvencore to run, only for compilation
    # to avoid breaking the documentation build process, we hide them for sphinx
    from setuptools import setup
    from Cython.Build import cythonize, build_ext

    setup(
        cmaclass={'build_ext': build_ext},
        ext_modules=cythonize(
            get_ext_paths('ryvencore', exclude_files=['ryvencore/addons/legacy/DTypes.py']),
            compiler_directives={'language_level': 3},
            annotate=True,
        )
    )
