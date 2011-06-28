from django.conf import settings

class Config(object):
    defaults = {'count_rows': True,
                'cache_home': True,
                }

    def __init__(self):
        if not hasattr(settings, 'IADMIN_CONFIG'):
            setattr(settings, 'IADMIN_CONFIG', self.defaults)

    def __getattr__(self, name):
        return getattr(settings.IADMIN_CONFIG, name, self.defaults[name])

config = Config()