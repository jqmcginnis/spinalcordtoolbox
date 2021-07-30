# -*- coding: utf-8 -*-
#
# Spinal Cord Toolbox documentation build configuration file, created by
# sphinx-quickstart on Mon Mar 26 11:35:58 2018.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

# allows sphinx to call CLI scripts and capture --help output
sct_root = os.path.abspath('../../')
sys.path.insert(0, sct_root)

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinxcontrib.programoutput',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'recommonmark',
    'sphinx.ext.extlinks',
    'sphinx_copybutton'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# copybutton_image_path = "img/copy.png"

# add doc for __init
autoclass_content = 'both'

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = ['.rst', '.md']
# source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'Spinal Cord Toolbox'
copyright = u'2020, SCT Contributors'
author = u'SCT Contributors'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
# version = u'3'
# The full version, including alpha/beta/rc tags.
# TODO: fetch latest release
# release = u'3.2.2'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['*/api', "*/api.rst"]

# The name of the Pygments (syntax highlighting) style to use.
# pygments_style = "monokai"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False

extlinks = {
    # e.g. :sct_tutorial_data:`data_template-registration.zip` gets expanded into:
    # 'https://github.com/spinalcordtoolbox/sct_tutorial_data/releases/download/<tag>/data_template-registration.zip'
    'sct_tutorial_data': ('https://github.com/spinalcordtoolbox/sct_tutorial_data/releases/download/r20210609/%s', '')
}


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
# html_theme = "sphinx_rtd_theme"
html_theme = "furo"

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = './_static/img/sct_logo_dark_grey.png'

html_theme_options = {
    "sidebar_hide_name": True,
    "light_css_variables": {
            "color-background-primary": "#fcfcfc",
            "color-sidebar-background": "#3d3d3c",
            # --color-admonition-title-background: #EAF6FF;
            # --color-admonition-title: #c2e2fb;
            # --color-admonition-title-background--note: #30c42626;
            # --color-admonition-title--note: #30c42659;
    }
}

html_context = {
    "display_github": True,
    "github_user": "neuropoly",
    "github_repo": "spinalcordtoolbox",
    "github_version": "master",
    "conf_py_path": "/documentations/",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_css_files = ['css/custom.css', 'css/pygments_dark.css']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
# html_sidebars = {
#     '**': [
#         'about.html',
#         'navigation.html',
#         'relations.html',  # needs 'show_related': True theme option to display
#         'searchbox.html',
#     ]
# }


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'SpinalCordToolboxdoc'


# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'SpinalCordToolbox.tex', u'Spinal Cord Toolbox Documentation',
     u'SCT Contributors', 'manual'),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'spinalcordtoolbox', u'Spinal Cord Toolbox Documentation',
     [author], 1)
]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'SpinalCordToolbox', u'Spinal Cord Toolbox Documentation',
     author, 'SpinalCordToolbox', 'One line description of project.',
     'Miscellaneous'),
]
