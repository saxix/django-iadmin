from django.conf import settings
from django.contrib.admin import ModelAdmin as DjangoModelAdmin, TabularInline as DjangoTabularInline
from django.contrib.admin.util import flatten_fieldsets
from django.db.models.fields import AutoField
from . import widgets


__all__ = ['IModelAdmin', 'ITabularInline']


class IModelAdmin(DjangoModelAdmin):
    add_undefined_fields = False
    change_form_template='admin/change_form_tab.html'

    def __init__(self, model, admin_site):
        super(IModelAdmin, self).__init__(model, admin_site)
    #        if not 'iadmin' in settings.INSTALLED_APPS:
#            raise Exception('Please add iadmin to your INSTALLED_APPS')

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        formfield = super(IModelAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if formfield and db_field.name not in self.raw_id_fields:
            formfield.widget = widgets.RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
        return formfield

    def _declared_fieldsets(self):
        # overriden to handle `add_undefined_fields`
        if self.fieldsets:
            if self.add_undefined_fields:
                def _valid(field):
                    return field.editable and type(field) not in (AutoField, ) and '_ptr' not in field.name

                flds = list(self.fieldsets)
                fieldset_fields = flatten_fieldsets(self.fieldsets)
                alls = [f.name for f in self.model._meta.fields if _valid(f)]
                missing_fields = [f for f in alls if f not in fieldset_fields ]
                flds.append(('Other', {'fields': missing_fields, 'classes': ('collapse',),},))
                return flds
            else:
                return self.fieldsets
        elif self.fields:
            return [(None, {'fields': self.fields})]
        return None
    declared_fieldsets = property(_declared_fieldsets)

    def change_view(self, request, object_id, extra_context=None):
        return super(IModelAdmin, self).change_view(request, object_id, extra_context)


#    def response_change(self, request, obj):
#
#        ret = super(IModelAdmin, self).response_change(request, obj)
#        if request.method == 'POST':
#            ret.set_cookie('selected_tab', request.POST.get('selected_tab', 0))
#        return ret

#    def change_view(self, request, object_id, extra_context=None):
#        if request.method == 'POST':
#            s = request.POST.get('selected_tab', 0)
#            assert s > 0
#        extra_context = {'selected_tab' : request.POST.get('selected_tab', 0)}
##        raise Exception(extra_context)
#        return super(IModelAdmin, self).change_view(request, object_id, extra_context)
#
#    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
#        ret =  super(IModelAdmin, self).render_change_form(request, context, add, change, form_url, obj)
#        if request.method == 'POST':
#            ret.set_cookie('selected_tab', request.POST.get('selected_tab', 0))
#        return ret


class ITabularInline(DjangoTabularInline):
    template = 'admin/edit_inline/tabular_tab.html'
    add_undefined_fields = False

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        formfield = super(ITabularInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if formfield and db_field.name not in self.raw_id_fields:
            formfield.widget = widgets.RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
        return formfield
