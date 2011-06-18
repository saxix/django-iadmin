from django.core.urlresolvers import reverse
from django.db.models.loading import get_apps, get_models

from django.test import TestCase
import geo
import iadmin.proxy as admin


class ViewsCompatibilityTest(TestCase):
    fixtures = ['test.json',]
    maxDiff = None

    def test_available_urls(self):
        """
        very stupid quick and dirty url checker
        """
        for model, model_admin in admin.site._registry.items():
            info = model._meta.app_label, model._meta.module_name
            for pattern in ('%s_%s_changelist', '%s_%s_add'):#, '%s_%s_history', '%s_%s_delete', '%s_%s_change'):#, '%s_%s_ajax'
                view_name = pattern % info
                url = reverse( view_name )
                print url

        for app in get_apps():
            for model in get_models(app):
                if model in admin.site._registry.keys():
                    print 222222222, model
                    info = model._meta.app_label, model._meta.module_name
                    for pattern in ('%s_%s_changelist', '%s_%s_add'):#, '%s_%s_history', '%s_%s_delete', '%s_%s_change'):#, '%s_%s_ajax'
                        view_name = pattern % info
                        url = reverse( view_name )
                        response = self.client.get( url )
                        self.assertEqual( response.status_code, 200)


