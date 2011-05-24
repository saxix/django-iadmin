# -*- coding: utf-8 -*-
'''
Created on 28/ott/2009

@author: sax
'''
import datetime
from django import forms
from django.contrib import messages
from django.http import HttpResponse
import csv
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.formats import date_format
from django.utils.safestring import mark_safe
from django.contrib.admin import helpers
from django.utils import formats
from django.utils import dateformat, numberformat, datetime_safe

delimiters=",;|:"
quotes="'\"`"
class CSVOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    header = forms.BooleanField(required=False)
    delimiter = forms.ChoiceField(choices=zip(delimiters, delimiters) )
    quotechar = forms.ChoiceField(choices=zip(quotes,quotes))
    quoting = forms.ChoiceField(
        choices=((csv.QUOTE_ALL, 'All'), (csv.QUOTE_MINIMAL, 'Minimal'), (csv.QUOTE_NONE, 'None'),
                 (csv.QUOTE_NONNUMERIC, 'Non Numeric')))
    

    datetime_format = forms.CharField(initial=formats.get_format('DATETIME_FORMAT'))
    date_format = forms.CharField(initial=formats.get_format('DATE_FORMAT'))
    time_format = forms.CharField(initial=formats.get_format('TIME_FORMAT'))
    columns = forms.MultipleChoiceField()

def export_to_csv(modeladmin, request, queryset):
    cols = [(f.name, f.verbose_name) for f in modeladmin.model._meta.fields]
    initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME),
               'columns': cols}
    if 'apply' in request.POST:
        form = CSVOptions(request.POST)
        form.fields['columns'].choices = cols
        if form.is_valid():
#            response = HttpResponse(mimetype='text/plain')
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment;filename="export.csv"'
            try:
                writer = csv.writer(response,
                                    delimiter=str(form.cleaned_data['delimiter']),
                                    quotechar=str(form.cleaned_data['quotechar']),
                                    quoting=int(form.cleaned_data['quoting']))
                if form.cleaned_data.get('header', False) :
                    writer.writerow( [ f for f in form.cleaned_data['columns']])

                for obj in queryset:
                    row = []
                    for fieldname in form.cleaned_data['columns']:
                        if hasattr(obj, 'get_%s_display' % fieldname):
                            value = getattr(obj, 'get_%s_display' % fieldname)()
                        else:
                            value = getattr(obj, fieldname)
                        if isinstance(value, datetime.datetime):
                            value =  dateformat.format(value, form.cleaned_data['datetime_format'] )
                        elif isinstance(value, datetime.date):
                            value =  dateformat.format(value, form.cleaned_data['date_format'] )
                        elif isinstance(value, datetime.time):
                            value =  dateformat.format(value, form.cleaned_data['time_format'] )
                        row.append(value)
                    writer.writerow(row)
            except AttributeError, e:
                messages.error(request, "Error accepting %s (%s)" % ('', str(e)) )
            else:
                return response
    else:
        form = CSVOptions(initial=initial)
        form.fields['columns'].choices = cols

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    return render_to_response('admin/export_csv.html',
                          RequestContext(request, { 'adminform': adminForm,
                                                    'form': form,
                                                    'change': True,
                                                    'is_popup': False,
                                                    'save_as': False,
                                                    'has_delete_permission': False,
                                                    'has_add_permission': False,
                                                    'has_change_permission': True,
                                                    'opts': modeladmin.model._meta,
                                                    'app_label': modeladmin.model._meta.app_label,
                                                    'action': 'export_to_csv',
                                                    'media': mark_safe(media),
                          }))