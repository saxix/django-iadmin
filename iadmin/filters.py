from django.contrib.admin.filters import SimpleListFilter, FieldListFilter, RelatedFieldListFilter
from django.db import models

class FieldComboFilter(RelatedFieldListFilter):
    template = 'iadmin/filters/fieldcombofilter.html'
