#
from django.conf import settings
from django.db import models

__author__ = 'sax'


from django.contrib.admin.views.main import ChangeList

class IChangeList(ChangeList):
    def _cell_filter(self, obj, field):
        target = getattr(obj, field.name)
        if not (obj and target):
            return ''
        if isinstance(field.rel, models.ManyToOneRel):
            rel_name = field.rel.get_related_field().name
            lookup_kwarg = '%s__%s__exact' % (field.name, rel_name)
            url = self.get_query_string( {lookup_kwarg: target.pk})
        else:
            lookup_kwarg = '%s__exact' % field.name
            url = self.get_query_string( {lookup_kwarg: target})

        return '&nbsp;<span class="linktomodel"><a href="%s"><img src="%siadmin/img/zoom.png"/></a></span>' % (url, settings.MEDIA_URL)

    def _link_to_model(self, obj, label=None):
        if not obj:
            return ''
        url = self.model_admin.admin_site.reverse_model(obj.__class__, obj.pk)
        return '&nbsp;<span class="linktomodel"><a href="%s"><img src="%siadmin/img/link.png"/></a></span>' % (url, settings.MEDIA_URL)