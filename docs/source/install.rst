
Installation
============

Installing iAdmin is as simple as checking out the source and adding it to
your project or ``PYTHONPATH``.


1. First of all follow the instruction to install `standard admin <standard_admin>`_ application,

2. Either check out iAdmin from `GitHub`_ or to pull a release off `PyPI`_. Doing ``sudo pip install django-iadmin`` or ``sudo easy_install django-iadmin`` is all that should be required.

3. Either symlink the ``iadmin`` directory into your project or copy the directory in. What ever works best for you.

.. include globals.rst

.. _GitHub: http://github.com/saxix/django-iadmin
.. _PyPI: http://pypi.python.org/pypi/django-iadmin/
.. _standard_admin: https://docs.djangoproject.com/en/1.3/ref/contrib/admin/#overview

Configuration
=============
Add :mod:`iadmin` to your :setting:`INSTALLED_APPS`::

    INSTALLED_APPS = (
        'iadmin',
        'django.contrib.admin',
        'django.contrib.messages',
    )


Add an entry into your urls.conf::


    import iadmin.proxy as admin
    admin.autodiscover()
    import iadmin.media_urls

    urlpatterns = patterns('',
                url(r'', include('iadmin.media_urls')),
                (r'^admin/', include(admin.site.urls)),
    )


In your admin.py file::

    import iadmin
    import iadmin.proxy as admin

