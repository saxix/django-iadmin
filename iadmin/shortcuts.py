# -*- coding: utf-8 -*-

from guardian.admin import GuardedModelAdmin
from iadmin.options import IModelAdmin, IModelAdminMixin

class IGuardedModelAdmin(IModelAdminMixin, GuardedModelAdmin):
    change_form_template =    'iadmin/guardian/model/change_form.html'
    obj_perms_manage_template ='iadmin/guardian/model/obj_perms_manage.html'
    obj_perms_manage_user_template ='iadmin/guardian/model/obj_perms_manage_user.html'
    obj_perms_manage_group_template ='iadmin/guardian/model/obj_perms_manage_group.html'


#    def get_urls(self):
#        return
