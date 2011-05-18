from django.conf import settings
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.core.urlresolvers import reverse, NoReverseMatch
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy, ugettext as _


__all__ = ['RelatedFieldWidgetWrapperLinkTo']


class LabelWidget(forms.HiddenInput, StrAndUnicode):
    
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
        return mark_safe(u'<span%s>%s</span>' % ( forms.util.flatatt(final_attrs),
                                                  force_unicode(value)
                                                  )
        )


class RelatedFieldWidgetWrapperLinkTo(RelatedFieldWidgetWrapper):
    def render(self, name, value, *args, **kwargs):
        rel_to = self.rel.to
        info = (rel_to._meta.app_label, rel_to._meta.object_name.lower())
        try:
            related_url = reverse('admin:%s_%s_add' % info, current_app=self.admin_site.name)
        except NoReverseMatch:
            info = (self.admin_site.root_path, rel_to._meta.app_label, rel_to._meta.object_name.lower())
            related_url = '%s%s/%s/add/' % info
        self.widget.choices = self.choices
        output = [self.widget.render(name, value, *args, **kwargs)]

        if value and rel_to in self.admin_site._registry: # If the related object has an admin interface:
            edit_url = reverse('admin:%s_%s_change' % info, current_app=self.admin_site.name, args=[value])
            output.append(u'<a href="%s" class="edit" id="edit_id_%s"> ' % (edit_url, name))
            output.append(u'<img src="%siadmin/img/edit.png" width="10" height="10" alt="%s"/></a>' % (settings.MEDIA_URL, _('Edit')))
        return mark_safe(u''.join(output))
