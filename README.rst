==============
Django iAdmin
==============

iAdmin is a replacement of standard django admin application.

Features
--------

- multiple columns portlets-like home page
- tabbed view of inlines
- mass updates functionality
- export to csv with options and formatting
- advanced import from csv with foreign key handling
- link to foreignkey edit page from changelist (list_display_rel_links)
- filter by cell values (cell_filters)
- ajax autocomplete widgets for ForeignKey
- auto register missed modules.
- auto add fields not present in fieldset (add_undefined_fields)
- utilities ( tabular_factory)
- info page for packages and application version
- integrated file manager with upload/zip functionality
- WYSIWYG editor wymeditor
- shortcuts to configure django.contrib.*  applications

Install
----
Edit your settings.py and add iadmin application before django.contrib.admin ::

    INSTALLED_APPS = (
        ...
        'iadmin',
        'django.contrib.admin',
        'django.contrib.messages',
        ...
        ...
    )
    IADMIN_FILE_UPLOAD_MAX_SIZE = 2000000 #
    IADMIN_FM_ROOT = # file manager home
    IADMIN_FM_CONFIG = {}

Add an entry into your urls.conf ::

    from django.conf.urls.defaults import *
    import iadmin.proxy as admin

    admin.autodiscover()

    urlpatterns = patterns('',
            (r'', include('iadmin.media_urls')), # only for development
            (r'^admin/', include(admin.site.urls)),
    )


In your admin.py file ::

    from django.contrib.admin.options import TabularInline
    from geo.models import Country, Lake, Location, Ocean

    from iadmin.utils import tabular_factory..

