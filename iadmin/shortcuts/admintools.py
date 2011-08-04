import iadmin.proxy as admin
import admin_tools

class BookmarkAdmin(admin.IModelAdmin):
    list_display = ('user', 'title')
    cell_filter = list_filter = ('user',)

class DashboardPreferencesAdmin(admin.IModelAdmin):
    cell_filter = list_filter = list_display = ('user', 'dashboard_id')

admin.site.register(admin_tools.menu.models.Bookmark, BookmarkAdmin, override=True)
admin.site.register(admin_tools.dashboard.models.DashboardPreferences, DashboardPreferencesAdmin, override=True)