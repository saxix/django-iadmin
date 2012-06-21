from django.conf.urls import patterns, url, include
from django.contrib import admin
import iadmin.tests.admin

admin.autodiscover()

from reg import site1, site2 # here only because we need to access to the instances from the tests
# but not rerun autodiscover

site1.process(iadmin.tests.admin)
#site1.investigate_admin(admin.site) # clone django.admin.site
#site2.investigate_admin(admin.site) # clone django.admin.site

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^iadmin/', include(site1.urls)),
    (r'^test/', include(site2.urls)),


)

