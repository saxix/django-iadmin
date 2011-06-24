
#from .widgets import *
import copy
from django.conf import settings
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.core.urlresolvers import reverse, NoReverseMatch
from django.forms.util import flatatt
from django.forms.widgets import TextInput, MultiWidget, Select, HiddenInput, Input, Widget
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from iadmin.widgets import RelatedFieldWidgetWrapperLinkTo, LinkToModelWidget


class AutoCompleteInput(Select):
    class Media:
        js = (
              settings.MEDIA_URL + "iadmin/js/jquery.min.js",
              settings.MEDIA_URL + "iadmin/js/jquery.autocomplete.pack.js",
              settings.MEDIA_URL + "iadmin/js/jquery.min.js",
              settings.MEDIA_URL + "iadmin/js/autocomplete.js",
              )
        css = {
            'all': (settings.MEDIA_URL + "iadmin/css/jquery.autocomplete.css",)
        }

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, type='text', name=name)
        if value != '':
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = force_unicode(value)
        return mark_safe(u'<input%s />' % flatatt(final_attrs))

class AjaxFieldWidgetWrapper(RelatedFieldWidgetWrapperLinkTo):
    widget = AutoCompleteInput

    def __init__(self, widget, rel, admin_site, can_add_related=None, service=None ):
        super(AjaxFieldWidgetWrapper, self).__init__(AutoCompleteInput(), rel, admin_site)
        self.service = service
        # 1.2.3, 1.3 compatibility
        if can_add_related is None:
            can_add_related = rel.to in admin_site._registry
        self.can_add_related = can_add_related

    def render(self, name, value, *args, **kwargs):
        try:
            id, label = value, self.rel.to.objects.get(pk=value)
        except Exception:
            id = ''
            label = ''

        hidden = copy.deepcopy(kwargs)
        kwargs['attrs']['id'] = "lbl_%s" % name
        kwargs['attrs']['class'] = "autocomplete"
        rel_to = self.rel.to
        info = (rel_to._meta.app_label, rel_to._meta.object_name.lower())

        try:
            edit_url = reverse('admin:%s_%s_change' % info, current_app=self.admin_site.name, args=[value])
        except NoReverseMatch, e:
            edit_url = reverse('admin:%s_%s_change' % info, current_app=self.admin_site.name, args=['0'])

        related_url = reverse('admin:%s_%s_add' % info, current_app=self.admin_site.name)
        output = [ HiddenInput().render(name, id, **hidden),
                  AutoCompleteInput().render('', label, **kwargs),
                  '<input type="hidden" value="%s"/>' % self.service,
                  ]

        if value and related_url and rel_to in self.admin_site._registry: # If the related object has an admin interface:
            output.append( LinkToModelWidget(self.widget, rel_to).render(name) )

        if self.can_add_related:
    #            TODO: "id_" is hard-coded here. This should instead use the correct
             # API to determine the ID dynamically.
             output.append(u'<a href="%s" class="add-another" id="add_id_%s" onclick="return showAddAnotherPopup(this);"> ' % \
                 (related_url, name))
             output.append(u'<img src="%simg/admin/icon_addlink.gif" width="10" height="10" alt="%s"/></a>' % (settings.ADMIN_MEDIA_PREFIX, _('Add Another')))

        return mark_safe(u''.join(output))

#    def _media(self):
#        return self.widget.media + self.media
#    media = property(_media)

    class Media:
        js = (
              settings.MEDIA_URL + "iadmin/js/jquery.min.js",
              settings.MEDIA_URL + "iadmin/js/jquery.autocomplete.pack.js",
              settings.MEDIA_URL + "iadmin/js/jquery.min.js",
              settings.MEDIA_URL + "iadmin/js/autocomplete.js",
              settings.MEDIA_URL + "iadmin/js/iadmin.js",
              )
        css = {
            'all': (settings.MEDIA_URL + "iadmin/css/jquery.autocomplete.css",)
        }