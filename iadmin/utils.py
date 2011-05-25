
from iadmin.options import ITabularInline

def tabular_factory(model, fields=None, Inline=ITabularInline, **kwargs):
    name = "%sInLine" % model.__class__.__name__
    form = "%sForm" % model.__class__.__name__
    attrs = {'model': model, 'fields': fields}
    if form in globals():
        attrs['form'] = form
    attrs.update(kwargs)
    Tab = type(name, (Inline,), attrs)
    return Tab