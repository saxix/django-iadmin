
IModelAdmin
-----------

    * **Attributes:**

        .. py:attr:: options.iadmin.IModelAdmin.add_undefined_fields
        If true create an 'Other' fieldset section with all fields not defined in other fieldsets

        .. py:attribute:: options.iadmin.IModelAdmin.list_display_rel_links
        If true create an link to the change form of a model from the changelist cell

        .. py:attribute:: options.iadmin.IModelAdmin.cell_filter
        list of fieldnames ( columns ) that can be filtered on the changelist. Useful if the values of a filter are too
        much to be showed in the left filter panel

        .. py:attribute:: options.iadmin.IModelAdmin.autocomplete_ajax
        If true use an autocomplete ajax widget for the ForeignKey field


    * **Actions:**
        .. function:: actions.export_to_csv
        Export selected queryset as csv file. See :doc:`Export queryset as CSV </actions>`

        .. function:: actions.mass_update

        .. function:: actions.export_as_json


