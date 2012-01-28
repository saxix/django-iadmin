from django.conf import settings
from django.core import urlresolvers
import re
from django.template.base import Library

register = Library()

@register.filter("range")
def to_range( value ):
    return range(value)

numeric_test = re.compile("^\d+$")

@register.filter(name='hide')
def getattribute(value, arg):
    if arg in ('PASSWORD', ):
        return '*******'
    else:
        return value

@register.filter(name='getattr')
def getattribute(value, arg):
    """Gets an attribute of an object dynamically from a string name"""
    if hasattr(value, str(arg)):
        return getattr(value, arg)
    elif hasattr(value, 'has_key') and value.has_key(arg):
        return value[arg]
    elif numeric_test.match(str(arg)) and len(value) > int(arg):
        return value[int(arg)]
    else:
        return settings.TEMPLATE_STRING_IF_INVALID


@register.simple_tag(takes_context=True)
def import_csv_url(context):
    args = ()
    kwargs = {}
    view_name = 'import_csv'

    if 'original' in context:
        app = context['original']._meta.app_label
        model = context['original'].__class__.__name__.lower()
        view_name = 'model_import_csv'
        kwargs = {'app': app, 'model': model, 'page': 1}
    elif 'app_list' in context and len(context['app_list']) == 1:
        app = context['app_list'][0]['name'].lower()
        view_name = 'app_import_csv'
        kwargs = {'app': app, 'page': 1}
    elif 'cl' in context:
        app = context['cl'].model._meta.app_label
        model = context['cl'].model.__name__.lower()
        view_name = 'model_import_csv'
        kwargs = {'app': app, 'model': model, 'page': 1}

    url = urlresolvers.reverse('admin:%s' % view_name, args=args, kwargs=kwargs)
    return '<a href="%s">import</a>' % url
