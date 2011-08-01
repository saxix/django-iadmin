from django.conf.urls.defaults import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import iadmin.proxy as admin

admin.autodiscover()

urlpatterns = patterns('',
#    (r'', include('iadmin.media_urls')), # only for development\
        (r'^admin/', include(admin.site.urls)),
)

#urlpatterns += staticfiles_urlpatterns()