from django.conf import settings

class Config(object):
    defaults = {'count_rows': False,
                'cache_home': False,
                }

    def __init__(self):
        if not hasattr(settings, 'IADMIN_CONFIG'):
            setattr(settings, 'IADMIN_CONFIG', self.defaults)

    def __getattr__(self, name):
        ret = settings.IADMIN_CONFIG.get(name, self.defaults[name])
        return ret

config = Config()