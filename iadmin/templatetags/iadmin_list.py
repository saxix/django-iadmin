from django.template.loader import get_template, select_template
from django.template.context import Context, RequestContext, ContextPopException

from django.contrib.admin.templatetags.admin_list import *

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



def result_headers(cl):
    """
    Generates the list column headers.
    """
    cl._filtered_on = []
    first = True
    for i, field_name in enumerate(cl.list_display):
        header, attr = label_for_field(field_name, cl.model,
            model_admin = cl.model_admin,
            return_attr = True
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
            admin_order_field = None

        th_classes = []
        if first and cl.model_admin.list_filter:
            first = False
            th_classes = ['elastic']
        new_order_type = 'asc'
        if field_name == cl.order_field or admin_order_field == cl.order_field:
            th_classes.append('sorted %sending' % cl.order_type.lower())
            new_order_type = {'asc': 'desc', 'desc': 'asc'}[cl.order_type.lower()]

        if hasattr(cl.model_admin, 'columns_classes'):
            th_classes.extend( cl.model_admin.columns_classes.get(field_name, '') )

        keys = cl.params.keys()
        for check in [admin_order_field, field_name, '%s__id' % field_name]:
            if check in keys:
                filtered = True
                url = cl.get_query_string(remove=[check])
                th_classes.append( 'filtered' )
                cl._filtered_on.append( field_name )
                break
            else:
                filtered = False
                url = cl.get_query_string({ORDER_VAR: i, ORDER_TYPE_VAR: new_order_type})

        class_attrib = mark_safe(th_classes and ' class="%s"' % ' '.join(th_classes) or '')

        yield {
            "text": header,
            "filtered": filtered,
            "sortable": True,
            "url": url,
            "class_attrib" : class_attrib
        }

            
def items_for_result(cl, result, form):
    """
    Generates the actual list of data.
    """
    first = True
    pk = cl.lookup_opts.pk.attname

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

                # show funnel.png if not active filter
#                if hasattr(cl.model_admin, 'cell_filter') and (field_name not in cl._filtered_on) and field_name in cl.model_admin.cell_filter:
#                    a =  cl._cell_filter(result, field_name)
#                    b =  result_repr
#                    result_repr =  mark_safe(b + smart_unicode(mark_safe(a)))

            else:
                if isinstance(f.rel, models.ManyToOneRel):
                    result_repr = escape(getattr(result, f.name))
                    if f.name in cl.model_admin.list_display_rel_links:
                        result_repr += mark_safe(cl._link_to_model(getattr(result, f.name)))
                else:
                    result_repr = display_for_field(value, f)

                if isinstance(f, models.DateField) or isinstance(f, models.TimeField):
                    row_class = ' class="nowrap"'

        if hasattr(cl.model_admin, 'cell_filter') and (field_name not in  cl._filtered_on) and field_name in cl.model_admin.cell_filter:
            a =  cl._cell_filter(result, field_name)
#            b =  result_repr
            result_repr = (result_repr,  smart_unicode(mark_safe(a)))
        else:
            result_repr = (result_repr,  '')

        if force_unicode(result_repr[0]) == '':
            result_repr = (mark_safe('&nbsp;'), '')
        # If list_display_links not defined, add the link tag to the first field
        if (first and not cl.list_display_links) or field_name in cl.list_display_links:
            table_tag = {True:'th', False:'td'}[first]
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
            yield mark_safe(u'<%s%s><a href="%s"%s>%s</a>%s</%s>' % \
                (table_tag, row_class, url, (cl.is_popup and ' onclick="opener.dismissRelatedLookupPopup(window, %s); return false;"' % result_id or ''), conditional_escape(result_repr[0]), conditional_escape(result_repr[1]), table_tag))
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
result_list = register.inclusion_tag("admin/change_list_results.html")(result_list)