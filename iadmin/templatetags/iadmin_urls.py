from django.core.urlresolvers import reverse, NoReverseMatch, resolve
from django import template
from django.template.base import Template
from django.template.loader import render_to_string, find_template, get_template

register = template.Library()

@register.filter
def admin_urlname(opts, arg):
    return 'admin:%s_%s_%s' % (opts.app_label, opts.module_name, arg)

@register.simple_tag(takes_context=True)
def admin_url(context, name, *args, **kwargs):
    return reverse('%s:%s' % (context.get('current_app','iadmin'), name), args=args, kwargs=kwargs, current_app=context.get('current_app','iadmin'))

@register.simple_tag(takes_context=True)
def admin_model_url(context, model, name):
    return reverse('%s:%s_%s_%s' % (context.get('current_app','iadmin'), model._meta.app_label, model._meta.module_name, name))

@register.simple_tag(takes_context=True)
def iinclude(context, filename):
    """ like standard templatetag `include` but allow to use context variables
    into the filename
    {% iinclude '{{myvar}}/path/to/filename' %}
    """
    real_filename =  Template(filename).render(context)
    return get_template(real_filename).render(context)























