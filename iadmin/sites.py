
import datetime
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
from django.views.decorators.cache import never_cache, cache_page, cache_control
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
    
INDEX_CACHE_KEY = 'iadmin:admin_index'
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

__all__= ['site', 'IAdminSite']

class IAdminSite(AdminSite):
    register_all_models = False
    plugins = [CSVImporter, FileManager]


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
            'info_url': reverse('admin:admin_env_info', current_app=self.name)
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response(self.index_template or 'iadmin/index.html', context,
            context_instance=context_instance
        )
    index = never_cache(cache_admin(index, INDEX_CACHE_KEY))

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
#            'info_url': reverse('admin:admin_env_info', current_app=self.name),
            'app_list': [app_dict],
            'app_label': app_label,
            'root_path': self.root_path,
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response(self.app_index_template or ('admin/%s/app_index.html' % app_label,
            'iadmin/app_index.html'), context,
            context_instance=context_instance
        )

    def admin_shortcut(self, request, content_type_id, object_id):
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get(pk=content_type_id)
        obj = content_type.get_object_for_this_type(pk=object_id)
        view = "%s:%s_%s_change" % (self.name, obj._meta.app_label, obj.__class__.__name__.lower())
        url = reverse(view, args=[int(object_id)])
        return HttpResponseRedirect( url )

    def reverse_model(self, clazz, pk):
        """
          returns the Admin view to the change page for the passed object
        """
        view = "%s:%s_%s_change" % (self.name, clazz._meta.app_label, clazz.__name__.lower())
        url = reverse(view, args=[int(pk)])
        return url

    def link_to_model(self, obj, label=None):
        if not obj:
            return ''
        url = self.reverse_model(obj.__class__, obj.pk)
        return '&nbsp;<span class="linktomodel"><a href="%s"><img src="%siadmin/img/link.png"/></a></span>' % (url, settings.STATIC_URL)

    _link_to_model = link_to_model

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
                   'curdir': os.path.abspath( os.path.curdir),
                   'user': getuser(),
                   'os': os,
                   'sys': {'platform':sys.platform, 'version': sys.version_info, 'os':os.uname()},
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

        return render_to_response('iadmin/env_info.html', context, context_instance=context_instance )
    
    def reverse_url(self, request, url_name):

        # Turn querystring into an array of couplets (2x list)
        # arg_couplets = [ ('key', 'value'), ('key', 'value') ]
        arg_couplets = request.REQUEST.items()

        # Sort by keys
        arg_couplets.sort(lambda x,y: cmp(x[0], y[0]))

        # Collapse list into just the values
        args = [c[1] for c in arg_couplets]

        try:
            if args:
                return HttpResponse(reverse('%s:%s' % (self.name, url_name), args=args))
            else:
                return HttpResponse(reverse('%s:%s' % (self.name, url_name)))
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
                                    name='admin_env_info'),

                                url(r'^i/reverse/(.*)/$',
                                    wrap(self.reverse_url),
                                    name='reverse_url'),

                                url(r'^i/(?P<content_type_id>\d+)/(?P<object_id>.+)/$',
                                    wrap(self.admin_shortcut),
                                    name='admin_shortcut'),
                                url(r'^i/nojs/', 'iadmin.views.nojs'),
                                )

        for PluginClass in self.plugins:
            plugin =  PluginClass(self)
            urlpatterns += patterns('', url(r'^i/%s/' % plugin.__class__.__name__.lower(), include( plugin.urls )))

        urlpatterns += super(IAdminSite, self).get_urls()
        return urlpatterns

    def register(self, model_or_iterable, admin_class=None, **options):
        """
            register a model or an iterable using IModelAdmin
        """
        if not admin_class:
            admin_class = IModelAdmin
        super(IAdminSite, self).register(model_or_iterable, admin_class, **options)

    def silent_unregister(self, model_or_iterable):
        """
        unregister witout raise NotRegistered Exceptior if not already registered
        """
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model in self._registry:
                del self._registry[model]

    def register_app(self, app):
        """
            register all models of application <app>
            Note: app must use the syntax `app.models`
        """
        from django.db.models.loading import get_models
        for m in get_models(app):
            if not m in self._registry:
                self.register(m, IModelAdmin)

    register_missing = register_app

def invalidate_index(sender, **kwargs):
    cache.delete(INDEX_CACHE_KEY)

post_save.connect(invalidate_index)
post_delete.connect(invalidate_index)

site = IAdminSite()


  