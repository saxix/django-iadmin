from django.contrib import admin
from biblio.models import Book, Author



class BookInline(admin.TabularInline):
    model = Book

class AuthorAdmin(admin.ModelAdmin):
    inlines = [BookInline]

class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author')

admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)