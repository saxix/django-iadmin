from django.conf.urls.defaults import *
from django.conf import settings
from django.views.static import serve
from django.contrib import admin
from django import get_version 
settings.DJANGO_VERSION = get_version() # only for debugging purpose 
admin.autodiscover()


urlpatterns = patterns('',
   
    (r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], serve, {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),

    (r'^%s(?P<path>.*)$' % settings.XADMIN_MEDIA_URL[1:], serve, {'document_root': settings.XADMIN_MEDIA_ROOT, 'show_indexes': True}),

    ('^$', 'django.views.generic.simple.redirect_to', {'url': '/admin/'}),
    (r'^admin/', include(admin.site.urls)),
    )
