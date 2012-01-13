#
from django.contrib.admin.util import lookup_field, quote, lookup_needs_distinct, get_fields_from_path
from django.db import models
from django.db.models import Q
from django.db.models.fields import FieldDoesNotExist, BooleanField
from django.utils.functional import cached_property
from iadmin.filters import FieldCellFilter, RelatedFieldCellFilter, ChoicesCellFilter, BooleanCellFilter

__author__ = 'sax'

from django.contrib.admin.views.main import ChangeList, IS_POPUP_VAR, SEARCH_VAR, ORDER_TYPE_VAR, ORDER_VAR, ALL_VAR, IGNORED_PARAMS


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
