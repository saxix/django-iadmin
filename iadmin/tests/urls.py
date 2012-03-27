from django.conf.urls import patterns, url, include

import iadmin.api as admin

admin.site.autodiscover()
import iadmin.tests.admin

urlpatterns = patterns('',
        (r'^admin/', include(admin.iservice.urls)),
        (r'^admin/', include(admin.isite.urls)),
)
