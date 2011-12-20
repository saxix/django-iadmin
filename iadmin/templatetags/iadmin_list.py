from django.conf import settings
from django.db.models.base import Model
from django.template.loader import get_template, select_template
from django.template.context import Context, RequestContext, ContextPopException

from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.admin.templatetags.admin_list import *
from django.utils import simplejson
from django.utils.translation import ugettext as _


register = Library()

def iter_get_attr(obj, attr, default=None):
    """Recursive get object's attribute. May use dot notation.

    >>> class C(object): pass
    >>> a = C()
    >>> a.b = C()
    >>> a.b.c = 4
    >>> iter_get_attr(a, 'b.c')
    4
    """
    if '.' not in attr:
        return getattr(obj, attr, default)
    else:
        L = attr.split('.')
        return iter_get_attr(getattr(obj, L[0], default), '.'.join(L[1:]), default)
    
def iadmin_list_filter(cl, spec):
    if hasattr(spec, "USE_OUTPUT_FUNC"):
        return spec.output(cl)
    else:
        ctx = {'title': spec.title,
               'choices': list(spec.choices(cl))
        }
        t = get_template('admin/filter.html')
        return t.render(Context(ctx))


iadmin_list_filter = register.simple_tag(iadmin_list_filter)

import django.contrib.admin.templatetags.admin_list as al
al__result_headers = al.result_headers
def result_headers(cl):
    # this allow us to be ready for django 1.4
    original = al__result_headers(cl)
    for i, original_data in enumerate(original):
#        original_data['text'] = i
        yield original_data
al.result_headers = result_headers
#
#def __result_headers(cl):
#    """
#    Generates the list column headers.
#    """
#    cl._filtered_on = []
#    first = True
#    for i, field_name in enumerate(cl.list_display):
#        header, attr = label_for_field(field_name, cl.model,
#                                       model_admin=cl.model_admin,
#                                       return_attr=True
#        )
#
#        if attr:
#            # if the field is the action checkbox: no sorting and special class
#            if field_name == 'action_checkbox':
#                yield {
#                    "text": header,
#                    "class_attrib": mark_safe(' class="action-checkbox-column"')
#                }
#                continue
#
#            # It is a non-field, but perhaps one that is sortable
#            admin_order_field = getattr(attr, "admin_order_field", None)
#            if not admin_order_field:
#                yield {"text": header}
#                continue
#
#                # So this _is_ a sortable non-field.  Go to the yield
#                # after the else clause.
#        else:
#            admin_order_field = ''
#
#        th_classes = []
#        if first and cl.model_admin.list_filter:
#            first = False
#            th_classes = ['elastic']
#        new_order_type = 'asc'
#        if field_name == cl.order_field or admin_order_field == cl.order_field:
#            th_classes.append('sorted %sending' % cl.order_type.lower())
#            new_order_type = {'asc': 'desc', 'desc': 'asc'}[cl.order_type.lower()]
#
#        if hasattr(cl.model_admin, 'columns_classes'):
#            th_classes.extend(cl.model_admin.columns_classes.get(field_name, ''))
#
#        keys = cl.params.keys()
#        for k in keys:
#            parts = k.split('__')
#            op = parts[-1]
#            target = k.replace('__', '_')
#            if '%s_' % field_name in target:
#                if target == ('%s_exact' % field_name) or target == ('%s_id_exact' % field_name):
#                    filtered = True
#                    sortable = False
#                    clear_filter_url = cl.get_query_string(remove=[k])
#                    break
#                elif op in ('not', 'lt', 'gt'):
#                    filtered = True
#                    sortable = True
#                    clear_filter_url = cl.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: new_order_type},remove=[k])
#                    url = cl.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: new_order_type})
#                    break
#            else:
#                filtered = False
#                sortable = True
#                clear_filter_url = ''
#                url = cl.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: new_order_type})
#        else:
#            filtered = False
#            sortable = True
#            clear_filter_url = ''
#            url = cl.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: new_order_type})
#
#        class_attrib = mark_safe(th_classes and ' class="%s"' % ' '.join(th_classes) or '')
#
#        yield {
#            "text": header,
#            "filtered": filtered,
#            "sortable": sortable,
#            "url": url,
#            "clear_filter_url": clear_filter_url,
#            "class_attrib": class_attrib
#        }
#
#CELL_FILTER_ICON = 'funnel_add.png'
#
#
def process_cell_filter(cl, field, attr, value, obj):
    labels = {'lt': _('Less than'),
              'gt': _('Greater than'),
              'lte': _('Less or equals than'),
              'gte': _('Greater or equals than'),
              'exact': _('Equals to'),
              'not': _('Not equals to'),
              'rem': _('Remove filter')}

    default_operators = ('exact', 'not')

    def process_field():
        target = field or  attr
        if field:
            col_operators = cl.model_admin.cell_filter_operators.get(field.name, default_operators)
        elif attr:
            col_operators = getattr(target, 'cell_filter_operators', default_operators)
        

        if hasattr(attr, 'cell_filter_func'):
            return 'TODO', 'TODO'
        elif hasattr(attr, 'admin_order_field'):
            target_field_name = getattr(attr, 'admin_order_field')
            parts = target_field_name.split('__')
            t = ".".join(parts)
            linked_object = iter_get_attr(obj, t )
            if isinstance(t, Model):
                return target_field_name, linked_object.pk, col_operators
            else:
                return target_field_name, linked_object, col_operators

        elif field:
            target = getattr(obj, field.name)
            if isinstance(field.rel, models.ManyToOneRel):
                rel_name = field.rel.get_related_field().name
                return '%s__%s' % (field.name, rel_name), target.pk, col_operators
            else:
                return field.name, target, col_operators
        elif settings.DEBUG:
            # todo add link to docs
            return " Unable to create cell filter for field '%s' on value '%s'" % ( field, value), '', []
        else:
            return ''

    lookup_kwarg, lookup_value, operators = process_field()
    if lookup_kwarg is None:
        return ''

    menu_items = []
    active_filters = ",".join ( cl.params.keys() )
    if lookup_kwarg in active_filters:
        menu_items.append((cl.get_query_string({}, [lookup_kwarg]),labels['rem']))

    for op in operators:
        fld = mark_safe(u"%s__%s" % (lookup_kwarg, op))
        url = cl.get_query_string({fld: lookup_value}, [lookup_kwarg])
        menu_items.append((url, labels[op]))

    items = "".join(
        ['<li class="iadmin-cell-menu-item" ><a href="%s">%s</a></li>' % (url, lbl) for url, lbl in menu_items])

#    items = "".join(
#        ['<li class="iadmin-cell-menu-item" ><span>"%s">%s</span></li>' % (url, lbl) for url, lbl in menu_items])

    if items:
        return r'''<div class="cell-menu">
        <ul>
        <li><a href="#" class="cell-menu-button">&nbsp;</a>
            <ul class="iadmin-cell-menu">%s</ul>
        </ul></div>''' % items
    else:
        return ''
#
#
def items_for_result(cl, result, form, context=None):
    """
    Generates the actual list of data.
    """
    def handle_link():
        if (field_name in model_admin.list_display_rel_links):
            if admin_order_field:
                linked_object = iter_get_attr(result, admin_order_field.replace('__','.'))
            else:
                linked_object = getattr(result, field_name) #f.rel.to
            return mark_safe( cl.url_for_obj(context['request'], linked_object) )
        return mark_safe('')


    first = True
    pk = cl.lookup_opts.pk.attname
    model_admin = cl.model_admin
    for field_name in cl.list_display:
        row_class = ''
        result_repr = ''
        cell_filter_menu = ''
        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except (AttributeError, ObjectDoesNotExist):
            result_repr = EMPTY_CHANGELIST_VALUE
        else:
            admin_order_field = getattr(attr, "admin_order_field", None)
            if f is None: # no field maybe modeladmin method
                if field_name == u'action_checkbox':
                    row_class = ' class="action-checkbox"'

                allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)

#                custom_filter = getattr(attr, 'cell_filter_func', False)

                if boolean:
                    allow_tags = True
                    result_repr = _boolean_icon(value)
                else:
                    result_repr = smart_unicode(value)
                    # Strip HTML tags in the resulting text, except if the
                # function has an "allow_tags" attribute set to True.
                if not allow_tags:
                    result_repr = escape(result_repr)
                else:
                    result_repr = mark_safe(result_repr)
            else:
                if isinstance(f.rel, models.ManyToOneRel):
                    field_val = getattr(result, f.name)
                    if field_val is None:
                        result_repr = EMPTY_CHANGELIST_VALUE
                    else:
                        result_repr = escape(field_val)
                else:
                    result_repr = display_for_field(value, f)
                if isinstance(f, models.DateField)\
                or isinstance(f, models.TimeField)\
                or isinstance(f, models.ForeignKey):
                    row_class = ' class="nowrap"'

        link = handle_link()

        if hasattr(model_admin, 'cell_filter') and (field_name not in  cl._filtered_on) \
                                                and field_name in model_admin.cell_filter:
            a = process_cell_filter(cl, f, attr, value, result)
            cell_filter_menu = smart_unicode(mark_safe(a))

        if force_unicode(result_repr) == '':
            result_repr = mark_safe('&nbsp;')

        # If list_display_links not defined, add the link tag to the first field
        if (first and not cl.list_display_links) or field_name in cl.list_display_links:
            table_tag = {True: 'th', False: 'td'}[first]
            first = False
            url = cl.url_for_result( result )
            # Convert the pk to something that can be used in Javascript.
            # Problem cases are long ints (23L) and non-ASCII strings.
            if cl.to_field:
                attr = str(cl.to_field)
            else:
                attr = pk
            value = result.serializable_value(attr)
            result_id = repr(force_unicode(value))[1:]
            yield mark_safe(u'<%s%s><a href="%s"%s>%s</a> %s %s</%s>' %\
                            (table_tag, row_class, url, (
                                cl.is_popup and ' onclick="opener.dismissRelatedLookupPopup(window, %s); return false;"' % result_id or '')
                             , conditional_escape(result_repr), link,  conditional_escape(cell_filter_menu), table_tag))
        else:
            # By default the fields come from ModelAdmin.list_editable, but if we pull
            # the fields out of the form instead of list_editable custom admins
            # can provide fields on a per request basis
            if form and field_name in form.fields:
                bf = form[field_name]
                result_repr = mark_safe(force_unicode(bf.errors) + force_unicode(bf))
            else:
                result_repr = '%s%s%s' % (conditional_escape(result_repr), link, conditional_escape( cell_filter_menu ))
            yield mark_safe(u'<td%s>%s</td>' % (row_class, result_repr))

    if form and not form[cl.model._meta.pk.name].is_hidden:
        yield mark_safe(u'<td>%s</td>' % force_unicode(form[cl.model._meta.pk.name]))

al.items_for_result = items_for_result

#def results(cl, context):
#    if cl.formset:
#        for res, form in zip(cl.result_list, cl.formset.forms):
#            yield ResultList(form, items_for_result(cl, res, form))
#    else:
#        for res in cl.result_list:
#            yield ResultList(None, items_for_result(cl, res, None, context=context))

#@register.inclusion_tag("admin/change_list_results.html", takes_context=True)
#def result_list(context, cl):
#    """
#    Displays the headers and data list together
#    """
#    headers = list(result_headers(cl))
#    for h in headers:
#        # Sorting in templates depends on sort_pos attributeue
#        h.setdefault('sort_pos', 0)
#    return {'cl': cl,
#            'result_hidden_fields': list(result_hidden_fields(cl)),
#            'result_headers': headers,
#            'reset_sorting_url': cl.get_query_string(remove=[ORDER_VAR]),
#            'results': list(results(cl, context))}
#
#
#def result_hidden_fields(cl):
#    if cl.formset:
#        for res, form in zip(cl.result_list, cl.formset.forms):
#            if form[cl.model._meta.pk.name].is_hidden:
#                yield mark_safe(force_unicode(form[cl.model._meta.pk.name]))
#
#
##@register.inclusion_tag("iadmin/change_list_results.html")
##def result_list(cl):
##    headers = list(result_headers(cl))
##    for h in headers:
##        # Sorting in templates depends on sort_pos attribute
##        h.setdefault('sort_pos', 0)
##    return {'cl': cl,
##            'result_hidden_fields': list(result_hidden_fields(cl)),
##            'result_headers': headers,
##            'reset_sorting_url': cl.get_query_string(remove=[ORDER_VAR]),
##            'results': list(results(cl))}
#
##    """
##    Displays the headers and data list together
##    """
##    return {'cl': cl,
##            'result_hidden_fields': list(result_hidden_fields(cl)),
##            'result_headers': list(result_headers(cl)),
##            'results': list(results(cl))}
#
#result_list = register.inclusion_tag("iadmin/change_list_results.html")(al.result_list)

@register.inclusion_tag('iadmin/tools.html', takes_context=True)
def admin_tools(context):
    """
    Track the number of times the action field has been rendered on the page,
    so we know which value to use.
    """
    context['tool_index'] = context.get('tool_index', -1) + 1
    return context