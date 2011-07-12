.. _api:

===
API
===


.. class:: iadmin.options.IModelAdmin


.. attribute:: ModelAdmin.date_hierarchy

    Set ``date_hierarchy`` to the name of a ``DateField`` or ``DateTimeField``
    in your model, and the change list page will include a date-based drilldown
    navigation by that field.

    Example::

        date_hierarchy = 'pub_date'

    .. versionadded:: 1.3

    This will intelligently populate itself based on available data,
    e.g. if all the dates are in one month, it'll show the day-level
    drill-down only.
