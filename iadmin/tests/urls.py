from django.conf.urls.defaults import *
import iadmin.proxy as admin
import iadmin.STATIC_URLs


admin.autodiscover()

urlpatterns = patterns('',

        (r'admin/', include(iadmin.static_urls)),

        (r'^admin/', include(admin.site.urls)),
)
