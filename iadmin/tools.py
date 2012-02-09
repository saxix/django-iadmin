from _csv import Error
from contextlib import contextmanager
import re
from django.forms.fields import ChoiceField, CharField
from django import forms
from django.forms import FileField
import csv
from django.forms.forms import Form, DeclarativeFieldsMetaclass, BoundField
from django.forms.widgets import Input, HiddenInput
from django.template.context import RequestContext
from django.utils.encoding import force_unicode, smart_str
from django.utils import formats
from django.conf import settings
import tempfile
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse
from django.db.models.fields.related import ForeignKey
from django.db.models.loading import get_model, get_models, get_apps, get_app
from django.shortcuts import render_to_response, redirect
import os
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.views.generic.base import View
from django.forms.fields import  CharField, BooleanField
from django.utils.translation import gettext as _

delimiters = ",;|:"
quotes = "'\"`"
escapechars = " \\"

def _get_all_models(filter_app_name=None):
    all_models = []
    if filter_app_name:
        apps = [get_app(filter_app_name)]
    else:
        apps = get_apps()
    from django.contrib.admin import site

    for app in apps:
        for mod in get_models(app):
            if mod in site._registry:
                all_models.append("%s:%s" % (mod._meta.app_label, force_unicode(mod._meta.verbose_name)))
    return zip(all_models, all_models)


@contextmanager
def open_csv(filename):
    fd = open(filename, 'rb')
    dialect = csv.Sniffer().sniff(fd.read(2048))
    fd.seek(0)
    csv_reader = csv.reader(fd, dialect=dialect)
    yield csv_reader
    fd.close()


class CsvFileField(FileField):
    def clean(self, data, initial=None):
        if not data and initial:
            return initial
        ret = super(FileField, self).clean(data)
        if ret:
            try:
                _dialect = csv.Sniffer().sniff(data.read(2048))
                data.seek(0)
                csv_reader = csv.reader(data, dialect=_dialect)
                for i in range(10):
                    csv_reader.next()
            except Error, e:
                raise ValidationError("Unable to load csv file (%s)" % e)
        return ret


class ImportForm(Form):
    model = ChoiceField()
    csv = CsvFileField()

    def __init__(self, app, model, data=None, files=None, auto_id='id_%s', prefix=None, initial=None):
        super(ImportForm, self).__init__(data, files, auto_id, prefix, initial)
        if self.data:
            app, model = self.data['model'].split(':')

        if model:
            m = "%s:%s" % ( app, model)
            self.fields['model'].choices = [(m, m)]
            self.fields['model'].widget = Input({'readonly': 'readonly'})
            self.initial['model'] = m
        elif app:
            self.fields['model'].choices = _get_all_models(app)
        else:
            self.fields['model'].choices = _get_all_models()


class CSVPRocessorForm(Form):
    header = BooleanField(label='Header', initial=False, required=False)
    validate = BooleanField(label='Form validation', initial=False, required=False)
    preview_all = BooleanField(label='Preview all records', initial=False, required=False)
    create_missing = BooleanField(label='Create missing rows', initial=False, required=False)

    def _head(self, rows=10):
        with open_csv(self._filename) as csv:
            output = []
            for i in range(rows):
                output.append(csv.next())
        return output

    def clean(self):
        found = False
        # todo: we should try to create a dummy model to force some validation ??
        for i, f  in enumerate(self._fields):
            fld = 'fld_%s' % i
            col = 'col_%s' % i
            lkf = 'lkf_%s' % i
            column = self.cleaned_data[col]
            field_name = self.cleaned_data[fld]
            lookup_name = self.cleaned_data[lkf]
            if column >= 0 or field_name:
                found = True
                if not ( column >= 0 and field_name):
                    self._errors[fld] = self.error_class([_("Please set both 'column' and 'field'")])
                    raise ValidationError("Please fix errors below")
                Field, _u, _u, _u = self._model._meta.get_field_by_name(field_name)
                if isinstance(Field, ForeignKey):
                    if not lookup_name:
                        self._errors[fld] = self.error_class([_('Please set lookup field name for "%s"') % field_name])
                    else:
                        try:
                            Field.rel.to._meta.get_field_by_name(lookup_name)
                        except Exception, e:
                            self._errors[fld] = self.error_class([e])

            if not found:
                raise ValidationError("Please set columns mapping")
        return self.cleaned_data

    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        top_errors = self.non_field_errors() # Errors that should be displayed above all fields.
        output, hidden_fields = [], []
        for name in ('header', 'preview_all', 'validate', 'create_missing'):
            field = self.fields[name]
            bf = BoundField(self, field, name)
            bf_errors = self.error_class(
                [conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
            if bf_errors:
                top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
            output.append('<tr><td class="label" colspan="4">%s</td><td>%s</td></tr>' % (bf.label, unicode(bf)))

        output.append(
            u'<tr><th>%s</th><th>%s</th><th class="rex">%s</th><th class="lkf">%s</th><th class="key">%s</th></tr>' % (
                _('Column'), _('Field'), _('Regex'), _('Lookup Field'), _('pk')))

        for i, f  in enumerate(self._fields):
            line = []
            error_line = []
            rowid = self.fields['col_%s' % i].label
            for n in ('col_%s', 'fld_%s', 'rex_%s', 'lkf_%s', 'key_%s'):
                name = n % i
                field = self.fields[name]
                bf = BoundField(self, field, name)
                bf_errors = self.error_class(
                    [conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
                error_line.append(force_unicode(bf_errors), )
                line.append('<td class=%(class)s>%(field)s</td>' %
                            {'field': unicode(bf),
                             'class': n[:3]}
                )
            output.append('<tr><td colspan="5">%s</td></tr>' % ''.join(error_line))
            output.append('<tr>%(line)s</tr>' % {'line': ''.join(line), 'rowid': rowid})

        if top_errors:
            output.insert(0, error_row % force_unicode(top_errors))

        return mark_safe(u'\n'.join(output))

    def as_hidden(self):
        output, hidden_fields = [], []
        for name, field in self.fields.items():
            field.widget = HiddenInput({'readonly': 'readonly'})
            bf = BoundField(self, field, name)
            output.append(unicode(bf))
        return mark_safe(u'\n'.join(output))

    def as_table(self):
        "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self._html_output(
            normal_row=u'<tr%(html_class_attr)s><th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>',
            error_row=u'<tr><td colspan="4">%s</td></tr>',
            row_ender=u'</td></tr>',
            help_text_html=u'<br /><span class="helptext">%s</span>',
            errors_on_separate_row=False)


def csv_processor_factory(app_name, model_name, csv_filename):
    """
      factory for Model specific CSVPRocessorForm
    """
    rows = []
    fd = open(csv_filename, 'rb')
    dialect = csv.Sniffer().sniff(fd.read(2048))
    fd.seek(0)
    csv_reader = csv.reader(fd, dialect=dialect)
    for i in range(10):
        rows.append(csv_reader.next())
    fd.close()
    columns_count = len(rows[0])

    model = get_model(app_name, model_name)

    model_fields = [('', '-- ignore --')] + [(f.name, f.name) for f in model._meta.fields]
    columns_def = [(-1, '-- ignore --')] + [(i, "Column %s" % i) for i in range(columns_count)]

    class_name = "%s%sImportForm" % (app_name, model_name)
    attrs = {
        #        'header': BooleanField(label='Header', initial=False, required=False),
        #        'validate': BooleanField(label='Form validation', initial=False, required=False),
        #        'preview_all': BooleanField(label='Preview all records', initial=False, required=False),
        #        'create_missing': BooleanField(label='Create missing rows', initial=False, required=False),
        'columns_count': columns_count,
        'sample': rows,
        '_model': model,
        '_fields': model._meta.fields,
        '_filename': csv_filename,
        '_dialect': dialect
    }

    for i, f  in enumerate(model._meta.fields):
        # column, field, regex to manipulate column value, lookup field name for foreign-keys, primary key flag
        attrs['col_%s' % i] = ColumnField(choices=columns_def, required=False)
        attrs['fld_%s' % i] = ChoiceField(choices=model_fields, required=False)
        attrs['rex_%s' % i] = RegexField(label='', initial='(.*)', required=False)
        attrs['lkf_%s' % i] = CharField(required=False)
        attrs['key_%s' % i] = BooleanField(label='', initial=False, required=False)

    return DeclarativeFieldsMetaclass(str(class_name), (CSVPRocessorForm,), attrs)


class CSVOptions(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    header = forms.BooleanField(required=False)
    delimiter = forms.ChoiceField(choices=zip(delimiters, delimiters))
    quotechar = forms.ChoiceField(choices=zip(quotes, quotes))
    quoting = forms.ChoiceField(
        choices=((csv.QUOTE_ALL, 'All'), (csv.QUOTE_MINIMAL, 'Minimal'), (csv.QUOTE_NONE, 'None'),
                 (csv.QUOTE_NONNUMERIC, 'Non Numeric')))

    escapechar = forms.ChoiceField(choices=(('', ''), ('\\', '\\')), required=False)
    datetime_format = forms.CharField(initial=formats.get_format('DATETIME_FORMAT'))
    date_format = forms.CharField(initial=formats.get_format('DATE_FORMAT'))
    time_format = forms.CharField(initial=formats.get_format('TIME_FORMAT'))
    columns = forms.MultipleChoiceField()


class CsvFileField(FileField):
    def clean(self, data, initial=None):
        if not data and initial:
            return initial
        ret = super(FileField, self).clean(data)
        if ret:
            try:
                _dialect = csv.Sniffer().sniff(data.read(2048))
                data.seek(0)
                csv_reader = csv.reader(data, dialect=_dialect)
                for i in range(10):
                    csv_reader.next()
            except Error, e:
                raise ValidationError("Unable to load csv file (%s)" % e)
        return ret


class ColumnField(ChoiceField):
    def to_python(self, value):
        "Returns a Unicode object."
        return int(value)

    def valid_value(self, value):
        return True


class RegexField(CharField):
    def clean(self, value):
        value = super(RegexField, self).clean(value)
        if value:
            try:
                if not ('(' or '(') in value:
                    raise ValidationError
                return  re.compile(value)
            except:
                raise ValidationError(_("'%s' is not a valid regex pattern" % value))
        return value


class Lookup(dict):
    """
    a dictionary which can lookup value by key, or keys by value
    """

    def __init__(self, items=None):
        """items can be a list of pair_lists or a dictionary"""
        dict.__init__(self, items or [])

    def get_key(self, value):
        """find the key(s) as a list given a value"""
        return [item[0] for item in self.items() if item[1] == value][0]

    def get_value(self, key):
        """find the value given a key"""
        return self[key]


def _get_all_models(filter_app_name=None):
    all_models = []
    if filter_app_name:
        apps = [get_app(filter_app_name)]
    else:
        apps = get_apps()
    from django.contrib.admin import site

    for app in apps:
        for mod in get_models(app):
            if mod in site._registry:
                all_models.append("%s:%s" % (mod._meta.app_label, force_unicode(mod._meta.verbose_name)))
    return zip(all_models, all_models)


def get_valid_choice(value, choices):
    for k, v in choices:
        if str(v) == str(value):
            return True, v

    return False, None


def update_model(request, original, updater, mapping):
    for fname, v in updater.items():
        _u, _u, _u, lookup_name, Field = mapping[fname]
        if isinstance(Field, ForeignKey):
            if lookup_name:
                try:
                    v = Field.rel.to.objects.get(**{lookup_name: v})
                except ObjectDoesNotExist, e:
                    raise ObjectDoesNotExist('%s %s' % (e, v))
        setattr(original, fname, v)
    return original


def set_model_attribute(instance, name, value, rex=None):
    if value == 'None':
        value = None
    field, model, direct, m2m = instance._meta.get_field_by_name(name)

    if isinstance(field, ForeignKey):
        m = re.compile(rex).match(value)

    elif hasattr(field, 'flatchoices'):
        choices = Lookup(getattr(field, 'flatchoices'))
        if value in choices.values():
            value = choices.get_key(value)
    setattr(instance, name, value)


#class IAdminPlugin(object):
#    def __init__(self, adminsite):
#        self.admin_site = adminsite
#        self.name = adminsite.name
#
#    def get_urls(self):
#        pass
#
#    @property
#    def urls(self):
#        return self.get_urls()


class CSVImporter(View):
    """
        workflow
          GET        POST
          start() -> page1
    """
    template_step1 = None
    template_step2 = None
    template_step3 = None

    def __init__(self, admin_site, app_label, model_name, page, **initkwargs):
        self.admin_site = admin_site
        self.app_label = app_label
        self.model_name = model_name
        self.page = page
        self.app = get_app(self.app_label)
        self.model = get_model(self.app_label, self.model_name)
        return super(CSVImporter, self).__init__(**initkwargs)


    def done(self, form_list, **kwargs):
        return render_to_response('done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            })

    def get_context_data(self, **kwargs):
        kwargs.update({'app_label': self.app_label.lower(),
                       'app': self.app,
                       'model': self.model,
                       'opts': self.model._meta,
                       'model_name': self.model_name.lower(),
                       #                                     'root_path': self.admin_site.root_path or '',
                       'lbl_next': 'Next >>',
                       'lbl_back': '<< Back',
                       'back': self.request.META.get('HTTP_REFERER', ''),
                       })
        kwargs.setdefault('title', 'Import CSV File %s/3' % kwargs['page'], )
        return kwargs

    def __get_mapping(self, form):
        mapping = {}
        for i, f in enumerate(form._fields):
            field_name = form.cleaned_data['fld_%s' % i]
            column = form.cleaned_data['col_%s' % i]
            rex = form.cleaned_data['rex_%s' % i]
            lk = form.cleaned_data['lkf_%s' % i]
            key = form.cleaned_data['key_%s' % i]

            if column >= 0:
                Field, _, _, _ = form._model._meta.get_field_by_name(field_name)
                mapping[field_name] = [column, rex, bool(key), lk, Field]
        return mapping

    def _process_row(self, row, mapping):
        record = {}
        key = {}
        for field_name, (col, rex, is_key, lk, Field) in mapping.items():
            try:
                raw_val = rex.search(row[col]).group(1)
                field_value = None
                if isinstance(Field, ForeignKey):
                    try:
                        field_value = Field.rel.to.objects.get(**{lk: raw_val})
                    except Field.rel.to.DoesNotExist:
                        pass
                else:
                    field_value = Field.to_python(raw_val)
                record[field_name] = field_value
                if is_key:
                    key[field_name] = record[field_name]
            except AttributeError, e:
                raise AttributeError('Error processing "%s": Invalid regex' % field_name)
            except Exception, e:
                raise e.__class__('Error processing "%s"' % field_name, e)
        return record, key

    #    def _step_1(self, request):
    #        context = self.get_context_data()
    #        if request.method == 'POST':
    #            form = ImportForm(self.app_label, self.model_name, request.POST, request.FILES)
    #            if form.is_valid():
    #                f = request.FILES['csv']
    #                fd = open(self.temp_file_name, 'wb')
    #                for chunk in f.chunks():
    #                    fd.write(chunk)
    #                fd.close()
    #                if settings.DEBUG:
    #                    messages.info(request, self.temp_file_name)
    #                app_name, model_name = form.cleaned_data['model'].split(':')
    #                goto_url = reverse('iadmin:import', kwargs={'app_label': self.app_label, 'model_name': self.model_name, 'page': 2})
    #                return HttpResponseRedirect(goto_url)
    #        else:
    #            form = ImportForm(self.app_label, self.model_name, initial={'page': 1})
    #
    #        context.update({'page': 1, 'form': form, })
    #
    #        return render_to_response(self.template_step1 or [
    #            "iadmin/%s/%s/import_csv_1.html" % (self.app_label, self.model_name),
    #            "iadmin/%s/import_csv_1.html" % self.app_label,
    #            "iadmin/import_csv_1.html"
    #        ], RequestContext(self.request, context))
    #
    #    def post_2(self):
    #        records = []
    #        context = self.get_context_data()
    #        try:
    #            Form = csv_processor_factory(self.app_label, self.model_name, self.temp_file_name)
    #            form = Form(self.request.POST, self.request.FILES)
    #            if form.is_valid():
    #                mapping = self.__get_mapping(form)
    #                Model = get_model(self.app_label, self.model_name)
    #                with open_csv(self.temp_file_name) as csv:
    #                    if form.cleaned_data['header']:
    #                        csv.next()
    #                    for i, row in enumerate(csv):
    #                        if i > 20 and not form.cleaned_data['preview_all']:
    #                            break
    #                        try:
    #                            sample = Model()
    #                            record, key = self._process_row(row, mapping)
    #                            exists = key and Model.objects.filter(**key).exists() or False
    #                            if key and exists:
    #                                sample = Model.objects.get(**key)
    #                            else:
    #                                sample = Model()
    #                            sample = update_model(self.request, sample, record, mapping)
    #
    #                            records.append([sample, None, row])
    #                        except (ValidationError, AttributeError), e:
    #                            records.append([sample, str(e), row])
    #                        except (ValueError, ObjectDoesNotExist, ValidationError), e:
    #                            messages.error(self.request, '%s' % e)
    #                            records.append([sample, str(e)])
    #                    return self._step_3(self.request, {'records': records, 'form': form})
    #
    #
    #            context.update({'page': 2,
    #                            'form': form,
    #                            'back': reverse('iadmin:import', kwargs={'app_label': self.app_label, 'model_name': self.model_name, 'page': 1}),
    #                            'fields': form._fields,
    #                            'sample': form._head(),
    #                            })
    #            return render_to_response(self.template_step2 or [
    #                                                    "iadmin/%s/%s/import_csv_2.html" % (self.app_label, self.model_name.lower()),
    #                                                    "iadmin/%s/import_csv_2.html" % self.app_label,
    #                                                    "iadmin/import_csv_2.html"
    #                                                ], RequestContext(self.request, context))
    #
    #        except IOError, e:
    #            messages.error(self.request, str(e))
    #            return redirect('iadmin:import', app_label=self.app_label, model_name=self.model_name, page=1)
    #
    #    def _step_3(self, request, extra_context ):
    #        context = self.get_context_data()
    #        Model = get_model(self.app_label, self.model_name)
    #        extra_context = extra_context or {}
    #        if 'apply' in request.POST:
    #            Form = csv_processor_factory(self.app_label, self.model_name, self.temp_file_name)
    #            form = Form(request.POST, request.FILES)
    #            if form.is_valid():
    #                mapping = self.__get_mapping(form)
    #                Model = get_model(self.app_label, self.model_name)
    #                with open_csv(self.temp_file_name) as csv:
    #                    if form.cleaned_data['header']:
    #                        csv.next()
    #                    for i, row in enumerate(csv):
    #                        record, key = self._process_row(row, mapping)
    #                        try:
    #                            if key:
    #                                if form.cleaned_data['create_missing']:
    #                                    sample, _ = Model.objects.get_or_create(**key)
    #                                else:
    #                                    sample = Model.objects.get(**key)
    #                            else:
    #                                sample = Model()
    #                            sample = update_model(request, sample, record, mapping)
    #                            sample.save()
    #                        except (IntegrityError, ObjectDoesNotExist), e:
    #                            messages.error(request, '%s: %s' % (str(e), row) )
    #                return redirect('%s:%s_%s_changelist' % (self.name, self.app_label, self.model_name.lower()))
    #        else:
    #            pass
    #        context.update({'page': 3,
    #                        'fields': Model._meta.fields,
    #                        'back': reverse('iadmin:import', kwargs={'app_label': self.app_label, 'model_name': self.model_name, 'page': 2}),
    #                        'lbl_next': 'Apply',
    #                        })
    #        context.update(extra_context)
    #        return render_to_response(self.template_step3 or [
    #                                                "iadmin/%s/%s/import_csv_3.html" % (self.app_label, self.model_name.lower()),
    #                                                "iadmin/%s/import_csv_3.html" % self.app_label,
    #                                                "iadmin/import_csv_3.html"
    #                                            ], RequestContext(request, context))
    #
    def start(self):
        form = ImportForm(self.app_label, self.model_name, initial={'page': 1})
        context = self.get_context_data(page=1, form=form)

        return render_to_response(self.template_step1 or [
            "iadmin/%s/%s/import_csv_1.html" % (self.app_label, self.model_name),
            "iadmin/%s/import_csv_1.html" % self.app_label,
            "iadmin/import_csv_1.html"
        ], RequestContext(self.request, context))

    def load_csv(self):
        form = ImportForm(self.app_label, self.model_name, self.request.POST, self.request.FILES)
        if form.is_valid():
            f = self.request.FILES['csv']
            fd = open(self.temp_file_name, 'wb')
            for chunk in f.chunks():
                fd.write(chunk)
            fd.close()
            if settings.DEBUG:
                messages.info(self.request, self.temp_file_name)
            return self.display_mapping()
        else:
            context = self.get_context_data(page=1, form=form)
            return render_to_response(self.template_step1 or [
                "iadmin/%s/%s/import_csv_1.html" % (self.app_label, self.model_name),
                "iadmin/%s/import_csv_1.html" % self.app_label,
                "iadmin/import_csv_1.html"
            ], RequestContext(self.request, context))

    def display_mapping(self):
        Form = csv_processor_factory(self.app_label, self.model_name, self.temp_file_name)
        form = Form(self.request.POST, self.request.FILES)
        context = self.get_context_data(page=2, form=form)

        #        if self.page == '2':
        #        if form.is_valid():
        #            self.process_mapping(form)

        return render_to_response(self.template_step1 or [
            "iadmin/%s/%s/import_csv_2.html" % (self.app_label, self.model_name),
            "iadmin/%s/import_csv_2.html" % self.app_label,
            "iadmin/import_csv_2.html"
        ], RequestContext(self.request, context))

    def process_mapping(self, form):
        records = []
        mapping = self.__get_mapping(form)
        Model = get_model(self.app_label, self.model_name)
        with open_csv(self.temp_file_name) as csv:
            if form.cleaned_data['header']:
                csv.next()
            for i, row in enumerate(csv):
                if i > 20 and not form.cleaned_data['preview_all']:
                    break
                try:
                    sample = Model()
                    record, key = self._process_row(row, mapping)
                    exists = key and Model.objects.filter(**key).exists() or False
                    if key and exists:
                        sample = Model.objects.get(**key)
                    else:
                        sample = Model()
                    sample = update_model(self.request, sample, record, mapping)

                    records.append([sample, None, row])
                except (ValidationError, AttributeError), e:
                    records.append([sample, str(e), row])
                except (ValueError, ObjectDoesNotExist, ValidationError), e:
                    messages.error(self.request, '%s' % e)
                    records.append([sample, str(e)])
            return self.preview({'records': records, 'form': form})

    def preview(self, ):
        context = self.get_context_data()
        Model = get_model(self.app_label, self.model_name)
        extra_context = extra_context or {}
        context.update({'page': 3,
                        'fields': Model._meta.fields,
                        'back': reverse('iadmin:import',
                            kwargs={'app_label': self.app_label, 'model_name': self.model_name, 'page': 2}),
                        'lbl_next': 'Apply',
                        })
        context.update(extra_context)
        return render_to_response(self.template_step3 or [
            "iadmin/%s/%s/import_csv_3.html" % (self.app_label, self.model_name.lower()),
            "iadmin/%s/import_csv_3.html" % self.app_label,
            "iadmin/import_csv_3.html"
        ], RequestContext(self.request, context))


    @property
    def temp_file_name(self):
        filename = "%s_%s_%s_%s" % (
        self.request.user.username, self.app_label, self.model_name, hash(self.request.user.password) )
        return os.path.join(tempfile.gettempdir(), 'iadmin_import_%s.temp~' % filename)

    def get(self, request, *args, **kwargs):
        return self.start()

    def post(self, request, *args, **kwargs):
        if self.page == '1':
            return self.load_csv()
        elif self.page == '2':
            return self.display_mapping()
        elif self.page == '3':
            return self.process_mapping()

#class CSVImporter2(IAdminPlugin):
#    template_step1 = None
#    template_step2 = None
#    template_step3 = None
#
#    def _get_base_context(self, request, app=None, model=None):
#        return template.RequestContext(request, {'app_label': (app or '').lower(),
#                                                 'model_name': (model or '').lower(),
#                                                 'root_path': self.admin_site.root_path or '',
#                                                 'lbl_next': 'Next >>',
#                                                 'lbl_back': '<< Back',
#                                                 'back': request.META['HTTP_REFERER'],
#                                                 },
#                                       current_app=self.name)
#
#    def __get_mapping(self, form):
#        mapping = {}
#        for i, f in enumerate(form._fields):
#            field_name = form.cleaned_data['fld_%s' % i]
#            column = form.cleaned_data['col_%s' % i]
#            rex = form.cleaned_data['rex_%s' % i]
#            lk = form.cleaned_data['lkf_%s' % i]
#            key = form.cleaned_data['key_%s' % i]
#
#            if column >= 0:
#                Field, _, _, _ = form._model._meta.get_field_by_name(field_name)
#                mapping[field_name] = [column, rex, bool(key), lk, Field]
#        return mapping
#
#    def _step_1(self, request, app=None, model=None, temp_file_name=None):
#        context = self._get_base_context(request, app, model)
#        if request.method == 'POST':
#            form = ImportForm(app, model, request.POST, request.FILES)
#            if form.is_valid():
#                f = request.FILES['csv']
#                fd = open(temp_file_name, 'wb')
#                for chunk in f.chunks():
#                    fd.write(chunk)
#                fd.close()
#                if settings.DEBUG:
#                    messages.info(request, temp_file_name)
#                app_name, model_name = form.cleaned_data['model'].split(':')
#                goto_url = reverse('%s:model_import_csv' % self.name,
#                                   kwargs={'app': app_name, 'model': model_name, 'page': 2})
#                return HttpResponseRedirect(goto_url)
#        else:
#            form = ImportForm(app, model, initial={'page': 1})
#
#        context.update({'page': 1, 'form': form, })
#
#        return render_to_response(self.template_step1 or [
#            "iadmin/%s/%s/import_csv_1.html" % (app, model),
#            "iadmin/%s/import_csv_1.html" % app,
#            "iadmin/import_csv_1.html"
#        ], context)
#
#
#    def _process_row(self, row, mapping):
#        record = {}
#        key = {}
#        for field_name, (col, rex, is_key, lk, Field) in mapping.items():
#            try:
#                raw_val = rex.search(row[col]).group(1)
#                field_value = None
#                if isinstance(Field, ForeignKey):
#                    try:
#                        field_value = Field.rel.to.objects.get(**{lk: raw_val})
#                    except Field.rel.to.DoesNotExist:
#                        pass
#                else:
#                    field_value = Field.to_python(raw_val)
#                record[field_name] = field_value
#                if is_key:
#                    key[field_name] = record[field_name]
#            except AttributeError, e:
#                raise AttributeError('Error processing "%s": Invalid regex' % field_name)
#            except Exception, e:
#                raise e.__class__('Error processing "%s"' % field_name, e)
#        return record, key
#
#    def _step_2(self, request, app_name=None, model_name=None, temp_file_name=None):
#        records = []
#        context = self._get_base_context(request, app_name, model_name)
#        try:
#            Form = csv_processor_factory(app_name, model_name, temp_file_name)
#            if request.method == 'POST':
#                form = Form(request.POST, request.FILES)
#                if form.is_valid():
#                    mapping = self.__get_mapping(form)
#                    Model = get_model(app_name, model_name)
#                    with open_csv(temp_file_name) as csv:
#                        if form.cleaned_data['header']:
#                            csv.next()
#                        for i, row in enumerate(csv):
#                            if i > 20 and not form.cleaned_data['preview_all']:
#                                break
#                            try:
#                                sample = Model()
#                                record, key = self._process_row(row, mapping)
#                                exists = key and Model.objects.filter(**key).exists() or False
#                                if key and exists:
#                                    sample = Model.objects.get(**key)
#                                else:
#                                    sample = Model()
#                                sample = update_model(request, sample, record, mapping)
#                                records.append([sample, None, row])
#                            except (ValidationError, AttributeError), e:
#                                records.append([sample, str(e), row])
#                            except (ValueError, ObjectDoesNotExist, ValidationError), e:
#                                #messages.error(request, '%s' % e)
#                                records.append([sample, str(e)])
#                        return self._step_3(request, app_name, model_name, temp_file_name, {'records': records,
#                                                                                            'form': form})
#
#            else:
#                form = Form()
#
#            context.update({'page': 2,
#                            'form': form,
#                            'back': reverse('%s:model_import_csv' % self.name,
#                                            kwargs={'app': app_name, 'model': model_name, 'page': 1}),
#                            'fields': form._fields,
#                            'sample': form._head(),
#                            })
#            return render_to_response(self.template_step2 or [
#                                                    "iadmin/%s/%s/import_csv_2.html" % (app_name, model_name.lower()),
#                                                    "iadmin/%s/import_csv_2.html" % app_name,
#                                                    "iadmin/import_csv_2.html"
#                                                ], context)
#
#        except IOError, e:
#            messages.error(request, str(e))
#            return redirect('%s:model_import_csv' % self.name, app=app_name, model=model_name, page=1)
#
#    def _step_3(self, request, app_name=None, model_name=None, temp_file_name=None, extra_context=None ):
#        context = self._get_base_context(request, app_name, model_name)
#        Model = get_model(app_name, model_name)
#        extra_context = extra_context or {}
#        if 'apply' in request.POST:
#            Form = csv_processor_factory(app_name, model_name, temp_file_name)
#            form = Form(request.POST, request.FILES)
#            if form.is_valid():
#                mapping = self.__get_mapping(form)
#                Model = get_model(app_name, model_name)
#                with open_csv(temp_file_name) as csv:
#                    if form.cleaned_data['header']:
#                        csv.next()
#                    for i, row in enumerate(csv):
#                        record, key = self._process_row(row, mapping)
#                        try:
#                            if key:
#                                if form.cleaned_data['create_missing']:
#                                    sample, _ = Model.objects.get_or_create(**key)
#                                else:
#                                    sample = Model.objects.get(**key)
#                            else:
#                                sample = Model()
#                            sample = update_model(request, sample, record, mapping)
#                            sample.save()
#                        except (IntegrityError, ObjectDoesNotExist), e:
#                            messages.error(request, '%s: %s' % (str(e), row) )
#                return redirect('%s:%s_%s_changelist' % (self.name, app_name, model_name.lower()))
#        else:
#            pass
#        context.update({'page': 3,
#                        'fields': Model._meta.fields,
#                        'back': reverse('%s:model_import_csv' % self.name,
#                                        kwargs={'app': app_name, 'model': model_name, 'page': 2}),
#                        'lbl_next': 'Apply',
#                        })
#        context.update(extra_context)
#        return render_to_response(self.template_step3 or [
#                                                "iadmin/%s/%s/import_csv_3.html" % (app_name, model_name.lower()),
#                                                "iadmin/%s/import_csv_3.html" % app_name,
#                                                "iadmin/import_csv_3.html"
#                                            ], context)
#
#
#    def import_csv(self, request, page=1, app=None, model=None):
#        temp_file_name = os.path.join(tempfile.gettempdir(), 'iadmin_import_%s_%s.temp~' % (
#            request.user.username, hash(request.user.password)))
#        if int(page) == 1:
#            return self._step_1(request, app, model, temp_file_name=temp_file_name)
#        elif int(page) == 2:
#            if not 'HTTP_REFERER' in request.META:
#                return redirect('%s:model_import_csv' % self.name, app=app, model=model, page=1)
#                # todo: check referer
#            return self._step_2(request, app, model, temp_file_name=temp_file_name)
#        elif int(page) == 3:
#            return self._step_3(request, app, model, temp_file_name=temp_file_name)
#        raise Exception(page)
#
#    def get_urls(self):
#        def wrap(view, cacheable=False):
#            def wrapper(*args, **kwargs):
#                return self.admin_site.admin_view(view, cacheable)(*args, **kwargs)
#
#            return update_wrapper(wrapper, view)
#
#        return patterns('',
#                        url(r'^import/1$',
#                            wrap(self.import_csv),
#                            name='import_csv'),
#
#                        url(r'^(?P<app>\w+)/(?P<model>\w+)/import/(?P<page>\d)',
#                            wrap(self.import_csv),
#                            name='model_import_csv'),
#
#                        url(r'^(?P<app>\w+)/import/(?P<page>\d)',
#                            wrap(self.import_csv),
#                            name='app_import_csv'),
##                        )