from django.conf import settings
from importer import *
from changelist import *
from mass_update import *

if getattr(settings,'ENABLE_SELENIUM', True):
    try:
        import selenium
        from selenium_tests import *
    except ImportError:
        import warnings
        warnings.warn('Unanble load Selenium. Selenium tests will be disabled')



class InfoPageTest(BaseTestCase):

    def test_info_page(self):
        url = reverse("iadmin:info")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual("System information", response.context['title'])
