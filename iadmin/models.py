from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.db import models


def create_readonly_permission(sender, **kwargs):
    from django.contrib.auth.models import Permission
    from django.db.models.loading import get_models
    from django.contrib.contenttypes.models import ContentType
    for model in get_models(sender):
        for op, name in (("view_%s", "Can view %s"), ("export_%s", "can export %s")):
            codename, label = (op % model.__name__.lower(), name % model._meta.verbose_name.title())
            ct = ContentType.objects.get_for_model(model)
            Permission.objects.get_or_create(codename=codename, content_type=ct, defaults={'name': name})

signals.post_syncdb.connect(create_readonly_permission)
