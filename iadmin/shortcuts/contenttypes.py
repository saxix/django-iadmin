from django.contrib.contenttypes.models import ContentType
from iadmin.options import IModelAdmin
import iadmin.proxy as admin

class ContentTypeAdmin(IModelAdmin, SA):
    pass


admin.site.unregister(ContentType)
admin.site.register(ContentType, ContentTypeAdmin)
