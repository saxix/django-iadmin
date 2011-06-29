from _csv import Error
from contextlib import contextmanager
import csv
from django.core.exceptions import ValidationError
from django.db.models.fields.related import ForeignKey
from django.forms.fields import  CharField, BooleanField
from django.db.models.loading import get_models, get_apps, get_app, get_model
from django.forms.fields import ChoiceField, FileField
from django.forms.forms import Form, DeclarativeFieldsMetaclass, BoundField
from django.forms.widgets import Input, HiddenInput, MultipleHiddenInput, TextInput
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

import re

__author__ = 'sax'

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
            data.close()
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

def update_model(original, updater):
    for fname, v in updater.items():
        setattr(original, fname, v )
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


def graph_form_factory(model):
    app_name = model._meta.app_label
    model_name = model.__name__

    model_fields = [(f.name, f.verbose_name) for f in model._meta.fields if not f.primary_key]
    graphs = [('PieChart', 'PieChart'), ('BarChart', 'BarChart')]
    model_fields.insert(0, ('', 'N/A'))
    class_name = "%s%sGraphForm" % (app_name, model_name)
    attrs = {'initial': {'app': app_name, 'model': model_name},
             '_selected_action': CharField(widget=MultipleHiddenInput),
             'select_across': BooleanField(initial='0', widget=HiddenInput, required=False),
             'app': CharField(initial=app_name, widget=HiddenInput),
             'model': CharField(initial=model_name, widget=HiddenInput),
             'graph_type': ChoiceField(label="Graph type", choices=graphs, required=True),
             'axes_x': ChoiceField(label="Group by and count by", choices=model_fields, required=True),
             #             'axes_y' : ChoiceField(label="Y values", choices=model_fields, required=False),
    }

    return DeclarativeFieldsMetaclass(str(class_name), (Form,), attrs)


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
        'header': BooleanField(label='Header', initial=False, required=False),
        'validate': BooleanField(label='Form validation', initial=False, required=False),
        'preview_all': BooleanField(label='Preview all records', initial=False, required=False),
        'columns_count': columns_count,
        'sample': rows,
        '_model': model,
        '_fields': model._meta.fields,
        '_filename': csv_filename,
        '_dialect': dialect
    }

    for i, f  in enumerate(model._meta.fields):
        attrs['col_%s' % i] = ColumnField(choices=columns_def, required=False)
        attrs['fld_%s' % i] = ChoiceField(choices=model_fields, required=False)
        attrs['rex_%s' % i] = RegexField(label='', initial='(.*)', required=False)
        attrs['key_%s' % i] = BooleanField(label='', initial=False, required=False)

    return DeclarativeFieldsMetaclass(str(class_name), (CSVPRocessorForm,), attrs)


@contextmanager
def open_csv(filename):
    fd = open(filename, 'rb')
    dialect = csv.Sniffer().sniff(fd.read(2048))
    fd.seek(0)
    csv_reader = csv.reader(fd, dialect=dialect)
    yield csv_reader
    fd.close()

class CSVPRocessorForm(Form):
    def _head(self, rows=10):
        with open_csv(self._filename) as csv:
            output = []
            for i in range(rows):
                output.append(csv.next())
        return output
    
    def clean(self):
        found = False
        for i, f  in enumerate(self._fields):
            col_name = 'col_%s' % i
            fld_name = 'fld_%s' % i
            if self.cleaned_data[col_name] >= 0:
                if not self.cleaned_data[fld_name]:
                    self._errors[fld_name] = self.error_class(['Set field for this column'])
                    raise ValidationError("Please fix errors below")
                found = True
            if self.cleaned_data[fld_name]:
                if self.cleaned_data[col_name] < 0:
                    self._errors[col_name] = self.error_class(['Set column for this field'])
                    raise ValidationError("Please fix errors below")
                found = True

        if not found:
            raise ValidationError("Please set columns mapping")
        return self.cleaned_data

    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        top_errors = self.non_field_errors() # Errors that should be displayed above all fields.
        output, hidden_fields = [], []
        for name in ('header', 'preview_all', 'validate'):
            field = self.fields[name]
            bf = BoundField(self, field, name)
            bf_errors = self.error_class(
                [conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
            if bf_errors:
                top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
            output.append('<tr><td class="label" colspan="3">%s</td><td>%s</td></tr>' % (bf.label, unicode(bf)))

        output.append('<tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (
            _('Column'), _('Field'), _('Regex'), _('Primary Key')))

        for i, f  in enumerate(self._fields):
            line = []
            error_line = []
            rowid = self.fields['col_%s' % i].label
            for n in ('col_%s', 'fld_%s', 'rex_%s', 'key_%s'):
                name = n % i
                field = self.fields[name]
                bf = BoundField(self, field, name)
                bf_errors = self.error_class(
                    [conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
                error_line.append(force_unicode(bf_errors), )
                line.append('<td class=%(class)s>%(field)s</td>' %
                            {'field': unicode(bf),
                             'errors': force_unicode(bf_errors),
                             'class': n[:3],
                             'n': n,
                             'i': i,
                             }
                )
            output.append('<tr><td  colspan="4">%s</td></tr>' % ''.join(error_line))
            output.append('<tr>%(line)s</tr>' % {'line': ''.join(line), 'rowid': rowid})

        if top_errors:
            output.insert(0, error_row % force_unicode(top_errors))

        return mark_safe(u'\n'.join(output))

    def as_hidden(self):
        output, hidden_fields = [], []
        for name, field in self.fields.items():
            field.widget = HiddenInput({'readonly':'readonly'})
            bf = BoundField(self, field, name)
            output.append( unicode(bf) )
        return mark_safe(u'\n'.join(output))

    def as_table(self):
        "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self._html_output(
            normal_row=u'<tr%(html_class_attr)s><th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>',
            error_row=u'<tr><td colspan="4">%s</td></tr>',
            row_ender=u'</td></tr>',
            help_text_html=u'<br /><span class="helptext">%s</span>',
            errors_on_separate_row=False)

