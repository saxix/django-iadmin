import iadmin.proxy as admin
from django.contrib.auth.admin import UserAdmin as UA, GroupAdmin as GA
from iadmin.options import IModelAdmin
from django.contrib.auth.models import User, Group, Permission
from iadmin.utils import tabular_factory

class UserAdmin(IModelAdmin, UA):
    filter_horizontal = ('user_permissions', 'groups')

class GroupAdmin(IModelAdmin, GA):
    pass
#    inlines = (tabular_factory(User),)


class PermissionAdmin(IModelAdmin):
    list_display = ('name', 'content_type', 'codename', 'app')
    search_fields = ('name', 'codenamne')
    cell_filter = ('content_type', 'app')
    list_filter = ('content_type__app_label', )

    
    def app(self, obj):
        return obj.content_type.app_label
    app.admin_order_field = 'content_type__app_label'

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Permission, PermissionAdmin)
