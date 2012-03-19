from time import sleep
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
import os
from iadmin.tests.common import BaseTestCase, FireFoxLiveTest

__all__ = ['CSVImportTest', 'CSVImportFireFox']

DATADIR = os.path.join(os.path.dirname(__file__), 'data')

class CSVImportTest(BaseTestCase):
    def test_step_1(self):
        url = reverse('iadmin:import', kwargs=dict(app_label='auth', model_name='user', page=1))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Import CSV File" in response.context['title'])

    def test_step_2(self):
        """ load and parese csv file
        """
        f = open(os.path.join(DATADIR, 'user_with_headers.csv'), 'rb')
        url = reverse('iadmin:import', kwargs=dict(app_label='auth', model_name='user', page=2))
        self.client.get(url)
        data = {'model': 'auth:user',
                'csv': f,
                'page': 1,
                }
        response = self.client.get(url, data)
        self.assertEqual(response.status_code, 200)

#    def test_import_csv_without_headers(self):
#        f = open(os.path.join(DATADIR, 'user_with_headers.csv'), 'rb')
#        url = reverse('iadmin:import', kwargs=dict(app_label='auth', model_name='user', page=1))
#        self.client.get(url)
#        data = {'model': 'auth:user',
#                'csv' : f,
#                'page': 1,
#        }
#        response = self.client.get(url, data)
#        self.assertEqual(response.status_code, 200)

class CSVImportFireFox(FireFoxLiveTest):
    urls = 'iadmin.tests.urls'
    fixtures = ['test.json', ]

    def test_impoty(self):
        """
        Check Boolean Field.
        Common values are not filled in boolean fields ( there is no reaseon to do that ). Always show
        """
        csv_file = os.path.realpath(os.path.join(os.path.dirname(__file__), 'data', 'user_with_headers.csv'))
        self.login()
        driver = self.driver
        driver.get(self.base_url + "/admin/")
        driver.find_element_by_link_text("Users").click()
        driver.find_element_by_link_text("import").click()
        self.assertTrue("Import CSV File" in driver.title)
        # ok stop here there is no way to laod a file via javascript :(
