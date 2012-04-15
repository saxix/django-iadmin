.. include globals.rst
.. _index:

====================
iAdmin documentation
====================

:Release: |release|
:Date: |today|

iAdmin is an alternative Django Admin application that offer some useful extra `features`; Can works both as replacement of standard admin application or parallel to it on an alternate url.

.. admonition:: Work in progress

    This document is still incomplete e under development


========
Features
========

- tabbed view of inlines
- auto add models not registered
- auto add fields not present in fieldset (add_undefined_fields)
- link to foreignkey edit page from changelist (:ref:`list_display_rel_links<list_display_rel_links>` )
- filters on cell values (:ref:`cell_filter<tutorial-cell-filter>`)
- utilities ( tabular_factory)
- mass updates functionality
- export to csv with options and formatting
- info page for packages and application version
- easy creation of multiple instances that use different template

=================
Table Of Contents
=================
.. toctree::
    :maxdepth: 2
    :hidden:

    install
    api


.. toctree::
    :maxdepth: 2

    install
    tutorial
    actions
    utils
    api
    releases/index
    help


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

