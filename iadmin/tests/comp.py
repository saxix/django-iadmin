from django.test.testcases import TestCase
import iadmin.proxy as admin 
from django.contrib.auth.models import User

class CompatibilityTest(TestCase):
    urls = 'iadmin.tests.urls'
    fixtures = ['test.json',]
    maxDiff = None

    def setUp(self):
        super(CompatibilityTest, self).setUp()
        self.client.login(username='sax', password='123')

    def tearDown(self):
        super(CompatibilityTest, self).tearDown()
        if User in admin.site._registry:
            admin.site.unregister( User )

