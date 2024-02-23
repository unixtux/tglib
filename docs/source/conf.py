# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

#'''
import sys
import os
sys.path.insert(0, os.path.abspath('../../'))
#'''

import tglib

project = 'tglib'
copyright = '2024, unixtux'
author = 'unixtux'
release = tglib.VERSION

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', ]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

'''
autodoc_type_aliases = {
    'InputMedia': 'InputMedia'
#    'Optional': 'Optional',
#    'Union': 'Union',
}
#'''

autodoc_preserve_defaults = True # to preserve default arguments value
autodoc_typehints = 'description' # 'none'
autodoc_typehints_format = 'short'
toc_object_entries = True # to not index members

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo' #'sphinx_rtd_theme' # 'alabaster'
html_static_path = [] # ['_static']
