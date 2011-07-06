from django.template.loader import get_template, select_template
from django.template.context import Context, RequestContext, ContextPopException

from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.admin.templatetags.admin_list import *
from django.utils import simplejson
from django.utils.translation import ugettext as _

register = Library()

def iadmin_list_filter(cl, spec):
    if hasattr(spec, "USE_OUTPUT_FUNC"):
        return spec.output(cl)
    else:
        ctx = {'title': spec.title(),
               'choices': list(spec.choices(cl))
        }
        t = get_template('admin/filter.html')
        return t.render(Context(ctx))


iadmin_list_filter = register.simple_tag(iadmin_list_filter)


def result_headers(cl):
    """
    Generates the list column headers.
    """
    cl._filtered_on = []
    first = True
    for i, field_name in enumerate(cl.list_display):
        header, attr = label_for_field(field_name, cl.model,
                                       model_admin=cl.model_admin,
                                       return_attr=True
        )

        if attr:
            # if the field is the action checkbox: no sorting and special class
            if field_name == 'action_checkbox':
                yield {
                    "text": header,
                    "class_attrib": mark_safe(' class="action-checkbox-column"')
                }
                continue

            # It is a non-field, but perhaps one that is sortable
            admin_order_field = getattr(attr, "admin_order_field", None)
            if not admin_order_field:
                yield {"text": header}
                continue

                # So this _is_ a sortable non-field.  Go to the yield
                # after the else clause.
        else:
            admin_order_field = ''

        th_classes = []
        if first and cl.model_admin.list_filter:
            first = False
            th_classes = ['elastic']
        new_order_type = 'asc'
        if field_name == cl.order_field or admin_order_field == cl.order_field:
            th_classes.append('sorted %sending' % cl.order_type.lower())
            new_order_type = {'asc': 'desc', 'desc': 'asc'}[cl.order_type.lower()]

        if hasattr(cl.model_admin, 'columns_classes'):
            th_classes.extend(cl.model_admin.columns_classes.get(field_name, ''))

        keys = cl.params.keys()
        for k in keys:
            parts = k.split('__')
            op = parts[-1]
            target = k.replace('__', '_')
            if '%s_' % field_name in target:
                if target == ('%s_exact' % field_name) or target == ('%s_id_exact' % field_name):
                    filtered = True
                    sortable = False
                    clear_filter_url = cl.get_query_string(remove=[k])
                    break
                elif op in ('not', 'lt', 'gt'):
                    filtered = True
                    sortable = True
                    clear_filter_url = cl.get_query_string(remove=[k])
                    break
            else:
                filtered = False
                sortable = True
                clear_filter_url = ''
                url = cl.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: new_order_type})
        else:
            filtered = False
            sortable = True
            clear_filter_url = ''
            url = cl.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: new_order_type})

        class_attrib = mark_safe(th_classes and ' class="%s"' % ' '.join(th_classes) or '')

        yield {
            "text": header,
            "filtered": filtered,
            "sortable": sortable,
            "url": url,
            "clear_filter_url": clear_filter_url,
            "class_attrib": class_attrib
        }

CELL_FILTER_ICON = 'funnel_add.png'


def process_cell_filter(cl, field, attr, value, obj):
    labels = {'lt': _('Less than'),
              'gt': _('Greater than'),
              'lte': _('Less or equals than'),
              'gte': _('Greater or equals than'),
              'exact': _('Equals to'),
              'not': _('Not equals to'),
              'rem': _('Remove filter')}

#    default_operators = ('lt', 'gt', 'exact', 'not')
    default_operators = ('exact', 'not')

    def process_field():
        target = field or  attr
        col_operators = getattr(target, 'cell_filter_operators', default_operators)

        if hasattr(attr, 'cell_filter_func'):
            return 'TODO', 'TODO'
        elif hasattr(attr, 'admin_order_field'):
            target_field_name = getattr(attr, 'admin_order_field')
            return target_field_name, value, col_operators
        elif field:
            target = getattr(obj, field.name)
            if not (obj and target):
                return '', '', []
            if isinstance(field.rel, models.ManyToOneRel):
                rel_name = field.rel.get_related_field().name
                return '%s__%s' % (field.name, rel_name), target.pk, col_operators
            else:
                return field.name, target, col_operators
        elif settings.DEBUG:
            # todo add link to docs
            return " Unable to create cell filter for field '%s' on value '%s'" % ( field, value), '', []


    lookup_kwarg, lookup_value, operators = process_field()
    if not lookup_kwarg:
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

    return r'''<div class="cell-menu">
    <ul>
    <li><a href="#" class="cell-menu-button">&nbsp;</a>
        <ul class="iadmin-cell-menu">%s</li></ul>
    </ul></div>''' % items


def items_for_result(cl, result, form):
    """
    Generates the actual list of data.
    """
    first = True
    pk = cl.lookup_opts.pk.attname
    model_admin = cl.model_admin
    for field_name in cl.list_display:
        row_class = ''

        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except (AttributeError, ObjectDoesNotExist):
            result_repr = EMPTY_CHANGELIST_VALUE
        else:
            if f is None: # no field maybe modeladmin method
                allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)
                custom_filter = getattr(attr, 'cell_filter_func', False)

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
                    result_repr = escape(getattr(result, f.name))
                    if hasattr(model_admin, 'list_display_rel_links') and f.name in model_admin.list_display_rel_links:
                        result_repr += mark_safe(model_admin.admin_site._link_to_model(getattr(result, f.name)))
                else:
                    result_repr = display_for_field(value, f)

                if isinstance(f, models.DateField) or isinstance(f, models.TimeField):
                    row_class = ' class="nowrap"'

        if hasattr(model_admin, 'cell_filter') and (
            field_name not in  cl._filtered_on) and field_name in model_admin.cell_filter:
            a = process_cell_filter(cl, f, attr, value, result)
            result_repr = (result_repr, smart_unicode(mark_safe(a)))
        else:
            result_repr = (result_repr, '')

        if force_unicode(result_repr[0]) == '':
            result_repr = (mark_safe('&nbsp;'), '')
            # If list_display_links not defined, add the link tag to the first field
        if (first and not cl.list_display_links) or field_name in cl.list_display_links:
            table_tag = {True: 'th', False: 'td'}[first]
            first = False
            url = cl.url_for_result(result)
            # Convert the pk to something that can be used in Javascript.
            # Problem cases are long ints (23L) and non-ASCII strings.
            if cl.to_field:
                attr = str(cl.to_field)
            else:
                attr = pk
            value = result.serializable_value(attr)
            result_id = repr(force_unicode(value))[1:]
            yield mark_safe(u'<%s%s><a href="%s"%s>%s</a>%s</%s>' %\
                            (table_tag, row_class, url, (
                                cl.is_popup and ' onclick="opener.dismissRelatedLookupPopup(window, %s); return false;"' % result_id or '')
                             , conditional_escape(result_repr[0]), conditional_escape(result_repr[1]), table_tag))
        else:
            # By default the fields come from ModelAdmin.list_editable, but if we pull
            # the fields out of the form instead of list_editable custom admins
            # can provide fields on a per request basis
            if form and field_name in form.fields:
                bf = form[field_name]
                result_repr = mark_safe(force_unicode(bf.errors) + force_unicode(bf))
            else:
                result_repr = '%s%s' % (conditional_escape(result_repr[0]), conditional_escape(result_repr[1]))
            yield mark_safe(u'<td%s>%s</td>' % (row_class, result_repr))
    if form and not form[cl.model._meta.pk.name].is_hidden:
        yield mark_safe(u'<td>%s</td>' % force_unicode(form[cl.model._meta.pk.name]))


def results(cl):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            yield list(items_for_result(cl, res, form))
    else:
        for res in cl.result_list:
            yield list(items_for_result(cl, res, None))


def result_hidden_fields(cl):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            if form[cl.model._meta.pk.name].is_hidden:
                yield mark_safe(force_unicode(form[cl.model._meta.pk.name]))


def result_list(cl):
    """
    Displays the headers and data list together
    """
    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': list(result_headers(cl)),
            'results': list(results(cl))}

result_list = register.inclusion_tag("iadmin/change_list_results.html")(result_list)