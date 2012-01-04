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

#@register.inclusion_tag('admin/submit_line.html', takes_context=True)
#def submit_row(context):
#    """
#    Displays the row of buttons for delete and save.
#    """
#    opts = context['opts']
#    change = context['change']
#    is_popup = context['is_popup']
#    save_as = context['save_as']
#    return {
#        'onclick_attrib': (opts.get_ordered_objects() and change
#                            and 'onclick="submitOrderForm();"' or ''),
#        'show_delete_link': (not is_popup and context['has_delete_permission']
#                              and (change or context['show_delete'])),
#        'show_save_as_new': not is_popup and change and save_as,
#        'show_save_and_add_another': context['has_add_permission'] and
#                            not is_popup and (not save_as or context['add']),
#        'show_save_and_continue': not is_popup and context['has_change_permission'],
#        'is_popup': is_popup,
#        'show_save': context['has_change_permission']
#    }