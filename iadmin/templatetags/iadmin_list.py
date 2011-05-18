from django.conf import settings
from django.contrib.admin.views.main import ALL_VAR, EMPTY_CHANGELIST_VALUE
from django.contrib.admin.views.main import ORDER_VAR, ORDER_TYPE_VAR, PAGE_VAR, SEARCH_VAR
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import dateformat
from django.utils.html import escape, conditional_escape
from django.utils.text import capfirst
from django.utils.safestring import mark_safe
from django.utils.translation import get_date_formats, get_partial_date_formats, ugettext as _
from django.utils.encoding import smart_unicode, smart_str, force_unicode
from django.template import Library
import datetime
from django.template.loader import get_template, select_template
from django.template.context import Context, RequestContext, ContextPopException

register = Library()

def iadmin_list_filter(cl, spec):
    if hasattr(spec, "USE_OUTPUT_FUNC"):        
        return spec.output(cl)
    else:
        ctx =  {'title': spec.title(), 
                'choices' : list(spec.choices(cl))
                }
        t = get_template('admin/filter.html')
        return t.render(Context(ctx))


iadmin_list_filter = register.simple_tag(iadmin_list_filter)

#def xsearch_form(cl, search_help_text=''):
#    return {
#        'search_help_text': search_help_text ,
#        'cl': cl,
#        'show_result_count': cl.result_count != cl.full_result_count,
#        'search_var': SEARCH_VAR
#    }
#xsearch_form = register.inclusion_tag('admin/search_form.html')(xsearch_form)

