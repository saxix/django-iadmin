#
__author__ = 'sax'
from django.db.models.fields import BooleanField
from collections import defaultdict
import datetime
from django.utils import simplejson as json
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.forms import FileField, ModelForm
from django.forms.models import modelform_factory, ModelMultipleChoiceField
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.contrib.admin import helpers

DO_NOT_MASS_UPDATE = 'do_NOT_mass_UPDATE'

class MassUpdateForm(ModelForm):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    _validate = forms.BooleanField(label='Validate', help_text="if checked use obj.save() instead of manager.update()")

    def _clean_fields(self):
        for name, field in self.fields.items():
            value = field.widget.value_from_datadict(self.data, self.files, self.add_prefix(name))
            try:
                if isinstance(field, FileField):
                    initial = self.initial.get(name, field.initial)
                    field.clean(value, initial)
                elif isinstance(field, ModelMultipleChoiceField) and value:
                    raise ValidationError("Unable no mass update ManyToManyField without 'validate'")
                else:
                    enabler = 'chk_id_%s' % name
                    if self.data.get(enabler, False):
                        value = field.clean(value)
                        self.cleaned_data[name] = value
                    if hasattr(self, 'clean_%s' % name):
                        value = getattr(self, 'clean_%s' % name)()
                        self.cleaned_data[name] = value
            except ValidationError, e:
                self._errors[name] = self.error_class(e.messages)
                if name in self.cleaned_data:
                    del self.cleaned_data[name]

    def clean__validate(self):
        return self.data.get('_validate', '') == 'on'

    def _post_clean(self):
        pass

    def is_valid(self):
        return super(MassUpdateForm, self).is_valid()


    def configured_fields(self):
        """
        Returns a list of BoundField objects that aren't hidden fields.
        The opposite of the hidden_fields() method.
        """
        return [field for field in self if not field.is_hidden and field.name.startswith('_')]

    def model_fields(self):
        """
        Returns a list of BoundField objects that aren't "private" fields.
        """
        return [field for field in self if not field.name.startswith('_')]


def mass_update(modeladmin, request, queryset):
    """
        mass update queryset
    """
    MForm = modelform_factory(modeladmin.model, form=MassUpdateForm)
    if 'apply' in request.POST:
        form = MForm(request.POST)
        if form.is_valid():
            done = 0
            if form.cleaned_data.get('_validate', False):
                for record in queryset:
                    for k, v in form.cleaned_data.items():
                        setattr(record, k, v)
                        record.save()
                        done += 1
                messages.info(request, "Updated %s records" % done)
            else:
                values = {}
                for field_name, value in form.cleaned_data.items():
                    if isinstance(form.fields[field_name], ModelMultipleChoiceField):
                        messages.error(request, "Unable no mass update ManyToManyField without 'validate'")
                        return HttpResponseRedirect(request.get_full_path())
                    elif field_name not in ['_selected_action', '_validate']:
                        values[field_name] = value
                queryset.update(**values)
            return HttpResponseRedirect(request.get_full_path())
        else:
            messages.error(request, "".join(form.errors))
    grouped = defaultdict(lambda: [])
    initial = {helpers.ACTION_CHECKBOX_NAME: request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)}

    for el in queryset.all()[:10]:
        for f in modeladmin.model._meta.fields:
            if hasattr(f, 'flatchoices') and f.flatchoices:
                grouped[f.name] = dict(getattr(f, 'flatchoices')).values()
            elif hasattr(f, 'choices') and f.choices:
                grouped[f.name] = dict(getattr(f, 'choices')).values()
            elif isinstance(f, BooleanField):
                grouped[f.name] = [True, False]
            else:
                value = getattr(el, f.name)
                if value is not None and value not in grouped[f.name]:
                    grouped[f.name].append(value)
            initial[f.name] = initial.get(f.name, value)

    form = MForm(initial=initial)

    adminForm = helpers.AdminForm(form, modeladmin.get_fieldsets(request), {}, [], model_admin=modeladmin)
    media = modeladmin.media + adminForm.media
    dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.date) else str(obj)

    return render_to_response('iadmin/mass_update.html',
        RequestContext(request, {'adminform': adminForm,
                                 'form': form,
                                 'title': u"Mass update %s" % force_unicode(modeladmin.opts.verbose_name_plural),
                                 'grouped': grouped,
                                 'fieldvalues': json.dumps(grouped, default=dthandler),
                                 'change': True,
                                 'is_popup': False,
                                 'save_as': False,
                                 'has_delete_permission': False,
                                 'has_add_permission': False,
                                 'has_change_permission': True,
                                 'opts': modeladmin.model._meta,
                                 'app_label': modeladmin.model._meta.app_label,
                                 'action': 'mass_update',
                                 'media': mark_safe(media),
                                 'selection': queryset,
                                 }))


mass_update.short_description = "Mass update"
