from _collections import defaultdict
from datetime import datetime
from grp import getgrgid
import mimetypes
from pwd import getpwuid
from django import http, template
from functools import update_wrapper
from django.conf.urls.defaults import patterns, url
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from iadmin.fm.forms import UploadForm
import utils
import os


class Base(object):
    def __init__(self, path ):
        self.relative_path = path
        self.url = utils.clean_path(path)
        self.absolute_path = os.path.join(utils.get_document_root(), self.relative_path)
        self.path = self.relative_path.split('/')
        self.name = self.path[-1]
        #        self.fileurl = utils.clean_path( self.relative_path)
        self.can_read = os.access(self.absolute_path, os.R_OK)
        self.can_write = os.access(self.absolute_path, os.W_OK)

    def _scan(self):
        try:
            return os.listdir(self.absolute_path)
        except OSError:
            raise http.Http404

    @property
    def files(self):
        _files = []
        listing = self._scan()
        for entry in listing:
            filesystem_path = os.path.join(self.absolute_path, entry)
            if os.path.isdir(filesystem_path):
                item = Dir(self, entry)
            else:
                item = File(self, entry)
            _files.append(item)
        _files.sort()
        return _files

    @property
    def breadcrumbs(self):
        elements = []
        for i, el in enumerate(self.path[::-1]):
            elements.insert(0, ['/'.join(self.path[:-i]), el + '/'])
        elements.insert(0, ['', '/'])
        return elements[:-1]

    def __str__(self):
        return self.name

perms = ['---', '--x', '-w-', '-wx', 'r--', 'r-x', 'rw-', 'rwx']
class FileSystemObject(object):
    def __init__(self, owner, name):
        self.owner = owner
        self.name = name

        self.relative_path = os.path.join(owner.relative_path, name)
        self.absolute_path = os.path.join(utils.get_document_root(), self.relative_path)
        #        self.fileurl = utils.clean_path( self.relative_path  )


        self.mime = mimetypes.guess_type(self.absolute_path, False)[0] or ''
        self.can_read = os.access(self.absolute_path, os.R_OK)
        self.can_write = os.access(self.absolute_path, os.W_OK)
        self.is_link = os.path.islink(self.absolute_path)
        try:
            itemstat = os.stat(self.absolute_path)
            self.user = getpwuid(itemstat.st_uid)[0]
            self.group = getgrgid(itemstat.st_gid)[0]
            self.size = itemstat.st_size
            self.ctime = datetime.fromtimestamp(itemstat.st_ctime)
            self.mtime = datetime.fromtimestamp(itemstat.st_mtime)
            octs = "%04d" % int(oct(itemstat.st_mode & 0777))
            self.perms_numeric = octs
            self.perms = "%s%s%s" % (perms[int(octs[1])],
                                     perms[int(octs[2])],
                                     perms[int(octs[3])])
        except:
            self.user = self.group = self.perms_numeric = self.perms = ''
            self.size = self.ctime = self.mtime = None

    @property
    def fileurl(self):
        if self.owner.name:
            return '/'.join((self.owner.name, self.name))
        else:
            return self.name


class File(FileSystemObject):
    is_directory = False

    def __init__(self, owner, name):
        super(File, self).__init__(owner, name)
        self.can_edit = self.mime in ['text', ]

    @property
    def fileurl(self):
        return reverse('%s:iadmin.fm.view' % self.owner.namespace, kwargs={'path': self.relative_path})

    def __lt__(self, other):
        if other.is_directory:
            return False
        else:
            return self.name < other.name


    def display(self):
        if self.mime in ['image/png', ]:
            return '<a href="%s">%s</a>' % (self.fileurl, self.name)
        else:
            return '-------------'

    def __repr__(self):
        return "%s:%s" % (self.mime, self.name)


class Dir(FileSystemObject):
    is_directory = True
    can_edit = False

    @property
    def parent(self):
        return reverse('admin:fm:iadmin.fm.index', kwargs={'path': '/'.join(self.path[:-1])})

    def __lt__(self, other):
        if other.is_directory:
            return self.name < other.name
        else:
            return True


class FileManager(AdminSite):
#    app_name = name = 'admin'
    parent = None

    def __init__(self, name='fm', app_name='fm'):
        super(FileManager, self).__init__(name, app_name)


    def index(self, request, path=None):
        """
            Show list of files in a url inside of the document root.
        """

        #        if request.method == 'POST':
        #            if request.POST.get('action') == 'delete_selected':
        #                response = delete_selected(request, url)
        #                if response:
        #                    return response

        url = utils.clean_path(path)
        directory = Base(url)
        directory.namespace = self.name

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
                                                           'files': files},
                                  context_instance=template.RequestContext(request))

    def view(self, request, path=None):
        url = utils.clean_path(path)
        directory = os.path.dirname(url)
        filename = os.path.basename(url)
        base = Base(directory)
        fname = File(base, filename)
        f = open(fname.absolute_path, 'rb')
        return HttpResponse(f.read(), mimetype=fname.mime)

    def upload(self, request, path=None):
        """
            Upload a new file.
        """
        url = utils.clean_path(path)
        base = Base(url)
        #path = os.path.join(utils.get_document_root(), url)

        if request.method == 'POST':
            form = UploadForm(base.absolute_path, data=request.POST, files=request.FILES)

            if form.is_valid():
                file_path = os.path.join(base.absolute_path, form.cleaned_data['file'].name)
                destination = open(file_path, 'wb+')
                for chunk in form.cleaned_data['file'].chunks():
                    destination.write(chunk)

                return redirect('admin:iadmin.fm.index', path=url)
        else:
            form = UploadForm(base.absolute_path)

        return render_to_response("iadmin/fm/upload.html", template.RequestContext(request,
                {'form': form,
                 'directory': base,
                 'fmindex' : reverse('%s:iadmin.fm.index' % self.name, kwargs={'path': ''}),
                 'max_size' : utils.get_max_upload_size(), 
                 'url': url}))


    def delete(self, request, path):
        dirname = os.path.dirname(path)
        name = os.path.basename(path)
        base = Base(dirname)
        target = os.path.join(base.absolute_path, name)
        try:
            if os.path.isdir(target):
                os.rmdir(target)
            else:
                os.unlink(target)
            messages.info(request, '`%s` deleted' % target)
        except (OSError, IOError), e:
            messages.error(request, 'Error deleting: %s' % str(e))
        return HttpResponseRedirect(reverse('%s:iadmin.fm.index' % self.name, kwargs={'path': base.relative_path}))

    def mkdir(self, request):
        base = Base(request.GET.get('base'))
        dirname = request.GET.get('name')
        target = os.path.join(base.absolute_path, dirname)
        try:
            os.mkdir(target)
            messages.info(request, target)
        except (OSError, IOError), e:
            messages.error(request, str(e))

        return HttpResponseRedirect(base.relative_path)

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
    
