.. include:: globals.rst
.. module:: iadmin.actions
.. |csv| replace:: :py:mod:`csv`



.. _actions:



=======
Actions
=======


Export queryset as CSV
======================

This action use the standard python |csv| module


Options
-------

.. sidebar:: CSV Options

    .. list-table:: CSV Options
       :widths: 15 10 30
       :header-rows: 1

       * - option
         - values
         - meaning

       * - header
         - checked/unchecked
         - create header ro with field names

       * - delimiter
         - `,` `;` `|` `:`
         - A one-character string used to separate fields. It defaults to ';'. (see: :py:const:`csv.Dialect.delimiter`)

       * - quotechar
         - " ' `
         - A one-character string used to quote fields containing special characters, such as the delimiter or quotechar, or which contain new-line characters. It defaults to '"'.

       * - quoting
         -
         - see `Quoting`_

       * - escapechar
         -
         - A one-character string used by the writer to escape the delimiter if quoting is set to QUOTE_NONE and the quotechar if doublequote is False. On reading, the escapechar removes any special meaning from the following character. It defaults to None, which disables escaping.

       * - datetimeformat
         - see strftime_
         - format used to represent DateTimeField_

       * - dateformat
         - see strftime_
         - format used to represent DateField_

       * - timeformat
         - see strftime_
         - format used to represent TimeField_

       * - columns
         -
         - which columns will be insert into csv file.



.. image:: _static/export_csv.png

Date & Time Formatting
""""""""""""""""""""""
These fields allow to configure formatting of DateTimeField_, DateField_ and TimeField_ django fields or their subclasses.
An ajax service show how the value will be formatted.


Quoting
"""""""

.. py:data:: QUOTE_ALL

   Instructs :class:`csv.writer` objects to quote all fields.


.. py:data:: QUOTE_MINIMAL

   Instructs :class:`csv.writer` objects to only quote those fields which contain
   special characters such as *delimiter*, *quotechar* or any of the characters in
   *lineterminator*.


.. py:data:: QUOTE_NONNUMERIC

   Instructs :class:`csv.writer` objects to quote all non-numeric fields.

   Instructs the reader to convert all non-quoted fields to type *float*.


.. data:: QUOTE_NONE

   Instructs :py:class:`csv.writer` objects to never quote fields.  When the current
   *delimiter* occurs in output data it is preceded by the current *escapechar*
   character.  If *escapechar* is not set, the writer will raise :exc:`Error` if
   any characters that require escaping are encountered.


Export queryset as fixture
==========================

TODO


Mass update
===========

Allow you to 'mass update' muliple rows to a specific value. Each row can be set of ignored. This action *do not* use
manager method `update` neither custom sql instead use the slower method `save` for each object to ensure custom validation.


