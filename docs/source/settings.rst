.. include globals.rst
.. _settings:


========
Settings
========
.. contents::
    :local:
    :depth: 1


.. setting:: IADMIN_CONFIG
IADMIN_CONFIG
+++++++++++++

iAdmin default configuration::

    { 'count_rows': True,
    }


* **show** : callback to chek if the file/directory should be showed or not. `fso` is a :class:`iadmin.fm.fs.FileSystemObject`


.. setting:: IADMIN_FILE_UPLOAD_MAX_SIZE
IADMIN_FILE_UPLOAD_MAX_SIZE
+++++++++++++++++++++++++++
Max size allowed for file upload via filemanage. Default 2000000 bytes


.. setting:: IADMIN_FM_ROOT
IADMIN_FM_ROOT
++++++++++++++
Absolute path to the root directory of the file manager. Default `MEDIA_ROOT`


IADMIN_FM_CONFIG
++++++++++++++++
Dictionary for the filemanager configuration. Default::

    { 'show': lambda fso: not fso.hidden }
