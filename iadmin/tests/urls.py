from django.conf.urls.defaults import *
from django.contrib import admin, auth


admin.autodiscover()
import iadmin.tests.admin

urlpatterns = patterns('',
        (r'^admin/', include(admin.site.urls)),
)
