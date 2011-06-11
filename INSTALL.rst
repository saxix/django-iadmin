
Install
=======


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
                url(r'', include('iadmin.media_urls')), # iadmin media
                (r'^admin/', include(admin.site.urls)),
                ...
                ...
    )


In your admin.py file::

    import iadmin
    import iadmin.proxy as admin

    class MyModelAdmin(admin.ModelAdmin):
        ...
        ...

