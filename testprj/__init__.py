# The next line needs clarification:
# try to manage the import of django-reversion into `except ImportError` section in django 1.2 cause strange issues,
# the development server refuse to start or is unable to find the templates once started. Thi works on 1.2 and higher
import settings
try:
    import reversion
except ImportError:
    settings.INSTALLED_APPS .remove('reversion')