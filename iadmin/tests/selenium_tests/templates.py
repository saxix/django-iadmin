# -*- coding: utf-8 -*-
import os
from django.core.urlresolvers import reverse
from iadmin.tests.selenium_tests.common import FireFoxLiveTest

__all__ = ['CustomTemplateFirefox', ]
TEST_TEMPLATES_DIRS = (os.path.join(os.path.dirname(__file__), 'templates'), )
TEST_TEMPLATE_LOADERS = ('django.template.loaders.filesystem.Loader',)

class CustomTemplateFirefox(FireFoxLiveTest):
#    def setUp(self):
#        super(CustomTemplateFirefox, self).setUp()
#        self.factory = RequestFactory()

    def test1(self):
        driver = self.driver
        url = reverse('test:index')
        self.login(url)
        self.assertEqual("Site administration | iAdmin TEST console", driver.title)

    def test2(self):
        driver = self.driver
        url = reverse('iadmin:index')
        self.login(url)
        self.assertEqual("Site administration | iAdmin console", driver.title)
        url = reverse('iadmin:auth_permission_add')
        self.go(url)
        self.assertEqual("Add permission | iAdmin console", driver.title)
