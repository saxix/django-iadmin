from django.contrib.auth.models import User
from django.test.testcases import TestCase
from . import urls

class MassUpdateTest(TestCase):
    fixtures = ['geo.json']
    urls = urls
    
    def test_1(self):
        self.client.login()
        print User.objects.all()
        self.client.get('/admin')