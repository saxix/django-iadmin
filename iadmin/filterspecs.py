# -*- coding: utf-8 -*-
'''
Created on 04/lug/2009

@author: sax
'''

from django.utils.encoding import smart_unicode, iri_to_uri
from django.utils.translation import ugettext as _
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.contrib.admin.filterspecs import FilterSpec, ChoicesFilterSpec, RelatedFilterSpec, AllValuesFilterSpec
from django.template.context import Context
from django.template.loader import get_template

class NullFilterSpec(FilterSpec):
    def __init__(self, f, request, params, model, model_admin, field_path=None):
        super(NullFilterSpec, self).__init__(f, request, params, model, model_admin)
        self.lookup_kwarg = '%s__isnull' % f.name
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)

    def choices(self, cl):
        yield {'selected': self.lookup_val is None,
               'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
               'display': _('All')}
        for k, v in ((True,_('Null')),('',_('With value'))):
            yield {'selected': k == self.lookup_val,
                    'query_string': cl.get_query_string({self.lookup_kwarg: k}),
                    'display': v}

FilterSpec.register(lambda f: f.null, NullFilterSpec)


from django.db import models
class DateRangeFilterSpec(FilterSpec):
    USE_OUTPUT_FUNC = True
    template = 'xadmin/widgets/date_range_filter.html'
    
    def __init__(self, f, request, params, model, model_admin, field_path=None):
        super(DateRangeFilterSpec, self).__init__(f, request, params, model, model_admin)
        self._from = request.GET.get('born__gte', "")
        self._to = request.GET.get('born__lte', "")
        
    def title(self):
        return self.field.verbose_name
    
    
    def output(self, cl):
        p ={'title': self.field.verbose_name,
            'from': self._from,
            'to':self._to,
            'query_string': cl.get_query_string({}, ['born__gte', 'born__lte']),
            }
    
        t = get_template(self.template)        
        return  t.render(Context(p)) 
    
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'date_range_filter', False) and \
                      isinstance(f, models.DateField), 
                      DateRangeFilterSpec) )

class AlphabeticFilterSpec(ChoicesFilterSpec):
    """
    original code: http://djangosnippets.org/snippets/1051/

    Adds filtering by first char (alphabetic style) of values in the admin
    filter sidebar. Set the alphabetic filter in the model field attribute
    'alphabetic_filter'.

    my_model_field.alphabetic_filter = True

    or

    class MyAdmin(iadmin.IModelAdmin):
        def __init__(self, model, admin_site):
            super(CountryAdmin, self).__init__(model, admin_site)
            model._meta.get_field_by_name('name')[0].alphabetic_filter = True

    """
    USE_OUTPUT_FUNC = True
    def __init__(self, f, request, params, model, model_admin, field_path=None):
        super(AlphabeticFilterSpec, self).__init__(f, request, params, model,
                                                   model_admin)
        self.lookup_kwarg = '%s__istartswith' % f.name
        self.lookup_val = request.GET.get(self.lookup_kwarg, None)
        values_list = model.objects.values_list(f.name, flat=True)
        # getting the first char of values
        self.lookup_choices = list(set(val[0] for val in values_list if val))
        self.lookup_choices.sort()

    def choices(self, cl):
        yield {'selected': self.lookup_val is None,
                'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
                'display': _('All')}
        for val in self.lookup_choices:
            yield {'selected': smart_unicode(val) == self.lookup_val,
                    'query_string': cl.get_query_string({self.lookup_kwarg: val}),
                    'display': val.upper()}
    def title(self):
        return _('%(field_name)s that starts with') % \
            {'field_name': self.field.verbose_name}

    def output(self, cl):
        t = []
        if self.has_output():
            t.append(_(u'<h3>By %s:</h3>\n<div class="alphabetic-filter">\n') % escape(self.title()))
            for choice in self.choices(cl):
                t.append(u'&nbsp;<span%s><a href="%s">%s</a></span>\n' % \
                    ((choice['selected'] and ' class="selected"' or ''),
                     iri_to_uri(choice['query_string']),
                     choice['display']))
            t.append('</div>\n\n')
        return mark_safe("".join(t))
        
# registering the filter
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'alphabetic_filter', False),
                                   AlphabeticFilterSpec))

class ComboFilterSpec(AllValuesFilterSpec):
    """
    Adds filtering by first char (alphabetic style) of values in the admin
    filter sidebar. Set the alphabetic filter in the model field attribute
    'alphabetic_filter'.

    my_model_field.combo_filter = True
    """
    USE_OUTPUT_FUNC = True
    
    def __init__(self, f, request, params, model, model_admin, field_path=None):
        super(ComboFilterSpec, self).__init__(f, request, params, model, model_admin)
        self.lookup_val = request.GET.get(f.name, None)    
        self.lookup_choices = model_admin.queryset(request).distinct().order_by(f.name).values(f.name)

    def choices(self, cl):
        yield {'selected': self.lookup_val is None,
               'query_string': cl.get_query_string({}, [self.field.name]),
               'display': _('All')}
        for val in self.lookup_choices:
            val = smart_unicode(val[self.field.name])
            
            yield {'selected': self.lookup_val == val,
                   'query_string': cl.get_query_string({self.field.name: val}),
                   'display': val}
            
    def title(self):
        return _('%(field_name)s that starts with') % \
            {'field_name': self.field.verbose_name}

    def output(self, cl):
        t = []
        if self.has_output():
            t.append(_(u'<h3>By %s:</h3>\n<div>\n') % escape(self.title()))
            
            t.append(u'<select onchange="window.location.href=this.options[this.selectedIndex].value;">')
            
            for choice in self.choices(cl):
                t.append(u'<option %s value="%s">%s</option>\n' % \
                    ((choice['selected'] and ' selected="selected"' or ''),
                     iri_to_uri(choice['query_string']),
                     choice['display']
                     ))
            t.append(u'</select>\n')
            t.append('</div>\n\n')
        return mark_safe("".join(t))
        
# registering the filter
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'combo_filter', False),
                                   ComboFilterSpec))


class ComboRelatedFilterSpec(RelatedFilterSpec):
    """
    Adds filtering by first char (alphabetic style) of values in the admin
    filter sidebar. Set the alphabetic filter in the model field attribute
    'alphabetic_filter'.

    my_model_field.alphabetic_filter = True
    """
    USE_OUTPUT_FUNC = True

    def choices(self, cl):
        yield {'selected': self.lookup_val is None,
               'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
               'display': _('All')}
        for pk_val, val in self.lookup_choices:
            yield {'selected': self.lookup_val == smart_unicode(pk_val),
                   'query_string': cl.get_query_string({self.lookup_kwarg: pk_val}),
                   'display': val}

    def output(self, cl):
        t = []
        if self.has_output():
            t.append(_(u'<h3>By %s:</h3>\n<div>\n') % escape(self.title()))
            
            t.append(u'<select onchange="window.location.href=this.options[this.selectedIndex].value;">')
            
            for choice in self.choices(cl):
                t.append(u'<option %s value="%s">%s</option>\n' % \
                    ((choice['selected'] and ' selected="selected"' or ''),
                     iri_to_uri(choice['query_string']),
                     choice['display']
                     ))
            t.append(u'</select>\n')
            t.append('</div>\n\n')
        return mark_safe("".join(t))
        
# registering the filter
FilterSpec.filter_specs.insert(0, (lambda f: getattr(f, 'combo_related_filter', False) and bool(f.rel),
                                   ComboRelatedFilterSpec))