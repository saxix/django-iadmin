.. _ref-tutorial:

=============================
Getting Started with iAdmin
=============================

iAdmin is a replacement of the standard Django Admin.

This tutorial assumes that you have a basic understanding of Django.
We will only explain the portions of the code that are iAdmin-specific in any kind of depth.

Home Page
---------
As installed iAdmin replace the standard home page with a 'portlets like' version.
The default template use a 5 columns layout, you can move the 'portlets' turu the columns and/or collapse them.
The layout is saved into a cookie to allow it to be restored.

.. image:: _static/home2.png

iAdmin is able to shows the number of rows present in each table, the home page is cached and the cache is
invalidated each time a model is added/deleted using django :func:`django.db.models.signals.post_save` and
:func:`django.db.models.signals.post_delete` (see :mod:`django.db.models.signals`).
If you want enable this feature, you should edit your settings as following::


    IADMIN_CONFIG = { 'count_rows': False,}

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake'
        }
    }

The :setting:`CACHES` configuration is only an example, please refer to Django Cache System for further infos.


IModelAdmin
-----------

    * **Attributes:**

        .. py:attribute:: options.iadmin.IModelAdmin.add_undefined_fields
        If true create an 'Other' fieldset section with all fields not defined in other fieldsets

        .. py:attribute:: options.iadmin.IModelAdmin.list_display_rel_links
        If true create an link to the change form of a model from the changelist cell

        .. py:attribute:: options.iadmin.IModelAdmin.cell_filter
        list of fieldnames ( columns ) that can be filtered on the changelist. Useful if the values of a filter are too
        much to be showed in the left filter panel

        .. py:attribute:: options.iadmin.IModelAdmin.autocomplete_ajax
        If true use an autocomplete ajax widget for the ForeignKey field


    * **Actions:**
        .. function:: actions.export_to_csv
        Export selected queryset as csv file. See :doc:`Export queryset as CSV </actions>`

        .. function:: actions.mass_update

        .. function:: actions.export_as_json


