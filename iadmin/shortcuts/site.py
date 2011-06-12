from iadmin.options import IModelAdmin
import iadmin.proxy as admin
from django.contrib.sites.models import Site
from django.contrib.sites.admin import SiteAdmin as SA

class SiteAdmin(IModelAdmin, SA):
    pass


admin.site.unregister(Site)
admin.site.register(Site, SiteAdmin)
