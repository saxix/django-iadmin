.. _ref-tutorial:

=============================
Getting Started with iAdmin
=============================

iAdmin is a replacement of the standard Django Admin.

This tutorial assumes that you have a basic understanding of Django.
We will only explain the portions of the code that are iAdmin-specific in any kind of depth.

Installation
============

Installing Tastypie is as simple as checking out the source and adding it to
your project or ``PYTHONPATH``.

    1. Download the dependencies:
        * Python 2.4+
        * Django 1.2.3+

    2. Either check out iadmin from GitHub_ or to pull a release off PyPI_.
     Doing ``sudo pip install django-iadmin`` or
     ``sudo easy_install django-iadmin`` is all that should be required.

    3. Either symlink the ``iadmin`` directory into your project or copy the
     directory in. What ever works best for you.

.. _GitHub: http://github.com/saxix/django-iadmin
.. _PyPI: http://pypi.python.org/


Configuration
=============

Edit your settinhs.py and add iadmin application before django.contrib.admin::

    INSTALLED_APPS = (
        ...
        'iadmin',
        'django.contrib.admin',
        'django.contrib.messages',
        ...
        ...
    )


Add an entry into your urls.conf::


    import iadmin.proxy as admin
    admin.autodiscover()
    import iadmin.media_urls

    urlpatterns = patterns('',
                url(r'', include('iadmin.media_urls')),
                (r'^admin/', include(admin.site.urls)),
                ...
                ...
    )


In your admin.py file::

    import iadmin
    import iadmin.proxy as admin


Customization
=============


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


