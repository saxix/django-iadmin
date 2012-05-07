#from django.db.models.base import ModelBase

def tabular_factory(model, fields=None, inline=None, form=None, **kwargs):
    """ factory for ITabularInline

    >>> class MD(IModelAdmin):
    ...     inlines = [tabular_factory(Permission)]
    """
    from iadmin.options import ITabularInline
    Inline = inline or ITabularInline
    name = "%sInLine" % model.__class__.__name__
    attrs = {'model': model, 'fields': fields}
    if form:
        attrs['form'] = form
    attrs.update(kwargs)
    Tab = type(name, (Inline,), attrs)
    return Tab

class Null(object):

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return self

    def __repr__(self):
        return "Null()"

    def __nonzero__(self):
        return 0

    def __getattr__(self, name):
        return self

    def __setattr__(self, name, value):
        return self

    def __delattr__(self, name):
        return self

    def __getitem__(self, item):
        return self

    def __setitem__(self, item, value):
        return self


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

class cached_property(object):
    '''A read-only @property that is only evaluated once. The value is cached
    on the object itself rather than the function or class; this should prevent
    memory leakage.'''

    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result

def force_unregister(model_or_iterable, adminsite=None):
    import django.contrib.admin
    from iadmin.options import IModelAdmin
    site = adminsite or django.contrib.admin.site
    if isinstance(model_or_iterable, ModelBase):
        model_or_iterable = [model_or_iterable]

    for model in model_or_iterable:
        if model in site._registry:
            site.unregister(model)

def force_register(model_or_iterable, model_admin=None, **options):
    import django.contrib.admin
    from iadmin.options import IModelAdmin
    from django.db.models.base import ModelBase

    adminsite = options.pop('adminsite', None)
    site = adminsite or django.contrib.admin.site
    modelAdmin = model_admin or IModelAdmin
    if isinstance(model_or_iterable, ModelBase):
        model_or_iterable = [model_or_iterable]

    for model in model_or_iterable:
        if model in site._registry:
            site.unregister(model)
        site.register(model, modelAdmin)
