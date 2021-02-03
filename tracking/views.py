# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
# import simplejson as json
import json
from django.core import serializers
from django.http import HttpResponse, JsonResponse

# Create your views here.
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import logging
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from django.db import connections
from django.db import transaction
import math

from django.contrib.auth import get_user_model

User = get_user_model()

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission
from util.db_helper import *
import pytz

from pg_oms import settings
from qc.models import glasses_final_inspection_controller
import requests

def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })
