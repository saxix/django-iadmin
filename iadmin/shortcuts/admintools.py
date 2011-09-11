from django.utils.text import capfirst
import iadmin.proxy as admin
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
import admin_tools.dashboard.models
from admin_tools.dashboard import modules, Dashboard, AppIndexDashboard
from admin_tools.utils import get_admin_site_name

class BookmarkAdmin(admin.IModelAdmin):
    list_display = ('user', 'title')
    cell_filter = list_filter = ('user',)

class DashboardPreferencesAdmin(admin.IModelAdmin):
    cell_filter = list_filter = list_display = ('user', 'dashboard_id')

#admin.site.register(admin_tools.menu.models.Bookmark, BookmarkAdmin, override=True)
admin.site.register(admin_tools.dashboard.models.DashboardPreferences, DashboardPreferencesAdmin, override=True)

class IAppList(modules.AppList):
    template = 'iadmin/admin_tools/dashboard/app_list.html',

    def init_with_context(self, context):
            if self._initialized:
                return
            items = self._visible_models(context['request'])
            req = context['request']
            apps = {}
            for model, perms in items:
                app_label = model._meta.app_label
                if app_label not in apps:
                    apps[app_label] = {
                        'title': capfirst(app_label.title()),
                        'url': self._get_admin_app_list_url(model, context),
                        'models': []
                    }
                model_dict = {}
                model_dict['title'] = capfirst(model._meta.verbose_name_plural)
                vv = req.user.has_perm
                if perms.get('view', False):
                    model_dict['view_url'] = self._get_admin_change_url(model, context)
                elif perms['change']:
                    model_dict['change_url'] = self._get_admin_change_url(model, context)
                if perms['add']:
                    model_dict['add_url'] = self._get_admin_add_url(model, context)
                apps[app_label]['models'].append(model_dict)

            apps_sorted = apps.keys()
            apps_sorted.sort()
            for app in apps_sorted:
                # sort model list alphabetically
                apps[app]['models'].sort(lambda x, y: cmp(x['title'], y['title']))
                self.children.append(apps[app])
            self._initialized = True


class IAdminDashboard(admin_tools.dashboard.Dashboard):
    columns = 3
    template = 'iadmin/admin_tools/dashboard/dashboard.html'
    def init_with_context(self, context):
            site_name = get_admin_site_name(context)
            # append a link list module for "quick links"
            self.children.append(modules.LinkList(
                _('Quick links'),
                layout='inline',
                children=[
                    [_('Return to site'), '/'],
                    [_('Change password'),
                     reverse('%s:password_change' % site_name)],
                    [_('Log out'), reverse('%s:logout' % site_name)],
                ]
            ))

            # append an app list module for "Applications"
            self.children.append(IAppList(
                _('Applications'),
                exclude=('django.contrib.*','permissions.*'),
            ))

            # append an app list module for "Administration"
            self.children.append(modules.AppList(
                _('Administration'),
                models=('django.contrib.*','permissions.*' ),
            ))

            # append a recent actions module
            self.children.append(modules.RecentActions(_('Recent Actions'), 5))

            # append a feed module
            self.children.append(modules.Feed(
                _('Latest Django News'),
                feed_url='http://www.djangoproject.com/rss/weblog/',
                limit=5
            ))

            # append another link list module for "support".
            self.children.append(modules.LinkList(
                _('Support'),
                children=[
                    {
                        'title': _('Django documentation'),
                        'url': 'http://docs.djangoproject.com/',
                        'external': True,
                    },
                    {
                        'title': _('Django "django-users" mailing list'),
                        'url': 'http://groups.google.com/group/django-users',
                        'external': True,
                    },
                    {
                        'title': _('Django irc channel'),
                        'url': 'irc://irc.freenode.net/django',
                        'external': True,
                    },
                ]
            ))