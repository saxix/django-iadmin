from django.conf.urls.defaults import *
import iadmin.proxy as admin
import iadmin.media_urls


admin.autodiscover()

urlpatterns = patterns('',

        (r'', include(iadmin.media_urls)),

        (r'', include(admin.site.urls)),
)
