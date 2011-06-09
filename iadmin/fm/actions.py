#
import shutil
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
import os
import tempfile
from iadmin.fm.fs import Dir
from iadmin.fm.utils import url_to_path, mkdirs
#
#__author__ = 'sax'
#
def delete_selected(modeladmin, request, url):
    path = url_to_path(url)
    dir = Dir( path )
    if request.method == 'POST':
        selection = request.POST.getlist('_selected_action')
        err = 0
        for fname in selection:
            f = dir.get_file(fname)
            try:
                os.unlink( f.absolute_path)
            except OSError, e:
                err += 1
                messages.error( e )
        if err == 0:
            messages.info(request, 'All file(s) succesfully deleted')
        else:
            messages.warning(request,  'All file(s) succesfully deleted')
    return redirect(dir)

delete_selected.short_description = "Delete selected file(s)"

def tar_selected(modeladmin, request, url):
    path = url_to_path(url)
    dir = Dir( path )
    if request.method == 'POST':
        selection = request.POST.getlist('_selected_action')
        dest_dir = os.path.join(tempfile.gettempdir(), str(request.user), 'images')
        shutil.rmtree(dest_dir, ignore_errors=True)
        mkdirs(dest_dir)
        archive_name = 'archive.tar.gz'
        archive_filename = os.path.join(dest_dir, archive_name)
        import tarfile

        tar = tarfile.open(archive_filename, 'w:gz')
        for fname in selection:
            f = dir.get_file(fname)
            tar.add(f.absolute_path)
        tar.close()

        ret = HttpResponse(open(archive_filename, "rb").read(), content_type="application/x-tar")
        ret['Content-Disposition'] = 'attachment; filename="%s"' %   archive_name

        return ret

tar_selected.short_description = "Tar selected file(s)"