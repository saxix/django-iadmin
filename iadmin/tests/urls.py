from django.conf.urls.defaults import *
from django.contrib import admin, auth

from iadmin.api import iservice
admin.autodiscover()
import iadmin.tests.admin

urlpatterns = patterns('',
        (r'^admin/', include(admin.site.urls)),
        (r'^iadmin/', include(iservice.urls)),
)
