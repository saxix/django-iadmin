import csv
from functools import update_wrapper
from django import template
from django.conf.urls.defaults import url, patterns
import tempfile
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
import os
from iadmin.plugins import IAdminPlugin
from .utils import set_model_attribute, ImportForm, csv_processor_factory


class CSVImporter(IAdminPlugin):
    def _import_csv_1(self, request, app=None, model=None, temp_file_name=None):
        context = { 'app_label': app or '',
                    'model': model or '',
                    'root_path': self.admin_site.root_path or ''
        }
        if request.method == 'POST':
            form = ImportForm(app, model, request.POST, request.FILES)
            if form.is_valid():
                file = request.FILES['csv']

                fd = open(temp_file_name, 'wb')
                for chunk in file.chunks():
                    fd.write(chunk)
                fd.close()
                messages.error(request, temp_file_name)
                app_name, model_name = form.cleaned_data['model'].split(':')
                url = reverse('%s:model_import_csv' % self.name, kwargs={'app': app_name, 'model':model_name, 'page':2})
                return HttpResponseRedirect( url )
        else:
            form = ImportForm(app, model, initial={'page': 1})

        context.update({'page': 1,
                            'form': form,
                            })
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response('iadmin/import_csv.html', context, context_instance=context_instance )


    def _import_csv_2(self, request, app_name=None, model_name=None, temp_file_name=None):
        try:
            Form = csv_processor_factory(app_name, model_name, temp_file_name)
        except IOError, e:
            messages.error(request, str(e))
            return HttpResponseRedirect('/admin/%s/%s/import/2' % (app_name, model_name))

        if request.method == 'POST':
            form = Form(request.POST, request.FILES)
            if form.is_valid():
                inserted, updated = 0, 0
                fd = open( form._filename, 'r')
                reader = csv.reader(fd, form._dialect)
                if form.cleaned_data.get('header', False):
                    reader.next()
                for row in reader:
                    mapping = {}
                    keys = {}
                    for i, cell in enumerate(row):
                        field = form.cleaned_data['col_%s' % i]
                        key = form.cleaned_data['key_%s' % i]
                        rex = form.cleaned_data['rex_%s' % i]
                        if key:
                            keys[field] = cell
                        elif field:
                            mapping[field] = cell
                    if keys:
                        obj, is_new = form._model.objects.get_or_create(**keys)
                    else:
                        obj = form._model()
                    for f,v in mapping.items():
                        set_model_attribute(obj, f, v, rex)
                    obj.save()
                    updated += 1
                messages.info(request, '%s records updated' % updated )
        else:
            form = Form()

        context = {'page': 2,
                   'form':form,
                   'current_app': self.name,
                   'app_label': app_name,
                   'sample': form._head(),
                   'model': model_name,
        }
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response('iadmin/import_csv.html', context, context_instance=context_instance )


    def import_csv(self, request, page=1, app=None, model=None):
            temp_file_name = os.path.join(tempfile.gettempdir(), 'iadmin_import_%s.temp~' % request.user.username)
            if int(page) == 1:
                return self._import_csv_1(request, app, model, temp_file_name = temp_file_name)
            elif int(page) == 2:
                return self._import_csv_2(request, app, model, temp_file_name = temp_file_name)
            raise Exception( page)

    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        return patterns('',
                                url(r'^import/1$',
                                    wrap(self.import_csv),
                                    name='import_csv'),

                                url(r'^(?P<app>\w+)/(?P<model>\w+)/import/(?P<page>\d)',
                                    wrap(self.import_csv),
                                    name='model_import_csv'),

                                url(r'^(?P<app>\w+)/import/(?P<page>\d)',
                                    wrap(self.import_csv),
                                    name='app_import_csv'),
                                )