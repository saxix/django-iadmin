#
import re
from django.conf import settings
from django.contrib.admin.filters import FieldListFilter
from django.contrib.admin.util import lookup_field, quote, lookup_needs_distinct, get_fields_from_path
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist, BooleanField
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.functional import cached_property
from django.utils.html import escape
from django.utils.safestring import mark_safe
from iadmin.filters import CellFilter, FieldCellFilter, RelatedFieldCellFilter, ChoicesCellFilter, BooleanCellFilter
from iadmin.utils import iter_get_attr

__author__ = 'sax'

from django.contrib.admin.views.main import ChangeList, IS_POPUP_VAR, SEARCH_VAR, ORDER_TYPE_VAR, ORDER_VAR, ALL_VAR, IGNORED_PARAMS

rex_sub = re.compile("__(exact|not|gt|lt|gte|lte|contains|icontains)")

class IChangeList(ChangeList):

    def __init__(self, request, model, list_display, list_display_links, list_filter, date_hierarchy, search_fields,
                 list_select_related, list_per_page, list_max_show_all, list_editable, model_admin):

        self.readonly = False
        self.request = request

        super(IChangeList, self).__init__(request, model, list_display, list_display_links, list_filter, date_hierarchy,
                                          search_fields, list_select_related, list_per_page, list_max_show_all,
                                          list_editable, model_admin)

    @cached_property
    def cell_filters(self):
        lookup_params = self.params.copy() # a dictionary of the query string
        cell_filter_specs = {}
        use_distinct = False

        if self.model_admin.cell_filter:
            for cell_filter in self.model_admin.cell_filter:
                path = field_path = None
                field, field_list_filter_class = cell_filter, FieldCellFilter

                if hasattr(self.model_admin, cell_filter):
                    # if it's a ModelAdmin method get the `admin_filter_field`
                    attr = getattr(self.model_admin, cell_filter)
                    field_path = getattr(attr, 'admin_filter_field')
                    path = get_fields_from_path(self.model, field_path)
                    field = path[-1]

                if not isinstance(field, models.Field):
                    try:
                        field_path = field
                        field = get_fields_from_path(self.model, field_path)[-1]

                    except FieldDoesNotExist:
                        raise Exception( "Cannot use field `%s` in cell_filter. Only valid Field objects are allowed" % cell_filter)

                if isinstance(field, BooleanField):
                    field_list_filter_class = BooleanCellFilter
                elif hasattr(field, 'rel') and bool(field.rel):
                    field_list_filter_class = RelatedFieldCellFilter
                elif hasattr(field, 'choices'):
                    field_list_filter_class = ChoicesCellFilter
                spec = field_list_filter_class(field, self.request, lookup_params,
                    self.model, self.model_admin, field_path=field_path)

                # Check if we need to use distinct()
                use_distinct = (use_distinct or
                                lookup_needs_distinct(self.lookup_opts,
                                                      field_path))
                if spec and spec.has_output():
                    cell_filter_specs[cell_filter] = spec

        return cell_filter_specs

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

#    def url_for_result(self, result):
#        if self.readonly:
#            return "%s/view/" % quote(getattr(result, self.pk_attname))
#        return "%s/" % quote(getattr(result, self.pk_attname))

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