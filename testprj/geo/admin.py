from django.contrib.admin.options import TabularInline
from geo.models import Country, Lake, Location, Ocean

from iadmin.utils import tabular_factory

__author__ = 'sax'

import iadmin.proxy as admin

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'country_continent')
    autocomplete_ajax = True

    search_fields = ('name',)
    cell_filter = ('country', 'country_continent', )
    list_display_rel_links = ('country', )
    
    def country_continent(self, h):
        return h.country.continent
    country_continent.admin_order_field = 'country__continent'
    country_continent.cell_filter_operators = ('lt', 'gt', 'exact', 'not')

class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'ISO_code', 'ISO3_code', 'num_code', 'fullname', 'region', 'continent')
    search_fields = ('name', 'fullname')
    cell_filter = ('region', 'continent', 'ISO_code', 'num_code')
    list_filter = ('name',)
    ajax_list_display = ('fullname',) # beacause autocomplete double check the entry here must be present one of ajax_search_fields

    inlines = (tabular_factory(Location, Inline=TabularInline), )

    def __init__(self, model, admin_site):
        super(CountryAdmin, self).__init__(model, admin_site)
        model._meta.get_field_by_name('name')[0].alphabetic_filter = True
        model._meta.get_field_by_name('num_code')[0].cell_filter_operators = ('lt', 'gt', 'exact', 'not')

    def custom_filter(self, request):
        pass
    
class LakeAdmin(admin.ModelAdmin):
    filter_horizontal = ('countries', )

class OceanAdmin(admin.ModelAdmin):
    filter_horizontal = ('countries', )

import iadmin.shortcuts.auth

admin.site.register(Country, CountryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Lake, LakeAdmin)
admin.site.register(Ocean)


from django.conf import settings
if settings.DEBUG:
    import geo
    admin.site.register_app(geo.models)

from iadmin.shortcuts import flatpages
from iadmin.shortcuts import auth
from iadmin.shortcuts import contenttypes

