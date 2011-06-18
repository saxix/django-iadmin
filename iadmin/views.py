#
from django.conf import settings
from django.contrib.admin.util import lookup_field
from django.db import models

__author__ = 'sax'


from django.contrib.admin.views.main import ChangeList

class IChangeList(ChangeList):
    pass
