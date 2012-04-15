# -*- coding: utf-8 -*-
from django.test.client import RequestFactory
import os
#from iadmin.tests.admin import IUserAdmin
from iadmin.tests.common import FireFoxLiveTest
import iadmin.api as admin

__all__ = ['CustomTemplateFirefox', ]
TEST_TEMPLATES_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'), )
TEST_TEMPLATE_LOADERS = ('django.template.loaders.filesystem.Loader',)

class CustomTemplateFirefox(FireFoxLiveTest):
    def setUp(self):
        self.factory = RequestFactory()

    def test1(self):
#        with self.settings(TEMPLATE_LOADERS=TEST_TEMPLATE_LOADERS, TEMPLATE_DIRS=TEST_TEMPLATES_DIRS):
#            IUserAdmin.template_prefix = admin.site.template_prefix = 'test'
        driver = self.driver
        self.login('/test/')
        self.assertEqual("Site administration | iAdmin TEST console", driver.title)
