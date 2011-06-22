from django.template.defaultfilters import filesizeformat
import os

from django import forms
from django.utils.translation import ugettext as _
from . import utils


class UploadForm(forms.Form):

    def __init__(self, path, *args, **kwargs):
        self.path = path
        super(UploadForm, self).__init__(*args, **kwargs)

    file = forms.FileField()

    def clean_file(self):
        filename = self.cleaned_data['file'].name

        if os.access(os.path.join(self.path, filename), os.F_OK):
            raise forms.ValidationError(_('File already exists.'))

        file_size = self.cleaned_data['file'].size
        max_size = utils.get_max_upload_size()
        if file_size > max_size:
            raise forms.ValidationError(_(u'Filesize (%s) exceeds allowed Upload Size (%s).' %
                                          (filesizeformat(file_size),filesizeformat(max_size))))

        return self.cleaned_data['file']
