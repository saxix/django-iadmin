import csv
from django.db.models.fields.related import ForeignKey
from django.forms.fields import  CharField, BooleanField
from django.db.models.loading import get_models, get_apps, get_app, get_model
from django.forms.fields import ChoiceField, FileField
from django.forms.forms import Form, DeclarativeFieldsMetaclass, BoundField
from django.forms.widgets import Input, HiddenInput, MultipleHiddenInput
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import re

__author__ = 'sax'

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
    for k,v in choices:
        if str(v) == str(value):
            return True, v

    return False, None

def set_model_attribute(instance, name, value, rex=None):
    if value == 'None':
        value = None
    field, model, direct, m2m = instance._meta.get_field_by_name(name)

    if isinstance(field, ForeignKey):
        m = re.compile(rex).match( value )

    elif hasattr(field, 'flatchoices'):
        choices = Lookup(getattr(field , 'flatchoices'))
        if value in choices.values():
            value = choices.get_key(value)
    setattr(instance, name, value)

    
class ImportForm(Form):
    model = ChoiceField()
    csv = FileField()

    def __init__(self, app, model, data=None, files=None, auto_id='id_%s', prefix=None, initial=None):
        super(ImportForm, self).__init__(data, files, auto_id, prefix, initial)
        if self.data:
            app, model = self.data['model'].split(':')

        if model:
            m = "%s:%s" % ( app, model)
            self.fields['model'].choices = [(m, m)]
            self.fields['model'].widget = Input({'readonly':'readonly'})
            self.initial['model'] = m
        elif app:
            self.fields['model'].choices = _get_all_models(app)
        else:
            self.fields['model'].choices = _get_all_models()

def graph_form_factory(model):
    app_name = model._meta.app_label
    model_name = model.__name__
    
    model_fields = [(f.name, f.verbose_name) for f in model._meta.fields if not f.primary_key]
    graphs = [('PieChart', 'PieChart'),('BarChart', 'BarChart')]
    model_fields.insert(0, ('', 'N/A'))
    class_name = "%s%sGraphForm" % (app_name, model_name)
    attrs = {'initial': {'app': app_name, 'model': model_name},
             '_selected_action' : CharField(widget=MultipleHiddenInput),
             'select_across': BooleanField(initial='0', widget=HiddenInput, required=False),
             'app': CharField(initial=app_name, widget=HiddenInput),
             'model': CharField(initial=model_name, widget=HiddenInput),
             'graph_type' : ChoiceField(label="Graph type", choices=graphs, required=True),
             'axes_x' : ChoiceField(label="Group by and count by", choices=model_fields, required=True),
#             'axes_y' : ChoiceField(label="Y values", choices=model_fields, required=False),
    }

    return DeclarativeFieldsMetaclass(str(class_name), (Form,), attrs)

def csv_processor_factory(app_name, model_name, csv_filename):
    """
      factory for Model specific CSVPRocessorForm 
    """
    fd = open(csv_filename, 'r')
    dialect = csv.Sniffer().sniff(fd.read(2048))
    fd.seek(0)
    csv_reader = csv.reader(fd, dialect=dialect)
    row = csv_reader.next()
    fd.close()

    model = get_model(app_name, model_name)

    model_fields = [('', '-- ignore --')] + [(f.name, f.name) for f in model._meta.fields]
    class_name = "%s%sImportForm" % (app_name, model_name)
    attrs = {'initial': {'app': app_name, 'model': model_name},
             'app': CharField(initial=app_name, widget=HiddenInput),
             'model': CharField(initial=model_name, widget=HiddenInput),
             'header': BooleanField(label='Header', initial=False, required=False),
             'columns_count': len(row),
             '_filename': csv_filename,
             '_dialect': dialect, '_model': model}

    for i, cell in enumerate(row):
        attrs['col_%s' % i] = ChoiceField(label="Column %s (%s)" % (i + 1, cell), choices=model_fields, initial=cell, required=False)
        attrs['rex_%s' % i] = CharField(label='', initial='', required=False)
        attrs['key_%s' % i] = BooleanField(label='', initial=False, required=False)

    return DeclarativeFieldsMetaclass(str(class_name), (CSVPRocessorForm,), attrs)


class CSVPRocessorForm(Form):
    app = CharField()
    model = CharField()

    def _head(self, rows=10):
        fd = open(self._filename, 'r')
        csv_reader = csv.reader(fd, dialect=self._dialect)
        output = []
        for i in range(rows):
            output.append(csv_reader.next())
        fd.close()
        return output


    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        top_errors = self.non_field_errors() # Errors that should be displayed above all fields.
        output, hidden_fields = [], []
        for name, field in (('header', self.fields['header']), ):
            bf = BoundField(self, field, name)
            bf_errors = self.error_class(
                [conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
            if bf_errors:
                top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
            output.append('<tr><td>%s</td><td colspan=4>%s</td></tr>' % (bf.label, unicode(bf)) )
        sample = self._head()

        for i in range(self.columns_count):
            line = []
            rowid = self.fields['col_%s' % i].label
            for n in ('col_%s', 'rex_%s', 'key_%s'):
                name = n % i
                field = self.fields[name]
                bf = BoundField(self, field, name)
                bf_errors = self.error_class([conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.

                line.append('<td>%(errors)s %(field)s</td>' %
                           {'field': unicode(bf),
                            'errors': force_unicode(bf_errors),
                            'n': n,
                            'i': i,
                            }
                )
            line.append('<td>%s</td>' % ' | '.join([s[i] for s in sample]))
            output.append('<tr><td>%(rowid)s</td>%(line)s</tr>' % {'line': ''.join(line), 'rowid':rowid })

        if top_errors:
            output.insert(0, error_row % force_unicode(top_errors))

        for name, field in (('app', self.fields['app']), ('model', self.fields['model'])):
            bf = BoundField(self, field, name)
            hidden_fields.append(unicode(bf))
            output.append('<tr><td colspan=5>%s</td></tr>' % unicode(bf) )

        return mark_safe(u'\n'.join(output))

    def as_table(self):
        "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self._html_output(
            normal_row=u'<tr%(html_class_attr)s><th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>',
            error_row=u'<tr><td colspan="2">%s</td></tr>',
            row_ender=u'</td></tr>',
            help_text_html=u'<br /><span class="helptext">%s</span>',
            errors_on_separate_row=False)

