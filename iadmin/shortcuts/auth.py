from django.conf import settings
from django.core.urlresolvers import resolve, reverse
from django.db.models.loading import get_model
from django.utils.safestring import mark_safe
import iadmin.proxy as admin
from django.contrib.auth.admin import UserAdmin as UA, GroupAdmin as GA
from iadmin.options import IModelAdmin
from django.contrib.auth.models import User, Group, Permission
from django.utils.translation import ugettext as _
import django

class UserAdmin(IModelAdmin, UA):

    actions = ['make_active', 'make_inactive',]
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login',]
    list_display = ['username', 'last_name', 'first_name', 'email', 'date_joined', 'is_active', 'is_staff', 'profile']
    list_display_links = ['first_name', 'last_name', 'email', 'username']
    
    fieldsets = (
            (None, {'fields': (('username', 'first_name', 'last_name', 'email'),)}),

            (_('Groups'), {'fields': ('groups',),'classes': ['collapse']}),
            (_('Permissions'), {'fields': (('is_active', 'is_staff', 'is_superuser'), ('user_permissions',)),'classes': ['collapse']}),
            (_('Advanced'), {'fields': (('last_login', 'date_joined'),'password', )}),
        )
    filter_horizontal = ('user_permissions', 'groups')
    columns_classes = {'last_name':['w200'], 'first_name':['w200'], 'email':['w200']}

    def profile(self, obj):
        if hasattr(settings, 'AUTH_PROFILE_MODULE'):
            app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
            model = get_model(app_label, model_name)
            # FIXME: should be a better way to do this
            # move in ModelAdmin
            model._default_manager.using(obj._state.db).get_or_create(user=obj)
            if model in self.admin_site._registry:
                url = reverse(('admin:%s_%s_change' % (app_label, model_name)).lower(), args=[obj.pk])
                return '<a href="%s">profile</a>' % url
        return ''
    profile.allow_tags = True

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
    search_fields = ('name', 'codename')
    cell_filter = ('content_type', 'app')
    list_filter = ('content_type__app_label', )
#
    def app(self, obj):
        return obj.content_type.app_label
#    app.admin_order_field = 'content_type'
    app.admin_order_field = 'content_type__app_label'

#admin.site.silent_unregister(User)
#admin.site.silent_unregister(Group)

admin.site.register(User, UserAdmin, override=True)
admin.site.register(Group, GroupAdmin, override=True)
admin.site.register(Permission, PermissionAdmin, override=True)
