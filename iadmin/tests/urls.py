from django.conf.urls import patterns, url, include
from django.contrib import admin
import iadmin.tests.admin

from reg import site1, site2
admin.autodiscover()
site1.autodiscover()
site1.process(iadmin.tests.admin)
site2.investigate_admin(site1)

urlpatterns = patterns('',
    (r'^a/', include(admin.site.urls)),
    (r'^admin/', include(site1.urls)),
    (r'^test/', include(site2.urls)),


)

