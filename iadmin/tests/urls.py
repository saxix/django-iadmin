from django.conf.urls import patterns, url, include
from django.contrib import admin, auth

from iadmin.api import iservice
#import iadmin.proxy as admin
#iadmin.proxy.patch()
admin.autodiscover()
import iadmin.tests.admin

urlpatterns = patterns('',
        (r'^admin/', include(iservice.urls)),
        (r'^admin/', include(admin.site.urls)),
)
