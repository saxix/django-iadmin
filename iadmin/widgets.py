# -*- coding: utf-8 -*-
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.admin.templatetags.admin_static import static
from django.utils.safestring import mark_safe


class IRelatedFieldWidgetWrapper(RelatedFieldWidgetWrapper):
    def render(self, name, value, *args, **kwargs):
        rel_to = self.rel.to
        info = (self.admin_site.name, rel_to._meta.app_label, rel_to._meta.object_name.lower())
        self.widget.choices = self.choices
        output = [self.widget.render(name, value, *args, **kwargs)]
        if self.can_add_related:
            related_url = reverse('%s:%s_%s_add' % info, current_app=self.admin_site.name)
            # TODO: "add_id_" is hard-coded here. This should instead use the
            # correct API to determine the ID dynamically.
            output.append(
                u'<a href="%s" class="add-another" id="add_id_%s" onclick="return showAddAnotherPopup(this);"> '
                % (related_url, name))
            output.append(u'<img src="%s" width="10" height="10" alt="%s"/></a>'
            % (static('admin/img/icon_addlink.gif'), _('Add Another')))
        return mark_safe(u''.join(output))
