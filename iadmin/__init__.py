
__version__ = (0, 1, 8, 'alpha')
__author__ = 'sax'

def get_version(version=None):
    """Derives a PEP386-compliant version number from VERSION."""
    if version is None:
        version = __version__
    assert len(version) == 5
    assert version[3] in ('alpha', 'beta', 'rc', 'final')

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for alpha, beta and rc releases

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])

    sub = ''
    if version[3] == 'alpha' and version[4] == 0:
        # At the toplevel, this would cause an import loop.
        from django.utils.version import get_svn_revision
        svn_revision = get_svn_revision()[4:]
        if svn_revision != 'unknown':
            sub = '.dev%s' % svn_revision

    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])

    return main + sub

#def get_version(release=True):
#    version = '%s.%s' % (__version__[0], __version__[1])
#
#    if release:
#        if __version__[2]:
#            version = '%s.%s' % (version, __version__[2])
#        if __version__[3] != 'final':
#            version = '%s-%s' % (version, __version__[3])
#    return version


