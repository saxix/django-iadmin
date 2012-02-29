import django.contrib.admin
from django.contrib.admin import site, ModelAdmin, TabularInline
from iadmin.api import *
ModelAdmin = IModelAdmin
TabularInline = ITabularInline
django.contrib.admin.ModelAdmin = IModelAdmin
django.contrib.admin.TabularInline = ITabularInline


