from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from geo.models import Country, Location, Lake, Ocean

class LocationAdmin(ModelAdmin):
    list_display = ('name', 'country', 'country_continent')
    autocomplete_ajax = True
    search_fields = ('name',)
    cell_filter = ('country', 'country_continent', )
    list_display_rel_links = ('country', )

    def country_continent(self, h):
        return h.country.continent
    country_continent.admin_order_field = 'country__continent'
    country_continent.cell_filter_operators = ('lt', 'gt', 'exact', 'not')

class CountryAdmin(ModelAdmin):
    list_display = ('name', 'ISO_code', 'ISO3_code', 'num_code', 'iana_tld', 'currency', 'population', 'fullname', 'region', 'continent')
    search_fields = ('name', 'fullname')
#    cell_filter = ('region', 'continent', 'ISO_code', 'num_code')
    list_filter = ('name', 'region')
#    ajax_list_display = ('fullname',) # beacause autocomplete double check the entry here must be present one of ajax_search_fields

#    inlines = (tabular_factory(Location, Inline=TabularInline), )
#    cell_filter_operators = {'num_code': ('exact', 'not', 'lt', 'gt')}

    def __init__(self, model, admin_site):
        super(CountryAdmin, self).__init__(model, admin_site)
        model._meta.get_field_by_name('name')[0].alphabetic_filter = True
        model._meta.get_field_by_name('num_code')[0].cell_filter_operators = ('lt', 'gt', 'exact', 'not')

    def custom_filter(self, request):
        pass

class LakeAdmin(ModelAdmin):
    filter_horizontal = ('countries', )

class OceanAdmin(ModelAdmin):
    filter_horizontal = ('countries', )


admin.site.register(Country, CountryAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Lake, LakeAdmin)
admin.site.register(Ocean)


from iadmin.tests.admin import __iadmin__
