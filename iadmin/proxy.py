

def patch():
    import django.contrib.admin
    import iadmin.api

    django.contrib.admin.site = iadmin.api.site
    django.contrib.admin.ModelAdmin = iadmin.api.IModelAdmin
    django.contrib.admin.TabularInline = iadmin.api.ITabularInline
    django.contrib.admin.autodiscover = iadmin.api.site.autodiscover