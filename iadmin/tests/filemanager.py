from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase
import tempfile
try:
    from mock import patch
except ImportError:
    patch = None
import os

files = []
RENAMED_FILENAME = '1111.txt'

def touch(fname):
    fullpath = os.path.join(settings.IADMIN_FM_ROOT, fname)
    f = open(fullpath, 'w')
    f.close()
    files.append(fullpath)


class FileManagerTest(TestCase):
    urls = 'iadmin.tests.urls'
    fixtures = ['test.json',]
#    maxDiff = None

    def setUp(self):
        super(FileManagerTest, self).setUp()
        assert self.client.login(username='sax', password='123')
        settings.IADMIN_FM_ROOT = os.path.join(os.path.dirname(__file__),'fmenv')
        if os.path.exists(os.path.join(settings.IADMIN_FM_ROOT, RENAMED_FILENAME)):
            os.unlink(os.path.join(settings.IADMIN_FM_ROOT, RENAMED_FILENAME))

    def tearDown(self):
        super(FileManagerTest, self).tearDown()
        if os.path.exists(os.path.join(settings.IADMIN_FM_ROOT, RENAMED_FILENAME)):
            os.unlink(os.path.join(settings.IADMIN_FM_ROOT, RENAMED_FILENAME))
        
    def test_upload(self):
        fm = reverse('admin:iadmin.fm.upload', kwargs={'path':''})
        r = self.client.get( fm )
        self.assertEqual(r.context['title'], 'FileManager')

    def test_index(self):
        fm = reverse('admin:iadmin.fm.index', kwargs={'path':''})
        r = self.client.get( fm )
        self.assertEqual(r.context['title'], 'FileManager')

        expected = [str(os.path.join(settings.IADMIN_FM_ROOT, f)) for f in  [u'dir1', u'dir2', u'file1.txt', u'file2.png']]
        got = [f.absolute_path for f in  r.context['files']]
        self.assertEqual(got, expected)

    def test_dir1(self):
        fm = reverse('admin:iadmin.fm.index', kwargs={'path':'dir1'})
        r = self.client.get( fm )
        self.assertEqual(r.context['title'], 'FileManager')

        expected = [os.path.join(settings.IADMIN_FM_ROOT, 'dir1' ,f) for f in  [u'dir11']]
        got = [f.absolute_path for f in  r.context['files']]
        self.assertEqual(got, expected)

    def test_delete(self):
        file_to_delete = tempfile.NamedTemporaryFile(dir=settings.IADMIN_FM_ROOT, prefix='iadmin')
        home = reverse('admin:iadmin.fm.index', kwargs={'path':''})
        url = reverse('admin:iadmin.fm.delete', kwargs={'path': file_to_delete.name})
        r = self.client.get( url )
        self.assertRedirects(r, home)

        r = self.client.get( home )
        self.assertFalse(file_to_delete.name in [f.absolute_path for f in  r.context['files']])

    def test_permission_denied_rename_dir(self):
        fm = reverse('admin:iadmin.fm.index', kwargs={'path':''})
        assert self.client.login(username='user_no_perm_for_file_manager', password='123')
        r = self.client.get( fm )
        path = r.context['files'][0].absolute_path # this should be dir1
        name = os.path.basename(path)
        rename_url = reverse('admin:iadmin.fm.rename')
        r = self.client.get( rename_url, {'oldname':name, 'newname':'222', 'base':''} )
        self.assertEqual(r.status_code, 403)

    def test_permission_granted_rename_dir(self):
        if patch:
            fm = reverse('admin:iadmin.fm.index', kwargs={'path':''})
            assert self.client.login(username='user_permission_file_manager', password='123')
            r = self.client.get( fm )
            path = r.context['files'][0].absolute_path # this should be dir1
            name = os.path.basename(path)
            rename_url = reverse('admin:iadmin.fm.rename')
            with patch('os.rename'):
                r = self.client.get( rename_url, {'oldname':name, 'newname':'222', 'base':''} )
            self.assertEqual(r.status_code, 302, 200)
