import datetime
import django
from django.conf.urls.defaults import url, patterns
#import django.contrib.admin.sites
from django import http, template
from django.contrib.admin.sites import AdminSite
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db.models.loading import get_models
from django.db.models.signals import post_save, post_delete
from django.http import HttpResponseRedirect, HttpResponse
from django.utils.functional import update_wrapper
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.views.decorators.cache import never_cache
from . import options 
from django.utils import dateformat, numberformat, datetime_safe


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
    
    def __init__(self, name=None, app_name='admin'):
        super(IAdminSite, self).__init__(name, app_name)
        #self.disable_action('delete_selected')

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
            'root_path': self.root_path,
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
            'app_list': [app_dict],
            'root_path': self.root_path,
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.name)
        return render_to_response(self.app_index_template or ('admin/%s/app_index.html' % app_label,
            'admin/app_index.html'), context,
            context_instance=context_instance
        )

    def admin_shortcut(self, request, content_type_id, object_id):
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get(pk=content_type_id)
        #obj = content_type.get_object_for_this_type(pk=object_id)
        view = "admin:%s_%s_change" % (content_type.app_label, content_type.model)
        url = reverse(view, args=[int(object_id)])
        return HttpResponseRedirect( url )

    def format_date(self, request):
        d = datetime.datetime.now()
        return HttpResponse(dateformat.format(d, request.GET.get('fmt','')))

    def get_urls(self):
        """
            url admin_shortcut
            Ex.
        """
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        urlpatterns = super(IAdminSite, self).get_urls\
            ()
        urlpatterns += patterns('',
                                url(r'^s/format/date/$',
                                    wrap(self.format_date),
                                    name='format_date'),

                                url(r'^a/(?P<content_type_id>\d+)/(?P<object_id>.+)/$',
                                    wrap(self.admin_shortcut),
                                    name='admin_shortcut'))
        return urlpatterns

    def register_missing(self, app):
        from django.db.models.loading import get_models
        [self.register(m, options.IModelAdmin) for m in get_models(app) if not m in self._registry]

def invalidate_index(sender, **kwargs):
    cache.set('admin_index', None, 0)
    #expire_view_cache('admin_index')

post_save.connect(invalidate_index)
post_delete.connect(invalidate_index)

django.contrib.admin.site = django.contrib.admin.sites.site = site = IAdminSite()

  