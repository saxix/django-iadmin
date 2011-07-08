from iadmin.options import ITabularInline
from django.db import models

def tabular_factory(model, fields=None, Inline=ITabularInline, form=None, **kwargs):
    """ factory for ITabularInline
            
    >>> class MD(IModelAdmin):
    ...     inlines = [tabular_factory(Permission)]
    """
    name = "%sInLine" % model.__class__.__name__
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

