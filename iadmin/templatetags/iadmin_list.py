from django.contrib.admin.util import lookup_field, display_for_field, quote
from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.base import Model
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode, force_unicode

from django.contrib.admin.templatetags.admin_list import register, result_hidden_fields, _boolean_icon
import django.contrib.admin.templatetags.admin_list as al
from iadmin.utils import Null, iter_get_attr


al__result_headers = al.result_headers

def iresult_headers(cl):
    original = list(al__result_headers(cl))

    for i, field_name in enumerate(cl.list_display):
        filter = cl.cell_filters.get(field_name, Null())
        original_data = original[i]
        if filter.is_active(cl):
            original_data['filtered'] = True
            original_data['clear_filter_url'] = cl.get_query_string({}, filter.expected_parameters())
        yield original_data


def get_items_cell_filter(cl, column, obj):
    menu_items = []
    filter = cl.cell_filters.get(column, None)
    if filter:
        filter_params = filter.expected_parameters()
        if filter.is_active(cl):
            menu_items.append((cl.get_query_string({}, filter_params), _('Remove filter')))

        for op in filter.col_operators:
            label, param = filter.get_menu_item_for_op(op)
            value = iter_get_attr(obj, filter.seed.replace('__', '.'))
            url = cl.get_query_string({param: value}, filter_params)
            menu_items.append((url, label))
    return menu_items


def get_popup_menu(items):
    menu_items = "".join(
        ['<li class="iadmin-cell-menu-item" ><a href="%s">%s</a></li>' % (url, lbl) for url, lbl in items if url])

    if menu_items:
        return '''<div class="iadmin-cell-menu-container"><span class="iadmin-cell-menu-button">&nbsp;</span><ul class="iadmin-cell-menu">%s</ul></div>''' % menu_items
    else:
        return ''


def iitems_for_result(cl, result, form, context=None):
    """
    Generates the actual list of data.
    """

    def handle_link():
        if field_name in model_admin.list_display_rel_links:
            if admin_order_field:
                linked_object = iter_get_attr(result, admin_order_field.replace('__', '.'))
            else:
                linked_object = getattr(result, field_name) #f.rel.to
            return mark_safe(cl.url_for_obj(context['request'], linked_object))
        return mark_safe('')


    first = True
    pk = cl.lookup_opts.pk.attname
    model_admin = cl.model_admin
    for field_name in cl.list_display:
        row_class = ''
        result_repr = ''
        cell_filter_menu = ''
        cell_menu_items = []
        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except (AttributeError, ObjectDoesNotExist):
            result_repr = EMPTY_CHANGELIST_VALUE
        else:
            admin_order_field = getattr(attr, "admin_order_field", None)
            if f is None: # no field maybe modeladmin method
                if field_name == u'action_checkbox':
                    row_class = ' action-checkbox'

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
                    row_class = ' nowrap'

                #        link = handle_link()
        cell_menu_items = []

        if field_name in model_admin.list_display_rel_links:
            if admin_order_field:
                linked_object = iter_get_attr(result, admin_order_field.replace('__', '.'))
            else:
                linked_object = getattr(result, field_name) #f.rel.to
            if linked_object and isinstance(linked_object, Model):
                if model_admin.has_change_permission(context['request'], linked_object):
                    view = "%s:%s_%s_change" % (
                    model_admin.admin_site.app_name, linked_object._meta.app_label, linked_object.__class__.__name__.lower())
                    url = reverse(view, args=[int(linked_object.pk)])
                elif model_admin.has_view_permission(context['request'], linked_object):
                    url = "view/%s/" % quote(getattr(linked_object, linked_object._meta.pk_attname))

                cell_menu_items.append([url, _("Jump to detail")])

        if hasattr(model_admin, 'cell_filter') and field_name in model_admin.cell_filter:
            cell_menu_items.extend(get_items_cell_filter(cl, field_name, result))

        cell_filter_menu = smart_unicode(mark_safe(get_popup_menu(cell_menu_items)))

        if row_class:
            row_class = ' class="%s"' % row_class

        if force_unicode(result_repr) == '':
            result_repr = mark_safe('&nbsp;')

        #        menu = mark_safe('%s%s' % (link, conditional_escape( cell_filter_menu )))
        menu = conditional_escape(cell_filter_menu)
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
            yield mark_safe(u'<%s%s>%s<a href="%s"%s>%s</a></%s>' %\
                            (table_tag, row_class, menu, url, (
                                cl.is_popup and ' onclick="opener.dismissRelatedLookupPopup(window, %s); return false;"' % result_id or '')
                             , conditional_escape(result_repr), table_tag))
        else:
            # By default the fields come from ModelAdmin.list_editable, but if we pull
            # the fields out of the form instead of list_editable custom admins
            # can provide fields on a per request basis
            if form and field_name in form.fields:
                bf = form[field_name]
                result_repr = mark_safe(force_unicode(bf.errors) + force_unicode(bf))
                yield mark_safe(u'<td%s>%s</td>' % (row_class, result_repr))
            else:
                yield mark_safe(u'<td>%s<span%s>%s</span></td>' % (menu, row_class, result_repr))

    if form and not form[cl.model._meta.pk.name].is_hidden:
        yield mark_safe(u'<td>%s</td>' % force_unicode(form[cl.model._meta.pk.name]))


def iresults(cl, context):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            yield al.ResultList(form, iitems_for_result(cl, res, form))
    else:
        for res in cl.result_list:
            yield al.ResultList(None, iitems_for_result(cl, res, None, context=context))


@register.inclusion_tag("iadmin/change_list_results.html", takes_context=True)
def iresult_list(context, cl):
    """
    Displays the headers and data list together
    """
    headers = list(iresult_headers(cl))
    num_sorted_fields = 0
    for h in headers:
        if h['sortable'] and h['sorted']:
            num_sorted_fields += 1
    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': headers,
            'num_sorted_fields': num_sorted_fields,
            'results': list(iresults(cl, context))}
