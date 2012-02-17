from django.contrib.admin import site, ModelAdmin, TabularInline
from iadmin.api import *

def patch():
    import django.contrib.admin
    import iadmin.api

    django.contrib.admin.ModelAdmin = iadmin.api.IModelAdmin
    django.contrib.admin.TabularInline = iadmin.api.ITabularInline
