from django.contrib import auth
from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.contrib.messages.storage.cookie import CookieStorage
from django.test.client import RequestFactory
from django.test.testcases import TestCase
from iadmin.actions.mass_update import mass_update
from iadmin.tests.common import FireFoxLiveTest, ChromeDriverMixin, BaseTestCase
from selenium.webdriver.support.ui import Select
import iadmin.tests.admin
import django.contrib.messages.storage

__all__=['MassUpdateTest', 'MassUpdateFireFox']

class MassUpdateTest(BaseTestCase):

    def setUp(self):
        super(MassUpdateTest, self).setUp()
        self.factory = RequestFactory()

    def test_action_get(self):

        request = self.factory.post('/admin/auth/user/',
                {'action': 'mass_update', 'index': 0, 'select_across': 0,
                 '_selected_action': [2, 3, 4]})

        request.user = User.objects.get(pk=1)
        queryset = User.objects.filter(is_superuser=False)
        modeladmin = site._registry[auth.models.User]
        response = mass_update(modeladmin, request, queryset)
        self.assertEqual(response.status_code, 200)

    def test_action_post(self):
        target_ids = [2, 3, 4, 7, 10]

        request = self.factory.post('/admin/auth/user/',
                {'action': 'mass_update', 'apply': 'Update records', 'chk_id_is_active': 'on',
                 '_selected_action': target_ids})

        request.user = User.objects.get(pk=1)
        modeladmin = site._registry[auth.models.User]

        # we add is_active=True just as double check
        queryset = User.objects.filter(pk__in=target_ids, is_active=True)
        response = mass_update(modeladmin, request, queryset)

        self.assertEquals(response.status_code, 302)
        self.assertEquals(target_ids, [u.pk for u in User.objects.filter(is_active=False)])

    def test_many_to_many(self):

        target_ids = [2, 3, 4, 7, 10]

        request = self.factory.post('/admin/auth/user/',
                {'action': 'mass_update', 'apply': 'Update records', 'chk_id_groups': 'on',
                 'groups': ['2'],'_selected_action': target_ids, '_validate': 'on'})

        request.user = User.objects.get(pk=1)
        request._messages = CookieStorage(request)
        modeladmin = site._registry[auth.models.User]

        # we add is_active=True just as double check
        queryset = User.objects.filter(pk__in=target_ids)
        response = mass_update(modeladmin, request, queryset)

        self.assertEquals(response.status_code, 200)
#        print [u.groups.all() for u in User.objects.filter(pk__in=target_ids)]
#        self.assertEquals(target_ids, [u.pk for u in User.objects.filter(is_active=False)])


class MassUpdateFireFox(FireFoxLiveTest):

    def test_mass_update_1(self):
        """
        Check Boolean Field.
        Common values are not filled in boolean fields ( there is no reaseon to do that ). Always show
        """

        self.login()
        driver = self.driver
        driver.get(self.base_url + "/admin/auth/user/")
        self.assertEqual("Select user to change | iAdmin console", driver.title)
        driver.find_element_by_xpath("//input[@id='action-toggle']").click() # select all
        driver.find_element_by_xpath("//input[@name='_selected_action' and @value='1']").click() # unselect sax
        Select(driver.find_element_by_name("action")).select_by_visible_text("Mass update")
        driver.find_element_by_name("index").click() # execute
        self.assertEqual("Mass update users | iAdmin console", driver.title)
        driver.find_element_by_xpath("//div[@id='col1']/form/table/tbody/tr[10]/td[4]/a[2]").click() # False
        driver.find_element_by_name("apply").click()
        self.assertEqual("Select user to change | iAdmin console", driver.title)
        queryset = User.objects.filter(is_active=True)
        self.assertAlmostEqual(len(queryset), 1)


class MassUpdateChrome(ChromeDriverMixin, MassUpdateFireFox):
    pass
