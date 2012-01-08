from iadmin.filters import FieldComboFilter, FieldCheckBoxFilter, FieldRadioFilter
from django.contrib.admin.options import TabularInline
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from iadmin.actions import mass_update
from iadmin.options import IModelAdmin
from iadmin.utils import force_register, force_unregister, tabular_factory

class IUserAdmin(UserAdmin, IModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', '_groups', 'last_login')
    list_display_links = ('username', 'first_name', 'last_name')

    cell_filter = ('email', 'is_staff', 'last_name', 'group', 'last_login')
    cell_filter_operators = {'last_login': ('exact', 'not', 'lt', 'gt')}


    list_filter = ( ('groups',FieldCheckBoxFilter), )
    search_fields = ('username', )
    actions = [mass_update]

    def _groups(self, obj):
        return ",".join( [o.name for o in obj.groups.all()])
    _groups.short_description = 'Groups'


class IUserInline(TabularInline):
#    model = User
    model = User.groups.through
    readonly_fields = ('user', )
    extra = 0

class IGroupAdmin(GroupAdmin, IModelAdmin):
    inlines = (IUserInline, )

class IContentType(IModelAdmin):
    list_display = ('name', 'app_label', 'model', )

class IPermission(IModelAdmin):
    list_display = ('name', 'content_type', 'codename', )
    search_fields = ('name'),
    list_filter = cell_filter = ('content_type', )

force_register(User, IUserAdmin)
force_register(Group, IGroupAdmin)
force_register(Permission, IPermission)
force_register(ContentType, IContentType)