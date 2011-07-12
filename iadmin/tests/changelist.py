from django.test.testcases import TestCase



class ChangeListTest(TestCase):
    urls = 'iadmin.tests.urls'
    fixtures = ['test.json',]
    def setUp(self):
        super(ChangeListTest, self).setUp()
        assert self.client.login(username='sax', password='123')

    def test_order(self):
        url = "/admin/auth/permission/"
        r = self.client.get(url, {'content_type__app_label':'iadmin'})