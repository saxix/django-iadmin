import urllib
import os
from django.conf import settings


def get_max_upload_size():
    return getattr(settings, 'IADMIN_FILE_UPLOAD_MAX_SIZE', 2000000)

def get_document_root():
    return getattr(settings, 'IADMIN_FM_ROOT', getattr(settings,'MEDIA_ROOT', '/tmp'))

def get_fm_config():
    config = { 'show': lambda x: not x.hidden}
    custom = getattr(settings, 'IADMIN_FM_CONFIG', {})
    config.update(custom)
    return config

def url_to_path(url):
    return os.path.join( get_document_root(), url)

def path_to_url(path):
    return path.replace(get_document_root(), '')

def mkdirs(*dirs):
    for target in dirs:
        if target:
            try:
                os.makedirs(target)
            except OSError, e:
                if e.errno == 17: #File exists
                    pass
                else:
                    raise
                
def clean_path(url):
    """
    Makes the path safe from '.', '..', and multiple slashes. Ensure all
    slashes point the right direction '/'.
    """
    if not url:
        return ''

    result = ''
    path = os.path.normpath(urllib.unquote(url))
    path = path.lstrip('/')
    for part in path.split('/'):
        if not part:
            # Strip empty path components.
            continue
        drive, part = os.path.splitdrive(part)
        head, part = os.path.split(part)
        if part in (os.curdir, os.pardir):
            # Strip '.' and '..' in path.
            continue
        result = os.path.join(result, part).replace('\\', '/')
        
    if result and path != result or not path:
        result = ''
    
    return result

# Copied from python 2.6 
def commonprefix(m):
    "Given a list of pathnames, returns the longest common leading component"
    if not m: return ''
    s1 = min(m)
    s2 = max(m)
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1

# Copied from python 2.6 
def relpath(path, start=os.path.curdir):
    """Return a relative version of a path"""

    if not path:
        raise ValueError("no path specified")

    start_list = os.path.abspath(start).split(os.path.sep)
    path_list = os.path.abspath(path).split(os.path.sep)
           
    # Work out how much of the filepath is shared by start and path.
    i = len(commonprefix([start_list, path_list]))
           
    rel_list = [os.pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return ''
    return os.path.join(*rel_list)

