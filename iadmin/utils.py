from iadmin.options import ITabularInline
from django.db import models

def tabular_factory(model, fields=None, Inline=ITabularInline, form=None, **kwargs):
    """ factory for ITabularInline
            
    >>> class MD(IModelAdmin):
    ...     inlines = [tabular_factory(Permission)]
    """
    name = "%sInLine" % model.__class__.__name__
    #form = "%sForm" % model.__class__.__name__
    attrs = {'model': model, 'fields': fields}
    if form:
        attrs['form'] = form
    attrs.update(kwargs)
    Tab = type(name, (Inline,), attrs)
    return Tab

class K:

    def __init__(self, label = None, **kwargs):
        assert(len(kwargs) == 1)
        for k, v in kwargs.items():
            self.id = k
            self.v = v
        self.label = label or self.id

    def __str__(self):
        return self.label


class Choices(object):
    """
    >>> options = Choices(
    ... K(pending=1, label='Pending'),
    ... K(accepted=2, label='Accepted'),
    ... K(rejected=3)
    ... )
    >>> options.pending
    1
    >>> options.choices()
    [(1, 'Pending'), (2, 'Accepted'), (3, 'rejected')]
    """

    def __iter__(self):
        for x in [(k.v, k.label) for k in self.klist ]:
            yield x

    def __init__(self, *args):
        self.klist = args
        for k in self.klist:
            setattr(self, k.id, k.v)

    def labels(self, excludes=None):
        _excludes = excludes or []
        return [k.label for k in self.klist if k.id not in _excludes]

    def choices(self, excludes=None):
        _excludes = excludes or []
        return [(k.v, k.label) for k in self.klist if k.id not in _excludes]

    def subset(self, includes=None):
        _includes = includes or []
        return [(k.v, k.label) for k in self.klist if k.id in _includes]

    def get_by_value(self, value):
        for x in self.klist:
            if x.v == value:
                return x

def iter_get_attr(obj, attr, default=None):
    """Recursive get object's attribute. May use dot notation.
    
    >>> class C(object): pass
    >>> a = C()
    >>> a.b = C()
    >>> a.b.c = 4
    >>> iter_get_attr(a, 'b.c')
    4
    """
    if '.' not in attr:
        return getattr(obj, attr, default)
    else:
        L = attr.split('.')
        return iter_get_attr(getattr(obj, L[0], default), '.'.join(L[1:]), default)


def lookup_field(name, obj, model_admin=None):
    opts = obj._meta
    try:
        f = opts.get_field(name)
    except models.FieldDoesNotExist:
        # For non-field values, the value is either a method, property or
        # returned via a callable.
        if callable(name):
            attr = name
            value = attr(obj)
        elif (model_admin is not None and hasattr(model_admin, name) and
          not name == '__str__' and not name == '__unicode__'):
            attr = getattr(model_admin, name)
            value = attr(obj)
        else:
            attr = getattr(obj, name)
            if callable(attr):
                value = attr()
            else:
                value = attr
        f = None
    else:
        attr = None
        value = getattr(obj, name)
    return f, attr, value    