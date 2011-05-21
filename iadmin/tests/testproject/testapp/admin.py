# -*- coding: utf-8 -*-
#pylint: disable-msg=E1101

from django.contrib.admin import TabularInline, StackedInline
from django.contrib.admin.models import LogEntry
from django.contrib.auth.admin import GroupAdmin as _ga, UserAdmin as _ua
from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from xadmin import admin
from xadmin.actions import action_export_master_detail_as_json
from xadmin.admin import XModelAdmin, XModelAdminButton
from xadmin.ajax.service import AjaxService
from xadmin.callbacks import get_model_change_href
from xadmin.views import export_csv
from testapp.models import *




class MessageAdmin(admin.ModelAdmin):
    pass


class UserAdmin(XModelAdmin, _ua):
    list_display   = ('username', 'first_name', 'last_name', 'email', 'date_joined', 'last_login', 'is_staff', 'is_superuser')
    search_fields  = ['username', 'first_name',  'last_name', 'email']
    list_filter    = ['is_staff', 'is_superuser', 'date_joined', 'last_login']
    date_hierarchy = 'date_joined'
    
    def add_view(self, request):
        return _ua.add_view(self, request )
    
class GroupAdmin(XModelAdmin, _ga):
    pass


def change_author_of_book(request, object_id, **kwargs):
    book = Book.objects.get(pk=object_id)  
    url = admin.site._registry[Author].get_changeview_name()
    return HttpResponseRedirect( reverse("admin:%s" % url,args=[book.author.pk]) )
#change_author_of_book.label = "aaaaaaaaaa"


class BookAdmin(XModelAdmin):
    list_display    = ('title','author', 'abstract', 'year','slug')
    list_filter     = ['author','year']
    search_fields  =  ['title', 'abstract','author__last_name']
    buttons         = [ 
                       export_csv,
                       change_author_of_book,
                       XModelAdminButton(named_url = "testapp_author_changelist"),
                       ]
    model_link_fields      = ['author']
    read_only_fields       = ['slug',]    
    enable_export_csv_url = True
    actions         = [action_export_master_detail_as_json]
    
    
class BookAdmin2(BookAdmin):
    list_display    = ('title','_author', 'abstract', 'year','slug')
    read_only = True
    verbose_name_plural = "Books (read only)"
    buttons = []
    
    _author = get_model_change_href('author')
#    def _author(self, obj):
#        return self._get_model_change_url(obj.author)
        
class ArticleAdmin(XModelAdmin):
    list_display = ['title','author', 'abstract']
    list_filter     = ['author',]

class BookStackedInline(StackedInline):
    model = Book
    verbose_name_plural = "Books"
    extra = 2
    collapseable = True
    initial_collapsed = True
    orderable = True
    
class LogEntryTabularInline(TabularInline):
    model = LogEntry
              
class ArticleTabularInline(TabularInline):
    model = Article
    verbose_name_plural = "Articles"
    extra = 1

class AllFieldsAdmin(XModelAdmin):
    list_display = ('char_field', 'boolean_field','date_field','email_field', 'image_field', 'integer_field','time_field','url_field','fk_field','_text_field')
    list_filter = ['char_field','boolean_field','date_field']
    search_fields = ('char_field', 'slug_field', 'fk_field__username')
    
    def _text_field(self, obj):
        return getattr(obj, 'text_field')[:30]
    _text_field.text_preview = True
    
class AuthorAdmin(XModelAdmin):
    fieldsets =  [
        (None, {'fields': (('last_name','first_name'),
                           ('born','wp_url'),
                           ('genres','nationality'),
                           )
                }),
        ("Biography", {'fields': ['biography'], 
                       'classes' : ('collapse',),
                       }),
        
    ]
#    def changelist_view(self, request, extra_context=None):
#        super(AuthorAdmin,self),changelist_view(request, extra_context)
#    changelist_view.label="aaaaaaaaaa"
    
    list_display   = ('first_name','last_name', 'born','wp_url')
    search_fields  = ['first_name', 'last_name' ]
    list_filter = ['last_name','born']
    date_hierarchy = 'born'
    read_only_fields = ['wp_url',]
    inlines = (BookStackedInline, ArticleTabularInline)
    fk_service = AjaxService(Author.objects.all(), ['pk',"__unicode__"], ['last_name__istartswith','first_name__istartswith']) 
    ordering = None
    actions         = [action_export_master_detail_as_json]
    #read_only_inlines = (BookStackedInline, )
    
class XAdminExtededFieldsAdmin(XModelAdmin):
    pass

admin.site.unregister(User)
admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)

#admin.site.register(Message, MessageAdmin)
#
admin.site.register(Author, AuthorAdmin)
admin.site.register(Book, BookAdmin)

#admin.site.register(Author2, AuthorAdmin2)
#admin.site.register(Author3, AuthorAdmin3)
#admin.site.register(Author4, AuthorAdmin4)
#admin.site.register(Author5, AuthorAdmin5)
admin.site.register(Book2, BookAdmin2)
admin.site.register(Article, ArticleAdmin)
admin.site.register(AllFields, AllFieldsAdmin)
#admin.site.register(XAdminExtededFields, XAdminExtededFieldsAdmin)
