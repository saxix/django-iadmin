from django.conf import settings
from django.conf.urls.defaults import patterns
import iadmin
import os

urlpatterns = patterns('',
                #iadmin media
                (r'^%siadmin/(?P<path>.*)' % settings.STATIC_URL[1:], 'django.views.static.serve',
                    {'document_root':os.path.join(os.path.abspath(os.path.dirname(iadmin.__file__)), 'static', 'iadmin'),
                     'show_indexes':True}),
                       )
