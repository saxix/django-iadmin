#
from django.conf import settings
from django.contrib.admin.util import lookup_field
from django.db import models
from django.shortcuts import render_to_response
from django.template.context import RequestContext

__author__ = 'sax'


from django.contrib.admin.views.main import ChangeList

class IChangeList(ChangeList):
    pass



AGENTS = { lambda x: 'Firefox' in x : ['Firefox', 'iadmin/nojs/firefox.html'],
           lambda x: 'Chrome' in x : ['Chrome', 'iadmin/nojs/chrome.html'],




}

def nojs(request):
    for k, v in AGENTS.items():
        if (k(request.META['HTTP_USER_AGENT'])):
            name, template = v
            
    ctx = { 'browser': name,
            'text': 'Preferences -&gt; Security Tab -&gt; Make sure "Enable JavaScript" is checked.',
            'img': 'iadmin/img/nojs/ie/1.png',
    }
    return render_to_response(template, RequestContext(request, ctx))