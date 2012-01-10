import django.contrib.admin
import iadmin
from iadmin.options import IModelAdmin, ITabularInline

def patch():
    django.contrib.admin.site = iadmin.sites.site
    django.contrib.admin.ModelAdmin = IModelAdmin
    django.contrib.admin.TabularInline = ITabularInline
    django.contrib.admin.autodiscover = iadmin.sites.site.autodiscover