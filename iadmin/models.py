from django.conf import settings
from django.contrib.auth.management import _get_permission_codename
from django.db.models import signals
from django.core.exceptions import ImproperlyConfigured

_requirements = ('django.contrib.auth', 'django.contrib.sessions')
for req in _requirements:
    if req not in settings.INSTALLED_APPS:
        raise ImproperlyConfigured("Put '%s' in your INSTALLED_APPS setting in order to use the iAdmin." % req)

def create_extra_permission(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.db.models.loading import get_models
    from django.contrib.contenttypes.models import ContentType

    for model in get_models(sender):
        for action in ('view', 'export', 'massupdate', 'import'):
            opts = model._meta
            codename = _get_permission_codename(action, opts)
            label = u'Can %s %s' % (action, opts.verbose_name_raw)
            ct = ContentType.objects.get_for_model(model)
            Permission.objects.get_or_create(codename=codename, content_type=ct, defaults={'name': label})

    # restrictions
    for model in get_models(sender):
        opts = model._meta
        codename = u'read_only_%s' % opts.object_name.lower()
        label = u'Can only read %s' % opts.verbose_name_raw
        ct = ContentType.objects.get_for_model(model)
        Permission.objects.get_or_create(codename=codename, content_type=ct, defaults={'name': label})

signals.post_syncdb.connect(create_extra_permission)
