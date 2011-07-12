#
import operator
from django.conf import settings
from django.contrib.admin.filterspecs import FilterSpec
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import lookup_field
from django.db import models
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import smart_str
from .filterspecs import *

__author__ = 'sax'

from django.contrib.admin.views.main import ChangeList, IS_POPUP_VAR, SEARCH_VAR, ORDER_TYPE_VAR, ORDER_VAR, ALL_VAR

class IFilterSpec(FilterSpec):
    def __init__(self, f, request, params, model, model_admin):
        self.field = f
        self.params = params


class IChangeList(ChangeList):

    def __init__(self, request, model, list_display, list_display_links, list_filter, date_hierarchy, search_fields,
                 list_select_related, list_per_page, list_editable, model_admin):

        self._filtered_on = []
        self.ordering = None
        super(IChangeList, self).__init__(request, model, list_display, list_display_links, list_filter, date_hierarchy,
                                          search_fields, list_select_related, list_per_page, list_editable, model_admin)

    def __get_query_set(self, request=None):
        qs = self.root_query_set
        lookup_params = self.params.copy() # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR):
            if i in lookup_params:
                del lookup_params[i]
        negate_filters = []
        for key, value in lookup_params.items():
            if not isinstance(key, str):
                # 'key' will be used as a keyword argument later, so Python
                # requires it to be a string.
                del lookup_params[key]
                lookup_params[smart_str(key)] = value

            # if key ends with __in, split parameter into separate values
            if key.endswith('__in'):
                lookup_params[key] = value.split(',')

            if key.endswith('__not'):
                negate_filters.append(~Q(**{key.replace('__not', ''): value}))
                del lookup_params[key]

            # if key ends with __isnull, special case '' and false
            if key.endswith('__isnull'):
                if value.lower() in ('', 'false'):
                    lookup_params[key] = False
                else:
                    lookup_params[key] = True

        # Apply lookup parameters from the query string.
        try:
            qs = qs.filter(**lookup_params).filter(*negate_filters)
        # Naked except! Because we don't have any other way of validating "params".
        # They might be invalid if the keyword arguments are incorrect, or if the
        # values are not in the correct type, so we might get FieldError, ValueError,
        # ValicationError, or ? from a custom field that raises yet something else
        # when handed impossible data.
        except:
            raise IncorrectLookupParameters

        # Use select_related() if one of the list_display options is a field
        # with a relationship and the provided queryset doesn't already have
        # select_related defined.
        if not qs.query.select_related:
            if self.list_select_related:
                qs = qs.select_related()
            else:
                for field_name in self.list_display:
                    try:
                        f = self.lookup_opts.get_field(field_name)
                    except models.FieldDoesNotExist:
                        pass
                    else:
                        if isinstance(f.rel, models.ManyToOneRel):
                            qs = qs.select_related()
                            break

        # Set ordering.
        if self.order_field:
            qs = qs.order_by('%s%s' % ((self.order_type == 'desc' and '-' or ''), self.order_field))

        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        if self.search_fields and self.query:
            for bit in self.query.split():
                or_queries = [models.Q(**{construct_search(str(field_name)): bit}) for field_name in self.search_fields]
                qs = qs.filter(reduce(operator.or_, or_queries))
            for field_name in self.search_fields:
                if '__' in field_name:
                    qs = qs.distinct()
                    break

        return qs


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