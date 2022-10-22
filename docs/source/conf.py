# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

from ryvencore import *
from setup_cython import *
from importlib.metadata import metadata

# -- Project information -----------------------------------------------------

project = 'ryvencore'
copyright = '2022, Leon Thomm'
author = 'Leon Thomm'

# The full version, including alpha/beta/rc tags
release = f"v{ metadata('ryvencore')['version'] }"
version = release

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

add_module_names = False

# autodoc options
autodoc_member_order = 'bysource'

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

import maisie_sphinx_theme
extensions.append("maisie_sphinx_theme")
html_theme = 'maisie_sphinx_theme'
html_theme_path = maisie_sphinx_theme.html_theme_path()

# html_theme = 'alabaster'
# 'furo'
# 'karma_sphinx_theme'
# 'insegel'
# 'pydata_sphinx_theme'
# 'furo'
# 'sphinx_rtd_theme'
# 'groundwork' 'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = [
    'custom.css',
]
