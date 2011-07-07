from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils.http import urlquote
import urllib2
from iadmin.utils import Choices, K
import django.utils.simplejson as json

CONTINENTS = Choices(
                    K(AFRICA = 'AF', label = 'Africa'),
                    K(ASIA = 'AS', label = 'Asia'),
                    K(EUROPE = 'EU', label = 'Europe'),
                    K(NORTH_AMERICA = 'NA', label = 'North America'),
                    K(SOUTH_AMERICA = 'SA', label = 'South America'),
                    K(OCEANIA = 'OC', label = 'Oceania'),
                    K(ANTARTICA = 'AN', label = 'Antartica'))

REGIONS = zip(range(1, 6), ('Africa', 'Americas', 'Asia', 'Middle East', 'Central Europe', 'Est Europe'), )

class Country(models.Model):
    ISO_code = models.CharField(max_length = 2, unique = True, blank=False, null=False, db_index = True)
    ISO3_code = models.CharField(max_length = 3, blank = True, null = True)
    num_code = models.CharField(max_length = 3, blank = True, null = True)
    name = models.CharField(max_length = 100, db_index = True)
    fullname = models.CharField(max_length = 100, db_index = True)


    region = models.IntegerField(choices = REGIONS, blank = True, null = True)
    continent = models.CharField(choices = CONTINENTS.choices(), max_length = 2)

    class Meta:
        app_label = 'geo'
        verbose_name_plural = 'Countries'
        ordering = ['name']

    def __unicode__(self):
        return "%s" % self.fullname

class Location(models.Model):
    """ Geographical location ( city, place everything with a name and Lat/Lng

    >>> 1+1
    2

    """
    ACCURACY = Choices(
        K(NONE=0, label='Nessuna'),
        K(COUNTRY=10, label='Country'),
        K(EXACT=20, label='Exact'),
        K(MANUAL=30, label='Manual'),
        K(COMPAS=40, label='Compas')
    )
    country = models.ForeignKey('Country', db_index = True)
    code = models.CharField(max_length = 4, blank=False, null=False, unique=True)
    name = models.CharField(max_length = 100, db_index = True)
    description = models.CharField(max_length = 100, blank=True, null=True)
    lat = models.DecimalField(max_digits=18, decimal_places=12, blank=True, null=True)
    lng = models.DecimalField(max_digits=18, decimal_places=12, blank=True, null=True)
    acc = models.IntegerField(choices=ACCURACY.choices(), default=ACCURACY.NONE, blank=True, null=True, help_text="Define the level of accuracy of lat/lng infos" )

    class Meta:
        verbose_name_plural = 'Locations'
        verbose_name = 'Location'
        app_label = 'geo'
        ordering = ("name",)

    def _get_coord_from_google(self, q):
        """ Take a google url and trasform in target format.
            Build  a request and return a json load from response
        """
        target =  urlquote( q )
        url = 'http://ajax.googleapis.com/ajax/services/search/local?v=1.0&q={0}'.format( target )
        request = urllib2.Request( url, None, {'Referer': settings.GMAP_DOMAIN})
        response = urllib2.urlopen(request, timeout=10)
        ret = json.load(response)
        return ret

    def store_coords(self):
        """ Store the Location coordinate """
        for acc, q in ( (Location.ACCURACY.EXACT, "{0.name} {0.country}".format(self)),
                        (Location.ACCURACY.COUNTRY, "{0.country}".format(self)) ):
            ret = self._get_coord_from_google( q )
            if ret['responseStatus'] == 200:
                if len( ret['responseData']['results']) >=1 :
                    self.lat = Decimal(ret['responseData']['results'][0]['lat'])
                    self.lng = Decimal(ret['responseData']['results'][0]['lng'])
                    self.acc = acc
                    return
        self.lat = 0
        self.lng = 0
        self.acc = Location.ACCURACY.NONE

    def save(self, force_insert=False, force_update=False, using=None):
        if self.lat is None and hasattr(settings, 'GMAP_DOMAIN'):
            self. store_coords()

        self.code = self.code.upper()
        self.name = self.name.title()
        super(Location, self).save(force_insert, force_update)

    def __unicode__(self):
        return u"{0.name} ({0.country})".format(self)

class Ocean(models.Model):
    name = models.CharField(max_length = 100, db_index = True)
    countries = models.ManyToManyField(Country, blank=True, null=True)

    def __unicode__(self):
        return unicode(self.name)

class Sea(models.Model):
    name = models.CharField(max_length = 100, db_index = True)
    countries = models.ManyToManyField(Country, blank=True, null=True)

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        app_label = 'geo'
        ordering = ['name']

class Lake(models.Model):
    name = models.CharField(max_length = 100, db_index = True)
    countries = models.ManyToManyField(Country, blank=True, null=True)
    area = models.DecimalField(max_digits=3, decimal_places=2 )

    def __unicode__(self):
        return unicode(self.name)

    class Meta:
        app_label = 'geo'
        ordering = ['name']
