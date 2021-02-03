# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.urls import reverse

# Sytem Import
import simplejson as json
from django.http import HttpResponse, JsonResponse
import logging
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# Customize Import
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required

from util.time_delta import *
from oms.models.order_models import LabOrder
from oms.models.actions_models import Action

# Create your views here.
from util.response import response_message,json_response
from oms.const import *

from .models import statement_lab_order_daily_control

import time
from django.utils import timezone
from util.format_helper import *
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from oms.views import namedtuplefetchall
import requests
import datetime
import math


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_statement_lab_order_daily(request):
    try:
        logging.debug('asd')
        doc_type = request.GET.get('doc_type', 'LENS')

        page = request.GET.get('page', 1)
        filter = request.GET.get('filter', '')
        workshop = request.GET.get('workshop', '')
        year = request.GET.get('year', '')
        month = request.GET.get('month', '')
        day = request.GET.get('day', '')

        today = timezone.now().date()

        if year == '':
            year = today.year
        if month == '':
            month = today.month
        if day == '':
            day = today.day

        currentPage = int(page)
        _form_data = {}

        doc_types = []
        doc_types.append('LENS')
        doc_types.append('GLASSES')

        _form_data['doc_types'] = doc_types
        _form_data['doc_type'] = doc_type

        vendors = __get_arries('vendors')
        _form_data['vendors'] = vendors

        workshops = __get_arries('workshops')
        _form_data['workshops'] = workshops

        _form_data['workshop'] = workshop

        years = __get_arries('years')
        months = __get_arries('months')
        days = __get_arries('days')

        _form_data['years'] = years
        _form_data['months'] = months
        _form_data['days'] = days

        _form_data['year'] = str(year)
        _form_data['month'] = str(month)
        _form_data['day'] = str(day)

        _objects = []

        rm = response_message()

        _total = 0

        slodc = statement_lab_order_daily_control()
        rm = slodc.get_statment_list(request)

        if rm.obj:
            _objects = rm.obj

        items = []

        items = _objects

        paginator = Paginator(items, PAGE_SIZE)  # Show 20 contacts per page

        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)

        if rm.obj:
            _total = len(rm.obj)

        _form_data['total'] = _total

        return render(request, 'statement_lab_order_daily.html',
                      {
                          'rm': rm,
                          'form_data': _form_data,
                          'list': items,
                          'filter': filter,
                          'currentPage': currentPage, 'paginator': paginator,
                          'requestUrl': reverse('statement_lab_order_daily')
                      })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)


def __get_arries(par):
    pars = []
    start = 1
    end = 12
    if par == 'years':
        start = 2018
        end = 2038
    elif par == 'months':
        start = 1
        end = 12
    elif par == 'days':
        start = 1
        end = 31
    elif par == 'vendors':
        start = 1
        end = 15
    elif par == 'workshops':
        start = 1
        end = 8

    end += 1

    if par == 'vendors':
        pars.append('All')

    for i in range(start, end):
        pars.append(str(i))

    return pars


def redirect_statement_lab_order_daily_csv(request):
    rm = response_message()

    entities = request.GET.get('entities', '')
    is_full = request.GET.get('is_full', '0')

    doc_type = request.GET.get('doc_type', '')

    # return HttpResponse(is_full)

    items = []

    try:

        # 前台选中的 entity id
        entities = request.GET.get('entities', '')

        arry_entities = entities.split(',')

        # 是否需要选择全部
        is_full = request.GET.get('is_full', '0')

        if is_full == '1':
            from qc.models import lens_registration
            arry_entities = []
            slodc = statement_lab_order_daily_control()
            rm = slodc.get_statment_list(request)

            if not rm.obj == None:
                if doc_type == 'LENS':
                    for lr in rm.obj:
                        arry_entities.append(lr.laborder_id)
                else:
                    for lr in rm.obj:
                        arry_entities.append(lr.lab_order_entity)

        for entity in arry_entities:
            logging.debug(entity)

        lbos = LabOrder.objects.filter(id__in=arry_entities)

        # Print Start

        import csv, codecs

        for lbo in lbos:
            items.append(lbo.lab_number)

        logging.debug('items count: %s' % len(items))

        response = HttpResponse(content_type='text/csv')
        file_name = 'statement_lab_order_daily_csv'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'

        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)

        doc_type = request.GET.get('doc_type', 'LENS')
        if doc_type == 'LENS':
            writer.writerow(['对账单-来片登记'])
            writer.writerow([
                '#', '条码', '订单号', '订单日期', '镜架', '框型', '实际镜片SKU', '实际镜片',
                '超防水', '设计SKU', '设计',
                '棱镜度', '高散', '染色','染色描述',
                '数量[片]', '收片日期', '生产周期', '登记次数',
                '计划镜片SKU', '计划镜片', '右眼SPH', '右眼CYL', '左眼SPH', '左眼CYL','备注'
            ])
        else:
            writer.writerow(['对账单-成镜收货'])
            writer.writerow([
                '#', '条码', '订单号', '订单日期', '镜架', '框型', '实际镜片SKU', '实际镜片',
                '超防水', '设计SKU', '设计',
                '棱镜度', '高散', '染色','染色描述',
                '数量[片]', '收货日期', '生产周期', '登记次数',
                '计划镜片SKU', '计划镜片', '右眼SPH', '右眼CYL', '左眼SPH', '左眼CYL','备注'
            ])

        count = len(items)
        index = 0

        for lbo in lbos:
            index += 1

            lbo = __formate_lbo(lbo)

            if doc_type == 'LENS':

                writer.writerow([
                    index, lbo.get_bar_code, lbo.lab_number, lbo.swap_create_at, lbo.frame,lbo.frame_type,
                    lbo.act_lens_sku, lbo.act_lens_name,
                    lbo.coating_sku,
                    lbo.get_pal_design_sku, lbo.pal_design_name,
                    lbo.get_has_prism, lbo.swap_strong_cyl, lbo.get_has_tint,lbo.tint_name,
                    lbo.get_lens_quantity, lbo.swap_lens_registration_date, lbo.days_of_lens_registration,
                    lbo.get_reg_times,
                    lbo.lens_sku, lbo.lens_name, lbo.od_sph, lbo.od_cyl, lbo.os_sph, lbo.os_cyl,lbo.comments
                ])
            else:
                writer.writerow([
                    index, lbo.get_bar_code, lbo.lab_number, lbo.swap_create_at, lbo.frame,lbo.frame_type,
                    lbo.act_lens_sku, lbo.act_lens_name,
                    lbo.coating_sku,
                    lbo.get_pal_design_sku, lbo.pal_design_name,
                    lbo.get_has_prism, lbo.swap_strong_cyl, lbo.get_has_tint,lbo.tint_name,
                    lbo.get_lens_quantity, lbo.swap_lens_registration_date, lbo.days_of_lens_registration,
                    lbo.get_reg_glasses_times,
                    lbo.lens_sku, lbo.lens_name, lbo.od_sph, lbo.od_cyl, lbo.os_sph, lbo.os_cyl,lbo.comments
                ])

        return response

    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        return HttpResponse('生成订单采购订单对账单遇到异常[ %s ], 请暂时手动生成，并联系系统支持....' % e.message)


def __formate_lbo(lbo):
    lbo.swap_create_at = format_date.date2string(lbo.create_at)
    lbo.swap_has_prism = 'True' if lbo.get_has_prism == True else ''
    lbo.swap_strong_cyl = 'True' if lbo.get_strong_cyl == True else ''
    lbo.swap_has_tint = 'True' if lbo.get_has_tint == True else ''
    lbo.swap_lens_registration_date = format_date.date2string(lbo.get_lens_registration_date)
    return lbo


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_statement_lab_order_month(request):
    try:
        _form_data = {}
        doc_type = request.GET.get('doc_type', 'LENS')
        page = request.GET.get('page', 1)
        filter = request.GET.get('filter', '')
        workshop = request.GET.get('workshop', '')
        begin_date = request.GET.get('begindate', '')
        end_date = request.GET.get('enddate', '')

        currentPage = int(page)
        doc_types = []                      
        doc_types.append('LENS')                    
        doc_types.append('GLASSES')                 
                                                    
        _form_data['doc_types'] = doc_types         
        _form_data['doc_type'] = doc_type
        vendors = __get_arries('vendors')
        _form_data['vendors'] = vendors
        _form_data['filter'] = filter
        workshops = __get_arries('workshops')
        _form_data['workshops'] = workshops
        _form_data['workshop'] = workshop
        _form_data['begin_date'] = begin_date
        _form_data['end_date'] = end_date
        _total = 0
        _objects = []
        items = []
        slodc = statement_lab_order_daily_control()
        req = slodc.get_statment_month_list(request)

        if req.obj:
            _objects = req.obj
            _total = len(req.obj)

        items = _objects
        paginator = Paginator(items, PAGE_SIZE)
        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)

        _form_data['total'] = _total

        return render(request, 'statement_lab_order_month.html',
                      {
                          'rm': req,
                          'form_data': _form_data,
                          'list': items,
                          'filter': filter,
                          'currentPage': currentPage,
                          'paginator': paginator,
                          'requestUrl': reverse('statement_lab_order_month')
                      })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)



def redirect_statement_lab_order_mouth_csv(request):
    rm = response_message()

    entities = request.GET.get('entities', '')
    is_full = request.GET.get('is_full', '0')
    doc_type = request.GET.get('doc_type', '')
    items = []
    try:
        # 前台选中的 entity id
        entities = request.GET.get('entities', '')
        arry_entities = entities.split(',')
        # 是否需要选择全部
        is_full = request.GET.get('is_full', '0')
        #if is_full == '1':
        from qc.models import lens_registration
        arry_entities = []
        slodc = statement_lab_order_daily_control()
        rm = slodc.get_statment_month_list(request)
        if not rm.obj == None:
            if doc_type == 'LENS':
                for lr in rm.obj:
                    arry_entities.append(lr.laborder_id)
            else:
                for lr in rm.obj:
                    arry_entities.append(lr.lab_order_entity)

        for entity in arry_entities:
            logging.debug(entity)
        lbos = []
        if len(arry_entities) > 0 and arry_entities[0] != '':
            lbos = LabOrder.objects.filter(id__in=arry_entities)

        # Print Start

        import csv, codecs

        for lbo in lbos:
            items.append(lbo.lab_number)

        logging.debug('items count: %s' % len(items))

        response = HttpResponse(content_type='text/csv')
        file_name = 'statement_lab_order_daily_csv'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'

        response.write(codecs.BOM_UTF8)

        writer = csv.writer(response)

        doc_type = request.GET.get('doc_type', 'LENS')
        if doc_type == 'LENS':
            writer.writerow(['对账单-来片登记'])
            writer.writerow([
                '#', '条码', '订单号', '订单日期', '镜架', '框型', '实际镜片SKU', '实际镜片',
                '超防水', '设计SKU', '设计',
                '棱镜度', '高散', '染色','染色描述',
                '数量[片]', '收片日期', '生产周期', '登记次数',
                '计划镜片SKU', '计划镜片', '右眼SPH', '右眼CYL', '左眼SPH', '左眼CYL','备注'
            ])
        else:
            writer.writerow(['对账单-成镜收货'])
            writer.writerow([
                '#', '条码', '订单号', '订单日期', '镜架', '框型', '实际镜片SKU', '实际镜片',
                '超防水', '设计SKU', '设计',
                '棱镜度', '高散', '染色','染色描述',
                '数量[片]', '收货日期', '生产周期', '登记次数',
                '计划镜片SKU', '计划镜片', '右眼SPH', '右眼CYL', '左眼SPH', '左眼CYL','备注'
            ])

        count = len(items)
        index = 0

        for lbo in lbos:
            index += 1

            lbo = __formate_lbo(lbo)

            if doc_type == 'LENS':

                writer.writerow([
                    index, lbo.get_bar_code, lbo.lab_number, lbo.swap_create_at, lbo.frame,lbo.frame_type,
                    lbo.act_lens_sku, lbo.act_lens_name,
                    lbo.coating_sku,
                    lbo.get_pal_design_sku, lbo.pal_design_name,
                    lbo.get_has_prism, lbo.swap_strong_cyl, lbo.get_has_tint,lbo.tint_name,
                    lbo.get_lens_quantity, lbo.swap_lens_registration_date, lbo.days_of_lens_registration,
                    lbo.get_reg_times,
                    lbo.lens_sku, lbo.lens_name, lbo.od_sph, lbo.od_cyl, lbo.os_sph, lbo.os_cyl,lbo.comments
                ])
            else:
                writer.writerow([
                    index, lbo.get_bar_code, lbo.lab_number, lbo.swap_create_at, lbo.frame,lbo.frame_type,
                    lbo.act_lens_sku, lbo.act_lens_name,
                    lbo.coating_sku,
                    lbo.get_pal_design_sku, lbo.pal_design_name,
                    lbo.get_has_prism, lbo.swap_strong_cyl, lbo.get_has_tint,lbo.tint_name,
                    lbo.get_lens_quantity, lbo.swap_lens_registration_date, lbo.days_of_lens_registration,
                    lbo.get_reg_glasses_times,
                    lbo.lens_sku, lbo.lens_name, lbo.od_sph, lbo.od_cyl, lbo.os_sph, lbo.os_cyl,lbo.comments
                ])

        return response

    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        return HttpResponse('生成订单采购订单对账单遇到异常[ %s ], 请暂时手动生成，并联系系统支持....' % e.message)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_request_notes_list(request):
    try:
        form_data = {}
        filter = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        currentPage = int(page)
        url = settings.PURCHASE_BASE_URL + '/api/request_notes_list/'
        api_response = requests.get(url, params={"filter":filter}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        data_list = data_json['data']['data']
        form_data['total'] = len(data_json['data']['data'])
        paginator = Paginator(data_list, 20)
        try:
            data_list = paginator.page(int(page))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)

        return render(request, 'purchase_request_notes_list.html', {
            "data_list": data_list,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_request_notes_list/',
        })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_request_notes_new(request):
    try:
        form_data = {}
        data_list = []
        data_dict = {}
        frame = request.GET.get('frame', '')
        page = request.GET.get('page', 1)
        pageSize = request.GET.get('pageSize', 20)
        currentPage = int(page)
        sql = """SELECT sku,name,quantity,status FROM wms_inventory_struct """
        lab_sql = """SELECT frame, frame_type, COUNT(1) AS sales_qty from oms_laborder WHERE year(create_at)=%s AND month(create_at)=%s GROUP BY frame""" % (
        datetime.datetime.now().year, (datetime.datetime.now().month - 1))

        if frame != '':
            sql = sql + """ WHERE sku='%s'""" % frame
        sql = sql + """ ORDER BY quantity"""
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            for item in namedtuplefetchall(cursor):
                data_dict[item.sku] = {
                    'frame': item.sku,
                    'name': item.name,
                    'quantity': str(item.quantity),
                    'status': item.status,
                    'frame_type': '',
                    'sales_qty': 0,
                    'plan_rep_quantity':'',
                    'disflag':'false'
                }
            cursor.execute(lab_sql)

            for item in namedtuplefetchall(cursor):
                if item.frame in data_dict.keys():
                    data_dict[item.frame]['frame_type'] = item.frame_type
                    data_dict[item.frame]['sales_qty'] = item.sales_qty

        for value in data_dict.values():
            data_list.append(value)
        form_data['total'] = len(data_list)
        paginator = Paginator(data_list, int(pageSize))
        try:
            data_list = paginator.page(int(page))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)
        return render(request, 'purchase_request_notes_new.html',{
            "data_list":data_list,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_request_notes_new/',
        })
    except Exception as e:
        return json_response(code=-1, msg='执行失败', data='')


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_request_notes_new(request):
    try:
        return render(request, 'purchase_request_notes_new.html', {
            'requestUrl': '/purchase/purchase_request_notes_new/',
        })
    except Exception as e:
        return json_response(code=-1, msg='执行失败', data='')


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_request_notes_new_list(request):
    try:
        form_data = {}
        data_list = []
        data_dict = {}
        frame = request.GET.get('frame', '')
        page = request.GET.get('page', 1)
        pageSize = request.GET.get('pageSize', 20)
        currentPage = int(page)
        sql = """SELECT sku,name,quantity,status FROM wms_inventory_struct """
        lab_sql = """SELECT frame, frame_type, COUNT(1) AS sales_qty from oms_laborder WHERE year(create_at)=%s AND month(create_at)=%s GROUP BY frame""" % (
        datetime.datetime.now().year, (datetime.datetime.now().month - 1))

        if frame != '':
            sql = sql + """ WHERE sku like '%%%s%%'""" % frame
        sql = sql + """ ORDER BY quantity"""
        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            for item in namedtuplefetchall(cursor):
                data_dict[item.sku] = {
                 'frame': item.sku,
                 'name': item.name,
                 'quantity': str(item.quantity),
                 'status': item.status,
                 'frame_type': '',
                 'sales_qty': 0,
                 'plan_rep_quantity':'',
                 'disflag':'false'
                }
            cursor.execute(lab_sql)

            for item in namedtuplefetchall(cursor):
                if item.frame in data_dict.keys():
                    data_dict[item.frame]['frame_type'] = item.frame_type
                    data_dict[item.frame]['sales_qty'] = item.sales_qty

        for value in data_dict.values():
            data_list.append(value)
        form_data['total'] = len(data_list)
        startindex = (currentPage-1)*pageSize
        endindex = startindex + pageSize
        data_list = data_list[startindex:endindex]
        form_data['data_list'] = data_list
        return json_response(code=0, msg='执行成功', data=form_data)
    except Exception as e:
        return json_response(code=-1, msg='执行失败', data='')


# @login_required
# @permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
# def redirect_purchase_request_notes_new(request):
#     try:
#         form_data = {}
#         data_list = []
#         data_dict = {}
#         frame = request.GET.get('frame', '')
#         page = request.GET.get('page', 1)
#         pageSize = request.GET.get('pageSize', 20)
#         currentPage = int(page)
#         sql = """SELECT sku,name,quantity,status FROM wms_inventory_struct """
#         lab_sql = """SELECT frame, frame_type, COUNT(1) AS sales_qty from oms_laborder WHERE year(create_at)=%s AND month(create_at)=%s GROUP BY frame""" % (
#         datetime.datetime.now().year, (datetime.datetime.now().month - 1))
#
#         if frame != '':
#             sql = sql + """ WHERE sku='%s'""" % frame
#         sql = sql + """ ORDER BY quantity"""
#         with connections['pg_oms_query'].cursor() as cursor:
#             cursor.execute(sql)
#             for item in namedtuplefetchall(cursor):
#                 data_dict[item.sku] = {
#                     'frame': item.sku,
#                     'name': item.name,
#                     'quantity': str(item.quantity),
#                     'status': item.status,
#                     'frame_type': '',
#                     'sales_qty': 0,
#                     'plan_rep_quantity':'',
#                     'disflag':'false'
#                 }
#             cursor.execute(lab_sql)
#
#             for item in namedtuplefetchall(cursor):
#                 if item.frame in data_dict.keys():
#                     data_dict[item.frame]['frame_type'] = item.frame_type
#                     data_dict[item.frame]['sales_qty'] = item.sales_qty
#
#         for value in data_dict.values():
#             data_list.append(value)
#         form_data['total'] = len(data_list)
#         paginator = Paginator(data_list, int(pageSize))
#         try:
#             data_list = paginator.page(int(page))
#         except PageNotAnInteger:
#             # If page is not an integer, deliver first page.
#             data_list = paginator.page(1)
#         except EmptyPage:
#             # If page is out of range (e.g. 9999), deliver last page of results.
#             data_list = paginator.page(paginator.num_pages)
#         return render(request, 'purchase_request_notes_new.html',{
#             "data_list":data_list,
#             'currentPage': currentPage,
#             'paginator': paginator,
#             'requestUrl': '/purchase/purchase_request_notes_new/',
#         })
#     except Exception as e:
#         return json_response(code=-1, msg='执行失败', data='')

@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_request_notes_del(request):
    try:
        doc_number = request.GET.get("doc_number", "")
        flag = request.GET.get("flag", "")
        sku = request.GET.get("sku", "")
        url = settings.PURCHASE_BASE_URL + '/api/request_notes_del/'
        api_response = requests.get(url, params={"doc_number":doc_number,"flag":flag,"sku":sku}, headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'删除成功')
        return json_response(code=-1, msg=u'删除失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_request_notes_save(request):
    try:
        doc_number = request.GET.get("doc_number", "")
        quantity = request.GET.get("quantity", "")
        sku = request.GET.get("sku", "")
        url = settings.PURCHASE_BASE_URL + '/api/request_notes_save/'
        api_response = requests.get(url, params={"doc_number":doc_number,"quantity":quantity,"sku":sku}, headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'保存成功')

        return json_response(code=-1, msg=u'保存失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_request_notes_change_status(request):
    try:
        doc_number = request.GET.get("doc_number", "")
        url = settings.PURCHASE_BASE_URL + '/api/request_notes_change_status/'
        api_response = requests.get(url, params={"doc_number": doc_number}, headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'保存成功')

        return json_response(code=-1, msg=u'保存失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@csrf_exempt
@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_request_notes_submit(request):
    try:
        data = request.POST.get('form_data', '')
        data = json.loads(data)
        data['username'] = request.user.username
        data['user_id'] = request.user.id
        url = settings.PURCHASE_BASE_URL + '/api/create_request_notes/'
        api_response = requests.post(url, data=json.dumps(data), headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'创建成功')

        return json_response(code=-1, msg=u'创建失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_plan_list(request):
    try:
        form_data = {}
        filter = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        currentPage = int(page)
        url = settings.PURCHASE_BASE_URL + '/api/plan_list/'
        api_response = requests.get(url, params={"filter": filter}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        data_list = data_json['data']['data']
        form_data['total'] = len(data_json['data']['data'])
        paginator = Paginator(data_list, 20)
        try:
            data_list = paginator.page(int(page))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)

        return render(request, 'purchase_plan_list.html',{
            "data_list": data_list,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_plan_list/',
        })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_plan_change_status(request):
    try:
        doc_number = request.GET.get("doc_number", "")
        url = settings.PURCHASE_BASE_URL + '/api/plan_change_status/'
        api_response = requests.get(url, params={"doc_number": doc_number}, headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'保存成功')

        return json_response(code=-1, msg=u'保存失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_plan_new(request):
    try:
        form_data = {}
        filter = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        currentPage = int(page)
        url = settings.PURCHASE_BASE_URL + '/api/request_notes_list/'
        api_response = requests.get(url, params={"flag":"plan", "filter": filter}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        data_list = data_json['data']['data']
        form_data['total'] = len(data_json['data']['data'])
        paginator = Paginator(data_list, 20)
        try:
            data_list = paginator.page(int(page))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)
        return render(request, 'purchase_plan_new.html', {
            "data_list": data_list,
            "vendor_list": data_json['data']['vendor_list'],
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_request_notes_new/',
        })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)


@csrf_exempt
@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_plan_submit(request):
    try:
        data = request.POST.get('form_data', '')
        data = json.loads(data)
        data['username'] = request.user.username
        data['user_id'] = request.user.id
        url = settings.PURCHASE_BASE_URL + '/api/create_plan/'
        api_response = requests.post(url, data=json.dumps(data), headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'创建成功')

        return json_response(code=-1, msg=u'创建失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_plan_del(request):
    try:
        doc_number = request.GET.get("doc_number", "")
        flag = request.GET.get("flag", "")
        sku = request.GET.get("sku", "")
        url = settings.PURCHASE_BASE_URL + '/api/plan_del/'
        api_response = requests.get(url, params={"doc_number": doc_number, "flag": flag,"sku": sku}, headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'删除成功')

        return json_response(code=-1, msg=u'删除失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_plan_save(request):
    try:
        doc_number = request.GET.get("doc_number", "")
        quantity = request.GET.get("quantity", "")
        price = request.GET.get("price", "")
        subtotal = request.GET.get("subtotal", "")
        sku = request.GET.get("sku", "")
        url = settings.PURCHASE_BASE_URL + '/api/plan_item_save/'
        api_response = requests.get(url, params={"doc_number": doc_number, "quantity": quantity, "sku": sku, "price": price, "subtotal": subtotal}, headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'保存成功')

        return json_response(code=-1, msg=u'保存失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_order_list(request):
    try:
        form_data = {}
        filter = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        currentPage = int(page)
        url = settings.PURCHASE_BASE_URL + '/api/order_list/'
        api_response = requests.get(url, params={"filter":filter}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        data_list = data_json['data']['data']
        form_data['total'] = len(data_list)
        paginator = Paginator(data_list, 20)
        try:
            data_list = paginator.page(int(page))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)
        return render(request, 'purchase_order_list.html',{
            "data_list": data_list,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_order_list/',
        })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_order_new(request):
    try:
        form_data = {}
        filter = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        currentPage = int(page)
        url = settings.PURCHASE_BASE_URL + '/api/plan_list/'
        api_response = requests.get(url, params={"flag":"order", "filter":filter}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        data_list = data_json['data']['data']
        form_data['total'] = len(data_list)
        paginator = Paginator(data_list, 20)
        try:
            data_list = paginator.page(currentPage)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)
        return render(request, 'purchase_order_new.html', {
            "data_list": data_list,
            "vendor_list": data_json['data']['vendor_list'],
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_order_new/',
        })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)


@csrf_exempt
@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_order_submit(request):
    try:
        data = request.POST.get('form_data', '')
        data = json.loads(data)
        data['username'] = request.user.username
        data['user_id'] = request.user.id
        url = settings.PURCHASE_BASE_URL + '/api/create_order/'
        api_response = requests.post(url, data=json.dumps(data), headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'创建成功')

        return json_response(code=-1, msg=u'创建失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_order_view_edit(request):
    try:
        # form_data = {}
        # frame = request.GET.get('frame', '')
        # page = request.GET.get('page', 1)
        # pageSize = request.GET.get('pageSize', 20)
        # currentPage = int(page)
        # request_data_list = []
        # data_dict = {}
        doc_number = request.GET.get('doc_number', '')
        if doc_number == '':
            return json_response(code=-1, msg=u'采购订单号为空')
        url = settings.PURCHASE_BASE_URL + '/api/order_list/'
        api_response = requests.get(url, params={'doc_number':doc_number}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        print(data_json)
        print(2222222222222222222222222222222222222)
        data_list = data_json['data']['data']
        print(data_list)
        print(111111111111111111)
        # sql = """SELECT sku,name,quantity,status FROM wms_inventory_struct"""
        # lab_sql = """SELECT frame, frame_type, COUNT(1) AS sales_qty from oms_laborder WHERE year(create_at)=%s AND month(create_at)=%s GROUP BY frame""" %(datetime.datetime.now().year, (datetime.datetime.now().month-1))
        #
        # if frame != '':
        #     sql = sql + """ WHERE sku='%s'""" % frame
        # sql = sql + """ ORDER BY quantity"""
        #
        # with connections['pg_oms_query'].cursor() as cursor:
        #     cursor.execute(sql)
        #     for item in namedtuplefetchall(cursor):
        #         data_dict[item.sku] = {
        #             'frame': item.sku,
        #             'name': item.name,
        #             'quantity': item.quantity,
        #             'status': item.status,
        #             'frame_type': '',
        #             'sales_qty': 0
        #         }
        #     cursor.execute(lab_sql)
        #     for item in namedtuplefetchall(cursor):
        #         if item.frame in data_dict.keys():
        #             data_dict[item.frame]['frame_type'] = item.frame_type
        #             data_dict[item.frame]['sales_qty'] = item.sales_qty
        #
        # for value in data_dict.values():
        #     request_data_list.append(value)
        #
        # form_data['total'] = len(request_data_list)
        # paginator = Paginator(request_data_list, 20)
        # try:
        #     request_data_list = paginator.page(int(page))
        # except PageNotAnInteger:
        #     # If page is not an integer, deliver first page.
        #     request_data_list = paginator.page(1)
        # except EmptyPage:
        #     # If page is out of range (e.g. 9999), deliver last page of results.
        #     request_data_list = paginator.page(paginator.num_pages)

        return render(request, 'purchase_order_view_edit.html',{
            "data_list": data_list,
            # 'currentPage': currentPage,
            'doc_number': doc_number,
            # 'frame': frame,
            # 'paginator': paginator,
            'requestUrl': '/purchase/purchase_order_view_edit/',
        })
    except Exception as e:
        return HttpResponse('系统遇到异常,已屏蔽所有操作! %s' % e.message)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_order_change_status(request):
    try:
        doc_number = request.GET.get('doc_number', '')
        status = request.GET.get('status', '')
        comments = request.GET.get('comments', '')
        url = settings.PURCHASE_BASE_URL + '/api/order_change_status/'
        api_response = requests.get(url, params={'doc_number': doc_number,'status': status, 'comments':comments},
                                    headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=response['message'])

        return json_response(code=-1, msg=response['message'])
    except Exception as e:
        print(e)
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_orderitem_del(request):
    try:
        doc_number = request.GET.get('doc_number', '')
        sku = request.GET.get('sku', '')
        total_quantity = request.GET.get('total_quantity', '')
        opening_quantity = request.GET.get('opening_quantity', '')
        grand_total = request.GET.get('grand_total', '')
        if doc_number == '':
            return json_response(code=-1, msg=u'采购订单号为空')
        api_response = requests.get('http://127.0.0.1:8002/api/orderitem_del/', params={'doc_number':doc_number, 'sku': sku, 'total_quantity':total_quantity, 'opening_quantity':opening_quantity, 'grand_total':grand_total}, headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'操作成功')
    except Exception as e:
        return json_response(code=0, msg=e)


@csrf_exempt
@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_order_update(request):
    try:
        data = request.POST.get('form_data', '')
        data = json.loads(data)
        data['username'] = request.user.username
        data['user_id'] = request.user.id
        url = settings.PURCHASE_BASE_URL + '/api/update_order/'
        api_response = requests.post(url, data=json.dumps(data), headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'更新成功')

        return json_response(code=-1, msg=u'更新失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@csrf_exempt
@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_order_complete(request):
    try:
        data = request.POST.get('form_data', '')
        data = json.loads(data)
        data['username'] = request.user.username
        data['user_id'] = request.user.id
        url = settings.PURCHASE_BASE_URL + '/api/complete_order/'
        api_response = requests.post(url, data=json.dumps(data), headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'执行成功')

        return json_response(code=-1, msg=u'执行失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_receipt_order_list(request):
    try:
        form_data = {}
        filter = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        currentPage = int(page)
        url = settings.PURCHASE_BASE_URL + '/api/receipt_order_list/'
        api_response = requests.get(url, params={'filter':filter}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        data_list = data_json['data']['data']
        form_data['total'] = len(data_list)
        paginator = Paginator(data_list, 20)
        try:
            data_list = paginator.page(int(page))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)
        return render(request, 'purchase_receipt_order_list.html',{
            "data_list": data_list,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_receipt_order_list/',
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_receipt_order_new(request):
    try:
        form_data = {}
        filter = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        currentPage = int(page)
        url = settings.PURCHASE_BASE_URL + '/api/order_list/'
        api_response = requests.get(url, params={'filter':filter, 'flag':'receipt'}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        data_list = data_json['data']['data']
        form_data['total'] = len(data_list)
        paginator = Paginator(data_list, 20)
        try:
            data_list = paginator.page(int(page))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)
        return render(request, 'purchase_receipt_order_new.html',{
            "data_list": data_list,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_receipt_order_new/',
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_receipt_order_view_edit(request):
    try:
        doc_number = request.GET.get('doc_number', '')
        if doc_number == '':
            return json_response(code=-1, msg=u'采购订单号为空')
        url = settings.PURCHASE_BASE_URL + '/api/receipt_order_view_edit/'
        api_response = requests.get(url, params={'doc_number':doc_number}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        return render(request, 'purchase_receipt_order_view_edit.html',{
            "data_list": data_json['data']['order_data'],
            "receipt_data": data_json['data']['receipt_order_data']
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_add_order(request):
    try:
        doc_number = request.GET.get('doc_number', '')
        if doc_number == '':
            return json_response(code=-1, msg=u'采购订单号为空')
        url = settings.PURCHASE_BASE_URL + '/api/order_list/'
        api_response = requests.get(url, params={'doc_number':doc_number}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        return json_response(code=0, msg=u'执行成功', data=data_json['data']['data'])
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_return_order_list(request):
    try:
        form_data = {}
        filter = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        currentPage = int(page)
        url = settings.PURCHASE_BASE_URL + '/api/return_order_list/'
        api_response = requests.get(url, params={'filter':filter, 'flag':''}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        data_list = data_json['data']['data']
        form_data['total'] = len(data_list)
        paginator = Paginator(data_list, 20)
        try:
            data_list = paginator.page(int(page))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)
        return render(request, 'purchase_return_order_list.html',{
            "data_list": data_list,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_return_order_list/',
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_return_order_new(request):
    try:
        form_data = {}
        filter = request.GET.get('filter', '')
        page = request.GET.get('page', 1)
        currentPage = int(page)
        url = settings.PURCHASE_BASE_URL + '/api/order_list/'
        api_response = requests.get(url, params={'filter':filter, 'flag':'complete'}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        data_list = data_json['data']['data']
        form_data['total'] = len(data_list)
        paginator = Paginator(data_list, 20)
        try:
            data_list = paginator.page(currentPage)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            data_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            data_list = paginator.page(paginator.num_pages)
        return render(request, 'purchase_return_order_new.html',{
            "data_list": data_list,
            'currentPage': currentPage,
            'paginator': paginator,
            'requestUrl': '/purchase/purchase_return_order_new/',
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_return_order_submit(request):
    try:
        data = request.POST.get('form_data', '')
        data = json.loads(data)
        data['username'] = request.user.username
        data['user_id'] = request.user.id
        url = settings.PURCHASE_BASE_URL + '/api/create_return_order/'
        api_response = requests.post(url, data=json.dumps(data), headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'创建成功')

        return json_response(code=-1, msg=u'创建失败')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_return_order_view_edit(request):
    try:
        doc_number = request.GET.get('doc_number', '')
        if doc_number == '':
            return json_response(code=-1, msg=u'采购订单号为空')
        url = settings.PURCHASE_BASE_URL + '/api/return_order_view_edit/'
        api_response = requests.get(url, params={'doc_number': doc_number}, headers={'content-type': 'application/json'})
        data_json = json.loads(api_response.text)
        return render(request, 'purchase_return_order_view_edit.html',{
            "data_list": data_json['data']['order_data'],
            "return_order_data": data_json['data']['return_order_data'],
            "receipt_order_data": data_json['data']['receipt_order_data']
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('purchase.SLOD_VIEW', login_url='/oms/forbid/')
def redirect_purchase_return_order_change_status(request):
    try:
        doc_number = request.GET.get('doc_number', '')
        url = settings.PURCHASE_BASE_URL + '/api/return_order_change_status/'
        api_response = requests.get(url, params={'doc_number':doc_number}, headers={'content-type': 'application/json'})
        response = json.loads(api_response.text)
        if response['code'] == 200:
            return json_response(code=0, msg=u'执行成功')
        return json_response(code=-1, msg=u'执行失败')
    except Exception as e:
        return json_response(code=-1, msg=e)
