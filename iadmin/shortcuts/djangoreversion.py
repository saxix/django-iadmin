from django.core.urlresolvers import reverse
from django.db import transaction
from iadmin.options import IModelAdmin
from reversion.admin import VersionAdmin as VA
import reversion

class VersionAdmin(IModelAdmin, VA):
    def __init__(self, model, admin_site):
        super(VersionAdmin, self).__init__(model, admin_site)
        VA.__init__(self,model, admin_site)
    change_list_template = None

    @transaction.commit_on_success
    @reversion.revision.create_on_success
    def change_view(self, *args, **kwargs):
        return super(VersionAdmin, self).change_view(*args, **kwargs)

    @transaction.commit_on_success
    @reversion.revision.create_on_success
    def add_view(self, *args, **kwargs):
        return super(VersionAdmin, self).add_view(*args, **kwargs)

    @transaction.commit_on_success
    @reversion.revision.create_on_success
    def delete_view(self, *args, **kwargs):
        return super(VersionAdmin, self).delete_view(*args, **kwargs)

    def history_view(self, request, object_id, extra_context=None):
        return super(VersionAdmin, self).history_view(request, object_id, extra_context)

    def get_urls(self):
        urls = super(VersionAdmin, self).get_urls()
        return urls

    @transaction.commit_on_success
    @reversion.revision.create_on_success
    def changelist_view(self, request, extra_context=None):
        """Renders the change view."""
        opts = self.model._meta
        context = {"recoverlist_url": reverse("%s:%s_%s_recoverlist" % (self.admin_site.name, opts.app_label, opts.module_name)),
                   "add_url": reverse("%s:%s_%s_add" % (self.admin_site.name, opts.app_label, opts.module_name)),}
        context.update(extra_context or {})
        return super(VersionAdmin, self).changelist_view(request, context)

    