from django.conf import settings
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.core.urlresolvers import reverse, NoReverseMatch
from django.forms.util import flatatt
from django.forms.widgets import Widget
from django.utils.safestring import mark_safe
from django.utils.translation import  ugettext as _

__all__ = ['RelatedFieldWidgetWrapperLinkTo']

class LinkToModelWidget(Widget):
    def __init__(self, linked_widget, model, attrs=None):
    #        self.linked_widget = linked_widget
        self.info = model._meta.app_label, model._meta.object_name.lower()
        super(LinkToModelWidget, self).__init__(attrs)

    def render(self, name, attrs=None):
        final_attrs = self.build_attrs(attrs, name='%s_%s_change' % self.info)
        final_attrs['class'] = u"%s edit link_to_model" % final_attrs.get('class', '')
        final_attrs['id'] = "edit_id_%s" % name
        output = [u'&nbsp;&nbsp<a href="#" %s>' % flatatt(final_attrs),
                  u'<img src="%siadmin/img/link.png" width="10" height="10" alt="%s"/></a>' % (settings.STATIC_URL,
                                                                                               _('Edit'))]

        return mark_safe(u''.join(output))


class RelatedFieldWidgetWrapperLinkTo(RelatedFieldWidgetWrapper):
    def __init__(self, widget, rel, admin_site, can_add_related=None):
        super(RelatedFieldWidgetWrapperLinkTo, self).__init__(widget, rel, admin_site)
        # 1.2.3, 1.3 compatibility
        if can_add_related is None:
            can_add_related = rel.to in admin_site._registry
        self.can_add_related = can_add_related

    def _link_to_code(self, name):
        rel_to = self.rel.to
        info = (rel_to._meta.app_label, rel_to._meta.object_name.lower())
        try:
            # use 0 as pk because the real code in in js, here only to check that user can acces to edit page
            edit_url = reverse('admin:%s_%s_change' % info, current_app=self.admin_site.name, args=['0'])
            if edit_url and rel_to in self.admin_site._registry: # If the related object has an admin interface:
                return LinkToModelWidget(self.widget, rel_to).render(name)
        except NoReverseMatch, e:
            pass
        return ''

    def _add_another_code(self, name):
        rel_to = self.rel.to
        info = (rel_to._meta.app_label, rel_to._meta.object_name.lower())
        try:
            add_related_url = reverse('admin:%s_%s_add' % info, current_app=self.admin_site.name)
            if add_related_url and self.can_add_related:
                # TODO: "id_" is hard-coded here. This should instead use the correct
                return u'''&nbsp;&nbsp;
                          <a href="%s" class="add-another" id="add_id_%s" onclick="return showAddAnotherPopup(this);">
                          <img src="%simg/admin/icon_addlink.gif" width="10" height="10" alt="%s"/></a>''' %\
                       (add_related_url, name, settings.ADMIN_MEDIA_PREFIX, _('Add Another'))
        except NoReverseMatch:
            pass
        return ''

    def render(self, name, value, *args, **kwargs):
        self.widget.choices = self.choices
        output = [self.widget.render(name, value, *args, **kwargs),
                  self._link_to_code(name),
                  self._add_another_code(name)]
        return mark_safe(u''.join(output))

    class Media:
        # TODO: move specific js to related widgets
        js = (
            settings.STATIC_URL + "iadmin/js/jquery.min.js",
            settings.STATIC_URL + "iadmin/js/jquery.min.js",
            settings.STATIC_URL + "iadmin/js/iadmin.js",
            settings.STATIC_URL + "iadmin/js/link_to_model.js",
            )
