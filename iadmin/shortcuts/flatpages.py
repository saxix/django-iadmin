from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.admin import FlatPageAdmin as FA
from iadmin.options import IModelAdmin
import iadmin.proxy as admin

class FlatPageAdmin(IModelAdmin, FA):
    list_display = ('url', 'title', 'enable_comments', 'registration_required')
    column_css = {'title':['w200'], 'url':['w300', 'elastic']}

admin.site.silent_unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin)
