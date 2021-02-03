# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
# import simplejson as json
import json
from django.core import serializers
from django.http import HttpResponse, JsonResponse
import logging
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login, logout

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        j=json.loads(request.body)
        username=j['username']
        password=j['password']
        json_body=json.dumps({
            "username":username,
            "password":password
        })
        user = authenticate(username=username, password=password)
        if user!=None:
            json_body={
                "code":0,
                "body":{
                    "id":user.id,
                    "username":user.username
                },
                "message":"登录成功"
            }
            logging.debug(json_body)
            return HttpResponse(json.dumps(json_body))
        else:
            json_body={
                "code":-1,
                "message":"登录失败"
            }
            logging.debug(json_body)
            return HttpResponse(json.dumps(json_body))
    else:
        json_body={
                "code":-2,
                "message":"不支持的请求方式"
            }
        logging.debug(json_body)
        return HttpResponse(json.dumps(json_body))
