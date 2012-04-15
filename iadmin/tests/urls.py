from django.conf.urls import patterns, url, include
from django.contrib import admin
import iadmin.tests.admin
admin.autodiscover()

from reg import site1, site2 # here only because we need to access to the instances from the tests
                             # but not rerun autodiscover

site1.autodiscover()
site1.process(iadmin.tests.admin)
site2.investigate_admin(admin.site)

urlpatterns = patterns('',
    (r'^a/', include(admin.site.urls)),
    (r'^admin/', include(site1.urls)),
    (r'^test/', include(site2.urls)),


)

