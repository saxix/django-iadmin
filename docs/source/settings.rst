.. include globals.rst
.. _settings:


========
Settings
========

.. py:data:: IADMIN_FILE_UPLOAD_MAX_SIZE
Max size allowed for file upload via filemanage. Default 2000000 bytes

.. py:data:: IADMIN_FM_ROOT
Absolute path to the root directory of the file manager. Default `MEDIA_ROOT`


.. py:data:: IADMIN_FM_CONFIG
Dictionary for the filemanager configuration. Default::

    { 'show': lambda fso: not fso.hidden }


* **show** : callback to chek if the file/directory should be showed or not. `fso` is a :class:`iadmin.fm.fs.FileSystemObject`