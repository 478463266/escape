#!/bin/bash

# See more: https://pythonhosted.org/an_example_pypi_project/sphinx.html

#sudo easy_install -U Sphinx
# cd ~/escape/src/escape_v2/pox/ext
# mkdir doc
#sphinx-quickstart

# # # Welcome to the Sphinx 1.3.1 quickstart utility.
# # # 
# # # Please enter values for the following settings (just press Enter to
# # # accept a default value, if one is given in brackets).
# # # 
# # # Enter the root path for documentation.
# # # > Root path for the documentation [.]: doc
# # # 
# # # You have two options for placing the build directory for Sphinx output.
# # # Either, you use a directory "_build" within the root path, or you separate
# # # "source" and "build" directories within the root path.
# # # > Separate source and build directories (y/n) [n]: y
# # # 
# # # Inside the root directory, two more directories will be created; "_templates"
# # # for custom HTML templates and "_static" for custom stylesheets and other static
# # # files. You can enter another prefix (such as ".") to replace the underscore.
# # # > Name prefix for templates and static dir [_]: 
# # # 
# # # The project name will occur in several places in the built documentation.
# # # > Project name: ESCAPEv2
# # # > Author name(s): Janos Czentye
# # # 
# # # Sphinx has the notion of a "version" and a "release" for the
# # # software. Each version can have multiple releases. For example, for
# # # Python the version is something like 2.5 or 3.0, while the release is
# # # something like 2.5.1 or 3.0a1.  If you don't need this dual structure,
# # # just set both to the same value.
# # # > Project version: 2.0.0
# # # > Project release [2.0.0]: 
# # # 
# # # If the documents are to be written in a language other than English,
# # # you can select a language here by its language code. Sphinx will then
# # # translate text that it generates into that language.
# # # 
# # # For a list of supported codes, see
# # # http://sphinx-doc.org/config.html#confval-language.
# # # > Project language [en]: 
# # # 
# # # The file name suffix for source files. Commonly, this is either ".txt"
# # # or ".rst".  Only files with this suffix are considered documents.
# # # > Source file suffix [.rst]: 
# # # 
# # # One document is special in that it is considered the top node of the
# # # "contents tree", that is, it is the root of the hierarchical structure
# # # of the documents. Normally, this is "index", but if your "index"
# # # document is a custom template, you can also set this to another filename.
# # # > Name of your master document (without suffix) [index]: 
# # # 
# # # Sphinx can also add configuration for epub output:
# # # > Do you want to use the epub builder (y/n) [n]: n
# # # 
# # # Please indicate if you want to use one of the following Sphinx extensions:
# # # > autodoc: automatically insert docstrings from modules (y/n) [n]: y
# # # > doctest: automatically test code snippets in doctest blocks (y/n) [n]: n
# # # > intersphinx: link between Sphinx documentation of different projects (y/n) [n]: y
# # # > todo: write "todo" entries that can be shown or hidden on build (y/n) [n]: n
# # # > coverage: checks for documentation coverage (y/n) [n]: n
# # # > pngmath: include math, rendered as PNG images (y/n) [n]: n
# # # > mathjax: include math, rendered in the browser by MathJax (y/n) [n]: n
# # # > ifconfig: conditional inclusion of content based on config values (y/n) [n]: y
# # # > viewcode: include links to the source code of documented Python objects (y/n) [n]: y
# # # 
# # # A Makefile and a Windows command file can be generated for you so that you
# # # only have to run e.g. `make html' instead of invoking sphinx-build
# # # directly.
# # # > Create Makefile? (y/n) [y]: y
# # # > Create Windows command file? (y/n) [y]: n

# conf.py --> insert
# sys.path.insert(0, os.path.abspath('../..'))  # ext dir
# sys.path.insert(0, os.path.abspath('../../..'))  # main pox dir
# html_theme = 'classic'

# cd doc
# sphinx-apidoc -f -o source/ ../

# index.rst --> insert
#    modules.rst
make clean
make html latexpdf
#sphinx-build -b html -d build/doctrees   source build/html