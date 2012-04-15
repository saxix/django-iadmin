import django.contrib.admin
import iadmin.api
django.contrib.admin.site = iadmin.api.site
django.contrib.admin.ModelAdmin = iadmin.api.IModelAdmin
django.contrib.admin.TabularInline = iadmin.api.ITabularInline

from django.contrib.admin import site, ModelAdmin, TabularInline
from iadmin.api import *


