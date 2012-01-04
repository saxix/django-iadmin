from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
import os

DATADIR = os.path.join(os.path.dirname(__file__), 'data')

class CSVImporterTest(TestCase):

    def test_import_csv_without_headers(self):
        f = open(os.path.join(DATADIR, 'user_with_headers.csv'), 'rb')
        url = reverse('admin:model_import_csv', kwargs=dict(app='auth', model='user', page=1))
        self.client.login()
        self.client.get(url)
        data = {'model': 'auth:user',
                'csv' : f,
                'page': 1,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

