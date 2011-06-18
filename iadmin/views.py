#
from django.conf import settings
from django.contrib.admin.util import lookup_field
from django.db import models

__author__ = 'sax'


from django.contrib.admin.views.main import ChangeList

CELL_FILTER_ICON = 'funnel_add.png'

class IChangeList(ChangeList):
    def _cell_filter(self, obj, field_name):
        try:
            field, attr, value = lookup_field(field_name, obj, self.model_admin)

            if hasattr(attr, 'admin_order_field'):
                target_field_name = getattr(attr, 'admin_order_field')

                lookup_kwarg = target_field_name
                lookup_value = value
            else:
                target = getattr(obj, field_name)
                #field = self.model_admin.model._meta.get_field_by_name(field_name)
                field, attr, value = lookup_field(field_name, obj, self.model_admin)
                if not (obj and target):
                    return ''
                if isinstance(field.rel, models.ManyToOneRel):
                    rel_name = field.rel.get_related_field().name
                    lookup_kwarg = '%s__%s' % (field.name, rel_name)
                    lookup_value = target.pk
                    #url = self.get_query_string( {lookup_kwarg: target.pk})
                else:
                    lookup_kwarg = field.name
                    lookup_value = target
            url = self.get_query_string( {lookup_kwarg: lookup_value})

            return '&nbsp;<span class="linktomodel"><a href="%s"><img src="%siadmin/img/%s"/></a></span>' % \
                   (url, settings.MEDIA_URL, CELL_FILTER_ICON)
        except Exception, e:
            return str(e)

    def _link_to_model(self, obj, label=None):
        if not obj:
            return ''
        url = self.model_admin.admin_site.reverse_model(obj.__class__, obj.pk)
        return '&nbsp;<span class="linktomodel"><a href="%s"><img src="%siadmin/img/link.png"/></a></span>' % (url, settings.MEDIA_URL)