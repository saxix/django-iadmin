from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.admin import FlatPageAdmin as FA
from iadmin.options import IModelAdmin
import iadmin.proxy as admin

class FlatPageAdmin(IModelAdmin, FA):
    list_display = ('url', 'title', 'enable_comments', 'registration_required')
    columns_classes = {'title':['w200'], 'url':['w300', 'elastic']}

#    class Media:
#        js = ( 'iadmin/js/jquery.min.js',
#               'iadmin/js/tiny_mce/jquery.tinymce.js',
#               'iadmin/js/tiny_mce/django_init.js',)

    class Media:
        js = ('iadmin/js/jquery.min.js',
              'iadmin/js/wymeditor/jquery.wymeditor.min.js',
              'iadmin/js/wymeditor/django_init.js',)

admin.site.silent_unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin)
