#import django
#import django.contrib.admin.util
from django.conf.urls.defaults import patterns, url
from django.contrib.admin import ModelAdmin as DjangoModelAdmin, TabularInline as DjangoTabularInline
from django.contrib.admin.util import flatten_fieldsets
from django.db.models.fields import AutoField
from . import widgets
from . import actions as ac
from django.http import HttpResponse
from django.utils.encoding import force_unicode, smart_str
from django.utils.functional import update_wrapper
from django.db import models, transaction
from iadmin.views import IChangeList
import django.utils.simplejson as json

__all__ = ['IModelAdmin', 'ITabularInline']

#def empty(modeladmin, request, queryset):
#    modeladmin.model.objects.all().delete()
#empty.short_description = "Empty (flush) the table"
AUTOCOMPLETE = 'a'
JSON = 'j'
PJSON = 'p'

class IModelAdmin(DjangoModelAdmin):
    add_undefined_fields = False
    change_form_template = 'admin/change_form_tab.html'
    actions = [ac.mass_update, ac.export_to_csv]

    list_display_rel_links = ()
    cell_filter = ()
    ajax_search_fields = None
    ajax_list_display = None

    def __init__(self, model, admin_site):
        self.ajax_search_fields = self.ajax_search_fields or self.search_fields
        self.ajax_list_display = self.ajax_list_display or self.list_display

        super(IModelAdmin, self).__init__(model, admin_site)
        x = []
        for name in self.cell_filter:
            try:
                f = self.model._meta.get_field(name)
                x.append(name)
            except:
                if hasattr(self, name):
                    x.append(name)
        self.cell_filter = x

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        formfield = super(IModelAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if formfield and db_field.name not in self.raw_id_fields:
            formfield.widget = widgets.RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
        return formfield


    def get_changelist(self, request, **kwargs):
        return IChangeList

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
        flds = set(('pk',) + tuple(self.ajax_list_display))
        qs = self.model.objects.filter(*or_queries).values_list( *flds )
        data = (map(smart_str,record) for record in qs)
        if fmt == AUTOCOMPLETE:
            ret = '\n'.join( "|".join(data) )
        elif fmt == JSON:
            ret = json.dumps( list(data) )
        elif fmt == PJSON:
            qs = self.model.objects.filter(*or_queries).values(*flds)
            ret = json.dumps( list(qs) )
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


