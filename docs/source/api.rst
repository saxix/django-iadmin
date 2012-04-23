.. _api:
.. module:: iadmin.options

===
API
===

``IModelAdmin``
---------------

.. class:: IModelAdmin

    The ``IModelAdmin`` simply extends the ``ModelAdmin``

.. attribute:: IModelAdmin.add_undefined_fields

    If True add all fields of the model to the form regardless are present in ``fields`` or ``fieldset`` attribute. This flag is only useful if you want to layout only some field into the fieldset but still want all fields available for editing. When ``add_undefined_fields`` a new section **Other** will be created with all fields not listed in the fieldset.

.. _cell_filter:
.. attribute:: IModelAdmin.cell_filter

    Set ``cell_filter`` to activate drop-down menu into the cell's grid, as illustrated in the following example:

    Example::

        class IUserAdmin(UserAdmin, IModelAdmin):
            list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active')
            cell_filter = ('email', 'is_staff', 'last_name')


    .. image:: _static/cell_filter.png

.. attribute:: IModelAdmin.cell_filter_operators

    Allow to customize which filter will be available for each column

    Example::

        class IUserAdmin(UserAdmin, IModelAdmin):
            cell_filter = ('email', 'is_staff', 'last_name')
            cell_filter_operators = {'last_login': ('exact', 'not', 'lt', 'gt')}

    This will create a dropdown menu like this:

    .. image:: _static/cell_filter_operators.png


.. _list_display_rel_links:

.. attribute:: IModelAdmin.list_display_rel_links

.. attribute:: IModelAdmin.cell_menu_on_click

.. attribute:: IModelAdmin.buttons

    .. versionchanged:: 0.1.9

.. attribute:: IModelAdmin.get_context

    .. versionadded:: 0.1.9

    Returns the context to be used in each view. You can put here common context objects
    needed by your custom template without override all the views.

.. attribute:: IModelAdmin.get_template

    .. versionadded:: 0.1.9

    Returns the search path of the template from the passed filename.
    By default::

        ["<admin_site.template_prefix>/<app_label>/<model>/<template>",
         "<admin_site.template_prefix>/<app_label>/<template>",
         "<admin_site.template_prefix>/<template>",
         "iadmin/<app_label>/<model>/<template>",
         "iadmin/<app_label>/<template>",
         "iadmin/<template>",
         <template>
         ]

.. attribute:: IModelAdmin.get_model_perms

.. attribute:: IModelAdmin.get_readonly_fields

.. attribute:: IModelAdmin.get_template

    .. versionadded:: 0.1.9


``IAdminSite``
--------------

.. class:: IAdminSite


.. attribute:: IAdminSite.template_prefix

    .. versionadded:: 0.1.9

    prefix of templates for this instances.

.. attribute:: IAdminSite.process

.. attribute:: IAdminSite.autodiscover

    Similar to ``django.contrib.admin.autodiscover()`` but with the following differences:

        * here is a method of IAdminSite, so only fill the current instance
        * looks for ``__iadmin__`` attribute to determinate which Model have to been registered

    Example of ``admin.py``::

        class IUserAdmin(UserAdmin, IModelAdmin):
            list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active')

        __iadmin__ = ((User, IUserAdmin), )


.. note:: IAdminSite do not raise an exception if try register an already registered model.

.. attribute:: IAdminSite.investigate_admin

    .. versionadded:: 0.1.9

    clone ad existing ``django.contrib.admin.site`` registry into the current instance, and
    configure ``cell_filter`` to the same value as ``list_filter``


.. attribute:: IAdminSite.register

.. attribute:: IAdminSite.register_all

.. attribute:: IAdminSite.get_context

    .. versionadded:: 0.1.9

.. attribute:: IAdminSite.reverse_admin

.. attribute:: IAdminSite.format_date

.. attribute:: IAdminSite.env_info_counters

.. attribute:: IAdminSite.env_info

.. attribute:: IAdminSite.test_mail

    .. versionadded:: 0.1.9

``ITabularInline``
------------------

.. class:: ITabularInline

``ITabularList``
----------------

.. class:: ITabularList


.. module:: iadmin.utils

``Utilities``
-------------

.. function:: tabular_factory
