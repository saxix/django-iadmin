from django.conf.urls.defaults import patterns, url
from django.contrib.admin import ModelAdmin as DjangoModelAdmin, TabularInline as DjangoTabularInline
from django.contrib.admin.util import flatten_fieldsets
from django.core.urlresolvers import reverse
from django.db.models.fields import AutoField
from . import widgets
from . import actions as ac
from django.db.models.sql.constants import LOOKUP_SEP, QUERY_TERMS
from django.http import HttpResponse
from django.utils.encoding import force_unicode, smart_str
from django.utils.functional import update_wrapper
from django.db import models, transaction
from . import ajax
from .views import IChangeList
import django.utils.simplejson as json
from iadmin.widgets import RelatedFieldWidgetWrapperLinkTo

__all__ = ['IModelAdmin', 'ITabularInline']

AUTOCOMPLETE = 'a'
JSON = 'j'
PJSON = 'p'


class IModelAdmin(DjangoModelAdmin):
    add_undefined_fields = False
    change_form_template = 'admin/change_form_tab.html'
    actions = [ac.mass_update, ac.export_to_csv, ac.export_as_json]

    list_display_rel_links = ()
    cell_filter = ()
    extra_allowed_filter = []
    ajax_search_fields = None
    ajax_list_display = None # always use searchable fields. Never __str__ ol similar
    enable_ajax = False


    def __init__(self, model, admin_site):
        self.ajax_search_fields = self.ajax_search_fields or self.search_fields
        self.ajax_list_display = self.ajax_list_display or self.ajax_search_fields

        super(IModelAdmin, self).__init__(model, admin_site)
        self._process_cell_filter()
        
    def lookup_allowed(self, lookup, value):
        # overriden to allow filter on cell_filter fields
        original = super(IModelAdmin, self).lookup_allowed(lookup, value)
        if original:
            return True
        parts = lookup.split(LOOKUP_SEP)
        if len(parts) > 1 and parts[-1] in QUERY_TERMS:
            parts.pop()
        clean_lookup = LOOKUP_SEP.join(parts)
        return clean_lookup in self.extra_allowed_filter

    def _process_cell_filter(self):
        # add cell_filter fields to `extra_allowed_filter` list
        for entry in self.cell_filter:
            method = getattr(self, entry, None)
            if method:
                cell_filter_field = getattr(method, "admin_order_field", None)
                self.extra_allowed_filter.append ( cell_filter_field )

#    def change_view(self, request, object_id, extra_context=None):
#        return super(IModelAdmin, self).change_view(request, object_id, extra_context)

    def get_changelist(self, request, **kwargs):
        return IChangeList

    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request", None)
        if isinstance(db_field, models.ForeignKey):
            formfield = self.formfield_for_foreignkey(db_field, request, **kwargs)
            modeladmin =  self.admin_site._registry.get( db_field.rel.to, False )
            if self.enable_ajax and  isinstance(modeladmin, IModelAdmin):
                service = reverse( 'admin:%s_%s_ajax' % (modeladmin.model._meta.app_label, modeladmin.model._meta.module_name) )
                if service:
                    formfield.widget = ajax.AjaxFieldWidgetWrapper(formfield.widget, db_field.rel, self.admin_site, service)
                return formfield
            elif formfield:
                formfield.widget = RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
                return formfield

        return super(IModelAdmin, self).formfield_for_dbfield(db_field, request=request, **kwargs)

    def ajax_query(self, request):
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
        bit = request.GET.get('q', '')
        fmt = request.GET.get('fmt', AUTOCOMPLETE)
        or_queries = [models.Q(**{construct_search(str(field_name)): bit}) for field_name in self.ajax_search_fields]
        flds = list(self.ajax_list_display)

        field_names = [f.name for f in self.model._meta.fields]
        qs = self.model.objects.filter(*or_queries)
        data = []
        for record in qs:
            row = [force_unicode(record.pk)]
            for fname in flds:
                if hasattr(record, fname):
                    attr = getattr(record, fname)
                    if callable(attr):
                        val = attr()
                    elif hasattr(self, fname):
                        val = attr
                    elif fname in field_names:
                        val = attr
                elif hasattr(self, fname):
                    attr = getattr(self, fname)
                    val = attr(record)
                        
                row.append( force_unicode( val ))
            data.append( row )

        if fmt == JSON:
            ret = json.dumps( list(data) )
        elif fmt == PJSON:
            ret = json.dumps( list(qs) )
        else: #AUTOCOMPLETE
            ret = '\n'.join( map("|".join, data) )
        return HttpResponse( ret, content_type='text/plain' )
    
    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view, cacheable)(*args, **kwargs)

            return update_wrapper(wrapper, view)
        info = self.model._meta.app_label, self.model._meta.module_name
        urlpatterns = super(IModelAdmin, self).get_urls()
        urlpatterns += patterns('',
                                url(r'^ajax/search$',
                                    wrap(self.ajax_query),
                                    name='%s_%s_ajax' % info),
                                )
        return urlpatterns

    def _declared_fieldsets(self):
        # overriden to handle `add_undefined_fields`
        if self.fieldsets:
            if self.add_undefined_fields:
                def _valid(field):
                    return field.editable and type(field) not in (AutoField, ) and '_ptr' not in field.name

                flds = list(self.fieldsets)
                fieldset_fields = flatten_fieldsets(self.fieldsets)
                alls = [f.name for f in self.model._meta.fields if _valid(f)]
                missing_fields = [f for f in alls if f not in fieldset_fields]
                flds.append(('Other', {'fields': missing_fields, 'classes': ('collapse',), },))
                return flds
            else:
                return self.fieldsets
        elif self.fields:
            return [(None, {'fields': self.fields})]
        return None

    declared_fieldsets = property(_declared_fieldsets)


class ITabularInline(DjangoTabularInline):
    template = 'admin/edit_inline/tabular_tab.html'
    add_undefined_fields = False

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        formfield = super(ITabularInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if formfield and db_field.name not in self.raw_id_fields:
            formfield.widget = widgets.RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
        return formfield

    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request", None)
        if isinstance(db_field, models.ForeignKey):
            formfield = self.formfield_for_foreignkey(db_field, request, **kwargs)
            modeladmin =  self.admin_site._registry.get( db_field.rel.to, False )
            if isinstance(modeladmin, IModelAdmin):
                service = reverse( 'admin:%s_%s_ajax' % (modeladmin.model._meta.app_label, modeladmin.model._meta.module_name) )
                if service:
                    formfield.widget = ajax.AjaxFieldWidgetWrapper(formfield.widget, db_field.rel, self.admin_site, service)
            return formfield

        return super(ITabularInline, self).formfield_for_dbfield(db_field, request=request, **kwargs)

