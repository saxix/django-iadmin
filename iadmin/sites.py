import copy
import datetime
from django.db.models.base import ModelBase
from django.db.models.loading import get_apps, get_models
from django.template.defaultfilters import capfirst
from django.views.decorators.csrf import csrf_protect
import os
import django
from django.conf import settings
from django.conf.urls import patterns, url, include
from django import http, template
from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save, post_delete
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.functional import update_wrapper
from django.shortcuts import render_to_response
from django.utils import dateformat
from iadmin.options import IModelAdmin
from iadmin.tools import CSVImporter
from django.utils.translation import gettext as _

try:
    from getpass import getuser
except ImportError:
    getuser = lambda: 'info not available'

INDEX_CACHE_KEY = 'admin:admin_index'

def cache_admin(method, key=None):
    entry = key or method.__name__

    def __inner(*args, **kwargs):
        cached = cache.get(entry, None)
        if not cached:
            cached = method(*args, **kwargs)
            cache.set(entry, cached, 3600)
        return cached

    return __inner


def cache_app_index(func):
    def __inner(self, request, app_label, extra_context=None):
        entry = "%s_index" % app_label
        cached = cache.get(entry, None)
        if not cached:
            cached = func(self, request, app_label, extra_context)
            cache.set(entry, cached, -1)
        return cached

    return __inner

__all__ = ['site', 'IAdminSite']

class IAdminService(object):
    def __init__(self, adminsite):
        self.admin_site = adminsite

    def format_date(self, request):
        d = datetime.datetime.now()
        #        return HttpResponse(d.strftime(request.GET.get('fmt', '')))
        return HttpResponse(dateformat.format(d, request.GET.get('fmt', '')))


    def env_info_counters(self, request, export=False):
        app_dict = {}
        for model, model_admin in self.admin_site._registry.items():
            app_label = model._meta.app_label
            info = (app_label, model._meta.module_name)
            model_dict = {
                'name': capfirst(model._meta.verbose_name_plural),
                'perms': model_admin.get_model_perms(request),
                'admin_url': reverse('admin:%s_%s_changelist' % info, current_app=self.admin_site.name),
                'row_count': model.objects.count(),
                }
            if app_label in app_dict:
                app_dict[app_label]['models'].append(model_dict)
            else:
                app_dict[app_label] = {
                    'name': app_label.title(),
                    #                    'app_url': reverse('admin:app_list', kwargs={'app_label': app_label}, current_app=self.name),
                    #                    'has_module_perms': has_module_perms,
                    'models': [model_dict],
                    }

        # Sort the apps alphabetically.
        app_list = app_dict.values()
        app_list.sort(key=lambda x: x['name'])

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])

        context = {
            'title': _('Site administration'),
            'app_list': app_list,
            'STATIC_URL': settings.STATIC_URL,
            }
        return render_to_response(('%s/env_info_counters.html' % self.admin_site.name,
                                   'iadmin/env_info_counters.html'), context)

    def env_info(self, request, export=False):
        def _apps():
            ret = []
            for app_name in settings.INSTALLED_APPS:
                mod = __import__(app_name)
                ver = 'unknown'
                for attr in ('__version__', '__VERSION__', 'VERSION', 'version', 'get_version'):
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

        lib = sorted([str(e) for e in pkg_resources.working_set], lambda x, y: cmp(x.lower(), y.lower()))

        context = {'lib': lib,
                   'curdir': os.path.abspath(os.path.curdir),
                   'os_user': getuser(),
                   'os': os,
                   'title': _("System information"),
                   'sys': {'platform': sys.platform, 'version': sys.version_info, 'os': os.uname(),
                           'django': django.get_version()},
                   'database': settings.DATABASES,
                   'path': sys.path,
                   'apps': _apps()
        }
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)

        return render_to_response(('%s/env_info.html' % self.admin_site.name,
                                   'iadmin/env_info.html'), context, context_instance=context_instance)

    def admin_view(self, view, cacheable=False):
        def inner(request, *args, **kwargs):
            if not self.admin_site.has_permission(request):
                return self.admin_site.login(request)
            return view(request, *args, **kwargs)

        if not getattr(view, 'csrf_exempt', False):
            inner = csrf_protect(inner)
        return update_wrapper(inner, view)

    def import_csv(self, request, app_label, model_name, page, **kwargs):
        return CSVImporter(self, app_label, model_name, page, **kwargs).dispatch(request)

    def admin_shortcut(self, request, content_type_id, object_id):
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get(pk=content_type_id)
        obj = content_type.get_object_for_this_type(pk=object_id)
        view = "%s:%s_%s_change" % (self.admin_site.name, obj._meta.app_label, obj.__class__.__name__.lower())
        url = reverse(view, args=[int(object_id)])
        return HttpResponseRedirect(url)

    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        urlpatterns = patterns('',
            url(r'^s/format/date/$',
                wrap(self.format_date),
                name='format_date'),

            url(r'^s/info/counters/$',
                wrap(self.env_info_counters, True),
                name="info_counters"
            ),
            url(r'^s/info/$',
                wrap(self.env_info, True),
                name="info"
            ),
            url(r'(?P<app_label>.*)/(?P<model_name>.*)/import/(?P<page>\d+)/$',
                wrap(self.import_csv),
                name="import"
            ),
            url(r'^i/(?P<content_type_id>\d+)/(?P<object_id>.+)/$',
                wrap(self.admin_shortcut),
                name='admin_shortcut'),

        )

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), 'iadmin', 'iadmin'


class IAdminSite(AdminSite):
    def __init__(self, name='admin', app_name='admin', template_base_dir='admin'):
        self.template_base_dir = template_base_dir
        return super(IAdminSite, self).__init__(name, app_name)

    def investigate_admin(self, site):
        """
        Register all models registerd int passed AdminSite instance
        :param site: AdminSite instance
        :return: None
        """
        for model, class_admin in site._registry.items():
            self.register(model, type(class_admin))

    def reverse_admin(self, model, view="changelist", args=None, kwargs=None):
        """
            return an admin url from the passed model
        :param model: Model instance or class
        :param view: view name as admin convention. (usually "change,changelist,update,history...)
        :param args:  eventually args to pass to reverse function
        :return: url as by reverse
        """
        view = "%s:%s_%s_%s" % (self.name, model._meta.app_label, model._meta.module_name, view)
        url = reverse(view, args=args, kwargs=kwargs)
        return url

    def register_all(self):
        """
        register all models of all applications
        :return: None
        """
        for app in get_apps():
            for model in get_models(app):
                self.register(model, IModelAdmin)

    def iautodiscover(self):
        self.autodiscover()
        for model, admin_class in self._registry.items():
            try:
                if not issubclass(admin_class.__class__, IModelAdmin):
                    attrs = {}
                    if not hasattr(admin_class, 'cell_filter'):
                        attrs = {'cell_filter': [f for f in admin_class.list_display if f not in ('__unicode__', '__str__')]}
                    self.register(model, type("I%sModelAdmin" % model._meta.module_name, (IModelAdmin, type(admin_class)), attrs),
                        override=True)
            except TypeError, e:
                pass

    def autodiscover(self):
        """
        same as django.admin.autodiscover.
        """
        from django.utils.importlib import import_module
        from django.utils.module_loading import module_has_submodule

        django.contrib.admin.site = self
        django.contrib.admin.ModelAdmin = IModelAdmin

        for app in settings.INSTALLED_APPS:
            mod = import_module(app)
            try:
                before_import_registry = copy.copy(self._registry)
                import_module('%s.admin' % app)
            except BaseException:
                self._registry = before_import_registry
                if module_has_submodule(mod, 'admin'):
                    raise

    def get_urls(self):
        urlpatterns = super(IAdminSite, self).get_urls()
        return iservice.get_urls() + urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name

    def register(self, model_or_iterable, admin_class=None, override=False, **options):
        """
            register a model or an iterable using IModelAdmin
        """
        if not admin_class:
            admin_class = IModelAdmin
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]

        for model in model_or_iterable:
            if model in self._registry:
                if override:
                    self.unregister(model)
                else:
                    continue
            super(IAdminSite, self).register(model, admin_class, **options)

#post_save.connect(invalidate_index)
#post_delete.connect(invalidate_index)
#
isite = site = IAdminSite()
iservice = IAdminService(site)

  