# -*- coding: utf-8 -*-
'''
Created on 28/ott/2009

@author: sax
'''
from collections import defaultdict
import datetime
from django.db.models.aggregates import Count
from django.db.models.fields.related import ForeignKey
from django.utils import simplejson as json
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import FileField, ModelForm
from django.forms.models import modelform_factory
from django.http import HttpResponse, HttpResponseRedirect
import csv
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import force_unicode, smart_str
from django.utils.safestring import mark_safe
from django.contrib.admin import helpers
from django.utils import formats
from django.utils import dateformat
from iadmin.plugins.csv.utils import graph_form_factory

__all__ = ('export_to_csv', 'mass_update')

delimiters = ",;|:"
quotes = "'\"`"
escapechars = " \\"

class CSVOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    header = forms.BooleanField(required=False)
    delimiter = forms.ChoiceField(choices=zip(delimiters, delimiters))
    quotechar = forms.ChoiceField(choices=zip(quotes, quotes))
    quoting = forms.ChoiceField(
        choices=((csv.QUOTE_ALL, 'All'), (csv.QUOTE_MINIMAL, 'Minimal'), (csv.QUOTE_NONE, 'None'),
                     (csv.QUOTE_NONNUMERIC, 'Non Numeric')))

    escapechar = forms.ChoiceField(choices=(('', ''), ('\\', '\\')), required=False)
    datetime_format = forms.CharField(initial=formats.get_format('DATETIME_FORMAT'))
    date_format = forms.CharField(initial=formats.get_format('DATE_FORMAT'))
    time_format = forms.CharField(initial=formats.get_format('TIME_FORMAT'))
    columns = forms.MultipleChoiceField()


def export_to_csv(modeladmin, request, queryset):
    """
        export a queryset to csv file
    """
    cols = [(f.name, f.verbose_name) for f in queryset.model._meta.fields]
    initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME), 'quotechar': '"',
               'columns': [x for x, v in cols], 'quoting': csv.QUOTE_ALL, 'delimiter': ';', 'escapechar': '\\', }

    if 'apply' in request.POST:
        form = CSVOptions(request.POST)
        form.fields['columns'].choices = cols
        if form.is_valid():
            response = HttpResponse(mimetype='text/csv')
            response[
            'Content-Disposition'] = 'attachment;filename="%s.csv"' % queryset.model._meta.verbose_name_plural.lower()
            try:
                writer = csv.writer(response,
                                    escapechar=str(form.cleaned_data['escapechar']),
                                    delimiter=str(form.cleaned_data['delimiter']),
                                    quotechar=str(form.cleaned_data['quotechar']),
                                    quoting=int(form.cleaned_data['quoting']))
                if form.cleaned_data.get('header', False):
                    writer.writerow([f for f in form.cleaned_data['columns']])

                for obj in queryset:
                    row = []
                    for fieldname in form.cleaned_data['columns']:
                        if hasattr(obj, 'get_%s_display' % fieldname):
                            value = getattr(obj, 'get_%s_display' % fieldname)()
                        else:
                            value = getattr(obj, fieldname)
                        if isinstance(value, datetime.datetime):
                            value = dateformat.format(value, form.cleaned_data['datetime_format'])
                        elif isinstance(value, datetime.date):
                            value = dateformat.format(value, form.cleaned_data['date_format'])
                        elif isinstance(value, datetime.time):
                            value = dateformat.format(value, form.cleaned_data['time_format'])
                        row.append(smart_str(value))
                    writer.writerow(row)
            except Exception, e:
                messages.error(request, "Error: (%s)" % str(e))
            else:
                return response
    else:
        form = CSVOptions(initial=initial)
        form.fields['columns'].choices = cols

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    return render_to_response('iadmin/export_csv.html',
                              RequestContext(request, {'adminform': adminForm,
                                                       'form': form,
                                                       'change': True,
                                                       'is_popup': False,
                                                       'save_as': False,
                                                       'has_delete_permission': False,
                                                       'has_add_permission': False,
                                                       'has_change_permission': True,
                                                       'opts': queryset.model._meta,
                                                       'app_label': queryset.model._meta.app_label,
                                                       'action': 'export_to_csv',
                                                       'media': mark_safe(media),
                                                       }))


DO_NOT_MASS_UPDATE = 'do_NOT_mass_UPDATE'

class MassUpdateForm(ModelForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    _validate = forms.BooleanField(label='Validate', help_text="if checked use obj.save() instead of manager.update()")

    def _clean_fields(self):
        for name, field in self.fields.items():
            value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, FileField):
                    initial = self.initial.get(name, field.initial)
                    field.clean(value, initial)
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

    def config_fields(self):
        """
        Returns a list of BoundField objects that aren't hidden fields.
        The opposite of the hidden_fields() method.
        """
        return [field for field in self if not field.is_hidden and field.name.startswith('_')]

    def model_fields(self):
        """
        Returns a list of BoundField objects that aren't hidden fields.
        The opposite of the hidden_fields() method.
        """
        return [field for field in self if not field.name.startswith('_')]

def mass_update(modeladmin, request, queryset):
    """
        mass update queryset
    """
    MForm = modelform_factory(modeladmin.model, form=MassUpdateForm)

    if 'apply' in request.POST:
        form = MForm(request.POST)
        if form.is_valid():
            done = 0
            if form.cleaned_data.get('_validate', False):
                for record in queryset:
                    for k, v in form.cleaned_data.items():
                        setattr(record, k, v)
                        record.save()
                        done += 1
                messages.info(request, "Updated %s records" % done)
            else:
                values = {}
                for k, v in form.cleaned_data.items():
                    if k not in ['_selected_action', '_validate']:
                        values[k]=v
                queryset.update(**values)

        return HttpResponseRedirect(request.get_full_path())
    else:
        grouped = defaultdict(lambda: [])
        initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)}

        for el in queryset.all()[:10]:
            for f in modeladmin.model._meta.fields:
                if hasattr(f, 'flatchoices') and f.flatchoices:
                    grouped[f.name] = dict(getattr(f, 'flatchoices')).values()
                elif hasattr(f, 'choices') and f.choices:
                    grouped[f.name] = dict(getattr(f, 'choices')).values()
                else:
                    value = getattr(el, f.name)
                    if value is not None and value not in grouped[f.name]:
                        grouped[f.name].append(value)
                initial[f.name] = initial.get(f.name, value)

        form = MForm(initial=initial)



    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.date) else str(obj)

    return render_to_response('iadmin/mass_update.html',
                              RequestContext(request, {'adminform': adminForm,
                                                       'form': form,
                                                       'grouped': grouped,
                                                       'fieldvalues': json.dumps(grouped, default=dthandler),
                                                       'change': True,
                                                       'is_popup': False,
                                                       'save_as': False,
                                                       'has_delete_permission': False,
                                                       'has_add_permission': False,
                                                       'has_change_permission': True,
                                                       'opts': modeladmin.model._meta,
                                                       'app_label': modeladmin.model._meta.app_label,
                                                       'action': 'mass_update',
                                                       'media': mark_safe(media),
                                                       'selection': queryset,
                                                       }))


mass_update.short_description = "Mass update"

def export_as_json(modeladmin, request, queryset):
    records = []
    for obj in queryset:
        records.append(obj)
    import django.core.serializers as ser

    json = ser.get_serializer('json')()
    ret = json.serialize(records, use_natural_keys=True, indent=2)
    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment;filename="%s.json"' % queryset.model._meta.verbose_name_plural.lower()
    response.content = ret
    return response

export_as_json.short_description = "Export as fixture"


def graph_queryset(modeladmin, request, queryset):
    MForm = graph_form_factory(modeladmin.model)

    graph_type = table = data_labels = data = total = None
    if 'apply' in request.POST:
        form = MForm(request.POST)
        if form.is_valid():
            try:
                x = form.cleaned_data['axes_x']
    #            y = form.cleaned_data['axes_y']
                graph_type = form.cleaned_data['graph_type']
                field, model, direct, m2m = modeladmin.model._meta.get_field_by_name(x)
                cc = queryset.values_list(x).annotate(Count(x)).order_by()
                if isinstance(field, ForeignKey):
                    data_labels = []
                    for value, cnt in cc:
                        data_labels.append(str(field.rel.to.objects.get(pk=value)))
                elif hasattr(modeladmin.model, 'get_%s_display' % field.name):
                    data_labels = []
                    for value, cnt in cc:
                        data_labels.append(force_unicode(dict(field.flatchoices).get(value, value), strings_only=True))
                else:
                    data_labels = [l for l, v in cc]
                data = [v for l, v in cc]
                table = zip(data_labels, data)
            except Exception, e:
                messages.error(request, 'Unable to produce valid data: %s' % str(e))
    elif request.method == 'POST':
        total = queryset.all().count()
        initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
                   'select_across': request.POST.get('select_across', 0)}
        form = MForm(initial=initial)
    else:
        initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
                   'select_across': request.POST.get('select_across', 0)}
        form = MForm(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media

    ctx = {'adminform': adminForm,
           'action': 'graph_queryset',
           'opts': modeladmin.model._meta,
           'app_label': queryset.model._meta.app_label,

           'as_json': json.dumps(table),
           'graph_type': graph_type,
           }
    return render_to_response('iadmin/charts/model.html', RequestContext(request, ctx))

graph_queryset.short_description = "Graph selected records"