from django.conf import settings, global_settings
import os
from django.test.testcases import TestCase
import iadmin
TEST_TEMPLATES_DIR = os.path.join(os.path.dirname(iadmin.__file__), 'tests', 'templates')


class BaseTestCase(TestCase):
    urls = 'iadmin.tests.urls'
    fixtures = ['test.json', ]

    def setUp(self):
        super(BaseTestCase, self).setUp()
        assert self.client.login(username='sax', password='123')
        self.sett = self.settings(MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE_CLASSES,
            TEMPLATE_DIRS=[TEST_TEMPLATES_DIR])
        self.sett.enable()

    def tearDown(self):
        self.sett.disable()
