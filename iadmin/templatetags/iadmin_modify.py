#
__author__ = 'sax'

from django.contrib.admin.templatetags.admin_modify import *


def class_if_errors(error_list, classname):
    """
        siplet tool to check if
    >>> class_if_errors([{},{}],"class")
    ""
    >>> class_if_errors([{1:1},{}],"class")
    "class"
    """
    for el in error_list:
        if el != {}:
            return classname
    return ""
class_if_errors = register.simple_tag(class_if_errors)