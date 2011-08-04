from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.db import models
import dexf.fields

class FileManager(models.Model):
    """ dummy class to link FileManager Permission
    """
    class Meta:
        abstract = True
        permissions = (("can_upload_file", "Can upload file"), ("can_create_dir", "Can make directory"),
                           ("can_delete_file", "Can delete file"), ("can_delete_dir", "Can delete directory"),
                           ("can_rename_file", "Can rename file"), ("can_rename_dir", "Can rename directory"),)


def register_permission(perm):
    ct, created = ContentType.objects.get_or_create(model='FileManager', app_label='iadmin',
                                                    defaults={'name': 'FileManager'})
    codename, name = perm
    p, created = Permission.objects.get_or_create(codename=codename, content_type=ct,
                                                  defaults={'name': name, 'content_type': ct})


def register(**kwargs):
    for p in FileManager.Meta.permissions:
        register_permission(p)

class UserPreferences(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, default='')
    user = models.ForeignKey('auth.User', blank=False, null=False)
    data = dexf.fields.JSONField(blank=True, null=False)


    def __unicode__(self):
        return "%s:%s user preferences" % (self.user.username, self.name)

    class Meta:
        ordering = ('user',)
        unique_together = ('user', 'name'),
        app_label = 'iadmin'



signals.post_syncdb.connect(register)