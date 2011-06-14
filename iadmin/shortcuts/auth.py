import iadmin.proxy as admin
from django.contrib.auth.admin import UserAdmin as UA, GroupAdmin as GA
from iadmin.options import IModelAdmin
from django.contrib.auth.models import User, Group, Permission
from django.utils.translation import ugettext as _
import django

class UserAdmin(IModelAdmin, UA):

    actions = ['make_active', 'make_inactive',]
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login',]
    list_display = ['first_name', 'last_name', 'email', 'username', 'date_joined', 'is_active', 'is_staff']
    list_display_links = ['first_name', 'last_name', 'email', 'username']

    fieldsets = (
            (None, {'fields': (('username', 'first_name', 'last_name', 'email'),)}),

            (_('Groups'), {'fields': ('groups',)}),
            (_('Permissions'), {'fields': (('is_active', 'is_staff', 'is_superuser'), ('user_permissions',))}),
            (_('Advanced'), {'fields': (('last_login', 'date_joined'),'password', )}),
        )
    filter_horizontal = ('user_permissions', 'groups')
    def make_active(self, request, queryset):
        rows_updated = queryset.update(is_active=True)
        if rows_updated == 1:
            message_bit = "1 person was"
        else:
            message_bit = "%s people were" % rows_updated
        self.message_user(request, "%s successfully made active." % message_bit)

    def make_inactive(self, request, queryset):
        rows_updated = queryset.update(is_active=False)
        if rows_updated == 1:
            message_bit = "1 person was"
        else:
            message_bit = "%s people were" % rows_updated
        self.message_user(request, "%s successfully made inactive." % message_bit)


class GroupAdmin(IModelAdmin, GA):
    pass

    
class PermissionAdmin(IModelAdmin):
    list_display = ('name', 'content_type', 'codename', 'app')
    search_fields = ('name', 'codenamne')
    cell_filter = ('content_type', 'app')
    if django.VERSION[1] >= 3: # before 1.3 cannot filter on 2^ level field
        list_filter = ('content_type__app_label', )

    def app(self, obj):
        return obj.content_type.app_label
    app.admin_order_field = 'content_type__app_label'

admin.site.unregister(User)
admin.site.unregister(Group)

admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Permission, PermissionAdmin)
