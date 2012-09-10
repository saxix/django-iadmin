from django.contrib.admin.options import ModelAdmin
import os
import copy
import datetime
import django
from django.conf import settings
from django.conf.urls import patterns, url
from django import http, template
from django.contrib.admin.sites import AdminSite, AlreadyRegistered
from django.core.cache import cache
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db.models.base import ModelBase
from django.db.models.loading import get_apps, get_models
from django.template.defaultfilters import capfirst
from django.template.response import TemplateResponse
from django.views.decorators.cache import never_cache
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.utils import dateformat
from django.utils.functional import update_wrapper
from django.utils.translation import ugettext_lazy as _

from iadmin.options import IModelAdmin, IModelAdminMixin
from iadmin.tools import CSVImporter
import logging

try:
    from getpass import getuser
except ImportError:
    getuser = lambda: 'info not available'

#INDEX_CACHE_KEY = 'admin:admin_index'

#def cache_admin(method, key=None):
#    entry = key or method.__name__
#
#    def __inner(*args, **kwargs):
#        cached = cache.get(entry, None)
#        if not cached:
#            cached = method(*args, **kwargs)
#            cache.set(entry, cached, 3600)
#        return cached
#
#    return __inner
#
#
#def cache_app_index(func):
#    def __inner(self, request, app_label, extra_context=None):
#        entry = "%s_index" % app_label
#        cached = cache.get(entry, None)
#        if not cached:
#            cached = func(self, request, app_label, extra_context)
#            cache.set(entry, cached, -1)
#        return cached
#
#    return __inner

__all__ = ['site', 'IAdminSite']

class IAdminService(object):
    def __init__(self, adminsite):
        self.admin_site = adminsite


class IProxy(object):
    def __enter__(self):
        import iadmin.proxy

        self.backup, django.contrib.admin.site = django.contrib.admin.site, iadmin.proxy.site

    def __exit__( self, type, value, tb ):
        django.contrib.admin.site = self.backup


class IAdminSite(AdminSite):
    def __init__(self, name='iadmin', app_name='iadmin', template_prefix='iadmin'):
        self.template_prefix = template_prefix or app_name
        super(IAdminSite, self).__init__(name, app_name)
        self._global_actions = self._actions.copy()

    @property
    def password_change_template(self):
        return '%s/registration/password_change_form.html' % self.template_prefix

    def get_template(self, name):
        return '%s/%s' % (self.template_prefix, name)

    @never_cache
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
                    info = (self.app_name, app_label, model._meta.module_name)
                    model_dict = {
                        'name': capfirst(model._meta.verbose_name_plural),
                        'perms': perms,
                        }
                    if perms.get('view', False):
                        try:
                            model_dict['admin_url'] = reverse('%s:%s_%s_changelist' % info, current_app=self.name)
                        except NoReverseMatch:
                            pass
                    if perms.get('add', False):
                        try:
                            model_dict['add_url'] = reverse('%s:%s_%s_add' % info, current_app=self.name)
                        except NoReverseMatch:
                            pass
                    if app_label in app_dict:
                        app_dict[app_label]['models'].append(model_dict)
                    else:
                        app_dict[app_label] = {
                            'name': app_label.title(),
                            'app_url': reverse('%s:app_list' % self.app_name, kwargs={'app_label': app_label},
                                current_app=self.name),
                            'has_module_perms': has_module_perms,
                            'models': [model_dict],
                            }

        # Sort the apps alphabetically.
        app_list = app_dict.values()
        app_list.sort(key=lambda x: x['name'])

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])

        context = self.get_context(**{
            'title': _('Site administration'),
            'app_list': app_list,
            })
        context.update(extra_context or {})
        return TemplateResponse(request, [
            self.index_template or self.get_template('index.html')
        ], context, current_app=self.name)


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
                        info = (self.app_name, app_label, model._meta.module_name)
                        model_dict = {
                            'name': capfirst(model._meta.verbose_name_plural),
                            'perms': perms,
                            }
                        if perms.get('change', False):
                            try:
                            #                                model_dict['admin_url'] = reverse('%s:%s_%s_changelist' % info, current_app=self.name)
                                model_dict['admin_url'] = reverse('%s:%s_%s_changelist' % info, current_app=self.name)
                            except NoReverseMatch:
                                pass
                        if perms.get('add', False):
                            try:
                                model_dict['add_url'] = reverse('%s:%s_%s_add' % info, current_app=self.name)
                            except NoReverseMatch:
                                pass
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
            raise Http404('The requested admin page does not exist.')
            # Sort the models alphabetically within each app.
        app_dict['models'].sort(key=lambda x: x['name'])
        context = self.get_context(**{
            'title': _('%s administration') % capfirst(app_label),
            'app_list': [app_dict],
            })
        context.update(extra_context or {})

        return TemplateResponse(request, self.app_index_template or [
            self.get_template('%s/app_index.html' % app_label),
            self.get_template('app_index.html'),
            ], context, current_app=self.name)

    def login(self, request, extra_context=None):
        self.login_template = self.login_template or self.get_template('login.html')
        context = self.get_context(**(extra_context or {}))
        return super(IAdminSite, self).login(request, context)

    def logout(self, request, extra_context=None):
        self.logout_template = self.logout_template or self.get_template('registration/logged_out.html')
        context = self.get_context(**(extra_context or {}))
        return super(IAdminSite, self).logout(request, context)


    def password_change(self, request):
        """
        Handles the "change password" task -- both form display and validation.
        """
        from django.contrib.auth.views import password_change

        url = reverse('admin:password_change_done', current_app=self.name)
        defaults = {
            'current_app': self.name,
            'post_change_redirect': url,
            'extra_context': self.get_context()
        }
        if self.password_change_template is not None:
            defaults['template_name'] = self.password_change_template
        return password_change(request, **defaults)


    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        urlpatterns = patterns('',
            url(r'^s/format/date/$',
                wrap(self.format_date),
                name='format_date'),

            url(r'^s/info/test_mail/$',
                wrap(self.test_mail, True),
                name="test_mail"
            ),
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
        return urlpatterns + super(IAdminSite, self).get_urls()

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name


    def get_imodeladmin(self, model_admin):
        if not isinstance(model_admin, ModelAdmin) and issubclass(model_admin, IModelAdminMixin):
            return model_admin

        name = 'I%s' % model_admin.__class__.__name__
        bases = (model_admin, IModelAdmin)
        if not hasattr(model_admin, 'cell_filter'):
            args = {'cell_filter': model_admin.list_filter}
        else:
            args = {}
        try:
            ret= type(name, bases, args)
        except TypeError as e:
            ret = type(name, (IModelAdminMixin, type(model_admin) ), args)
        except Exception as  e:
            ret = IModelAdmin

        return ret

    def process(self, mod):
        for model, model_admin in mod.__iadmin__:
            try:
                self.register(model, model_admin)
            except Exception, e:
                logging.error(e)


    def autodiscover(self):
        """
        same as django.admin.autodiscover.
        """
        from django.utils.importlib import import_module
        from django.utils.module_loading import module_has_submodule

        with IProxy():
            for app in settings.INSTALLED_APPS:
                mod = import_module(app)
                try:
                    before_import_registry = copy.copy(self._registry)
                    mod = import_module('%s.admin' % app)
                except BaseException:
                    self._registry = before_import_registry
                    if module_has_submodule(mod, 'admin'):
                        raise

    def autoregister(self):
        """
        register models defined into __iadmin__ attribute
        """
        from django.utils.importlib import import_module
        from django.utils.module_loading import module_has_submodule

        for app in settings.INSTALLED_APPS:
            mod = import_module(app)
            try:
                before_import_registry = copy.copy(self._registry)
                mod = import_module('%s.admin' % app)
#                if hasattr(mod, '__iadmin__'):
#                    self.process(mod)
            except BaseException:
                self._registry = before_import_registry
                if module_has_submodule(mod, 'admin'):
                    raise

    def investigate_admin(self, site):
        """
        Register all models registerd int passed AdminSite instance
        :param site: AdminSite instance
        :return: None
        """
        for model, model_admin in site._registry.items():
            self.register(model, self.get_imodeladmin(model_admin))

    def register(self, model_or_iterable, admin_class=None, **options):
        """
            register a model or an iterable using IModelAdmin
        """
        if not admin_class:
            admin_class = IModelAdmin
        else:
            admin_class = self.get_imodeladmin(admin_class)
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]

        override = options.pop('override', False)

        for model in model_or_iterable:
            if model in self._registry:
                if override:
                    self.unregister(model)
                else:
                    continue
            super(IAdminSite, self).register(model, admin_class, **options)

    def register_all(self, exclude=None):
        """
        register all models of all applications
        :return: None
        """
        _exclude = exclude or []
        for app in (a for a in get_apps() if a not in _exclude):
            for model in get_models(app):
                self.register(model, IModelAdmin)

    def format_date(self, request):
        d = datetime.datetime.now()
        return HttpResponse(dateformat.format(d, request.GET.get('fmt', '')))

    def get_context(self, **kwargs):
        ctx = {'current_app': self.name}
        ctx.update(kwargs)
        return ctx

    def env_info_counters(self, request, export=False):
        app_dict = {}
        for model, model_admin in self._registry.items():
            app_label = model._meta.app_label
            info = (self.name, app_label, model._meta.module_name)
            model_dict = {
                'name': capfirst(model._meta.verbose_name_plural),
                'perms': model_admin.get_model_perms(request),
                'admin_url': self.reverse_admin(model),
                'row_count': model.objects.count(),
                }
            if app_label in app_dict:
                app_dict[app_label]['models'].append(model_dict)
            else:
                app_dict[app_label] = {
                    'name': app_label.title(),
                    'models': [model_dict],
                    }

        # Sort the apps alphabetically.
        app_list = app_dict.values()
        app_list.sort(key=lambda x: x['name'])

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])

        context = self.get_context(**{
            'title': _('Site administration'),
            'app_list': app_list,
            'STATIC_URL': settings.STATIC_URL,
            })
        return render_to_response(('%s/env_info_counters.html' % self.template_prefix,
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

        context = self.get_context(**{'lib': lib,
                                      'curdir': os.path.abspath(os.path.curdir),
                                      'os_user': getuser(),
                                      'os': os,
                                      'title': _("System information"),
                                      'sys': {'platform': sys.platform,
                                              'version': sys.version_info,
                                              'os': os.uname(),
                                              'mail_server': settings.EMAIL_HOST,
                                              'django': django.get_version()},
                                      'database': settings.DATABASES,
                                      'path': sys.path,
                                      'apps': _apps()
        })
        context_instance = template.RequestContext(request, current_app=self.name)

        return render_to_response(('%s/env_info.html' % self.template_prefix,
                                   'iadmin/env_info.html'), context, context_instance=context_instance)

    def test_mail(self, request):
        from django.core.mail import send_mail

        email = request.user.email
        send_mail('test email', 'This is a test message', email, [email], fail_silently=True)
        return HttpResponseRedirect(reverse("%s:info" % self.app_name))

    def import_csv(self, request, app_label, model_name, page, **kwargs):
        return CSVImporter(self, app_label, model_name, page, **kwargs).dispatch(request)

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

    def admin_shortcut(self, request, content_type_id, object_id):
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get(pk=content_type_id)
        obj = content_type.get_object_for_this_type(pk=object_id)
        url = self.reverse_admin(obj, 'change', args=[int(object_id)])
        return HttpResponseRedirect(url)


site = IAdminSite()

