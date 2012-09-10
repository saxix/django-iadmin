from django.conf import settings, global_settings
import os
from django.test.testcases import TestCase
import iadmin

TEST_TEMPLATES_DIR = os.path.join(os.path.dirname(iadmin.__file__), 'tests', 'templates')
SETTINGS = {'MIDDLEWARE_CLASSES': global_settings.MIDDLEWARE_CLASSES,
            'TEMPLATE_DIRS': [TEST_TEMPLATES_DIR],
#            'COMPRESS_CSS_COMPRESSOR': None,
#            'COMPRESS_JS_COMPRESSOR': None,
            'AUTHENTICATION_BACKENDS': ('django.contrib.auth.backends.ModelBackend',),
            'TEMPLATE_LOADERS': ('django.template.loaders.filesystem.Loader',
                                 'django.template.loaders.app_directories.Loader'),
            'TEMPLATE_CONTEXT_PROCESSORS': ("django.contrib.auth.context_processors.auth",
                                            "django.core.context_processors.debug",
                                            "django.core.context_processors.i18n",
                                            "django.core.context_processors.media",
                                            "django.core.context_processors.static",
                                            "django.core.context_processors.request",
                                            "django.core.context_processors.tz",
                                            "django.contrib.messages.context_processors.messages"
                )
}

class BaseTestCase(TestCase):
    urls = 'iadmin.tests.urls'
    fixtures = ['iadmin_test.json', ]

    def setUp(self):
        TestCase.setUp(self)
        self.sett = self.settings(**SETTINGS)
        self.sett.enable()
        assert self.client.login(username='sax', password='123')

    def tearDown(self):
        self.sett.disable()
