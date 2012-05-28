.. _install:

.. include globals.rst

Installation
============

Installing iAdmin is as simple as checking out the source and adding it to
your project or ``PYTHONPATH``.


1. First of all follow the instruction to install `standard admin <standard_admin>`_ application,

2. Either check out iAdmin from `GitHub`_ or to pull a release off `PyPI`_. Doing ``pip install django-iadmin`` or ``easy_install django-iadmin`` is all that should be required.

3. Either symlink the ``iadmin`` directory into your project or copy the directory in. What ever works best for you.



.. _GitHub: http://github.com/saxix/django-iadmin
.. _PyPI: http://pypi.python.org/pypi/django-iadmin/
.. _standard_admin: https://docs.djangoproject.com/en/1.3/ref/contrib/admin/#overview

Configuration
=============

Add :mod:`iadmin` to your :setting:`INSTALLED_APPS`::

    INSTALLED_APPS = (
        'iadmin', # must be before django.contrib.admin to select right templates
        'django.contrib.admin',
        'django.contrib.messages',
    )



Add an entry into your urls.conf::

    from django.contrib import admin
    import iadmin.api

    site1 = iadmin.api.IAdminSite()
    site1.process(myapp.admin)

    urlpatterns = patterns('',
        (r'^admin/', include(admin.site.urls)), # standard admin
        (r'^iadmin/', include(site1.urls)), # iadmin instance
    )


Configure your admin::

    class IUserAdmin(IModelAdminMixin, UserAdmin):
        list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', '_groups', 'last_login')
        list_display_links = ('username', 'first_name', 'last_name')

        cell_filter = ('email', 'is_staff', 'last_name', 'last_login')
        cell_filter_operators = {'last_login': ('exact', 'not', 'lt', 'gt')}

        list_filter = ( ('groups', RelatedFieldCheckBoxFilter), )
        search_fields = ('username', )
        actions = [mass_update]

    __iadmin__ = ((User, IUserAdmin), )

