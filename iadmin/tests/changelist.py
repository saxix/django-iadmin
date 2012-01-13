from django.contrib.auth.models import User
from django.test.testcases import TestCase
from iadmin.tests.common import FireFoxLiveTest, ChromeDriverMixin

class ChangeListTest(TestCase):
    urls = 'iadmin.tests.urls'
    fixtures = ['test.json',]

    def setUp(self):
        super(ChangeListTest, self).setUp()
        assert self.client.login(username='sax', password='123')

    def test_not_equals_to(self):
        url = "/admin/auth/user/"
        u = User.objects.get(email='sax@os4d.org')
        response = self.client.get(url, {'email__not':u.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cl'].result_count, 11)

    def test_equals_to(self):
        url = "/admin/auth/user/"
        u = User.objects.get(email='sax@os4d.org')
        response = self.client.get(url, {'email__exact':u.email})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cl'].result_count, 1)


class CellFilterFireFox(FireFoxLiveTest):

    def _test_menu_open(self):
        self.login()
        self.go('/admin/auth/user/')
        self.driver.find_elements_by_class_name('iadmin-cell-menu-button')[0].click()

    def test_equals_to(self):
        self.login()
        self.driver.implicitly_wait(10)
        self.go('/admin/auth/user/')
        # get the menu container
        container = self.driver.find_elements_by_class_name('iadmin-cell-menu-container')[0]
        # click the button...
        container.find_elements_by_class_name('iadmin-cell-menu-button')[0].click()
        # and click the 'Equals to' menu item
        container.find_element_by_link_text('Equals to').click()

        # collects all the rows
        tbody = self.driver.find_element_by_css_selector('#result_list tbody')
        rows = tbody.find_elements_by_class_name('action-checkbox')
        self.assertEquals(len(rows), 1)

    def test_not_equals_to(self):
        self.login()
        self.driver.implicitly_wait(10)
        self.go('/admin/auth/user/')
        # get the menu container
        container = self.driver.find_elements_by_class_name('iadmin-cell-menu-container')[0]

        # click the button...
        container.find_elements_by_class_name('iadmin-cell-menu-button')[0].click()
        # and click the 'Equals to' menu item
        container.find_element_by_link_text('Not equals to').click()

        # collects all the rows
        tbody = self.driver.find_element_by_css_selector('#result_list tbody')
        rows = tbody.find_elements_by_class_name('action-checkbox')
        self.assertEquals(len(rows), 11)
#        self.driver.save_screenshot()

    def test_equals_to_bool(self):
        self.login()
        self.driver.implicitly_wait(10)
        self.go('/admin/auth/user/')
        # get the menu container
        container = self.driver.find_elements_by_class_name('iadmin-cell-menu-container')[2]
        # click the button...
        container.find_elements_by_class_name('iadmin-cell-menu-button')[0].click()
        # and click the 'Equals to' menu item
        container.find_element_by_link_text('Yes').click()

        # collects all the rows
        tbody = self.driver.find_element_by_css_selector('#result_list tbody')
        rows = tbody.find_elements_by_class_name('action-checkbox')
        self.assertEquals(len(rows), 1)

    def test_not_equals_to_bool(self):
        self.login()
        self.driver.implicitly_wait(10)
        self.go('/admin/auth/user/')
        # get the menu container
        container = self.driver.find_elements_by_class_name('iadmin-cell-menu-container')[2]
        # click the button...
        container.find_elements_by_class_name('iadmin-cell-menu-button')[0].click()
        # and click the 'Equals to' menu item
        container.find_element_by_link_text('No').click()

        # collects all the rows
        tbody = self.driver.find_element_by_css_selector('#result_list tbody')
        rows = tbody.find_elements_by_class_name('action-checkbox')
        self.assertEquals(len(rows), 11)

class CellFilterChrome(ChromeDriverMixin, CellFilterFireFox):
    pass
