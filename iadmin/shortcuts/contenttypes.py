from django.contrib.contenttypes.models import ContentType
from iadmin.options import IModelAdmin
import iadmin.proxy as admin

class ContentTypeAdmin(IModelAdmin):
    list_filter = ['app_label',]
    list_display = list_display_links = ['name', 'app_label', 'model']
    search_fields = ('name', 'app_label',)


admin.site.silent_unregister(ContentType)
admin.site.register(ContentType, ContentTypeAdmin)
