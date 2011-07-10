__version__ = (0, 1, 8, 'alpha')
__author__ = 'sax'


def get_version(release=True):
    version = '%s.%s' % (__version__[0], __version__[1])

    if release:
        if __version__[2]:
            version = '%s.%s' % (version, __version__[2])
        if __version__[3] != 'final':
            version = '%s-%s' % (version, __version__[3])
    return version