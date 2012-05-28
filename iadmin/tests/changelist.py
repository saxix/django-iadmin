from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from iadmin.tests.common import BaseTestCase

class ChangeListTest(BaseTestCase):

    def test_not_equals_to(self):
        url = reverse("iadmin:auth_user_changelist")
        u = User.objects.get(email='sax@os4d.org')
        response = self.client.get(url, {'email__not':u.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cl'].result_count, 11)

    def test_equals_to(self):
        url = reverse("iadmin:auth_user_changelist")
        u = User.objects.get(email='sax@os4d.org')
        response = self.client.get(url)
        response = self.client.get(url, {'email__exact':u.email})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cl'].result_count, 1)

