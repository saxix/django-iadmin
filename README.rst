==============
Django iAdmin
==============

iAdmin is a replacement of standard django admin application.

Features
--------

- multiple columns portlets-like home page
- tabbed view of inlines
- auto register missed modules.
- auto add fields not present in fieldset (add_undefined_fields)
- link to foreignkey edit page from changelist (list_display_rel_links)
- filters on cell values (cell_filters)
- utilities ( tabular_factory)
- ajax autocomplete widgets for ForeignKey
- mass updates functionality
- export to csv with options and formatting
- info page for packages and application version
- integrated file manager with upload/zip functionality

Install
----
Edit your settinhs.py and add iadmin application before django.contrib.admin ::

    INSTALLED_APPS = (
        ...
        'iadmin',
        'django.contrib.admin',
        'django.contrib.messages',
        ...
        ...
    )

Add an entry into your urls.conf ::

    from iadmin.sites import site
    site.autodiscover()

    urlpatterns = patterns('',
                url(r'', include('iadmin.urls')),
                (r'^admin/', include(admin.site.urls)),
                ...
                ...
    )


In your admin.py file ::

    import iadmin
    from iadmin.proxy import *

    site.register....

