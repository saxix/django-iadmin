from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.db import models

class FileManager(models.Model):
    """ dummy class to link FileManager Permission
    """
    class Meta:
        abstract = True


def register_permission(perm):
    ct, created = ContentType.objects.get_or_create(model='FileManager', app_label='iadmin', defaults={'name': 'iadmin'})
    codename, name = perm
    p, created = Permission.objects.get_or_create(codename=codename, content_type__pk=ct.id,
                                                  defaults={'name': name, 'content_type': ct})


def register(**kwargs):
    for p in [("can_upload_file", "Can upload file"),("can_create_dir", "Can make directory"),
            ("can_delete_file", "Can delete file"),("can_delete_dir", "Can delete directory"),
            ("can_rename_dir", "Can rename directory"), ("can_rename_dir", "Can rename directory"),
                                                    ]:
        register_permission(p)

signals.post_syncdb.connect(register)


