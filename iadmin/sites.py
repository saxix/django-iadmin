import datetime
from django.contrib.admin.options import ModelAdmin
from django.contrib.admin.util import quote
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
import os
import django
from django.conf import settings
from django.conf.urls.defaults import url, patterns
from django import http, template
from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models.base import ModelBase
from django.db.models.signals import post_save, post_delete
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.conf.urls.defaults import include
from django.utils import dateformat
from .options import IModelAdmin
#from .wizard import ImportForm, csv_processor_factory, set_model_attribute
from iadmin.plugins import FileManager, CSVImporter
from iadmin.conf import config

try:
    from getpass import getuser
except ImportError:
    getuser = lambda : 'info not available'

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

class IAdminSite(AdminSite):
    register_all_models = False
    plugins = [CSVImporter, FileManager]

    def autodiscover(self):
        from django.utils.importlib import import_module
        for app in settings.INSTALLED_APPS:
            try:
                django.contrib.admin.sites.site, bak = self, django.contrib.admin.site
                mod = import_module(app)
                # Attempt to import the app's admin module.
                try:
                    before_import_registry = copy.copy(django.contrib.admin.site._registry)
                    import_module('%s.%s' % (app, module) )
                except:
                    # Reset the model registry to the state before the last import as
                    # this import will have to reoccur on the next request and this
                    # could raise NotRegistered and AlreadyRegistered exceptions
                    # (see #8245).
                    selected_site._registry = before_import_registry

                    # Decide whether to bubble up this error. If the app just
                    # doesn't have an admin module, we can ignore the error
                    # attempting to import it, otherwise we want it to bubble up.
                    if module_has_submodule(mod, 'admin'):
                        raise
            finally:
                django.contrib.admin.sites.site =  bak

    def index(self, request, extra_context=None):
        """
        Displays the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        app_dict = {}
        user = request.user

        if config.count_rows:
            count_models = lambda model: model.objects.all().count()
        else:
            count_models = lambda model: ''
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
                        'count': count_models(model)
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
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response(self.index_template or
                                  (
#                                      'iadmin/index.html',
                                   'admin/index.html',
                                      ), context, context_instance=context_instance)


    #    index = never_cache(cache_admin(index, INDEX_CACHE_KEY))

    @cache_app_index
    def app_index(self, request, app_label, extra_context=None):
        user = request.user
        has_module_perms = user.has_module_perms(app_label)
        app_dict = {}
        if config.count_rows:
            count_models = lambda model: model.objects.all().count()
        else:
            count_models = lambda model: ''

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
                            'count': count_models(model)
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
            'app_list': [app_dict],
            'app_label': app_label,
            }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response(self.app_index_template or
                                  (
#                                    'iadmin/app_index.html',
                                    'admin/app_index.html',), context,
                                  context_instance=context_instance
        )

    def admin_shortcut(self, request, content_type_id, object_id):
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get(pk=content_type_id)
        obj = content_type.get_object_for_this_type(pk=object_id)
        view = "%s:%s_%s_change" % (self.app_name, obj._meta.app_label, obj.__class__.__name__.lower())
        url = reverse(view, args=[int(object_id)])
        return HttpResponseRedirect(url)

    def reverse_model(self, clazz, pk):
        """
          returns the Admin view to the change page for the passed object
        """
        view = "%s:%s_%s_change" % (self.app_name, clazz._meta.app_label, clazz.__name__.lower())
        url = reverse(view, args=[int(pk)])
        return url

    def format_date(self, request):
        d = datetime.datetime.now()
        return HttpResponse(dateformat.format(d, request.GET.get('fmt', '')))

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

        lib = sorted([str(e) for e in pkg_resources.working_set], lambda x, y: cmp(x.lower(), y.lower()))

        context = {'lib': lib,
                   'curdir': os.path.abspath(os.path.curdir),
                   'os_user': getuser(),
                   'os': os,
                   'sys': {'platform': sys.platform, 'version': sys.version_info, 'os': os.uname(),
                           'django': django.get_version()},
                   'path': sys.path,
                   'apps': _apps()
        }
        context_instance = template.RequestContext(request, current_app=self.name)

        return render_to_response(('%s/env_info.html' % self.name,
                                   'iadmin/env_info.html'), context, context_instance=context_instance)

    def reverse_url(self, request, url_name):
        # Turn querystring into an array of couplets (2x list)
        # arg_couplets = [ ('key', 'value'), ('key', 'value') ]
        arg_couplets = request.REQUEST.items()

        # Sort by keys
        arg_couplets.sort(lambda x, y: cmp(x[0], y[0]))

        # Collapse list into just the values
        args = [c[1] for c in arg_couplets]

        try:
            if args:
                return HttpResponse(reverse('%s:%s' % (self.app_name, url_name), args=args))
            else:
                return HttpResponse(reverse('%s:%s' % (self.app_name, url_name)))
        except NoReverseMatch, e:
            return HttpResponse(str(e))

    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        urlpatterns = patterns('',
                               url(r'^i/format/date/$',
                                   wrap(self.format_date),
                                   name='format_date'),

                               url(r'^i/info/$',
                                   wrap(self.env_info),
                                   name='iadmin.info'),

                               url(r'^i/reverse/(.*)/$',
                                   wrap(self.reverse_url),
                                   name='reverse_url'),

                               url(r'^i/(?P<content_type_id>\d+)/(?P<object_id>.+)/$',
                                   wrap(self.admin_shortcut),
                                   name='admin_shortcut'),
                               url(r'^i/nojs/', 'iadmin.views.nojs'),
                               )

        for PluginClass in self.plugins:
            plugin = PluginClass(self)
            urlpatterns += patterns('', url(r'^i/%s/' % plugin.__class__.__name__.lower(), include(plugin.urls)))

        urlpatterns += super(IAdminSite, self).get_urls()
        return urlpatterns

#    def copy_registry(self, other):
#        for model, a in other._registry.items():
#            self.register(model, a.__class__)

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

    def silent_unregister(self, model_or_iterable):
        """
        unregister witout raise NotRegistered Exceptior if not already registered
        """
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model in self._registry:
                del self._registry[model]

#    def register_app(self, app, admin_class=None,  override=False ):
#        """
#            register all models of application <app>
#            Note: app must use the syntax `app.models`
#        """
#        from django.db.models.loading import get_models
#
#        if not admin_class:
#            admin_class = IModelAdmin
#
#        for m in get_models(app):
#            self.register(m, admin_class, override=override)
#    register_missing = register_app

class IPublicModelAdmin(IModelAdmin):
    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


class IPublicSite(IAdminSite):

    def admin_view(self, view, cacheable=False):
        def inner(request, *args, **kwargs):
            if not self.has_permission(request):
                return self.login(request)
            return view(request, *args, **kwargs)
        if not cacheable:
            inner = never_cache(inner)
        # We add csrf_protect here so this function can be used as a utility
        # function for any view, without having to repeat 'csrf_protect'.
        if not getattr(view, 'csrf_exempt', False):
            inner = csrf_protect(inner)
        return update_wrapper(inner, view)

    def has_permission(self, request):
        """
        Returns True if the given HttpRequest has permission to view
        *at least one* page in the admin site.
        """
        return request.user.is_active

    def register(self, model_or_iterable, admin_class=None, override=False, **options):
        if not admin_class:
            admin_class = IPublicModelAdmin

        super(IPublicSite, self).register(model_or_iterable, admin_class, override, **options)


def invalidate_index(sender, **kwargs):
    cache.delete(INDEX_CACHE_KEY)

post_save.connect(invalidate_index)
post_delete.connect(invalidate_index)

site = IAdminSite()


  