import django.contrib.admin
from django.contrib.admin import *
from iadmin.sites import IAdminSite, site
from iadmin.options import IModelAdmin as ModelAdmin, ITabularInline as TabularInline
from iadmin.options import IModelAdmin, ITabularInline

django.contrib.admin.site = django.contrib.admin.sites.site = site = IAdminSite()

