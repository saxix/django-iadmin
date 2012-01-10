from django.contrib import admin
from iadmin.options import IModelAdmin
from biblio.models import Book, Author



class BookInline(admin.TabularInline):
    model = Book

class AuthorAdmin(IModelAdmin):
    inlines = [BookInline]

class BookAdmin(IModelAdmin):
    list_display = ('title', 'author')

admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)