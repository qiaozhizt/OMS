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

from django.contrib.auth import get_user_model

User = get_user_model()

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, Permission

from django.db import connections
from django.db import transaction
from collections import namedtuple
from django.db.models import Q

import oms.const
from oms.models.utilities_models import utilities, DateEncoder
from .models import *
from util.db_helper import *

from oms.models.order_models import LabOrder, PgOrder, PgOrderItem

from oms.const import *

from util.time_delta import *
from util.response import *
from .models import reponse_order_detail, combined_list, combined_list_controller

from api.controllers.tracking_controllers import tracking_lab_order_controller
from oms.views import add_tracklog, add_order_tracking_report, addOrderTrackingReportCs
from oms.models.ordertracking_models import OrderTracking
from wms.models import inventory_struct_warehouse_controller, product_frame, locker_controller, LockersItem
from accsorder.models import AccsOrder
from pg_oms import settings


def index(request):
    _form_data = {}
    return render(request, "exceptions.html",
                  {
                      'form_data': _form_data,
                  })


@login_required
@permission_required('oms.OA_VIEW', login_url='/oms/forbid/')
def redirect_address(request):
    _form_data = {}
    _form_data['request_feature'] = 'Address'

    order_number = request.GET.get('order_number', '')

    page = request.GET.get('page', 1)
    currentPage = int(page)
    filter = request.GET.get('filter', 'express')
    region = request.GET.get('region', 'all')

    _form_data['filter'] = filter
    _filter = {}

    items = []
    paginator = None

    STATUS_CHOICES = (
        ('', '新订单'),
        ('PRINT_DATE', '打印'),
        ('REQUEST_NOTES', '出库申请'),
        ('FRAME_OUTBOUND', '镜架出库'),
        # ('TINT', '染色'),
        # ('RX_LAB', '车房'),
        # ('ADD_HARDENED', '加硬'),
        # ('COATING', '加膜'),

        ('LENS_RECEIVE', '镜片收货'),
        ('INITIAL_INSPECTION', '初检'),
        # ('ASSEMBLING', '装配'),

        # ('SHAPING', '整形'),
        ('FINAL_INSPECTION', '终检'),
        # ('PURGING', '清洗'),

        ('ORDER_MATCH', '订单配对'),
        # ('PACKAGE', '包装'),
        ('SHIPPING', '发货'),
        ('COMPLETE', '完成'),
        ('ONHOLD', '暂停'),
        ('CANCELLED', '取消'),
        ('REDO', '重做'),
    )

    status_choices_list = []

    states_list = PgOrder.states_list

    try:
        # filter["status"] = 'PRINT_DATE'

        items = PgOrder.objects.filter(create_at__gte=time_delta()).order_by('-id')

        if filter == 'all':
            pass
        elif filter == 'express' or filter == 'standard' or filter == 'flatrate' or filter == 'employee':
            _filter['ship_direction'] = filter
            items = items.filter(**_filter)

        if region == 'east':
            items = items.filter(**_filter).exclude(region__in=states_list)
        elif region == 'west':
            _filter['region__in'] = states_list
            items = items.filter(**_filter)

        if filter == 'issue_addr':
            items = PgOrder.objects.filter(create_at__gte=time_delta()).filter(is_issue_addr=True) \
                .exclude(status='canceled')

        if filter == 'issue_addr_processing':
            items = PgOrder.objects.filter(create_at__gte=time_delta()).filter(is_issue_addr=True) \
                .exclude(status='canceled') \
                .exclude(status='complete') \
                .exclude(status='closed') \
                .exclude(status='shipped') \
                .exclude(web_status='complete') \
                .exclude(web_status='closed') \
                .exclude(web_status='shipped')

        if not order_number == '':
            _form_data['search_entity'] = order_number
            items = PgOrder.objects.filter(order_number=order_number).order_by('-id')

        count = items.count()
        if count > 0:
            _form_data['total'] = count

        paginator = Paginator(items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)

        return render(request, "address.html",
                      {
                          'form_data': _form_data,
                          'list': items,
                          'currentPage': currentPage, 'paginator': paginator,
                          'requestUrl': reverse('shipment_address'),
                          'filter': filter,
                          'region': region,
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                      })


@login_required
@permission_required('oms.OA_VIEW', login_url='/oms/forbid/')
def redirect_address_generate_csv(request):
    page_info = {}
    form_data = None
    page = request.GET.get('page', 1)
    currentPage = int(page)
    laborder_filter = request.GET.get('filter', 'all')

    id = request.GET.get('id', '')
    try:
        id = int(id)
    except:
        return HttpResponse('系统获取参数ID遇到错误')

    lines = request.GET.get('lines', 30)

    items = []
    paginator = None

    try:
        filter = {}

        lbos = []

        # Print Start

        for lbo in lbos:
            items.append(lbo.lab_number)

        logging.debug('items count: %s' % len(items))

        response = HttpResponse(content_type='text')
        file_name = 'laborder_numbers_barcode'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.txt'

        count = len(items)
        index = 0

        for item in items:
            index += 1
            if index < count:
                response.write(item + '\n')
            else:
                response.write(item)
        return response

    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        return HttpResponse('生成条码标签清单遇到异常[ %s ], 请暂时手动生成，并联系系统支持....' % e.message)


@login_required
@permission_required('oms.OA_VERIFY', login_url='/oms/forbid/')
def redirect_address_verify(request):
    _form_data = {}
    _form_data['request_feature'] = 'Address'

    order_number = request.GET.get('order_number', '')

    page = request.GET.get('page', 1)
    currentPage = int(page)
    filter = request.GET.get('filter', 'all')
    region = request.GET.get('region', 'all')

    _form_data['filter'] = filter
    _filter = {}

    items = []
    paginator = None

    STATUS_CHOICES = (
        ('', '新订单'),
        ('PRINT_DATE', '打印'),
        ('REQUEST_NOTES', '出库申请'),
        ('FRAME_OUTBOUND', '镜架出库'),
        # ('TINT', '染色'),
        # ('RX_LAB', '车房'),
        # ('ADD_HARDENED', '加硬'),
        # ('COATING', '加膜'),

        ('LENS_RECEIVE', '镜片收货'),
        ('INITIAL_INSPECTION', '初检'),
        # ('ASSEMBLING', '装配'),

        # ('SHAPING', '整形'),
        ('FINAL_INSPECTION', '终检'),
        # ('PURGING', '清洗'),

        ('ORDER_MATCH', '订单配对'),
        # ('PACKAGE', '包装'),
        ('SHIPPING', '发货'),
        ('COMPLETE', '完成'),
        ('ONHOLD', '暂停'),
        ('CANCELLED', '取消'),
        ('REDO', '重做'),
    )

    status_choices_list = []

    states_list = PgOrder.states_list

    try:
        # filter["status"] = 'PRINT_DATE'

        items = PgOrder.objects.filter(create_at__gte=time_delta()).order_by('-id')

        if filter == 'all':
            pass
        elif filter == 'express' or filter == 'standard' or filter == 'flatrate' or filter == 'employee':
            _filter['ship_direction'] = filter
            items = items.filter(**_filter)

        if region == 'east':
            items = items.filter(**_filter).exclude(region__in=states_list)
        elif region == 'west':
            _filter['region__in'] = states_list
            items = items.filter(**_filter)

        if filter == 'issue_addr':
            items = PgOrder.objects.filter(create_at__gte=time_delta()).filter(is_issue_addr=True) \
                .exclude(status='canceled')

        if filter == 'issue_addr_processing':
            from django.db.models import Q
            items = PgOrder.objects.filter(create_at__gte=time_delta()).filter(is_issue_addr=True) \
                .exclude(status='canceled') \
                .exclude(status='complete') \
                .exclude(status='closed') \
                .exclude(status='shipped') \
                .exclude(web_status='complete') \
                .exclude(web_status='closed') \
                .exclude(web_status='shipped') \
                .exclude(is_verified_addr=True)
            items_list = PgOrder.objects.filter(Q(street__icontains='box')|Q(street2__icontains='box'),create_at__gte=time_delta(), ship_direction__in=['EXPRESS','CA_EXPRESS'])\
                .exclude(status='canceled') \
                .exclude(status='complete') \
                .exclude(status='closed') \
                .exclude(status='shipped') \
                .exclude(web_status='complete') \
                .exclude(web_status='closed') \
                .exclude(web_status='shipped')\
                .exclude(is_verified_addr=True)
            items = items.union(items_list)
        if not order_number == '':
            _form_data['search_entity'] = order_number
            items = PgOrder.objects.filter(order_number=order_number).order_by('-id')

        logging.debug(items.query)

        count = items.count()
        if count > 0:
            _form_data['total'] = count
        # 获取URL中除page外的其它参数
        import re
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string
        paginator = Paginator(items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)

        return render(request, "address_verify.html",
                      {
                          'form_data': _form_data,
                          'list': items,
                          'currentPage': currentPage,
                          'paginator': paginator,
                          'requestUrl': reverse('shipment_address_verify'),
                          'filter': filter,
                          'region': region,
                          'query_string': query_string
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                      })


'''
 预发货单
 预发货单有独立权限，适用于发货操作人员
 处理逻辑：
 1.不同的用户可以创建一个预发货单
 2.直接打开预发货单，如果当前用户没有 New 状态的预发货单，系统会自动创建
'''


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_pre_delivery(request):
    rm = response_message()
    _form_data = {}
    if request.method == 'POST':
        _id = request.POST.get('order_entity', '-1')
        _pd_entity = request.POST.get('pd_entity', '-1')
        if not _id == '-1':

            _order_detail = reponse_order_detail()

            if _id[0].upper() == 'A' or 'AO' in _id:
                if 'AO' in _id:
                    od = _order_detail.get_by_lab_number(_id, flag='A')
                else:
                    id = _id.upper().lstrip('A')
                    logging.debug('id: %s' % id)
                    od = _order_detail.get_by_lab_order_entity(id, flag='A')
            else:
                if _id[0].upper() == settings.BAR_CODE_PREFIX:
                    id = _id.upper().lstrip(settings.BAR_CODE_PREFIX)
                    logging.debug('id: %s' % id)
                    od = _order_detail.get_by_lab_order_entity(id)
                else:
                    od = _order_detail.get_by_lab_number(_id)

            pf_obj = product_frame.objects.get(sku=od.current_lab_order_entity.frame)
            if pf_obj.frame_type == 'FWC':
                _form_data['lab_number'] = _id
                return json_response(code=-1, msg="此单是套镜，请检查夹片是否配齐！", data=_form_data)
            return json_response(code=0, msg="Success")
    else:
        paginator = None
        page = request.GET.get('page', 1)
        ship_region = request.GET.get('ship_region', 'all')

        currentPage = int(page)
        _id = -1
        od = None
        _delivery = None
        lab_number = ''
        _form_data['total'] = 0
        items = []
        rx_flag = 'B'
        try:
            _id = request.GET.get('order_entity', '-1')
            _pd_entity = request.GET.get('pd_entity', '-1')
            logging.debug('-id: %s' % _id)
            logging.debug('_pd_entity: %s' % _pd_entity)

            if not _id == '-1':

                _order_detail = reponse_order_detail()

                if _id[0].upper() == 'A' or 'AO' in _id:
                    rx_flag = 'A'
                    if 'AO' in _id:
                        od = _order_detail.get_by_lab_number(_id, flag='A')
                    else:
                        id = _id.upper().lstrip('A')
                        logging.debug('id: %s' % id)
                        od = _order_detail.get_by_lab_order_entity(id, flag='A')
                else:
                    if _id[0].upper() == settings.BAR_CODE_PREFIX:
                        id = _id.upper().lstrip(settings.BAR_CODE_PREFIX)
                        logging.debug('id: %s' % id)
                        od = _order_detail.get_by_lab_order_entity(id)
                    else:
                        od = _order_detail.get_by_lab_number(_id)

                _form_data['obj'] = od

                pdc = pre_delivery_controller()
                rm = pdc.add(request, od, rx_flag)
                # _delivery = rm.obj
                if rm.code == 0 or rm.code == 1:
                    _delivery = rm.obj
                    items = rm.obj.lines_sorted
                    _form_data['pd_entity'] = rm.obj.id

                # 2019.11.14 再次扫描到拣配单的时候，自动清除仓位；
                if _id <> '':
                    objs = []
                    loc = lab_order_controller()
                    objs = loc.get_by_entity(_id)
                    if len(objs) > 0:
                        lab_number = objs[0].lab_number
                    elif len(objs) == 0:
                        lab_number = _id
                    if lab_number <> '':
                        lc = locker_controller()
                        logging.debug(lab_number)
                        lockersItem = LockersItem.objects.filter(lab_number=lab_number)
                        logging.debug(lockersItem.query)
                        if len(lockersItem) > 0:
                            lc.deleteItem(lab_number)

            elif not _pd_entity == '-1':
                pd = pre_delivery.objects.get(id=_pd_entity)
                _form_data['pd_entity'] = _pd_entity
                _delivery = pd
                items = pd.lines_sorted

            if len(items) > 0 and not ship_region == 'all':
                items = items.filter(ship_region=ship_region)

        except Exception as e:
            rm.code = -1
            rm.message = e.message
        _form_data['total'] = len(items)

        if len(items) > 0 and not ship_region == 'all':
            paginator = Paginator(items, len(items))
        else:
            paginator = Paginator(items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

        try:
            items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            items = paginator.page(paginator.num_pages)
        try:
            return render(request, "pre_delivery.html",
                          {
                              'form_data': _form_data,
                              'list': items,
                              'delivery': _delivery,
                              'response_message': rm,
                              'obj': od,
                              'currentPage': currentPage, 'paginator': paginator,
                              'order_entity': _id,
                              'requestUrl': reverse('pre_delivery')
                          })
        except Exception as e:
            logging.debug('Exception: %s' % e.message)
            _form_data['exceptions'] = e
            _form_data['error_message'] = e.message
            return render(request, "exceptions.html",
                          {
                              'form_data': _form_data,
                          })


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_pre_delivery_update_status(request):
    rm = response_message()
    _form_data = {}
    entity = request.POST.get('entity', 0)
    status = request.POST.get('status', '')
    region = request.POST.get('region', '')
    return action_delivery_update_status(entity, status, region)


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_pre_delivery_update_status_final_inspection(request):
    rm = response_message()
    _form_data = {}
    entity = request.POST.get('entity', 0)
    return action_delivery_update_status(entity, 'FINAL_INSPECTION')


@csrf_exempt
def action_delivery_update_status(entity, status, region=''):
    entity = entity
    try:
        pd = pre_delivery.objects.get(id=entity)
        if region == '':
            lines = pd.lines
        else:
            lines = pd.lines.filter(ship_region=region)
        for line in lines:
            lbo = line.lab_order_entity
            lbo.status = status
            lbo.save()
        return HttpResponse('0')
    except Exception as e:
        logging.debug(e.message)
        return HttpResponse(e.message)


'''
 预发货单
 暂缓发货
 初期时暂缓发货，将订单暂时更新为终检合格；
 在发货功能完全实现之后，将调整为订单配对
'''


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_pre_delivery_update_status_final_inspection_line(request):
    rm = response_message()
    _form_data = {}
    res = {}
    entity = request.POST.get('entity', 0)
    line_id = request.POST.get('line_id', 0)
    location = ''
    try:
        pd = pre_delivery.objects.get(id=entity)

        pdl = pre_delivery_line.objects.get(id=line_id)

        if pdl.ship_region == 'E':
            e_count = pd.e_count - 1
            if e_count < 0:
                e_count = 0
            pd.e_count = e_count
        elif pdl.ship_region == 'W':
            w_count = pd.w_count - 1
            if w_count < 0:
                w_count = 0
            pd.w_count = w_count
        elif pdl.ship_region == 'Express':
            express_count = pd.express_count - 1
            if express_count < 0:
                express_count = 0
            pd.express_count = express_count
        else:
            other_count = pd.other_count - 1
            if other_count < 0:
                other_count = 0
            pd.other_count = other_count

        pd.save()

        pdl.delete()

        lbo = pdl.lab_order_entity
        lbo.status = 'ORDER_MATCH'
        lbo.save()

        # 2019.11.14 暂缓发货进行仓位号分配
        # 加急单
        if lbo.act_ship_direction == 'EXPRESS' or lbo.act_ship_direction == 'CA_EXPRESS':
            location = 'OM-EPS'
        else:
            location = 'OM'
        locker = locker_controller()
        max_glass = locker.get_locker_config(location)
        locker_obj = locker.locker_add(location, max_glass, request.user.username, lbo)
        print(type(locker_obj.code))
        if locker_obj.code == 0:
            locker_obj_num = locker_obj.obj.storage_location + "-" + locker_obj.obj.locker_num
        elif locker_obj.code == -1:
            locker_obj_num = locker_obj.obj.storage_location + "-" + locker_obj.obj.locker_num
            res['code'] = -1
            res['message'] = str(locker_obj_num) + "仓位中存在该订单，请人工确认"
            return HttpResponse(json.dumps(res))
        elif locker_obj.code == -2:
            res['code'] = -2
            res['message'] = "仓位未设置专属VD号"
            return HttpResponse(json.dumps(res))

        tloc = tracking_lab_order_controller()
        tloc.tracking(lbo, request.user, 'ORDER_MATCH')

        res['code'] = 0
        res['message'] = str(locker_obj_num)
        return HttpResponse(json.dumps(res))

    except Exception as e:
        logging.debug(e.message)
        res['code'] = -3
        res['message'] = e.message
        return HttpResponse(json.dumps(res))


'''
 关闭预发货单
 只有关闭预发货单之后，才能启用新的发货单

'''


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_pre_delivery_shipped(request):
    rm = response_message()
    _form_data = {}
    try:
        entity = request.POST.get('entity', 0)
        pd = pre_delivery.objects.get(id=entity)

        if pd.status == '' or pd.status == None:
            pd.status = 'SHIPPED'
            pd.save()
        else:
            msg = '该预发货单已经完成'
            return HttpResponse(msg)
        return HttpResponse('0')
    except Exception as e:
        rm.capture_execption(e)

    return HttpResponse(rm.message)


'''
 发货单
 发货历史清单 区分东部/西部/加急/内部等
'''


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_delivery(request):
    rm = response_message()
    _form_data = {}
    paginator = None
    page = request.GET.get('page', 1)

    currentPage = int(page)

    _form_data['total'] = 0
    items = []
    try:
        items = pre_delivery.objects.filter(is_enabled=True).order_by('-id')

    except Exception as e:
        rm.code = -1
        rm.message = e.message

    _form_data['total'] = items.count()

    paginator = Paginator(items, oms.const.PAGE_SIZE)  # Show 20 contacts per page
    # 获取URL中除page外的其它参数\
    import re
    query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
    if query_string:
        query_string = '&' + query_string
    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)

    try:
        return render(request, "delivery.html",
                      {
                          'form_data': _form_data,
                          'list': items,
                          'response_message': rm,
                          'currentPage': currentPage,
                          'paginator': paginator,
                          'requestUrl': reverse('delivery'),
                          'query_string': query_string
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                      })


'''
 发货单详情
'''


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_delivery_detail(request):
    rm = response_message()
    _form_data = {}
    paginator = None
    page = request.GET.get('page', 1)
    ship_region = request.GET.get('ship_region', 'all')
    currentPage = int(page)
    _id = -1
    od = None
    _delivery = None

    _form_data['total'] = 0
    items = []
    try:
        _id = request.GET.get('order_entity', '-1')
        _pd_entity = request.GET.get('pd_entity', '-1')

        logging.debug('-id: %s' % _id)
        logging.debug('_pd_entity: %s' % _pd_entity)

        if not _id == '-1':

            _order_detail = reponse_order_detail()

            if _id[0].upper() == settings.BAR_CODE_PREFIX:
                id = _id.upper().lstrip(settings.BAR_CODE_PREFIX)
                logging.debug('id: %s' % id)
                od = _order_detail.get_by_lab_order_entity(id)
            else:
                od = _order_detail.get_by_lab_number(_id)

            _form_data['obj'] = od

        elif not _pd_entity == '-1':
            pd = pre_delivery.objects.get(id=_pd_entity)
            _form_data['pd_entity'] = _pd_entity
            _form_data['pd'] = pd
            _delivery = pd
            items = pd.lines_sorted
        if len(items) > 0 and not ship_region == 'all':
            items = items.filter(ship_region=ship_region)
    except Exception as e:
        rm.code = -1
        rm.message = e.message

    _form_data['total'] = len(items)

    if len(items) > 0 and not ship_region == 'all':
        paginator = Paginator(items, len(items))
    else:
        paginator = Paginator(items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)

    try:
        return render(request, "delivery_detail.html",
                      {
                          'form_data': _form_data,
                          'list': items,
                          'delivery': _delivery,
                          'response_message': rm,
                          'obj': od,
                          'currentPage': currentPage, 'paginator': paginator,
                          'order_entity': _id,
                          'requestUrl': reverse('delivery_detail'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                      })


'''
导出地址清单
'''


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_pre_delivery_print_addr(request):
    id = request.GET.get('entity', '')
    try:
        id = int(id)
    except:
        return HttpResponse('系统获取参数ID遇到错误')
    items = []
    try:
        pd = pre_delivery.objects.get(id=id)
        items = pd.lines
        import csv, codecs
        response = HttpResponse(content_type='text/csv')
        file_name = 'express_addr'
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)
        writer = csv.writer(response)
        writer.writerow(['Address List'])
        writer.writerow([
            'Increment ID', 'First Name', 'Last Name', 'Post Code', 'Street', 'City', 'Region', 'Country ID',
            'Telephone'
        ])

        order_numbers = []

        for item in items:
            order_number = item.lab_order_entity.order_number
            if not order_number in order_numbers:
                order_numbers.append(order_number)

        with connections['pg_mg_query'].cursor() as cursor:
            sql = '''
                select t0.increment_id,
                t3.firstname,
                t3.lastname,
                t3.postcode,
                t3.street,
                t3.city,
                t3.region,
                t3.country_id,
                t3.telephone
                from sales_order_grid t0 left join sales_order_address t3
                on t0.entity_id=t3.parent_id and t3.address_type='shipping'
                where t0.increment_id in %s
            '''
            logging.info(sql)
            cursor.execute(sql, [order_numbers])
            results = namedtuplefetchall(cursor)

            logging.debug(order_numbers)

            logging.debug(results)

            for i in range(len(results)):
                writer.writerow(
                    [
                        results[i].increment_id, results[i].firstname,
                        results[i].lastname, results[i].postcode,
                        results[i].street, results[i].city,
                        results[i].region, results[i].country_id,
                        results[i].telephone
                    ]
                )

        return response

    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        return HttpResponse('生成订单地址时遇到异常[ %s ], 请暂时手动生成，并联系系统支持....' % e.message)


'''
 转加急或普通
'''


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_pre_delivery_convert(request):
    rm = response_message()
    try:
        pdc = pre_delivery_controller()
        rm = pdc.convert(request)

        if rm.code == 0:
            return HttpResponse('0')
        else:
            return HttpResponse(rm.message)

    except Exception as e:
        logging.debug(e.message)
        return HttpResponse(e.message)


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_collection_glasses(request):
    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Received Glasses'
    items = []
    lbo = None
    try:

        if request.method == 'POST':
            res = {}
            lab_number = request.POST.get('lab_nubmer', '')
            send_to = request.POST.get('send_to', '')
            send_from = request.POST.get('send_from', '')
            time_now = request.POST.get('time_now', '')
            if lab_number == '':
                res['code'] = -1
                res['message'] = '请先输入订单号订单!!'
                return HttpResponse(json.dumps(res))
            if send_from == '':
                res['code'] = -1
                res['message'] = '请先选择归集发出地!!'
                return HttpResponse(json.dumps(res))
            if send_to == '':
                res['code'] = -1
                res['message'] = '请先选择归集到哪里!!'
                return HttpResponse(json.dumps(res))
            try:
                logging.debug('----------------------------------------')
                cgc = collection_glasses_control()  # 归集单控制器
                # add 添加数据
                rm = cgc.add(
                    request,
                    lab_number,
                    send_to,
                    send_from,
                    time_now
                )
                res['code'] = rm.code
                res['message'] = rm.message
                logging.debug('----------------------------------------')

            except Exception as e:
                res['code'] = -999
                res['message'] = '数据遇到异常: ' + str(e)

            return HttpResponse(json.dumps(res))
        # 基于时间生成编号
        time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
        # 获取GET参数
        entity_id = request.GET.get('entity_id', '')
        send_to = request.GET.get('send_to', '')
        send_from = request.GET.get('send_from', '')

        # 根据单号查询工厂订单
        poi = {}
        if not entity_id == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity_id)

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number
            lab_number_split = lab_number.split('-')
            lab_number_split_split = lab_number_split[2].split('T')
            _form_data['one_order_num'] = lab_number_split_split[1]
            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo

            # 从上一个订单获取归集方向
            # pdl = collection_glasses.objects.filter(lab_order_entity=lbo.id)
            # if len(pdl) > 0 :
            #    send_to = pdl[0].send_to
            #    send_from = pdl[0].send_from
        # 查询当日的归集单
        invrs = collection_glasses.objects.filter(collection_number=time_now).order_by("-status", "send_from")
        _form_data['total'] = len(invrs)

        # 对invrs进行分页
        # 获取页码
        page = request.GET.get('page', 1)
        # 获取URL中除page外的其它参数
        import re
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string
        # 分页对象，设置每页20条数据
        paginator = Paginator(invrs, 10)

        try:
            contacts = paginator.page(page)
        except PageNotAnInteger:
            # 如果页码不在范围内，返回第一页
            contacts = paginator.page(1)
        except EmptyPage:
            # 如果页码超出范围，定位最后一页
            contacts = paginator.page(paginator.num_pages)
        return render(request, "collection_glasses.html", {
            'form_data': _form_data,
            'requestUrl': reverse('collection_glasses'),
            'item': lbo,
            'list': contacts,
            'paginator': paginator,
            'send_to': send_to,  # 归集去向
            'send_from': send_from,  # 归集来源
            'time_now': time_now,
            'query_string': query_string,
            'poi': poi,
        })

    except Exception as e:
        logging.debug('Exception: %s' % str(e))
        _form_data['exceptions'] = e
        _form_data['error_message'] = str(e)
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('collection_glasses'),
                      })


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_shipments_received_glasses(request):
    '''
    成镜收货单
    :param request:
    :return:
    '''

    rm = response_message()
    _form_data = {}

    _form_data['request_feature'] = 'Received Glasses'
    items = []
    cg = {}
    lbo = None
    lab_number = ''
    try:
        if request.method == 'POST':
            res = {}
            lab_number = request.POST.get('lab_nubmer', '')

            if lab_number == '':
                res['code'] = -1
                res['message'] = '请输入订单号!!'
                return HttpResponse(json.dumps(res))

            try:
                logging.debug('----------------------------------------')
                rgc = received_glasses_control()
                # add 中已做事务处理
                rm = rgc.add(
                    request,
                    lab_number
                )
                res['code'] = rm.code
                res['message'] = rm.message
                logging.debug('----------------------------------------')

            except Exception as e:
                res['code'] = -999
                res['message'] = '数据遇到异常: ' + e.message

            return HttpResponse(json.dumps(res))

        entity_id = request.GET.get('entity_id', '')
        # _form_data["search_entity"] = entity_id
        # 获取归集单中，某一单，未归集到位数量
        cg_num = ''
        cg_arrive_num = ''
        cg = []  # 归集单对象
        if not entity_id == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity_id)  # 支持条码查询

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number
            cg = collection_glasses.objects.filter(lab_number=lab_number)
            if len(cg) > 0:
                cg_collection_number = cg[0].collection_number  # 获取归集单号
                if not cg_collection_number == '':
                    cg = collection_glasses.objects.filter(collection_number=cg_collection_number).order_by("-status",
                                                                                                            "send_from")  # 获取所有单
                    cg_num = len(cg)  # 获取数量
                    cg_arrive_num = len(cg.filter(status='ARRIVE'))  # 已到位数量
        # 对CG进行分页处理
        # 获取页码
        page = request.GET.get('page', 1)
        # 获取URL中除page外的其它参数
        import re
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string
        # 分页对象，设置每页20条数据
        paginator = Paginator(cg, 10)

        try:
            contacts = paginator.page(page)
        except PageNotAnInteger:
            # 如果页码不在范围内，返回第一页
            contacts = paginator.page(1)
        except EmptyPage:
            # 如果页码超出范围，定位最后一页
            contacts = paginator.page(paginator.num_pages)
        # 获取发货方向
        ship_region = ''
        if not entity_id == '':
            loc = lab_order_controller()
            lbos = loc.get_by_entity(entity_id)

            if len(lbos) == 1:
                lbo = lbos[0]
                lab_number = lbo.lab_number

            lbo = LabOrder.objects.get(lab_number=lab_number)
            _form_data['laborder'] = lbo

            pdl = pre_delivery_line.objects.filter(lab_order_entity=lbo.id)
            if len(pdl) > 0:
                ship_region = pdl[0].ship_region
            else:
                ship_region = lbo.order_ship_region

        return render(request, "shipment_received_glasses.html", {
            'form_data': _form_data,
            'requestUrl': reverse('shipments_received_glasses'),
            'item': lbo,
            'list': contacts,  # 归集单
            'paginator': paginator,
            'query_string': query_string,
            'ship_region': ship_region,
            'cg_num': cg_num,
            'cg_arrive_num': cg_arrive_num
        })

    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                          'requestUrl': reverse('shipments_received_glasses'),
                      })


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_glasses_boxing(request):
    rm = response_message()
    _form_data = {}
    paginator = None
    page = request.GET.get('page', 1)

    currentPage = int(page)

    _form_data['total'] = 0
    items = []
    try:
        items = pre_delivery.objects.filter(is_enabled=True).filter(Q(status=None) | Q(status='')) \
            .order_by('-id')

        logging.debug(items.query)

    except Exception as e:
        logging.debug(str(e))
        rm.code = -1
        rm.message = e.message

    _form_data['total'] = len(items)

    paginator = Paginator(items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)

    try:
        return render(request, "glasses_boxing.html",
                      {
                          'form_data': _form_data,
                          'list': items,
                          'response_message': rm,
                          'currentPage': currentPage, 'paginator': paginator,
                          'requestUrl': reverse('delivery'),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                      })


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_glasses_boxing_scan(request):
    rm = response_message()
    _form_data = {}
    paginator = None
    page = request.GET.get('page', 1)

    logging.debug(request.get_full_path())

    currentPage = int(page)

    _form_data['total'] = 0
    items = []
    try:
        gbc = glasses_box_controller()
        rm = gbc.add(request)
        items = rm.obj.get('gbls', None)
        if not items:
            items = []

    except Exception as e:
        logging.debug(str(e))
        rm.code = -1
        rm.message = e.message
        rm.capture_execption(e)

    _form_data['total'] = len(items)

    paginator = Paginator(items, oms.const.PAGE_SIZE)  # Show 20 contacts per page

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        items = paginator.page(paginator.num_pages)

    try:
        return render(request, "glasses_boxing_scan.html",
                      {
                          'form_data': _form_data,
                          'list': items,
                          'response_message': rm,
                          'resp': rm,
                          'currentPage': currentPage, 'paginator': paginator,
                          'requestUrl': reverse('glasses_boxing_scan'),
                          'curUrl': request.get_full_path(),
                      })
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                      })


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_glasses_boxing_create_bag(request):
    rm = response_message()

    try:
        if request.method == 'POST':

            box_id = request.POST.get('box_id', '')
            user_id = request.user.id
            user_name = request.user.username

            paras = {}
            paras['box_id'] = box_id
            paras['user_id'] = user_id
            paras['user_name'] = user_name
            gbbc = glasses_box_bag_controller()
            rm = gbbc.create_bag(paras)

        else:
            rm.code = -5
            rm.message = 'get method is not supported'

        rm_dict = utilities.convert_to_dict(rm)
        rm_json = json.dumps(rm_dict, cls=DateEncoder)

        return HttpResponse(rm_json)

    except Exception as e:
        logging.debug(str(e))
        rm.capture_execption(e)

    rm_dict = utilities.convert_to_dict(rm)
    rm_json = json.dumps(rm_dict, cls=DateEncoder)

    return HttpResponse(rm_json)


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_pre_delivery_set_shippingmethod(request):
    rm = response_message()

    try:
        if request.method == 'POST':
            logging.debug('redirect_pre_delivery_set_shippingmethod .... ')
            pdc = pre_delivery_controller()
            rm = pdc.set_shipping_method(request)
        else:
            rm.code = -5
            rm.message = 'get method is not supported'

        rm_dict = utilities.convert_to_dict(rm)
        rm_json = json.dumps(rm_dict, cls=DateEncoder)

        return HttpResponse(rm_json)

    except Exception as e:
        logging.debug(str(e))
        rm.capture_execption(e)

    rm_dict = utilities.convert_to_dict(rm)
    rm_json = json.dumps(rm_dict, cls=DateEncoder)

    return HttpResponse(rm_json)


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_glasses_boxing_post_box(request):
    rm = response_message()

    try:
        if request.method == 'POST':
            gbbc = glasses_box_controller()
            rm = gbbc.post_box(request)

        else:
            rm.code = -5
            rm.message = 'get method is not supported'

        rm_dict = utilities.convert_to_dict(rm)
        rm_json = json.dumps(rm_dict, cls=DateEncoder)

        return HttpResponse(rm_json)

    except Exception as e:
        logging.debug(str(e))
        rm.capture_execption(e)

    rm_dict = utilities.convert_to_dict(rm)
    rm_json = json.dumps(rm_dict, cls=DateEncoder)

    return HttpResponse(rm_json)


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_calculate_combined_shipment(request):
    rm = response_message()
    try:
        clc = combined_list_controller()
        data = clc.check_combined(request)
        if data['code'] == 0:
            return json_response(code=0, msg='success', data=data['obj'])
        return json_response(code=-1, msg=e)
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_laborder_status_change(request):
    rm = response_message()
    try:
        box_id = request.POST.get("box_id", "")
        carrier = request.POST.get("carrier", "")
        status = request.POST.get("status", "")
        tracking_number = request.POST.get("tracking_number", "")
        lab_number = request.POST.get("lab_number", "")
        pg_order_number = request.POST.get("order_number", "")
        pg_order_number = pg_order_number.replace(" ", "").replace("\n", "").replace("\r", "")
        min_lab_number = lab_number.split("-")[1]
        lbos = LabOrder.objects.filter(lab_number__contains=min_lab_number).exclude(status='CANCELLED')
        nowtime = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        message = ''

        with connections['pg_oms_query'].cursor() as cursor:
            pois = PgOrderItem.objects.filter(order_number=pg_order_number)
            for laborder in lbos:
                sql = """SELECT id FROM shipment_pre_delivery_line WHERE lab_order_entity_id='%s' AND pre_delivery_entity_id='%s'""" %(laborder.id, box_id)
                cursor.execute(sql)
                pdl = namedtuplefetchall(cursor)
                if len(pdl)>0:
                    if laborder.shipping_number != '' and laborder.status == 'SHIPPING':
                        message = message +'-'+str(laborder.lab_number) + '该订单已处于已发货状态,请人工确认'
                        continue

                    laborder.final_time = nowtime
                    laborder.carriers = carrier
                    laborder.shipping_number = tracking_number
                    laborder.status = status
                    laborder.save()
                    labnumber = laborder.lab_number
                    lablist = labnumber.split("-")[:3]
                    order_number = "-".join(lablist)
                    for poi in pois:
                        if poi.lab_order_number == order_number:
                            poi.final_date = nowtime
                            poi.status = "shipped"
                            poi.save()
                            # add order_tracking log
                            add_tracklog(laborder, laborder.lab_number, laborder.frame, laborder.order_date, request.user, '发货',
                                         laborder.status)
                            # add order_tracking_report
                            add_order_tracking_report(laborder.lab_number, laborder, laborder.status, carrier, tracking_number,
                                                      "null")
                            # add order_tracking_report_cs
                            addOrderTrackingReportCs(poi.order_number, poi.shipping_method, laborder.lab_number, laborder.frame,
                                                     laborder.order_date, laborder.status, carrier, tracking_number, 'null')
                else:
                    message = message+'-'+ '该box中不存在该订单-' + str(laborder.lab_number) + ',请人工确认'
                    continue

            pg_order = PgOrder.objects.get(order_number=pg_order_number)
            pg_order.final_date = nowtime
            pg_order.status = 'shipped'
            pg_order.save()
            if message == '':
                message = 'Success'
            dict_rm = rm.response_dict(code='0', msg=message)
            return HttpResponse(json.dumps(dict_rm))
    except Exception as e:
        dict_rm = rm.response_dict(code='-1', msg=e)
        return HttpResponse(json.dumps(dict_rm))


@login_required
@permission_required('oms.ACT_SHIPMENT', login_url='/oms/forbid/')
def redirect_open_close_box(request):
    rm = response_message()
    try:
        id = request.GET.get('id', '')
        flag = request.GET.get('flag', '')
        if id == '':
            return json_response(code=-1, msg='参数错误')

        pd = pre_delivery.objects.get(id=id)
        if flag == 'open':
            pd.status = ''
        elif flag == 'close':
            pd.status = 'SHIPPED'

        pd.save()
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


class status_choice:
    key = ''
    value = ''
    permission = ''
    switch = 0

@login_required
@permission_required('oms.OLOR_VIEW', login_url='/oms/forbid/')
def redirect_shipping_orders(request):
    rm = response_message()
    _form_data = {}
    _items = []
    try:
        import re
        from shipping_orders import ShippingOrdersReport
        lab_number = request.GET.get('lab_number', '')
        overdue_days = request.GET.get('overdue_days', '2')
        if overdue_days == '':
            overdue_days = '2'
        status = request.GET.get('status', 'all')
        box_id = request.GET.get('box_id', 'all')
        ship_direction = request.GET.get('ship_direction', 'all')

        parameters = {}
        parameters['lab_number'] = lab_number
        parameters['box_id'] = box_id
        parameters['ship_direction'] = ship_direction

        sor = ShippingOrdersReport()
        rm = sor.get_list_report(request, parameters)

        _items = rm.obj.get('items')
        request.session['shipping_orders_list_sql'] = rm.obj.get('sql_script')

        page = request.GET.get('page', 1)
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        query_string_complex = request.META.get('QUERY_STRING', None)

        _form_data['total'] = len(_items)

        vendor_list = []
        for vcl in LabOrder.VENDOR_CHOICES:
            vc = status_choice()
            vc.key = vcl[0]
            vc.value = vcl[1]
            vendor_list.append(vc)
        _form_data['vendor_list'] = vendor_list

        priority_list = []
        for i in range(6):
            vc = status_choice()
            vc.key = str(i)
            vc.value = str(i)
            if i != 0:
                priority_list.append(vc)
        _form_data['priority_list'] = priority_list

        ship_direction_list = []
        for vcl in LabOrder.SHIP_DIRECTION_CHOICES:
            vc = status_choice()
            vc.key = vcl[0]
            vc.value = vcl[1]
            ship_direction_list.append(vc)
        _form_data['ship_direction_list'] = ship_direction_list

        rm_box_id_list = sor.get_box_id_list(request)
        _form_data['box_id_list'] = rm_box_id_list.obj.get('items')

        if box_id != 'all' and box_id != 'None':
            box_id = int(box_id)
        
        _form_data['box_id'] = box_id
        _form_data['ship_direction'] = ship_direction

        paginator = Paginator(_items, 20)

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)
        return render(request, 'shipping_orders.html', {
            'form_data': _form_data,
            'list': _items,
            'paginator': paginator,
            'requestUrl': reverse('shipping_orders'),
            'query_string': query_string,
            'query_string_complex': query_string_complex,
            'filter': filter,
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('oms.OLOR_VIEW', login_url='/oms/forbid/')
def redirect_shipping_orders_csv(request):
    _form_data = {}
    lbo_list = []
    try:
        import csv, codecs

        sql = request.session.get('shipping_orders_list_sql','')

        data = DbHelper.query_with_titles(sql)

        response = HttpResponse(content_type='text/csv')
        time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
        file_name = 'shipping_orders_list_csv-%s' % time_now
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)
        writer = csv.writer(response)
        writer.writerow(data['titles'])
        import pytz

        for item in data['results']:
            writer.writerow(item)

        return response
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                      })

@login_required
@csrf_exempt
def redirect_upload_excel(request):
    try:
        file_obj = request.FILES.get("file")
        file_name = settings.UPLOAD_BASE + settings.UPLOAD_CONFIG['UPLOAD_EXCEL_URL'] + 'ups_number.xlsx'
        with open(file_name, 'wb') as f_write:
            for chunk in file_obj:
                f_write.write(chunk)
        return json_response(code=0, msg='Success')
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('oms.OLOR_VIEW', login_url='/oms/forbid/')
def redirect_delivered_orders(request):
    rm = response_message()
    _form_data = {}
    _items = []
    try:
        import re
        from shipping_orders import ShippingOrdersReport
        lab_number = request.GET.get('lab_number', '')
        overdue_days = request.GET.get('overdue_days', '2')
        if overdue_days == '':
            overdue_days = '2'
        status = request.GET.get('status', 'all')
        box_id = request.GET.get('box_id', 'all')
        ship_direction = request.GET.get('ship_direction', 'all')
        time_type = request.GET.get('time_type', 'all')
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')


        parameters = {}
        parameters['lab_number'] = lab_number
        parameters['box_id'] = box_id
        parameters['ship_direction'] = ship_direction
        parameters['time_type'] = time_type
        parameters['start_date'] = start_date
        parameters['end_date'] = end_date


        sor = ShippingOrdersReport()
        rm = sor.get_list_delivered_report(request, parameters)

        _items = rm.obj.get('items')
        request.session['delivered_orders_list_sql'] = rm.obj.get('sql_script')

        page = request.GET.get('page', 1)
        query_string = re.sub(r'page=[0-9]+[&]?', '', request.META.get('QUERY_STRING', None))
        if query_string:
            query_string = '&' + query_string

        query_string_complex = request.META.get('QUERY_STRING', None)

        _form_data['total'] = len(_items)

        vendor_list = []
        for vcl in LabOrder.VENDOR_CHOICES:
            vc = status_choice()
            vc.key = vcl[0]
            vc.value = vcl[1]
            vendor_list.append(vc)
        _form_data['vendor_list'] = vendor_list

        priority_list = []
        for i in range(6):
            vc = status_choice()
            vc.key = str(i)
            vc.value = str(i)
            if i != 0:
                priority_list.append(vc)
        _form_data['priority_list'] = priority_list

        ship_direction_list = []
        for vcl in LabOrder.SHIP_DIRECTION_CHOICES:
            vc = status_choice()
            vc.key = vcl[0]
            vc.value = vcl[1]
            ship_direction_list.append(vc)
        _form_data['ship_direction_list'] = ship_direction_list

        time_type_list = []
        for vcl in LabOrder.TIME_TYPE_CHOICES:
            vc = status_choice()
            vc.key = vcl[0]
            vc.value = vcl[1]
            time_type_list.append(vc)
        _form_data['time_type_list'] = time_type_list


        rm_box_id_list = sor.get_delivered_box_id_list(request)
        _form_data['box_id_list'] = rm_box_id_list.obj.get('items')

        delivered_avg_day_list = sor.get_delivered_avg_day(request,parameters)
        _form_data['avg_day_list'] = delivered_avg_day_list.obj.get('items')

        if box_id != 'all' and box_id != 'None':
            box_id = int(box_id)

        _form_data['box_id'] = box_id
        _form_data['ship_direction'] = ship_direction
        _form_data['time_type'] = time_type


        paginator = Paginator(_items, 20)

        try:
            _items = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            _items = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            _items = paginator.page(paginator.num_pages)
        return render(request, 'delivered_orders.html', {
            'form_data': _form_data,
            'list': _items,
            'paginator': paginator,
            'requestUrl': reverse('delivered_orders'),
            'query_string': query_string,
            'query_string_complex': query_string_complex,
            'filter': filter,
        })
    except Exception as e:
        return json_response(code=-1, msg=e)


@login_required
@permission_required('oms.OLOR_VIEW', login_url='/oms/forbid/')
def redirect_delivered_orders_csv(request):
    _form_data = {}
    lbo_list = []
    try:
        import csv, codecs

        sql = request.session.get('delivered_orders_list_sql','')

        data = DbHelper.query_with_titles(sql)

        response = HttpResponse(content_type='text/csv')
        time_now = time.strftime('%Y%m%d', time.localtime(time.time()))
        file_name = 'redirect_delivered_orders_csv-%s' % time_now
        response['Content-Disposition'] = 'attachment;filename=' + file_name + '.csv'
        response.write(codecs.BOM_UTF8)
        writer = csv.writer(response)
        writer.writerow(['ID','订单号','工厂订单','发货方向','捡配单号','发货单号','跟踪号','网上订单日期','工厂订单日期','发货单日期','妥投日期','物流天数','已发货天数','生产小时数','生产天数'])

        import pytz

        for item in data['results']:
            writer.writerow(item)

        return response
    except Exception as e:
        logging.debug('Exception: %s' % e.message)
        _form_data['exceptions'] = e
        _form_data['error_message'] = e.message
        return render(request, "exceptions.html",
                      {
                          'form_data': _form_data,
                      })