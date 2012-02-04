import copy
import datetime
from django.db.models.base import ModelBase
from django.db.models.loading import get_apps, get_models
from django.views.decorators.csrf import csrf_protect
import os
import django
from django.conf import settings
from django.conf.urls.defaults import url, patterns
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
                   'title' : _("System information"),
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

    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        urlpatterns = patterns('',
                                url(r'^s/format/date/$',
                                    wrap(self.format_date),
                                    name='format_date'),

                                url(r'^s/info/$',
                                    wrap(self.env_info),
                                    name="info"
                                ),
                                url(r'(?P<app_label>.*)/(?P<model_name>.*)/import/(?P<page>\d+)/$',
                                    wrap(self.import_csv),
                                    name="import"
                                ),
        )

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), 'iadmin', 'iadmin'


iservice = IAdminService(django.contrib.admin.site)

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

    def reverse_admin(self, model, view="changelist", args=None):
        """
            return an admin url from the passed model
        :param model: Model instance or class
        :param view: view name as admin convention. (usually "change,changelist,update,history...)
        :param args:  eventually args to pass to reverse function
        :return: url as by reverse
        """
        view = "%s:%s_%s_%s" % (self.name, model._meta.app_label, model._meta.module_name, view)
        url = reverse(view, args=args)
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
                    attrs={'cell_filter' : [f for f in admin_class.list_display if f not in ('__unicode__','__str__')]}
                    self.register(model, type("I%sModelAdmin" % model._meta.module_name, (IModelAdmin, type(admin_class)), attrs), override=True)
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

    def get_templates_for(self, ):
        pass

#    def index(self, request, extra_context=None):
#        """
#        Displays the main admin index page, which lists all of the installed
#        apps that have been registered in this site.
#        """
#        app_dict = {}
#        user = request.user
#
#        if getattr(settings, 'IADMIN_COUNT_ROWS', True):
#            count_models = lambda model: model.objects.all().count()
#        else:
#            count_models = lambda model: ''
#        for model, model_admin in self._registry.items():
#            app_label = model._meta.app_label
#            has_module_perms = user.has_module_perms(app_label)
#
#            if has_module_perms:
#                perms = model_admin.get_model_perms(request)
#
#                # Check whether user has any perm for this module.
#                # If so, add the module to the model_list.
#                if True in perms.values():
#                    model_dict = {
#                        'name': capfirst(model._meta.verbose_name_plural),
#                        'admin_url': mark_safe('%s/%s/' % (app_label, model.__name__.lower())),
#                        'perms': perms,
#                        'count': count_models(model)
#                    }
#                    if app_label in app_dict:
#                        app_dict[app_label]['models'].append(model_dict)
#                    else:
#                        app_dict[app_label] = {
#                            'name': app_label.title(),
#                            'app_url': app_label + '/',
#                            'has_module_perms': has_module_perms,
#                            'models': [model_dict],
#                            }
#
#        # Sort the apps alphabetically.
#        app_list = app_dict.values()
#        app_list.sort(lambda x, y: cmp(x['name'], y['name']))
#
#        # Sort the models alphabetically within each app.
#        for app in app_list:
#            app['models'].sort(lambda x, y: cmp(x['name'], y['name']))
#
#        context = {
#            'title': _('Site administration'),
#            'app_list': app_list,
#            }
#        context.update(extra_context or {})
#        context_instance = template.RequestContext(request, current_app=self.name)
#        return render_to_response(self.index_template or '%s/index.html' % self.template_base_dir,
#            context, context_instance=context_instance)

#    @cache_app_index
#    def app_index(self, request, app_label, extra_context=None):
#        user = request.user
#        has_module_perms = user.has_module_perms(app_label)
#        app_dict = {}
#        if getattr(settings, 'IADMIN_COUNT_ROWS', True):
#            count_models = lambda model: model.objects.all().count()
#        else:
#            count_models = lambda model: ''
#
#        for model, model_admin in self._registry.items():
#            if app_label == model._meta.app_label:
#                if has_module_perms:
#                    perms = model_admin.get_model_perms(request)
#
#                    # Check whether user has any perm for this module.
#                    # If so, add the module to the model_list.
#                    if True in perms.values():
#                        model_dict = {
#                            'name': capfirst(model._meta.verbose_name_plural),
#                            'admin_url': '%s/' % model.__name__.lower(),
#                            'perms': perms,
#                            'count': count_models(model)
#                        }
#                        if app_dict:
#                            app_dict['models'].append(model_dict),
#                        else:
#                            # First time around, now that we know there's
#                            # something to display, add in the necessary meta
#                            # information.
#                            app_dict = {
#                                'name': app_label.title(),
#                                'app_url': '',
#                                'has_module_perms': has_module_perms,
#                                'models': [model_dict],
#                                }
#        if not app_dict:
#            raise http.Http404('The requested admin page does not exist.')
#            # Sort the models alphabetically within each app.
#        app_dict['models'].sort(lambda x, y: cmp(x['name'], y['name']))
#        context = {
#            'title': _('%s administration') % capfirst(app_label),
#            'app_list': [app_dict],
#            'app_label': app_label,
#            }
#        context.update(extra_context or {})
#        context_instance = template.RequestContext(request, current_app=self.name)
#        return render_to_response(self.app_index_template or '%s/app_index.html' % self.template_base_dir, context,
#            context_instance=context_instance)


    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        urlpatterns = []
        urlpatterns.extend(super(IAdminSite, self).get_urls())
        return urlpatterns

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

##
##    def silent_unregister(self, model_or_iterable):
##        """
##        unregister witout raise NotRegistered Exceptior if not already registered
##        """
##        if isinstance(model_or_iterable, ModelBase):
##            model_or_iterable = [model_or_iterable]
##        for model in model_or_iterable:
##            if model in self._registry:
##                del self._registry[model]
#
##    def register_app(self, app, admin_class=None,  override=False ):
##        """
##            register all models of application <app>
##            Note: app must use the syntax `app.models`
##        """
##        from django.db.models.loading import get_models
##
##        if not admin_class:
##            admin_class = IModelAdmin
##
##        for m in get_models(app):
##            self.register(m, admin_class, override=override)
##    register_missing = register_app
#
##class IPublicModelAdmin(IModelAdmin):
##    def has_add_permission(self, request):
##        return True
##
##    def has_change_permission(self, request, obj=None):
##        return True
##
##    def has_delete_permission(self, request, obj=None):
##        return True
#
#
##class IPublicSite(IAdminSite):
##
##    def admin_view(self, view, cacheable=False):
##        def inner(request, *args, **kwargs):
##            if not self.has_permission(request):
##                return self.login(request)
##            return view(request, *args, **kwargs)
##        if not cacheable:
##            inner = never_cache(inner)
##        # We add csrf_protect here so this function can be used as a utility
##        # function for any view, without having to repeat 'csrf_protect'.
##        if not getattr(view, 'csrf_exempt', False):
##            inner = csrf_protect(inner)
##        return update_wrapper(inner, view)
##
##    def has_permission(self, request):
##        """
##        Returns True if the given HttpRequest has permission to view
##        *at least one* page in the admin site.
##        """
##        return request.user.is_active
##
##    def register(self, model_or_iterable, admin_class=None, override=False, **options):
##        if not admin_class:
##            admin_class = IPublicModelAdmin
##
##        super(IPublicSite, self).register(model_or_iterable, admin_class, override, **options)


#def invalidate_index(sender, **kwargs):
#    cache.delete(INDEX_CACHE_KEY)
#
#post_save.connect(invalidate_index)
#post_delete.connect(invalidate_index)
#
site = IAdminSite()


  