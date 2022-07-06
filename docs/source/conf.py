# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

import calatrava

# -- Project information -----------------------------------------------------

project = "calatrava"
author = "L. F. Pereira"
copyright = f"2022, {author}"

# The full version, including alpha/beta/rc tags
release = calatrava.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = ["myst_parser"]

source_suffix = [".rst", ".md"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# general sphinx config
add_module_names = False

# mathjax config within myst_parser
suppress_warnings = ["myst.mathjax"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "github_url": "https://github.com/lpereira95/calatrava",
    "icon_links": [
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/calatrava",
            "icon": "fas fa-box",
        },
    ]
}
