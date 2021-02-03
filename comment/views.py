# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
import simplejson as json
from django.http import HttpResponse, JsonResponse

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

import oms.const
from oms.models.utilities_models import utilities
from .models import *
from .forms import form_comments_create, form_comments_reviwed


def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


@login_required
@permission_required('comment.COMMENTS_VIEW', login_url='/oms/forbid/')
def redirect_comments(request):
    _form_data = {}
    items = []
    try:

        biz_id = request.GET.get('biz_id', 0)
        if biz_id == 0:
            cmt = comment.objects.all().filter(parent_entity=None).order_by('-id')
        else:
            cmt = comment.objects.filter(biz_id=biz_id)
        page = request.GET.get('page', 1)
        currentPage = int(page)
        filter = request.GET.get('filter', 'all')
        status = request.GET.get('status', 'all')

        _form_data['filter'] = filter
        _form_data['full_path'] = request.get_full_path()

        items = cmt
        paginator = None

        count = len(items)
        if count > 0:
            _form_data['total'] = count

        # paginator = Paginator(items, oms.const.PAGE_SIZE)  # Show 20 contacts per page
        paginator = Paginator(items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)

        return render(request, "comments_list.html",
                      {
                          'form_data': _form_data,
                          'filter': filter,
                          'status': status,
                          'list': items,
                          'currentPage': currentPage, 'paginator': paginator,
                          'requestUrl': reverse('comments'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        _form_data['request_feature'] = 'All Comments'
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('comments'),
                      })


@csrf_exempt
@login_required
@permission_required('comment.COMMENTS_VIEW', login_url='/oms/forbid/')
def redirect_comments_details(request):
    _form_data = {}
    items = []
    try:
        form = None

        if request.method == 'POST':
            form = form_comments_reviwed(request.POST)
            c_entity = request.POST.get('entity', 0)
            full_path = request.POST.get('full_path', '#')

            logging.debug('user: %s' % request.user.id)

            com = comment()
            if not c_entity == 0:
                com_parent = comment.objects.get(id=c_entity)
                com.biz_type = com_parent.biz_type
                com.biz_id = com_parent.biz_id
                com.parent_entity = com_parent

            com.comments = request.POST.get('id_comments')
            com.assign_id = request.POST.get('id_assign')
            assign = User.objects.get(id=com.assign_id)
            com.assign_name = assign.username
            com.user_id = request.user.id
            reporter = User.objects.get(id=com.user_id)
            com.user_name = reporter.username

            com.status = '1'
            com.save()

            com_dict = utilities.convert_to_dict(com)

            logging.debug(com.__dict__)

            json_return = json.dumps(com_dict)

            logging.debug(json_return)
            return json_return
        else:
            form = form_comments_reviwed()

        entity = request.GET.get('entity', 0)
        logging.debug('entity: %s' % entity)

        _form_data['entity'] = entity

        # full_path = request.POST.get('full_path', '')
        _form_data['full_path'] = request.get_full_path()

        cmts = comment.objects.filter(id=entity)
        if len(cmts) > 0:
            cmt = cmts[0]
            items = comment.objects.filter(parent_entity=cmt)

        count = len(items)
        _form_data['total'] = count

        return render(request, "comments_list_children.pspf.html",
                      {
                          'form_data': _form_data,
                          'list': items,
                          'form': form,
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        _form_data['request_feature'] = 'All Comments'
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('comments_details'),
                      })


@csrf_exempt
@login_required
@permission_required('comment.COMMENTS_VIEW', login_url='/oms/forbid/')
def redirect_comments_close(request):
    _form_data = {}
    items = []
    try:
        form = None
        if request.method == 'POST':
            c_entity = request.POST.get('entity', 0)
            logging.debug('user: %s' % request.user.id)

            if not c_entity == 0:
                com_parent = comment.objects.get(id=c_entity)
                com = com_parent
                com.status = '3'

                com.save()

            message = {"message": "ok"}
            return message

    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        _form_data['request_feature'] = 'All Comments'
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('comments_details'),
                      })


@login_required
@permission_required('comment.COMMENTS_VIEW', login_url='/oms/forbid/')
def redirect_comments_create(request):
    form = None
    if request.method == 'POST':  # 当提交表单时

        form = form_comments_create(request.POST)  # form 包含提交的数据

        if form.is_valid():  # 如果提交的数据合法
            com = comment()
            com.biz_type = form.cleaned_data['biz_type']
            com.biz_id = form.cleaned_data['biz_id']
            com.comments = form.cleaned_data['comments']
            com.assign_id = form.cleaned_data['assign']
            assign = User.objects.get(id=com.assign_id)
            com.assign_name = assign.username
            com.user_id = request.user.id
            reporter = User.objects.get(id=com.user_id)
            com.user_name = reporter.username

            com.save()
            return HttpResponseRedirect(reverse('comments'))
        else:
            return HttpResponse('Values Check failed!')

    else:  # 当正常访问时
        # form = AddForm()
        form = form_comments_create()
    return render(request, 'comments_create.html', {'form': form})


@login_required
@permission_required('comment.COMMENTS_VIEW', login_url='/oms/forbid/')
def redirect_bizs(request):
    _form_data = {}
    try:
        biz_type = request.GET.get('biz_type', '')
        biz_id = request.GET.get('biz_id', '0')

        if biz_type == 'OPOR' or biz_type == 'PORL':
            return HttpResponseRedirect(reverse('pgorder_detail_v3') + '?number=' + biz_id)

        return HttpResponse('Only support Pg Order. Your Biz Type: %s' % biz_type)
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        _form_data['request_feature'] = 'All Comments'
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('comments'),
                      })
