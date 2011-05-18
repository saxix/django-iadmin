#!/usr/bin/env python
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
import os

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

def scan_dir( target, packages = [], data_files=[] ):
    for dirpath, dirnames, filenames in os.walk(target):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])
    return packages, data_files

packages, data_files = scan_dir( 'iadmin' )

setup(
    name = "django-iadmin",
    version = '0.1dev',
#    url = 'http://alaska.k-tech.it/',
#    download_url = 'http://alaska.k-tech.it/pypi/pasportng/',
    author = 'sax',
    author_email = 'sax@k-tech.it',
    license='BSD',
#    description = 'WFP Salary Calculation',
#    packages = packages,
#    cmdclass = cmdclasses,
    data_files = data_files,
    include_package_data=True,
    platforms = ['any'],
    zip_safe=False,
    install_requires=[
        'djangodevtools>=0.3dev',
        'distribute==0.6.14',
        'Wfp-Kiowa>=0.3.1',
        'suds==0.4',
        'pisa==3.0.33',
        "lxml==2.2.4",
        "pil==1.1.7",
        "pypdf==1.12",
        "reportlab==2.5",
        'python-dateutil==1.5',
        'twill==0.9',
        'django-test-utils==0.3',
        'html5lib==0.11.1', # it's not a direct dependency but must be here because the dependency_links
    ],

    classifiers = ['Development Status :: 5 - Production/Stable',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   ],
    long_description = \
"""
""",

)
