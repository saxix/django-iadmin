from django.contrib.admin.options import TabularInline
from geo.models import Country, Lake, Location, Ocean
from iadmin.utils import tabular_factory

__author__ = 'sax'

import iadmin.proxy as admin

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'country_continent')
    autocomplete_ajax = True
    search_fields = ('name',)
    cell_filter = ('country', 'country_continent')
    list_display_rel_links = ('country', 'country__continent')
    
    def country_continent(self, h):
        return h.country.continent
    country_continent.admin_order_field = 'country__continent'
    country_continent.admin_filter_value = 'country.continent' #TODO 

class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'ISO_code', 'ISO3_code', 'num_code', 'fullname', 'region', 'continent')
    search_fields = ('name', 'fullname')
    cell_filter = ('region', 'continent')

    inlines = (tabular_factory(Location, Inline=TabularInline),
                )

class LakeAdmin(admin.ModelAdmin):
    filter_horizontal = ('countries', )

class OceanAdmin(admin.ModelAdmin):
    filter_horizontal = ('countries', )

admin.site.register(Country, CountryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Lake, LakeAdmin)
admin.site.register(Ocean, OceanAdmin)

from django.conf import settings
if settings.DEBUG:
    import geo
    admin.site.register_missing(geo.models)

