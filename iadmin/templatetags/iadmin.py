from . import register
from django.core import urlresolvers


@register.simple_tag(takes_context=True)
def import_csv_url(context):
    args = ()
    kwargs = {}
    view_name = 'import_csv'

    if 'original' in context:
        app = context['original']._meta.app_label
        model = context['original'].__class__.__name__.lower()
        view_name = 'model_import_csv'
        kwargs={'app':app, 'model':model,'page':1}
    elif 'app_list' in context and len(context['app_list']) == 1:
        app = context['app_list'][0]['name'].lower()
        view_name = 'app_import_csv'
        kwargs={'app':app, 'page':1}
    elif 'cl' in context:
        app = context['cl'].model._meta.app_label
        model = context['cl'].model.__name__.lower()
        view_name = 'model_import_csv'
        kwargs={'app':app, 'model':model,'page':1}

    url = urlresolvers.reverse('admin:%s' % view_name, args=args, kwargs=kwargs)
    return '<a href="%s">import</a>' % url
