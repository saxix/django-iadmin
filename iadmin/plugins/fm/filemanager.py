from _collections import defaultdict
from django import http, template
from functools import update_wrapper
from django.conf.urls.defaults import patterns, url
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect
from iadmin.plugins.base import IAdminPlugin
import utils
import os

from .fs import Dir
from .actions import delete_selected, tar_selected

ORDER_MAP =  {'s': 'size', 't':'mime', 'u':'user', 'g':'group', 'c':'ctime', 'm':'mtime'}


class FileManager(IAdminPlugin):

    actions = [delete_selected, tar_selected]

    def __init__(self, adminsite):
        super(FileManager, self).__init__(adminsite)
        self.home_dir = utils.get_document_root()
        self.actions = [(a, a.short_description) for a in self.actions]

    def index(self, request, path=None):
        """
            Show list of files in a url inside of the document root.
        """

        if request.method == 'POST':
            selection = request.POST.getlist('_selected_action')
            act = request.POST.get('action')
            if act and selection:
                response = self.actions[int(act)][0](self, request, path)
                if response:
                    return response

        url = utils.clean_path(path)
        directory = Dir(utils.url_to_path(url))

        sort_by = request.GET.get('s', 'n')
        sort_dir = request.GET.get('ot', 'asc')
        order = defaultdict(lambda : ['', '', 'asc'],
                {sort_by: ['sorted', sort_dir, sort_dir == 'asc' and 'desc' or 'asc']})
        key = ORDER_MAP.get(sort_by, None )
        if key:
            func = lambda el: getattr(el, key)
            files = sorted(directory.files, key=func, reverse=sort_dir == 'desc')
        else:
            directory.files.sort()
            files = directory.files

        return render_to_response("iadmin/fm/index.html", {'directory': directory,
                                                           'path': url,
                                                           'title' : 'FileManager',
                                                           'fmindex': reverse('%s:iadmin.fm.index' % self.name,
                                                                              kwargs={'path': ''}),
                                                           'order': order,
                                                           'filemanager' : self,
                                                           'files': files},
                                  context_instance=template.RequestContext(request))

    def view(self, request, path=None):
        path = utils.url_to_path(path)
        directory, filename  = os.path.split(path)
        fname = Dir( directory ).get_file(filename)
        f = open(fname.absolute_path, 'rb')
        return HttpResponse(f.read(), mimetype=fname.mime)

    def upload(self, request, path=None):
        """
            Upload a new file.
        """
        if not request.user.has_perm('iadmin.can_upload_file'):
            raise PermissionDenied

        from iadmin.plugins.fm.forms import UploadForm
        path = utils.url_to_path(path)
        base = Dir( path )

        url = utils.clean_path(path)

        if request.method == 'POST':
            form = UploadForm(base.absolute_path, data=request.POST, files=request.FILES)

            if form.is_valid():
                file_path = os.path.join(base.absolute_path, form.cleaned_data['file'].name)
                destination = open(file_path, 'wb+')
                for chunk in form.cleaned_data['file'].chunks():
                    destination.write(chunk)
                messages.info(request, '`%s` uploaded' % form.cleaned_data['file'].name)
                return redirect( base )
                #return redirect('admin:iadmin.fm.index', path=base.relative_path)

        else:
            form = UploadForm(base.absolute_path)

        return render_to_response("iadmin/fm/upload.html", template.RequestContext(request,
                {'form': form,
                 'directory': base,
                 'title' : 'FileManager',
                 'filemanager' : self,
                 'fmindex' : reverse('%s:iadmin.fm.index' % self.name, kwargs={'path': ''}),
                 'max_size' : utils.get_max_upload_size(), 
                 'url': url}))

    def can_rename_object(self, request, obj):
        perm = ['iadmin.can_rename_file', 'iadmin.can_rename_dir'][obj.is_directory]
        return request.user.has_perm( perm )

    def can_delete_object(self, request, obj):
        perm = ['iadmin.can_delete_file', 'iadmin.can_delete_dir'][obj.is_directory]
        return request.user.has_perm( perm )

    def delete(self, request, path):
        path = utils.url_to_path(path)
        dirname, name = os.path.split(path)
        base = Dir(dirname)
        target = base.get_child(name) #os.path.join(base.absolute_path, name)
        if not self.can_delete_object(request, target):
            raise PermissionDenied

        try:
            target.delete()
            messages.info(request, '`%s` deleted' % target)
        except (OSError, IOError), e:
            messages.error(request, 'Error deleting: %s' % str(e))
        return redirect( base )

    def mkdir(self, request):
        if not request.user.has_perm('iadmin.can_create_dir'):
            raise PermissionDenied

        path = utils.url_to_path(request.GET.get('base'))
        dirname = request.GET.get('name')
        base = Dir( path )
        target = os.path.join(base.absolute_path, dirname)
        try:
            os.mkdir(target)
            messages.info(request, target)
        except (OSError, IOError), e:
            messages.error(request, str(e))
        return redirect( base )

    def rename(self, request):
        path = utils.url_to_path(request.GET.get('base'))
        oldname = request.GET.get('oldname')
        newname = request.GET.get('newname')
        base = Dir( path )

        target = base.get_child(oldname) 
        if not self.can_rename_object(request, target):
            raise PermissionDenied

        oldpath = os.path.join(base.absolute_path, oldname)
        newpath = os.path.join(base.absolute_path, newname)
        try:
            if os.path.exists(newpath):
                raise OSError('Destination exists')
            os.rename(oldpath, newpath)
            messages.info(request, 'Successfully renamed `%s` as `%s`' % (oldname, newname))
        except (OSError, IOError), e:
            messages.error(request, str(e))
        return redirect( base )

    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view, cacheable)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        return patterns('',
                        url(r'^mkdir$',
                            wrap(self.mkdir),
                            name='iadmin.fm.mkdir'),

                        url(r'^rename$',
                            wrap(self.rename),
                            name='iadmin.fm.rename'),

                        url(r'^upload/(?P<path>.*)$',
                            wrap(self.upload),
                            name='iadmin.fm.upload'),

                        url(r'^delete/(?P<path>.*)$',
                            wrap(self.delete),
                            name='iadmin.fm.delete'),

                        url(r'^view/(?P<path>.*)/$',
                            wrap(self.view),
                            name='iadmin.fm.view'),

                        url(r'^(?P<path>.*)$',
                            wrap(self.index),
                            name='iadmin.fm.index'),
                        )


    
