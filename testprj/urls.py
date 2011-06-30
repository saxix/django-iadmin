from django.conf.urls.defaults import *
import iadmin.proxy as admin

admin.autodiscover()

urlpatterns = patterns('',
        (r'', include('iadmin.media_urls')), # only for development
        (r'^admin/', include(admin.site.urls)),
)
