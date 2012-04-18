# -*- coding: utf-8 -*-
from django.test.client import RequestFactory
import os
#from iadmin.tests.admin import IUserAdmin
from django.core.urlresolvers import reverse
from iadmin.tests.common import FireFoxLiveTest
import iadmin.api as admin

__all__ = ['CustomTemplateFirefox', ]
TEST_TEMPLATES_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'), )
TEST_TEMPLATE_LOADERS = ('django.template.loaders.filesystem.Loader',)

class CustomTemplateFirefox(FireFoxLiveTest):
    def setUp(self):
        self.factory = RequestFactory()

    def test1(self):
        driver = self.driver
        self.login('/test/')
        self.assertEqual("Site administration | iAdmin TEST console", driver.title)

    def test2(self):
        driver = self.driver
        self.login('/admin/')
        self.assertEqual("Site administration | iAdmin console", driver.title)
        url = reverse('iadmin:auth_permission_add')
        self.go(url)
        self.assertEqual("Add permission | iAdmin console", driver.title)
