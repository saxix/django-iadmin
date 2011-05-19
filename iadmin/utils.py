#
from . import options

__author__ = 'sax'


def tabular_factory(model, fields=None, **kwargs):
    name = "%sInLine" % model.__class__.__name__
    form = "%sForm" % model.__class__.__name__
    attrs = {'model': model, 'fields': fields }
    if form in globals():
        attrs['form'] = form
    Tab = type(name, (options .ITabularInline,), attrs)
    return Tab