from django.db import models

class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __unicode__(self):
        return u"%s, %s" %(self.last_name, self.first_name)

class Book(models.Model):
    author = models.ForeignKey(Author)
    title = models.CharField(max_length=50)

    def __unicode__(self):
        return unicode( self.title )