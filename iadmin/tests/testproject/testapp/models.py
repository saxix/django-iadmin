## -*- coding: utf-8 -*-
#pylint: disable-msg=W0212,W0232

from django.db import models
from django.contrib.auth.models import User

__all__ = ['Author',
         'Book', 'Book2',
         'Article', 'AllFields']

class Genres( models.Model ):
    name = models.CharField( max_length = 255 )

class Author( models.Model ):
    """
        aaaaaaaaaaaaaaaaaaaa
    """
    first_name = models.CharField( max_length = 255 )
    last_name = models.CharField( max_length = 255 )
    born = models.DateField( u"DateField", blank = True, null = True )
    wp_url = models.URLField( u"Wikipedia url", max_length = 255, blank = True, verify_exists = False, null = True )
    biography = models.TextField( blank = True, null = True )
    genres = models.ForeignKey( Genres, blank = True, null = True )
    nationality = models.CharField( max_length = 255, blank = True, null = True )

    last_name.alphabetic_filter = True
    born.date_range_filter = True

    class Meta:
        app_label = "testapp"
        permissions = ( 
            ( "cant_edit_wp_url", "CANNOT edit website url " ),
            ( "cant_read_wp_url", "CANNOT read website url " ),
            ( "cant_read_born", "CANNOT read born date" ),
            ( "cant_edit_born", "CANNOT edit born date" ),
            ( "cant_read_first_name", "CANNOT read first name" ),
            ( "cant_edit_first_name", "CANNOT edit first name" ),
        )

    def __unicode__( self ):
        return u'%s %s' % ( self.last_name, self.first_name )

class Book( models.Model ):
    author = models.ForeignKey( Author )
    title = models.CharField( max_length = 255, blank = False, null = False )
    abstract = models.CharField( max_length = 255, blank = True, null = True )
    year = models.IntegerField( u"year", blank = True, null = True )
    slug = models.CharField( max_length = 255, blank = True, null = True )
    order = models.IntegerField()

    year.combo_filter = True

    class Meta:
        app_label = "testapp"
        ordering = ["order"]

    def __unicode__( self ):
        return u'%s' % self.title

class Author2( Author ):
    class Meta:
        proxy = True
        app_label = "testapp"

class Book2( Book ):
    class Meta:
        proxy = True
        app_label = "testapp"

class Article( models.Model ):
    author = models.ForeignKey( Author )
    title = models.CharField( max_length = 255, blank = False, null = False )
    abstract = models.CharField( max_length = 255, blank = True, null = True )
    class Meta:
        app_label = "testapp"

    def __unicode__( self ):
        return u'%s' % self.title

class AllFields( models.Model ):
    char_field = models.CharField( u"AutoField", max_length = 255, blank = False, null = False )
    boolean_field = models.BooleanField( u"BooleanField", blank = True, default = True )
    char_field = models.CharField( u"CharField", max_length = 255, blank = True, null = True )
    # CommaSeparatedIntegerField
    date_field = models.DateField( u"DateField", blank = True, null = True )
    datetime_field = models.DateTimeField( u"DateTimeField", blank = True, null = True )
    decimal_field = models.DecimalField( u"DecimalField", blank = True, max_digits = 5, decimal_places = 4, null = True )
    email_field = models.EmailField( u"EmailField", max_length = 255, blank = True, null = True )
    file_field = models.FileField( u"FileField", blank = True, upload_to = 'uploads/', null = True )
    float_field = models.FloatField( u"FloatField", blank = True, null = True )
    image_field = models.ImageField( u"ImageField", blank = True, upload_to = 'uploads/', null = True )
    integer_field = models.IntegerField( u"IntegerField", blank = True, null = True )
    ip_field = models.IPAddressField( u"IPAddressField", blank = True, null = True )
    nboolean_field = models.NullBooleanField( u"NullBoolean", blank = True, null = True )
    pinteger_field = models.PositiveIntegerField( u"PositiveIntegerField", blank = True, null = True )
    psinteger_field = models.PositiveSmallIntegerField( u"PositiveSmallIntegerField", blank = True, null = True )
    slug_field = models.SlugField( u"SlugField", max_length = 50, null = True )
    sinteger_field = models.SmallIntegerField( u"SmallIntegerField", blank = True, null = True )
    text_field = models.TextField( u"TextField", blank = True, null = True )
    time_field = models.TimeField( u"TimeField", blank = True, null = True )
    url_field = models.URLField( u"URLField", max_length = 255, blank = True, verify_exists = False, null = True )
    # XMLField
    fk_field = models.ForeignKey( User, verbose_name = u"ForeignKey", blank = True, null = True )
#    inline_field    = models.ForeignKey('InlineTabularTest', verbose_name=u"ForeignKey (inline tabular)", blank=True, null=True)
#    inline_field2   = models.ForeignKey('InlineStackedTest', verbose_name=u"ForeignKey (inline stacked)", blank=True, null=True)
    m2m_field = models.ManyToManyField( User, verbose_name = u"ManyToManyField", blank = True, related_name = 'many_to_many', null = True )
    o2o_field = models.OneToOneField( User, verbose_name = u"OneToOneField", blank = True, related_name = 'one_to_one', null = True )

    def __unicode__( self ):
        return u'%s' % self.char_field

    class Meta:
        verbose_name = u'Django All Field test'
        verbose_name_plural = u'Django All Field tests'
        app_label = "testapp"

