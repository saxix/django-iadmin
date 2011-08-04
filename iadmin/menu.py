"""
This file was generated with the custommenu management command, it contains
the classes for the admin menu, you can customize this class as you want.

To activate your custom menu add the following to your settings.py::
    ADMIN_TOOLS_MENU = 'testprj.menu.CustomMenu'
"""

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from admin_tools.menu import items, Menu


class AdminToolsIAdminMenu(Menu):
    """
    Custom Menu for testprj admin site.
    """
    def __init__(self, **kwargs):
        Menu.__init__(self, **kwargs)
        self.children += [
            items.MenuItem(_('Dashboard'), reverse('admin:index')),
            items.Bookmarks(),
            items.AppList(
                _('Applications'),
                exclude=('django.contrib.*',)
            ),
            items.AppList(
                _('Administration'),
                models=('django.contrib.*',)
            ),
            items.AppList(
                _('Tools'),
                models=('admin_tools.menu.models.Bookmark','admin_tools.dashboard.models.DashboardPreferences')
            ),
            items.MenuItem(_('Info'), reverse('admin:iadmin.info')),
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super(AdminToolsIAdminMenu, self).init_with_context(context)
