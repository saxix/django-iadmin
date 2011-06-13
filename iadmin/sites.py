import csv
import datetime
import tempfile
import django
from django.conf import settings
from django.conf.urls.defaults import url, patterns
from django.contrib import messages
from django import http, template
from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save, post_delete
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.views.decorators.cache import never_cache
from django.conf.urls.defaults import include
from django.utils import dateformat
import os
from . import options
from iadmin.options import IModelAdmin
from .wizard import ImportForm, csv_processor_factory, set_model_attribute

def cache_admin(method, key=None):
    entry = key or method.__name__
    def __inner(*args, **kwargs):
        cached = cache.get(entry, None)
        if not cached:
            cached = method(*args, **kwargs)
            cache.set(entry, cached, 1)
        return cached
    return __inner

def cache_app_index(func):
    def __inner(self, request, app_label, extra_context=None):
        entry = "%s_index" % app_label
        cached = cache.get(entry, None)
        if not cached:
            cached = func(self, request, app_label, extra_context)
            cache.set(entry, cached, 1)
        return cached
    return __inner

__all__= ['site', 'IAdminSite']

class IAdminSite(AdminSite):
    register_all_models = False

    def index(self, request, extra_context=None):
        """
        Displays the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        app_dict = {}
        user = request.user
        for model, model_admin in self._registry.items():
            app_label = model._meta.app_label
            has_module_perms = user.has_module_perms(app_label)

            if has_module_perms:
                perms = model_admin.get_model_perms(request)

                # Check whether user has any perm for this module.
                # If so, add the module to the model_list.
                if True in perms.values():
                    model_dict = {
                        'name': capfirst(model._meta.verbose_name_plural),
                        'admin_url': mark_safe('%s/%s/' % (app_label, model.__name__.lower())),
                        'perms': perms,
                        'count': model.objects.all().count()
                    }
                    if app_label in app_dict:
                        app_dict[app_label]['models'].append(model_dict)
                    else:
                        app_dict[app_label] = {
                            'name': app_label.title(),
                            'app_url': app_label + '/',
                            'has_module_perms': has_module_perms,
                            'models': [model_dict],
                        }

        # Sort the apps alphabetically.
        app_list = app_dict.values()
        app_list.sort(lambda x, y: cmp(x['name'], y['name']))

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(lambda x, y: cmp(x['name'], y['name']))

        context = {
            'title': _('Site administration'),
            'app_list': app_list,
            'info_url': reverse('admin:admin_env_info', current_app=self.name)
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response(self.index_template or 'admin/index.html', context,
            context_instance=context_instance
        )
    index = never_cache(cache_admin(index, 'admin_index'))

    @cache_app_index
    def app_index(self, request, app_label, extra_context=None):
        user = request.user
        has_module_perms = user.has_module_perms(app_label)
        app_dict = {}
        for model, model_admin in self._registry.items():
            if app_label == model._meta.app_label:
                if has_module_perms:
                    perms = model_admin.get_model_perms(request)

                    # Check whether user has any perm for this module.
                    # If so, add the module to the model_list.
                    if True in perms.values():
                        model_dict = {
                            'name': capfirst(model._meta.verbose_name_plural),
                            'admin_url': '%s/' % model.__name__.lower(),
                            'perms': perms,
                             'count': model.objects.all().count()
                        }
                        if app_dict:
                            app_dict['models'].append(model_dict),
                        else:
                            # First time around, now that we know there's
                            # something to display, add in the necessary meta
                            # information.
                            app_dict = {
                                'name': app_label.title(),
                                'app_url': '',
                                'has_module_perms': has_module_perms,
                                'models': [model_dict],
                            }
        if not app_dict:
            raise http.Http404('The requested admin page does not exist.')
        # Sort the models alphabetically within each app.
        app_dict['models'].sort(lambda x, y: cmp(x['name'], y['name']))
        context = {
            'title': _('%s administration') % capfirst(app_label),
#            'info_url': reverse('admin:admin_env_info', current_app=self.name),
            'app_list': [app_dict],
            'root_path': self.root_path,
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response(self.app_index_template or ('admin/%s/app_index.html' % app_label,
            'admin/app_index.html'), context,
            context_instance=context_instance
        )

    def reverse_model(self, clazz, pk):
        view = "%s:%s_%s_change" % (self.name, clazz._meta.app_label, clazz.__name__.lower())
        url = reverse(view, args=[int(pk)])
        return url

    def format_date(self, request):
        d = datetime.datetime.now()
        return HttpResponse(dateformat.format(d, request.GET.get('fmt','')))

    def env_info(self, request, export=False):
        def _apps():
            ret = []
            for app_name in settings.INSTALLED_APPS:
                mod = __import__(app_name)
                ver = 'unknown'
                for attr in ('__version__', '__VERSION__', 'VERSION', 'VERSION', 'get_version'):
                    try:
                        ver = getattr(mod, attr)
                        if callable(ver):
                            ver = ver()
                        break
                    except AttributeError:
                        pass
                ret.append((app_name, ver))
            return ret

        import pkg_resources, sys
        lib = sorted([str(e) for e in pkg_resources.working_set], lambda x,y: cmp(x.lower(), y.lower()))
        lib.append ('Django %s' % django.get_version())
#        apps = [app for app in get_apps()]

        context = {'lib': lib,
                   'info_url': reverse('admin:admin_env_info', current_app=self.name),
                   'root_path': self.root_path or '/'+self.name + '/',
                   'path': sys.path,
                   'apps': _apps()
        }
        context_instance = template.RequestContext(request, current_app=self.name)
        if export:
            response = HttpResponse(mimetype='text/plain')
            response['Content-Disposition'] = 'attachment;filename="environment.txt"'
            response.content = '\n'.join([str(e) for e in lib])
            return response

        return render_to_response('admin/env_info.html', context, context_instance=context_instance )

    def _import_csv_1(self, request, app=None, model=None, temp_file_name=None):
        context = { 'app_label': app or '',
                    'model': model or '',
                    'root_path': self.root_path or ''
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
        return render_to_response('admin/import_csv.html', context, context_instance=context_instance )

    
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
        return render_to_response('admin/import_csv.html', context, context_instance=context_instance )


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
                return self.admin_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)



        urlpatterns = patterns('',
                                url(r'^s/format/date/$',
                                    wrap(self.format_date),
                                    name='format_date'),

                                url(r'^r/info/$',
                                    wrap(self.env_info),
                                    name='admin_env_info'),

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

        from iadmin.fm.filemanager import FileManager
        filemanager = FileManager(self)
        urlpatterns += patterns('', url(r'^i/fm/', include( filemanager.urls )))

        urlpatterns += super(IAdminSite, self).get_urls()
        return urlpatterns

    def register(self, model_or_iterable, admin_class=None, **options):
        if not admin_class:
            admin_class = IModelAdmin
        super(IAdminSite, self).register(model_or_iterable, admin_class, **options)


    def register_missing(self, app):
        from django.db.models.loading import get_models
        [self.register(m, options.IModelAdmin) for m in get_models(app) if not m in self._registry]

def invalidate_index(sender, **kwargs):
    cache.set('admin_index', None, 0)
    #expire_view_cache('admin_index')

post_save.connect(invalidate_index)
post_delete.connect(invalidate_index)

django.contrib.admin.site = django.contrib.admin.sites.site = site = IAdminSite()

  