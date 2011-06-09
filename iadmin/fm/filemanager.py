from _collections import defaultdict
from django import http, template
from functools import update_wrapper
from django.conf.urls.defaults import patterns, url
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
import utils
import os

from iadmin.fm.fs import Dir
from iadmin.fm import actions



class FileManager(AdminSite):
#    app_name = name = 'admin'
    parent = None
    actions = [actions.delete_selected, actions.tar_selected]

    def __init__(self, name='fm', app_name='fm'):
        super(FileManager, self).__init__(name, app_name)
        self.home_dir = utils.get_document_root()
        self._actions = {}
        for a in self.actions:
            self._actions[a.__name__] = a


    def index(self, request, path=None):
        """
            Show list of files in a url inside of the document root.
        """

        if request.method == 'POST':
            act = request.POST.get('action')
            response = self._actions[act](self, request, path)
            if response:
                return response

        url = utils.clean_path(path)
        directory = Dir(utils.url_to_path(url))

        sort_by = request.GET.get('s', 'n')
        sort_dir = request.GET.get('ot', 'asc')

        order = defaultdict(lambda : ['', '', 'asc'],
                {sort_by: ['sorted', sort_dir, sort_dir == 'asc' and 'desc' or 'asc']})

        key = None
        if sort_by == 's':
            key = lambda el: el.size
        elif sort_by == 't':
            key = lambda el: el.mime
        elif sort_by == 'u':
            key = lambda el: el.user
        elif sort_by == 'g':
            key = lambda el: el.group
        elif sort_by == 'c':
            key = lambda el: el.ctime
        elif sort_by == 'm':
            key = lambda el: el.mtime

        if key:
            files = sorted(directory.files, key=key, reverse=sort_dir == 'desc')
        else:
            directory.files.sort()
            files = directory.files

        return render_to_response("iadmin/fm/index.html", {'directory': directory,
                                                           'path': url,
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
        from iadmin.fm.forms import UploadForm
        path = utils.url_to_path(path)
        base = Dir( path )

        url = utils.clean_path(path)
        #path = os.path.join(utils.get_document_root(), url)

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
                 'filemanager' : self,
                 'fmindex' : reverse('%s:iadmin.fm.index' % self.name, kwargs={'path': ''}),
                 'max_size' : utils.get_max_upload_size(), 
                 'url': url}))


    def delete(self, request, path):
        path = utils.url_to_path(path)
        dirname, name = os.path.split(path)
        base = Dir(dirname)
        target = os.path.join(base.absolute_path, name)
        try:
            if os.path.isdir(target):
                os.rmdir(target)
            else:
                os.unlink(target)
            messages.info(request, '`%s` deleted' % target)
        except (OSError, IOError), e:
            messages.error(request, 'Error deleting: %s' % str(e))
        return redirect( base )
#        return HttpResponseRedirect(reverse('%s:iadmin.fm.index' % self.name, kwargs={'path': base.relative_path}))

    def mkdir(self, request):
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
#        return HttpResponseRedirect(base.relative_path)

    def get_urls(self):
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            return update_wrapper(wrapper, view)

        return patterns('',
                        url(r'^mkdir$',
                            wrap(self.mkdir),
                            name='iadmin.fm.mkdir'),

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

    @property
    def urls(self):
        return self.get_urls() #, self.app_name, self.name
    
