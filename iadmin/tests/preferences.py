from django.contrib.auth.models import User
from django.test.testcases import TestCase
from iadmin.models import UserPreferences

class UserPrefsTest(TestCase):
    fixtures = ['sax']
    
    def test1(self):
        u = User.objects.get(username='sax')
        p, _ = UserPreferences.objects.get_or_create(user=u, name='test')

        self.assertEqual(p.data, {})

        