import django
from django.conf.urls.defaults import patterns, url
from django.contrib.admin import ModelAdmin as DjangoModelAdmin, TabularInline as DjangoTabularInline, helpers
from django.contrib.admin.options import IncorrectLookupParameters, csrf_protect_m
from django.contrib.admin.util import flatten_fieldsets, unquote
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models.fields import AutoField
from . import widgets
from . import actions as ac
from django.db.models.sql.constants import LOOKUP_SEP, QUERY_TERMS
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template.response import TemplateResponse, SimpleTemplateResponse
from django.utils.encoding import force_unicode
from django.utils.functional import update_wrapper
from django.db import models, transaction
from . import ajax
from django.utils.html import escape
from django.utils.safestring import mark_safe
import logging
from .views import IChangeList
import django.utils.simplejson as json
from iadmin.widgets import RelatedFieldWidgetWrapperLinkTo
from django.utils.translation import ugettext as _, ungettext
import django.core.serializers

__all__ = ['IModelAdmin', 'ITabularInline']

AUTOCOMPLETE = 'a'
JSON = 'j'
PJSON = 'p'

class IModelAdmin(DjangoModelAdmin):
    """
        extended ModelAdmin
    """
    add_undefined_fields = False
    list_display_rel_links = ()
    cell_filter = ()
    cell_menu_on_click = False # if true need to click on icon else mouseover is enough
    ajax_search_fields = None
    ajax_list_display = None # always use searchable fields. Never __str__ ol similar
    autocomplete_ajax = False
    #    change_form_template = 'iadmin/change_form_tab.html'
    actions = [ac.mass_update, ac.export_to_csv, ac.export_as_json, ac.graph_queryset]
    columns_classes = {}
    columns_attributes = {}
    cell_filter_operators = {}


    def __init__(self, model, admin_site):
        self.ajax_search_fields = self.ajax_search_fields or self.search_fields
        self.ajax_list_display = self.ajax_list_display or self.ajax_search_fields
        self.extra_allowed_filter = []
        super(IModelAdmin, self).__init__(model, admin_site)
        self._process_cell_filter()

    def get_actions(self, request):
        acts = super(IModelAdmin, self).get_actions(request)
        if not self.has_delete_permission(request, None):
            acts.pop('delete_selected')
        return acts

    def has_change_permission(self, request, obj=None):
        return super(IModelAdmin, self).has_change_permission(request, obj)

    def has_view_permission(self, request, obj=None):
        opts = self.opts
        return self.has_change_permission(request, obj) or\
               request.user.has_perm(opts.app_label + '.' + 'view_%s' % self.model.__name__.lower())

#    def response_add(self, request, obj, post_url_continue='../%s/'):
#        """
#        Determines the HttpResponse for the add_view stage.
#        """
#        opts = obj._meta
#        pk_value = obj._get_pk_val()
#
#        msg = _('The %(name)s "%(obj)s" was added successfully.') % {'name': force_unicode(opts.verbose_name),
#                                                                     'obj': force_unicode(obj)}
#        # Here, we distinguish between different save types by checking for
#        # the presence of keys in request.POST.
#        if "_continue" in request.POST:
#            self.message_user(request, msg + ' ' + _("You may edit it again below."))
#            if "_popup" in request.POST:
#                post_url_continue += "?_popup=1"
#            return HttpResponseRedirect(post_url_continue % pk_value)
#
#        if "_popup" in request.POST:
#            return HttpResponse(
#                '<script type="text/javascript">opener.dismissAddAnotherPopup(window, "%s", "%s");</script>' %\
#                # escape() calls force_unicode.
#                (escape(pk_value), escapejs(obj)))
#        elif "_addanother" in request.POST:
#            self.message_user(request,
#                              msg + ' ' + (_("You may add another %s below.") % force_unicode(opts.verbose_name)))
#            return HttpResponseRedirect(request.path)
#        else:
#            self.message_user(request, msg)
#
#            # Figure out where to redirect. If the user has change permission,
#            # redirect to the change-list page for this object. Otherwise,
#            # redirect to the admin index.
#            if self.has_change_permission(request, None) or self.has_view_permission(request, None):
#                post_url = '../'
#            else:
#                post_url = '../../../'
#            return HttpResponseRedirect(post_url)

    def get_model_perms(self, request):
        """
        Returns a dict of all perms for this model. This dict has the keys
        ``add``, ``change``, and ``delete`` and ``view`` mapping to the True/False
        for each of those actions.
        """
        return {
            'add': self.has_add_permission(request),
            'change': self.has_change_permission(request),
            'delete': self.has_delete_permission(request),
            'view': self.has_view_permission(request),
            }

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        opts = self.model._meta
        app_label = opts.app_label
        target_template = None
        if add and self.add_form_template is None:
            target_template = 'add_form_template'
        elif self.change_form_template is None:
            target_template = 'change_form_template'
        if target_template:
            setattr(self, target_template, [
                "iadmin/%s/%s/change_form.html" % (app_label, opts.object_name.lower()),
                "iadmin/%s/change_form.html" % app_label,
                "iadmin/change_form.html",
                ])
        return super(IModelAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def _process_cell_filter(self):
        # add cell_filter fields to `extra_allowed_filter` list
        for entry in self.cell_filter:
            method = getattr(self, entry, None)
            if method:
                cell_filter_field = getattr(method, "admin_order_field", None)
                self.extra_allowed_filter.append(cell_filter_field)

    def lookup_allowed(self, lookup, value):
    # overriden to allow filter on cell_filter fields
    #        import django.contrib.admin.options
    #        django.contrib.admin.options.QUERY_TERMS.update({'not':'not'})
        original = super(IModelAdmin, self).lookup_allowed(lookup, value)
        if original:
            return True
        parts = lookup.split(LOOKUP_SEP)
        if len(parts) > 1 and parts[-1] in QUERY_TERMS:
            parts.pop()
        clean_lookup = LOOKUP_SEP.join(parts)
        return clean_lookup in self.extra_allowed_filter

    def changelist_view(self, request, extra_context=None):
        "The 'change list' admin view for this model."
        from django.contrib.admin.views.main import ERROR_FLAG

        opts = self.model._meta
        app_label = opts.app_label
        if not (self.has_change_permission(request, None) or self.has_view_permission(request, None)):
            raise PermissionDenied

        # Check actions to see if any are available on this changelist
        actions = self.get_actions(request)
        # Remove action checkboxes if there aren't any actions available.
        list_display = list(self.get_list_display(request))
        if not actions:
            try:
                list_display.remove('action_checkbox')
            except ValueError:
                pass

        ChangeList = self.get_changelist(request)
        try:
            cl = ChangeList(request, self.model, list_display, self.list_display_links,
                self.list_filter, self.date_hierarchy, self.search_fields,
                self.list_select_related, self.list_per_page, self.list_max_show_all, self.list_editable, self)

            cl.readonly = not self.has_change_permission(request, None)
        except IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given
            # and the 'invalid=1' parameter was already in the query string,
            # something is screwed up with the database, so display an error
            # page.
            if ERROR_FLAG in request.GET.keys():
                return SimpleTemplateResponse('admin/invalid_setup.html', {
                    'title': _('Database error'),
                    })
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

        # If the request was POSTed, this might be a bulk action or a bulk
        # edit. Try to look up an action or confirmation first, but if this
        # isn't an action the POST will fall through to the bulk edit check,
        # below.
        action_failed = False
        selected = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)


        # Actions with no confirmation
        if (actions and request.method == 'POST' and
            'index' in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(request, queryset=cl.get_query_set(request))
                if response:
                    return response
                else:
                    action_failed = True
            else:
                msg = _("Items must be selected in order to perform "
                        "actions on them. No items have been changed.")
                self.message_user(request, msg)
                action_failed = True

        # Actions with confirmation
        if (actions and request.method == 'POST' and
            helpers.ACTION_CHECKBOX_NAME in request.POST and
            'index' not in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(request, queryset=cl.get_query_set(request))
                if response:
                    return response
                else:
                    action_failed = True

        # If we're allowing changelist editing, we need to construct a formset
        # for the changelist given all the fields to be edited. Then we'll
        # use the formset to validate/process POSTed data.
        formset = cl.formset = None

        # Handle POSTed bulk-edit data.
        if (request.method == "POST" and cl.list_editable and
            '_save' in request.POST and not action_failed):
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(request.POST, request.FILES, queryset=cl.result_list)
            if formset.is_valid():
                changecount = 0
                for form in formset.forms:
                    if form.has_changed():
                        obj = self.save_form(request, form, change=True)
                        self.save_model(request, obj, form, change=True)
                        form.save_m2m()
                        change_msg = self.construct_change_message(request, form, None)
                        self.log_change(request, obj, change_msg)
                        changecount += 1

                if changecount:
                    if changecount == 1:
                        name = force_unicode(opts.verbose_name)
                    else:
                        name = force_unicode(opts.verbose_name_plural)
                    msg = ungettext("%(count)s %(name)s was changed successfully.",
                                    "%(count)s %(name)s were changed successfully.",
                                    changecount) % {'count': changecount,
                                                    'name': name,
                                                    'obj': force_unicode(obj)}
                    self.message_user(request, msg)

                return HttpResponseRedirect(request.get_full_path())

        # Handle GET -- construct a formset for display.
        elif cl.list_editable:
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(queryset=cl.result_list)

        # Build the list of media to be used by the formset.
        if formset:
            media = self.media + formset.media
        else:
            media = self.media

        # Build the action form and populate it with available actions.
        if actions:
            action_form = self.action_form(auto_id=None)
            action_form.fields['action'].choices = self.get_action_choices(request)
        else:
            action_form = None

        selection_note_all = ungettext('%(total_count)s selected',
                                       'All %(total_count)s selected', cl.result_count)

        context = {
            'module_name': force_unicode(opts.verbose_name_plural),
            'selection_note': _('0 of %(cnt)s selected') % {'cnt': len(cl.result_list)},
            'selection_note_all': selection_note_all % {'total_count': cl.result_count},
            'title': cl.title,
            'is_popup': cl.is_popup,
            'cl': cl,
            'media': media,
            'has_add_permission': self.has_add_permission(request),
            'has_view_permission': self.has_view_permission(request),
            'app_label': app_label,
            'action_form': action_form,
            'actions_on_top': self.actions_on_top,
            'actions_on_bottom': self.actions_on_bottom,
            'actions_selection_counter': self.actions_selection_counter,
            'cell_menu_on_click': self.cell_menu_on_click,
            }
        context.update(extra_context or {})

        return TemplateResponse(request, self.change_list_template or [
            'iadmin/%s/%s/change_list.html' % (app_label, opts.object_name.lower()),
            'iadmin/%s/change_list.html' % app_label,
            'iadmin/change_list.html'
        ], context, current_app=self.admin_site.name)

    #    def changelist_view(self, request, extra_context=None):
    #        opts = self.model._meta
    #        app_label = opts.app_label
    #        self.change_list_template = self.change_list_template or [
    #            'iadmin/change_list.html',
    #            'admin/change_list.html'
    #        ]
    #        extra_context = {'cell_menu_on_click': self.cell_menu_on_click}
    #        return super(IModelAdmin, self).changelist_view(request, extra_context)

    def get_changelist(self, request, **kwargs):
        return IChangeList

    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request", None)
        if isinstance(db_field, models.ForeignKey):
            formfield = self.formfield_for_foreignkey(db_field, request, **kwargs)
            related_modeladmin = self.admin_site._registry.get(db_field.rel.to, None)
            if self.autocomplete_ajax and  hasattr(related_modeladmin, 'ajax_query'):
                service = reverse('admin:%s_%s_ajax' % (
                    related_modeladmin.model._meta.app_label, related_modeladmin.model._meta.module_name))
                if service:
                    formfield.widget = ajax.AjaxFieldWidgetWrapper(formfield.widget, db_field.rel, self.admin_site,
                                                                   service=service)
                return formfield
            elif formfield:
                formfield.widget = RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
                return formfield

        return super(IModelAdmin, self).formfield_for_dbfield(db_field, request=request, **kwargs)



    def ajax_query(self, request):
        """
            ajax service to perform autocomplete widget queries
        """

        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name


        bit = request.GET.get('q', '')
        fmt = request.GET.get('fmt', AUTOCOMPLETE)

        logging.info(self.ajax_search_fields )
        logging.info(self.search_fields )

        logging.info([{construct_search(str(field_name)): bit} for field_name in self.ajax_search_fields] )

        if bit == '?': # show all if user inputs `?`
            or_queries = {}
        else:
            or_queries = [models.Q(**{construct_search(str(field_name)): bit}) for field_name in
                          self.ajax_search_fields]

        flds = list(self.ajax_list_display)
        field_names = [f.name for f in self.model._meta.fields]
        qs = self.model.objects.filter(*or_queries)
        logging.info( qs )
        data = []
        for record in qs:
            row = [force_unicode(record.pk)]
            for fname in flds:
                if hasattr(record, fname):
                    attr = getattr(record, fname)
                    if callable(attr):
                        val = attr()
                    elif hasattr(self, fname):
                        val = attr
                    elif fname in field_names:
                        val = attr
                elif hasattr(self, fname):
                    attr = getattr(self, fname)
                    val = attr(record)

                row.append(force_unicode(val))
            data.append(row)

        if fmt == JSON:
            ret = json.dumps(list(data))
        elif fmt == PJSON:
            ser = django.core.serializers.get_serializer('json')
            ret = ser().serialize(qs)
        else: #AUTOCOMPLETE
            ret = '\n'.join(map("|".join, data))
#        raise Exception( qs )
        return HttpResponse(ret, content_type='text/plain')


    @csrf_protect_m
    @transaction.commit_on_success
    def change_view(self, request, object_id, extra_context=None):
        return super(IModelAdmin, self).change_view(request, object_id, extra_context)

#    @transaction.commit_on_success
    def display_view(self, request, object_id, extra_context=None):
        "The 'display' admin view for this model."
        model = self.model
        opts = model._meta
        if request.method == 'POST':
            raise PermissionDenied

        obj = self.get_object(request, unquote(object_id))
        if not self.has_view_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})


        ModelForm = self.get_form(request, obj)
        formsets = []
        form = ModelForm(instance=obj)
        prefixes = {}
        for FormSet, inline in zip(self.get_formsets(request, obj), self.inline_instances):
            prefix = FormSet.get_default_prefix()
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
            if prefixes[prefix] != 1:
                prefix = "%s-%s" % (prefix, prefixes[prefix])
            formset = FormSet(instance=obj, prefix=prefix,
                              queryset=inline.queryset(request))
            formsets.append(formset)

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj),
            self.get_prepopulated_fields(request, obj),
            self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            readonly = list(inline.get_readonly_fields(request, obj))
            prepopulated = dict(inline.get_prepopulated_fields(request, obj))
            inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                fieldsets, prepopulated, readonly, model_admin=self)
            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        context = {
            'title': _('Change %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'has_view_permission': self.has_view_permission(request),
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)

    def get_readonly_fields(self, request, obj=None):
        if not self.has_change_permission(request, obj):
            return [f.name for f in self.model._meta.fields]

        return super(IModelAdmin, self).get_readonly_fields(request, obj)


    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view, cacheable)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name
        #        urlpatterns = super(IModelAdmin, self).get_urls()
        urlpatterns = patterns('',
                               url(r'^$',
                                   wrap(self.changelist_view),
                                   name='%s_%s_changelist' % info),
                               url(r'^add/$',
                                   wrap(self.add_view),
                                   name='%s_%s_add' % info),
                               url(r'^(.+)/history/$',
                                   wrap(self.history_view),
                                   name='%s_%s_history' % info),
                               url(r'^(.+)/delete/$',
                                   wrap(self.delete_view),
                                   name='%s_%s_delete' % info),
                               url(r'^(.+)/view/$',
                                   wrap(self.display_view),
                                   name='%s_%s_display' % info),
                               url(r'^ajax/search$',
                                   wrap(self.ajax_query),
                                   name='%s_%s_ajax' % info),
                               url(r'^(.+)/$',
                                   wrap(self.change_view),
                                   name='%s_%s_change' % info),
                               )
        return urlpatterns

    def _declared_fieldsets(self):
        # overriden to handle `add_undefined_fields`
        if self.fieldsets:
            if self.add_undefined_fields:
                def _valid(field):
                    return field.editable and type(field) not in (AutoField, ) and '_ptr' not in field.name

                flds = list(self.fieldsets)
                fieldset_fields = flatten_fieldsets(self.fieldsets)
                alls = [f.name for f in self.model._meta.fields if _valid(f)]
                missing_fields = [f for f in alls if f not in fieldset_fields]
                flds.append(('Other', {'fields': missing_fields, 'classes': ('collapse',), },))
                return flds
            else:
                return self.fieldsets
        elif self.fields:
            return [(None, {'fields': self.fields})]
        return None

    declared_fieldsets = property(_declared_fieldsets)


class ITabularInline(DjangoTabularInline):
    template = 'iadmin/edit_inline/tabular_tab.html'
    add_undefined_fields = False
    autocomplete_ajax = False
    
    #if True enable link to change view from inlines. Must be False if the related Model is not registered in the admin
    edit_link = False

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(ITabularInline, self).get_formset(request, obj, **kwargs)
        formset.edit_link = self.edit_link
        return formset

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        formfield = super(ITabularInline, self).formfield_for_foreignkey(db_field, request, **kwargs)
        if formfield and db_field.name not in self.raw_id_fields:
            formfield.widget = widgets.RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
        return formfield

    def formfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request", None)
        if isinstance(db_field, models.ForeignKey):
            formfield = self.formfield_for_foreignkey(db_field, request, **kwargs)
            modeladmin = self.admin_site._registry.get(db_field.rel.to, False)
            if isinstance(modeladmin, IModelAdmin):
                service = reverse(
                    'admin:%s_%s_ajax' % (modeladmin.model._meta.app_label, modeladmin.model._meta.module_name))
                if (service is not None) and db_field.name not in self.raw_id_fields:
                    formfield.widget = ajax.AjaxFieldWidgetWrapper(formfield.widget, db_field.rel, self.admin_site,
                                                                   service=service)
            return formfield

        return super(ITabularInline, self).formfield_for_dbfield(db_field, request=request, **kwargs)

    def dformfield_for_dbfield(self, db_field, **kwargs):
        request = kwargs.pop("request", None)
        if isinstance(db_field, models.ForeignKey):
            formfield = self.formfield_for_foreignkey(db_field, request, **kwargs)
            related_modeladmin = self.admin_site._registry.get(db_field.rel.to, None)
            if self.autocomplete_ajax and  hasattr(related_modeladmin, 'ajax_query'):
                service = reverse('admin:%s_%s_ajax' % (
                    related_modeladmin.model._meta.app_label, related_modeladmin.model._meta.module_name))
                if service:
                    formfield.widget = ajax.AjaxFieldWidgetWrapper(formfield.widget, db_field.rel, self.admin_site,
                                                                   service=service)
                return formfield
            elif formfield:
                formfield.widget = RelatedFieldWidgetWrapperLinkTo(formfield.widget, db_field.rel, self.admin_site)
                return formfield

        return super(ITabularInline, self).formfield_for_dbfield(db_field, request=request, **kwargs)