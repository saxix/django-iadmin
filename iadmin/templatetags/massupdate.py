from django.template import Library
from django.utils.safestring import mark_safe

register = Library()

def fields_values(d, k):
    """
    Returns the string contained in the setting ADMIN_MEDIA_PREFIX.
    """
    values = d.get(k,[])
    return ",".join(map(str,values))

fields_values = register.simple_tag(fields_values)


def link_fields_values(d, k):
    """
    Returns the string contained in the setting ADMIN_MEDIA_PREFIX.
    """
    ret = []
    for v in d.get(k,[]):
        if v == '': # ignore empty
            continue
        ret.append('<a href="#" class="fastfieldvalue %s">%s</a>' % (k,str(v)))
        
    return mark_safe(", ".join(ret))

link_fields_values = register.simple_tag(link_fields_values)
