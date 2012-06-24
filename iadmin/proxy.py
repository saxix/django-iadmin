from iadmin.api import ITabularInline
from iadmin.api import IModelAdmin
from iadmin.api import IAdminSite
import django.contrib.admin.sites
import django.contrib.admin.options
import django.contrib.admin.helpers

from iadmin.api import *
site = IAdminSite( 'admin', 'admin')



django.contrib.admin.sites.site = site
django.contrib.admin.site = site

