#
import re
from django.contrib.admin.util import lookup_field, quote
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.safestring import mark_safe

__author__ = 'sax'

from django.contrib.admin.views.main import ChangeList, IS_POPUP_VAR, SEARCH_VAR, ORDER_TYPE_VAR, ORDER_VAR, ALL_VAR, IGNORED_PARAMS

rex_sub = re.compile("__(exact|not|gt|lt|gte|lte|contains|icontains)")

class IChangeList(ChangeList):

    def __init__(self, request, model, list_display, list_display_links, list_filter, date_hierarchy, search_fields,
                 list_select_related, list_per_page, list_max_show_all, list_editable, model_admin):

        self._filtered_on = []
        self.ordering = None
        self.readonly = False
        super(IChangeList, self).__init__(request, model, list_display, list_display_links, list_filter, date_hierarchy,
                                          search_fields, list_select_related, list_per_page, list_max_show_all,
                                          list_editable, model_admin)

#    def get_filters(self, request):
#        (self.filter_specs, self.has_filters, remaining_lookup_params,
#                     use_distinct) = super(IChangeList, self).get_filters(request)
#        self.has_filters = self.has_filters or self.model_admin.cell_filter
#        return self.filter_specs, self.has_filters, remaining_lookup_params, use_distinct
#
#    def active_filters(self):
#        pass
    def get_filtered_field_columns(self):

        filtered_fields = []
        for p in self.params:
            if p not in IGNORED_PARAMS:
                target = rex_sub.sub("", p)
#                field, _operator = target.rsplit('__', 1)
                filtered_fields.append(target)
        return filtered_fields

    def get_query_set(self, request):
        backup_params = self.params.copy() # a dictionary of the query string
        negate_filters = []
        for key, value in self.params.items():
            if key.endswith('__not'):
                field_name = key.replace('__not', '')
                negate_filters.append(~Q(**{field_name: value}))
                del self.params[key]
                
        ret = super(IChangeList, self).get_query_set(request)
        self.negate_filters = [ c.children[0].children[0][0] for c in negate_filters]
        self.params = backup_params
        return ret.filter(*negate_filters)

    def url_for_result(self, result):
        if self.readonly:
            return "%s/view/" % quote(getattr(result, self.pk_attname))
        return "%s/" % quote(getattr(result, self.pk_attname))

#    def url_for_obj(self, request, obj):
#        if not obj:
#            return 'xxx'
#        if self.model_admin.has_change_permission(request, obj):
#            view = "%s:%s_%s_change" % (self.model_admin.admin_site.app_name, obj._meta.app_label, obj.__class__.__name__.lower())
#            url = reverse(view, args=[int(obj.pk)])
#        elif self.model_admin.has_view_permission(request, obj):
#            url = "view/%s/" % quote(getattr(obj, obj._meta.pk_attname))
#        return mark_safe('<span class="linktomodel" > &nbsp;<a href="%s">&nbsp;</a></span>' % url)

#AGENTS = {lambda x: 'Firefox' in x: ['Firefox', 'iadmin/nojs/firefox.html'],
#          lambda x: 'Chrome' in x: ['Chrome', 'iadmin/nojs/chrome.html'],
#
#
#          }
#
#def nojs(request):
#    for k, v in AGENTS.items():
#        if (k(request.META['HTTP_USER_AGENT'])):
#            name, template = v
#
#    ctx = {'browser': name,
#           'text': 'Preferences -&gt; Security Tab -&gt; Make sure "Enable JavaScript" is checked.',
#           'img': 'iadmin/img/nojs/ie/1.png',
#           }
#    return render_to_response(template, RequestContext(request, ctx))