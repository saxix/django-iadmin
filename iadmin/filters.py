from django.contrib.admin.filters import SimpleListFilter, FieldListFilter, RelatedFieldListFilter
from django.db import models
from django.db.models.query_utils import Q
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode

class FieldComboFilter(RelatedFieldListFilter):
    template = 'iadmin/filters/fieldcombobox.html'

class FieldRadioFilter(RelatedFieldListFilter):
    template = 'iadmin/filters/fieldradio.html'

class FieldCheckBoxFilter(RelatedFieldListFilter):
    template = 'iadmin/filters/fieldcheckbox.html'

    def __init__(self, field, request, params, model, model_admin, field_path):
        super(FieldCheckBoxFilter, self).__init__(field, request, params, model, model_admin, field_path)
        self.lookup_val = request.GET.getlist(self.lookup_kwarg, []);

    def queryset(self, request, queryset):
        if not len(self.lookup_val):
            return queryset

        filters = []
        for val in self.lookup_val:
            filters.append( Q(**{self.lookup_kwarg:val}  ) )

        query = filters.pop()
        for item in filters:
            query |= item

        return queryset.filter(query)

    def choices(self, cl):
        from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
        yield {
            'selected': not len(self.lookup_val) and not self.lookup_val_isnull,
            'query_string': cl.get_query_string({},
                [self.lookup_kwarg, self.lookup_kwarg_isnull]),
            'display': _('All'),
        }
        for pk_val, val in self.lookup_choices:
            yield {
                'selected': smart_unicode(pk_val) in self.lookup_val,
                'query_string': cl.get_query_string({
                    self.lookup_kwarg: pk_val,
                }, [self.lookup_kwarg_isnull]),
                'display': val,
            }
        if (isinstance(self.field, models.related.RelatedObject)
                and self.field.field.null or hasattr(self.field, 'rel')
                    and self.field.null):
            yield {
                'selected': bool(self.lookup_val_isnull),
                'query_string': cl.get_query_string({
                    self.lookup_kwarg_isnull: 'True',
                }, [self.lookup_kwarg]),
                'display': EMPTY_CHANGELIST_VALUE,
            }