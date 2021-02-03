# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import simplejson as json
from django.http import HttpResponse, JsonResponse
from django.core import serializers

# Create your views here.
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import logging
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import get_user_model

User = get_user_model()

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission

from util.response import response_message
import util
import time

from util.dict_helper import *
from util.format_helper import *

from contollers import *


def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


@login_required
@permission_required('mrp.TASKS', login_url='/oms/forbid/')
def redirect_tasks(request, parameters=''):
    _form_data = {}
    rm = response_message()
    dh = dict_helper()
    try:
        if request.method == 'POST':
            entity = parameters
            parameters = {}
            parameters['entity'] = entity

        _form_data['list'] = rm.obj
    except Exception as e:
        rm.capture_execption(e)
        json_body = dh.convert_to_dict(rm)
        json_body = json.dumps(json_body, cls=DateEncoder)
        return HttpResponse(json_body)

    return render(
        request, "tasks.html",
        {
            "form": _form_data
        }
    )
