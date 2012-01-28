from django.core.urlresolvers import reverse
from importer import *
from changelist import *
from mass_update import *
from export_csv import *

class InfoPageTest(BaseTestCase):

    def test_info_page(self):
        url = reverse("iadmin:info")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual("System information", response.context['title'])
