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