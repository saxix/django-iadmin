from django.conf import settings
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.core.urlresolvers import reverse, NoReverseMatch
from django.forms.widgets import Widget, MediaDefiningClass
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy, ugettext as _

__all__ = ['RelatedFieldWidgetWrapperLinkTo']

class LinkToModelWidget(Widget):


    def __init__(self, linked_widget, model, attrs=None):
        self.linked_widget = linked_widget
        self.info = model._meta.app_label, model._meta.object_name.lower()
        super(LinkToModelWidget, self).__init__(attrs)

    def render(self, name, attrs=None):
        FMT = r"""
        <script>
(function($) {
    $(document).ready(function() {
        $('#edit_id_%(name)s').click(function(){
            var val = $('#id_%(link)s').val();
            var url = $.Resolver.reverse("%(view)s", [val] );
            window.location = url;
        });
    });
})(django.jQuery);
        </script>
""" % {'link': self.linked_widget.id_for_label(name), 'name': name, 'view': '%s_%s_change' % self.info }

        output = [mark_safe(FMT)]
        output.append(u'<a href="#" class="edit" id="edit_id_%s">&nbsp;&nbsp;' % name)
        output.append(u'<img src="%siadmin/img/link.png" width="10" height="10" alt="%s"/></a>&nbsp;&nbsp;' % (settings.MEDIA_URL, _('Edit')))
        return mark_safe(u''.join(output))



class RelatedFieldWidgetWrapperLinkTo(RelatedFieldWidgetWrapper):

    def __init__(self, widget, rel, admin_site, can_add_related=None):
        super(RelatedFieldWidgetWrapperLinkTo, self).__init__(widget, rel, admin_site)
        # 1.2.3, 1.3 compatibility
        if can_add_related is None:
            can_add_related = rel.to in admin_site._registry
        self.can_add_related = can_add_related

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

        if value and related_url and rel_to in self.admin_site._registry: # If the related object has an admin interface:
            output.append( LinkToModelWidget(self.widget, rel_to).render(name) )

        if self.can_add_related:
            # TODO: "id_" is hard-coded here. This should instead use the correct
            # API to determine the ID dynamically.
            output.append(u'<a href="%s" class="add-another" id="add_id_%s" onclick="return showAddAnotherPopup(this);"> ' % \
                (related_url, name))
            output.append(u'<img src="%simg/admin/icon_addlink.gif" width="10" height="10" alt="%s"/></a>' % (settings.ADMIN_MEDIA_PREFIX, _('Add Another')))
        return mark_safe(u''.join(output))

    class Media:
        js = (
              settings.MEDIA_URL + "iadmin/js/iadmin.js",
              )
