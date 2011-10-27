#
from iadmin.options import IModelAdmin

__author__ = 'sax'


from guardian.admin import GuardedModelAdmin
#

class IGuardedModelAdmin(IModelAdmin, GuardedModelAdmin):
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
