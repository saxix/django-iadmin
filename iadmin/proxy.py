

def patch():
    import django.contrib.admin
    import iadmin.api
#    from iadmin.options import IModelAdmin, ITabularInline

    django.contrib.admin.site = iadmin.api.site
    django.contrib.admin.ModelAdmin = iadmin.api.IModelAdmin
    django.contrib.admin.TabularInline = iadmin.api.ITabularInline
#    django.contrib.admin.autodiscover = iadmin.api.site.autodiscover