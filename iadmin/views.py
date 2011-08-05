#
import operator
from django.conf import settings
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import lookup_field
from django.db import models
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import smart_str
import django

__author__ = 'sax'

from django.contrib.admin.views.main import ChangeList, IS_POPUP_VAR, SEARCH_VAR, ORDER_TYPE_VAR, ORDER_VAR, ALL_VAR


class IChangeList(ChangeList):

    def __init__(self, request, model, list_display, list_display_links, list_filter, date_hierarchy, search_fields,
                 list_select_related, list_per_page, list_editable, model_admin):

        self._filtered_on = []
        self.ordering = None
        super(IChangeList, self).__init__(request, model, list_display, list_display_links, list_filter, date_hierarchy,
                                          search_fields, list_select_related, list_per_page, list_editable, model_admin)

    def active_filters(self):
        pass

    def get_query_set(self, request=None):
        backup_params = self.params.copy() # a dictionary of the query string
        negate_filters = []
        for key, value in self.params.items():
            if key.endswith('__not'):
                field_name = key.replace('__not', '')
                negate_filters.append(~Q(**{field_name: value}))
                del self.params[key]
                
        # todo remove backward compatibility 
        if django.VERSION[0:2] == (1,3):
            ret = super(IChangeList, self).get_query_set()
        else:
            ret = super(IChangeList, self).get_query_set(request)
        self.negate_filters = [ c.children[0].children[0][0] for c in negate_filters]
        self.params = backup_params
        return ret.filter(*negate_filters)


AGENTS = {lambda x: 'Firefox' in x: ['Firefox', 'iadmin/nojs/firefox.html'],
          lambda x: 'Chrome' in x: ['Chrome', 'iadmin/nojs/chrome.html'],


          }

def nojs(request):
    for k, v in AGENTS.items():
        if (k(request.META['HTTP_USER_AGENT'])):
            name, template = v

    ctx = {'browser': name,
           'text': 'Preferences -&gt; Security Tab -&gt; Make sure "Enable JavaScript" is checked.',
           'img': 'iadmin/img/nojs/ie/1.png',
           }
    return render_to_response(template, RequestContext(request, ctx))