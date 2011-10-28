from django.forms.models import ModelChoiceField, modelform_factory
from guardian.models import UserObjectPermission, GroupObjectPermission
from iadmin.options import IModelAdmin
import guardian.admin
from guardian.admin import GuardedModelAdmin

guardian.admin.UserManage = modelform_factory(UserObjectPermission, fields=['user'] )
guardian.admin.GroupManage= modelform_factory(GroupObjectPermission, fields=['group'] )

class IGuardedModelAdmin(IModelAdmin, GuardedModelAdmin):
    change_form_template = 'iadmin/guardian/model/change_form.html'
    obj_perms_manage_template = 'iadmin/guardian/model/obj_perms_manage.html'
    obj_perms_manage_user_template = 'iadmin/guardian/model/obj_perms_manage_user.html'
    obj_perms_manage_group_template = 'iadmin/guardian/model/obj_perms_manage_group.html'
    def get_urls(self):
        urls1 = IModelAdmin.get_urls(self)
        urls2 = GuardedModelAdmin.get_urls(self)
        return urls2+urls1


class BaseObjectPermissionAdmin(IModelAdmin):
    cell_filter = ('content_type', 'user')
    list_filter = ('content_type__app_label',)
    list_display_rel_links = ('content_type',)

    def application(self, h):
        return h.content_type.app_label


class GroupObjectPermissionAdmin(BaseObjectPermissionAdmin):
    list_display = ('id', 'group', 'application', 'content_type', 'object_pk', 'content_object')
    cell_filter = ('content_type','group', )


class UserObjectPermissionAdmin(BaseObjectPermissionAdmin):
    list_display = ('id', 'user', 'application', 'content_type', 'object_pk', 'content_object')
    cell_filter = ('content_type', 'user', )

