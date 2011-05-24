import datetime
from django.conf import settings
from django.contrib.admin import ModelAdmin as DjangoModelAdmin, TabularInline as DjangoTabularInline
from django.contrib.admin.util import flatten_fieldsets
from django.contrib.admin import helpers
from django.core.exceptions import ValidationError
from django.db.models.fields import AutoField
from django.db import models, transaction
from django import forms
from . import widgets
from django.contrib.admin.widgets import AdminDateWidget
from . import filterspecs
from django.forms.fields import FileField
from django.forms.models import modelform_factory, ModelForm
from django.forms.util import ErrorList
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.functional import curry
from django.utils.safestring import mark_safe
from django.utils import simplejson as json
from iadmin.actions import export_to_csv

__all__ = ['IModelAdmin', 'ITabularInline']

#def empty(modeladmin, request, queryset):
#    modeladmin.model.objects.all().delete()
#empty.short_description = "Empty (flush) the table"

DO_NOT_MASS_UPDATE = 'do_NOT_mass_UPDATE'

class MassUpdateForm(ModelForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    def _clean_fields(self):
        for name, field in self.fields.items():
            value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, FileField):
                    initial = self.initial.get(name, field.initial)
                    value = field.clean(value, initial)
                else:
                    enabler = 'chk_id_%s' % name
                    if self.data.get(enabler, False):
                        value = field.clean(value)
                        self.cleaned_data[name] = value
                    if hasattr(self, 'clean_%s' % name):
                        value = getattr(self, 'clean_%s' % name)()
                        self.cleaned_data[name] = value
            except ValidationError, e:
                self._errors[name] = self.error_class(e.messages)
                if name in self.cleaned_data:
                    del self.cleaned_data[name]

    def _post_clean(self):
        pass

class IModelAdmin(DjangoModelAdmin):
    add_undefined_fields = False
    change_form_template='admin/change_form_tab.html'
    actions = ['mass_update', export_to_csv]
    formfield_overrides = {models.DateField:       {'widget': AdminDateWidget}}

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        formfield = super(IModelAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if formfield and db_field.name not in self.raw_id_fields:
            formfield.widget = widgets.RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
        return formfield


    def mass_update(self, request, queryset):
        Form = self.get_form(request)
        MForm = modelform_factory(self.model, form=MassUpdateForm)
        form = None

        if 'apply' in request.POST:
            form = MForm(request.POST)
            if form.is_valid():
                for record in queryset:
                    for k,v in form.cleaned_data.items():
                        setattr(record,k,v)
                        record.save()
#                messages.error(request, "Error accepting %s (%s)" % (record, str(e)) )
            return HttpResponseRedirect(request.get_full_path())
        else:
            grouped = {}
            initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)}

            for f in self.model._meta.fields:
                grouped[f.name] = []
            for el in queryset.all():
                for f in self.model._meta.fields:
                    if hasattr(el, 'get_%s_display' % f.name):
                        value =  getattr(el, 'get_%s_display' % f.name)()
                    else:
                        value =  getattr(el, f.name)
                    grouped[f.name].append( value )


            for f in self.model._meta.fields:
                initial[f.name] = grouped[f.name][0]
                grouped[f.name] = list(set(grouped[f.name]))


            form = MForm(initial=initial)

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request), {}, [], model_admin=self)
        media = self.media + adminForm.media
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.date) else str(obj)

        return render_to_response('admin/mass_update.html',
                                  RequestContext(request, { 'adminform': adminForm,
                                                            'form': form,
                                                            'grouped': grouped,
                                                            'fieldvalues': json.dumps(grouped, default=dthandler),
                                                            'change': True,
                                                            'is_popup': False,
                                                            'save_as': False,
                                                            'has_delete_permission': False,
                                                            'has_add_permission': False,
                                                            'has_change_permission': True,
                                                            'opts': self.model._meta,
                                                            'app_label': self.model._meta.app_label,
                                                            'action': 'mass_update',
                                                            'media': mark_safe(media),
                                                            'selection': queryset,
                                  }))


    mass_update.short_description = "Mass update"

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


class ITabularInline(DjangoTabularInline):
    template = 'admin/edit_inline/tabular_tab.html'
    add_undefined_fields = False

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        formfield = super(ITabularInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if formfield and db_field.name not in self.raw_id_fields:
            formfield.widget = widgets.RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
        return formfield


